import os
import glob
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import Dataset, DataLoader, ConcatDataset
from tqdm import tqdm
import sys

# Ensure we can import cnn1d
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cnn1d import CAN1DCNN

class GlobalCANDataset(Dataset):
    def __init__(self, file_path, label, window_size=29):
        self.file_path = file_path
        self.window_size = window_size
        
        # User Request: Take EXACTLY the first 10,000 rows from EACH csv file
        try:
            self.data = pd.read_csv(file_path, nrows=10000)
        except Exception as e:
            self.data = pd.DataFrame()
            
        if self.data.empty or len(self.data) < window_size:
            self.num_samples = 0
            return
            
        # Feature Extraction: IAT
        self.data['IAT'] = self.data['timestamp'].diff().fillna(0)
        
        # Feature Extraction: ID (Normalized)
        self.data['ID'] = self.data['arbitration_id'].apply(lambda x: int(str(x), 16) if pd.notnull(x) else 0) / 2047.0
        
        # Feature Extraction: Payload (DATA_0 to DATA_7)
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
        self.data[['DATA_0', 'DATA_1', 'DATA_2', 'DATA_3', 'DATA_4', 'DATA_5', 'DATA_6', 'DATA_7', 'DLC']] = pd.DataFrame(parsed_data.tolist(), index=self.data.index)
        
        self.features = self.data[['IAT', 'ID', 'DLC', 'DATA_0', 'DATA_1', 'DATA_2', 'DATA_3', 'DATA_4', 'DATA_5', 'DATA_6', 'DATA_7']].values
        self.labels = np.full(len(self.features), label)
        
        self.num_samples = len(self.features) - self.window_size + 1

    def __len__(self):
        return max(0, getattr(self, 'num_samples', 0))

    def __getitem__(self, idx):
        x_seq = self.features[idx:idx + self.window_size]
        y_seq = self.labels[idx:idx + self.window_size]
        
        x_tensor = torch.tensor(x_seq, dtype=torch.float32)
        y_tensor = torch.tensor(y_seq.max(), dtype=torch.long)
        return x_tensor, y_tensor

def main():
    print("=== PUF-CP-IDS: Global Stage 1 CNN Retraining ===")
    
    # 10 Class Label Map
    label_map = {
        'attack-free': 0, 'extra-attack-free': 0,
        'DoS-attacks': 1, 'fuzzing-attacks': 2,
        'gear-attacks': 3, 'rpm-attacks': 4,
        'speed-attacks': 5, 'standstill-attacks': 6,
        'systematic-attacks': 7, 'combined-attacks': 8,
        'interval-attacks': 9
    }
    
    dataset_dir = r"e:\capstone-2027\can_noniid_data"
    csv_files = glob.glob(os.path.join(dataset_dir, "**", "*.csv"), recursive=True)
    print(f"Found {len(csv_files)} CSV files across all vehicles and attack types.")
    
    all_datasets = []
    # Build the Massive Dataset
    for file_path in tqdm(csv_files, desc="Parsing Datasets (10,000 rows each)"):
        parent_folder = os.path.basename(os.path.dirname(file_path))
        label = label_map.get(parent_folder, 0)
        
        ds = GlobalCANDataset(file_path, label)
        if len(ds) > 0:
            all_datasets.append(ds)
            
    combined_dataset = ConcatDataset(all_datasets)
    print(f"\nTotal robust sequences ready for training: {len(combined_dataset)}")
    
    dataloader = DataLoader(combined_dataset, batch_size=256, shuffle=True, num_workers=0)
    
    # Initialize Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = CAN1DCNN(num_features=11, num_classes=10).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.CrossEntropyLoss()
    
    # Train
    epochs = 3
    print("\nStarting Global Training Loop...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch_idx, (inputs, targets) in enumerate(dataloader):
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
            if batch_idx % 50 == 0:
                print(f"Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(dataloader)} | Loss: {loss.item():.4f}")
                
        acc = 100. * correct / total
        print(f"==> Epoch {epoch+1} Complete | Average Loss: {total_loss/len(dataloader):.4f} | Accuracy: {acc:.2f}%\n")
        
    # Save the robust model
    os.makedirs(r"e:\capstone-2027\src\ml\models", exist_ok=True)
    save_path = r"e:\capstone-2027\src\ml\models\stage1_cnn1d_model.pth"
    torch.save(model.state_dict(), save_path)
    print(f"SUCCESS: Robust Baseline Model saved to {save_path}")

if __name__ == "__main__":
    main()
