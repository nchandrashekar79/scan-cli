"""Graphical launcher for the Disk Storage Analyzer using tkinter.

Each scan opens in a new tab within the same window.
"""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional


class DiskAnalyzerGUI:
    """A tkinter GUI with menu bar — each scan result opens in a new tab."""

    # Color palette (dark theme)
    BG = "#0f172a"
    SURFACE = "#1e293b"
    SURFACE2 = "#334155"
    BORDER = "#475569"
    TEXT = "#f1f5f9"
    TEXT_MUTED = "#94a3b8"
    ACCENT = "#3b82f6"
    ACCENT_HOVER = "#2563eb"

    def __init__(self, initial_path: Optional[str] = None) -> None:
        self._initial_path = initial_path
        self._tab_counter = 0
        self._scanning = False

        self.root = tk.Tk()
        self.root.title("Disk Storage Analyzer")
        self.root.geometry("860x580")
        self.root.minsize(700, 480)
        self.root.configure(bg=self.BG)

        # Center on screen
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"+{x}+{y}")

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # ── Menu bar ──
        menubar = tk.Menu(self.root, bg=self.SURFACE2, fg=self.TEXT,
                          activebackground=self.ACCENT, activeforeground="#ffffff",
                          font=("Segoe UI", 10))
        scan_menu = tk.Menu(menubar, tearoff=0, bg=self.SURFACE, fg=self.TEXT,
                            activebackground=self.ACCENT, activeforeground="#ffffff",
                            font=("Segoe UI", 10))
        scan_menu.add_command(label="📂  New Scan...", command=self._start_new_scan,
                              accelerator="Ctrl+N")
        scan_menu.add_separator()
        scan_menu.add_command(label="✕  Close Current Tab", command=self._close_current_tab,
                              accelerator="Ctrl+W")
        scan_menu.add_command(label="🚪  Exit", command=self.root.quit,
                              accelerator="Ctrl+Q")
        menubar.add_cascade(label="Scan", menu=scan_menu)
        self.root.config(menu=menubar)

        # Keyboard shortcuts
        self.root.bind_all("<Control-n>", lambda _e: self._start_new_scan())
        self.root.bind_all("<Control-w>", lambda _e: self._close_current_tab())
        self.root.bind_all("<Control-q>", lambda _e: self.root.quit())

        # ── Main notebook (one tab per scan) ──
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=self.BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=self.SURFACE2, foreground=self.TEXT,
                        padding=[14, 6], font=("Segoe UI", 10))
        style.map("TNotebook.Tab", background=[("selected", self.ACCENT)],
                  foreground=[("selected", "#ffffff")])

        self._notebook = ttk.Notebook(self.root)
        self._notebook.grid(row=0, column=0, sticky="nsew", padx=8, pady=(4, 8))

        # ── Welcome tab ──
        self._add_welcome_tab()

    def _add_welcome_tab(self) -> None:
        """Show a welcome screen as the first tab."""
        frame = tk.Frame(self._notebook, bg=self.BG)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        center = tk.Frame(frame, bg=self.BG)
        center.grid(row=0, column=0)

        tk.Label(center, text="💾", font=("Segoe UI", 64), bg=self.BG).pack(pady=(40, 10))
        tk.Label(center, text="Disk Storage Analyzer",
                 font=("Segoe UI", 26, "bold"), bg=self.BG, fg=self.TEXT).pack()
        tk.Label(center, text="Scan any folder to visualise what's consuming your storage",
                 font=("Segoe UI", 12), bg=self.BG, fg=self.TEXT_MUTED).pack(pady=(4, 30))

        new_btn = tk.Label(center, text="📂  New Scan",
                           font=("Segoe UI", 14, "bold"), bg=self.ACCENT, fg="#ffffff",
                           cursor="hand2", padx=36, pady=12)
        new_btn.pack()
        new_btn.bind("<Button-1>", lambda _e: self._start_new_scan())
        new_btn.bind("<Enter>", lambda _e: new_btn.configure(bg=self.ACCENT_HOVER))
        new_btn.bind("<Leave>", lambda _e: new_btn.configure(bg=self.ACCENT))

        hint = tk.Label(center, text="or press  Ctrl+N",
                        font=("Segoe UI", 9), bg=self.BG, fg=self.TEXT_MUTED)
        hint.pack(pady=(12, 0))

        self._notebook.add(frame, text="🏠  Home")
        self._notebook.select(len(self._notebook.tabs()) - 1)

    # ── Scan flow ───────────────────────────────────────────────────

    def _start_new_scan(self) -> None:
        """Open a folder dialog and begin scanning in a new tab."""
        if self._scanning:
            messagebox.showinfo("Scan in Progress",
                                "Please wait for the current scan to finish.")
            return

        folder = filedialog.askdirectory(
            title="Select a folder to scan",
            initialdir=self._initial_path or "C:\\",
        )
        if not folder:
            return

        self._scanning = True
        self._tab_counter += 1
        tab_id = self._tab_counter
        short_name = os.path.basename(folder) or folder

        # ── Create a loading tab ──
        load_frame = tk.Frame(self._notebook, bg=self.BG)
        load_frame.columnconfigure(0, weight=1)
        load_frame.rowconfigure(0, weight=1)

        center = tk.Frame(load_frame, bg=self.BG)
        center.grid(row=0, column=0)

        tk.Label(center, text="⏳", font=("Segoe UI", 48), bg=self.BG).pack(pady=(40, 10))
        tk.Label(center, text=f"Scanning {short_name}…",
                 font=("Segoe UI", 16, "bold"), bg=self.BG, fg=self.TEXT).pack()
        self._scan_status_var = tk.StringVar(value="Starting scan…")
        tk.Label(center, textvariable=self._scan_status_var,
                 font=("Segoe UI", 11), bg=self.BG, fg=self.TEXT_MUTED).pack(pady=(8, 0))

        progress = ttk.Progressbar(load_frame, mode="indeterminate", length=400)
        progress.grid(row=1, column=0, sticky="ew", padx=100, pady=(0, 40))
        progress.start(10)

        self._notebook.add(load_frame, text=f"⏳  {short_name[:20]}")
        self._notebook.select(len(self._notebook.tabs()) - 1)

        # ── Run scan in background ──
        t = threading.Thread(
            target=self._run_scan,
            args=(folder, tab_id, short_name, load_frame, progress),
            daemon=True,
        )
        t.start()

    def _run_scan(self, path: str, tab_id: int, short_name: str,
                  load_frame: tk.Frame, progress: ttk.Progressbar) -> None:
        """Run the full scan pipeline (background thread)."""
        try:
            from disk_analyzer.aggregator import aggregate
            from disk_analyzer.config import Config
            from disk_analyzer.scanner import load_cache, save_cache, scan_files

            import time

            config = Config()
            scan_path = os.path.abspath(path)

            # ── Check cache (only reuses cache if scan_path matches) ──
            self._schedule_status_text(f"Loading cache for {short_name}…")
            files = load_cache(config, scan_path=scan_path)
            if files is not None:
                self._schedule_status_text(
                    f"✅ Loaded {len(files):,} files from cache — aggregating…"
                )
            else:
                self._schedule_status_text(f"📡 Scanning {short_name}…")

                def _progress(found: int, current: str) -> None:
                    self._schedule_status_text(
                        f"📁  {found:,} files found  —  {os.path.basename(current) or current}"
                    )

                scan_start = time.time()
                files = scan_files(config, scan_path, progress_callback=_progress)
                elapsed = time.time() - scan_start
                self._schedule_status_text(
                    f"✅ Scanned {len(files):,} files in {elapsed:.1f}s — caching…"
                )
                save_cache(config, files, scan_path)

            # ── Aggregate ──
            self._schedule_status_text("📊 Aggregating data…")
            data = aggregate(config, files)

            # ── Replace loading tab with results tab ──
            self._schedule_replace_tab(tab_id, short_name, data, scan_path,
                                       load_frame, progress)

        except Exception as exc:
            self._schedule_show_error(load_frame, progress, str(exc))

    def _schedule_status_text(self, msg: str) -> None:
        """Update the scanning status label from any thread."""
        def _update() -> None:
            try:
                self._scan_status_var.set(msg)
            except tk.TclError:
                pass
        self.root.after(0, _update)

    def _schedule_replace_tab(self, tab_id: int, short_name: str, data: dict,
                              scan_path: str, load_frame: tk.Frame,
                              progress: ttk.Progressbar) -> None:
        """Replace the loading tab with the results view (main thread)."""

        def _replace() -> None:
            try:
                progress.stop()
                progress.destroy()
                tab_idx = self._notebook.index(load_frame)
                self._notebook.forget(tab_idx)
            except tk.TclError:
                pass

            # ── Build the results tab content ──
            self._build_result_tab(short_name, data, scan_path)
            self._scanning = False

        self.root.after(0, _replace)

    def _schedule_show_error(self, load_frame: tk.Frame, progress: ttk.Progressbar,
                             error: str) -> None:
        """Show error in place of the loading tab (main thread)."""

        def _show() -> None:
            try:
                progress.stop()
                progress.destroy()
                tab_idx = self._notebook.index(load_frame)
                self._notebook.forget(tab_idx)
            except tk.TclError:
                pass

            messagebox.showerror("Scan Error", error)
            self._scanning = False

        self.root.after(0, _show)

    # ── Results tab builder ─────────────────────────────────────────

    def _build_result_tab(self, short_name: str, data: dict,
                          scan_path: str) -> None:
        """Create a new tab with full scan results."""
        s = data["summary"]
        scan_info = data["scan_info"]
        folders = data.get("folders", [])
        files = data.get("files", [])

        container = tk.Frame(self._notebook, bg=self.BG)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        # ── Title row ──
        tk.Label(container, text="✅  Scan Complete",
                 font=("Segoe UI", 18, "bold"), bg=self.BG,
                 fg=self.TEXT).grid(row=0, column=0, pady=(14, 2))

        tk.Label(container, text=scan_path, font=("Consolas", 9),
                 bg=self.BG, fg=self.TEXT_MUTED).grid(row=1, column=0, pady=(0, 8))

        # ── Stat cards ──
        cards = tk.Frame(container, bg=self.BG)
        cards.grid(row=2, column=0, pady=(0, 8))
        self._make_stat_card(cards, "Total Size",
                             f"{s['total_size'] / (1024**3):.2f} GB",
                             f"{s['total_size'] / (1024**2):.1f} MB", 0)
        self._make_stat_card(cards, "Files", f"{s['total_files']:,}", "", 1)
        self._make_stat_card(cards, "Folders",
                             f"{scan_info.get('total_folders', 0):,}", "", 2)
        self._make_stat_card(cards, "Largest File",
                             f"{s['largest_file_size'] / (1024**2):.1f} MB",
                             s.get('largest_file_name', ''), 3)

        # ── Sub-notebook: Folders / Files ──
        sub_style = ttk.Style()
        sub_style.configure("Sub.TNotebook", background=self.BG, borderwidth=0)
        sub_style.configure("Sub.TNotebook.Tab", background=self.SURFACE2,
                            foreground=self.TEXT, padding=[10, 3],
                            font=("Segoe UI", 9))
        sub_style.map("Sub.TNotebook.Tab", background=[("selected", self.ACCENT)],
                      foreground=[("selected", "#ffffff")])

        sub_notebook = ttk.Notebook(container, style="Sub.TNotebook")
        sub_notebook.grid(row=3, column=0, sticky="nsew", padx=8)

        # Folders tab
        folders_frame = tk.Frame(sub_notebook, bg=self.SURFACE)
        self._build_treeview(folders_frame,
                             columns=("folder", "size", "files"),
                             headings=("Folder", "Size", "Files"),
                             data=[(f["path"], self._fmt_size(f["total_size"]),
                                    f"{f['file_count']:,}") for f in folders[:50]],
                             col_widths=(400, 120, 100))
        sub_notebook.add(folders_frame, text="📁  Top Folders")

        # Files tab
        files_frame = tk.Frame(sub_notebook, bg=self.SURFACE)
        self._build_treeview(files_frame,
                             columns=("name", "size", "path"),
                             headings=("Name", "Size", "Path"),
                             data=[(f["name"], self._fmt_size(f["size"]),
                                    f["path"]) for f in files[:100]],
                             col_widths=(250, 120, 400))
        sub_notebook.add(files_frame, text="📄  Top Files")

        # ── Bottom buttons ──
        btn_frame = tk.Frame(container, bg=self.BG)
        btn_frame.grid(row=4, column=0, pady=(8, 6))

        new_btn = tk.Button(btn_frame, text="📂  New Scan",
                            font=("Segoe UI", 10, "bold"),
                            bg=self.ACCENT, fg="#ffffff", relief="flat",
                            cursor="hand2", padx=20, pady=6,
                            command=self._start_new_scan)
        new_btn.pack(side=tk.LEFT, padx=6)
        new_btn.bind("<Enter>", lambda _e: new_btn.configure(bg=self.ACCENT_HOVER))
        new_btn.bind("<Leave>", lambda _e: new_btn.configure(bg=self.ACCENT))

        close_btn = tk.Button(btn_frame, text="✕  Close Tab",
                              font=("Segoe UI", 9),
                              bg=self.SURFACE2, fg=self.TEXT, relief="flat",
                              cursor="hand2", padx=14, pady=6,
                              command=self._close_current_tab)
        close_btn.pack(side=tk.LEFT, padx=6)
        close_btn.bind("<Enter>", lambda _e: close_btn.configure(bg=self.BORDER))
        close_btn.bind("<Leave>", lambda _e: close_btn.configure(bg=self.SURFACE2))

        # ── Add to notebook & select ──
        self._notebook.add(container, text=f"📊  {short_name[:20]}")
        self._notebook.select(len(self._notebook.tabs()) - 1)

    # ── Tab management ──────────────────────────────────────────────

    def _close_current_tab(self) -> None:
        """Close the currently selected tab (keep at least the Home tab)."""
        sel = self._notebook.select()
        if not sel:
            return
        idx = self._notebook.index(sel)
        if idx == 0:  # Don't close the Home tab
            return
        self._notebook.forget(idx)

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _fmt_size(bytes_val: int) -> str:
        if bytes_val == 0:
            return "0 B"
        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while bytes_val >= 1024 and i < len(units) - 1:
            bytes_val /= 1024
            i += 1
        return f"{bytes_val:.1f} {units[i]}"

    def _make_stat_card(self, parent: tk.Frame, label: str, value: str,
                        sub: str, col: int) -> None:
        card = tk.Frame(parent, bg=self.SURFACE2, bd=0, highlightthickness=1,
                        highlightbackground=self.BORDER, padx=14, pady=8)
        card.grid(row=0, column=col, padx=6)
        tk.Label(card, text=label, font=("Segoe UI", 8, "bold"),
                 bg=self.SURFACE2, fg=self.TEXT_MUTED).pack()
        tk.Label(card, text=value, font=("Segoe UI", 14, "bold"),
                 bg=self.SURFACE2, fg=self.TEXT).pack()
        if sub:
            tk.Label(card, text=sub, font=("Segoe UI", 8),
                     bg=self.SURFACE2, fg=self.TEXT_MUTED).pack()

    def _build_treeview(self, parent: tk.Frame, columns: tuple,
                        headings: tuple, data: list,
                        col_widths: tuple) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        tree = ttk.Treeview(parent, columns=columns, show="headings",
                            selectmode="browse")
        for col, heading, w in zip(columns, headings, col_widths):
            tree.heading(col, text=heading)
            tree.column(col, width=w, anchor="w")

        style = ttk.Style()
        style.configure("Treeview", background=self.SURFACE, foreground=self.TEXT,
                        fieldbackground=self.SURFACE, rowheight=24,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=self.SURFACE2,
                        foreground=self.TEXT, font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", self.ACCENT)])

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for row in data:
            tree.insert("", tk.END, values=row)

    # ── Run ─────────────────────────────────────────────────────────

    def run(self) -> None:
        self.root.mainloop()
