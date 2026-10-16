`timescale 1ps / 1ps
//=============================================================================
// Module:  vehicle_fleet_puf
// Purpose: Instantiates 5 identical Arbiter PUF circuits representing 5
//          different automotive vehicles. Each instance receives UNIQUE
//          delay parameters simulating manufacturing process variations
//          (different silicon, same mask/design).
//
// Key Principle:
//   ALL 5 instances share the EXACT SAME gate-level structure (mux2to1_gate,
//   puf_switch_stage, d_flip_flop_arbiter). ONLY the delay parameters differ —
//   modeling sub-nanometer threshold voltage variations, oxide thickness
//   differences, and dopant fluctuations inherent in real CMOS fabrication.
//
// Clean Parameterization:
//   All synthetic delays are passed as parameter overrides at instantiation
//   time (here in this file). The gate-level modules themselves contain
//   ZERO hardcoded delay values — they only use the parameters they receive.
//
// Delay Profiles (picoseconds):
//   +---------+-------------+------------+-------------+---------------------+
//   | Vehicle | UPPER_BIAS  | LOWER_BIAS | JITTER_STEP | Silicon Character   |
//   +---------+-------------+------------+-------------+---------------------+
//   | Car 1   |      3      |      0     |      2      | Slight upper-slow   |
//   | Car 2   |      0      |      5     |      3      | Lower-path bias     |
//   | Car 3   |      7      |      2     |      1      | Strong upper-heavy  |
//   | Car 4   |      1      |      8     |      4      | Strong lower-heavy  |
//   | Car 5   |      4      |      1     |      5      | Moderate, high-jit  |
//   +---------+-------------+------------+-------------+---------------------+
//
// Pre-Arbiter Race Signals:
//   Each car exposes its path_upper_arrival and path_lower_arrival wires
//   so the testbench VCD dump captures the literal timing race for each
//   vehicle independently.
//=============================================================================

module vehicle_fleet_puf #(
    parameter N = 8   // Challenge width (bits)
)(
    input  wire            trigger,
    input  wire [N-1:0]    challenge,

    // ── Response outputs (one bit per car) ──
    output wire            car1_response,
    output wire            car2_response,
    output wire            car3_response,
    output wire            car4_response,
    output wire            car5_response,

    // ── Pre-arbiter race signals (for waveform proof) ──
    // Each pair shows the literal picosecond gap at the arbiter inputs.
    output wire            car1_upper_arrival,  car1_lower_arrival,
    output wire            car2_upper_arrival,  car2_lower_arrival,
    output wire            car3_upper_arrival,  car3_lower_arrival,
    output wire            car4_upper_arrival,  car4_lower_arrival,
    output wire            car5_upper_arrival,  car5_lower_arrival
);

    // ================================================================
    //  Car 1 — Vehicle ID 101
    //  Silicon Character: Slight upper-path bias
    //  Upper path is marginally slower; low per-stage jitter.
    // ================================================================
    arbiter_puf #(
        .N             (N),
        .NOMINAL_DELAY (100),
        .UPPER_BIAS    (3),
        .LOWER_BIAS    (0),
        .JITTER_STEP   (2)
    ) u_car1 (
        .trigger            (trigger),
        .challenge          (challenge),
        .response           (car1_response),
        .path_upper_arrival (car1_upper_arrival),
        .path_lower_arrival (car1_lower_arrival)
    );

    // ================================================================
    //  Car 2 — Vehicle ID 102
    //  Silicon Character: Lower-path bias (opposite polarity to Car 1)
    //  Lower path is noticeably slower; moderate jitter.
    // ================================================================
    arbiter_puf #(
        .N             (N),
        .NOMINAL_DELAY (100),
        .UPPER_BIAS    (0),
        .LOWER_BIAS    (5),
        .JITTER_STEP   (3)
    ) u_car2 (
        .trigger            (trigger),
        .challenge          (challenge),
        .response           (car2_response),
        .path_upper_arrival (car2_upper_arrival),
        .path_lower_arrival (car2_lower_arrival)
    );

    // ================================================================
    //  Car 3 — Vehicle ID 103
    //  Silicon Character: Strong upper-path bias, minimal jitter
    //  Upper path is significantly slower; very stable per-stage.
    // ================================================================
    arbiter_puf #(
        .N             (N),
        .NOMINAL_DELAY (100),
        .UPPER_BIAS    (7),
        .LOWER_BIAS    (2),
        .JITTER_STEP   (1)
    ) u_car3 (
        .trigger            (trigger),
        .challenge          (challenge),
        .response           (car3_response),
        .path_upper_arrival (car3_upper_arrival),
        .path_lower_arrival (car3_lower_arrival)
    );

    // ================================================================
    //  Car 4 — Vehicle ID 104
    //  Silicon Character: Strong lower-path bias, high jitter
    //  Lower path is heavily biased; large per-stage variation.
    // ================================================================
    arbiter_puf #(
        .N             (N),
        .NOMINAL_DELAY (100),
        .UPPER_BIAS    (1),
        .LOWER_BIAS    (8),
        .JITTER_STEP   (4)
    ) u_car4 (
        .trigger            (trigger),
        .challenge          (challenge),
        .response           (car4_response),
        .path_upper_arrival (car4_upper_arrival),
        .path_lower_arrival (car4_lower_arrival)
    );

    // ================================================================
    //  Car 5 — Vehicle ID 105
    //  Silicon Character: Moderate upper bias, highest jitter step
    //  Balanced bias but aggressive per-stage modulation.
    // ================================================================
    arbiter_puf #(
        .N             (N),
        .NOMINAL_DELAY (100),
        .UPPER_BIAS    (4),
        .LOWER_BIAS    (1),
        .JITTER_STEP   (5)
    ) u_car5 (
        .trigger            (trigger),
        .challenge          (challenge),
        .response           (car5_response),
        .path_upper_arrival (car5_upper_arrival),
        .path_lower_arrival (car5_lower_arrival)
    );

endmodule
