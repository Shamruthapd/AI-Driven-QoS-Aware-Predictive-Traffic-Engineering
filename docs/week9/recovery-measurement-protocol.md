# Week 9: Recovery-Measurement Protocol

## Objective
Measure data-plane recovery after a primary inter-switch link failure and determine whether recovery is under one second.

## Recovery-Time Definition
Recovery time = timestamp of the first successful packet after failure - timestamp of link-down.

The link-down timestamp must come from the failure-injection log. The first successful packet must be identified from the continuous traffic log.

## Procedure
1. Start Mininet and connect all switches to the controller.
2. Verify the primary and backup paths and record Fast-Failover group statistics.
3. Start continuous ping across the primary path. Use a documented probe interval, preferably 10 ms if the environment supports it.
4. Record the trial ID, mode, link under test, and start time.
5. Bring the primary link down and record the exact timestamp.
6. Identify the first successful ping after the failure and verify that traffic uses the backup path.
7. Record packet loss, the number of lost probes, probe interval, estimated recovery time, and group-counter changes.
8. Restore the primary link and observe failback.
9. Repeat at least 10 valid trials per mode for Week 11. Record invalid trials and reasons; do not silently discard them.

## Metrics
- Recovery time in milliseconds.
- Lost ping probes.
- Probe interval in milliseconds.
- Estimated loss duration = lost probes × probe interval.
- Whether the backup bucket carried traffic.
- Whether failback occurred after link restoration.

## Target and Reporting
Target: recovery under 1 second.

Report measured results honestly. Do not claim the target was met until trial evidence supports it. For the final analysis, report mean, standard deviation, minimum, maximum, and 95th percentile for valid trials.

## Trial Record Template

| Trial ID | Mode | Link failed | Link-down timestamp | First successful packet timestamp | Lost probes | Probe interval (ms) | Recovery time (ms) | Valid? | Notes |
|---|---|---|---|---|---:|---:|---:|---|---|
| T001 | To be specified | To be specified | Pending | Pending | Pending | Pending | Pending | Pending | Awaiting live test |

## Evidence to Save
- Failure-injection timestamps.
- Continuous ping output.
- Fast-Failover group and group-statistics output before and after failure.
- Relevant controller port-status logs.
- Trial validity notes and any observed failures.

## Current Status
This document defines the test procedure only. No new recovery-time measurements or successful Fast-Failover results are claimed here.
