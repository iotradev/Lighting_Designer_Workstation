# -*- coding: utf-8 -*-
"""
灯具配接器 FixturePatcher
管理DMX宇宙地址分配与灯具配接
"""
import sys
import json
import csv
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QGroupBox, QFileDialog, QMessageBox, QScrollArea,
    QFrame, QHeaderView, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

try:
    import path_setup
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location('path_setup', str(Path(__file__).resolve().parent.parent.parent.parent / 'path_setup.py'))
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod); import sys; sys.modules['path_setup'] = _mod; path_setup = _mod
path_setup.ensure_common_path(__file__)
from ui.base_window import BaseToolWindow

# Fixture color palette for visual grid
FIXTURE_COLORS = [
    QColor(58, 134, 255),   # blue
    QColor(255, 89, 89),    # red
    QColor(89, 255, 134),   # green
    QColor(255, 200, 58),   # yellow
    QColor(200, 89, 255),   # purple
    QColor(89, 255, 255),   # cyan
    QColor(255, 150, 89),   # orange
    QColor(255, 89, 200),   # pink
    QColor(150, 255, 89),   # lime
    QColor(89, 150, 255),   # sky blue
    QColor(255, 255, 150),  # light yellow
    QColor(150, 89, 255),   # violet
    QColor(89, 255, 200),   # teal
    QColor(255, 150, 150),  # salmon
    QColor(150, 255, 255),  # light cyan
    QColor(200, 200, 89),   # olive
]

# Common fixture types with channel counts
FIXTURE_TYPES = {
    "常规灯 (1ch)": 1,
    "RGB灯 (3ch)": 3,
    "RGBW灯 (4ch)": 4,
    "RGBAW灯 (5ch)": 5,
    "摇头灯 (16ch)": 16,
    "摇头灯 (20ch)": 20,
    "LED条 (6ch)": 6,
    "频闪灯 (2ch)": 2,
    "烟雾机 (1ch)": 1,
    "自定义": 0,
}


