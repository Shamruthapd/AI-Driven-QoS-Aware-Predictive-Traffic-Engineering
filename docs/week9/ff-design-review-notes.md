# Week 9: Fast-Failover Design Review Notes

## Review Scope
Compare the self-healing design with the current controller code and record gaps requiring implementation or verification.

## Finding 1: Fast-Failover Groups
**Status:** Not found in `controller/app.py` during the Week 9 source search.

The search found no matches for `OFPGT_FF`, `GroupMod`, `port_status`, `fast.failover`, or `group`. This does not prove that no related implementation exists elsewhere in the repository.

**Action:** Review the other controller modules and coordinate with Member 1 before integrating or duplicating implementation.

## Finding 2: Port Map
The proposed port map is provisional:
- s1: h1=1, h2=2, s3=3, s2=4
- s2: h3=1, h4=2, s3=3, s1=4
- s3: s1=1, s2=2

**Action:** Verify against Member 2's agreed port map and actual switch port output before installing groups.

## Finding 3: Recovery Evidence
No successful failover or recovery-time result is established by this code search.

**Action:** Test link failure, backup-bucket traffic, packet loss, recovery time, and failback. Save logs and group statistics.

## Design Review Checklist
- [ ] Confirm primary and backup paths with the team.
- [ ] Verify port numbers on running switches.
- [ ] Confirm Fast-Failover groups and watched ports are implemented.
- [ ] Confirm queue actions are compatible with the agreed QoS design.
- [ ] Verify local failover during manual link-down without controller intervention.
- [ ] Record failback behaviour and recovery measurements.
- [ ] Document discrepancies and retest after fixes.

## Review Conclusion
The design is documented, but implementation and live failover remain unverified. Do not mark the failover requirement complete until evidence is collected.

## Source-Code Review Results

### Controller Inspection
Reviewed `controller/app.py`, including switch initialization, flow installation, packet forwarding, and `apply_qos_policy()`.

- Ordinary MAC-learning forwarding is present.
- A priority UDP flow and QoS queue-selection logic are present.
- No Fast-Failover group creation, backup buckets, or watched-port configuration were found in the inspected controller code.
- No port-status event handler was found in the inspected controller code.
- The priority flow uses a direct output action rather than a Fast-Failover group.

### Discrepancy and Required Follow-Up
The documented self-healing design requires switch-local primary-to-backup failover. The inspected controller code does not demonstrate that behaviour.

Coordinate with Member 1 to confirm whether Fast-Failover implementation exists on another branch or is still pending. Do not duplicate or modify their implementation before confirming ownership.

### Verification Status
Source review completed for the inspected controller code. Port-map agreement, implementation elsewhere in the repository, and live failover behaviour remain to be verified. No recovery-time results are claimed.
