# -*- coding: utf-8 -*-
"""
分块器基类模块
提供所有分块器的通用功能和抽象接口
"""

import re
from abc import ABC, abstractmethod
from typing import List, Dict
from dataclasses import dataclass


@dataclass
class Chunk:
    """分块数据类"""
    text: str
    index: int


class BaseChunker(ABC):
    """分块器基类 - 定义所有分块器的通用接口和共享功能"""

    def __init__(self, max_size: int = 1000, min_size: int = 300):
        """
        初始化分块器

        Args:
            max_size: 单个块的最大字符数
            min_size: 单个块的最小字符数
        """
        self.max_size = max_size
        self.min_size = min_size

    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        """
        核心分块方法 - 子类必须实现

        Args:
            text: 待分块的文本

        Returns:
            List[str]: 分块后的文本列表
        """
        pass

    def _preprocess(self, text: str) -> str:
        """
        预处理: 标准化换行和空格
        - 统一换行符为 \\n
        - 把连续 >= 3 的换行变为两个
        - 去除首尾空白
        """
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _merge_short(self, chunks: List[str]) -> List[str]:
        """
        合并过短的chunks - 贪婪策略持续合并直到满足min_size

        策略:
            - 优先向后合并
            - 如果向后合并后仍不足，尝试与前一个合并
            - 确保合并后不超过 max_size
        """
        if not chunks:
            return chunks

        merged = []
        i = 0

        while i < len(chunks):
            current = chunks[i]

            # 如果当前chunk太短，持续合并直到达到min_size或超过max_size
            if len(current) < self.min_size:
                j = i + 1

                # 持续向后合并
                while j < len(chunks) and len(current) < self.min_size:
                    next_chunk = chunks[j]
                    combined = current + "\n\n" + next_chunk

                    # 如果合并后超过max_size，停止合并
                    if len(combined) > self.max_size:
                        break

                    current = combined
                    j += 1

                # 如果合并后仍然小于min_size，尝试与前一个chunk合并
                if len(current) < self.min_size and merged:
                    last_chunk = merged[-1]
                    combined_with_prev = last_chunk + "\n\n" + current

                    if len(combined_with_prev) <= self.max_size:
                        # 与前一个合并
                        merged[-1] = combined_with_prev
                        i = j
                        continue

                # 添加合并后的chunk
                merged.append(current)
                i = j
            else:
                # 当前chunk长度已经满足要求
                merged.append(current)
                i += 1

        return merged

    def build_context(self, chunks: List[str], index: int) -> str:
        """
        构建上下文: 前一个 + 当前 + 后一个

        Args:
            chunks: 所有chunks列表
            index: 当前chunk的索引

        Returns:
            str: 包含上下文的合并文本
        """
        context_parts = []

        # 添加前一个chunk
        if index > 0:
            context_parts.append(chunks[index - 1])

        # 添加当前chunk
        context_parts.append(chunks[index])

        # 添加后一个chunk
        if index < len(chunks) - 1:
            context_parts.append(chunks[index + 1])

        return "\n\n".join(context_parts)

    def _process_chunk_for_metadata(self, chunk: str) -> str:
        """
        处理chunk用于metadata存储
        子类可以重写此方法以自定义处理逻辑（如HTML清理）

        Args:
            chunk: 原始chunk文本

        Returns:
            str: 处理后的chunk文本
        """
        return chunk

    def format_output(self, chunks: List[str], doc_id: str) -> List[Dict]:
        """
        格式化输出为标准字典结构

        Args:
            chunks: 分块后的文本列表
            doc_id: 文档ID

        Returns:
            List[Dict]: 格式化后的结果，每个元素包含：
                - pk: 主键 (doc_id#index)
                - doc_id: 文档ID
                - text: 包含上下文的完整文本
                - metadata: 元数据
        """
        result = []

        for i, chunk in enumerate(chunks):
            # 构建包含上下文的文本
            merged_text = self.build_context(chunks, i)

            # 处理chunk用于metadata（子类可以自定义）
            processed_chunk = self._process_chunk_for_metadata(chunk)

            # 格式化为字典结构
            result.append({
                "pk": f"{doc_id}#{i}",
                "doc_id": doc_id,
                "text": merged_text,
                "metadata": {
                    "chunk_index": i,
                    "sub_chunk": processed_chunk,
                    "sub_char_count": len(chunk),
                    "merged_char_count": len(merged_text)
                }
            })

        return result

    def chunk_with_stats(self, text: str) -> Dict:
        """
        分块并返回统计信息

        Args:
            text: 待分块的文本

        Returns:
            Dict: 包含chunks和统计信息
        """
        chunks = self.chunk(text)

        return {
            "chunks": chunks,
            "stats": {
                "total_chunks": len(chunks),
                "total_chars": len(text),
                "avg_chunk_size": sum(len(c) for c in chunks) / len(chunks) if chunks else 0,
                "min_chunk_size": min(len(c) for c in chunks) if chunks else 0,
                "max_chunk_size": max(len(c) for c in chunks) if chunks else 0,
            }
        }
