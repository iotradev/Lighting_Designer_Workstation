# -*- coding: utf-8 -*-
param(
  [string]$OutputDir = "Releases\dist\LightingDesignerWorkstation"
)

$ErrorActionPreference = "Stop"

$version = (Get-Content -Raw Config\version.json | ConvertFrom-Json).version

Write-Host "[1/4] 检查 Python" -ForegroundColor Cyan
python --version | Out-Null

Write-Host "[2/4] 安装依赖" -ForegroundColor Cyan
python -m pip install -r requirements.txt --quiet

Write-Host "[3/4] 准备输出目录" -ForegroundColor Cyan
if (Test-Path $OutputDir) {
  Remove-Item $OutputDir -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
New-Item -ItemType Directory -Force -Path Releases | Out-Null

Write-Host "[4/4] 打包启动器与工具" -ForegroundColor Cyan
pyinstaller --noconfirm --clean --name LightingDesignerWorkstation --distpath $OutputDir --workpath Releases\.build --specpath Releases\.spec launcher.py

xcopy Tools "$OutputDir\Tools\" /e /i /q >nul
xcopy Common "$OutputDir\Common\" /e /i /q >nul
xcopy Assets "$OutputDir\Assets\" /e /i /q >nul
xcopy Config "$OutputDir\Config\" /e /i /q >nul
xcopy Libraries "$OutputDir\Libraries\" /e /i /q >nul
xcopy Templates "$OutputDir\Templates\" /e /i /q >nul
copy README.md "$OutputDir\" >nul
copy CHANGELOG.md "$OutputDir\" >nul
copy LICENSE "$OutputDir\" >nul

$zipPath = "Releases\LightingDesignerWorkstation_v$version.zip"
if (Test-Path $zipPath) {
  Remove-Item $zipPath -Force
}
Compress-Archive -Path "$OutputDir\*" -DestinationPath $zipPath -Force

$hash = (Get-FileHash $zipPath -Algorithm SHA256).Hash
Set-Content -Path Releases\SHA256SUMS.txt -Value "$hash  LightingDesignerWorkstation_v$version.zip"

Write-Host "完成。输出：$zipPath" -ForegroundColor Green

