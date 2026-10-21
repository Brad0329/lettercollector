"""Routes package exports."""
from src.routes.web_api import (
    get_cursive_api_route,
    get_gallery_html_route,
    get_image_file_route,
    health_check_route,
)

__all__ = [
    "health_check_route",
    "get_cursive_api_route",
    "get_gallery_html_route",
    "get_image_file_route",
]
