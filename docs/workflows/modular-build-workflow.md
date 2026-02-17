# Modular Build Workflow

**Always use this workflow.** Every game gets components and a build manifest — not just games with 100+ items. The context window is the bottleneck, not item count. A 50-item game with complex triggers and quests can exhaust context just as easily as a 500-item environment.

## Core Principle: One Subagent Per Component

Each component is written by a **fresh subagent** with a **focused context**. The main conversation handles design and coordination — it never writes component code itself.

## File Structure

```
games/{room-id}/
  design.md              — approved game design document
  BUILD_MANIFEST.md      — component breakdown with status and subagent prompts
  generate.py            — thin compositor (~40-80 lines)
  components/
    __init__.py           — empty
    environment.py        — floor, walls, lighting, spawn
    gameplay.py           — triggers, interactions, core mechanics
    logic.py              — quests, progression, scoring
    audio.py              — sound emitters, ambient audio
    ...                   — as many as the game needs
  snapshot.json           — generated output
```

## Standard Component Interface

Every component follows the same function signature:

```python
def build_<name>(items: dict, next_id, **kwargs):
    """
    Mutates `items` dict in place. Returns a dict of named references
    to important items/IDs created (for use by downstream components).

    Args:
        items: room items dict — add items with items[next_id()] = {...}
        next_id: callable returning the next unique string ID
        **kwargs: dependencies from other components (refs, quest numbers, etc.)

    Returns:
        dict with named references, e.g.:
        {"spawn_id": "5", "quest_num": 3, "controller_id": "12"}
    """
```

Components that also create quests take a `quests` dict parameter:

```python
def build_<name>(items: dict, quests: dict, next_id, **kwargs):
```

## Build Manifest Format

The manifest is the coordination document. It defines every component, what it needs, and how to prompt the subagent that writes it.

```markdown
# BUILD_MANIFEST.md

## Room Info
- Room ID: {room-id}
- Creator UID: {uid}
- Design: design.md

## Components

### 1. environment.py [pending]
**Scope**: Floor grid, walls, ceiling, lighting, spawn point, ambient sound
**Depends on**: nothing
**Produces**: spawn_id
**Docs needed**: items/building.md, systems/settings.md
**Placement strategy**: modular grid (floors/walls), organic scatter (vegetation), furniture arrangement (spawn area)
**Design section**: "World & Space" from design.md

### 2. gameplay.py [pending]
**Scope**: Core mechanic items — platforms, obstacles, collectibles
**Depends on**: environment (spawn_id)
**Produces**: collectible_ids[], zone_refs{}
**Docs needed**: items/gameplay.md, items/models.md
**Placement strategy**: varies by item type — see scene-design.md
**Design section**: "Core Mechanics" from design.md

### 3. logic.py [pending]
**Scope**: Quest progression, scoring, win/loss conditions
**Depends on**: gameplay (collectible_ids, zone_refs)
**Produces**: quest entries, controller_id
**Docs needed**: systems/quests.md, systems/interactions.md
**Design section**: "Player Journey" from design.md
```

## Subagent Delegation

### How It Works

The main conversation:
1. Completes the design phase, writes `design.md`
2. Creates `BUILD_MANIFEST.md` with component breakdown
3. Writes the thin `generate.py` compositor
4. Dispatches one subagent per component (independent ones in parallel)
5. After all components are written, runs `generate.py`, pushes to room

### Why Subagents Don't Write Files

Subagents cannot reliably use Write/Edit tools due to permission constraints. Instead, each subagent **generates the component code and returns it as its response**. The main conversation then writes the file. This is more reliable and keeps all file I/O in the main context where permissions work.

### What Each Subagent Receives

Each subagent gets a **focused prompt** containing only:

1. **The component's job** — scope, inputs, outputs from the manifest
2. **The relevant design section** — not the entire design doc
3. **The specific technical docs** — only the doc files listed in the manifest
4. **Catalog data** — only if the component places GLB models
5. **The standard interface** — function signature, import pattern

### Subagent Prompt Template

```
Generate the Python code for: games/{room-id}/components/{name}.py

**IMPORTANT: Do NOT write any files. Return the complete file content as your response.**

## Component Spec
{paste the manifest entry for this component}

## Design Context
{paste only the relevant section from design.md}

## Technical Reference
Read these docs before writing:
- docs/{specific-doc-1}.md
- docs/{specific-doc-2}.md

## Catalog (if GLB)
Read: games/{room-id}/catalog.json

## Standard Interface
- Function: build_{name}(items, next_id, **kwargs) -> dict
- Import pattern: sys.path is set by generate.py, use `from portals_core import ...`
- Return named refs dict for downstream components

## Scene Design
Read the relevant placement strategy section from docs/workflows/scene-design.md:
- Modular items → "Modular Kit Pieces" section (precise grid, no gaps)
- Organic items → "Organic / Natural Items" section (scatter, overlap, rotation variety)
- Connectable items → "Connectable / Seamless Items" section (overlap at joints)
- Furniture → "Furniture & Functional Items" section (avatar-scaled, functional positioning)
- Decorative → "Decorative / Accent Items" section (surface-mounted, eye-level)

## Rules
- Keep under 200 lines
- If this component needs 200+ items, split into sub-components (see Deep Delegation below)
- Use helpers from portals_core.py and portals_effects.py — don't reinvent
- Return refs dict with all IDs that downstream components need

## Output Format
Return ONLY the complete Python file content. The main conversation will write it to disk.
```

## Deep Delegation: Splitting Large Components

When a single component would produce **200+ items** (cities, large environments, complex logic systems), split it further using sub-components.

### When to Split

