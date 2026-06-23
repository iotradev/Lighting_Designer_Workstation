# -*- coding: utf-8 -*-
"""时间码生成器 v3 - SMPTE/MTC + 音频同步播放 + UI美化"""
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
    QComboBox, QSpinBox, QGroupBox, QTableWidget,
    QFileDialog, QFrame, QMessageBox, QCheckBox,
    QSlider, QTextBrowser
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

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

PRESETS = {
    "PAL 25fps": {"fps": 25, "offset_h": 0, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "NTSC 30fps": {"fps": 30, "offset_h": 0, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "Film 24fps": {"fps": 24, "offset_h": 0, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "演出开场 01:00:00:00": {"fps": 25, "offset_h": 1, "offset_m": 0, "offset_s": 0, "offset_f": 0},
    "演出开场 00:10:00:00": {"fps": 25, "offset_h": 0, "offset_m": 10, "offset_s": 0, "offset_f": 0},
    "1小时倒计时": {"fps": 25, "offset_h": 1, "offset_m": 0, "offset_s": 0, "offset_f": 0, "countdown": True},
    "自定义...": None,
}


class TimecodeDisplay(QFrame):
    """大字体时间码显示"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setFixedHeight(60)
        self._text = "00:00:00:00"
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        self._label = QLabel(self._text)
        font = QFont("Consolas", 36, QFont.Bold)
        self._label.setFont(font)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet("color: #00FF00; background-color: #0a0a0a; border-radius: 6px;")
        layout.addWidget(self._label)

    def set_timecode(self, tc_str):
        self._text = tc_str
        self._label.setText(tc_str)


class TimecodeGenerator(BaseToolWindow):
    """时间码生成器 v3 - MTC + 音频同步"""

    def __init__(self):
        super().__init__('TimecodeGenerator', '时间码生成器', '3.0.0', 1100, 750)

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
        self._audio_channels = 1
        self._audio_playing = False
        self._audio_stream = None
        self._audio_position = 0
        self._audio_total = 0
        self._audio_seek_to = -1

        # 同步模式
        self._sync_mode = False
        self._volume = 0.8  # 0.0 ~ 1.0  # True = 音频驱动时间码

        # 定时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

        self._build_ui()
        self._refresh_midi_ports()
        self.logger.info("时间码生成器 v3 已初始化")

    def _ensure_visible(self):
        """确保窗口在屏幕内可见"""
        from PySide6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            # 如果窗口不在屏幕内，居中显示
            if not geo.intersects(self.geometry()):
                self.move(geo.center() - self.rect().center())
            # 确保窗口不被最小化
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def _build_ui(self):
        central = QWidget()
        self.set_central_content(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(10, 8, 10, 8)

        # ── 时间码大显示 ──
        self._tc_display = TimecodeDisplay()
        root.addWidget(self._tc_display)

        # ── 设置时间码 + 帧率 ──
        tc_group = QGroupBox("时间码设置")
        tc_layout = QHBoxLayout(tc_group)
        tc_layout.setSpacing(8)

        tc_layout.addWidget(QLabel("时间:"))
        self._set_h = QSpinBox(); self._set_h.setRange(0, 23); self._set_h.setPrefix("H "); self._set_h.setFixedWidth(80)
        self._set_m = QSpinBox(); self._set_m.setRange(0, 59); self._set_m.setPrefix("M "); self._set_m.setFixedWidth(80)
        self._set_s = QSpinBox(); self._set_s.setRange(0, 59); self._set_s.setPrefix("S "); self._set_s.setFixedWidth(80)
        self._set_f = QSpinBox(); self._set_f.setRange(0, 29); self._set_f.setPrefix("F "); self._set_f.setFixedWidth(80)
        for w in [self._set_h, self._set_m, self._set_s, self._set_f]:
            tc_layout.addWidget(w)

        set_btn = QPushButton("设置")
        set_btn.setFixedWidth(60)
        set_btn.clicked.connect(self._on_set_timecode)
        tc_layout.addWidget(set_btn)
        tc_layout.addSpacing(16)

        tc_layout.addWidget(QLabel("帧率:"))
        self._fps_combo = QComboBox()
        self._fps_combo.addItems(["24", "25", "30"])
        self._fps_combo.setCurrentText("25")
        self._fps_combo.currentTextChanged.connect(self._on_fps_changed)
        self._fps_combo.setFixedWidth(55)
        tc_layout.addWidget(self._fps_combo)

        tc_layout.addWidget(QLabel("预设:"))
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(PRESETS.keys())
        self._preset_combo.currentTextChanged.connect(self._on_preset)
        tc_layout.addWidget(self._preset_combo, 1)

        tc_layout.addWidget(QLabel("速度:"))
        for label, mult in [("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(mult == 1.0)
            btn.setMinimumWidth(50)
            btn.clicked.connect(lambda checked, m=mult: self._set_speed(m))
            tc_layout.addWidget(btn)
        root.addWidget(tc_group)

        # ── MIDI + 音频 控制 ──
        ctrl_group = QGroupBox("MIDI / 音频 控制")
        ctrl_layout = QVBoxLayout(ctrl_group)
        ctrl_layout.setSpacing(6)

        # MIDI 行
        midi_row = QHBoxLayout()
        midi_row.setSpacing(8)
        midi_row.addWidget(QLabel("MIDI端口:"))
        self._midi_combo = QComboBox()
        self._midi_combo.setMinimumWidth(200)
        midi_row.addWidget(self._midi_combo, 1)
        self._midi_refresh_btn = QPushButton("刷新")
        self._midi_refresh_btn.clicked.connect(self._refresh_midi_ports)
        midi_row.addWidget(self._midi_refresh_btn)
        self._midi_connect_btn = QPushButton("连接")
        self._midi_connect_btn.clicked.connect(self._toggle_midi)
        midi_row.addWidget(self._midi_connect_btn)
        self._midi_status = QLabel("未连接")
        self._midi_status.setStyleSheet("color: #666;")
        midi_row.addWidget(self._midi_status)
        self._mtc_check = QCheckBox("发送MTC")
        self._mtc_check.setChecked(True)
        self._mtc_check.toggled.connect(lambda v: setattr(self, '_send_mtc', v))
        midi_row.addWidget(self._mtc_check)
        ctrl_layout.addLayout(midi_row)

        # 音频行
        audio_row = QHBoxLayout()
        audio_row.setSpacing(8)
        audio_row.addWidget(QLabel("音频:"))
        self._audio_btn = QPushButton("导入音频")
        self._audio_btn.clicked.connect(self._on_import_audio)
        audio_row.addWidget(self._audio_btn)
        self._audio_label = QLabel("未导入")
        self._audio_label.setStyleSheet("color: #666;")
        audio_row.addWidget(self._audio_label, 1)
        self._audio_play_btn = QPushButton("播放")
        self._audio_play_btn.setEnabled(False)
        self._audio_play_btn.clicked.connect(self._on_toggle_audio)
        audio_row.addWidget(self._audio_play_btn)
        self._audio_stop_btn = QPushButton("停止")
        self._audio_stop_btn.setEnabled(False)
        self._audio_stop_btn.clicked.connect(self._on_stop_audio)
        audio_row.addWidget(self._audio_stop_btn)
        ctrl_layout.addLayout(audio_row)

        # 进度条 + 音量
        progress_row = QHBoxLayout()
        progress_row.setSpacing(8)
        self._progress_slider = QSlider(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 1000)
        self._progress_slider.setValue(0)
        self._progress_slider.setEnabled(False)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        self._progress_slider.sliderMoved.connect(self._on_slider_moved)
        progress_row.addWidget(self._progress_slider, 1)
        self._progress_time = QLabel("00:00 / 00:00")
        self._progress_time.setStyleSheet("color: #888; font-size: 11px;")
        self._progress_time.setFixedWidth(100)
        progress_row.addWidget(self._progress_time)

        progress_row.addSpacing(12)
        progress_row.addWidget(QLabel("音量:"))
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setFixedWidth(120)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        progress_row.addWidget(self._volume_slider)
        self._volume_label = QLabel("80%")
        self._volume_label.setStyleSheet("color: #888; font-size: 11px;")
        self._volume_label.setFixedWidth(50)
        progress_row.addWidget(self._volume_label)

        ctrl_layout.addLayout(progress_row)
        root.addWidget(ctrl_group)

        # ── 操作按钮 ──
        act_group = QGroupBox("播放控制")
        act_layout = QHBoxLayout(act_group)
        act_layout.setSpacing(10)

        self._sync_btn = QPushButton("同步播放 (音频+MTC)")
        self._sync_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold; font-size: 14px;
                background: #1a5c1a; color: #fff;
                padding: 8px 16px; border-radius: 6px;
            }
            QPushButton:hover { background: #2a7a2a; }
            QPushButton:disabled { background: #333; color: #666; }
        """)
        self._sync_btn.clicked.connect(self._on_sync_play)
        act_layout.addWidget(self._sync_btn)

        self._start_btn = QPushButton("仅MTC发送")
        self._start_btn.setStyleSheet("font-weight: bold; background: #2a4a6e;")
        self._start_btn.clicked.connect(self._on_start)
        act_layout.addWidget(self._start_btn)

        self._stop_btn = QPushButton("停止")
        self._stop_btn.setStyleSheet("background: #6e2a2a;")
        self._stop_btn.clicked.connect(self._on_stop)
        self._stop_btn.setEnabled(False)
        act_layout.addWidget(self._stop_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.clicked.connect(self._on_reset)
        act_layout.addWidget(self._reset_btn)

        export_btn = QPushButton("导出CSV")
        export_btn.clicked.connect(self._on_export)
        act_layout.addWidget(export_btn)
        root.addWidget(act_group)

        # ── MTC日志 ──
        log_group = QGroupBox("MTC消息日志")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(4, 10, 4, 4)

        stats_row = QHBoxLayout()
        self._log_count_label = QLabel("消息: 0")
        self._log_count_label.setStyleSheet("color: #888; font-size: 11px;")
        stats_row.addWidget(self._log_count_label)
        self._log_rate_label = QLabel("速率: 0/秒")
        self._log_rate_label.setStyleSheet("color: #888; font-size: 11px;")
        stats_row.addWidget(self._log_rate_label)
        stats_row.addStretch()
        clear_log_btn = QPushButton("清除")
        clear_log_btn.setFixedWidth(60)
        clear_log_btn.setStyleSheet("font-size: 11px; padding: 2px 6px;")
        clear_log_btn.clicked.connect(self._clear_log)
        stats_row.addWidget(clear_log_btn)
        log_layout.addLayout(stats_row)

        self._log_view = QTextBrowser()
        self._log_view.setStyleSheet("""
            QTextBrowser {
                background-color: #0a0a0a; color: #ccc;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px; border: 1px solid #2a2a2d;
                border-radius: 4px; padding: 4px;
            }
        """)
        self._log_view.setOpenLinks(False)
        log_layout.addWidget(self._log_view, 1)
        root.addWidget(log_group, 1)

        # 进度更新定时器
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(50)
        self._progress_timer.timeout.connect(self._update_progress)

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
        if self._midi_out and self._send_mtc:
            try:
                self._midi_out.send_message(msg)
            except Exception as e:
                self.logger.error(f"MIDI发送失败: {e}")

    def _send_mtc_quarter_frame(self, part, data):
        byte = (part << 4) | (data & 0x0F)
        self._send_midi_message([0xF1, byte])

    def _send_mtc_full_frame(self):
        hh, mm, ss, ff = self._hours, self._minutes, self._seconds, self._frames
        fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)
        sysex = [0xF0, 0x7F, 0x7F, 0x01, 0x01,
                 fps_type << 5 | (hh & 0x1F), mm & 0x3F, ss & 0x3F, ff & 0x1F, 0xF7]
        self._send_midi_message(sysex)

    def _send_mtc_start(self):
        self._send_midi_message([0xFA])

    def _send_mtc_stop(self):
        self._send_midi_message([0xFC])

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
            self._audio_label.setText(f"✓ {Path(path).name[:20]} ({duration:.0f}s)")
            self._audio_label.setStyleSheet("color: #4ec9b0;")
            self._audio_play_btn.setEnabled(True)
            self._sync_btn.setEnabled(True)
            self._progress_slider.setEnabled(True)
            self._progress_slider.setRange(0, int(duration * 1000))
            self._progress_slider.setValue(0)
            self._audio_total = len(self._audio_data) * 2
            self._progress_time.setText(f"00:00 / {int(duration//60):02d}:{int(duration%60):02d}")
            self.logger.info(f"音频已导入: {path}")
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"无法加载音频:\n{e}")

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
            self._audio_playing = True
            self._audio_play_btn.setText("暂停")
            self._audio_stop_btn.setEnabled(True)
            self._progress_timer.start()

            raw_bytes = bytes(self._audio_data)
            n_channels = self._audio_channels
            sr = self._audio_sample_rate
            bpf = n_channels * 2
            total = len(raw_bytes)
            self._audio_total = total

            def audio_gen():
                pos = 0
                buf = b''
                framecount = yield
                while True:
                    seek = self._audio_seek_to
                    if seek >= 0:
                        pos = max(0, min(seek, total - bpf))
                        pos = pos - (pos % bpf)
                        buf = b''
                        self._audio_seek_to = -1

                    if not self._audio_playing:
                        self._audio_position = pos
                        framecount = yield b'\x00' * (framecount * bpf)
                        continue

                    need = framecount * bpf
                    while len(buf) < need and pos < total:
                        end = min(pos + need * 2, total)
                        buf += raw_bytes[pos:end]
                        pos = end

                    if not buf and pos >= total:
                        self._audio_playing = False
                        self._audio_position = total
                        framecount = yield b'\x00' * need
                        continue

                    data = buf[:need]
                    buf = buf[need:]
                    if len(data) < need:
                        data += b'\x00' * (need - len(data))

                    # 应用音量
                    vol = self._volume
                    if vol < 0.99:
                        import struct
                        samples = struct.unpack(f'<{len(data)//2}h', data)
                        scaled = struct.pack(f'<{len(samples)}h',
                            *[max(-32768, min(32767, int(s * vol))) for s in samples])
                        data = scaled

                    self._audio_position = pos - len(buf)
                    framecount = yield data

            def play():
                try:
                    dev = miniaudio.PlaybackDevice(
                        output_format=miniaudio.SampleFormat.SIGNED16,
                        nchannels=n_channels, sample_rate=sr
                    )
                    gen = audio_gen()
                    next(gen)
                    dev.start(gen)
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
        self._audio_play_btn.setText("播放")
        self._audio_stop_btn.setEnabled(False)
        self._progress_timer.stop()
        if self._audio_stream:
            try:
                self._audio_stream.stop()
            except Exception:
                pass
        self.logger.info("音频播放已停止")

    def _on_slider_pressed(self):
        self._progress_timer.stop()

    def _on_slider_released(self):
        if not self._audio_data:
            return
        ms = self._progress_slider.value()
        sr = self._audio_sample_rate
        ch = self._audio_channels
        sample_pos = int(ms / 1000.0 * sr) * ch
        byte_pos = sample_pos * 2
        self._audio_seek_to = byte_pos
        if self._audio_playing:
            self._progress_timer.start()

    def _on_slider_moved(self, ms):
        cur = ms / 1000.0
        total = self._progress_slider.maximum() / 1000.0
        self._progress_time.setText(
            f"{int(cur//60):02d}:{int(cur%60):02d} / {int(total//60):02d}:{int(total%60):02d}"
        )

    def _on_volume_changed(self, value):
        self._volume = value / 100.0
        self._volume_label.setText(f"{value}%")

    def _update_progress(self):
        if not self._audio_playing or not self._audio_sample_rate:
            return
        sr = self._audio_sample_rate
        ch = self._audio_channels
        pos_bytes = self._audio_position
        cur_sec = pos_bytes / (sr * ch * 2)
        total_sec = self._audio_total / (sr * ch * 2)
        self._progress_slider.setValue(int(cur_sec * 1000))
        self._progress_time.setText(
            f"{int(cur_sec//60):02d}:{int(cur_sec%60):02d} / {int(total_sec//60):02d}:{int(total_sec%60):02d}"
        )

        # 同步模式: 音频位置驱动时间码 + 发送MTC
        if self._sync_mode and self._running:
            self._sync_timecode_from_audio(cur_sec)
            self._send_mtc_for_current_frame()

    def _sync_timecode_from_audio(self, audio_sec):
        """根据音频播放位置同步时间码"""
        total_frames = int(audio_sec * self._fps)
        self._hours = total_frames // (3600 * self._fps)
        rem = total_frames % (3600 * self._fps)
        self._minutes = rem // (60 * self._fps)
        rem = rem % (60 * self._fps)
        self._seconds = rem // self._fps
        self._frames = rem % self._fps
        self._update_display()

    def _send_mtc_for_current_frame(self):
        """发送当前帧的MTC quarter-frame消息"""
        if not self._midi_out or not self._send_mtc:
            return
        fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)
        self._send_mtc_quarter_frame(0, self._frames & 0x0F)
        self._send_mtc_quarter_frame(1, (self._frames >> 4) & 0x01)
        self._send_mtc_quarter_frame(2, self._seconds & 0x0F)
        self._send_mtc_quarter_frame(3, (self._seconds >> 4) & 0x03)
        self._send_mtc_quarter_frame(4, self._minutes & 0x0F)
        self._send_mtc_quarter_frame(5, (self._minutes >> 4) & 0x03)
        self._send_mtc_quarter_frame(6, self._hours & 0x0F)
        self._send_mtc_quarter_frame(7, (fps_type << 1) | ((self._hours >> 4) & 0x01))
        self._log_timecode()

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
        self.logger.info(f"帧率: {self._fps} FPS")

    def _set_speed(self, mult):
        self._speed_multiplier = mult
        if self._running and not self._sync_mode:
            interval = max(1, int(1000 / self._fps / self._speed_multiplier))
            self._timer.setInterval(interval)
        self.logger.info(f"速度: {mult}x")

    def _on_set_timecode(self):
        self._hours = self._set_h.value()
        self._minutes = self._set_m.value()
        self._seconds = self._set_s.value()
        self._frames = self._set_f.value()
        self._update_display()

    def _on_sync_play(self):
        """同步播放: 音频 + MTC 同时启动"""
        if not self._audio_data:
            QMessageBox.information(self, "提示", "请先导入音频文件")
            return
        self._sync_mode = True
        self._on_start()
        self._start_audio_playback()
        self.logger.info("同步播放已启动 (音频+MTC)")

    def _on_start(self):
        if self._running:
            return
        self._running = True
        self._start_btn.setEnabled(False)
        self._sync_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)

        if self._midi_out and self._send_mtc:
            self._send_mtc_full_frame()
            self._send_mtc_start()

        if not self._sync_mode:
            interval = max(1, int(1000 / self._fps / self._speed_multiplier))
            self._timer.setInterval(interval)
            self._timer.start()
        self.logger.info("MTC发送已启动")

    def _on_stop(self):
        if not self._running:
            return
        self._running = False
        self._sync_mode = False
        self._timer.stop()

        if self._midi_out and self._send_mtc:
            self._send_mtc_stop()

        self._start_btn.setEnabled(True)
        self._sync_btn.setEnabled(bool(self._audio_data))
        self._stop_btn.setEnabled(False)
        self._on_stop_audio()
        self.logger.info("已停止")

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
                            self._hours = self._minutes = self._seconds = self._frames = 0
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

        if self._midi_out and self._send_mtc:
            fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)
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
        fps_type = {24: 0, 25: 1, 30: 3}.get(self._fps, 1)
        mtc_msg = f"F1:{(fps_type << 5) | (self._hours & 0x1F):02X} F2:{self._minutes:02X} F3:{self._seconds:02X} F4:{self._frames:02X}"
        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        row = len(self._tc_log) + 1

        html = (
            f'<span style="color:#555">#{row:>4d}</span> '
            f'<span style="color:#666">{now}</span> '
            f'<span style="color:#4ec9b0; font-weight:bold">{tc}</span> '
            f'<span style="color:#e8912d">{mtc_msg}</span> '
            f'<span style="color:#569cd6">帧{total_frames}</span>'
        )
        self._log_view.append(html)

        if row > 500:
            doc = self._log_view.document()
            if doc.blockCount() > 500:
                cursor = self._log_view.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.select(cursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()

        self._tc_log.append({'timestamp': now, 'smpte': tc, 'mtc': mtc_msg, 'frames': total_frames})
        self._log_count_label.setText(f"消息: {len(self._tc_log)}")

        sb = self._log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _clear_log(self):
        self._tc_log.clear()
        self._log_view.clear()
        self._log_count_label.setText("消息: 0")
        self._log_rate_label.setText("速率: 0/秒")

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出时间码日志", "timecode_log.csv", "CSV文件 (*.csv)")
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'smpte', 'mtc', 'frames'])
                writer.writeheader()
                writer.writerows(self._tc_log)
            self.logger.info(f"日志已导出: {path}")

    def closeEvent(self, event):
        self._on_stop()
        self._disconnect_midi()
        super().closeEvent(event)


if __name__ == '__main__':
    import traceback
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = TimecodeGenerator()
        window.show()
        window.raise_()
        window.activateWindow()
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
