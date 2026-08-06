"""PySide6 GUI entry point — VerbaMind main window."""

import sys

from PySide6.QtWidgets import QApplication, QLabel, QMainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VerbaMind")
        self.setMinimumSize(800, 600)
        label = QLabel("VerbaMind — AI-Assisted Counseling Documentation")
        label.setStyleSheet("font-size: 16px; padding: 20px;")
        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
