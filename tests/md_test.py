import json
from fastchunker_hq.md_chunker import MarkdownChunker



chunker = MarkdownChunker(max_size=1500, min_size=300)
md_path = "DL-T 5629-2021_架空输电线路钢骨钢管混凝土结构设计技术规程.md"
with open(md_path, "r") as f:
    markdown_text = f.read()

# 分块
chunks = chunker.chunk(markdown_text)

# 格式化输出
result = chunker.format_output(chunks, doc_id="doc_001")

# 按sub_chunk字符数量排序（从小到大）
# result_sorted = sorted(result, key=lambda x: x["metadata"]["sub_char_count"])

# 保存为jsonl格式
output_path = "chunks_output.jsonl"
with open(output_path, "w", encoding="utf-8") as f:
    for chunk in result:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"✓ 成功处理 {len(result)} 个chunks")
print(f"✓ 已保存到: {output_path}")
print(f"✓ 已按sub_chunk字符数量排序（从小到大）")