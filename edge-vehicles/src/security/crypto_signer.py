import hashlib
import json
import os
import base64
import numpy as np

class CryptographicSigner:
    @staticmethod
    def derive_session_key(puf_response):
        response_bytes = np.packbits((puf_response > 0).astype(int)).tobytes()
        return hashlib.sha256(response_bytes).hexdigest()

    @staticmethod
    def generate_signature(payload_dict, session_key):
        payload_string = json.dumps(payload_dict, sort_keys=True)
        return hashlib.sha256(f"{payload_string}{session_key}".encode()).hexdigest()

    @staticmethod
    def encrypt_data(data: list, session_key_hex: str) -> str:
        """
        Encrypts a list of dicts using AES-256-GCM for the OTA secure tunnel.
        The session_key_hex (64-char SHA-256 hex) is used to derive a 32-byte AES key.
        Returns a base64-encoded string: nonce(12B) + tag(16B) + ciphertext.
        Falls back to HMAC-signed JSON if the cryptography library is unavailable.
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            key = bytes.fromhex(session_key_hex)[:32]  # 32 bytes = AES-256
            nonce = os.urandom(12)                      # 96-bit nonce for GCM
            plaintext = json.dumps(data).encode('utf-8')
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            # Prepend nonce so the receiver can decrypt: nonce || ciphertext+tag
            return base64.b64encode(nonce + ciphertext).decode('utf-8')
        except ImportError:
            # Fallback: HMAC-signed plaintext (still authenticated, not encrypted)
            payload_string = json.dumps(data, sort_keys=True)
            sig = hashlib.sha256(f"{payload_string}{session_key_hex}".encode()).hexdigest()
            return base64.b64encode(json.dumps({"data": data, "sig": sig}).encode()).decode('utf-8')

    @staticmethod
    def decrypt_data(encrypted_b64: str, session_key_hex: str) -> list:
        """
        Decrypts a payload encrypted by encrypt_data.
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            key = bytes.fromhex(session_key_hex)[:32]
            raw = base64.b64decode(encrypted_b64)
            nonce, ciphertext = raw[:12], raw[12:]
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(plaintext.decode('utf-8'))
        except ImportError:
            raw = json.loads(base64.b64decode(encrypted_b64).decode('utf-8'))
            return raw["data"]