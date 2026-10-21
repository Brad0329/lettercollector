"""MCP resources providing read-only access to cached cursive script metadata."""
import json
from src.collector.storage import CursiveStorage

storage = CursiveStorage()


def list_cached_characters() -> str:
    """Return JSON string of all currently cached characters."""
    chars = storage.list_all_characters()
    return json.dumps(chars, ensure_ascii=False, indent=2)


def get_character_metadata(char: str) -> str:
    """Return JSON string of index.json for a specific character."""
    index_obj = storage.get_index(char)
    if index_obj is None:
        return json.dumps({"error": f"Character '{char}' is not cached locally."}, ensure_ascii=False)
    return index_obj.model_dump_json(indent=2)
