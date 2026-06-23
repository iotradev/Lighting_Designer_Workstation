"""
光束计算器 (BeamCalculator)
照明设计光束参数计算器 - 计算光束角度、覆盖面积、投射距离
"""
import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QTabWidget, QComboBox,
    QDoubleSpinBox, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPolygonF, QBrush
from ui.base_window import BaseToolWindow


class BeamDiagramWidget(QWidget):
    """光束可视化图"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.beam_angle = 30.0
        self.distance = 10.0
        self.fixture_height = 5.0
        self.setMinimumSize(400, 300)
    
    def update_diagram(self, angle, distance, height):
        self.beam_angle = angle
        self.distance = distance
        self.fixture_height = height
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # 背景
        painter.fillRect(0, 0, w, h, QColor(30, 30, 30))
        
        # 绘制区域
        margin = 60
        draw_w = w - 2 * margin
        draw_h = h - 2 * margin
        
        # 灯具位置 (顶部居中)
        fixture_x = margin + draw_w // 2
        fixture_y = margin
        
        # 计算光束在目标处的宽度
        half_angle_rad = math.radians(self.beam_angle / 2)
        beam_radius = self.distance * math.tan(half_angle_rad)
        
        # 比例尺：将距离映射到绘图高度
        total_distance = self.distance if self.distance > 0 else 10
        scale_y = draw_h / total_distance
        
        # 目标位置 y
        target_y = fixture_y + self.distance * scale_y
        
        # 光束宽度在绘图坐标中
        beam_pixel_radius = beam_radius * scale_y
        left_x = fixture_x - beam_pixel_radius
        right_x = fixture_x + beam_pixel_radius
        
        # 绘制光束锥形（半透明）
        beam_color = QColor(255, 200, 50, 60)
        brush = QBrush(beam_color)
        painter.setBrush(brush)
        painter.setPen(QPen(QColor(255, 200, 50, 150), 2))
        
        beam_polygon = QPolygonF([
            QPointF(fixture_x, fixture_y),
            QPointF(left_x, target_y),
            QPointF(right_x, target_y)
        ])
        painter.drawPolygon(beam_polygon)
        
        # 绘制地面线
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawLine(int(margin), int(target_y), int(w - margin), int(target_y))
        
        # 绘制光束中心线
        painter.setPen(QPen(QColor(255, 255, 100, 100), 1, Qt.PenStyle.DashLine))
        painter.drawLine(int(fixture_x), int(fixture_y), int(fixture_x), int(target_y))
        
        # 绘制灯具图标
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawRect(int(fixture_x - 15), int(fixture_y - 10), 30, 20)
        
        # 标注
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        
        # 距离标注
        painter.drawText(int(fixture_x + 5), int((fixture_y + target_y) / 2),
                        f"距离: {self.distance:.1f}m")
        
        # 角度标注
        painter.drawText(int(fixture_x + 10), int(fixture_y + 25),
                        f"角度: {self.beam_angle:.1f}°")
        
        # 覆盖宽度标注
        painter.drawText(int(fixture_x - beam_pixel_radius), int(target_y + 15),
                        f"覆盖宽度: {beam_radius * 2:.2f}m")
        
        painter.end()


class BeamCalculator(BaseToolWindow):
    def __init__(self):
        super().__init__('BeamCalculator', '光束计算器', '1.0.0', 1000, 700)
        self._setup_ui()
        self._calculate()
    
    def _setup_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 标签页
        tabs = QTabWidget()
        tabs.addTab(self._create_angle_tab(), "光束角度")
        tabs.addTab(self._create_coverage_tab(), "覆盖计算")
        tabs.addTab(self._create_distance_tab(), "距离计算")
        left_layout.addWidget(tabs)
        
        # 结果显示
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout(result_group)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(200)
        result_layout.addWidget(self.result_text)
        left_layout.addWidget(result_group)
        
        # 右侧光束图
        self.diagram = BeamDiagramWidget()
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(self.diagram)
        splitter.setSizes([400, 600])
        
        main_layout.addWidget(splitter)
        self.set_central_content(main_widget)
    
    def _create_angle_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        
        layout.addWidget(QLabel("透镜直径 (mm, 仅供参考):"), 0, 0)
        self.lens_diameter = QDoubleSpinBox()
        self.lens_diameter.setRange(1, 500)
        self.lens_diameter.setValue(150)
        self.lens_diameter.setToolTip("透镜直径仅用于显示参考，不参与角度计算")
        layout.addWidget(self.lens_diameter, 0, 1)
        
        layout.addWidget(QLabel("投射距离 (m):"), 1, 0)
        self.angle_distance = QDoubleSpinBox()
        self.angle_distance.setRange(0.1, 500)
        self.angle_distance.setValue(10)
        layout.addWidget(self.angle_distance, 1, 1)
        
        layout.addWidget(QLabel("光束直径 (m):"), 2, 0)
        self.beam_diameter = QDoubleSpinBox()
        self.beam_diameter.setRange(0.01, 1000)
        self.beam_diameter.setValue(5)
        layout.addWidget(self.beam_diameter, 2, 1)
        
        btn = QPushButton("计算光束角度")
        btn.clicked.connect(self._calc_angle)
        layout.addWidget(btn, 3, 0, 1, 2)
        
        return widget
    
    def _create_coverage_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        
        layout.addWidget(QLabel("光束角度 (°):"), 0, 0)
        self.cov_angle = QDoubleSpinBox()
        self.cov_angle.setRange(1, 180)
        self.cov_angle.setValue(30)
        layout.addWidget(self.cov_angle, 0, 1)
        
        layout.addWidget(QLabel("投射距离 (m):"), 1, 0)
        self.cov_distance = QDoubleSpinBox()
        self.cov_distance.setRange(0.1, 500)
        self.cov_distance.setValue(10)
        layout.addWidget(self.cov_distance, 1, 1)
        
        btn = QPushButton("计算覆盖面积")
        btn.clicked.connect(self._calc_coverage)
        layout.addWidget(btn, 2, 0, 1, 2)
        
        return widget
    
    def _create_distance_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        
        layout.addWidget(QLabel("光束角度 (°):"), 0, 0)
        self.dist_angle = QDoubleSpinBox()
        self.dist_angle.setRange(1, 180)
        self.dist_angle.setValue(30)
        layout.addWidget(self.dist_angle, 0, 1)
        
        layout.addWidget(QLabel("所需覆盖宽度 (m):"), 1, 0)
        self.desired_width = QDoubleSpinBox()
        self.desired_width.setRange(0.1, 1000)
        self.desired_width.setValue(5)
        layout.addWidget(self.desired_width, 1, 1)
        
        layout.addWidget(QLabel("灯具高度 (m):"), 2, 0)
        self.fixture_height = QDoubleSpinBox()
        self.fixture_height.setRange(0.5, 50)
        self.fixture_height.setValue(5)
        layout.addWidget(self.fixture_height, 2, 1)
        
        btn = QPushButton("计算投射距离")
        btn.clicked.connect(self._calc_distance)
        layout.addWidget(btn, 3, 0, 1, 2)
        
        return widget
    
    def _calc_angle(self):
        lens_mm = self.lens_diameter.value()
        distance_m = self.angle_distance.value()
        beam_d = self.beam_diameter.value()
        
        # 角度 = 2 * atan(beam_radius / distance)
        angle = 2 * math.degrees(math.atan(beam_d / 2 / distance_m))
        
        self.result_text.setPlainText(
            f"=== 光束角度计算 ===\n"
            f"透镜直径: {lens_mm:.1f} mm\n"
            f"投射距离: {distance_m:.2f} m\n"
            f"光束直径: {beam_d:.2f} m\n"
            f"光束角度: {angle:.2f}°"
        )
        
        self.diagram.update_diagram(angle, distance_m, self.fixture_height.value())
        self.logger.info(f"计算光束角度: {angle:.2f}°")
    
    def _calc_coverage(self):
        angle = self.cov_angle.value()
        distance = self.cov_distance.value()
        
        half_angle_rad = math.radians(angle / 2)
        beam_radius = distance * math.tan(half_angle_rad)
        beam_width = beam_radius * 2
        # 覆盖面积（圆形近似）
        area = math.pi * beam_radius ** 2
        # 椭圆近似的深度
        depth = beam_width * 0.85
        
        self.result_text.setPlainText(
            f"=== 覆盖面积计算 ===\n"
            f"光束角度: {angle:.2f}°\n"
            f"投射距离: {distance:.2f} m\n"
            f"覆盖宽度: {beam_width:.2f} m\n"
            f"覆盖深度: {depth:.2f} m\n"
            f"光束直径: {beam_width:.2f} m\n"
            f"覆盖面积: {area:.2f} m²"
        )
        
        self.diagram.update_diagram(angle, distance, self.fixture_height.value())
        self.logger.info(f"覆盖宽度: {beam_width:.2f}m, 面积: {area:.2f}m2")
    
    def _calc_distance(self):
        angle = self.dist_angle.value()
        desired_w = self.desired_width.value()
        height = self.fixture_height.value()
        
        half_angle_rad = math.radians(angle / 2)
        # distance = (desired_width / 2) / tan(half_angle)
        distance = (desired_w / 2) / math.tan(half_angle_rad)
        
        actual_radius = distance * math.tan(half_angle_rad)
        actual_width = actual_radius * 2
        
        self.result_text.setPlainText(
            f"=== 投射距离计算 ===\n"
            f"光束角度: {angle:.2f}°\n"
            f"所需覆盖宽度: {desired_w:.2f} m\n"
            f"灯具高度: {height:.2f} m\n"
            f"所需投射距离: {distance:.2f} m\n"
            f"实际覆盖宽度: {actual_width:.2f} m\n"
            f"光束直径: {actual_width:.2f} m"
        )
        
        self.diagram.update_diagram(angle, distance, height)
        self.logger.info(f"投射距离: {distance:.2f}m")
    
    def _calculate(self):
        """默认计算"""
        self._calc_coverage()


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = BeamCalculator()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "BeamCalculator - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
