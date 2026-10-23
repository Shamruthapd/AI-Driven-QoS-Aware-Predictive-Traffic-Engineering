# Week 8: QoS Policy Engine Design

## Objective

Connect congestion predictions and anomaly signals to explicit QoS policy
decisions. The first implementation runs in dry-run mode and logs intended
actions without changing the network.

## Queue Mapping

| Traffic class | Queue ID | Configured rate policy |
|---|---:|---|
| Bulk TCP data | 0 | Maximum 4 Mbps |
| Priority video/IoT UDP | 1 | Minimum 8 Mbps, maximum 10 Mbps |

These are the intended queue settings documented in
`docs/week7/queue-id-reference.md`. The running switch configuration must
be verified before live enforcement.

## Trigger Rules

| Signal | Condition | Policy decision |
|---|---|---|
| Predicted port throughput | Greater than 10 Mbps for 2 consecutive valid readings | Enter congestion policy |
| Predicted port throughput | At or below 10 Mbps | Clear consecutive-high counter |
| Anomaly detector | `predicted_anomaly == 1` | Record anomaly signal; do not infer congestion from anomaly alone |
| Missing or invalid prediction | Required value unavailable or non-numeric | Log and skip action |
| Stale prediction | Timestamp exceeds configured freshness limit | Log and skip action |
| Simultaneous congestion signals | More than one signal triggers | Log all signals and select one deterministic policy decision |

## Congestion Action

When congestion is confirmed, the intended policy is to preserve priority
traffic in Queue 1 and constrain bulk traffic in Queue 0. Actual enforcement
must use the verified controller interface and matching flow rules.

## Stability and Safety

- Require two consecutive over-threshold readings before triggering.
- Do not act on missing, invalid, or stale readings.
- Log the input signal, threshold, decision, and intended action.
- Do not send live OpenFlow or shell commands in dry-run mode.
- Avoid repeatedly issuing the same action on every polling interval.

## Known Integration Dependencies

- Confirm Member 1's controller enforcement interface.
- Confirm Member 4's prediction file/feed format and update cadence.
- Confirm the correct switch, egress port, and traffic match for each queue.
- Verify Queue 0 and Queue 1 exist and have the intended rate settings.

## Validation Scope

The available Week 6 anomaly results and traffic telemetry can test decision
logic. They do not by themselves validate live predictive QoS enforcement.
