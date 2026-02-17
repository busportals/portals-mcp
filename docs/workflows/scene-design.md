# Scene Design & Environment Best Practices

How to make Portals environments feel real, lived-in, and intentional. This document covers asset classification, placement strategies, composition principles, and variety techniques.

**Who reads this**: The main conversation during design phase (to inform `design.md`) and subagents during build phase (to produce natural-looking scenes).

---

## Asset Classification

Every GLB asset falls into one of these placement categories. Identify each asset's category in `catalog.json` and in the build manifest so subagents know which placement strategy to use.

### Modular Kit Pieces
**Examples**: Wall panels, floor tiles, ceiling tiles, corridor segments, window frames, door frames, stair sections, railing segments.

**Characteristics**: Designed to snap together seamlessly. Uniform dimensions. Repeating patterns. Often share a consistent material/style.

**Placement rules**:
- **Precise alignment** — no gaps, no overlaps (unless intentional weathering)
- **Grid-based** — calculate spacing from exact dimensions in catalog
- **Consistent scale** — all pieces in a kit use the same scale factor
- **Rotation in 90° increments** — modular pieces snap to cardinal directions
- **Edge-to-edge** — use `footprint` dimensions for exact tiling

```python
# Modular wall segments along X axis
wall_width = get_width("wall_panel") * SCALE
for i in range(num_panels):
    place("wall_panel", (start_x + i * wall_width, 0, wall_z),
          facing_deg=0, scale=SCALE)
```

**Modular kit helpers**: When working with kits that have been through the detection pipeline, use the `ModularKit` class for grid-based placement with automatic validation. See [modular-kits.md](../reference/modular-kits.md) for the full API.

### Organic / Natural Items
**Examples**: Plants, trees, rocks, mushrooms, coral, alien egg sacs, vines, grass clumps, flowers, debris, crystals.

**Characteristics**: Irregular shapes. Look wrong when perfectly aligned. Benefit from randomness. Often clustered in groups.

**Placement rules**:
- **Intentional overlap** — 10-30% overlap between items in clusters looks natural
- **Random rotation** — full 360° rotation variety. No two adjacent items should face the same way
- **Scale variation** — ±15-25% random scale variation within a group
- **Position jitter** — offset from grid by ±5-15% of item width
- **Y variation** — slight Y offset (±0.05m) simulates uneven terrain
- **Cluster, don't grid** — organic items grow in clusters, not rows

```python
import random

def scatter_organic(catalog_key, center, count, radius, base_scale=1.0):
    """Scatter organic items naturally around a center point."""
    for _ in range(count):
        angle = random.uniform(0, 360)
        dist = random.uniform(0, radius) ** 0.5 * radius  # sqrt for even distribution
        x = center[0] + dist * math.sin(math.radians(angle))
        z = center[2] + dist * math.cos(math.radians(angle))
        y = center[1] + random.uniform(-0.05, 0.05)
        rot = random.uniform(0, 360)
        scale = base_scale * random.uniform(0.8, 1.2)
        place(catalog_key, (x, y, z), facing_deg=rot, scale=scale)
```

### Connectable / Seamless Items
**Examples**: Alien walls, cave walls, fence segments, pipe sections, organic corridors, bridge segments, terrain borders.

**Characteristics**: Need to connect end-to-end without visible gaps. May not be geometrically precise like modular kits. Overlap at joints is acceptable and often desirable to hide seams.

**Placement rules**:
- **Overlap at joints** — 5-15% overlap at connection points hides seams
- **Match end profiles** — rotate pieces so their connection edges align
- **Slight rotation variation** — ±2-5° on non-connecting axes adds natural feel
- **Scale consistency** — keep uniform scale so connections line up
- **Fill gaps with detail** — place small decorative items (vines, moss, debris) at joints

```python
# Alien wall segments with slight overlap
wall_length = get_width("alien_wall") * SCALE
overlap = wall_length * 0.1  # 10% overlap at joints
effective_step = wall_length - overlap

for i in range(num_segments):
    x = start_x + i * effective_step
    # Slight Y and rotation variation for organic feel
    y_jitter = random.uniform(-0.02, 0.02) * SCALE
    rot_jitter = random.uniform(-3, 3)
    place("alien_wall", (x, y_jitter, wall_z),
          facing_deg=base_facing + rot_jitter, scale=SCALE)
```

### Furniture & Functional Items
**Examples**: Chairs, tables, desks, beds, shelves, workstations, counters, bars, podiums.

