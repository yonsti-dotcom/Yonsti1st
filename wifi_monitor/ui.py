"""Compact 320x240 layout. All NetworkManager work stays off the Tk event loop."""

from collections import Counter, deque
from datetime import datetime
import queue
import threading
import tkinter as tk

from .network import MonitorError

BG = "#101923"
FG = "#edf5ff"
MUTED = "#a4b6c9"
ACCENT = "#57ddac"


class Dashboard:
    def __init__(self, backend, fullscreen=False, interval=10, demo=False):
        self.backend, self.interval, self.demo = backend, interval, demo
        self.snapshot, self.error, self.updated = None, "", ""
        self.history = deque(maxlen=40)
        self.results = queue.Queue()
        self.busy, self.tab, self.page = False, "Status", 0
        self.root = tk.Tk()
        self.root.title("Pi Wi-Fi Monitor")
        self.root.geometry("320x240")
        self.root.minsize(320, 240)
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", fullscreen)
        self.root.bind("<Escape>", lambda event: self.root.attributes("-fullscreen", False))
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Configure>", lambda event: self.draw())
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x")
        tk.Label(header, text="WI-FI" + (" / DEMO" if demo else ""), bg=BG, fg=ACCENT,
                 font=("DejaVu Sans", 11, "bold")).pack(side="left", padx=7)
        self.scan_button = self.button(header, "Scan", lambda: self.refresh(True))
        self.scan_button.pack(side="right")
        self.button(header, "Quit", self.root.destroy).pack(side="right")
        tabs = tk.Frame(self.root, bg=BG)
        tabs.pack(fill="x")
        for name in ("Status", "Networks", "Channels"):
            self.button(tabs, name, lambda name=name: self.select(name)).pack(side="left", expand=True, fill="x")
        self.canvas = tk.Canvas(self.root, bg=BG, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.tap)
        self.root.after(100, self.poll)
        self.root.after(150, self.refresh)
        self.root.after(interval * 1000, self.periodic)

    def button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, bg="#243648", fg=FG,
                         activebackground="#36516a", activeforeground=FG,
                         font=("DejaVu Sans", 10), relief="flat", pady=7, takefocus=True)

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def select(self, name):
        self.tab, self.page = name, 0
        self.draw()

    def refresh(self, rescan=False):
        if self.busy:
            return
        self.busy = True
        self.scan_button.configure(state="disabled", text="...")
        def work():
            try:
                self.results.put((self.backend.read(rescan=rescan), ""))
            except MonitorError as exc:
                self.results.put((None, str(exc)))
            except Exception as exc:
                self.results.put((None, f"Read failed: {exc}"))
        threading.Thread(target=work, daemon=True).start()
        self.draw()

    def periodic(self):
        self.refresh()
        self.root.after(self.interval * 1000, self.periodic)

    def poll(self):
        try:
            snapshot, self.error = self.results.get_nowait()
        except queue.Empty:
            pass
        else:
            self.busy = False
            self.scan_button.configure(state="normal", text="Scan")
            if snapshot is not None:
                self.snapshot = snapshot
                self.updated = datetime.now().strftime("%H:%M:%S")
                active = next((ap for ap in snapshot.networks if ap.active), None)
                self.history.append(active.signal if active else None)
            self.draw()
        self.root.after(100, self.poll)

    def text(self, x, y, value, size=10, color=FG, **kwargs):
        self.canvas.create_text(x, y, text=value, anchor="nw", fill=color,
                                font=("DejaVu Sans", size), **kwargs)

    def draw(self):
        if not hasattr(self, "canvas"):
            return
        c = self.canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 320), max(c.winfo_height(), 130)
        if self.error:
            self.text(8, 8, self.error, color="#ffb779", width=w-16)
            self.text(8, h-22, "Tap Scan to retry", color=MUTED)
            return
        if self.snapshot is None:
            self.text(8, 10, "Reading Wi-Fi...", color=MUTED)
            return
        s = self.snapshot
        if self.tab == "Status":
            active = next((ap for ap in s.networks if ap.active), None)
            self.text(8, 4, active.ssid[:30] if active else s.state, 13)
            if active:
                self.text(8, 28, f"{active.signal}% quality   Ch {active.channel}   {active.security}", color=ACCENT)
            else:
                self.text(8, 28, "No connected access point", color=MUTED)
            self.text(8, 50, f"{s.interface} / {s.address or 'No IPv4 address'}")
            self.text(8, 70, f"Gateway: {s.gateway or '-'}", color=MUTED)
            # Plot quality history with gaps for disconnected samples.
            top, bottom = 96, h-25
            if bottom > top:
                c.create_line(8, bottom, w-8, bottom, fill="#36516a")
                points = list(self.history)
                if points and points[-1] is not None:
                    x = 8+(len(points)-1)*(w-16)/39
                    y = bottom-points[-1]*(bottom-top)/100
                    c.create_oval(x-2, y-2, x+2, y+2, fill=ACCENT, outline="")
                for i in range(1, len(points)):
                    if points[i-1] is not None and points[i] is not None:
                        c.create_line(8+(i-1)*(w-16)/39, bottom-points[i-1]*(bottom-top)/100,
                                      8+i*(w-16)/39, bottom-points[i]*(bottom-top)/100,
                                      fill=ACCENT, width=2)
            self.text(8, h-20, f"{'Reading...' if self.busy else 'Updated '+self.updated} / {len(s.networks)} APs", 9, MUTED)
        else:
            rows = max(1, (h-32)//36)
            if self.tab == "Networks":
                items = [(f"{'*' if ap.active else '-'} {ap.ssid[:22]}",
                          f"{ap.signal}%  ch {ap.channel}  {ap.security}") for ap in s.networks]
            else:
                counts = Counter(ap.channel for ap in s.networks)
                items = [(f"Channel {channel}", f"{count} visible AP{'s' if count != 1 else ''}")
                         for channel, count in sorted(counts.items(), key=lambda item: int(item[0]) if item[0].isdigit() else 0)]
            pages = max(1, (len(items)+rows-1)//rows)
            self.page = min(self.page, pages-1)
            for i, (title, detail) in enumerate(items[self.page*rows:(self.page+1)*rows]):
                self.text(8, 3+i*36, title, 10)
                self.text(16, 20+i*36, detail, 9, MUTED)
            if not items:
                self.text(8, 8, "No cached networks. Tap Scan.", color=MUTED)
            c.create_rectangle(0, h-30, w, h, fill="#243648", outline="")
            self.text(8, h-24, "< Back", 10)
            self.text(w/2-18, h-24, f"{self.page+1}/{pages}", 10)
            self.text(w-70, h-24, "Next >", 10)

    def tap(self, event):
        if self.tab != "Status" and event.y >= self.canvas.winfo_height()-30:
            self.page = max(0, self.page + (1 if event.x > self.canvas.winfo_width()/2 else -1))
            self.draw()

    def run(self):
        self.root.mainloop()
