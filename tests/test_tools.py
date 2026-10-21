"""Unit tests for cursive MCP tools."""
from unittest.mock import AsyncMock, patch
import pytest

from src.collector.models import CursiveCharIndex, CursiveItem
from src.common.exceptions import CursiveErrorKind, CursiveException
from src.tools.cursive_tools import find_cursive, get_cursive_image


@pytest.mark.asyncio
async def test_find_cursive_validation_error():
    with pytest.raises(CursiveException) as excinfo:
        await find_cursive("書永")  # 2 characters
    assert excinfo.value.kind == CursiveErrorKind.VALIDATION


@pytest.mark.asyncio
async def test_find_cursive_cached(tmp_path):
    char_dir = tmp_path / "書"
    char_dir.mkdir(parents=True, exist_ok=True)
    grid_path = char_dir / "grid.png"
    gallery_path = char_dir / "index.html"
    grid_path.write_bytes(b"dummy grid")
    gallery_path.write_text("dummy gallery", encoding="utf-8")

    dummy_index = CursiveCharIndex(
        char="書",
        canonical_char="書",
        canonical_path="1122/248309",
        total_count=1,
        calligrapher_counts={"黄庭坚": 1},
        fetched_at="2026-10-21T10:00:00",
        storage_dir=str(char_dir.resolve()),
        items=[
            CursiveItem(
                index=1,
                calligrapher="黄庭坚",
                calligrapher_ko="황정견",
                url="https://sf.zdic.net/1.gif",
                filename="001_황정견.gif",
                file_path=str((char_dir / "001_황정견.gif").resolve()),
            )
        ],
        grid_image_path=str(grid_path.resolve()),
        gallery_html_path=str(gallery_path.resolve()),
    )

    with patch("src.tools.cursive_tools.storage.get_index", return_value=dummy_index):
        result = await find_cursive("書")
        assert "**총 수집 장수**: **1장**" in result
        assert "grid.png" in result


@pytest.mark.asyncio
async def test_get_cursive_image_bounds(tmp_path):
    char_dir = tmp_path / "書"
    dummy_index = CursiveCharIndex(
        char="書",
        canonical_char="書",
        canonical_path="1122/248309",
        total_count=2,
        calligrapher_counts={"黄庭坚": 2},
        fetched_at="2026-10-21T10:00:00",
        storage_dir=str(char_dir.resolve()),
        items=[
            CursiveItem(
                index=1,
                calligrapher="黄庭坚",
                calligrapher_ko="황정견",
                url="https://sf.zdic.net/1.gif",
                filename="001_황정견.gif",
                file_path=str((char_dir / "001_황정견.gif").resolve()),
            ),
            CursiveItem(
                index=2,
                calligrapher="黄庭坚",
                calligrapher_ko="황정견",
                url="https://sf.zdic.net/2.gif",
                filename="002_황정견.gif",
                file_path=str((char_dir / "002_황정견.gif").resolve()),
            ),
        ],
    )

    with patch("src.tools.cursive_tools.storage.get_index", return_value=dummy_index):
        # Valid index 1
        res1 = await get_cursive_image("書", 1)
        assert "초서 이미지 #1" in res1
        assert "001_황정견.gif" in res1

        # Out of bounds index 3
        with pytest.raises(CursiveException) as excinfo:
            await get_cursive_image("書", 3)
        assert excinfo.value.kind == CursiveErrorKind.VALIDATION
