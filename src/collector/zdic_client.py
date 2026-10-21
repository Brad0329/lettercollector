"""Client and parser for sf.zdic.net cursive calligraphy repository."""
import html
import re
import urllib.parse
from typing import Any
import httpx

from src.common.aliases import get_calligrapher_ko, normalize_calligrapher_name
from src.common.config import (
    DEFAULT_HEADERS,
    NETWORK_TIMEOUT_SECONDS,
    ZDIC_BASE_URL,
    ZDIC_FRAGMENT_URL_TEMPLATE,
    ZDIC_SEARCH_URL,
    is_valid_image,
)
from src.common.exceptions import CursiveErrorKind, CursiveException
from src.common.logging import logger

ZDIC_NO_RESULT_MARKER = "没有搜索到相关的内容"
GSFT_REGEX = re.compile(r"""gsft\(\s*["']cs["']\s*,\s*["']([0-9]+/[0-9]+)["']\s*\)""", re.IGNORECASE)
IMG_TAG_REGEX = re.compile(r"""<img\b[^>]*>""", re.IGNORECASE)


def extract_html_attr(tag: str, attr_name: str) -> str | None:
    """Extract an attribute value from an HTML tag string and unescape entities."""
    pattern = rf"""\b{attr_name}\s*=\s*["']([^"']*)["']"""
    m = re.search(pattern, tag, re.IGNORECASE)
    if not m:
        return None
    val = m.group(1)
    val = html.unescape(val)
    val = val.replace("&middot;", "·").replace("&#183;", "·")
    return val.strip()


def parse_zdic_char_page(html_content: str) -> str | None:
    """Extract fragment path (e.g. '1122/248309') from character page HTML.

    Returns:
        str: Relative path key if found.
        None: When character has no cursive scripts available (legitimate 0 results).

    Raises:
        CursiveException: If page structure changed unexpectedly.
    """
    m = GSFT_REGEX.search(html_content)
    if m:
        return m.group(1)
    if ZDIC_NO_RESULT_MARKER in html_content:
        return None

    head = html_content.strip()[:60]
    raise CursiveException(
        CursiveErrorKind.BAD_RESPONSE,
        f"zdic 글자 페이지 형식이 다릅니다 (앞부분: {head})",
    )


def parse_zdic_fragment(html_content: str) -> list[dict[str, Any]]:
    """Parse cursive images from fragment HTML chunk.

    Looks for `<img src="..." title="서예가" class="bn">`.
    """
    hits: list[dict[str, Any]] = []
    has_any_img = False

    for m in IMG_TAG_REGEX.finditer(html_content):
        tag = m.group(0)
        has_any_img = True
        cls = extract_html_attr(tag, "class")
        if cls != "bn":
            continue

        src = extract_html_attr(tag, "src")
        title = extract_html_attr(tag, "title")

        if not src or not title:
            logger.warning("Skipping zdic img tag missing src or title: %s", tag)
            continue

        # Full URL resolution if relative
        if src.startswith("//"):
            src = "https:" + src
        elif src.startswith("/"):
            src = urllib.parse.urljoin(ZDIC_BASE_URL, src)

        norm_title = normalize_calligrapher_name(title)
        ko_title = get_calligrapher_ko(norm_title)

        hits.append({
            "calligrapher": norm_title,
            "calligrapher_ko": ko_title,
            "url": src,
        })

    if not hits and has_any_img:
        raise CursiveException(
            CursiveErrorKind.BAD_RESPONSE,
            "초서 목록 조각에서 class='bn' 이미지를 찾지 못했습니다 (사이트 구조 변경 가능성)",
        )

    return hits


