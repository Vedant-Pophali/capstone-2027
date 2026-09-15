# Project Context: PUF-KeySNN Vehicle Network
This is a Dockerized, multi-container simulation of an autonomous Vehicle-to-Vehicle (V2V) network using Federated Learning (FL). 

## Architecture Requirements
- **Monorepo Structure:** 5 microservices (`/edge-vehicles`, `/network-gateway`, `/fl-cloud`, `/audit-logger`, `/vsoc-dashboard`).
- **Edge Simulation (Python/PyTorch):** Identical Docker containers scaling dynamically to represent individual cars. Must simulate a PUF (Physical Unclonable Function) for identity and run a dual-branch Spiking Neural Network (SNN) for zero-day threat detection.
- **Gateway (Go):** High-speed, asynchronous routing between the fleet and cloud.
- **Cloud (Python/Flower):** Federated aggregation using Byzantine-robust algorithms (Krum) to reject poisoned weights.
- **Dashboard & Logs (Node.js/Java):** Real-time web UI showing fleet threat status and a secure audit ledger.

## Execution Rules
- No physical hardware. All PUFs and vehicular CAN bus data (HCRL dataset) are software-simulated.
- Isolate domain logic: The Python agent must not touch the Go network gateway.