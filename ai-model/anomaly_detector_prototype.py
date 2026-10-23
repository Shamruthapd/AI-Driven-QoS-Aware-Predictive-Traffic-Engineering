
import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="datasets/processed/qos_features.csv"
    )
    parser.add_argument(
        "--output",
        default="datasets/processed/week5_anomaly_results.csv"
    )
    parser.add_argument("--feature", default="throughput_bps")
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--k", type=float, default=3.0)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    required = {
        "timestamp", "dpid", "port",
        args.feature, "is_anomalous"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )
    df[args.feature] = pd.to_numeric(
        df[args.feature], errors="coerce"
    )
    df["is_anomalous"] = pd.to_numeric(
        df["is_anomalous"], errors="coerce"
    )

    df = df.dropna(
        subset=["timestamp", "dpid", "port", args.feature,
                "is_anomalous"]
    ).copy()

    df = df.sort_values(
        ["dpid", "port", "timestamp"]
    ).reset_index(drop=True)

    # Week 5 placeholder: predict using previous readings only.
    groups = df.groupby(["dpid", "port"], sort=False)[args.feature]
    df["predicted_placeholder"] = groups.transform(
        lambda s: s.shift(1).rolling(
            window=args.window,
            min_periods=args.window
        ).mean()
    )

    df["residual"] = (
        df[args.feature] - df["predicted_placeholder"]
    )

    # Estimate threshold from normal samples only.
    normal = df.loc[
        (df["is_anomalous"] == 0)
        & df["residual"].notna(),
        "residual"
    ]

    if len(normal) < 2:
        raise ValueError(
            "Not enough normal residuals to calibrate threshold."
        )

    residual_mean = normal.mean()
    residual_std = normal.std(ddof=1)

    if not np.isfinite(residual_std) or residual_std == 0:
        raise ValueError(
            "Normal residual standard deviation is zero or invalid."
        )

    df["anomaly_score"] = (
        df["residual"] - residual_mean
    ).abs()

    df["predicted_anomalous"] = (
        df["anomaly_score"] > args.k * residual_std
    ).astype(int)

    # Evaluate only rows where a prediction was possible.
    evaluated = df.dropna(subset=["residual"]).copy()
    actual = evaluated["is_anomalous"].astype(int)
    predicted = evaluated["predicted_anomalous"]

    tp = int(((actual == 1) & (predicted == 1)).sum())
    fn = int(((actual == 1) & (predicted == 0)).sum())
    fp = int(((actual == 0) & (predicted == 1)).sum())
    tn = int(((actual == 0) & (predicted == 0)).sum())

    recall = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print("\nWEEK 5 ANOMALY DETECTOR RESULTS")
    print("--------------------------------")
    print("Input rows:", len(pd.read_csv(args.input)))
    print("Rows after cleaning:", len(df))
    print("Rows evaluated:", len(evaluated))
    print("Normal residual mean:", residual_mean)
    print("Normal residual standard deviation:", residual_std)
    print("Threshold k:", args.k)
    print("Threshold distance:", args.k * residual_std)
    print("TP:", tp, "FN:", fn, "FP:", fp, "TN:", tn)
    print(f"Recall: {recall:.4f}")
    print(f"False-positive rate: {fpr:.4f}")
    print("Results saved to:", output)


if __name__ == "__main__":
    main()
