"""Design tokens – Dynamic Island Windows v3"""

BG_PRIMARY   = "#080808"
BG_SURFACE   = "#141416"
BG_ELEVATED  = "#2C2C2E"

TEXT_PRIMARY   = "#F5F5F7"
TEXT_SECONDARY = "#98989F"
TEXT_TERTIARY  = "#48484A"

ACCENT_BLUE   = "#0A84FF"
ACCENT_GREEN  = "#30D158"
ACCENT_RED    = "#FF453A"
ACCENT_ORANGE = "#FF9F0A"
ACCENT_PURPLE = "#BF5AF2"
ACCENT_CYAN   = "#5AC8FA"

SEPARATOR = "rgba(255,255,255,0.07)"
BORDER    = "rgba(255,255,255,0.09)"

FONT_FAMILY = "Segoe UI"
CORNER_RADIUS = 22

SETTINGS_STYLE = f"""
    QDialog {{
        background: {BG_SURFACE};
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
    }}
    QLabel {{
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        background: transparent;
    }}
    QSlider::groove:horizontal {{
        background: {BG_ELEVATED};
        height: 3px; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {TEXT_PRIMARY};
        width: 14px; height: 14px;
        margin: -6px 0; border-radius: 7px;
    }}
    QSlider::sub-page:horizontal {{
        background: {ACCENT_BLUE};
        height: 3px; border-radius: 2px;
    }}
    QCheckBox {{
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border-radius: 5px;
        border: 1.5px solid #48484A;
        background: {BG_ELEVATED};
    }}
    QCheckBox::indicator:checked {{
        background: {ACCENT_BLUE};
        border: 1.5px solid {ACCENT_BLUE};
    }}
    QPushButton {{
        background: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: none; border-radius: 8px;
        padding: 7px 18px;
        font-family: {FONT_FAMILY}; font-size: 12px;
    }}
    QPushButton:hover {{ background: #3A3A3C; }}
    QPushButton#primary {{
        background: {ACCENT_BLUE}; color: white;
    }}
    QPushButton#primary:hover {{ background: #0070E0; }}
    QComboBox {{
        background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
        border: none; border-radius: 8px;
        padding: 5px 10px;
        font-family: {FONT_FAMILY}; font-size: 12px;
    }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
        border: 1px solid #3A3A3C;
        selection-background-color: {ACCENT_BLUE};
        outline: none;
    }}
    QLineEdit {{
        background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
        border: none; border-radius: 8px;
        padding: 5px 10px;
        font-family: {FONT_FAMILY}; font-size: 12px;
    }}
    QScrollBar:vertical {{
        background: transparent; width: 4px; border-radius: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: #48484A; border-radius: 2px; min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        border: none; background: none;
    }}
"""

CONTEXT_MENU_STYLE = f"""
    QMenu {{
        background: rgba(20,20,22,0.98);
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 4px 3px;
        color: {TEXT_PRIMARY};
        font-family: {FONT_FAMILY};
        font-size: 12px;
    }}
    QMenu::item {{
        padding: 6px 14px;
        border-radius: 6px;
        margin: 1px 2px;
    }}
    QMenu::item:selected {{ background: rgba(255,255,255,0.09); }}
    QMenu::separator {{
        height: 1px;
        background: {SEPARATOR};
        margin: 3px 6px;
    }}
"""
