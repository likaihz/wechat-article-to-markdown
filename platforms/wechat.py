from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import PlatformAdapter


class WeChatAdapter(PlatformAdapter):
    """微信公众号文章适配器"""

    @classmethod
    def match(cls, url: str) -> bool:
        return url.startswith("https://mp.weixin.qq.com/")

    @classmethod
    def get_content_selector(cls) -> str:
        return "#js_content"

    @classmethod
    def get_image_referer(cls) -> str:
        return "https://mp.weixin.qq.com/"

    @classmethod
    def extract_metadata(cls, soup: BeautifulSoup, html: str) -> dict:
        """提取文章元数据: 标题、作者、发布时间"""
        title_el = soup.select_one("#activity-name")
        author_el = soup.select_one("#js_name")
        return {
            "title": title_el.get_text(strip=True) if title_el else "",
            "author": author_el.get_text(strip=True) if author_el else "",
            "publish_time": cls._extract_publish_time(html),
        }

    @classmethod
    def _extract_publish_time(cls, html: str) -> str:
        """从 HTML script 标签中提取发布时间"""
        # JsDecode 格式
        m = re.search(r"create_time\s*:\s*JsDecode\('([^']+)'\)", html)
        if m:
            val = m.group(1)
            try:
                ts = int(val)
                if ts > 0:
                    return cls._format_timestamp(ts)
            except ValueError:
                return val

        # 纯数字格式
        m = re.search(r"create_time\s*:\s*'(\d+)'", html)
        if m:
            return cls._format_timestamp(int(m.group(1)))

        # 兼容双引号与 = 赋值风格
        m = re.search(r'create_time\s*[:=]\s*["\']?(\d+)["\']?', html)
        if m:
            return cls._format_timestamp(int(m.group(1)))

        return ""

    @classmethod
    def _format_timestamp(cls, ts: int) -> str:
        """Unix timestamp (秒) -> 'YYYY-MM-DD HH:mm:ss' (Asia/Shanghai, UTC+8)"""
        from datetime import datetime, timezone, timedelta

        tz = timezone(timedelta(hours=8))
        dt = datetime.fromtimestamp(ts, tz=tz)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def process_content(cls, soup: BeautifulSoup) -> tuple[str, list[dict], list[str]]:
        """
        预处理正文 DOM：修复图片、处理代码块、移除噪声元素。
        返回 (content_html, code_blocks, img_urls)
        """
        content_el = soup.select_one("#js_content")
        if not content_el:
            return "", [], []

        # 1) 图片: data-src -> src (微信懒加载)
        for img in content_el.find_all("img"):
            data_src = img.get("data-src")
            if data_src:
                img["src"] = data_src

        # 2) 代码块: 提取 code-snippet__fix 内容，替换为占位符
        code_blocks = []
        for el in content_el.select(".code-snippet__fix"):
            # 移除行号
            for line_idx in el.select(".code-snippet__line-index"):
                line_idx.decompose()

            pre = el.select_one("pre[data-lang]")
            lang = pre.get("data-lang", "") if pre else ""

            lines = []
            for code_tag in el.find_all("code"):
                text = code_tag.get_text()
                # 跳过 CSS counter 泄漏的垃圾行
                if re.match(r"^[ce]?ounter\(line", text):
                    continue
                lines.append(text)

            if not lines:
                lines.append(el.get_text())

            placeholder = f"CODEBLOCK-PLACEHOLDER-{len(code_blocks)}"
            code_blocks.append({"lang": lang, "code": "\n".join(lines)})
            el.replace_with(soup.new_tag("p", string=placeholder))

        # 3) 移除噪声元素
        for sel in ("script", "style", ".qr_code_pc", ".reward_area"):
            for tag in content_el.select(sel):
                tag.decompose()

        # 4) 收集图片 URL（去重）
        img_urls = []
        seen = set()
        for img in content_el.find_all("img", src=True):
            src = img["src"]
            if src not in seen:
                seen.add(src)
                img_urls.append(src)

        return str(content_el), code_blocks, img_urls