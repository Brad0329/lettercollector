"""Unit tests for MCP resources."""
import json
from unittest.mock import patch

from src.collector.models import CursiveCharIndex
from src.resources.cursive_resources import get_character_metadata, list_cached_characters


def test_list_cached_characters_empty(tmp_path):
    with patch("src.resources.cursive_resources.storage.list_all_characters", return_value=[]):
        res = list_cached_characters()
        assert json.loads(res) == []


def test_get_character_metadata_not_found(tmp_path):
    with patch("src.resources.cursive_resources.storage.get_index", return_value=None):
        res = get_character_metadata("無")
        data = json.loads(res)
        assert "error" in data


def test_get_character_metadata_found(tmp_path):
    dummy_index = CursiveCharIndex(
        char="永",
        canonical_char="永",
        canonical_path="0101/1000",
        total_count=26,
        calligrapher_counts={"王羲之": 5},
        fetched_at="2026-10-21T10:00:00",
        storage_dir=str(tmp_path / "永"),
        items=[],
    )

    with patch("src.resources.cursive_resources.storage.get_index", return_value=dummy_index):
        res = get_character_metadata("永")
        data = json.loads(res)
        assert data["char"] == "永"
        assert data["total_count"] == 26
