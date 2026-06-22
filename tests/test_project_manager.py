# -*- coding: utf-8 -*-
import json
from pathlib import Path

from Common.project.project_manager import Project


def test_atomic_save(tmp_path):
    path = tmp_path / "project.json"
    project = Project()
    project.path = path
    project.save(path)
    assert path.exists()
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["name"] == ""