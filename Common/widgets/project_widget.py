# -*- coding: utf-8 -*-
"""
椤圭洰绠＄悊闈㈡澘缁勪欢
鏄剧ず椤圭洰鍒楄〃銆佹敮鎸佹柊寤?鎵撳紑/鍒犻櫎椤圭洰
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QInputDialog, QMessageBox, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction
from pathlib import Path


class ProjectWidget(QWidget):
    """椤圭洰绠＄悊闈㈡澘"""
    project_selected = Signal(str)  # 鍙戝皠椤圭洰璺緞

    def __init__(self, project_mgr, logger=None, parent=None):
        super().__init__(parent)
        self.project_mgr = project_mgr
        self.logger = logger
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 鏍囬
        title = QLabel("馃搧 椤圭洰绠＄悊")
        title.setStyleSheet("font-weight:bold; color:#e8912d; font-size:14px;")
        layout.addWidget(title)

        # 鎸夐挳琛?        btn_row = QHBoxLayout()
        btn_new = QPushButton("鏂板缓")
        btn_new.setObjectName("accent_btn")
        btn_new.clicked.connect(self._new_project)
        btn_row.addWidget(btn_new)

        btn_refresh = QPushButton("鍒锋柊")
        btn_refresh.clicked.connect(self.refresh)
        btn_row.addWidget(btn_refresh)
        layout.addLayout(btn_row)

        # 椤圭洰鍒楄〃
        self.project_list = QListWidget()
        self.project_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.project_list.customContextMenuRequested.connect(self._context_menu)
        self.project_list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.project_list)

        # 淇℃伅鍖?        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color:#808080; font-size:11px;")
        layout.addWidget(self.info_label)

    def refresh(self):
        """鍒锋柊椤圭洰鍒楄〃"""
        self.project_list.clear()
        projects = self.project_mgr.list_projects()
        for p in projects:
            item = QListWidgetItem(f"馃搫 {p['name']}")
            item.setData(Qt.ItemDataRole.UserRole, p["path"])
            item.setToolTip(f"鍦哄湴: {p.get('venue', '')}\n淇敼: {p.get('modified', '')}")
            self.project_list.addItem(item)
        self.info_label.setText(f"鍏?{len(projects)} 涓」鐩?)

    def _new_project(self):
        name, ok = QInputDialog.getText(self, "鏂板缓椤圭洰", "椤圭洰鍚嶇О:")
        if ok and name:
            self.project_mgr.new_project(name)
            self.refresh()
            self.project_selected.emit(str(self.project_mgr.current_project.path))

    def _on_double_click(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            try:
                self.project_mgr.open_project(path)
                self.project_selected.emit(path)
            except Exception as e:
                QMessageBox.warning(self, "閿欒", str(e))

    def _context_menu(self, pos):
        item = self.project_list.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        menu.addAction("鎵撳紑", lambda: self._on_double_click(item))
        menu.addAction("鍦ㄨ祫婧愮鐞嗗櫒涓墦寮€", lambda: self._open_in_explorer(item))
        menu.addSeparator()
        menu.addAction("鍒犻櫎", lambda: self._delete_project(item))
        menu.exec_(self.project_list.mapToGlobal(pos))

    def _open_in_explorer(self, item):
        from launcher_utils import run_process
        path = Path(item.data(Qt.ItemDataRole.UserRole)).parent
        run_process(["explorer", str(path)], logger=self.logger)

    def _delete_project(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        name = item.text().replace("馃搫 ", "")
        reply = QMessageBox.question(
            self, "纭鍒犻櫎",
            f'纭畾瑕佸垹闄ら」鐩?"{name}" 鍚楋紵\n姝ゆ搷浣滀笉鍙仮澶嶃€?,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import shutil
            project_dir = Path(path).parent
            if project_dir.exists():
                shutil.rmtree(project_dir)
            self.refresh()

