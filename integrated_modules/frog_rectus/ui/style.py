"""Accessible colour system shared by all Frog Rectus screens."""

PRIMARY = "#1565C0"
PRIMARY_LIGHT = "#287CCB"
PRIMARY_DARK = "#0D47A1"
ACCENT = "#00897B"
DANGER = "#C62828"
WARNING = "#EF6C00"
SUCCESS = "#2E7D32"
BG_WHITE = "#F4F8FC"
BG_PANEL = "#E7EEF6"
BG_CARD = "#FFFFFF"
TEXT_PRIMARY = "#182433"
TEXT_SECONDARY = "#526174"
BORDER = "#BFCBDD"
GRAPH_BG = "#F1F6FA"
BATH_BLUE = "#90CAF9"
MUSCLE_PINK = "#EF5350"
RINGER_GREEN = "#A5D6A7"

FONT_TITLE = 23
FONT_HEADING = 17
FONT_BODY = 13
FONT_SMALL = 11
FONT_BUTTON = 13

# Keep institutional branding quiet on working screens so the experiment title
# and controls remain the visual focus.  The home screen intentionally retains
# the full department and college name as the application's front page.
INSTITUTION_TEXT = "MAMC, New Delhi"
INSTITUTION_LABEL_STYLE = f"""
font-size: 10px;
font-weight: 600;
color: {TEXT_SECONDARY};
padding: 2px 4px;
"""

MAIN_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_WHITE};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", Tahoma, Arial, sans-serif;
    font-size: {FONT_BODY}px;
}}
QPushButton {{
    background-color: {PRIMARY};
    color: white;
    border: 1px solid {PRIMARY_DARK};
    border-radius: 7px;
    padding: 9px 15px;
    font-size: {FONT_BUTTON}px;
    font-weight: 600;
    min-height: 24px;
}}
QPushButton:hover {{ background-color: {PRIMARY_LIGHT}; }}
QPushButton:pressed {{ background-color: {PRIMARY_DARK}; }}
QPushButton:focus {{ border: 2px solid #FFB300; }}
QPushButton:disabled {{ background-color: #AEB9C4; color: #F4F6F8; }}
QPushButton[secondary="true"] {{
    background-color: #FFFFFF;
    color: {PRIMARY_DARK};
    border: 2px solid {PRIMARY};
}}
QPushButton[secondary="true"]:hover {{ background-color: #E3F2FD; }}
QPushButton[danger="true"] {{ background-color: {DANGER}; border-color: #8E0000; }}
QPushButton[danger="true"]:hover {{ background-color: #D63B3B; }}
QPushButton[success="true"] {{ background-color: {SUCCESS}; border-color: #1B5E20; }}
QPushButton[success="true"]:hover {{ background-color: #388E3C; }}

QLineEdit, QComboBox, QDoubleSpinBox {{
    background-color: #FFFFFF;
    border: 2px solid {BORDER};
    border-radius: 6px;
    padding: 7px 9px;
    min-height: 22px;
    selection-background-color: {PRIMARY};
}}
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{ border-color: {PRIMARY}; }}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{
    background: white;
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    selection-background-color: {PRIMARY};
    selection-color: white;
}}
QLabel {{ color: {TEXT_PRIMARY}; background: transparent; }}
QLabel[heading="true"] {{
    font-size: {FONT_HEADING}px;
    font-weight: 700;
    color: {PRIMARY_DARK};
}}
QLabel[subheading="true"] {{ color: {TEXT_SECONDARY}; }}

QGroupBox {{
    font-weight: 650;
    border: 1px solid {BORDER};
    border-radius: 9px;
    margin-top: 14px;
    padding-top: 18px;
    background: {BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 10px;
    color: {PRIMARY_DARK};
    background: #EAF3FC;
    border-radius: 5px;
}}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: {BG_PANEL}; width: 14px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #899BB1; border-radius: 6px; min-height: 35px; }}
QScrollBar:horizontal {{ background: {BG_PANEL}; height: 15px; margin: 0; }}
QScrollBar::handle:horizontal {{ background: #738AA5; border-radius: 6px; min-width: 45px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QTextBrowser, QTextEdit {{
    background: white;
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px;
}}
QCheckBox {{ spacing: 7px; min-height: 25px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 3px;
    border: 2px solid {BORDER}; background: white;
}}
QCheckBox::indicator:checked {{ background: {PRIMARY}; border-color: {PRIMARY}; }}
QTableWidget {{
    background: white; alternate-background-color: #EEF5FB;
    gridline-color: {BORDER}; border: 1px solid {BORDER};
}}
QHeaderView::section {{
    background: {PRIMARY_DARK}; color: white; padding: 7px;
    border: 1px solid #E3F2FD; font-weight: 600;
}}
QSplitter::handle {{ background: {BG_PANEL}; width: 5px; height: 5px; }}
QStatusBar {{
    background: {BG_PANEL}; color: {TEXT_SECONDARY};
    font-size: {FONT_SMALL}px; border-top: 1px solid {BORDER};
}}
"""

HOME_BUTTON_STYLE = f"""
QPushButton {{
    background-color: #FFFFFF;
    color: {TEXT_PRIMARY};
    border: 2px solid {BORDER};
    border-left: 7px solid {PRIMARY};
    border-radius: 11px;
    padding: 18px 20px;
    font-size: 14px;
    font-weight: 650;
    text-align: left;
    min-height: 62px;
}}
QPushButton:hover {{ border-color: {PRIMARY}; background-color: #EAF4FF; }}
QPushButton:pressed {{ background-color: #D9ECFF; }}
"""

TITLE_LABEL_STYLE = f"""
font-size: {FONT_TITLE}px;
font-weight: 800;
color: {PRIMARY_DARK};
"""

SUBTITLE_LABEL_STYLE = f"""
font-size: {FONT_BODY}px;
color: {TEXT_SECONDARY};
font-weight: 400;
"""
