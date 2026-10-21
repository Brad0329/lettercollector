"""Unit tests for zdic HTML parsing and error handling."""
import pytest
from src.collector.zdic_client import (
    extract_html_attr,
    parse_zdic_char_page,
    parse_zdic_fragment,
)
from src.common.exceptions import CursiveErrorKind, CursiveException


def test_extract_html_attr():
    tag = '<img src="https://example.com/test.gif" title="晋 · 王羲之" class="bn">'
    assert extract_html_attr(tag, "src") == "https://example.com/test.gif"
    assert extract_html_attr(tag, "title") == "晋 · 王羲之"
    assert extract_html_attr(tag, "class") == "bn"
    assert extract_html_attr(tag, "nonexistent") is None


def test_parse_zdic_char_page_success():
    html_sample = """
    <!DOCTYPE html>
    <html>
    <head><title>書字草书</title></head>
    <body>
      <div id="content">
        <script>gsft("cs","1122/248309");</script>
      </div>
    </body>
    </html>
    """
    path = parse_zdic_char_page(html_sample)
    assert path == "1122/248309"


def test_parse_zdic_char_page_no_results():
    html_sample = """
    <!DOCTYPE html>
    <html>
    <body>
      <div>没有搜索到相关的内容</div>
    </body>
    </html>
    """
    path = parse_zdic_char_page(html_sample)
    assert path is None


def test_parse_zdic_char_page_bad_response():
    html_sample = "<html><body>Something totally unexpected</body></html>"
    with pytest.raises(CursiveException) as excinfo:
        parse_zdic_char_page(html_sample)
    assert excinfo.value.kind == CursiveErrorKind.BAD_RESPONSE


def test_parse_zdic_fragment_success():
    frag_html = """
    <div class="list">
      <img src="/d/file/mingjiashufa/caoshu/42/huang.gif" title="黄庭坚" class="bn">
      <img src="https://sf.zdic.net/d/file/mingjiashufa/caoshu/42/zhao.gif" title="赵子昂" class="bn">
      <img src="/ignore.gif" title="광고" class="ad">
    </div>
    """
    hits = parse_zdic_fragment(frag_html)
    assert len(hits) == 2
    assert hits[0]["calligrapher"] == "黄庭坚"
    assert hits[0]["calligrapher_ko"] == "황정견"
    assert hits[0]["url"] == "https://sf.zdic.net/d/file/mingjiashufa/caoshu/42/huang.gif"

    # Alias check (赵子昂 -> 赵孟頫 / 조맹부)
    assert hits[1]["calligrapher"] == "赵孟頫"
    assert hits[1]["calligrapher_ko"] == "조맹부"


def test_parse_zdic_fragment_structure_changed():
    frag_html = """
    <div class="list">
      <img src="/img1.gif" title="서예가1" class="other_class">
      <img src="/img2.gif" title="서예가2">
    </div>
    """
    with pytest.raises(CursiveException) as excinfo:
        parse_zdic_fragment(frag_html)
    assert excinfo.value.kind == CursiveErrorKind.BAD_RESPONSE
