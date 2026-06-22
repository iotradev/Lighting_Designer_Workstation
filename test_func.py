import sys, os, json, tempfile
from pathlib import Path
sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Common")

# Test 1: ProjectManager
from project.project_manager import ProjectManager, Project
pm = ProjectManager()
p = pm.new_project("test_project", "test_author")
print(f"[1] new project: {p.data['name']}")

# Atomic save test
tmp = Path(tempfile.mktemp(suffix=".json"))
p.save(tmp)
with open(tmp, encoding="utf-8") as f:
    d = json.load(f)
print(f"[2] atomic save: name={d['name']}, author={d['author']}")
os.unlink(tmp)

# Add data
p.add_fixture({"name": "LED Wash", "channel": 1})
p.add_cue({"cue_number": 1, "name": "Opening"})
print(f"[3] add data: fixtures={len(p.data['fixtures'])}, cues={len(p.data['cues'])}")

# JSON serialization
j = p.to_json()
print(f"[4] JSON: {len(j)} chars")

print("ProjectManager: ALL OK")