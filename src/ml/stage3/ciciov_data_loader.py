import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader

class CICIoVDataset(Dataset):
    def __init__(self, file_path, window_size=29):
        self.file_path = file_path
        self.window_size = window_size
        
        print(f"Loading CICIoV data from {file_path}...")
        # Read only required columns to save memory
        cols = ['ID', 'DATA_0', 'DATA_1', 'DATA_2', 'DATA_3', 'DATA_4', 'DATA_5', 'DATA_6', 'DATA_7', 'specific_class']
        self.data = pd.read_csv(file_path, usecols=cols)
        
        # Mapping specific_class to integer labels
        label_map = {
            'BENIGN': 0,
            'DoS': 1,
            'spoofing-GAS': 2,
            'spoofing-RPM': 3,
            'spoofing-SPEED': 4,
            'spoofing-STEERING_WHEEL': 5
        }
        self.data['Label'] = self.data['specific_class'].map(label_map).fillna(0).astype(int)
        
        # Normalize numeric features
        # Normalize ID (Standard CAN ID max is 2047)
        self.data['ID'] = self.data['ID'] / 2047.0
        
        # Normalize DATA bytes (0-255)
        for i in range(8):
            self.data[f'DATA_{i}'] = self.data[f'DATA_{i}'] / 255.0
            
        self.features = self.data[['ID', 'DATA_0', 'DATA_1', 'DATA_2', 'DATA_3', 'DATA_4', 'DATA_5', 'DATA_6', 'DATA_7']].values
        self.labels = self.data['Label'].values
        
        self.num_samples = len(self.features) - self.window_size + 1

    def __len__(self):
        return max(0, self.num_samples)

    def __getitem__(self, idx):
        x_seq = self.features[idx:idx + self.window_size]
        y_seq = self.labels[idx:idx + self.window_size]
        
        x_tensor = torch.tensor(x_seq, dtype=torch.float32)
        y_tensor = torch.tensor(y_seq.max(), dtype=torch.long)
        
        return x_tensor, y_tensor

def get_ciciov_dataloader(file_path, batch_size=256, window_size=29, shuffle=True):
    dataset = CICIoVDataset(file_path, window_size=window_size)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=0)
