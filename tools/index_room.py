#!/usr/bin/env python3
"""
Portals Room Index Generator

Reads a Portals room snapshot.json and generates a compact room_index.md
with 5 layers of information. Designed to avoid loading full snapshots
(10K-28K lines) into AI agent context windows.

Layers:
  1. Summary       — item counts, variables, spawn, bounding box (~20 lines)
  2. Interactive    — every item with interactions (~50-100 lines)
  3. Spatial Map    — items grouped by 20x20 grid cells (~20-50 lines)
  4. Parent-Child   — items grouped by parent (~20-40 lines)
  5. Quests         — quest names, states, transitions (~30-60 lines)

Usage:
    python tools/index_room.py games/{room-id}/snapshot.json
    python tools/index_room.py games/{room-id}/snapshot.json --output /tmp/index.md

Can also be imported as a module:
    from index_room import generate_index
"""

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from portals_utils import normalize_snapshot


# ============================================================================
# CONSTANTS
# ============================================================================

# Trigger $type name shortcuts
TRIGGER_SHORT: Dict[str, str] = {
    "OnEnterEvent": "Enter",
    "OnExitEvent": "Exit",
    "OnClickEvent": "Click",
    "OnCollideEvent": "Collide",
    "OnStartEvent": "Start",
    "OnTimerEvent": "Timer",
    "ScoreTrigger": "ValueUpdated",
    "QuestTrigger": "Quest",
    "OnPointerEnterEvent": "PointerEnter",
    "OnPointerExitEvent": "PointerExit",
    "OnEquipEvent": "Equip",
    "OnUnequipEvent": "Unequip",
    "OnDeathEvent": "Death",
    "OnRespawnEvent": "Respawn",
    "OnGrabEvent": "Grab",
    "OnReleaseEvent": "Release",
    "OnPlayerJoinEvent": "PlayerJoin",
    "OnPlayerLeaveEvent": "PlayerLeave",
    "OnConsumeEvent": "Consume",
    "OnChatCommandEvent": "ChatCommand",
    "OnEmoteEvent": "Emote",
    "OnDamageEvent": "Damage",
    "OnHealEvent": "Heal",
}

# Effect $type name shortcuts
EFFECT_SHORT: Dict[str, str] = {
    "TeleportEvent": "Teleport",
    "PlaySoundOnce": "Sound",
    "PlaySoundInALoop": "SoundLoop",
    "StopSound": "StopSound",
    "UpdateScoreEvent": "UpdateScore",
    "UpdateScoreEventString": "UpdateScoreStr",
    "NotificationPillEvent": "Notification",
    "ShowObjectEvent": "Show",
    "HideObjectEvent": "Hide",
    "MoveToSpot": "Move",
    "FunctionEffector": "Function",
    "RunTriggersFromEffector": "RunTriggers",
    "PortalsAnimation": "Animation",
    "DuplicateItem": "Duplicate",
    "ChangePlayerHealth": "Health",
    "LockMovement": "LockMove",
    "UnlockMovement": "UnlockMove",
    "DisplayValueEvent": "DisplayValue",
    "HideValueEvent": "HideValue",
    "StartTimerEffect": "StartTimer",
    "StopTimerEffect": "StopTimer",
    "CancelTimerEffect": "CancelTimer",
    "AddVelocityToPlayer": "Velocity",
    "LockCamera": "LockCam",
    "UnlockCamera": "UnlockCam",
    "ChangeCameraZoom": "CamZoom",
    "ToggleFreeCam": "FreeCam",
    "ChangeCamState": "CamState",
    "SetCameraFilter": "CamFilter",
    "ShowOutline": "Outline",
    "HideOutline": "HideOutline",
    "MoveItemToPlayer": "MoveToPlayer",
    "DamageOverTime": "DOT",
    "PlayerEmote": "Emote",
    "MutePlayer": "Mute",
    "PostScoreToLeaderboard": "PostScore",
    "ClearLeaderboard": "ClearLB",
    "OpenLeaderboardEffect": "OpenLB",
    "ResetAllTasks": "ResetTasks",
    "ChangeAudiusEffect": "Audius",
    "StartAutoRun": "AutoRun",
    "StopAutoRun": "StopAutoRun",
    "ChangeMovementProfile": "MoveProfile",
    "HideAllPlayersEvent": "HidePlayers",
    "LockAvatarChange": "LockAvatar",
    "UnlockAvatarChange": "UnlockAvatar",
    "DisplayAvatarScreen": "AvatarScreen",
    "ChangeAvatarEffector": "ChangeAvatar",
    "ChangeRoundyWearableEffector": "Wearable",
    "ToggleLockCursor": "LockCursor",
}

