#!/usr/bin/env python3
"""
Portals Room Data Validator

Validates snapshot.json files for structural correctness and semantic validity
before pushing to rooms via MCP.

Usage:
    python tools/validate_room.py games/{room-id}/snapshot.json

Exit code 0 = no errors, 1 = errors found.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "lib"))

from portals_utils import validate_quest_name, validate_color, parse_extra_data, normalize_snapshot


# ============================================================================
# CONSTANTS
# ============================================================================

VALID_PREFAB_NAMES = {
    # Building
    "ResizableCube", "WorldText", "Portal", "SpawnPoint",
    # Models
    "GLB", "GlbCollectable", "Destructible", "GLBNPC",
    # Gameplay
    "Trigger", "JumpPad", "Gun", "Shotgun", "9Cube",
    # Lighting
    "Light", "BlinkLight", "SpotLight",
    # Media & Display
    "DefaultPainting", "DefaultVideo", "PlaceableTV",
    "Leaderboard", "Chart", "GLBSign",
    # Camera & Misc
    "CameraObject",
    # Visual Effects (Addressable)
    "Addressable",
}

# 63 confirmed effect $type values (does not include item-specific effects)
VALID_EFFECTS = {
    # Visibility
    "ShowObjectEvent", "HideObjectEvent", "ShowOutline", "HideOutline",
    # Movement & Transform
    "MoveToSpot", "PortalsAnimation", "DuplicateItem", "MoveItemToPlayer",
    # Player Effects
    "AddVelocityToPlayer", "TeleportEvent", "ChangePlayerHealth",
    "DamageOverTime", "LockMovement", "UnlockMovement",
    "StartAutoRun", "StopAutoRun", "PlayerEmote", "MutePlayer",
    "HideAllPlayersEvent", "LockAvatarChange", "UnlockAvatarChange",
    "DisplayAvatarScreen", "ChangeAvatarEffector", "ChangeMovementProfile",
    "ChangeRoundyWearableEffector",
    # Camera
    "LockCamera", "UnlockCamera", "ChangeCameraZoom", "ToggleFreeCam",
    "ChangeCamState", "SetCameraFilter", "ToggleLockCursor",
    # UI & Notifications
    "NotificationPillEvent",
    # Values (Variables)
    "DisplayValueEvent", "HideValueEvent", "UpdateScoreEvent", "UpdateScoreEventString",
    # Function Effects
    "FunctionEffector",
    # Quest/Task Control
    "RunTriggersFromEffector", "ResetAllTasks",
    # Timers
    "StartTimerEffect", "StopTimerEffect", "CancelTimerEffect",
    # Leaderboard
    "PostScoreToLeaderboard", "ClearLeaderboard", "OpenLeaderboardEffect",
    # Audio
    "PlaySoundOnce", "PlaySoundInALoop", "StopSound", "ChangeAudiusEffect",
    # Environment
    "ChangeBloom", "ChangeTimeOfDay", "RotateSkybox", "ChangeFog",
    # Communication
    "SendMessageToIframes", "ChangeVoiceGroup",
    # Iframes
    "IframeEvent", "IframeStopEvent",
    # NPC
    "NPCMessageEvent",
    # Token Swap
    "DisplaySellSwap", "HideSellSwap",
    # Dialogue
    "DialogEffectorDisplay",
    # Inventory
    "RefreshUserInventory",
    # Gun
    "EquipGunEffect", "TossGunEffect", "ResetGunEffect",
    # Trigger Zone
    "ActivateTriggerZoneEffect", "DeactivateTriggerZoneEffect",
    # GLB Animation
    "PlayAnimationOnce", "PlayAnimationInALoop", "StopGLBAnimation",
    # Destructible
    "RespawnDestructible",
}

# 23 confirmed trigger $type values
VALID_TRIGGERS = {
    # General (work on any item)
    "OnClickEvent", "OnCollideEvent", "OnCollisionStoppedEvent",
    "OnHoverStartEvent", "OnHoverEndEvent",
    "OnPlayerLoggedIn", "OnKeyPressedEvent", "OnKeyReleasedEvent",
    "OnPlayerDied", "OnPlayerRevived",
    "OnPlayerMove", "OnPlayerStoppedMoving",
    "OnMicrophoneUnmuted", "OnTimerStopped", "OnCountdownTimerFinished",
    "ScoreTrigger", "OnAnimationStoppedEvent", "OnItemCollectedEvent",
    "OnItemClickEvent", "PlayerLeave", "SwapVolume",
    # Trigger-cube-only (OnExitEvent is an alias for UserExitTrigger)
    "OnEnterEvent", "UserExitTrigger", "OnExitEvent",
    # Item-specific
    "OnDestroyedEvent",
    "OnGunEquippedTrigger", "ShotHitTrigger", "GotKillTrigger",
    "StartedAimingTrigger", "StoppedAimingTrigger", "OnGunTossedTrigger",
    "OnTakeDamageTrigger",
    "OnVehicleEntered", "OnVehicleExited",
    "OnNpcSentTag",
    "OnEnemyDied",
}

# Triggers that only work on Trigger items (invisible trigger cubes)
TRIGGER_CUBE_ONLY = {"OnEnterEvent", "UserExitTrigger", "OnExitEvent"}

# Triggers that require VISIBLE items (never on Trigger cubes)
VISIBLE_ONLY_TRIGGERS = {"OnClickEvent", "OnHoverStartEvent", "OnHoverEndEvent"}

# Valid encoded TargetState values for quest state transitions
VALID_LINKED_TASK_STATES = {101, 111, 121, 131, 141, 151, 161, 171, 181}

# Required parameters per effect type (only effects with mandatory params)
EFFECT_REQUIRED_PARAMS = {
    "MoveToSpot": ["_transformState"],
    "AddVelocityToPlayer": ["vel"],
    "TeleportEvent": ["id"],
    "ChangePlayerHealth": ["healthChange"],
    "PlayerEmote": ["animationName"],
    "ChangeAvatarEffector": ["Url"],
    "ChangeMovementProfile": ["mvmtProfile"],
    "ChangeRoundyWearableEffector": ["ItemID"],
    "ChangeCameraZoom": ["zoomAmount"],
    "ChangeCamState": ["camState"],
    "SetCameraFilter": ["url"],
    "ToggleLockCursor": ["lockCursor"],
    "NotificationPillEvent": ["nt"],
    "DisplayValueEvent": ["label"],
    "HideValueEvent": ["label"],
    "UpdateScoreEventString": ["targetText", "label"],
    "FunctionEffector": ["V"],
    "RunTriggersFromEffector": ["linkedTasks"],
    "StartTimerEffect": ["tn"],
    "StopTimerEffect": ["tn"],
    "CancelTimerEffect": ["tn"],
    "ClearLeaderboard": ["label"],
    "OpenLeaderboardEffect": ["lb"],
    "PlaySoundOnce": ["Url"],
    "PlaySoundInALoop": ["Url"],
    "StopSound": ["url"],
    "ChangeAudiusEffect": ["ap"],
    "ChangeBloom": ["Intensity"],
    "RotateSkybox": ["rotation"],
    "ChangeFog": ["color", "distance"],
    "SendMessageToIframes": ["iframeMsg"],
    "ChangeVoiceGroup": ["group"],
    "NPCMessageEvent": ["n", "m"],
    "IframeEvent": ["url"],
    "IframeStopEvent": ["iframeUrl"],
    "DisplaySellSwap": ["id"],
}

# Capitalization-sensitive parameters (common mistakes)
CASE_SENSITIVE_PARAMS = {
    "PlaySoundOnce": {"wrong": {"url": "Url", "dist": "Dist"}, "note": "uses capital Url and Dist"},
    "PlaySoundInALoop": {"wrong": {"url": "Url", "dist": "Dist"}, "note": "uses capital Url and Dist"},
    "StopSound": {"wrong": {"Url": "url"}, "note": "uses lowercase url"},
}

# Transform key confusion between effects
TRANSFORM_KEY_CHECKS = {
    "DuplicateItem": {"wrong_key": "_transformState", "correct_key": "TS"},
    "MoveToSpot": {"wrong_key": "TS", "correct_key": "_transformState"},
}

# Required extraData keys per prefab type
# NOTE: Light/SpotLight/BlinkLight brightness ("b" or "i") and range ("r") have engine
# defaults, so only keys essential for defining the item's purpose are required.
# SpawnPoint "n" is optional (missing = default spawn point).
ITEM_REQUIRED_EXTRA_KEYS = {
    "Trigger": ["keyCode"],
    "WorldText": ["text"],
    "GlbCollectable": ["valueLabel", "valueChange"],
    "GLBNPC": ["n"],
    "Destructible": ["maxHealth", "respawnTime"],
    "Portal": ["id"],
}

# Known Addressable VFX content string values (FurnitureAddressables/ prefix)
KNOWN_ADDRESSABLE_EFFECTS = {
    # Particles
    "DustParticles", "ParticlesExplosion1", "ParticlesExplosion2",
    "ParticlesExplosion3", "ParticlesExplosion4", "ParticlesExplosion5",
    # Fire
    "Fire", "Fire1", "Fire2", "Fire3", "FireBall1",
    # Explosion — Bomb
    "ExplosionBomb1", "ExplosionBomb2", "ExplosionBomb3", "ExplosionBomb4",
    "ExplosionBomb5", "ExplosionBomb6", "ExplosionBomb7",
    # Explosion — Ring
    "ExplosionRing1", "ExplosionRings2", "ExplosionRings3",
    # Explosion — Other
    "MagneticExplosion", "NuclearExplosion", "ShockExplosion",
    "SmokeExplosion1", "SmokeExplosion2", "WavesExplosion",
    # Lightning
    "LightningBall1", "LightningExplosion1", "LightningExplosion2",
    "LightningExplosion3", "LightningParticlesTree", "LightningShock1",
    "LightningStrike1", "LightningWave3", "LightningWaves2",
    # Energy
    "AtomBall1", "AtomBall2",
    # Other
    "LineWaves1", "Portal",
}

# Common color key mistakes for ResizableCube
CUBE_COLOR_MISTAKES = {"color", "colour", "Color", "Colour"}

# Known valid roomBase values
VALID_ROOM_BASES = {
    "BlankScene", "BlankSceneNight",
}

# Expected top-level settings keys (Portals schema)
# If none of these are present, the settings object is likely using a wrong format
SETTINGS_EXPECTED_KEYS = {
    "roomBase", "isNight", "roomSettingsExtraData",
    "wallIndex", "allCanBuild", "chatDisabled",
    "globalSpeaking", "inTownHallMode", "audiusPlaylist",
    "roomPrompt", "bannedUsers", "tasksRefresh",
    "onlyNftHolders", "roomNodeExtraData",
    "shareLiveKitCrossInstances",
    "tokenImage", "tokenName", "tokenAddress",
}

# Keys that indicate a wrong/custom settings format (game-design fields, not Portals schema)
SETTINGS_WRONG_KEYS = {
    "roomName", "description", "skybox", "fogDensity", "fogColor",
    "ambientColor", "ambientIntensity", "gravity",
}

# Quest ID pattern: starts with "m", followed by lowercase alphanumeric chars
# Our generator uses "mlh" prefix, but the Portals editor generates "mk", "ml", etc.
QUEST_ID_PATTERN = re.compile(r'^m[a-z0-9]{10,16}$')

# UUID pattern
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_quest_id(quest_id: str) -> bool:
    """Check if quest ID follows the Portals pattern: m + 10-16 lowercase alphanumeric."""
    return bool(QUEST_ID_PATTERN.match(quest_id))


def fmt(section: str, msg: str) -> str:
    """Format an error message."""
    return f"ERROR [{section}] {msg}"


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    return bool(UUID_PATTERN.match(value))


def safe_parse_extra_data(item_key: str, raw: str) -> tuple:
    """Parse extraData, returning (parsed_dict, error_or_None)."""
    if not raw:
        # Empty extraData string — editor-placed items may have this
        return {}, None
    try:
        return parse_extra_data(raw), None
    except (json.JSONDecodeError, TypeError) as e:
        return None, fmt(f"item {item_key}", f"extraData is not valid JSON: {e}")


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_top_level(data: dict) -> List[str]:
    """Validate top-level snapshot structure."""
    errors = []
    required_keys = {"roomItems", "settings", "roomTasks", "quests"}
    # "logic" is optional (stripped by normalize_snapshot)
    optional_keys = {"logic"}

    for key in required_keys:
        if key not in data:
            errors.append(fmt("root", f"missing required key: '{key}'"))

    if "roomTasks" in data:
        rt = data["roomTasks"]
        if not isinstance(rt, dict):
            errors.append(fmt("roomTasks", f"must be a dict, got {type(rt).__name__}"))
        elif rt != {"Tasks": []}:
            if "Tasks" not in rt:
                errors.append(fmt("roomTasks", 'must be {"Tasks": []}, not ' + json.dumps(rt)[:80]))
            elif not isinstance(rt["Tasks"], list):
                errors.append(fmt("roomTasks", '"Tasks" must be a list'))

    if "roomItems" in data:
        items = data["roomItems"]
        if not isinstance(items, dict):
            errors.append(fmt("roomItems", f"must be a dict, got {type(items).__name__}"))
        else:
            for key in items:
                if not isinstance(key, str) or not key.isdigit():
                    errors.append(fmt("roomItems", f"item key '{key}' must be a numeric string"))

    return errors


def validate_settings(settings: dict) -> List[str]:
    """Validate room settings structure and values."""
    errors = []

    if not isinstance(settings, dict):
        errors.append(fmt("settings", f"must be a dict, got {type(settings).__name__}"))
        return errors

    # Empty settings is always an error
    if not settings:
        errors.append(fmt("settings", 'settings is empty — use default_settings() from portals_utils to generate proper settings'))
        return errors

    # Check for wrong/custom format (game-design fields instead of Portals schema)
    present_keys = set(settings.keys())
    wrong_keys = present_keys & SETTINGS_WRONG_KEYS
    expected_keys = present_keys & SETTINGS_EXPECTED_KEYS

    if wrong_keys and not expected_keys:
        errors.append(fmt("settings", f"uses custom format (found {sorted(wrong_keys)}) instead of Portals schema — needs roomBase, isNight, roomSettingsExtraData, etc."))
        return errors

    if wrong_keys:
        for key in sorted(wrong_keys):
            errors.append(fmt("settings", f'unexpected key "{key}" — not a Portals settings field'))

    # roomBase validation
    if "roomBase" not in settings:
        errors.append(fmt("settings", 'missing "roomBase" — should be "BlankScene" or similar'))

    # roomSettingsExtraData validation
    if "roomSettingsExtraData" not in settings:
        errors.append(fmt("settings", 'missing "roomSettingsExtraData" — use default_settings() from portals_utils'))

    # tasksRefresh validation (must be boolean if present)
    tasks_refresh = settings.get("tasksRefresh")
    if tasks_refresh is not None and not isinstance(tasks_refresh, bool):
        errors.append(fmt("settings", f'tasksRefresh must be a boolean, got {type(tasks_refresh).__name__}'))

    # roomSettingsExtraData must be a JSON string if present
    rsed = settings.get("roomSettingsExtraData")
    if rsed is not None:
        if not isinstance(rsed, str):
            errors.append(fmt("settings", f"roomSettingsExtraData must be a JSON string, got {type(rsed).__name__}"))
        elif rsed:
            try:
                parsed = json.loads(rsed)
                if not isinstance(parsed, dict):
                    errors.append(fmt("settings", f"roomSettingsExtraData must parse to a dict, got {type(parsed).__name__}"))

                # Validate numericParameters format if present
                params = parsed.get("numericParameters", [])
                if not isinstance(params, list):
                    errors.append(fmt("settings", f"numericParameters must be a list, got {type(params).__name__}"))
                else:
                    for i, param in enumerate(params):
                        if not isinstance(param, dict):
                            errors.append(fmt("settings", f"numericParameters[{i}] must be a dict"))
                        elif "N" not in param:
                            errors.append(fmt("settings", f'numericParameters[{i}] missing "N" (variable name)'))
                        if isinstance(param, dict) and "VT" in param and not isinstance(param["VT"], int):
                            errors.append(fmt("settings", f'numericParameters[{i}] VT must be an integer, got {type(param["VT"]).__name__}'))

            except json.JSONDecodeError as e:
                errors.append(fmt("settings", f"roomSettingsExtraData is not valid JSON: {e}"))

    return errors


def validate_item_structure(item_key: str, item: dict, all_keys: Set[str]) -> List[str]:
    """Validate an item's required fields and types."""
    errors = []
    section = f"item {item_key}"

    # Required fields
    if "prefabName" not in item:
        errors.append(fmt(section, "missing 'prefabName'"))
    elif item["prefabName"] not in VALID_PREFAB_NAMES:
        errors.append(fmt(section, f"invalid prefabName '{item['prefabName']}' — not a known item type"))

    # Position
    if "pos" not in item:
        errors.append(fmt(section, "missing 'pos'"))
    elif isinstance(item["pos"], dict):
        for axis in ("x", "y", "z"):
            if axis not in item["pos"]:
                errors.append(fmt(section, f"pos missing '{axis}' component"))

    # Rotation
    if "rot" not in item:
        errors.append(fmt(section, "missing 'rot'"))
    elif isinstance(item["rot"], dict):
        for axis in ("x", "y", "z", "w"):
            if axis not in item["rot"]:
                errors.append(fmt(section, f"rot missing '{axis}' component"))

    # Scale
    if "scale" not in item:
        errors.append(fmt(section, "missing 'scale'"))
    elif isinstance(item["scale"], dict):
        for axis in ("x", "y", "z"):
            if axis not in item["scale"]:
                errors.append(fmt(section, f"scale missing '{axis}' component"))

    # extraData
    if "extraData" not in item:
        errors.append(fmt(section, "missing 'extraData'"))
    elif not isinstance(item["extraData"], str):
        errors.append(fmt(section, f"extraData must be a JSON string, got {type(item['extraData']).__name__}"))

    # parentItemID
    parent_id = item.get("parentItemID", 0)
    if parent_id != 0:
        parent_key = str(parent_id)
        if parent_key not in all_keys:
            errors.append(fmt(section, f"parentItemID {parent_id} references non-existent item"))

    return errors


