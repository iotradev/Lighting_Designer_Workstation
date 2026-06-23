# -*- coding: utf-8 -*-
"""
BaseToolWindow - GrandMA3 风格基础工具窗口框架

功能特性:
- 菜单栏(文件/编辑/视图/工具/帮助)
- 状态栏(项目信息/就绪状态/版本号)
- 可停靠面板(日志面板/项目面板)
- 自动保存/主题切换/DPI适配
- 最近项目记录/拖放支持
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QMenu, QStatusBar, QLabel,
    QDockWidget, QFileDialog, QMessageBox, QApplication,
)
from PySide6.QtCore import Qt, QTimer, QByteArray, QSize
from PySide6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent

BASE_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "Common"))

from themes.stylesheet import generate_stylesheet
from config.config_manager import ConfigManager
from log_system.tool_logger import LogPanel
from project.project_manager import ProjectManager


def _ensure_dpi_awareness():
    """确保DPI适配，设置最小字号为11pt"""
    app = QApplication.instance()
    if app:
        font = app.font()
        if font.pointSize() < 11:
            font.setPointSize(11)
            app.setFont(font)


class BaseToolWindow(QMainWindow):
    """基础工具窗口，为所有工具提供统一的界面框架。"""

    def __init__(self, tool_name: str, tool_title: str, version: str = "1.0.0",
                 width: int = 1400, height: int = 900, parent=None):
        super().__init__(parent)
        _ensure_dpi_awareness()

        self.tool_name = tool_name
        self.tool_title = tool_title
        self.version = version

        self.config = ConfigManager()
        self.project_mgr = ProjectManager()

        theme = self.config.get("theme", "dark")
        self.setStyleSheet(generate_stylesheet(theme))

        self.setWindowTitle(f"{tool_title} - Lighting Designer Workstation")
        self.setMinimumSize(800, 600)
        self.resize(width, height)
        self.setAcceptDrops(True)

        self._restore_geometry()

        self.log_panel = LogPanel(tool_name)
        self.logger = self.log_panel.get_logger()

        self._init_menu_bar()
        self._init_toolbar()
        self._init_status_bar()
        self._init_dock_panels()

        if self.config.get("auto_save", True):
            self._auto_save_timer = QTimer(self)
            self._auto_save_timer.timeout.connect(self._auto_save)
            interval = self.config.get("auto_save_interval", 300) * 1000
            self._auto_save_timer.start(interval)

        self._layout_timer = QTimer(self)
        self._layout_timer.timeout.connect(self._save_geometry)
        self._layout_timer.start(60000)

        self.logger.info(f"{tool_title} v{version} started")

    def _init_menu_bar(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        self._add_action(file_menu, "新建(&N)", self._on_new_project, QKeySequence.StandardKey.New)
        self._add_action(file_menu, "打开(&O)...", self._on_open_project, QKeySequence.StandardKey.Open)
        file_menu.addSeparator()
        self._add_action(file_menu, "保存(&S)", self._on_save_project, QKeySequence.StandardKey.Save)
        self._add_action(file_menu, "另存为(&A)...", self._on_save_as, QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()
        self.recent_menu = file_menu.addMenu("最近项目(&R)")
        self._update_recent_menu()
        file_menu.addSeparator()
        self._add_action(file_menu, "退出(&Q)", self.close, QKeySequence("Alt+F4"))

        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        self._add_action(edit_menu, "撤销", self._stub("Undo"), QKeySequence.StandardKey.Undo, enabled=False)
        self._add_action(edit_menu, "重做", self._stub("Redo"), QKeySequence.StandardKey.Redo, enabled=False)
        edit_menu.addSeparator()
        self._add_action(edit_menu, "剪切", self._stub("Cut"), QKeySequence.StandardKey.Cut, enabled=False)
        self._add_action(edit_menu, "复制", self._stub("Copy"), QKeySequence.StandardKey.Copy, enabled=False)
        self._add_action(edit_menu, "粘贴", self._stub("Paste"), QKeySequence.StandardKey.Paste, enabled=False)

        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        self._add_action(view_menu, "日志面板", self._toggle_log_panel, QKeySequence("Ctrl+L"))
        self._add_action(view_menu, "项目面板", self._toggle_project_panel, QKeySequence("Ctrl+P"))
        view_menu.addSeparator()
        self._add_action(view_menu, "深色主题", lambda: self._switch_theme("dark"))
        self._add_action(view_menu, "浅色主题", lambda: self._switch_theme("light"))

        # 工具菜单
        self.tool_menu = menubar.addMenu("工具(&T)")

        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        self._add_action(help_menu, "关于", self._show_about)
        self._add_action(help_menu, "快捷键", self._show_shortcuts)

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
        """初始化工具栏（默认隐藏）"""
        from PySide6.QtWidgets import QToolBar
        self.toolbar = QToolBar("常用工具")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)
        self.toolbar.addAction("新建", self._on_new_project)
        self.toolbar.addAction("打开", self._on_open_project)
        self.toolbar.addAction("保存", self._on_save_project)
        self.toolbar.setVisible(False)

    def _init_status_bar(self):
        """初始化状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_project = QLabel("项目: 未打开")
        self.status_project.setStyleSheet("color: #888; font-size: 12px;")
        self.statusbar.addWidget(self.status_project, 1)

        self.status_ready = QLabel("就绪")
        self.status_ready.setStyleSheet("color: #4ec9b0; font-size: 12px;")
        self.statusbar.addPermanentWidget(self.status_ready)

        self.status_version = QLabel(f"v{self.version}")
        self.status_version.setStyleSheet("color: #666; font-size: 11px;")
        self.statusbar.addPermanentWidget(self.status_version)

    def _init_dock_panels(self):
        """初始化可停靠面板"""
        # 日志面板
        self.log_dock = QDockWidget("日志输出", self)
        self.log_dock.setWidget(self.log_panel)
        self.log_dock.setMinimumHeight(60)
        self.log_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetClosable |
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.log_dock.setMaximumHeight(200)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.log_dock)
        self.log_dock.setVisible(False)

        # 项目面板
        self.project_panel = self._create_project_panel()
        if self.project_panel:
            self.project_dock = QDockWidget("项目管理", self)
            self.project_dock.setWidget(self.project_panel)
            self.project_dock.setMinimumWidth(200)
            self.project_dock.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetClosable |
                QDockWidget.DockWidgetFeature.DockWidgetMovable |
                QDockWidget.DockWidgetFeature.DockWidgetFloatable
            )
            self.project_dock.setMaximumWidth(300)
            self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_dock)
            self.project_dock.setVisible(False)

    def _create_project_panel(self):
        """创建项目面板控件"""
        from widgets.project_widget import ProjectWidget
        return ProjectWidget(self.project_mgr, self.logger)

    # ===== 内容区域 =====

    def set_central_content(self, widget):
        """设置中央内容区域"""
        self.setCentralWidget(widget)

    # ===== 项目操作 =====

    def _on_new_project(self):
        """新建项目"""
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建项目", "项目名称:")
        if ok and name:
            project = self.project_mgr.new_project(name)
            self._update_project_status(name)
            self._update_recent_menu()
            self.logger.info(f"新建项目: {name}")

    def _on_open_project(self):
        """打开项目"""
        path, _ = QFileDialog.getOpenFileName(
            self, "打开项目",
            self.config.get("last_open_dir", str(BASE_DIR / "Projects")),
            "项目文件 (project.json);;所有文件 (*)"
        )
        if path:
            try:
                project = self.project_mgr.open_project(path)
                self._update_project_status(project.data["name"])
                self._update_recent_menu()
            except Exception as e:
                QMessageBox.critical(self, "打开失败", f"无法打开项目:\n{e}")

    def _on_save_project(self):
        """保存项目"""
        if self.project_mgr.current_project:
            self.project_mgr.save_project()
            self.status_ready.setText("已保存")
            QTimer.singleShot(3000, lambda: self.status_ready.setText("就绪"))
        else:
            self._on_save_as()

    def _on_save_as(self):
        """另存为"""
        if not self.project_mgr.current_project:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "另存为",
            str(BASE_DIR / "Projects" / "project.json"),
            "项目文件 (project.json)"
        )
        if path:
            self.project_mgr.current_project.save(Path(path))
            self._update_project_status(self.project_mgr.current_project.data["name"])

    def _open_recent(self, path):
        """打开最近项目"""
        try:
            project = self.project_mgr.open_project(path)
            self._update_project_status(project.data["name"])
        except Exception as e:
            QMessageBox.warning(self, "打开失败", f"无法打开项目:\n{e}")

    def _update_recent_menu(self):
        """更新最近项目菜单"""
        self.recent_menu.clear()
        recent = self.config.get_recent_projects()
        if not recent:
            action = QAction("无最近项目", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
        else:
            for path in recent[:10]:
                name = Path(path).parent.name if path.endswith("project.json") else Path(path).stem
                action = QAction(f"{name}  ({path})", self)
                action.triggered.connect(lambda checked, p=path: self._open_recent(p))
                self.recent_menu.addAction(action)

    def _update_project_status(self, name):
        """更新状态栏项目名"""
        self.status_project.setText(f"项目: {name}")

    # ===== 自动保存 =====

    def _auto_save(self):
        """自动保存"""
        if self.project_mgr.current_project:
            self.project_mgr.save_project()
            self.logger.debug("自动保存已触发")

    def _save_geometry(self):
        """保存窗口位置"""
        self.config.save_window_layout(self.tool_name, self.saveGeometry().toHex().data().decode())

    def _restore_geometry(self):
        """恢复窗口位置"""
        geo = self.config.load_window_layout(self.tool_name)
        if geo:
            self.restoreGeometry(QByteArray.fromHex(geo.encode()))

    # ===== 主题切换 =====

    def _switch_theme(self, theme_name):
        """切换主题"""
        self.config.set("theme", theme_name)
        self.setStyleSheet(generate_stylesheet(theme_name))
        self.logger.info(f"切换主题: {theme_name}")

    # ===== 面板切换 =====

    def _toggle_log_panel(self):
        self.log_dock.setVisible(not self.log_dock.isVisible())

    def _toggle_project_panel(self):
        if hasattr(self, 'project_dock'):
            self.project_dock.setVisible(not self.project_dock.isVisible())

    # ===== 拖放支持 =====

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            self._handle_dropped_file(path)

    def _handle_dropped_file(self, path):
        """处理拖放文件（子类可重写）"""
        self.logger.info(f"拖放文件: {path}")

    # ===== 帮助 =====

    def _show_about(self):
        QMessageBox.about(self, f"关于 {self.tool_title}",
            f"<h2>{self.tool_title}</h2>"
            f"<p>版本: {self.version}</p>"
            f"<p>Lighting Designer Workstation - 舞台灯光设计工作站</p>"
            f"<p>专业舞台灯光设计与编程工具集</p>")

    def _show_shortcuts(self):
        """显示快捷键列表"""
        shortcuts_text = """
        <table>
        <tr><td><b>Ctrl+N</b></td><td>新建项目</td></tr>
        <tr><td><b>Ctrl+O</b></td><td>打开项目</td></tr>
        <tr><td><b>Ctrl+S</b></td><td>保存项目</td></tr>
        <tr><td><b>Ctrl+Shift+S</b></td><td>另存为</td></tr>
        <tr><td><b>Ctrl+L</b></td><td>日志面板</td></tr>
        <tr><td><b>Ctrl+P</b></td><td>项目面板</td></tr>
        <tr><td><b>Alt+F4</b></td><td>退出</td></tr>
        </table>
        """
        QMessageBox.information(self, "快捷键", shortcuts_text)

    def _stub(self, name):
        """占位操作（未实现的功能）"""
        return lambda: self.logger.debug(f"{name}: 功能未实现")

    # ===== 关闭 =====

    def closeEvent(self, event):
        """关闭事件"""
        if self.project_mgr.current_project:
            self.project_mgr.save_project()
        self._save_geometry()
        self.logger.info(f"{self.tool_title} 已退出")
        event.accept()
