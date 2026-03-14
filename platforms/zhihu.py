from __future__ import annotations

import re

from bs4 import BeautifulSoup

from .base import PlatformAdapter


class ZhihuAdapter(PlatformAdapter):
    """知乎适配器：支持问答页面和专栏文章"""

    # 页面类型
    TYPE_QUESTION = "question"  # 问答页面
    TYPE_ARTICLE = "article"    # 专栏文章

    @classmethod
    def match(cls, url: str) -> bool:
        return (
            "zhihu.com/question/" in url or
            url.startswith("https://zhuanlan.zhihu.com/p/")
        )

    @classmethod
    def _get_page_type(cls, url: str) -> str:
        """判断页面类型"""
        if "zhihu.com/question/" in url:
            return cls.TYPE_QUESTION
        return cls.TYPE_ARTICLE

    @classmethod
    def get_content_selector(cls) -> str:
        """返回正文容器的 CSS 选择器"""
        # 返回多个选择器，用于等待加载
        return ".RichText, .Post-RichText, .RichContent-inner"

    @classmethod
    def get_image_referer(cls, url: str = "") -> str:
        """下载图片时使用的 Referer"""
        if "zhuanlan.zhihu.com" in url:
            return "https://zhuanlan.zhihu.com/"
        return "https://www.zhihu.com/"

    @classmethod
    def extract_metadata(cls, soup: BeautifulSoup, html: str, url: str = "") -> dict:
        """提取元数据：title, author, publish_time"""
        page_type = cls._get_page_type(url)

        if page_type == cls.TYPE_ARTICLE:
            return cls._extract_article_metadata(soup, html)
        return cls._extract_question_metadata(soup, html)

    @classmethod
    def _extract_article_metadata(cls, soup: BeautifulSoup, html: str) -> dict:
        """提取专栏文章元数据"""
        title_el = soup.select_one(".Post-Title")
        author_el = soup.select_one(".AuthorInfo-name")

        return {
            "title": title_el.get_text(strip=True) if title_el else "",
            "author": author_el.get_text(strip=True) if author_el else "",
            "publish_time": "",  # 知乎专栏文章的发布时间较难提取
        }

    @classmethod
    def _extract_question_metadata(cls, soup: BeautifulSoup, html: str) -> dict:
        """提取问答页面元数据"""
        # 问题标题
        title_el = soup.select_one(".QuestionHeader-title")
        # 回答作者
        author_el = soup.select_one(".AuthorInfo-name")

        return {
            "title": title_el.get_text(strip=True) if title_el else "",
            "author": author_el.get_text(strip=True) if author_el else "",
            "publish_time": "",  # 问答的回答时间较难提取
        }

    @classmethod
    def process_content(cls, soup: BeautifulSoup, url: str = "") -> tuple[str, list[dict], list[str]]:
        """
        处理正文，返回 (content_html, code_blocks, img_urls)
        """
        page_type = cls._get_page_type(url)

        # 查找内容容器
        content_el = (
            soup.select_one(".Post-RichText") or
            soup.select_one(".RichText") or
            soup.select_one(".RichContent-inner")
        )

        if not content_el:
            return "", [], []

        # 知乎的代码块是标准 <pre> 标签，markdownify 可以直接处理
        # 无需特殊处理

        # 移除噪声元素
        for sel in ("script", "style", ".RichContent-actions", ".ContentItem-actions"):
            for tag in content_el.select(sel):
                tag.decompose()

        # 收集图片 URL（去重）
        img_urls = []
        seen = set()
        for img in content_el.find_all("img", src=True):
            src = img["src"]
            # 跳过表情图片等小图
            if "zhimg.com" in src and "_xs." in src:
                continue
            if src not in seen:
                seen.add(src)
                img_urls.append(src)

        return str(content_el), [], img_urls