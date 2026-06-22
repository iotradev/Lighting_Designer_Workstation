# -*- coding: utf-8 -*-
"""
椤圭洰绠＄悊绯荤粺
缁熶竴浣跨敤JSON鏍煎紡锛屾墍鏈夊伐鍏峰叡浜?Projects/ 鐩綍
鏀寔: 鏂板缓銆佹墦寮€銆佷繚瀛樸€佽嚜鍔ㄥ浠姐€佹渶杩戦」鐩?"""
import json, os, shutil, time
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

BASE_DIR = Path(__file__).parent.parent.parent
PROJECTS_DIR = BASE_DIR / "Projects"
BACKUPS_DIR = BASE_DIR / "Backups"

class Project:
    """椤圭洰鏁版嵁妯″瀷"""
    def __init__(self, path: Path = None):
        self.path = path
        self.data = {
            "name": "鏈懡鍚嶉」鐩?,
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
        """浠嶫SON鏂囦欢鍔犺浇椤圭洰"""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self.data.update(loaded)
        except (json.JSONDecodeError, IOError) as e:
            raise ValueError(f"鏃犳硶鍔犺浇椤圭洰鏂囦欢: {e}")

    def save(self, path: Path = None):
        """原子写入项目文件"""
        save_path = path or self.path
        if not save_path:
            raise ValueError("未指定保存路径")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["modified_at"] = datetime.now().isoformat()
        tmp_path = save_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, save_path)
        self.path = save_path

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def add_fixture(self, fixture: dict):
        """娣诲姞鐏叿"""
        self.data["fixtures"].append(fixture)

    def remove_fixture(self, index: int):
        """绉婚櫎鐏叿"""
        if 0 <= index < len(self.data["fixtures"]):
            self.data["fixtures"].pop(index)

    def add_cue(self, cue: dict):
        """娣诲姞Cue"""
        self.data["cues"].append(cue)

    def get_cues_sorted(self):
        """鑾峰彇鎺掑簭鍚庣殑Cue鍒楄〃"""
        return sorted(self.data["cues"], key=lambda c: c.get("cue_number", 0))

    def to_json(self):
        return json.dumps(self.data, indent=2, ensure_ascii=False)


class ProjectManager:
    """
    椤圭洰绠＄悊鍣?    绠＄悊椤圭洰鐨勬柊寤恒€佹墦寮€銆佷繚瀛樸€佸浠姐€佹渶杩戦」鐩?    """
    def __init__(self, logger=None):
        self.current_project: Optional[Project] = None
        self.logger = logger
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    def new_project(self, name: str, author: str = "") -> Project:
        """鏂板缓椤圭洰"""
        project_dir = PROJECTS_DIR / name
        project_dir.mkdir(parents=True, exist_ok=True)
        project = Project()
        project.data["name"] = name
        project.data["author"] = author
        project.path = project_dir / "project.json"
        project.save()
        self.current_project = project
        if self.logger:
            self.logger.info(f"鏂板缓椤圭洰: {name}")
        return project

    def open_project(self, path: str) -> Project:
        """鎵撳紑椤圭洰"""
        p = Path(path)
        if p.is_dir():
            p = p / "project.json"
        if not p.exists():
            raise FileNotFoundError(f"椤圭洰鏂囦欢涓嶅瓨鍦? {p}")
        project = Project(p)
        self.current_project = project
        # 娣诲姞鍒版渶杩戦」鐩?        from ..config import ConfigManager
        cfg = ConfigManager()
        cfg.add_recent_project(str(p))
        if self.logger:
            self.logger.info(f"鎵撳紑椤圭洰: {project.data['name']}")
        return project

    def save_project(self):
        """淇濆瓨褰撳墠椤圭洰"""
        if not self.current_project:
            return
        self.current_project.save()
        if self.logger:
            self.logger.info(f"椤圭洰宸蹭繚瀛? {self.current_project.data['name']}")

    def backup_project(self):
        """澶囦唤褰撳墠椤圭洰"""
        if not self.current_project or not self.current_project.path:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = self.current_project.data["name"]
        backup_name = f"{name}_{ts}"
        backup_dir = BACKUPS_DIR / backup_name
        # 澶嶅埗鏁翠釜椤圭洰鐩綍
        src = self.current_project.path.parent
        if src.exists():
            shutil.copytree(src, backup_dir, dirs_exist_ok=True)
            if self.logger:
                self.logger.info(f"椤圭洰宸插浠? {backup_name}")
        # 娓呯悊鏃у浠?        self._cleanup_backups(name)

    def _cleanup_backups(self, project_name, max_backups=50):
        """娓呯悊鏃у浠?""
        backups = sorted(
            [d for d in BACKUPS_DIR.iterdir() if d.is_dir() and d.name.startswith(project_name)],
            key=lambda d: d.stat().st_mtime,
            reverse=True
        )
        for old in backups[max_backups:]:
            shutil.rmtree(old, ignore_errors=True)

    def list_projects(self) -> List[Dict[str, Any]]:
        """鍒楀嚭鎵€鏈夐」鐩?""
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
        """鑾峰彇鏈€杩戦」鐩垪琛?""
        from ..config import ConfigManager
        return ConfigManager().get_recent_projects()

