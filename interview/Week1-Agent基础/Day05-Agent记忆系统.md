# Day 05 — Agent 记忆系统

> **本周进度**: Day1 ✅ Agent 基础概念 → Day2 ✅ ReAct 框架 → Day3 ✅ Function Calling → Day4 ✅ MCP 协议 → **Day5 记忆系统** → Day6 规划与推理 → Day7 回顾与手撕

---

## 一、知识图谱

```
                    Agent 记忆系统
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     记忆架构         记忆操作       存储后端
          │              │              │
    ┌─────┼─────┐   ┌───┼───┐    ┌────┼────┐
    │     │     │   │   │   │    │    │    │
  工作记忆 短期 长期  写入 读取 遗忘  向量DB KV  图DB
    │     │     │   │   │   │    │    │    │
  上下文窗口 摘要 对话 │   │   │  Pinecone Redis Neo4j
    │           │   │   │   │    ChromaPostgres
  Scratchpad  情节 语义 │   │
    │           │   │   │   │
  当前推理    程序  事实  编码 检索 衰减
```

**核心关系链**: 感知 → 写入工作记忆 → 触发长期记忆检索 → 融合上下文 → 推理决策 → 执行 → 更新记忆

---

## 二、面试题（10 道）

### Q1: 什么是 Agent 的记忆系统？为什么 Agent 需要记忆？

<details>
<summary>点击查看参考答案</summary>

**Agent 记忆系统**是指 Agent 获取、存储、检索和遗忘信息的一整套机制，使 Agent 能够跨对话轮次、跨会话保持和利用历史信息。

**为什么需要记忆？**

| 层面 | 无记忆 | 有记忆 |
|------|--------|--------|
| 上下文窗口 | 每轮重新构造 prompt，超出窗口丢失 | 可持久化关键信息 |
| 用户体验 | 重复问已告知的偏好 | 记住用户习惯 |
| 任务连续性 | 跨会话断档 | 长期项目持续推进 |
| 学习改进 | 重复犯同样错误 | 从历史失败中学习 |

**记忆的三个核心功能**：
1. **信息持久化**：将关键信息从易失的上下文窗口转移到持久存储
2. **相关检索**：在需要时按语义相关性召回历史信息
3. **遗忘机制**：淘汰过时、冗余信息，避免噪声干扰

**与 RAG 的区别**：RAG 是从外部知识库检索，记忆系统是从 Agent 自身经历中检索。两者互补：RAG 提供"世界知识"，记忆提供"个人经验"。

</details>

---

### Q2: 详细描述 Agent 的四层记忆架构

<details>
<summary>点击查看参考答案</summary>

**四层记忆架构**是当前 Agent 系统的主流设计：

#### 1. 工作记忆（Working Memory / Context Window）
- **载体**：LLM 的上下文窗口（如 GPT-4 的 128K tokens）
- **内容**：当前推理所需的全部信息——系统提示、对话历史、工具结果、中间推理
- **特点**：速度最快，但容量有限且易失
- **类比**：人脑的"短期工作台"

```python
# 工作记忆就是 messages 列表
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "帮我分析这份报告"},
    {"role": "assistant", "content": "好的，我来分析..."},
    {"role": "tool", "content": "报告内容..."},
    # 当前所有活跃信息
]
```

#### 2. 短期记忆（Short-Term Memory / Session Memory）
- **载体**：会话级存储（Redis / 内存中的对话缓冲区）
- **内容**：当前会话的对话历史摘要、关键决策点
- **特点**：会话结束后可提升为长期记忆或丢弃
- **策略**：滑动窗口 + 摘要压缩

```python
class ShortTermMemory:
    def __init__(self, max_messages=50):
        self.messages = []
        self.max_messages = max_messages
        self.summary = ""

    def add(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            # 触发摘要压缩
            self._compress()

    def _compress(self):
        # 将旧消息摘要后保留，原文丢弃
        old_msgs = self.messages[:20]
        new_summary = llm.summarize(old_msgs, self.summary)
        self.summary = new_summary
        self.messages = self.messages[20:]
```

#### 3. 长期记忆（Long-Term Memory）
- **载体**：向量数据库（Pinecone / Chroma / PostgreSQL+pgvector）
- **内容**：跨会话的事实、偏好、历史决策、学到的教训
- **三个子类型**：
  - **语义记忆（Semantic）**：事实知识——"用户是 Java 后端工程师"
  - **情节记忆（Episodic）**：具体事件——"昨天帮用户调试了 ReAct 循环 bug"
  - **程序记忆（Procedural）**：操作技能——"处理 CSV 文件时先检查编码"

```python
class LongTermMemory:
    def __init__(self, vector_store):
        self.store = vector_store  # 向量数据库

    def write(self, content, metadata=None):
        embedding = embedding_model.encode(content)
        self.store.add(
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata or {}]
        )

    def retrieve(self, query, top_k=5):
        query_emb = embedding_model.encode(query)
        results = self.store.query(
            query_embeddings=[query_emb],
            n_results=top_k
        )
        return results
```

#### 4. 外部记忆（External Memory）
- **载体**：文件系统、数据库、知识图谱、外部 API
- **内容**：结构化数据、文档、代码仓库等
- **特点**：容量无限，但需主动查询，不自动进入上下文

**四层协作流程**：
```
用户输入 → 工作记忆（构造 prompt）
           ↑ 检索补充
         短期记忆（当前会话摘要）
           ↑ 遗忘/提升
         长期记忆（向量检索相关历史）
           ↑ 按需查询
         外部记忆（数据库/文件/API）
```

