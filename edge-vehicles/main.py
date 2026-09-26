import os
import sys
from puf_simulator import VehiclePUF
from state_machine import RedundantStateMachine, HandshakeState
from crypto_signer import CryptographicSigner
from secure_envelope import SecurePayloadEnvelope
from cloud_adapter import AdapterFactory
from payload_factory import PayloadFactory

class VehicleNode:
    """
    Decoupled orchestrator for a single Edge Vehicle.
    Allows instantiating multiple independent simulated vehicles at scale.
    """
    def __init__(self, vehicle_id: str, challenge_seed: int = 12345):
        self.vehicle_id = vehicle_id
        self.challenge_seed = challenge_seed
        self.state_machine = RedundantStateMachine()
        
        # We need to temporarily set the environment variable so the PUF simulator 
        # picks up the right ID, since it defaults to using the env var currently.
        # (This can also be refactored inside VehiclePUF later for better injection).
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

            # 3. Derive Per-Round Session Key
            session_key = CryptographicSigner.derive_session_key(response)
            print(f"[+] Derived Hardware Session Key: {session_key[:12]}...")
            
            # 3a. Send lightweight proof (signed heartbeat)
            proof_signature = CryptographicSigner.generate_signature({"heartbeat": cloud_challenge}, session_key)
            if not self.adapter.send_proof(self.vehicle_id, cloud_challenge, proof_signature):
                print("[!] Cloud gateway rejected the PUF proof. Unauthorized vehicle.")
                return False

            self.state_machine.transition_to(HandshakeState.VERIFIED)
            current_state = self.state_machine.check_state()
            print(f"[+] Handshake Verified (State: {current_state.name}). Vehicle hardware authenticated.")
            print("[*] Cloud issued secure command to begin heavy SNN training cycle.")

            # 4. Construct Payload using Scalable Factory (Simulates SNN ML payload computation)
            raw_payload = PayloadFactory.build(payload_type)

            # 5. Wrap into Secure Payload Envelope with Anti-Replay Nonce/Timestamp + HMAC Signature
            secure_envelope = SecurePayloadEnvelope.create(
                vehicle_id=self.vehicle_id,
                payload_type=payload_type,
                payload_data=raw_payload,
                challenge_seed=cloud_challenge,
                session_key=session_key
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

def main():
    vehicle_id = os.getenv("VEHICLE_ID", "42")
    payload_type = os.getenv("PAYLOAD_TYPE", "MODEL_UPDATE")
    
    node = VehicleNode(vehicle_id=vehicle_id)
    success = node.run(payload_type=payload_type)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()