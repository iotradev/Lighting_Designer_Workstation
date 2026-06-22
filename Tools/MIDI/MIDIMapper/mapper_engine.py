# -*- coding: utf-8 -*-
"""
MIDI映射引擎 - MIDI输入处理、映射存储、消息路由
支持 rtmidi 或 stub 模式（无硬件时使用模拟）
"""
import json
import time
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal, QTimer

# 尝试导入 rtmidi
try:
    import rtmidi
    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False


@dataclass
class MIDIMessage:
    """MIDI消息数据"""
    msg_type: str = "CC"        # CC, NoteOn, NoteOff, PitchBend, Aftertouch
    channel: int = 0            # 0-15
    number: int = 0             # CC number / Note number
    value: int = 0              # 0-127
    timestamp: float = 0.0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def key(self):
        """用于映射匹配的唯一键"""
        return (self.msg_type, self.channel, self.number)

    def display_text(self):
        """显示文本"""
        return f"{self.msg_type} CH{self.channel+1} #{self.number} Val:{self.value}"


@dataclass
class MappingEntry:
    """单条映射"""
    input_type: str = "CC"          # CC, NoteOn, NoteOff
    input_channel: int = 0          # 0-15
    input_number: int = 0           # CC/Note number
    output_action: str = "DMX通道"  # DMX通道, 场景触发, 宏命令, 无
    output_param: str = "1/255"     # action-specific parameter
    enabled: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    def display_input(self):
        return f"{self.input_type} CH{self.input_channel+1} #{self.input_number}"


class MapperEngine(QObject):
    """MIDI映射引擎"""
    midi_received = Signal(object)   # MIDIMessage
    mapping_triggered = Signal(object, object)  # MappingEntry, MIDIMessage
    device_list_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mappings: list[MappingEntry] = []
        self.learn_mode = False
        self.learn_callback: Optional[Callable] = None
        self._midi_in = None
        self._midi_out = None
        self._current_device = None
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_midi)
        self._last_devices = []

    # ===== 设备管理 =====
    def get_input_devices(self) -> list[str]:
        """获取MIDI输入设备列表"""
        if RTMIDI_AVAILABLE:
            try:
                midi_in = rtmidi.MidiIn()
                devices = [midi_in.get_port_name(i) for i in range(midi_in.get_port_count())]
                del midi_in
                return devices
            except Exception:
                pass
        return ["(模拟MIDI设备 - 无硬件)"]

    def get_output_devices(self) -> list[str]:
        """获取MIDI输出设备列表"""
        if RTMIDI_AVAILABLE:
            try:
                midi_out = rtmidi.MidiOut()
                devices = [midi_out.get_port_name(i) for i in range(midi_out.get_port_count())]
                del midi_out
                return devices
            except Exception:
                pass
        return ["(模拟MIDI输出 - 无硬件)"]

    def open_input(self, device_name: str) -> bool:
        """打开MIDI输入设备"""
        self.close_input()
        if not RTMIDI_AVAILABLE:
            self._current_device = device_name
            self._poll_timer.start(100)
            return True
        try:
            self._midi_in = rtmidi.MidiIn()
            devices = self.get_input_devices()
            if device_name in devices:
                idx = devices.index(device_name)
                self._midi_in.open_port(idx)
                self._midi_in.set_callback(self._rtmidi_callback)
                self._current_device = device_name
                return True
        except Exception:
            pass
        return False

    def close_input(self):
        """关闭MIDI输入"""
        self._poll_timer.stop()
        if self._midi_in:
            try:
                self._midi_in.close_port()
                del self._midi_in
            except Exception:
                pass
            self._midi_in = None
        self._current_device = None

    def _rtmidi_callback(self, msg_data, time_stamp):
        """rtmidi回调"""
        if msg_data and len(msg_data[0]) >= 3:
            parsed = self._parse_raw_message(msg_data[0])
            if parsed:
                parsed.timestamp = time.time()
                self._process_message(parsed)

    def _poll_midi(self):
        """Stub模式轮询（无实际硬件）"""
        pass

    def _parse_raw_message(self, data: bytes) -> Optional[MIDIMessage]:
        """解析原始MIDI字节"""
        if len(data) < 3:
            return None
        status = data[0]
        channel = status & 0x0F
        msg_type = status & 0xF0
        if msg_type == 0x90 and data[2] > 0:
            return MIDIMessage("NoteOn", channel, data[1], data[2])
        elif msg_type == 0x90 and data[2] == 0:
            return MIDIMessage("NoteOff", channel, data[1], 0)
        elif msg_type == 0x80:
            return MIDIMessage("NoteOff", channel, data[1], data[2])
        elif msg_type == 0xB0:
            return MIDIMessage("CC", channel, data[1], data[2])
        elif msg_type == 0xE0:
            val = (data[2] << 7) | data[1]
            return MIDIMessage("PitchBend", channel, 0, val)
        return None

    def _process_message(self, msg: MIDIMessage):
        """处理收到的MIDI消息"""
        self.midi_received.emit(msg)
        # Learn模式下捕获第一条消息
        if self.learn_mode and self.learn_callback:
            self.learn_callback(msg)
            return
        # 查找映射并触发
        for entry in self.mappings:
            if not entry.enabled:
                continue
            if (entry.input_type == msg.msg_type and
                entry.input_channel == msg.channel and
                entry.input_number == msg.number):
                self.mapping_triggered.emit(entry, msg)

    # ===== 测试模式 =====
    def send_test_message(self, msg: MIDIMessage):
        """发送测试MIDI消息（模拟收到）"""
        msg.timestamp = time.time()
        self._process_message(msg)

    # ===== 映射管理 =====
    def add_mapping(self, entry: MappingEntry):
        self.mappings.append(entry)

    def remove_mapping(self, index: int):
        if 0 <= index < len(self.mappings):
            self.mappings.pop(index)

    def update_mapping(self, index: int, entry: MappingEntry):
        if 0 <= index < len(self.mappings):
            self.mappings[index] = entry

    def get_mappings(self) -> list[MappingEntry]:
        return self.mappings

    def clear_mappings(self):
        self.mappings.clear()

    # ===== 存储 =====
    def save_profile(self, path: str):
        """保存映射配置到JSON"""
        data = {
            "version": "1.0",
            "mappings": [m.to_dict() for m in self.mappings]
        }
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_profile(self, path: str):
        """从JSON加载映射配置"""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.mappings.clear()
        for d in data.get("mappings", []):
            self.mappings.append(MappingEntry.from_dict(d))

    # ===== Learn模式 =====
    def start_learn(self, callback: Callable):
        self.learn_mode = True
        self.learn_callback = callback

    def stop_learn(self):
        self.learn_mode = False
        self.learn_callback = None
