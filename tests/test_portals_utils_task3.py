#!/usr/bin/env python3
"""
Verification tests for Task 3: portals_utils.py changes.

Tests:
- merge_logic_into_items()
- split_logic_from_items()
- normalize_snapshot()
- _count_types_in_logic()
- generate_build_summary() with separate logic dict
- validate_room_data() with new format support
"""

import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "lib"))

from portals_utils import (
    merge_logic_into_items,
    split_logic_from_items,
    normalize_snapshot,
    _count_types_in_logic,
    generate_build_summary,
    validate_room_data,
    format_extra_data,
    parse_extra_data,
)


def test_merge_logic_into_items():
    """merge_logic_into_items embeds logic dicts as extraData strings."""
    print("TEST: merge_logic_into_items")

    logic_dict = {"Tasks": [{"$type": "TaskTriggerSubscription"}]}
    data = {
        "roomItems": {
            "1": {"prefabName": "GLB", "pos": {"x": 0, "y": 0, "z": 0}},
            "2": {"prefabName": "Trigger", "pos": {"x": 1, "y": 0, "z": 0}},
        },
        "logic": {
            "1": logic_dict,
        },
    }

    result = merge_logic_into_items(data)

    # logic key should be removed
    assert "logic" not in result, "logic key should be popped from data"

    # Item 1 should have extraData as a JSON string
    ed = result["roomItems"]["1"]["extraData"]
    assert isinstance(ed, str), f"extraData should be a string, got {type(ed)}"
    parsed = json.loads(ed)
    assert parsed == logic_dict, f"Parsed extraData should match logic dict: {parsed}"

    # Item 2 should NOT have extraData (no logic entry for it)
    assert "extraData" not in result["roomItems"]["2"], "Item 2 should not have extraData"

    # Test with logic entry that's already a string
    data2 = {
        "roomItems": {"3": {"prefabName": "GLB"}},
        "logic": {"3": '{"Tasks":[]}'},
    }
    result2 = merge_logic_into_items(data2)
    assert result2["roomItems"]["3"]["extraData"] == '{"Tasks":[]}', "String logic entry should be passed through"

    # Test with logic entry referencing non-existent item
    data3 = {
        "roomItems": {"4": {"prefabName": "GLB"}},
        "logic": {"999": {"Tasks": []}},
    }
    result3 = merge_logic_into_items(data3)
    assert "extraData" not in result3["roomItems"]["4"], "Non-matching logic should be ignored"

    print("  PASS")


def test_split_logic_from_items():
    """split_logic_from_items extracts extraData into separate logic dict."""
    print("TEST: split_logic_from_items")

    logic_dict = {"Tasks": [{"$type": "TaskTriggerSubscription"}]}
    data = {
        "roomItems": {
            "1": {"prefabName": "GLB", "extraData": json.dumps(logic_dict)},
            "2": {"prefabName": "Trigger"},  # no extraData
            "3": {"prefabName": "Light", "extraData": ""},  # empty string
        },
    }

    result = split_logic_from_items(data)

    # Item 1: extraData removed, logic entry created
    assert "extraData" not in result["roomItems"]["1"], "extraData should be removed from item 1"
    assert "1" in result["logic"], "Logic entry should exist for item 1"
    assert result["logic"]["1"] == logic_dict, f"Logic should match: {result['logic']['1']}"

    # Item 2: no extraData, no logic
    assert "2" not in result["logic"], "Item 2 should not have logic entry"

    # Item 3: empty extraData string, no logic
    assert "3" not in result["logic"], "Item 3 (empty string) should not have logic entry"
    assert "extraData" not in result["roomItems"]["3"], "Empty extraData should be removed"

    # Test with extraData that's already a dict (edge case)
    data2 = {
        "roomItems": {
            "5": {"prefabName": "GLB", "extraData": {"Tasks": []}},
        },
    }
    result2 = split_logic_from_items(data2)
    assert result2["logic"]["5"] == {"Tasks": []}, "Dict extraData should pass through"

    # Test preserves existing logic entries
    data3 = {
        "roomItems": {
            "6": {"prefabName": "GLB", "extraData": '{"Tasks":[]}'},
        },
        "logic": {
            "7": {"Tasks": [{"$type": "OnClickEvent"}]},
        },
    }
    result3 = split_logic_from_items(data3)
    assert "6" in result3["logic"], "New logic from extraData should be added"
    assert "7" in result3["logic"], "Existing logic entries should be preserved"

    print("  PASS")


