# Interactions & Effects

Complete reference for triggers, effects, and interaction patterns.

There are two systems for triggering effects on items:

1. **Basic Interactions** -- direct trigger to effect. Not persistent (no state stored). Fires immediately when triggered.
2. **Quest-Driven Task Effects** -- tied to quest states (Not Active, Active, Completed). Persistent -- state is stored and survives page reloads.

Both go in `logic[itemId].Tasks` — a separate top-level `logic` dict keyed by item ID, not embedded inside items.

**Adding interactions in Python:**
```python
from portals_effects import add_task_to_logic, basic_interaction, trigger_on_click, effector_notification

# portals_core creators return (item, logic) tuples
items[id_], logic[id_] = create_cube(pos=(0, 0.5, 0))

# Wire an interaction into the logic entry
task = basic_interaction(trigger_on_click(), effector_notification("Hello!", "00FF00"))
add_task_to_logic(logic[id_], task)
```

---

## Basic Interactions (Direct Trigger to Effect)

A basic interaction fires an effect immediately when a trigger occurs (e.g., player clicks the item). No quest needed. Not persistent.

The wrapper is `TaskTriggerSubscription`. It contains a `Trigger` field specifying the event, and a `DirectEffector` wrapping the effect.

**Full example -- click to MoveToSpot (absolute):**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnClickEvent"},
  "DirectEffector": {
    "Effector": {
      "$type": "MoveToSpot",
      "_transformState": {
        "position": [0, 5, 0],
        "rotation": [0, 0, 0, 1],
        "scale": [1, 1, 1]
      }
    },
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

**Full example -- click to MoveToSpot (relative):**

When `"relative": true` is set on the MoveToSpot effector, all `_transformState` values become **offsets from the item's current transform** instead of absolute world values. For example, `position: [1, 0, 0]` moves the item 1 unit in the +X direction from wherever it currently is.

```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnClickEvent"},
  "DirectEffector": {
    "Effector": {
      "$type": "MoveToSpot",
      "_transformState": {
        "position": [1, 0, 0],
        "rotation": [0, 0, 0, 1]
      },
      "relative": true
    },
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

### Key Differences from Quest-Driven Effects

| Property | Basic Interaction | Quest-Driven Effect |
|----------|-------------------|---------------------|
| `$type` | `TaskTriggerSubscription` | `TaskEffectorSubscription` |
| Has `Trigger` field | Yes | No |
| Has `DirectEffector` | Yes | No |
| Has `TaskTriggerId` | No | Yes (links to quest) |
| Persistence | Not persistent | Persistent (survives reload) |

### Click-to-Advance-Quest Trigger

A `TaskTriggerSubscription` can also directly change a **quest state** on click, without a `DirectEffector`. This links the click to a quest using the encoded TargetState values:

```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnClickEvent"},
  "Id": "unique-uuid",
  "TargetState": 111,
  "Name": "quest-name",
  "TaskTriggerId": "quest-id"
}
```

- Uses encoded `TargetState` values (same table as RunTriggersFromEffector, e.g., `111` = Not Active to Active)
- Has `TaskTriggerId` and `Name` linking it to a quest
- No `DirectEffector` -- the trigger changes the quest state directly
- Combine with `TaskEffectorSubscription` effects on other items to make clicking one item animate others

---

## Quest-Driven Task Effects

Animations driven by **quests**. Each quest has states (Not Active, Active, Completed). Items subscribe to quest state changes via `TaskEffectorSubscription` entries in their `logic[itemId].Tasks` array.

### Single Player vs Multiplayer Quests

Quests can be **single player** or **multiplayer**, controlled by the `Group` field:

| Type | `Group` field | Scope | Persistence |
|------|--------------|-------|-------------|
| Single player | `""` (empty) | Per-player | Saved between sessions |
| Non-persistent | `"nonPersistent"` | Per-player | Resets on leave/reload |
| Multiplayer | `"multiplayer"` | Shared (all players) | Saved between sessions |

### Quest Format

Quests come in pairs -- one `inProgress` entry and one `completed` entry sharing the same `EntryId`. Each pair represents a single logical quest. Quests can be created via MCP using the proper format.

**Critical requirements:**
- Quest names MUST follow the numbered format: `0_questname`, `1_nextquest`, `2_another`, etc.
- The numbered prefix is **required** -- quests will not work without it
- All fields listed below must always be present (even if empty or default values)

**Complete quest pair example (MCP flat-dict format):**

Quests are stored as a flat dict keyed by quest ID. Each logical quest has TWO entries (inProgress + completed) sharing the same `EntryId` but with DIFFERENT `id` values.

```json
{
  "mljstsdgsfy4d7": {
    "EntryId": "07b29300-f6df-47e4-8f55-5aa697303896",
    "Name": "0_assemble",
    "Description": "created in unity",
    "Status": "inProgress",
    "Group": "",
    "DisplayGroup": "",
    "Enabled": true,
    "RepeatableLimit": 0,
    "FinishTime": 0,
    "AutoStart": false,
    "TriggeredByInventory": false,
    "Requirements": [],
    "Creator": "<your-firebase-uid>",
    "TemplateName": "",
    "Tracked": true,
    "Visible": false,
    "ExtraText": "",
    "id": "mljstsdgsfy4d7"
  },
  "mljstsdiapl8qf": {
    "EntryId": "07b29300-f6df-47e4-8f55-5aa697303896",
    "Name": "0_assemble",
    "Description": "created in unity",
    "Status": "completed",
    "Group": "",
    "DisplayGroup": "",
    "Enabled": true,
    "RepeatableLimit": 0,
    "FinishTime": 0,
    "AutoStart": false,
    "TriggeredByInventory": false,
    "Requirements": [],
    "Rewards": [],
    "Creator": "<your-firebase-uid>",
    "TemplateName": "",
    "Tracked": true,
    "Visible": false,
    "ExtraText": "",
    "SuccessMsg": "",
    "id": "mljstsdiapl8qf"
  }
}
```

**Quest field reference:**

| Field | Type | Value | Description |
|-------|------|-------|-------------|
| `EntryId` | UUID | `uuid.uuid4()` | Shared UUID between the inProgress/completed pair |
| `id` | String | `mlh` + random chars | The quest ID used in `TaskTriggerId`. Format: `mlh` + 11-14 lowercase alphanumeric chars. Each entry in a pair MUST have a different `id` (they share `EntryId` but not `id`). Use the inProgress entry's `id` as the `TaskTriggerId` in effects. |
| `Name` | String | `"0_name"` format | **Required numbered format**: `0_`, `1_`, `2_`, etc. prefix. Must match effect `Name` fields. |
| `Description` | String | `"created in unity"` | Must always be `"created in unity"`. This is a required fixed value. |
| `Status` | String | `"inProgress"` or `"completed"` | Determines which array the entry goes in |
| `Group` | String | `""`, `"nonPersistent"`, or `"multiplayer"` | `""` = single-player persistent, `"nonPersistent"` = single-player resets, `"multiplayer"` = shared persistent |
| `Enabled` | Boolean | `true` | Must be `true` for quest to function |
| `RepeatableLimit` | Number | `0` | How many times quest can repeat. `0` = infinite |
| `AutoStart` | Boolean | `false` | **Does NOT set the quest to Active state.** This field does not trigger a state transition. To make a quest Active, you must use a trigger (e.g., `TaskTriggerSubscription` with `OnClickEvent`, `OnEnterEvent`, etc.). |
| `Requirements` | Array | `[]` | Quest dependencies. Use empty array unless you have specific dependencies |
| `Creator` | String | Firebase UID | MUST be the authenticated user's Firebase UID (from `authenticate` response). Quests with invalid Creator will not function. |
| `Tracked` | Boolean | `true` | Whether quest appears in player's quest log |
| `Visible` | Boolean | `false` | Whether quest is visible in UI. Usually `false` for animation triggers |

**Generating quest IDs in Python:**

```python
import random
import string
import uuid

