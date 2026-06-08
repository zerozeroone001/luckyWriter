from typing import List, Tuple
import re
from config import settings


class ContentFilter:
    """内容过滤服务"""

    def __init__(self):
        self.keywords = settings.FILTER_KEYWORDS

    def contains_sensitive_content(self, text: str) -> Tuple[bool, List[str]]:
        """
        检查文本是否包含敏感内容

        Args:
            text: 待检查文本

        Returns:
            Tuple[bool, List[str]]: (是否包含敏感内容, 匹配到的关键词列表)
        """
        matched_keywords = []

        for keyword in self.keywords:
            if keyword in text:
                matched_keywords.append(keyword)

        return len(matched_keywords) > 0, matched_keywords

    def filter_text(self, text: str, replacement: str = "***") -> str:
        """
        过滤文本中的敏感内容

        Args:
            text: 待过滤文本
            replacement: 替换字符

        Returns:
            str: 过滤后的文本
        """
        filtered_text = text

        for keyword in self.keywords:
            if keyword in filtered_text:
                filtered_text = filtered_text.replace(keyword, replacement)

        return filtered_text


# 全局内容过滤实例
content_filter = ContentFilter()
