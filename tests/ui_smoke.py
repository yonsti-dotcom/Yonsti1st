"""Run with: xvfb-run -a python3 tests/ui_smoke.py (from the repository)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wifi_monitor.network import DemoNetworkManager
from wifi_monitor.ui import Dashboard

app = Dashboard(DemoNetworkManager(), interval=3, demo=True)
app.root.update()
app.refresh(True)


def check():
    try:
        assert app.snapshot is not None, "background reading did not complete"
        assert app.snapshot.networks[0].ssid == "Home Wi-Fi"
        assert not app.busy
        assert app.history[-1] == 82
        for tab in ("Status", "Networks", "Channels"):
            app.select(tab)
            app.root.update()
            assert app.canvas.find_all(), f"{tab} did not render"
        app.page = 100
        app.draw()
        assert app.page < 100, "pagination was not clamped"
        app.error = "Wi-Fi unavailable"
        app.draw()
        assert any(app.canvas.itemcget(item, "text") == "Wi-Fi unavailable"
                   for item in app.canvas.find_all())
        app.error = ""
        app.root.geometry("480x360")
        app.root.update()
        app.select("Status")
        print("UI smoke passed: 320x240/480x360, async read, tabs, paging, error display")
    except BaseException:
        app.root.destroy()
        raise
    app.root.destroy()


# Tk callback exceptions otherwise print without failing the process.
def fail(exc_type, value, traceback):
    sys.excepthook(exc_type, value, traceback)
    app.root.destroy()
    sys.exit(1)


app.root.report_callback_exception = fail
app.root.after(1000, check)
app.run()
