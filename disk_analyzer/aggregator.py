"""Aggregation logic - computes folder rollups, extension stats, and summaries."""

import os
from collections import defaultdict
from typing import Dict, List, Tuple

from disk_analyzer.config import Config


def compute_folder_sizes(files: List[Dict]) -> List[Dict]:
    """
    Aggregate file sizes by parent directory.

    Returns a list of dicts sorted by total_size descending, each with:
        path, total_size, file_count, largest_file, largest_file_size
    """
    folder_map: Dict[str, Dict] = {}

    for f in files:
        folder = os.path.dirname(f["path"])
        if folder not in folder_map:
            folder_map[folder] = {
                "path": folder,
                "total_size": 0,
                "file_count": 0,
                "largest_file": "",
                "largest_file_size": 0,
            }
        entry = folder_map[folder]
        entry["total_size"] += f["size"]
        entry["file_count"] += 1
        if f["size"] > entry["largest_file_size"]:
            entry["largest_file_size"] = f["size"]
            entry["largest_file"] = f["name"]

    folders = sorted(
        folder_map.values(), key=lambda x: x["total_size"], reverse=True
    )
    return folders


def compute_extension_stats(files: List[Dict]) -> List[Dict]:
    """
    Aggregate file sizes and counts by file extension.

    Returns a list of dicts sorted by total_size descending, each with:
        extension, total_size, count
    """
    ext_map: Dict[str, Dict] = {}

    for f in files:
        ext = f["extension"]
        if ext not in ext_map:
            ext_map[ext] = {"extension": ext, "total_size": 0, "count": 0}
        ext_map[ext]["total_size"] += f["size"]
        ext_map[ext]["count"] += 1

    extensions = sorted(
        ext_map.values(), key=lambda x: x["total_size"], reverse=True
    )
    return extensions


def compute_summary(files: List[Dict]) -> Dict:
    """Compute summary statistics from the file list."""
    if not files:
        return {
            "total_size": 0,
            "total_files": 0,
            "largest_file": "",
            "largest_file_size": 0,
            "average_file_size": 0,
        }

    total_size = sum(f["size"] for f in files)
    largest = files[0]  # already sorted desc by size

    return {
        "total_size": total_size,
        "total_files": len(files),
        "largest_file": largest["path"],
        "largest_file_name": largest["name"],
        "largest_file_size": largest["size"],
        "average_file_size": total_size // len(files) if files else 0,
    }


def aggregate(config: Config, files: List[Dict]) -> Dict:
    """
    Run all aggregation steps and return a complete report data structure.

    Returns:
        Dict with keys: files (top N), folders, extensions, summary, scan_info
    """
    folders = compute_folder_sizes(files)
    extensions = compute_extension_stats(files)
    summary = compute_summary(files)

    return {
        "files": files[: config.table_limit],
        "folders": folders[: config.top_folders_count],
        "extensions": extensions[: config.top_extensions_count],
        "summary": summary,
        "scan_info": {
            "total_files_scanned": len(files),
            "total_folders": len(folders),
            "total_extensions": len(extensions),
        },
    }
