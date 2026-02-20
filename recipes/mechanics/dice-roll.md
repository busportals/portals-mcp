---
name: Dice Roll
category: mechanics
tags: [dice, random, roll, chance, rng, select, board game, turn]
patterns: [variable-tracking, direct-trigger-effect]
summary: Random number generation using SelectRandom in function effects, with variable storage and display
---

# Dice Roll

Generate random outcomes using `SelectRandom()` inside a function effect. The result is stored in a variable for other systems to read.

## Basic Roll (1-6)

### Items needed

- **Roll trigger** (any item — button click, collide zone, quest-driven)

### Wiring pattern

```python
from portals_effects import (
    basic_interaction, trigger_on_click, add_task_to_logic,
    effector_function, effector_display_value, effector_notification
)

# Roll a d6 — store result in "roll" variable
add_task_to_logic(logic[button_id], basic_interaction(
    trigger_on_click(),
    effector_function(
        "SetVariable('roll', SelectRandom(1.0, 2.0, 3.0, 4.0, 5.0, 6.0), 0.0)"
    )
))

# Display the result (0.1s delay — value must settle first)
add_task_to_logic(logic[button_id], basic_interaction(
    trigger_on_click(delay=0.1),
    effector_display_value(label="roll", color="F7E808")
))

# Optional: show a notification with the roll result
add_task_to_logic(logic[button_id], basic_interaction(
    trigger_on_click(delay=0.1),
    effector_notification(text="You rolled |roll|!", color="F7E808")
))
```

### Delay rule

`DisplayValueEvent` and `NotificationPillEvent` with pipe syntax must fire **at least 0.1s after** the `FunctionEffector` that sets the variable. Otherwise the display reads the stale value.

---

## Custom Dice

Change the `SelectRandom` arguments to create any die:

```python
# d4
"SetVariable('roll', SelectRandom(1.0, 2.0, 3.0, 4.0), 0.0)"

# d20
"SetVariable('roll', SelectRandom(1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,17.0,18.0,19.0,20.0), 0.0)"

# Weighted roll (double chance of 6)
"SetVariable('roll', SelectRandom(1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.0), 0.0)"

# Coin flip
"SetVariable('flip', SelectRandom(1.0, 2.0), 0.0)"
```

---

## Roll + Accumulate

Roll a die and add the result to a running total (e.g., board game movement points):

```python
# Roll and add to position counter in one expression
add_task_to_logic(logic[button_id], basic_interaction(
    trigger_on_click(),
    effector_function(
        "SetVariable('lastRoll', SelectRandom(1.0,2.0,3.0,4.0,5.0,6.0), 0.0)"
        " + SetVariable('position', $N{position} + SelectRandom(1.0,2.0,3.0,4.0,5.0,6.0), 0.0)"
    )
))
```

**Important:** Each `SelectRandom` call generates an **independent** random value. In the expression above, `lastRoll` and the amount added to `position` will be **different** random numbers. If you need the same roll applied to both, use a two-step approach:

```python
# Step 1: Roll the die
add_task_to_logic(logic[button_id], basic_interaction(
    trigger_on_click(),
    effector_function(
        "SetVariable('lastRoll', SelectRandom(1.0,2.0,3.0,4.0,5.0,6.0), 0.0)"
    )
))

# Step 2: Add the stored roll to position (0.1s delay)
add_task_to_logic(logic[button_id], basic_interaction(
    trigger_on_click(delay=0.1),
    effector_function(
        "SetVariable('position', $N{position} + $N{lastRoll}, 0.0)"
    )
))
```

---

## Critical Rules

1. **SelectRandom returns a float.** Values are always numeric (1.0, not 1). Use float comparisons downstream.

2. **Each SelectRandom call is independent.** Two calls in the same expression produce different results. Store the roll in a variable first if you need to reuse it.

3. **Shared vs per-player.** `SetVariable('name', value, 0.0)` with third arg `0.0` is a **shared** (network) variable — all players see the same roll. For per-player rolls, the variable must be per-player scoped (use score labels via `UpdateScoreEvent` instead).

4. **Delay chaining.** If the roll feeds into quest completion or movement, chain with 0.1s delays so each step sees the updated value.
