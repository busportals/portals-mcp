
# Portals Building System Index

Quick reference for all item types, triggers, effects, and systems available in Portals.

## Item Types

| Category | Items | prefabNames | Docs |
|----------|-------|-------------|------|
| **Building** | Cube, Text, Portal, Spawn | ResizableCube, WorldText, Portal, SpawnPoint | [reference/items/building.md](reference/items/building.md) |
| **Models** | GLB, Collectible, Destructible | GLB, GlbCollectable, Destructible | [reference/items/models.md](reference/items/models.md) |
| **Gameplay** | Trigger, Jump Pad, Elemental, Gun, Shotgun, Camera, Vehicle | Trigger, JumpPad, 9Cube, Gun, Shotgun, CameraObject, Vehicle | [reference/items/gameplay.md](reference/items/gameplay.md) |
| **Media** | Image, Video, Screenshare | DefaultPainting, DefaultVideo, PlaceableTV | [reference/items/media.md](reference/items/media.md) |
| **Lighting** | Light, Blink Light, Spotlight | Light, BlinkLight, SpotLight | [reference/items/lighting.md](reference/items/lighting.md) |
| **Display** | Leaderboard, Chart, Billboard | Leaderboard, Chart, GLBSign | [reference/items/display.md](reference/items/display.md) |
| **Interactive** | NPC, Combat NPC | GLBNPC, EnemyNPC | [reference/items/interactive.md](reference/items/interactive.md) |
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
| **Shot Hit** | ShotHitTrigger | Bullet hits target (Gun/Shotgun only) |
| **Got Kill** | GotKillTrigger | Player gets a kill (Gun/Shotgun only) |
| **Started Aiming** | StartedAimingTrigger | Player aims down sights (Gun/Shotgun only) |
| **Stopped Aiming** | StoppedAimingTrigger | Player stops aiming (Gun/Shotgun only) |
| **Gun Tossed** | OnGunTossedTrigger | Player drops gun (Gun/Shotgun only) |
| **Vehicle Entered** | OnVehicleEntered | Player enters vehicle (Vehicle only) |
| **Vehicle Exited** | OnVehicleExited | Player exits vehicle (Vehicle only) |
| **Enemy Died** | OnEnemyDied | Enemy NPC killed (EnemyNPC only) |
| **Take Damage** | OnTakeDamageTrigger | Enemy NPC took damage (EnemyNPC only) |

## Effects

### Visibility

| Effect | $type | Use Case |
|--------|-------|----------|
| **Show** | ShowObjectEvent | Reveal a hidden item |
| **Hide** | HideObjectEvent | Hide an item (invisible + no collider) |
| **Show Outline** | ShowOutline | Show selection outline |
| **Hide Outline** | HideOutline | Remove selection outline |

### Movement & Transform

| Effect | $type | Use Case |
|--------|-------|----------|
| **MoveToSpot** | MoveToSpot | Animate position/rotation/scale (absolute or relative) |
| **PortalsAnimation** | PortalsAnimation | Multi-keyframe animation |
| **Duplicate** | DuplicateItem | Clone item at position |
| **Move to Player** | MoveItemToPlayer | Teleport item to player's position |

### Player Effects

| Effect | $type | Use Case |
|--------|-------|----------|
| **Velocity** | AddVelocityToPlayer | Launch/push player |
| **Teleport** | TeleportEvent | Move player to room/spawn |
| **Heal** | ChangePlayerHealth | Heal player |
| **Damage** | ChangePlayerHealth (op:2) | Damage player |
| **Damage Over Time** | DamageOverTime | Continuous damage on contact |
| **Lock Movement** | LockMovement | Freeze player |
| **Unlock Movement** | UnlockMovement | Unfreeze player |
| **Start Auto Run** | StartAutoRun | Force auto-run |
| **Stop Auto Run** | StopAutoRun | Stop auto-run |
| **Emote** | PlayerEmote | Play emote animation |
| **Mute** | MutePlayer | Mute player mic |
| **Hide All Players** | HideAllPlayersEvent | Hide other players |
| **Lock Avatar** | LockAvatarChange | Prevent avatar change |
| **Unlock Avatar** | UnlockAvatarChange | Allow avatar change |
| **Avatar Screen** | DisplayAvatarScreen | Open avatar selection |
| **Change Avatar** | ChangeAvatarEffector | Set avatar to GLB |
| **Movement Profile** | ChangeMovementProfile | Switch movement settings |
| **Equip Wearable** | ChangeRoundyWearableEffector | Equip wearable item |

