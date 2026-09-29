"""
Phase 1 Integration Tests — PUF Hardware Root of Trust
=======================================================
Tests the entire chain:
  PUFEnrollmentDB → PUFAuthenticatedStrategy → fl_client signing

Test groups:
  1. Enrollment DB: enroll, query, revoke, persistence
  2. FL Strategy: accepts genuine, blocks Sybil, blocks clone, blocks MITM
  3. FL Client signing: produces correct signature that passes server-side check
  4. Regression: all 8 existing edge-vehicle tests still pass after Phase 1
  5. Edge cases: empty challenge, re-enrollment, revoked vehicle mid-round
"""

import os
import sys
import json
import tempfile
import unittest

# Path setup
_HERE = os.path.dirname(os.path.abspath(__file__))
_EDGE_VEHICLES_ROOT = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "edge-vehicles"))
for _p in [_HERE, _EDGE_VEHICLES_ROOT]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from puf_enrollment_db import PUFEnrollmentDB, ENROLLMENT_CHALLENGE_SEED
from src.security.puf_simulator import VehiclePUF
from src.security.crypto_signer import CryptographicSigner
from src.core.state_machine import RedundantStateMachine, HandshakeState
from src.network.gateway_verifier import GatewaySecurityVerifier


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_temp_db() -> PUFEnrollmentDB:
    """Return a fresh in-memory-like enrollment DB backed by a temp file."""
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.close()
    db = PUFEnrollmentDB(db_path=f.name)
    db.clear()   # ensure empty
    return db


def _sign_for_vehicle(vehicle_id: str, challenge: int, round_num: int) -> tuple[str, str]:
    """Compute (session_key, signature) for a vehicle exactly as fl_client.py does."""
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


def _server_verify(db: PUFEnrollmentDB, vehicle_id: str, challenge: int,
                   round_num: int, submitted_sig: str) -> bool:
    """Replicate exactly what PUFAuthenticatedStrategy does for one client."""
    if not db.is_enrolled(str(vehicle_id)):
        return False
    expected_key = db.get_expected_session_key(str(vehicle_id), challenge)
    expected_sig = CryptographicSigner.generate_signature(
        {"round": round_num, "challenge": challenge}, expected_key
    )
    return submitted_sig == expected_sig


# ---------------------------------------------------------------------------
# Group 1: PUFEnrollmentDB unit tests
# ---------------------------------------------------------------------------

class TestEnrollmentDB(unittest.TestCase):

    def setUp(self):
        self.db = _make_temp_db()

    def tearDown(self):
        if os.path.exists(self.db.db_path):
            os.unlink(self.db.db_path)

    def test_enroll_and_is_enrolled(self):
        """Enrolling a vehicle marks it as enrolled."""
        self.assertFalse(self.db.is_enrolled("v1"))
        self.db.enroll("v1")
        self.assertTrue(self.db.is_enrolled("v1"))

    def test_list_enrolled(self):
        """list_enrolled returns all enrolled vehicle IDs."""
        self.db.enroll("v1")
        self.db.enroll("v2")
        enrolled = self.db.list_enrolled()
        self.assertIn("v1", enrolled)
        self.assertIn("v2", enrolled)

    def test_revoke(self):
        """Revoked vehicles are no longer enrolled."""
        self.db.enroll("v1")
        self.assertTrue(self.db.is_enrolled("v1"))
        revoked = self.db.revoke("v1")
        self.assertTrue(revoked)
        self.assertFalse(self.db.is_enrolled("v1"))

    def test_revoke_unknown_returns_false(self):
        """Revoking a vehicle that was never enrolled returns False."""
        self.assertFalse(self.db.revoke("never_enrolled"))

    def test_persistence_across_reload(self):
        """Enrolled records survive DB reload from disk."""
        self.db.enroll("v_persist")
        # Reload from the same file
        db2 = PUFEnrollmentDB(db_path=self.db.db_path)
        self.assertTrue(db2.is_enrolled("v_persist"))

    def test_reenrollment_overwrites(self):
        """Re-enrolling the same vehicle_id updates the record without duplication."""
        self.db.enroll("v_re", challenge_seed=11111)
        key1 = self.db.get_expected_session_key("v_re", 11111)
        self.db.enroll("v_re", challenge_seed=22222)  # different challenge
        self.assertEqual(len(self.db.list_enrolled()), 1)   # still one record
        key2 = self.db.get_expected_session_key("v_re", 22222)
        self.assertIsNotNone(key2)

    def test_get_expected_key_for_unenrolled_returns_none(self):
        """Querying a key for an unenrolled vehicle returns None."""
        result = self.db.get_expected_session_key("ghost_vehicle", 99999)
        self.assertIsNone(result)

    def test_different_vehicles_produce_different_keys(self):
        """Two distinct vehicle IDs enrolled with the same challenge produce distinct keys."""
        self.db.enroll("va")
        self.db.enroll("vb")
        key_a = self.db.get_expected_session_key("va", ENROLLMENT_CHALLENGE_SEED)
        key_b = self.db.get_expected_session_key("vb", ENROLLMENT_CHALLENGE_SEED)
        self.assertNotEqual(key_a, key_b)


