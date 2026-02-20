---
name: Leaderboard & Scoring
category: scoring
tags: [leaderboard, score, points, timer, value, update, display, ranking]
patterns: [direct-trigger-effect, variable-tracking]
summary: Points-based and time-based scoring with leaderboard display, including reset and timer invalidation patterns
---

# Leaderboard & Scoring

Two scoring modes: **points** (numeric values) and **time** (timers). Each uses different effects and different leaderboard wiring.

## Points-Based Scoring

The core loop: update the value → display it → post to leaderboard. **Display and post must fire with a 0.1s delay after the update** to avoid runtime errors.

### Items needed

- **Scoring trigger** (any item with a trigger — click, enter, collect, etc.)
- **Leaderboard** (prefabName: `"Leaderboard"`) with **`tb: false` (required for points)**

### Leaderboard extraData

```python
leaderboard_logic = {
    "gn": "Game Name",       # displayed on the leaderboard
    "ln": "Points",           # MUST match the variable name used in UpdateScoreEvent
    "tb": False,              # REQUIRED for points — default is time-based when omitted
    "ci": "",                 # leave empty for standard tracking
    "Tasks": [],
    "ViewNodes": []
}
```

### Wiring pattern

```python
from portals_effects import (
    basic_interaction, trigger_on_click, add_task_to_logic,
    effector_update_value, effector_display_value, effector_post_score
)

# 1. Update the value (fires immediately — no delay)
add_task_to_logic(logic[item_id], basic_interaction(
    trigger_on_click(),
    effector_update_value(label="Points", op=1, change=1.0)  # op=1 add
))

# 2. Display the value on HUD (0.1s delay)
add_task_to_logic(logic[item_id], basic_interaction(
    trigger_on_click(delay=0.1),
    effector_display_value(label="Points", color="26D710")
))

# 3. Post to leaderboard (0.1s delay)
add_task_to_logic(logic[item_id], basic_interaction(
    trigger_on_click(delay=0.1),
    effector_post_score(label="Points")
))
```

### UpdateScoreEvent operations

| `op` value | Operation | Example |
|------------|-----------|---------|
| **omit** | **Set** — sets variable to `scoreChange` | `effector_update_value(label="Points", change=0.0)` — resets to 0 |
| `1` | **Add** | `effector_update_value(label="Points", op=1, change=1.0)` |
| `2` | **Subtract** | `effector_update_value(label="Points", op=2, change=5.0)` |
| `3` | **Multiply** | `effector_update_value(label="Points", op=3, change=2.0)` |
| `4` | **Divide** | `effector_update_value(label="Points", op=4, change=2.0)` |

To **set** a value (e.g. reset to 0), omit the `op` field entirely. Pass `op=None` in the Python helper:

```python
effector_update_value(label="Points", op=None, change=0.0)  # sets Points to 0
```

### Reset pattern

A separate item (e.g. a "reset" button) that sets the value back to 0:

```python
add_task_to_logic(logic[reset_id], basic_interaction(
    trigger_on_click(),
    effector_update_value(label="Points", op=None, change=0.0)  # set to 0
))
```

---

## Time-Based Scoring

Uses timer effects instead of UpdateScoreEvent. **No PostScoreToLeaderboard needed** — `StopTimerEffect` automatically records the time to the leaderboard.

### Items needed

- **Start zone** (Trigger) — starts the timer when player enters
- **End zone** (Trigger) — stops the timer and records the time
- **Cancel zone** (Trigger, optional) — invalidates the run (death, out of bounds)
- **Leaderboard** (prefabName: `"Leaderboard"`) — `tb` can be omitted (defaults to time-based)

### Leaderboard extraData

```python
leaderboard_logic = {
    "gn": "Game Name",       # displayed on the leaderboard
    "ln": "Time",             # MUST match the timer name (tn) in Start/Stop/Cancel effects
                              # tb omitted — defaults to time-based, which is what we want here
    "ci": "",                 # leave empty for standard tracking
    "Tasks": [],
    "ViewNodes": []
}
```

### Wiring pattern

