#!/usr/bin/env python3
"""
merge_room.py — Apply a patch to an existing Portals room snapshot.json.

Enables AI agents to make targeted changes (add, modify, remove items/quests,
modify settings) without loading the entire snapshot into context. After merging,
re-generates the room index.

Usage:
    python tools/merge_room.py games/{room-id}/ --patch patch.json
    python tools/merge_room.py games/{room-id}/ --patch patch.json --dry-run
    python tools/merge_room.py games/{room-id}/ --patch patch.json --no-index

Patch format (all keys optional):
    {
        "add_items":       {"501": {...}, "502": {...}},
        "modify_items":    {"47": {"pos": {...}, "interactions": [...]}},
        "remove_items":    ["12", "13", "14"],
        "add_logic":       {"501": {"Tasks": [...], "col": "FF0000"}},
        "modify_logic":    {"47": {"col": "00FF00"}},
        "remove_logic":    ["12", "13"],
        "add_quests":      {"quest-uuid": {...}},
        "remove_quests":   ["quest-uuid-old"],
        "modify_settings": {"Variables": [...]}
    }

Operation order: remove -> modify -> add (items first, then logic, then quests, then settings)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from portals_utils import normalize_snapshot, split_logic_from_items


# ============================================================================
# Patch validation
# ============================================================================

VALID_PATCH_KEYS = {
    "add_items", "modify_items", "remove_items",
    "add_logic", "modify_logic", "remove_logic",
    "add_quests", "remove_quests", "modify_settings",
}


def validate_patch_structure(patch: dict) -> None:
    """Validate that the patch dict has only recognized keys and correct types."""
    for key in patch:
        if key not in VALID_PATCH_KEYS:
            raise ValueError(f"Unknown patch key: '{key}'. Valid keys: {sorted(VALID_PATCH_KEYS)}")

    if "add_items" in patch and not isinstance(patch["add_items"], dict):
        raise ValueError("add_items must be a dict of {id: item_data}")
    if "modify_items" in patch and not isinstance(patch["modify_items"], dict):
        raise ValueError("modify_items must be a dict of {id: partial_item_data}")
    if "remove_items" in patch and not isinstance(patch["remove_items"], list):
        raise ValueError("remove_items must be a list of item ID strings")
    if "add_quests" in patch and not isinstance(patch["add_quests"], dict):
        raise ValueError("add_quests must be a dict of {quest_id: quest_data}")
    if "remove_quests" in patch and not isinstance(patch["remove_quests"], list):
        raise ValueError("remove_quests must be a list of quest ID strings")
    if "add_logic" in patch and not isinstance(patch["add_logic"], dict):
        raise ValueError("add_logic must be a dict of {item_id: logic_dict}")
    if "modify_logic" in patch and not isinstance(patch["modify_logic"], dict):
        raise ValueError("modify_logic must be a dict of {item_id: logic_dict}")
    if "remove_logic" in patch and not isinstance(patch["remove_logic"], list):
        raise ValueError("remove_logic must be a list of item ID strings")
    if "modify_settings" in patch and not isinstance(patch["modify_settings"], dict):
        raise ValueError("modify_settings must be a dict of settings fields")


# ============================================================================
# Safety checks
# ============================================================================

def find_children(room_items: dict, parent_id: str) -> list[str]:
    """Find all item IDs that are children of parent_id.

    Supports both our format ('p') and MCP format ('parentItemID').
    """
    children = []
    for item_id, item_data in room_items.items():
        if not isinstance(item_data, dict):
            continue
        p = item_data.get("p")
        pid = item_data.get("parentItemID")
        if (p is not None and str(p) == str(parent_id)) or \
           (pid is not None and str(pid) == str(parent_id) and str(pid) != "0"):
            children.append(item_id)
    return children


def _get_interactions_from_item(item_data: dict) -> list:
    """Extract interactions from an item, supporting both formats."""
    interactions = item_data.get("interactions", [])
    if interactions and isinstance(interactions, list):
        return interactions

    ed = item_data.get("extraData", "")
    if isinstance(ed, str) and ed:
        try:
            parsed = json.loads(ed)
            tasks = parsed.get("Tasks", [])
            if tasks and isinstance(tasks, list):
                return tasks
        except (json.JSONDecodeError, ValueError):
            pass
    return []


def _search_for_id_in_obj(obj, target_id: str) -> bool:
    """Recursively search for target_id in any string field of an object."""
    if isinstance(obj, str):
        return str(target_id) in obj
    elif isinstance(obj, dict):
        for val in obj.values():
            if _search_for_id_in_obj(val, target_id):
                return True
    elif isinstance(obj, list):
        for val in obj:
            if _search_for_id_in_obj(val, target_id):
                return True
    return False


def find_quest_references(room_items: dict, target_id: str) -> list[str]:
    """Find item IDs whose interactions reference the target_id in effects.

    Supports both our format (effects array) and MCP format (DirectEffector).
    """
    referencing_items = []
    for item_id, item_data in room_items.items():
        if not isinstance(item_data, dict):
            continue
        interactions = _get_interactions_from_item(item_data)
        for interaction in interactions:
            if not isinstance(interaction, dict):
                continue

            # Our format: effects array
            effects = interaction.get("effects", [])
            if isinstance(effects, list):
                for effect in effects:
                    if not isinstance(effect, dict):
                        continue
                    if str(effect.get("TargetId", "")) == str(target_id):
                        referencing_items.append(item_id)
                        break
                    if _search_for_id_in_obj(effect, target_id):
                        referencing_items.append(item_id)
                        break
                else:
                    # MCP format: DirectEffector
                    direct = interaction.get("DirectEffector", {})
                    if isinstance(direct, dict) and _search_for_id_in_obj(direct, target_id):
                        referencing_items.append(item_id)
                        break
                    continue
                break
            else:
                # MCP format: DirectEffector
                direct = interaction.get("DirectEffector", {})
                if isinstance(direct, dict) and _search_for_id_in_obj(direct, target_id):
                    referencing_items.append(item_id)
                    break
    return referencing_items


def run_safety_checks(
    snapshot: dict,
    patch: dict,
) -> tuple[list[str], list[str]]:
    """
    Run all safety checks. Returns (errors, warnings).

    Checks performed:
    - remove_items: parent-child integrity
    - remove_items: quest interaction references (warning only)
    - add_items: no duplicate IDs
    - modify_items: items must exist
    - remove_quests: warning if quest not found
    """
    errors: list[str] = []
    warnings: list[str] = []

    room_items = snapshot.get("roomItems", {})
    quests = snapshot.get("quests", {})

    remove_ids = [str(x) for x in patch.get("remove_items", [])]
    add_ids = list(patch.get("add_items", {}).keys())
    modify_ids = list(patch.get("modify_items", {}).keys())
    remove_quest_ids = [str(x) for x in patch.get("remove_quests", [])]

    # --- remove_items checks ---
    for rid in remove_ids:
        # Parent-child check
        children = find_children(room_items, rid)
        orphans = [c for c in children if c not in remove_ids]
        if orphans:
            errors.append(
                f"Cannot remove item {rid}: it has children {orphans}. "
                f"Remove children first or include them in remove_items."
            )

        # Quest interaction reference check
        referencing = find_quest_references(room_items, rid)
        if referencing:
            warnings.append(
                f"WARNING: Removing item {rid} which is referenced in quest "
                f"interactions (by items: {referencing})."
            )

    # --- add_items checks ---
    for aid in add_ids:
        if str(aid) in room_items:
            errors.append(
                f"Cannot add item {aid}: already exists. "
                f"Use modify_items to change it."
            )

    # --- modify_items checks ---
    for mid in modify_ids:
        if str(mid) not in room_items:
            errors.append(
                f"Cannot modify item {mid}: not found. "
                f"Use add_items to create it."
            )

    # --- remove_quests checks ---
    for rqid in remove_quest_ids:
        if str(rqid) not in quests:
            warnings.append(
                f"WARNING: Quest {rqid} not found in quests dict."
            )

    return errors, warnings


# ============================================================================
# Merge operations
# ============================================================================

def apply_merge(snapshot: dict, patch: dict) -> dict:
    """
    Apply patch to snapshot in-place and return the modified snapshot.

    Operation order: remove -> modify -> add
    """
    room_items = snapshot.setdefault("roomItems", {})
    quests = snapshot.setdefault("quests", {})
    settings = snapshot.setdefault("settings", {})

    # 1. remove_items (also removes their embedded logic/extraData)
    for rid in patch.get("remove_items", []):
        rid = str(rid)
        room_items.pop(rid, None)

    # 2. modify_items (shallow merge at item top level)
    for mid, fields in patch.get("modify_items", {}).items():
        mid = str(mid)
        if mid in room_items:
            existing = room_items[mid]
            for key, value in fields.items():
                existing[key] = value

    # 3. add_items
    for aid, item_data in patch.get("add_items", {}).items():
        room_items[str(aid)] = item_data

    # 4. remove_quests
    for rqid in patch.get("remove_quests", []):
        rqid = str(rqid)
        quests.pop(rqid, None)

    # 5. add_quests
    for aqid, quest_data in patch.get("add_quests", {}).items():
        quests[str(aqid)] = quest_data

    # 6. modify_settings (shallow merge at settings top level)
    for key, value in patch.get("modify_settings", {}).items():
        settings[key] = value

    # 7. remove_logic — remove extraData from items
    for rid in patch.get("remove_logic", []):
        rid = str(rid)
        if rid in room_items:
            room_items[rid].pop("extraData", None)

    # 8. modify_logic — shallow merge into existing extraData
    for mid, logic_dict in patch.get("modify_logic", {}).items():
        mid = str(mid)
        if mid in room_items:
            item = room_items[mid]
            existing_ed = item.get("extraData", "")
            if isinstance(existing_ed, str) and existing_ed:
                try:
                    parsed = json.loads(existing_ed)
                except (json.JSONDecodeError, ValueError):
                    parsed = {}
            elif isinstance(existing_ed, dict):
                parsed = existing_ed
            else:
                parsed = {}
            parsed.update(logic_dict)
            item["extraData"] = json.dumps(parsed, separators=(',', ':'))

    # 9. add_logic — add extraData to items (serialize as JSON string)
    for aid, logic_dict in patch.get("add_logic", {}).items():
        aid = str(aid)
        if aid in room_items:
            room_items[aid]["extraData"] = json.dumps(logic_dict, separators=(',', ':'))

    return snapshot


# ============================================================================
# Dry-run report
# ============================================================================

def build_dry_run_report(snapshot: dict, patch: dict) -> str:
    """Build a human-readable report of what the merge would do."""
    lines = ["DRY RUN — no changes will be made", ""]

    room_items = snapshot.get("roomItems", {})
    quests = snapshot.get("quests", {})

    items_before = len(room_items)
    quests_before = len(quests)

    remove_ids = [str(x) for x in patch.get("remove_items", [])]
    modify_map = patch.get("modify_items", {})
    add_map = patch.get("add_items", {})
    remove_logic_ids = [str(x) for x in patch.get("remove_logic", [])]
    modify_logic_map = patch.get("modify_logic", {})
    add_logic_map = patch.get("add_logic", {})
    remove_quest_ids = [str(x) for x in patch.get("remove_quests", [])]
    add_quest_map = patch.get("add_quests", {})
    modify_settings = patch.get("modify_settings", {})

    has_changes = False

    # Remove items
    if remove_ids:
        has_changes = True
        lines.append(f"Would remove {len(remove_ids)} item(s): {', '.join(remove_ids)}")

    # Modify items
    if modify_map:
        has_changes = True
        lines.append(f"Would modify {len(modify_map)} item(s): {', '.join(modify_map.keys())}")
        for mid, fields in modify_map.items():
            mid = str(mid)
            for field_name in sorted(fields.keys()):
                existing_item = room_items.get(mid, {})
                old_val = existing_item.get(field_name)
                new_val = fields[field_name]
                detail = "replaced"
                if field_name == "interactions":
                    old_count = len(old_val) if isinstance(old_val, list) else 0
                    new_count = len(new_val) if isinstance(new_val, list) else 0
                    detail = f"replaced (was {old_count} interaction(s), now {new_count})"
                lines.append(f"  - {field_name}: {detail}")

    # Add items
    if add_map:
        has_changes = True
        lines.append(f"Would add {len(add_map)} item(s): {', '.join(add_map.keys())}")

    # Remove logic
    if remove_logic_ids:
        has_changes = True
        lines.append(f"Would remove logic from {len(remove_logic_ids)} item(s): {', '.join(remove_logic_ids)}")

    # Modify logic
    if modify_logic_map:
        has_changes = True
        lines.append(f"Would modify logic on {len(modify_logic_map)} item(s): {', '.join(modify_logic_map.keys())}")

    # Add logic
    if add_logic_map:
        has_changes = True
        lines.append(f"Would add logic to {len(add_logic_map)} item(s): {', '.join(add_logic_map.keys())}")

    # Remove quests
    if remove_quest_ids:
        has_changes = True
        lines.append(f"Would remove {len(remove_quest_ids)} quest(s): {', '.join(remove_quest_ids)}")

    # Add quests
    if add_quest_map:
        has_changes = True
        for aqid, qdata in add_quest_map.items():
            quest_name = qdata.get("Name", "unnamed")
            lines.append(f"Would add 1 quest: {aqid} ({quest_name})")

    # Modify settings
    if modify_settings:
        has_changes = True
        lines.append("Would modify settings:")
        for key in sorted(modify_settings.keys()):
            lines.append(f"  - {key}: replaced")

    if not has_changes:
        lines.append("No changes — patch is empty or contains only empty values.")
        return "\n".join(lines)

    # Calculate result counts
    items_after = items_before - len(remove_ids) + len(add_map)
    quests_after = quests_before - len(remove_quest_ids) + len(add_quest_map)

    lines.append("")
    lines.append(
        f"Result: {items_before} items -> {items_after} items, "
        f"{quests_before} quests -> {quests_after} quests"
    )

    return "\n".join(lines)


# ============================================================================
# Summary builder
# ============================================================================

def build_summary(
    snapshot_before: dict,
    snapshot_after: dict,
    patch: dict,
    room_dir: str,
    index_updated: bool,
) -> tuple[str, dict]:
    """Build a human-readable summary and a machine-readable summary dict."""
    items_before = len(snapshot_before.get("roomItems", {}))
    items_after = len(snapshot_after.get("roomItems", {}))
    quests_before = len(snapshot_before.get("quests", {}))
    quests_after = len(snapshot_after.get("quests", {}))

    removed_items = len(patch.get("remove_items", []))
    modified_items = len(patch.get("modify_items", {}))
    added_items = len(patch.get("add_items", {}))
    removed_logic = len(patch.get("remove_logic", []))
    modified_logic = len(patch.get("modify_logic", {}))
    added_logic = len(patch.get("add_logic", {}))
    removed_quests = len(patch.get("remove_quests", []))
    added_quests = len(patch.get("add_quests", {}))
    modified_settings = bool(patch.get("modify_settings"))

    parts = []
    parts.append("Merge complete:")

    removed_parts = []
    if removed_items:
        removed_parts.append(f"{removed_items} item(s)")
    if removed_logic:
        removed_parts.append(f"logic from {removed_logic} item(s)")
    if removed_quests:
        removed_parts.append(f"{removed_quests} quest(s)")
    if removed_parts:
        parts.append(f"  Removed: {', '.join(removed_parts)}")

    modified_parts = []
    if modified_items:
        modified_parts.append(f"{modified_items} item(s)")
    if modified_logic:
        modified_parts.append(f"logic on {modified_logic} item(s)")
    if modified_settings:
        modified_parts.append("settings")
    if modified_parts:
        parts.append(f"  Modified: {', '.join(modified_parts)}")

    added_parts = []
    if added_items:
        added_parts.append(f"{added_items} item(s)")
    if added_logic:
        added_parts.append(f"logic to {added_logic} item(s)")
    if added_quests:
        added_parts.append(f"{added_quests} quest(s)")
    if added_parts:
        parts.append(f"  Added: {', '.join(added_parts)}")

    parts.append(
        f"  Total: {items_before} -> {items_after} items, "
        f"{quests_before} -> {quests_after} quests"
    )

    if index_updated:
        index_path = os.path.join(room_dir, "room_index.md")
        parts.append(f"Room index updated: {index_path}")

    summary_dict = {
        "removed_items": removed_items,
        "modified_items": modified_items,
        "added_items": added_items,
        "removed_logic": removed_logic,
        "modified_logic": modified_logic,
        "added_logic": added_logic,
        "removed_quests": removed_quests,
        "added_quests": added_quests,
        "modified_settings": modified_settings,
        "items_before": items_before,
        "items_after": items_after,
        "quests_before": quests_before,
        "quests_after": quests_after,
        "index_updated": index_updated,
    }

    return "\n".join(parts), summary_dict


# ============================================================================
# Main merge function (importable)
# ============================================================================

def merge_room(
    room_dir: str,
    patch_data: dict,
    dry_run: bool = False,
    no_index: bool = False,
) -> dict:
    """
    Apply a patch to the snapshot.json in room_dir.

    Args:
        room_dir: Path to the room directory (must contain snapshot.json).
        patch_data: The patch dict (see module docstring for format).
        dry_run: If True, print what would happen without modifying files.
        no_index: If True, skip re-indexing after merge.

    Returns:
        A summary dict with counts of changes made.

    Raises:
        FileNotFoundError: If snapshot.json does not exist.
        ValueError: If patch structure is invalid or safety checks fail.
    """
    snapshot_path = os.path.join(room_dir, "snapshot.json")

    if not os.path.isfile(snapshot_path):
        raise FileNotFoundError(f"snapshot.json not found in {room_dir}")

    # Validate patch structure
    validate_patch_structure(patch_data)

    # Load snapshot
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    # Normalize: merge logic into items as extraData so processing code works
    normalize_snapshot(snapshot)

    # Run safety checks
    errors, warnings = run_safety_checks(snapshot, patch_data)

    # Print warnings to stderr
    for w in warnings:
        print(w, file=sys.stderr)

    # Abort on errors
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        raise ValueError(
            f"Safety checks failed with {len(errors)} error(s). Merge aborted."
        )

    if warnings:
        print(f"\nSafety checks: PASSED with {len(warnings)} warning(s)", file=sys.stderr)
    else:
        print("Safety checks: PASSED", file=sys.stderr)

    # Dry run
    if dry_run:
        report = build_dry_run_report(snapshot, patch_data)
        # Prepend safety check status
        print("", file=sys.stderr)
        print(report)
        return {
            "dry_run": True,
            "errors": len(errors),
            "warnings": len(warnings),
        }

    # Keep a copy of counts before merge for summary
    snapshot_before = {
        "roomItems": dict(snapshot.get("roomItems", {})),
        "quests": dict(snapshot.get("quests", {})),
    }

    # Apply merge
    apply_merge(snapshot, patch_data)

    # Convert back to new format: split extraData out into separate logic key
    split_logic_from_items(snapshot)

    # Write updated snapshot
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Re-index
    index_updated = False
    if not no_index:
        try:
            tools_dir = os.path.dirname(os.path.abspath(__file__))
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            from index_room import generate_index
            generate_index(snapshot_path)
            index_updated = True
        except ImportError:
            print(
                "WARNING: Could not import index_room.generate_index. "
                "Skipping re-index.",
                file=sys.stderr,
            )
        except Exception as e:
            print(
                f"WARNING: Re-indexing failed: {e}. Snapshot was saved successfully.",
                file=sys.stderr,
            )

    # Build and print summary
    summary_text, summary_dict = build_summary(
        snapshot_before, snapshot, patch_data, room_dir, index_updated
    )
    print(summary_text)

    return summary_dict


# ============================================================================
# CLI entry point
# ============================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply a patch to an existing Portals room snapshot.json.",
        epilog=(
            "Example:\n"
            "  python tools/merge_room.py games/abc123/ --patch patch.json\n"
            "  python tools/merge_room.py games/abc123/ --patch patch.json --dry-run\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "room_dir",
        help="Path to the room directory (must contain snapshot.json)",
    )
    parser.add_argument(
        "--patch",
        required=True,
        help="Path to the patch JSON file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would happen without modifying any files",
    )
    parser.add_argument(
        "--no-index",
        action="store_true",
        default=False,
        help="Skip re-indexing after merge",
    )

    args = parser.parse_args()

    # Validate room directory
    if not os.path.isdir(args.room_dir):
        print(f"ERROR: Room directory not found: {args.room_dir}", file=sys.stderr)
        sys.exit(1)

    # Validate and load patch file
    if not os.path.isfile(args.patch):
        print(f"ERROR: Patch file not found: {args.patch}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.patch, "r", encoding="utf-8") as f:
            patch_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Patch file is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(patch_data, dict):
        print("ERROR: Patch file must contain a JSON object at the top level.", file=sys.stderr)
        sys.exit(1)

    # Run merge
    try:
        merge_room(
            room_dir=args.room_dir,
            patch_data=patch_data,
            dry_run=args.dry_run,
            no_index=args.no_index,
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
