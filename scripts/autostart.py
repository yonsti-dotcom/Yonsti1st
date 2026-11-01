#!/usr/bin/env python3
"""Opt-in XDG desktop autostart; run as the Pi desktop user, not root."""
import argparse
import os
from pathlib import Path
import shlex


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--remove", action="store_true")
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error("run as your normal desktop user, without sudo")
    repo = Path(__file__).resolve().parent.parent
    config = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    destination = config / "autostart" / "yonsti-wifi-monitor.desktop"
    if args.remove:
        destination.unlink(missing_ok=True)
        (config / "yonsti-wifi-monitor" / "start.sh").unlink(missing_ok=True)
        print("Autostart removed")
        return
    if destination.exists():
        parser.error(f"{destination} already exists; remove it first with --remove")
    # Desktop Entry Exec escaping is distinct from shell quoting. Use a launcher
    # so paths containing spaces, quotes and percent signs remain unambiguous.
    launcher = config / "yonsti-wifi-monitor" / "start.sh"
    launcher.parent.mkdir(parents=True, exist_ok=True)
    if launcher.exists():
        parser.error(f"{launcher} already exists; preserve or remove it first")
    launcher.write_text("#!/bin/sh\nset -eu\ncd " + shlex.quote(str(repo)) +
                        "\nexec /usr/bin/python3 -m wifi_monitor --fullscreen\n")
    launcher.chmod(0o700)
    escaped = str(launcher).replace("\\", "\\\\\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$").replace("%", "%%")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("[Desktop Entry]\nType=Application\nName=Pi Wi-Fi Monitor\n"
                           f'Exec="{escaped}"\nTerminal=false\n')
    print(f"Created {destination}; starts after your next desktop login")


if __name__ == "__main__":
    main()
