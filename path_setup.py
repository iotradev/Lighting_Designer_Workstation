# -*- coding: utf-8 -*-
"""
统一的 sys.path 初始化工具。

工具 main.py 中只需:
    from pathlib import Path
    _root = Path(__file__).resolve().parent.parent.parent.parent
    (_root / "path_setup").with_suffix(".py").exists() and exec((_root / "path_setup").read_text(encoding="utf-8"))

或调用 ensure_common_path() 即可。
"""
import sys
from pathlib import Path


def ensure_common_path(anchor_file=None):
    """确保 Common/ 目录在 sys.path 中。

    anchor_file: 传入 __file__ 即可，自动向上找到项目根目录。
    """
    if anchor_file is None:
        return
    root = Path(anchor_file).resolve().parent
    for _ in range(10):
        common = root / "Common"
        if common.is_dir() and (common / "__init__.py").exists():
            s = str(common)
            if s not in sys.path:
                sys.path.insert(0, s)
            return
        parent = root.parent
        if parent == root:
            break
        root = parent
