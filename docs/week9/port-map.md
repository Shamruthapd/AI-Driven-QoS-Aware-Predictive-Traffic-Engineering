# Week 9: Network Topology Port-Map Specification

**Author:** Member 2 (Data-Plane Failover & Experiment Lead)  
**Date:** Week 9 (Month 3 Freeze)  
**Status:** FROZEN & VERIFIED

---

## 1. Overview
This document specifies the exact, frozen OpenFlow switch port numbers, interface bindings, and link capacities across the edge network topology. All controller group configurations (Member 1) and self-healing policies (Member 3) must conform strictly to these port numbers.

---

## 2. Port Mapping Table

### Edge Switch s1 (DPID = 1)
| OpenFlow Port | Linux Interface | Connected Node | Connection Type | Bandwidth | QoS Queues Configured | Role |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `s1-eth1` | Host `h1` (`10.0.0.1`) | Access link | 10 Mbps | Default (None) | Host Access |
| **2** | `s1-eth2` | Host `h2` (`10.0.0.2`) | Access link | 10 Mbps | Queue 0 (4M), Queue 1 (8-10M) | Host Access |
| **3** | `s1-eth3` | Switch `s3` (`s3-eth1`) | Backbone link | 100 Mbps | Queue 0 (4M), Queue 1 (8-10M) | **Primary Egress Path** |
| **4** | `s1-eth4` | Switch `s2` (`s2-eth4`) | Inter-edge link | 100 Mbps | Queue 0 (4M), Queue 1 (8-10M) | **Backup / Fast-Failover Egress** |

### Edge Switch s2 (DPID = 2)
| OpenFlow Port | Linux Interface | Connected Node | Connection Type | Bandwidth | QoS Queues Configured | Role |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `s2-eth1` | Host `h3` (`10.0.0.3`) | Access link | 10 Mbps | Default (None) | Host Access |
| **2** | `s2-eth2` | Host `h4` (`10.0.0.4`) | Access link | 10 Mbps | Queue 0 (4M), Queue 1 (8-10M) | Host Access |
| **3** | `s2-eth3` | Switch `s3` (`s3-eth2`) | Backbone link | 100 Mbps | Queue 0 (4M), Queue 1 (8-10M) | **Primary Egress Path** |
| **4** | `s2-eth4` | Switch `s1` (`s1-eth4`) | Inter-edge link | 100 Mbps | Queue 0 (4M), Queue 1 (8-10M) | **Backup / Fast-Failover Egress** |

### Core Backbone Switch s3 (DPID = 3)
| OpenFlow Port | Linux Interface | Connected Node | Connection Type | Bandwidth | QoS Queues Configured | Role |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | `s3-eth1` | Switch `s1` (`s1-eth3`) | Backbone link | 100 Mbps | None (OVS Default) | Inter-switch Core |
| **2** | `s3-eth2` | Switch `s2` (`s2-eth3`) | Backbone link | 100 Mbps | None (OVS Default) | Inter-switch Core |

---

## 3. Fast-Failover Group Assignment Rules
Based on this frozen topology:
- **Switch s1 (Group 100):**
  - **Bucket 1 (Primary):** `watch_port = 3`, `set_queue = 1` (Priority) or `set_queue = 0` (Best-Effort), `output = 3` (to `s3`).
  - **Bucket 2 (Backup):** `watch_port = 4`, `set_queue = 1` (Priority) or `set_queue = 0` (Best-Effort), `output = 4` (to `s2`).
- **Switch s2 (Group 200):**
  - **Bucket 1 (Primary):** `watch_port = 3`, `set_queue = 1` (Priority) or `set_queue = 0` (Best-Effort), `output = 3` (to `s3`).
  - **Bucket 2 (Backup):** `watch_port = 4`, `set_queue = 1` (Priority) or `set_queue = 0` (Best-Effort), `output = 4` (to `s1`).

---

## 4. IP and MAC Address Bindings
| Node | IP Address | MAC Address | Connected Switch Port |
| :--- | :--- | :--- | :--- |
| **h1** | `10.0.0.1/24` | `00:00:00:00:00:01` | `s1-eth1` (Port 1) |
| **h2** | `10.0.0.2/24` | `00:00:00:00:00:02` | `s1-eth2` (Port 2) |
| **h3** | `10.0.0.3/24` | `00:00:00:00:00:03` | `s2-eth1` (Port 1) |
| **h4** | `10.0.0.4/24` | `00:00:00:00:00:04` | `s2-eth2` (Port 2) |
