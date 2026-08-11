# -*- coding: utf-8 -*-
import json
import pytest
from pathlib import Path
from Common.project.project_manager import Project, ProjectManager


class TestProject:
    def test_default_data(self):
        p = Project()
        assert p.data["name"] == ""
        assert p.data["version"] == "1.0"
        assert p.data["fixtures"] == []
        assert p.data["cues"] == []

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "project.json"
        p = Project()
        p.data["name"] = "Test Show"
        p.save(path)
        assert path.exists()
        p2 = Project(path)
        assert p2.data["name"] == "Test Show"

    def test_get_set(self):
        p = Project()
        p.set("venue", "Grand Theatre")
        assert p.get("venue") == "Grand Theatre"
        assert p.get("missing", "default") == "default"

    def test_add_remove_fixture(self):
        p = Project()
        p.add_fixture({"name": "Spot", "channel": 1})
        p.add_fixture({"name": "Wash", "channel": 10})
        assert len(p.data["fixtures"]) == 2
        p.remove_fixture(0)
        assert len(p.data["fixtures"]) == 1
        assert p.data["fixtures"][0]["name"] == "Wash"

    def test_remove_fixture_out_of_range(self):
        p = Project()
        p.remove_fixture(99)
        p.remove_fixture(-1)
        assert len(p.data["fixtures"]) == 0

    def test_add_cue_and_sort(self):
        p = Project()
        p.add_cue({"cue_number": 3, "name": "Cue 3"})
        p.add_cue({"cue_number": 1, "name": "Cue 1"})
        p.add_cue({"cue_number": 2, "name": "Cue 2"})
        sorted_cues = p.get_cues_sorted()
        assert [c["cue_number"] for c in sorted_cues] == [1, 2, 3]

    def test_to_json(self):
        p = Project()
        p.data["name"] = "JSON Test"
        j = p.to_json()
        parsed = json.loads(j)
        assert parsed["name"] == "JSON Test"

    def test_load_missing_file_creates_default(self, tmp_path):
        p = Project(tmp_path / "nonexistent.json")
        assert p.data["name"] == ""
        assert p.path == tmp_path / "nonexistent.json"

    def test_save_no_path_raises(self):
        p = Project()
        with pytest.raises(ValueError):
            p.save()


class TestProjectManager:
    def test_new_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        proj = pm.new_project("My Show", "Author")
        assert proj.data["name"] == "My Show"
        assert proj.data["author"] == "Author"
        assert proj.path.exists()
        assert pm.current_project is proj

    def test_new_project_rejects_duplicate_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        pm.new_project("My Show")
        with pytest.raises(FileExistsError):
            pm.new_project("My Show")

    def test_open_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        proj = pm.new_project("Open Test")
        pm2 = ProjectManager.__new__(ProjectManager)
        pm2.current_project = None
        pm2.logger = None
        opened = pm2.open_project(str(proj.path))
        assert opened.data["name"] == "Open Test"

    def test_open_project_dir(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        proj = pm.new_project("Dir Test")
        proj_dir = proj.path.parent
        pm2 = ProjectManager.__new__(ProjectManager)
        pm2.current_project = None
        pm2.logger = None
        opened = pm2.open_project(str(proj_dir))
        assert opened.data["name"] == "Dir Test"

    def test_open_nonexistent_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager.__new__(ProjectManager)
        pm.current_project = None
        pm.logger = None
        with pytest.raises(FileNotFoundError):
            pm.open_project(str(tmp_path / "nope.json"))

    def test_save_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        proj = pm.new_project("Save Test")
        proj.set("venue", "Arena")
        pm.save_project()
        loaded = Project(proj.path)
        assert loaded.data["venue"] == "Arena"

    def test_save_project_no_current(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager.__new__(ProjectManager)
        pm.current_project = None
        pm.logger = None
        pm.save_project()

    def test_list_projects(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        pm.new_project("Show A")
        pm.new_project("Show B")
        projects = pm.list_projects()
        names = [p["name"] for p in projects]
        assert "Show A" in names
        assert "Show B" in names

    def test_backups_are_isolated_by_project(self, tmp_path, monkeypatch):
        monkeypatch.setattr("Common.project.project_manager.PROJECTS_DIR", tmp_path / "Projects")
        monkeypatch.setattr("Common.project.project_manager.BACKUPS_DIR", tmp_path / "Backups")
        pm = ProjectManager()
        pm.new_project("Show")
        pm.backup_project()
        pm.current_project = pm.new_project("Show_2")
        pm.backup_project()
        pm._cleanup_backups("Show", max_backups=0)
        assert not (tmp_path / "Backups" / "Show").exists() or not list((tmp_path / "Backups" / "Show").iterdir())
        assert list((tmp_path / "Backups" / "Show_2").iterdir())
