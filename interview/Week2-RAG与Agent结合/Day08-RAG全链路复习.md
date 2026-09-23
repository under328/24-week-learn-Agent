# Day 08 — RAG 全链路复习

> **Week 2 · Day 1** | AI Agent 面试 31 天冲刺计划
> 学习时长建议: 3-4 小时 | 难度: ★★★☆☆ | 面试频率: ★★★★★

## 学习目标

经过 Week 1 的 Agent 基础训练(ReAct / Function Calling / MCP / 记忆 / 规划),我们已具备构建"会思考、会调用工具"的 Agent 能力。Week 2 转向 **RAG 与 Agent 结合**——这是企业级 Agent 落地最核心的能力:让 Agent 基于私有知识库回答问题,而非依赖预训练时固化的知识。

Day 08 作为 Week 2 开篇,目标是**把 RAG 的完整链路从摄入到生成一次性串起来**,形成一张可复用的"知识地图"。完成今天的学习后,你应该能够:

1. 用一句话讲清楚 RAG 是什么、为什么需要它,并能与"微调"路线做正面对比;
2. 画出 RAG 的**索引阶段**和**查询阶段**完整数据流,讲清楚每个环节的输入/输出;
3. 针对**分块、Embedding、向量索引、混合检索、Rerank** 五个核心环节,给出选型理由而非死记结论;
4. 手写一个最小可运行的 RAG 查询引擎(mock LLM),并能在面试白板上画出来;
5. 完成一个支持多部门、权限控制、十万级文档的企业知识库 RAG 系统设计。

## 面试定位说明

RAG 是大模型应用层最高频的考点,几乎每一场 Agent / LLM 应用岗的面试都会涉及。面试官常从三个角度切入:

- **概念层**:RAG vs 微调、朴素 RAG vs 高级 RAG、为什么需要 Rerank —— 考察你对"为什么这么做"的理解深度;
- **工程层**:分块策略、Embedding 选型、向量索引算法、混合检索 + RRF —— 考察你能否落地,而不是只会调 LangChain API;
- **系统层**:企业知识库 RAG 设计、多租户、权限、更新策略 —— 考察你有没有真实生产经验。

今天的 10 道题分别对应这三个层次,务必做到**能讲、能画、能写**。

---

## 今日知识图谱

```
RAG 全链路 (Day 08)
│
├── 1. 概念定位
│   ├── 什么是 RAG (Retrieval-Augmented Generation)
│   ├── 为什么需要 RAG (知识时效 / 私有知识 / 幻觉 / 成本)
│   └── RAG vs Fine-tuning (成本、更新、可解释、可控)
│
├── 2. 完整链路架构
│   ├── 索引阶段 (Indexing)
│   │   ├── 文档加载 (Loaders)
│   │   ├── 文档分块 (Chunking)
│   │   ├── Embedding 向量化
│   │   └── 写入向量库 (Vector Store)
│   │
│   └── 查询阶段 (Query / Retrieval)
│       ├── Query 改写 (Rewrite / HyDE / Step-back)
│       ├── Embedding 查询向量化
│       ├── 检索 (Dense / Sparse / Hybrid)
│       ├── 重排序 (Rerank / Cross-Encoder)
│       ├── Prompt 组装 (Context + Question)
│       └── 生成 (LLM Generate)
│
├── 3. 核心环节深挖
│   ├── 分块策略 (固定 / 递归 / 语义 / 父子 / 结构感知)
│   ├── Embedding 选型 (BGE / OpenAI / Cohere / 选型维度)
│   ├── 向量索引 (Flat / IVF / HNSW / 选型对比)
│   ├── 混合检索 (BM25 + Dense + RRF 融合)
│   └── Reranker (Bi-Encoder vs Cross-Encoder)
│
├── 4. 架构演进
│   ├── Naive RAG
│   ├── Advanced RAG (检索前后优化)
│   └── Modular RAG (模块可插拔)
│
└── 5. 工程实战
    ├── 手撕 RAG 查询引擎 (Python mock)
    └── 企业知识库 RAG 系统设计
```

---

## 面试题(共 10 道)

### Q1: 什么是 RAG? 为什么需要 RAG? RAG vs 微调的优劣对比?

<details>
<summary>点击展开答案</summary>

**RAG(Retrieval-Augmented Generation,检索增强生成)** 是一种在生成阶段前,先从外部知识库检索相关文档,再将检索到的文档作为上下文喂给 LLM 进行生成的架构。它最早由 Facebook AI 在 2020 年论文《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》中提出。

**为什么需要 RAG?** 核心动机有四点:

1. **知识时效性**:LLM 的训练知识截止到某个时间点,无法回答之后发生的事(如"今天的新闻")。RAG 通过实时检索外部库解决。
2. **私有知识**:企业内部文档、产品手册、客户数据从未进入预训练,LLM 一无所知。RAG 让 LLM 能"看到"私有知识。
3. **幻觉控制**:LLM 容易编造事实。RAG 把生成"锚定"在检索到的真实文档上,显著降低幻觉率。
4. **成本与可控性**:相比微调,RAG 无需重新训练,知识更新只需更新知识库;且可追溯(能告诉用户答案来自哪篇文档)。

**RAG vs Fine-tuning 对比表:**

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| **知识更新成本** | 低,只需更新知识库 | 高,需重新训练 |
| **知识时效性** | 实时(检索即用) | 训练时固化,易过时 |
| **私有知识接入** | 直接检索,无需训练 | 需用私有数据训练 |
| **幻觉控制** | 强,可锚定到文档 | 弱,仍可能编造 |
| **可解释 / 可追溯** | 强,可返回引用来源 | 弱,黑盒 |
| **训练成本** | 几乎为零(只需 Embedding) | 高,GPU + 数据标注 |
| **推理延迟** | 多一次检索,延迟较高 | 单次前向,延迟低 |
| **适合场景** | 事实问答、知识库、最新信息 | 风格学习、领域术语、格式控制 |
| **参数化知识** | 外置(向量库) | 内化(权重) |
| **可组合性** | 与微调可叠加 | 与 RAG 可叠加 |

**经典结论(面试金句):**
> "RAG 解决的是'模型不知道什么',微调解决的是'模型不会做什么'。前者补知识,后者补能力。生产中两者常叠加使用——先微调让模型学会领域语言风格,再用 RAG 注入实时事实。"

**何时该用 RAG 而非微调?**
- 知识频繁变化 → RAG
- 需要可追溯引用 → RAG
- 数据量大但更新频繁 → RAG
- 需要改变模型语气/格式/特定任务能力 → 微调
- 二者结合:RAG 提供事实,微调提供风格

</details>

### Q2: RAG 完整链路架构(索引阶段 + 查询阶段),画出完整数据流图

<details>
<summary>点击展开答案</summary>

RAG 链路分为**离线索引阶段(Indexing)**和**在线查询阶段(Query/Retrieval)**两大块。索引阶段把原始文档处理成可检索的向量,查询阶段把用户问题转成向量、检索、组装、生成。

**完整数据流图:**

