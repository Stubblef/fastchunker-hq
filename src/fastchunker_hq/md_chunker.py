# -*- coding: utf-8 -*-
"""
Markdown分块器模块
专门用于处理Markdown格式的文档，保留标题层级和特殊结构
"""

import re
import json
import csv
import os
from datetime import datetime
from typing import List
from bs4 import BeautifulSoup

from fastchunker_hq.base import BaseChunker

def clean_html(html_text: str, gen_report:bool=True) -> str:
    """
    移除 HTML 标签并清洗文本，用于 embedding 前的语义提取。
    """
    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_text, "html.parser")

    # 提取可见文本
    text = soup.get_text(separator=" ")

    # 去掉多余空白、换行、制表符
    clean_text = re.sub(r"\s+", " ", text).strip()

    if gen_report:
        # 生成CSV报告文件
        report_path = "./html_clean_report.csv"

        # 检查文件是否存在，如果不存在则创建并写入表头
        file_exists = os.path.exists(report_path)

        with open(report_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)

            # 如果文件不存在，先写入表头
            if not file_exists:
                writer.writerow(["timestamp", "original_length", "cleaned_length", "original_text", "cleaned_text"])

            # 写入数据行
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                timestamp,
                len(html_text),
                len(clean_text),
                html_text, # if len(html_text) > 500 else html_text,  # 限制长度避免CSV过大
                clean_text  #  + "..." if len(clean_text) > 500 else clean_text
            ])

    return clean_text


class MarkdownChunker(BaseChunker):
    """Markdown分块器 - 专门处理Markdown格式文档"""

    def __init__(self, max_size: int = 1000, min_size: int = 300):
        """
        初始化Markdown分块器

        Args:
            max_size: 单个块的最大字符数
            min_size: 单个块的最小字符数
        """
        super().__init__(max_size, min_size)
        self.sections = []

        # 核心正则
        self.header_pattern = re.compile(r'^#{1,6}\s+.+$', re.MULTILINE)
        self.code_block_pattern = re.compile(r'^```[\s\S]*?^```$', re.MULTILINE)
        self.table_pattern = re.compile(r'(?:^\|.+\|$\n?)+', re.MULTILINE)
        

    def chunk(self, text: str) -> List[str]:
        """
        核心分块方法: 将Markdown文本智能分割成多个语义完整的块

        处理流程:
            1. 预处理: 统一换行符格式，清理多余空白
            2. 按标题分割: 根据 Markdown 标题 (#, ##, ###...) 将文本分成多个 section
            3. 处理 section: 对超长 section 进行二次分割，保护代码块和表格不被拆散
            4. 合并短块: 将过短的 chunk 与相邻块合并

        Args:
            text: 待分块的 Markdown 文本

        Returns:
            List[str]: 分块后的文本列表
        """
        # 1. 预处理
        text = self._preprocess(text)

        # 2. 按标题分割
        sections = self._split_by_headers(text)

        # 3. 处理每个section
        chunks = []
        for section in sections:
            chunks.extend(self._process_section(section))

        # 4. 合并过短的chunks
        chunks = self._merge_short(chunks)
        return chunks

    def _process_chunk_for_metadata(self, chunk: str) -> str:
        """
        重写基类方法：为Markdown使用HTML清理功能

        Args:
            chunk: 原始chunk文本

        Returns:
            str: 清理HTML后的纯文本
        """
        return clean_html(chunk, gen_report=False)

    def _split_by_headers(self, text: str) -> List[str]:
        """按标题分割成sections"""
        matches = list(self.header_pattern.finditer(text))
        
        if not matches:
            return [text]
        
        # 第一个标题之前的内容
        if matches[0].start() > 0:
            self.sections.append(text[:matches[0].start()].strip())
        
        # 每个标题及其内容
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            section = text[start:end].strip()
            if section:
                self.sections.append(section)
        
        return self.sections
    
    def _process_section(self, section: str) -> List[str]:
        """处理单个section"""
        # 如果section不超过最大长度,直接返回
        if len(section) <= self.max_size:
            return [section]
        
        # 保护特殊块(代码、表格)
        protected_blocks = []
        temp_text = section
        
        # 提取代码块
        for match in self.code_block_pattern.finditer(section):
            placeholder = f"<<<CODE_BLOCK_{len(protected_blocks)}>>>"
            protected_blocks.append(match.group(0))
            temp_text = temp_text.replace(match.group(0), placeholder, 1)
        
        # 提取表格
        for match in self.table_pattern.finditer(temp_text):
            placeholder = f"<<<TABLE_{len(protected_blocks)}>>>"
            protected_blocks.append(match.group(0))
            temp_text = temp_text.replace(match.group(0), placeholder, 1)
        
        # 按段落分割
        paragraphs = re.split(r'\n\s*\n', temp_text)
        
        # 组装chunks
        chunks = []
        current = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 恢复保护的块
            for i, block in enumerate(protected_blocks):
                para = para.replace(f"<<<CODE_BLOCK_{i}>>>", block)
                para = para.replace(f"<<<TABLE_{i}>>>", block)
            
            # 检查是否需要新chunk
            if current and len(current) + len(para) + 2 > self.max_size:
                chunks.append(current)
                current = para
            else:
                current = current + "\n\n" + para if current else para
        
        if current:
            chunks.append(current)

        return chunks



