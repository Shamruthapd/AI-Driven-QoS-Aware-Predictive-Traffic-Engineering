"""Deterministic tests for Week 9 evaluation parsing and summary output."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("evaluate", ROOT / "scripts" / "evaluate.py")
evaluate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(evaluate)


class EvaluationTests(unittest.TestCase):
    def test_week8_summary_reproduces_documented_tcp_change(self):
        fixture = ROOT / "tests" / "fixtures" / "week8_qos_on_vs_off_measurements.csv"
        with tempfile.TemporaryDirectory() as temp:
            output = evaluate.reproduce_week8(fixture, Path(temp))
            import pandas as pd
            frame = pd.read_csv(output)
            tcp = frame[frame["flow_type"] == "Bulk_TCP_Data"].iloc[0]
            self.assertAlmostEqual(float(tcp["throughput_change_pct"]), -68.1666666, places=4)
            self.assertEqual(tcp["evidence_status"], "recomputed_from_summary_csv")

    def test_ping_parser_calculates_latency_loss_and_variation(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "reactive_S3_trial_01_ping.log"
            path.write_text(
                "64 bytes from x: icmp_seq=1 ttl=64 time=2.0 ms\n"
                "64 bytes from x: icmp_seq=2 ttl=64 time=4.0 ms\n"
                "10 packets transmitted, 9 received, 10% packet loss\n",
                encoding="utf-8",
            )
            result = evaluate.parse_one(path)
            self.assertTrue(result["valid"])
            self.assertEqual(result["scenario"], "S3")
            self.assertAlmostEqual(result["latency_ms_mean"], 3.0)
            self.assertAlmostEqual(result["packet_loss_pct"], 10.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
