# -*- coding: utf-8 -*-
"""
缁熶竴涓荤獥鍙ｅ熀绫?- GrandMA3 椋庢牸
鎵€鏈夊伐鍏风獥鍙ｅ繀椤荤户鎵挎绫伙紝鑷姩鑾峰緱:
- 鑿滃崟鏍?(鏂囦欢/缂栬緫/瑙嗗浘/宸ュ叿/甯姪)
- 宸ュ叿鏍?(甯哥敤鎿嶄綔)
- 鐘舵€佹爮 (椤圭洰淇℃伅/灏辩华鐘舵€?
- 鏃ュ織绐楀彛 (鍙仠闈?
- 椤圭洰绠＄悊鍣?(鍙仠闈?
- 娣辫壊涓婚
- 绐楀彛甯冨眬璁板繂
- 蹇嵎閿?- 鎷栨斁鏀寔
- 楂楧PI閫傞厤
"""
import sys, os
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar, QLabel,
    QDockWidget, QTextEdit, QFileDialog, QMessageBox, QWidget,
    QVBoxLayout, QApplication, QSplitter
)
from PySide6.QtCore import Qt, QTimer, QByteArray, QSettings, QSize, Signal
from PySide6.QtGui import QAction, QKeySequence, QIcon, QFont, QDragEnterEvent, QDropEvent


def _ensure_dpi_awareness():
    """纭繚楂楧PI鎰熺煡 - 鍦ㄩ娆″垱寤虹獥鍙ｅ墠璋冪敤"""
    app = QApplication.instance()
    if app:
        # 璁剧疆榛樿瀛椾綋澶у皬 (閫傞厤楂楧PI)
        font = app.font()
        if font.pointSize() < 11:
            font.setPointSize(11)
            app.setFont(font)

# 瀵煎叆鏍稿績妯″潡
BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "Common"))

from themes.stylesheet import generate_stylesheet
from config.config_manager import ConfigManager
from log_system.tool_logger import ToolLogger, LogPanel
from project.project_manager import ProjectManager


