# Component Template

Reference template for subagents writing component files. Copy the relevant variant into subagent prompts.

## Basic Component (no quests)

```python
"""
{Game Name} — {Component Name}
{One-line description of what this component builds}
"""
from portals_core import create_cube, create_text, create_light, create_spawn, create_glb, create_trigger, create_jump_pad
from portals_effects import (
    basic_interaction, add_task_to_logic,
    trigger_on_click, trigger_on_enter, trigger_on_collide,
    effector_hide, effector_show, effector_teleport, effector_notification,
    effector_move_to_spot, effector_play_sound_once
)


def build_{name}(items, logic, next_id, **kwargs):
    """
    Build {description}.

    Args:
        items: room items dict to populate (spatial/visual only)
        logic: room logic dict to populate (interactions, type config)
        next_id: callable returning next unique string ID

    Returns:
        dict of named references for downstream components
    """
    refs = {}

    # --- Section 1: {description} ---

    id_ = next_id()
    items[id_], logic[id_] = create_cube(pos=(0, 0.5, 0))
    refs["example_id"] = id_

    # Add an interaction to the cube
    add_task_to_logic(logic[id_], basic_interaction(
        trigger=trigger_on_click(),
        effector=effector_notification("Hello!", "00FF00")
    ))

    # --- Section 2: {description} ---

    # ...

    return refs
```

## Component with Quests

```python
"""
{Game Name} — {Component Name}
{One-line description}
"""
from portals_core import create_cube, create_trigger
from portals_effects import (
    Quest, basic_interaction, add_task_to_logic,
    trigger_on_enter, trigger_on_click,
    effector_hide, effector_show, effector_notification,
    effector_play_sound_once, effector_run_triggers
)


def build_{name}(items, logic, quests, next_id, **kwargs):
    """
    Build {description}.

    Args:
        items: room items dict to populate (spatial/visual only)
        logic: room logic dict to populate (interactions, type config)
        quests: room quests dict to populate
        next_id: callable returning next unique string ID
        **kwargs: upstream refs (e.g., controller_id, zone_refs)

    Returns:
        dict of named references including quest_num for downstream
    """
    creator = kwargs.get("creator_uid", "YOUR_FIREBASE_UID")
    start_quest_num = kwargs.get("start_quest_num", 0)
    refs = {}

    # --- Quest setup ---
    q = Quest(start_quest_num, "example", creator)
    quests.update(q.entries)
    refs["quest_num"] = start_quest_num + 1  # next available quest number

    # --- Items with quest-driven logic ---

    id_ = next_id()
    items[id_], logic[id_] = create_cube(pos=(0, 0.5, 0))

    # Single quest-driven effect: hide cube when quest completes
    q.effector(logic[id_], 2, effector_hide())

    # Multiple effects on the same quest state:
    # q.on_state(logic[id_], 2, [
    #     effector_hide(),
    #     effector_notification("Done!", "00FF00"),
    #     effector_play_sound_once("https://example.com/win.mp3"),
    # ])

    # Trigger that advances quest on click:
    # q.trigger(logic[btn_id], 181, trigger_on_click())

    # ...

    return refs
```

## Scene-Only Component

Use when a component only places items with no interactions. Ideal for environment art, decorations, structural geometry, and GLB model layouts.

```python
"""
{Game Name} — {Component Name} (scene)
{One-line description — no interactions, spatial layout only}
"""
from portals_core import create_cube, create_glb, create_light, create_text
from portals_utils import yrot


def build_{name}_scene(items, logic, next_id, catalog, **kwargs):
    """
    Scene component: places items, no interactions.

    Only positions, rotations, scales, and models. No triggers or effects.
    Logic entries are still populated (for color, shadow settings, etc.)
    but no Tasks are added.

    Args:
        items: room items dict to populate
        logic: room logic dict to populate
        next_id: callable returning next unique string ID
        catalog: dict from catalog.json with GLB metadata (dimensions, URLs)

    Returns:
        dict of named references (item IDs) for logic components to wire up
    """
    refs = {}

    # --- Structural geometry ---

    id_ = next_id()
    items[id_], logic[id_] = create_cube(
        pos=(0, 0, 0), scale=(20, 0.1, 20), color="444444"
    )
    refs["floor_id"] = id_

    # --- GLB placement using catalog dimensions ---

    entry = catalog["barrel"]
    id_ = next_id()
    items[id_], logic[id_] = create_glb(
        pos=(3, 0, 5),
        glb_url=entry["url"],
        rot=yrot(90)
    )
    refs["barrel_id"] = id_

    # --- Lighting ---

    id_ = next_id()
    items[id_], logic[id_] = create_light(pos=(0, 4, 0), brightness=3.0)
    refs["main_light_id"] = id_

    return refs
```

## Logic-Only Component

Use when a component only wires interactions and quests onto items that already exist. Ideal for adding game mechanics to a scene built by a scene-only component, or for complex multi-quest logic systems.

