`timescale 1ps / 1ps
//=============================================================================
// Module:  vehicle_fleet_puf
// Purpose: Instantiates 5 Parallel Arbiter PUF circuits representing 5
//          different automotive vehicles. Each 32-bit parallel PUF receives
//          UNIQUE delay parameters and a unique BASE_SEED, simulating
//          manufacturing process variations (different silicon, same design).
//
// Architecture Upgrade:
//   OLD: 1-bit sequential Arbiter PUF (8-stage, 8-bit challenge, 1-bit response)
//   NEW: 32-bit Parallel Arbiter PUF (128-stage × 32 lanes, 128-bit challenge,
//        32-bit response in a single cycle)
//
// Key Principle:
//   ALL 5 instances share the EXACT SAME gate-level structure. ONLY the delay
//   parameters and jitter seeds differ — modeling sub-nanometer process
//   variations inherent in real CMOS fabrication.
//
// Delay Profiles (calibrated for 50% inter-die Hamming distance & balanced bias):
//   +---------+--------+--------+--------+--------+-------------+
//   | Vehicle | NOM_DLY| UP_BIAS| LO_BIAS| JIT_STP| BASE_SEED   |
//   +---------+--------+--------+--------+--------+-------------+
//   | Car 1   |  100   |   0    |   0    |  12    | 0xA3B1C5D7  |
//   | Car 2   |  102   |   0    |   0    |  15    | 0x7E2F4A81  |
//   | Car 3   |   98   |   0    |   0    |  10    | 0x1D4C8B3F  |
//   | Car 4   |  101   |   0    |   0    |  18    | 0xF5926E0A  |
//   | Car 5   |   99   |   0    |   0    |  14    | 0x4B8D17C6  |
//   +---------+--------+--------+--------+--------+-------------+
//
// Pre-Arbiter Race Signals:
//   Each car exposes lane 0's upper/lower arrival for GTKWave waveform proof.
//=============================================================================

module vehicle_fleet_puf #(
    parameter N         = 128,  // Challenge width (bits) / stages per lane
    parameter RESP_BITS = 32    // Response width (parallel lanes)
)(
    input  wire                 trigger,
    input  wire [N-1:0]         challenge,

    // ── 32-bit response outputs (one word per car) ──
    output wire [RESP_BITS-1:0] car1_response,
    output wire [RESP_BITS-1:0] car2_response,
    output wire [RESP_BITS-1:0] car3_response,
    output wire [RESP_BITS-1:0] car4_response,
    output wire [RESP_BITS-1:0] car5_response,

    // ── Pre-arbiter race signals for lane 0 (waveform proof) ──
    output wire                 car1_lane0_upper,  car1_lane0_lower,
    output wire                 car2_lane0_upper,  car2_lane0_lower,
    output wire                 car3_lane0_upper,  car3_lane0_lower,
    output wire                 car4_lane0_upper,  car4_lane0_lower,
    output wire                 car5_lane0_upper,  car5_lane0_lower
);

    // ================================================================
    //  Car 1 — Vehicle ID 101
    //  NOMINAL_DELAY=100ps, JITTER_STEP=12ps, BASE_SEED=0xA3B1C5D7
    // ================================================================
    parallel_puf #(
        .N             (N),
        .RESP_BITS     (RESP_BITS),
        .NOMINAL_DELAY (100),
        .UPPER_BIAS    (0),
        .LOWER_BIAS    (0),
        .JITTER_STEP   (12),
        .BASE_SEED     (32'hA3B1C5D7)
    ) u_car1 (
        .trigger             (trigger),
        .challenge           (challenge),
        .response            (car1_response),
        .lane0_upper_arrival (car1_lane0_upper),
        .lane0_lower_arrival (car1_lane0_lower)
    );

    // ================================================================
    //  Car 2 — Vehicle ID 102
    //  NOMINAL_DELAY=102ps, JITTER_STEP=15ps, BASE_SEED=0x7E2F4A81
    // ================================================================
    parallel_puf #(
        .N             (N),
        .RESP_BITS     (RESP_BITS),
        .NOMINAL_DELAY (102),
        .UPPER_BIAS    (0),
        .LOWER_BIAS    (0),
        .JITTER_STEP   (15),
        .BASE_SEED     (32'h7E2F4A81)
    ) u_car2 (
        .trigger             (trigger),
        .challenge           (challenge),
        .response            (car2_response),
        .lane0_upper_arrival (car2_lane0_upper),
        .lane0_lower_arrival (car2_lane0_lower)
    );

    // ================================================================
    //  Car 3 — Vehicle ID 103
    //  NOMINAL_DELAY=98ps, JITTER_STEP=10ps, BASE_SEED=0x1D4C8B3F
    // ================================================================
    parallel_puf #(
        .N             (N),
        .RESP_BITS     (RESP_BITS),
        .NOMINAL_DELAY (98),
        .UPPER_BIAS    (0),
        .LOWER_BIAS    (0),
        .JITTER_STEP   (10),
        .BASE_SEED     (32'h1D4C8B3F)
    ) u_car3 (
        .trigger             (trigger),
        .challenge           (challenge),
        .response            (car3_response),
        .lane0_upper_arrival (car3_lane0_upper),
        .lane0_lower_arrival (car3_lane0_lower)
    );

    // ================================================================
    //  Car 4 — Vehicle ID 104
    //  NOMINAL_DELAY=101ps, JITTER_STEP=18ps, BASE_SEED=0xF5926E0A
    // ================================================================
    parallel_puf #(
        .N             (N),
        .RESP_BITS     (RESP_BITS),
        .NOMINAL_DELAY (101),
        .UPPER_BIAS    (0),
        .LOWER_BIAS    (0),
        .JITTER_STEP   (18),
        .BASE_SEED     (32'hF5926E0A)
    ) u_car4 (
        .trigger             (trigger),
        .challenge           (challenge),
        .response            (car4_response),
        .lane0_upper_arrival (car4_lane0_upper),
        .lane0_lower_arrival (car4_lane0_lower)
    );

    // ================================================================
    //  Car 5 — Vehicle ID 105
    //  NOMINAL_DELAY=99ps, JITTER_STEP=14ps, BASE_SEED=0x4B8D17C6
    // ================================================================
    parallel_puf #(
        .N             (N),
        .RESP_BITS     (RESP_BITS),
        .NOMINAL_DELAY (99),
        .UPPER_BIAS    (0),
        .LOWER_BIAS    (0),
        .JITTER_STEP   (14),
        .BASE_SEED     (32'h4B8D17C6)
    ) u_car5 (
        .trigger             (trigger),
        .challenge           (challenge),
        .response            (car5_response),
        .lane0_upper_arrival (car5_lane0_upper),
        .lane0_lower_arrival (car5_lane0_lower)
    );

endmodule
