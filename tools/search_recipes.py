#!/usr/bin/env python3
"""
Recipe Search Tool

Searches the recipe manifest for mechanics matching a query. Supports
multi-keyword scoring, tag + summary matching, and optional full content
output. Designed to be called by subagents to find relevant recipes in
one step instead of manual grep → read cycles.

Usage:
    python tools/search_recipes.py "capture the flag"
    python tools/search_recipes.py "score leaderboard points" --full
    python tools/search_recipes.py "timer countdown" --top 3 --category scoring
    python tools/search_recipes.py --list-categories

Tip: Check recipes/patterns.md for game-type-to-keyword mappings
     (e.g., "Capture the Flag" → "team, capture, score, respawn, flag")
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ============================================================================
# CONSTANTS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_RECIPES_DIR = PROJECT_ROOT / "recipes"
MANIFEST_FILENAME = "manifest.md"
TOP_DEFAULT = 5


# ============================================================================
# MANIFEST PARSING
# ============================================================================

def parse_manifest(manifest_path: Path) -> List[Dict[str, str]]:
    """
    Parse manifest.md table into a list of recipe dicts.

    Returns list of dicts with keys: name, category, tags, patterns, summary, path
    """
    if not manifest_path.exists():
        return []

    content = manifest_path.read_text(encoding="utf-8")
    entries = []

    for line in content.split("\n"):
        line = line.strip()
        # Skip non-table-row lines
        if not line.startswith("|") or line.startswith("| Recipe") or line.startswith("|---"):
            continue

        parts = [p.strip() for p in line.split("|")]
        # Split produces empty strings at start/end from leading/trailing |
        parts = [p for p in parts if p or parts.index(p) not in (0, len(parts) - 1)]
        parts = line.split("|")[1:-1]  # drop empty first/last from split
        parts = [p.strip() for p in parts]

        if len(parts) >= 6:
            entries.append({
                "name": parts[0],
                "category": parts[1],
                "tags": parts[2],
                "patterns": parts[3],
                "summary": parts[4],
                "path": parts[5],
            })

    return entries


# ============================================================================
# SCORING
# ============================================================================

def tokenize_query(query: str) -> List[str]:
    """Split query into lowercase search tokens, filtering noise words."""
    noise = {"a", "an", "the", "i", "want", "to", "make", "build", "create",
             "game", "with", "and", "or", "for", "in", "my", "me", "need"}
    tokens = re.findall(r"[a-z0-9]+", query.lower())
    return [t for t in tokens if t not in noise and len(t) > 1]


def score_entry(entry: Dict[str, str], tokens: List[str]) -> float:
    """
    Score a recipe entry against search tokens.

    Scoring:
    - Tag match: 3 points (tags are curated, high signal)
    - Name match: 2 points
    - Summary match: 1 point
    - Partial/substring matches: 0.5 points

    Returns total score (0 = no match).
    """
    score = 0.0
    searchable_tags = entry["tags"].lower()
    searchable_name = entry["name"].lower()
    searchable_summary = entry["summary"].lower()
    searchable_all = f"{searchable_tags} {searchable_name} {searchable_summary}"

    for token in tokens:
        # Exact word boundary matches (higher value)
        tag_words = set(re.findall(r"[a-z0-9]+", searchable_tags))
        name_words = set(re.findall(r"[a-z0-9]+", searchable_name))
        summary_words = set(re.findall(r"[a-z0-9]+", searchable_summary))

        if token in tag_words:
            score += 3.0
        elif token in name_words:
            score += 2.0
        elif token in summary_words:
            score += 1.0
        # Substring/partial match fallback
        elif token in searchable_all:
            score += 0.5

    return score


# ============================================================================
# SEARCH
# ============================================================================

def search_recipes(
    recipes_dir: Path,
    query: str,
    top_n: int = TOP_DEFAULT,
    include_content: bool = False,
    category: Optional[str] = None,
) -> str:
    """
    Search recipes and return formatted results.

    Returns a formatted string with matching recipes, sorted by relevance.
    """
    manifest_path = recipes_dir / MANIFEST_FILENAME
    entries = parse_manifest(manifest_path)

    if not entries:
        return "No recipes found. Run `python tools/build_recipe_manifest.py` to generate the manifest."

    # Apply category filter before scoring
    if category:
        cat_lower = category.lower()
        entries = [e for e in entries if e["category"].lower() == cat_lower]
        if not entries:
            all_cats = sorted(set(e["category"] for e in parse_manifest(manifest_path)))
            return (
                f"No recipes in category: {category!r}\n"
                f"Available categories: {', '.join(all_cats)}"
            )

    tokens = tokenize_query(query)
    if not tokens:
        return f"No search tokens extracted from query: {query!r}"

    # Score all entries
    scored = []
    for entry in entries:
        s = score_entry(entry, tokens)
        if s > 0:
            scored.append((s, entry))

    scored.sort(key=lambda x: -x[0])
    total_matches = len(scored)
    scored = scored[:top_n]

    if not scored:
        # No matches — actionable guidance
        categories = sorted(set(e["category"] for e in entries))
        all_tags = set()
        for e in entries:
            all_tags.update(t.strip() for t in e["tags"].split(","))
        tag_sample = ", ".join(sorted(all_tags)[:20])

        return (
            f"No recipes matched: {query!r}\n"
            f"Search tokens: {tokens}\n\n"
            f"Available categories: {', '.join(categories)}\n"
            f"Sample tags: {tag_sample}\n\n"
            f"Next steps:\n"
            f"  1. Check recipes/patterns.md for game-type-to-keyword mappings\n"
            f"  2. Try broader keywords or run: python tools/search_recipes.py --list-categories\n"
            f"  3. If no recipe exists, use recipes/patterns.md to build from compositional patterns"
        )

    # Format results
    lines = [f"Found {len(scored)} of {total_matches} match(es) for: {query!r}\n"]

    for rank, (score, entry) in enumerate(scored, 1):
        lines.append(f"{'─' * 60}")
        lines.append(f"{rank}. {entry['name']}  ({entry['category']})")
        lines.append(f"   Tags: {entry['tags']}")
        lines.append(f"   {entry['summary']}")
        lines.append(f"   Path: recipes/{entry['path']}")

        if include_content:
            recipe_path = recipes_dir / entry["path"]
            if recipe_path.exists():
                content = recipe_path.read_text(encoding="utf-8")
                lines.append(f"\n{'─' * 40} CONTENT {'─' * 40}")
                lines.append(content.rstrip())
                lines.append(f"{'─' * 60}")
            else:
                lines.append(f"   File not found: {recipe_path}")

    # Truncation guidance
    if total_matches > top_n:
        lines.append(f"\n{total_matches - top_n} more match(es) not shown. Use --top {total_matches} to see all.")

    lines.append("")
    return "\n".join(lines)


def list_categories(recipes_dir: Path) -> str:
    """List all categories with recipe counts."""
    manifest_path = recipes_dir / MANIFEST_FILENAME
    entries = parse_manifest(manifest_path)

    if not entries:
        return "No recipes found. Run `python tools/build_recipe_manifest.py` to generate the manifest."

    # Count by category
    cats: Dict[str, int] = {}
    for e in entries:
        cat = e["category"]
        cats[cat] = cats.get(cat, 0) + 1

    lines = [f"Recipe categories ({sum(cats.values())} total recipes):\n"]
    for cat in sorted(cats):
        lines.append(f"  {cat}: {cats[cat]} recipe(s)")

    # Also list all unique tags
    all_tags = set()
    for e in entries:
        all_tags.update(t.strip() for t in e["tags"].split(","))

    lines.append(f"\nAll tags ({len(all_tags)}):")
    for tag in sorted(all_tags):
        lines.append(f"  {tag}")

    lines.append("")
    return "\n".join(lines)


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Search game mechanic recipes by keyword.",
        epilog="Examples:\n"
               "  python tools/search_recipes.py 'capture the flag'\n"
               "  python tools/search_recipes.py 'score leaderboard' --full\n"
               "  python tools/search_recipes.py --list-categories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Search query — keywords, game type, or mechanic name",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Include full recipe file content in results",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=TOP_DEFAULT,
        help=f"Number of results to return (default: {TOP_DEFAULT})",
    )
    parser.add_argument(
        "--recipes-dir",
        type=Path,
        default=DEFAULT_RECIPES_DIR,
        help="Path to recipes directory",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter results to a specific category (e.g., combat, scoring, multiplayer)",
    )
    parser.add_argument(
        "--list-categories",
        action="store_true",
        help="List all categories and tags instead of searching",
    )
    args = parser.parse_args()

    recipes_dir = args.recipes_dir.resolve()

    if args.list_categories:
        print(list_categories(recipes_dir))
        return 0

    if not args.query:
        parser.print_help()
        return 1

    print(search_recipes(recipes_dir, args.query, args.top, args.full, args.category))
    return 0


if __name__ == "__main__":
    sys.exit(main())
