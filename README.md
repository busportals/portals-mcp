# Portals Game Designer

Build interactive 3D games inside [Portals](https://theportal.to) rooms using AI. You describe what you want — Claude handles everything from game design to technical execution.

> **This repo is required for building with the Portals MCP.** The MCP server (`portals-mcp`) gives Claude the ability to talk to the Portals API, but it doesn't know *how* to design games, place 3D models correctly, set up interactions, or structure room data. That knowledge lives here — in the documentation, tools, libraries, and instructions in this repository. Without it, Claude will produce broken or low-quality results. **Always run Claude Code from inside this repo.**

## What Is This?

This is a toolkit that connects [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (an AI coding assistant) to [Portals](https://theportal.to) (a platform for creating 3D virtual spaces). Together, they let you design and build complete games just by having a conversation.

You say things like "build me a treasure hunt game" or "make an escape room." Claude acts as your game designer — it asks you about story, mechanics, and feel, writes a design document for your approval, then builds the entire game and pushes it live to your Portals room.

No coding required on your end.

## How It Works

There are three pieces working together:

### 1. Portals (the platform)
[Portals](https://theportal.to) is a 3D virtual space platform. You can create rooms, fill them with objects, add game mechanics (triggers, effects, quests), and share them with anyone via a link. Rooms are accessed in-browser — no downloads needed.

### 2. Claude Code (the AI)
[Claude Code](https://docs.anthropic.com/en/docs/claude-code) is Anthropic's AI coding assistant that runs in your terminal. When launched from this project folder, it reads the instructions and documentation here to understand how Portals works — what item types exist, how triggers and effects work, how quests are structured, and so on.

### 3. This Repository (the knowledge base)
This repo is the bridge between them. It contains:

- **Instructions** (`CLAUDE.md`) — tells Claude how to act as a game designer, what steps to follow, and what rules to obey
- **Documentation** (`docs/`) — detailed reference material for every Portals system (item types, triggers, effects, quests, settings, etc.)
- **Tools** (`tools/`) — Python utilities for tasks like extracting 3D model dimensions, validating room data, and indexing room contents
- **Libraries** (`lib/`) — Python code that Claude uses to generate room data programmatically
- **MCP connection** (`.mcp.json`) — the configuration that lets Claude talk directly to the Portals API to read and write room data

### How the repo stays current

This repository is maintained by the Portals team. When new features, item types, effects, or systems are added to the platform, the documentation and tools here get updated to match. That way, Claude always has accurate, up-to-date knowledge of what Portals can do.

If something isn't working as expected, it might mean the docs need updating — feel free to open an issue.

## Setup

### Prerequisites

You'll need these installed on your computer:

- **Node.js** (v18 or later) — needed to run the MCP server that connects Claude to Portals. Download from [nodejs.org](https://nodejs.org/).
- **Python 3.9+** — needed for the local tools that process 3D models, validate data, etc. Most Macs have this already. Check with `python3 --version`.
- **Claude Code** — Anthropic's CLI tool. Install it by following the [official guide](https://docs.anthropic.com/en/docs/claude-code).
- **A Portals account** — sign up at [theportal.to](https://theportal.to) if you don't have one.

### Step 1: Clone the repo

Open your terminal and run:

```bash
git clone <repo-url>
cd portals-mcp
```

(Replace `<repo-url>` with the actual repository URL.)

### Step 2: Install the Portals MCP

```bash
npx portals-mcp@latest
```

This installs the MCP server that lets Claude communicate with the Portals API. The repo's `.mcp.json` file is already configured to use it — Claude Code will launch it automatically on startup.

### Step 3: Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs libraries used by the local tools (for 3D model processing, thumbnail generation, etc.).

### Step 4: Launch Claude Code

```bash
claude
```

Run this from inside the project folder. Claude will automatically:
- Load the game designer instructions from `CLAUDE.md`
- Connect to the Portals API via the MCP server (configured in `.mcp.json`)
- Be ready to design and build games

On first use, Claude will authenticate with Portals by opening a browser window where you can log in. After that, you're ready to go.

## Using It

### Starting a new game

Just tell Claude what you want:

- "I want to build a game"
- "Make me an escape room"
- "I have a room, here's the ID: abc-123-def"

Claude will ask whether you want to design every detail together or have it surprise you with the best game it can think of. Either way, it follows a structured process:

1. **Design** — Claude asks about your vision (story, mechanics, feel), then writes a design document for your approval
2. **Build** — once you approve the design, Claude generates all the room data (items, interactions, quests, lighting, audio) and pushes it to your room
3. **Playtest** — you visit your room at `https://theportal.to/?room=<your-room-id>` and try it out
4. **Iterate** — tell Claude what to change ("the jumps are too hard", "add more enemies", "make the ending more dramatic") and it updates the room

### Working with an existing room

If you already have a Portals room with content, Claude can work with it. Give it your room ID and it will pull the current room data, index it, and understand what's already there before making changes.

### What Claude can do

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
CLAUDE.md                — Instructions for Claude (loaded automatically every session)
.mcp.json                — MCP server config (connects Claude to Portals API)
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

When you build a game, Claude creates a folder under `games/` with your room ID containing the design document, build scripts, 3D model catalog, and generated room data.

## What's in the Documentation

The `docs/` folder contains everything Claude needs to know about Portals. You generally don't need to read these yourself (Claude reads them on demand), but here's what's there:

- **26+ item types** — cubes, 3D models, lights, NPCs, triggers, collectibles, images, videos, particle effects, and more
- **21 trigger types** — click, enter zone, exit zone, collide, hover, key press, take damage, and more
- **63+ effect types** — show/hide, move, teleport, play sound, spawn particles, change avatar, lock camera, deal damage, update score, and more
- **Quest system** — multi-state quests with progression, persistence, and per-player tracking
- **Settings** — room-level configuration for lighting, fog, movement physics, avatars, UI toggles
- **Workflow guides** — step-by-step processes for design, building, quality review, scene layout, and more

## Troubleshooting

**"Claude doesn't seem to know about Portals"**
Make sure you're running `claude` from inside this project folder. Claude reads `CLAUDE.md` from the current directory.

**"MCP connection failed" or "authenticate failed"**
Check that Node.js is installed (`node --version`) and try authenticating again — Claude will open a browser window for you to log in.

**"Permission denied" when pushing room data**
You need write permissions for the room you're targeting. Check that you own the room or have admin access.

**"Module not found" errors from Python tools**
Run `pip install -r requirements.txt` to install dependencies.

## License

MIT — see [LICENSE](LICENSE)
