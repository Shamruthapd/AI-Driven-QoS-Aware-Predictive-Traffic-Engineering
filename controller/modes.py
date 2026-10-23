"""
Operation Mode Manager for SDN Controller.
Provides seamless switching between the three evaluated operational modes:
1. baseline_shortest_path: Static shortest-path forwarding; no AI, no QoS queues, no Fast-Failover.
2. reactive: Controller-driven reroute initiated only after receiving OFPPortStatus event.
3. full_ai_qos_ff: Full proactive AI-driven QoS traffic engineering with switch-local Fast-Failover.
"""

import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


class ControllerMode:
    BASELINE_SHORTEST_PATH = "baseline_shortest_path"
    REACTIVE = "reactive"
    FULL_AI_QOS_FF = "full_ai_qos_ff"

    ALL_MODES = [BASELINE_SHORTEST_PATH, REACTIVE, FULL_AI_QOS_FF]


class ModeManager:
    def __init__(self, default_mode=ControllerMode.FULL_AI_QOS_FF, timelines_dir="data/results/week11_controller_timelines"):
        self.active_mode = default_mode
        self.timelines_dir = Path(timelines_dir)
        self.timelines_dir.mkdir(parents=True, exist_ok=True)
        self.current_trial_id = "trial_000"
        self.trial_events = []

    def set_mode(self, mode_str, trial_id=None):
        if mode_str not in ControllerMode.ALL_MODES:
            raise ValueError(f"Unknown mode: {mode_str}. Must be one of {ControllerMode.ALL_MODES}")
        self.active_mode = mode_str
        if trial_id:
            self.current_trial_id = trial_id
            self.trial_events = []
        print(f"[*] Operation Mode switched to: {self.active_mode} (Trial: {self.current_trial_id})")

    def log_trial_event(self, event_type, details=""):
        now_iso = datetime.now(timezone.utc).isoformat()
        epoch_ts = time.time()
        record = {
            "trial_id": self.current_trial_id,
            "mode": self.active_mode,
            "timestamp_iso": now_iso,
            "timestamp_epoch": f"{epoch_ts:.6f}",
            "event_type": event_type,
            "details": details
        }
        self.trial_events.append(record)
        return record

    def export_timeline(self):
        """
        Exports per-trial timeline covering controller-side view of the experiment.
        """
        filename = f"{self.current_trial_id}_{self.active_mode}_timeline.csv"
        out_path = self.timelines_dir / filename
        fieldnames = ["trial_id", "mode", "timestamp_iso", "timestamp_epoch", "event_type", "details"]

        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for ev in self.trial_events:
                writer.writerow(ev)
        print(f"[+] Exported trial timeline: {out_path} ({len(self.trial_events)} events)")
        return out_path

    def should_use_fast_failover(self):
        return self.active_mode == ControllerMode.FULL_AI_QOS_FF

    def should_use_qos_queues(self):
        return self.active_mode in (ControllerMode.REACTIVE, ControllerMode.FULL_AI_QOS_FF)

    def should_use_ai_prediction(self):
        return self.active_mode == ControllerMode.FULL_AI_QOS_FF

    def handle_port_down_reactive(self, dpid, port_no, reroute_callback):
        """
        In Reactive mode: Upon receiving port down, controller must reactively compute
        and install new flows to reroute traffic.
        """
        if self.active_mode == ControllerMode.REACTIVE:
            self.log_trial_event("REACTIVE_TRIGGER_DETECTED", f"DPID={dpid} Port={port_no} DOWN")
            t_start = time.time()
            if reroute_callback:
                reroute_callback(dpid, port_no)
            t_end = time.time()
            self.log_trial_event("REACTIVE_FLOW_MODS_INSTALLED", f"Rerouted via controller in {(t_end - t_start)*1000:.2f}ms")


if __name__ == "__main__":
    mm = ModeManager()
    mm.set_mode("full_ai_qos_ff", trial_id="test_trial_01")
    mm.log_trial_event("TRIAL_START", "Scenario S3 initialized")
    mm.log_trial_event("PORT_DOWN", "s1-eth3 link down detected")
    mm.log_trial_event("FF_TRIGGERED", "Switch hardware selected backup bucket in 40ms")
    mm.log_trial_event("TRIAL_END", "Completed")
    mm.export_timeline()
