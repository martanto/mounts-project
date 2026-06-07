; Inno Setup script for MOUNTS Desktop Dashboard.
;
; Build:
;   1. uv run pyinstaller mounts-dashboard.spec      (produces dist\mounts-dashboard\)
;   2. iscc installer\mounts-dashboard.iss           (produces installer\Output\mounts-dashboard-setup-<ver>.exe)
;
; Install Inno Setup 6 from https://jrsoftware.org/isdl.php if `iscc` is not on PATH.

#define MyAppName       "MOUNTS Dashboard"
#define MyAppVersion    "0.2.4"
#define MyAppPublisher  "Martanto"
#define MyAppURL        "https://github.com/martanto/mounts-project"
#define MyAppExeName    "mounts-dashboard.exe"
#define MyAppDistDir    "..\dist\mounts-dashboard"

[Setup]
AppId={{8B5F2C9E-7A3D-4B2E-9F1A-6D4C8E2B7A91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=mounts-dashboard-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyAppDistDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#MyAppDistDir}\*";                DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "{#MyAppExeName}"

[Icons]
Name: "{group}\{#MyAppName}";          Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}";    Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
