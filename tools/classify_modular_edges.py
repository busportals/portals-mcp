#!/usr/bin/env python3
"""
Classify modular kit piece edges via slab-based rasterization.

For each cardinal face (+X, -X, +Z, -Z) of a GLB mesh, this tool:
1. Extracts a thin slab of triangles near the bounding-box face
2. Projects those triangles onto a 2D plane (dropping the face axis)
3. Rasterizes them into a boolean image
4. Analyzes coverage in the "passage zone" (excluding floor/ceiling bands)
5. Classifies each face as open, closed, or uncertain

Also derives piece_type (straight, corner, t_junction, etc.) and
default_rotation from the classified edge pattern.

This module provides the foundational functions. The full CLI pipeline
(classify_piece, main) will be added in a later task.
"""

import os
import sys
import json
import argparse
import numpy as np
import trimesh
from PIL import Image, ImageDraw

# ── Module constants ────────────────────────────────────────────────────────

SLAB_PERCENT = 0.15
FLOOR_EXCLUDE = 0.15
CEILING_EXCLUDE = 0.15
OPEN_THRESHOLD = 0.20
CLOSED_THRESHOLD = 0.70
SIDE_EXCLUDE = 0.15    # side fraction of cell width to exclude (trim)
RENDER_RES = 128
EDGE_ORDER = ["+z", "+x", "-z", "-x"]
GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "games")


# ── 1. Mesh loading ────────────────────────────────────────────────────────

def load_mesh(glb_path):
    """Load a GLB file, combine all meshes, return a single trimesh.

    Matches the pattern from extract_glb_metadata.py load_glb().

    Args:
        glb_path: Path to a .glb file.

    Returns:
        trimesh.Trimesh: Combined mesh from all geometry in the scene.

    Raises:
        ValueError: If no meshes are found in the GLB.
    """
    scene = trimesh.load(glb_path, force='scene')
    meshes = [g for g in scene.geometry.values() if isinstance(g, trimesh.Trimesh)]
    if not meshes:
        raise ValueError(f"No meshes found in {glb_path}")
    return trimesh.util.concatenate(meshes)


# ── 2. Slab triangle filtering ─────────────────────────────────────────────

def get_slab_triangles(mesh, axis, slab_min, slab_max, normal_axis=None,
                       normal_threshold=0.1):
    """Filter mesh triangles whose centroids fall within a slab along an axis.

    Optionally also filters by face normal direction to exclude geometry
    that is perpendicular to the face being analyzed (e.g., side walls
    that extend to the boundary but don't block the passage).

    Args:
        mesh: trimesh.Trimesh object.
        axis: 0 (X), 1 (Y), or 2 (Z) — the axis to filter along.
        slab_min: Minimum coordinate along the axis.
        slab_max: Maximum coordinate along the axis.
        normal_axis: If set, also filter by face normal. Only keep triangles
            whose normal has abs(component) > normal_threshold along this axis.
            Typically set equal to `axis` to keep only face-facing geometry.
        normal_threshold: Minimum abs(normal component) to keep. Default 0.1.

    Returns:
        Tuple of (vertices, filtered_faces) where vertices is mesh.vertices
        and filtered_faces is an (N, 3) array of face indices within the slab.
        Returns (None, None) if no triangles fall within the slab.
    """
    centroids = mesh.triangles_center
    mask = (centroids[:, axis] >= slab_min) & (centroids[:, axis] <= slab_max)

    if normal_axis is not None:
        face_normals = mesh.face_normals
        normal_mask = np.abs(face_normals[:, normal_axis]) > normal_threshold
        mask = mask & normal_mask

    filtered_faces = mesh.faces[mask]
    if len(filtered_faces) == 0:
        return None, None
    return mesh.vertices, filtered_faces


# ── 3. 2D projection ───────────────────────────────────────────────────────

def project_to_2d(vertices, face_axis):
    """Project 3D vertices to 2D by dropping the face axis.

    Convention:
        - For +/-X faces (axis=0): u = Z, v = Y
        - For +/-Z faces (axis=2): u = X, v = Y

    Args:
        vertices: (N, 3) array of vertex positions.
        face_axis: 0 (X face) or 2 (Z face).

    Returns:
        Tuple of (u_array, v_array) as 1D numpy arrays.
    """
    if face_axis == 0:
        # X face: u=Z, v=Y
        u = vertices[:, 2]
        v = vertices[:, 1]
    else:
        # Z face: u=X, v=Y
        u = vertices[:, 0]
        v = vertices[:, 1]
    return u, v


