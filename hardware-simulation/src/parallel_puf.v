`timescale 1ps / 1ps
//=============================================================================
// Module:  parallel_puf
// Purpose: 32-bit Parallel Arbiter PUF — instantiates 32 independent arbiter
//          PUF delay chains in parallel. A single 128-bit challenge is fed
//          to ALL 32 chains simultaneously. Each chain produces 1 response
//          bit, yielding a 32-bit response in a single clock cycle.
//
// Architecture:
//                          128-bit challenge
//                    ┌──────────┼──────────┐
//                    │          │          │
//              [Lane 0]   [Lane 1]  ... [Lane 31]
//                │          │          │
//              resp[0]    resp[1]    resp[31]
//                    └──────────┼──────────┘
//                          32-bit response
//
// Per-Lane Variation:
//   Each lane receives a unique JITTER_SEED derived from the car-level
//   BASE_SEED parameter:
//     lane_seed[k] = BASE_SEED ^ (k * 2862933555)  // Weyl sequence hash
//
//   This ensures that even though all 32 lanes share the same challenge
//   and bias parameters, each lane accumulates a different total delay —
//   producing a unique response bit. The per-stage jitter within each
//   lane is further diversified by the LFSR-hash inside arbiter_puf.
//
// Pre-Arbiter Race Signals:
//   Lane 0's upper/lower arrival signals are exposed for GTKWave/EPWave
//   waveform inspection. Additional lanes can be probed via hierarchical
//   $dumpvars in the testbench.
//=============================================================================

module parallel_puf #(
    parameter N             = 128,   // Challenge width per lane (stages)
    parameter RESP_BITS     = 32,    // Number of parallel lanes / response width
    parameter NOMINAL_DELAY = 100,   // Base gate delay (ps)
    parameter UPPER_BIAS    = 0,     // Upper path systematic offset (ps)
    parameter LOWER_BIAS    = 0,     // Lower path systematic offset (ps)
    parameter JITTER_STEP   = 0,     // Max per-stage jitter amplitude (ps)
    parameter BASE_SEED     = 0      // Car-level seed for per-lane diversification
)(
    input  wire                trigger,            // Race start pulse
    input  wire [N-1:0]        challenge,          // 128-bit challenge (shared)
    output wire [RESP_BITS-1:0] response,          // 32-bit parallel response

    // Lane 0 pre-arbiter race signals (for waveform proof)
    output wire                lane0_upper_arrival,
    output wire                lane0_lower_arrival
);

    // ── Internal wires for all lanes' pre-arbiter signals ──────────────
    wire [RESP_BITS-1:0] lane_upper;
    wire [RESP_BITS-1:0] lane_lower;

    // ── Generate 32 parallel arbiter PUF lanes ─────────────────────────
    genvar k;
    generate
        for (k = 0; k < RESP_BITS; k = k + 1) begin : lane
            // Per-lane seed: Weyl-sequence hash ensures each lane diverges
            // from the car's base seed in a non-linear, non-repeating way.
            localparam integer LANE_SEED = BASE_SEED ^ (k * 2862933555);

            arbiter_puf #(
                .N             (N),
                .NOMINAL_DELAY (NOMINAL_DELAY),
                .UPPER_BIAS    (UPPER_BIAS),
                .LOWER_BIAS    (LOWER_BIAS),
                .JITTER_STEP   (JITTER_STEP),
                .JITTER_SEED   (LANE_SEED)
            ) u_lane (
                .trigger            (trigger),
                .challenge          (challenge),
                .response           (response[k]),
                .path_upper_arrival (lane_upper[k]),
                .path_lower_arrival (lane_lower[k])
            );
        end
    endgenerate

    // ── Expose lane 0 race signals for GTKWave inspection ──────────────
    assign lane0_upper_arrival = lane_upper[0];
    assign lane0_lower_arrival = lane_lower[0];

endmodule