def test_normalize_snapshot():
    """normalize_snapshot handles both new and legacy formats."""
    print("TEST: normalize_snapshot")

    # New format (has logic key) -> merges into items
    logic_dict = {"Tasks": []}
    data_new = {
        "roomItems": {"1": {"prefabName": "GLB"}},
        "logic": {"1": logic_dict},
    }
    result = normalize_snapshot(data_new)
    assert "logic" not in result, "logic key should be removed after normalize"
    assert "extraData" in result["roomItems"]["1"], "extraData should be embedded"
    assert json.loads(result["roomItems"]["1"]["extraData"]) == logic_dict

    # Legacy format (no logic key, items already have extraData) -> no change
    data_legacy = {
        "roomItems": {"1": {"prefabName": "GLB", "extraData": '{"Tasks":[]}'}},
    }
    result2 = normalize_snapshot(data_legacy)
    assert result2["roomItems"]["1"]["extraData"] == '{"Tasks":[]}', "Legacy format should be unchanged"

    # Empty logic dict -> still gets removed
    data_empty_logic = {
        "roomItems": {"1": {"prefabName": "GLB"}},
        "logic": {},
    }
    result3 = normalize_snapshot(data_empty_logic)
    assert "logic" not in result3, "Empty logic dict should still be removed"

    print("  PASS")


def test_count_types_in_logic():
    """_count_types_in_logic counts types from plain dicts."""
    print("TEST: _count_types_in_logic")

    # Logic entry with triggers, audio, visual effects
    logic_entry = {
        "Tasks": [
            {
                "$type": "TaskTriggerSubscription",
                "Trigger": {"$type": "OnClickEvent"},
                "DirectEffector": {
                    "Effector": {"$type": "PlaySoundOnce", "Url": "http://example.com/sound.mp3"},
                },
            },
            {
                "$type": "TaskTriggerSubscription",
                "Trigger": {"$type": "OnCollideEvent"},
                "DirectEffector": {
                    "Effector": {"$type": "ShowObjectEvent"},
                },
            },
        ]
    }
    counts = _count_types_in_logic(logic_entry)
    assert counts["triggers"] == 2, f"Expected 2 triggers, got {counts['triggers']}"
    assert counts["audio"] == 1, f"Expected 1 audio, got {counts['audio']}"
    assert counts["visual"] == 1, f"Expected 1 visual, got {counts['visual']}"
    assert counts["camera"] == 0, f"Expected 0 camera, got {counts['camera']}"

    # Empty dict
    counts_empty = _count_types_in_logic({})
    assert all(v == 0 for v in counts_empty.values()), "Empty dict should have all zeros"

    # None-like falsy value
    counts_none = _count_types_in_logic(None)
    assert all(v == 0 for v in counts_none.values()), "None should have all zeros"

    # Camera effects
    logic_camera = {
        "Tasks": [
            {
                "$type": "TaskTriggerSubscription",
                "Trigger": {"$type": "OnEnterEvent"},
                "DirectEffector": {
                    "Effector": {"$type": "SetCameraFilter", "url": "filter.png"},
                },
            }
        ]
    }
    counts_cam = _count_types_in_logic(logic_camera)
    assert counts_cam["camera"] == 1, f"Expected 1 camera, got {counts_cam['camera']}"
    assert counts_cam["triggers"] == 1, f"Expected 1 trigger (OnEnterEvent), got {counts_cam['triggers']}"

    print("  PASS")


