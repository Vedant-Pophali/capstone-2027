import datetime
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from puf_simulator import VehiclePUF
from crypto_signer import CryptographicSigner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GatewayVerifier")

class GatewaySecurityVerifier:
    """
    Gateway/Cloud verification module that enforces zero-trust security checks on incoming payloads:
    1. Schema & Required Field Validation
    2. Anti-Replay Timestamp Freshness ($\pm 30$ seconds)
    3. Anti-Replay Nonce Tracking
    4. Hardware PUF Session Key Re-derivation
    5. Cryptographic Signature & Tamper Verification
    """

    def __init__(self, max_drift_seconds: int = 30):
        self.max_drift_seconds = max_drift_seconds
        self.seen_nonces = set()
        # Cache PUF instances per vehicle_id for speed in simulation
        self.puf_cache = {}

    def get_vehicle_puf(self, vehicle_id: str) -> VehiclePUF:
        v_id = str(vehicle_id)
        if v_id not in self.puf_cache:
            # Temporarily inject environment variable to instantiate PUF for vehicle_id
            old_env = os.environ.get("VEHICLE_ID")
            os.environ["VEHICLE_ID"] = v_id
            self.puf_cache[v_id] = VehiclePUF()
            if old_env is not None:
                os.environ["VEHICLE_ID"] = old_env
            elif "VEHICLE_ID" in os.environ:
                del os.environ["VEHICLE_ID"]
        return self.puf_cache[v_id]

    def verify_envelope(self, envelope: dict) -> tuple[bool, str]:
        # 1. Schema & Field Validation
        required_fields = ["version", "payload_id", "vehicle_id", "timestamp", "nonce", "payload_type", "payload", "challenge_seed", "signature"]
        for field in required_fields:
            if field not in envelope:
                msg = f"Security Error: Missing required field '{field}' in envelope"
                logger.warning(msg)
                return False, msg

        # 2. Anti-Replay: Nonce Uniqueness Check
        nonce = envelope["nonce"]
        if nonce in self.seen_nonces:
            msg = f"Security Violation: Replay attack detected! Nonce '{nonce}' has already been processed."
            logger.error(msg)
            return False, msg

        # 3. Anti-Replay: Timestamp Freshness Check
        try:
            payload_time = datetime.datetime.fromisoformat(envelope["timestamp"])
            now = datetime.datetime.now(datetime.timezone.utc)
            time_diff = abs((now - payload_time).total_seconds())

            if time_diff > self.max_drift_seconds:
                msg = f"Security Violation: Timestamp out of bounds ({time_diff:.1f}s drift > {self.max_drift_seconds}s limit)."
                logger.error(msg)
                return False, msg
        except Exception as e:
            msg = f"Security Error: Invalid ISO timestamp format: {e}"
            logger.error(msg)
            return False, msg

        # 4. PUF Session Key Re-derivation
        vehicle_id = envelope["vehicle_id"]
        challenge_seed = envelope["challenge_seed"]
        puf = self.get_vehicle_puf(vehicle_id)

        _, response = puf.get_response(challenge_seed)
        expected_session_key = CryptographicSigner.derive_session_key(response)

        # 5. Cryptographic HMAC Signature Verification
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

        expected_signature = CryptographicSigner.generate_signature(signing_content, expected_session_key)

        if envelope["signature"] != expected_signature:
            msg = f"Security Violation: Signature mismatch! Payload tampered or unauthorized identity for vehicle {vehicle_id}."
            logger.error(msg)
            return False, msg

        # All checks passed: register nonce and return success
        self.seen_nonces.add(nonce)
        logger.info(f"Verification Success: Envelope '{envelope['payload_id']}' from Vehicle '{vehicle_id}' cryptographically verified.")
        return True, "Payload verified successfully"
