@echo off
chcp 65001 >nul
echo 正在下載 ExifTool Windows 版本...

:: 建立 assets 資料夾
if not exist "assets" mkdir assets

:: 使用 PowerShell 下載 ExifTool（Windows 10/11 內建）
powershell -Command ^
    "$url='https://exiftool.org/exiftool-13.05_64.zip';" ^
    "$zip='assets\exiftool_tmp.zip';" ^
    "Write-Host '下載中...';" ^
    "Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing;" ^
    "Write-Host '解壓縮中...';" ^
    "Expand-Archive -Path $zip -DestinationPath 'assets\exiftool_tmp' -Force;" ^
    "Get-ChildItem 'assets\exiftool_tmp' -Recurse -Filter 'exiftool(-k).exe' | " ^
    "  Select-Object -First 1 | Copy-Item -Destination 'assets\exiftool.exe';" ^
    "Remove-Item $zip -Force;" ^
    "Remove-Item 'assets\exiftool_tmp' -Recurse -Force;" ^
    "Write-Host 'ExifTool 下載完成！'"

if exist "assets\exiftool.exe" (
    echo ✅ exiftool.exe 已成功放入 assets\ 資料夾！
) else (
    echo ❌ 下載失敗，請手動前往以下網址下載：
    echo    https://exiftool.org
    echo    下載 Windows Executable 版本，將 exiftool(-k).exe 重新命名為 exiftool.exe
    echo    並放入 assets\ 資料夾中。
    exit /b 1
)
