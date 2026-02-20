---
name: Keypad Code Entry
category: mechanics
tags: [keypad, code, pin, password, lock, escape room, puzzle, safe, combination, door, security]
patterns: [variable-tracking, conditional-logic, quest-advancing-trigger, direct-trigger-effect]
summary: Numeric code entry system using clickable animated key buttons, digit accumulation via variables, and reactive code validation with success/failure feedback
---

# Keypad Code Entry

A physical-style numeric keypad where players click individual key buttons to enter a PIN code. Each press animates the key, plays a click sound, and appends a digit to a code variable. When enough digits are entered, a reactive validator checks the code — correct input completes a quest (unlocking doors, safes, etc.), wrong input shows an error and resets.

## How It Works

The core technique is **digit accumulation**: a variable stores the code as a number, and each key press shifts left by one digit and adds the new one:

```
codeEntry = (codeEntry × 10) + digit
```

Press 1, then 2, then 3, then 4 → `codeEntry` goes: `0 → 1 → 12 → 123 → 1234`

A **reactive FunctionEffector** (`"R": true`) on the keypad body watches `codeEntry`. When it reaches 4 digits (≥1000 and ≤9999), it auto-validates — no submit button needed.

## Items Needed

- **Keypad body** — GLB parent that holds all keys and contains the validation logic
- **Digit keys 0-9** — 10 GLB children, each with press animation + click sound + digit append
- **Optional: * and # keys** — decorative or wired for clear/submit
- **Optional: lock indicators** — two overlapping GLBs that swap visibility on success (closed → open)
- **Optional: reward container** — GLB with open animation triggered on success (safe, lockbox, door)

## Quests

Two quests with simple binary states:

| Quest | Purpose |
|-------|---------|
| `keypad` | inProgress → completed on correct code |
| `wrongCode` | inProgress → completed on wrong code (resets automatically) |

```python
from portals_utils import make_quest

quests["keypad"] = make_quest(name="keypad", display_name="Keypad", creator=CREATOR_UID, shared=False)
quests["wrongCode"] = make_quest(name="wrongCode", display_name="Wrong Code", creator=CREATOR_UID, shared=False)
```

## Wiring Pattern

### 1. Digit key (repeat for each digit 0-9)

Each key has 4 interactions: reset animation on load, press animation on click, click sound, and digit append.

```python
from portals_effects import (
    basic_interaction, trigger_on_click, trigger_on_player_logged_in,
    add_task_to_logic, effector_function, effector_play_animation_once,
    effector_stop_animation, effector_play_sound
)

CLICK_SOUND = "YOUR_CLICK_SOUND_URL"

def wire_digit_key(logic, key_id, digit):
    """Wire a single digit key with animation, sound, and digit append."""

    # Reset animation on load (prevents keys from being stuck mid-press)
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_on_player_logged_in(),
        effector_stop_animation()
    ))

    # Press animation on click (speed 3.0 for snappy feedback)
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_on_click(),
        effector_play_animation_once(speed=3.0)
    ))

    # Click sound
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_on_click(),
        effector_play_sound(url=CLICK_SOUND, distance=-1, preload=True)
    ))

    # Append digit to code variable (only if < 4 digits entered)
    add_task_to_logic(logic[key_id], basic_interaction(
        trigger_on_click(),
        effector_function(
            f"if($N{{codeEntry}} < 1000.0,\n"
            f"   SetVariable('codeEntry', ($N{{codeEntry}} * 10.0) + {float(digit)}, 0.0),\n"
            f"   0.0\n"
            f")",
            shared=False
        )
    ))

# Wire all 10 digit keys
for digit in range(10):
    wire_digit_key(logic, key_ids[digit], digit)
```

**Key detail:** The guard `$N{codeEntry} < 1000.0` prevents more than 4 digits from being entered. For a 4-digit code, 1000.0 means "already has 4 digits" (the minimum 4-digit number). Adjust this threshold for different code lengths:
- 3-digit code: `< 100.0`
- 4-digit code: `< 1000.0`
- 5-digit code: `< 10000.0`
- 6-digit code: `< 100000.0`

### 2. Reactive code validator (on the keypad body)

The validator uses `"R": true` on the FunctionEffector, which makes it **reactive** — it automatically re-evaluates whenever `codeEntry` changes. No explicit re-trigger needed.

```python
# The correct code (change this!)
CORRECT_CODE = 1234.0

# Validator expression
validator_expr = (
    f"if($N{{codeEntry}} >= 1000.0 && $N{{codeEntry}} <= 9999.0,\n"
    f"   if($N{{codeEntry}} == {CORRECT_CODE},\n"
    f"      SetTask('keypad', 'Active', 0.0),\n"
    f"      SetTask('wrongCode', 'Active', 0.0) +\n"
    f"      SetVariable('codeEntry', 0.0, 0.5)\n"
    f"   ),\n"
    f"   0.0\n"
    f")"
)

# Wire with reactive flag — this is the critical piece
add_task_to_logic(logic[keypad_body_id], basic_interaction(
    trigger_on_player_logged_in(),
    effector_function(validator_expr, reactive=True)
))
```

