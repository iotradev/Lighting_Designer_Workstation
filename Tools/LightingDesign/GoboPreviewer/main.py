#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GOBO预览器 - 灯具GOBO图案预览与模拟工具"""

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QSlider, QLabel, QPushButton, QColorDialog, QGroupBox, QSpinBox,
    QDoubleSpinBox, QSplitter, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient,
    QPixmap, QImage, QConicalGradient, QPainterPath, QFont
)


# ─── GOBO 图案库 ────────────────────────────────────────────────────────────

def draw_circle_pattern(painter, cx, cy, r):
    """同心圆图案"""
    for i in range(5):
        rr = r * (i + 1) / 5
        painter.drawEllipse(QPointF(cx, cy), rr, rr)


def draw_star_pattern(painter, cx, cy, r):
    """五角星图案"""
    points = []
    for i in range(5):
        angle = math.radians(i * 144 - 90)
        points.append(QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle)))
    from PySide6.QtGui import QPolygonF
    painter.drawPolygon(QPolygonF(points))


def draw_leaves_pattern(painter, cx, cy, r):
    """树叶图案"""
    for i in range(6):
        angle = math.radians(i * 60)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(math.degrees(angle))
        path = QPainterPath()
        path.moveTo(0, 0)
        path.cubicTo(r * 0.3, -r * 0.4, r * 0.7, -r * 0.3, r * 0.8, 0)
        path.cubicTo(r * 0.7, r * 0.3, r * 0.3, r * 0.4, 0, 0)
        painter.drawPath(path)
        painter.restore()


def draw_breakup_pattern(painter, cx, cy, r):
    """碎裂图案"""
    import random
    random.seed(42)
    for _ in range(30):
        x = cx + random.uniform(-r, r)
        y = cy + random.uniform(-r, r)
        if math.hypot(x - cx, y - cy) < r:
            size = random.uniform(r * 0.05, r * 0.2)
            painter.drawEllipse(QPointF(x, y), size, size * 0.7)


def draw_lines_pattern(painter, cx, cy, r):
    """条纹图案"""
    for i in range(8):
        y = cy - r + (2 * r) * (i + 0.5) / 8
        painter.drawLine(QPointF(cx - r, y), QPointF(cx + r, y))


def draw_dots_pattern(painter, cx, cy, r):
    """点阵图案"""
    for row in range(7):
        for col in range(7):
            x = cx - r + (2 * r) * (col + 0.5) / 7
            y = cy - r + (2 * r) * (row + 0.5) / 7
            if math.hypot(x - cx, y - cy) < r * 0.85:
                painter.drawEllipse(QPointF(x, y), r * 0.04, r * 0.04)


def draw_ginkgo_pattern(painter, cx, cy, r):
    """银杏叶图案"""
    for i in range(3):
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(i * 120)
        path = QPainterPath()
        path.moveTo(0, 0)
        path.cubicTo(r * 0.2, -r * 0.5, r * 0.6, -r * 0.6, r * 0.5, -r * 0.9)
        path.cubicTo(r * 0.3, -r * 0.6, -r * 0.1, -r * 0.4, 0, 0)
        painter.drawPath(path)
        painter.restore()


def draw_butterfly_pattern(painter, cx, cy, r):
    """蝴蝶图案"""
    painter.save()
    painter.translate(cx, cy)
    for sign in [-1, 1]:
        path = QPainterPath()
        path.moveTo(0, 0)
        path.cubicTo(sign * r * 0.5, -r * 0.6, sign * r * 0.9, -r * 0.3, sign * r * 0.7, r * 0.1)
        path.cubicTo(sign * r * 0.5, r * 0.4, sign * r * 0.2, r * 0.3, 0, 0)
        painter.drawPath(path)
    painter.restore()


def draw_rosette_pattern(painter, cx, cy, r):
    """玫瑰花窗图案"""
    for i in range(8):
        angle = math.radians(i * 45)
        x1 = cx + r * 0.3 * math.cos(angle)
        y1 = cy + r * 0.3 * math.sin(angle)
        painter.drawEllipse(QPointF(x1, y1), r * 0.35, r * 0.35)


def draw_wave_pattern(painter, cx, cy, r):
    """波浪图案"""
    for i in range(5):
        y = cy - r + (2 * r) * (i + 0.5) / 5
        path = QPainterPath()
        path.moveTo(cx - r, y)
        for x_step in range(20):
            x = cx - r + (2 * r) * x_step / 19
            yy = y + math.sin(x_step * 0.8) * r * 0.1
            path.lineTo(x, yy)
        painter.drawPath(path)


