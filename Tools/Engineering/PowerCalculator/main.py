# -*- coding: utf-8 -*-
"""
功率计算器 - 计算灯光系统总功率、电流、安全裕量
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QDoubleSpinBox, QSpinBox, QMessageBox,
    QSplitter, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class PowerCalculatorWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('PowerCalculator', '功率计算器', '1.0.0', 1000, 700)
        self.fixtures = []
        self._build_ui()
        self.logger.info('功率计算器初始化完成')

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # --- 输入区 ---
        input_group = QGroupBox('添加灯具')
        input_layout = QGridLayout()

        input_layout.addWidget(QLabel('灯具名称:'), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('例如: LED Wash 1000')
        input_layout.addWidget(self.name_edit, 0, 1)

        input_layout.addWidget(QLabel('功率 (W):'), 0, 2)
        self.watts_spin = QDoubleSpinBox()
        self.watts_spin.setRange(1, 50000)
        self.watts_spin.setValue(300)
        self.watts_spin.setSuffix(' W')
        input_layout.addWidget(self.watts_spin, 0, 3)

        input_layout.addWidget(QLabel('数量:'), 0, 4)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        self.qty_spin.setValue(12)
        input_layout.addWidget(self.qty_spin, 0, 5)

        add_btn = QPushButton('➕ 添加灯具')
        add_btn.clicked.connect(self._add_fixture)
        input_layout.addWidget(add_btn, 0, 6)

        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # --- 表格 ---
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['灯具名称', '功率 (W)', '数量', '小计 (W)', '操作'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.table, 1)

        # --- 计算参数区 ---
        params_group = QGroupBox('电气参数')
        params_layout = QGridLayout()

        params_layout.addWidget(QLabel('供电电压 (V):'), 0, 0)
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(100, 500)
        self.voltage_spin.setValue(220)
        self.voltage_spin.setSuffix(' V')
        params_layout.addWidget(self.voltage_spin, 0, 1)

        params_layout.addWidget(QLabel('功率因数:'), 0, 2)
        self.pf_spin = QDoubleSpinBox()
        self.pf_spin.setRange(0.1, 1.0)
        self.pf_spin.setValue(0.85)
        self.pf_spin.setSingleStep(0.01)
        params_layout.addWidget(self.pf_spin, 0, 3)

        params_layout.addWidget(QLabel('供电相数:'), 0, 4)
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(['单相', '三相'])
        params_layout.addWidget(self.phase_combo, 0, 5)

        calc_btn = QPushButton('⚡ 计算')
        calc_btn.clicked.connect(self._calculate)
        params_layout.addWidget(calc_btn, 0, 6)

        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)

        # --- 结果区 ---
        result_group = QGroupBox('计算结果')
        result_layout = QGridLayout()

        labels = ['总功率:', '视在功率:', '单相电流:', '三相电流:',
                  '80%安全裕量:', '建议额定容量:']
        self.result_labels = {}
        for i, text in enumerate(labels):
            row, col = divmod(i, 2)
            lbl = QLabel(text)
            lbl.setStyleSheet('font-weight: bold;')
            result_layout.addWidget(lbl, row, col * 2)
            val = QLabel('---')
            val.setStyleSheet('font-size: 16px; color: #00ff88; font-weight: bold;')
            result_layout.addWidget(val, row, col * 2 + 1)
            self.result_labels[text] = val

        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)

        self.set_central_content(central)

    def _add_fixture(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请输入灯具名称')
            return
        watts = self.watts_spin.value()
        qty = self.qty_spin.value()
        self.fixtures.append({'name': name, 'watts': watts, 'qty': qty})
        self._refresh_table()
        self.name_edit.clear()
        self.logger.info(f'添加灯具: {name} x{qty} @ {watts}W')

    def _refresh_table(self):
        self.table.setRowCount(len(self.fixtures))
        for i, f in enumerate(self.fixtures):
            self.table.setItem(i, 0, QTableWidgetItem(f['name']))
            self.table.setItem(i, 1, QTableWidgetItem(f'{f["watts"]:.1f}'))
            self.table.setItem(i, 2, QTableWidgetItem(str(f['qty'])))
            subtotal = f['watts'] * f['qty']
            self.table.setItem(i, 3, QTableWidgetItem(f'{subtotal:.1f}'))

            del_btn = QPushButton('删除')
            del_btn.clicked.connect(lambda _, idx=i: self._remove_fixture(idx))
            self.table.setCellWidget(i, 4, del_btn)

    def _remove_fixture(self, idx):
        if 0 <= idx < len(self.fixtures):
            removed = self.fixtures.pop(idx)
            self.logger.info(f'删除灯具: {removed["name"]}')
            self._refresh_table()

    def _calculate(self):
        if not self.fixtures:
            QMessageBox.warning(self, '提示', '请先添加灯具')
            return

        total_watts = sum(f['watts'] * f['qty'] for f in self.fixtures)
        voltage = self.voltage_spin.value()
        pf = self.pf_spin.value()
        is_three_phase = self.phase_combo.currentIndex() == 1

        apparent_power = total_watts / pf if pf > 0 else 0

        if is_three_phase:
            # 三相: I = P / (√3 × V × PF)
            current = total_watts / (1.732 * voltage * pf) if (voltage * pf) > 0 else 0
            current_display = current
        else:
            # 单相: I = P / (V × PF)
            current = total_watts / (voltage * pf) if (voltage * pf) > 0 else 0
            current_display = current

        # 80% 规则: 建议容量 = 总功率 / 0.8
        safety_capacity = total_watts / 0.8

        # 三相电流（始终计算作为参考）
        current_3p = total_watts / (1.732 * voltage * pf) if (voltage * pf) > 0 else 0
        current_1p = total_watts / (voltage * pf) if (voltage * pf) > 0 else 0

        self.result_labels['总功率:'].setText(f'{total_watts:.1f} W')
        self.result_labels['视在功率:'].setText(f'{apparent_power:.1f} VA ({apparent_power/1000:.2f} kVA)')
        self.result_labels['单相电流:'].setText(f'{current_1p:.2f} A')
        self.result_labels['三相电流:'].setText(f'{current_3p:.2f} A')
        self.result_labels['80%安全裕量:'].setText(f'{safety_capacity:.1f} W')
        self.result_labels['建议额定容量:'].setText(f'{safety_capacity/1000:.2f} kVA')

        self.logger.info(f'计算完成: 总功率 {total_watts:.0f}W, 视在 {apparent_power:.0f}VA, '
                         f'电流 {current_display:.2f}A')


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = PowerCalculatorWindow()
    win.show()
    sys.exit(app.exec())
