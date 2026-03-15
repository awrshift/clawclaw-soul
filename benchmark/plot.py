"""CVB v2 Visualization: Dual-Pane (Time Domain + Frequency Domain).

Top pane: Engine input modifier (cyan dotted) vs LLM embedding score (pink solid)
Bottom pane: FFT of input vs FFT of output (overlaid, peak alignment)

Design: brainstorm 002 — "one image tells the whole story."
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = Path(__file__).parent / "results"

# Dark theme colors
BG_COLOR = "#0f1729"
SURFACE_COLOR = "#1e293b"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#334155"

INPUT_COLOR = "#06b6d4"    # cyan — engine input
OUTPUT_COLOR = "#ec4899"   # pink — LLM output
STATIC_COLOR = "#6b7280"   # gray — static baseline
RANDOM_COLOR = "#f59e0b"   # amber — random control

ORBITAL_PERIODS = {
    "Lunar": 29.53,
    "Mercury": 87.97,
}


def plot_cvb_v2(analysis: dict, output_path: Path | None = None):
    """Generate the CVB v2 dual-pane visualization."""
    temporal = analysis.get("temporal", {})
    if not temporal:
        print("No temporal data found in analysis.")
        return

    steps = np.array(temporal["steps"])
    scores = np.array(temporal["scores"])
    modifiers = np.array(temporal.get("modifiers", []))

    # Convert steps to days
    step_hours = 12
    days = steps * step_hours / 24.0

    fig, (ax_time, ax_freq) = plt.subplots(
        2, 1, figsize=(16, 10), height_ratios=[1.2, 1],
        gridspec_kw={"hspace": 0.35},
    )
    fig.patch.set_facecolor(BG_COLOR)

    # ─── Top Pane: Time Domain ───
    ax_time.set_facecolor(SURFACE_COLOR)

    # Normalize both series to [0, 1] for visual comparison
    def normalize(arr):
        mn, mx = arr.min(), arr.max()
        if mx - mn < 1e-10:
            return np.zeros_like(arr)
        return (arr - mn) / (mx - mn)

    if len(modifiers) > 0:
        mod_norm = normalize(modifiers)
        ax_time.plot(
            days, mod_norm,
            color=INPUT_COLOR, linewidth=1.5, linestyle="--", alpha=0.7,
            label="Engine Input (agreeableness modifier)",
        )

    score_norm = normalize(scores)
    # Smooth with rolling mean (window=5 steps)
    window = 5
    if len(score_norm) >= window:
        kernel = np.ones(window) / window
        smoothed = np.convolve(score_norm, kernel, mode="same")
    else:
        smoothed = score_norm

    ax_time.plot(
        days, smoothed,
        color=OUTPUT_COLOR, linewidth=2.5, alpha=0.9,
        label="LLM Output (embedding score)",
    )
    ax_time.fill_between(days, smoothed, alpha=0.1, color=OUTPUT_COLOR)

    # Also plot static and random if available
    for cond, color, label in [
        ("static", STATIC_COLOR, "Static (no prompt)"),
        ("random", RANDOM_COLOR, "Random (daily random)"),
    ]:
        cond_data = analysis.get(cond, {})
        if "scores" in cond_data:
            cond_scores = normalize(np.array(cond_data["scores"]))
            cond_days = np.array(cond_data["steps"]) * step_hours / 24.0
            if len(cond_scores) >= window:
                cond_smooth = np.convolve(cond_scores, kernel, mode="same")
            else:
                cond_smooth = cond_scores
            ax_time.plot(
                cond_days, cond_smooth,
                color=color, linewidth=1.2, alpha=0.5, label=label,
            )

    ax_time.set_xlabel("Day", fontsize=12, color=TEXT_COLOR)
    ax_time.set_ylabel("Normalized Score", fontsize=12, color=TEXT_COLOR)
    ax_time.set_title(
        f"Celestial Variance Benchmark — Time Domain ({int(days[-1]+1)} days)",
        fontsize=15, fontweight="bold", color=TEXT_COLOR, pad=15,
    )
    ax_time.legend(fontsize=9, loc="upper right", framealpha=0.8,
                   facecolor=SURFACE_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)
    ax_time.grid(True, alpha=0.2, linestyle="--", color=GRID_COLOR)
    ax_time.tick_params(colors=TEXT_COLOR)
    for spine in ax_time.spines.values():
        spine.set_color(GRID_COLOR)

    # ─── Bottom Pane: Frequency Domain (FFT overlay) ───
    ax_freq.set_facecolor(SURFACE_COLOR)

    input_fft = temporal.get("input_fft", {})
    output_fft = temporal.get("output_fft", {})

    max_period = float(days[-1]) if len(days) > 0 else 90.0

    def plot_fft(ax, fft_data, color, label, fill=True):
        if not fft_data or "periods" not in fft_data:
            return
        periods = np.array(fft_data["periods"])
        magnitudes = np.array(fft_data["magnitudes"])

        # Normalize magnitudes for comparison
        mag_max = magnitudes.max()
        if mag_max > 0:
            magnitudes = magnitudes / mag_max

        # Filter to meaningful range
        mask = (periods >= 2) & (periods <= max_period * 0.9)
        p = periods[mask]
        m = magnitudes[mask]

        ax.plot(p, m, color=color, linewidth=2, alpha=0.9, label=label)
        if fill:
            ax.fill_between(p, 0, m, color=color, alpha=0.1)

    plot_fft(ax_freq, input_fft, INPUT_COLOR, "Engine Input FFT", fill=False)
    plot_fft(ax_freq, output_fft, OUTPUT_COLOR, "LLM Output FFT", fill=True)

    # Annotate orbital periods
    for name, period in ORBITAL_PERIODS.items():
        if 2 <= period <= max_period * 0.9:
            ax_freq.axvline(period, color="#ef4444", linestyle=":", alpha=0.5, linewidth=1)
            ax_freq.annotate(
                f"{name} ({period:.1f}d)",
                xy=(period, 0.95), fontsize=8, color="#ef4444",
                ha="center", va="top",
            )

    # Annotate peak alignment
    peak_aligned = temporal.get("peak_aligned", False)
    if output_fft:
        out_peak = output_fft.get("peak_period_days", 0)
        out_snr = output_fft.get("snr", 0)
        verdict_text = "ALIGNED" if peak_aligned else "MISALIGNED"
        verdict_color = "#22c55e" if peak_aligned else "#ef4444"
        ax_freq.annotate(
            f"Output Peak: {out_peak:.1f}d (SNR {out_snr:.1f}x) — {verdict_text}",
            xy=(0.02, 0.92), xycoords="axes fraction",
            fontsize=11, fontweight="bold", color=verdict_color,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=BG_COLOR, edgecolor=verdict_color, alpha=0.8),
        )

    ax_freq.set_xlabel("Period (days)", fontsize=12, color=TEXT_COLOR)
    ax_freq.set_ylabel("Normalized Magnitude", fontsize=12, color=TEXT_COLOR)

    title_suffix = "Peaks Aligned" if peak_aligned else "Peaks Misaligned"
    ax_freq.set_title(
        f"FFT Periodogram — Engine vs LLM ({title_suffix})",
        fontsize=15, fontweight="bold", color=TEXT_COLOR, pad=15,
    )
    ax_freq.legend(fontsize=9, loc="upper right", framealpha=0.8,
                   facecolor=SURFACE_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)
    ax_freq.grid(True, alpha=0.2, linestyle="--", color=GRID_COLOR)
    ax_freq.tick_params(colors=TEXT_COLOR)
    for spine in ax_freq.spines.values():
        spine.set_color(GRID_COLOR)

    fig.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight",
                    facecolor=BG_COLOR, edgecolor="none")
        print(f"CVB v2 plot saved: {output_path}")

    return fig


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CVB v2 Visualization")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    analysis_path = RESULTS_DIR / "cvb_v2_analysis_full.json"
    if not analysis_path.exists():
        print(f"No analysis found at {analysis_path}. Run cvb_runner.py first.")
        return

    analysis = json.loads(analysis_path.read_text())

    out_path = Path(args.output) if args.output else RESULTS_DIR / "plots" / "cvb_v2_dual_pane.png"
    plot_cvb_v2(analysis, out_path)


if __name__ == "__main__":
    main()
