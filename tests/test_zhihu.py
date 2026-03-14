"""
Integration tests for Zhihu adapter using local HTML fixtures.

Since Zhihu has strong anti-bot protection, these tests use saved HTML files.
To update fixtures, manually save pages from your browser:
1. Open the URL in browser
2. Right-click -> Save Page As -> HTML only
3. Save to tests/fixtures/
"""
import pytest
from pathlib import Path
from bs4 import BeautifulSoup

from platforms.zhihu import ZhihuAdapter
from wechat_article_to_markdown import convert_to_markdown, build_markdown

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def zhihu_article_html():
    """Load Zhihu article fixture if available."""
    path = FIXTURES_DIR / "zhihu-article.html"
    if not path.exists():
        pytest.skip(f"Fixture not found: {path}. Save HTML from browser to run this test.")
    return path.read_text(encoding="utf-8")


@pytest.fixture
def zhihu_question_html():
    """Load Zhihu question fixture if available."""
    path = FIXTURES_DIR / "zhihu-question.html"
    if not path.exists():
        pytest.skip(f"Fixture not found: {path}. Save HTML from browser to run this test.")
    return path.read_text(encoding="utf-8")


def test_zhihu_article_extraction(zhihu_article_html):
    """Test extracting Zhihu article (zhuanlan) content."""
    url = "https://zhuanlan.zhihu.com/p/384158529"
    soup = BeautifulSoup(zhihu_article_html, "html.parser")

    # Test adapter matching
    assert ZhihuAdapter.match(url)

    # Test metadata extraction
    meta = ZhihuAdapter.extract_metadata(soup, zhihu_article_html, url)
    assert meta["title"], "Should extract title"
    assert len(meta["title"]) > 5, "Title should be meaningful"
    print(f"Title: {meta['title']}")
    print(f"Author: {meta['author']}")

    # Test content extraction
    content_html, code_blocks, img_urls = ZhihuAdapter.process_content(soup, url)
    assert content_html, "Should extract content"

    # Test markdown conversion
    md = convert_to_markdown(content_html, code_blocks)
    assert len(md) > 100, "Markdown should have substantial content"
    print(f"Markdown length: {len(md)} chars")
    print(f"Images: {len(img_urls)}")

    # Test full output
    meta["source_url"] = url
    full_md = build_markdown(meta, md)
    assert meta["title"] in full_md
    assert url in full_md


def test_zhihu_question_extraction(zhihu_question_html):
    """Test extracting Zhihu question/answer content."""
    url = "https://www.zhihu.com/question/1999842555244860056/answer/2009895179386130858"
    soup = BeautifulSoup(zhihu_question_html, "html.parser")

    # Test adapter matching
    assert ZhihuAdapter.match(url)

    # Test metadata extraction
    meta = ZhihuAdapter.extract_metadata(soup, zhihu_question_html, url)
    assert meta["title"], "Should extract question title"
    print(f"Title: {meta['title']}")
    print(f"Author: {meta['author']}")

    # Test content extraction
    content_html, code_blocks, img_urls = ZhihuAdapter.process_content(soup, url)
    assert content_html, "Should extract answer content"

    # Test markdown conversion
    md = convert_to_markdown(content_html, code_blocks)
    assert len(md) > 50, "Markdown should have content"

    # Test full output
    meta["source_url"] = url
    full_md = build_markdown(meta, md)
    assert meta["title"] in full_md


def test_zhihu_url_matching():
    """Test Zhihu URL pattern matching."""
    # Should match
    assert ZhihuAdapter.match("https://zhuanlan.zhihu.com/p/123456")
    assert ZhihuAdapter.match("https://www.zhihu.com/question/123/answer/456")
    assert ZhihuAdapter.match("https://zhihu.com/question/123/answer/456")

    # Should not match
    assert not ZhihuAdapter.match("https://mp.weixin.qq.com/s/xxx")
    assert not ZhihuAdapter.match("https://example.com/article")


def test_zhihu_page_type_detection():
    """Test detecting Zhihu page type from URL."""
    article_url = "https://zhuanlan.zhihu.com/p/384158529"
    question_url = "https://www.zhihu.com/question/123/answer/456"

    assert ZhihuAdapter._get_page_type(article_url) == ZhihuAdapter.TYPE_ARTICLE
    assert ZhihuAdapter._get_page_type(question_url) == ZhihuAdapter.TYPE_QUESTION


def test_zhihu_image_referer():
    """Test correct Referer header for different Zhihu pages."""
    article_url = "https://zhuanlan.zhihu.com/p/123"
    question_url = "https://www.zhihu.com/question/123/answer/456"

    assert ZhihuAdapter.get_image_referer(article_url) == "https://zhuanlan.zhihu.com/"
    assert ZhihuAdapter.get_image_referer(question_url) == "https://www.zhihu.com/"