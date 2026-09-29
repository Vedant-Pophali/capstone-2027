# Edge Vehicle Simulation Context

**Stack:** Python, PyTorch, pypuf, Flower
**Role:** Simulates a single autonomous vehicle node contributing to a federated learning fleet.

## Overall Objectives
1. **Pillar 1 (Hardware Root of Trust):** Generate unique hardware identifiers using a simulated PUF (Physical Unclonable Function) to anchor vehicle identities.
2. **Pillar 2 (Zero-Day Detection):** Execute a dual-branch Spiking Neural Network (SNN). The supervised branch detects known CAN attacks, and the unsupervised branch flags unknown anomalies.
3. **Pillar 3 (Fault Tolerance):** Protect the hardware handshake from physical voltage/clock glitches via a Triple Modular Redundant (TMR) state machine.

**Constraints:** Never hardcode vehicle IDs; read them from environment variables to allow Docker Compose scaling.

---

## Roadmap & Implementation Status

### ✅ Phase 1: PUF Simulation & Hardware Root of Trust (COMPLETED)
* **`puf_enrollment_db.py`**: A simulated secure facility database storing Challenge-Response Pairs (CRPs) for each enrolled vehicle.
* **`puf_fl_strategy.py`**: A custom Flower strategy (`PUFAuthenticatedStrategy`) wrapping Multi-Krum that mandates a cryptographic PUF signature before aggregating weights.
* **`fl_client.py`**: Edge vehicle FL client initialized with its unique simulated silicon, generating session keys and signing its weight updates.
* **Security Achievements:** Successfully blocks unregistered Sybil nodes, identity clones (wrong silicon), and Man-in-the-Middle (MITM) tampering, preventing weight-poisoning attacks.

### ⏳ Phase 2: Dual-Branch SNN & Zero-Day Detection (NEXT)
* **Goal:** Run an unsupervised spiking network alongside the supervised one to catch unknown attacks.
* **Implementation:** 
  1. Train existing SNN on known HCRL Car Hacking dataset labels (supervised).
  2. Implement a parallel unsupervised branch (e.g., STDP or reconstruction error) to establish a baseline of "normal" CAN bus traffic.
  3. Simulate a Zero-Day attack to demonstrate the supervised branch failing but the unsupervised branch successfully flagging a high novelty score.

### ⏳ Phase 3: Fault Injection Simulation & Redundant State Machine (PLANNED)
* **Goal:** Protect the PUF handshake from physical hardware glitch attacks.
* **Implementation:**
  1. Wrap the PUF handshake in a Redundant State Machine (Triple Modular Redundancy - TMR).
  2. Run 3 parallel state instances and apply a majority-voting mechanism (2-out-of-3).
  3. Build an "Attacker/Glitcher" utility that corrupts one state machine in memory.
  4. Ensure the TMR detects the fault and forces the vehicle into a fail-safe mode, aborting the compromised payload transmission and notifying the VSOC.