</details>

---

### Q3: 如何设计记忆的写入策略？什么时候该写入，写什么？

<details>
<summary>点击参考答案</summary>

**核心原则**：不是所有信息都值得记住。写入策略需要平衡"信息价值"与"存储/检索成本"。

#### 写入触发时机

| 时机 | 示例 | 写入内容 |
|------|------|----------|
| 用户明确告知偏好 | "我喜欢用 Python" | 语义记忆：偏好 |
| Agent 做出重要决策 | 选择方案 A 而非 B | 情节记忆：决策+理由 |
| 任务完成/失败 | 调试成功/报错 | 情节+程序记忆：经验教训 |
| 用户纠正 Agent | "不对，应该是…" | 语义记忆：修正事实 |
| 发现新事实 | 工具返回新数据 | 语义记忆：事实 |

#### 写入策略设计

```python
class MemoryWriter:
    def __init__(self, llm, vector_store):
        self.llm = llm
        self.store = vector_store

    def should_memorize(self, message, context):
        """判断是否值得写入长期记忆"""
        prompt = f"""判断以下信息是否值得长期记住。
        信息: {message}
        上下文: {context}

        判断标准:
        - 用户偏好/事实 → 值得
        - 一次性任务细节 → 不值得
        - 可复用的经验教训 → 值得
        - 临时中间结果 → 不值得

        只回答 YES 或 NO，并说明理由。"""
        decision = self.llm.generate(prompt)
        return "YES" in decision.upper()

    def write(self, message, context):
        if not self.should_memorize(message, context):
            return None

        # 提取结构化记忆
        extracted = self.llm.generate(f"""
        将以下信息提取为结构化记忆:
        信息: {message}
        输出格式: type|content|importance(1-10)
        类型: semantic|episodic|procedural
        """)

        # 解析并写入
        mem_type, content, importance = extracted.split("|")
        self.store.add(
            documents=[content],
            metadatas={"type": mem_type, "importance": int(importance),
                       "timestamp": datetime.now().isoformat()},
            ids=[str(uuid4())]
        )
```

#### 关键设计考量

1. **去重**：写入前检索相似记忆，避免重复
2. **重要性评分**：不是所有记忆同等重要，用 1-10 分排序
3. **衰减机制**：低重要性记忆随时间衰减
4. **批量写入**：不要每轮都写，任务结束时批量提取记忆

</details>

---

### Q4: 如何设计记忆的读取（检索）策略？如何把记忆注入上下文？

<details>
<summary>点击查看参考答案</summary>

**记忆检索是 Agent 记忆系统最关键的环节**——检索质量直接决定 Agent 的表现。

#### 检索策略全景

```
当前用户输入
      │
      ├─ 1. 语义检索（向量相似度）
      ├─ 2. 时间衰减（近期优先）
      ├─ 3. 重要性加权（高分优先）
      ├─ 4. 频率加权（常引用优先）
      └─ 5. 上下文相关性（与当前任务匹配）
      │
      融合排序 → Top-K → 注入 Prompt
```

#### 实现方案

```python
class MemoryRetriever:
    def __init__(self, vector_store, llm):
        self.store = vector_store
        self.llm = llm

    def retrieve(self, query, top_k=5, current_context=""):
        # 第一步：向量召回（扩大召回量）
        candidates = self.store.query(
            query_embeddings=[embedding_model.encode(query)],
            n_results=top_k * 3  # 召回 3 倍
        )

        # 第二步：多因子重排
        scored = []
        for i, doc in enumerate(candidates['documents'][0]):
            meta = candidates['metadatas'][0][i]
            score = self._compute_score(query, doc, meta, current_context)
            scored.append((doc, meta, score))

        scored.sort(key=lambda x: -x[2])
        return scored[:top_k]

    def _compute_score(self, query, doc, meta, context):
        # 向量相似度 (0-1)
        sim = cosine_similarity(
            embedding_model.encode(query),
            embedding_model.encode(doc)
        )

        # 时间衰减：半衰期 30 天
        age_days = (datetime.now() - datetime.fromisoformat(meta['timestamp'])).days
        recency = math.exp(-age_days / 30)

        # 重要性 (0-1)
        importance = meta.get('importance', 5) / 10

        # 频率
        frequency = min(meta.get('access_count', 0) / 10, 1.0)

        # 加权融合
        return (0.4 * sim + 0.2 * recency +
                0.2 * importance + 0.2 * frequency)

    def inject_into_prompt(self, query, system_prompt, current_context=""):
        """将记忆注入系统提示"""
        memories = self.retrieve(query, top_k=5, current_context=current_context)

        if not memories:
            return system_prompt

        memory_block = "\n## 相关记忆\n"
        for doc, meta, score in memories:
            memory_block += f"- [{meta.get('type','?')}] {doc} (相关性: {score:.2f})\n"

        return system_prompt + "\n" + memory_block
```

#### 注入位置的选择

| 注入位置 | 优点 | 缺点 |
|----------|------|------|
| System Prompt 尾部 | 简单直接 | 可能被后续消息稀释 |
| 用户消息前缀 | 与当前问题关联 | 格式不自然 |
| 独立 system 消息 | 清晰隔离 | 占用额外 token |

**最佳实践**：在 system prompt 中预留 `[RELEVANT_MEMORIES]` 占位符，动态替换。

</details>

---

### Q5: 记忆的遗忘机制怎么设计？为什么遗忘很重要？

