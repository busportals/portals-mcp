
# Portals Building System Index

Quick reference for all item types, triggers, effects, and systems available in Portals.

## Item Types

| Category | Items | prefabNames | Docs |
|----------|-------|-------------|------|
| **Building** | Cube, Text, Portal, Spawn | ResizableCube, WorldText, Portal, SpawnPoint | [reference/items/building.md](reference/items/building.md) |
| **Models** | GLB, Collectible, Destructible | GLB, GlbCollectable, Destructible | [reference/items/models.md](reference/items/models.md) |
| **Gameplay** | Trigger, Jump Pad, Elemental, Gun, Shotgun, Camera | Trigger, JumpPad, 9Cube, Gun, Shotgun, CameraObject | [reference/items/gameplay.md](reference/items/gameplay.md) |
| **Media** | Image, Video, Screenshare | DefaultPainting, DefaultVideo, PlaceableTV | [reference/items/media.md](reference/items/media.md) |
| **Lighting** | Light, Blink Light, Spotlight | Light, BlinkLight, SpotLight | [reference/items/lighting.md](reference/items/lighting.md) |
| **Display** | Leaderboard, Chart, Billboard | Leaderboard, Chart, GLBSign | [reference/items/display.md](reference/items/display.md) |
| **Interactive** | NPC | GLBNPC | [reference/items/interactive.md](reference/items/interactive.md) |
| **Effects** | Addressable VFX (particles, fire, explosions, lightning) | Addressable | [reference/items/effects.md](reference/items/effects.md) |

## Triggers

**Note:** Click, Hover Start, and Hover End require a **visible** item — never use them on Trigger cubes (invisible).

| Trigger | $type | Use Case |
|---------|-------|----------|
| **Click** | OnClickEvent | Player clicks item (visible items only) |
| **On Enter** | OnEnterEvent | Player enters trigger zone (Trigger cube only) |
| **On Exit** | OnExitEvent | Player exits trigger zone (Trigger cube only) |
| **Collide** | OnCollideEvent | Player collides with item |
| **Collision Stopped** | OnCollisionStoppedEvent | Player stops colliding |
| **Hover Start** | OnHoverStartEvent | Cursor enters item (visible items only) |
| **Hover End** | OnHoverEndEvent | Cursor leaves item (visible items only) |
| **Key Pressed** | OnKeyPressedEvent | Keyboard key down |
| **Key Released** | OnKeyReleasedEvent | Keyboard key up |
| **Value Updated** | ScoreTrigger | Variable changes |
| **Item Collected** | OnItemCollectedEvent | Collectible picked up |
| **Player Login** | OnPlayerLoggedIn | Player joins room |
| **Player Died** | OnPlayerDied | Player health reaches 0 |
| **Player Revived** | OnPlayerRevived | Player revives after death |
| **Player Move** | OnPlayerMove | Player starts moving |
| **Player Stopped** | OnPlayerStoppedMoving | Player stops moving |
| **Player Leave** | PlayerLeave | Player leaves room |
| **Mic Unmuted** | OnMicrophoneUnmuted | Mic turns on |
| **Timer Stopped** | OnTimerStopped | Timer stopped |
| **Countdown Finished** | OnCountdownTimerFinished | Countdown reaches 0 |
| **Animation Stopped** | OnAnimationStoppedEvent | PortalsAnimation finishes |
| **Backpack Item** | OnItemClickEvent | Inventory item activated |
| **Swap Volume** | SwapVolume | Swap volume trigger |
| **Item Destroyed** | OnDestroyedEvent | Destructible item destroyed |
| **Gun Equipped** | OnGunEquippedTrigger | Player equips a gun (Gun/Shotgun only) |

## Effects

