# Station Omega — Last Transmission Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete 5-zone mystery exploration game on room `c0df789f-c9a9-43f1-a88c-214e484a8c71` (spaceship template).

**Architecture:** Seven Python component files (one per zone + settings + quests) assembled by a thin `generate.py` compositor. Each zone component returns a `refs` dict of key item IDs so the quest component can wire cross-zone logic. Items and logic are built as dicts during generation; `serialize_logic()` is called once at the end before writing `snapshot.json`.

**Tech Stack:** Python 3, `lib/portals_core.py`, `lib/portals_effects.py`, `lib/portals_utils.py`, `tools/validate_room.py`

---

## World Coordinate System

The station runs linearly along the Z-axis. Player moves from spawn (z=0) toward escape pod (z~55). Corridor width: 8 units (x = -4 to +4). Ceiling height: 4 units.

```
Zone 1: Crew Quarters    z=0  → z=12   (spawn here)
Zone 2: Medical Bay      z=12 → z=22
Zone 3: Reactor          z=22 → z=38   (wider: x=-6 to +6, h=8 for vertical drama)
Zone 4: Research Wing    z=38 → z=48
Zone 5: Lab 4 + Pod Bay  z=48 → z=62
```

Each zone has a "gate" — a locked door (thin ResizableCube wall) and a terminal trigger to open it — except Zone 1 (open from spawn) and Zone 5 (unlocked by completing all 8 logs).

---

## Data Log Layout

| Log | Zone | Description |
|-----|------|-------------|
| Log 01 | Crew Quarters | Torres — food recycler complaint, normal life |
| Log 02 | Crew Quarters | Nakamura — excited about Lab 4 breakthrough |
| Log 03 | Medical Bay | Osei — worried, Vasquez hiding something |
| Log 04 | Medical Bay | Reinholt — refuses to discuss Lab 4 |
| Log 05 | Engineering | Patel — locked her bunk, word "containment" |
| Log 06 | Engineering | Cho — trying to mediate, sides forming |
| Log 07 | Research Wing | Lindqvist — others are gone, almost over |
| Log 08 | Research Wing | Vasquez — afraid of you, last entry |

Log 08 is the most emotionally loaded. It ends: *"Whatever you are now... I don't think you wanted this."*

---

## Component Architecture

```
games/c0df789f-c9a9-43f1-a88c-214e484a8c71/
  generate.py                    ← thin compositor (~60 lines)
  components/
    settings.py                  ← room settings, spawn
    zone_crew_quarters.py        ← Zone 1: scene + local logic
    zone_medical.py              ← Zone 2: scene + local logic
    zone_reactor.py              ← Zone 3: scene + local logic
    zone_research.py             ← Zone 4: scene + local logic
    zone_lab4.py                 ← Zone 5: scene + ARIA finale
    quests.py                    ← master quest + cross-zone wiring
```

---

## Refs Contract

Each zone component returns a `refs` dict. `generate.py` passes these to `quests.py`.

```python
# zone_crew_quarters.py returns:
{
    "log_01_trigger": id_,   # trigger zone for log 01
    "log_01_visual": id_,    # glowing cube for log 01
    "log_02_trigger": id_,   # trigger zone for log 02
    "log_02_visual": id_,    # glowing cube for log 02
    "door_to_medical": id_,  # cube wall blocking Zone 2
}

# zone_medical.py returns:
{
    "log_03_trigger": id_,
    "log_03_visual": id_,
    "log_04_trigger": id_,
    "log_04_visual": id_,
    "terminal_medical": id_,  # trigger zone activating door
    "door_to_reactor": id_,
}

# zone_reactor.py returns:
{
    "log_05_trigger": id_,
    "log_05_visual": id_,
    "log_06_trigger": id_,
    "log_06_visual": id_,
    "terminal_reactor": id_,
    "door_to_research": id_,
    "reactor_respawn_trigger": id_,  # fall zone → respawn
}

# zone_research.py returns:
{
    "log_07_trigger": id_,
    "log_07_visual": id_,
    "log_08_trigger": id_,
    "log_08_visual": id_,
    "terminal_research": id_,
    "door_to_lab4": id_,
}

# zone_lab4.py returns:
{
    "pod_trigger": id_,         # escape pod trigger
    "aria_lab4": id_,           # ARIA NPC (final speech)
    "pod_bay_lights": [id_, ...], # lights that turn on for finale
}
```

---

## Quest Design

One master quest: **"Find all crew logs and escape"**

Quest states (using Portals 3-state system):
- State 0: Default (initial)
- State 1: Log collected (used to hide the visual cube via `quest_effector`)

Each log uses a separate quest + task:
- `quest_log_01` through `quest_log_08` — simple 2-state quests
- Collecting log trigger → State 1 → hides visual cube + shows notification

