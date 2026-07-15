@echo off
chcp 65001 >nul
echo =====================================================
echo   RAW 批次轉檔工具 - Windows 全自動建置腳本 v1.0
echo =====================================================
echo.

:: ── 步驟 1：檢查 Python ─────────────────────────────
echo [1/6] 檢查 Python 環境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [錯誤] 找不到 Python！
    echo 請至 https://www.python.org/downloads/ 下載安裝 Python 3.10+
    echo 安裝時請勾選 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>&1') do echo    %%v 已就緒

:: ── 步驟 2：安裝 Python 套件 ────────────────────────
echo [2/6] 安裝依賴套件 (customtkinter, pyinstaller)...
pip install customtkinter pyinstaller pillow --quiet --upgrade
if errorlevel 1 (
    echo [錯誤] 套件安裝失敗，請確認網路連線。
    pause
    exit /b 1
)
echo    套件安裝完成

:: ── 步驟 3：下載 ExifTool ───────────────────────────
echo [3/6] 檢查 ExifTool...
if not exist "assets" mkdir assets
if not exist "assets\exiftool.exe" (
    echo    找不到 exiftool.exe，正在下載...
    call download_exiftool.bat
    if errorlevel 1 (
        echo [錯誤] ExifTool 下載失敗，請手動執行 download_exiftool.bat
        pause
        exit /b 1
    )
) else (
    echo    exiftool.exe 已存在，略過下載
)

:: ── 步驟 4：PyInstaller 打包 ────────────────────────
echo [4/6] 使用 PyInstaller 打包 .exe（約需 1-3 分鐘）...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "RAW轉檔工具" ^
    --add-data "assets/exiftool.exe;assets" ^
    --clean ^
    --noconfirm ^
    raw_converter.py

if errorlevel 1 (
    echo [錯誤] PyInstaller 打包失敗！
    pause
    exit /b 1
)
echo    PyInstaller 打包完成

:: ── 步驟 5：安裝 Inno Setup（若尚未安裝）──────────
echo [5/6] 檢查 Inno Setup 6...
set "ISCC="
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
    set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
)

if not defined ISCC (
    echo    Inno Setup 未安裝，正在自動下載與安裝（需要管理員權限）...
    powershell -Command ^
        "Invoke-WebRequest -Uri 'https://jrsoftware.org/download.php/is.exe' -OutFile 'innosetup_installer.exe' -UseBasicParsing; Write-Host '下載完成，正在靜默安裝...'"
    if errorlevel 1 (
        echo [錯誤] Inno Setup 下載失敗，請前往 https://jrsoftware.org/isdl.php 手動安裝
        pause
        exit /b 1
    )
    innosetup_installer.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
    del /f /q innosetup_installer.exe >nul 2>&1
    :: 安裝後重新確認路徑
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    )
    if exist "C:\Program Files\Inno Setup 6\ISCC.exe" (
        set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
    )
)

if not defined ISCC (
    echo [警告] 無法找到 Inno Setup，跳過安裝程式製作。
    echo    僅輸出單一執行檔：dist\RAW轉檔工具.exe
    goto :only_exe
)
echo    Inno Setup 已就緒：%ISCC%

:: ── 步驟 6：編譯 Inno Setup 安裝程式 ───────────────
echo [6/6] 編譯 Windows 安裝程式...
if not exist "installer_output" mkdir installer_output
"%ISCC%" installer.iss
if errorlevel 1 (
    echo [錯誤] Inno Setup 編譯失敗！請確認 installer.iss 設定正確。
    pause
    exit /b 1
)

echo.
echo =====================================================
echo   ✅ 全部完成！以下是您的輸出檔案：
echo.
if exist "installer_output\RAW轉檔工具_Setup_v1.0.exe" (
    echo   ^📦 安裝程式：
    echo      %CD%\installer_output\RAW轉檔工具_Setup_v1.0.exe
    echo.
)
echo   ^💾 單一執行檔：
echo      %CD%\dist\RAW轉檔工具.exe
echo =====================================================
echo.
pause
exit /b 0

:only_exe
echo.
echo =====================================================
echo   ✅ 完成！（僅單一執行檔，無安裝程式）
echo.
echo   ^💾 執行檔位置：
echo      %CD%\dist\RAW轉檔工具.exe
echo =====================================================
echo.
pause
