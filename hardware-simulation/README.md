# 32-bit Parallel Arbiter PUF Hardware Simulation

Gate-level Verilog simulation of a 32-bit Parallel Arbiter Physically Unclonable Function (PUF) architecture for vehicular edge network authentication in the Capstone 2027 project.

## Purpose

This simulation provides **visual, waveform-level proof** that identical digital circuits produce unique, hardware-intrinsic 32-bit responses when excited by a 128-bit challenge in a single clock cycle. Microscopic manufacturing delay variations between vehicles generate an ideal ~50% inter-die Hamming distance, serving as physical roots-of-trust for vehicular authentication.

---

## Architecture

### 32-bit Parallel Arbiter PUF (`parallel_puf.v`)

```
                         128-bit Challenge (Shared across all 32 lanes)
                    ┌───────────────────────┼───────────────────────┐
                    │                       │                       │
               [Lane 0]                [Lane 1]       ...      [Lane 31]
             (128 stages)            (128 stages)             (128 stages)
                    │                       │                       │
                resp[0]                 resp[1]       ...       resp[31]
                    └───────────────────────┼───────────────────────┘
                                     32-bit Response
```

Each lane contains an independent 128-stage Arbiter PUF delay chain (`arbiter_puf.v`). A single 128-bit challenge vector is fed into all 32 parallel lanes simultaneously. In a single clock cycle, each lane resolves its internal sub-picosecond delay race to yield 1 response bit, forming the full 32-bit parallel response word.

### Per-Lane Delay Chain (`arbiter_puf.v`)

```
              Challenge[0]    Challenge[1]         Challenge[127]
                   |               |                     |
  trigger ──┬── [Stage 0] ──── [Stage 1] ──── ... ──── [Stage 127] ──┬── D ──[DFF]──> response[k]
            └── [Stage 0] ──── [Stage 1] ──── ... ──── [Stage 127] ──┘── CLK ─┘
               upper path                                                lower path
```

- **Timescale**: `` `timescale 1ps/1ps `` across all modules to preserve picosecond-resolution timing dynamics.
- **Stage Primitives**: Each stage uses 2 gate-level 2:1 multiplexers built from gate primitives (`not`, `and`, `or`).
- **Non-Linear Delay Model**: Per-stage delay variations use multiplicative hash formulas driven by unique per-lane seeds, simulating uncorrelated, non-linear Gaussian silicon variation.

---

## 5-Car Vehicular Fleet (`vehicle_fleet_puf.v`)

Five automotive vehicles (VID 101 to 105) instantiate the exact same 32-bit Parallel Arbiter PUF circuit with unique silicon delay parameters:

| Vehicle | ID  | NOMINAL_DELAY (ps) | JITTER_STEP (ps) | Base Seed   | Silicon Profile               |
|---------|-----|--------------------|------------------|-------------|-------------------------------|
| Car 1   | 101 | 100                | 12               | 0xA3B1C5D7  | Nominal process corner        |
| Car 2   | 102 | 102                | 15               | 0x7E2F4A81  | Slightly slow corner, high jit|
| Car 3   | 103 | 98                 | 10               | 0x1D4C8B3F  | Fast corner, tight tolerance  |
| Car 4   | 104 | 101                | 18               | 0xF5926E0A  | Wide process spread           |
| Car 5   | 105 | 99                 | 14               | 0x4B8D17C6  | Balanced process corner       |

All delay profiles are calibrated to ensure:
- **Inter-Die Hamming Distance**: ~50% (ideal uniqueness across fleet).
- **Per-Car Response Uniformity / Bias**: ~50% (balanced 0s and 1s).

---

## Running the Simulation

### Option A: Local Execution (Icarus Verilog)

```powershell
cd hardware-simulation
.\scripts\run_simulation.ps1
```

### Option B: Manual Command Line

```powershell
cd hardware-simulation
iverilog -o puf_sim.out src\mux2to1_gate.v src\d_flip_flop_arbiter.v src\puf_switch_stage.v src\arbiter_puf.v src\parallel_puf.v src\vehicle_fleet_puf.v tb\puf_fleet_tb.v
vvp puf_sim.out
```

---

## Output Files

| File                     | Location                | Purpose                                                 |
|--------------------------|-------------------------|---------------------------------------------------------|
| `puf_fleet_waveform.vcd` | `hardware-simulation/` | Waveform showing pre-arbiter race signals in GTKWave    |
| `puf_crp_export.csv`     | `data/`                | 128-bit challenge & 32-bit response CRP dataset for SNN |

### CSV Format (`data/puf_crp_export.csv`)

```csv
challenge_hex,car1_vid101,car2_vid102,car3_vid103,car4_vid104,car5_vid105
a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5a5,953a9c59,f4c4f4f4,c455b58e,5c1c2322,06187ce9
4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b4b,9dac36ca,85938985,241a4925,2b0db4d8,a4eb8025
...
```

Each row provides the applied 128-bit challenge (hex) and the resulting 32-bit parallel response words (hex) for all 5 vehicles.

---

## GTKWave Visual Proof Instructions

1. Launch GTKWave:
   ```powershell
   gtkwave hardware-simulation/puf_fleet_waveform.vcd
   ```
2. Under the top-level module `puf_fleet_tb`, add the pre-arbiter race signals:
   - `car1_lane0_upper` vs `car1_lane0_lower` (Car 1 Lane 0 Race)
   - `car2_lane0_upper` vs `car2_lane0_lower` (Car 2 Lane 0 Race)
   - `car1_response[31:0]` and `car2_response[31:0]`
3. Zoom into the rising transition immediately following the `trigger` pulse.
4. Measure the picosecond arrival difference between upper and lower signals:
   - If upper arrives before lower: DFF latches `1`.
   - If lower arrives before upper: DFF latches `0`.
5. Compare Car 1 vs Car 2 to visually demonstrate that identical input stimuli produce different race winners due to silicon-level delay variation.