def validate_item_extra_data(item_key: str, prefab: str, extra: dict, content_string: str) -> List[str]:
    """Validate item-specific extraData fields."""
    errors = []
    section = f"item {item_key}, {prefab}"

    # ResizableCube color checks
    if prefab == "ResizableCube":
        # Check for common color key mistakes
        for mistake in CUBE_COLOR_MISTAKES:
            if mistake in extra:
                errors.append(fmt(section, f'extraData uses "{mistake}" for color — should be "col"'))

        # Check if "c" is being used as a color string (it should be a bool for collider)
        if "c" in extra and isinstance(extra["c"], str):
            errors.append(fmt(section, 'extraData uses "c" (string) for color — should be "col". "c" is the collider toggle (bool)'))

        # Validate color value if present
        if "col" in extra and isinstance(extra["col"], str):
            if not validate_color(extra["col"]):
                errors.append(fmt(section, f'invalid color value "{extra["col"]}" — must be 6-char hex (e.g., "FF0000")'))

    # Content string checks for URL-based items
    if prefab in ("GLB", "GLBNPC", "DefaultPainting", "DefaultVideo"):
        if not content_string:
            errors.append(fmt(section, "contentString is empty — must be a URL"))

    if prefab == "GlbCollectable":
        if not content_string:
            errors.append(fmt(section, "contentString is empty — must be a GLB URL"))
        elif "?dynamic=true" not in content_string:
            errors.append(fmt(section, "contentString missing '?dynamic=true' suffix"))

    # Required extraData keys per prefab
    if prefab in ITEM_REQUIRED_EXTRA_KEYS:
        for key in ITEM_REQUIRED_EXTRA_KEYS[prefab]:
            if key not in extra:
                errors.append(fmt(section, f'extraData missing required key "{key}"'))

    # Addressable VFX validation
    if prefab == "Addressable":
        if not content_string:
            errors.append(fmt(section, "contentString is empty — must be FurnitureAddressables/{EffectName}"))
        elif not content_string.startswith("FurnitureAddressables/"):
            errors.append(fmt(section, f'contentString "{content_string}" missing "FurnitureAddressables/" prefix'))
        else:
            effect_name = content_string.replace("FurnitureAddressables/", "", 1)
            if effect_name not in KNOWN_ADDRESSABLE_EFFECTS:
                # Warn but don't error — new effects may be added by Portals
                pass  # Unknown effect names are allowed (catalog may be incomplete)

    # Light color validation
    if prefab in ("Light", "SpotLight", "BlinkLight"):
        if "c" in extra and isinstance(extra["c"], str):
            if not validate_color(extra["c"]):
                errors.append(fmt(section, f'invalid light color "{extra["c"]}" — must be 6-char hex'))

    return errors


