# -*- coding: utf-8 -*-
"""特效设计器 - FXDesigner"""
import sys, csv, json
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QListWidget,
    QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QCheckBox, QTabWidget,
    QListWidgetItem, QScrollArea, QToolBar, QLineEdit
)
from PySide6.QtCore import Qt, QPointF, QRectF, Signal, QMimeData
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QMouseEvent,
    QPaintEvent, QDragEnterEvent, QDropEvent, QDrag,
    QAction, QKeySequence
)

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow


class EffectType(Enum):
    SMOKE = "烟雾"
    CO2 = "CO2喷射"
    FLAME = "火焰"
    COLD_SPARK = "冷烟花"


EFFECT_COLORS = {
    EffectType.SMOKE: QColor(180, 180, 200, 180),
    EffectType.CO2: QColor(200, 230, 255, 200),
    EffectType.FLAME: QColor(255, 120, 0, 200),
    EffectType.COLD_SPARK: QColor(255, 255, 200, 200),
}

EFFECT_ICONS = {
    EffectType.SMOKE: "💨",
    EffectType.CO2: "❄️",
    EffectType.FLAME: "🔥",
    EffectType.COLD_SPARK: "✨",
}


@dataclass
class FxEffect:
    name: str
    effect_type: EffectType
    cue_number: float
    start_time: float  # seconds
    duration: float  # seconds
    intensity: float  # 0-100%
    pos_x: float  # stage position meters
    pos_y: float
    safety_hold: float = 2.0  # seconds between this and next effect


