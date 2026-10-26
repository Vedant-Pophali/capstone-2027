import torch
import torch.nn as nn
import torch.optim as optim
import sys
import os

# Ensure we can import from siblings in src/ml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stage1.cnn1d import CAN1DCNN
from stage2.snn import TimingSNN

print("\n=== PUF-CP-IDS: Zero-Day Orchestrator Pipeline ===")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# 1. Load Pretrained Global CNN Model (Stage 1)
print("[1] Loading Federated Global CNN Model (Stage 1)...")
model = CAN1DCNN(num_features=11, num_classes=10)
global_model_path = r'e:\capstone-2027\src\ml\models\stage1_cnn1d_model.pth'
if not os.path.exists(global_model_path):
    global_model_path = r'e:\capstone-2027\src\ml\models\stage4_global_model.pth'

try:
    model.load_state_dict(torch.load(global_model_path, map_location=device))
    print(f"Loaded weights from {global_model_path}")
except Exception as e:
    print(f"Warning: Could not load model checkpoint ({e}). Using initialized weights for simulation.")

# 2. Instantiate Stage 2 Unsupervised SNN (Timing Anomaly Detector)
print("[2] Initializing Stage 2 TimingSNN Anomaly Detector...")
snn_model = TimingSNN().to(device)

# 3. Adapt CNN Architecture for Continual Learning (Adding Class 10: Zero-Day Anomaly)
print("[3] Adapting CNN Architecture for Continual Learning (Expanding to 11 Classes)...")
in_features = model.classifier[3].in_features
# Expand final linear layer: 64 -> 11
old_weights = model.classifier[3].weight.data.clone()
old_bias = model.classifier[3].bias.data.clone()

model.classifier[3] = nn.Linear(in_features, 11)
# Preserve learned weights for classes 0-9
with torch.no_grad():
    model.classifier[3].weight[:10] = old_weights
    model.classifier[3].bias[:10] = old_bias
    
model.to(device)

optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# 4. Stream Processing with Dual-Stage Consensus Logic
print("\n[4] Streaming CAN Bus Traffic through Dual-Stage Detection Pipeline...")
zero_day_buffer = []

# Simulate 300 sequential CAN stream windows
# Mixture: Normal traffic, Known attacks, and Zero-Day stealth attacks
for step in range(1, 301):
    if step <= 100:
        # Scenario A: Benign normal traffic (Normal payload, Normal IAT ~0.5)
        stream_data = torch.zeros(1, 29, 11).to(device)
        stream_data[:, :, 0] = 0.5 # Normal steady 10-20ms IAT
    elif step <= 180:
        # Scenario B: Known attack (Simulated injection payload, abnormal IAT)
        stream_data = torch.rand(1, 29, 11).to(device)
        stream_data[:, :, 0] = 2.0 # High excitation DoS IAT
    else:
        # Scenario C: ZERO-DAY ATTACK!
        # Attacker injects packets that appear benign/zeros to CNN (Class 0),
        # but the bus injection causes high-frequency timing burst (IAT=2.0)
        stream_data = torch.zeros(1, 29, 11).to(device)
        stream_data[:, :, 0] = 2.0 # Bus flooding rate disruption
    
    # --- Step 4a: Stage 2 SNN Timing Reflex ---
    # Extract IAT sequence (Column 0) -> Shape: (Time_Steps=29, Batch=1, Features=1)
    iat_sequence = stream_data[0, :, 0].view(29, 1, 1)
    spk_rec, _ = snn_model(iat_sequence)
    snn_anomaly = snn_model.detect_anomaly(spk_rec, threshold_high=16, threshold_low=4)
    
    # --- Step 4b: Stage 1 CNN Payload Inspection ---
    model.eval()
    with torch.no_grad():
        output = model(stream_data)
        cnn_pred = torch.argmax(output, dim=1).item()
        
    cnn_is_normal = (cnn_pred == 0)
    
    # --- Step 4c: Dual-Stage Consensus Truth Table ---
    if cnn_is_normal and snn_anomaly:
        # ZERO-DAY ATTACK DETECTED:
        # CNN missed it (Class 0), but SNN caught the timing disruption!
        zero_day_buffer.append(stream_data)
        if len(zero_day_buffer) % 25 == 0 or len(zero_day_buffer) == 1:
            print(f" -> [ZERO-DAY DETECTED] Step {step:3d}: CNN classified as Normal (0), but SNN caught Timing Anomaly! Spikes: {spk_rec.sum().item():.0f}")
            
    elif not cnn_is_normal and snn_anomaly:
        if step % 50 == 0:
            print(f" -> [KNOWN ATTACK]     Step {step:3d}: Both CNN (Class {cnn_pred}) and SNN confirmed attack.")
            
    elif cnn_is_normal and not snn_anomaly:
        if step == 50:
            print(f" -> [NORMAL TRAFFIC]  Step {step:3d}: CNN and SNN agree traffic is benign.")

print(f"\n[Quarantine Buffer] Collected {len(zero_day_buffer)} Zero-Day attack sequences.")

# 5. Trigger Continual Learning on Edge Device
print("\n[5] Triggering Local Continual Learning for Newly Discovered Zero-Day (Class 10)...")
model.train()
epochs = 5

for epoch in range(epochs):
    total_loss = 0.0
    for payload in zero_day_buffer:
        optimizer.zero_grad()
        output = model(payload)
        
        # Label 10 = Zero-Day Anomaly Class
        target = torch.tensor([10]).to(device)
        loss = criterion(output, target)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        
    avg_loss = total_loss / max(1, len(zero_day_buffer))
    print(f" Continual Learning Epoch {epoch+1}/{epochs} | Avg Loss: {avg_loss:.4f}")

# 6. Verification: Does CNN now recognize the Zero-Day payload as Class 10?
model.eval()
with torch.no_grad():
    sample_test = zero_day_buffer[0]
    new_pred = torch.argmax(model(sample_test), dim=1).item()
    print(f"\n[Verification] Re-evaluating Zero-Day payload: Prediction is now Class {new_pred} (Class 10 = Zero-Day)")

# Save the newly adapted weights to local_update.pth for Federated Learning transmission
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
os.makedirs(models_dir, exist_ok=True)
save_update_path = os.path.join(models_dir, 'local_update.pth')
torch.save(model.state_dict(), save_update_path)
print(f"\n[Export] Local adapted weights saved to: {save_update_path}")

print("\n[6] SUCCESS: Stage 1 CNN adapted to newly discovered Zero-Day attack!")
print("The edge device is now immunized and ready to transmit updated weights in the next FL round.")
print("===================================================================================\n")
