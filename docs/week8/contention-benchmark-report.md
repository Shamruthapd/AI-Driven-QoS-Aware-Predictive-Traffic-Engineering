# Week 8 Contention Benchmark & Telemetry Handshake Report

## Summary of Results
- **QoS OFF State**:
  - Bulk TCP Flow: ~12.02 Mbps
  - Priority UDP Flow: 8.00 Mbps (Jitter: 0.041 ms, Loss: 0.0%)
  - Total Bandwidth Consumed: ~20.02 Mbps (Link unconstrained)

- **QoS ON State**:
  - Bulk TCP Flow: Restricted to 3.76 Mbps (Successfully throttled by Queue 0 HTB max 4Mbps)
  - Priority UDP Flow: Bottlenecked at 3.95 Mbps (Assigned to Queue 0 default path; needs Queue 1 binding in Member 1 controller logic)

## Next Action Items
1. **Member 1 (Controller Logic)**: Ensure OpenFlow flow entries explicitly set `actions=set_queue:1` for destination UDP port 5202 / host `10.0.0.3`.
2. **Member 4 (Data Pipeline)**: Export `data/results/week8_qos_on_vs_off_measurements.csv` into the evaluation notebook.
