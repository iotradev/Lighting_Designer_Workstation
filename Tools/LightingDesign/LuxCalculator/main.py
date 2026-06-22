"""
照度计算器 (LuxCalculator)
基于反平方定律的照明照度计算器
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QDoubleSpinBox, QTextEdit, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QFont, QBrush, QPen, QRadialGradient
from ui.base_window import BaseToolWindow


class HeatmapWidget(QWidget):
    """照度热力图显示"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fixtures = []  # [(x, y, intensity), ...]
        self.area_width = 20.0  # 米
        self.area_depth = 20.0
        self.setMinimumSize(400, 400)
    
    def update_fixtures(self, fixtures, area_w=20, area_d=20):
        self.fixtures = fixtures
        self.area_width = area_w
        self.area_depth = area_d
        self.update()
    
    def _lux_at_point(self, px, py):
        """计算某点的总照度"""
        total_lux = 0.0
        for fx, fy, intensity in self.fixtures:
            dx = px - fx
            dy = py - fy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.1:
                dist = 0.1
            # 反平方定律 + 余弦修正
            # 假设灯具垂直向下照射
            lux = intensity / (dist * dist + 1.0)  # +1 避免除以0
            total_lux += lux
        return total_lux
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 背景
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))
        
        margin = 50
        draw_w = w - 2 * margin
        draw_h = h - 2 * margin
        
        if draw_w <= 0 or draw_h <= 0:
            return
        
        # 采样网格生成热力图
        grid_size = 8  # 像素
        max_lux = 1.0
        
        # 先计算最大lux用于归一化
        for gx in range(0, draw_w, grid_size):
            for gy in range(0, draw_h, grid_size):
                px = (gx / draw_w) * self.area_width
                py = (gy / draw_h) * self.area_depth
                lux = self._lux_at_point(px, py)
                if lux > max_lux:
                    max_lux = lux
        
        # 绘制热力图
        for gx in range(0, draw_w, grid_size):
            for gy in range(0, draw_h, grid_size):
                px = (gx / draw_w) * self.area_width
                py = (gy / draw_h) * self.area_depth
                lux = self._lux_at_point(px, py)
                
                ratio = min(lux / max_lux, 1.0)
                
                # 颜色映射: 蓝(低) -> 绿 -> 黄 -> 红(高)
                if ratio < 0.33:
                    r = 0
                    g = int(ratio * 3 * 255)
                    b = 255
                elif ratio < 0.66:
                    t = (ratio - 0.33) * 3
                    r = int(t * 255)
                    g = 255
                    b = int((1 - t) * 255)
                else:
                    t = (ratio - 0.66) * 3
                    r = 255
                    g = int((1 - t) * 255)
                    b = 0
                
                color = QColor(r, g, b, 200)
                painter.fillRect(margin + gx, margin + gy, grid_size, grid_size, color)
        
        # 绘制灯具位置
        for fx, fy, intensity in self.fixtures:
            sx = margin + int((fx / self.area_width) * draw_w)
            sy = margin + int((fy / self.area_depth) * draw_h)
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.setBrush(QBrush(QColor(255, 255, 0)))
            painter.drawEllipse(sx - 6, sy - 6, 12, 12)
            painter.setPen(QColor(255, 255, 255))
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(sx + 8, sy - 2, f"{intensity:.0f}cd")
        
        # 绘制坐标轴
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawLine(margin, margin + draw_h, margin + draw_w, margin + draw_h)
        painter.drawLine(margin, margin, margin, margin + draw_h)
        
        # 标尺
        for i in range(0, int(self.area_width) + 1, max(1, int(self.area_width) // 5)):
            x = margin + int((i / self.area_width) * draw_w)
            painter.drawLine(x, margin + draw_h, x, margin + draw_h + 5)
            painter.drawText(x - 10, margin + draw_h + 18, f"{i}m")
        
        for i in range(0, int(self.area_depth) + 1, max(1, int(self.area_depth) // 5)):
            y = margin + int((i / self.area_depth) * draw_h)
            painter.drawLine(margin - 5, y, margin, y)
            painter.drawText(margin - 35, y + 4, f"{i}m")
        
        # 色标
        legend_x = margin + draw_w + 10
        for i in range(draw_h):
            ratio = i / draw_h
            if ratio < 0.33:
                r, g, b = 0, int(ratio * 3 * 255), 255
            elif ratio < 0.66:
                t = (ratio - 0.33) * 3
                r, g, b = int(t * 255), 255, int((1 - t) * 255)
            else:
                t = (ratio - 0.66) * 3
                r, g, b = 255, int((1 - t) * 255), 0
            painter.fillRect(legend_x, margin + i, 15, 1, QColor(r, g, b))
        
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(legend_x, margin - 5, f"{max_lux:.0f}lx")
        painter.drawText(legend_x, margin + draw_h + 15, "0lx")
        
        painter.end()


class LuxCalculator(BaseToolWindow):
    def __init__(self):
        super().__init__('LuxCalculator', '照度计算器', '1.0.0', 1000, 700)
        self.fixtures = []
        self._setup_ui()
    
    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 单点计算
        single_group = QGroupBox("单点照度计算")
        single_layout = QGridLayout(single_group)
        
        single_layout.addWidget(QLabel("灯具强度 (cd):"), 0, 0)
        self.intensity_spin = QDoubleSpinBox()
        self.intensity_spin.setRange(1, 1000000)
        self.intensity_spin.setValue(10000)
        single_layout.addWidget(self.intensity_spin, 0, 1)
        
        single_layout.addWidget(QLabel("距离 (m):"), 1, 0)
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.1, 500)
        self.distance_spin.setValue(5)
        single_layout.addWidget(self.distance_spin, 1, 1)
        
        single_layout.addWidget(QLabel("光束角度 (°):"), 2, 0)
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(1, 180)
        self.angle_spin.setValue(30)
        single_layout.addWidget(self.angle_spin, 2, 1)
        
        btn_calc = QPushButton("计算照度")
        btn_calc.clicked.connect(self._calc_single)
        single_layout.addWidget(btn_calc, 3, 0, 1, 2)
        
        self.single_result = QLabel("照度: -- lux")
        self.single_result.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ff88;")
        single_layout.addWidget(self.single_result, 4, 0, 1, 2)
        
        left_layout.addWidget(single_group)
        
        # 多灯具管理
        multi_group = QGroupBox("多灯具管理")
        multi_layout = QVBoxLayout(multi_group)
        
        add_layout = QGridLayout()
        add_layout.addWidget(QLabel("X (m):"), 0, 0)
        self.fx_spin = QDoubleSpinBox()
        self.fx_spin.setRange(0, 100)
        self.fx_spin.setValue(5)
        add_layout.addWidget(self.fx_spin, 0, 1)
        
        add_layout.addWidget(QLabel("Y (m):"), 0, 2)
        self.fy_spin = QDoubleSpinBox()
        self.fy_spin.setRange(0, 100)
        self.fy_spin.setValue(5)
        add_layout.addWidget(self.fy_spin, 0, 3)
        
        add_layout.addWidget(QLabel("强度 (cd):"), 1, 0)
        self.fintensity_spin = QDoubleSpinBox()
        self.fintensity_spin.setRange(1, 1000000)
        self.fintensity_spin.setValue(10000)
        add_layout.addWidget(self.fintensity_spin, 1, 1, 1, 3)
        
        btn_add = QPushButton("添加灯具")
        btn_add.clicked.connect(self._add_fixture)
        add_layout.addWidget(btn_add, 2, 0, 1, 2)
        
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self._clear_fixtures)
        add_layout.addWidget(btn_clear, 2, 2, 1, 2)
        
        multi_layout.addLayout(add_layout)
        
        # 灯具列表
        self.fixture_table = QTableWidget()
        self.fixture_table.setColumnCount(4)
        self.fixture_table.setHorizontalHeaderLabels(["编号", "X (m)", "Y (m)", "强度 (cd)"])
        self.fixture_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        multi_layout.addWidget(self.fixture_table)
        
        btn_update = QPushButton("更新热力图")
        btn_update.clicked.connect(self._update_heatmap)
        multi_layout.addWidget(btn_update)
        
        left_layout.addWidget(multi_group)
        
        # 结果
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout(result_group)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(100)
        result_layout.addWidget(self.result_text)
        left_layout.addWidget(result_group)
        
        # 右侧热力图
        self.heatmap = HeatmapWidget()
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.heatmap)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        self.set_central_content(main_widget)
        
        # 默认添加一个灯具
        self.fixtures = [(5.0, 5.0, 10000.0)]
        self._refresh_table()
        self._update_heatmap()
    
    def _calc_single(self):
        intensity = self.intensity_spin.value()
        distance = self.distance_spin.value()
        angle = self.angle_spin.value()
        
        # E = I / d² (反平方定律)
        lux = intensity / (distance * distance)
        
        # 光束锥面积
        half_angle_rad = math.radians(angle / 2)
        beam_radius = distance * math.tan(half_angle_rad)
        beam_area = math.pi * beam_radius ** 2
        avg_lux = (intensity / (distance * distance + 1)) if beam_area > 0 else lux
        
        self.single_result.setText(f"照度: {lux:.1f} lux")
        
        self.result_text.setPlainText(
            f"直射照度: {lux:.1f} lux\n"
            f"光束半径: {beam_radius:.2f} m\n"
            f"光束面积: {beam_area:.2f} m²\n"
            f"平均照度: {intensity / max(beam_area, 0.01):.1f} lux"
        )
        self.logger.info(f"照度: {lux:.1f}lux @ {distance}m")
    
    def _add_fixture(self):
        x = self.fx_spin.value()
        y = self.fy_spin.value()
        intensity = self.fintensity_spin.value()
        self.fixtures.append((x, y, intensity))
        self._refresh_table()
        self._update_heatmap()
        self.logger.info(f"添加灯具: ({x}, {y}) {intensity}cd")
    
    def _clear_fixtures(self):
        self.fixtures.clear()
        self._refresh_table()
        self._update_heatmap()
    
    def _refresh_table(self):
        self.fixture_table.setRowCount(len(self.fixtures))
        for i, (x, y, intensity) in enumerate(self.fixtures):
            self.fixture_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.fixture_table.setItem(i, 1, QTableWidgetItem(f"{x:.1f}"))
            self.fixture_table.setItem(i, 2, QTableWidgetItem(f"{y:.1f}"))
            self.fixture_table.setItem(i, 3, QTableWidgetItem(f"{intensity:.0f}"))
    
    def _update_heatmap(self):
        self.heatmap.update_fixtures(self.fixtures)
        # 计算总照度统计
        if self.fixtures:
            total_intensity = sum(i for _, _, i in self.fixtures)
            avg_dist = 5.0
            avg_lux = total_intensity / (avg_dist * avg_dist)
            self.result_text.setPlainText(
                f"灯具数量: {len(self.fixtures)}\n"
                f"总强度: {total_intensity:.0f} cd\n"
                f"5m处平均照度: {avg_lux:.1f} lux"
            )


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = LuxCalculator()
    window.show()
    sys.exit(app.exec())
