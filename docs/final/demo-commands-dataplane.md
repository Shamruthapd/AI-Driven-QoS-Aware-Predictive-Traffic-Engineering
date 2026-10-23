# Final Live Demonstration Runbook — Data Plane

**Operator:** Member 2 (Data-Plane Failover & Experiment Lead)  
**Target:** Mininet Emulation, Queue Configuration & Traffic Scenarios  

---

## 1. Mininet Network Startup Command
Open Terminal 2 (Mininet Terminal):
```bash
# Clean up any leftover virtual interfaces from prior runs
sudo mn -c

# Launch the final edge fat-tree topology
sudo python3 mininet/topo.py --controller-ip 127.0.0.1 --controller-port 6633
```

Expected Mininet CLI Prompt:
```text
*** Creating network
*** Adding controller
*** Adding hosts:
h1 h2 h3 h4 
*** Adding switches:
s1 s2 s3 
*** Adding links:
(h1, s1) (h2, s1) (h3, s2) (h4, s2) (s1, s3) (s2, s3) (s1, s2)
*** Starting controller
*** Starting 3 switches
s1 s2 s3 ...
*** Running CLI for verification
mininet>
```

---

## 2. Apply QoS Queue Configuration on Primary & Backup Ports
In Terminal 3 (or from host shell):
```bash
# Execute the comprehensive queue setup script
sudo bash mininet/configure_queues.sh
```

Verification inside Mininet CLI:
```text
mininet> dpctl dump-flows
```
Observe that egress ports `s1-eth3`, `s1-eth4`, `s2-eth3`, and `s2-eth4` now report HTB QoS queues attached.

---

## 3. Launching Live Traffic Scenarios
From Terminal 3, execute any of the standardized scenarios:

### Scenario S1 (Steady Mixed Load):
```bash
python3 mininet/run_scenario.py --scenario scenarios/S1_steady.yaml --mode full_ai_qos_ff --trial-id demo_s1
```

### Scenario S2 (Heavy Congestion Demo):
```bash
python3 mininet/run_scenario.py --scenario scenarios/S2_congestion.yaml --mode full_ai_qos_ff --trial-id demo_s2
```

### Scenario S3 (Live Link Failure Under Load):
```bash
python3 mininet/run_scenario.py --scenario scenarios/S3_failure.yaml --mode full_ai_qos_ff --trial-id demo_s3
```

---

## 4. Manual Link Failure Trigger on Cue
During the presentation, when Member 3 cues the live failure demonstration:
```bash
# Manually trigger primary link down for 8 seconds
sudo python3 mininet/inject_failure.py --interface s1-eth3 --down-duration 8.0
```
- In Mininet CLI or ping monitor: observe that only **3–4 pings are dropped**, followed immediately by continuous ping recovery via backup port 4.
