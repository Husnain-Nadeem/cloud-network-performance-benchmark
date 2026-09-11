# #!/usr/bin/env python3
# """
# analyze.py
# ==========

# Computes descriptive statistics and directional comparison statistics for the
# two-way iperf3 network measurement study between an EC2 instance in
# us-east-1 (Virginia) and an EC2 instance in us-west-2 (Oregon).

# Inputs (relative to project root):
#     data/network_metrics.csv            -> iperf3 client run on us-east-1 (Virginia),
#                                              sending to us-west-2 (Oregon)
#     data/network_metrics_reverse.csv    -> iperf3 client run on us-west-2 (Oregon),
#                                              sending to us-east-1 (Virginia)

# Outputs (relative to project root):
#     results/summary_statistics.csv      -> per-direction descriptive stats for every metric
#     results/comparison_results.csv      -> east->west vs west->east comparison per metric
#                                              (mean/median deltas, % difference, Welch's t-test,
#                                              Mann-Whitney U test)

# Run from anywhere; paths are resolved relative to this file's location, so:
#     python3 analysis/analyze.py
# or
#     cd analysis && python3 analyze.py
# both work.
# """

import os
import sys
import pandas as pd
import numpy as np
from scipy import stats

# ---------------------------------------------------------------------------
# Path setup (robust to being run from project root or from analysis/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

FORWARD_CSV = os.path.join(DATA_DIR, "network_metrics.csv")           # us-east-1 -> us-west-2
REVERSE_CSV = os.path.join(DATA_DIR, "network_metrics_reverse.csv")   # us-west-2 -> us-east-1

os.makedirs(RESULTS_DIR, exist_ok=True)

# Metrics we report on, and how each should be labeled in output
METRICS = {
    "avg_latency_ms": "Average Latency (ms)",
    "min_latency_ms": "Minimum Latency (ms)",
    "max_latency_ms": "Maximum Latency (ms)",
    "jitter_ms": "Jitter (ms)",
    "packet_loss_percent": "Packet Loss (%)",
    "throughput_mbps": "Throughput (Mbps)",
    "retransmissions": "Retransmissions (count)",
}


def load_direction(csv_path):
    """Load a metrics CSV and derive a human-readable direction label."""
    if not os.path.isfile(csv_path):
        sys.exit(f"ERROR: expected input file not found: {csv_path}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])

    src = df["source_region"].iloc[0]
    dst = df["destination_region"].iloc[0]
    direction_label = f"{src}_to_{dst}"       # e.g. us-east-1_to_us-west-2
    direction_slug = direction_label.replace("-", "_")  # us_east_1_to_us_west_2

    df["direction"] = direction_label
    return df, direction_slug, direction_label


def summarize(df, direction_label):
    """Build descriptive statistics rows for one direction, one row per metric."""
    rows = []
    for col, pretty_name in METRICS.items():
        series = df[col].dropna()
        rows.append({
            "direction": direction_label,
            "metric": col,
            "metric_label": pretty_name,
            "count": int(series.count()),
            "mean": series.mean(),
            "std": series.std(),
            "min": series.min(),
            "p25": series.quantile(0.25),
            "median": series.median(),
            "p75": series.quantile(0.75),
            "p95": series.quantile(0.95),
            "p99": series.quantile(0.99),
            "max": series.max(),
        })
    return rows


def compare(df_a, label_a, df_b, label_b):
    """
    Compare each metric between two directions.

    Uses Welch's t-test (does not assume equal variance) for means, and the
    Mann-Whitney U test as a non-parametric check that doesn't assume
    normally distributed samples (network measurements are often skewed).
    """
    rows = []
    for col, pretty_name in METRICS.items():
        a = df_a[col].dropna().to_numpy()
        b = df_b[col].dropna().to_numpy()

        mean_a, mean_b = a.mean(), b.mean()
        median_a, median_b = np.median(a), np.median(b)

        mean_diff = mean_a - mean_b
        pct_diff = (mean_diff / mean_b * 100) if mean_b != 0 else np.nan

        # Welch's t-test (unequal variance)
        t_stat, t_pvalue = stats.ttest_ind(a, b, equal_var=False)

        # Mann-Whitney U test (non-parametric)
        try:
            u_stat, u_pvalue = stats.mannwhitneyu(a, b, alternative="two-sided")
        except ValueError:
            u_stat, u_pvalue = np.nan, np.nan

        rows.append({
            "metric": col,
            "metric_label": pretty_name,
            f"mean_{label_a}": mean_a,
            f"mean_{label_b}": mean_b,
            "mean_difference": mean_diff,
            "pct_difference_vs_b": pct_diff,
            f"median_{label_a}": median_a,
            f"median_{label_b}": median_b,
            "welch_t_stat": t_stat,
            "welch_p_value": t_pvalue,
            "mannwhitney_u_stat": u_stat,
            "mannwhitney_p_value": u_pvalue,
            "significant_at_0.05": bool(t_pvalue < 0.05),
        })
    return rows


def main():
    print("Loading data...")
    df_fwd, slug_fwd, label_fwd = load_direction(FORWARD_CSV)
    df_rev, slug_rev, label_rev = load_direction(REVERSE_CSV)

    print(f"  Forward direction : {label_fwd}  ({len(df_fwd)} rows)  <- {FORWARD_CSV}")
    print(f"  Reverse direction : {label_rev}  ({len(df_rev)} rows)  <- {REVERSE_CSV}")

    # ---------------- Summary statistics ----------------
    summary_rows = summarize(df_fwd, label_fwd) + summarize(df_rev, label_rev)
    summary_df = pd.DataFrame(summary_rows)
    summary_path = os.path.join(RESULTS_DIR, "summary_statistics.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"Wrote {summary_path}  ({len(summary_df)} rows)")

    # ---------------- Directional comparison ----------------
    comparison_rows = compare(df_fwd, label_fwd, df_rev, label_rev)
    comparison_df = pd.DataFrame(comparison_rows)
    comparison_path = os.path.join(RESULTS_DIR, "comparison_results.csv")
    comparison_df.to_csv(comparison_path, index=False)
    print(f"Wrote {comparison_path}  ({len(comparison_df)} rows)")

    print("\nDone.")


if __name__ == "__main__":
    main()