class UniverseGridWidget(QWidget):
    """16x32 visual grid for a single DMX universe (512 channels)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.grid_layout)
        self.cells = []
        self._build_grid()

    def _build_grid(self):
        self.cells = []
        for row in range(16):
            row_cells = []
            for col in range(32):
                cell = QFrame()
                cell.setFixedSize(18, 18)
                cell.setFrameShape(QFrame.Shape.Box)
                cell.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
                label = QLabel(str(row * 32 + col + 1))
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("font-size: 7px; color: #888; background: transparent; border: none;")
                layout = QVBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(label)
                cell.setLayout(layout)
                self.grid_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.cells.append(row_cells)

    def update_channels(self, fixture_map):
        """Update grid colors. fixture_map: dict of channel -> (fixture_name, color)"""
        for row in range(16):
            for col in range(32):
                ch = row * 32 + col
                cell = self.cells[row][col]
                if ch in fixture_map:
                    name, color = fixture_map[ch]
                    cell.setStyleSheet(
                        f"background-color: {color.name()}; border: 1px solid #666;"
                    )
                else:
                    cell.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")


class FixturePatcher(BaseToolWindow):
    def __init__(self):
        super().__init__('FixturePatcher', '灯具配接器', '1.0.0', 1300, 850)
        self.patch_data = []  # list of dicts
        self.color_index = 0
        self._build_ui()
        self.logger.info("灯具配接器就绪")

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Top area: left (add form) | center (table) | right (grid)
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- LEFT: Add fixture form ---
        left_panel = QGroupBox("添加灯具")
        left_layout = QVBoxLayout()

        # Fixture name
        left_layout.addWidget(QLabel("灯具名称:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("输入灯具名称")
        left_layout.addWidget(self.name_input)

        # Universe
        left_layout.addWidget(QLabel("DMX宇宙 (0-15):"))
        self.universe_spin = QSpinBox()
        self.universe_spin.setRange(0, 15)
        left_layout.addWidget(self.universe_spin)

        # Start address
        left_layout.addWidget(QLabel("起始地址 (1-512):"))
        self.address_spin = QSpinBox()
        self.address_spin.setRange(1, 512)
        left_layout.addWidget(self.address_spin)

        # Channel mode dropdown
        left_layout.addWidget(QLabel("通道模式:"))
        self.mode_combo = QComboBox()
        for mode_name in FIXTURE_TYPES:
            self.mode_combo.addItem(mode_name)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        left_layout.addWidget(self.mode_combo)

        # Channel count (manual)
        left_layout.addWidget(QLabel("通道数:"))
        self.channel_spin = QSpinBox()
        self.channel_spin.setRange(1, 512)
        self.channel_spin.setValue(3)
        left_layout.addWidget(self.channel_spin)

        # Buttons
        self.add_btn = QPushButton("添加灯具")
        self.add_btn.clicked.connect(self._add_fixture)
        left_layout.addWidget(self.add_btn)

        self.auto_patch_btn = QPushButton("自动配接")
        self.auto_patch_btn.clicked.connect(self._auto_patch)
        left_layout.addWidget(self.auto_patch_btn)

        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        left_panel.setMaximumWidth(220)
        top_splitter.addWidget(left_panel)

        # --- CENTER: Patch table ---
        center_panel = QGroupBox("配接表")
        center_layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["名称", "宇宙", "起始地址", "结束地址", "通道数", "模式"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        center_layout.addWidget(self.table)

        # Table buttons
        btn_row = QHBoxLayout()
        self.edit_btn = QPushButton("编辑选中")
        self.edit_btn.clicked.connect(self._edit_selected)
        btn_row.addWidget(self.edit_btn)
        self.delete_btn = QPushButton("删除选中")
        self.delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(self.delete_btn)
        self.clear_btn = QPushButton("清空全部")
        self.clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(self.clear_btn)
        center_layout.addLayout(btn_row)

        center_panel.setLayout(center_layout)
        top_splitter.addWidget(center_panel)

        # --- RIGHT: Universe grid ---
        right_panel = QGroupBox("宇宙总览")
        right_layout = QVBoxLayout()

        # Universe selector
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("选择宇宙:"))
        self.grid_universe_spin = QSpinBox()
        self.grid_universe_spin.setRange(0, 15)
        self.grid_universe_spin.valueChanged.connect(self._refresh_grid)
        sel_row.addWidget(self.grid_universe_spin)
        right_layout.addLayout(sel_row)

        # Scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.universe_grid = UniverseGridWidget()
        scroll.setWidget(self.universe_grid)
        right_layout.addWidget(scroll)

        # Legend
        self.legend_label = QLabel("")
        self.legend_label.setWordWrap(True)
        right_layout.addWidget(self.legend_label)

        right_panel.setLayout(right_layout)
        top_splitter.addWidget(right_panel)

        top_splitter.setSizes([200, 500, 400])
        main_layout.addWidget(top_splitter, stretch=1)

        # --- BOTTOM bar ---
        bottom = QHBoxLayout()
        self.export_csv_btn = QPushButton("导出CSV")
        self.export_csv_btn.clicked.connect(self._export_csv)
        bottom.addWidget(self.export_csv_btn)

        self.save_json_btn = QPushButton("保存JSON")
        self.save_json_btn.clicked.connect(self._save_json)
        bottom.addWidget(self.save_json_btn)

        self.load_json_btn = QPushButton("加载JSON")
        self.load_json_btn.clicked.connect(self._load_json)
        bottom.addWidget(self.load_json_btn)

        bottom.addStretch()

        self.conflict_label = QLabel("")
        self.conflict_label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        bottom.addWidget(self.conflict_label)

        main_layout.addLayout(bottom)

        self.set_central_content(central)

    def _on_mode_changed(self, index):
        mode_text = self.mode_combo.currentText()
        ch_count = FIXTURE_TYPES.get(mode_text, 0)
        if ch_count > 0:
            self.channel_spin.setValue(ch_count)

    def _get_fixtures_for_universe(self, universe):
        return [f for f in self.patch_data if f['universe'] == universe]

    def _detect_conflicts(self):
        """Detect address overlaps within same universe"""
        conflicts = []
        by_universe = {}
        for f in self.patch_data:
            key = f['universe']
            by_universe.setdefault(key, []).append(f)
        for u, fixtures in by_universe.items():
            sorted_f = sorted(fixtures, key=lambda x: x['start'])
            for i in range(len(sorted_f)):
                for j in range(i + 1, len(sorted_f)):
                    a, b = sorted_f[i], sorted_f[j]
                    a_end = a['start'] + a['channels'] - 1
                    if b['start'] <= a_end:
                        conflicts.append(
                            f"宇宙{u}: \"{a['name']}\"({a['start']}-{a_end}) 与 \"{b['name']}\"({b['start']}-{b['start']+b['channels']-1}) 地址冲突"
                        )
        return conflicts

    def _add_fixture(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入灯具名称")
            return

        entry = {
            'name': name,
            'universe': self.universe_spin.value(),
            'start': self.address_spin.value(),
            'channels': self.channel_spin.value(),
            'mode': self.mode_combo.currentText(),
            'color': FIXTURE_COLORS[self.color_index % len(FIXTURE_COLORS)],
        }

        # Check address overflow
        if entry['start'] + entry['channels'] - 1 > 512:
            QMessageBox.warning(self, "警告", f"地址溢出: 起始{entry['start']}+{entry['channels']}通道超出512")
            return

        self.patch_data.append(entry)
        self.color_index += 1
        self._refresh_table()
        self._refresh_grid()
        self._update_conflicts()
        self.logger.info(f"添加灯具: {name} 宇宙{entry['universe']} 地址{entry['start']}-{entry['start']+entry['channels']-1}")

    def _auto_patch(self):
        """Auto-assign next available address in current universe"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "警告", "请输入灯具名称再执行自动配接")
            return

        universe = self.universe_spin.value()
        channels = self.channel_spin.value()
        mode = self.mode_combo.currentText()

        # Find occupied ranges
        occupied = []
        for f in self.patch_data:
            if f['universe'] == universe:
                occupied.append((f['start'], f['start'] + f['channels'] - 1))
        occupied.sort()

        # Find first gap that fits
        addr = 1
        placed = False
        for s, e in occupied:
            if addr + channels - 1 < s:
                placed = True
                break
            addr = max(addr, e + 1)

        if not placed and addr + channels - 1 <= 512:
            placed = True

        if not placed:
            QMessageBox.warning(self, "警告", f"宇宙{universe}无可用连续{channels}通道地址")
            return

        entry = {
            'name': name,
            'universe': universe,
            'start': addr,
            'channels': channels,
            'mode': mode,
            'color': FIXTURE_COLORS[self.color_index % len(FIXTURE_COLORS)],
        }
        self.patch_data.append(entry)
        self.color_index += 1
        self._refresh_table()
        self._refresh_grid()
        self._update_conflicts()
        self.logger.info(f"自动配接: {name} 宇宙{universe} 地址{addr}-{addr+channels-1}")

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.patch_data):
            return
        f = self.patch_data[row]
        self.name_input.setText(f['name'])
        self.universe_spin.setValue(f['universe'])
        self.address_spin.setValue(f['start'])
        self.channel_spin.setValue(f['channels'])
        # Remove entry; user will re-add
        self.patch_data.pop(row)
        self._refresh_table()
        self._refresh_grid()
        self._update_conflicts()

    def _delete_selected(self):
        rows = sorted(set(idx.row() for idx in self.table.selectedIndexes()), reverse=True)
        for row in rows:
            if 0 <= row < len(self.patch_data):
                removed = self.patch_data.pop(row)
                self.logger.info(f"删除灯具: {removed['name']}")
        self._refresh_table()
        self._refresh_grid()
        self._update_conflicts()

    def _clear_all(self):
        if self.patch_data:
            reply = QMessageBox.question(self, "确认", "确定清空所有配接数据？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.patch_data.clear()
                self.color_index = 0
                self._refresh_table()
                self._refresh_grid()
                self._update_conflicts()

    def _refresh_table(self):
        self.table.setRowCount(len(self.patch_data))
        for i, f in enumerate(self.patch_data):
            end_addr = f['start'] + f['channels'] - 1
            self.table.setItem(i, 0, QTableWidgetItem(f['name']))
            self.table.setItem(i, 1, QTableWidgetItem(str(f['universe'])))
            self.table.setItem(i, 2, QTableWidgetItem(str(f['start'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(end_addr)))
            self.table.setItem(i, 4, QTableWidgetItem(str(f['channels'])))
            self.table.setItem(i, 5, QTableWidgetItem(f.get('mode', '')))
            # Color the row
            for col in range(6):
                item = self.table.item(i, col)
                if item:
                    item.setBackground(f['color'])

    def _refresh_grid(self, *_):
        universe = self.grid_universe_spin.value()
        fixture_map = {}
        legend_parts = []

        for i, f in enumerate(self.patch_data):
            if f['universe'] == universe:
                color = f['color']
                for ch_offset in range(f['channels']):
                    ch = f['start'] - 1 + ch_offset  # 0-indexed
                    if 0 <= ch < 512:
                        fixture_map[ch] = (f['name'], color)
                legend_parts.append(f"{f['name']}: {f['start']}-{f['start']+f['channels']-1} ({f['channels']}ch)")

        self.universe_grid.update_channels(fixture_map)
        self.legend_label.setText("  |  ".join(legend_parts) if legend_parts else "该宇宙无配接数据")

    def _update_conflicts(self):
        conflicts = self._detect_conflicts()
        if conflicts:
            self.conflict_label.setText(f"⚠ {len(conflicts)} 个地址冲突!")
            self.conflict_label.setToolTip("\n".join(conflicts))
        else:
            self.conflict_label.setText("✓ 无地址冲突")
            self.conflict_label.setStyleSheet("color: #6bff6b; font-weight: bold;")

    def _export_csv(self):
        if not self.patch_data:
            QMessageBox.information(self, "提示", "无配接数据可导出")
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "patch_table.csv", "CSV文件 (*.csv)")
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["灯具名称", "DMX宇宙", "起始地址", "结束地址", "通道数", "模式"])
                    for entry in self.patch_data:
                        end_addr = entry['start'] + entry['channels'] - 1
                        writer.writerow([entry['name'], entry['universe'], entry['start'],
                                         end_addr, entry['channels'], entry.get('mode', '')])
                self.logger.info(f"已导出CSV: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def _save_json(self):
        if not self.patch_data:
            QMessageBox.information(self, "提示", "无配接数据可保存")
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存配接", "patch.json", "JSON文件 (*.json)")
        if path:
            try:
                data = []
                for f in self.patch_data:
                    entry = {k: v for k, v in f.items() if k != 'color'}
                    entry['color'] = f['color'].name()
                    data.append(entry)
                with open(path, 'w', encoding='utf-8') as fp:
                    json.dump({"fixtures": data}, fp, ensure_ascii=False, indent=2)
                self.logger.info(f"已保存配接: {path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def _load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载配接", "", "JSON文件 (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                fixtures = data.get("fixtures", [])
                self.patch_data.clear()
                for f in fixtures:
                    color = QColor(f.get('color', '#3a86ff'))
                    self.patch_data.append({
                        'name': f['name'],
                        'universe': f['universe'],
                        'start': f['start'],
                        'channels': f['channels'],
                        'mode': f.get('mode', ''),
                        'color': color,
                    })
                self.color_index = len(self.patch_data)
                self._refresh_table()
                self._refresh_grid()
                self._update_conflicts()
                self.logger.info(f"已加载配接: {path} ({len(self.patch_data)}个灯具)")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载失败: {e}")


if __name__ == '__main__':
    import traceback
    try:

        app = QApplication(sys.argv)
        window = FixturePatcher()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "FixturePatcher - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
