"""Verbatim+BIRP modal dialog — editable transcript & BIRP, audio retention confirm, PDF export."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from verbamind.gui.nonverbal_labels import nonverbal_label

BIRP_FIELDS = [
    ("behavior", "B (Perilaku):"),
    ("intervention", "I (Intervensi):"),
    ("response", "R (Respons):"),
    ("plan", "P (Rencana):"),
]


class VerbatimBIRPDialog(QDialog):

    birp_saved = Signal(int, dict)  # session_id, birp
    audio_deleted = Signal(int)
    audio_kept = Signal(int)

    def __init__(self, session: dict, birp: dict | None, segments: list[dict], parent=None):
        super().__init__(parent)
        self._session = session
        self._birp = birp or {}
        self._segments = segments
        self._decided_audio = False

        self.setWindowTitle(
            f"Hasil Verbatim — {session.get('patient_name', '')}, "
            f"{session.get('date', '')} (S-{session.get('id', 0):04d})"
        )
        self.resize(1100, 700)

        layout = QVBoxLayout(self)

        # ---- Konfirmasi Penyimpanan Audio ----
        if session.get("audio_status") not in ("Dihapus otomatis",):
            confirm = QWidget()
            confirm.setStyleSheet(
                "background: #fff4ce; border: 1px solid #d8a400; border-radius: 2px;"
            )
            cl = QVBoxLayout(confirm)
            cl.setContentsMargins(10, 8, 10, 8)
            msg = QLabel(
                "<b>⚠ Konfirmasi Penyimpanan Audio</b><br>"
                "Apakah verbatim / ringkasan BIRP sesi ini akan diedit lagi? "
                "Jika tidak, file audio akan dihapus otomatis."
            )
            msg.setStyleSheet("background: transparent; border: none;")
            msg.setWordWrap(True)
            cl.addWidget(msg)
            btns = QHBoxLayout()
            keep_btn = QPushButton("Ya, akan edit — simpan audio")
            keep_btn.setObjectName("primary_btn")
            keep_btn.setStyleSheet("padding: 4px 12px; font-size: 11.5px;")
            keep_btn.clicked.connect(self._on_keep_audio)
            del_btn = QPushButton("Tidak — hapus audio sekarang")
            del_btn.setStyleSheet(
                "padding: 4px 12px; font-size: 11.5px; color: #a02a1f; "
                "border: 1px solid #c0392b; background: #fbeaea;"
            )
            del_btn.clicked.connect(self._on_delete_audio)
            btns.addWidget(keep_btn)
            btns.addWidget(del_btn)
            btns.addStretch()
            cl.addLayout(btns)
            self._confirm_box = confirm
            layout.addWidget(confirm)
        else:
            self._confirm_box = None

        # ---- Split: transcript | BIRP ----
        split = QHBoxLayout()
        split.setSpacing(12)

        # Left: transcript table
        left = QVBoxLayout()
        t_title = QLabel("Transkrip (klik sel untuk edit)")
        t_title.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Waktu", "Pembicara", "Ucapan", "Fisiologis Suara"]
        )
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setWordWrap(True)
        self._table.setRowCount(len(segments))
        for i, seg in enumerate(segments):
            start = seg.get("start", 0.0)
            m, s = int(start // 60), int(start % 60)
            self._table.setItem(i, 0, QTableWidgetItem(f"{m:02d}:{s:02d}"))
            self._table.setItem(
                i, 1, QTableWidgetItem(str(seg.get("speaker", "—")).capitalize())
            )
            self._table.setItem(i, 2, QTableWidgetItem(seg.get("text", "")))
            nonverbal_item = QTableWidgetItem(nonverbal_label(seg.get("emotion")))
            self._table.setItem(i, 3, nonverbal_item)
        self._table.horizontalHeader().sectionResized.connect(self._layout_rows)
        self._table.itemChanged.connect(self._layout_rows)
        self._layout_rows()
        left.addWidget(t_title)
        left.addWidget(self._table, 1)

        pdf_t_btn = QPushButton("Ekspor PDF Transkrip")
        pdf_t_btn.setObjectName("small_btn")
        pdf_t_btn.clicked.connect(self._export_transcript_pdf)
        left.addWidget(pdf_t_btn)

        # Right: BIRP fields
        right = QVBoxLayout()
        b_title = QLabel("Ringkasan BIRP — isian dari AI, edit konten sesuai kebutuhan")
        b_title.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #5a5a5a;")
        b_title.setWordWrap(True)
        right.addWidget(b_title)
        self._birp_fields: dict[str, QTextEdit] = {}
        for key, label in BIRP_FIELDS:
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 11px; color: #5a5a5a;")
            edit = QTextEdit()
            edit.setPlainText(self._birp.get(key, ""))
            edit.setMaximumHeight(90)
            right.addWidget(lbl)
            right.addWidget(edit)
            self._birp_fields[key] = edit

        save_btn = QPushButton("Simpan Perubahan")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self._on_save)
        pdf_b_btn = QPushButton("Ekspor PDF BIRP")
        pdf_b_btn.setObjectName("small_btn")
        pdf_b_btn.clicked.connect(self._export_birp_pdf)
        rb = QHBoxLayout()
        rb.addWidget(save_btn)
        rb.addWidget(pdf_b_btn)
        rb.addStretch()
        right.addLayout(rb)
        right.addStretch()

        split.addLayout(left, 3)
        split.addLayout(right, 2)
        layout.addLayout(split, 1)

        close_btn = QPushButton("Tutup")
        close_btn.setObjectName("small_btn")
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_row.addWidget(close_btn)
        close_btn.clicked.connect(self.accept)
        layout.addLayout(close_row)

    # ---- audio decisions ----
    def _on_keep_audio(self):
        self._decided_audio = True
        self.audio_kept.emit(self._session["id"])
        self._confirm_box.setVisible(False)

    def _on_delete_audio(self):
        confirm = QMessageBox.question(
            self,
            "Hapus Audio",
            "File audio sesi ini akan dihapus permanen. Lanjutkan?",
        )
        if confirm == QMessageBox.Yes:
            self._decided_audio = True
            self.audio_deleted.emit(self._session["id"])
            self._confirm_box.setVisible(False)

    # ---- save ----
    def _on_save(self):
        birp = {k: e.toPlainText().strip() for k, e in self._birp_fields.items()}
        self.birp_saved.emit(self._session["id"], birp)
        QMessageBox.information(self, "Simpan", "Perubahan BIRP tersimpan.")

    # ---- PDF ----
    def _export_transcript_pdf(self):
        from PySide6.QtWidgets import QFileDialog

        from verbamind.gui.pdf_export import export_transcript_pdf

        path, _ = QFileDialog.getSaveFileName(
            self, "Ekspor PDF Transkrip", f"transkrip_S{self._session['id']:04d}.pdf", "PDF (*.pdf)"
        )
        if path:
            export_transcript_pdf(path, self._session, self._collect_segments())

    def _export_birp_pdf(self):
        from PySide6.QtWidgets import QFileDialog

        from verbamind.gui.pdf_export import export_birp_pdf

        path, _ = QFileDialog.getSaveFileName(
            self, "Ekspor PDF BIRP", f"birp_S{self._session['id']:04d}.pdf", "PDF (*.pdf)"
        )
        if path:
            birp = {k: e.toPlainText().strip() for k, e in self._birp_fields.items()}
            export_birp_pdf(path, self._session, birp)

    def _layout_rows(self, *_args):
        col_width = self._table.columnWidth(2)
        if col_width <= 0:
            col_width = max(300, self._table.viewport().width() - 340)
        fm = QFontMetrics(self._table.font())
        line_h = max(1, fm.lineSpacing())
        usable = max(60, col_width - 32)
        for i in range(self._table.rowCount()):
            item = self._table.item(i, 2)
            text = item.text() if item is not None else ""
            lines = 0
            for paragraph in (text.split("\n") if text else [""]):
                rect = fm.boundingRect(
                    0, 0, usable, 0, Qt.TextWordWrap | Qt.AlignLeft, paragraph
                )
                lines += max(1, -(-rect.height() // line_h))
            lines = max(1, lines)
            self._table.setRowHeight(i, lines * line_h + 16)

    def showEvent(self, event):  # noqa: N802 — Qt override
        super().showEvent(event)
        self._layout_rows()

    def _collect_segments(self) -> list[dict]:
        out = []
        for i in range(self._table.rowCount()):
            out.append(
                {
                    "start": self._table.item(i, 0).text(),
                    "speaker": self._table.item(i, 1).text(),
                    "text": self._table.item(i, 2).text(),
                }
            )
        return out
