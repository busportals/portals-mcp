"""
Portals Effect & Trigger Builders
All confirmed effect and trigger syntax for the Portals Tasks system.

Architecture:
- Effector functions return the inner {"$type": "...", ...} payload
- Trigger functions return the inner {"$type": "..."} payload
- Wrapper functions assemble these into TaskEffectorSubscription / TaskTriggerSubscription
- Helper functions attach tasks to logic dicts

Usage:
    from portals_effects import *

    # Basic interaction: click cube -> notification
    task = basic_interaction(
        trigger=trigger_on_click(),
        effector=effector_notification("Hello!", "00FF00")
    )
    add_task_to_logic(my_logic, task)

    # Quest-linked: effect fires when quest completes
    task = quest_effector(quest_id, quest_name, 2, effector_hide())
    add_task_to_logic(my_logic, task)

    # Quest-linked: trigger advances quest state
    task = quest_trigger(quest_id, quest_name, 181, trigger_on_click())
    add_task_to_logic(my_logic, task)
"""

import uuid
from typing import Dict, List, Optional


# ============================================================================
# EFFECTOR BUILDERS (63 confirmed — ALL general effects)
# Each returns the inner effector payload: {"$type": "...", ...params}
# ============================================================================

# ── Visibility ──────────────────────────────────────────────────────────────

def effector_show() -> Dict:
    """Show a hidden item."""
    return {"$type": "ShowObjectEvent"}


def effector_hide() -> Dict:
    """Hide an item (invisible + no collider)."""
    return {"$type": "HideObjectEvent"}


def effector_show_outline() -> Dict:
    """Show selection outline on the item."""
    return {"$type": "ShowOutline"}


def effector_hide_outline() -> Dict:
    """Remove selection outline from the item."""
    return {"$type": "HideOutline"}


def effector_duplicate(
    position: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    destroy_after: float = 0.0
) -> Dict:
    """
    Duplicate the item at a new position.

    Args:
        position: [x, y, z] spawn position for the duplicate.
        rotation: [qx, qy, qz, qw] spawn rotation. None = same as original.
        scale: [sx, sy, sz] spawn scale. None = same as original.
        destroy_after: Auto-destroy the duplicate after this many seconds. 0 = never.
    """
    e = {"$type": "DuplicateItem"}
    ts = {}
    if position is not None:
        ts["position"] = position
    if rotation is not None:
        ts["rotation"] = rotation
    if scale is not None:
        ts["scale"] = scale
    if ts:
        e["TS"] = ts
    if destroy_after > 0:
        e["destroyAfterTime"] = destroy_after
    return e


# ── Movement & Transform ───────────────────────────────────────────────────

def effector_move_to_spot(
    position: Optional[List[float]] = None,
    rotation: Optional[List[float]] = None,
    scale: Optional[List[float]] = None,
    duration: float = 0.0
) -> Dict:
    """
    Animate item to a new position/rotation/scale.

    Args:
        position: [x, y, z] target position. None = don't change.
        rotation: [qx, qy, qz, qw] target quaternion. None = don't change.
        scale: [sx, sy, sz] target scale. None = don't change.
        duration: Animation time in seconds. 0 = instant.
    """
    state = {"duration": duration}
    if position is not None:
        state["position"] = position
    if rotation is not None:
        state["rotation"] = rotation
    if scale is not None:
        state["scale"] = scale
    return {"$type": "MoveToSpot", "_transformState": state}


def effector_move_item_to_player() -> Dict:
    """Teleport the item to the player's position."""
    return {"$type": "MoveItemToPlayer"}


