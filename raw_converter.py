"""
RAW 批次轉檔工具 - Windows 桌面版
使用 ExifTool 提取內嵌預覽圖，無需 rawpy 等複雜依賴
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import subprocess
import sys
import time
from pathlib import Path

# ── 外觀設定 ──────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "1.0.0"
RAW_EXTENSIONS = {'.nef', '.cr2', '.cr3', '.arw', '.dng', '.orf', '.raf', '.rw2', '.pef', '.sr2'}


def get_exiftool_path() -> Path:
    """取得 exiftool.exe 路徑，支援 PyInstaller 打包模式"""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / 'assets' / 'exiftool.exe'


def get_raw_files(source_dir: Path) -> list:
    """遞迴掃描資料夾中所有支援的 RAW 格式檔案"""
    files = []
    for ext in RAW_EXTENSIONS:
        files.extend(source_dir.rglob(f'*{ext}'))
        files.extend(source_dir.rglob(f'*{ext.upper()}'))
    return sorted(set(files), key=lambda f: f.stat().st_mtime)


def get_time_prefix(raw_path: Path, exiftool: Path) -> str:
    """使用 ExifTool 提取拍攝時間作為檔名前綴"""
    try:
        cmd = [str(exiftool), '-charset', 'filename=utf8', '-s3', '-DateTimeOriginal', '-@', '-']
        res = subprocess.run(cmd, input=f"{raw_path}\n".encode('utf-8'),
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                             timeout=10,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        dt = res.stdout.decode('utf-8', errors='ignore').strip()
        if dt:
            clean = ''.join(c for c in dt if c.isdigit())
            if len(clean) >= 14:
                return f"{clean[:8]}_{clean[8:14]}_"
    except Exception:
        pass
    return ""


def format_size(size_bytes: float) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def convert_single_raw(raw_path: Path, dest_path: Path, exiftool: Path) -> tuple:
    """
    轉換單張 RAW 照片（preview 模式）
    回傳 (success: bool, message: str)
    """
    no_window = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    temp_jpg = dest_path.with_suffix('.temp.jpg')

    try:
        # 步驟 1：嘗試 JpgFromRaw（Nikon、Sony 常用）
        cmd = [str(exiftool), '-charset', 'filename=utf8', '-b', '-JpgFromRaw', '-@', '-']
        res = subprocess.run(cmd, input=f"{raw_path}\n".encode('utf-8'),
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
                             creationflags=no_window)
        if res.returncode == 0 and len(res.stdout) > 50 * 1024:
            with open(temp_jpg, 'wb') as f:
                f.write(res.stdout)

        # 步驟 2：嘗試 PreviewImage（Canon CR3、DNG 等）
        if not temp_jpg.exists() or temp_jpg.stat().st_size < 50 * 1024:
            cmd = [str(exiftool), '-charset', 'filename=utf8', '-b', '-PreviewImage', '-@', '-']
            res = subprocess.run(cmd, input=f"{raw_path}\n".encode('utf-8'),
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
                                 creationflags=no_window)
            if res.returncode == 0 and len(res.stdout) > 50 * 1024:
                with open(temp_jpg, 'wb') as f:
                    f.write(res.stdout)

        # 步驟 3：最後嘗試 ThumbnailImage
        if not temp_jpg.exists() or temp_jpg.stat().st_size < 10 * 1024:
            cmd = [str(exiftool), '-charset', 'filename=utf8', '-b', '-ThumbnailImage', '-@', '-']
            res = subprocess.run(cmd, input=f"{raw_path}\n".encode('utf-8'),
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30,
                                 creationflags=no_window)
            if res.returncode == 0 and len(res.stdout) > 10 * 1024:
                with open(temp_jpg, 'wb') as f:
                    f.write(res.stdout)

        if not temp_jpg.exists() or temp_jpg.stat().st_size < 10 * 1024:
            if temp_jpg.exists():
                temp_jpg.unlink()
            return False, "無法提取內嵌預覽圖（此 RAW 格式可能不含嵌入 JPEG）"

        # 步驟 4：移動至目標路徑
        if dest_path.exists():
            dest_path.unlink()
        temp_jpg.rename(dest_path)

        # 步驟 5：複製原始 EXIF 至輸出檔案
        cmd = [str(exiftool), '-charset', 'filename=utf8', '-@', '-']
        args = f"-overwrite_original\n-TagsFromFile\n{raw_path}\n-all:all>all:all\n-unsafe\n{dest_path}\n"
        subprocess.run(cmd, input=args.encode('utf-8'),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=30, creationflags=no_window)

        return True, "成功"

    except Exception as e:
        if temp_jpg.exists():
            temp_jpg.unlink()
        return False, str(e)


# ══════════════════════════════════════════════════════════
#  主視窗
# ══════════════════════════════════════════════════════════

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"📷  RAW 批次轉檔工具  v{APP_VERSION}")
        self.geometry("720x740")
        self.minsize(660, 680)

        self.exiftool = get_exiftool_path()
        self.source_dir = tk.StringVar()
        self.dest_dir   = tk.StringVar()
        self.use_prefix = tk.BooleanVar(value=True)
        self.out_format = tk.StringVar(value='jpg')

        self.raw_files      = []
        self.is_converting  = False
        self.stop_requested = False

        self._build_ui()
        self._check_exiftool()

    # ── ExifTool 檢查 ──────────────────────────────────────
    def _check_exiftool(self):
        if not self.exiftool.exists():
            self._log(f"⚠️  找不到 exiftool.exe！", 'warn')
            self._log(f"   預期路徑：{self.exiftool}", 'warn')
            self._log("   請執行 download_exiftool.bat 下載，或手動放入 assets/ 資料夾。", 'warn')
        else:
            self._log(f"✅  ExifTool 就緒：{self.exiftool}", 'success')

    # ── UI 建構 ────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=20)

        # 標題
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill='x', **pad, pady=(18, 4))
        ctk.CTkLabel(hdr, text="📷  RAW 批次轉檔工具",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side='left')
        ctk.CTkLabel(hdr, text=f"v{APP_VERSION}  ·  ExifTool Preview Mode",
                     font=ctk.CTkFont(size=11), text_color="gray55").pack(side='left', padx=(10, 0), pady=(6, 0))

        # ── 資料夾選取 ────────────────────────────────────
        ff = ctk.CTkFrame(self)
        ff.pack(fill='x', **pad, pady=6)
        ff.columnconfigure(1, weight=1)

        ctk.CTkLabel(ff, text="來源資料夾", width=90, anchor='w').grid(row=0, column=0, padx=(14, 8), pady=10, sticky='w')
        ctk.CTkEntry(ff, textvariable=self.source_dir,
                     placeholder_text="選擇包含 RAW 照片的資料夾...").grid(row=0, column=1, padx=(0, 8), pady=10, sticky='ew')
        ctk.CTkButton(ff, text="選擇", width=60, command=self._browse_source).grid(row=0, column=2, padx=(0, 12), pady=10)

        ctk.CTkLabel(ff, text="輸出資料夾", width=90, anchor='w').grid(row=1, column=0, padx=(14, 8), pady=(0, 10), sticky='w')
        ctk.CTkEntry(ff, textvariable=self.dest_dir,
                     placeholder_text="留空則自動建立 converted_images 子資料夾").grid(row=1, column=1, padx=(0, 8), pady=(0, 10), sticky='ew')
        ctk.CTkButton(ff, text="選擇", width=60, command=self._browse_dest).grid(row=1, column=2, padx=(0, 12), pady=(0, 10))

        # ── 設定選項 ──────────────────────────────────────
        of = ctk.CTkFrame(self)
        of.pack(fill='x', **pad, pady=6)

        row1 = ctk.CTkFrame(of, fg_color="transparent")
        row1.pack(fill='x', padx=14, pady=(12, 6))
        ctk.CTkLabel(row1, text="輸出格式：", font=ctk.CTkFont(weight="bold")).pack(side='left')
        ctk.CTkRadioButton(row1, text="JPG (高相容，Windows / Android)", variable=self.out_format, value='jpg').pack(side='left', padx=(10, 24))
        ctk.CTkRadioButton(row1, text="HEIC (Apple 裝置)", variable=self.out_format, value='heic').pack(side='left')

        row2 = ctk.CTkFrame(of, fg_color="transparent")
        row2.pack(fill='x', padx=14, pady=(0, 12))
        ctk.CTkCheckBox(row2, text="以拍攝時間重新命名檔案（例：20260502_144804_IMG_1888.jpg）",
                        variable=self.use_prefix).pack(side='left')

        # ── 操作按鈕 ──────────────────────────────────────
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill='x', **pad, pady=6)
        bf.columnconfigure(0, weight=1)
        bf.columnconfigure(1, weight=1)

        self.scan_btn = ctk.CTkButton(
            bf, text="🔍  掃描 RAW 檔案", height=44,
            font=ctk.CTkFont(size=14),
            fg_color="#374151", hover_color="#4B5563",
            command=self._do_scan)
        self.scan_btn.grid(row=0, column=0, padx=(0, 6), sticky='ew')

        self.start_btn = ctk.CTkButton(
            bf, text="▶  開始轉換", height=44,
            font=ctk.CTkFont(size=14, weight="bold"),
            state='disabled', command=self._do_start)
        self.start_btn.grid(row=0, column=1, padx=(6, 0), sticky='ew')

        self.stop_btn = ctk.CTkButton(
            bf, text="■  停止", height=44,
            font=ctk.CTkFont(size=14),
            fg_color="#991B1B", hover_color="#7F1D1D",
            state='disabled', command=self._do_stop)

        # ── 進度條 ────────────────────────────────────────
        pf = ctk.CTkFrame(self)
        pf.pack(fill='x', **pad, pady=6)

        pt = ctk.CTkFrame(pf, fg_color="transparent")
        pt.pack(fill='x', padx=14, pady=(10, 4))
        self.prog_label = ctk.CTkLabel(pt, text="等待開始...", anchor='w')
        self.prog_label.pack(side='left')
        self.prog_pct = ctk.CTkLabel(pt, text="0%", anchor='e', font=ctk.CTkFont(weight="bold"))
        self.prog_pct.pack(side='right')

        self.prog_bar = ctk.CTkProgressBar(pf, height=14, corner_radius=7)
        self.prog_bar.pack(fill='x', padx=14, pady=(0, 12))
        self.prog_bar.set(0)

        # ── 統計欄 ────────────────────────────────────────
        sf = ctk.CTkFrame(self)
        sf.pack(fill='x', **pad, pady=6)
        for i in range(4):
            sf.columnconfigure(i, weight=1)

        self.stat_total   = self._stat_box(sf, "掃描總數",   "0 張",   0)
        self.stat_success = self._stat_box(sf, "✅ 成功",    "0 張",   1, "#10b981")
        self.stat_fail    = self._stat_box(sf, "❌ 失敗",    "0 張",   2, "#ef4444")
        self.stat_saved   = self._stat_box(sf, "💾 節省空間", "0.0 MB", 3, "#3b82f6")

        # ── 日誌 ──────────────────────────────────────────
        lf = ctk.CTkFrame(self)
        lf.pack(fill='both', expand=True, **pad, pady=(6, 18))

        ctk.CTkLabel(lf, text="轉換日誌", anchor='w',
                     font=ctk.CTkFont(weight="bold")).pack(anchor='w', padx=14, pady=(10, 4))

        self.log = ctk.CTkTextbox(lf, font=ctk.CTkFont(family="Consolas", size=12), state='disabled')
        self.log.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        self.log.tag_config('success', foreground='#10b981')
        self.log.tag_config('error',   foreground='#ef4444')
        self.log.tag_config('info',    foreground='#60a5fa')
        self.log.tag_config('warn',    foreground='#f59e0b')

    def _stat_box(self, parent, label, value, col, color=None):
        f = ctk.CTkFrame(parent, fg_color=("#1e2530", "#1e2530"), corner_radius=8)
        f.grid(row=0, column=col, padx=6, pady=10, sticky='ew')
        ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=11), text_color="gray60").pack(pady=(8, 2))
        lbl = ctk.CTkLabel(f, text=value, font=ctk.CTkFont(size=16, weight="bold"),
                           text_color=color or "white")
        lbl.pack(pady=(0, 8))
        return lbl

    # ── 瀏覽目錄 ──────────────────────────────────────────
    def _browse_source(self):
        p = filedialog.askdirectory(title="選擇來源資料夾")
        if p:
            self.source_dir.set(p)
            self._do_scan()

    def _browse_dest(self):
        p = filedialog.askdirectory(title="選擇輸出資料夾")
        if p:
            self.dest_dir.set(p)

    # ── 日誌輸出 ──────────────────────────────────────────
    def _log(self, msg: str, tag: str = None):
        def _w():
            self.log.configure(state='normal')
            self.log.insert('end', msg + '\n', tag or '')
            self.log.see('end')
            self.log.configure(state='disabled')
        self.after(0, _w)

    # ── 掃描 ──────────────────────────────────────────────
    def _do_scan(self):
        src = self.source_dir.get().strip()
        if not src:
            self._log("⚠️  請先選擇來源資料夾！", 'warn')
            return
        p = Path(src)
        if not p.exists():
            self._log(f"❌  路徑不存在：{src}", 'error')
            return

        self._log(f"\n🔍  掃描中：{src} ...", 'info')
        self.raw_files = get_raw_files(p)
        n = len(self.raw_files)
        self.stat_total.configure(text=f"{n} 張")

        if n == 0:
            self._log("⚠️  此資料夾沒有支援的 RAW 照片。", 'warn')
            self.start_btn.configure(state='disabled', text="▶  開始轉換")
        else:
            sz = sum(f.stat().st_size for f in self.raw_files)
            self._log(f"✅  找到 {n} 張 RAW 照片，共 {format_size(sz)}", 'success')
            self.start_btn.configure(state='normal', text=f"▶  開始轉換 ({n} 張)")

    # ── 開始轉換 ──────────────────────────────────────────
    def _do_start(self):
        if not self.raw_files:
            self._log("⚠️  請先掃描 RAW 檔案。", 'warn')
            return
        if not self.exiftool.exists():
            messagebox.showerror("錯誤", f"找不到 exiftool.exe！\n路徑：{self.exiftool}")
            return

        src  = Path(self.source_dir.get().strip())
        dst  = self.dest_dir.get().strip()
        dest = Path(dst) if dst else src / 'converted_images'
        dest.mkdir(parents=True, exist_ok=True)

        self.is_converting  = True
        self.stop_requested = False

        self.scan_btn.configure(state='disabled')
        self.start_btn.configure(state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=(6, 0), sticky='ew')
        self.stop_btn.configure(state='normal')

        self.stat_success.configure(text="0 張")
        self.stat_fail.configure(text="0 張")
        self.stat_saved.configure(text="0.0 MB")
        self.prog_bar.set(0)
        self.prog_pct.configure(text="0%")
        self.prog_label.configure(text="準備中...")

        self._log(f"\n{'─'*52}", 'info')
        self._log(f"🚀  開始轉換 {len(self.raw_files)} 張 RAW 照片", 'info')
        self._log(f"📁  輸出目錄：{dest}", 'info')
        self._log(f"{'─'*52}", 'info')

        threading.Thread(target=self._worker, args=(src, dest), daemon=True).start()

    def _do_stop(self):
        self.stop_requested = True
        self.stop_btn.configure(state='disabled', text="■  正在停止...")
        self._log("⏹️  使用者請求停止...", 'warn')

    # ── 背景轉換執行緒 ────────────────────────────────────
    def _worker(self, src: Path, dest: Path):
        files   = self.raw_files
        total   = len(files)
        prefix  = self.use_prefix.get()
        fmt     = self.out_format.get()
        tool    = self.exiftool
        ok_n = fail_n = saved = 0
        t0 = time.time()

        for idx, raw in enumerate(files, 1):
            if self.stop_requested:
                self._log("⏹️  已停止。", 'warn')
                break

            pct = (idx - 1) / total
            name = raw.name
            self.after(0, lambda p=pct, i=idx, n=name: (
                self.prog_bar.set(p),
                self.prog_pct.configure(text=f"{int(p*100)}%"),
                self.prog_label.configure(text=f"({i}/{total})  {n}")
            ))

            time_pfx = get_time_prefix(raw, tool) if prefix else ""
            new_name  = f"{time_pfx}{raw.stem}.jpg"
            try:
                rel = raw.relative_to(src)
            except ValueError:
                rel = Path(raw.name)
            out = dest / rel.with_name(new_name)
            out.parent.mkdir(parents=True, exist_ok=True)

            raw_sz = raw.stat().st_size
            ok, msg = convert_single_raw(raw, out, tool)

            if ok:
                ok_n  += 1
                saved += max(0, raw_sz - (out.stat().st_size if out.exists() else 0))
                self._log(f"  ✅  {new_name}", 'success')
            else:
                fail_n += 1
                self._log(f"  ❌  {raw.name}  →  {msg}", 'error')

            ok_n_c, fail_n_c, saved_c = ok_n, fail_n, saved
            self.after(0, lambda s=ok_n_c, f=fail_n_c, sv=saved_c: (
                self.stat_success.configure(text=f"{s} 張"),
                self.stat_fail.configure(text=f"{f} 張"),
                self.stat_saved.configure(text=format_size(sv))
            ))

        elapsed = time.time() - t0
        self.after(0, lambda: self._finish(ok_n, fail_n, saved, elapsed, dest))

    def _finish(self, ok, fail, saved, elapsed, dest):
        self.is_converting = False
        self.prog_bar.set(1.0)
        self.prog_pct.configure(text="100%")
        self.prog_label.configure(text="完成！")

        self._log(f"\n{'═'*52}", 'info')
        tag = 'success' if fail == 0 else 'warn'
        self._log(f"🎉  轉換完成！成功 {ok} 張 / 失敗 {fail} 張 / 耗時 {elapsed:.1f} 秒", tag)
        self._log(f"💾  節省空間：{format_size(saved)}", 'info')
        self._log(f"📁  輸出位置：{dest}", 'info')
        self._log(f"{'═'*52}", 'info')

        self.scan_btn.configure(state='normal')
        self.start_btn.configure(state='normal', text=f"▶  再次轉換 ({len(self.raw_files)} 張)")
        self.stop_btn.grid_forget()
        self.stop_btn.configure(state='normal', text="■  停止")

        if ok > 0 and fail == 0:
            messagebox.showinfo("✅ 轉換完成",
                                f"成功轉換 {ok} 張照片！\n節省空間：{format_size(saved)}\n\n輸出位置：\n{dest}")
        elif fail > 0:
            messagebox.showwarning("⚠️ 部分失敗",
                                   f"成功 {ok} 張 / 失敗 {fail} 張\n\n請查看日誌了解失敗原因。")


if __name__ == '__main__':
    app = App()
    app.mainloop()
