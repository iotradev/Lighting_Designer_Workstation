# -*- coding: utf-8 -*-
"""
时间轴编辑器 - 灯光时间线控制
支持关键帧编辑、插值、播放控制和导出
"""
import sys, json, math
from pathlib import Path
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QFormLayout, QHeaderView, QMessageBox, QFileDialog, QSplitter,
    QScrollArea, QFrame, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QRect, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPolygonF, QLinearGradient


class Interpolation(Enum):
    LINEAR = "线性"
    STEP = "阶跃"
    EASE_IN_OUT = "缓入缓出"


class Keyframe:
    """关键帧数据"""
    def __init__(self, time: float, value: float, interp: Interpolation = Interpolation.LINEAR):
        self.time = time
        self.value = value
        self.interp = interp

    def to_dict(self):
        return {"time": self.time, "value": self.value, "interp": self.interp.value}

    @staticmethod
    def from_dict(d):
        interp_map = {"线性": Interpolation.LINEAR, "阶跃": Interpolation.STEP, "缓入缓出": Interpolation.EASE_IN_OUT}
        return Keyframe(d["time"], d["value"], interp_map.get(d.get("interp", "线性"), Interpolation.LINEAR))


class Track:
    """轨道 - 对应一个灯具组或属性"""
    def __init__(self, name: str, attribute: str = "亮度"):
        self.name = name
        self.attribute = attribute
        self.keyframes: list[Keyframe] = []
        self.color = QColor(80, 180, 255)

    def add_keyframe(self, kf: Keyframe):
        self.keyframes.append(kf)
        self.keyframes.sort(key=lambda k: k.time)

    def remove_keyframe(self, index):
        if 0 <= index < len(self.keyframes):
            self.keyframes.pop(index)

    def get_value_at(self, t: float) -> float:
        if not self.keyframes:
            return 0.0
        if t <= self.keyframes[0].time:
            return self.keyframes[0].value
        if t >= self.keyframes[-1].time:
            return self.keyframes[-1].value
        for i in range(len(self.keyframes) - 1):
            k0, k1 = self.keyframes[i], self.keyframes[i + 1]
            if k0.time <= t <= k1.time:
                if k0.interp == Interpolation.STEP:
                    return k0.value
                duration = k1.time - k0.time
                if duration == 0:
                    return k0.value
                progress = (t - k0.time) / duration
                if k0.interp == Interpolation.EASE_IN_OUT:
                    progress = progress * progress * (3 - 2 * progress)
                return k0.value + (k1.value - k0.value) * progress
        return 0.0

    def to_dict(self):
        return {"name": self.name, "attribute": self.attribute, "keyframes": [k.to_dict() for k in self.keyframes]}

    @staticmethod
    def from_dict(d):
        t = Track(d["name"], d.get("attribute", "亮度"))
        t.keyframes = [Keyframe.from_dict(k) for k in d.get("keyframes", [])]
        return t


