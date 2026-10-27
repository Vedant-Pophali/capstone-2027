# Capstone 2027: VSOC Fleet Manager

Secure Edge-to-Cloud Vehicle Management System for the Vehicle Security Operations Center (VSOC).

## Overview

This project consists of:

- **Fleet Manager (Backend)**: A Spring Boot application providing the REST API and WebSocket connections for real-time fleet activity.
- **VSOC Dashboard (Frontend)**: A modern React/Vite web application providing an administrative interface.
- **Edge Vehicles**: Simulated vehicle environments deployed dynamically as Docker containers.
- **ML / PUF Simulations**: Python-based pipeline simulations for zero-day attacks and secure edge node handshakes.
- **Hardware PUF Simulation**: 32-bit Parallel Arbiter PUF gate-level simulation in Verilog with picosecond race resolution for fleet authentication.

---

## 🚀 Getting Started (Step-by-Step Guide)

Follow this sequential order to get the entire system running properly on your local machine. All commands are run through our unified startup script `start.ps1`.

### Step 1: Start Docker Desktop

Before running any scripts, ensure **Docker Desktop** is open and the engine is running. You should see a green "Engine running" indicator in the bottom left of the Docker UI. This is required to spin up the simulated edge vehicle containers.

### Step 2: Choose your Startup Mode

Open a PowerShell window in the root directory (`d:\capstone-2027`). You have two ways to start the primary application:

**Option A: Local Development Mode (Recommended for Code Editing)**
This runs the Spring Boot backend natively on port 8081 and the Vite React frontend natively on port 5173. It provides live-reloading.

```powershell
.\start.ps1 -Dev
```

**Option B: Full Docker Mode**
This bundles both the frontend and backend into Docker containers and runs them via docker-compose.

```powershell
.\start.ps1
```

### Step 3: Access the Dashboard

Once the startup script completes, the UI will be live.

- Open your browser and navigate to: **<http://localhost:5173>**
- Go to the **Fleet** tab to try adding a new vehicle (this will dynamically spin up a Docker container on your machine).

### Step 4: Run Machine Learning & PUF Simulations (Optional)

To test the Python-based edge ML simulations (PUF handshakes and Zero-Day Attack Neural Network retraining), open a **new** PowerShell window in the root directory and run:

```powershell
.\start.ps1 -MLSimulation
```

### Step 5: Run Automated Tests (Optional)

To verify the REST API is working correctly without using the UI, open a **new** PowerShell window and run the CRUD smoke tests:

```powershell
.\start.ps1 -TestOnly
```

---

## Shutting Down

- **If using `-Dev`**: Press `Ctrl+C` in your terminal to stop the local servers.
- **If using Docker**: Press `Ctrl+C` in your terminal, and the script will automatically run `docker-compose down` to clean up your environment.

---

## Utility Scripts

Standalone Python scripts live in the `scripts/` folder at the project root:

| Script | Purpose |
| -------- | --------- |
| `scripts/factory_enrollment.py` | Offline PUF CRP provisioning — seeds the SQLite DB with challenge-response pairs |
| `scripts/visualize_hardware_metrics.py` | Generates ArbiterPUF uniqueness/reliability graphs |
| `hardware-simulation/scripts/run_simulation.ps1` | Compiles & runs the 32-bit Parallel Arbiter PUF Verilog fleet simulation |

Run from the project root, e.g.:

```powershell
python scripts/factory_enrollment.py --vehicle-ids 1,2,3 --count 10000
python scripts/visualize_hardware_metrics.py
```

## Architecture Diagrams

### 1. Component-Level Architecture

