from enum import Enum

class HandshakeState(Enum):
    INIT = 1
    CHALLENGE_ISSUED = 2
    RESPONSE_COMPUTED = 3
    VERIFIED = 4

class RedundantStateMachine:
    def __init__(self):
        self.state_a = HandshakeState.INIT
        self.state_b = HandshakeState.INIT
        self.state_c = HandshakeState.INIT

    def transition_to(self, target_state):
        self.state_a = self.state_b = self.state_c = target_state

    def check_state(self):
        votes = {state: 0 for state in HandshakeState}
        votes[self.state_a] += 1
        votes[self.state_b] += 1
        votes[self.state_c] += 1
        
        majority_state = max(votes, key=votes.get)
        
        if votes[majority_state] != 3:
            raise SystemError("CRITICAL: Fault-injection detected! Failing safe.")
        
        return majority_state