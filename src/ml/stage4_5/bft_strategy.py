import flwr as fl
import numpy as np

class MultiKrum(fl.server.strategy.FedAvg):
    def __init__(self, m=4, f=1, **kwargs):
        """
        Byzantine Fault Tolerant (BFT) Multi-Krum Strategy
        m: total number of clients participating
        f: number of expected Byzantine (malicious) clients
        """
        super().__init__(**kwargs)
        self.m = m
        self.f = f

    def aggregate_fit(self, server_round, results, failures):
        if not results:
            return None, {}
            
        # Extract weights from results
        weights_results = [
            (fl.common.parameters_to_ndarrays(fit_res.parameters), fit_res.num_examples)
            for _, fit_res in results
        ]
        
        # If we have less clients than needed for Krum, fallback to FedAvg
        if len(weights_results) < self.m - self.f:
            print("Not enough clients for Multi-Krum. Falling back to standard FedAvg.")
            return super().aggregate_fit(server_round, results, failures)
            
        print(f"\n[BFT Multi-Krum] Aggregating {len(weights_results)} client updates...")
        
        # Calculate pairwise distances between all client weight vectors
        distances = np.zeros((len(weights_results), len(weights_results)))
        
        for i, (w1, _) in enumerate(weights_results):
            for j, (w2, _) in enumerate(weights_results):
                if i != j:
                    # Flatten and concatenate all layers to compute L2 norm
                    flat_w1 = np.concatenate([layer.flatten() for layer in w1])
                    flat_w2 = np.concatenate([layer.flatten() for layer in w2])
                    distances[i, j] = np.linalg.norm(flat_w1 - flat_w2)
                    
        # For each client, sum the distances to its (m - f - 2) nearest neighbors
        scores = []
        k_nearest = max(1, self.m - self.f - 2)
        
        for i in range(len(distances)):
            sorted_dists = np.sort(distances[i])
            # Drop the first one (distance to self is 0) and take the k nearest
            score = np.sum(sorted_dists[1:k_nearest+1])
            scores.append((score, i))
            
        # Sort clients by score (lower score = more central/trustworthy)
        scores.sort(key=lambda x: x[0])
        
        # Select the top (m - f) clients to aggregate
        num_to_aggregate = max(1, self.m - self.f)
        selected_indices = [idx for _, idx in scores[:num_to_aggregate]]
        
        print(f"[BFT Multi-Krum] Filtered out {len(results) - num_to_aggregate} potential malicious/poisoned clients.")
        print(f"[BFT Multi-Krum] Selected trustworthy clients indices: {selected_indices}")
        
        # Filter results to only include selected clients
        selected_results = [results[i] for i in selected_indices]
        
        # Delegate the actual weighted average of the trusted clients to FedAvg
        aggregated_parameters, metrics = super().aggregate_fit(server_round, selected_results, failures)
        
        # Save the global model to disk
        if aggregated_parameters is not None:
            import os
            import torch
            import sys
            
            # Append the parent dir so we can import CAN1DCNN
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from stage1.cnn1d import CAN1DCNN
            from collections import OrderedDict
            
            # Convert Flower Parameters to NumPy ndarrays
            ndarrays = fl.common.parameters_to_ndarrays(aggregated_parameters)
            
            # Initialize a blank model (num_classes=10 for Non-IID dataset)
            model = CAN1DCNN(num_features=11, num_classes=10)
            
            # Load weights into the PyTorch model
            params_dict = zip(model.state_dict().keys(), ndarrays)
            state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
            model.load_state_dict(state_dict, strict=True)
            
            # Save it
            models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models')
            os.makedirs(models_dir, exist_ok=True)
            save_path = os.path.join(models_dir, 'stage4_global_model.pth')
            torch.save(model.state_dict(), save_path)
            print(f"\n[Server] Global model successfully saved to: {save_path}\n")
            
        return aggregated_parameters, metrics
