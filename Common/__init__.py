# -*- coding: utf-8 -*-
"""
Lighting Designer Workstation - 共享库
GrandMA3 风格深色主题
"""
__version__ = "2.1.0"
import sys, os
# 确保 Common/ 在 sys.path 中（避免重复插入）
_common_dir = os.path.dirname(os.path.abspath(__file__))
if _common_dir not in sys.path:
    sys.path.insert(0, _common_dir)
