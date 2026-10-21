"""Configuration and environment settings for LetterCollector."""
import os
from pathlib import Path
from urllib.parse import quote

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_STORAGE_DIR = PROJECT_ROOT / "storage"
STORAGE_DIR = Path(os.environ.get("LETTER_STORAGE_DIR", str(DEFAULT_STORAGE_DIR))).resolve()

# Public base URL of this server (e.g. https://letter-collector-xxx.run.app).
# Set on cloud deploys so tool answers carry web URLs instead of server-local file paths,
# which remote clients cannot open. Unset (local stdio use) keeps local paths.
PUBLIC_BASE_URL = os.environ.get("LETTER_PUBLIC_BASE_URL", "").strip().rstrip("/")


def public_url(char: str, filename: str | None = None) -> str:
    """Web URL of a character's gallery (filename=None) or one of its files. Requires PUBLIC_BASE_URL."""
    if filename is None:
        return f"{PUBLIC_BASE_URL}/gallery/{quote(char)}"
    return f"{PUBLIC_BASE_URL}/images/{quote(char)}/{quote(filename)}"

# zdic endpoints
ZDIC_BASE_URL = "https://sf.zdic.net/"
ZDIC_SEARCH_URL = "https://sf.zdic.net/e/search/index.php"
ZDIC_FRAGMENT_URL_TEMPLATE = "https://sf.zdic.net/sftplb/cs/{path}.php"

# Network settings
NETWORK_TIMEOUT_SECONDS = float(os.environ.get("LETTER_TIMEOUT", "30.0"))

# User-Agent and headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": ZDIC_BASE_URL,
}

# Image validation magic numbers
def is_valid_image(data: bytes) -> bool:
    """Check if binary data begins with standard image header signatures."""
    if len(data) < 12:
        return False
    # JPEG (FF D8 FF)
    if data.startswith(b"\xff\xd8\xff"):
        return True
    # PNG (89 50 4E 47)
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    # GIF (GIF87a or GIF89a)
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return True
    # WEBP (RIFF....WEBP)
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return True
    return False
