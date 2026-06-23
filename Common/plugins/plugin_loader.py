# -*- coding: utf-8 -*-
"""

 Plugins/ 
: plugin.json () + main.py ()
"""
import json, importlib.util, sys
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent.parent
PLUGINS_DIR = BASE_DIR / "Plugins"


class PluginInfo:
    """"""
    def __init__(self, name, version, description, author, path, entry):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.path = path
        self.entry = entry
        self.module = None
        self.enabled = True

    def __repr__(self):
        return f"<Plugin: {self.name} v{self.version}>"


class PluginLoader:
    """插件加载器

    安全警告: 插件通过 exec_module 直接执行，无沙箱隔离。
    仅加载可信来源的插件。恶意插件可执行任意代码。
    """

    def __init__(self, logger=None):
        self.plugins: Dict[str, PluginInfo] = {}
        self.logger = logger
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)

    def discover(self) -> List[PluginInfo]:
        """"""
        self.plugins.clear()
        for plugin_dir in PLUGINS_DIR.iterdir():
            if not plugin_dir.is_dir():
                continue
            meta_file = plugin_dir / "plugin.json"
            entry_file = plugin_dir / "main.py"
            if not meta_file.exists() or not entry_file.exists():
                continue
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                info = PluginInfo(
                    name=meta.get("name", plugin_dir.name),
                    version=meta.get("version", "1.0"),
                    description=meta.get("description", ""),
                    author=meta.get("author", ""),
                    path=plugin_dir,
                    entry=entry_file,
                )
                self.plugins[info.name] = info
                if self.logger:
                    self.logger.info(f": {info.name} v{info.version}")
            except (json.JSONDecodeError, KeyError) as e:
                if self.logger:
                    self.logger.warning(f": {plugin_dir.name} - {e}")
        return list(self.plugins.values())

    def load(self, name: str) -> Optional[object]:
        info = self.plugins.get(name)
        if not info:
            if self.logger:
                self.logger.error(f": {name}")
            return None
        if not info.enabled:
            if self.logger:
                self.logger.info(f": {name}")
            return None
        try:
            if not info.entry.resolve().is_relative_to(info.path.resolve()):
                raise ValueError("入口文件不在插件目录内")
            spec = importlib.util.spec_from_file_location(
                f"plugin_{name}", str(info.entry)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            info.module = module
            sys.modules[f"plugin_{name}"] = module
            if self.logger:
                self.logger.info(f": {name}")
            return module
        except Exception as e:
            if self.logger:
                self.logger.error(f": {name} - {e}")
            return None

    def load_all(self) -> Dict[str, object]:
        """"""
        self.discover()
        loaded = {}
        for name in self.plugins:
            module = self.load(name)
            if module:
                loaded[name] = module
        return loaded

    def get_plugin_list(self) -> List[PluginInfo]:
        return list(self.plugins.values())
