# -*- coding: utf-8 -*-
"""
Lighting Designer Workstation - 图形启动器 v3
GrandMA3 风格深色主题 · 侧栏导航 · 动画效果 · 自定义标题栏
"""
import sys, os, subprocess, json
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QGridLayout,
    QLineEdit, QMessageBox, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QTimer
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPalette,
    QLinearGradient, QBrush, QPen
)

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "Config" / "launcher_config.json"
VERSION_FILE = BASE_DIR / "Config" / "version.json"


def _get_version():
    """从配置文件读取版本号"""
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", "1.0.0")
    except Exception:
        return "1.0.0"


APP_VERSION = _get_version()


# 查找系统 Python
def _find_python():
    """查找可用的 Python 解释器"""
    import shutil
    if not getattr(sys, "frozen", False):
        return sys.executable
    for name in ["python", "python3", "python.exe"]:
        found = shutil.which(name)
        if found:
            return found
    for p in [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python311" / "python.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python312" / "python.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Python" / "Python310" / "python.exe",
        Path("C:/Python311/python.exe"),
        Path("C:/Python312/python.exe"),
        Path("C:/Python310/python.exe"),
    ]:
        if p.exists():
            return str(p)
    return None


PYTHON_EXE = _find_python()


# 工具定义
CATEGORIES = [
    {"name": "音乐分析", "icon": "🎵", "color": "#e8912d",
     "tools": [
         ("BPM分析器", "BPMAnalyzer", "自动/实时BPM检测", "MusicAnalysis"),
         ("节拍检测器", "BeatDetector", "节拍/强弱拍识别", "MusicAnalysis"),
         ("频谱分析器", "AudioSpectrum", "FFT频谱分析", "MusicAnalysis"),
         ("音乐结构分析", "MusicStructureAnalyzer", "段落识别", "MusicAnalysis"),
         ("情绪分析器", "MoodAnalyzer", "情绪/能量曲线", "MusicAnalysis"),
     ]},
    {"name": "MIDI工具", "icon": "🎹", "color": "#569cd6",
     "tools": [
         ("MIDI监听器", "MIDIMonitor", "实时监听/日志", "MIDI"),
         ("MIDI发送器", "MIDISender", "发送/脚本/面板", "MIDI"),
         ("MIDI映射器", "MIDIMapper", "学习/按钮映射", "MIDI"),
         ("MIDI录制器", "MIDIRecorder", "录制/回放/导出", "MIDI"),
         ("时间码生成", "TimecodeGenerator", "SMPTE/MTC/LTC", "MIDI"),
         ("时间码监视", "TimecodeMonitor", "漂移检测/同步", "MIDI"),
     ]},
    {"name": "DMX/网络", "icon": "🌐", "color": "#4ec9b0",
     "tools": [
         ("DMX计算器", "DMXCalculator", "地址/通道计算", "DMX"),
         ("灯具配接器", "FixturePatcher", "Patch表/规划", "DMX"),
         ("DMX测试器", "DMXTester", "通道/故障检测", "DMX"),
         ("Art-Net监听", "ArtNetMonitor", "协议监听", "DMX"),
         ("sACN监听器", "sACNMonitor", "Universe分析", "DMX"),
         ("RDM管理", "RDMTool", "发现/参数读写", "DMX"),
     ]},
    {"name": "灯光设计", "icon": "🔦", "color": "#c586c0",
     "tools": [
         ("舞台平面图", "StagePlotDesigner", "灯位图绘制", "LightingDesign"),
         ("灯具数据库", "FixtureLibrary", "搜索/管理", "LightingDesign"),
         ("光束计算器", "BeamCalculator", "角度/覆盖计算", "LightingDesign"),
         ("照度计算器", "LuxCalculator", "照度/覆盖分析", "LightingDesign"),
         ("色彩设计器", "ColorDesigner", "RGB/CMY/Gel", "LightingDesign"),
         ("GOBO预览", "GoboPreviewer", "预览/旋转模拟", "LightingDesign"),
     ]},
    {"name": "视觉预演", "icon": "🎬", "color": "#dcdcaa",
     "tools": [
         ("视觉模拟器", "VisualSimulator", "3D灯光模拟", "VisualPreview"),
         ("像素映射器", "PixelMapper", "LED矩阵设计", "VisualPreview"),
     ]},
    {"name": "特效工程", "icon": "✅", "color": "#d16969",
     "tools": [
         ("激光规划器", "LaserPlanner", "区域/安全计算", "Effects"),
         ("特效设计器", "FXDesigner", "烟雾/CO2/焰火", "Effects"),
         ("功率计算器", "PowerCalculator", "功率/电流", "Engineering"),
         ("线缆计算器", "CableCalculator", "压降/线径", "Engineering"),
         ("配电规划器", "DistributionPlanner", "负载平衡", "Engineering"),
         ("UPS续航", "UPSCalculator", "续航计算", "Engineering"),
         ("发电机容量", "GeneratorCalculator", "容量计算", "Engineering"),
     ]},
    {"name": "演出管理", "icon": "🎭", "color": "#4ec9b0",
     "tools": [
         ("演出管理器", "ShowManager", "项目/场景/Cue", "ShowManagement"),
         ("CUE设计器", "CueDesigner", "Cue/Chase/效果", "ShowManagement"),
         ("时间轴编辑", "TimelineEditor", "音乐同步", "ShowManagement"),
         ("节目单生成", "CueSheetGenerator", "Cue Sheet", "ShowManagement"),
         ("设备清单", "EquipmentListGenerator", "清单生成", "ShowManagement"),
         ("备份管理器", "BackupManager", "自动备份", "ShowManagement"),
     ]},
    {"name": "AI辅助", "icon": "🤖", "color": "#e8912d",
     "tools": [
         ("AI灯光助手", "AILightingDesigner", "灯光建议", "AI"),
         ("AI编程助手", "AIProgrammingAssistant", "Chase/效果", "AI"),
         ("AI舞美助手", "AIStageDesigner", "布局建议", "AI"),
         ("AI故障诊断", "AITroubleshooter", "故障诊断", "AI"),
     ]},
]