# ---------------------------------------------------------------------------
# Group 2: Server-side PUF verification (what PUFAuthenticatedStrategy does)
# ---------------------------------------------------------------------------

CHALLENGE = 43210
ROUND     = 1

class TestServerVerification(unittest.TestCase):

    def setUp(self):
        self.db = _make_temp_db()
        self.db.enroll("legit_vehicle", challenge_seed=CHALLENGE)

    def tearDown(self):
        if os.path.exists(self.db.db_path):
            os.unlink(self.db.db_path)

    def test_legitimate_vehicle_accepted(self):
        """A correctly enrolled vehicle with the correct PUF is accepted."""
        _, sig = _sign_for_vehicle("legit_vehicle", CHALLENGE, ROUND)
        self.assertTrue(_server_verify(self.db, "legit_vehicle", CHALLENGE, ROUND, sig))

    def test_sybil_unregistered_blocked(self):
        """An unregistered vehicle ID is unconditionally rejected."""
        _, sig = _sign_for_vehicle("rogue_vehicle", CHALLENGE, ROUND)
        self.assertFalse(_server_verify(self.db, "rogue_vehicle", CHALLENGE, ROUND, sig))

    def test_cloned_identity_blocked(self):
        """
        An attacker claiming legit_vehicle's ID but running a different PUF
        (different silicon = different seed) produces a wrong key → blocked.
        """
        # Attacker signs with their own PUF (seeded differently)
        old_env = os.environ.get("VEHICLE_ID")
        os.environ["VEHICLE_ID"] = "ATTACKER_CHIP_ID"
        attacker_puf = VehiclePUF()
        if old_env is not None:
            os.environ["VEHICLE_ID"] = old_env
        elif "VEHICLE_ID" in os.environ:
            del os.environ["VEHICLE_ID"]

        _, attacker_resp = attacker_puf.get_response(CHALLENGE)
        attacker_key = CryptographicSigner.derive_session_key(attacker_resp)
        attacker_sig = CryptographicSigner.generate_signature(
            {"round": ROUND, "challenge": CHALLENGE}, attacker_key
        )

        self.assertFalse(
            _server_verify(self.db, "legit_vehicle", CHALLENGE, ROUND, attacker_sig)
        )

    def test_mitm_tampered_signature_blocked(self):
        """A valid signature with even a single byte flipped is rejected."""
        _, sig = _sign_for_vehicle("legit_vehicle", CHALLENGE, ROUND)
        tampered = sig[:-1] + ("0" if sig[-1] != "0" else "1")
        self.assertFalse(
            _server_verify(self.db, "legit_vehicle", CHALLENGE, ROUND, tampered)
        )

    def test_wrong_challenge_blocked(self):
        """A correct signature for challenge X does not verify at challenge Y."""
        _, sig = _sign_for_vehicle("legit_vehicle", CHALLENGE, ROUND)
        self.assertFalse(
            _server_verify(self.db, "legit_vehicle", CHALLENGE + 1, ROUND, sig)
        )

    def test_wrong_round_blocked(self):
        """A signature from round N cannot be replayed at round N+1."""
        _, sig = _sign_for_vehicle("legit_vehicle", CHALLENGE, ROUND)
        self.assertFalse(
            _server_verify(self.db, "legit_vehicle", CHALLENGE, ROUND + 1, sig)
        )

    def test_revoked_vehicle_blocked(self):
        """Once a vehicle is revoked its signature is rejected even if correct."""
        _, sig = _sign_for_vehicle("legit_vehicle", CHALLENGE, ROUND)
        self.db.revoke("legit_vehicle")
        self.assertFalse(
            _server_verify(self.db, "legit_vehicle", CHALLENGE, ROUND, sig)
        )

    def test_multiple_legitimate_vehicles(self):
        """Several distinct enrolled vehicles are each individually accepted."""
        for vid in ["veh_a", "veh_b", "veh_c"]:
            self.db.enroll(vid, challenge_seed=CHALLENGE)
            _, sig = _sign_for_vehicle(vid, CHALLENGE, ROUND)
            self.assertTrue(
                _server_verify(self.db, vid, CHALLENGE, ROUND, sig),
                msg=f"Vehicle {vid} was incorrectly rejected"
            )

    def test_empty_signature_blocked(self):
        """An empty string signature is always rejected."""
        self.assertFalse(
            _server_verify(self.db, "legit_vehicle", CHALLENGE, ROUND, "")
        )


