# Visual Effects Items

Particle systems and visual effects loaded via Unity Addressable assets.

## Addressable (VFX)

Visual effects (particles, fire, explosions, lightning) loaded from the built-in Portals asset library. These are NOT custom GLBs — they are pre-built Unity particle systems referenced by name.

**Important:** Addressable items use `contentString` (not a URL) to identify which effect to load. The format is always `FurnitureAddressables/{EffectName}`.

**Base structure:**

```json
{
  "prefabName": "Addressable",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "FurnitureAddressables/Fire2",
  "extraData": "{\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key fields:**
- `contentString`: `FurnitureAddressables/{EffectName}` — determines which VFX to load (see catalog below)
- `pos`: Emitter origin point. Most effects emit from center, so `y: 0.5` places them slightly above ground
- `scale`: Affects particle system size. Default `(1,1,1)` for standard size
- `rot`: Quaternion rotation. Most effects are omnidirectional, so identity quaternion works
- `extraData`: Supports `Tasks` and `ViewNodes` like other items. Can attach triggers/effects to show/hide

**Key points:**
- `modelsize` and `modelCenter` are always `{0, 0, 0}` — particle effects have no mesh bounding box
- Effects play continuously by default (looping particle systems)
- Use `ShowObjectEvent` / `HideObjectEvent` effects to toggle VFX on/off via triggers
- No special extraData keys — just `Tasks` and `ViewNodes`

---

## Known Effect Catalog

All `contentString` values use the `FurnitureAddressables/` prefix.

### Particles (6 effects)

| contentString | Description |
|---------------|-------------|
| `DustParticles` | Ambient floating dust motes |
| `ParticlesExplosion1` | Particle burst variant 1 |
| `ParticlesExplosion2` | Particle burst variant 2 |
| `ParticlesExplosion3` | Particle burst variant 3 |
| `ParticlesExplosion4` | Particle burst variant 4 |
| `ParticlesExplosion5` | Particle burst variant 5 |

### Fire (4 effects)

| contentString | Description |
|---------------|-------------|
| `Fire` | Standard fire effect |
| `Fire1` | Fire variant 1 |
| `Fire2` | Fire variant 2 |
| `Fire3` | Fire variant 3 |

### Explosion — Bomb (7 effects)

| contentString | Description |
|---------------|-------------|
| `ExplosionBomb1` | Bomb explosion variant 1 |
| `ExplosionBomb2` | Bomb explosion variant 2 |
| `ExplosionBomb3` | Bomb explosion variant 3 |
| `ExplosionBomb4` | Bomb explosion variant 4 |
| `ExplosionBomb5` | Bomb explosion variant 5 |
| `ExplosionBomb6` | Bomb explosion variant 6 |
| `ExplosionBomb7` | Bomb explosion variant 7 |

### Explosion — Ring (3 effects)

| contentString | Description |
|---------------|-------------|
| `ExplosionRing1` | Expanding ring explosion |
| `ExplosionRings2` | Multi-ring explosion variant 2 |
| `ExplosionRings3` | Multi-ring explosion variant 3 |

### Explosion — Other (4 effects)

| contentString | Description |
|---------------|-------------|
| `MagneticExplosion` | Magnetic field burst |
| `NuclearExplosion` | Mushroom cloud / nuclear blast |
| `SmokeExplosion1` | Smoke burst variant 1 |
| `SmokeExplosion2` | Smoke burst variant 2 |

### Explosion — Wave (2 effects)

| contentString | Description |
|---------------|-------------|
| `ShockExplosion` | Shockwave burst |
| `WavesExplosion` | Expanding wave explosion |

### Lightning (9 effects)

| contentString | Description |
|---------------|-------------|
| `LightningBall1` | Ball lightning / electric sphere |
| `LightningExplosion1` | Lightning burst variant 1 |
| `LightningExplosion2` | Lightning burst variant 2 |
| `LightningExplosion3` | Lightning burst variant 3 |
| `LightningParticlesTree` | Branching lightning tree / sparks |
| `LightningShock1` | Electric shock effect |
| `LightningStrike1` | Lightning bolt strike |
| `LightningWave3` | Lightning wave variant 3 |
| `LightningWaves2` | Lightning wave variant 2 |

### Energy (3 effects)

| contentString | Description |
|---------------|-------------|
| `AtomBall1` | Atomic energy sphere variant 1 |
| `AtomBall2` | Atomic energy sphere variant 2 |
| `FireBall1` | Fireball projectile effect |

### Other (2 effects)

| contentString | Description |
|---------------|-------------|
| `LineWaves1` | Undulating line wave pattern |
| `Portal` | Swirling portal VFX |

---

## Python Generator

```python
from lib.portals_core import create_addressable

# Fire effect at position (collider off by default)
fire, fire_logic = create_addressable(pos=(5, 0.5, 10), effect_name="Fire2")

# Dust particles, scaled up
dust, dust_logic = create_addressable(pos=(0, 1, 0), effect_name="DustParticles", scale=(2, 2, 2))

# Lightning strike
lightning, lightning_logic = create_addressable(pos=(8, 0, 15), effect_name="LightningStrike1")

# VFX that needs to block players (rare)
barrier, barrier_logic = create_addressable(pos=(3, 0, 5), effect_name="Fire2", collider=True)
```

---

## Common Uses

- **Ambient atmosphere**: `DustParticles`, `Fire` variants for torches/campfires
- **Combat feedback**: `ExplosionBomb` variants for hit impacts, `ShockExplosion` for knockback
- **Magic/abilities**: `LightningBall1`, `AtomBall` variants for spell effects
- **Environmental hazards**: `Fire` + damage trigger zones, `LightningStrike1` for storm areas
- **Decorative portals**: `Portal` VFX at teleport locations
- **Triggered effects**: Hide by default, `ShowObjectEvent` on trigger to play on demand

## Tips

- **Disable colliders**: Addressable VFX items have colliders enabled by default, which can block player movement or projectiles. It is recommended to turn colliders off by setting `"noCollide": true` in the item data, unless you specifically need the VFX to be a physical obstacle.
- **Toggling VFX**: Place the effect hidden (attach `HideObjectEvent` on Player Login), then use `ShowObjectEvent` when a trigger fires. Hide again after a delay to create one-shot effects.
- **Scaling**: Larger `scale` values expand the entire particle system. Most effects look best at scale 1-3.
- **Naming inconsistency**: Note `ExplosionRing1` (singular) vs `ExplosionRings2` / `ExplosionRings3` (plural). Use exact names.
- **Naming inconsistency**: Note `LightningWave3` (singular) vs `LightningWaves2` (plural). Use exact names.
