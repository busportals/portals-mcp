"""
Portals MCP Utilities
Provides helper functions for MCP operations, quest generation, and data validation.
"""

import os
import random
import string
import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================================
# Environment & Configuration
# ============================================================================

def load_access_key() -> str:
    """
    Load PORTALS_ACCESS_KEY from .env file.

    Returns:
        str: The access key

    Raises:
        FileNotFoundError: If .env file doesn't exist
        ValueError: If PORTALS_ACCESS_KEY not found in .env
    """
    env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        raise FileNotFoundError(f".env file not found at {env_path}")

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("PORTALS_ACCESS_KEY="):
                key = line.split("=", 1)[1]
                return key

    raise ValueError("PORTALS_ACCESS_KEY not found in .env file")


# ============================================================================
# Quest ID Generation
# ============================================================================

def generate_quest_id() -> str:
    """
    Generate a quest ID following the Portals format: mlh + 11-14 random lowercase alphanumeric chars.

    Returns:
        str: Quest ID like "mlh9kkyxvll8ql"
    """
    length = random.randint(11, 14)
    chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"mlh{chars}"


def create_quest_pair(
    number: int,
    name_suffix: str,
    creator: str,
    multiplayer: bool = False,
    auto_start: bool = False,
    visible: bool = False,
    display_group: str = "",
    requirements: Optional[List[Dict]] = None,
    repeatable_limit: int = 0,
    finish_time: int = 0,
    success_msg: str = "",
) -> Dict:
    """
    Create a quest pair in MCP flat-dict format.

    Each quest has an inProgress and completed entry that share the same EntryId
    but have DIFFERENT quest IDs (since they're keyed in a flat dict).

    Args:
        number: Quest number (0, 1, 2, etc.) for the name prefix
        name_suffix: Suffix for the quest name (e.g., "assemble", "collect")
        creator: The authenticated user's Firebase UID (required)
        multiplayer: If True, quest state is synced across all players
        auto_start: If True, quest activates when player enters room
        visible: If True, quest appears in player's quest log
        display_group: Group label for quest log UI (same value groups quests together)
        requirements: List of requirement dicts, e.g. [{"delete": False, "amount": 1, "type": "quest", "id": "mlh..."}]
        repeatable_limit: Max completions (0 = infinite, 1 = one-shot, N = max N)
        finish_time: Seconds before auto-expiry (0 = no time limit)
        success_msg: Message shown on completion (completed entry only)

    Returns:
        Dict with keys:
            - "entries": dict of {quest_id: quest_entry} for both entries (merge into quests dict)
            - "quest_id": the inProgress quest ID (for use in triggers/effects)
            - "quest_name": the full quest name (for use in triggers/effects)
    """
    entry_id = str(uuid.uuid4())
    id_progress = generate_quest_id()
    id_completed = generate_quest_id()
    quest_name = f"{number}_{name_suffix}"

    base = {
        "EntryId": entry_id,
        "Name": quest_name,
        "Description": "created in unity",
        "Group": "multiplayer" if multiplayer else "",
        "DisplayGroup": display_group,
        "Enabled": True,
        "RepeatableLimit": repeatable_limit,
        "FinishTime": finish_time,
        "AutoStart": auto_start,
        "TriggeredByInventory": False,
        "Requirements": requirements if requirements is not None else [],
        "Creator": creator,
        "TemplateName": "",
        "Tracked": True,
        "Visible": visible,
        "ExtraText": "",
    }

    entries = {
        id_progress: {**base, "Status": "inProgress", "id": id_progress},
        id_completed: {**base, "Status": "completed", "id": id_completed,
                       "Rewards": [], "SuccessMsg": success_msg},
    }

    return {
        "entries": entries,
        "quest_id": id_progress,
        "quest_name": quest_name
    }


# ============================================================================
# Geometry & Transformations
# ============================================================================

