# -*- coding: utf-8 -*-
"""
视觉模拟器 - 3D 舞台灯光预览工具
支持俯视/侧视/等轴测视图，光束模拟，雾气效果
"""
import sys, json, math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSlider, QSpinBox, QColorDialog,
    QGroupBox, QSplitter, QToolBar, QFileDialog, QMessageBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QPolygonF, QFont,
    QLinearGradient, QRadialGradient, QAction, QMouseEvent,
    QWheelEvent, QPaintEvent, QResizeEvent
)

from simulator_engine import (
    StageModel, Fixture, Truss, CoordinateTransform,
    create_default_stage
)


# ── 3D 画布 ───────────────────────────────────────────────────────────────

class StageCanvas(QWidget):
    """3D 舞台画布 - 使用 QPainter 绘制等轴测/俯视/侧视图"""

    fixture_clicked = object  # Signal-like: index or -1
    VIEW_TOP = 0
    VIEW_SIDE = 1
    VIEW_ISO = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = StageModel()
        self.ct = CoordinateTransform()
        self.view_mode = self.VIEW_ISO
        self.show_grid = True
        self.show_beams = True
        self.show_fog = True
        self._dragging = False
        self._last_pos = QPointF()
        self._drag_fixture_idx = -1
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self._clicked_index = -1

    def set_stage(self, stage: StageModel):
        self.stage = stage
        self.update()

    def set_view_mode(self, mode: int):
        self.view_mode = mode
        self._center_view()
        self.update()

    def _center_view(self):
        w, h = self.width(), self.height()
        self.ct.offset_x = w / 2
        self.ct.offset_y = h / 2

    def _w2s(self, x, y, z=0) -> QPointF:
        if self.view_mode == self.VIEW_TOP:
            return self.ct.world_to_screen_top(x, y, z)
        elif self.view_mode == self.VIEW_SIDE:
            return self.ct.world_to_screen_side(x, y, z)
        else:
            return self.ct.world_to_screen_iso(x, y, z)

    # ── 绘制 ──

    def paintEvent(self, event: QPaintEvent):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 背景
        p.fillRect(self.rect(), QColor(20, 20, 28))

        if self.show_grid:
            self._draw_grid(p)

        self._draw_stage_floor(p)
        self._draw_trusses(p)

        if self.show_beams:
            self._draw_beams(p)

        self._draw_fixtures(p)
        self._draw_labels(p)

        # HUD
        self._draw_hud(p)
        p.end()

    def _draw_grid(self, p: QPainter):
        pen = QPen(QColor(50, 50, 60), 1, Qt.DotLine)
        p.setPen(pen)
        step = self.ct.zoom
        if step < 5:
            step = 50
        w, h = self.width(), self.height()
        ox = self.ct.offset_x % step
        oy = self.ct.offset_y % step
        x = ox
        while x < w:
            p.drawLine(QPointF(x, 0), QPointF(x, h))
            x += step
        y = oy
        while y < h:
            p.drawLine(QPointF(0, y), QPointF(w, y))
            y += step

    def _draw_stage_floor(self, p: QPainter):
        sw, sd = self.stage.width, self.stage.depth
        corners = [
            self._w2s(0, 0, 0),
            self._w2s(sw, 0, 0),
            self._w2s(sw, sd, 0),
            self._w2s(0, sd, 0),
        ]
        poly = QPolygonF(corners)
        fc = self.stage.floor_color
        p.setPen(QPen(QColor(100, 100, 120), 2))
        p.setBrush(QBrush(QColor(fc[0], fc[1], fc[2])))
        p.drawPolygon(poly)

    def _draw_trusses(self, p: QPainter):
        pen = QPen(QColor(180, 180, 180), 4)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)
        for t in self.stage.trusses:
            w = t.width
            # 画桁架为矩形截面的线段（简化为粗线）
            p1 = self._w2s(t.x1, t.y1, t.z)
            p2 = self._w2s(t.x2, t.y2, t.z)
            p.drawLine(p1, p2)
            # 竖直支撑
            for sx, sy in [(t.x1, t.y1), (t.x2, t.y2)]:
                bot = self._w2s(sx, sy, 0)
                top = self._w2s(sx, sy, t.z)
                p.setPen(QPen(QColor(120, 120, 120), 2))
                p.drawLine(bot, top)
                p.setPen(QPen(QColor(180, 180, 180), 4))

    def _draw_fixtures(self, p: QPainter):
        for fx in self.stage.fixtures:
            pos = self._w2s(fx.x, fx.y, fx.z)
            size = 12
            if fx.selected:
                p.setPen(QPen(QColor(255, 255, 0), 2))
            else:
                p.setPen(QPen(QColor(200, 200, 200), 1))
            p.setBrush(QBrush(fx.color))
            # 灯具用菱形表示
            diamond = QPolygonF([
                QPointF(pos.x(), pos.y() - size),
                QPointF(pos.x() + size, pos.y()),
                QPointF(pos.x(), pos.y() + size),
                QPointF(pos.x() - size, pos.y()),
            ])
            p.drawPolygon(diamond)

    def _draw_beams(self, p: QPainter):
        for fx in self.stage.fixtures:
            if fx.intensity < 0.01:
                continue
            origin = self._w2s(fx.x, fx.y, fx.z)
            cone_pts_3d = fx.beam_cone_points(16)
            cone_pts = [self._w2s(*pt) for pt in cone_pts_3d]

            # 光束颜色（带透明度模拟强度）
            alpha = int(80 * fx.intensity)
            beam_color = QColor(fx.color_r, fx.color_g, fx.color_b, alpha)

            # 从灯具位置到锥体底面的三角形扇面
            for i in range(len(cone_pts)):
                j = (i + 1) % len(cone_pts)

                if self.show_fog:
                    # 雾气渐变效果：越远越淡
                    dist_ratio = (i + 1) / len(cone_pts)
                    fog_alpha = int(alpha * (1.0 - dist_ratio * 0.6))
                    fog_color = QColor(
                        fx.color_r, fx.color_g, fx.color_b,
                        max(5, fog_alpha)
                    )
                    p.setPen(Qt.NoPen)
                    p.setBrush(QBrush(fog_color))
                else:
                    p.setPen(Qt.NoPen)
                    p.setBrush(QBrush(beam_color))

                tri = QPolygonF([origin, cone_pts[i], cone_pts[j]])
                p.drawPolygon(tri)

            # 光束中心线
            endpoint = self._w2s(*fx.beam_endpoint())
            center_pen = QPen(QColor(fx.color_r, fx.color_g, fx.color_b,
                                      int(150 * fx.intensity)), 1, Qt.DashLine)
            p.setPen(center_pen)
            p.drawLine(origin, endpoint)

    def _draw_labels(self, p: QPainter):
        p.setPen(QColor(200, 200, 200))
        font = QFont("Consolas", 8)
        p.setFont(font)
        for fx in self.stage.fixtures:
            pos = self._w2s(fx.x, fx.y, fx.z)
            p.drawText(QPointF(pos.x() + 15, pos.y() - 5), fx.name)

    def _draw_hud(self, p: QPainter):
        view_names = {self.VIEW_TOP: "俯视图", self.VIEW_SIDE: "侧视图", self.VIEW_ISO: "等轴测"}
        p.setPen(QColor(180, 180, 180))
        p.setFont(QFont("Microsoft YaHei", 10))
        p.drawText(10, 20, f"视图: {view_names.get(self.view_mode, '?')}")
        p.drawText(10, 38, f"缩放: {self.ct.zoom:.1f} 像素/米")
        p.drawText(10, 56, f"灯具数: {len(self.stage.fixtures)}")

    # ── 交互 ──

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            # 查找点击的灯具
            click_pos = event.position()
            found = -1
            for i, fx in enumerate(self.stage.fixtures):
                pos = self._w2s(fx.x, fx.y, fx.z)
                dx = click_pos.x() - pos.x()
                dy = click_pos.y() - pos.y()
                if (dx*dx + dy*dy) < 200:
                    found = i
                    break
            self._clicked_index = found
            if found >= 0:
                self.stage.select_fixture(found)
                self._drag_fixture_idx = found
                self._dragging = True
            else:
                self.stage.select_fixture(-1)
            self.update()
        elif event.button() == Qt.MiddleButton:
            self._dragging = True
            self._last_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and self._drag_fixture_idx >= 0:
            # 拖动灯具
            sp = event.position()
            fx = self.stage.fixtures[self._drag_fixture_idx]
            # 逆变换（简化：只在俯视模式下拖动）
            if self.view_mode == self.VIEW_TOP:
                fx.x = (sp.x() - self.ct.offset_x) / self.ct.zoom
                fx.y = (sp.y() - self.ct.offset_y) / self.ct.zoom
            self.update()
        elif self._dragging:
            # 平移视图
            dx = event.position().x() - self._last_pos.x()
            dy = event.position().y() - self._last_pos.y()
            self.ct.offset_x += dx
            self.ct.offset_y += dy
            self._last_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False
        self._drag_fixture_idx = -1

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y()
        factor = 1.1 if delta > 0 else 0.9
        self.ct.zoom = max(5, min(200, self.ct.zoom * factor))
        self.update()

    def get_clicked_index(self) -> int:
        return self._clicked_index