```
┌─────────────────────────── 索引阶段 (离线) ───────────────────────────┐
│                                                                       │
│  原始文档          文档加载器         分块器            Embedding       │
│  ┌──────┐        ┌──────────┐     ┌─────────┐       ┌──────────┐    │
│  │ PDF  │──────▶│ LangChain │────▶│ Recursive│─────▶│  BGE /   │    │
│  │ Word │        │ Unstruct  │     │  Splitter│      │  OpenAI  │    │
│  │ HTML │        │ LlamaParse│     │ Semantic │       │ Embedding│    │
│  │ MD   │        └──────────┘     └─────────┘       └─────┬────┘    │
│  └──────┘                                │                  │         │
│                                          │  (chunk + meta)  │ (vector) │
│                                          ▼                  ▼         │
│                                  ┌──────────────────────────────┐   │
│                                  │   向量库 (Vector Store)        │   │
│                                  │  Milvus / Qdrant / PGVector   │   │
│                                  │  ┌────────────────────────┐  │   │
│                                  │  │ id | vector | text |   │  │   │
│                                  │  │    |        | meta |   │  │   │
│                                  │  └────────────────────────┘  │   │
│                                  └──────────────────────────────┘   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ (离线构建一次,在线查询复用)
                                        ▼
┌─────────────────────────── 查询阶段 (在线) ───────────────────────────┐
│                                                                       │
│  用户问题         Query 改写          Query Embedding                   │
│  ┌────────┐     ┌───────────┐       ┌──────────┐                      │
│  │ "公司  │────▶│ HyDE /    │─────▶│  Embedding│                      │
│  │ 病假  │      │ Step-back │       │  Model    │                      │
│  │ 政策?"│      │ Rewrite   │       └─────┬────┘                      │
│  └────────┘     └───────────┘             │ (query vector)            │
│                                          ▼                            │
│                          ┌──────────────────────────────┐            │
│                          │      混合检索 (Hybrid)         │            │
│                          │  ┌─────────┐    ┌─────────┐  │            │
│                          │  │ Dense   │    │ BM25    │  │            │
│                          │  │ (向量)  │    │ (关键词)│  │            │
│                          │  └────┬────┘    └────┬────┘  │            │
│                          │       └──────┬───────┘       │            │
│                          │         RRF 融合            │            │
│                          └──────────────┬───────────────┘            │
│                                         ▼                            │
│                          ┌──────────────────────────────┐            │
│                          │    Reranker (Cross-Encoder)   │            │
│                          │   重排序 Top-K → Top-N        │            │
│                          └──────────────┬───────────────┘            │
│                                         ▼                            │
│                          ┌──────────────────────────────┐            │
│                          │   Prompt 组装                  │            │
│                          │  System: 你是助手,基于上下文回答│            │
│                          │  Context: [chunk1, chunk2...] │            │
│                          │  Question: 用户原始问题        │            │
│                          └──────────────┬───────────────┘            │
│                                         ▼                            │
│                          ┌──────────────────────────────┐            │
│                          │      LLM 生成                  │            │
│                          │   GPT-4 / Claude / Qwen       │            │
│                          └──────────────┬───────────────┘            │
│                                         ▼                            │
│                          ┌──────────────────────────────┐            │
│                          │   答案 + 引用来源              │            │
│                          └──────────────────────────────┘            │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

**每个环节的输入/输出速查表:**

| 环节 | 输入 | 输出 | 关键技术 |
|------|------|------|---------|
| 文档加载 | PDF/Word/HTML | 纯文本 + 元数据 | LangChain Loaders, LlamaParse |
| 分块 | 长文本 | chunk 列表 | Recursive/Token Splitter |
| Embedding | chunk 文本 | 高维向量 (768/1536d) | BGE, OpenAI text-embedding-3 |
| 写入向量库 | 向量 + 元数据 | 索引结构 | HNSW / IVF |
| Query 改写 | 原始问题 | 改写后问题 | HyDE, Step-back, Multi-Query |
| Query Embedding | 改写后问题 | 查询向量 | 同索引阶段模型 |
| 混合检索 | 查询向量 + 原始查询 | Top-K 候选 | Dense + BM25 + RRF |
| Rerank | Top-K 候选 + 查询 | Top-N 重排 | Cross-Encoder |
| Prompt 组装 | Top-N + 查询 | 完整 Prompt | 模板 + 截断策略 |
| 生成 | Prompt | 答案 + 引用 | LLM |

**面试讲解要点:**
- 强调"索引阶段离线一次性构建,查询阶段每次请求在线执行"——这是 RAG 比微调便宜的根本原因。
- 指出每个环节都是可替换的模块(分块器、Embedding、向量库、Reranker 都可独立升级)。
- 提一句"检索质量决定 RAG 上限,生成质量决定下限"——检索是 RAG 的瓶颈所在。

</details>

### Q3: 文档分块策略(固定/递归/语义/父子/结构感知),各优缺点和适用场景?

<details>
<summary>点击展开答案</summary>

分块(Chunking)是 RAG 中**最容易被低估但影响最大**的环节。分块粒度直接决定检索精度:太大 → 噪声多、Embedding 不聚焦;太小 → 上下文断裂、语义不完整。

**五种主流分块策略对比:**

| 策略 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **固定分块** (Fixed-size) | 按固定 token 数切分,可加重叠 | 实现简单、速度快 | 可能切断句子/段落 | 快速原型、均匀文本 |
| **递归分块** (Recursive) | 按分隔符优先级递归切分(`\n\n` → `\n` → `.` → 空格),最后兜底 token | 优先保持段落完整,LangChain 默认 | 仍可能语义不完整 | 通用文本(最常用) |
| **语义分块** (Semantic) | 用 Embedding 计算相邻句子相似度,在相似度骤降处切分 | 语义边界准确 | 需调用 Embedding,成本高 | 高质量问答、长文档 |
| **父子分块** (Parent-Child / Small-to-Big) | 检索用小块(精准),生成时返回其所属大块(上下文完整) | 兼顾检索精度与上下文 | 存储翻倍、需维护父子映射 | 长文档问答、需上下文场景 |
| **结构感知分块** (Structure-aware) | 按 Markdown 标题/HTML 标签/代码函数切分 | 保留文档结构,元信息丰富 | 依赖文档格式 | Markdown 文档、代码库、API 文档 |

**代码示例 — 递归分块(LangChain 风格):**

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,          # 每块最大 500 字符
    chunk_overlap=50,        # 块间重叠 50 字符,防止边界信息丢失
    separators=["\n\n", "\n", "。", ".", " ", ""],  # 中文优先按段落
)

chunks = splitter.split_text(long_text)
```

**代码示例 — 语义分块(基于 Embedding 相似度):**

```python
import numpy as np

def semantic_chunk(text, embed_fn, threshold_percentile=95):
    """
    按句子 Embedding 相似度的骤降点切分。
    """
    sentences = split_to_sentences(text)               # 1. 切句
    embeddings = np.array([embed_fn(s) for s in sentences])  # 2. 向量化
    # 3. 计算相邻句子的余弦相似度
    sims = cosine_similarity(embeddings[:-1], embeddings[1:]).diagonal()
    # 4. 相似度低于阈值的点作为切分边界
    threshold = np.percentile(sims, 100 - threshold_percentile)
    split_points = [i for i, s in enumerate(sims) if s < threshold]
    # 5. 按切分点合并句子成块
    return merge_by_points(sentences, split_points)
```

**代码示例 — 父子分块(Small-to-Big):**

```python
# 父块:大粒度(如 2000 token),用于生成时提供上下文
# 子块:小粒度(如 200 token),用于精准检索
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
child_splitter  = RecursiveCharacterTextSplitter(chunk_size=200,  chunk_overlap=20)

parent_chunks = parent_splitter.split_text(doc)
store = {}  # parent_id -> parent_text
for p in parent_chunks:
    pid = hash(p)
    store[pid] = p
    children = child_splitter.split_text(p)
    for c in children:
        index.add(emb(c), metadata={"parent_id": pid, "text": c})

# 检索时:用子块命中,但返回父块给 LLM
hits = index.search(query_emb, k=10)
parent_ids = list(dict.fromkeys(h["parent_id"] for h in hits))  # 去重保序
context = [store[pid] for pid in parent_ids[:3]]                 # 取 Top-3 父块
```

**选型决策树:**

```
文档是否结构化 (Markdown/HTML/代码)?
├── 是 → 结构感知分块 (按标题/函数切)
└── 否 → 质量要求高吗?
        ├── 高 → 语义分块 (或父子分块)
        └── 一般 → 递归分块 (生产默认)
                  └── 原型/MVP → 固定分块
```

**关键参数调优经验:**
- `chunk_size`:中文 300-500 字符,英文 500-1000 token 为常用范围;问答任务偏小,摘要任务偏大。
- `chunk_overlap`:取 chunk_size 的 10%-20%,避免边界信息丢失。
- 不要一味追求大 chunk——Embedding 模型对长文本语义会有稀释效应。

</details>

### Q4: Embedding 模型选型(BGE / OpenAI / Cohere 等),选型维度?

<details>
<summary>点击展开答案</summary>

Embedding 模型把文本映射到高维向量空间,是 RAG 检索的"地基"。选型直接影响召回率,且一旦上线迁移成本高(所有历史向量需重新生成),所以选型要慎重。

**主流 Embedding 模型对比(2024-2025):**

| 模型 | 厂商 | 维度 | 开源 | 中文支持 | MTEB 均分 | 部署方式 | 备注 |
|------|------|------|------|---------|----------|---------|------|
| **bge-large-zh-v1.5** | 智源 | 1024 | 是 | 优 | 中文榜 Top | 本地 GPU/CPU | 中文场景首选开源 |
| **bge-m3** | 智源 | 1024 | 是 | 优 | 多语言 Top | 本地 | 支持稠密+稀疏+多向量 |
| **text-embedding-3-large** | OpenAI | 3072(可降维) | 否 | 良 | 全球 Top | API | 闭源、需翻墙 |
| **text-embedding-3-small** | OpenAI | 1536 | 否 | 良 | 中上 | API | 便宜 |
| **embed-english-v3** | Cohere | 1024 | 否 | 弱(英文优) | 英文 Top | API | 英文场景强 |
| **embed-multilingual-v3** | Cohere | 1024 | 否 | 良 | 多语言优 | API | 多语言 |
| **gte-large-zh** | 阿里 | 1024 | 是 | 优 | 中文前列 | 本地 | 与 BGE 竞争 |
| **jina-embeddings-v3** | Jina | 1024 | 是 | 良 | 中上 | 本地 | 长文本友好 |
| **voyage-3** | Voyage AI | 1024 | 否 | 良 | 全球 Top | API | 新秀,性能强 |