def validate_effect_params(item_key: str, prefab: str, effect_type: str, effect: dict) -> List[str]:
    """Validate effect-specific parameters."""
    errors = []
    section = f"item {item_key}, {prefab}"

    # Required parameters
    if effect_type in EFFECT_REQUIRED_PARAMS:
        for param in EFFECT_REQUIRED_PARAMS[effect_type]:
            if param not in effect:
                errors.append(fmt(section, f'{effect_type} missing required param "{param}"'))

    # Case-sensitive parameter checks
    if effect_type in CASE_SENSITIVE_PARAMS:
        rules = CASE_SENSITIVE_PARAMS[effect_type]
        for wrong, correct in rules["wrong"].items():
            if wrong in effect and correct not in effect:
                errors.append(fmt(section, f'{effect_type} uses "{wrong}" — should be "{correct}" ({rules["note"]})'))

    # Transform key confusion
    if effect_type in TRANSFORM_KEY_CHECKS:
        check = TRANSFORM_KEY_CHECKS[effect_type]
        if check["wrong_key"] in effect:
            errors.append(fmt(section, f'{effect_type} uses "{check["wrong_key"]}" — should be "{check["correct_key"]}"'))

    # RunTriggersFromEffector: validate linkedTasks
    if effect_type == "RunTriggersFromEffector" and "linkedTasks" in effect:
        for i, lt in enumerate(effect["linkedTasks"]):
            if "TargetState" in lt and lt["TargetState"] not in VALID_LINKED_TASK_STATES:
                errors.append(fmt(section, f'RunTriggersFromEffector linkedTasks[{i}] has invalid TargetState {lt["TargetState"]} — valid: {sorted(VALID_LINKED_TASK_STATES)}'))

    return errors