# ── 4. Rasterization ───────────────────────────────────────────────────────

def rasterize_triangles(verts_u, verts_v, faces, u_min, u_max, v_min, v_max,
                        res_u, res_v):
    """Rasterize projected triangles into a boolean image.

    Draws each triangle as a filled white polygon on a black image.
    V axis is flipped so that high V (ceiling) maps to row 0 (top of image)
    and low V (floor) maps to row (res_v - 1) (bottom of image).

    Args:
        verts_u: 1D array of U coordinates for all vertices.
        verts_v: 1D array of V coordinates for all vertices.
        faces: (N, 3) array of face indices into verts_u/verts_v.
        u_min, u_max: U-axis range to map into image columns.
        v_min, v_max: V-axis range to map into image rows.
        res_u: Image width in pixels.
        res_v: Image height in pixels.

    Returns:
        Boolean numpy array of shape (res_v, res_u). True = geometry present.
    """
    img = Image.new('L', (res_u, res_v), 0)
    draw = ImageDraw.Draw(img)

    u_range = u_max - u_min
    v_range = v_max - v_min

    # Avoid division by zero
    if u_range <= 0 or v_range <= 0:
        return np.zeros((res_v, res_u), dtype=bool)

    for face in faces:
        poly = []
        for vi in face:
            # Map U to pixel column [0, res_u - 1]
            px = (verts_u[vi] - u_min) / u_range * (res_u - 1)
            # Map V to pixel row — flip so high V -> row 0
            py = (1.0 - (verts_v[vi] - v_min) / v_range) * (res_v - 1)
            poly.append((px, py))
        draw.polygon(poly, fill=255)

    return np.array(img) > 0


# ── 5. Coverage analysis ───────────────────────────────────────────────────

def analyze_coverage(raster, cells, floor_exclude, ceiling_exclude,
                     side_exclude=0.15):
    """Compute coverage ratio in the passage zone for each cell segment.

    The raster image has row 0 at the top (ceiling) and row (h-1) at the
    bottom (floor). Excludes ceiling_exclude fraction from the top and
    floor_exclude fraction from the bottom.

    The image is divided horizontally into `cells` equal-width segments
    (left to right). Within each segment, the outer side_exclude fraction
    is excluded from each side to remove door-frame/trim geometry.

    Args:
        raster: Boolean array of shape (height, width).
        cells: Number of horizontal segments to analyze.
        floor_exclude: Fraction of image height to exclude from bottom (floor).
        ceiling_exclude: Fraction of image height to exclude from top (ceiling).
        side_exclude: Fraction of cell width to exclude from each side.
            Removes trim/frame geometry at cell edges. Default 0.15.

    Returns:
        List of float coverage ratios, one per cell. Each ratio is in [0.0, 1.0].
    """
    h, w = raster.shape

    # Compute row boundaries for passage zone
    top_row = int(round(h * ceiling_exclude))
    bottom_row = int(round(h * (1.0 - floor_exclude)))

    # Clamp
    top_row = max(0, min(top_row, h))
    bottom_row = max(top_row, min(bottom_row, h))

    passage = raster[top_row:bottom_row, :]
    ph, pw = passage.shape

    if ph == 0 or pw == 0:
        return [0.0] * cells

    coverages = []
    for i in range(cells):
        cell_start = int(round(i * pw / cells))
        cell_end = int(round((i + 1) * pw / cells))
        cell_end = max(cell_start + 1, cell_end)
        cell_end = min(cell_end, pw)
        cell_width = cell_end - cell_start

        # Narrow within cell to exclude side trim
        side_px = int(round(cell_width * side_exclude))
        col_start = cell_start + side_px
        col_end = cell_end - side_px
        if col_start >= col_end:
            col_start = cell_start
            col_end = cell_end

        segment = passage[:, col_start:col_end]
        total_pixels = segment.size
        if total_pixels == 0:
            coverages.append(0.0)
        else:
            coverages.append(float(segment.sum()) / total_pixels)

    return coverages


# ── 6. Coverage classification ──────────────────────────────────────────────

