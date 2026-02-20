# GLB Asset Catalog System

How to upload, catalog, and arrange GLB 3D models in Portals rooms. This workflow ensures items are correctly sized, spaced, rotated, and organized every time.

**IMPORTANT**: Always follow this process when placing GLB models. Do not eyeball positions or guess dimensions — use the catalog for real measurements.

---

## Overview

The asset catalog system solves three problems:
1. **Sizing** — Know exact item dimensions for proper spacing
2. **Rotation** — Place items facing the correct direction
3. **Organization** — Track uploaded assets with names, categories, and CDN URLs

Every room with GLB assets should have a `catalog.json` in its `games/{room-id}/` folder.

---

## The Full Workflow

### Step 1: Upload GLBs to CDN

Use the MCP upload tools to get CDN URLs:

```python
# Single file
mcp.upload_glb(filePath="/path/to/model.glb")

# Entire folder
mcp.upload_glbs_from_folder(folderPath="/path/to/folder/")
```

Save the returned CDN URLs — you'll need them for the catalog.

### Step 2: Extract Metadata

Run the extraction tool on the GLB files:

```bash
python tools/extract_glb_metadata.py /path/to/glbs room-id
```

This produces:
- `games/{room-id}/catalog.json` — item metadata (AABB, size, center, PCA, triangle count)
- `games/{room-id}/thumbnails/` — 4-view PNG renders of each item

If you already have CDN URLs, pass them:
```bash
python tools/extract_glb_metadata.py /path/to/glbs room-id --cdn-urls urls.json
```

### Step 3: Review Thumbnails and Populate Catalog

Read the thumbnail PNGs to identify each item, then update the catalog with:
- **name** — Human-readable name (e.g., "Cosmic Comfy Chair Orange")
- **description** — Brief description for hover text
- **category** — Item type (seat, table, decoration, lighting, wall, floor, prop, etc.)
- **url** — CDN URL from Step 1
- **front** — Front direction vector (usually `[0, 0, -1]` in glTF space)

**Tagging structural pieces:** While reviewing thumbnails, any item that is a structural building component — a wall, corridor, corner, doorway, floor tile, room, intersection, end cap, gate, ramp, or staircase — should get `modular` fields (piece type, edge classifications, grid footprint). This applies even if there's only one such piece in the batch. See the Modular Kit Reference section below.

**If multiple structural pieces share a grid** (e.g., several corridor/wall/corner pieces with matching footprint dimensions), also add top-level `modular_kit` metadata to the catalog (grid size, level height, precision). This enables the `ModularKit` grid placement helpers.

Write a small update script (like `update_catalog.py`) to batch-populate these fields.

### Step 4: Write the Generation Script

Create `games/{room-id}/generate.py` that reads `catalog.json` for real dimensions. See the Generation Script Template section below.

**For modular kits:** Use `ModularKit` from `lib/modular_helpers.py` instead of manual placement. This gives you grid-based placement, edge-aware rotation, and layout validation. See the Modular Kit Reference section below.

### Step 5: Generate and Push

```bash
python games/{room-id}/generate.py
```

**For modular kits:** Run `kit.validate_layout()` before pushing. Fix any overlap or open-edge warnings first.

Then push via MCP:
```python
mcp.set_room_data(roomId="room-id", filePath="games/{room-id}/snapshot.json")
```

---

## Catalog Schema

```json
{
  "room_id": "{room-id}",
  "items": {
    "item_key": {
      "name": "Cosmic Comfy Chair",
      "description": "Padded lounge chair with low back, grey upholstery",
      "category": "seat",
      "url": "https://d365bxku1h71bo.cloudfront.net/uploads/gltf/...",
      "source_file": "Cosmic_retro_mesa_chair_comfy.glb",
      "units": "meters",
      "up_axis": "Y",
      "front": [0, 0, -1],
      "aabb": {
        "min": [-0.4001, 0.0, -0.4498],
        "max": [0.4001, 1.1113, 0.4129]
      },
      "size": [0.8002, 1.1113, 0.8627],
      "center": [0.0, 0.5557, -0.0185],
      "pivot": [0.0, 0.0, 0.0],
      "footprint": [0.8002, 0.8627],
      "pca_axes": [[...], [...], [...]],
      "pca_extents": [1.3116, 0.8002, 0.8394],
      "triangles": 324
    }
  }
}
```