def generate_quest_id():
    """Generate quest ID: mlh + 11-14 random lowercase alphanumeric chars"""
    length = random.randint(11, 14)
    chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"mlh{chars}"

def create_quest_pair(number, name_suffix, creator):
    """Create a quest pair in MCP flat-dict format.

    Args:
        number: Quest number prefix (0, 1, 2, ...)
        name_suffix: Quest name after the number (e.g., "assemble")
        creator: Authenticated user's Firebase UID (from authenticate response)

    Returns dict with:
        - "entries": {id: entry, id: entry} -- merge into your quests dict
        - "quest_id": inProgress ID (use as TaskTriggerId in effects)
        - "quest_name": full name like "0_assemble"
    """
    entry_id = str(uuid.uuid4())
    id_progress = generate_quest_id()
    id_completed = generate_quest_id()
    quest_name = f"{number}_{name_suffix}"

    base = {
        "EntryId": entry_id,
        "Name": quest_name,
        "Description": "created in unity",
        "Group": "",  # or "multiplayer"
        "DisplayGroup": "",
        "Enabled": True,
        "RepeatableLimit": 0,
        "FinishTime": 0,
        "AutoStart": False,
        "TriggeredByInventory": False,
        "Requirements": [],
        "Creator": creator,
        "TemplateName": "",
        "Tracked": True,
        "Visible": False,
        "ExtraText": "",
    }

    entries = {
        id_progress: {**base, "Status": "inProgress", "id": id_progress},
        id_completed: {**base, "Status": "completed", "id": id_completed,
                       "Rewards": [], "SuccessMsg": ""},
    }

    return {
        "entries": entries,
        "quest_id": id_progress,
        "quest_name": quest_name,
    }
```

**Key points:**
- The inProgress entry's `id` is what items reference as `TaskTriggerId` in effects
- Each pair has TWO DIFFERENT `id` values but shares the same `EntryId`
- The `Name` field MUST start with a number and underscore (e.g., `"0_assemble"`, `"1_activate"`)
- The `Creator` field MUST be the authenticated user's Firebase UID -- not an arbitrary string
- Both entries must be identical except for `Status`, `id`, and the completed entry's extra fields (`Rewards`, `SuccessMsg`)
- Quests are stored as a flat dict `{quest_id: entry, ...}` -- NOT the old `{inProgress: [...], completed: [...]}` format
- All fields must always be present -- do not omit any fields
- Set `"Group": "multiplayer"` for effects visible to all players
- Always read existing quests before writing to avoid overwriting others

### Task Effect Format (3 States)

Each item can have effects that trigger on quest state changes. All 3 states use the **same `TaskTriggerId`** and **same `Name`**.

**State 0 -- Not Active (default state):**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {
    "$type": "MoveToSpot",
    "_transformState": {
      "position": [0, 0, 0],
      "rotation": [0, 0, 0, 1],
      "scale": [1, 1, 1],
      "duration": 0.0
    }
  },
  "Id": "unique-uuid",
  "Name": "0_assemble",
  "TaskTriggerId": "quest-id"
}
```