<details>
<summary>点击查看参考答案</summary>

**遗忘不是缺陷，是特性**。没有遗忘机制的 Agent 会被噪声淹没，检索质量持续下降。

#### 为什么需要遗忘

1. **检索质量下降**：无关记忆越多，信噪比越低
2. **存储成本增长**：无界增长导致向量检索变慢
3. **上下文污染**：过时信息可能误导当前决策
4. **矛盾处理**：旧事实与新事实冲突时需要更新

#### 遗忘策略设计

```python
class MemoryDecay:
    def __init__(self, vector_store):
        self.store = vector_store
        self.decay_config = {
            "half_life_days": 30,      # 半衰期
            "min_importance": 3,       # 低于此分直接删除
            "max_memories": 10000,     # 容量上限
            "merge_threshold": 0.92,   # 相似度高于此则合并
        }

    def decay(self):
        """定期执行遗忘策略"""
        all_memories = self.store.get_all()

        # 策略1: 时间+重要性衰减
        for mem in all_memories:
            age = days_since(mem['metadata']['timestamp'])
            importance = mem['metadata']['importance']

            # 衰减后的有效重要性
            effective_imp = importance * math.exp(-age / self.decay_config['half_life_days'])

            if effective_imp < self.decay_config['min_importance']:
                self.store.delete(mem['id'])

        # 策略2: 去重合并
        self._merge_duplicates()

        # 策略3: 容量管理（LRU + 最低分淘汰）
        if self.store.count() > self.decay_config['max_memories']:
            self._evict_lowest()

    def _merge_duplicates(self):
        """合并高度相似的记忆"""
        memories = self.store.get_all()
        for i, mem_a in enumerate(memories):
            for mem_b in memories[i+1:]:
                sim = cosine_similarity(mem_a['embedding'], mem_b['embedding'])
                if sim > self.decay_config['merge_threshold']:
                    # 用 LLM 合并两条记忆
                    merged = self.llm.generate(f"""
                    合并两条相似记忆，保留关键信息:
                    A: {mem_a['document']}
                    B: {mem_b['document']}
                    合并结果:""")
                    # 写入合并结果，删除原始两条
                    self.store.add(documents=[merged],
                                   metadatas=[{**mem_a['metadata'],
                                              'importance': max(mem_a['metadata']['importance'],
                                                                mem_b['metadata']['importance'])}])
                    self.store.delete([mem_a['id'], mem_b['id']])
```

#### 遗忘策略对比

| 策略 | 原理 | 适用场景 |
|------|------|----------|
| 时间衰减 | 指数衰减，近期优先 | 通用场景 |
| 重要性淘汰 | 低分优先删除 | 有明确重要性评分 |
| 访问频率 | LRU，少访问的删除 | 长期运行 Agent |
| 相似合并 | 去重 + 信息融合 | 避免冗余 |
| 主动遗忘 | 用户/Agent 标记删除 | 隐私合规、错误修正 |

</details>

---

### Q6: 向量数据库在 Agent 记忆系统中扮演什么角色？如何选型？

<details>
<summary>点击查看参考答案</summary>

**向量数据库是长期记忆的核心存储引擎**，负责将文本转化为高维向量并支持相似度检索。

#### 角色定位

```
记忆写入: 文本 → Embedding 模型 → 向量 → 存入向量DB
记忆检索: 查询 → Embedding 模型 → 向量 → 向量DB 近邻搜索 → Top-K 文本
```

#### 主流向量数据库对比

| 数据库 | 类型 | 特点 | 适用场景 |
|--------|------|------|----------|
| Pinecone | 托管 SaaS | 零运维，自动扩展 | 快速上线，不想运维 |
| Chroma | 嵌入式 | 轻量，Python 原生 | 原型开发，小规模 |
| Weaviate | 开源 | 内置混合检索 | 需要关键词+向量混合 |
| Milvus | 开源 | 高性能，支持十亿级 | 大规模生产 |
| pgvector | PostgreSQL 扩展 | 与关系数据统一 | 已有 PG 基础设施 |
| Qdrant | 开源 | Rust 实现，高性能 | 性能敏感场景 |
| Redis | 内存 + RediSearch | 超低延迟 | 短期记忆 + 缓存 |

#### 选型决策树

```
需要管理基础设施吗？
├─ 否 → Pinecone（托管）
└─ 是
   ├─ 规模 > 1 亿向量？
   │   ├─ 是 → Milvus
   │   └─ 否
   │       ├─ 已有 PostgreSQL？
   │       │   ├─ 是 → pgvector
   │       │   └─ 否
   │       │       ├─ 需要混合检索？
   │       │       │   ├─ 是 → Weaviate
   │       │       │   └─ 否 → Qdrant / Chroma
```

#### 记忆系统中的关键配置

```python
# 以 Chroma 为例的记忆系统配置
import chromadb

client = chromadb.PersistentClient(path="./memory_db")
collection = client.create_collection(
    name="agent_memory",
    metadata={
        "hnsw:space": "cosine",      # 距离度量
        "hnsw:M": 16,                # 连接数（精度 vs 速度）
        "hnsw:construction_ef": 200, # 构建时搜索宽度
    }
)

# 写入记忆
collection.add(
    embeddings=[embedding],
    documents=["用户偏好Python，熟悉Spring Boot"],
    metadatas=[{
        "type": "semantic",
        "importance": 8,
        "timestamp": "2026-09-22T10:00:00",
        "source": "user_statement",
        "session_id": "sess_123"
    }],
    ids=["mem_001"]
)

# 检索记忆（带元数据过滤）
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={"type": "semantic"}  # 只检索语义记忆
)
```