### Field Reference

| Field | Description |
|-------|-------------|
| `name` | Human-readable display name (used for hover text) |
| `description` | Brief description (used for hover body) |
| `category` | Item type for grouping: seat, table, stool, decoration, lighting, wall, floor, prop |
| `url` | CDN URL for the GLB file |
| `source_file` | Original filename for reference |
| `size` | Bounding box dimensions `[width_X, height_Y, depth_Z]` in meters |
| `aabb` | Axis-aligned bounding box min/max corners |
| `center` | Geometric center of the model |
| `pivot` | Pivot/origin point (usually `[0, 0, 0]`) |
| `footprint` | Ground-plane dimensions `[width_X, depth_Z]` for spacing |
| `front` | Front direction in glTF space (usually `[0, 0, -1]`) |
| `pca_axes` | Principal component axes (useful for odd-shaped items) |
| `pca_extents` | Extent along each PCA axis |
| `triangles` | Face count (keep under 15,000 for performance) |
| `file_size_bytes` | GLB file size in bytes (used by storage check) |

### Modular Kit Fields

When a catalog contains modular pieces, add a top-level `modular_kit` key and per-item `modular` fields:

```json
{
  "room_id": "abc-123",
  "modular_kit": {
    "grid_size": [4.0, 4.0],
    "level_height": 4.25,
    "precision": "snug",
    "kit_name": "Sci-Fi Corridors",
    "piece_count": 18
  },
  "items": {
    "corridor_corner": {
      "name": "Corridor Corner",
      "category": "structure",
      "url": "https://cdn.example.com/corridor_corner.glb",
      "size": [4.02, 4.25, 3.98],
      "modular": {
        "grid_footprint": [1, 1],
        "piece_type": "corner",
        "edges": {
          "+x": ["closed"],
          "-x": ["open"],
          "+z": ["open"],
          "-z": ["closed"]
        },
        "default_rotation": 0,
        "tags": ["corridor", "structural"]
      }
    }
  }
}
```

| Field | Type | Description |
|---|---|---|
| `modular_kit.grid_size` | `[float, float]` | Nominal XZ grid unit in meters (read from most common footprint) |
| `modular_kit.level_height` | `float` | Vertical spacing per level (height of tallest structural piece) |
| `modular_kit.precision` | `string` | `exact` (<2% deviation), `snug` (<5%), or `loose` (<10%) |
| `modular_kit.kit_name` | `string` | Human-readable kit name |
| `modular_kit.piece_count` | `int` | Number of modular items in catalog |
| `modular.grid_footprint` | `[int, int]` | Size in grid cells `[W, D]` |
| `modular.piece_type` | `string` | `straight`, `corner`, `t_junction`, `intersection`, `end_cap`, `enclosed`, or `room` |
| `modular.edges` | `dict` | Edge state per cardinal direction — see Modular Kit Reference |
| `modular.default_rotation` | `int` | Rotation steps (0-3) if the piece needs a base rotation |
| `modular.tags` | `[string]` | Freeform tags for filtering (e.g., `["corridor"]`, `["room"]`, `["gate"]`) |

Non-modular items in the same catalog simply have no `modular` key.

---

## GLB Rotation in Portals (CONFIRMED)

This is the most critical section. Getting rotation wrong makes scenes look broken.

### The Rule

**GLB models face +Z in Portals/Unity** after the glTF-to-Unity Z-axis flip on import. In raw glTF files, models face -Z. But Portals runs in Unity (left-handed coordinates), which negates Z on import.

### Quaternion Formula

```python
def yrot(deg):
    """Quaternion for Y-axis rotation in degrees."""
    r = math.radians(deg)
    return {
        "x": 0,
        "y": round(math.sin(r / 2), 6),
        "z": 0,
        "w": round(math.cos(r / 2), 6)
    }
```

### Facing Direction

`yrot(θ)` applied to the model's front vector `(0, 0, 1)` produces direction `(sin θ, 0, cos θ)`.

To make an item face a target direction: **`θ = atan2(target_x, target_z)`**

| Direction | facing_deg |
|-----------|-----------|
| Face +Z (away from camera) | 0° |
| Face +X (right) | 90° |
| Face -Z (toward camera) | 180° |
| Face -X (left) | -90° |
| Face diagonal (+X, +Z) | 45° |
| Face diagonal (-X, -Z) | -135° |

