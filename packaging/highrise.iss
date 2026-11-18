; Inno Setup script for the Windows installer (highrise-windows-setup.exe).
;
; Build (after `pyinstaller highrise.spec --noconfirm` made dist\highrise):
;   iscc /DAppVersion=1.1.0 packaging\highrise.iss
; The release workflow does this and passes the version from the tag (pyproject.toml on a
; manual run).
;
; Reusable for other pygamine games: change AppId (generate a new GUID once, never change it
; afterwards), MyAppName, MyExeName, the output name and the [Languages] list.

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#define MyAppName "Highrise"
#define MyExeName "highrise.exe"

[Setup]
; Fixed for this game forever: it is how Windows (and a newer installer) recognizes the install.
AppId={{78916AC4-445F-4E1D-9936-EBC11052AAB9}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppPublisher=VectorViolet
; Installs for all users into Program Files by default (the setup asks for admin rights); its
; dialog also offers "only for me", which installs per-user ({autopf} then maps to the user's
; Programs folder).
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
DefaultDirName={autopf}\highrise
; Always show the folder page, so players can pick e.g. C:\Games.
DisableDirPage=no
DisableProgramGroupPage=yes
; Language dialog at the start. Only the lists are synced with config/lang/ (a test checks it);
; the choice here does not set the game's language.
ShowLanguageDialog=yes
UsePreviousLanguage=no
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyExeName}
OutputDir=..\installer-out
OutputBaseFilename=highrise-windows-setup
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Languages]
; One entry per config/lang/<code>.yaml, named by that code.
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "tr"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
; An update must not leave files the new build no longer ships (the game finds languages and
; animation frames by globbing, and old DLLs would sit beside the new ones). Saves of this
; build are in %APPDATA%. Builds before this installer kept them in _internal\databases, so
; installing over an old unzipped folder deletes those (accepted by the owner; README and
; ADR 0003 say so).
; Only where our own exe already is, so a folder the player picked that holds something else
; (say C:\Games with another game's _internal) is never wiped.
Type: filesandordirs; Name: "{app}\_internal"; Check: IsOurInstall

[Files]
; The whole PyInstaller onedir output, including _internal.
Source: "..\dist\highrise\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

; The uninstaller removes only what the installer put in the install folder (and the shortcuts).
; The save database lives in %APPDATA%\VectorViolet\highrise\databases, outside this folder, so
; it stays after an uninstall or an update: nothing here touches it.

[Code]
// True when the chosen folder already holds a Highrise install (an update or a reinstall).
function IsOurInstall: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\{#MyExeName}'));
end;
