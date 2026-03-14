from bs4 import BeautifulSoup

from wechat_article_to_markdown import (
    convert_to_markdown,
    replace_image_urls,
)
from platforms.wechat import WeChatAdapter


def test_wechat_extract_publish_time_supports_multiple_patterns() -> None:
    ts = 1700000000
    expected = WeChatAdapter._format_timestamp(ts)

    assert WeChatAdapter._extract_publish_time(f"create_time:'{ts}'") == expected
    assert WeChatAdapter._extract_publish_time(f'create_time:"{ts}"') == expected
    assert WeChatAdapter._extract_publish_time(f"create_time = {ts}") == expected
    assert WeChatAdapter._extract_publish_time(f"create_time:JsDecode('{ts}')") == expected


def test_replace_image_urls_handles_parentheses() -> None:
    md = (
        "![](https://example.com/a_(1).png)\n"
        "![alt](https://example.com/b.png?x=1&y=2)"
    )
    url_map = {
        "https://example.com/a_(1).png": "images/a.png",
        "https://example.com/b.png?x=1&y=2": "images/b.png",
    }

    out = replace_image_urls(md, url_map)
    assert "![](images/a.png)" in out
    assert "![alt](images/b.png)" in out


def test_wechat_process_content_extracts_code_and_images() -> None:
    html = """
    <div id="js_content">
      <img data-src="https://example.com/1.png" />
      <img src="https://example.com/1.png" />
      <div class="code-snippet__fix">
        <pre data-lang="python"></pre>
        <code>print('hello')</code>
      </div>
      <script>bad()</script>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    content_html, code_blocks, img_urls = WeChatAdapter.process_content(soup)

    assert "script" not in content_html
    assert img_urls == ["https://example.com/1.png"]
    assert code_blocks == [{"lang": "python", "code": "print('hello')"}]


def test_convert_to_markdown_restores_code_block() -> None:
    html = "<p>before</p><p>CODEBLOCK-PLACEHOLDER-0</p><p>after</p>"
    md = convert_to_markdown(html, [{"lang": "python", "code": "print(1)"}])

    assert "```python" in md
    assert "print(1)" in md
    assert "CODEBLOCK-PLACEHOLDER-0" not in md


def test_zhihu_adapter_matches_urls() -> None:
    from platforms.zhihu import ZhihuAdapter

    assert ZhihuAdapter.match("https://zhuanlan.zhihu.com/p/123456")
    assert ZhihuAdapter.match("https://www.zhihu.com/question/123/answer/456")
    assert not ZhihuAdapter.match("https://mp.weixin.qq.com/s/xxx")


def test_wechat_adapter_matches_urls() -> None:
    assert WeChatAdapter.match("https://mp.weixin.qq.com/s/xxx")
    assert not WeChatAdapter.match("https://zhuanlan.zhihu.com/p/123456")


def test_zhihu_article_extract_metadata() -> None:
    from platforms.zhihu import ZhihuAdapter

    html = """
    <html>
    <h1 class="Post-Title">Test Article Title</h1>
    <div class="AuthorInfo-name">Test Author</div>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    url = "https://zhuanlan.zhihu.com/p/123456"

    meta = ZhihuAdapter.extract_metadata(soup, html, url)
    assert meta["title"] == "Test Article Title"
    assert meta["author"] == "Test Author"


def test_zhihu_question_extract_metadata() -> None:
    from platforms.zhihu import ZhihuAdapter

    html = """
    <html>
    <h1 class="QuestionHeader-title">Test Question Title</h1>
    <div class="AuthorInfo-name">Test Answerer</div>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    url = "https://www.zhihu.com/question/123/answer/456"

    meta = ZhihuAdapter.extract_metadata(soup, html, url)
    assert meta["title"] == "Test Question Title"
    assert meta["author"] == "Test Answerer"