def classify_coverage(coverage):
    """Classify a single coverage value into open, closed, or uncertain.

    Args:
        coverage: Float coverage ratio in [0.0, 1.0].

    Returns:
        Tuple of (state, method) where:
            state: "open", "closed", or "uncertain"
            method: always "slab_analysis"
    """
    if coverage < OPEN_THRESHOLD:
        return ("open", "slab_analysis")
    elif coverage > CLOSED_THRESHOLD:
        return ("closed", "slab_analysis")
    else:
        return ("uncertain", "needs_review")


# ── 7. Piece type derivation ───────────────────────────────────────────────

def derive_piece_type(edges):
    """Derive the modular piece type from classified edges.

    Counts open faces and their arrangement to determine type.

    Args:
        edges: Dict with keys "+x", "-x", "+z", "-z", each mapping to
               a string "open" or "closed".

    Returns:
        String piece type: "straight", "corner", "t_junction",
        "intersection", "end_cap", or "enclosed".
    """
    open_faces = [face for face in ["+z", "+x", "-z", "-x"]
                  if edges.get(face) == "open"]
    n_open = len(open_faces)

    if n_open == 0:
        return "enclosed"
    elif n_open == 1:
        return "end_cap"
    elif n_open == 4:
        return "intersection"
    elif n_open == 3:
        return "t_junction"
    elif n_open == 2:
        # Check if the two open faces are opposite or adjacent
        opposites = [{"+z", "-z"}, {"+x", "-x"}]
        open_set = set(open_faces)
        if open_set in opposites:
            return "straight"
        else:
            return "corner"

    # Fallback (shouldn't happen with 4 faces)
    return "enclosed"


# ── 8. Default rotation derivation ─────────────────────────────────────────

def derive_default_rotation(edges, piece_type):
    """Derive how many 90-degree rotation steps to reach canonical orientation.

    Canonical orientations (when rotation = 0):
        - straight:     open on +Z and -Z
        - corner:       open on -X and +Z
        - t_junction:   open on -X, +Z, -Z
        - end_cap:      open on -Z
        - intersection: always 0 (symmetric)
        - enclosed:     always 0 (symmetric)

    Uses EDGE_ORDER = ["+z", "+x", "-z", "-x"] for rotation.
    Rotation step N means the piece is rotated N * 90 degrees clockwise
    from canonical.

    Args:
        edges: Dict with keys "+x", "-x", "+z", "-z", each mapping to
               "open" or "closed".
        piece_type: String from derive_piece_type().

    Returns:
        Integer 0-3 rotation steps from canonical to current orientation.
    """
    if piece_type in ("intersection", "enclosed"):
        return 0

    # Build a binary pattern from EDGE_ORDER: 1 = open, 0 = closed
    def pattern_from_edges(e):
        return tuple(1 if e.get(face) == "open" else 0 for face in EDGE_ORDER)

    actual = pattern_from_edges(edges)

    # Define canonical patterns
    canonical_patterns = {
        # EDGE_ORDER = ["+z", "+x", "-z", "-x"]
        "straight":    (1, 0, 1, 0),   # open +Z, -Z
        "corner":      (1, 0, 0, 1),   # open +Z, -X
        "t_junction":  (1, 0, 1, 1),   # open +Z, -Z, -X
        "end_cap":     (0, 0, 1, 0),   # open -Z
    }

    canonical = canonical_patterns.get(piece_type)
    if canonical is None:
        return 0

    # Try rotating canonical by 0-3 steps to match actual
    for rot in range(4):
        # Rotate canonical pattern by rot steps
        rotated = tuple(canonical[(i - rot) % 4] for i in range(4))
        if rotated == actual:
            return rot

    # No match found (shouldn't happen if piece_type is correct)
    return 0


# ── 9. Edge simplification helper ─────────────────────────────────────────

def _simplify_edges(edges):
    """Convert array-format edges to simple format for type/rotation derivation.

    classify_piece produces edges as arrays: {"+z": ["open"], "-z": ["closed"], ...}
    but derive_piece_type and derive_default_rotation expect flat strings:
    {"+z": "open", "-z": "closed", ...}

    We pick "open" if any cell is open, otherwise "closed".

    Args:
        edges: Dict mapping face names to lists of state strings.

    Returns:
        Dict mapping face names to a single state string ("open" or "closed").
    """
    return {face: "open" if "open" in states else "closed"
            for face, states in edges.items()}


# ── 10. Main classification function ──────────────────────────────────────

