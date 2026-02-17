#!/usr/bin/env python3
"""
Extract metadata + multi-view thumbnails from GLB files.
Produces a catalog.json and per-item thumbnail PNGs for a Portals room.

Usage:
    python extract_glb_metadata.py <glb_folder_or_file> <room_id> [--cdn-urls urls.json]

The --cdn-urls flag accepts a JSON file mapping filenames to CDN URLs.
If omitted, URLs default to empty strings (fill in later or upload first).
"""

import argparse
import json
import os
import sys
import math
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')  # headless
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from pathlib import Path
from PIL import Image


GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "games")


def load_glb(path):
    """Load a GLB and return a single combined trimesh."""
    scene = trimesh.load(path, force='scene')
    meshes = [g for g in scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
    if not meshes:
        raise ValueError(f"No meshes found in {path}")
    combined = trimesh.util.concatenate(meshes)
    return combined, scene


def detect_edges(mesh):
    """Detect which cardinal faces (±X, ±Z) are open vs closed.

    Uses face-area coverage analysis: counts mesh triangles that form
    wall panels (normals facing outward) near each bounding box face.
    High coverage = wall, low coverage = opening.

    GLB convention: Y-up, so passage height is along Y axis.

    Returns dict with keys '+x', '-x', '+z', '-z', each having:
      - state: 'open', 'closed', or 'door' (partially open)
      - openness: float 0.0 (fully blocked) to 1.0 (fully open)
    """
    bounds = mesh.bounds
    bmin, bmax = bounds[0], bounds[1]
    size = bmax - bmin

    # If piece is very flat (< 0.5m tall), skip edge detection
    if size[1] < 0.5:
        return None

    # Passage height band: skip bottom 10% (floor) and top 10% (ceiling)
    y_lo = bmin[1] + size[1] * 0.10
    y_hi = bmax[1] - size[1] * 0.10

    # Get triangle data
    face_normals = mesh.face_normals
    face_centroids = mesh.triangles_center
    face_areas = mesh.area_faces

    # Search threshold: look for wall geometry within 15% of piece size from face
    threshold = max(size[0], size[2]) * 0.15

    edges = {}

    face_configs = [
        # (name, axis, sign, face_pos, tangent_axis)
        ('+x', 0, +1, bmax[0], 2),
        ('-x', 0, -1, bmin[0], 2),
        ('+z', 2, +1, bmax[2], 0),
        ('-z', 2, -1, bmin[2], 0),
    ]

    for name, axis, sign, face_pos, tangent in face_configs:
        # Find triangles near this face boundary
        near_face = np.abs(face_centroids[:, axis] - face_pos) < threshold
        # In the passage height band (not floor/ceiling)
        in_height = (face_centroids[:, 1] > y_lo) & (face_centroids[:, 1] < y_hi)
        # Normal has significant component along the face direction (wall panels)
        facing = (face_normals[:, axis] * sign) > 0.3

        mask = near_face & in_height & facing
        covered_area = face_areas[mask].sum()

        # Total face area = face width × passage height
        face_width = size[tangent]
        face_height = y_hi - y_lo
        total_face_area = face_width * face_height

        coverage = covered_area / total_face_area if total_face_area > 0 else 0
        openness = round(max(0.0, 1.0 - min(coverage, 1.0)), 3)

        if openness > 0.6:
            state = 'open'
        elif openness > 0.3:
            state = 'door'
        else:
            state = 'closed'

        edges[name] = {'state': state, 'openness': openness}

    return edges


def extract_metadata(mesh):
    """Extract spatial metadata from a trimesh."""
    bounds = mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    aabb_min = bounds[0].tolist()
    aabb_max = bounds[1].tolist()
    size = (bounds[1] - bounds[0]).tolist()
    center = ((bounds[0] + bounds[1]) / 2).tolist()

    # Pivot is at origin (0,0,0) for most GLBs
    pivot = [0.0, 0.0, 0.0]

    # Footprint (XZ at ground plane)
    footprint = [size[0], size[2]]

    # PCA
    try:
        vertices = mesh.vertices
        centered = vertices - vertices.mean(axis=0)
        cov = np.cov(centered.T)
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        # Sort by eigenvalue descending
        idx = np.argsort(eigenvalues)[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]
        pca_axes = eigenvectors.T.tolist()  # each row is an axis
        # PCA extents: project vertices onto each axis, measure range
        pca_extents = []
        for axis in eigenvectors.T:
            projections = centered @ axis
            pca_extents.append(float(projections.max() - projections.min()))
    except Exception:
        pca_axes = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        pca_extents = size

    triangles = len(mesh.faces)

    # Programmatic edge detection via ray casting
    edges = detect_edges(mesh)

    result = {
        "units": "meters",
        "up_axis": "Y",
        "front": [0, 0, -1],  # default assumption, visual check will refine
        "aabb": {"min": [round(v, 4) for v in aabb_min], "max": [round(v, 4) for v in aabb_max]},
        "size": [round(v, 4) for v in size],
        "center": [round(v, 4) for v in center],
        "pivot": pivot,
        "footprint": [round(v, 4) for v in footprint],
        "pca_axes": [[round(v, 4) for v in axis] for axis in pca_axes],
        "pca_extents": [round(v, 4) for v in pca_extents],
        "triangles": triangles,
    }

    if edges is not None:
        result["edges"] = edges

    return result


def render_view(ax, mesh, elevation, azimuth, title):
    """Render a single view of the mesh onto a matplotlib axis."""
    vertices = mesh.vertices.copy()
    faces = mesh.faces

    # Convert GLB Y-up to matplotlib Z-up via +90° rotation around X-axis.
    # This preserves handedness (right-handed → right-handed), unlike a
    # simple Y↔Z column swap which mirrors horizontally.
    # Mapping: (x, y, z)_glb → (x, -z, y)_mpl
    new_y = -vertices[:, 2].copy()
    new_z = vertices[:, 1].copy()
    vertices[:, 1] = new_y
    vertices[:, 2] = new_z

    # Subsample faces if too many (for rendering speed)
    max_faces = 5000
    if len(faces) > max_faces:
        indices = np.random.choice(len(faces), max_faces, replace=False)
        faces_subset = faces[indices]
    else:
        faces_subset = faces

    # Create polygon collection
    verts_for_faces = vertices[faces_subset]

    # Simple shading based on face normals
    face_normals = np.cross(
        verts_for_faces[:, 1] - verts_for_faces[:, 0],
        verts_for_faces[:, 2] - verts_for_faces[:, 0]
    )
    norms = np.linalg.norm(face_normals, axis=1, keepdims=True)
    norms[norms == 0] = 1
    face_normals = face_normals / norms

    # Light from upper-right-front
    light_dir = np.array([0.5, 0.8, 0.6])
    light_dir = light_dir / np.linalg.norm(light_dir)
    intensity = np.abs(face_normals @ light_dir)
    intensity = 0.3 + 0.7 * intensity  # ambient + diffuse

    colors = np.zeros((len(faces_subset), 4))
    colors[:, 0] = 0.55 * intensity  # R
    colors[:, 1] = 0.65 * intensity  # G
    colors[:, 2] = 0.75 * intensity  # B
    colors[:, 3] = 1.0

    collection = Poly3DCollection(verts_for_faces, facecolors=colors, edgecolors='none', linewidths=0)
    ax.add_collection3d(collection)

    # Set view — after the +90° X rotation, vertex coords are in matplotlib's
    # Z-up convention with preserved handedness.
    bounds_swapped = vertices.min(axis=0), vertices.max(axis=0)
    center = (bounds_swapped[0] + bounds_swapped[1]) / 2
    extent = (bounds_swapped[1] - bounds_swapped[0]).max() * 0.65

    ax.set_xlim(center[0] - extent, center[0] + extent)
    ax.set_ylim(center[1] - extent, center[1] + extent)
    ax.set_zlim(center[2] - extent, center[2] + extent)

    ax.view_init(elev=elevation, azim=azimuth)
    ax.set_title(title, fontsize=9, fontweight='bold', pad=2)
    ax.set_axis_off()


def render_thumbnail(mesh, output_path):
    """Render a 2x2 multi-view composite thumbnail."""
    fig = plt.figure(figsize=(8, 8), facecolor='#1a1a2e')

    # Camera angles calibrated for the (x, -z, y) coordinate transform.
    # After transform: mpl_x = GLB_x, mpl_y = -GLB_z, mpl_z = GLB_y
    # Front (-Z): azim=90 → camera at mpl_y<0 → GLB_z>0 → looking toward -Z ✓
    # Right (+X): azim=0  → camera at mpl_x>0 → looking toward -X from +X ✓
    # Top:        elev=90 → camera above  → looking down at XZ plane ✓
    # Perspective: azim=45 → camera at upper-right-front
    views = [
        (10, 90, "Front (-Z)"),
        (10, 0, "Right (+X)"),
        (90, -90, "Top"),
        (25, 45, "Perspective"),
    ]

    for i, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(2, 2, i + 1, projection='3d', facecolor='#1a1a2e')
        ax.title.set_color('white')
        render_view(ax, mesh, elev, azim, title)

    plt.tight_layout(pad=1.0)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close(fig)


def slugify(filename):
    """Convert a filename to a clean catalog key."""
    name = Path(filename).stem
    # Lowercase, replace spaces/special chars with underscores
    slug = name.lower().replace(' ', '_').replace('-', '_')
    # Remove double underscores
    while '__' in slug:
        slug = slug.replace('__', '_')
    return slug


def process_glb(glb_path, thumbnail_dir, cdn_url=""):
    """Process a single GLB file. Returns (key, catalog_entry)."""
    filename = os.path.basename(glb_path)
    key = slugify(filename)

    print(f"  Processing: {filename} -> {key}")

    # Track file size
    file_size_bytes = os.path.getsize(glb_path)

    # Load and extract
    mesh, scene = load_glb(glb_path)
    metadata = extract_metadata(mesh)

    # Render thumbnail
    thumb_path = os.path.join(thumbnail_dir, f"{key}.png")
    render_thumbnail(mesh, thumb_path)
    print(f"    Thumbnail: {thumb_path}")

    # Build catalog entry
    entry = {
        "name": Path(filename).stem.replace('_', ' '),
        "description": "",
        "category": "",
        "url": cdn_url,
        "source_file": filename,
        "file_size_bytes": file_size_bytes,
        **metadata,
    }

    return key, entry


def main():
    parser = argparse.ArgumentParser(description="Extract GLB metadata and thumbnails for Portals catalog")
    parser.add_argument("input", help="Path to a GLB file or folder of GLBs")
    parser.add_argument("room_id", help="Room ID (used for output folder)")
    parser.add_argument("--cdn-urls", help="JSON file mapping filenames to CDN URLs", default=None)
    args = parser.parse_args()

    # Set up paths
    room_dir = os.path.join(GAMES_DIR, args.room_id)
    thumbnail_dir = os.path.join(room_dir, "thumbnails")
    catalog_path = os.path.join(room_dir, "catalog.json")
    os.makedirs(thumbnail_dir, exist_ok=True)

    # Load existing catalog if present
    if os.path.exists(catalog_path):
        with open(catalog_path) as f:
            catalog = json.load(f)
    else:
        catalog = {"room_id": args.room_id, "items": {}}

    # Load CDN URL mapping if provided
    cdn_urls = {}
    if args.cdn_urls:
        with open(args.cdn_urls) as f:
            cdn_urls = json.load(f)

    # Find GLB files
    input_path = os.path.abspath(args.input)
    if os.path.isfile(input_path):
        glb_files = [input_path]
    elif os.path.isdir(input_path):
        glb_files = sorted([
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith('.glb')
        ])
    else:
        print(f"Error: {input_path} is not a file or directory")
        sys.exit(1)

    print(f"Found {len(glb_files)} GLB files")
    print(f"Output: {room_dir}")
    print()

    for glb_path in glb_files:
        filename = os.path.basename(glb_path)
        cdn_url = cdn_urls.get(filename, "")

        try:
            key, entry = process_glb(glb_path, thumbnail_dir, cdn_url)
            catalog["items"][key] = entry
            print(f"    Size: {entry['size']}, Triangles: {entry['triangles']}")
            if 'edges' in entry:
                edge_summary = ', '.join(
                    f"{k}={v['state']}({v['openness']:.0%})"
                    for k, v in entry['edges'].items()
                )
                print(f"    Edges: {edge_summary}")
            print()
        except Exception as e:
            print(f"    ERROR: {e}")
            print()

    # Save catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)

    print(f"Catalog saved: {catalog_path}")
    print(f"Total items: {len(catalog['items'])}")

    # Storage check on processed files
    try:
        from check_room_storage import check_storage, print_report
        total_bytes, status, file_details = check_storage(paths=[input_path])
        print_report(total_bytes, status, file_details)
    except ImportError:
        # Fallback: inline summary if module not available
        total_size = sum(
            entry.get("file_size_bytes", 0)
            for entry in catalog["items"].values()
        )
        mb = total_size / (1024 * 1024)
        print(f"\nTotal unique GLB storage: {mb:.1f} MB")
        if mb > 500:
            print("CRITICAL: Over 500 MB — room may not load properly")
        elif mb > 200:
            print("WARNING: Over 200 MB — room is heavy, consider optimizing")

    # Note: modular kit classification is now done during manual thumbnail review.
    # See docs/systems/glb-asset-catalog.md "Modular Kit Reference" section.


if __name__ == "__main__":
    main()
