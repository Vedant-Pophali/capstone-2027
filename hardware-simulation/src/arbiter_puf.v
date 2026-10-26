`timescale 1ps / 1ps
//=============================================================================
// Module:  arbiter_puf
// Purpose: Parameterized N-stage Arbiter PUF delay chain.
//          Each instance produces a single response bit from an N-bit
//          challenge by racing two signal paths through N switch stages.
//
// Architecture:
//                C[0]           C[1]                  C[N-1]
//                 |              |                      |
//   trigger ─┬─[Stage 0]──┬──[Stage 1]──┬── ... ──[Stage N-1]──┬─ path_upper ─[D]──> response
//            └─[Stage 0]──┘──[Stage 1]──┘── ... ──[Stage N-1]──┘─ path_lower ─[CLK]─┘
//              upper path                                          lower path     (DFF)
//
// Delay Parameterization:
//   All delay variations are injected through top-level parameters.
//   A pseudo-random jitter per stage is derived from JITTER_SEED using an
//   LFSR-inspired formula to produce non-linear, non-repeating per-stage
//   variation — closely mimicking real process corner distributions.
//
//   Per-stage delay formula:
//     hash[i]   = JITTER_SEED ^ (i * 2654435761)   // Knuth multiplicative hash
//     jitter[i] = (hash[i] % (JITTER_RANGE + 1))   // Bounded jitter
//     Stage[i] upper MUX delay = NOMINAL_DELAY + UPPER_BIAS + jitter_upper[i]
//     Stage[i] lower MUX delay = NOMINAL_DELAY + LOWER_BIAS + jitter_lower[i]
//
// Pre-Arbiter Race Signals:
//   path_upper_arrival and path_lower_arrival are explicitly exposed so the
//   testbench VCD dump captures the literal picosecond race at the arbiter
//   inputs, enabling visual waveform proof for faculty demonstration.
//=============================================================================

module arbiter_puf #(
    parameter N             = 128,   // Challenge width / number of stages
    parameter NOMINAL_DELAY = 100,   // Base gate delay per primitive (ps)
    parameter UPPER_BIAS    = 0,     // Upper path systematic offset (ps)
    parameter LOWER_BIAS    = 0,     // Lower path systematic offset (ps)
    parameter JITTER_STEP   = 0,     // Per-stage jitter modulation step (ps)
    parameter JITTER_SEED   = 0      // Pseudo-random seed for non-linear jitter
)(
    input  wire            trigger,            // Rising edge starts the race
    input  wire [N-1:0]    challenge,          // N-bit challenge vector
    output wire            response,           // Arbiter decision bit (CRP output)
    output wire            path_upper_arrival, // Pre-arbiter upper signal (for VCD)
    output wire            path_lower_arrival  // Pre-arbiter lower signal (for VCD)
);

    // ── Internal delay chain wires ──────────────────────────────────────
    wire [N:0] upper_chain;
    wire [N:0] lower_chain;

    // Both paths originate from the same trigger signal (symmetric start)
    assign upper_chain[0] = trigger;
    assign lower_chain[0] = trigger;

    // ── Generate N switch stages with per-stage non-linear delay ────────
    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : stage
            // LFSR-inspired per-stage jitter using Knuth multiplicative hash.
            // The XOR with JITTER_SEED ensures each lane (different seed)
            // gets a completely different jitter pattern even with identical
            // UPPER_BIAS / LOWER_BIAS / JITTER_STEP parameters.
            //
            // Upper path hash uses index i; lower uses (i + N) to decorrelate.
            localparam integer HASH_UPPER = (JITTER_SEED ^ (i * 32'd2654435761) ^ 32'h5A5A5A5A) & 32'hFFFFFFFF;
            localparam integer HASH_LOWER = (JITTER_SEED ^ (i * 32'd2246822519) ^ 32'hA5A5A5A5) & 32'hFFFFFFFF;

            // Bound jitter to [0, JITTER_STEP] range (mod is safe since
            // JITTER_STEP+1 >= 1 always; when JITTER_STEP==0, jitter==0).
            localparam integer JITTER_UPPER = (JITTER_STEP > 0)
                ? ((HASH_UPPER % (JITTER_STEP + 1)))
                : 0;
            localparam integer JITTER_LOWER = (JITTER_STEP > 0)
                ? ((HASH_LOWER % (JITTER_STEP + 1)))
                : 0;

            localparam integer STAGE_UPPER_DLY = NOMINAL_DELAY + UPPER_BIAS + JITTER_UPPER;
            localparam integer STAGE_LOWER_DLY = NOMINAL_DELAY + LOWER_BIAS + JITTER_LOWER;

            puf_switch_stage #(
                .DELAY_UPPER_PS (STAGE_UPPER_DLY),
                .DELAY_LOWER_PS (STAGE_LOWER_DLY)
            ) u_switch (
                .upper_in      (upper_chain[i]),
                .lower_in      (lower_chain[i]),
                .challenge_bit (challenge[i]),
                .upper_out     (upper_chain[i+1]),
                .lower_out     (lower_chain[i+1])
            );
        end
    endgenerate

    // ── Expose pre-arbiter race signals for waveform inspection ────────
    assign path_upper_arrival = upper_chain[N];
    assign path_lower_arrival = lower_chain[N];

    // ── Arbiter: D Flip-Flop captures the race winner ──────────────────
    d_flip_flop_arbiter u_arbiter (
        .d   (upper_chain[N]),
        .clk (lower_chain[N]),
        .q   (response)
    );

endmodule
