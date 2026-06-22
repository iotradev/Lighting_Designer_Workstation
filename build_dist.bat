@echo off
chcp 65001 >nul 2>&1
title 打包分发 - Lighting Designer Workstation
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║    打包可分发版本 - Lighting Designer Workstation         ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: 检查 PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo  [安装] PyInstaller...
    pip install pyinstaller --quiet
)

:: 清理
if exist Releases\dist rmdir /s /q Releases\dist
if not exist Releases mkdir Releases

echo  ═══════════════════════════════════════════════════════
echo  [1/3] 打包单文件 EXE (最易分发)
echo  ═══════════════════════════════════════════════════════

pyinstaller ^
    --onefile --windowed ^
    --name "LightingDesignerWorkstation" ^
    --distpath Releases\dist ^
    --workpath Releases\.build ^
    --specpath Releases\.spec ^
    --clean --noconfirm ^
    --add-data "Config;Config" ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtSvg ^
    --hidden-import numpy ^
    launcher.py

if errorlevel 1 (
    echo  [错误] 单文件打包失败！
    pause
    exit /b 1
)

echo.
echo  ═══════════════════════════════════════════════════════
echo  [2/3] 创建分发包
echo  ═══════════════════════════════════════════════════════

:: 创建分发目录
set DIST=Releases\dist\LightingDesignerWorkstation
mkdir "%DIST%" 2>nul

:: 复制单文件 EXE
copy Releases\dist\LightingDesignerWorkstation.exe "%DIST%\" >nul

:: 复制工具和资源
xcopy Tools "%DIST%\Tools\" /e /i /q >nul
xcopy Common "%DIST%\Common\" /e /i /q >nul
xcopy Libraries "%DIST%\Libraries\" /e /i /q >nul
xcopy Assets "%DIST%\Assets\" /e /i /q >nul
xcopy Templates "%DIST%\Templates\" /e /i /q >nul
xcopy Config "%DIST%\Config\" /e /i /q >nul

:: 复制文档
copy README.md "%DIST%\" >nul
copy CHANGELOG.md "%DIST%\" >nul
copy LICENSE "%DIST%\" >nul

:: 创建启动脚本
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo cd /d "%%~dp0"
echo start "" "LightingDesignerWorkstation.exe"
) > "%DIST%\启动.bat"

:: 创建说明文件
(
echo Lighting Designer Workstation - 舞台灯光设计工作站
echo ====================================================
echo.
echo 使用方法:
echo   双击 LightingDesignerWorkstation.exe 启动
echo   或双击 启动.bat 启动
echo.
echo 系统要求:
echo   Windows 10/11 64位
echo   无需安装 Python (已内置)
echo.
echo 工具列表:
echo   42 个专业灯光设计工具
echo   详见 README.md
echo.
echo 版本: 1.0.0
echo 许可证: MIT License
) > "%DIST%\使用说明.txt"

echo.
echo  ═══════════════════════════════════════════════════════
echo  [3/3] 创建 ZIP 压缩包
echo  ═══════════════════════════════════════════════════════

:: 尝试用 PowerShell 创建 ZIP
powershell -Command "Compress-Archive -Path '%DIST%\*' -DestinationPath 'Releases\LightingDesignerWorkstation_v1.0.0.zip' -Force" 2>nul
if exist Releases\LightingDesignerWorkstation_v1.0.0.zip (
    echo  ZIP 压缩包已创建
) else (
    echo  [提示] ZIP 创建失败，请手动压缩 Releases\dist\LightingDesignerWorkstation 目录
)

:: 清理临时文件
if exist Releases\.build rmdir /s /q Releases\.build
if exist Releases\.spec rmdir /s /q Releases\.spec

echo.
echo  ═══════════════════════════════════════════════════════════
echo  打包完成！
echo.
echo  输出文件:
echo    Releases\dist\LightingDesignerWorkstation.exe  (单文件 EXE)
echo    Releases\dist\LightingDesignerWorkstation\     (完整目录)
echo    Releases\LightingDesignerWorkstation_v1.0.0.zip (ZIP 压缩包)
echo.
echo  分发方式:
echo    1. 发送 ZIP 压缩包，解压后双击 EXE 即可运行
echo    2. 或发送单文件 EXE + Tools/Common 目录
echo  ═══════════════════════════════════════════════════════════
echo.
pause