### Practical Examples

```python
# Chair on -X side of table, facing +X toward table center
place("chair", (-2, 0, 0), facing_deg=90)

# Chair on +X side of table, facing -X toward table center
place("chair", (2, 0, 0), facing_deg=-90)

# Sofa along back wall (+Z), facing -Z toward room center
place("sofa", (0, 0, 10), facing_deg=180)

# Chair in front of desk, facing +Z toward desk
place("chair", (0, 0, -2), facing_deg=0)

# Bean bag in corner (-X, -Z), facing center (+X, +Z)
# Direction to center: atan2(1, 1) = 45°
place("beanbag", (-3, 0, -3), facing_deg=45)
```

### Items Facing Each Other Across a Table

```python
# Table at (6, 0.35, -7)
# Chair A on -Z side, facing +Z (toward table) → 0°
place("chair_a", (6, 0, -7 - offset), facing_deg=0)
# Chair B on +Z side, facing -Z (toward table) → 180°
place("chair_b", (6, 0, -7 + offset), facing_deg=180)
```

### Wall and Panel Rotation

Walls are the most common source of rotation errors. The key insight: **a wall's "front" is its detailed/textured face**. At yaw=0°, that face points +Z. You want the detailed face to point **inward** (toward the room interior).

**The rule:** Determine which direction is "inward" from the wall's position, then apply the standard rotation formula.

| Wall position | Interior direction | Rotation |
|---|---|---|
| South boundary (low Z) | +Z (into room) | yaw=0° |
| North boundary (high Z) | -Z (into room) | yaw=180° |
| East boundary (high X) | -X (into room) | yaw=270° / -90° |
| West boundary (low X) | +X (into room) | yaw=90° |

**Common mistake:** Swapping east/west or north/south rotations, which puts the detailed face OUTWARD. This makes every wall look "inside-out" — the plain back faces the room interior.

```python
# Room: x=0..10, z=0..8
# South wall at z=0 — face +Z into room
place_wall(x=5, z=0, facing_deg=0)

# North wall at z=8 — face -Z into room
place_wall(x=5, z=8, facing_deg=180)

# East wall at x=10 — face -X into room
place_wall(x=10, z=4, facing_deg=-90)

# West wall at x=0 — face +X into room
place_wall(x=0, z=4, facing_deg=90)
```

**Wall-mounted items** (lamps, AC units, panels) follow the same rule — their front faces AWAY from the wall, into the room. A lamp on the west wall (low X) faces +X.

### Rotation by Item Category

| Category | "Front" is... | Faces toward... |
|---|---|---|
| **Walls/panels** | Detailed/textured side | Room interior |
| **Chairs/seats** | Where you sit from | The desk/table they serve |
| **Consoles/monitors** | Screen side | The operator position |
| **Wall-mounted items** | Display/emitting side | Away from wall, into room |
| **Vending machines** | Interaction panel | Room interior / approach path |
| **Beds/bunks** | Long side you approach from | Room center |
| **Cabinets/lockers** | Door side | Room center |
| **Symmetric items** | N/A | Rotation matters less |

---

## Z-up vs Y-up Asset Placement

GLB files can have different coordinate systems depending on the tool that created them. The extraction tool (`extract_glb_metadata.py`) reads raw vertices, which may use a different "up" axis than Portals/Unity. Getting this wrong causes items to float meters above their intended position or sink below the ground.

### Identifying the Coordinate System

- **Z-up assets** (Blender, ZARN, many DCC tools): Raw AABB has Z as the vertical axis. The `up_axis` field in `catalog.json` will be `"Z"`.
- **Y-up assets** (game-ready, some exporters): Raw AABB already uses Y as vertical. The `up_axis` field will be `"Y"`.

### How Unity Handles Z-up

Unity's glTF importer applies a root-node +90° X rotation to convert Z-up to Y-up. This effectively maps:
- `Unity_Y = -catalog_Z` (the Z axis gets negated and becomes Y)
- `Unity_X = catalog_X` (unchanged)
- `Unity_Z = catalog_Y` (swapped)

This negation is critical — it **inverts** which end of the Z-axis AABB maps to the top vs bottom in Unity.

### Placement Formulas

