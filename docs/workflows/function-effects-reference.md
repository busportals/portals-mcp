# Function Effects & NCalc Reference

> **Context loading:** Read this doc when implementing game logic with variables, conditionals, timers, or multiplayer state.

Use FunctionEffector expressions when the game design requires any of the following:
- **Gating progress** -- "only unlock X when Y and Z are done", "need 10 coins to open the shop"
- **Tracking/modifying values** -- scores, coins, health, counters, cooldowns
- **Decisions based on state** -- "NPC says different things depending on quest progress"
- **Randomness** -- random rewards, coin flips, random enemy spawns
- **Timers as logic** -- "check how long the player took", "bonus if under 30 seconds"
- **Multiplayer coordination** -- assigning teams/roles, shared scores, filtering players by state
- **Chained consequences** -- "when this completes, start that after a delay"

FunctionEffector uses NCalc expressions. All numeric values MUST use decimals (`0.0` not `0`). Strings use single quotes (`'Active'` not `"Active"`).

## Reading Values

| Syntax | Returns | Example |
|--------|---------|---------|
| `$T{name}` | `'NotActive'` / `'Active'` / `'Completed'` | `$T{door} == 'Active'` |
| `$TN{name}` | `0` / `1` / `2` | `$TN{door} == 1.0` |
| `$N{name}` | Number (variable value) | `$N{coins} >= 10.0` |
| `$N{timerName}` | Number (elapsed seconds) | `$N{RaceTimer} >= 60.0` |

## Operators

**Math:** `+` `-` `*` `/` `%` (mod) `**` (power)
**Compare:** `==` `!=` `>` `<` `>=` `<=`
**Logic:** `&&` (and) `||` (or) `!` (not)

Group with parentheses: `($N{coins} >= 10.0) && ($T{quest} == 'Active')`

## Control Flow

### if(condition, whenTrue, whenFalse)

```
if($N{coins} >= 10.0,
   SetTask('shop', 'Active', 0.0),
   0.0
)
```

Nested (else-if):
```
if($T{quest} == 'NotActive',
   SetTask('offer', 'Active', 0.0),
   if($T{quest} == 'Active',
      SetTask('reminder', 'Active', 0.0),
      SetTask('done', 'Active', 0.0)
   )
)
```

### ifs(cond1, val1, cond2, val2, ..., default)

```
ifs(
  $T{step} == 'NotActive', SetVariable('hint', 0.0, 0.0),
  $T{step} == 'Active',    SetVariable('hint', 1.0, 0.0),
                            SetVariable('hint', 2.0, 0.0)
)
```

Last entry (no condition) is the default.

## Portals Functions

### SetTask(taskName, state, delay)
```
SetTask('alarm', 'Active', 0.0)
SetTask('alarm', 'NotActive', 5.0)   // reset after 5s
```
States: `'NotActive'`, `'Active'`, `'Completed'`

### SetVariable(varName, value, delay)
```
SetVariable('coins', 0.0, 0.0)                  // set to 0
SetVariable('coins', $N{coins} + 10.0, 0.0)     // add 10
SetVariable('health', Max($N{health} - 1.0, 0.0), 0.0)  // subtract, floor at 0
```

### SelectRandom(item1, item2, ...)
```
SetVariable('reward', SelectRandom(5.0, 10.0, 25.0, 50.0), 0.0)
SelectRandom(true, false)   // coin flip
```

### OnChange(taskName, targetState)
Fires only at the moment of transition, not on every evaluation.
```
if(OnChange('puzzle1', 'Completed'),
   SetVariable('doorOpen', 1.0, 0.0),
   0.0
)
```

Combine multiple:
```
(OnChange('task1', 'Active') || OnChange('task2', 'Completed'))
&& $T{task1} == 'Active' && $T{task2} == 'Completed'
```

## Math Functions

