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
        
        # Simple 1D input (IAT) to 1 output neuron
        self.fc = nn.Linear(1, 1)
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

    def detect_anomaly(self, spike_train, threshold_high=15, threshold_low=2):
        """
        Unsupervised anomaly detection based on total spike count.
        If the timing (IAT) causes too many spikes (DoS) or too few (Drop), it flags True.
        """
        total_spikes = spike_train.sum().item()
        
        # If the rate deviates heavily from normal rhythm, flag as anomaly
        if total_spikes > threshold_high or total_spikes < threshold_low:
            return True
        return False
