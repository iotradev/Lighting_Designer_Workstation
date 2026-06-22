; ═══════════════════════════════════════════════════════════════
; Lighting Designer Workstation - Inno Setup 安装脚本
; GrandMA3 风格深色主题安装向导
; ═══════════════════════════════════════════════════════════════

#define MyAppName "Lighting Designer Workstation"
#define MyAppNameCN "舞台灯光设计工作站"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Lighting Designer"
#define MyAppExeName "LightingDesignerWorkstation.exe"
#define MyAppURL "https://github.com/lighting-designer/workstation"

[Setup]
AppId={{LDW-2026-ABCD-EFGH}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=LICENSE
OutputDir=Releases
OutputBaseFilename=LightingDesignerWorkstation_Setup_v{#MyAppVersion}
SetupIconFile=Assets\icon.ico
WizardImageFile=Assets\wizard_sidebar.bmp
WizardSmallImageFile=Assets\wizard_top.bmp
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
DisableProgramGroupPage=yes
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion=1.0.0.0
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppNameCN}
VersionInfoProductName={#MyAppName}
WizardSizePercent=110

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; 主程序
Source: "Releases\dist\LightingDesignerWorkstation.exe"; DestDir: "{app}"; Flags: ignoreversion
; 工具和资源
Source: "Tools\*"; DestDir: "{app}\Tools"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Common\*"; DestDir: "{app}\Common"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Libraries\*"; DestDir: "{app}\Libraries"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Assets\*"; DestDir: "{app}\Assets"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "wizard_*.bmp"
Source: "Templates\*"; DestDir: "{app}\Templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Config\*"; DestDir: "{app}\Config"; Flags: ignoreversion recursesubdirs createallsubdirs
; 文档
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\Projects"; Flags: uninsneveruninstall
Name: "{app}\Backups"; Flags: uninsneveruninstall
Name: "{app}\Logs"; Flags: uninsneveruninstall
Name: "{app}\Exports"; Flags: uninsneveruninstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "Launch {#MyAppName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; Comment: "Launch {#MyAppName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\Logs"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\Config"

[Messages]
; 自定义安装向导文字
WelcomeLabel1=Welcome to the [name] Setup Wizard
WelcomeLabel2=This will install [name/ver] on your computer.%n%nLighting Designer Workstation is a professional lighting design toolbox with 42 integrated tools for music analysis, MIDI, DMX, lighting design, visual preview, effects engineering, show management, and AI assistance.%n%nIt is recommended that you close all other applications before continuing.
FinishedLabel=Setup has finished installing [name] on your computer. The application may be launched by selecting the installed icons.
ReadyLabel1=Setup is now ready to begin installing [name] on your computer.
SelectDirLabel3=Setup will install [name] into the following folder.%n%nA Python 3.10+ installation is required to run the tools. If Python is not installed, you will be prompted to download it after installation.

[Code]
function IsPythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  if Exec('cmd.exe', '/c python --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
      Result := True;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // 创建数据目录
    CreateDir(ExpandConstant('{app}\Projects'));
    CreateDir(ExpandConstant('{app}\Backups'));
    CreateDir(ExpandConstant('{app}\Logs'));
    CreateDir(ExpandConstant('{app}\Exports'));

    // 检查 Python
    if not IsPythonInstalled then
    begin
      if MsgBox('Python 3.10+ is required to run the tools.' + #13#10 + #13#10 +
                'Would you like to download Python now?' + #13#10 + #13#10 +
                'After installing Python, restart this application.',
                mbConfirmation, MB_YESNO) = IDYES then
      begin
        ShellExec('open', 'https://www.python.org/downloads/', '', '', SW_SHOWNORMAL, ewNoWait, ResultCode);
      end;
    end
    else
    begin
      // 自动安装依赖
      Exec('cmd.exe', '/c python -c "import PySide6" >nul 2>&1 || pip install PySide6 numpy --quiet',
           '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;
