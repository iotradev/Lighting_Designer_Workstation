# -*- coding: utf-8 -*-
"""
节目单生成器 - Cue Sheet Generator
模板化节目单生成，支持CSV/HTML/纯文本导出
"""
import sys, json, csv, os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QHeaderView, QMessageBox, QFileDialog, QSplitter,
    QScrollArea, QFrame, QTabWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class CueSheetGenerator(BaseToolWindow):
    """节目单生成器 - 主窗口"""
    def __init__(self):
        super().__init__('CueSheetGenerator', '节目单生成器', '1.0.0', 1200, 850)
        self.cues = []
        self._build_ui()
        self.logger.info("节目单生成器初始化完成")

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        tabs = QTabWidget()

        # Tab1: 编辑
        edit_tab = QWidget()
        edit_layout = QVBoxLayout(edit_tab)

        # 演出信息
        info_group = QGroupBox("演出信息")
        info_layout = QFormLayout(info_group)
        self.show_name = QLineEdit()
        self.show_date = QLineEdit()
        self.show_venue = QLineEdit()
        self.ld_name = QLineEdit()
        self.show_page = QLineEdit("1")
        info_layout.addRow("演出名称:", self.show_name)
        info_layout.addRow("演出日期:", self.show_date)
        info_layout.addRow("演出场地:", self.show_venue)
        info_layout.addRow("灯光设计:", self.ld_name)
        info_layout.addRow("起始页码:", self.show_page)
        edit_layout.addWidget(info_group)

        # Cue表格
        cue_group = QGroupBox("Cue列表")
        cue_layout = QVBoxLayout(cue_group)

        # 表格操作
        btn_row = QHBoxLayout()
        btn_add = QPushButton("➕ 添加Cue")
        btn_del = QPushButton("🗑️ 删除Cue")
        btn_up = QPushButton("⬆️ 上移")
        btn_down = QPushButton("⬇️ 下移")
        btn_load = QPushButton("📂 从项目加载")
        btn_add.clicked.connect(self.add_cue)
        btn_del.clicked.connect(self.delete_cue)
        btn_up.clicked.connect(self.move_up)
        btn_down.clicked.connect(self.move_down)
        btn_load.clicked.connect(self.load_from_project)
        for b in [btn_add, btn_del, btn_up, btn_down, btn_load]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        cue_layout.addLayout(btn_row)

        self.cue_table = QTableWidget(0, 6)
        self.cue_table.setHorizontalHeaderLabels(["Cue编号", "页码", "动作/场景", "灯光状态描述", "时机/渐变", "备注"])
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cue_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        cue_layout.addWidget(self.cue_table)
        edit_layout.addWidget(cue_group)

        tabs.addTab(edit_tab, "📝 编辑节目单")

        # Tab2: 预览
        preview_tab = QWidget()
        preview_layout = QVBoxLayout(preview_tab)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        btn_refresh_preview = QPushButton("🔄 刷新预览")
        btn_refresh_preview.clicked.connect(self.refresh_preview)
        preview_layout.addWidget(btn_refresh_preview)
        tabs.addTab(preview_tab, "👁️ 预览")

        main_layout.addWidget(tabs)

        # 底部导出按钮
        export_row = QHBoxLayout()
        btn_csv = QPushButton("📄 导出CSV")
        btn_html = QPushButton("🌐 导出HTML(可打印)")
        btn_txt = QPushButton("📃 导出纯文本")
        btn_csv.clicked.connect(self.export_csv)
        btn_html.clicked.connect(self.export_html)
        btn_txt.clicked.connect(self.export_txt)
        for b in [btn_csv, btn_html, btn_txt]:
            export_row.addWidget(b)
        export_row.addStretch()
        main_layout.addLayout(export_row)

        self.set_central_content(central)

    def add_cue(self):
        row = self.cue_table.rowCount()
        self.cue_table.insertRow(row)
        self.cue_table.setItem(row, 0, QTableWidgetItem(f"Cue {row + 1}"))
        self.cue_table.setItem(row, 1, QTableWidgetItem(self.show_page.text()))
        self.cue_table.setItem(row, 2, QTableWidgetItem(""))
        self.cue_table.setItem(row, 3, QTableWidgetItem(""))
        self.cue_table.setItem(row, 4, QTableWidgetItem("3"))
        self.cue_table.setItem(row, 5, QTableWidgetItem(""))

    def delete_cue(self):
        row = self.cue_table.currentRow()
        if row >= 0:
            self.cue_table.removeRow(row)

    def move_up(self):
        row = self.cue_table.currentRow()
        if row > 0:
            self._swap_rows(row, row - 1)
            self.cue_table.selectRow(row - 1)

    def move_down(self):
        row = self.cue_table.currentRow()
        if 0 <= row < self.cue_table.rowCount() - 1:
            self._swap_rows(row, row + 1)
            self.cue_table.selectRow(row + 1)

    def _swap_rows(self, r1, r2):
        for col in range(self.cue_table.columnCount()):
            item1 = self.cue_table.takeItem(r1, col)
            item2 = self.cue_table.takeItem(r2, col)
            self.cue_table.setItem(r1, col, item2)
            self.cue_table.setItem(r2, col, item1)

    def load_from_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载项目", "", "JSON文件 (*.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 兼容ShowManager格式
            if "show_info" in data:
                info = data["show_info"]
                self.show_name.setText(info.get("name", ""))
                self.show_date.setText(info.get("date", ""))
                self.show_venue.setText(info.get("venue", ""))
                self.ld_name.setText(info.get("ld", ""))
            # 加载Cue
            self.cue_table.setRowCount(0)
            for scene in data.get("scenes", []):
                for cue in scene.get("cues", []):
                    row = self.cue_table.rowCount()
                    self.cue_table.insertRow(row)
                    self.cue_table.setItem(row, 0, QTableWidgetItem(str(cue.get("number", ""))))
                    self.cue_table.setItem(row, 1, QTableWidgetItem(self.show_page.text()))
                    self.cue_table.setItem(row, 2, QTableWidgetItem(cue.get("action", scene.get("name", ""))))
                    self.cue_table.setItem(row, 3, QTableWidgetItem(scene.get("description", "")))
                    self.cue_table.setItem(row, 4, QTableWidgetItem(cue.get("timing", "3")))
                    self.cue_table.setItem(row, 5, QTableWidgetItem(cue.get("notes", "")))
            self.logger.info(f"已从项目加载: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {e}")

    def _gather_info(self):
        return {
            "name": self.show_name.text(),
            "date": self.show_date.text(),
            "venue": self.show_venue.text(),
            "ld": self.ld_name.text()
        }

    def _gather_cues(self):
        cues = []
        for row in range(self.cue_table.rowCount()):
            cue = {}
            for col, key in enumerate(["number", "page", "action", "description", "timing", "notes"]):
                item = self.cue_table.item(row, col)
                cue[key] = item.text() if item else ""
            cues.append(cue)
        return cues

    def _format_text(self):
        info = self._gather_info()
        cues = self._gather_cues()
        lines = []
        lines.append(f"{'=' * 60}")
        lines.append(f"  节目单 / CUE SHEET")
        lines.append(f"{'=' * 60}")
        lines.append(f"  演出: {info['name']}")
        lines.append(f"  日期: {info['date']}")
        lines.append(f"  场地: {info['venue']}")
        lines.append(f"  灯光设计: {info['ld']}")
        lines.append(f"{'=' * 60}")
        lines.append("")
        lines.append(f"{'Cue':<10} {'页码':<6} {'动作':<20} {'灯光状态':<25} {'时机':<8} {'备注'}")
        lines.append(f"{'-' * 90}")
        for c in cues:
            lines.append(f"{c['number']:<10} {c['page']:<6} {c['action']:<20} {c['description']:<25} {c['timing']:<8} {c['notes']}")
        lines.append(f"{'-' * 90}")
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return "\n".join(lines)

    def _format_html(self):
        info = self._gather_info()
        cues = self._gather_cues()
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>节目单 - {info['name']}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h1 {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
.info {{ margin: 10px 0; }}
.info span {{ margin-right: 30px; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th, td {{ border: 1px solid #555; padding: 8px 12px; text-align: left; }}
th {{ background-color: #333; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
.footer {{ margin-top: 20px; font-size: 12px; color: #888; }}
@media print {{ body {{ margin: 0; }} }}
</style></head>
<body>
<h1>节目单 / CUE SHEET</h1>
<div class="info">
<span><b>演出:</b> {info['name']}</span>
<span><b>日期:</b> {info['date']}</span>
<span><b>场地:</b> {info['venue']}</span>
<span><b>灯光设计:</b> {info['ld']}</span>
</div>
<table>
<tr><th>Cue</th><th>页码</th><th>动作</th><th>灯光状态描述</th><th>时机/渐变</th><th>备注</th></tr>
"""
        for c in cues:
            html += f"<tr><td>{c['number']}</td><td>{c['page']}</td><td>{c['action']}</td><td>{c['description']}</td><td>{c['timing']}</td><td>{c['notes']}</td></tr>\n"
        html += f"""</table>
<div class="footer">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</body></html>"""
        return html

    def refresh_preview(self):
        self.preview_text.setPlainText(self._format_text())

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "", "CSV文件 (*.csv)")
        if not path:
            return
        try:
            info = self._gather_info()
            cues = self._gather_cues()
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["演出名称", info["name"]])
                writer.writerow(["日期", info["date"]])
                writer.writerow(["场地", info["venue"]])
                writer.writerow(["灯光设计", info["ld"]])
                writer.writerow([])
                writer.writerow(["Cue编号", "页码", "动作", "灯光状态描述", "时机/渐变", "备注"])
                for c in cues:
                    writer.writerow([c["number"], c["page"], c["action"], c["description"], c["timing"], c["notes"]])
            self.logger.info(f"已导出CSV: {path}")
            QMessageBox.information(self, "成功", f"已导出: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出HTML", "", "HTML文件 (*.html)")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._format_html())
            self.logger.info(f"已导出HTML: {path}")
            QMessageBox.information(self, "成功", f"已导出: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出纯文本", "", "文本文件 (*.txt)")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self._format_text())
            self.logger.info(f"已导出纯文本: {path}")
            QMessageBox.information(self, "成功", f"已导出: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(CueSheetGenerator, "CueSheetGenerator - 启动错误")