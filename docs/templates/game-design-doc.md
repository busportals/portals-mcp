# {Game Name}

> {One-line pitch — what is this game in one sentence?}

## The Fantasy

{What does it feel like to play this? What are you? What's the vibe? Write this as if you're describing the experience to a friend, not documenting a system.}

## Story & Narrative

### Premise
{Why does this world exist? Why is the player here, right now? What happened before the game starts? Write this as a story, not a system description. E.g., "You're the last lighthouse keeper on a crumbling island chain. Last night, every light went dark. Ships are crashing on the rocks and a fleet of refugees is approaching. You have until dawn."}

### Stakes
{What's at risk — narratively, not mechanically? What happens if the player fails? Who suffers? What's lost? E.g., "If the lighthouses stay dark, the refugee fleet is lost at sea. The island chain falls silent forever."}

### Conflict
{What force opposes the player? A villain, a curse, a ticking clock, nature, a rival? What's their motivation? E.g., "Someone is deliberately extinguishing the lights. As you relight each lighthouse, the saboteur strikes the next one faster."}

### Characters
{Who does the player meet? What are their roles, motivations, and personalities? Even one well-drawn NPC transforms a space from "game level" to "world." E.g., "Old Maren at the first lighthouse warns you: 'The lights didn't go out on their own. Be careful who you trust.'"}

### Story Arc
{How does the narrative unfold across the game? What does the player believe at the start? What do they discover? Is there a twist, a revelation, a shift in understanding? E.g., "Midway through, you discover the saboteur is the former keeper — your predecessor — who believes the islands must be abandoned to survive."}

### Resolution
{How does the story end when the player wins? When they lose? How does the ending connect back to the stakes and the premise? E.g., "Win: You relight all the lighthouses. The fleet arrives safely. The saboteur is revealed and the islanders must decide his fate. Lose: Dawn breaks with lights still dark. The fleet turns away. The islands go silent."}

## Core Mechanics

### What You Do
{The primary action — jumping, collecting, fighting, solving, exploring. One sentence.}

### The Challenge
{What makes it hard? What's the skill or puzzle?}

### The Reward Loop
{What happens when you succeed at the core action? What keeps you doing it?}

### Fail State
{What happens when you mess up? Is there a penalty? Respawn? Lose progress?}

### Progression
{How does the game change over time? Does it get harder? Do you unlock things?}

## Player Journey

### The First 30 Seconds
{Critical — what does the player see, hear, and do immediately? This must hook them.}

### The Middle
{The main body of gameplay. What are they doing, how does it escalate?}

### The Climax
{The big moment — final challenge, boss, reveal, race to the finish.}

### The Ending
{What happens when you win? What happens when you lose? How is it acknowledged?}

## World & Space

### Visual Direction
{Colors, materials, mood. "Neon cyberpunk alley" or "sun-drenched tropical island" or "dark stone dungeon."}

### Layout
{How big is the play space? Linear path, open world, maze, vertical tower?}

### Lighting
{Bright and cheerful? Dark and moody? Neon? Mixed zones?}

### Key Landmarks
{Notable locations the player will remember — the starting area, the big room, the final arena.}

## Audio Landscape

### Ambient Layers
| Zone | Ambient Sound | Volume | Loop? |
|------|--------------|--------|-------|
| {zone name} | {description or URL} | {0.0-1.0} | yes/no |

### Zone Transitions
| From → To | Audio Change |
|-----------|-------------|
| {zone A} → {zone B} | {what shifts — new ambient starts, music changes, old ambient fades} |

### Action Sounds
| Action | Sound | Spatial? | Falloff |
|--------|-------|----------|---------|
| {player action} | {description or URL} | yes/no | {distance in meters} |

### Progression Sounds
| Event | Sound |
|-------|-------|
| {milestone/achievement} | {fanfare/chime/rumble description} |

### Victory / Defeat
{What does the player hear when they win? When they lose? Include ambient changes, not just stingers.}

## Environment Density

### Detail Layers Per Zone

Every zone needs items at four layers. A zone with only structural and functional items feels like a test level. All four layers make it feel like a place.

| Zone | Structural | Functional | Atmospheric | Decorative |
|------|-----------|-----------|-------------|-----------|
| {zone} | {walls, floors, geometry} | {gameplay items, triggers, collectibles} | {particles, fog, ambient lights, ambient sounds} | {props, clutter, storytelling objects, plants} |

### Hero Moments

2-3 specific moments where the player stops and looks around. These are the screenshots, the moments they share:

1. **{Moment name}**: {What they see. Where it is. Why it's impressive — what combination of scale, lighting, audio, and space creates the wow.}
2. **{Moment name}**: {Same format.}
3. **{Moment name}**: {Optional third moment.}

### Density Targets

| Zone | Density Level | Target Items | Notes |
|------|--------------|-------------|-------|
| {zone} | high / medium / low | ~{number} | {focal point, transition, rest area, etc.} |

## Feedback Design

### Core Action Feedback

Every action the player takes should have multi-sensory feedback. At minimum: sound + one visual effect.

| Action | Sound | Visual | Camera | Notification |
|--------|-------|--------|--------|-------------|
| {action} | {sound URL or desc} | {particle/effect/animation} | {bloom/zoom/filter/none} | {text + hex color, or "—"} |

### Milestone Feedback

Key progression moments get extra feedback — multiple effects with staggered timing.

| Milestone | Feedback Stack |
|-----------|---------------|
| {milestone} | {Sequence: e.g., "sound chime → 0.2s delay → particle burst + bloom +0.3 → 0.5s delay → notification 'Chapter Complete' in gold"} |

### Spectacle Sequences

2-3 moments designed to make players stop and share. Each combines multiple systems.

| Moment | Trigger | Effects (in order) |
|--------|---------|-------------------|
| {moment name} | {what triggers it} | {Step-by-step: e.g., "1. Camera zoom out over 1s, 2. Fog clears revealing vista, 3. Skybox rotation starts, 4. Music shifts to triumphant theme, 5. NPC message: 'Behold...'"} |

## Technical Notes

### Estimated Item Count
{Rough estimate of total items needed.}

### Key Systems Used
{Which Portals systems does this game rely on? Quests, variables, triggers, collectibles, guns, etc.}

### Multiplayer
{Solo, co-op, or competitive? If multiplayer, what's shared vs. per-player?}
