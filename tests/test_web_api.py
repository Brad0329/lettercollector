"""Unit tests for REST API endpoints and web routes."""
import json
import httpx
import pytest

from src.server import mcp


@pytest.fixture
def app():
    return mcp.http_app()


@pytest.mark.asyncio
async def test_health_check_endpoint(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "LetterCollector"


@pytest.mark.asyncio
async def test_api_cursive_validation(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/cursive/永書")  # 2 characters
        assert resp.status_code == 400
        assert "Invalid character" in resp.json()["error"]


@pytest.mark.asyncio
async def test_api_cursive_cached(app, tmp_path):
    # Test reading already cached '永' (which we cached during earlier tests)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/cursive/永")
        assert resp.status_code == 200
        data = resp.json()
        assert data["char"] == "永"
        assert data["total_count"] == 26
        assert len(data["items"]) == 26
        assert data["grid_url"] == "/images/永/grid.png"
        assert data["gallery_url"] == "/gallery/永"


@pytest.mark.asyncio
async def test_gallery_html_endpoint(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/gallery/永")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "草書 '永' 서예 갤러리" in resp.text
        # Relative <img src> must resolve under /images/永/, not /gallery/
        assert '<base href="/images/%E6%B0%B8/">' in resp.text
        first_img = resp.text.split('<img src="', 1)[1].split('"', 1)[0]
        img_resp = await client.get(f"/images/永/{first_img}")
        assert img_resp.status_code == 200
        assert img_resp.headers["content-type"] == "image/gif"


@pytest.mark.asyncio
async def test_get_image_file_endpoint(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Check grid.png
        resp = await client.get("/images/永/grid.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert len(resp.content) > 1000

        # Check path traversal protection
        bad_resp = await client.get("/images/永/../../AGENTS.md")
        assert bad_resp.status_code in (403, 404)