class TimelineWidget(QWidget):
    """特效时间线"""
    SECONDS_PER_PIXEL = 0.05
    ROW_HEIGHT = 50
    HEADER_HEIGHT = 30

    effect_selected = Signal(int)  # index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.effects: list[FxEffect] = []
        self.setMinimumHeight(200)
        self.total_duration = 60.0  # seconds
        self._dragging_idx = -1
        self._drag_offset = 0
        self._selected_idx = -1
        self.setMouseTracking(True)

    def set_effects(self, effects: list[FxEffect]):
        self.effects = effects
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(25, 25, 35))

        # Time ruler
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.setFont(QFont("Consolas", 9))
        px_per_sec = 1.0 / self.SECONDS_PER_PIXEL
        for s in range(0, int(self.total_duration) + 1, 5):
            x = s * px_per_sec
            painter.drawLine(int(x), 0, int(x), h)
            painter.drawText(int(x + 2), 15, f"{s}s")
        # Minor ticks
        painter.setPen(QPen(QColor(60, 60, 70), 1))
        for s in range(0, int(self.total_duration) + 1):
            x = s * px_per_sec
            painter.drawLine(int(x), self.HEADER_HEIGHT - 5, int(x), self.HEADER_HEIGHT)

        # Header line
        painter.setPen(QPen(QColor(100, 100, 120), 1))
        painter.drawLine(0, self.HEADER_HEIGHT, w, self.HEADER_HEIGHT)

        # Effects
        for i, fx in enumerate(self.effects):
            x = fx.start_time * px_per_sec
            bw = fx.duration * px_per_sec
            row = i % max(1, (h - self.HEADER_HEIGHT) // self.ROW_HEIGHT)
            y = self.HEADER_HEIGHT + row * self.ROW_HEIGHT + 2

            color = EFFECT_COLORS.get(fx.effect_type, QColor(100, 100, 255))
            selected = (i == self._selected_idx)
            if selected:
                painter.setPen(QPen(QColor(255, 255, 0), 2))
            else:
                painter.setPen(QPen(color.lighter(130), 1))
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(int(x), int(y), max(int(bw), 20), self.ROW_HEIGHT - 4, 4, 4)

            # Label
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Microsoft YaHei", 8))
            icon = EFFECT_ICONS.get(fx.effect_type, "")
            label = f"{icon} {fx.name}"
            painter.drawText(int(x + 4), int(y + 15), label)
            painter.drawText(int(x + 4), int(y + 30), f"{fx.duration:.1f}s {fx.intensity:.0f}%")

            # Safety hold indicator
            if fx.safety_hold > 0:
                hold_x = x + bw
                hold_w = fx.safety_hold * px_per_sec
                painter.setPen(QPen(QColor(255, 100, 100, 150), 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush(QColor(255, 0, 0, 30)))
                painter.drawRect(int(hold_x), int(y), max(int(hold_w), 4), self.ROW_HEIGHT - 4)

        # Playhead
        painter.setPen(QPen(QColor(255, 255, 0), 1))
        # Just show a cursor at 0
        painter.drawLine(0, 0, 0, h)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            px_per_sec = 1.0 / self.SECONDS_PER_PIXEL
            pos = event.position()
            for i, fx in enumerate(self.effects):
                x = fx.start_time * px_per_sec
                bw = max(fx.duration * px_per_sec, 20)
                row = i % max(1, (self.height() - self.HEADER_HEIGHT) // self.ROW_HEIGHT)
                y = self.HEADER_HEIGHT + row * self.ROW_HEIGHT + 2
                if x <= pos.x() <= x + bw and y <= pos.y() <= y + self.ROW_HEIGHT - 4:
                    self._selected_idx = i
                    self._dragging_idx = i
                    self._drag_offset = pos.x() - x
                    self.effect_selected.emit(i)
                    self.update()
                    return
            self._selected_idx = -1
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging_idx >= 0:
            px_per_sec = 1.0 / self.SECONDS_PER_PIXEL
            new_x = event.position().x() - self._drag_offset
            new_time = max(0, new_x * self.SECONDS_PER_PIXEL)
            self.effects[self._dragging_idx].start_time = new_time
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging_idx = -1


class StageCanvas(QWidget):
    """舞台特效位置画布"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.effects: list[FxEffect] = []
        self.setMinimumSize(400, 300)
        self.scale = 40.0

    def set_effects(self, effects: list[FxEffect]):
        self.effects = effects
        self.update()

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(30, 30, 40))

        # Stage
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.setBrush(QBrush(QColor(45, 45, 55)))
        painter.drawRect(40, 40, w - 80, int(h * 0.5))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.setFont(QFont("Microsoft YaHei", 10))
        painter.drawText(50, 60, "舞台")

        # Audience
        painter.setPen(QPen(QColor(100, 100, 150), 2, Qt.PenStyle.DashLine))
        painter.setBrush(QBrush(QColor(35, 35, 50)))
        ay = 40 + h * 0.55
        painter.drawRect(40, int(ay), w - 80, int(h * 0.3))
        painter.drawText(50, int(ay + 18), "观众区")

        # Effects positions
        for fx in self.effects:
            px = 40 + fx.pos_x * self.scale
            py = 40 + fx.pos_y * self.scale
            color = EFFECT_COLORS.get(fx.effect_type, QColor(100, 100, 255))
            icon = EFFECT_ICONS.get(fx.effect_type, "●")

            # Glow
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 40)))
            painter.drawEllipse(QPointF(px, py), 25, 25)

            # Dot
            painter.setPen(QPen(color.lighter(150), 2))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(QPointF(px, py), 10, 10)

            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.setFont(QFont("Microsoft YaHei", 8))
            painter.drawText(int(px + 14), int(py - 4), fx.name)
            painter.drawText(int(px + 14), int(py + 8), f"{fx.effect_type.value}")

        painter.end()


class FXDesignerWindow(BaseToolWindow):
    """特效设计器主窗口"""

    def __init__(self):
        super().__init__('FXDesigner', '特效设计器', '1.0.0', 1200, 850)

        # Toolbar
        self.toolbar.addSeparator()
        self.toolbar.addAction("📊 导出CSV", self._export_csv)
        self.toolbar.addAction("📋 导出JSON", self._export_json)
        self.toolbar.addAction("🔄 刷新", self._refresh_views)

        self.effects: list[FxEffect] = []
        self._cue_counter = 1

        central = QWidget()
        main_layout = QVBoxLayout(central)

        # Top: controls + stage
        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: effect palette + properties
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setMaximumWidth(300)

        # Effect palette
        palette_group = QGroupBox("特效类型")
        pl = QVBoxLayout(palette_group)
        for et in EffectType:
            btn = QPushButton(f"{EFFECT_ICONS[et]} {et.value}")
            btn.clicked.connect(lambda checked, t=et: self._add_effect(t))
            pl.addWidget(btn)
        left_layout.addWidget(palette_group)

        # Effect properties
        props_group = QGroupBox("特效属性")
        form = QFormLayout(props_group)
        self.prop_name = QLineEdit()
        form.addRow("名称:", self.prop_name)
        self.prop_cue = QDoubleSpinBox()
        self.prop_cue.setRange(0, 9999)
        self.prop_cue.setDecimals(1)
        form.addRow("提示号:", self.prop_cue)
        self.prop_start = QDoubleSpinBox()
        self.prop_start.setRange(0, 3600)
        self.prop_start.setSuffix(" 秒")
        form.addRow("开始时间:", self.prop_start)
        self.prop_duration = QDoubleSpinBox()
        self.prop_duration.setRange(0.1, 300)
        self.prop_duration.setValue(3.0)
        self.prop_duration.setSuffix(" 秒")
        form.addRow("持续时间:", self.prop_duration)
        self.prop_intensity = QDoubleSpinBox()
        self.prop_intensity.setRange(0, 100)
        self.prop_intensity.setValue(80)
        self.prop_intensity.setSuffix(" %")
        form.addRow("强度:", self.prop_intensity)
        self.prop_posx = QDoubleSpinBox()
        self.prop_posx.setRange(0, 50)
        self.prop_posx.setValue(5)
        self.prop_posx.setSuffix(" m")
        form.addRow("X位置:", self.prop_posx)
        self.prop_posy = QDoubleSpinBox()
        self.prop_posy.setRange(0, 50)
        self.prop_posy.setValue(3)
        self.prop_posy.setSuffix(" m")
        form.addRow("Y位置:", self.prop_posy)
        self.prop_safety = QDoubleSpinBox()
        self.prop_safety.setRange(0, 60)
        self.prop_safety.setValue(2.0)
        self.prop_safety.setSuffix(" 秒")
        form.addRow("安全间隔:", self.prop_safety)
        btn_apply = QPushButton("应用修改")
        btn_apply.clicked.connect(self._apply_props)
        form.addRow(btn_apply)
        left_layout.addWidget(props_group)

        # Effect list
        list_group = QGroupBox("特效列表")
        ll = QVBoxLayout(list_group)
        self.effect_list = QListWidget()
        self.effect_list.currentRowChanged.connect(self._on_effect_selected)
        ll.addWidget(self.effect_list)
        btn_del = QPushButton("删除选中")
        btn_del.clicked.connect(self._delete_effect)
        ll.addWidget(btn_del)
        left_layout.addWidget(list_group)

        left_layout.addStretch()

        # Center: timeline + stage canvas
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.timeline = TimelineWidget()
        self.timeline.effect_selected.connect(self._on_timeline_select)
        right_layout.addWidget(self.timeline, 1)

        self.stage_canvas = StageCanvas()
        right_layout.addWidget(self.stage_canvas, 1)

        top_splitter.addWidget(left_panel)
        top_splitter.addWidget(right_panel)
        top_splitter.setSizes([300, 900])

        main_layout.addWidget(top_splitter)
        self.set_central_content(central)
        self.logger.info("特效设计器已就绪")

    def _add_effect(self, effect_type: EffectType):
        idx = len(self.effects)
        name = f"{effect_type.value}_{self._cue_counter}"
        fx = FxEffect(
            name=name,
            effect_type=effect_type,
            cue_number=float(self._cue_counter),
            start_time=idx * 5.0,
            duration=3.0,
            intensity=80.0,
            pos_x=3 + idx * 2,
            pos_y=3
        )
        self._cue_counter += 1
        self.effects.append(fx)
        self._refresh_list()
        self._refresh_views()
        self.logger.info(f"添加特效: {name}")

    def _refresh_list(self):
        self.effect_list.clear()
        for fx in self.effects:
            icon = EFFECT_ICONS.get(fx.effect_type, "")
            self.effect_list.addItem(
                f"{icon} {fx.name} | {fx.start_time:.1f}s | {fx.duration:.1f}s | {fx.intensity:.0f}%")

    def _refresh_views(self):
        self.timeline.set_effects(self.effects)
        self.stage_canvas.set_effects(self.effects)

    def _on_effect_selected(self, row):
        if 0 <= row < len(self.effects):
            fx = self.effects[row]
            self.prop_name.setText(fx.name)
            self.prop_cue.setValue(fx.cue_number)
            self.prop_start.setValue(fx.start_time)
            self.prop_duration.setValue(fx.duration)
            self.prop_intensity.setValue(fx.intensity)
            self.prop_posx.setValue(fx.pos_x)
            self.prop_posy.setValue(fx.pos_y)
            self.prop_safety.setValue(fx.safety_hold)

    def _on_timeline_select(self, idx):
        self.effect_list.setCurrentRow(idx)
        self._on_effect_selected(idx)

    def _apply_props(self):
        row = self.effect_list.currentRow()
        if row < 0 or row >= len(self.effects):
            return
        fx = self.effects[row]
        fx.name = self.prop_name.text()
        fx.cue_number = self.prop_cue.value()
        fx.start_time = self.prop_start.value()
        fx.duration = self.prop_duration.value()
        fx.intensity = self.prop_intensity.value()
        fx.pos_x = self.prop_posx.value()
        fx.pos_y = self.prop_posy.value()
        fx.safety_hold = self.prop_safety.value()
        self._refresh_list()
        self._refresh_views()
        self.logger.info(f"已更新特效: {fx.name}")

    def _delete_effect(self):
        row = self.effect_list.currentRow()
        if 0 <= row < len(self.effects):
            name = self.effects[row].name
            self.effects.pop(row)
            self._refresh_list()
            self._refresh_views()
            self.logger.info(f"删除特效: {name}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "", "CSV文件 (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["提示号", "名称", "类型", "开始时间(s)", "持续时间(s)",
                                "强度(%)", "X位置(m)", "Y位置(m)", "安全间隔(s)"])
                for fx in self.effects:
                    writer.writerow([fx.cue_number, fx.name, fx.effect_type.value,
                                   f"{fx.start_time:.1f}", f"{fx.duration:.1f}",
                                   f"{fx.intensity:.0f}", f"{fx.pos_x:.1f}",
                                   f"{fx.pos_y:.1f}", f"{fx.safety_hold:.1f}"])
            self.logger.info(f"已导出CSV: {path}")
            QMessageBox.information(self, "导出成功", f"特效列表已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出JSON", "", "JSON文件 (*.json)")
        if not path:
            return
        try:
            data = []
            for fx in self.effects:
                data.append({
                    "cue": fx.cue_number,
                    "name": fx.name,
                    "type": fx.effect_type.value,
                    "start_time": fx.start_time,
                    "duration": fx.duration,
                    "intensity": fx.intensity,
                    "position": {"x": fx.pos_x, "y": fx.pos_y},
                    "safety_hold": fx.safety_hold
                })
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已导出JSON: {path}")
            QMessageBox.information(self, "导出成功", f"特效列表已导出到:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))

    def _show_shortcuts(self):
        text = """<table>
        <tr><td><b>点击特效类型</b></td><td>添加新特效到时间线</td></tr>
        <tr><td><b>拖拽时间线条</b></td><td>调整特效开始时间</td></tr>
        <tr><td><b>选中特效后修改</b></td><td>点击"应用修改"保存</td></tr>
        </table>"""
        QMessageBox.information(self, "操作说明", text)


if __name__ == '__main__':
    from launcher_utils import run_tool
    run_tool(FXDesignerWindow, "FXDesigner - 启动错误")