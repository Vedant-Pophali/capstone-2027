`timescale 1ps / 1ps
//=============================================================================
// Testbench: puf_fleet_tb
// Purpose:   Feeds identical challenges to all 5 cars simultaneously,
//            captures VCD waveforms (for GTKWave/EPWave), and exports
//            CRPs to CSV (for the SNN/CNN ML pipeline in src/ml).
//
// Outputs:
//   1. puf_fleet_waveform.vcd — Full waveform dump including pre-arbiter
//      race signals (car*_upper_arrival, car*_lower_arrival) showing the
//      literal picosecond timing difference at each arbiter's inputs.
//
//   2. ../data/puf_crp_export.csv — Challenge-Response Pairs for all 5
//      cars, formatted for direct consumption by the ML pipeline.
//
// Key Signals Exposed in VCD:
//   - trigger:              Synchronized start pulse for all cars
//   - challenge[N-1:0]:     The input challenge vector
//   - car*_upper_arrival:   Upper path arrival at arbiter (pre-DFF)
//   - car*_lower_arrival:   Lower path arrival at arbiter (pre-DFF)
//   - car*_response:        Final arbiter decision bits (the CRP)
//
// Faculty Demonstration:
//   In the waveform viewer, zoom into any car's upper_arrival and
//   lower_arrival signals. The picosecond gap between their rising edges
//   IS the race condition. Compare across cars to see how identical logic
//   with different delays produces different outcomes.
//=============================================================================

module puf_fleet_tb;

    // ── Configuration Parameters ──────────────────────────────────────
    parameter N              = 8;      // Challenge width (bits)
    parameter NUM_CHALLENGES = 32;     // Number of challenge vectors to test
    parameter SETTLE_TIME    = 5000;   // Wait time for propagation (ps)
    parameter RESET_TIME     = 2000;   // Dead time between challenges (ps)

    // ── Stimulus Registers ────────────────────────────────────────────
    reg             trigger;
    reg  [N-1:0]    challenge;

    // ── Response Wires ────────────────────────────────────────────────
    wire car1_response, car2_response, car3_response, car4_response, car5_response;

    // ── Pre-Arbiter Race Wires (THE critical faculty demo signals) ────
    // These show the literal rising-edge arrival times at each DFF.
    // The time gap between upper and lower IS the race condition.
    wire car1_upper_arrival, car1_lower_arrival;
    wire car2_upper_arrival, car2_lower_arrival;
    wire car3_upper_arrival, car3_lower_arrival;
    wire car4_upper_arrival, car4_lower_arrival;
    wire car5_upper_arrival, car5_lower_arrival;

    // ── Instantiate 5-Car Fleet ───────────────────────────────────────
    vehicle_fleet_puf #(.N(N)) uut (
        .trigger            (trigger),
        .challenge          (challenge),

        .car1_response      (car1_response),
        .car2_response      (car2_response),
        .car3_response      (car3_response),
        .car4_response      (car4_response),
        .car5_response      (car5_response),

        .car1_upper_arrival (car1_upper_arrival),
        .car1_lower_arrival (car1_lower_arrival),
        .car2_upper_arrival (car2_upper_arrival),
        .car2_lower_arrival (car2_lower_arrival),
        .car3_upper_arrival (car3_upper_arrival),
        .car3_lower_arrival (car3_lower_arrival),
        .car4_upper_arrival (car4_upper_arrival),
        .car4_lower_arrival (car4_lower_arrival),
        .car5_upper_arrival (car5_upper_arrival),
        .car5_lower_arrival (car5_lower_arrival)
    );

    // ── VCD Waveform Dump ─────────────────────────────────────────────
    // This is CRITICAL: generates the .vcd file for GTKWave / EPWave.
    // $dumpvars(0, ...) dumps ALL signals recursively, including the
    // internal stage chains — enabling full delay chain inspection.
    initial begin
        $dumpfile("puf_fleet_waveform.vcd");
        $dumpvars(0, puf_fleet_tb);
    end

    // ── CSV File Handle & Counters ────────────────────────────────────
    integer csv_file;
    integer i;
    integer diverge_count;
    integer total_ones_car1, total_ones_car2, total_ones_car3;
    integer total_ones_car4, total_ones_car5;

    // ── Main Stimulus Block ───────────────────────────────────────────
    initial begin
        // Initialize all signals
        trigger         = 1'b0;
        challenge       = {N{1'b0}};
        diverge_count   = 0;
        total_ones_car1 = 0;
        total_ones_car2 = 0;
        total_ones_car3 = 0;
        total_ones_car4 = 0;
        total_ones_car5 = 0;

        // ── Open CSV file for ML pipeline export ──────────────────────
        csv_file = $fopen("../data/puf_crp_export.csv", "w");
        if (csv_file == 0) begin
            $display("");
            $display("[ERROR] Could not open CSV file for writing.");
            $display("[HINT]  Ensure the data/ directory exists at the project root.");
            $display("[HINT]  Run simulation from the hardware-simulation/ directory:");
            $display("          cd hardware-simulation && vvp puf_sim.out");
            $display("");
            $finish;
        end

        // CSV header row
        $fdisplay(csv_file, "challenge_bin,challenge_dec,car1_vid101,car2_vid102,car3_vid103,car4_vid104,car5_vid105");

        // ── Console Banner ────────────────────────────────────────────
        $display("");
        $display("================================================================");
        $display("       ARBITER PUF FLEET SIMULATION - 5 Cars, Same Logic");
        $display("       Proving: Identical circuits produce different CRPs");
        $display("       due to synthetic manufacturing delay variations.");
        $display("================================================================");
        $display("");
        $display(" Params: N=%0d stages, %0d challenges, settle=%0dps",
                 N, NUM_CHALLENGES, SETTLE_TIME);
        $display("");
        $display(" Challenge  | Car1 | Car2 | Car3 | Car4 | Car5 | Divergent?");
        $display("------------|------|------|------|------|------|------------");

        // Allow initial signal settling (challenge sel lines through MUX NOT gates)
        #(RESET_TIME);

        // ── Sweep Challenges ──────────────────────────────────────────
        for (i = 0; i < NUM_CHALLENGES; i = i + 1) begin
            // Set challenge vector
            challenge = i;

            // Reset trigger and wait for new challenge select lines to settle
            trigger = 1'b0;
            #(RESET_TIME);

            // *** FIRE THE TRIGGER — starts the race in all 5 cars ***
            trigger = 1'b1;

            // Wait for signals to propagate through all N stages + arbiter
            // During this time, the VCD captures the exact picosecond
            // arrival times on car*_upper_arrival and car*_lower_arrival.
            #(SETTLE_TIME);

            // ── Capture and Display Results ───────────────────────────
            // Track per-car response totals for bias analysis
            total_ones_car1 = total_ones_car1 + car1_response;
            total_ones_car2 = total_ones_car2 + car2_response;
            total_ones_car3 = total_ones_car3 + car3_response;
            total_ones_car4 = total_ones_car4 + car4_response;
            total_ones_car5 = total_ones_car5 + car5_response;

            // Check if any car produced a different response
            if (car1_response !== car2_response ||
                car2_response !== car3_response ||
                car3_response !== car4_response ||
                car4_response !== car5_response) begin
                $display(" %b |  %b   |  %b   |  %b   |  %b   |  %b   |  YES *",
                         challenge, car1_response, car2_response, car3_response,
                         car4_response, car5_response);
                diverge_count = diverge_count + 1;
            end else begin
                $display(" %b |  %b   |  %b   |  %b   |  %b   |  %b   |  no",
                         challenge, car1_response, car2_response, car3_response,
                         car4_response, car5_response);
            end

            // ── Write to CSV ──────────────────────────────────────────
            $fdisplay(csv_file, "%b,%0d,%b,%b,%b,%b,%b",
                      challenge, i,
                      car1_response, car2_response, car3_response,
                      car4_response, car5_response);

            // De-assert trigger (falling edge propagates, clean waveform)
            trigger = 1'b0;
            #(RESET_TIME);
        end

        // ── Summary Report ────────────────────────────────────────────
        $display("------------|------|------|------|------|------|------------");
        $display("");
        $display("================================================================");
        $display("  RESULTS SUMMARY");
        $display("================================================================");
        $display("  Total challenges tested       : %0d", NUM_CHALLENGES);
        $display("  Divergent responses (unique)   : %0d / %0d", diverge_count, NUM_CHALLENGES);
        $display("  Identical responses            : %0d / %0d", NUM_CHALLENGES - diverge_count, NUM_CHALLENGES);
        $display("  Inter-die uniqueness ratio     : %0d%%", (diverge_count * 100) / NUM_CHALLENGES);
        $display("");
        $display("  Per-car response bias (ones / total):");
        $display("    Car 1 (VID 101): %0d / %0d", total_ones_car1, NUM_CHALLENGES);
        $display("    Car 2 (VID 102): %0d / %0d", total_ones_car2, NUM_CHALLENGES);
        $display("    Car 3 (VID 103): %0d / %0d", total_ones_car3, NUM_CHALLENGES);
        $display("    Car 4 (VID 104): %0d / %0d", total_ones_car4, NUM_CHALLENGES);
        $display("    Car 5 (VID 105): %0d / %0d", total_ones_car5, NUM_CHALLENGES);
        $display("================================================================");
        $display("");
        $display("  Output files generated:");
        $display("    [VCD] puf_fleet_waveform.vcd      <- Load in GTKWave / EPWave");
        $display("    [CSV] ../data/puf_crp_export.csv  <- Feed to SNN/CNN pipeline");
        $display("");
        $display("  GTKWave Inspection Guide:");
        $display("    1. Add signals: car*_upper_arrival, car*_lower_arrival");
        $display("    2. Zoom into rising edges after each trigger pulse");
        $display("    3. Measure the picosecond gap between upper and lower");
        $display("    4. Compare gap polarity across all 5 cars");
        $display("    5. The response bit (0 or 1) matches which path won");
        $display("================================================================");

        // Close CSV file
        $fclose(csv_file);

        $finish;
    end

endmodule
