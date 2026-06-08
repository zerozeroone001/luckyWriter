from typing import List, Dict, Any
import json


class ContextManager:
    """上下文管理服务：处理长文本的上下文压缩和摘要"""

    def __init__(self, max_context_length: int = 8000):
        """
        Args:
            max_context_length: 最大上下文长度（字符数）
        """
        self.max_context_length = max_context_length

    def truncate_context(
        self,
        recent_chapters: List[str],
        full_context_window: int = 3,
    ) -> str:
        """
        滑动窗口截断：保留最近N章完整内容

        Args:
            recent_chapters: 章节列表（按时间倒序）
            full_context_window: 保留完整内容的章节数

        Returns:
            str: 截断后的上下文
        """
        if not recent_chapters:
            return ""

        # 保留最近N章的完整内容
        recent_full = recent_chapters[:full_context_window]
        context = "\n\n".join(recent_full)

        return context

    def summarize_distant_context(
        self,
        chapters: List[Dict[str, Any]],
    ) -> str:
        """
        生成远期章节的摘要（用于AI调用前的提示词准备）

        Args:
            chapters: 章节列表，每个章节包含 title 和 content

        Returns:
            str: 摘要文本
        """
        summaries = []

        for chapter in chapters:
            title = chapter.get("title", "未命名章节")
            content = chapter.get("content", "")

            # 简单提取：取前200字作为摘要
            summary = content[:200] + "..." if len(content) > 200 else content
            summaries.append(f"【{title}】{summary}")

        return "\n".join(summaries)

    def build_hierarchical_context(
        self,
        novel_info: Dict[str, Any],
        outline: str,
        character_cards: List[Dict[str, Any]],
        recent_chapters: List[str],
        distant_summary: str = "",
    ) -> str:
        """
        构建分层上下文：小说信息 -> 大纲 -> 角色 -> 远期摘要 -> 近期完整

        Args:
            novel_info: 小说基本信息
            outline: 大纲内容
            character_cards: 角色卡列表
            recent_chapters: 最近章节（完整内容）
            distant_summary: 远期章节摘要

        Returns:
            str: 完整的分层上下文
        """
        context_parts = []

        # 1. 小说基本信息
        if novel_info:
            context_parts.append(f"【小说信息】")
            context_parts.append(f"标题：{novel_info.get('title', '')}")
            context_parts.append(f"类型：{novel_info.get('genre', '')}")
            context_parts.append(f"简介：{novel_info.get('synopsis', '')}")
            context_parts.append("")

        # 2. 大纲
        if outline:
            context_parts.append(f"【大纲】")
            context_parts.append(outline)
            context_parts.append("")

        # 3. 角色卡（主要角色）
        if character_cards:
            context_parts.append(f"【主要角色】")
            for char in character_cards[:5]:  # 只取前5个主要角色
                context_parts.append(f"- {char.get('name', '')}：{char.get('identity_info', '')[:100]}")
            context_parts.append("")

        # 4. 远期章节摘要
        if distant_summary:
            context_parts.append(f"【前情回顾】")
            context_parts.append(distant_summary)
            context_parts.append("")

        # 5. 最近章节完整内容
        if recent_chapters:
            context_parts.append(f"【最近章节】")
            context_parts.append("\n\n".join(recent_chapters))

        full_context = "\n".join(context_parts)

        # 如果超出最大长度，进行智能截断
        if len(full_context) > self.max_context_length:
            full_context = full_context[:self.max_context_length] + "\n[上下文已截断...]"

        return full_context

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        提取文本关键词（简单实现，可用jieba优化）

        Args:
            text: 文本内容
            top_n: 返回关键词数量

        Returns:
            List[str]: 关键词列表
        """
        # 简单实现：提取高频词（排除常见停用词）
        stopwords = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "着", "来", "也"}

        # 简单分词（按标点和空格）
        import re
        words = re.findall(r'[一-龥]+', text)

        # 统计词频
        word_freq = {}
        for word in words:
            if len(word) >= 2 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # 排序返回Top N
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]


# 全局上下文管理实例
context_manager = ContextManager()
