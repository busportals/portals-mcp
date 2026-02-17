# Interactive Items

NPCs and interactive characters.

## NPC (GLBNPC)

Interactive non-player character with dialogue and AI. Uses `prefabName: "GLBNPC"`. NPCs sit on the ground at `y=0` (not `y=0.5` like cubes).

**Base structure:**
```json
{
  "prefabName": "GLBNPC",
  "pos": {"x": 0, "y": 0, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "https://example.com/avatar.glb",
  "extraData": "{\"n\":\"Guard\",\"a\":\"Salute\",\"p\":\"You are a palace guard. Be stern but helpful.\",\"bq\":true,\"swn\":true,\"events\":[],\"tags\":[],\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**NPC avatar (contentString):**

The `contentString` holds the GLB model URL. Two types are supported:

| GLB Type | URL Format |
|----------|------------|
| **Rigged** (has skeleton/animations) | Use the straight GLB URL |
| **Non-rigged** (static model) | Append `?nonrigged=true` to the GLB URL |

**extraData fields:**
- `n`: NPC display name. Can be any string.
- `a`: Default animation. Empty string `""` for idle. See permitted animations table below.
- `p`: AI personality prompt. When set, the NPC assumes this personality and players can chat with it via messages. Can be any descriptive text.
- `bq`: `true` to enable.
- `swn`: Show when near / auto popup. `true` = NPC dialogue appears automatically when player approaches. Omit for manual interaction.
- `events`: Array of events. Usually `[]`.
- `tags`: Array of tags. Usually `[]`.

**Permitted NPC animations:**

| Animation Name |
|---------------|
| `Sitting` |
| `Can Can` |
| `Wave` |
| `Salute` |
| `Jive` |
| `Salsa` |
| `Shuffling` |
| `Chicken` |
| `Slide n Jive` |
| `Robot` |

Use an empty string `""` for the default idle animation.
