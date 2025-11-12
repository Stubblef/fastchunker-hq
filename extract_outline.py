#!/usr/bin/env python3
"""
从 HTML 文件中提取文档大纲
"""
from bs4 import BeautifulSoup
import re
import json


def clean_html_for_outline(soup):
    """
    清理 HTML，移除与大纲无关的内容

    Args:
        soup: BeautifulSoup 对象

    Returns:
        清理后的 BeautifulSoup 对象和清理统计信息
    """
    stats = {
        'tables_removed': 0,
        'images_removed': 0,
        'scripts_removed': 0,
        'captions_removed': 0,
        'long_paragraphs_removed': 0
    }

    # 1. 移除所有表格（table标签及其内容）
    tables = soup.find_all('table')
    stats['tables_removed'] = len(tables)
    for table in tables:
        table.decompose()

    # 2. 移除所有图片（img标签）
    images = soup.find_all('img')
    stats['images_removed'] = len(images)
    for img in images:
        img.decompose()

    # 3. 移除脚本和样式标签
    scripts = soup.find_all(['script', 'style'])
    stats['scripts_removed'] = len(scripts)
    for tag in scripts:
        tag.decompose()

    # 4. 移除常见的非内容标签
    for tag in soup.find_all(['head', 'meta', 'link', 'svg', 'canvas']):
        tag.decompose()

    # 5. 移除包含图片引用的段落（可能是图注）
    for p in soup.find_all(['p', 'div']):
        text = p.get_text().strip()
        # 移除"图"、"表"开头的标注（如"图1.1"、"表2.3"）
        if re.match(r'^(图|表|Fig|Table)\s*[\d\.]+', text):
            stats['captions_removed'] += 1
            p.decompose()
            continue

        # 移除过长的文本段落（超过200字符，通常标题都很短）
        if len(text) > 200:
            stats['long_paragraphs_removed'] += 1
            p.decompose()
            continue

    return soup, stats


def extract_outline(html_file, output_file=None, format='txt', max_level=2):
    """
    从 HTML 文件提取文档大纲

    Args:
        html_file: HTML 文件路径
        output_file: 输出文件路径（可选）
        format: 输出格式 ('txt', 'json', 'markdown')
        max_level: 最大提取层级，1-3之间，默认为2（提取一级和二级标题）
    """
    # 读取 HTML 文件
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析 HTML
    soup = BeautifulSoup(content, 'html.parser')

    # 清理 HTML，移除表格、图片等无关内容
    soup, clean_stats = clean_html_for_outline(soup)

    print("HTML 清理完成：")
    print(f"  - 移除表格: {clean_stats['tables_removed']} 个")
    print(f"  - 移除图片: {clean_stats['images_removed']} 个")
    print(f"  - 移除脚本/样式: {clean_stats['scripts_removed']} 个")
    print(f"  - 移除图表标注: {clean_stats['captions_removed']} 个")
    print(f"  - 移除长文本段落: {clean_stats['long_paragraphs_removed']} 个")
    print()

    # 查找所有段落
    paragraphs = soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

    # 定义章节编号的正则表达式
    # 匹配: "1 标题"、"1.1 标题"、"1.1.1 标题" 等
    heading_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+?)(?:\s+\d+)?$')

    outline = []
    processed_numbers = set()  # 用于去重

    for p in paragraphs:
        text = p.get_text().strip()

        # 跳过空行
        if not text:
            continue

        # # 跳过过短的文本（少于3个字符）
        # if len(text) < 3:
        #     continue

        # 跳过纯数字或特殊字符的文本
        if re.match(r'^[\d\s\.\-\,\(\)\[\]]+$', text):
            continue

        # 匹配章节编号
        match = heading_pattern.match(text)
        if match:
            number = match.group(1)
            title = match.group(2).strip()

            # 跳过空标题
            if not title or len(title) < 2:
                continue

            # 跳过重复的章节编号
            if number in processed_numbers:
                continue

            # 计算层级（根据点号数量）
            level = number.count('.') + 1

            # 只保留指定层级的标题
            if level <= max_level:
                outline.append({
                    'number': number,
                    'title': title,
                    'level': level,
                    'full_text': text
                })
                processed_numbers.add(number)

    # 输出结果
    if format == 'json':
        output_text = json.dumps(outline, ensure_ascii=False, indent=2)
    elif format == 'markdown':
        output_text = generate_markdown_outline(outline)
    else:  # txt
        output_text = generate_text_outline(outline)

    # 保存到文件或打印
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output_text)
        print(f"大纲已保存到: {output_file}")
    else:
        print(output_text)

    return outline


def generate_text_outline(outline):
    """生成纯文本格式的大纲"""
    lines = []

    for item in outline:
        indent = "  " * (item['level'] - 1)
        lines.append(f"{indent}{item['number']} {item['title']}")

    return "\n".join(lines)


def generate_markdown_outline(outline):
    """生成 Markdown 格式的大纲"""
    lines = []
    lines.append("# 文档大纲")
    lines.append("")

    for item in outline:
        # 使用 Markdown 标题语法
        heading_marker = "#" * (item['level'] + 1)
        lines.append(f"{heading_marker} {item['number']} {item['title']}")
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    import argparse

    # 解析命令行参数
    parser = argparse.ArgumentParser(description='从 HTML 文件中提取文档大纲')
    parser.add_argument('input_file', nargs='?',
                       default="/Users/tsing/data/jhq/fastchunker-hq/附件1.html",
                       help='HTML 文件路径（默认: 附件1.html）')
    parser.add_argument('--max-level', type=int, default=2, choices=[1, 2, 3],
                       help='最大提取层级 (1-3)，默认为 2')
    parser.add_argument('--format', choices=['txt', 'json', 'markdown'], default='txt',
                       help='输出格式，默认为 txt')
    parser.add_argument('--output', help='输出文件路径（可选）')

    args = parser.parse_args()
    input_file = args.input_file
    max_level = args.max_level

    # 提取大纲并以不同格式输出
    print(f"正在提取文档大纲（最大层级: {max_level}）...\n")

    # 1. 在控制台打印（文本格式）
    outline = extract_outline(input_file, format='txt', max_level=max_level)

    # 2. 保存为文本文件
    extract_outline(input_file, output_file="附件1_outline.txt", format='txt', max_level=max_level)

    # 3. 保存为 Markdown 文件
    extract_outline(input_file, output_file="附件1_outline.md", format='markdown', max_level=max_level)

    # 4. 保存为 JSON 文件
    extract_outline(input_file, output_file="附件1_outline.json", format='json', max_level=max_level)

    print(f"\n共提取到 {len(outline)} 个章节标题（层级 1-{max_level}）")
    print("\n生成的文件：")
    print("  - 附件1_outline.txt (纯文本格式)")
    print("  - 附件1_outline.md (Markdown 格式)")
    print("  - 附件1_outline.json (JSON 格式)")
    print(f"\n使用示例：")
    print(f"  python extract_outline.py                     # 默认提取 1-2 级标题")
    print(f"  python extract_outline.py --max-level 3       # 提取 1-3 级标题")
    print(f"  python extract_outline.py --max-level 1       # 只提取 1 级标题")
