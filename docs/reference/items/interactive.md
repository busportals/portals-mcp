# Interactive Items

NPCs and interactive characters.

## NPC (GLBNPC)

Interactive non-player character with dialogue and AI. Uses `prefabName: "GLBNPC"`. NPCs sit on the ground at `y=0` (not `y=0.5` like cubes).

**Base structure:**
```json
{
  "prefabName": "GLBNPC",
  "pos": {"x": 0, "y": 0, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "https://example.com/avatar.glb",
  "extraData": "{\"n\":\"Guard\",\"a\":\"Salute\",\"p\":\"You are a palace guard. Be stern but helpful.\",\"bq\":true,\"swn\":true,\"events\":[],\"tags\":[],\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**NPC avatar (contentString):**

The `contentString` holds the GLB model URL. Two types are supported:

| GLB Type | URL Format |
|----------|------------|
| **Rigged** (has skeleton/animations) | Use the straight GLB URL |
| **Non-rigged** (static model) | Append `?nonrigged=true` to the GLB URL |

**extraData fields:**
- `n`: NPC display name. Can be any string.
- `a`: Default animation. Empty string `""` for idle. See permitted animations table below.
- `p`: AI personality prompt. When set, the NPC assumes this personality and players can chat with it via messages. Can be any descriptive text.
- `bq`: `true` to enable.
- `swn`: Show when near / auto popup. `true` = NPC dialogue appears automatically when player approaches. Omit for manual interaction.
- `events`: Array of events. Usually `[]`.
- `tags`: Array of tags. Usually `[]`.

**Permitted animations (shared with `PlayerEmote` and `NpcAnimation`):**

| Animation Name |
|---------------|
| `Sitting` |
| `Can Can` |
| `Wave` |
| `Salute` |
| `Jive` |
| `Salsa` |
| `Shuffling` |
| `Chicken` |
| `Slide n Jive` |
| `Robot` |

This is the same animation list used by the `PlayerEmote` effect and the `NpcAnimation` effect. Use an empty string `""` for the default idle animation.

### Available Robot NPC Models

Built-in robot avatar models for GLBNPC. All are rigged with walk/idle/talk animations. Default scale is 1.0.

| Model | contentString URL |
|-------|-------------------|
| **Robot Orange** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FRobot_NPC_Default_Orange.glb?alt=media&token=e119cef4-bdbb-481d-9504-6cdbbf2e1df0` |
| **Robot Yellow** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FRobot_NPC_Default_Yellow.glb?alt=media&token=24142b58-2c9e-4b1f-b26e-edbb4eadb3c6` |
| **Robot Red** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FRobot_NPC_Default_Red.glb?alt=media&token=c261ac38-8c60-43d0-8c98-a6dc77e64b9a` |
| **Robot Navy** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FRobot_NPC_Default_Navy.glb?alt=media&token=3122756b-55ea-41f9-ba67-ef889bfa7d30` |
| **Robot Purple** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FRobot_NPC_Default_Purple.glb?alt=media&token=ba9a5bf0-c20b-4483-86b1-1633e3ae64c6` |
| **Robot Green** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FRobot_NPC_Default_Green.glb?alt=media&token=5a9925e8-4c65-482f-b577-5c68892d8d59` |

**URL shorthand:** Portals also supports a `~` prefix as shorthand for the Firebase storage base URL. For example, `~Robot_NPC_Default_Orange.glb?alt=media&token=...` resolves to the full URL above. Both formats work in `contentString`.

**Scaling with FixedSize:** To scale a robot NPC larger, append `&FixedSize=<float>&overrideSize=true` to the URL and set the item's `scale` to match. For example, scale 2.85: `...&FixedSize=2.854788&overrideSize=true` with `scale: {x: 2.85, y: 2.85, z: 2.85}`.

### NPC-Specific Effects

These effects only work on GLBNPC items. They control NPC behavior — animation, movement, facing, and speaking.

#### `NpcAnimation`

Plays a named animation on the NPC. Uses the same restricted animation list as the `PlayerEmote` effect and the NPC `a` extraData field (see table above).

```json
{"$type": "NpcAnimation", "animationName": "Sitting"}
```

| Field | Type | Description |
|-------|------|-------------|
| `animationName` | string | Animation to play. See permitted animations table above. |

#### `NpcCopyPlayerPath`

Makes the NPC walk along a recorded path of positions and rotations with matching animator parameters. The path is typically recorded from a player's movement in the editor.

```json
{
  "$type": "NpcCopyPlayerPath",
  "positions": [[x, y, z], [x, y, z], ...],
  "rotations": [[qx, qy, qz, qw], [qx, qy, qz, qw], ...],
  "animatorParameterDatas": [
    {"g": true, "d": "0.0", "a": "0.0", "v": "-4.0", "i": "0.0", "o": "0.0", "m": "0.0", "r": "0.0"},
    ...
  ],
  "shouldLoop": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `positions` | array of [x,y,z] | Waypoint positions along the path |
| `rotations` | array of [qx,qy,qz,qw] | Quaternion rotations at each waypoint |
| `animatorParameterDatas` | array of objects | Animator state at each waypoint. Keys: `g` (grounded), `d` (direction), `a` (angle), `v` (vertical velocity), `i` (input magnitude), `o` (output speed), `m` (movement speed), `r` (rotation speed). Optional `s` (sprinting). |
| `shouldLoop` | bool | `true` = NPC loops the path continuously. Default `false`. |

All three arrays must have the same length. Each index represents one frame/waypoint of the path.

#### `NpcCopyPlayerPathStop`

Stops the NPC from following its current path.

```json
{"$type": "NpcCopyPlayerPathStop"}
```

| Field | Type | Description |
|-------|------|-------------|
| `RP` | bool | Optional. `true` = reset the NPC to its original position after stopping. |

#### `TurnToPlayer`

Makes the NPC turn to face the player who activated the effect.

```json
{"$type": "TurnToPlayer"}
```

No parameters.

#### `WalkNpcToSpot`

Walks the NPC to a target position at a given speed, playing a walk animation.

```json
{"$type": "WalkNpcToSpot", "walkSpeed": 3.0, "endPosition": [0, 0, 10], "endRotation": [0, 0, 0, 1]}
```

| Field | Type | Description |
|-------|------|-------------|
| `walkSpeed` | float | Movement speed in units/sec |
| `endPosition` | [x,y,z] | Target world position |
| `endRotation` | [qx,qy,qz,qw] | Final rotation after arriving |

#### `StartSpeaking`

Starts the NPC's talking animation. Does not trigger AI conversation — purely visual.

```json
{"$type": "StartSpeaking"}
```

No parameters.

#### `StopSpeaking`

Stops the NPC's talking animation.

```json
{"$type": "StopSpeaking"}
```

No parameters.

#### Common NPC Effect Patterns

**NPC patrol loop (walk path that repeats):**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnPlayerLoggedIn"},
  "DirectEffector": {
    "Effector": {
      "$type": "NpcCopyPlayerPath",
      "positions": [[0, 0, 0], [5, 0, 0], [5, 0, 5], [0, 0, 5]],
      "rotations": [[0, 0, 0, 1], [0, 0.707, 0, 0.707], [0, 1, 0, 0], [0, -0.707, 0, 0.707]],
      "animatorParameterDatas": [
        {"g": true, "d": "0.0", "a": "0.0", "v": "-4.0", "i": "0.0", "o": "1.0", "m": "1.5", "r": "0.0"},
        {"g": true, "d": "0.0", "a": "0.0", "v": "-4.0", "i": "0.0", "o": "1.0", "m": "1.5", "r": "0.0"},
        {"g": true, "d": "0.0", "a": "0.0", "v": "-4.0", "i": "0.0", "o": "1.0", "m": "1.5", "r": "0.0"},
        {"g": true, "d": "0.0", "a": "0.0", "v": "-4.0", "i": "0.0", "o": "1.0", "m": "1.5", "r": "0.0"}
      ],
      "shouldLoop": true
    },
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

**NPC greets player (turn + speak animation):**
```json
[
  {
    "$type": "TaskTriggerSubscription",
    "Trigger": {"$type": "OnEnterEvent"},
    "DirectEffector": {
      "Effector": {"$type": "TurnToPlayer"},
      "Id": "unique-uuid", "TargetState": 2, "Name": ""
    },
    "Id": "unique-uuid", "TargetState": 2, "Name": ""
  },
  {
    "$type": "TaskTriggerSubscription",
    "Trigger": {"$type": "OnEnterEvent"},
    "DirectEffector": {
      "Effector": {"$type": "StartSpeaking"},
      "Id": "unique-uuid", "TargetState": 2, "Name": ""
    },
    "Id": "unique-uuid", "TargetState": 2, "Name": ""
  }
]
```

---

## Combat NPC (EnemyNPC)

AI-controlled enemy that chases and attacks players. Uses `prefabName: "EnemyNPC"`. Combat NPCs **require a nav mesh surface** to function — they must be placed as children of a ResizableCube or 9Cube that has `"nav": true` in its logic. Without a nav mesh parent, the NPC cannot pathfind and will not work.

**Base structure:**
```json
{
  "prefabName": "EnemyNPC",
  "parentItemID": 100,
  "pos": {"x": 3.6, "y": 0.09, "z": 1.9},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1.41, "y": 1.41, "z": 1.41},
  "contentString": "https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FSkeleton%20Plain_Skeleton_Plain.glb?alt=media&token=e822b470-5305-4348-905f-dc6b380bf961&FixedSize=1.411088&overrideSize=true",
  "modelsize": {"x": 0, "y": 0, "z": 0},
  "modelCenter": {"x": 0, "y": 0, "z": 0},
  "interactivityType": 0,
  "interactivityURL": "",
  "hoverTitle": "",
  "hoverBodyContent": "",
  "ImageInteractivityDetails": {"buttonText": "", "buttonURL": ""},
  "sessionData": "",
  "instanceId": "",
  "placed": true,
  "locked": false,
  "superLocked": false
}
```

### contentString (NPC Model)

The `contentString` holds the GLB model URL. Combat NPC models must be rigged (have a skeleton with animations). The URL supports two sizing parameters:

| URL Parameter | Description |
|---------------|-------------|
| `FixedSize=<float>` | Sets the NPC's visual size. This is the **primary** sizing control. Must match the item's `scale` values. |
| `overrideSize=true` | **Required** for any NPC with `FixedSize` greater than 1.6. Always include when using `FixedSize`. |

Example URL with sizing:
```
https://example.com/skeleton.glb?alt=media&token=abc&FixedSize=1.411088&overrideSize=true
```

### Nav Mesh Requirement

Combat NPCs must be children of a surface with `"nav": true`. Two item types support nav mesh:

- **ResizableCube**: Set `"nav": true` in logic. The cube becomes an AI-walkable surface.
- **9Cube** (Elemental Cube): Set `"nav": true` in logic. Same behavior.

Set the EnemyNPC's `parentItemID` to the nav mesh item's ID. The NPC's `pos` is then local to the parent.

### Logic Fields

The logic entry for an EnemyNPC contains combat stats, weapon configuration, and behavior flags.

**Combat stats:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `health` | int | `40` | Hit points before the NPC dies |
| `damage` | int | `10` | Damage dealt per attack |
| `healthRecovery` | int | `0` | HP recovered per second during health recovery |
| `recoveryDelay` | int | `0` | Seconds without taking damage before health recovery begins |
| `detectDistance` | float | `5.0` | Range at which the NPC detects and chases a player |
| `attackDistance` | float | `1.0` | Range at which the NPC can attack |
| `loseTarget` | float | `7.0` | Distance at which the NPC stops chasing and returns |
| `fov` | int | `330` | Field of view in degrees for player detection |
| `minTimeAttack` | float | `0.5` | Minimum time between attacks (seconds) |
| `maxTimeAttack` | float | `2.0` | Maximum time between attacks (seconds) |
| `attackSpeed` | float | `1.0` | Attack animation speed multiplier |
| `swingSpeed` | float | `1.0` | Swing/attack animation speed multiplier |
| `maxAttacks` | int | `1` | Maximum attacks per combo |
| `rollChance` | float | `0.0` | Chance for NPC to dodge-roll (0.0 = never) |
| `detectState` | int | `0` | Idle behavior: `0` = idle (stands still until detecting a player), `1` = wander (roams around when no player detected) |
| `speedMultiplier` | float | `1.0` | Movement speed multiplier. Higher = faster NPC |
| `reviveAfterDeath` | bool | `false` | Whether the NPC auto-revives after dying |
| `hideHealthBar` | bool | `false` | Hide the health bar above the NPC |

**Weapon configuration:**

| Field | Type | Description |
|-------|------|-------------|
| `weapon` | string | CDN URL of the weapon GLB model. Empty string `""` for unarmed. |
| `point` | object | Weapon attachment point on the NPC's hand. Contains `position`, `rotation` (quaternion), `scale` arrays and `duration`. |

**Weapon point example (Stone Axe):**
```json
{
  "point": {
    "position": [0.03, 0.18, 0.11],
    "rotation": [0.019, -0.009, 0.906, -0.423],
    "scale": [1.0, 1.0, 1.0],
    "duration": 3.0
  }
}
```

Each weapon model requires different attachment point values to sit correctly in the NPC's hand. See the weapon catalog below for tested values.

**Behavior flags:**

| Field | Type | Observed | Description |
|-------|------|----------|-------------|
| `s` | bool | `true` | Shadows |
| `l` | bool | `false` | (pending documentation) |
| `c` | bool | `true` | Collider |
| `gi` | string | `""` | (pending documentation) |
| `f` | bool | `false` | (pending documentation) |
| `r` | bool | `false` | (pending documentation) |

### Combat NPC Triggers & Effects

All triggers and effects below are specific to EnemyNPC items.

#### Triggers

**`OnEnemyDied`** — Fires when this NPC is killed.

```json
{
  "$type": "OnEnemyDied",
  "RTime": 0.0,
  "Delay": 0.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `RTime` | float | Respawn timer — seconds before the NPC can respawn after death |
| `Delay` | float | Delay before the trigger fires after death |

**`OnTakeDamageTrigger`** — Fires when this NPC takes damage from any source.

```json
{"$type": "OnTakeDamageTrigger"}
```

No parameters. Useful for reactive behaviors — e.g., forcing an idle NPC to attack when hit, spawning reinforcements, or triggering visual effects on damage.

#### Effects

**`ReviveEnemy`** — Revives a dead EnemyNPC. Restores full health and returns it to its original position. No parameters.

```json
{"$type": "ReviveEnemy"}
```

**`ResetEnemy`** — Respawns the enemy with fresh health at its original position. No parameters.

```json
{"$type": "ResetEnemy"}
```

**`AttackPlayer`** — Forces the NPC to immediately attack the nearest player, regardless of detection range or FOV. No parameters.

```json
{"$type": "AttackPlayer"}
```

**`ChangeEnemyHealth`** — Modifies the NPC's health.

```json
{"$type": "ChangeEnemyHealth", "op": 1, "healthChange": 1}
```

| Field | Type | Description |
|-------|------|-------------|
| `op` | int | Operation: `1` = add, `2` = subtract |
| `healthChange` | int | Amount of health to add or subtract |

**`DuplicateEnemy`** — Spawns copies of this NPC at a named SpawnPoint.

```json
{"$type": "DuplicateEnemy", "spawnName": "EnemySpawn1", "count": 2, "randomRadius": 2.0}
```

| Field | Type | Description |
|-------|------|-------------|
| `spawnName` | string | Name of the SpawnPoint where clones appear. Must match a SpawnPoint's `n` field exactly. |
| `count` | int | Number of copies to spawn |
| `randomRadius` | float | Random offset radius around the spawn point (meters). Prevents all clones stacking on the same spot. |

Place a named SpawnPoint in the room (set its `n` field), then reference that name in `spawnName`. Useful for creating enemy swarms — e.g., duplicate more enemies each round.

#### Common Patterns

**Respawn on quest completion:**
```json
{
  "$type": "TaskEffectorSubscription",
  "Effector": {"$type": "ReviveEnemy"},
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": "quest-name",
  "TaskTriggerId": "quest-id"
}
```

**On-death loot drop (random):**

Use `OnEnemyDied` with `OtherRandomTasksEmpty` to randomly pick one quest to advance from a set of options:

```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnEnemyDied", "RTime": 0.0, "Delay": 0.0},
  "OtherRandomTasksEmpty": [
    {
      "Id": "uuid-1",
      "TargetState": 181,
      "Name": "1_drop_rare_loot",
      "TaskTriggerId": "quest-id-1"
    },
    {
      "Id": "uuid-2",
      "TargetState": 181,
      "Name": "2_drop_common_loot",
      "TaskTriggerId": "quest-id-2"
    }
  ],
  "Id": "uuid-main",
  "TargetState": 181,
  "Name": "0_drop_default_loot",
  "TaskTriggerId": "quest-id-0"
}
```

The main task fires by default. If `OtherRandomTasksEmpty` entries are present, one is randomly selected instead.

**Reactive aggro — idle NPC attacks when hit:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnTakeDamageTrigger"},
  "DirectEffector": {
    "Effector": {"$type": "AttackPlayer"},
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

**Spawn reinforcements on damage:**
```json
{
  "$type": "TaskTriggerSubscription",
  "Trigger": {"$type": "OnTakeDamageTrigger"},
  "DirectEffector": {
    "Effector": {"$type": "DuplicateEnemy", "spawnName": "ReinforcementSpawn", "count": 2, "randomRadius": 3.0},
    "Id": "unique-uuid",
    "TargetState": 2,
    "Name": ""
  },
  "Id": "unique-uuid",
  "TargetState": 2,
  "Name": ""
}
```

### Available Skeleton Models

Built-in skeleton models that work with EnemyNPC. All are rigged with combat animations.

| Model | Recommended Scale | contentString URL |
|-------|------------------|-------------------|
| **Skeleton Plain** | 1.41 | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FSkeleton%20Plain_Skeleton_Plain.glb?alt=media&token=e822b470-5305-4348-905f-dc6b380bf961&FixedSize=1.411088&overrideSize=true` |
| **Skeleton Red Eyes** | 1.41 | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FSkeleton%20Red%20Eyes_Skeleton_Red_Eyes.glb?alt=media&token=9cc16fc8-09b0-43d2-a086-c2f3268b4d84&FixedSize=1.411088&overrideSize=true` |
| **Skeleton Ghost** | 1.41 | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FSkeleton%20Ghost_Skeleton_Ghost.glb?alt=media&token=c9cec9cb-d482-4f56-8fcf-33a5b7db4acb` |
| **Skelly-B** (custom) | 1.60 | `https://d365bxku1h71bo.cloudfront.net:443/uploads/e2ebb15f-1bff-4981-91e7-1446dbbc6bad/gltf/2024-11-09_skelly-b_54f7e761984006fe.glb?FixedSize=1.6&overrideSize=true` |

### Available Weapons

Built-in weapon GLBs for combat NPCs. Each weapon requires a specific attachment `point` to sit correctly in the NPC's hand.

| Weapon | URL | Attachment Point |
|--------|-----|-----------------|
| **Stone Axe** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FStone%20Axe_StoneAxe.glb?alt=media&token=1b87fd10-a3ce-426f-96bd-2b2bfc964ad8` | pos: `[0.03, 0.18, 0.11]`, rot: `[0.019, -0.009, 0.906, -0.423]`, scale: `[1,1,1]` |
| **Bronze Axe** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FBronze%20Axe_BronzeAxe.glb?alt=media&token=be7a04c4-a4a5-433f-8fae-a9037292bf3b` | pos: `[0.08, 0.13, 0.10]`, rot: `[0.299, 0.037, -0.845, 0.441]`, scale: `[1,1,1]` |
| **Diamond Axe** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FDiamond%20Axe_DiamondAxe.glb?alt=media&token=632074ba-35db-4ff0-8373-6e9593b9a506` | pos: `[0.08, 0.12, 0.16]`, rot: `[0.299, 0.037, -0.845, 0.441]`, scale: `[1,1,1]` |
| **Knight Sword** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FKnight%20Sword%20(Back)_Back_KnightSword.glb?alt=media&token=a3a694ee-1b40-4605-b5f5-a45786d8ae3a` | pos: `[0.03, 0.10, 0.36]`, rot: `[0.232, -0.668, 0.252, -0.661]`, scale: `[1.32,1.32,1.32]` |
| **Gold Knight Sword** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FGold%20Knight%20Sword%20(Back)_Back_GoldKnightSword.glb?alt=media&token=14b060ed-19a3-4580-8583-52d428a831c4` | pos: `[0.03, 0.04, 0.38]`, rot: `[0.173, -0.686, 0.193, -0.680]`, scale: `[1.32,1.32,1.32]` |
| **Lava Sword** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FBack%20Lava%20Sword_Back_LavaSword.glb?alt=media&token=d80e555f-5fb1-4f43-bc09-a9f3595c5fcd` | pos: `[0.03, 0.04, 0.38]`, rot: `[0.173, -0.686, 0.193, -0.680]`, scale: `[1.32,1.32,1.32]` |
| **Grim Reaper Scythe** | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FGrim%20Reaper%20Scythe%20(Back)_Back_GrimReaperScythe.glb?alt=media&token=333b4633-5c22-45c5-a1b0-593827be0f56` | pos: `[0.04, 0.22, 0.20]`, rot: `[0.659, 0.177, 0.706, 0.189]`, scale: `[1.2,1.2,1.2]` |

### Difficulty Tuning Guide

Stat ranges observed across a working combat room with 44 NPCs:

| Difficulty | Health | Damage | Detect Dist | Attack Dist | Attack Speed | Max Attacks |
|-----------|--------|--------|-------------|-------------|-------------|-------------|
| **Easy** (fodder) | 40 | 10 | 5.0 | 1.0 | 1.0 | 1 |
| **Medium** | 80-120 | 20-30 | 8-10 | 1.6 | 0.8-1.0 | 1 |
| **Hard** (elite) | 200-320 | 50-100 | 12-15 | 2.4-4.0 | 0.64-1.4 | 2 |

Adjust `minTimeAttack` and `maxTimeAttack` to control attack frequency — lower values make the NPC attack more often.
