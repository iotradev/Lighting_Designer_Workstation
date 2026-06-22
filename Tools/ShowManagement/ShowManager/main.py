# -*- coding: utf-8 -*-
"""
演出管理器 - 中央管理枢纽
管理演出项目信息、场景列表、Cue总览和时间线概览
"""
import sys, json, csv, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QHeaderView, QMessageBox, QFileDialog, QSplitter,
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QFont


class ShowInfoWidget(QWidget):
    """演出信息编辑区"""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QFormLayout(self)
        self.show_name = QLineEdit()
        self.venue = QLineEdit()
        self.client = QLineEdit()
        self.ld_name = QLineEdit()
        self.date = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        layout.addRow("演出名称:", self.show_name)
        layout.addRow("演出场地:", self.venue)
        layout.addRow("客户/甲方:", self.client)
        layout.addRow("灯光设计:", self.ld_name)
        layout.addRow("演出日期:", self.date)
        layout.addRow("备注:", self.notes)

    def to_dict(self):
        return {
            "name": self.show_name.text(),
            "venue": self.venue.text(),
            "client": self.client.text(),
            "ld": self.ld_name.text(),
            "date": self.date.text(),
            "notes": self.notes.toPlainText()
        }

    def from_dict(self, d):
        self.show_name.setText(d.get("name", ""))
        self.venue.setText(d.get("venue", ""))
        self.client.setText(d.get("client", ""))
        self.ld_name.setText(d.get("ld", ""))
        self.date.setText(d.get("date", ""))
        self.notes.setPlainText(d.get("notes", ""))


class SceneListWidget(QWidget):
    """场景列表管理"""
    scene_changed = None  # signal placeholder

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scenes = []
        layout = QVBoxLayout(self)

        # 工具栏
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("➕ 添加场景")
        btn_edit = QPushButton("✏️ 编辑场景")
        btn_del = QPushButton("🗑️ 删除场景")
        btn_up = QPushButton("⬆️ 上移")
        btn_down = QPushButton("⬇️ 下移")
        btn_add.clicked.connect(self.add_scene)
        btn_edit.clicked.connect(self.edit_scene)
        btn_del.clicked.connect(self.delete_scene)
        btn_up.clicked.connect(self.move_up)
        btn_down.clicked.connect(self.move_down)
        for b in [btn_add, btn_edit, btn_del, btn_up, btn_down]:
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)

        # 表格
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["序号", "场景名称", "灯具预设", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def add_scene(self):
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("添加场景")
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)
        name_edit = QLineEdit()
        preset_combo = QComboBox()
        preset_combo.addItems(["默认", "暖色调", "冷色调", "追光", "染色", "特效", "自定义"])
        desc_edit = QLineEdit()
        form.addRow("场景名称:", name_edit)
        form.addRow("灯具预设:", preset_combo)
        form.addRow("描述:", desc_edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted and name_edit.text():
            scene = {
                "name": name_edit.text(),
                "preset": preset_combo.currentText(),
                "description": desc_edit.text(),
                "cues": []
            }
            self.scenes.append(scene)
            self.refresh_table()

    def edit_scene(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个场景")
            return
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        scene = self.scenes[row]
        dlg = QDialog(self)
        dlg.setWindowTitle("编辑场景")
        dlg.setMinimumWidth(400)
        form = QFormLayout(dlg)
        name_edit = QLineEdit(scene["name"])
        preset_combo = QComboBox()
        preset_combo.addItems(["默认", "暖色调", "冷色调", "追光", "染色", "特效", "自定义"])
        preset_combo.setCurrentText(scene.get("preset", "默认"))
        desc_edit = QLineEdit(scene.get("description", ""))
        form.addRow("场景名称:", name_edit)
        form.addRow("灯具预设:", preset_combo)
        form.addRow("描述:", desc_edit)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            scene["name"] = name_edit.text()
            scene["preset"] = preset_combo.currentText()
            scene["description"] = desc_edit.text()
            self.refresh_table()

    def delete_scene(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择一个场景")
            return
        name = self.scenes[row]["name"]
        if QMessageBox.question(self, "确认", f"确定删除场景 '{name}' 吗?") == QMessageBox.StandardButton.Yes:
            self.scenes.pop(row)
            self.refresh_table()

    def move_up(self):
        row = self.table.currentRow()
        if row > 0:
            self.scenes[row], self.scenes[row - 1] = self.scenes[row - 1], self.scenes[row]
            self.refresh_table()
            self.table.selectRow(row - 1)

    def move_down(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.scenes) - 1:
            self.scenes[row], self.scenes[row + 1] = self.scenes[row + 1], self.scenes[row]
            self.refresh_table()
            self.table.selectRow(row + 1)

    def refresh_table(self):
        self.table.setRowCount(len(self.scenes))
        for i, s in enumerate(self.scenes):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(s["name"]))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("preset", "")))
            self.table.setItem(i, 3, QTableWidgetItem(s.get("description", "")))

    def to_list(self):
        return self.scenes

    def from_list(self, scenes):
        self.scenes = scenes
        self.refresh_table()


class CueOverviewWidget(QWidget):
    """Cue总览 - 列出所有场景的Cue"""
    def __init__(self, scene_widget: SceneListWidget, parent=None):
        super().__init__(parent)
        self.scene_widget = scene_widget
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Cue编号", "所属场景", "动作", "时机", "备注"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("🔄 刷新")
        btn_refresh.clicked.connect(self.refresh)
        btn_layout.addWidget(btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def refresh(self):
        rows = []
        for scene in self.scene_widget.to_list():
            for cue in scene.get("cues", []):
                rows.append((cue.get("number", ""), scene["name"], cue.get("action", ""), cue.get("timing", ""), cue.get("notes", "")))
        self.table.setRowCount(len(rows))
        for i, (num, scn, act, tim, note) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(num)))
            self.table.setItem(i, 1, QTableWidgetItem(scn))
            self.table.setItem(i, 2, QTableWidgetItem(act))
            self.table.setItem(i, 3, QTableWidgetItem(tim))
            self.table.setItem(i, 4, QTableWidgetItem(note))


