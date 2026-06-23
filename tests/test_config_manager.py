# -*- coding: utf-8 -*-
import json
import pytest
from pathlib import Path
from Common.config.config_manager import ConfigManager


@pytest.fixture(autouse=True)
def reset_singleton(monkeypatch, tmp_path):
    """ConfigManager """
    ConfigManager._instance = None
    ConfigManager._data = None
    config_dir = tmp_path / "Config"
    config_file = config_dir / "settings.json"
    monkeypatch.setattr("Common.config.config_manager.CONFIG_DIR", config_dir)
    monkeypatch.setattr("Common.config.config_manager.CONFIG_FILE", config_file)
    yield
    ConfigManager._instance = None
    ConfigManager._data = None


def test_singleton():
    a = ConfigManager()
    b = ConfigManager()
    assert a is b


def test_defaults_loaded():
    cfg = ConfigManager()
    assert cfg.get("theme") == "dark"
    assert cfg.get("language") == "zh_CN"
    assert cfg.get("max_recent") == 20
    assert cfg.get("auto_save") is True


def test_get_nested_key():
    cfg = ConfigManager()
    assert cfg.get("window_layouts", {}) == {}


def test_get_missing_key_default():
    cfg = ConfigManager()
    assert cfg.get("nonexistent") is None
    assert cfg.get("nonexistent", "fallback") == "fallback"


def test_set_and_get():
    cfg = ConfigManager()
    cfg.set("theme", "light")
    assert cfg.get("theme") == "light"


def test_set_nested_creates_intermediate():
    cfg = ConfigManager()
    cfg.set("a.b.c", 42)
    assert cfg.get("a.b.c") == 42


def test_set_persists(tmp_path, monkeypatch):
    cfg = ConfigManager()
    cfg.set("theme", "light")
    config_file = tmp_path / "Config" / "settings.json"
    with open(config_file, encoding="utf-8") as f:
        data = json.load(f)
    assert data["theme"] == "light"


def test_add_recent_project():
    cfg = ConfigManager()
    cfg.add_recent_project("/a/b.json")
    cfg.add_recent_project("/c/d.json")
    recent = cfg.get_recent_projects()
    assert recent[0] == "/c/d.json"
    assert recent[1] == "/a/b.json"


def test_add_recent_dedup():
    cfg = ConfigManager()
    cfg.add_recent_project("/a/b.json")
    cfg.add_recent_project("/c/d.json")
    cfg.add_recent_project("/a/b.json")
    recent = cfg.get_recent_projects()
    assert recent[0] == "/a/b.json"
    assert recent.count("/a/b.json") == 1


def test_save_load_window_layout():
    cfg = ConfigManager()
    cfg.save_window_layout("MyTool", "ABC123")
    assert cfg.load_window_layout("MyTool") == "ABC123"


def test_load_window_layout_missing():
    cfg = ConfigManager()
    assert cfg.load_window_layout("NonExistent") is None


def test_load_corrupted_file(tmp_path, monkeypatch):
    config_dir = tmp_path / "Config"
    config_dir.mkdir()
    config_file = config_dir / "settings.json"
    config_file.write_text("not valid json{{{", encoding="utf-8")
    ConfigManager._instance = None
    ConfigManager._data = None
    cfg = ConfigManager()
    assert cfg.get("theme") == "dark"
