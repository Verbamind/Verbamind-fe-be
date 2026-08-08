"""Color tokens and stylesheet — Windows classic aesthetic from ui-verbamind-a.html."""

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
    font-family: "Segoe UI", "Tahoma", sans-serif;
    font-size: 13px;
    color: #1a1a1a;
}
QGroupBox {
    background-color: #f4f4f4;
    border: 1px solid #b1b1b1;
    border-radius: 4px;
    margin-top: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px 0 5px;
}
QPushButton {
    background-color: #ffffff;
    border: 1px solid #8f8f8f;
    border-radius: 3px;
    padding: 5px 16px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #cfe4fb;
    border-color: #0a5fc4;
}
QPushButton:pressed {
    background-color: #0a5fc4;
    color: #ffffff;
}
QPushButton#record_btn {
    background-color: #dc3545;
    color: #ffffff;
    font-weight: bold;
    border-radius: 24px;
    min-width: 48px;
    min-height: 48px;
    font-size: 16px;
}
QPushButton#record_btn:hover {
    background-color: #c82333;
}
QLineEdit {
    border: 1px solid #8f8f8f;
    border-radius: 3px;
    padding: 4px 8px;
}
QComboBox {
    border: 1px solid #8f8f8f;
    border-radius: 3px;
    padding: 4px 8px;
    background-color: #ffffff;
}
QListWidget {
    background-color: #e7e7e7;
    border: none;
    font-size: 14px;
}
QListWidget::item {
    padding: 10px 16px;
}
QListWidget::item:selected {
    background-color: #0a5fc4;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background-color: #cfe4fb;
}
QLabel#section_title {
    font-size: 16px;
    font-weight: bold;
    color: #1a1a1a;
    padding: 12px 0;
}
"""
