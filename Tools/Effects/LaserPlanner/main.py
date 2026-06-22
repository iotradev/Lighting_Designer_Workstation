# -*- coding: utf-8 -*-
"""激光规划器 - LaserPlanner"""
import sys, csv, math
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QCheckBox, QTabWidget,
    QListWidgetItem, QToolBar
)
from PySide6.QtCore import Qt, QPointF, QRectF, QSizeF, QTimer
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPolygonF,
    QMouseEvent, QPaintEvent, QWheelEvent, QAction, QKeySequence
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow


class ZoneType(Enum):
    RECTANGLE = "矩形"
    CIRCLE = "圆形"


@dataclass
class LaserZone:
    name: str
    zone_type: ZoneType
    x: float
    y: float
    width: float  # or radius for circle
    height: float  # same as width for circle
    color: QColor = field(default_factory=lambda: QColor(0, 255, 0, 80))
    power_mw: float = 50.0  # laser power in mW
    wavelength_nm: int = 532  # nm


@dataclass
class AudienceZone:
    name: str
    x: float
    y: float
    width: float
    height: float


@dataclass
class LaserSource:
    name: str
    x: float
    y: float
    target_x: float = 0.0
    target_y: float = 0.0
    power_mw: float = 100.0
    wavelength_nm: int = 532
    beam_divergence_mrad: float = 1.5  # mrad


