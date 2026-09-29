"""
PUF Enrollment Database — Phase 1: Hardware Root of Trust
==========================================================
Simulates a secure facility's enrollment store.

During real hardware deployment this would be a Hardware Security Module (HSM).
In simulation, it's a JSON file written once during enrollment and read-only
during the FL round for verification.

Responsibilities:
  - Enroll a new vehicle: generate a CRP, store it keyed by vehicle_id.
  - Query whether a vehicle is enrolled.
  - Retrieve the expected session key for a given vehicle + challenge.

This module is PURE Python (no torch, no flwr) so it can be imported by
both the FL server and the edge-vehicle simulation without heavyweight deps.
"""

import json
import os
import sys
import hashlib

# Allow importing from the edge-vehicles security module regardless of CWD
_EDGE_VEHICLES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "edge-vehicles")
)
if _EDGE_VEHICLES_ROOT not in sys.path:
    sys.path.insert(0, _EDGE_VEHICLES_ROOT)

from src.security.puf_simulator import VehiclePUF
from src.security.crypto_signer import CryptographicSigner


# Default path for the enrollment store — sits next to this file in stage4_5/
_DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "enrolled_vehicles.json")

# Fixed enrollment challenge seed used during the "secure facility" phase.
# In real hardware, each vehicle would be enrolled with a randomly generated CRP set.
ENROLLMENT_CHALLENGE_SEED = 55555


class PUFEnrollmentDB:
    """
    Persistent enrollment database backed by a JSON file.

    Thread-safety: single-process simulation only. For multi-process FL,
    use a file lock or a proper DB.
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH):
        self.db_path = db_path
        self._records: dict = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                content = f.read().strip()
                self._records = json.loads(content) if content else {}
        else:
            self._records = {}

    def _save(self):
        with open(self.db_path, "w") as f:
            json.dump(self._records, f, indent=2)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def enroll(self, vehicle_id: str, challenge_seed: int = ENROLLMENT_CHALLENGE_SEED) -> str:
        """
        Enroll a vehicle by computing its PUF response to a fixed challenge and
        storing the derived session key.  Returns the expected session key.

        This should be called ONCE per vehicle at the "secure factory floor".
        Calling it again for the same vehicle_id overwrites the record (re-enrollment).
        """
        vid = str(vehicle_id)

        # Instantiate the vehicle's unique PUF (seeded by vehicle_id)
        old_env = os.environ.get("VEHICLE_ID")
        os.environ["VEHICLE_ID"] = vid
        puf = VehiclePUF()
        if old_env is not None:
            os.environ["VEHICLE_ID"] = old_env
        elif "VEHICLE_ID" in os.environ:
            del os.environ["VEHICLE_ID"]

        _, response = puf.get_response(challenge_seed)
        session_key = CryptographicSigner.derive_session_key(response)

        self._records[vid] = {
            "vehicle_id": vid,
            "challenge_seed": challenge_seed,
            "enrolled_session_key": session_key,
        }
        self._save()
        print(f"[EnrollmentDB] Vehicle '{vid}' enrolled. Key prefix: {session_key[:12]}...")
        return session_key

    def is_enrolled(self, vehicle_id: str) -> bool:
        return str(vehicle_id) in self._records

    def get_expected_session_key(self, vehicle_id: str, challenge_seed: int) -> str | None:
        """
        Re-derive the expected session key for a vehicle given a challenge seed.
        Returns None if the vehicle is not enrolled.

        The server calls this during FL weight submission to verify the client's
        PUF signature without trusting the client's claimed identity.
        """
        vid = str(vehicle_id)
        if vid not in self._records:
            return None

        # Re-derive fresh (not cached from enrollment) — supports arbitrary challenges
        old_env = os.environ.get("VEHICLE_ID")
        os.environ["VEHICLE_ID"] = vid
        puf = VehiclePUF()
        if old_env is not None:
            os.environ["VEHICLE_ID"] = old_env
        elif "VEHICLE_ID" in os.environ:
            del os.environ["VEHICLE_ID"]

        _, response = puf.get_response(challenge_seed)
        return CryptographicSigner.derive_session_key(response)

    def list_enrolled(self) -> list[str]:
        return list(self._records.keys())

    def revoke(self, vehicle_id: str) -> bool:
        """Remove a vehicle from the authorized fleet (e.g., compromised node)."""
        vid = str(vehicle_id)
        if vid in self._records:
            del self._records[vid]
            self._save()
            print(f"[EnrollmentDB] Vehicle '{vid}' revoked.")
            return True
        return False

    def clear(self):
        """Wipe the entire database — useful in tests."""
        self._records = {}
        if os.path.exists(self.db_path):
            os.remove(self.db_path)


def run_enrollment(vehicle_ids: list[str], db_path: str = _DEFAULT_DB_PATH):
    """
    Convenience function: enroll a list of vehicle IDs and print a summary.
    Run this once before starting the FL simulation.
    """
    db = PUFEnrollmentDB(db_path=db_path)
    print("\n=== PUF Enrollment Phase (Secure Factory Floor) ===")
    for vid in vehicle_ids:
        db.enroll(vid)
    print(f"\n[EnrollmentDB] {len(vehicle_ids)} vehicle(s) enrolled in '{db_path}'")
    print(f"[EnrollmentDB] Enrolled fleet: {db.list_enrolled()}\n")
    return db


if __name__ == "__main__":
    # Run enrollment for the default 4-vehicle FL simulation fleet
    run_enrollment(["vehicle_0", "vehicle_1", "vehicle_2", "vehicle_3"])
