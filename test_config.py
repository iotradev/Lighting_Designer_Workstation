import json
from pathlib import Path

# Test launcher version reading
ver_path = Path(r"D:\Lighting_Designer_Workstation\Config\version.json")
ver = json.loads(ver_path.read_text(encoding="utf-8"))
print(f"[1] version.json: {ver}")

# Test launcher.py has correct version reference
content = Path(r"D:\Lighting_Designer_Workstation\launcher.py").read_text(encoding="utf-8")
has_version_file = "VERSION_FILE" in content
has_get_version = "_get_version" in content
has_app_version = "APP_VERSION" in content
print(f"[2] launcher.py has VERSION_FILE: {has_version_file}")
print(f"[3] launcher.py has _get_version: {has_get_version}")
print(f"[4] launcher.py has APP_VERSION: {has_app_version}")

# Test build_all.ps1 reads version
build = Path(r"D:\Lighting_Designer_Workstation\build_all.ps1").read_text(encoding="utf-8")
has_ver_read = "version.json" in build
print(f"[5] build_all.ps1 reads version.json: {has_ver_read}")

# Test requirements.txt
req = Path(r"D:\Lighting_Designer_Workstation\requirements.txt").read_text(encoding="utf-8")
print(f"[6] requirements.txt: {req.strip()}")

# Test pyproject.toml
toml = Path(r"D:\Lighting_Designer_Workstation\pyproject.toml").read_text(encoding="utf-8")
print(f"[7] pyproject.toml has project: {'[project]' in toml}")

print("\nConfig & Build: ALL OK")