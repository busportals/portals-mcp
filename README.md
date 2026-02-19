# Portals Game Designer

Build interactive 3D games inside [Portals](https://theportal.to) rooms using AI. You describe what you want — your AI handles everything from game design to technical execution.

> **This repo is the knowledge base for building with the Portals MCP.** The MCP server (`portals-mcp`) gives your AI the ability to talk to the Portals API, but it doesn't know *how* to design games, place 3D models correctly, set up interactions, or structure room data. That knowledge lives here — in the documentation, tools, libraries, and instructions in this repository. Without it, your AI will produce broken or low-quality results.

## What Is This?

This is a toolkit that connects any AI coding assistant to [Portals](https://theportal.to) (a platform for creating 3D virtual spaces). Together, they let you design and build complete games just by having a conversation.

You say things like "build me a treasure hunt game" or "make an escape room." Your AI acts as your game designer — it asks you about story, mechanics, and feel, writes a design document for your approval, then builds the entire game and pushes it live to your Portals room.

No coding required on your end.

### Compatible Tools

This repo works with any AI tool that supports MCP (Model Context Protocol):

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
- [Cursor](https://www.cursor.com/)
- [Windsurf](https://windsurf.com/)
- [Cline](https://github.com/cline/cline)
- [Codex](https://openai.com/index/codex/)
- Any other MCP-compatible AI assistant

## How It Works

There are three pieces working together:

### 1. Portals (the platform)
[Portals](https://theportal.to) is a 3D virtual space platform. You can create rooms, fill them with objects, add game mechanics (triggers, effects, quests), and share them with anyone via a link. Rooms are accessed in-browser — no downloads needed.

### 2. Your AI Tool (the builder)
Your AI coding assistant reads the instructions and documentation in this repo to understand how Portals works — what item types exist, how triggers and effects work, how quests are structured, and so on.

### 3. This Repository (the knowledge base)
This repo is the bridge between them. It contains:

- **Instructions** (`CLAUDE.md`) — tells the AI how to act as a game designer, what steps to follow, and what rules to obey
- **Documentation** (`docs/`) — detailed reference material for every Portals system (item types, triggers, effects, quests, settings, etc.)
- **Tools** (`tools/`) — Python utilities for tasks like extracting 3D model dimensions, validating room data, and indexing room contents
- **Libraries** (`lib/`) — Python code the AI uses to generate room data programmatically
- **MCP connection** (`.mcp.json`) — the configuration that connects your AI to the Portals API

### How the repo stays current

This repository is maintained by the Portals team. When new features, item types, effects, or systems are added to the platform, the documentation and tools here get updated to match. That way, your AI always has accurate, up-to-date knowledge of what Portals can do.

If something isn't working as expected, it might mean the docs need updating — feel free to open an issue.

## Setup

### The Quick Way

**If your AI tool can read project files, just open this repo and tell it to get started.** It will read the instructions in `CLAUDE.md`, understand the project structure, and walk you through anything that still needs to be set up (like the MCP server or Python dependencies). This is the fastest path for most people.

If that doesn't work or you prefer to set things up manually, follow the steps below.

### Prerequisites

You'll need these installed on your computer:

- **Node.js** (v18 or later) — needed to run the MCP server that connects your AI to Portals. Download from [nodejs.org](https://nodejs.org/).
- **Python 3.9+** — needed for the local tools that process 3D models, validate data, etc. Most Macs have this already. Check with `python3 --version`.
- **An AI coding tool** — any MCP-compatible tool from the list above.
- **A Portals account** — sign up at [theportal.to](https://theportal.to) if you don't have one.

### Step 1: Clone the repo

```bash
git clone https://github.com/busportals/portals-mcp.git
cd portals-mcp
```

### Step 2: Install the Portals MCP server

```bash
npx portals-mcp@latest
```

This installs the MCP server that lets your AI communicate with the Portals API.

### Step 3: Configure MCP in your tool

The MCP server needs to be registered with your AI tool. The config is the same across tools — just the file location differs:

**Claude Code** — already configured via `.mcp.json` in this repo. No extra step needed.

**Cursor** — add to `.cursor/mcp.json` in the project root (create the file if it doesn't exist):
```json
{
  "mcpServers": {
    "portals": {
      "command": "npx",
      "args": ["portals-mcp"]
    }
  }
}
```

**Windsurf** — add to your Windsurf MCP config (`~/.codeium/windsurf/mcp_config.json`):
```json
{
  "mcpServers": {
    "portals": {
      "command": "npx",
      "args": ["portals-mcp"]
    }
  }
}
```

**Cline / Other tools** — add the same server config to your tool's MCP settings. The server definition is always:
```json
{
  "command": "npx",
  "args": ["portals-mcp"]
}
```

### Step 4: Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs libraries used by the local tools (for 3D model processing, thumbnail generation, etc.).

### Step 5: Open the repo in your AI tool

Launch your AI tool from inside the project folder (or open the folder in your IDE). The AI will automatically:
- Load the game designer instructions from `CLAUDE.md`
- Connect to the Portals API via the MCP server
- Be ready to design and build games

On first use, the AI will authenticate with Portals by opening a browser window where you can log in. After that, you're ready to go.

## Using It

### Starting a new game

Just tell your AI what you want:

- "I want to build a game"
- "Make me an escape room"
- "I have a room, here's the ID: abc-123-def"

The AI will ask whether you want to design every detail together or have it surprise you with the best game it can think of. Either way, it follows a structured process:

1. **Design** — asks about your vision (story, mechanics, feel), then writes a design document for your approval
2. **Build** — once you approve the design, generates all the room data (items, interactions, quests, lighting, audio) and pushes it to your room
3. **Playtest** — you visit your room at `https://theportal.to/?room=<your-room-id>` and try it out
4. **Iterate** — tell the AI what to change ("the jumps are too hard", "add more enemies", "make the ending more dramatic") and it updates the room

### Working with an existing room

If you already have a Portals room with content, the AI can work with it. Give it your room ID and it will pull the current room data, index it, and understand what's already there before making changes.

### What the AI can do

- Design complete games from scratch (story, mechanics, progression, audio, visuals)
- Place and arrange 3D models with correct dimensions and spacing
- Set up triggers and effects (click a button to open a door, step on a platform to teleport, etc.)
- Create quest systems with progression and state tracking
- Configure room settings (lighting, fog, movement physics, avatars)
- Upload and manage 3D models (GLB files) and images
- Create new rooms from templates or duplicate existing ones
- Validate everything before pushing to make sure nothing is broken

## Project Structure

```
CLAUDE.md                — Instructions for the AI (loaded automatically)
.mcp.json                — MCP server config (connects AI to Portals API)
requirements.txt         — Python dependencies

docs/                    — Reference documentation
  INDEX.md               — Master index of all item types, triggers, effects
  reference/             — System docs (interactions, quests, settings, etc.)
  reference/items/       — Item type docs by category (building, models, gameplay, etc.)
  workflows/             — Step-by-step workflow guides
  templates/             — Design doc template and example room data

tools/                   — Python CLI tools
  validate_room.py       — Validate room data before pushing
  index_room.py          — Generate compact room index from snapshot
  query_room.py          — Look up specific items in a room
  merge_room.py          — Patch changes into existing room data
  extract_glb_metadata.py — Extract dimensions/thumbnails from 3D models
  check_room_storage.py  — Check room asset storage size
  classify_modular_edges.py — Classify edges of modular kit pieces
  blender_to_portals.py  — Import Blender scenes (run inside Blender)
  manifest_to_room_data.py — Convert Blender manifests to room data
  parse_cdn_upload.py    — Parse CDN upload results
  merge_modular_proposal.py — Merge modular kit proposals into catalog

lib/                     — Python libraries for room data generation
  portals_core.py        — Item generators (cubes, text, lights, triggers, etc.)
  portals_effects.py     — Trigger and effect builders (63 effects, 21 triggers)
  portals_utils.py       — Quest helpers, math, validation, data formatting
  modular_helpers.py     — Modular kit placement helpers
  board_helpers.py       — Game logic visualization (circuit-board flowcharts)

games/                   — Your game projects (one folder per room)
```

When you build a game, the AI creates a folder under `games/` with your room ID containing the design document, build scripts, 3D model catalog, and generated room data.

## What's in the Documentation

The `docs/` folder contains everything the AI needs to know about Portals. You generally don't need to read these yourself (the AI reads them on demand), but here's what's there:

- **26+ item types** — cubes, 3D models, lights, NPCs, triggers, collectibles, images, videos, particle effects, and more
- **21 trigger types** — click, enter zone, exit zone, collide, hover, key press, take damage, and more
- **63+ effect types** — show/hide, move, teleport, play sound, spawn particles, change avatar, lock camera, deal damage, update score, and more
- **Quest system** — multi-state quests with progression, persistence, and per-player tracking
- **Settings** — room-level configuration for lighting, fog, movement physics, avatars, UI toggles
- **Workflow guides** — step-by-step processes for design, building, quality review, scene layout, and more

## Troubleshooting

**"The AI doesn't seem to know about Portals"**
Make sure you've opened this project folder in your AI tool. The AI needs to read `CLAUDE.md` from this directory.

**"MCP connection failed" or "authenticate failed"**
Check that Node.js is installed (`node --version`), verify your MCP config is set up for your tool (see Step 3), and try authenticating again — the AI will open a browser window for you to log in.

**"Permission denied" when pushing room data**
You need write permissions for the room you're targeting. Check that you own the room or have admin access.

**"Module not found" errors from Python tools**
Run `pip install -r requirements.txt` to install dependencies.

## License

MIT — see [LICENSE](LICENSE)
