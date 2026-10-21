"""Tests for FastMCP server initialization and schema inspection."""
import pytest
from src.server import mcp


@pytest.mark.asyncio
async def test_server_tools_registered():
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "find_cursive" in tool_names
    assert "get_cursive_image" in tool_names


@pytest.mark.asyncio
async def test_server_resources_registered():
    resources = await mcp.list_resources()
    resource_uris = [str(r.uri) for r in resources]
    assert any("cursive://list" in uri for uri in resource_uris)
