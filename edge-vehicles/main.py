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
    Edge Vehicle orchestrator.

    The vehicle performs the PUF handshake once and keeps the
    resulting session key for subsequent secure payloads.
    """

    def __init__(self, vehicle_id: str, challenge_seed: int = 12345):
        self.vehicle_id = vehicle_id
        self.challenge_seed = challenge_seed
        self.state_machine = RedundantStateMachine()

        old_env = os.environ.get("VEHICLE_ID")
        os.environ["VEHICLE_ID"] = str(self.vehicle_id)

        self.puf_module = VehiclePUF()

        if old_env is not None:
            os.environ["VEHICLE_ID"] = old_env
        else:
            os.environ.pop("VEHICLE_ID", None)

        self.adapter = AdapterFactory.create_adapter()
        self.adapter.connect()

        # Session information is established during authenticate().
        self.session_key = None
        self.cloud_challenge = None
        self.authenticated = False

    def authenticate(self):
        """
        Perform the PUF authentication handshake once.

        Returns True if the vehicle is successfully authenticated.
        """

        if self.authenticated:
            return True

        print(
            f"\n[*] Booting Edge Node for Vehicle ID: "
            f"{self.vehicle_id}"
        )

        try:
            print(
                "[*] Initiating Hardware PUF Handshake sequence..."
            )

            self.state_machine.transition_to(
                HandshakeState.CHALLENGE_ISSUED
            )
            self.state_machine.check_state()

            # Request to join.
            join_resp = self.adapter.request_join(
                self.vehicle_id
            )

            if join_resp.get("status") != "authorized":
                print(
                    "[!] Cloud gateway rejected the connection: "
                    f"{join_resp.get('reason')}"
                )
                return False

            self.cloud_challenge = join_resp.get(
                "challenge"
            )

            print(
                f"[+] Received Challenge from Cloud: "
                f"{self.cloud_challenge}"
            )

            # Compute PUF response.
            _, response = self.puf_module.get_response(
                self.cloud_challenge
            )

            self.state_machine.transition_to(
                HandshakeState.RESPONSE_COMPUTED
            )
            self.state_machine.check_state()

            # Derive session key.
            self.session_key = (
                CryptographicSigner.derive_session_key(
                    response
                )
            )

            print(
                f"[+] Derived Hardware Session Key: "
                f"{self.session_key[:12]}..."
            )

            # Send signed proof.
            proof_signature = (
                CryptographicSigner.generate_signature(
                    {"heartbeat": self.cloud_challenge},
                    self.session_key
                )
            )

            if not self.adapter.send_proof(
                self.vehicle_id,
                self.cloud_challenge,
                proof_signature
            ):
                print(
                    "[!] Cloud gateway rejected the PUF proof. "
                    "Unauthorized vehicle."
                )

                self.session_key = None
                return False

            self.state_machine.transition_to(
                HandshakeState.VERIFIED
            )

            current_state = self.state_machine.check_state()

            print(
                f"[+] Handshake Verified "
                f"(State: {current_state.name}). "
                f"Vehicle hardware authenticated."
            )

            self.authenticated = True

            return True

        except SystemError as e:
            print(
                f"[!] SECURITY CRITICAL FAILURE: {e}"
            )

            self.session_key = None
            self.authenticated = False

            return False

    def send_payload(
        self,
        payload_type: str,
        detection_result: dict = None
    ):
        """
        Build and securely transmit a payload using the
        already-established session key.
        """

        if not self.authenticated:
            print(
                "[!] Vehicle is not authenticated."
            )
            return False

        if self.session_key is None:
            print(
                "[!] No active session key."
            )
            return False

        try:
            # -----------------------------------------------------
            # 1. Construct payload
            # -----------------------------------------------------
            raw_payload = PayloadFactory.build(
                payload_type,
                detection_result=detection_result
            )

            print("\n[+] Payload constructed:")

            for key, value in raw_payload.items():
                print(
                    f"    {key}: {value}"
                )

            # -----------------------------------------------------
            # 2. Create secure envelope
            # -----------------------------------------------------
            secure_envelope = SecurePayloadEnvelope.create(
                vehicle_id=self.vehicle_id,
                payload_type=payload_type,
                payload_data=raw_payload,
                challenge_seed=self.cloud_challenge,
                session_key=self.session_key
            )

            print(
                "\n[+] Secure Envelope successfully constructed:"
            )

            print(
                f"    Payload ID   : "
                f"{secure_envelope['payload_id']}"
            )

            print(
                f"    Nonce        : "
                f"{secure_envelope['nonce']}"
            )

            print(
                f"    Timestamp    : "
                f"{secure_envelope['timestamp']}"
            )

            print(
                f"    HMAC Sig     : "
                f"{secure_envelope['signature'][:16]}..."
            )

            # -----------------------------------------------------
            # 3. Transmit
            # -----------------------------------------------------
            print(
                f"\n[*] Transmitting secure payload to cloud "
                f"via {self.adapter.__class__.__name__}..."
            )

            success = self.adapter.send(
                secure_envelope
            )

            if success:
                print(
                    "[+] Payload transmission completed safely."
                )
            else:
                print(
                    "[!] Transmission failed on transport layer."
                )

            return success

        except SystemError as e:
            print(
                f"[!] SECURITY CRITICAL FAILURE: {e}"
            )
            return False

    def run(
        self,
        payload_type: str = "MODEL_UPDATE",
        detection_result: dict = None
    ):
        """
        Backward-compatible single-run interface.

        Performs authentication and then sends one payload.
        """

        if not self.authenticate():
            return False

        return self.send_payload(
            payload_type=payload_type,
            detection_result=detection_result
        )


def main():
    vehicle_id = os.getenv(
        "VEHICLE_ID",
        "42"
    )

    payload_type = os.getenv(
        "PAYLOAD_TYPE",
        "MODEL_UPDATE"
    )

    node = VehicleNode(
        vehicle_id=vehicle_id
    )

    success = node.run(
        payload_type=payload_type
    )

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()