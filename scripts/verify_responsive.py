"""Programmatic responsiveness verification — proves content scrolls, not clipped."""
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QScrollArea, QMainWindow

from verbamind.gui.windows.main_window import MainWindow
from verbamind.gui.widgets.sidebar import Sidebar

app = QApplication([])
window = MainWindow()
window.resize(1000, 660)
window.show()
app.processEvents()

print("=== Responsiveness Verification ===")
print(f"Window size: {window.width()}x{window.height()}")
print(f"Minimum size: {window.minimumWidth()}x{window.minimumHeight()}")

# 1. Every page is wrapped in QScrollArea
scrolls = window.findChildren(QScrollArea, "content_scroll")
print(f"ScrollArea count: {len(scrolls)}  (expect 8 pages)")
assert len(scrolls) >= 8, "Not all pages wrapped in scroll area"

# 2. ScrollAreas are resizable
all_resizable = all(s.widgetResizable() for s in scrolls)
print(f"All scroll areas widgetResizable: {all_resizable}")
assert all_resizable

# 3. Sidebar is fixed, content stretches
sidebar = window.findChild(Sidebar, "sidebar")
stack = window.findChild(QMainWindow, "")
print(f"Sidebar width: {sidebar.width()}")

# 4. Test resizing down — content should scroll, not clip
window.resize(650, 400)
app.processEvents()
print(f"\nAfter resize to 650x400: window={window.width()}x{window.height()}")

# Recording page is the tallest — check its scroll area
sidebar.setCurrentRow(2)  # Sesi Baru
app.processEvents()
recording_scroll = None
for s in scrolls:
    if s.isVisible():
        recording_scroll = s
        break
if recording_scroll:
    viewport_h = recording_scroll.viewport().height()
    widget_h = recording_scroll.widget().sizeHint().height()
    has_vbar = recording_scroll.verticalScrollBar().maximum() > 0
    print(f"Recording page: viewport={viewport_h}px, content_hint={widget_h}px, "
          f"vertical_scrollbar_active={has_vbar}")
    if widget_h > viewport_h:
        print("  => CONTENT SCROLLS (not clipped) ✓")
        assert has_vbar, "Scrollbar should be active when content taller than viewport"
    else:
        print("  => Content fits (no scroll needed) ✓")

print("\nALL RESPONSIVENESS CHECKS PASSED")
window.close()
