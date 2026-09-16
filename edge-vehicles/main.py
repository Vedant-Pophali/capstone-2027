import os
from puf_simulator import VehiclePUF
from state_machine import RedundantStateMachine, HandshakeState
from crypto_signer import CryptographicSigner

def main():
    vehicle_id = os.getenv("VEHICLE_ID", "42")
    print(f"[*] Booting Edge Node for Vehicle ID: {vehicle_id}")

    # 1. Initialize Components
    state_machine = RedundantStateMachine()
    puf_module = VehiclePUF()
    challenge_seed = 12345  # Simulated incoming challenge from the cloud aggregator

    try:
        # 2. Begin Handshake Protocol
        print("[*] Initiating PUF Handshake sequence...")
        state_machine.transition_to(HandshakeState.CHALLENGE_ISSUED)
        state_machine.check_state()

        # 3. Compute Hardware Response
        challenge, response = puf_module.get_response(challenge_seed)
        state_machine.transition_to(HandshakeState.RESPONSE_COMPUTED)
        state_machine.check_state()

        # 4. Derive Per-Round Session Key
        session_key = CryptographicSigner.derive_session_key(response)
        print(f"[+] Derived Session Key: {session_key[:12]}...")

        state_machine.transition_to(HandshakeState.VERIFIED)
        state_machine.check_state()
        print("[+] Handshake Verified. Vehicle container mathematically authenticated.")

        # 5. Simulate SNN Payload Signing (Protecting against Fleet Poisoning)
        print("[*] Simulating Local SNN-IDS Update...")
        dummy_snn_weights = {"layer_1": [0.01, -0.05], "layer_2": [0.1, 0.2]}
        secure_payload = CryptographicSigner.sign_payload(dummy_snn_weights, session_key)
        
        print("[+] Payload cryptographically signed and ready for Go Gateway transmission:")
        print(secure_payload)

    except SystemError as e:
        # This block catches any state mismatches and fails safe instead of transmitting[cite: 1].
        print(f"[!] {e}")

if __name__ == "__main__":
    main()