# Final Live Demonstration Runbook — Control Plane

**Operator:** Member 1 (Control-Plane Lead)  
**Target:** OS-Ken OpenFlow 1.3 Controller & AI-SDN Bridge  

---

## 1. Controller Startup Command
Open Terminal 1 (WSL or Linux environment):
```bash
# Navigate to project root
cd /path/to/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering

# Activate Python virtual environment
source venv/bin/activate

# Launch the unified SDN controller with Fast-Failover and Port Logger
./scripts/run_controller.sh local
```

Expected Output:
```text
====================================
 AI-QoS SDN Controller Started 
 Controller Version: v6 
 OpenFlow Version: 1.3 
 QoS Classification: ENABLED 
 QoS Metadata Tags: ENABLED 
 Queue Enforcement: ENABLED 
 Fast-Failover Groups: ENABLED 
 s1 FF Group: 100 
 s2 FF Group: 200 
 s3 FF Group: 300 
====================================
Fast-Failover Group Module with QoS Queue Preservation Started
Port Status Event Logger Initialized
```

---

## 2. Verifying Switch Group Tables During Demo
Once Member 2 starts Mininet in Terminal 2, inspect switch groups:
```bash
# Verify group table on Edge Switch s1
ovs-ofctl -O OpenFlow13 dump-groups s1

# Expected response showing buckets and set_queue actions:
# group_id=100,type=ff,bucket=watch_port:3,actions=set_queue:1,output:3,bucket=watch_port:4,actions=set_queue:1,output:4
# group_id=101,type=ff,bucket=watch_port:3,actions=set_queue:0,output:3,bucket=watch_port:4,actions=set_queue:0,output:4
```

---

## 3. Verifying Flow Classification & Active QoS Rules
```bash
# View installed QoS flows matching DSCP/ports and metadata tags
ovs-ofctl -O OpenFlow13 dump-flows s1

# Look for priority=100 flow with priority metadata:
# priority=100,ip,nw_dst=10.0.0.3,udp_dst=5202 actions=write_metadata:0x1,group:100
```

---

## 4. Demonstrating Zero Flow-Mods During Failover
When Member 3 cues Member 2 to trigger the link failure:
1. Show the controller console in real time.
2. Highlight that the controller logs `PORT_STATUS_EVENT: DPID=1 | PORT=3 | STATE=DOWN`.
3. Point out that **NO new OFPT_FLOW_MOD is sent**.
4. Run `ovs-ofctl -O OpenFlow13 dump-group-stats s1` to prove that packet counters immediately increment on Bucket 1 (port 4).

---

## 5. Live Mode Switching Demo
To demonstrate the mode switch between `baseline_shortest_path`, `reactive`, and `full_ai_qos_ff`:
```bash
# Inspect current mode
curl -s http://127.0.0.1:8080/api/status

# Switch mode via bridge API without code restart
curl -X POST http://127.0.0.1:8080/api/mode -H "Content-Type: application/json" -d '{"mode": "full_ai_qos_ff", "trial_id": "demo_run_01"}'
```
