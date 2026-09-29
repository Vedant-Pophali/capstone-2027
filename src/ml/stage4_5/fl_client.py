"""
FL Client — Phase 1: PUF-Authenticated Federated Learning
==========================================================
Each FL round, the server sends a per-round challenge via fit_config.
This client:
  1. Computes its PUF response to that challenge.
  2. Derives a session key from the PUF response.
  3. Signs the round context (round number + challenge) with that key.
  4. Returns the signature + vehicle_id in the fit() metrics dict.

The server-side PUFAuthenticatedStrategy re-derives the expected key
from its enrollment DB and verifies the signature before aggregating.
"""

import sys
import os
import torch
import torch.optim as optim
import flwr as fl
from collections import OrderedDict
from tqdm import tqdm

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- PUF signing imports (Phase 1) ---
_EDGE_VEHICLES_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "edge-vehicles")
)
if _EDGE_VEHICLES_ROOT not in sys.path:
    sys.path.insert(0, _EDGE_VEHICLES_ROOT)

from src.security.puf_simulator import VehiclePUF
from src.security.crypto_signer import CryptographicSigner
# ------------------------------------

from stage4_5.data_loader_noniid import get_vehicle_dataloader
from stage1.cnn1d import CAN1DCNN
from stage1.fedprox import FedProxLoss


class PUFClient(fl.client.NumPyClient):
    def __init__(self, model, trainloader, device, vehicle_id: str):
        self.model = model
        self.trainloader = trainloader
        self.device = device
        self.vehicle_id = vehicle_id
        self.criterion = FedProxLoss(mu=0.01)  # FedProx handles Non-IID skew
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)

        # Instantiate this vehicle's unique PUF (seeded by vehicle_id).
        # In real hardware this is the silicon Arbiter PUF chip at boot time.
        old_env = os.environ.get("VEHICLE_ID")
        os.environ["VEHICLE_ID"] = str(vehicle_id)
        self.puf = VehiclePUF()
        if old_env is not None:
            os.environ["VEHICLE_ID"] = old_env
        elif "VEHICLE_ID" in os.environ:
            del os.environ["VEHICLE_ID"]

        print(f"[PUFClient] Vehicle '{vehicle_id}' PUF module initialized.")

    # ------------------------------------------------------------------

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config):
        self.set_parameters(parameters)

        # --- Phase 1: PUF Authentication ---
        # Server injects puf_challenge + current_round via configure_fit().
        # Graceful fallback so tests without a server still work.
        puf_challenge = int(config.get("puf_challenge", 12345))
        server_round  = int(config.get("current_round", 1))

        _, puf_response = self.puf.get_response(puf_challenge)
        session_key = CryptographicSigner.derive_session_key(puf_response)

        puf_signature = CryptographicSigner.generate_signature(
            {"round": server_round, "challenge": puf_challenge},
            session_key,
        )
        print(
            f"[PUFClient] Vehicle '{self.vehicle_id}' signed round {server_round} "
            f"with PUF key prefix: {session_key[:12]}..."
        )
        # -----------------------------------

        import copy
        global_model = copy.deepcopy(self.model)
        for param in global_model.parameters():
            param.requires_grad = False

        self.model.train()
        print("\nStarting local training with FedProx...")

        total_loss = 0.0
        loop = tqdm(self.trainloader, desc="Local Epoch", leave=False)
        for data, target in loop:
            data, target = data.to(self.device), target.to(self.device)
            self.optimizer.zero_grad()
            output = self.model(data)

            loss = self.criterion(output, target, self.model, global_model)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
            loop.set_postfix(Loss=f"{loss.item():.4f}")

        print(f"Local training complete. Avg Loss: {total_loss/len(self.trainloader):.4f}")

        # Return weights + PUF proof in metrics — server verifies signature
        return (
            self.get_parameters(config={}),
            len(self.trainloader.dataset),
            {"vehicle_id": self.vehicle_id, "puf_signature": puf_signature},
        )


def main():
    if len(sys.argv) < 2:
        print("Usage: python fl_client.py <vehicle_folder_path>")
        sys.exit(1)

    vehicle_dir = sys.argv[1]
    vehicle_id  = os.path.basename(vehicle_dir)  # e.g. "vehicle_0"

    print(f"\n--- Starting FL Client for {vehicle_id} ---")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model       = CAN1DCNN(num_features=11, num_classes=10).to(device)
    trainloader = get_vehicle_dataloader(vehicle_dir, batch_size=256)

    client = PUFClient(model, trainloader, device, vehicle_id=vehicle_id)
    fl.client.start_client(server_address="127.0.0.1:8084", client=client.to_client())


if __name__ == "__main__":
    main()
