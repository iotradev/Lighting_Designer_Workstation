# -*- coding: utf-8 -*-
"""
Common  sys.path。

- (PYTHONPATH ): PYTHONPATH  Common/  sys.path
- ():  main.py  sys.path.insert 
"""
import sys
from pathlib import Path

def setup():
    """PYTHONPATH  Common/  sys.path"""
    for p in sys.path:
        candidate = Path(p) / "Common"
        if candidate.is_dir() and (candidate / "__init__.py").exists():
            s = str(candidate)
            if s not in sys.path:
                sys.path.insert(0, s)
            return
