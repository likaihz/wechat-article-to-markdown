from __future__ import annotations

from abc import ABC, abstractmethod

from bs4 import BeautifulSoup


class PlatformAdapter(ABC):
    """平台适配器抽象基类"""

    @classmethod
    @abstractmethod
    def match(cls, url: str) -> bool:
        """检测 URL 是否匹配此平台"""
        pass

    @classmethod
    @abstractmethod
    def get_content_selector(cls) -> str:
        """返回正文容器的 CSS 选择器，用于等待加载"""
        pass

    @classmethod
    @abstractmethod
    def extract_metadata(cls, soup: BeautifulSoup, html: str) -> dict:
        """提取元数据：title, author, publish_time"""
        pass

    @classmethod
    @abstractmethod
    def process_content(cls, soup: BeautifulSoup) -> tuple[str, list[dict], list[str]]:
        """处理正文，返回 (content_html, code_blocks, img_urls)"""
        pass

    @classmethod
    def get_image_referer(cls) -> str:
        """下载图片时使用的 Referer"""
        return ""

    @classmethod
    def get_platform_name(cls) -> str:
        """返回平台名称，用于显示"""
        return cls.__name__.replace("Adapter", "")