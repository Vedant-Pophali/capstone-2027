# Federated Cloud Aggregation Context
**Stack:** Python, Flower (flwr)
**Role:** Centralized model training server.
**Objectives:**
1. Receive local SNN model updates from the edge vehicles.
2. Verify cryptographic signatures to ensure weights come from PUF-authenticated containers.
3. Apply Byzantine-robust aggregation algorithms (e.g., Krum) to discard poisoned model weights.
**Constraints:** This service must not process raw CAN data, only mathematical model weights.