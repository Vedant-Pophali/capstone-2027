import time

class PayloadFactory:
    """
    Factory for generating different types of edge-vehicle payloads.
    Makes the system scalable for dozens of potential CAN bus alerts and statuses.
    """
    
    @staticmethod
    def build(payload_type: str) -> dict:
        payload_type = payload_type.upper()
        
        if payload_type == "THREAT_ALERT":
            return {
                "alert_id": "ALT-9001",
                "severity": "CRITICAL",
                "attack_type": "DoS_Injected_CAN_ID_0x000",
                "anomaly_score": 0.985,
                "timestamp_ms": int(time.time() * 1000)
            }
        elif payload_type == "MODEL_UPDATE":
            return {
                "layer_1_weights": [0.012, -0.045, 0.312, -0.110],
                "layer_2_weights": [0.104, 0.229, -0.003, 0.441],
                "num_samples": 500,
                "local_loss": 0.0341
            }
        elif payload_type == "HEARTBEAT":
            return {
                "status": "Healthy",
                "cpu_usage": "45%",
                "ram_usage": "32%"
            }
        else:
            raise ValueError(f"Unknown payload type: {payload_type}")
