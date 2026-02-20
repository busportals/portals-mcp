---
name: Keypad Code Entry
category: mechanics
tags: [keypad, code, pin, password, lock, escape room, puzzle, safe, combination, door, security]
patterns: [variable-tracking, conditional-logic, quest-advancing-trigger, direct-trigger-effect]
summary: Numeric code entry system using clickable animated key buttons, digit accumulation via variables, and reactive code validation with success/failure feedback
---

# Keypad Code Entry

A code entry system where players click buttons to enter a PIN. Each press plays feedback and appends a digit to a variable. When enough digits are entered, a reactive validator checks the code — correct input completes a quest, wrong input shows an error and resets.

**This is a composable component.** The keypad handles input and validation. Its output is a **quest** — when the correct code is entered, that quest completes. You decide what happens next by wiring other items to react to that quest: a door opens, a gate lifts, lights turn on, a secret passage reveals, a sound plays — anything. The keypad doesn't know or care what it unlocks.

## How It Works

The core technique is **digit accumulation**: a variable stores the code as a number, and each button press shifts left by one digit and adds the new one:

```
codeEntry = (codeEntry × 10) + digit
```

Press 1, then 2, then 3, then 4 → `codeEntry` goes: `0 → 1 → 12 → 123 → 1234`

A **reactive FunctionEffector** (`"R": true`) on a host item watches `codeEntry`. When it reaches 4 digits (≥1000 and ≤9999), it auto-validates — no submit button needed.

This pattern works with **any clickable items** — pre-built keypad GLBs, custom 3D models, ResizableCubes, or anything that receives `OnClickEvent`.

---

## Part 1: Pre-Built Keypad (Drop-In Component)

A complete, production-tested keypad using the pre-built asset pack. Call `build_keypad()` and get back items, logic, and quests — no assembly required.

### Assets

**GLB models** (positions baked into geometry — all children at `(0,0,0)` relative to parent):

