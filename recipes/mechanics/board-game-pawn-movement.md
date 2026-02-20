---
name: Board Game Pawn Movement
category: mechanics
tags: [pawn, board game, move, walk, npc, glb, step, waypoint, horse race, token, piece, board]
patterns: [quest-gated-effect, state-machine, variable-tracking, chain-reaction]
summary: Move pawns along a board using quest-sequenced steps — NPC approach (WalkNpcToSpot) or GLB approach (MoveToSpot, recommended for performance)
---

# Board Game Pawn Movement

Move game pieces along a sequence of waypoints on a board. Each step is a quest — completing quest `STEP1` moves the pawn to position 1, `STEP2` to position 2, and so on. A position counter variable tracks which step the pawn is on, and a function effect maps the counter to the correct quest completion.

Two approaches: **GLB pawns** (recommended) and **NPC pawns**.

## GLB Pawns (Recommended)

GLBs are lighter weight than NPCs — faster to load, lower resource usage, and work with any 3D model. Use `MoveToSpot` to animate the pawn to each waypoint.

### Items needed

- **Pawn** — a GLB item (the game piece that moves)
- **Step dispatcher** — a ResizableCube with logic that maps the position counter to quest completions
- **Position counter** — a shared variable tracking which step the pawn is on

### Waypoint list

Define positions as a list. Each index corresponds to a step number:

```python
# Board positions — index 0 is the start, index N is step N
WAYPOINTS = [
    [0.0, 0.5, -10.0],  # start (step 0)
    [0.0, 0.5, -9.0],   # step 1
    [0.0, 0.5, -8.0],   # step 2
    [1.0, 0.5, -8.0],   # step 3 (turn corner)
    [2.0, 0.5, -8.0],   # step 4
    # ... continue for all board spaces
]
```

### Pawn wiring (GLB)

Each quest moves the pawn to the next waypoint using `MoveToSpot`:

```python
from portals_effects import (
    quest_interaction, add_task_to_logic, effector_move_to_spot
)

# Generate one quest-driven MoveToSpot per step
for i, pos in enumerate(WAYPOINTS[1:], start=1):
    quest_name = f"BLUE{i}"
    quest_id = generate_quest_id()  # unique ID

    add_task_to_logic(logic[pawn_id], quest_interaction(
        quest_name=quest_name,
        quest_id=quest_id,
        target_state=2,  # on quest completed
        effector=effector_move_to_spot(
            position=pos,
            duration=0.5  # animate over 0.5 seconds
        )
    ))
```

### Quest definitions

Each step needs a quest entry:

```python
from portals_utils import make_quest

quests = {}
for i in range(1, len(WAYPOINTS)):
    quest_name = f"BLUE{i}"
    quests[quest_name] = make_quest(
        name=quest_name,
        display_name=f"Step {i}",
        creator=CREATOR_UID,
        shared=True  # all players see the same board state
    )
```

---

## NPC Pawns

NPCs use `WalkNpcToSpot` which plays a walk animation while moving. More visually engaging for character-style pawns, but heavier on resources.

### Items needed

- **NPC pawn** — a GLBNPC item (robot NPC or custom rigged GLB)
- **Step dispatcher** — same as GLB approach
- **Position counter** — same as GLB approach

### Pawn wiring (NPC)

```python
from portals_effects import (
    quest_interaction, add_task_to_logic, effector_walk_npc_to_spot
)

# Generate one quest-driven WalkNpcToSpot per step
for i, pos in enumerate(WAYPOINTS[1:], start=1):
    quest_name = f"RED{i}"
    quest_id = generate_quest_id()

    add_task_to_logic(logic[npc_id], quest_interaction(
        quest_name=quest_name,
        quest_id=quest_id,
        target_state=2,  # on quest completed
        effector=effector_walk_npc_to_spot(
            position=pos,
            walk_speed=3.0  # units per second
        )
    ))
```

### NPC starting position

When using NPCs, add a `startgame` quest that resets the NPC to the start position at high speed (instant snap-back):

```python
add_task_to_logic(logic[npc_id], quest_interaction(
    quest_name="startgame",
    quest_id=generate_quest_id(),
    target_state=2,
    effector=effector_walk_npc_to_spot(
        position=WAYPOINTS[0],
        walk_speed=15.0  # fast snap to start
    )
))
```

---

## The Step Dispatcher

The dispatcher is the brain — it reads the position counter and completes the matching quest. This is the same pattern for both GLB and NPC pawns.

### Approach A: Nested-if chain (up to ~50 steps)

For boards with up to ~50 spaces, use a nested `if` chain inside a function effect. The dispatcher fires on collide (game loop tick) or click (turn-based):

```python
from portals_effects import (
    basic_interaction, trigger_on_collide, add_task_to_logic,
    effector_function
)

# Build the nested if chain
def build_step_chain(color, max_steps):
    """Generate nested if/else for step dispatch."""
    expr_parts = []
    for i in range(1, max_steps + 1):
        condition = f"$N{{{color}}} == {float(i)}"
        action = f"SetTask('{color.upper()}{i}', 'Completed', 0.0)"
        expr_parts.append((condition, action))

    # Build from inside out
    result = "0.0"
    for condition, action in reversed(expr_parts):
        result = f"if({condition},\n   {action},\n   {result}\n)"
    return result

# Wire the dispatcher
add_task_to_logic(logic[dispatcher_id], basic_interaction(
    trigger_on_collide(),
    effector_function(build_step_chain("blue", 50))
))
```

### Approach B: Direct quest completion (simpler, fewer steps)

