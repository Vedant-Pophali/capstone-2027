import os
from pypuf.simulation import ArbiterPUF
from pypuf.io import random_inputs

class VehiclePUF:
    def __init__(self, challenge_length=64):
        self.challenge_length = challenge_length
        self.vehicle_id = int(os.getenv("VEHICLE_ID", "42"))
        self.puf = ArbiterPUF(n=self.challenge_length, seed=self.vehicle_id)

    def get_response(self, challenge_seed):
        challenge = random_inputs(n=self.challenge_length, N=1, seed=challenge_seed)
        response = self.puf.eval(challenge)
        return challenge, response