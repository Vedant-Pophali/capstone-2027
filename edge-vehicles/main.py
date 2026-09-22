import os
import sys
from puf_simulator import VehiclePUF
from state_machine import RedundantStateMachine, HandshakeState
from crypto_signer import CryptographicSigner
from secure_envelope import SecurePayloadEnvelope
from cloud_adapter import AdapterFactory

def main():
    vehicle_id = os.getenv("VEHICLE_ID", "42")
    print(f"[*] Booting Edge Node for Vehicle ID: {vehicle_id}")

    # 1. Initialize Components & Cloud Transport Adapter
    state_machine = RedundantStateMachine()
    puf_module = VehiclePUF()
    challenge_seed = 12345  # Simulated incoming challenge from cloud aggregator
    
    # Instantiate configured Cloud Transport Adapter (e.g. Mock, HTTP, WebSocket)
    adapter = AdapterFactory.create_adapter()
    adapter.connect()

    try:
        # 2. Begin PUF Handshake Sequence
        print("[*] Initiating Hardware PUF Handshake sequence...")
        state_machine.transition_to(HandshakeState.CHALLENGE_ISSUED)
        state_machine.check_state()

        # 3. Compute Hardware Response
        challenge, response = puf_module.get_response(challenge_seed)
        state_machine.transition_to(HandshakeState.RESPONSE_COMPUTED)
        state_machine.check_state()

        # 4. Derive Per-Round Session Key
        session_key = CryptographicSigner.derive_session_key(response)
        print(f"[+] Derived Hardware Session Key: {session_key[:12]}...")

        state_machine.transition_to(HandshakeState.VERIFIED)
        current_state = state_machine.check_state()
        print(f"[+] Handshake Verified (State: {current_state.name}). Vehicle hardware authenticated.")

        # 5. Construct Sample Payloads (Support both Model Updates and Anomaly Alerts)
        payload_type = os.getenv("PAYLOAD_TYPE", "MODEL_UPDATE")
        
        if payload_type == "THREAT_ALERT":
            raw_payload = {
                "alert_id": "ALT-9001",
                "severity": "CRITICAL",
                "attack_type": "DoS_Injected_CAN_ID_0x000",
                "anomaly_score": 0.985,
                "timestamp_ms": 1726950000000
            }
        else:
            raw_payload = {
                "layer_1_weights": [0.012, -0.045, 0.312, -0.110],
                "layer_2_weights": [0.104, 0.229, -0.003, 0.441],
                "num_samples": 500,
                "local_loss": 0.0341
            }

        # 6. Wrap into Secure Payload Envelope with Anti-Replay Nonce/Timestamp + HMAC Signature
        secure_envelope = SecurePayloadEnvelope.create(
            vehicle_id=vehicle_id,
            payload_type=payload_type,
            payload_data=raw_payload,
            challenge_seed=challenge_seed,
            session_key=session_key
        )

        print("\n[+] Secure Envelope successfully constructed:")
        print(f"    Payload ID   : {secure_envelope['payload_id']}")
        print(f"    Nonce        : {secure_envelope['nonce']}")
        print(f"    Timestamp    : {secure_envelope['timestamp']}")
        print(f"    HMAC Sig     : {secure_envelope['signature']}")

        # 7. Safe Transmission via Cloud Adapter Interface
        # Transmission is strictly gated by redundant state machine sanity check
        print(f"\n[*] Transmitting secure payload to cloud via {adapter.__class__.__name__}...")
        success = adapter.send(secure_envelope)

        if success:
            print("[+] Payload transmission completed safely.")
        else:
            print("[!] Transmission failed on transport layer.")

    except SystemError as e:
        # Catches fault-injection state mismatches and aborts immediately to fail safe
        print(f"[!] SECURITY CRITICAL FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()