**Z-up assets (Blender/ZARN):**
```python
# Ground placement (bottom of model at Y=0):
pos_y = aabb_max[2] * scale   # NOT -aabb_min[2] * scale

# Surface placement (top of model at Y=0, e.g. hanging from ceiling):
pos_y = aabb_min[2] * scale   # NOT -aabb_max[2] * scale
```

**Y-up assets (already correct orientation):**
```python
# Ground placement (bottom of model at Y=0):
pos_y = -aabb_min[1] * scale

# Surface placement (top of model at Y=0):
pos_y = -aabb_max[1] * scale
```

### Why the Sign Matters

For a typical Z-up asset where the model sits above the origin:
- `aabb_min[2]` might be `0.0` (bottom of model at Z=0)
- `aabb_max[2]` might be `1.5` (top of model at Z=1.5)

After Unity's Z-negation, the bottom in Unity space is at `-aabb_max[2]` and the top is at `-aabb_min[2]`. To place the bottom at Y=0, you offset by `aabb_max[2] * scale` (positive value, pushing the model up so its bottom touches ground).

Using the wrong formula (`-aabb_min[2] * scale`) would give `0.0` — which seems right for this example but fails when models have non-zero `aabb_min[2]` values, causing items to float 3-5m too high.

### Helper Function

```python
def ground_y(catalog_key, scale=1.0):
    """Calculate Y position to place model bottom at ground level."""
    entry = items_db[catalog_key]
    if entry.get("up_axis") == "Z":
        return entry["aabb"]["max"][2] * scale
    else:  # Y-up
        return -entry["aabb"]["min"][1] * scale
```

---

## Floor Tile Placement

GLB floor tiles have geometry height that matters at large scales.

### The Problem

A floor tile with AABB height 0.054m at scale 1 is negligible. But at scale 8:
- Tile top surface = 0.054 × 8 = **0.43m above the placement Y**
- All furniture at Y=0 ends up embedded in the floor

### The Fix

Place floor tiles below Y=0 so their top surface aligns with the ground plane:

```python
FLOOR_TILE_HEIGHT = 0.0545  # from AABB max Y
FLOOR_SCALE = 8
FLOOR_Y = -(FLOOR_TILE_HEIGHT * FLOOR_SCALE)  # -0.436

# Place floor tile
pos = {"x": 0, "y": FLOOR_Y, "z": 0}
scale = {"x": FLOOR_SCALE, "y": FLOOR_SCALE, "z": FLOOR_SCALE}
```

### Seamless Tiling

Floor tiles must be spaced exactly: `spacing = tile_width × scale`

```python
TILE_WIDTH = 0.5  # raw tile width in meters
FLOOR_STEP = TILE_WIDTH * FLOOR_SCALE  # 4m per tile at scale 8

for fx in range(-3, 4):
    for fz in range(-3, 4):
        place_floor(fx * FLOOR_STEP, FLOOR_Y, fz * FLOOR_STEP)
```

---

## Modular Kit Reference

Any structural building component — even a single wall or doorway — benefits from modular metadata (edge classifications, piece type). When multiple structural pieces share a common grid, you also get kit-level helpers for grid-based placement and validation. This section covers the edge model, how to classify pieces during thumbnail review, and the generation helpers.

### Core Model

Every modular piece occupies one or more grid cells. At rotation 0, each cardinal edge is classified:

- **open** — passage / connection point
- **closed** — solid wall / barrier
- **partial** — archway, window, half-wall

The combination of open/closed edges defines the piece type:

| Open edges | Pattern | Type |
|---|---|---|
| 2 opposite | `--` | `straight` |
| 2 adjacent | `L` | `corner` |
| 3 | `T` | `t_junction` |
| 4 | `+` | `intersection` |
| 1 | dead end | `end_cap` |
| 0 | box | `enclosed` |

Multi-cell pieces (grid footprint larger than 1x1) are classified as `room`.

### Edge Arrays

Edges are arrays with one entry per grid cell along that wall. For a piece with `grid_footprint: [W, D]`:

- `+z` and `-z` edges have **W** entries (left to right along X)
- `+x` and `-x` edges have **D** entries (front to back along Z)

A 1x1 piece has length-1 arrays everywhere. Example — a 3x3 room with a door in the middle of the +Z wall:

```json
{
  "grid_footprint": [3, 3],
  "edges": {
    "+z": ["closed", "open", "closed"],
    "-z": ["closed", "closed", "closed"],
    "+x": ["closed", "closed", "closed"],
    "-x": ["closed", "closed", "closed"]
  }
}
```

### Classifying Pieces During Thumbnail Review

During Step 3 (thumbnail review), identify structural pieces visually. Tag **every** item that is a wall, corridor, corner, room, doorway, gate, ramp, floor tile, end cap, intersection, or staircase — even if it's the only one in the batch.

For each structural piece:

1. **Look at the thumbnail** — what is it? A wall, corridor, corner, room, doorway?
2. **Classify edges** — for each cardinal direction (+x, -x, +z, -z), is the edge open (passage), closed (wall), or partial (archway/window)?
3. **Determine piece type** — count open edges and use the table above.
4. **Set grid footprint** — `[1, 1]` for standard single-cell pieces. For larger pieces, divide by the grid size (e.g., 8m piece on a 4m grid = `[2, 1]`).

If there are **multiple structural pieces with matching footprint dimensions**, they form a kit:

5. **Determine grid size** — the most common footprint dimension across the structural pieces (e.g., most are ~4m x 4m → grid is `[4.0, 4.0]`).
6. **Note precision** — compare actual dimensions to the grid. Within 2% = `exact`, within 5% = `snug`, within 10% = `loose`.
7. **Add `modular_kit` top-level metadata** to the catalog — this enables the `ModularKit` grid placement helpers.

### Edge Rotation

The catalog records edges at rotation 0 only. Use `rotated_edges()` to get edges at other rotations:

```python
from modular_helpers import rotated_edges

edges = {"+z": ["open"], "+x": ["closed"], "-z": ["closed"], "-x": ["open"]}

rotated_edges(edges, 0)  # unchanged
rotated_edges(edges, 1)  # 90 CW: open moves to +z and +x
rotated_edges(edges, 2)  # 180: open moves to -z and +x
rotated_edges(edges, 3)  # 270: open moves to -z and -x
```

For multi-cell pieces, arrays reverse on odd rotation steps to account for mirroring.

### Generation Helpers

Located in `lib/modular_helpers.py`. Import into generation scripts:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))
from modular_helpers import ModularKit, rotated_edges, find_piece
```

#### `ModularKit` Class

Orchestrates grid-based placement:

```python
kit = ModularKit(
    grid_size=catalog["modular_kit"]["grid_size"],
    level_height=catalog["modular_kit"]["level_height"],
    catalog_items=catalog["items"]
)
kit.place_fn = lambda key, pos, facing_deg, scale: place(key, pos, facing_deg=facing_deg, scale=scale)
```

| Method | Purpose |
|---|---|
| `kit.place_mod(key, gx, gz, rot_steps, level)` | Place single piece on grid |
| `kit.place_room(key, anchor_gx, anchor_gz, rot_steps, level)` | Place multi-cell room (anchor = -X, -Z corner) |
| `kit.place_corridor_run(key, start_gx, start_gz, direction, length)` | Place straight corridor run |
| `kit.validate_layout()` | Check for overlaps, disconnected edges |

World position is calculated as: `x = gx * grid_size[0]`, `z = gz * grid_size[1]`, `y = level * level_height`.

Direction mapping for corridor runs:

| Direction | Grid step | rot_steps |
|---|---|---|
| `"+x"` | (1, 0) | 1 |
| `"-x"` | (-1, 0) | 1 |
| `"+z"` | (0, 1) | 0 |
| `"-z"` | (0, -1) | 0 |

#### `find_piece(catalog_items, piece_type, needs_open, tags)`

Search catalog for pieces matching constraints. Tests all 4 rotations when `needs_open` is specified:

```python
# Find any corner piece
results = find_piece(catalog["items"], piece_type="corner")

# Find a piece open on +z and +x at some rotation
results = find_piece(catalog["items"], needs_open={"+z": True, "+x": True})
# Returns: [("corridor_corner", 1), ("t_junction", 0), ...]  — (key, rot_steps)
```

#### `validate_layout()`

Always run before pushing. Detects overlapping grid cells and open edges with no neighbor:

```python
warnings = kit.validate_layout()
for w in warnings:
    print(f"  WARNING: {w}")
```

### Complete Modular Example

```python
import json
from modular_helpers import ModularKit

