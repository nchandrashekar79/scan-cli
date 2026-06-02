"""Graphical launcher for the Disk Storage Analyzer using tkinter."""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional


class DiskAnalyzerGUI:
    """A tkinter GUI for selecting a folder and launching a disk scan."""

    # Color palette (matches the HTML report dark theme)
    BG = "#0f172a"
    SURFACE = "#1e293b"
    SURFACE2 = "#334155"
    BORDER = "#475569"
    TEXT = "#f1f5f9"
    TEXT_MUTED = "#94a3b8"
    ACCENT = "#3b82f6"
    ACCENT_HOVER = "#2563eb"
    GREEN = "#22c55e"
    RED = "#ef4444"

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Disk Storage Analyzer")
        self.root.geometry("780x520")
        self.root.minsize(620, 420)
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

        # State
        self._scanning = False
        self._cancel_requested = False

        self._build_ui()

    # ── UI Construction ──────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = tk.Frame(self.root, bg=self.BG)
        main.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(7, weight=1)

        # ── Header ──
        tk.Label(
            main,
            text="💾  Disk Storage Analyzer",
            font=("Segoe UI", 22, "bold"),
            bg=self.BG,
            fg=self.TEXT,
        ).grid(row=0, column=0, pady=(0, 4))

        tk.Label(
            main,
            text="Scan any folder to visualise what's consuming your storage",
            font=("Segoe UI", 11),
            bg=self.BG,
            fg=self.TEXT_MUTED,
        ).grid(row=1, column=0, pady=(0, 28))

        # ── Input controls container (hidden when showing results) ──
        self._input_frame = tk.Frame(main, bg=self.BG)
        self._input_frame.grid(row=2, column=0, sticky="ew")
        self._input_frame.columnconfigure(0, weight=1)

        # ── Folder selection row ──
        sel_frame = tk.Frame(self._input_frame, bg=self.BG)
        sel_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        sel_frame.columnconfigure(0, weight=0)
        sel_frame.columnconfigure(1, weight=1)

        tk.Label(
            sel_frame,
            text="Folder to scan",
            font=("Segoe UI", 10, "bold"),
            bg=self.BG,
            fg=self.TEXT,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        self._path_var = tk.StringVar(value=os.path.abspath("."))
        self._path_entry = tk.Entry(
            sel_frame,
            textvariable=self._path_var,
            font=("Consolas", 10),
            bg=self.SURFACE,
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.BORDER,
            highlightcolor=self.ACCENT,
        )
        self._path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8), ipady=6, ipadx=8)

        self._browse_btn = self._styled_btn(
            sel_frame,
            text="📂  Browse",
            command=self._browse_folder,
            bg=self.SURFACE2,
            hover=self.BORDER,
        )
        self._browse_btn.grid(row=1, column=1, sticky="e")

        # ── Quick-path buttons ──
        quick_frame = tk.Frame(self._input_frame, bg=self.BG)
        quick_frame.grid(row=1, column=0, sticky="w", pady=(0, 24))
        tk.Label(
            quick_frame, text="Quick:", font=("Segoe UI", 9), bg=self.BG, fg=self.TEXT_MUTED
        ).pack(side=tk.LEFT, padx=(0, 6))

        for label, target in [
            ("This PC", "C:\\"),
            ("Users", os.path.expanduser("~")),
            ("Desktop", os.path.join(os.path.expanduser("~"), "Desktop")),
            ("Documents", os.path.join(os.path.expanduser("~"), "Documents")),
        ]:
            btn = tk.Label(
                quick_frame,
                text=label,
                font=("Segoe UI", 9, "underline"),
                bg=self.BG,
                fg=self.ACCENT,
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=(0, 14))
            btn.bind("<Button-1>", lambda _e, t=target: self._set_path(t))
            btn.bind(
                "<Enter>",
                lambda _e, b=btn: b.configure(fg=self.ACCENT_HOVER),
            )
            btn.bind(
                "<Leave>",
                lambda _e, b=btn: b.configure(fg=self.ACCENT),
            )

        # ── Scan button & progress (in input_frame) ──
        self._scan_btn = self._styled_btn(
            self._input_frame,
            text="▶  Start Scan",
            command=self._start_scan,
            bg=self.ACCENT,
            hover=self.ACCENT_HOVER,
            font_size=12,
        )
        self._scan_btn.grid(row=2, column=0, pady=(0, 18), ipady=8)

        # ── Progress bar ──
        self._progress = ttk.Progressbar(
            self._input_frame,
            mode="indeterminate",
            length=600,
        )
        self._progress.grid(row=3, column=0, pady=(0, 8), sticky="ew")
        self._progress.grid_remove()

        # ── Status label ──
        self._status_var = tk.StringVar(value="Ready  —  choose a folder and click Start Scan")
        self._status_lbl = tk.Label(
            main,
            textvariable=self._status_var,
            font=("Segoe UI", 10),
            bg=self.BG,
            fg=self.TEXT_MUTED,
            wraplength=680,
            justify=tk.CENTER,
        )
        self._status_lbl.grid(row=6, column=0, pady=(0, 4))

        # ── Results container (hidden until scan completes) ──
        self._results_frame = tk.Frame(main, bg=self.BG)
        self._results_frame.grid(row=7, column=0, sticky="nsew", pady=(0, 10))
        self._results_frame.columnconfigure(0, weight=1)
        self._results_frame.rowconfigure(1, weight=1)
        self._results_frame.grid_remove()

    def _styled_btn(
        self,
        parent: tk.Widget,
        text: str,
        command,
        bg: str,
        hover: str,
        font_size: int = 10,
    ) -> tk.Label:
        """Create a label that looks like a button (customisable colours)."""
        btn = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", font_size, "bold"),
            bg=bg,
            fg=self.TEXT,
            cursor="hand2",
            padx=20,
            pady=6,
        )
        btn.bind("<Button-1>", lambda _e: command())
        btn.bind("<Enter>", lambda _e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda _e: btn.configure(bg=bg))
        return btn

    # ── Actions ─────────────────────────────────────────────────────

    def _set_path(self, path: str) -> None:
        self._path_var.set(path)

    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(
            title="Select a folder to scan",
            initialdir=self._path_var.get() or "C:\\",
        )
        if folder:
            self._path_var.set(folder)

    def _set_scanning_state(self, scanning: bool) -> None:
        self._scanning = scanning
        state = tk.DISABLED if scanning else tk.NORMAL
        self._browse_btn.configure(state=state)
        self._scan_btn.configure(state=state)
        for child in self._scan_btn.master.winfo_children():
            for sub in (
                child.winfo_children() if hasattr(child, "winfo_children") else []
            ):
                if isinstance(sub, tk.Label) and sub.cget("text") in (
                    "This PC",
                    "Users",
                    "Desktop",
                    "Documents",
                ):
                    sub.configure(state=state)

        if scanning:
            self._progress.grid()
            self._progress.start(10)
            self._scan_btn.configure(text="⏳  Scanning…")
        else:
            self._progress.stop()
            self._progress.grid_remove()
            self._scan_btn.configure(text="▶  Start Scan")

    def _start_scan(self) -> None:
        if self._scanning:
            return

        path = self._path_var.get().strip()
        if not path or not os.path.isdir(path):
            messagebox.showwarning(
                "Invalid Folder",
                "Please select a valid folder before scanning.",
            )
            return

        self._cancel_requested = False
        self._set_scanning_state(True)
        self._status_var.set("Scanning…  this may take a while for large folders")

        # Run scan in background thread
        t = threading.Thread(target=self._run_scan, args=(path,), daemon=True)
        t.start()

    def _run_scan(self, path: str) -> None:
        """Run the full scan pipeline (background thread)."""
        try:
            from disk_analyzer.aggregator import aggregate
            from disk_analyzer.config import Config
            from disk_analyzer.scanner import load_cache, save_cache, scan_files

            import time

            config = Config()
            scan_path = os.path.abspath(path)

            # ── Check cache ──
            files = load_cache(config)
            if files is not None:
                self._schedule_status(
                    f"✅ Loaded {len(files):,} files from cache — aggregating…"
                )
            else:
                self._schedule_status(f"📡 Scanning {scan_path}…")

                def _progress(found: int, current: str) -> None:
                    self._schedule_status(
                        f"📁  {found:,} files found  —  {os.path.basename(current) or current}"
                    )

                scan_start = time.time()
                files = scan_files(config, scan_path, progress_callback=_progress)
                elapsed = time.time() - scan_start

                self._schedule_status(
                    f"✅ Scanned {len(files):,} files in {elapsed:.1f}s — caching…"
                )
                save_cache(config, files, scan_path)
                self._schedule_status(
                    f"✅ Scanned {len(files):,} files in {elapsed:.1f}s — cached"
                )

            if self._cancel_requested:
                self._schedule_finish(cancelled=True)
                return

            # ── Aggregate ──
            self._schedule_status("📊 Aggregating data…")
            data = aggregate(config, files)

            self._schedule_finish(data=data)

        except Exception as exc:
            self._schedule_finish(error=str(exc))

    def _schedule_status(self, msg: str) -> None:
        """Schedule a status update on the main thread."""
        self.root.after(0, lambda: self._status_var.set(msg))

    def _schedule_finish(
        self,
        cancelled: bool = False,
        data=None,
        error: Optional[str] = None,
    ) -> None:
        """Schedule completion handling on the main thread."""

        def _finish() -> None:
            self._set_scanning_state(False)
            if error:
                self._status_var.set(f"❌  Error: {error}")
                messagebox.showerror("Scan Error", error)
            elif cancelled:
                self._status_var.set("⛔  Scan cancelled")
            elif data:
                self._show_results(data)

        self.root.after(0, _finish)

    def _show_results(self, data) -> None:
        """Fill the embedded results frame and show it, hiding the input form."""
        s = data["summary"]
        scan_info = data["scan_info"]

        # Clear any previous results
        for child in self._results_frame.winfo_children():
            child.destroy()

        # ── Scrollable canvas for results ──
        canvas = tk.Canvas(self._results_frame, bg=self.BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(self._results_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.BG)

        scrollable.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw", width=canvas.winfo_width())
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))

        scrollable.columnconfigure(0, weight=1)

        # ── Results header ──
        header = tk.Frame(scrollable, bg=self.BG, padx=10, pady=(0, 12))
        header.grid(row=0, column=0, sticky="ew")
        tk.Label(
            header, text="✅  Scan Complete",
            font=("Segoe UI", 16, "bold"),
            bg=self.BG, fg=self.TEXT,
        ).pack()
        tk.Label(
            header, text=self._path_var.get(),
            font=("Consolas", 9), bg=self.BG, fg=self.TEXT_MUTED,
        ).pack()

        # ── Stats cards ──
        cards_frame = tk.Frame(scrollable, bg=self.BG, padx=0, pady=6)
        cards_frame.grid(row=1, column=0, sticky="ew")
        cards_frame.columnconfigure(0, weight=1)

        stats = [
            ("Total Size", f"{s['total_size'] / (1024**3):.2f} GB",
             f"{s['total_size'] / (1024**2):.1f} MB"),
            ("Total Files", f"{s['total_files']:,}", ""),
            ("Total Folders", f"{scan_info.get('total_folders', 0):,}", ""),
            ("Largest File", s['largest_file_name'],
             f"{s['largest_file_size'] / (1024**2):.1f} MB"),
            ("Avg File Size", f"{s['average_file_size'] / 1024:.1f} KB", ""),
        ]

        for label, value, sub in stats:
            card = tk.Frame(
                cards_frame, bg=self.SURFACE, padx=16, pady=10,
                highlightbackground=self.BORDER, highlightthickness=1,
            )
            card.grid(row=cards_frame.grid_size()[1], column=0, sticky="ew", pady=3)
            row = tk.Frame(card, bg=self.SURFACE)
            row.pack(fill=tk.X)
            tk.Label(
                row, text=label, font=("Segoe UI", 9, "bold"),
                bg=self.SURFACE, fg=self.TEXT_MUTED,
            ).pack(side=tk.LEFT)
            tk.Label(
                row, text=value, font=("Segoe UI", 14, "bold"),
                bg=self.SURFACE, fg=self.ACCENT,
            ).pack(side=tk.RIGHT)
            if sub:
                tk.Label(
                    card, text=sub, font=("Segoe UI", 9),
                    bg=self.SURFACE, fg=self.TEXT_MUTED,
                    anchor="e",
                ).pack(fill=tk.X)

        # ── Top 5 extensions ──
        if "extensions" in data and data["extensions"]:
            ext_frame = tk.Frame(scrollable, bg=self.BG, padx=0, pady=(4, 10))
            ext_frame.grid(row=2, column=0, sticky="ew")
            ext_frame.columnconfigure(0, weight=1)
            tk.Label(
                ext_frame, text="Top File Types",
                font=("Segoe UI", 10, "bold"),
                bg=self.BG, fg=self.TEXT,
            ).grid(row=0, column=0, sticky="w", pady=(0, 4))
            for ext in data["extensions"][:5]:
                ext_row = tk.Frame(ext_frame, bg=self.SURFACE2, padx=12, pady=4)
                ext_row.grid(row=ext_frame.grid_size()[1], column=0, sticky="ew", pady=2)
                tk.Label(
                    ext_row, text=ext["extension"],
                    font=("Consolas", 10, "bold"),
                    bg=self.SURFACE2, fg=self.GREEN,
                ).pack(side=tk.LEFT)
                tk.Label(
                    ext_row, text=f"{ext['count']:,} files  ·  "
                    f"{ext['total_size'] / (1024**2):.1f} MB",
                    font=("Segoe UI", 10),
                    bg=self.SURFACE2, fg=self.TEXT_MUTED,
                ).pack(side=tk.RIGHT)

        # ── Scan Again button ──
        btn_frame = tk.Frame(scrollable, bg=self.BG, padx=0, pady=8)
        btn_frame.grid(row=3, column=0, sticky="ew")
        again_btn = tk.Button(
            btn_frame, text="🔄  Scan Another Folder",
            font=("Segoe UI", 10, "bold"),
            bg=self.ACCENT, fg=self.TEXT,
            relief="flat", cursor="hand2",
            command=self._reset_view,
        )
        again_btn.pack()
        again_btn.bind("<Enter>", lambda _e: again_btn.configure(bg=self.ACCENT_HOVER))
        again_btn.bind("<Leave>", lambda _e: again_btn.configure(bg=self.ACCENT))

        # ── Swap views ──
        self._input_frame.grid_remove()
        self._results_frame.grid()

    def _reset_view(self) -> None:
        """Hide results and show the input form again."""
        self._results_frame.grid_remove()
        self._input_frame.grid()
        self._status_var.set("Ready  —  choose a folder and click Start Scan")

    # ── Run ─────────────────────────────────────────────────────────

    def run(self) -> None:
        self.root.mainloop()
