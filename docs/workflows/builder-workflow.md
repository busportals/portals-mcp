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
3. Read `docs/reference/api-cheatsheet.md` for the complete API (all item creators, triggers, effectors, helpers)
4. If the game involves **gating progress on conditions, tracking/modifying values (scores, coins, health), decisions based on state, randomness, timer logic, multiplayer role/team assignment, or delayed consequences**, load `docs/workflows/function-effects-reference.md` for FunctionEffector expression syntax

### Step 2: Write the Generation Script

Create `games/{room-id}/generate.py` with this structure:

```python
"""
{Game Name} -- Generation Script
Produces all room data for: {one-line description}
Room: {room-id}
"""
import sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

# Import only what this script needs — see docs/reference/api-cheatsheet.md for full API
from portals_core import create_cube, create_spawn, create_glb, create_light, create_trigger
from portals_effects import basic_interaction, add_task_to_logic, trigger_on_click, effector_notification
from portals_utils import serialize_logic, default_settings, yrot

# ============================================================================
# Item Generation
# ============================================================================
items = {}
logic = {}
quests = {}
item_id = 2  # Start at 2 (1 is reserved)

def next_id():
    global item_id
    current = str(item_id)
    item_id += 1
    return current

# All creators return (item, logic) tuples — always unpack into both dicts
id_ = next_id()
items[id_], logic[id_] = create_spawn(pos=(0, 0.2, 0), name="")

# To add interactions, wire tasks into the logic entry:
# add_task_to_logic(logic[id_], basic_interaction(
#     trigger=trigger_on_click(),
#     effector=effector_notification("Clicked!", "00FF00")
# ))

# ============================================================================
# Output
# ============================================================================
room_data = {
    "roomItems": items,
    "logic": logic,
    "settings": default_settings(),
    "roomTasks": {"Tasks": []},
    "quests": quests,
}

# REQUIRED: serialize logic dicts to JSON strings before writing
serialize_logic(room_data)

output_path = os.path.join(os.path.dirname(__file__), 'snapshot.json')
with open(output_path, 'w') as f:
    json.dump(room_data, f, indent=2)
print(f"Snapshot saved. {len(items)} items, {len(quests)} quest entries.")
```

### Script Quality Requirements

- **Well-commented**: Group items by purpose (environment, gameplay, lighting, etc.)
- **Parameterized**: Put tunable values (colors, sizes, positions, difficulty) in a config section at the top
- **Complete**: Must generate ALL items needed -- environment, gameplay, lighting, decorations, audio-enabled collectibles
- **Validated**: Run `python tools/validate_room.py` on the output before pushing

### Key Patterns

All item creators return `(item, logic)` tuples. Items hold spatial/visual data; logic holds behavioral data (interactions, type config). Import only what you need — the full API is in `docs/reference/api-cheatsheet.md`.

### Step 3: Run, Validate, and Push

1. Run the script: `python games/{room-id}/generate.py`
2. Validate: `python tools/validate_room.py games/{room-id}/snapshot.json` -- fix any errors before pushing
3. Authenticate with MCP: call `authenticate` (opens browser for login)
4. Read existing room data: `get_room_data(roomId)` -- check if room has items
5. Confirm with user if overwriting existing data
6. Push: `set_room_data(roomId, filePath)` -- pushes the entire snapshot.json (items, logic, settings, quests, roomTasks) in one call
7. Return URL: `https://theportal.to/?room={room-id}`

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