class BaseToolWindow(QMainWindow):
    """
    宸ュ叿涓荤獥鍙ｅ熀绫?    鎵€鏈夌伅鍏夎璁″伐鍏风户鎵挎绫伙紝鑷姩鑾峰緱缁熶竴鐨勭獥鍙ｆ鏋?    """

    def __init__(self, tool_name: str, tool_title: str, version: str = "1.0.0",
                 width: int = 1400, height: int = 900, parent=None):
        super().__init__(parent)
        # 纭繚楂楧PI閫傞厤
        _ensure_dpi_awareness()
        self.tool_name = tool_name
        self.tool_title = tool_title
        self.version = version

        # 鍒濆鍖栨牳蹇冪郴缁?        self.config = ConfigManager()
        self.project_mgr = ProjectManager()

        # 搴旂敤涓婚
        theme = self.config.get("theme", "dark")
        self.setStyleSheet(generate_stylesheet(theme))

        # 绐楀彛璁剧疆
        self.setWindowTitle(f"{tool_title} - Lighting Designer Workstation")
        self.setMinimumSize(800, 600)
        self.resize(width, height)
        self.setAcceptDrops(True)

        # 鎭㈠绐楀彛甯冨眬
        self._restore_geometry()

        # 鍒濆鍖栨棩蹇楃郴缁?        self.log_panel = LogPanel(tool_name)
        self.logger = self.log_panel.get_logger()

        # 鏋勫缓鐣岄潰
        self._init_menu_bar()
        self._init_toolbar()
        self._init_status_bar()
        self._init_dock_panels()

        # 鑷姩淇濆瓨瀹氭椂鍣?        if self.config.get("auto_save", True):
            self._auto_save_timer = QTimer(self)
            self._auto_save_timer.timeout.connect(self._auto_save)
            interval = self.config.get("auto_save_interval", 300) * 1000
            self._auto_save_timer.start(interval)

        # 绐楀彛甯冨眬璁板繂瀹氭椂鍣?        self._layout_timer = QTimer(self)
        self._layout_timer.timeout.connect(self._save_geometry)
        self._layout_timer.start(60000)  # 姣忓垎閽熶繚瀛樹竴娆″竷灞€

        self.logger.info(f"{tool_title} v{version} 宸插惎鍔?)

    def _init_menu_bar(self):
        """鍒濆鍖栬彍鍗曟爮"""
        menubar = self.menuBar()

        # 鏂囦欢鑿滃崟
        file_menu = menubar.addMenu("鏂囦欢(&F)")
        self._add_action(file_menu, "鏂板缓椤圭洰(&N)", self._on_new_project, QKeySequence.StandardKey.New)
        self._add_action(file_menu, "鎵撳紑椤圭洰(&O)...", self._on_open_project, QKeySequence.StandardKey.Open)
        file_menu.addSeparator()
        self._add_action(file_menu, "淇濆瓨(&S)", self._on_save_project, QKeySequence.StandardKey.Save)
        self._add_action(file_menu, "鍙﹀瓨涓?&A)...", self._on_save_as, QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()

        # 鏈€杩戦」鐩瓙鑿滃崟
        self.recent_menu = file_menu.addMenu("鏈€杩戦」鐩?&R)")
        self._update_recent_menu()

        file_menu.addSeparator()
        self._add_action(file_menu, "閫€鍑?&Q)", self.close, QKeySequence("Alt+F4"))

        # 缂栬緫鑿滃崟
        edit_menu = menubar.addMenu("缂栬緫(&E)")
        self._add_action(edit_menu, "鎾ら攢", self._stub("鎾ら攢"), QKeySequence.StandardKey.Undo)
        self._add_action(edit_menu, "閲嶅仛", self._stub("閲嶅仛"), QKeySequence.StandardKey.Redo)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "鍓垏", self._stub("鍓垏"), QKeySequence.StandardKey.Cut)
        self._add_action(edit_menu, "澶嶅埗", self._stub("澶嶅埗"), QKeySequence.StandardKey.Copy)
        self._add_action(edit_menu, "绮樿创", self._stub("绮樿创"), QKeySequence.StandardKey.Paste)

        # 瑙嗗浘鑿滃崟
        view_menu = menubar.addMenu("瑙嗗浘(&V)")
        self._add_action(view_menu, "鏃ュ織绐楀彛", self._toggle_log_panel, QKeySequence("Ctrl+L"))
        self._add_action(view_menu, "椤圭洰绠＄悊鍣?, self._toggle_project_panel, QKeySequence("Ctrl+P"))
        view_menu.addSeparator()
        self._add_action(view_menu, "娣辫壊涓婚", lambda: self._switch_theme("dark"))
        self._add_action(view_menu, "娴呰壊涓婚", lambda: self._switch_theme("light"))

        # 宸ュ叿鑿滃崟
        self.tool_menu = menubar.addMenu("宸ュ叿(&T)")
        # 瀛愮被鍙湪姝ゆ坊鍔犲伐鍏风壒瀹氳彍鍗曢」

        # 甯姪鑿滃崟
        help_menu = menubar.addMenu("甯姪(&H)")
        self._add_action(help_menu, "鍏充簬", self._show_about)
        self._add_action(help_menu, "蹇嵎閿垪琛?, self._show_shortcuts)

    def _add_action(self, menu, text, slot, shortcut=None):
        """鍚戣彍鍗曟坊鍔犲姩浣?""
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _init_toolbar(self):
        """鍒濆鍖栧伐鍏锋爮"""
        self.toolbar = QToolBar("涓诲伐鍏锋爮")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.toolbar)

        # 閫氱敤宸ュ叿鏍忔寜閽?        self.toolbar.addAction("馃搫 鏂板缓", self._on_new_project)
        self.toolbar.addAction("馃搨 鎵撳紑", self._on_open_project)
        self.toolbar.addAction("馃捑 淇濆瓨", self._on_save_project)
        self.toolbar.addSeparator()
        # 瀛愮被鍙坊鍔犳洿澶氬伐鍏锋爮鎸夐挳

    def _init_status_bar(self):
        """鍒濆鍖栫姸鎬佹爮"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # 椤圭洰淇℃伅
        self.status_project = QLabel("椤圭洰: 鏈墦寮€")
        self.statusbar.addWidget(self.status_project, 1)

        # 灏辩华鐘舵€?        self.status_ready = QLabel("灏辩华")
        self.statusbar.addPermanentWidget(self.status_ready)

        # 鐗堟湰淇℃伅
        self.status_version = QLabel(f"v{self.version}")
        self.statusbar.addPermanentWidget(self.status_version)

    def _init_dock_panels(self):
        """鍒濆鍖栧彲鍋滈潬闈㈡澘"""
        # 鏃ュ織闈㈡澘
        self.log_dock = QDockWidget("馃搵 鏃ュ織", self)
        self.log_dock.setWidget(self.log_panel)
        self.log_dock.setMinimumHeight(100)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        # 椤圭洰闈㈡澘 (瀛愮被鍙互瑕嗙洊鎴栨墿灞?
        self.project_panel = self._create_project_panel()
        if self.project_panel:
            self.project_dock = QDockWidget("馃搧 椤圭洰", self)
            self.project_dock.setWidget(self.project_panel)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_dock)

    def _create_project_panel(self):
        """鍒涘缓椤圭洰绠＄悊闈㈡澘 (瀛愮被鍙鐩?"""
        from widgets.project_widget import ProjectWidget
        return ProjectWidget(self.project_mgr, self.logger)

    # ===== 涓績鍐呭鍖?(瀛愮被蹇呴』瀹炵幇) =====
    def set_central_content(self, widget):
        """璁剧疆涓績鍐呭鍖?""
        self.setCentralWidget(widget)

    # ===== 鏂囦欢鎿嶄綔 =====
    def _on_new_project(self):
        """鏂板缓椤圭洰"""
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "鏂板缓椤圭洰", "椤圭洰鍚嶇О:")
        if ok and name:
            project = self.project_mgr.new_project(name)
            self._update_project_status(name)
            self._update_recent_menu()
            self.logger.info(f"鏂板缓椤圭洰: {name}")

    def _on_open_project(self):
        """鎵撳紑椤圭洰"""
        path, _ = QFileDialog.getOpenFileName(
            self, "鎵撳紑椤圭洰",
            self.config.get("last_open_dir", str(BASE_DIR / "Projects")),
            "椤圭洰鏂囦欢 (project.json);;鎵€鏈夋枃浠?(*)"
        )
        if path:
            try:
                project = self.project_mgr.open_project(path)
                self._update_project_status(project.data["name"])
                self._update_recent_menu()
            except Exception as e:
                QMessageBox.critical(self, "閿欒", f"鏃犳硶鎵撳紑椤圭洰:\n{e}")

    def _on_save_project(self):
        """淇濆瓨椤圭洰"""
        if self.project_mgr.current_project:
            self.project_mgr.save_project()
            self.status_ready.setText("宸蹭繚瀛?)
            QTimer.singleShot(3000, lambda: self.status_ready.setText("灏辩华"))
        else:
            self._on_save_as()

    def _on_save_as(self):
        """鍙﹀瓨涓?""
        if not self.project_mgr.current_project:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "鍙﹀瓨涓?,
            str(BASE_DIR / "Projects" / "project.json"),
            "椤圭洰鏂囦欢 (project.json)"
        )
        if path:
            self.project_mgr.current_project.save(Path(path))
            self._update_project_status(self.project_mgr.current_project.data["name"])

    def _open_recent(self, path):
        """鎵撳紑鏈€杩戦」鐩?""
        try:
            project = self.project_mgr.open_project(path)
            self._update_project_status(project.data["name"])
        except Exception as e:
            QMessageBox.warning(self, "璀﹀憡", f"鏃犳硶鎵撳紑椤圭洰:\n{e}")

    def _update_recent_menu(self):
        """鏇存柊鏈€杩戦」鐩彍鍗?""
        self.recent_menu.clear()
        recent = self.config.get_recent_projects()
        if not recent:
            action = QAction("鏃犳渶杩戦」鐩?, self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
        else:
            for path in recent[:10]:
                name = Path(path).parent.name if path.endswith("project.json") else Path(path).stem
                action = QAction(f"{name}  ({path})", self)
                action.triggered.connect(lambda checked, p=path: self._open_recent(p))
                self.recent_menu.addAction(action)

    def _update_project_status(self, name):
        """鏇存柊鐘舵€佹爮椤圭洰淇℃伅"""
        self.status_project.setText(f"椤圭洰: {name}")

    # ===== 鑷姩淇濆瓨涓庡浠?=====
    def _auto_save(self):
        """鑷姩淇濆瓨"""
        if self.project_mgr.current_project:
            self.project_mgr.save_project()
            self.logger.debug("鑷姩淇濆瓨瀹屾垚")

    def _save_geometry(self):
        """淇濆瓨绐楀彛鍑犱綍"""
        self.config.save_window_layout(self.tool_name, self.saveGeometry().toHex().data().decode())

    def _restore_geometry(self):
        """鎭㈠绐楀彛鍑犱綍"""
        geo = self.config.load_window_layout(self.tool_name)
        if geo:
            self.restoreGeometry(QByteArray.fromHex(geo.encode()))

    # ===== 涓婚鍒囨崲 =====
    def _switch_theme(self, theme_name):
        """鍒囨崲涓婚"""
        self.config.set("theme", theme_name)
        self.setStyleSheet(generate_stylesheet(theme_name))
        self.logger.info(f"宸插垏鎹㈠埌{theme_name}涓婚")

    # ===== 闈㈡澘鍒囨崲 =====
    def _toggle_log_panel(self):
        self.log_dock.setVisible(not self.log_dock.isVisible())

    def _toggle_project_panel(self):
        if hasattr(self, 'project_dock'):
            self.project_dock.setVisible(not self.project_dock.isVisible())

    # ===== 鎷栨斁鏀寔 =====
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            self._handle_dropped_file(path)

    def _handle_dropped_file(self, path):
        """澶勭悊鎷栨斁鏂囦欢 (瀛愮被瑕嗙洊)"""
        self.logger.info(f"鏀跺埌鏂囦欢: {path}")

    # ===== 甯姪 =====
    def _show_about(self):
        QMessageBox.about(self, f"鍏充簬 {self.tool_title}",
            f"<h2>{self.tool_title}</h2>"
            f"<p>鐗堟湰: {self.version}</p>"
            f"<p>Lighting Designer Workstation - 鑸炲彴鐏厜璁捐宸ヤ綔绔?/p>"
            f"<p>涓撲笟鑸炲彴鐏厜璁捐宸ュ叿闆?/p>")

    def _show_shortcuts(self):
        """鏄剧ず蹇嵎閿垪琛?""
        shortcuts_text = """
        <table>
        <tr><td><b>Ctrl+N</b></td><td>鏂板缓椤圭洰</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>鎵撳紑椤圭洰</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>淇濆瓨椤圭洰</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>鍙﹀瓨涓?/td></tr>
        <tr><td><b>Ctrl+L</b></td><td>鏃ュ織绐楀彛</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>椤圭洰绠＄悊鍣?/td></tr>
        <tr><td><b>F11</b></td><td>鍏ㄥ睆</td></tr>
        <tr><td><b>Alt+F4</b></td><td>閫€鍑?/td></tr>
        </table>
        """
        QMessageBox.information(self, "蹇嵎閿垪琛?, shortcuts_text)

    def _stub(self, name):
        """鍗犱綅鎿嶄綔"""
        return lambda: self.logger.debug(f"{name}: 鍔熻兘寰呭疄鐜?)

    # ===== 鍏抽棴浜嬩欢 =====
    def closeEvent(self, event):
        """鍏抽棴鍓嶈嚜鍔ㄤ繚瀛?""
        if self.project_mgr.current_project:
            self.project_mgr.save_project()
        self._save_geometry()
        self.logger.info(f"{self.tool_title} 宸插叧闂?)
        event.accept()

