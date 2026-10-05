# Edge Vehicle Simulation Context

**Stack:** Python, PyTorch, pypuf, cryptography
**Role:** Simulates a single autonomous vehicle with hardware-grade identity and secure cloud communication.

## Objectives

1. Generate unique hardware identifiers using a simulated PUF (Physical Unclonable Function) via `pypuf` Arbiter PUF.
2. Process mock CAN bus data streams (HCRL dataset).
3. Execute a dual-branch Spiking Neural Network (SNN). The supervised branch detects known CAN attacks; the unsupervised branch flags unknown anomalies (Zero-Days).
4. Authenticate with the Fleet Manager cloud server using a PUF Challenge-Response Protocol (CRP) — no hardcoded passwords or certificates.
5. Encrypt all outbound payloads using AES-256-GCM with a session key derived from the PUF response hash.
6. Perform secure OTA firmware/model updates via the `ota_handler` module, which re-validates vehicle identity before applying any update.

## Security Modules (`src/security/`)

| Module | Purpose |
| --- | --- |
| `puf_simulator.py` | Wraps `pypuf` ArbiterPUF; generates deterministic challenge→response pairs for the vehicle |
| `crypto_signer.py` | Derives AES-256-GCM session keys from PUF response hashes; signs and verifies payloads |
| `secure_envelope.py` | Bundles challenge, encrypted payload, and HMAC into a single transmission envelope |
| `ota_handler.py` | Handles OTA update handshake: sends challenge to fleet manager, receives encrypted delta, applies update |

## Communication

- **Protocol:** HTTP/HTTPS REST (no MQTT)
- **Target:** Fleet Manager (`fleet-manager` service) via Docker internal network
- **Endpoints used:** `/api/puf/authenticate`, `/api/puf/ota-renew`

## Constraints

- Never hardcode vehicle IDs; read from `VEHICLE_ID` environment variable (Docker Compose scaling).
- Do **not** modify anything under `src/ml/` — maintained by a separate team member.
- All crypto operations must use the `cryptography` library (not `pycryptodome`).