class StageCanvas(QWidget):
    """舞台布局画布"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.laser_zones: list[LaserZone] = []
        self.audience_zones: list[AudienceZone] = []
        self.laser_sources: list[LaserSource] = []
        self.drawing = False
        self.draw_type = "rectangle"
        self.start_pos: Optional[QPointF] = None
        self.current_pos: Optional[QPointF] = None
        self.selected_zone_idx = -1
        self.show_beams = True
        self.show_safety = True
        self.mpe_distance = 3.0  # meters - MPE safety distance
        self.scale = 50.0  # pixels per meter
        self.pan_offset = QPointF(0, 0)
        self.overlap_pairs: list[tuple[int, int]] = []
        self._dragging = False
        self._last_mouse: Optional[QPointF] = None

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(30, 30, 40))

        # Grid
        painter.setPen(QPen(QColor(60, 60, 80), 1))
        gs = int(self.scale)
        ox = int(self.pan_offset.x()) % gs
        oy = int(self.pan_offset.y()) % gs
        for x in range(ox, w, gs):
            painter.drawLine(x, 0, x, h)
        for y in range(oy, h, gs):
            painter.drawLine(0, y, w, y)

        # Stage outline
        stage_pen = QPen(QColor(180, 180, 180), 2)
        painter.setPen(stage_pen)
        painter.setBrush(QBrush(QColor(50, 50, 60)))
        sx = 50 + self.pan_offset.x()
        sy = 50 + self.pan_offset.y()
        painter.drawRect(int(sx), int(sy), int(w - 100), int(h * 0.4))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.drawText(int(sx + 10), int(sy + 20), "舞台区域")

        # Audience area
        painter.setPen(QPen(QColor(100, 100, 150), 2, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(40, 40, 55)))
        ay = sy + h * 0.45
        painter.drawRect(int(sx), int(ay), int(w - 100), int(h * 0.35))
        painter.setPen(QPen(QColor(150, 150, 200), 1))
        painter.drawText(int(sx + 10), int(ay + 20), "观众区域")

        # Audience exclusion zones
        for az in self.audience_zones:
            painter.setPen(QPen(QColor(255, 100, 100, 200), 2, Qt.PenStyle.DashDotLine))
            painter.setBrush(QBrush(QColor(255, 0, 0, 40)))
            ax = sx + az.x * self.scale
            ay2 = sy + az.y * self.scale
            painter.drawRect(int(ax), int(ay2),
                           int(az.width * self.scale), int(az.height * self.scale))
            painter.setPen(QPen(QColor(255, 150, 150), 1))
            painter.drawText(int(ax + 4), int(ay2 + 14), az.name)

        # Laser zones
        for i, z in enumerate(self.laser_zones):
            col = z.color
            # Overlap highlight
            is_overlap = any(i in p for p in self.overlap_pairs)
            pen_col = QColor(255, 50, 50, 200) if is_overlap else QColor(col.red(), col.green(), col.blue(), 180)
            painter.setPen(QPen(pen_col, 2))
            painter.setBrush(QBrush(col))
            zx = sx + z.x * self.scale
            zy = sy + z.y * self.scale
            if z.zone_type == ZoneType.RECTANGLE:
                painter.drawRect(int(zx), int(zy),
                               int(z.width * self.scale), int(z.height * self.scale))
            else:
                painter.drawEllipse(QPointF(zx + z.width * self.scale / 2,
                                           zy + z.width * self.scale / 2),
                                   z.width * self.scale / 2, z.width * self.scale / 2)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(int(zx + 4), int(zy + 14), z.name)

        # Safety zones (MPE circles) around sources
        if self.show_safety:
            for src in self.laser_sources:
                mpe_px = self.mpe_distance * self.scale
                src_px = QPointF(sx + src.x * self.scale, sy + src.y * self.scale)
                painter.setPen(QPen(QColor(255, 200, 0, 120), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(255, 200, 0, 20)))
                painter.drawEllipse(src_px, mpe_px, mpe_px)
                painter.setPen(QPen(QColor(255, 200, 0, 180), 1))
                painter.drawText(int(src_px.x() + mpe_px + 4), int(src_px.y()), f"MPE {self.mpe_distance}m")

        # Laser beams
        if self.show_beams:
            for src in self.laser_sources:
                sp = QPointF(sx + src.x * self.scale, sy + src.y * self.scale)
                tp = QPointF(sx + src.target_x * self.scale, sy + src.target_y * self.scale)
                beam_col = QColor(0, 255, 100, 200) if src.wavelength_nm == 532 else QColor(200, 0, 255, 200)
                painter.setPen(QPen(beam_col, 2))
                painter.drawLine(sp, tp)
                # Source dot
                painter.setPen(QPen(QColor(255, 255, 0), 2))
                painter.setBrush(QBrush(QColor(255, 255, 0)))
                painter.drawEllipse(sp, 5, 5)
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.drawText(int(sp.x() + 8), int(sp.y() - 8), src.name)

        # Drawing preview
        if self.drawing and self.start_pos and self.current_pos:
            painter.setPen(QPen(QColor(255, 255, 255, 150), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(100, 200, 255, 40)))
            r = QRectF(self.start_pos, self.current_pos).normalized()
            if self.draw_type == "rectangle":
                painter.drawRect(r)
            else:
                center = r.center()
                rad = max(r.width(), r.height()) / 2
                painter.drawEllipse(center, rad, rad)

        # Legend
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Microsoft YaHei", 9))
        lx, ly = 10, h - 70
        painter.drawText(lx, ly, "🟢 激光光束")
        painter.drawText(lx, ly + 15, "🟡 MPE安全距离")
        painter.drawText(lx, ly + 30, "🔴 观众排除区")
        painter.drawText(lx, ly + 45, "🟠 重叠警告")

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing:
                self.start_pos = event.position()
                self.current_pos = event.position()
            else:
                self._dragging = True
                self._last_mouse = event.position()
        elif event.button() == Qt.MouseButton.RightButton:
            self.drawing = False
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.drawing and self.start_pos:
            self.current_pos = event.position()
            self.update()
        elif self._dragging and self._last_mouse:
            delta = event.position() - self._last_mouse
            self.pan_offset += QPointF(delta.x(), delta.y())
            self._last_mouse = event.position()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drawing and self.start_pos and self.current_pos:
                r = QRectF(self.start_pos, self.current_pos).normalized()
                sx = 50 + self.pan_offset.x()
                sy = 50 + self.pan_offset.y()
                zx = (r.x() - sx) / self.scale
                zy = (r.y() - sy) / self.scale
                zw = r.width() / self.scale
                zh = r.height() / self.scale
                if zw > 0.1 and zh > 0.1:
                    self._add_zone_callback(zx, zy, zw, zh)
                self.drawing = False
                self.start_pos = None
                self.current_pos = None
                self.update()
            self._dragging = False
            self._last_mouse = None

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale = min(200, self.scale * 1.1)
        else:
            self.scale = max(10, self.scale / 1.1)
        self.update()

    def _add_zone_callback(self, x, y, w, h):
        """Overridden by parent"""
        pass

    def check_overlaps(self):
        self.overlap_pairs.clear()
        for i in range(len(self.laser_zones)):
            for j in range(i + 1, len(self.laser_zones)):
                if self._zones_overlap(self.laser_zones[i], self.laser_zones[j]):
                    self.overlap_pairs.append((i, j))
        self.update()

    def _zones_overlap(self, a: LaserZone, b: LaserZone) -> bool:
        if a.zone_type == ZoneType.RECTANGLE and b.zone_type == ZoneType.RECTANGLE:
            return not (a.x + a.width < b.x or b.x + b.width < a.x or
                       a.y + a.height < b.y or b.y + b.height < a.y)
        # Simplified circle-rect / circle-circle check
        cx_a = a.x + a.width / 2 if a.zone_type == ZoneType.RECTANGLE else a.x
        cy_a = a.y + a.height / 2 if a.zone_type == ZoneType.RECTANGLE else a.y
        cx_b = b.x + b.width / 2 if b.zone_type == ZoneType.RECTANGLE else b.x
        cy_b = b.y + b.height / 2 if b.zone_type == ZoneType.RECTANGLE else b.y
        r_a = max(a.width, a.height) / 2
        r_b = max(b.width, b.height) / 2
        dist = math.hypot(cx_a - cx_b, cy_a - cy_b)
        return dist < r_a + r_b


class LaserPlannerWindow(BaseToolWindow):
    """激光规划器主窗口"""

    def __init__(self):
        super().__init__('LaserPlanner', '激光规划器', '1.0.0', 1100, 800)

        # Add toolbar buttons
        self.toolbar.addSeparator()
        self.toolbar.addAction("🔍 重叠检测", self._check_overlaps)
        self.toolbar.addAction("📊 导出报告", self._export_csv)
        self.toolbar.addAction("🔆 显示光束", self._toggle_beams)

        # Build central widget
        central = QWidget()
        main_layout = QHBoxLayout(central)

        # Left: canvas
        self.canvas = StageCanvas()
        self.canvas._add_zone_callback = self._on_zone_drawn

        # Right: controls
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_panel.setMaximumWidth(320)

        # Zone creation
        zone_group = QGroupBox("创建区域")
        zone_form = QFormLayout(zone_group)
        self.draw_type_combo = QComboBox()
        self.draw_type_combo.addItems(["矩形", "圆形"])
        zone_form.addRow("区域类型:", self.draw_type_combo)
        self.zone_name_edit = QLabel("区域_1")
        zone_form.addRow("名称:", self.zone_name_edit)
        self.btn_start_draw = QPushButton("开始绘制")
        self.btn_start_draw.clicked.connect(self._start_drawing)
        zone_form.addRow(self.btn_start_draw)
        right_layout.addWidget(zone_group)

        # Laser source
        src_group = QGroupBox("激光光源")
        src_form = QFormLayout(src_group)
        self.src_name = QLabel("激光_1")
        src_form.addRow("名称:", self.src_name)
        self.src_power = QDoubleSpinBox()
        self.src_power.setRange(1, 10000)
        self.src_power.setValue(100)
        self.src_power.setSuffix(" mW")
        src_form.addRow("功率:", self.src_power)
        self.src_wavelength = QComboBox()
        self.src_wavelength.addItems(["532nm (绿)", "445nm (蓝)", "638nm (红)", "405nm (紫)"])
        src_form.addRow("波长:", self.src_wavelength)
        self.src_x = QDoubleSpinBox()
        self.src_x.setRange(0, 100)
        self.src_x.setValue(5)
        src_form.addRow("X位置(m):", self.src_x)
        self.src_y = QDoubleSpinBox()
        self.src_y.setRange(0, 100)
        self.src_y.setValue(2)
        src_form.addRow("Y位置(m):", self.src_y)
        self.src_tx = QDoubleSpinBox()
        self.src_tx.setRange(0, 100)
        self.src_tx.setValue(10)
        src_form.addRow("目标X(m):", self.src_tx)
        self.src_ty = QDoubleSpinBox()
        self.src_ty.setRange(0, 100)
        self.src_ty.setValue(8)
        src_form.addRow("目标Y(m):", self.src_ty)
        btn_add_src = QPushButton("添加光源")
        btn_add_src.clicked.connect(self._add_source)
        src_form.addRow(btn_add_src)
        right_layout.addWidget(src_group)

        # Safety settings
        safety_group = QGroupBox("安全设置")
        safety_form = QFormLayout(safety_group)
        self.mpe_distance = QDoubleSpinBox()
        self.mpe_distance.setRange(0.5, 50)
        self.mpe_distance.setValue(3.0)
        self.mpe_distance.setSuffix(" m")
        self.mpe_distance.valueChanged.connect(self._update_mpe)
        safety_form.addRow("MPE距离:", self.mpe_distance)
        self.show_safety_check = QCheckBox("显示安全区域")
        self.show_safety_check.setChecked(True)
        self.show_safety_check.toggled.connect(self._toggle_safety)
        safety_form.addRow(self.show_safety_check)
        right_layout.addWidget(safety_group)

        # Zone list
        zone_list_group = QGroupBox("区域列表")
        zl = QVBoxLayout(zone_list_group)
        self.zone_list = QListWidget()
        zl.addWidget(self.zone_list)
        btn_row = QHBoxLayout()
        btn_del = QPushButton("删除选中")
        btn_del.clicked.connect(self._delete_zone)
        btn_row.addWidget(btn_del)
        btn_clear = QPushButton("清除全部")
        btn_clear.clicked.connect(self._clear_all)
        btn_row.addWidget(btn_clear)
        zl.addLayout(btn_row)
        right_layout.addWidget(zone_list_group)

        # Warnings
        warn_group = QGroupBox("⚠️ 警告")
        wl = QVBoxLayout(warn_group)
        self.warn_label = QLabel("无警告")
        self.warn_label.setWordWrap(True)
        wl.addWidget(self.warn_label)
        right_layout.addWidget(warn_group)

        right_layout.addStretch()

        main_layout.addWidget(self.canvas, 1)
        main_layout.addWidget(right_panel)

        self.set_central_content(central)
        self._zone_counter = 1
        self._source_counter = 1
        self.logger.info("激光规划器已就绪")

    def _start_drawing(self):
        dt = self.draw_type_combo.currentText()
        self.canvas.draw_type = "circle" if dt == "圆形" else "rectangle"
        self.canvas.drawing = True
        self.status_ready.setText("在画布上拖拽绘制区域...")

    def _on_zone_drawn(self, x, y, w, h):
        zt = ZoneType.CIRCLE if self.canvas.draw_type == "circle" else ZoneType.RECTANGLE
        name = f"区域_{self._zone_counter}"
        self._zone_counter += 1
        color = QColor(0, 255, 0, 80) if zt == ZoneType.RECTANGLE else QColor(0, 150, 255, 80)
        zone = LaserZone(name=name, zone_type=zt, x=x, y=y, width=w, height=h, color=color)
        self.canvas.laser_zones.append(zone)
        self.zone_list.addItem(f"{name} ({zt.value}) [{x:.1f},{y:.1f}]")
        self.canvas.check_overlaps()
        self._update_warnings()
        self.logger.info(f"创建区域: {name}")

    def _add_source(self):
        name = f"激光_{self._source_counter}"
        self._source_counter += 1
        wl_text = self.src_wavelength.currentText()
        wl = int(wl_text.split("nm")[0])
        src = LaserSource(
            name=name,
            x=self.src_x.value(), y=self.src_y.value(),
            target_x=self.src_tx.value(), target_y=self.src_ty.value(),
            power_mw=self.src_power.value(),
            wavelength_nm=wl
        )
        self.canvas.laser_sources.append(src)
        self.zone_list.addItem(f"🔦 {name} ({wl}nm, {src.power_mw}mW)")
        self.canvas.update()
        self.logger.info(f"添加光源: {name}")

    def _delete_zone(self):
        row = self.zone_list.currentRow()
        if row < 0:
            return
        if row < len(self.canvas.laser_zones):
            self.canvas.laser_zones.pop(row)
        elif row < len(self.canvas.laser_zones) + len(self.canvas.audience_zones):
            self.canvas.audience_zones.pop(row - len(self.canvas.laser_zones))
        else:
            si = row - len(self.canvas.laser_zones) - len(self.canvas.audience_zones)
            if si < len(self.canvas.laser_sources):
                self.canvas.laser_sources.pop(si)
        self.zone_list.takeItem(row)
        self.canvas.check_overlaps()
        self._update_warnings()

    def _clear_all(self):
        self.canvas.laser_zones.clear()
        self.canvas.audience_zones.clear()
        self.canvas.laser_sources.clear()
        self.canvas.overlap_pairs.clear()
        self.zone_list.clear()
        self.warn_label.setText("无警告")
        self.canvas.update()

    def _check_overlaps(self):
        self.canvas.check_overlaps()
        self._update_warnings()

    def _update_warnings(self):
        warnings = []
        if self.canvas.overlap_pairs:
            for i, j in self.canvas.overlap_pairs:
                a = self.canvas.laser_zones[i]
                b = self.canvas.laser_zones[j]
                warnings.append(f"⚠️ {a.name} 与 {b.name} 重叠")
        if not warnings:
            self.warn_label.setText("✅ 无重叠警告")
        else:
            self.warn_label.setText("\n".join(warnings))
        self.canvas.update()

    def _update_mpe(self, val):
        self.canvas.mpe_distance = val
        self.canvas.update()

    def _toggle_safety(self, checked):
        self.canvas.show_safety = checked
        self.canvas.update()

    def _toggle_beams(self):
        self.canvas.show_beams = not self.canvas.show_beams
        self.canvas.update()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出安全报告", "", "CSV文件 (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["类型", "名称", "X(m)", "Y(m)", "宽度/半径(m)", "高度(m)",
                                "功率(mW)", "波长(nm)", "安全距离(m)", "重叠警告"])
                for i, z in enumerate(self.canvas.laser_zones):
                    overlap = "是" if any(i in p for p in self.canvas.overlap_pairs) else "否"
                    writer.writerow(["激光区域", z.name, f"{z.x:.2f}", f"{z.y:.2f}",
                                   f"{z.width:.2f}", f"{z.height:.2f}",
                                   z.power_mw, z.wavelength_nm,
                                   f"{self.canvas.mpe_distance:.1f}", overlap])
                for src in self.canvas.laser_sources:
                    writer.writerow(["激光光源", src.name, f"{src.x:.2f}", f"{src.y:.2f}",
                                   f"{src.target_x:.2f}", f"{src.target_y:.2f}",
                                   src.power_mw, src.wavelength_nm,
                                   f"{self.canvas.mpe_distance:.1f}", ""])
                writer.writerow([])
                writer.writerow(["=== 安全报告摘要 ==="])
                writer.writerow(["区域总数", len(self.canvas.laser_zones)])
                writer.writerow(["光源总数", len(self.canvas.laser_sources)])
                writer.writerow(["重叠区域数", len(self.canvas.overlap_pairs)])
                writer.writerow(["MPE安全距离", f"{self.canvas.mpe_distance} m"])
            self.logger.info(f"安全报告已导出: {path}")
            QMessageBox.information(self, "导出成功", f"安全报告已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    # Override menu actions
    def _show_shortcuts(self):
        text = """<table>
        <tr><td><b>绘制</b></td><td>选择类型后点击"开始绘制"，在画布拖拽</td></tr>
        <tr><td><b>右键</b></td><td>取消绘制</td></tr>
        <tr><td><b>滚轮</b></td><td>缩放画布</td></tr>
        <tr><td><b>左键拖拽</b></td><td>平移画布（非绘制模式）</td></tr>
        </table>"""
        QMessageBox.information(self, "操作说明", text)


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = LaserPlannerWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "LaserPlanner - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
