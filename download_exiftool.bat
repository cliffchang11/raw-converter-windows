@echo off
chcp 65001 >nul
echo 正在下載 ExifTool Windows 版本...

:: 建立 assets 資料夾
if not exist "assets" mkdir assets

:: 使用 PowerShell 下載 ExifTool（Windows 10/11 內建）
powershell -Command ^
    "Write-Host '正在獲取最新 ExifTool 版本資訊...';" ^
    "try { " ^
    "  $html = Invoke-WebRequest -Uri 'https://exiftool.org/' -UseBasicParsing -TimeoutSec 15;" ^
    "  $link = ($html.Links | Where-Object { $_.href -like 'exiftool-*_64.zip' } | Select-Object -First 1).href;" ^
    "  if (-not $link) { $link = 'exiftool-13.59_64.zip' }" ^
    "} catch { " ^
    "  $link = 'exiftool-13.59_64.zip' " ^
    "};" ^
    "$url = 'https://exiftool.org/' + $link;" ^
    "$zip = 'assets\exiftool_tmp.zip';" ^
    "Write-Host '下載中...' $url;" ^
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
