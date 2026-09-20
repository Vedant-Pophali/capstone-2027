import torch
import torch.nn as nn
from tqdm import tqdm

class FedProxLoss(nn.Module):
    def __init__(self, mu=0.01):
        """
        Custom FedProx Loss Function.
        L_FedProx(w) = CrossEntropyLoss(w) + (mu/2) * ||w - w_global||^2
        
        Args:
            mu (float): Proximal term coefficient.
        """
        super(FedProxLoss, self).__init__()
        self.mu = mu
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, outputs, targets, local_model, global_model):
        """
        Args:
            outputs: Predictions from local model
            targets: Ground truth labels
            local_model: The local PyTorch model (w)
            global_model: The global PyTorch model (w_global) - frozen/detached
        """
        # Standard Cross Entropy Loss
        ce_loss = self.criterion(outputs, targets)
        
        # Proximal Term (L2 distance between local and global weights)
        proximal_term = 0.0
        if global_model is not None:
            for local_param, global_param in zip(local_model.parameters(), global_model.parameters()):
                proximal_term += ((local_param - global_param) ** 2).sum()
                
        total_loss = ce_loss + (self.mu / 2.0) * proximal_term
        return total_loss

def train_local_model(local_model, global_model, dataloader, optimizer, device, epochs=1, mu=0.01):
    """
    Simulates local training on a client device using FedProx.
    
    Args:
        local_model: The model to be trained.
        global_model: The reference global model (kept frozen).
        dataloader: PyTorch DataLoader for the client's local data.
        optimizer: PyTorch optimizer (e.g., SGD, Adam).
        device: 'cpu' or 'cuda'.
        epochs: Number of local epochs.
        mu: FedProx proximal coefficient.
        
    Returns:
        The trained local_model and average loss.
    """
    local_model.to(device)
    if global_model is not None:
        global_model.to(device)
        global_model.eval() # Global model is strictly for reference
        
    local_model.train()
    loss_fn = FedProxLoss(mu=mu)
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        correct = 0
        total = 0
        
        progress_bar = tqdm(dataloader, desc=f"Local Epoch {epoch+1}/{epochs}")
        for batch_idx, (inputs, targets) in enumerate(progress_bar):
            inputs, targets = inputs.to(device), targets.to(device)
            
            optimizer.zero_grad()
            
            outputs = local_model(inputs)
            loss = loss_fn(outputs, targets, local_model, global_model)
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            # Calculate accuracy
            _, predicted = torch.max(outputs.data, 1)
            total += targets.size(0)
            correct += (predicted == targets).sum().item()
            
            progress_bar.set_postfix({
                'Loss': f"{loss.item():.4f}", 
                'Acc': f"{100. * correct / total:.2f}%"
            })
            
        print(f"End of Epoch {epoch+1}. Avg Loss: {epoch_loss/len(dataloader):.4f}, Acc: {100.*correct/total:.2f}%")
        
    return local_model
