# Arbiter PUF Hardware Simulation

Gate-level Verilog simulation of an Arbiter Physically Unclonable Function (PUF) for the Capstone 2027 automotive authentication system.

## Purpose

This simulation provides **visual, waveform-level proof** that identical digital circuits produce different Challenge-Response Pairs (CRPs) due to microscopic manufacturing delay variations — the fundamental principle behind hardware-based vehicle authentication without certificates or passwords.

---

## Architecture

```
              Challenge[0]    Challenge[1]         Challenge[N-1]
                  |               |                     |
 trigger ──┬── [Stage 0] ──── [Stage 1] ──── ... ──── [Stage N-1] ──┬── D ──[DFF]──> response
            └── [Stage 0] ──── [Stage 1] ──── ... ──── [Stage N-1] ──┘── CLK ─┘
               upper path                                              lower path
```

Each **stage** is a 2×2 switch block containing two gate-level multiplexers (NOT + AND + OR primitives). The challenge bit at each stage controls whether the upper and lower paths route **straight-through** or **crossover**. After N stages, the two paths **race** to a D Flip-Flop arbiter — whichever rising edge arrives first determines the response bit.

### Gate-Level Detail (per MUX)

```
sel ──┬──[NOT #delay]──> sel_n
      │
in0 ──[AND #delay]──┐
       (with sel_n)  [OR #delay]──> out
in1 ──[AND #delay]──┘
       (with sel)
```

Data path propagation = **2 × delay** (AND + OR) per MUX when select is pre-settled.

---

## 5-Car Fleet Simulation

Five instances of the **exact same** PUF circuit are instantiated in `vehicle_fleet_puf.v`, each with unique delay parameters representing real-world silicon process variation:

| Vehicle | ID  | UPPER_BIAS (ps) | LOWER_BIAS (ps) | JITTER_STEP (ps) | Silicon Character |
|---------|-----|-----------------|------------------|-------------------|-------------------|
| Car 1   | 101 | 3               | 0                | 2                 | Slight upper-slow |
| Car 2   | 102 | 0               | 5                | 3                 | Lower-path bias   |
| Car 3   | 103 | 7               | 2                | 1                 | Strong upper-heavy|
| Car 4   | 104 | 1               | 8                | 4                 | Strong lower-heavy|
| Car 5   | 105 | 4               | 1                | 5                 | High-jitter       |

**All delays are injected via parameter overrides at instantiation time** — no values are hardcoded inside the gate primitives.

---

## Quick Start

### Option A: Local Simulation (Icarus Verilog)

```powershell
# Install Icarus Verilog (pick one):
#   Download: https://bleyer.org/icarus/
#   Chocolatey: choco install iverilog
#   Scoop: scoop install iverilog

# Run the simulation:
cd hardware-simulation
.\scripts\run_simulation.ps1
```

### Option B: Online via EDA Playground (No Install)

1. Go to [EDA Playground](https://www.edaplayground.com)
2. Select **Icarus Verilog 12.0** as the simulator
3. **Design panel**: Paste contents of all 5 files in `src/` (concatenated in any order)
4. **Testbench panel**: Paste `tb/puf_fleet_tb.v`
5. Check ✅ **"Open EPWave after run"**
6. Click **Run**

> **Note:** EDA Playground runs in a cloud sandbox. VCD waveforms will be viewable in EPWave, but the CSV file will not be saved locally. Use Option A for the full output.

---

## Viewing Waveforms (The Faculty Demo)

After simulation, open `puf_fleet_waveform.vcd` in **GTKWave** or **EPWave**.

### Key Signals to Add

| Signal Name                           | What It Proves                                        |
|---------------------------------------|-------------------------------------------------------|
| `trigger`                             | Synchronized start pulse — same for all 5 cars       |
| `challenge[7:0]`                      | The input challenge vector — identical for all cars   |
| `car1_upper_arrival`                  | Car 1's upper path arrival at arbiter                 |
| `car1_lower_arrival`                  | Car 1's lower path arrival at arbiter                 |
| `car2_upper_arrival` ... `car5_lower_arrival` | Same signals for all other cars              |
| `car1_response` ... `car5_response`   | Final arbiter decisions — the CRP output bits         |

### What to Look For

1. **Zoom** into the rising edges of `car1_upper_arrival` and `car1_lower_arrival` right after a `trigger` pulse.
2. **Measure** the picosecond gap between the two edges — this is the literal **race condition**.
3. **Compare** the same gap across all 5 cars — each car has a different gap because of its unique delay profile.
4. **Observe** that the `response` bit (0 or 1) matches which path won the race:
   - Upper arrived first → response = **1**
   - Lower arrived first → response = **0**
5. **Note** that different challenges change the routing through the switch stages, producing different race outcomes even within the same car.

---

## Output Files

| File                     | Location                        | Purpose                                              |
|--------------------------|---------------------------------|------------------------------------------------------|
| `puf_fleet_waveform.vcd` | `hardware-simulation/`         | VCD waveform for GTKWave/EPWave visual proof         |
| `puf_crp_export.csv`     | `data/`                        | CRP dataset for SNN/CNN ML pipeline integration      |

### CSV Format

```csv
challenge_bin,challenge_dec,car1_vid101,car2_vid102,car3_vid103,car4_vid104,car5_vid105
00000000,0,0,1,0,1,0
00000001,1,1,0,1,0,1
00000010,2,1,1,0,0,1
...
```

Each row represents one challenge applied simultaneously to all 5 cars. The response columns contain the single-bit arbiter output for each car.

---

## Integration with ML Pipeline

The exported CSV in `data/puf_crp_export.csv` can be loaded directly by the SNN/CNN models in `src/ml/` for:

- **Training** attack detection models on hardware-accurate CRP data
- **Validating** PUF uniqueness metrics (inter-die Hamming distance)
- **Benchmarking** against the Python-based pypuf simulation in `edge-vehicles/src/security/puf_simulator.py`

Example Python loading:

```python
import pandas as pd
df = pd.read_csv("data/puf_crp_export.csv")
# df columns: challenge_bin, challenge_dec, car1_vid101, ..., car5_vid105
```

---

## File Structure

```
hardware-simulation/
├── src/
│   ├── mux2to1_gate.v          Gate-level 2:1 MUX (NOT + AND + OR primitives)
│   ├── d_flip_flop_arbiter.v   Edge-triggered D-FF (race arbiter)
│   ├── puf_switch_stage.v      2×2 switch block (straight/cross routing)
│   ├── arbiter_puf.v           N-stage parameterized PUF top module
│   └── vehicle_fleet_puf.v     5-car fleet with delay parameter overrides
├── tb/
│   └── puf_fleet_tb.v          Testbench: VCD dump + CSV export + console table
├── scripts/
│   └── run_simulation.ps1      One-click compile & run script
└── README.md                   This file
```

---

## Relationship to Other Components

| Component                                    | Role                                      |
|----------------------------------------------|-------------------------------------------|
| `edge-vehicles/src/security/puf_simulator.py`| Python math-model PUF (pypuf wrapper)     |
| `scripts/factory_enrollment.py`              | Seeds CRP database for fleet-manager      |
| `scripts/visualize_hardware_metrics.py`      | Generates uniqueness/reliability graphs   |
| **This module (hardware-simulation/)**       | **Gate-level Verilog proof with waveforms**|

The Python simulation provides statistical proof (Hamming distance graphs).  
The Verilog simulation provides **physical proof** (waveform-visible timing races).  
Together, they form a complete hardware security argument for the capstone presentation.