def effector_animation(
    transform_states: List[Dict],
    states: List[Dict],
    loop: bool = False,
    seamless: bool = False,
    state_events: Optional[List] = None
) -> Dict:
    """
    Play a multi-keyframe animation on an item.

    Args:
        transform_states: List of keyframe dicts with position/rotation/scale.
            Each: {"position": [x,y,z], "rotation": [qx,qy,qz,qw], "scale": [sx,sy,sz]}
        states: Legacy keyframe format (required alongside transform_states).
            Each: {"x":, "y":, "z":, "rx":, "sx":, "sy":, "sz":, "duration": float}
        loop: True = animation repeats forever.
        seamless: True = smooth loop transition.
        state_events: Optional list of events at specific keyframes.
    """
    return {
        "$type": "PortalsAnimation",
        "stateEvents": state_events or [],
        "_transformStates": transform_states,
        "states": states,
        "loopAnimation": loop,
        "seamless": seamless
    }


# ── Player Effects ─────────────────────────────────────────────────────────

def effector_velocity(vel: List[float], local: bool = True) -> Dict:
    """
    Apply velocity to the player (launch/push).

    Args:
        vel: [x, y, z] velocity. e.g. [0, 8, 0] for upward launch.
        local: True = relative to player facing, False = world space.
    """
    return {"$type": "AddVelocityToPlayer", "vel": vel, "local": local}


def effector_teleport(room_id: str, spawn_name: str = "", spawn_radius: float = 0.0) -> Dict:
    """
    Teleport player to a room/spawn point.

    Args:
        room_id: Target room UUID. Same room = respawn.
        spawn_name: Target spawn point name. "" = default spawn.
        spawn_radius: Random offset from spawn point.
    """
    return {"$type": "TeleportEvent", "id": room_id, "sn": spawn_name, "sr": spawn_radius}


def effector_heal(amount: int) -> Dict:
    """Heal the player by amount."""
    return {"$type": "ChangePlayerHealth", "healthChange": amount}


def effector_damage(amount: int) -> Dict:
    """Damage the player by amount."""
    return {"$type": "ChangePlayerHealth", "op": 2, "healthChange": amount}


def effector_damage_over_time() -> Dict:
    """Apply continuous damage while player is in contact."""
    return {"$type": "DamageOverTime"}


def effector_lock_movement() -> Dict:
    """Freeze the player in place."""
    return {"$type": "LockMovement"}


def effector_unlock_movement() -> Dict:
    """Unfreeze the player."""
    return {"$type": "UnlockMovement"}


def effector_start_auto_run() -> Dict:
    """Force the player to auto-run forward."""
    return {"$type": "StartAutoRun"}


def effector_stop_auto_run() -> Dict:
    """Stop forced auto-run."""
    return {"$type": "StopAutoRun"}


def effector_emote(animation_name: str) -> Dict:
    """
    Make the player perform an emote.

    Args:
        animation_name: Emote name. Options include:
            "Chicken", "Wave", "Salute", "Jive", "Salsa",
            "Shuffling", "Slide n Jive", "Robot", "Can Can", "Sitting"
    """
    return {"$type": "PlayerEmote", "animationName": animation_name}


def effector_mute_player() -> Dict:
    """Mute the player's microphone."""
    return {"$type": "MutePlayer"}


def effector_hide_all_players() -> Dict:
    """Hide all other players from this player's view."""
    return {"$type": "HideAllPlayersEvent"}


def effector_lock_avatar_change() -> Dict:
    """Prevent the player from changing their avatar."""
    return {"$type": "LockAvatarChange"}


def effector_unlock_avatar_change() -> Dict:
    """Allow the player to change their avatar again."""
    return {"$type": "UnlockAvatarChange"}


def effector_display_avatar_screen() -> Dict:
    """Open the avatar selection screen."""
    return {"$type": "DisplayAvatarScreen"}


def effector_change_avatar(url: str, persistent: bool = True) -> Dict:
    """
    Change the player's avatar to a GLB model.

    Args:
        url: Public URL to a GLB avatar model.
        persistent: True = avatar persists across sessions.
    """
    return {"$type": "ChangeAvatarEffector", "Url": url, "Persistent": persistent}


