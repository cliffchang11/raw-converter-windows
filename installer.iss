[Setup]
AppName=RAW 批次轉檔工具
AppVersion=1.0.0
AppPublisher=Cliff
AppPublisherURL=https://github.com/
DefaultDirName={autopf}\RAW轉檔工具
DefaultGroupName=RAW 轉檔工具
OutputBaseFilename=RAW轉檔工具_Setup_v1.0
OutputDir=installer_output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\RAW轉檔工具.exe
SetupIconFile=assets\icon.ico

[Languages]
Name: "tradchinese"; MessagesFile: "compiler:Languages\ChineseTraditional.isl"

[Tasks]
Name: "desktopicon"; Description: "在桌面建立捷徑"; GroupDescription: "其他工作"; Flags: checked

[Files]
; 主程式（由 build.bat 生成的 exe）
Source: "dist\RAW轉檔工具.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; 開始功能表捷徑
Name: "{group}\RAW 批次轉檔工具";  Filename: "{app}\RAW轉檔工具.exe"
Name: "{group}\解除安裝";           Filename: "{uninstallexe}"
; 桌面捷徑（可選）
Name: "{autodesktop}\RAW 批次轉檔工具"; Filename: "{app}\RAW轉檔工具.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\RAW轉檔工具.exe"; Description: "立即啟動 RAW 批次轉檔工具"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