```mermaid
graph TB
    subgraph "Edge Vehicle Domain (Docker / Physical Node)"
        CAN[CAN Bus Stream / Dataset]
        SNN[TimingSNN Reflex Node]
        CNN[CAN1DCNN Classifier]
        CL[Continual Learning Engine]
        PUF[VehiclePUF Arbiter Simulation]
        TMR[Triple-Redundant State Machine]
        DP[Privacy Filter: Clip + Noise + Sparsity]
        CIPHER[Cipher Engine: HKDF + AES-GCM]
        ENV[Secure Envelope Builder]
        ADAPT[Transport Adapter: HTTP/Local/Mock]
    end

    subgraph "Perimeter & Verification"
        GW[Network Gateway / Ingestion Endpoint]
        VERIF[GatewaySecurityVerifier]
    end

    subgraph "Cloud Backend & Fleet Management"
        SPRING[Fleet Manager: Spring Boot 8081]
        CRP_DB[(SQLite CRP Store: fleet.db)]
        DOC_ORCH[DockerContainerOrchestrator]
        DOCKER_SOCK[Host Docker Socket: /var/run/docker.sock]
        WS[STOMP WebSocket Broker: /topic/fleet]
    end

    subgraph "VSOC Monitoring & Administration"
        VITE[VSOC Dashboard: React SPA 5173]
    end

    subgraph "Federated Aggregation (Isolated)"
        FL_SERVER[Flower FL Server: Port 8084]
        MKRUM[MultiKrum BFT Strategy]
    end

    CAN --> SNN
    CAN --> CNN
    SNN -->|Zero-Day Trigger| CL
    CNN -->|Zero-Day Trigger| CL
    PUF --> TMR
    TMR -->|Gating Open| CL
    CL -->|Weights .pth| DP
    DP --> CIPHER
    PUF -->|Session Key| CIPHER
    CIPHER --> ENV
    PUF -->|HMAC Key| ENV
    ENV --> ADAPT
    ADAPT -.->|HTTP REST / Envelope| GW
    GW --> VERIF
    VERIF --> SPRING
    SPRING <--> CRP_DB
    SPRING --> WS
    WS --> VITE
    VITE -->|REST API + JWT| SPRING
    SPRING --> DOC_ORCH
    DOC_ORCH --> DOCKER_SOCK
    DOCKER_SOCK -.->|Spins up| Edge
    CL -.->|Manual / Disconnected| FL_SERVER
    FL_SERVER --> MKRUM

```

### 2. Module Dependency Graph

```mermaid
graph LR
    main["edge-vehicles/main.py"] --> state_machine["src/core/state_machine.py"]
    main --> puf_simulator["src/security/puf_simulator.py"]
    main --> crypto_signer["src/security/crypto_signer.py"]
    main --> secure_envelope["src/security/secure_envelope.py"]
    main --> ota_handler["src/security/ota_handler.py"]
    main --> cloud_adapter["src/network/cloud_adapter.py"]
    main --> payload_factory["src/network/payload_factory.py"]

    secure_pipeline["edge-vehicles/secure_pipeline.py"] --> cipher_engine["edge-vehicles/cipher_engine.py"]
    secure_pipeline --> privacy_filter["edge-vehicles/privacy_filter.py"]
    secure_pipeline --> secure_envelope
    secure_pipeline --> cloud_adapter

    cloud_adapter --> gateway_verifier["src/network/gateway_verifier.py"]
    gateway_verifier --> puf_simulator
    gateway_verifier --> crypto_signer

    ota_handler --> crypto_signer
    ota_handler --> cloud_adapter

    zero_day["src/ml/orchestrator/zero_day_pipeline.py"] --> cnn1d["src/ml/stage1/cnn1d.py"]
    fl_client["src/ml/stage4_5/fl_client.py"] --> cnn1d
    fl_client --> fedprox["src/ml/stage1/fedprox.py"]
    fl_client --> data_loader_noniid["src/ml/stage4_5/data_loader_noniid.py"]
    fl_server["src/ml/stage4_5/fl_server.py"] --> bft_strategy["src/ml/stage4_5/bft_strategy.py"]
    bft_strategy --> cnn1d

```

### 3. Vehicle Authentication Sequence