### Camera

| Effect | $type | Use Case |
|--------|-------|----------|
| **Lock Camera** | LockCamera | Lock camera position |
| **Unlock Camera** | UnlockCamera | Unlock camera |
| **Zoom** | ChangeCameraZoom | Change zoom level |
| **Free Cam** | ToggleFreeCam | Toggle free camera |
| **Cam State** | ChangeCamState | Switch to named camera state |
| **Filter** | SetCameraFilter | Apply image overlay |
| **Cursor Lock** | ToggleLockCursor | Lock/unlock mouse cursor |

### UI & Notifications

| Effect | $type | Use Case |
|--------|-------|----------|
| **Notification** | NotificationPillEvent | Toast message on screen |

### Values (Variables)

| Effect | $type | Use Case |
|--------|-------|----------|
| **Display Value** | DisplayValueEvent | Show variable on HUD |
| **Hide Value** | HideValueEvent | Hide variable from HUD |
| **Update Value** | UpdateScoreEvent | Modify numeric variable |
| **Update String** | UpdateScoreEventString | Set string variable |

### Logic & Control

| Effect | $type | Use Case |
|--------|-------|----------|
| **Function** | FunctionEffector | NCalc expression |
| **Run Triggers** | RunTriggersFromEffector | Chain quest states |
| **Reset All Tasks** | ResetAllTasks | Reset all quests |

### Timers

| Effect | $type | Use Case |
|--------|-------|----------|
| **Start Timer** | StartTimerEffect | Start a named timer |
| **Stop Timer** | StopTimerEffect | Stop timer (fires OnTimerStopped) |
| **Cancel Timer** | CancelTimerEffect | Cancel timer silently |

### Leaderboard

| Effect | $type | Use Case |
|--------|-------|----------|
| **Post Score** | PostScoreToLeaderboard | Post score to leaderboard |
| **Clear** | ClearLeaderboard | Clear a leaderboard |
| **Open** | OpenLeaderboardEffect | Open leaderboard UI |

### Audio

| Effect | $type | Use Case |
|--------|-------|----------|
| **Play Once** | PlaySoundOnce | One-shot sound effect |
| **Play Loop** | PlaySoundInALoop | Looping ambient/music |
| **Stop Sound** | StopSound | Stop a playing sound |
| **Change Audius** | ChangeAudiusEffect | Change music playlist |

### Environment

| Effect | $type | Use Case |
|--------|-------|----------|
| **Bloom** | ChangeBloom | Adjust bloom post-processing |
| **Time of Day** | ChangeTimeOfDay | Cycle lighting/skybox |
| **Rotate Skybox** | RotateSkybox | Rotate sky background |
| **Fog** | ChangeFog | Change fog color/distance |

### Communication & Iframes

| Effect | $type | Use Case |
|--------|-------|----------|
| **Send to Iframes** | SendMessageToIframes | Push data to open iframes |
| **Voice Group** | ChangeVoiceGroup | Move player to voice group |
| **Open Iframe** | IframeEvent | Open HTML overlay |
| **Close Iframe** | IframeStopEvent | Close HTML overlay |

### NPC (GLBNPC only)