def draw_hexagon_pattern(painter, cx, cy, r):
    """六边形图案"""
    for ring in range(3):
        rr = r * (ring + 1) / 3
        points = []
        for i in range(6):
            angle = math.radians(i * 60 - 30)
            points.append(QPointF(cx + rr * math.cos(angle), cy + rr * math.sin(angle)))
        from PySide6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF(points))


def draw_triangle_pattern(painter, cx, cy, r):
    """三角形图案"""
    for i in range(3):
        angle = math.radians(i * 120 - 90)
        points = []
        for j in range(3):
            a = math.radians(i * 120 - 90 + j * 120)
            points.append(QPointF(cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a)))
        from PySide6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF(points))


def draw_square_pattern(painter, cx, cy, r):
    """方形图案"""
    for i in range(4):
        rr = r * (i + 1) / 4
        painter.drawRect(QRectF(cx - rr, cy - rr, rr * 2, rr * 2))


def draw_cross_pattern(painter, cx, cy, r):
    """十字图案"""
    w = r * 0.2
    painter.drawRect(QRectF(cx - w, cy - r, w * 2, r * 2))
    painter.drawRect(QRectF(cx - r, cy - w, r * 2, w * 2))


def draw_diamond_pattern(painter, cx, cy, r):
    """菱形图案"""
    for i in range(3):
        rr = r * (i + 1) / 3
        from PySide6.QtGui import QPolygonF
        points = [
            QPointF(cx, cy - rr), QPointF(cx + rr, cy),
            QPointF(cx, cy + rr), QPointF(cx - rr, cy)
        ]
        painter.drawPolygon(QPolygonF(points))


def draw_iris_pattern(painter, cx, cy, r):
    """光圈图案"""
    for i in range(6):
        angle = math.radians(i * 60)
        path = QPainterPath()
        x1 = cx + r * 0.3 * math.cos(angle - 0.3)
        y1 = cy + r * 0.3 * math.sin(angle - 0.3)
        x2 = cx + r * math.cos(angle)
        y2 = cy + r * math.sin(angle)
        x3 = cx + r * 0.3 * math.cos(angle + 0.3)
        y3 = cy + r * 0.3 * math.sin(angle + 0.3)
        path.moveTo(x1, y1)
        path.lineTo(x2, y2)
        path.lineTo(x3, y3)
        path.lineTo(cx, cy)
        path.closeSubpath()
        painter.drawPath(path)


def draw_parallel_lines_pattern(painter, cx, cy, r):
    """平行线图案"""
    for i in range(10):
        x = cx - r + (2 * r) * (i + 0.5) / 10
        painter.drawLine(QPointF(x, cy - r), QPointF(x, cy + r))


def draw_concentric_squares_pattern(painter, cx, cy, r):
    """同心方图案"""
    for i in range(5):
        rr = r * (i + 1) / 5
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(45 * i / 5)
        painter.drawRect(QRectF(-rr, -rr, rr * 2, rr * 2))
        painter.restore()


def draw_sunburst_pattern(painter, cx, cy, r):
    """光芒图案"""
    for i in range(12):
        angle = math.radians(i * 30)
        painter.drawLine(
            QPointF(cx + r * 0.2 * math.cos(angle), cy + r * 0.2 * math.sin(angle)),
            QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle))
        )
    painter.drawEllipse(QPointF(cx, cy), r * 0.2, r * 0.2)


def draw_leaf_vein_pattern(painter, cx, cy, r):
    """叶脉图案"""
    # 主脉
    painter.drawLine(QPointF(cx, cy - r * 0.9), QPointF(cx, cy + r * 0.9))
    # 侧脉
    for i in range(6):
        y = cy - r * 0.7 + (2 * r * 0.7) * i / 5
        for sign in [-1, 1]:
            painter.drawLine(QPointF(cx, y), QPointF(cx + sign * r * 0.6, y - r * 0.15))


def draw_cloud_pattern(painter, cx, cy, r):
    """云朵图案"""
    positions = [
        (0, 0, 0.4), (-0.3, -0.15, 0.3), (0.3, -0.15, 0.3),
        (-0.15, -0.3, 0.25), (0.15, -0.3, 0.25),
        (-0.4, 0, 0.2), (0.4, 0, 0.2)
    ]
    for px, py, pr in positions:
        painter.drawEllipse(QPointF(cx + px * r, cy + py * r), r * pr, r * pr * 0.7)


