# Game Logic Board

> **Context loading:** Read this doc when creating a visual logic board to display game trigger/effect chains.

Generate a cyberpunk circuit-board flowchart inside a Portals room that visually maps the entire game logic -- triggers, effects, quests, conditionals, and timing. Nodes are color-coded by function, connected by bars, and animated with traveling electric pulses.

**Key principle: The board is not just a diagram -- it's the functional home for global logic.** Instead of scattering invisible helper cubes around the room to hold ambient sounds, login triggers, variable initialization, and other "orphan" logic, attach that logic directly to the board's nodes. The board becomes both documentation AND implementation. Players (and builders) can find everything in one place.

**Helper functions:** `lib/board_helpers.py`

## Workflow

### 1. Analyze the Game

Read the game's `generate.py` (preferred) or `snapshot.json`. Extract every:
- **Trigger -> Effect chain** (OnClickEvent -> PlaySound, SetTask, etc.)
- **Quest state transition** (NotActive -> Active -> Completed -> reset)
- **Conditional branch** (FunctionEffector with `if($N{var})` or `$T{quest}`)
- **Timing/delay** (auto-advance durations, effect delays)
- **Parameter setting** (SetPlayersParameters, SetNumberVariable)

Build a directed graph: each node is a logical step, each edge is a causal connection with optional delay.

### 2. Classify Nodes

Every logical step gets a type and color:

| Type | Color | Hex | Emission | Use for |
|------|-------|-----|----------|---------|
| **Input** | Amber | `FFB800` | 0.45 | Player actions (click, enter, hover) |
| **Logic** | Purple | `9B59B6` | 0.40 | Conditions, branching, parameter setting |
| **Quest** | Emerald | `2ECC71` | 0.40 | Quest state changes (->Active, ->Completed) |
| **Effect** | Cyan | `00D4FF` | 0.35 | Outputs (sound, teleport, notification) |
| **Auto-reset** | Dim variant | see below | 0.15-0.20 | Timed resets back to NotActive |

Auto-reset dim colors: Red `992222`, Blue `223399`, Green `1A7A3A`, Gray `444444`.

### 3. Layout

Arrange nodes in horizontal rows by **dependency depth** (topological sort):
- **Row 0 (top)**: Entry points -- player triggers, initial actions
- **Row 1**: Immediate effects -- what happens on trigger
- **Row 2**: Logic gates -- conditionals, quest checks
- **Row 3+**: Branching paths -- team splits, outcomes, effects
- **Bottom rows**: Auto-reset chains

**Spacing rules** (all multiplied by scale factor `S = 4.5`):
- Vertical row spacing: `1.6S` between rows
- Horizontal node spacing: `4S` between nodes in same row
- Parallel branches spread symmetrically from center

### 4. Generate

Add a `# LOGIC BOARD` section to the game's `generate.py`. Use the helper functions from `lib/board_helpers.py` -- copy them into the generate script or adapt the pattern.

**Required board elements:**
1. Base board (dark cube, all items parented to it)
2. Nodes with borders (color-coded by type)
3. Labels on each node (bold title + gray sublabel showing effect type)
4. Connectors between nodes (horizontal, vertical, or diagonal)
5. Delay annotations on connectors (orange text showing timing)
6. Animated pulses tracing each flow path
7. Legend in top-right corner
8. Section divider labels
9. Decorative grid, corner accents, edge glow

## Functional Nodes -- Logic Lives Here

When building a game from scratch, **attach real game logic to the board nodes instead of hiding it on invisible cubes scattered around the room.** The board node is both the visual representation AND the item that holds the trigger/effect.

### What goes on board nodes