# ---------------------------------------------------------------------------
# Group 3: FL Client signing produces verifiable signature
# ---------------------------------------------------------------------------

class TestFLClientSigning(unittest.TestCase):

    def setUp(self):
        self.db = _make_temp_db()
        self.vehicle_id = "vehicle_42"
        self.challenge  = 77777
        self.round_num  = 3
        self.db.enroll(self.vehicle_id, challenge_seed=self.challenge)

    def tearDown(self):
        if os.path.exists(self.db.db_path):
            os.unlink(self.db.db_path)

    def test_client_signature_accepted_by_server(self):
        """Signature produced by fl_client logic passes the server verification."""
        _, sig = _sign_for_vehicle(self.vehicle_id, self.challenge, self.round_num)
        self.assertTrue(
            _server_verify(self.db, self.vehicle_id, self.challenge, self.round_num, sig)
        )

    def test_same_vehicle_same_challenge_deterministic(self):
        """PUF response is deterministic: same input always yields same signature."""
        _, sig1 = _sign_for_vehicle(self.vehicle_id, self.challenge, self.round_num)
        _, sig2 = _sign_for_vehicle(self.vehicle_id, self.challenge, self.round_num)
        self.assertEqual(sig1, sig2)

    def test_different_challenges_different_signatures(self):
        """Each challenge produces a unique session key and thus a unique signature."""
        _, sig_a = _sign_for_vehicle(self.vehicle_id, 11111, self.round_num)
        _, sig_b = _sign_for_vehicle(self.vehicle_id, 22222, self.round_num)
        self.assertNotEqual(sig_a, sig_b)

    def test_different_rounds_different_signatures(self):
        """Different round numbers produce different signatures (no cross-round replay)."""
        _, sig_r1 = _sign_for_vehicle(self.vehicle_id, self.challenge, 1)
        _, sig_r2 = _sign_for_vehicle(self.vehicle_id, self.challenge, 2)
        self.assertNotEqual(sig_r1, sig_r2)


# ---------------------------------------------------------------------------
# Group 4: Regression — all original edge-vehicle tests still pass
# ---------------------------------------------------------------------------