| Function | Example | Result |
|----------|---------|--------|
| `Min(a, b)` | `Min($N{coins}, 999.0)` | Cap at 999 |
| `Max(a, b)` | `Max($N{health}, 0.0)` | Floor at 0 |
| `Round(n)` | `Round(3.6)` | 4 |
| `Floor(n)` | `Floor(3.9)` | 3 |
| `Ceiling(n)` | `Ceiling(3.1)` | 4 |
| `Abs(n)` | `Abs(-5.0)` | 5 |
| `Sqrt(n)` | `Sqrt(9.0)` | 3 |

Clamp pattern: `Min(Max($N{health}, 0.0), 100.0)`

## Multiplayer Functions

### Player Lists
- `[Players]` -- all players in room (literal syntax, brackets required)
- Chain with `+`: later operations override earlier ones

### Functions

```
AssignNumbersInOrder([Players], 'playerNum')        // sequential 1,2,3...
SelectRandomPlayers([Players], 2)                    // pick 2 random players
SelectPlayers([Players], 'team', 'red')              // filter by param value
SelectPlayersParameters([Players], 'health')         // get param from all players
SetPlayersParameters([Players], 'canMove', true)     // set param on all players
CountArray(SelectPlayers([Players], 'alive', 'true'))  // count matching
PrintString(value)                                   // debug to browser console
```

### UpdateMultiplayerNumericVariable(varName, value, opType, delay)

| opType | Operation |
|--------|-----------|
| `0.0` | Set |
| `1.0` | Add |
| `2.0` | Subtract |
| `3.0` | Multiply |
| `4.0` | Divide |

```
UpdateMultiplayerNumericVariable('score', 10.0, 1.0, 0.0)  // add 10
```

### Common Multiplayer Patterns

Team split:
```
SetPlayersParameters([Players], 'team', 'blue')
+ SetPlayersParameters(SelectRandomPlayers([Players], Floor($N{PlayerCount} / 2.0)), 'team', 'red')
```

Impostor assignment:
```
SetPlayersParameters([Players], 'impostor', false)
+ SetPlayersParameters(SelectRandomPlayers([Players], 2), 'impostor', true)
```

## UI Toggles

| Toggle | Effect |
|--------|--------|
| **Trigger on Tasks Change** | Auto-evaluates when any referenced task/variable changes |
| **Activate on Start** | Evaluates once on player login |

## Displaying Variables in Text

Use pipe syntax `|variableName|` to show a variable's live value inline in text. The value updates automatically when the variable changes.

**Works in:**
- **WorldText** `text` field — `"Score: |coins|"`
- **NotificationPillEvent** `nt` field — `"You earned |reward| points!"`

**Example — score display with WorldText:**
```python
# Create a text item showing live score
score_display = create_text(
    pos=(0, 3, 0),
    content="<color=#FFD700>Score: |coins|</color>",
    billboard=True
)
```

**Example — notification with variable:**
```python
task = basic_interaction(
    trigger_on_click(),
    effector_notification("You have |coins| coins!", "00FF00")
)
```

Variables referenced by pipe syntax must be set via `SetVariable()`, `UpdateScoreEvent`, or `UpdateMultiplayerNumericVariable()`.

---

## Critical Rules

1. **Always decimals** -- `0.0` not `0`, `1.0` not `1`. Integers cause cast errors.
2. **Single quotes for strings** -- `'Active'` not `"Active"`
3. **Task names omit the numbered prefix** -- Quest `Name` fields use `0_redteam`, but in NCalc expressions use just `'redteam'` (no `0_` prefix). This applies to `SetTask()`, `$T{}`, `$TN{}`, and `OnChange()`.
4. **Unstarted timers return 0** -- must use Start Timer effect first
5. **Tasks persist by default** -- use "Non-Persistent" setting to reset on reload
6. **`$T{}` preferred over `$TN{}`** -- more readable, same performance
7. **`+` chains multiplayer ops** -- order matters, later overrides earlier
8. **OnChange is edge-triggered** -- fires once at transition, not continuously