**State 1 -- Active:**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {
    "$type": "MoveToSpot",
    "_transformState": {
      "position": [0, 5, 0],
      "rotation": [0, 0, 0, 1],
      "scale": [1, 1, 1],
      "duration": 3.0
    }
  },
  "Id": "unique-uuid",
  "TargetState": 1,
  "Name": "0_assemble",
  "TaskTriggerId": "quest-id"
}
```

**State 2 -- Completed:**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {
    "$type": "MoveToSpot",
    "_transformState": {
      "position": [0, 10, 0],
      "rotation": [0, 0, 0, 1],
      "scale": [1, 1, 1],
      "duration": 1.0
    }
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": "0_assemble",
  "TaskTriggerId": "quest-id"
}
```

### Critical Rules

- State 0 has **NO** `TargetState` field
- State 1 has `"TargetState": 1`
- State 2 has `"TargetState": 2`
- All three share the same `TaskTriggerId` and `Name`
- Each effect needs a unique `Id` (UUID v4)
- `duration` controls animation time in seconds. `0.0` = instant.
- `_transformState` can independently set position, rotation, scale, and duration per state
- `position` and `scale` use arrays `[x, y, z]`, `rotation` uses `[qx, qy, qz, qw]`
- **By default, all `_transformState` values are ABSOLUTE, not relative to the item's placed transform.** `position` is an absolute world coordinate, `scale` is an absolute scale value, and `rotation` is an absolute quaternion. For example, if an item is placed at scale `[0.5, 0.5, 0.5]` and a MoveToSpot uses `scale: [1, 1, 1]`, the item will visually grow to double its placed size. To keep the item's original size during movement, set `scale` to match the item's placed scale.
- **Relative mode**: Add `"relative": true` to the MoveToSpot effector (sibling to `_transformState`) to make all values **offsets from the item's current transform**. Values accumulate with each trigger — `position: [1, 0, 0]` moves 1 unit in +X each time (so 3 clicks = 3 units total). **Scale is additive**: `scale: [1, 1, 1]` adds 1 to each axis each time, so an item at scale 1 grows to 2, then 3, then 4, etc. `rotation` is applied as a delta. Useful for repeatable/stackable movements. **Note:** `"relative"` only exists on `MoveToSpot`, not on `PortalsAnimation`.
- Multiple quests can drive independent animation sequences on the same item

---

## ShowObjectEvent / HideObjectEvent

Controls whether an item is visible or hidden. Objects are **visible by default**. Use `HideObjectEvent` to hide an item and `ShowObjectEvent` to reveal a previously hidden item.

The effector takes no parameters -- just the `$type`:

**HideObjectEvent:**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {"$type": "HideObjectEvent"},
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": "quest-name",
  "TaskTriggerId": "quest-id"
}
```

**ShowObjectEvent:**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {"$type": "ShowObjectEvent"},
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": "quest-name",
  "TaskTriggerId": "quest-id"
}
```

- Works with both `TaskEffectorSubscription` (quest-driven) and `TaskTriggerSubscription` (basic interaction via `DirectEffector`)
- Follows the same `TargetState` / `Name` / `TaskTriggerId` rules as all other effects
- You only need `ShowObjectEvent` to re-show an item that was previously hidden by `HideObjectEvent`
- Useful for revealing/hiding elements based on quest progress (e.g., hide a wall when a puzzle is solved, show a reward item when a quest completes)

---

## RunTriggersFromEffector

Triggers a state change on a quest when another quest reaches a specific state. Extremely powerful for creating loops, cascading sequences, and resetting quests automatically.

```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {
    "$type": "RunTriggersFromEffector",
    "linkedTasks": [
      {
        "Trigger": {},
        "Id": "unique-uuid",
        "TargetState": 101,
        "Name": "0_multiplayer",
        "TaskTriggerId": "quest-id"
      }
    ]
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": "0_multiplayer",
  "TaskTriggerId": "quest-id"
}
```

### How It Works

- The **outer** `TaskEffectorSubscription` watches a quest for a specific state (e.g., `TargetState: 2` = completed)
- When triggered, the **inner** `linkedTasks` fire, changing quests to new states
- `linkedTasks` is an array -- you can chain multiple state changes at once

### linkedTasks Entry Fields

`linkedTasks` is an array -- you can trigger **multiple** quest state changes from a single event. Each entry can target a different quest with a different state change and optional delay.

| Field | Description |
|-------|-------------|
| `Trigger` | `{}` = immediate. `{"Delay": 1.0}` = delay in seconds before firing. |
| `TargetState` | Encoded state transition value (see table below) |
| `Name` | Quest name to target |
| `TaskTriggerId` | Quest ID to target |

### TargetState Values for linkedTasks

| Value | From | To |
|-------|------|----|
| `101` | Any | Not Active |
| `151` | Any | Active |
| `141` | Any | Completed |
| `111` | Not Active | Active |
| `181` | Not Active | Completed |
| `161` | Active | Not Active |
| `121` | Active | Completed |
| `171` | Completed | Not Active |
| `131` | Completed | Active |

The "Any" variants (`101`, `151`, `141`) trigger regardless of current state. The constrained variants (e.g., `121` = Active to Completed) only fire when the quest is currently in the specified "from" state, acting as a guard/blocker.

### useRandom Option

Set `"useRandom": true` on the `RunTriggersFromEffector` effector (sibling to `linkedTasks`) to randomly pick **one** of the linked tasks to fire instead of firing all of them. Only useful when there are multiple entries in `linkedTasks`.

### Common Patterns

- **Auto-reset loop**: When quest completes (state 2) then reset to not active (101) so it can be triggered again
- **Cascade**: When quest A completes then activate quest B
- **Multi-step sequences**: Chain multiple quests in order

---

## PortalsAnimation

Similar to `MoveToSpot` but chains multiple transform states together to create multi-step keyframe animations. The item moves through each keyframe in sequence. Wraps in a standard `TaskEffectorSubscription` so it integrates with quests just like `MoveToSpot`.

