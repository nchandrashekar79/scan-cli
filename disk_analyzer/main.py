#!/usr/bin/env python3
"""Disk Storage Analyzer - GUI + CLI entry point.

Launches a graphical folder browser (default) or a CLI scanner.
Scans a directory, aggregates file/folder sizes, and displays
a storage consumption summary.

Usage:
    python -m disk_analyzer.main              # Launch GUI
    python -m disk_analyzer.main --cli --path C:/Users   # CLI mode
    python -m disk_analyzer.main --help
"""

import argparse
import os
import sys
import time


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="💾 Disk Storage Analyzer - Scan files and display "
        "storage consumption analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  %(prog)s                          # Launch GUI\n"
        "  %(prog)s --path D:\\Projects       # CLI: scan a specific folder\n"
        "  %(prog)s --cli --path C:\\ --scan   # CLI: force rescan\n"
        "  %(prog)s --cli --exclude temp,cache\n",
    )

    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode instead of launching the GUI",
    )

    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Directory to scan (default: C:\\)",
    )

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Force a fresh scan, ignoring any cached results",
    )

    parser.add_argument(
        "--exclude",
        type=str,
        default=None,
        help="Comma-separated folder name patterns to exclude (e.g., 'temp,cache,$Recycle')",
    )

    return parser.parse_args()


def progress_callback(files_found: int, current_dir: str) -> None:
    """Show scan progress in the terminal."""
    # Only print every N directories to avoid flooding
    print(f"  📁 {files_found:>10,} files found  |  {current_dir[:80]}", end="\r")


def main() -> None:
    """Main entry point — launches GUI or runs CLI depending on arguments."""
    args = parse_args()

    # ── GUI mode (default) ──
    if not args.cli:
        from disk_analyzer.gui import DiskAnalyzerGUI

        gui = DiskAnalyzerGUI()
        gui.run()
        return

    # ── CLI mode ──
    from disk_analyzer.aggregator import aggregate
    from disk_analyzer.config import Config
    from disk_analyzer.scanner import load_cache, save_cache, scan_files

    # --- Configuration ---
    config = Config()
    scan_path = args.path or config.default_scan_path
    if args.exclude:
        config.exclude_patterns = [p.strip() for p in args.exclude.split(",")]

    # Resolve absolute path
    scan_path = os.path.abspath(scan_path)

    print("=" * 60)
    print("  💾 Disk Storage Analyzer")
    print("=" * 60)
    print(f"  Scan path : {scan_path}")
    if config.exclude_patterns:
        print(f"  Exclude   : {', '.join(config.exclude_patterns)}")
    print()

    # --- Scan or load cache ---
    files = None
    if not args.scan:
        print("  🔍 Checking cache...")
        files = load_cache(config)
        if files is not None:
            print(f"  ✅ Loaded {len(files):,} files from cache ({config.cache_path})")
        else:
            print("  ℹ️  No cache found, starting scan...")

    if files is None:
        print(f"  📡 Scanning {scan_path} (this may take a while)...")
        print()

        scan_start = time.time()
        files = scan_files(config, scan_path, progress_callback=progress_callback)
        scan_elapsed = time.time() - scan_start

        print()
        print(f"  ✅ Scanned {len(files):,} files in {scan_elapsed:.1f}s")

        # Save to cache
        save_cache(config, files, scan_path)
        print(f"  💾 Cached to {config.cache_path}")

    print()

    # --- Aggregate ---
    print("  📊 Aggregating data...")
    agg_start = time.time()
    data = aggregate(config, files)
    print(f"  ✅ Aggregated {data['scan_info']['total_files_scanned']:,} files "
          f"across {data['scan_info']['total_folders']:,} folders "
          f"in {time.time() - agg_start:.2f}s")
    print()

    # --- Summary ---
    s = data["summary"]
    print("─" * 60)
    print(f"  Total size     : {s['total_size'] / (1024**3):.2f} GB "
          f"({s['total_size'] / (1024**2):.1f} MB)")
    print(f"  Total files    : {s['total_files']:,}")
    print(f"  Largest file   : {s['largest_file_name']} "
          f"({s['largest_file_size'] / (1024**2):.1f} MB)")
    print(f"  Avg file size  : {s['average_file_size'] / 1024:.1f} KB")
    print("─" * 60)
    print()
    print("  ✅ Analysis complete.")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  ⛔ Scan cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n  ❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
