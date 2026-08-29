# Week 2 — SDN Controller Implementation and Verification Report

## 1. Project Information

**Project Title:** AI-driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

**Role:** Member 1

**Week:** 2

**Primary Responsibility:** SDN Controller Implementation

---

## 2. Objective

The objective of Week 2 was to establish and verify the SDN control plane using an OS-Ken controller, Open vSwitch, Mininet, and OpenFlow 1.3.

The implementation provides the basic forwarding functionality required for the subsequent traffic-generation, QoS-monitoring, telemetry, and dataset-generation stages of the project.

---

## 3. Implementation Environment

| Component | Version / Configuration |
|---|---|
| Operating System | Ubuntu/Linux VM |
| Python | 3.12.3 |
| SDN Controller | OS-Ken 4.2.1 |
| Network Emulator | Mininet 2.3.0 |
| Virtual Switch | Open vSwitch 3.3.4 |
| Protocol | OpenFlow 1.3 |
| Controller Endpoint | 127.0.0.1:6633 |
| Virtual Environment | ~/SDN-Lab/venv |

---

## 4. Controller Components

The Week 2 implementation consists of the following modules:

```text
scripts/run_controller.py
controller/app.py
controller/monitor.py
controller/telemetry.py
````

### 4.1 Controller Launcher

`scripts/run_controller.py` uses the OS-Ken AppManager to load:

* `os_ken.controller.ofp_handler`
* `controller.app`
* `controller.telemetry`
* `controller.monitor`

The project root is added to the Python import path.

### 4.2 Main SDN Controller

`controller/app.py` implements:

* OpenFlow 1.3
* switch connection handling
* table-miss flow installation
* Packet-In handling
* MAC learning
* destination lookup
* Flow-Mod installation
* Packet-Out processing

---

## 5. OpenFlow 1.3 and Mininet Setup

The verified Mininet topology was:

```text
h1 ---- s1 ---- h2
```

The topology was started using:

```bash
sudo mn --topo single,2 --mac \
  --switch ovsk,protocols=OpenFlow13 \
  --controller=remote,ip=127.0.0.1,port=6633
```

The Open vSwitch switch was configured for OpenFlow 1.3 and connected to the OS-Ken controller at:

```text
127.0.0.1:6633
```

The controller-switch connection was successfully established.

---

## 6. Table-Miss Flow

When the switch connects, the controller installs a table-miss flow with priority `0`.

The rule sends unmatched packets to the controller:

```text
priority=0 actions=CONTROLLER
```

This allows the controller to receive Packet-In messages for packets that do not yet match a forwarding rule.

---

## 7. Packet-In and MAC Learning

The controller processes Packet-In messages and extracts:

* ingress port
* source MAC address
* destination MAC address

The source MAC address is stored in a per-switch MAC learning table.

The forwarding decision is then made based on whether the destination MAC address is already known.

Unknown destinations are flooded.

Known destinations are forwarded through the learned switch port.

LLDP packets are ignored.

---

## 8. Flow-Mod Installation

When the destination MAC address is known, the controller installs a forwarding flow.

The implemented match includes:

```text
in_port
eth_dst
```

The forwarding flow uses priority `10`.

This allows subsequent matching packets to be forwarded directly by the switch.

---

## 9. Packet-Out

The controller sends the current Packet-In packet using an OpenFlow Packet-Out message.

This allows the current packet to be forwarded immediately while the forwarding flow is installed for subsequent traffic.

---

## 10. Connectivity Verification

Connectivity was verified using:

```text
pingall
```

Observed result:

```text
*** Results: 0% dropped (2/2 received)
```

This confirms successful connectivity between the Mininet hosts through the OpenFlow-controlled switch.

---

## 11. Flow-Table Verification

The live OVS flow table was verified using:

```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
```

The verified forwarding entries included:

```text
priority=10,in_port="s1-eth2",dl_dst=00:00:00:00:00:01
actions=output:"s1-eth1"
```

and:

```text
priority=10,in_port="s1-eth1",dl_dst=00:00:00:00:00:02
actions=output:"s1-eth2"
```

The table-miss rule was also verified:

```text
priority=0 actions=CONTROLLER:65535
```

The forwarding entries had non-zero packet counters, confirming that traffic actually traversed the installed flows.

The flow-table evidence is stored at:

```text
screenshots/week2-ovs-flow-table.jpg
```

---

## 12. Telemetry Integration

The controller launcher also loads the monitoring and telemetry applications.

`controller/monitor.py` periodically requests OpenFlow port statistics from connected switches.

The configured polling interval is:

```text
5 seconds
```

`controller/telemetry.py` receives OpenFlow port-statistics replies and stores raw measurements in:

```text
datasets/raw/telemetry.csv
```

Detailed telemetry processing and QoS feature extraction are addressed in the later Week 4 work.

---

## 13. Verification Summary

| Component                    | Result         |
| ---------------------------- | -------------- |
| OS-Ken controller            | Verified       |
| OpenFlow 1.3                 | Verified       |
| Controller-switch connection | Verified       |
| Table-miss flow              | Verified       |
| Packet-In handling           | Verified       |
| MAC learning                 | Verified       |
| Flow-Mod installation        | Verified       |
| Packet-Out                   | Implemented    |
| Mininet connectivity         | Verified       |
| `pingall`                    | 0% packet loss |
| OVS forwarding flows         | Verified       |
| Flow counters                | Non-zero       |
| Evidence screenshot          | Captured       |

---

## 14. Challenges and Resolution

### Challenge 1: OVS flow inspection from Mininet CLI

The `ovs-ofctl` command was initially attempted inside the Mininet CLI.

The Mininet CLI does not directly execute the Linux `ovs-ofctl` utility.

**Resolution:** The command was executed from a separate Linux terminal while the Mininet topology was still running.

### Challenge 2: Switch unavailable after Mininet cleanup

After exiting Mininet, the OVS bridge `s1` was removed.

Attempting to inspect the switch afterward resulted in:

```text
s1 is not a bridge or a socket
```

**Resolution:** The Mininet topology was restarted and the flow table was inspected while `s1` was active.

---

## 15. Week 2 Outcome

Week 2 successfully established the functional SDN control-plane foundation of the project.

The verified implementation demonstrates communication between Mininet/Open vSwitch and the OS-Ken controller using OpenFlow 1.3.

The controller successfully performs MAC learning, dynamic forwarding-rule installation, Packet-In processing, and Packet-Out forwarding.

The completed controller foundation will support the next project stages:

```text
SDN Controller
      ↓
Traffic Generation
      ↓
Telemetry Collection
      ↓
QoS Feature Extraction
      ↓
Predictive Traffic Engineering
      ↓
Self-Healing
```

## 16. Week 3 Next Step

The next stage will focus on reproducible iPerf3 traffic generation, including TCP bulk traffic, UDP steady-rate traffic, controlled experiment duration, and baseline throughput measurements.