def effector_change_movement_profile(profile: str) -> Dict:
    """
    Change the player's movement profile.

    Args:
        profile: Movement profile name (configured in room settings).
    """
    return {"$type": "ChangeMovementProfile", "mvmtProfile": profile}


def effector_equip_wearable(item_id: str) -> Dict:
    """
    Equip a wearable item on the player.

    Args:
        item_id: Wearable item ID from the Portals inventory system.
    """
    return {"$type": "ChangeRoundyWearableEffector", "ItemID": item_id}


# ── Camera ─────────────────────────────────────────────────────────────────

def effector_lock_camera() -> Dict:
    """Lock the camera in its current position/rotation."""
    return {"$type": "LockCamera"}


def effector_unlock_camera() -> Dict:
    """Unlock the camera to follow the player again."""
    return {"$type": "UnlockCamera"}


def effector_camera_zoom(zoom_amount: float, lock_zoom: bool = False) -> Dict:
    """
    Change camera zoom level.

    Args:
        zoom_amount: Zoom multiplier. Higher = more zoomed in.
        lock_zoom: True = prevent player from changing zoom.
    """
    return {"$type": "ChangeCameraZoom", "zoomAmount": zoom_amount, "lockZoom": lock_zoom}


def effector_toggle_free_cam() -> Dict:
    """Toggle free camera mode (detach from player)."""
    return {"$type": "ToggleFreeCam"}


def effector_change_cam_state(cam_state: str, transition_speed: float = 1.0) -> Dict:
    """
    Switch to a named camera state.

    Args:
        cam_state: Camera state name (configured in room settings).
        transition_speed: Transition speed to the new camera state.
    """
    return {"$type": "ChangeCamState", "camState": cam_state, "transitionSpeed": transition_speed}


def effector_camera_filter(url: str, alpha: float = 1.0) -> Dict:
    """
    Apply an image overlay to the camera.

    Args:
        url: Public image URL for the filter overlay.
        alpha: Opacity (0.0 = invisible, 1.0 = fully opaque).
    """
    return {"$type": "SetCameraFilter", "url": url, "alpha": alpha}


def effector_toggle_cursor_lock(lock: bool = True) -> Dict:
    """
    Lock or unlock the mouse cursor.

    Args:
        lock: True = lock cursor to center, False = free cursor.
    """
    return {"$type": "ToggleLockCursor", "lockCursor": lock}


# ── UI & Notifications ────────────────────────────────────────────────────

def effector_notification(text: str, color: str = "FFFFFF", hide_background: bool = False) -> Dict:
    """
    Show a notification pill on screen.

    Args:
        text: Message text. Supports rich text tags: <b>, <i>, <color=#hex>.
        color: 6-char hex color for the pill (no # prefix).
        hide_background: True = text only, no pill background.
    """
    return {"$type": "NotificationPillEvent", "nt": text, "c": color, "hideBackground": hide_background}


# ── Values (Variables) ─────────────────────────────────────────────────────

def effector_display_value(label: str, color: str = "FFFFFF") -> Dict:
    """
    Show a variable's value on the player's HUD.

    Args:
        label: Variable name to display.
        color: 6-char hex color for the display.
    """
    return {"$type": "DisplayValueEvent", "label": label, "color": color}


def effector_hide_value(label: str) -> Dict:
    """
    Hide a variable from the player's HUD.

    Args:
        label: Variable name to hide.
    """
    return {"$type": "HideValueEvent", "label": label}


def effector_update_value(label: str = "", op: int = 1, change: float = 1.0) -> Dict:
    """
    Modify a numeric variable.

    Args:
        label: Variable name. "" = uses the item's default variable.
        op: Operation. 1 = add, 2 = subtract, 3 = set, 4 = multiply.
        change: Amount to change by.
    """
    e = {"$type": "UpdateScoreEvent", "op": op, "scoreChange": change}
    if label:
        e["label"] = label
    return e