def quaternion_from_euler(yaw: float = 0.0, pitch: float = 0.0, roll: float = 0.0) -> Tuple[float, float, float, float]:
    """
    Convert Euler angles (degrees) to quaternion using Unity's ZXY rotation order.

    Args:
        yaw: Rotation around Y axis (degrees) - horizontal spin
        pitch: Rotation around X axis (degrees) - tilt forward/back
        roll: Rotation around Z axis (degrees) - tilt left/right

    Returns:
        Tuple (qx, qy, qz, qw)
    """
    import math

    yaw_rad = math.radians(yaw)
    pitch_rad = math.radians(pitch)
    roll_rad = math.radians(roll)

    cy = math.cos(yaw_rad * 0.5)
    sy = math.sin(yaw_rad * 0.5)
    cp = math.cos(pitch_rad * 0.5)
    sp = math.sin(pitch_rad * 0.5)
    cr = math.cos(roll_rad * 0.5)
    sr = math.sin(roll_rad * 0.5)

    # Unity ZXY extrinsic rotation order (= YXZ intrinsic)
    qw = cy * cp * cr + sy * sp * sr
    qx = cy * sp * cr + sy * cp * sr
    qy = sy * cp * cr - cy * sp * sr
    qz = cy * cp * sr - sy * sp * cr

    return (qx, qy, qz, qw)


def euler_from_quaternion(qx: float, qy: float, qz: float, qw: float) -> Tuple[float, float, float]:
    """
    Convert quaternion to Euler angles (degrees).

    Args:
        qx, qy, qz, qw: Quaternion components

    Returns:
        Tuple (yaw, pitch, roll) in degrees
    """
    import math

    # Roll (x-axis rotation)
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2 * (qw * qy - qz * qx)
    if abs(sinp) >= 1:
        pitch = math.copysign(math.pi / 2, sinp)
    else:
        pitch = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return (math.degrees(yaw), math.degrees(pitch), math.degrees(roll))


# ============================================================================
# Data Validation
# ============================================================================

def validate_color(color: str) -> bool:
    """
    Check if color is valid 6-char hex (no # prefix).

    Args:
        color: Color string to validate

    Returns:
        bool: True if valid
    """
    return len(color) == 6 and all(c in string.hexdigits for c in color)


def validate_quest_id(quest_id: str) -> bool:
    """
    Check if quest ID follows the mlh + alphanumeric format.

    Args:
        quest_id: Quest ID to validate

    Returns:
        bool: True if valid
    """
    if not quest_id.startswith("mlh"):
        return False
    suffix = quest_id[3:]
    return len(suffix) >= 11 and suffix.isalnum() and suffix.islower()


def validate_quest_name(quest_name: str) -> bool:
    """
    Check if quest name follows the numbered format (0_name, 1_name, etc.).

    Args:
        quest_name: Quest name to validate

    Returns:
        bool: True if valid
    """
    if "_" not in quest_name:
        return False
    prefix, suffix = quest_name.split("_", 1)
    return prefix.isdigit() and len(suffix) > 0


# ============================================================================
# Extra Data Helpers
# ============================================================================

def format_extra_data(data: Dict) -> str:
    """DEPRECATED: Use logic dicts directly.
    Convert dict to JSON string for extraData field.

    Args:
        data: Dictionary to convert

    Returns:
        str: JSON string with no whitespace
    """
    return json.dumps(data, separators=(',', ':'))


def parse_extra_data(data_str: str) -> Dict:
    """DEPRECATED: Use logic dicts directly.
    Parse extraData JSON string to dict.

    Args:
        data_str: JSON string from extraData field

    Returns:
        dict: Parsed data
    """
    return json.loads(data_str)


# ============================================================================
# Default Settings
# ============================================================================