| Effect | $type | Use Case |
|--------|-------|----------|
| **NPC Message** | NPCMessageEvent | Send message to AI NPC |
| **Walk NPC** | WalkNpcToSpot | Walk NPC to position |
| **NPC Animation** | NpcAnimation | Play named animation |
| **NPC Path** | NpcCopyPlayerPath | NPC walks along recorded path |
| **NPC Stop Path** | NpcCopyPlayerPathStop | Stop NPC path following |
| **Turn to Player** | TurnToPlayer | NPC faces activating player |
| **Start Speaking** | StartSpeaking | Start talking animation |
| **Stop Speaking** | StopSpeaking | Stop talking animation |

### Gun (Gun/Shotgun only)

| Effect | $type | Use Case |
|--------|-------|----------|
| **Equip Gun** | EquipGunEffect | Auto-equip the gun |
| **Toss Gun** | TossGunEffect | Force drop equipped gun |
| **Reset Gun** | ResetGunEffect | Reset ammo/reload |

### EnemyNPC (EnemyNPC only)

| Effect | $type | Use Case |
|--------|-------|----------|
| **Revive Enemy** | ReviveEnemy | Revive dead EnemyNPC |
| **Reset Enemy** | ResetEnemy | Reset to full health at origin |
| **Attack Player** | AttackPlayer | Force attack nearest player |
| **Change Enemy HP** | ChangeEnemyHealth | Modify enemy health |
| **Duplicate Enemy** | DuplicateEnemy | Spawn copies at SpawnPoint |

### Vehicle (Vehicle only)

| Effect | $type | Use Case |
|--------|-------|----------|
| **Enter Vehicle** | EnterVehicle | Force player into vehicle |
| **Exit Vehicle** | ExitVehicle | Force player out of vehicle |
| **Vehicle Boost** | VehicleBoost | Temporary speed boost |

### Trigger Zone (Trigger only)

| Effect | $type | Use Case |
|--------|-------|----------|
| **Activate Zone** | ActivateTriggerZoneEffect | Re-enable trigger zone |
| **Deactivate Zone** | DeactivateTriggerZoneEffect | Disable trigger zone |

### Destructible (Destructible only)

| Effect | $type | Use Case |
|--------|-------|----------|
| **Respawn** | RespawnDestructible | Respawn destroyed item |

### GLB Animation

| Effect | $type | Use Case |
|--------|-------|----------|
| **Play Animation** | PlayAnimationOnce | Play GLB animation once (negative speed = reverse) |

### Other

| Effect | $type | Use Case |
|--------|-------|----------|
| **Token Swap** | DisplaySellSwap / HideSellSwap | Show/hide token swap UI |
| **Dialogue** | DialogEffectorDisplay | Interactive dialogue tree |
| **Refresh Inventory** | RefreshUserInventory | Refresh inventory display |

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
| **Iframes (Custom UI)** | **Any custom UI**: HUDs, scoreboards, inventory, mini-games, maps, overlays. Bidirectional HTML/JS communication, Portals SDK, variable interpolation, URL appearance control. | [reference/iframes.md](reference/iframes.md) |

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

Some GLB files (especially those exported from Unity via UnityGLTF, older Blender plugins, or other tools) use external `"uri"` references for textures instead of embedding them in the binary buffer. These files load fine locally but **fail on the Portals CDN** because the relative path (e.g., `Textures/colormap.png`) doesn't exist on the CDN.

**How to detect:** After uploading, if models appear untextured (white/grey), inspect the GLB's JSON chunk — `images[].uri` means the textures are external and broken. `images[].bufferView` means they're correctly embedded.

**How to fix:** Run `python tools/repack_glb_textures.py <input_folder> <output_folder>` to embed textures, then re-upload. See `docs/reference/glb-asset-catalog.md` Troubleshooting section for details.

## Python Generation Libraries

Located in `lib/`:
- `portals_core.py` — Item generators (cubes, NPCs, lights, etc.). All creators return `(item, logic)` tuples.
- `portals_effects.py` — Trigger/effect builders. Use `add_task_to_logic(logic, task)` to wire interactions.
- `portals_utils.py` — Quest helpers, validation, `serialize_logic()`, `normalize_snapshot()`
