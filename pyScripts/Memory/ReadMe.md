Memory = {
    "id": "uuid4",              # 唯一标识（必须）
    "content": "原始压缩事实",   # 原始记忆
    "summary": "语义压缩",       # LLM快速读取
    "tags": ["food", "apple"],  # 粗过滤索引
    "time": "ISO8601时间",      # 时间推理
    "embedding": [float...]     # 语义检索
}


用户输入
   ↓
embedding生成
   ↓
向量数据库（找相似记忆）
   ↓
SQL数据库（拿完整内容）
   ↓
LLM总结回答