# Prefab name abbreviations for compact display
PREFAB_SHORT: Dict[str, str] = {
    "ResizableCube": "Cube",
    "Addressable": "VFX",
    "GlbCollectable": "Collectible",
    "WorldText": "Text",
    "SpawnPoint": "Spawn",
    "DefaultPainting": "Image",
    "DefaultVideo": "Video",
    "PlaceableTV": "TV",
    "CameraObject": "Camera",
    "GLBNPC": "NPC",
    "GLBSign": "Sign",
    "BlinkLight": "BlinkLight",
    "SpotLight": "SpotLight",
    "Destructible": "Destructible",
}

# Grid cell size for spatial map (units on XZ plane)
GRID_CELL_SIZE = 20.0

# Minimum items in a grid cell before it gets merged
MERGE_THRESHOLD = 3


# ============================================================================
# HELPERS
# ============================================================================

def shorten_trigger(type_name: str) -> str:
    """Shorten a trigger $type name for display."""
    if type_name in TRIGGER_SHORT:
        return TRIGGER_SHORT[type_name]
    # Fallback: remove "Event" suffix and "On" prefix
    short = type_name
    if short.endswith("Event"):
        short = short[:-5]
    if short.startswith("On"):
        short = short[2:]
    return short


def shorten_effect(type_name: str) -> str:
    """Shorten an effect $type name for display."""
    if type_name in EFFECT_SHORT:
        return EFFECT_SHORT[type_name]
    # Fallback: remove "Event" or "Effect" suffix
    short = type_name
    if short.endswith("Event"):
        short = short[:-5]
    elif short.endswith("Effect"):
        short = short[:-6]
    return short


def shorten_prefab(prefab_name: str) -> str:
    """Shorten a prefab name for compact display."""
    return PREFAB_SHORT.get(prefab_name, prefab_name)


def get_pos(item: Dict[str, Any]) -> Tuple[float, float, float]:
    """Extract position from an item, defaulting to (0, 0, 0)."""
    pos = item.get("pos", {})
    return (
        float(pos.get("x", 0)),
        float(pos.get("y", 0)),
        float(pos.get("z", 0)),
    )


def fmt_pos(x: float, y: float, z: float) -> str:
    """Format a 3D position to 1 decimal place."""
    return f"({x:.1f}, {y:.1f}, {z:.1f})"


def fmt_pos_xz(x: float, z: float) -> str:
    """Format an XZ position to 1 decimal place."""
    return f"({x:.1f}, {z:.1f})"


def grid_key(x: float, z: float) -> Tuple[int, int]:
    """Convert world XZ to grid cell coordinates."""
    gx = int(math.floor(x / GRID_CELL_SIZE)) * int(GRID_CELL_SIZE)
    gz = int(math.floor(z / GRID_CELL_SIZE)) * int(GRID_CELL_SIZE)
    return (gx, gz)


def zone_name(gx: int, gz: int) -> str:
    """Generate a compass-style zone name from grid coordinates."""
    ns = ""
    ew = ""
    if gz < 0:
        ns = "S"
    elif gz > 0:
        ns = "N"

    if gx < 0:
        ew = "W"
    elif gx > 0:
        ew = "E"

    direction = ns + ew
    if not direction:
        direction = "Center"

    return f"{direction} ({gx}, {gz})"


def parse_extra_data(item: Dict[str, Any]) -> Dict[str, Any]:
    """Parse the extraData JSON string field if present."""
    ed = item.get("extraData", "")
    if isinstance(ed, str) and ed:
        try:
            return json.loads(ed)
        except (json.JSONDecodeError, ValueError):
            return {}
    elif isinstance(ed, dict):
        return ed
    return {}


