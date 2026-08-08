"""Render VerbaMind GUI offscreen and capture screenshot for visual verification."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from verbamind.gui.windows.main_window import MainWindow

app = QApplication([])
window = MainWindow()
window.resize(1000, 660)
window.show()

app.processEvents()

out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
os.makedirs(out_dir, exist_ok=True)

# Capture each page
from verbamind.gui.widgets.sidebar import Sidebar

sidebar = window.findChild(Sidebar, "sidebar")
for i in range(sidebar.count()):
    sidebar.setCurrentRow(i)
    app.processEvents()
    raw = sidebar.item(i).text()
    name = "".join(c for c in raw if c.isalnum() or c in "_ ").replace(" ", "_").strip().strip("_")
    pixmap = window.grab()
    path = os.path.join(out_dir, f"page_{i}_{name}.png")
    pixmap.save(path)
    print(f"Saved: {path}")

# Small window test — verify content scrolls (not clipped)
window.resize(700, 480)
app.processEvents()
pixmap = window.grab()
path = os.path.join(out_dir, "small_window_700x480.png")
pixmap.save(path)
print(f"Saved: {path}")

window.close()
print("Done")
