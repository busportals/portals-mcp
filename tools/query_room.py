#!/usr/bin/env python3
"""
query_room.py — Query a Portals room snapshot for items matching filter criteria.

Returns specific items from a snapshot.json without loading the entire file into
context. Useful for AI agents that need selective access to room data.

Usage:
    # Get specific items by ID
    python tools/query_room.py games/{room-id}/snapshot.json --id 47 --id 48

    # Find all Triggers
    python tools/query_room.py games/{room-id}/snapshot.json --type Trigger

    # Spatial query — items within 5 units of a point
    python tools/query_room.py games/{room-id}/snapshot.json --near 10,0,15 --radius 5

    # Items with interactions
    python tools/query_room.py games/{room-id}/snapshot.json --has-triggers

    # Items referencing a quest
    python tools/query_room.py games/{room-id}/snapshot.json --quest "Main Quest"

    # Children of a parent item
    python tools/query_room.py games/{room-id}/snapshot.json --parent 12

    # Text search across all string fields
    python tools/query_room.py games/{room-id}/snapshot.json --search "door"

    # Combine filters (AND logic)
    python tools/query_room.py games/{room-id}/snapshot.json --type GLB --near 0,0,0 --radius 20

    # Importable usage
    from tools.query_room import query_items
    results = query_items("games/abc/snapshot.json", type=["GLB"], radius=10, near=(0, 0, 0))
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from portals_utils import normalize_snapshot


# ============================================================================
# Filtering Functions
# ============================================================================

def filter_by_id(item_id: str, item: dict, ids: list[str]) -> bool:
    """Match items with specific IDs."""
    return item_id in ids


def filter_by_type(item_id: str, item: dict, types: list[str]) -> bool:
    """Match items by prefabName. Case-sensitive."""
    return item.get("prefabName") in types


def filter_by_near(item_id: str, item: dict, center: tuple[float, float, float], radius: float) -> bool:
    """Match items within radius of a center point (Euclidean 3D distance)."""
    pos = item.get("pos")
    if pos is None:
        return False
    dx = pos.get("x", 0) - center[0]
    dy = pos.get("y", 0) - center[1]
    dz = pos.get("z", 0) - center[2]
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    return distance <= radius


def _get_interactions(item: dict) -> list:
    """Extract interactions from an item, supporting both formats.

    - Our format: item["interactions"] = [{trigger, effects}, ...]
    - MCP format: item["extraData"]["Tasks"] = [{Trigger, DirectEffector}, ...]
    """
    interactions = item.get("interactions")
    if interactions and isinstance(interactions, list):
        return interactions

    # MCP format: extraData is a JSON string containing Tasks
    ed = item.get("extraData", "")
    if isinstance(ed, str) and ed:
        try:
            parsed = json.loads(ed)
            tasks = parsed.get("Tasks", [])
            if tasks and isinstance(tasks, list):
                return tasks
            events = parsed.get("events", [])
            if events and isinstance(events, list):
                return events
        except (json.JSONDecodeError, ValueError):
            pass
    elif isinstance(ed, dict):
        tasks = ed.get("Tasks", [])
        if tasks and isinstance(tasks, list):
            return tasks

    return []


def filter_has_triggers(item_id: str, item: dict) -> bool:
    """Match items with at least one interaction trigger."""
    interactions = _get_interactions(item)
    return len(interactions) > 0


def filter_has_effects(item_id: str, item: dict) -> bool:
    """Match items with at least one effect in any interaction."""
    interactions = _get_interactions(item)
    for interaction in interactions:
        # Our format
        effects = interaction.get("effects")
        if effects and isinstance(effects, list) and len(effects) > 0:
            return True
        # MCP format
        direct = interaction.get("DirectEffector", {})
        if isinstance(direct, dict) and direct.get("Effector"):
            return True
    return False


def filter_by_quest(item_id: str, item: dict, quest_name: str) -> bool:
    """Match items whose interactions reference a quest name."""
    interactions = _get_interactions(item)
    if not interactions:
        return False
    quest_lower = quest_name.lower()
    for interaction in interactions:
        if _search_object_for_text(interaction, quest_lower):
            return True
    return False


def filter_by_parent(item_id: str, item: dict, parent_id: str) -> bool:
    """Match items that are children of the given parent ID.

    Supports both our format ("p") and MCP format ("parentItemID").
    """
    p = item.get("p")
    if p is not None and str(p) == parent_id:
        return True
    pid = item.get("parentItemID")
    if pid is not None and str(pid) == parent_id and str(pid) != "0":
        return True
    return False


def filter_by_search(item_id: str, item: dict, text: str) -> bool:
    """Case-insensitive text search across item string fields."""
    text_lower = text.lower()

    # Search prefabName
    prefab = item.get("prefabName", "")
    if isinstance(prefab, str) and text_lower in prefab.lower():
        return True

    # Search "t" (WorldText content)
    t_val = item.get("t", "")
    if isinstance(t_val, str) and text_lower in t_val.lower():
        return True

    # Search top-level string values
    for key, val in item.items():
        if key in ("prefabName", "t", "e", "extraData"):
            continue
        if isinstance(val, str) and text_lower in val.lower():
            return True

    # Search extraData — supports both "e" (our format) and "extraData" (MCP format)
    for ed_key in ("e", "extraData"):
        extra = item.get(ed_key)
        if isinstance(extra, str) and extra:
            try:
                parsed = json.loads(extra)
                if _search_object_for_text(parsed, text_lower):
                    return True
            except (json.JSONDecodeError, TypeError):
                if text_lower in extra.lower():
                    return True

    return False


# ============================================================================
# Helpers
# ============================================================================

def _search_object_for_text(obj: Any, text_lower: str) -> bool:
    """Recursively search an object for a case-insensitive text match in any string value."""
    if isinstance(obj, str):
        return text_lower in obj.lower()
    elif isinstance(obj, dict):
        for val in obj.values():
            if _search_object_for_text(val, text_lower):
                return True
    elif isinstance(obj, list):
        for val in obj:
            if _search_object_for_text(val, text_lower):
                return True
    return False


def parse_near(value: str) -> tuple[float, float, float]:
    """Parse a 'X,Y,Z' string into a tuple of three floats."""
    parts = value.split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(f"--near must be X,Y,Z (got '{value}')")
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError:
        raise argparse.ArgumentTypeError(f"--near values must be numbers (got '{value}')")


# ============================================================================
# Core Query Function (importable)
# ============================================================================

def query_items(
    snapshot_path: str,
    *,
    ids: Optional[list[str]] = None,
    types: Optional[list[str]] = None,
    near: Optional[tuple[float, float, float]] = None,
    radius: Optional[float] = None,
    has_triggers: bool = False,
    has_effects: bool = False,
    quest: Optional[str] = None,
    parent: Optional[str] = None,
    search: Optional[str] = None,
) -> dict:
    """
    Query a snapshot.json and return items matching all specified filters.

    Args:
        snapshot_path: Path to the snapshot.json file.
        ids: List of item IDs to match (OR within this filter).
        types: List of prefabName values to match (OR within this filter).
        near: Center point (x, y, z) for spatial query. Requires radius.
        radius: Radius for spatial query. Requires near.
        has_triggers: If True, only items with interactions.
        has_effects: If True, only items with effects in interactions.
        quest: Quest name to search for in interactions.
        parent: Parent item ID — returns children of this parent.
        search: Case-insensitive text search across string fields.

    Returns:
        Dict of matching items keyed by item ID, sorted numerically.

    Raises:
        FileNotFoundError: If snapshot_path does not exist.
        ValueError: If --near is given without --radius or vice versa.
        json.JSONDecodeError: If the snapshot is not valid JSON.
    """
    # Validate spatial query args
    if (near is not None) != (radius is not None):
        raise ValueError("--near requires --radius (and vice versa)")

    # Load snapshot
    path = Path(snapshot_path)
    with open(path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    normalize_snapshot(snapshot)  # Merge logic into items if new format

    room_items: dict = snapshot.get("roomItems", {})

    # Build filter list — each entry is a callable(item_id, item) -> bool
    filters: list = []

    if ids:
        filters.append(lambda iid, item: filter_by_id(iid, item, ids))

    if types:
        filters.append(lambda iid, item: filter_by_type(iid, item, types))

    if near is not None and radius is not None:
        filters.append(lambda iid, item: filter_by_near(iid, item, near, radius))

    if has_triggers:
        filters.append(lambda iid, item: filter_has_triggers(iid, item))

    if has_effects:
        filters.append(lambda iid, item: filter_has_effects(iid, item))

    if quest:
        filters.append(lambda iid, item: filter_by_quest(iid, item, quest))

    if parent is not None:
        filters.append(lambda iid, item: filter_by_parent(iid, item, parent))

    if search:
        filters.append(lambda iid, item: filter_by_search(iid, item, search))

    # Apply all filters (AND logic)
    matched: dict = {}
    for item_id, item in room_items.items():
        if all(f(item_id, item) for f in filters):
            matched[item_id] = item

    # Sort by numeric ID
    sorted_matched: dict = {}
    for key in sorted(matched.keys(), key=lambda k: int(k) if k.isdigit() else k):
        sorted_matched[key] = matched[key]

    return sorted_matched


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Query a Portals room snapshot.json for items matching filter criteria.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/query_room.py snapshot.json --id 47 --id 48
  python tools/query_room.py snapshot.json --type Trigger --type GLB
  python tools/query_room.py snapshot.json --near 10,0,15 --radius 5
  python tools/query_room.py snapshot.json --has-triggers
  python tools/query_room.py snapshot.json --quest "Main Quest"
  python tools/query_room.py snapshot.json --parent 12
  python tools/query_room.py snapshot.json --search "door"
  python tools/query_room.py snapshot.json --type GLB --near 0,0,0 --radius 20
        """,
    )

    parser.add_argument(
        "snapshot",
        type=str,
        help="Path to the snapshot.json file",
    )

    parser.add_argument(
        "--id",
        type=str,
        action="append",
        dest="ids",
        metavar="ID",
        help="Match specific item IDs (repeatable)",
    )

    parser.add_argument(
        "--type",
        type=str,
        action="append",
        dest="types",
        metavar="TYPE",
        help="Match by prefabName, e.g. Trigger, GLB, ResizableCube (repeatable)",
    )

    parser.add_argument(
        "--near",
        type=parse_near,
        default=None,
        metavar="X,Y,Z",
        help="Center point for spatial query (requires --radius)",
    )

    parser.add_argument(
        "--radius",
        type=float,
        default=None,
        metavar="R",
        help="Radius for spatial query (requires --near)",
    )

    parser.add_argument(
        "--has-triggers",
        action="store_true",
        default=False,
        help="Items with at least one interaction trigger",
    )

    parser.add_argument(
        "--has-effects",
        action="store_true",
        default=False,
        help="Items with at least one effect in any interaction",
    )

    parser.add_argument(
        "--quest",
        type=str,
        default=None,
        metavar="NAME",
        help="Items whose interactions reference this quest name",
    )

    parser.add_argument(
        "--parent",
        type=str,
        default=None,
        metavar="ID",
        help="All children of a parent item",
    )

    parser.add_argument(
        "--search",
        type=str,
        default=None,
        metavar="TEXT",
        help="Case-insensitive text search across item string fields",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Validate: at least one filter must be specified
    has_filter = any([
        args.ids,
        args.types,
        args.near is not None,
        args.radius is not None,
        args.has_triggers,
        args.has_effects,
        args.quest,
        args.parent,
        args.search,
    ])

    if not has_filter:
        print("ERROR: No filters specified. Use --help for filter options.", file=sys.stderr)
        return 1

    # Validate spatial query pairing
    if (args.near is not None) != (args.radius is not None):
        if args.near is not None:
            print("ERROR: --near requires --radius", file=sys.stderr)
        else:
            print("ERROR: --radius requires --near", file=sys.stderr)
        return 1

    # Run query
    try:
        results = query_items(
            args.snapshot,
            ids=args.ids,
            types=args.types,
            near=args.near,
            radius=args.radius,
            has_triggers=args.has_triggers,
            has_effects=args.has_effects,
            quest=args.quest,
            parent=args.parent,
            search=args.search,
        )
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.snapshot}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {args.snapshot}: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Output
    count = len(results)

    if count == 0:
        print("No items matched filters", file=sys.stderr)
        print("{}")
    else:
        if count > 50:
            print(f"WARNING: {count} items matched. Consider narrowing your filters.", file=sys.stderr)
        print(f"// Matched {count} items", file=sys.stderr)
        print(json.dumps(results, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
