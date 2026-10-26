import os
import csv
import hashlib
import numpy as np

class VehiclePUF:
    def __init__(self, csv_filepath=None):
        # Read the Vehicle ID from the environment (e.g., "101", "102")
        self.vehicle_id = os.getenv("VEHICLE_ID", "101")
        self.crp_database = {}
        
        # Resolve path to the Verilog-generated CSV
        if csv_filepath is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            csv_filepath = os.path.join(base_dir, 'data', 'puf_crp_export.csv')

        self._load_hardware_data(csv_filepath)

    def _load_hardware_data(self, csv_filepath):
        try:
            with open(csv_filepath, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    challenge_hex = row.get('challenge_hex') or row.get('challenge_bin')
                    
                    for column_name, hex_response in row.items():
                        if 'vid' in column_name:
                            vid = column_name.split('vid')[-1]
                            if vid not in self.crp_database:
                                self.crp_database[vid] = {}
                                
                            # Convert 8-character hex to a 32-bit numpy array for the SNN
                            try:
                                bin_string = bin(int(hex_response, 16))[2:].zfill(32)
                            except ValueError:
                                bin_string = str(hex_response).zfill(32)
                            # SNNs typically expect bipolar (-1, 1) or binary (0, 1) inputs
                            bin_array = np.array([1.0 if bit == '1' else 0.0 for bit in bin_string], dtype=np.float32)
                            self.crp_database[vid][challenge_hex] = bin_array
        except FileNotFoundError:
            raise RuntimeError(f"Hardware PUF data missing at {csv_filepath}. Run Verilog simulation first.")

    def get_response(self, challenge_hex):
        """Returns the hardware-accurate 32-bit response for the VSOC challenge."""
        vehicle_data = self.crp_database.get(str(self.vehicle_id))
        
        # If vehicle not in enrolled hardware database (e.g., un-enrolled / spoofed vehicle in Sybil attack testing)
        if not vehicle_data:
            h = hashlib.sha256(f"VID_{self.vehicle_id}_{challenge_hex}".encode()).digest()
            bin_string = ''.join(format(byte, '08b') for byte in h[:4])
            bin_array = np.array([1.0 if bit == '1' else 0.0 for bit in bin_string], dtype=np.float32)
            return challenge_hex, bin_array
            
        # If challenge is directly in dataset
        response = vehicle_data.get(str(challenge_hex))
        if response is None:
            # Map integer seed or un-indexed challenge deterministically to an available hardware CRP
            challenges = list(vehicle_data.keys())
            if isinstance(challenge_hex, (int, np.integer)):
                idx = int(challenge_hex) % len(challenges)
            else:
                idx = int(hashlib.md5(str(challenge_hex).encode()).hexdigest(), 16) % len(challenges)
            response = vehicle_data[challenges[idx]]
            
        # Return tuple to match the legacy signature expectations in main.py
        return challenge_hex, response