import os
import sys
import numpy as np
import torch

# Allow imports from src/ml
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ML_ROOT = os.path.join(PROJECT_ROOT, "src", "ml")

if ML_ROOT not in sys.path:
    sys.path.insert(0, ML_ROOT)

from stage1.cnn1d import CAN1DCNN


CLASS_NAMES = [
    "BENIGN",
    "DoS",
    "Fuzzing",
    "Gear",
    "RPM",
    "Speed",
    "Standstill",
    "Systematic",
    "Combined",
    "Interval",
]


class CANDetector:
    def __init__(self, model_path=None, window_size=29):
        self.window_size = window_size

        if model_path is None:
            model_path = os.path.join(
                ML_ROOT,
                "models",
                "stage4_global_model.pth"
            )

        self.model_path = model_path

        self.model = CAN1DCNN(
            num_features=11,
            num_classes=10
        )

        self.model.load_state_dict(
            torch.load(
                self.model_path,
                map_location="cpu"
            )
        )

        self.model.eval()

        print(f"[detector] Loaded CNN: {self.model_path}")

    @staticmethod
    def frame_to_features(frame, previous_timestamp=None):
        timestamp = float(frame["timestamp"])

        can_id = int(str(frame["can_id"]), 16)

        dlc = int(frame.get("dlc", 0))

        data_hex = str(frame.get("data", ""))

        data_hex = data_hex[:16].ljust(16, "0")

        data_bytes = [
            int(data_hex[i:i + 2], 16)
            for i in range(0, 16, 2)
        ]

        if previous_timestamp is None:
            iat = 0.0
        else:
            iat = timestamp - previous_timestamp

        features = [
            iat,
            can_id / 2047.0,
            dlc / 8.0,
        ]

        features.extend(
            byte_value / 255.0
            for byte_value in data_bytes
        )

        return np.asarray(features, dtype=np.float32)

    @torch.no_grad()
    def classify(self, window):
        """
        window shape: (29, 11)
        """

        if window.shape != (self.window_size, 11):
            raise ValueError(
                f"Expected ({self.window_size}, 11), "
                f"got {window.shape}"
            )

        x = torch.tensor(
            window,
            dtype=torch.float32
        ).unsqueeze(0)

        logits = self.model(x)

        probabilities = torch.softmax(
            logits,
            dim=1
        )[0]

        class_id = int(
            torch.argmax(probabilities).item()
        )

        confidence = float(
            probabilities[class_id].item()
        )

        return {
            "class_id": class_id,
            "label": CLASS_NAMES[class_id],
            "confidence": confidence,
            "is_attack": class_id != 0,
        }
if __name__ == "__main__":
    import csv

    print("[test] Creating CAN detector...")
    detector = CANDetector()

    dataset_path = os.path.join(
        PROJECT_ROOT,
        "datasets",
        "hcrl",
        "fuzzy_dataset.csv"
    )

    print("[test] Dataset:", dataset_path)

    features = []
    previous_timestamp = None

    with open(dataset_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)

        for row in reader:
            if len(row) < 12:
                continue

            try:
                timestamp = float(row[0])
                can_id = row[1].strip()
                dlc = int(row[2])

                data_bytes = [
                    value.strip()
                    for value in row[3:11]
                ]

                data_hex = "".join(data_bytes)

                frame = {
                    "timestamp": timestamp,
                    "can_id": can_id,
                    "dlc": dlc,
                    "data": data_hex,
                }

                feature = detector.frame_to_features(
                    frame,
                    previous_timestamp
                )

                features.append(feature)
                previous_timestamp = timestamp

            except (ValueError, IndexError):
                continue

            if len(features) >= detector.window_size:
                break

    window = np.asarray(
        features[:detector.window_size],
        dtype=np.float32
    )

    print("[test] Window shape:", window.shape)

    result = detector.classify(window)

    print("[test] Detection result:")
    print("       class:", result["label"])
    print("       confidence:", result["confidence"])
    print("       attack:", result["is_attack"])