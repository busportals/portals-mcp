# Purpose-Driven Quality System

Every item and interaction in a Portals game must justify its existence. This document defines the framework for evaluating quality, the automated build summary that drives review, and the subagent-powered quality loop that catches gaps before the player ever sees the room.

---

## 1. The Five-Purpose Framework

Every item and interaction in a game must serve at least one of these five purposes. If it serves none, it does not belong. If a zone is missing one, the quality review will flag it.

### Orientation

Helps the player know where they are and where to go.

Examples: light trails, landmarks, sightlines between zones, waypoints, signage, colored lighting that distinguishes areas, elevation changes that reveal layout, breadcrumb collectibles along the intended path.

### Reward

Makes the player feel good about an action they just took.

Examples: particle bursts on collection, satisfying sound effects on interaction, camera bloom on achievement, notifications confirming progress, score updates, door-opening animations after solving a puzzle, confetti on quest completion.

### Atmosphere

Makes the space feel alive and real, even when the player is doing nothing.

Examples: ambient particle systems (dust, embers, rain), fog layers, ambient sound loops (wind, machinery, music), decorative clutter (crates, debris, plants), environmental lighting (flickering torches, neon glow, god rays), skybox selection and tinting.

### Story

Tells the player something about the world, its history, or what happened here.

Examples: NPC dialogue, environmental clues (overturned furniture, scorch marks, abandoned equipment), journal entries, quest-driven reveals, locked doors that imply something behind them, before/after zone contrasts, audio logs.

### Spectacle

Creates a moment worth sharing -- something the player would screenshot, clip, or tell a friend about.

Examples: dramatic reveals (a door opens to a massive vista), scale contrast (tiny corridor opens into a cathedral), lighting shifts (sunrise sequence, blackout-to-spotlight), transformation sequences (the environment changes around the player), skybox rotation or swap, boss entrance animations.

### The Rule

- If an item serves **zero** purposes, remove it.
- If a zone is missing **any** purpose, the quality review flags it for enhancement.
- Most items serve one purpose. Great items serve two. Items that serve three or more are keystones of the experience.

---

## 2. Build Summary Format

After `generate.py` assembles all components, it calls `generate_build_summary()` to produce a compact diagnostic. This is what the review subagent reads -- NOT the full `snapshot.json`. The summary keeps review context tight (~200 tokens instead of ~50,000).

### Format

```
BUILD SUMMARY — {Game Name}
═══════════════════════════════════════════
Zones: {zone}({count}), {zone}({count}), ...
Total Items: {n}

By Type:
  cube: {n}  |  glb: {n}  |  light: {n}  |  trigger: {n}
  sound: {n}  |  effect: {n}  |  text: {n}  |  spawn: {n}

Interactions:
  onClick: {n}  |  onCollide: {n}  |  onEnter: {n}  |  onHover: {n}

Audio:
  Ambient loops: {n}  |  One-shot sounds: {n}  |  Music changes: {n}

Quests:
  Total: {n}  |  Visible: {n}  |  Hidden: {n}

Feedback Coverage:
  Actions with sound: {n}/{total}
  Actions with particles: {n}/{total}
  Actions with camera effects: {n}/{total}

Detail Layers:
  {zone}: structural ✓/✗  |  functional ✓/✗  |  atmospheric ✓/✗  |  decorative ✓/✗

Spectacle Moments: {n} identified
═══════════════════════════════════════════
```

### Generation

The function `generate_build_summary()` in `lib/portals_utils.py` produces this output. It is called at the end of `generate.py` after all components have been assembled. The result is written to `games/{room-id}/BUILD_SUMMARY.md`.

The summary is deterministic -- the same snapshot always produces the same summary. This makes pass-over-pass comparison reliable.

---

## 3. The Quality Review Loop

After the initial build (Phase 4 of the modular build workflow), before handing the room to the user, run the quality review loop. This catches density gaps, missing feedback, and absent spectacle before the player ever sees the room.

### Step 1: Generate Build Summary

