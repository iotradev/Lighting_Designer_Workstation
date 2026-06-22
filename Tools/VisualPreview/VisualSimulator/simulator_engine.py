# -*- coding: utf-8 -*-
"""
视觉模拟引擎 - 舞台模型、灯具模型、坐标变换、光束计算
"""
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPolygonF


# ── 数据模型 ──────────────────────────────────────────────────────────────

@dataclass
class Fixture:
    """灯具模型"""
    id: str = ""
    name: str = "灯具"
    x: float = 0.0          # 舞台坐标 X (米)
    y: float = 0.0          # 舞台坐标 Y (米)
    z: float = 5.0          # 高度 (米)
    pan: float = 0.0        # 水平角度 (-180~180)
    tilt: float = -45.0     # 垂直角度 (-90~90)
    color_r: int = 255
    color_g: int = 255
    color_b: int = 255
    intensity: float = 1.0  # 0~1
    beam_angle: float = 25.0  # 光束角度
    beam_length: float = 12.0  # 光束长度(米)
    selected: bool = False

    @property
    def color(self) -> QColor:
        return QColor(self.color_r, self.color_g, self.color_b)

    def beam_endpoint(self) -> Tuple[float, float, float]:
        """根据 pan/tilt 计算光束终点"""
        pan_rad = math.radians(self.pan)
        tilt_rad = math.radians(self.tilt)
        dx = self.beam_length * math.cos(tilt_rad) * math.sin(pan_rad)
        dy = self.beam_length * math.cos(tilt_rad) * math.cos(pan_rad)
        dz = self.beam_length * math.sin(tilt_rad)
        return (self.x + dx, self.y + dy, self.z + dz)

    def beam_cone_points(self, num_points: int = 12) -> List[Tuple[float, float, float]]:
        """计算光束锥体底面圆周点"""
        pan_rad = math.radians(self.pan)
        tilt_rad = math.radians(self.tilt)
        half_angle = math.radians(self.beam_angle / 2)
        length = self.beam_length

        # 光束方向向量
        dx = math.cos(tilt_rad) * math.sin(pan_rad)
        dy = math.cos(tilt_rad) * math.cos(pan_rad)
        dz = math.sin(tilt_rad)

        # 构建垂直于光束方向的两个向量
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            ux, uy, uz = 1.0, 0.0, 0.0
        else:
            ux, uy, uz = -dy, dx, 0.0
            mag = math.sqrt(ux**2 + uy**2 + uz**2)
            ux, uy, uz = ux/mag, uy/mag, uz/mag

        vx = dy * uz - dz * uy
        vy = dz * ux - dx * uz
        vz = dx * uy - dy * ux

        radius = length * math.tan(half_angle)
        ex, ey, ez = self.beam_endpoint()

        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            px = ex + radius * (ux * math.cos(angle) + vx * math.sin(angle))
            py = ey + radius * (uy * math.cos(angle) + vy * math.sin(angle))
            pz = ez + radius * (uz * math.cos(angle) + vz * math.sin(angle))
            points.append((px, py, pz))
        return points

    def to_dict(self) -> dict:
        return {
            'id': self.id, 'name': self.name,
            'x': self.x, 'y': self.y, 'z': self.z,
            'pan': self.pan, 'tilt': self.tilt,
            'color_r': self.color_r, 'color_g': self.color_g, 'color_b': self.color_b,
            'intensity': self.intensity, 'beam_angle': self.beam_angle,
            'beam_length': self.beam_length,
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Fixture':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Truss:
    """桁架结构"""
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 10.0
    y2: float = 0.0
    z: float = 6.0
    width: float = 0.4

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict) -> 'Truss':
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class StageModel:
    """舞台模型"""
    width: float = 20.0
    depth: float = 15.0
    floor_color: Tuple[int, int, int] = (40, 40, 50)
    fixtures: List[Fixture] = field(default_factory=list)
    trusses: List[Truss] = field(default_factory=list)

    def add_fixture(self, fixture: Fixture):
        self.fixtures.append(fixture)

    def remove_fixture(self, index: int):
        if 0 <= index < len(self.fixtures):
            self.fixtures.pop(index)

    def get_selected(self) -> Optional[Fixture]:
        for f in self.fixtures:
            if f.selected:
                return f
        return None

    def select_fixture(self, index: int):
        for i, f in enumerate(self.fixtures):
            f.selected = (i == index)

    def to_dict(self) -> dict:
        return {
            'width': self.width, 'depth': self.depth,
            'floor_color': self.floor_color,
            'fixtures': [f.to_dict() for f in self.fixtures],
            'trusses': [t.to_dict() for t in self.trusses],
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'StageModel':
        stage = cls(
            width=d.get('width', 20), depth=d.get('depth', 15),
            floor_color=tuple(d.get('floor_color', (40, 40, 50)))
        )
        for fd in d.get('fixtures', []):
            stage.fixtures.append(Fixture.from_dict(fd))
        for td in d.get('trusses', []):
            stage.trusses.append(Truss.from_dict(td))
        return stage


# ── 坐标变换 ──────────────────────────────────────────────────────────────

class CoordinateTransform:
    """坐标变换引擎 - 支持俯视/侧视/等轴测视图"""

    def __init__(self):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 30.0  # 像素/米

    def set_view_offset(self, ox: float, oy: float):
        self.offset_x = ox
        self.offset_y = oy

    def world_to_screen_top(self, x: float, y: float, z: float = 0) -> QPointF:
        """俯视图: X->右, Y->下"""
        sx = (x * self.zoom) + self.offset_x
        sy = (y * self.zoom) + self.offset_y
        return QPointF(sx, sy)

    def world_to_screen_side(self, x: float, y: float, z: float = 0) -> QPointF:
        """侧视图: X->右, Z->上"""
        sx = (x * self.zoom) + self.offset_x
        sy = self.offset_y - (z * self.zoom)
        return QPointF(sx, sy)

    def world_to_screen_iso(self, x: float, y: float, z: float = 0) -> QPointF:
        """等轴测视图"""
        angle = math.radians(30)
        sx = (x - y) * math.cos(angle) * self.zoom + self.offset_x
        sy = (x + y) * math.sin(angle) * self.zoom - z * self.zoom + self.offset_y
        return QPointF(sx, sy)


# ── 默认场景 ──────────────────────────────────────────────────────────────

def create_default_stage() -> StageModel:
    """创建默认演示舞台"""
    stage = StageModel(width=20, depth=15)

    # 添加默认桁架
    stage.trusses.append(Truss(x1=2, y1=2, x2=18, y2=2, z=6))
    stage.trusses.append(Truss(x1=2, y1=7, x2=18, y2=7, z=6))
    stage.trusses.append(Truss(x1=2, y1=12, x2=18, y2=12, z=6))

    # 添加默认灯具
    colors = [
        (255, 100, 100), (100, 255, 100), (100, 100, 255),
        (255, 255, 100), (255, 100, 255), (100, 255, 255),
    ]
    for row_i, row_y in enumerate([2, 7, 12]):
        for col_i in range(3):
            cx = 5 + col_i * 5
            c = colors[(row_i * 3 + col_i) % len(colors)]
            stage.fixtures.append(Fixture(
                id=f"fix_{row_i}_{col_i}",
                name=f"灯具-{row_i+1}-{col_i+1}",
                x=cx, y=row_y, z=6,
                pan=0, tilt=-45,
                color_r=c[0], color_g=c[1], color_b=c[2],
                intensity=0.8, beam_angle=25,
            ))

    if stage.fixtures:
        stage.fixtures[0].selected = True
    return stage
