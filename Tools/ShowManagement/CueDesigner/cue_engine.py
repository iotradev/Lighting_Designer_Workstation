"""
CueEngine - Cue数据模型、CueList管理器、交叉渐变插值器、效果生成器
"""
import math
import random
import time
import json
import csv
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Callable
from enum import Enum


class EffectType(Enum):
    SINE = "sine"
    RANDOM = "random"
    RANDOM_COLOR = "random_color"
    CHASE = "chase"


@dataclass
class Cue:
    """单个Cue数据模型"""
    cue_number: float = 1.0
    name: str = ""
    fade_in: float = 3.0      # 秒
    fade_out: float = 3.0     # 秒
    delay: float = 0.0        # 秒
    channel_values: List[int] = field(default_factory=lambda: [0] * 512)

    def to_dict(self) -> dict:
        return {
            'cue_number': self.cue_number,
            'name': self.name,
            'fade_in': self.fade_in,
            'fade_out': self.fade_out,
            'delay': self.delay,
            'channel_values': self.channel_values[:]
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Cue':
        c = cls(
            cue_number=d.get('cue_number', 1.0),
            name=d.get('name', ''),
            fade_in=d.get('fade_in', 3.0),
            fade_out=d.get('fade_out', 3.0),
            delay=d.get('delay', 0.0),
        )
        vals = d.get('channel_values', [0]*512)
        c.channel_values = (vals + [0]*512)[:512]
        return c


class CueList:
    """Cue列表管理器"""

    def __init__(self):
        self.cues: List[Cue] = []
        self.name: str = "新建Cue列表"

    def add_cue(self, cue: Cue):
        self.cues.append(cue)
        self.cues.sort(key=lambda c: c.cue_number)

    def remove_cue(self, index: int):
        if 0 <= index < len(self.cues):
            self.cues.pop(index)

    def move_up(self, index: int) -> int:
        if index > 0:
            self.cues[index], self.cues[index-1] = self.cues[index-1], self.cues[index]
            return index - 1
        return index

    def move_down(self, index: int) -> int:
        if index < len(self.cues) - 1:
            self.cues[index], self.cues[index+1] = self.cues[index+1], self.cues[index]
            return index + 1
        return index

    def get_cue(self, index: int) -> Optional[Cue]:
        if 0 <= index < len(self.cues):
            return self.cues[index]
        return None

    def save_to_json(self, filepath: str):
        data = {
            'name': self.name,
            'cues': [c.to_dict() for c in self.cues]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_json(self, filepath: str):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.name = data.get('name', '未命名')
        self.cues = [Cue.from_dict(d) for d in data.get('cues', [])]

    def export_csv(self, filepath: str):
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['Cue编号', '名称', '淡入时间(s)', '淡出时间(s)', '延迟时间(s)'])
            for c in self.cues:
                writer.writerow([c.cue_number, c.name, c.fade_in, c.fade_out, c.delay])


class CrossfadeInterpolator:
    """交叉渐变插值器"""

    @staticmethod
    def lerp(from_vals: List[int], to_vals: List[int], t: float) -> List[int]:
        """线性插值两个DMX场景"""
        t = max(0.0, min(1.0, t))
        result = []
        for a, b in zip(from_vals, to_vals):
            result.append(int(round(a + (b - a) * t)))
        return result

    @staticmethod
    def ease_in_out(t: float) -> float:
        """缓入缓出曲线"""
        return t * t * (3 - 2 * t)


class EffectGenerator:
    """效果生成器"""

    @staticmethod
    def sine_effect(channels: List[int], speed: float, amplitude: float,
                    phase_offset: float = 0.0, time_val: float = 0.0) -> List[int]:
        """正弦波效果"""
        values = []
        for i, ch in enumerate(channels):
            phase = time_val * speed * 2 * math.pi + i * phase_offset
            val = 128 + amplitude * 127 * math.sin(phase)
            values.append(max(0, min(255, int(val))))
        return values

    @staticmethod
    def random_effect(num_channels: int, speed: float) -> List[int]:
        """随机闪烁效果"""
        values = []
        for _ in range(num_channels):
            values.append(random.randint(0, 255) if random.random() < speed else 0)
        return values

    @staticmethod
    def random_color_effect(num_channels: int) -> List[int]:
        """随机颜色效果（RGB三通道一组）"""
        values = []
        for i in range(0, num_channels, 3):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            values.extend([r, g, b])
        return values[:num_channels]

    @staticmethod
    def chase_effect(num_channels: int, speed: float, time_val: float) -> List[int]:
        """追逐效果"""
        values = []
        pos = int(time_val * speed) % max(num_channels, 1)
        for i in range(num_channels):
            if i == pos:
                values.append(255)
            else:
                values.append(0)
        return values
