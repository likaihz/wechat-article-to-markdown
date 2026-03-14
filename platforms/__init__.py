from __future__ import annotations

from .base import PlatformAdapter
from .wechat import WeChatAdapter
from .zhihu import ZhihuAdapter

__all__ = ["PlatformAdapter", "WeChatAdapter", "ZhihuAdapter"]

# 所有可用的平台适配器列表
ADAPTERS: list[type[PlatformAdapter]] = [
    WeChatAdapter,
    ZhihuAdapter,
]


def get_adapter(url: str) -> type[PlatformAdapter] | None:
    """根据 URL 获取匹配的平台适配器"""
    for adapter in ADAPTERS:
        if adapter.match(url):
            return adapter
    return None