with open("games/my-room/catalog.json") as f:
    catalog = json.load(f)

mk = catalog["modular_kit"]
kit = ModularKit(
    grid_size=mk["grid_size"],
    level_height=mk["level_height"],
    catalog_items=catalog["items"]
)
kit.place_fn = lambda key, pos, facing_deg, scale: place(key, pos, facing_deg=facing_deg, scale=scale)

# Build an L-shaped corridor with a room
kit.place_corridor_run("corridor_straight", 0, 0, "+x", 5)
kit.place_mod("corridor_corner", 5, 0, rot_steps=1)
kit.place_corridor_run("corridor_straight", 5, 1, "+z", 3)
kit.place_room("lab_room", 3, 5)
kit.place_mod("end_cap", 0, 0, rot_steps=3)

warnings = kit.validate_layout()
assert not warnings, f"Layout has {len(warnings)} issues"
```

---

## Generation Script Template

Every generation script should follow this pattern:

```python
#!/usr/bin/env python3
"""Generate room items from catalog metadata."""
import json
import math
import os

ROOM_DIR = os.path.dirname(__file__)
CATALOG_PATH = os.path.join(ROOM_DIR, "catalog.json")
OUTPUT_PATH = os.path.join(ROOM_DIR, "snapshot.json")

# Load catalog
with open(CATALOG_PATH) as f:
    catalog = json.load(f)
items_db = catalog["items"]


# ── Helpers ─────────────────────────────────────────────────────────

def yrot(deg):
    """Quaternion for Y-axis rotation in degrees."""
    r = math.radians(deg)
    return {"x": 0, "y": round(math.sin(r / 2), 6), "z": 0, "w": round(math.cos(r / 2), 6)}

NO_ROT = {"x": 0, "y": 0, "z": 0, "w": 1}
item_counter = 0
room_items = {}

def place(catalog_key, pos, facing_deg=0, scale=1.0):
    """Place a catalog item. facing_deg: +X=90, -X=-90, +Z=0, -Z=180."""
    global item_counter
    item_counter += 1
    entry = items_db[catalog_key]
    s = {"x": scale, "y": scale, "z": scale} if isinstance(scale, (int, float)) else scale
    room_items[str(item_counter)] = {
        "prefabName": "GLB",
        "parentItemID": 0,
        "currentEditornetId": 0,
        "pos": {"x": pos[0], "y": pos[1], "z": pos[2]},
        "modelsize": {"x": 0, "y": 0, "z": 0},
        "modelCenter": {"x": 0, "y": 0, "z": 0},
        "rot": yrot(facing_deg),
        "scale": s,
        "contentString": entry["url"],
        "interactivityType": 0,
        "interactivityURL": "",
        "hoverTitle": "",
        "hoverBodyContent": "",
        "ImageInteractivityDetails": {"buttonText": "", "buttonURL": ""},
        "extraData": json.dumps({"events": [], "ViewNodes": []}),
        "sessionData": "",
        "instanceId": "",
        "placed": True,
        "locked": False,
        "superLocked": False,
    }

def cube(pos, scale, color="333333"):
    """Place a ResizableCube. pos is center, scale is full size."""
    global item_counter
    item_counter += 1
    room_items[str(item_counter)] = {
        "prefabName": "ResizableCube",
        "parentItemID": 0,
        "currentEditornetId": 0,
        "pos": {"x": pos[0], "y": pos[1], "z": pos[2]},
        "modelsize": {"x": 0, "y": 0, "z": 0},
        "modelCenter": {"x": 0, "y": 0, "z": 0},
        "rot": NO_ROT,
        "scale": {"x": scale[0], "y": scale[1], "z": scale[2]},
        "contentString": "",
        "interactivityType": 0,
        "interactivityURL": "",
        "hoverTitle": "",
        "hoverBodyContent": "",
        "ImageInteractivityDetails": {"buttonText": "", "buttonURL": ""},
        "extraData": json.dumps({"events": [], "ViewNodes": [], "c": color}),
        "sessionData": "",
        "instanceId": "",
        "placed": True,
        "locked": False,
        "superLocked": False,
    }

def get_width(key):
    """X-axis width."""
    return items_db[key]["size"][0]

def get_depth(key):
    """Z-axis depth."""
    return items_db[key]["size"][2]

