# Builder Workflow

> **Context loading:** Read this doc when building or iterating on a game from an approved design.

Translates approved game designs into playable Portals rooms, and iterates based on playtesting feedback.

## Build Workflow

### Step 1: Load Context

1. Read the design doc: `games/{room-id}/design.md`
2. Read the relevant docs from `docs/` -- check `docs/INDEX.md` for what's available
   - Item formats: `docs/reference/items/` (building.md, models.md, gameplay.md, media.md, lighting.md, display.md, interactive.md)
   - Effects & triggers: `docs/reference/interactions.md`
   - Quests: `docs/reference/quests.md`
3. Read existing Python helpers: check `lib/portals_core.py`, `lib/portals_effects.py`, `lib/portals_utils.py`
   - Use these for items they support (cubes, text, spawns, portals, collectibles, jump pads, triggers, leaderboards)
   - For item types NOT in the helpers (lights, NPCs, GLBs, images, videos, guns, etc.), construct item dicts directly using the reference
4. If the game involves **gating progress on conditions, tracking/modifying values (scores, coins, health), decisions based on state, randomness, timer logic, multiplayer role/team assignment, or delayed consequences**, load `docs/workflows/function-effects-reference.md` for FunctionEffector expression syntax

### Step 2: Write the Generation Script

Create `games/{room-id}/generate.py` with this structure:

```python
"""
{Game Name} -- Generation Script
Produces all room data for: {one-line description}
Room: {room-id}
"""

import sys
import os
import json
import uuid
import random
import string
import math

# Adjust this path to point to your project's lib/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from portals_core import create_cube, create_text, create_spawn, create_portal, create_collectible, create_jump_pad, create_trigger, create_leaderboard, create_base_item
from portals_effects import create_move_effect, create_show_hide_effect, create_run_triggers_effect, create_click_trigger, add_effect_to_item, add_effects_to_item
from portals_utils import create_quest_pair, generate_quest_id, quaternion_from_euler, validate_room_data

# ============================================================================
# Configuration -- tweak these to iterate
# ============================================================================
GAME_NAME = "{Game Name}"
# ... game-specific parameters ...

# ============================================================================
# Item Generation
# ============================================================================
items = {}
quests = {"inProgress": [], "completed": []}
item_id = 2  # Start at 2 (1 is reserved)

def next_id():
    global item_id
    current = str(item_id)
    item_id += 1
    return current

# --- Spawn Point ---
items[next_id()] = create_spawn(pos=(0, 0.2, 0), name="")

# --- Environment ---
# (floors, walls, decorations, lighting)

# --- Gameplay ---
# (platforms, triggers, collectibles, NPCs, etc.)

# --- Quests & Effects ---
# (quest pairs, state-driven animations, chaining)

# ============================================================================
# Output
# ============================================================================
errors = validate_room_data({"items": items, "quests": quests})
if errors:
    print("VALIDATION ERRORS:")
    for e in errors:
        print(f"  - {e}")
else:
    print(f"Generated {len(items)} items, {len(quests['inProgress'])} quests")
    print(f"Item IDs: 2 to {item_id - 1}")

# Save snapshot
output = {"items": items, "quests": quests}
output_path = os.path.join(os.path.dirname(__file__), 'snapshot.json')
with open(output_path, 'w') as f:
    json.dump(output, f, indent=2)
print("Snapshot saved.")
```

### Script Quality Requirements

- **Well-commented**: Group items by purpose (environment, gameplay, lighting, etc.)
- **Parameterized**: Put tunable values (colors, sizes, positions, difficulty) in a config section at the top
- **Complete**: Must generate ALL items needed -- environment, gameplay, lighting, decorations, audio-enabled collectibles
- **Validated**: Run `validate_room_data()` before output

### Building Item Types Without Helpers

For items not covered by `portals_core.py`, use `create_base_item()` directly:

