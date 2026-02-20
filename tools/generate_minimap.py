#!/usr/bin/env python3
"""
Generate a top-down minimap image from a Portals room snapshot.

Usage:
    python tools/generate_minimap.py games/{room-id}/snapshot.json

Output:
    games/{room-id}/minimap.png — top-down schematic
    Prints the complete minimap URL with bounds to stdout
"""

import json
import sys
import os
import math

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.transforms as transforms
except ImportError:
    print("ERROR: matplotlib is required. Install with: pip install matplotlib")
    sys.exit(1)


def quat_to_yaw(rot):
    """Extract Y-axis rotation (yaw) from quaternion {x, y, z, w}."""
    x = rot.get('x', 0)
    y = rot.get('y', 0)
    z = rot.get('z', 0)
    w = rot.get('w', 1)
    siny_cosp = 2 * (w * y + x * z)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    return math.atan2(siny_cosp, cosy_cosp)


def rotated_footprint(scale, rot):
    """Compute X-Z footprint and Y height of a cube after full 3D rotation.

    Returns (width, depth, yaw, y_height).
    For Y-only rotations: (scale.x, scale.z, yaw, scale.y).
    For cubes rotated around X or Z (e.g. floors): AABB extents with yaw=0.
    """
    qx = rot.get('x', 0)
    qy = rot.get('y', 0)
    qz = rot.get('z', 0)
    qw = rot.get('w', 1)
    sx = scale.get('x', 1)
    sy = scale.get('y', 1)
    sz = scale.get('z', 1)

    # Fast path: Y-only rotation (no X/Z tilt) — most cubes
    if abs(qx) < 0.001 and abs(qz) < 0.001:
        return sx, sz, quat_to_yaw(rot), sy

    # Full rotation: rotate 8 corners and compute AABB on all axes
    hx, hy, hz = sx / 2, sy / 2, sz / 2
    min_x = min_y = min_z = float('inf')
    max_x = max_y = max_z = float('-inf')
    for dx in (-1, 1):
        for dy in (-1, 1):
            for dz in (-1, 1):
                vx, vy, vz = dx * hx, dy * hy, dz * hz
                # q * v * q^-1 via rodrigues
                tx = 2 * (qy * vz - qz * vy)
                ty = 2 * (qz * vx - qx * vz)
                tz = 2 * (qx * vy - qy * vx)
                rx = vx + qw * tx + (qy * tz - qz * ty)
                ry = vy + qw * ty + (qz * tx - qx * tz)
                rz = vz + qw * tz + (qx * ty - qy * tx)
                min_x = min(min_x, rx)
                max_x = max(max_x, rx)
                min_y = min(min_y, ry)
                max_y = max(max_y, ry)
                min_z = min(min_z, rz)
                max_z = max(max_z, rz)

    return max_x - min_x, max_z - min_z, 0, max_y - min_y


def load_snapshot(path):
    with open(path) as f:
        data = json.load(f)
    return data.get('roomItems', {})


def extract_footprints(items):
    """Extract 2D footprints (top-down rectangles) from room items."""
    footprints = []
    for item_id, item in items.items():
        prefab = item.get('prefabName', '')
        pos = item.get('pos', {})
        scale = item.get('scale', {})
        rot = item.get('rot', {})
        px = pos.get('x', 0)
        py = pos.get('y', 0)
        pz = pos.get('z', 0)
        sx = scale.get('x', 1)
        sz = scale.get('z', 1)

        # Skip items far below ground — hidden/utility items
        if py < -2:
            continue

        if prefab == 'ResizableCube':
            w, d, yaw, y_height = rotated_footprint(scale, rot)
            # Thin cubes after rotation are floors/ceilings — render subtly
            cube_type = 'floor' if y_height < 0.5 else 'cube'
            footprints.append({
                'x': px, 'z': pz,
                'w': w, 'd': d,
                'yaw': yaw,
                'type': cube_type
            })
        elif prefab in ('GLB', 'GlbCollectable', 'Destructible'):
            footprints.append({
                'x': px, 'z': pz,
                'w': sx * 0.5, 'd': sz * 0.5,
                'yaw': 0,
                'type': 'glb'
            })
        elif prefab in ('GLBNPC', 'EnemyNPC'):
            footprints.append({
                'x': px, 'z': pz,
                'w': 0.4, 'd': 0.4,
                'yaw': 0,
                'type': 'npc'
            })
        elif prefab == 'SpawnPoint':
            footprints.append({
                'x': px, 'z': pz,
                'w': 0.3, 'd': 0.3,
                'yaw': 0,
                'type': 'spawn'
            })
        elif prefab == 'Trigger':
            w, d, yaw, _ = rotated_footprint(scale, rot)
            footprints.append({
                'x': px, 'z': pz,
                'w': w, 'd': d,
                'yaw': yaw,
                'type': 'trigger'
            })
    return footprints


