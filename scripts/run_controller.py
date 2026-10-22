
import logging
import signal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from os_ken.base import app_manager

APPLICATIONS = [
    "os_ken.controller.ofp_handler",
    "controller.app",
    "controller.telemetry",
    "controller.monitor",
]

def patch_hub_thread_kill():
    from os_ken.lib import hub

    thread_cls = getattr(hub, "HubThread", None)
    if thread_cls is not None and not hasattr(thread_cls, "kill"):
        thread_cls.kill = lambda self: self.join(timeout=1)

def main():
    (PROJECT_ROOT / "logs").mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                PROJECT_ROOT / "logs" / "controller.log",
                encoding="utf-8",
            ),
        ],
        force=True,
    )

    logging.getLogger("os_ken").setLevel(logging.INFO)

    print("[controller] Starting OS-Ken; press Ctrl+C to stop.", flush=True)

    patch_hub_thread_kill()

    try:
        app_manager.AppManager.run_apps(APPLICATIONS)
    except KeyboardInterrupt:
        print("[controller] Stopped by user.", flush=True)

if __name__ == "__main__":
    main()
