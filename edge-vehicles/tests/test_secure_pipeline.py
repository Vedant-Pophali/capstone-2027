import unittest
import os
import sys
import datetime

# Ensure edge-vehicles directory is in Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.network.cloud_adapter import AdapterFactory, MockCloudAdapter, HTTPRestAdapter, WebSocketAdapter
from src.security.secure_envelope import SecurePayloadEnvelope
from src.network.gateway_verifier import GatewaySecurityVerifier
from src.security.puf_simulator import VehiclePUF
from src.security.crypto_signer import CryptographicSigner
from src.core.state_machine import RedundantStateMachine, HandshakeState

class TestSecureEdgeToCloudPipeline(unittest.TestCase):

    def setUp(self):
        os.environ["VEHICLE_ID"] = "101"
        self.vehicle_id = "101"
        self.puf = VehiclePUF()
        self.challenge_seed = 9999
        _, response = self.puf.get_response(self.challenge_seed)
        self.session_key = CryptographicSigner.derive_session_key(response)
        self.verifier = GatewaySecurityVerifier(max_drift_seconds=30)

    def test_adapter_factory(self):
        """Tests dynamic instantiation of transport adapters."""
        mock_adapter = AdapterFactory.create_adapter("mock")
        self.assertIsInstance(mock_adapter, MockCloudAdapter)

        http_adapter = AdapterFactory.create_adapter("http", "http://test:8080/ingest")
        self.assertIsInstance(http_adapter, HTTPRestAdapter)
        self.assertEqual(http_adapter.endpoint_url, "http://test:8080/ingest")

        ws_adapter = AdapterFactory.create_adapter("websocket", "ws://test:8080/ws")
        self.assertIsInstance(ws_adapter, WebSocketAdapter)
        self.assertEqual(ws_adapter.endpoint_url, "ws://test:8080/ws")

    def test_secure_envelope_verification_success(self):
        """Verifies that a validly signed payload envelope passes gateway verification."""
        raw_payload = {"snn_layer1": [0.1, -0.2], "status": "NORMAL"}
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="MODEL_UPDATE",
            payload_data=raw_payload,
            challenge_seed=self.challenge_seed,
            session_key=self.session_key
        )

        is_valid, msg = self.verifier.verify_envelope(envelope)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "Payload verified successfully")

    def test_tampered_payload_rejected(self):
        """Proves that any payload tampering in transit invalidates the signature."""
        raw_payload = {"weights": [1.0, 2.0]}
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="MODEL_UPDATE",
            payload_data=raw_payload,
            challenge_seed=self.challenge_seed,
            session_key=self.session_key
        )

        # Attacker modifies weights in transit
        envelope["payload"]["weights"] = [999.0, 999.0]

        is_valid, msg = self.verifier.verify_envelope(envelope)
        self.assertFalse(is_valid)
        self.assertIn("Signature mismatch", msg)

    def test_replay_attack_rejected_duplicate_nonce(self):
        """Proves that replaying an identical envelope with a seen nonce is caught."""
        raw_payload = {"alert": "DOS_ATTACK"}
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="THREAT_ALERT",
            payload_data=raw_payload,
            challenge_seed=self.challenge_seed,
            session_key=self.session_key
        )

        # First transmission -> Valid
        is_valid_1, _ = self.verifier.verify_envelope(envelope)
        self.assertTrue(is_valid_1)

        # Second transmission (Replay Attack) -> Rejected
        is_valid_2, msg_2 = self.verifier.verify_envelope(envelope)
        self.assertFalse(is_valid_2)
        self.assertIn("Replay attack detected", msg_2)

    def test_replay_attack_rejected_expired_timestamp(self):
        """Proves that sending an envelope with an old timestamp is rejected."""
        raw_payload = {"telemetry": "speed=120"}
        envelope = SecurePayloadEnvelope.create(
            vehicle_id=self.vehicle_id,
            payload_type="TELEMETRY",
            payload_data=raw_payload,
            challenge_seed=self.challenge_seed,
            session_key=self.session_key
        )

        # Tamper timestamp to 100 seconds in the past
        old_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=100)
        envelope["timestamp"] = old_time.isoformat()

        # Recompute signature for the old timestamp to isolate timestamp check
        signing_content = {
            "version": envelope["version"],
            "payload_id": envelope["payload_id"],
            "vehicle_id": envelope["vehicle_id"],
            "timestamp": envelope["timestamp"],
            "nonce": envelope["nonce"],
            "payload_type": envelope["payload_type"],
            "payload": envelope["payload"],
            "challenge_seed": envelope["challenge_seed"]
        }
        envelope["signature"] = CryptographicSigner.generate_signature(signing_content, self.session_key)

        is_valid, msg = self.verifier.verify_envelope(envelope)
        self.assertFalse(is_valid)
        self.assertIn("Timestamp out of bounds", msg)

    def test_fault_injection_aborts_state_machine(self):
        """Ensures that state machine majority voting catches memory corruption before dispatch."""
        sm = RedundantStateMachine()
        sm.transition_to(HandshakeState.CHALLENGE_ISSUED)
        
        # Corrupt state_a to simulate fault injection glitch
        sm.state_a = HandshakeState.INIT

        with self.assertRaises(SystemError) as context:
            sm.check_state()
        self.assertIn("Fault-injection detected", str(context.exception))

if __name__ == "__main__":
    unittest.main()
