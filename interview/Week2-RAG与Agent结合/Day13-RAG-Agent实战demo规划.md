# Day 13 — RAG-Agent 实战 demo 规划

> **学习目标**
> - 学会用 STAR 法则在面试中讲清楚一个 RAG+Agent 项目,让面试官 5 分钟内 get 到你的技术深度
> - 掌握三个面试友好型项目选题的取舍逻辑,选出最适合自己背景的 demo 方向
> - 输出一份可落地的技术架构 + 一周 MVP 执行计划,并能在白板上徒手画出来
> - 沉淀一套"项目介绍话术模板 + 易错点清单 + 自测题",作为冲刺期反复演练的弹药库
>
> **面试定位**
> 面试官最爱问的不是"你懂 RAG 吗",而是"你做过什么项目?遇到什么难点?怎么解决的?"。一个能写在简历上、能在白板上讲清楚、能撕出核心代码的 RAG+Agent 项目,是 Day13~Day14 这两天的核心产出。本日重点是"规划",Day14 会进入"手撕骨架代码"的实战环节。

---

## 一、今日知识图谱:RAG-Agent 项目架构

下面这张 ASCII 树状图,是本日所有内容围绕的"项目全景图"。从底层数据到顶层应用,每一层都对应后续 Q4 的模块拆解和 Q10 的白板讲解。

```
RAG + Agent 项目架构
│
├── 1. 应用层 (Application Layer)
│   ├── Web UI ────────── Streamlit / Gradio / Next.js
│   ├── API 网关 ──────── FastAPI + 鉴权 + 限流
│   └── 会话管理 ──────── Redis 存对话历史 + Session 状态机
│
├── 2. Agent 决策层 (Agent Orchestration)
│   ├── 路由器 Router ─── 意图识别:闲聊 / 检索 / 工具调用 / 澄清
│   ├── 规划器 Planner ── ReAct / Plan-and-Execute 任务分解
│   ├── 工具集 Tools ──── 检索工具 / 计算器 / SQL查询 / API调用
│   ├── 反思 Self-Reflect─ 答案评分 + 检索重写 + 兜底澄清
│   └── 记忆 Memory ───── 短期对话窗口 + 长期向量记忆
│
├── 3. 检索引擎 (Retrieval Engine)
│   ├── 混合检索 Hybrid ─ 向量检索(BM25) + 语义检索(dense)
│   ├── 重排 Rerank ───── Cross-Encoder (bge-reranker / Cohere)
│   ├── 查询改写 ──────── HyDE / Multi-Query / Step-Back
│   └── 上下文压缩 ────── LongLLMLingua / 基于相关性的裁剪
│
├── 4. 索引与存储层 (Indexing & Storage)
│   ├── 向量库 VectorDB ─ Milvus / Qdrant / Chroma / PGVector
│   ├── 文档元数据 ────── 标题/章节/时间/来源/权限标签
│   ├── 索引策略 ──────── HNSW / IVF-PQ,参数调优
│   └── 增量更新 ──────── 文档变更监听 + 增量 embedding
│
├── 5. 数据处理 Pipeline (Data Pipeline)
│   ├── 加载 Loader ──── PDF / Word / Markdown / HTML / 代码
│   ├── 切分 Chunker ── 语义切分 / 递归切分 / 父子文档
│   ├── 清洗 Cleaner ── 去水印 / 去页眉页脚 / 公式保留
│   ├── Embedding ───── bge-m3 / text-embedding-3 / 本地 BGE
│   └── 质量校验 ─────── 切分粒度统计 + 语义完整性检查
│
└── 6. 评估与可观测 (Eval & Observability)
    ├── 离线评估 ──────── RAGAS (Faithfulness / Answer Relevancy / Context Recall)
    ├── 在线监控 ──────── LangSmith / Langfuse 调用链追踪
    ├── A/B 实验 ──────── 检索策略对比 / Prompt 版本对比
    └── 兜底机制 ──────── 拒答阈值 + 人工反馈闭环
```

---

## 二、面试题(共 10 道)

> 使用说明:每道题先用 `<summary>` 里的一句话自测,能答上来再展开看答案。建议先合上答案默写要点,再对照补充。

### Q1: 面试中如何介绍一个 RAG 项目?用 STAR 法则 + 技术亮点表达。

<details>
<summary>点击展开:STAR 四段式 + 三层技术亮点 + 30 秒电梯演讲模板</summary>

**核心思路**:面试官一天听 10 个候选人讲项目,最怕"流水账式"的"我用了 LangChain + Milvus 做了个问答机器人"。你要做的是:**先给结果,再给冲突,最后给技术解法**。

#### STAR 法则套用模板

| 维度 | 内容要点 | 反面教材 |
|------|----------|----------|
| **S**ituation 背景 | 业务场景 + 数据规模 + 用户痛点(1 句话) | "我们公司有个知识库……"(无规模无痛点) |
| **T**ask 任务 | 你负责什么 + 目标指标(召回率/延迟/成本) | "我负责开发"(无目标无指标) |
| **A**ction 行动 | 3 个关键技术决策 + 取舍理由 | 罗列技术栈,不讲为什么选 |
| **R**esult 结果 | 量化指标 + 业务价值 + 你的反思 | "效果还不错"(无数字) |

#### 30 秒电梯演讲模板

> "我在 XX 项目中负责一个企业知识库问答系统,**Situation**:内部文档 5 万篇、PDF/Word/Confluence 多源,员工查资料平均要翻 20 分钟。**Task**:目标是做一个 RAG+Agent 助手,把首答准确率做到 85% 以上、P95 延迟 3 秒内。**Action**:我用 bge-m3 做多语言 embedding、Milvus 做 HNSW 向量检索 + BM25 混合召回,Agent 层用 ReAct 做多轮澄清,遇到低置信度自动追问。**Result**:上线后首答准确率从基线 62% 提到 88%,P95 延迟 2.4 秒,每月节省工时约 1200 小时。我个人觉得最大的收获是检索环节的 rerank 策略调优,这块踩了不少坑。"

#### 三层技术亮点表达法

讲项目时,技术亮点要"分层递进",让面试官能选择追问哪一层:

1. **第一层(业务价值)**:指标提升、成本节省、用户满意度 —— 让面试官知道这不是玩具
2. **第二层(技术决策)**:为什么选 Milvus 不选 Pinecone?为什么用 bge-m3 不用 OpenAI? —— 展示取舍能力
3. **第三层(实现细节)**:HNSW 的 M 参数怎么调?rerank 的 top-k 怎么定? —— 展示深度

**面试官心理**:第一层让他觉得你"靠谱",第二层让他觉得你"有判断力",第三层让他觉得你"真做过"。三层缺一不可。

#### 常见追问预判

- "这个 88% 是怎么测的?" → 提前准备评估集构造方法(见 Q5)
- "为什么不用 GPT-4 直接 long context?" → 准备成本/延迟/可更新性三连击
- "如果文档更新了怎么办?" → 增量索引策略
</details>

---

### Q2: 项目选题 — 三个适合面试展示的 RAG+Agent 项目方案,各优缺点。

<details>
<summary>点击展开:企业知识库 / 研究助手 / 代码审查 三方案对比表 + 选型建议</summary>

**选题原则**:面试友好的项目要满足三条 —— ①业务场景真实(面试官能共鸣)②技术点足够覆盖 RAG+Agent 全链路 ③能在 1~2 周内做出可演示的 MVP。

#### 方案 A:企业知识库问答 Agent

| 维度 | 说明 |
|------|------|
| 场景 | 对接公司 Wiki/Confluence/文档库,员工自然语言提问,Agent 检索+回答+澄清 |
| 技术覆盖 | 全链路:文档解析、切分、混合检索、rerank、ReAct、多轮对话 |
| 优点 | 业务真实、面试官秒懂、技术点齐全、容易做出对比实验 |
| 缺点 | 同质化严重,满大街都是"知识库问答";需要差异化亮点 |
| 差异化建议 | 加 Agentic RAG(自反思+检索重写)+ 权限管控 + 引用溯源 + 评估闭环 |
| 适合人群 | 有企业背景、想快速出活、技术广度优先 |

#### 方案 B:深度研究助手(Research Agent)

| 维度 | 说明 |
|------|------|
| 场景 | 用户给一个研究主题,Agent 自动拆解子问题 → 多轮检索 → 综合生成报告 |
| 技术覆盖 | Plan-and-Execute、多跳检索、子问题并行、长文本综合、引用网络 |
| 优点 | 技术深度高、能体现 Agent 的"规划"能力、产物可见(报告)有冲击力 |
| 缺点 | 评估难、效果不稳定、容易"看起来很酷但答非所问" |
| 差异化建议 | 引入"证据强度评分" + "矛盾信息检测" + 报告结构化模板 |
| 适合人群 | 想冲高端岗、愿意花时间调 Agent 行为、研究型选手 |

#### 方案 C:代码审查 / 代码问答 Agent

| 维度 | 说明 |
|------|------|
| 场景 | 输入代码仓库或 PR diff,Agent 检索相关规范/历史 issue/相似代码,给出审查意见 |
| 技术覆盖 | 代码切分(AST 级)、代码 embedding、调用链检索、工具调用(读 git log) |
| 优点 | 极度差异化(少有人做)、技术含量高、和工程师面试官强共鸣 |
| 缺点 | 代码切分难度大、embedding 质量难保证、评估需要人工标注 |
| 差异化建议 | 用 tree-sitter 做函数级切分 + 调用图增强检索 + 规范库 RAG |
| 适合人群 | 后端/编译器背景、想突出"懂代码"、愿意啃硬骨头 |