def effector_update_string_value(label: str, text: str) -> Dict:
    """
    Set a string variable's value.

    Args:
        label: Variable name.
        text: New text value.
    """
    return {"$type": "UpdateScoreEventString", "targetText": text, "label": label}


# ── Function Effects ───────────────────────────────────────────────────────

def effector_function(expression: str) -> Dict:
    """
    Evaluate an NCalc expression (conditional logic, math, etc.).

    Args:
        expression: NCalc expression string.
            Examples:
                "$N{coins} >= 10.0"  — check if coins >= 10
                "$N{score} + 5"      — add 5 to score
            Refer to Portals function docs for full syntax.
    """
    return {"$type": "FunctionEffector", "V": expression}


# ── Quest/Task Control ─────────────────────────────────────────────────────

def effector_run_triggers(
    linked_tasks: List[Dict],
    use_random: bool = False
) -> Dict:
    """
    Trigger state changes on other quests.

    Args:
        linked_tasks: List of quest transitions. Each dict:
            {
                "quest_id": "mlh...",
                "quest_name": "0_name",
                "target_state": 181,  # encoded state transition
                "delay": 0.0          # optional delay in seconds
            }
        use_random: True = fire ONE random task, False = fire all.

    Encoded target_state values:
        101 = Any -> Not Active
        111 = Not Active -> Active
        121 = Active -> Completed
        131 = Completed -> Active
        141 = Any -> Completed
        151 = Any -> Active
        161 = Active -> Not Active
        171 = Completed -> Not Active
        181 = Not Active -> Completed
    """
    tasks = []
    for t in linked_tasks:
        entry = {
            "Trigger": {"Delay": t["delay"]} if t.get("delay") else {},
            "Id": str(uuid.uuid4()),
            "TargetState": t["target_state"],
            "Name": t["quest_name"],
            "TaskTriggerId": t["quest_id"]
        }
        tasks.append(entry)

    e = {"$type": "RunTriggersFromEffector", "linkedTasks": tasks}
    if use_random:
        e["useRandom"] = True
    return e


def effector_reset_all_tasks() -> Dict:
    """Reset all quests in the room to their initial state."""
    return {"$type": "ResetAllTasks"}


# ── Timers ─────────────────────────────────────────────────────────────────

def effector_start_timer(timer_name: str, countdown_id: str = "") -> Dict:
    """
    Start a named timer.

    Args:
        timer_name: Timer identifier (must match across start/stop/cancel).
        countdown_id: Optional countdown configuration ID.
    """
    return {"$type": "StartTimerEffect", "tn": timer_name, "ci": countdown_id}


def effector_stop_timer(timer_name: str, countdown_id: str = "") -> Dict:
    """
    Stop a running timer (fires OnTimerStopped trigger).

    Args:
        timer_name: Timer identifier to stop.
        countdown_id: Optional countdown configuration ID.
    """
    return {"$type": "StopTimerEffect", "tn": timer_name, "ci": countdown_id}


def effector_cancel_timer(timer_name: str) -> Dict:
    """
    Cancel a timer without firing the stopped trigger.

    Args:
        timer_name: Timer identifier to cancel.
    """
    return {"$type": "CancelTimerEffect", "tn": timer_name}


# ── Leaderboard ────────────────────────────────────────────────────────────

def effector_post_score() -> Dict:
    """Post the player's current score to the leaderboard."""
    return {"$type": "PostScoreToLeaderboard"}


def effector_clear_leaderboard(label: str) -> Dict:
    """
    Clear a leaderboard.

    Args:
        label: Leaderboard/timer name to clear.
    """
    return {"$type": "ClearLeaderboard", "label": label}


def effector_open_leaderboard(leaderboard_name: str) -> Dict:
    """
    Open the leaderboard UI for the player.

    Args:
        leaderboard_name: Name of the leaderboard to display.
    """
    return {"$type": "OpenLeaderboardEffect", "lb": leaderboard_name}


# ── Audio ──────────────────────────────────────────────────────────────────

