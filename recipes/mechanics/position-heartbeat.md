---
name: Position Heartbeat & Minimap
category: mechanics
tags: [heartbeat, position, tracking, minimap, hud, iframe, loop, timer, broadcast, map, player dot]
patterns: [chain-reaction, quest-gated-effect]
summary: Complete minimap system — heartbeat broadcasts player positions, hosted iframe renders them on an auto-generated or custom map image
depends: []
---

# Position Heartbeat & Minimap

A complete minimap system for any Portals room.

**IMPORTANT: The minimap HTML viewer is ALREADY HOSTED. Do NOT write your own minimap HTML.**
The hosted viewer URL is: `https://busportals.github.io/portals-games/minimap/`
You configure it entirely via URL parameters. See "Minimap Integration" section below.

This recipe has two parts:
1. **Position Heartbeat** — a quest loop that broadcasts player positions to iframes at ~10Hz
2. **Minimap Integration** — opening the hosted minimap iframe with the right URL params

## Part 1: Position Heartbeat

### Items needed

- **Heartbeat controller** (ResizableCube, hidden — fires on player login)
- **Heartbeat quest** (non-persistent, invisible, repeatable)

### Wiring pattern

```python
from portals_core import create_cube
from portals_effects import (
    basic_interaction, quest_effector, add_task_to_logic,
    trigger_player_logged_in, effector_send_iframe_message,
    effector_run_triggers
)
from portals_utils import create_quest_pair

CREATOR_UID = "YOUR_FIREBASE_UID"

# --- Quest (MUST be non-persistent so it resets each session) ---
hb_quest = create_quest_pair(
    number=99, name_suffix="heartbeat",
    creator=CREATOR_UID,
    non_persistent=True,  # REQUIRED — resets on leave, enables the loop to restart
    auto_start=False,
    visible=False,
    repeatable_limit=0,  # infinite
)
hb_id = hb_quest["quest_id"]
hb_name = hb_quest["quest_name"]

# --- Heartbeat controller (hidden cube — OnPlayerLoggedIn works on any item) ---
items[hb_cube_id], logic[hb_cube_id] = create_cube(
    pos=(0, -10, 0),  # below ground, out of sight
    scale=(1, 1, 1),
    opacity=0.01,
)

# 1. Player logs in → activate quest (starts the loop)
add_task_to_logic(logic[hb_cube_id], basic_interaction(
    trigger_player_logged_in(),
    effector_run_triggers([{
        "quest_id": hb_id, "quest_name": hb_name,
        "target_state": 151,  # Any -> Active
        "delay": 0.0
    }])
))

# 2. Quest becomes Active → send position to all iframes
add_task_to_logic(logic[hb_cube_id], quest_effector(
    hb_id, hb_name, 1,  # 1 = Active/InProgress
    effector_send_iframe_message("|username|pos:|position|")
))

# 2b. Quest becomes Active → send rotation to all iframes
add_task_to_logic(logic[hb_cube_id], quest_effector(
    hb_id, hb_name, 1,
    effector_send_iframe_message("|username|rot:|rotation|")
))

# 3. Quest becomes Active → complete it after 0.1s (to loop)
add_task_to_logic(logic[hb_cube_id], quest_effector(
    hb_id, hb_name, 1,
    effector_run_triggers([{
        "quest_id": hb_id, "quest_name": hb_name,
        "target_state": 121,  # Active -> Completed
        "delay": 0.01
    }])
))

# 4. Quest completes → re-activate it (loop continues)
add_task_to_logic(logic[hb_cube_id], quest_effector(
    hb_id, hb_name, 2,  # 2 = Completed
    effector_run_triggers([{
        "quest_id": hb_id, "quest_name": hb_name,
        "target_state": 151,  # Any -> Active
        "delay": 0.0
    }])
))
```

### How it works

1. Player logs into the room → `OnPlayerLoggedIn` fires → quest activates
2. Quest Active (state 1) fires three effects simultaneously:
   - `SendMessageToIframes` with `|username|pos:|position|` — broadcasts position data
   - `SendMessageToIframes` with `|username|rot:|rotation|` — broadcasts Y-rotation (degrees)
   - `RunTriggersFromEffector` with 0.01s delay → transitions quest Active → Completed
3. Quest Completed (state 2) fires `RunTriggersFromEffector` → transitions Any → Active
4. Back to step 2 — loop repeats forever at ~100Hz

### Adding more data

Stack additional `SendMessageToIframes` on the Active state to send more variables:

```python
# Also send health
add_task_to_logic(logic[hb_cube_id], quest_effector(
    hb_id, hb_name, 1,
    effector_send_iframe_message("|username|health:|health|")
))
```

### Stopping the heartbeat

To stop the loop (e.g., on game over), transition the quest to Not Active without re-activating:

```python
effector_run_triggers([{
    "quest_id": hb_id, "quest_name": hb_name,
    "target_state": 101,  # Any -> Not Active
    "delay": 0.0
}])
```

## Part 2: Minimap Integration (Complete Setup)

