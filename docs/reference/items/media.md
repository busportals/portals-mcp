# Media Items

Media content placed in 3D space — images, videos, and screen shares.

## DefaultPainting

2D image placed in 3D space. Images need to be rotated to display upright — without rotation they lie flat on the ground. Use `scale` to control width, height, and thickness.

**Base structure:**
```json
{
  "prefabName": "DefaultPainting",
  "parentItemID": 0,
  "pos": {"x": 0, "y": 1, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 2.0, "y": 1.5, "z": 0.03},
  "contentString": "https://cdn.theportal.to/uploads/room-id/image.png",
  "interactivityType": 0,
  "interactivityURL": "",
  "extraData": "{\"t\":true,\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key fields:**
- `contentString`: Image URL. Any publicly hosted image works.
- `interactivityType`: `0` = no click interaction (preferred). `3` = click to view full image.
- `interactivityURL`: URL shown on click. Usually same as `contentString`. Only needed when `interactivityType` is `3`.
- `scale`: Controls image dimensions. `x` = width, `y` = height, `z` = thickness (keep thin, e.g. `0.03`). Size is relative to the image's pixel dimensions — a 100x200px image might appear as `0.5 x 1.0` in-world.

**extraData fields:**
- `t`: Transparency. `true` = PNG transparency is respected. Omit for opaque images.
- `b`: Borderless / frame off. `true` = no frame around the image. Omit for default frame.
- `e`: Emission/glow intensity. e.g., `0.5` for moderate glow. Omit for no glow.

**Orientation:**

Images default to lying flat on the ground. Set the `rot` quaternion to orient them upright. Images can also be parented to a ResizableCube via `parentItemID` to mount them on walls — when parented, `pos` and `rot` are relative to the parent item.

---

## DefaultVideo

MP4 video placed in 3D space. Only accepts `.mp4` files. Unlike images, videos display upright by default with identity rotation — no rotation needed.

**Base structure:**
```json
{
  "prefabName": "DefaultVideo",
  "pos": {"x": 0, "y": 0.75, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 3.0, "y": 1.7, "z": 0.03},
  "contentString": "https://d365bxku1h71bo.cloudfront.net/uploads/room-id/videos/example.mp4",
  "extraData": "{\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**Key fields:**
- `contentString`: MP4 video URL. Must be a full, publicly accessible URL.
- `scale`: Controls video dimensions. `x` = width, `y` = height, `z` = thickness (keep thin, e.g. `0.03`). Size is relative to the video's pixel dimensions — a 100x200px video might appear as `0.5 x 1.0` in-world.

**extraData fields:**
- `b`: Borderless / frame off. `true` = no frame around the video. Omit or `false` for default frame.
- `e`: Emission/glow intensity. e.g., `1.0` for full glow. Omit for no glow.
- `fStart`: Sound falloff start distance (meters). Beyond this distance, the video's audio begins to get quieter.
- `sEnd`: Sound falloff end distance (meters). At this distance, the audio is completely silent.

**Orientation:**

Videos display upright by default (unlike images which lie flat). Identity rotation `{x:0, y:0, z:0, w:1}` produces a correctly oriented, upright video.

---

## PlaceableTV

Screen sharing display that allows players to share their screen in-world. Displays upright by default with identity rotation. Scale resizes the screen proportionally.

**Base structure:**
```json
{
  "prefabName": "PlaceableTV",
  "pos": {"x": 0, "y": 1, "z": 0},
  "rot": {"x": 0, "y": 0, "z": 0, "w": 1},
  "scale": {"x": 1, "y": 1, "z": 1},
  "extraData": "{\"Tasks\":[],\"ViewNodes\":[]}"
}
```

**extraData fields:**
- `useSpatialAudio`: `true` = audio volume changes based on player distance from the screen. Omit for non-spatial audio.
- `fullVolumeRange`: Distance (meters) within which audio plays at full volume. Beyond this distance, audio fades out. Only relevant when `useSpatialAudio` is `true`.
