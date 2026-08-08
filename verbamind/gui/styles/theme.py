"""Windows classic 3D aesthetic — matches ui-verbamind-a.html spec precisely.

Every widget gets explicit color to prevent font/background blend issues.
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
    "danger": "#c0392b",
    "success": "#2e7d32",
}

MAIN_STYLESHEET = """
/* Global default — force Segoe UI everywhere */
QWidget {
    font-family: "Segoe UI", "Tahoma", sans-serif;
    font-size: 13px;
    color: #1a1a1a;
}

QMainWindow {
    background-color: #f0f0f0;
    color: #1a1a1a;
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
    color: #1a1a1a;
    background: transparent;
}
QMenuBar::item:selected {
    background: #cfe4fb;
    color: #1a1a1a;
}
QMenuBar::item:pressed {
    background: #0a5fc4;
    color: #ffffff;
}

/* Dropdown menu — explicit background + text color */
QMenu {
    background: #ffffff;
    border: 1px solid #b1b1b1;
    color: #1a1a1a;
    padding: 4px;
    font-size: 12px;
}
QMenu::item {
    padding: 6px 24px;
    color: #1a1a1a;
    background: transparent;
}
QMenu::item:selected {
    background: #cfe4fb;
    color: #1a1a1a;
}
QMenu::item:disabled {
    color: #999999;
}
QMenu::separator {
    height: 1px;
    background: #b1b1b1;
    margin: 4px 8px;
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
    color: #1a1a1a;
    padding: 8px 0;
    outline: none;
}
QListWidget#sidebar::item {
    padding: 8px 14px;
    border-left: 3px solid transparent;
    color: #1a1a1a;
}
QListWidget#sidebar::item:hover {
    background: #dcecfb;
    color: #1a1a1a;
}
QListWidget#sidebar::item:selected {
    background: #cfe4fb;
    border-left: 3px solid #0a5fc4;
    font-weight: 600;
    color: #1a1a1a;
}

/* Content area — white panel */
QWidget#content_area {
    background-color: #ffffff;
}

/* Page headers */
QLabel#section_title {
    font-size: 15px;
    font-weight: 600;
    color: #1a1a1a;
    background: transparent;
    border: none;
    border-bottom: 1px solid #b1b1b1;
    padding: 4px 0 10px 0;
    margin: 0 0 14px 0;
    min-height: 24px;
}

/* GroupBox — Windows classic with title overlay */
QGroupBox {
    border: 1px solid #b1b1b1;
    background: #f4f4f4;
    border-radius: 2px;
    margin-top: 14px;
    padding: 16px 14px 14px 14px;
    color: #1a1a1a;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    top: -9px;
    background: #ffffff;
    padding: 0 6px;
    color: #5a5a5a;
    font-size: 11.5px;
    font-weight: 600;
}

/* Labels — explicit color to prevent blend */
QLabel {
    color: #1a1a1a;
    background: transparent;
}
QLabel#text_dim {
    color: #5a5a5a;
}
QLabel#stat_number {
    font-size: 22px;
    font-weight: 700;
    color: #0a5fc4;
}
QLabel#stat_label {
    font-size: 11px;
    color: #5a5a5a;
}
QLabel#timer_big {
    font-size: 28px;
    font-weight: 700;
    color: #1a1a1a;
    font-family: "Consolas", "Courier New", monospace;
}
QLabel#status_rec {
    font-size: 11px;
    color: #c0392b;
    font-weight: 600;
}
QLabel#birp_label {
    font-size: 11.5px;
    font-weight: 700;
    color: #0a5fc4;
}

/* Buttons — 3D gradient Windows classic */
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
    color: #1a1a1a;
}
QPushButton:pressed {
    background: #dcebfb;
}
QPushButton:disabled {
    color: #999999;
    background: #f0f0f0;
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
    color: #ffffff;
}

/* Danger (red) button */
QPushButton#danger_btn {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #ffffff, stop:1 #fbeaea);
    border-color: #c0392b;
    color: #a02a1f;
}
QPushButton#danger_btn:hover {
    background: #f9d6d2;
    color: #a02a1f;
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
    color: #1a1a1a;
    border-radius: 2px;
}
QLineEdit:focus {
    border-color: #0a5fc4;
}
QLineEdit:disabled {
    background: #efefef;
    color: #5a5a5a;
}

/* ComboBox */
QComboBox {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    padding: 5px 6px;
    font-size: 12.5px;
    color: #1a1a1a;
    border-radius: 2px;
}
QComboBox:focus {
    border-color: #0a5fc4;
}
QComboBox:disabled {
    background: #efefef;
    color: #5a5a5a;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    color: #1a1a1a;
    selection-background-color: #cfe4fb;
    selection-color: #1a1a1a;
}

/* Table */
QTableWidget {
    background: #ffffff;
    border: 1px solid #b1b1b1;
    gridline-color: #dddddd;
    font-size: 12px;
    color: #1a1a1a;
    alternate-background-color: #f7f9fb;
}
QTableWidget::item {
    padding: 6px 8px;
    color: #1a1a1a;
}
QTableWidget::item:alternate {
    background: #f7f9fb;
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
QStatusBar::item {
    border: none;
}
QStatusBar QLabel {
    color: #5a5a5a;
    background: transparent;
}

/* TextEdit for BIRP — Consolas font */
QTextEdit {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    padding: 6px 8px;
    font-family: "Consolas", "Segoe UI", monospace;
    font-size: 12px;
    color: #1a1a1a;
    border-radius: 2px;
}
QTextEdit:focus {
    border-color: #0a5fc4;
}

/* TextEdit read-only (disabled) */
QTextEdit[readOnly="true"] {
    background: #fafafa;
    color: #1a1a1a;
}

/* Progress bar */
QProgressBar {
    border: 1px solid #b1b1b1;
    background: #ffffff;
    border-radius: 2px;
    height: 16px;
    color: #1a1a1a;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0 y1:0, x2:0 y2:1,
        stop:0 #1a78d6, stop:1 #0a5fc4);
}

/* Slider */
QSlider::groove:horizontal {
    height: 6px;
    background: #cfcfcf;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    background: #ffffff;
    border: 1px solid #0a5fc4;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background: #0a5fc4;
    border-radius: 3px;
}

/* Message box / dialog */
QDialog {
    background: #f0f0f0;
    color: #1a1a1a;
}
"""
