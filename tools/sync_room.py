#!/usr/bin/env python3
"""
sync_room.py — Sync manual editor changes into local project files.

When a user says "I made changes" in the Portals editor, this tool:
1. Diffs the current server state against the local snapshot
2. Generates an overrides.json that generators respect on regeneration
3. Updates the local snapshot.json with the server state
4. Re-indexes room_index.md

Usage:
    python tools/sync_room.py games/{room-id}/ --server-data /tmp/server.json
    python tools/sync_room.py games/{room-id}/ --server-data /tmp/server.json --dry-run
    python tools/sync_room.py games/{room-id}/ --clear-overrides

Workflow:
    1. Agent calls MCP get_room_data → gets temp file path
    2. Agent runs: python tools/sync_room.py games/{room-id}/ --server-data /tmp/xxx.json
    3. Tool diffs, writes overrides.json, updates snapshot.json, re-indexes
    4. Future generate.py runs call apply_overrides() to preserve manual edits
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from portals_utils import normalize_snapshot, split_logic_from_items


# ============================================================================
# Constants
# ============================================================================

# Tolerance for floating-point comparison
POS_TOLERANCE = 0.001
ROT_TOLERANCE = 0.0001
SCALE_TOLERANCE = 0.001

# Fields managed by the server — not relevant to game design diffs
IGNORED_FIELDS = {
    "extraData",     # handled separately as logic
    "id",            # same as dict key
    "roomItemId",    # same as dict key
    "updatedAt", "createdAt",
    "updatedBy", "createdBy",
    "version",
}

# Fields that are vector dicts {x, y, z} or {x, y, z, w}
VECTOR_FIELDS = {
    "pos": POS_TOLERANCE,
    "rot": ROT_TOLERANCE,
    "scl": SCALE_TOLERANCE,
}


# ============================================================================
# Data Loading
# ============================================================================

def load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def extract_items_and_logic(data: Dict) -> Tuple[Dict, Dict]:
    """
    Extract items and logic from room data, normalizing both formats.

    Handles:
    - Separated format: roomItems + logic (our generators)
    - Embedded format: roomItems with extraData (legacy/server)

    Returns (items, logic) where items have NO extraData
    and logic values are parsed dicts.
    """
    items = {}
    logic = {}

    # Copy items
    for item_id, item in data.get("roomItems", {}).items():
        items[str(item_id)] = dict(item)

    # Parse logic from separated logic key
    for item_id, entry in data.get("logic", {}).items():
        item_id = str(item_id)
        if isinstance(entry, str):
            try:
                logic[item_id] = json.loads(entry)
            except (json.JSONDecodeError, ValueError):
                logic[item_id] = entry
        elif isinstance(entry, dict):
            logic[item_id] = entry

    # Also extract embedded extraData from items
    for item_id, item in items.items():
        if "extraData" in item:
            ed = item.pop("extraData")
            if item_id not in logic:  # don't override separated logic
                if isinstance(ed, str) and ed:
                    try:
                        logic[item_id] = json.loads(ed)
                    except (json.JSONDecodeError, ValueError):
                        pass
                elif isinstance(ed, dict):
                    logic[item_id] = ed

    return items, logic


# ============================================================================
# Diff Engine
# ============================================================================

def vec_equal(a: Optional[Dict], b: Optional[Dict], tolerance: float) -> bool:
    """Compare two vector dicts ({x,y,z} or {x,y,z,w}) within tolerance."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if not isinstance(a, dict) or not isinstance(b, dict):
        return a == b
    all_keys = set(a.keys()) | set(b.keys())
    for key in all_keys:
        va = float(a.get(key, 0))
        vb = float(b.get(key, 0))
        if abs(va - vb) > tolerance:
            return False
    return True


def diff_item_fields(local_item: Dict, server_item: Dict) -> Dict:
    """
    Compare two items field by field. Returns dict of changed fields
    with their new (server) values. Empty dict means no changes.
    """
    changes = {}

    # Compare vector fields with tolerance
    for field, tolerance in VECTOR_FIELDS.items():
        lv = local_item.get(field)
        sv = server_item.get(field)
        if not vec_equal(lv, sv, tolerance):
            if sv is not None:
                changes[field] = sv
            elif lv is not None:
                # Field was removed on server
                changes[field] = None

    # Compare all other fields
    all_keys = set(local_item.keys()) | set(server_item.keys())
    for field in all_keys:
        if field in IGNORED_FIELDS or field in VECTOR_FIELDS:
            continue
        lv = local_item.get(field)
        sv = server_item.get(field)
        if lv != sv:
            if sv is not None:
                changes[field] = sv

    return changes


