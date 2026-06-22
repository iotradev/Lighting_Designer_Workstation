# Lighting Designer Workstation - 安装程序生成器
# 运行此脚本将创建一个完整的 Windows 安装包

$ErrorActionPreference = "Stop"
$AppName = "Lighting Designer Workstation"
$AppVersion = "1.0.0"
$Publisher = "Lighting Designer"
$InstallDir = "$env:LOCALAPPDATA\$AppName"
$DistDir = "Releases\dist\LightingDesignerWorkstation"
$OutputDir = "Releases"

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║    创建安装程序 - $AppName         ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 检查分发包是否存在
if (-not (Test-Path "$DistDir\$AppName.exe" -ErrorAction SilentlyContinue)) {
    Write-Host "  [错误] 未找到分发包，请先运行 build_dist.bat" -ForegroundColor Red
    exit 1
}

# 创建安装脚本
Write-Host "  [1/3] 生成安装脚本..." -ForegroundColor Yellow

$installScript = @"
# Lighting Designer Workstation - 安装脚本
# 右键 -> 使用 PowerShell 运行

`$ErrorActionPreference = "Stop"
`$AppName = "$AppName"
`$AppVersion = "$AppVersion"
`$InstallDir = "`$env:LOCALAPPDATA\`$AppName"

Write-Host ""
Write-Host "  正在安装 `$AppName v`$AppVersion..." -ForegroundColor Cyan
Write-Host ""

# 创建安装目录
if (-not (Test-Path `$InstallDir)) {
    New-Item -ItemType Directory -Path `$InstallDir -Force | Out-Null
}

# 复制文件
Write-Host "  [1/4] 复制文件..." -ForegroundColor Gray
`$sourceDir = Split-Path -Parent `$MyInvocation.MyCommand.Path
Copy-Item -Path "`$sourceDir\*" -Destination `$InstallDir -Recurse -Force -Exclude @("安装.bat","卸载.bat","install.ps1")

# 创建桌面快捷方式
Write-Host "  [2/4] 创建桌面快捷方式..." -ForegroundColor Gray
`$shell = New-Object -ComObject WScript.Shell
`$shortcut = `$shell.CreateShortcut("`$env:USERPROFILE\Desktop\`$AppName.lnk")
`$shortcut.TargetPath = "`$InstallDir\$AppName.exe"
`$shortcut.WorkingDirectory = `$InstallDir
`$shortcut.Description = `$AppName
`$shortcut.Save()

# 创建开始菜单快捷方式
Write-Host "  [3/4] 创建开始菜单..." -ForegroundColor Gray
`$startMenu = "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\`$AppName"
if (-not (Test-Path `$startMenu)) {
    New-Item -ItemType Directory -Path `$startMenu -Force | Out-Null
}
`$shortcut = `$shell.CreateShortcut("`$startMenu\`$AppName.lnk")
`$shortcut.TargetPath = "`$InstallDir\$AppName.exe"
`$shortcut.WorkingDirectory = `$InstallDir
`$shortcut.Description = `$AppName
`$shortcut.Save()

# 创建卸载快捷方式
`$uninstallShortcut = `$shell.CreateShortcut("`$startMenu\卸载.lnk")
`$uninstallShortcut.TargetPath = "`$InstallDir\卸载.bat"
`$uninstallShortcut.WorkingDirectory = `$InstallDir
`$uninstallShortcut.Save()

Write-Host "  [4/4] 完成安装" -ForegroundColor Gray
Write-Host ""
Write-Host "  ══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  安装完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  安装位置: `$InstallDir" -ForegroundColor White
Write-Host "  桌面快捷方式: 已创建" -ForegroundColor White
Write-Host "  开始菜单: 已创建" -ForegroundColor White
Write-Host ""
Write-Host "  双击桌面快捷方式即可启动" -ForegroundColor White
Write-Host "  ══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
pause
"@

# 创建卸载脚本
$uninstallScript = @"
# Lighting Designer Workstation - 卸载脚本
`$AppName = "$AppName"
`$InstallDir = "`$env:LOCALAPPDATA\`$AppName"

Write-Host ""
Write-Host "  正在卸载 `$AppName..." -ForegroundColor Yellow
Write-Host ""

# 删除桌面快捷方式
`$desktop = "`$env:USERPROFILE\Desktop\`$AppName.lnk"
if (Test-Path `$desktop) { Remove-Item `$desktop -Force }

# 删除开始菜单
`$startMenu = "`$env:APPDATA\Microsoft\Windows\Start Menu\Programs\`$AppName"
if (Test-Path `$startMenu) { Remove-Item `$startMenu -Recurse -Force }

# 删除安装目录
if (Test-Path `$InstallDir) {
    Remove-Item `$InstallDir -Recurse -Force
}

Write-Host "  卸载完成！" -ForegroundColor Green
Write-Host ""
pause
"@

# 写入脚本文件
$installScript | Out-File -FilePath "$DistDir\安装.bat" -Encoding utf8
$uninstallScript | Out-File -FilePath "$DistDir\卸载.bat" -Encoding utf8

Write-Host "  [2/3] 创建 ZIP 安装包..." -ForegroundColor Yellow

# 创建带安装脚本的 ZIP
$zipPath = "$OutputDir\LightingDesignerWorkstation_Setup_v$AppVersion.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path "$DistDir\*" -DestinationPath $zipPath -Force

Write-Host "  [3/3] 完成" -ForegroundColor Yellow

Write-Host ""
Write-Host "  ═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  安装包创建完成！" -ForegroundColor Green
Write-Host ""
Write-Host "  输出文件:" -ForegroundColor White
Write-Host "    $zipPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "  分发方式:" -ForegroundColor White
Write-Host "    1. 把 ZIP 发给别人" -ForegroundColor White
Write-Host "    2. 对方解压 ZIP" -ForegroundColor White
Write-Host "    3. 双击 安装.bat" -ForegroundColor White
Write-Host "    4. 自动安装到开始菜单和桌面" -ForegroundColor White
Write-Host "    5. 卸载时双击 卸载.bat" -ForegroundColor White
Write-Host ""
Write-Host "  安装过程:" -ForegroundColor White
Write-Host "    - 自动复制到 %LOCALAPPDATA%\Lighting Designer Workstation" -ForegroundColor Gray
Write-Host "    - 自动创建桌面快捷方式" -ForegroundColor Gray
Write-Host "    - 自动创建开始菜单" -ForegroundColor Gray
Write-Host "    - 无需管理员权限" -ForegroundColor Gray
Write-Host "  ═══════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

# 显示文件大小
$zipSize = (Get-Item $zipPath).Length / 1MB
Write-Host "  安装包大小: $([math]::Round($zipSize, 1)) MB" -ForegroundColor Cyan
Write-Host ""
