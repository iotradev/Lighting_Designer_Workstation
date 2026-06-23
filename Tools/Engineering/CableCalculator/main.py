# -*- coding: utf-8 -*-
"""
线缆计算器 - 电压降计算、线缆尺寸推荐、线缆截面图
"""
import sys, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QDoubleSpinBox,
    QTextEdit, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath


# 铜/铝电阻率 (Ω·mm²/m) @ 20°C
RESISTIVITY = {'铜 (Cu)': 0.0175, '铝 (Al)': 0.0283}

# 标准线缆截面 (mm²)
CABLE_SIZES = [0.5, 0.75, 1.0, 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300]

# 载流量近似 (A, 铜, 明敷)
AMPACITY_CU = {0.5: 8, 0.75: 12, 1.0: 15, 1.5: 19, 2.5: 26, 4: 34, 6: 44,
               10: 61, 16: 82, 25: 108, 35: 135, 50: 168, 70: 213, 95: 258,
               120: 299, 150: 344, 185: 392, 240: 461, 300: 530}


class CableCrossSectionWidget(QWidget):
    """线缆截面可视化"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cable_size = 2.5
        self.material = '铜 (Cu)'
        self.setMinimumSize(200, 200)

    def set_cable(self, size, material):
        self.cable_size = size
        self.material = material
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        # 外径估算: 绝缘层 + 导体
        outer_r = min(w, h) * 0.42
        inner_r = outer_r * 0.7

        # 外层绝缘 (黑色)
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawEllipse(QRectF(cx - outer_r, cy - outer_r, outer_r * 2, outer_r * 2))

        # 内层绝缘 (灰色)
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawEllipse(QRectF(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2))

        # 导体
        conductor_color = QColor(220, 160, 50) if 'Cu' in self.material else QColor(180, 180, 190)
        conductor_r = inner_r * 0.8
        # 多股线效果
        strand_count = max(1, int(math.sqrt(self.cable_size) * 2))
        if strand_count <= 1:
            painter.setBrush(QBrush(conductor_color))
            painter.drawEllipse(QRectF(cx - conductor_r, cy - conductor_r, conductor_r * 2, conductor_r * 2))
        else:
            strand_r = conductor_r / (strand_count + 0.5)
            painter.setBrush(QBrush(conductor_color))
            for row in range(strand_count):
                for col in range(strand_count):
                    sx = cx - conductor_r + strand_r + col * strand_r * 2
                    sy = cy - conductor_r + strand_r + row * strand_r * 2
                    dist = math.sqrt((sx - cx)**2 + (sy - cy)**2)
                    if dist + strand_r <= conductor_r:
                        painter.drawEllipse(QRectF(sx - strand_r, sy - strand_r, strand_r * 2, strand_r * 2))

        # 标注
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(QRectF(0, h - 50, w, 50), Qt.AlignmentFlag.AlignCenter,
                         f'{self.cable_size} mm² {self.material}')

        painter.end()


class CableCalculatorWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('CableCalculator', '线缆计算器', '1.0.0', 1000, 700)
        self._build_ui()
        self.logger.info('线缆计算器初始化完成')

    def _build_ui(self):
        central = QWidget()
        main_layout = QHBoxLayout(central)

        # --- 左侧: 输入和结果 ---
        left = QWidget()
        left_layout = QVBoxLayout(left)

        # 输入
        input_group = QGroupBox('计算参数')
        grid = QGridLayout()

        grid.addWidget(QLabel('电流 (A):'), 0, 0)
        self.current_spin = QDoubleSpinBox()
        self.current_spin.setRange(0.1, 10000)
        self.current_spin.setValue(32)
        self.current_spin.setSuffix(' A')
        grid.addWidget(self.current_spin, 0, 1)

        grid.addWidget(QLabel('线缆长度 (m):'), 1, 0)
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setRange(1, 10000)
        self.length_spin.setValue(50)
        self.length_spin.setSuffix(' m')
        grid.addWidget(self.length_spin, 1, 1)

        grid.addWidget(QLabel('线缆材质:'), 2, 0)
        self.material_combo = QComboBox()
        self.material_combo.addItems(['铜 (Cu)', '铝 (Al)'])
        grid.addWidget(self.material_combo, 2, 1)

        grid.addWidget(QLabel('供电电压 (V):'), 3, 0)
        self.voltage_spin = QDoubleSpinBox()
        self.voltage_spin.setRange(100, 500)
        self.voltage_spin.setValue(220)
        self.voltage_spin.setSuffix(' V')
        grid.addWidget(self.voltage_spin, 3, 1)

        grid.addWidget(QLabel('允许压降 (%):'), 4, 0)
        self.drop_limit_spin = QDoubleSpinBox()
        self.drop_limit_spin.setRange(0.5, 10)
        self.drop_limit_spin.setValue(3.0)
        self.drop_limit_spin.setSuffix(' %')
        grid.addWidget(self.drop_limit_spin, 4, 1)

        calc_btn = QPushButton('⚡ 计算')
        calc_btn.clicked.connect(self._calculate)
        grid.addWidget(calc_btn, 5, 0, 1, 2)

        input_group.setLayout(grid)
        left_layout.addWidget(input_group)

        # 结果
        result_group = QGroupBox('计算结果')
        result_layout = QGridLayout()

        self.result_labels = {}
        labels = ['电压降 (V):', '压降百分比:', '功率损耗 (W):',
                  '推荐线缆 (mm²):', '允许载流量:', '结果判定:']
        for i, text in enumerate(labels):
            row, col = divmod(i, 2)
            lbl = QLabel(text)
            lbl.setStyleSheet('font-weight: bold;')
            result_layout.addWidget(lbl, row, col * 2)
            val = QLabel('---')
            val.setStyleSheet('font-size: 14px; color: #00ff88; font-weight: bold;')
            result_layout.addWidget(val, row, col * 2 + 1)
            self.result_labels[text] = val

        result_group.setLayout(result_layout)
        left_layout.addWidget(result_group)

        # 载流量参考表
        ref_group = QGroupBox('常用线缆载流量参考 (铜)')
        ref_text = QTextEdit()
        ref_text.setReadOnly(True)
        ref_text.setMaximumHeight(150)
        ref_lines = ['截面(mm²)  载流量(A)']
        for s, a in AMPACITY_CU.items():
            ref_lines.append(f'  {s:<10} {a}')
        ref_text.setText('\n'.join(ref_lines))
        ref_group.setLayout(QVBoxLayout())
        ref_group.layout().addWidget(ref_text)
        left_layout.addWidget(ref_group)

        # --- 右侧: 截面图 ---
        right = QWidget()
        right_layout = QVBoxLayout(right)

        self.cable_widget = CableCrossSectionWidget()
        right_layout.addWidget(self.cable_widget)

        right_layout.addStretch()
        main_layout.addWidget(left, 2)
        main_layout.addWidget(right, 1)

        self.set_central_content(central)

    def _calculate(self):
        current = self.current_spin.value()
        length = self.length_spin.value()
        material = self.material_combo.currentText()
        voltage = self.voltage_spin.value()
        drop_limit = self.drop_limit_spin.value()

        rho = RESISTIVITY.get(material, 0.0175)

        # 推荐线缆: Vd = 2 * L * I * rho / S => S = 2 * L * I * rho / (voltage * drop%)
        max_vdrop = voltage * drop_limit / 100.0
        if max_vdrop > 0 and current > 0 and length > 0:
            required_s = 2 * length * current * rho / max_vdrop
        else:
            required_s = 0

        # 取最接近的标准尺寸
        recommended = CABLE_SIZES[-1]
        for s in CABLE_SIZES:
            if s >= required_s:
                recommended = s
                break

        # 实际压降
        actual_vdrop = 2 * length * current * rho / recommended
        actual_pct = (actual_vdrop / voltage) * 100 if voltage > 0 else 0
        power_loss = actual_vdrop * current

        # 载流量判断
        ampacity = AMPACITY_CU.get(recommended, 0)
        if 'Al' in material:
            ampacity = int(ampacity * 0.78)  # 铝线载流量约78%

        ok = actual_pct <= drop_limit and current <= ampacity

        self.result_labels['电压降 (V):'].setText(f'{actual_vdrop:.2f} V')
        self.result_labels['压降百分比:'].setText(f'{actual_pct:.2f} %')
        self.result_labels['功率损耗 (W):'].setText(f'{power_loss:.1f} W')
        self.result_labels['推荐线缆 (mm²):'].setText(f'{recommended} mm²')
        self.result_labels['允许载流量:'].setText(f'{ampacity} A')

        if ok:
            self.result_labels['结果判定:'].setText('✅ 合格')
            self.result_labels['结果判定:'].setStyleSheet('font-size: 14px; color: #00ff88; font-weight: bold;')
        else:
            reasons = []
            if actual_pct > drop_limit:
                reasons.append('压降超标')
            if current > ampacity:
                reasons.append('载流量不足')
            self.result_labels['结果判定:'].setText(f'❌ 不合格 ({"、".join(reasons)})')
            self.result_labels['结果判定:'].setStyleSheet('font-size: 14px; color: #ff4444; font-weight: bold;')

        # 更新截面图
        self.cable_widget.set_cable(recommended, material)

        self.logger.info(f'计算完成: 推荐 {recommended}mm², 压降 {actual_pct:.2f}%, '
                         f'损耗 {power_loss:.1f}W, {"合格" if ok else "不合格"}')


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(CableCalculatorWindow, "CableCalculator - 启动错误")