</details>

---

### Q7: 上下文窗口不够用时，如何压缩和管理上下文？

<details>
<summary>点击查看参考答案</summary>

**上下文管理是 Agent 系统的核心工程挑战**——LLM 窗口有限，但任务可能产生大量中间信息。

#### 压缩策略全景

```
上下文溢出
    │
    ├─ 1. 滑动窗口（丢弃最旧消息）
    ├─ 2. 摘要压缩（LLM 总结旧消息）
    ├─ 3. 选择性保留（保留关键消息）
    ├─ 4. 结构化提取（提取关键信息到表格）
    └─ 5. 外部化（转存到向量DB，按需检索）
```

#### 策略1: 滑动窗口 + 摘要

```python
class ContextManager:
    def __init__(self, llm, max_tokens=8000, keep_recent=10):
        self.llm = llm
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent  # 保留最近 N 条
        self.running_summary = ""

    def manage(self, messages):
        total_tokens = count_tokens(messages)

        if total_tokens <= self.max_tokens:
            return messages

        # 分离：保留最近消息 + 压缩旧消息
        recent = messages[-self.keep_recent:]
        old = messages[:-self.keep_recent]

        # 生成摘要
        old_text = "\n".join([f"{m['role']}: {m['content']}" for m in old])
        self.running_summary = self.llm.generate(f"""
        将以下对话历史压缩为简洁摘要，保留:
        - 用户的核心需求
        - 已做出的关键决策
        - 重要的中间结果
        - 未解决的问题

        当前摘要: {self.running_summary}
        新增内容: {old_text}

        更新后的摘要:""")

        # 构造压缩后的上下文
        return [
            {"role": "system", "content": f"## 对话摘要\n{self.running_summary}"},
            *recent
        ]
```

#### 策略2: 选择性保留（标记重要消息）

```python
class SelectiveContextManager:
    """基于消息重要性的选择性保留"""
    
    IMPORTANCE_MARKERS = {
        "decision": 10,    # 决策点
        "error": 8,        # 错误信息
        "user_correction": 9,  # 用户纠正
        "tool_result": 5,  # 工具结果
        "small_talk": 1,   # 闲聊
    }

    def manage(self, messages, max_tokens=8000):
        # 为每条消息评分
        scored = [(msg, self._score(msg)) for msg in messages]

        # 按分数排序，保留高分消息
        scored.sort(key=lambda x: -x[1])

        kept = []
        token_count = 0
        for msg, score in scored:
            msg_tokens = count_tokens([msg])
            if token_count + msg_tokens > max_tokens:
                break
            kept.append(msg)
            token_count += msg_tokens

        # 恢复时间顺序
        kept.sort(key=lambda m: messages.index(m))
        return kept
```

#### 策略3: 结构化外部化

```python
class ExternalizedContext:
    """将中间结果外部化到向量DB，按需检索"""
    
    def __init__(self, vector_store):
        self.store = vector_store
        self.working_context = []

    def add_tool_result(self, result, tool_name, query_context):
        """工具结果不留在上下文，存入向量DB"""
        if count_tokens(result) > 500:  # 大结果外部化
            self.store.add(
                documents=[result],
                metadatas={"tool": tool_name, "query": query_context},
                ids=[str(uuid4())]
            )
            # 上下文中只保留摘要
            summary = llm.summarize(result, max_words=50)
            self.working_context.append({
                "role": "tool",
                "content": f"[结果已外部化] 摘要: {summary}"
            })
        else:
            self.working_context.append({"role": "tool", "content": result})

    def retrieve_external(self, query):
        """需要时从外部检索完整结果"""
        return self.store.query(query_embeddings=[encode(query)], n_results=3)
```

#### 实际产品中的方案

| 产品 | 方案 |
|------|------|
| Claude | 自动压缩长对话（Prompt Caching + 压缩） |
| ChatGPT | 记忆功能（自动提取关键事实） |
| Cursor | 代码库索引 + 按需检索 |
| Devin | 分层记忆 + 任务状态外部化 |

</details>

---

### Q8: 手撕一个带记忆系统的 Agent（核心代码）

<details>
<summary>点击查看答案</summary>

