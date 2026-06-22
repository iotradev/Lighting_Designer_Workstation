# -*- coding: utf-8 -*-

"""

Lighting Designer Workstation - ?v3

GrandMA3       

"""
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



#   Python 

def _find_python():

    """TODO"""

    import shutil

    # 1.  sys.executable

    if not getattr(sys, 'frozen', False):

        return sys.executable

    # 2. ?Python

    for name in ['python', 'python3', 'python.exe']:

        found = shutil.which(name)

        if found:

            return found

    # 3. 

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



#   

CATEGORIES = [

    {"name": "", "icon": "", "color": "#e8912d",

     "tools": [

         ("BPM?, "BPMAnalyzer", "/BPM?, "MusicAnalysis"),

         ("", "BeatDetector", "/"?, "MusicAnalysis"),

         ("", "AudioSpectrum", "FFT", "MusicAnalysis"),

         ("", "MusicStructureAnalyzer", "", "MusicAnalysis"),

         ("", "MoodAnalyzer", "/", "MusicAnalysis"),

     ]},

    {"name": "MIDI", "icon": "", "color": "#569cd6",

     "tools": [

         ("MIDI"?, "MIDIMonitor", "/", "MIDI"),

         ("MIDI", "MIDISender", "/", "MIDI"),

         ("MIDI"?, "MIDIMapper", "/", "MIDI"),

         ("MIDI"?, "MIDIRecorder", "//", "MIDI"),

         ("", "TimecodeGenerator", "SMPTE/MTC/LTC", "MIDI"),

         ("", "TimecodeMonitor", "", "MIDI"),

     ]},

    {"name": "DMX/", "icon": "", "color": "#4ec9b0",

     "tools": [

         ("DMX"?, "DMXCalculator", "/", "DMX"),

         ("", "FixturePatcher", "Patch", "DMX"),

         ("DMX?, "DMXTester", "/?, "DMX"),

         ("Art-Net", "ArtNetMonitor", "", "DMX"),

         ("sACN"?, "sACNMonitor", "Universe", "DMX"),

         ("RDM", "RDMTool", "/", "DMX"),

     ]},

    {"name": "", "icon": "", "color": "#c586c0",

     "tools": [

         ("", "StagePlotDesigner", "", "LightingDesign"),

         ("", "FixtureLibrary", "/", "LightingDesign"),

         ("", "BeamCalculator", "/", "LightingDesign"),

         ("", "LuxCalculator", "/", "LightingDesign"),

         ("", "ColorDesigner", "RGB/CMY/Gel", "LightingDesign"),

         ("GOBO", "GoboPreviewer", "/", "LightingDesign"),

     ]},

    {"name": "", "icon": "", "color": "#dcdcaa",

     "tools": [

         ("", "VisualSimulator", "3D", "VisualPreview"),

         ("", "PixelMapper", "LED", "VisualPreview"),

     ]},

    {"name": "", "icon": ", "color": "#d16969",

     "tools": [

         ("", "LaserPlanner", "/", "Effects"),

         ("", "FXDesigner", "/CO2/", "Effects"),

         ("", "PowerCalculator", "/", "Engineering"),

         ("", "CableCalculator", "/", "Engineering"),

         ("", "DistributionPlanner", "", "Engineering"),

         ("UPS", "UPSCalculator", "", "Engineering"),

         ("", "GeneratorCalculator", "", "Engineering"),

     ]},

    {"name": "", "icon": "", "color": "#4ec9b0",

     "tools": [

         ("", "ShowManager", "//Cue", "ShowManagement"),

         ("Cue"?, "CueDesigner", "Cue/Chase/", "ShowManagement"),

         ("", "TimelineEditor", "", "ShowManagement"),

         ("", "CueSheetGenerator", "Cue Sheet", "ShowManagement"),

         ("", "EquipmentListGenerator", "", "ShowManagement"),

         ("", "BackupManager", "", "ShowManagement"),

     ]},

    {"name": "AI", "icon": "", "color": "#e8912d",

     "tools": [

         ("AI", "AILightingDesigner", "", "AI"),

         ("AI", "AIProgrammingAssistant", "Chase/", "AI"),

         ("AI", "AIStageDesigner", "", "AI"),

         ("AI", "AITroubleshooter", "", "AI"),

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





#   

class SplashScreen(QWidget):

    finished = Signal = None  # will be set after import

    def __init__(self):

        super().__init__()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setFixedSize(460, 280)

        self._progress = 0

        self._status = ".."

        self._dots = 0

        self._anim_timer = QTimer(self)

        self._anim_timer.timeout.connect(self._tick)

        self._anim_timer.start(60)



    def _tick(self):

        self._dots = (self._dots + 1) % 4

        self._progress = min(100, self._progress + 4)

        steps = [(15, "), (35, ""), (55, "), (75, ""), (92, "")]

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

        # 

        p.setBrush(QColor(18, 18, 28, 245))

        p.setPen(QPen(QColor("#e8912d"), 2))

        p.drawRoundedRect(0, 0, 460, 280, 14, 14)

        # Logo

        p.setFont(QFont("Segoe UI", 38))

        p.setPen(QColor("#e8912d"))

        p.drawText(0, 20, 460, 55, Qt.AlignmentFlag.AlignCenter, "")

        # 

        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        p.setPen(QColor("#ffffff"))

        p.drawText(0, 72, 460, 28, Qt.AlignmentFlag.AlignCenter, "Lighting Designer Workstation")

        p.setFont(QFont("Microsoft YaHei UI", 9))

        p.setPen(QColor("#777"))

        p.drawText(0, 98, 460, 18, Qt.AlignmentFlag.AlignCenter, " v")

        # ?

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

        # ?

        p.setFont(QFont("Microsoft YaHei UI", 8))

        p.setPen(QColor("#999"))

        p.drawText(0, 168, 460, 16, Qt.AlignmentFlag.AlignCenter, f"{self._status}{'.' * self._dots}")

        # 

        p.setFont(QFont("Consolas", 7))

        p.setPen(QColor("#444"))

        p.drawText(0, 248, 460, 14, Qt.AlignmentFlag.AlignCenter,

                   f"Python {sys.version.split()[0]}    PySide6    Qt6")

        p.end()







#   

class TitleBar(QFrame):

    """TODO"""

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

        logo = QLabel("")

        logo.setFont(QFont("Segoe UI", 16))

        logo.setStyleSheet("color: #e8912d; background: transparent;")

        layout.addWidget(logo)



        # 

        title = QLabel("Lighting Designer Workstation")

        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        title.setStyleSheet("color: #ffffff; background: transparent;")

        layout.addWidget(title)



        # 

        ver = QLabel("v")

        ver.setStyleSheet("color: #e8912d; font-size: 16px; background: transparent;")

        layout.addWidget(ver)

        layout.addStretch()



        # 

        total = sum(len(c["tools"]) for c in CATEGORIES)

        stats = QLabel(f"{len(CATEGORIES)}   {total} ")

        stats.setStyleSheet("color: #888; font-size: 16px; background: transparent;")

        layout.addWidget(stats)



        # 

        btn_min = QPushButton("")

        btn_min.setFixedSize(32, 28)

        btn_min.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_min.setStyleSheet("""

            QPushButton { background: transparent; color: #aaa; border: none; font-size: 16px; }

            QPushButton:hover { background: #ffffff15; color: #fff; }

        """)

        btn_min.clicked.connect(lambda: parent.showMinimized() if parent else None)

        layout.addWidget(btn_min)



        # 

        btn_max = QPushButton("")

        btn_max.setFixedSize(32, 28)

        btn_max.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_max.setStyleSheet(btn_min.styleSheet())

        btn_max.clicked.connect(self._toggle_max)

        layout.addWidget(btn_max)

        self._btn_max = btn_max



        # 

        btn_close = QPushButton("")

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

                self._btn_max.setText("")

            else:

                self._parent.showMaximized()

                self._btn_max.setText("")



    # 

    def mousePressEvent(self, event):

        if event.button() == Qt.MouseButton.LeftButton:

            self._drag_pos = event.globalPosition().toPoint() - self._parent.pos()



    def mouseMoveEvent(self, event):

        if hasattr(self, '_drag_pos') and event.buttons() == Qt.MouseButton.LeftButton:

            self._parent.move(event.globalPosition().toPoint() - self._drag_pos)





#   

class ToolButton(QPushButton):

    """

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





#   

class CategoryCard(QFrame):

    """

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



        # 

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



        # ?

        sep = QFrame()

        sep.setFrameShape(QFrame.Shape.HLine)

        sep.setStyleSheet(f"background: {self.color}22; max-height: 1px; border: none;")

        layout.addWidget(sep)



        # 

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

            QMessageBox.warning(self, "", f" {script}")

            return

        if not PYTHON_EXE:

            QMessageBox.critical(self, "Python",

                "Python 3.10+ n\n"

                ": https://www.python.org/downloads/\n\n"

                "'Add Python to PATH'")

            return

        subprocess.Popen([PYTHON_EXE, str(script)], cwd=str(script.parent))

        if self.tool_launched:

            self.tool_launched.emit(folder, exe)





# Signal

from PySide6.QtCore import Signal as _Signal

CategoryCard.tool_launched = _Signal(str, str)





#  ?

class LauncherWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.config = _load_config()

        self.setMinimumSize(1050, 700)

        self.resize(1150, 780)



        # 

        if self.config.get("window_geometry"):

            try:

                self.restoreGeometry(bytes.fromhex(self.config["window_geometry"]))

            except Exception:

                pass

        # 

        QTimer.singleShot(0, self._ensure_visible)



    def _ensure_visible(self):

        """

        from PySide6.QtGui import QGuiApplication

        screen = QGuiApplication.primaryScreen()

        if screen:

            geo = screen.availableGeometry()

            if not geo.intersects(self.geometry()):

                self.move(geo.center() - self.rect().center())



        # 

        self.all_tools = {}

        for cat in CATEGORIES:

            for name, exe, desc, folder in cat["tools"]:

                self.all_tools[exe] = {"name": name, "exe": exe, "desc": desc, "folder": folder, "color": cat["color"]}



        # 

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



        # ?

        self.setWindowTitle("Lighting Designer Workstation - "?)



        # ?

        content = QHBoxLayout()

        content.setContentsMargins(0, 0, 0, 0)

        content.setSpacing(0)



        #  ?

        sidebar = QFrame()

        sidebar.setFixedWidth(180)

        sidebar.setStyleSheet("background: #1a1a1d; border-right: 1px solid #2a2a2d;")

        sb_layout = QVBoxLayout(sidebar)

        sb_layout.setContentsMargins(8, 12, 8, 12)

        sb_layout.setSpacing(3)



        # 

        self.search_box = QLineEdit()

        self.search_box.setPlaceholderText(" ...")

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



        # 

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



        # 

        for text, slot in [(" ", self._open_projects), (" ", self._open_base)]:

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



        #   

        right = QVBoxLayout()

        right.setContentsMargins(0, 0, 0, 0)

        right.setSpacing(0)



        # ?

        self.recent_bar = QFrame()

        self.recent_bar.setStyleSheet("background: #1e1e21; border-bottom: 1px solid #2a2a2d;")

        self.recent_bar.setFixedHeight(40)

        rb_layout = QHBoxLayout(self.recent_bar)

        rb_layout.setContentsMargins(16, 0, 16, 0)

        rb_layout.setSpacing(6)

        lbl = QLabel("")

        lbl.setStyleSheet("color: #666; font-size: 15px; background: transparent;")

        rb_layout.addWidget(lbl)

        self.recent_btns_widget = QWidget()

        self.recent_btns_layout = QHBoxLayout(self.recent_btns_widget)

        self.recent_btns_layout.setContentsMargins(0, 0, 0, 0)

        self.recent_btns_layout.setSpacing(4)

        rb_layout.addWidget(self.recent_btns_widget)

        rb_layout.addStretch()

        right.addWidget(self.recent_bar)



        # ?

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



        # 

        footer = QFrame()

        footer.setFixedHeight(30)

        footer.setStyleSheet("background: #007acc; border-top: 1px solid #005a9e;")

        fl = QHBoxLayout(footer)

        fl.setContentsMargins(12, 0, 12, 0)

        ver_label = QLabel("v")

        ver_label.setStyleSheet("color:#fff; font-size:10px; background:transparent;")

        fl.addWidget(ver_label)

        fl.addStretch()

        # Python ?

        if PYTHON_EXE:

            py_name = Path(PYTHON_EXE).name

            py_status = QLabel(f" {py_name}")

            py_status.setStyleSheet("color: #4ec9b0; font-size: 16px; background: transparent;")

        else:

            py_status = QLabel("?Python")

            py_status.setStyleSheet("color: #ff6b6b; font-size: 16px; background: transparent;")

        fl.addWidget(py_status)

        fl.addSpacing(12)

        hint = QLabel("Ctrl+K     ")

        hint.setStyleSheet("color: #ffffffaa; font-size: 16px; background: transparent;")

        fl.addWidget(hint)

        right.addWidget(footer)



        content.addLayout(right, 1)

        root.addLayout(content, 1)



        # ?

        from PySide6.QtGui import QShortcut, QKeySequence

        QShortcut(QKeySequence("Ctrl+K"), self, lambda: self.search_box.setFocus())

        QShortcut(QKeySequence("Escape"), self, self._clear_search)

        QShortcut(QKeySequence("Ctrl+Q"), self, self.close)



        # ?

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
        """



    def _scroll_to_category(self, idx):

        if idx < len(self.cards):

            card = self.cards[idx]

            #  QScrollArea

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

            QMessageBox.warning(self, "", f" {script}")

            return

        if not PYTHON_EXE:

            QMessageBox.critical(self, "Python",

                "Python 3.10+ n\n"

                ": https://www.python.org/downloads/\n\n"

                "'Add Python to PATH'")

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

        # ?

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





#   

def main():

    # ?DPI  - ?QApplication ?

    if hasattr(Qt, 'AA_EnableHighDpiScaling'):

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)

    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):

        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Windows DPI 

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



    #  QSS 

    qss_path = BASE_DIR / "Common" / "themes" / "launcher.qss"

    if qss_path.exists():

        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))



    # ?

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

        QMessageBox.warning(None, "", f" pip install {' '.join(missing)}")



    # 

    window = LauncherWindow()

    window.show()



    sys.exit(app.exec())





if __name__ == "__main__":

    main()