```python
# Light
items[next_id()] = create_base_item(
    prefab_name="Light",
    pos=(0, 3, 0),
    extra_data={"c": "FFFFFF", "b": 2.0, "r": 10.0, "Tasks": [], "ViewNodes": []}
)

# NPC
items[next_id()] = create_base_item(
    prefab_name="GLBNPC",
    pos=(5, 0, 3),
    content_string="https://example.com/avatar.glb",
    extra_data={"n": "Guide", "a": "", "p": "You are a friendly guide. Help the player.", "bq": True, "swn": True, "events": [], "tags": [], "Tasks": [], "ViewNodes": []}
)

# Image (needs rotation to stand upright)
items[next_id()] = create_base_item(
    prefab_name="DefaultPainting",
    pos=(0, 2, -5),
    rot=quaternion_from_euler(pitch=90),  # Stand upright
    scale=(3, 2, 0.03),
    content_string="https://example.com/image.png",
    extra_data={"t": True, "b": True, "Tasks": [], "ViewNodes": []}
)

# GLB model
items[next_id()] = create_base_item(
    prefab_name="GLB",
    pos=(0, 0, 0),
    content_string="https://example.com/model.glb",
    extra_data={"s": False, "Tasks": [], "ViewNodes": []}
)

# Gun
items[next_id()] = create_base_item(
    prefab_name="Gun",
    pos=(5, 0.5, 0),
    extra_data={"weaponType": 1, "maxDamage": 20, "minDamage": 10, "firerate": 0.5, "clipSize": 12, "startLoaded": True, "Tasks": [], "ViewNodes": []}
)
```

### Step 3: Run and Push

1. Run the script: `python games/{room-id}/generate.py`
2. Verify the output: check item count, quest count, any validation errors
3. Authenticate with MCP: call `authenticate` (opens browser for login)
4. Read existing room data: `get_all_room_data` -- check if room has items
5. Confirm with user if overwriting existing items
6. Push items: `set_room_items(roomId, data=items)`
7. Push quests if any: `set_room_quests(roomId, data=quests)`
8. Return URL: `https://theportal.to/room/{room-id}`

**Important**: The MCP has payload size limits. If the game has 100+ items, consider pushing in sections or verify the push succeeds.

## Iterate Workflow

When the user returns with playtesting feedback:

### Step 1: Understand the Feedback

- Read `games/{room-id}/design.md` and `games/{room-id}/generate.py` to remember context
- Interpret feedback through a game design lens:
  - "Too hard" -> platform too small? gap too wide? jump pad underpowered? too few checkpoints?
  - "Boring" -> not enough variety? reward loop too slow? missing progression?
  - "Confusing" -> no visual cues? missing NPC guidance? unclear objective?
  - "Ugly" -> no environment dressing? flat lighting? no color variety?
- **Propose the fix** -- don't just ask "what do you want to change?"

### Step 2: Update the Script

- Modify the generation script parameters or structure
- Re-run to produce updated room data
- Save new snapshot

### Step 3: Push and Log

- Push updated data to room via MCP
- Append to `games/{room-id}/changelog.md`:
  ```
  ## YYYY-MM-DD
  - {What changed}: {why, based on what feedback}
  ```

## The Complete Game Checklist

Before declaring ANY game done, verify ALL of these:

- [ ] **Clear start** -- spawn point with immediate visual/audio cue about what to do
- [ ] **Core loop** -- the fun thing you do repeatedly is present and working
- [ ] **Progression** -- difficulty or complexity changes over time
- [ ] **Feedback** -- collecting/winning/failing has sound + visual response
- [ ] **Climax** -- there's a build-up to a final moment
- [ ] **Ending** -- win/lose is acknowledged (leaderboard, NPC, notification)
- [ ] **Environment** -- the space has floors, walls, lighting, and decoration beyond bare mechanics
- [ ] **Audio** -- ambient sound, action sounds, victory/defeat sounds exist

If ANY item is unchecked, keep building. A game missing environment or audio is not done.