```python
"""
带四层记忆系统的 Agent 实现
- 工作记忆: 当前对话上下文
- 短期记忆: 会话级消息缓冲 + 摘要
- 长期记忆: 向量数据库（语义/情节/程序）
- 外部记忆: 按需查询的知识库
"""

import json
import time
import math
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# ============ 记忆类型定义 ============

class MemoryType(Enum):
    SEMANTIC = "semantic"     # 事实知识
    EPISODIC = "episodic"     # 事件经历
    PROCEDURAL = "procedural" # 操作技能


@dataclass
class Memory:
    id: str
    content: str
    memory_type: MemoryType
    importance: float  # 1-10
    timestamp: str
    access_count: int = 0
    last_accessed: Optional[str] = None
    embedding: list = field(default_factory=list)


# ============ 长期记忆（向量存储）============

class LongTermMemory:
    """基于向量的长期记忆存储"""

    def __init__(self, embed_fn, llm_fn):
        self.embed_fn = embed_fn    # 文本转向量的函数
        self.llm_fn = llm_fn        # LLM 调用函数
        self.memories: list[Memory] = []
        self.decay_half_life = 30   # 30天半衰期

    def write(self, content: str, mem_type: MemoryType,
              importance: float = 5.0):
        """写入记忆（带去重检查）"""
        embedding = self.embed_fn(content)

        # 去重：检查是否已有高度相似记忆
        for mem in self.memories:
            sim = self._cosine_sim(embedding, mem.embedding)
            if sim > 0.92:
                # 合并：取更高重要性
                mem.importance = max(mem.importance, importance)
                mem.content = self._merge(mem.content, content)
                mem.embedding = self.embed_fn(mem.content)
                return mem.id

        # 新记忆
        mem = Memory(
            id=f"mem_{int(time.time()*1000)}",
            content=content,
            memory_type=mem_type,
            importance=importance,
            timestamp=datetime.now().isoformat(),
            embedding=embedding,
        )
        self.memories.append(mem)
        return mem.id

    def retrieve(self, query: str, top_k: int = 5,
                 mem_type: Optional[MemoryType] = None) -> list[Memory]:
        """多因子检索：向量相似度 + 时间衰减 + 重要性"""
        query_emb = self.embed_fn(query)

        candidates = self.memories
        if mem_type:
            candidates = [m for m in candidates if m.memory_type == mem_type]

        scored = []
        for mem in candidates:
            # 向量相似度 (0-1)
            sim = self._cosine_sim(query_emb, mem.embedding)

            # 时间衰减
            age_days = (datetime.now() - datetime.fromisoformat(mem.timestamp)).days
            recency = math.exp(-age_days / self.decay_half_life)

            # 重要性 (0-1)
            importance = mem.importance / 10.0

            # 频率
            frequency = min(mem.access_count / 10.0, 1.0)

            # 融合分数
            score = 0.45 * sim + 0.20 * recency + 0.20 * importance + 0.15 * frequency
            scored.append((mem, score))

        scored.sort(key=lambda x: -x[1])

        # 更新访问计数
        result = []
        for mem, score in scored[:top_k]:
            mem.access_count += 1
            mem.last_accessed = datetime.now().isoformat()
            result.append(mem)

        return result

    def decay(self, min_importance: float = 2.0):
        """遗忘：删除衰减后重要性低于阈值的记忆"""
        before = len(self.memories)
        self.memories = [
            m for m in self.memories
            if m.importance * math.exp(
                -((datetime.now() - datetime.fromisoformat(m.timestamp)).days) / self.decay_half_life
            ) >= min_importance
        ]
        pruned = before - len(self.memories)
        return f"遗忘 {pruned} 条记忆（剩余 {len(self.memories)} 条）"

    def _cosine_sim(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        return dot / (norm_a * norm_b + 1e-8)

    def _merge(self, old: str, new: str) -> str:
        return self.llm_fn(f"合并两条记忆，保留关键信息:\nA: {old}\nB: {new}\n合并结果:")


# ============ 短期记忆（会话级）============

class ShortTermMemory:
    """会话级记忆：滑动窗口 + 自动摘要"""

    def __init__(self, llm_fn, max_messages: int = 30):
        self.llm_fn = llm_fn
        self.messages: list[dict] = []
        self.max_messages = max_messages
        self.summary: str = ""

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self._compress()

    def _compress(self):
        """压缩旧消息为摘要"""
        old = self.messages[: self.max_messages // 2]
        new_summary = self.llm_fn(
            f"更新对话摘要，保留关键信息:\n"
            f"当前摘要: {self.summary}\n"
            f"新增对话: {json.dumps(old, ensure_ascii=False)}\n"
            f"更新后的摘要:"
        )
        self.summary = new_summary
        self.messages = self.messages[self.max_messages // 2:]

    def get_context(self) -> list[dict]:
        """获取当前上下文（摘要 + 最近消息）"""
        ctx = []
        if self.summary:
            ctx.append({"role": "system", "content": f"## 会话摘要\n{self.summary}"})
        ctx.extend(self.messages)
        return ctx


# ============ 记忆管理器 ============

class MemoryManager:
    """记忆管理器：协调短期/长期记忆的写入和检索"""

    def __init__(self, llm_fn, embed_fn):
        self.llm_fn = llm_fn
        self.short_term = ShortTermMemory(llm_fn)
        self.long_term = LongTermMemory(embed_fn, llm_fn)

    def extract_and_store(self, user_input: str, agent_response: str):
        """从对话中提取值得记住的信息"""
        extraction = self.llm_fn(f"""分析以下对话，提取值得长期记忆的信息。
对每条记忆输出: type|content|importance(1-10)
type: semantic(事实), episodic(事件), procedural(技能)
不值得记忆则输出 NONE

用户: {user_input}
Agent: {agent_response}

格式:
type|content|importance
type|content|importance
""")
        if "NONE" in extraction:
            return []

        stored = []
        for line in extraction.strip().split("\n"):
            parts = line.split("|")
            if len(parts) == 3:
                mem_type_str, content, importance = parts
                try:
                    mem_type = MemoryType(mem_type_str.strip().lower())
                    importance = float(importance.strip())
                    mem_id = self.long_term.write(content.strip(), mem_type, importance)
                    stored.append(mem_id)
                except (ValueError, KeyError):
                    continue
        return stored

    def recall(self, query: str, top_k: int = 5) -> str:
        """检索相关记忆，格式化为文本"""
        memories = self.long_term.retrieve(query, top_k=top_k)
        if not memories:
            return ""

        lines = ["## 相关记忆"]
        type_labels = {
            MemoryType.SEMANTIC: "事实",
            MemoryType.EPISODIC: "经历",
            MemoryType.PROCEDURAL: "技能",
        }
        for mem in memories:
            label = type_labels.get(mem.memory_type, "?")
            lines.append(f"- [{label}] {mem.content}")
        return "\n".join(lines)


# ============ 带 Memory 的 Agent ============

class MemoryAgent:
    """集成记忆系统的 Agent"""

    def __init__(self, llm_fn, embed_fn, tools: dict, system_prompt: str):
        self.llm_fn = llm_fn
        self.tools = tools
        self.system_prompt = system_prompt
        self.memory = MemoryManager(llm_fn, embed_fn)

    def chat(self, user_input: str) -> str:
        # 1. 检索长期记忆
        recalled = self.memory.recall(user_input)

        # 2. 构造上下文：系统提示 + 记忆 + 短期记忆
        system = self.system_prompt
        if recalled:
            system = system + "\n\n" + recalled

        context = [{"role": "system", "content": system}]
        context.extend(self.memory.short_term.get_context())
        context.append({"role": "user", "content": user_input})

        # 3. LLM 推理（简化版，实际应包含工具调用循环）
        response = self.llm_fn(json.dumps(context, ensure_ascii=False))

        # 4. 存入短期记忆
        self.memory.short_term.add("user", user_input)
        self.memory.short_term.add("assistant", response)

        # 5. 提取并写入长期记忆
        self.memory.extract_and_store(user_input, response)

        return response

    def periodic_maintenance(self):
        """定期维护：遗忘过时记忆"""
        return self.memory.long_term.decay()


# ============ 使用示例 ============

if __name__ == "__main__":
    # Mock 函数
    def mock_llm(prompt: str) -> str:
        return f"[LLM回应] {prompt[:50]}..."

    def mock_embed(text: str) -> list:
        # 模拟 embedding（实际用 OpenAI/BGE 等）
        return [0.1] * 128

    agent = MemoryAgent(
        llm_fn=mock_llm,
        embed_fn=mock_embed,
        tools={},
        system_prompt="你是一个有帮助的AI助手。"
    )

    # 对话
    print(agent.chat("我叫张三，是一名Java后端工程师。"))
    print(agent.chat("帮我写一个Python脚本。"))
    # 第二轮对话时，Agent 应该能从记忆中检索到"用户是Java工程师"

    # 定期维护
    print(agent.periodic_maintenance())
```

