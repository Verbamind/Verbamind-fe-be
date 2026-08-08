"""PySide6 GUI entry point — VerbaMind main window."""

import sys

from PySide6.QtWidgets import QApplication

from verbamind.gui.windows.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
