#!/usr/bin/env python3
"""
Merge an approved modular proposal into a catalog.json.

Usage:
    python merge_modular_proposal.py <catalog.json> <modular_proposal.json>
    python merge_modular_proposal.py <catalog.json> <modular_proposal.json> --dry-run
"""
import argparse
import json
import sys


def merge_proposal_into_catalog(catalog, proposal):
    """Merge modular proposal into catalog dict.

    Args:
        catalog: catalog dict (with "items")
        proposal: proposal dict from analyze_batch()

    Returns:
        Updated catalog dict with modular fields added.
    """
    if not proposal.get("detected"):
        return catalog

    catalog["modular_kit"] = {
        "grid_size": proposal["grid_size"],
        "level_height": proposal.get("level_height"),
        "precision": proposal.get("precision"),
        "kit_name": "",
        "piece_count": len(proposal.get("pieces", {})),
    }

    for key, piece in proposal.get("pieces", {}).items():
        if key not in catalog["items"]:
            continue

        catalog["items"][key]["modular"] = {
            "grid_footprint": piece["grid_footprint"],
            "piece_type": piece["proposed_type"],
            "edges": piece.get("proposed_edges", {}),
            "default_rotation": 0,
            "tags": [],
        }

    return catalog


def main():
    parser = argparse.ArgumentParser(
        description="Merge modular proposal into catalog"
    )
    parser.add_argument("catalog", help="Path to catalog.json")
    parser.add_argument("proposal", help="Path to modular_proposal.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print result without writing")
    args = parser.parse_args()

    with open(args.catalog) as f:
        catalog = json.load(f)
    with open(args.proposal) as f:
        proposal = json.load(f)

    result = merge_proposal_into_catalog(catalog, proposal)

    if args.dry_run:
        print(json.dumps(result, indent=2))
    else:
        with open(args.catalog, 'w') as f:
            json.dump(result, f, indent=2)
        kit = result.get("modular_kit", {})
        print(f"Merged {kit.get('piece_count', 0)} modular pieces into {args.catalog}")
        print(f"  Grid: {kit.get('grid_size')}, Precision: {kit.get('precision')}")


if __name__ == "__main__":
    main()