</details>

---

### Q9: 设计一个支持百万用户的 Agent 记忆系统（系统设计题）

<details>
<summary>点击查看参考答案</summary>

#### 需求分析

- **用户规模**：100 万活跃用户
- **记忆量**：每用户平均 100-1000 条记忆 → 1-10 亿条总记忆
- **延迟要求**：记忆检索 P99 < 100ms
- **写入量**：峰值 10K QPS
- **一致性**：允许最终一致，但单用户内需读己之写

#### 架构设计

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  Memory Service │  (无状态，水平扩展)
                    └───┬────┬────┬───┘
                        │    │    │
              ┌─────────┘    │    └─────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │  Redis   │  │ Vector DB│  │PostgreSQL│
        │ (缓存层) │  │ (长期记忆)│  │ (元数据) │
        │          │  │ (分片)   │  │          │
        └──────────┘  └──────────┘  └──────────┘
              │              │              │
              │         ┌────┴────┐         │
              │         ▼         ▼         │
              │     Shard 1   Shard 2  ... │
              │    (用户hash分片)           │
              │                             │
        ┌─────┴─────────────────────────────┴─────┐
        │          Embedding Service              │
        │     (GPU 集群 / API 调用)               │
        └─────────────────────────────────────────┘
```

#### 核心组件

**1. 分片策略**
```python
# 按用户 ID 分片，确保同一用户记忆在同一分片
shard_id = hash(user_id) % num_shards  # 如 16 个分片

# 每个分片独立的向量数据库实例
# 避免跨分片检索，保证单用户检索性能
```

**2. 多级缓存**
```python
class MemoryCache:
    def __init__(self):
        self.l1 = {}      # 进程内 LRU（最近对话）
        self.l2 = Redis    # 分布式缓存（热用户记忆）
        self.l3 = VectorDB # 持久存储（全量记忆）

    async def get(self, user_id, query):
        # L1: 进程缓存（1ms）
        cache_key = f"{user_id}:{hash(query)}"
        if cache_key in self.l1:
            return self.l1[cache_key]

        # L2: Redis 热缓存（5ms）
        cached = await self.l2.get(cache_key)
        if cached:
            self.l1[cache_key] = cached
            return cached

        # L3: 向量检索（50ms）
        results = await self.l3.query(user_id, query)
        # 回填缓存
        await self.l2.setex(cache_key, 3600, results)
        self.l1[cache_key] = results
        return results
```

**3. 写入异步化**
```python
# 写入不阻塞用户请求
async def chat_with_memory(user_id, message):
    response = await llm.generate(message)

    # 同步写入短期记忆
    await redis.lpush(f"session:{user_id}", message)

    # 异步提取并写入长期记忆
    asyncio.create_task(
        extract_and_store_long_term(user_id, message, response)
    )

    return response
