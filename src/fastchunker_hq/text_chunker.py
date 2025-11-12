# -*- coding: utf-8 -*-
"""
通用文本分块器模块
提供智能文本分块功能，适用于任何纯文本内容
"""

import re
import json
import os
from typing import List

from fastchunker_hq.base import BaseChunker


class TextChunker(BaseChunker):
    """通用文本分块器 - 适用于任何纯文本"""

    def __init__(self, max_size: int = 1500, min_size: int = 300):
        """
        初始化文本分块器

        Args:
            max_size: 单个块的最大字符数
            min_size: 单个块的最小字符数
        """
        super().__init__(max_size, min_size)

        # 句子结束符的正则（支持中英文）
        self.sentence_pattern = re.compile(r'[.!?。！？]+["\']?\s*')

    def chunk(self, text: str) -> List[str]:
        """
        核心分块方法: 将长文本智能分割成多个语义完整的块

        处理流程:
            1. 预处理: 统一换行符格式，清理多余空白
            2. 按段落分割: 根据双换行将文本分成多个段落
            3. 按大小分块: 将段落组合成合适大小的块
            4. 合并短块: 将过短的 chunk 与相邻块合并

        Args:
            text: 待分块的纯文本

        Returns:
            List[str]: 分块后的文本列表

        Examples:
            >>> chunker = TextChunker(max_size=1000, min_size=300)
            >>> chunks = chunker.chunk(long_text)
        """
        # 1. 预处理
        text = self._preprocess(text)

        # 2. 按段落分割
        paragraphs = self._split_by_paragraphs(text)

        # 3. 组装成chunks
        chunks = self._build_chunks(paragraphs)

        # 4. 合并过短的chunks
        chunks = self._merge_short(chunks)

        return chunks

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """
        按段落分割文本
        - 双换行作为段落分隔符
        - 过滤空段落
        """
        paragraphs = re.split(r'\n\s*\n', text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _build_chunks(self, paragraphs: List[str]) -> List[str]:
        """
        将段落组装成大小合适的chunks

        策略:
            - 优先按段落保持语义完整性
            - 如果单个段落过长，按句子分割
            - 控制每个chunk在 max_size 范围内
        """
        chunks = []
        current = ""

        for para in paragraphs:
            # 如果段落本身就超过max_size，需要进一步分割
            if len(para) > self.max_size:
                # 先保存当前累积的内容
                if current:
                    chunks.append(current)
                    current = ""

                # 按句子分割超长段落
                sub_chunks = self._split_by_sentences(para)
                chunks.extend(sub_chunks)
                continue

            # 检查是否需要新chunk
            if current and len(current) + len(para) + 2 > self.max_size:
                chunks.append(current)
                current = para
            else:
                current = current + "\n\n" + para if current else para

        # 添加最后一个chunk
        if current:
            chunks.append(current)

        return chunks

    def _split_by_sentences(self, text: str) -> List[str]:
        """
        按句子分割过长的文本

        Args:
            text: 需要分割的文本

        Returns:
            List[str]: 分割后的文本块列表
        """
        # 使用句子分隔符分割
        sentences = self.sentence_pattern.split(text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current = ""

        for sentence in sentences:
            # 如果单个句子就超过max_size，直接作为一个chunk
            if len(sentence) > self.max_size:
                if current:
                    chunks.append(current)
                    current = ""
                chunks.append(sentence)
                continue

            # 检查是否需要新chunk
            if current and len(current) + len(sentence) + 1 > self.max_size:
                chunks.append(current)
                current = sentence
            else:
                current = current + " " + sentence if current else sentence

        if current:
            chunks.append(current)

        return chunks