def get_height(key):
    """Y-axis height."""
    return items_db[key]["size"][1]


# ── Place Items ─────────────────────────────────────────────────────

# ... your scene layout here, using catalog dimensions for spacing ...


# ── Output ──────────────────────────────────────────────────────────

room_data = {
    "roomItems": room_items,
    "settings": { ... },
    "roomTasks": {"Tasks": []},
    "quests": {},
}

with open(OUTPUT_PATH, "w") as f:
    json.dump(room_data, f)

print(f"Generated {item_counter} items → {OUTPUT_PATH}")
```

---

## Avatar-Relative Scaling

### The Rule

Portals avatars range from **1.0m to 1.6m tall** (default 1.6m). All GLB models must be scaled so they look proportional to the player. Video game worlds tend to be slightly larger than real life, but objects should still feel right — a chair should be sittable, a doorway should be walkable, a table should be waist-height.

### Default Behavior

**Unless the user says otherwise**, scale GLB assets so they match avatar proportions:

| Object | Real-world height | Target in-game height | Notes |
|--------|-------------------|----------------------|-------|
| Chair seat | 0.45m | 0.4-0.5m | Slightly below avatar waist |
| Table | 0.75m | 0.7-0.8m | Avatar waist height |
| Doorway | 2.0m | 2.0-2.5m | Comfortable clearance |
| Ceiling | 2.5-3.0m | 2.5-3.5m | Slightly generous |
| Street lamp | 3-5m | 3-5m | Taller than avatar |
| Building story | 3.0m | 3.0-4.0m | Game-scale generous |
| Tree | 4-15m | 4-12m | Varies by type |

### Scaling Formula

When a GLB model's raw dimensions don't match the intended in-game size:

```python
def avatar_scale(catalog_key, target_height):
    """Calculate uniform scale to make an item a target height in meters."""
    raw_height = get_height(catalog_key)
    return target_height / raw_height

# Example: chair model is 2m tall in the GLB, should be ~0.9m in-game
chair_scale = avatar_scale("my_chair", 0.9)  # → 0.45
place("my_chair", (0, 0, 0), scale=chair_scale)
```

### When NOT to Rescale

- User explicitly says "keep original scale" or "exact size"
- User wants jumbo/miniature items as a design choice
- Model is already at correct proportions (common with game-ready assets)
- Floor tiles and wall panels — these are scaled to cover area, not match avatar height

### Sanity Check

Before pushing, mentally walk through the scene as a 1.6m avatar:
- Can I walk through doorways without crouching?
- Do chairs come up to my knees/waist?
- Do tables come up to my waist?
- Can I see over counters?
- Do decorations feel like the right "weight" in the space?

If something feels off, adjust the scale. A 10m chair is never correct unless the user specifically asked for giant furniture.

---

## Spacing Best Practices

### Use Real Dimensions

Always read item sizes from the catalog — never hardcode or estimate:

```python
chair_w = get_width("my_chair")   # actual X size
chair_d = get_depth("my_chair")   # actual Z size
gap = 0.3  # comfortable gap between items

# Two chairs side by side
place("my_chair", (0, 0, 0))
place("my_chair", (chair_w + gap, 0, 0))
```

### Items Around a Table

Position items using table dimensions + item depth + gap:

```python
TABLE_W, TABLE_D = 1.8, 1.2
gap = 0.3

# Chair on -Z side, facing table (+Z → 0°)
chair_d = get_depth("chair")
place("chair", (0, 0, -(TABLE_D/2 + gap + chair_d/2)), facing_deg=0)

# Chair on +Z side, facing table (-Z → 180°)
place("chair", (0, 0, TABLE_D/2 + gap + chair_d/2), facing_deg=180)
```

### Items Along a Wall/Bar

Line items up using their widths for proper spacing:

```python
z_cursor = start_z
for key in item_keys:
    w = get_width(key)
    place(key, (bar_x, 0, z_cursor), facing_deg=90)  # face +X toward bar
    z_cursor += w + 0.4  # move cursor by item width + gap
