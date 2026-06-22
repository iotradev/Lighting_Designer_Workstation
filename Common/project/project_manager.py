# -*- coding: utf-8 -*-
"""
项目管理系统
统一使用JSON格式，所有工具共享 Projects/ 目录
支持: 新建、打开、保存、自动备份、最近项目
"""
import json, os, shutil, time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).parent.parent.parent
PROJECTS_DIR = BASE_DIR / "Projects"
BACKUPS_DIR = BASE_DIR / "Backups"

class Project:
    """项目数据模型"""
    def __init__(self, path: Path = None):
        self.path = path
        self.data = {
            "name": "未命名项目",
            "author": "",
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "description": "",
            "venue": "",
            "event_date": "",
            "fixtures": [],
            "cues": [],
            "scenes": [],
            "groups": [],
            "presets": [],
            "patch": [],
            "notes": [],
            "settings": {},
            "tags": []
        }
        if path and path.exists():
            self.load()

    def load(self):
        """从JSON文件加载项目"""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self.data.update(loaded)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"无法加载项目文件: {e}")

    def save(self, path: Path = None):
        """保存项目到JSON文件"""
        save_path = path or self.path
        if not save_path:
            raise ValueError("未指定保存路径")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["modified_at"] = datetime.now().isoformat()
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        self.path = save_path

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def add_fixture(self, fixture: dict):
        """添加灯具"""
        self.data["fixtures"].append(fixture)

    def remove_fixture(self, index: int):
        """移除灯具"""
        if 0 <= index < len(self.data["fixtures"]):
            self.data["fixtures"].pop(index)

    def add_cue(self, cue: dict):
        """添加Cue"""
        self.data["cues"].append(cue)

    def get_cues_sorted(self):
        """获取排序后的Cue列表"""
        return sorted(self.data["cues"], key=lambda c: c.get("cue_number", 0))

    def to_json(self):
        return json.dumps(self.data, indent=2, ensure_ascii=False)


class ProjectManager:
    """
    项目管理器
    管理项目的新建、打开、保存、备份、最近项目
    """
    def __init__(self, logger=None):
        self.current_project: Optional[Project] = None
        self.logger = logger
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    def new_project(self, name: str, author: str = "") -> Project:
        """新建项目"""
        project_dir = PROJECTS_DIR / name
        project_dir.mkdir(parents=True, exist_ok=True)
        project = Project()
        project.data["name"] = name
        project.data["author"] = author
        project.path = project_dir / "project.json"
        project.save()
        self.current_project = project
        if self.logger:
            self.logger.info(f"新建项目: {name}")
        return project

    def open_project(self, path: str) -> Project:
        """打开项目"""
        p = Path(path)
        if p.is_dir():
            p = p / "project.json"
        if not p.exists():
            raise FileNotFoundError(f"项目文件不存在: {p}")
        project = Project(p)
        self.current_project = project
        # 添加到最近项目
        from ..config import ConfigManager
        cfg = ConfigManager()
        cfg.add_recent_project(str(p))
        if self.logger:
            self.logger.info(f"打开项目: {project.data['name']}")
        return project

    def save_project(self):
        """保存当前项目"""
        if not self.current_project:
            return
        self.current_project.save()
        if self.logger:
            self.logger.info(f"项目已保存: {self.current_project.data['name']}")

    def backup_project(self):
        """备份当前项目"""
        if not self.current_project or not self.current_project.path:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = self.current_project.data["name"]
        backup_name = f"{name}_{ts}"
        backup_dir = BACKUPS_DIR / backup_name
        # 复制整个项目目录
        src = self.current_project.path.parent
        if src.exists():
            shutil.copytree(src, backup_dir, dirs_exist_ok=True)
            if self.logger:
                self.logger.info(f"项目已备份: {backup_name}")
        # 清理旧备份
        self._cleanup_backups(name)

    def _cleanup_backups(self, project_name, max_backups=50):
        """清理旧备份"""
        backups = sorted(
            [d for d in BACKUPS_DIR.iterdir() if d.is_dir() and d.name.startswith(project_name)],
            key=lambda d: d.stat().st_mtime,
            reverse=True
        )
        for old in backups[max_backups:]:
            shutil.rmtree(old, ignore_errors=True)

    def list_projects(self) -> List[Dict[str, Any]]:
        """列出所有项目"""
        projects = []
        for d in PROJECTS_DIR.iterdir():
            pf = d / "project.json"
            if d.is_dir() and pf.exists():
                try:
                    with open(pf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    projects.append({
                        "name": data.get("name", d.name),
                        "path": str(pf),
                        "author": data.get("author", ""),
                        "modified": data.get("modified_at", ""),
                        "venue": data.get("venue", ""),
                    })
                except (json.JSONDecodeError, IOError):
                    pass
        return sorted(projects, key=lambda p: p["modified"], reverse=True)

    def get_recent_projects(self) -> List[str]:
        """获取最近项目列表"""
        from ..config import ConfigManager
        return ConfigManager().get_recent_projects()
