# -*- coding: utf-8 -*-
"""
像素映射引擎 - LED矩阵数据模型、DMX映射、图案生成器、动画帧缓冲
"""

import math
import colorsys
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class PixelData:
    """单个LED像素数据"""
    r: int = 0
    g: int = 0
    b: int = 0
    dmx_address: int = 0  # 起始DMX地址
    channels_per_pixel: int = 3  # RGB=3, RGBW=4
    fixture_id: str = ""  # 灯具ID

    def to_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def set_color(self, r: int, g: int, b: int):
        self.r = max(0, min(255, r))
        self.g = max(0, min(255, g))
        self.b = max(0, min(255, b))

    def clear(self):
        self.r = 0
        self.g = 0
        self.b = 0


@dataclass
class DMXMapping:
    """DMX映射配置"""
    start_address: int = 1
    channels_per_pixel: int = 3  # 3=RGB, 4=RGBW
    auto_assign: bool = True

    @property
    def max_pixels(self) -> int:
        """最大可映射像素数(基于512通道限制)"""
        return 512 // self.channels_per_pixel

    def get_dmx_address(self, index: int) -> int:
        """根据索引获取DMX地址"""
        addr = self.start_address + index * self.channels_per_pixel
        if addr + self.channels_per_pixel - 1 > 512:
            return -1  # 超出范围
        return addr


class PatternGenerator:
    """图案生成器"""

    @staticmethod
    def rainbow(rows: int, cols: int, offset: float = 0.0) -> List[List[Tuple[int, int, int]]]:
        """彩虹渐变图案"""
        result = []
        for r in range(rows):
            row = []
            for c in range(cols):
                hue = ((c / max(cols - 1, 1)) + offset) % 1.0
                sat = 1.0 - (r / max(rows - 1, 1)) * 0.3
                val = 1.0
                rgb = colorsys.hsv_to_rgb(hue, sat, val)
                row.append((int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)))
            result.append(row)
        return result

    @staticmethod
    def color_wave(rows: int, cols: int, phase: float = 0.0) -> List[List[Tuple[int, int, int]]]:
        """颜色波浪图案"""
        result = []
        for r in range(rows):
            row = []
            for c in range(cols):
                wave = math.sin((c + r) * 0.3 + phase) * 0.5 + 0.5
                hue = (wave * 0.6 + phase * 0.1) % 1.0
                rgb = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
                row.append((int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)))
            result.append(row)
        return result

    @staticmethod
    def checkerboard(rows: int, cols: int,
                     color1: Tuple[int, int, int] = (255, 255, 255),
                     color2: Tuple[int, int, int] = (0, 0, 0),
                     shift: int = 0) -> List[List[Tuple[int, int, int]]]:
        """棋盘格图案"""
        result = []
        for r in range(rows):
            row = []
            for c in range(cols):
                if (r + c + shift) % 2 == 0:
                    row.append(color1)
                else:
                    row.append(color2)
            result.append(row)
        return result

    @staticmethod
    def spiral(rows: int, cols: int, angle_offset: float = 0.0) -> List[List[Tuple[int, int, int]]]:
        """螺旋图案"""
        result = []
        cx = cols / 2.0
        cy = rows / 2.0
        for r in range(rows):
            row = []
            for c in range(cols):
                dx = c - cx
                dy = r - cy
                dist = math.sqrt(dx * dx + dy * dy)
                angle = math.atan2(dy, dx) + angle_offset
                hue = ((angle / (2 * math.pi)) + dist * 0.1) % 1.0
                rgb = colorsys.hsv_to_rgb(hue, 0.9, 1.0)
                row.append((int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)))
            result.append(row)
        return result


