"""Windows classic 3D aesthetic — matches ui-verbamind-a.html spec precisely.

QSS with gradient buttons, 3D panel borders, Segoe UI typography,
sidebar dot indicators, group box title overlays, status bar.
"""

COLORS = {
    "win_bg": "#f0f0f0",
    "panel_bg": "#ffffff",
    "border_dark": "#8f8f8f",
    "border_light": "#ffffff",
    "border_mid": "#b1b1b1",
    "accent": "#0a5fc4",
    "accent_soft": "#cfe4fb",
    "text": "#1a1a1a",
    "text_dim": "#5a5a5a",
    "sidebar_bg": "#e7e7e7",
    "statusbar_bg": "#e2e2e2",
    "groupbox_bg": "#f4f4f4",
    "led_on": "#2ecc57",
    "led_off": "#c9c9c9",
    "warn_bg": "#fff4ce",
    "warn_border": "#d8a400",
}

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #f0f0f0;
}
QMainWindow::separator {
    width: 1px;
    background: #b1b1b1;
}

/* Menu bar */
QMenuBar {
    background: #f0f0f0;
    border-bottom: 1px solid #b1b1b1;
    padding: 2px 6px;
    font-size: 12px;
    color: #1a1a1a;
}
QMenuBar::item {
    padding: 4px 10px;
}
QMenuBar::item:selected {
    background: #cfe4fb;
}

/* Toolbar */
QToolBar {
    background: #f0f0f0;
    border-bottom: 1px solid #b1b1b1;
    spacing: 6px;
    padding: 4px 8px;
}
QToolBar::separator {
    width: 1px;
    height: 24px;
    background: #b1b1b1;
    margin: 0 4px;
}
QToolButton {
    border: 1px solid transparent;
    background: transparent;
    padding: 2px 6px;
    font-size: 10px;
    color: #1a1a1a;
    qproperty-toolButtonStyle: ToolButtonTextUnderIcon;
}
QToolButton:hover {
    border-color: #b1b1b1;
    background: #e5f0fb;
}

/* Sidebar (QListWidget) */
QListWidget#sidebar {
    background-color: #e7e7e7;
    border: none;
    border-right: 1px solid #b1b1b1;
    font-size: 12.5px;
    padding: 8px 0;
}
QListWidget#sidebar::item {
    padding: 8px 14px;
    border-left: 3px solid transparent;
}
QListWidget#sidebar::item:hover {
    background: #dcecfb;
}
QListWidget#sidebar::item:selected {
    background: #cfe4fb;
    border-left: 3px solid #0a5fc4;
    font-weight: 600;
    color: #1a1a1a;
}

/* Content area */
QWidget#content_area {
    background-color: #ffffff;
}

/* Page headers */
QWidget#content_area QLabel#section_title {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
    border-bottom: 1px solid #b1b1b1;
    padding-bottom: 8px;
    margin-bottom: 12px;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #b1b1b1;
    background: #f4f4f4;
    border-radius: 2px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    font-size: 11.5px;
    font-weight: 600;
    color: #5a5a5a;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    top: -9px;
    background: #ffffff;
    padding: 0 6px;
}

/* Buttons — 3D gradient */
QPushButton {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #ffffff, stop:1 #e6e6e6);
    border: 1px solid #b1b1b1;
    border-radius: 2px;
    padding: 6px 16px;
    font-size: 12.5px;
    color: #1a1a1a;
}
QPushButton:hover {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #f2f8ff, stop:1 #dcebfb);
    border-color: #0a5fc4;
}
QPushButton:pressed {
    background: #dcebfb;
}
QPushButton:disabled {
    color: #b1b1b1;
}

/* Primary (blue) button */
QPushButton#primary_btn {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #1a78d6, stop:1 #0a5fc4);
    color: #ffffff;
    border-color: #08519f;
    font-weight: 600;
}
QPushButton#primary_btn:hover {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #2286e6, stop:1 #0f6ad3);
}

/* Record button (round red) */
QPushButton#record_btn {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #e74c3c, stop:1 #c0392b);
    color: #ffffff;
    font-weight: bold;
    border: 1px solid #a02a1f;
    border-radius: 24px;
    min-width: 100px;
    min-height: 42px;
    font-size: 14px;
    padding: 8px 24px;
}
QPushButton#record_btn:hover {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #ef5350, stop:1 #d32f2f);
}
QPushButton#record_btn:pressed {
    background: #b71c1c;
}

/* Small button */
QPushButton#small_btn {
    padding: 3px 10px;
    font-size: 11.5px;
}

/* Line Edit */
QLineEdit {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    padding: 5px 6px;
    font-size: 12.5px;
    border-radius: 2px;
}
QLineEdit:focus {
    border-color: #0a5fc4;
}

/* ComboBox */
QComboBox {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    padding: 5px 6px;
    font-size: 12.5px;
    border-radius: 2px;
}
QComboBox:focus {
    border-color: #0a5fc4;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    selection-background-color: #cfe4fb;
}

/* Table */
QTableWidget {
    background: #ffffff;
    border: 1px solid #b1b1b1;
    gridline-color: #dddddd;
    font-size: 12px;
    alternate-background-color: #f7f9fb;
}
QTableWidget::item {
    padding: 6px 8px;
}
QTableWidget::item:selected {
    background: #cfe4fb;
    color: #1a1a1a;
}
QHeaderView::section {
    background: #e9e9e9;
    border: 1px solid #b1b1b1;
    padding: 6px 8px;
    font-weight: 600;
    font-size: 12px;
    color: #5a5a5a;
}

/* Scroll area */
QScrollArea {
    border: none;
    background: transparent;
}
QScrollBar:vertical {
    background: #f0f0f0;
    width: 14px;
    border: 1px solid #b1b1b1;
}
QScrollBar::handle:vertical {
    background: #c1c1c1;
    min-height: 20px;
    border: 1px solid #a0a0a0;
    border-radius: 2px;
}
QScrollBar::handle:vertical:hover {
    background: #a0a0a0;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status bar */
QStatusBar {
    background: #e2e2e2;
    border-top: 1px solid #b1b1b1;
    font-size: 11px;
    color: #5a5a5a;
    padding: 2px 10px;
}

/* TextEdit for BIRP */
QTextEdit {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    padding: 6px 8px;
    font-family: "Consolas", "Segoe UI", monospace;
    font-size: 12px;
    border-radius: 2px;
}
QTextEdit:focus {
    border-color: #0a5fc4;
}

/* Modern label styling */
QLabel#stat_number {
    font-size: 22px;
    font-weight: 700;
    color: #0a5fc4;
}
QLabel#stat_label {
    font-size: 11px;
    color: #5a5a5a;
}

/* Badge */
QLabel#emotion_badge {
    padding: 2px 8px;
    border-radius: 9px;
    font-size: 10.5px;
    font-weight: 600;
    color: #ffffff;
}
"""
