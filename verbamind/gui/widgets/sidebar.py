"""Sidebar navigation — QListWidget with Dashboard, Recording, Patients, Audit Log."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):
    navigation_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(180)
        self.addItems(["Dashboard", "Recording", "Patients", "Audit Log"])
        self.setCurrentRow(0)
        self.currentRowChanged.connect(self.navigation_changed.emit)
