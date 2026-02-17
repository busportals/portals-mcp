"""
Board Helpers — Reusable functions for generating a game logic visualization board.

USAGE: Copy these functions into your game's generate.py, inside the
"# LOGIC BOARD" section. They depend on your script's `add()`, `create_cube()`,
`create_text()`, and `create_light()` functions already being defined.

All board items are parented to a base board cube. Positions use board-local
coordinates (lx, ly) which are offsets from BOARD_POS.
"""

import json
import math
import uuid


# =============================================================================
# CONFIGURATION — Adjust these for your game
# =============================================================================

S = 4.5  # Scale factor — all measurements multiplied by this

# Board placement (position behind/above the main game area)
BOARD_POS = (0, S * 6, -40)
BOARD_SCALE = (18 * S, 12 * S, 0.15)
BOARD_COLOR = "080812"  # Dark navy

# Z-layering (prevents z-fighting between overlapping elements)
BOARD_Z_GRID = -0.01     # Background grid lines
BOARD_Z_CONN = 0.07      # Connector bars
BOARD_Z_FRONT = 0.10     # Node rectangles
BOARD_Z_PULSE = 0.11     # Animated pulses
BOARD_Z_TEXT = 0.16       # Text labels

# Node colors (cyberpunk palette)
COL_INPUT = "FFB800"      # Amber — player actions
COL_LOGIC = "9B59B6"      # Purple — logic/conditions
COL_QUEST = "2ECC71"      # Emerald — quest state changes
COL_EFFECT = "00D4FF"     # Cyan — output effects
COL_CONNECTOR = "2A2A40"  # Dim connector bars
COL_PULSE = "00D4FF"      # Bright cyan (default pulse color)
COL_DELAY_TEXT = "FF8C00"  # Orange delay labels
COL_LABEL = "AAAAAA"      # Gray sublabels
COL_BORDER = "1C1C2E"     # Subtle grid/border

# Dim colors for auto-reset nodes
COL_DIM_RED = "992222"
COL_DIM_BLUE = "223399"
COL_DIM_GREEN = "1A7A3A"
COL_DIM_GRAY = "444444"

# Sizing (all scaled by S)
NODE_W = S * 2.0           # Standard node width
NODE_H = S * 1.0           # Standard node height
NODE_THICK = 0.04          # Node Z thickness
SMALL_W = S * 1.5          # Small node width (effects, resets)
SMALL_H = S * 0.7          # Small node height
CONNECTOR_H = S * 0.05     # Connector bar height (thin)
CONNECTOR_THICK = 0.03     # Connector Z thickness
CONN_GAP = S * 0.08        # Inset from node edges
PULSE_SIZE = S * 0.12      # Animated pulse cube size
PULSE_SPEED = S * 3.0      # Units per second for pulse travel
TEXT_SCALE = 6              # Multiplier for all board text


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def board_item(item, board_id, add_fn, title=""):
    """Add an item parented to the logic board.

    Args:
        item: The item dict (from create_cube, create_text, etc.)
        board_id: The ID of the base board cube (returned by add_fn)
        add_fn: Your script's add() function
        title: Optional title for the item
    Returns:
        The item ID string
    """
    item["parentItemID"] = int(board_id)
    return add_fn(item, title)


def board_node(lx, ly, w, h, color, board_id, add_fn, create_cube_fn,
               emission=0.35, title=""):
    """Create a colored node rectangle on the board.

    Args:
        lx, ly: Board-local position (center of node)
        w, h: Width and height of the node
        color: Hex color string (no #)
        board_id: Base board item ID
        add_fn: Your add() function
        create_cube_fn: Your create_cube() function
        emission: Glow intensity (default 0.35)
        title: Optional title
    """
    node = create_cube_fn(
        pos=(lx, ly, BOARD_Z_FRONT),
        scale=(w, h, NODE_THICK),
        color=color, emission=emission,
        collider=False, shadows=False
    )
    return board_item(node, board_id, add_fn, title)


def board_node_border(lx, ly, w, h, color, board_id, add_fn, create_cube_fn,
                      emission=0.15):
    """Create a subtle border glow around a node.

    Slightly larger than the node, slightly behind it in Z.
    """
    border = create_cube_fn(
        pos=(lx, ly, BOARD_Z_FRONT - 0.005),
        scale=(w + S * 0.12, h + S * 0.12, NODE_THICK),
        color=color, emission=emission,
        collider=False, shadows=False
    )
    return board_item(border, board_id, add_fn)


