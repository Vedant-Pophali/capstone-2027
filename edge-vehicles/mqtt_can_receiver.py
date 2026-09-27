import json
from collections import deque

import numpy as np
import paho.mqtt.client as mqtt

from can_detector import CANDetector
from main import VehicleNode


class MQTTCANReceiver:
    def __init__(
        self,
        detector,
        vehicle_id="42",
        host="127.0.0.1",
        port=1883,
        topic="fleet/vehicle/1/can/in",
    ):
        self.detector = detector
        self.vehicle_id = vehicle_id
        self.host = host
        self.port = port
        self.topic = topic

        self.window = deque(
            maxlen=detector.window_size
        )

        self.previous_timestamp = None
        self.windows_processed = 0

        # VehicleNode provides the existing PUF + secure
        # envelope + cloud transmission pipeline.
        self.vehicle_node = VehicleNode(
            vehicle_id=vehicle_id
        )
        if not self.vehicle_node.authenticate():
            raise RuntimeError(
                "Vehicle PUF authentication failed."
            )

        self.client = mqtt.Client()

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(
                f"[mqtt] connected; subscribing to {self.topic}"
            )
            client.subscribe(self.topic)
        else:
            print(
                f"[mqtt] connection failed: {rc}"
            )

    def _on_message(self, client, userdata, message):
        try:
            frame = json.loads(
                message.payload.decode("utf-8")
            )

            feature = self.detector.frame_to_features(
                frame,
                self.previous_timestamp,
            )

            self.previous_timestamp = float(
                frame["timestamp"]
            )

            self.window.append(feature)

            if len(self.window) < self.detector.window_size:
                return

            window = np.asarray(
                self.window,
                dtype=np.float32,
            )

            result = self.detector.classify(window)

            self.windows_processed += 1

            print(
                f"[mqtt] window={self.windows_processed} "
                f"class={result['label']} "
                f"confidence={result['confidence']:.3f} "
                f"attack={result['is_attack']}"
            )

            # ---------------------------------------------------------
            # Forward detected attacks into the existing secure
            # vehicle-to-cloud pipeline.
            # ---------------------------------------------------------
            if result["is_attack"]:
                print(
                    "[security] Attack detected. "
                    "Creating secure threat alert..."
                )

                success = self.vehicle_node.send_payload(
                    payload_type="THREAT_ALERT",
                    detection_result=result,
                )

                if success:
                    print(
                        "[security] Threat alert securely "
                        "transmitted."
                    )
                else:
                    print(
                        "[security] Failed to transmit "
                        "threat alert."
                    )

        except Exception as exc:
            print(
                f"[mqtt] frame processing error: {exc}"
            )
    def start(self):
            print(
                f"[mqtt] connecting to "
                f"{self.host}:{self.port}"
            )

            self.client.connect(
                self.host,
                self.port,
                60,
            )

            print("[mqtt] waiting for CAN frames...")

            self.client.loop_forever()


def main():
    detector = CANDetector()

    vehicle_id = "42"

    receiver = MQTTCANReceiver(
        detector=detector,
        vehicle_id=vehicle_id,
    )

    receiver.start()


if __name__ == "__main__":
    main()