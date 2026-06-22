import sys
sys.path.insert(0, r"D:\Lighting_Designer_Workstation\Common")

# Test 2: ConfigManager
from config.config_manager import ConfigManager
c = ConfigManager()
print(f"[1] default theme: {c.get('theme', 'dark')}")

# Test 3: ToolLogger
from log_system.tool_logger import ToolLogger, LogLevel
l = ToolLogger("func_test")
l.set_level(LogLevel.DEBUG)
l.debug("debug msg")
l.info("info msg")
l.warning("warning msg")
print(f"[2] log file: {l._log_path}")

# Test 4: PluginLoader
from plugins.plugin_loader import PluginLoader
pl = PluginLoader()
plugins = pl.discover()
print(f"[3] plugins found: {len(plugins)}")

# Test 5: Theme stylesheet
from themes.stylesheet import generate_stylesheet
qss = generate_stylesheet("dark")
print(f"[4] dark QSS: {len(qss)} chars")
qss2 = generate_stylesheet("light")
print(f"[5] light QSS: {len(qss2)} chars")

print("Common modules: ALL OK")