class PixelGridModel:
    """LED像素网格数据模型"""

    def __init__(self, rows: int = 16, cols: int = 16):
        self._rows = rows
        self._cols = cols
        self._pixels: List[List[PixelData]] = []
        self._dmx_mapping = DMXMapping()
        self._frames: List[List[List[Tuple[int, int, int]]]] = []  # 动画帧缓冲
        self._init_grid()

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def total_pixels(self) -> int:
        return self._rows * self._cols

    @property
    def dmx_mapping(self) -> DMXMapping:
        return self._dmx_mapping

    @property
    def total_channels(self) -> int:
        return self.total_pixels * self._dmx_mapping.channels_per_pixel

    def _init_grid(self):
        """初始化网格"""
        self._pixels = []
        for r in range(self._rows):
            row = []
            for c in range(self._cols):
                row.append(PixelData())
            self._pixels.append(row)
        if self._dmx_mapping.auto_assign:
            self.auto_assign_dmx()

    def resize(self, rows: int, cols: int):
        """调整网格大小"""
        rows = max(4, min(64, rows))
        cols = max(4, min(64, cols))
        self._rows = rows
        self._cols = cols
        self._init_grid()

    def get_pixel(self, row: int, col: int) -> Optional[PixelData]:
        """获取像素数据"""
        if 0 <= row < self._rows and 0 <= col < self._cols:
            return self._pixels[row][col]
        return None

    def set_pixel_color(self, row: int, col: int, r: int, g: int, b: int):
        """设置像素颜色"""
        pixel = self.get_pixel(row, col)
        if pixel:
            pixel.set_color(r, g, b)

    def erase_pixel(self, row: int, col: int):
        """擦除像素"""
        pixel = self.get_pixel(row, col)
        if pixel:
            pixel.clear()

    def fill_all(self, r: int, g: int, b: int):
        """填充所有像素"""
        for row in self._pixels:
            for pixel in row:
                pixel.set_color(r, g, b)

    def clear_all(self):
        """清除所有像素"""
        for row in self._pixels:
            for pixel in row:
                pixel.clear()

    def auto_assign_dmx(self):
        """自动分配DMX地址"""
        addr = self._dmx_mapping.start_address
        for r in range(self._rows):
            for c in range(self._cols):
                pixel = self._pixels[r][c]
                pixel.dmx_address = addr
                pixel.channels_per_pixel = self._dmx_mapping.channels_per_pixel
                pixel.fixture_id = f"P{r}_{c}"
                addr += self._dmx_mapping.channels_per_pixel

    def set_dmx_start(self, addr: int):
        """设置DMX起始地址"""
        self._dmx_mapping.start_address = max(1, min(512, addr))
        if self._dmx_mapping.auto_assign:
            self.auto_assign_dmx()

    def set_channels_per_pixel(self, ch: int):
        """设置每像素通道数"""
        self._dmx_mapping.channels_per_pixel = max(1, min(4, ch))
        if self._dmx_mapping.auto_assign:
            self.auto_assign_dmx()

    def get_color_grid(self) -> List[List[Tuple[int, int, int]]]:
        """获取当前颜色网格"""
        return [[p.to_tuple() for p in row] for row in self._pixels]

    def set_color_grid(self, grid: List[List[Tuple[int, int, int]]]):
        """从颜色网格设置"""
        for r in range(min(len(grid), self._rows)):
            for c in range(min(len(grid[r]), self._cols)):
                self._pixels[r][c].set_color(*grid[r][c])

    # === 图案应用 ===

    def apply_pattern(self, pattern_name: str, **kwargs):
        """应用内置图案"""
        gen = PatternGenerator
        if pattern_name == "rainbow":
            grid = gen.rainbow(self._rows, self._cols, kwargs.get("offset", 0.0))
        elif pattern_name == "wave":
            grid = gen.color_wave(self._rows, self._cols, kwargs.get("phase", 0.0))
        elif pattern_name == "checker":
            grid = gen.checkerboard(self._rows, self._cols,
                                    kwargs.get("color1", (255, 255, 255)),
                                    kwargs.get("color2", (0, 0, 0)),
                                    kwargs.get("shift", 0))
        elif pattern_name == "spiral":
            grid = gen.spiral(self._rows, self._cols, kwargs.get("angle", 0.0))
        else:
            return
        self.set_color_grid(grid)

    # === 动画帧管理 ===

    def save_frame(self):
        """保存当前状态为动画帧"""
        self._frames.append(self.get_color_grid())

    def load_frame(self, index: int):
        """加载动画帧"""
        if 0 <= index < len(self._frames):
            self.set_color_grid(self._frames[index])

    def clear_frames(self):
        """清除所有帧"""
        self._frames.clear()

    @property
    def frame_count(self) -> int:
        return len(self._frames)

    def generate_animation(self, pattern_name: str, frame_count: int = 30, **kwargs):
        """生成动画序列"""
        self._frames.clear()
        for i in range(frame_count):
            t = i / max(frame_count - 1, 1)
            if pattern_name == "rainbow":
                grid = PatternGenerator.rainbow(self._rows, self._cols, offset=t)
            elif pattern_name == "wave":
                grid = PatternGenerator.color_wave(self._rows, self._cols, phase=t * math.pi * 2)
            elif pattern_name == "checker":
                grid = PatternGenerator.checkerboard(self._rows, self._cols, shift=i % 2)
            elif pattern_name == "spiral":
                grid = PatternGenerator.spiral(self._rows, self._cols, angle_offset=t * math.pi * 2)
            else:
                grid = PatternGenerator.rainbow(self._rows, self._cols, offset=t)
            self._frames.append(grid)

    # === 导出 ===

    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        pixels_data = []
        for r in range(self._rows):
            for c in range(self._cols):
                p = self._pixels[r][c]
                pixels_data.append({
                    "row": r, "col": c,
                    "fixture_id": p.fixture_id,
                    "dmx_address": p.dmx_address,
                    "channels": p.channels_per_pixel,
                    "color": p.to_hex()
                })
        return {
            "grid_size": {"rows": self._rows, "cols": self._cols},
            "dmx_mapping": {
                "start_address": self._dmx_mapping.start_address,
                "channels_per_pixel": self._dmx_mapping.channels_per_pixel,
                "total_channels": self.total_channels
            },
            "pixels": pixels_data
        }