def effector_play_sound_once(url: str, distance: float = 10.0) -> Dict:
    """
    Play a sound effect once.

    Args:
        url: Public URL to an MP3 file.
        distance: Audible distance in meters.
    """
    return {"$type": "PlaySoundOnce", "Url": url, "Dist": distance}


def effector_play_sound_loop(url: str, distance: float = -1.0, preload: bool = True) -> Dict:
    """
    Play a sound in a continuous loop.

    Args:
        url: Public URL to an MP3 file.
        distance: Audible distance in meters. -1 = global (heard everywhere).
        preload: True = preload the audio file for instant playback.
    """
    return {"$type": "PlaySoundInALoop", "Url": url, "Dist": distance, "Preload": preload}


def effector_stop_sound(url: str, fade_out: float = 0.0) -> Dict:
    """
    Stop a playing sound.

    Args:
        url: URL of the sound to stop (must match the playing sound's URL).
        fade_out: Fade out duration in seconds. 0 = instant stop.
    """
    return {"$type": "StopSound", "url": url, "fadeOut": fade_out}


def effector_change_audius(playlist: str) -> Dict:
    """
    Change the Audius playlist playing in the room.

    Args:
        playlist: Audius playlist name/slug.
    """
    return {"$type": "ChangeAudiusEffect", "ap": playlist}


# ── Environment ────────────────────────────────────────────────────────────

def effector_change_bloom(intensity: float, clamp: float = 1.0, diffusion: float = 1.0) -> Dict:
    """
    Change the bloom post-processing effect.

    Args:
        intensity: Bloom intensity (0 = off, higher = stronger glow).
        clamp: Bloom clamp value.
        diffusion: Bloom diffusion spread.
    """
    return {"$type": "ChangeBloom", "Intensity": intensity, "Clamp": clamp, "Diffusion": diffusion}


def effector_change_time_of_day() -> Dict:
    """Cycle the time of day (changes lighting/skybox)."""
    return {"$type": "ChangeTimeOfDay"}


def effector_rotate_skybox(rotation: float, duration: float = 1.0) -> Dict:
    """
    Rotate the skybox.

    Args:
        rotation: Target rotation in degrees.
        duration: Animation time in seconds.
    """
    return {"$type": "RotateSkybox", "rotation": rotation, "duration": duration}


def effector_change_fog(color: str, distance: float) -> Dict:
    """
    Change the fog settings.

    Args:
        color: 6-char hex color for the fog (no # prefix).
        distance: Fog draw distance in meters. Lower = thicker fog.
    """
    return {"$type": "ChangeFog", "color": color, "distance": distance}


# ── Communication ──────────────────────────────────────────────────────────

def effector_send_iframe_message(message: str) -> Dict:
    """
    Send a message to all iframes in the room.

    Args:
        message: Message string that iframes will receive.
    """
    return {"$type": "SendMessageToIframes", "iframeMsg": message}


def effector_change_voice_group(group: str) -> Dict:
    """
    Move the player to a voice chat group.

    Args:
        group: Voice group name.
    """
    return {"$type": "ChangeVoiceGroup", "group": group}


# ── Iframes ───────────────────────────────────────────────────────────────

def effector_open_iframe(url: str) -> Dict:
    """
    Open an iframe overlay for the player.

    Args:
        url: Public URL to load in the iframe.
    """
    return {"$type": "IframeEvent", "url": url}


def effector_close_iframe(url: str) -> Dict:
    """
    Close a specific iframe overlay.

    Args:
        url: URL of the iframe to close (must match the open iframe's URL).
    """
    return {"$type": "IframeStopEvent", "iframeUrl": url}


# ── NPC ────────────────────────────────────────────────────────────────────

def effector_npc_message(npc_name: str, message: str, repeatable: bool = True) -> Dict:
    """
    Send a message to an AI NPC (triggers NPC to speak/respond).

    Args:
        npc_name: Name of the target NPC.
        message: Message to send to the NPC.
        repeatable: True = can be triggered multiple times.
    """
    return {"$type": "NPCMessageEvent", "n": npc_name, "m": message, "r": repeatable}


