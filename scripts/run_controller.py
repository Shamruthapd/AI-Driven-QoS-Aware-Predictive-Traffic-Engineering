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

    OS-Ken's default log level is WARNING, which hides the application
    INFO banners ("AI-QoS SDN Controller Started", Packet-In lines, ...)
    and makes the controller look unresponsive during normal operation.
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

    # Un-hold OS-Ken's own logger messages as well.
    logging.getLogger("os_ken").setLevel(logging.INFO)


def patch_native_hub_threads():
    """
    Workaround for the OS-Ken 4.2.1 native-hub shutdown bug.

    When the native hub (os_ken.lib.hub.HubThread, a threading.Thread
    subclass) is used, Ctrl+C inside run_apps() reaches its finally
    block:

        for t in services:
            t.kill()    # -> AttributeError: 'HubThread' object has
                        #    no attribute 'kill'

    The AttributeError aborts run_apps(), but the spawned application
    threads are NON-daemon, so the interpreter then blocks forever at
    exit trying to join them.  Marking every HubThread as daemon lets
    the process terminate cleanly once main() returns.  The raised
    AttributeError is classified as "interrupted" by
    _run_os_ken_apps() so no traceback is surfaced.

    Note: we deliberately do NOT add a working per-thread kill() -- the
    native hub's kill() is a documented no-op, so run_apps() would then
    hang forever in the following `hub.joinall(services)`.
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
    Translate SIGTERM into KeyboardInterrupt so that e.g.
    `timeout 60 python3 scripts/run_controller.py` stops the controller
    through the same clean shutdown path as Ctrl+C.
    """
    def _sigterm_to_keyboard_interrupt(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _sigterm_to_keyboard_interrupt)
    except (ValueError, OSError):
        # e.g. non-main thread context; SIGINT keeps its default handler
        pass


def _run_os_ken_apps(holder):
    """
    Execute the OS-Ken applications on a dedicated daemon thread.

    Outcome is recorded in ``holder`` so the main thread can decide how
    to terminate:
      * normal run_apps() return ......... holder["returned"] = True
      * OS-Ken 4.2.1 native-hub shutdown  . holder["interrupted"] = True
        AttributeError (t.kill on HubThread)
      * any other error ................... holder["error"] = <exc>
    """
    try:
        app_manager.AppManager.run_apps(APPLICATIONS)
        holder["returned"] = True
    except KeyboardInterrupt:
        holder["interrupted"] = True
    except AttributeError as exc:
        # OS-Ken 4.2.1 native-hub shutdown bug triggered by Ctrl+C:
        # "'HubThread' object has no attribute 'kill'".
        if "has no attribute 'kill'" in str(exc):
            holder["interrupted"] = True
        else:
            holder["error"] = exc
    except BaseException as exc:  # noqa: BLE001 - surfaced to main()
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
        # Keep the MAIN thread executing Python bytecode (sleep poll loop)
        # so Ctrl+C / SIGTERM are delivered and handled immediately.
        # If the main thread instead blocked inside os_ken's
        # hub.joinall() -> thread.join(), CPython may never deliver the
        # KeyboardInterrupt because the joined app threads never finish.
        while runner.is_alive():
            time.sleep(0.25)
    except KeyboardInterrupt:
        print("\n[controller] Stopped by user (Ctrl+C/SIGTERM).", flush=True)
        # The OS-Ken native hub cannot cleanly join or kill the app
        # threads (its kill() is a no-op on this hub), so a hard exit is
        # the only reliable graceful stop.  Exit code 130 = SIGINT.
        os._exit(130)

    # The runner thread ended on its own: surface any error, else finish.
    if holder.get("error") is not None:
        raise holder["error"]

    if holder.get("interrupted"):
        print("\n[controller] OS-Ken apps stopped.", flush=True)
        return

    # runner gone without interruption: run_apps() returned normally.
    print(
        "[controller] run_apps returned; all app services stopped.",
        flush=True,
    )


if __name__ == "__main__":
    main()
