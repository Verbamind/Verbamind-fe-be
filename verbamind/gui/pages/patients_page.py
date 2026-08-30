"""Patients page — data pasien dengan search dan tabel. Empty by default."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.widgets.section_title import SectionTitle


class PatientsPage(QWidget):

    add_patient_requested = Signal()
    open_patient_requested = Signal(int)
    delete_patient_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._patients: list[dict] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = SectionTitle("Data Pasien")

        search_row = QHBoxLayout()
        search_input = QLineEdit()
        search_input.setPlaceholderText("Cari nama pasien...")
        search_input.setFixedWidth(260)
        search_btn = QPushButton("Cari")
        search_btn.setObjectName("small_btn")
        add_btn = QPushButton("+ Tambah Pasien")
        add_btn.setObjectName("primary_btn")
        add_btn.setStyleSheet("padding: 5px 12px; font-size: 12px;")
        search_input.textChanged.connect(lambda t: self._apply_filter(t))
        add_btn.clicked.connect(self.add_patient_requested.emit)
        search_row.addWidget(search_input)
        search_row.addWidget(search_btn)
        search_row.addStretch()
        search_row.addWidget(add_btn)
        self._search_input = search_input

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["ID", "Nama", "Tanggal Lahir", "No. Rekam Medis", "Jumlah Sesi", "Aksi"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setRowCount(0)

        self._empty_label = QLabel("Belum ada pasien terdaftar.")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #5a5a5a; font-size: 12.5px; padding: 24px; background: #fafafa; "
            "border: 1px dashed #b1b1b1; border-radius: 2px;"
        )

        layout.addWidget(title)
        layout.addLayout(search_row)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table)
        self._table.setVisible(False)
        layout.addStretch()

    def load_patients(self, patients: list[dict]):
        self._patients = patients
        self._apply_filter(self._search_input.text())

    def _apply_filter(self, text: str):
        text = (text or "").lower()
        patients = [p for p in self._patients if text in p.get("name", "").lower()]
        if not patients:
            self._empty_label.setVisible(True)
            self._table.setVisible(False)
            return
        self._empty_label.setVisible(False)
        self._table.setVisible(True)
        self._table.setRowCount(len(patients))
        for i, p in enumerate(patients):
            self._table.setItem(i, 0, QTableWidgetItem(f"P-{p.get('id', 0):03d}"))
            self._table.setItem(i, 1, QTableWidgetItem(p.get("name", "")))
            self._table.setItem(i, 2, QTableWidgetItem(p.get("birth_date", "—")))
            self._table.setItem(i, 3, QTableWidgetItem(p.get("medical_record", "—")))
            self._table.setItem(i, 4, QTableWidgetItem(str(p.get("session_count", 0))))

            actions = QWidget()
            ar = QHBoxLayout(actions)
            ar.setContentsMargins(2, 2, 2, 2)
            ar.setSpacing(6)
            open_btn = QPushButton("Buka")
            open_btn.setObjectName("small_btn")
            open_btn.setMinimumHeight(24)
            pid_open = p.get("id")
            open_btn.clicked.connect(
                lambda _=False, pid=pid_open: self.open_patient_requested.emit(pid)
            )
            del_btn = QPushButton("Hapus")
            del_btn.setObjectName("small_btn")
            del_btn.setMinimumHeight(24)
            del_btn.setStyleSheet(
                "color: #a02a1f; border: 1px solid #c0392b; "
                "padding: 3px 10px; font-size: 11.5px;"
            )
            pid_del = p.get("id")
            del_btn.clicked.connect(
                lambda _=False, pid=pid_del: self.delete_patient_requested.emit(pid)
            )
            ar.addStretch()
            ar.addWidget(open_btn)
            ar.addWidget(del_btn)
            ar.addStretch()
            self._table.setCellWidget(i, 5, actions)
            self._table.setRowHeight(i, 36)