def render_minimap(footprints, output_path, dpi=150):
    """Render top-down PNG from footprints.

    Returns (img_w, img_h, x_min, x_max, z_min, z_max) or None.
    """
    if not footprints:
        print("WARNING: No structural items found")
        return None

    # Calculate world bounds with padding
    all_x = [f['x'] for f in footprints]
    all_z = [f['z'] for f in footprints]
    padding = 5.0
    x_min = min(all_x) - padding
    x_max = max(all_x) + padding
    z_min = min(all_z) - padding
    z_max = max(all_z) + padding

    # Figure size proportional to world bounds
    # X = horizontal (left/right), Z = vertical (forward/back)
    x_range = x_max - x_min
    z_range = z_max - z_min
    fig_w = 6
    fig_h = max(fig_w * (z_range / x_range), 2) if x_range > 0 else 6

    fig, ax = plt.subplots(1, 1, figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor('#0a0e14')
    ax.set_facecolor('#0a0e14')

    # Color map by type
    colors = {
        'cube': '#2a3a4a',
        'floor': 'none',       # outline only
        'glb': '#3a4a5a',
        'npc': '#c4a35a',
        'spawn': '#69d2ff',
        'trigger': '#ff6b6b44',
    }

    # Draw floors first (zorder=0) so walls/objects render on top
    sorted_fps = sorted(footprints, key=lambda f: 0 if f['type'] == 'floor' else 1)

    for fp in sorted_fps:
        color = colors.get(fp['type'], '#333')
        if fp['type'] in ('spawn', 'npc'):
            ax.plot(fp['x'], fp['z'], 'o', color=color, markersize=6, zorder=3)
        elif fp['type'] == 'floor':
            rect = patches.FancyBboxPatch(
                (fp['x'] - fp['w'] / 2, fp['z'] - fp['d'] / 2),
                fp['w'], fp['d'],
                boxstyle="round,pad=0.02",
                facecolor='#1a2030',
                edgecolor='#2a3a4a55',
                linewidth=0.5,
                zorder=0
            )
            t = transforms.Affine2D().rotate_around(
                fp['x'], fp['z'], -fp['yaw']
            ) + ax.transData
            rect.set_transform(t)
            ax.add_patch(rect)
        else:
            rect = patches.FancyBboxPatch(
                (fp['x'] - fp['w'] / 2, fp['z'] - fp['d'] / 2),
                fp['w'], fp['d'],
                boxstyle="round,pad=0.02",
                facecolor=color,
                edgecolor='#4a5a6a33',
                linewidth=0.5,
                zorder=1
            )
            t = transforms.Affine2D().rotate_around(
                fp['x'], fp['z'], -fp['yaw']
            ) + ax.transData
            rect.set_transform(t)
            ax.add_patch(rect)

    # Grid — X horizontal (left/right), Z vertical (+Z = forward = up on map)
    # matplotlib default: y increases upward → z_max at top of plot → top of saved PNG
    # HTML worldToImg maps zMax to imgY=0 (top) — these match without inversion
    ax.grid(True, alpha=0.08, color='#69d2ff', linewidth=0.5)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(z_min, z_max)
    ax.set_aspect('equal')
    ax.axis('off')

    plt.tight_layout(pad=0)
    fig.savefig(output_path, facecolor=fig.get_facecolor(),
                bbox_inches='tight', pad_inches=0)
    plt.close(fig)

    # Read actual image dimensions
    try:
        from PIL import Image
        with Image.open(output_path) as im:
            img_w, img_h = im.size
    except ImportError:
        # Fallback: estimate from figure
        img_w = int(fig_w * dpi)
        img_h = int(fig_h * dpi)

    return img_w, img_h, x_min, x_max, z_min, z_max


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/generate_minimap.py <snapshot.json>")
        sys.exit(1)

    snapshot_path = sys.argv[1]
    output_dir = os.path.dirname(snapshot_path) or '.'
    output_path = os.path.join(output_dir, 'minimap.png')

    items = load_snapshot(snapshot_path)
    footprints = extract_footprints(items)
    print(f"Found {len(footprints)} items for minimap")

    result = render_minimap(footprints, output_path)
    if result is None:
        sys.exit(1)

    img_w, img_h, x_min, x_max, z_min, z_max = result
    print(f"Generated: {output_path} ({img_w}x{img_h}px)")
    print(f"World bounds: X[{x_min:.1f}, {x_max:.1f}] Z[{z_min:.1f}, {z_max:.1f}]")
    print()
    print("Upload minimap.png, then use this URL (replace MAP_CDN_URL):")
    print(f"  minimap.html?map=MAP_CDN_URL"
          f"&xMin={x_min:.2f}&xMax={x_max:.2f}"
          f"&zMin={z_min:.2f}&zMax={z_max:.2f}"
          f"&imgW={img_w}&imgH={img_h}"
          f"&shape=circle&radius=126&showAll=true&style=dark")


if __name__ == '__main__':
    main()