**How it works:**
1. Player logs in → validator starts watching `codeEntry`
2. Each key press updates `codeEntry` → validator re-evaluates
3. While `codeEntry` < 1000 (fewer than 4 digits) → no-op
4. When `codeEntry` reaches 4 digits → checks against `CORRECT_CODE`
5. Match → completes `keypad` quest
6. No match → completes `wrongCode` quest + resets `codeEntry` to 0 after 0.5s delay

**The 0.5s reset delay** gives the error feedback time to display before the keypad resets.

### 3. Success feedback (on the keypad body)

```python
from portals_effects import (
    quest_interaction, effector_notification, effector_play_sound
)

SUCCESS_SOUND = "YOUR_SUCCESS_SOUND_URL"
ERROR_SOUND = "YOUR_ERROR_SOUND_URL"

# "Door Unlocked!" notification on correct code
add_task_to_logic(logic[keypad_body_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_notification(
        text="<color=#189033>Door Unlocked!</color>",
        hide_background=True
    )
))

# Success sound
add_task_to_logic(logic[keypad_body_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_play_sound(url=SUCCESS_SOUND, distance=-1, preload=True)
))

# "Wrong Code!" notification on incorrect code
add_task_to_logic(logic[keypad_body_id], quest_interaction(
    quest_name="wrongCode", quest_id=wrong_quest_id, target_state=2,
    effector=effector_notification(
        text="<color=#FF2A00>Wrong Code!</color>",
        hide_background=True
    )
))

# Error sound
add_task_to_logic(logic[keypad_body_id], quest_interaction(
    quest_name="wrongCode", quest_id=wrong_quest_id, target_state=2,
    effector=effector_play_sound(url=ERROR_SOUND, distance=-1, preload=True)
))
```

### 4. Lock indicators (optional visual feedback on keypad)

Two overlapping GLBs — one shows a closed lock, the other an open lock. They swap visibility when the code is correct.

```python
from portals_effects import effector_show, effector_hide

# Closed lock: visible by default, hides on success
add_task_to_logic(logic[lock_closed_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=1,  # inProgress
    effector=effector_show()
))
add_task_to_logic(logic[lock_closed_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,  # completed
    effector=effector_hide()
))

# Open lock: hidden by default, shows on success
add_task_to_logic(logic[lock_open_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_show()
))
add_task_to_logic(logic[lock_open_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=1,
    effector=effector_hide()
))
```

### 5. Reward container — safe/lockbox with open animation

```python
OPEN_SOUND = "YOUR_LOCKBOX_OPEN_SOUND_URL"

# Stay closed while keypad is incomplete
add_task_to_logic(logic[lockbox_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=1,
    effector=effector_stop_animation()
))

# Play open animation when code is correct
add_task_to_logic(logic[lockbox_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_play_animation_once(speed=1.0)
))

# Mechanical opening sound (slight delay to sync with animation)
add_task_to_logic(logic[lockbox_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_play_sound(url=OPEN_SOUND, distance=-1, preload=True, delay=0.2, volume=0.62)
))
```

---

## Pre-Built Asset Pack

A complete keypad asset set is available in the Portals CDN. These are production-tested animated GLBs with embedded press animations. Use these to skip the GLB creation step entirely.

### GLB Assets

| Asset | CDN Path | Purpose |
|-------|----------|---------|
| Keypad body | `#gltf/2026-01-31_keybox00_82c2beb69144a28f_0.glb` | Parent container — holds all keys |
| Key 0 | `#gltf/2026-01-31_key00000_bbabbca37a7a1fd1_0.glb` | Digit 0 button |
| Key 1 | `#gltf/2026-01-31_key10000_1a7c52510170cbba_0.glb` | Digit 1 button |
| Key 2 | `#gltf/2026-01-31_key20000_a5c7bce096e32806_0.glb` | Digit 2 button |
| Key 3 | `#gltf/2026-01-31_key30000_12eb2a31c5efd422_0.glb` | Digit 3 button |
| Key 4 | `#gltf/2026-01-31_key40000_e0f15ceafecce4f1_0.glb` | Digit 4 button |
| Key 5 | `#gltf/2026-01-31_key50000_2f99bdcc47cf4f9d_0.glb` | Digit 5 button |
| Key 6 | `#gltf/2026-01-31_key60000_f5433b73ac91634c_0.glb` | Digit 6 button |
| Key 7 | `#gltf/2026-01-31_key70000_ea0ba454be69e40b_0.glb` | Digit 7 button |
| Key 8 | `#gltf/2026-01-31_key80000_9e5cea8a1cdc0688_0.glb` | Digit 8 button |
| Key 9 | `#gltf/2026-01-31_key90000_27d056eca5ca8980_0.glb` | Digit 9 button |
| Star key | `#gltf/2026-01-31_keystar0_581618f213980fbe_0.glb` | * button (decorative or clear) |
| Pound key | `#gltf/2026-01-31_keypound_8c1588da73eef569_0.glb` | # button (decorative or submit) |
| Lock closed | `#gltf/2026-01-31_keyclose_6bb46245c5b9aa89_0.glb` | Closed lock indicator |
| Lock open | `#gltf/2026-01-31_keyopen0_713d932433207ab6_0.glb` | Open lock indicator |
| Lockbox | `#gltf/2026-01-31_lockbox0_985976b3cfd8fb35_0.glb` | Safe with open animation |