#### 三方案横向对比

| 对比项 | A 知识库 | B 研究助手 | C 代码审查 |
|--------|----------|------------|------------|
| 业务真实度 | ★★★★★ | ★★★★ | ★★★★ |
| 技术广度 | ★★★★★ | ★★★★ | ★★★ |
| 技术深度 | ★★★ | ★★★★★ | ★★★★★ |
| 差异化 | ★★ | ★★★★ | ★★★★★ |
| MVP 周期 | 3-5 天 | 5-7 天 | 7-10 天 |
| 面试讲清楚难度 | 易 | 中 | 难 |
| 简历加分项 | 中 | 高 | 极高 |

#### 选型建议(本课程推荐)

- **如果你时间紧(只剩 1 周)**:选 A,但必须加上"Agentic 自反思 + 评估闭环"两个差异化亮点
- **如果你想冲大厂 Agent 岗**:选 B,Plan-and-Execute 是 Agent 岗高频考点
- **如果你是后端/系统背景**:选 C,差异化最强,且能复用你的代码理解能力

**本日后续 Q3~Q10 以方案 A(企业知识库 + Agentic 增强)为主线讲解**,因为它最适合作为"基座项目",B 和 C 可以在此基础上替换检索对象和 Agent 策略。
</details>

---

### Q3: 技术架构设计 — 从数据层到应用层的完整架构,画出系统架构图。

<details>
<summary>点击展开:六层架构图 + 数据流时序 + 关键设计决策</summary>

#### 系统架构图(白板版)

```
┌─────────────────────────────────────────────────────────────────┐
│                      用户层 (User)                              │
│   员工提问 ──→ Web UI ──→ API 网关 ──→ 会话管理               │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   Agent 决策层 (Orchestration)                  │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────────┐      │
│  │ Router  │→│ Planner │→│ Tools    │→│ Self-Reflect │      │
│  │意图路由 │  │任务规划 │  │检索/SQL/ │  │答案评分+重写 │      │
│  └─────────┘  └─────────┘  │API/计算器│  └──────────────┘      │
│                            └──────────┘                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                   检索引擎层 (Retrieval)                        │
│  查询改写(HyDE/MultiQ) → 混合检索(向量+BM25) → Rerank → 压缩   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              索引与存储层 (Index & Storage)                     │
│  Milvus(HNSW)  +  元数据(PG)  +  对话历史(Redis)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              数据处理 Pipeline (Offline)                        │
│  Loader → Cleaner → Chunker(父子文档) → Embedder → 入库        │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│              评估与可观测 (Eval & Observability)                │
│  RAGAS 离线评估  +  Langfuse 在线追踪  +  人工反馈闭环          │
└─────────────────────────────────────────────────────────────────┘
```

#### 核心数据流(在线查询)

```
用户问题
  │
  ▼
[1] Router 判断意图(闲聊/检索/工具/澄清)
  │   └─ 闲聊 → 直接 LLM 回答
  │   └─ 工具 → 调用 SQL/计算器
  │   └─ 检索 → 进入 RAG 链路 ↓
  ▼
[2] 查询改写:HyDE 生成假设答案 → 用假设答案做向量检索
  │
  ▼
[3] 混合检索:向量 top-20 (Milvus HNSW) + BM25 top-20 (ES)
  │   → RRF 融合 → top-10
  │
  ▼
[4] Rerank:bge-reranker-large 打分 → top-5
  │
  ▼
[5] 上下文压缩:LongLLMLingua 裁剪到 4K token
  │
  ▼
[6] 生成:LLM 基于上下文 + 对话历史生成答案 + 引用
  │
  ▼
[7] Self-Reflect:答案置信度 < 阈值? → 触发检索重写 / 追问用户
  │
  ▼
[8] 返回答案 + 引用源 + 追问建议
```

#### 五个关键设计决策(面试必答)

| 决策点 | 选择 | 理由(面试话术) |
|--------|------|------------------|
| 检索策略 | 混合检索 + Rerank | 纯向量召回在专有名词上漏召,纯 BM25 不懂同义,混合 + rerank 是性价比最高的方案 |
| 切分策略 | 父子文档(子块检索,父块返回) | 小块检索精度高,大块上下文完整,两者兼得 |
| Agent 模式 | ReAct + Self-Reflect | ReAct 处理多步,Self-Reflect 兜底低置信度,避免一本正经胡说 |
| 向量库 | Milvus | 开源、支持 HNSW、可水平扩展、生态成熟;Qdrant 也行,看团队熟悉度 |
| 评估 | RAGAS + 人工标注 | 离线用 RAGAS 量化迭代,线上用人工反馈兜底,闭环 |

#### 面试官常追问

- "为什么不用 GPT-4 的 128K 长上下文直接塞进去?" → ①成本(每查一次塞 10 万 token 贵 10 倍)②延迟 ③文档更新要重新塞 ④检索能溯源
- "Agent 这一层是不是过度设计?" → 不一定,简单 QA 可以不要 Agent;但多轮澄清 + 工具调用 + 自反思能显著提升复杂问题准确率,这就是 Agentic RAG 的价值
</details>

---

### Q4: 核心模块拆解 — 文档处理 pipeline / 检索引擎 / Agent 决策层 / 生成模块,各模块技术选型。

<details>
<summary>点击展开:四大模块的选型表 + 取舍理由 + 接口定义</summary>

#### 模块一:文档处理 Pipeline

| 子环节 | 候选方案 | 推荐选型 | 理由 |
|--------|----------|----------|------|
| Loader | LangChain Loader / Unstructured / LlamaParse | **Unstructured**(通用) + LlamaParse(复杂 PDF) | Unstructured 多格式兼容;LlamaParse 对表格/公式强 |
| Cleaner | 正则 / 规则引擎 | 规则引擎 + 人工抽检 | 去页眉页脚、去水印、保留公式 |
| Chunker | 固定长度 / 递归切分 / 语义切分 / 父子文档 | **父子文档 + 语义切分** | 父子兼顾精度与上下文;语义切分保留语义完整 |
| Embedding | OpenAI text-3 / bge-m3 / bge-large-zh | **bge-m3**(多语言) 或 bge-large-zh(纯中文) | 开源、可本地部署、多语言强;OpenAI 贵且有数据合规问题 |
| 质量校验 | 切分粒度统计 / embedding 质量分 | 切分粒度统计 + 抽样人工 | 统计 chunk 长度分布,异常值人工复核 |

**接口定义(Python 伪代码)**:

```python
class DocumentPipeline:
    def load(self, source: str) -> List[Document]: ...
    def clean(self, docs: List[Document]) -> List[Document]: ...
    def chunk(self, docs: List[Document]) -> List[Chunk]: ...
    def embed(self, chunks: List[Chunk]) -> List[Embedding]: ...
    def index(self, embeddings: List[Embedding]) -> None: ...
    def run(self, source: str) -> None:
        docs = self.embed(self.chunk(self.clean(self.load(source))))
        self.index(docs)
```

#### 模块二:检索引擎

| 子环节 | 候选方案 | 推荐选型 | 理由 |
|--------|----------|----------|------|
| 向量检索 | Milvus / Qdrant / Chroma / PGVector | **Milvus**(生产) / **Chroma**(原型) | Milvus 性能强可扩展;Chroma 零部署适合 demo |
| 稀疏检索 | Elasticsearch / BM25 Okapi | **Elasticsearch** | 成熟、支持复杂查询;轻量可用 rank_bm25 |
| 查询改写 | HyDE / Multi-Query / Step-Back | **HyDE + Multi-Query** | HyDE 提升语义召回;Multi-Query 覆盖多角度 |
| 融合策略 | RRF / Linear | **RRF** | 无需调参、对分数尺度不敏感 |
| Rerank | bge-reranker / Cohere / cross-encoder | **bge-reranker-large** | 开源、中文强、效果接近 Cohere |
| 上下文压缩 | LongLLMLingua / LLMLingua / 摘要式 | **LongLLMLingua** | token 级压缩,保留关键信息 |

**接口定义**:

```python
class RetrievalEngine:
    def rewrite_query(self, query: str) -> List[str]: ...          # HyDE + Multi-Query
    def dense_search(self, queries: List[str], top_k: int) -> List[Hit]: ...
    def sparse_search(self, queries: List[str], top_k: int) -> List[Hit]: ...
    def fuse(self, dense: List[Hit], sparse: List[Hit]) -> List[Hit]: ...  # RRF
    def rerank(self, query: str, hits: List[Hit], top_k: int) -> List[Hit]: ...
    def compress(self, query: str, hits: List[Hit], max_tokens: int) -> str: ...
    def retrieve(self, query: str) -> str:
        queries = self.rewrite_query(query)
        fused = self.fuse(self.dense_search(queries, 20),
                          self.sparse_search(queries, 20))
        reranked = self.rerank(query, fused, 5)
        return self.compress(query, reranked, 4096)
```

#### 模块三:Agent 决策层

