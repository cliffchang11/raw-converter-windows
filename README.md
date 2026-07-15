# RAW 批次轉檔工具 - Windows 版建置說明

## 📋 系統需求（建置電腦）

- **Windows 10 / 11** (64位元)
- **Python 3.10+**（安裝時須勾選 "Add Python to PATH"）
- **網路連線**（用於下載 ExifTool 與 Python 套件）
- **Inno Setup 6**（可選，用於製作安裝程式）

---

## 🚀 快速建置步驟

### 步驟 1：複製資料夾至 Windows 電腦

將整個 `windows_app/` 資料夾複製至 Windows 電腦任意位置，例如：
```
C:\Users\Cliff\Desktop\windows_app\
```

### 步驟 2：雙擊執行 `build.bat`

`build.bat` 會自動完成以下工作：
1. 檢查 Python 環境
2. 安裝 `customtkinter`、`pyinstaller` 套件
3. 自動下載 `exiftool.exe` 並放入 `assets/`
4. 使用 PyInstaller 打包成 `RAW轉檔工具.exe`

建置完成後，執行檔位於：
```
windows_app\dist\RAW轉檔工具.exe
windows_app\RAW轉檔工具.exe  （同一份，複製到根目錄方便取用）
```

### 步驟 3（可選）：製作安裝程式

如需產出標準的 Windows 安裝精靈（`.exe` Setup 檔）：

1. 前往 https://jrsoftware.org/isdl.php 下載並安裝 **Inno Setup 6**
2. 用 Inno Setup 開啟 `installer.iss`
3. 按下 `Build > Compile`
4. 安裝程式將輸出至 `installer_output\RAW轉檔工具_Setup_v1.0.exe`

---

## 📁 目錄結構

```
windows_app/
├── raw_converter.py          ← 主程式原始碼
├── build.bat                 ← 一鍵建置腳本
├── download_exiftool.bat     ← ExifTool 下載工具
├── installer.iss             ← Inno Setup 安裝程式腳本
├── README.md                 ← 本說明文件
└── assets/
    └── exiftool.exe          ← (build.bat 自動下載)
```

---

## 🎯 功能說明

| 功能 | 說明 |
|------|------|
| 來源資料夾選取 | 支援遞迴掃描子資料夾 |
| 輸出資料夾選取 | 留空時自動建立 `converted_images` |
| 輸出格式 | JPG（高相容）/ HEIC（Apple 裝置）|
| 以拍攝時間命名 | 例：`20260502_144804_IMG_1888.jpg` |
| 批次進度顯示 | 即時進度條、逐檔日誌、統計報告 |
| 停止功能 | 可隨時中斷，已完成的照片不受影響 |

## 🔧 支援的 RAW 格式

`.NEF` `.CR2` `.CR3` `.ARW` `.DNG` `.ORF` `.RAF` `.RW2` `.PEF` `.SR2`

---

## ❓ 常見問題

**Q：`exiftool.exe` 下載失敗怎麼辦？**
> 請前往 https://exiftool.org 手動下載 Windows Executable 版本，
> 將 `exiftool(-k).exe` 重新命名為 `exiftool.exe`，放入 `assets/` 資料夾。

**Q：打包後的 .exe 被防毒軟體偵測為威脅？**
> PyInstaller 打包的程式有時會觸發誤報，請將程式加入防毒軟體的白名單，
> 或使用程式碼簽章（需購買程式碼簽章憑證）。

**Q：HEIC 格式無法輸出？**
> HEIC 輸出目前需要系統安裝 `heif-enc`，一般 Windows 環境不支援。
> 建議使用 JPG 格式。
