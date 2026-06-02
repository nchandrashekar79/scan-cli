## Plan: Disk Storage Analyzer (Python + HTML Report)

**TL;DR**: Create a Python script inside the `scan-cli` folder that scans all files on the C: drive, computes file/folder sizes, and generates a self-contained interactive HTML report with sortable tables, search, treemap, and pie/bar charts to identify storage hogs.

---

### Phases

#### Phase 1: Project structure & scanner

1. **Create `disk_analyzer/` package folder** inside `scan-cli/` with:
   - `__init__.py`
   - `scanner.py` — walks C:\ recursively via `os.walk()`, collects `(path, size, is_dir, modified_time)`, stores in a list
   - `aggregator.py` — aggregates file data into folder-level rollups (total size, file count, largest files per folder)
   - `config.py` — configurable exclusions list (default empty per user choice, but easy to customize)

2. **Handle performance**: Since scanning C:\ is massive:
   - Use `tqdm` (progress bar) or a simple counter printed periodically
   - Handle permission errors gracefully (`try/except` around `os.scandir` / `os.walk`)
   - Store intermediate results to a JSON cache file so re-running the HTML generation is fast without rescanning

#### Phase 2: HTML report generator

3. **Create `report_generator.py`** — generates a single self-contained HTML file `disk_report.html`

   **Data embedded as JSON** in a `<script>` tag:
   - Top 5000 largest files
   - Top 200 largest folders
   - Extension-based breakdown

   **External CDN libraries** (loaded via `<script src="...">`):
   - **Chart.js** — for pie chart (storage by file extension) and bar chart (top 20 folders by size)
   - **D3.js** — for interactive treemap visualization of folder hierarchy
   - No server-side dependencies

   **HTML features** (all client-side JavaScript):
   - **Sortable table**: Top 5000 files, sortable by name, size, path, last modified (vanilla JS)
   - **Search/filter**: Real-time text filter on the file table
   - **Treemap**: D3.js treemap showing folder sizes with drill-down
   - **Pie chart**: Storage breakdown by file extension (.mp4, .dll, .zip, etc.)
   - **Bar chart**: Top 20 folders by total size
   - **Summary stats**: Total disk usage, total file count, largest file, average file size

#### Phase 3: Entry point & UX

4. **Create `main.py`** — CLI entry point with:
   - `--scan` flag: force rescan (by default, uses cached JSON if available)
   - `--path` argument: override scan path (defaults to `C:\`)
   - `--output` argument: custom output HTML path
   - `--exclude` argument: comma-separated folder patterns to exclude

5. **Create `requirements.txt`** — minimal dependencies (`tqdm` only; charting is purely CDN-based in HTML)

---

### Relevant Files

All under `c:\Users\Admin\Documents\ai\scan-cli\disk_analyzer\`:
| File | Purpose |
|------|---------|
| `__init__.py` | Package marker |
| `config.py` | Default scan path (`C:\`), exclusion patterns, output filename |
| `scanner.py` | Recursive file walker with permission handling, stores `ScanResult` objects |
| `aggregator.py` | Folder rollups, extension stats, top-N sorting |
| `report_generator.py` | Generates full HTML with embedded JSON data + Chart.js/D3.js |
| `main.py` | CLI entry point with argparse |
| `requirements.txt` | `tqdm` |

---

### Verification

1. Run `python disk_analyzer/main.py --path C:\Users\Admin\Documents` (a small subtree for quick testing)
2. Open the generated `disk_report.html` in a browser
3. Verify: sortable table works (click column headers), search filters rows
4. Verify: treemap renders with folder rectangles
5. Verify: pie chart (by extension) and bar chart (top folders) render
6. Verify: second run uses cache (fast)
7. Run `python disk_analyzer/main.py --scan --path C:\` for full scan (will take minutes)

---

### Decisions

- **Scan approach**: Use `os.scandir()` for iterative traversal instead of `os.walk()` for better performance and error handling on individual entries
- **Dependencies**: `tqdm` only for progress indication; charts are CDN-based (no Python charting libs needed)
- **Self-contained HTML**: All CSS/JS data is embedded in the single HTML file except CDN library links — zero server needed
- **Sorting**: Client-side vanilla JS (not DataTables) to keep the HTML lightweight
- **Cache**: JSON cache stored at `cache/scan_cache.json` so the slow scan step can be skipped on re-runs

---

### Further Considerations

1. **Scanning C:\ is very slow** — the user chose full C: scan with no exclusions. Consider adding a warning about scan time and suggesting smaller paths for testing.
2. **File count limit** — Showing all files in the table could crash the browser. Cap table at top 5000 by size; full data is used for aggregation charts only.
3. **Admin privileges** — Some folders (System32, $Recycle.Bin) may be inaccessible. This is handled gracefully by `os.scandir` try/except.