def default_settings() -> Dict:
    """Return a complete default settings dict matching the Portals schema.
    Includes roomBase, top-level fields, and a full roomSettingsExtraData JSON string.
    Use this as a starting point — override individual fields as needed."""
    extra_data = {
        "welcomeEmbed": "",
        "openWelcomeIframeInBackground": False,
        "addWelcomeIframeToInfoButton": False,
        "showWelcomeOnEntry": False,
        "skyBoxDayTextureUrl": "",
        "skyBoxNightTextureUrl": "",
        "skyBoxDayRotation": 0,
        "skyBoxNightRotation": 0,
        "skyBoxDayExposure": 1.0,
        "skyBoxNightExposure": 1.0,
        "enableCustomAvatars": False,
        "defaultToReadyPlayerMe": False,
        "playerCollisions": True,
        "preloadRoom": False,
        "fastDownload": False,
        "allowedUsers": 0,
        "disableHToSpawn": False,
        "playJoinSound": True,
        "jumpSounds": False,
        "showNameTags": True,
        "showBackpack": True,
        "showQuestLog": False,
        "showPlayerCount": True,
        "showMic": True,
        "showMusic": True,
        "showEmotes": True,
        "showSpaceInfo": True,
        "requestMicPopup": False,
        "requireUsername": False,
        "releasedRoom": "",
        "uncompressedGLB": False,
        "movementValues": {
            "movementStateName": "",
            "walkByDefault": False,
            "walkSpeed": 2.0,
            "runSpeed": 4.0,
            "sprintSpeed": 6.8,
            "strafing": False,
            "jumpTimer": 0.3,
            "jumpHeight": 4.0,
            "airSpeed": 5.0,
            "gravity": -10.0,
            "rotationSpeed": 16.0,
            "ledgeGrab": False,
            "forceFirstPerson": False,
            "stopVerticalInput": False,
            "stopJumps": False,
        },
        "numericParameters": [],
        "fog": {
            "DayFogMax": 0.0,
            "NightFogMax": 0.0,
            "DayFogColor": "",
            "NightFogColor": "",
        },
        "postprocess": {
            "BloomDayIntensity": 0.0,
            "BloomNightIntensity": 0.0,
            "BloomDayClamp": 0.0,
            "BloomNightClamp": 0.0,
            "BloomDayDiffusion": 0.0,
            "BloomNightDiffusion": 0.0,
            "CameraMaxDistanceDay": 0.0,
            "CameraMaxDistanceNight": 0.0,
        },
        "lightValues": {"NightShadows": 0},
        "blockyAvatars": False,
        "rpmAvatars": False,
        "collectibleAvatars": False,
        "customAvatars": False,
        "roundyAvatars": False,
        "guardianAvatars": True,
        "psx": False,
        "pixelation": 0.24,
        "movementStates": [],
        "customSpaceAvatars": [],
        "customCameraStates": [],
        "weaponDatas": [],
        "defaultCameraState": -1,
        "defaultWeapon": -1,
        "defaultMovementState": -1,
        "EventData": json.dumps({"itemNames": [], "itemEvents": []}),
        "voiceChatRange": 14.0,
        "globalChat": False,
        "onboardingType": 1,
        "RoomItemsData": [],
        "carSettings": {
            "acceleration": 0,
            "drag": 0,
            "maxSpeed": 0,
            "steering": 0,
            "mass": 0,
            "gravity": 0,
            "timeToMaxSteer": 0,
        },
        "showCombatUI": False,
    }

    return {
        "roomBase": "BlankScene",
        "onlyNftHolders": False,
        "isNight": False,
        "wallIndex": 0,
        "inTownHallMode": False,
        "globalSpeaking": False,
        "audiusPlaylist": "",
        "chatDisabled": False,
        "allCanBuild": False,
        "roomPrompt": "",
        "roomSettingsExtraData": json.dumps(extra_data),
        "roomNodeExtraData": "",
        "bannedUsers": "",
        "shareLiveKitCrossInstances": False,
        "tokenImage": "",
        "tokenName": "",
        "tokenAddress": "",
        "tasksRefresh": True,
    }


# ============================================================================
# Format Conversion
# ============================================================================

def serialize_logic(data: Dict) -> Dict:
    """Serialize logic dict values to JSON strings for MCP output.
    The platform expects logic values as JSON strings, not raw dicts.
    Mutates data in-place."""
    logic = data.get("logic", {})
    for item_id, logic_entry in logic.items():
        if isinstance(logic_entry, dict):
            logic[item_id] = json.dumps(logic_entry, separators=(',', ':'))
    return data


def merge_logic_into_items(data: Dict) -> Dict:
    """Merge logic entries into items as extraData strings.
    Converts separated format to embedded format for tool consumption.
    Mutates data in-place."""
    logic = data.pop("logic", {})
    items = data.get("roomItems", {})
    # Logic entries for non-existent items are silently dropped.
    # This is intentional — MCP data may contain orphaned logic entries.
    for item_id, logic_entry in logic.items():
        if item_id in items:
            if isinstance(logic_entry, str):
                items[item_id]["extraData"] = logic_entry
            else:
                items[item_id]["extraData"] = json.dumps(logic_entry, separators=(',', ':'))
    return data