def board_label(lx, ly, text, board_id, add_fn, create_text_fn,
                scale=None):
    """Create a text label on the board.

    Args:
        lx, ly: Board-local position
        text: Rich text content (supports <b>, <color=#HEX>, <size=N%>)
        scale: Base scale before TEXT_SCALE multiplier (default S * 0.45)
    """
    if scale is None:
        scale = S * 0.45
    s = scale * TEXT_SCALE
    txt = create_text_fn(
        pos=(lx, ly, BOARD_Z_TEXT),
        content=text, billboard=False,
        scale=(s, s, s)
    )
    return board_item(txt, board_id, add_fn)


def board_connector_h(x1, x2, y, board_id, add_fn, create_cube_fn,
                      color=None, emission=0.15, gap=True):
    """Create a horizontal connector bar between two X positions.

    Args:
        x1, x2: Start and end X positions (board-local)
        y: Y position (board-local)
        gap: If True, inset from node edges by CONN_GAP
    """
    if color is None:
        color = COL_CONNECTOR
    if gap:
        if x1 < x2:
            x1 += CONN_GAP
            x2 -= CONN_GAP
        else:
            x1 -= CONN_GAP
            x2 += CONN_GAP
    cx = (x1 + x2) / 2
    length = abs(x2 - x1)
    conn = create_cube_fn(
        pos=(cx, y, BOARD_Z_CONN),
        scale=(length, CONNECTOR_H, CONNECTOR_THICK),
        color=color, emission=emission,
        collider=False, shadows=False
    )
    return board_item(conn, board_id, add_fn)


def board_connector_v(x, y1, y2, board_id, add_fn, create_cube_fn,
                      color=None, emission=0.15, gap=True):
    """Create a vertical connector bar between two Y positions.

    Args:
        x: X position (board-local)
        y1, y2: Start and end Y positions (top to bottom typically)
        gap: If True, inset from node edges by CONN_GAP
    """
    if color is None:
        color = COL_CONNECTOR
    if gap:
        if y1 > y2:
            y1 -= CONN_GAP
            y2 += CONN_GAP
        else:
            y1 += CONN_GAP
            y2 -= CONN_GAP
    cy = (y1 + y2) / 2
    length = abs(y2 - y1)
    conn = create_cube_fn(
        pos=(x, cy, BOARD_Z_CONN),
        scale=(CONNECTOR_H, length, CONNECTOR_THICK),
        color=color, emission=emission,
        collider=False, shadows=False
    )
    return board_item(conn, board_id, add_fn)


def board_connector_diag(x1, y1, x2, y2, board_id, add_fn, create_cube_fn,
                         color=None, emission=0.15):
    """Create a diagonal connector (rotated thin bar).

    Uses Z-axis quaternion rotation to angle the bar between two points.
    """
    if color is None:
        color = COL_CONNECTOR
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx * dx + dy * dy)
    length = max(length - CONN_GAP * 2, 0.1)  # Inset both ends
    angle = math.atan2(dy, dx)
    qz = math.sin(angle / 2)
    qw = math.cos(angle / 2)

    conn = create_cube_fn(
        pos=(cx, cy, BOARD_Z_CONN),
        scale=(length, CONNECTOR_H, CONNECTOR_THICK),
        color=color, emission=emission,
        collider=False, shadows=False
    )
    # Apply Z-axis rotation
    conn["rot"] = {"x": 0, "y": 0, "z": qz, "w": qw}
    return board_item(conn, board_id, add_fn)


def world_pos(lx, ly, lz=None):
    """Convert board-local coords to world coords."""
    if lz is None:
        lz = BOARD_Z_FRONT
    return (BOARD_POS[0] + lx, BOARD_POS[1] + ly, BOARD_POS[2] + lz)