| 子环节 | 候选方案 | 推荐选型 | 理由 |
|--------|----------|----------|------|
| 框架 | LangChain / LangGraph / LlamaIndex / 自研 | **LangGraph**(复杂) / 自研轻量(简单) | LangGraph 状态机清晰;自研可控性强适合面试讲透 |
| 路由 | 规则 / 小模型 / LLM 分类 | **LLM 分类 + 规则兜底** | LLM 灵活,规则兜底降本 |
| 规划 | ReAct / Plan-and-Execute / Reflexion | **ReAct + Reflexion** | ReAct 通用,Reflexion 自反思 |
| 工具 | 检索 / SQL / 计算器 / API | 检索 + SQL + 计算器 | 覆盖面试常考工具集 |
| 记忆 | Buffer / Summary / Vector Store | **Buffer + Summary** | 短期 Buffer,长期 Summary 压缩 |

**接口定义**:

```python
class Agent:
    def route(self, query: str) -> str: ...              # 返回 "chat"/"rag"/"tool"/"clarify"
    def plan(self, query: str) -> List[Action]: ...      # ReAct 分解
    def execute(self, action: Action) -> str: ...        # 调用工具
    def reflect(self, query: str, answer: str) -> float: ...  # 置信度评分
    def run(self, query: str) -> str:
        intent = self.route(query)
        if intent == "rag":
            actions = self.plan(query)
            result = "".join(self.execute(a) for a in actions)
            score = self.reflect(query, result)
            if score < 0.6:
                return self.run(self.rewrite_for_clarify(query))
            return result
```

#### 模块四:生成模块

| 子环节 | 候选方案 | 推荐选型 | 理由 |
|--------|----------|----------|------|
| LLM | GPT-4o / Claude / Qwen / DeepSeek | **DeepSeek**(性价比) / Qwen(合规) | DeepSeek 便宜效果好;Qwen 国内合规 |
| Prompt | Zero-shot / Few-shot / CoT | **Few-shot + CoT + 引用模板** | Few-shot 稳定输出格式,CoT 提升推理 |
| 引用溯源 | 句级 / 段级 | **段级引用** | 实现简单、用户可验证 |
| 兜底 | 拒答 / 追问 | **拒答 + 追问二选一** | 低置信度拒答,信息不足追问 |

**接口定义**:

```python
class Generator:
    def build_prompt(self, query: str, context: str, history: List) -> str: ...
    def generate(self, prompt: str) -> str: ...
    def postprocess(self, answer: str, sources: List) -> str: ...  # 加引用
    def answer(self, query: str, context: str) -> str:
        prompt = self.build_prompt(query, context, self.history)
        raw = self.generate(prompt)
        return self.postprocess(raw, context.sources)
```

#### 模块间数据契约(关键)

```
Pipeline 产出 → Chunk{ id, text, parent_id, metadata }
Retrieval 产出 → Hit{ chunk_id, score, text, source }
Agent 产出 → Action{ tool, input } → Observation{ tool, output }
Generator 产出 → Answer{ text, citations: List[Hit], confidence }
```

**面试话术**:"四大模块我用清晰的接口隔离,每个模块可独立替换和测试。比如向量库从 Chroma 换 Milvus 只改 RetrievalEngine 内部;LLM 从 DeepSeek 换 Qwen 只改 Generator。这是工程化的基本功。"
</details>

---

### Q5: 如何在项目中体现技术深度?对比实验 / 性能优化 / 评估指标。

<details>
<summary>点击展开:三维度深度展示 + 对比实验设计 + 指标体系</summary>

**核心思路**:面试官判断"深度"的三个信号 —— ①有对比实验(说明你试过多个方案)②有量化指标(说明你会评估)③有性能优化(说明你懂工程)。

#### 维度一:对比实验设计(最加分)

设计 3 组对比实验,每组只变一个变量,固定其他:

| 实验组 | 变量 | 基线 | 实验组 | 评估指标 |
|--------|------|------|--------|----------|
| 实验1 切分策略 | chunk 策略 | 固定 512 token | 父子文档 | Context Recall / Answer Relevancy |
| 实验2 检索策略 | 检索方法 | 纯向量 | 向量+BM25+Rerank | Hit Rate / MRR |
| 实验3 Embedding | embedding 模型 | text-2 | bge-m3 | 召回率 @5 |

**记录表(面试可展示)**:

```
| 方案                | Hit@5 | MRR  | Faithfulness | Answer Relevancy | P95延迟 |
|---------------------|-------|------|--------------|------------------|---------|
| 固定512 + 纯向量    | 0.71  | 0.58 | 0.82         | 0.79             | 1.8s    |
| 父子 + 纯向量       | 0.78  | 0.64 | 0.85         | 0.83             | 1.9s    |
| 父子 + 混合+Rerank  | 0.86  | 0.73 | 0.89         | 0.88             | 2.4s    |
| + bge-m3            | 0.89  | 0.76 | 0.91         | 0.90             | 2.4s    |
```

**话术**:"我做了三组消融实验,每只变一个变量。最终方案比基线 Hit@5 提升 18 个点,但 P95 延迟增加 0.6 秒,这个取舍我认为值得,因为准确率优先于延迟,且 2.4 秒仍在可接受范围。"

#### 维度二:性能优化(展示工程力)

| 优化点 | 手段 | 收益 |
|--------|------|------|
| Embedding 批量化 | 批量编码 + 异步 | 吞吐 5x |
| 向量检索参数 | HNSW M=16→32, ef=64→128 | 召回 +3%, 延迟 +20ms |
| 缓存 | 查询 embedding 缓存 + 答案缓存 | 重复查询 0 延迟 |
| 上下文压缩 | LongLLMLingua | token -50%, 延迟 -30% |
| 并发 | 异步 FastAPI + 信号量限流 | QPS 3 → 15 |
| 模型蒸馏 | 小模型做路由 + 大模型做生成 | 成本 -40% |

#### 维度三:评估指标体系(RAGAS)

| 指标 | 含义 | 计算方式 | 目标值 |
|------|------|----------|--------|
| **Context Precision** | 检索上下文相关性 | LLM 判断每条 context 是否相关 | > 0.85 |
| **Context Recall** | 检索是否覆盖答案所需信息 | 答案能否由 context 推出 | > 0.80 |
| **Faithfulness** | 答案是否忠于上下文(不幻觉) | 答案claims能否由context支持 | > 0.90 |
| **Answer Relevancy** | 答案是否切题 | LLM 反推问题与原问题相似度 | > 0.85 |
| **Hit Rate @k** | top-k 是否命中金标 | 命中数 / 总查询数 | > 0.85 |
| **MRR** | 平均倒数排名 | Σ(1/rank) / N | > 0.70 |

**评估集构造**:
- 规模:200~500 条(够用即可,太多来不及标注)
- 来源:真实用户问题 50% + 人工构造 30% + 对抗样本 20%
- 标注:问题 + 金标答案 + 金标文档 id

**话术**:"我用 RAGAS 做离线评估,200 条标注集,四个核心指标。每次迭代跑全量评估,用 git 管理评估结果,形成'改 prompt → 跑评估 → 看指标'的闭环。这是 RAG 项目专业度的核心标志。"

#### 三维度的优先级

如果时间有限,优先级:**对比实验 > 评估指标 > 性能优化**。因为对比实验最能体现"你思考过",评估指标体现"你会验证",性能优化体现"你做过"——面试官最看重前两者。
</details>

---

### Q6: 项目中的难点和解决方案 — 面试中最常追问的 3 个技术难点。

<details>
<summary>点击展开:三大难点(切分/多跳检索/幻觉) + 解决方案 + 话术</summary>

**核心思路**:难点不是"我用了某个技术",而是"我遇到一个问题,试了 A 不行,B 部分解决,最终用 C 解决"。讲难点的公式 = **冲突 + 试错 + 最终方案 + 量化结果**。

#### 难点一:文档切分导致语义断裂

**冲突**:
> "知识库里有大量长文档(规范、手册),固定长度切分会把一个完整的'请假流程'切成两半,检索时只召回一半,答案就残缺。"

**试错过程**:
1. 先试固定 512 token → 切断表格、列表、步骤
2. 改用递归切分(按段落 → 句子) → 表格还是会被拆
3. 试语义切分(用 embedding 相邻句子相似度) → 慢,且边界不稳

**最终方案:父子文档 + 结构感知切分**
- 用 Unstructured 识别文档结构(标题/段落/表格/列表),按结构单元切"父块"(512~2048 token)
- 父块再切成"子块"(128~256 token)用于检索
- 检索命中子块 → 返回父块作为上下文

**量化结果**:Context Recall 从 0.68 → 0.83,且表格类问题准确率从 54% → 79%。

**话术**:"切分是最容易被低估的环节。我踩的坑是:一开始以为切分是预处理随便搞搞,后来发现 60% 的 badcase 都是切分不当导致。最终用父子文档 + 结构感知,把 Context Recall 提了 15 个点。这是我最大的收获之一。"

#### 难点二:多跳/复杂问题的检索失败

**冲突**:
> "用户问'去年Q3销量最高的产品在Q4的库存情况',这需要两跳检索:先查Q3销量→再查该产品Q4库存。单次检索只能拿到一跳,答案必然错。"

