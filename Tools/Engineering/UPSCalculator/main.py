# -*- coding: utf-8 -*-
"""
UPS续航计算器 - 计算UPS电池续航时间，支持多组比较和电池配置
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDoubleSpinBox, QSpinBox, QComboBox, QMessageBox,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class UPSCalculatorWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('UPSCalculator', 'UPS续航计算器', '1.0.0', 900, 650)
        self.ups_list = []
        self._build_ui()
        self.logger.info('UPS续航计算器初始化完成')

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # --- 计算参数 ---
        input_group = QGroupBox('UPS / 电池参数')
        grid = QGridLayout()

        grid.addWidget(QLabel('电池容量 (Ah):'), 0, 0)
        self.ah_spin = QDoubleSpinBox()
        self.ah_spin.setRange(1, 10000)
        self.ah_spin.setValue(100)
        self.ah_spin.setSuffix(' Ah')
        grid.addWidget(self.ah_spin, 0, 1)

        grid.addWidget(QLabel('电池电压 (V):'), 0, 2)
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(1, 500)
        self.voltage_spin.setValue(12)
        self.voltage_spin.setSuffix(' V')
        grid.addWidget(self.voltage_spin, 0, 3)

        grid.addWidget(QLabel('UPS效率 (%):'), 1, 0)
        self.eff_spin = QDoubleSpinBox()
        self.eff_spin.setRange(50, 100)
        self.eff_spin.setValue(90)
        self.eff_spin.setSuffix(' %')
        grid.addWidget(self.eff_spin, 1, 1)

        grid.addWidget(QLabel('负载功率 (W):'), 1, 2)
        self.load_spin = QDoubleSpinBox()
        self.load_spin.setRange(1, 100000)
        self.load_spin.setValue(500)
        self.load_spin.setSuffix(' W')
        grid.addWidget(self.load_spin, 1, 3)

        grid.addWidget(QLabel('串联数量:'), 2, 0)
        self.series_spin = QSpinBox()
        self.series_spin.setRange(1, 100)
        self.series_spin.setValue(1)
        grid.addWidget(self.series_spin, 2, 1)

        grid.addWidget(QLabel('并联数量:'), 2, 2)
        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 100)
        self.parallel_spin.setValue(1)
        grid.addWidget(self.parallel_spin, 2, 3)

        btn_row = QHBoxLayout()
        calc_btn = QPushButton('⚡ 计算续航')
        calc_btn.clicked.connect(self._calculate)
        btn_row.addWidget(calc_btn)

        add_btn = QPushButton('➕ 添加到比较列表')
        add_btn.clicked.connect(self._add_to_compare)
        btn_row.addWidget(add_btn)

        clear_btn = QPushButton('🗑️ 清空列表')
        clear_btn.clicked.connect(lambda: self.ups_list.clear() or self._refresh_table())
        btn_row.addWidget(clear_btn)
        grid.addLayout(btn_row, 3, 0, 1, 4)

        input_group.setLayout(grid)
        main_layout.addWidget(input_group)

        # --- 结果显示 ---
        result_group = QGroupBox('计算结果')
        result_layout = QHBoxLayout()

        self.runtime_label = QLabel('---')
        self.runtime_label.setStyleSheet('font-size: 36px; color: #00ff88; font-weight: bold;')
        self.runtime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_layout.addWidget(self.runtime_label)

        info_frame = QFrame()
        info_grid = QGridLayout(info_frame)
        self.info_labels = {}
        info_items = ['总电池容量:', '有效容量:', '系统电压:', '实际负载:']
        for i, text in enumerate(info_items):
            lbl = QLabel(text)
            lbl.setStyleSheet('font-weight: bold;')
            info_grid.addWidget(lbl, i, 0)
            val = QLabel('---')
            val.setStyleSheet('color: #88ccff; font-size: 13px;')
            info_grid.addWidget(val, i, 1)
            self.info_labels[text] = val

        result_layout.addWidget(info_frame)
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)

        # --- 比较表 ---
        compare_group = QGroupBox('UPS方案比较')
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            '方案名称', '电池Ah', '电压V', '串联', '并联', '负载W', '续航(分钟)', '续航(小时)'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        compare_group.setLayout(QVBoxLayout())
        compare_group.layout().addWidget(self.table)
        main_layout.addWidget(compare_group)

        self.set_central_content(central)

    def _calculate(self):
        ah = self.ah_spin.value()
        voltage = self.voltage_spin.value()
        efficiency = self.eff_spin.value() / 100.0
        load_w = self.load_spin.value()
        series = self.series_spin.value()
        parallel = self.parallel_spin.value()

        # 系统电压 = 电池电压 × 串联数
        sys_voltage = voltage * series
        # 总容量 = 单组Ah × 并联数
        total_ah = ah * parallel
        # 有效容量 (考虑放电深度约80%)
        effective_ah = total_ah * 0.8
        # Runtime(min) = (Ah × V × η) / W × 60
        # 用系统电压和总Ah
        runtime_hours = (effective_ah * sys_voltage * efficiency) / load_w if load_w > 0 else 0
        runtime_min = runtime_hours * 60

        self.runtime_label.setText(self._format_runtime(runtime_min))

        self.info_labels['总电池容量:'].setText(f'{total_ah:.0f} Ah')
        self.info_labels['有效容量:'].setText(f'{effective_ah:.0f} Ah (80% DoD)')
        self.info_labels['系统电压:'].setText(f'{sys_voltage:.0f} V')
        self.info_labels['实际负载:'].setText(f'{load_w:.0f} W')

        self.logger.info(f'计算完成: {runtime_min:.1f} 分钟 ({runtime_hours:.2f} 小时)')
        return runtime_min

    def _format_runtime(self, minutes):
        if minutes < 1:
            return '续航不足'
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        if hours > 0:
            return f'{hours} 小时 {mins} 分钟'
        return f'{mins} 分钟'

    def _add_to_compare(self):
        runtime_min = self._calculate()
        entry = {
            'name': f'方案{len(self.ups_list)+1}',
            'ah': self.ah_spin.value(),
            'voltage': self.voltage_spin.value(),
            'series': self.series_spin.value(),
            'parallel': self.parallel_spin.value(),
            'load': self.load_spin.value(),
            'runtime_min': runtime_min
        }
        self.ups_list.append(entry)
        self._refresh_table()
        self.logger.info(f'添加比较方案: {entry["name"]}')

    def _refresh_table(self):
        self.table.setRowCount(len(self.ups_list))
        for i, e in enumerate(self.ups_list):
            self.table.setItem(i, 0, QTableWidgetItem(e['name']))
            self.table.setItem(i, 1, QTableWidgetItem(f'{e["ah"]:.0f}'))
            self.table.setItem(i, 2, QTableWidgetItem(f'{e["voltage"]:.0f}'))
            self.table.setItem(i, 3, QTableWidgetItem(str(e['series'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(e['parallel'])))
            self.table.setItem(i, 5, QTableWidgetItem(f'{e["load"]:.0f}'))
            self.table.setItem(i, 6, QTableWidgetItem(f'{e["runtime_min"]:.1f}'))
            self.table.setItem(i, 7, QTableWidgetItem(f'{e["runtime_min"]/60:.2f}'))


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = UPSCalculatorWindow()
    win.show()
    sys.exit(app.exec())
