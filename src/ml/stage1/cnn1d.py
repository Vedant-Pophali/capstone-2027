import torch
import torch.nn as nn

class CAN1DCNN(nn.Module):
    def __init__(self, num_features=11, num_classes=2):
        """
        1D-CNN Model for CAN bus anomaly detection (Stage 1).
        
        Args:
            num_features (int): Number of input features per CAN frame (default 11: IAT, ID, DLC, D0-D7).
            num_classes (int): Number of output classes (2 for Normal/Attack).
        """
        super(CAN1DCNN, self).__init__()
        
        # Input shape: (Batch, Sequence/Window Length, Features)
        # PyTorch Conv1d expects: (Batch, Channels/Features, Sequence Length)
        # We will permute the input in the forward pass.
        
        self.conv_block1 = nn.Sequential(
            nn.Conv1d(in_channels=num_features, out_channels=64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(64),
            nn.MaxPool1d(kernel_size=2)
        )
        
        self.conv_block2 = nn.Sequential(
            nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.MaxPool1d(kernel_size=2)
        )
        
        # Global Average Pooling reduces (Batch, 128, Seq_Len) to (Batch, 128, 1) -> (Batch, 128)
        self.global_avg_pool = nn.AdaptiveAvgPool1d(1)
        
        self.classifier = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Linear(64, num_classes) 
            # Note: Softmax is omitted here because PyTorch's CrossEntropyLoss applies it internally.
        )

    def forward(self, x):
        # x shape initially: (Batch, Window_Size, Num_Features)
        # Permute to: (Batch, Num_Features, Window_Size) for Conv1d
        x = x.permute(0, 2, 1)
        
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        
        x = self.global_avg_pool(x)
        x = torch.flatten(x, 1) # Flatten all dimensions except batch
        
        out = self.classifier(x)
        return out

if __name__ == "__main__":
    # Test the model with dummy data
    batch_size = 32
    window_size = 29
    num_features = 11
    
    dummy_input = torch.randn(batch_size, window_size, num_features)
    model = CAN1DCNN(num_features=num_features, num_classes=2)
    output = model(dummy_input)
    
    print(f"Input shape: {dummy_input.shape}")
    print(f"Output shape: {output.shape}")
    assert output.shape == (batch_size, 2), "Output shape mismatch!"
    print("Model initialized successfully.")