GOBO_LIBRARY = [
    ("同心圆", draw_circle_pattern),
    ("五角星", draw_star_pattern),
    ("树叶", draw_leaves_pattern),
    ("碎裂", draw_breakup_pattern),
    ("条纹", draw_lines_pattern),
    ("点阵", draw_dots_pattern),
    ("银杏叶", draw_ginkgo_pattern),
    ("蝴蝶", draw_butterfly_pattern),
    ("玫瑰花窗", draw_rosette_pattern),
    ("波浪", draw_wave_pattern),
    ("六边形", draw_hexagon_pattern),
    ("三角形", draw_triangle_pattern),
    ("方形", draw_square_pattern),
    ("十字", draw_cross_pattern),
    ("菱形", draw_diamond_pattern),
    ("光圈", draw_iris_pattern),
    ("平行线", draw_parallel_lines_pattern),
    ("同心方", draw_concentric_squares_pattern),
    ("光芒", draw_sunburst_pattern),
    ("叶脉", draw_leaf_vein_pattern),
    ("云朵", draw_cloud_pattern),
]


# ─── GOBO 画布 ──────────────────────────────────────────────────────────────

class GoboCanvas(QWidget):
    """GOBO图案预览画布"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 400)
        self._pattern_func = None
        self._rotation = 0.0
        self._blur_radius = 0.0
        self._color = QColor(255, 255, 255)
        self._bg_color = QColor(0, 0, 0)

    def set_pattern(self, func):
        self._pattern_func = func
        self.update()

    def set_rotation(self, degrees):
        self._rotation = degrees
        self.update()

    def set_blur(self, radius):
        self._blur_radius = radius
        self.update()

    def set_color(self, color):
        self._color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        # 背景
        painter.fillRect(0, 0, w, h, self._bg_color)

        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - 20

        # 圆形投影区域 - 发光边缘
        gradient = QRadialGradient(QPointF(cx, cy), r)
        gradient.setColorAt(0.85, QColor(40, 40, 40))
        gradient.setColorAt(0.95, QColor(20, 20, 20))
        gradient.setColorAt(1.0, QColor(5, 5, 5))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        if self._pattern_func:
            # 模糊效果 - 通过多次绘制偏移实现
            layers = max(1, int(self._blur_radius * 3))
            for layer in range(layers):
                opacity = 1.0 / (layer + 1) if layer > 0 else 1.0
                offset_x = 0
                offset_y = 0
                if layer > 0 and self._blur_radius > 0:
                    import random
                    random.seed(layer * 7)
                    offset_x = random.uniform(-self._blur_radius, self._blur_radius)
                    offset_y = random.uniform(-self._blur_radius, self._blur_radius)

                painter.save()
                painter.setOpacity(opacity)
                painter.setClipPath(self._circle_path(cx, cy, r))

                # 旋转
                painter.translate(cx + offset_x, cy + offset_y)
                painter.rotate(self._rotation)
                painter.translate(-cx - offset_x, -cy - offset_y)

                pen = QPen(self._color, max(1, 2 - self._blur_radius * 0.3))
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                self._pattern_func(painter, cx + offset_x, cy + offset_y, r * 0.85)

                painter.restore()

            # 中心光点
            center_gradient = QRadialGradient(QPointF(cx, cy), r * 0.15)
            center_gradient.setColorAt(0, QColor(255, 255, 255, 60))
            center_gradient.setColorAt(1, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(center_gradient))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(cx, cy), r * 0.15, r * 0.15)

        painter.end()

    def _circle_path(self, cx, cy, r):
        from PySide6.QtGui import QRegion
        from PySide6.QtCore import QPoint
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), r, r)
        return path


# ─── 主窗口 ──────────────────────────────────────────────────────────────────

class GoboPreviewer(BaseToolWindow):
    """GOBO预览器"""

    def __init__(self):
        super().__init__('GoboPreviewer', 'GOBO预览器', '1.0.0', 1000, 750)

        self._rotation_angle = 0.0
        self._rotation_speed = 0.0
        self._color = QColor(255, 255, 255)
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_rotate_tick)
        self._timer.setInterval(33)  # ~30fps

        self._build_ui()
        self._populate_gobo_list()
        self.logger.info("GOBO预览器已初始化")

    def _build_ui(self):
        central = QWidget()
        self.set_central_content(central)
        main_layout = QHBoxLayout(central)

        # 左侧控制面板
        left_panel = QWidget()
        left_panel.setMaximumWidth(280)
        left_layout = QVBoxLayout(left_panel)

        # GOBO选择器
        gobo_group = QGroupBox("GOBO图案库")
        gobo_layout = QVBoxLayout(gobo_group)
        self._gobo_list = QListWidget()
        self._gobo_list.currentRowChanged.connect(self._on_gobo_selected)
        gobo_layout.addWidget(self._gobo_list)
        left_layout.addWidget(gobo_group)

        # 旋转控制
        rotate_group = QGroupBox("旋转控制")
        rotate_layout = QVBoxLayout(rotate_group)

        speed_label = QLabel("旋转速度 (°/帧):")
        rotate_layout.addWidget(speed_label)
        self._speed_slider = QSlider(Qt.Horizontal)
        self._speed_slider.setRange(-200, 200)
        self._speed_slider.setValue(0)
        self._speed_slider.valueChanged.connect(self._on_speed_changed)
        rotate_layout.addWidget(self._speed_slider)
        self._speed_value_label = QLabel("速度: 0 °/帧")
        rotate_layout.addWidget(self._speed_value_label)

        angle_label = QLabel("手动角度:")
        rotate_layout.addWidget(angle_label)
        self._angle_slider = QSlider(Qt.Horizontal)
        self._angle_slider.setRange(0, 3600)
        self._angle_slider.setValue(0)
        self._angle_slider.valueChanged.connect(self._on_angle_changed)
        rotate_layout.addWidget(self._angle_slider)
        self._angle_value_label = QLabel("角度: 0.0°")
        rotate_layout.addWidget(self._angle_value_label)

        left_layout.addWidget(rotate_group)

        # 模糊控制
        blur_group = QGroupBox("聚焦模糊")
        blur_layout = QVBoxLayout(blur_group)
        self._blur_slider = QSlider(Qt.Horizontal)
        self._blur_slider.setRange(0, 100)
        self._blur_slider.setValue(0)
        self._blur_slider.valueChanged.connect(self._on_blur_changed)
        blur_layout.addWidget(self._blur_slider)
        self._blur_label = QLabel("模糊量: 0")
        blur_layout.addWidget(self._blur_label)
        left_layout.addWidget(blur_group)

        # 颜色控制
        color_group = QGroupBox("颜色叠加")
        color_layout = QVBoxLayout(color_group)
        self._color_btn = QPushButton("选择颜色")
        self._color_btn.clicked.connect(self._on_color_pick)
        color_layout.addWidget(self._color_btn)
        self._color_preview = QFrame()
        self._color_preview.setFixedSize(60, 30)
        self._color_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid #666;")
        color_layout.addWidget(self._color_preview)
        left_layout.addWidget(color_group)

        left_layout.addStretch()
        main_layout.addWidget(left_panel)

        # 右侧预览画布
        self._canvas = GoboCanvas()
        main_layout.addWidget(self._canvas, 1)

    def _populate_gobo_list(self):
        for name, _ in GOBO_LIBRARY:
            self._gobo_list.addItem(name)
        self._gobo_list.setCurrentRow(0)

    def _on_gobo_selected(self, row):
        if 0 <= row < len(GOBO_LIBRARY):
            _, func = GOBO_LIBRARY[row]
            self._canvas.set_pattern(func)
            self.logger.info(f"选择GOBO: {GOBO_LIBRARY[row][0]}")

    def _on_speed_changed(self, value):
        self._rotation_speed = value / 10.0
        self._speed_value_label.setText(f"速度: {self._rotation_speed:.1f} °/帧")
        if abs(self._rotation_speed) > 0.01:
            if not self._timer.isActive():
                self._timer.start()
        else:
            self._timer.stop()

    def _on_angle_changed(self, value):
        self._rotation_angle = value / 10.0
        self._canvas.set_rotation(self._rotation_angle)
        self._angle_value_label.setText(f"角度: {self._rotation_angle:.1f}°")

    def _on_blur_changed(self, value):
        self._canvas.set_blur(value / 10.0)
        self._blur_label.setText(f"模糊量: {value}")

    def _on_color_pick(self):
        color = QColorDialog.getColor(self._color, self, "选择GOBO颜色")
        if color.isValid():
            self._color = color
            self._canvas.set_color(color)
            self._color_preview.setStyleSheet(
                f"background-color: {color.name()}; border: 1px solid #666;"
            )

    def _on_rotate_tick(self):
        self._rotation_angle = (self._rotation_angle + self._rotation_speed) % 360
        self._canvas.set_rotation(self._rotation_angle)
        self._angle_slider.blockSignals(True)
        self._angle_slider.setValue(int(self._rotation_angle * 10))
        self._angle_slider.blockSignals(False)
        self._angle_value_label.setText(f"角度: {self._rotation_angle:.1f}°")

    def closeEvent(self, event):
        """关闭窗口时停止旋转定时器"""
        self._timer.stop()
        super().closeEvent(event)


# ─── 入口 ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = GoboPreviewer()
    window.show()
    sys.exit(app.exec())
