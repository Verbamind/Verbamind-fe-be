; ============================================================
; VerbaMind — Inno Setup Installer Script
; ============================================================
; Requires: Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
; Usage: Open this file in Inno Setup Studio, click Compile
; ============================================================

#define MyAppName "VerbaMind"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "VerbaMind"
#define MyAppURL "https://github.com/Verbamind"
#define MyAppExeName "VerbaMind.exe"

[Setup]
AppId={{VERBAMIND-2026-AIDEANATION}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer\output
OutputBaseFilename=VerbaMind-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DiskSpanning=yes
DiskSliceSize=2000000000
SetupIconFile=installer\verbamind.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "indonesian"; MessagesFile: "compiler:Languages\Indonesian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; GUI application
Source: "dist\VerbaMind.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Backend service
Source: "dist\backend.dist\*"; DestDir: "{app}\backend"; Flags: ignoreversion recursesubdirs createallsubdirs
; VC++ Redistributable (bundled)
Source: "installer\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ Redistributable silently
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Visual C++ Runtime..."; Check: VCRedistNeedsInstall
; Launch app after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\backend"

[Code]
// Check if VC++ Redistributable is already installed
function VCRedistNeedsInstall(): Boolean;
var
  Result1: Cardinal;
begin
  Result := not RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Version', Result1);
end;