```python
from portals_effects import (
    basic_interaction, trigger_on_enter, add_task_to_logic,
    effector_start_timer, effector_stop_timer, effector_cancel_timer
)

# Start zone — begin timing
add_task_to_logic(logic[start_trigger_id], basic_interaction(
    trigger_on_enter(),
    effector_start_timer(timer_name="Time")
))

# End zone — stop timer and record to leaderboard
add_task_to_logic(logic[end_trigger_id], basic_interaction(
    trigger_on_enter(),
    effector_stop_timer(timer_name="Time")
))

# Cancel zone — invalidate the run (optional, e.g. death/out of bounds)
add_task_to_logic(logic[cancel_trigger_id], basic_interaction(
    trigger_on_enter(),
    effector_cancel_timer(timer_name="Time")
))
```

### Timer behavior

| Effect | What happens | Records to leaderboard? |
|--------|-------------|------------------------|
| `StartTimerEffect` | Starts counting up from 0 | No |
| `StopTimerEffect` | Stops the timer | **Yes** — time is automatically sent to matching leaderboard |
| `CancelTimerEffect` | Cancels without recording | **No** — use for death, falling off map, leaving area |

### Timer UI

`StartTimerEffect` accepts an optional `showTimerUI` field:
- `true` (or omit) — shows a visible timer on screen
- `false` — timer runs invisibly (useful for hidden time limits)

---

## Run Lifecycle

### Failed run (death, out of bounds, timeout)

On failure, clean up scoring state and return the player to try again:

```python
from portals_effects import (
    basic_interaction, trigger_on_enter, add_task_to_logic,
    effector_cancel_timer, effector_update_value, effector_teleport
)

# Hazard zone / death trigger — cancel timer + reset points + respawn
# For time-based games:
add_task_to_logic(logic[hazard_id], basic_interaction(
    trigger_on_enter(),
    effector_cancel_timer(timer_name="Time")
))

# For points-based games:
add_task_to_logic(logic[hazard_id], basic_interaction(
    trigger_on_enter(),
    effector_update_value(label="Points", op=None, change=0.0)  # set to 0
))

# Respawn player to start or last checkpoint
add_task_to_logic(logic[hazard_id], basic_interaction(
    trigger_on_enter(),
    effector_teleport(room_id="", spawn_name="start", spawn_radius=0.0)
))
```

- **Always cancel timers** on failure — otherwise a stale timer keeps running into the next attempt
- **Always reset points to 0** on failure — otherwise the previous attempt's score carries over
- **Teleport to start or checkpoint** — use `spawn_name` to target a specific SpawnPoint

### Successful run

On success, the order matters: **post the final score first, then reset**.

**Points-based** — post score, then reset to 0 with a delay:

```python
# End zone — post final score, then reset
# 1. Post to leaderboard (immediate)
add_task_to_logic(logic[end_trigger_id], basic_interaction(
    trigger_on_enter(),
    effector_post_score(label="Points")
))

# 2. Reset points to 0 (0.1s delay — AFTER post completes)
add_task_to_logic(logic[end_trigger_id], basic_interaction(
    trigger_on_enter(delay=0.1),
    effector_update_value(label="Points", op=None, change=0.0)
))
```

**Time-based** — just stop the timer, no reset needed:

```python
# End zone — stop timer records automatically
add_task_to_logic(logic[end_trigger_id], basic_interaction(
    trigger_on_enter(),
    effector_stop_timer(timer_name="Time")
))
# No reset needed — starting a new timer overwrites the previous one
```

---

## Critical Rules

1. **Delay rule**: `DisplayValueEvent` and `PostScoreToLeaderboard` must fire with at least 0.1s delay after `UpdateScoreEvent` on the same trigger. Otherwise you get runtime errors because the value hasn't updated yet.

2. **PostScoreToLeaderboard is only for numeric values**. Never use it for timers. Timer values are recorded automatically by `StopTimerEffect`.

3. **Timer name matching**: The `tn` field in Start/Stop/Cancel must exactly match the `ln` field on the leaderboard. A mismatch means the leaderboard shows nothing.

4. **Variable name matching**: The `label` field in `UpdateScoreEvent`, `DisplayValueEvent`, and `PostScoreToLeaderboard` must all match the leaderboard's `ln` field exactly.

5. **CancelTimer does not fire OnTimerStopped**. If you have logic wired to `OnTimerStopped`, it won't trigger on cancel — only on stop. Use this distinction to separate "completed run" from "failed run".
