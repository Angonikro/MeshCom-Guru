#ifndef APP_VERSION
#define APP_VERSION "0.3.65"
#endif

[Setup]
AppName=MeshCom-Guru
AppVersion={#APP_VERSION}
AppPublisher=Angonikro
DefaultDirName={autopf}\MeshCom-Guru
DefaultGroupName=MeshCom-Guru
OutputDir=Output
OutputBaseFilename=MeshCom-Guru_v{#APP_VERSION}_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes

[Files]
Source: "..\dist\MeshCom-Guru\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\MeshCom-Guru"; Filename: "{app}\MeshCom-Guru.exe"
Name: "{autodesktop}\MeshCom-Guru"; Filename: "{app}\MeshCom-Guru.exe"

[Run]
Filename: "{app}\MeshCom-Guru.exe"; Description: "MeshCom-Guru starten"; Flags: nowait postinstall skipifsilent
