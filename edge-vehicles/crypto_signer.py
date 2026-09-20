import hashlib
import json
import numpy as np

class CryptographicSigner:
    @staticmethod
    def derive_session_key(puf_response):
        response_bytes = np.packbits((puf_response > 0).astype(int)).tobytes()
        return hashlib.sha256(response_bytes).hexdigest()

    @staticmethod
    def sign_payload(payload_dict, session_key):
        payload_string = json.dumps(payload_dict, sort_keys=True)
        signature = hashlib.sha256(f"{payload_string}{session_key}".encode()).hexdigest()
        
        return {
            "data": payload_dict,
            "signature": signature
        }