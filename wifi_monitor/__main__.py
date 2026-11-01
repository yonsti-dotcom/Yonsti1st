import argparse
import json
import sys

from .network import DemoNetworkManager, MonitorError, NetworkManager


def main():
    parser = argparse.ArgumentParser(description="Pi touchscreen Wi-Fi monitor")
    parser.add_argument("--demo", action="store_true", help="show simulated networks")
    parser.add_argument("--once", action="store_true", help="print one JSON reading without a display")
    parser.add_argument("--interface", help="Wi-Fi device (default: connected or first Wi-Fi adapter)")
    parser.add_argument("--fullscreen", action="store_true")
    parser.add_argument("--interval", type=int, default=10, help="cached status refresh seconds (minimum 3)")
    args = parser.parse_args()
    backend = DemoNetworkManager() if args.demo else NetworkManager(args.interface)
    if args.once:
        try:
            print(json.dumps(backend.read(rescan=True).to_dict(), indent=2))
        except MonitorError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0
    try:
        from .ui import Dashboard
        Dashboard(backend, args.fullscreen, max(3, args.interval), args.demo).run()
    except ImportError as exc:
        print(f"GUI dependency unavailable: {exc}. Install python3-tk.", file=sys.stderr)
        return 1
    except Exception as exc:
        # TclError also covers starting the GUI from an SSH session without a display.
        import tkinter
        if not isinstance(exc, tkinter.TclError):
            raise
        print(f"Display unavailable: {exc}. Run from the Pi desktop or use --once.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
