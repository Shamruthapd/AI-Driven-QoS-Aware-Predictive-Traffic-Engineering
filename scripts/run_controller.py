import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path

from os_ken.base import app_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Matches config/settings.yaml -> logging.file
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "controller.log"

APPLICATIONS = [
    "os_ken.controller.ofp_handler",
    "controller.app",
    "controller.telemetry",
    "controller.monitor",
]


def setup_logging():
    """
    Make controller activity visible.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )

    logging.getLogger("os_ken").setLevel(logging.INFO)


def patch_native_hub_threads():
    """
    Workaround for the OS-Ken 4.2.1 native-hub shutdown bug.
    """
    from os_ken.lib import hub as os_ken_hub

    hub_thread_cls = getattr(os_ken_hub, "HubThread", None)
    if hub_thread_cls is None:
        return

    original_init = hub_thread_cls.__init__

    def daemon_thread_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.daemon = True

    hub_thread_cls.__init__ = daemon_thread_init


def install_signal_handlers():
    """
    Translate SIGTERM into KeyboardInterrupt.
    """
    def _sigterm_to_keyboard_interrupt(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)
    except (ValueError, OSError):
        pass


def _run_os_ken_apps(holder):
    """
    Execute the OS-Ken applications on a dedicated daemon thread.
    """
    try:
        app_manager.AppManager.run_apps(APPLICATIONS)
        holder["returned"] = True

    except KeyboardInterrupt:
        holder["interrupted"] = True

    except AttributeError as exc:
        if "has no attribute 'kill'" in str(exc):
            holder["interrupted"] = True
        else:
            holder["error"] = exc

    except BaseException as exc:
        holder["error"] = exc


def main():
    setup_logging()
    install_signal_handlers()
    patch_native_hub_threads()

    holder = {}

    runner = threading.Thread(
        target=_run_os_ken_apps,
        args=(holder,),
        name="os-ken-run-apps",
        daemon=True,
    )

    runner.start()

    try:
        while runner.is_alive():
            time.sleep(0.25)

    except KeyboardInterrupt:
        print(
            "\n[controller] Stopped by user (Ctrl+C/SIGTERM).",
            flush=True,
        )

        os._exit(130)

    if holder.get("error") is not None:
        raise holder["error"]

    if holder.get("interrupted"):
        print(
            "\n[controller] OS-Ken apps stopped.",
            flush=True,
        )
        return

    print(
        "[controller] run_apps returned; all app services stopped.",
        flush=True,
    )


if __name__ == "__main__":
    main()
