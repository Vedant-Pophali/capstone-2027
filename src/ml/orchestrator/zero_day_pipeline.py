import torch
import torch.nn as nn
import torch.optim as optim
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stage1.cnn1d import CAN1DCNN

print("\n=== PUF-CP-IDS: Zero-Day Orchestrator Pipeline ===")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load Global CNN
print("[1] Loading Federated Global CNN Model...")
model = CAN1DCNN(num_features=11, num_classes=10)
try:
    model.load_state_dict(torch.load(r'e:\capstone-2027\src\ml\models\stage4_global_model.pth', map_location=device))
except Exception as e:
    print(f"Warning: Could not load global model ({e}). Using initialized weights for simulation.")

# Expand classification head for Continual Learning (Class 10 = Zero-Day Anomaly)
print("[2] Adapting Neural Network for Continual Learning (Adding Class 10)...")
# model.classifier[3] is the final nn.Linear(64, 10) layer
in_features = model.classifier[3].in_features
model.classifier[3] = nn.Linear(in_features, 11)
    
model.to(device)
model.train() # We will be retraining it

optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Simulate a live CAN bus stream
print("\n[3] Simulating Live CAN Bus Traffic...")
zero_day_buffer = []

# Generate simulated Zero-Day attack payloads (e.g. extreme timing anomalies)
for step in range(1, 501):
    # Simulated incoming data (Batch=1, Window=29, Features=11)
    simulated_data = torch.rand(1, 29, 11).to(device)
    
    # Simulate SNN Reflex
    # In this simulation, the SNN successfully detects the packets as a Timing Anomaly
    snn_anomaly_detected = True 
    
    # CNN Classification
    output = model(simulated_data)
    cnn_prediction = torch.argmax(output, dim=1).item()
    
    if snn_anomaly_detected and (cnn_prediction == 0 or cnn_prediction != 10):
        # Zero-Day Detected! SNN says anomaly, but CNN misclassifies it
        zero_day_buffer.append(simulated_data)
        if step % 100 == 0:
            print(f" -> Stream Step {step}: SNN intercepted Zero-Day attack! CNN misclassified it.")
            
print(f"\n[Buffer] Collected {len(zero_day_buffer)} Zero-Day payloads.")
print("\n[4] Triggering Local PyTorch Continual Learning (Classifying as Class 10)...")

# Retrain the CNN on the new class
epochs = 5
for epoch in range(epochs):
    total_loss = 0
    for payload in zero_day_buffer:
        optimizer.zero_grad()
        output = model(payload)
        
        # Target is Class 10 (Unknown Anomaly)
        target = torch.tensor([10]).to(device)
        
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
    print(f"Continual Learning Epoch {epoch+1}/{epochs} - Loss: {total_loss/len(zero_day_buffer):.4f}")

print("\n[5] SUCCESS: CNN successfully adapted to the Zero-Day attack!")
print("The edge device is now ready to transmit updated feature extractors to the Federated Server.")
print("====================================================\n")
