"""Microphone channel configuration — dual QComboBox for patient/psychologist input."""

from PySide6.QtWidgets import QComboBox, QFormLayout, QWidget


class DeviceConfig(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)

        self.patient_combo = QComboBox()
        self.patient_combo.setObjectName("patient_combo")
        self.psychologist_combo = QComboBox()
        self.psychologist_combo.setObjectName("psychologist_combo")

        self._populate_devices()

        layout.addRow("Patient Input:", self.patient_combo)
        layout.addRow("Psychologist Input:", self.psychologist_combo)

    def _populate_devices(self):
        try:
            from verbamind.backend.audio.device import list_input_devices

            devices = list_input_devices()
            for d in devices:
                label = f"{d['name']} ({d['channels']}ch)"
                self.patient_combo.addItem(label, d["index"])
                self.psychologist_combo.addItem(label, d["index"])
        except Exception:
            self.patient_combo.addItem("Default Input (0)", 0)
            self.psychologist_combo.addItem("Default Input (1)", 1)
