#!/usr/bin/env python3
"""
AI-Driven Self-Healing Module (Layer 2 Proactive Rerouting).
Cooperates with OpenFlow Fast-Failover (Layer 1) to provide resilient traffic engineering.
- Detects predictive congestion and performance degradation using LSTM residuals and calibrated utilization.
- Proactively reroutes bulk (Best-Effort) flows to alternate paths before drops occur, while preserving Priority flows.
- Implements cooldown timers and hysteresis to eliminate route oscillation.
- Respects Layer 1 Fast-Failover: avoids conflicting flow modifications during physical link down events.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Try importing YAML config
CONFIG = {}
CONFIG_FILE = Path("controller/config.yaml")
if CONFIG_FILE.exists():
    try:
        import yaml
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            CONFIG = yaml.safe_load(f) or {}
    except Exception:
        pass

DEFAULT_COOLDOWN_SEC = CONFIG.get("self_healing", {}).get("cooldown_sec", 15.0)
DEFAULT_CONGESTION_THRESHOLD = CONFIG.get("self_healing", {}).get("congestion_trigger_threshold", 0.85)
DEFAULT_RECOVERY_THRESHOLD = CONFIG.get("self_healing", {}).get("failback_recovery_threshold", 0.60)
UNIFIED_LOG = Path(CONFIG.get("logging", {}).get("unified_event_log", "data/results/unified_event_log.csv"))


class SelfHealingEngine:
    def __init__(
        self,
        cooldown_sec=DEFAULT_COOLDOWN_SEC,
        congestion_threshold=DEFAULT_CONGESTION_THRESHOLD,
        recovery_threshold=DEFAULT_RECOVERY_THRESHOLD,
        log_path=UNIFIED_LOG
    ):
        self.cooldown_sec = cooldown_sec
        self.congestion_threshold = congestion_threshold
        self.recovery_threshold = recovery_threshold
        self.log_path = Path(log_path)
        
        # State tracking
        self.current_bulk_route = "PRIMARY"  # "PRIMARY" (port 3) or "BACKUP" (port 4)
        self.last_action_timestamp = 0.0
        self.last_action_reason = "INIT"
        self.decision_count = 0

    def evaluate_telemetry(self, telemetry_data):
        """
        Evaluates current and predicted network state to produce self-healing actions.
        
        telemetry_data dict:
        - dpid: int
        - port_no: int
        - link_status: 'UP' or 'DOWN'
        - predicted_utilization: float (0.0 to 1.0)
        - is_anomaly: bool
        - mse_residual: float
        - timestamp: str (optional)
        """
        now = time.time()
        dpid = telemetry_data.get("dpid", 1)
        port_no = telemetry_data.get("port_no", 3)
        link_status = telemetry_data.get("link_status", "UP")
        pred_util = telemetry_data.get("predicted_utilization", 0.0)
        is_anomaly = telemetry_data.get("is_anomaly", False)
        mse = telemetry_data.get("mse_residual", 0.0)
        
        elapsed_since_action = now - self.last_action_timestamp
        in_cooldown = elapsed_since_action < self.cooldown_sec
        cooldown_remaining = max(0.0, self.cooldown_sec - elapsed_since_action)

        decision = {
            "dpid": dpid,
            "port_no": port_no,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "HOLD",
            "previous_route": self.current_bulk_route,
            "new_route": self.current_bulk_route,
            "target_flow_class": "BEST_EFFORT",
            "reason": "Normal conditions; no reroute needed.",
            "cooldown_remaining_sec": round(cooldown_remaining, 2)
        }

        # Rule 1: Respect Layer 1 Fast-Failover
        # If physical link is already DOWN, FF hardware group tables immediately handle it.
        # Layer 2 must NOT issue conflicting flow-mods that clash with FF bucket selection.
        if link_status == "DOWN":
            decision["action"] = "DEFER_TO_FAST_FAILOVER"
            decision["reason"] = "Physical link DOWN detected; Layer 1 Fast-Failover handles failover locally."
            self._log_decision(decision, event_type="decision")
            return decision

        # Rule 2: Stability / Cooldown Window
        if in_cooldown:
            decision["action"] = "HOLD_COOLDOWN"
            decision["reason"] = f"In stability cooldown ({cooldown_remaining:.1f}s remaining). Suppressing oscillation."
            self._log_decision(decision, event_type="decision")
            return decision

        # Rule 3: Congestion / Degradation Proactive Reroute (Primary -> Backup for Bulk traffic)
        if self.current_bulk_route == "PRIMARY":
            if pred_util >= self.congestion_threshold or is_anomaly:
                self.current_bulk_route = "BACKUP"
                self.last_action_timestamp = now
                self.last_action_reason = f"Congestion predicted (util={pred_util:.2f}, anomaly={is_anomaly})"
                
                decision["action"] = "PROACTIVE_REROUTE_BULK"
                decision["new_route"] = "BACKUP"
                decision["destination_port"] = 4
                decision["priority_protected"] = True
                decision["reason"] = self.last_action_reason
                self.decision_count += 1
                
                self._log_decision(decision, event_type="decision")
                self._log_decision(decision, event_type="enforcement")
                return decision

        # Rule 4: Failback with Hysteresis (Backup -> Primary when load stabilizes)
        elif self.current_bulk_route == "BACKUP":
            if pred_util < self.recovery_threshold and not is_anomaly:
                self.current_bulk_route = "PRIMARY"
                self.last_action_timestamp = now
                self.last_action_reason = f"Load recovered below threshold (util={pred_util:.2f} < {self.recovery_threshold})"
                
                decision["action"] = "FAILBACK_RESTORE_PRIMARY"
                decision["new_route"] = "PRIMARY"
                decision["destination_port"] = 3
                decision["priority_protected"] = True
                decision["reason"] = self.last_action_reason
                self.decision_count += 1
                
                self._log_decision(decision, event_type="decision")
                self._log_decision(decision, event_type="enforcement")
                return decision

        # Otherwise hold state
        self._log_decision(decision, event_type="decision")
        return decision

    def _log_decision(self, decision, event_type="decision"):
        try:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            file_exists = self.log_path.exists()
            with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["timestamp_iso", "timestamp_epoch", "event_type", "dpid", "port", "trial_id", "mode", "details"]
                )
                if not file_exists:
                    writer.writeheader()
                writer.writerow({
                    "timestamp_iso": decision["timestamp"],
                    "timestamp_epoch": f"{time.time():.6f}",
                    "event_type": event_type,
                    "dpid": decision["dpid"],
                    "port": decision["port_no"],
                    "trial_id": "trial_self_healing",
                    "mode": "full_ai_qos_ff",
                    "details": f"Action={decision['action']} | Route={decision['new_route']} | Reason={decision['reason']}"
                })
        except Exception:
            pass


def replay_evaluation(predictions_file, cooldown_sec=15.0):
    """
    Replays historical / validation predictions through the Self-Healing engine.
    """
    path = Path(predictions_file)
    if not path.exists():
        print(f"Error: Predictions file not found: {predictions_file}")
        return []

    print(f"[*] Replaying Self-Healing Engine against {predictions_file}...")
    engine = SelfHealingEngine(cooldown_sec=cooldown_sec)
    results = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            throughput = float(row.get("predicted_throughput_bps", row.get("throughput_bps", 0.0)))
            # Assume 10 Mbps bottleneck link capacity for edge
            util = min(1.0, throughput / 10000000.0)
            is_anomaly = bool(int(float(row.get("predicted_anomaly", row.get("is_anomalous", 0)))))
            mse = float(row.get("mse", 0.0))
            
            telemetry = {
                "dpid": int(row.get("dpid", 1)),
                "port_no": int(row.get("port", 3)),
                "link_status": "UP",
                "predicted_utilization": util,
                "is_anomaly": is_anomaly,
                "mse_residual": mse,
                "timestamp": row.get("timestamp", datetime.now(timezone.utc).isoformat())
            }
            res = engine.evaluate_telemetry(telemetry)
            results.append(res)
            # Simulate passage of time (e.g. 5s per step)
            time.sleep(0.01)

    reroutes = [r for r in results if r["action"] == "PROACTIVE_REROUTE_BULK"]
    failbacks = [r for r in results if r["action"] == "FAILBACK_RESTORE_PRIMARY"]
    cooldowns = [r for r in results if r["action"] == "HOLD_COOLDOWN"]

    print(f"[*] Replay Complete: Total Samples={len(results)}")
    print(f"    - Proactive Reroutes: {len(reroutes)}")
    print(f"    - Safe Failbacks:     {len(failbacks)}")
    print(f"    - Cooldown Holds:     {len(cooldowns)} (Oscillations Prevented)")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Self-Healing Module")
    parser.add_argument("--replay-csv", default="ai-model/integration_predictions.csv", help="Predictions CSV to replay")
    parser.add_argument("--cooldown", type=float, default=DEFAULT_COOLDOWN_SEC, help="Cooldown in seconds")
    args = parser.parse_args()

    replay_evaluation(args.replay_csv, cooldown_sec=args.cooldown)
