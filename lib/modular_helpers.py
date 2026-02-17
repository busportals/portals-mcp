# lib/modular_helpers.py
"""
Modular kit placement helpers for Portals generation scripts.

Provides grid-aware placement, edge rotation, piece finding,
and layout validation for modular kit assembly.

Usage in generation scripts:
    from modular_helpers import ModularKit, rotated_edges, find_piece
"""
import math
import json
from typing import Dict, List, Optional, Tuple, Callable


EDGE_ORDER = ["+z", "+x", "-z", "-x"]


def rotated_edges(edges: Dict[str, List[str]], rot_steps: int) -> Dict[str, List[str]]:
    """Rotate an edge map by N 90-degree clockwise steps.

    Args:
        edges: {"+z": [...], "-z": [...], "+x": [...], "-x": [...]}
        rot_steps: 0-3 rotation steps (0, 90, 180, 270 degrees)

    Returns:
        New edge dict with rotated assignments.
        Arrays reverse on odd steps to account for mirror effect.
    """
    rot_steps = rot_steps % 4
    if rot_steps == 0:
        return {k: list(v) for k, v in edges.items()}

    rotated = {}
    for i, edge_name in enumerate(EDGE_ORDER):
        source = EDGE_ORDER[(i - rot_steps) % 4]
        arr = list(edges[source])
        if rot_steps % 2 == 1:
            arr = list(reversed(arr))
        rotated[edge_name] = arr
    return rotated


def find_piece(
    catalog_items: Dict,
    piece_type: Optional[str] = None,
    needs_open: Optional[Dict[str, bool]] = None,
    tags: Optional[List[str]] = None
) -> List[Tuple[str, int]]:
    """Find catalog pieces matching constraints.

    Searches all pieces at all 4 rotations to find matches.

    Args:
        catalog_items: dict of {key: entry} where entry has "modular" key
        piece_type: filter by piece_type string
        needs_open: dict like {"+z": True, "-x": True} — edges that must be open
        tags: list of tags that must all be present

    Returns:
        list of (key, rot_steps) tuples that satisfy all constraints.
    """
    results = []

    for key, entry in catalog_items.items():
        mod = entry.get("modular")
        if not mod:
            continue

        if piece_type and mod["piece_type"] != piece_type:
            continue

        if tags:
            entry_tags = set(mod.get("tags", []))
            if not all(t in entry_tags for t in tags):
                continue

        if needs_open:
            for rot in range(4):
                edges = rotated_edges(mod["edges"], rot)
                match = True
                for edge_name, must_open in needs_open.items():
                    if must_open and not all(e == "open" for e in edges.get(edge_name, [])):
                        match = False
                        break
                if match:
                    results.append((key, rot))
        else:
            results.append((key, 0))

    return results


