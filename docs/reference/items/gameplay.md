# Gameplay Items

Interactive items for game mechanics.

## Trigger Cube

Invisible zone that activates events when players enter, exit, or press a key while inside.

**IMPORTANT: Trigger cubes are invisible during play.** Never use visibility-dependent triggers (`OnClickEvent`, `OnHoverStartEvent`, `OnHoverEndEvent`) on Trigger cubes — players cannot see, click, or hover over invisible items. Use visible items (ResizableCube, GLB, etc.) for click/hover interactions. Trigger cubes are designed for **zone-based triggers** (`OnEnterEvent`, `OnExitEvent`) and optionally press-to-interact via `pressBtn`.

**Base structure:**
```json
{
  "prefabName": "Trigger",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"events\":[],\"cm\":\"\",\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key points:**
- Invisible during play (visible in build mode)
- Default 1x1x1 cube, resize with `scale`
- Two trigger types: **User Enter** and **User Exit**

**extraData fields:**
- `events`: Array of events (usually `[]` when using Tasks)
- `pressBtn`: `true` = require key press. Omit for auto-trigger
- `keyCode`: Key to press (e.g., `"X"`, `"H"`, `"E"`)
- `cm`: Custom message. "Press [key] to [message]"
- `opacity`: Visual opacity in editor (float, 0.0-1.0). e.g., `0.01` for near-invisible. Does not affect gameplay (trigger cubes are always invisible during play)
- `Tasks`: Array of trigger subscriptions

**Configurations:**

Auto-trigger on enter:
```json
"extraData": "{\"events\":[],\"cm\":\"\",\"Tasks\":[],\"ViewNodes\":[]}"
```

Press X to activate:
```json
"extraData": "{\"events\":[],\"pressBtn\":true,\"cm\":\"activate\",\"keyCode\":\"X\",\"Tasks\":[],\"ViewNodes\":[]}"
```

**Python generator:**
```python
from scripts.portals_core import create_trigger

# Auto-trigger zone
death_zone = create_trigger(
    pos=(0, -5, 0),
    scale=(100, 1, 100),  # Large area below platforms
    press_button=False
)

# Press X to activate
button = create_trigger(
    pos=(5, 0.5, 0),
    scale=(1, 1, 1),
    press_button=True,
    key_code="X",
    message="activate switch"
)
```

**Common uses:**
- Death zones (below platforms)
- Checkpoint zones
- Puzzle activation areas
- Win condition zones

---

## Jump Pad

Launches players into the air when stepped on.

**Base structure:**
```json
{
  "prefabName": "JumpPad",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"p\":6.9}"
}
```

**extraData fields:**
- `p`: Launch power. Higher = more height/distance

**Power reference:** See [movement-reference.md](../systems/movement-reference.md) for empirically measured jump heights, horizontal distances, and level design guidelines. The UI slider ranges from 1-10; setting 1 = normal jump (~1.63m), setting 3 = ~6.73m height / ~22.5m horizontal.

**Python generator:**
```python
from scripts.portals_core import create_jump_pad

# Medium jump
pad = create_jump_pad(
    pos=(2, 0.5, 0),
    power=6.9,
    scale=(1, 1, 1)
)

