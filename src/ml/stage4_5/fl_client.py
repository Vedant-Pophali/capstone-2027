import sys
import os
import torch
import torch.nn as nn
import torch.optim as optim
import flwr as fl
from collections import OrderedDict
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage4_5.data_loader_noniid import get_vehicle_dataloader
from stage1.cnn1d import CAN1DCNN
from stage1.fedprox import FedProxLoss

class PUFClient(fl.client.NumPyClient):
    def __init__(self, model, trainloader, device):
        self.model = model
        self.trainloader = trainloader
        self.device = device
        self.criterion = FedProxLoss(mu=0.01) # Use FedProx to handle Non-IID
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)
        
        import copy
        global_model = copy.deepcopy(self.model)
        for param in global_model.parameters():
            param.requires_grad = False
        
        self.model.train()
        print("\nStarting local training with FedProx...")
        
        total_loss = 0.0
        # 1 local epoch per federated round
        loop = tqdm(self.trainloader, desc="Local Epoch", leave=False)
        for data, target in loop:
            data, target = data.to(self.device), target.to(self.device)
            self.optimizer.zero_grad()
            output = self.model(data)
            
            # Add FedProx proximal term
            loss = self.criterion(output, target, self.model, global_model)
            
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            
            loop.set_postfix(Loss=f"{loss.item():.4f}")
            
        print(f"Local training complete. Avg Loss: {total_loss/len(self.trainloader):.4f}")
        return self.get_parameters(config={}), len(self.trainloader.dataset), {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python fl_client.py <vehicle_folder_path>")
        sys.exit(1)
        
    vehicle_dir = sys.argv[1]
    
    print(f"\n--- Starting FL Client for {os.path.basename(vehicle_dir)} ---")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Num classes = 10 (covering 0 to 9 in our label_map)
    model = CAN1DCNN(num_features=11, num_classes=10).to(device)
    
    # Load ALL CSVs for this specific vehicle
    trainloader = get_vehicle_dataloader(vehicle_dir, batch_size=256)
    
    # Start Flower client
    client = PUFClient(model, trainloader, device)
    fl.client.start_client(server_address="127.0.0.1:8084", client=client.to_client())

if __name__ == "__main__":
    main()
