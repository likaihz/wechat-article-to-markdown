# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the tool
uv run wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx"

# Specify output directory
uv run wechat-article-to-markdown "https://mp.weixin.qq.com/s/xxxxxxxx" -o ./my-articles

# Backward-compatible entry point
uv run main.py "https://mp.weixin.qq.com/s/xxxxxxxx"

# Run unit tests (default CI path, no network required)
uv run --with pytest pytest -q -m "not e2e"

# Run E2E tests against live WeChat articles
WECHAT_E2E_URLS="https://mp.weixin.qq.com/s/xxx,https://mp.weixin.qq.com/s/yyy" \
  uv run --with pytest pytest -q -m e2e -s

# Build package
uv build
```

## Architecture

Single-file Python tool (`wechat_article_to_markdown.py`) with three processing stages:

1. **Fetch** - `fetch_article()` uses Camoufox (anti-detection browser) to get HTML, bypassing WeChat's bot detection
2. **Process** - `process_content()` extracts code blocks, fixes lazy-loaded images (`data-src` → `src`), removes noise
3. **Convert** - `convert_to_markdown()` uses markdownify, `download_all_images()` localizes images concurrently

Output structure: `output/<article-title>/<article-title>.md` + `output/<article-title>/images/`

## Key Dependencies

- **Camoufox** - Anti-detection browser (headless Firefox variant)
- **BeautifulSoup** - HTML parsing
- **markdownify** - HTML to Markdown conversion
- **httpx** - Async HTTP for concurrent image downloads

## Testing

- Unit tests (`tests/test_core.py`) - Test parsing/conversion logic, no network required
- E2E tests (`tests/test_e2e_live.py`) - Live fetch against real URLs, requires `WECHAT_E2E_URLS` env var

E2E tests run via manual GitHub Actions workflow (`.github/workflows/e2e.yml`), not in CI.

## Skill Integration

This project is also distributed as an AI agent skill. `SKILL.md` describes the tool for AI agents. Changes to core functionality should update both README.md and SKILL.md.