# Display Items

Leaderboards, charts, and billboards for displaying information.

## Chart

3D candlestick chart displaying a Solana token's price. Uses `prefabName: "Chart"`. Always displays 25 candles. At scale 1, the chart is 7 meters wide and 3 meters tall in-world. Requires a 90-degree Y rotation for proper orientation.

**Base structure:**
```json
{
  "prefabName": "Chart",
  "pos": {"x": 0, "y": 0.5, "z": 0},
  "rot": {"x": 0, "y": 0.7071068, "z": 0, "w": 0.7071068},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "PRTLSwfLzpVGSAQiUfXEenJkq1cwTsEcsn1hPL9zwwg",
  "extraData": "{\"h\":11.0,\"r\":0.0,\"c\":true,\"t\":0,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key fields:**
- `contentString`: Solana token address. The chart displays this token's price data.
- `rot`: Use `{x:0, y:0.7071068, z:0, w:0.7071068}` (90-degree Y rotation) for proper orientation.
- `scale`: Proportional scaling. At `1`, the chart is 7m wide x 3m tall.

**extraData fields:**
- `t`: Time interval for each candle. See table below.
- `h`: Candle height scale. Controls how tall the candles appear. Higher = taller candles.
- `r`: Curve rotation (degrees). Curves the chart along an arc. `0.0` = flat. `14.4` = perfect circle (since there are always 25 candles, 360 / 25 = 14.4 degrees per candle).
- `c`: Collision. `true` = solid, players collide with the chart. `false` = players pass through.

**Time intervals:**

| Value | Interval |
|-------|----------|
| `0` | 1 minute |
| `1` | 15 minutes |
| `2` | 60 minutes |

---

## Leaderboard

Displays player rankings and scores. Uses `prefabName: "Leaderboard"`. The visual style is chosen via `contentString` -- only the 3 standard leaderboard models are supported. Leaderboards can display either time-based or numeric (points) values.

**Base structure:**
```json
{
  "prefabName": "Leaderboard",
  "pos": {"x": 0, "y": 0.75, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "~1slpk_Leaderboard_Black_NeonBlue.glb?alt=media&token=8b518415-b51b-4264-ae7e-d49465260757",
  "extraData": "{\"gn\":\"Game Name\",\"ln\":\"Score Label\",\"ci\":\"\",\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Leaderboard models:**

Set `contentString` to one of these values:

| Style | contentString |
|-------|---------------|
| Black / Neon Blue | `~1slpk_Leaderboard_Black_NeonBlue.glb?alt=media&token=8b518415-b51b-4264-ae7e-d49465260757` |
| Gray / Neon Orange | `~5wnot_Leaderboard_Gray_NeonOrange.glb?alt=media&token=5312ebfe-b00b-4f99-ad4b-a72bd518a74a` |
| Screen Only | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2F00L_screenLeaderboard.glb?alt=media&token=b1f9eef5-ee70-4d5e-a9ee-3e8e2ef26e59?screenOnly=true` |

**extraData fields:**
- `gn`: Game name displayed on the leaderboard.
- `ln`: Score label (e.g., "Points", "Time", "Score").
- `tb`: Time-based. `true` = leaderboard displays time values. `false` or omit = displays numeric values (points).
- `ci`: Custom identifier for the data source. Empty string `""` for standard score tracking. Set to `"swapsPerRoom"` to track token swap volume (specific to rooms with token trading).

---

## Billboard (GLBSign)

Pre-built hanging sign model with a customizable image. Uses `prefabName: "GLBSign"`. The sign shape is chosen via a `GLBUrl` in extraData -- only the standard billboard GLB URLs below are supported. The `contentString` holds the image displayed on the sign.

**Base structure:**
```json
{
  "prefabName": "GLBSign",
  "pos": {"x": 0, "y": 0, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "contentString": "https://example.com/sign-image.png",
  "extraData": "{\"GLBUrl\":\"https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_SmallSquare_A_Rig.glb\"}"
}
```

**Key fields:**
- `contentString`: Image URL displayed on the sign face. Any publicly hosted image works.
- `scale`: Proportional multiplier on the sign model size. Scales uniformly.

**extraData fields:**
- `GLBUrl`: **Required.** The billboard model URL. Must be one of the standard URLs listed below.
- `c`: Billboard border color. 6-char hex, no `#` prefix. e.g., `"449C18"` for green.
- `e`: Emission/glow intensity. e.g., `1.0` for full glow. Omit for no glow.
- `so`: Shadow off. `true` = no shadows. Omit for default (shadows on).

**Standard billboard GLB URLs:**

These are the only valid `GLBUrl` values:

| Sign Type | URL |
|-----------|-----|
| 3-Sided A | `https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_3Sided_A_Rig.glb` |
| Medium Vertical A | `https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_MediumVertical_A_Rig.glb?selectedID=0` |
| Medium Vertical B | `https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_MediumVertical_B_Rig.glb?selectedID=0` |
| Large Vertical B | `https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_LargeVertical_B_Rig.glb?selectedID=0` |
| Small Square A (with attachments) | `https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_SmallSquare_A_Rig.glb` |
| Small Square B (with attachments) | `https://dwh7ute75zx34.cloudfront.net/Models/08_09/HangingSigns_SmallSquare_B_Rig.glb` |
| Small Square A (no attachments) | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FHanging%20Signs%20SmallSquare%20A%20No%20Attachments_HangingSigns_SmallSquare_A_NoAttachments.glb?alt=media&token=22da1096-457e-42f8-878e-da6912b5f4c5` |
| Small Square B (no attachments) | `https://firebasestorage.googleapis.com/v0/b/portals-1b487.appspot.com/o/GLBs%2FHanging%20Signs%20Small%20Square%20B%20No%20Attachments_HangingSigns_SmallSquare_B_NoAttachments.glb?alt=media&token=ab45dddf-50e7-429f-85de-e53b3cc7c0ad` |
