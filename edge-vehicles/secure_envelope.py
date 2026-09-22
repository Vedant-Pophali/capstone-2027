import uuid
import datetime
import secrets
from crypto_signer import CryptographicSigner

class SecurePayloadEnvelope:
    VERSION = "1.0"

    @classmethod
    def create(cls, vehicle_id: str, payload_type: str, payload_data: dict, challenge_seed: int, session_key: str) -> dict:
        """
        Wraps raw payload data into a standardized secure envelope with replay protection
        (timestamp + nonce) and a PUF-derived cryptographic signature.
        """
        payload_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        nonce = secrets.token_hex(8)

        # Structure of metadata to be signed
        signing_content = {
            "version": cls.VERSION,
            "payload_id": payload_id,
            "vehicle_id": str(vehicle_id),
            "timestamp": timestamp,
            "nonce": nonce,
            "payload_type": payload_type,
            "payload": payload_data,
            "challenge_seed": challenge_seed
        }

        # Calculate signature over the entire payload & metadata using PUF session key
        signature = CryptographicSigner.generate_signature(signing_content, session_key)

        # Build final secure envelope
        envelope = signing_content
        envelope["signature"] = signature
        return envelope