def board_pulse(waypoints, board_id, add_fn, create_cube_fn,
                color=None):
    """Create an animated pulse that travels along waypoints.

    Args:
        waypoints: List of (lx, ly) board-local coordinates
        board_id: Base board item ID
        color: Hex color for the pulse (default COL_PULSE)

    The pulse is a small glowing cube with a PortalsAnimation that loops
    through the waypoints. Triggered on OnPlayerLoggedIn.
    """
    if color is None:
        color = COL_PULSE
    if len(waypoints) < 2:
        return

    start_lx, start_ly = waypoints[0]
    pulse = create_cube_fn(
        pos=(start_lx, start_ly, BOARD_Z_PULSE),
        scale=(PULSE_SIZE, PULSE_SIZE, PULSE_SIZE),
        color=color, emission=1.0,
        collider=False, shadows=False, opacity=0.9
    )

    # Build animation keyframes
    transform_states = []
    states = []
    for i, (lx, ly) in enumerate(waypoints):
        wx, wy, wz = world_pos(lx, ly, BOARD_Z_PULSE)
        if i == 0:
            dur = 0.0
        else:
            prev_lx, prev_ly = waypoints[i - 1]
            dist = math.sqrt((lx - prev_lx)**2 + (ly - prev_ly)**2)
            dur = max(dist / PULSE_SPEED, 0.1)

        transform_states.append({
            "position": [wx, wy, wz],
            "rotation": [0, 0, 0, 1],
            "scale": [PULSE_SIZE, PULSE_SIZE, PULSE_SIZE],
            "duration": dur
        })
        states.append({
            "x": wx, "y": wy, "z": wz,
            "sx": PULSE_SIZE, "sy": PULSE_SIZE, "sz": PULSE_SIZE,
            "duration": dur
        })

    anim_effector = {
        "$type": "PortalsAnimation",
        "stateEvents": [],
        "_transformStates": transform_states,
        "states": states,
        "loopAnimation": True,
        "seamless": True
    }

    anim_task = {
        "$type": "TaskTriggerSubscription",
        "Trigger": {"$type": "OnPlayerLoggedIn"},
        "DirectEffector": {
            "Effector": anim_effector,
            "Id": str(uuid.uuid4()),
            "TargetState": 2,
            "Name": ""
        },
        "Id": str(uuid.uuid4()),
        "TargetState": 2,
        "Name": ""
    }

    extra = json.loads(pulse["extraData"])
    extra["Tasks"].append(anim_task)
    pulse["extraData"] = json.dumps(extra, separators=(',', ':'))

    return board_item(pulse, board_id, add_fn, "Pulse")


def delay_label(x, y, text, board_id, add_fn, create_text_fn,
                color=None, scale=None):
    """Small delay/timing annotation positioned above a connector.

    Rendered in orange by default, 80% size.
    """
    if color is None:
        color = COL_DELAY_TEXT
    if scale is None:
        scale = S * 0.3
    return board_label(
        x, y + S * 0.18,
        f"<color=#{color}><size=80%>{text}</size></color>",
        board_id, add_fn, create_text_fn, scale
    )


# =============================================================================
# COMPOSITE HELPERS — Higher-level functions for common patterns
# =============================================================================

def add_legend(base_x, base_y, node_types, board_id, add_fn,
               create_cube_fn, create_text_fn):
    """Generate a legend in the corner of the board.

    Args:
        base_x, base_y: Top-left position of legend (board-local)
        node_types: List of (label, color) tuples, e.g.:
            [("Player Action", COL_INPUT), ("Logic", COL_LOGIC), ...]
    """
    board_label(
        base_x, base_y,
        f"<color=#{COL_LABEL}><size=80%><b>LEGEND</b></size></color>",
        board_id, add_fn, create_text_fn, S * 0.35
    )
    for i, (label, color) in enumerate(node_types):
        row_y = base_y - S * (0.45 + i * 0.4)
        board_node(
            base_x - S * 1.2, row_y, S * 0.3, S * 0.2, color,
            board_id, add_fn, create_cube_fn, emission=0.5
        )
        board_label(
            base_x, row_y,
            f"<color=#{COL_LABEL}><size=70%>{label}</size></color>",
            board_id, add_fn, create_text_fn, S * 0.28
        )