Run `generate.py`. At the end of the script, call `generate_build_summary()`. This writes `BUILD_SUMMARY.md` to the game folder.

### Step 2: Dispatch Review Subagent

One focused subagent receives:

- The build summary (compact text, ~200 tokens)
- The design doc (`design.md`)
- The quality checklist (Section 5 of this document)

It does **NOT** receive the full `snapshot.json`. This keeps context tight and focused.

The review subagent asks three questions through the five-purpose lens:

1. **"What's thin?"** -- Which zones lack density? Which of the five purposes (Orientation, Reward, Atmosphere, Story, Spectacle) are underserved? A zone with structural and functional items but no atmospheric or decorative items is thin.

2. **"What's missing juice?"** -- Which player actions lack multi-sensory feedback? Are there actions with only one feedback channel (e.g., a door that opens silently, a collectible with no particle burst)? Every core action should have at least two channels.

3. **"What would make someone share this?"** -- Are there at least 2 spectacle moments? Does the first 10 seconds hook the player? Does the ending satisfy (both win and lose paths)? Is there a moment a player would screenshot?

### Step 3: Dispatch Enhancement Subagents

The review subagent produces a numbered enhancement list. Each enhancement specifies:

- **Component**: which file to modify
- **Addition**: what to add (specific items, effects, sounds)
- **Purpose**: which of the five purposes it serves
- **Size**: small / medium / large

Enhancements are grouped by component. Each group is dispatched to a subagent that modifies the existing component file. Independent components are dispatched in parallel.

### Step 4: Regenerate and Check Convergence

Re-run `generate.py`. Call `generate_build_summary()` again. Compare the new build summary to the previous one. Track enhancement counts across passes.

### Step 5: Loop or Stop

**Continue if:** The enhancement count decreased from the previous pass (the build is converging toward quality).

**Stop if any of these are true:**
- Enhancement count is **0** -- the build has converged, all quality metrics are met.
- Enhancement count is **equal to or greater than** the previous pass -- the build is not converging; further passes will not help.
- Pass count has reached **3** -- hard cap to prevent runaway loops.

When stopping due to non-convergence or hard cap, log the remaining enhancements in `changelog.md` as known gaps for the user to review.

---

## 4. Quality Metrics (Termination Conditions)

The review loop is "satisfied" -- and outputs `CONVERGED` -- when **ALL** of these conditions are met:

### Detail Layer Coverage
Every zone has items in all 4 detail layers:
- **Structural** -- walls, floors, platforms, core geometry
- **Functional** -- gameplay items, triggers, interactables, spawn points
- **Atmospheric** -- particles, fog, ambient lights, ambient sound loops
- **Decorative** -- props, clutter, storytelling objects, visual polish

### Feedback Density
Every core player action (as defined in the design doc) has **2 or more** feedback channels:
- Sound effect
- Visual effect (particle, outline, object animation)
- Camera effect (bloom, zoom, filter change)
- Notification or score update

### Spectacle Count
At least **2 spectacle moments** are implemented and identifiable in the build summary.

### Audio Completeness
- Ambient sound loop present in **every** zone
- Sound effect on **every** interactable item
- No zero values in the Audio section of the build summary (for games with multiple zones, "Ambient loops: 0" is a failure)

### No Empty Categories
No category in the build summary reads `0` when the design doc implies it should have content. A puzzle game with "Quests: 0" is a failure. A combat game with "Interactions: onClick: 0" is a failure.

---

## 5. Review Subagent Prompt Template

Dispatch this prompt to a single review subagent after generating the build summary.