def classify_piece(mesh, grid_size, level_height):
    """Classify a single modular piece.

    Analyzes each cardinal face (+X, -X, +Z, -Z) to determine whether
    it is open, closed, or uncertain. Derives piece type and default
    rotation from the edge pattern.

    Args:
        mesh: trimesh.Trimesh object.
        grid_size: [x, z] grid cell dimensions.
        level_height: Vertical height per level.

    Returns:
        Dict with "modular" key containing edges, coverage, piece_type, etc.
        Or dict with "skip": True for floor tiles (height < 0.5m).
        Also includes "slab_rasters" key with per-face boolean arrays for diagnostics.
    """
    bounds = mesh.bounds  # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
    height = bounds[1][1] - bounds[0][1]
    width = bounds[1][0] - bounds[0][0]
    depth = bounds[1][2] - bounds[0][2]

    # Skip floor tiles (height < 0.5m)
    if height < 0.5:
        return {"skip": True, "reason": "floor_tile", "height": float(height)}

    # Compute grid footprint
    cells_x = max(1, round(width / grid_size[0]))
    cells_z = max(1, round(depth / grid_size[1]))

    edges = {}
    coverage_map = {}
    methods = {}
    slab_rasters = {}
    needs_review = False

    # Face definitions: (face_name, axis, direction, perp_cells)
    face_defs = [
        ("+x", 0, +1, cells_z),
        ("-x", 0, -1, cells_z),
        ("+z", 2, +1, cells_x),
        ("-z", 2, -1, cells_x),
    ]

    for face_name, axis, direction, perp_cells in face_defs:
        # Determine grid dimension along this axis
        grid_dim = grid_size[0] if axis == 0 else grid_size[1]
        slab_thickness = SLAB_PERCENT * grid_dim

        # Compute slab boundaries
        if direction > 0:
            slab_min = bounds[1][axis] - slab_thickness
            slab_max = bounds[1][axis]
        else:
            slab_min = bounds[0][axis]
            slab_max = bounds[0][axis] + slab_thickness

        # Filter triangles in slab
        verts, faces = get_slab_triangles(mesh, axis, slab_min, slab_max,
                                                 normal_axis=axis)

        if verts is None:
            # No triangles in slab -> all cells are open
            edges[face_name] = ["open"] * perp_cells
            coverage_map[face_name] = [0.0] * perp_cells
            methods[face_name] = ["slab_analysis"] * perp_cells
            slab_rasters[face_name] = None
            continue

        # Project to 2D
        u_coords, v_coords = project_to_2d(verts, face_axis=axis)

        # Determine 2D bounds
        if axis == 0:
            # X face: u from Z range, v from Y range
            u_min_val = bounds[0][2]
            u_max_val = bounds[1][2]
        else:
            # Z face: u from X range, v from Y range
            u_min_val = bounds[0][0]
            u_max_val = bounds[1][0]
        v_min_val = bounds[0][1]
        v_max_val = bounds[1][1]

        # Compute raster resolution
        res_u = RENDER_RES * perp_cells
        v_range = v_max_val - v_min_val
        res_v = max(RENDER_RES, int(RENDER_RES * v_range / grid_dim))

        # Rasterize
        raster = rasterize_triangles(
            u_coords, v_coords, faces,
            u_min_val, u_max_val,
            v_min_val, v_max_val,
            res_u, res_v
        )

        slab_rasters[face_name] = raster

        # Analyze coverage
        coverages = analyze_coverage(raster, perp_cells, FLOOR_EXCLUDE, CEILING_EXCLUDE)

        # Classify each cell
        face_states = []
        face_methods = []
        for cov in coverages:
            state, method = classify_coverage(cov)
            face_states.append(state)
            face_methods.append(method)
            if state == "uncertain":
                needs_review = True

        edges[face_name] = face_states
        coverage_map[face_name] = coverages
        methods[face_name] = face_methods

    # Derive piece type and default rotation from simplified edges
    simple_edges = _simplify_edges(edges)
    piece_type = derive_piece_type(simple_edges)
    default_rotation = derive_default_rotation(simple_edges, piece_type)

    modular = {
        "edges": edges,
        "coverage": coverage_map,
        "methods": methods,
        "piece_type": piece_type,
        "default_rotation": default_rotation,
        "grid_footprint": [cells_x, cells_z],
        "needs_review": needs_review,
    }

    return {"modular": modular, "slab_rasters": slab_rasters}


# ── 11. Diagnostic image rendering ────────────────────────────────────────