**试错过程**:
1. 单次检索 + 长 prompt → LLM 自己拆解? → 不稳定,常漏跳
2. Multi-Query 生成多个子查询 → 还是单跳,没解决多跳
3. 加大 top-k → 召回噪声也增加,得不偿失

**最终方案:Agent 驱动的多跳检索(Plan-and-Execute)**
- Planner 把复杂问题拆成子问题序列:[Q3销量排名, top1产品, 该产品Q4库存]
- Executor 顺序执行,每步结果作为下一步 context
- Reflector 检查是否所有子问题都已回答,否则继续

**量化结果**:多跳问题准确率从 41% → 76%,但延迟从 2s → 6s(用户可接受,因为复杂问题本就该慢)。

**话术**:"多跳是 RAG 的天花板问题。纯检索范式解决不了,必须上 Agent。我用 Plan-and-Execute,把'检索'从一次性变成多步规划。这块让我真正理解了 Agentic RAG 的价值——不是噱头,是解决一类检索范式解决不了的问题。"

#### 难点三:LLM 幻觉与引用失实

**冲突**:
> "系统上线初期,约 12% 的回答出现幻觉:要么编造文档里没有的内容,要么引用了不相关的文档。用户一旦发现一次幻觉,信任度就崩塌。"

**试错过程**:
1. Prompt 加"如果不知道就说不知道" → 有改善但 LLM 还是会"自信地胡说"
2. 加 temperature=0 → 略好,但根本问题是检索没命中时 LLM 硬编
3. 引用强制:要求每个 claim 必须挂引用 → LLM 会"挂错引用"

**最终方案:三层防幻觉机制**
1. **检索层**:Rerank 后加相关性阈值,score < 0.3 直接拒答
2. **生成层**:Few-shot 示例 + "只基于context回答,否则说'文档中未提及'"约束
3. **校验层**:Self-Reflect 用 NLI 模型验证每个 claim 是否被 context 支持,不支持的 claim 删除或标注"未证实"

**量化结果**:幻觉率从 12% → 2.3%,但拒答率从 5% → 11%(可接受,拒答优于胡说)。

**话术**:"幻觉是 RAG 的生死线。我的体会是:不能只靠 prompt,要从检索、生成、校验三层兜底。特别是校验层用 NLI 模型做 claim 级验证,这是我最得意的一个设计——把'信任'变成可量化的指标。"

#### 难点讲解的三个原则

1. **冲突要具体**:不要说"遇到性能问题",要说"P95 延迟从 2 秒涨到 8 秒"
2. **试错要真实**:讲 1~2 个失败的尝试,显示你不是抄答案
3. **结果要量化**:每个难点都要有 before/after 数字
</details>

---

### Q7: 项目如何展示工程能力?代码质量 / 测试 / 部署 / 监控。

<details>
<summary>点击展开:四维工程能力展示 + 项目结构 + CI/CD + 监控设计</summary>

**核心思路**:很多候选人项目功能很炫,但一问"怎么部署""怎么监控""怎么测"就露馅。工程能力是区分"demo 玩家"和"能上线"的关键。

#### 维度一:代码质量

| 实践 | 具体做法 | 面试话术 |
|------|----------|----------|
| 项目结构 | 分层 + 模块化(见下方目录树) | "我按 clean architecture 分层,core 是业务逻辑,infra 是基础设施,接口隔离" |
| 类型注解 | Python type hints + Pydantic | "所有接口用 Pydantic 做参数校验,IDE 提示 + 运行时校验双保险" |
| 配置管理 | pydantic-settings + .env | "配置和代码分离,支持多环境(dev/staging/prod)" |
| 错误处理 | 自定义异常 + 全局兜底 | "定义业务异常层级,API 层统一兜底,不让 500 裸露" |
| 代码规范 | ruff + black + pre-commit | "提交前自动格式化 + lint,代码风格统一" |

**推荐项目结构**:

```
rag-agent/
├── pyproject.toml
├── .env.example
├── docker-compose.yml
├── src/
│   ├── core/                  # 业务核心(不依赖框架)
│   │   ├── pipeline/
│   │   ├── retrieval/
│   │   ├── agent/
│   │   └── generator/
│   ├── infra/                 # 基础设施实现
│   │   ├── vectorstore/       # Milvus/Chroma 适配
│   │   ├── llm/               # LLM 适配
│   │   └── cache/
│   ├── api/                   # FastAPI 路由
│   ├── config.py              # 配置
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── eval/
│   ├── dataset.jsonl
│   └── run_ragas.py
└── deploy/
    ├── Dockerfile
    └── k8s/
```

#### 维度二:测试

| 测试类型 | 覆盖对象 | 工具 | 目标 |
|----------|----------|------|------|
| 单元测试 | 切分/检索/Agent 逻辑 | pytest | 覆盖率 > 70% |
| 集成测试 | 检索+生成端到端 | pytest + testcontainers | 关键路径全覆盖 |
| 评估测试 | 答案质量 | RAGAS + 评估集 | 指标达标 |
| 回归测试 | 迭代不退化 | 评估集 diff | 指标不下降 |

**测试示例话术**:
> "我对检索引擎写了 30+ 单测,用 testcontainers 起一个临时 Milvus 跑集成测试。每次改检索逻辑,CI 自动跑评估集,指标下降就阻断合并。这让我敢重构。"

#### 维度三:部署

| 维度 | 方案 | 话术 |
|------|------|------|
| 容器化 | Dockerfile 多阶段构建 | "多阶段构建,最终镜像 < 500MB" |
| 编排 | docker-compose(本地) / k8s(生产) | "本地 compose 一键起,生产 k8s + HPA 自动伸缩" |
| 依赖 | Milvus / Redis / ES 用官方镜像 | "中间件用官方 helm chart,不自维护" |
| 配置 | ConfigMap + Secret | "敏感配置走 Secret,非敏感走 ConfigMap" |
| 灰度 | 两套索引 + 流量切换 | "新索引构建完,流量按比例切换,出问题秒级回滚" |

**Dockerfile 示例(可讲)**:

```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --user -e . && rm -rf /root/.cache
# 运行阶段
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY src/ /app/src/
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 维度四:监控

| 监控对象 | 指标 | 工具 |
|----------|------|------|
| 调用链 | 每步耗时、token、成本 | Langfuse / LangSmith |
| 业务指标 | 答案置信度分布、拒答率、引用命中率 | 自建 + Grafana |
| 系统 | QPS、延迟、错误率 | Prometheus + Grafana |
| 用户反馈 | 点赞/点踩、追问率 | 数据库 + 看板 |

**Langfuse 追踪话术**:
> "我用 Langfuse 做全链路追踪,每次请求能看到:查询改写 → 检索 → rerank → 生成每一步的耗时、token、cost。线上 badcase 可以一键复现整条链路,定位是检索错还是生成错。这是 RAG 项目可观测性的标配。"

#### 工程能力的"四问"自检

讲完项目后,面试官常追问这四个问题,你要都能答上:
1. "怎么部署的?" → Docker + k8s
2. "怎么测试的?" → 单测 + 集成 + 评估
3. "怎么监控的?" → Langfuse + Prometheus
4. "怎么迭代不退化?" → CI 跑评估集 + 回归门禁
</details>

---

### Q8: 从 0 到 1 的项目执行计划 — 一周内完成 MVP 的日程安排。

<details>
<summary>点击展开:7 天 MVP 日程表 + 每日交付物 + 风险预案</summary>

**前提假设**:每天可投入 4~6 小时,已有 LLM API key 和基本 Python 环境。

#### 一周 MVP 日程

| Day | 主题 | 任务 | 交付物 | 预计耗时 |
|-----|------|------|--------|----------|
| D1 | 环境与数据 | ①搭项目骨架 ②选 100~500 篇文档 ③跑通 Loader | 项目可运行 + 文档加载脚本 | 5h |
| D2 | 切分与索引 | ①实现切分(父子文档) ②接 embedding ③入向量库 | 可检索 top-k | 5h |
| D3 | 检索引擎 | ①向量检索 ②加 BM25 混合 ③接 rerank | 检索质量可评估 | 6h |
| D4 | 生成与 Agent | ①Prompt 模板 ②接 LLM ③ReAct Agent 骨架 | 端到端问答可用 | 6h |
| D5 | 评估与优化 | ①构造 50 条评估集 ②跑 RAGAS ③针对性优化 | 评估报告 + 优化后指标 | 5h |
| D6 | 工程化 | ①FastAPI 接口 ②Streamlit UI ③Docker 部署 | 可演示的 web 应用 | 5h |
| D7 | 文档与演练 | ①README ②架构图 ③面试话术演练 | 可讲可演的项目 | 4h |

#### 每日详细任务

**Day 1 — 环境与数据(5h)**
- [ ] 1h 初始化项目:pyproject.toml、目录结构、pre-commit
- [ ] 1h 选数据源:公开数据集(如 Anthropic 的 gov-reports)或公司脱敏文档
- [ ] 2h 实现 Loader:用 Unstructured 加载 PDF/Markdown/HTML
- [ ] 1h 写一个 smoke test:加载 10 篇文档,打印结构

**Day 2 — 切分与索引(5h)**
- [ ] 1.5h 实现父子文档切分:结构感知 + 子块 200 token
- [ ] 1h 接 bge-m3 embedding(本地或 API)
- [ ] 1.5h 接 Milvus/Chroma,建集合 + HNSW 索引
- [ ] 1h 写检索 smoke test:5 个 query,看 top-5 结果

**Day 3 — 检索引擎(6h)**
- [ ] 1.5h 加 BM25 稀疏检索(rank_bm25 库)
- [ ] 1h 实现 RRF 融合
- [ ] 1.5h 接 bge-reranker-large
- [ ] 1h 实现 HyDE 查询改写
- [ ] 1h 横向对比:纯向量 vs 混合 vs 混合+rerank,记录 Hit@5

**Day 4 — 生成与 Agent(6h)**
- [ ] 1.5h Prompt 模板: Few-shot + 引用格式 + CoT
- [ ] 1h 接 LLM(DeepSeek/Qwen),实现 Generator
- [ ] 2h ReAct Agent 骨架:Router + Planner + Executor
- [ ] 1h 加 Self-Reflect:LLM 打分 + 低置信度重写
- [ ] 0.5h 端到端 smoke test

**Day 5 — 评估与优化(5h)**
- [ ] 2h 构造 50 条评估集(问题+金标答案+金标doc id)
- [ ] 1h 接 RAGAS,跑四指标
- [ ] 1.5h 看 badcase,针对性优化(切分/prompt/rerank 阈值)

**Day 6 — 工程化(5h)**
- [ ] 1.5h FastAPI:POST /ask 接口 + 流式返回
- [ ] 1.5h Streamlit UI:对话框 + 引用展示
- [ ] 1h Dockerfile + docker-compose(含 Milvus)
- [ ] 1h 接 Langfuse 追踪

**Day 7 — 文档与演练(4h)**
- [ ] 1h README:架构图 + 快速启动 + 指标
- [ ] 1h 画架构图(draw.io / mermaid)
- [ ] 1h 写面试话术:30 秒电梯演讲 + 三大难点
- [ ] 1h 对镜演练:5 分钟讲完项目

#### 风险预案

| 风险 | 应对 |
|------|------|
| 文档解析坑多(PDF 表格) | D1 优先选 Markdown 文档,PDF 用 LlamaParse 兜底 |
| 向量库部署慢 | 用 Chroma(嵌入式)做 MVP,后期换 Milvus |
| 评估集标注耗时 | D5 只标 50 条,够看趋势即可 |
| Agent 调试难 | D4 先做"检索+生成"无 Agent 版本,Agent 作为增强 |
| 时间不够 | 砍 Day6 的 UI,只保留 API;或砍 Day3 的 BM25,只做向量 |

#### MVP 完成标准(Definition of Done)

- [ ] 可加载 100+ 文档并建索引
- [ ] 端到端问答延迟 < 5 秒
- [ ] RAGAS 四指标均有数值
- [ ] 有 3 组对比实验数据
- [ ] Docker 一键启动
- [ ] README 有架构图
- [ ] 能 5 分钟讲清楚项目

**话术**:"我用一周做了 MVP,核心是'先跑通全链路再优化局部'。Day1-4 跑通端到端,Day5 加评估闭环,Day6 工程化,Day7 准备面试素材。这个节奏让我既有可演示的产物,又有可讲的数据。"
</details>

---

### Q9: 手撕代码题 — 实现项目的核心骨架(项目入口 / 配置管理 / 模块注册 / RAG pipeline 编排),Python 完整实现。

<details>
<summary>点击展开:完整可运行的项目骨架代码 + 注释 + 扩展点</summary>

**题目**:实现一个 RAG+Agent 项目的核心骨架,要求:
1. 配置管理(支持 .env + 多环境)
2. 模块注册(检索/生成/Agent 可插拔)
3. RAG pipeline 编排(查询改写 → 检索 → rerank → 生成 → 反思)
4. 项目入口(支持 CLI 和 API 两种调用)
5. 完整类型注解 + 错误处理

**完整代码**(可直接 `python main.py` 运行,需要装 `pydantic`, `pydantic-settings`):

```python
"""
RAG + Agent 项目核心骨架
========================
- 配置管理:pydantic-settings,支持 .env 和环境变量
- 模块注册:基于抽象基类 + 工厂模式,模块可插拔
- Pipeline 编排:查询改写 → 检索 → rerank → 生成 → 反思
- 入口:CLI 和 API 双模式
"""

from __future__ import annotations

import os
import sys
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# =====================================================================
# 1. 配置管理
# =====================================================================

class Settings(BaseSettings):
    """全局配置,从 .env 或环境变量加载。"""
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RAG_", extra="ignore")

    # 基础
    env: str = "dev"                                   # dev / staging / prod
    log_level: str = "INFO"

    # LLM
    llm_provider: str = "deepseek"                     # deepseek / qwen / openai
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 2048

    # Embedding
    embed_provider: str = "bge"                        # bge / openai
    embed_model: str = "BAAI/bge-m3"
    embed_dim: int = 1024

    # 向量库
    vectorstore_provider: str = "chroma"               # chroma / milvus
    vectorstore_host: str = "localhost"
    vectorstore_port: int = 19530
    vectorstore_collection: str = "rag_agent"
    hnsw_m: int = 16
    hnsw_ef: int = 128

    # 检索
    retrieval_top_k: int = 20
    rerank_top_k: int = 5
    rerank_threshold: float = 0.3
    use_hyde: bool = True
    use_bm25: bool = True

    # Agent
    agent_mode: str = "react"                          # react / plan_execute / none
    reflect_threshold: float = 0.6
    max_retry: int = 2

    # 生成
    max_context_tokens: int = 4096
    enable_citation: bool = True

    # 评估
    eval_dataset_path: str = "eval/dataset.jsonl"


settings = Settings()

# =====================================================================
# 2. 日志
# =====================================================================

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag-agent")


# =====================================================================
# 3. 数据模型
# =====================================================================

@dataclass
class Chunk:
    """文档切分块。"""
    id: str
    text: str
    parent_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hit:
    """检索命中。"""
    chunk: Chunk
    score: float
    source: str = ""


@dataclass
class Answer:
    """生成答案。"""
    text: str
    citations: list[Hit] = field(default_factory=list)
    confidence: float = 0.0
    retried: int = 0


class Intent(str, Enum):
    CHAT = "chat"
    RAG = "rag"
    TOOL = "tool"
    CLARIFY = "clarify"


# =====================================================================
# 4. 抽象接口(模块可插拔的关键)
# =====================================================================

class IEmbedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class IVectorStore(ABC):
    @abstractmethod
    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...
    @abstractmethod
    def search(self, vector: list[float], top_k: int) -> list[Hit]: ...


class IRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str) -> list[Hit]: ...


class IGenerator(ABC):
    @abstractmethod
    def generate(self, query: str, context: str, history: list[dict]) -> str: ...


class IAgent(ABC):
    @abstractmethod
    def route(self, query: str) -> Intent: ...
    @abstractmethod
    def reflect(self, query: str, answer: str) -> float: ...


# =====================================================================
# 5. 模块注册表(工厂模式 + 依赖注入)
# =====================================================================

class Registry:
    """模块注册表,根据配置实例化对应实现。"""

    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg
        self.embedder: IEmbedder = self._build_embedder()
        self.vectorstore: IVectorStore = self._build_vectorstore()
        self.retriever: IRetriever = self._build_retriever()
        self.generator: IGenerator = self._build_generator()
        self.agent: IAgent = self._build_agent()
        logger.info("Registry initialized: embedder=%s, vectorstore=%s, agent=%s",
                    cfg.embed_provider, cfg.vectorstore_provider, cfg.agent_mode)

    def _build_embedder(self) -> IEmbedder:
        # 实际项目:根据 self.cfg.embed_provider 返回 BGEEmbedder / OpenAIEmbedder
        return _DummyEmbedder(self.cfg.embed_dim)

    def _build_vectorstore(self) -> IVectorStore:
        return _DummyVectorStore()

    def _build_retriever(self) -> IRetriever:
        return HybridRetriever(self.vectorstore, self.embedder, self.cfg)

    def _build_generator(self) -> IGenerator:
        return _DummyGenerator(self.cfg)

    def _build_agent(self) -> IAgent:
        return ReActAgent(self.cfg)


# =====================================================================
# 6. 检索引擎实现(混合检索 + rerank + HyDE)
# =====================================================================

class HybridRetriever(IRetriever):
    """混合检索:向量 + BM25(可选)+ HyDE 改写 + Rerank。"""

    def __init__(self, vs: IVectorStore, emb: IEmbedder, cfg: Settings) -> None:
        self.vs = vs
        self.emb = emb
        self.cfg = cfg

    def _hyde(self, query: str) -> str:
        """HyDE:让 LLM 生成假设答案,用假设答案做向量检索。"""
        # 实际项目:调用 LLM 生成假设答案
        # demo 中直接返回原 query
        logger.debug("HyDE rewrite (skipped in demo)")
        return query

    def retrieve(self, query: str) -> list[Hit]:
        # 1. 查询改写
        search_query = self._hyde(query) if self.cfg.use_hyde else query

        # 2. 向量检索
        vec = self.emb.embed([search_query])[0]
        hits = self.vs.search(vec, self.cfg.retrieval_top_k)

        # 3. BM25 混合(实际项目:接 ES 或 rank_bm25)
        # 这里略,见 Day9 内容

        # 4. Rerank(实际项目:接 bge-reranker)
        # demo 中按 score 降序截断
        hits.sort(key=lambda h: h.score, reverse=True)
        reranked = hits[: self.cfg.rerank_top_k]

        # 5. 阈值过滤
        reranked = [h for h in reranked if h.score >= self.cfg.rerank_threshold]
        logger.info("Retrieved %d hits (after rerank & threshold)", len(reranked))
        return reranked