```

### Zone-Based Layout

Organize scenes into distinct zones, each with a center point:

```python
# Zone 1: Central lounge at origin
# Zone 2: Bar counter at +X
# Zone 3: Back wall seating at +Z
# Zone 4: Work area at -X
# Zone 5: Corner seating at +X, -Z
```

---

## ResizableCube Placement

Cubes (tables, walls, platforms) use center-origin placement:

```python
# A table 1.8m wide, 0.44m tall, 1.2m deep
# pos.y = half-height puts the bottom at Y=0
cube((0, 0.22, 0), (1.8, 0.44, 1.2), "1a1a2e")

# A wall 8m wide, 3m tall, 0.2m thick along +Z edge
cube((0, 1.5, 10), (8, 3, 0.2), "333333")
```

---

## Project File Structure

```
games/{room-id}/
  catalog.json       ← item metadata (dimensions, URLs, categories)
  thumbnails/        ← 4-view PNG renders of each item
  generate.py        ← Python script that reads catalog + produces room data
  snapshot.json      ← generated room data (pushed to MCP)
  update_catalog.py  ← one-time script to populate catalog fields
  design.md          ← game design document
  changelog.md       ← iteration history
```

---

## Extraction Tool Reference

## Storage Limits

Portals rooms are browser-based, so total asset size matters. The storage check runs automatically during metadata extraction and Blender export, or manually:

```bash
python tools/check_room_storage.py /path/to/glbs/
python tools/check_room_storage.py --catalog games/room-id/catalog.json
```

| Total unique files | Status | Action |
|---|---|---|
| Under 200 MB | OK | Room should load fine |
| 200–500 MB | WARNING | Room is heavy — optimize large assets |
| Over 500 MB | CRITICAL | Room may fail to load — reduce asset sizes |

Only **unique** files count — instanced copies of the same GLB don't add significant load.

---

## Extraction Tool Reference

`tools/extract_glb_metadata.py` requires: `trimesh`, `numpy`, `matplotlib`, `Pillow`

```bash
pip install trimesh numpy matplotlib Pillow
```

### Usage

```bash
# Single GLB
python tools/extract_glb_metadata.py model.glb room-id

# Folder of GLBs
python tools/extract_glb_metadata.py ./models/ room-id

# With pre-known CDN URLs
python tools/extract_glb_metadata.py ./models/ room-id --cdn-urls urls.json
```

### Output

Each item gets a 4-view thumbnail PNG:
- **Front (-Z)** — glTF front view
- **Right (+X)** — side view
- **Top (-Y)** — bird's eye
- **Perspective** — angled overview

Use these to visually identify items and determine their category, name, and front direction.

---

## Troubleshooting

### GLBs Not Loading or Appearing Invisible

If a user reports that GLB models aren't showing up at all, check these common causes in order:

1. **Bad URL** — Verify the `contentString` is a valid, publicly accessible CDN URL. Open it in a browser to confirm it downloads.
2. **File too large** — Run `python tools/check_room_storage.py --catalog games/{room-id}/catalog.json`. Individual GLBs over ~15 MB or rooms over 500 MB total may fail to load.
3. **Corrupt GLB** — Try opening the file in a local glTF viewer (e.g., https://gltf-viewer.donmccurdy.com/). If it doesn't render there either, the file itself is broken.
4. **External texture references** — See the next section. This is the most common cause of models loading but appearing white/grey.
5. **Scale issue** — A model at scale 0.001 will be invisible. Check the `scale` field in the room data.

### Models Appear Untextured (White/Grey) After Upload

**Symptom:** GLB models load fine locally but appear white/grey on the Portals CDN.

**Cause:** The GLB uses external `"uri"` references for textures instead of embedding them in the binary buffer. This is common with GLBs exported from Unity (via UnityGLTF), older Blender plugins, or other tools that write texture paths like `Textures/colormap.png`. The relative path doesn't exist on the CDN.

**How to detect:** Inspect the GLB file's JSON chunk. Look at the `images` array:
- `"uri": "Textures/colormap.png"` — **broken** (external reference)
- `"bufferView": 3, "mimeType": "image/png"` — **correct** (embedded)

**How to fix:** Use the repack tool:

```bash
python tools/repack_glb_textures.py <input_folder> <output_folder>
```

This reads each GLB, finds images with external `"uri"` entries, embeds the referenced texture files into the binary buffer, and writes fixed GLBs to the output folder. Files without external textures are copied as-is.

The tool looks for referenced textures relative to the GLB file's directory, and also checks a `Textures/` subfolder. After repacking, upload the output folder and verify models render with textures on the CDN.