def save_slab_render(raster, face_name, piece_key, coverage_val, state,
                     output_dir):
    """Save a single face's slab raster as a labeled diagnostic PNG.

    Args:
        raster: Boolean numpy array (res_v, res_u) or None.
        face_name: Face identifier, e.g. "+x", "-z".
        piece_key: Catalog key for the piece (used in filename and label).
        coverage_val: Float coverage ratio for this face.
        state: Classification state string ("open", "closed", "uncertain").
        output_dir: Directory to save the PNG.

    Returns:
        Filename of the saved image (relative to output_dir).
    """
    os.makedirs(output_dir, exist_ok=True)

    # Sanitize face name for filename
    safe_face = face_name.replace("+", "pos_").replace("-", "neg_")
    filename = f"{piece_key}_{safe_face}.png"
    filepath = os.path.join(output_dir, filename)

    min_size = 256

    if raster is None:
        # Create a blank labeled image
        img = Image.new('RGB', (min_size, min_size), (30, 30, 30))
    else:
        h, w = raster.shape
        # Scale up for visibility
        scale_x = max(1, min_size // w)
        scale_y = max(1, min_size // h)
        scale = max(scale_x, scale_y)
        new_w = w * scale
        new_h = h * scale

        # Build RGB image from raster
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        rgb[raster] = [255, 255, 255]

        # Tint excluded floor/ceiling zones red
        ceil_row = int(round(h * CEILING_EXCLUDE))
        floor_row = int(round(h * (1.0 - FLOOR_EXCLUDE)))

        # Ceiling zone (top rows)
        for r in range(min(ceil_row, h)):
            for c in range(w):
                if raster[r, c]:
                    rgb[r, c] = [255, 100, 100]  # red-tinted white
                else:
                    rgb[r, c] = [60, 20, 20]  # dark red

        # Floor zone (bottom rows)
        for r in range(max(floor_row, 0), h):
            for c in range(w):
                if raster[r, c]:
                    rgb[r, c] = [255, 100, 100]
                else:
                    rgb[r, c] = [60, 20, 20]

        img = Image.fromarray(rgb)
        img = img.resize((new_w, new_h), Image.NEAREST)

    # Overlay text
    draw = ImageDraw.Draw(img)
    label = f"{piece_key} | {face_name} | cov={coverage_val:.2f} | {state}"
    draw.text((4, 4), label, fill=(255, 255, 0))

    img.save(filepath)
    return filename


# ── 12. Summary markdown generation ──────────────────────────────────────

def generate_summary(results, thumbnail_dir, diag_dir, output_path):
    """Generate a review markdown document for classified pieces.

    Args:
        results: Dict mapping piece_key -> classify_piece result.
        thumbnail_dir: Path to directory containing piece thumbnails.
        diag_dir: Path to directory containing diagnostic PNGs.
        output_path: Path to write the summary.md file.
    """
    lines = ["# Edge Classification Summary\n"]
    lines.append(f"Pieces analyzed: {len(results)}\n")

    skipped = {k: v for k, v in results.items() if v.get("skip")}
    classified = {k: v for k, v in results.items() if "modular" in v}

    if skipped:
        lines.append(f"\n## Skipped ({len(skipped)})\n")
        for key, result in sorted(skipped.items()):
            reason = result.get("reason", "unknown")
            lines.append(f"- **{key}**: {reason} (height={result.get('height', '?'):.2f}m)")
        lines.append("")

    lines.append(f"\n## Classified ({len(classified)})\n")

    for key in sorted(classified.keys()):
        mod = classified[key]["modular"]
        lines.append(f"### {key}\n")

        # Link to thumbnail if exists
        thumb_path = os.path.join(thumbnail_dir, f"{key}.png")
        if os.path.exists(thumb_path):
            rel_thumb = os.path.relpath(thumb_path, os.path.dirname(output_path))
            lines.append(f"![thumbnail]({rel_thumb})\n")

        # Piece info
        lines.append(f"- **Type**: {mod['piece_type']}")
        lines.append(f"- **Grid footprint**: {mod['grid_footprint']}")
        lines.append(f"- **Default rotation**: {mod['default_rotation']}")
        lines.append(f"- **Needs review**: {mod['needs_review']}")
        lines.append("")

        # Edge table
        lines.append("| Face | Edge(s) | Coverage | Method |")
        lines.append("|------|---------|----------|--------|")

        for face in EDGE_ORDER:
            edge_states = mod["edges"].get(face, [])
            coverages = mod["coverage"].get(face, [])
            face_methods = mod["methods"].get(face, [])

            edge_str = ", ".join(edge_states)
            cov_str = ", ".join(f"{c:.2f}" for c in coverages)
            method_str = ", ".join(face_methods)

            # Flag uncertain faces with diagnostic image link
            if "uncertain" in edge_states:
                safe_face = face.replace("+", "pos_").replace("-", "neg_")
                diag_file = f"{key}_{safe_face}.png"
                diag_path = os.path.join(diag_dir, diag_file)
                if os.path.exists(diag_path):
                    rel_diag = os.path.relpath(diag_path, os.path.dirname(output_path))
                    edge_str += f" [diag]({rel_diag})"

            lines.append(f"| {face} | {edge_str} | {cov_str} | {method_str} |")

        lines.append("")

        # Empty fields for AI review step
        lines.append("- **Name**: ")
        lines.append("- **Description**: ")
        lines.append("- **Category**: ")
        lines.append("")

    # Write
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("\n".join(lines))


# ── 13. CLI entrypoint ───────────────────────────────────────────────────

def main():
    """CLI entrypoint for modular edge classification.

    Usage:
        python3 tools/classify_modular_edges.py games/{room-id}/

    Options:
        --glb-dir       Override GLB directory (auto-detects glbs_fixed/, glbs/, or game dir)
        --slab-percent  Override SLAB_PERCENT (default: 0.15)
        --open-threshold Override OPEN_THRESHOLD (default: 0.20)
        --closed-threshold Override CLOSED_THRESHOLD (default: 0.70)
    """
    global SLAB_PERCENT, OPEN_THRESHOLD, CLOSED_THRESHOLD

    parser = argparse.ArgumentParser(
        description="Classify modular kit piece edges via slab-based rasterization."
    )
    parser.add_argument("game_dir", help="Path to game directory (e.g. games/{room-id}/)")
    parser.add_argument("--glb-dir", help="Override GLB directory")
    parser.add_argument("--slab-percent", type=float, default=SLAB_PERCENT,
                        help=f"Slab thickness as fraction of grid dim (default: {SLAB_PERCENT})")
    parser.add_argument("--open-threshold", type=float, default=OPEN_THRESHOLD,
                        help=f"Coverage below this = open (default: {OPEN_THRESHOLD})")
    parser.add_argument("--closed-threshold", type=float, default=CLOSED_THRESHOLD,
                        help=f"Coverage above this = closed (default: {CLOSED_THRESHOLD})")
    args = parser.parse_args()

    # Apply threshold overrides
    SLAB_PERCENT = args.slab_percent
    OPEN_THRESHOLD = args.open_threshold
    CLOSED_THRESHOLD = args.closed_threshold

    game_dir = args.game_dir

    # Load catalog.json
    catalog_path = os.path.join(game_dir, "catalog.json")
    if not os.path.exists(catalog_path):
        print(f"ERROR: No catalog.json found in {game_dir}")
        sys.exit(1)

    with open(catalog_path, 'r') as f:
        catalog = json.load(f)

    # Require modular_kit metadata
    kit_meta = catalog.get("modular_kit")
    if not kit_meta:
        print("ERROR: catalog.json has no 'modular_kit' metadata.")
        print("Expected: {\"modular_kit\": {\"grid_size\": [x, z], \"level_height\": h}}")
        sys.exit(1)

    grid_size = kit_meta.get("grid_size")
    level_height = kit_meta.get("level_height")
    if not grid_size or not level_height:
        print("ERROR: modular_kit must have 'grid_size' and 'level_height' fields.")
        sys.exit(1)

    print(f"Kit: grid_size={grid_size}, level_height={level_height}")

    # Auto-detect GLB directory
    if args.glb_dir:
        glb_dir = args.glb_dir
    else:
        candidates = [
            os.path.join(game_dir, "glbs_fixed"),
            os.path.join(game_dir, "glbs"),
            game_dir,
        ]
        glb_dir = None
        for candidate in candidates:
            if os.path.isdir(candidate):
                # Check if it contains GLBs
                glbs_in_dir = [f for f in os.listdir(candidate) if f.lower().endswith('.glb')]
                if glbs_in_dir:
                    glb_dir = candidate
                    break
        if not glb_dir:
            print("ERROR: No GLB directory found. Checked: glbs_fixed/, glbs/, game dir")
            sys.exit(1)

    print(f"GLB directory: {glb_dir}")

    # Set up output directories
    diag_dir = os.path.join(game_dir, "edge_diagnostics")
    thumbnail_dir = os.path.join(game_dir, "thumbnails")
    os.makedirs(diag_dir, exist_ok=True)

    # Process each catalog item
    items = catalog.get("items", {})
    results = {}
    coverage_dist = {"open": 0, "closed": 0, "uncertain": 0}

    for key, item in items.items():
        # Find GLB file
        cdn_url = item.get("cdn_url", "")
        # Use source_file from catalog (original filename), fall back to key
        glb_filename = item.get("source_file", f"{key}.glb")
        glb_path = os.path.join(glb_dir, glb_filename)

        if not os.path.exists(glb_path):
            # Try matching by original filename from URL
            if cdn_url:
                url_filename = cdn_url.split("/")[-1]
                glb_path = os.path.join(glb_dir, url_filename)

        if not os.path.exists(glb_path):
            # Try case-insensitive search
            found = False
            for f in os.listdir(glb_dir):
                if f.lower() == glb_filename.lower():
                    glb_path = os.path.join(glb_dir, f)
                    found = True
                    break
            if not found:
                print(f"  SKIP {key}: GLB not found")
                continue

        print(f"  Processing {key}...")

        try:
            mesh = load_mesh(glb_path)
            result = classify_piece(mesh, grid_size, level_height)
            results[key] = result

            if result.get("skip"):
                print(f"    Skipped: {result.get('reason', 'unknown')}")
                continue

            mod = result["modular"]
            print(f"    Type: {mod['piece_type']}, "
                  f"Footprint: {mod['grid_footprint']}, "
                  f"Review: {mod['needs_review']}")

            # Save diagnostic images
            slab_rasters = result.get("slab_rasters", {})
            for face_name in EDGE_ORDER:
                raster = slab_rasters.get(face_name)
                coverages = mod["coverage"].get(face_name, [0.0])
                states = mod["edges"].get(face_name, ["unknown"])

                # Use average coverage for the diagnostic label
                avg_cov = sum(coverages) / len(coverages) if coverages else 0.0
                primary_state = states[0] if states else "unknown"

                save_slab_render(raster, face_name, key, avg_cov, primary_state,
                                 diag_dir)

            # Track coverage distribution
            for face_name, states in mod["edges"].items():
                for state in states:
                    if state in coverage_dist:
                        coverage_dist[state] += 1

            # Update catalog item with modular data
            item["modular"] = {
                "edges": mod["edges"],
                "piece_type": mod["piece_type"],
                "default_rotation": mod["default_rotation"],
                "grid_footprint": mod["grid_footprint"],
                "needs_review": mod["needs_review"],
            }

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    # Save updated catalog
    with open(catalog_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    print(f"\nUpdated catalog: {catalog_path}")

    # Generate summary
    summary_path = os.path.join(diag_dir, "summary.md")
    generate_summary(results, thumbnail_dir, diag_dir, summary_path)
    print(f"Generated summary: {summary_path}")

    # Print coverage distribution
    total_faces = sum(coverage_dist.values())
    print(f"\nCoverage distribution ({total_faces} faces):")
    for state in ["open", "closed", "uncertain"]:
        count = coverage_dist[state]
        pct = (count / total_faces * 100) if total_faces > 0 else 0
        print(f"  {state}: {count} ({pct:.1f}%)")

    # Kit-level consistency warnings
    if classified_results := {k: v for k, v in results.items() if "modular" in v}:
        types = [v["modular"]["piece_type"] for v in classified_results.values()]
        footprints = [tuple(v["modular"]["grid_footprint"]) for v in classified_results.values()]

        unique_types = set(types)
        unique_footprints = set(footprints)

        if len(unique_footprints) > 3:
            print(f"\nWARNING: {len(unique_footprints)} different grid footprints detected.")
            print("  This may indicate inconsistent grid_size. Check catalog modular_kit settings.")

        if coverage_dist["uncertain"] > 0:
            pct = coverage_dist["uncertain"] / total_faces * 100
            print(f"\nWARNING: {coverage_dist['uncertain']} uncertain faces ({pct:.1f}%).")
            print("  Review edge_diagnostics/summary.md and adjust thresholds if needed.")

        print(f"\nPiece type distribution:")
        from collections import Counter
        for ptype, count in Counter(types).most_common():
            print(f"  {ptype}: {count}")


if __name__ == "__main__":
    main()
