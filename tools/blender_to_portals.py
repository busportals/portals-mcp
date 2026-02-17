"""
Blender-to-Portals exporter.

Runs inside Blender headless mode to export each visible mesh object as an
individual GLB file and produce a manifest.json that records every object's
Portals-coordinate transform.

Mesh instancing: objects that share the same Blender mesh datablock are
exported only once. All instances reference the same GLB file in the manifest,
each with their own world-space transform.

Usage:
    blender --background scene.blend --python tools/blender_to_portals.py -- /output/dir

Everything after the "--" separator in sys.argv belongs to this script.
The first (and only required) argument is the output directory.
"""

import sys
import os
import json
import re
import math

import bpy  # available inside Blender's Python environment


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    """Return arguments that appear after the '--' separator in sys.argv."""
    try:
        separator_index = sys.argv.index("--")
        return sys.argv[separator_index + 1:]
    except ValueError:
        return []


# ---------------------------------------------------------------------------
# Name sanitisation & deduplication
# ---------------------------------------------------------------------------

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9_\-]")


def sanitize_name(name: str) -> str:
    """Replace dots, spaces, and other non-filesystem-safe chars with underscores."""
    return _UNSAFE_CHARS.sub("_", name)


def deduplicate_names(names: list[str]) -> list[str]:
    """
    Given a list of sanitised names, append _2, _3 ... for any duplicates so
    every entry is unique.  Preserves order.
    """
    seen: dict[str, int] = {}
    result: list[str] = []
    for name in names:
        if name not in seen:
            seen[name] = 1
            result.append(name)
        else:
            seen[name] += 1
            unique = f"{name}_{seen[name]}"
            while unique in seen:
                seen[name] += 1
                unique = f"{name}_{seen[name]}"
            seen[unique] = 1
            result.append(unique)
    return result


# ---------------------------------------------------------------------------
# Coordinate conversion  (Blender Z-up RH  ->  Portals Y-up LH)
#
# Portals runs on Unity which uses Y-up LEFT-handed coordinates.
# The glTF exporter converts mesh vertices from Z-up RH to Y-up RH,
# and Unity's glTF importer then negates X to convert RH → LH.
# Our manifest transforms must match this full chain.
#
# Axis mapping:
#   Blender X  ->  Portals -X  (handedness flip)
#   Blender Y  ->  Portals -Z
#   Blender Z  ->  Portals Y   (up)
# ---------------------------------------------------------------------------

def blender_position_to_portals(loc) -> dict:
    """
    Blender (X, Y, Z) with Z-up RH  ->  Portals (X, Y, Z) with Y-up LH.
    Mapping: portal = (-blender_x, blender_z, -blender_y)
    """
    return {
        "x": round(-loc.x, 6),
        "y": round(loc.z, 6),
        "z": round(-loc.y, 6),
    }


def blender_rotation_to_portals(quat) -> dict:
    """
    Blender quaternion is WXYZ.  Portals stores XYZW dict.
    Axis remapping (Z-up RH -> Y-up LH, with handedness flip):
        portal.x =  blender_quat.x
        portal.y = -blender_quat.z
        portal.z =  blender_quat.y
        portal.w =  blender_quat.w
    """
    return {
        "x": round(quat.x, 6),
        "y": round(-quat.z, 6),
        "z": round(quat.y, 6),
        "w": round(quat.w, 6),
    }


def blender_scale_to_portals(scl) -> dict:
    """
    Scale with Y/Z swap to match axis remapping.
    portal = (blender_sx, blender_sz, blender_sy)
    """
    return {
        "x": round(scl.x, 6),
        "y": round(scl.z, 6),
        "z": round(scl.y, 6),
    }


# ---------------------------------------------------------------------------
# GLB export helpers
# ---------------------------------------------------------------------------

def has_geometry(obj) -> bool:
    """Return True if the mesh has at least one face or edge (not degenerate)."""
    mesh = obj.data
    if mesh is None:
        return False
    return len(mesh.polygons) > 0 or len(mesh.edges) > 0