class ModularKit:
    """Orchestrates grid-based placement of modular pieces.

    Args:
        grid_size: [x_size, z_size] in world units per grid cell
        level_height: vertical distance between levels
        catalog_items: optional dict of catalog entries for validation
    """

    def __init__(
        self,
        grid_size: List[float],
        level_height: float,
        catalog_items: Optional[Dict] = None
    ):
        self.grid_size = grid_size
        self.level_height = level_height
        self.catalog_items = catalog_items or {}
        self.place_fn: Optional[Callable] = None
        self._placed: List[Dict] = []

    def place_mod(
        self,
        key: str,
        gx: int,
        gz: int,
        rot_steps: int = 0,
        level: int = 0,
        scale: float = 1.0
    ) -> None:
        """Place a modular piece on the grid.

        Args:
            key: catalog key for the piece
            gx: grid X coordinate
            gz: grid Z coordinate
            rot_steps: 0-3 rotation steps (0, 90, 180, 270 degrees)
            level: vertical level (0 = ground)
            scale: uniform scale multiplier
        """
        x = gx * self.grid_size[0]
        z = gz * self.grid_size[1]
        y = level * self.level_height
        facing_deg = rot_steps * 90

        self._placed.append({
            "key": key,
            "gx": gx,
            "gz": gz,
            "rot_steps": rot_steps,
            "level": level,
        })

        if self.place_fn:
            self.place_fn(key, (x, y, z), facing_deg=facing_deg, scale=scale)

    def place_room(
        self,
        key: str,
        anchor_gx: int,
        anchor_gz: int,
        rot_steps: int = 0,
        level: int = 0,
        scale: float = 1.0
    ) -> None:
        """Place a multi-cell room. Anchor is the -X, -Z corner.

        Args:
            key: catalog key for the room piece
            anchor_gx: grid X of the -X, -Z corner
            anchor_gz: grid Z of the -X, -Z corner
            rot_steps: 0-3 rotation steps
            level: vertical level
            scale: uniform scale multiplier
        """
        mod = self.catalog_items.get(key, {}).get("modular", {})
        fp = mod.get("grid_footprint", [1, 1])

        cx = anchor_gx + fp[0] / 2.0
        cz = anchor_gz + fp[1] / 2.0

        x = cx * self.grid_size[0]
        z = cz * self.grid_size[1]
        y = level * self.level_height
        facing_deg = rot_steps * 90

        self._placed.append({
            "key": key,
            "gx": anchor_gx,
            "gz": anchor_gz,
            "rot_steps": rot_steps,
            "level": level,
            "footprint": fp,
        })

        if self.place_fn:
            self.place_fn(key, (x, y, z), facing_deg=facing_deg, scale=scale)

    def place_corridor_run(
        self,
        key: str,
        start_gx: int,
        start_gz: int,
        direction: str,
        length: int,
        level: int = 0,
        scale: float = 1.0
    ) -> None:
        """Place a straight run of corridor segments.

        Args:
            key: catalog key for the corridor piece
            start_gx: starting grid X
            start_gz: starting grid Z
            direction: "+x", "-x", "+z", or "-z"
            length: number of segments to place
            level: vertical level
            scale: uniform scale multiplier
        """
        dir_map = {
            "+x": (1, 0, 1),
            "-x": (-1, 0, 1),
            "+z": (0, 1, 0),
            "-z": (0, -1, 0),
        }
        dx, dz, rot = dir_map[direction]

        for i in range(length):
            gx = start_gx + i * dx
            gz = start_gz + i * dz
            self.place_mod(key, gx, gz, rot_steps=rot, level=level, scale=scale)

    def validate_layout(self) -> List[str]:
        """Check all placed modular pieces for issues.

        Detects:
            - Overlapping grid cells
            - Open edges with no neighboring piece

        Returns:
            List of warning strings. Empty list = no issues.
        """
        warnings = []
        occupied = {}

        # Check for overlaps
        for p in self._placed:
            fp = p.get("footprint", [1, 1])
            for dx in range(fp[0]):
                for dz in range(fp[1]):
                    cell = (p["gx"] + dx, p["gz"] + dz, p["level"])
                    if cell in occupied:
                        warnings.append(
                            f"Overlap at grid ({cell[0]}, {cell[1]}) level {cell[2]}: "
                            f"{occupied[cell]} and {p['key']}"
                        )
                    occupied[cell] = p["key"]

        # Check for open edges with no neighbor
        if self.catalog_items:
            for p in self._placed:
                mod = self.catalog_items.get(p["key"], {}).get("modular")
                if not mod:
                    continue
                edges = rotated_edges(mod["edges"], p["rot_steps"])
                fp = p.get("footprint", [1, 1])

                for edge_name, edge_arr in edges.items():
                    for i, state in enumerate(edge_arr):
                        if state != "open":
                            continue
                        if edge_name == "+z":
                            ncell = (p["gx"] + i, p["gz"] + fp[1], p["level"])
                        elif edge_name == "-z":
                            ncell = (p["gx"] + i, p["gz"] - 1, p["level"])
                        elif edge_name == "+x":
                            ncell = (p["gx"] + fp[0], p["gz"] + i, p["level"])
                        elif edge_name == "-x":
                            ncell = (p["gx"] - 1, p["gz"] + i, p["level"])

                        if ncell not in occupied:
                            warnings.append(
                                f"Open edge at grid ({p['gx']}, {p['gz']}) "
                                f"facing {edge_name}: no neighbor at "
                                f"({ncell[0]}, {ncell[1]})"
                            )

        return warnings
