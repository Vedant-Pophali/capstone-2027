"""
PUF-Authenticated Flower Strategy — Phase 1: Hardware Root of Trust
====================================================================
Wraps Multi-Krum BFT with a pre-aggregation PUF signature check.

Flow per FL round:
  1. Server sends a per-round challenge (random int) in `fit_config`.
  2. Each FL client computes its PUF response, derives a session key, signs
     its weight update using that key, and returns the signature + vehicle_id
     in the fit metrics dict alongside its numpy weights.
  3. This strategy intercepts `aggregate_fit`, verifies the PUF signature for
     every client BEFORE passing results to Multi-Krum.
  4. Any client whose signature fails (wrong PUF = cloned/rogue vehicle) is
     dropped entirely — its weights never touch the aggregation step.

This separates concerns:
  - PUF layer: "Is this the genuine hardware node?"
  - Multi-Krum layer: "Are these weights Byzantine-poisoned?"
"""

import json
import numpy as np
import flwr as fl
from flwr.common import FitRes, Parameters, Scalar
from flwr.server.client_proxy import ClientProxy

import sys
import os

# Resolve paths so this works regardless of working directory
_STAGE45_DIR = os.path.dirname(os.path.abspath(__file__))
_ML_DIR = os.path.dirname(_STAGE45_DIR)
_EDGE_VEHICLES_ROOT = os.path.normpath(os.path.join(_STAGE45_DIR, "..", "..", "..", "edge-vehicles"))

for _p in [_ML_DIR, _EDGE_VEHICLES_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from stage4_5.bft_strategy import MultiKrum
from stage4_5.puf_enrollment_db import PUFEnrollmentDB
from src.security.crypto_signer import CryptographicSigner


class PUFAuthenticatedStrategy(MultiKrum):
    """
    Extends Multi-Krum with a mandatory PUF handshake verification layer.

    Args:
        enrollment_db:   PUFEnrollmentDB instance with the enrolled fleet.
        round_challenge: Per-round random integer sent to clients as a challenge.
                         In production, this would be freshly generated each round.
        **kwargs:        Passed through to MultiKrum → FedAvg.
    """

    def __init__(
        self,
        enrollment_db: PUFEnrollmentDB,
        round_challenge: int,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.enrollment_db = enrollment_db
        self.round_challenge = round_challenge
        self.blocked_this_round: list[str] = []   # track for reporting
        self.verified_this_round: list[str] = []

    # ------------------------------------------------------------------
    # Override: inject challenge into every client's fit config
    # ------------------------------------------------------------------

    def configure_fit(self, server_round, parameters, client_manager):
        configs = super().configure_fit(server_round, parameters, client_manager)
        # Append the PUF challenge to each client's config dict
        puf_config = {"puf_challenge": self.round_challenge}
        return [(proxy, fl.common.FitIns(ins.parameters, {**ins.config, **puf_config})) for proxy, ins in configs]

    # ------------------------------------------------------------------
    # Override: verify PUF signatures before aggregating
    # ------------------------------------------------------------------

    def aggregate_fit(
        self,
        server_round: int,
        results: list[tuple[ClientProxy, FitRes]],
        failures,
    ):
        self.blocked_this_round = []
        self.verified_this_round = []

        verified_results = []

        for proxy, fit_res in results:
            metrics = fit_res.metrics or {}
            vehicle_id = metrics.get("vehicle_id", "UNKNOWN")
            submitted_sig = metrics.get("puf_signature", "")

            # --- Check 1: Is the vehicle enrolled at all? ---
            if not self.enrollment_db.is_enrolled(str(vehicle_id)):
                print(
                    f"[PUFStrategy] BLOCKED — Vehicle '{vehicle_id}' not in enrollment DB. "
                    f"Possible Sybil / rogue node."
                )
                self.blocked_this_round.append(vehicle_id)
                continue

            # --- Check 2: Re-derive the expected session key server-side ---
            expected_key = self.enrollment_db.get_expected_session_key(
                str(vehicle_id), self.round_challenge
            )

            # --- Check 3: Verify the submitted signature ---
            expected_sig = CryptographicSigner.generate_signature(
                {"round": server_round, "challenge": self.round_challenge},
                expected_key,
            )

            if submitted_sig != expected_sig:
                print(
                    f"[PUFStrategy] BLOCKED — Vehicle '{vehicle_id}' submitted INVALID PUF "
                    f"signature. Hardware mismatch or poisoning attempt."
                )
                self.blocked_this_round.append(vehicle_id)
                continue

            print(f"[PUFStrategy] VERIFIED — Vehicle '{vehicle_id}' PUF signature valid.")
            self.verified_this_round.append(vehicle_id)
            verified_results.append((proxy, fit_res))

        # Report summary
        print(
            f"\n[PUFStrategy] Round {server_round} summary: "
            f"{len(verified_results)} verified, {len(self.blocked_this_round)} blocked."
        )
        if self.blocked_this_round:
            print(f"[PUFStrategy] Blocked vehicles: {self.blocked_this_round}")

        if not verified_results:
            print("[PUFStrategy] No verified clients remain. Skipping aggregation.")
            return None, {}

        # Delegate to Multi-Krum with only verified results
        return super().aggregate_fit(server_round, verified_results, failures)