**Characteristics**: Must be scaled relative to avatar height (see Avatar-Relative Scaling in glb-asset-catalog.md). Positioned for usability — chairs face tables, desks face open space.

**Placement rules**:
- **Avatar-scaled** — always scale to match 1.0-1.6m avatar proportions
- **Functional positioning** — chairs face tables, screens face seating, doors align with walls
- **Comfortable spacing** — leave 0.5-1.0m between seated positions for avatar clearance
- **Slight imperfection** — in casual spaces, offset chairs ±5° and ±0.1m from perfect alignment. In formal spaces (boardroom, theater), keep precise alignment
- **Group by function** — dining set, lounge area, workspace, reception desk

### Decorative / Accent Items
**Examples**: Posters, signs, lighting fixtures, vases, trophies, monitors, clocks, paintings, flags, banners.

**Characteristics**: Secondary to the scene's main structure. Add character and detail. Often wall-mounted or placed on surfaces.

**Placement rules**:
- **Surface-mounted** — calculate Y position from the surface below: `surface_y + item_height/2`
- **Wall-mounted** — align Z or X with the wall face, offset by item depth/2
- **Eye-level placement** — signs, screens, and art at avatar eye height (~1.3-1.5m)
- **Varied heights** — don't put all decorations at the same Y. Stagger.
- **Don't overcrowd** — less is more. 3 well-placed decorations beat 12 crammed ones

---

## Scene Composition

### Zones

Every scene should be divided into **zones** — distinct areas with a purpose. Zones drive the component breakdown in the build manifest.

```
Zone types:
- Focal point     — the thing players look at first (stage, monument, boss arena)
- Activity zone   — where gameplay happens (obstacle course, puzzle room, battle arena)
- Transition zone — corridors, paths, bridges between areas
- Rest zone       — safe areas, spawn, shops, social spaces
- Background      — distant scenery, skybox framing, horizon detail
```

Design the zone layout during the design phase. Each zone can become a component or sub-component.

### Visual Hierarchy

Players should instantly understand:
1. **Where am I?** — Environment type (forest, city, space station)
2. **Where do I go?** — Clear paths, lighting draws the eye, openings invite exploration
3. **What matters?** — Important items are larger, brighter, more detailed, or isolated

Achieve this through:
- **Scale contrast** — important things are bigger
- **Lighting contrast** — bright areas draw attention, dark areas feel mysterious
- **Color contrast** — key items stand out from background palette
- **Negative space** — empty space around important items makes them pop
- **Framing** — walls, arches, or vegetation frame the focal point

### Sightlines

Design what the player sees from key positions:

- **From spawn** — player should see the first objective or path forward
- **From each zone** — player should see at least one adjacent zone or waypoint
- **Block unfinished areas** — use walls, fog, or terrain to hide empty space

### Hero Moments

Every game needs 2-3 moments where the player stops moving and looks around. These are the screenshots, the moments they tell friends about. Design them intentionally — they don't happen by accident.

**Three types of hero moment:**

- **The Reveal** — A transition that opens into a dramatically larger or more impressive space. The player walks through a narrow corridor and emerges into a vast cavern. The contrast between confined and open creates awe.
- **The Vista** — A high point where the player can see the whole world laid out. They see where they've been, where they're going, and how it all connects. This rewards exploration and creates a sense of scale.
- **The Transformation** — A moment when the environment visibly changes around the player. Lights come on, fog clears, the skybox shifts, music swells. The world reacts to what the player did.

**What makes a hero moment work:**
- **Scale contrast** — suddenly bigger (or dramatically smaller)
- **Lighting contrast** — suddenly brighter, or dramatically different color temperature
- **Audio shift** — new music, or silence after noise, or a single dramatic sound
- **Negative space** — emptiness around the impressive thing makes it pop
- **Timing** — the moment should follow effort (a climb, a puzzle, a boss) so it feels earned

### Density Gradient

Scenes feel natural when detail density varies:

```
High density  → focal points, activity zones, decorative clusters
Medium density → paths, transitions, functional areas
Low density   → backgrounds, open fields, negative space
```

A scene at uniform density everywhere feels flat. Vary it.

### Detail Layers

Every zone should have items at four layers of detail:

