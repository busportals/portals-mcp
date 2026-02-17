# Parent-Child Relationships

Items can be parented to other items using `parentItemID`. This creates a hierarchy where children move, rotate, and scale with their parent.

## Why Use Parenting

- **Group movement**: Pick up or animate a parent and all children move with it
- **Organized layout**: Keep children at relative positions, only reposition the parent to move the whole group
- **Modular design**: Build a sign, control panel, or decorative cluster as a unit — move it anywhere by changing one position
- **PortalsAnimation**: Animating a parent with `MoveToSpot` or `PortalsAnimation` moves all children together

## How It Works

Every item has a `parentItemID` field:
- `0` = no parent (default, item is in world space)
- Any other number = the **item key** of the parent

```json
{
  "85": {
    "prefabName": "ResizableCube",
    "parentItemID": 0,
    "pos": {"x": -14.4, "y": 3.4, "z": -23.3},
    "scale": {"x": 10, "y": 7, "z": 0.2}
  },
  "86": {
    "prefabName": "WorldText",
    "parentItemID": 85,
    "pos": {"x": 0.2, "y": 2.9, "z": 0.1}
  },
  "87": {
    "prefabName": "ResizableCube",
    "parentItemID": 85,
    "pos": {"x": 4.3, "y": 2.0, "z": 0.1}
  }
}
```

## Local Space Coordinates

**When an item has a parent, its `pos` and `rot` are in the parent's local space, not world space.**

- A child at `pos: {x: 0, y: 0, z: 0}` sits at the parent's center
- A child at `pos: {x: 1, y: 0, z: 0}` is offset 1 unit right from the parent's center
- Rotation is also relative — a child with identity rotation inherits the parent's world rotation

This means you can:
1. Position children relative to the parent once
2. Move the parent anywhere in the room
3. All children maintain their relative positions automatically

## Python Generation

```python
from scripts.portals_core import create_cube, create_text

def build_info_board(start_id, board_pos):
    """Create a dark board with title and colored status indicators."""
    items = {}
    parent_id = start_id

    # Parent: dark background board (world space position)
    items[str(parent_id)] = create_cube(
        pos=board_pos,
        scale=(10, 7, 0.2),
        color="020102"
    )

    # Child: title text (local space — relative to parent center)
    child = create_text(
        pos=(0.2, 2.9, 0.1),  # near top of board
        content="<b>Status Board</b>",
        billboard=False
    )
    child["parentItemID"] = parent_id
    items[str(parent_id + 1)] = child

    # Child: green indicator cube (local space)
    indicator = create_cube(
        pos=(4.3, 2.0, 0.1),  # right side of board
        scale=(1, 1, 0.05),
        color="18E708",
        emission=0.4
    )
    indicator["parentItemID"] = parent_id
    items[str(parent_id + 2)] = indicator

    return items
```

### Setting parentItemID

The `create_base_item` function sets `parentItemID: 0` by default. To parent an item, set it after creation:

```python
child_item = create_cube(pos=(0, 0, 0.1), scale=(1, 1, 0.05), color="FF0000")
child_item["parentItemID"] = 85  # key of the parent item
```

Or use the helper:

```python
from scripts.portals_core import create_base_item

def set_parent(item, parent_key):
    """Set an item's parent. The item's pos/rot become local to the parent."""
    item["parentItemID"] = parent_key
    return item
```

## Rules and Gotchas

| Rule | Details |
|------|---------|
| **parentItemID references the item key** | The string key in the items dict (e.g., `"85"`), stored as integer |
| **Children use local coordinates** | `pos` and `rot` are relative to parent, not world origin |
| **Scale is independent** | Child `scale` is its own size, not multiplied by parent scale |
| **Any item can be a parent** | ResizableCubes, GLBs, etc. — no special setup needed |
| **Nesting depth** | Children can have children (grandchildren), though deep nesting is rare |
| **Moving the parent moves children** | In editor, grab/animation, or MoveToSpot — children follow |
| **Deleting a parent** | Children become orphaned — they keep their local coordinates but lose the parent reference |

## Common Patterns

### Sign / Info Panel
Parent = flat dark cube (the board), children = text labels, colored indicators, images

### Moving Platform with Decorations
Parent = platform cube with PortalsAnimation, children = railings, glow cubes, text labels all ride along

### Furniture Group
Parent = invisible or base cube, children = multiple GLB models and lights arranged as a unit

### UI Panel
Parent = flat cube as background, children = WorldText items for labels and values