### Sound Assets

| Sound | CDN Path | Purpose |
|-------|----------|---------|
| Key click | `#{ID}/7b0091463b98e6e7d7cbb6fc6e957f1c.mp3?file=keyboard_key_click_#4-1769833309818.mp3` | Button press feedback |
| Success buzz | `#{ID}/c5648f4ae40337750cd688b0598b0bd0.mp3?file=positive_electric_bu_#3-1769885014726.mp3` | Correct code entered |
| Error buzz | `#{ID}/62be125f5212f6dc706eb16a4774b1dd.mp3?file=error_electric_buzze_#4-1769885042231.mp3` | Wrong code entered |
| Lockbox open | `#{ID}/0d4b0b2c251231155e7b3054c6e27e88.mp3?file=metal_door_squeaking_#4-1769884934103.mp3` | Mechanical opening |

### Placement

All items use a **parent-child hierarchy**. The keypad body is the parent; all keys and indicators are children at position (0, 0, 0) relative to it. This means you only need to position the keypad body — all children follow automatically.

```python
# Keypad body placement
KEYPAD_SCALE = 3.5  # all keypad items use this scale
KEYPAD_ROT = (-0.7071068, 0, 0, -0.7071068)  # -90° X rotation (face-mounted on wall)

# Lockbox placement (separate from keypad, nearby)
LOCKBOX_SCALE = 0.362
LOCKBOX_ROT = (-0.7071068, 0, 0, -0.7071068)  # same wall-mount rotation
```

The key GLBs have their positions baked into the model — when all placed at (0, 0, 0) relative to the parent at scale 3.5, they form a standard 3×4+2 phone-style keypad layout. No manual positioning of individual keys required.

---

## Variations

### Clear button (wire * key)

Wire the star key to reset `codeEntry` so players can start over without waiting for the wrong-code timeout:

```python
add_task_to_logic(logic[star_key_id], basic_interaction(
    trigger_on_click(),
    effector_function("SetVariable('codeEntry', 0.0, 0.0)", shared=False)
))
```

### Different code lengths

Adjust two values:
1. The digit guard threshold on each key
2. The range check in the validator

```python
# For a 6-digit code:
# Keys: change guard to < 100000.0
f"if($N{{codeEntry}} < 100000.0, ...)"

# Validator: change range to 100000-999999
f"if($N{{codeEntry}} >= 100000.0 && $N{{codeEntry}} <= 999999.0, ...)"
```

### Multiple keypads (different codes)

Use different variable names and quest names per keypad:

```python
# Keypad A — uses codeA variable and keypadA quest
wire_digit_key(logic, key_id, digit=5, var_name="codeA")
# Validator checks codeA == 1234, completes keypadA quest

# Keypad B — uses codeB variable and keypadB quest
wire_digit_key(logic, key_id, digit=5, var_name="codeB")
# Validator checks codeB == 5678, completes keypadB quest
```

### Door/gate wiring

The `keypad` quest can trigger any effect — not just a lockbox. Wire it to a door, gate, elevator, or any quest-gated effect:

```python
# Door opens when keypad quest completes
add_task_to_logic(logic[door_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_play_animation_once(speed=1.0)
))

# Invisible wall hides (collision barrier removed)
add_task_to_logic(logic[wall_id], quest_interaction(
    quest_name="keypad", quest_id=keypad_quest_id, target_state=2,
    effector=effector_hide()
))
```

---

## Critical Rules

1. **Reactive flag is essential.** The validator FunctionEffector MUST have `"R": true` (reactive mode). Without it, the validator only runs once on login and never re-checks when digits are entered. This is the `reactive=True` parameter in `effector_function()`.

2. **Digit keys must be children of the keypad body.** The pre-built GLBs have their layout baked into model coordinates — placing them all at (0,0,0) relative to the parent produces the correct 3×4 grid. Moving individual keys breaks the layout.

3. **Guard prevents overflow.** The `< 1000.0` check on each key prevents the variable from growing beyond 4 digits. Without it, pressing keys after 4 digits would corrupt the code (e.g., 12345 instead of staying at 1234).

4. **Reset delay matters.** The 0.5s delay on `SetVariable('codeEntry', 0.0, 0.5)` in the wrong-code path gives the error notification time to display before the keypad accepts new input. Without it, the error and reset happen simultaneously and players don't see feedback.

5. **Animation reset on login.** Every animated key needs a `PlayerLoggedIn → StopAnimationEvt` interaction. Without this, keys may start in a random animation frame when a player enters the room.

6. **Per-player variables.** Use `shared=False` (third arg `0.0` in SetVariable) so each player has their own code entry state. Shared mode would cause one player's key presses to affect another's entry.