| Layer | What it includes | Purpose | Examples |
|-------|-----------------|---------|----------|
| **Structural** | Walls, floors, ceilings, major geometry | The bones of the space | Wall panels, floor tiles, pillars, railings |
| **Functional** | Gameplay items, interactables, triggers, collectibles | The game itself | Platforms, doors, buttons, crystals, checkpoints |
| **Atmospheric** | Particles, fog, ambient lights, ambient sounds, skybox effects | The mood and feeling | DustParticles, fog zones, colored point lights, ambient loops |
| **Decorative** | Props, clutter, environmental storytelling objects, signs, vegetation | The life and character | Posters, debris, overturned chairs, plant clusters, stains |

A zone with only structural and functional items feels like a test level — geometry exists, mechanics work, but nothing feels real. Adding atmospheric items creates mood. Adding decorative items creates believability.

**During the build manifest phase**, each component should note which layers it covers. During the quality review, gaps in layers are the first thing to check.

**Common gaps to watch for:**
- Atmospheric layer missing entirely (no particles, no fog, no ambient light variation)
- Decorative layer is uniform (same item repeated without variety)
- Functional layer has no feedback (triggers exist but produce no visual/audio response)

---

## Variety Techniques

### Rotation Variety

**Grid-aligned items** (modular): 0°, 90°, 180°, 270° only.

**Furniture**: Base direction faces the functional target (table, screen), then ±0-10° jitter for casual spaces. No jitter for formal spaces.

**Organic**: Full 360° random rotation. Every instance should be different.

**Decorative**: Face the viewer or the room center. Slight tilt for personality.

### Scale Variety

| Asset Type | Scale Variation | Notes |
|------------|----------------|-------|
| Modular kit | None (0%) | Must tile precisely |
| Connectable | None (0%) | Must connect at joints |
| Furniture | Minimal (±5%) | Keep proportional to avatar |
| Organic | Moderate (±15-25%) | Natural growth variation |
| Decorative | Moderate (±10-20%) | Adds visual interest |
| Rocks/terrain | High (±20-40%) | Geology varies wildly |

### Position Jitter

Add small random offsets to break grid patterns:

```python
def jitter(base_pos, amount=0.1):
    """Add random position offset to break grid feel."""
    return (
        base_pos[0] + random.uniform(-amount, amount),
        base_pos[1],  # usually keep Y stable
        base_pos[2] + random.uniform(-amount, amount)
    )
```

- Modular: **no jitter** (must align)
- Furniture: **0.05-0.15m** in casual spaces, **none** in formal
- Organic: **10-20% of item width**
- Decorative: **0.02-0.08m** for subtle imperfection

### Color/Material Variation

When multiple instances of the same item exist, vary them:
- Use different catalog items from the same category (3 chair styles instead of 1)
- If only one model, vary scale and rotation to de-emphasize repetition
- For ResizableCubes, vary color hex slightly (e.g., "2a2a3e", "2c2c40", "282838")

---

## Common Scene Recipes

### Forest / Organic Environment
```
Ground: Floor tiles at large scale, slight Y variation between tiles
Trees: scatter_organic() with 3-4 tree types, scale 0.6-1.4, full rotation
Undergrowth: Dense scatter of small plants, 20-30% overlap, clustered near trees
Rocks: 2-3 sizes, scatter with high scale variation (±30%)
Path: ResizableCubes as path segments, or modular path tiles, precise alignment
Lighting: Scattered point lights with warm tones, low intensity, canopy shadows
```

### Sci-Fi Corridor
```
Structure: Modular wall panels, precise grid alignment, no gaps
Floor: Modular tiles, exact tiling, consistent scale
Lighting: Evenly spaced spotlights or light strips, cool blue/white tones
Pipes/cables: Connectable segments along walls, slight Z offset from wall face
Details: Screens, signs, vents at irregular intervals (not every panel)
Accent: Colored emission cubes for status lights, warning stripes
```

### Alien/Fantasy Interior
```
Walls: Connectable organic wall segments, 10% overlap, ±3° rotation jitter
Floor: Organic tiles or resizable cubes with irregular color variation
Vegetation: Organic scatter — alien plants, bioluminescent items, egg sacs
Lighting: Colored point lights (purple, green, amber), varied intensity
Props: Asymmetric placement, nothing perfectly centered, clusters of 3-5
Atmosphere: Mix of empty cavern space and dense detail clusters
```

### City / Urban
```
Ground: Precise modular road and sidewalk tiles
Buildings: Modular or unique GLBs, grid-aligned to road, varied heights
Street props: Lamps, benches, bins — placed along sidewalk with regular but not rigid spacing
Vegetation: Trees in planters (precise base, organic canopy), flower beds (organic scatter)
Signs: Wall-mounted at eye level, facing street/sidewalk
Detail density: High near ground level, decreasing with height
```

