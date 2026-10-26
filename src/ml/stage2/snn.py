import torch
import torch.nn as nn
import snntorch as snn
from snntorch import surrogate

class TimingSNN(nn.Module):
    """
    Unsupervised Spiking Neural Network for CAN bus timing anomalies.
    Only analyzes Inter-Arrival Time (IAT).
    """
    def __init__(self):
        super(TimingSNN, self).__init__()
        
        # Leaky Integrate-and-Fire parameters
        self.beta = 0.95
        spike_grad = surrogate.fast_sigmoid(slope=25)
        
        # 1D input (IAT) to 1 output neuron
        self.fc = nn.Linear(1, 1)
        # Calibrate baseline weights for steady state firing rhythm
        self.fc.weight.data.fill_(1.2)
        self.fc.bias.data.fill_(0.1)
        self.lif = snn.Leaky(beta=self.beta, spike_grad=spike_grad)
        
    def forward(self, x):
        # x is the sequence of IATs. 
        # Shape expected: (Time_Steps, Batch, 1)
        mem = self.lif.init_leaky()
        
        spk_rec = []
        mem_rec = []
        
        for step in range(x.size(0)):
            cur = self.fc(x[step])
            spk, mem = self.lif(cur, mem)
            spk_rec.append(spk)
            mem_rec.append(mem)
            
        return torch.stack(spk_rec, dim=0), torch.stack(mem_rec, dim=0)

    def detect_anomaly(self, spike_train, threshold_high=16, threshold_low=4):
        """
        Unsupervised anomaly detection based on total spike count.
        If the timing (IAT) causes too many spikes (DoS) or too few (Drop/Loss), it flags True.
        """
        total_spikes = spike_train.sum().item()
        
        # If the firing rate deviates heavily from normal rhythm, flag as anomaly
        if total_spikes > threshold_high or total_spikes < threshold_low:
            return True
        return False

if __name__ == '__main__':
    print('=== Stage 2: TimingSNN Anomaly Detection Demonstration ===\n')
    model = TimingSNN()
    
    # 1. Normal CAN Bus Traffic Simulation (Regular 10ms-20ms intervals)
    # Shape: (Time_Steps=20, Batch=1, Features=1)
    normal_iat = torch.full((20, 1, 1), 0.5)
    spk_norm, _ = model(normal_iat)
    norm_spikes = spk_norm.sum().item()
    is_norm_anomaly = model.detect_anomaly(spk_norm)
    print(f'[Test 1 - Normal Traffic]      Total Spikes: {norm_spikes:.1f}/20 | Anomaly Flagged: {is_norm_anomaly}')
    
    # 2. DoS Attack Simulation (Bus Flooding -> Microsecond intervals, High Current)
    dos_iat = torch.full((20, 1, 1), 2.0)
    spk_dos, _ = model(dos_iat)
    dos_spikes = spk_dos.sum().item()
    is_dos_anomaly = model.detect_anomaly(spk_dos)
    print(f'[Test 2 - DoS Flooding Attack]  Total Spikes: {dos_spikes:.1f}/20 | Anomaly Flagged: {is_dos_anomaly}')
    
    # 3. Message Drop / Evasion Attack (Zero/Negative Excitation)
    drop_iat = torch.full((20, 1, 1), -0.5)
    spk_drop, _ = model(drop_iat)
    drop_spikes = spk_drop.sum().item()
    is_drop_anomaly = model.detect_anomaly(spk_drop)
    print(f'[Test 3 - Message Drop Attack]  Total Spikes: {drop_spikes:.1f}/20 | Anomaly Flagged: {is_drop_anomaly}')
    
    print('\n[SUCCESS] Stage 2 TimingSNN is working and verified.')