# ── Token Swap ─────────────────────────────────────────────────────────────

def effector_show_token_swap(swap_id: str, typ: int = 3) -> Dict:
    """
    Display the token swap UI for a specific token.

    Args:
        swap_id: Token swap configuration ID.
        typ: Swap type (3 = standard).
    """
    return {"$type": "DisplaySellSwap", "id": swap_id, "typ": typ}


def effector_hide_token_swap() -> Dict:
    """Hide the token swap UI."""
    return {"$type": "HideSellSwap"}


# ── Dialogue ───────────────────────────────────────────────────────────────

def effector_dialogue_display(
    character_name: str,
    dialogue_nodes: List[Dict],
    creator_uid: str,
    repeatable: bool = True,
    audio: bool = False,
    hide_on_finish: bool = True,
    goodbye_action: str = "leave",
    dialogue_voice_id: str = ""
) -> Dict:
    """
    Display an interactive dialogue tree. This is one of the most complex effects —
    it embeds an entire quest-based dialogue tree inline in the effector.

    Args:
        character_name: NPC name displayed in the dialogue UI.
        dialogue_nodes: List of dialogue node dicts, each:
            {
                "question": "What the NPC says",
                "answers": [
                    {"text": "Player answer text", "next": 1},  # index of next node
                    {"text": "Another answer", "next": 2},
                ]
            }
            Terminal nodes have empty answers list [].
            Answer "next" is the index into dialogue_nodes for branching.
        creator_uid: Firebase UID of the room creator.
        repeatable: True = dialogue can be triggered again after finishing.
        audio: True = enable audio playback for dialogue.
        hide_on_finish: True = hide dialogue UI when finished.
        goodbye_action: What happens when dialogue ends. "leave" = close.
        dialogue_voice_id: Optional voice ID for TTS.

    Returns:
        DialogEffectorDisplay effector dict.

    Example:
        effector_dialogue_display(
            character_name="Guard",
            dialogue_nodes=[
                {"question": "Halt! Who goes there?", "answers": [
                    {"text": "A friend", "next": 1},
                    {"text": "None of your business", "next": 2},
                ]},
                {"question": "Welcome, friend!", "answers": []},
                {"question": "Guards! Seize them!", "answers": []},
            ],
            creator_uid="YOUR_FIREBASE_UID",
        )
    """
    import json as _json

    story_id = str(uuid.uuid4())

    # Build task names for each node
    task_names = [f"-{i}_{node['question'][:30].replace(' ', ' ')}" for i, node in enumerate(dialogue_nodes)]

    # Build tasksN list
    tasks_n = [{"N": name} for name in task_names]

    # Build tasksSorM with inline quest entries
    tasks_sor_m = {}
    for i, node in enumerate(dialogue_nodes):
        name = task_names[i]
        entry_id = str(uuid.uuid4())

        # Build answer references
        answers = []
        for ans in node.get("answers", []):
            next_name = task_names[ans["next"]]
            answers.append({
                "Task": next_name,
                "Txt": ans["text"],
                "Name": ans["text"]
            })

        extra_text = _json.dumps({
            "ExtraTaskDTODataDialog": {
                "QT": node["question"],
                "AT": answers
            }
        })

        base = {
            "Name": name,
            "Description": "created in unity",
            "Group": "",
            "Enabled": True,
            "Requirements": [],
            "Rewards": [],
            "Creator": creator_uid,
            "EntryId": entry_id,
            "Tracked": True,
            "ExtraText": extra_text,
            "DisplayGroup": "",
        }

        # Generate unique IDs for inProgress and completed entries
        id_progress = f"mlh{''.join(__import__('random').choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))}"
        id_completed = f"mlh{''.join(__import__('random').choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))}"

        tasks_sor_m[name] = {
            "completed": {
                **base,
                "id": id_completed,
                "Status": "completed",
                "SuccessMsg": "",
                "GetStatus": "completed"
            },
            "inProgress": {
                **base,
                "id": id_progress,
                "Status": "inProgress",
                "GetStatus": "inProgress",
                "GetStatusEnum": 1
            },
        }

    return {
        "$type": "DialogEffectorDisplay",
        "tasksN": tasks_n,
        "GN": character_name,
        "S": f"_{story_id}",
        "Audio": audio,
        "HF": hide_on_finish,
        "R": repeatable,
        "DV": dialogue_voice_id,
        "GB": goodbye_action,
        "Story": f"_{story_id}",
        "tasksSorM": tasks_sor_m
    }


