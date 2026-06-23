# -*- coding: utf-8 -*-
"""逐个启动工具并截图"""
import sys
import os
import importlib.util
import ast
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "Common"))
sys.path.insert(0, str(BASE_DIR))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap

app = QApplication.instance() or QApplication(sys.argv)

TOOLS_DIR = BASE_DIR / "Tools"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

def take_screenshot(window, name):
    """截取窗口截图"""
    pixmap = window.grab()
    path = SCREENSHOTS_DIR / f"{name}.png"
    pixmap.save(str(path))
    print(f"  Saved: {path}")

def test_tool(tool_dir, cat_name):
    """测试单个工具并截图"""
    main_py = tool_dir / "main.py"
    if not main_py.exists():
        return None
    
    tool_name = f"{cat_name}_{tool_dir.name}"
    
    # 清除旧模块
    for k in list(sys.modules.keys()):
        if k.startswith("tool_") or k in ("engine", "main", "midi_engine", "bpm_engine",
            "beat_engine", "spectrum_engine", "cue_engine", "artnet_engine", "sacn_engine",
            "rdm_engine", "dmx_test_engine", "mapper_engine", "midi_sender_engine",
            "simulator_engine", "pixel_engine", "fixture_data", "stage_elements"):
            del sys.modules[k]
    
    old_path = sys.path.copy()
    try:
        sys.path.insert(0, str(tool_dir))
        
        with open(main_py, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        
        window_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = base.id if isinstance(base, ast.Name) else (base.attr if isinstance(base, ast.Attribute) else "")
                    if base_name == "BaseToolWindow":
                        window_classes.append(node.name)
        
        if not window_classes:
            return None
        
        spec = importlib.util.spec_from_file_location(f"tool_{tool_dir.name}", str(main_py))
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"tool_{tool_dir.name}"] = module
        spec.loader.exec_module(module)
        
        cls = getattr(module, window_classes[0])
        window = cls()
        window.show()
        app.processEvents()
        
        # 等待窗口渲染
        QTimer.singleShot(500, lambda: take_screenshot(window, tool_name))
        QTimer.singleShot(800, window.close)
        
        return tool_name
    except Exception as e:
        print(f"  FAIL {tool_name}: {type(e).__name__}: {e}")
        return None
    finally:
        sys.path = old_path

# 按类别测试
categories = sorted(TOOLS_DIR.iterdir())
current_cat = 0
current_tool = 0
tools_to_test = []

for cat_dir in categories:
    if not cat_dir.is_dir():
        continue
    for tool_dir in sorted(cat_dir.iterdir()):
        if not tool_dir.is_dir():
            continue
        if (tool_dir / "main.py").exists():
            tools_to_test.append((tool_dir, cat_dir.name))

print(f"Testing {len(tools_to_test)} tools...")
print(f"Screenshots will be saved to: {SCREENSHOTS_DIR}")
print()

# 逐个测试
for i, (tool_dir, cat_name) in enumerate(tools_to_test):
    tool_name = f"{cat_name}_{tool_dir.name}"
    print(f"[{i+1}/{len(tools_to_test)}] {tool_name}")
    test_tool(tool_dir, cat_name)
    app.processEvents()

print()
print("Done! Check screenshots/ folder.")
