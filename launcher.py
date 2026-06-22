# -*- coding: utf-8 -*-
"""
Lighting Designer Workstation - 鍥惧舰鍚姩鍣?v3
GrandMA3 椋庢牸娣辫壊涓婚 路 渚ф爮瀵艰埅 路 鍔ㄧ敾鏁堟灉 路 鑷畾涔夋爣棰樻爮
"""
import sys, os, subprocess, json
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QScrollArea, QGridLayout,
    QLineEdit, QMessageBox, QGraphicsOpacityEffect, QSizePolicy,
    QToolButton, QMenu, QWidgetAction, QSpacerItem
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize,
    QParallelAnimationGroup, Property, QRect, QRectF
)
from PySide6.QtGui import (
    QFont, QColor, QPainter, QPalette, QIcon, QAction,
    QLinearGradient, QBrush, QPen, QPixmap, QCursor, QFontMetrics
)

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "Config" / "launcher_config.json"

# 鈹€鈹€ 鏌ユ壘绯荤粺 Python 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def _find_python():
    """鏌ユ壘鍙敤鐨?Python 瑙ｉ噴鍣?""
    import shutil
    # 1. 闈炴墦鍖呮ā寮忕洿鎺ョ敤 sys.executable
    if not getattr(sys, 'frozen', False):
        return sys.executable
    # 2. 鎵撳寘妯″紡锛氭煡鎵剧郴缁?Python
    for name in ['python', 'python3', 'python.exe']:
        found = shutil.which(name)
        if found:
            return found
    # 3. 甯歌瀹夎璺緞
    for p in [
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Python' / 'Python311' / 'python.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Python' / 'Python312' / 'python.exe',
        Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Python' / 'Python310' / 'python.exe',
        Path('C:/Python311/python.exe'),
        Path('C:/Python312/python.exe'),
        Path('C:/Python310/python.exe'),
    ]:
        if p.exists():
            return str(p)
    return None

PYTHON_EXE = _find_python()

# 鈹€鈹€ 宸ュ叿瀹氫箟 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
CATEGORIES = [
    {"name": "闊充箰鍒嗘瀽", "icon": "馃幍", "color": "#e8912d",
     "tools": [
         ("BPM鍒嗘瀽鍣?, "BPMAnalyzer", "鑷姩/瀹炴椂BPM妫€娴?, "MusicAnalysis"),
         ("鑺傛媿妫€娴嬪櫒", "BeatDetector", "鑺傛媿/寮哄急鎷嶈瘑鍒?, "MusicAnalysis"),
         ("棰戣氨鍒嗘瀽鍣?, "AudioSpectrum", "FFT棰戣氨鍒嗘瀽", "MusicAnalysis"),
         ("闊充箰缁撴瀯鍒嗘瀽", "MusicStructureAnalyzer", "娈佃惤璇嗗埆", "MusicAnalysis"),
         ("鎯呯华鍒嗘瀽鍣?, "MoodAnalyzer", "鎯呯华/鑳介噺鏇茬嚎", "MusicAnalysis"),
     ]},
    {"name": "MIDI宸ュ叿", "icon": "馃幑", "color": "#569cd6",
     "tools": [
         ("MIDI鐩戝惉鍣?, "MIDIMonitor", "瀹炴椂鐩戝惉/鏃ュ織", "MIDI"),
         ("MIDI鍙戦€佸櫒", "MIDISender", "鍙戦€?鑴氭湰/闈㈡澘", "MIDI"),
         ("MIDI鏄犲皠鍣?, "MIDIMapper", "瀛︿範/鎸夐挳鏄犲皠", "MIDI"),
         ("MIDI褰曞埗鍣?, "MIDIRecorder", "褰曞埗/鍥炴斁/瀵煎嚭", "MIDI"),
         ("鏃堕棿鐮佺敓鎴?, "TimecodeGenerator", "SMPTE/MTC/LTC", "MIDI"),
         ("鏃堕棿鐮佺洃瑙?, "TimecodeMonitor", "婕傜Щ妫€娴?鍚屾", "MIDI"),
     ]},
    {"name": "DMX/缃戠粶", "icon": "馃挕", "color": "#4ec9b0",
     "tools": [
         ("DMX璁＄畻鍣?, "DMXCalculator", "鍦板潃/閫氶亾璁＄畻", "DMX"),
         ("鐏叿閰嶆帴鍣?, "FixturePatcher", "Patch琛?瑙勫垝", "DMX"),
         ("DMX娴嬭瘯鍣?, "DMXTester", "閫氶亾/鏁呴殰妫€娴?, "DMX"),
         ("Art-Net鐩戝惉", "ArtNetMonitor", "鍗忚鐩戝惉", "DMX"),
         ("sACN鐩戝惉鍣?, "sACNMonitor", "Universe鍒嗘瀽", "DMX"),
         ("RDM绠＄悊", "RDMTool", "鍙戠幇/鍙傛暟璇诲啓", "DMX"),
     ]},
    {"name": "鐏厜璁捐", "icon": "馃敠", "color": "#c586c0",
     "tools": [
         ("鑸炲彴骞抽潰鍥?, "StagePlotDesigner", "鐏綅鍥剧粯鍒?, "LightingDesign"),
         ("鐏叿鏁版嵁搴?, "FixtureLibrary", "鎼滅储/绠＄悊", "LightingDesign"),
         ("鍏夋潫璁＄畻鍣?, "BeamCalculator", "瑙掑害/瑕嗙洊璁＄畻", "LightingDesign"),
         ("鐓у害璁＄畻鍣?, "LuxCalculator", "鐓у害/瑕嗙洊鍒嗘瀽", "LightingDesign"),
         ("鑹插僵璁捐鍣?, "ColorDesigner", "RGB/CMY/Gel", "LightingDesign"),
         ("GOBO棰勮", "GoboPreviewer", "棰勮/鏃嬭浆妯℃嫙", "LightingDesign"),
     ]},
    {"name": "瑙嗚棰勬紨", "icon": "馃幀", "color": "#dcdcaa",
     "tools": [
         ("瑙嗚妯℃嫙鍣?, "VisualSimulator", "3D鐏厜妯℃嫙", "VisualPreview"),
         ("鍍忕礌鏄犲皠鍣?, "PixelMapper", "LED鐭╅樀璁捐", "VisualPreview"),
     ]},
    {"name": "鐗规晥宸ョ▼", "icon": "鉁?, "color": "#d16969",
     "tools": [
         ("婵€鍏夎鍒掑櫒", "LaserPlanner", "鍖哄煙/瀹夊叏璁＄畻", "Effects"),
         ("鐗规晥璁捐鍣?, "FXDesigner", "鐑熼浘/CO2/鐒扮伀", "Effects"),
         ("鍔熺巼璁＄畻鍣?, "PowerCalculator", "鍔熺巼/鐢垫祦", "Engineering"),
         ("绾跨紗璁＄畻鍣?, "CableCalculator", "鍘嬮檷/绾垮緞", "Engineering"),
         ("閰嶇數瑙勫垝鍣?, "DistributionPlanner", "璐熻浇骞宠　", "Engineering"),
         ("UPS缁埅", "UPSCalculator", "缁埅璁＄畻", "Engineering"),
         ("鍙戠數鏈哄閲?, "GeneratorCalculator", "瀹归噺璁＄畻", "Engineering"),
     ]},
    {"name": "婕斿嚭绠＄悊", "icon": "馃幁", "color": "#4ec9b0",
     "tools": [
         ("婕斿嚭绠＄悊鍣?, "ShowManager", "椤圭洰/鍦烘櫙/Cue", "ShowManagement"),
         ("Cue璁捐鍣?, "CueDesigner", "Cue/Chase/鏁堟灉", "ShowManagement"),
         ("鏃堕棿杞寸紪杈?, "TimelineEditor", "闊充箰鍚屾", "ShowManagement"),
         ("鑺傜洰鍗曠敓鎴?, "CueSheetGenerator", "Cue Sheet", "ShowManagement"),
         ("璁惧娓呭崟", "EquipmentListGenerator", "娓呭崟鐢熸垚", "ShowManagement"),
         ("澶囦唤绠＄悊鍣?, "BackupManager", "鑷姩澶囦唤", "ShowManagement"),
     ]},
    {"name": "AI杈呭姪", "icon": "馃", "color": "#e8912d",
     "tools": [
         ("AI鐏厜鍔╂墜", "AILightingDesigner", "鐏厜寤鸿", "AI"),
         ("AI缂栫▼鍔╂墜", "AIProgrammingAssistant", "Chase/鏁堟灉", "AI"),
         ("AI鑸炵編鍔╂墜", "AIStageDesigner", "甯冨眬寤鸿", "AI"),
         ("AI鏁呴殰璇婃柇", "AITroubleshooter", "鏁呴殰璇婃柇", "AI"),
     ]},
]


def _load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {"recent_tools": [], "favorites": [], "window_geometry": None}


def _save_config(cfg):
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding='utf-8')
    except Exception:
        pass


# 鈹€鈹€ 鍚姩鐢婚潰 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class SplashScreen(QWidget):
    finished = Signal = None  # will be set after import
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(460, 280)
        self._progress = 0
        self._status = "姝ｅ湪鍒濆鍖?.."
        self._dots = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(60)

    def _tick(self):
        self._dots = (self._dots + 1) % 4
        self._progress = min(100, self._progress + 4)
        steps = [(15, "妫€鏌ヤ緷璧?), (35, "鍔犺浇涓婚"), (55, "鍒濆鍖栧伐鍏?), (75, "鎵弿鎻掍欢"), (92, "鍑嗗鐣岄潰")]
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
        # 鑳屾櫙
        p.setBrush(QColor(18, 18, 28, 245))
        p.setPen(QPen(QColor("#e8912d"), 2))
        p.drawRoundedRect(0, 0, 460, 280, 14, 14)
        # Logo
        p.setFont(QFont("Segoe UI", 38))
        p.setPen(QColor("#e8912d"))
        p.drawText(0, 20, 460, 55, Qt.AlignmentFlag.AlignCenter, "猬?)
        # 鏍囬
        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        p.setPen(QColor("#ffffff"))
        p.drawText(0, 72, 460, 28, Qt.AlignmentFlag.AlignCenter, "Lighting Designer Workstation")
        p.setFont(QFont("Microsoft YaHei UI", 9))
        p.setPen(QColor("#777"))
        p.drawText(0, 98, 460, 18, Qt.AlignmentFlag.AlignCenter, "鑸炲彴鐏厜璁捐宸ヤ綔绔? v")
        # 杩涘害鏉?
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
        # 鐘舵€?
        p.setFont(QFont("Microsoft YaHei UI", 8))
        p.setPen(QColor("#999"))
        p.drawText(0, 168, 460, 16, Qt.AlignmentFlag.AlignCenter, f"{self._status}{'.' * self._dots}")
        # 搴曢儴
        p.setFont(QFont("Consolas", 7))
        p.setPen(QColor("#444"))
        p.drawText(0, 248, 460, 14, Qt.AlignmentFlag.AlignCenter,
                   f"Python {sys.version.split()[0]}  路  PySide6  路  Qt6")
        p.end()



# 鈹€鈹€ 鑷畾涔夋爣棰樻爮 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class TitleBar(QFrame):
    """鑷畾涔夋棤杈规鏍囬鏍?""
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

        # Logo
        logo = QLabel("猬?)
        logo.setFont(QFont("Segoe UI", 16))
        logo.setStyleSheet("color: #e8912d; background: transparent;")
        layout.addWidget(logo)

        # 鏍囬
        title = QLabel("Lighting Designer Workstation")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; background: transparent;")
        layout.addWidget(title)

        # 鐗堟湰
        ver = QLabel("v")
        ver.setStyleSheet("color: #e8912d; font-size: 16px; background: transparent;")
        layout.addWidget(ver)
        layout.addStretch()

        # 缁熻
        total = sum(len(c["tools"]) for c in CATEGORIES)
        stats = QLabel(f"{len(CATEGORIES)} 鍒嗙被 路 {total} 宸ュ叿")
        stats.setStyleSheet("color: #888; font-size: 16px; background: transparent;")
        layout.addWidget(stats)

        # 鏈€灏忓寲
        btn_min = QPushButton("鈹€")
        btn_min.setFixedSize(32, 28)
        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_min.setStyleSheet("""
            QPushButton { background: transparent; color: #aaa; border: none; font-size: 16px; }
            QPushButton:hover { background: #ffffff15; color: #fff; }
        """)
        btn_min.clicked.connect(lambda: parent.showMinimized() if parent else None)
        layout.addWidget(btn_min)

        # 鏈€澶у寲
        btn_max = QPushButton("鈻?)
        btn_max.setFixedSize(32, 28)
        btn_max.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_max.setStyleSheet(btn_min.styleSheet())
        btn_max.clicked.connect(self._toggle_max)
        layout.addWidget(btn_max)
        self._btn_max = btn_max

        # 鍏抽棴
        btn_close = QPushButton("鉁?)
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
                self._btn_max.setText("鈻?)
            else:
                self._parent.showMaximized()
                self._btn_max.setText("鉂?)

    # 鎷栧姩绐楀彛
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._parent.pos()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_pos') and event.buttons() == Qt.MouseButton.LeftButton:
            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)


# 鈹€鈹€ 宸ュ叿鎸夐挳 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class ToolButton(QPushButton):
    """甯﹀浘鏍囩殑宸ュ叿鎸夐挳"""
    def __init__(self, name, desc, color, parent=None):
        super().__init__(parent)
        self.accent = color
        self.setText(f"  {name}")
        self.setToolTip(desc)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(46)
        self.setMinimumWidth(180)
        self.setStyleSheet(self._style(False))

    def _style(self, hover):
        if hover:
            return f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {self.accent}22, stop:1 {self.accent}11);
                    color: {self.accent};
                    border: 1px solid {self.accent}66;
                    border-left: 3px solid {self.accent};
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: left;
                }}
            """
        return f"""
            QPushButton {{
                background: #2a2a2d;
                color: #ccc;
                border: 1px solid #333;
                border-left: 3px solid transparent;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 16px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: #333;
                color: #fff;
                border-left: 3px solid {self.accent}88;
            }}
        """

    def enterEvent(self, e):
        self.setStyleSheet(self._style(True))
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setStyleSheet(self._style(False))
        super().leaveEvent(e)


# 鈹€鈹€ 鍒嗙被鍗＄墖 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class CategoryCard(QFrame):
    """鍒嗙被鍗＄墖"""
    tool_launched = None  # Signal set after class

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
                border-radius: 10px;
                border-top: 3px solid {self.color};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # 鏍囬
        hdr = QHBoxLayout()
        icon = QLabel(category["icon"])
        icon.setFont(QFont("Segoe UI Emoji", 16))
        icon.setFixedSize(28, 28)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hdr.addWidget(icon)
        name = QLabel(category["name"])
        name.setFont(QFont("Microsoft YaHei UI", 13, QFont.Weight.Bold))
        name.setStyleSheet(f"color: {self.color}; background: transparent; border: none;")
        hdr.addWidget(name)
        hdr.addStretch()
        cnt = QLabel(f"{len(category['tools'])}")
        cnt.setStyleSheet(f"color: {self.color}88; font-size: 22px; font-weight: bold; background: transparent; border: none;")
        hdr.addWidget(cnt)
        layout.addLayout(hdr)

        # 鍒嗛殧绾?
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {self.color}22; max-height: 1px; border: none;")
        layout.addWidget(sep)

        # 宸ュ叿鍒楄〃
        grid = QGridLayout()
        grid.setSpacing(4)
        for i, (name, exe, desc, folder) in enumerate(category["tools"]):
            btn = ToolButton(name, desc, self.color)
            btn.clicked.connect(lambda _, f=folder, e=exe: self._launch(f, e))
            grid.addWidget(btn, i // 2, i % 2)
        layout.addLayout(grid)

    def _launch(self, folder, exe):
        script = BASE_DIR / "Tools" / folder / exe / "main.py"
        if not script.exists():
            QMessageBox.warning(self, "閿欒", f"鎵句笉鍒? {script}")
            return
        if not PYTHON_EXE:
            QMessageBox.critical(self, "鏈壘鍒?Python",
                "闇€瑕佸畨瑁?Python 3.10+ 鎵嶈兘杩愯宸ュ叿銆俓n\n"
                "涓嬭浇鍦板潃: https://www.python.org/downloads/\n\n"
                "瀹夎鏃惰鍕鹃€?'Add Python to PATH'")
            return
        subprocess.Popen([PYTHON_EXE, str(script)], cwd=str(script.parent))
        if self.tool_launched:
            self.tool_launched.emit(folder, exe)


# Signal
from PySide6.QtCore import Signal as _Signal
CategoryCard.tool_launched = _Signal(str, str)


# 鈹€鈹€ 涓荤獥鍙?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = _load_config()
        self.setMinimumSize(1050, 700)
        self.resize(1150, 780)

        # 鎭㈠绐楀彛浣嶇疆锛堝眳涓綔涓洪粯璁わ級
        if self.config.get("window_geometry"):
            try:
                self.restoreGeometry(bytes.fromhex(self.config["window_geometry"]))
            except Exception:
                pass
        # 濡傛灉鎭㈠鍚庣獥鍙ｄ笉鍦ㄥ彲瑙佸尯鍩燂紝灞呬腑鏄剧ず
        QTimer.singleShot(0, self._ensure_visible)

    def _ensure_visible(self):
        """纭繚绐楀彛鍦ㄥ彲瑙佸睆骞曞尯鍩熷唴"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if not geo.intersects(self.geometry()):
                self.move(geo.center() - self.rect().center())

        # 鏋勫缓宸ュ叿鏄犲皠
        self.all_tools = {}
        for cat in CATEGORIES:
            for name, exe, desc, folder in cat["tools"]:
                self.all_tools[exe] = {"name": name, "exe": exe, "desc": desc, "folder": folder, "color": cat["color"]}

        # 鍏ㄥ眬鏍峰紡
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

        # 鏍囧噯鏍囬鏍?
        self.setWindowTitle("Lighting Designer Workstation - 鑸炲彴鐏厜璁捐宸ヤ綔绔?)

        # 鍐呭鍖?
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # 鈹€鈹€ 宸︿晶鏍?鈹€鈹€
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("background: #1a1a1d; border-right: 1px solid #2a2a2d;")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(8, 12, 8, 12)
        sb_layout.setSpacing(3)

        # 鎼滅储
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("馃攳 鎼滅储...")
        self.search_box.setFixedHeight(36)
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: #222; color: #ccc; border: 1px solid #333;
                border-radius: 6px; padding: 4px 10px; font-size: 15px;
            }
            QLineEdit:focus { border-color: #e8912d66; }
        """)
        self.search_box.textChanged.connect(self._on_search)
        self.search_box.returnPressed.connect(self._on_search_enter)
        sb_layout.addWidget(self.search_box)
        sb_layout.addSpacing(8)

        # 鍒嗙被鎸夐挳
        self.cat_buttons = []
        for i, cat in enumerate(CATEGORIES):
            btn = QPushButton(f" {cat['icon']}  {cat['name']}")
            btn.setFixedHeight(46)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._cat_style(cat["color"], False))
            btn.clicked.connect(lambda _, idx=i: self._scroll_to_category(idx))
            sb_layout.addWidget(btn)
            self.cat_buttons.append(btn)

        sb_layout.addStretch()

        # 搴曢儴鎸夐挳
        for text, slot in [("馃搨 鎵撳紑椤圭洰鐩綍", self._open_projects), ("馃搧 鎵撳紑绋嬪簭鐩綍", self._open_base)]:
            btn = QPushButton(text)
            btn.setFixedHeight(30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #666; border: none;
                    font-size: 15px; text-align: left; padding: 4px 8px;
                }
                QPushButton:hover { color: #aaa; }
            """)
            btn.clicked.connect(slot)
            sb_layout.addWidget(btn)

        content.addWidget(sidebar)

        # 鈹€鈹€ 鍙充晶鍐呭 鈹€鈹€
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # 鏈€杩戜娇鐢?
        self.recent_bar = QFrame()
        self.recent_bar.setStyleSheet("background: #1e1e21; border-bottom: 1px solid #2a2a2d;")
        self.recent_bar.setFixedHeight(40)
        rb_layout = QHBoxLayout(self.recent_bar)
        rb_layout.setContentsMargins(16, 0, 16, 0)
        rb_layout.setSpacing(6)
        lbl = QLabel("鈴?鏈€杩?")
        lbl.setStyleSheet("color: #666; font-size: 15px; background: transparent;")
        rb_layout.addWidget(lbl)
        self.recent_btns_widget = QWidget()
        self.recent_btns_layout = QHBoxLayout(self.recent_btns_widget)
        self.recent_btns_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_btns_layout.setSpacing(4)
        rb_layout.addWidget(self.recent_btns_widget)
        rb_layout.addStretch()
        right.addWidget(self.recent_bar)

        # 婊氬姩鍖?
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        self.grid = QGridLayout(scroll_content)
        self.grid.setContentsMargins(16, 12, 16, 12)
        self.grid.setSpacing(12)

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

        # 搴曢儴鐘舵€佹爮
        footer = QFrame()
        footer.setFixedHeight(30)
        footer.setStyleSheet("background: #007acc; border-top: 1px solid #005a9e;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 0, 12, 0)
        ver_label = QLabel("v")
        ver_label.setStyleSheet("color:#fff; font-size:10px; background:transparent;")
        fl.addWidget(ver_label)
        fl.addStretch()
        # Python 鐘舵€?
        if PYTHON_EXE:
            py_name = Path(PYTHON_EXE).name
            py_status = QLabel(f"馃悕 {py_name}")
            py_status.setStyleSheet("color: #4ec9b0; font-size: 16px; background: transparent;")
        else:
            py_status = QLabel("鈿?鏈畨瑁?Python")
            py_status.setStyleSheet("color: #ff6b6b; font-size: 16px; background: transparent;")
        fl.addWidget(py_status)
        fl.addSpacing(12)
        hint = QLabel("Ctrl+K 鎼滅储  路  鐐瑰嚮鍚姩")
        hint.setStyleSheet("color: #ffffffaa; font-size: 16px; background: transparent;")
        fl.addWidget(hint)
        right.addWidget(footer)

        content.addLayout(right, 1)
        root.addLayout(content, 1)

        # 蹇嵎閿?
        from PySide6.QtGui import QShortcut, QKeySequence
        QShortcut(QKeySequence("Ctrl+K"), self, lambda: self.search_box.setFocus())
        QShortcut(QKeySequence("Escape"), self, self._clear_search)
        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)

        # 鏇存柊鏈€杩?
        self._update_recent()

    def _cat_style(self, color, active):
        if active:
            return f"""
                QPushButton {{
                    background: {color}22; color: {color}; border: none;
                    border-left: 3px solid {color}; border-radius: 4px;
                    font-size: 15px; text-align: left; padding: 6px 10px;
                }}
            """
        return f"""
            QPushButton {{
                background: transparent; color: #888; border: none;
                border-left: 3px solid transparent; border-radius: 4px;
                font-size: 15px; text-align: left; padding: 6px 10px;
            }}
            QPushButton:hover {{
                background: {color}11; color: {color};
                border-left: 3px solid {color}66;
            }}
        """

    def _scroll_to_category(self, idx):
        if idx < len(self.cards):
            card = self.cards[idx]
            # 鍚戜笂鏌ユ壘 QScrollArea
            w = card.parent()
            while w:
                if isinstance(w, QScrollArea):
                    w.ensureWidgetVisible(card, 50, 50)
                    break
                w = w.parent()

    def _on_search(self, text):
        text = text.lower().strip()
        for i, cat in enumerate(CATEGORIES):
            card = self.cards[i]
            if not text:
                card.show()
                continue
            match = text in cat["name"].lower()
            if not match:
                for name, exe, desc, folder in cat["tools"]:
                    if text in name.lower() or text in desc.lower() or text in exe.lower():
                        match = True
                        break
            card.show() if match else card.hide()

    def _on_search_enter(self):
        text = self.search_box.text().lower().strip()
        if not text:
            return
        for cat in CATEGORIES:
            for name, exe, desc, folder in cat["tools"]:
                if text in name.lower() or text in desc.lower() or text in exe.lower():
                    self._launch_tool(name, exe, desc, folder)
                    self.search_box.clear()
                    return

    def _clear_search(self):
        self.search_box.clear()
        self.search_box.clearFocus()
        for card in self.cards:
            card.show()

    def _launch_tool(self, name, exe, desc, folder):
        script = BASE_DIR / "Tools" / folder / exe / "main.py"
        if not script.exists():
            QMessageBox.warning(self, "閿欒", f"鎵句笉鍒? {script}")
            return
        if not PYTHON_EXE:
            QMessageBox.critical(self, "鏈壘鍒?Python",
                "闇€瑕佸畨瑁?Python 3.10+ 鎵嶈兘杩愯宸ュ叿銆俓n\n"
                "涓嬭浇鍦板潃: https://www.python.org/downloads/\n\n"
                "瀹夎鏃惰鍕鹃€?'Add Python to PATH'")
            return
        subprocess.Popen([PYTHON_EXE, str(script)], cwd=str(script.parent))
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
        # 娓呴櫎鏃ф寜閽?
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
                        padding: 2px 8px; font-size: 16px;
                    }}
                    QPushButton:hover {{ background: {info["color"]}44; }}
                """)
                btn.setToolTip(info["desc"])
                btn.clicked.connect(lambda _, n=info["name"], e=info["exe"],
                                           d=info["desc"], f=info["folder"]:
                                    self._launch_tool(n, e, d, f))
                self.recent_btns_layout.addWidget(btn)

    def _open_projects(self):
        os.startfile(str(BASE_DIR / "Projects"))

    def _open_base(self):
        os.startfile(str(BASE_DIR))

    def closeEvent(self, event):
        self.config["window_geometry"] = self.saveGeometry().toHex().data().decode()
        _save_config(self.config)
        super().closeEvent(event)


# 鈹€鈹€ 鍏ュ彛 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
def main():
    # 楂?DPI 閫傞厤 - 蹇呴』鍦?QApplication 鍒涘缓鍓嶈缃?
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    # Windows DPI 鎰熺煡
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
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

    # 加载统一 QSS 样式表
    qss_path = BASE_DIR / "Common" / "themes" / "launcher.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # 渚濊禆妫€鏌?
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
        QMessageBox.warning(None, "缂哄皯渚濊禆", f"璇峰畨瑁? pip install {' '.join(missing)}")

    # 鐩存帴鏄剧ず涓荤獥鍙ｏ紙璺宠繃鍚姩鐢婚潰閬垮厤鍏煎鎬ч棶棰橈級
    window = LauncherWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


