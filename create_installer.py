# -*- coding: utf-8 -*-
"""创建 Windows 安装包"""
import os, shutil, zipfile
from pathlib import Path

BASE = Path(__file__).parent
DIST = BASE / "Releases" / "dist" / "LightingDesignerWorkstation"
OUTPUT = BASE / "Releases"
APP = "Lighting Designer Workstation"
VER = "1.0.0"

print()
print("  ╔══════════════════════════════════════════════════════╗")
print("  ║    创建安装程序 - Lighting Designer Workstation       ║")
print("  ╚══════════════════════════════════════════════════════╝")
print()

if not (DIST / "LightingDesignerWorkstation.exe").exists():
    print("  [错误] 未找到分发包，请先运行 build_dist.bat")
    exit(1)

# ── 1. 创建安装脚本 ──
print("  [1/4] 生成安装脚本...")

install_bat = r"""@echo off
chcp 65001 >nul 2>&1
title 安装 - Lighting Designer Workstation
cd /d "%~dp0

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║    安装 - Lighting Designer Workstation               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  正在安装...
echo.

:: 安装目录
set "INSTDIR=%LOCALAPPDATA%\Lighting Designer Workstation"

:: 复制文件
echo  [1/3] 复制文件到 %INSTDIR% ...
if not exist "%INSTDIR%" mkdir "%INSTDIR%"
xcopy /e /i /q /y "%~dp0Tools" "%INSTDIR%\Tools" >nul
xcopy /e /i /q /y "%~dp0Common" "%INSTDIR%\Common" >nul
xcopy /e /i /q /y "%~dp0Libraries" "%INSTDIR%\Libraries" >nul
xcopy /e /i /q /y "%~dp0Assets" "%INSTDIR%\Assets" >nul
xcopy /e /i /q /y "%~dp0Templates" "%INSTDIR%\Templates" >nul
xcopy /e /i /q /y "%~dp0Config" "%INSTDIR%\Config" >nul
copy /y "%~dp0LightingDesignerWorkstation.exe" "%INSTDIR%\" >nul
copy /y "%~dp0README.md" "%INSTDIR%\" >nul
copy /y "%~dp0LICENSE" "%INSTDIR%\" >nul
copy /y "%~dp0使用说明.txt" "%INSTDIR%\" >nul

:: 创建启动脚本
(
echo @echo off
echo cd /d "%%~dp0"
echo start "" "LightingDesignerWorkstation.exe"
) > "%INSTDIR%\启动.bat"

:: 创建卸载脚本
(
echo @echo off
echo title 卸载 - Lighting Designer Workstation
echo echo.
echo echo  正在卸载...
echo del /q "%%USERPROFILE%%\Desktop\Lighting Designer Workstation.lnk" 2^>nul
echo rmdir /s /q "%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\Lighting Designer Workstation" 2^>nul
echo rmdir /s /q "%%LOCALAPPDATA%%\Lighting Designer Workstation" 2^>nul
echo echo.
echo echo  卸载完成！
echo pause
) > "%INSTDIR%\卸载.bat"

:: 创建桌面快捷方式
echo  [2/3] 创建快捷方式...
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%USERPROFILE%\Desktop\Lighting Designer Workstation.lnk'); $s.TargetPath='%INSTDIR%\LightingDesignerWorkstation.exe'; $s.WorkingDirectory='%INSTDIR%'; $s.Save()" >nul 2>&1

:: 创建开始菜单
set "SMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Lighting Designer Workstation"
if not exist "%SMENU%" mkdir "%SMENU%"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SMENU%\Lighting Designer Workstation.lnk'); $s.TargetPath='%INSTDIR%\LightingDesignerWorkstation.exe'; $s.WorkingDirectory='%INSTDIR%'; $s.Save()" >nul 2>&1
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SMENU%\卸载.lnk'); $s.TargetPath='%INSTDIR%\卸载.bat'; $s.WorkingDirectory='%INSTDIR%'; $s.Save()" >nul 2>&1

echo  [3/3] 完成
echo.
echo  ══════════════════════════════════════════════════════
echo  安装完成！
echo.
echo  安装位置: %INSTDIR%
echo  桌面快捷方式: 已创建
echo  开始菜单: 已创建
echo.
echo  双击桌面快捷方式即可启动
echo  ══════════════════════════════════════════════════════
echo.
pause
"""

