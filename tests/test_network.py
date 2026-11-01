import subprocess
import unittest
from unittest.mock import patch

from wifi_monitor.network import MonitorError, NetworkManager, split_fields


class NetworkTests(unittest.TestCase):
    def test_escaped_ssid_and_bssid(self):
        self.assertEqual(split_fields(r"Cafe\:west:back\\slash:aa\:bb:"),
                         ["Cafe:west", "back\\slash", "aa:bb", ""])

    @patch("wifi_monitor.network.subprocess.run")
    def test_complete_read_with_connected_adapter_and_multiple_addresses(self, run):
        run.side_effect = [
            subprocess.CompletedProcess([], 0, "wlan1:wifi:disconnected\nwlan0:wifi:connected\n"),
            subprocess.CompletedProcess([], 0, "IP4.ADDRESS[1]:192.0.2.10/24\nIP4.ADDRESS[2]:198.51.100.5/24\nIP4.GATEWAY:192.0.2.1\n"),
            subprocess.CompletedProcess([], 0, " :Other:02\\:00\\:00\\:00\\:00\\:02:36:99:WPA3\n".lstrip() +
                "*:Cafe\\:west:02\\:00\\:00\\:00\\:00\\:01:6:80:WPA2\n" +
                ":hidden:02\\:00:1:bad:WPA2\n"),
        ]
        snapshot = NetworkManager().read(True)
        self.assertEqual(snapshot.interface, "wlan0")
        self.assertEqual(snapshot.address, "192.0.2.10/24")
        self.assertEqual(snapshot.gateway, "192.0.2.1")
        self.assertEqual(len(snapshot.networks), 2)
        self.assertEqual(snapshot.networks[0].ssid, "Cafe:west")
        self.assertEqual(snapshot.networks[0].bssid, "02:00:00:00:00:01")
        self.assertTrue(snapshot.networks[0].active)
        self.assertIn("yes", run.call_args.args[0])
        self.assertEqual(run.call_args.kwargs["env"]["LC_ALL"], "C")

    @patch.object(NetworkManager, "command", return_value="eth0:ethernet:connected\n")
    def test_no_wifi(self, command):
        with self.assertRaisesRegex(MonitorError, "No Wi-Fi"):
            NetworkManager().read()

    @patch.object(NetworkManager, "command", return_value="wlan0:wifi:disconnected\n")
    def test_missing_requested_interface(self, command):
        with self.assertRaisesRegex(MonitorError, "wlan9 not found"):
            NetworkManager("wlan9").read()

    @patch("wifi_monitor.network.subprocess.run")
    def test_command_failures(self, run):
        for effect, message in [(FileNotFoundError(), "nmcli missing"),
                                (subprocess.TimeoutExpired("nmcli", 20), "timed out")]:
            with self.subTest(message=message):
                run.side_effect = effect
                with self.assertRaisesRegex(MonitorError, message):
                    NetworkManager().command("device")
        run.side_effect = None
        run.return_value = subprocess.CompletedProcess([], 10, "", "NetworkManager is not running")
        with self.assertRaisesRegex(MonitorError, "not running"):
            NetworkManager().command("device")

    @patch.object(NetworkManager, "command")
    def test_hidden_network_open_security_and_cached_refresh(self, command):
        command.side_effect = ["wlan0:wifi:disconnected\n", "IP4.GATEWAY:\n",
                               ": :02\\:00:1:120:\n".replace(": :", "::")]
        snapshot = NetworkManager().read()
        self.assertEqual(snapshot.networks[0].ssid, "<hidden>")
        self.assertEqual(snapshot.networks[0].security, "Open")
        self.assertEqual(snapshot.networks[0].signal, 100)
        self.assertEqual(command.call_args.args[-1], "no")


if __name__ == "__main__":
    unittest.main()