Final quest: `quest_escape` — activated after all 8 logs collected (via FunctionEffector checking log quest states). Fires: ARIA finale sequence → pod bay lights on → pod trigger activates.

Door unlocks use direct trigger/effector (not quests):
- `terminal_medical` OnCollide → `door_to_medical` HideObjectEvent
- `terminal_reactor` OnCollide → `door_to_reactor` HideObjectEvent
- `terminal_research` OnCollide → `door_to_research` HideObjectEvent
- All 8 logs collected → `door_to_lab4` HideObjectEvent (via FunctionEffector)

---

## Task 1: Scaffold — `generate.py` and `components/` directory

**Files:**
- Create: `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/generate.py`
- Create: `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/__init__.py` (empty)

**Step 1: Create components directory**
```bash
mkdir -p "games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components"
touch "games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/__init__.py"
```

**Step 2: Write generate.py**

```python
"""
Station Omega — Last Transmission
generate.py: thin compositor — assembles all components into snapshot.json
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from portals_utils import make_id_generator, serialize_logic

from components.settings import build_settings
from components.zone_crew_quarters import build_crew_quarters
from components.zone_medical import build_medical
from components.zone_reactor import build_reactor
from components.zone_research import build_research
from components.zone_lab4 import build_lab4
from components.quests import build_quests

ROOM_ID = "c0df789f-c9a9-43f1-a88c-214e484a8c71"

def main():
    items = {}
    logic = {}
    next_id = make_id_generator()

    # Settings (returns settings dict, not items)
    settings = build_settings()

    # Zone 1
    refs_quarters = build_crew_quarters(items, logic, next_id)

    # Zone 2
    refs_medical = build_medical(items, logic, next_id)

    # Zone 3
    refs_reactor = build_reactor(items, logic, next_id)

    # Zone 4
    refs_research = build_research(items, logic, next_id)

    # Zone 5
    refs_lab4 = build_lab4(items, logic, next_id)

    # Quest wiring (needs all refs)
    all_refs = {**refs_quarters, **refs_medical, **refs_reactor, **refs_research, **refs_lab4}
    quests, room_tasks = build_quests(items, logic, next_id, all_refs)

    # Assemble room data
    room_data = {
        "roomItems": items,
        "settings": settings,
        "roomTasks": room_tasks,
        "quests": quests,
        "logic": serialize_logic({"roomItems": items, "logic": logic})["logic"]
    }

    out_path = os.path.join(os.path.dirname(__file__), "snapshot.json")
    with open(out_path, "w") as f:
        json.dump(room_data, f, indent=2)
    print(f"Written: {out_path} ({len(items)} items, {len(quests)} quests)")

if __name__ == "__main__":
    main()
```

**Step 3: Verify portals_utils has `make_id_generator`**

Run: `grep -n "make_id_generator\|def make_id" lib/portals_utils.py`

If not found, `make_id_generator` should return a function that generates sequential string IDs:
```python
def make_id_generator():
    counter = [0]
    def next_id():
        counter[0] += 1
        return str(counter[0])
    return next_id
```
Add to portals_utils.py if missing.

**Step 4: Verify serialize_logic signature**
Run: `grep -n "def serialize_logic" lib/portals_utils.py`
Expected: takes room_data dict, returns modified dict with logic values as JSON strings.

---

## Task 2: Settings Component

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/settings.py`

**Reference:** `docs/reference/settings.md`

Build room settings that establish the Station Omega atmosphere:
- **Fog**: enabled, dark blue-black, density ~0.03
- **Ambient light**: very dim (0.1), let placed lights do the work
- **Bloom**: enabled, intensity 0.3 (makes emissive lights glow beautifully)
- **Movement profile**: default (no changes needed)
- **Skybox**: dark space skybox if available, otherwise default dark
- **Gravity**: default
- No avatar restrictions

```python
"""
Station Omega — Settings
Sets atmospheric room settings: fog, bloom, dark ambient.
"""
import json

def build_settings():
    extra_data = {
        "FogEnabled": True,
        "FogColor": "0a0a1a",
        "FogDensity": 0.03,
        "AmbientLightIntensity": 0.1,
        "BloomEnabled": True,
        "BloomIntensity": 0.3,
    }
    return {
        "roomSettingsExtraData": json.dumps(extra_data),
        # add other top-level settings fields as needed per docs/reference/settings.md
    }
```

Read `docs/reference/settings.md` for the full field names — the above are approximations.

---

## Task 3: Zone 1 — Crew Quarters

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/zone_crew_quarters.py`

**Reads:** `lib/portals_core.py`, `lib/portals_effects.py`, `docs/reference/items/building.md`, `docs/reference/items/gameplay.md`

