`timescale 1ps / 1ps
//=============================================================================
// Module:  arbiter_puf
// Purpose: Parameterized N-stage Arbiter PUF top module.
//
// Architecture:
//                C[0]           C[1]                  C[N-1]
//                 |              |                      |
//   trigger ─┬─[Stage 0]──┬──[Stage 1]──┬── ... ──[Stage N-1]──┬─ path_upper_arrival ─[D]──> response
//            └─[Stage 0]──┘──[Stage 1]──┘── ... ──[Stage N-1]──┘─ path_lower_arrival ─[CLK]─┘
//              upper path                                          lower path           (DFF)
//
// Delay Parameterization (Clean — per the user's requirement):
//   All delay variations are injected EXCLUSIVELY through these top-level
//   parameters. No delays are hardcoded inside the gate-level primitives.
//
//   Per-stage delay formula:
//     Stage[i] upper MUX delay = NOMINAL_DELAY + UPPER_BIAS + (i % 3) * JITTER_STEP
//     Stage[i] lower MUX delay = NOMINAL_DELAY + LOWER_BIAS + ((i+1) % 3) * JITTER_STEP
//
//   The modular indexing (i%3, (i+1)%3) creates asymmetric, non-uniform
//   per-stage variation — mimicking real process corner distributions.
//
// Pre-Arbiter Race Signals:
//   path_upper_arrival and path_lower_arrival are explicitly exposed so the
//   testbench VCD dump captures the literal picosecond race at the arbiter
//   inputs, enabling visual waveform proof for faculty demonstration.
//=============================================================================

module arbiter_puf #(
    parameter N             = 8,     // Challenge width / number of stages
    parameter NOMINAL_DELAY = 100,   // Base gate delay per primitive (ps)
    parameter UPPER_BIAS    = 0,     // Upper path systematic offset (ps)
    parameter LOWER_BIAS    = 0,     // Lower path systematic offset (ps)
    parameter JITTER_STEP   = 0      // Per-stage jitter modulation step (ps)
)(
    input  wire            trigger,            // Rising edge starts the race
    input  wire [N-1:0]    challenge,          // N-bit challenge vector
    output wire            response,           // Arbiter decision bit (CRP output)
    output wire            path_upper_arrival, // Pre-arbiter upper signal (for VCD waveform)
    output wire            path_lower_arrival  // Pre-arbiter lower signal (for VCD waveform)
);

    // ── Internal delay chain wires ──────────────────────────────────────
    // upper_chain[0] = trigger input,  upper_chain[N] = final upper arrival
    // lower_chain[0] = trigger input,  lower_chain[N] = final lower arrival
    wire [N:0] upper_chain;
    wire [N:0] lower_chain;

    // Both paths originate from the same trigger signal (symmetric start)
    assign upper_chain[0] = trigger;
    assign lower_chain[0] = trigger;

    // ── Generate N switch stages with per-stage delay variation ─────────
    genvar i;
    generate
        for (i = 0; i < N; i = i + 1) begin : stage
            // Compute per-stage delays from top-level parameters
            // The modular pattern creates non-uniform but deterministic variation
            localparam integer STAGE_UPPER_DLY = NOMINAL_DELAY + UPPER_BIAS
                                                 + ((i % 3) * JITTER_STEP);
            localparam integer STAGE_LOWER_DLY = NOMINAL_DELAY + LOWER_BIAS
                                                 + (((i + 1) % 3) * JITTER_STEP);

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
    // These are THE critical signals: the faculty demo depends on seeing
    // the picosecond gap between these two rising edges in GTKWave/EPWave.
    assign path_upper_arrival = upper_chain[N];
    assign path_lower_arrival = lower_chain[N];

    // ── Arbiter: D Flip-Flop captures the race winner ──────────────────
    // Upper path -> D (data), Lower path -> CLK (clock)
    // If upper arrives first: D=1 when CLK rises -> response = 1
    // If lower arrives first: CLK rises while D=0  -> response = 0
    d_flip_flop_arbiter u_arbiter (
        .d   (upper_chain[N]),
        .clk (lower_chain[N]),
        .q   (response)
    );

endmodule