# ── Inventory ──────────────────────────────────────────────────────────────

def effector_refresh_inventory() -> Dict:
    """Refresh the player's inventory display."""
    return {"$type": "RefreshUserInventory"}


# ============================================================================
# TRIGGER BUILDERS (23 confirmed: 21 general + 2 trigger-cube-only)
# Each returns the inner trigger payload: {"$type": "..."}
# ============================================================================

# ── General Triggers (work on any item) ────────────────────────────────────

def trigger_on_click() -> Dict:
    """Player clicks/taps the item."""
    return {"$type": "OnClickEvent"}


def trigger_on_collide() -> Dict:
    """Player collides with the item (collision started)."""
    return {"$type": "OnCollideEvent"}


def trigger_collision_stopped() -> Dict:
    """Player stops colliding with the item."""
    return {"$type": "OnCollisionStoppedEvent"}


def trigger_hover_start() -> Dict:
    """Player's cursor starts hovering over the item."""
    return {"$type": "OnHoverStartEvent"}


def trigger_hover_end() -> Dict:
    """Player's cursor stops hovering over the item."""
    return {"$type": "OnHoverEndEvent"}


def trigger_player_logged_in() -> Dict:
    """Player logs into the room (authenticated)."""
    return {"$type": "OnPlayerLoggedIn"}


def trigger_player_died() -> Dict:
    """Player's health reaches zero."""
    return {"$type": "OnPlayerDied"}


def trigger_player_move() -> Dict:
    """Player starts moving."""
    return {"$type": "OnPlayerMove"}


def trigger_player_stopped_moving() -> Dict:
    """Player stops moving."""
    return {"$type": "OnPlayerStoppedMoving"}


def trigger_key_pressed() -> Dict:
    """Player presses a key."""
    return {"$type": "OnKeyPressedEvent"}


def trigger_key_released() -> Dict:
    """Player releases a key."""
    return {"$type": "OnKeyReleasedEvent"}


def trigger_mic_unmuted() -> Dict:
    """Player unmutes their microphone."""
    return {"$type": "OnMicrophoneUnmuted"}


def trigger_player_revived() -> Dict:
    """Player is revived after dying."""
    return {"$type": "OnPlayerRevived"}


def trigger_timer_stopped() -> Dict:
    """A timer is stopped (via StopTimerEffect)."""
    return {"$type": "OnTimerStopped"}


def trigger_countdown_finished() -> Dict:
    """A countdown timer reaches zero."""
    return {"$type": "OnCountdownTimerFinished"}


def trigger_value_updated() -> Dict:
    """A variable/score value is updated."""
    return {"$type": "ScoreTrigger"}


def trigger_animation_stopped() -> Dict:
    """A PortalsAnimation finishes playing."""
    return {"$type": "OnAnimationStoppedEvent"}


def trigger_item_collected() -> Dict:
    """An item is collected by the player."""
    return {"$type": "OnItemCollectedEvent"}


def trigger_backpack_item_activated() -> Dict:
    """A backpack/inventory item is clicked/activated."""
    return {"$type": "OnItemClickEvent"}


def trigger_player_leave() -> Dict:
    """A player leaves the room."""
    return {"$type": "PlayerLeave"}


