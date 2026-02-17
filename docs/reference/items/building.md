# Building Items

Core building blocks for creating spaces in Portals.

## ResizableCube

Primary building block. Default 1x1x1 cube, freely scalable to any dimensions.

**Base structure:**
```json
{
  "prefabName": "ResizableCube",
  "parentItemID": 0,
  "currentEditornetId": 0,
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "modelsize": {"x": 0, "y": 0, "z": 0},
  "modelCenter": {"x": 0, "y": 0, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "",
  "interactivityType": 0,
  "interactivityURL": "",
  "hoverTitle": "",
  "hoverBodyContent": "",
  "ImageInteractivityDetails": {"buttonText": "", "buttonURL": ""},
  "extraData": "{\"col\":\"888888\",\"Tasks\":[],\"ViewNodes\":[]}",
  "sessionData": "",
  "instanceId": "",
  "placed": true,
  "locked": false,
  "superLocked": false
}
```

**Key fields:**
- `pos`: World position (or local position if parented). Ground is y=0. A 1x1 cube on ground has center at y=0.5.
- `rot`: Quaternion `{x, y, z, w}`. Default: `{0, 0, 0, 1}` (no rotation)
- `scale`: Dimensions. `{2, 0.1, 2}` = flat 2x2 platform
- `parentItemID`: Item key of the parent (`0` = no parent). When set, `pos`/`rot` become local to the parent. See [parent-child docs](../systems/parent-child.md).
- `contentString`: Image texture URL (optional)
- `placed`: Must be `true` to appear in room

**extraData fields:**
- `col`: 6-char hex color (no `#` prefix). e.g., `"FF0000"` for red
- `e`: Emission/glow intensity (0.0-1.0+). Omit for no glow
- `o`: Opacity (0.0-1.0). Omit for fully opaque
- `c`: Collider. `false` = players pass through. Omit for solid
- `s`: Shadows. `false` = no shadows. Omit for shadows on
- `nav`: Nav mesh. `true` = AI walkable. Omit for non-walkable
- `t`: Texture tiling (when contentString set). `2.0` = repeats twice
- `title`: Internal label for identification
- `Tasks`: Array of effects/triggers
- `ViewNodes`: Always `[]`

**Python generator:**
```python
from scripts.portals_core import create_cube

# Platform
platform = create_cube(
    pos=(0, 0.5, 0),
    scale=(4, 0.2, 4),
    color="4169E1",
    shadows=False
)

# Glowing wall
wall = create_cube(
    pos=(0, 2, 5),
    scale=(10, 4, 0.2),
    color="FF0000",
    emission=0.8
)
```

---

## WorldText

3D text labels with rich formatting support.

**Base structure:**
```json
{
  "prefabName": "WorldText",
  "pos": {"x": 0, "y": 1, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"text\":\"Hello World\",\"lookAtCamera\":true,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**
- `text`: String with Unity rich text tags
- `lookAtCamera`: Billboard mode. `true` (default) = always faces camera

**Rich text tags:**
- `<b>bold</b>`
- `<i>italic</i>`
- `<u>underline</u>`
- `<color=#FF0000>red text</color>` (note: `#` prefix required here)

**Python generator:**
```python
from scripts.portals_core import create_text

title = create_text(
    pos=(0, 3, 0),
    content="<b><color=#FFD700>Welcome!</color></b>",
    billboard=True
)
```

---

## Portal

Teleportation between rooms or spawn points.

**Base structure:**
```json
{
  "prefabName": "Portal",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "destination-room-id",
  "extraData": "{\"id\":\"destination-room-id\",\"sn\":\"\",\"auto\":true,\"cm\":\"teleport\",\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**
- `id`: Destination room ID (UUID). Must match `contentString`
- `sn`: Spawn point name. `""` = default spawn
- `auto`: `true` = instant teleport on contact. Omit for press-X
- `cm`: Custom message. e.g., `"teleport"` → "Press X to teleport"

**Portal configurations:**

Auto-teleport to default spawn:
```json
"extraData": "{\"id\":\"room-id\",\"sn\":\"\",\"auto\":true,\"cm\":\"teleport\",\"Tasks\":[],\"ViewNodes\":[]}"
```

Auto-teleport to named spawn:
```json
"extraData": "{\"id\":\"room-id\",\"sn\":\"RedSpawn1\",\"auto\":true,\"cm\":\"teleport\",\"Tasks\":[],\"ViewNodes\":[]}"
```

Press X to teleport:
```json
"extraData": "{\"id\":\"room-id\",\"sn\":\"SpawnName\",\"cm\":\"teleport\",\"Tasks\":[],\"ViewNodes\":[]}"
```

**Python generator:**
```python
from scripts.portals_core import create_portal

portal = create_portal(
    pos=(10, 0.5, 0),
    scale=(2, 3, 2),
    destination_room_id="other-room-uuid",
    spawn_name="RedSpawn1",
    auto_teleport=True
)
```

---

## SpawnPoint

Defines where players appear when entering or teleporting.

**Base structure (default spawn):**
```json
{
  "prefabName": "SpawnPoint",
  "pos": {"x": 0, "y": 0.2, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 0.3, "y": 0.3, "z": 0.3},
  "extraData": "{\"Tasks\":[],\"n\":\"\",\"r\":0.0}"
}
```

**Base structure (named spawn):**
```json
{
  "prefabName": "SpawnPoint",
  "pos": {"x": 5, "y": 0.2, "z": 3},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 0.3, "y": 0.3, "z": 0.3},
  "extraData": "{\"Tasks\":[],\"n\":\"RedSpawn1\",\"r\":0.0}"
}
```

**extraData fields:**
- `n`: Spawn name. `""` = default spawn. Any string = named spawn
- `r`: Rotation offset (degrees). `0.0` = player faces Z+ direction
- `title`: Display title for the spawn point (optional)
- `absPos`: Absolute world position `{x,y,z}` (optional, set by editor)
- `absRot`: Absolute world rotation `{x,y,z,w}` (optional, set by editor)

**Spawn behavior:**
- Default spawn (`n:""`) - used when entering room or portal without spawn name
- Named spawn - used when portal `sn` field matches this name
- Multiple spawns with same name - player randomly assigned to one
- Scale always `0.3` - no need to change

**Python generator:**
```python
from scripts.portals_core import create_spawn

# Default spawn
default_spawn = create_spawn(
    pos=(0, 0.2, 0),
    name="",
    rotation_offset=0.0
)

# Named spawn
red_spawn = create_spawn(
    pos=(10, 0.2, 5),
    name="RedSpawn1",
    rotation_offset=90.0  # Face east
)
```

---

## Coordinate System

- Ground plane: y = 0
- Up: +Y
- 1x1 cube on ground: center at y = 0.5
- Default rotation: `{x:0, y:0, z:0, w:1}` (identity quaternion)
- With default rotation, player spawns facing Z+ direction

## Item IDs

Items stored in dict keyed by string numbers. ID `"1"` reserved. Start at `"2"`.

Example:
```python
items = {
    "2": create_spawn(pos=(0, 0.2, 0)),
    "3": create_cube(pos=(0, 0.5, 0), scale=(4, 0.2, 4)),
    "4": create_text(pos=(0, 3, 0), content="Welcome!")
}
```