def diff_rooms(
    local_items: Dict, server_items: Dict,
    local_logic: Dict, server_logic: Dict,
) -> Dict:
    """
    Compute structured diff between local and server room data.

    Returns dict with keys:
        added: {item_id: {item: {...}, logic: {...}}} — items only on server
        removed: [item_id, ...] — items only in local (deleted by user)
        modified: {item_id: {field: new_value, ...}} — field-level item changes
        logic_replaced: {item_id: new_logic_dict_or_None} — logic that changed
    """
    local_ids = set(local_items.keys())
    server_ids = set(server_items.keys())

    added_ids = server_ids - local_ids
    removed_ids = local_ids - server_ids
    common_ids = local_ids & server_ids

    result = {
        "added": {},
        "removed": [],
        "modified": {},
        "logic_replaced": {},
    }

    # Added items (only on server — user created them in editor)
    for item_id in sorted(added_ids, key=lambda x: int(x)):
        entry = {"item": server_items[item_id]}
        if item_id in server_logic:
            entry["logic"] = server_logic[item_id]
        result["added"][item_id] = entry

    # Removed items (only in local — user deleted them in editor)
    result["removed"] = sorted(removed_ids, key=lambda x: int(x))

    # Modified items (exist in both — compare field by field)
    for item_id in sorted(common_ids, key=lambda x: int(x)):
        item_changes = diff_item_fields(local_items[item_id], server_items[item_id])
        if item_changes:
            result["modified"][item_id] = item_changes

        # Compare logic
        local_logic_entry = local_logic.get(item_id)
        server_logic_entry = server_logic.get(item_id)
        if local_logic_entry != server_logic_entry:
            # Full replacement — logic structures are complex, partial merging is risky
            result["logic_replaced"][item_id] = server_logic_entry  # None if removed

    return result


def diff_quests(local_quests: Dict, server_quests: Dict) -> Dict:
    """
    Compare quest dicts. Returns structured diff.

    Returns dict with keys:
        added: {quest_id: quest_data}
        removed: [quest_id, ...]
        modified: {quest_id: quest_data}  (full replacement for changed quests)
    """
    local_ids = set(local_quests.keys())
    server_ids = set(server_quests.keys())

    return {
        "added": {qid: server_quests[qid] for qid in sorted(server_ids - local_ids)},
        "removed": sorted(local_ids - server_ids),
        "modified": {
            qid: server_quests[qid]
            for qid in sorted(local_ids & server_ids)
            if local_quests[qid] != server_quests[qid]
        },
    }


def diff_settings(local_settings: Dict, server_settings: Dict) -> Dict:
    """Compare settings, return changed fields."""
    changes = {}
    all_keys = set(local_settings.keys()) | set(server_settings.keys())
    for key in all_keys:
        lv = local_settings.get(key)
        sv = server_settings.get(key)
        if lv != sv and sv is not None:
            changes[key] = sv
    return changes


# ============================================================================
# Report Formatting
# ============================================================================

def _fmt_pos(pos: Dict) -> str:
    if not pos or not isinstance(pos, dict):
        return "(?)"
    return f"({pos.get('x', 0):.1f}, {pos.get('y', 0):.1f}, {pos.get('z', 0):.1f})"


def _item_label(item: Dict) -> str:
    prefab = item.get("prefabName", "?")
    name = item.get("n", "")
    if name:
        return f'{prefab} "{name}"'
    return prefab


