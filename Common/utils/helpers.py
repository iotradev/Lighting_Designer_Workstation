# -*- coding: utf-8 -*-
"""
通用工具函数
"""
import os, json, csv, math
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent


def ensure_dir(path):
    """确保目录存在"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)


def load_json(path):
    """加载JSON文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data, indent=2):
    """保存JSON文件"""
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def export_csv(path, headers, rows):
    """导出CSV文件"""
    ensure_dir(Path(path).parent)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def dmx_to_hex(value):
    """DMX值(0-255)转十六进制"""
    return f"0x{max(0, min(255, int(value))):02X}"


def dmx_to_percent(value):
    """DMX值(0-255)转百分比"""
    return round(max(0, min(255, int(value))) / 255 * 100, 1)


def percent_to_dmx(percent):
    """百分比转DMX值(0-255)"""
    return max(0, min(255, int(percent / 100 * 255)))


def universe_address(universe, channel):
    """计算全局地址 (Universe从0开始, Channel从1开始)"""
    return universe * 512 + channel


def address_to_universe(address):
    """全局地址转 Universe/Channel"""
    return (address - 1) // 512, (address - 1) % 512 + 1


def rgb_to_hex(r, g, b):
    """RGB转十六进制颜色"""
    return f"#{max(0,min(255,r)):02X}{max(0,min(255,g)):02X}{max(0,min(255,b)):02X}"


def hex_to_rgb(hex_color):
    """十六进制颜色转RGB"""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def kelvin_to_rgb(kelvin):
    """色温(K)转RGB近似值"""
    temp = kelvin / 100
    if temp <= 66:
        r = 255
        g = max(0, min(255, 99.4708025861 * math.log(temp) - 161.1195681661))
    else:
        r = max(0, min(255, 329.698727446 * ((temp - 60) ** -0.1332047592)))
        g = max(0, min(255, 288.1221695283 * ((temp - 60) ** -0.0755148492)))
    if temp >= 66:
        b = 255
    elif temp <= 19:
        b = 0
    else:
        b = max(0, min(255, 138.5177312231 * math.log(temp - 10) - 305.0447927307))
    return int(r), int(g), int(b)


def format_timecode(hours, minutes, seconds, frames, fps=30):
    """格式化时间码"""
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{int(frames):02d}"


def timestamp():
    """当前时间戳字符串"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_filename(name):
    """生成安全文件名"""
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, "_")
    return name.strip()