| Effect | $type | Use Case |
|--------|-------|----------|
| **MoveToSpot** | MoveToSpot | Animate position/rotation/scale |
| **PortalsAnimation** | PortalsAnimation | Multi-keyframe animation |
| **Show/Hide** | ShowObjectEvent / HideObjectEvent | Toggle visibility |
| **Teleport** | TeleportEvent | Move player to room/spawn |
| **Run Triggers** | RunTriggersFromEffector | Chain quest states |
| **Heal/Damage** | ChangePlayerHealth | Modify HP |
| **Lock Movement** | LockMovement / UnlockMovement | Freeze/unfreeze player |
| **Notification** | NotificationPillEvent | Toast message |
| **Display Value** | DisplayValueEvent | Show variable UI |
| **Update Value** | UpdateScoreEvent | Modify numeric variable |
| **Function Effect** | FunctionEffector | NCalc expression |
| **Play Sound** | PlaySoundOnce | One-shot audio |
| **Duplicate** | DuplicateItem | Clone item at position |
| **Change Bloom** | ChangeBloom | Post-processing bloom |
| **Rotate Skybox** | RotateSkybox | Rotate sky background |
| **Camera** | LockCamera / ChangeCameraZoom / SetCameraFilter | Camera control |
| **Timers** | StartTimerEffect / StopTimerEffect / CancelTimerEffect | Timer control |
| **Trigger Zone** | ActivateTriggerZoneEffect / DeactivateTriggerZoneEffect | Enable/disable trigger zones |
| **Gun Control** | EquipGunEffect / TossGunEffect / ResetGunEffect | Equip, drop, or reset guns |
| **Destructible** | RespawnDestructible | Respawn destroyed items |
| **GLB Animation** | PlayAnimationOnce | Play model animation once (supports reverse) |

All trigger and effect schemas are in [reference/interactions.md](reference/interactions.md).

## Workflow Guides

| Guide | When to Load | Docs |
|-------|-------------|------|
| **Game Designer** | Designing a new game or modifying an existing one | [workflows/game-designer-workflow.md](workflows/game-designer-workflow.md) |
| **Builder** | Building or iterating on a game from an approved design | [workflows/builder-workflow.md](workflows/builder-workflow.md) |
| **Function Effects** | Game logic with variables, conditionals, timers, multiplayer | [workflows/function-effects-reference.md](workflows/function-effects-reference.md) |
| **Logic Board** | Visual circuit-board diagrams of game logic | [workflows/game-logic-board.md](workflows/game-logic-board.md) |

## Systems

| System | Description | Docs |
|--------|-------------|------|
| **Settings** | Room environment, physics, UI, avatars, camera, variables | [reference/settings.md](reference/settings.md) |
| **Quests** | State-based animation system (NotActive → Active → Completed) | [reference/quests.md](reference/quests.md) |
| **Parent-Child** | Group items so children move/animate with parent | [reference/parent-child.md](reference/parent-child.md) |
| **GLB Asset Catalog** | Upload, catalog, rotate, and arrange GLB models. Includes modular kit classification, edge model, and grid placement helpers. | [reference/glb-asset-catalog.md](reference/glb-asset-catalog.md) |
| **Interactions** | Triggers, effects, quest-driven animations, PortalsAnimation, dialogue | [reference/interactions.md](reference/interactions.md) |
| **Room Index** | Compact room representation — index, query, merge tools. **Never read snapshot.json directly.** | [reference/room-index.md](reference/room-index.md) |
| **Movement** | Player physics, jump heights, gap widths, jump pad data, level design guidelines | [reference/movement-reference.md](reference/movement-reference.md) |
| **Functions** | NCalc expressions for complex logic | [workflows/function-effects-reference.md](workflows/function-effects-reference.md) |

## Coordinate System

- **Ground plane**: y = 0
- **Up**: +Y
- **1x1 cube on ground**: center at y = 0.5
- Default rotation: `{x: 0, y: 0, z: 0, w: 1}` (identity quaternion)
- **GLB rotation**: Models face +Z in Portals. `facing_deg = atan2(target_x, target_z)`. See [GLB Asset Catalog](reference/glb-asset-catalog.md).

## Build Patterns

Located in `docs/workflows/`:
- [modular-build-workflow.md](workflows/modular-build-workflow.md) — **Always use this.** Component breakdown, subagent delegation, deep delegation for large worlds
- [component-template.md](workflows/component-template.md) — Standard component interfaces, generate.py template, sub-component compositor pattern
- [scene-design.md](workflows/scene-design.md) — Asset classification, placement strategies (modular/organic/connectable/furniture), composition, variety techniques, helper functions

## Pipelines

| Pipeline | Use When | Docs |
|----------|----------|------|
| **Blender Import** | User provides a `.blend` file with a pre-arranged scene | [workflows/blender-to-portals.md](workflows/blender-to-portals.md) |

## Common Pitfalls

### Field Naming Inconsistencies

Portals uses different field names for the same concept across item types. These are the most common sources of bugs:

| Concept | ResizableCube | Light/BlinkLight/SpotLight | Effects |
|---------|---------------|---------------------------|---------|
| **Color** | `"col"` (6-char hex) | `"c"` (6-char hex) | varies by effect |
| **Collider** | `"c"` (bool) | n/a | n/a |

- ResizableCube color = `"col"`, NOT `"c"` (which is collider on cubes)
- Light color = `"c"`, NOT `"col"`
- Both use 6-char hex with no `#` prefix

### Sound Effect Field Capitalization

| Effect | URL field | Distance field |
|--------|-----------|----------------|
| `PlaySoundOnce` | `"Url"` (capital U) | `"Dist"` (capital D) |
| `PlaySoundInALoop` | `"Url"` (capital U) | `"Dist"` (capital D) |
| `StopSound` | `"url"` (lowercase u) | n/a |

### Room Data Format

The top-level room data structure pushed via MCP must follow this exact format:

```json
{
  "roomItems": { ... },
  "settings": { ... },
  "roomTasks": {"Tasks": []},
  "quests": { ... },
  "logic": { ... }
}
```

- **`roomTasks` MUST be `{"Tasks": []}` — NOT `{}`.** An empty dict breaks room loading. Even if you have no room tasks, the `Tasks` key with an empty array is required.
- **`logic` is a top-level key** containing interaction and type-config data as **JSON strings**, keyed by item ID. It is NOT embedded as `extraData` inside items. When generating rooms, `portals_core.py` creators return `(item, logic)` tuples — items go into `roomItems`, logic entries go into `logic`. Call `serialize_logic(room_data)` before writing `snapshot.json` to convert logic dicts to strings.

### Logic Separation

Interactions (triggers, effects, quest subscriptions) and type-specific configuration live in a **separate `logic` top-level key**, not embedded as `extraData` in items. Each key in `logic` is an item ID, and its value is a **JSON string** containing the serialized interaction data.

```json
{
  "roomItems": {
    "1": {"prefabName": "ResizableCube", "pos": {"x": 0, "y": 0.5, "z": 0}, ...}
  },
  "logic": {
    "1": "{\"Tasks\":[{\"$type\":\"TaskTriggerSubscription\",\"Trigger\":{\"$type\":\"OnClickEvent\"}}]}"
  }
}
```

During generation, build logic entries as dicts, then call `serialize_logic(room_data)` from `portals_utils` before writing — this converts each logic value to a JSON string. Use `add_task_to_logic(logic[item_id], task)` from `portals_effects.py` to wire interactions. The room index tools auto-normalize older snapshots (with embedded `extraData`) via `normalize_snapshot()`.

### FunctionEffector Task Names

Quest `Name` fields use the numbered format (`0_redteam`), but NCalc expressions in `FunctionEffector` use the name **without** the numbered prefix. Use `'redteam'` (not `'0_redteam'`) in `SetTask()`, `$T{}`, and `OnChange` expressions.

### Trigger Naming Symmetry

Enter and exit triggers use symmetric `$type` names:
- Enter: `OnEnterEvent`
- Exit: `OnExitEvent`

Both only work on Trigger cubes (prefabName `"Trigger"`). Note: `UserExitTrigger` was a legacy alias that also worked but `OnExitEvent` is the correct/preferred name.

### GLB External Texture References

Some GLB files (especially those exported from Unity via UnityGLTF, such as Kenney asset kits) use external `"uri"` references for textures instead of embedding them in the binary buffer. These files load fine locally but **fail on the Portals CDN** because the relative path (e.g., `Textures/colormap.png`) doesn't exist on the CDN.

**How to detect:** After uploading, if models appear untextured (white/grey), inspect the GLB's JSON chunk — `images[].uri` means the textures are external and broken. `images[].bufferView` means they're correctly embedded.

**How to fix:** Re-pack the GLB to embed textures — replace each `"uri"` with a `"bufferView"` + `"mimeType"` entry and append the image bytes to the binary buffer. See `docs/reference/glb-asset-catalog.md` for details.

## Python Generation Libraries

Located in `lib/`:
- `portals_core.py` — Item generators (cubes, NPCs, lights, etc.). All creators return `(item, logic)` tuples.
- `portals_effects.py` — Trigger/effect builders. Use `add_task_to_logic(logic, task)` to wire interactions.
- `portals_utils.py` — Quest helpers, validation, `serialize_logic()`, `normalize_snapshot()`