def format_diff_report(
    item_diff: Dict, quest_diff: Dict, settings_diff: Dict,
    local_items: Dict, server_items: Dict,
) -> str:
    """Generate a human-readable diff report."""
    lines = []

    # Count unique changes
    logic_only = set(item_diff["logic_replaced"].keys()) - set(item_diff["modified"].keys())
    item_changes = (
        len(item_diff["added"]) + len(item_diff["removed"])
        + len(item_diff["modified"]) + len(logic_only)
    )
    quest_changes = (
        len(quest_diff["added"]) + len(quest_diff["removed"])
        + len(quest_diff["modified"])
    )
    settings_changes = len(settings_diff)
    total = item_changes + quest_changes + settings_changes

    if total == 0:
        lines.append("No changes detected — server matches local snapshot.")
        return "\n".join(lines)

    lines.append(f"SYNC REPORT — {total} change(s) detected")
    lines.append("=" * 55)

    # --- Items ---
    if item_diff["added"]:
        lines.append(f"\nADDED ITEMS ({len(item_diff['added'])})")
        for item_id, entry in item_diff["added"].items():
            item = entry["item"]
            label = _item_label(item)
            pos_str = _fmt_pos(item.get("pos"))
            logic_note = " [has logic]" if entry.get("logic") else ""
            lines.append(f"  + {item_id} ({label}) at {pos_str}{logic_note}")

    if item_diff["removed"]:
        lines.append(f"\nREMOVED ITEMS ({len(item_diff['removed'])})")
        for item_id in item_diff["removed"]:
            item = local_items.get(item_id, {})
            label = _item_label(item)
            lines.append(f"  - {item_id} ({label})")

    if item_diff["modified"]:
        lines.append(f"\nMODIFIED ITEMS ({len(item_diff['modified'])})")
        for item_id, changes in item_diff["modified"].items():
            item = server_items.get(item_id, {})
            label = _item_label(item)
            change_keys = ", ".join(sorted(changes.keys()))
            lines.append(f"  ~ {item_id} ({label}): {change_keys}")

            # Detail for position changes
            if "pos" in changes:
                old_pos = local_items.get(item_id, {}).get("pos", {})
                new_pos = changes["pos"]
                lines.append(f"    pos: {_fmt_pos(old_pos)} → {_fmt_pos(new_pos)}")

            if "rot" in changes:
                lines.append(f"    rot: changed")

            if "scl" in changes:
                old_scl = local_items.get(item_id, {}).get("scl", {})
                new_scl = changes["scl"]
                lines.append(f"    scl: {_fmt_pos(old_scl)} → {_fmt_pos(new_scl)}")

            # Note logic changes for this item
            if item_id in item_diff["logic_replaced"]:
                entry = item_diff["logic_replaced"][item_id]
                if entry is None:
                    lines.append(f"    logic: REMOVED")
                else:
                    lines.append(f"    logic: CHANGED")

    if logic_only:
        lines.append(f"\nLOGIC-ONLY CHANGES ({len(logic_only)})")
        for item_id in sorted(logic_only, key=lambda x: int(x)):
            item = server_items.get(item_id, local_items.get(item_id, {}))
            label = _item_label(item)
            entry = item_diff["logic_replaced"][item_id]
            if entry is None:
                lines.append(f"  ~ {item_id} ({label}): logic REMOVED")
            else:
                lines.append(f"  ~ {item_id} ({label}): logic CHANGED")

    # --- Quests ---
    if quest_changes > 0:
        lines.append(f"\nQUEST CHANGES ({quest_changes})")
        for qid, qdata in quest_diff["added"].items():
            name = qdata.get("Name", "unnamed")
            lines.append(f"  + {name} ({qid})")
        for qid in quest_diff["removed"]:
            lines.append(f"  - {qid}")
        for qid, qdata in quest_diff["modified"].items():
            name = qdata.get("Name", "unnamed")
            lines.append(f"  ~ {name} ({qid})")

    # --- Settings ---
    if settings_changes > 0:
        lines.append(f"\nSETTINGS CHANGES ({settings_changes})")
        for key in sorted(settings_diff.keys()):
            lines.append(f"  ~ {key}")

    lines.append("\n" + "=" * 55)
    return "\n".join(lines)


# ============================================================================
# Overrides Management
# ============================================================================

