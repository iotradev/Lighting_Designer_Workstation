"""
色彩设计器 (ColorDesigner)
照明色彩设计与管理工具
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSlider, QLineEdit, QSpinBox,
    QTabWidget, QListWidget, QListWidgetItem, QFileDialog,
    QColorDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont
from ui.base_window import BaseToolWindow

# Lee 色片库
LEE_GELS = [
    ("Lee 001", "Primary Red", "#FF0000"),
    ("Lee 002", "Medium Red", "#CC0000"),
    ("Lee 003", "Follies Pink", "#FF6699"),
    ("Lee 004", "Bastard Amber", "#FF9933"),
    ("Lee 005", "Rose Pink", "#FF3366"),
    ("Lee 009", "Pale Yellow", "#FFFF66"),
    ("Lee 10", "Middle Rose", "#FF6699"),
    ("Lee 12", "Straw", "#FFD699"),
    ("Lee 13", "Geezer Blue", "#3366FF"),
    ("Lee 14", "Medium Blue", "#0066FF"),
    ("Lee 15", "Deep Golden Amber", "#CC6600"),
    ("Lee 17", "Flame Red", "#FF3300"),
    ("Lee 18", "Fire", "#FF6600"),
    ("Lee 20", "Deep Amber", "#CC9900"),
    ("Lee 21", "Golden Amber", "#FFCC00"),
    ("Lee 24", "Scarlet", "#FF2200"),
    ("Lee 25", "Orange Red", "#FF4400"),
    ("Lee 26", "Bright Red", "#EE0000"),
    ("Lee 34", "Golden Green", "#99CC00"),
    ("Lee 36", "Medium Violet", "#9933CC"),
    ("Lee 39", "Spec. Lavender", "#9966CC"),
    ("Lee 48", "Rose Purple", "#993366"),
    ("Lee 51", "Surprise Pink", "#FF33CC"),
    ("Lee 52", "Light Lavender", "#CC99FF"),
    ("Lee 54", "Special Pink", "#FF66CC"),
    ("Lee 57", "Coral", "#FF6666"),
    ("Lee 60", "No Color Blue", "#3333CC"),
    ("Lee 61", "No Color Pink", "#FF0066"),
    ("Lee 63", "Pale Blue", "#99CCFF"),
    ("Lee 64", "Light Amber", "#FFCC66"),
    ("Lee 65", "Daylight Blue", "#6699FF"),
    ("Lee 68", "Sky Blue", "#3399FF"),
    ("Lee 71", "Tokyo Blue", "#0066CC"),
    ("Lee 73", "Evening Blue", "#003399"),
    ("Lee 74", "Night Blue", "#000066"),
    ("Lee 79", "Just Blue", "#0033CC"),
    ("Lee 85", "Deep Orange", "#CC4400"),
    ("Lee 86", "Pea Green", "#66CC00"),
    ("Lee 87", "Pale Lavender", "#CC99FF"),
    ("Lee 89", "Muscular Blue", "#0033FF"),
    ("Lee 90", "Dark Yellow Green", "#669900"),
    ("Lee 93", "Blue Green", "#006666"),
    ("Lee 95", "Medium Blue Green", "#009999"),
    ("Lee 96", "Aquamarine", "#33CCCC"),
    ("Lee 99", "Chocolate", "#663300"),
    ("Lee 100", "Spring Yellow", "#CCFF00"),
    ("Lee 101", "Quneut", "#339933"),
    ("Lee 102", "Light Amber", "#FFCC33"),
    ("Lee 103", "Straw", "#FFD699"),
    ("Lee 104", "Golden Amber", "#FF9900"),
    ("Lee 105", "Orange", "#FF6600"),
    ("Lee 106", "Primary Green", "#00CC00"),
    ("Lee 107", "Rich Purple", "#660066"),
    ("Lee 108", "English Rose", "#FF9999"),
    ("Lee 110", "School Bus", "#FF9900"),
    ("Lee 111", "Use Me", "#FFCC00"),
    ("Lee 113", "Magenta", "#FF00FF"),
    ("Lee 115", "Goddess Gold", "#FFB847"),
    ("Lee 116", "Medium Purple", "#9933FF"),
    ("Lee 117", "Steel Blue", "#336699"),
    ("Lee 118", "Light Green", "#66FF66"),
    ("Lee 119", "Dark Green", "#006600"),
    ("Lee 120", "Dark Blue", "#000099"),
    ("Lee 121", "Lee Gold", "#FFD700"),
    ("Lee 122", "Fern Green", "#339933"),
    ("Lee 124", "Dark Steel Blue", "#1A3C6E"),
    ("Lee 126", "Mauve", "#996699"),
    ("Lee 128", "Bright Pink", "#FF0080"),
    ("Lee 131", "Marine Blue", "#004C99"),
    ("Lee 132", "Medium Amber", "#CC8800"),
    ("Lee 134", "Chocolate", "#663300"),
    ("Lee 135", "Deep Blue", "#000080"),
    ("Lee 136", "Pale Lavender", "#B8A9FF"),
    ("Lee 137", "Special Lavender", "#9966FF"),
    ("Lee 138", "Pale Green", "#99FF99"),
    ("Lee 139", "Safari Blue", "#3399CC"),
    ("Lee 141", "Bright Red", "#CC0000"),
    ("Lee 142", "Artic Blue", "#003366"),
    ("Lee 146", "Rust", "#CC3300"),
    ("Lee 147", "Apricot", "#FF9966"),
    ("Lee 148", "Deep Red", "#800000"),
    ("Lee 150", "Golden Yellow", "#FFD700"),
    ("Lee 152", "Light Lavender", "#B8B8FF"),
    ("Lee 154", "Eye Blue", "#3399FF"),
    ("Lee 156", "Navy Blue", "#000080"),
    ("Lee 157", "Royal Blue", "#0033CC"),
    ("Lee 158", "Deep Lavender", "#663399"),
    ("Lee 161", "Slate Blue", "#556688"),
    ("Lee 162", "Bastard Amber", "#FF9966"),
    ("Lee 164", "Medium Amber", "#CC8800"),
    ("Lee 165", "Daylight Blue", "#6699FF"),
    ("Lee 166", "Plus Green", "#00FF00"),
    ("Lee 167", "Minus Green", "#FF00FF"),
    ("Lee 168", "Pale Blue", "#99CCFF"),
    ("Lee 169", "Lilac", "#CC66FF"),
    ("Lee 170", "Dk Violet", "#330066"),
    ("Lee 171", "Jasper", "#336633"),
    ("Lee 172", "Deep Lavender", "#660099"),
    ("Lee 173", "Midnight Blue", "#000040"),
    ("Lee 174", "Deep Red", "#660000"),
    ("Lee 179", "Bluebell", "#6666FF"),
    ("Lee 180", "Lavender", "#9999FF"),
    ("Lee 181", "Eighth White", "#EEEEEE"),
    ("Lee 182", "Quarter White", "#DDDDDD"),
    ("Lee 183", "Half White", "#CCCCCC"),
    ("Lee 200", "Double CT Blue", "#3366FF"),
    ("Lee 201", "Full CT Blue", "#6699FF"),
    ("Lee 202", "Half CT Blue", "#99BBFF"),
    ("Lee 203", "Quarter CT Blue", "#CCDDFF"),
    ("Lee 204", "Three Quarter CT Orange", "#FFAA44"),
    ("Lee 205", "Full CT Orange", "#FF9933"),
    ("Lee 206", "Half CT Orange", "#FFBB66"),
    ("Lee 207", "Quarter CT Orange", "#FFDD99"),
    ("Lee 208", "Eighth CT Orange", "#FFEECC"),
    ("Lee 209", "Half Plus Green", "#88FF88"),
    ("Lee 248", "Frost", "#DDDDDD"),
    ("Lee 250", "Half CT Blue", "#AABBDD"),
    ("Lee 281", "Three Quarter Minus Green", "#CC66CC"),
    ("Lee 285", "Three Quarter Plus Green", "#66CC66"),
    ("Lee 314", "Hamburg Frost", "#EEEEFF"),
    ("Lee 318", "Moonlight Blue", "#6688CC"),
    ("Lee 319", "Quiet Strand", "#CCBB99"),
    ("Lee 320", "Electric Lavender", "#9966FF"),
    ("Lee 322", "Urban Blue", "#3366AA"),
    ("Lee 323", "Cosmetic Peach", "#FFBB99"),
    ("Lee 324", "Cosmetic Rouge", "#FF9999"),
    ("Lee 328", "Filter Template", "#CCCCCC"),
    ("Lee 329", "Glamour Gold", "#FFCC33"),
    ("Lee 331", "Nightingale", "#665544"),
    ("Lee 332", "Blonde", "#FFDD88"),
    ("Lee 333", "Dusty Pink", "#CC9999"),
    ("Lee 334", "Pale Gold", "#FFDD66"),
    ("Lee 335", "Marine Blue", "#004466"),
    ("Lee 336", "Lincoln Green", "#336600"),
    ("Lee 337", "Dark Steel Blue", "#224466"),
    ("Lee 338", "Teal Blue", "#006688"),
    ("Lee 339", "Eggshell", "#CCBB99"),
    ("Lee 340", "Med. Blue", "#0055AA"),
    ("Lee 341", "Salmon", "#FF8866"),
    ("Lee 342", "Just Blue", "#0044AA"),
    ("Lee 343", "Navy Blue", "#002244"),
    ("Lee 344", "CT Orange", "#FF8800"),
    ("Lee 345", "Golden Amber", "#FF9900"),
    ("Lee 346", "Primary Red", "#FF0033"),
    ("Lee 347", "Rose Red", "#CC0033"),
    ("Lee 348", "Lavender", "#9966CC"),
    ("Lee 349", "Filter Green", "#009933"),
    ("Lee 350", "Petroleum Blue", "#003355"),
    ("Lee 351", "Bermuda Blue", "#3399AA"),
    ("Lee 352", "Sun Color Straw", "#FFCC66"),
    ("Lee 353", "Natalies Pink", "#FF6699"),
    ("Lee 354", "Rust", "#AA3300"),
]

# Rosco 色片库
ROSCO_GELS = [
    ("Rosco R00", "Clear", "#FFFFFF"),
    ("Rosco R01", "Light Bastard Amber", "#FFD4A0"),
    ("Rosco R02", "Bastard Amber", "#FFB878"),
    ("Rosco R03", "Dark Bastard Amber", "#FF9C50"),
    ("Rosco R04", "Medium Amber", "#FFA028"),
    ("Rosco R05", "Light Straw", "#FFE0A0"),
    ("Rosco R06", "No Color Pink", "#FF8888"),
    ("Rosco R07", "Pale Yellow", "#FFF8D8"),
    ("Rosco R08", "Pale Gold", "#FFECB0"),
    ("Rosco R09", "Pale Amber Gold", "#FFE088"),
    ("Rosco R10", "Medium Yellow", "#FFF000"),
    ("Rosco R11", "Light Straw", "#FFE8B0"),
    ("Rosco R12", "Straw", "#FFD888"),
    ("Rosco R13", "Medium Straw", "#FFD060"),
    ("Rosco R14", "Dark Straw", "#FFC838"),
    ("Rosco R15", "Deep Amber", "#FFB800"),
    ("Rosco R16", "Light Lemon", "#FFFF88"),
    ("Rosco R17", "Flame Red", "#FF2200"),
    ("Rosco R18", "Fire Red", "#FF4400"),
    ("Rosco R19", "Fire", "#FF6600"),
    ("Rosco R20", "Medium Amber", "#FFAA00"),
    ("Rosco R21", "Golden Amber", "#FFBB00"),
    ("Rosco R22", "Deep Amber", "#FF9900"),
    ("Rosco R23", "Orange", "#FF7700"),
    ("Rosco R24", "Scarlet", "#FF2200"),
    ("Rosco R25", "Red", "#FF0000"),
    ("Rosco R26", "Light Red", "#FF3333"),
    ("Rosco R27", "Medium Red", "#DD0000"),
    ("Rosco R28", "Turkey Red", "#BB0000"),
    ("Rosco R29", "Bright Red", "#FF0000"),
    ("Rosco R30", "Dark Primary Red", "#990000"),
    ("Rosco R31", "Rose", "#FF6699"),
    ("Rosco R32", "Medium Rose", "#FF3366"),
    ("Rosco R33", "No Color Pink", "#FF8888"),
    ("Rosco R34", "Flesh Pink", "#FFBBAA"),
    ("Rosco R35", "Light Pink", "#FFAACC"),
    ("Rosco R36", "Medium Pink", "#FF88BB"),
    ("Rosco R37", "Pink", "#FF66AA"),
    ("Rosco R38", "Ruby", "#CC0044"),
    ("Rosco R39", "Primary Red", "#FF0033"),
    ("Rosco R40", "Lavender", "#9966CC"),
    ("Rosco R41", "Salmon", "#FF8866"),
    ("Rosco R42", "Deep Salmon", "#CC5533"),
    ("Rosco R43", "Eighth White", "#EEEEEE"),
    ("Rosco R44", "Quarter White", "#DDDDDD"),
    ("Rosco R45", "Half White", "#CCCCCC"),
    ("Rosco R46", "Three Quarter White", "#BBBBBB"),
    ("Rosco R47", "Rose Purple", "#993366"),
    ("Rosco R48", "Mauve", "#996699"),
    ("Rosco R49", "Medium Purple", "#663399"),
    ("Rosco R50", "Magenta", "#FF00FF"),
    ("Rosco R51", "Surprise Pink", "#FF33FF"),
    ("Rosco R52", "Light Lavender", "#CC99FF"),
    ("Rosco R53", "Pale Lavender", "#B8A9FF"),
    ("Rosco R54", "Special Lavender", "#9977FF"),
    ("Rosco R55", "Lilac", "#CC66FF"),
    ("Rosco R56", "Gorgeous Green", "#00CC66"),
    ("Rosco R57", "Jade Green", "#00CC99"),
    ("Rosco R58", "Dark Green", "#006633"),
    ("Rosco R59", "Indigo", "#330066"),
    ("Rosco R60", "No Color Blue", "#3366FF"),
    ("Rosco R61", "No Color Blue", "#0066FF"),
    ("Rosco R62", "Bastard Amber", "#FF9966"),
    ("Rosco R63", "Pale Blue", "#99CCFF"),
    ("Rosco R64", "Light Amber", "#FFCC66"),
    ("Rosco R65", "Daylight Blue", "#6699FF"),
    ("Rosco R66", "Cool Blue", "#0066CC"),
    ("Rosco R67", "Light Sky Blue", "#66BBFF"),
    ("Rosco R68", "Sky Blue", "#3399FF"),
    ("Rosco R69", "Brilliant Blue", "#0088FF"),
    ("Rosco R70", "Plum", "#660044"),
    ("Rosco R71", "Tokyo Blue", "#0066CC"),
    ("Rosco R72", "Deep Blue", "#003399"),
    ("Rosco R73", "Evening Blue", "#003399"),
    ("Rosco R74", "Night Blue", "#000066"),
    ("Rosco R75", "Twilight Blue", "#001144"),
    ("Rosco R76", "Medium Blue", "#0044CC"),
    ("Rosco R77", "Green Blue", "#006699"),
    ("Rosco R78", "Azure Blue", "#0099CC"),
    ("Rosco R79", "Just Blue", "#0033CC"),
    ("Rosco R80", "Primary Blue", "#0000FF"),
    ("Rosco R81", "Urban Blue", "#3366AA"),
    ("Rosco R82", "Blue Ice", "#99CCFF"),
    ("Rosco R83", "Medium Blue Green", "#009999"),
    ("Rosco R84", "Aquamarine", "#33CCCC"),
    ("Rosco R85", "Deep Orange", "#CC4400"),
    ("Rosco R86", "Pea Green", "#66CC00"),
    ("Rosco R87", "Pale Lavender", "#CC99FF"),
    ("Rosco R88", "Light Blue", "#6699FF"),
    ("Rosco R89", "Muscular Blue", "#0044FF"),
    ("Rosco R90", "Dark Yellow Green", "#669900"),
    ("Rosco R91", "Primary Green", "#00FF00"),
    ("Rosco R92", "Medium Blue Green", "#009999"),
    ("Rosco R93", "Blue Green", "#006666"),
    ("Rosco R94", "Kelly Green", "#33CC33"),
    ("Rosco R95", "Medium Blue Green", "#00AAAA"),
    ("Rosco R96", "Aquamarine", "#33CCCC"),
    ("Rosco R97", "Steel Blue", "#336699"),
    ("Rosco R98", "Chromatic Green", "#00CC66"),
    ("Rosco R99", "Chocolate", "#663300"),
    ("Rosco R100", "Yellow Green", "#99CC00"),
    ("Rosco R101", "Q Blue", "#006699"),
    ("Rosco R102", "Light Amber", "#FFCC33"),
    ("Rosco R103", "Straw", "#FFD699"),
    ("Rosco R104", "Golden Amber", "#FF9900"),
    ("Rosco R105", "Orange", "#FF6600"),
    ("Rosco R106", "Primary Green", "#00CC00"),
    ("Rosco R107", "Rich Purple", "#660066"),
    ("Rosco R108", "English Rose", "#FF9999"),
    ("Rosco R322", "Glacier Blue", "#C0DDFF"),
]


class ColorSwatchWidget(QWidget):
    """大色块预览"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor(255, 255, 255)
        self.setMinimumSize(200, 150)
    
    def set_color(self, color):
        self.color = color
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 背景棋盘格（透明度指示）
        check_size = 10
        for x in range(0, w, check_size):
            for y in range(0, h, check_size):
                c = QColor(200, 200, 200) if (x // check_size + y // check_size) % 2 == 0 else QColor(255, 255, 255)
                painter.fillRect(x, y, check_size, check_size, c)
        
        # 颜色色块
        painter.fillRect(0, 0, w, h, self.color)
        
        # 边框
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawRect(0, 0, w - 1, h - 1)
        
        # 显示颜色值
        painter.setPen(QColor(255, 255, 255) if self.color.lightness() < 128 else QColor(0, 0, 0))
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        painter.setFont(font)
        
        hex_color = self.color.name().upper()
        painter.drawText(10, 30, hex_color)
        
        font.setPointSize(9)
        painter.setFont(font)
        r, g, b = self.color.red(), self.color.green(), self.color.blue()
        painter.drawText(10, 50, f"RGB: {r}, {g}, {b}")
        
        c, m, y = 255 - r, 255 - g, 255 - b
        painter.drawText(10, 70, f"CMY: {c}, {m}, {y}")
        
        painter.end()


class ColorDesigner(BaseToolWindow):
    def __init__(self):
        super().__init__('ColorDesigner', '色彩设计器', '1.0.0', 1100, 800)
        self.current_color = QColor(255, 255, 255)
        self.palette = []
        self.palette_file = Path(__file__).parent / 'palettes' / 'default.json'
        self._setup_ui()
        self._load_palette_file()
    
    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        
        # 顶部：色块预览 + 信息
        top_layout = QHBoxLayout()
        
        self.swatch = ColorSwatchWidget()
        self.swatch.setMinimumSize(250, 150)
        top_layout.addWidget(self.swatch)
        
        info_layout = QGridLayout()
        info_layout.addWidget(QLabel("十六进制:"), 0, 0)
        self.hex_edit = QLineEdit("#FFFFFF")
        self.hex_edit.returnPressed.connect(self._on_hex_changed)
        info_layout.addWidget(self.hex_edit, 0, 1)
        
        info_layout.addWidget(QLabel("RGB:"), 1, 0)
        self.rgb_label = QLabel("255, 255, 255")
        info_layout.addWidget(self.rgb_label, 1, 1)
        
        info_layout.addWidget(QLabel("CMY:"), 2, 0)
        self.cmy_label = QLabel("0, 0, 0")
        info_layout.addWidget(self.cmy_label, 2, 1)
        
        info_layout.addWidget(QLabel("色温 (K):"), 3, 0)
        self.kelvin_label = QLabel("--")
        info_layout.addWidget(self.kelvin_label, 3, 1)
        
        btn_pick = QPushButton("拾取颜色...")
        btn_pick.clicked.connect(self._pick_color)
        info_layout.addWidget(btn_pick, 4, 0, 1, 2)
        
        top_layout.addLayout(info_layout)
        main_layout.addLayout(top_layout)
        
        # 标签页
        tabs = QTabWidget()
        tabs.addTab(self._create_rgb_tab(), "RGB 混合器")
        tabs.addTab(self._create_cmy_tab(), "CMY 混合器")
        tabs.addTab(self._create_kelvin_tab(), "色温转换")
        tabs.addTab(self._create_gel_tab(), "色片库")
        tabs.addTab(self._create_palette_tab(), "调色板")
        main_layout.addWidget(tabs)
        
        self.set_central_content(main_widget)
    
    def _create_slider_row(self, label, min_val, max_val, callback):
        """创建滑块行"""
        layout = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(30)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(min_val, max_val)
        slider.valueChanged.connect(callback)
        val_label = QLabel(str(min_val))
        val_label.setFixedWidth(40)
        slider.valueChanged.connect(lambda v: val_label.setText(str(v)))
        layout.addWidget(lbl)
        layout.addWidget(slider)
        layout.addWidget(val_label)
        return layout, slider
    
    def _create_rgb_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("RGB 色彩混合器"))
        
        r_layout, self.r_slider = self._create_slider_row("R", 0, 255, self._on_rgb_changed)
        layout.addLayout(r_layout)
        
        g_layout, self.g_slider = self._create_slider_row("G", 0, 255, self._on_rgb_changed)
        layout.addLayout(g_layout)
        
        b_layout, self.b_slider = self._create_slider_row("B", 0, 255, self._on_rgb_changed)
        layout.addLayout(b_layout)
        
        btn = QPushButton("应用 RGB")
        btn.clicked.connect(self._on_rgb_changed)
        layout.addWidget(btn)
        
        layout.addStretch()
        return widget
    
    def _create_cmy_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("CMY 色彩混合器"))
        
        c_layout, self.c_slider = self._create_slider_row("C", 0, 100, self._on_cmy_changed)
        layout.addLayout(c_layout)
        
        m_layout, self.m_slider = self._create_slider_row("M", 0, 100, self._on_cmy_changed)
        layout.addLayout(m_layout)
        
        y_layout, self.y_slider = self._create_slider_row("Y", 0, 100, self._on_cmy_changed)
        layout.addLayout(y_layout)
        
        btn = QPushButton("应用 CMY")
        btn.clicked.connect(self._on_cmy_changed)
        layout.addWidget(btn)
        
        layout.addStretch()
        return widget
    
    def _create_kelvin_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("色温转换器 (开尔文 → RGB)"))
        
        kelvin_layout = QHBoxLayout()
        kelvin_layout.addWidget(QLabel("色温 (K):"))
        self.kelvin_spin = QSpinBox()
        self.kelvin_spin.setRange(2000, 10000)
        self.kelvin_spin.setValue(5600)
        self.kelvin_spin.setSingleStep(100)
        kelvin_layout.addWidget(self.kelvin_spin)
        
        btn = QPushButton("转换")
        btn.clicked.connect(self._on_kelvin_changed)
        kelvin_layout.addWidget(btn)
        layout.addLayout(kelvin_layout)
        
        layout.addWidget(QLabel("预设色温:"))
        presets = [
            ("蜡烛", 1900), ("白炽灯", 2700), ("卤素灯", 3200),
            ("日出/日落", 3500), ("荧光灯", 4200), ("正午阳光", 5600),
            ("阴天", 6500), ("蓝天", 8000), ("北方天空", 10000)
        ]
        preset_layout = QGridLayout()
        for i, (name, kelvin) in enumerate(presets):
            btn = QPushButton(f"{name}\n{kelvin}K")
            btn.setFixedHeight(45)
            btn.clicked.connect(lambda checked, k=kelvin: self._set_kelvin(k))
            preset_layout.addWidget(btn, i // 3, i % 3)
        layout.addLayout(preset_layout)
        
        layout.addStretch()
        return widget
    
    def _create_gel_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("搜索:"))
        self.gel_filter = QLineEdit()
        self.gel_filter.setPlaceholderText("输入色片名称或编号...")
        self.gel_filter.textChanged.connect(self._filter_gels)
        filter_layout.addWidget(self.gel_filter)
        layout.addLayout(filter_layout)
        
        self.gel_list = QListWidget()
        self.gel_list.setIconSize(self.gel_list.iconSize())  # 确保有图标大小
        self.gel_list.itemClicked.connect(self._on_gel_clicked)
        layout.addWidget(self.gel_list)
        
        # 填充色片列表
        self._populate_gels()
        
        return widget
    
    def _create_palette_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 调色板预览区域
        self.palette_scroll = QScrollArea()
        self.palette_widget = QWidget()
        self.palette_layout = QGridLayout(self.palette_widget)
        self.palette_scroll.setWidget(self.palette_widget)
        self.palette_scroll.setWidgetResizable(True)
        layout.addWidget(self.palette_scroll)
        
        btn_layout = QHBoxLayout()
        btn_save_color = QPushButton("添加当前颜色")
        btn_save_color.clicked.connect(self._add_to_palette)
        btn_layout.addWidget(btn_save_color)
        
        btn_save_file = QPushButton("保存调色板")
        btn_save_file.clicked.connect(self._save_palette_file)
        btn_layout.addWidget(btn_save_file)
        
        btn_load_file = QPushButton("加载调色板")
        btn_load_file.clicked.connect(self._load_palette_file)
        btn_layout.addWidget(btn_load_file)
        
        btn_clear = QPushButton("清空调色板")
        btn_clear.clicked.connect(self._clear_palette)
        btn_layout.addWidget(btn_clear)
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _set_color(self, color):
        """设置当前颜色并更新所有显示"""
        self.current_color = QColor(color)
        self.swatch.set_color(self.current_color)
        self.hex_edit.setText(self.current_color.name().upper())
        
        r, g, b = self.current_color.red(), self.current_color.green(), self.current_color.blue()
        self.rgb_label.setText(f"{r}, {g}, {b}")
        c, m, y = 255 - r, 255 - g, 255 - b
        self.cmy_label.setText(f"{c}, {m}, {y}")
        
        # 更新滑块（断开信号避免循环）
        self.r_slider.blockSignals(True)
        self.r_slider.setValue(r)
        self.r_slider.blockSignals(False)
        self.g_slider.blockSignals(True)
        self.g_slider.setValue(g)
        self.g_slider.blockSignals(False)
        self.b_slider.blockSignals(True)
        self.b_slider.setValue(b)
        self.b_slider.blockSignals(False)
        
        self.c_slider.blockSignals(True)
        self.c_slider.setValue(c)
        self.c_slider.blockSignals(False)
        self.m_slider.blockSignals(True)
        self.m_slider.setValue(m)
        self.m_slider.blockSignals(False)
        self.y_slider.blockSignals(True)
        self.y_slider.setValue(y)
        self.y_slider.blockSignals(False)
        
        self._update_palette_display()
    
    def _on_rgb_changed(self):
        r = self.r_slider.value()
        g = self.g_slider.value()
        b = self.b_slider.value()
        self._set_color(QColor(r, g, b))
    
    def _on_cmy_changed(self):
        c = self.c_slider.value()
        m = self.m_slider.value()
        y = self.y_slider.value()
        r = 255 - int(c * 2.55)
        g = 255 - int(m * 2.55)
        b = 255 - int(y * 2.55)
        self._set_color(QColor(r, g, b))
    
    def _on_hex_changed(self):
        hex_val = self.hex_edit.text().strip()
        if not hex_val.startswith('#'):
            hex_val = '#' + hex_val
        color = QColor(hex_val)
        if color.isValid():
            self._set_color(color)
    
    def _on_kelvin_changed(self):
        self._set_kelvin(self.kelvin_spin.value())
    
    def _set_kelvin(self, kelvin):
        """色温转RGB (Tanner Helland算法)"""
        temp = kelvin / 100.0
        
        # 红色
        if temp <= 66:
            r = 255
        else:
            r = temp - 60
            r = 329.698727446 * (r ** -0.1332047592)
            r = max(0, min(255, int(r)))
        
        # 绿色
        if temp <= 66:
            g = temp
            g = 99.4708025861 * (g ** 0.1332047592) - 16.1105021076
        else:
            g = temp - 60
            g = 288.1221695283 * (g ** -0.0755148492)
        g = max(0, min(255, int(g)))
        
        # 蓝色
        if temp >= 66:
            b = 255
        elif temp <= 19:
            b = 0
        else:
            b = temp - 10
            b = 138.5177312231 * (b ** 0.1332047592) - 305.0447927307
            b = max(0, min(255, int(b)))
        
        self.kelvin_spin.setValue(kelvin)
        self._set_color(QColor(r, g, b))
        self.kelvin_label.setText(f"{kelvin}K")
    
    def _populate_gels(self):
        """填充色片列表"""
        self.gel_list.clear()
        for code, name, hex_color in LEE_GELS + ROSCO_GELS:
            item = QListWidgetItem(f"{code} - {name}")
            color = QColor(hex_color)
            # 创建彩色图标
            pixmap = self._create_swatch_pixmap(color, 20, 20)
            from PySide6.QtGui import QPixmap
            if isinstance(pixmap, QPixmap):
                from PySide6.QtGui import QIcon
                item.setIcon(QIcon(pixmap))
            item.setData(Qt.ItemDataRole.UserRole, hex_color)
            self.gel_list.addItem(item)
    
    def _create_swatch_pixmap(self, color, w, h):
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(w, h)
        pixmap.fill(color)
        return pixmap
    
    def _filter_gels(self, text):
        """过滤色片列表"""
        text = text.lower()
        for i in range(self.gel_list.count()):
            item = self.gel_list.item(i)
            item.setHidden(text not in item.text().lower())
    
    def _on_gel_clicked(self, item):
        hex_color = item.data(Qt.ItemDataRole.UserRole)
        if hex_color:
            self._set_color(QColor(hex_color))
    
    def _pick_color(self):
        color = QColorDialog.getColor(self.current_color, self, "选择颜色")
        if color.isValid():
            self._set_color(color)
    
    def _add_to_palette(self):
        color = self.current_color.name().upper()
        if color not in self.palette:
            self.palette.append(color)
            self._update_palette_display()
            self.logger.info(f"添加颜色到调色板: {color}")
    
    def _update_palette_display(self):
        """更新调色板显示"""
        # 清除旧内容
        while self.palette_layout.count():
            item = self.palette_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for i, hex_color in enumerate(self.palette):
            btn = QPushButton(hex_color)
            btn.setFixedSize(80, 40)
            btn.setStyleSheet(f"background-color: {hex_color}; color: {'white' if QColor(hex_color).lightness() < 128 else 'black'}; font-weight: bold;")
            btn.clicked.connect(lambda checked, c=hex_color: self._set_color(QColor(c)))
            self.palette_layout.addWidget(btn, i // 6, i % 6)
    
    def _save_palette_file(self):
        path = self.palette_file.parent
        path.mkdir(parents=True, exist_ok=True)
        filepath, _ = QFileDialog.getSaveFileName(self, "保存调色板", str(self.palette_file), "JSON文件 (*.json)")
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({'palette': self.palette}, f, indent=2, ensure_ascii=False)
            self.palette_file = Path(filepath)
            self.logger.info(f"调色板已保存: {filepath}")
    
    def _load_palette_file(self):
        try:
            if self.palette_file.exists():
                with open(self.palette_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.palette = data.get('palette', [])
            self._update_palette_display()
        except Exception as e:
            self.logger.error(f"加载调色板失败: {e}")
    
    def _clear_palette(self):
        self.palette.clear()
        self._update_palette_display()


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = ColorDesigner()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "ColorDesigner - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