```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {
    "$type": "PortalsAnimation",
    "stateEvents": [],
    "_transformStates": [
      {
        "position": [0, 0, 0],
        "rotation": [0, 0, 0, 1],
        "scale": [1, 1, 1]
      },
      {
        "position": [0, 5, 0],
        "rotation": [0, 0, 0, 1],
        "scale": [1, 1, 1]
      }
    ],
    "states": [
      {"x": 0, "y": 0, "z": 0, "rx": 0.0, "sx": 1.0, "sy": 1.0, "sz": 1.0, "duration": 3.0},
      {"x": 0, "y": 5, "z": 0, "rx": 0.0, "sx": 1.0, "sy": 1.0, "sz": 1.0, "duration": 3.0}
    ]
  },
  "Id": "unique-uuid",
  "TargetState": 1,
  "Name": "quest-name",
  "TaskTriggerId": "quest-id"
}
```

The effect has two parallel arrays describing the same keyframes:

| Array | Format | Notes |
|-------|--------|-------|
| `_transformStates` | Quaternion-based: `position`, `rotation` [qx,qy,qz,qw], `scale` | Same format as `MoveToSpot._transformState`, no duration |
| `states` | Euler-based: `x,y,z` (position), `rx` (rotation degrees), `sx,sy,sz` (scale), `duration` | Each keyframe has its own `duration` in seconds |

Both arrays must have the same number of entries and describe the same positions. The `states` array controls the `duration` of each step.

- `stateEvents`: Array for triggering events at specific keyframes (empty `[]` for basic animations)
- `rx: 0.0` in `states` is the default rotation (identity quaternion `[0, 0, 0, 1]`)
- Add as many keyframes as needed -- the animation plays through them in sequence

### Optional PortalsAnimation Flags

These boolean fields go inside the `Effector` object alongside `_transformStates` and `states`:

| Field | Default | Description |
|-------|---------|-------------|
| `loopAnimation` | `false` | Loops the animation continuously |
| `seamless` | `false` | Smooths the loop transition (only useful when `loopAnimation` is `true`) |
| `fixedUpdate` | `false` | Optimizes for collision detection. Only enable if the item has a collision trigger. |

---

## StopAnimationEvt (Stop GLB Animation)

Stops an animated GLB model's embedded animation at a specific normalized time point. The `stop` field ranges from `0.0` (beginning of the animation, 0%) to `1.0` (end, 100%). When fired, the GLB freezes at that frame.

**Common pattern:** Use `OnPlayerLoggedIn` → `StopAnimationEvt` with `stop: 0.0` to freeze animated GLBs at their first frame on room load. Then use `PlayAnimationOnce` on click or quest state change to play the animation when desired (e.g., opening a door, activating a lever).

**Basic interaction -- freeze animation on room entry:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnPlayerLoggedIn"},
  "DirectEffector": {
    "Effector": {
      "$type": "StopAnimationEvt",
      "stop": 0.0
    },
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

**Quest-driven -- stop animation when quest completes:**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {
    "$type": "StopAnimationEvt",
    "stop": 0.0
  },
  "Id": "unique-uuid",
  "Name": "0_questname",
  "TaskTriggerId": "quest-id"
}
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `stop` | Float | — | Normalized time: `0.0` = start (0%), `1.0` = end (100%). Omitting the field stops the animation at whatever frame it's currently on. |

**Python builder:**
```python
from portals_effects import effector_stop_animation, effector_play_animation_once

# Freeze at start of animation
effector_stop_animation(stop=0.0)

# Freeze at 50% through the animation
effector_stop_animation(stop=0.5)

# Freeze at end of animation
effector_stop_animation(stop=1.0)

# Pair with PlayAnimationOnce for a play-on-demand pattern:
# 1. On room entry, freeze the GLB at frame 0
# 2. On click (or quest), play the animation once
```

**Typical use cases:**
- **Doors**: Freeze closed on load (`stop: 0.0`), play animation to open on trigger
- **Levers/switches**: Hold at starting position, animate on interaction
- **Cutscene poses**: Freeze animated characters at specific poses
- **State machines**: Stop at `0.0` (closed) or `1.0` (open) to represent binary states

---

## DialogEffectorDisplay

Creates an interactive dialogue tree with branching answers. The most complex effect type -- embeds inline quest entries for each dialogue node.

### Effector Structure