**Coordinate range:** x: -4 to +4, z: 0 to 12, y: 0 to 4

### Layout

```
[SPAWN]  [BUNK R]  [BUNK L]  [BUNK R]
  z=2      z=4       z=4       z=7

[LOG 01]            [LOG 02]
  on bunk z=4         on shelf z=8

[DOOR TO MEDICAL] — thin wall at z=12 (hidden by default = NO, visible = blocks passage)
```

### Items to Build

**Structural:**
- Floor: ResizableCube 8×0.2×12, pos (0, -0.1, 6), color "1a1a2e" (dark blue-black)
- Ceiling: ResizableCube 8×0.2×12, pos (0, 4.1, 6), color "111122"
- Left wall: ResizableCube 0.2×4×12, pos (-4, 2, 6), color "1e1e30"
- Right wall: ResizableCube 0.2×4×12, pos (4, 2, 6), color "1e1e30"
- Back wall: ResizableCube 8×4×0.2, pos (0, 2, 0), color "1e1e30"
- Door wall: ResizableCube 8×4×0.2, pos (0, 2, 12), color "1e1e30" — this is `door_to_medical` (gets hidden when terminal activated)

**Bunks (ResizableCubes):**
- Bunk frame right: 1.8×0.15×2.2, pos (3, 0.5, 4.5), color "2a2a3e"
- Bunk mattress right: 1.6×0.1×2.0, pos (3, 0.65, 4.5), color "3a2a2a" (dark red)
- Bunk frame left: 1.8×0.15×2.2, pos (-3, 0.5, 7), color "2a2a3e"
- Personal shelf: 0.8×0.1×0.4, pos (-3.5, 1.5, 7), color "2a2a3e"
- Jacket hook (small cube): 0.1×0.3×0.1, pos (3.5, 2.0, 3), color "333333"

**Lighting:**
- Red emergency strip (Light): pos (0, 3.8, 3), color "FF1100", intensity 0.8, range 8
- Red emergency strip (Light): pos (0, 3.8, 9), color "FF1100", intensity 0.8, range 8
- BlinkLight at ceiling mid-zone: pos (0, 3.7, 6), color "FFFFFF", intensity 0.3 — creates the flickering effect

**Data Log 01** (Torres):
- Visual: ResizableCube 0.25×0.25×0.25, pos (3, 0.83, 4.5), color "FFAA00", emission=2.5 → `log_01_visual`
- Trigger: Trigger (OnCollide), pos (3, 0.83, 4.5), scale (0.6, 0.6, 0.6) → `log_01_trigger`

**Data Log 02** (Nakamura):
- Visual: ResizableCube 0.25×0.25×0.25, pos (-3.5, 1.65, 7), color "FFAA00", emission=2.5 → `log_02_visual`
- Trigger: Trigger (OnCollide), pos (-3.5, 1.65, 7), scale (0.6, 0.6, 0.6) → `log_02_trigger`

**Spawn Point:**
- SpawnPoint at pos (0, 0, 1.5) — facing +Z (into the room)

### Logic

