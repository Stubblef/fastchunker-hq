import mammoth

input_file = "/Users/tsing/data/jhq/fastchunker-hq/datasets/附件1.华能内蒙古蒙东新能源有限公司赤峰市200万千瓦自建调峰能力风光储多能互补一体化＋荒漠治理基地（翁牛特旗120万千瓦风电项目区）可行性研究报告(1).docx"
output_file = "/Users/tsing/data/jhq/fastchunker-hq/附件1.html"

with open(input_file, "rb") as docx_file:
    result = mammoth.convert_to_html(docx_file)
    html = result.value
    
with open(output_file, "w", encoding="utf-8") as html_file:
    html_file.write(html)
    
print(f"转换完成！HTML 文件已保存到: {output_file}")
print(f"HTML 文件大小: {len(html)} 字符")
if result.messages:
    print(f"\n转换消息: {len(result.messages)} 条")
    for msg in result.messages[:5]:  # 只显示前5条消息
        print(f"  - {msg}")

