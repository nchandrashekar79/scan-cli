"""File system scanner - walks directories and collects file metadata."""

import json
import os
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from disk_analyzer.config import Config


def format_timestamp(ts: float) -> str:
    """Format a Unix timestamp to ISO string."""
    return datetime.fromtimestamp(ts).isoformat()


def scan_files(
    config: Config,
    scan_path: Optional[str] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    scan_id: Optional[str] = None,
) -> List[Dict]:
    """
    Recursively scan a directory and return a list of file metadata dicts.

    Each dict has keys: path, name, size, modified, extension.

    Args:
        config: Application configuration.
        scan_path: Directory to scan (defaults to config.default_scan_path).
        progress_callback: Optional function called with (files_found, current_dir).
        scan_id: Optional identifier for this scan run.

    Returns:
        List of file info dicts sorted by size descending.
    """
    path_to_scan = scan_path or config.default_scan_path
    files: List[Dict] = []
    errors: List[str] = []
    start_time = time.time()

    if not os.path.exists(path_to_scan):
        raise FileNotFoundError(f"Scan path does not exist: {path_to_scan}")

    for root, dirs, names in os.walk(path_to_scan, topdown=True):
        # Filter excluded directories in-place (prevents walking into them)
        if config.exclude_patterns:
            dirs[:] = [
                d
                for d in dirs
                if not config.should_exclude(os.path.join(root, d))
            ]

        if progress_callback:
            progress_callback(len(files), root)

        for name in names:
            filepath = os.path.join(root, name)
            try:
                stat_info = os.stat(filepath)
                files.append(
                    {
                        "path": filepath,
                        "name": name,
                        "size": stat_info.st_size,
                        "modified": format_timestamp(stat_info.st_mtime),
                        "extension": os.path.splitext(name)[1].lower()
                        or "(no ext)",
                    }
                )
            except (OSError, PermissionError):
                errors.append(filepath)

    elapsed = time.time() - start_time
    files.sort(key=lambda f: f["size"], reverse=True)

    if progress_callback:
        progress_callback(len(files), f"Done ({elapsed:.1f}s, {len(errors)} errors)")

    return files


def save_cache(config: Config, files: List[Dict], scan_path: str) -> str:
    """Save scan results to a JSON cache file."""
    os.makedirs(config.cache_dir, exist_ok=True)
    cache_data = {
        "scan_path": scan_path,
        "scan_time": datetime.now().isoformat(),
        "file_count": len(files),
        "files": files,
    }
    with open(config.cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, indent=2)
    return config.cache_path


def load_cache(config: Config, scan_path: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Load scan results from cache.

    Args:
        config: Application configuration.
        scan_path: If provided, only returns cached data when the cached
                   scan_path matches this path (ensures cache is for the
                   same folder being requested).

    Returns:
        List of file dicts, or None if cache is missing, invalid, or
        the scan_path doesn't match.
    """
    if not os.path.exists(config.cache_path):
        return None
    try:
        with open(config.cache_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "files" not in data or not isinstance(data["files"], list):
            return None
        # Verify the cache is for the same scan path (when provided)
        if scan_path is not None:
            cached_path = data.get("scan_path")
            if cached_path != scan_path:
                return None
        return data["files"]
    except (json.JSONDecodeError, OSError):
        return None
