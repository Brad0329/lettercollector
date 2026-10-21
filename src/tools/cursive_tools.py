"""Core MCP tools for searching, collecting and inspecting Chinese cursive script calligraphy."""
import asyncio
from pathlib import Path
from typing import Any

from src.collector.models import CursiveCharIndex
from src.collector.storage import CursiveStorage
from src.collector.visualizer import generate_grid_image, generate_html_gallery
from src.collector.zdic_client import ZdicClient
from src.common import config
from src.common.config import public_url
from src.common.exceptions import CursiveErrorKind, CursiveException
from src.common.logging import logger
from fastmcp.utilities.types import Image

storage = CursiveStorage()
zdic_client = ZdicClient()


async def _download_all_images(hits: list[dict], max_concurrency: int = 10) -> list[bytes]:
    """Download images in parallel while bounding concurrency."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _fetch(hit: dict) -> bytes:
        async with semaphore:
            return await zdic_client.download_image(hit["url"])

    tasks = [_fetch(h) for h in hits]
    return await asyncio.gather(*tasks)


async def find_cursive(char: str, refresh: bool = False) -> str:
    """
    Find and retrieve all cursive script (草書) calligraphy images for a given Chinese character from sf.zdic.net, saving them to local storage and returning statistics, a visual grid summary image path, and an HTML gallery path.

    WHEN TO USE:
    - Use this tool when the user asks to look up or show cursive script images for a Chinese character (e.g., '書 글자 초서 찾아줘', 'show cursive for 永').
    - Caches results locally so repeated queries are instant without re-downloading.

    Args:
        char: A single Chinese character (e.g. '書', '永', '龍'). Must be exactly 1 character.
        refresh: If True, bypasses local cache and re-downloads fresh images from sf.zdic.net (default: False).

    Returns:
        A markdown summary containing total image count, calligrapher list with counts, local storage path, grid image path, and HTML gallery path.
    """
    clean_char = char.strip()
    if len(clean_char) != 1:
        raise CursiveException(
            CursiveErrorKind.VALIDATION,
            f"검색어는 정확히 1글자의 한자여야 합니다 (입력: '{char}')",
        )

    # 1. Check local cache
    cached = storage.get_index(clean_char)
    if cached is not None and not refresh:
        logger.info("Using cached cursive data for '%s' (%d images)", clean_char, cached.total_count)
        index_obj = cached
        # Ensure grid and gallery artifacts exist
        char_dir = Path(index_obj.storage_dir)
        grid_file = char_dir / "grid.png"
        gallery_file = char_dir / "index.html"
        updated = False
        if not grid_file.exists():
            generate_grid_image(index_obj, grid_file)
            index_obj.grid_image_path = str(grid_file.resolve())
            updated = True
        if not gallery_file.exists():
            generate_html_gallery(index_obj, gallery_file)
            index_obj.gallery_html_path = str(gallery_file.resolve())
            updated = True
        if updated:
            storage.update_index_artifacts(
                index_obj.canonical_char,
                grid_path=index_obj.grid_image_path,
                gallery_path=index_obj.gallery_html_path,
            )
    else:
        # 2. Fetch from zdic
        logger.info("Fetching cursive scripts for '%s' from sf.zdic.net (refresh=%s)", clean_char, refresh)
        canonical_path, hits = await zdic_client.search_cursive(clean_char)

        if not hits:
            return f"### 📜 '{clean_char}' 초서(草書) 검색 결과\n\nsf.zdic.net에 '{clean_char}' 글자의 초서 이미지가 등록되어 있지 않습니다 (0건)."

        # 3. Download images
        logger.info("Downloading %d cursive images for '%s'", len(hits), clean_char)
        images = await _download_all_images(hits)

        # 4. Save collection atomically
        index_obj = storage.save_collection(clean_char, canonical_path, hits, images)

        # 5. Generate grid image and HTML gallery
        char_dir = Path(index_obj.storage_dir)
        grid_file = char_dir / "grid.png"
        gallery_file = char_dir / "index.html"

        generate_grid_image(index_obj, grid_file)
        generate_html_gallery(index_obj, gallery_file)

        index_obj.grid_image_path = str(grid_file.resolve())
        index_obj.gallery_html_path = str(gallery_file.resolve())
        storage.update_index_artifacts(
            index_obj.canonical_char,
            grid_path=index_obj.grid_image_path,
            gallery_path=index_obj.gallery_html_path,
        )

    # 6. Format Markdown Response
    top_calligraphers = sorted(index_obj.calligrapher_counts.items(), key=lambda x: -x[1])
    calligrapher_summary_lines = []
    for name, cnt in top_calligraphers[:10]:
        calligrapher_summary_lines.append(f"- **{name}**: {cnt}장")
    if len(top_calligraphers) > 10:
        calligrapher_summary_lines.append(f"- *(외 {len(top_calligraphers) - 10}명의 서예가)*")

    calligraphers_text = "\n".join(calligrapher_summary_lines)
    canonical = index_obj.canonical_char
    if config.PUBLIC_BASE_URL:
        # Remote server: local paths mean nothing to the client — give web URLs instead.
        grid_url = public_url(canonical, "grid.png") if index_obj.grid_image_path else ""
        grid_embed = f"\n\n![{clean_char} 초서 격자 미리보기]({grid_url})" if grid_url else ""
        grid_info = f"- **격자 합성 미리보기**: {grid_url}" if grid_url else ""
        gallery_info = f"- **브라우저 HTML 갤러리**: {public_url(canonical)}" if index_obj.gallery_html_path else ""
        location_line = ""
    else:
        grid_uri = Path(index_obj.grid_image_path).as_uri() if index_obj.grid_image_path else ""
        grid_embed = f"\n\n![{clean_char} 초서 격자 미리보기]({grid_uri})" if grid_uri else ""
        grid_info = f"- **격자 합성 미리보기**: `{index_obj.grid_image_path}`" if index_obj.grid_image_path else ""
        gallery_info = f"- **브라우저 HTML 갤러리**: `{index_obj.gallery_html_path}`" if index_obj.gallery_html_path else ""
        location_line = f"- **저장 위치**: `{index_obj.storage_dir}`\n"

    summary_text = f"""### 📜 '{clean_char}' 초서(草書) 수집 결과 요약

