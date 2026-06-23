# -*- coding: utf-8 -*-
"""pytest conftest - 测试环境隔离"""
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def _isolate_config(monkeypatch, tmp_path):
    """隔离 ConfigManager 测试，避免污染生产 settings.json"""
    config_dir = tmp_path / "Config"
    config_file = config_dir / "settings.json"
    monkeypatch.setattr("Common.config.config_manager.CONFIG_DIR", config_dir)
    monkeypatch.setattr("Common.config.config_manager.CONFIG_FILE", config_file)