def test_generate_build_summary():
    """generate_build_summary works with separate logic dict."""
    print("TEST: generate_build_summary")

    items = {
        "1": {"prefabName": "GLB", "position": {"x": 0, "y": 0, "z": 0}},
        "2": {"prefabName": "Trigger", "position": {"x": 5, "y": 0, "z": 5}},
        "3": {"prefabName": "Light", "position": {"x": -2, "y": 3, "z": -2}},
    }

    logic = {
        "2": {
            "Tasks": [
                {
                    "$type": "TaskTriggerSubscription",
                    "Trigger": {"$type": "OnEnterEvent"},
                    "DirectEffector": {
                        "Effector": {"$type": "PlaySoundOnce", "Url": "http://example.com/sound.mp3"},
                    },
                }
            ]
        },
        "3": {
            "Tasks": [
                {
                    "$type": "TaskTriggerSubscription",
                    "Trigger": {"$type": "OnClickEvent"},
                    "DirectEffector": {
                        "Effector": {"$type": "PlaySoundInALoop", "Url": "http://example.com/ambient.mp3"},
                    },
                }
            ]
        },
    }

    quests = {}

    summary = generate_build_summary("Test Game", items, logic, quests)
    assert "BUILD SUMMARY" in summary
    assert "Test Game" in summary
    assert "Total Items: 3" in summary
    assert "OnEnter:" in summary or "OnClick:" in summary, f"Should have trigger counts in summary"
    assert "Ambient loops: 1" in summary, f"Should find 1 ambient loop, got: {summary}"
    assert "One-shot sounds: 1" in summary, f"Should find 1 one-shot, got: {summary}"

    # Test with zones
    zones = {
        "main": (float('-inf'), float('inf'), float('-inf'), float('inf')),
    }
    summary_zoned = generate_build_summary("Test Game", items, logic, quests, zones=zones)
    assert "main(3)" in summary_zoned, f"All items should be in main zone"
    assert "Detail Layers:" in summary_zoned

    # Test with spectacle moments
    spectacle = ["Epic finale explosion"]
    summary_spec = generate_build_summary("Test Game", items, logic, quests, spectacle_moments=spectacle)
    assert "Spectacle Moments: 1" in summary_spec
    assert "Epic finale explosion" in summary_spec

    # Test with empty logic
    summary_empty = generate_build_summary("Empty Game", items, {}, quests)
    assert "Total Items: 3" in summary_empty
    assert "(no item-level triggers found" in summary_empty

    print("  PASS")


def test_validate_room_data_new_format():
    """validate_room_data accepts roomItems key and validates logic entries."""
    print("TEST: validate_room_data (new format)")

    # Valid new format with roomItems and logic
    data = {
        "roomItems": {
            "1": {"prefabName": "GLB"},
            "2": {"prefabName": "Trigger"},
        },
        "logic": {
            "1": {"Tasks": []},
            "2": {"Tasks": [{"$type": "TaskTriggerSubscription"}]},
        },
    }
    errors = validate_room_data(data)
    assert errors == [], f"Valid data should have no errors, got: {errors}"

    # roomItems with missing prefabName
    data_bad_item = {
        "roomItems": {
            "1": {"pos": {"x": 0, "y": 0, "z": 0}},
        },
    }
    errors = validate_room_data(data_bad_item)
    assert any("missing prefabName" in e for e in errors), f"Should flag missing prefabName: {errors}"

    # Invalid logic entry (not a dict)
    data_bad_logic = {
        "roomItems": {"1": {"prefabName": "GLB"}},
        "logic": {"1": "not a dict"},
    }
    errors = validate_room_data(data_bad_logic)
    assert any("Logic entry" in e and "must be a dict" in e for e in errors), f"Should flag non-dict logic: {errors}"

    # Logic itself is not a dict
    data_bad_logic_type = {
        "roomItems": {"1": {"prefabName": "GLB"}},
        "logic": "not a dict",
    }
    errors = validate_room_data(data_bad_logic_type)
    assert any("logic must be a dict" in e for e in errors), f"Should flag non-dict logic container: {errors}"

    print("  PASS")


def test_validate_room_data_legacy_format():
    """validate_room_data still accepts legacy 'items' key."""
    print("TEST: validate_room_data (legacy format)")

    data = {
        "items": {
            "1": {"prefabName": "GLB"},
        },
    }
    errors = validate_room_data(data)
    assert errors == [], f"Legacy format should be valid, got: {errors}"

    # Legacy with missing prefabName
    data_bad = {
        "items": {
            "1": {},
        },
    }
    errors = validate_room_data(data_bad)
    assert any("missing prefabName" in e for e in errors), f"Should flag missing prefabName in legacy: {errors}"

    print("  PASS")


