# XC9022 2.8-inch display on Bookworm ARM64

The supplied XC9022 instructions select `LCD28-show` from
<https://github.com/goodtft/LCD-show>. Upstream calls this display type
**2.8-inch MPI2801**; the XC9022 retail model mapping comes from the instructions
you supplied, not a tested hardware identification in this project.

## Why the old install instructions need care

Inspected upstream revision: `a36c00a55e11f0de3b4be0e66f0a2cec47076e23`.
`LCD28-show`, `system_backup.sh` and `system_config.sh` do considerably more
than install a library. They replace boot configuration from templates, change
X11 configuration, alter startup files, select an X11/console login workflow,
install a legacy `rpi-fbcp` helper, configure a `tft9341` overlay, and reboot.
`system_config.sh` links `/boot/config.txt` to `/boot/firmware/config.txt` when
the latter exists. The overlay copy commands still target `/boot/overlays`.
There are string-based Debian-version comparisons, which cannot be relied on
as numeric version comparisons (for example 12.9 versus 12.10).

Although upstream includes ARM64 branches, that alone does not establish
compatibility with your Bookworm kernel, boot layout, or XC9022 revision. The
legacy framebuffer helper is an additional compatibility concern on a modern
64-bit graphics stack. This project has **not** run the script on a Pi and
does not automatically run or patch it.

## Prepare and inspect on the Pi

1. Shut down and remove power before attaching the TFT to the GPIO header.
   Follow the XC9022 manual's orientation/power instructions.
2. Keep a working SSH connection and HDMI fallback. Record the Pi's address.
3. Make a full SD-card backup/image before changing the display stack. The
   vendor's own backup routine does not replace a full card backup, and removes
   some existing configuration while it runs.
4. Record `uname -a`, `uname -m`, `cat /etc/os-release` and
   `ls -ld /boot/overlays /boot/firmware/overlays`. Keep copies of
   `/boot/firmware/config.txt`, `/boot/firmware/cmdline.txt` and your X11
   settings outside the card as well. Do not publish files containing credentials.

Download and inspect the vendor code without installing it:

```sh
sudo apt-get install -y git
git clone https://github.com/goodtft/LCD-show.git
cd LCD-show
git rev-parse HEAD
less LCD28-show
less system_config.sh
less system_backup.sh
```

For a USB transfer, copy/unzip the repository archive into your home directory
and enter its extracted folder (`LCD-show-master` for a typical GitHub ZIP).
The URL in the supplied text has a typo: use the URL above, without `[`. The
permission command is `chmod +x LCD28-show`, not `chmod +x #-show`.

## Vendor installation command (conditional)

Only after confirming a supported Bookworm ARM64 procedure for your display
revision with the supplier, and preparing recovery access, their command is:

```sh
cd ~/LCD-show  # or your extracted vendor folder
chmod +x LCD28-show
sudo ./LCD28-show
```

**This changes system configuration and automatically reboots.** Do not assume
that changing `/boot` paths or disabling KMS by hand is a complete compatibility
fix. If the supplier's driver requires a different OS/kernel, use their supported
combination or obtain a modern supported driver; the Wi-Fi app itself can run
on Bookworm independently of the TFT driver.

Once the desktop is working on the TFT, verify touch at all four corners and
follow the supplier's calibration/rotation procedure for that driver and session.
If the script changed the machine to console login, select desktop login in
`sudo raspi-config` after confirming the display stack supports it. Log in to
the desktop before launching the app or enabling its XDG autostart.

## Recover

If the screen is blank, SSH in or use HDMI to inspect boot and display logs.
Use your known-good configuration/card image to recover; do not blindly rerun
the vendor script, since it refreshes its backup directory. The app's install
script never changes display configuration, so removing the app cannot undo
vendor driver changes.
