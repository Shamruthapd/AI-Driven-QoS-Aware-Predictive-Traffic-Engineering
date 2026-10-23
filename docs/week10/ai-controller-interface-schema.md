# Week 10: AI–SDN Controller Interface Specification & JSON Schema

**Authors:** Member 1 (Control-Plane Lead) & Member 4 (AI Runtime Lead)  
**Date:** Week 10 (Month 3)  
**Status:** AGREED & STANDARDIZED

---

## 1. Architecture Overview
To avoid blocking OpenFlow packet handling with PyTorch matrix computation, the AI loop runs as an independent OS process. The controller and AI process communicate asynchronously via HTTP REST endpoints or lightweight TCP JSON sockets provided by `controller/ai_sdn_bridge.py`.

```
+------------------------------------+          REST / JSON Sockets          +------------------------------------+
|           SDN Controller           |  ---------------------------------->  |           AI Loop Process          |
|  - Telemetry Polling (Every 5s)    |     POST /api/telemetry (Window)      |  - Sliding Window Buffer (W=12)    |
|  - Unified Event Logger            |                                       |  - PyTorch LSTM Inference          |
|  - Dynamic Flow-Mod Enforcement    |  <----------------------------------  |  - Anomaly Detector & Residuals    |
|  - Fast-Failover Group Tables      |     POST /api/decision (Action)       |  - Self-Healing Decision Module    |
+------------------------------------+                                       +------------------------------------+
```

---

## 2. Telemetry Window Payload (Controller -> AI Process)
**Endpoint:** `POST /api/telemetry` or TCP JSON message with type `"TELEMETRY_WINDOW"`

### Request Body Schema:
```json
{
  "timestamp": "2026-10-23T10:00:00.123456+00:00",
  "dpid": 1,
  "port_no": 3,
  "telemetry_window": [
    {
      "step": 0,
      "timestamp": "2026-10-23T09:59:05.123456+00:00",
      "rx_packets_delta": 1420,
      "tx_packets_delta": 2350,
      "rx_bytes_delta": 118400,
      "tx_bytes_delta": 2450000,
      "rx_dropped_delta": 0,
      "tx_dropped_delta": 0,
      "rx_errors_delta": 0,
      "tx_errors_delta": 0,
      "throughput_bps": 3920000.0,
      "packet_rate_pps": 754.0
    }
  ],
  "link_status": "UP",
  "active_mode": "full_ai_qos_ff"
}
```

---

## 3. AI Prediction & Decision Payload (AI Process -> Controller)
**Endpoint:** `POST /api/decision` or TCP JSON message with type `"AI_DECISION"`

### Request Body Schema:
```json
{
  "timestamp": "2026-10-23T10:00:00.450120+00:00",
  "dpid": 1,
  "port_no": 3,
  "prediction": {
    "predicted_throughput_bps": 14500000.0,
    "predicted_packet_rate_pps": 1280.0,
    "predicted_utilization_ratio": 0.92,
    "inference_latency_ms": 14.8
  },
  "anomaly": {
    "is_anomaly": true,
    "mse_residual": 8.42,
    "mse_threshold": 5.0,
    "confidence": 0.96
  },
  "decision": {
    "action": "PROACTIVE_REROUTE_BULK",
    "target_flow_class": "BEST_EFFORT",
    "source_port": 3,
    "destination_port": 4,
    "priority_protected": true,
    "cooldown_remaining_sec": 0
  }
}
```

---

## 4. Controller Enforcement Response (Controller -> AI Process)
```json
{
  "status": "SUCCESS",
  "dpid": 1,
  "enforcement_action": "FLOW_MOD_APPLIED",
  "flows_modified": 1,
  "flow_rule": {
    "traffic_class": "BEST_EFFORT",
    "assigned_queue": 0,
    "egress_port": 4,
    "metadata": 2
  },
  "timestamp": "2026-10-23T10:00:00.468000+00:00"
}
```

---

## 5. Unified Event Log Integration
Every exchange generates an atomic row in `data/results/unified_event_log.csv` tagged with one of the 6 canonical event types:
1. `telemetry`: Periodic switch port statistics query and delta calculation.
2. `prediction`: LSTM inference output with predicted bandwidth and MSE residual.
3. `decision`: Policy engine decision (e.g. `PROACTIVE_REROUTE_BULK` or `HOLD`).
4. `enforcement`: Controller flow modification or queue reassignment.
5. `port_down`: OpenFlow Port-Status down event notification.
6. `ff_used`: Switch hardware fast-failover group bucket transition.