def build_overrides(
    item_diff: Dict, quest_diff: Dict, settings_diff: Dict,
) -> Dict:
    """Convert diffs into overrides.json format."""
    overrides = {"_version": 1}

    if item_diff["modified"]:
        overrides["modified"] = item_diff["modified"]
    if item_diff["added"]:
        overrides["added"] = item_diff["added"]
    if item_diff["removed"]:
        overrides["removed"] = item_diff["removed"]
    if item_diff["logic_replaced"]:
        overrides["logic_replaced"] = item_diff["logic_replaced"]

    if quest_diff["added"] or quest_diff["removed"] or quest_diff["modified"]:
        overrides["quests"] = {}
        if quest_diff["added"]:
            overrides["quests"]["added"] = quest_diff["added"]
        if quest_diff["removed"]:
            overrides["quests"]["removed"] = quest_diff["removed"]
        if quest_diff["modified"]:
            overrides["quests"]["modified"] = quest_diff["modified"]

    if settings_diff:
        overrides["settings_modified"] = settings_diff

    return overrides


def merge_overrides(existing: Dict, new: Dict) -> Dict:
    """
    Merge new overrides into existing, with new taking precedence.
    Handles accumulation across multiple syncs.
    """
    result = dict(existing)
    result["_version"] = 1

    # Modified items: merge field-level (new fields override existing)
    existing_mod = dict(result.get("modified", {}))
    for item_id, fields in new.get("modified", {}).items():
        if item_id in existing_mod:
            existing_mod[item_id].update(fields)
        else:
            existing_mod[item_id] = fields
    if existing_mod:
        result["modified"] = existing_mod
    elif "modified" in result:
        del result["modified"]

    # Added items: new replaces existing
    existing_add = dict(result.get("added", {}))
    existing_add.update(new.get("added", {}))
    if existing_add:
        result["added"] = existing_add
    elif "added" in result:
        del result["added"]

    # Removed items: union, minus any re-added items
    existing_rem = set(result.get("removed", []))
    new_rem = set(new.get("removed", []))
    combined_rem = existing_rem | new_rem
    combined_rem -= set(result.get("added", {}).keys())
    if combined_rem:
        result["removed"] = sorted(combined_rem, key=lambda x: int(x))
    elif "removed" in result:
        del result["removed"]

    # Logic replaced: new replaces existing
    existing_logic = dict(result.get("logic_replaced", {}))
    existing_logic.update(new.get("logic_replaced", {}))
    if existing_logic:
        result["logic_replaced"] = existing_logic
    elif "logic_replaced" in result:
        del result["logic_replaced"]

    # Quest overrides: merge each sub-key
    existing_quests = dict(result.get("quests", {}))
    new_quests = new.get("quests", {})
    if new_quests:
        for sub_key in ("added", "modified"):
            eq = dict(existing_quests.get(sub_key, {}))
            eq.update(new_quests.get(sub_key, {}))
            if eq:
                existing_quests[sub_key] = eq
        eq_rem = set(existing_quests.get("removed", []))
        eq_rem |= set(new_quests.get("removed", []))
        eq_rem -= set(existing_quests.get("added", {}).keys())
        if eq_rem:
            existing_quests["removed"] = sorted(eq_rem)
        elif "removed" in existing_quests:
            del existing_quests["removed"]
    if existing_quests:
        result["quests"] = existing_quests
    elif "quests" in result:
        del result["quests"]

    # Settings: merge field-level
    existing_settings = dict(result.get("settings_modified", {}))
    existing_settings.update(new.get("settings_modified", {}))
    if existing_settings:
        result["settings_modified"] = existing_settings
    elif "settings_modified" in result:
        del result["settings_modified"]

    return result


# ============================================================================
# Main Sync
# ============================================================================

