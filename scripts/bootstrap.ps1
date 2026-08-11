param(
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/4] 检查 Python 版本" -ForegroundColor Cyan
$version = & $Python --version
if ($LASTEXITCODE -ne 0) {
  throw "未找到 $Python"
}
Write-Host "  $version"

Write-Host "[2/4] 创建虚拟环境 .venv" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
  & $Python -m venv .venv
}

$venvPython = ".\.venv\Scripts\python.exe"

Write-Host "[3/4] 升级 pip" -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip

Write-Host "[4/4] 安装依赖" -ForegroundColor Cyan
& $venvPython -m pip install -r requirements.txt

Write-Host "完成。运行: .\.venv\Scripts\python.exe launcher.py" -ForegroundColor Green
Write-Host "测试: .\.venv\Scripts\python.exe -m pytest tests/ -v" -ForegroundColor Green
