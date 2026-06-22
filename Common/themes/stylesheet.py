# -*- coding: utf-8 -*-
"""PySide6 QSS"""
from . import load_theme

def generate_stylesheet(theme_name="dark"):
    """Qt"""
    t = load_theme(theme_name)
    c = t["colors"]
    f = t["fonts"]
    s = t["spacing"]
    r = t["radius"]
    
    return f"""
/* ===== Lighting Designer Workstation - {t['name']} ===== */

/*  */
QWidget {{
    background-color: {c['background']};
    color: {c['text']};
    font-family: {f['family']};
    font-size: {f['size_normal']}px;
    selection-background-color: {c['selection']};
    selection-color: {c['text_bright']};
}}

/*  */
QMainWindow {{
    background-color: {c['background']};
}}

QMainWindow::separator {{
    background-color: {c['border']};
    width: 2px;
    height: 2px;
}}

/*  */
QMenuBar {{
    background-color: {c['menu_bg']};
    border-bottom: 1px solid {c['border']};
    padding: 2px;
}}
QMenuBar::item {{
    padding: 6px 12px;
    background: transparent;
}}
QMenuBar::item:selected {{
    background-color: {c['highlight']};
}}
QMenu {{
    background-color: {c['menu_bg']};
    border: 1px solid {c['border']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
}}
QMenu::item:selected {{
    background-color: {c['accent']};
}}
QMenu::separator {{
    height: 1px;
    background-color: {c['border']};
    margin: 4px 8px;
}}

/*  */
QToolBar {{
    background-color: {c['toolbar_bg']};
    border: none;
    padding: 4px;
    spacing: 4px;
}}
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {r['sm']}px;
    padding: 6px;
    color: {c['text']};
}}
QToolButton:hover {{
    background-color: {c['button_hover']};
    border: 1px solid {c['border']};
}}
QToolButton:pressed {{
    background-color: {c['accent_pressed']};
}}

/*  */
QStatusBar {{
    background-color: {c['statusbar_bg']};
    color: {c['text_bright']};
    font-size: {f['size_small']}px;
}}
QStatusBar::item {{
    border: none;
}}

/*  */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    background-color: {c['surface']};
}}
QTabBar::tab {{
    background-color: {c['tab_inactive']};
    color: {c['text_dim']};
    padding: 8px 16px;
    border: 1px solid {c['border']};
    border-bottom: none;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {c['tab_active']};
    color: {c['text_bright']};
    border-bottom: 2px solid {c['accent']};
}}
QTabBar::tab:hover {{
    background-color: {c['button_hover']};
}}

/*  */
QPushButton {{
    background-color: {c['button_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: {r['sm']}px;
    padding: 6px 16px;
    min-height: 24px;
}}
QPushButton:hover {{
    background-color: {c['button_hover']};
    border-color: {c['accent']};
}}
QPushButton:pressed {{
    background-color: {c['accent_pressed']};
}}
QPushButton:disabled {{
    background-color: {c['surface']};
    color: {c['text_dim']};
}}
QPushButton#accent_btn {{
    background-color: {c['accent']};
    color: {c['text_bright']};
    font-weight: bold;
}}
QPushButton#accent_btn:hover {{
    background-color: {c['accent_hover']};
}}

/*  */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['input_bg']};
    color: {c['text']};
    border: 1px solid {c['input_border']};
    border-radius: {r['sm']}px;
    padding: 6px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c['accent']};
}}

/*  */
QComboBox {{
    background-color: {c['input_bg']};
    color: {c['text']};
    border: 1px solid {c['input_border']};
    border-radius: {r['sm']}px;
    padding: 6px;
}}
QComboBox:hover {{
    border-color: {c['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    selection-background-color: {c['accent']};
}}

/*  */
QSpinBox, QDoubleSpinBox {{
    background-color: {c['input_bg']};
    color: {c['text']};
    border: 1px solid {c['input_border']};
    border-radius: {r['sm']}px;
    padding: 4px;
}}

/*  */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {c['tree_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    alternate-background-color: {c['table_alt']};
}}
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {c['selection']};
    color: {c['text_bright']};
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {c['highlight']};
}}
QHeaderView::section {{
    background-color: {c['table_header']};
    color: {c['text']};
    border: 1px solid {c['border']};
    padding: 6px;
    font-weight: bold;
}}

/*  */
QScrollBar:vertical {{
    background-color: {c['background']};
    width: 12px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {c['scrollbar']};
    border-radius: 6px;
    min-height: 30px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {c['scrollbar_hover']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background-color: {c['background']};
    height: 12px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {c['scrollbar']};
    border-radius: 6px;
    min-width: 30px;
    margin: 2px;
}}

/*  */
QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: {r['md']}px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
    color: {c['accent']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}}

/*  */
QProgressBar {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: {r['sm']}px;
    text-align: center;
    color: {c['text_bright']};
}}
QProgressBar::chunk {{
    background-color: {c['accent']};
    border-radius: {r['sm']}px;
}}

/*  */
QSlider::groove:horizontal {{
    background-color: {c['surface']};
    height: 6px;
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background-color: {c['accent']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background-color: {c['accent_hover']};
}}

/*  */
QDockWidget {{
    color: {c['text']};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background-color: {c['panel']};
    padding: 8px;
    border-bottom: 1px solid {c['border']};
    font-weight: bold;
}}

/*  */
QToolTip {{
    background-color: {c['panel']};
    color: {c['text']};
    border: 1px solid {c['accent']};
    padding: 6px;
    font-size: {f['size_small']}px;
}}

/*  */
QSplitter::handle {{
    background-color: {c['border']};
}}
QSplitter::handle:horizontal {{
    width: 3px;
}}
QSplitter::handle:vertical {{
    height: 3px;
}}

/* / */
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c['input_border']};
    border-radius: 3px;
    background-color: {c['input_bg']};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {c['accent']};
    border-color: {c['accent']};
}}
QRadioButton::indicator {{
    border-radius: 9px;
}}
"""