### Interior / Lounge
```
Furniture: Avatar-scaled, grouped by function (seating cluster, dining set, bar area)
Lighting: Mix of overhead and accent, warm tones, varied brightness per zone
Decorations: Wall art at eye level, plants in corners, objects on surfaces
Floor: Single material or large tiles, consistent
Casual feel: ±5° chair rotation, slight position offsets, asymmetric layout
```

---

## Spatial Navigation & Clearance Rules

These rules prevent players from getting stuck, blocked, or frustrated by geometry that looks fine from above but is impassable at ground level.

### Doorway Clearance

Walls must not cover or overlap doorways. If a wall segment spans the same position as a door frame, shorten or split the wall to leave the doorway fully open. A door that is visually present but physically blocked by a wall is worse than no door at all — the player sees a path but can't use it.

- **Check every doorway** after placing walls. Verify the opening is unobstructed on both sides.
- **Wall-to-door alignment**: If using modular walls, plan the segment layout so door positions fall at segment boundaries, not mid-panel.
- **Minimum clearance**: The full width and height of the door frame must be clear of any geometry.

### Walking Space Near Doors

Never place items directly in front of or behind a doorway. When a player walks through a door, they need at least **1.5-2.0m of clear floor space** on both sides before encountering furniture, decorations, or obstacles. Items placed immediately at a door's threshold create a frustrating collision that stops the player the moment they enter.

- **1.5m minimum clearance** in front of and behind every door
- **No items in the doorway approach path** — imagine a 1.5m-wide, 2.0m-deep rectangle extending from each side of the door. Keep it empty.
- **Exceptions**: Flat floor items (rugs, floor markings) that don't have collision are fine.

```python
# When placing furniture near a door, enforce clearance
DOOR_CLEARANCE = 2.0  # meters of clear space on each side of door

def is_too_close_to_door(item_pos, door_pos, door_facing_deg):
    """Check if an item is in the door's approach zone."""
    dx = item_pos[0] - door_pos[0]
    dz = item_pos[2] - door_pos[2]
    # Rotate into door's local space
    rad = math.radians(door_facing_deg)
    local_forward = dx * math.sin(rad) + dz * math.cos(rad)
    local_side = dx * math.cos(rad) - dz * math.sin(rad)
    # Check if within the approach rectangle
    return abs(local_side) < 0.75 and abs(local_forward) < DOOR_CLEARANCE
```

### Wall-Mounted Items

Items that belong on walls (pictures, vents, AC units, screens, clocks, signs, shelves) must be placed on the **correct side** of the wall — the interior side for interior items, the exterior side for exterior items. They should sit flush against or slightly proud of the wall surface, never clipping through it.

- **Interior items** (art, shelves, screens, clocks): Place on the room-facing side of the wall. Offset from the wall center by `wall_depth/2 + item_depth/2` toward the room interior.
- **Exterior items** (signs, vents, AC units, exterior lights): Place on the outside-facing side. Offset from wall center by `wall_depth/2 + item_depth/2` toward the exterior.
- **Facing direction**: Wall-mounted items should face away from the wall (into the room for interior, outward for exterior).
- **No deep clipping**: A small amount of contact/overlap at the mount point is fine, but the item's visible face and body must not penetrate the wall.

```python
def wall_mount_offset(wall_pos, wall_normal_deg, wall_depth, item_depth, interior=True):
    """Calculate position for a wall-mounted item.

    Args:
        wall_pos: (x, y, z) center of the wall segment
        wall_normal_deg: direction the wall's interior face points (degrees)
        wall_depth: wall thickness in meters
        item_depth: item depth in meters
        interior: True = mount on interior side, False = exterior
    """
    rad = math.radians(wall_normal_deg)
    sign = 1 if interior else -1
    offset = sign * (wall_depth / 2 + item_depth / 2)
    return (
        wall_pos[0] + offset * math.sin(rad),
        wall_pos[1],  # set Y separately for height
        wall_pos[2] + offset * math.cos(rad)
    )
```

---

## Integration with Build Workflow

### During Design Phase

When writing `design.md`, specify for each zone:
- **Asset classification** — what type of placement each major element needs
- **Density** — high/medium/low detail density
- **Variety level** — formal (precise) vs casual (jittered) vs organic (scattered)
- **Key sightlines** — what should be visible from where

### In the Build Manifest