def validate_item_tasks(item_key: str, prefab: str, tasks: list) -> List[str]:
    """Validate triggers and effects in an item's Tasks array."""
    errors = []
    section = f"item {item_key}, {prefab}"

    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(fmt(section, f"Tasks[{i}] is not a dict"))
            continue

        task_type = task.get("$type", "")

        if task_type == "TaskEffectorSubscription":
            # Validate effector
            effector = task.get("Effector")
            if not effector or not isinstance(effector, dict):
                errors.append(fmt(section, f"Tasks[{i}] TaskEffectorSubscription missing Effector"))
            else:
                etype = effector.get("$type", "")
                if etype not in VALID_EFFECTS:
                    errors.append(fmt(section, f'Tasks[{i}] unknown effect type "{etype}"'))
                else:
                    errors.extend(validate_effect_params(item_key, prefab, etype, effector))

            # Validate quest linkage
            if "TaskTriggerId" in task and task["TaskTriggerId"]:
                if not validate_quest_id(task["TaskTriggerId"]):
                    errors.append(fmt(section, f'Tasks[{i}] TaskTriggerId "{task["TaskTriggerId"]}" is not a valid quest ID (should be mlh + alphanumeric)'))
                if "Name" in task and task["Name"] and not validate_quest_name(task["Name"]):
                    errors.append(fmt(section, f'Tasks[{i}] quest Name "{task["Name"]}" should follow N_suffix format (e.g., "0_activate")'))

        elif task_type == "TaskTriggerSubscription":
            # Validate trigger
            trigger = task.get("Trigger")
            if not trigger or not isinstance(trigger, dict):
                errors.append(fmt(section, f"Tasks[{i}] TaskTriggerSubscription missing Trigger"))
            else:
                ttype = trigger.get("$type", "")
                if ttype not in VALID_TRIGGERS:
                    errors.append(fmt(section, f'Tasks[{i}] unknown trigger type "{ttype}"'))
                else:
                    # Trigger-item compatibility
                    if ttype in TRIGGER_CUBE_ONLY and prefab != "Trigger":
                        errors.append(fmt(section, f'Tasks[{i}] {ttype} only works on Trigger items, not {prefab}'))
                    if ttype in VISIBLE_ONLY_TRIGGERS and prefab == "Trigger":
                        errors.append(fmt(section, f'Tasks[{i}] {ttype} on Trigger item — Triggers are invisible during play, use a visible item'))

            # Validate DirectEffector if present
            direct = task.get("DirectEffector")
            if direct and isinstance(direct, dict):
                de_effector = direct.get("Effector")
                if de_effector and isinstance(de_effector, dict):
                    etype = de_effector.get("$type", "")
                    if etype not in VALID_EFFECTS:
                        errors.append(fmt(section, f'Tasks[{i}] DirectEffector unknown effect type "{etype}"'))
                    else:
                        errors.extend(validate_effect_params(item_key, prefab, etype, de_effector))

            # Validate quest linkage
            if "TaskTriggerId" in task and task["TaskTriggerId"]:
                if not validate_quest_id(task["TaskTriggerId"]):
                    errors.append(fmt(section, f'Tasks[{i}] TaskTriggerId "{task["TaskTriggerId"]}" is not a valid quest ID'))
                if "Name" in task and task["Name"] and not validate_quest_name(task["Name"]):
                    errors.append(fmt(section, f'Tasks[{i}] quest Name "{task["Name"]}" should follow N_suffix format'))

            # Validate TargetState for quest triggers
            if "TaskTriggerId" in task and task["TaskTriggerId"] and "TargetState" in task:
                ts = task["TargetState"]
                if ts not in VALID_LINKED_TASK_STATES:
                    errors.append(fmt(section, f'Tasks[{i}] TargetState {ts} is not a valid quest transition — valid: {sorted(VALID_LINKED_TASK_STATES)}'))

        else:
            if task_type:
                errors.append(fmt(section, f'Tasks[{i}] unknown task $type "{task_type}" — must be TaskEffectorSubscription or TaskTriggerSubscription'))
            else:
                errors.append(fmt(section, f"Tasks[{i}] missing $type"))

    return errors


