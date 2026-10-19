; Inno Setup script for WA Desktop.
;
;   iscc /DAppVersion=1.1.0 /DSourceDir="dist\WA Desktop" /DOutputDir=packages packaging\windows\wadesk.iss
;
; Installs per user by default (no administrator rights needed); the setup offers an
; "install for all users" choice as well.

#ifndef AppVersion
  #error AppVersion must be defined
#endif
#ifndef SourceDir
  #define SourceDir "..\..\dist\WA Desktop"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\packages"
#endif

#define AppName "WA Desktop"
#define AppExe "WA Desktop.exe"
#define AppUserModelID "io.github.pahrulirfan.wadesk"

[Setup]
AppId={{8C3F2B6E-6A0E-4D8E-9C5B-2E7F4A1D9B30}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=Pahrul Irfan
AppPublisherURL=https://pahrulirfan.github.io/wa-desktop/
AppSupportURL=https://github.com/pahrulirfan/wa-desktop/issues
AppUpdatesURL=https://github.com/pahrulirfan/wa-desktop/releases/latest
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir={#OutputDir}
OutputBaseFilename=WA-Desktop-{#AppVersion}-windows-x64-setup
SetupIconFile=wadesk.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
LicenseFile=..\..\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "{#AppUserModelID}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; AppUserModelID: "{#AppUserModelID}"; Tasks: desktopicon

[Registry]
; Only removes the "Launch at login" entry the app may have created; the app writes it itself.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "{#AppName}"; Flags: uninsdeletevalue dontcreatekey

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/f /im ""{#AppExe}"""; Flags: runhidden; RunOnceId: "StopApp"