**选型维度(面试必答的"七维框架"):**

1. **语言匹配度**:中文优先 BGE/GTE,英文 OpenAI/Cohere/Voyage,多语言 bge-m3/Cohere multilingual。
2. **检索质量(MTEB / C-MTEB 榜单)**:看目标任务对应的子榜单(问答、检索、STS),不要只看均分。
3. **维度与存储成本**:维度越高,向量库存储和检索成本越高。OpenAI 3072d vs BGE 1024d,存储差 3 倍。
4. **部署方式**:能否本地部署?数据合规要求高的场景(金融、医疗)必须本地,只能选开源。
5. **推理延迟**:本地大模型 vs API 调用,需结合 QPS 评估。
6. **最大输入长度**:长文档场景需选支持长输入的(如 jina-v3 支持 8k token)。
7. **License**:商用是否允许?BGE 是 MIT,Cohere 是商业 API。

**代码示例 — BGE 本地推理:**

```python
from FlagEmbedding import FlagModel

model = FlagModel("BAAI/bge-large-zh-v1.5",
                  use_fp16=True,
                  query_instruction="为这个句子生成表示用于检索相关文章:")

# 索引阶段
doc_embeddings = model.encode_corpus(doc_chunks, batch_size=32)

# 查询阶段
query_embedding = model.encode_queries(["公司病假政策"])
```

**代码示例 — OpenAI Embedding(带降维):**

```python
from openai import OpenAI

client = OpenAI()

# text-embedding-3-large 支持降维,可在不损失太多精度的情况下省存储
resp = client.embeddings.create(
    model="text-embedding-3-large",
    input=doc_chunks,
    dimensions=1536,   # 从 3072 降到 1536
)
```

**面试金句:**
> "Embedding 选型本质是'质量-成本-合规'三角权衡。中文生产场景我倾向 BGE 系列:开源可本地、中文榜单领先、维度适中;如果用 OpenAI,记得用 dimensions 参数降维省成本。"

**易错点提醒:**
- 索引和查询**必须用同一个 Embedding 模型**,否则向量空间不一致,检索失效。
- BGE 等模型对 query 有特殊 instruction 前缀(如"为这个句子生成表示..."),query 和 doc 的前缀不同,别搞混。
- 不要把 Embedding 模型和 LLM 混为一谈——前者负责向量化,后者负责生成。

</details>

### Q5: 向量检索索引算法(HNSW / IVF / Flat),对比和选型?

<details>
<summary>点击展开答案</summary>

向量库的核心是**近似最近邻搜索(ANN, Approximate Nearest Neighbor)** 算法。数据量大时,精确检索(Flat)太慢,需要用近似算法以可接受的召回率换速度。

**三大主流算法对比:**

| 算法 | 原理 | 构建速度 | 查询速度 | 召回率 | 内存 | 适合数据量 | 增删改 |
|------|------|---------|---------|--------|------|----------|--------|
| **Flat** | 暴力遍历计算距离 | 极快(无需构建) | 慢 O(N) | 100% | 低 | <10k | 容易 |
| **IVF** | K-means 聚类,查询时只搜最近的 nprobe 个簇 | 中 | 快 O(N/nprobe) | 中高 | 中 | 10k-1M | 中等 |
| **HNSW** | 分层小世界图,在图上贪心搜索 | 慢 | 极快 O(log N) | 高 | 高(存图) | 1M-100M | 难(重建图) |
| **IVF-PQ** | IVF + 乘积量化压缩 | 中 | 快 | 中 | 极低 | 1M+ | 中等 |
| **DiskANN** | 图 + 磁盘存储 | 慢 | 中(磁盘 IO) | 高 | 低(磁盘) | 100M+ | 难 |

**1. Flat(暴力检索)**
- 直接对所有向量计算距离,取 Top-K。
- 召回率 100%,但 O(N) 复杂度,N 大时不可用。
- 适合数据量小(<1万)或需要精确结果的场景(如评估基准)。

**2. IVF(Inverted File Index)**
- 先用 K-means 把向量聚成 `nlist` 个簇,每个簇维护一个倒排表。
- 查询时,先找离 query 最近的 `nprobe` 个簇,只在这些簇内精确检索。
- `nprobe` 越大召回越高、速度越慢,是核心调参点。
- 适合中等数据量(10万-100万),且需要训练聚类中心。

```python
# FAISS 中的 IVF 示例
import faiss
nlist = 100  # 簇数
quantizer = faiss.IndexFlatIP(dim)
index = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
index.train(vectors)   # 需要训练
index.add(vectors)
index.nprobe = 10      # 查询时搜索 10 个簇
```

**3. HNSW(Hierarchical Navigable Small World)**
- 构建多层图:上层稀疏(快速跳越),下层密集(精细搜索)。
- 查询从最上层贪心向下,类似跳表的思想。
- 召回率高、查询极快,是**目前生产环境最常用的算法**(Milvus、Qdrant、pgvector 默认)。
- 缺点:内存占用大(存图结构)、构建慢、删除难。

```python
# HNSW 核心参数(Milvus / pgvector 通用)
{
    "M": 16,            # 每个节点的邻居数,越大召回越高、内存越大
    "ef_construction": 200,  # 构建时候选邻居数,越大质量越好、构建越慢
    "ef_search": 50,    # 查询时候选数,越大召回越高、查询越慢
}
```

**HNSW 参数调优经验:**
- `M`:16 是默认值,高质量场景调到 32-64。
- `ef_construction`:200 够用,追求极致可调到 500,但构建时间翻倍。
- `ef_search`:动态调整,在线服务可设 50,离线批量可设 200+。

**选型决策:**

```
数据量 < 1万 → Flat (精确,简单)
数据量 1万-100万,需要训练 → IVF (调 nprobe 平衡)
数据量 100万-1亿,内存充足 → HNSW (生产默认)
数据量 > 1亿,内存吃紧 → DiskANN / IVF-PQ
```

**面试金句:**
> "HNSW 是当前生产 RAG 的默认选择,本质是分层图+贪心搜索,用 O(log N) 换召回率。但要注意它内存占用大、删除难,所以频繁更新的场景要考虑 IVF 或带软删除的向量库(如 Qdrant)。"

</details>

### Q6: 混合检索(向量 + BM25 关键词) + RRF 融合的原理和实现?

<details>
<summary>点击展开答案</summary>

**为什么需要混合检索?**
- **Dense(向量)检索**擅长语义匹配(同义词、近义表达),但对**精确关键词、专有名词、代码标识符、产品型号**等不敏感。
- **Sparse(BM25)检索**基于词频,擅长精确匹配,但不理解语义(同义词召回弱)。
- 二者互补,混合检索能显著提升召回率,是生产 RAG 的标配。

**BM25 算法简述:**

BM25 是基于词频和逆文档频率的打分函数,是传统搜索引擎(Elasticsearch、Lucene)的核心:

```
score(q, d) = Σ IDF(qi) · (f(qi,d) · (k1+1)) / (f(qi,d) + k1·(1 - b + b·|d|/avgdl))

其中:
- f(qi,d):词 qi 在文档 d 中的频率
- |d|:文档长度,avgdl:平均文档长度
- k1, b:调节参数(典型 k1=1.2, b=0.75)
- IDF(qi) = log((N - n(qi) + 0.5) / (n(qi) + 0.5) + 1)
```

BM25 对长文档有惩罚(b 参数),对高频词有降权(IDF),适合"找包含特定词的文档"。

**为什么不能简单加权融合?**
- Dense 返回的是余弦相似度(范围 [-1, 1] 或 [0, 1]);
- BM25 返回的是无界分数(可能 0-30);
- 两者**量纲不同**,直接相加会被 BM25 的大数值主导。
- 且不同查询下两者的分数分布不同,固定权重不鲁棒。

**RRF(Reciprocal Rank Fusion,倒数排名融合)原理:**

RRF 不看绝对分数,只看**排名**,把每个检索器返回的文档按排名倒数打分再求和:

```
RRF_score(d) = Σ 1 / (k + rank_i(d))

其中:
- rank_i(d):文档 d 在第 i 个检索器结果中的排名(从 1 开始)
- k:平滑常数(典型 k=60),防止排名 1 的文档权重过大
```

