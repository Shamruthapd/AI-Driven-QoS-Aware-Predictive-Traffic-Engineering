import sys
from pathlib import Path

from os_ken.base import app_manager


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main():
    applications = [
        "os_ken.controller.ofp_handler",
        "controller.app",
	"controller.telemetry",
        "controller.monitor",
    ]

    app_manager.AppManager.run_apps(applications)


if __name__ == "__main__":
    main()
