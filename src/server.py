"""LetterCollector MCP Server Entrypoint."""
import os
import sys

# Ensure UTF-8 I/O encoding on Windows to prevent stdio protocol destruction
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from typing import Any
from fastmcp import FastMCP

from src.common.logging import logger
from src.resources.cursive_resources import get_character_metadata, list_cached_characters
from src.routes import (
    get_cursive_api_route,
    get_gallery_html_route,
    get_image_file_route,
    health_check_route,
)
from src.tools.cursive_tools import find_cursive as _find_cursive
from src.tools.cursive_tools import get_cursive_image as _get_cursive_image

# Initialize FastMCP Server
mcp = FastMCP("LetterCollector")

# ---------------------------------------------------------
# Custom Web & REST API Routes (Cloud / App / Web support)
# ---------------------------------------------------------
mcp.custom_route("/health", methods=["GET"])(health_check_route)
mcp.custom_route("/api/cursive/{char}", methods=["GET"])(get_cursive_api_route)
mcp.custom_route("/gallery/{char}", methods=["GET"])(get_gallery_html_route)
mcp.custom_route("/images/{char}/{filename}", methods=["GET"])(get_image_file_route)

# ---------------------------------------------------------
# MCP Tools
# ---------------------------------------------------------
@mcp.tool()
async def find_cursive(char: str, refresh: bool = False) -> Any:
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
async def get_cursive_image(char: str, index: int) -> Any:
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
    """Run FastMCP server.

    If PORT environment variable is set (e.g. Google Cloud Run) or MCP_TRANSPORT=sse,
    runs over HTTP (SSE/Streamable HTTP) transport with REST APIs enabled.
    Otherwise defaults to standard stdio transport for local AI tools (Claude Desktop / Claude Code / Antigravity).
    """
    port_env = os.environ.get("PORT")
    transport_env = os.environ.get("MCP_TRANSPORT", "").lower()

    if port_env or transport_env in ("http", "sse"):
        port = int(port_env or "8080")
        host = os.environ.get("HOST", "0.0.0.0")
        logger.info("Starting LetterCollector Server on %s:%d via SSE/HTTP...", host, port)
        mcp.run(transport="sse", host=host, port=port)
    else:
        logger.info("Starting LetterCollector MCP Server via stdio...")
        mcp.run()


if __name__ == "__main__":
    main()
