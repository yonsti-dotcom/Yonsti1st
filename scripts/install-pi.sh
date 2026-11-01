#!/bin/sh
# Run as your normal desktop user. Display drivers are deliberately separate.
set -eu
if [ "$(id -u)" -eq 0 ]; then
    echo "Run as your desktop user, without sudo; this script uses sudo for apt." >&2
    exit 1
fi
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
sudo apt-get update
sudo apt-get install -y python3 python3-tk network-manager
echo "Dependencies installed. No display, Wi-Fi, or boot settings were changed."
echo "From the desktop, run:"
printf 'cd "%s" && /usr/bin/python3 -m wifi_monitor --fullscreen\n' "$repo"
