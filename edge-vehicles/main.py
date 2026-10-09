import os
import sys
from src.security.puf_simulator import VehiclePUF
from src.core.state_machine import RedundantStateMachine, HandshakeState
from src.security.crypto_signer import CryptographicSigner
from src.security.secure_envelope import SecurePayloadEnvelope
from src.security.ota_handler import OTAReenrollmentHandler
from src.network.cloud_adapter import AdapterFactory
from src.network.payload_factory import PayloadFactory

class VehicleNode:
    """
    Decoupled orchestrator for a single Edge Vehicle.
    Allows instantiating multiple independent simulated vehicles at scale.

    Security model:
      - PUF handshake MUST complete (reach VERIFIED state) before any telemetry is sent.
      - The Gating Mechanism is enforced by a hard state check; if the state machine
        is not in VERIFIED state, all ML payload construction is skipped entirely.
      - OTA re-enrollment runs over the same session key, so the CRP batch is
        always transmitted in an AES-256-GCM encrypted tunnel.
    """
    def __init__(self, vehicle_id: str, challenge_seed: int = 12345):
        self.vehicle_id = vehicle_id
        self.challenge_seed = challenge_seed
        self.state_machine = RedundantStateMachine()
        self.session_key = None  # Set after handshake; reused for OTA tunnel

        # Temporarily set env var so VehiclePUF picks up the right seed.
        old_env = os.environ.get("VEHICLE_ID")
        os.environ["VEHICLE_ID"] = str(self.vehicle_id)
        self.puf_module = VehiclePUF()
        if old_env is not None:
            os.environ["VEHICLE_ID"] = old_env
            
        self.adapter = AdapterFactory.create_adapter()
        self.adapter.connect()

    def run(self, payload_type: str = "MODEL_UPDATE"):
        print(f"\n[*] Booting Edge Node for Vehicle ID: {self.vehicle_id}")

        try:
            # 1. Begin PUF Handshake Sequence (Two-Way)
            print("[*] Initiating Hardware PUF Handshake sequence...")
            self.state_machine.transition_to(HandshakeState.CHALLENGE_ISSUED)
            self.state_machine.check_state()

            # 1a. Send lightweight ping requesting to join
            join_resp = self.adapter.request_join(self.vehicle_id)
            if join_resp.get("status") != "authorized":
                print(f"[!] Cloud gateway rejected the connection: {join_resp.get('reason')}")
                return False
                
            cloud_challenge = join_resp.get("challenge")
            print(f"[+] Received Challenge from Cloud: {cloud_challenge}")

            # 2. Compute Hardware Response to the Cloud Challenge
            _, response = self.puf_module.get_response(cloud_challenge)
            self.state_machine.transition_to(HandshakeState.RESPONSE_COMPUTED)
            self.state_machine.check_state()

            # 3. Derive Per-Round Session Key (PUF-backed SHA-256)
            self.session_key = CryptographicSigner.derive_session_key(response)
            print(f"[+] Derived Hardware Session Key: {self.session_key[:12]}...")
            
            # 3a. Send lightweight proof (signed heartbeat)
            proof_signature = CryptographicSigner.generate_signature({"heartbeat": cloud_challenge}, self.session_key)
            if not self.adapter.send_proof(self.vehicle_id, cloud_challenge, proof_signature):
                print("[!] Cloud gateway rejected the PUF proof. Unauthorized vehicle.")
                return False

            self.state_machine.transition_to(HandshakeState.VERIFIED)
            current_state = self.state_machine.check_state()
            print(f"[+] Handshake Verified (State: {current_state.name}). Vehicle hardware authenticated.")
            print("[*] Cloud issued secure command to begin heavy SNN training cycle.")

            # ─────────────────────────────────────────────────────────────────
            # GATING MECHANISM
            # Hard assertion: if the state machine is not in VERIFIED state,
            # we do NOT construct or transmit any ML payload whatsoever.
            # The src/ml blackbox is never invoked until this gate is open.
            # ─────────────────────────────────────────────────────────────────
            if self.state_machine.check_state() != HandshakeState.VERIFIED:
                print("[!] GATING MECHANISM: State not VERIFIED. Telemetry LOCKED. Shutting down.")
                return False

            print("[+] ✓ GATE OPEN — Hardware identity confirmed. Telemetry pipeline unlocked.")

            # 4. Construct Payload using Scalable Factory (Simulates SNN ML payload computation)
            #    Note: PayloadFactory bridges to the ML pipeline; src/ml is never modified here.
            raw_payload = PayloadFactory.build(payload_type)

            # 5. Wrap into Secure Payload Envelope with Anti-Replay Nonce/Timestamp + HMAC Signature
            secure_envelope = SecurePayloadEnvelope.create(
                vehicle_id=self.vehicle_id,
                payload_type=payload_type,
                payload_data=raw_payload,
                challenge_seed=cloud_challenge,
                session_key=self.session_key
            )

            print("\n[+] Secure Envelope successfully constructed:")
            print(f"    Payload ID   : {secure_envelope['payload_id']}")
            print(f"    Nonce        : {secure_envelope['nonce']}")
            print(f"    Timestamp    : {secure_envelope['timestamp']}")
            print(f"    HMAC Sig     : {secure_envelope['signature'][:16]}...")

            # 6. Safe Transmission via Cloud Adapter Interface
            print(f"\n[*] Transmitting secure payload to cloud via {self.adapter.__class__.__name__}...")
            success = self.adapter.send(secure_envelope)

            if success:
                print("[+] Payload transmission completed safely.")
            else:
                print("[!] Transmission failed on transport layer.")
                
            return success

        except SystemError as e:
            print(f"[!] SECURITY CRITICAL FAILURE: {e}")
            return False

    def run_ota_renewal(self) -> bool:
        """
        Triggers OTA re-enrollment using the session key from the last successful handshake.
        Must be called after a successful run() to have a valid session_key.
        """
        if self.session_key is None:
            print("[!] OTA renewal requires a valid session. Run handshake first.")
            return False

        print(f"\n[*] Starting OTA Re-enrollment for Vehicle {self.vehicle_id}...")
        handler = OTAReenrollmentHandler(
            vehicle_id=self.vehicle_id,
            puf_module=self.puf_module,
            adapter=self.adapter,
            session_key=self.session_key
        )
        return handler.run()

def main():
    vehicle_id = os.getenv("VEHICLE_ID", "42")
    payload_type = os.getenv("PAYLOAD_TYPE", "MODEL_UPDATE")
    run_ota = os.getenv("RUN_OTA_RENEWAL", "false").lower() == "true"
    
    node = VehicleNode(vehicle_id=vehicle_id)
    success = node.run(payload_type=payload_type)

    if success and run_ota:
        node.run_ota_renewal()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()