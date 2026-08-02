# OpenFlow Flow-Table Reference

**Project:** SDN-Based Edge Network
**OpenFlow Version:** 1.3
**Purpose:** Quick reference for flow-table design and Ryu controller implementation

---

## 1. Prioritization Explanation

In an SDN architecture, the controller (e.g., a Ryu app) doesn't move packets itself — it programs **flow entries** into the switch's flow table. Each entry has a **priority** value, and when an incoming packet matches more than one entry, the switch always applies the entry with the **highest priority number** first, regardless of the order the rules were installed in.

To make Video/Voice traffic from Host A "win" over Bulk Data traffic from Host B, we don't touch the wiring or the physical link — we just install two flow entries with different priorities and different actions:

- **Host A (Video/Voice):** A high-priority entry matches Host A's traffic (often identified by DSCP marking, IP address, or port) and sends it to a **high-priority output queue** attached to the egress port.
- **Host B (Bulk Data):** A lower-priority (or default/catch-all) entry matches Host B's traffic and sends it to a **best-effort queue** on the same egress port.

Because both flows share the same physical egress port, the **queue** — not the flow priority — is actually what enforces bandwidth/latency treatment on the wire. The **flow priority** just determines *which rule* a packet matches; the **queue** determines *how* that packet is scheduled once it's about to leave the port. In short:

> Flow priority = "which rule applies to this packet."
> Queue assignment (via `SET_QUEUE`) = "how this packet is scheduled on the wire."

Together, this means Host A's video/voice packets are classified early, matched precisely, and pushed into a queue that gets serviced first (or with guaranteed minimum bandwidth), while Host B's bulk data is left in a lower-priority queue that only gets bandwidth once higher-priority queues are satisfied.

---

## 2. QoS Match Fields & Actions

These are the OpenFlow 1.3 match fields and actions we'll need for QoS classification later in the project.

### Match Fields (OXM — OpenFlow Extensible Match)

| Field Name | Description |
|---|---|
| `ip_dscp` (or `nw_tos` in older syntax) | Matches the DSCP (Differentiated Services Code Point) value in the IP header — the primary field for QoS classification |
| `ip_ecn` | Matches Explicit Congestion Notification bits, useful for congestion-aware queuing |
| `eth_type` | Must be set to `0x0800` (IPv4) or `0x86dd` (IPv6) before `ip_dscp` can be matched |
| `ip_proto` | Matches protocol (e.g., `17` for UDP — common for RTP voice/video, `6` for TCP — common for bulk transfers) |
| `udp_src` / `udp_dst` | Matches specific UDP ports (e.g., RTP/RTCP media ports) |
| `tcp_src` / `tcp_dst` | Matches specific TCP ports (e.g., bulk transfer or file-sharing ports) |
| `in_port` | Matches the physical/logical ingress port (useful if Host A/B connect via dedicated switch ports) |
| `ipv4_src` / `ipv4_dst` | Matches source/destination IP address (e.g., Host A vs. Host B) |

### Actions

| Action | Description |
|---|---|
| `SET_QUEUE` | Assigns the packet to a specific queue ID on the egress port for QoS scheduling (this is how DSCP classification actually becomes bandwidth/latency treatment) |
| `SET_FIELD` (with `ip_dscp`) | Rewrites/remarks the DSCP value — useful at the network edge to enforce a trust boundary |
| `OUTPUT` | Forwards the packet out a specified port (usually paired with `SET_QUEUE`) |
| `METER` (via `GOTO_METER` / meter table) | Applies rate-limiting or policing, useful for capping bulk traffic |
| `GOTO_TABLE` | Sends the packet to a subsequent table for further pipeline processing (e.g., separating classification from forwarding logic) |

> **Note:** `SET_QUEUE` requires the queues to already exist on the switch (typically configured via OVSDB/`ovs-vsctl` on Open vSwitch), since OpenFlow itself only assigns packets *to* a queue — it doesn't create the queue's rate limits.

---

## 3. Annotated Flow Rules

Below are simplified, annotated OpenFlow 1.3 flow entries. Syntax is written in a generic `ovs-ofctl`-style format for readability — your Ryu code will express these as `OFPFlowMod` messages with matching `OFPMatch` and `OFPActionSetQueue` / `OFPActionOutput` objects.

### Example 1 — High-Priority Video/Voice Traffic (Host A)

```
# Match: IPv4 traffic from Host A, DSCP = 46 (EF - Expedited Forwarding, standard for voice/video)
# Priority: 200 (high)
# Action: send to high-priority queue 1 on port 2

priority=200,
ip,
nw_src=10.0.0.1,          # Host A's IP
ip_dscp=46,                # EF (Expedited Forwarding) - VoIP/video standard marking
actions=set_queue:1,output:2
```

**Explanation:** This rule catches packets from Host A that are already marked DSCP 46 (EF), which is the standard marking for real-time voice/video traffic. It assigns them to queue 1 (configured on the switch for low-latency, high-priority scheduling) and forwards them out port 2.

### Example 2 — Best-Effort Bulk Traffic (Host B)

```
# Match: IPv4 traffic from Host B, TCP protocol (typical for bulk transfers)
# Priority: 100 (lower than video/voice)
# Action: send to best-effort queue 0 on port 2

priority=100,
ip,
nw_src=10.0.0.2,          # Host B's IP
ip_proto=6,                 # TCP
actions=set_queue:0,output:2
```

**Explanation:** This rule catches Host B's bulk TCP traffic and assigns it to queue 0 (the default best-effort queue with no bandwidth guarantee). Its lower priority value means the video/voice rule above will always be evaluated first if a packet happens to match both.

> **Reminder:** Always include a low-priority catch-all/default rule (priority 0) that sends unmatched traffic to the controller or a default queue, so nothing gets silently dropped.

---

## 4. Fast-Failover Note

An OpenFlow **group table** is a separate table (alongside the flow table) that lets a flow entry's action point to a **group** instead of a single fixed action. A group contains one or more **action buckets**, and depending on the group's **type**, the switch decides which bucket(s) to execute.

One of the group types is **Fast-Failover (FF)**:

- Each bucket in a Fast-Failover group is tied to a **watch port** and/or **watch group**.
- The switch continuously monitors the liveness of that port/group at the *data-plane* level.
- If the primary bucket's watched port goes down, the switch **automatically switches to the next live bucket** — with no need to wait for the controller to detect the failure and push a new flow rule.

**Why it matters for our project:** For edge links carrying real-time video/voice, waiting for the controller round-trip to reroute traffic after a link failure can cause noticeable jitter or a dropped call. A Fast-Failover group lets the switch itself react to link-down events in milliseconds, rerouting Host A's high-priority traffic to a backup port instantly, while the controller is only informed after the fact (via a port-status message) for logging/re-optimization.

> In short: the **flow table** decides *what happens to a packet*; a **Fast-Failover group** decides *which physical path* that action actually uses, and switches paths on its own when a link fails.

---

*Reference sheet for Ryu controller development — update as match fields, queue IDs, and DSCP conventions are finalized for the project.*
