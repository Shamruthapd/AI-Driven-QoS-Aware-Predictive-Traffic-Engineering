#!/usr/bin/env python3
"""Run the telemetry processor in a continuous loop to feed the AI runtime."""
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import process_telemetry

_STOP = False


def _sig_handler(sig, frame):
    global _STOP
    _STOP = True


signal.signal(signal.SIGINT, _sig_handler)
signal.signal(signal.SIGTERM, _sig_handler)


def main():
    interval = 5.0
    print(f"[telemetry_processor] Started loop (interval={interval}s)", flush=True)
    while not _STOP:
        t0 = time.time()
        try:
            process_telemetry.main()
        except Exception as exc:
            print(f"[telemetry_processor] Error: {exc}", file=sys.stderr, flush=True)
        elapsed = time.time() - t0
        time.sleep(max(0.1, interval - elapsed))
    print("[telemetry_processor] Stopped.", flush=True)


if __name__ == "__main__":
    main()
