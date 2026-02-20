---
name: Side-Scroller Platformer
category: mechanics
tags: [side-scroller, platformer, 2d, camera, platform, checkpoint, hazard, collectible, jump, level, section]
patterns: [direct-trigger-effect, quest-gated-effect, quest-advancing-trigger, state-machine, variable-tracking]
summary: Fixed side-view camera with platformer movement, axis-aligned level sections, checkpoint/respawn system, hazards, collectibles, and jump pads — turns a 3D Portals room into a 2D platformer
---

# Side-Scroller Platformer

A complete side-scrolling platformer setup that constrains the player to a 2D plane using a fixed-angle camera and locked movement axis. The level is built from platforms aligned on a single plane, with hazards, collectibles, and checkpoints sharing that alignment.

## Core Principles

Three things make a Portals room feel like a 2D side-scroller:

1. **Fixed side-view camera** — `cameraMode: 1` (follows player), angled 90° to view from the side
2. **Platformer movement** — `stopVerticalInput: true` locks the player to the scrolling plane, preventing them from walking toward or away from the camera
3. **Axis alignment** — all gameplay items share the same X position (X=0), creating a flat plane for the player to traverse through Z (horizontal scrolling) and Y (vertical jumping)

## Settings

### Camera State

The camera follows the player but views from a fixed side angle. Define a custom camera state in `roomSettingsExtraData.customCameraStates`:

```python
SIDE_SCROLLER_CAMERA = {
    "stateName": "platformer",
    "cameraMode": 1,        # Fixed angle — follows player position
    "distance": -17.0,      # Negative = offset perpendicular to view
    "height": 3.0,          # Slight upward offset
    "fov": 60.0,            # Standard field of view
    "right": 10.0,          # Lateral offset
    "angleX": -90.0,        # Look from the side (perpendicular to play plane)
    "angleY": 180.0,        # Face toward the play plane
    "pos": {"x": 0, "y": 0, "z": 0},
    "rot": {"x": 0, "y": 0, "z": 0},
    "lookAtPlayer": False
}
```

