#!/usr/bin/env python3
"""
Unit tests for Week 10 Self-Healing Engine, Mode Switcher, and AI Bridge.
"""

import unittest
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ai-model"))

from controller.modes import ModeManager, ControllerMode
from self_healing_module import SelfHealingEngine


class TestSelfHealingAndModes(unittest.TestCase):
    def test_mode_manager(self):
        mm = ModeManager(default_mode=ControllerMode.FULL_AI_QOS_FF)
        self.assertTrue(mm.should_use_fast_failover())
        self.assertTrue(mm.should_use_qos_queues())
        self.assertTrue(mm.should_use_ai_prediction())

        mm.set_mode(ControllerMode.BASELINE_SHORTEST_PATH)
        self.assertFalse(mm.should_use_fast_failover())
        self.assertFalse(mm.should_use_qos_queues())
        self.assertFalse(mm.should_use_ai_prediction())

        mm.set_mode(ControllerMode.REACTIVE)
        self.assertFalse(mm.should_use_fast_failover())
        self.assertTrue(mm.should_use_qos_queues())
        self.assertFalse(mm.should_use_ai_prediction())

    def test_self_healing_cooldown_and_precedence(self):
        engine = SelfHealingEngine(cooldown_sec=10.0, congestion_threshold=0.80, recovery_threshold=0.50)

        # 1. Normal state
        res1 = engine.evaluate_telemetry({
            "dpid": 1, "port_no": 3, "link_status": "UP",
            "predicted_utilization": 0.40, "is_anomaly": False
        })
        self.assertEqual(res1["action"], "HOLD")

        # 2. Predictive congestion triggers proactive reroute of bulk traffic
        res2 = engine.evaluate_telemetry({
            "dpid": 1, "port_no": 3, "link_status": "UP",
            "predicted_utilization": 0.90, "is_anomaly": True
        })
        self.assertEqual(res2["action"], "PROACTIVE_REROUTE_BULK")
        self.assertEqual(res2["new_route"], "BACKUP")

        # 3. Subsequent reading within cooldown must HOLD
        res3 = engine.evaluate_telemetry({
            "dpid": 1, "port_no": 3, "link_status": "UP",
            "predicted_utilization": 0.85, "is_anomaly": True
        })
        self.assertEqual(res3["action"], "HOLD_COOLDOWN")

        # 4. Hard link failure MUST defer to Fast-Failover
        res4 = engine.evaluate_telemetry({
            "dpid": 1, "port_no": 3, "link_status": "DOWN",
            "predicted_utilization": 0.0, "is_anomaly": False
        })
        self.assertEqual(res4["action"], "DEFER_TO_FAST_FAILOVER")


if __name__ == "__main__":
    unittest.main()
