# -*- coding: utf-8 -*-
"""
RDM (Remote Device Management) 模拟引擎
提供 RDM 设备发现、参数读写等功能的模拟实现
"""
import random
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RDMDevice:
    """RDM 设备数据"""
    uid: str                 # 唯一标识  如 "00A1:12345678"
    label: str               # 设备标签
    model_id: int            # 型号 ID
    model_name: str          # 型号名称
    software_version: str    # 固件版本
    dmx_address: int         # DMX 起始地址 (1-512)
    personality: int         # DMX 个性索引
    footprint: int           # DMX 通道占用
    manufacturer: str        # 制造商名称
    mode: str                # 当前工作模式
    sensor_count: int        # 传感器数量
    identify: bool = False   # 识别模式
    is_online: bool = True


# 模拟设备数据库
SIMULATED_DEVICES = [
    RDMDevice(
        uid="7FF1:00000001", label="舞台左前-洗墙灯1", model_id=1,
        model_name="LED Wash 600", software_version="2.3.1",
        dmx_address=1, personality=1, footprint=16,
        manufacturer="Robe Lighting", mode="标准模式", sensor_count=2
    ),
    RDMDevice(
        uid="7FF1:00000002", label="舞台右前-洗墙灯2", model_id=1,
        model_name="LED Wash 600", software_version="2.3.1",
        dmx_address=17, personality=1, footprint=16,
        manufacturer="Robe Lighting", mode="标准模式", sensor_count=2
    ),
    RDMDevice(
        uid="4E45:00100001", label="面光-追光灯1", model_id=2,
        model_name="Spot 1200E", software_version="3.1.0",
        dmx_address=100, personality=2, footprint=24,
        manufacturer="Clay Paky", mode="扩展模式", sensor_count=3
    ),
    RDMDevice(
        uid="4E45:00100002", label="逆光-追光灯2", model_id=2,
        model_name="Spot 1200E", software_version="3.1.0",
        dmx_address=124, personality=2, footprint=24,
        manufacturer="Clay Paky", mode="扩展模式", sensor_count=3
    ),
    RDMDevice(
        uid="04B4:00A00001", label="舞台顶部-光束灯1", model_id=3,
        model_name="Beam 5R", software_version="1.8.5",
        dmx_address=200, personality=3, footprint=20,
        manufacturer="Martin Professional", mode="光束模式", sensor_count=1
    ),
    RDMDevice(
        uid="04B4:00A00002", label="舞台顶部-光束灯2", model_id=3,
        model_name="Beam 5R", software_version="1.8.5",
        dmx_address=220, personality=3, footprint=20,
        manufacturer="Martin Professional", mode="光束模式", sensor_count=1
    ),
    RDMDevice(
        uid="04B4:00A00003", label="舞台顶部-光束灯3", model_id=3,
        model_name="Beam 5R", software_version="1.9.0",
        dmx_address=240, personality=3, footprint=20,
        manufacturer="Martin Professional", mode="光束模式", sensor_count=1
    ),
    RDMDevice(
        uid="5448:000B0001", label="观众区-频闪灯1", model_id=4,
        model_name="Atomic 3000", software_version="1.2.0",
        dmx_address=300, personality=1, footprint=4,
        manufacturer="Martin Professional", mode="频闪模式", sensor_count=0
    ),
]


class RDMMessage:
    """RDM 消息封装 (模拟)"""
    # RDM PID 常量
    PID_DEVICE_LABEL = 0x0082
    PID_DMX_START_ADDRESS = 0x00F0
    PID_IDENTIFY_DEVICE = 0x1000
    PID_SENSOR_VALUE = 0x0300
    PID_MANUFACTURER_LABEL = 0x0081
    PID_DEVICE_MODEL_DESCRIPTION = 0x0080
    PID_SOFTWARE_VERSION_LABEL = 0x00C0
    PID_DMX_PERSONALITY = 0x00E0
    PID_DMX_PERSONALITY_DESCRIPTION = 0x00E1

    @staticmethod
    def encode_get(uid: str, pid: int) -> bytes:
        """编码 GET 请求 (模拟)"""
        header = bytes([0xCC, 0x01])  # RDM 标识
        uid_bytes = uid.encode('utf-8')
        msg = header + uid_bytes + pid.to_bytes(2, 'big')
        return msg

    @staticmethod
    def encode_set(uid: str, pid: int, data: bytes) -> bytes:
        """编码 SET 请求 (模拟)"""
        header = bytes([0xCC, 0x02])
        uid_bytes = uid.encode('utf-8')
        msg = header + uid_bytes + pid.to_bytes(2, 'big') + data
        return msg

    @staticmethod
    def decode(data: bytes) -> dict:
        """解码 RDM 消息 (模拟)"""
        if len(data) < 4:
            return {'status': 'error', 'message': '数据过短'}
        msg_type = 'SET' if data[1] == 0x02 else 'GET'
        return {
            'status': 'ok',
            'type': msg_type,
            'raw_length': len(data)
        }