RRF 的优点:
1. 无需归一化,量纲无关;
2. 对离群分鲁棒(只看排名);
3. 实现简单,效果稳定,是工业界默认融合方法。

**代码实现 — 混合检索 + RRF:**

```python
from rank_bm25 import BM25Okapi
import numpy as np

class HybridRetriever:
    def __init__(self, chunks, embed_fn, k=60):
        self.chunks = chunks
        self.k = k  # RRF 平滑常数
        # 1. 构建 BM25 索引
        tokenized = [c.split() for c in chunks]   # 中文需先分词
        self.bm25 = BM25Okapi(tokenized)
        # 2. 构建向量索引(简化用暴力检索)
        self.vectors = np.array([embed_fn(c) for c in chunks])

    def dense_search(self, query_vec, top_k=20):
        sims = self.vectors @ query_vec           # 内积(已归一化即余弦)
        idx = np.argsort(-sims)[:top_k]
        return [(self.chunks[i], i) for i in idx]

    def sparse_search(self, query, top_k=20):
        scores = self.bm25.get_scores(query.split())
        idx = np.argsort(-scores)[:top_k]
        return [(self.chunks[i], i) for i in idx]

    def hybrid_search(self, query, query_vec, top_k=10):
        dense_hits = self.dense_search(query_vec, top_k=20)
        sparse_hits = self.sparse_search(query, top_k=20)
        # RRF 融合
        rrf_score = {}
        for rank, (chunk, idx) in enumerate(dense_hits, 1):
            rrf_score[idx] = rrf_score.get(idx, 0) + 1 / (self.k + rank)
        for rank, (chunk, idx) in enumerate(sparse_hits, 1):
            rrf_score[idx] = rrf_score.get(idx, 0) + 1 / (self.k + rank)
        # 取融合后 Top-K
        sorted_idx = sorted(rrf_score, key=rrf_score.get, reverse=True)[:top_k]
        return [(self.chunks[i], rrf_score[i]) for i in sorted_idx]
```

**混合检索数据流:**

```
                ┌─── Dense (向量) ──── Top-20 ──┐
  Query  ──────┤                                  ├── RRF 融合 ── Top-10
                └─── BM25 (关键词) ── Top-20 ──┘
```

**进阶 — 加权 RRF:**

如果知道某个检索器更可靠,可加权重:

```python
# Dense 权重 0.7, BM25 权重 0.3
weights = {"dense": 0.7, "sparse": 0.3}
for rank, (_, idx) in enumerate(dense_hits, 1):
    rrf_score[idx] = rrf_score.get(idx, 0) + weights["dense"] / (k + rank)
```

**面试金句:**
> "生产 RAG 我一定上混合检索:Dense 抓语义,BM25 抓精确词,RRF 融合避免量纲问题。中文场景记得 BM25 前要先分词(jieba/HanLP),否则词频统计无意义。"

**易错点:**
- BM25 在中文场景**必须先分词**,否则按空格切分中文会失效。
- RRF 的 k 值通常取 60,过小会让 Top-1 权重过大,过大会让排名差异被抹平。
- 两个检索器的候选集要足够大(各取 Top-20+),否则融合效果打折。

</details>

### Q7: Reranker(Cross-Encoder)的作用,为什么需要重排序?

<details>
<summary>点击展开答案</summary>

**Reranker 的定位:**
混合检索(或单路检索)返回的 Top-K 候选,**召回率高但精度不一定高**——里面可能混入相关度低的噪声。Reranker 用更重但更精准的模型对 Top-K 重新打分,选出真正最相关的 Top-N(N << K)喂给 LLM。

**为什么需要 Rerank?核心原因:Bi-Encoder vs Cross-Encoder 的精度差异。**

| 类型 | 代表 | 原理 | 速度 | 精度 | 用途 |
|------|------|------|------|------|------|
| **Bi-Encoder** (双塔) | BGE, OpenAI Embedding | Query 和 Doc 分别编码成向量,算余弦相似度 | 极快(可预计算) | 中 | 一阶段召回 |
| **Cross-Encoder** (交叉编码) | bge-reranker, Cohere Rerank | Query 和 Doc 拼接后输入 Transformer,输出相关度分数 | 慢(不可预计算) | 高 | 二阶段重排 |

**精度差异的根本原因:**
- Bi-Encoder 把 Query 和 Doc **独立编码**,两者在向量空间交互有限,丢失细粒度匹配信息。
- Cross-Encoder 把 `[CLS] Query [SEP] Doc [SEP]` 拼接输入,Transformer 的注意力让 Query 和 Doc 的每个 token **全量交互**,能捕捉"这个词是否真的相关"。

**典型两阶段检索架构:**

```
Query
  │
  ├──▶ Bi-Encoder (快) ──▶ 从 100万文档召回 Top-100
  │                          │
  │                          ▼
  └──▶ Cross-Encoder (精) ──▶ 从 Top-100 重排取 Top-5
                                 │
                                 ▼
                              喂给 LLM
```

**代码实现 — 用 BGE Reranker:**

```python
from FlagEmbedding import FlagReranker

reranker = FlagReranker("BAAI/bge-reranker-large", use_fp16=True)

def rerank(query, candidates, top_n=5):
    """
    candidates: List[str],从混合检索得到的 Top-K 文本
    """
    pairs = [[query, c] for c in candidates]
    scores = reranker.compute_score(pairs)  # 返回每对的相关度分数
    ranked = sorted(zip(candidates, scores), key=lambda x: -x[1])
    return ranked[:top_n]

# 使用
top_k_chunks = [c for c, _ in hybrid_results]   # 混合检索 Top-20
top_n_chunks = rerank(query, top_k_chunks, top_n=5)
```

**主流 Reranker 模型:**

| 模型 | 厂商 | 开源 | 中文 | 部署 |
|------|------|------|------|------|
| bge-reranker-large | 智源 | 是 | 优 | 本地 |
| bge-reranker-v2-m3 | 智源 | 是 | 优 | 本地,多语言 |
| Cohere Rerank 3 | Cohere | 否 | 良 | API |
| jina-reranker-v2 | Jina | 是 | 良 | 本地 |
| Voyage Rerank | Voyage | 否 | 良 | API |

**Reranker 调优经验:**
- **Top-K → Top-N**:常见 100→5 或 20→5,N 越小上下文越精,但可能漏召回。
- **批处理**:Cross-Encoder 慢,务必 batch 推理,可用 ONNX/TensorRT 加速。
- **缓存**:对同一 query 的 rerank 结果可短期缓存。
- **不是必须**:小数据集、简单问答可不用 Rerank,直接用 Dense 结果;复杂问答、多路召回强烈建议加。

**为什么不直接用 Cross-Encoder 检索全部文档?**
- 100 万文档逐对打分需要 100 万次 Transformer 前向,延迟不可接受(分钟级)。
- 所以用 Bi-Encoder 先粗筛到 Top-100,再用 Cross-Encoder 精排——这是"漏斗式"设计的经典应用。

**面试金句:**
> "Rerank 是 RAG 精度的'最后一公里'。Bi-Encoder 负责'快但粗'地从百万级召回 Top-100,Cross-Encoder 负责'慢但精'地重排出 Top-5。这种两阶段漏斗架构和推荐系统的'召回-精排'是同一个思想。"

</details>

### Q8: 朴素 RAG vs 高级 RAG vs 模块化 RAG 的演进?

<details>
<summary>点击展开答案</summary>

RAG 架构经历了三个阶段的演进,对应论文《Retrieval-Augmented Generation for Large Language Models: A Survey》(2023)中的分类。理解这个演进能展示你对 RAG 体系的系统认知。

**三阶段对比总表:**

| 维度 | Naive RAG | Advanced RAG | Modular RAG |
|------|-----------|--------------|-------------|
| **提出时间** | 2020 (Facebook) | 2023 | 2023-2024 |
| **索引阶段** | 简单分块 + Embedding | 优化分块 + 元数据 + 混合索引 | 可插拔模块 |
| **检索前优化** | 无 | Query 改写 / HyDE / Step-back | 多种策略可选 |
| **检索方式** | 单路 Dense | 混合检索 (Dense + Sparse) | 多检索器协同 |
| **检索后优化** | 无 | Rerank + 上下文压缩 | 自适应压缩 |
| **生成策略** | 单次生成 | 迭代 / 自我修正 | 多 Agent 协作 |
| **可扩展性** | 低 | 中 | 高(模块化) |
| **典型问题** | 召回差、噪声多 | 仍依赖固定流程 | 复杂度高 |
| **适用场景** | 原型 / 简单问答 | 生产主流 | 复杂推理 / Agentic-RAG |