# Extreme launch
launch_pad = create_jump_pad(
    pos=(10, 0.5, 0),
    power=12.0,
    scale=(1.5, 1.5, 1.5)
)
```

**Tips:**
- Place slightly above ground (y=0.5 for default size)
- Use larger scale (1.5-2.0) for easier targeting
- Chain multiple pads for platformer sequences
- Adjust power based on distance between platforms

---

## Gun

Pickupable weapon that players can use to shoot. Deals damage to other players and Destructible items. The weapon type determines the visual model.

**Base structure:**
```json
{
  "prefabName": "Gun",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"weaponType\":1,\"maxDamage\":20,\"minDamage\":10,\"minDamageDistance\":10.0,\"maxDamageDistance\":40.0,\"firerate\":0.2,\"projectilesPerShot\":1,\"dispersion\":0.5,\"clipSize\":12,\"startLoaded\":true,\"startingReserveAmmo\":36,\"reloadTime\":1.5,\"autoReload\":true,\"maxRange\":50.0,\"cameraStability\":0.7,\"recoilRight\":0.5,\"recoilLeft\":-0.5,\"recoilUp\":1.5,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

### Weapon Types

| Value | Type |
|-------|------|
| `1` | Pistol |
| `2` | Rifle |
| `3` | Shotgun (default) |

### Damage

| Key | Default | Description |
|-----|---------|-------------|
| `maxDamage` | `25` | Maximum damage dealt at close range. |
| `minDamage` | `10` | Minimum damage dealt at long range. |
| `minDamageDistance` | `8` | Distance where max damage starts to fall off. |
| `maxDamageDistance` | `50` | Distance where damage reaches minimum. |

### Firing

| Key | Default | Description |
|-----|---------|-------------|
| `firerate` | `0.8` | Time between shots (seconds). |
| `projectilesPerShot` | `8` | Number of pellets/bullets per shot. |
| `dispersion` | `5.0` | Bullet spread angle (degrees). |
| `automaticWeapon` | `false` | `true` = fires continuously while holding trigger. |
| `maxRange` | `30` | Maximum bullet travel distance. |

### Ammo

| Key | Default | Description |
|-----|---------|-------------|
| `isInfinityAmmo` | `false` | `true` = infinite ammo, never needs reloading. |
| `infiniteReserveAmmo` | `false` | `true` = infinite reserve ammo, still needs to reload clips. |
| `clipSize` | `8` | Magazine/clip capacity. |
| `startLoaded` | `true` | `true` = starts with a full magazine. |
| `startingReserveAmmo` | `0` | Reserve ammo on pickup. |
| `reloadTime` | `1.0` | Reload duration (seconds). |
| `autoReload` | `false` | `true` = auto reload when magazine is empty. |
| `dontUseReload` | `false` | `true` = disable reload mechanic entirely. |
| `reloadOneByOne` | `false` | `true` = reload one round at a time (like a shotgun). |

### Recoil

| Key | Default | Description |
|-----|---------|-------------|
| `cameraStability` | `0.5` | Camera stability. Lower = more shake. |
| `recoilRight` | `2.5` | Maximum rightward recoil. |
| `recoilLeft` | `-2.5` | Maximum leftward recoil. |
| `recoilUp` | `2.0` | Upward recoil per shot. |

### Audio

| Key | Default | Description |
|-----|---------|-------------|
| `gunShotVolume` | `1.0` | Gunshot sound volume. |
| `reloadVolume` | `1.0` | Reload sound volume. |
| `audioMaxVolumeDistance` | `10` | Distance for full volume. |
| `audioMinVolumeDistance` | `50` | Distance where sound fades to zero. |
| `customGunShotUrl` | `""` | URL to a custom gunshot sound file (MP3). |

### Display & Behavior

| Key | Default | Description |
|-----|---------|-------------|
| `multiplayer` | `false` | `true` = syncs across all players. |
| `canCollectByCollision` | `true` | `true` = pick up by walking over it. |
| `showCrosshair` | `true` | Display crosshair when aiming. |
| `showHitmarkers` | `true` | Show hit feedback markers. |
| `displayAmmoCount` | `true` | Show ammo counter UI. |
| `clipAmmoLabel` | `"Clip Ammo"` | Label for clip ammo display. |
| `reserveAmmoLabel` | `"Reserve Ammo"` | Label for reserve ammo display. Can reference a variable name. |
| `gunColor` | `"000000"` | Gun model color. 6-char hex, no `#` prefix. |
| `animateGun` | `true` | Enable gun animations. |

### Model Settings

| Key | Default | Description |
|-----|---------|-------------|
| `s` | `true` | Shadows. `false` = no shadows. |
| `l` | `true` | Local animation. `false` = syncs animation across server. |
| `c` | `true` | Collider. `false` = no collision. |
| `f` | `false` | Camera fade. `true` = object fades instead of camera colliding. |
| `r` | `false` | Remove first frame. `true` = removes frame 0 from animated GLBs. |

---

## Shotgun

Weapon variant with a different visual model. Functionally identical to Gun — uses the same extraData fields. Setting `weaponType: 3` on a Gun item also produces a shotgun model, so this prefab may be an alternative way to create shotgun-type weapons.

**Base structure:**
```json
{
  "prefabName": "Shotgun",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"weaponType\":3,\"maxDamage\":25,\"minDamage\":10,\"firerate\":0.8,\"projectilesPerShot\":8,\"dispersion\":5.0,\"clipSize\":8,\"startLoaded\":true,\"startingReserveAmmo\":24,\"reloadTime\":1.0,\"reloadOneByOne\":true,\"autoReload\":false,\"maxRange\":30.0,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

Uses the same extraData fields as Gun — see [Gun](#gun) for full field reference.

---

## CameraObject

Defines a named camera position/state in the room. Linked to `customCameraStates` in settings via the `sn` (state name) field. Used to place camera viewpoints at specific world positions.

**Base structure:**
```json
{
  "prefabName": "CameraObject",
  "pos": {"x": 2.238, "y": 0.582, "z": 2.270},
  "rot": {"x": 0.075, "y": -0.075, "z": -0.703, "w": 0.703},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"fov\":86.0,\"sn\":\"crewmate\",\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**

| Key | Type | Description |
|-----|------|-------------|
| `fov` | float | Field of view in degrees |
| `sn` | string | State name — must match a `customCameraStates[].stateName` in room settings |
| `Tasks` | array | Standard Tasks array |
| `ViewNodes` | array | Always `[]` |

**Usage:** Place CameraObject items at desired camera viewpoints. Set the `sn` field to match a `customCameraStates` entry in settings. Use the `ChangeCamState` effect to switch players to this camera view.

---

## Elemental Cube

Animated elemental block with rounded corners. Works like a ResizableCube (1x1x1 default, can be resized and stretched) but has an animated texture and rounded corners instead of sharp edges. The element type is set via `contentString`. All elemental cubes share the same GLB model.

**Base structure:**
```json
{
  "prefabName": "9Cube",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "lava",
  "extraData": "{\"GLBUrl\":\"https://dwh7ute75zx34.cloudfront.net/Models/08_09/9SliceBlock_Rig_Empty.glb\",\"c\":\"\",\"Tasks\":[],\"ViewNodes\":[]}"
}
```

### Elemental Types

Set the `contentString` to one of these values:

| Value | Description |
|-------|-------------|
| `lava` | Lava texture |
| `hotlava` | Hot lava texture (alternate lava variant) |
| `water` | Water texture |

### Elemental Cube extraData fields

| Key | Description |
|-----|-------------|
| `GLBUrl` | Always `"https://dwh7ute75zx34.cloudfront.net/Models/08_09/9SliceBlock_Rig_Empty.glb"`. |
| `c` | Always empty string `""`. |
| `s` | Texture scale. Higher number = larger visual texture. Omit for default. |
| `t` | Transparency. `0.0` = fully transparent, `1.0` = fully opaque. Omit for fully opaque. |
| `e` | Emission/glow intensity. Omit for default. |
| `nc` | No collider. `true` = players pass through. Omit for default (solid). |
| `so` | Shadow off. `true` = no shadows. Omit for default (shadows on). |
| `nav` | AI walkable nav mesh. `true` = item becomes a nav mesh surface. Omit for non-walkable. |

---

## Trigger + Effects Pattern

Triggers become powerful when combined with effects in the `Tasks` array:

**Example: Death zone that teleports player back to spawn**
```python
from scripts.portals_effects import create_enter_trigger, create_teleport_effect

# Create quest for death system
death_quest = create_quest_pair(0, "death", "Respawn system")

# Trigger with teleport effect
death_zone = create_trigger(pos=(0, -10, 0), scale=(100, 1, 100))
death_zone["extraData"] = format_extra_data({
    "events": [],
    "cm": "",
    "Tasks": [
        create_enter_trigger(
            quest_id=death_quest["quest_id"],
            quest_name=death_quest["quest_name"],
            target_state=1,
            effect=create_teleport_effect(spawn_name="")
        )
    ],
    "ViewNodes": []
})
```

See [effects/transform.md](../effects/transform.md) and [systems/quests.md](../systems/quests.md) for more on triggers and effects.
