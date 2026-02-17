# Quest System

Quests drive interactive animations and state-based gameplay in Portals.

## Overview

Quests are the foundation for interactive experiences. They provide:
- **3-state system**: Not Active → Active → Completed
- **Persistent state**: Survives page reloads
- **Effect orchestration**: Items react to quest state changes
- **Single/multiplayer modes**: Per-player or shared across all players

## Quest States

Every quest has 3 states:

| State | Value | Description |
|-------|-------|-------------|
| **Not Active** | 0 | Default state. Quest not started. |
| **Active** | 1 | Quest in progress. Player working on objective. |
| **Completed** | 2 | Quest finished. Final state reached. |

State transitions trigger effects on items subscribed to the quest.

## Quest Format

Quests come in **pairs** -- one `inProgress` entry and one `completed` entry sharing the same `EntryId`. Quests are stored as a **flat dict** keyed by quest ID. Each logical quest has TWO entries (inProgress + completed) sharing the same `EntryId` but with **DIFFERENT** `id` values.

**Complete Quest Pair (flat-dict format):**
```json
{
  "mljstsdgsfy4d7": {
    "EntryId": "07b29300-f6df-47e4-8f55-5aa697303896",
    "Name": "0_collect",
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
    "Creator": "YOUR_FIREBASE_UID",
    "TemplateName": "",
    "Tracked": true,
    "Visible": false,
    "ExtraText": "",
    "id": "mljstsdgsfy4d7"
  },
  "mljstsdiapl8qf": {
    "EntryId": "07b29300-f6df-47e4-8f55-5aa697303896",
    "Name": "0_collect",
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
    "Creator": "YOUR_FIREBASE_UID",
    "TemplateName": "",
    "Tracked": true,
    "Visible": false,
    "ExtraText": "",
    "SuccessMsg": "",
    "id": "mljstsdiapl8qf"
  }
}
```

## Quest Field Reference

