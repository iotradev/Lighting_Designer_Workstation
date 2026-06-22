@echo off
chcp 65001 >nul 2>&1
title Lighting Designer Workstation
cd /d "%~dp0"

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [错误] 未找到 Python
    echo  请安装 Python 3.10+: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 首次运行自动安装依赖
python -c "import PySide6" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [提示] 首次运行，正在安装依赖...
    pip install PySide6 numpy --quiet
    echo.
)

:: 启动
python launcher.py
