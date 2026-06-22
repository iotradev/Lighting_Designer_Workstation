@echo off
chcp 65001 >nul
title Lighting Designer Workstation - 一键打包
echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║          一键打包 - Lighting Designer Workstation         ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

:: 安装依赖
echo [1/3] 安装依赖...
pip install PySide6 numpy pyinstaller --quiet
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，继续尝试打包...
)

:: 创建输出目录
echo [2/3] 准备打包环境...
if not exist Releases mkdir Releases
if not exist Releases\.build mkdir Releases\.build
if not exist Releases\.spec mkdir Releases\.spec

:: 打包所有工具
echo [3/3] 开始打包工具...

set TOOLS=BPMAnalyzer BeatDetector AudioSpectrum MusicStructureAnalyzer MoodAnalyzer
set TOOLS=%TOOLS% MIDIMonitor MIDISender MIDIMapper MIDIRecorder TimecodeGenerator TimecodeMonitor
set TOOLS=%TOOLS% DMXCalculator FixturePatcher DMXTester ArtNetMonitor sACNMonitor RDMTool
set TOOLS=%TOOLS% StagePlotDesigner FixtureLibrary BeamCalculator LuxCalculator ColorDesigner GoboPreviewer
set TOOLS=%TOOLS% VisualSimulator PixelMapper
set TOOLS=%TOOLS% LaserPlanner FXDesigner
set TOOLS=%TOOLS% PowerCalculator CableCalculator DistributionPlanner UPSCalculator GeneratorCalculator
set TOOLS=%TOOLS% ShowManager CueDesigner TimelineEditor CueSheetGenerator EquipmentListGenerator BackupManager
set TOOLS=%TOOLS% AILightingDesigner AIProgrammingAssistant AIStageDesigner AITroubleshooter

set /a COUNT=0
for %%T in (%TOOLS%) do (
    set /a COUNT+=1
    echo   打包 %%T...
    :: 查找main.py位置
    for /r Tools %%F in (%%T\main.py) do (
        pyinstaller --onefile --windowed --name "%%T" --distpath Releases --workpath Releases\.build --specpath Releases\.spec --clean "%%F" >nul 2>&1
    )
)

echo.
echo  ══════════════════════════════════════════════════════════
echo  打包完成！共 %COUNT% 个工具
echo  输出目录: Releases/
echo  ══════════════════════════════════════════════════════════
echo.
pause
