# -*- coding: utf-8 -*-
"""
配电规划器 - 规划灯光系统配电方案，三相负载平衡，功率流向图
"""
import sys, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QDoubleSpinBox, QSpinBox, QComboBox, QMessageBox,
    QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont


class PowerFlowDiagram(QWidget):
    """功率流向图 - QPainter树形图"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.supply_kva = 100
        self.phases = [[], [], []]  # 三相负载
        self.setMinimumSize(400, 300)

    def set_data(self, supply_kva, phases):
        self.supply_kva = supply_kva
        self.phases = phases
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        # 供电节点
        supply_x, supply_y = w // 2, 40
        self._draw_node(painter, supply_x, supply_y, 120, 40,
                        f'主供电 {self.supply_kva:.0f} kVA', QColor(50, 120, 200))

        phase_colors = [QColor(200, 60, 60), QColor(60, 180, 60), QColor(60, 60, 200)]
        phase_names = ['L1 (A相)', 'L2 (B相)', 'L3 (C相)']

        # 三相分支
        phase_x_start = 80
        phase_x_step = (w - 160) // 3

        total_per_phase = []
        for i in range(3):
            px = phase_x_start + i * phase_x_step + phase_x_step // 2
            py = 140
            total = sum(load['watts'] * load['qty'] for load in self.phases[i]) / 1000.0
            total_per_phase.append(total)
            self._draw_line(painter, supply_x, supply_y + 40, px, py)
            self._draw_node(painter, px, py, 140, 36,
                            f'{phase_names[i]}: {total:.1f} kW', phase_colors[i])

            # 负载节点
            for j, load in enumerate(self.phases[i]):
                ly = py + 60 + j * 50
                kw = load['watts'] * load['qty'] / 1000.0
                self._draw_line(painter, px, py + 36, px, ly)
                self._draw_node(painter, px, ly, 160, 32,
                                f'{load["name"]} x{load["qty"]} ({kw:.1f}kW)', QColor(80, 80, 80))

        # 平衡指示
        max_load = max(total_per_phase) if total_per_phase else 0
        min_load = min(total_per_phase) if total_per_phase else 0
        imbalance = ((max_load - min_load) / max_load * 100) if max_load > 0 else 0

        info_y = h - 40
        painter.setPen(QColor(200, 200, 200))
        balance_color = QColor(0, 255, 136) if imbalance < 15 else QColor(255, 200, 0) if imbalance < 30 else QColor(255, 60, 60)
        painter.setPen(balance_color)
        painter.drawText(QRectF(0, info_y, w, 30), Qt.AlignmentFlag.AlignCenter,
                         f'负载不平衡度: {imbalance:.1f}%  |  总计: {sum(total_per_phase):.1f} kW')

        painter.end()

    def _draw_node(self, painter, x, y, w, h, text, color):
        painter.setPen(QPen(color, 2))
        painter.setBrush(QBrush(color.darker(200)))
        painter.drawRoundedRect(QRectF(x - w/2, y - h/2, w, h), 8, 8)
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(QRectF(x - w/2, y - h/2, w, h),
                         Qt.AlignmentFlag.AlignCenter, text)

    def _draw_line(self, painter, x1, y1, x2, y2):
        painter.setPen(QPen(QColor(120, 120, 120), 2))
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))


class DistributionPlannerWindow(BaseToolWindow):
    def __init__(self):
        super().__init__('DistributionPlanner', '配电规划器', '1.0.0', 1100, 800)
        self.loads = []
        self._build_ui()
        self.logger.info('配电规划器初始化完成')

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- 上半部: 输入 + 表格 ---
        top = QWidget()
        top_layout = QHBoxLayout(top)

        # 左: 输入
        input_group = QGroupBox('添加负载')
        input_grid = QGridLayout()

        input_grid.addWidget(QLabel('负载名称:'), 0, 0)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('例如: 舞台面光')
        input_grid.addWidget(self.name_edit, 0, 1)

        input_grid.addWidget(QLabel('单组功率 (W):'), 1, 0)
        self.watts_spin = QDoubleSpinBox()
        self.watts_spin.setRange(1, 50000)
        self.watts_spin.setValue(2000)
        self.watts_spin.setSuffix(' W')
        input_grid.addWidget(self.watts_spin, 1, 1)

        input_grid.addWidget(QLabel('数量:'), 2, 0)
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 100)
        self.qty_spin.setValue(1)
        input_grid.addWidget(self.qty_spin, 2, 1)

        input_grid.addWidget(QLabel('分配相位:'), 3, 0)
        self.phase_combo = QComboBox()
        self.phase_combo.addItems(['自动分配', 'A相 (L1)', 'B相 (L2)', 'C相 (L3)'])
        input_grid.addWidget(self.phase_combo, 3, 1)

        input_grid.addWidget(QLabel('供电容量 (kVA):'), 4, 0)
        self.supply_spin = QDoubleSpinBox()
        self.supply_spin.setRange(1, 10000)
        self.supply_spin.setValue(100)
        self.supply_spin.setSuffix(' kVA')
        input_grid.addWidget(self.supply_spin, 4, 1)

        btn_row = QHBoxLayout()
        add_btn = QPushButton('➕ 添加')
        add_btn.clicked.connect(self._add_load)
        btn_row.addWidget(add_btn)
        auto_btn = QPushButton('🔄 自动均衡')
        auto_btn.clicked.connect(self._auto_balance)
        btn_row.addWidget(auto_btn)
        clear_btn = QPushButton('🗑️ 清空')
        clear_btn.clicked.connect(self._clear_all)
        btn_row.addWidget(clear_btn)
        input_grid.addLayout(btn_row, 5, 0, 1, 2)

        input_group.setLayout(input_grid)
        top_layout.addWidget(input_group, 1)

        # 右: 表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(['负载名称', '功率(W)', '数量', '相位', '小计(W)'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        top_layout.addWidget(self.table, 2)

        splitter.addWidget(top)

        # --- 下半部: 图 + 结果 ---
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)

        self.diagram = PowerFlowDiagram()
        bottom_layout.addWidget(self.diagram, 2)

        # 结果面板
        result_group = QGroupBox('配电汇总')
        result_layout = QGridLayout()
        self.phase_labels = {}
        phase_names = ['A相 (L1)', 'B相 (L2)', 'C相 (C3)']
        phase_colors = ['#cc3c3c', '#3cb43c', '#3c3ccc']
        for i, (name, color) in enumerate(zip(phase_names, phase_colors)):
            lbl = QLabel(f'{name}:')
            lbl.setStyleSheet(f'font-weight: bold; color: {color};')
            result_layout.addWidget(lbl, i, 0)
            val = QLabel('0 W')
            val.setStyleSheet(f'font-size: 14px; color: {color}; font-weight: bold;')
            result_layout.addWidget(val, i, 1)
            self.phase_labels[i] = val

        self.total_label = QLabel('总计: 0 W')
        self.total_label.setStyleSheet('font-size: 16px; color: #00ff88; font-weight: bold;')
        result_layout.addWidget(self.total_label, 3, 0, 1, 2)

        self.warning_label = QLabel('')
        self.warning_label.setStyleSheet('font-size: 12px; color: #ff4444; font-weight: bold;')
        result_layout.addWidget(self.warning_label, 4, 0, 1, 2)

        result_group.setLayout(result_layout)
        bottom_layout.addWidget(result_group, 1)

        splitter.addWidget(bottom)
        main_layout.addWidget(splitter)
        self.set_central_content(central)

    def _add_load(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, '提示', '请输入负载名称')
            return
        watts = self.watts_spin.value()
        qty = self.qty_spin.value()
        phase = self.phase_combo.currentIndex()  # 0=auto
        self.loads.append({'name': name, 'watts': watts, 'qty': qty, 'phase': phase})
        self.name_edit.clear()
        self._update_all()
        self.logger.info(f'添加负载: {name} x{qty} @ {watts}W')

    def _clear_all(self):
        self.loads.clear()
        self._update_all()

    def _auto_balance(self):
        """自动均衡分配负载到三相"""
        if not self.loads:
            return
        # 简单贪心: 每次分配给当前总功率最小的相
        phase_totals = [0, 0, 0]
        # 按功率降序排列
        sorted_loads = sorted(self.loads, key=lambda x: x['watts'] * x['qty'], reverse=True)
        for load in sorted_loads:
            min_phase = phase_totals.index(min(phase_totals))
            load['phase'] = min_phase + 1  # 1-indexed for combo (1=L1, 2=L2, 3=L3)
            phase_totals[min_phase] += load['watts'] * load['qty']
        self._update_all()
        self.logger.info('已自动均衡分配负载')

    def _update_all(self):
        self._refresh_table()
        self._update_results()
        self._update_diagram()

    def _refresh_table(self):
        phase_names = {0: '自动', 1: 'A相 (L1)', 2: 'B相 (L2)', 3: 'C相 (L3)'}
        self.table.setRowCount(len(self.loads))
        for i, load in enumerate(self.loads):
            self.table.setItem(i, 0, QTableWidgetItem(load['name']))
            self.table.setItem(i, 1, QTableWidgetItem(f'{load["watts"]:.0f}'))
            self.table.setItem(i, 2, QTableWidgetItem(str(load['qty'])))
            self.table.setItem(i, 3, QTableWidgetItem(phase_names.get(load['phase'], '?')))
            self.table.setItem(i, 4, QTableWidgetItem(f'{load["watts"] * load["qty"]:.0f}'))

    def _get_phase_assignments(self):
        """返回 [[], [], []] 三相的负载列表"""
        phases = [[], [], []]
        auto_phase = 0
        auto_totals = [0, 0, 0]

        for load in self.loads:
            p = load['phase']
            if p == 0:
                # 自动分配: 给最小负载的相
                min_p = auto_totals.index(min(auto_totals))
                phases[min_p].append(load)
                auto_totals[min_p] += load['watts'] * load['qty']
            else:
                phases[p - 1].append(load)

        return phases

    def _update_results(self):
        phases = self._get_phase_assignments()
        total = 0
        phase_totals = []
        for i, phase_loads in enumerate(phases):
            phase_total = sum(l['watts'] * l['qty'] for l in phase_loads)
            phase_totals.append(phase_total)
            total += phase_total
            self.phase_labels[i].setText(f'{phase_total:.0f} W ({phase_total/1000:.2f} kW)')

        self.total_label.setText(f'总计: {total:.0f} W ({total/1000:.2f} kW)')

        # 过载检查
        supply_w = self.supply_spin.value() * 1000
        warnings = []
        if total > supply_w:
            warnings.append(f'⚠️ 总负载 ({total/1000:.1f}kW) 超过供电容量 ({supply_w/1000:.1f}kW)!')
        max_p = max(phase_totals) if phase_totals else 0
        if max_p > supply_w / 3:
            warnings.append(f'⚠️ 单相负载 ({max_p/1000:.1f}kW) 超过单相容量 ({supply_w/3/1000:.1f}kW)!')
        self.warning_label.setText('\n'.join(warnings) if warnings else '✅ 负载在安全范围内')

    def _update_diagram(self):
        phases = self._get_phase_assignments()
        self.diagram.set_data(self.supply_spin.value(), phases)


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = DistributionPlannerWindow()
    win.show()
    sys.exit(app.exec())
