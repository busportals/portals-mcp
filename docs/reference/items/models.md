# Model Items

3D models (GLB format) for decorations, collectibles, and interactive objects.

## Custom GLB

Static or animated 3D model from a GLB file.

**Base structure:**
```json
{
  "prefabName": "GLB",
  "pos": {"x": 0, "y": 0, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "https://example.com/model.glb",
  "extraData": "{\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key fields:**
- `contentString`: GLB model URL (publicly accessible)
- `scale`: Proportional multiplier on model's native size

**extraData fields:**
- `s`: Shadows. `false` = no shadows (improves FPS)
- `c`: Collider. `false` = no collision
- `l`: Local animation. `true` (default) = independent per client. `false` = synced
- `f`: Camera fade. `true` = fades instead of camera collision
- `r`: Remove first frame. `true` = removes frame 0 for animations

---

## Collectible GLB

Pickupable 3D model that modifies a variable when collected.

**Base structure:**
```json
{
  "prefabName": "GlbCollectable",
  "pos": {"x": 0, "y": 1, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "https://example.com/coin.glb?dynamic=true",
  "extraData": "{\"valueLabel\":\"coins\",\"valueChange\":1,\"displayValue\":true,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**IMPORTANT**: URL must have `?dynamic=true` appended.

**extraData fields:**
- `valueLabel`: Variable name to modify (e.g., "coins", "score")
- `valueChange`: Amount to add/subtract. Default `1`
- `op`: Operation. Omit = add. `2` = subtract
- `displayValue`: `true` = show UI with current value on collection
- `a`: Animation. `true` (default) = rotates. `false` = static
- `se`: Sound effect URL (MP3) played on collection
- `l`: Local animation. `true` (default) = per-client
- `minRespawnTime`: Min seconds before reappear
- `maxRespawnTime`: Max seconds before reappear (random between min/max)
- `minDespawnTime`: Min seconds before auto-despawn
- `maxDespawnTime`: Max seconds before auto-despawn
- `randomRadius`: Respawn within this radius (meters) of original position

**Python generator:**
```python
from scripts.portals_core import create_collectible

coin = create_collectible(
    pos=(5, 1, 0),
    glb_url="https://example.com/coin.glb",
    variable="coins",
    value_change=1,
    sound_url="https://example.com/coin.mp3",
    display_value=True,
    respawn_time=(3.0, 5.0)  # Respawn after 3-5 seconds
)
```

**Common coin GLB URL:**
```
https://dwh7ute75zx34.cloudfront.net/Models/Collectibles/Coin_Gold.glb?dynamic=true
```

---

## Destructible

3D model that can be destroyed by players using guns or melee weapons. When destroyed, the item plays a particle explosion effect and respawns after a configurable delay. Scale acts as a proportional multiplier on the model's native size.

**Base structure:**
```json
{
  "prefabName": "Destructible",
  "pos": {"x": 0, "y": 1, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "https://example.com/model.glb",
  "extraData": "{\"destructionEffect\":{\"particleCount\":40,\"minParticleSize\":0.01,\"maxParticleSize\":0.4,\"minParticleSpeed\":1.0,\"maxParticleSpeed\":6.0,\"particleLifetime\":5.0,\"radius\":2.0},\"particleOrigin\":{\"rotation\":[0.0,0.0,0.0,1.0],\"scale\":[1.0,1.0,1.0]},\"healthBarPos\":{\"position\":[0.0,2.0,0.0],\"rotation\":[0.0,0.0,0.0,1.0],\"scale\":[1.0,1.0,1.0]},\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key fields:**
- `contentString`: GLB model URL. Must be a full, publicly accessible URL.
- `scale`: Proportional multiplier on the model's native size.

**extraData fields:**

| Key | Description |
|-----|-------------|
| `maxHealth` | Health points before destruction. Default is `100` if omitted. |
| `respawnTime` | Time (seconds) before the destructible reappears after being destroyed. |
| `multiplayer` | `true` = destruction state is shared across all players. Omit for single-player (each player destroys independently). |
| `showHealthBar` | `false` = hide the health bar. Omit or `true` for visible health bar. |

### Destruction Effect

The `destructionEffect` object controls the particle explosion when destroyed:

| Key | Description |
|-----|-------------|
| `particleCount` | Number of particles spawned. |
| `minParticleSize` / `maxParticleSize` | Size range for particles. |
| `minParticleSpeed` / `maxParticleSpeed` | Speed range for particles. |
| `particleLifetime` | How long particles last (seconds). |
| `radius` | Explosion radius. |

### Transform Overrides

| Key | Description |
|-----|-------------|
| `particleOrigin` | Transform for where particles spawn. Contains `rotation` [qx,qy,qz,qw] and `scale` [x,y,z]. Adjustable to fine-tune the explosion origin. |
| `healthBarPos` | Transform for the health bar position. Contains `position` [x,y,z], `rotation` [qx,qy,qz,qw], and `scale` [x,y,z]. Adjustable to position the health bar above the model. |

---

## Variable System Integration

Collectibles modify **variables** which must be defined in the room's `variables` array:

```python
variables = [
    {
        "name": "coins",
        "multiplayer": False,  # Per-player tracking
        "persistent": True,    # Saves across sessions
        "variableType": "Numeric"
    }
]
```

See [systems/variables.md](../systems/variables.md) for full variable documentation.

---

## Tips

**For coins/gems:**
- Use small scale (0.3-0.5) for pickups
- Enable `displayValue` to show count
- Add sound effect for feedback
- Set respawn time for replayability

**For power-ups:**
- Use larger scale (0.8-1.2)
- Longer despawn time (60+ seconds)
- Subtract operation (`op:2`) for removing items

**For quest items:**
- Single collection (no respawn)
- Link to quest trigger via `valueLabel`
- Consider disabling auto-display for narrative items