def trigger_swap_volume() -> Dict:
    """Swap volume trigger fires."""
    return {"$type": "SwapVolume"}


# ── Trigger-Cube-Only Triggers (only work on prefabName: "Trigger") ──────

def trigger_on_enter() -> Dict:
    """Player enters the trigger zone. ONLY works on Trigger items."""
    return {"$type": "OnEnterEvent"}


def trigger_on_exit() -> Dict:
    """Player exits the trigger zone. ONLY works on Trigger items."""
    return {"$type": "OnExitEvent"}


# ============================================================================
# WRAPPER FUNCTIONS
# Assemble effectors/triggers into the full Task subscription dicts
# ============================================================================

def basic_interaction(trigger: Dict, effector: Dict) -> Dict:
    """
    Create a direct trigger -> effect (no quest needed).

    This is the simplest pattern: when trigger fires, effect runs immediately.

    Args:
        trigger: Trigger payload from a trigger_*() function.
        effector: Effector payload from an effector_*() function.

    Returns:
        TaskTriggerSubscription dict ready for item's Tasks array.
    """
    return {
        "$type": "TaskTriggerSubscription",
        "Trigger": trigger,
        "DirectEffector": {
            "Effector": effector,
            "Id": str(uuid.uuid4()),
            "TargetState": 2,
            "Name": ""
        },
        "Id": str(uuid.uuid4()),
        "TargetState": 2,
        "Name": ""
    }


def quest_effector(
    quest_id: str,
    quest_name: str,
    target_state: int,
    effector: Dict
) -> Dict:
    """
    Create a quest-linked effect (fires when quest reaches target_state).

    Args:
        quest_id: Quest ID (e.g., "mlh9kkyxvll8ql") — the inProgress entry ID.
        quest_name: Quest name (e.g., "0_activate") — must match quest Name field.
        target_state: Quest state that triggers this effect:
            0 = Not Active, 1 = Active/In Progress, 2 = Completed
        effector: Effector payload from an effector_*() function.

    Returns:
        TaskEffectorSubscription dict ready for item's Tasks array.
    """
    task = {
        "$type": "TaskEffectorSubscription",
        "Effector": effector,
        "Id": str(uuid.uuid4()),
        "Name": quest_name,
        "TaskTriggerId": quest_id
    }
    if target_state > 0:
        task["TargetState"] = target_state
    return task


def quest_trigger(
    quest_id: str,
    quest_name: str,
    target_state: int,
    trigger: Dict
) -> Dict:
    """
    Create a quest-linked trigger (advances quest when trigger fires).

    Args:
        quest_id: Quest ID (e.g., "mlh9kkyxvll8ql").
        quest_name: Quest name (e.g., "0_activate").
        target_state: Encoded state transition. Common values:
            111 = Not Active -> Active
            121 = Active -> Completed
            181 = Not Active -> Completed
            161 = Active -> Not Active
            171 = Completed -> Not Active
        trigger: Trigger payload from a trigger_*() function.

    Returns:
        TaskTriggerSubscription dict ready for item's Tasks array.
    """
    return {
        "$type": "TaskTriggerSubscription",
        "Trigger": trigger,
        "Id": str(uuid.uuid4()),
        "TargetState": target_state,
        "Name": quest_name,
        "TaskTriggerId": quest_id
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def add_task_to_logic(logic: Dict, task: Dict) -> None:
    """
    Add a task (trigger or effect subscription) to a logic entry's Tasks array.
    Modifies logic dict in-place.
    """
    if "Tasks" not in logic:
        logic["Tasks"] = []
    logic["Tasks"].append(task)


def add_tasks_to_logic(logic: Dict, tasks: List[Dict]) -> None:
    """
    Add multiple tasks to a logic entry's Tasks array.
    Modifies logic dict in-place.
    """
    if "Tasks" not in logic:
        logic["Tasks"] = []
    logic["Tasks"].extend(tasks)