(DIST / "安装.bat").write_text(install_bat, encoding='utf-8')

# ── 2. 创建卸载脚本（独立版）──
uninstall_bat = r"""@echo off
chcp 65001 >nul 2>&1
title 卸载 - Lighting Designer Workstation

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║    卸载 - Lighting Designer Workstation               ║
echo  ╚══════════════════════════════════════════════════════╝
echo.
echo  正在卸载...
echo.

del /q "%USERPROFILE%\Desktop\Lighting Designer Workstation.lnk" 2>nul
rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Lighting Designer Workstation" 2>nul
rmdir /s /q "%LOCALAPPDATA%\Lighting Designer Workstation" 2>nul

echo  卸载完成！
echo.
pause
"""

(DIST / "卸载.bat").write_text(uninstall_bat, encoding='utf-8')

# ── 3. 创建使用说明 ──
readme = f"""Lighting Designer Workstation v{VER}
舞台灯光设计工作站

═══════════════════════════════════════

安装方法:
  1. 双击 "安装.bat"
  2. 等待安装完成
  3. 双击桌面快捷方式启动

卸载方法:
  双击 "卸载.bat"

═══════════════════════════════════════

包含 42 个专业灯光设计工具:

  🎵 音乐分析 (5个)
     BPM分析、节拍检测、频谱分析、音乐结构、情绪分析

  🎹 MIDI工具 (6个)
     监听、发送、映射、录制、时间码生成/监视

  💡 DMX/网络 (6个)
     DMX计算、灯具配接、DMX测试、Art-Net/sACN监听、RDM

  🔦 灯光设计 (6个)
     舞台平面图、灯具数据库、光束/照度/色彩计算、GOBO预览

  🎬 视觉预演 (2个)
     3D灯光模拟、LED像素映射

  ✨ 特效工程 (7个)
     激光规划、特效设计、功率/线缆/配电/UPS/发电机计算

  🎭 演出管理 (6个)
     演出管理、Cue设计、时间轴、节目单、设备清单、备份

  🤖 AI辅助 (4个)
     灯光建议、编程助手、舞美建议、故障诊断

═══════════════════════════════════════

系统要求:
  Windows 10/11 (64位)
  无需安装 Python (已内置)

版本: {VER}
许可证: MIT License
"""

(DIST / "使用说明.txt").write_text(readme, encoding='utf-8')

print("  [2/4] 安装脚本已生成")

# ── 4. 创建 ZIP 安装包 ──
print("  [3/4] 创建 ZIP 安装包...")

zip_path = OUTPUT / f"LightingDesignerWorkstation_Setup_v{VER}.zip"
if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(DIST):
        for f in files:
            fp = Path(root) / f
            arcname = fp.relative_to(DIST)
            zf.write(fp, arcname)

print("  [4/4] 完成")

# ── 输出 ──
size_mb = zip_path.stat().st_size / (1024 * 1024)
print()
print("  ═══════════════════════════════════════════════════════════")
print("  安装包创建完成！")
print()
print(f"  输出: {zip_path}")
print(f"  大小: {size_mb:.1f} MB")
print()
print("  分发方式:")
print("    1. 把 ZIP 发给别人")
print("    2. 对方解压 ZIP")
print("    3. 双击 安装.bat")
print("    4. 自动安装到桌面和开始菜单")
print("    5. 卸载时双击 卸载.bat")
print()
print("  安装过程:")
print("    - 复制到 %LOCALAPPDATA%\\Lighting Designer Workstation")
print("    - 自动创建桌面快捷方式")
print("    - 自动创建开始菜单")
print("    - 无需管理员权限")
print("  ═══════════════════════════════════════════════════════════")
print()
