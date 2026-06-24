# -*- coding: utf-8 -*-
"""
DMX计算器 - DMX地址计算、Universe规划与冲突检测工具
"""

import sys
from pathlib import Path

# 添加公共库路径
try:
    import path_setup
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location('path_setup', str(Path(__file__).resolve().parent.parent.parent.parent / 'path_setup.py'))
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod); import sys; sys.modules['path_setup'] = _mod; path_setup = _mod
path_setup.ensure_common_path(__file__)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QGridLayout, QFrame,
    QMessageBox, QGroupBox, QSplitter, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from ui.base_window import BaseToolWindow


class AddressCalcTab(QWidget):
    """地址计算标签页"""

    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 输入区域
        input_group = QGroupBox("输入参数")
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel("起始地址 (1-512):"), 0, 0)
        self.start_addr = QSpinBox()
        self.start_addr.setRange(1, 512)
        self.start_addr.setValue(1)
        input_layout.addWidget(self.start_addr, 0, 1)

        input_layout.addWidget(QLabel("通道数量:"), 1, 0)
        self.ch_count = QSpinBox()
        self.ch_count.setRange(1, 512)
        self.ch_count.setValue(16)
        input_layout.addWidget(self.ch_count, 1, 1)

        self.calc_btn = QPushButton("计算")
        self.calc_btn.clicked.connect(self._calculate)
        input_layout.addWidget(self.calc_btn, 2, 0, 1, 2)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 结果区域
        result_group = QGroupBox("计算结果")
        result_layout = QGridLayout()

        result_layout.addWidget(QLabel("结束地址:"), 0, 0)
        self.end_addr_label = QLabel("--")
        self.end_addr_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        result_layout.addWidget(self.end_addr_label, 0, 1)

        result_layout.addWidget(QLabel("起始 Universe:"), 1, 0)
        self.start_uni_label = QLabel("--")
        self.start_uni_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        result_layout.addWidget(self.start_uni_label, 1, 1)

        result_layout.addWidget(QLabel("结束 Universe:"), 2, 0)
        self.end_uni_label = QLabel("--")
        self.end_uni_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        result_layout.addWidget(self.end_uni_label, 2, 1)

        result_layout.addWidget(QLabel("使用 Universe 数:"), 3, 0)
        self.uni_count_label = QLabel("--")
        self.uni_count_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        result_layout.addWidget(self.uni_count_label, 3, 1)

        result_group.setLayout(result_layout)
        layout.addWidget(result_group)

        # 警告区域
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("font-size: 14px; color: #FF8A65; padding: 10px;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)

        layout.addStretch()

    def _calculate(self):
        start = self.start_addr.value()
        count = self.ch_count.value()
        end = start + count - 1

        start_uni = (start - 1) // 512
        end_uni = (end - 1) // 512

        self.end_addr_label.setText(str(end))
        self.start_uni_label.setText(f"Universe {start_uni}")
        self.end_uni_label.setText(f"Universe {end_uni}")
        self.uni_count_label.setText(str(end_uni - start_uni + 1))

        # 冲突警告
        warnings = []
        if end > 32768:
            warnings.append("⚠ 结束地址超出 DMX 最大地址范围 (64 Universes × 512)")
        if start_uni != end_uni:
            warnings.append(f"⚠ 该灯具跨越了 {end_uni - start_uni + 1} 个 Universe")
        if start + count - 1 > 512 and start <= 512:
            warnings.append("⚠ 该灯具在起始 Universe 内超出 512 通道，将溢出到下一 Universe")

        if warnings:
            self.warning_label.setText("\n".join(warnings))
            self.warning_label.setStyleSheet("font-size: 14px; color: #FF8A65; padding: 10px;")
        else:
            self.warning_label.setText("✓ 地址范围正常，无冲突")
            self.warning_label.setStyleSheet("font-size: 14px; color: #81C784; padding: 10px;")

        self.logger.info(f"地址计算: 起始={start}, 通道数={count}, 结束={end}")


class UniversePlanTab(QWidget):
    """Universe规划标签页"""

    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.fixtures = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 灯具表格
        table_group = QGroupBox("灯具列表")
        table_layout = QVBoxLayout()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["灯具名称", "起始通道", "通道数量", "结束通道"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.table)

        # 添加/删除按钮
        btn_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("灯具名称")
        self.start_input = QSpinBox()
        self.start_input.setRange(1, 32768)
        self.start_input.setPrefix("CH ")
        self.ch_count_input = QSpinBox()
        self.ch_count_input.setRange(1, 512)
        self.ch_count_input.setValue(16)

        add_btn = QPushButton("➕ 添加灯具")
        add_btn.clicked.connect(self._add_fixture)
        remove_btn = QPushButton("➖ 移除选中")
        remove_btn.clicked.connect(self._remove_fixture)

        btn_layout.addWidget(QLabel("名称:"))
        btn_layout.addWidget(self.name_input)
        btn_layout.addWidget(QLabel("起始通道:"))
        btn_layout.addWidget(self.start_input)
        btn_layout.addWidget(QLabel("通道数:"))
        btn_layout.addWidget(self.ch_count_input)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)

        table_layout.addLayout(btn_layout)
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)

        # 可视化网格
        grid_group = QGroupBox("Universe 通道可视化 (16×32 = 512通道)")
        grid_layout = QVBoxLayout()

        # Universe选择
        uni_layout = QHBoxLayout()
        uni_layout.addWidget(QLabel("显示 Universe:"))
        self.uni_selector = QComboBox()
        for i in range(64):
            self.uni_selector.addItem(f"Universe {i}")
        self.uni_selector.currentIndexChanged.connect(self._update_grid)
        uni_layout.addWidget(self.uni_selector)
        uni_layout.addStretch()

        refresh_btn = QPushButton("🔄 刷新视图")
        refresh_btn.clicked.connect(self._update_grid)
        uni_layout.addWidget(refresh_btn)

        grid_layout.addLayout(uni_layout)

        # 图例
        legend_layout = QHBoxLayout()
        for color, text in [("#4CAF50", "空闲"), ("#FF9800", "已占用"), ("#F44336", "冲突")]:
            lbl = QLabel(f"  {text}  ")
            lbl.setStyleSheet(f"background-color: {color}; color: white; padding: 4px; border-radius: 3px;")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()
        grid_layout.addLayout(legend_layout)

        # 16x32 网格
        self.grid_frame = QFrame()
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(2)
        self.grid_cells = []

        for row in range(16):
            row_cells = []
            for col in range(32):
                cell = QLabel(str(row * 32 + col + 1))
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setFixedSize(36, 24)
                cell.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 2px; font-size: 10px;")
                self.grid_layout.addWidget(cell, row, col)
                row_cells.append(cell)
            self.grid_cells.append(row_cells)

        grid_layout.addWidget(self.grid_frame)
        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)

    def _add_fixture(self):
        name = self.name_input.text().strip()
        if not name:
            name = f"灯具_{len(self.fixtures) + 1}"
        start = self.start_input.value()
        count = self.ch_count_input.value()
        end = start + count - 1

        self.fixtures.append({"name": name, "start": start, "count": count, "end": end})

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(str(start)))
        self.table.setItem(row, 2, QTableWidgetItem(str(count)))
        self.table.setItem(row, 3, QTableWidgetItem(str(end)))

        self._update_grid()
        self.name_input.clear()
        self.logger.info(f"添加灯具: {name}, 起始通道={start}, 通道数={count}")

    def _remove_fixture(self):
        row = self.table.currentRow()
        if row >= 0:
            name = self.table.item(row, 0).text()
            self.table.removeRow(row)
            self.fixtures.pop(row)
            self._update_grid()
            self.logger.info(f"移除灯具: {name}")

    def _update_grid(self):
        uni = self.uni_selector.currentIndex()
        uni_start = uni * 512 + 1
        uni_end = (uni + 1) * 512

        # 统计每个通道的使用情况
        channel_usage = {}  # channel_offset -> fixture_name
        conflicts = set()

        for f in self.fixtures:
            for ch in range(f["start"], f["end"] + 1):
                if uni_start <= ch <= uni_end:
                    offset = ch - uni_start  # 0-511
                    if offset in channel_usage:
                        conflicts.add(offset)
                    else:
                        channel_usage[offset] = f["name"]

        for row in range(16):
            for col in range(32):
                offset = row * 32 + col
                cell = self.grid_cells[row][col]
                if offset in conflicts:
                    cell.setStyleSheet("background-color: #F44336; color: white; border-radius: 2px; font-size: 10px;")
                    cell.setToolTip(f"通道 {offset + 1}: 冲突!")
                elif offset in channel_usage:
                    cell.setStyleSheet("background-color: #FF9800; color: white; border-radius: 2px; font-size: 10px;")
                    cell.setToolTip(f"通道 {offset + 1}: {channel_usage[offset]}")
                else:
                    cell.setStyleSheet("background-color: #4CAF50; color: white; border-radius: 2px; font-size: 10px;")
                    cell.setToolTip(f"通道 {offset + 1}: 空闲")