class TimelineOverviewWidget(QWidget):
    """时间线概览 - 可视化展示场景区块"""
    def __init__(self, scene_widget: SceneListWidget, parent=None):
        super().__init__(parent)
        self.scene_widget = scene_widget
        self.setMinimumHeight(150)
        self.total_duration = 300  # 默认5分钟

    def paintEvent(self, event):
        scenes = self.scene_widget.to_list()
        if not scenes:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        colors = [QColor(80, 130, 200), QColor(200, 130, 80), QColor(130, 200, 80),
                  QColor(200, 80, 130), QColor(130, 80, 200), QColor(80, 200, 130)]
        block_h = 50
        y = (h - block_h) // 2
        n = len(scenes)
        gap = 4
        block_w = max(60, (w - gap * (n + 1)) // max(n, 1))
        for i, scene in enumerate(scenes):
            x = gap + i * (block_w + gap)
            color = colors[i % len(colors)]
            painter.setBrush(color)
            painter.setPen(QColor(200, 200, 200))
            painter.drawRoundedRect(x, y, block_w, block_h, 6, 6)
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(QRect(x, y, block_w, block_h), Qt.AlignmentFlag.AlignCenter, scene["name"][:12])
            # 序号
            painter.drawText(x + 4, y - 6, f"#{i + 1}")
        painter.end()

    def refresh(self):
        self.update()


class ShowManager(BaseToolWindow):
    """演出管理器 - 主窗口"""
    def __init__(self):
        super().__init__('ShowManager', '演出管理器', '1.0.0', 1400, 900)
        self._build_ui()
        self.logger.info("演出管理器初始化完成")

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # 标签页
        tabs = QTabWidget()

        # Tab1: 演出信息 + 场景列表
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.show_info = ShowInfoWidget()
        info_group = QGroupBox("演出信息")
        ig_layout = QVBoxLayout(info_group)
        ig_layout.addWidget(self.show_info)
        splitter.addWidget(info_group)

        self.scene_list = SceneListWidget()
        scene_group = QGroupBox("场景列表")
        sg_layout = QVBoxLayout(scene_group)
        sg_layout.addWidget(self.scene_list)
        splitter.addWidget(scene_group)
        splitter.setSizes([350, 800])
        t1_layout.addWidget(splitter)

        # 时间线概览
        tl_group = QGroupBox("时间线概览")
        tl_layout = QVBoxLayout(tl_group)
        self.timeline_overview = TimelineOverviewWidget(self.scene_list)
        tl_scroll = QScrollArea()
        tl_scroll.setWidget(self.timeline_overview)
        tl_scroll.setWidgetResizable(True)
        tl_scroll.setMaximumHeight(120)
        tl_layout.addWidget(tl_scroll)
        t1_layout.addWidget(tl_group)
        tabs.addTab(tab1, "📋 演出管理")

        # Tab2: Cue总览
        self.cue_overview = CueOverviewWidget(self.scene_list)
        tabs.addTab(self.cue_overview, "🎬 Cue总览")

        main_layout.addWidget(tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_export_csv = QPushButton("📄 导出CSV节目单")
        btn_export_csv.clicked.connect(self.export_csv)
        btn_save = QPushButton("💾 保存项目JSON")
        btn_save.clicked.connect(self.save_project_json)
        btn_load = QPushButton("📂 加载项目JSON")
        btn_load.clicked.connect(self.load_project_json)
        btn_refresh = QPushButton("🔄 刷新总览")
        btn_refresh.clicked.connect(self._refresh_all)
        for b in [btn_export_csv, btn_save, btn_load, btn_refresh]:
            btn_layout.addWidget(b)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.set_central_content(central)

    def _refresh_all(self):
        self.cue_overview.refresh()
        self.timeline_overview.refresh()
        self.logger.info("总览已刷新")

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "", "CSV文件 (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["场景序号", "场景名称", "灯具预设", "Cue编号", "动作", "时机", "备注"])
                for si, scene in enumerate(self.scene_list.to_list()):
                    cues = scene.get("cues", [])
                    if not cues:
                        writer.writerow([si + 1, scene["name"], scene.get("preset", ""), "", "", "", ""])
                    else:
                        for cue in cues:
                            writer.writerow([si + 1, scene["name"], scene.get("preset", ""),
                                             cue.get("number", ""), cue.get("action", ""),
                                             cue.get("timing", ""), cue.get("notes", "")])
            self.logger.info(f"已导出CSV: {path}")
            QMessageBox.information(self, "成功", f"已导出到: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def save_project_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存项目", "", "JSON文件 (*.json)")
        if not path:
            return
        data = {
            "show_info": self.show_info.to_dict(),
            "scenes": self.scene_list.to_list()
        }
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"项目已保存: {path}")
            QMessageBox.information(self, "成功", f"项目已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def load_project_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载项目", "", "JSON文件 (*.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.show_info.from_dict(data.get("show_info", {}))
            self.scene_list.from_list(data.get("scenes", []))
            self._refresh_all()
            self.logger.info(f"项目已加载: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {e}")


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        win = ShowManager()
        win.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "ShowManager - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
