# Week 9: Failure-Scenario Catalogue

## Purpose
Define expected system behaviour for link failures, unstable links, congestion, and loss of all available paths.

## Scenario 1: Single-Link Failure
**Trigger:** The primary inter-switch link goes down during continuous traffic.

**Expected behaviour:**
- OpenFlow Fast-Failover selects a live backup bucket locally.
- Traffic continues over the backup path if the required links and flows are available.
- Priority queue treatment should be preserved in the backup bucket.

**Evidence:** Link-down timestamp, group statistics before and after failure, continuous ping output, and packet loss.

**Status:** Pending live verification.

## Scenario 2: Link Flapping
**Trigger:** The same link repeatedly goes down and comes back up.

**Expected behaviour:**
- Fast-Failover responds to port liveness.
- Repeated transitions are timestamped and recorded.
- Recovery behaviour is observed for oscillation or repeated packet loss.

**Evidence:** Port-status events, group counters, ping logs, and link transition timestamps.

**Status:** Pending live verification.

## Scenario 3: Congestion Without Link Failure
**Trigger:** Throughput or another agreed congestion indicator crosses the configured threshold while links remain up.

**Expected behaviour:**
- The AI/policy layer detects sustained congestion according to its configured confirmation rule.
- A proactive reroute may be requested for best-effort traffic if controller enforcement is implemented.
- Priority traffic should retain its intended protection.
- Fast-Failover alone is not expected to detect congestion.

**Evidence:** Telemetry, prediction, policy decision, enforcement event if implemented, and traffic measurements.

**Status:** Policy dry-run tested; live enforcement not yet verified.

## Scenario 4: Double Failure / No Available Path
**Trigger:** Both the primary and backup paths become unavailable.

**Expected behaviour:**
- Traffic may be interrupted because no live path remains.
- The system records the outage instead of claiming successful failover.
- Connectivity is tested again after a path is restored.

**Evidence:** Port-status events, group statistics, ping logs, and timestamps for restoration.

**Status:** Pending live verification.

## General Recording Rules
For every test, record the scenario, trial ID, link changed, start and end timestamps, traffic type, packet loss, observed recovery time, and whether the trial is valid. Do not invent results or discard failed trials without documenting the reason.
- Repeated transitions are timestamped and recorded.
- Recovery behaviour is observed for oscillation or repeated packet loss.

**Evidence:** Port-status events, group counters, ping logs, and link transition timestamps.

**Status:** Pending live verification.

## Scenario 3: Congestion Without Link Failure
**Trigger:** Throughput or another agreed congestion indicator crosses the configured threshold while links remain up.

**Expected behaviour:**
- The AI/policy layer detects sustained congestion according to its configured confirmation rule.
- A proactive reroute may be requested for best-effort traffic if controller enforcement is implemented.
- Priority traffic should retain its intended protection.
- Fast-Failover alone is not expected to detect congestion.

**Evidence:** Telemetry, prediction, policy decision, enforcement event if implemented, and traffic measurements.

**Status:** Policy dry-run tested; live enforcement not yet verified.

## Scenario 4: Double Failure / No Available Path
**Trigger:** Both the primary and backup paths become unavailable.

**Expected behaviour:**
- Traffic may be interrupted because no live path remains.
- The system records the outage instead of claiming successful failover.
- Connectivity is tested again after a path is restored.

**Evidence:** Port-status events, group statistics, ping logs, and timestamps for restoration.

**Status:** Pending live verification.

## General Recording Rules
For every test, record the scenario, trial ID, link changed, start and end timestamps, traffic type, packet loss, observed recovery time, and whether the trial is valid. Do not invent results or discard failed trials without documenting the reason.
