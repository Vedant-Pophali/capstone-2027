# 32-Bit Parallel Arbiter PUF Simulation

Gate-level Verilog simulation of a 32-bit Parallel Arbiter Physically Unclonable Function (PUF) architecture designed for vehicular edge network authentication in the Capstone 2027 project.

---

## 1. Executive Summary

This directory contains the Verilog gate-level simulation for a **32-Bit Parallel Arbiter Physical Unclonable Function (PUF)**. The simulation models nanoscale silicon manufacturing process variations (at picosecond resolution) to derive unique, deterministic Challenge-Response Pairs (CRPs) for a fleet of five edge vehicles (VID 101 through 105).

The generated hardware responses serve as a silicon-intrinsic **Hardware Root of Trust (RoT)** that directly interfaces with the vehicular security stack and downstream Python-based Spiking Neural Network (SNN) and Convolutional Neural Network (CNN) anomaly detection pipeline ([puf_simulator.py](file:///d:/capstone-2027/edge-vehicles/src/security/puf_simulator.py)).

---

## 2. Architectural Specification

### 2.1 32-Bit Parallel Arbiter Topology (`parallel_puf.v`)

To satisfy automotive throughput and latency constraints, the architecture evaluates a full 32-bit response word in a single clock cycle across 32 parallel, independent delay lanes excited by a shared 128-bit challenge vector.

```
                         128-Bit Challenge (Shared across all 32 lanes)
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
                [Lane 0]                [Lane 1]       ...      [Lane 31]
              (128 stages)            (128 stages)             (128 stages)
                    │                       │                       │
                 resp[0]                 resp[1]       ...       resp[31]
                    └───────────────────────┼───────────────────────┘
                                     32-Bit Response
```

Each lane houses an independent 128-stage Arbiter PUF delay chain ([arbiter_puf.v](file:///d:/capstone-2027/hardware-simulation/src/arbiter_puf.v)). When excited by the challenge vector, each lane resolves its internal sub-picosecond delay race to yield one bit, collectively forming the 32-bit parallel response word.

### 2.2 Per-Lane 128-Stage Switch Chain (`arbiter_puf.v`)

Each parallel lane implements a symmetric 128-stage multiplexer cascade terminated by an edge-triggered D flip-flop arbiter:

```
              Challenge[0]    Challenge[1]         Challenge[127]
                    |               |                     |
  trigger ──┬── [Stage 0] ──── [Stage 1] ──── ... ──── [Stage 127] ──┬── D ──[DFF]──> response[k]
            └── [Stage 0] ──── [Stage 1] ──── ... ──── [Stage 127] ──┘── CLK ─┘
               upper path                                                lower path
```

- **Simulation Timescale**: `` `timescale 1ps/1ps `` across all modules to preserve picosecond-resolution timing dynamics.
- **Structural Primitives**: Pure structural gate implementation using standard 2:1 multiplexers ([mux2to1_gate.v](file:///d:/capstone-2027/hardware-simulation/src/mux2to1_gate.v)) composed of logic primitives (`not`, `and`, `or`).
- **Non-Linear Delay Model**: Process variability is modeled using multiplicative pseudo-random dispersion algorithms parameterized by distinct per-lane seeds, accurately reflecting uncorrelated intra-die Gaussian silicon variation.

---

## 3. Vehicular Fleet Configuration & Academic Rationale (`vehicle_fleet_puf.v`)

Based on academic literature regarding PUF reliability, uniformity, and anomaly detection classification thresholds, this simulation models a representative fleet of five vehicles (**VID 101 to 105**).

### Academic Justification
- **Statistical Uniqueness**: A 5-car fleet provides sufficient combinatorial variance to empirically validate an ideal **~50% Inter-Die Hamming Distance (HD)** across pairwise challenge evaluations.
- **Uniformity & Balance**: Calibrated delay distributions guarantee ~50% intra-device response uniformity (zero systemic bias towards logical '0' or '1').
- **Pipeline Efficiency**: Constraining the baseline fleet to 5 hardware instances maintains crystal-clear waveform trace inspections in GTKWave while keeping dataset footprints optimal for initial SNN/CNN training regimes.

### Fleet Silicon Delay Profiles
| Vehicle | Identifier | Nominal Delay (ps) | Jitter Step (ps) | Base PRNG Seed | Silicon Process Profile       |
|:-------:|:----------:|:------------------:|:----------------:|:--------------:|:------------------------------|
| Car 1   | VID 101    | 100                | 12               | `0xA3B1C5D7`   | Typical / Nominal Corner      |
| Car 2   | VID 102    | 102                | 15               | `0x7E2F4A81`   | Slow Corner, High Jitter      |
| Car 3   | VID 103    | 98                 | 10               | `0x1D4C8B3F`   | Fast Corner, Tight Tolerance  |
| Car 4   | VID 104    | 101                | 18               | `0xF5926E0A`   | High Variance Process Spread  |
| Car 5   | VID 105    | 99                 | 14               | `0x4B8D17C6`   | Balanced Corner               |

All delay profiles are calibrated to ensure an ideal ~50% inter-die Hamming distance across the fleet and balanced ~50% response uniformity per vehicle.

---

## 4. Prerequisites & Environment Setup

### 4.1 Toolchain Installation via Chocolatey (Windows)

To execute this simulation on Windows, install the open-source **Icarus Verilog (`iverilog`)** compiler and runtime along with the **GTKWave** visualizer via Chocolatey:

1. Open PowerShell with Administrator privileges.
2. Run the package installation command:
   ```powershell
   choco install iverilog -y
   ```
   *(Note: This package installs `iverilog`, the `vvp` simulation engine, and `gtkwave`)*.

### 4.2 Python Runtime & Data Loading Dependencies

Ensure Python is installed, along with the `numpy` package required for the machine learning data loader and SNN preprocessing:

```powershell
pip install numpy
```

---

## 5. Executing the Simulation

The simulation workflow is fully automated through a PowerShell runner script. It compiles the Verilog source files, evaluates the 128-bit challenges across all 32 parallel lanes for all 5 vehicles, and generates verification outputs.

### 5.1 Automated Script Execution

1. Open a terminal in the root of the repository.
2. Navigate to the simulation directory and execute the runner:
   ```powershell
   cd hardware-simulation
   .\scripts\run_simulation.ps1
   ```

### 5.2 Manual Command-Line Compilation (Alternative)

If manual compilation is preferred, execute:

```powershell
cd hardware-simulation
iverilog -o puf_sim.out src\mux2to1_gate.v src\d_flip_flop_arbiter.v src\puf_switch_stage.v src\arbiter_puf.v src\parallel_puf.v src\vehicle_fleet_puf.v tb\puf_fleet_tb.v
vvp puf_sim.out
```

---

## 6. Generated Simulation Outputs

Upon successful execution, the script generates two critical output files:

| Output File | Destination Path | Description & Downstream Consumption |
|:------------|:-----------------|:-------------------------------------|
| `puf_crp_export.csv` | `../data/puf_crp_export.csv` | **Hardware Output Dataset**: Contains the 128-bit hex challenges and the unique 32-bit hex responses for all 5 cars. The Python [puf_simulator.py](file:///d:/capstone-2027/edge-vehicles/src/security/puf_simulator.py) script automatically ingests this file. |
| `puf_fleet_waveform.vcd` | `hardware-simulation/puf_fleet_waveform.vcd` | **Value Change Dump (VCD)**: The picosecond-scale waveform file used to visually verify and demonstrate the physical race conditions to faculty and reviewers. |

### Dataset Structure (`data/puf_crp_export.csv`)

```csv
challenge_hex,car1_vid101,car2_vid102,car3_vid103,car4_vid104,car5_vid105
a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5,953a9c59,f4c4f4f4,c455b58e,5c1c2322,06187ce9
4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b,9dac36ca,85938985,241a4925,2b0db4d8,a4eb8025
...
```

Each row provides the applied 128-bit challenge (hex) and the resulting 32-bit parallel response words (hex) for all 5 vehicles.

---

## 7. Waveform Inspection & Physical Race Verification (GTKWave)

To demonstrate why structurally identical circuits produce divergent responses under identical excitation vectors, observe the picosecond timing differentials in GTKWave:

### Step 1: Launch GTKWave
Execute the following from your terminal in the `hardware-simulation` folder:
```powershell
gtkwave puf_fleet_waveform.vcd
```

### Step 2: Append Diagnostic Signals
1. In the upper-left **SST (Structural Search Tree)** panel, select the top-level testbench module: `puf_fleet_tb`.
2. In the signal list below the SST panel, select the following signals and click **Append**:
   - `trigger`
   - `car1_lane0_upper`
   - `car1_lane0_lower`
   - `car2_lane0_upper`
   - `car2_lane0_lower`
   - `car1_response[31:0]`
   - `car2_response[31:0]`

### Step 3: Inspect Picosecond Race Resolution
1. Click the **Zoom In (`+`)** button on the toolbar repeatedly until the timeline scale changes from nanoseconds (`ns`) down to picoseconds (`ps`).
2. Examine the rising edges immediately following the `trigger` pulse.
3. Observe the microscopic arrival time differential ($\Delta t$) between the upper and lower paths:
   - **Car 1 Arrival**: If `car1_lane0_upper` arrives before `car1_lane0_lower`, the arbiter D flip-flop latches logical `1`.
   - **Car 2 Arrival**: If `car2_lane0_lower` arrives before `car2_lane0_upper`, the arbiter D flip-flop latches logical `0`.
4. Comparing Car 1 versus Car 2 visually confirms how identical gate topologies resolve different bit outcomes due to process-induced physical delay variance.

---

## 8. Downstream Integration with Python ML Pipeline

The generated hardware CRPs interface directly with the vehicular software stack:

1. **Hardware Ingestion**: [VehiclePUF](file:///d:/capstone-2027/edge-vehicles/src/security/puf_simulator.py#L6-L66) in `edge-vehicles/src/security/puf_simulator.py` loads `puf_crp_export.csv` according to the active `VEHICLE_ID` (101–105).
2. **Signal Representation**: 32-bit hex responses are mapped into binary NumPy arrays (`dtype=np.float32`) for compatibility with SNN neuromorphic spike encoders.
3. **Cryptographic Root of Trust**: When a challenge is issued by the VSOC Gateway, the vehicle computes its response, extracts `K_session = SHA256(packbits(R > 0))`, and uses this key to authenticate handshake tokens and encrypt continual learning model updates.
