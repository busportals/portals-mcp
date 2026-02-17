# Room Settings

Room settings control the environment, physics, UI, avatars, camera, and player experience. Settings are split into two layers:

1. **Top-level settings** — basic room configuration
2. **`roomSettingsExtraData`** — a JSON string containing the detailed configuration object

When writing settings via MCP, you must read the existing settings first (writes replace the entire object). The `roomSettingsExtraData` field must be a JSON-encoded string, not a raw object.

---

## Top-Level Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `roomBase` | string | `"BlankScene"` | Base scene/environment template |
| `isNight` | bool | `false` | Night mode (affects lighting, skybox) |
| `onlyNftHolders` | bool | `false` | Restrict entry to NFT holders |
| `wallIndex` | int | `0` | Wall style index |
| `inTownHallMode` | bool | `false` | Stage/audience mode — one speaker, others listen |
| `globalSpeaking` | bool | `false` | All voice chat is global (no distance falloff) |
| `chatDisabled` | bool | `false` | Disable text chat |
| `allCanBuild` | bool | `false` | Allow all users to place items |
| `audiusPlaylist` | string | `""` | Audius playlist URL for background music |
| `roomPrompt` | string | `""` | System prompt for AI NPCs in the room |
| `bannedUsers` | string | `""` | Banned user list |
| `shareLiveKitCrossInstances` | bool | `false` | Share voice across room instances |
| `tokenImage` | string | `""` | Token gate image URL |
| `tokenName` | string | `""` | Token gate token name |
| `tokenAddress` | string | `""` | Token gate contract address |
| `tasksRefresh` | bool | `true` | Live-refresh triggers/effects while editing tasks. When `true`, changes take effect immediately. When `false`, requires room refresh to apply changes. |
| `roomNodeExtraData` | string | `""` | Additional room node data |

---

## roomSettingsExtraData

All fields below are inside the `roomSettingsExtraData` JSON string.

### Welcome & Onboarding

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `welcomeEmbed` | string | `""` | iframe URL shown on room entry |
| `openWelcomeIframeInBackground` | bool | `false` | Load welcome iframe in background |
| `addWelcomeIframeToInfoButton` | bool | `false` | Add welcome iframe to the info button |
| `showWelcomeOnEntry` | bool | `true` | Show welcome screen when player enters |
| `onboardingType` | int | `1` | `0` = none, `1` = click to drag (default), `2` = toggle cursor lock |
| `requireUsername` | bool | `false` | Force username entry before joining |
| `allowedUsers` | int | `0` | `0` = anyone, `1` = logged-in users only, `2` = crypto wallet required |

### Skybox

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `skyBoxDayTextureUrl` | string | `""` | Custom day skybox texture URL |
| `skyBoxNightTextureUrl` | string | `""` | Custom night skybox texture URL |
| `skyBoxDayRotation` | float | `0` | Day skybox rotation (degrees) |
| `skyBoxNightRotation` | float | `0` | Night skybox rotation (degrees) |
| `skyBoxDayExposure` | float | `1.0` | Day skybox brightness |
| `skyBoxNightExposure` | float | `1.0` | Night skybox brightness |

### Movement (Default)

