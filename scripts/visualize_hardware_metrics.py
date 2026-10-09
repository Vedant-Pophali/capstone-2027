#!/usr/bin/env python3
"""
visualize_hardware_metrics.py — PUF Hardware Simulation Proof-of-Concept Visualizer

Generates the two canonical hardware evaluation graphs for an ArbiterPUF simulation:

  Graph 1 — Uniqueness (Inter-Die Hamming Distance)
    Demonstrates that different simulated vehicles produce different responses to the
    same challenge. A good PUF peaks at ~50% Hamming Distance (HD), forming a bell curve.
    This proves that no two vehicles are identically "manufactured".

  Graph 2 — Reliability (Intra-Die Hamming Distance)
    Demonstrates that the same vehicle, queried with the same challenge under simulated
    environmental noise (temperature/voltage variation), produces a consistent response
    with a low bit-error rate (typically 1–5%).
    This proves that the simulation realistically models physical hardware jitter.

These plots are the standard academic presentation format used in IEEE/ACM PUF papers
when physical silicon is not available (purely software mathematical delay model).

Usage:
    python visualize_hardware_metrics.py
    python visualize_hardware_metrics.py --vehicles 100 --challenges 200 --noise 0.03
"""

import argparse
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — safe inside Docker
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def hamming_distance_fraction(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of bits that differ between two binary response arrays."""
    bits_a = (a > 0).astype(int)
    bits_b = (b > 0).astype(int)
    return float(np.mean(bits_a != bits_b))


def get_puf_class():
    """Dynamically import VehiclePUF from the edge-vehicles module."""
    # When running from scripts/, go up one level to the project root
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, base)
    # Also add edge_vehicles directory if running from repo root
    ev_path = os.path.join(base, "edge-vehicles")
    if os.path.isdir(ev_path):
        sys.path.insert(0, ev_path)
    from src.security.puf_simulator import VehiclePUF
    return VehiclePUF


# ─────────────────────────────────────────────────────────────────────────────
# Graph 1: Uniqueness — Inter-Die Hamming Distance
# ─────────────────────────────────────────────────────────────────────────────

def compute_uniqueness(n_vehicles: int, n_challenges: int) -> list:
    """
    Instantiate n_vehicles PUFs (different seeds = different 'silicon').
    For each pair of vehicles, compute the average HD across n_challenges.
    Returns a flat list of all pairwise HD values.
    """
    VehiclePUF = get_puf_class()
    print(f"[Uniqueness] Instantiating {n_vehicles} simulated vehicles...")

    pufs = []
    for vid in range(n_vehicles):
        os.environ["VEHICLE_ID"] = str(vid)
        pufs.append(VehiclePUF())

    challenge_seeds = list(range(1000, 1000 + n_challenges))

    # Pre-compute responses for each vehicle
    print(f"[Uniqueness] Evaluating {n_challenges} challenges per vehicle...")
    responses = []  # shape: (n_vehicles, n_challenges) responses
    for puf in pufs:
        vehicle_responses = []
        for seed in challenge_seeds:
            _, r = puf.get_response(seed)
            vehicle_responses.append(r)
        responses.append(vehicle_responses)

    # Compute pairwise HD
    print("[Uniqueness] Computing pairwise Hamming Distances...")
    hd_values = []
    for i in range(n_vehicles):
        for j in range(i + 1, n_vehicles):
            pair_hds = []
            for k in range(n_challenges):
                hd = hamming_distance_fraction(responses[i][k], responses[j][k])
                pair_hds.append(hd)
            hd_values.append(np.mean(pair_hds))

    return hd_values


# ─────────────────────────────────────────────────────────────────────────────
# Graph 2: Reliability — Intra-Die Hamming Distance (with noise simulation)
# ─────────────────────────────────────────────────────────────────────────────

def compute_reliability(n_evaluations: int, n_challenges: int, noise_level: float) -> list:
    """
    Query a single vehicle PUF n_evaluations times with the same challenges,
    injecting Gaussian noise into the challenge bits to simulate temperature drift.
    Returns a list of average HD values vs. the noiseless golden reference.
    """
    VehiclePUF = get_puf_class()
    print(f"\n[Reliability] Using single vehicle PUF with {noise_level*100:.1f}% noise level...")

    os.environ["VEHICLE_ID"] = "42"
    puf = VehiclePUF()

    challenge_seeds = list(range(5000, 5000 + n_challenges))

    # Golden reference: noiseless responses
    golden_responses = []
    for seed in challenge_seeds:
        _, r = puf.get_response(seed)
        golden_responses.append(r)

    # Noisy evaluations: perturb the challenge seed slightly to simulate environmental drift
    print(f"[Reliability] Running {n_evaluations} noisy evaluations...")
    hd_values = []
    for _ in range(n_evaluations):
        round_hds = []
        for idx, seed in enumerate(challenge_seeds):
            # Simulate noise by adding small Gaussian perturbation to the seed
            noisy_seed = int(seed + np.random.normal(0, noise_level * seed))
            noisy_seed = max(1, abs(noisy_seed))  # Ensure positive
            _, noisy_r = puf.get_response(noisy_seed)
            hd = hamming_distance_fraction(golden_responses[idx], noisy_r)
            round_hds.append(hd)
        hd_values.append(np.mean(round_hds))

    return hd_values


# ─────────────────────────────────────────────────────────────────────────────
# Plotting
# ─────────────────────────────────────────────────────────────────────────────

def plot_metrics(uniqueness_hd: list, reliability_hd: list, output_path: str):
    """Render and save both graphs side by side with publication-quality styling."""

    fig = plt.figure(figsize=(14, 6), facecolor="#0f1117")
    gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)

    ACCENT = "#4f8ef7"
    ACCENT2 = "#f76b4f"
    TEXT_COLOR = "#e0e0e0"
    GRID_COLOR = "#2a2d3a"
    BG_COLOR = "#1a1d27"

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "text.color": TEXT_COLOR,
        "axes.labelcolor": TEXT_COLOR,
        "xtick.color": TEXT_COLOR,
        "ytick.color": TEXT_COLOR,
    })

    # ── Graph 1: Uniqueness ──────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0])
    ax1.set_facecolor(BG_COLOR)
    ax1.spines[:].set_color(GRID_COLOR)

    unique_pct = [hd * 100 for hd in uniqueness_hd]
    ax1.hist(unique_pct, bins=20, color=ACCENT, edgecolor="#0f1117", alpha=0.85, density=True)
    ax1.axvline(x=50, color="#f7c24f", linestyle="--", linewidth=1.5, label="Ideal (50%)")
    ax1.axvline(x=np.mean(unique_pct), color=ACCENT2, linestyle="-", linewidth=2,
                label=f"Mean = {np.mean(unique_pct):.1f}%")

    ax1.set_title("Uniqueness (Inter-Die HD)", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    ax1.set_xlabel("Hamming Distance (%)", color=TEXT_COLOR)
    ax1.set_ylabel("Probability Density", color=TEXT_COLOR)
    ax1.legend(facecolor=BG_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)
    ax1.grid(True, color=GRID_COLOR, alpha=0.5)
    ax1.set_xlim(0, 100)

    # Annotation
    ax1.annotate(
        f"σ = {np.std(unique_pct):.2f}%\nn = {len(uniqueness_hd)} pairs",
        xy=(0.02, 0.95), xycoords="axes fraction",
        fontsize=9, color=TEXT_COLOR, va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=GRID_COLOR, alpha=0.6)
    )

    # ── Graph 2: Reliability ─────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor(BG_COLOR)
    ax2.spines[:].set_color(GRID_COLOR)

    rel_pct = [hd * 100 for hd in reliability_hd]
    x = np.arange(1, len(rel_pct) + 1)
    ax2.plot(x, rel_pct, color=ACCENT2, linewidth=1.2, alpha=0.6, label="Per-round BER")
    ax2.axhline(y=np.mean(rel_pct), color=ACCENT, linestyle="--", linewidth=2,
                label=f"Mean BER = {np.mean(rel_pct):.2f}%")
    ax2.fill_between(x, rel_pct, alpha=0.15, color=ACCENT2)

    ax2.set_title("Reliability (Intra-Die HD)", color=TEXT_COLOR, fontsize=13, fontweight="bold", pad=12)
    ax2.set_xlabel("Evaluation Round", color=TEXT_COLOR)
    ax2.set_ylabel("Bit Error Rate (%)", color=TEXT_COLOR)
    ax2.legend(facecolor=BG_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=9)
    ax2.grid(True, color=GRID_COLOR, alpha=0.5)
    ax2.set_ylim(bottom=0)

    ax2.annotate(
        f"Max BER = {max(rel_pct):.2f}%\nMin BER = {min(rel_pct):.2f}%",
        xy=(0.02, 0.95), xycoords="axes fraction",
        fontsize=9, color=TEXT_COLOR, va="top",
        bbox=dict(boxstyle="round,pad=0.3", facecolor=GRID_COLOR, alpha=0.6)
    )

    # ── Main title ───────────────────────────────────────────────────────────
    fig.suptitle(
        "pypuf ArbiterPUF — Hardware Quality Metrics\n(Mathematical Delay Model Simulation)",
        color=TEXT_COLOR, fontsize=14, fontweight="bold", y=1.02
    )

    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"\n[Visualizer] ✓ Graph saved to: {output_path}")
    plt.close()


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PUF Hardware Metrics Visualizer")
    parser.add_argument("--vehicles", type=int, default=50,
                        help="Number of simulated vehicles for uniqueness test (default: 50)")
    parser.add_argument("--challenges", type=int, default=100,
                        help="Number of challenges per vehicle (default: 100)")
    parser.add_argument("--evaluations", type=int, default=100,
                        help="Number of noisy evaluations for reliability test (default: 100)")
    parser.add_argument("--noise", type=float, default=0.03,
                        help="Noise level as a fraction of the seed value (default: 0.03 = 3%%)")
    parser.add_argument("--output", type=str, default="puf_hardware_metrics.png",
                        help="Output image filename (default: puf_hardware_metrics.png)")
    args = parser.parse_args()

    print("=" * 60)
    print("  PUF Hardware Metrics Visualizer")
    print("=" * 60)
    print(f"  Vehicles        : {args.vehicles}")
    print(f"  Challenges/veh  : {args.challenges}")
    print(f"  Noise level     : {args.noise * 100:.1f}%")
    print(f"  Evaluations     : {args.evaluations}")
    print("=" * 60)

    uniqueness_hd = compute_uniqueness(args.vehicles, args.challenges)
    reliability_hd = compute_reliability(args.evaluations, args.challenges, args.noise)
    plot_metrics(uniqueness_hd, reliability_hd, args.output)

    print("\n[Summary]")
    print(f"  Uniqueness  — Mean HD : {np.mean([h*100 for h in uniqueness_hd]):.2f}%  (ideal: ~50%)")
    print(f"  Reliability — Mean BER: {np.mean([h*100 for h in reliability_hd]):.2f}%  (ideal: <5%)")


if __name__ == "__main__":
    main()
