#!/usr/bin/env python3
"""
Convert a Blender export manifest into Portals room data.

Reads a manifest.json (produced by a Blender export addon) and a CDN URL
mapping, then generates a snapshot.json suitable for pushing to a Portals
room via MCP.

Usage:
    python tools/manifest_to_room_data.py /path/to/blender_export/ --cdn-urls urls.json
    python tools/manifest_to_room_data.py /path/to/blender_export/ --cdn-urls urls.json --room-id abc-123

Arguments:
    export_dir          Path to the export directory (contains manifest.json and GLB files)
    --cdn-urls          Path to a JSON file mapping GLB filenames to CDN URLs
                        Format: {"Chair_001.glb": "https://cdn.example.com/...", ...}
    --room-id           Optional room ID. When provided, output is written to
                        games/{room-id}/snapshot.json instead of the export dir.
"""

import argparse
import json
import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
GAMES_DIR = PROJECT_ROOT / "games"


def load_manifest(export_dir: str) -> list:
    """Load and return the manifest.json from the export directory."""
    manifest_path = os.path.join(export_dir, "manifest.json")
    if not os.path.exists(manifest_path):
        print(f"ERROR: manifest.json not found in {export_dir}")
        sys.exit(1)

    with open(manifest_path) as f:
        data = json.load(f)

    # Support both a bare list and a dict with an "objects" key
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "objects" in data:
        return data["objects"]

    print(f"ERROR: manifest.json has unexpected format — expected a list or dict with 'objects' key")
    sys.exit(1)


def load_cdn_urls(cdn_urls_path: str) -> dict:
    """Load the CDN URL mapping from a JSON file."""
    if not os.path.exists(cdn_urls_path):
        print(f"ERROR: CDN URLs file not found: {cdn_urls_path}")
        sys.exit(1)

    with open(cdn_urls_path) as f:
        data = json.load(f)

    if not isinstance(data, dict):
        print(f"ERROR: CDN URLs file must contain a JSON object, got {type(data).__name__}")
        sys.exit(1)

    return data


def manifest_object_to_room_item(obj: dict, cdn_url: str) -> dict:
    """
    Convert a single manifest object into a Portals room item.

    The manifest is expected to provide position, rotation, and scale
    already converted to Portals coordinate space (Y-up left-handed).
    """
    return {
        "prefabName": "GLB",
        "parentItemID": 0,
        "currentEditornetId": 0,
        "pos": obj["position"],
        "modelsize": {"x": 0, "y": 0, "z": 0},
        "modelCenter": {"x": 0, "y": 0, "z": 0},
        "rot": obj["rotation"],
        "scale": obj["scale"],
        "contentString": cdn_url,
        "interactivityType": 0,
        "interactivityURL": "",
        "hoverTitle": "",
        "hoverBodyContent": "",
        "ImageInteractivityDetails": {"buttonText": "", "buttonURL": ""},
        "extraData": json.dumps({"events": [], "ViewNodes": []}),
        "sessionData": "",
        "instanceId": "",
        "placed": True,
        "locked": False,
        "superLocked": False,
    }


def build_room_data(manifest_objects: list, cdn_urls: dict) -> dict:
    """
    Build a complete Portals room data dict from manifest objects.

    Returns the room data envelope with roomItems, settings, roomTasks, quests.
    """
    room_items = {}
    warnings = []

    for i, obj in enumerate(manifest_objects):
        item_id = str(i + 1)  # Item IDs start at "1"

        glb_file = obj.get("glb_file", "")
        cdn_url = cdn_urls.get(glb_file, "")

        if not cdn_url:
            name = obj.get("name", f"object #{i}")
            warnings.append(f"WARNING: No CDN URL found for '{glb_file}' (object: {name}) — using empty string")

        room_items[item_id] = manifest_object_to_room_item(obj, cdn_url)

    # Print warnings
    for w in warnings:
        print(w)

    room_data = {
        "roomItems": room_items,
        "settings": {
            "roomBase": "BlankScene",
            "isNight": False,
            "allCanBuild": False,
            "chatDisabled": False,
            "globalSpeaking": False,
            "inTownHallMode": False,
            "tasksRefresh": True,
            "roomSettingsExtraData": json.dumps({
                "preloadRoom": True,
                "showNameTags": True,
                "playerCollisions": True,
                "movementValues": {
                    "walkSpeed": 2.0,
                    "runSpeed": 4.0,
                    "sprintSpeed": 6.8,
                    "jumpHeight": 4.0,
                    "gravity": -10.0,
                    "airSpeed": 5.0,
                    "rotationSpeed": 16.0,
                },
            }),
        },
        "roomTasks": {"Tasks": []},
        "quests": {},
    }

    return room_data


def main():
    parser = argparse.ArgumentParser(
        description="Convert a Blender export manifest into Portals room data"
    )
    parser.add_argument(
        "export_dir",
        help="Path to the export directory (contains manifest.json and GLB files)",
    )
    parser.add_argument(
        "--cdn-urls",
        required=True,
        help="Path to a JSON file mapping GLB filenames to CDN URLs",
    )
    parser.add_argument(
        "--room-id",
        default=None,
        help="Optional room ID (output goes to games/{room-id}/snapshot.json)",
    )
    args = parser.parse_args()

    export_dir = os.path.abspath(args.export_dir)
    if not os.path.isdir(export_dir):
        print(f"ERROR: Export directory not found: {export_dir}")
        sys.exit(1)

    # Load inputs
    manifest_objects = load_manifest(export_dir)
    cdn_urls = load_cdn_urls(args.cdn_urls)

    print(f"Manifest: {len(manifest_objects)} objects")
    print(f"CDN URLs: {len(cdn_urls)} mappings")
    print()

    # Build room data
    room_data = build_room_data(manifest_objects, cdn_urls)

    # Determine output path
    if args.room_id:
        output_dir = str(GAMES_DIR / args.room_id)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "snapshot.json")
    else:
        output_path = os.path.join(export_dir, "snapshot.json")

    # Write output
    with open(output_path, "w") as f:
        json.dump(room_data, f, indent=2)

    item_count = len(room_data["roomItems"])
    print(f"Generated {item_count} room items")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