For small boards (<20 spaces), each step can be a separate interaction on the dispatcher:

```python
from portals_effects import (
    quest_interaction, add_task_to_logic, effector_function
)

for i in range(1, num_steps + 1):
    quest_name = f"BLUE{i}"
    # Use ValueUpdated trigger — fires when the position variable hits this value
    add_task_to_logic(logic[dispatcher_id], quest_interaction(
        quest_name=quest_name,
        quest_id=generate_quest_id(),
        target_state=2,
        effector=effector_function(
            f"SetTask('{quest_name}', 'Completed', 0.0)"
        )
    ))
```

---

## Combining with Dice Rolls

A classic board game rolls a die to determine how many steps to move. Combine this recipe with the **Dice Roll** recipe (`recipes/mechanics/dice-roll.md`):

```python
# 1. Roll trigger — player clicks a "Roll" button
add_task_to_logic(logic[roll_button_id], basic_interaction(
    trigger_on_click(),
    effector_function(
        "SetVariable('lastRoll', SelectRandom(1.0,2.0,3.0,4.0,5.0,6.0), 0.0)"
    )
))

# 2. Add roll to position counter (0.1s delay)
add_task_to_logic(logic[roll_button_id], basic_interaction(
    trigger_on_click(delay=0.1),
    effector_function(
        "SetVariable('blue', $N{blue} + $N{lastRoll}, 0.0)"
    )
))

# 3. Dispatcher fires on the position variable update (see step dispatcher above)
# The dispatcher reads $N{blue} and completes the matching BLUE<N> quest
# which triggers MoveToSpot/WalkNpcToSpot on the pawn
```

### Multi-step movement after a roll

When a pawn needs to visually move through intermediate spaces (not teleport to the final position), use a **loop quest** that increments the position counter one step at a time with delays:

```python
# Roll stores the target position
add_task_to_logic(logic[roll_button_id], basic_interaction(
    trigger_on_click(),
    effector_function(
        "SetVariable('target', $N{blue} + SelectRandom(1.0,2.0,3.0,4.0,5.0,6.0), 0.0)"
    )
))

# Loop cube — on "loop" quest, advance one step if not at target
add_task_to_logic(logic[loop_cube_id], quest_interaction(
    quest_name="loop",
    quest_id=loop_quest_id,
    target_state=2,
    effector=effector_function(
        "if($N{blue} < $N{target},\n"
        "   SetVariable('blue', $N{blue} + 1.0, 0.0),\n"
        "   0.0\n"
        ")"
    )
))
```

---

## Multi-Pawn Races

For multiple pawns (e.g., 4-player horse race), create separate variable + quest sets per pawn:

| Pawn | Variable | Quest prefix | Color |
|------|----------|-------------|-------|
| Pawn 1 | `red` | `RED1`-`RED50` | Red NPC/GLB |
| Pawn 2 | `blue` | `BLUE1`-`BLUE50` | Blue NPC/GLB |
| Pawn 3 | `green` | `GREEN1`-`GREEN50` | Green NPC/GLB |
| Pawn 4 | `yellow` | `YELLOW1`-`YELLOW50` | Yellow NPC/GLB |

Each pawn gets its own dispatcher and movement quests. A shared "game tick" (loop quest or collide zone) rolls dice for all pawns simultaneously.

### Finish detection

Use a function effect to check if any pawn has reached the end:

```python
finish_expr = (
    "if($N{red} >= 50.0 && $N{redFinish} == 0.0,\n"
    "   SetVariable('redFinish', $N{nextFinish}, 0.0)"
    " + SetVariable('nextFinish', $N{nextFinish} + 1.0, 0.0),\n"
    "   0.0\n"
    ")"
    " + if($N{blue} >= 50.0 && $N{blueFinish} == 0.0,\n"
    "   SetVariable('blueFinish', $N{nextFinish}, 0.0)"
    " + SetVariable('nextFinish', $N{nextFinish} + 1.0, 0.0),\n"
    "   0.0\n"
    ")"
)
```

`nextFinish` is a shared counter starting at 1.0 — the first pawn to finish gets place 1, the second gets place 2, etc.

---

## GLB vs NPC Comparison

| Factor | GLB (MoveToSpot) | NPC (WalkNpcToSpot) |
|--------|-------------------|---------------------|
| **Performance** | Lighter — faster load, less memory | Heavier — NPC system overhead |
| **Animation** | Slides to position (or use PortalsAnimation for custom) | Plays walk animation automatically |
| **Model flexibility** | Any GLB model | Must be rigged NPC or robot default |
| **Reset** | MoveToSpot back to start (instant with `duration: 0`) | WalkNpcToSpot at high speed (15+) |
| **Recommendation** | Preferred for most board games | Use when walk animation adds value (character races, narrative) |

---

## Critical Rules

1. **Quest count scales linearly.** 50 steps per pawn x 4 pawns = 200 quests. This is within Portals limits but keep boards under ~50 steps per pawn.

2. **Shared quests for board state.** Use `shared=True` on movement quests so all players see the same board. Per-player pawns need per-player quest scoping.

3. **Dispatcher delay.** When chaining dice roll → position update → dispatcher → pawn movement, use 0.1s delays between each stage so variables settle before the next read.

4. **GLB Y position.** For GLB pawns on a flat board, keep the Y coordinate consistent across all waypoints (e.g., `0.5` for a pawn sitting on a surface at Y=0). Mismatched Y values make pawns float or sink.

5. **NPC ground offset.** NPC `endPosition` Y should be slightly above the surface (e.g., `0.05`) — the NPC model has its own height.
