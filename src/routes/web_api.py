"""Custom HTTP routes for web browsers, mobile apps (e.g. hanjadic), and cloud health checks."""
import os
from pathlib import Path
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, Response

from src.collector.storage import CursiveStorage
from src.collector.visualizer import generate_grid_image, generate_html_gallery
from src.collector.zdic_client import ZdicClient
from src.common.config import STORAGE_DIR
from src.common.exceptions import CursiveErrorKind, CursiveException
from src.common.logging import logger
from src.tools.cursive_tools import _download_all_images

storage = CursiveStorage()
zdic_client = ZdicClient()


def _verify_api_key(request: Request) -> bool:
    """Check API key if LETTER_API_KEY environment variable is configured."""
    expected_key = os.environ.get("LETTER_API_KEY")
    if not expected_key:
        return True  # Open access when key is not configured

    client_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    return client_key == expected_key


async def health_check_route(request: Request) -> Response:
    """Cloud Run / load balancer health check."""
    return JSONResponse({
        "status": "ok",
        "service": "LetterCollector",
        "storage_dir": str(STORAGE_DIR),
    })


async def get_cursive_api_route(request: Request) -> Response:
    """REST API endpoint for mobile apps and web frontends: GET /api/cursive/{char}."""
    if not _verify_api_key(request):
        return JSONResponse({"error": "Unauthorized: Invalid or missing API key"}, status_code=401)

    char = request.path_params.get("char", "").strip()
    if len(char) != 1:
        return JSONResponse({"error": f"Invalid character: '{char}'. Must be exactly 1 character."}, status_code=400)

    refresh = request.query_params.get("refresh", "false").lower() in ("true", "1", "yes")

    try:
        # Check cache
        cached = storage.get_index(char)
        if cached is None or refresh:
            logger.info("REST API fetching cursive for '%s' (refresh=%s)", char, refresh)
            canonical_path, hits = await zdic_client.search_cursive(char)
            if not hits:
                return JSONResponse({
                    "char": char,
                    "total_count": 0,
                    "items": [],
                    "message": f"No cursive calligraphy found for '{char}' on sf.zdic.net",
                })

            images = await _download_all_images(hits)
            index_obj = storage.save_collection(char, canonical_path, hits, images)

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
        else:
            index_obj = cached

        canonical_char = index_obj.canonical_char
        return JSONResponse({
            "char": char,
            "canonical_char": canonical_char,
            "total_count": index_obj.total_count,
            "calligrapher_counts": index_obj.calligrapher_counts,
            "fetched_at": index_obj.fetched_at,
            "grid_url": f"/images/{canonical_char}/grid.png",
            "gallery_url": f"/gallery/{canonical_char}",
            "items": [
                {
                    "index": item.index,
                    "calligrapher": item.calligrapher,
                    "calligrapher_ko": item.calligrapher_ko,
                    "image_url": f"/images/{canonical_char}/{item.filename}",
                    "source_url": item.url,
                }
                for item in index_obj.items
            ],
        })

    except CursiveException as e:
        logger.error("CursiveException in REST API for '%s': %s", char, e)
        return JSONResponse({"error": str(e), "kind": e.kind.value}, status_code=500)
    except Exception as e:
        logger.error("Unexpected error in REST API for '%s': %s", char, e)
        return JSONResponse({"error": f"Internal server error: {e}"}, status_code=500)


async def get_gallery_html_route(request: Request) -> Response:
    """Serve standalone HTML gallery view in browser: GET /gallery/{char}."""
    char = request.path_params.get("char", "").strip()
    if len(char) != 1:
        return HTMLResponse("<h1>Invalid character</h1>", status_code=400)

    cached = storage.get_index(char)
    if not cached or not cached.gallery_html_path or not Path(cached.gallery_html_path).exists():
        # Trigger fetch if not cached
        canonical_char = storage.resolve_canonical_char(char)
        char_dir = storage.storage_dir / canonical_char
        gallery_file = char_dir / "index.html"
        if not gallery_file.exists():
            return HTMLResponse(f"<h1>'{char}' 글자의 초서 갤러리가 없습니다. 먼저 수집해 주세요.</h1>", status_code=404)
        return HTMLResponse(gallery_file.read_text(encoding="utf-8"))

    return HTMLResponse(Path(cached.gallery_html_path).read_text(encoding="utf-8"))


async def get_image_file_route(request: Request) -> Response:
    """Serve static image files (GIF, grid.png): GET /images/{char}/{filename}."""
    char = request.path_params.get("char", "").strip()
    filename = request.path_params.get("filename", "").strip()

    # Security check: Prevent path traversal
    target_char = storage.resolve_canonical_char(char)
    file_path = (storage.storage_dir / target_char / filename).resolve()

    try:
        file_path.relative_to(storage.storage_dir)
    except ValueError:
        return Response("Forbidden: Path traversal detected", status_code=403)

    if not file_path.exists() or not file_path.is_file():
        return Response("Image not found", status_code=404)

    media_type = "image/png" if filename.endswith(".png") else "image/gif"
    return FileResponse(file_path, media_type=media_type)