def validate_quests(quests: dict) -> List[str]:
    """Validate quest structure, IDs, pairing, required fields, and field types."""
    errors = []
    required_fields = {"EntryId", "Name", "Description", "Status", "Group", "Enabled", "Creator", "id"}

    # Valid Group values
    valid_groups = {"", "multiplayer", "nonPersistent"}

    # Group quests by EntryId for pairing validation
    entry_groups: Dict[str, List[dict]] = {}

    # Collect all quest IDs for requirement cross-referencing
    all_quest_ids = set(quests.keys())

    for quest_id, quest in quests.items():
        section = f"quest {quest_id}"

        # ID matches key
        if quest.get("id") != quest_id:
            errors.append(fmt(section, f'"id" field ({quest.get("id")}) does not match dict key ({quest_id})'))

        # Quest ID format
        if not validate_quest_id(quest_id):
            errors.append(fmt(section, f'invalid quest ID format — should be mlh + 11-14 lowercase alphanumeric'))

        # Required fields
        for field in required_fields:
            if field not in quest:
                errors.append(fmt(section, f'missing required field "{field}"'))

        # EntryId is valid UUID
        entry_id = quest.get("EntryId", "")
        if entry_id and not is_valid_uuid(entry_id):
            errors.append(fmt(section, f'EntryId "{entry_id}" is not a valid UUID'))

        # Name format
        name = quest.get("Name", "")
        if name and not validate_quest_name(name):
            errors.append(fmt(section, f'Name "{name}" should follow N_suffix format (e.g., "0_activate")'))

        # Description must be "created in unity"
        desc = quest.get("Description", "")
        if desc and desc != "created in unity":
            errors.append(fmt(section, f'Description must be "created in unity", got "{desc}"'))

        # Status validation
        status = quest.get("Status", "")
        if status and status not in ("inProgress", "completed"):
            errors.append(fmt(section, f'Status must be "inProgress" or "completed", got "{status}"'))

        # Group validation
        group = quest.get("Group")
        if group is not None and not isinstance(group, str):
            errors.append(fmt(section, f'Group must be a string, got {type(group).__name__}'))
        elif isinstance(group, str) and group not in valid_groups:
            errors.append(fmt(section, f'Group must be "", "nonPersistent", or "multiplayer", got "{group}"'))

        # DisplayGroup validation (must be a string)
        display_group = quest.get("DisplayGroup")
        if display_group is not None and not isinstance(display_group, str):
            errors.append(fmt(section, f'DisplayGroup must be a string, got {type(display_group).__name__}'))

        # Boolean field type validation
        for bool_field in ("Enabled", "AutoStart", "TriggeredByInventory", "Tracked", "Visible"):
            val = quest.get(bool_field)
            if val is not None and not isinstance(val, bool):
                errors.append(fmt(section, f'{bool_field} must be a boolean, got {type(val).__name__}'))

        # Numeric field type validation
        for num_field in ("RepeatableLimit", "FinishTime"):
            val = quest.get(num_field)
            if val is not None and not isinstance(val, (int, float)):
                errors.append(fmt(section, f'{num_field} must be a number, got {type(val).__name__}'))

        # Requirements validation
        reqs = quest.get("Requirements")
        if reqs is not None:
            if not isinstance(reqs, list):
                errors.append(fmt(section, f'Requirements must be a list, got {type(reqs).__name__}'))
            else:
                for i, req in enumerate(reqs):
                    if not isinstance(req, dict):
                        errors.append(fmt(section, f'Requirements[{i}] must be a dict'))
                        continue
                    # Required requirement fields
                    for req_field in ("type", "id", "amount"):
                        if req_field not in req:
                            errors.append(fmt(section, f'Requirements[{i}] missing "{req_field}"'))
                    # Validate requirement type
                    req_type = req.get("type", "")
                    if req_type and req_type != "quest":
                        errors.append(fmt(section, f'Requirements[{i}] unknown type "{req_type}" — expected "quest"'))
                    # Cross-reference requirement quest ID
                    req_id = req.get("id", "")
                    if req_id and all_quest_ids and req_id not in all_quest_ids:
                        errors.append(fmt(section, f'Requirements[{i}] references quest "{req_id}" not found in quests'))
                    # Amount must be positive
                    req_amount = req.get("amount")
                    if isinstance(req_amount, (int, float)) and req_amount < 0:
                        errors.append(fmt(section, f'Requirements[{i}] amount must be non-negative, got {req_amount}'))

        # Rewards validation (completed entries only)
        rewards = quest.get("Rewards")
        if rewards is not None:
            if not isinstance(rewards, list):
                errors.append(fmt(section, f'Rewards must be a list, got {type(rewards).__name__}'))

        # SuccessMsg validation (completed entries only)
        success_msg = quest.get("SuccessMsg")
        if success_msg is not None and not isinstance(success_msg, str):
            errors.append(fmt(section, f'SuccessMsg must be a string, got {type(success_msg).__name__}'))

        # Group quests for pairing
        if entry_id:
            entry_groups.setdefault(entry_id, []).append(quest)

    # Validate pairing
    for entry_id, entries in entry_groups.items():
        statuses = [e.get("Status") for e in entries]
        ids = [e.get("id") for e in entries]

        if len(entries) != 2:
            errors.append(fmt("quests", f'EntryId "{entry_id}" has {len(entries)} entries — must have exactly 2 (inProgress + completed)'))
            continue

        if "inProgress" not in statuses:
            errors.append(fmt("quests", f'EntryId "{entry_id}" missing inProgress entry'))
        if "completed" not in statuses:
            errors.append(fmt("quests", f'EntryId "{entry_id}" missing completed entry'))

        # Pair must have different IDs
        if len(set(ids)) < 2:
            errors.append(fmt("quests", f'EntryId "{entry_id}" pair has duplicate quest IDs — each entry must have a different id'))

        # Pair must have matching Group, Name, and DisplayGroup
        if len(entries) == 2:
            for check_field in ("Group", "Name", "DisplayGroup"):
                vals = [e.get(check_field) for e in entries]
                if vals[0] != vals[1]:
                    errors.append(fmt("quests", f'EntryId "{entry_id}" pair has mismatched {check_field}: {vals}'))

    return errors