def _load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"recent_tools": [], "favorites": [], "window_geometry": None}


def _save_config(cfg):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class SplashScreen(QWidget):
    """启动画面"""
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 280)
        self._progress = 0
        self._status = "正在初始化..."
        self._dots = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(60)

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self._progress = min(100, self._progress + 4)
        steps = [(15, "检查依赖"), (35, "加载主题"), (55, "初始化工具"), (75, "扫描插件"), (92, "准备界面")]
        for t, s in steps:
            if self._progress >= t and self._progress < t + 15:
                self._status = s
        self.update()
        if self._progress >= 100:
            self._anim_timer.stop()
            QTimer.singleShot(200, self.close)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(18, 18, 28, 245))
        p.setPen(QPen(QColor("#e8912d"), 2))
        p.drawRoundedRect(0, 0, 460, 280, 14, 14)
        p.setFont(QFont("Segoe UI", 38))
        p.setPen(QColor("#e8912d"))
        p.drawText(0, 20, 460, 55, Qt.AlignmentFlag.AlignCenter, "💡")
        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        p.setPen(QColor("#ffffff"))
        p.drawText(0, 72, 460, 28, Qt.AlignmentFlag.AlignCenter, "Lighting Designer Workstation")
        p.setFont(QFont("Microsoft YaHei UI", 9))
        p.setPen(QColor("#777"))
        p.drawText(0, 98, 460, 18, Qt.AlignmentFlag.AlignCenter, f"舞台灯光设计工作站  v{APP_VERSION}")
        bx, by, bw, bh = 50, 150, 360, 5
        p.setBrush(QColor(40, 40, 55))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(bx, by, bw, bh, 2, 2)
        fw = int(bw * self._progress / 100)
        g = QLinearGradient(bx, 0, bx + bw, 0)
        g.setColorAt(0, QColor("#e8912d"))
        g.setColorAt(1, QColor("#f5a623"))
        p.setBrush(QBrush(g))
        p.drawRoundedRect(bx, by, fw, bh, 2, 2)
        p.setFont(QFont("Microsoft YaHei UI", 8))
        p.setPen(QColor("#999"))
        p.drawText(0, 168, 460, 16, Qt.AlignmentFlag.AlignCenter, f"{self._status}{'.' * self._dots}")
        p.setFont(QFont("Consolas", 7))
        p.setPen(QColor("#444"))
        p.drawText(0, 248, 460, 14, Qt.AlignmentFlag.AlignCenter,
                   f"Python {sys.version.split()[0]}  ·  PySide6  ·  Qt6")
        p.end()