The `movementValues` object defines the default player physics. All movement states (see [Custom Movement States](#custom-movement-states)) share this same structure.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `movementStateName` | string | `""` | Name (empty for default state) |
| `walkByDefault` | bool | `false` | Start in walk mode instead of run |
| `walkSpeed` | float | `2.0` | Walk speed |
| `runSpeed` | float | `4.0` | Run speed |
| `sprintSpeed` | float | `6.8` | Sprint speed |
| `strafing` | bool | `false` | Enable strafing (side movement without turning) |
| `jumpTimer` | float | `0.3` | Cooldown between jumps (seconds) |
| `jumpHeight` | float | `4.0` | Jump height |
| `airSpeed` | float | `5.0` | Movement speed while airborne |
| `gravity` | float | `-10.0` | Gravity strength (negative = down) |
| `rotationSpeed` | float | `16.0` | Player turn speed |
| `ledgeGrab` | bool | `false` | Enable ledge grabbing |
| `forceFirstPerson` | bool | `false` | Lock to first-person view |
| `stopVerticalInput` | bool | `false` | Disable vertical movement input |
| `stopJumps` | bool | `false` | Disable jumping entirely |

### Custom Movement States

The `movementStates` array defines named movement presets that can be switched to via the `ChangeMovementState` effect. Each entry has the same fields as `movementValues` plus a required `movementStateName`.

`defaultMovementState` (int, default `-1`): Index into `movementStates` to use on room entry. `-1` = use default `movementValues`.

```json
"movementStates": [
  {
    "movementStateName": "swimming",
    "walkByDefault": true,
    "walkSpeed": 1.5,
    "runSpeed": 3.0,
    "sprintSpeed": 4.0,
    "strafing": true,
    "jumpTimer": 0.3,
    "jumpHeight": 2.0,
    "airSpeed": 3.0,
    "gravity": -5.0,
    "rotationSpeed": 12.0,
    "ledgeGrab": false,
    "forceFirstPerson": false,
    "stopVerticalInput": false,
    "stopJumps": false
  }
]
```

### Numeric Parameters (Variables)

The `numericParameters` array defines room variables used by triggers and effects (UpdateScoreEvent, ScoreTrigger, FunctionEffector, etc.).

| Field | Type | Description |
|-------|------|-------------|
| `N` | string | Variable name |
| `VT` | int | Value type: `0` = numeric, `1` = string |
| `M` | bool | Multiplayer synced (shared across all players) |
| `P` | bool | Persistent (saved across sessions) |

```json
"numericParameters": [
  {"N": "score", "VT": 0, "M": false, "P": false},
  {"N": "team_score", "VT": 0, "M": true, "P": false},
  {"N": "high_score", "VT": 0, "M": false, "P": true},
  {"N": "player_name", "VT": 1, "M": false, "P": true}
]
```

### UI Toggles

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `showNameTags` | bool | `true` | Show player name labels |
| `showBackpack` | bool | `true` | Show inventory/backpack button |
| `showQuestLog` | bool | `false` | Show quest log button |
| `showPlayerCount` | bool | `true` | Show player count |
| `showMic` | bool | `true` | Show microphone button |
| `showMusic` | bool | `true` | Show music controls |
| `showEmotes` | bool | `true` | Show emote wheel |
| `showSpaceInfo` | bool | `true` | Show space info button |
| `showCombatUI` | bool | `false` | Show combat controls (attack/block buttons) |
| `requestMicPopup` | bool | `false` | Show mic permission popup on entry |

### Player Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `playerCollisions` | bool | `true` | Players collide with each other |
| `disableHToSpawn` | bool | `false` | Disable the H key spawn shortcut |
| `playJoinSound` | bool | `true` | Play sound when a player joins |
| `jumpSounds` | bool | `false` | Play sound on jump |

### Avatar Types

Multiple avatar types can be enabled simultaneously. Players choose from the enabled types.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `guardianAvatars` | bool | `true` | Default Portals avatars |
| `blockyAvatars` | bool | `false` | Block-style avatars |
| `roundyAvatars` | bool | `false` | Round-style avatars |
| `rpmAvatars` | bool | `false` | Ready Player Me avatars |
| `collectibleAvatars` | bool | `false` | Collectible avatars |
| `customAvatars` | bool | `false` | Custom uploaded avatars |
| `enableCustomAvatars` | bool | `false` | Master toggle for custom avatars |

### Custom Space Avatars

The `customSpaceAvatars` array defines room-specific avatar options. Requires `enableCustomAvatars: true` and `customAvatars: true`.

| Field | Type | Description |
|-------|------|-------------|
| `avatarName` | string | Display name for the avatar |
| `glbUrl` | string | URL to the avatar GLB model |
| `imgUrl` | string | URL to the avatar thumbnail image |

```json
"customSpaceAvatars": [
  {
    "avatarName": "Robot Guard",
    "glbUrl": "https://example.com/robot.glb",
    "imgUrl": "https://example.com/robot-thumb.png"
  }
]
```

### Custom Camera States

The `customCameraStates` array defines named camera presets switchable via the `ChangeCamState` effect.

`defaultCameraState` (int, default `-1`): Index into `customCameraStates` to use on room entry. `-1` = default third-person camera.

| Field | Type | Description |
|-------|------|-------------|
| `stateName` | string | Name of the camera state |
| `cameraMode` | int | `1` = fixed angle (follows player), `2` = fixed position (world space) |
| `distance` | float | Camera distance from player |
| `height` | float | Camera height offset |
| `fov` | float | Field of view (degrees) |
| `right` | float | Horizontal offset |
| `angleX` | float | Vertical angle |
| `angleY` | float | Horizontal angle |
| `pos` | object | World position `{x, y, z}` (used by mode 2) |
| `rot` | object | World rotation `{x, y, z}` (Euler degrees, used by mode 2) |
| `lookAtPlayer` | bool | Camera faces the player (used by mode 2) |

```json
"customCameraStates": [
  {
    "stateName": "top down",
    "cameraMode": 1,
    "distance": 15.0,
    "height": 12.0,
    "fov": 60.0,
    "right": 0.0,
    "angleX": 80.0,
    "angleY": 0.0,
    "pos": {"x": 0, "y": 0, "z": 0},
    "rot": {"x": 0, "y": 0, "z": 0},
    "lookAtPlayer": false
  },
  {
    "stateName": "security cam",
    "cameraMode": 2,
    "distance": 1.5,
    "height": 0.0,
    "fov": 60.0,
    "right": 0.0,
    "angleX": 0.0,
    "angleY": 0.0,
    "pos": {"x": -7.0, "y": 3.2, "z": 1.0},
    "rot": {"x": 22.0, "y": 91.5, "z": 0.0},
    "lookAtPlayer": true
  }
]
```

### Visual Effects

#### Fog

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `fog.DayFogMax` | float | `0.0` | Day fog density (0 = off) |
| `fog.NightFogMax` | float | `0.0` | Night fog density |
| `fog.DayFogColor` | string | `""` | Day fog color (hex) |
| `fog.NightFogColor` | string | `""` | Night fog color (hex) |

#### Post-Processing

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `postprocess.BloomDayIntensity` | float | `0.0` | Day bloom strength |
| `postprocess.BloomNightIntensity` | float | `0.0` | Night bloom strength |
| `postprocess.BloomDayClamp` | float | `0.0` | Day bloom clamp |
| `postprocess.BloomNightClamp` | float | `0.0` | Night bloom clamp |
| `postprocess.BloomDayDiffusion` | float | `0.0` | Day bloom spread |
| `postprocess.BloomNightDiffusion` | float | `0.0` | Night bloom spread |
| `postprocess.CameraMaxDistanceDay` | float | `0.0` | Max camera distance (day) |
| `postprocess.CameraMaxDistanceNight` | float | `0.0` | Max camera distance (night) |

#### Lighting

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `lightValues.NightShadows` | int | `0` | Night shadow mode |

#### Retro Rendering

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `psx` | bool | `false` | PSX-style retro rendering |
| `pixelation` | float | `0.24` | Pixelation amount (lower = more pixelated) |

### Performance

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `preloadRoom` | bool | `false` | Load all GLBs before player enters. Recommended for games to prevent seeing hidden items during load. |
| `fastDownload` | bool | `false` | Faster asset loading. May cause errors in very large rooms. |
| `uncompressedGLB` | bool | `false` | Use uncompressed GLB files |

### Voice Chat

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `voiceChatRange` | float | `14.0` | Voice chat audible distance (units) |
| `globalChat` | bool | `false` | Global text chat (no distance limit) |

### Vehicles

The `carSettings` object defines vehicle physics (when vehicles are in the room).

| Field | Type | Description |
|-------|------|-------------|
| `acceleration` | float | Vehicle acceleration |
| `drag` | float | Vehicle drag/friction |
| `maxSpeed` | float | Top speed |
| `steering` | float | Steering responsiveness |
| `mass` | float | Vehicle mass |
| `gravity` | float | Vehicle gravity |
| `timeToMaxSteer` | float | Time to reach full steering angle |

### Ignored Fields

These fields exist in the data but should be left at defaults:

| Field | Default | Notes |
|-------|---------|-------|
| `EventData` | `"{\"itemNames\":[],\"itemEvents\":[]}"` | Leave empty |
| `RoomItemsData` | `[]` | Leave empty |
| `weaponDatas` | `[]` | Weapon system (not documented) |
| `defaultWeapon` | `-1` | Leave at -1 |
| `releasedRoom` | `""` | Internal use |

---

## Game Design Recommendations

**For platformers**: Tune `jumpHeight`, `gravity`, `airSpeed`, and consider `ledgeGrab`. Use `preloadRoom: true` to hide platforms until loaded. Set `stopJumps: false` (obviously).

**For exploration games**: Lower `runSpeed`/`sprintSpeed` for a slower pace. Enable `strafing` for more natural movement. Consider custom camera states for cinematic moments.

**For competitive games**: Use `M: true` (multiplayer) variables for shared scores. Set `playerCollisions: true`. Enable `showCombatUI` if using the combat system. Set `allowedUsers: 1` to require login.

**For narrative games**: Use `requireUsername: true`, `showQuestLog: true`. Set up a `welcomeEmbed` iframe for story intro. Consider `forceFirstPerson` for immersion. Hide unnecessary UI (`showEmotes: false`, `showMusic: false`).

**For performance**: Enable `preloadRoom` for games with many GLBs. Use `fastDownload` for medium-sized rooms. Avoid both on very large rooms (500+ items).