def split_logic_from_items(data: Dict) -> Dict:
    """Extract extraData from items into a separate logic dict.
    Converts embedded format to separated format.
    Mutates data in-place."""
    items = data.get("roomItems", {})
    logic = data.get("logic", {})
    for item_id, item in list(items.items()):
        if "extraData" in item:
            ed = item.pop("extraData")
            if isinstance(ed, str) and ed:
                logic[item_id] = json.loads(ed)
            elif isinstance(ed, dict):
                logic[item_id] = ed
    data["logic"] = logic
    return data


def normalize_snapshot(data: Dict) -> Dict:
    """Normalize snapshot for tool consumption.
    If data has a 'logic' key, merges logic into items as extraData
    so existing tool code works unchanged. If no 'logic' key,
    items already have extraData — nothing to do.
    Mutates data in-place."""
    if "logic" in data:
        merge_logic_into_items(data)
    return data


# ============================================================================
# Template Management
# ============================================================================

def load_template(template_name: str) -> Dict:
    """
    Load a pre-made template from docs/patterns/templates/.

    Args:
        template_name: Template filename (with or without .json extension)

    Returns:
        dict: Template data with keys like items, quests, variables

    Raises:
        FileNotFoundError: If template doesn't exist
    """
    if not template_name.endswith(".json"):
        template_name += ".json"

    template_path = Path(__file__).parent.parent / "docs" / "patterns" / "templates" / template_name

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    with open(template_path) as f:
        return json.load(f)


def save_template(template_name: str, data: Dict) -> None:
    """
    Save custom template to docs/patterns/templates/.

    Args:
        template_name: Template filename (with or without .json extension)
        data: Template data to save
    """
    if not template_name.endswith(".json"):
        template_name += ".json"

    template_path = Path(__file__).parent.parent / "docs" / "patterns" / "templates" / template_name
    template_path.parent.mkdir(parents=True, exist_ok=True)

    with open(template_path, 'w') as f:
        json.dump(data, f, indent=2)


# ============================================================================
# MCP Integration Notes
# ============================================================================

# NOTE: The actual MCP tool calls (mcp__portals__authenticate, mcp__portals__list_my_rooms, etc.)
# are made directly by Claude via the MCP protocol. These helper functions prepare data
# for those calls or process their results.

# For authentication, Claude will call:
#   mcp__portals__authenticate(accessKey=load_access_key())

# For listing rooms, Claude will call:
#   mcp__portals__list_my_rooms()

# For room data operations, Claude will call:
#   mcp__portals__get_room_items(roomId=room_id)
#   mcp__portals__set_room_items(roomId=room_id, data=items_dict)
#   mcp__portals__get_room_quests(roomId=room_id)
#   mcp__portals__set_room_quests(roomId=room_id, data=quests_dict)


# ============================================================================
# Validation Before Push
# ============================================================================

def validate_room_data(data: Dict) -> List[str]:
    """
    Validate room data before pushing to MCP.

    Args:
        data: Room data dict (may contain roomItems/items, logic, quests, settings)

    Returns:
        list: List of error messages (empty if valid)
    """
    errors = []

    # Accept both "items" and "roomItems" key names
    items_key = "roomItems" if "roomItems" in data else "items"
    items = data.get("roomItems", data.get("items", {}))
    if items and not isinstance(items, dict):
        errors.append(f"{items_key} must be a dict")
    elif isinstance(items, dict):
        for item_id, item in items.items():
            if not isinstance(item_id, str):
                errors.append(f"Item ID must be string, got {type(item_id)}")
            if "prefabName" not in item:
                errors.append(f"Item {item_id} missing prefabName")

    # Validate logic if present
    logic = data.get("logic", {})
    if logic and not isinstance(logic, dict):
        errors.append("logic must be a dict")
    elif isinstance(logic, dict):
        for item_id, entry in logic.items():
            if not isinstance(entry, dict):
                errors.append(f"Logic entry {item_id} must be a dict, got {type(entry)}")

    # Validate quests if present (MCP flat-dict format: {quest_id: quest_entry, ...})
    if "quests" in data:
        quests = data["quests"]
        if not isinstance(quests, dict):
            errors.append("quests must be a dict")
        else:
            for quest_id, quest in quests.items():
                if not validate_quest_id(quest_id):
                    errors.append(f"Quest has invalid ID key: {quest_id}")
                if quest.get("id") != quest_id:
                    errors.append(f"Quest id field ({quest.get('id')}) doesn't match dict key ({quest_id})")
                if "Name" in quest and not validate_quest_name(quest["Name"]):
                    errors.append(f"Quest has invalid name format: {quest.get('Name')} (should be 0_name, 1_name, etc.)")
                if not quest.get("Creator"):
                    errors.append(f"Quest {quest_id} missing Creator field (must be authenticated user's UID)")

    return errors


