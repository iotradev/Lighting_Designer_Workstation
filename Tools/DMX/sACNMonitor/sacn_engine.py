# -*- coding: utf-8 -*-
"""
sACN (E1.31) 引擎 - UDP多播监听与数据包解析
"""
import socket
import struct
import time
import threading
from collections import OrderedDict
from PySide6.QtCore import QThread, Signal, QObject

# sACN 常量
SACN_PORT = 5568
SACN_MULTICAST_BASE = 0xEF000000  # 239.x.x.x
SACN_ROOT_PREAMBLE_SIZE = 0x0010
SACN_ROOT_POSTAMBLE_SIZE = 0x0000
SACN_ROOT_ACN_PID = 0x4153432D45312E313700  # "ASC-E1.17\0"
SACN_ROOT_VECTOR = 0x00000004
SACN_FRAMING_VECTOR = 0x00000002
SACN_DMP_VECTOR = 0x02
SACN_DMP_ADDRESS_TYPE = 0xA1
SACN_DMP_FIRST_PROPERTY = 0x0000
SACN_DMP_ADDRESS_INCREMENT = 0x0001
SACN_START_CODE = 0x00

SACN_SOURCE_NAME_MAX = 64
SACN_DATA_LENGTH = 513  # start code + 512 channels


def get_multicast_address(universe):
    """根据universe编号计算多播地址"""
    return f"239.255.{(universe >> 8) & 0xFF}.{universe & 0xFF}"


class SACNSourceInfo:
    """sACN数据源信息"""
    def __init__(self, cid, source_name, universe, priority):
        self.cid = cid
        self.source_name = source_name
        self.universe = universe
        self.priority = priority
        self.sequence = 0
        self.last_seen = time.time()
        self.packet_count = 0
        self.dmx_data = bytearray(512)

    def update(self, priority, sequence, dmx_data):
        self.priority = priority
        self.sequence = sequence
        self.last_seen = time.time()
        self.packet_count += 1
        if dmx_data:
            self.dmx_data = dmx_data


class SACNPacketParser:
    """sACN数据包解析器"""

    @staticmethod
    def parse(data, addr=None):
        """
        解析sACN数据包，返回解析结果字典或None
        """
        try:
            if len(data) < 126:
                return None

            offset = 0

            # Root Layer
            preamble_size = struct.unpack('!H', data[0:2])[0]
            if preamble_size != SACN_ROOT_PREAMBLE_SIZE:
                return None
            postamble_size = struct.unpack('!H', data[2:4])[0]
            # bytes 4-13: ACN Packet Identifier "ASC-E1.17\0"
            # data[4:14] should match SACN_ROOT_ACN_PID (10 bytes)
            # Actually SACN_ROOT_ACN_PID is 10 bytes as bytes
            root_flags_length = struct.unpack('!H', data[14:16])[0]
            root_length = root_flags_length & 0x0FFF
            root_vector = struct.unpack('!I', data[16:20])[0]
            if root_vector != SACN_ROOT_VECTOR:
                return None
            # CID: 16 bytes at offset 20
            cid = data[20:36]

            offset = 36

            # Framing Layer
            fl_flags_length = struct.unpack('!H', data[offset:offset+2])[0]
            fl_length = fl_flags_length & 0x0FFF
            fr_vector = struct.unpack('!I', data[offset+2:offset+6])[0]
            if fr_vector != SACN_FRAMING_VECTOR:
                return None
            # Source Name: 64 bytes
            source_name_raw = data[offset+6:offset+70]
            source_name = source_name_raw.split(b'\x00')[0].decode('utf-8', errors='replace')
            priority = struct.unpack('!B', data[offset+70:offset+71])[0]
            # reserved: 2 bytes
            seq_number = struct.unpack('!B', data[offset+72:offset+73])[0]
            options = struct.unpack('!B', data[offset+73:offset+74])[0]
            universe = struct.unpack('!H', data[offset+74:offset+76])[0]

            offset = offset + 76

            # DMP Layer
            dm_flags_length = struct.unpack('!H', data[offset:offset+2])[0]
            dm_length = dm_flags_length & 0x0FFF
            dmp_vector = struct.unpack('!B', data[offset+2:offset+3])[0]
            if dmp_vector != SACN_DMP_VECTOR:
                return None
            address_type = struct.unpack('!B', data[offset+3:offset+4])[0]
            first_prop = struct.unpack('!H', data[offset+4:offset+6])[0]
            address_increment = struct.unpack('!H', data[offset+6:offset+8])[0]
            prop_count = struct.unpack('!H', data[offset+8:offset+10])[0]

            # DMX data: first byte is start code, then 512 channels
            dmx_raw = data[offset+10:offset+10+prop_count]
            start_code = dmx_raw[0] if len(dmx_raw) > 0 else -1
            dmx_data = bytearray(dmx_raw[1:]) if len(dmx_raw) > 1 else bytearray()
            # Pad to 512
            if len(dmx_data) < 512:
                dmx_data.extend(b'\x00' * (512 - len(dmx_data)))
            dmx_data = dmx_data[:512]

            return {
                'cid': cid,
                'source_name': source_name,
                'priority': priority,
                'sequence': seq_number,
                'universe': universe,
                'start_code': start_code,
                'dmx_data': dmx_data,
                'source_addr': addr,
            }
        except Exception:
            return None


