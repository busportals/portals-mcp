# Blender-to-Portals Pipeline

Import a Blender scene layout directly into a Portals room. Use this when the user has already arranged objects in Blender and wants to bring that spatial layout into Portals.

**This does NOT replace the GLB catalog workflow.** Use the catalog workflow when building scenes from scratch or arranging items programmatically. Use this pipeline when a `.blend` file with a pre-arranged scene is provided.

---

## When to Use

- User provides a `.blend` file path and wants the scene imported
- The spatial arrangement is already done in Blender
- Game logic (triggers, NPCs, quests) will be added separately after import

## When NOT to Use

- Building a scene from scratch (use catalog workflow)
- User has loose GLB files without a scene arrangement
- User needs catalog metadata for programmatic layout calculations

---

## Prerequisites

- Blender must be installed and accessible from the command line (`blender --background` must work)
- On macOS, this is typically: `/Applications/Blender.app/Contents/MacOS/Blender`
- If `blender` is not on PATH, use the full path

---

## The Pipeline

### Step 1: Set Up Output Directory

```bash
mkdir -p games/{room-id}/blender_export
```

### Step 2: Run Blender Export

**Context-saving:** Blender produces verbose per-file export logs (100-200+ lines). Pipe stdout to a log file to avoid bloating the conversation context. The manifest.json contains everything needed afterward (object count, unique meshes, filenames).

```bash
blender --background /path/to/scene.blend --python tools/blender_to_portals.py -- games/{room-id}/blender_export/ > games/{room-id}/blender_export/export.log 2>&1
```

Verify success by checking the manifest exists and the log tail:
```bash
tail -3 games/{room-id}/blender_export/export.log
```

This exports:
- One `.glb` file per visible mesh object (at local origin, no baked transform)
- `manifest.json` with object names, Portals-space positions, rotations, and scales

**What gets exported:** All visible mesh objects (`obj.type == 'MESH' and obj.visible_get()`).
**What gets skipped:** Lights, cameras, empties, armatures, curves, hidden objects, degenerate meshes.
**Hierarchy:** Flattened — all objects use world-space transforms regardless of parenting.
**Instancing:** Objects sharing the same mesh datablock are exported as one GLB. All instances reference the same file with their own transforms. A scene with 790 objects but 200 unique meshes only uploads 200 GLBs.

### Step 2b: Check Storage Size

The Blender exporter prints a storage summary automatically. You can also run the check manually:

```bash
python tools/check_room_storage.py games/{room-id}/blender_export/
```

| Total unique GLBs | Status | Action |
|---|---|---|
| Under 200 MB | OK | Proceed to upload |
| 200–500 MB | WARNING | Warn user — room will be heavy, consider optimizing |
| Over 500 MB | CRITICAL | Warn user — room may not load, must reduce asset sizes before uploading |

### Step 3: Upload GLBs to CDN

**Context-saving:** The upload tool returns one line per file, which can be hundreds of lines. When the result overflows, Claude Code dumps it to a temp file. Use `parse_cdn_upload.py` to parse it — returns only a concise summary.

```python
mcp.upload_glbs_from_folder(folderPath="games/{room-id}/blender_export/")
```

Then parse the result (handles both raw text and JSON overflow formats):

```bash
python tools/parse_cdn_upload.py <upload_result_file> games/{room-id}/blender_export/
```

This parses the upload output, verifies all manifest GLBs have CDN URLs, and saves `cdn_urls.json`. Output is a 5-line summary.

### Step 4: Generate Room Data

```bash
python tools/manifest_to_room_data.py games/{room-id}/blender_export/ --cdn-urls games/{room-id}/blender_export/cdn_urls.json --room-id {room-id}
```

Produces `games/{room-id}/snapshot.json`.

### Step 5: Validate

```bash
python tools/validate_room.py games/{room-id}/snapshot.json
```

Always validate before pushing. Fix any errors before proceeding.

### Step 6: Checkpoint — Check for Existing Data

Before pushing, check if the room already has items or game logic:
- **Empty room:** Push directly.
- **Room has existing data:** Ask the user: "This room has existing items/interactions. Should I merge the Blender scene alongside them, or replace everything?"

### Step 7: Push to Room

```python
mcp.set_room_data(roomId="{room-id}", filePath="games/{room-id}/snapshot.json")
```

Room URL: `https://theportal.to/?room={room-id}`

---

## Coordinate Conversion Reference

Blender (Z-up, right-handed) to Portals (Y-up, right-handed).

**Important:** Portals loads GLB mesh data as-is without a handedness Z-negate.
The Blender glTF exporter converts mesh vertices to Y-up RH, so our manifest
positions must also be in Y-up RH to stay consistent with the mesh data.

**Position:**

| Blender | Portals |
|---------|---------|
| X | X |
| Y | -Z |
| Z | Y |

**Rotation** (Blender quaternion WXYZ to Portals XYZW):
- `portal.x = blender.x`
- `portal.y = blender.z`
- `portal.z = -blender.y`
- `portal.w = blender.w`

**Scale:** Axis swap to match position (swap Y/Z). Both systems use meters.

---

## Output Structure

```
games/{room-id}/
  blender_export/
    manifest.json       — object list with Portals-space transforms
    cdn_urls.json       — filename-to-CDN-URL mapping (saved after upload)
    *.glb               — individual mesh exports
  snapshot.json         — generated room data
```

---

## Limitations (V1)

- **Meshes only** — lights, cameras, armatures, curves not imported
- **Flat hierarchy** — parent-child relationships not preserved
- **No game logic** — triggers, NPCs, quests added separately after import
- **Materials** — only what Blender bakes into the GLB export (PBR materials transfer, but custom shader setups may not)
- **Requires Blender CLI** — headless Blender must be available

---

## Tools Reference

| Tool | Location | Purpose |
|------|----------|---------|
| `blender_to_portals.py` | `tools/` | Blender headless export script — GLBs + manifest |
| `parse_cdn_upload.py` | `tools/` | Parse CDN upload results → `cdn_urls.json` + verify against manifest |
| `manifest_to_room_data.py` | `tools/` | Manifest + CDN URLs → Portals room data |
| `check_room_storage.py` | `tools/` | Check cumulative storage of unique files against size thresholds |
