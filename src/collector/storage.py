"""Local file storage and caching management for cursive scripts."""
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.collector.models import CursiveCharIndex, CursiveItem
from src.common.config import STORAGE_DIR
from src.common.exceptions import CursiveErrorKind, CursiveException
from src.common.logging import logger

CHAR_MAP_FILE = "char_map.json"


class CursiveStorage:
    """Manages character folders, image files, index.json, and canonical mapping."""

    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = Path(storage_dir or STORAGE_DIR).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.map_file = self.storage_dir / CHAR_MAP_FILE
        self._char_map = self._load_char_map()

    def _load_char_map(self) -> dict[str, str]:
        if self.map_file.exists():
            try:
                return json.loads(self.map_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to parse char_map.json, resetting: %s", e)
        return {}

    def _save_char_map(self) -> None:
        try:
            self.map_file.write_text(
                json.dumps(self._char_map, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to write char_map.json: %s", e)

    def resolve_canonical_char(self, char: str) -> str:
        """Find the canonical folder name for the character if mapped."""
        return self._char_map.get(char, char)

    def get_index(self, char: str) -> CursiveCharIndex | None:
        """Load cached CursiveCharIndex for a character if it exists."""
        target_char = self.resolve_canonical_char(char)
        char_dir = self.storage_dir / target_char
        index_file = char_dir / "index.json"

        if not index_file.exists():
            return None

        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            # Reconstruct model
            return CursiveCharIndex(**data)
        except Exception as e:
            logger.warning("Failed to load cache index for '%s': %s", target_char, e)
            return None

    def save_collection(
        self,
        char: str,
        canonical_path: str,
        hits: list[dict[str, Any]],
        images: list[bytes],
    ) -> CursiveCharIndex:
        """Atomically save all downloaded images and generate index.json."""
        if len(hits) != len(images):
            raise CursiveException(
                CursiveErrorKind.BAD_RESPONSE,
                f"저장 데이터 불일치 (메타데이터 {len(hits)}건 vs 이미지 {len(images)}건)",
            )

        # Check if canonical_path is already mapped to an existing character folder
        path_key = f"path:{canonical_path}" if canonical_path else ""
        canonical_char = self._char_map.get(path_key, char) if path_key else char

        # Register mapping: char -> canonical_char & path_key -> canonical_char
        self._char_map[char] = canonical_char
        if path_key:
            self._char_map[path_key] = canonical_char
        self._save_char_map()

        char_dir = self.storage_dir / canonical_char
        char_dir.mkdir(parents=True, exist_ok=True)

        items: list[CursiveItem] = []
        calligrapher_counts: Counter[str] = Counter()

        for idx, (hit, img_data) in enumerate(zip(hits, images, strict=True), start=1):
            calligrapher = hit["calligrapher"]
            calligrapher_ko = hit.get("calligrapher_ko", calligrapher)
            calligrapher_counts[calligrapher] += 1

            # Format: 001_황정견.gif (sanitized)
            safe_name = "".join(c for c in calligrapher if c.isalnum() or c in ("_", "-"))
            filename = f"{idx:03d}_{safe_name}.gif"
            file_path = char_dir / filename

            # Write individual image
            file_path.write_bytes(img_data)

            items.append(
                CursiveItem(
                    index=idx,
                    calligrapher=calligrapher,
                    calligrapher_ko=calligrapher_ko,
                    url=hit["url"],
                    filename=filename,
                    file_path=str(file_path.resolve()),
                )
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        index_obj = CursiveCharIndex(
            char=char,
            canonical_char=canonical_char,
            canonical_path=canonical_path,
            total_count=len(items),
            calligrapher_counts=dict(calligrapher_counts),
            fetched_at=now_iso,
            storage_dir=str(char_dir.resolve()),
            items=items,
            grid_image_path=None,
            gallery_html_path=None,
        )

        # Write index.json
        index_file = char_dir / "index.json"
        index_file.write_text(
            index_obj.model_dump_json(indent=2),
            encoding="utf-8",
        )
        logger.info("Saved collection for '%s' (%d images) at %s", char, len(items), char_dir)
        return index_obj

    def update_index_artifacts(
        self,
        canonical_char: str,
        grid_path: str | None = None,
        gallery_path: str | None = None,
    ) -> None:
        """Update artifact paths (grid/gallery) in index.json."""
        char_dir = self.storage_dir / canonical_char
        index_file = char_dir / "index.json"
        if not index_file.exists():
            return

        try:
            data = json.loads(index_file.read_text(encoding="utf-8"))
            if grid_path is not None:
                data["grid_image_path"] = grid_path
            if gallery_path is not None:
                data["gallery_html_path"] = gallery_path
            index_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error("Failed to update index artifacts for '%s': %s", canonical_char, e)

    def list_all_characters(self) -> list[dict[str, Any]]:
        """List all cached characters and their summary."""
        results = []
        for p in self.storage_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                index_file = p / "index.json"
                if index_file.exists():
                    try:
                        data = json.loads(index_file.read_text(encoding="utf-8"))
                        results.append({
                            "char": data.get("canonical_char", p.name),
                            "total_count": data.get("total_count", 0),
                            "fetched_at": data.get("fetched_at", ""),
                            "storage_dir": str(p.resolve()),
                        })
                    except Exception:
                        pass
        return sorted(results, key=lambda x: x["char"])