# =====================================================================
# 7. Agent 实现(ReAct + Self-Reflect)
# =====================================================================

class ReActAgent(IAgent):
    """ReAct Agent:路由 + 反思。"""

    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg

    def route(self, query: str) -> Intent:
        """简单路由:实际项目用 LLM 分类 + 规则兜底。"""
        if any(k in query for k in ["你好", "hello", "hi"]):
            return Intent.CHAT
        if "计算" in query or "查询" in query:
            return Intent.TOOL
        return Intent.RAG

    def reflect(self, query: str, answer: str) -> float:
        """反思:返回 [0,1] 置信度。实际项目用 LLM 打分。"""
        # demo:答案长度 > 50 且包含"文档"字样 → 高置信
        if len(answer) > 50 and "文档" in answer:
            return 0.8
        return 0.4


# =====================================================================
# 8. RAG Pipeline 编排(核心)
# =====================================================================

class RAGPipeline:
    """RAG 全链路编排:检索 → 上下文构造 → 生成 → 反思 → 重试。"""

    def __init__(self, reg: Registry) -> None:
        self.reg = reg
        self.history: list[dict] = []

    def _build_context(self, hits: list[Hit]) -> str:
        """把检索结果拼成上下文,带引用编号。"""
        if not hits:
            return ""
        parts = []
        for i, h in enumerate(hits, 1):
            parts.append(f"[{i}] (来源:{h.source or '未知'})\n{h.chunk.text}")
        return "\n\n".join(parts)

    async def arun(self, query: str) -> Answer:
        """异步执行 RAG 全链路。"""
        # 1. 路由
        intent = self.reg.agent.route(query)
        logger.info("Query routed: intent=%s", intent)

        if intent == Intent.CHAT:
            text = self.reg.generator.generate(query, "", self.history)
            return Answer(text=text, confidence=0.9)

        # 2. 检索
        hits = self.reg.retriever.retrieve(query)
        if not hits:
            return Answer(
                text="抱歉,文档库中未检索到相关信息,无法回答。",
                confidence=0.0,
            )

        # 3. 上下文压缩(实际项目:接 LongLLMLingua)
        context = self._build_context(hits)

        # 4. 生成
        answer_text = self.reg.generator.generate(query, context, self.history)

        # 5. 反思 + 重试
        confidence = self.reg.agent.reflect(query, answer_text)
        retried = 0
        while confidence < self.cfg.reflect_threshold and retried < self.cfg.max_retry:
            retried += 1
            logger.warning("Low confidence %.2f, retry %d", confidence, retried)
            # 实际项目:改写 query 或扩大 top_k 后重检索
            answer_text = self.reg.generator.generate(query, context, self.history)
            confidence = self.reg.agent.reflect(query, answer_text)

        # 6. 记录历史
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": answer_text})

        return Answer(
            text=answer_text,
            citations=hits,
            confidence=confidence,
            retried=retried,
        )


# =====================================================================
# 9. Dummy 实现(demo 用,实际项目替换为真实实现)
# =====================================================================

