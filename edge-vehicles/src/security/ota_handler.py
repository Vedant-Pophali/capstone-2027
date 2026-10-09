import hashlib
import logging
import numpy as np

logger = logging.getLogger("OTAHandler")


class OTAReenrollmentHandler:
    """
    Handles Secure OTA Re-enrollment for an Edge Vehicle.

    When the Cloud Verification Server drops below the CRP threshold (< 500 unused CRPs),
    it sends a renewal signal to this vehicle. This handler then:
      1. Receives a fresh batch of random challenge seeds from the cloud.
      2. Evaluates them locally using the vehicle's pypuf PUF instance.
      3. Encrypts the new CRPs using the active session key (AES-256-GCM).
      4. Sends the encrypted batch back to the cloud via the already-authenticated adapter.

    The cloud then decrypts, stores the new CRPs, and the database is replenished
    without any hardware re-fabrication.
    """

    def __init__(self, vehicle_id: str, puf_module, adapter, session_key: str):
        """
        Args:
            vehicle_id: The ID of this vehicle.
            puf_module:  The VehiclePUF instance (already initialized).
            adapter:     The CloudAdapter instance (already authenticated).
            session_key: The PUF-derived session key hex from the current handshake.
        """
        self.vehicle_id = vehicle_id
        self.puf_module = puf_module
        self.adapter = adapter
        self.session_key = session_key

    def run(self) -> bool:
        """
        Execute the full OTA re-enrollment sequence.
        Returns True if the cloud confirms successful storage.
        """
        logger.info("[OTA] Renewal signal received. Starting OTA re-enrollment sequence.")

        # Step 1: Request a batch of new challenge seeds from the cloud
        challenge_seeds = self._request_new_challenges()
        if not challenge_seeds:
            logger.error("[OTA] Cloud returned no challenge seeds. Aborting renewal.")
            return False

        logger.info("[OTA] Received %d new challenge seeds from cloud.", len(challenge_seeds))

        # Step 2: Evaluate each challenge through the local PUF and build the CRP list
        crp_batch = self._evaluate_challenges(challenge_seeds)

        # Step 3: Encrypt the CRP batch using the authenticated session key
        from src.security.crypto_signer import CryptographicSigner
        encrypted_payload = CryptographicSigner.encrypt_data(crp_batch, self.session_key)
        logger.info("[OTA] CRP batch encrypted with AES-256-GCM session key.")

        # Step 4: Ship the encrypted payload back to the cloud
        success = self.adapter.send_ota_batch(self.vehicle_id, encrypted_payload)

        if success:
            logger.info("[OTA] Re-enrollment complete. Cloud database replenished with %d new CRPs.", len(crp_batch))
        else:
            logger.error("[OTA] Cloud rejected OTA batch. Manual intervention required.")

        return success

    def _request_new_challenges(self) -> list:
        """
        Asks the cloud adapter to return a fresh list of integer challenge seeds.
        The cloud generates these at random — the vehicle has never seen them before.
        """
        return self.adapter.request_ota_challenge_seeds(self.vehicle_id)

    def _evaluate_challenges(self, challenge_seeds: list) -> list:
        """
        Runs each challenge seed through the local pypuf ArbiterPUF instance.
        Returns a list of dicts ready to be sent to the cloud:
          [{"challenge": "12345", "responseHash": "sha256hex..."}, ...]

        The responseHash is stored on the cloud side and later used to verify
        future proof signatures derived from the same PUF response.
        """
        crp_batch = []
        for seed in challenge_seeds:
            try:
                _, response = self.puf_module.get_response(seed)
                # Derive the session key equivalent for this response (same logic as CryptographicSigner)
                response_bytes = np.packbits((response > 0).astype(int)).tobytes()
                response_hash = hashlib.sha256(response_bytes).hexdigest()
                crp_batch.append({
                    "challenge": str(seed),
                    "responseHash": response_hash
                })
            except Exception as e:
                logger.warning("[OTA] Skipping challenge seed %s due to error: %s", seed, e)
        return crp_batch
