# -*- coding: utf-8 -*-
"""
Art-Net 引擎 - UDP 监听与 Art-Net 数据包解析
"""
import socket
import struct
import time
import threading
from collections import defaultdict

from PySide6.QtCore import QThread, Signal, QObject


# Art-Net 操作码
ARTNET_OP_POLL = 0x2000
ARTNET_OP_POLL_REPLY = 0x2100
ARTNET_OP_DMX = 0x5000
ARTNET_PORT = 6454
ARTNET_HEADER = b"Art-Net\x00"


class UniverseData:
    """单个 Universe 的 DMX 数据"""
    __slots__ = ("channels", "sequence", "physical", "last_update", "packet_count",
                 "rate_counter", "rate", "rate_ts")

    def __init__(self):
        self.channels = bytearray(512)
        self.sequence = 0
        self.physical = 0
        self.last_update = 0.0
        self.packet_count = 0
        self.rate_counter = 0
        self.rate = 0.0
        self.rate_ts = time.time()

    def update(self, sequence: int, physical: int, data: bytes):
        length = min(len(data), 512)
        self.channels[:length] = data[:length]
        if len(data) < 512:
            self.channels[len(data):] = b"\x00" * (512 - len(data))
        self.sequence = sequence
        self.physical = physical
        self.last_update = time.time()
        self.packet_count += 1
        self.rate_counter += 1
        now = time.time()
        elapsed = now - self.rate_ts
        if elapsed >= 1.0:
            self.rate = self.rate_counter / elapsed
            self.rate_counter = 0
            self.rate_ts = now


class ArtnetListener(QThread):
    """Art-Net UDP 监听线程"""
    packet_received = Signal(int, int, int, float)       # universe_key, seq, data_len, rate
    node_found = Signal(str, str)                         # ip, name
    error_occurred = Signal(str)
    status_changed = Signal(str)
    log_entry = Signal(str, int, int, int)                # timestamp_str, universe, size, sequence

    def __init__(self, bind_addr: str = "0.0.0.0", port: int = ARTNET_PORT, parent=None):
        super().__init__(parent)
        self.bind_addr = bind_addr
        self.port = port
        self._running = False
        self._sock = None
        self.universes: dict[int, UniverseData] = {}
        self._known_nodes: dict[str, float] = {}  # ip -> last_seen
        self._lock = threading.Lock()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

    def get_universe_data(self, key: int) -> UniverseData | None:
        with self._lock:
            return self.universes.get(key)

    def get_active_universes(self) -> list[tuple[int, float, int]]:
        """返回 [(universe_key, rate, packet_count), ...]"""
        with self._lock:
            return [(k, u.rate, u.packet_count) for k, u in sorted(self.universes.items())]

    def send_poll(self):
        """发送 ArtPoll 包发现节点"""
        if not self._sock:
            return
        # ArtPoll: header(8) + opcode(2) + protver(2) + flags(1) + diagpriority(1) = 14 bytes
        poll = ARTNET_HEADER + struct.pack("<H", ARTNET_OP_POLL) + struct.pack("<H", 14) + b"\x00\x00"
        try:
            self._sock.sendto(poll, ("255.255.255.255", self.port))
        except OSError as e:
            self.error_occurred.emit(f"ArtPoll 发送失败: {e}")

    def run(self):
        self._running = True
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._sock.settimeout(0.5)
            self._sock.bind((self.bind_addr, self.port))
            self.status_changed.emit(f"已连接 - {self.bind_addr}:{self.port}")
        except OSError as e:
            self.error_occurred.emit(f"绑定失败: {e}")
            self._running = False
            if self._sock:
                try:
                    self._sock.close()
                except OSError:
                    pass
                self._sock = None
            return

        # 发送 ArtPoll
        self.send_poll()

        while self._running:
            try:
                data, addr = self._sock.recvfrom(1500)
            except socket.timeout:
                continue
            except OSError:
                if self._running:
                    continue
                break

            if len(data) < 12:
                continue
            if data[:8] != ARTNET_HEADER:
                continue

            opcode = struct.unpack_from("<H", data, 8)[0]

            if opcode == ARTNET_OP_DMX:
                self._parse_artdmx(data, addr)
            elif opcode == ARTNET_OP_POLL_REPLY:
                self._parse_poll_reply(data, addr)

        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        self.status_changed.emit("已断开")

    def _parse_artdmx(self, data: bytes, addr: tuple):
        if len(data) < 18:
            return
        # Opcode(2) already read, now: ProtVer(2) at offset 10
        protver = struct.unpack_from("<H", data, 10)[0]
        sequence = data[12]
        physical = data[13]
        subuni = data[14]
        net = data[15]
        dmx_length = struct.unpack_from(">H", data, 16)[0]  # big-endian per spec

        if len(data) < 18 + dmx_length:
            return

        universe_key = (net << 8) | subuni
        dmx_data = bytes(data[18:18 + dmx_length])
        ts_str = time.strftime("%H:%M:%S")

        with self._lock:
            if universe_key not in self.universes:
                self.universes[universe_key] = UniverseData()
            udata = self.universes[universe_key]
            udata.update(sequence, physical, dmx_data)

        self.packet_received.emit(universe_key, sequence, dmx_length, udata.rate)
        self.log_entry.emit(ts_str, universe_key, dmx_length, sequence)

    def _parse_poll_reply(self, data: bytes, addr: tuple):
        """解析 ArtPollReply 获取节点信息"""
        ip = addr[0]
        if ip not in self._known_nodes:
            self._known_nodes[ip] = time.time()
            # Node name 通常在偏移 18 处，18 字节短名，64 字节长名
            name = "Art-Net 节点"
            if len(data) > 26:
                try:
                    short_name = data[26:44].split(b"\x00")[0].decode("ascii", errors="replace")
                    if short_name.strip():
                        name = short_name.strip()
                except Exception:
                    pass
            self.node_found.emit(ip, name)
