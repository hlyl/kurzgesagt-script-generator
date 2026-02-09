"""Unit tests for scene parser JSON repair helpers."""

from src.kurzgesagt.core.scene_parser import SceneParser


def test_repair_json_text_closes_strings_and_braces():
    broken = '{"scenes": [{"number": 1, "title": "Intro"'
    repaired = SceneParser._repair_json_text(broken)

    assert repaired.endswith("}")
    assert repaired.count("{") == repaired.count("}")


def test_parse_json_with_truncation_returns_valid_prefix():
    text = '{"scenes": [{"number": 1}], "extra": {"a": 1}} trailing'
    parsed = SceneParser._parse_json_with_truncation(text)

    assert parsed["scenes"][0]["number"] == 1