"""Sidebar — 5 nav items with unicolor (monochrome) vector icons."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

from verbamind.gui.widgets.icons import make_icon

ICON_COLOR = "#5a5a5a"
ICON_SIZE = 18


class Sidebar(QListWidget):
    navigation_changed = Signal(int)

    ITEMS = [
        ("Dashboard", "dashboard"),
        ("Data Pasien", "patients"),
        ("Sesi Baru", "record"),
        ("Log Audit", "audit"),
        ("Pengaturan", "settings"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(190)
        self.setSpacing(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setIconSize(QSize(ICON_SIZE, ICON_SIZE))

        for label, kind in self.ITEMS:
            item = QListWidgetItem(label)
            item.setIcon(make_icon(kind, size=ICON_SIZE, color=ICON_COLOR))
            self.addItem(item)

        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.navigation_changed.emit)
