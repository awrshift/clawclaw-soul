"""CVB v3 Visualization: Multi-Metric Time+Frequency Domain.

Shows proxy metrics (word_count, bullet_count, sentence_count) over time
and their FFT periodograms compared to engine input dimensions.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = Path(__file__).parent / "results"

# Dark theme
BG_COLOR = "#0f1729"
SURFACE_COLOR = "#1e293b"
TEXT_COLOR = "#e2e8f0"
GRID_COLOR = "#334155"

INPUT_COLOR = "#06b6d4"    # cyan — engine input
OUTPUT_COLOR = "#ec4899"   # pink — temporal output
STATIC_COLOR = "#6b7280"   # gray — static baseline
RANDOM_COLOR = "#f59e0b"   # amber — random control

METRIC_COLORS = {
    "word_count": "#ec4899",      # pink
    "hedge_density": "#a855f7",   # purple
    "bullet_count": "#22c55e",    # green
    "sentence_count": "#f59e0b",  # amber
}

STEP_HOURS = 12


def plot_cvb_v3(scored_file: Path | None = None, output_path: Path | None = None):
    """Generate multi-panel CVB v3 visualization."""
    if scored_file is None:
        scored_file = RESULTS_DIR / "cvb_v3_scored.json"
    if not scored_file.exists():
        print(f"No scored data at {scored_file}. Run cvb_runner.py first.")
        return

    results = json.loads(scored_file.read_text())

    # Separate conditions
    temporal = sorted([r for r in results if r["condition"] == "temporal"], key=lambda r: r["step"])
    static = sorted([r for r in results if r["condition"] == "static"], key=lambda r: r["step"])
    random_c = sorted([r for r in results if r["condition"] == "random"], key=lambda r: r["step"])

    days_t = np.array([r["step"] * STEP_HOURS / 24.0 for r in temporal])
    days_s = np.array([r["step"] * STEP_HOURS / 24.0 for r in static])
    days_r = np.array([r["step"] * STEP_HOURS / 24.0 for r in random_c])

    # Extract metrics
    def get_metric(data, metric):
        return np.array([r["metrics"][metric] for r in data])

    # Extract engine input dimensions
    empathy = np.array([r["dimensions"]["empathy"] for r in temporal])
    execution = np.array([r["dimensions"]["execution"] for r in temporal])
    authority = np.array([r["dimensions"]["authority"] for r in temporal])

    # ── Figure: 3 rows x 2 cols ──
    # Left column: time domain (metric + engine input)
    # Right column: FFT periodogram
    fig, axes = plt.subplots(3, 2, figsize=(18, 14), gridspec_kw={"hspace": 0.4, "wspace": 0.3})
    fig.patch.set_facecolor(BG_COLOR)

    metrics_config = [
        ("word_count", "Word Count", empathy, "Empathy (Moon)"),
        ("bullet_count", "Bullet Count", execution, "Execution (Mars)"),
        ("sentence_count", "Sentence Count", authority, "Authority (Sun)"),
    ]

    for row, (metric, label, input_dim, dim_label) in enumerate(metrics_config):
        ax_time = axes[row, 0]
        ax_freq = axes[row, 1]

        # Get metric values
        ts_temporal = get_metric(temporal, metric)
        ts_static = get_metric(static, metric)
        ts_random = get_metric(random_c, metric)

        # ─── Time Domain ───
        ax_time.set_facecolor(SURFACE_COLOR)

        # Normalize engine input to metric scale for overlay
        dim_norm = (input_dim - input_dim.min()) / max(input_dim.max() - input_dim.min(), 1e-10)
        metric_range = ts_temporal.max() - ts_temporal.min()
        dim_scaled = dim_norm * metric_range + ts_temporal.min()

        ax_time.plot(days_t, dim_scaled, color=INPUT_COLOR, linewidth=1.5, linestyle="--",
                     alpha=0.7, label=f"Engine: {dim_label}")
        ax_time.plot(days_t, ts_temporal, color=OUTPUT_COLOR, linewidth=2, alpha=0.9,
                     label=f"Temporal {label}")
        ax_time.plot(days_s, ts_static, color=STATIC_COLOR, linewidth=1, alpha=0.4,
                     label="Static")
        ax_time.fill_between(days_t, ts_temporal, alpha=0.1, color=OUTPUT_COLOR)

        ax_time.set_xlabel("Day", fontsize=10, color=TEXT_COLOR)
        ax_time.set_ylabel(label, fontsize=10, color=TEXT_COLOR)
        ax_time.set_title(f"{label} — Time Domain", fontsize=12, fontweight="bold",
                          color=TEXT_COLOR, pad=10)
        ax_time.legend(fontsize=8, loc="upper right", framealpha=0.8,
                       facecolor=SURFACE_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)
        ax_time.grid(True, alpha=0.2, linestyle="--", color=GRID_COLOR)
        ax_time.tick_params(colors=TEXT_COLOR)
        for spine in ax_time.spines.values():
            spine.set_color(GRID_COLOR)

        # ─── Frequency Domain (FFT) ───
        ax_freq.set_facecolor(SURFACE_COLOR)

        from scipy.fft import fft, fftfreq
        from scipy.signal import detrend

        def compute_fft_for_plot(signal):
            N = len(signal)
            if N < 8:
                return np.array([]), np.array([])
            d = detrend(signal, type="linear")
            w = np.hanning(N) * d
            yf = fft(w)
            xf = fftfreq(N, d=STEP_HOURS / 24.0)
            pos = xf > 0
            freqs = xf[pos]
            mags = 2.0 / N * np.abs(yf[pos])
            periods = 1.0 / freqs
            return periods, mags

        # Input FFT
        p_in, m_in = compute_fft_for_plot(input_dim)
        if len(m_in) > 0:
            m_in_norm = m_in / max(m_in.max(), 1e-10)
            mask = (p_in >= 2) & (p_in <= 60)
            ax_freq.plot(p_in[mask], m_in_norm[mask], color=INPUT_COLOR, linewidth=2,
                         alpha=0.7, label=f"Engine Input ({dim_label})")

        # Output FFT
        p_out, m_out = compute_fft_for_plot(ts_temporal)
        if len(m_out) > 0:
            m_out_norm = m_out / max(m_out.max(), 1e-10)
            mask = (p_out >= 2) & (p_out <= 60)
            ax_freq.plot(p_out[mask], m_out_norm[mask], color=OUTPUT_COLOR, linewidth=2,
                         alpha=0.9, label=f"LLM Output ({label})")
            ax_freq.fill_between(p_out[mask], 0, m_out_norm[mask], color=OUTPUT_COLOR, alpha=0.1)

        # Static FFT (control)
        p_st, m_st = compute_fft_for_plot(ts_static)
        if len(m_st) > 0:
            m_st_norm = m_st / max(m_st.max(), 1e-10)
            mask = (p_st >= 2) & (p_st <= 60)
            ax_freq.plot(p_st[mask], m_st_norm[mask], color=STATIC_COLOR, linewidth=1,
                         alpha=0.4, label="Static (control)")

        ax_freq.set_xlabel("Period (days)", fontsize=10, color=TEXT_COLOR)
        ax_freq.set_ylabel("Normalized Magnitude", fontsize=10, color=TEXT_COLOR)
        ax_freq.set_title(f"{label} — FFT Periodogram", fontsize=12, fontweight="bold",
                          color=TEXT_COLOR, pad=10)
        ax_freq.legend(fontsize=8, loc="upper right", framealpha=0.8,
                       facecolor=SURFACE_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR)
        ax_freq.grid(True, alpha=0.2, linestyle="--", color=GRID_COLOR)
        ax_freq.tick_params(colors=TEXT_COLOR)
        for spine in ax_freq.spines.values():
            spine.set_color(GRID_COLOR)

    # Suptitle
    fig.suptitle(
        "Celestial Variance Benchmark v3 — Structural Constraints + Proxy Metrics",
        fontsize=16, fontweight="bold", color=TEXT_COLOR, y=0.98,
    )

    fig.tight_layout(rect=[0, 0, 1, 0.96])

    if output_path is None:
        output_path = RESULTS_DIR / "plots" / "cvb_v3_multi_panel.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=BG_COLOR, edgecolor="none")
    print(f"CVB v3 plot saved: {output_path}")
    return fig


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CVB v3 Visualization")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    out_path = Path(args.output) if args.output else None
    plot_cvb_v3(output_path=out_path)


if __name__ == "__main__":
    main()
