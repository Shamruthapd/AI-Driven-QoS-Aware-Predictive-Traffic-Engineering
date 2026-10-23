# Final Live Demonstration Script — Self-Healing & Fast-Failover Segment

**Presenter:** Member 3 (Self-Healing Design Lead)  
**Co-Operators:** Member 1 (Controller Console), Member 2 (Mininet & Injector)  
**Target Duration:** 3 Minutes  

---

## 1. Stage Setup (T = 0:00 - 0:45)
- **Member 3 (Speaking):**
  > *"Examiners, I will now demonstrate the most critical capability of our system: sub-second self-healing without controller round-trip overhead.
  > On the left screen, Member 2 has Mininet running with continuous high-rate traffic flowing between host h1 and host h3. On the right, Member 1 has the OpenFlow group tables displayed."*
- **Member 1 Action:** Runs `ovs-ofctl -O OpenFlow13 dump-group-stats s1`.
- **Member 3 (Pointing to screen):**
  > *"Notice Bucket 0 packet counters are incrementing rapidly. Bucket 1 (the backup path) has 0 packets. Traffic is currently flowing along the primary path via switch s3."*

---

## 2. Triggering the Hard Link Failure (T = 0:45 - 1:30)
- **Member 3 (Speaking):**
  > *"Now, Member 2 will inject a hard physical link-down on interface s1-eth3, cutting the primary link."*
- **Member 2 Action:** Executes `sudo ip link set dev s1-eth3 down` (or `python3 mininet/inject_failure.py --interface s1-eth3 --down-duration 10.0`).
- **Member 3 (Speaking):**
  > *"Look at the live ping monitor in Terminal 2! Only 3 to 4 pings drop—representing just 40 milliseconds of disruption—before traffic immediately continues!
  > More importantly, look at Member 1's controller log: ZERO new Flow-Mod messages were sent by the controller! The switch detected the dead link locally and flipped to Bucket 1 in hardware."*
- **Member 1 Action:** Runs `ovs-ofctl -O OpenFlow13 dump-group-stats s1`. Shows Bucket 1 packet counters incrementing.

---

## 3. Link Restoration & Failback (T = 1:30 - 2:15)
- **Member 2 Action:** Restores interface: `sudo ip link set dev s1-eth3 up`.
- **Member 3 (Speaking):**
  > *"When the primary link returns, the OpenFlow Fast-Failover group automatically detects port liveness on watched port 3 and restores traffic to the primary path without any packet loss.
  > This confirms our first layer of self-healing."*

---

## 4. Proactive AI Congestion Rerouting Segment (T = 2:15 - 3:00)
- **Member 3 (Speaking):**
  > *"Next, we demonstrate Layer 2: soft degradation. In Scenario S2, when an aggressive bulk flow attempts to congest the link, our LSTM predictive model detects the rising bandwidth demand 15 seconds in advance.
  > As shown in the unified event log, the Self-Healing Module proactively redirects bulk TCP to the secondary link, protecting the priority voice stream from bufferbloat."*
- **Member 1 Action:** Shows `data/results/unified_event_log.csv` showing `PROACTIVE_REROUTE_BULK`.
