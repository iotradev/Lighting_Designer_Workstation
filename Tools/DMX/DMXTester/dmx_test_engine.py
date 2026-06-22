# -*- coding: utf-8 -*-
"""
DMX测试引擎 - 512通道DMX输出模拟
支持单通道/范围设置、Chase/Ramp自动测试、故障检测
"""

import time
import threading
from typing import List, Callable, Optional


class DMXTestEngine:
    """DMX测试引擎 - 模拟512通道DMX输出"""

    def __init__(self):
        self.channels = [0] * 512  # DMX 512通道
        self._chase_running = False
        self._ramp_running = False
        self._chase_thread: Optional[threading.Thread] = None
        self._ramp_thread: Optional[threading.Thread] = None
        self._update_callback: Optional[Callable] = None

    def set_update_callback(self, callback: Callable):
        """设置更新回调（UI刷新用）"""
        self._update_callback = callback

    def _notify_update(self):
        """通知UI更新"""
        if self._update_callback:
            self._update_callback()

    # ===== 基础通道操作 =====

    def set_channel(self, channel: int, value: int):
        """设置单个通道值 (channel: 1-512, value: 0-255)"""
        if 1 <= channel <= 512:
            self.channels[channel - 1] = max(0, min(255, value))
            self._notify_update()

    def get_channel(self, channel: int) -> int:
        """获取通道值"""
        if 1 <= channel <= 512:
            return self.channels[channel - 1]
        return 0

    def set_range(self, start: int, end: int, value: int):
        """设置通道范围"""
        start = max(1, min(512, start))
        end = max(1, min(512, end))
        if start > end:
            start, end = end, start
        for ch in range(start - 1, end):
            self.channels[ch] = max(0, min(255, value))
        self._notify_update()

    def set_all(self, value: int):
        """设置所有通道"""
        value = max(0, min(255, value))
        self.channels = [value] * 512
        self._notify_update()

    def blackout(self):
        """所有通道归零"""
        self.set_all(0)

    def full_on(self):
        """所有通道满值"""
        self.set_all(255)

    # ===== Chase测试 =====

    def start_chase(self, speed_ms: int = 100, callback: Callable = None):
        """启动Chase测试 - 逐通道点亮"""
        if self._chase_running:
            return
        self._chase_running = True

        def _chase_loop():
            ch = 0
            while self._chase_running:
                self.blackout()
                self.channels[ch] = 255
                self._notify_update()
                if callback:
                    callback(ch + 1)
                ch = (ch + 1) % 512
                time.sleep(speed_ms / 1000.0)
            self.blackout()

        self._chase_thread = threading.Thread(target=_chase_loop, daemon=True)
        self._chase_thread.start()

    def stop_chase(self):
        """停止Chase测试"""
        self._chase_running = False
        if self._chase_thread:
            self._chase_thread.join(timeout=1.0)
            self._chase_thread = None

    @property
    def is_chase_running(self) -> bool:
        return self._chase_running

    # ===== Ramp测试 =====

    def start_ramp(self, channel: int, speed_ms: int = 20, callback: Callable = None):
        """启动Ramp测试 - 单通道渐变 0->255->0"""
        if self._ramp_running:
            return
        self._ramp_running = True

        def _ramp_loop():
            while self._ramp_running:
                # 上升 0->255
                for v in range(0, 256, 2):
                    if not self._ramp_running:
                        break
                    self.channels[channel - 1] = v
                    self._notify_update()
                    if callback:
                        callback(v)
                    time.sleep(speed_ms / 1000.0)
                # 下降 255->0
                for v in range(254, -1, -2):
                    if not self._ramp_running:
                        break
                    self.channels[channel - 1] = v
                    self._notify_update()
                    if callback:
                        callback(v)
                    time.sleep(speed_ms / 1000.0)
            self.channels[channel - 1] = 0
            self._notify_update()

        self._ramp_thread = threading.Thread(target=_ramp_loop, daemon=True)
        self._ramp_thread.start()

    def stop_ramp(self):
        """停止Ramp测试"""
        self._ramp_running = False
        if self._ramp_thread:
            self._ramp_thread.join(timeout=1.0)
            self._ramp_thread = None

    @property
    def is_ramp_running(self) -> bool:
        return self._ramp_running

    # ===== 故障检测 =====

    def run_fault_detection(self, callback: Callable = None) -> List[dict]:
        """
        故障检测流程:
        1. 全部设为255，记录状态
        2. 全部设为0，记录状态
        3. 检测卡死通道（设0后仍>0的通道）

        返回: 故障通道列表 [{'channel': int, 'stuck_value': int}, ...]
        """
        results = []

        # 步骤1: 全部255
        if callback:
            callback("正在设置所有通道为255...")
        self.set_all(255)
        time.sleep(0.5)

        # 步骤2: 全部0
        if callback:
            callback("正在设置所有通道为0...")
        self.set_all(0)
        time.sleep(0.5)

        # 步骤3: 检测 - 模拟检测（实际环境中需读取硬件反馈）
        # 这里模拟：随机标记几个"故障"通道用于演示
        # 实际实现应比较预期值与实际读回值
        if callback:
            callback("正在检测卡死通道...")

        # 模拟故障检测：检查内部状态是否正确归零
        for i in range(512):
            if self.channels[i] != 0:
                results.append({
                    'channel': i + 1,
                    'stuck_value': self.channels[i],
                    'status': '卡死'
                })

        if callback:
            callback(f"检测完成，发现 {len(results)} 个故障通道")

        return results

    def stop_all_tests(self):
        """停止所有自动测试"""
        self.stop_chase()
        self.stop_ramp()
        self.blackout()