```json
{
  "$type": "DialogEffectorDisplay",
  "tasksN": [{"N": "-0_task_name"}, {"N": "-1_task_name"}],
  "GN": "Character Name",
  "S": "_<story-uuid>",
  "Audio": false,
  "HF": true,
  "R": true,
  "DV": "",
  "GB": "leave",
  "Story": "_<story-uuid>",
  "tasksSorM": {
    "-0_task_name": {
      "completed": { /* quest entry */ },
      "inProgress": { /* quest entry */ }
    },
    "-1_task_name": {
      "completed": { /* quest entry */ },
      "inProgress": { /* quest entry */ }
    }
  }
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `tasksN` | `[{"N": str}]` | Ordered list of task name references |
| `GN` | `str` | Character name displayed in dialogue UI |
| `S` | `str` | Story UUID prefixed with `_` |
| `Audio` | `bool` | Enable audio playback |
| `HF` | `bool` | Hide dialogue UI on finish |
| `R` | `bool` | Allow dialogue to be repeated |
| `DV` | `str` | Dialogue voice ID (for TTS). Empty = no voice. |
| `GB` | `str` | Goodbye action. `"leave"` = close dialogue. |
| `Story` | `str` | Same as `S` (story identifier) |
| `tasksSorM` | `dict` | Maps task names to `{completed: quest, inProgress: quest}` pairs |

### Dialogue Node Quest Entry

Each quest entry in `tasksSorM` uses `ExtraText` (JSON string) to store the dialogue data:

```json
{
  "ExtraTaskDTODataDialog": {
    "QT": "What the NPC says",
    "AT": [
      {"Task": "-1_next_node", "Txt": "Player answer text", "Name": "Answer label"}
    ]
  }
}
```

| Field | Description |
|-------|-------------|
| `QT` | Question/statement text from the NPC |
| `AT` | Array of answer options. Empty `[]` = terminal node (end of branch). |
| `AT[].Task` | Task name to branch to when this answer is chosen |
| `AT[].Txt` | Displayed text for this answer option |
| `AT[].Name` | Answer label/identifier |

### Task Naming Convention

Task names follow the pattern `-{index}_{description}` (e.g., `-0_greeting`, `-1_farewell`).

### Quest Entry Fields

Each quest in `tasksSorM` needs both `completed` and `inProgress` entries with standard quest fields:
- `id`: Unique quest ID (mlh pattern)
- `Name`: Must match the task name key
- `Description`: `"created in unity"` (required fixed value)
- `Status`: `"completed"` or `"inProgress"`
- `Creator`: Firebase UID of room creator
- `EntryId`: Shared UUID between completed/inProgress pair
- `ExtraText`: JSON string with `ExtraTaskDTODataDialog`

---

## All Confirmed Effects Quick Reference

Quick reference for every confirmed effect `$type` and its parameters. Use these inside `TaskEffectorSubscription` or `DirectEffector` wrappers.

### No-Parameter Effects

| Effect | `$type` |
|--------|---------|
| Show Object | `ShowObjectEvent` |
| Hide Object | `HideObjectEvent` |
| Show Outline | `ShowOutline` |
| Hide Outline | `HideOutline` |
| Damage Over Time | `DamageOverTime` |
| Lock Movement | `LockMovement` |
| Unlock Movement | `UnlockMovement` |
| Start Auto Run | `StartAutoRun` |
| Stop Auto Run | `StopAutoRun` |
| Lock Avatar Change | `LockAvatarChange` |
| Unlock Avatar Change | `UnlockAvatarChange` |
| Lock Camera | `LockCamera` |
| Unlock Camera | `UnlockCamera` |
| Toggle Free Cam | `ToggleFreeCam` |
| Mute Player | `MutePlayer` |
| Hide All Players | `HideAllPlayersEvent` |
| Display Avatar Screen | `DisplayAvatarScreen` |
| Move Item to Player | `MoveItemToPlayer` |
| Reset All Tasks | `ResetAllTasks` |
| Post Score to Leaderboard | `PostScoreToLeaderboard` | `{"label": "variable name"}` — only for numeric values, not timers |
| Refresh Inventory | `RefreshUserInventory` |
| Change Time of Day | `ChangeTimeOfDay` |
| Hide Token Swap | `HideSellSwap` |
| Equip Gun | `EquipGunEffect` |
| Toss Gun | `TossGunEffect` |
| Reset Gun | `ResetGunEffect` |
| Respawn Destructible | `RespawnDestructible` |
| Activate Trigger Zone | `ActivateTriggerZoneEffect` |
| Deactivate Trigger Zone | `DeactivateTriggerZoneEffect` |
| Turn to Player | `TurnToPlayer` |
| Start Speaking | `StartSpeaking` |
| Stop Speaking | `StopSpeaking` |
| Enter Vehicle | `EnterVehicle` |
| Exit Vehicle | `ExitVehicle` |
| Revive Enemy | `ReviveEnemy` |
| Reset Enemy | `ResetEnemy` |
| Attack Player | `AttackPlayer` |

### Parameterized Effects

| Effect | `$type` | Parameters |
|--------|---------|------------|
| Apply Velocity | `AddVelocityToPlayer` | `{"vel": [x,y,z], "local": bool}` |
| MoveToSpot | `MoveToSpot` | `{"_transformState": {"position": [x,y,z], "rotation": [qx,qy,qz,qw], "scale": [x,y,z], "duration": float}, "relative": bool}` — by default all values are **ABSOLUTE** (world position, world scale, world rotation). Add `"relative": true` to make values **offsets from current transform**. Not on PortalsAnimation. |
| Notification Pill | `NotificationPillEvent` | `{"nt": "text", "c": "hex", "hideBackground": bool}` — `nt` supports pipe syntax `\|varName\|` for inline variable display (e.g., `"You have \|coins\| coins!"`) |
| Teleport | `TeleportEvent` | `{"id": "room-id", "sn": "spawn name", "sr": float}` |
| Heal Player | `ChangePlayerHealth` | `{"healthChange": int}` |
| Damage Player | `ChangePlayerHealth` | `{"op": 2, "healthChange": int}` |
| Display Value | `DisplayValueEvent` | `{"label": "name", "color": "hex"}` |
| Hide Value | `HideValueEvent` | `{"label": "name"}` |
| Update Value | `UpdateScoreEvent` | `{"scoreChange": float}` or `{"op": int, "scoreChange": float}` — **omit `op` entirely to set value**. When `op` is present: 1=add, 2=sub, 3=mul, 4=div |
| Update String Value | `UpdateScoreEventString` | `{"targetText": "text", "label": "name"}` |
| Function Effect | `FunctionEffector` | `{"V": "NCalc expression"}` — **task names omit the numbered prefix**: quest `Name` uses `0_redteam` but NCalc uses just `'redteam'` (no `0_` prefix) in `SetTask()`, `$T{}`, `OnChange` |
| Player Emote | `PlayerEmote` | `{"animationName": "emote"}` — same animation list as `NpcAnimation`: Sitting, Can Can, Wave, Salute, Jive, Salsa, Shuffling, Chicken, Slide n Jive, Robot |
| Camera Filter | `SetCameraFilter` | `{"url": "image url", "alpha": float}` |
| Camera Zoom | `ChangeCameraZoom` | `{"zoomAmount": float, "lockZoom": bool}` |
| Toggle Cursor Lock | `ToggleLockCursor` | `{"lockCursor": bool}` |
| Change Fog | `ChangeFog` | `{"color": "hex", "distance": float}` |
| Send Msg to Iframes | `SendMessageToIframes` | `{"iframeMsg": "text"}` — supports `\|variable\|` interpolation (`\|username\|`, `\|position\|`, player vars). See [iframes.md](iframes.md). |
| Clear Leaderboard | `ClearLeaderboard` | `{"label": "name"}` |
| Open Leaderboard | `OpenLeaderboardEffect` | `{"lb": "leaderboard name"}` |
| Start Timer | `StartTimerEffect` | `{"tn": "timer name", "ci": "", "showTimerUI": bool}` |
| Stop Timer | `StopTimerEffect` | `{"tn": "timer name", "ci": ""}` |
| Cancel Timer | `CancelTimerEffect` | `{"tn": "timer name"}` |
| Change Voice Group | `ChangeVoiceGroup` | `{"group": "group name"}` |
| Duplicate Item | `DuplicateItem` | `{"TS": {"position": [x,y,z], "rotation": [qx,qy,qz,qw], "scale": [x,y,z]}, "destroyAfterTime": float}` |
| Play Sound Once | `PlaySoundOnce` | `{"Url": "mp3 url", "Dist": float}` (note capital U and D) |
| Play Sound Loop | `PlaySoundInALoop` | `{"Url": "mp3 url", "Dist": float, "Preload": bool}` (Dist: -1 = global) |
| Stop Sound | `StopSound` | `{"url": "mp3 url", "fadeOut": float}` (note lowercase `url`) |
| Change Audius | `ChangeAudiusEffect` | `{"ap": "playlist name"}` |
| Change Bloom | `ChangeBloom` | `{"Intensity": float, "Clamp": float, "Diffusion": float}` |
| Rotate Skybox | `RotateSkybox` | `{"rotation": float (degrees), "duration": float (seconds)}` |
| Change Avatar | `ChangeAvatarEffector` | `{"Url": "glb url", "Persistent": bool}` |
| Change Movement Profile | `ChangeMovementProfile` | `{"mvmtProfile": "profile name"}` |
| Change Cam State | `ChangeCamState` | `{"camState": "camera name", "transitionSpeed": float}` |
| Equip Wearable | `ChangeRoundyWearableEffector` | `{"ItemID": "wearable id"}` |
| Play Animation Once | `PlayAnimationOnce` | `{"speed": float}` (negative = reverse playback) |
| Stop Animation | `StopAnimationEvt` | `{"stop": float}` — normalized time 0.0 (start) to 1.0 (end). Freezes GLB animation at that frame. |
| Open Iframe | `IframeEvent` | `{"url": "iframe url"}` — URL supports appearance params (`?maximized=true`, `?noCloseBtn=true`, etc.). See [iframes.md](iframes.md). |
| Close Iframe | `IframeStopEvent` | `{"iframeUrl": "iframe url"}` — URL must match the opened iframe. See [iframes.md](iframes.md). |
| NPC Message | `NPCMessageEvent` | `{"n": "npc name", "m": "message", "r": bool}` |
| Walk NPC to Spot | `WalkNpcToSpot` | `{"walkSpeed": float, "endPosition": [x,y,z], "endRotation": [qx,qy,qz,qw]}` |
| NPC Animation | `NpcAnimation` | `{"animationName": "Sitting"}` — same animation list as `PlayerEmote`. GLBNPC-only |
| NPC Copy Player Path | `NpcCopyPlayerPath` | `{"positions": [[x,y,z],...], "rotations": [[qx,qy,qz,qw],...], "animatorParameterDatas": [...], "shouldLoop": bool}` — GLBNPC walks along recorded path |
| NPC Stop Path | `NpcCopyPlayerPathStop` | `{"RP": bool}` — stops path following. `RP: true` = reset to original position. GLBNPC-only |
| Show Token Swap | `DisplaySellSwap` | `{"id": "swap config id", "typ": int}` |
| Change Enemy Health | `ChangeEnemyHealth` | `{"op": int, "healthChange": int}` — `op`: 1=add, 2=sub. EnemyNPC-only. |
| Vehicle Boost | `VehicleBoost` | `{"duration": float, "speedOfBoost": float, "rampUpTime": float, "rampDownTime": float}` — temporary speed boost. Vehicle-only. |
| Duplicate Enemy | `DuplicateEnemy` | `{"spawnName": "spawn name", "count": int, "randomRadius": float}` — spawns copies at named SpawnPoint. EnemyNPC-only. |

### Complex Effects

| Effect | `$type` | Notes |
|--------|---------|-------|
| PortalsAnimation | `PortalsAnimation` | Multi-keyframe animation -- see [PortalsAnimation](#portalsanimation) section |
| Run Triggers | `RunTriggersFromEffector` | Quest state chaining -- see [RunTriggersFromEffector](#runtriggersfromeffector) section |
| Dialogue Display | `DialogEffectorDisplay` | Dialogue tree -- see [DialogEffectorDisplay](#dialogeffectordisplay) section |

### Syntax Quirks

- `DuplicateItem` uses `"TS"` for its transform state (not `"_transformState"`)
- `PlaySoundOnce` and `PlaySoundInALoop` use capital `"Url"` and `"Dist"`
- `StopSound` uses lowercase `"url"`
- `ChangeTimeOfDay` has no parameters
- `StartTimerEffect`: `"showTimerUI": true` (or omit) shows visible timer UI on screen; `"showTimerUI": false` hides it. Count-up timer by default.
- `EquipGunEffect`: No parameters. Auto-equips the Gun item it is attached to. Attach to the Gun item itself with any trigger (e.g., `OnPlayerLoggedIn` for auto-equip, or quest-driven for game-start equip).
- `TossGunEffect`: No parameters. Forces the player to drop/toss their equipped gun. Attach to Gun items.
- `ResetGunEffect`: No parameters. Resets gun state (reload/ammo). Attach to Gun items.
- `RespawnDestructible`: No parameters. Respawns a destroyed Destructible item. Attach to Destructible items.
- `ActivateTriggerZoneEffect` / `DeactivateTriggerZoneEffect`: No parameters. Enable/disable a Trigger zone so it stops/starts firing enter/exit events. Attach to Trigger items.
- `PlayAnimationOnce`: `{"speed": float}` — plays a GLB animation once at the given speed. Negative speed plays in reverse.
- `StopAnimationEvt`: `{"stop": float}` — stops/freezes a GLB animation at normalized time (0.0–1.0). Common pattern: `OnPlayerLoggedIn` → `StopAnimationEvt(stop: 0.0)` to freeze on load, then `PlayAnimationOnce` on click to play. Omitting `stop` freezes at the current frame.
- `WalkNpcToSpot`: GLBNPC-only. Walks the NPC to `endPosition` at `walkSpeed` (units/sec). The NPC plays a walk animation while moving. Attach to the GLBNPC item. Typically quest-driven — use one quest per waypoint to sequence movement (e.g., `STEP1` → walk to position A, `STEP2` → walk to position B). `endPosition` and `endRotation` are arrays, not objects.
- `NpcAnimation`: GLBNPC-only. Uses the same restricted animation list as `PlayerEmote` and the NPC `a` extraData field: `Sitting`, `Can Can`, `Wave`, `Salute`, `Jive`, `Salsa`, `Shuffling`, `Chicken`, `Slide n Jive`, `Robot`.
- `NpcCopyPlayerPath`: GLBNPC-only. Makes the NPC walk along a recorded path. All three arrays (`positions`, `rotations`, `animatorParameterDatas`) must have the same length. Set `shouldLoop: true` for continuous patrol.
- `NpcCopyPlayerPathStop`: GLBNPC-only. Stops path following. Set `RP: true` to reset the NPC to its original position.
- `TurnToPlayer`: GLBNPC-only. Makes the NPC turn to face the player who activated the effect. No parameters.
- `StartSpeaking`: GLBNPC-only. Starts the NPC's talking animation (purely visual — does not trigger AI conversation). No parameters.
- `StopSpeaking`: GLBNPC-only. Stops the NPC's talking animation. No parameters.
- `ReviveEnemy`: No parameters. Revives a dead EnemyNPC. Attach to EnemyNPC items. Typically quest-driven — use `ReviveEnemy` on a quest completion to respawn enemies after a timer or event.
- `ResetEnemy`: No parameters. Respawns the enemy with fresh health at its original position. Attach to EnemyNPC items.
- `AttackPlayer`: No parameters. Forces the NPC to immediately attack the nearest player. Attach to EnemyNPC items.
- `ChangeEnemyHealth`: `{"op": int, "healthChange": int}` — modifies the NPC's health. `op`: 1=add, 2=sub. Attach to EnemyNPC items.
- `DuplicateEnemy`: `{"spawnName": "spawn name", "count": int, "randomRadius": float}` — spawns copies of the NPC at a named SpawnPoint. Set a SpawnPoint's `n` field and reference it in `spawnName`. Useful for creating enemy swarms.
- `OnEnemyDied`: EnemyNPC-only trigger. `{"$type": "OnEnemyDied", "RTime": float, "Delay": float}`. `RTime` is the respawn timer (seconds), `Delay` is fire delay. Use to trigger loot drops, score updates, or respawn sequences when an enemy is killed.
- `OnTakeDamageTrigger`: EnemyNPC-only trigger. No parameters. Fires when the NPC takes damage. Use for reactive behaviors like aggro-on-hit or spawning reinforcements.
- `EnterVehicle`: No parameters. Forces the player into the vehicle. Attach to Vehicle items. Typically triggered via `OnClickEvent` when player is within `maxDistanceToEnter` range.
- `ExitVehicle`: No parameters. Forces the player out of the vehicle. Attach to Vehicle items.
- `VehicleBoost`: `{"duration": float, "speedOfBoost": float, "rampUpTime": float, "rampDownTime": float}` — applies a temporary speed boost. Attach to Vehicle items. `rampUpTime` smoothly accelerates to boost speed, `rampDownTime` smoothly decelerates back to normal.
- `OnVehicleEntered`: Vehicle-only trigger. No parameters. Fires when a player enters the vehicle. Use for UI changes, sound effects, or starting sequences.
- `OnVehicleExited`: Vehicle-only trigger. No parameters. Fires when a player exits the vehicle. Use for cleanup, UI reset, or stop sequences.

---

## All Confirmed Triggers Quick Reference

All general triggers use bare `{"$type": "TriggerName"}` with no extra params.

### General Triggers (work on any item)

**Note:** While these triggers technically attach to any item type, visibility-dependent triggers (`OnClickEvent`, `OnHoverStartEvent`, `OnHoverEndEvent`) require the item to be **visible** to players. Never use them on Trigger cubes (invisible) -- use a ResizableCube, GLB, or other visible item instead.

| Trigger | `$type` |
|---------|---------|
| On Click | `OnClickEvent` |
| On Collide | `OnCollideEvent` |
| Collision Stopped | `OnCollisionStoppedEvent` |
| Hover Start | `OnHoverStartEvent` |
| Hover End | `OnHoverEndEvent` |
| Player Logged In | `OnPlayerLoggedIn` |
| Key Pressed | `OnKeyPressedEvent` |
| Key Released | `OnKeyReleasedEvent` |
| Player Died | `OnPlayerDied` |
| Player Revived | `OnPlayerRevived` |
| Player Move | `OnPlayerMove` |
| Player Stopped Moving | `OnPlayerStoppedMoving` |
| Mic Unmuted | `OnMicrophoneUnmuted` |
| Timer Stopped | `OnTimerStopped` |
| Countdown Finished | `OnCountdownTimerFinished` |
| Value Updated | `ScoreTrigger` |
| Animation Stopped | `OnAnimationStoppedEvent` |
| Item Collected | `OnItemCollectedEvent` |
| Backpack Item Activated | `OnItemClickEvent` |
| Player Leave | `PlayerLeave` |
| Swap Volume | `SwapVolume` |
| Item Destroyed | `OnDestroyedEvent` |

**`OnPlayerLoggedIn` is the "room enter" trigger.** It fires once per player when they join the room. Use it for any logic that should run when a player enters: initializing variables (`SetNumberVariable`), starting ambient sounds (`PlaySoundInALoop`), hiding/showing objects for initial state (`HideObjectEvent`/`ShowObjectEvent`), equipping items (`EquipGunEffect`), resetting animations (`StopAnimationEvt`), or opening welcome UI (`OpenIframe`). This is the primary "game start" trigger — if you need something to happen when a player arrives, put it on `OnPlayerLoggedIn`.

### EnemyNPC Triggers (prefabName: "EnemyNPC")

| Trigger | `$type` | Notes |
|---------|---------|-------|
| Enemy Died | `OnEnemyDied` | NPC was killed. Has optional `RTime` (respawn timer, seconds) and `Delay` (fire delay, seconds) fields. |
| Take Damage | `OnTakeDamageTrigger` | NPC took damage from any source. No parameters. |

**Example — OnEnemyDied trigger advancing a quest:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnEnemyDied", "RTime": 0.0, "Delay": 0.0},
  "Id": "unique-uuid",
  "TargetState": 181,
  "Name": "quest-name",
  "TaskTriggerId": "quest-id"
}
```

