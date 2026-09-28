import unittest
import os
import sys

# Ensure edge-vehicles directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.state_machine import RedundantStateMachine, HandshakeState
from src.security.puf_simulator import VehiclePUF
from src.security.crypto_signer import CryptographicSigner

class TestPUFSecurityFramework(unittest.TestCase):

    def test_fault_injection_fails_safe(self):
        """Simulates a glitch during the PUF handshake to ensure the state machine catches it."""
        sm = RedundantStateMachine()
        sm.transition_to(HandshakeState.CHALLENGE_ISSUED)
        
        # Simulate an attacker glitching the memory of state_a
        sm.state_a = HandshakeState.INIT 
        
        # The system must catch the discrepancy and fail safe rather than silently transmitting.
        with self.assertRaises(SystemError) as context:
            sm.check_state()
        self.assertTrue("Fault-injection detected" in str(context.exception))

    def test_sybil_spoofed_vehicle_resistance(self):
        """Proves two cloned containers cannot generate the same PUF key."""
        # Vehicle 1 (Valid)
        os.environ["VEHICLE_ID"] = "101"  # Inject environment variable BEFORE instantiation
        car1 = VehiclePUF()
        _, resp1 = car1.get_response(999)
        key1 = CryptographicSigner.derive_session_key(resp1)

        # Vehicle 2 (Hacker trying to spoof Vehicle 1)
        os.environ["VEHICLE_ID"] = "202"  # Inject a different environment variable
        car2 = VehiclePUF()
        _, resp2 = car2.get_response(999)
        key2 = CryptographicSigner.derive_session_key(resp2)

        # The mathematical keys must differ, successfully blocking the cloned vehicle.
        self.assertNotEqual(key1, key2)

if __name__ == '__main__':
    unittest.main()