- **글자**: `{clean_char}` (저장 대표명: `{index_obj.canonical_char}`)
- **총 수집 장수**: **{index_obj.total_count}장**
- **서예가 수**: {len(index_obj.calligrapher_counts)}명
{location_line}{grid_info}
{gallery_info}
{grid_embed}

#### 주요 서예가별 장수
{calligraphers_text}

> 특정 서예가의 이미지를 열람하려면 `get_cursive_image(char='{clean_char}', index=N)` 도구를 호출하세요 (1 ~ {index_obj.total_count}).
"""
    if index_obj.grid_image_path and Path(index_obj.grid_image_path).exists():
        return [summary_text, Image(path=index_obj.grid_image_path)]
    return summary_text


async def get_cursive_image(char: str, index: int) -> Any:
    """
    Get information and the local file path of a specific cursive script image by index (1-based) for a Chinese character.

    WHEN TO USE:
    - Use this tool when the user wants to inspect or view a specific single image among the collected cursive scripts.

    Args:
        char: A single Chinese character (e.g. '書').
        index: 1-based index of the image to retrieve (e.g. 1 for the first image).

    Returns:
        A markdown summary with calligrapher name, source URL, local file path, and image metadata.
    """
    clean_char = char.strip()
    if len(clean_char) != 1:
        raise CursiveException(
            CursiveErrorKind.VALIDATION,
            f"검색어는 정확히 1글자의 한자여야 합니다 (입력: '{char}')",
        )

    # Check cache, or fetch if not present
    cached = storage.get_index(clean_char)
    if cached is None:
        logger.info("Character '%s' not cached yet, fetching first", clean_char)
        await find_cursive(clean_char)
        cached = storage.get_index(clean_char)

    if cached is None or cached.total_count == 0:
        return f"### ❌ '{clean_char}' 초서 이미지 없음\n\n'{clean_char}'에 대해 수집된 초서 이미지가 없습니다."

    if index < 1 or index > cached.total_count:
        raise CursiveException(
            CursiveErrorKind.VALIDATION,
            f"순번 오류: 1부터 {cached.total_count} 사이의 번호를 지정해야 합니다 (입력 index: {index})",
        )

    target_item = cached.items[index - 1]
    if config.PUBLIC_BASE_URL:
        img_uri = public_url(cached.canonical_char, target_item.filename)
        location_line = f"- **이미지 URL**: {img_uri}"
    else:
        img_uri = Path(target_item.file_path).as_uri()
        location_line = f"- **로컬 파일 경로**: `{target_item.file_path}`"

    info_text = f"""### 🖼️ '{clean_char}' 초서 이미지 #{target_item.index}

![{clean_char} #{target_item.index} {target_item.calligrapher_ko}]({img_uri})

- **서예가**: **{target_item.calligrapher_ko}** ({target_item.calligrapher})
- **파일명**: `{target_item.filename}`
{location_line}
- **원본 웹 URL**: {target_item.url}
- **전체 장수 중 순번**: {target_item.index} / {cached.total_count}
"""
    if Path(target_item.file_path).exists():
        return [info_text, Image(path=target_item.file_path)]
    return info_text
