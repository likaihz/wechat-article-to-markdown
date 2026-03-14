from __future__ import annotations

# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "camoufox[geoip]",
#     "markdownify",
#     "beautifulsoup4",
#     "httpx",
# ]
# ///

"""
Article to Markdown — 文章抓取 & Markdown 转换工具

支持平台：
- 微信公众号 (mp.weixin.qq.com)
- 知乎问答 (zhihu.com/question/.../answer/...)
- 知乎专栏 (zhuanlan.zhihu.com/p/...)

使用 Camoufox (反检测浏览器) + BeautifulSoup + markdownify 将文章
转换为干净的 Markdown 文件，图片自动下载到本地。
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

import httpx
import markdownify
from bs4 import BeautifulSoup
from camoufox.async_api import AsyncCamoufox

from platforms import get_adapter

# Default output directory (can be overridden via CLI --output)
OUTPUT_DIR = Path.cwd() / "output"
IMAGE_CONCURRENCY = 5


# ============================================================
# Image Downloading
# ============================================================


async def download_image(
    client: httpx.AsyncClient,
    img_url: str,
    img_dir: Path,
    index: int,
    semaphore: asyncio.Semaphore,
    referer: str = "",
) -> tuple[str, str | None]:
    """下载单张图片到本地，返回 (remote_url, local_relative_path | None)"""
    async with semaphore:
        try:
            url = img_url if not img_url.startswith("//") else f"https:{img_url}"

            # 推断扩展名
            ext_match = re.search(r"wx_fmt=(\w+)", url) or re.search(
                r"\.(\w{3,4})(?:\?|$)", url
            )
            ext = ext_match.group(1) if ext_match else "png"

            filename = f"img_{index:03d}.{ext}"
            filepath = img_dir / filename

            headers = {"Referer": referer} if referer else {}
            resp = await client.get(
                url,
                headers=headers,
                timeout=15.0,
            )
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
            return img_url, f"images/{filename}"
        except Exception as e:
            print(f"  ⚠ 图片下载失败: {e}")
            return img_url, None


async def download_all_images(
    img_urls: list[str],
    img_dir: Path,
    referer: str = "",
) -> dict[str, str]:
    """并发下载所有图片，返回 {remote_url: local_path} 映射"""
    if not img_urls:
        return {}

    print(f"🖼  下载 {len(img_urls)} 张图片 (并发 {IMAGE_CONCURRENCY})...")
    semaphore = asyncio.Semaphore(IMAGE_CONCURRENCY)

    async with httpx.AsyncClient() as client:
        tasks = [
            download_image(client, url, img_dir, i + 1, semaphore, referer)
            for i, url in enumerate(img_urls)
        ]
        results = await asyncio.gather(*tasks)

    url_map = {}
    for remote_url, local_path in results:
        if local_path:
            url_map[remote_url] = local_path

    downloaded = sum(1 for v in url_map.values() if v)
    print(f"  ✅ {downloaded}/{len(img_urls)}")
    return url_map


# ============================================================
# Content Processing
# ============================================================


def convert_to_markdown(content_html: str, code_blocks: list[dict]) -> str:
    """HTML -> Markdown，还原代码块，清理格式"""
    md = markdownify.markdownify(
        content_html,
        heading_style="ATX",
        bullets="-",
        convert=["p", "h1", "h2", "h3", "h4", "h5", "h6",
                 "strong", "em", "a", "img", "ul", "ol", "li",
                 "blockquote", "br", "hr", "table", "thead",
                 "tbody", "tr", "th", "td", "pre", "code"],
    )

    # 还原代码块占位符
    for i, block in enumerate(code_blocks):
        placeholder = f"CODEBLOCK-PLACEHOLDER-{i}"
        fenced = f"\n```{block['lang']}\n{block['code']}\n```\n"
        md = md.replace(placeholder, fenced)

    # 清理 &nbsp; 残留
    md = md.replace("\u00a0", " ")
    # 清理多余空行
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    # 清理行尾多余空格
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)

    return md


def replace_image_urls(md: str, url_map: dict[str, str]) -> str:
    """替换 Markdown 中的远程图片链接为本地路径"""
    # Use exact URL matching to avoid regex edge cases such as ')' in URL.
    for remote_url, local_path in url_map.items():
        pattern = re.compile(r"!\[([^\]]*)\]\(" + re.escape(remote_url) + r"\)")
        md = pattern.sub(lambda m: f"![{m.group(1)}]({local_path})", md)
    return md


def build_markdown(meta: dict, body_md: str) -> str:
    """拼接最终 Markdown 文件内容"""
    lines = [f"# {meta['title']}", ""]
    if meta.get("author"):
        author_label = meta.get("author_label", "作者")
        lines.append(f"> {author_label}: {meta['author']}")
    if meta.get("publish_time"):
        lines.append(f"> 发布时间: {meta['publish_time']}")
    if meta.get("source_url"):
        lines.append(f"> 原文链接: {meta['source_url']}")
    if meta.get("author") or meta.get("publish_time") or meta.get("source_url"):
        lines.append("")
    lines.extend(["---", ""])
    return "\n".join(lines) + body_md


# ============================================================
# Main
# ============================================================


async def fetch_article(url: str) -> None:
    print(f"🔄 正在抓取: {url}")

    # 获取平台适配器
    adapter_cls = get_adapter(url)
    if not adapter_cls:
        print("❌ 不支持的平台，目前支持：微信公众号、知乎")
        sys.exit(1)

    print(f"📋 平台: {adapter_cls.get_platform_name()}")

    # 使用 Camoufox 反检测浏览器获取完整 HTML
    print("🦊 启动 Camoufox 浏览器...")
    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        # 等待正文加载
        try:
            await page.wait_for_selector(adapter_cls.get_content_selector(), timeout=10000)
        except Exception:
            pass  # 超时也继续尝试解析
        # 额外等待确保 JS 执行完毕
        await asyncio.sleep(2)
        html = await page.content()

    # 解析
    soup = BeautifulSoup(html, "html.parser")

    # 提取元数据
    meta = adapter_cls.extract_metadata(soup, html, url)
    if not meta["title"]:
        print("❌ 未能提取到文章标题，可能触发了验证码")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / "debug.html").write_text(html, encoding="utf-8")
        print("已保存原始 HTML 到 output/debug.html")
        sys.exit(1)

    meta["source_url"] = url
    print(f"📄 标题: {meta['title']}")
    if meta.get("author"):
        print(f"👤 作者: {meta['author']}")

    # 处理正文
    content_html, code_blocks, img_urls = adapter_cls.process_content(soup, url)
    if not content_html:
        print("❌ 未能提取到正文内容")
        sys.exit(1)

    # 转 Markdown
    md = convert_to_markdown(content_html, code_blocks)

    # 下载图片
    safe_title = re.sub(r'[/\\?%*:|"<>]', "_", meta["title"])[:80]
    article_dir = OUTPUT_DIR / safe_title
    img_dir = article_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    referer = adapter_cls.get_image_referer(url)
    url_map = await download_all_images(img_urls, img_dir, referer)
    md = replace_image_urls(md, url_map)

    # 写入文件
    result = build_markdown(meta, md)
    md_path = article_dir / f"{safe_title}.md"
    md_path.write_text(result, encoding="utf-8")

    print(f"✅ 已保存: {md_path}")
    print(f"📊 Markdown 约 {len(md)} 字符")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch articles and convert to Markdown"
    )
    parser.add_argument(
        "url",
        help="Article URL (微信/知乎)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory (default: ./output)",
    )
    args = parser.parse_args()

    url = args.url

    # 检测平台
    adapter_cls = get_adapter(url)
    if not adapter_cls:
        print("❌ 不支持的平台")
        print("支持的平台：")
        print("  - 微信公众号: https://mp.weixin.qq.com/s/...")
        print("  - 知乎问答: https://www.zhihu.com/question/.../answer/...")
        print("  - 知乎专栏: https://zhuanlan.zhihu.com/p/...")
        sys.exit(1)

    # Set output directory
    global OUTPUT_DIR
    if args.output:
        OUTPUT_DIR = args.output.expanduser().resolve()

    try:
        asyncio.run(fetch_article(url))
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()