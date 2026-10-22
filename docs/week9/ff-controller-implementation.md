# Week 9 – Fast-Failover Controller Implementation

## 1. Objective

The objective of Week 9 was to implement Fast-Failover (FF) support in the SDN controller so that traffic can automatically use a backup path when the primary network path becomes unavailable.

The implementation was added without creating a separate controller. The existing OS-Ken controller and QoS enforcement architecture were preserved.

## 2. Network Topology

The topology contains three Open vSwitch switches:

- s1
- s2
- s3

The redundant backbone links are:

- s1-eth3 → s3
- s1-eth4 → s2
- s2-eth3 → s3
- s2-eth4 → s1

For s1, the Fast-Failover configuration is:

- Primary port: s1-eth3
- Backup port: s1-eth4
- Fast-Failover Group ID: 100

For s2, the Fast-Failover configuration is:

- Primary port: s2-eth3
- Backup port: s2-eth4
- Fast-Failover Group ID: 200

## 3. Fast-Failover Implementation

A new OS-Ken application was implemented in:

`controller/ff_groups.py`

The application creates OpenFlow 1.3 Fast-Failover groups using:

`OFPGT_FF`

Each group contains two buckets:

### Primary bucket

- Watches the primary switch port.
- Outputs traffic through the primary port.

### Backup bucket

- Watches the backup switch port.
- Outputs traffic through the backup port.

The implementation uses:

- Group 100 for s1
- Group 200 for s2

The Fast-Failover buckets contain only output actions. QoS queue selection remains in the existing controller QoS enforcement logic so that Fast-Failover does not override the configured QoS queue.

## 4. Integration with Existing Controller

The existing controller in:

`controller/app.py`

was modified to use Fast-Failover groups when forwarding traffic through redundant backbone ports.

A forwarding-action function determines whether the destination port belongs to an FF-enabled backbone path.

For s1:

- Port 3 → Group 100
- Port 4 → Group 100

For s2:

- Port 3 → Group 200
- Port 4 → Group 200

Host-facing ports continue to use normal OpenFlow output actions.

The existing QoS classification and queue enforcement remain unchanged.

Therefore, the architecture is:

Traffic → QoS Classification → Queue Action → Fast-Failover Group → Primary/Backup Output

## 5. Controller Integration

The Fast-Failover application was added to:

`scripts/run_controller.py`

The controller loads:

- OS-Ken OpenFlow handler
- Main SDN controller
- Telemetry
- Monitoring
- Fast-Failover application

The implementation was syntax checked successfully using Python compilation.

## 6. Fast-Failover Verification

Open vSwitch group information was checked using:

`ovs-ofctl -O OpenFlow13 dump-groups s1`

Group 100 was verified as:

- Type: Fast-Failover
- Primary watch port: s1-eth3
- Backup watch port: s1-eth4

Forwarding flows were also verified to reference Group 100 and Group 200.

This confirmed that the controller was not only creating the groups but also using them in forwarding flows.

## 7. Controlled Failure Test

A continuous ping was started between:

`h1 → h3`

The primary link:

`s1 → s3`

was then brought down.

After the failure, Fast-Failover group statistics were checked.

### Baseline

Before the controlled failure:

- Primary bucket: 526 packets
- Backup bucket: 112 packets
- Total: 638 packets

### During the failure-test interval

After bringing the primary link down:

- Primary bucket: 682 packets
- Backup bucket: 525 packets
- Total: 1207 packets

Change during the measured interval:

- Primary bucket: +156 packets
- Backup bucket: +413 packets
- Total: +569 packets

The substantial increase in backup-bucket traffic demonstrates that the backup path was actively used during the controlled primary-link failure.

Continuous h1 → h3 connectivity was maintained during the test.

## 8. Recovery

After the failure test, the primary link was restored:

`s1 → s3`

The interface was verified using:

`ip link show s1-eth3`

The interface reported:

`UP, LOWER_UP`

confirming that the primary link was restored.

## 9. Evidence

The controlled failure evidence is stored in:

`results/week9/evidence/W9_01_Fast_Failover_Test.txt`

The evidence contains the topology configuration, group statistics, failure-test results, and observations.

## 10. Result

Week 9 successfully implemented and verified OpenFlow Fast-Failover support in the existing OS-Ken SDN controller.

The implementation provides:

- Primary-path forwarding
- Backup-path forwarding
- Automatic Fast-Failover group selection by OVS
- Integration with existing QoS enforcement
- Controlled link-failure testing
- Verified backup-bucket traffic during failure

Exact failover/recovery time was not measured during this test, so no specific millisecond recovery-time claim is made.