# ============================================================================
# Error Messages
# ============================================================================

def format_mcp_error(error_type: str, details: str = "") -> str:
    """
    Format MCP error messages for user-friendly display.

    Args:
        error_type: Error type (AUTH_REQUIRED, ROOM_NOT_FOUND, etc.)
        details: Additional details

    Returns:
        str: Formatted error message
    """
    messages = {
        "AUTH_REQUIRED": "Authentication required. I'll read your access key from the .env file.",
        "AUTH_FAILED": "Authentication failed. Please check your PORTALS_ACCESS_KEY in the .env file.",
        "ROOM_NOT_FOUND": "Room not found. Let me list your available rooms.",
        "FORBIDDEN": "You don't have permission to modify this room. You must be an owner or admin.",
        "VALIDATION_ERROR": f"Data validation failed: {details}",
        "INTERNAL_ERROR": f"Internal server error: {details}"
    }

    return messages.get(error_type, f"Unknown error: {error_type} - {details}")


# ============================================================================
# Build Summary Generation
# ============================================================================

# Prefab name → human-readable category
_PREFAB_CATEGORIES = {
    "ResizableCube": "cube",
    "GLB": "glb",
    "GLBNPC": "npc",
    "WorldText": "text",
    "SpawnPoint": "spawn",
    "Portal": "portal",
    "GlbCollectable": "collectible",
    "JumpPad": "jumppad",
    "Trigger": "trigger",
    "Light": "light",
    "SpotLight": "light",
    "BlinkLight": "light",
    "DefaultPainting": "image",
    "DefaultVideo": "video",
    "Gun": "gun",
    "Shotgun": "gun",
    "Destructible": "destructible",
    "9Cube": "elemental",
    "Addressable": "effect",
    "Leaderboard": "leaderboard",
}

# Trigger type names that indicate player interactions
_TRIGGER_TYPES = {
    "OnClickEvent", "OnCollideEvent", "OnCollisionStoppedEvent",
    "OnEnterEvent", "OnExitEvent",
    "OnHoverStartEvent", "OnHoverEndEvent",
    "OnKeyPressedEvent", "OnKeyReleasedEvent",
    "OnItemCollectedEvent", "OnItemClickEvent",
    "OnGunEquippedTrigger", "ShotHitTrigger", "GotKillTrigger",
}

# Effect type names for audio
_AUDIO_EFFECTS = {"PlaySoundOnce", "PlaySoundInALoop", "StopSound"}

# Effect type names for visual feedback
_VISUAL_EFFECTS = {
    "ShowObjectEvent", "HideObjectEvent", "ShowOutline", "HideOutline",
    "MoveToSpot", "DuplicateItem", "PlayAnimationOnce",
    "PlayerEmote", "NotificationPillEvent", "NPCMessageEvent",
}

# Effect type names for camera
_CAMERA_EFFECTS = {
    "SetCameraFilter", "ChangeCameraZoom", "ChangeBloom",
    "ChangeFog", "RotateSkybox", "LockCamera", "UnlockCamera",
}


def _count_types_in_logic(logic_entry: Dict) -> Dict[str, int]:
    """Count $type occurrences by category in a logic dict."""
    counts = {"triggers": 0, "audio": 0, "visual": 0, "camera": 0}
    if not logic_entry:
        return counts
    type_values = []
    _collect_types(logic_entry, type_values)
    for t in type_values:
        if t in _TRIGGER_TYPES:
            counts["triggers"] += 1
        if t in _AUDIO_EFFECTS:
            counts["audio"] += 1
        if t in _VISUAL_EFFECTS:
            counts["visual"] += 1
        if t in _CAMERA_EFFECTS:
            counts["camera"] += 1
    return counts