| Scenario | Strategy |
|----------|----------|
| City with districts | One sub-component per district |
| Large floor/terrain | Grid sectors (NW, NE, SW, SE) |
| Many building types | One sub-component per building type |
| Complex logic system | One sub-component per mechanic |
| Many NPC interactions | One sub-component per NPC or NPC group |
| Multi-stage progression | One sub-component per stage |

### Sub-Component File Structure

```
components/
  environment/
    __init__.py          — exports build_environment() that composes sub-components
    floor.py             — floor grid tiles
    buildings_north.py   — buildings in north district
    buildings_south.py   — buildings in south district
    lighting.py          — all lights and ambient
    decorations.py       — props, vegetation, details
```

### Sub-Component Compositor Pattern

The parent component becomes a thin compositor itself:

```python
# components/environment/__init__.py
from .floor import build_floor
from .buildings_north import build_buildings_north
from .buildings_south import build_buildings_south
from .lighting import build_lighting
from .decorations import build_decorations

def build_environment(items, next_id, **kwargs):
    refs = {}
    refs["floor"] = build_floor(items, next_id)
    refs["north"] = build_buildings_north(items, next_id)
    refs["south"] = build_buildings_south(items, next_id)
    refs["lighting"] = build_lighting(items, next_id)
    refs["decorations"] = build_decorations(items, next_id)
    return refs
```

### Sub-Component Manifest

Add nested entries to the manifest:

```markdown
### 1. environment/ [pending]
**Scope**: Entire city environment (~800 items)
**Strategy**: Deep delegation — 5 sub-components

#### 1a. environment/floor.py [pending]
**Scope**: 10x10 floor tile grid (100 tiles)
**Items**: ~100
**Docs needed**: systems/glb-asset-catalog.md

#### 1b. environment/buildings_north.py [pending]
**Scope**: North district — 8 buildings with interiors
**Items**: ~200
**Docs needed**: items/building.md, items/models.md
```

Each sub-component gets its own subagent with its own focused prompt.

### Recursive Depth

In extreme cases (2000+ item worlds), sub-components can split further:

```
components/
  environment/
    district_north/
      __init__.py        — composes buildings in north district
      residential.py     — houses
      commercial.py      — shops
      park.py           — green space
```

**Rule of thumb**: No single file should produce more than 200 items or exceed 300 lines. If it would, split it.

## Workflow Step by Step

### Phase 1: Design (Main Context)
1. Design conversation with user
2. Write `design.md`, get approval

### Phase 2: Plan (Main Context)
1. Analyze the design — estimate item counts per system
2. Decide component breakdown (flat or deep based on scale)
3. Write `BUILD_MANIFEST.md`
4. Write `generate.py` (thin compositor)
5. Write `components/__init__.py`

### Phase 3: Build (Subagents → Main Writes)
1. Identify independent components (no cross-dependencies)
2. Dispatch those subagents in parallel using `dispatching-parallel-agents`
   - Each subagent **returns** the component code as its response (does NOT write files)
3. **Main conversation writes each file** using the returned content
4. When independent components are written, dispatch dependent components (passing refs from completed ones)
5. Continue until all components are written

### Phase 4: Assemble (Main Context)
1. Run `generate.py` to produce `snapshot.json`
2. Validate output (item count, quest count, no errors)
3. Generate build summary by calling `generate_build_summary()` — saves to `BUILD_SUMMARY.md`
4. Proceed to Quality Review Loop

### Phase 5: Quality Review Loop (Main Context + Subagents)

Before pushing to the user, run at least one quality review pass. See `docs/workflows/quality-passes.md` for the full protocol.

1. **Review**: Dispatch a review subagent with the build summary + design doc + quality checklist
   - The subagent receives the compact build summary (~200 tokens), NOT the full snapshot
   - It evaluates through the five-purpose lens: Orientation, Reward, Atmosphere, Story, Spectacle
   - It outputs a numbered enhancement list with purpose tags and size estimates
2. **Enhance**: Group enhancements by component, dispatch enhancement subagents
   - Each subagent modifies one existing component file with specific additions
   - Same dispatch pattern as Phase 3 (parallel for independent components)
3. **Regenerate**: Re-run `generate.py`, generate new build summary
4. **Converge**: Compare enhancement count to previous pass
   - If decreased → loop (quality is improving)
   - If zero → converged (all metrics met)
   - If equal/increased → stop (not converging)
   - If pass count = 3 → stop (hard cap)

**Convergence log** (tracked in main context):
```
Pass 1: 12 enhancements (8 small, 3 medium, 1 large)
Pass 2: 4 enhancements (3 small, 1 medium)
Pass 3: 0 enhancements — CONVERGED
```

**Quality metrics** (loop is "satisfied" when all are met):
- Every zone has all 4 detail layers (structural, functional, atmospheric, decorative)
- Every core player action has 2+ feedback channels
- At least 2 spectacle moments implemented
- Audio coverage: ambient in every zone, sound on every interactable
- No zero categories in build summary

### Phase 6: Push (Main Context)
1. Push final `snapshot.json` to room via MCP
2. Share room URL with user: `https://theportal.to/room/{room-id}`

### Phase 7: Iterate (Main Context or Subagent)
1. User playtests, gives feedback
2. Identify which component needs changes
3. Dispatch a subagent to update just that component
4. Re-run `generate.py`, push, verify

## Key Principles

- **generate.py stays thin** — imports and composes, never builds items directly
- **Components are independent** — each can be regenerated without touching others
- **Subagents get minimal context** — only the docs and design sections they need
- **Parallel when possible** — independent components build simultaneously
- **Each push is testable** — after each phase, the room should be loadable
- **Never hand-write JSON** — always use `portals_core.py` and `portals_effects.py` helpers
- **Review before shipping** — never push a first build without at least one quality pass through the five-purpose lens
