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
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer\output
OutputBaseFilename=VerbaMind-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DiskSpanning=yes
DiskSliceSize=2000000000
; LicenseKeyFile=installer\license.txt
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
; Models directory (placeholder — user adds models after install)
Source: "models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\models'))
; Config
Source: "verbamind\config\config.example.json"; DestDir: "{app}\config"; DestName: "config.json"; Flags: onlyifdoesntexist
; VC++ Redistributable (bundled)
Source: "installer\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Install VC++ Redistributable silently
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Installing Visual C++ Runtime..."; Check: VCRedistNeedsInstall
; Launch app after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\recordings"
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\output_hasil"

[Code]
// Check if VC++ Redistributable is already installed
function VCRedistNeedsInstall(): Boolean;
var
  Result1: Cardinal;
begin
  Result := not RegQueryDWordValue(HKLM, 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64', 'Version', Result1);
end;

// Custom page: License Key Input
var
  LicensePage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  LicensePage := CreateInputQueryPage(wpUserInfo,
    'License Activation',
    'Enter your VerbaMind license key',
    'Your license key is bound to this computer''s Hardware ID. Please enter the key provided to you.');
  LicensePage.Add('License Key:', False);
  LicensePage.Add('Hardware ID (auto-detected):', True);
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  // Skip the license page during silent install
  if WizardSilent() and (PageID = LicensePage.ID) then
    Result := True
  else
    Result := False;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  LicenseKey: String;
begin
  Result := True;
  
  if CurPageID = LicensePage.ID then
  begin
    LicenseKey := LicensePage.Values[0];
    if LicenseKey = '' then
    begin
      MsgBox('Please enter your license key.', mbError, MB_OK);
      Result := False;
    end;
    // Save license key for the app to validate on first run
    SaveStringToFile(ExpandConstant('{app}\config\.license_key'), LicenseKey, False);
  end;
end;

function UpdateReadyMemo(Space, NewLine, MemoUserInfoInfo, MemoDirInfo, MemoTypeInfo, MemoComponentsInfo, MemoGroupInfo, MemoTasksInfo: String): String;
begin
  Result := MemoDirInfo + NewLine + NewLine +
            'License Key: ' + LicensePage.Values[0] + NewLine +
            'Hardware ID: ' + LicensePage.Values[1] + NewLine + NewLine +
            MemoGroupInfo + NewLine + NewLine +
            MemoTasksInfo;
end;
