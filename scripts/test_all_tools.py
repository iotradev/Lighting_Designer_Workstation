# -*- coding: utf-8 -*-
"""逐个测试所有42个工具的启动能力"""
import sys
import os
import importlib
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR / "Common"))
sys.path.insert(0, str(BASE_DIR))

from PySide6.QtWidgets import QApplication

# 确保 QApplication 存在
app = QApplication.instance() or QApplication(sys.argv)

TOOLS_DIR = BASE_DIR / "Tools"
results = {"ok": [], "fail": [], "skip": []}

for cat_dir in sorted(TOOLS_DIR.iterdir()):
    if not cat_dir.is_dir():
        continue
    for tool_dir in sorted(cat_dir.iterdir()):
        if not tool_dir.is_dir():
            continue
        main_py = tool_dir / "main.py"
        if not main_py.exists():
            results["skip"].append(f"{cat_dir.name}/{tool_dir.name}: main.py missing")
            continue
        
        tool_name = f"{cat_dir.name}/{tool_dir.name}"
        
        # 清除旧模块缓存
        mods_to_remove = [k for k in sys.modules if k.startswith("tool_")]
        for m in mods_to_remove:
            del sys.modules[m]
        # 清除可能冲突的模块名
        for conflict in ("engine", "main", "midi_engine", "bpm_engine", "beat_engine",
                         "spectrum_engine", "cue_engine", "artnet_engine", "sacn_engine",
                         "rdm_engine", "dmx_test_engine", "mapper_engine", "midi_sender_engine",
                         "simulator_engine", "pixel_engine", "fixture_data", "stage_elements"):
            if conflict in sys.modules:
                del sys.modules[conflict]
        
        old_path = sys.path.copy()
        try:
            sys.path.insert(0, str(tool_dir))
            
            # 读取并编译代码
            with open(main_py, encoding="utf-8") as f:
                code = f.read()
            
            # 查找主窗口类
            import ast
            tree = ast.parse(code)
            window_classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr
                        if base_name == "BaseToolWindow":
                            window_classes.append(node.name)
            
            if not window_classes:
                results["fail"].append(f"{tool_name}: no BaseToolWindow subclass found")
                continue
            
            # 尝试导入模块
            spec = importlib.util.spec_from_file_location(
                f"tool_{tool_dir.name}", str(main_py)
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"tool_{tool_dir.name}"] = module
            spec.loader.exec_module(module)
            
            # 尝试实例化主窗口类
            cls = getattr(module, window_classes[0])
            window = cls()
            window.close()
            
            results["ok"].append(tool_name)
            print(f"  OK  {tool_name}")
            
        except Exception as e:
            tb = traceback.format_exc().split("\n")
            short_tb = "\n".join(tb[-3:])
            results["fail"].append(f"{tool_name}: {type(e).__name__}: {e}")
            print(f"  FAIL {tool_name}: {type(e).__name__}: {e}")
        finally:
            sys.path = old_path

print()
print(f"=" * 60)
print(f"Results: {len(results['ok'])} OK, {len(results['fail'])} FAIL, {len(results['skip'])} SKIP")
print(f"=" * 60)

if results["fail"]:
    print()
    print("FAILURES:")
    for f in results["fail"]:
        print(f"  {f}")