| Logic type | Example | Board node |
|------------|---------|------------|
| Ambient sound loop | `PlaySoundInALoop` on `OnPlayerLoggedIn` | "AMBIENT" effect node |
| Global variable init | `SetNumberVariable` on `OnPlayerLoggedIn` | "INIT VARS" logic node |
| Quest auto-advance | `SetTask` effectors for timed quest transitions | "AUTO-RESET" node |
| Conditional branching | `FunctionEffector` with `if($N{var})` | "CHECK" logic node |
| Global notifications | `NotificationPillEvent` for game-wide messages | "NOTIFY" effect node |
| Score tracking | `SetNumberVariable` / `OnChange` listeners | "SCORE" logic node |

### What stays on world items

Logic that is inherently tied to a physical object stays on that object:
- **Click triggers** -- stay on the clickable cube/GLB (the player clicks *that* item)
- **Enter/exit triggers** -- stay on the trigger cube at that location
- **Item-specific effects** -- hide/show/animate a specific object stays on it
- **Collision/physics** -- stays on the physical item

### How it works in generate.py

When creating a board node that also holds logic, add the tasks to the node cube:

```python
# Create the node visually
node_id = board_node(lx, ly, NODE_W, NODE_H, COL_EFFECT,
                     board_id, add, create_cube, title="Node_Ambient")
board_label(lx, ly + S * 0.1, "<b><color=#FFFFFF>AMBIENT</color></b>",
            board_id, add, create_text)

# Attach the ACTUAL logic to this node
ambient_task = {
    "$type": "TaskTriggerSubscription",
    "Trigger": {"$type": "OnPlayerLoggedIn"},
    "DirectEffector": {
        "Effector": {"$type": "PlaySoundInALoop", "Url": "...", "Dist": 100},
        ...
    },
    ...
}
add_task_to_item(items[node_id], ambient_task)
```

The node is now both the visual label on the board AND the item running the logic. No hidden helpers needed.

## Board Architecture

### Coordinate System

```
Board base cube at BOARD_POS, e.g. (0, 27, -40)
All child items use board-local coordinates (lx, ly)
World position = BOARD_POS + (lx, ly, z_offset)

Board size: 18S x 12S (81 x 54 units at S=4.5)
Usable range: roughly (-8S, -5.5S) to (+8S, +5.5S)
```

### Z-Layering (prevents z-fighting)

| Layer | Z offset | Contents |
|-------|----------|----------|
| Grid | -0.01 | Background grid lines |
| Connectors | 0.07 | Bars between nodes |
| Nodes | 0.10 | Colored rectangles |
| Pulses | 0.11 | Animated dots |
| Text | 0.16 | All labels |

### Node Sizes

| Type | Width | Height | Thickness |
|------|-------|--------|-----------|
| Standard | `2S` (9) | `1S` (4.5) | 0.04 |
| Small (effects, resets) | `1.5S` (6.75) | `0.7S` (3.15) | 0.04 |
| Border | node + `0.12S` padding | same | 0.04 |

### Text Scaling

All text uses `TEXT_SCALE = 6` multiplier applied to base scales:

| Element | Base scale | Final (x6) |
|---------|-----------|------------|
| Board title | `S x 0.7` | 18.9 |
| Node title | `S x 0.35-0.4` | ~10-11 |
| Node sublabel | `S x 0.25-0.3` | ~7-8 |
| Delay annotation | `S x 0.3` | 8.1 |
| Legend text | `S x 0.28` | 7.56 |

Rich text tags: `<b>Bold</b>`, `<color=#HEX>colored</color>`, `<size=N%>scaled</size>`

### Connectors

- Height: `0.05S` -- thin bars
- Thickness: 0.03 -- slightly behind nodes in Z
- Gap from node edge: `CONN_GAP = 0.08S` -- don't touch the node
- Diagonal connectors: rotated via Z-axis quaternion (`sin(angle/2)`, `cos(angle/2)`)

### Animated Pulses

Small cubes (`0.12S`) that travel along waypoint paths:
- Emission: 1.0, opacity: 0.9 (bright and visible)
- Speed: `PULSE_SPEED = 3S` units/sec
- Duration per segment: `distance / PULSE_SPEED` (min 0.1s)
- Triggered by `OnPlayerLoggedIn`, loop seamlessly
- Color matches the flow (amber for input path, red for red team path, etc.)

