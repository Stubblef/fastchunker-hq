import json, os
from fastchunker_hq.text_chunker import TextChunker


# 使用示例
if __name__ == "__main__":
    # 创建分块器
    chunker = TextChunker(max_size=1000, min_size=300)

    # 读取文本文件
    text_path = "DL-T 5629-2021_架空输电线路钢骨钢管混凝土结构设计技术规程.md"

    if not os.path.exists(text_path):
        print(f"文件不存在: {text_path}")
        print("请提供正确的文件路径")
    else:
        with open(text_path, "r", encoding="utf-8") as f:
            text_content = f.read()

        # 方法1: 基本分块
        chunks = chunker.chunk(text_content)
        print(f"基本分块完成: {len(chunks)} 个chunks")

        # 方法2: 带统计信息的分块
        result_with_stats = chunker.chunk_with_stats(text_content)
        print(f"\n统计信息:")
        for key, value in result_with_stats["stats"].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")

        # 方法3: 格式化输出
        formatted_result = chunker.format_output(chunks, doc_id="doc_001")

        # 按sub_chunk字符数量排序
        # formatted_result_sorted = sorted(
        #     formatted_result,
        #     key=lambda x: x["metadata"]["sub_char_count"]
        # )

        # 保存为jsonl格式
        output_path = "text_chunks_output.jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in formatted_result:
                f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

        print(f"\n成功处理 {len(formatted_result)} 个chunks")
        print(f"已保存到: {output_path}")
        print(f"已按sub_chunk字符数量排序")