Each component's manifest entry should include:
```markdown
**Placement strategy**: organic scatter / modular grid / connectable / furniture arrangement
**Variety**: rotation ±X°, scale ±Y%, position jitter ±Zm
**Density**: high / medium / low
```

This tells the subagent exactly how to place items without needing to infer it.

### In Subagent Prompts

Include the relevant section of this document in each subagent's prompt. For example:
- Environment subagent gets: "Organic / Natural Items" + "Scatter Organic" recipe + zone composition rules
- Modular structure subagent gets: "Modular Kit Pieces" + precise alignment rules
- Furniture subagent gets: "Furniture & Functional Items" + avatar scaling reference

Don't send the whole document — send only the placement strategy section that matches the component's asset types.

---

## Helper Functions

These should be available in generation scripts for common placement patterns:

```python
import random
import math

def scatter_organic(catalog_key, center, count, radius,
                    base_scale=1.0, scale_var=0.2, y_var=0.05,
                    place_fn=None):
    """Scatter items naturally around a center point.

    Args:
        catalog_key: item key in catalog.json
        center: (x, y, z) center of scatter area
        count: number of items to place
        radius: scatter radius in meters
        base_scale: base scale factor
        scale_var: ±variation as fraction (0.2 = ±20%)
        y_var: ±Y offset in meters
        place_fn: the place() function to call
    """
    for _ in range(count):
        angle = random.uniform(0, 360)
        dist = math.sqrt(random.random()) * radius
        x = center[0] + dist * math.sin(math.radians(angle))
        z = center[2] + dist * math.cos(math.radians(angle))
        y = center[1] + random.uniform(-y_var, y_var)
        rot = random.uniform(0, 360)
        s = base_scale * random.uniform(1 - scale_var, 1 + scale_var)
        place_fn(catalog_key, (x, y, z), facing_deg=rot, scale=s)


def place_row(catalog_key, start, direction, count, spacing,
              facing_deg=0, scale=1.0, jitter=0, rot_jitter=0,
              place_fn=None):
    """Place items in a row with optional jitter.

    Args:
        start: (x, y, z) first item position
        direction: (dx, dz) direction vector (will be normalized)
        count: number of items
        spacing: distance between items in meters
        jitter: ±position offset in meters (0 for precise)
        rot_jitter: ±rotation offset in degrees (0 for precise)
    """
    length = math.sqrt(direction[0]**2 + direction[1]**2)
    dx, dz = direction[0]/length, direction[1]/length
    for i in range(count):
        x = start[0] + i * spacing * dx + random.uniform(-jitter, jitter)
        z = start[2] + i * spacing * dz + random.uniform(-jitter, jitter)
        y = start[1]
        rot = facing_deg + random.uniform(-rot_jitter, rot_jitter)
        place_fn(catalog_key, (x, y, z), facing_deg=rot, scale=scale)


def place_circle(catalog_key, center, radius, count,
                 face_center=True, scale=1.0, place_fn=None):
    """Place items in a circle, optionally facing center.

    Args:
        center: (x, y, z) center point
        radius: circle radius in meters
        count: number of items around the circle
        face_center: if True, items face the center point
    """
    for i in range(count):
        angle = (360 / count) * i
        x = center[0] + radius * math.sin(math.radians(angle))
        z = center[2] + radius * math.cos(math.radians(angle))
        if face_center:
            # Face toward center
            facing = math.degrees(math.atan2(-math.sin(math.radians(angle)),
                                             -math.cos(math.radians(angle))))
        else:
            facing = angle
        place_fn(catalog_key, (x, center[1], z), facing_deg=facing, scale=scale)


def place_grid(catalog_key, origin, rows, cols, spacing_x, spacing_z,
               facing_deg=0, scale=1.0, jitter=0, place_fn=None):
    """Place items in a grid pattern.

    Args:
        origin: (x, y, z) corner of grid
        rows: number of rows (Z axis)
        cols: number of columns (X axis)
        spacing_x: X spacing in meters
        spacing_z: Z spacing in meters
        jitter: ±position offset (0 for modular/precise)
    """
    for row in range(rows):
        for col in range(cols):
            x = origin[0] + col * spacing_x + random.uniform(-jitter, jitter)
            z = origin[2] + row * spacing_z + random.uniform(-jitter, jitter)
            place_fn(catalog_key, (x, origin[1], z),
                     facing_deg=facing_deg, scale=scale)
```

These helpers should be added to `lib/portals_core.py` or used inline in components that need them.
