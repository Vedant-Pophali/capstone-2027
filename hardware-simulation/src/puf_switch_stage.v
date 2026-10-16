`timescale 1ps / 1ps
//=============================================================================
// Module:  puf_switch_stage
// Purpose: A single 2x2 switch stage in the Arbiter PUF delay chain.
//          Implements challenge-controlled path routing using two MUXes.
//
// Routing Table:
//   challenge_bit = 0 (Straight):
//       upper_in -> upper_out    (via upper MUX, selecting in0)
//       lower_in -> lower_out    (via lower MUX, selecting in0)
//
//   challenge_bit = 1 (Crossover):
//       lower_in -> upper_out    (via upper MUX, selecting in1)
//       upper_in -> lower_out    (via lower MUX, selecting in1)
//
// Delay Injection:
//   Each MUX has independently parameterized gate delays (DELAY_UPPER_PS,
//   DELAY_LOWER_PS), enabling per-path manufacturing variation simulation.
//   These are set via parameter overrides from the parent module — never
//   hardcoded here.
//=============================================================================

module puf_switch_stage #(
    parameter DELAY_UPPER_PS = 100,   // Gate delay for upper-path MUX (ps)
    parameter DELAY_LOWER_PS = 100    // Gate delay for lower-path MUX (ps)
)(
    input  wire upper_in,        // Upper path input
    input  wire lower_in,        // Lower path input
    input  wire challenge_bit,   // Challenge bit controlling routing
    output wire upper_out,       // Upper path output
    output wire lower_out        // Lower path output
);

    // ── Upper MUX: straight = upper_in (in0), cross = lower_in (in1) ──
    mux2to1_gate #(
        .DELAY_PS (DELAY_UPPER_PS)
    ) u_mux_upper (
        .in0 (upper_in),
        .in1 (lower_in),
        .sel (challenge_bit),
        .out (upper_out)
    );

    // ── Lower MUX: straight = lower_in (in0), cross = upper_in (in1) ──
    mux2to1_gate #(
        .DELAY_PS (DELAY_LOWER_PS)
    ) u_mux_lower (
        .in0 (lower_in),
        .in1 (upper_in),
        .sel (challenge_bit),
        .out (lower_out)
    );

endmodule