```

**4. Embedding 服务**
- 使用轻量模型（如 BGE-small, 384 维）降低延迟和成本
- 批量编码：积累请求后批量处理
- GPU 推理服务 + 本地缓存常见 embedding

#### 容量估算

| 指标 | 估算 |
|------|------|
| 总记忆条数 | 1 亿（100万用户 × 100条） |
| 向量维度 | 1536（OpenAI）或 384（BGE-small） |
| 存储空间 | 1亿 × 1536 × 4字节 ≈ 600GB |
| 分片后单片 | 600GB / 16 ≈ 37.5GB |
| QPS | 写入 10K，读取 50K |
| Embedding QPS | 10K（每次写入+读取各一次） |

#### 面试中的关键讨论点

1. **分片 vs 全局检索**：分片保证性能但无法跨用户检索（推荐系统需全局）
2. **Embedding 成本**：OpenAI $0.13/1M tokens，10K QPS → 每月约 $3K
3. **隐私合规**：支持用户级数据删除（GDPR right to be forgotten）
4. **记忆冲突**：同一事实多条记忆时，以最新+最高重要性为准
5. **冷启动**：新用户无记忆，使用默认 prompt + 预置 FAQ

</details>

---

### Q10: 对比分析 MemGPT、Mem0、Letta 等记忆框架的设计思路

<details>
<summary>点击查看参考答案</summary>

#### MemGPT — 操作系统隐喻

**核心思想**：将 LLM 的上下文管理类比为操作系统的虚拟内存管理。

```
┌────────────────────────────────┐
│        LLM Context Window      │  ← "主存" (RAM)
│  ┌──────┐  ┌────────────────┐  │
│  │System│  │  Working Memory │  │
│  │Prompt│  │  (最近对话)     │  │
│  └──────┘  └────────────────┘  │
│  ┌────────────────────────────┐│
│  │  Memory Functions (系统调用)││  ← LLM 主动管理记忆
│  │  mread() / mwrite() /      ││
│  │  msearch() / mforget()     ││
│  └────────────────────────────┘│
└────────────────────────────────┘
         ↕ 页面置换
┌────────────────────────────────┐
│      External Memory (硬盘)     │  ← 向量数据库
│  对话历史 / 事实 / 摘要         │
└────────────────────────────────┘
```

**关键创新**：
- LLM 通过函数调用主动管理记忆（而非被动注入）
- 分页机制：上下文满时自动"换页"
- 自我编辑：LLM 可以更新、删除自己的记忆

**局限**：LLM 自主管理记忆增加推理开销，且可能做出糟糕的记忆管理决策。

#### Mem0 — 生产级记忆平台

**核心思想**：记忆即服务（Memory-as-a-Service），提供统一的记忆 API 层。

```python
from mem0 import Memory

