"""Unit tests for local storage and caching mechanism."""
import pytest
from src.collector.storage import CursiveStorage


def test_storage_save_and_get(tmp_path):
    storage = CursiveStorage(storage_dir=tmp_path)

    # Initial get should be None
    assert storage.get_index("書") is None

    # Fake hits & image bytes
    hits = [
        {
            "calligrapher": "黄庭坚",
            "calligrapher_ko": "황정견",
            "url": "https://sf.zdic.net/huang.gif",
        },
        {
            "calligrapher": "赵孟頫",
            "calligrapher_ko": "조맹부",
            "url": "https://sf.zdic.net/zhao.gif",
        },
    ]
    images = [
        b"GIF89a" + b"\x00" * 10,
        b"GIF89a" + b"\x01" * 10,
    ]

    index_obj = storage.save_collection(
        char="書",
        canonical_path="1122/248309",
        hits=hits,
        images=images,
    )

    assert index_obj.total_count == 2
    assert index_obj.calligrapher_counts == {"黄庭坚": 1, "赵孟頫": 1}

    # Verify retrieved index
    loaded = storage.get_index("書")
    assert loaded is not None
    assert loaded.total_count == 2
    assert len(loaded.items) == 2
    assert loaded.items[0].filename == "001_黄庭坚.gif"

    # Verify file existence on disk
    char_dir = tmp_path / "書"
    assert (char_dir / "index.json").exists()
    assert (char_dir / "001_黄庭坚.gif").exists()
    assert (char_dir / "002_赵孟頫.gif").exists()


def test_canonical_mapping_simplified_traditional(tmp_path):
    storage = CursiveStorage(storage_dir=tmp_path)

    hits = [{"calligrapher": "王羲之", "calligrapher_ko": "왕희지", "url": "https://sf.zdic.net/wang.gif"}]
    images = [b"GIF89a" + b"\x00" * 10]

    # First saved with traditional '書' and path '1122/248309'
    storage.save_collection("書", "1122/248309", hits, images)

    # Now simplified '书' comes with the same canonical path
    storage.save_collection("书", "1122/248309", hits, images)

    # Both '書' and '书' should resolve to the same folder and load index
    idx_trad = storage.get_index("書")
    idx_simp = storage.get_index("书")

    assert idx_trad is not None
    assert idx_simp is not None
    assert idx_trad.canonical_char == "書"
    assert idx_simp.canonical_char == "書"
    # Should not create a separate '书' folder
    assert not (tmp_path / "书").exists()