def test_validate_room_data_roomItems_takes_precedence():
    """When both roomItems and items exist, roomItems is used."""
    print("TEST: validate_room_data (roomItems precedence)")

    data = {
        "roomItems": {
            "1": {"prefabName": "GLB"},
        },
        "items": {
            "2": {},  # invalid, but should not be checked
        },
    }
    errors = validate_room_data(data)
    assert errors == [], f"Should use roomItems (valid), not items: {errors}"

    print("  PASS")


def test_deprecation_notes():
    """format_extra_data and parse_extra_data still work and have deprecation notes."""
    print("TEST: deprecation notes")

    # Functions still work
    result = format_extra_data({"Tasks": []})
    assert result == '{"Tasks":[]}', f"format_extra_data should still work: {result}"

    parsed = parse_extra_data('{"Tasks":[]}')
    assert parsed == {"Tasks": []}, f"parse_extra_data should still work: {parsed}"

    # Docstrings have deprecation notes
    assert "DEPRECATED" in format_extra_data.__doc__, "format_extra_data should have deprecation note"
    assert "DEPRECATED" in parse_extra_data.__doc__, "parse_extra_data should have deprecation note"

    print("  PASS")


def test_roundtrip_merge_split():
    """merge_logic_into_items and split_logic_from_items are inverse operations."""
    print("TEST: roundtrip merge/split")

    logic_data = {
        "1": {"Tasks": [{"$type": "TaskTriggerSubscription", "Trigger": {"$type": "OnClickEvent"}}]},
        "2": {"keyCode": 0},
    }

    # Start with new format
    data = {
        "roomItems": {
            "1": {"prefabName": "GLB"},
            "2": {"prefabName": "Trigger"},
            "3": {"prefabName": "Light"},  # no logic
        },
        "logic": dict(logic_data),  # copy
    }

    # Merge -> items have extraData, no logic key
    import copy
    data_copy = copy.deepcopy(data)
    merge_logic_into_items(data_copy)
    assert "logic" not in data_copy
    assert "extraData" in data_copy["roomItems"]["1"]
    assert "extraData" in data_copy["roomItems"]["2"]

    # Split -> back to separate format
    split_logic_from_items(data_copy)
    assert "logic" in data_copy
    assert "1" in data_copy["logic"]
    assert "2" in data_copy["logic"]
    assert data_copy["logic"]["1"] == logic_data["1"], f"Logic 1 should roundtrip: {data_copy['logic']['1']}"
    assert data_copy["logic"]["2"] == logic_data["2"], f"Logic 2 should roundtrip: {data_copy['logic']['2']}"
    assert "extraData" not in data_copy["roomItems"]["1"]
    assert "extraData" not in data_copy["roomItems"]["2"]

    print("  PASS")


def test_generate_build_summary_zone_atmospheric():
    """Zone atmospheric detection uses logic for PlaySoundInALoop."""
    print("TEST: generate_build_summary zone atmospheric detection")

    items = {
        "1": {"prefabName": "GLB", "pos": {"x": 0, "y": 0, "z": 0}},
    }
    logic = {
        "1": {
            "Tasks": [
                {
                    "$type": "TaskTriggerSubscription",
                    "Trigger": {"$type": "OnEnterEvent"},
                    "DirectEffector": {
                        "Effector": {"$type": "PlaySoundInALoop", "Url": "http://example.com/ambient.mp3"},
                    },
                }
            ]
        },
    }
    zones = {
        "zone1": (-10, 10, -10, 10),
    }

    summary = generate_build_summary("Atmo Test", items, logic, {}, zones=zones)
    assert "atmospheric=Y" in summary, f"Should detect atmospheric via logic: {summary}"

    # Without the logic entry, atmospheric should be N (GLB is structural, not atmospheric)
    summary_no_logic = generate_build_summary("Atmo Test", items, {}, {}, zones=zones)
    assert "atmospheric=N" in summary_no_logic, f"Without ambient loop, atmospheric should be N: {summary_no_logic}"

    print("  PASS")


if __name__ == "__main__":
    test_merge_logic_into_items()
    test_split_logic_from_items()
    test_normalize_snapshot()
    test_count_types_in_logic()
    test_generate_build_summary()
    test_validate_room_data_new_format()
    test_validate_room_data_legacy_format()
    test_validate_room_data_roomItems_takes_precedence()
    test_deprecation_notes()
    test_roundtrip_merge_split()
    test_generate_build_summary_zone_atmospheric()

    print("\n=== ALL TESTS PASSED ===")