The heartbeat broadcasts positions. To display them, open the **already-hosted** minimap iframe viewer. **Do NOT create your own minimap HTML file** — the viewer is hosted at `https://busportals.github.io/portals-games/minimap/` and is configured entirely via URL parameters.

### Step 1: Generate a map image

```bash
# Auto-generate a top-down blueprint from the room snapshot
python tools/generate_minimap.py games/{room-id}/snapshot.json
# → creates games/{room-id}/minimap.png
# → prints world bounds and minimap URL template
```

### Step 2: Upload the map image

Upload `minimap.png` via MCP `upload_image` tool. Save the CDN URL.

### Step 3: Open the minimap iframe on player login

Add this to the SAME heartbeat controller item (or any other item):

```python
from portals_effects import basic_interaction, trigger_player_logged_in, effector_open_iframe, add_task_to_logic

# Open minimap iframe when player logs in
# Replace values from generate_minimap.py output
MINIMAP_URL = (
    "https://busportals.github.io/portals-games/minimap/"
    "?map=YOUR_CDN_URL"
    "&xMin=-35&xMax=35&zMin=-35&zMax=35"  # world bounds from generator
    "&imgW=900&imgH=900"                    # image dimensions from generator
    "&shape=circle&radius=126"
    "&showAll=true"
    "&style=dark"
)

add_task_to_logic(logic[hb_cube_id], basic_interaction(
    trigger_player_logged_in(),
    effector_open_iframe(
        MINIMAP_URL,
        no_close_btn=True,
        no_blur=True,
        no_pointer_events=True,  # click-through — player can still interact with game
        width=270, height=270,   # slightly larger than diameter (2×radius)
        left=30, bottom=100,
    )
))
```

### Step 4: Verify

Both the heartbeat AND the iframe opener fire on `OnPlayerLoggedIn`. When a player joins:
1. Heartbeat quest starts looping → positions broadcast to all iframes
2. Minimap iframe opens → receives position messages → renders player dot on map

### Minimap URL parameters reference

| Param | Required | Default | Description |
|-------|----------|---------|-------------|
| `map` | yes | — | URL-encoded image URL (CDN) |
| `xMin`, `xMax` | yes | — | World X bounds (from generator output) |
| `zMin`, `zMax` | yes | — | World Z bounds (from generator output) |
| `imgW`, `imgH` | yes | — | Image pixel dimensions (from generator output) |
| `shape` | no | `circle` | `circle` or `rect` |
| `radius` | no | `126` | Viewport radius in pixels |
| `showAll` | no | `false` | Show all players (`true`) or just self |
| `dotColor` | no | `#69d2ff` | Player dot color (URL-encoded hex) |
| `otherColor` | no | `#ff6b6b` | Other players' dot color |
| `style` | no | `dark` | `dark` (bg + border) or `minimal` (transparent) |

### Custom map image (with calibration)

If using a hand-drawn or screenshot map instead of auto-generated:

1. Open the minimap in calibration mode as a **positioned, non-blocking** iframe so the player can see the game world while walking:

```python
# Calibration iframe — positioned top-left, sized to not cover the whole screen
CAL_URL = (
    "https://busportals.github.io/portals-games/minimap/"
    "?calibrate=true"
    "&map=YOUR_IMAGE_URL"
    "&imgW=W&imgH=H"
    "&noBlur=true"
    "&width=500&height=400"
    "&left=0&top=0"
)

add_task_to_logic(logic[some_item_id], basic_interaction(
    trigger_player_logged_in(),
    effector_open_iframe(CAL_URL, no_blur=True)
))
```

2. Walk to a recognizable spot in the room → tap **Mark Position** → tap that spot on the map image
3. Walk to a **different** recognizable spot → tap **Mark Position** → tap that spot on the map
4. Copy the generated URL with calibrated bounds
5. Remove the calibration iframe and replace with the final minimap URL using the calibrated bounds

## Critical Rules

1. **Do NOT write your own minimap HTML.** The viewer is already hosted at `https://busportals.github.io/portals-games/minimap/`. Configure it via URL params only. Never create local HTML files for the minimap.
2. Use `OnPlayerLoggedIn` (not `OnEnterEvent`) to start the heartbeat — it fires reliably when a player enters the room, works on any item type, and doesn't require a giant invisible trigger zone.
2. The quest MUST use `non_persistent=True` (sets `Group: "nonPersistent"`) and `repeatable_limit=0`. Non-persistent means the quest resets when the player leaves — this is required so the heartbeat loop restarts on each visit. Using `multiplayer=False` alone sets `Group: ""` which is **persistent** and will break the loop on re-entry.
3. The 0.01s delay on Active → Completed prevents infinite recursion. Do not set to 0.
4. `|position|` is a built-in variable that resolves to ALL players' positions, not just the triggering player.
5. `|rotation|` is a built-in variable that resolves to ALL players' Y-rotations in degrees (0-360). Format: `{"Player1"="343.0", "Player2"="120.5"}`.
6. The heartbeat fires per-player — each player's client runs its own loop. The iframe receives messages from the local player's loop.
7. The minimap renders players as directional arrows (not dots) using the rotation data — arrows point in the direction each player is facing.
