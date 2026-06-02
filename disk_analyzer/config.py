"""Configuration for the Disk Storage Analyzer."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    """Application configuration with sensible defaults."""

    # Default path to scan (can be overridden via CLI)
    default_scan_path: str = "C:\\"

    # Patterns to exclude (folder names containing these substrings)
    exclude_patterns: List[str] = field(default_factory=list)

    # Output HTML filename
    output_file: str = "disk_report.html"

    # Cache directory (relative to CWD)
    cache_dir: str = ".cache"

    # Cache filename
    cache_file: str = "scan_cache.json"

    # Max files to show in the HTML table
    table_limit: int = 5000

    # Max folders to show in charts
    top_folders_count: int = 200

    # Max extensions to show in pie chart
    top_extensions_count: int = 15

    @property
    def cache_path(self) -> str:
        return os.path.join(self.cache_dir, self.cache_file)

    def should_exclude(self, path: str) -> bool:
        """Check if a path matches any exclusion pattern."""
        for pattern in self.exclude_patterns:
            if pattern.lower() in path.lower():
                return True
        return False