class _DummyEmbedder(IEmbedder):
    def __init__(self, dim: int) -> None:
        self.dim = dim
    def embed(self, texts: list[str]) -> list[list[float]]:
        # demo:用文本 hash 生成伪向量(实际项目调用 bge/openai)
        import hashlib
        result = []
        for t in texts:
            h = hashlib.md5(t.encode()).digest()
            vec = [(b - 128) / 128 for b in h * (self.dim // 16 + 1)][: self.dim]
            result.append(vec)
        return result


class _DummyVectorStore(IVectorStore):
    def __init__(self) -> None:
        self.store: dict[str, tuple[Chunk, list[float]]] = {}
    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        for c, v in zip(chunks, vectors):
            self.store[c.id] = (c, v)
    def search(self, vector: list[float], top_k: int) -> list[Hit]:
        # demo:用余弦相似度
        import math
        def cos(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            return dot / (na * nb + 1e-8)
        scored = [(cos(vector, v), c) for c, v in self.store.values()]
        scored.sort(reverse=True)
        return [Hit(chunk=c, score=s) for s, c in scored[:top_k]]


class _DummyGenerator(IGenerator):
    def __init__(self, cfg: Settings) -> None:
        self.cfg = cfg
    def generate(self, query: str, context: str, history: list[dict]) -> str:
        if not context:
            return f"文档中未提及'{query}'相关信息。"
        return f"根据文档,{query}的答案如下:\n{context[:200]}...\n(置信度:demo 模式)"


# =====================================================================
# 10. 入口:CLI + API
# =====================================================================

async def cli_main() -> None:
    """CLI 模式:交互式问答。"""
    reg = Registry(settings)
    pipeline = RAGPipeline(reg)

    # 预置一些 demo 文档
    demo_chunks = [
        Chunk(id="d1", text="公司请假流程:员工在 OA 系统提交请假申请,直属领导审批。"),
        Chunk(id="d2", text="报销规范:差旅报销需附发票,30 天内提交。"),
        Chunk(id="d3", text="入职指南:新员工需在入职 3 天内完成信息安全培训。"),
    ]
    reg.vectorstore.add(demo_chunks, reg.embedder.embed([c.text for c in demo_chunks]))

    print("=" * 60)
    print("RAG + Agent Demo (输入 quit 退出)")
    print("=" * 60)
    while True:
        query = input("\n你: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        answer = await pipeline.arun(query)
        print(f"\n助手: {answer.text}")
        print(f"  [置信度={answer.confidence:.2f}, 重试={answer.retried}, "
              f"引用数={len(answer.citations)}]")


def api_main() -> None:
    """API 模式:启动 FastAPI 服务。"""
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel as PyModel
    except ImportError:
        print("FastAPI 未安装,请 pip install fastapi uvicorn")
        return

    app = FastAPI(title="RAG Agent")
    reg = Registry(settings)
    pipeline = RAGPipeline(reg)

    class QueryReq(PyModel):
        query: str

    @app.post("/ask")
    async def ask(req: QueryReq) -> dict:
        ans = await pipeline.arun(req.query)
        return {
            "answer": ans.text,
            "confidence": ans.confidence,
            "citations": [{"id": h.chunk.id, "score": h.score} for h in ans.citations],
        }

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "cli"
    if mode == "api":
        api_main()
    else:
        asyncio.run(cli_main())
```

**运行方式**:

```bash
# CLI 模式
python main.py cli

# API 模式(需安装 fastapi uvicorn)
python main.py api
```

**扩展点(面试可讲)**:

| 扩展点 | 当前实现 | 升级方向 |
|--------|----------|----------|
| Embedder | Dummy(hash 向量) | BGE-M3 / OpenAI text-3 |
| VectorStore | Dummy(内存 dict) | Milvus / Qdrant |
| Retriever | 纯向量 | 加 BM25 + RRF + Rerank |
| Generator | Dummy(字符串拼接) | 接 DeepSeek / Qwen API |
| Agent | 简单路由 + 长度反思 | ReAct + LLM 打分 + 工具调用 |
| 评估 | 无 | 接 RAGAS |

**面试讲解话术**:
> "这个骨架我特意设计成'抽象 + 工厂'模式:所有模块都有接口,Registry 根据配置实例化。这样 demo 阶段用 Dummy 实现快速跑通,生产阶段换真实实现只改 Registry 不动 Pipeline。这是 DIP(依赖倒置)原则的应用,也是项目可演进的关键。"
</details>

---

### Q10: 系统设计题 — 面试白板讲解:在白板上画出你的 RAG+Agent 项目架构并讲解(含话术模板)。

<details>
<summary>点击展开:白板讲解 5 段式话术 + 常见追问 + 评分要点</summary>

**场景**:面试官说"在白板上画出你做过的 RAG 项目架构,并讲解"。限时 10~15 分钟。

#### 白板讲解 5 段式话术模板

##### 第 1 段:开场 + 业务背景(30 秒)

> "我画一下我做过的企业知识库问答 Agent。业务背景是:公司内部有 5 万篇文档,分散在 Confluence、Wiki、共享盘,员工查资料平均要 20 分钟,目标是做一个 RAG+Agent 助手,首答准确率 85%+,P95 延迟 3 秒内。"

*(白板动作:在顶部写"企业知识库问答 Agent" + 业务指标)*

##### 第 2 段:画架构六层(3 分钟)

> "我从下往上画。**最底层是数据处理 Pipeline**,负责离线把文档加载、清洗、切分、embedding、入向量库。**往上是存储层**,Milvus 做向量库,HNSW 索引,旁边一个 PG 存元数据,Redis 存对话历史。**再往上是检索引擎**,这是核心,我做的是混合检索:向量检索 + BM25,用 RRF 融合,再过一遍 bge-reranker 重排。**再往上是 Agent 决策层**,用 ReAct 模式,包含 Router 做意图路由、Planner 做任务分解、Tools 调用检索/SQL/计算器,还有 Self-Reflect 做答案置信度评分。**最上面是应用层**,FastAPI + Streamlit。**右侧贯穿的是评估和可观测**,离线用 RAGAS,在线用 Langfuse。"

*(白板动作:从下到上画 6 层框,每层标注组件,右侧画一个贯穿的评估列)*

##### 第 3 段:讲核心数据流(2 分钟)

> "我讲一下在线查询的数据流。用户提问 → Router 判断意图,如果是检索类 → 查询改写用 HyDE 生成假设答案 → 用假设答案做向量检索 top-20,同时 BM25 检索 top-20 → RRF 融合 → reranker 重排取 top-5 → 上下文压缩到 4K token → LLM 生成带引用的答案 → Self-Reflect 打分,低于 0.6 触发检索重写或追问。整个过程 P95 延迟 2.4 秒。"

*(白板动作:从上到下画箭头,标注每步的 top-k 和耗时)*

##### 第 4 段:讲技术亮点和难点(3 分钟)

> "这个项目我有三个技术亮点。**第一是父子文档切分**,解决了长文档语义断裂问题,Context Recall 从 0.68 提到 0.83。**第二是 Agent 驱动的多跳检索**,用 Plan-and-Execute 解决复杂问题,多跳准确率从 41% 到 76%。**第三是三层防幻觉机制**,检索阈值 + Prompt 约束 + NLI 校验,幻觉率从 12% 降到 2.3%。最大的难点是多跳检索,我试过单次检索 + 长 prompt、Multi-Query 都不行,最终用 Agent 规划子问题序列才解决。"

*(白板动作:在架构图旁画三个亮点气泡 + 三个指标 before/after)*

##### 第 5 段:讲结果和反思(1 分钟)

> "最终上线后首答准确率 88%,P95 延迟 2.4 秒,月节省工时约 1200 小时。反思下来,我觉得最大的收获是检索环节的 rerank 调优和 Agent 的自反思设计——前者是 RAG 的精度上限,后者是 RAG 的可靠性下限。如果重做,我会更早引入评估闭环,而不是上线后才补。"

#### 白板图最终样貌(文字版)

```
┌─────────────────────────────────────────────┐
│  企业知识库问答 Agent  目标:88%准确率,2.4s │
├─────────────────────────────────────────────┤
│  应用层: FastAPI + Streamlit               │
├─────────────────────────────────────────────┤
│  Agent: Router→Planner→Tools→Self-Reflect  │
├─────────────────────────────────────────────┤
│  检索: HyDE→向量+BM25→RRF→Rerank→压缩    │
├─────────────────────────────────────────────┤
│  存储: Milvus(HNSW) + PG(元数据) + Redis │
├─────────────────────────────────────────────┤
│  Pipeline: Load→Clean→Chunk(父子)→Embed   │
└─────────────────────────────────────────────┘
            │
   评估: RAGAS(离线) + Langfuse(在线)

  亮点: ①父子切分 ②多跳Agent ③三层防幻觉
```

#### 常见追问 + 应答

| 追问 | 应答要点 |
|------|----------|
| "为什么用 Milvus 不用 Pinecone?" | 开源可控、数据不出公司、HNSW 性能好;Pinecone 是 SaaS 有合规问题 |
| "Agent 这层是不是过度设计?" | 简单 QA 不需要,但多跳/工具调用/自反思能显著提升复杂问题,这是 Agentic RAG 价值 |
| "怎么评估的?" | RAGAS 四指标 + 200 条标注集 + 每次迭代跑全量 + badcase 分析 |
| "文档更新了怎么办?" | 增量索引:文档变更监听 + 增量 embedding + 双索引灰度切换 |
| "成本怎么控?" | 查询缓存 + 小模型路由 + 上下文压缩 + DeepSeek 替代 GPT-4 |
| "QPS 能到多少?" | 单节点 ~15 QPS(异步 + 限流),可水平扩展 Agent 层 |
| "怎么处理多轮对话?" | Redis 存历史 + 摘要压缩 + 当前 query 改写时带上历史 |

#### 白板讲解的评分要点(面试官视角)

| 评分项 | 加分 | 扣分 |
|--------|------|------|
| 结构清晰 | 分层画、有数据流箭头 | 一坨框框无层次 |
| 取舍理由 | 每个选型都说为什么 | 只列技术栈不讲理由 |
| 量化指标 | 有 before/after 数字 | "效果不错"无数字 |
| 难点真实 | 讲试错过程 | 只讲成功不讲失败 |
| 反思深度 | 讲"如果重做会怎样" | 无反思 |
| 应对追问 | 冷静、有数据、不慌 | 卡壳或编造 |

#### 演练建议

1. **对镜练 3 遍**:第 1 遍看稿,第 2 遍半脱稿,第 3 遍全脱稿
2. **录视频复盘**:看自己语速、手势、白板布局
3. **找人模拟**:让朋友扮面试官追问,练应变
4. **限时**:严格控 10 分钟,超时是大忌
</details>

---

## 三、核心知识回顾表

| 知识点 | 一句话记忆 | 面试常问度 | 关联题目 |
|--------|------------|------------|----------|
| STAR 法则 | Situation→Task→Action→Result,先给结果再给过程 | ★★★★★ | Q1 |
| 项目选题三原则 | 业务真实 + 技术覆盖 + MVP 可达 | ★★★★ | Q2 |
| 六层架构 | 数据→存储→检索→Agent→应用→评估 | ★★★★★ | Q3 |
| 父子文档切分 | 子块检索精度,父块上下文完整 | ★★★★★ | Q4/Q6 |
| 混合检索 | 向量 + BM25 + RRF + Rerank 是性价比之王 | ★★★★★ | Q4 |
| ReAct + Self-Reflect | ReAct 多步,Reflect 兜底低置信 | ★★★★ | Q4/Q6 |
| 对比实验 | 每次只变一个变量,量化对比 | ★★★★★ | Q5 |
| RAGAS 四指标 | Context Precision/Recall + Faithfulness + Answer Relevancy | ★★★★ | Q5 |
| 三大难点 | 切分断裂 / 多跳检索 / 幻觉 | ★★★★★ | Q6 |
| 工程四维 | 代码 + 测试 + 部署 + 监控 | ★★★★ | Q7 |
| 一周 MVP | D1环境→D4端到端→D5评估→D6工程化→D7演练 | ★★★ | Q8 |
| 模块可插拔 | 抽象接口 + 工厂注册,换实现不动 Pipeline | ★★★★ | Q9 |
| 白板 5 段式 | 背景→架构→数据流→亮点→反思 | ★★★★★ | Q10 |
| 30 秒电梯演讲 | 业务+指标+技术决策+结果,一句话讲完 | ★★★★★ | Q1 |
| 防幻觉三层 | 检索阈值 + Prompt 约束 + NLI 校验 | ★★★★ | Q6 |
| Langfuse 追踪 | 全链路每步耗时/token/cost 可视化 | ★★★ | Q7 |
| 增量索引 | 文档变更监听 + 增量 embedding + 双索引灰度 | ★★★ | Q10追问 |

---

## 四、面试速记卡 — 项目介绍话术模板

> **使用方法**:把下面这张卡背下来,面试时被问"介绍一下你的项目"直接套用。括号 `[]` 内按你的实际情况替换。

### 30 秒版(电梯演讲)

> "我在 [公司] 做了一个 [企业知识库问答 Agent],对接 [5 万篇] 文档,用 [bge-m3 + Milvus + 混合检索 + ReAct] 技术栈,把首答准确率从基线 [62%] 提到 [88%],P95 延迟 [2.4 秒],月节省工时 [1200 小时]。我负责 [检索引擎和 Agent 决策层],最大亮点是 [父子切分 + 多跳 Agent + 三层防幻觉]。"

### 2 分钟版(详细讲解)

> **背景**:"业务上 [员工查资料要翻 20 分钟],我们做了一个 RAG+Agent 助手来提效。"
>
> **目标**:"首答准确率 85%+,P95 延迟 3 秒内,月节省工时 1000 小时以上。"
>
> **架构**:"六层架构:数据处理 → 存储 → 检索引擎 → Agent 决策 → 应用 → 评估可观测。"
>
> **技术决策**:
> - "切分用父子文档,子块 200 token 检索,父块 1000 token 给上下文。"
> - "检索用向量 + BM25 混合,RRF 融合,bge-reranker 重排。"
> - "Agent 用 ReAct,Router 做意图路由,Self-Reflect 做置信度兜底。"
> - "评估用 RAGAS 四指标,200 条标注集,每次迭代跑全量。"
>
> **结果**:"准确率 62%→88%,延迟 P95 2.4s,幻觉率 12%→2.3%,月省 1200 工时。"
>
> **反思**:"最大收获是 rerank 调优和自反思设计。如果重做,会更早引入评估闭环。"

### 难点讲解卡(被追问时用)

> **难点1 切分**:"长文档固定切分会语义断裂。我试过递归切分、语义切分,最终用父子文档 + 结构感知,Context Recall 0.68→0.83。"
>
> **难点2 多跳**:"复杂问题单次检索解决不了。试过长 prompt、Multi-Query 都不行,最终用 Plan-and-Execute 多步规划,多跳准确率 41%→76%。"
>
> **难点3 幻觉**:"LLM 一本正经胡说。我用三层兜底:检索阈值 + Prompt 约束 + NLI 校验,幻觉率 12%→2.3%,拒答率 5%→11%(可接受)。"

### 技术选型卡(被追问时用)

| 选型 | 我的回答 |
|------|----------|
| 为什么 Milvus? | 开源、HNSW、可扩展、数据不出公司 |
| 为什么 bge-m3? | 开源、多语言、可本地部署、性价比高 |
| 为什么 ReAct? | 通用、支持多步、社区成熟;复杂场景可升 Plan-and-Execute |
| 为什么 DeepSeek? | 性价比高、中文好、API 兼容 OpenAI |
| 为什么 RAGAS? | 业界标准、四指标覆盖检索+生成、可自动化 |
| 为什么不用 long context? | 成本、延迟、可更新性、可溯源四点 |

---

## 五、易错点提醒(10 个)

> 面试中讲项目最容易犯的 10 个错误,逐一对照自检。

### 易错点 1:把项目讲成技术栈罗列

**错误**:"我用了 LangChain、Milvus、bge、FastAPI、Docker……"
**正确**:"我解决了 X 问题,用了 Y 技术因为 Z,效果是 W。"
**原因**:面试官要的是判断力,不是购物清单。

### 易错点 2:指标全是"还不错""挺好的"

**错误**:"效果还不错,用户反馈挺好。"
**正确**:"准确率从 62% 提到 88%,P95 延迟 2.4 秒,月省 1200 工时。"
**原因**:无数字 = 没做过 = 直接淘汰。

### 易错点 3:只讲成功不讲试错

**错误**:"我用父子文档,效果很好。"
**正确**:"我先试固定切分,表格被拆;再试语义切分,边界不稳;最后用父子文档 + 结构感知,才解决。"
**原因**:试错过程证明真实性,成功故事像编的。

### 易错点 4:架构图无层次一坨框

**错误**:白板上画 20 个框用线乱连。
**正确**:分 6 层,每层 3~5 个组件,数据流箭头从上到下。
**原因**:层次清晰 = 思维清晰 = 工程素养。

### 易错点 5:Agent 讲成万能药

**错误**:"我加了 Agent,什么问题都解决了。"
**正确**:"简单 QA 不用 Agent;多跳/工具调用/自反思才需要,这是 Agentic RAG 的适用边界。"
**原因**:过度吹捧技术 = 不懂取舍 = 扣分。

### 易错点 6:不提评估就说效果

**错误**:"准确率 88%。"
**正确**:"我用 RAGAS 在 200 条标注集上测,Context Recall 0.83, Faithfulness 0.91,综合准确率 88%。"
**原因**:不讲评估方法的指标 = 不可信。

### 易错点 7:把 demo 当生产讲

**错误**:"我的项目支持万级 QPS。"
**正确**:"MVP 单节点 15 QPS,生产可水平扩展 Agent 层。"
**原因**:夸大 = 被追问就露馅 = 诚信问题。

### 易错点 8:回避"你做了什么"

**错误**:"我们团队做了……" 全程"我们"。
**正确**:"我负责检索引擎和 Agent 决策层,具体做了 X/Y/Z。"
**原因**:面试官招的是你,不是团队。

### 易错点 9:不会讲"如果重做"

**错误**:"我觉得项目挺完美的。"
**正确**:"如果重做,我会更早引入评估闭环,且把切分策略做成可配置。"
**原因**:无反思 = 无成长性 = 潜力不足。

### 易错点 10:白板讲解超时

**错误**:讲了 20 分钟还没讲完,被打断。
**正确**:严格 10 分钟,5 段式各 2 分钟,留 5 分钟追问。
**原因**:超时 = 表达能力差 = 协作风险。

---

## 六、自测检查清单

### 概念题(10 道)

- [ ] 1. 能用 STAR 法则在 30 秒内讲完项目吗?
- [ ] 2. 能说出三个项目选题的优缺点和适用人群吗?
- [ ] 3. 能默画出六层架构图吗?
- [ ] 4. 能讲清四大模块(处理/检索/Agent/生成)的技术选型和理由吗?
- [ ] 5. 能说出对比实验的三组设计和结论吗?
- [ ] 6. 能讲清三大难点(切分/多跳/幻觉)的试错过程和最终方案吗?
- [ ] 7. 能说出工程四维(代码/测试/部署/监控)的具体做法吗?
- [ ] 8. 能背出一周 MVP 的 7 天日程和每日交付物吗?
- [ ] 9. 能讲清"为什么不用 long context 直接塞"的四个理由吗?
- [ ] 10. 能说出 RAGAS 四指标的含义和目标值吗?

### 代码题(3 道)

- [ ] 11. 能默写 RAGPipeline.arun 的核心流程(路由→检索→生成→反思→重试)吗?
- [ ] 12. 能实现一个可插拔的 Registry(抽象接口 + 工厂)吗?
- [ ] 13. 能用 pydantic-settings 写一个支持 .env 的配置类吗?

### 系统设计题(2 道)

- [ ] 14. 能在白板上 10 分钟内画完架构图并讲完 5 段式吗?
- [ ] 15. 能应对 7 个常见追问(Milvus vs Pinecone / Agent 过度设计 / 评估方法 / 文档更新 / 成本 / QPS / 多轮对话)吗?

---

## 七、延伸阅读 — 优秀开源 RAG 项目参考

> 看别人的项目是提升最快的办法。以下项目按"参考价值"排序,建议至少精读 2 个。

| 项目 | 地址 | 亮点 | 参考价值 |
|------|------|------|----------|
| **RAGFlow** | github.com/infiniflow/ragflow | 深度文档解析 + 模板化切分 + 可视化 | ★★★★★ |
| **Dify** | github.com/langgenius/dify | RAG + Agent + 工作流一站式平台 | ★★★★★ |
| **LangGraph RAG Agent** | langchain-ai.github.io/langgraph | 官方 Agentic RAG + Self-Reflect 范式 | ★★★★★ |
| **LlamaIndex** | github.com/run-llama/llama_index | RAG 框架标杆,高级检索器丰富 | ★★★★ |
| **QAnything** | github.com/netease-youdao/QAnything | 网易有道开源,中文 RAG 友好 | ★★★★ |
| **FastGPT** | github.com/labring/FastGPT | 国产开源,知识库 + 工作流 | ★★★★ |
| **Verba** | github.com/weaviate/Verba | Weaviate 官方 demo,轻量易读 | ★★★ |
| **Self-RAG** | github.com/AkariAsai/self-rag | 自反思 RAG 论文实现,研究向 | ★★★ |
| **GraphRAG** | github.com/microsoft/graphrag | 微软图谱 RAG,知识图谱增强 | ★★★ |
| **LightRAG** | github.com/HKUDS/LightRAG | 轻量图增强 RAG,论文+实现 | ★★★ |

**精读建议**:
1. **RAGFlow**:看它的 `chunker` 模块,学结构感知切分
2. **LangGraph RAG Agent**:学 CrRect(自反思 RAG)的状态机设计
3. **Dify**:看它的 `api/core/rag` 目录,学工程化组织

**简历项目描述参考句式**:

```
项目:企业知识库问答 Agent(个人项目 / 实习项目)
- 基于 RAG + ReAct Agent 架构,对接 5 万篇多源文档,实现首答准确率 88%、P95 延迟 2.4s
- 设计父子文档切分 + 混合检索(向量+BM25+Rerank),Context Recall 较基线提升 15 个点
- 实现 Plan-and-Execute 多跳检索,复杂问题准确率从 41% 提升至 76%
- 设计三层防幻觉机制(检索阈值+Prompt约束+NLI校验),幻觉率从 12% 降至 2.3%
- 用 RAGAS 构建评估闭环,200 条标注集,三组对比实验驱动迭代
- 技术栈:Python / FastAPI / Milvus / bge-m3 / DeepSeek / LangGraph / RAGAS / Docker
```

---

## 八、明日预告:Day 14 — Week2 回顾与手撕代码

> Day13 规划完项目,Day14 进入"动手"环节。

**Day14 预告内容**:
1. **Week2 全周回顾**:RAG 全链路 / Agentic RAG / 向量数据库 / 上下文工程 / RAG 评估 / 项目规划 六大主题串讲
2. **Week2 知识大串讲**:用一个完整案例把 6 天知识点串起来,形成"知识网络"
3. **手撕代码专题**:在 Day13 骨架基础上,手撕 3 个核心组件 —— ①混合检索引擎(向量+BM25+RRF+Rerank)②ReAct Agent(含工具调用和自反思)③RAGAS 评估脚本
4. **Week2 模拟面试**:10 道高频题 + 2 道系统设计题,限时作答
5. **Week3 预告**:进入"框架与系统设计"周,LangChain / LangGraph / AutoGen / MetaGPT 深度拆解

**今日作业**:
- [ ] 选定你的项目选题(A/B/C 三选一),写下 30 秒电梯演讲
- [ ] 在纸上默画一遍六层架构图(不看答案)
- [ ] 把 Q9 的骨架代码跑通,理解 Registry 和 Pipeline 的设计
- [ ] 对镜演练一次 5 段式白板讲解,限时 10 分钟

> **今日金句**:"项目不是讲出来的,是练出来的。Day13 给你地图,Day14 给你武器,剩下 17 天反复打磨,面试场上才能信手拈来。"

---

*Day 13 完。明日 Day 14 见。*
