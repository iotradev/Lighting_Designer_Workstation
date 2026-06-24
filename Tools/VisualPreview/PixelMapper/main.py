# -*- coding: utf-8 -*-
"""
像素映射器 - LED矩阵网格设计器
支持LED像素到DMX通道映射、颜色图案编辑、动画预览
"""

import sys
import json
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
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QSpinBox, QPushButton, QComboBox, QColorDialog, QGroupBox,
    QScrollArea, QFileDialog, QMessageBox, QSlider, QSizePolicy,
    QFrame, QCheckBox, QSplitter, QApplication
)
from PySide6.QtCore import Qt, QTimer, QRect, QSize
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QMouseEvent, QPaintEvent,
    QResizeEvent, QFont, QLinearGradient, QRadialGradient
)

from pixel_engine import PixelGridModel, PatternGenerator


# ====================================================================
# 像素网格绘制组件
# ====================================================================

class PixelGridWidget(QWidget):
    """LED像素网格绘制控件"""

    def __init__(self, model: PixelGridModel, parent=None):
        super().__init__(parent)
        self.model = model
        self._brush_color = QColor(255, 0, 0)
        self._brush_mode = "paint"  # paint / erase / fill
        self._cell_size = 24
        self._show_dmx = False
        self._pressed = False
        self.setMinimumSize(200, 200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def set_brush_color(self, color: QColor):
        self._brush_color = color

    def set_brush_mode(self, mode: str):
        self._brush_mode = mode

    def set_show_dmx(self, show: bool):
        self._show_dmx = show

    def update_from_model(self):
        self._calc_cell_size()
        self.update()

    def _calc_cell_size(self):
        if self.model.rows == 0 or self.model.cols == 0:
            return
        w = self.width() - 4
        h = self.height() - 4
        self._cell_size = max(4, min(w // self.model.cols, h // self.model.rows))

    def _get_cell(self, x, y):
        """鼠标坐标转网格坐标"""
        cols = self.model.cols
        rows = self.model.rows
        grid_w = cols * self._cell_size
        grid_h = rows * self._cell_size
        ox = (self.width() - grid_w) // 2
        oy = (self.height() - grid_h) // 2
        c = (x - ox) // self._cell_size
        r = (y - oy) // self._cell_size
        if 0 <= r < rows and 0 <= c < cols:
            return r, c
        return None, None

    def _paint_cell(self, r, c):
        if self._brush_mode == "paint":
            self.model.set_pixel_color(r, c, self._brush_color.red(),
                                       self._brush_color.green(), self._brush_color.blue())
        elif self._brush_mode == "erase":
            self.model.erase_pixel(r, c)
        elif self._brush_mode == "fill":
            self.model.fill_all(self._brush_color.red(),
                                self._brush_color.green(), self._brush_color.blue())

    def mousePressEvent(self, ev: QMouseEvent):
        if ev.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            r, c = self._get_cell(int(ev.position().x()), int(ev.position().y()))
            if r is not None:
                self._paint_cell(r, c)
                self.update()

    def mouseMoveEvent(self, ev: QMouseEvent):
        if self._pressed and self._brush_mode != "fill":
            r, c = self._get_cell(int(ev.position().x()), int(ev.position().y()))
            if r is not None:
                self._paint_cell(r, c)
                self.update()

    def mouseReleaseEvent(self, ev: QMouseEvent):
        self._pressed = False

    def resizeEvent(self, event: QResizeEvent):
        self._calc_cell_size()
        super().resizeEvent(event)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cols = self.model.cols
        rows = self.model.rows
        grid_w = cols * self._cell_size
        grid_h = rows * self._cell_size
        ox = (self.width() - grid_w) // 2
        oy = (self.height() - grid_h) // 2

        # 背景
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        # 绘制网格
        for r in range(rows):
            for c in range(cols):
                pixel = self.model.get_pixel(r, c)
                x = ox + c * self._cell_size
                y = oy + r * self._cell_size
                rect = QRect(x, y, self._cell_size, self._cell_size)

                # 像素颜色
                cr, cg, cb = pixel.to_tuple()
                if cr == 0 and cg == 0 and cb == 0:
                    painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor(50, 50, 50))
                else:
                    painter.fillRect(rect.adjusted(1, 1, -1, -1), QColor(cr, cg, cb))
                    # LED发光效果
                    if self._cell_size >= 12:
                        glow = QRect(x + 2, y + 2, self._cell_size - 4, self._cell_size - 4)
                        grad = QRadialGradient(glow.center(), glow.width() / 2)
                        grad.setColorAt(0, QColor(cr, cg, cb, 60))
                        grad.setColorAt(1, QColor(cr, cg, cb, 0))
                        painter.fillRect(glow, grad)

                # DMX地址显示
                if self._show_dmx and self._cell_size >= 16:
                    painter.setPen(QPen(QColor(200, 200, 200, 180)))
                    font = QFont("Arial", max(6, self._cell_size // 5))
                    painter.setFont(font)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(pixel.dmx_address))

        # 网格线
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        for r in range(rows + 1):
            y = oy + r * self._cell_size
            painter.drawLine(ox, y, ox + grid_w, y)
        for c in range(cols + 1):
            x = ox + c * self._cell_size
            painter.drawLine(x, oy, x, oy + grid_h)

        # 边框
        painter.setPen(QPen(QColor(120, 120, 120), 2))
        painter.drawRect(ox, oy, grid_w, grid_h)

        painter.end()


# ====================================================================
# 主窗口
# ====================================================================

class PixelMapperWindow(BaseToolWindow):
    """像素映射器主窗口"""

    def __init__(self):
        super().__init__('PixelMapper', '像素映射器', '1.0.0', 1200, 850)
        self.model = PixelGridModel(16, 16)
        self._current_color = QColor(255, 0, 0)
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._on_anim_tick)
        self._anim_frame_idx = 0
        self._anim_running = False
        self._setup_ui()
        self.logger.info("像素映射器初始化完成")

    def _setup_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # === 顶部：网格大小控制 ===
        top = self._build_top_bar()
        main_layout.addWidget(top)

        # === 中间区域 ===
        mid_layout = QHBoxLayout()
        mid_layout.setSpacing(4)

        # 左侧面板
        left_panel = self._build_left_panel()
        mid_layout.addWidget(left_panel, 0)

        # 中心网格
        self.grid_widget = PixelGridWidget(self.model)
        mid_layout.addWidget(self.grid_widget, 1)

        # 右侧DMX面板
        right_panel = self._build_right_panel()
        mid_layout.addWidget(right_panel, 0)

        main_layout.addLayout(mid_layout, 1)

        # === 底部：动画和导出 ===
        bottom = self._build_bottom_bar()
        main_layout.addWidget(bottom)

        self.set_central_content(central)
        self._refresh_dmx_info()

    # ---------- 顶部栏 ----------

    def _build_top_bar(self) -> QWidget:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        layout.addWidget(QLabel("行数:"))
        self.spin_rows = QSpinBox()
        self.spin_rows.setRange(4, 64)
        self.spin_rows.setValue(16)
        layout.addWidget(self.spin_rows)

        layout.addWidget(QLabel("列数:"))
        self.spin_cols = QSpinBox()
        self.spin_cols.setRange(4, 64)
        self.spin_cols.setValue(16)
        layout.addWidget(self.spin_cols)

        btn_apply = QPushButton("应用")
        btn_apply.clicked.connect(self._apply_grid_size)
        layout.addWidget(btn_apply)

        layout.addStretch()

        self.chk_show_dmx = QCheckBox("显示DMX地址")
        self.chk_show_dmx.toggled.connect(self._toggle_dmx_display)
        layout.addWidget(self.chk_show_dmx)

        return frame

    # ---------- 左侧面板 ----------

    def _build_left_panel(self) -> QWidget:
        frame = QFrame()
        frame.setFixedWidth(180)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        # 颜色选择
        grp_color = QGroupBox("颜色")
        cl = QVBoxLayout(grp_color)
        self.color_preview = QPushButton()
        self.color_preview.setFixedSize(160, 40)
        self.color_preview.setStyleSheet("background-color: #ff0000; border: 1px solid #666;")
        self.color_preview.clicked.connect(self._pick_color)
        cl.addWidget(self.color_preview)

        # 预设颜色
        preset_colors = [
            ("红色", 255, 0, 0), ("绿色", 0, 255, 0), ("蓝色", 0, 0, 255),
            ("黄色", 255, 255, 0), ("青色", 0, 255, 255), ("品红", 255, 0, 255),
            ("白色", 255, 255, 255), ("橙色", 255, 128, 0), ("紫色", 128, 0, 255),
        ]
        preset_row = QHBoxLayout()
        for i, (name, r, g, b) in enumerate(preset_colors):
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #555;")
            btn.setToolTip(name)
            btn.clicked.connect(lambda _, rr=r, gg=g, bb=b: self._set_preset_color(rr, gg, bb))
            preset_row.addWidget(btn)
            if (i + 1) % 3 == 0:
                cl.addLayout(preset_row)
                preset_row = QHBoxLayout()
        if preset_row.count() > 0:
            cl.addLayout(preset_row)
        layout.addWidget(grp_color)

        # 画笔工具
        grp_brush = QGroupBox("画笔工具")
        bl = QVBoxLayout(grp_brush)
        self.combo_brush = QComboBox()
        self.combo_brush.addItems(["画笔", "橡皮擦", "填充"])
        self.combo_brush.currentIndexChanged.connect(self._on_brush_changed)
        bl.addWidget(self.combo_brush)
        layout.addWidget(grp_brush)

        # 图案预设
        grp_pattern = QGroupBox("图案预设")
        pl = QVBoxLayout(grp_pattern)
        self.combo_pattern = QComboBox()
        self.combo_pattern.addItems(["彩虹渐变", "颜色波浪", "棋盘格", "螺旋"])
        pl.addWidget(self.combo_pattern)
        btn_apply_pattern = QPushButton("应用图案")
        btn_apply_pattern.clicked.connect(self._apply_preset_pattern)
        pl.addWidget(btn_apply_pattern)
        btn_gen_anim = QPushButton("生成动画")
        btn_gen_anim.setToolTip("基于当前图案生成30帧动画")
        btn_gen_anim.clicked.connect(self._generate_animation)
        pl.addWidget(btn_gen_anim)
        layout.addWidget(grp_pattern)

        layout.addStretch()
        return frame

    # ---------- 右侧面板 ----------

    def _build_right_panel(self) -> QWidget:
        frame = QFrame()
        frame.setFixedWidth(200)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        grp_dmx = QGroupBox("DMX映射")
        dl = QGridLayout(grp_dmx)

        dl.addWidget(QLabel("起始地址:"), 0, 0)
        self.spin_dmx_start = QSpinBox()
        self.spin_dmx_start.setRange(1, 512)
        self.spin_dmx_start.setValue(1)
        self.spin_dmx_start.valueChanged.connect(self._on_dmx_start_changed)
        dl.addWidget(self.spin_dmx_start, 0, 1)

        dl.addWidget(QLabel("每像素通道:"), 1, 0)
        self.combo_ch = QComboBox()
        self.combo_ch.addItems(["1 (单色)", "2", "3 (RGB)", "4 (RGBW)"])
        self.combo_ch.setCurrentIndex(2)
        self.combo_ch.currentIndexChanged.connect(self._on_ch_changed)
        dl.addWidget(self.combo_ch, 1, 1)

        dl.addWidget(QLabel("总像素数:"), 2, 0)
        self.lbl_total_pixels = QLabel("256")
        dl.addWidget(self.lbl_total_pixels, 2, 1)

        dl.addWidget(QLabel("总通道数:"), 3, 0)
        self.lbl_total_channels = QLabel("768")
        dl.addWidget(self.lbl_total_channels, 3, 1)

        dl.addWidget(QLabel("DMX地址范围:"), 4, 0)
        self.lbl_dmx_range = QLabel("1 - 768")
        dl.addWidget(self.lbl_dmx_range, 4, 1)

        chk_auto = QCheckBox("自动分配地址")
        chk_auto.setChecked(True)
        chk_auto.toggled.connect(self._on_auto_assign)
        dl.addWidget(chk_auto, 5, 0, 1, 2)

        layout.addWidget(grp_dmx)

        # 像素信息
        grp_info = QGroupBox("像素信息")
        il = QVBoxLayout(grp_info)
        self.lbl_pixel_info = QLabel("行: - 列: -\n地址: -\n颜色: -")
        self.lbl_pixel_info.setWordWrap(True)
        il.addWidget(self.lbl_pixel_info)
        layout.addWidget(grp_info)

        layout.addStretch()

        # 清除按钮
        btn_clear = QPushButton("清除所有像素")
        btn_clear.clicked.connect(self._clear_all)
        layout.addWidget(btn_clear)

        return frame

    # ---------- 底部栏 ----------

    def _build_bottom_bar(self) -> QWidget:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(4, 4, 4, 4)

        # 动画控制
        layout.addWidget(QLabel("动画:"))
        self.btn_play = QPushButton("▶ 播放")
        self.btn_play.clicked.connect(self._toggle_animation)
        layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("⏹ 停止")
        self.btn_stop.clicked.connect(self._stop_animation)
        layout.addWidget(self.btn_stop)

        layout.addWidget(QLabel("速度:"))
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(1, 60)
        self.slider_speed.setValue(15)
        self.slider_speed.setFixedWidth(120)
        layout.addWidget(self.slider_speed)

        self.lbl_speed = QLabel("15 fps")
        self.slider_speed.valueChanged.connect(lambda v: self.lbl_speed.setText(f"{v} fps"))
        layout.addWidget(self.lbl_speed)

        self.lbl_frame = QLabel("帧: 0/0")
        layout.addWidget(self.lbl_frame)

        layout.addStretch()

        # 导出
        btn_export_json = QPushButton("📦 导出JSON")
        btn_export_json.clicked.connect(self._export_json)
        layout.addWidget(btn_export_json)

        return frame

    # ====================================================================
    # 事件处理
    # ====================================================================

    def _apply_grid_size(self):
        rows = self.spin_rows.value()
        cols = self.spin_cols.value()
        self.model.resize(rows, cols)
        self.grid_widget.update_from_model()
        self._refresh_dmx_info()
        self.logger.info(f"网格大小调整为 {rows}×{cols}")

    def _pick_color(self):
        color = QColorDialog.getColor(self._current_color, self, "选择颜色")
        if color.isValid():
            self._current_color = color
            self.color_preview.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
            self.grid_widget.set_brush_color(color)

    def _set_preset_color(self, r, g, b):
        self._current_color = QColor(r, g, b)
        self.color_preview.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #666;")
        self.grid_widget.set_brush_color(self._current_color)

    def _on_brush_changed(self, idx):
        modes = ["paint", "erase", "fill"]
        self.grid_widget.set_brush_mode(modes[idx])

    def _apply_preset_pattern(self):
        names = ["rainbow", "wave", "checker", "spiral"]
        idx = self.combo_pattern.currentIndex()
        self.model.apply_pattern(names[idx])
        self.grid_widget.update()
        self.logger.info(f"已应用图案: {self.combo_pattern.currentText()}")

    def _generate_animation(self):
        names = ["rainbow", "wave", "checker", "spiral"]
        idx = self.combo_pattern.currentIndex()
        self.model.generate_animation(names[idx], frame_count=30)
        self._anim_frame_idx = 0
        if self.model.frame_count > 0:
            self.model.load_frame(0)
            self.grid_widget.update()
        self._refresh_frame_label()
        self.logger.info(f"已生成 {self.model.frame_count} 帧动画")

    def _toggle_animation(self):
        if self.model.frame_count == 0:
            QMessageBox.information(self, "提示", "请先生成动画帧（点击【生成动画】按钮）")
            return
        if self._anim_running:
            self._pause_animation()
        else:
            self._start_animation()

    def _start_animation(self):
        self._anim_running = True
        self.btn_play.setText("⏸ 暂停")
        fps = self.slider_speed.value()
        self._anim_timer.start(max(16, 1000 // fps))
        self.logger.info(f"动画播放中 ({fps} fps)")

    def _pause_animation(self):
        self._anim_running = False
        self.btn_play.setText("▶ 播放")
        self._anim_timer.stop()

    def _stop_animation(self):
        self._anim_running = False
        self._anim_timer.stop()
        self.btn_play.setText("▶ 播放")
        self._anim_frame_idx = 0
        if self.model.frame_count > 0:
            self.model.load_frame(0)
            self.grid_widget.update()
        self._refresh_frame_label()

    def _on_anim_tick(self):
        if self.model.frame_count == 0:
            self._stop_animation()
            return
        self._anim_frame_idx = (self._anim_frame_idx + 1) % self.model.frame_count
        self.model.load_frame(self._anim_frame_idx)
        self.grid_widget.update()
        self._refresh_frame_label()

    def _refresh_frame_label(self):
        self.lbl_frame.setText(f"帧: {self._anim_frame_idx + 1}/{self.model.frame_count}")

    def _toggle_dmx_display(self, checked):
        self.grid_widget.set_show_dmx(checked)
        self.grid_widget.update()

    def _on_dmx_start_changed(self, val):
        self.model.set_dmx_start(val)
        self._refresh_dmx_info()

    def _on_ch_changed(self, idx):
        ch_map = [1, 2, 3, 4]
        self.model.set_channels_per_pixel(ch_map[idx])
        self._refresh_dmx_info()

    def _on_auto_assign(self, checked):
        self.model.dmx_mapping.auto_assign = checked
        if checked:
            self.model.auto_assign_dmx()
            self._refresh_dmx_info()

    def _refresh_dmx_info(self):
        m = self.model
        self.lbl_total_pixels.setText(str(m.total_pixels))
        self.lbl_total_channels.setText(str(m.total_channels))
        end_addr = m.dmx_mapping.start_address + m.total_channels - 1
        self.lbl_dmx_range.setText(f"{m.dmx_mapping.start_address} - {end_addr}")

    def _clear_all(self):
        self.model.clear_all()
        self.grid_widget.update()
        self.logger.info("已清除所有像素")

    def _export_json(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出像素映射", "", "JSON文件 (*.json)")
        if path:
            try:
                data = self.model.export_to_dict()
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                self.logger.info(f"像素映射已导出: {path}")
                QMessageBox.information(self, "导出成功", f"已导出到:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def closeEvent(self, event):
        """关闭窗口时停止动画定时器"""
        if self._anim_timer.isActive():
            self._anim_timer.stop()
        super().closeEvent(event)


# ====================================================================
# 入口
# ====================================================================

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = PixelMapperWindow()
    window.show()
    if not QApplication.instance().parent():
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
            QMessageBox.critical(None, "PixelMapper - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
