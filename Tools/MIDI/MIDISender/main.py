# -*- coding: utf-8 -*-
"""
MIDI发送器 - 主应用程序
MIDI消息发送工具，支持音符发送、CC控制、自定义消息和脚本执行
"""
import sys
from pathlib import Path

# 添加公共库路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'Common'))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QComboBox,
    QPushButton, QSlider, QLineEdit, QTextEdit, QSpinBox, QGroupBox,
    QGridLayout, QFrame, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent

from ui.base_window import BaseToolWindow
from midi_sender_engine import MIDISenderEngine, RTMIDI_AVAILABLE


# ===== 钢琴键盘控件 =====

class PianoKeyboard(QWidget):
    """自定义钢琴键盘控件"""
    note_pressed = Signal(int, int)  # note, velocity
    note_released = Signal(int)  # note

    # 白键和黑键的音符映射（一个八度内）
    WHITE_NOTES = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
    BLACK_NOTES = [1, 3, 6, 8, 10]         # C# D# F# G# A#

    def __init__(self, octaves: int = 4, start_octave: int = 2, parent=None):
        super().__init__(parent)
        self.octaves = octaves
        self.start_octave = start_octave
        self.velocity = 100
        self._pressed_keys = set()
        self._hover_key = -1
        self.setMinimumHeight(160)
        self.setMinimumWidth(600)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)
        self._white_key_width = 0
        self._white_key_height = 0

    def _total_white_keys(self):
        return self.octaves * 7 + 1  # +1 for the last C

    def _note_to_key_rect(self, note):
        """计算按键的矩形区域"""
        octave = (note // 12) - self.start_octave
        note_in_octave = note % 12

        w = self._white_key_width
        h = self._white_key_height

        if note_in_octave in self.WHITE_NOTES:
            # 白键
            white_index = self.WHITE_NOTES.index(note_in_octave)
            x = (octave * 7 + white_index) * w
            return (int(x), 0, int(w - 1), int(h)), True
        else:
            # 黑键
            black_index = self.BLACK_NOTES.index(note_in_octave)
            # 黑键位置：在对应白键之间
            white_map = {1: 0, 3: 1, 6: 3, 8: 4, 10: 5}
            parent_white = white_map[note_in_octave]
            x = (octave * 7 + parent_white) * w + w * 0.65
            bw = w * 0.65
            bh = h * 0.6
            return (int(x), 0, int(bw), int(bh)), False

    def _get_key_at_pos(self, x, y):
        """获取鼠标位置对应的音符"""
        w = self._white_key_width
        h = self._white_key_height

        # 先检查黑键（在上层）
        for octave in range(self.octaves):
            for note_in_octave in self.BLACK_NOTES:
                note = (self.start_octave + octave) * 12 + note_in_octave
                rect, is_white = self._note_to_key_rect(note)
                rx, ry, rw, rh = rect
                if rx <= x <= rx + rw and 0 <= y <= rh:
                    return note

        # 再检查白键
        if w > 0:
            white_key_index = int(x / w)
            octave = white_key_index // 7
            idx = white_key_index % 7
            if octave < self.octaves and idx < len(self.WHITE_NOTES):
                note = (self.start_octave + octave) * 12 + self.WHITE_NOTES[idx]
                return note

        return -1

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        total_white = self._total_white_keys()
        self._white_key_width = w / total_white
        self._white_key_height = h

        # 画白键
        for i in range(total_white):
            x = int(i * self._white_key_width)
            kw = int(self._white_key_width - 1)
            octave = i // 7
            idx = i % 7
            note = (self.start_octave + octave) * 12 + self.WHITE_NOTES[idx]

            if note in self._pressed_keys:
                painter.setBrush(QColor(100, 180, 255))
            elif note == self._hover_key:
                painter.setBrush(QColor(220, 230, 240))
            else:
                painter.setBrush(QColor(255, 255, 255))

            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawRect(x, 0, kw, int(h - 1))

            # 标注C音
            if idx == 0:
                painter.setPen(QColor(120, 120, 120))
                painter.setFont(QFont("Arial", 8))
                painter.drawText(x + 2, h - 8, f"C{self.start_octave + octave}")

        # 画黑键
        for octave in range(self.octaves):
            for note_in_octave in self.BLACK_NOTES:
                note = (self.start_octave + octave) * 12 + note_in_octave
                rect, _ = self._note_to_key_rect(note)
                rx, ry, rw, rh = rect

                if note in self._pressed_keys:
                    painter.setBrush(QColor(80, 150, 230))
                elif note == self._hover_key:
                    painter.setBrush(QColor(60, 60, 70))
                else:
                    painter.setBrush(QColor(30, 30, 30))

                painter.setPen(QPen(QColor(0, 0, 0), 1))
                painter.drawRect(rx, ry, rw, rh)

        painter.end()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            note = self._get_key_at_pos(int(event.position().x()), int(event.position().y()))
            if note >= 0:
                self._pressed_keys.add(note)
                self.note_pressed.emit(note, self.velocity)
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            for note in list(self._pressed_keys):
                self._pressed_keys.discard(note)
                self.note_released.emit(note)
            self.update()

    def mouseMoveEvent(self, event):
        note = self._get_key_at_pos(int(event.position().x()), int(event.position().y()))
        if note != self._hover_key:
            self._hover_key = note
            self.update()

    def leaveEvent(self, event):
        self._hover_key = -1
        self.update()


# ===== CC滑块组 =====

class CCFaderGroup(QWidget):
    """CC控制滑块组"""
    cc_changed = Signal(int, int)  # cc_number, value

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setSpacing(6)

        self.faders = {}
        self.labels = {}

        for i in range(16):
            row = 0
            col = i

            group = QVBoxLayout()
            group.setSpacing(2)

            # 值标签
            val_label = QLabel("64")
            val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val_label.setStyleSheet("color: #aaa; font-size: 10px;")
            group.addWidget(val_label)

            # 滑块
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(0, 127)
            slider.setValue(64)
            slider.setMinimumHeight(120)
            slider.valueChanged.connect(lambda val, cc=i, lbl=val_label: self._on_fader_changed(cc, val, lbl))
            group.addWidget(slider)

            # CC编号标签
            cc_label = QLabel(f"CC{i}")
            cc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cc_label.setStyleSheet("font-size: 10px; font-weight: bold;")
            group.addWidget(cc_label)

            layout.addLayout(group, row, col)
            self.faders[i] = slider
            self.labels[i] = val_label

    def _on_fader_changed(self, cc, value, label):
        label.setText(str(value))
        self.cc_changed.emit(cc, value)

    def set_fader_value(self, cc, value):
        if cc in self.faders:
            self.faders[cc].setValue(value)

    def reset_all(self):
        for slider in self.faders.values():
            slider.setValue(64)


# ===== 消息预设 =====

MIDI_PRESETS = [
    ("Note On C4 (通道1)", "90 3C 7F"),
    ("Note Off C4 (通道1)", "80 3C 00"),
    ("CC1 Modulation (通道1)", "B0 01 40"),
    ("CC7 Volume (通道1)", "B0 07 64"),
    ("CC10 Pan (通道1)", "B0 0A 40"),
    ("CC64 Sustain (通道1开)", "B0 40 7F"),
    ("CC64 Sustain (通道1关)", "B0 40 00"),
    ("CC123 All Notes Off (通道1)", "B0 7B 00"),
    ("CC120 All Sound Off (通道1)", "B0 78 00"),
    ("Program Change 0 (通道1)", "C0 00"),
    ("Program Change Piano (通道1)", "C0 00"),
    ("Program Change Strings (通道1)", "C0 28"),
    ("Pitch Bend Center (通道1)", "E0 00 40"),
    ("System Reset", "FF"),
    ("GM System On", "F0 7E 7F 09 01 F7"),
]


# ===== 主窗口 =====

class MIDISenderWindow(BaseToolWindow):
    """MIDI发送器主窗口"""

    def __init__(self):
        super().__init__(
            tool_name="MIDISender",
            tool_title="MIDI发送器",
            version="1.0.0",
            width=1000,
            height=750
        )

        self.engine = MIDISenderEngine()
        self.engine.set_message_callback(self._on_midi_message)

        self._init_ui()
        self._refresh_devices()

        # 状态定时器
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(1000)

        self.logger.info("MIDI发送器已就绪")

    def _init_ui(self):
        """构建中心UI"""
        central = QWidget()
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ===== 顶部：设备选择 =====
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("MIDI输出设备:"))

        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(250)
        top_bar.addWidget(self.device_combo)

        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.setFixedWidth(60)
        self.btn_refresh.clicked.connect(self._refresh_devices)
        top_bar.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton("连接")
        self.btn_connect.setFixedWidth(80)
        self.btn_connect.clicked.connect(self._toggle_connection)
        top_bar.addWidget(self.btn_connect)

        self.btn_virtual = QPushButton("虚拟端口")
        self.btn_virtual.setFixedWidth(80)
        self.btn_virtual.clicked.connect(self._open_virtual_port)
        top_bar.addWidget(self.btn_virtual)

        top_bar.addStretch()

        self.status_label = QLabel("● 未连接")
        self.status_label.setStyleSheet("color: #ff6666; font-weight: bold;")
        top_bar.addWidget(self.status_label)

        main_layout.addLayout(top_bar)

        # ===== 标签页 =====
        self.tabs = QTabWidget()

        # Tab 1: Note发送
        self.tabs.addTab(self._create_note_tab(), "🎹 Note发送")

        # Tab 2: CC控制
        self.tabs.addTab(self._create_cc_tab(), "🎚 CC控制")

        # Tab 3: 消息构建
        self.tabs.addTab(self._create_message_tab(), "📝 消息构建")

        # Tab 4: 脚本
        self.tabs.addTab(self._create_script_tab(), "📜 脚本")

        main_layout.addWidget(self.tabs, 1)

        # ===== 底部：快捷操作和消息日志 =====
        bottom_layout = QHBoxLayout()

        # 快捷按钮
        quick_group = QGroupBox("快捷操作")
        quick_layout = QHBoxLayout(quick_group)

        btn_panic = QPushButton("🔇 Panic (全静音)")
        btn_panic.setStyleSheet("background-color: #8b0000; color: white; font-weight: bold;")
        btn_panic.clicked.connect(self._on_panic)
        quick_layout.addWidget(btn_panic)

        btn_all_off = QPushButton("All Notes Off")
        btn_all_off.clicked.connect(lambda: self._send_all_notes_off())
        quick_layout.addWidget(btn_all_off)

        btn_reset_cc = QPushButton("重置CC")
        btn_reset_cc.clicked.connect(self._reset_cc_faders)
        quick_layout.addWidget(btn_reset_cc)

        bottom_layout.addWidget(quick_group)

        # 消息日志
        log_group = QGroupBox("发送日志")
        log_layout = QVBoxLayout(log_group)
        self.msg_log = QTextEdit()
        self.msg_log.setReadOnly(True)
        self.msg_log.setMaximumHeight(100)
        self.msg_log.setFont(QFont("Consolas", 9))
        log_layout.addWidget(self.msg_log)
        bottom_layout.addWidget(log_group, 1)

        main_layout.addLayout(bottom_layout)

        self.set_central_content(central)

    def _create_note_tab(self):
        """Tab1: Note发送"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 控制栏
        ctrl_layout = QHBoxLayout()

        ctrl_layout.addWidget(QLabel("通道:"))
        self.note_channel = QSpinBox()
        self.note_channel.setRange(1, 16)
        self.note_channel.setValue(1)
        self.note_channel.setFixedWidth(60)
        ctrl_layout.addWidget(self.note_channel)

        ctrl_layout.addWidget(QLabel("力度:"))
        self.velocity_slider = QSlider(Qt.Orientation.Horizontal)
        self.velocity_slider.setRange(1, 127)
        self.velocity_slider.setValue(100)
        self.velocity_slider.setFixedWidth(150)
        self.velocity_slider.valueChanged.connect(self._on_velocity_changed)
        ctrl_layout.addWidget(self.velocity_slider)

        self.velocity_label = QLabel("100")
        self.velocity_label.setFixedWidth(40)
        ctrl_layout.addWidget(self.velocity_label)

        self.velocity_bar = QProgressBar()
        self.velocity_bar.setRange(0, 127)
        self.velocity_bar.setValue(100)
        self.velocity_bar.setFixedWidth(100)
        self.velocity_bar.setTextVisible(False)
        ctrl_layout.addWidget(self.velocity_bar)

        ctrl_layout.addStretch()

        btn_send = QPushButton("发送当前音符")
        btn_send.setFixedWidth(100)
        ctrl_layout.addWidget(btn_send)

        layout.addLayout(ctrl_layout)

        # 钢琴键盘
        self.keyboard = PianoKeyboard(octaves=4, start_octave=2)
        self.keyboard.note_pressed.connect(self._on_key_pressed)
        self.keyboard.note_released.connect(self._on_key_released)
        layout.addWidget(self.keyboard, 1)

        return tab

    def _create_cc_tab(self):
        """Tab2: CC控制"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 通道选择
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("通道:"))
        self.cc_channel = QSpinBox()
        self.cc_channel.setRange(1, 16)
        self.cc_channel.setValue(1)
        self.cc_channel.setFixedWidth(60)
        ctrl.addWidget(self.cc_channel)
        ctrl.addStretch()

        btn_reset = QPushButton("重置全部")
        btn_reset.clicked.connect(self._reset_cc_faders)
        ctrl.addWidget(btn_reset)

        layout.addLayout(ctrl)

        # CC滑块组
        self.cc_group = CCFaderGroup()
        self.cc_group.cc_changed.connect(self._on_cc_changed)
        layout.addWidget(self.cc_group, 1)

        return tab

    def _create_message_tab(self):
        """Tab3: 消息构建"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 预设选择
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("-- 选择预设 --")
        for name, _ in MIDI_PRESETS:
            self.preset_combo.addItem(name)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_layout)

        # 通道选择（用于部分预设）
        ch_layout = QHBoxLayout()
        ch_layout.addWidget(QLabel("通道 (用于自动调整):"))
        self.msg_channel = QSpinBox()
        self.msg_channel.setRange(1, 16)
        self.msg_channel.setValue(1)
        self.msg_channel.setFixedWidth(60)
        ch_layout.addWidget(self.msg_channel)
        ch_layout.addStretch()
        layout.addLayout(ch_layout)

        # 十六进制输入
        hex_group = QGroupBox("十六进制消息")
        hex_layout = QVBoxLayout(hex_group)

        self.hex_input = QLineEdit()
        self.hex_input.setPlaceholderText("输入十六进制字节，空格分隔，如: 90 3C 7F")
        self.hex_input.setFont(QFont("Consolas", 11))
        self.hex_input.returnPressed.connect(self._send_raw_message)
        hex_layout.addWidget(self.hex_input)

        # 解析预览
        self.parse_label = QLabel("解析: (等待输入)")
        self.parse_label.setStyleSheet("color: #888;")
        hex_layout.addWidget(self.parse_label)

        btn_send = QPushButton("发送")
        btn_send.setFixedHeight(36)
        btn_send.setStyleSheet("font-size: 14px; font-weight: bold;")
        btn_send.clicked.connect(self._send_raw_message)
        hex_layout.addWidget(btn_send)

        layout.addWidget(hex_group)

        # 常见消息格式说明
        help_text = QLabel(
            "格式说明:\n"
            "  90-9F = Note On (通道1-16)   80-8F = Note Off\n"
            "  B0-BF = Control Change       C0-CF = Program Change\n"
            "  E0-EF = Pitch Bend           F0 = SysEx 开始\n"
            "  第二字节: 音符/CC号 (00-7F)   第三字节: 值 (00-7F)"
        )
        help_text.setStyleSheet("color: #999; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch()
        return tab

    def _create_script_tab(self):
        """Tab4: 脚本"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # 工具栏
        toolbar = QHBoxLayout()

        btn_run = QPushButton("▶ 执行")
        btn_run.setStyleSheet("background-color: #1a6b1a; color: white; font-weight: bold;")
        btn_run.setFixedWidth(80)
        btn_run.clicked.connect(self._run_script)
        toolbar.addWidget(btn_run)

        btn_stop = QPushButton("⏹ 停止")
        btn_stop.setStyleSheet("background-color: #6b1a1a; color: white;")
        btn_stop.setFixedWidth(80)
        btn_stop.clicked.connect(self._stop_script)
        toolbar.addWidget(btn_stop)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedWidth(60)
        btn_clear.clicked.connect(lambda: self.script_editor.clear())
        toolbar.addWidget(btn_clear)

        btn_example = QPushButton("示例脚本")
        btn_example.setFixedWidth(80)
        btn_example.clicked.connect(self._load_example_script)
        toolbar.addWidget(btn_example)

        toolbar.addStretch()

        self.script_status = QLabel("就绪")
        self.script_status.setStyleSheet("color: #aaa;")
        toolbar.addWidget(self.script_status)

        layout.addLayout(toolbar)

        # 脚本编辑器
        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Consolas", 11))
        self.script_editor.setPlaceholderText(
            "# 每行一条MIDI命令，支持的命令:\n"
            "# note_on <通道> <音符> <力度>\n"
            "# note_off <通道> <音符> [力度]\n"
            "# cc <通道> <CC号> <值>\n"
            "# program_change <通道> <程序号>\n"
            "# raw <十六进制字节...>\n"
            "# sleep <秒数>\n"
            "# # 这是注释"
        )
        layout.addWidget(self.script_editor, 1)

        return tab

    # ===== 事件处理 =====

    def _on_velocity_changed(self, value):
        self.velocity_label.setText(str(value))
        self.velocity_bar.setValue(value)
        self.keyboard.velocity = value

    def _on_key_pressed(self, note, velocity):
        ch = self.note_channel.value() - 1  # 内部0-15
        self.engine.send_note_on(ch, note, velocity)

    def _on_key_released(self, note):
        ch = self.note_channel.value() - 1
        self.engine.send_note_off(ch, note)

    def _on_cc_changed(self, cc, value):
        ch = self.cc_channel.value() - 1
        self.engine.send_cc(ch, cc, value)

    def _on_preset_selected(self, index):
        if index > 0 and index <= len(MIDI_PRESETS):
            _, hex_msg = MIDI_PRESETS[index - 1]
            self.hex_input.setText(hex_msg)
            self._update_parse_preview()

    def _send_raw_message(self):
        hex_str = self.hex_input.text().strip()
        if hex_str:
            success = self.engine.send_raw(hex_str)
            if not success:
                self.logger.warning(f"发送失败: {hex_str}")
        self._update_parse_preview()

    def _update_parse_preview(self):
        """更新解析预览"""
        hex_str = self.hex_input.text().strip()
        if not hex_str:
            self.parse_label.setText("解析: (等待输入)")
            return

        try:
            parts = hex_str.split()
            if len(parts) >= 1:
                status = int(parts[0], 16)
                msg_type = status & 0xF0
                ch = (status & 0x0F) + 1

                descriptions = {
                    0x80: "Note Off",
                    0x90: "Note On",
                    0xA0: "Polyphonic Aftertouch",
                    0xB0: "Control Change",
                    0xC0: "Program Change",
                    0xD0: "Channel Aftertouch",
                    0xE0: "Pitch Bend",
                    0xF0: "System Exclusive",
                }

                desc = descriptions.get(msg_type, f"状态: 0x{status:02X}")
                if msg_type in (0x80, 0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0):
                    desc += f" (通道 {ch})"
                if msg_type in (0x90, 0x80) and len(parts) >= 3:
                    desc += f"  音符={int(parts[1],16)}  力度={int(parts[2],16)}"
                elif msg_type == 0xB0 and len(parts) >= 3:
                    desc += f"  CC#{int(parts[1],16)}  值={int(parts[2],16)}"

                self.parse_label.setText(f"解析: {desc}")
                self.parse_label.setStyleSheet("color: #6f6;")
            else:
                self.parse_label.setText("解析: 格式错误")
                self.parse_label.setStyleSheet("color: #f66;")
        except Exception:
            self.parse_label.setText("解析: 无法解析")
            self.parse_label.setStyleSheet("color: #f66;")

    def _run_script(self):
        script = self.script_editor.toPlainText()
        if not script.strip():
            return

        self.script_status.setText("执行中...")
        self.script_status.setStyleSheet("color: #6f6;")

        def progress_cb(current, total, line):
            self.script_status.setText(f"执行中: {current}/{total}")

        self.engine.execute_script(script, progress_cb)

        # 定期检查完成状态
        self._script_check_timer = QTimer(self)
        self._script_check_timer.timeout.connect(self._check_script_done)
        self._script_check_timer.start(200)

    def _check_script_done(self):
        if not self.engine.is_script_running:
            self._script_check_timer.stop()
            self.script_status.setText("完成")
            self.script_status.setStyleSheet("color: #6f6;")
            QTimer.singleShot(3000, lambda: (
                self.script_status.setText("就绪"),
                self.script_status.setStyleSheet("color: #aaa;")
            ))

    def _stop_script(self):
        self.engine.stop_script()
        self.script_status.setText("已停止")
        self.script_status.setStyleSheet("color: #f66;")

    def _load_example_script(self):
        example = """# 示例MIDI脚本 - C大调音阶
# 通道1，音符，力度100
note_on 1 60 100
sleep 0.3
note_off 1 60
sleep 0.1
note_on 1 62 100
sleep 0.3
note_off 1 62
sleep 0.1
note_on 1 64 100
sleep 0.3
note_off 1 64
sleep 0.1
note_on 1 65 100
sleep 0.3
note_off 1 65
sleep 0.1
note_on 1 67 100
sleep 0.3
note_off 1 67
sleep 0.1
note_on 1 69 100
sleep 0.3
note_off 1 69
sleep 0.1
note_on 1 71 100
sleep 0.3
note_off 1 71
sleep 0.1
note_on 1 72 100
sleep 0.5
note_off 1 72
# 完成"""
        self.script_editor.setPlainText(example)

    def _on_panic(self):
        self.engine.send_panic()
        self.logger.info("已发送 Panic")

    def _send_all_notes_off(self):
        ch = self.note_channel.value() - 1
        self.engine.send_all_notes_off(ch)
        self.logger.info(f"已发送 All Notes Off (通道{ch+1})")

    def _reset_cc_faders(self):
        self.cc_group.reset_all()

    def _on_midi_message(self, msg):
        """MIDI消息回调 - 更新日志"""
        hex_str = ' '.join(f'{b:02X}' for b in msg)
        self.msg_log.append(f"TX: {hex_str}")
        # 限制日志行数
        doc = self.msg_log.document()
        if doc.blockCount() > 100:
            cursor = self.msg_log.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, 10)
            cursor.removeSelectedText()

    # ===== 设备管理 =====

    def _refresh_devices(self):
        """刷新设备列表"""
        self.device_combo.clear()
        ports = self.engine.get_output_ports()
        if ports:
            for port in ports:
                self.device_combo.addItem(port)
            self.logger.info(f"发现 {len(ports)} 个MIDI输出端口")
        else:
            self.device_combo.addItem("无可用MIDI设备")
            self.logger.warning("未发现MIDI输出设备")

    def _toggle_connection(self):
        """切换连接状态"""
        if self.engine.is_connected:
            self.engine.close_port()
            self.btn_connect.setText("连接")
            self.status_label.setText("● 未连接")
            self.status_label.setStyleSheet("color: #ff6666; font-weight: bold;")
        else:
            port = self.device_combo.currentIndex()
            if port >= 0:
                success = self.engine.open_port(port)
                if success:
                    self.btn_connect.setText("断开")
                    self.status_label.setText("● 已连接")
                    self.status_label.setStyleSheet("color: #66ff66; font-weight: bold;")
                else:
                    self.logger.error("连接失败")

    def _open_virtual_port(self):
        """打开虚拟端口"""
        success = self.engine.open_virtual_port("MIDISender")
        if success:
            self.btn_connect.setText("断开")
            self.status_label.setText("● 虚拟端口")
            self.status_label.setStyleSheet("color: #66aaff; font-weight: bold;")
            self.device_combo.addItem("虚拟端口: MIDISender")
            self.device_combo.setCurrentIndex(self.device_combo.count() - 1)

    def _update_status(self):
        """更新连接状态"""
        if not self.engine.is_connected:
            if "已连接" in self.status_label.text() or "虚拟端口" in self.status_label.text():
                self.status_label.setText("● 断开")
                self.status_label.setStyleSheet("color: #ff6666; font-weight: bold;")
                self.btn_connect.setText("连接")

    def closeEvent(self, event):
        """关闭窗口"""
        self.engine.shutdown()
        super().closeEvent(event)


def main():
    """应用程序入口"""
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("MIDI发送器")

    window = MIDISenderWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    import traceback
    try:

        main()
    except Exception as _e:
        traceback.print_exc()
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            _app = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "MIDISender - 启动错误",
                f"{type(_e).__name__}: {_e}\n\n请检查日志文件。")
        except Exception:
            pass
