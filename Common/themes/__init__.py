# -*- coding: utf-8 -*-
"""主题系统 - GrandMA3风格深色/浅色主题"""
import json, os
from pathlib import Path

THEMES_DIR = Path(__file__).parent.parent.parent / "Config" / "Themes"

def load_theme(name="dark"):
    """加载主题配置"""
    theme_file = THEMES_DIR / f"{name}.json"
    if theme_file.exists():
        with open(theme_file, "r", encoding="utf-8") as f:
            return json.load(f)
    # 默认返回深色主题
    return _default_dark()

def _default_dark():
    return {
        "name": "GrandMA3 Dark",
        "colors": {
            "background": "#1e1e1e",
            "surface": "#252526",
            "surface_alt": "#2d2d30",
            "panel": "#333337",
            "border": "#3f3f46",
            "text": "#cccccc",
            "text_bright": "#ffffff",
            "text_dim": "#808080",
            "accent": "#e8912d",
            "accent_hover": "#f0a040",
            "accent_pressed": "#c07820",
            "success": "#4ec9b0",
            "warning": "#e8912d",
            "error": "#f44747",
            "info": "#569cd6",
            "highlight": "#264f78",
            "selection": "#094771",
            "input_bg": "#1e1e1e",
            "input_border": "#3f3f46",
            "button_bg": "#333337",
            "button_hover": "#3e3e42",
            "menu_bg": "#2d2d30",
            "toolbar_bg": "#333337",
            "statusbar_bg": "#007acc",
            "tab_active": "#1e1e1e",
            "tab_inactive": "#2d2d30",
            "scrollbar": "#424242",
            "scrollbar_hover": "#4f4f4f",
            "tree_bg": "#252526",
            "table_bg": "#252526",
            "table_alt": "#2a2a2d",
            "table_header": "#333337",
            "chart_line": "#e8912d",
            "chart_fill": "rgba(232,145,45,0.3)",
            "meter_green": "#4ec9b0",
            "meter_yellow": "#e8912d",
            "meter_red": "#f44747"
        },
        "fonts": {
            "family": "Microsoft YaHei UI, Segoe UI, sans-serif",
            "family_mono": "Cascadia Code, Consolas, monospace",
            "size_small": 12,
            "size_normal": 14,
            "size_large": 17,
            "size_title": 22,
            "size_header": 26
        },
        "spacing": {
            "xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "xxl": 32
        },
        "radius": {
            "sm": 4, "md": 6, "lg": 10
        }
    }
