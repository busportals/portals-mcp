#!/usr/bin/env python3
"""
Check cumulative storage of unique files for a Portals room.

Scans a folder (or specific files) and reports total storage with thresholds:
  - Under 200 MB:  OK — room should load fine
  - 200–500 MB:    WARNING — room is heavy, consider optimizing
  - Over 500 MB:   CRITICAL — room may not load properly

Only counts unique files (by filename). Instanced/duplicated references
to the same file don't add significant load in the browser.

Usage:
    python tools/check_room_storage.py <folder_or_files...>
    python tools/check_room_storage.py path/to/glbs/ path/to/images/
    python tools/check_room_storage.py --catalog games/room-id/catalog.json

Can also be imported as a module:
    from check_room_storage import check_storage, StorageStatus
"""

import argparse
import json
import os
import sys
from enum import Enum
from pathlib import Path

# Thresholds in bytes
THRESHOLD_OK = 200 * 1024 * 1024        # 200 MB
THRESHOLD_WARNING = 500 * 1024 * 1024    # 500 MB

# File extensions we care about
ASSET_EXTENSIONS = {'.glb', '.gltf', '.png', '.jpg', '.jpeg', '.gif', '.mp3', '.wav', '.ogg', '.mp4', '.webm'}


class StorageStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


def format_size(size_bytes):
    """Format bytes into a human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_status(total_bytes):
    """Determine storage status based on thresholds."""
    if total_bytes <= THRESHOLD_OK:
        return StorageStatus.OK
    elif total_bytes <= THRESHOLD_WARNING:
        return StorageStatus.WARNING
    else:
        return StorageStatus.CRITICAL


def collect_files_from_paths(paths, extensions=None):
    """
    Collect unique files from a list of paths (files or directories).
    Returns a dict of {filename: file_path} for unique files.
    """
    unique_files = {}

    for path in paths:
        path = os.path.abspath(path)
        if os.path.isfile(path):
            filename = os.path.basename(path)
            if extensions is None or Path(path).suffix.lower() in extensions:
                unique_files[filename] = path
        elif os.path.isdir(path):
            for entry in os.listdir(path):
                full_path = os.path.join(path, entry)
                if os.path.isfile(full_path):
                    if extensions is None or Path(entry).suffix.lower() in extensions:
                        unique_files[entry] = full_path
    return unique_files


def collect_files_from_catalog(catalog_path):
    """
    Collect unique file references from a catalog.json.
    Returns a dict of {filename: file_size_bytes} where available,
    or {filename: None} if sizes aren't in the catalog.
    Also returns the catalog data for further inspection.
    """
    with open(catalog_path) as f:
        catalog = json.load(f)

    items = catalog.get("items", {})
    unique_files = {}

    for key, item in items.items():
        source_file = item.get("source_file", "")
        if source_file and source_file not in unique_files:
            unique_files[source_file] = item.get("file_size_bytes")

    return unique_files, catalog


def check_storage(paths=None, catalog_path=None, extensions=None, quiet=False):
    """
    Check cumulative storage of unique files.

    Args:
        paths: List of file/folder paths to scan
        catalog_path: Path to a catalog.json (alternative to scanning paths)
        extensions: Set of file extensions to include (None = all asset types)
        quiet: If True, suppress detailed output

    Returns:
        (total_bytes, status, file_details) where file_details is a list of
        (filename, size_bytes) tuples sorted by size descending.
    """
    if extensions is None:
        extensions = ASSET_EXTENSIONS

    file_details = []

    if catalog_path:
        unique_files, _ = collect_files_from_catalog(catalog_path)
        for filename, size_bytes in unique_files.items():
            if size_bytes is not None:
                file_details.append((filename, size_bytes))
            else:
                if not quiet:
                    print(f"  Note: No file_size_bytes for '{filename}' in catalog")
    elif paths:
        unique_files = collect_files_from_paths(paths, extensions)
        for filename, filepath in unique_files.items():
            size = os.path.getsize(filepath)
            file_details.append((filename, size))

    # Sort by size descending
    file_details.sort(key=lambda x: x[1], reverse=True)
    total_bytes = sum(size for _, size in file_details)
    status = get_status(total_bytes)

    return total_bytes, status, file_details


def print_report(total_bytes, status, file_details, verbose=False):
    """Print a formatted storage report to stdout."""
    # ANSI colors
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    color = {
        StorageStatus.OK: GREEN,
        StorageStatus.WARNING: YELLOW,
        StorageStatus.CRITICAL: RED,
    }[status]

    print()
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}  Room Storage Check{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    print()
    print(f"  Unique files:  {len(file_details)}")
    print(f"  Total size:    {BOLD}{format_size(total_bytes)}{RESET}")
    print()

    if status == StorageStatus.OK:
        print(f"  {color}OK{RESET} — Room is within size limits ({format_size(total_bytes)} / 200 MB)")
    elif status == StorageStatus.WARNING:
        print(f"  {color}WARNING{RESET} — Room is heavy ({format_size(total_bytes)} / 200 MB recommended)")
        print(f"  Consider optimizing large assets to improve load times.")
    else:
        print(f"  {color}CRITICAL{RESET} — Room exceeds 500 MB ({format_size(total_bytes)})")
        print(f"  The room may fail to load in the browser. Reduce asset sizes.")

    # Show top files by size
    if file_details and (verbose or status != StorageStatus.OK):
        print()
        show_count = min(10, len(file_details))
        print(f"  {'Largest files:'}")
        for filename, size in file_details[:show_count]:
            bar_pct = size / file_details[0][1] if file_details[0][1] > 0 else 0
            bar = "█" * max(1, int(bar_pct * 20))
            print(f"    {format_size(size):>10s}  {bar}  {filename}")
        if len(file_details) > show_count:
            remaining = len(file_details) - show_count
            remaining_size = sum(s for _, s in file_details[show_count:])
            print(f"    {format_size(remaining_size):>10s}  ... and {remaining} more files")

    print()
    print(f"{BOLD}{'='*60}{RESET}")
    print()

    return status


def main():
    parser = argparse.ArgumentParser(
        description="Check cumulative storage of unique files for a Portals room"
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="File(s) or folder(s) to scan for assets",
    )
    parser.add_argument(
        "--catalog",
        help="Path to a catalog.json (reads file_size_bytes from catalog entries)",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Include all files, not just known asset extensions",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show file breakdown even when status is OK",
    )
    args = parser.parse_args()

    if not args.paths and not args.catalog:
        parser.error("Provide at least one path or --catalog")

    extensions = None if args.all_files else ASSET_EXTENSIONS

    total_bytes, status, file_details = check_storage(
        paths=args.paths,
        catalog_path=args.catalog,
        extensions=extensions,
    )

    print_report(total_bytes, status, file_details, verbose=args.verbose)

    # Exit code: 0 = ok, 1 = warning, 2 = critical
    if status == StorageStatus.CRITICAL:
        sys.exit(2)
    elif status == StorageStatus.WARNING:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
