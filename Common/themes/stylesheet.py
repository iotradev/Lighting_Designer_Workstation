# -*- coding: utf-8 -*-
"""PySide6 QSS - GrandMA3 风格全局样式表"""
from . import load_theme

def generate_stylesheet(theme_name="dark"):
    """生成全局QSS样式表"""
    t = load_theme(theme_name)
    c = t["colors"]
    f = t["fonts"]
    r = t["radius"]
    
    return f"""
/* ===== Lighting Designer Workstation - {t['name']} ===== */

/* 全局 */
QWidget {{
    background-color: {c['background']};
    color: {c['text']};
    font-family: {f['family']};
    font-size: {f['size_normal']}px;
    selection-background-color: {c['selection']};
    selection-color: {c['text_bright']};
}}

/* 主窗口 */
QMainWindow {{
    background-color: {c['background']};
}}
QMainWindow::separator {{
    background-color: {c['border']};
    width: 2px;
    height: 2px;
}}

/* 菜单栏 */
QMenuBar {{
    background-color: {c['menu_bg']};
    border-bottom: 1px solid {c['border']};
    padding: 0px;
}}
QMenuBar::item {{
    padding: 3px 8px;
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
    padding: 5px 20px 5px 10px;
}}
QMenu::item:selected {{
    background-color: {c['accent']};
}}
QMenu::separator {{
    height: 1px;
    background-color: {c['border']};
    margin: 4px 8px;
}}

/* 工具栏 */
QToolBar {{
    background-color: {c['toolbar_bg']};
    border: none;
    padding: 2px;
    spacing: 2px;
}}
QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: {r['sm']}px;
    padding: 4px 8px;
    color: {c['text']};
}}
QToolButton:hover {{
    background-color: {c['button_hover']};
    border: 1px solid {c['border']};
}}
QToolButton:pressed {{
    background-color: {c['accent_pressed']};
}}

/* 状态栏 */
QStatusBar {{
    background-color: {c['statusbar_bg']};
    color: {c['text_dim']};
    font-size: {f['size_small']}px;
    border-top: 1px solid {c['border']};
    padding: 2px 8px;
    min-height: 24px;
}}
QStatusBar::item {{
    border: none;
    padding: 0 4px;
}}
QStatusBar QLabel {{
    color: {c['text_dim']};
    font-size: {f['size_small']}px;
    padding: 0 6px;
}}

/* 标签页 */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    background-color: {c['surface']};
    border-radius: {r['sm']}px;
}}
QTabBar::tab {{
    background-color: {c['tab_inactive']};
    color: {c['text_dim']};
    padding: 6px 14px;
    border: 1px solid {c['border']};
    border-bottom: none;
    margin-right: 2px;
    border-top-left-radius: {r['sm']}px;
    border-top-right-radius: {r['sm']}px;
}}
QTabBar::tab:selected {{
    background-color: {c['tab_active']};
    color: {c['text_bright']};
    border-bottom: 2px solid {c['accent']};
}}
QTabBar::tab:hover {{
    background-color: {c['button_hover']};
}}

/* 按钮 */
QPushButton {{
    background-color: {c['button_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    border-radius: {r['sm']}px;
    padding: 5px 14px;
    min-height: 22px;
}}
QPushButton:hover {{
    background-color: {c['button_hover']};
    border-color: {c['accent']}66;
}}
QPushButton:pressed {{
    background-color: {c['accent_pressed']};
}}
QPushButton:disabled {{
    background-color: {c['surface']};
    color: {c['text_dim']};
    border-color: {c['surface']};
}}
QPushButton#accent_btn {{
    background-color: {c['accent']};
    color: {c['text_bright']};
    font-weight: bold;
    border: 1px solid {c['accent']};
}}
QPushButton#accent_btn:hover {{
    background-color: {c['accent_hover']};
    border-color: {c['accent_hover']};
}}

/* 输入框 */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['input_bg']};
    color: {c['text']};
    border: 1px solid {c['input_border']};
    border-radius: {r['sm']}px;
    padding: 5px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {c['accent']}88;
}}

/* 下拉框 */
QComboBox {{
    background-color: {c['input_bg']};
    color: {c['text']};
    border: 1px solid {c['input_border']};
    border-radius: {r['sm']}px;
    padding: 5px;
}}
QComboBox:hover {{
    border-color: {c['accent']}66;
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

/* 数字输入 */
QSpinBox, QDoubleSpinBox {{
    background-color: {c['input_bg']};
    color: {c['text']};
    border: 1px solid {c['input_border']};
    border-radius: {r['sm']}px;
    padding: 3px 6px;
    padding-right: 20px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c['accent']}88;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid {c['border']};
    border-bottom: 1px solid {c['border']};
    border-top-right-radius: {r['sm']}px;
    background-color: {c['button_bg']};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
    background-color: {c['button_hover']};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    width: 8px;
    height: 8px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid {c['border']};
    border-top: 1px solid {c['border']};
    border-bottom-right-radius: {r['sm']}px;
    background-color: {c['button_bg']};
}}
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {c['button_hover']};
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
}}

/* 列表/树/表格 */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {c['tree_bg']};
    color: {c['text']};
    border: 1px solid {c['border']};
    alternate-background-color: {c['table_alt']};
    border-radius: {r['sm']}px;
    gridline-color: {c['border']};
}}
QListWidget::item:selected, QTreeWidget::item:selected, QTableWidget::item:selected {{
    background-color: {c['selection']};
    color: {c['text_bright']};
}}
QListWidget::item:hover, QTreeWidget::item:hover {{
    background-color: {c['highlight']}44;
}}
QTableWidget::item {{
    padding: 3px 6px;
}}
QHeaderView::section {{
    background-color: {c['table_header']};
    color: {c['text']};
    border: 1px solid {c['border']};
    padding: 5px 8px;
    font-weight: bold;
}}

/* 滚动条 */
QScrollBar:vertical {{
    background-color: {c['background']};
    width: 10px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {c['scrollbar']};
    border-radius: 5px;
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
    height: 10px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {c['scrollbar']};
    border-radius: 5px;
    min-width: 30px;
    margin: 2px;
}}
QScrollBar::handle:horizontal:hover {{
    background-color: {c['scrollbar_hover']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* 分组框 */
QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: {r['md']}px;
    margin-top: 12px;
    padding-top: 14px;
    font-weight: bold;
    color: {c['accent']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {c['accent']};
}}

/* 进度条 */
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

/* 滑块 */
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

/* 停靠面板 */
QDockWidget {{
    color: {c['text']};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background-color: {c['panel']};
    padding: 6px 10px;
    border-bottom: 1px solid {c['border']};
    font-weight: bold;
}}

/* 工具提示 */
QToolTip {{
    background-color: {c['panel']};
    color: {c['text']};
    border: 1px solid {c['accent']}88;
    padding: 6px;
    font-size: {f['size_small']}px;
}}

/* 分割器 */
QSplitter::handle {{
    background-color: {c['border']};
}}
QSplitter::handle:horizontal {{
    width: 3px;
}}
QSplitter::handle:vertical {{
    height: 3px;
}}

/* 搜索框 */
QLineEdit#search_box {{
    border-radius: 15px;
    padding: 6px 16px;
}}

/* 复选框/单选框 */
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
QCheckBox {{
    spacing: 6px;
}}
QCheckBox:hover {{
    color: {c['text_bright']};
}}
"""
