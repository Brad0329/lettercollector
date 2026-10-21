"""Tests for common configurations, exceptions, aliases, and logging."""
import pytest
from src.common.aliases import get_calligrapher_ko, normalize_calligrapher_name
from src.common.config import is_valid_image
from src.common.exceptions import CursiveErrorKind, CursiveException


def test_normalize_and_korean_alias():
    # Pen name alias test
    assert normalize_calligrapher_name("赵子昂") == "赵孟頫"
    assert get_calligrapher_ko("赵子昂") == "조맹부"
    assert get_calligrapher_ko("王羲之") == "왕희지"
    assert get_calligrapher_ko("황정견") == "황정견"  # Unknown/fallback


def test_is_valid_image():
    # Valid headers
    assert is_valid_image(b"GIF89a" + b"\x00" * 10)
    assert is_valid_image(b"GIF87a" + b"\x00" * 10)
    assert is_valid_image(b"\xff\xd8\xff" + b"\x00" * 10)
    assert is_valid_image(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10)
    assert is_valid_image(b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 10)

    # Invalid / Too short / HTML
    assert not is_valid_image(b"GIF8")
    assert not is_valid_image(b"<!DOCTYPE html><html><body>Error</body></html>")
    assert not is_valid_image(b"\x00" * 20)


def test_cursive_exception():
    exc = CursiveException(CursiveErrorKind.NETWORK, "timeout")
    assert "네트워크 오류" in str(exc)

    exc2 = CursiveException(CursiveErrorKind.BAD_RESPONSE, "parse failed")
    assert "사이트 구조 변경" in str(exc2)

    exc3 = CursiveException(CursiveErrorKind.NO_RESULTS, "결과 없음")
    assert "초서 결과가 없습니다" in str(exc3)
