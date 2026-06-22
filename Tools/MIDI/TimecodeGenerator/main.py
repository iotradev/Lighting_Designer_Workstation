#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""时间码生成器 v2 - SMPTE/MTC生成 + MIDI输出 + 音频播放"""

import sys
import csv
import time
import threading
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))
from ui.base_window import BaseToolWindow

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QFrame, QGridLayout, QMessageBox, QCheckBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QFont, QColor

try:
    import rtmidi
    HAS_RTMIDI = True
except ImportError:
    HAS_RTMIDI = False

try:
    import miniaudio
    HAS_MINIAUDIO = True
except ImportError:
    HAS_MINIAUDIO = False


# ─── 常用预设 ────────────────────────────────────────────────────────────────
PRESETS = {
    "PAL 25fps": {"fps": 25, "offset_h": 0, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "NTSC 30fps": {"fps": 30, "offset_h": 0, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "Film 24fps": {"fps": 24, "offset_h": 0, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "演出开场 01:00:00:00": {"fps": 25, "offset_h": 1, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "演出开场 00:10:00:00": {"fps": 25, "offset_h": 0, "offset_m": 10, "offset_s": 0, "offset_f": 0},
    "1小时倒计时": {"fps": 25, "offset_h": 1, "offset_m": 0, "offset_s": 0, "offset_f": 0, "countdown": True},
    "自定义...": None,
}


class MidiWorker(QObject):
    """MIDI发送工作线程信号"""
    tick_signal = Signal(str, str, int)  # smpte_str, mtc_msg, total_frames
    error_signal = Signal(str)


class TimecodeDisplay(QFrame):
    """大字体时间码显示"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setMinimumHeight(80)
        self._text = "00:00:00:00"

        layout = QHBoxLayout(self)
        self._label = QLabel(self._text)
        font = QFont("Consolas", 42, QFont.Bold)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #00FF00; background-color: #1a1a1a;")
        layout.addWidget(self._label)

    def set_timecode(self, tc_str):
        self._text = tc_str
        self._label.setText(tc_str)


class TimecodeGenerator(BaseToolWindow):
    """时间码生成器 v2 - MIDI输出 + 音频播放"""

    def __init__(self):
        super().__init__('TimecodeGenerator', '时间码生成器', '2.0.0', 1100, 750)

        self._running = False
        self._fps = 25
        self._speed_multiplier = 1.0
        self._hours = 0
        self._minutes = 0
        self._seconds = 0
        self._frames = 0
        self._tc_log = []
        self._countdown = False

        # MIDI
        self._midi_out = None
        self._midi_port_name = None
        self._send_mtc = True

        # 音频
        self._audio_data = None
        self._audio_sample_rate = 0
        self._audio_playing = False
        self._audio_stream = None

        # 定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._build_ui()
        self._refresh_midi_ports()
        self.logger.info("时间码生成器 v2 已初始化")

    def _build_ui(self):
        central = QWidget()
        self.set_central_content(central)
        layout = QVBoxLayout(central)

        # ── 时间码显示 ──
        self._tc_display = TimecodeDisplay()
        layout.addWidget(self._tc_display)

        # ── 设置面板 ──
        settings_layout = QHBoxLayout()

        # MIDI输出
        midi_group = QGroupBox("MIDI 输出")
        midi_layout = QVBoxLayout(midi_group)
        midi_row = QHBoxLayout()
        midi_row.addWidget(QLabel("端口:"))
        self._midi_combo = QComboBox()
        self._midi_combo.setMinimumWidth(200)
        midi_row.addWidget(self._midi_combo, 1)
        self._midi_refresh_btn = QPushButton("刷新")
        self._midi_refresh_btn.setFixedWidth(50)
        self._midi_refresh_btn.clicked.connect(self._refresh_midi_ports)
        midi_row.addWidget(self._midi_refresh_btn)
        self._midi_connect_btn = QPushButton("连接")
        self._midi_connect_btn.setFixedWidth(60)
        self._midi_connect_btn.clicked.connect(self._toggle_midi)
        midi_row.addWidget(self._midi_connect_btn)
        midi_layout.addLayout(midi_row)

        self._midi_status = QLabel("未连接")
        self._midi_status.setStyleSheet("color: #888;")
        midi_layout.addWidget(self._midi_status)

        self._mtc_check = QCheckBox("发送MTC")
        self._mtc_check.setChecked(True)
        self._mtc_check.toggled.connect(lambda v: setattr(self, '_send_mtc', v))
        midi_layout.addWidget(self._mtc_check)
        settings_layout.addWidget(midi_group)

        # 预设
        preset_group = QGroupBox("常用预设")
        preset_layout = QVBoxLayout(preset_group)
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(PRESETS.keys())
        self._preset_combo.currentTextChanged.connect(self._on_preset)
        preset_layout.addWidget(self._preset_combo)
        settings_layout.addWidget(preset_group)

        # FPS
        fps_group = QGroupBox("帧率 (FPS)")
        fps_layout = QVBoxLayout(fps_group)
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["24", "25", "30"])
        self._fps_combo.setCurrentText("25")
        self._fps_combo.currentTextChanged.connect(self._on_fps_changed)
        fps_layout.addWidget(self._fps_combo)
        settings_layout.addWidget(fps_group)

        # 速度
        speed_group = QGroupBox("播放速度")
        speed_layout = QVBoxLayout(speed_group)
        speed_btn_layout = QHBoxLayout()
        for label, mult in [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(mult == 1.0)
            btn.clicked.connect(lambda checked, m=mult: self._set_speed(m))
            speed_btn_layout.addWidget(btn)
        speed_layout.addLayout(speed_btn_layout)
        settings_layout.addWidget(speed_group)

        # 设置时间码
        set_group = QGroupBox("设置时间码")
        set_layout = QGridLayout(set_group)
        self._set_h = QSpinBox(); self._set_h.setRange(0, 23); self._set_h.setPrefix("时 ")
        self._set_m = QSpinBox(); self._set_m.setRange(0, 59); self._set_m.setPrefix("分 ")
        self._set_s = QSpinBox(); self._set_s.setRange(0, 59); self._set_s.setPrefix("秒 ")
        self._set_f = QSpinBox(); self._set_f.setRange(0, 29); self._set_f.setPrefix("帧 ")
        set_layout.addWidget(self._set_h, 0, 0)
        set_layout.addWidget(self._set_m, 0, 1)
        set_layout.addWidget(self._set_s, 0, 2)
        set_layout.addWidget(self._set_f, 0, 3)
        set_btn = QPushButton("设置")
        set_btn.clicked.connect(self._on_set_timecode)
        set_layout.addWidget(set_btn, 0, 4)
        settings_layout.addWidget(set_group)

        layout.addLayout(settings_layout)

        # ── 音频导入 ──
        audio_group = QGroupBox("音频同步")
        audio_layout = QHBoxLayout(audio_group)
        self._audio_btn = QPushButton("📂 导入音频")
        self._audio_btn.clicked.connect(self._on_import_audio)
        audio_layout.addWidget(self._audio_btn)
        self._audio_label = QLabel("未导入音频")
        self._audio_label.setStyleSheet("color: #888;")
        audio_layout.addWidget(self._audio_label, 1)
        self._audio_play_btn = QPushButton("▶ 播放音频")
        self._audio_play_btn.setEnabled(False)
        self._audio_play_btn.clicked.connect(self._on_toggle_audio)
        audio_layout.addWidget(self._audio_play_btn)
        self._audio_stop_btn = QPushButton("⏹ 停止音频")
        self._audio_stop_btn.setEnabled(False)
        self._audio_stop_btn.clicked.connect(self._on_stop_audio)
        audio_layout.addWidget(self._audio_stop_btn)
        layout.addWidget(audio_group)

        # ── 播放控制 ──
        ctrl_layout = QHBoxLayout()
        self._start_btn = QPushButton("▶ 开始发送")
        self._start_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        self._start_btn.clicked.connect(self._on_start)
        ctrl_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("⏹ 停止")
        self._stop_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        ctrl_layout.addWidget(self._stop_btn)

        self._reset_btn = QPushButton("↺ 重置")
        self._reset_btn.setStyleSheet("font-size: 14px; padding: 8px 20px;")
        self._reset_btn.clicked.connect(self._on_reset)
        ctrl_layout.addWidget(self._reset_btn)

        export_btn = QPushButton("💾 导出CSV")
        export_btn.clicked.connect(self._on_export)
        ctrl_layout.addWidget(export_btn)

        layout.addLayout(ctrl_layout)

        # ── MTC日志 ──
        log_group = QGroupBox("MTC消息日志")
        log_layout = QVBoxLayout(log_group)
        self._log_table = QTableWidget(0, 5)
        self._log_table.setHorizontalHeaderLabels(["#", "时间", "SMPTE", "MTC消息", "帧数"])
        self._log_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        log_layout.addWidget(self._log_table)
        layout.addWidget(log_group, 1)

    # ── MIDI ──────────────────────────────────────────────────────────────────

    def _refresh_midi_ports(self):
        self._midi_combo.clear()
        if not HAS_RTMIDI:
            self._midi_combo.addItem("(需要 python-rtmidi)")
            self._midi_status.setText("未安装 rtmidi")
            self._midi_status.setStyleSheet("color: #f44747;")
            return
        try:
            tmp = rtmidi.MidiOut()
            ports = tmp.get_ports()
            del tmp
            if ports:
                self._midi_combo.addItems(ports)
                self._midi_status.setText(f"找到 {len(ports)} 个端口")
            else:
                self._midi_combo.addItem("(无可用端口)")
                self._midi_status.setText("未找到MIDI端口")
                self._midi_status.setStyleSheet("color: #e8912d;")
        except Exception as e:
            self._midi_status.setText(f"扫描失败: {e}")
            self._midi_status.setStyleSheet("color: #f44747;")

    def _toggle_midi(self):
        if self._midi_out:
            self._disconnect_midi()
        else:
            self._connect_midi()

    def _connect_midi(self):
        if not HAS_RTMIDI:
            QMessageBox.warning(self, "缺少依赖", "需要安装 python-rtmidi:\npip install python-rtmidi")
            return
        port_name = self._midi_combo.currentText()
        if not port_name or "(" in port_name:
            QMessageBox.warning(self, "提示", "请选择有效的MIDI端口")
            return
        try:
            self._midi_out = rtmidi.MidiOut()
            ports = self._midi_out.get_ports()
            if port_name in ports:
                self._midi_out.open_port(ports.index(port_name))
            else:
                self._midi_out.open_virtual_port("TimecodeGenerator")
            self._midi_port_name = port_name
            self._midi_connect_btn.setText("断开")
            self._midi_status.setText(f"已连接: {port_name}")
            self._midi_status.setStyleSheet("color: #4ec9b0;")
            self._midi_combo.setEnabled(False)
            self.logger.info(f"MIDI已连接: {port_name}")
        except Exception as e:
            QMessageBox.critical(self, "连接失败", f"MIDI连接失败:\n{e}")
            self._midi_out = None

    def _disconnect_midi(self):
        if self._midi_out:
            try:
                self._midi_out.close_port()
                del self._midi_out
            except Exception:
                pass
            self._midi_out = None
            self._midi_port_name = None
        self._midi_connect_btn.setText("连接")
        self._midi_status.setText("未连接")
        self._midi_status.setStyleSheet("color: #888;")
        self._midi_combo.setEnabled(True)
        self.logger.info("MIDI已断开")

    def _send_midi_message(self, msg):
        """发送MIDI消息"""
        if self._midi_out and self._send_mtc:
            try:
                self._midi_out.send_message(msg)
            except Exception as e:
                self.logger.error(f"MIDI发送失败: {e}")

    def _send_mtc_quarter_frame(self, part, data):
        """发送MTC quarter-frame消息 (0xF1 + data)"""
        byte = (part << 4) | (data & 0x0F)
        self._send_midi_message([0xF1, byte])

    def _send_mtc_full_frame(self):
        """发送MTC Full Frame消息 (SysEx)"""
        hh = self._hours
        mm = self._minutes
        ss = self._seconds
        ff = self._frames
        fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)

        sysex = [0xF0, 0x7F, 0x7F, 0x01, 0x01,
                 fps_type << 5 | (hh & 0x1F),
                 mm & 0x3F,
                 ss & 0x3F,
                 ff & 0x1F,
                 0xF7]
        self._send_midi_message(sysex)

    def _send_mtc_start(self):
        """发送MTC开始 (start sysex)"""
        self._send_midi_message([0xFA])  # MIDI Start

    def _send_mtc_stop(self):
        """发送MTC停止"""
        self._send_midi_message([0xFC])  # MIDI Stop

    # ── 音频 ──────────────────────────────────────────────────────────────────

    def _on_import_audio(self):
        if not HAS_MINIAUDIO:
            QMessageBox.warning(self, "缺少依赖", "需要安装 miniaudio:\npip install miniaudio")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", str(Path.home()),
            "音频文件 (*.wav *.mp3 *.flac *.ogg *.aac *.m4a);;所有文件 (*)"
        )
        if not path:
            return
        try:
            with open(path, 'rb') as f:
                data = f.read()
            decoded = miniaudio.decode(data, output_format=miniaudio.SampleFormat.SIGNED16)
            self._audio_data = decoded.samples
            self._audio_sample_rate = decoded.sample_rate
            self._audio_channels = decoded.nchannels
            duration = len(self._audio_data) / self._audio_sample_rate / self._audio_channels
            self._audio_label.setText(f"✓ {Path(path).name} ({duration:.1f}秒, {self._audio_sample_rate}Hz)")
            self._audio_label.setStyleSheet("color: #4ec9b0;")
            self._audio_play_btn.setEnabled(True)
            self.logger.info(f"音频已导入: {path}")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"无法加载音频:\n{e}")
            self.logger.error(f"音频导入失败: {e}")

    def _on_toggle_audio(self):
        if self._audio_playing:
            self._on_stop_audio()
        else:
            self._start_audio_playback()

    def _start_audio_playback(self):
        if not self._audio_data:
            return
        try:
            import miniaudio
            # 在后台线程播放音频
            self._audio_playing = True
            self._audio_play_btn.setText("⏸ 暂停音频")
            self._audio_stop_btn.setEnabled(True)

            # 将 samples 转为 generator
            samples = self._audio_data
            chunk_size = 4096
            n_channels = self._audio_channels
            sr = self._audio_sample_rate

            def audio_generator():
                """分块输出音频数据的generator"""
                pos = 0
                while pos < len(samples):
                    if not self._audio_playing:
                        # 输出静音直到停止
                        yield bytes(chunk_size * 2 * n_channels)
                        continue
                    end = min(pos + chunk_size * n_channels, len(samples))
                    chunk = samples[pos:end]
                    pos = end
                    # array.array -> bytes
                    yield chunk.tobytes()
                # 播放结束
                self._audio_playing = False

            def play():
                try:
                    dev = miniaudio.PlaybackDevice(
                        output_format=miniaudio.SampleFormat.SIGNED16,
                        nchannels=n_channels,
                        sample_rate=sr
                    )
                    dev.start(audio_generator)
                    self._audio_stream = dev
                    while self._audio_playing:
                        time.sleep(0.1)
                    dev.stop()
                    dev.close()
                except Exception as e:
                    self.logger.error(f"音频播放失败: {e}")
                finally:
                    self._audio_playing = False

            threading.Thread(target=play, daemon=True).start()
            self.logger.info("音频播放已开始")
        except Exception as e:
            QMessageBox.critical(self, "播放失败", f"无法播放音频:\n{e}")

    def _on_stop_audio(self):
        self._audio_playing = False
        self._audio_play_btn.setText("▶ 播放音频")
        self._audio_stop_btn.setEnabled(False)
        if self._audio_stream:
            try:
                self._audio_stream.stop()
            except Exception:
                pass
        self.logger.info("音频播放已停止")

    # ── 预设 ──────────────────────────────────────────────────────────────────

    def _on_preset(self, name):
        preset = PRESETS.get(name)
        if not preset:
            return
        self._fps_combo.setCurrentText(str(preset["fps"]))
        self._set_h.setValue(preset.get("offset_h", 0))
        self._set_m.setValue(preset.get("offset_m", 0))
        self._set_s.setValue(preset.get("offset_s", 0))
        self._set_f.setValue(preset.get("offset_f", 0))
        self._countdown = preset.get("countdown", False)
        self._on_set_timecode()
        self.logger.info(f"已加载预设: {name}")

    # ── 控制 ──────────────────────────────────────────────────────────────────

    def _on_fps_changed(self, text):
        self._fps = int(text)
        self._set_f.setRange(0, self._fps - 1)
        self.logger.info(f"帧率设置为: {self._fps} FPS")

    def _set_speed(self, mult):
        self._speed_multiplier = mult
        if self._running:
            interval = max(1, int(1000 / self._fps / self._speed_multiplier))
            self._timer.setInterval(interval)
        self.logger.info(f"速度设置为: {mult}x")

    def _on_set_timecode(self):
        self._hours = self._set_h.value()
        self._minutes = self._set_m.value()
        self._seconds = self._set_s.value()
        self._frames = self._set_f.value()
        self._update_display()

    def _on_start(self):
        if self._running:
            return
        self._running = True
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

        # 发送MTC开始
        if self._midi_out and self._send_mtc:
            self._send_mtc_full_frame()
            self._send_mtc_start()

        interval = max(1, int(1000 / self._fps / self._speed_multiplier))
        self._timer.setInterval(interval)
        self._timer.start()
        self.logger.info("时间码发送已启动")

    def _on_stop(self):
        if not self._running:
            return
        self._running = False
        self._timer.stop()

        # 发送MTC停止
        if self._midi_out and self._send_mtc:
            self._send_mtc_stop()

        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self.logger.info("时间码发送已停止")

    def _on_reset(self):
        self._on_stop()
        self._hours = self._minutes = self._seconds = self._frames = 0
        self._update_display()

    def _on_tick(self):
        if self._countdown:
            self._frames -= 1
            if self._frames < 0:
                self._frames = self._fps - 1
                self._seconds -= 1
                if self._seconds < 0:
                    self._seconds = 59
                    self._minutes -= 1
                    if self._minutes < 0:
                        self._minutes = 59
                        self._hours -= 1
                        if self._hours < 0:
                            self._hours = 0
                            self._minutes = 0
                            self._seconds = 0
                            self._frames = 0
                            self._on_stop()
                            return
        else:
            self._frames += 1
            if self._frames >= self._fps:
                self._frames = 0
                self._seconds += 1
                if self._seconds >= 60:
                    self._seconds = 0
                    self._minutes += 1
                    if self._minutes >= 60:
                        self._minutes = 0
                        self._hours = (self._hours + 1) % 24

        self._update_display()

        # 发送MTC quarter-frame消息
        if self._midi_out and self._send_mtc:
            fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)
            # 8个quarter-frame消息 per frame
            # F0: frame low nibble
            # F1: frame high nibble + fps type
            # F2: seconds low
            # F3: seconds high
            # F4: minutes low
            # F5: minutes high
            # F6: hours low
            # F7: hours high + fps type
            self._send_mtc_quarter_frame(0, self._frames & 0x0F)
            self._send_mtc_quarter_frame(1, (self._frames >> 4) & 0x01)
            self._send_mtc_quarter_frame(2, self._seconds & 0x0F)
            self._send_mtc_quarter_frame(3, (self._seconds >> 4) & 0x03)
            self._send_mtc_quarter_frame(4, self._minutes & 0x0F)
            self._send_mtc_quarter_frame(5, (self._minutes >> 4) & 0x03)
            self._send_mtc_quarter_frame(6, self._hours & 0x0F)
            self._send_mtc_quarter_frame(7, (fps_type << 1) | ((self._hours >> 4) & 0x01))

        self._log_timecode()

    def _update_display(self):
        tc = f"{self._hours:02d}:{self._minutes:02d}:{self._seconds:02d}:{self._frames:02d}"
        self._tc_display.set_timecode(tc)

    def _log_timecode(self):
        tc = f"{self._hours:02d}:{self._minutes:02d}:{self._seconds:02d}:{self._frames:02d}"
        total_frames = (self._hours * 3600 + self._minutes * 60 + self._seconds) * self._fps + self._frames
        mtc_msg = self._generate_mtc_string()

        row = self._log_table.rowCount()
        self._log_table.insertRow(row)
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self._log_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self._log_table.setItem(row, 1, QTableWidgetItem(now))
        self._log_table.setItem(row, 2, QTableWidgetItem(tc))
        self._log_table.setItem(row, 3, QTableWidgetItem(mtc_msg))
        self._log_table.setItem(row, 4, QTableWidgetItem(str(total_frames)))

        self._tc_log.append({
            'timestamp': now, 'smpte': tc, 'mtc': mtc_msg, 'frames': total_frames
        })

        if self._log_table.rowCount() > 500:
            self._log_table.removeRow(0)
            self._tc_log.pop(0)

    def _generate_mtc_string(self):
        hh, mm, ss, ff = self._hours, self._minutes, self._seconds, self._frames
        fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)
        return f"F1:{(fps_type << 5) | (hh & 0x1F):02X} F2:{mm:02X} F3:{ss:02X} F4:{ff:02X}"

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出时间码日志", "timecode_log.csv", "CSV文件 (*.csv)"
        )
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'smpte', 'mtc', 'frames'])
                writer.writeheader()
                writer.writerows(self._tc_log)
            self.logger.info(f"日志已导出: {path}")

    def closeEvent(self, event):
        self._on_stop()
        self._on_stop_audio()
        self._disconnect_midi()
        super().closeEvent(event)


# ─── 入口 ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import traceback
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = TimecodeGenerator()
        window.show()
        sys.exit(app.exec())
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "TimecodeGenerator - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
