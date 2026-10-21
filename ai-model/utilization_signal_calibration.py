"""
Week 7 - Utilization Signal Calibration

Converts predicted throughput (bps) into a normalized
0-100% link-utilization signal.

The calibration uses the configured link capacity as the
engineering reference and clips the resulting utilization
to the valid 0-100% range.
"""

import numpy as np
import pandas as pd


# ============================================================
# Configuration
# ============================================================

# Configured Mininet/Open vSwitch link capacity.
LINK_CAPACITY_BPS = 10_000_000

# Input/output files.
INPUT_FILE = "data/results/week7_predicted_throughput.csv"
OUTPUT_FILE = "data/results/week7_calibrated_utilization.csv"


# ============================================================
# Calibration Function
# ============================================================

def calibrate_utilization(predicted_throughput_bps, link_capacity_bps):
    """
    Convert predicted throughput into link utilization percentage.

    Formula:
        utilization (%) =
            predicted throughput / link capacity * 100

    The result is clipped to 0-100%.
    """

    if link_capacity_bps <= 0:
        raise ValueError("Link capacity must be greater than zero.")

    utilization = (
        np.asarray(predicted_throughput_bps, dtype=float)
        / link_capacity_bps
        * 100.0
    )

    return np.clip(utilization, 0.0, 100.0)


# ============================================================
# Main
# ============================================================

def main():

    print("=" * 70)
    print("WEEK 7 - UTILIZATION SIGNAL CALIBRATION")
    print("=" * 70)

    # Check that the prediction input exists.
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"\nInput file not found: {INPUT_FILE}")
        print("Calibration function is ready, but prediction data is required.")
        return

    if "predicted_throughput_bps" not in df.columns:
        raise ValueError(
            "Input CSV must contain 'predicted_throughput_bps'."
        )

    # Generate calibrated 0-100% utilization signal.
    df["predicted_utilization_pct"] = calibrate_utilization(
        df["predicted_throughput_bps"],
        LINK_CAPACITY_BPS
    )

    # Store whether clipping occurred.
    df["utilization_clipped"] = (
        (df["predicted_throughput_bps"] < 0)
        | (df["predicted_throughput_bps"] > LINK_CAPACITY_BPS)
    )

    # Save calibrated signal.
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nLink capacity: {LINK_CAPACITY_BPS:,} bps")
    print(
        f"Utilization range: "
        f"{df['predicted_utilization_pct'].min():.2f}% - "
        f"{df['predicted_utilization_pct'].max():.2f}%"
    )
    print(f"\nCalibrated signal saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()