| Field | Type | Value | Required |
|-------|------|-------|----------|
| `EntryId` | UUID | Shared between pair | ✅ |
| `id` | String | `mlh` + 11-14 alphanumeric. **Each entry in a pair MUST have a different `id`** (they share `EntryId` but not `id`). The inProgress entry's `id` is used as `TaskTriggerId` in effects. | ✅ |
| `Name` | String | `0_name`, `1_name` format | ✅ |
| `Description` | String | **Must always be `"created in unity"`**. This is a required fixed value. | ✅ |
| `Status` | String | `"inProgress"` or `"completed"` | ✅ |
| `Group` | String | `""` (single player, persistent), `"nonPersistent"` (single player, resets), or `"multiplayer"` (shared, persistent) | ✅ |
| `DisplayGroup` | String | Group label for quest log UI. `""` = no group. Set same value on multiple quests to group them together in the quest log. | ✅ |
| `Enabled` | Boolean | `true` | ✅ |
| `RepeatableLimit` | Number | `0` = infinite repeats, `1` = one-shot, `N` = max N completions | ✅ |
| `FinishTime` | Number | `0` = no time limit. Positive value = seconds before auto-expiry | ✅ |
| `AutoStart` | Boolean | `false`. If `true`, quest auto-activates when player enters room | ✅ |
| `TriggeredByInventory` | Boolean | `false`. If `true`, quest is triggered by inventory item activation | ✅ |
| `Requirements` | Array | `[]` unless quest has dependencies. See [Requirements](#requirements) below | ✅ |
| `Creator` | String | **Must be the authenticated user's Firebase UID** (from `mcp__portals__authenticate` response). Not an arbitrary string. | ✅ |
| `TemplateName` | String | `""` | ✅ |
| `Tracked` | Boolean | `true` | ✅ |
| `Visible` | Boolean | `false` for animation-only quests, `true` to show in quest log | ✅ |
| `ExtraText` | String | `""` or JSON string for dialogue trees (see DialogEffectorDisplay) | ✅ |
| `Rewards` | Array | `[]` or reward objects (completed entry only). See [Rewards](#rewards) below | ✅ (completed) |
| `SuccessMsg` | String | `""` or message shown on completion (completed entry only) | ✅ (completed) |

### Critical Requirements

**Quest names MUST follow numbered format:**
- ✅ Correct: `"0_collect"`, `"1_activate"`, `"2_complete"`
- ❌ Wrong: `"collect"`, `"quest1"`, `"myQuest"`

**Quest IDs follow `mlh` pattern:**
- Format: `mlh` + 11-14 lowercase alphanumeric chars
- Example: `"mlh9kkyxvll8ql"`, `"mlhab7cd3efg12"`
- NOT UUIDs (those are for `EntryId`)

## Non-Persistent Tasks (tasksRefresh)

By default, quest states persist across page reloads. To make tasks reset on reload, set `tasksRefresh: true` in room settings.

| Setting | Location | Default | Effect |
|---------|----------|---------|--------|
| `tasksRefresh` | Room `settings` (top-level) | `false` | When `true`, all task/quest states reset to NotActive on page reload |

This is a **room-level** setting — it affects ALL quests in the room. There is no per-quest persistence toggle. Use this for:
- Games that should restart fresh each session
- Testing/development (avoid stale state between reloads)
- Arcade-style experiences without save progress

**In room settings JSON:**
```json
{
  "tasksRefresh": true,
  "roomBase": "BlankScene",
  ...
}
```

## Requirements

Quests can depend on other quests via the `Requirements` array. A quest with requirements won't activate until all requirements are met.

**Requirement object structure:**
```json
{
  "delete": false,
  "amount": 1,
  "type": "quest",
  "id": "mlho37zcvchf0u"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `delete` | Boolean | `false` = requirement must be met, `true` = requirement is being removed |
| `amount` | Number | How many times the required quest must be completed (usually `1`) |
| `type` | String | Requirement type. Known value: `"quest"` (depends on another quest) |
| `id` | String | The quest ID (`mlh...` format) of the required quest (use the inProgress entry's `id`) |

**Example — Quest 1 requires Quest 0 to be completed first:**
```python
q0 = create_quest_pair(0, "find_key", creator_uid)
q1 = create_quest_pair(1, "open_door", creator_uid,
    requirements=[{"delete": False, "amount": 1, "type": "quest", "id": q0["quest_id"]}]
)
```

## Rewards

The `Rewards` array on completed quest entries can grant items on completion. This is typically configured through the Portals team for wearable/collectible item setup.

```json
{
  "Rewards": [
    {
      "type": "wearable",
      "id": "item-id-here"
    }
  ]
}
```

## Quest Groups (Scope & Persistence)

Control scope and persistence via the `Group` field:

| Type | `Group` | Scope | Persistence | Use Case |
|------|---------|-------|-------------|----------|
| **Single Player** | `""` (empty) | Per-player | Saved between sessions | Personal progress, achievements |
| **Non-Persistent** | `"nonPersistent"` | Per-player | Resets on leave/reload | Game state that should reset each session |
| **Multiplayer** | `"multiplayer"` | Shared (all players) | Saved between sessions | Cooperative objectives, room-wide events |

**Example - Single Player (persistent):**
```json
{
  "Group": "",
  "Name": "0_tutorial",
  "Description": "created in unity"
}
```
Each player progresses independently. State is saved between sessions.

**Example - Non-Persistent (per-player, resets):**
```json
{
  "Group": "nonPersistent",
  "Name": "0_game_state",
  "Description": "created in unity"
}
```
Per-player state that resets when the player leaves or the room reloads. Ideal for game logic (active game, round state, player roles).

**Example - Multiplayer (shared, persistent):**
```json
{
  "Group": "multiplayer",
  "Name": "0_boss",
  "Description": "created in unity"
}
```
When any player defeats boss, all players see the effect. State persists across sessions.

## Python Generation

**Generating Quest IDs:**
```python
import random
import string
import uuid

def generate_quest_id():
    """Generate quest ID: mlh + 11-14 random lowercase alphanumeric chars"""
    length = random.randint(11, 14)
    chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return f"mlh{chars}"
```

**Creating quest pairs:**
```python
from portals_utils import create_quest_pair

# Basic quest (single player, no special config)
q = create_quest_pair(0, "collect", creator_uid)

# Multiplayer quest visible in quest log
q = create_quest_pair(1, "boss", creator_uid, multiplayer=True, visible=True)

# Quest with dependencies and display grouping
q = create_quest_pair(2, "open_door", creator_uid,
    requirements=[{"delete": False, "amount": 1, "type": "quest", "id": prev_quest_id}],
    display_group="Chapter 1",
)

# One-shot quest with time limit
q = create_quest_pair(3, "timed_challenge", creator_uid,
    repeatable_limit=1,
    finish_time=60,
    success_msg="Challenge completed!",
)
```

**Building complete quests dict:**
```python
creator_uid = "YOUR_FIREBASE_UID"  # from authenticate response
quests = {}

# Add quest 0
q0 = create_quest_pair(0, "collect", creator_uid)
quests.update(q0["entries"])

# Add quest 1
q1 = create_quest_pair(1, "activate", creator_uid)
quests.update(q1["entries"])

# Add quest 2
q2 = create_quest_pair(2, "complete", creator_uid)
quests.update(q2["entries"])

# q0["quest_id"] is the inProgress ID -- use as TaskTriggerId in effects
# q0["quest_name"] is "0_collect" -- use as Name in effects
```

## Linking Effects to Quests

Items subscribe to quest state changes via `TaskEffectorSubscription` in their `logic[itemId].Tasks` array. Interactions live in a separate `logic` dict, not embedded as `extraData` inside items.

**Example: Cube that moves when quest activates**
```python
from portals_effects import add_task_to_logic, quest_effector, effector_move_to_spot
from portals_core import create_cube

# Create quest
quest = create_quest_pair(0, "activate", creator_uid)

# Create cube — returns (item, logic) tuple
items[id_], logic[id_] = create_cube(pos=(0, 0.5, 0), scale=(2, 0.2, 2))

# Add effect to the item's logic entry
task = quest_effector(
    quest_id=quest["quest_id"],
    quest_name=quest["quest_name"],
    target_state=1,  # Fires when quest becomes Active
    effector=effector_move_to_spot(position=(0, 5, 0), duration=2.0)
)
add_task_to_logic(logic[id_], task)
```

## 3-State Effect Pattern

Items can have different effects for each quest state:

```python
from portals_effects import add_tasks_to_logic, quest_effector, effector_move_to_spot

# State 0 (Not Active) - cube at origin
effect_state_0 = quest_effector(
    quest["quest_id"], quest["quest_name"], 0,
    effector_move_to_spot(position=(0, 0.5, 0), duration=0.0)
)

# State 1 (Active) - cube rises
effect_state_1 = quest_effector(
    quest["quest_id"], quest["quest_name"], 1,
    effector_move_to_spot(position=(0, 5, 0), duration=2.0)
)

# State 2 (Completed) - cube returns
effect_state_2 = quest_effector(
    quest["quest_id"], quest["quest_name"], 2,
    effector_move_to_spot(position=(0, 0.5, 0), duration=1.0)
)

# Add all 3 to the item's logic entry
add_tasks_to_logic(logic[id_], [effect_state_0, effect_state_1, effect_state_2])
```

**IMPORTANT:** State 0 effects have NO `TargetState` field (omitted entirely).

## Quest Progression

**Triggering state changes:**

1. **Click to advance:**
```python
from portals_effects import add_task_to_logic, quest_trigger, trigger_on_click

# Click cube to activate quest
task = quest_trigger(
    quest["quest_id"], quest["quest_name"],
    target_state=111,  # Not Active → Active (encoded value)
    trigger=trigger_on_click()
)
add_task_to_logic(logic[id_], task)
```

2. **Auto-start on player login:**
```json
{
  "AutoStart": true
}
```

3. **Variable threshold:**
Use `ValueUpdatedEvent` trigger (see [triggers/world.md](../triggers/world.md))

4. **Timer:**
Use `TimerStoppedEvent` trigger

See [effects/logic.md](../effects/logic.md) for `RunTriggersFromEffector` (chaining quests).

## Common Patterns

**Sequential quests:**
```python
# Quest 0 → Quest 1 → Quest 2
q0 = create_quest_pair(0, "step1", creator_uid)
q1 = create_quest_pair(1, "step2", creator_uid)
q2 = create_quest_pair(2, "step3", creator_uid)

quests = {}
quests.update(q0["entries"])
quests.update(q1["entries"])
quests.update(q2["entries"])

# When q0 completes, activate q1
# When q1 completes, activate q2
# (Use RunTriggersFromEffector - see effects/logic.md)
```

**Collectible quest:**
```python
# Create variable
variables = [{"name": "coins", "variableType": "Numeric", "multiplayer": False}]

# Quest advances when coins >= 10
# (Use ValueUpdatedEvent trigger)
```

**Multiplayer cooperative quest:**
```python
quest = create_quest_pair(0, "team", creator_uid, multiplayer=True)
quests.update(quest["entries"])
```

## Best Practices

✅ **Do:**
- Use numbered quest names: `0_name`, `1_name`, `2_name`
- Generate quest IDs with `portals_utils.generate_quest_id()`
- Always read existing quests before writing (avoid overwriting)
- Use `multiplayer` for room-wide events
- Set `Visible:false` for animation-only quests

❌ **Don't:**
- Skip numbered prefix in quest names
- Use UUIDs for quest `id` field (use `mlh` format)
- Forget to create both `inProgress` and `completed` entries
- Omit required fields
- Use `TargetState` field on state 0 effects

## Debugging

**Check quest state:**
- Use Portals web interface build mode
- Inspect quest panel to see current state
- Verify quest name format and ID pattern

**Common issues:**
- Quest name missing numbered prefix → won't work
- Quest ID wrong format → won't link to effects
- Missing `TargetState` on states 1/2 → won't fire
- Including `TargetState` on state 0 → wrong behavior
