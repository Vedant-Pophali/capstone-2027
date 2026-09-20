import flwr as fl
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stage4_5.bft_strategy import MultiKrum

def main():
    print("\n=== PUF-CP-IDS Stage 4/5: FL Server (BFT Multi-Krum) ===")
    
    # We have 4 edge vehicles
    strategy = MultiKrum(
        m=4,  # Total clients
        f=1,  # Max Byzantine (malicious) clients we expect
        fraction_fit=1.0,
        min_fit_clients=4,
        min_available_clients=4,
    )

    # Start Flower server
    fl.server.start_server(
        server_address="127.0.0.1:8084",
        config=fl.server.ServerConfig(num_rounds=1), # 1 round to prove integration works
        strategy=strategy,
    )
    print("\nFederated Learning Complete.")

if __name__ == "__main__":
    main()