```python
"""
{Game Name} — {Component Name} (logic)
{One-line description — wires interactions on existing items}
"""
from portals_effects import (
    Quest, basic_interaction, add_task_to_logic,
    trigger_on_click, trigger_on_enter,
    effector_hide, effector_show, effector_notification,
    effector_play_sound_once, effector_run_triggers
)


def build_{name}_logic(logic, quests, item_refs, **kwargs):
    """
    Logic component: wires interactions on existing items.

    Only adds Tasks to logic entries and creates quests.
    Does not create any new items.

    Args:
        logic: room logic dict (must already contain entries from scene components)
        quests: room quests dict to populate
        item_refs: dict of named item IDs from scene components
        **kwargs: upstream refs (e.g., creator_uid, start_quest_num)

    Returns:
        dict of named references including quest_num for downstream
    """
    creator = kwargs.get("creator_uid", "YOUR_FIREBASE_UID")
    start_quest_num = kwargs.get("start_quest_num", 0)
    refs = {}

    # --- Quest setup ---
    q = Quest(start_quest_num, "activate", creator)
    quests.update(q.entries)
    refs["quest_num"] = start_quest_num + 1

    # --- Wire interactions onto existing items ---

    barrel_id = item_refs["barrel_id"]
    add_task_to_logic(logic[barrel_id], basic_interaction(
        trigger=trigger_on_click(),
        effector=effector_notification("You found a barrel!", "FFD700")
    ))

    floor_id = item_refs["floor_id"]
    add_task_to_logic(logic[floor_id], basic_interaction(
        trigger=trigger_on_enter(),
        effector=effector_play_sound_once("https://example.com/step.mp3")
    ))

    return refs
```

## Sub-Component Compositor

When a component is split into sub-components via deep delegation:

```python
# components/{name}/__init__.py
"""
{Game Name} — {Component Name} (compositor)
Composes sub-components into the full {name} system.
"""
from .{sub1} import build_{sub1}
from .{sub2} import build_{sub2}
from .{sub3} import build_{sub3}


def build_{name}(items, logic, next_id, **kwargs):
    """Compose all {name} sub-components."""
    refs = {}
    refs["{sub1}"] = build_{sub1}(items, logic, next_id, **kwargs)
    refs["{sub2}"] = build_{sub2}(items, logic, next_id, **kwargs)
    refs["{sub3}"] = build_{sub3}(items, logic, next_id, **kwargs)
    return refs
```

For scene/logic split compositors:

```python
# components/{name}/__init__.py
"""
{Game Name} — {Component Name} (scene+logic compositor)
Composes scene layout and logic wiring into the full {name} system.
"""
from .scene import build_{name}_scene
from .logic import build_{name}_logic


def build_{name}(items, logic, quests, next_id, catalog, **kwargs):
    """Compose scene placement and logic wiring."""
    # Scene first: place all items
    scene_refs = build_{name}_scene(items, logic, next_id, catalog, **kwargs)

    # Logic second: wire interactions onto placed items
    logic_refs = build_{name}_logic(logic, quests, scene_refs, **kwargs)

    return {**scene_refs, **logic_refs}
```

## Generate.py Compositor

The top-level script that imports all components:

```python
#!/usr/bin/env python3
"""
{Game Name} — Room Generator
Room: {room-id}

Thin compositor: imports components and assembles the room.
See BUILD_MANIFEST.md for build status.
"""
import sys
import os
import json

# Set up imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from components.environment import build_environment
from components.gameplay import build_gameplay
from components.logic import build_logic

ROOM_ID = "{room-id}"
CREATOR = "{creator-uid}"

# --- ID Management ---
_next = 1
def next_id():
    global _next
    _next += 1
    return str(_next)

# --- Build ---
items = {}
logic = {}
quests = {}

env = build_environment(items, logic, next_id)
game = build_gameplay(items, logic, next_id, **env)
lgc = build_logic(items, logic, quests, next_id, creator_uid=CREATOR, **game)

# --- Settings ---
settings = {
    "roomId": ROOM_ID,
    # ... room settings
}

# --- Output ---
from portals_utils import serialize_logic

room_data = {
    "roomItems": items,
    "settings": settings,
    "roomTasks": {"Tasks": list(quests.keys())},
    "quests": quests,
    "logic": logic,
}
serialize_logic(room_data)

script_dir = os.path.dirname(os.path.abspath(__file__))
output = os.path.join(script_dir, "snapshot.json")
with open(output, 'w') as f:
    json.dump(room_data, f, indent=2)

print(f"Generated {len(items)} items, {len(quests)} quests")
print(f"Saved to {output}")
```

## Conventions

- **Imports**: Only import what you use from `portals_core` and `portals_effects`
- **No global state**: Components receive everything they need via arguments
- **Refs flow downstream**: Each component returns refs; downstream components receive them via `**kwargs`
- **Quest numbering**: Pass `start_quest_num` in, return next available number in refs
- **ID management**: Never create your own ID counter -- always use the `next_id` callable from generate.py
- **Max size**: 200 items or 300 lines per file. Split if larger.
- **Item/logic separation**: `portals_core` creators return `(item, logic)` tuples. Always unpack into both dicts: `items[id_], logic[id_] = create_*(...)`. The `items` dict holds spatial/visual data; the `logic` dict holds behavioral data (interactions, type config, color, etc.)
- **Adding interactions**: Use `add_task_to_logic(logic[id_], task)` from `portals_effects`. Never modify `items` to add interactions.
- **Scene/logic split**: When a component has complex layout AND complex logic, split into `build_{name}_scene()` and `build_{name}_logic()`. Scene runs first (creates items), logic runs second (wires interactions using item refs). This enables parallel subagent work.