```mermaid
sequenceDiagram
    autonumber
    participant V as VehicleNode (Edge)
    participant SM as RedundantStateMachine
    participant P as VehiclePUF
    participant S as CryptographicSigner
    participant G as GatewayVerifier / FleetManager

    Note over V,SM: Initialization
    V->>SM: transition_to(CHALLENGE_ISSUED)
    V->>G: request_join(vehicle_id)
    G-->>V: {status: "authorized", challenge: 54321}
    
    Note over V,P: Hardware PUF Evaluation
    V->>P: get_response(challenge=54321)
    P-->>V: response bits R
    V->>SM: transition_to(RESPONSE_COMPUTED)
    
    Note over V,S: Key Derivation & Proof
    V->>S: derive_session_key(R)
    S-->>V: K_session = SHA256(packbits(R > 0))
    V->>S: generate_signature({"heartbeat": 54321}, K_session)
    S-->>V: Proof Signature
    V->>G: send_proof(vehicle_id, 54321, Proof)
    
    Note over G: Cloud Re-Evaluation
    G->>G: Lookup CRP or re-evaluate PUF(vehicle_id, 54321)
    G->>G: Verify Proof matches expected signature
    G->>G: Consume CRP (atomic update)
    G-->>V: {verified: true}
    
    Note over V,SM: Gate Enforcement
    V->>SM: transition_to(VERIFIED)
    V->>SM: check_state()
    SM-->>V: HandshakeState.VERIFIED (3/3 votes)
    Note over V: ✓ GATE OPEN: Telemetry unlocked

```

### 4. CAN Intrusion Detection & Continual Learning Sequence

```mermaid
sequenceDiagram
    autonumber
    participant BUS as CAN Bus Stream
    participant SNN as TimingSNN
    participant CNN as CAN1DCNN
    participant BUF as Zero-Day Buffer
    participant CL as Continual Learning Engine

    loop Stream Monitoring
        BUS->>SNN: Sequence of IATs (TimeSteps, 1)
        BUS->>CNN: Normalized Window (1, 29, 11)
        SNN->>SNN: Integrate membrane potential & count spikes
        CNN->>CNN: Conv1D feature extraction & classification
        
        alt SNN flags anomaly (Spikes > 15) AND CNN predicts Class 0 (Normal)
            Note over SNN,CNN: Anomaly Discordance Detected!
            BUS->>BUF: Append window to zero_day_buffer
        end
    end

    Note over BUF,CL: Retraining Threshold Reached
    BUF->>CL: Flush buffered zero-day payloads
    CL->>CNN: Expand final linear layer: Linear(64, 10) -> Linear(64, 11)
    
    loop Local Retraining (5 Epochs)
        CL->>CNN: Forward pass on buffered payload
        CL->>CL: Compute CrossEntropyLoss with target = Class 10
        CL->>CNN: Backward pass & Adam optimizer step
    end
    
    Note over CL: Local model checkpoint updated

```

### 5. Secure Model-Update Transmission Sequence

```mermaid
sequenceDiagram
    autonumber
    participant PL as SecurePipeline
    participant DP as PrivacyFilter
    participant KDF as HKDF (cipher_engine)
    participant AEAD as AES-256-GCM (cipher_engine)
    participant ENV as SecurePayloadEnvelope
    participant ADAPT as CloudAdapter / LocalStorage

    PL->>PL: Read model weights from disk (.pth)
    PL->>DP: apply_privacy_filter(state_dict)
    DP->>DP: L2-Norm clipping (max_norm=1.0)
    DP->>DP: Inject Gaussian noise (sigma=0.01)
    DP->>DP: Top-K sparsification (top_k_ratio=0.1)
    DP-->>PL: Privacy-filtered state_dict
    
    PL->>PL: Serialize state_dict to raw bytes
    PL->>PL: Generate nonce_ecu (16B) & nonce_cloud (16B)
    PL->>KDF: derive_aes_key(K_session, nonce_ecu, nonce_cloud)
    KDF-->>PL: 256-bit AES Key (K_aes)
    
    PL->>AEAD: encrypt_weights(raw_bytes, K_aes)
    AEAD-->>PL: {ciphertext_b64, nonce_b64}
    
    PL->>ENV: create_binary(vehicle_id, "WEIGHT_FILE", encrypted_payload, C, K_session)
    ENV->>ENV: Compute ciphertext_hash = SHA256(ciphertext_b64)
    ENV->>ENV: Construct metadata + anti-replay nonce + timestamp
    ENV->>ENV: Sign metadata with HMAC-SHA256(K_session)
    ENV-->>PL: Complete Secure Envelope
    
    PL->>ADAPT: send(envelope)
    ADAPT-->>PL: Transmission confirmation

```

### 6. Cloud Verification & Model Ingestion Sequence

