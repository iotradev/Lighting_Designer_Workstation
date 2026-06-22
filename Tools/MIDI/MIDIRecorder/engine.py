"""MIDI录制引擎 - 录制、回放和导出MIDI消息"""

import struct
import time
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class MIDIMessageType(Enum):
    NOTE_ON = 0x90
    NOTE_OFF = 0x80
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    PITCH_BEND = 0xE0


@dataclass
class MIDIMessage:
    timestamp: float       # 秒
    status: int            # 状态字节
    data1: int             # 第一个数据字节
    data2: int             # 第二个数据字节
    message_type: str = "" # 可读类型名

    def __post_init__(self):
        if not self.message_type:
            msg_type = self.status & 0xF0
            channel = self.status & 0x0F
            type_names = {
                0x80: "Note Off",
                0x90: "Note On",
                0xB0: "Control Change",
                0xC0: "Program Change",
                0xE0: "Pitch Bend",
            }
            name = type_names.get(msg_type, f"Unknown (0x{msg_type:02X})")
            self.message_type = f"{name} Ch{channel + 1}"

    @property
    def channel(self) -> int:
        return self.status & 0x0F

    @property
    def raw_type(self) -> int:
        return self.status & 0xF0

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "status": self.status,
            "data1": self.data1,
            "data2": self.data2,
            "message_type": self.message_type,
        }


class MIDIEngine:
    """MIDI录制引擎"""

    def __init__(self):
        self.messages: List[MIDIMessage] = []
        self.is_recording = False
        self.is_playing = False
        self.is_paused = False
        self.record_start_time = 0.0
        self._input_device = None
        self._playback_timer = None

    def start_record(self):
        """开始录制"""
        self.messages.clear()
        self.is_recording = True
        self.record_start_time = time.time()

    def stop_record(self):
        """停止录制"""
        self.is_recording = False

    def add_message(self, status: int, data1: int, data2: int, timestamp: float = None):
        """添加MIDI消息"""
        if timestamp is None:
            timestamp = time.time() - self.record_start_time

        msg = MIDIMessage(
            timestamp=timestamp,
            status=status,
            data1=data1,
            data2=data2,
        )
        self.messages.append(msg)
        return msg

    def try_open_input(self) -> Optional[str]:
        """尝试打开MIDI输入设备"""
        try:
            import rtmidi
            midi_in = rtmidi.MidiIn()
            ports = midi_in.get_ports()
            if ports:
                midi_in.open_port(0)
                self._input_device = midi_in
                return ports[0]
            else:
                return None
        except ImportError:
            return None
        except Exception:
            if 'midi_in' in dir():
                try:
                    del midi_in
                except Exception:
                    pass
            return None

    def set_callback(self, callback):
        """设置MIDI回调函数"""
        if self._input_device:
            def _callback(message, data):
                if self.is_recording and message:
                    status, data1, data2 = message[0], message[1] if len(message) > 1 else 0, message[2] if len(message) > 2 else 0
                    self.add_message(status, data1, data2)
                    if callback:
                        callback(status, data1, data2)
            self._input_device.set_callback(_callback)

    def close_input(self):
        """关闭输入设备"""
        if self._input_device:
            try:
                self._input_device.close_port()
            except Exception:
                pass
            self._input_device = None

    def export_csv(self, filepath: str):
        """导出到CSV"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("时间戳(秒),状态字节,数据1,数据2,消息类型\n")
            for msg in self.messages:
                f.write(f"{msg.timestamp:.4f},"
                        f"0x{msg.status:02X},"
                        f"{msg.data1},"
                        f"{msg.data2},"
                        f"\"{msg.message_type}\"\n")

    def export_midi(self, filepath: str, bpm: int = 120):
        """导出为标准MIDI文件(.mid)"""
        if not self.messages:
            return

        # MIDI文件格式
        ticks_per_beat = 480
        tempo_microseconds = int(60_000_000 / bpm)

        # 构建Track数据
        track_data = bytearray()

        # 写入tempo事件 (Meta Event FF 51 03 + tempo)
        track_data += self._write_var_len(0)  # delta time = 0
        track_data += b'\xFF\x51\x03'
        track_data += struct.pack('>I', tempo_microseconds)[1:]  # 3字节

        prev_tick = 0
        for msg in self.messages:
            # 时间转换为ticks
            beat_time = msg.timestamp * bpm / 60.0
            tick = int(beat_time * ticks_per_beat)
            delta = tick - prev_tick
            prev_tick = tick

            # 写入delta time
            track_data += self._write_var_len(delta)

            # 写入MIDI事件
            if msg.raw_type == 0xC0:  # Program Change只有1个数据字节
                track_data += bytes([msg.status, msg.data1])
            else:
                track_data += bytes([msg.status, msg.data1, msg.data2])

        # End of Track
        track_data += b'\x00\xFF\x2F\x00'

        # 写入MIDI文件
        with open(filepath, 'wb') as f:
            # Header: MThd
            f.write(b'MThd')
            f.write(struct.pack('>I', 6))       # header length
            f.write(struct.pack('>H', 0))       # format type 0
            f.write(struct.pack('>H', 1))       # 1 track
            f.write(struct.pack('>H', ticks_per_beat))

            # Track: MTrk
            f.write(b'MTrk')
            f.write(struct.pack('>I', len(track_data)))
            f.write(track_data)

    def _write_var_len(self, value: int) -> bytes:
        """写入变长数值"""
        result = bytearray()
        result.append(value & 0x7F)
        value >>= 7
        while value:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.reverse()
        return bytes(result)

    def clear(self):
        """清空所有消息"""
        self.messages.clear()
        self.is_recording = False
        self.is_playing = False
        self.is_paused = False