**1. Naive RAG(朴素 RAG)**

最基础的"检索-生成"管线,流程固定:

```
Index: 文档 → 固定分块 → Embedding → 向量库
Query:  问题 → Embedding → Top-K 检索 → 拼接 Prompt → LLM 生成
```

**痛点:**
- 检索质量低:固定分块语义不完整,单路 Dense 漏召回。
- 噪声多:Top-K 里混入无关文档,污染生成。
- 无 query 优化:用户问题表达不清时检索失效。
- 无迭代:一次检索定生死,错了不纠正。

**2. Advanced RAG(高级 RAG)**

在 Naive RAG 基础上,围绕"检索前(Pre-Retrieval)+ 检索中(Retrieval)+ 检索后(Post-Retrieval)"三环节优化:

```
                    ┌─ Pre-Retrieval ─┐
                    │  Query 改写      │
                    │  HyDE           │
                    │  Step-back      │
                    │  Multi-Query    │
                    └────────┬────────┘
                             ▼
                    ┌─ Retrieval ─────┐
                    │  混合检索        │
                    │  Dense + BM25   │
                    │  RRF 融合       │
                    └────────┬────────┘
                             ▼
                    ┌─ Post-Retrieval ┐
                    │  Rerank         │
                    │  上下文压缩      │
                    │  去重 / 截断     │
                    └────────┬────────┘
                             ▼
                       LLM 生成
```

**各环节优化技术:**

| 环节 | 技术 | 作用 |
|------|------|------|
| Pre-Retrieval | Query Rewriting | 把口语化问题改写成更适合检索的形式 |
| Pre-Retrieval | HyDE (Hypothetical Document) | 先让 LLM 生成假设答案,用答案检索(答案比问题更接近文档) |
| Pre-Retrieval | Step-back Prompting | 把具体问题抽象成更高层问题再检索 |
| Pre-Retrieval | Multi-Query | LLM 生成多个变体问题,并行检索取并集 |
| Retrieval | 混合检索 | Dense + BM25 + RRF |
| Retrieval | 元数据过滤 | 先按部门/时间过滤再向量检索 |
| Post-Retrieval | Rerank | Cross-Encoder 重排 |
| Post-Retrieval | Context Compression | 用小模型压缩冗长 chunk |
| Post-Retrieval | Contextual Compression | 只保留与 query 相关的句子 |

**3. Modular RAG(模块化 RAG)**

把 RAG 拆成可插拔模块,根据任务灵活编排,甚至引入迭代、反思、Agent:

```
┌─────────────────────────────────────────────────┐
│              Modular RAG 编排层                   │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐        │
│  │Router│  │Retrieve│ │Rerank│  │Generate│       │
│  └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘        │
│     │         │         │         │             │
│  ┌──▼───┐  ┌──▼───┐  ┌──▼───┐  ┌──▼───┐        │
│  │Judge │  │Memory│  │Rewrite│  │Reflect│       │
│  └──────┘  └──────┘  └──────┘  └──────┘        │
└─────────────────────────────────────────────────┘
```

**Modular RAG 的关键能力:**
- **Retrieval 模块可替换**:Dense / Sparse / Graph / Web Search 按需切换。
- **Judge 模块(路由)**:判断是否需要检索、检索哪个库。
- **Reflect 模块(自我修正)**:评估生成答案质量,不满意则重新检索。
- **Iterative(迭代)**:多轮检索-生成,逐步逼近答案。
- **Agentic-RAG**:用 Agent 决策"何时检索、检索什么、是否足够",这是 Day09 的主题。

**演进的本质:**

```
Naive RAG      → "固定流水线,能跑就行"
Advanced RAG   → "在固定流水线上做局部优化"
Modular RAG    → "拆成乐高积木,按需编排"
Agentic-RAG    → "让 Agent 自己决定怎么编排"(Day09)
```

**面试金句:**
> "RAG 演进是从'静态流水线'到'动态可编排'的过程。Naive RAG 是 V1,Advanced RAG 是当前生产主流,Modular RAG 是未来方向——而 Agentic-RAG 把编排权交给 Agent,是 RAG 和 Agent 的真正融合点,也是明天 Day09 的内容。"

</details>

### Q9: 手撕代码题 — 实现一个完整的 RAG 查询引擎(Python,mock LLM)

<details>
<summary>点击展开答案</summary>

**题目:** 实现一个最小可运行的 RAG 查询引擎,包含分块、Embedding、混合检索、Rerank、生成五个环节。用 mock 函数模拟 Embedding 模型和 LLM,代码可直接运行。

**完整实现:**

