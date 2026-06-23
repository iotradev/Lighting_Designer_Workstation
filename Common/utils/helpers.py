# -*- coding: utf-8 -*-
"""

"""
import json, csv, math
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent


def ensure_dir(path):
    """"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)


def load_json(path):
    """JSON"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data, indent=2):
    """JSON"""
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def export_csv(path, headers, rows):
    """CSV"""
    ensure_dir(Path(path).parent)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def dmx_to_hex(value):
    """DMX(0-255)"""
    return f"0x{max(0, min(255, int(value))):02X}"


def dmx_to_percent(value):
    """DMX(0-255)"""
    return round(max(0, min(255, int(value))) / 255 * 100, 1)


def percent_to_dmx(percent):
    """DMX(0-255)"""
    return max(0, min(255, int(percent / 100 * 255)))


def universe_address(universe, channel):
    """ (Universe0, Channel1)"""
    return universe * 512 + channel


def address_to_universe(address):
    """ Universe/Channel"""
    return (address - 1) // 512, (address - 1) % 512 + 1


def rgb_to_hex(r, g, b):
    """RGB"""
    return f"#{max(0,min(255,r)):02X}{max(0,min(255,g)):02X}{max(0,min(255,b)):02X}"


def hex_to_rgb(hex_color):
    """RGB"""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    if len(h) != 6:
        raise ValueError(f"无效颜色值: {hex_color}")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def kelvin_to_rgb(kelvin):
    """(K)RGB"""
    if kelvin <= 0:
        return (0, 0, 0)
    kelvin = max(1000, min(40000, kelvin))
    temp = kelvin / 100
    if temp <= 66:
        r = 255
        g = max(0, min(255, 99.4708025861 * math.log(temp) - 161.1195681661))
    else:
        t_minus_60 = temp - 60
        if t_minus_60 <= 0:
            t_minus_60 = 0.01
        r = max(0, min(255, 329.698727446 * (t_minus_60 ** -0.1332047592)))
        g = max(0, min(255, 288.1221695283 * (t_minus_60 ** -0.0755148492)))
    if temp >= 66:
        b = 255
    elif temp <= 19:
        b = 0
    else:
        b = max(0, min(255, 138.5177312231 * math.log(temp - 10) - 305.0447927307))
    return int(r), int(g), int(b)


def format_timecode(hours, minutes, seconds, frames, fps=30):
    """"""
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}:{int(frames):02d}"


def timestamp():
    """"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_filename(name):
    """"""
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, "_")
    name = name.strip()
    reserved = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2',
                'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
    if name.upper() in reserved:
        name = f"_{name}"
    return name
