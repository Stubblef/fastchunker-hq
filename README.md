# 文本分块
# markdown分块
# 分块接口生成简要上下文


```
contextual_prompt = """
<document>
{WHOLE_DOCUMENT}
</document>

Here is the chunk we want to situate within the whole document
<chunk>
{CHUNK_CONTENT}
</chunk>

Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.
"""
```