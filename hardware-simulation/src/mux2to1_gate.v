`timescale 1ps / 1ps
//=============================================================================
// Module:  mux2to1_gate
// Purpose: Gate-level 2:1 Multiplexer with parameterized propagation delay.
//          Used as the fundamental switching element in the Arbiter PUF chain.
//
// Topology:
//          sel ──┬──[NOT]──> sel_n
//                │
//   in0 ────[AND]──┐
//        (sel_n)   [OR]──> out
//   in1 ────[AND]──┘
//          (sel)
//
// Delay:   Each gate (NOT, AND, OR) incurs DELAY_PS picoseconds.
//          Data path propagation (in -> out) = 2 x DELAY_PS (AND + OR)
//          when the select line is pre-settled before the trigger pulse.
//=============================================================================

module mux2to1_gate #(
    parameter DELAY_PS = 100  // Propagation delay per gate (picoseconds)
)(
    input  wire in0,    // Input 0 (selected when sel = 0)
    input  wire in1,    // Input 1 (selected when sel = 1)
    input  wire sel,    // Select line (driven by challenge bit)
    output wire out     // Multiplexer output
);

    wire sel_n;          // Inverted select
    wire and0_out;       // in0 AND sel_n
    wire and1_out;       // in1 AND sel

    not #(DELAY_PS) u_inv  (sel_n,    sel);
    and #(DELAY_PS) u_and0 (and0_out, in0, sel_n);
    and #(DELAY_PS) u_and1 (and1_out, in1, sel);
    or  #(DELAY_PS) u_or   (out,      and0_out, and1_out);

endmodule