### Vehicle Triggers (prefabName: "Vehicle")

| Trigger | `$type` | Notes |
|---------|---------|-------|
| Vehicle Entered | `OnVehicleEntered` | Player enters the vehicle. No parameters. |
| Vehicle Exited | `OnVehicleExited` | Player exits the vehicle. No parameters. |

**Example — OnVehicleEntered trigger with notification:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnVehicleEntered"},
  "DirectEffector": {
    "Effector": {"$type": "NotificationPillEvent", "nt": "Welcome aboard!", "c": "00FF00"},
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

### Vehicle Effects (prefabName: "Vehicle")

| Effect | `$type` | Notes |
|--------|---------|-------|
| Enter Vehicle | `EnterVehicle` | Forces player into the vehicle. No parameters. |
| Exit Vehicle | `ExitVehicle` | Forces player out of the vehicle. No parameters. |
| Vehicle Boost | `VehicleBoost` | Temporary speed boost with ramp-up/down. |

**VehicleBoost parameters:**

| Field | Type | Description |
|-------|------|-------------|
| `duration` | float | Total boost duration in seconds |
| `speedOfBoost` | float | Boost speed value |
| `rampUpTime` | float | Seconds to reach full boost speed |
| `rampDownTime` | float | Seconds to return to normal speed |

**Example — click to boost:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnClickEvent"},
  "DirectEffector": {
    "Effector": {
      "$type": "VehicleBoost",
      "duration": 5.0,
      "speedOfBoost": 200.0,
      "rampUpTime": 1.0,
      "rampDownTime": 1.5
    },
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

### Gun Triggers (prefabName: "Gun" or "Shotgun")

| Trigger | `$type` | Notes |
|---------|---------|-------|
| Gun Equipped | `OnGunEquippedTrigger` | Player equips the gun. Supports optional `Delay` field. |
| Shot Hit | `ShotHitTrigger` | Bullet hits a target |
| Got Kill | `GotKillTrigger` | Player gets a kill with this gun |
| Started Aiming | `StartedAimingTrigger` | Player starts aiming down sights |
| Stopped Aiming | `StoppedAimingTrigger` | Player stops aiming |
| Gun Tossed | `OnGunTossedTrigger` | Player drops/tosses the gun |

**Example — OnGunEquippedTrigger with delay:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnGunEquippedTrigger", "Delay": 0.1},
  "DirectEffector": {
    "Effector": {"$type": "NotificationPillEvent", "nt": "Gun equipped!", "c": "FF0000"},
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

### Trigger-Cube-Only (prefabName: "Trigger")

| Trigger | `$type` |
|---------|---------|
| On Enter | `OnEnterEvent` |
| On Exit | `OnExitEvent` |

These two triggers ONLY work on trigger cubes (prefabName `"Trigger"`). They do NOT work on ResizableCubes, GLBs, or other item types.

**Note:** `UserExitTrigger` is a legacy alias that also works, but `OnExitEvent` is the correct/preferred name.

**Important:** Trigger cubes are invisible during play. Never use visibility-dependent triggers (`OnClickEvent`, `OnHoverStartEvent`, `OnHoverEndEvent`) on them -- players cannot click or hover over what they cannot see.