def _collect_types(obj, result: list):
    """Recursively collect all $type values from a nested structure."""
    if isinstance(obj, dict):
        if "$type" in obj:
            result.append(obj["$type"])
        for v in obj.values():
            _collect_types(v, result)
    elif isinstance(obj, list):
        for item in obj:
            _collect_types(item, result)


def _logic_has_type(logic_entry: Dict, type_name: str) -> bool:
    """Check if a logic entry contains a specific $type value."""
    if not logic_entry:
        return False
    type_vals = []
    _collect_types(logic_entry, type_vals)
    return type_name in type_vals


def _item_in_zone(item: Dict, bounds: Tuple[float, float, float, float]) -> bool:
    """Check if item position falls within zone bounds (x_min, x_max, z_min, z_max)."""
    pos = item.get("position", {})
    x = pos.get("x", 0)
    z = pos.get("z", 0)
    x_min, x_max, z_min, z_max = bounds
    return x_min <= x <= x_max and z_min <= z <= z_max


def generate_build_summary(
    game_name: str,
    items: Dict,
    logic: Dict,
    quests: Dict,
    zones: Optional[Dict[str, Tuple[float, float, float, float]]] = None,
    spectacle_moments: Optional[List[str]] = None,
) -> str:
    """
    Generate a compact build summary for quality review.

    The summary is designed to be passed to a review subagent (~200-300 tokens)
    instead of the full snapshot (~50K tokens). It provides enough information
    to identify quality gaps without overwhelming context.

    Args:
        game_name: Name of the game
        items: dict of room items (keyed by string IDs)
        logic: dict of logic entries (keyed by item ID, values are dicts)
        quests: dict of quest entries (keyed by quest IDs)
        zones: optional dict mapping zone names to (x_min, x_max, z_min, z_max) bounds.
               If not provided, zone breakdown is omitted.
        spectacle_moments: optional list of spectacle moment descriptions. These
               can't be auto-detected, so the generate.py author provides them.

    Returns:
        str: formatted build summary
    """
    lines = []
    lines.append(f"BUILD SUMMARY — {game_name}")
    lines.append("=" * 50)

    total_items = len(items)
    lines.append(f"Total Items: {total_items}")

    # --- Items by zone ---
    if zones:
        zone_counts = {}
        unzoned = 0
        for item in items.values():
            placed = False
            for zone_name, bounds in zones.items():
                if _item_in_zone(item, bounds):
                    zone_counts[zone_name] = zone_counts.get(zone_name, 0) + 1
                    placed = True
                    break
            if not placed:
                unzoned += 1
        zone_parts = [f"{name}({count})" for name, count in zone_counts.items()]
        if unzoned:
            zone_parts.append(f"unzoned({unzoned})")
        lines.append(f"Zones: {', '.join(zone_parts)}")
    lines.append("")

    # --- Items by type ---
    type_counts: Dict[str, int] = {}
    for item in items.values():
        prefab = item.get("prefabName", "unknown")
        category = _PREFAB_CATEGORIES.get(prefab, prefab.lower())
        type_counts[category] = type_counts.get(category, 0) + 1

    lines.append("By Type:")
    type_line_parts = [f"  {cat}: {count}" for cat, count in sorted(type_counts.items())]
    # Group into rows of 4 for readability
    for i in range(0, len(type_line_parts), 4):
        lines.append("  " + "  |".join(type_line_parts[i:i+4]))
    lines.append("")

    # --- Interaction analysis ---
    trigger_counts: Dict[str, int] = {}
    items_with_audio = 0
    items_with_visual = 0
    items_with_camera = 0
    items_with_interactions = 0

    for item_id, item in items.items():
        logic_entry = logic.get(item_id, {})
        counts = _count_types_in_logic(logic_entry)
        if counts["triggers"] > 0:
            items_with_interactions += 1
        if counts["audio"] > 0:
            items_with_audio += 1
        if counts["visual"] > 0:
            items_with_visual += 1
        if counts["camera"] > 0:
            items_with_camera += 1

        # Count individual trigger types
        if logic_entry:
            type_vals = []
            _collect_types(logic_entry, type_vals)
            for t in type_vals:
                if t in _TRIGGER_TYPES:
                    trigger_counts[t] = trigger_counts.get(t, 0) + 1

    lines.append("Interactions:")
    if trigger_counts:
        for trig, count in sorted(trigger_counts.items()):
            short = trig.replace("Event", "").replace("Trigger", "")
            lines.append(f"  {short}: {count}")
    else:
        lines.append("  (no item-level triggers found — check quest linkedTasks)")
    lines.append("")

    # --- Audio ---
    ambient_loops = 0
    oneshot_sounds = 0
    music_changes = 0
    for item_id in items:
        logic_entry = logic.get(item_id, {})
        if not logic_entry:
            continue
        type_vals = []
        _collect_types(logic_entry, type_vals)
        type_set = set(type_vals)
        if "PlaySoundInALoop" in type_set:
            ambient_loops += 1
        if "PlaySoundOnce" in type_set:
            oneshot_sounds += 1
        if "ChangeAudiusEffect" in type_set:
            music_changes += 1

    lines.append("Audio:")
    lines.append(f"  Ambient loops: {ambient_loops}  |  One-shot sounds: {oneshot_sounds}  |  Music changes: {music_changes}")
    lines.append("")

    # --- Quests ---
    total_quests = 0
    visible_quests = 0
    hidden_quests = 0
    # Count unique quests by EntryId (each quest has inProgress + completed entries)
    seen_entries = set()
    for quest in quests.values():
        entry_id = quest.get("EntryId", quest.get("id", ""))
        if entry_id in seen_entries:
            continue
        seen_entries.add(entry_id)
        total_quests += 1
        if quest.get("Visible", False):
            visible_quests += 1
        else:
            hidden_quests += 1

    lines.append("Quests:")
    lines.append(f"  Total: {total_quests}  |  Visible: {visible_quests}  |  Hidden: {hidden_quests}")
    lines.append("")

    # --- Feedback coverage ---
    total_interactive = max(items_with_interactions, 1)  # avoid division by zero
    lines.append("Feedback Coverage:")
    lines.append(f"  Actions with sound: {items_with_audio}/{items_with_interactions}")
    lines.append(f"  Actions with visual effects: {items_with_visual}/{items_with_interactions}")
    lines.append(f"  Actions with camera effects: {items_with_camera}/{items_with_interactions}")
    lines.append("")

    # --- Detail layers per zone ---
    if zones:
        lines.append("Detail Layers:")
        for zone_name, bounds in zones.items():
            zone_item_ids = [iid for iid, item in items.items() if _item_in_zone(item, bounds)]
            zone_items = [items[iid] for iid in zone_item_ids]
            has_structural = any(
                _PREFAB_CATEGORIES.get(i.get("prefabName", ""), "") in ("cube", "glb")
                for i in zone_items
            )
            has_functional = any(
                _PREFAB_CATEGORIES.get(i.get("prefabName", ""), "") in
                ("trigger", "collectible", "jumppad", "gun", "destructible", "portal")
                for i in zone_items
            )
            # Check for atmospheric: lights/effects or ambient sound loops in logic
            has_atmospheric = any(
                _PREFAB_CATEGORIES.get(items[iid].get("prefabName", ""), "") in ("light", "effect")
                or _logic_has_type(logic.get(iid, {}), "PlaySoundInALoop")
                for iid in zone_item_ids
            )
            has_decorative = any(
                _PREFAB_CATEGORIES.get(i.get("prefabName", ""), "") in
                ("npc", "image", "text", "video", "leaderboard")
                for i in zone_items
            )
            s = "Y" if has_structural else "N"
            f = "Y" if has_functional else "N"
            a = "Y" if has_atmospheric else "N"
            d = "Y" if has_decorative else "N"
            lines.append(f"  {zone_name}: structural={s} | functional={f} | atmospheric={a} | decorative={d}")
        lines.append("")

    # --- Spectacle moments ---
    if spectacle_moments:
        lines.append(f"Spectacle Moments: {len(spectacle_moments)} identified")
        for moment in spectacle_moments:
            lines.append(f"  - {moment}")
    else:
        lines.append("Spectacle Moments: 0 identified")
    lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)
