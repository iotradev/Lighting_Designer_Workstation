# -*- coding: utf-8 -*-
"""
MIDI发送引擎 - MIDI输出核心
支持 rtmidi 实时发送，不可用时使用日志桩
"""
import time
import threading
import logging
from typing import Optional, List, Callable

logger = logging.getLogger("MIDISender")

try:
    import rtmidi
    RTMIDI_AVAILABLE = True
except ImportError:
    RTMIDI_AVAILABLE = False
    logger.warning("python-rtmidi 未安装，使用日志桩模式")


class MIDIStub:
    """rtmidi不可用时的桩实现"""
    def __init__(self):
        self._ports = []

    def get_ports(self):
        return ["[桩] 虚拟MIDI输出端口"]

    def open_port(self, port: int, name: str = ""):
        logger.info(f"[桩] 打开端口 {port}: {self._ports[port] if port < len(self._ports) else '未知'}")

    def open_virtual_port(self, name: str):
        logger.info(f"[桩] 打开虚拟端口: {name}")

    def close_port(self):
        logger.info(f"[桩] 关闭端口")

    def send_message(self, msg):
        hex_str = ' '.join(f'{b:02X}' for b in msg)
        logger.info(f"[桩] 发送MIDI: {hex_str}")


class MIDISenderEngine:
    """MIDI发送引擎"""

    def __init__(self):
        self._midi_out = None
        self._connected = False
        self._current_port = -1
        self._running_script = False
        self._script_thread: Optional[threading.Thread] = None
        self._message_callback: Optional[Callable] = None
        self._init_backend()

    def _init_backend(self):
        """初始化MIDI后端"""
        if RTMIDI_AVAILABLE:
            self._midi_out = rtmidi.MidiOut()
        else:
            self._midi_out = MIDIStub()

    def get_output_ports(self) -> List[str]:
        """获取可用输出端口列表"""
        try:
            return self._midi_out.get_ports()
        except Exception as e:
            logger.error(f"获取端口失败: {e}")
            return []

    def open_port(self, port_index: int) -> bool:
        """打开指定端口"""
        try:
            if self._connected:
                self.close_port()
            if RTMIDI_AVAILABLE:
                self._midi_out.open_port(port_index)
            else:
                self._midi_out.open_port(port_index)
            self._connected = True
            self._current_port = port_index
            logger.info(f"已连接MIDI端口 {port_index}")
            return True
        except Exception as e:
            logger.error(f"打开端口失败: {e}")
            return False

    def open_virtual_port(self, name: str = "MIDISender") -> bool:
        """打开虚拟端口"""
        try:
            if self._connected:
                self.close_port()
            if RTMIDI_AVAILABLE:
                self._midi_out.open_virtual_port(name)
            else:
                self._midi_out.open_virtual_port(name)
            self._connected = True
            self._current_port = -2  # 虚拟端口标记
            logger.info(f"已打开虚拟端口: {name}")
            return True
        except Exception as e:
            logger.error(f"打开虚拟端口失败: {e}")
            return False

    def close_port(self):
        """关闭当前端口"""
        try:
            if RTMIDI_AVAILABLE and self._midi_out:
                self._midi_out.close_port()
            self._connected = False
            self._current_port = -1
            logger.info("已断开MIDI端口")
        except Exception as e:
            logger.error(f"关闭端口失败: {e}")

    @property
    def is_connected(self) -> bool:
        return self._connected

    def set_message_callback(self, callback: Callable):
        """设置消息发送回调（用于UI日志显示）"""
        self._message_callback = callback

    def _send(self, msg: list):
        """发送原始MIDI消息"""
        try:
            if RTMIDI_AVAILABLE:
                self._midi_out.send_message(msg)
            else:
                self._midi_out.send_message(msg)
            if self._message_callback:
                self._message_callback(msg)
        except Exception as e:
            logger.error(f"发送MIDI失败: {e}")

    # ===== 高级消息发送 =====

    def send_note_on(self, channel: int, note: int, velocity: int):
        """发送 Note On"""
        channel = max(0, min(15, channel))
        note = max(0, min(127, note))
        velocity = max(0, min(127, velocity))
        self._send([0x90 | channel, note, velocity])

    def send_note_off(self, channel: int, note: int, velocity: int = 0):
        """发送 Note Off"""
        channel = max(0, min(15, channel))
        note = max(0, min(127, note))
        self._send([0x80 | channel, note, velocity])

    def send_cc(self, channel: int, cc: int, value: int):
        """发送 Control Change"""
        channel = max(0, min(15, channel))
        cc = max(0, min(127, cc))
        value = max(0, min(127, value))
        self._send([0xB0 | channel, cc, value])

    def send_program_change(self, channel: int, program: int):
        """发送 Program Change"""
        channel = max(0, min(15, channel))
        program = max(0, min(127, program))
        self._send([0xC0 | channel, program])

    def send_pitch_bend(self, channel: int, value: int):
        """发送 Pitch Bend (0-16383, 8192为中心)"""
        channel = max(0, min(15, channel))
        value = max(0, min(16383, value))
        lsb = value & 0x7F
        msb = (value >> 7) & 0x7F
        self._send([0xE0 | channel, lsb, msb])

    def send_raw(self, hex_string: str) -> bool:
        """发送原始十六进制消息，如 '90 3C 7F'"""
        try:
            parts = hex_string.strip().split()
            msg = [int(p, 16) for p in parts]
            self._send(msg)
            return True
        except Exception as e:
            logger.error(f"解析MIDI消息失败: {e}")
            return False

    def send_all_notes_off(self, channel: int):
        """发送 All Notes Off (CC 123)"""
        self.send_cc(channel, 123, 0)

    def send_panic(self):
        """紧急关闭所有通道所有音符"""
        for ch in range(16):
            for note in range(128):
                self.send_note_off(ch, note, 0)
            self.send_cc(ch, 123, 0)  # All Notes Off
            self.send_cc(ch, 120, 0)  # All Sound Off
        logger.info("已发送 Panic (全通道静音)")

    # ===== 脚本执行 =====

    def execute_script(self, script_text: str, callback: Optional[Callable] = None):
        """
        执行MIDI脚本（在后台线程中运行）
        脚本格式（每行一条）:
            note_on <channel> <note> <velocity>
            note_off <channel> <note> [velocity]
            cc <channel> <cc_number> <value>
            program_change <channel> <program>
            raw <hex_bytes...>
            sleep <seconds>
            # 注释
        """
        if self._running_script:
            logger.warning("脚本正在运行中")
            return

        self._running_script = True
        self._script_thread = threading.Thread(
            target=self._run_script, args=(script_text, callback), daemon=True
        )
        self._script_thread.start()

    def stop_script(self):
        """停止脚本执行"""
        self._running_script = False
        logger.info("脚本已停止")

    @property
    def is_script_running(self) -> bool:
        return self._running_script

    def _run_script(self, script_text: str, callback: Optional[Callable]):
        """脚本执行线程"""
        lines = script_text.strip().split('\n')
        total = len(lines)

        for i, line in enumerate(lines):
            if not self._running_script:
                break

            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            cmd = parts[0].lower()

            try:
                if cmd == 'note_on' and len(parts) >= 4:
                    ch, note, vel = int(parts[1]), int(parts[2]), int(parts[3])
                    self.send_note_on(ch, note, vel)
                elif cmd == 'note_off' and len(parts) >= 3:
                    ch, note = int(parts[1]), int(parts[2])
                    vel = int(parts[3]) if len(parts) > 3 else 0
                    self.send_note_off(ch, note, vel)
                elif cmd == 'cc' and len(parts) >= 4:
                    ch, cc_num, val = int(parts[1]), int(parts[2]), int(parts[3])
                    self.send_cc(ch, cc_num, val)
                elif cmd == 'program_change' and len(parts) >= 3:
                    ch, prog = int(parts[1]), int(parts[2])
                    self.send_program_change(ch, prog)
                elif cmd == 'raw' and len(parts) >= 2:
                    hex_str = ' '.join(parts[1:])
                    self.send_raw(hex_str)
                elif cmd == 'sleep' and len(parts) >= 2:
                    time.sleep(float(parts[1]))
                else:
                    logger.warning(f"脚本第{i+1}行无法解析: {line}")

                if callback:
                    callback(i + 1, total, line)

            except Exception as e:
                logger.error(f"脚本第{i+1}行执行失败: {e}")

        self._running_script = False
        if callback:
            callback(total, total, "[完成]")
        logger.info("脚本执行完成")

    def shutdown(self):
        """关闭引擎"""
        self._running_script = False
        if self._connected:
            self.close_port()
        if RTMIDI_AVAILABLE and self._midi_out:
            del self._midi_out
        logger.info("MIDI引擎已关闭")
