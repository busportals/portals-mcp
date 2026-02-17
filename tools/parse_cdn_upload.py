#!/usr/bin/env python3
"""
Parse CDN upload results and save as cdn_urls.json.

Handles two input formats:
  1. Raw text file with "filename.glb -> https://..." lines
  2. JSON array from MCP tool overflow (Claude Code dumps large results as JSON)

Verifies all manifest-referenced GLBs have CDN URLs.

Usage:
    python tools/parse_cdn_upload.py <upload_result_file> <export_dir>

Arguments:
    upload_result_file   Path to the raw upload output (text or JSON overflow file)
    export_dir           Path to blender_export/ dir (contains manifest.json, receives cdn_urls.json)
"""

import json
import os
import sys


def extract_text_from_file(filepath: str) -> str:
    """Read the upload result, handling both raw text and JSON overflow formats."""
    with open(filepath) as f:
        content = f.read()

    # Try JSON array format first (Claude Code overflow format)
    try:
        data = json.loads(content)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("type") == "text":
                    return item["text"]
    except (json.JSONDecodeError, TypeError):
        pass

    # Fall back to raw text
    return content


def parse_cdn_lines(text: str) -> dict:
    """Parse 'filename.glb -> https://...' lines into a dict."""
    cdn_urls = {}
    for line in text.strip().split("\n"):
        if " -> " in line:
            filename, url = line.split(" -> ", 1)
            cdn_urls[filename.strip()] = url.strip()
    return cdn_urls


def main():
    if len(sys.argv) < 3:
        print("Usage: python tools/parse_cdn_upload.py <upload_result_file> <export_dir>")
        sys.exit(1)

    upload_file = sys.argv[1]
    export_dir = sys.argv[2]

    if not os.path.exists(upload_file):
        print(f"ERROR: Upload result file not found: {upload_file}")
        sys.exit(1)

    manifest_path = os.path.join(export_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"ERROR: manifest.json not found in {export_dir}")
        sys.exit(1)

    # Parse upload results
    text = extract_text_from_file(upload_file)
    cdn_urls = parse_cdn_lines(text)

    # Load manifest
    with open(manifest_path) as f:
        manifest = json.load(f)

    objects = manifest.get("objects", manifest if isinstance(manifest, list) else [])
    manifest_glbs = {obj["glb_file"] for obj in objects}

    # Verify
    missing = manifest_glbs - set(cdn_urls.keys())
    matched = manifest_glbs & set(cdn_urls.keys())
    extra = len(cdn_urls) - len(matched)

    # Save cdn_urls.json
    output_path = os.path.join(export_dir, "cdn_urls.json")
    with open(output_path, "w") as f:
        json.dump(cdn_urls, f, indent=2)

    # Print concise summary
    print(f"CDN URLs parsed: {len(cdn_urls)} total")
    print(f"Manifest GLBs: {len(manifest_glbs)} unique")
    print(f"Matched: {len(matched)}/{len(manifest_glbs)}")
    if extra:
        print(f"Extra (not in manifest): {extra}")
    if missing:
        print(f"MISSING: {sorted(missing)}")
        sys.exit(1)
    else:
        print("All manifest GLBs resolved.")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
