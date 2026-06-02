# 💾 Disk Storage Analyzer

A Python tool that scans a directory, aggregates file/folder sizes, and displays a storage consumption summary — either in the terminal (CLI) or through a native tkinter GUI.

---

## 🚀 Quick Start

Run directly from the project root (no activation needed):

**GUI mode** (opens a folder picker window):
```powershell
.venv\Scripts\python.exe -m disk_analyzer.main
```

**CLI mode** (scans and prints results in the terminal):
```powershell
.venv\Scripts\python.exe -m disk_analyzer.main --cli --path "C:\Users"
```

> ⚠️ Always use `-m disk_analyzer.main` — not `disk_analyzer/main.py`. The `-m` flag ensures internal package imports resolve correctly.

---

## 🧰 CLI Options

| Flag | Purpose |
|---|---|
| `--cli` | Run in terminal instead of launching the GUI |
| `--path D:\Folder` | Directory to scan (default: `C:\`) |
| `--scan` | Force a fresh scan, ignoring any cached results |
| `--exclude temp,cache` | Comma-separated folder names to skip |
| `--help` | Show all available options |

### Examples

```powershell
# Scan a specific folder
.venv\Scripts\python.exe -m disk_analyzer.main --cli --path "D:\Projects"

# Force rescan (ignore cache)
.venv\Scripts\python.exe -m disk_analyzer.main --cli --path "C:\" --scan

# Exclude common junk folders
.venv\Scripts\python.exe -m disk_analyzer.main --cli --path "C:\Users" --exclude temp,cache,node_modules
```

---

## 📦 Requirements

- Python 3.8+
- `tqdm` (installed automatically in the virtual environment)

Install dependencies manually with:

```powershell
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
disk_analyzer/
├── __init__.py          # Package marker
├── main.py              # Entry point (GUI / CLI)
├── gui.py               # tkinter GUI (folder picker + results dialog)
├── scanner.py           # File system scanner
├── aggregator.py        # Size aggregation logic
├── report_generator.py  # HTML report generator
├── config.py            # Configuration defaults
```

---

## 🖥️ GUI Results

When scanning via the GUI, a native results dialog appears showing:
- Total size (GB / MB)
- Total files and folders scanned
- Largest file found
- Average file size
- Top 5 file types by count/size
