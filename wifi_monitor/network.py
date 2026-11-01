"""Read NetworkManager status without changing connections or radio modes."""

from dataclasses import asdict, dataclass, field
import os
import subprocess


class MonitorError(RuntimeError):
    pass


def split_fields(line):
    """Decode nmcli's escaped terse fields, including colons in SSIDs/BSSIDs."""
    fields, value, escaped = [], [], False
    for char in line:
        if escaped:
            value.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(value))
            value = []
        else:
            value.append(char)
    if escaped:
        value.append("\\")
    return fields + ["".join(value)]


@dataclass
class AccessPoint:
    active: bool
    ssid: str
    bssid: str
    channel: str
    signal: int
    security: str


@dataclass
class Snapshot:
    interface: str
    state: str
    address: str = ""
    gateway: str = ""
    networks: list[AccessPoint] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class NetworkManager:
    def __init__(self, interface=None):
        self.interface = interface

    def command(self, *args):
        try:
            result = subprocess.run(
                ["nmcli", "--terse", "--escape", "yes", "--colors", "no", *args],
                capture_output=True, text=True, timeout=20,
                env={**os.environ, "LC_ALL": "C"},
            )
        except FileNotFoundError as exc:
            raise MonitorError("nmcli missing: install network-manager") from exc
        except subprocess.TimeoutExpired as exc:
            raise MonitorError("NetworkManager request timed out") from exc
        if result.returncode:
            raise MonitorError(result.stderr.strip() or "NetworkManager request failed")
        return result.stdout

    def read(self, rescan=False):
        devices = [split_fields(line) for line in self.command(
            "--fields", "DEVICE,TYPE,STATE", "device", "status").splitlines()]
        wifi = [row for row in devices if len(row) == 3 and row[1] == "wifi"]
        if not wifi:
            raise MonitorError("No Wi-Fi adapter found; check NetworkManager and rfkill")
        selected = next((row for row in wifi if row[0] == self.interface), None)
        if self.interface and selected is None:
            raise MonitorError(f"Wi-Fi adapter {self.interface} not found")
        selected = selected or next((row for row in wifi if row[2] == "connected"), wifi[0])
        interface, _, state = selected
        details = {}
        for line in self.command("--fields", "IP4.ADDRESS,IP4.GATEWAY", "device", "show", interface).splitlines():
            row = split_fields(line)
            if len(row) >= 2:
                details[row[0]] = row[1]
        networks = []
        for line in self.command(
            "--fields", "IN-USE,SSID,BSSID,CHAN,SIGNAL,SECURITY", "device", "wifi", "list",
            "ifname", interface, "--rescan", "yes" if rescan else "no",
        ).splitlines():
            row = split_fields(line)
            if len(row) != 6:
                continue
            active, ssid, bssid, channel, signal, security = row
            try:
                quality = max(0, min(100, int(signal)))
            except ValueError:
                continue
            networks.append(AccessPoint(active == "*", ssid or "<hidden>", bssid,
                                        channel, quality, security or "Open"))
        networks.sort(key=lambda ap: (not ap.active, -ap.signal, ap.ssid))
        return Snapshot(interface, state, details.get("IP4.ADDRESS[1]", ""),
                        details.get("IP4.GATEWAY", ""), networks)


class DemoNetworkManager:
    def read(self, rescan=False):
        return Snapshot("wlan0", "connected", "192.0.2.10/24", "192.0.2.1", [
            AccessPoint(True, "Home Wi-Fi", "02:00:00:00:00:01", "6", 82, "WPA2"),
            AccessPoint(False, "Guest", "02:00:00:00:00:02", "11", 56, "WPA2"),
            AccessPoint(False, "Workshop 5GHz", "02:00:00:00:00:03", "36", 43, "WPA3"),
            AccessPoint(False, "<hidden>", "02:00:00:00:00:04", "1", 27, "WPA2"),
        ])