def validate_cross_references(data: dict) -> List[str]:
    """Validate cross-references between items, quests, settings."""
    errors = []

    items = data.get("roomItems", {})
    quests = data.get("quests", {})
    settings = data.get("settings", {})

    # Extract known quest IDs
    quest_ids = set(quests.keys())

    # Extract known variables from settings
    variable_names: Set[str] = set()
    camera_state_names: Set[str] = set()
    movement_state_names: Set[str] = set()

    rsed_str = settings.get("roomSettingsExtraData", "")
    if rsed_str and isinstance(rsed_str, str):
        try:
            rsed = json.loads(rsed_str)

            # Variables
            for param in rsed.get("numericParameters", []):
                if isinstance(param, dict) and "N" in param:
                    variable_names.add(param["N"])

            # Camera states
            for cs in rsed.get("customCameraStates", []):
                if isinstance(cs, dict) and "stateName" in cs:
                    camera_state_names.add(cs["stateName"])

            # Movement states
            for ms in rsed.get("movementStates", []):
                if isinstance(ms, dict) and "movementStateName" in ms:
                    movement_state_names.add(ms["movementStateName"])

        except (json.JSONDecodeError, TypeError):
            errors.append(fmt("settings", "roomSettingsExtraData is not valid JSON"))

    # Walk all items and check references
    for item_key, item in items.items():
        raw_extra = item.get("extraData", "")
        if not isinstance(raw_extra, str):
            continue
        try:
            extra = json.loads(raw_extra)
        except (json.JSONDecodeError, TypeError):
            continue

        tasks = extra.get("Tasks", [])
        if not isinstance(tasks, list):
            continue

        prefab = item.get("prefabName", "")

        for i, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue

            section = f"item {item_key}, {prefab}"

            # Check quest ID references
            trigger_id = task.get("TaskTriggerId", "")
            if trigger_id and quest_ids and trigger_id not in quest_ids:
                # Only flag if we actually have quests defined
                errors.append(fmt(section, f'Tasks[{i}] TaskTriggerId "{trigger_id}" not found in quests'))

            # Check effect-specific cross-references
            effector = task.get("Effector") or (task.get("DirectEffector", {}) or {}).get("Effector")
            if effector and isinstance(effector, dict):
                etype = effector.get("$type", "")

                # Variable references
                if etype in ("UpdateScoreEvent", "DisplayValueEvent", "HideValueEvent"):
                    label = effector.get("label", "")
                    if label and variable_names and label not in variable_names:
                        errors.append(fmt(section, f'Tasks[{i}] {etype} references variable "{label}" not defined in settings numericParameters'))

                # Camera state references
                if etype == "ChangeCamState":
                    cam_state = effector.get("camState", "")
                    if cam_state and camera_state_names and cam_state not in camera_state_names:
                        errors.append(fmt(section, f'Tasks[{i}] ChangeCamState references camera state "{cam_state}" not defined in settings'))

                # Movement profile references
                if etype == "ChangeMovementProfile":
                    profile = effector.get("mvmtProfile", "")
                    if profile and movement_state_names and profile not in movement_state_names:
                        errors.append(fmt(section, f'Tasks[{i}] ChangeMovementProfile references movement state "{profile}" not defined in settings'))

    return errors