m = Memory()
# 自动提取、存储、检索
m.add("我喜欢用 Python", user_id="user_123")
results = m.search("编程偏好", user_id="user_123")
```

**设计特点**：
- **自动提取**：LLM 自动从对话中提取值得记住的信息
- **多后端支持**：支持 Pinecone / Chroma / Qdrant 等
- **冲突处理**：新记忆与旧记忆冲突时自动更新
- **用户/会话/Agent 隔离**：支持多级记忆命名空间
- **API 优先**：可作为独立服务部署

#### Letta（原 MemGPT 团队产品化）

**核心思想**：将 MemGPT 的理念产品化为完整的 Agent 平台。

**关键特性**：
- **状态化 Agent**：Agent 有持久状态，跨会话保持
- **记忆编辑**：支持人类查看和编辑 Agent 记忆
- **多 Agent 共享记忆**：多个 Agent 可共享记忆池
- **A/B 测试记忆策略**：对比不同记忆配置的效果

#### 对比总结

| 维度 | MemGPT | Mem0 | Letta |
|------|--------|------|-------|
| **核心隐喻** | 操作系统虚拟内存 | 记忆即服务 | 有状态 Agent 平台 |
| **记忆管理** | LLM 自主管理 | 自动提取+规则 | LLM自主+人类可编辑 |
| **架构层级** | 研究原型 | 中间件库 | 完整平台 |
| **适用场景** | 研究、长对话 | 生产集成 | 企业级 Agent |
| **记忆类型** | 分页消息 | 语义+情节 | 多层记忆 |
| **冲突处理** | LLM 决策 | 自动更新 | 人工+自动 |
| **可观测性** | 低 | 中 | 高（记忆可视化） |

#### 面试中的加分分析

**"你认为理想的 Agent 记忆系统应该是什么样的？"**

> 理想的记忆系统应该做到三点：
> 1. **自适应**：根据任务复杂度自动调节记忆粒度——简单对话不需要复杂记忆
> 2. **可解释**：Agent 引用记忆时应标注来源，用户可查看和编辑
> 3. **分层遗忘**：不是简单删除，而是从精确记忆→模糊摘要→最终遗忘的渐进过程
>
> 当前框架的共同不足是**缺乏记忆质量评估**——没有机制判断"记住的东西是否正确、是否有用"。未来的记忆系统应该包含记忆验证和自我纠错机制。

</details>

---

## 三、当日小结

### 核心知识点回顾

| # | 知识点 | 一句话总结 | 重要程度 |
|---|--------|-----------|---------|
| 1 | 四层记忆架构 | 工作记忆→短期→长期→外部，从快到慢、从易失到持久 | ⭐⭐⭐⭐⭐ |
| 2 | 记忆写入策略 | 不是所有信息都值得记，需要重要性判断+去重 | ⭐⭐⭐⭐ |
| 3 | 记忆检索策略 | 向量相似度+时间衰减+重要性+频率的多因子融合 | ⭐⭐⭐⭐⭐ |
| 4 | 遗忘机制 | 遗忘是特性不是缺陷，防止噪声积累 | ⭐⭐⭐⭐ |
| 5 | 向量数据库选型 | Pinecone(托管)/Milvus(大规模)/pgvector(已有PG)/Chroma(原型) | ⭐⭐⭐ |
| 6 | 上下文压缩 | 滑动窗口+摘要+选择性保留+外部化 | ⭐⭐⭐⭐ |
| 7 | 记忆系统设计 | 分片+多级缓存+异步写入+Embedding服务 | ⭐⭐⭐⭐⭐ |
| 8 | 记忆框架 | MemGPT(OS隐喻)/Mem0(服务化)/Letta(平台化) | ⭐⭐⭐ |
| 9 | 记忆类型 | 语义(事实)/情节(经历)/程序(技能)三类长期记忆 | ⭐⭐⭐⭐ |
| 10 | 记忆注入 | 通过 system prompt 占位符动态注入检索结果 | ⭐⭐⭐ |

### 面试速记卡

| 卡片 | 正面 | 背面 |
|------|------|------|
| 卡1 | Agent 四层记忆？ | 工作记忆(上下文窗口) → 短期(会话缓冲+摘要) → 长期(向量DB) → 外部(文件/DB/API) |
| 卡2 | 记忆检索的核心公式？ | Score = 0.45×相似度 + 0.20×时间衰减 + 0.20×重要性 + 0.15×访问频率 |
| 卡3 | 为什么需要遗忘？ | ①提高信噪比 ②控制存储成本 ③避免过时信息误导 ④解决记忆冲突 |
| 卡4 | 向量DB选型关键？ | 托管(Pinecone) vs 开源(Milvus) vs 嵌入式(Chroma) vs PG扩展(pgvector) |
| 卡5 | 上下文压缩四策略？ | 滑动窗口丢弃 / LLM摘要压缩 / 选择性保留高分 / 外部化到向量DB |
| 卡6 | MemGPT 核心创新？ | LLM通过函数调用自主管理记忆(mread/mwrite/msearch)，类比OS虚拟内存 |
| 卡7 | 记忆写入何时触发？ | 用户告知偏好 / 重要决策 / 任务完成失败 / 用户纠正 / 发现新事实 |
| 卡8 | 百万用户记忆系统瓶颈？ | ①Embedding计算(QPS+成本) ②向量检索延迟 ③存储容量 ④写入吞吐 |

### 易错点提醒

| # | 易错点 | 正确理解 |
|---|--------|---------|
| 1 | "记忆就是保存对话历史" | ❌ 对话历史是短期记忆，长期记忆需要**提取**关键信息而非全量保存 |
| 2 | "记忆越多越好" | ❌ 噪声记忆降低检索质量，遗忘机制同样重要 |
| 3 | "向量检索就够了" | ❌ 纯向量检索缺少时间、重要性维度，需要多因子重排 |
| 4 | "RAG 和记忆是一回事" | ❌ RAG 检索外部知识库，记忆检索 Agent 自身经历 |
| 5 | "每轮都写入长期记忆" | ❌ 写入需判断价值，大部分对话不值得长期记忆 |
| 6 | "上下文窗口够大就不需要记忆" | ❌ 窗口再大也无法跨会话保持，且成本与长度正相关 |
| 7 | "遗忘就是删除" | ❌ 理想遗忘是渐进的：精确→模糊摘要→最终删除 |
| 8 | "记忆系统不需要运维" | ❌ 需要定期衰减、去重合并、容量管理 |

### 自测检查清单

- [ ] 能画出四层记忆架构图并解释每层的载体和特点
- [ ] 能写出记忆检索的多因子评分公式
- [ ] 能解释遗忘机制的必要性和至少 3 种遗忘策略
- [ ] 能对比至少 3 种向量数据库的优劣势
- [ ] 能写出上下文压缩的滑动窗口+摘要方案伪代码
- [ ] 能设计百万用户记忆系统的分片和缓存策略
- [ ] 能解释 MemGPT 的操作系统隐喻
- [ ] 能区分语义记忆、情节记忆、程序记忆
- [ ] 能写出记忆注入 prompt 的构造方式
- [ ] 能讨论记忆系统的 3 个当前局限和改进方向

### 延伸阅读

| 资源 | 类型 | 价值 |
|------|------|------|
| [MemGPT: Towards LLMs as Operating Systems](https://arxiv.org/abs/2310.08560) | 论文 | 记忆系统的 OS 隐喻开创性工作 |
| [Mem0 官方文档](https://docs.mem0.ai/) | 文档 | 生产级记忆系统的 API 设计 |
| [Letta (原 MemGPT) GitHub](https://github.com/letta-ai/letta) | 代码 | MemGPT 的产品化实现 |
| [Generative Agents 论文](https://arxiv.org/abs/2304.03442) | 论文 | 斯坦福小镇 Agent 的记忆架构 |
| [ChromaDB 文档](https://docs.trychroma.com/) | 文档 | 轻量向量数据库使用 |

---

## 四、明日预告

> **Day 06** 将深入 **Agent 规划与推理范式**，包括：
> - 推理范式全景：CoT / ToT / GoT / PoT
> - 规划策略：前向规划 vs 逆向规划
> - Plan-and-Execute 模式
> - Reflexion / Self-Refine / Tree of Thoughts
> - 多 Agent 协作规划
> - 规划失败的原因与恢复策略
> - 推理与规划的系统设计面试题
