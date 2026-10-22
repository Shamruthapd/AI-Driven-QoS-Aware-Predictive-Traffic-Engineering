"""Small deterministic tests for Member 4's Week 9 runtime safety helpers."""
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-model"))
import ai_loop  # noqa: E402


class RuntimeHelperTests(unittest.TestCase):
    def test_finite_number_rejects_nan_and_infinity(self):
        self.assertEqual(ai_loop.finite_number("2.5"), 2.5)
        self.assertIsNone(ai_loop.finite_number("nan"))
        self.assertIsNone(ai_loop.finite_number(float("inf")))
        self.assertIsNone(ai_loop.finite_number("bad"))

    def test_calibration_clips_to_zero_and_one_hundred(self):
        self.assertEqual(ai_loop.calibrated_utilization(5_000_000, 10_000_000), 50.0)
        self.assertEqual(ai_loop.calibrated_utilization(-2, 10_000_000), 0.0)
        self.assertEqual(ai_loop.calibrated_utilization(20_000_000, 10_000_000), 100.0)
        with self.assertRaises(ValueError):
            ai_loop.calibrated_utilization(1, 0)

    def test_config_parses_simple_yaml_without_pyyaml(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.yaml"
            path.write_text("polling_interval_seconds: 2\nuse_model: false\noutput_jsonl: 'x.jsonl'\n", encoding="utf-8")
            config = ai_loop.load_config(path)
            self.assertEqual(config["polling_interval_seconds"], 2)
            self.assertIs(config["use_model"], False)
            self.assertEqual(config["output_jsonl"], "x.jsonl")

    def test_missing_csv_returns_no_data_reason(self):
        rows, reason = ai_loop.read_latest_window(Path("/file/that/does/not/exist.csv"), 5, 10, 15)
        self.assertEqual(rows, [])
        self.assertEqual(reason, "telemetry_file_missing")

    def test_latest_window_accepts_fresh_contiguous_rows(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "telemetry.csv"
            now = datetime.now(timezone.utc)
            rows = []
            for index in range(5):
                row = {"timestamp": (now - pd.Timedelta(seconds=4-index)).isoformat(), "dpid": 1, "port": 2}
                row.update({feature: 100 + index for feature in ai_loop.FEATURE_COLUMNS})
                rows.append(row)
            pd.DataFrame(rows).to_csv(path, index=False)
            window, reason = ai_loop.read_latest_window(path, 5, 10, 15, now=now)
            self.assertIsNone(reason)
            self.assertEqual(len(window), 5)

    def test_latest_window_rejects_gap_and_does_not_bridge_it(self):
        import pandas as pd
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "telemetry.csv"
            now = datetime.now(timezone.utc)
            offsets = [20, 19, 18, 6, 5]
            rows = []
            for index, offset in enumerate(offsets):
                row = {"timestamp": (now - pd.Timedelta(seconds=offset)).isoformat(), "dpid": 1, "port": 2}
                row.update({feature: 100 + index for feature in ai_loop.FEATURE_COLUMNS})
                rows.append(row)
            pd.DataFrame(rows).to_csv(path, index=False)
            window, reason = ai_loop.read_latest_window(path, 5, 10, 30, now=now)
            self.assertEqual(window, [])
            self.assertEqual(reason, "telemetry_gap_or_nonmonotonic_timestamp")

    def test_jsonl_writer_never_allows_nan(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "out.jsonl"
            ai_loop.append_jsonl(path, {"status": "no_data", "metric": None})
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsNone(record["metric"])
            with self.assertRaises(ValueError):
                ai_loop.append_jsonl(path, {"metric": math.nan})


if __name__ == "__main__":
    unittest.main(verbosity=2)
