# Week 7 — Calibrated Utilization Signal Specification

## 1. Purpose

The LSTM model produces a predicted `throughput_bps` value.

Member 3 requires a normalized utilization signal rather than the raw model output.

This specification defines how the raw predicted throughput is converted into a
link-utilization percentage from **0% to 100%**.

---

## 2. Input Signal

**Input field:**

`predicted_throughput_bps`

Unit:

**bits per second (bps)**

The value is obtained from the trained LSTM prediction after inverse-transforming
the model output using the training scaler.

---

## 3. Link Capacity Reference

The current Mininet/Open vSwitch configuration uses:

`10,000,000 bps` = **10 Mbps**

Therefore:

```text
LINK_CAPACITY_BPS = 10,000,000