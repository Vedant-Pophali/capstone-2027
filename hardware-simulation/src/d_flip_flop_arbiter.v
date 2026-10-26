`timescale 1ps / 1ps
//=============================================================================
// Module:  d_flip_flop_arbiter
// Purpose: Edge-triggered D Flip-Flop serving as the Arbiter in the PUF.
//          Determines the race winner between the upper and lower delay paths.
//
// Operation:
//   - D input  <- Upper path arrival signal
//   - CLK input <- Lower path arrival signal
//   - On posedge CLK (lower path arrives):
//       If D is already HIGH (upper was faster)  -> Q = 1  (Response bit)
//       If D is still LOW  (upper was slower)     -> Q = 0  (Response bit)
//
// This is the decision element that converts a sub-picosecond timing race
// into a deterministic digital bit — the fundamental arbiter of the PUF.
//=============================================================================

module d_flip_flop_arbiter (
    input  wire d,      // Data — upper path arrival
    input  wire clk,    // Clock — lower path arrival
    output reg  q       // Arbiter decision (response bit)
);

    initial q = 1'b0;

    always @(posedge clk) begin
        q <= d;
    end

endmodule
