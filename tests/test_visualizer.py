"""Unit tests for visualizer (grid image and html gallery generation)."""
from pathlib import Path
from PIL import Image

from src.collector.models import CursiveCharIndex, CursiveItem
from src.collector.visualizer import generate_grid_image, generate_html_gallery


def test_generate_grid_and_html(tmp_path):
    char_dir = tmp_path / "書"
    char_dir.mkdir(parents=True, exist_ok=True)

    # Create dummy GIF image with white background
    img1 = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    img1_path = char_dir / "001_황정견.gif"
    img1.save(img1_path, format="GIF")

    items = [
        CursiveItem(
            index=1,
            calligrapher="黄庭坚",
            calligrapher_ko="황정견",
            url="https://sf.zdic.net/1.gif",
            filename="001_황정견.gif",
            file_path=str(img1_path.resolve()),
        )
    ]

    index_obj = CursiveCharIndex(
        char="書",
        canonical_char="書",
        canonical_path="1122/248309",
        total_count=1,
        calligrapher_counts={"黄庭坚": 1},
        fetched_at="2026-10-21T10:00:00",
        storage_dir=str(char_dir.resolve()),
        items=items,
    )

    grid_file = char_dir / "grid.png"
    gallery_file = char_dir / "index.html"

    # Test grid generation
    out_grid = generate_grid_image(index_obj, grid_file)
    assert out_grid.exists()
    with Image.open(out_grid) as im:
        assert im.format == "PNG"
        assert im.width > 0
        assert im.height > 0

    # Test HTML gallery generation
    out_gallery = generate_html_gallery(index_obj, gallery_file)
    assert out_gallery.exists()
    content = out_gallery.read_text(encoding="utf-8")
    assert "草書 '書' 서예 갤러리" in content
    assert "황정견" in content
    assert "001_황정견.gif" in content