def sync_room(
    room_dir: str,
    server_data_path: str,
    dry_run: bool = False,
    no_overrides: bool = False,
) -> Dict:
    """
    Main sync function.

    Args:
        room_dir: Path to games/{room-id}/ directory
        server_data_path: Path to server data JSON (from MCP get_room_data)
        dry_run: If True, show diff without writing files
        no_overrides: If True, update snapshot but skip overrides.json

    Returns:
        Summary dict with status and change counts
    """
    room_dir = Path(room_dir)
    snapshot_path = room_dir / "snapshot.json"
    overrides_path = room_dir / "overrides.json"

    # Load server data
    server_data = load_json(server_data_path)
    server_items, server_logic = extract_items_and_logic(server_data)
    server_quests = server_data.get("quests", {})
    server_settings = server_data.get("settings", {})

    # No local snapshot — first sync
    if not snapshot_path.exists():
        print("No local snapshot found. Saving server data as initial snapshot.")
        if not dry_run:
            room_dir.mkdir(parents=True, exist_ok=True)
            save_json(str(snapshot_path), server_data)
            _reindex(str(snapshot_path))
        return {"status": "initial_sync", "changes": 0}

    # Load local snapshot
    local_data = load_json(str(snapshot_path))
    local_items, local_logic = extract_items_and_logic(local_data)
    local_quests = local_data.get("quests", {})
    local_settings = local_data.get("settings", {})

    # Compute diffs
    item_diff = diff_rooms(local_items, server_items, local_logic, server_logic)
    quest_diff = diff_quests(local_quests, server_quests)
    settings_diff = diff_settings(local_settings, server_settings)

    # Print report
    report = format_diff_report(
        item_diff, quest_diff, settings_diff,
        local_items, server_items,
    )
    print(report)

    # Count total changes
    logic_only = set(item_diff["logic_replaced"].keys()) - set(item_diff["modified"].keys())
    total = (
        len(item_diff["added"]) + len(item_diff["removed"])
        + len(item_diff["modified"]) + len(logic_only)
        + len(quest_diff["added"]) + len(quest_diff["removed"])
        + len(quest_diff["modified"])
        + len(settings_diff)
    )

    if total == 0:
        return {"status": "no_changes", "changes": 0}

    if dry_run:
        print("\nDRY RUN — no files modified.")
        return {"status": "dry_run", "changes": total}

    # Write overrides.json
    if not no_overrides:
        existing_overrides = {}
        if overrides_path.exists():
            existing_overrides = load_json(str(overrides_path))

        new_overrides = build_overrides(item_diff, quest_diff, settings_diff)
        merged = merge_overrides(existing_overrides, new_overrides)
        save_json(str(overrides_path), merged)
        print(f"\nOverrides written: {overrides_path}")

    # Update snapshot.json with server data
    save_json(str(snapshot_path), server_data)
    print(f"Snapshot updated: {snapshot_path}")

    # Re-index
    _reindex(str(snapshot_path))

    return {"status": "synced", "changes": total}


def _reindex(snapshot_path: str) -> None:
    """Re-index the room after sync."""
    try:
        tools_dir = os.path.dirname(os.path.abspath(__file__))
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from index_room import generate_index
        generate_index(snapshot_path)
    except Exception as e:
        print(f"WARNING: Re-indexing failed: {e}", file=sys.stderr)


# ============================================================================
# CLI
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync manual editor changes into local project files.",
        epilog=(
            "Examples:\n"
            "  python tools/sync_room.py games/abc123/ --server-data /tmp/server.json\n"
            "  python tools/sync_room.py games/abc123/ --server-data /tmp/server.json --dry-run\n"
            "  python tools/sync_room.py games/abc123/ --clear-overrides\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "room_dir",
        help="Path to the room directory (games/{room-id}/)",
    )
    parser.add_argument(
        "--server-data",
        help="Path to server data JSON file (from MCP get_room_data)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show diff without writing any files",
    )
    parser.add_argument(
        "--no-overrides",
        action="store_true",
        default=False,
        help="Update snapshot only, skip overrides.json generation",
    )
    parser.add_argument(
        "--clear-overrides",
        action="store_true",
        default=False,
        help="Delete overrides.json and exit (reset manual edits)",
    )

    args = parser.parse_args()

    # Handle --clear-overrides
    if args.clear_overrides:
        overrides_path = Path(args.room_dir) / "overrides.json"
        if overrides_path.exists():
            overrides_path.unlink()
            print(f"Overrides cleared: {overrides_path}")
        else:
            print("No overrides.json found — nothing to clear.")
        return

    # Validate args
    if not args.server_data:
        print("ERROR: --server-data is required (unless using --clear-overrides)", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(args.server_data):
        print(f"ERROR: Server data file not found: {args.server_data}", file=sys.stderr)
        sys.exit(1)

    # Run sync
    try:
        result = sync_room(
            room_dir=args.room_dir,
            server_data_path=args.server_data,
            dry_run=args.dry_run,
            no_overrides=args.no_overrides,
        )
        if result["status"] == "synced":
            print(f"\nSync complete: {result['changes']} change(s) applied.")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
