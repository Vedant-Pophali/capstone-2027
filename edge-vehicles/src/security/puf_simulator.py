import os
import csv
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
                    challenge_hex = row['challenge_hex']
                    
                    for column_name, hex_response in row.items():
                        if 'vid' in column_name:
                            vid = column_name.split('vid')[-1]
                            if vid not in self.crp_database:
                                self.crp_database[vid] = {}
                                
                            # Convert 8-character hex to a 32-bit numpy array for the SNN
                            bin_string = bin(int(hex_response, 16))[2:].zfill(32)
                            # SNNs typically expect bipolar (-1, 1) or binary (0, 1) inputs
                            bin_array = np.array([1 if bit == '1' else 0 for bit in bin_string], dtype=np.float32)
                            self.crp_database[vid][challenge_hex] = bin_array
        except FileNotFoundError:
            raise RuntimeError(f"Hardware PUF data missing at {csv_filepath}. Run Verilog simulation first.")

    def get_response(self, challenge_hex):
        """Returns the hardware-accurate 32-bit response for the VSOC challenge."""
        vehicle_data = self.crp_database.get(str(self.vehicle_id))
        if not vehicle_data:
            raise ValueError(f"Vehicle ID {self.vehicle_id} not found in hardware dataset.")
            
        response = vehicle_data.get(challenge_hex)
        if response is None:
            raise ValueError(f"Challenge {challenge_hex} not computed for VID {self.vehicle_id}.")
            
        # Return tuple to match the legacy signature expectations in main.py
        return challenge_hex, response