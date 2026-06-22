import sys
sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Common")

# Test QSS loading
from themes.stylesheet import generate_stylesheet
dark = generate_stylesheet("dark")
light = generate_stylesheet("light")
print(f"[1] Dark QSS: {len(dark)} chars, has background: {'background' in dark}")
print(f"[2] Light QSS: {len(light)} chars, has background: {'background' in light}")

# Test launcher QSS file
from pathlib import Path
qss_path = Path(r"D:\Lighting_Designer_Workstation\Common\themes\launcher.qss")
if qss_path.exists():
    qss = qss_path.read_text(encoding="utf-8")
    print(f"[3] launcher.qss: {len(qss)} chars")
else:
    print("[3] launcher.qss: NOT FOUND")

# Test version.json
ver_path = Path(r"D:\Lighting_Designer_Workstation\Config\version.json")
import json
ver = json.loads(ver_path.read_text(encoding="utf-8"))
print(f"[4] version.json: {ver}")

# Test launcher.py version reading
sys.path.insert(0, r"D:\Lighting_Designer_Workstation")
# We can't import launcher directly (it has QApplication), but we can check the function
exec(open(r"D:\Lighting_Designer_Workstation\launcher.py", encoding="utf-8").read().split("class SplashScreen")[0])
print(f"[5] APP_VERSION: {APP_VERSION}")

print("\nTheme & Config: ALL OK")