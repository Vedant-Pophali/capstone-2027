# Edge Vehicle Simulation Context
**Stack:** Python, PyTorch, pypuf
**Role:** Simulates a single autonomous vehicle.
**Objectives:**
1. Generate unique hardware identifiers using a simulated PUF (Physical Unclonable Function).
2. Process mock CAN bus data streams (HCRL dataset).
3. Execute a dual-branch Spiking Neural Network (SNN). The supervised branch detects known CAN attacks, and the unsupervised branch flags unknown anomalies (Zero-Days).
**Constraints:** Never hardcode vehicle IDs; read them from environment variables to allow Docker Compose scaling.