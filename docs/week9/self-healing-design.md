# Week 9: Self-Healing Design

## 1. Objective

Design a two-layer recovery system for the AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing project.

- Layer 1 — OpenFlow Fast-Failover (FF): the switch detects a watched-port failure and selects a live backup bucket locally, without waiting for the controller to install a replacement flow.
- Layer 2 — AI-based recovery: the AI/policy layer detects sustained congestion or degradation and may request proactive rerouting of best-effort traffic. Priority traffic should retain its protection.

Fast-Failover handles port/link failure; it does not independently detect congestion.

## 2. Topology

The Mininet topology contains three switches and four hosts:

- s1: h1 (10.0.0.1), h2 (10.0.0.2)
- s2: h3 (10.0.0.3), h4 (10.0.0.4)
- s3: intermediate backbone switch
- Primary inter-switch path: s1–s3–s2
- Redundant direct link: s1–s2

The topology creates host links first, then s1–s3, s2–s3, and finally s1–s2.

## 3. Provisional Port Map

Based on the link-creation order in mininet/topo.py, the expected ports are:

| Switch | Port | Connected device | Intended role |
|---|---:|---|---|
| s1 | 1 | h1 | Host access |
| s1 | 2 | h2 | Host access |
| s1 | 3 | s3 | Primary backbone |
| s1 | 4 | s2 | Redundant direct link |
| s2 | 1 | h3 | Host access |
| s2 | 2 | h4 | Host access |
| s2 | 3 | s3 | Primary backbone |
| s2 | 4 | s1 | Redundant direct link |
| s3 | 1 | s1 | Backbone |
| s3 | 2 | s2 | Backbone |

These assignments are inferred from topology construction, not yet verified from a running Mininet instance. Confirm them using switch port descriptions before installing groups. Coordinate with Member 2 and use the team's agreed port map as authoritative.

## 4. Fast-Failover Design

For traffic crossing between the edge switches, the proposed group buckets are:

### Switch s1

1. Primary bucket: watch port 3; apply the appropriate queue action and output to port 3 (s3).
2. Backup bucket: watch port 4; apply the same traffic-class queue action and output to port 4 (s2).

### Switch s2

1. Primary bucket: watch port 3; apply the appropriate queue action and output to port 3 (s3).
2. Backup bucket: watch port 4; apply the same traffic-class queue action and output to port 4 (s1).

The group IDs, exact queue IDs, flow matches, and priorities must be agreed with Member 1 and Member 2 before implementation. Every bucket must preserve the relevant QoS queue treatment.

## 5. Recovery and Failback

- When a watched primary port goes down, the switch should select a live backup bucket locally.
- When the primary port returns, Fast-Failover may return traffic to the first eligible bucket.
- Confirm actual behaviour using group statistics and end-to-end traffic; do not infer success from configuration alone.
- If no bucket is live, record the outage and allow recovery when connectivity returns.
- Avoid adding controller-driven reroutes that conflict with a switch's active Fast-Failover path.

## 6. Failure Scenarios

| Scenario | Expected behaviour | Evidence required |
|---|---|---|
| Single primary-link failure | Traffic uses a live backup bucket | Port status, group counters, ping log |
| Link flapping | Failover follows port liveness; record repeated transitions | Timestamped event log and traffic continuity |
| Congestion without link failure | AI/policy may request a proactive best-effort reroute; FF alone should not trigger | Congestion telemetry, decision and enforcement logs |
| Double failure / no live path | Traffic may be interrupted; system must report no available path and recover when a path returns | Port events, group counters and recovery ping |

## 7. Recovery-Time Measurement Protocol

Define recovery time as:

**Recovery time = timestamp of first successful packet on the backup path − timestamp of link-down.**

1. Start continuous ping traffic across the primary path.
2. Record the link-down timestamp using the failure-injection log.
3. Record ping sequence numbers and timestamps.
4. Identify the first successful packet after failure and verify that traffic used the backup path.
5. Estimate recovery time from the timestamps; also report lost probes and probe interval.
6. Repeat at least 10 valid trials per mode for the Week 11 evaluation. Record invalid trials and their reasons rather than deleting them.
7. Report mean, standard deviation, minimum, maximum and 95th percentile.
8. Use under 1 second as the target, but report measured results honestly even if the target is missed.

## 8. Verification and Sign-Off

Before this design is considered verified:

- [ ] Confirm the port map with Member 2.
- [ ] Review Member 1's Fast-Failover group and flow implementation.
- [ ] Verify both groups and their buckets with OpenFlow 1.3 group dumps.
- [ ] Confirm queue actions are present in both buckets.
- [ ] Bring down the primary link during continuous traffic.
- [ ] Verify backup-bucket counters increase and quantify ping loss.
- [ ] Confirm recovery/failback when the primary link returns.
- [ ] Record any differences between this design and the running implementation.

## 9. Known Limitations

This document is a proposed design based on the repository topology and Week 9 work plan. Port assignments are inferred until verified. Group installation, queue preservation, failover, failback, and recovery time are not claimed as tested until evidence is collected.
