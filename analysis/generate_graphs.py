# #!/usr/bin/env python3
# """
# generate_graphs.py
# ===================

# Generates all figures for the two-way iperf3 network measurement study
# between EC2 instances in us-east-1 (Virginia) and us-west-2 (Oregon).

# Inputs (relative to project root):
#     data/network_metrics.csv            -> us-east-1 -> us-west-2 (forward)
#     data/network_metrics_reverse.csv    -> us-west-2 -> us-east-1 (reverse)

# Outputs (relative to project root), all under figures/:
#     <direction>_latency.png
#     <direction>_throughput.png
#     <direction>_jitter.png
#     <direction>_retransmissions.png
#         for direction in {us_east_1_to_us_west_2, us_west_2_to_us_east_1}

#     latency_direction_comparison.png
#     throughput_direction_comparison.png
#     jitter_direction_comparison.png
#     retransmissions_direction_comparison.png

# Run from anywhere; paths are resolved relative to this file's location:
#     python3 analysis/generate_graphs.py
# or
#     cd analysis && python3 generate_graphs.py
# """

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless / no display needed
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------------------------------------------------------------------------
# Path setup (robust to being run from project root or from analysis/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "figures")

FORWARD_CSV = os.path.join(DATA_DIR, "network_metrics.csv")           # us-east-1 -> us-west-2
REVERSE_CSV = os.path.join(DATA_DIR, "network_metrics_reverse.csv")   # us-west-2 -> us-east-1

os.makedirs(FIGURES_DIR, exist_ok=True)

plt.rcParams.update({
    "figure.figsize": (11, 5),
    "figure.dpi": 120,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "font.size": 10,
})

FORWARD_COLOR = "#1f77b4"   # blue
REVERSE_COLOR = "#d62728"   # red


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_direction(csv_path):
    if not os.path.isfile(csv_path):
        sys.exit(f"ERROR: expected input file not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"]).sort_values("timestamp")

    src = df["source_region"].iloc[0]
    dst = df["destination_region"].iloc[0]
    direction_label = f"{src} -> {dst}"
    direction_slug = f"{src}_to_{dst}".replace("-", "_")   # us_east_1_to_us_west_2

    return df, direction_slug, direction_label


# ---------------------------------------------------------------------------
# Per-direction time series figures
# ---------------------------------------------------------------------------
def plot_timeseries(df, direction_slug, direction_label, color):
    """Create latency, throughput, jitter, and retransmissions time-series plots."""

    def _save(fig, name):
        path = os.path.join(FIGURES_DIR, f"{direction_slug}_{name}.png")
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        print(f"Wrote {path}")

    x = df["timestamp"]

    # --- Latency (avg with min/max band) ---
    fig, ax = plt.subplots()
    ax.fill_between(x, df["min_latency_ms"], df["max_latency_ms"],
                     color=color, alpha=0.15, label="Min-Max range")
    ax.plot(x, df["avg_latency_ms"], color=color, linewidth=1.3, label="Average latency")
    ax.set_title(f"Latency over Time: {direction_label}")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Latency (ms)")
    ax.legend(loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    _save(fig, "latency")

    # --- Throughput ---
    fig, ax = plt.subplots()
    ax.plot(x, df["throughput_mbps"], color=color, linewidth=1.3)
    ax.set_title(f"Throughput over Time: {direction_label}")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Throughput (Mbps)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    _save(fig, "throughput")

    # --- Jitter ---
    fig, ax = plt.subplots()
    ax.plot(x, df["jitter_ms"], color=color, linewidth=1.3)
    ax.set_title(f"Jitter over Time: {direction_label}")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Jitter (ms)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    _save(fig, "jitter")

    # --- Retransmissions ---
    fig, ax = plt.subplots()
    ax.plot(x, df["retransmissions"], color=color, linewidth=1.0, marker="o", markersize=2)
    ax.set_title(f"TCP Retransmissions over Time: {direction_label}")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Retransmissions (count)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    fig.autofmt_xdate()
    _save(fig, "retransmissions")


# ---------------------------------------------------------------------------
# Direction comparison figures (box plot + mean bar, side by side)
# ---------------------------------------------------------------------------
def plot_comparison(df_fwd, label_fwd, df_rev, label_rev, column, ylabel, title, filename):
    fig, (ax_box, ax_bar) = plt.subplots(1, 2, figsize=(11, 5))

    data = [df_fwd[column].dropna(), df_rev[column].dropna()]
    labels = [label_fwd, label_rev]

    bp = ax_box.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=False)
    for patch, color in zip(bp["boxes"], [FORWARD_COLOR, REVERSE_COLOR]):
        patch.set_facecolor(color)
        patch.set_alpha(0.5)
    ax_box.set_ylabel(ylabel)
    ax_box.set_title("Distribution")
    ax_box.tick_params(axis="x", rotation=15)

    means = [d.mean() for d in data]
    stds = [d.std() for d in data]
    ax_bar.bar(labels, means, yerr=stds, capsize=6,
               color=[FORWARD_COLOR, REVERSE_COLOR], alpha=0.75)
    ax_bar.set_ylabel(ylabel)
    ax_bar.set_title("Mean (+/- 1 std dev)")
    ax_bar.tick_params(axis="x", rotation=15)

    fig.suptitle(title)
    fig.tight_layout()
    path = os.path.join(FIGURES_DIR, filename)
    fig.savefig(path)
    plt.close(fig)
    print(f"Wrote {path}")


def main():
    print("Loading data...")
    df_fwd, slug_fwd, label_fwd = load_direction(FORWARD_CSV)
    df_rev, slug_rev, label_rev = load_direction(REVERSE_CSV)

    print(f"  Forward direction : {label_fwd}  ({len(df_fwd)} rows)")
    print(f"  Reverse direction : {label_rev}  ({len(df_rev)} rows)")

    print("\nGenerating per-direction time series figures...")
    plot_timeseries(df_fwd, slug_fwd, label_fwd, FORWARD_COLOR)
    plot_timeseries(df_rev, slug_rev, label_rev, REVERSE_COLOR)

    print("\nGenerating direction comparison figures...")
    plot_comparison(df_fwd, label_fwd, df_rev, label_rev,
                     column="avg_latency_ms", ylabel="Latency (ms)",
                     title="Latency: Forward vs Reverse Direction",
                     filename="latency_direction_comparison.png")

    plot_comparison(df_fwd, label_fwd, df_rev, label_rev,
                     column="throughput_mbps", ylabel="Throughput (Mbps)",
                     title="Throughput: Forward vs Reverse Direction",
                     filename="throughput_direction_comparison.png")

    plot_comparison(df_fwd, label_fwd, df_rev, label_rev,
                     column="jitter_ms", ylabel="Jitter (ms)",
                     title="Jitter: Forward vs Reverse Direction",
                     filename="jitter_direction_comparison.png")

    plot_comparison(df_fwd, label_fwd, df_rev, label_rev,
                     column="retransmissions", ylabel="Retransmissions (count)",
                     title="Retransmissions: Forward vs Reverse Direction",
                     filename="retransmissions_direction_comparison.png")

    print("\nDone.")


if __name__ == "__main__":
    main()