```mermaid
sequenceDiagram
    autonumber
    participant ADAPT as Transport (HTTP / Local)
    participant GW as GatewaySecurityVerifier
    participant CRP as SQLite CRP Store
    participant DEC as Receiver Decryptor
    participant DISK as Storage / ML Checkpoint

    ADAPT->>GW: verify_envelope(envelope)
    
    Note over GW: 1. Schema & Field Validation
    GW->>GW: Check version, payload_id, nonce, timestamp, signature
    
    Note over GW: 2. Anti-Replay Nonce Check
    GW->>GW: Assert envelope.nonce NOT in seen_nonces
    
    Note over GW: 3. Timestamp Freshness Check
    GW->>GW: Assert |now - envelope.timestamp| <= 30 seconds
    
    Note over GW: 4. Re-derive Session Key
    GW->>CRP: Lookup vehicle PUF model / expected response
    GW->>GW: Recompute expected K_session
    
    Note over GW: 5. Cryptographic Signature Verification
    GW->>GW: Recompute HMAC signature over envelope metadata
    GW->>GW: Constant-time string equality check
    
    alt Verification Fails
        GW-->>ADAPT: (False, "Security Violation: Signature mismatch / Replay")
    else Verification Succeeds
        GW->>GW: seen_nonces.add(envelope.nonce)
        GW-->>ADAPT: (True, "Payload verified successfully")
        
        Note over DEC: Payload Decryption
        ADAPT->>DEC: receive_and_decrypt(envelope, K_session)
        DEC->>DEC: Re-derive K_aes = HKDF(K_session, nonce_ecu, nonce_cloud)
        DEC->>DEC: Decrypt AES-256-GCM (verifies 16-byte tag)
        DEC->>DISK: Write decrypted .pth to disk
    end

```

### 7. Complete End-to-End Operational Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Admin as VSOC Operator
    participant UI as VSOC Dashboard (React)
    participant FM as Fleet Manager (Spring Boot)
    participant DOCKER as Docker Engine
    participant EDGE as Edge Vehicle Container
    participant CAN as CAN Bus Stream
    participant ML as Edge ML Engine
    participant SEC as Secure Pipeline
    participant STORE as Storage / Gateway

    Admin->>UI: Click "Add Vehicle" (ID: 42)
    UI->>FM: POST /api/vehicles {id: "42", model: "Sedan"}
    FM->>DOCKER: docker run -d -e VEHICLE_ID=42 capstone-2027-edge-vehicle-base
    FM-->>UI: 201 Created
    FM-)UI: WebSocket /topic/fleet: VehicleCreatedEvent
    
    Note over DOCKER,EDGE: Container Boots
    EDGE->>FM: POST /api/puf/join {vehicleId: "42"}
    FM-->>EDGE: {status: "authorized", challenge: 88888}
    EDGE->>EDGE: Evaluate local PUF: R = ArbiterPUF(88888)
    EDGE->>EDGE: K_session = SHA256(packbits(R > 0))
    EDGE->>FM: POST /api/puf/verify {vehicleId: "42", challenge: 88888, signature: Proof}
    FM->>FM: Verify signature & consume CRP in SQLite
    FM-->>EDGE: {verified: true}
    EDGE->>EDGE: State machine checks 3/3 votes -> VERIFIED
    
    Note over EDGE,CAN: Monitoring & Anomaly Detection
    CAN->>ML: Streaming CAN frames
    ML->>ML: SNN detects timing anomaly, CNN detects zero-day
    ML->>ML: Expand classification head (Class 10) & local retrain
    
    Note over ML,SEC: Secure Export
    ML->>SEC: Export retrained checkpoint (.pth)
    SEC->>SEC: DP Filter (Clip + Noise + Sparsify)
    SEC->>SEC: HKDF derive K_aes from K_session + nonces
    SEC->>SEC: AES-256-GCM encrypt model weights
    SEC->>SEC: Wrap in Secure Envelope with HMAC-SHA256 signature
    SEC->>STORE: Transmit Envelope via Adapter
    
    Note over STORE: Cloud Verification & Persistence
    STORE->>STORE: Anti-replay verify, HMAC verify, AES-GCM decrypt
    STORE->>FM: Alert: Anomaly adapted on Vehicle 42
    FM-)UI: WebSocket /topic/fleet: VehicleStatusChanged (Healthy -> Threat Alerted)
```