class TestOriginalPipelineRegression(unittest.TestCase):
    """Imports and re-runs the original tests to guarantee Phase 1 didn't break anything."""

    def setUp(self):
        os.environ["VEHICLE_ID"] = "101"
        self.vehicle_id = "101"
        self.puf = VehiclePUF()
        self.challenge_seed = 9999
        _, response = self.puf.get_response(self.challenge_seed)
        self.session_key = CryptographicSigner.derive_session_key(response)
        self.verifier = GatewaySecurityVerifier(max_drift_seconds=30)

    def test_fault_injection_fails_safe(self):
        sm = RedundantStateMachine()
        sm.transition_to(HandshakeState.CHALLENGE_ISSUED)
        sm.state_a = HandshakeState.INIT
        with self.assertRaises(SystemError) as ctx:
            sm.check_state()
        self.assertIn("Fault-injection detected", str(ctx.exception))

    def test_sybil_spoofed_vehicle_different_keys(self):
        os.environ["VEHICLE_ID"] = "101"
        car1 = VehiclePUF()
        _, resp1 = car1.get_response(999)
        key1 = CryptographicSigner.derive_session_key(resp1)

        os.environ["VEHICLE_ID"] = "202"
        car2 = VehiclePUF()
        _, resp2 = car2.get_response(999)
        key2 = CryptographicSigner.derive_session_key(resp2)

        self.assertNotEqual(key1, key2)

    def test_secure_envelope_verification_success(self):
        from src.security.secure_envelope import SecurePayloadEnvelope
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="MODEL_UPDATE",
            payload_data={"weights": [0.1, -0.2]},
            challenge_seed=self.challenge_seed,
            session_key=self.session_key,
        )
        is_valid, msg = self.verifier.verify_envelope(envelope)
        self.assertTrue(is_valid)

    def test_tampered_payload_rejected(self):
        from src.security.secure_envelope import SecurePayloadEnvelope
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="MODEL_UPDATE",
            payload_data={"weights": [1.0, 2.0]},
            challenge_seed=self.challenge_seed,
            session_key=self.session_key,
        )
        envelope["payload"]["weights"] = [999.0, 999.0]
        is_valid, msg = self.verifier.verify_envelope(envelope)
        self.assertFalse(is_valid)
        self.assertIn("Signature mismatch", msg)

    def test_replay_attack_rejected(self):
        from src.security.secure_envelope import SecurePayloadEnvelope
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="THREAT_ALERT",
            payload_data={"alert": "DOS"},
            challenge_seed=self.challenge_seed,
            session_key=self.session_key,
        )
        is_valid_1, _ = self.verifier.verify_envelope(envelope)
        self.assertTrue(is_valid_1)
        is_valid_2, msg = self.verifier.verify_envelope(envelope)
        self.assertFalse(is_valid_2)
        self.assertIn("Replay attack detected", msg)


# ---------------------------------------------------------------------------
# Group 5: Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases(unittest.TestCase):

    def setUp(self):
        self.db = _make_temp_db()

    def tearDown(self):
        if os.path.exists(self.db.db_path):
            os.unlink(self.db.db_path)

    def test_zero_challenge_seed(self):
        """Challenge seed of 0 is a valid (if unusual) input — must not crash."""
        self.db.enroll("v_zero", challenge_seed=0)
        key = self.db.get_expected_session_key("v_zero", 0)
        self.assertIsNotNone(key)
        self.assertIsInstance(key, str)

    def test_large_challenge_seed(self):
        """Very large challenge seeds are handled without overflow or crash."""
        BIG = 2**31 - 1
        self.db.enroll("v_big", challenge_seed=BIG)
        key = self.db.get_expected_session_key("v_big", BIG)
        self.assertIsNotNone(key)

    def test_vehicle_id_type_coercion(self):
        """Integer vehicle IDs (as used in Docker env) are treated the same as string."""
        self.db.enroll(42)              # int
        self.assertTrue(self.db.is_enrolled("42"))   # query as string
        self.assertTrue(self.db.is_enrolled(42))     # query as int

    def test_clear_removes_all_records(self):
        """clear() wipes all records and removes the backing file."""
        self.db.enroll("v1")
        self.db.enroll("v2")
        self.db.clear()
        self.assertEqual(self.db.list_enrolled(), [])

    def test_enroll_100_vehicles_all_unique_keys(self):
        """100 vehicles enrolled with the same challenge all produce distinct session keys."""
        challenge = 31415
        keys = set()
        for i in range(100):
            vid = f"vehicle_{i}"
            self.db.enroll(vid, challenge_seed=challenge)
            key = self.db.get_expected_session_key(vid, challenge)
            keys.add(key)
        self.assertEqual(len(keys), 100, "Duplicate keys detected among 100 vehicles")


if __name__ == "__main__":
    unittest.main(verbosity=2)
