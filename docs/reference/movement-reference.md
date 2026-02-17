# Player Movement Reference

Empirical measurements for level design. All values measured with **default movement settings** (jumpHeight=4.0, gravity=-10.0, airSpeed=5.0, runSpeed=4.0, sprintSpeed=6.8).

Test room: `8dda512b-f2ad-467b-b7ba-b2821d4410e3`

---

## Player Dimensions

| Property | Value | Notes |
|----------|-------|-------|
| Width | ~1.0m | Minimum gap the player can fit through |
| Height | ~1.6m | Also the ledge-grab reach distance |
| Camera clearance | ~2.0m minimum | Camera collides with low ceilings; use >2m in practice |

---

## Default Jump (No Jump Pad)

| Property | Value |
|----------|-------|
| Max height | ~1.63m |
| Time to apex | ~0.3s |
| Total airtime | ~0.6s |
| Arc shape | Symmetric (max height at midpoint) |

### Horizontal Distance (Default Jump)

| Movement | Max Distance |
|----------|-------------|
| Running (hold forward) | ~3.6m |
| Sprinting (hold shift) | ~4.3m |

**Design rule:** A gap wider than 3.5m requires a sprint jump at default settings. Gaps wider than 4m are near the limit — add a small margin for player error (keep gaps ≤3.8m for comfortable sprint jumps).

---

## Jump Pad Heights

Jump pads have a UI power setting from 1-10. Setting 1 equals a normal jump.

| Setting | Max Height | Status |
|---------|-----------|--------|
| 1 | ~1.63m | Same as default jump |
| 2 | ~3.5m | Measured |
| 3 | ~6.73m | Measured |
| 4 | ? | Needs testing |
| 5 | ? | Needs testing |
| 6 | ? | Needs testing |
| 7 | ? | Needs testing |
| 8 | ? | Needs testing |
| 9 | ? | Needs testing |
| 10 | ? | Needs testing |

**Note:** The `p` field in jump pad extraData (`"p": 6.9`) is a float that the UI slider maps to. The mapping from UI setting (1-10) to `p` value is not yet documented.

---

## Jump Pad Horizontal Distance

Players **keep horizontal momentum** through jump pads and can **air-steer** while airborne.

| Setting | Horizontal Distance (running) | Status |
|---------|------------------------------|--------|
| 1 | ~3.6m (same as default) | Derived |
| 2 | ~8.3m | Measured |
| 3 | ~22.5m | Measured |
| 4-10 | ? | Needs testing |

**Note:** The large jump from 8.3m (setting 2) to 22.5m (setting 3) is expected — higher launches mean much longer airtime, and horizontal momentum + air steer compound over that time.

---

## Ledge Grab

When `ledgeGrab: true` in movement settings:
- Adds ~1.6m (player height) to reachable height
- Player grabs the ledge and pulls up

| Scenario | Max Reachable Height |
|----------|---------------------|
| Default jump | ~1.63m |
| Default jump + ledge grab | ~3.23m |
| Jump pad 2 | ~3.5m |
| Jump pad 2 + ledge grab | ~5.1m |
| Jump pad 3 | ~6.73m |
| Jump pad 3 + ledge grab | ~8.33m |

---

## Custom Movement Settings

The `jumpHeight` setting scales actual jump height roughly linearly:

| jumpHeight setting | Approximate actual max height |
|--------------------|-------------------------------|
| 2.0 | ~0.8m |
| 4.0 (default) | ~1.63m |
| 6.0 | ~2.4m |
| 8.0 | ~3.3m |

Ratio: **actual_height ≈ jumpHeight × 0.41** (approximate).

Gravity, airSpeed, and movement speeds also affect jump arcs. Changing these requires re-testing if precise measurements are needed.

---

## Level Design Guidelines

### Platform Heights

| Target | Max Recommended Height | Method |
|--------|----------------------|--------|
| Easy step-up | ≤0.5m | Walk onto it |
| Normal jump | ≤1.4m | Default jump with margin |
| Hard jump | 1.4–1.6m | Near max height, tight |
| Jump pad required | >1.6m | Use jump pad or ledge grab |

### Gap Widths

| Target | Max Recommended Gap | Method |
|--------|--------------------|--------|
| Easy gap | ≤2.5m | Running jump, forgiving |
| Normal gap | 2.5–3.2m | Running jump, moderate |
| Hard gap | 3.2–3.6m | Sprint jump required |
| Near-impossible | 3.6–4.3m | Perfect sprint jump |
| Jump pad required | >4.3m | Use jump pad |

### Combined Height + Distance

For jumps that go both up AND across, the arc must reach the target height **before** or **at** the horizontal midpoint. Because the arc is symmetric:

- If the platform is at the **same height**: max gap = full horizontal distance
- If the platform is **higher**: the arc must have enough height remaining at the horizontal distance of the platform. Higher targets reduce effective gap distance.
- If the platform is **lower**: the player has more airtime, so the effective gap distance increases.

**Rule of thumb:** For every 0.5m of height gain, reduce the max comfortable gap by ~0.5m.

| Jump Type | Height Gain | Comfortable Gap |
|-----------|-------------|-----------------|
| Running jump, same height | 0m | 3.0m |
| Running jump, +0.5m | 0.5m | 2.5m |
| Running jump, +1.0m | 1.0m | 2.0m |
| Running jump, +1.5m | 1.5m | near-impossible |
| Sprint jump, same height | 0m | 3.6m |
| Sprint jump, +0.5m | 0.5m | 3.0m |
| Sprint jump, +1.0m | 1.0m | 2.5m |

### Minimum Platform Sizes

| Difficulty | Minimum Width/Depth |
|------------|-------------------|
| Easy / casual | 2.0m x 2.0m |
| Normal | 1.5m x 1.5m |
| Hard | 1.0m x 1.0m |
| Expert | 0.5m x 0.5m (near player width) |

### Ceiling Clearance

- Minimum: 2.0m (camera collision threshold)
- Comfortable: 2.5m+
- If player needs to jump in the area: ceiling must be at least jump height + 2.0m above the floor

### Jump Pad Placement

- Place jump pads where players naturally approach from — don't require precision to step onto the pad
- Scale jump pads to 1.5-2.0x for easier targeting in fast-paced sequences
- For directional launches, ensure the landing zone is visible from the pad
- Include a landing zone at least 2.0m x 2.0m at the destination
- For jump pad setting 3+, the landing zone should be clearly marked — players travel far and need visual guidance

---

## Quick Reference Card

```
DEFAULT JUMP
  Height:     1.63m
  Run gap:    3.6m
  Sprint gap: 4.3m
  Airtime:    0.6s

JUMP PAD 2
  Height:  3.5m
  Run gap: 8.3m

JUMP PAD 3
  Height:  6.73m
  Run gap: 22.5m

PLAYER
  Width:   1.0m
  Height:  1.6m
  Camera:  2.0m clearance

LEDGE GRAB
  Adds:    1.6m to reachable height
```