```python
"""
最小可运行 RAG 查询引擎
包含: 递归分块 + Mock Embedding + 混合检索(Dense+BM25+RRF) + Mock Rerank + Mock LLM 生成
"""
import re
import math
import numpy as np
from typing import List, Dict, Tuple
from collections import defaultdict


# ============================================================
# 1. 分块器(递归分块,简化版)
# ============================================================
class RecursiveChunker:
    def __init__(self, chunk_size: int = 200, overlap: int = 20):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.separators = ["\n\n", "\n", "。", ".", " ", ""]

    def split(self, text: str) -> List[str]:
        chunks = []
        # 简化:按段落 + 句号切,再按 chunk_size 合并
        sentences = re.split(r"(?<=[。.!?])\s*", text)
        buf = ""
        for s in sentences:
            if len(buf) + len(s) <= self.chunk_size:
                buf += s
            else:
                if buf:
                    chunks.append(buf.strip())
                # 保留 overlap
                buf = buf[-self.overlap:] + s if self.overlap else s
        if buf.strip():
            chunks.append(buf.strip())
        return chunks


# ============================================================
# 2. Mock Embedding 模型(用词袋哈希模拟向量)
# ============================================================
class MockEmbedder:
    """
    用词袋 + 哈希模拟 Embedding,真实场景替换为 BGE / OpenAI。
    保证:相同文本 → 相同向量;相似文本 → 高余弦相似度。
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def _tokenize(self, text: str) -> List[str]:
        # 中文按字切,英文按空格切(简化)
        return list(text.replace(" ", "")) if any('\u4e00' <= c <= '\u9fff' for c in text) \
            else text.lower().split()

    def embed(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim)
        for tok in self._tokenize(text):
            h = hash(tok) % self.dim
            vec[h] += 1.0
        # L2 归一化,使内积 = 余弦相似度
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        return np.array([self.embed(t) for t in texts])


# ============================================================
# 3. BM25 稀疏检索
# ============================================================
class BM25:
    def __init__(self, docs: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = docs
        self.tokenized = [d.split() if not any('\u4e00' <= c <= '\u9fff' for c in d)
                          else list(d) for d in docs]
        self.N = len(docs)
        self.avgdl = sum(len(d) for d in self.tokenized) / max(self.N, 1)
        # 计算 IDF
        self.df = defaultdict(int)
        for toks in self.tokenized:
            for t in set(toks):
                self.df[t] += 1
        self.idf = {t: math.log((self.N - n + 0.5) / (n + 0.5) + 1)
                    for t, n in self.df.items()}

    def score(self, query: str) -> List[float]:
        q_tokens = query.split() if not any('\u4e00' <= c <= '\u9fff' for c in query) \
                   else list(query)
        scores = []
        for toks in self.tokenized:
            tf = defaultdict(int)
            for t in toks:
                tf[t] += 1
            s = 0.0
            for q in q_tokens:
                if q not in self.idf:
                    continue
                f = tf.get(q, 0)
                s += self.idf[q] * (f * (self.k1 + 1)) / \
                     (f + self.k1 * (1 - self.b + self.b * len(toks) / self.avgdl))
            scores.append(s)
        return scores


# ============================================================
# 4. 混合检索(Dense + BM25 + RRF 融合)
# ============================================================
class HybridRetriever:
    def __init__(self, chunks: List[str], embedder: MockEmbedder, k_rrf: int = 60):
        self.chunks = chunks
        self.embedder = embedder
        self.k_rrf = k_rrf
        self.vectors = embedder.embed_batch(chunks)
        self.bm25 = BM25(chunks)

    def dense_search(self, query_vec: np.ndarray, top_k: int = 20) -> List[int]:
        sims = self.vectors @ query_vec
        return list(np.argsort(-sims)[:top_k])

    def sparse_search(self, query: str, top_k: int = 20) -> List[int]:
        scores = self.bm25.score(query)
        return list(np.argsort(-np.array(scores))[:top_k])

    def hybrid(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        q_vec = self.embedder.embed(query)
        dense_idx = self.dense_search(q_vec, top_k=20)
        sparse_idx = self.sparse_search(query, top_k=20)
        # RRF 融合
        rrf = defaultdict(float)
        for rank, idx in enumerate(dense_idx, 1):
            rrf[idx] += 1.0 / (self.k_rrf + rank)
        for rank, idx in enumerate(sparse_idx, 1):
            rrf[idx] += 1.0 / (self.k_rrf + rank)
        ranked = sorted(rrf.items(), key=lambda x: -x[1])[:top_k]
        return ranked


# ============================================================
# 5. Mock Reranker(用词重叠率模拟 Cross-Encoder)
# ============================================================
class MockReranker:
    """
    真实场景用 bge-reranker-large / Cohere Rerank。
    这里用 query 与 doc 的字符重叠率模拟相关度。
    """
    def rerank(self, query: str, candidates: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
        q_chars = set(query)
        scored = []
        for c in candidates:
            c_chars = set(c)
            overlap = len(q_chars & c_chars) / max(len(q_chars | c_chars), 1)
            scored.append((c, overlap))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_n]


# ============================================================
# 6. Mock LLM 生成器
# ============================================================
class MockLLM:
    """
    真实场景调用 GPT-4 / Claude / Qwen。
    这里用模板拼接模拟生成,强调"基于上下文回答"。
    """
    def generate(self, query: str, context: List[str]) -> str:
        ctx_text = "\n\n".join(f"[参考{i+1}] {c}" for i, c in enumerate(context))
        return (
            f"【问题】{query}\n\n"
            f"【基于以下参考资料生成回答】\n{ctx_text}\n\n"
            f"【回答】根据参考资料,{query}的答案可以从上述参考中归纳如下:\n"
            f"(真实场景此处由 LLM 基于上下文生成,并标注引用来源)"
        )


# ============================================================
# 7. RAG 查询引擎(串联全链路)
# ============================================================
class RAGEngine:
    def __init__(self, docs: List[str]):
        self.chunker = RecursiveChunker(chunk_size=200, overlap=20)
        self.embedder = MockEmbedder(dim=128)
        self.reranker = MockReranker()
        self.llm = MockLLM()
        # 索引阶段
        self.chunks = []
        for doc in docs:
            self.chunks.extend(self.chunker.split(doc))
        self.retriever = HybridRetriever(self.chunks, self.embedder)

    def query(self, question: str, top_k: int = 20, top_n: int = 5) -> Dict:
        # 查询阶段
        # Step 1: 混合检索
        hybrid_results = self.retriever.hybrid(question, top_k=top_k)
        candidates = [self.chunks[idx] for idx, _ in hybrid_results]
        # Step 2: Rerank
        reranked = self.reranker.rerank(question, candidates, top_n=top_n)
        top_chunks = [c for c, _ in reranked]
        # Step 3: 生成
        answer = self.llm.generate(question, top_chunks)
        return {
            "question": question,
            "retrieved_chunks": top_chunks,
            "answer": answer,
        }


# ============================================================
# 8. 运行示例
# ============================================================
if __name__ == "__main__":
    # 模拟企业知识库文档
    docs = [
        "华为公司病假政策:员工因病需要请假,应提前在 OA 系统提交病假申请,并附医院证明。"
        "病假天数在 3 天以内的,由直属主管审批;超过 3 天需部门经理审批。"
        "病假期间工资按基本工资的 80% 发放。",

        "华为年假制度:入职满 1 年的员工享有 5 天年假,满 5 年享有 10 天,满 10 年享有 15 天。"
        "年假应在当年使用,未休完的可顺延至次年第一季度。年假期间工资照常发放。",

        "华为加班管理规定:工作日加班需提前申请,加班费按 1.5 倍工资计算;"
        "周末加班按 2 倍工资计算;法定节假日加班按 3 倍工资计算。每月加班不超过 36 小时。",

        "华为出差报销标准:国内出差交通费实报实销,住宿费一线城市上限 500 元/晚,"
        "二线城市 400 元/晚,餐饮补贴 100 元/天。出差前需在系统提交申请。",

        "华为远程办公政策:符合条件的员工可申请每周最多 2 天远程办公。"
        "需在 OA 系统提交申请,经主管审批。远程办公期间应保持在线,不得影响协作。",
    ]

    engine = RAGEngine(docs)

    questions = [
        "病假怎么请?工资怎么算?",
        "年假有多少天?",
        "出差住宿费上限多少?",
    ]

    for q in questions:
        print(f"\n{'='*60}")
        result = engine.query(q)
        print(f"Q: {result['question']}")
        print(f"\n检索到的 Top 片段:")
        for i, c in enumerate(result["retrieved_chunks"], 1):
            print(f"  [{i}] {c[:80]}...")
        print(f"\n{result['answer']}")
```

**运行输出示例(节选):**

```
============================================================
Q: 病假怎么请?工资怎么算?

检索到的 Top 片段:
  [1] 华为公司病假政策:员工因病需要请假,应提前在 OA 系统提交病假申请,并附医院证明。病假天数在 3 天以内的,由直属主管审批;超过 3 天需部门经理审批。病假期间工资按基本工资的 80% 发放。
  ...

【问题】病假怎么请?工资怎么算?
【基于以下参考资料生成回答】
[参考1] 华为公司病假政策:...
【回答】根据参考资料,病假怎么请?工资怎么算?的答案可以从上述参考中归纳如下:
(真实场景此处由 LLM 基于上下文生成,并标注引用来源)
```

**代码讲解要点(面试可讲):**
1. **模块解耦**:Chunker / Embedder / Retriever / Reranker / LLM 各自独立,可单独替换为真实组件。
2. **索引与查询分离**:`__init__` 完成索引,`query()` 在线查询。
3. **RRF 融合**:`hybrid()` 中 Dense 和 BM25 各取 Top-20,RRF 融合后取 Top-10。
4. **漏斗式检索**:Top-20(混合) → Top-5(Rerank) → LLM。
5. **Mock 设计**:Embedder 用词袋哈希,Reranker 用字符重叠率,LLM 用模板——保证代码可独立运行,面试现场可演示。

**升级路径(生产化):**
- `MockEmbedder` → `FlagEmbedding.BGE`
- `BM25` → `Elasticsearch` / `OpenSearch`
- `MockReranker` → `bge-reranker-large`
- `MockLLM` → `OpenAI / Qwen API`
- 内存检索 → `Milvus / Qdrant`

</details>

### Q10: 系统设计题 — 设计一个企业知识库 RAG 系统(多部门、权限控制、十万级文档)

<details>
<summary>点击展开答案</summary>

**题目:** 设计一个企业知识库 RAG 系统,要求:
- 支持多部门(研发、HR、法务、财务...),每个部门有独立知识库;
- 权限控制:员工只能检索自己有权限的部门文档;
- 文档量 10 万级,日新增 100+,日查询 QPS 50;
- 答案需标注引用来源;
- 支持文档增量更新。

**一、需求拆解**

| 维度 | 要求 | 量化 |
|------|------|------|
| 规模 | 文档数 | 10 万篇,分块后约 100 万 chunks |
| 多租户 | 部门数 | 20+ 部门 |
| 权限 | 可见性 | 用户-部门多对多,文档-部门一对多 |
| 性能 | 查询延迟 | P95 < 2s |
| 性能 | QPS | 50(峰值 200) |
| 更新 | 增量 | 日新增 100 文档,需分钟级生效 |
| 可追溯 | 引用 | 答案标注来源文档 + chunk |

**二、整体架构图**

```
┌────────────────────────────────────────────────────────────────────┐
│                        接入层 (API Gateway)                         │
│              鉴权 / 限流 / 路由 / 日志                                │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                      RAG 查询服务 (在线)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │Query改写 │─▶│混合检索  │─▶│ Rerank   │─▶│ LLM 生成  │          │
│  │(LLM)    │  │+权限过滤 │  │(Cross-Enc)│  │+引用标注  │          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
└──────┬───────────────┬──────────────┬──────────────┬──────────────┘
       │               │              │              │
       ▼               ▼              ▼              ▼
  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
  │向量库    │    │BM25索引  │    │Rerank模型│    │ LLM API │
  │(Milvus) │    │(ES)     │    │(GPU)    │    │(Qwen)   │
  │分collection│ │分index  │    │         │    │         │
  └─────────┘    └─────────┘    └─────────┘    └─────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    索引服务 (离线/近实时)                            │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐      │
│  │文档上传│─▶│解析    │─▶│分块    │─▶│Embedding│─▶│写库    │      │
│  │(OSS)  │  │(LlamaParse)│(递归) │  │(BGE)   │  │(Milvus+ES)│   │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘      │
│       ▲                                                            │
│       │ 文档变更事件 (CDC)                                          │
│  ┌────┴───────────┐                                                │
│  │ 文档管理后台    │  元数据:doc_id, dept, acl, time, source      │
│  └────────────────┘                                                │
└────────────────────────────────────────────────────────────────────┘
```