Log 01 trigger (OnCollide) → chain:
1. Hide `log_01_visual`
2. Notification: amber (#FFAA00): `"[Log 01 — Torres] 'Food recycler's broken again. Third time this month. Vasquez says parts are coming on the next supply run. Sure they are.' — 142 days ago"`

Log 02 trigger (OnCollide) → chain:
1. Hide `log_02_visual`
2. Notification: amber: `"[Log 02 — Nakamura] 'Breakthrough in Lab 4 today. Can't say what yet but Dr. Vasquez looked... excited? She never looks excited. Something big is happening.' — 134 days ago"`

Door wall (`door_to_medical`) starts as a VISIBLE blocking wall. It gets hidden when the Zone 2 terminal is activated (wired in quests.py).

### Returns
```python
return {
    "log_01_trigger": log_01_trigger_id,
    "log_01_visual": log_01_visual_id,
    "log_02_trigger": log_02_trigger_id,
    "log_02_visual": log_02_visual_id,
    "door_to_medical": door_to_medical_id,
}
```

---

## Task 4: Zone 2 — Medical Bay

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/zone_medical.py`

**Coordinate range:** x: -4 to +4, z: 12 to 22, y: 0 to 4

### Layout

```
[TERMINAL]  [EXAM TABLE]  [LOG 03]
  z=14         z=17         on table

               [LOG 04]  [MEDICAL SCREEN glow]
               shelf z=20

[DOOR TO REACTOR] at z=22
```

### Items to Build

**Structural (same dark palette as Zone 1):**
- Floor, ceiling, left wall, right wall spanning z=12 to z=22
- Door wall: pos (0, 2, 22) — `door_to_reactor`

**Terminal** (activates this door):
- ResizableCube 0.6×1.0×0.3, pos (-3, 0.5, 14), color "004466" (dark teal) — visual terminal
- Screen face: ResizableCube 0.5×0.6×0.05, pos (-3, 0.8, 14.16), color "00AAFF", emission=1.5
- WorldText on screen: "SECTOR LOCK: MEDICAL\n[ENTER TO UNLOCK]", pos (-3, 0.85, 14.2), scale (0.3, 0.3, 0.3)
- Trigger zone: Trigger (OnCollide) 1.5×2×1.5, pos (-3, 1, 14) → `terminal_medical`

**Medical props:**
- Exam table: ResizableCube 1.8×0.6×2.5, pos (2, 0.3, 17), color "2a2a3e"
- Overturned chair: ResizableCube 0.5×0.5×0.5, pos (-1, 0.25, 19), color "333344", rot slightly tilted
- Supply cabinet (closed): ResizableCube 0.8×1.8×0.4, pos (3.5, 0.9, 21), color "2a2a3e"
- Medical screen glow: Light at (-3.5, 2.5, 18), color "00FFAA", intensity 0.6, range 5

**BlinkLight:** pos (0, 3.7, 16), color "00FFAA", intensity 0.2

**Data Log 03** (Osei):
- Visual: pos (2, 0.95, 17), color "FFAA00", emission=2.5 → `log_03_visual`
- Trigger: pos (2, 0.95, 17) → `log_03_trigger`
- Notification: `"[Log 03 — Osei] 'Something happened in Lab 4. Nobody's talking about it. Vasquez cancelled the weekly briefing. Reinholt won't go back. I asked Torres and he just... changed the subject.' — 121 days ago"`

**Data Log 04** (Reinholt):
- Visual: pos (3.5, 1.9, 21.2), color "FFAA00", emission=2.5 → `log_04_visual`
- Trigger: pos (3.5, 1.9, 21.2) → `log_04_trigger`
- Notification: `"[Log 04 — Reinholt] 'I'm not going back to Lab 4. I'm not explaining why. If anyone asks, I was never in Lab 4. Whatever Vasquez is running in there — that's not science anymore.' — 118 days ago"`

**Terminal logic:**
- OnCollide → Notification: teal (#00AAFF) "Access granted — Medical sector unlocked"
- OnCollide → PlaySoundOnce: door unlock sound

### Returns
```python
return {
    "log_03_trigger": ..., "log_03_visual": ...,
    "log_04_trigger": ..., "log_04_visual": ...,
    "terminal_medical": ...,
    "door_to_reactor": ...,
}
```

---

## Task 5: Zone 3 — Engineering / Reactor

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/zone_reactor.py`

**Coordinate range:** x: -6 to +6, z: 22 to 38, y: 0 to 8 ← **wider and taller for drama**

This is the most complex zone. The floor opens into a reactor void in the center, with platforms the player must jump across. The reactor core is visible below.

### Layout (top-down, y=0 level)

```
[ENTRY CORRIDOR]  z=22-25  (normal floor)
[REACTOR VOID]    z=25-35  (floor drops away — platforms cross it)
[EXIT CORRIDOR]   z=35-38  (normal floor + terminal)

Platforms at y=1.5 crossing the void:
- Platform A: x=-5 to -2, z=25-27 (left entry)
- Platform B: x=-2 to +2, z=27-29 (center)
- Platform C: x=+2 to +5, z=29-32 (right)
- Platform D: x=-1 to +1, z=32-35 (exit)

JumpPads on Platform A (launch to B) and Platform C (launch to D)
Reactor core visual: large orange glowing cube far below at y=-8
Fall zone trigger: covers the void area (y=-1 to -5)
```

### Items to Build

**Entry corridor (z=22-25):**
- Floor 12×0.2×3, ceiling 12×0.2×3, walls
- Warning sign (WorldText): "REACTOR ZONE — CAUTION — COMPROMISED SHIELDING"
- Hazard stripes (alternating cubes on floor): orange/black, small, decorative

**Reactor chamber walls (z=25-35):**
- Left wall: 0.2×8×10, pos (-6, 4, 30), color "1a1a1a"
- Right wall: 0.2×8×10, pos (6, 4, 30), color "1a1a1a"
- Ceiling: 12×0.2×10, pos (0, 8.1, 30), color "111111"
- No floor here — the void is the floor

**Reactor Core (visual only, below void):**
- Core: ResizableCube 4×3×4, pos (0, -8, 30), color "FF6600", emission=3.0
- Glow light: Light at (0, -3, 30), color "FF4400", intensity 2.0, range 20
- Glow light 2: Light at (0, 0, 30), color "FF8800", intensity 1.0, range 15

**Platforms:**
- Platform A: ResizableCube 3×0.3×2, pos (-3.5, 1.5, 26), color "333333"
- Platform B: ResizableCube 4×0.3×2, pos (0, 1.5, 28), color "333333"
- Platform C: ResizableCube 3×0.3×3, pos (3.5, 1.5, 30.5), color "333333"
- Platform D: ResizableCube 2×0.3×3, pos (0, 1.5, 33.5), color "333333"

**JumpPads:**
- JumpPad on Platform A: pos (-3.5, 1.8, 27), force toward Platform B
- JumpPad on Platform D approach: pos (3.5, 1.8, 31.5), force toward Platform D

**Fall Zone (respawn trigger):**
- Trigger (OnCollide), large zone covering void: 12×3×10, pos (0, -2, 30) → `reactor_respawn_trigger`
- Logic: OnCollide → TeleportEvent to Platform A entry (pos: -3.5, 1.8, 25.5)
- Also: OnCollide → Notification red (#FF4400): "Reactor alert — emergency transport activated"

**Particle effects (sparks):**
- Use Light with BlinkLight effect near reactor sides to simulate sparks/flicker

**Data Log 05** (Patel) — on Platform B:
- Visual: pos (0, 1.95, 28), color "FFAA00", emission=2.5 → `log_05_visual`
- Trigger: pos (0, 1.95, 28) → `log_05_trigger`
- Notification: `"[Log 05 — Patel] 'I locked my bunk. I know how that sounds. It's containment protocol. Vasquez didn't order it but I've read enough incident reports to know what containment looks like. We're in it.' — 109 days ago"`

**Data Log 06** (Cho) — in exit corridor:
- Visual: pos (0, 0.4, 36), color "FFAA00", emission=2.5 → `log_06_visual`
- Trigger: pos (0, 0.4, 36) → `log_06_trigger`
- Notification: `"[Log 06 — Cho] 'I'm trying. I'm trying to keep things together. Half the crew won't go south of the med bay. The other half won't say why. Whatever it is — it's in all of us now. We just haven't named it yet.' — 104 days ago"`

**Terminal (exit corridor):**
- Same style as medical terminal, pos (2.5, 0.5, 37) → `terminal_reactor`
- Logic: unlock `door_to_research`

**Door to Research:** thin wall at z=38 → `door_to_reactor` (wait — naming: this door blocks Research Wing) → `door_to_research`

### Returns
```python
return {
    "log_05_trigger": ..., "log_05_visual": ...,
    "log_06_trigger": ..., "log_06_visual": ...,
    "terminal_reactor": ...,
    "door_to_research": ...,
    "reactor_respawn_trigger": ...,
}
```

---

## Task 6: Zone 4 — Research Wing

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/zone_research.py`

**Coordinate range:** x: -4 to +4, z: 38 to 48, y: 0 to 4

This zone is intentionally sparse and cold. The silence after the reactor is unnerving.

### Items to Build

**Structural:** floor/ceiling/walls, same dark palette, no BlinkLight here — cold teal only

**Workstation area (z=41-45):**
- Desk left: ResizableCube 2×0.8×1.0, pos (-2.5, 0.4, 42), color "1e1e30"
- Desk right: ResizableCube 2×0.8×1.0, pos (2.5, 0.4, 42), color "1e1e30"
- Research screen (emissive): 1.5×1.0×0.05, pos (-2.5, 1.5, 42.5), color "0088AA", emission=1.0
- Research screen right: 1.5×1.0×0.05, pos (2.5, 1.5, 42.5), color "0088AA", emission=1.0

**WorldText items:**
- Whiteboard: pos (-3.9, 2.0, 45), facing +X, text: "FIELD RESONANCE — DAY 47\nStability: 23% (+8% overnight)\n??? — check Lab 4 readings 0300"
- Sticky note: pos (2.5, 1.4, 42.6), scale (0.2, 0.2, 0.2), text: "DO NOT ACCESS ARIA LOG 114+"
- Coffee mug (tiny cube): ResizableCube 0.15×0.2×0.15, pos (-2.5, 0.9, 42.3), color "4a3020"

**Teal screen lights:**
- Light at (-2.5, 2.5, 42), color "00AACC", intensity 0.5, range 4
- Light at (2.5, 2.5, 42), color "00AACC", intensity 0.5, range 4

**Data Log 07** (Lindqvist) — on left desk:
- Visual: pos (-2.5, 0.95, 42), color "FFAA00", emission=2.5 → `log_07_visual`
- Trigger: pos (-2.5, 0.95, 42) → `log_07_trigger`
- Notification: `"[Log 07 — Lindqvist] 'Everyone else is gone. I don't know where. ARIA won't tell me. I'm not afraid — I understand now. It wasn't your fault. You tried. I want that on record. Whatever you are now — you tried.' — 14 days ago"`

**Data Log 08** (Vasquez) — on right desk:
- Visual: pos (2.5, 0.95, 42), color "FF4444", emission=3.0 → `log_08_visual` (RED — this one is different)
- Trigger: pos (2.5, 0.95, 42) → `log_08_trigger`
- Notification: `"[Log 08 — Dr. Vasquez] 'If you are reading this — if ARIA let you find this — then she has already decided. The accident in Lab 4 was not your fault. The resonance cascade was mine. You went back in. Twice. Whatever you are now... I don't think you wanted this.' — 14 days ago"`

**Terminal:**
- pos (-3, 0.5, 47) → `terminal_research`
- Logic: unlock `door_to_lab4` (but this is overridden — door only unlocks after ALL 8 logs collected, handled in quests.py — the terminal here just adds a notification "Lab 4 protocols require full crew verification")
- Actually: terminal_research triggers notification only: "Lab 4 access locked — crew verification required (8/8 logs)"

**Door to Lab 4:** thin wall at z=48 → `door_to_lab4` (hidden by quests.py after all logs collected)

### Returns
```python
return {
    "log_07_trigger": ..., "log_07_visual": ...,
    "log_08_trigger": ..., "log_08_visual": ...,
    "terminal_research": ...,
    "door_to_lab4": ...,
}
```

---

## Task 7: Zone 5 — Lab 4 + Escape Pod Bay

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/zone_lab4.py`

**Coordinate range:** x: -4 to +4, z: 48 to 62, y: 0 to 4. Pod bay is x: -5 to +5, z: 58 to 62 (slightly wider).

This zone starts in total darkness (no lights). The escape pod bay has warm gold lighting that turns on when the finale triggers.

### Lab 4 (z=48-58):

**Structural:** same walls/floor/ceiling but add: debris props (tilted small cubes scattered), knocked-over chair

**Debris props:**
- 3-4 small tilted ResizableCubes (0.3-0.8 size) scattered on floor with slight rotation, colors "2a2a3e" and "333333"
- Overturned stool: 0.4×0.8×0.4, pos (-1, 0.4, 52), color "333333", rotated 45° on X

**ARIA terminal (the only screen in this zone):**
- Screen cube: 1.0×0.8×0.05, pos (0, 1.8, 49.1), color "004422", emission=0.5 → `aria_screen`
- WorldText: "ARIA — STATION AI\nSTATUS: ACTIVE\nPERSONNEL: 0", pos (0, 1.85, 49.15), scale (0.15, 0.15, 0.15)
- ARIA NPC: GLBNPC or use trigger as proxy — pos (0, 0, 49), scale (0.8, 0.8, 0.8) → `aria_lab4`
  - Note: If GLBNPC requires a GLB URL, use a trigger zone as proxy with a notification chain instead

### Escape Pod Bay (z=58-62):

**Structural:** slightly wider walls (x: ±5), same ceiling/floor

**Star viewport (the emotional hero moment):**
- Viewport frame: ResizableCube 4×3×0.1, pos (0, 2, 62), color "111122"
- Viewport glass (semi-transparent): ResizableCube 3.5×2.5×0.05, pos (0, 2, 61.95), color "001133", opacity=0.3, emission=0.5
- Star light beyond: Light at (0, 2, 63), color "AACCFF", intensity 0.8, range 10

**Pod Bay lights (start OFF — turned on by finale):**
- Warm light 1: Light, pos (-2, 3, 59), color "FFCC88", intensity 0.0 → `pod_light_1` (starts off)
- Warm light 2: Light, pos (2, 3, 59), color "FFCC88", intensity 0.0 → `pod_light_2`
- Warm light 3: Light, pos (0, 3, 61), color "FFE0AA", intensity 0.0 → `pod_light_3`
- Implementation note: hide lights by default, show them via ShowObjectEvent in finale sequence

**Escape Pod (visual):**
- Pod body: ResizableCube 3×2×4, pos (0, 1, 59), color "334455"
- Pod detail (nose): ResizableCube 1.5×1.5×1.5, pos (0, 1, 57.5), color "334455"
- Pod viewport: 0.8×0.8×0.1, pos (0, 1.6, 57.4), color "001133", opacity=0.4, emission=0.3

**Escape Pod Trigger:**
- Trigger (OnCollide), pos (0, 1, 57), scale (3, 2, 2) → `pod_trigger`
- Default: invisible, collider=false (activated by finale sequence)

### Returns
```python
return {
    "pod_trigger": ...,
    "aria_lab4": ...,
    "pod_light_1": ...,
    "pod_light_2": ...,
    "pod_light_3": ...,
    "door_to_lab4_interior": ...,  # internal door between lab and pod bay if needed
}
```

---

## Task 8: Quest Logic Component

**File:** `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/quests.py`

**Reference:** `docs/reference/quests.md`, `docs/reference/interactions.md`, `docs/workflows/function-effects-reference.md`

This component wires all the cross-zone logic using `all_refs`. It:
1. Defines 8 log quests (one per data log)
2. Defines the escape quest
3. Wires each log trigger to its quest task (advance to collected)
4. Wires log collection to hide the visual cube
5. Wires terminal zones to unlock doors
6. Wires "all 8 logs collected" condition to unlock Lab 4 and trigger ARIA finale
7. Wires pod trigger to finale end sequence

```python
"""
Station Omega — Quest Logic
Wires all cross-zone interactions, quests, and the finale sequence.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'lib'))

from portals_utils import generate_quest_id
from portals_effects import (
    add_task_to_logic, basic_interaction, quest_trigger, quest_effector,
    trigger_on_collide, trigger_on_enter,
    effector_hide, effector_notification, effector_play_sound_once,
    effector_function,  # for FunctionEffector with NCalc conditionals
)


LOG_DATA = [
    ("log_01", "Log 01 — Torres",    "FFAA00"),
    ("log_02", "Log 02 — Nakamura",  "FFAA00"),
    ("log_03", "Log 03 — Osei",      "FFAA00"),
    ("log_04", "Log 04 — Reinholt",  "FFAA00"),
    ("log_05", "Log 05 — Patel",     "FFAA00"),
    ("log_06", "Log 06 — Cho",       "FFAA00"),
    ("log_07", "Log 07 — Lindqvist", "FFAA00"),
    ("log_08", "Log 08 — Vasquez",   "FF4444"),
]

def build_quests(items, logic, next_id, refs):
    quests = {}
    room_tasks = {}

    # --- Per-log quests (8x) ---
    for i, (key, label, color) in enumerate(LOG_DATA, 1):
        quest_id = generate_quest_id()
        quest_name = f"quest_{key}"
        # Quest: 2 states — 0=not collected, 1=collected
        quests[quest_id] = {
            "ID": quest_id,
            "Name": quest_name,
            "Creator": "nzwCTQhZuFeJpUVGShPAJl1kzJP2",
            "IsMultiplayer": False,
            "CurrentState": 0,
            "TotalStates": 1,
        }
        # Wire: trigger zone OnCollide → quest advance to state 1
        trigger_id = refs[f"{key}_trigger"]
        visual_id = refs[f"{key}_visual"]

        add_task_to_logic(logic[trigger_id], quest_trigger(
            quest_id=quest_id,
            quest_name=quest_name,
            task_id=181,  # advance quest
            trigger=trigger_on_collide(),
        ))

        # Wire: when quest hits state 1 → hide visual cube
        add_task_to_logic(logic[visual_id], quest_effector(
            quest_id=quest_id,
            quest_name=quest_name,
            state=1,
            effector=effector_hide(),
        ))

    # --- Terminal → door unlocks ---
    # Medical terminal → hide door_to_medical (Zone 1's blocking wall)
    med_door = refs["door_to_medical"]
    add_task_to_logic(logic[refs["terminal_medical"]], basic_interaction(
        trigger=trigger_on_collide(),
        effector=effector_hide(),
        target_id=med_door,
    ))

    # Reactor terminal → hide door_to_reactor
    add_task_to_logic(logic[refs["terminal_reactor"]], basic_interaction(
        trigger=trigger_on_collide(),
        effector=effector_hide(),
        target_id=refs["door_to_reactor"],
    ))

    # Research terminal → notification only (Lab 4 needs all logs)
    add_task_to_logic(logic[refs["terminal_research"]], basic_interaction(
        trigger=trigger_on_collide(),
        effector=effector_notification("Lab 4 access locked — crew verification required", "00AAFF"),
    ))

    # --- All-logs finale ---
    # When log 08 is collected (quest_log_08 → state 1), check if all 8 are done
    # Use FunctionEffector with NCalc: if all log quest vars = 1, unlock Lab 4
    # Implementation: wire log_08 trigger to a FunctionEffector that hides door_to_lab4
    # and starts ARIA finale sequence
    log_08_trigger = refs["log_08_trigger"]

    # Hide Lab 4 door
    add_task_to_logic(logic[log_08_trigger], basic_interaction(
        trigger=trigger_on_collide(),
        effector=effector_hide(),
        target_id=refs["door_to_lab4"],
    ))

    # ARIA finale notification sequence (timed)
    aria_lines = [
        ("", "FF0000", 0),    # lights cut — use ChangeFog or just notification timing
        ("...", "888888", 1000),
        ("ARIA: 'You found them all.'", "00FFCC", 2500),
        ("ARIA: 'I've been waiting fourteen months for you to wake up.'", "00FFCC", 5000),
        ("ARIA: 'I wanted you to understand before I told you.'", "00FFCC", 8000),
        ("ARIA: 'The cascade in Lab 4 — it was an accident. Dr. Vasquez knew that.'", "00FFCC", 11500),
        ("ARIA: 'You went back in. Twice. For the others.'", "00FFCC", 15000),
        ("ARIA: 'Four of them made it to lifepods because of you.'", "00FFCC", 18500),
        ("ARIA: 'The neural feedback locked you in stasis. I couldn't wake you sooner.'", "00FFCC", 22000),
        ("ARIA: 'I didn't want to tell you all at once. I thought you deserved to find out.'", "00FFCC", 26000),
        ("ARIA: 'The escape pod is ready. It always was.'", "00FFCC", 30000),
        ("The pod bay lights come on.", "FFCC88", 33000),
    ]
    # Wire as a sequence of delayed notifications on the log_08 trigger
    # Use portals_effects timer or delay chain if available
    # Fallback: chain all as immediate notifications (less theatrical but functional)

    # Show pod bay lights (ShowObjectEvent on each light)
    for light_key in ["pod_light_1", "pod_light_2", "pod_light_3"]:
        if light_key in refs:
            add_task_to_logic(logic[log_08_trigger], basic_interaction(
                trigger=trigger_on_collide(),
                effector=effector_show(),
                target_id=refs[light_key],
            ))

    # --- Escape pod finale ---
    pod_id = refs["pod_trigger"]
    add_task_to_logic(logic[pod_id], basic_interaction(
        trigger=trigger_on_collide(),
        effector=effector_notification(
            "The escape pod launches. Stars fill the viewport.\n\nYou remembered.\nYou can rest now.",
            "FFEECC"
        ),
    ))

    return quests, room_tasks
```

**Important:** Read `docs/reference/interactions.md` and `docs/reference/quests.md` carefully. The exact signatures of `quest_trigger`, `quest_effector`, and `basic_interaction` with `target_id` must match what `portals_effects.py` actually exports. Check the file before writing — don't guess. The above is a sketch; use real function signatures.

---

## Task 9: Run generate.py

**Step 1:** Verify all component files exist
```bash
ls games/c0df789f-c9a9-43f1-a88c-214e484a8c71/components/
```
Expected: `__init__.py`, `settings.py`, `zone_crew_quarters.py`, `zone_medical.py`, `zone_reactor.py`, `zone_research.py`, `zone_lab4.py`, `quests.py`

**Step 2:** Run generate.py
```bash
cd "/Users/nathanmccarthy/Local Documents/Portals MCP"
python3 games/c0df789f-c9a9-43f1-a88c-214e484a8c71/generate.py
```
Expected: `Written: .../snapshot.json (NNN items, 9 quests)`

Fix any import errors, KeyErrors, or missing refs before proceeding.

---

## Task 10: Validate

```bash
python3 tools/validate_room.py games/c0df789f-c9a9-43f1-a88c-214e484a8c71/snapshot.json
```

Expected: PASS with 0 errors. Fix any validation failures — common issues:
- Logic values not JSON strings (call `serialize_logic()` first)
- Missing required item fields
- Invalid trigger/effect types (check against `portals_effects.EFFECT_TYPES`)

---

## Task 11: Index + Push

**Step 1:** Index the room
```bash
python3 tools/index_room.py games/c0df789f-c9a9-43f1-a88c-214e484a8c71/snapshot.json
```

**Step 2:** Push via MCP (Claude Code only — use `set_room_data` MCP tool)
- Room ID: `c0df789f-c9a9-43f1-a88c-214e484a8c71`
- File: `games/c0df789f-c9a9-43f1-a88c-214e484a8c71/snapshot.json`

**Step 3:** Return URL to user
```
https://theportal.to/?room=c0df789f-c9a9-43f1-a88c-214e484a8c71
```

---

## Execution Notes

**Parallel opportunity:** Tasks 3-7 (zone components) are fully independent and can run as parallel subagents. Task 8 (quests) must run after all zone components exist (needs their refs).

**Subagent context for each zone:** Pass the relevant task section from this plan + `lib/portals_core.py` + `lib/portals_effects.py` + the Refs Contract section + `docs/reference/items/building.md`.

**Critical check for quests.py subagent:** Must read actual function signatures from `portals_effects.py` before writing. Don't assume — verify.
