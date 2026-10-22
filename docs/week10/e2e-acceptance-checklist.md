# Week 10 — End-to-End Acceptance Checklist

## Objective
Validate the integrated SDN system from Mininet telemetry through AI prediction, policy decision, enforcement, and self-healing.

Mark a check PASS only after collecting evidence. Use BLOCKED when a required component or interface is unavailable.

| ID | Acceptance check | Required evidence | Status |
|---|---|---|---|
| E2E-01 | Mininet topology starts | Topology output and switch/link status | NOT RUN |
| E2E-02 | Three expected switches connect to OS-Ken | Controller logs showing switch connections | NOT RUN |
| E2E-03 | Telemetry flows and processed data refreshes | Recent timestamps and processed CSV | NOT RUN |
| E2E-04 | AI runtime logs valid predictions | Successful records in AI JSONL log | NOT RUN |
| E2E-05 | Predictions reach the policy component | Correlated prediction and decision events | NOT RUN |
| E2E-06 | Decisions trigger enforcement | Decision and corresponding enforcement logs | NOT RUN |
| E2E-07 | Required fast-failover groups are installed and verified | Switch/controller group configuration and state | NOT RUN |
| E2E-08 | Link failure triggers rerouting | Failure, reroute, and post-failure traffic evidence | NOT RUN |
| E2E-09 | Congestion triggers the expected self-healing action | Congestion scenario, action, and measurements | NOT RUN |
| E2E-10 | Unified logs contain all required event types | telemetry, prediction, decision, enforcement, port_down, ff_used | NOT RUN |
| E2E-11 | Full system runs uninterrupted for at least 30 minutes | Start/end timestamps and logs from the same session | NOT RUN |
| E2E-12 | End-to-end delay is measured | Correlated timestamps and calculated delay | NOT RUN |

## Test rules
- Record commit, environment, scenario, participants, start/end time, and log paths.
- Use PASS, FAIL, BLOCKED, or NOT RUN.
- A restart begins a new uninterrupted-run attempt.
- Unit tests and isolated AI runtime tests do not prove full-system integration.
- Gate B passes only when the complete chain succeeds in one uninterrupted session.
