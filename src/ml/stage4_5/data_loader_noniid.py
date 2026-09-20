import os
import glob
import pandas as pd
import torch
import numpy as np
from torch.utils.data import Dataset, DataLoader, ConcatDataset
from tqdm import tqdm

class NonIIDCANDataset(Dataset):
    def __init__(self, file_path, label, window_size=29):
        self.file_path = file_path
        self.window_size = window_size
        # Read only up to 50,000 rows to prevent Out of Memory crashes
        self.data = pd.read_csv(file_path, nrows=50000)
        
        # Calculate IAT
        self.data['IAT'] = self.data['timestamp'].diff().fillna(0)
        
        # Parse Arbitration ID (Hex to Int)
        self.data['ID'] = self.data['arbitration_id'].apply(lambda x: int(str(x), 16) if pd.notnull(x) else 0) / 2047.0
        
        # Parse Data Field (Hex string to up to 8 integer bytes)
        def parse_data(hex_str):
            hex_str = str(hex_str)
            if hex_str == 'nan':
                return [0]*8 + [0]
            
            byte_len = len(hex_str) // 2
            bytes_list = []
            for i in range(8):
                if i < byte_len:
                    byte_val = int(hex_str[i*2:i*2+2], 16)
                    bytes_list.append(byte_val / 255.0)
                else:
                    bytes_list.append(0.0)
            return bytes_list + [byte_len / 8.0]
            
        parsed_data = self.data['data_field'].apply(parse_data)
        
        # Expand parsed data into columns
        self.data[['DATA_0', 'DATA_1', 'DATA_2', 'DATA_3', 'DATA_4', 'DATA_5', 'DATA_6', 'DATA_7', 'DLC']] = pd.DataFrame(parsed_data.tolist(), index=self.data.index)
        
        # Extract features (11 total)
        self.features = self.data[['IAT', 'ID', 'DLC', 'DATA_0', 'DATA_1', 'DATA_2', 'DATA_3', 'DATA_4', 'DATA_5', 'DATA_6', 'DATA_7']].values
        
        # All rows in this specific file share the same label based on the folder they came from
        self.labels = np.full(len(self.features), label)
        
        self.num_samples = len(self.features) - self.window_size + 1

    def __len__(self):
        return max(0, self.num_samples)

    def __getitem__(self, idx):
        x_seq = self.features[idx:idx + self.window_size]
        y_seq = self.labels[idx:idx + self.window_size]
        
        x_tensor = torch.tensor(x_seq, dtype=torch.float32)
        y_tensor = torch.tensor(y_seq.max(), dtype=torch.long)
        
        return x_tensor, y_tensor

def get_vehicle_dataloader(vehicle_dir, batch_size=256, window_size=29):
    """
    Recursively scans the vehicle directory, loading every single CSV file found,
    dynamically assigning labels based on folder structure.
    """
    all_datasets = []
    
    label_map = {
        'attack-free': 0,
        'extra-attack-free': 0,
        'DoS-attacks': 1,
        'fuzzing-attacks': 2,
        'gear-attacks': 3,
        'rpm-attacks': 4,
        'speed-attacks': 5,
        'standstill-attacks': 6,
        'systematic-attacks': 7,
        'combined-attacks': 8,
        'interval-attacks': 9
    }
    
    # Recursively find all csv files
    search_path = os.path.join(vehicle_dir, '**', '*.csv')
    csv_files = glob.glob(search_path, recursive=True)
    
    print(f"Found {len(csv_files)} CSV files for vehicle {os.path.basename(vehicle_dir)}")
    
    # Load a limited subset of files to prevent Out of Memory (OOM) laptop crashes
    category_counts = {k: 0 for k in label_map.keys()}
    max_files_per_category = 1 # Only load 1 massive CSV per attack type
    
    for file_path in tqdm(csv_files, desc="Parsing vehicle CSVs"):
        parent_folder = os.path.basename(os.path.dirname(file_path))
        label = label_map.get(parent_folder, 0)
        
        # Check if we already have enough files for this category to save RAM
        if parent_folder in category_counts and category_counts[parent_folder] >= max_files_per_category:
            continue
            
        try:
            # We also limit pandas to only read the first 50,000 rows of the CSV file
            ds = NonIIDCANDataset(file_path, label, window_size=window_size)
            if len(ds) > 0:
                all_datasets.append(ds)
                if parent_folder in category_counts:
                    category_counts[parent_folder] += 1
        except Exception as e:
            pass # Skip corrupted files if any
            
    if not all_datasets:
        raise ValueError(f"No valid datasets loaded for vehicle {vehicle_dir}!")
        
    combined_dataset = ConcatDataset(all_datasets)
    print(f"Total sequences loaded for client: {len(combined_dataset)}")
    
    return DataLoader(combined_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
