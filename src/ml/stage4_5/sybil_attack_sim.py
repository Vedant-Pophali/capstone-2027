"""
Sybil / Weight-Poisoning Attack Simulation — Phase 1 Demo
==========================================================
This script proves that without a valid PUF signature, a rogue vehicle
(attacker cloning a legitimate vehicle's identity or injecting from a new
unregistered node) cannot contribute poisoned weights to the global model.

Scenarios simulated:
  A. Legitimate client — enrolled, correct PUF — ACCEPTED
  B. Rogue Sybil (unregistered vehicle ID) — BLOCKED
  C. Cloned identity (right vehicle_id, wrong PUF hardware) — BLOCKED
  D. Tampered signature (MITM bit-flip after signing) — BLOCKED

Run standalone:
    python sybil_attack_sim.py
"""

import os
import sys
import json
import tempfile

# Path resolution
_STAGE45_DIR = os.path.dirname(os.path.abspath(__file__))
_EDGE_VEHICLES_ROOT = os.path.normpath(
    os.path.join(_STAGE45_DIR, "..", "..", "..", "edge-vehicles")
)
for _p in [_STAGE45_DIR, _EDGE_VEHICLES_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from puf_enrollment_db import PUFEnrollmentDB
from puf_fl_strategy import PUFAuthenticatedStrategy
from src.security.puf_simulator import VehiclePUF
from src.security.crypto_signer import CryptographicSigner


SEPARATOR = "=" * 60
ROUND_CHALLENGE = 87654   # Fixed for this simulation
ROUND_NUMBER    = 1


def build_puf_signature(vehicle_id: str, challenge: int, round_num: int) -> tuple[str, str]:
    """Helper: compute the PUF signature for a given vehicle at a given challenge."""
    old_env = os.environ.get("VEHICLE_ID")
    os.environ["VEHICLE_ID"] = str(vehicle_id)
    puf = VehiclePUF()
    if old_env is not None:
        os.environ["VEHICLE_ID"] = old_env
    elif "VEHICLE_ID" in os.environ:
        del os.environ["VEHICLE_ID"]

    _, response = puf.get_response(challenge)
    session_key = CryptographicSigner.derive_session_key(response)
    signature   = CryptographicSigner.generate_signature(
        {"round": round_num, "challenge": challenge}, session_key
    )
    return session_key, signature


def simulate_attack(
    label: str,
    vehicle_id: str,
    signature: str,
    enrollment_db: PUFEnrollmentDB,
) -> bool:
    """
    Simulate the server-side PUF verification check for one client submission.
    Returns True if the client would be ACCEPTED, False if BLOCKED.
    """
    print(f"\n  Scenario: {label}")
    print(f"  Vehicle ID : '{vehicle_id}'")
    print(f"  Signature  : {signature[:24]}...")

    # Step 1: Enrollment check
    if not enrollment_db.is_enrolled(str(vehicle_id)):
        print("  Result     : [BLOCKED] BLOCKED — Vehicle not in enrollment DB (Sybil/rogue node)")
        return False

    # Step 2: Re-derive expected key from enrollment DB
    expected_key = enrollment_db.get_expected_session_key(str(vehicle_id), ROUND_CHALLENGE)
    expected_sig = CryptographicSigner.generate_signature(
        {"round": ROUND_NUMBER, "challenge": ROUND_CHALLENGE},
        expected_key,
    )

    # Step 3: Compare
    if signature != expected_sig:
        print("  Result     : [BLOCKED] BLOCKED — PUF signature mismatch (cloned identity / MITM)")
        return False

    print("  Result     : [SUCCESS] ACCEPTED — Genuine hardware node verified")
    return True


def main():
    print(SEPARATOR)
    print("  Phase 1 — Sybil & Weight-Poisoning Attack Simulation")
    print(SEPARATOR)

    # ----------------------------------------------------------------
    # Setup: enroll only the legitimate vehicle (vehicle_0)
    # ----------------------------------------------------------------
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        db_path = f.name

    db = PUFEnrollmentDB(db_path=db_path)
    db.enroll("vehicle_0", challenge_seed=ROUND_CHALLENGE)
    print(f"\n[Setup] Enrolled fleet: {db.list_enrolled()}")
    print(f"[Setup] Round challenge: {ROUND_CHALLENGE}")

    results = {}

    # ----------------------------------------------------------------
    # Scenario A: Legitimate enrolled vehicle with correct PUF
    # ----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    _, legit_sig = build_puf_signature("vehicle_0", ROUND_CHALLENGE, ROUND_NUMBER)
    results["A_legitimate"] = simulate_attack(
        label="Legitimate vehicle (enrolled, correct hardware)",
        vehicle_id="vehicle_0",
        signature=legit_sig,
        enrollment_db=db,
    )

    # ----------------------------------------------------------------
    # Scenario B: Rogue Sybil — completely unknown vehicle ID
    # ----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    _, rogue_sig = build_puf_signature("rogue_999", ROUND_CHALLENGE, ROUND_NUMBER)
    results["B_sybil_unregistered"] = simulate_attack(
        label="Sybil attack — unregistered vehicle ID 'rogue_999'",
        vehicle_id="rogue_999",
        signature=rogue_sig,
        enrollment_db=db,
    )

    # ----------------------------------------------------------------
    # Scenario C: Cloned identity — attacker uses vehicle_0's ID
    # but runs it through their own PUF (different silicon = different key)
    # ----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    # Attacker's PUF is seeded with a DIFFERENT id internally (simulates different chip)
    old_env = os.environ.get("VEHICLE_ID")
    os.environ["VEHICLE_ID"] = "ATTACKER_CHIP"   # wrong silicon seed
    attacker_puf = VehiclePUF()
    if old_env is not None:
        os.environ["VEHICLE_ID"] = old_env
    elif "VEHICLE_ID" in os.environ:
        del os.environ["VEHICLE_ID"]

    _, attacker_resp = attacker_puf.get_response(ROUND_CHALLENGE)
    attacker_key     = CryptographicSigner.derive_session_key(attacker_resp)
    attacker_sig     = CryptographicSigner.generate_signature(
        {"round": ROUND_NUMBER, "challenge": ROUND_CHALLENGE}, attacker_key
    )
    results["C_cloned_identity"] = simulate_attack(
        label="Cloned identity — uses vehicle_0's ID but attacker's own PUF chip",
        vehicle_id="vehicle_0",  # Claims to be vehicle_0
        signature=attacker_sig,  # But signs with wrong silicon
        enrollment_db=db,
    )

    # ----------------------------------------------------------------
    # Scenario D: MITM bit-flip — valid signature tampered in transit
    # ----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    # Take the legit signature and flip one character (simulates network tampering)
    tampered_sig = legit_sig[:-4] + "XXXX"
    results["D_mitm_tampered"] = simulate_attack(
        label="MITM tampering — valid sig with 4 trailing chars flipped",
        vehicle_id="vehicle_0",
        signature=tampered_sig,
        enrollment_db=db,
    )

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("  SIMULATION SUMMARY")
    print(SEPARATOR)
    for scenario, accepted in results.items():
        status = "[SUCCESS] ACCEPTED" if accepted else "[BLOCKED] BLOCKED"
        print(f"  {scenario:<30}: {status}")

    # Verify expected outcomes
    assert results["A_legitimate"]       is True,  "FAIL: Legit vehicle was wrongly blocked"
    assert results["B_sybil_unregistered"] is False, "FAIL: Sybil was not blocked"
    assert results["C_cloned_identity"]  is False,  "FAIL: Clone was not blocked"
    assert results["D_mitm_tampered"]    is False,  "FAIL: Tampered sig was not blocked"

    print(f"\n  All {len(results)} scenarios passed assertions. [SUCCESS]")
    print(SEPARATOR)

    # Cleanup
    os.unlink(db_path)


if __name__ == "__main__":
    main()
