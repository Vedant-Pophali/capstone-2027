import torch.nn as nn
import torch.nn.functional as F

class IoV1DCNN(nn.Module):
    def __init__(self, num_features=9, num_classes=6):
        super(IoV1DCNN, self).__init__()
        
        self.conv1 = nn.Conv1d(in_channels=num_features, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(32)
        
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        
        self.fc1 = nn.Linear(64, 32)
        self.fc2 = nn.Linear(32, num_classes)
        
    def forward(self, x):
        # Input x shape: (Batch, Sequence, Features)
        # Conv1d expects: (Batch, Channels/Features, Sequence)
        x = x.permute(0, 2, 1)
        
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        
        # Global Average Pooling across the sequence dimension
        x = F.adaptive_avg_pool1d(x, 1).squeeze(2)
        
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        
        return x