```
You are reviewing a game build for quality gaps.

## Build Summary
{paste build summary here}

## Design Document
{paste full design.md here}

## Quality Checklist

Evaluate against the five purposes: Orientation, Reward, Atmosphere, Story, Spectacle.

### 1. Density & Detail Layers
For each zone, check all 4 layers are present:
- Structural (walls, floors, geometry) — present?
- Functional (gameplay items, triggers) — present?
- Atmospheric (particles, fog, ambient lights, ambient sounds) — present?
- Decorative (props, clutter, storytelling objects) — present?

### 2. Feedback & Juice
For each core player action defined in the design:
- Does it have a sound effect?
- Does it have a visual effect (particle, outline, object animation)?
- Does it have a camera effect (bloom, zoom, filter)?
- Does it have a notification or score update?
Count: how many actions have 2+ channels?

### 3. Spectacle & Shareability
- Are there 2+ designed spectacle moments?
- Does the opening hook (first 10 seconds)?
- Does the ending feel satisfying (win and lose paths)?
- Is there a moment a player would screenshot?

### 4. Audio Completeness
- Ambient sound in every zone?
- Sound effects on every interactable?
- Music/atmosphere shift at zone transitions?
- Victory/defeat audio?

## Output Format

Output a numbered enhancement list. Each enhancement:
- Component: {which file to modify}
- Addition: {specific items, effects, or sounds to add}
- Purpose: {Orientation / Reward / Atmosphere / Story / Spectacle}
- Size: {small / medium / large}

If ALL quality metrics are met, output: "CONVERGED — no significant gaps."
```

---

## 6. Enhancement Subagent Prompt Template

Dispatch this prompt to each enhancement subagent. One subagent per component file that needs modification.

```
Generate the modified version of: games/{room-id}/components/{name}.py

**IMPORTANT: Do NOT write any files. Return the complete modified file content as your response.**

## Current File
Read: games/{room-id}/components/{name}.py

## Enhancements to Add
{numbered list from review — only the items for THIS component}

## Technical Reference
Read these docs before making changes:
{list only the specific docs needed for these additions}

## Rules
- Add to the existing build function — do NOT rewrite from scratch
- Each addition must serve its stated purpose
- Use helpers from portals_core.py and portals_effects.py
- Keep the file under 300 lines total after additions
- If additions would exceed 300 lines, split into a sub-component

## Output Format
Return ONLY the complete modified Python file content. The main conversation will write it to disk.
```

### Grouping Rules

- Enhancements are grouped by the `Component` field from the review output.
- If a component has only small enhancements, they can be batched into one subagent call.
- If a component has a large enhancement, it gets its own subagent call with full context for that addition.
- Independent component subagents are dispatched in parallel. Components with dependencies are dispatched sequentially.

---

## 7. Context Management

The quality review loop is designed to add quality without blowing up the main conversation context. Here is why it works.

### Token Budget Per Pass

| Input | Tokens (approx.) |
|-------|-------------------|
| Build summary | ~200 |
| Review subagent total input (summary + design + checklist) | ~3,000 |
| Enhancement subagent input (per component) | ~2,000-3,000 |
| Main context overhead per pass (enhancement list log) | ~500 |

### Token Budget Total

| Passes | Main Context Overhead |
|--------|----------------------|
| 1 pass | ~500 tokens |
| 2 passes | ~1,000 tokens |
| 3 passes (hard cap) | ~1,500 tokens |

### Why This Is Efficient

1. **Each subagent is fresh.** No accumulated state from previous passes. Every subagent starts clean with exactly the context it needs.

2. **Only compact summaries pass between passes.** The build summary (~200 tokens) replaces the full snapshot (~50,000 tokens). The review output is a numbered list (~300-500 tokens), not a prose essay.

3. **Enhancement subagents are surgical.** Each one modifies one component with specific additions. Same context size as the initial build subagents -- the quality loop reuses the existing delegation pattern, not a new one.

4. **Main context only tracks convergence metadata.** Pass number, enhancement count per pass, and whether to continue or stop. The actual review and enhancement work happens entirely in subagents.

### What the Main Context Logs

After each pass, log a single block to the main conversation:

```
Quality Pass {n}: {enhancement_count} enhancements
  Components modified: {list}
  Convergence: {decreasing / stable / diverging}
  Decision: {continue / stop — reason}
```

This is all the main context needs to decide whether to loop again. Everything else lives in subagents.