class SACNListenerThread(QThread):
    """sACN多播监听线程"""
    packet_received = Signal(dict)  # 解析后的数据包
    error_occurred = Signal(str)
    status_changed = Signal(str)

    def __init__(self, universe=1, parent=None):
        super().__init__(parent)
        self.universe = universe
        self._running = False
        self._socket = None

    def set_universe(self, universe):
        self.universe = universe

    def stop(self):
        self._running = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass

    def run(self):
        self._running = True
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind(('', SACN_PORT))

            mcast_addr = get_multicast_address(self.universe)
            mcast_group = socket.inet_aton(mcast_addr)
            # Join multicast on all interfaces
            self._socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                struct.pack('4sL', mcast_group, socket.INADDR_ANY)
            )
            self._socket.settimeout(1.0)
            self.status_changed.emit(f"监听中: {mcast_addr}:{SACN_PORT}")

            while self._running:
                try:
                    data, addr = self._socket.recvfrom(1200)
                    parsed = SACNPacketParser.parse(data, addr)
                    if parsed:
                        self.packet_received.emit(parsed)
                except socket.timeout:
                    continue
                except OSError:
                    break
        except Exception as e:
            self.error_occurred.emit(f"监听错误: {e}")
        finally:
            if self._socket:
                try:
                    self._socket.close()
                except Exception:
                    pass
            self.status_changed.emit("已停止")


class SACNEngine(QObject):
    """sACN引擎 - 管理监听、源跟踪、数据包速率"""
    source_updated = Signal(str, int, int, str, int)  # source_name, universe, priority, cid_hex, seq
    dmx_data_updated = Signal(int, object)  # universe, bytearray(512)
    packet_rate_updated = Signal(float)  # packets/sec
    log_message = Signal(str)
    status_changed = Signal(str)

    SOURCE_TIMEOUT = 10.0  # 秒

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sources = OrderedDict()  # key=(cid_hex, universe) -> SACNSourceInfo
        self._listener = None
        self._selected_universe = 1
        self._packet_counter = 0
        self._rate_timer = None

    @property
    def selected_universe(self):
        return self._selected_universe

    def start_listening(self, universe=1):
        self._selected_universe = universe
        self._listener = SACNListenerThread(universe, self)
        self._listener.packet_received.connect(self._on_packet)
        self._listener.error_occurred.connect(self._on_error)
        self._listener.status_changed.connect(self.status_changed)
        self._listener.start()

        # 速率计算定时器
        self._rate_timer = threading.Timer(1.0, self._rate_tick)
        self._rate_timer.daemon = True
        self._rate_timer.start()

        self.log_message.emit(f"开始监听 Universe {universe}")

    def stop_listening(self):
        if self._listener:
            self._listener.stop()
            self._listener.wait(3000)
            self._listener = None
        if self._rate_timer:
            self._rate_timer.cancel()
            self._rate_timer = None
        self.log_message.emit("已停止监听")

    def _on_packet(self, pkt):
        self._packet_counter += 1
        cid_hex = pkt['cid'].hex()
        key = (cid_hex, pkt['universe'])
        src_name = pkt['source_name']

        if key not in self.sources:
            self.sources[key] = SACNSourceInfo(
                pkt['cid'], src_name, pkt['universe'], pkt['priority']
            )
            self.log_message.emit(f"发现新源: {src_name} (Universe {pkt['universe']})")

        self.sources[key].update(pkt['priority'], pkt['sequence'], pkt['dmx_data'])
        self.source_updated.emit(
            src_name, pkt['universe'], pkt['priority'],
            cid_hex[:12], pkt['sequence']
        )

        if pkt['universe'] == self._selected_universe:
            self.dmx_data_updated.emit(pkt['universe'], pkt['dmx_data'])

        # 清理超时源
        self._cleanup_sources()

    def _cleanup_sources(self):
        now = time.time()
        expired = [k for k, v in self.sources.items() if now - v.last_seen > self.SOURCE_TIMEOUT]
        for k in expired:
            name = self.sources[k].source_name
            del self.sources[k]
            self.log_message.emit(f"源超时移除: {name}")

    def _on_error(self, msg):
        self.log_message.emit(msg)

    def _rate_tick(self):
        rate = float(self._packet_counter)
        self._packet_counter = 0
        self.packet_rate_updated.emit(rate)
        if self._listener and self._listener._running:
            self._rate_timer = threading.Timer(1.0, self._rate_tick)
            self._rate_timer.daemon = True
            self._rate_timer.start()
