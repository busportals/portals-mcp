# Compositional Patterns

The 7 core patterns that explain how Portals primitives compose into game mechanics. Every recipe is built from 1-3 of these patterns. Load this file when adapting a recipe to a new situation, inventing a mechanic not covered by existing recipes, or debugging broken game logic.

## 1. Direct Trigger → Effect

Player does X, Y happens immediately. No quest state, no conditions.

**When to use:** Simple one-shot interactions — click a button, enter a zone, collide with an object.

```python
from portals_effects import basic_interaction, trigger_on_click, effector_notification, add_task_to_logic

add_task_to_logic(logic[item_id], basic_interaction(
    trigger_on_click(),
    effector_notification("You clicked it!", "00FF00")
))
```

**Composes with:** variable-tracking (trigger → update variable), chain-reaction (trigger → cascade)

## 2. Quest-Gated Effect

Effect fires only when a quest reaches a specific state. The effect is "waiting" until the quest advances.

**When to use:** Unlocking doors after collecting keys, showing rewards after completing objectives, revealing paths after solving puzzles.

```python
from portals_effects import quest_effector, effector_show, add_task_to_logic

# Show the exit door when quest "0_collect_keys" reaches Completed (state 2)
add_task_to_logic(logic[door_id], quest_effector(
    quest_id=q["quest_id"], quest_name=q["quest_name"],
    target_state=2,  # 0=NotActive, 1=Active, 2=Completed
    effector=effector_show()
))
```

**Composes with:** quest-advancing-trigger (to advance the quest that gates this effect), state-machine (multi-step gating)

## 3. Quest-Advancing Trigger

Player action advances a quest's state. This is how players "make progress" — each action pushes a quest forward.

**When to use:** Clicking a button to start a mission, entering a zone to complete an objective, collecting an item to advance progress.

```python
from portals_effects import quest_trigger, trigger_on_enter, add_task_to_logic

# Entering the trigger zone completes quest "0_reach_exit"
add_task_to_logic(logic[trigger_id], quest_trigger(
    quest_id=q["quest_id"], quest_name=q["quest_name"],
    target_state=121,  # 111=NotActive→Active, 121=Active→Completed, 181=NotActive→Completed
    trigger=trigger_on_enter()
))
```

**Composes with:** quest-gated-effect (advance quest → something unlocks), state-machine (chaining multiple quest advances)

## 4. State Machine

Multi-step game flow using quest states: NotActive → Active → Completed. Chain multiple quests together for complex progression. Each quest is a "gate" that controls what happens next.

**When to use:** Multi-phase puzzles, story progression, unlock chains, any flow that has distinct stages.

```python
from portals_utils import create_quest_pair

# Create quest pair — returns entries (for quests dict) and IDs (for triggers/effects)
q = create_quest_pair(0, "phase_one", creator_uid)
quests.update(q["entries"])  # merge into quests dict

# Use q["quest_id"] and q["quest_name"] in quest_trigger() and quest_effector()
# Chain: completing phase_one can auto-activate phase_two via effector_run_triggers()
```

**State transitions:** `111` = NotActive→Active, `121` = Active→Completed, `181` = NotActive→Completed (skip Active)

**Composes with:** quest-advancing-trigger, quest-gated-effect, chain-reaction (to link quest phases)

## 5. Variable Tracking

Per-player numeric state via NCalc expressions and FunctionEffector. Variables persist for the session and can be displayed on HUD or leaderboard.

**When to use:** Scores, counters, health, team assignment, any per-player numeric value.

```python
from portals_effects import basic_interaction, trigger_on_enter, effector_function, effector_display_value, add_task_to_logic

# Increment score when entering a zone
add_task_to_logic(logic[zone_id], basic_interaction(
    trigger_on_enter(),
    effector_function("SetVariable('score', $N{score} + 1, 0.0)")
))

# Display variable on HUD
add_task_to_logic(logic[any_id], basic_interaction(
    trigger_player_logged_in(),
    effector_display_value(label="score", color="FFD700")
))
```

**Key NCalc functions:** `SetVariable(name, value, default)`, `$N{name}` (read numeric), `$S{name}` (read string), `SetPlayersParameters([Players], key, value)`

**Composes with:** conditional-logic (check variable before acting), direct-trigger-effect (trigger → update)

## 6. Chain Reaction

One effect triggers effects on other items, creating cascading chains. Used for scripted sequences, multi-item synchronization, and domino effects.

**When to use:** Scripted cutscenes, lighting sequences, multi-door openings, any "when X happens, A and B and C also happen."

```python
from portals_effects import quest_effector, effector_run_triggers, add_task_to_logic

# When quest completes, trigger state changes on other quests with delays
add_task_to_logic(logic[controller_id], quest_effector(
    quest_id=q["quest_id"], quest_name=q["quest_name"],
    target_state=2,
    effector=effector_run_triggers([
        {"quest_id": q2["quest_id"], "quest_name": q2["quest_name"], "target_state": 111, "delay": 0.0},
        {"quest_id": q3["quest_id"], "quest_name": q3["quest_name"], "target_state": 111, "delay": 2.0},
    ])
))
```

**Composes with:** state-machine (chain quest state changes), quest-gated-effect (each chained quest gates its own effects)

## 7. Conditional Logic

Check quest state or variable value before acting. Uses NCalc `if()` expressions in FunctionEffector.

**When to use:** One-time rewards (only if not already collected), branching paths (different action based on team), prerequisites (only allow if score >= 10).

```python
from portals_effects import basic_interaction, trigger_on_enter, effector_function, add_task_to_logic

# Only award points if quest "collect_keys" is Completed
add_task_to_logic(logic[zone_id], basic_interaction(
    trigger_on_enter(),
    effector_function("if($T{collect_keys} == 'Completed', SetVariable('score', $N{score} + 10, 0.0), 0.0)")
))
```

**Key NCalc checks:** `$T{quest_name}` returns `'NotActive'`, `'Active'`, or `'Completed'` (use quest name WITHOUT numbered prefix — `'collect_keys'` not `'0_collect_keys'`)

**Composes with:** variable-tracking (check variable before acting), state-machine (check quest state before acting)

---

## Common Game Type Compositions

When a user names a game type, use these search terms to grep `recipes/manifest.md`:

| Game Type | Search Terms |
|-----------|-------------|
| Capture the Flag | team, capture, score, respawn, flag |
| Escape Room | gate, lock, collect, timer, sequence, puzzle |
| Platformer | checkpoint, hazard, timer, collect, jump, platform |
| Scavenger Hunt | collect, npc, gate, quest, hidden, find |
| PvP Arena | team, respawn, score, hazard, weapon, damage |
| Wave Survival | round, wave, respawn, hazard, spawn, enemy |
| Race / Obstacle Course | checkpoint, timer, teleport, speed, course |
| Board Game | pawn, dice, roll, board, move, step, waypoint, turn |
| RPG / Quest Game | npc, gate, score, quest, dialogue, inventory |
| Puzzle Room | gate, sequence, lock, collect, trigger, puzzle |
| Tour / Exhibit | npc, dialogue, teleport, sequence, waypoint |
