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
    """Deterministic fallback ArbiterPUF simulation if pypuf library is not installed.
    
    Returns a full n-bit response derived from SHA-256(seed || challenge_bytes)
    so that every distinct vehicle_id seed produces a cryptographically unique key.
    """
    def __init__(self, n=64, seed=42):
        self.n = n
        self.seed = seed

    def eval(self, challenge):
        # Challenge is a 2D numpy array (1, n) with elements in {-1, 1}
        ch_bytes = challenge.tobytes()
        # Use SHA-256 to generate enough entropy for n bits
        digest = hashlib.sha256(f"{self.seed}".encode() + ch_bytes).digest()
        # Expand digest to n bits using repeated hashing if needed
        bits = []
        block = digest
        while len(bits) < self.n:
            bits.extend([1 if b % 2 == 0 else -1 for b in block])
            block = hashlib.sha256(block).digest()
        return np.array(bits[:self.n])


class VehiclePUF:
    def __init__(self, challenge_length=64):
        self.challenge_length = challenge_length
        raw_id = os.getenv("VEHICLE_ID", "42")
        # Support both numeric IDs (42) and string IDs ("vehicle_42").
        # For non-numeric IDs we derive a stable integer seed via SHA-256
        # so the PUF remains deterministic and unique per vehicle.
        try:
            self.vehicle_id = int(raw_id)
        except ValueError:
            import hashlib
            self.vehicle_id = int(hashlib.sha256(raw_id.encode()).hexdigest(), 16) % (2**31)
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