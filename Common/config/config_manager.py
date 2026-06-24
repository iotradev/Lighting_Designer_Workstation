# -*- coding: utf-8 -*-
"""


: D:/Lighting_Designer_Workstation/Config/
"""
import json
import os
import threading
import tempfile
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent.parent  # D:/Lighting_Designer_Workstation
CONFIG_DIR = BASE_DIR / "Config"
CONFIG_FILE = CONFIG_DIR / "settings.json"

class ConfigManager:
    """"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load()
        return cls._instance

    def _load(self):
        """"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = self._defaults()
        else:
            self._data = self._defaults()
            self.save()

    def _defaults(self):
        """"""
        return {
            "version": "1.0.0",
            "theme": "dark",
            "language": "zh_CN",
            "recent_projects": [],
            "max_recent": 20,
            "auto_save": True,
            "auto_save_interval": 300,  # 
            "auto_backup": True,
            "backup_interval": 3600,
            "max_backups": 50,
            "window_layouts": {},
            "log_level": "INFO",
            "log_to_file": True,
            "plugins_enabled": True,
            "last_open_dir": str(BASE_DIR / "Projects"),
            "last_export_dir": str(BASE_DIR / "Exports"),
        }

    def get(self, key, default=None):
        """"""
        keys = key.split(".")
        with self._lock:
            val = self._data
            for k in keys:
                if isinstance(val, dict) and k in val:
                    val = val[k]
                else:
                    return default
        return val

    def set(self, key, value):
        keys = key.split(".")
        with self._lock:
            d = self._data
            for k in keys[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = value
        self.save()

    def save(self):
        """"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=str(CONFIG_DIR), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            Path(tmp_path).replace(CONFIG_FILE)
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def add_recent_project(self, path):
        """"""
        with self._lock:
            recent = self._data.get("recent_projects", [])
            path_str = str(path)
            if path_str in recent:
                recent.remove(path_str)
            recent.insert(0, path_str)
            self._data["recent_projects"] = recent[:self._data.get("max_recent", 20)]
        self.save()

    def get_recent_projects(self):
        """"""
        return self._data.get("recent_projects", [])

    def save_window_layout(self, name, geometry_hex):
        """"""
        with self._lock:
            layouts = self._data.get("window_layouts", {})
            layouts[name] = {"geometry": geometry_hex, "saved_at": datetime.now().isoformat()}
            self._data["window_layouts"] = layouts
        self.save()

    def load_window_layout(self, name):
        """"""
        with self._lock:
            layouts = self._data.get("window_layouts", {})
            layout = layouts.get(name)
            return layout.get("geometry") if layout else None
