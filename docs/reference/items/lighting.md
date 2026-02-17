# Lighting Items

Light sources for illuminating spaces.

## Light

Static point light source. Lights are on by default.

**Base structure:**
```json
{
  "prefabName": "Light",
  "pos": {"x": 0, "y": 3, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"c\":\"FFFFFF\",\"b\":2.0,\"r\":10.0,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**
- `c`: Light color. 6-char hex, no `#` prefix. e.g., `"7BFB00"` for green.
- `b`: Brightness intensity. Higher = brighter. Omit for default.
- `r`: Range. How far the light reaches. Omit for default.
- `no`: Only night. `true` = light only active when room is set to night mode. Omit for always on.

---

## BlinkLight

Animated flashing/blinking light. Same base fields as Light with additional blink controls.

**Base structure:**
```json
{
  "prefabName": "BlinkLight",
  "pos": {"x": 0, "y": 3, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"c\":\"FFB200\",\"b\":2.5,\"r\":7.0,\"bd\":1.2,\"bi\":2.6,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**
- `c`: Light color. 6-char hex, no `#` prefix.
- `b`: Brightness intensity. Omit for default.
- `r`: Range. How far the light reaches. Omit for default.
- `bd`: Blink duration. How long the light stays on (in seconds).
- `bi`: Blink interval. Time between blinks (in seconds).
- `no`: Only night. `true` = light only active in night mode. Omit for always on.

---

## SpotLight

Directional cone light. Points in the direction set by `rot`.

**Base structure:**
```json
{
  "prefabName": "SpotLight",
  "pos": {"x": 0, "y": 3, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"c\":\"FFFFFF\",\"b\":2.0,\"r\":5.0,\"ang\":80.0,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**
- `c`: Light color. 6-char hex, no `#` prefix.
- `b`: Brightness intensity. Omit for default.
- `r`: Range. How far the light reaches. Omit for default.
- `ang`: Spread angle (degrees). Controls how wide the spotlight cone is. Smaller = narrow beam, larger = wide flood.

---

## Light Toggle via Effects

Lights are on by default. To control them dynamically:
- Use `HideObjectEvent` to turn a light off
- Use `ShowObjectEvent` to turn a light on