# ============================================================================
# MAIN VALIDATION ORCHESTRATOR
# ============================================================================

def validate_snapshot(file_path: str) -> List[str]:
    """
    Validate a snapshot.json file and return all errors found.

    Args:
        file_path: Path to the snapshot.json file.

    Returns:
        List of error strings. Empty list = valid.
    """
    errors = []

    # Load JSON
    path = Path(file_path)
    if not path.exists():
        return [fmt("file", f"file not found: {file_path}")]

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [fmt("file", f"invalid JSON: {e}")]

    if not isinstance(data, dict):
        return [fmt("file", f"root must be a dict, got {type(data).__name__}")]

    # Normalize: merge logic into items as extraData
    normalize_snapshot(data)

    # 1. Top-level structure
    errors.extend(validate_top_level(data))

    # 2. Settings
    if "settings" in data:
        errors.extend(validate_settings(data["settings"]))

    # If missing roomItems, can't validate items
    items = data.get("roomItems", {})
    if isinstance(items, dict):
        all_keys = set(items.keys())

        # 2-5. Per-item validation
        for item_key, item in items.items():
            if not isinstance(item, dict):
                errors.append(fmt(f"item {item_key}", "item is not a dict"))
                continue

            # 2. Structure
            errors.extend(validate_item_structure(item_key, item, all_keys))

            # Parse extraData for deeper validation
            raw_extra = item.get("extraData", "")
            if not isinstance(raw_extra, str):
                continue
            extra, parse_err = safe_parse_extra_data(item_key, raw_extra)
            if parse_err:
                errors.append(parse_err)
                continue

            prefab = item.get("prefabName", "")
            content_string = item.get("contentString", "")

            # 3. Item-specific extraData
            if prefab in VALID_PREFAB_NAMES:
                errors.extend(validate_item_extra_data(item_key, prefab, extra, content_string))

            # 4. Tasks (triggers & effects)
            tasks = extra.get("Tasks", [])
            if isinstance(tasks, list) and tasks:
                errors.extend(validate_item_tasks(item_key, prefab, tasks))

    # 5. Quests
    quests = data.get("quests", {})
    if isinstance(quests, dict) and quests:
        errors.extend(validate_quests(quests))

    # 6. Cross-references
    errors.extend(validate_cross_references(data))

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate a Portals room snapshot.json file"
    )
    parser.add_argument("file", help="Path to snapshot.json file")
    args = parser.parse_args()

    errors = validate_snapshot(args.file)

    if errors:
        for error in errors:
            print(error)
        print(f"\n{len(errors)} error(s) found")
        sys.exit(1)
    else:
        print("OK — no errors found")
        sys.exit(0)


if __name__ == "__main__":
    main()