def add_decorations(board_id, add_fn, create_cube_fn, create_light_fn):
    """Add grid lines, corner accents, edge glow, and board light.

    Call this after all nodes/connectors/labels are placed.
    """
    # Subtle grid lines
    for gx_i in range(-8, 9, 2):
        item = create_cube_fn(
            pos=(S * gx_i, 0, BOARD_Z_GRID),
            scale=(0.02, S * 11, 0.005),
            color=COL_BORDER, emission=0.03,
            collider=False, shadows=False
        )
        board_item(item, board_id, add_fn)

    for gy_i in range(-5, 6, 2):
        item = create_cube_fn(
            pos=(0, S * gy_i, BOARD_Z_GRID),
            scale=(S * 17, 0.02, 0.005),
            color=COL_BORDER, emission=0.03,
            collider=False, shadows=False
        )
        board_item(item, board_id, add_fn)

    # Corner accent markers
    for cx, cy in [(-8.5, 5.5), (8.5, 5.5), (-8.5, -5.5), (8.5, -5.5)]:
        item = create_cube_fn(
            pos=(S * cx, S * cy, BOARD_Z_FRONT),
            scale=(S * 0.3, S * 0.3, 0.03),
            color=COL_PULSE, emission=0.6,
            collider=False, shadows=False
        )
        board_item(item, board_id, add_fn)

    # Edge glow borders
    for edge_x in [-9, 9]:
        item = create_cube_fn(
            pos=(S * edge_x, 0, BOARD_Z_FRONT),
            scale=(0.05, S * 12, 0.03),
            color=COL_PULSE, emission=0.2,
            collider=False, shadows=False
        )
        board_item(item, board_id, add_fn)

    for edge_y in [-6, 6]:
        item = create_cube_fn(
            pos=(0, S * edge_y, BOARD_Z_FRONT),
            scale=(S * 18, 0.05, 0.03),
            color=COL_PULSE, emission=0.2,
            collider=False, shadows=False
        )
        board_item(item, board_id, add_fn)

    # Board light
    add_fn(create_light_fn(
        (BOARD_POS[0], BOARD_POS[1], BOARD_POS[2] + 5),
        color="334455", brightness=2.0, range=S * 8
    ), "BoardLight")


# =============================================================================
# BOARD CREATION — Main entry point
# =============================================================================

def create_board(add_fn, create_cube_fn):
    """Create the base board and return its ID.

    Call this first, then use the returned board_id for all other helpers.
    """
    board = create_cube_fn(
        pos=BOARD_POS, scale=BOARD_SCALE,
        color=BOARD_COLOR, emission=0.02,
        collider=False, shadows=False
    )
    return add_fn(board, "LogicBoard")


# =============================================================================
# EXAMPLE USAGE (for reference — adapt to your game)
# =============================================================================
#
# board_id = create_board(add, create_cube)
#
# # Title
# board_label(0, S * 5.2, "<b><color=#FFFFFF>MY GAME LOGIC</color></b>",
#             board_id, add, create_text, scale=S * 0.7)
#
# # Node
# board_node_border(click_x, click_y, NODE_W, NODE_H, COL_INPUT,
#                   board_id, add, create_cube)
# board_node(click_x, click_y, NODE_W, NODE_H, COL_INPUT,
#            board_id, add, create_cube, emission=0.45, title="Node_Click")
# board_label(click_x, click_y + S * 0.1,
#             "<b><color=#FFFFFF>CLICK</color></b>",
#             board_id, add, create_text, S * 0.4)
# board_label(click_x, click_y - S * 0.2,
#             f"<color=#{COL_LABEL}><size=60%>OnClickEvent</size></color>",
#             board_id, add, create_text, S * 0.3)
#
# # Connector
# board_connector_h(click_x + NODE_W/2, split_x - NODE_W/2, click_y,
#                   board_id, add, create_cube)
#
# # Delay label
# delay_label((click_x + split_x) / 2, click_y, "0.1s",
#             board_id, add, create_text)
#
# # Legend
# add_legend(S * 7.8, S * 5.0, [
#     ("Player Action", COL_INPUT),
#     ("Logic / Condition", COL_LOGIC),
#     ("Quest State", COL_QUEST),
#     ("Effect / Output", COL_EFFECT),
# ], board_id, add, create_cube, create_text)
#
# # Decorations
# add_decorations(board_id, add, create_cube, create_light)
#
# # Pulse
# board_pulse([
#     (click_x + NODE_W/2, click_y),
#     (split_x - NODE_W/2, split_y),
# ], board_id, add, create_cube, color=COL_INPUT)
