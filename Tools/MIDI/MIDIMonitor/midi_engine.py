# -*- coding: utf-8 -*-
"""
MIDI Monitor Engine
基于 python-rtmidi 的 MIDI 监控引擎，若 rtmidi 不可用则使用模拟数据桩。
"""
import time
import random
import threading
from dataclasses import dataclass, field
from typing import Optional, Callable, List

# 尝试导入 rtmidi
try:
    import rtmidi
    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False


# MIDI 消息类型常量
MSG_TYPE_NAMES = {
    0x80: "音符关闭",
    0x90: "音符开启",
    0xA0: "触后压力",
    0xB0: "控制变化",
    0xC0: "程序变化",
    0xD0: "通道压力",
    0xE0: "弯音",
    0xF0: "系统消息",
}


@dataclass
class MIDIMessage:
    """MIDI 消息数据结构"""
    timestamp: float
    status: int
    channel: int
    data1: int
    data2: int
    msg_type: int
    msg_type_name: str
    raw: tuple = field(default_factory=tuple)


class MIDIEngine:
    """MIDI 监控引擎"""

    def __init__(self, callback: Optional[Callable[[MIDIMessage], None]] = None):
        self.callback = callback
        self._running = False
        self._midi_in = None
        self._stub_thread: Optional[threading.Thread] = None
        self._current_device = None
        self._virtual_mode = False
        self._stats_lock = threading.Lock()

        # 统计信息
        self.msg_count = 0
        self.active_notes: dict = {}          # {(ch, note): velocity}
        self.cc_values: dict = {}             # {(ch, cc): value}
        self.msg_type_counts: dict = {}       # {type_name: count}

    # ------------------------------------------------------------------
    # 设备枚举
    # ------------------------------------------------------------------
    def get_input_devices(self) -> List[str]:
        """获取可用 MIDI 输入设备列表"""
        if RTMIDI_AVAILABLE:
            midi_in = rtmidi.MidiIn()
            ports = midi_in.get_ports()
            del midi_in
            return ports
        return ["[演示] 模拟 MIDI 输入"]

    def get_output_devices(self) -> List[str]:
        """获取可用 MIDI 输出设备（用于虚拟端口）"""
        if RTMIDI_AVAILABLE:
            midi_out = rtmidi.MidiOut()
            ports = midi_out.get_ports()
            del midi_out
            return ports
        return []

    # ------------------------------------------------------------------
    # 启动 / 停止
    # ------------------------------------------------------------------
    def start(self, device_name: Optional[str] = None, virtual: bool = False):
        """开始监听 MIDI"""
        if self._running:
            return
        self._running = True
        self.msg_count = 0
        self.active_notes.clear()
        self.cc_values.clear()
        self.msg_type_counts.clear()

        if virtual and RTMIDI_AVAILABLE:
            self._start_virtual(device_name or "MIDIMonitor 虚拟端口")
        elif RTMIDI_AVAILABLE:
            self._start_real(device_name)
        else:
            self._start_stub()

    def stop(self):
        """停止监听"""
        self._running = False
        if self._midi_in is not None:
            try:
                self._midi_in.close_port()
            except Exception:
                pass
            self._midi_in = None
        self._virtual_mode = False

    # ------------------------------------------------------------------
    # 内部启动方法
    # ------------------------------------------------------------------
    def _start_real(self, device_name: str):
        """使用 rtmidi 打开真实设备"""
        self._midi_in = rtmidi.MidiIn()
        ports = self._midi_in.get_ports()
        if device_name and device_name in ports:
            port_index = ports.index(device_name)
        elif ports:
            port_index = 0
        else:
            self._running = False
            return
        self._midi_in.open_port(port_index)
        self._midi_in.set_callback(self._rtmidi_callback)

    def _start_virtual(self, port_name: str):
        """打开虚拟 MIDI 端口"""
        self._midi_in = rtmidi.MidiIn()
        self._midi_in.open_virtual_port(port_name)
        self._midi_in.set_callback(self._rtmidi_callback)
        self._virtual_mode = True

    def _start_stub(self):
        """启动模拟数据桩"""
        self._stub_thread = threading.Thread(target=self._stub_loop, daemon=True)
        self._stub_thread.start()

    # ------------------------------------------------------------------
    # 回调
    # ------------------------------------------------------------------
    def _rtmidi_callback(self, message, data=None):
        """rtmidi 回调"""
        msg_tuple, _delta = message
        if not self._running:
            return
        if len(msg_tuple) < 2:
            return
        parsed = self._parse_message(msg_tuple)
        if parsed:
            self._update_stats(parsed)
            if self.callback:
                self.callback(parsed)

    def _stub_loop(self):
        """模拟 MIDI 数据生成循环"""
        note = 60
        cc_num = 1
        while self._running:
            time.sleep(random.uniform(0.05, 0.3))
            if not self._running:
                break
            r = random.random()
            if r < 0.35:
                # Note On
                note = random.randint(36, 84)
                vel = random.randint(40, 127)
                raw = (0x90, note, vel)
            elif r < 0.55:
                # Note Off
                raw = (0x80, note, 0)
            elif r < 0.80:
                # CC
                cc_num = random.randint(1, 127)
                raw = (0xB0, cc_num, random.randint(0, 127))
            elif r < 0.90:
                # Program Change
                raw = (0xC0, random.randint(0, 127), 0)
            else:
                # Pitch Bend
                raw = (0xE0, random.randint(0, 127), random.randint(0, 127))

            parsed = self._parse_message(raw)
            if parsed:
                self._update_stats(parsed)
                if self.callback:
                    self.callback(parsed)

    # ------------------------------------------------------------------
    # 解析
    # ------------------------------------------------------------------
    def _parse_message(self, raw: tuple) -> Optional[MIDIMessage]:
        status = raw[0]
        msg_type = status & 0xF0
        channel = (status & 0x0F) + 1
        data1 = raw[1] if len(raw) > 1 else 0
        data2 = raw[2] if len(raw) > 2 else 0
        type_name = MSG_TYPE_NAMES.get(msg_type, f"未知(0x{msg_type:02X})")

        return MIDIMessage(
            timestamp=time.time(),
            status=status,
            channel=channel,
            data1=data1,
            data2=data2,
            msg_type=msg_type,
            msg_type_name=type_name,
            raw=raw,
        )

    # ------------------------------------------------------------------
    # 统计
    # ------------------------------------------------------------------
    def _update_stats(self, msg: MIDIMessage):
        with self._stats_lock:
            self.msg_count += 1
            self.msg_type_counts[msg.msg_type_name] = \
                self.msg_type_counts.get(msg.msg_type_name, 0) + 1

            if msg.msg_type == 0x90 and msg.data2 > 0:
                self.active_notes[(msg.channel, msg.data1)] = msg.data2
            elif msg.msg_type == 0x80 or (msg.msg_type == 0x90 and msg.data2 == 0):
                self.active_notes.pop((msg.channel, msg.data1), None)
            elif msg.msg_type == 0xB0:
                self.cc_values[(msg.channel, msg.data1)] = msg.data2

    def get_stats_snapshot(self):
        with self._stats_lock:
            return {
                'msg_count': self.msg_count,
                'active_notes': dict(self.active_notes),
                'cc_values': dict(self.cc_values),
                'msg_type_counts': dict(self.msg_type_counts),
            }
