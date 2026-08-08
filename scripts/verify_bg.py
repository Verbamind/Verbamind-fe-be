"""Verify content background is white (not black) by sampling pixels."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from verbamind.gui.windows.main_window import MainWindow
from verbamind.gui.widgets.sidebar import Sidebar

app = QApplication([])
window = MainWindow()
window.resize(1000, 660)
window.show()
app.processEvents()

sidebar = window.findChild(Sidebar, "sidebar")

# Sample points in the content area (right of sidebar, in the page region)
# Content starts after sidebar (190px). Sample middle-right of window.
sample_points = [
    (500, 100),   # upper content area
    (700, 300),   # mid content area
    (600, 550),   # lower content area
    (400, 400),   # left-ish content area
]

black_found = False
for i in range(sidebar.count()):
    sidebar.setCurrentRow(i)
    app.processEvents()
    pixmap = window.grab()
    print(f"\n--- Page {i}: {sidebar.item(i).text().strip()} ---")
    for (x, y) in sample_points:
        color: QColor = pixmap.toImage().pixelColor(x, y)
        hexc = color.name()
        is_black = color.lightness() < 30
        if is_black:
            black_found = True
        print(f"  pixel({x},{y}) = {hexc} {'BLACK!' if is_black else ''}")

print(f"\n{'FAIL: black background detected!' if black_found else 'PASS: no black background in content area'}")
window.close()
sys.exit(1 if black_found else 0)