Each pulse needs a `PortalsAnimation` with `_transformStates` and `states` arrays, triggered by `TaskTriggerSubscription` with `OnPlayerLoggedIn`.

### Decorations

- **Grid**: Vertical + horizontal lines (`0.02` wide, color `1C1C2E`, emission 0.03)
- **Corner accents**: Small cyan squares at four corners
- **Edge glow**: Thin cyan borders along all four edges
- **Board light**: Point light in front of board (color `334455`, brightness 2.0, range `8S`)

## Helper Functions Reference

The file `lib/board_helpers.py` contains all the reusable helper functions. Copy the relevant functions into your generate.py's logic board section:

| Function | Purpose |
|----------|---------|
| `board_item(item, board_id)` | Parent any item to the board |
| `board_node(lx, ly, w, h, color, ...)` | Colored node rectangle |
| `board_node_border(lx, ly, w, h, color, ...)` | Subtle border glow around node |
| `board_label(lx, ly, text, scale, ...)` | Text label on the board |
| `board_connector_h(x1, x2, y, ...)` | Horizontal connector bar |
| `board_connector_v(x, y1, y2, ...)` | Vertical connector bar |
| `board_connector_diag(x1, y1, x2, y2, ...)` | Diagonal connector (rotated) |
| `board_pulse(waypoints, color, ...)` | Animated traveling pulse |
| `delay_label(x, y, text, ...)` | Orange timing annotation |
| `add_legend(base_x, base_y, node_types, ...)` | Auto-generate legend |
| `add_decorations(S, ...)` | Grid, corners, edge glow |

## Layout Algorithm

For complex games, use this approach:

1. **Parse** -- Walk the generate.py and list every trigger->effect relationship as edges
2. **Topological sort** -- Assign each node a depth (row number)
3. **Row Y coordinates** -- `y = S * (top_row - depth * 1.6)` where `top_row` ~ 3-5 depending on board height
4. **Column X coordinates** -- Within a row, center nodes: `x = S * ((col - (count-1)/2) * 4)`
5. **Branch detection** -- Conditional nodes (if/else, team split) create parallel sub-trees; spread children symmetrically
6. **Auto-reset chains** -- Append below their parent branch, offset by `1S` per step
7. **Connect** -- Draw connectors following the edges; use horizontal when same row, vertical when same column, diagonal otherwise
8. **Pulse paths** -- Trace each distinct flow path (main flow, each branch, each reset chain) as a pulse waypoint list

## Scaling for Larger Games

| Nodes | Scale factor S | Board multiplier | Notes |
|-------|---------------|-----------------|-------|
| 5-15 | 4.5 | 18S x 12S | Standard |
| 15-30 | 4.5 | 22S x 16S | Wider board |
| 30-50 | 3.5 | 22S x 18S | Smaller nodes, tighter spacing |
| 50+ | 3.0 | 26S x 20S | Consider splitting into sub-boards |

## Common Mistakes

- **No z-layering** -- Nodes, connectors, text at same Z = visual mess. Always separate.
- **Text too small** -- Always apply `TEXT_SCALE = 6`. Board is physically large.
- **No legend** -- Players won't know what colors mean. Always include one.
- **Static board** -- Animated pulses are what make it feel alive and show flow direction.
- **Connectors touching nodes** -- Use `CONN_GAP` to inset from edges.
- **Forgetting parenting** -- Every board item must have `parentItemID` set to the base board.
- **Wrong position convention** -- Board items use board-local coords added to `BOARD_POS`, not parented-relative offsets.
- **Hidden helper cubes** -- Don't create invisible cubes at `(0, -10, 0)` for global logic. Put that logic on the board nodes instead. The board is the home for all non-physical game logic.
