# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx"
uv run wechat-article-to-markdown "https://zhuanlan.zhihu.com/p/xxxxxxxx"
uv run wechat-article-to-markdown "https://www.zhihu.com/question/xxx/answer/xxx"

# Specify output directory
uv run wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx" -o ./my-articles

# Backward-compatible entry point
uv run main.py "https://mp.weixin.qq.com/s/xxxxxxxx"

# Run unit tests (default CI path, no network required)
uv run --with pytest pytest -q -m "not e2e"

# Run E2E tests against live articles
WECHAT_E2E_URLS="https://mp.weixin.qq.com/s/xxx,https://mp.weixin.qq.com/s/yyy" \
  uv run --with pytest pytest -q -m e2e -s

# Build package
uv build
```

## Architecture

Platform adapter pattern with three layers:

```
wechat_article_to_markdown.py  # Main entry, platform detection & routing
platforms/
  __init__.py                  # Adapter registry & get_adapter()
  base.py                      # PlatformAdapter abstract base class
  wechat.py                    # WeChat Official Account adapter
  zhihu.py                     # Zhihu adapter (questions + articles)
```

### PlatformAdapter Interface

Each platform implements:
- `match(url)` - Detect if URL belongs to this platform
- `get_content_selector()` - CSS selector for main content container
- `extract_metadata(soup, html, url)` - Extract title, author, publish_time
- `process_content(soup, url)` - Process HTML, return (html, code_blocks, img_urls)
- `get_image_referer(url)` - Referer header for image downloads

### Processing Pipeline

1. **Fetch** - `fetch_article()` uses Camoufox (anti-detection browser) to get HTML
2. **Detect** - `get_adapter(url)` selects appropriate platform adapter
3. **Process** - Adapter extracts metadata and processes content
4. **Convert** - `convert_to_markdown()` uses markdownify
5. **Download** - `download_all_images()` localizes images concurrently

Output structure: `output/<article-title>/<article-title>.md` + `output/<article-title>/images/`

## Supported Platforms

| Platform | URL Pattern | Content Selector |
|----------|-------------|------------------|
| 微信公众号 | `mp.weixin.qq.com/s/...` | `#js_content` |
| 知乎专栏 | `zhuanlan.zhihu.com/p/...` | `.Post-RichText` |
| 知乎问答 | `zhihu.com/question/.../answer/...` | `.RichContent-inner` |

## Key Dependencies

- **Camoufox** - Anti-detection browser (headless Firefox variant)
- **BeautifulSoup** - HTML parsing
- **markdownify** - HTML to Markdown conversion
- **httpx** - Async HTTP for concurrent image downloads

## Testing

- Unit tests (`tests/test_core.py`) - Test parsing/conversion logic, no network required
- E2E tests (`tests/test_e2e_live.py`) - Live fetch against real URLs, requires `WECHAT_E2E_URLS` env var

E2E tests run via manual GitHub Actions workflow (`.github/workflows/e2e.yml`), not in CI.

## Adding New Platforms

1. Create `platforms/<name>.py` extending `PlatformAdapter`
2. Implement all abstract methods
3. Add adapter to `platforms/__init__.py` `ADAPTERS` list
4. Add tests to `tests/test_core.py`
5. Update documentation (README.md, SKILL.md)