Set `defaultCameraState` to the index of this camera state (usually `0` if it's the only one).

**Tuning:** Adjust `distance` for zoom level (more negative = further away, showing more of the level). Adjust `fov` for perspective vs. flattened look.

### Movement

Platformer movement uses `stopVerticalInput: true` to lock the player onto the 2D plane. This is the critical setting that prevents the player from walking toward/away from the camera.

```python
PLATFORMER_MOVEMENT = {
    "movementStateName": "",
    "walkByDefault": False,
    "walkSpeed": 2.0,
    "runSpeed": 8.0,
    "sprintSpeed": 10.0,
    "jumpTimer": 0.3,
    "jumpHeight": 6.0,
    "airSpeed": 10.0,
    "gravity": -15.0,
    "rotationSpeed": 16.0,
    "ledgeGrab": True,           # Helps with platform edges
    "forceFirstPerson": False,
    "stopVerticalInput": True    # THE KEY SETTING — locks to 2D plane
}
```

### Other Settings

```python
settings = {
    "roomBase": "BlankScene",
    "isNight": True,             # Dark background makes platforms pop
    "roomSettingsExtraData": json.dumps({
        "customCameraStates": [SIDE_SCROLLER_CAMERA],
        "defaultCameraState": 0,
        "movementValues": PLATFORMER_MOVEMENT,
        # Avatar selection (optional)
        "roundyAvatars": True,
        "blockyAvatars": False,
        "rpmAvatars": False,
        "collectibleAvatars": False,
        "customAvatars": False,
        # Fog pushed far back so it doesn't clip the level
        "fog": {
            "DayFogMax": 500.0,
            "NightFogMax": 500.0,
            "DayFogColor": "080C10",
            "NightFogColor": "000000"
        },
        "preloadRoom": True,
        "onboardingType": 1
    })
}
```

## Level Structure

### Axis Alignment

All gameplay items sit at **X=0**. The player moves through **Z** (horizontal — the scrolling direction) and **Y** (vertical — jumping). Background scenery sits at negative X values (behind the play plane), foreground at positive X values (in front).

```
Camera (X = +17)
  |
  |  Foreground (X > 0) — decorative only, no collision
  |
  |  Play Plane (X = 0) — platforms, hazards, collectibles, triggers
  |
  |  Background (X < 0) — scenery, parallax layers
  |
```

### Platforms

The essential requirement: every platform sits at **X=0** and is **wide enough on the X axis** for the player to run on without falling off the sides (the camera hides X-axis drift, but the player can still slip off a narrow platform). A minimum X-scale of ~3-5 units keeps things comfortable.

Platforms can be **ResizableCubes** (solid geometry) or **GLBs** (themed visuals). They don't need to be children of anything — flat placement at absolute coordinates works fine:

```python
from portals_core import create_cube

def create_platform(platform_id, y, z, z_width, thickness=0.5, x_depth=5):
    """
    Create a platform on the play plane.

    Args:
        y: Vertical position (height of the platform)
        z: Horizontal position (along the scrolling direction)
        z_width: How long the platform is in the scrolling direction
        thickness: Platform thickness (Y)
        x_depth: Width into/out of the screen — keep ≥3 so the player doesn't slip off
    """
    item, logic_entry = create_cube(
        id_=platform_id,
        position=[0, y, z],
        scale=[x_depth, thickness, z_width],
        locked=True
    )
    return item, logic_entry
```

For GLB platforms, the same principle applies — place at X=0 and ensure the model is wide enough on X that the player has room.

### Section Parents (Optional)

For large levels, you can optionally group platforms into **section parent cubes** chained along Z. All children use relative coordinates, so repositioning a section moves everything inside it. This is useful for iteration but not required — flat placement works equally well for simpler levels.

## Checkpoint / Respawn System

Checkpoints use **SpawnPoints** placed throughout the level. When the player dies (hits a hazard), they teleport back to the nearest checkpoint spawn.

### Spawn Points

Place spawn points at the start of each level segment, at X=0. The spawn's index (order of creation) determines its `sn` (spawn number) used by teleport effects.

```python
from portals_core import create_spawn_point

def create_checkpoint(spawn_id, y, z):
    """Create a checkpoint spawn on the play plane."""
    item, logic_entry = create_spawn_point(
        id_=spawn_id,
        position=[0, y, z]
    )
    return item, logic_entry
```

### Death / Respawn Wiring

Each hazard needs a **repeatable death cycle**: collide → trigger death quest → play sound + teleport → reset quest (so it can fire again).

Two shared quests drive the system:

```python
from portals_utils import make_quest

quests["die_sound"] = make_quest(
    name="die_sound", display_name="Die Sound",
    creator=CREATOR_UID, shared=False
)
```

Each hazard also gets its own quest for targeting the correct checkpoint:

```python
quests[f"hazard_{n}"] = make_quest(
    name=f"hazard_{n}", display_name=f"Hazard {n}",
    creator=CREATOR_UID, shared=False
)
```

### Hazard Wiring Pattern

Each hazard (GLB with collision or Trigger cube) uses a **fire-and-reset** quest cycle:

```python
from portals_effects import add_task_to_logic

def wire_hazard(logic, hazard_id, hazard_quest_name, hazard_quest_ids, die_sound_ids, checkpoint_spawn_number, room_id):
    """
    Wire a hazard with death sound + teleport to checkpoint + auto-reset.

    Args:
        hazard_id: The hazard item ID
        hazard_quest_name: Quest name for this specific hazard (e.g. "hazard_1")
        hazard_quest_ids: Dict with "inProgress" and "completed" IDs for the hazard quest
        die_sound_ids: Dict with "inProgress" and "completed" IDs for the die_sound quest
        checkpoint_spawn_number: Spawn index to teleport to (string, e.g. "2")
        room_id: The room UUID
    """
    tasks = logic[hazard_id].setdefault("Tasks", [])

    # 1. On collide → complete hazard quest (triggers teleport)
    tasks.append({
        "$type": "TaskTriggerSubscription",
        "Trigger": {"$type": "OnCollideEvent", "Delay": 0},
        "Id": str(uuid4()),
        "TargetState": 141,  # Force-complete from any state
        "Name": hazard_quest_name,
        "InProgressId": hazard_quest_ids["inProgress"],
        "CompletedId": hazard_quest_ids["completed"],
        "TaskTriggerId": hazard_quest_ids["completed"]
    })

    # 2. On collide → complete die_sound quest (triggers death sound)
    tasks.append({
        "$type": "TaskTriggerSubscription",
        "Trigger": {"$type": "OnCollideEvent", "Delay": 0},
        "Id": str(uuid4()),
        "TargetState": 141,
        "Name": "die_sound",
        "InProgressId": die_sound_ids["inProgress"],
        "CompletedId": die_sound_ids["completed"],
        "TaskTriggerId": die_sound_ids["completed"]
    })

    # 3. After 1s → reset die_sound quest (so it can fire again)
    tasks.append({
        "$type": "TaskTriggerSubscription",
        "Trigger": {"$type": "OnCollideEvent", "Delay": 1},
        "Id": str(uuid4()),
        "TargetState": 101,  # Reset to base state
        "Name": "die_sound",
        "InProgressId": die_sound_ids["inProgress"],
        "CompletedId": die_sound_ids["completed"],
        "TaskTriggerId": die_sound_ids["inProgress"]
    })

    # 4. When hazard quest completes → teleport to checkpoint
    tasks.append({
        "$type": "TaskEffectorSubscription",
        "Effector": {
            "$type": "TeleportEvent",
            "id": room_id,
            "sn": checkpoint_spawn_number
        },
        "PreparationEffector": None,
        "Id": str(uuid4()),
        "TargetState": 2,
        "Name": hazard_quest_name,
        "InProgressId": hazard_quest_ids["inProgress"],
        "CompletedId": hazard_quest_ids["completed"],
        "TaskTriggerId": hazard_quest_ids["inProgress"]
    })

    # 5. After 1s → reset hazard quest (so hazard can fire again)
    tasks.append({
        "$type": "TaskTriggerSubscription",
        "Trigger": {"$type": "OnCollideEvent", "Delay": 1},
        "Id": str(uuid4()),
        "TargetState": 101,
        "Name": hazard_quest_name,
        "InProgressId": hazard_quest_ids["inProgress"],
        "CompletedId": hazard_quest_ids["completed"],
        "TaskTriggerId": hazard_quest_ids["inProgress"]
    })
```

**Key detail:** The 1-second delay on the reset tasks ensures the death sound plays and the teleport executes before the quest resets for the next collision.

### Death Sound (on a controller item)

A single controller item (often a hidden cube at the origin) listens for the `die_sound` quest and plays the death sound globally:

```python
from portals_effects import quest_effector, effector_play_sound, add_task_to_logic

DEATH_SOUND_URL = "YOUR_DEATH_SOUND_URL"

add_task_to_logic(logic[controller_id], quest_effector(
    quest_id=die_sound_quest_id, quest_name="die_sound",
    target_state=2,
    effector=effector_play_sound(url=DEATH_SOUND_URL, distance=-1, preload=True)
))
```

## Kill Triggers (Fall Zones)

Invisible Trigger cubes placed below platforms act as fall-death zones. They use the **same fire-and-reset pattern** as hazard GLBs but with `OnEnterEvent` instead of `OnCollideEvent`:

```python
from portals_core import create_trigger

def create_kill_zone(trigger_id, y, z, z_width):
    """Create an invisible kill zone below a platform gap."""
    item, logic_entry = create_trigger(
        id_=trigger_id,
        position=[0, y, z],
        scale=[5, 1, z_width]
    )
    return item, logic_entry
```

Wire identically to hazards but swap `OnCollideEvent` for `OnEnterEvent`.

## Collectibles

AutoCollectGLB items auto-collect when the player touches them and can track to a global counter or quest. Place at X=0 along the platform path.

```python
from portals_core import create_collectible

def create_coin(coin_id, y, z, glb_url, collect_sound_url, group_id=""):
    """Create a collectible coin/orb on the play plane."""
    item, logic_entry = create_collectible(
        id_=coin_id,
        position=[0, y, z],
        rotation=[-0.7071068, 0, 0, -0.7071068],
        glb_url=glb_url,
        sound_url=collect_sound_url,
        group_id=group_id  # Groups share a collect counter
    )
    return item, logic_entry
```

## Jump Pads

Jump pads launch the player vertically. The `p` field in the logic controls launch power.

```python
from portals_core import create_jump_pad

def create_launcher(pad_id, y, z, power=10.0):
    """Create a jump pad on the play plane."""
    item, logic_entry = create_jump_pad(
        id_=pad_id,
        position=[0, y, z],
        rotation=[-0.7071068, 0, 0, 0.7071068],
        scale=[2, 2, 0.02],  # Flat disc
        power=power
    )
    return item, logic_entry
```

## Level Portals (Section Transitions)

Portals teleport the player to another room. Use these at the end of a level to link to the next one, or to loop back to the start.

```python
from portals_core import create_portal

def create_level_portal(portal_id, y, z, target_room_id):
    """Create a portal leading to the next level."""
    item, logic_entry = create_portal(
        id_=portal_id,
        position=[0, y, z],
        rotation=[0.7071068, 0, 0, 0.7071068],
        scale=[4.5, 1, 5.7],
        target_room_id=target_room_id
    )
    return item, logic_entry
```

## Background & Foreground

Scenery creates visual depth without affecting gameplay. Place items at different X values:

| Layer | X Range | Purpose |
|-------|---------|---------|
| Far background | X = -10 to -20 | Skyline, distant mountains, parallax layers |
| Near background | X = -2 to -5 | Walls, pipes, windows, decorative detail |
| Play plane | X = 0 | Platforms, hazards, collectibles, triggers |
| Foreground | X = +2 to +5 | Railing, foliage, particles (decorative only) |

Background and foreground items should have **no collision** (`"c": false` in logic, or use non-collidable item types like GoldenPainting for images).

## Complete Level Assembly

```python
import json

room_items = {}
logic = {}
quests = {}

# 1. Platforms — lay out the level along Z, all at X=0
#    Y = height, Z = horizontal position
platforms = [
    {"id": 101, "y": 0, "z": 0, "width": 15},      # ground
    {"id": 102, "y": 3, "z": 20, "width": 8},       # raised platform
    {"id": 103, "y": 0, "z": 35, "width": 10},      # ground continues
    {"id": 104, "y": 6, "z": 50, "width": 6},       # high ledge
]
for p in platforms:
    item, lg = create_platform(p["id"], p["y"], p["z"], p["width"])
    room_items[str(p["id"])] = item
    logic[str(p["id"])] = lg

# 2. Checkpoints — spawn points at key positions
# 3. Hazards — GLBs or triggers, wired with fire-and-reset pattern
# 4. Collectibles — coins/orbs along platform paths
# 5. Jump pads — at vertical transitions
# 6. Background scenery — at X < 0 for depth
# 7. Portals — at end of level linking to next room

# Assemble and serialize
room_data = {
    "roomItems": room_items,
    "settings": settings,
    "roomTasks": {},
    "quests": quests,
    "logic": logic
}

from portals_utils import serialize_logic
serialize_logic(room_data)

with open("snapshot.json", "w") as f:
    json.dump(room_data, f)
```

---

## Critical Rules

1. **`stopVerticalInput: true` is non-negotiable.** Without it, players walk toward the camera and fall off the level plane. This single setting is what makes the room feel 2D.

2. **All gameplay at X=0.** Platforms, triggers, hazards, collectibles, jump pads, spawn points — all at X=0. Anything at other X values is scenery only.

3. **Platforms must be wide enough on X.** The camera hides X-axis movement, but the player can still drift sideways and fall off a narrow platform. Keep X-scale at 3-5+ units.

4. **Hazard quests must reset.** The fire-and-reset pattern (complete on collide → reset after 1s delay) is essential. Without the reset, the hazard only kills once.

5. **Spawn point order matters.** Teleport effects reference spawns by index (`"sn": "2"`). Create spawn points in a consistent order so checkpoint numbers are predictable.

6. **Camera distance controls difficulty feel.** Closer camera (distance -10) feels intense and fast. Further camera (distance -25) shows more level, giving players more reaction time. Start at -17 and adjust.

7. **Background creates the atmosphere.** A side-scroller with only platforms in a void looks like a prototype. Add background layers at negative X values. Even simple colored cubes at X=-10 as building silhouettes make a huge difference.
