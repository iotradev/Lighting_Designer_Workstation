"""
Cue设计器 - 灯光演出Cue列表管理与预览工具
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QDoubleSpinBox, QSpinBox, QComboBox, QFileDialog, QMessageBox,
    QHeaderView, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QBrush

from cue_engine import Cue, CueList, CrossfadeInterpolator, EffectGenerator, EffectType


class DMXGridWidget(QWidget):
    """512通道DMX值网格控件"""

    def __init__(self, cols=32, rows=16, parent=None):
        super().__init__(parent)
        self.cols = cols
        self.rows = rows
        self.values = [0] * 512
        self.selected_channels = set()
        self.setMinimumSize(400, 200)

    def set_values(self, values):
        self.values = (values + [0]*512)[:512]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        cell_w = w / self.cols
        cell_h = h / self.rows

        for i in range(512):
            row = i // self.cols
            col = i % self.cols
            if row >= self.rows:
                break
            val = self.values[i]
            x = col * cell_w
            y = row * cell_h

            if i in self.selected_channels:
                painter.setPen(QColor(255, 255, 0))
            else:
                painter.setPen(QColor(60, 60, 60))

            color = QColor(0, val, 0) if val > 0 else QColor(30, 30, 30)
            painter.fillRect(int(x)+1, int(y)+1, int(cell_w)-2, int(cell_h)-2, QBrush(color))

        painter.end()


class DMXEditGrid(QWidget):
    """可编辑的DMX通道网格(16x32)"""
    channel_changed = Signal(int, int)  # channel(0-based), value

    def __init__(self, parent=None):
        super().__init__(parent)
        self.values = [0] * 512
        self.spinboxes = []
        layout = QGridLayout(self)
        layout.setSpacing(1)
        self._build_grid()

    def _build_grid(self):
        layout = self.layout()
        for i in range(512):
            row = i // 32
            col = i % 32
            sb = QSpinBox()
            sb.setRange(0, 255)
            sb.setFixedSize(40, 22)
            sb.setStyleSheet("font-size:9px;")
            sb.setToolTip(f"CH {i+1}")
            sb.valueChanged.connect(lambda v, ch=i: self._on_change(ch, v))
            layout.addWidget(sb, row, col)
            self.spinboxes.append(sb)

    def _on_change(self, channel, value):
        self.values[channel] = value
        self.channel_changed.emit(channel, value)

    def set_values(self, values):
        self.values = (values + [0]*512)[:512]
        for i, sb in enumerate(self.spinboxes):
            sb.blockSignals(True)
            sb.setValue(self.values[i])
            sb.blockSignals(False)

    def get_values(self):
        return self.values[:]


class CueDesignerWindow(BaseToolWindow):
    """Cue设计器主窗口"""

    def __init__(self):
        super().__init__('CueDesigner', 'Cue设计器', '1.0.0', 1400, 900)

        self.cue_list = CueList()
        self.current_index = -1
        self.crossfade_timer = QTimer()
        self.crossfade_timer.timeout.connect(self._crossfade_step)
        self.crossfade_t = 0.0
        self.crossfade_step_size = 0.0
        self.crossfade_from = [0]*512
        self.crossfade_to = [0]*512
        self.crossfade_duration = 3.0
        self.is_crossfading = False

        self.chase_timer = QTimer()
        self.chase_timer.timeout.connect(self._chase_step)
        self.chase_index = 0
        self.is_chase_running = False

        self.effect_timer = QTimer()
        self.effect_timer.timeout.connect(self._effect_step)
        self.effect_start_time = 0.0
        self.is_effect_running = False

        self._build_ui()
        self._refresh_cue_table()

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # 顶部：三栏布局
        top_layout = QHBoxLayout()

        # 左栏：Cue列表
        left_panel = self._build_cue_list_panel()
        top_layout.addWidget(left_panel, 2)

        # 中栏：Cue编辑 + 通道网格
        center_panel = self._build_center_panel()
        top_layout.addWidget(center_panel, 5)

        # 右栏：效果生成器
        right_panel = self._build_effect_panel()
        top_layout.addWidget(right_panel, 2)

        main_layout.addLayout(top_layout, 8)

        # 底部：预览控制
        bottom_panel = self._build_preview_panel()
        main_layout.addWidget(bottom_panel, 2)

        self.set_central_content(central)

    def _build_cue_list_panel(self):
        group = QGroupBox("Cue列表")
        layout = QVBoxLayout(group)

        self.cue_table = QTableWidget()
        self.cue_table.setColumnCount(5)
        self.cue_table.setHorizontalHeaderLabels(['Cue#', '名称', '淡入(s)', '淡出(s)', '延迟(s)'])
        self.cue_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cue_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cue_table.setSelectionMode(QTableWidget.SingleSelection)
        self.cue_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.cue_table.cellClicked.connect(self._on_cue_selected)
        self.cue_table.setSortingEnabled(True)
        layout.addWidget(self.cue_table)

        # 操作按钮
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加")
        self.btn_edit = QPushButton("编辑")
        self.btn_delete = QPushButton("删除")
        self.btn_up = QPushButton("上移")
        self.btn_down = QPushButton("下移")

        self.btn_add.clicked.connect(self._add_cue)
        self.btn_edit.clicked.connect(self._edit_cue)
        self.btn_delete.clicked.connect(self._delete_cue)
        self.btn_up.clicked.connect(self._move_up)
        self.btn_down.clicked.connect(self._move_down)

        for b in [self.btn_add, self.btn_edit, self.btn_delete, self.btn_up, self.btn_down]:
            btn_layout.addWidget(b)
        layout.addLayout(btn_layout)

        # 文件操作
        file_layout = QHBoxLayout()
        btn_save = QPushButton("保存JSON")
        btn_load = QPushButton("加载JSON")
        btn_csv = QPushButton("导出CSV")
        btn_save.clicked.connect(self._save_json)
        btn_load.clicked.connect(self._load_json)
        btn_csv.clicked.connect(self._export_csv)
        for b in [btn_save, btn_load, btn_csv]:
            file_layout.addWidget(b)
        layout.addLayout(file_layout)

        return group

    def _build_center_panel(self):
        group = QGroupBox("Cue编辑器")
        layout = QVBoxLayout(group)

        # Cue参数编辑
        param_layout = QGridLayout()
        param_layout.addWidget(QLabel("Cue编号:"), 0, 0)
        self.spin_cue_num = QDoubleSpinBox()
        self.spin_cue_num.setRange(0, 9999)
        self.spin_cue_num.setDecimals(1)
        param_layout.addWidget(self.spin_cue_num, 0, 1)

        param_layout.addWidget(QLabel("名称:"), 0, 2)
        self.edit_name = QLineEdit()
        param_layout.addWidget(self.edit_name, 0, 3)

        param_layout.addWidget(QLabel("淡入时间(s):"), 1, 0)
        self.spin_fadein = QDoubleSpinBox()
        self.spin_fadein.setRange(0, 600)
        self.spin_fadein.setDecimals(1)
        param_layout.addWidget(self.spin_fadein, 1, 1)

        param_layout.addWidget(QLabel("淡出时间(s):"), 1, 2)
        self.spin_fadeout = QDoubleSpinBox()
        self.spin_fadeout.setRange(0, 600)
        self.spin_fadeout.setDecimals(1)
        param_layout.addWidget(self.spin_fadeout, 1, 3)

        param_layout.addWidget(QLabel("延迟时间(s):"), 2, 0)
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setRange(0, 600)
        self.spin_delay.setDecimals(1)
        param_layout.addWidget(self.spin_delay, 2, 1)

        layout.addLayout(param_layout)

        # 通道值编辑网格
        layout.addWidget(QLabel("通道值 (16×32):"))
        scroll = QScrollArea()
        self.dmx_edit_grid = DMXEditGrid()
        scroll.setWidget(self.dmx_edit_grid)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        return group

    def _build_effect_panel(self):
        group = QGroupBox("效果生成器")
        layout = QVBoxLayout(group)

        layout.addWidget(QLabel("效果类型:"))
        self.combo_effect = QComboBox()
        self.combo_effect.addItems(["正弦波", "随机闪烁", "随机颜色", "追逐"])
        layout.addWidget(self.combo_effect)

        layout.addWidget(QLabel("速度:"))
        self.spin_speed = QDoubleSpinBox()
        self.spin_speed.setRange(0.1, 20.0)
        self.spin_speed.setValue(1.0)
        self.spin_speed.setSingleStep(0.1)
        layout.addWidget(self.spin_speed)

        layout.addWidget(QLabel("振幅:"))
        self.spin_amplitude = QDoubleSpinBox()
        self.spin_amplitude.setRange(0, 1.0)
        self.spin_amplitude.setValue(0.5)
        self.spin_amplitude.setSingleStep(0.05)
        layout.addWidget(self.spin_amplitude)

        layout.addWidget(QLabel("起始通道:"))
        self.spin_ch_start = QSpinBox()
        self.spin_ch_start.setRange(1, 512)
        self.spin_ch_start.setValue(1)
        layout.addWidget(self.spin_ch_start)

        layout.addWidget(QLabel("结束通道:"))
        self.spin_ch_end = QSpinBox()
        self.spin_ch_end.setRange(1, 512)
        self.spin_ch_end.setValue(16)
        layout.addWidget(self.spin_ch_end)

        self.btn_apply_effect = QPushButton("应用效果")
        self.btn_apply_effect.clicked.connect(self._apply_effect)
        layout.addWidget(self.btn_apply_effect)

        self.btn_preview_effect = QPushButton("预览效果")
        self.btn_preview_effect.clicked.connect(self._toggle_effect_preview)
        layout.addWidget(self.btn_preview_effect)

        layout.addStretch()

        # 追逐模式
        chase_group = QGroupBox("追逐模式")
        chase_layout = QVBoxLayout(chase_group)
        chase_layout.addWidget(QLabel("追逐速度(s):"))
        self.spin_chase_speed = QDoubleSpinBox()
        self.spin_chase_speed.setRange(0.1, 30.0)
        self.spin_chase_speed.setValue(2.0)
        self.spin_chase_speed.setSingleStep(0.1)
        chase_layout.addWidget(self.spin_chase_speed)

        self.btn_chase_start = QPushButton("启动追逐")
        self.btn_chase_start.clicked.connect(self._toggle_chase)
        chase_layout.addWidget(self.btn_chase_start)
        layout.addWidget(chase_group)

        return group

    def _build_preview_panel(self):
        group = QGroupBox("预览控制")
        layout = QHBoxLayout(group)

        # 控制按钮
        ctrl_layout = QVBoxLayout()
        self.btn_go = QPushButton("GO")
        self.btn_go.setStyleSheet("font-size:16px; font-weight:bold; background:#4CAF50; color:white; padding:8px;")
        self.btn_go.clicked.connect(self._go_next)

        self.btn_back = QPushButton("BACK")
        self.btn_back.setStyleSheet("font-size:14px; background:#2196F3; color:white; padding:6px;")
        self.btn_back.clicked.connect(self._go_back)

        self.btn_stop = QPushButton("STOP")
        self.btn_stop.setStyleSheet("font-size:14px; background:#f44336; color:white; padding:6px;")
        self.btn_stop.clicked.connect(self._stop_crossfade)

        ctrl_layout.addWidget(self.btn_go)
        ctrl_layout.addWidget(self.btn_back)
        ctrl_layout.addWidget(self.btn_stop)
        layout.addLayout(ctrl_layout)

        # 当前Cue信息
        info_layout = QVBoxLayout()
        self.label_current_cue = QLabel("当前Cue: 无")
        self.label_current_cue.setStyleSheet("font-size:14px; font-weight:bold;")
        self.label_crossfade_status = QLabel("状态: 就绪")
        self.label_crossfade_status.setStyleSheet("font-size:12px; color:gray;")
        info_layout.addWidget(self.label_current_cue)
        info_layout.addWidget(self.label_crossfade_status)
        layout.addLayout(info_layout)

        # DMX预览
        layout.addWidget(QLabel("DMX预览:"))
        self.dmx_preview = DMXGridWidget(cols=32, rows=16)
        layout.addWidget(self.dmx_preview)

        return group

    # ---- Cue列表操作 ----

    def _refresh_cue_table(self):
        self.cue_table.setSortingEnabled(False)
        self.cue_table.setRowCount(len(self.cue_list.cues))
        for i, cue in enumerate(self.cue_list.cues):
            self.cue_table.setItem(i, 0, QTableWidgetItem(str(cue.cue_number)))
            self.cue_table.setItem(i, 1, QTableWidgetItem(cue.name))
            self.cue_table.setItem(i, 2, QTableWidgetItem(str(cue.fade_in)))
            self.cue_table.setItem(i, 3, QTableWidgetItem(str(cue.fade_out)))
            self.cue_table.setItem(i, 4, QTableWidgetItem(str(cue.delay)))
        self.cue_table.setSortingEnabled(True)

    def _on_cue_selected(self, row, col):
        self.current_index = row
        cue = self.cue_list.get_cue(row)
        if cue:
            self._load_cue_to_editor(cue)
            self.dmx_preview.set_values(cue.channel_values)
            self.label_current_cue.setText(f"当前Cue: {cue.cue_number} - {cue.name}")

    def _load_cue_to_editor(self, cue: Cue):
        self.spin_cue_num.setValue(cue.cue_number)
        self.edit_name.setText(cue.name)
        self.spin_fadein.setValue(cue.fade_in)
        self.spin_fadeout.setValue(cue.fade_out)
        self.spin_delay.setValue(cue.delay)
        self.dmx_edit_grid.set_values(cue.channel_values)

    def _get_editor_cue(self) -> Cue:
        cue = Cue(
            cue_number=self.spin_cue_num.value(),
            name=self.edit_name.text(),
            fade_in=self.spin_fadein.value(),
            fade_out=self.spin_fadeout.value(),
            delay=self.spin_delay.value(),
        )
        cue.channel_values = self.dmx_edit_grid.get_values()
        return cue

    def _add_cue(self):
        cue = self._get_editor_cue()
        self.cue_list.add_cue(cue)
        self._refresh_cue_table()
        self.logger.info(f"添加Cue: {cue.cue_number} - {cue.name}")

    def _edit_cue(self):
        if self.current_index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个Cue")
            return
        cue = self._get_editor_cue()
        self.cue_list.cues[self.current_index] = cue
        self.cue_list.cues.sort(key=lambda c: c.cue_number)
        self._refresh_cue_table()
        self.logger.info(f"编辑Cue: {cue.cue_number} - {cue.name}")

    def _delete_cue(self):
        if self.current_index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个Cue")
            return
        self.cue_list.remove_cue(self.current_index)
        self.current_index = -1
        self._refresh_cue_table()

    def _move_up(self):
        if self.current_index > 0:
            self.current_index = self.cue_list.move_up(self.current_index)
            self._refresh_cue_table()
            self.cue_table.selectRow(self.current_index)

    def _move_down(self):
        if 0 <= self.current_index < len(self.cue_list.cues) - 1:
            self.current_index = self.cue_list.move_down(self.current_index)
            self._refresh_cue_table()
            self.cue_table.selectRow(self.current_index)

    # ---- 文件操作 ----

    def _save_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存Cue列表", "", "JSON文件 (*.json)")
        if path:
            self.cue_list.save_to_json(path)
            self.logger.info(f"保存Cue列表: {path}")

    def _load_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载Cue列表", "", "JSON文件 (*.json)")
        if path:
            self.cue_list.load_from_json(path)
            self._refresh_cue_table()
            self.logger.info(f"加载Cue列表: {path}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出CSV", "", "CSV文件 (*.csv)")
        if path:
            self.cue_list.export_csv(path)
            self.logger.info(f"导出CSV: {path}")

    # ---- 预览控制 ----

    def _go_next(self):
        """执行下一个Cue（带交叉渐变）"""
        if len(self.cue_list.cues) == 0:
            return
        next_idx = self.current_index + 1
        if next_idx >= len(self.cue_list.cues):
            next_idx = 0

        if self.current_index >= 0:
            from_cue = self.cue_list.cues[self.current_index]
        else:
            from_cue = Cue()  # 全黑

        to_cue = self.cue_list.cues[next_idx]
        self._start_crossfade(from_cue.channel_values, to_cue.channel_values,
                              to_cue.fade_in, next_idx)

    def _go_back(self):
        """回到上一个Cue"""
        if len(self.cue_list.cues) == 0:
            return
        prev_idx = max(0, self.current_index - 1)
        if self.current_index < 0:
            return

        from_cue = self.cue_list.cues[self.current_index]
        to_cue = self.cue_list.cues[prev_idx]
        self._start_crossfade(from_cue.channel_values, to_cue.channel_values,
                              to_cue.fade_in, prev_idx)

    def _start_crossfade(self, from_vals, to_vals, duration, target_idx):
        self.crossfade_from = from_vals[:]
        self.crossfade_to = to_vals[:]
        self.crossfade_duration = max(duration, 0.1)
        self.crossfade_t = 0.0
        self.crossfade_step_size = 0.05 / self.crossfade_duration  # 50ms步进
        self.is_crossfading = True
        self.label_crossfade_status.setText(f"状态: 渐变中 -> Cue {self.cue_list.cues[target_idx].cue_number}")
        self.crossfade_timer.start(50)  # 20fps
        self.current_index = target_idx
        self.cue_table.selectRow(target_idx)
        cue = self.cue_list.cues[target_idx]
        self.label_current_cue.setText(f"当前Cue: {cue.cue_number} - {cue.name}")

    def _crossfade_step(self):
        self.crossfade_t += self.crossfade_step_size
        t = CrossfadeInterpolator.ease_in_out(min(1.0, self.crossfade_t))
        values = CrossfadeInterpolator.lerp(self.crossfade_from, self.crossfade_to, t)
        self.dmx_preview.set_values(values)
        self.dmx_edit_grid.set_values(values)

        if self.crossfade_t >= 1.0:
            self.crossfade_timer.stop()
            self.is_crossfading = False
            self.label_crossfade_status.setText("状态: 就绪")

    def _stop_crossfade(self):
        self.crossfade_timer.stop()
        self.is_crossfading = False
        self.chase_timer.stop()
        self.is_chase_running = False
        self.label_crossfade_status.setText("状态: 已停止")

    # ---- 追逐模式 ----

    def _toggle_chase(self):
        if self.is_chase_running:
            self.chase_timer.stop()
            self.is_chase_running = False
            self.btn_chase_start.setText("启动追逐")
            self.label_crossfade_status.setText("状态: 就绪")
        else:
            if len(self.cue_list.cues) < 2:
                QMessageBox.warning(self, "提示", "至少需要2个Cue来启动追逐")
                return
            self.chase_index = 0
            self.is_chase_running = True
            self.btn_chase_start.setText("停止追逐")
            speed = int(self.spin_chase_speed.value() * 1000)
            self.chase_timer.start(speed)
            self.label_crossfade_status.setText("状态: 追逐中")

    def _chase_step(self):
        if not self.cue_list.cues:
            return
        cue = self.cue_list.cues[self.chase_index % len(self.cue_list.cues)]
        self.dmx_preview.set_values(cue.channel_values)
        self.dmx_edit_grid.set_values(cue.channel_values)
        self.current_index = self.chase_index % len(self.cue_list.cues)
        self.cue_table.selectRow(self.current_index)
        self.label_current_cue.setText(f"当前Cue: {cue.cue_number} - {cue.name}")
        self.chase_index += 1

    # ---- 效果生成器 ----

    def _apply_effect(self):
        """将效果应用到当前Cue的选中通道"""
        if self.current_index < 0:
            QMessageBox.warning(self, "提示", "请先选择一个Cue")
            return

        ch_start = self.spin_ch_start.value() - 1
        ch_end = self.spin_ch_end.value()
        num_ch = ch_end - ch_start
        effect_type = self.combo_effect.currentIndex()
        speed = self.spin_speed.value()
        amplitude = self.spin_amplitude.value()

        cue = self.cue_list.cues[self.current_index]
        if effect_type == 0:  # 正弦波
            vals = EffectGenerator.sine_effect(list(range(ch_start, ch_end)), speed, amplitude)
        elif effect_type == 1:  # 随机闪烁
            vals = EffectGenerator.random_effect(num_ch, speed)
        elif effect_type == 2:  # 随机颜色
            vals = EffectGenerator.random_color_effect(num_ch)
        else:  # 追逐
            vals = EffectGenerator.chase_effect(num_ch, speed, 0)

        for i, v in enumerate(vals):
            if ch_start + i < 512:
                cue.channel_values[ch_start + i] = v

        self.dmx_edit_grid.set_values(cue.channel_values)
        self.dmx_preview.set_values(cue.channel_values)
        self.logger.info(f"应用效果到通道 {ch_start+1}-{ch_end}")

    def _toggle_effect_preview(self):
        if self.is_effect_running:
            self.effect_timer.stop()
            self.is_effect_running = False
            self.btn_preview_effect.setText("预览效果")
        else:
            self.effect_start_time = time.time()
            self.is_effect_running = True
            self.btn_preview_effect.setText("停止预览")
            self.effect_timer.start(50)

    def _effect_step(self):
        elapsed = time.time() - self.effect_start_time
        ch_start = self.spin_ch_start.value() - 1
        ch_end = self.spin_ch_end.value()
        num_ch = ch_end - ch_start
        effect_type = self.combo_effect.currentIndex()
        speed = self.spin_speed.value()
        amplitude = self.spin_amplitude.value()

        if effect_type == 0:
            vals = EffectGenerator.sine_effect(list(range(ch_start, ch_end)), speed, amplitude, time_val=elapsed)
        elif effect_type == 1:
            vals = EffectGenerator.random_effect(num_ch, speed)
        elif effect_type == 2:
            vals = EffectGenerator.random_color_effect(num_ch)
        else:
            vals = EffectGenerator.chase_effect(num_ch, speed, elapsed)

        preview_vals = [0] * 512
        for i, v in enumerate(vals):
            if ch_start + i < 512:
                preview_vals[ch_start + i] = v

        self.dmx_preview.set_values(preview_vals)


if __name__ == '__main__':
    import traceback
    try:

        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = CueDesignerWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "CueDesigner - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
