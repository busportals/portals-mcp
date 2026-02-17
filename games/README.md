# Games Directory

This folder is where your game projects live. Each game gets its own subfolder named by room ID.

## Structure

When you start a new game, Claude creates a folder like this:

```
games/{room-id}/
  design.md            — approved game design document
  BUILD_MANIFEST.md    — component breakdown with status
  generate.py          — thin compositor script (~40-80 lines)
  components/          — one file per system, written by subagents
  catalog.json         — GLB metadata (dimensions, URLs, categories)
  thumbnails/          — 4-view PNG renders of each GLB
  snapshot.json        — last-known room state (never read into context)
  room_index.md        — compact index of snapshot (read this instead)
  changelog.md         — what changed and when
```

## Getting Started

1. Get your room ID from [Portals](https://theportal.to)
2. Tell Claude: "I want to build a game in room `{your-room-id}`"
3. Claude will create this folder structure automatically
