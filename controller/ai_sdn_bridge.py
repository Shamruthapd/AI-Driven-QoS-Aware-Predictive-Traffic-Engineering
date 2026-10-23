"""
AI-SDN Integration Bridge.
Provides REST and JSON interface between the OS-Ken OpenFlow Controller and the AI loop process.
Decouples PyTorch inference latency from OpenFlow packet processing while unifying
event logging across telemetry, prediction, decision, enforcement, port_down, and ff_used.
"""

import csv
import json
import os
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Load config if available
CONFIG = {}
CONFIG_PATH = Path("controller/config.yaml")
try:
    import yaml
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            CONFIG = yaml.safe_load(f) or {}
except Exception:
    pass

DEFAULT_HOST = CONFIG.get("controller", {}).get("bridge_ip", "0.0.0.0")
DEFAULT_PORT = CONFIG.get("controller", {}).get("bridge_port", 8080)
UNIFIED_LOG_PATH = Path(CONFIG.get("logging", {}).get("unified_event_log", "data/results/unified_event_log.csv"))


class UnifiedEventLogger:
    """
    Central thread-safe logger for all six canonical event types:
    - telemetry
    - prediction
    - decision
    - enforcement
    - port_down
    - ff_used
    """
    _lock = threading.Lock()

    @classmethod
    def log(cls, event_type, dpid=1, port=3, details="", trial_id="", mode="full_ai_qos_ff"):
        now_iso = datetime.now(timezone.utc).isoformat()
        epoch_ts = time.time()
        
        row = {
            "timestamp_iso": now_iso,
            "timestamp_epoch": f"{epoch_ts:.6f}",
            "event_type": event_type,
            "dpid": dpid,
            "port": port,
            "trial_id": trial_id,
            "mode": mode,
            "details": details if isinstance(details, str) else json.dumps(details)
        }

        with cls._lock:
            UNIFIED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            file_exists = UNIFIED_LOG_PATH.exists()
            with open(UNIFIED_LOG_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["timestamp_iso", "timestamp_epoch", "event_type", "dpid", "port", "trial_id", "mode", "details"]
                )
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
                f.flush()

        print(f"[{now_iso}] [{event_type.upper()}] DPID={dpid} Port={port} | Mode={mode} | {details}")


# Shared in-memory state
SHARED_STATE = {
    "latest_telemetry": {},
    "latest_prediction": {},
    "latest_decision": {},
    "enforcement_hook": None,
    "active_mode": CONFIG.get("operation_mode", {}).get("mode", "full_ai_qos_ff"),
    "trial_id": "trial_001"
}


class BridgeRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health" or self.path == "/api/status":
            self._send_json(200, {
                "status": "HEALTHY",
                "mode": SHARED_STATE["active_mode"],
                "trial_id": SHARED_STATE["trial_id"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        elif self.path == "/api/telemetry":
            self._send_json(200, SHARED_STATE.get("latest_telemetry", {}))
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if self.path == "/api/telemetry":
            # Controller pushes new telemetry window
            SHARED_STATE["latest_telemetry"] = payload
            UnifiedEventLogger.log(
                event_type="telemetry",
                dpid=payload.get("dpid", 1),
                port=payload.get("port_no", 3),
                details=f"Received telemetry window size {len(payload.get('telemetry_window', []))}",
                trial_id=SHARED_STATE["trial_id"],
                mode=SHARED_STATE["active_mode"]
            )
            self._send_json(200, {"status": "TELEMETRY_RECORDED"})

        elif self.path == "/api/prediction":
            # AI Loop pushes LSTM prediction
            SHARED_STATE["latest_prediction"] = payload
            UnifiedEventLogger.log(
                event_type="prediction",
                dpid=payload.get("dpid", 1),
                port=payload.get("port_no", 3),
                details=payload.get("prediction", {}),
                trial_id=SHARED_STATE["trial_id"],
                mode=SHARED_STATE["active_mode"]
            )
            self._send_json(200, {"status": "PREDICTION_RECORDED"})

        elif self.path == "/api/decision":
            # Self-Healing Module or Policy Engine pushes reroute decision
            SHARED_STATE["latest_decision"] = payload
            action = payload.get("decision", {}).get("action", "HOLD")
            dpid = payload.get("dpid", 1)
            port = payload.get("port_no", 3)

            UnifiedEventLogger.log(
                event_type="decision",
                dpid=dpid,
                port=port,
                details=payload.get("decision", {}),
                trial_id=SHARED_STATE["trial_id"],
                mode=SHARED_STATE["active_mode"]
            )

            # Trigger enforcement hook if registered
            enforcement_result = "NO_ENFORCEMENT_REQUIRED"
            if action in ("PROACTIVE_REROUTE_BULK", "REROUTE_BEST_EFFORT"):
                if SHARED_STATE["enforcement_hook"]:
                    try:
                        SHARED_STATE["enforcement_hook"](payload)
                        enforcement_result = "ENFORCEMENT_SUCCESS"
                    except Exception as ex:
                        enforcement_result = f"ENFORCEMENT_ERROR: {ex}"
                else:
                    enforcement_result = "ENFORCEMENT_RECORDED_DRY_RUN"

                UnifiedEventLogger.log(
                    event_type="enforcement",
                    dpid=dpid,
                    port=port,
                    details=f"Action={action} Result={enforcement_result}",
                    trial_id=SHARED_STATE["trial_id"],
                    mode=SHARED_STATE["active_mode"]
                )

            self._send_json(200, {
                "status": "DECISION_PROCESSED",
                "action": action,
                "enforcement": enforcement_result
            })

        elif self.path == "/api/mode":
            # Switch active mode
            new_mode = payload.get("mode")
            if new_mode in ("baseline_shortest_path", "reactive", "full_ai_qos_ff"):
                SHARED_STATE["active_mode"] = new_mode
                SHARED_STATE["trial_id"] = payload.get("trial_id", SHARED_STATE["trial_id"])
                UnifiedEventLogger.log(
                    event_type="decision",
                    details=f"Switched operation mode to {new_mode}",
                    trial_id=SHARED_STATE["trial_id"],
                    mode=SHARED_STATE["active_mode"]
                )
                self._send_json(200, {"status": "MODE_UPDATED", "mode": new_mode})
            else:
                self._send_json(400, {"error": "Invalid mode"})
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def log_message(self, format, *args):
        # Suppress noisy standard HTTP logs
        pass


def start_bridge_server(host=DEFAULT_HOST, port=DEFAULT_PORT):
    server = HTTPServer((host, port), BridgeRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[*] AI-SDN Bridge HTTP Server running on {host}:{port}")
    return server


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    print(f"Starting standalone AI-SDN Bridge on {host}:{port}...")
    server = HTTPServer((host, port), BridgeRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping bridge server.")
        server.server_close()
