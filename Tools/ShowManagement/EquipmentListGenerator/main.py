#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""设备清单生成器 - 灯光项目设备清单管理与导出工具"""

import sys
import csv
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QFileDialog, QTabWidget, QSpinBox, QLineEdit, QComboBox,
    QGridLayout, QMessageBox, QTextEdit, QSplitter, QFormLayout,
    QDoubleSpinBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


# ─── 添加灯具对话框 ──────────────────────────────────────────────────────────

class AddFixtureDialog(QDialog):
    """添加灯具对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("添加灯具")
        self.setMinimumWidth(400)

        layout = QFormLayout(self)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("例如: Martin MAC Viper")
        layout.addRow("灯具名称:", self._name_edit)

        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 999)
        layout.addRow("数量:", self._qty_spin)

        self._mode_edit = QLineEdit()
        self._mode_edit.setPlaceholderText("例如: Standard 16ch")
        layout.addRow("模式:", self._mode_edit)

        self._universe_spin = QSpinBox()
        self._universe_spin.setRange(1, 128)
        layout.addRow("Universe:", self._universe_spin)

        self._address_spin = QSpinBox()
        self._address_spin.setRange(1, 512)
        layout.addRow("起始地址:", self._address_spin)

        self._power_spin = QDoubleSpinBox()
        self._power_spin.setRange(0, 10000)
        self._power_spin.setSuffix(" W")
        self._power_spin.setValue(200)
        layout.addRow("功率:", self._power_spin)

        self._weight_spin = QDoubleSpinBox()
        self._weight_spin.setRange(0, 500)
        self._weight_spin.setSuffix(" kg")
        self._weight_spin.setValue(10)
        layout.addRow("重量:", self._weight_spin)

        self._circuit_spin = QSpinBox()
        self._circuit_spin.setRange(1, 100)
        layout.addRow("回路:", self._circuit_spin)

        self._ip_edit = QLineEdit()
        self._ip_edit.setPlaceholderText("例如: 192.168.1.100")
        layout.addRow("IP地址:", self._ip_edit)

        self._node_combo = QComboBox()
        self._node_combo.addItems(["无", "ArtNet", "sACN"])
        layout.addRow("网络节点:", self._node_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self):
        return {
            'name': self._name_edit.text() or "未命名灯具",
            'qty': self._qty_spin.value(),
            'mode': self._mode_edit.text() or "默认",
            'universe': self._universe_spin.value(),
            'address': self._address_spin.value(),
            'power': self._power_spin.value(),
            'weight': self._weight_spin.value(),
            'circuit': self._circuit_spin.value(),
            'ip': self._ip_edit.text() or "--",
            'node': self._node_combo.currentText()
        }


# ─── 主窗口 ──────────────────────────────────────────────────────────────────

class EquipmentListGenerator(BaseToolWindow):
    """设备清单生成器"""

    def __init__(self):
        super().__init__('EquipmentListGenerator', '设备清单生成器', '1.0.0', 1200, 850)

        self._fixtures = []

        self._build_ui()
        self._load_sample_fixtures()
        self.logger.info("设备清单生成器已初始化")

    def _build_ui(self):
        central = QWidget()
        self.set_central_content(central)
        layout = QVBoxLayout(central)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ 添加灯具")
        add_btn.clicked.connect(self._on_add_fixture)
        toolbar.addWidget(add_btn)

        remove_btn = QPushButton("➖ 删除选中")
        remove_btn.clicked.connect(self._on_remove_fixture)
        toolbar.addWidget(remove_btn)

        clear_btn = QPushButton("🗑 清空列表")
        clear_btn.clicked.connect(self._on_clear_fixtures)
        toolbar.addWidget(clear_btn)

        toolbar.addStretch()

        export_csv_btn = QPushButton("导出 CSV")
        export_csv_btn.clicked.connect(self._on_export_csv)
        toolbar.addWidget(export_csv_btn)

        export_html_btn = QPushButton("导出 HTML")
        export_html_btn.clicked.connect(self._on_export_html)
        toolbar.addWidget(export_html_btn)

        layout.addLayout(toolbar)

        # 标签页
        self._tabs = QTabWidget()

        # 灯具清单标签页
        self._fixture_table = QTableWidget(0, 10)
        self._fixture_table.setHorizontalHeaderLabels([
            "灯具名称", "数量", "模式", "Universe", "起始地址",
            "功率(W)", "重量(kg)", "回路", "IP地址", "网络节点"
        ])
        self._fixture_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabs.addTab(self._fixture_table, "灯具清单")

        # 电力分配标签页
        self._power_table = QTableWidget(0, 4)
        self._power_table.setHorizontalHeaderLabels(["回路", "灯具", "数量", "功率(W)"])
        self._power_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabs.addTab(self._power_table, "电力分配")

        # 网络清单标签页
        self._network_table = QTableWidget(0, 5)
        self._network_table.setHorizontalHeaderLabels(["灯具", "数量", "IP地址", "Universe", "节点类型"])
        self._network_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tabs.addTab(self._network_table, "网络清单")

        # 汇总统计标签页
        self._summary_text = QTextEdit()
        self._summary_text.setReadOnly(True)
        self._summary_text.setFont(QFont("Consolas", 11))
        self._tabs.addTab(self._summary_text, "汇总统计")

        layout.addWidget(self._tabs, 1)

        # 底部刷新按钮
        bottom = QHBoxLayout()
        refresh_btn = QPushButton("🔄 刷新所有清单")
        refresh_btn.setStyleSheet("font-size: 14px; padding: 8px;")
        refresh_btn.clicked.connect(self._refresh_all)
        bottom.addWidget(refresh_btn)
        layout.addLayout(bottom)

    def _load_sample_fixtures(self):
        """加载示例灯具数据"""
        samples = [
            {"name": "Martin MAC Viper Profile", "qty": 12, "mode": "Standard 20ch", "universe": 1, "address": 1, "power": 850, "weight": 33.5, "circuit": 1, "ip": "--", "node": "无"},
            {"name": "Robe BMFL Spot", "qty": 8, "mode": "Extended 32ch", "universe": 1, "address": 241, "power": 1700, "weight": 42, "circuit": 2, "ip": "--", "node": "无"},
            {"name": "GLP Impression X4 Bar", "qty": 16, "mode": "RGB 8ch", "universe": 2, "address": 1, "power": 200, "weight": 8.5, "circuit": 3, "ip": "--", "node": "无"},
            {"name": "Robe Spiider", "qty": 6, "mode": "Extended 25ch", "universe": 2, "address": 129, "power": 600, "weight": 22, "circuit": 4, "ip": "--", "node": "无"},
            {"name": "Clay Paky Sharpy Plus", "qty": 20, "mode": "Standard 16ch", "universe": 3, "address": 1, "power": 350, "weight": 24, "circuit": 5, "ip": "--", "node": "无"},
            {"name": "ETC Source Four LED", "qty": 24, "mode": "Direct 6ch", "universe": 4, "address": 1, "power": 160, "weight": 11.3, "circuit": 6, "ip": "--", "node": "无"},
            {"name": "MA Lighting grandMA3", "qty": 2, "mode": "N/A", "universe": 0, "address": 0, "power": 200, "weight": 15, "circuit": 7, "ip": "192.168.1.10", "node": "ArtNet"},
            {"name": "ArtNet Node 4-Port", "qty": 4, "mode": "N/A", "universe": 0, "address": 0, "power": 15, "weight": 2, "circuit": 8, "ip": "192.168.1.100", "node": "ArtNet"},
        ]
        self._fixtures = samples
        self._refresh_all()

    def _on_add_fixture(self):
        dialog = AddFixtureDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            self._fixtures.append(data)
            self._refresh_all()
            self.logger.info(f"添加灯具: {data['name']} x{data['qty']}")

    def _on_remove_fixture(self):
        rows = set(idx.row() for idx in self._fixture_table.selectedIndexes())
        if not rows:
            return
        for row in sorted(rows, reverse=True):
            if row < len(self._fixtures):
                removed = self._fixtures.pop(row)
                self.logger.info(f"删除灯具: {removed['name']}")
        self._refresh_all()

    def _on_clear_fixtures(self):
        if QMessageBox.question(self, "确认", "确定要清空所有灯具列表吗？") == QMessageBox.Yes:
            self._fixtures.clear()
            self._refresh_all()

    def _refresh_all(self):
        self._refresh_fixture_table()
        self._refresh_power_table()
        self._refresh_network_table()
        self._refresh_summary()

    def _refresh_fixture_table(self):
        self._fixture_table.setRowCount(len(self._fixtures))
        for row, f in enumerate(self._fixtures):
            self._fixture_table.setItem(row, 0, QTableWidgetItem(str(f['name'])))
            self._fixture_table.setItem(row, 1, QTableWidgetItem(str(f['qty'])))
            self._fixture_table.setItem(row, 2, QTableWidgetItem(str(f['mode'])))
            self._fixture_table.setItem(row, 3, QTableWidgetItem(str(f['universe'])))
            self._fixture_table.setItem(row, 4, QTableWidgetItem(str(f['address'])))
            self._fixture_table.setItem(row, 5, QTableWidgetItem(f"{f['power']:.0f}"))
            self._fixture_table.setItem(row, 6, QTableWidgetItem(f"{f['weight']:.1f}"))
            self._fixture_table.setItem(row, 7, QTableWidgetItem(str(f['circuit'])))
            self._fixture_table.setItem(row, 8, QTableWidgetItem(str(f['ip'])))
            self._fixture_table.setItem(row, 9, QTableWidgetItem(str(f['node'])))

    def _refresh_power_table(self):
        # 按回路分组
        circuits = {}
        for f in self._fixtures:
            c = f['circuit']
            if c not in circuits:
                circuits[c] = []
            circuits[c].append(f)

        rows = []
        for c in sorted(circuits.keys()):
            for f in circuits[c]:
                rows.append((c, f['name'], f['qty'], f['power'] * f['qty']))

        self._power_table.setRowCount(len(rows))
        for row, (circuit, name, qty, power) in enumerate(rows):
            self._power_table.setItem(row, 0, QTableWidgetItem(f"回路 {circuit}"))
            self._power_table.setItem(row, 1, QTableWidgetItem(name))
            self._power_table.setItem(row, 2, QTableWidgetItem(str(qty)))
            self._power_table.setItem(row, 3, QTableWidgetItem(f"{power:.0f}"))

    def _refresh_network_table(self):
        network_fixtures = [f for f in self._fixtures if f['node'] != '无']
        self._network_table.setRowCount(len(network_fixtures))
        for row, f in enumerate(network_fixtures):
            self._network_table.setItem(row, 0, QTableWidgetItem(f['name']))
            self._network_table.setItem(row, 1, QTableWidgetItem(str(f['qty'])))
            self._network_table.setItem(row, 2, QTableWidgetItem(f['ip']))
            self._network_table.setItem(row, 3, QTableWidgetItem(str(f['universe'])))
            self._network_table.setItem(row, 4, QTableWidgetItem(f['node']))

    def _refresh_summary(self):
        total_fixtures = sum(f['qty'] for f in self._fixtures)
        total_power = sum(f['power'] * f['qty'] for f in self._fixtures)
        total_weight = sum(f['weight'] * f['qty'] for f in self._fixtures)
        total_dmx_fixtures = sum(f['qty'] for f in self._fixtures if f['universe'] > 0)
        network_fixtures = [f for f in self._fixtures if f['node'] != '无']
        circuits = set(f['circuit'] for f in self._fixtures)

        # 按类型统计
        type_counts = {}
        for f in self._fixtures:
            name = f['name']
            type_counts[name] = type_counts.get(name, 0) + f['qty']

        lines = [
            "=" * 60,
            "  设备清单汇总统计",
            "=" * 60,
            "",
            f"  灯具种类数:       {len(type_counts)}",
            f"  灯具总数:         {total_fixtures}",
            f"  DMX灯具数:        {total_dmx_fixtures}",
            f"  网络设备数:       {sum(f['qty'] for f in network_fixtures)}",
            f"  总功率:           {total_power:,.0f} W ({total_power/1000:.1f} kW)",
            f"  总重量:           {total_weight:,.1f} kg ({total_weight/1000:.2f} t)",
            f"  回路数:           {len(circuits)}",
            "",
            "─── 按类型统计 ───",
        ]
        for name, count in sorted(type_counts.items()):
            lines.append(f"  {name}: {count}")

        lines.extend([
            "",
            "─── 电力分配 ───",
        ])
        circuit_power = {}
        for f in self._fixtures:
            c = f['circuit']
            circuit_power[c] = circuit_power.get(c, 0) + f['power'] * f['qty']
        for c in sorted(circuit_power.keys()):
            lines.append(f"  回路 {c}: {circuit_power[c]:,.0f} W")

        if network_fixtures:
            lines.extend([
                "",
                "─── 网络设备 ───",
            ])
            for f in network_fixtures:
                lines.append(f"  {f['name']}: {f['ip']} ({f['node']})")

        lines.extend([
            "",
            "=" * 60,
            f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ])

        self._summary_text.setText("\n".join(lines))

    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出设备清单", "equipment_list.csv", "CSV文件 (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["灯具名称", "数量", "模式", "Universe", "起始地址",
                               "功率(W)", "重量(kg)", "回路", "IP地址", "网络节点"])
                for fix in self._fixtures:
                    writer.writerow([
                        fix['name'], fix['qty'], fix['mode'], fix['universe'],
                        fix['address'], fix['power'], fix['weight'], fix['circuit'],
                        fix['ip'], fix['node']
                    ])

                writer.writerow([])
                writer.writerow(["汇总"])
                writer.writerow(["灯具总数", sum(f['qty'] for f in self._fixtures)])
                writer.writerow(["总功率(W)", f"{sum(f['power'] * f['qty'] for f in self._fixtures):.0f}"])
                writer.writerow(["总重量(kg)", f"{sum(f['weight'] * f['qty'] for f in self._fixtures):.1f}"])

            self.logger.info(f"已导出CSV: {path}")
            QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _on_export_html(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出设备清单", "equipment_list.html", "HTML文件 (*.html)"
        )
        if not path:
            return

        total_fixtures = sum(f['qty'] for f in self._fixtures)
        total_power = sum(f['power'] * f['qty'] for f in self._fixtures)
        total_weight = sum(f['weight'] * f['qty'] for f in self._fixtures)

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>设备清单</title>
<style>
body {{ font-family: "Microsoft YaHei", sans-serif; margin: 20px; }}
h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
h2 {{ color: #555; }}
table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
th {{ background-color: #007acc; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
.summary {{ background: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
.summary p {{ margin: 5px 0; font-size: 14px; }}
.footer {{ color: #999; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<h1>🎬 设备清单</h1>
<div class="summary">
<p><strong>灯具总数:</strong> {total_fixtures}</p>
<p><strong>总功率:</strong> {total_power:,.0f} W ({total_power/1000:.1f} kW)</p>
<p><strong>总重量:</strong> {total_weight:,.1f} kg</p>
</div>

<h2>灯具清单</h2>
<table>
<tr><th>名称</th><th>数量</th><th>模式</th><th>Universe</th><th>地址</th><th>功率(W)</th><th>重量(kg)</th><th>回路</th><th>IP</th><th>节点</th></tr>
"""
        for f in self._fixtures:
            html += f"<tr><td>{f['name']}</td><td>{f['qty']}</td><td>{f['mode']}</td>"
            html += f"<td>{f['universe']}</td><td>{f['address']}</td><td>{f['power']:.0f}</td>"
            html += f"<td>{f['weight']:.1f}</td><td>{f['circuit']}</td><td>{f['ip']}</td><td>{f['node']}</td></tr>\n"

        html += "</table>\n"

        # 电力分配表
        html += "<h2>电力分配</h2>\n<table><tr><th>回路</th><th>灯具</th><th>数量</th><th>功率(W)</th></tr>\n"
        circuit_data = {}
        for f in self._fixtures:
            c = f['circuit']
            if c not in circuit_data:
                circuit_data[c] = []
            circuit_data[c].append(f)
        for c in sorted(circuit_data.keys()):
            for f in circuit_data[c]:
                html += f"<tr><td>回路 {c}</td><td>{f['name']}</td><td>{f['qty']}</td><td>{f['power']*f['qty']:.0f}</td></tr>\n"
        html += "</table>\n"

        # 网络设备表
        network = [f for f in self._fixtures if f['node'] != '无']
        if network:
            html += "<h2>网络设备</h2>\n<table><tr><th>名称</th><th>数量</th><th>IP地址</th><th>Universe</th><th>节点类型</th></tr>\n"
            for f in network:
                html += f"<tr><td>{f['name']}</td><td>{f['qty']}</td><td>{f['ip']}</td><td>{f['universe']}</td><td>{f['node']}</td></tr>\n"
            html += "</table>\n"

        html += f'<p class="footer">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>\n'
        html += "</body></html>"

        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            self.logger.info(f"已导出HTML: {path}")
            QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))


# ─── 入口 ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = EquipmentListGenerator()
    window.show()
    sys.exit(app.exec())
