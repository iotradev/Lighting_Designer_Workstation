@echo off
chcp 65001 >nul 2>&1
title Packaging - Lighting Designer Workstation
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║    打包启动器 - Lighting Designer Workstation         ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo  [安装] PyInstaller...
    pip install pyinstaller --quiet
)

:: 清理
if exist Releases\Launcher rmdir /s /q Releases\Launcher
if not exist Releases mkdir Releases

echo  [1/2] 打包启动器...
pyinstaller ^
    --onedir --windowed ^
    --name "Launcher" ^
    --distpath Releases ^
    --workpath Releases\.build ^
    --specpath Releases\.spec ^
    --clean --noconfirm ^
    --add-data "Config;Config" ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    launcher.py

if errorlevel 1 (
    echo  [错误] 打包失败！
    pause
    exit /b 1
)

:: 清理临时文件
if exist Releases\.build rmdir /s /q Releases\.build
if exist Releases\.spec rmdir /s /q Releases\.spec

echo  [2/2] 复制工具和资源...
set DST=Releases\Launcher\_internal
xcopy Tools "%DST%\Tools\" /e /i /q >nul
xcopy Common "%DST%\Common\" /e /i /q >nul
xcopy Libraries "%DST%\Libraries\" /e /i /q >nul
xcopy Assets "%DST%\Assets\" /e /i /q >nul
xcopy Templates "%DST%\Templates\" /e /i /q >nul
copy README.md Releases\Launcher\ >nul
copy CHANGELOG.md Releases\Launcher\ >nul

echo.
echo  ══════════════════════════════════════════════════════
echo  打包完成！
echo  输出: Releases\Launcher\
echo  运行: Releases\Launcher\Launcher.exe
echo  大小:
dir /s Releases\Launcher\Launcher.exe | find "Launcher.exe"
echo  ══════════════════════════════════════════════════════
echo.
pause
