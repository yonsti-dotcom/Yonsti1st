# Pi Wi-Fi Monitor

A touch dashboard for a **Raspberry Pi 4 running 64-bit Raspberry Pi OS
Bookworm**, designed for the XC9022 2.8-inch display in landscape orientation.
Works at 320×240 and larger desktop sizes. Uses Python's Tkinter and Bookworm's
NetworkManager; no pip dependencies or root privileges needed to run the app.

## What it shows

- **Status:** connected SSID, signal quality percentage, recent quality graph,
  channel, security, adapter, IPv4 address and gateway.
- **Networks:** visible access points with touch pagination.
- **Channels:** visible AP counts by channel. This is an AP count, not an RF
  interference or airtime measurement.
- **Scan:** requests a fresh Wi-Fi scan. Background status refreshes every ten
  seconds using NetworkManager's cache; NetworkManager may refresh that cache
  independently. Scans can briefly affect throughput on the built-in radio.

This monitors ordinary connection and scan information. It does not switch the
adapter into packet capture mode or disconnect devices. Signal percentage is
NetworkManager quality, not a calibrated dBm reading. No Internet service,
API key or remote telemetry is used.

## Install on the Pi

Start with Raspberry Pi OS **Bookworm 64-bit with Desktop** and a working Wi-Fi
connection. Enable SSH before working on the display. Lite needs a desktop/X
session installed separately; this application does not draw directly to a
framebuffer.

```sh
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/yonsti-dotcom/Yonsti1st.git
cd Yonsti1st
sh scripts/install-pi.sh
python3 -m wifi_monitor --once
```

The install script only installs dependencies. It does not enable radios,
replace networking configuration, install LCD drivers, or reboot. If you already
have this checkout, use it rather than cloning another copy.

Launch **from a terminal on the Pi desktop**, after the display is working:

```sh
cd ~/Yonsti1st
python3 -m wifi_monitor --fullscreen
```

Tap Status / Networks / Channels to change views; Back / Next page through lists.
Tap Quit to return to the desktop. Escape leaves fullscreen; F11 toggles it.
Use `--interface wlan1` to select a USB adapter, or `--interval 5` for a five-second
cached refresh. The default adapter is the connected Wi-Fi device, or the first
Wi-Fi device if none is connected. Scan errors are displayed with a retry button.

## XC9022 display and touch

See [the display setup guide](docs/xc9022-bookworm.md) **before** running
`LCD28-show`. The supplied vendor instructions point to
[goodtft/LCD-show](https://github.com/goodtft/LCD-show), but compatibility of the
XC9022 and its legacy framebuffer path with your current Bookworm kernel remains
unverified. The app does not depend on that specific driver: any working desktop
display/touch stack is sufficient. Physical display, touch calibration, ARM64
and real radio checks must be completed on the Pi.

## Start at desktop login (optional)

After checking fullscreen operation, run as your normal desktop user:

```sh
python3 scripts/autostart.py
```

This creates a launcher in `~/.config/yonsti-wifi-monitor/` and an XDG autostart
entry in `~/.config/autostart/`. Keep the checkout at its current path. Enable
desktop auto-login through `sudo raspi-config` if you want unattended startup
after boot. The application starts in the logged-in graphical session, not as
a root service. To undo:

```sh
python3 scripts/autostart.py --remove
```

## Develop and test without hardware

Use this existing checkout in cloud tasks; no additional Git worktree is needed.

```sh
python3 -m wifi_monitor --demo          # requires a graphical session
python3 -m wifi_monitor --demo --once   # deterministic JSON, no display needed
python3 -m unittest discover -s tests -v
# Optional GUI smoke check on Linux with Xvfb installed:
xvfb-run -a python3 tests/ui_smoke.py
```

The demo uses simulated networks and documentation-only IP addresses. The
unit tests exercise nmcli parsing and error handling with mocked command output;
they do not validate radio hardware. The GUI smoke test checks rendering,
background refresh, tabs, pagination and errors on a virtual display.

## Troubleshooting

- **No display / TclError:** launch inside the desktop session, not an ordinary
  SSH shell. Over SSH use `python3 -m wifi_monitor --once` to test networking.
- **No adapter / no networks:** check `nmcli device status`, `rfkill list`, and
  `systemctl status NetworkManager`. Resolve disabled Wi-Fi or unmanaged devices
  in the OS first. Check your Wi-Fi country setting in `sudo raspi-config`.
- **Scan not authorized:** test `nmcli device wifi list --rescan yes` as the
  same desktop user and check your session's NetworkManager/Polkit policy.
  Do not run the whole GUI as root to work around a policy issue.
- **Blank TFT or misaligned touch:** use SSH/HDMI and the display guide. This is
  independent of the Wi-Fi app; get the desktop and pointer working first.

### Pi acceptance checks

1. `uname -m` returns `aarch64`; `/etc/os-release` identifies Bookworm.
2. The XC9022 shows the desktop and touch reaches all four corners.
3. `python3 -m wifi_monitor --once` agrees with `nmcli device wifi list`.
4. Fullscreen fits the TFT; every tab, Scan, paging and Quit responds to touch.
5. Disconnect/reconnect Wi-Fi through the OS and check status recovers.
6. If autostart is enabled, reboot and verify it appears after desktop login.