def extract_interactions(item: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract the interactions list from an item.

    Supports two formats:
    - Our generate.py format: item["interactions"] = [{trigger, effects}, ...]
    - MCP format: item["extraData"]["Tasks"] = [{$type: TaskTriggerSubscription, Trigger, DirectEffector}, ...]
    """
    # Check our format first
    interactions = item.get("interactions", [])
    if interactions:
        return interactions

    # Check MCP format: extraData.Tasks
    ed = parse_extra_data(item)
    tasks = ed.get("Tasks", [])
    if tasks:
        return tasks

    # Also check extraData.events
    events = ed.get("events", [])
    if events:
        return events

    return []


def extract_trigger_type(interaction: Dict[str, Any]) -> str:
    """Extract the trigger $type from an interaction block.

    Supports three formats:
    - Our format: interaction["trigger"]["$type"]
    - MCP TaskTriggerSubscription: interaction["Trigger"]["$type"]
    - MCP TaskEffectorSubscription: quest-driven (no trigger, uses quest Name)
    """
    # Our format
    trigger = interaction.get("trigger", {})
    if isinstance(trigger, dict) and trigger.get("$type"):
        return trigger["$type"]

    # MCP format: TaskTriggerSubscription
    trigger = interaction.get("Trigger", {})
    if isinstance(trigger, dict) and trigger.get("$type"):
        return trigger["$type"]

    # MCP format: TaskEffectorSubscription (quest state change driven)
    if interaction.get("$type") == "TaskEffectorSubscription":
        quest_name = interaction.get("Name", "")
        if quest_name:
            parts = quest_name.split("_", 1)
            try:
                int(parts[0])
                short_name = parts[1] if len(parts) > 1 else quest_name
            except ValueError:
                short_name = quest_name
            return f"Quest({short_name})"
        return "QuestState"

    return "Unknown"


def extract_effects(interaction: Dict[str, Any]) -> List[str]:
    """Extract effect $type names from an interaction block.

    Supports two formats:
    - Our format: interaction["effects"] = [{$type, ...}, ...]
    - MCP format: interaction["DirectEffector"]["Effector"]["$type"] (single effect per task)
    """
    result = []

    # Our format: effects array
    effects = interaction.get("effects", [])
    if effects:
        for effect in effects:
            etype = effect.get("$type", "Unknown")
            result.append(etype)
        return result

    # MCP format: DirectEffector.Effector (single effect per TaskTriggerSubscription)
    direct = interaction.get("DirectEffector", {})
    if isinstance(direct, dict):
        effector = direct.get("Effector", {})
        if isinstance(effector, dict) and effector.get("$type"):
            result.append(effector["$type"])

    # MCP format: Effector (top-level on TaskEffectorSubscription)
    if not result:
        effector = interaction.get("Effector", {})
        if isinstance(effector, dict) and effector.get("$type"):
            result.append(effector["$type"])

    return result


def euclidean_xz(ax: float, az: float, bx: float, bz: float) -> float:
    """Euclidean distance on XZ plane."""
    return math.sqrt((ax - bx) ** 2 + (az - bz) ** 2)


# ============================================================================
# LAYER 1: SUMMARY
# ============================================================================

def build_summary(
    room_id: str,
    room_items: Dict[str, Dict],
    settings: Dict[str, Any],
    quests: Dict[str, Any],
) -> str:
    """Build the summary layer."""
    lines: List[str] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines.append(f"# Room Index: {room_id}")
    lines.append(f"Generated: {timestamp}")
    lines.append("")

    # Item stats
    item_count = len(room_items)
    if room_items:
        ids = sorted(int(k) for k in room_items.keys())
        id_range = f"{ids[0]}-{ids[-1]}"
    else:
        id_range = "none"

    # Quest count (deduplicate by Name for MCP format)
    quest_count = len(quests)
    if quests:
        sample = next(iter(quests.values()), {})
        if "Status" in sample and "Tasks" not in sample:
            unique_names = set(q.get("Name", "") for q in quests.values())
            unique_count = len(unique_names)
            if unique_count != quest_count:
                quest_count = unique_count  # Show unique count

    # Variables
    variables = settings.get("Variables", [])
    if variables:
        var_parts = []
        for v in variables:
            name = v.get("Name", "?")
            vtype = v.get("Type", "?")
            scope = v.get("Scope", "?")
            var_parts.append(f"{name} ({vtype}, {scope})")
        var_str = ", ".join(var_parts)
    else:
        var_str = "none"

    # Spawn
    spawn = settings.get("spawnPosition", None)
    if spawn and isinstance(spawn, dict):
        sx = float(spawn.get("x", 0))
        sy = float(spawn.get("y", 0))
        sz = float(spawn.get("z", 0))
        spawn_str = fmt_pos(sx, sy, sz)
    else:
        spawn_str = "not set"

    # Bounding box
    if room_items:
        all_x, all_y, all_z = [], [], []
        for item in room_items.values():
            px, py, pz = get_pos(item)
            all_x.append(px)
            all_y.append(py)
            all_z.append(pz)
        bb_min = fmt_pos(min(all_x), min(all_y), min(all_z))
        bb_max = fmt_pos(max(all_x), max(all_y), max(all_z))
    else:
        bb_min = fmt_pos(0, 0, 0)
        bb_max = fmt_pos(0, 0, 0)

    lines.append("## Overview")
    lines.append(f"- Items: {item_count} (ID range: {id_range})")
    lines.append(f"- Quests: {quest_count}")
    lines.append(f"- Variables: {var_str}")
    lines.append(f"- Spawn: {spawn_str}")
    lines.append(f"- Bounding box: {bb_min} to {bb_max}")
    lines.append("")

    # Item counts by type
    type_counts: Counter = Counter()
    for item in room_items.values():
        prefab = item.get("prefabName", "Unknown")
        type_counts[prefab] += 1

    lines.append("## Item Counts by Type")
    for prefab, count in type_counts.most_common():
        lines.append(f"  {prefab}: {count}")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# LAYER 2: INTERACTIVE ITEMS
# ============================================================================

def build_interactive(room_items: Dict[str, Dict]) -> str:
    """Build the interactive items layer."""
    lines: List[str] = []
    lines.append("## Interactive Items")

    # Collect interactive items
    interactive: List[Tuple[int, Dict]] = []
    for item_id_str, item in room_items.items():
        interactions = extract_interactions(item)
        if interactions:
            interactive.append((int(item_id_str), item))

    if not interactive:
        lines.append("No interactive items found.")
        lines.append("")
        return "\n".join(lines)

    interactive.sort(key=lambda x: x[0])

    # If too many interactive items, separate player-triggered from quest-driven
    # and only show player-triggered in detail (cap at 80 rows)
    MAX_INTERACTIVE_ROWS = 80
    if len(interactive) > MAX_INTERACTIVE_ROWS:
        # Separate: items with real player triggers vs quest-state-only items
        player_triggered = []
        quest_driven = []
        for item_id, item in interactive:
            interactions = extract_interactions(item)
            has_player_trigger = False
            for ix in interactions:
                ttype = extract_trigger_type(ix)
                if not ttype.startswith("Quest(") and ttype != "QuestState" and ttype != "Unknown":
                    has_player_trigger = True
                    break
            if has_player_trigger:
                player_triggered.append((item_id, item))
            else:
                quest_driven.append((item_id, item))

        if quest_driven:
            lines.append(f"_{len(interactive)} interactive items total. "
                         f"Showing {len(player_triggered)} player-triggered items. "
                         f"{len(quest_driven)} quest-driven items omitted (use query tool for details)._")
            lines.append("")
        interactive = player_triggered

    lines.append("| ID | Type | Position | Triggers | # Effects | Summary |")
    lines.append("|----|------|----------|----------|-----------|---------|")

    for item_id, item in interactive:
        prefab = shorten_prefab(item.get("prefabName", "?"))
        px, py, pz = get_pos(item)
        pos_str = fmt_pos(px, py, pz)

        interactions = extract_interactions(item)
        triggers: List[str] = []
        all_effects: List[str] = []

        for interaction in interactions:
            trigger_type = extract_trigger_type(interaction)
            triggers.append(shorten_trigger(trigger_type))
            effects = extract_effects(interaction)
            all_effects.extend(effects)

        trigger_str = ", ".join(triggers)
        effect_count = len(all_effects)

        # Deduplicate effect names for summary while preserving order
        seen = set()
        unique_effects: List[str] = []
        for e in all_effects:
            short = shorten_effect(e)
            if short not in seen:
                seen.add(short)
                unique_effects.append(short)
        summary_str = ", ".join(unique_effects)

        lines.append(
            f"| {item_id} | {prefab} | {pos_str} | {trigger_str} "
            f"| {effect_count} | {summary_str} |"
        )

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# LAYER 3: SPATIAL MAP
# ============================================================================

def build_spatial_map(room_items: Dict[str, Dict]) -> str:
    """Build the spatial map layer with 20x20 grid cells."""
    lines: List[str] = []
    lines.append("## Spatial Map")

    if not room_items:
        lines.append("No items to map.")
        lines.append("")
        return "\n".join(lines)

    # Assign items to grid cells
    cells: Dict[Tuple[int, int], List[Tuple[str, Dict]]] = defaultdict(list)
    for item_id_str, item in room_items.items():
        px, py, pz = get_pos(item)
        key = grid_key(px, pz)
        cells[key].append((item_id_str, item))

    # Merge small cells into nearest non-empty cell
    small_cells = [k for k, v in cells.items() if len(v) < MERGE_THRESHOLD]
    large_cells = [k for k, v in cells.items() if len(v) >= MERGE_THRESHOLD]

    if large_cells:
        for sk in small_cells:
            # Find nearest large cell
            sx, sz = sk
            best_key = None
            best_dist = float("inf")
            for lk in large_cells:
                lx, lz = lk
                d = euclidean_xz(float(sx), float(sz), float(lx), float(lz))
                if d < best_dist:
                    best_dist = d
                    best_key = lk
            if best_key is not None:
                cells[best_key].extend(cells[sk])
                del cells[sk]
    # If all cells are small (no large cells), keep them as-is

    # Build zone rows
    zone_rows: List[Tuple[str, str, int, str]] = []
    for (gx, gz), items in sorted(cells.items(), key=lambda x: (-len(x[1]), x[0])):
        name = zone_name(gx, gz)
        item_count = len(items)

        # Centroid (XZ only)
        sum_x, sum_z = 0.0, 0.0
        for _, item in items:
            px, py, pz = get_pos(item)
            sum_x += px
            sum_z += pz
        cx = sum_x / item_count
        cz = sum_z / item_count
        center_str = fmt_pos_xz(cx, cz)

        # Type breakdown (top 5, abbreviated)
        type_counter: Counter = Counter()
        for _, item in items:
            prefab = shorten_prefab(item.get("prefabName", "Unknown"))
            type_counter[prefab] += 1
        top5 = type_counter.most_common(5)
        breakdown_parts = [f"{count} {name}" for name, count in top5]
        remaining = item_count - sum(count for _, count in top5)
        if remaining > 0:
            breakdown_parts.append(f"{remaining} other")
        breakdown_str = ", ".join(breakdown_parts)

        zone_rows.append((name, center_str, item_count, breakdown_str))

    lines.append("| Zone | Center | Items | Breakdown |")
    lines.append("|------|--------|-------|-----------|")
    for name, center, count, breakdown in zone_rows:
        lines.append(f"| {name} | {center} | {count} | {breakdown} |")

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# LAYER 4: PARENT-CHILD GROUPS
# ============================================================================

def build_parent_child(room_items: Dict[str, Dict]) -> str:
    """Build the parent-child groups layer."""
    lines: List[str] = []
    lines.append("## Parent-Child Groups")

    # Build parent -> children mapping
    # Supports both our format ("p") and MCP format ("parentItemID")
    children_map: Dict[str, List[str]] = defaultdict(list)
    for item_id_str, item in room_items.items():
        parent_id = item.get("p") or item.get("parentItemID")
        if parent_id is not None and str(parent_id) != "0" and str(parent_id) != "":
            children_map[str(parent_id)].append(item_id_str)

    if not children_map:
        lines.append("No parent-child relationships found.")
        lines.append("")
        return "\n".join(lines)

    lines.append("| Parent ID | Type | Position | Children |")
    lines.append("|-----------|------|----------|----------|")

    # Sort by parent ID numerically
    for parent_id_str in sorted(children_map.keys(), key=lambda x: int(x)):
        parent_item = room_items.get(parent_id_str, {})
        parent_type = shorten_prefab(parent_item.get("prefabName", "?"))
        px, py, pz = get_pos(parent_item)
        pos_str = fmt_pos(px, py, pz)

        child_parts: List[str] = []
        for child_id in sorted(children_map[parent_id_str], key=lambda x: int(x)):
            child_item = room_items.get(child_id, {})
            child_type = shorten_prefab(child_item.get("prefabName", "?"))
            child_parts.append(f"{child_id} ({child_type})")
        children_str = ", ".join(child_parts)

        lines.append(f"| {parent_id_str} | {parent_type} | {pos_str} | {children_str} |")

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# LAYER 5: QUEST DETAILS
# ============================================================================

def build_quests(quests: Dict[str, Any]) -> str:
    """Build the quests layer.

    Supports two formats:
    - Our format: quest has "Tasks" array with TaskAction entries
    - MCP format: multiple quest entries with same Name but different "Status" fields
      (e.g. "inProgress", "completed"). Deduplicates by Name.
    """
    lines: List[str] = []
    lines.append("## Quests")

    if not quests:
        lines.append("No quests defined.")
        lines.append("")
        return "\n".join(lines)

    # First, detect format: MCP quests have "Status" field, ours have "Tasks" with TaskAction
    sample = next(iter(quests.values()), {})
    is_mcp_format = "Status" in sample and "Tasks" not in sample

    MAX_QUEST_ROWS = 50

    if is_mcp_format:
        # MCP format: deduplicate by Name, collect statuses
        quest_by_name: Dict[str, List[str]] = defaultdict(list)
        for quest_id, quest_data in quests.items():
            name = quest_data.get("Name", "unnamed")
            status = quest_data.get("Status", "unknown")
            quest_by_name[name].append(status)

        # Parse and sort by numeric prefix
        quest_entries: List[Tuple[int, str, List[str]]] = []
        for name, statuses in quest_by_name.items():
            parts = name.split("_", 1)
            try:
                num = int(parts[0])
                display_name = parts[1] if len(parts) > 1 else name
            except (ValueError, IndexError):
                num = 999
                display_name = name
            quest_entries.append((num, display_name, statuses))

        quest_entries.sort(key=lambda x: x[0])

        unique_count = len(quest_entries)

        if unique_count > MAX_QUEST_ROWS:
            # Group quests by name prefix pattern for compact display
            lines.append(f"_{unique_count} unique quests ({len(quests)} total entries). Showing grouped summary._")
            lines.append("")

            # Group by common prefix (e.g. "shield_1" -> "shield", "vis_b1_s1_t1" -> "vis")
            groups: Dict[str, int] = Counter()
            for num, display_name, statuses in quest_entries:
                # Use first word as group key
                group_key = display_name.split("_")[0] if "_" in display_name else display_name
                groups[group_key] += 1

            lines.append("| Group | Count | Example Names |")
            lines.append("|-------|-------|---------------|")
            for group_name, count in groups.most_common():
                # Find first 3 examples
                examples = [dn for _, dn, _ in quest_entries if dn.split("_")[0] == group_name][:3]
                example_str = ", ".join(examples)
                if count > 3:
                    example_str += ", ..."
                lines.append(f"| {group_name} | {count} | {example_str} |")
        else:
            lines.append("| # | Name | States | Transitions |")
            lines.append("|---|------|--------|-------------|")
            for num, display_name, statuses in quest_entries:
                status_order = {"notStarted": 0, "inProgress": 1, "completed": 2}
                unique_statuses = sorted(set(statuses), key=lambda s: status_order.get(s, 99))
                states_str = " -> ".join(unique_statuses) if unique_statuses else "none"
                lines.append(f"| {num} | {display_name} | {states_str} | — |")
    else:
        # Our format: Tasks array with TaskAction entries
        quest_entries_full: List[Tuple[int, str, Dict]] = []
        for quest_id, quest_data in quests.items():
            quest_name = quest_data.get("Name", "unnamed")
            parts = quest_name.split("_", 1)
            try:
                num = int(parts[0])
                display_name = parts[1] if len(parts) > 1 else quest_name
            except (ValueError, IndexError):
                num = 999
                display_name = quest_name
            quest_entries_full.append((num, display_name, quest_data))

        quest_entries_full.sort(key=lambda x: x[0])

        for num, display_name, quest_data in quest_entries_full:
            tasks = quest_data.get("Tasks", [])

            # Extract unique states in order of appearance
            states_seen: List[str] = []
            states_set: set = set()
            for task in tasks:
                action = task.get("TaskAction", "")
                if action and action not in states_set:
                    states_set.add(action)
                    states_seen.append(action)
            states_str = " -> ".join(states_seen) if states_seen else "none"

            # Extract transitions
            transitions: List[str] = []
            for task in tasks:
                target_state = task.get("TaskAction", "?")

                trigger_info = task.get("trigger", task.get("Trigger", {}))
                trigger_type = trigger_info.get("$type", "") if isinstance(trigger_info, dict) else ""

                item_id = task.get("ItemId", task.get("itemId", ""))

                score_name = task.get("ScoreName", task.get("scoreName", ""))
                score_value = task.get("ScoreValue", task.get("scoreValue", ""))
                score_comparison = task.get("Comparison", task.get("comparison", ""))

                if trigger_type:
                    short_trigger = shorten_trigger(trigger_type)
                    if item_id:
                        transitions.append(f"{short_trigger}({item_id}) -> {target_state}")
                    else:
                        transitions.append(f"{short_trigger} -> {target_state}")
                elif score_name:
                    comp_symbol = {
                        "GreaterThan": ">", "LessThan": "<", "EqualTo": "==",
                        "GreaterThanOrEqualTo": ">=", "LessThanOrEqualTo": "<=",
                        "NotEqualTo": "!=",
                    }.get(score_comparison, score_comparison)
                    transitions.append(f"{score_name} {comp_symbol} {score_value} -> {target_state}")
                elif item_id:
                    transitions.append(f"item({item_id}) -> {target_state}")

            # Limit to first 3 transitions
            if len(transitions) > 3:
                trans_str = ", ".join(transitions[:3]) + ", ..."
            elif transitions:
                trans_str = ", ".join(transitions)
            else:
                trans_str = "none"

            lines.append(f"| {num} | {display_name} | {states_str} | {trans_str} |")

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_index(snapshot_path: str, output_path: Optional[str] = None) -> str:
    """
    Generate a room index from a snapshot.json file.

    Args:
        snapshot_path: Path to the snapshot.json file.
        output_path: Optional output path. Defaults to room_index.md in the
                     same directory as the snapshot.

    Returns:
        The path to the generated index file.
    """
    snapshot_path = Path(snapshot_path).resolve()

    if not snapshot_path.exists():
        raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")

    # Determine room ID from directory name
    room_id = snapshot_path.parent.name

    # Determine output path
    if output_path:
        out = Path(output_path).resolve()
    else:
        out = snapshot_path.parent / "room_index.md"

    # Load snapshot
    with open(snapshot_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize format (handle both legacy and new logic-separated format)
    normalize_snapshot(data)

    room_items: Dict[str, Dict] = data.get("roomItems", {})
    settings: Dict[str, Any] = data.get("settings", {})
    quests: Dict[str, Any] = data.get("quests", {})

    # Build all layers
    sections: List[str] = [
        build_summary(room_id, room_items, settings, quests),
        build_interactive(room_items),
        build_spatial_map(room_items),
        build_parent_child(room_items),
        build_quests(quests),
    ]

    index_content = "\n".join(sections)

    # Write output
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(index_content)

    # Summary stats for stdout
    quest_count = len(quests)
    item_count = len(room_items)
    print(f"Index generated: {out} ({item_count} items, {quest_count} quests)")

    return str(out)


# ============================================================================
# CLI
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a compact room index from a Portals snapshot.json"
    )
    parser.add_argument(
        "snapshot",
        help="Path to the snapshot.json file",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for room_index.md (default: same dir as snapshot)",
        default=None,
    )

    args = parser.parse_args()

    try:
        generate_index(args.snapshot, args.output)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in snapshot — {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
