import os
import hashlib
import numpy as np

try:
    from pypuf.simulation import ArbiterPUF
    from pypuf.io import random_inputs
    HAS_PYPUF = True
except ImportError:
    HAS_PYPUF = False

class FallbackSimulatedPUF:
    """Deterministic fallback ArbiterPUF simulation if pypuf library is not installed."""
    def __init__(self, n=64, seed=42):
        self.n = n
        self.seed = seed

    def eval(self, challenge):
        # Challenge is a 2D numpy array (1, n) with elements in {-1, 1}
        # Compute deterministic challenge-response using seed and challenge bits
        ch_bytes = challenge.tobytes()
        h = hashlib.sha256(f"{self.seed}".encode() + ch_bytes).digest()
        # Convert first byte to response array in {-1, 1}
        bit = 1 if h[0] % 2 == 1 else -1
        return np.array([bit])

class VehiclePUF:
    def __init__(self, challenge_length=64):
        self.challenge_length = challenge_length
        self.vehicle_id = int(os.getenv("VEHICLE_ID", "42"))
        if HAS_PYPUF:
            self.puf = ArbiterPUF(n=self.challenge_length, seed=self.vehicle_id)
        else:
            self.puf = FallbackSimulatedPUF(n=self.challenge_length, seed=self.vehicle_id)

    def get_response(self, challenge_seed):
        if HAS_PYPUF:
            challenge = random_inputs(n=self.challenge_length, N=1, seed=challenge_seed)
            response = self.puf.eval(challenge)
        else:
            np.random.seed(challenge_seed)
            challenge = np.random.choice([-1, 1], size=(1, self.challenge_length))
            response = self.puf.eval(challenge)
        return challenge, response