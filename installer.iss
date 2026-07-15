[Setup]
AppName=RAW Converter
AppVersion=1.0.0
AppPublisher=Cliff Chang
AppPublisherURL=https://github.com/cliffchang11/raw-converter-windows
AppMutex=RAW_Converter_Mutex_Unique_998877
DefaultDirName={autopf}\RAW Converter
DefaultGroupName=RAW Converter
OutputBaseFilename=RAW_Converter_Setup_v1.0
OutputDir=installer_output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\RAW_Converter.exe

[Tasks]
Name: "desktopicon"; Description: "在桌面建立捷徑"; GroupDescription: "其他工作"

[Files]
Source: "dist\RAW_Converter.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\RAW Converter";  Filename: "{app}\RAW_Converter.exe"
Name: "{group}\解除安裝";        Filename: "{uninstallexe}"
Name: "{autodesktop}\RAW Converter"; Filename: "{app}\RAW_Converter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\RAW_Converter.exe"; Description: "立即啟動 RAW 批次轉檔工具"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