def export_object_as_glb(obj, filepath: str) -> None:
    """
    Export a single object as a GLB file.

    Temporarily unparents the object and moves it to the world origin with
    identity rotation and unit scale so the exported GLB contains only the mesh
    at its local origin.  The original parent and transform are restored afterward.

    The unparent step is critical: if we just set matrix_world = Identity on a
    parented object, Blender adjusts matrix_local to the inverse of the parent
    transform.  The glTF exporter then bakes that inverse-parent into the GLB
    node, shifting the mesh.
    """
    from mathutils import Matrix

    # -- Save original state --
    original_matrix = obj.matrix_world.copy()
    original_parent = obj.parent
    original_parent_inverse = obj.matrix_parent_inverse.copy() if obj.parent else None

    # -- Clear parent (keeps world position by adjusting matrix_world) --
    if obj.parent:
        world_copy = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world_copy

    # -- Reset to origin (now safe — no parent to interfere) --
    obj.matrix_world = Matrix.Identity(4)

    # Force a dependency graph update so the export picks up the new transform.
    bpy.context.view_layer.update()

    # -- Select only this object --
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # -- Export --
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=True,
        export_format='GLB',
        export_apply=True,  # bake modifiers
    )

    # -- Restore original parent and transform --
    if original_parent:
        obj.parent = original_parent
        obj.matrix_parent_inverse = original_parent_inverse
    obj.matrix_world = original_matrix
    bpy.context.view_layer.update()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if not args:
        print("ERROR: No output directory provided.")
        print("Usage: blender --background scene.blend "
              "--python blender_to_portals.py -- /output/dir")
        sys.exit(1)

    output_dir = args[0]
    os.makedirs(output_dir, exist_ok=True)

    # Determine source filename for the manifest.
    blend_path = bpy.data.filepath
    source_name = os.path.basename(blend_path) if blend_path else "unknown.blend"

    # -- Collect visible mesh objects --
    eligible = [
        obj for obj in bpy.context.scene.objects
        if obj.type == 'MESH' and obj.visible_get()
    ]

    # Filter out degenerate meshes.
    objects_to_export = []
    for obj in eligible:
        if has_geometry(obj):
            objects_to_export.append(obj)
        else:
            print(f"  Skipping '{obj.name}' — zero-area / degenerate mesh")

    total = len(objects_to_export)
    print(f"Found {total} visible mesh object(s) to export from '{source_name}'.")

    if total == 0:
        manifest = {
            "source": source_name,
            "object_count": 0,
            "unique_meshes": 0,
            "objects": [],
        }
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"Wrote empty manifest to {manifest_path}")
        return

    # -- Group objects by shared mesh datablock --
    # Objects sharing the same obj.data are identical meshes (linked duplicates).
    # We only need to export one GLB per unique mesh.
    mesh_groups: dict[str, list] = {}  # mesh.name -> [obj, ...]
    for obj in objects_to_export:
        mesh_name = obj.data.name
        if mesh_name not in mesh_groups:
            mesh_groups[mesh_name] = []
        mesh_groups[mesh_name].append(obj)

    unique_count = len(mesh_groups)
    instance_count = total - unique_count
    print(f"Unique meshes: {unique_count}, instanced copies: {instance_count}")

    # -- Export one GLB per unique mesh --
    # Map mesh.name -> sanitised GLB filename
    mesh_to_glb: dict[str, str] = {}
    glb_names_used: dict[str, int] = {}  # for deduplication of filenames

    export_idx = 0
    for mesh_name, objs in mesh_groups.items():
        export_idx += 1
        # Use the mesh datablock name for the GLB filename
        safe_name = sanitize_name(mesh_name)

        # Deduplicate filenames
        if safe_name not in glb_names_used:
            glb_names_used[safe_name] = 1
        else:
            glb_names_used[safe_name] += 1
            safe_name = f"{safe_name}_{glb_names_used[safe_name]}"
            glb_names_used[safe_name] = 1

        glb_filename = f"{safe_name}.glb"
        glb_path = os.path.join(output_dir, glb_filename)
        mesh_to_glb[mesh_name] = glb_filename

        # Export using the first object in the group as the representative
        representative = objs[0]
        count_str = f" ({len(objs)} instances)" if len(objs) > 1 else ""
        print(f"Exporting {glb_filename}{count_str} ({export_idx}/{unique_count})...")
        export_object_as_glb(representative, glb_path)

    # -- Build manifest entries for ALL objects --
    manifest_objects: list[dict] = []

    for obj in objects_to_export:
        loc, rot, scl = obj.matrix_world.decompose()
        glb_filename = mesh_to_glb[obj.data.name]

        # Compute bounding box in Blender local space, then convert to GLB Y-up.
        # The GLB is exported at Identity, so the bbox matches the raw mesh data
        # after the glTF exporter's Z-up → Y-up conversion.
        bbox = obj.bound_box  # 8 corners in local space
        bl_min = [min(v[i] for v in bbox) for i in range(3)]
        bl_max = [max(v[i] for v in bbox) for i in range(3)]

        # Z-up → Y-up: (bx, by, bz) → (bx, bz, -by)
        glb_min = [bl_min[0], bl_min[2], -bl_max[1]]
        glb_max = [bl_max[0], bl_max[2], -bl_min[1]]
        glb_center = [round((glb_min[i] + glb_max[i]) / 2.0, 6) for i in range(3)]
        glb_size = [round(glb_max[i] - glb_min[i], 6) for i in range(3)]

        manifest_objects.append({
            "name": sanitize_name(obj.name),
            "glb_file": glb_filename,
            "position": blender_position_to_portals(loc),
            "rotation": blender_rotation_to_portals(rot),
            "scale": blender_scale_to_portals(scl),
            "glb_bbox_center": {"x": glb_center[0], "y": glb_center[1], "z": glb_center[2]},
            "glb_bbox_size": {"x": glb_size[0], "y": glb_size[1], "z": glb_size[2]},
        })

    # -- Write manifest --
    manifest = {
        "source": source_name,
        "object_count": total,
        "unique_meshes": unique_count,
        "objects": manifest_objects,
    }

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Done. {total} object(s), {unique_count} unique GLB(s) exported to {output_dir}")
    print(f"Manifest written to {manifest_path}")

    # --- Storage check on exported unique GLBs ---
    total_bytes = 0
    file_sizes = []
    for glb_filename in mesh_to_glb.values():
        glb_path = os.path.join(output_dir, glb_filename)
        if os.path.exists(glb_path):
            size = os.path.getsize(glb_path)
            total_bytes += size
            file_sizes.append((glb_filename, size))

    mb = total_bytes / (1024 * 1024)
    print(f"\nUnique GLB storage: {mb:.1f} MB ({unique_count} files)")
    if total_bytes > 500 * 1024 * 1024:
        print("CRITICAL: Over 500 MB — room may not load properly in the browser.")
        print("  Reduce mesh complexity, combine small meshes, or remove unused objects.")
    elif total_bytes > 200 * 1024 * 1024:
        print("WARNING: Over 200 MB — room is heavy and may have slow load times.")
        print("  Consider optimizing large meshes or reducing texture sizes.")
    else:
        print("OK — within recommended size limits.")

    # Show top 5 largest files if over warning threshold
    if total_bytes > 200 * 1024 * 1024 and file_sizes:
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        print("\nLargest GLBs:")
        for name, size in file_sizes[:5]:
            print(f"  {size / (1024*1024):.1f} MB  {name}")


if __name__ == "__main__":
    main()
