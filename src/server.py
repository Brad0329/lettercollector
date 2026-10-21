"""LetterCollector MCP Server Entrypoint."""
import sys

# Ensure UTF-8 I/O encoding on Windows to prevent stdio protocol destruction
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from fastmcp import FastMCP

from src.common.logging import logger
from src.resources.cursive_resources import get_character_metadata, list_cached_characters
from src.tools.cursive_tools import find_cursive as _find_cursive
from src.tools.cursive_tools import get_cursive_image as _get_cursive_image

# Initialize FastMCP Server
mcp = FastMCP("LetterCollector")

# ---------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------
@mcp.tool()
async def find_cursive(char: str, refresh: bool = False) -> str:
    """Find and retrieve all cursive script (草書) calligraphy images for a given Chinese character from sf.zdic.net, saving them to local storage and returning statistics, a visual grid summary image path, and an HTML gallery path.

    WHEN TO USE:
    - Use this tool when the user asks to look up or show cursive script images for a Chinese character (e.g., '書 글자 초서 찾아줘', 'show cursive for 永').
    - Caches results locally so repeated queries are instant without re-downloading.

    Args:
        char: A single Chinese character (e.g. '書', '永', '龍'). Must be exactly 1 character.
        refresh: If True, bypasses local cache and re-downloads fresh images from sf.zdic.net (default: False).

    Returns:
        A markdown summary containing total image count, calligrapher list with counts, local storage path, grid image path, and HTML gallery path.
    """
    return await _find_cursive(char=char, refresh=refresh)


@mcp.tool()
async def get_cursive_image(char: str, index: int) -> str:
    """Get information and the local file path of a specific cursive script image by index (1-based) for a Chinese character.

    WHEN TO USE:
    - Use this tool when the user wants to inspect or view a specific single image among the collected cursive scripts.

    Args:
        char: A single Chinese character (e.g. '書').
        index: 1-based index of the image to retrieve (e.g. 1 for the first image).

    Returns:
        A markdown summary with calligrapher name, source URL, local file path, and image metadata.
    """
    return await _get_cursive_image(char=char, index=index)


# ---------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------
@mcp.resource("cursive://list")
def list_cached_characters_resource() -> str:
    """Read-only JSON list of all locally cached characters and their total image counts."""
    return list_cached_characters()


@mcp.resource("cursive://char/{char}")
def get_character_metadata_resource(char: str) -> str:
    """Read-only JSON metadata of index.json for a specific character."""
    return get_character_metadata(char=char)


def main() -> None:
    """Run FastMCP server over standard stdio."""
    logger.info("Starting LetterCollector MCP Server via stdio...")
    mcp.run()


if __name__ == "__main__":
    main()