class RDMEngine:
    """RDM 引擎 - 模拟 RDM 设备通信"""

    def __init__(self):
        self._devices: dict[str, RDMDevice] = {}
        self._discovered = False
        self._discovering = False
        self._progress = 0

    def start_discovery(self) -> bool:
        """启动设备发现 (模拟)"""
        if self._discovering:
            return False
        self._discovering = True
        self._progress = 0
        self._devices.clear()
        self._discovered = False
        return True

    def advance_discovery(self) -> tuple[int, bool]:
        """
        推进发现进度 (每调用一次前进一格)
        返回 (进度百分比, 是否完成)
        """
        if not self._discovering:
            return (100, True)

        self._progress += random.randint(8, 18)
        if self._progress >= 100:
            self._progress = 100
            self._discovering = False
            self._discovered = True
            # 一次性加载所有模拟设备 (部分设备可能不在线)
            for dev in SIMULATED_DEVICES:
                dev.is_online = random.random() > 0.1  # 90% 在线概率
                self._devices[dev.uid] = dev
            return (100, True)
        return (self._progress, False)

    def get_devices(self) -> list[RDMDevice]:
        """获取已发现的在线设备列表"""
        return [d for d in self._devices.values() if d.is_online]

    def get_device(self, uid: str) -> Optional[RDMDevice]:
        """根据 UID 获取设备"""
        return self._devices.get(uid)

    def get_device_count(self) -> int:
        return len([d for d in self._devices.values() if d.is_online])

    def read_parameter(self, uid: str, pid_name: str) -> tuple[bool, str]:
        """
        读取设备参数
        返回 (成功, 值字符串)
        """
        dev = self._devices.get(uid)
        if not dev or not dev.is_online:
            return False, "设备不在线"

        # 模拟 GET 请求
        pid_map = {
            'manufacturer': (RDMMessage.PID_MANUFACTURER_LABEL, dev.manufacturer),
            'model': (RDMMessage.PID_DEVICE_MODEL_DESCRIPTION, dev.model_name),
            'mode': (RDMMessage.PID_DMX_PERSONALITY_DESCRIPTION, dev.mode),
            'dmx_start': (RDMMessage.PID_DMX_START_ADDRESS, str(dev.dmx_address)),
            'sensor_count': (RDMMessage.PID_SENSOR_VALUE, str(dev.sensor_count)),
            'label': (RDMMessage.PID_DEVICE_LABEL, dev.label),
            'software_version': (RDMMessage.PID_SOFTWARE_VERSION_LABEL, dev.software_version),
            'identify': (RDMMessage.PID_IDENTIFY_DEVICE, "开启" if dev.identify else "关闭"),
        }

        if pid_name not in pid_map:
            return False, f"未知参数: {pid_name}"

        pid, value = pid_map[pid_name]
        # 模拟消息编码
        msg = RDMMessage.encode_get(uid, pid)
        decoded = RDMMessage.decode(msg)

        return True, value

    def set_parameter(self, uid: str, pid_name: str, value) -> tuple[bool, str]:
        """
        设置设备参数
        返回 (成功, 消息)
        """
        dev = self._devices.get(uid)
        if not dev or not dev.is_online:
            return False, "设备不在线"

        if pid_name == 'dmx_address':
            addr = int(value)
            if addr < 1 or addr > 512:
                return False, "DMX 地址必须在 1-512 范围内"
            old = dev.dmx_address
            dev.dmx_address = addr
            # 模拟 SET 消息
            data = addr.to_bytes(2, 'big')
            msg = RDMMessage.encode_set(uid, RDMMessage.PID_DMX_START_ADDRESS, data)
            return True, f"DMX 地址已从 {old} 更改为 {addr}"

        elif pid_name == 'label':
            label = str(value)
            if len(label) > 32:
                return False, "标签长度不能超过 32 字符"
            old = dev.label
            dev.label = label
            data = label.encode('utf-8')
            msg = RDMMessage.encode_set(uid, RDMMessage.PID_DEVICE_LABEL, data)
            return True, f"标签已从 '{old}' 更改为 '{label}'"

        elif pid_name == 'identify':
            ident = bool(value)
            dev.identify = ident
            data = bytes([1 if ident else 0])
            msg = RDMMessage.encode_set(uid, RDMMessage.PID_IDENTIFY_DEVICE, data)
            state = "开启" if ident else "关闭"
            return True, f"识别模式已{state}"

        else:
            return False, f"参数 '{pid_name}' 不可写"

    def get_discovery_status(self) -> dict:
        return {
            'discovering': self._discovering,
            'progress': self._progress,
            'discovered': self._discovered,
            'device_count': self.get_device_count()
        }