**三、核心模块设计**

**1. 多部门与权限控制(关键)**

权限模型采用 **用户-部门-文档三级结构**:

```
User ──(N:M)── Department ──(1:N)── Document
  │                                   │
  └── ACL: 用户可见部门集合 ──▶ 检索时过滤
```

**权限过滤的两种实现方案:**

| 方案 | 实现 | 优点 | 缺点 |
|------|------|------|------|
| **元数据过滤(推荐)** | 向量库按 dept 建字段,检索时 `filter=dept in user_depts` | 性能好,无需分库 | 依赖向量库支持过滤 |
| **物理分 Collection** | 每个部门一个 collection,查询时只查有权限的 | 隔离强 | 部门多时管理复杂,跨部门检索需多次查 |

**生产推荐:元数据过滤**,在 Milvus / Qdrant 中给每个 chunk 带上 `dept` 字段:

```python
# Milvus 写入时带元数据
collection.insert([
    {"id": 1, "vector": emb, "text": "...", "dept": "hr", "acl": ["hr", "legal"]},
])

# 查询时带过滤表达式
results = collection.search(
    data=[query_vec],
    anns_field="vector",
    param={"metric_type": "IP"},
    limit=20,
    expr='dept in ["hr", "legal"]',  # 只检索用户有权限的部门
)
```

**2. 文档管理与增量更新**

```
文档变更(CDC) → 消息队列(Kafka) → 索引 Worker → 解析/分块/Embedding → 写库
```

- 新增文档:解析 → 分块 → Embedding → 写入向量库 + ES。
- 删除文档:按 doc_id 删除所有关联 chunks(需维护 doc_id → chunk_ids 映射)。
- 更新文档:先删旧 chunks,再加新 chunks(保证一致性)。
- 分钟级生效:用近实时索引(Milvus 的 streaming + ES 的 refresh_interval=1s)。

**3. 混合检索 + Rerank 管线**

```python
def query(user, question):
    # 1. 权限解析
    user_depts = acl_service.get_user_depts(user.id)  # ["hr", "legal"]

    # 2. Query 改写(LLM)
    rewritten = llm.rewrite(question)

    # 3. 混合检索(带权限过滤)
    dense_hits = milvus.search(emb(rewritten), filter=f'dept in {user_depts}', k=50)
    sparse_hits = es.search(rewritten, filter={'dept': user_depts}, size=50)
    fused = rrf_fusion(dense_hits, sparse_hits, top_k=20)

    # 4. Rerank
    reranked = reranker.rerank(question, [c.text for c in fused], top_n=5)

    # 5. Prompt 组装 + 引用标注
    prompt = build_prompt(question, reranked, with_citations=True)

    # 6. LLM 生成
    answer = llm.generate(prompt)
    return {"answer": answer, "citations": reranked}
```

**4. 引用来源标注**

让 LLM 在生成时标注引用,有两种方式:
- **Prompt 指令法**:在 system prompt 中要求"每个事实陈述后标注[参考i]"。
- **后处理法**:生成后用 NLP 模型对齐句子与 chunk(更精确但复杂)。

```
Prompt 模板:
system: 你是企业知识助手,只能基于以下参考资料回答。每个事实后标注[参考i]。
context:
  [参考1] (dept=hr) 病假工资按 80% 发放...
  [参考2] (dept=hr) 病假需 OA 申请...
question: 病假怎么请?
→ answer: 病假需在 OA 系统提交申请并附医院证明[参考2],工资按基本工资 80% 发放[参考1]。
```

**5. 容量与性能估算**

| 资源 | 估算 | 说明 |
|------|------|------|
| 向量存储 | 100万 chunks × 1024d × 4B = 4GB | BGE 1024 维 |
| HNSW 索引 | ×1.5 = 6GB | 图结构开销 |
| ES 索引 | ~2GB | BM25 倒排 |
| 总内存 | ~16GB | 含缓存 |
| Embedding 吞吐 | 100 文档/天 ≈ 1000 chunks/天 | 单卡 BGE 足够 |
| 查询 QPS | 50 | 单机 Rerank GPU 够用 |
| LLM 调用 | 50 QPS | 用 Qwen API,需限流 |

**6. 可观测性与评估**

- **检索质量监控**:记录 Top-K 召回率(用标注集评估),低于阈值告警。
- **生成质量监控**:用 LLM-as-Judge 自动评估答案相关性、忠实性、引用准确性。
- **Trace 链路**:OpenTelemetry 记录每环节耗时,定位瓶颈。
- **A/B 测试框架**:不同分块/Embedding/Rerank 策略灰度对比。
- **评估指标**:Recall@K, MRR, Faithfulness, Answer Relevancy。

**7. 演进路线**

```
V1: 单部门 Naive RAG (1周)
V2: 多部门 + 权限 + 混合检索 (1月)
V3: Rerank + Query 改写 + 引用标注 (2月)
V4: Agentic-RAG (多轮检索/路由) — Day09 内容
V5: GraphRAG (知识图谱增强) — Day09 内容
```

**面试讲解策略:**
1. **先讲需求拆解**:把模糊需求量化,展示工程思维。
2. **重点讲权限控制**:这是企业场景和玩具 demo 的关键区别,元数据过滤是标准答案。
3. **画架构图**:索引服务(离线)+ 查询服务(在线)分离,用 CDC 做增量。
4. **容量估算**:展示你对资源成本的把握,面试官最爱问"10 万文档要多大内存"。
5. **提演进路线**:展示你不是只会做 V1,知道怎么一步步上生产。

**面试金句:**
> "企业 RAG 的核心难点不是检索算法,而是权限控制、增量更新和可观测性。权限我用向量库元数据过滤实现,避免物理分库的管理复杂度;增量更新用 CDC + 近实时索引;评估用 LLM-as-Judge 持续监控 Faithfulness。这三件事决定了 RAG 能不能上生产。"

</details>

---

## 核心知识回顾表

| 知识点 | 关键内容 | 面试频率 |
|--------|---------|---------|
| RAG 定义 | 检索增强生成,先检索后生成,锚定事实 | ★★★★★ |
| RAG vs 微调 | RAG 补知识(外置),微调补能力(内化),可叠加 | ★★★★★ |
| RAG 链路 | 索引阶段(加载/分块/Embedding/入库)+ 查询阶段(改写/检索/重排/生成) | ★★★★★ |
| 分块策略 | 固定/递归/语义/父子/结构感知,chunk_size 300-500,overlap 10-20% | ★★★★☆ |
| Embedding 选型 | 中文 BGE,英文 OpenAI/Cohere,七维选型框架 | ★★★★☆ |
| 向量索引 | Flat/IVF/HNSW,生产默认 HNSW,M=16,ef=50-200 | ★★★★☆ |
| 混合检索 | Dense + BM25 互补,RRF 融合(k=60)避免量纲问题 | ★★★★★ |
| Reranker | Cross-Encoder 重排,Bi-Encoder 召回+Cross-Encoder 精排的漏斗架构 | ★★★★☆ |
| RAG 演进 | Naive → Advanced(检索前后优化)→ Modular(可插拔)→ Agentic | ★★★☆☆ |
| Query 改写 | Rewrite / HyDE / Step-back / Multi-Query | ★★★☆☆ |
| 企业 RAG 设计 | 多部门权限(元数据过滤)+ 增量更新(CDC)+ 引用标注 + 评估 | ★★★★★ |
| 评估指标 | Recall@K, MRR, Faithfulness, Answer Relevancy | ★★★☆☆ |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG 全链路速记卡                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ▍核心链路                                                      │
│  Index:  Doc → Chunk → Embed → VectorStore                      │
│  Query:  Q → Rewrite → Embed → Hybrid → Rerank → LLM → Answer   │
│                                                                 │
│  ▍关键公式                                                      │
│  BM25:    score = Σ IDF · tf·(k1+1) / (tf + k1·(1-b+b·dl/avgdl))│
│           k1=1.2, b=0.75                                        │
│  RRF:     score(d) = Σ 1/(k + rank_i), k=60                     │
│  HNSW:    O(log N), M=16, ef_construction=200, ef_search=50     │
│  Cosine:  sim = (a·b)/(|a|·|b|),归一化后即内积                  │
│                                                                 │
│  ▍分块参数                                                      │
│  chunk_size: 中文 300-500, 英文 500-1000 token                  │
│  overlap:    chunk_size 的 10%-20%                              │
│                                                                 │
│  ▍选型口诀                                                      │
│  Embedding: 中文 BGE, 英文 OpenAI, 多语言 bge-m3                │
│  向量库:    小 Flat, 中 IVF, 大 HNSW, 超大 DiskANN              │
│  Rerank:    bge-reranker-large / Cohere Rerank                  │
│  检索:      混合检索(Dense+BM25+RRF)是生产标配                 │
│                                                                 │
│  ▍RAG vs 微调                                                   │
│  RAG 补知识(外置,实时,可追溯,低成本更新)                    │
│  微调补能力(内化,风格,格式,高成本)                           │
│  生产: 两者叠加,微调定风格 + RAG 注入事实                      │
│                                                                 │
│  ▍漏斗式检索                                                    │
│  百万级 → Bi-Encoder 召回 Top-100 → Cross-Encoder 精排 Top-5    │
│  快但粗 ──────────────────────────▶ 慢但精                      │
│                                                                 │
│  ▍企业 RAG 三大难点                                              │
│  1. 权限:向量库元数据过滤(dept in user_depts)                 │
│  2. 增量:CDC + 近实时索引                                       │
│  3. 评估:Recall@K + Faithfulness(LLM-as-Judge)                │
│                                                                 │
│  ▍RAG 演进                                                      │
│  Naive → Advanced(Pre/Post 优化)→ Modular(可插拔)→ Agentic     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒

| # | 易错点 | 正确做法 | 错误后果 |
|---|--------|---------|---------|
| 1 | 索引和查询用不同 Embedding 模型 | 必须同模型,迁移时全量重建 | 检索完全失效 |
| 2 | BGE 的 query/doc instruction 用反 | query 加查询前缀,doc 不加或加文档前缀 | 召回率下降 |
| 3 | BM25 中文未分词 | 先用 jieba/HanLP 分词再建索引 | 中文检索失效 |
| 4 | chunk_size 过大(>1000 token) | 中文 300-500,英文 500-1000 | Embedding 语义稀释,召回差 |
| 5 | RRF 的 k 值设太小(如 1) | 默认 60,过小会让 Top-1 权重过大 | 融合退化成"谁第一谁赢" |
| 6 | 混合检索候选集太小(各取 Top-5) | 各取 Top-20 以上再融合 | 融合效果打折 |
| 7 | Rerank 直接对全库重排 | 只对 Bi-Encoder 召回的 Top-K 重排 | 延迟不可接受 |
| 8 | HNSW 频繁删除 | 用软删除或定期重建 | 图结构损坏,召回下降 |
| 9 | 向量未 L2 归一化就用内积 | 归一化后内积=余弦,或直接用 metric=COSINE | 相似度计算错误 |
| 10 | 答案不标注引用 | Prompt 要求标注[参考i],或后处理对齐 | 不可追溯,用户不信任 |

---

## 自测检查清单

### 概念题(10 个)

- [ ] 1. 能用一句话讲清 RAG 是什么,并说出 4 个核心动机?
- [ ] 2. 能列出 RAG vs 微调的至少 6 个对比维度,并说出"何时用哪个"?
- [ ] 3. 能画出 RAG 索引阶段 + 查询阶段的完整数据流图?
- [ ] 4. 能说出 5 种分块策略及各自适用场景,并解释为什么 chunk_size 不能太大?
- [ ] 5. 能说出 Embedding 选型的 7 个维度,并给出中文/英文/多语言的首选模型?
- [ ] 6. 能对比 Flat/IVF/HNSW 的原理、速度、召回率,并给出选型决策?
- [ ] 7. 能解释为什么混合检索需要 RRF 而非简单加权,并写出 RRF 公式?
- [ ] 8. 能解释 Bi-Encoder vs Cross-Encoder 的精度差异原因,以及为什么用两阶段漏斗?
- [ ] 9. 能说出 Naive/Advanced/Modular RAG 的区别,以及 Advanced RAG 在 Pre/Post 环节各有哪些优化技术?
- [ ] 10. 能说出企业 RAG 的三大难点(权限/增量/评估)及各自解决方案?

### 代码题(3 个)

- [ ] 1. 能手写 RRF 融合函数(输入两路排名,输出融合分数)?
- [ ] 2. 能手写一个最小 RAG 引擎(分块 + Embedding mock + 检索 + 生成 mock),代码可运行?
- [ ] 3. 能手写 BM25 打分函数的核心逻辑(tf-idf + 长度归一化)?

### 系统设计题(2 个)

- [ ] 1. 能设计一个支持多部门、权限控制、十万级文档的企业知识库 RAG 系统,画出架构图并做容量估算?
- [ ] 2. 如果 QPS 从 50 涨到 500,你的 RAG 系统会有哪些瓶颈?如何水平扩展?(思考:Embedding 缓存、向量库分片、Rerank GPU 扩容、LLM 限流)

---

## 延伸阅读

**核心论文:**
1. 《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》(Lewis et al., 2020) — RAG 开山之作。
2. 《Retrieval-Augmented Generation for Large Language Models: A Survey》(Gao et al., 2023) — Naive/Advanced/Modular RAG 分类法来源。
3. 《Hypothetical Document Embeddings》(HyDE, Gao et al., 2022) — HyDE Query 改写。
4. 《Take a Step Back: Evoking Reasoning via Abstraction in Large Language Models》(Zheng et al., 2023) — Step-back Prompting。
5. 《HNSW: Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs》(Malkov & Yashunin, 2018) — HNSW 算法原理。
6. 《BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings》(Chen et al., 2024) — BGE M3 模型。

**工具与框架:**
- **LangChain / LlamaIndex**:RAG 编排框架,生产常用。
- **LlamaParse**:复杂文档(PDF/表格)解析。
- **Milvus / Qdrant / Weaviate**:开源向量数据库。
- **FAISS**:Meta 开源的向量检索库,适合单机。
- **Elasticsearch / OpenSearch**:BM25 + 向量混合检索。
- **FlagEmbedding**:BGE 系列 Embedding + Reranker 官方库。
- **Cohere Rerank API**:托管 Rerank 服务。
- **RAGAS**:RAG 评估框架(Faithfulness / Answer Relevancy)。
- **TruLens**:RAG 可观测性与评估。

**榜单与基准:**
- **MTEB / C-MTEB**:Embedding 模型榜单(https://github.com/embeddings-benchmark/mteb)。
- **BEIR**:信息检索基准。
- **RAGAS**:RAG 评估指标库。

**实战博客:**
- LangChain 官方文档 RAG 教程:https://python.langchain.com/docs/use_cases/question_answering/
- LlamaIndex RAG 指南:https://docs.llamaindex.ai/
- Milvus 官方文档:https://milvus.io/docs

---

## 明日预告 — Day 09: Agentic-RAG 与 GraphRAG

今天的 RAG 全链路是"静态流水线":检索→重排→生成,流程固定。但真实场景中,用户问题千变万化:
- 简单问题可能不需要检索;
- 复杂问题可能需要多轮检索、跨库检索;
- 有些问题需要先拆解成子问题再分别检索;
- 有些事实之间的关系不是"相似文档"能表达的,需要知识图谱。

明天 Day 09 我们进入 **Agentic-RAG 与 GraphRAG**:
- **Agentic-RAG**:让 Agent 决策"何时检索、检索什么、检索够不够、要不要再检索",把 RAG 从流水线升级为"会思考的检索循环"。
- **GraphRAG**(微软 2024 提出的方法):先用 LLM 从文档抽取实体关系构建知识图谱,检索时基于社区层级摘要回答全局性问题,解决传统 RAG 对"全局性总结问题"无能为力的痛点。
- 二者的结合点:Agent 路由到不同检索源(向量库 / 图谱 / Web),实现"自适应检索"。

**预习建议:**
- 复习 Day 04 的 ReAct 模式,Agentic-RAG 本质是 ReAct + RAG 工具。
- 浏览微软 GraphRAG 论文《From Local to Global: A Graph RAG Approach to Query-Focused Summarization》(2024)。
- 思考:传统 RAG 在回答"这份文档的核心观点是什么"时为什么效果差?(提示:Top-K 检索只能找到局部相似,无法覆盖全文主旨。)

---

> **今日总结**:RAG 全链路 = 索引(分块/Embedding/入库)+ 查询(改写/混合检索/Rerank/生成)。生产标配:递归分块 + BGE Embedding + HNSW 向量库 + Dense+BM25 混合检索 + RRF 融合 + Cross-Encoder Rerank + LLM 生成 + 引用标注。企业场景三大难点:权限(元数据过滤)、增量(CDC)、评估(Recall@K + Faithfulness)。
>
> 明天我们让 RAG "活"起来——Agent 接管检索决策,GraphRAG 接管全局性问题。