class TimelineRuler(QWidget):
    """时间轴标尺"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 120.0  # 总时长(秒)
        self.pixels_per_second = 20.0
        self.scroll_offset = 0
        self.setFixedHeight(30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        painter.setPen(QColor(150, 150, 150))
        painter.drawLine(0, h - 1, w, h - 1)

        start_sec = self.scroll_offset / self.pixels_per_second
        end_sec = (self.scroll_offset + w) / self.pixels_per_second
        step = 1.0
        if self.pixels_per_second < 10:
            step = 5.0
        elif self.pixels_per_second < 5:
            step = 10.0

        t = math.floor(start_sec / step) * step
        while t <= end_sec:
            x = int((t * self.pixels_per_second) - self.scroll_offset)
            painter.drawLine(x, h - 10, x, h - 1)
            painter.drawText(x + 3, h - 12, f"{t:.0f}s")
            sub_step = step / 5
            for j in range(1, 5):
                sx = int(((t + j * sub_step) * self.pixels_per_second) - self.scroll_offset)
                painter.drawLine(sx, h - 5, sx, h - 1)
            t += step
        painter.end()


class TimelineTrackWidget(QWidget):
    """单条轨道绘制区"""
    def __init__(self, track: Track, ruler: TimelineRuler, parent=None):
        super().__init__(parent)
        self.track = track
        self.ruler = ruler
        self.setFixedHeight(60)
        self.setMinimumWidth(600)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # 背景
        painter.fillRect(0, 0, w, h, QColor(40, 40, 45))
        painter.setPen(QColor(70, 70, 75))
        painter.drawLine(0, h - 1, w, h - 1)

        pps = self.ruler.pixels_per_second
        off = self.ruler.scroll_offset

        # 连线
        if len(self.track.keyframes) >= 2:
            pen = QPen(self.track.color, 2)
            painter.setPen(pen)
            points = []
            for kf in self.track.keyframes:
                x = kf.time * pps - off
                y = h - (kf.value / 100.0) * (h - 10) - 5
                points.append(QPointF(x, y))
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        # 关键帧点
        for kf in self.track.keyframes:
            x = kf.time * pps - off
            y = h - (kf.value / 100.0) * (h - 10) - 5
            painter.setBrush(self.track.color)
            painter.setPen(QColor(255, 255, 255))
            painter.drawEllipse(QPointF(x, y), 5, 5)

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pps = self.ruler.pixels_per_second
            off = self.ruler.scroll_offset
            t = (event.position().x() + off) / pps
            v = max(0, min(100, (1 - (event.position().y() - 5) / (self.height() - 10))) * 100)
            kf = Keyframe(round(t, 2), round(v, 1))
            self.track.add_keyframe(kf)
            self.update()
            # 通知父级更新表格
            parent = self.parent()
            while parent and not isinstance(parent, TimelineEditor):
                parent = parent.parent()
            if parent:
                parent._update_keyframe_table()


class TimelineEditor(BaseToolWindow):
    """时间轴编辑器 - 主窗口"""
    def __init__(self):
        super().__init__('TimelineEditor', '时间轴编辑器', '1.0.0', 1400, 850)
        self.tracks: list[Track] = []
        self.playing = False
        self.playhead_time = 0.0
        self.play_timer = QTimer(self)
        self.play_timer.timeout.connect(self._on_play_tick)
        self._build_ui()
        self.logger.info("时间轴编辑器初始化完成")

    def _build_ui(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        # 顶部控件
        top = QHBoxLayout()
        top.addWidget(QLabel("总时长(秒):"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(10, 7200)
        self.duration_spin.setValue(120)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        top.addWidget(self.duration_spin)

        top.addWidget(QLabel("缩放:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(5, 100)
        self.zoom_slider.setValue(20)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        top.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("20 px/s")
        top.addWidget(self.zoom_label)
        top.addStretch()
        main_layout.addLayout(top)

        # 分割器: 轨道区 + 关键帧表
        splitter = QSplitter(Qt.Orientation.Vertical)

        # 轨道区
        track_area_widget = QWidget()
        track_area_layout = QVBoxLayout(track_area_widget)

        # 标尺 + 播放头层
        self.ruler = TimelineRuler()
        self.ruler.duration = 120.0

        # 轨道列表区(含标尺)
        self.track_container = QWidget()
        self.track_layout = QVBoxLayout(self.track_container)
        self.track_layout.setContentsMargins(0, 0, 0, 0)
        self.track_layout.setSpacing(0)
        self.track_layout.addWidget(self.ruler)

        scroll = QScrollArea()
        scroll.setWidget(self.track_container)
        scroll.setWidgetResizable(True)
        track_area_layout.addWidget(scroll)

        # 播放控制
        play_layout = QHBoxLayout()
        btn_play = QPushButton("▶ 播放")
        btn_pause = QPushButton("⏸ 暂停")
        btn_stop = QPushButton("⏹ 停止")
        btn_play.clicked.connect(self.play)
        btn_pause.clicked.connect(self.pause)
        btn_stop.clicked.connect(self.stop)
        self.time_label = QLabel("00:00.00 / 02:00.00")
        for b in [btn_play, btn_pause, btn_stop]:
            play_layout.addWidget(b)
        play_layout.addWidget(self.time_label)
        play_layout.addStretch()
        track_area_layout.addLayout(play_layout)

        splitter.addWidget(track_area_widget)

        # 底部: 轨道管理 + 关键帧表
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)

        # 轨道管理
        track_ctrl = QGroupBox("轨道管理")
        tc_layout = QVBoxLayout(track_ctrl)
        btn_add_track = QPushButton("➕ 添加轨道")
        btn_add_track.clicked.connect(self.add_track)
        btn_del_track = QPushButton("🗑️ 删除轨道")
        btn_del_track.clicked.connect(self.delete_track)
        btn_add_kf = QPushButton("📌 添加关键帧")
        btn_add_kf.clicked.connect(self.add_keyframe_dialog)
        btn_del_kf = QPushButton("🗑️ 删除关键帧")
        btn_del_kf.clicked.connect(self.delete_selected_keyframe)
        tc_layout.addWidget(btn_add_track)
        tc_layout.addWidget(btn_del_track)
        tc_layout.addSpacing(10)
        tc_layout.addWidget(btn_add_kf)
        tc_layout.addWidget(btn_del_kf)
        tc_layout.addStretch()
        bottom_layout.addWidget(track_ctrl, 1)

        # 关键帧表
        kf_group = QGroupBox("关键帧列表")
        kf_layout = QVBoxLayout(kf_group)
        self.kf_table = QTableWidget(0, 5)
        self.kf_table.setHorizontalHeaderLabels(["轨道", "时间(秒)", "值", "插值", "索引"])
        self.kf_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.kf_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        kf_layout.addWidget(self.kf_table)
        bottom_layout.addWidget(kf_group, 3)

        splitter.addWidget(bottom)
        splitter.setSizes([500, 250])
        main_layout.addWidget(splitter)

        # 底部操作
        btn_row = QHBoxLayout()
        btn_export = QPushButton("📄 导出Cue列表JSON")
        btn_export.clicked.connect(self.export_cue_json)
        btn_export_tl = QPushButton("💾 保存时间线")
        btn_export_tl.clicked.connect(self.save_timeline)
        btn_load_tl = QPushButton("📂 加载时间线")
        btn_load_tl.clicked.connect(self.load_timeline)
        for b in [btn_export, btn_export_tl, btn_load_tl]:
            btn_row.addWidget(b)
        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        self.set_central_content(central)

    def _on_duration_changed(self, val):
        self.ruler.duration = val
        self.ruler.update()

    def _on_zoom_changed(self, val):
        self.ruler.pixels_per_second = val
        self.zoom_label.setText(f"{val} px/s")
        self._refresh_track_widgets()

    def _refresh_track_widgets(self):
        for i in range(self.track_layout.count()):
            w = self.track_layout.itemAt(i).widget()
            if w and w != self.ruler:
                w.update()
        self.ruler.update()

    def add_track(self):
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("添加轨道")
        form = QFormLayout(dlg)
        name_edit = QLineEdit(f"轨道{len(self.tracks) + 1}")
        attr_combo = QComboBox()
        attr_combo.addItems(["亮度", "颜色", "位置X", "位置Y", "缩放", "频闪", "自定义"])
        form.addRow("轨道名称:", name_edit)
        form.addRow("属性:", attr_combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted and name_edit.text():
            track = Track(name_edit.text(), attr_combo.currentText())
            colors = [QColor(80, 180, 255), QColor(255, 140, 80), QColor(80, 255, 140),
                      QColor(255, 80, 180), QColor(180, 80, 255), QColor(255, 255, 80)]
            track.color = colors[len(self.tracks) % len(colors)]
            self.tracks.append(track)
            tw = TimelineTrackWidget(track, self.ruler, self.track_container)
            self.track_layout.addWidget(tw)
            self.logger.info(f"已添加轨道: {track.name}")

    def delete_track(self):
        idx = len(self.tracks) - 1
        if idx < 0:
            QMessageBox.warning(self, "提示", "没有可删除的轨道")
            return
        # 删除最后一条轨道
        self.tracks.pop()
        item = self.track_layout.takeAt(self.track_layout.count() - 1)
        if item.widget():
            item.widget().deleteLater()
        self._update_keyframe_table()

    def add_keyframe_dialog(self):
        if not self.tracks:
            QMessageBox.warning(self, "提示", "请先添加轨道")
            return
        from PySide6.QtWidgets import QDialog, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("添加关键帧")
        form = QFormLayout(dlg)
        track_combo = QComboBox()
        for t in self.tracks:
            track_combo.addItem(t.name)
        time_spin = QDoubleSpinBox()
        time_spin.setRange(0, 9999)
        time_spin.setSuffix(" 秒")
        value_spin = QDoubleSpinBox()
        value_spin.setRange(0, 100)
        value_spin.setSuffix(" %")
        interp_combo = QComboBox()
        interp_combo.addItems(["线性", "阶跃", "缓入缓出"])
        form.addRow("轨道:", track_combo)
        form.addRow("时间:", time_spin)
        form.addRow("值:", value_spin)
        form.addRow("插值:", interp_combo)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            interp_map = {"线性": Interpolation.LINEAR, "阶跃": Interpolation.STEP, "缓入缓出": Interpolation.EASE_IN_OUT}
            kf = Keyframe(time_spin.value(), value_spin.value(), interp_map[interp_combo.currentText()])
            self.tracks[track_combo.currentIndex()].add_keyframe(kf)
            self._update_keyframe_table()
            self._refresh_track_widgets()

    def delete_selected_keyframe(self):
        row = self.kf_table.currentRow()
        if row < 0:
            return
        track_idx = self.kf_table.item(row, 4)
        if track_idx:
            ti = int(track_idx.text())
            if 0 <= ti < len(self.tracks):
                kf_idx_text = self.kf_table.item(row, 1).text()
                # Find by time
                t = float(kf_idx_text.replace('s', ''))
                for i, kf in enumerate(self.tracks[ti].keyframes):
                    if abs(kf.time - t) < 0.01:
                        self.tracks[ti].remove_keyframe(i)
                        break
                self._update_keyframe_table()
                self._refresh_track_widgets()

    def _update_keyframe_table(self):
        rows = []
        for ti, track in enumerate(self.tracks):
            for kf in track.keyframes:
                rows.append((track.name, f"{kf.time:.2f}", f"{kf.value:.1f}", kf.interp.value, str(ti)))
        self.kf_table.setRowCount(len(rows))
        for i, (name, t, v, interp, idx) in enumerate(rows):
            self.kf_table.setItem(i, 0, QTableWidgetItem(name))
            self.kf_table.setItem(i, 1, QTableWidgetItem(t))
            self.kf_table.setItem(i, 2, QTableWidgetItem(v))
            self.kf_table.setItem(i, 3, QTableWidgetItem(interp))
            self.kf_table.setItem(i, 4, QTableWidgetItem(idx))

    def play(self):
        if not self.playing:
            self.playing = True
            self.play_timer.start(50)  # 20fps
            self.logger.info("播放开始")

    def pause(self):
        self.playing = False
        self.play_timer.stop()

    def stop(self):
        self.playing = False
        self.play_timer.stop()
        self.playhead_time = 0.0
        self._update_time_label()

    def _on_play_tick(self):
        self.playhead_time += 0.05
        if self.playhead_time >= self.ruler.duration:
            self.playhead_time = 0.0
        self._update_time_label()
        self._refresh_track_widgets()

    def _update_time_label(self):
        t = self.playhead_time
        m, s = divmod(t, 60)
        total = self.ruler.duration
        tm, ts = divmod(total, 60)
        self.time_label.setText(f"{int(m):02d}:{s:05.2f} / {int(tm):02d}:{ts:05.2f}")

    def export_cue_json(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出Cue列表", "", "JSON文件 (*.json)")
        if not path:
            return
        cue_list = []
        all_times = set()
        for track in self.tracks:
            for kf in track.keyframes:
                all_times.add(kf.time)
        for t in sorted(all_times):
            cue = {"time": t, "values": {}}
            for track in self.tracks:
                cue["values"][f"{track.name}.{track.attribute}"] = track.get_value_at(t)
            cue_list.append(cue)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cue_list, f, ensure_ascii=False, indent=2)
            self.logger.info(f"已导出Cue列表: {path}")
            QMessageBox.information(self, "成功", f"已导出: {path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def save_timeline(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存时间线", "", "JSON文件 (*.json)")
        if not path:
            return
        try:
            data = {"duration": self.ruler.duration, "tracks": [t.to_dict() for t in self.tracks]}
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"时间线已保存: {path}")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def load_timeline(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载时间线", "", "JSON文件 (*.json)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "加载失败", str(e))
            return
        self.ruler.duration = data.get("duration", 120)
        self.duration_spin.setValue(self.ruler.duration)
        # 清除旧轨道widget
        for i in range(self.track_layout.count() - 1, 0, -1):
            item = self.track_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        self.tracks = [Track.from_dict(d) for d in data.get("tracks", [])]
        colors = [QColor(80, 180, 255), QColor(255, 140, 80), QColor(80, 255, 140),
                  QColor(255, 80, 180), QColor(180, 80, 255), QColor(255, 255, 80)]
        for i, track in enumerate(self.tracks):
            track.color = colors[i % len(colors)]
            tw = TimelineTrackWidget(track, self.ruler, self.track_container)
            self.track_layout.addWidget(tw)
        self._update_keyframe_table()
        self.logger.info(f"时间线已加载: {path}")


if __name__ == '__main__':
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    win = TimelineEditor()
    win.show()
    sys.exit(app.exec())
