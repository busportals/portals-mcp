# Room Index System

Compact room representation that replaces loading full snapshot.json (~10K-28K lines) into agent context.

## The Rule

**Never read snapshot.json into context.** Use these three tools instead:

1. `tools/index_room.py` — generates a compact room index (~30-200 lines)
2. `tools/query_room.py` — selective access to specific items
3. `tools/merge_room.py` — applies patches to snapshots on disk

## Tool 1: Indexer

```bash
python3 tools/index_room.py games/{room-id}/snapshot.json
```

Generates `room_index.md` in the same directory. Contains 5 layers:

| Layer | Content | Typical Size |
|-------|---------|-------------|
| Summary | Item counts, quests, variables, spawn, bounding box | ~15 lines |
| Interactive Items | Items with triggers/effects (player-triggered only if >80 total) | ~10-80 lines |
| Spatial Map | Items grouped by 20x20 grid zones | ~10-15 lines |
| Parent-Child | Grouped items | ~5-20 lines |
| Quests | Quest names, states, transitions (grouped if >50 quests) | ~10-50 lines |

Re-run the indexer after any change to snapshot.json. The merge tool does this automatically.

## Tool 2: Query

```bash
# By ID
python3 tools/query_room.py games/{room-id}/snapshot.json --id 47 --id 48

# By type
python3 tools/query_room.py games/{room-id}/snapshot.json --type Trigger

# Spatial query
python3 tools/query_room.py games/{room-id}/snapshot.json --near 10,0,15 --radius 5

# Items with player triggers
python3 tools/query_room.py games/{room-id}/snapshot.json --has-triggers

# Children of a parent
python3 tools/query_room.py games/{room-id}/snapshot.json --parent 12

# Text search
python3 tools/query_room.py games/{room-id}/snapshot.json --search "door"

# Combine filters (AND logic)
python3 tools/query_room.py games/{room-id}/snapshot.json --type GLB --near 0,0,0 --radius 20
```

All filters: `--id`, `--type`, `--near X,Y,Z` + `--radius R`, `--has-triggers`, `--has-effects`, `--quest NAME`, `--parent ID`, `--search TEXT`.

Aim for queries returning <50 items. Warns if more.

## Tool 3: Merge

```bash
# Dry run first
python3 tools/merge_room.py games/{room-id}/ --patch patch.json --dry-run

# Apply
python3 tools/merge_room.py games/{room-id}/ --patch patch.json
```

### Patch Format

```json
{
  "add_items": {
    "501": {"prefabName": "Trigger", "pos": {"x": 5, "y": 0.5, "z": 10}, ...}
  },
  "modify_items": {
    "47": {"pos": {"x": 10, "y": 1, "z": -5}}
  },
  "remove_items": ["12", "13"],
  "add_quests": {"quest-uuid": {"Name": "3_boss", ...}},
  "remove_quests": ["old-uuid"],
  "modify_settings": {"Variables": [...]}
}
```

All keys optional. **Field-level replace** for modify: specified fields replace, unspecified fields preserved.

### Safety Checks

- Cannot remove a parent without removing its children (error)
- Cannot add an item with an existing ID (error)
- Cannot modify a non-existent item (error)
- Warns when removing items referenced in interactions

### After Merge

Automatically re-runs the indexer to update `room_index.md`.

## Workflows

### New Build

1. Design → generate.py → snapshot.json → push via MCP
2. Run indexer to create room_index.md for future iterations

### Iteration (component-based)

1. Read `room_index.md`
2. Modify the relevant component file
3. Re-run generate.py → snapshot.json
4. Push via MCP
5. Indexer auto-runs if using merge tool; otherwise run manually

### Iteration (patch-based)

1. Read `room_index.md`
2. Query specific items if needed
3. Write `patch.json`
4. `python3 tools/merge_room.py games/{room-id}/ --patch patch.json`
5. Push merged snapshot.json via MCP

### First Contact with Manual Room

1. Fetch room data from MCP → save as `games/{room-id}/snapshot.json`
2. `python3 tools/index_room.py games/{room-id}/snapshot.json`
3. Read `room_index.md` — **not** snapshot.json

## Data Format & Normalization

All three tools auto-normalize legacy snapshots via `normalize_snapshot()` from `portals_utils.py`. This means:

- **New format** (logic separated): `logic` is a top-level key alongside `roomItems`. Items contain only spatial/visual data; interactions and type config live in `logic[itemId]`.
- **Legacy format** (embedded extraData): Interactions were embedded as `extraData` inside each item. `normalize_snapshot()` merges `logic` back into items as `extraData` so tool internals work unchanged.

You do not need to worry about which format a snapshot uses. The tools detect and handle both automatically. When generating new rooms, always use the new separated format (`roomItems` + `logic`).
