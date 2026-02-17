# Component Template

Reference template for subagents writing component files. Copy the relevant variant into subagent prompts.

## Basic Component (no quests)

```python
"""
{Game Name} — {Component Name}
{One-line description of what this component builds}
"""
from portals_core import cube, text, light, spawn, glb, trigger, jump_pad
from portals_effects import (
    trigger_sub, effector_sub,
    on_enter, on_click, on_collide,
    hide_effect, show_effect, teleport_effect, notification_effect,
    move_to_spot, play_sound_once
)


def build_{name}(items, next_id, **kwargs):
    """
    Build {description}.

    Args:
        items: room items dict to populate
        next_id: callable returning next unique string ID

    Returns:
        dict of named references for downstream components
    """
    refs = {}

    # --- Section 1: {description} ---

    id_ = next_id()
    items[id_] = cube(x=0, y=0.5, z=0, sx=1, sy=1, sz=1)
    refs["example_id"] = id_

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
from portals_core import cube, trigger
from portals_effects import (
    trigger_sub, effector_sub,
    on_enter, on_click,
    hide_effect, show_effect, run_triggers_effect,
    function_effector
)
from portals_utils import create_quest_pair


def build_{name}(items, quests, next_id, **kwargs):
    """
    Build {description}.

    Args:
        items: room items dict to populate
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
    q = create_quest_pair(
        number=start_quest_num, name_suffix="example",
        creator=creator, multiplayer=False
    )
    quests.update(q["entries"])
    refs["quest_num"] = start_quest_num + 1  # next available quest number

    # --- Items with quest-driven logic ---

    # ...

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


def build_{name}(items, next_id, **kwargs):
    """Compose all {name} sub-components."""
    refs = {}
    refs["{sub1}"] = build_{sub1}(items, next_id, **kwargs)
    refs["{sub2}"] = build_{sub2}(items, next_id, **kwargs)
    refs["{sub3}"] = build_{sub3}(items, next_id, **kwargs)
    return refs
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'scripts'))

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
quests = {}

env = build_environment(items, next_id)
game = build_gameplay(items, next_id, **env)
logic = build_logic(items, quests, next_id, creator_uid=CREATOR, **game)

# --- Settings ---
settings = {
    "roomId": ROOM_ID,
    # ... room settings
}

# --- Output ---
room_data = {
    "roomItems": items,
    "settings": settings,
    "roomTasks": {"Tasks": []},
    "quests": quests,
}

script_dir = os.path.dirname(os.path.abspath(__file__))
output = os.path.join(script_dir, "snapshot.json")
with open(output, 'w') as f:
    json.dump(room_data, f, separators=(',', ':'))

print(f"Generated {len(items)} items, {len(quests)} quests")
print(f"Saved to {output}")
```

## Conventions

- **Imports**: Only import what you use from `portals_core` and `portals_effects`
- **No global state**: Components receive everything they need via arguments
- **Refs flow downstream**: Each component returns refs; downstream components receive them via `**kwargs`
- **Quest numbering**: Pass `start_quest_num` in, return next available number in refs
- **ID management**: Never create your own ID counter — always use the `next_id` callable from generate.py
- **Max size**: 200 items or 300 lines per file. Split if larger.