class ZdicClient:
    """HTTP client interacting strictly with sf.zdic.net."""

    def __init__(self, timeout: float = NETWORK_TIMEOUT_SECONDS):
        self.timeout = timeout

    async def search_cursive(self, char: str) -> tuple[str, list[dict[str, Any]]]:
        """Search cursive scripts for a character.

        Returns:
            tuple[str, list[dict]]: (fragment_path, hits).
            If no cursive script found, returns ("", []).
        """
        if len(char) != 1:
            raise CursiveException(
                CursiveErrorKind.VALIDATION,
                f"한 글자의 한자만 검색 가능합니다 (입력: '{char}')",
            )

        encoded_char = urllib.parse.quote(char)
        form_str = f"classid=35&show=simtra&tp=tp1&keyboard={encoded_char}"
        form_bytes = form_str.encode("utf-8")

        headers = dict(DEFAULT_HEADERS)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Content-Length"] = str(len(form_bytes))

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
            try:
                # 1. POST search request
                current_url = httpx.URL(ZDIC_SEARCH_URL)
                logger.info("Sending zdic search POST for '%s'", char)
                response = await client.post(
                    current_url,
                    content=form_bytes,
                    headers=headers,
                )

                # 2. Follow redirects manually (typically two 302 hops)
                hops = 0
                while response.is_redirect:
                    hops += 1
                    if hops > 5:
                        raise CursiveException(
                            CursiveErrorKind.BAD_RESPONSE,
                            f"리다이렉트 횟수 초과 ({hops}회)",
                        )
                    loc = response.headers.get("location")
                    if not loc:
                        raise CursiveException(
                            CursiveErrorKind.BAD_RESPONSE,
                            f"리다이렉트 응답에 Location 헤더가 없습니다 (status={response.status_code})",
                        )
                    current_url = current_url.join(loc)
                    logger.debug("Following 302 redirect [%d] to: %s", hops, current_url)
                    response = await client.get(current_url, headers=DEFAULT_HEADERS)

                if response.status_code != 200:
                    raise CursiveException(
                        CursiveErrorKind.NETWORK,
                        f"글자 페이지 응답 오류 (HTTP {response.status_code})",
                    )

                char_page_html = response.text
                fragment_path = parse_zdic_char_page(char_page_html)

                if fragment_path is None:
                    logger.info("No cursive results for '%s' from zdic", char)
                    return ("", [])

                # 3. Fetch fragment HTML chunk
                frag_url = ZDIC_FRAGMENT_URL_TEMPLATE.format(path=fragment_path)
                logger.info("Fetching cursive fragment from: %s", frag_url)
                frag_headers = dict(DEFAULT_HEADERS)
                frag_headers["Referer"] = str(current_url)

                frag_resp = await client.get(frag_url, headers=frag_headers)
                if frag_resp.status_code != 200:
                    raise CursiveException(
                        CursiveErrorKind.NETWORK,
                        f"초서 목록 조각 요청 실패 (HTTP {frag_resp.status_code})",
                    )

                hits = parse_zdic_fragment(frag_resp.text)
                logger.info("Successfully parsed %d cursive hits for '%s'", len(hits), char)
                return (fragment_path, hits)

            except httpx.RequestError as exc:
                logger.error("Network error during zdic request for '%s': %s", char, exc)
                raise CursiveException(
                    CursiveErrorKind.NETWORK,
                    f"zdic 통신 실패: {exc}",
                ) from exc

    async def download_image(self, url: str) -> bytes:
        """Download a single cursive script image and verify binary magic number."""
        headers = dict(DEFAULT_HEADERS)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    raise CursiveException(
                        CursiveErrorKind.NETWORK,
                        f"이미지 다운로드 실패 (HTTP {resp.status_code}, URL: {url})",
                    )
                content = resp.content
                if not is_valid_image(content):
                    raise CursiveException(
                        CursiveErrorKind.BAD_RESPONSE,
                        f"다운로드된 데이터가 유효한 이미지가 아닙니다 ({len(content)} bytes, URL: {url})",
                    )
                return content
            except httpx.RequestError as exc:
                raise CursiveException(
                    CursiveErrorKind.NETWORK,
                    f"이미지 다운로드 네트워크 실패 ({url}): {exc}",
                ) from exc