| Asset | CDN Path |
|-------|----------|
| Keypad body | `#gltf/2026-01-31_keybox00_82c2beb69144a28f_0.glb` |
| Key 0 | `#gltf/2026-01-31_key00000_bbabbca37a7a1fd1_0.glb` |
| Key 1 | `#gltf/2026-01-31_key10000_1a7c52510170cbba_0.glb` |
| Key 2 | `#gltf/2026-01-31_key20000_a5c7bce096e32806_0.glb` |
| Key 3 | `#gltf/2026-01-31_key30000_12eb2a31c5efd422_0.glb` |
| Key 4 | `#gltf/2026-01-31_key40000_e0f15ceafecce4f1_0.glb` |
| Key 5 | `#gltf/2026-01-31_key50000_2f99bdcc47cf4f9d_0.glb` |
| Key 6 | `#gltf/2026-01-31_key60000_f5433b73ac91634c_0.glb` |
| Key 7 | `#gltf/2026-01-31_key70000_ea0ba454be69e40b_0.glb` |
| Key 8 | `#gltf/2026-01-31_key80000_9e5cea8a1cdc0688_0.glb` |
| Key 9 | `#gltf/2026-01-31_key90000_27d056eca5ca8980_0.glb` |
| Star key (\*) | `#gltf/2026-01-31_keystar0_581618f213980fbe_0.glb` |
| Pound key (#) | `#gltf/2026-01-31_keypound_8c1588da73eef569_0.glb` |

**Sounds** (hosted at a fixed CDN location — do NOT substitute with game room ID):

| Sound | URL |
|-------|-----|
| Key click | `https://d365bxku1h71bo.cloudfront.net/uploads/06730913-c11c-4438-9292-485689fc74d0/7b0091463b98e6e7d7cbb6fc6e957f1c.mp3` |
| Success buzz | `https://d365bxku1h71bo.cloudfront.net/uploads/06730913-c11c-4438-9292-485689fc74d0/c5648f4ae40337750cd688b0598b0bd0.mp3` |
| Error buzz | `https://d365bxku1h71bo.cloudfront.net/uploads/06730913-c11c-4438-9292-485689fc74d0/62be125f5212f6dc706eb16a4774b1dd.mp3` |

### Complete Component

```python
"""Keypad code entry — pre-built asset pack component.

Usage in generate.py:
    from components.keypad import build_keypad
    kp = build_keypad(
        pos=(5.0, 1.3, -9.95),
        rot=(-0.7071068, 0, 0, -0.7071068),
        correct_code=1234,
        start_id=500,
        quest_number=0,
        creator_uid=CREATOR_UID,
    )
    items.update(kp["items"])
    logic.update(kp["logic"])
    quests.update(kp["quests"])
"""
from portals_core import create_glb
from portals_effects import (
    basic_interaction, quest_effector, add_task_to_logic,
    trigger_on_click, trigger_player_logged_in,
    effector_function, effector_play_animation_once,
    effector_stop_animation, effector_play_sound_once,
    effector_notification, effector_show, effector_hide,
)
from portals_utils import create_quest_pair

# ── Pre-built asset URLs ──────────────────────────────────────────────────

KEYPAD_BODY_URL = "#gltf/2026-01-31_keybox00_82c2beb69144a28f_0.glb"
KEY_URLS = [
    "#gltf/2026-01-31_key00000_bbabbca37a7a1fd1_0.glb",  # 0
    "#gltf/2026-01-31_key10000_1a7c52510170cbba_0.glb",  # 1
    "#gltf/2026-01-31_key20000_a5c7bce096e32806_0.glb",  # 2
    "#gltf/2026-01-31_key30000_12eb2a31c5efd422_0.glb",  # 3
    "#gltf/2026-01-31_key40000_e0f15ceafecce4f1_0.glb",  # 4
    "#gltf/2026-01-31_key50000_2f99bdcc47cf4f9d_0.glb",  # 5
    "#gltf/2026-01-31_key60000_f5433b73ac91634c_0.glb",  # 6
    "#gltf/2026-01-31_key70000_ea0ba454be69e40b_0.glb",  # 7
    "#gltf/2026-01-31_key80000_9e5cea8a1cdc0688_0.glb",  # 8
    "#gltf/2026-01-31_key90000_27d056eca5ca8980_0.glb",  # 9
]
STAR_KEY_URL = "#gltf/2026-01-31_keystar0_581618f213980fbe_0.glb"
POUND_KEY_URL = "#gltf/2026-01-31_keypound_8c1588da73eef569_0.glb"
LOCK_CLOSED_URL = "#gltf/2026-01-31_keyclose_6bb46245c5b9aa89_0.glb"
LOCK_OPEN_URL = "#gltf/2026-01-31_keyopen0_713d932433207ab6_0.glb"

CDN_BASE = "https://d365bxku1h71bo.cloudfront.net/uploads/06730913-c11c-4438-9292-485689fc74d0"
CLICK_SOUND = f"{CDN_BASE}/7b0091463b98e6e7d7cbb6fc6e957f1c.mp3"
SUCCESS_SOUND = f"{CDN_BASE}/c5648f4ae40337750cd688b0598b0bd0.mp3"
ERROR_SOUND = f"{CDN_BASE}/62be125f5212f6dc706eb16a4774b1dd.mp3"

KEYPAD_SCALE = (3.5, 3.5, 3.5)
CHILD_ROT = (0, 0, 0, 1)  # identity — children NEVER get the body rotation


def build_keypad(pos, rot, correct_code, start_id, quest_number, creator_uid,
                 var_name="codeEntry", code_length=4):
    """Build a complete keypad with all items, logic, quests, and feedback.

    Args:
        pos: (x, y, z) world position for the keypad body.
        rot: (x, y, z, w) quaternion for the keypad body.
             Wall-mount facing +Z: (-0.7071068, 0, 0, -0.7071068)
        correct_code: Integer PIN code (e.g. 1234). Must match code_length digits.
        start_id: First item ID. Uses start_id through start_id+14 (15 items total).
        quest_number: Quest number prefix (0, 1, 2...). Avoid collisions with other quests.
        creator_uid: Firebase UID of the room creator.
        var_name: Variable name for digit accumulation (default "codeEntry").
                  Change this when using multiple keypads in the same room.
        code_length: Number of digits (default 4). Adjusts guard and validator range.

    Returns:
        {"items": {...}, "logic": {...}, "quests": {...},
         "keypad_quest_id": str, "keypad_quest_name": str}
    """
    items = {}
    logic = {}
    quests = {}

    body_id = start_id
    digit_guard = 10 ** (code_length - 1)  # 4 digits → 1000, 6 digits → 100000
    range_max = (10 ** code_length) - 1     # 4 digits → 9999, 6 digits → 999999

    # ── Quests ─────────────────────────────────────────────────────────────

    kp = create_quest_pair(quest_number, "keypad", creator_uid)
    quests.update(kp["entries"])
    keypad_quest_id = kp["quest_id"]
    keypad_quest_name = kp["quest_name"]      # e.g. "0_keypad"

    wc = create_quest_pair(quest_number + 1, "wrongCode", creator_uid)
    quests.update(wc["entries"])
    wrong_quest_id = wc["quest_id"]
    wrong_quest_name = wc["quest_name"]       # e.g. "1_wrongCode"

    # ── Helper: wire a clickable key ───────────────────────────────────────

    def _wire_key(key_id, click_effect=None):
        """Wire animation reset, press animation, click sound, and optional click effect."""
        sid = str(key_id)

        # Reset animation on login (prevents stuck mid-press state)
        add_task_to_logic(logic[sid], basic_interaction(
            trigger_player_logged_in(),
            effector_stop_animation()
        ))

        # Press animation on click (speed 3.0 for snappy feel)
        add_task_to_logic(logic[sid], basic_interaction(
            trigger_on_click(),
            effector_play_animation_once(speed=3.0)
        ))

        # Click sound
        add_task_to_logic(logic[sid], basic_interaction(
            trigger_on_click(),
            effector_play_sound_once(url=CLICK_SOUND, distance=-1, preload=True)
        ))

        # Optional: digit append, clear, etc.
        if click_effect is not None:
            add_task_to_logic(logic[sid], basic_interaction(
                trigger_on_click(),
                click_effect
            ))

    # ── Create items ───────────────────────────────────────────────────────

    # Body (parent) — world space position/rotation
    body_item, body_logic = create_glb(
        pos=pos, glb_url=KEYPAD_BODY_URL,
        scale=KEYPAD_SCALE, rot=rot,
        collider=False  # body is visual only; keys handle clicks
    )
    items[str(body_id)] = body_item
    logic[str(body_id)] = body_logic

    # Digit keys 0-9 — children at (0,0,0), identity rotation
    for digit in range(10):
        key_id = body_id + 1 + digit
        key_item, key_logic = create_glb(
            pos=(0, 0, 0), glb_url=KEY_URLS[digit],
            scale=KEYPAD_SCALE, rot=CHILD_ROT,
            collider=True
        )
        key_item["parentItemID"] = body_id
        items[str(key_id)] = key_item
        logic[str(key_id)] = key_logic

        # Wire: animation + sound + digit append
        _wire_key(key_id, click_effect=effector_function(
            f"if($N{{{var_name}}} < {float(digit_guard)},"
            f" SetVariable('{var_name}', ($N{{{var_name}}} * 10.0) + {float(digit)}, 0.0),"
            f" 0.0)"
        ))

    # Star key (*) — clear/reset
    star_id = body_id + 11
    star_item, star_logic = create_glb(
        pos=(0, 0, 0), glb_url=STAR_KEY_URL,
        scale=KEYPAD_SCALE, rot=CHILD_ROT,
        collider=True
    )
    star_item["parentItemID"] = body_id
    items[str(star_id)] = star_item
    logic[str(star_id)] = star_logic
    _wire_key(star_id, click_effect=effector_function(
        f"SetVariable('{var_name}', 0.0, 0.0)"
    ))

    # Pound key (#) — decorative (animation + sound only)
    pound_id = body_id + 12
    pound_item, pound_logic = create_glb(
        pos=(0, 0, 0), glb_url=POUND_KEY_URL,
        scale=KEYPAD_SCALE, rot=CHILD_ROT,
        collider=True
    )
    pound_item["parentItemID"] = body_id
    items[str(pound_id)] = pound_item
    logic[str(pound_id)] = pound_logic
    _wire_key(pound_id)  # no click_effect — just animation + sound

    # ── Lock indicators (children of body) ─────────────────────────────────

    lock_closed_id = body_id + 13
    lock_open_id = body_id + 14

    for lock_url, lock_id in [(LOCK_CLOSED_URL, lock_closed_id), (LOCK_OPEN_URL, lock_open_id)]:
        lock_item, lock_logic = create_glb(
            pos=(0, 0, 0), glb_url=lock_url,
            scale=KEYPAD_SCALE, rot=CHILD_ROT,
            collider=False
        )
        lock_item["parentItemID"] = body_id
        items[str(lock_id)] = lock_item
        logic[str(lock_id)] = lock_logic

    # ── Validator (reactive, on body) ──────────────────────────────────────

    # IMPORTANT: SetTask in NCalc uses the BARE name (no number prefix).
    # "keypad" not "0_keypad". quest_effector uses the full prefixed name.
    validator_expr = (
        f"if($N{{{var_name}}} >= {float(digit_guard)}"
        f" && $N{{{var_name}}} <= {float(range_max)},"
        f" if($N{{{var_name}}} == {float(correct_code)},"
        f" SetTask('keypad', 'Completed', 0.0),"
        f" SetTask('wrongCode', 'Completed', 0.0)"
        f" + SetVariable('{var_name}', 0.0, 0.5)"
        f" + SetTask('wrongCode', 'NotActive', 0.5)),"
        f" 0.0)"
    )

    # effector_function() has no reactive param — add "R" manually
    validator_effect = effector_function(validator_expr)
    validator_effect["R"] = True

    add_task_to_logic(logic[str(body_id)], basic_interaction(
        trigger_player_logged_in(),
        validator_effect
    ))

    # ── Success/error feedback (on body) ───────────────────────────────────

    # quest_effector uses FULL prefixed name (opposite of SetTask in NCalc)

    # Correct code → "Code Accepted!" + success sound
    add_task_to_logic(logic[str(body_id)], quest_effector(
        quest_id=keypad_quest_id, quest_name=keypad_quest_name,
        target_state=2,
        effector=effector_notification(
            text="<color=#189033>Code Accepted!</color>",
            hide_background=True
        )
    ))
    add_task_to_logic(logic[str(body_id)], quest_effector(
        quest_id=keypad_quest_id, quest_name=keypad_quest_name,
        target_state=2,
        effector=effector_play_sound_once(url=SUCCESS_SOUND, distance=-1, preload=True)
    ))

    # Wrong code → "Wrong Code!" + error sound
    add_task_to_logic(logic[str(body_id)], quest_effector(
        quest_id=wrong_quest_id, quest_name=wrong_quest_name,
        target_state=2,
        effector=effector_notification(
            text="<color=#FF2A00>Wrong Code!</color>",
            hide_background=True
        )
    ))
    add_task_to_logic(logic[str(body_id)], quest_effector(
        quest_id=wrong_quest_id, quest_name=wrong_quest_name,
        target_state=2,
        effector=effector_play_sound_once(url=ERROR_SOUND, distance=-1, preload=True)
    ))

    # ── Lock indicator visibility (quest-driven) ──────────────────────────

    # Red lock (closed): visible at state 0 (NotActive), hides on success
    add_task_to_logic(logic[str(lock_closed_id)], quest_effector(
        quest_id=keypad_quest_id, quest_name=keypad_quest_name,
        target_state=0, effector=effector_show()
    ))
    add_task_to_logic(logic[str(lock_closed_id)], quest_effector(
        quest_id=keypad_quest_id, quest_name=keypad_quest_name,
        target_state=2, effector=effector_hide()
    ))

    # Green lock (open): hidden at state 0 (NotActive), shows on success
    add_task_to_logic(logic[str(lock_open_id)], quest_effector(
        quest_id=keypad_quest_id, quest_name=keypad_quest_name,
        target_state=0, effector=effector_hide()
    ))
    add_task_to_logic(logic[str(lock_open_id)], quest_effector(
        quest_id=keypad_quest_id, quest_name=keypad_quest_name,
        target_state=2, effector=effector_show()
    ))

    return {
        "items": items,
        "logic": logic,
        "quests": quests,
        "keypad_quest_id": keypad_quest_id,
        "keypad_quest_name": keypad_quest_name,
    }
```

### Placement Notes

- **Wall-mount rotation** facing +Z: `(-0.7071068, 0, 0, -0.7071068)` (−90° X). For other walls, compose with a Y rotation using `yrot()` from `portals_utils`.
- **Y height**: ~1.2–1.5 for chest-height access (player eye level is ~1.6).
- **Z offset**: Place body slightly in front of wall surface to avoid z-fighting.
- The returned `keypad_quest_id` and `keypad_quest_name` let you wire other items to the keypad quest (doors, gates, locks — see Variations below).

### Connecting the Keypad to Your Game

The keypad's output is a **quest**. When the correct code is entered, that quest reaches state 2 (Completed). Any item in the room can react to this state change — that's how you make things happen when the code is correct.

The returned dict includes `keypad_quest_id` and `keypad_quest_name` — pass these to `quest_effector()` on any item to wire it up:

```python
from portals_effects import (
    quest_effector, add_task_to_logic,
    effector_play_animation_once, effector_hide,
    effector_play_sound_once, effector_show,
    effector_notification,
)

# Build the keypad
kp = build_keypad(pos=(...), rot=(...), correct_code=4567, ...)
items.update(kp["items"])
logic.update(kp["logic"])
quests.update(kp["quests"])

quest_id = kp["keypad_quest_id"]
quest_name = kp["keypad_quest_name"]
```

Then wire any number of downstream effects. Each is independent — add as many as you need:

```python
# Door plays its open animation
add_task_to_logic(logic[str(door_id)], quest_effector(
    quest_id=quest_id, quest_name=quest_name,
    target_state=2, effector=effector_play_animation_once(speed=1.0)
))

# Invisible collision wall disappears (so player can walk through)
add_task_to_logic(logic[str(wall_id)], quest_effector(
    quest_id=quest_id, quest_name=quest_name,
    target_state=2, effector=effector_hide()
))

# Hidden room lights up (a light that was hidden becomes visible)
add_task_to_logic(logic[str(light_id)], quest_effector(
    quest_id=quest_id, quest_name=quest_name,
    target_state=2, effector=effector_show()
))

# Dramatic sound plays
add_task_to_logic(logic[str(any_item_id)], quest_effector(
    quest_id=quest_id, quest_name=quest_name,
    target_state=2,
    effector=effector_play_sound_once(url=DOOR_OPEN_SOUND, distance=-1, preload=True)
))

# Player gets a notification
add_task_to_logic(logic[str(any_item_id)], quest_effector(
    quest_id=quest_id, quest_name=quest_name,
    target_state=2,
    effector=effector_notification(text="<color=#FFD700>The vault is open!</color>",
                                   hide_background=True)
))
```

**Key point:** The effects go on the *target* items, not on the keypad. The door gets the "play animation" effect. The wall gets the "hide" effect. The keypad doesn't need to know about any of them — it just completes the quest, and everything else reacts.

You can also react to the **wrong code** quest for punishment or drama:

```python
wrong_id = wc_quest_id    # from create_quest_pair(1, "wrongCode", ...)
wrong_name = wc_quest_name

# Alarm sound on wrong code
add_task_to_logic(logic[str(alarm_id)], quest_effector(
    quest_id=wrong_id, quest_name=wrong_name,
    target_state=2,
    effector=effector_play_sound_once(url=ALARM_SOUND, distance=-1, preload=True)
))
```

---

## Part 2: Custom Keypad (Build Your Own)

The digit accumulation pattern works with **any clickable items** — not just the pre-built GLB keypad. You can use ResizableCubes, custom 3D models, animated buttons, or any combination. This section explains the generic pattern so you can build a keypad with whatever items fit your game's visual style.

### What Makes a "Key"

A key is any item that:
1. **Receives `OnClickEvent`** — must have collision enabled (`collider=True` for GLBs, or any solid item type)
2. **Gives click feedback** — animation, sound, color change, or any combination
3. **Appends a digit** — runs a FunctionEffector with the digit accumulation formula

That's it. The item type doesn't matter. Common options:

| Item type | Click feedback options | Notes |
|-----------|----------------------|-------|
| GLB with animation | `PlayAnimationOnce` + sound | Best feel — actual press animation |
| ResizableCube | Sound + color change (via notification) | Simple, no model needed |
| GLB without animation | Sound only | Works but feels flat |
| GlbCollectable | Sound + collect animation | Unusual but functional |

### Arranging Keys

**Pre-built GLBs with baked positions:** All children at `(0,0,0)` — the model geometry handles layout. This is what Part 1 uses.

**Manual positioning (cubes, custom GLBs, any items):** You arrange the grid yourself. Typical 3×4 phone layout:

```python
# 3-column grid, bottom-to-top: 1-2-3, 4-5-6, 7-8-9, *-0-#
# Adjust spacing based on button size
BUTTON_SIZE = 0.3
GAP = 0.05
STEP = BUTTON_SIZE + GAP

GRID_POSITIONS = {
    1: (-STEP, 2*STEP, 0),   2: (0, 2*STEP, 0),   3: (STEP, 2*STEP, 0),
    4: (-STEP, STEP, 0),     5: (0, STEP, 0),      6: (STEP, STEP, 0),
    7: (-STEP, 0, 0),        8: (0, 0, 0),         9: (STEP, 0, 0),
    "star": (-STEP, -STEP, 0), 0: (0, -STEP, 0),  "pound": (STEP, -STEP, 0),
}
```

If using a parent-child hierarchy, these are local-space positions relative to the parent. If using standalone items, these are world-space offsets from your keypad's center.

### The Three Pieces You Need

Regardless of item type, every custom keypad has three pieces. The first two (keys + validator) handle input. The third (feedback) is optional — the real outcome comes from wiring other items to the keypad quest, exactly like Part 1's "Connecting the Keypad to Your Game" section.

#### 1. Per-key wiring

Each key needs the same interactions. Adapt the feedback to your item type:

```python
from portals_effects import (
    basic_interaction, add_task_to_logic,
    trigger_on_click, trigger_player_logged_in,
    effector_function, effector_play_animation_once,
    effector_stop_animation, effector_play_sound_once,
)

def wire_custom_key(logic, key_id, digit, var_name="codeEntry",
                    digit_guard=1000.0, click_sound=None):
    """Wire any clickable item as a digit key.

    Args:
        logic: The logic dict (keyed by string item ID).
        key_id: String item ID of the key.
        digit: Integer 0-9.
        var_name: Variable name for code accumulation.
        digit_guard: Max value before lockout (1000.0 for 4-digit codes).
        click_sound: Optional sound URL. Pass None to skip sound.
    """
    # If the item has an animation, reset it on login
    # (safe to include even if item has no animation — it's a no-op)
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_player_logged_in(),
        effector_stop_animation()
    ))

    # Animation feedback on click (only useful for GLBs with embedded animations)
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_on_click(),
        effector_play_animation_once(speed=3.0)
    ))

    # Sound feedback on click
    if click_sound:
        add_task_to_logic(logic[key_id], basic_interaction(
            trigger_on_click(),
            effector_play_sound_once(url=click_sound, distance=-1, preload=True)
        ))

    # Digit accumulation (the core mechanic — same for all item types)
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_on_click(),
        effector_function(
            f"if($N{{{var_name}}} < {digit_guard},"
            f" SetVariable('{var_name}', ($N{{{var_name}}} * 10.0) + {float(digit)}, 0.0),"
            f" 0.0)"
        )
    ))
```

For items **without** animations (e.g. ResizableCubes), skip the `PlayAnimationOnce` and `StopAnimationEvt` calls — they won't cause errors but are unnecessary.

#### 2. Reactive validator

Place this on any item in the room — it doesn't have to be a key or the keypad body. It just needs to exist. A common choice is a host cube or the keypad backplate.

```python
from portals_utils import create_quest_pair

# Create quests
kp = create_quest_pair(0, "keypad", CREATOR_UID)
quests.update(kp["entries"])

wc = create_quest_pair(1, "wrongCode", CREATOR_UID)
quests.update(wc["entries"])

# Validator expression
# IMPORTANT: SetTask uses BARE name ("keypad"), quest_effector uses FULL name ("0_keypad")
correct_code = 1234.0
digit_guard = 1000.0      # 10^(code_length - 1)
range_max = 9999.0        # 10^code_length - 1

validator_expr = (
    f"if($N{{codeEntry}} >= {digit_guard} && $N{{codeEntry}} <= {range_max},"
    f" if($N{{codeEntry}} == {correct_code},"
    f" SetTask('keypad', 'Completed', 0.0),"
    f" SetTask('wrongCode', 'Completed', 0.0)"
    f" + SetVariable('codeEntry', 0.0, 0.5)"
    f" + SetTask('wrongCode', 'NotActive', 0.5)),"
    f" 0.0)"
)

# Build effect and add reactive flag manually
validator_effect = effector_function(validator_expr)
validator_effect["R"] = True  # CRITICAL: without this, validator runs once and never re-checks

add_task_to_logic(logic[host_item_id], basic_interaction(
    trigger_player_logged_in(),
    validator_effect
))
```

#### 3. Success/error feedback

Wire quest-linked effects to the host item (or any item):

```python
from portals_effects import quest_effector, effector_notification, effector_play_sound_once

# Correct code feedback
add_task_to_logic(logic[host_item_id], quest_effector(
    quest_id=kp["quest_id"],
    quest_name=kp["quest_name"],      # "0_keypad" — FULL prefixed name
    target_state=2,
    effector=effector_notification(
        text="<color=#189033>Code Accepted!</color>",
        hide_background=True
    )
))

# Wrong code feedback
add_task_to_logic(logic[host_item_id], quest_effector(
    quest_id=wc["quest_id"],
    quest_name=wc["quest_name"],      # "1_wrongCode" — FULL prefixed name
    target_state=2,
    effector=effector_notification(
        text="<color=#FF2A00>Wrong Code!</color>",
        hide_background=True
    )
))
```

### Example: Cube Keypad

A minimal 4-button keypad using colored cubes (for testing or stylized games):

```python
from portals_core import create_cube

COLORS = ["FF0000", "00FF00", "0000FF", "FFFF00"]  # red, green, blue, yellow
CODE = [2, 0, 3, 1]  # blue, red, yellow, green — the correct sequence as digits 0-3

# Create 4 button cubes in a row
for i in range(4):
    btn_id = start_id + i
    btn = create_cube(
        pos=(base_x + i * 0.8, base_y, base_z),
        scale=(0.6, 0.6, 0.1),
        color=COLORS[i]
    )
    items[str(btn_id)] = btn
    logic[str(btn_id)] = {"Tasks": [], "ViewNodes": []}

    wire_custom_key(logic, str(btn_id), digit=i,
                    digit_guard=1000.0, click_sound=CLICK_SOUND)
```

This creates 4 colored buttons where pressing them in the right order (blue → red → yellow → green) enters code `2031`. The validator and feedback are wired the same way as any other keypad.

---

## Variations

### Different code lengths

Adjust two values:
1. The digit guard threshold on each key: `10^(code_length - 1)`
2. The range check in the validator: `10^(code_length - 1)` to `10^code_length - 1`

The pre-built component's `code_length` parameter handles this automatically. For custom keypads, pass the adjusted `digit_guard` to `wire_custom_key()`.

### Multiple keypads (different codes)

Use different `var_name` and `quest_number` values per keypad:

```python
# Pre-built: two keypads with different codes and variables
kp_a = build_keypad(pos=(...), rot=(...), correct_code=1234,
                    start_id=500, quest_number=0, creator_uid=UID,
                    var_name="codeA")
kp_b = build_keypad(pos=(...), rot=(...), correct_code=5678,
                    start_id=520, quest_number=2, creator_uid=UID,
                    var_name="codeB")
```

### Lock indicators (visual feedback on keypad)

Two overlapping items that swap visibility — red lock shows by default, green lock shows on success. Both are children of the keypad body (or standalone items near the keypad).

```python
from portals_effects import effector_show, effector_hide

# Lock indicator GLBs from the pre-built asset pack
LOCK_CLOSED_URL = "#gltf/2026-01-31_keyclose_6bb46245c5b9aa89_0.glb"
LOCK_OPEN_URL = "#gltf/2026-01-31_keyopen0_713d932433207ab6_0.glb"

# Create as children of body (same pattern as keys)
for lock_url, lock_id in [(LOCK_CLOSED_URL, lock_closed_id), (LOCK_OPEN_URL, lock_open_id)]:
    lock_item, lock_logic = create_glb(
        pos=(0, 0, 0), glb_url=lock_url,
        scale=KEYPAD_SCALE, rot=(0, 0, 0, 1),  # identity rotation
        collider=False
    )
    lock_item["parentItemID"] = body_id
    items[str(lock_id)] = lock_item
    logic[str(lock_id)] = lock_logic

# Red lock (closed): visible at state 0 (NotActive — default on every login), hides on success
add_task_to_logic(logic[str(lock_closed_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=0, effector=effector_show()
))
add_task_to_logic(logic[str(lock_closed_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=2, effector=effector_hide()
))

# Green lock (open): hidden at state 0 (NotActive), shows on success
add_task_to_logic(logic[str(lock_open_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=0, effector=effector_hide()
))
add_task_to_logic(logic[str(lock_open_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=2, effector=effector_show()
))
```

### Reward container (lockbox, safe, door)

The keypad quest can trigger any effect on any item:

```python
LOCKBOX_URL = "#gltf/2026-01-31_lockbox0_985976b3cfd8fb35_0.glb"
OPEN_SOUND = "https://d365bxku1h71bo.cloudfront.net/uploads/06730913-c11c-4438-9292-485689fc74d0/0d4b0b2c251231155e7b3054c6e27e88.mp3"

lockbox_item, lockbox_logic = create_glb(
    pos=(lockbox_x, lockbox_y, lockbox_z), glb_url=LOCKBOX_URL,
    scale=(0.362, 0.362, 0.362),
    rot=(-0.7071068, 0, 0, -0.7071068),
)
items[str(lockbox_id)] = lockbox_item
logic[str(lockbox_id)] = lockbox_logic

# Stay closed while keypad incomplete
add_task_to_logic(logic[str(lockbox_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=1, effector=effector_stop_animation()
))

# Open on correct code
add_task_to_logic(logic[str(lockbox_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=2, effector=effector_play_animation_once(speed=1.0)
))

# Open sound
add_task_to_logic(logic[str(lockbox_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=2, effector=effector_play_sound_once(url=OPEN_SOUND, distance=-1, preload=True)
))
```

### Door/gate wiring

```python
# Door opens when keypad quest completes
add_task_to_logic(logic[str(door_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=2, effector=effector_play_animation_once(speed=1.0)
))

# Invisible wall hides (collision barrier removed)
add_task_to_logic(logic[str(wall_id)], quest_effector(
    quest_id=keypad_quest_id, quest_name=keypad_quest_name,
    target_state=2, effector=effector_hide()
))
```

---

## Critical Rules

1. **Child rotation must be identity.** Children inherit the parent's world rotation. Giving a child the same rotation as the parent causes double-rotation (parent rotation × child rotation). Always use `rot = (0, 0, 0, 1)` for children.

2. **Reactive flag must be added manually.** `effector_function()` does not accept a `reactive` parameter. Build the effect dict, then add `"R": True` to it. Without reactive mode, the validator only runs once on login and never re-checks when digits are entered.

3. **SetTask vs quest_effector use different name formats.** This is the most common source of silent failures:
   - `SetTask()` in NCalc expressions uses the **bare name**: `SetTask('keypad', 'Completed', 0.0)`
   - `quest_effector()` in Python uses the **full name with number prefix**: `quest_name="0_keypad"`
   - If you use the full name in SetTask or the bare name in quest_effector, the quest will silently fail to advance.

4. **SetTask state must be `'Completed'`** (not `'Active'`). `'Completed'` advances the quest to state 2, which is what `quest_effector(target_state=2, ...)` watches. Using `'Active'` would set state 1, so none of the success/error feedback would fire.

5. **All pre-built key children at (0, 0, 0).** The pre-built key GLBs have their layout baked into model coordinates. Placing them all at `pos = (0, 0, 0)` relative to the parent produces the correct 3×4 grid. Do not manually offset them. For custom keys, you position each one yourself.

6. **Same scale for all pre-built items.** The body and every key must use the same scale (default: 3.5). Mismatched scales will misalign the baked key layout.

7. **Guard prevents overflow.** The digit guard check on each key prevents the variable from growing beyond N digits. Without it, pressing keys after the code is full would corrupt the value.

8. **Reset delay matters.** The 0.5s delay on `SetVariable('codeEntry', 0.0, 0.5)` in the wrong-code path gives the error notification time to display before the keypad accepts new input.

9. **wrongCode quest must reset to NotActive.** After `SetTask('wrongCode', 'Completed', 0.0)` fires, the quest stays at state 2. If you don't reset it with `SetTask('wrongCode', 'NotActive', 0.5)`, the error feedback will only fire once — subsequent wrong codes will silently fail because the quest is already Completed. The 0.5s delay lets the feedback play before the reset.

10. **Animation reset on login for ALL animated keys.** Every item with an animation needs `trigger_player_logged_in() → effector_stop_animation()`. Without this, items may start in a random animation frame when a player enters the room.

11. **Per-player variables.** `SetVariable('codeEntry', value, 0.0)` — third arg `0.0` = per-player. Always use `0.0` so each player has their own code entry state.

12. **Clickable items need collision.** Keys must have `collider=True` (GLBs) or be solid item types. The host/body item can skip collision if it's just a visual container.

13. **Sound URLs are fixed CDN paths.** The pre-built sounds are uploaded to room `06730913-c11c-4438-9292-485689fc74d0`. Do not substitute with the game room's ID.
