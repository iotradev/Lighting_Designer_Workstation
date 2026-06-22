# -*- coding: utf-8 -*-

"""
BaseToolWindow - GrandMA3 风格基础工具窗口框架

功能特性:
- 菜单栏(文件/编辑/视图/工具/帮助)
- 工具栏(常用操作快捷按钮)
- 状态栏(项目信息/就绪状态/版本号)
- 可停靠面板(日志面板/项目面板)
- 自动保存/主题切换/DPI适配
- 最近项目记录/拖放支持
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

    """确保DPI适配，设置最小字号为11pt"""

    app = QApplication.instance()

    if app:

        # 调整字体大小以适配高DPI屏幕

        font = app.font()

        if font.pointSize() < 11:

            font.setPointSize(11)

            app.setFont(font)



# 

BASE_DIR = Path(__file__).parent.parent.parent

sys.path.insert(0, str(BASE_DIR / "Common"))



from themes.stylesheet import generate_stylesheet

from config.config_manager import ConfigManager

from log_system.tool_logger import ToolLogger, LogPanel

from project.project_manager import ProjectManager





class BaseToolWindow(QMainWindow):



    """基础工具窗口，为所有工具提供统一的界面框架。"""



    def __init__(self, tool_name: str, tool_title: str, version: str = "1.0.0",

                 width: int = 1400, height: int = 900, parent=None):

        super().__init__(parent)

        # 初始化DPI适配

        _ensure_dpi_awareness()

        self.tool_name = tool_name

        self.tool_title = tool_title

        self.version = version



        self.config = ConfigManager()

        self.project_mgr = ProjectManager()



        # 初始化配置管理器

        theme = self.config.get("theme", "dark")

        self.setStyleSheet(generate_stylesheet(theme))



        # 

        self.setWindowTitle(f"{tool_title} - Lighting Designer Workstation")

        self.setMinimumSize(800, 600)

        self.resize(width, height)

        self.setAcceptDrops(True)



        # 初始化日志面板

        self._restore_geometry()



        self.log_panel = LogPanel(tool_name)

        self.logger = self.log_panel.get_logger()



        # 

        self._init_menu_bar()

        self._init_toolbar()

        self._init_status_bar()

        self._init_dock_panels()



        # 应用主题样式

        if self.config.get("auto_save", True):

            self._auto_save_timer = QTimer(self)

            self._auto_save_timer.timeout.connect(self._auto_save)

            interval = self.config.get("auto_save_interval", 300) * 1000

            self._auto_save_timer.start(interval)



        # 恢复上次窗口位置

        self._layout_timer = QTimer(self)

        self._layout_timer.timeout.connect(self._save_geometry)

        self._layout_timer.start(60000)  # 



        self.logger.info(f"{tool_title} v{version} started")



    def _init_menu_bar(self):

        """"""

        menubar = self.menuBar()



        # 启用自动保存

        file_menu = menubar.addMenu("文件(&F)")

        self._add_action(file_menu, "新建(&N)", self._on_new_project, QKeySequence.StandardKey.New, tooltip="新建项目")

        self._add_action(file_menu, "打开(&O)...", self._on_open_project, QKeySequence.StandardKey.Open, tooltip="打开已有项目")

        file_menu.addSeparator()

        self._add_action(file_menu, "保存(&S)", self._on_save_project, QKeySequence.StandardKey.Save, tooltip="保存当前项目")

        self._add_action(file_menu, "另存为(&A)...", self._on_save_as, QKeySequence("Ctrl+Shift+S"), tooltip="另存为新文件")

        file_menu.addSeparator()

        self.recent_menu = file_menu.addMenu("最近项目(&R)")

        self._update_recent_menu()

        file_menu.addSeparator()

        self._add_action(file_menu, "退出(&Q)", self.close, QKeySequence("Alt+F4"), tooltip="退出程序")



        edit_menu = menubar.addMenu("编辑(&E)")

        self._add_action(edit_menu, "撤销", self._stub("Undo"), QKeySequence.StandardKey.Undo, tooltip="撤销", enabled=False)

        self._add_action(edit_menu, "重做", self._stub("Redo"), QKeySequence.StandardKey.Redo, tooltip="重做", enabled=False)

        edit_menu.addSeparator()

        self._add_action(edit_menu, "剪切", self._stub("Cut"), QKeySequence.StandardKey.Cut, tooltip="剪切", enabled=False)

        self._add_action(edit_menu, "复制", self._stub("Copy"), QKeySequence.StandardKey.Copy, tooltip="复制", enabled=False)

        self._add_action(edit_menu, "粘贴", self._stub("Paste"), QKeySequence.StandardKey.Paste, tooltip="粘贴", enabled=False)



        view_menu = menubar.addMenu("视图(&V)")

        self._add_action(view_menu, "切换日志面板", self._toggle_log_panel, QKeySequence("Ctrl+L"), tooltip="显示/隐藏日志面板")

        self._add_action(view_menu, "切换项目面板", self._toggle_project_panel, QKeySequence("Ctrl+P"), tooltip="显示/隐藏项目面板")

        view_menu.addSeparator()

        self._add_action(view_menu, "深色主题", lambda: self._switch_theme("dark"), tooltip="切换到深色主题")

        self._add_action(view_menu, "浅色主题", lambda: self._switch_theme("light"), tooltip="切换到浅色主题")



        self.tool_menu = menubar.addMenu("工具(&T)")

        help_menu = menubar.addMenu("帮助(&H)")

        self._add_action(help_menu, "关于", self._show_about, tooltip="关于本程序")

        self._add_action(help_menu, "快捷键", self._show_shortcuts, tooltip="查看快捷键列表")



    def _add_action(self, menu, text, slot, shortcut=None, tooltip=None, enabled=True):

        action = QAction(text, self)
        if shortcut:
            action.setShortcut(shortcut)
        if tooltip:
            action.setToolTip(tooltip)
        action.setEnabled(enabled)
        action.triggered.connect(slot)
        menu.addAction(action)
        return action



    def _init_toolbar(self):

        """"""

        self.toolbar = QToolBar("常用工具")

        self.toolbar.setMovable(False)

        self.toolbar.setIconSize(QSize(24, 24))

        self.addToolBar(self.toolbar)



        self.toolbar.addAction(" ", self._on_new_project)

        self.toolbar.addAction(" ", self._on_open_project)

        self.toolbar.addAction(" ", self._on_save_project)

        self.toolbar.addSeparator()

        # 



    def _init_status_bar(self):

        """"""

        self.statusbar = QStatusBar()

        self.setStatusBar(self.statusbar)



        # 

        self.status_project = QLabel("项目: ")

        self.statusbar.addWidget(self.status_project, 1)



        self.status_ready = QLabel("就绪")
        self.statusbar.addPermanentWidget(self.status_ready)



        # 

        self.status_version = QLabel(f"v{self.version}")

        self.statusbar.addPermanentWidget(self.status_version)



    def _init_dock_panels(self):

        """"""

        # 日志面板

        self.log_dock = QDockWidget("\u65e5\u5fd7\u8f93\u51fa", self)

        self.log_dock.setWidget(self.log_panel)

        self.log_dock.setMinimumHeight(60)

        self.log_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)

        self.log_dock.setMaximumHeight(200)

        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)

        self.log_dock.setVisible(False)



        # 项目面板（可选）

        self.project_panel = self._create_project_panel()

        if self.project_panel:

            self.project_dock = QDockWidget("\u9879\u76ee\u7ba1\u7406", self)

            self.project_dock.setWidget(self.project_panel)

            self.project_dock.setMinimumWidth(200)

            self.project_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetFloatable)

            self.project_dock.setMaximumWidth(300)

            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_dock)

            self.project_dock.setVisible(False)



    def _create_project_panel(self):

        """\u521b\u5efa\u9879\u76ee\u9762\u677f\u63a7\u4ef6"""

        from widgets.project_widget import ProjectWidget

        return ProjectWidget(self.project_mgr, self.logger)



    # ===== 内容区域 =====

    def set_central_content(self, widget):

        """TODO"""""

        self.setCentralWidget(widget)



    # =====  =====

    def _on_new_project(self):

        """"""

        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "", ":")

        if ok and name:

            project = self.project_mgr.new_project(name)

            self._update_project_status(name)

            self._update_recent_menu()

            self.logger.info(f": {name}")



    def _on_open_project(self):

        """"""

        path, _ = QFileDialog.getOpenFileName(

            self, "",

            self.config.get("last_open_dir", str(BASE_DIR / "Projects")),

            "项目文件 (project.json);;所有文件 (*)"

        )

        if path:

            try:

                project = self.project_mgr.open_project(path)

                self._update_project_status(project.data["name"])

                self._update_recent_menu()

            except Exception as e:

                QMessageBox.critical(self, "", f":\n{e}")



    def _on_save_project(self):

        """"""

        if self.project_mgr.current_project:

            self.project_mgr.save_project()

            self.status_ready.setText("已保存")

            QTimer.singleShot(3000, lambda: self.status_ready.setText("就绪"))

        else:

            self._on_save_as()



    def _on_save_as(self):

        """TODO"""""

        if not self.project_mgr.current_project:

            return

        path, _ = QFileDialog.getSaveFileName(

            self, "",

            str(BASE_DIR / "Projects" / "project.json"),

            "项目文件 (project.json)"

        )

        if path:

            self.project_mgr.current_project.save(Path(path))

            self._update_project_status(self.project_mgr.current_project.data["name"])



    def _open_recent(self, path):

        """TODO"""""

        try:

            project = self.project_mgr.open_project(path)

            self._update_project_status(project.data["name"])

        except Exception as e:

            QMessageBox.warning(self, "", f":\n{e}")



    def _update_recent_menu(self):

        """TODO"""""

        self.recent_menu.clear()

        recent = self.config.get_recent_projects()

        if not recent:

            action = QAction("\u65e0\u6700\u8fd1\u9879\u76ee", self)

            action.setEnabled(False)

            self.recent_menu.addAction(action)

        else:

            for path in recent[:10]:

                name = Path(path).parent.name if path.endswith("project.json") else Path(path).stem

                action = QAction(f"{name}  ({path})", self)

                action.triggered.connect(lambda checked, p=path: self._open_recent(p))

                self.recent_menu.addAction(action)



    def _update_project_status(self, name):

        """"""

        self.status_project.setText(f"项目: {name}")



    # ===== 自动保存 =====

    def _auto_save(self):

        """"""

        if self.project_mgr.current_project:

            self.project_mgr.save_project()

            self.logger.debug("自动保存已触发")



    def _save_geometry(self):

        """"""

        self.config.save_window_layout(self.tool_name, self.saveGeometry().toHex().data().decode())



    def _restore_geometry(self):

        """"""

        geo = self.config.load_window_layout(self.tool_name)

        if geo:

            self.restoreGeometry(QByteArray.fromHex(geo.encode()))



    # =====  =====

    def _switch_theme(self, theme_name):

        """"""

        self.config.set("theme", theme_name)

        self.setStyleSheet(generate_stylesheet(theme_name))

        self.logger.info(f"{theme_name}")



    # =====  =====

    def _toggle_log_panel(self):

        self.log_dock.setVisible(not self.log_dock.isVisible())



    def _toggle_project_panel(self):

        if hasattr(self, 'project_dock'):

            self.project_dock.setVisible(not self.project_dock.isVisible())



    # =====  =====

    def dragEnterEvent(self, event: QDragEnterEvent):

        if event.mimeData().hasUrls():

            event.acceptProposedAction()



    def dropEvent(self, event: QDropEvent):

        urls = event.mimeData().urls()

        for url in urls:

            path = url.toLocalFile()

            self._handle_dropped_file(path)



    def _handle_dropped_file(self, path):

        """ ()"""

        self.logger.info(f": {path}")



    # =====  =====

    def _show_about(self):

        QMessageBox.about(self, f" {self.tool_title}",

            f"<h2>{self.tool_title}</h2>"

            f"<p>: {self.version}</p>"

            f"<p>Lighting Designer Workstation - 舞台灯光设计工作站</p>"

            f"<p>专业舞台灯光设计与编程工具集</p>")



    def _show_shortcuts(self):

        """TODO"""""

        shortcuts_text = """

        <table>

        <tr><td><b>Ctrl+N</b></td><td></td></tr>

        <tr><td><b>Ctrl+O</b></td><td></td></tr>

        <tr><td><b>Ctrl+S</b></td><td></td></tr>

        <tr><td><b>Ctrl+Shift+S</b></td><td>另存为</td></tr>

        <tr><td><b>Ctrl+L</b></td><td></td></tr>

        <tr><td><b>Ctrl+P</b></td><td>项目面板</td></tr>

        <tr><td><b>F11</b></td><td></td></tr>

        <tr><td><b>Alt+F4</b></td><td>退出</td></tr>

        </table>

        """

        QMessageBox.information(self, "", shortcuts_text)



    def _stub(self, name):

        """"""

        return lambda: self.logger.debug(f"{name}: ")



    # =====  =====

    def closeEvent(self, event):

        """TODO"""""

        if self.project_mgr.current_project:

            self.project_mgr.save_project()

        self._save_geometry()

        self.logger.info(f"{self.tool_title} ")

        event.accept()


