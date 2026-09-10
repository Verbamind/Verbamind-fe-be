"""Settings page — database info, AI model config, audio config, license info."""

from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.api_client import VerbaMindClient
from verbamind.gui.widgets.section_title import SectionTitle


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._client = VerbaMindClient()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = SectionTitle("Pengaturan")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)

        model_group = QGroupBox("Model AI (Ollama)")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(8)
        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        self._model_combo.setToolTip("Pilih model yang terinstall di Ollama, atau ketik nama model.")
        row = QHBoxLayout()
        row.setSpacing(8)
        refresh_btn = QPushButton("Muat ulang")
        refresh_btn.clicked.connect(self._refresh_models)
        save_btn = QPushButton("Simpan")
        save_btn.clicked.connect(self._save_model)
        row.addWidget(self._model_combo, 1)
        row.addWidget(refresh_btn)
        row.addWidget(save_btn)
        model_layout.addWidget(QLabel("Model LLM yang dipakai untuk analisis BIRP:"))
        model_layout.addLayout(row)
        content_layout.addWidget(model_group)

        db_group = QGroupBox("Basis Data")
        db_layout = QVBoxLayout(db_group)
        db_layout.setSpacing(8)
        from verbamind.config.config import get_database_url
        db_path = QLabel(get_database_url())
        db_path.setObjectName("db_path_label")
        db_path.setWordWrap(True)
        db_path.setStyleSheet("font-size: 11.5px; font-family: 'Consolas', monospace; color: #5a5a5a;")
        db_layout.addWidget(db_path)
        content_layout.addWidget(db_group)

        license_group = QGroupBox("Lisensi")
        license_layout = QVBoxLayout(license_group)
        license_layout.setSpacing(8)
        try:
            from verbamind.security.activation import get_hardware_id
            hwid = get_hardware_id()
        except Exception:
            hwid = "Unavailable"
        hwid_label = QLabel(f"ID Perangkat: {hwid}")
        hwid_label.setWordWrap(True)
        hwid_label.setStyleSheet("font-size: 11.5px; font-family: 'Consolas', monospace; color: #5a5a5a;")
        license_layout.addWidget(hwid_label)
        content_layout.addWidget(license_group)

        content_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)

        layout.addWidget(title)
        layout.addWidget(scroll, 1)

        self._refresh_models()

    def _refresh_models(self):
        current = None
        try:
            current = self._client.get_llm_settings().get("llm_model")
        except Exception:
            current = None

        try:
            models = self._client.list_models().get("models", [])
        except Exception:
            models = []

        self._model_combo.clear()
        if models:
            self._model_combo.addItems(models)
        if current:
            self._model_combo.setCurrentText(current)

    def _save_model(self):
        model = self._model_combo.currentText().strip()
        if not model:
            return
        try:
            result = self._client.update_llm_settings(llm_model=model)
            QMessageBox.information(
                self, "Tersimpan", f"Model disetel ke: {result.get('llm_model', model)}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Gagal", f"Gagal menyimpan model: {e}")
