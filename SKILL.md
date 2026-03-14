---
name: wechat-article-to-markdown
description: Fetch articles from WeChat Official Account (微信公众号) or Zhihu (知乎) and convert to Markdown. 微信/知乎文章转 Markdown 工具。
author: jackwener
version: "1.1.0"
tags:
  - wechat
  - 微信
  - 微信文章
  - 公众号
  - mp.weixin.qq.com
  - zhihu
  - 知乎
  - zhuanlan.zhihu.com
  - markdown
  - article
  - converter
  - cli
---

# Article to Markdown

Fetch an article from WeChat or Zhihu and convert it to a clean Markdown file.

## When to use

Use this skill when you need to save articles as Markdown for:
- Personal archive
- AI summarization input
- Knowledge base ingestion

## Prerequisites

- Python 3.8+

```bash
# Install
uv tool install wechat-article-to-markdown
# Or: pipx install wechat-article-to-markdown
```

## Usage

```bash
wechat-article-to-markdown "<ARTICLE_URL>"
```

Options:
- `-o, --output <dir>` - Specify output directory (default: `./output`)

## Supported Platforms

| Platform | URL Pattern |
|----------|-------------|
| 微信公众号 | `https://mp.weixin.qq.com/s/...` |
| 知乎专栏 | `https://zhuanlan.zhihu.com/p/...` |
| 知乎问答 | `https://www.zhihu.com/question/.../answer/...` |

Output files:
- `<output-dir>/<article-title>/<article-title>.md`
- `<output-dir>/<article-title>/images/*`

Default output directory: `./output`

## Features

1. Multi-platform support: WeChat, Zhihu (articles & Q&A)
2. Anti-detection fetch with Camoufox
3. Metadata extraction (title, author name, source URL)
4. Image localization to local files
5. Code block extraction with language fences
6. HTML to Markdown conversion via markdownify
7. Concurrent image downloading

## Limitations

- Some code snippets are image/SVG rendered and cannot be extracted as source code
- Zhihu publish time is not extracted (difficult to parse)
- Zhihu anti-bot detection may block requests in some cases