# ── 灯具列表面板 ──────────────────────────────────────────────────────────

class FixtureListPanel(QWidget):
    """左侧灯具列表"""

    selection_changed = None  # 外部连接
    fixture_changed = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("灯具列表")
        title.setStyleSheet("font-weight:bold; color:#e0e0e0; font-size:13px;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_select)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("添加")
        self.btn_add.clicked.connect(self._add_fixture)
        self.btn_remove = QPushButton("删除")
        self.btn_remove.clicked.connect(self._remove_fixture)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        layout.addLayout(btn_row)

        # 快速控制
        grp = QGroupBox("快速控制")
        gl = QVBoxLayout(grp)

        gl.addWidget(QLabel("颜色"))
        color_row = QHBoxLayout()
        self.btn_color = QPushButton("选择颜色")
        self.btn_color.clicked.connect(self._pick_color)
        self._color_preview = QLabel("  ")
        self._color_preview.setFixedSize(30, 20)
        self._color_preview.setStyleSheet("background:#fff; border:1px solid #666;")
        color_row.addWidget(self.btn_color)
        color_row.addWidget(self._color_preview)
        gl.addLayout(color_row)

        gl.addWidget(QLabel("亮度"))
        self.slider_intensity = QSlider(Qt.Horizontal)
        self.slider_intensity.setRange(0, 100)
        self.slider_intensity.setValue(80)
        self.slider_intensity.valueChanged.connect(self._on_intensity)
        gl.addWidget(self.slider_intensity)

        self.lbl_intensity = QLabel("80%")
        gl.addWidget(self.lbl_intensity)

        layout.addWidget(grp)
        layout.addStretch()

    def set_stage(self, stage: StageModel):
        self.stage = stage
        self.refresh()

    def refresh(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        if not self.stage:
            self.list_widget.blockSignals(False)
            return
        for i, fx in enumerate(self.stage.fixtures):
            item = QListWidgetItem(f"{'▶ ' if fx.selected else ''}{fx.name}  ({fx.id})")
            self.list_widget.addItem(item)
            if fx.selected:
                self.list_widget.setCurrentRow(i)
        self.list_widget.blockSignals(False)
        self._update_color_preview()

    def _on_select(self, row: int):
        if not self.stage or row < 0:
            return
        if getattr(self, '_selecting', False):
            return
        self._selecting = True
        try:
            self.stage.select_fixture(row)
            self.refresh()
            if self.selection_changed:
                self.selection_changed(row)
        finally:
            self._selecting = False

    def _add_fixture(self):
        if not self.stage:
            return
        idx = len(self.stage.fixtures)
        fx = Fixture(
            id=f"fix_new_{idx}", name=f"新灯具-{idx+1}",
            x=5 + (idx % 4) * 4, y=5 + (idx // 4) * 4, z=6,
        )
        self.stage.fixtures.append(fx)
        self.refresh()
        if self.fixture_changed:
            self.fixture_changed()

    def _remove_fixture(self):
        if not self.stage:
            return
        row = self.list_widget.currentRow()
        if row >= 0:
            self.stage.remove_fixture(row)
            self.refresh()
            if self.fixture_changed:
                self.fixture_changed()

    def _pick_color(self):
        fx = self.stage.get_selected() if self.stage else None
        if not fx:
            return
        c = QColorDialog.getColor(fx.color, self, "选择灯具颜色")
        if c.isValid():
            fx.color_r, fx.color_g, fx.color_b = c.red(), c.green(), c.blue()
            self._update_color_preview()
            if self.fixture_changed:
                self.fixture_changed()

    def _on_intensity(self, val):
        fx = self.stage.get_selected() if self.stage else None
        if fx:
            fx.intensity = val / 100.0
            self.lbl_intensity.setText(f"{val}%")
            if self.fixture_changed:
                self.fixture_changed()

    def _update_color_preview(self):
        fx = self.stage.get_selected() if self.stage else None
        if fx:
            self._color_preview.setStyleSheet(
                f"background:rgb({fx.color_r},{fx.color_g},{fx.color_b}); border:1px solid #666;")
            self.slider_intensity.setValue(int(fx.intensity * 100))


# ── 属性面板 ──────────────────────────────────────────────────────────────

class PropertiesPanel(QWidget):
    """右侧属性面板"""

    property_changed = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stage = None
        self._updating = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        title = QLabel("属性面板")
        title.setStyleSheet("font-weight:bold; color:#e0e0e0; font-size:13px;")
        layout.addWidget(title)

        # 名称
        grp_name = QGroupBox("基本信息")
        gn_l = QVBoxLayout(grp_name)
        self.lbl_name = QLabel("未选中")
        gn_l.addWidget(self.lbl_name)
        self.lbl_pos = QLabel("")
        gn_l.addWidget(self.lbl_pos)
        layout.addWidget(grp_name)

        # 颜色
        grp_color = QGroupBox("颜色 (RGB)")
        gc_l = QVBoxLayout(grp_color)

        for ch in [('r', '红'), ('g', '绿'), ('b', '蓝')]:
            row = QHBoxLayout()
            row.addWidget(QLabel(ch[1]))
            spin = QSpinBox()
            spin.setRange(0, 255)
            spin.setValue(255)
            spin.valueChanged.connect(lambda v, c=ch[0]: self._on_rgb(c, v))
            setattr(self, f'spin_{ch[0]}', spin)
            row.addWidget(spin)
            gc_l.addLayout(row)

        self.btn_pick_color = QPushButton("打开颜色选择器")
        self.btn_pick_color.clicked.connect(self._pick_color)
        gc_l.addWidget(self.btn_pick_color)

        self._color_bar = QLabel()
        self._color_bar.setFixedHeight(20)
        self._color_bar.setStyleSheet("background:#fff; border:1px solid #666;")
        gc_l.addWidget(self._color_bar)
        layout.addWidget(grp_color)

        # 角度
        grp_angle = QGroupBox("角度")
        ga_l = QVBoxLayout(grp_angle)

        ga_l.addWidget(QLabel("水平 (Pan)"))
        self.spin_pan = QDoubleSpinBox()
        self.spin_pan.setRange(-180, 180)
        self.spin_pan.setSuffix("°")
        self.spin_pan.valueChanged.connect(self._on_pan)
        ga_l.addWidget(self.spin_pan)

        ga_l.addWidget(QLabel("垂直 (Tilt)"))
        self.spin_tilt = QDoubleSpinBox()
        self.spin_tilt.setRange(-90, 90)
        self.spin_tilt.setSuffix("°")
        self.spin_tilt.valueChanged.connect(self._on_tilt)
        ga_l.addWidget(self.spin_tilt)
        layout.addWidget(grp_angle)

        # 亮度
        grp_int = QGroupBox("亮度")
        gi_l = QVBoxLayout(grp_int)
        self.spin_intensity = QDoubleSpinBox()
        self.spin_intensity.setRange(0, 100)
        self.spin_intensity.setSuffix("%")
        self.spin_intensity.setValue(80)
        self.spin_intensity.valueChanged.connect(self._on_intensity)
        gi_l.addWidget(self.spin_intensity)
        layout.addWidget(grp_int)

        # 光束
        grp_beam = QGroupBox("光束")
        gb_l = QVBoxLayout(grp_beam)
        gb_l.addWidget(QLabel("光束角度"))
        self.spin_beam_angle = QDoubleSpinBox()
        self.spin_beam_angle.setRange(1, 120)
        self.spin_beam_angle.setValue(25)
        self.spin_beam_angle.setSuffix("°")
        self.spin_beam_angle.valueChanged.connect(self._on_beam_angle)
        gb_l.addWidget(self.spin_beam_angle)
        gb_l.addWidget(QLabel("光束长度"))
        self.spin_beam_len = QDoubleSpinBox()
        self.spin_beam_len.setRange(1, 50)
        self.spin_beam_len.setValue(12)
        self.spin_beam_len.setSuffix(" m")
        self.spin_beam_len.valueChanged.connect(self._on_beam_len)
        gb_l.addWidget(self.spin_beam_len)
        layout.addWidget(grp_beam)

        layout.addStretch()

    def set_stage(self, stage: StageModel):
        self.stage = stage
        self.update_display()

    def update_display(self):
        fx = self.stage.get_selected() if self.stage else None
        self._updating = True
        if not fx:
            self.lbl_name.setText("未选中灯具")
            self.lbl_pos.setText("")
            self._updating = False
            return

        self.lbl_name.setText(f"{fx.name}  (ID: {fx.id})")
        self.lbl_pos.setText(f"位置: X={fx.x:.1f}  Y={fx.y:.1f}  Z={fx.z:.1f}")

        self.spin_r.setValue(fx.color_r)
        self.spin_g.setValue(fx.color_g)
        self.spin_b.setValue(fx.color_b)
        self._update_color_bar()

        self.spin_pan.setValue(fx.pan)
        self.spin_tilt.setValue(fx.tilt)
        self.spin_intensity.setValue(fx.intensity * 100)
        self.spin_beam_angle.setValue(fx.beam_angle)
        self.spin_beam_len.setValue(fx.beam_length)
        self._updating = False

    def _get_fx(self):
        return self.stage.get_selected() if self.stage else None

    def _on_rgb(self, ch, val):
        if self._updating:
            return
        fx = self._get_fx()
        if not fx:
            return
        setattr(fx, f'color_{ch}', val)
        self._update_color_bar()
        if self.property_changed:
            self.property_changed()

    def _pick_color(self):
        fx = self._get_fx()
        if not fx:
            return
        c = QColorDialog.getColor(fx.color, self, "选择颜色")
        if c.isValid():
            self._updating = True
            fx.color_r, fx.color_g, fx.color_b = c.red(), c.green(), c.blue()
            self.spin_r.setValue(c.red())
            self.spin_g.setValue(c.green())
            self.spin_b.setValue(c.blue())
            self._update_color_bar()
            self._updating = False
            if self.property_changed:
                self.property_changed()

    def _on_pan(self, val):
        if self._updating:
            return
        fx = self._get_fx()
        if fx:
            fx.pan = val
            if self.property_changed:
                self.property_changed()

    def _on_tilt(self, val):
        if self._updating:
            return
        fx = self._get_fx()
        if fx:
            fx.tilt = val
            if self.property_changed:
                self.property_changed()

    def _on_intensity(self, val):
        if self._updating:
            return
        fx = self._get_fx()
        if fx:
            fx.intensity = val / 100.0
            if self.property_changed:
                self.property_changed()

    def _on_beam_angle(self, val):
        if self._updating:
            return
        fx = self._get_fx()
        if fx:
            fx.beam_angle = val
            if self.property_changed:
                self.property_changed()

    def _on_beam_len(self, val):
        if self._updating:
            return
        fx = self._get_fx()
        if fx:
            fx.beam_length = val
            if self.property_changed:
                self.property_changed()

    def _update_color_bar(self):
        r = self.spin_r.value()
        g = self.spin_g.value()
        b = self.spin_b.value()
        self._color_bar.setStyleSheet(f"background:rgb({r},{g},{b}); border:1px solid #666;")


# ── 主窗口 ────────────────────────────────────────────────────────────────

class VisualSimulator(BaseToolWindow):
    """视觉模拟器主窗口"""

    def __init__(self):
        super().__init__('VisualSimulator', '视觉模拟器', '1.0.0', 1400, 900)
        self.stage = create_default_stage()
        self.logger.info("视觉模拟器已初始化")
        self._build_ui()
        self._refresh_all()

    def _build_ui(self):
        # 工具栏
        self._build_toolbar()

        # 主内容
        splitter = QSplitter(Qt.Horizontal)

        # 左侧 - 灯具列表
        self.fixture_panel = FixtureListPanel()
        self.fixture_panel.selection_changed = self._on_fixture_selected
        self.fixture_panel.fixture_changed = self._refresh_all
        self.fixture_panel.set_stage(self.stage)
        self.fixture_panel.setMinimumWidth(200)
        self.fixture_panel.setMaximumWidth(300)
        splitter.addWidget(self.fixture_panel)

        # 中间 - 3D 画布
        self.canvas = StageCanvas()
        self.canvas.set_stage(self.stage)
        splitter.addWidget(self.canvas)

        # 右侧 - 属性面板
        self.props_panel = PropertiesPanel()
        self.props_panel.property_changed = self._refresh_all
        self.props_panel.set_stage(self.stage)
        self.props_panel.setMinimumWidth(220)
        self.props_panel.setMaximumWidth(320)
        splitter.addWidget(self.props_panel)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        self.set_central_content(splitter)
        self._center_view()

    def _build_toolbar(self):
        tb = self.addToolBar("视图工具")
        tb.setMovable(False)

        # 视图切换
        self._view_actions = []
        for name, mode in [("俯视图", StageCanvas.VIEW_TOP),
                           ("侧视图", StageCanvas.VIEW_SIDE),
                           ("等轴测", StageCanvas.VIEW_ISO)]:
            act = QAction(name, self)
            act.setCheckable(True)
            act.setChecked(mode == StageCanvas.VIEW_ISO)
            act.triggered.connect(lambda checked, m=mode: self._set_view(m))
            tb.addAction(act)
            self._view_actions.append((act, mode))

        tb.addSeparator()

        # 网格
        act_grid = QAction("网格", self)
        act_grid.setCheckable(True)
        act_grid.setChecked(True)
        act_grid.triggered.connect(self._toggle_grid)
        tb.addAction(act_grid)
        self._act_grid = act_grid

        # 光束
        act_beams = QAction("光束", self)
        act_beams.setCheckable(True)
        act_beams.setChecked(True)
        act_beams.triggered.connect(self._toggle_beams)
        tb.addAction(act_beams)

        # 雾气
        act_fog = QAction("雾气", self)
        act_fog.setCheckable(True)
        act_fog.setChecked(True)
        act_fog.triggered.connect(self._toggle_fog)
        tb.addAction(act_fog)

        tb.addSeparator()

        # 缩放
        act_zoom_in = QAction("放大", self)
        act_zoom_in.triggered.connect(lambda: self._zoom(1.3))
        tb.addAction(act_zoom_in)

        act_zoom_out = QAction("缩小", self)
        act_zoom_out.triggered.connect(lambda: self._zoom(0.7))
        tb.addAction(act_zoom_out)

        act_zoom_fit = QAction("适应", self)
        act_zoom_fit.triggered.connect(self._center_view)
        tb.addAction(act_zoom_fit)

        tb.addSeparator()

        # 文件
        act_save = QAction("保存场景", self)
        act_save.triggered.connect(self._save_scene)
        tb.addAction(act_save)

        act_load = QAction("加载场景", self)
        act_load.triggered.connect(self._load_scene)
        tb.addAction(act_load)

    def _set_view(self, mode):
        self.canvas.set_view_mode(mode)
        for act, m in self._view_actions:
            act.setChecked(m == mode)

    def _toggle_grid(self, checked):
        self.canvas.show_grid = checked
        self.canvas.update()

    def _toggle_beams(self, checked):
        self.canvas.show_beams = checked
        self.canvas.update()

    def _toggle_fog(self, checked):
        self.canvas.show_fog = checked
        self.canvas.update()

    def _zoom(self, factor):
        self.canvas.ct.zoom = max(5, min(200, self.canvas.ct.zoom * factor))
        self.canvas.update()

    def _center_view(self):
        self.canvas._center_view()
        self.canvas.update()

    def _on_fixture_selected(self, row):
        if hasattr(self, 'props_panel'):
            self.props_panel.update_display()
        if hasattr(self, 'canvas'):
            self.canvas.update()

    def _refresh_all(self):
        self.fixture_panel.refresh()
        self.props_panel.update_display()
        self.canvas.update()

    def _save_scene(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存场景", "", "JSON 文件 (*.json)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.stage.to_dict(), f, ensure_ascii=False, indent=2)
                self.logger.info(f"场景已保存: {path}")
                self.statusBar().showMessage(f"已保存: {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "保存失败", str(e))

    def _load_scene(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载场景", "", "JSON 文件 (*.json)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.stage = StageModel.from_dict(data)
                self.fixture_panel.set_stage(self.stage)
                self.props_panel.set_stage(self.stage)
                self.canvas.set_stage(self.stage)
                self._center_view()
                self.logger.info(f"场景已加载: {path}")
                self.statusBar().showMessage(f"已加载: {path}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "加载失败", str(e))


# ── 入口 ──────────────────────────────────────────────────────────────────

def main():
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = VisualSimulator()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    import traceback
    try:

        main()
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "VisualSimulator - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
