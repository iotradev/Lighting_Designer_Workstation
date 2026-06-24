# -*- coding: utf-8 -*-
"""
发电机容量计算器 - 计算所需发电机容量、燃油消耗、多场景比较
"""
import sys
from pathlib import Path

try:
    import path_setup
except ImportError:
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location('path_setup', str(Path(__file__).resolve().parent.parent.parent.parent / 'path_setup.py'))
    _mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod); import sys; sys.modules['path_setup'] = _mod; path_setup = _mod
path_setup.ensure_common_path(__file__)
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDoubleSpinBox, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt


class GeneratorCalculatorWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('GeneratorCalculator', '发电机容量计算器', '1.0.0', 900, 650)
        self.scenarios = []
        self._build_ui()
        self.logger.info('发电机容量计算器初始化完成')

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # --- 输入参数 ---
        input_group = QGroupBox('负载参数')
        grid = QGridLayout()

        grid.addWidget(QLabel('负载总功率 (kW):'), 0, 0)
        self.load_kw_spin = QDoubleSpinBox()
        self.load_kw_spin.setRange(0.1, 10000)
        self.load_kw_spin.setValue(50)
        self.load_kw_spin.setSuffix(' kW')
        grid.addWidget(self.load_kw_spin, 0, 1)

        grid.addWidget(QLabel('功率因数 (PF):'), 0, 2)
        self.pf_spin = QDoubleSpinBox()
        self.pf_spin.setRange(0.1, 1.0)
        self.pf_spin.setValue(0.8)
        self.pf_spin.setSingleStep(0.01)
        grid.addWidget(self.pf_spin, 0, 3)

        grid.addWidget(QLabel('启动系数:'), 1, 0)
        self.start_factor_spin = QDoubleSpinBox()
        self.start_factor_spin.setRange(1.0, 8.0)
        self.start_factor_spin.setValue(1.5)
        self.start_factor_spin.setSingleStep(0.1)
        self.start_factor_spin.setToolTip('电机类负载启动电流倍数，一般1.5~3倍')
        grid.addWidget(self.start_factor_spin, 1, 1)

        grid.addWidget(QLabel('冗余系数:'), 1, 2)
        self.redundancy_spin = QDoubleSpinBox()
        self.redundancy_spin.setRange(1.0, 2.0)
        self.redundancy_spin.setValue(1.1)
        self.redundancy_spin.setSingleStep(0.05)
        self.redundancy_spin.setToolTip('安全裕量系数')
        grid.addWidget(self.redundancy_spin, 1, 3)

        grid.addWidget(QLabel('柴油机燃油消耗率 (g/kWh):'), 2, 0)
        self.fuel_rate_spin = QDoubleSpinBox()
        self.fuel_rate_spin.setRange(100, 400)
        self.fuel_rate_spin.setValue(210)
        self.fuel_rate_spin.setSuffix(' g/kWh')
        grid.addWidget(self.fuel_rate_spin, 2, 1)

        grid.addWidget(QLabel('柴油密度 (kg/L):'), 2, 2)
        self.diesel_density_spin = QDoubleSpinBox()
        self.diesel_density_spin.setRange(0.7, 0.9)
        self.diesel_density_spin.setValue(0.835)
        self.diesel_density_spin.setDecimals(3)
        grid.addWidget(self.diesel_density_spin, 2, 3)

        grid.addWidget(QLabel('场景名称:'), 3, 0)
        self.scenario_edit = QLineEdit()
        self.scenario_edit.setPlaceholderText('例如: 音乐会满载')
        grid.addWidget(self.scenario_edit, 3, 1)

        btn_row = QHBoxLayout()
        calc_btn = QPushButton('⚡ 计算')
        calc_btn.clicked.connect(self._calculate)
        btn_row.addWidget(calc_btn)
        add_btn = QPushButton('➕ 保存场景')
        add_btn.clicked.connect(self._add_scenario)
        btn_row.addWidget(add_btn)
        clear_btn = QPushButton('🗑️ 清空场景')
        clear_btn.clicked.connect(lambda: self.scenarios.clear() or self._refresh_table())
        btn_row.addWidget(clear_btn)
        grid.addLayout(btn_row, 4, 0, 1, 4)

        input_group.setLayout(grid)
        main_layout.addWidget(input_group)

        # --- 结果 ---
        result_group = QGroupBox('计算结果')
        result_layout = QGridLayout()

        self.result_labels = {}
        results = [
            ('负载视在功率:', 'kVA'),
            ('考虑启动系数后:', 'kVA'),
            ('推荐发电机容量:', 'kVA'),
            ('柴油消耗 (额定):', 'L/h'),
            ('柴油消耗 (75%负载):', 'L/h'),
            ('标准发电机型号:', ''),
        ]
        for i, (text, unit) in enumerate(results):
            row, col = divmod(i, 2)
            lbl = QLabel(text)
            lbl.setStyleSheet('font-weight: bold;')
            result_layout.addWidget(lbl, row, col * 2)
            val = QLabel('---')
            val.setStyleSheet('font-size: 15px; color: #00ff88; font-weight: bold;')
            result_layout.addWidget(val, row, col * 2 + 1)
            self.result_labels[text] = (val, unit)

        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)

        # --- 场景比较 ---
        compare_group = QGroupBox('场景比较')
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            '场景', '负载(kW)', 'PF', '启动系数', '推荐容量(kVA)', '油耗(L/h)', '75%油耗(L/h)'
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        compare_group.setLayout(QVBoxLayout())
        compare_group.layout().addWidget(self.table)
        main_layout.addWidget(compare_group)

        self.set_central_content(central)

    def _calculate(self):
        load_kw = self.load_kw_spin.value()
        pf = self.pf_spin.value()
        start_factor = self.start_factor_spin.value()
        redundancy = self.redundancy_spin.value()
        fuel_rate = self.fuel_rate_spin.value()  # g/kWh
        diesel_density = self.diesel_density_spin.value()  # kg/L

        # 视在功率 S = P / PF
        apparent_kva = load_kw / pf if pf > 0 else 0

        # 考虑启动系数
        startup_kva = apparent_kva * start_factor

        # 推荐容量 = max(正常视在功率, 启动需求) × 冗余系数
        recommended_kva = max(apparent_kva, startup_kva) * redundancy

        # 取标准发电机容量（向上取整到常见规格）
        std_sizes = [5, 8, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150, 175, 200,
                     250, 300, 350, 400, 500, 600, 750, 800, 1000, 1250, 1500, 2000]
        std_gen = std_sizes[-1]
        for s in std_sizes:
            if s >= recommended_kva:
                std_gen = s
                break

        # 油耗: 额定 = 额定kW × fuel_rate / (density × 1000)
        # 实际带载75%时
        fuel_full = (std_gen * pf) * fuel_rate / (diesel_density * 1000)  # L/h
        fuel_75 = (std_gen * 0.75 * pf) * fuel_rate / (diesel_density * 1000)  # L/h

        labels = self.result_labels
        labels['负载视在功率:'][0].setText(f'{apparent_kva:.1f} kVA')
        labels['考虑启动系数后:'][0].setText(f'{startup_kva:.1f} kVA')
        labels['推荐发电机容量:'][0].setText(f'{recommended_kva:.1f} kVA')
        labels['柴油消耗 (额定):'][0].setText(f'{fuel_full:.1f} L/h')
        labels['柴油消耗 (75%负载):'][0].setText(f'{fuel_75:.1f} L/h')
        labels['标准发电机型号:'][0].setText(f'{std_gen} kVA 柴油发电机组')

        self.logger.info(f'计算完成: 推荐 {recommended_kva:.1f}kVA, 标准 {std_gen}kVA')
        return recommended_kva, std_gen, fuel_full, fuel_75

    def _add_scenario(self):
        result = self._calculate()
        name = self.scenario_edit.text().strip() or f'场景{len(self.scenarios)+1}'
        recommended, std_gen, fuel_full, fuel_75 = result
        self.scenarios.append({
            'name': name,
            'load_kw': self.load_kw_spin.value(),
            'pf': self.pf_spin.value(),
            'start_factor': self.start_factor_spin.value(),
            'recommended': recommended,
            'std_gen': std_gen,
            'fuel_full': fuel_full,
            'fuel_75': fuel_75,
        })
        self._refresh_table()
        self.scenario_edit.clear()
        self.logger.info(f'保存场景: {name}')

    def _refresh_table(self):
        self.table.setRowCount(len(self.scenarios))
        for i, s in enumerate(self.scenarios):
            self.table.setItem(i, 0, QTableWidgetItem(s['name']))
            self.table.setItem(i, 1, QTableWidgetItem(f'{s["load_kw"]:.1f}'))
            self.table.setItem(i, 2, QTableWidgetItem(f'{s["pf"]:.2f}'))
            self.table.setItem(i, 3, QTableWidgetItem(f'{s["start_factor"]:.1f}'))
            self.table.setItem(i, 4, QTableWidgetItem(f'{s["recommended"]:.1f} / {s["std_gen"]}'))
            self.table.setItem(i, 5, QTableWidgetItem(f'{s["fuel_full"]:.1f}'))
            self.table.setItem(i, 6, QTableWidgetItem(f'{s["fuel_75"]:.1f}'))


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(GeneratorCalculatorWindow, "GeneratorCalculator - 启动错误")