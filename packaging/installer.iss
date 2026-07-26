; Inno Setup script — build.ps1 truyền version qua /DMyAppVersion=x.y.z
; Cần Inno Setup 6: https://jrsoftware.org/isdl.php (iscc.exe trong PATH)

#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif

[Setup]
; AppId CỐ ĐỊNH — mọi bản update cài đè đúng chỗ, KHÔNG được đổi
AppId={{B7E63FA2-4C1D-4E8A-9F2B-5A0C8D913E77}
AppName=rebarFlow
AppVersion={#MyAppVersion}
AppPublisher=tuananhfr
AppPublisherURL=https://github.com/tuananhfr/rebarflow
DefaultDirName={autopf}\rebarFlow
DefaultGroupName=rebarFlow
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=rebarflow-setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
; updater gọi /SILENT /CLOSEAPPLICATIONS — 2 dòng dưới cho phép đóng app đang chạy
CloseApplications=yes
RestartApplications=yes
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\rebarflow\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\rebarFlow"; Filename: "{app}\rebarflow.exe"
Name: "{autodesktop}\rebarFlow"; Filename: "{app}\rebarflow.exe"

[Run]
Filename: "{app}\rebarflow.exe"; Description: "Chạy rebarFlow"; Flags: nowait postinstall skipifsilent