class QuickConvertTab(QWidget):
    """快速转换标签页"""

    def __init__(self, logger, parent=None):
        super().__init__(parent)
        self.logger = logger
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 全局地址 -> Universe/Channel
        group1 = QGroupBox("全局地址 → Universe + 通道")
        g1_layout = QGridLayout()

        g1_layout.addWidget(QLabel("全局地址 (1-32768):"), 0, 0)
        self.global_addr = QSpinBox()
        self.global_addr.setRange(1, 32768)
        self.global_addr.setValue(1)
        g1_layout.addWidget(self.global_addr, 0, 1)

        g1_btn = QPushButton("转换 →")
        g1_btn.clicked.connect(self._global_to_uc)
        g1_layout.addWidget(g1_btn, 0, 2)

        g1_layout.addWidget(QLabel("Universe:"), 1, 0)
        self.out_uni = QLabel("--")
        self.out_uni.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        g1_layout.addWidget(self.out_uni, 1, 1)

        g1_layout.addWidget(QLabel("通道:"), 2, 0)
        self.out_ch = QLabel("--")
        self.out_ch.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        g1_layout.addWidget(self.out_ch, 2, 1)

        group1.setLayout(g1_layout)
        layout.addWidget(group1)

        # Universe/Channel -> 全局地址
        group2 = QGroupBox("Universe + 通道 → 全局地址")
        g2_layout = QGridLayout()

        g2_layout.addWidget(QLabel("Universe:"), 0, 0)
        self.in_uni = QSpinBox()
        self.in_uni.setRange(0, 63)
        g2_layout.addWidget(self.in_uni, 0, 1)

        g2_layout.addWidget(QLabel("通道 (1-512):"), 1, 0)
        self.in_ch = QSpinBox()
        self.in_ch.setRange(1, 512)
        self.in_ch.setValue(1)
        g2_layout.addWidget(self.in_ch, 1, 1)

        g2_btn = QPushButton("转换 →")
        g2_btn.clicked.connect(self._uc_to_global)
        g2_layout.addWidget(g2_btn, 2, 0, 1, 2)

        g2_layout.addWidget(QLabel("全局地址:"), 3, 0)
        self.out_global = QLabel("--")
        self.out_global.setStyleSheet("font-size: 16px; font-weight: bold; color: #4FC3F7;")
        g2_layout.addWidget(self.out_global, 3, 1)

        group2.setLayout(g2_layout)
        layout.addWidget(group2)

        layout.addStretch()

    def _global_to_uc(self):
        addr = self.global_addr.value()
        uni = (addr - 1) // 512
        ch = ((addr - 1) % 512) + 1
        self.out_uni.setText(f"Universe {uni}")
        self.out_ch.setText(str(ch))
        self.logger.info(f"全局地址 {addr} → Universe {uni}, 通道 {ch}")

    def _uc_to_global(self):
        uni = self.in_uni.value()
        ch = self.in_ch.value()
        addr = uni * 512 + ch
        self.out_global.setText(str(addr))
        self.logger.info(f"Universe {uni} + 通道 {ch} → 全局地址 {addr}")


class DMXCalculator(BaseToolWindow):
    """DMX计算器主窗口"""

    def __init__(self):
        super().__init__(
            tool_name="DMXCalculator",
            tool_title="DMX计算器",
            version="1.0.0",
            width=1100,
            height=850
        )

        # 构建中心内容
        central = QWidget()
        main_layout = QVBoxLayout(central)

        tabs = QTabWidget()

        self.calc_tab = AddressCalcTab(self.logger)
        tabs.addTab(self.calc_tab, "📐 地址计算")

        self.plan_tab = UniversePlanTab(self.logger)
        tabs.addTab(self.plan_tab, "🗺️ Universe规划")

        self.convert_tab = QuickConvertTab(self.logger)
        tabs.addTab(self.convert_tab, "⚡ 快速转换")

        main_layout.addWidget(tabs)
        self.set_central_content(central)

        self.logger.info("DMX计算器初始化完成")


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(DMXCalculator, "DMXCalculator - 启动错误")