class TitleBar(QFrame):
    """自定义无边框标题栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._parent = parent
        self.setFixedHeight(46)
        self.setObjectName("titlebar")
        self.setStyleSheet("""
            QFrame#titlebar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
                border-bottom: 1px solid #e8912d44;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        logo = QLabel("💡")
        logo.setFont(QFont("Segoe UI", 16))
        logo.setStyleSheet("color: #e8912d; background: transparent;")
        layout.addWidget(logo)

        title = QLabel("Lighting Designer Workstation")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(title)

        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet("color: #e8912d; font-size: 16px; background: transparent;")
        layout.addWidget(ver)
        layout.addStretch()

        total = sum(len(c["tools"]) for c in CATEGORIES)
        stats = QLabel(f"{len(CATEGORIES)} 分类 · {total} 工具")
        stats.setStyleSheet("color: #888; font-size: 16px; background: transparent;")
        layout.addWidget(stats)

        btn_min = QPushButton("—")
        btn_min.setFixedSize(32, 28)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setStyleSheet("""
            QPushButton { background: transparent; color: #aaa; border: none; font-size: 16px; }
            QPushButton:hover { background: #333; color: #fff; border: none; font-size: 16px; }
        """)
        btn_min.clicked.connect(lambda: parent.showMinimized() if parent else None)
        layout.addWidget(btn_min)

        self._btn_max = QPushButton("☐")
        self._btn_max.setFixedSize(32, 28)
        self._btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_max.setStyleSheet(btn_min.styleSheet())
        self._btn_max.clicked.connect(self._toggle_max)
        layout.addWidget(self._btn_max)

        btn_close = QPushButton("✕")
        btn_close.setFixedSize(32, 28)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton { background: transparent; color: #aaa; border: none; font-size: 16px; }
            QPushButton:hover { background: #e81123; color: #fff; }
        """)
        btn_close.clicked.connect(lambda: parent.close() if parent else None)
        layout.addWidget(btn_close)

    def _toggle_max(self):
        if self._parent:
            if self._parent.isMaximized():
                self._parent.showNormal()
                self._btn_max.setText("☐")
            else:
                self._parent.showMaximized()
                self._btn_max.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.pos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_drag_pos") and event.buttons() == Qt.MouseButton.LeftButton:
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class ToolButton(QPushButton):
    """Tool button with hover effect"""
    def __init__(self, name, desc, color, parent=None):
        super().__init__(parent)
        self.accent = color
        self.setText(f"  {name}")
        self.setToolTip(desc)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(38)
        self.setMinimumWidth(160)
        self.setStyleSheet(f"""
            QPushButton {{
                background: #2a2a2d;
                color: #ccc;
                border: 1px solid #333;
                border-left: 3px solid transparent;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: #333;
                color: #fff;
                border-left: 3px solid {color}88;
            }}
        """)


class CategoryCard(QFrame):
    """分类卡片"""
    tool_launched = None

    def __init__(self, category, parent=None):
        super().__init__(parent)
        self.category = category
        self.color = category["color"]
        self.setObjectName("catcard")
        self.setStyleSheet(f"""
            QFrame#catcard {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #252528, stop:1 #1e1e21);
                border: 1px solid #333;
                border-radius: 8px;
                border-top: 3px solid {self.color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        icon = QLabel(category["icon"])
        icon.setFont(QFont("Segoe UI Emoji", 14))
        icon.setFixedSize(24, 24)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(icon)
        name = QLabel(category["name"])
        name.setFont(QFont("Microsoft YaHei UI", 12, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {self.color}; background: transparent; border: none;")
        hdr.addWidget(name)
        hdr.addStretch()
        cnt = QLabel(f"{len(category['tools'])}")
        cnt.setStyleSheet(f"color: {self.color}66; font-size: 18px; font-weight: bold; background: transparent; border: none;")
        hdr.addWidget(cnt)
        layout.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {self.color}22; max-height: 1px; border: none;")
        layout.addWidget(sep)

        grid = QGridLayout()
        grid.setSpacing(3)
        for i, (name, exe, desc, folder) in enumerate(category["tools"]):
            btn = ToolButton(name, desc, self.color)
            btn.clicked.connect(lambda _, f=folder, e=exe: self._launch(f, e))
            grid.addWidget(btn, i // 2, i % 2)
        layout.addLayout(grid)

        # 统一卡片最小高度 (header 30 + separator 6 + 3行按钮 * 41 + padding 20)
        rows_needed = (len(category["tools"]) + 1) // 2
        min_h = 30 + 6 + rows_needed * 41 + 20
        self.setMinimumHeight(min_h)

    def _launch(self, folder, exe):
        script = BASE_DIR / "Tools" / folder / exe / "main.py"
        if not script.exists():
            QMessageBox.warning(self, "错误", f"找不到: {script}")
            return
        if not PYTHON_EXE:
            QMessageBox.critical(self, "未找到 Python",
                "需要安装 Python 3.10+ 才能运行工具。\n\n"
                "下载地址: https://www.python.org/downloads/\n\n"
                "安装时请勾选 'Add Python to PATH'")
            return
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(BASE_DIR)
            subprocess.Popen([PYTHON_EXE, str(script)], cwd=str(script.parent), env=env)
        except Exception as e:
            QMessageBox.critical(self, "启动失败",
                f"无法启动 {exe}:\n{type(e).__name__}: {e}")
            return
        if self.tool_launched:
            self.tool_launched.emit(folder, exe)


from PySide6.QtCore import Signal as _Signal
CategoryCard.tool_launched = _Signal(str, str)


class LauncherWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.config = _load_config()
        self.setMinimumSize(1050, 700)
        self.resize(1150, 780)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        if self.config.get("window_geometry"):
            try:
                self.restoreGeometry(bytes.fromhex(self.config["window_geometry"]))
            except Exception:
                pass

        QTimer.singleShot(0, self._ensure_visible)

        self.all_tools = {}
        for cat in CATEGORIES:
            for name, exe, desc, folder in cat["tools"]:
                self.all_tools[exe] = {"name": name, "exe": exe, "desc": desc, "folder": folder, "color": cat["color"]}

        self.setStyleSheet("""
            QMainWindow { background: #18181b; }
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { background: #18181b; width: 8px; }
            QScrollBar::handle:vertical { background: #333; border-radius: 4px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #444; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.setWindowTitle(f"Lighting Designer Workstation - v{APP_VERSION}")

        # Custom title bar for frameless window dragging
        title_bar = TitleBar(self)
        root.addWidget(title_bar)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # 侧栏
        self._sidebar_expanded = True
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setStyleSheet("background: #1a1a1d; border-right: 1px solid #2a2a2d;")
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(6, 8, 6, 8)
        sb_layout.setSpacing(2)

        # 搜索框
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索 ...")
        self.search_box.setFixedHeight(30)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #222; color: #ccc; border: 1px solid #333;
                border-radius: 5px; padding: 3px 8px; font-size: 12px;
            }
            QLineEdit:focus { border-color: #e8912d66; }
        """)
        self.search_box.textChanged.connect(self._on_search)
        self.search_box.returnPressed.connect(self._on_search_enter)
        sb_layout.addWidget(self.search_box)
        sb_layout.addSpacing(4)

        # "全部" 按钮
        self._all_btn = QPushButton(" ◉  全部工具")
        self._all_btn.setFixedHeight(34)
        self._all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._all_btn.setStyleSheet("""
            QPushButton {
                background: #e8912d22; color: #e8912d;
                border: 1px solid #e8912d44; border-left: 3px solid #e8912d;
                border-radius: 4px; padding: 4px 10px; font-size: 12px;
                font-weight: bold; text-align: left;
            }
            QPushButton:hover { background: #e8912d33; }
        """)
        self._all_btn.clicked.connect(lambda: self._filter_category(-1))
        sb_layout.addWidget(self._all_btn)

        self._active_cat = -1  # -1 = 全部
        self.cat_buttons = []
        self._cat_data = []  # 存储分类数据供折叠时用
        for i, cat in enumerate(CATEGORIES):
            btn = QPushButton(f" {cat['icon']}  {cat['name']}")
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._cat_style(cat["color"], False))
            btn.clicked.connect(lambda _, idx=i: self._filter_category(idx))
            sb_layout.addWidget(btn)
            self.cat_buttons.append(btn)
            self._cat_data.append(cat)

        sb_layout.addStretch()

        # 折叠/展开按钮
        self._toggle_btn = QPushButton("◀")
        self._toggle_btn.setFixedSize(30, 30)
        self._toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #555; border: none;
                font-size: 14px; border-radius: 4px;
            }
            QPushButton:hover { background: #333; color: #aaa; }
        """)
        self._toggle_btn.clicked.connect(self._toggle_sidebar)
        sb_layout.addWidget(self._toggle_btn, 0, Qt.AlignmentFlag.AlignBottom)

        content.addWidget(self.sidebar)

        # 右侧内容
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # 最近使用栏
        self.recent_bar = QFrame()
        self.recent_bar.setStyleSheet("background: #1e1e21; border-bottom: 1px solid #2a2a2d;")
        self.recent_bar.setFixedHeight(36)
        rb_layout = QHBoxLayout(self.recent_bar)
        rb_layout.setContentsMargins(16, 0, 16, 0)
        rb_layout.setSpacing(6)
        lbl = QLabel("⏱ 最近使用")
        lbl.setStyleSheet("color: #555; font-size: 12px; background: transparent;")
        rb_layout.addWidget(lbl)
        self.recent_btns_widget = QWidget()
        self.recent_btns_layout = QHBoxLayout(self.recent_btns_widget)
        self.recent_btns_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_btns_layout.setSpacing(4)
        rb_layout.addWidget(self.recent_btns_widget)
        rb_layout.addStretch()
        right.addWidget(self.recent_bar)

        # 分类卡片网格
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.grid = QGridLayout(scroll_content)
        self.grid.setContentsMargins(12, 10, 12, 10)
        self.grid.setSpacing(10)

        self.cards = []
        for i, cat in enumerate(CATEGORIES):
            card = CategoryCard(cat)
            card.tool_launched.connect(self._on_tool_launched)
            row, col = divmod(i, 2)
            self.grid.addWidget(card, row, col)
            self.cards.append(card)

        self.grid.setColumnStretch(0, 1)
        self.grid.setColumnStretch(1, 1)
        self.grid.setRowStretch(self.grid.rowCount(), 1)

        scroll.setWidget(scroll_content)
        right.addWidget(scroll, 1)

        # 底部状态栏
        footer = QFrame()
        footer.setFixedHeight(30)
        footer.setStyleSheet("background: #1a1a1d; border-top: 1px solid #2a2a2d;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 0, 12, 0)
        ver_label = QLabel(f"v{APP_VERSION}")
        ver_label.setStyleSheet("color:#666; font-size:11px; background:transparent;")
        fl.addWidget(ver_label)
        fl.addStretch()
        if PYTHON_EXE:
            py_name = Path(PYTHON_EXE).name
            py_status = QLabel(f"Python: {py_name}")
            py_status.setStyleSheet("color: #4ec9b0; font-size: 11px; background: transparent;")
        else:
            py_status = QLabel("⚠ 未安装Python")
            py_status.setStyleSheet("color: #ff6b6b; font-size: 11px; background: transparent;")
        fl.addWidget(py_status)
        fl.addSpacing(12)
        hint = QLabel("Ctrl+K 搜索 · Ctrl+B 抽屉 · Ctrl+Q 退出")
        hint.setStyleSheet("color: #555; font-size: 11px; background: transparent;")
        fl.addWidget(hint)
        right.addWidget(footer)

        content.addLayout(right, 1)
        root.addLayout(content, 1)

        # 快捷键
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Ctrl+K"), self, lambda: self.search_box.setFocus())
        QShortcut(QKeySequence("Escape"), self, self._clear_search)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)
        QShortcut(QKeySequence("Ctrl+B"), self, self._toggle_sidebar)

        self._update_recent()


    # -- Window dragging support --
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if hasattr(self, "_drag_pos") and self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _ensure_visible(self):
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if not geo.intersects(self.geometry()):
                self.move(geo.center() - self.rect().center())

    def _cat_style(self, color, active):
        if active:
            return f"""
                QPushButton {{
                    background: {color}22; color: {color};
                    border: 1px solid {color}44; border-left: 3px solid {color};
                    border-radius: 4px; padding: 6px 12px; font-size: 13px;
                    font-weight: bold; text-align: left;
                }}
            """
        return f"""
            QPushButton {{
                background: transparent; color: #aaa;
                border: 1px solid transparent; border-left: 3px solid transparent;
                border-radius: 4px; padding: 6px 12px; font-size: 13px; text-align: left;
            }}
            QPushButton:hover {{
                background: {color}11; color: {color};
                border-left: 3px solid {color}66;
            }}
        """

    def _toggle_sidebar(self):
        """切换侧栏抽屉：展开/收起"""
        self._sidebar_expanded = not self._sidebar_expanded
        if self._sidebar_expanded:
            self.sidebar.setFixedWidth(180)
            self._toggle_btn.setText("◀")
            self._toggle_btn.setToolTip("收起侧栏 (Ctrl+B)")
            self.search_box.show()
            self._all_btn.setText(" ◉  全部工具")
            for i, btn in enumerate(self.cat_buttons):
                cat = self._cat_data[i]
                btn.setText(f" {cat['icon']}  {cat['name']}")
                btn.setToolTip("")
        else:
            self.sidebar.setFixedWidth(50)
            self._toggle_btn.setText("▶")
            self._toggle_btn.setToolTip("展开侧栏 (Ctrl+B)")
            self.search_box.hide()
            self._all_btn.setText("◉")
            for i, btn in enumerate(self.cat_buttons):
                cat = self._cat_data[i]
                btn.setText(f"{cat['icon']}")
                btn.setToolTip(cat['name'])

    def _filter_category(self, idx):
        """过滤分类: -1=全部, 0-7=指定分类"""
        # 再次点击同一分类 = 恢复全部
        if self._active_cat == idx:
            idx = -1
        self._active_cat = idx

        # 更新侧栏按钮高亮
        is_all = (idx == -1)
        self._all_btn.setStyleSheet("""
            QPushButton {
                background: """ + ("#e8912d22" if is_all else "transparent") + """;
                color: """ + ("#e8912d" if is_all else "#666") + """;
                border: 1px solid """ + ("#e8912d44" if is_all else "transparent") + """;
                border-left: 3px solid """ + ("#e8912d" if is_all else "transparent") + """;
                border-radius: 4px; padding: 6px 12px; font-size: 13px;
                font-weight: bold; text-align: left;
            }
            QPushButton:hover { background: #e8912d11; color: #e8912d; }
        """)
        for i, btn in enumerate(self.cat_buttons):
            cat = CATEGORIES[i]
            btn.setStyleSheet(self._cat_style(cat["color"], i == idx))

        # 显示/隐藏卡片
        for i, card in enumerate(self.cards):
            card.setVisible(idx == -1 or i == idx)

    def _on_search(self, text):
        text = text.lower().strip()
        # 搜索时重置分类过滤
        if text:
            self._active_cat = -1
            for btn in self.cat_buttons:
                cat = CATEGORIES[self.cat_buttons.index(btn)]
                btn.setStyleSheet(self._cat_style(cat["color"], False))
        for card in self.cards:
            if not text:
                # 恢复分类过滤状态
                card.setVisible(self._active_cat == -1 or self.cards.index(card) == self._active_cat)
                continue
            visible = False
            for btn in card.findChildren(ToolButton):
                if text in btn.text().lower() or text in btn.toolTip().lower():
                    visible = True
                    break
            card.setVisible(visible)

    def _on_search_enter(self):
        text = self.search_box.text().lower().strip()
        if not text:
            return
        for card in self.cards:
            for btn in card.findChildren(ToolButton):
                if text in btn.text().lower() or text in btn.toolTip().lower():
                    btn.click()
                    return

    def _clear_search(self):
        self.search_box.clear()
        self._filter_category(-1)

    def _launch_tool(self, name, exe, desc, folder):
        script = BASE_DIR / "Tools" / folder / exe / "main.py"
        if not script.exists():
            QMessageBox.warning(self, "错误", f"找不到: {script}")
            return
        if not PYTHON_EXE:
            QMessageBox.critical(self, "未找到 Python",
                "需要安装 Python 3.10+ 才能运行工具。\n\n"
                "下载地址: https://www.python.org/downloads/\n\n"
                "安装时请勾选 'Add Python to PATH'")
            return
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(BASE_DIR)
            subprocess.Popen([PYTHON_EXE, str(script)], cwd=str(script.parent), env=env)
        except Exception as e:
            QMessageBox.critical(self, "启动失败",
                f"无法启动 {exe}:\n{type(e).__name__}: {e}")
            return
        self._on_tool_launched(folder, exe)

    def _on_tool_launched(self, folder, exe):
        recent = self.config.get("recent_tools", [])
        if exe in recent:
            recent.remove(exe)
        recent.insert(0, exe)
        self.config["recent_tools"] = recent[:10]
        _save_config(self.config)
        self._update_recent()

    def _update_recent(self):
        while self.recent_btns_layout.count():
            item = self.recent_btns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        recent = self.config.get("recent_tools", [])
        self.recent_bar.setVisible(len(recent) > 0)

        for exe in recent[:6]:
            if exe in self.all_tools:
                info = self.all_tools[exe]
                btn = QPushButton(info["name"])
                btn.setFixedHeight(32)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {info["color"]}22; color: {info["color"]};
                        border: 1px solid {info["color"]}44; border-radius: 3px;
                        padding: 2px 8px; font-size: 12px;
                    }}
                    QPushButton:hover {{ background: {info["color"]}44; }}
                """)
                btn.setToolTip(info["desc"])
                btn.clicked.connect(lambda _, n=info["name"], e=info["exe"],
                                           d=info["desc"], f=info["folder"]:
                                    self._launch_tool(n, e, d, f))
                self.recent_btns_layout.addWidget(btn)

    def _open_projects(self):
        self._open_folder(str(BASE_DIR / "Projects"))

    def _open_base(self):
        self._open_folder(str(BASE_DIR))

    @staticmethod
    def _open_folder(path):
        import platform
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def closeEvent(self, event):
        self.config["window_geometry"] = self.saveGeometry().toHex().data().decode()
        _save_config(self.config)
        super().closeEvent(event)


def main():
    import traceback
    _log_path = BASE_DIR / "Logs" / "launcher_error.log"
    _log_path.parent.mkdir(parents=True, exist_ok=True)

    # Qt6 ??????DPI?????????
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwarenessContext(-4)  # PER_MONITOR_AWARE_V2
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Lighting Designer Workstation")

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#18181b"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e4e4e7"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e21"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#27272a"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e4e4e7"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#27272a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e4e4e7"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#e8912d"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    missing = []
    try:
        import PySide6
    except ImportError:
        missing.append("PySide6")
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    if missing:
        QMessageBox.warning(None, "缺少依赖", f"请安装: pip install {' '.join(missing)}")

    try:
        window = LauncherWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        with open(str(_log_path), "w", encoding="utf-8") as f:
            traceback.print_exc(file=f)
        print(f"\n\u542f\u52a8\u5668\u5d29\u6e83: {e}")
        print(f"\u8be6\u7ec6\u65e5\u5fd7: {_log_path}")
        traceback.print_exc()
        input("\n\u6309\u56de\u8f66\u9000\u51fa...")


if __name__ == "__main__":
    main()