# Day 09 — Agentic RAG 与 GraphRAG

> **学习目标**: 深入掌握 Agentic RAG 的自主检索决策机制与 GraphRAG 的知识图谱增强检索范式,能够在面试中清晰阐述二者的核心思想、实现细节、适用场景,并能手撕 Agentic RAG 代码、设计融合两者的研究助手系统。
>
> **面试定位**: 中高级 Agent 工程师岗位的高频考点。Day08 复习了 RAG 全链路(索引/检索/生成/评估),Day09 进入两个进阶方向 —— 这是区分"会用 RAG 框架"和"能设计 RAG 系统"的关键分水岭。面试官常通过这一主题考察候选人对 RAG 局限性的理解、对 Agent 决策循环的掌握、以及对知识图谱与向量检索融合的系统性思考。
>
> **预计学习时长**: 3-4 小时(理论 1.5h + 代码 1.5h + 系统设计 1h)
>
> **前置知识**: Day08 的 RAG 全链路(Embedding/Chunking/向量检索/Rerank/RAG评估)、Day04 的 ReAct 模式、Day05 的 Tool Use。

---

## 今日知识图谱

```
Agentic RAG 与 GraphRAG
│
├── Agentic RAG(自主检索决策)
│   │
│   ├── 核心思想
│   │   ├── Agent 作为检索的"大脑",而非固定 Pipeline
│   │   ├── LLM 自主决策:何时检索 / 检索什么 / 从哪检索 / 是否足够
│   │   └── 本质:把 RAG 从"线性流程"升级为"闭环控制系统"
│   │
│   ├── 五大核心能力
│   │   ├── 1. 检索路由(Retrieval Routing)
│   │   │   ├── 语义路由:按 query 意图分发到不同索引
│   │   │   ├── 数据源路由:向量库 / 知识图谱 / SQL / Web Search
│   │   │   └── 策略路由:单次检索 / 多跳检索 / 迭代检索
│   │   │
│   │   ├── 2. 查询构造(Query Construction)
│   │   │   ├── Query Rewriting:改写为更适合检索的形式
│   │   │   ├── Sub-query Decomposition:复杂问题拆解为子问题
│   │   │   ├── HyDE:假设性文档嵌入
│   │   │   └── Step-back Prompting:抽象到更高层级
│   │   │
│   │   ├── 3. 结果评估(Result Evaluation)
│   │   │   ├── 相关性评分:LLM-as-Judge / 交叉编码器
│   │   │   ├── 充分性判断:当前证据能否回答问题
│   │   │   └── 矛盾检测:多源证据冲突处理
│   │   │
│   │   ├── 4. 迭代检索(Iterative Retrieval)
│   │   │   ├── 不足则补检索,基于缺口生成新 query
│   │   │   ├── 最大迭代次数限制(防无限循环)
│   │   │   └── 收敛判断:答案置信度阈值
│   │   │
│   │   └── 5. 多跳推理(Multi-hop Reasoning)
│   │       ├── 链式推理:A→B→C,前跳结果指导后跳
│   │       ├── 并行子问题:独立子问题并行检索
│   │       └── 推理链可视化:便于调试与可解释
│   │
│   ├── 检索门控(Retrieval Gating)
│   │   ├── 何时跳过检索:参数知识足够 / 闲聊 / 简单事实
│   │   ├── 何时触发检索:时效性信息 / 长尾知识 / 需要引用
│   │   └── 实现方式:分类器 / LLM 判断 / 置信度阈值
│   │
│   ├── 防无限循环机制
│   │   ├── 最大迭代数(如 max_iterations=5)
│   │   ├── 重复 query 检测(嵌入相似度阈值)
│   │   ├── 收敛判断(答案置信度不再提升)
│   │   └── 超时熔断(单次检索 token/时间上限)
│   │
│   └── 代表框架
│       ├── LangGraph 的 Self-RAG / Corrective RAG(CRAG)
│       ├── LlamaIndex Workflow / Agent Workflow
│       ├── AutoGen 的 retrieval agent
│       └── 自研 ReAct + RAG 工具组合
│
├── GraphRAG(知识图谱增强检索)
│   │
│   ├── 核心思想
│   │   ├── 用知识图谱结构化文档,捕获实体间关系
│   │   ├── 向量检索擅长"相似",图谱擅长"关联"
│   │   └── 社区检测形成层次化摘要,支持全局问题
│   │
│   ├── 图谱构建流程
│   │   ├── 1. 文档切分(Chunking)
│   │   ├── 2. 实体抽取(NER + LLM 抽取)
│   │   │   ├── Named Entity Recognition
│   │   │   └── LLM Prompt 抽取(更灵活,成本高)
│   │   ├── 3. 关系抽取(Relation Extraction)
│   │   │   ├── 实体对之间的关系类型
│   │   │   └── 关系强度/置信度
│   │   ├── 4. 实体消歧与合并(Entity Resolution)
│   │   ├── 5. 社区检测(Community Detection)
│   │   │   ├── Leiden 算法(优于 Louvain)
│   │   │   ├── 层次化聚类:形成多层级社区
│   │   │   └── 社区摘要:LLM 生成每个社区摘要
│   │   └── 6. 索引:实体索引 / 关系索引 / 社区摘要索引
│   │
│   ├── 查询模式
│   │   ├── 局部查询(Local Search)
│   │   │   ├── 从种子实体出发,扩展邻居
│   │   │   ├── 适合:具体实体相关的问题
│   │   │   └── 类似向量检索 + 图遍历
│   │   └── 全局查询(Global Search)
│   │       ├── 遍历所有社区摘要,Map-Reduce 聚合
│   │       ├── 适合:"整个数据集的主题是什么"类问题
│   │       └── 无需定位具体实体,直接回答全局问题
│   │
│   ├── Microsoft GraphRAG 框架
│   │   ├── 开源实现:github.com/microsoft/graphrag
│   │   ├── Pipeline:Indexing(构建图) + Query(局部/全局)
│   │   ├── 关键参数:社区层级、摘要长度、实体抽取 prompt
│   │   └── 与向量 RAG 对比:全局问题 F1 提升 50%+
│   │
│   ├── 向量 RAG vs GraphRAG
│   │   ├── 向量 RAG:擅长语义相似、局部事实、单跳
│   │   ├── GraphRAG:擅长多跳关联、全局主题、关系推理
│   │   ├── 成本:GraphRAG 构图成本高(大量 LLM 调用)
│   │   └── 融合:Hybrid RAG = 向量 + 图谱 + 重排
│   │
│   └── Leiden 算法要点
│       ├── 改进 Louvain:解决"连通分量"问题
│       ├── 三阶段:局部优化 → 社区细化 → 全局聚合
│       ├── 层次化:可输出多层级社区树
│       └── 模块度 Q(Modularity)作为优化目标
│
└── 系统设计融合
    ├── 研究助手 = Agentic RAG + GraphRAG
    ├── 路由决策:向量 / 图谱 / Web / 混合
    ├── 迭代检索:不足时补充,跨源融合
    ├── 引用追溯:每个论断标注来源
    └── 评估闭环:离线评测 + 在线反馈
```

---

## 面试题

### Q1: 什么是 Agentic RAG?它与传统 RAG 的本质区别是什么?

<details>
<summary>点击查看答案</summary>

**Agentic RAG 定义**: Agentic RAG 是将 Agent 的自主决策能力引入检索增强生成流程的范式。Agent 不再被动地执行"检索-生成"固定管线,而是作为一个**有状态的决策中枢**,根据当前上下文动态判断:是否需要检索、检索什么内容、从哪个数据源检索、检索结果是否充分、是否需要再次检索。

**传统 RAG vs Agentic RAG 对比**:

| 维度 | 传统 RAG | Agentic RAG |
|------|---------|-------------|
| **流程** | 线性:Query → Retrieve → Generate | 闭环:Query → 决策 → 检索 → 评估 → (迭代) → Generate |
| **检索次数** | 固定 1 次(或固定 K 次) | 动态,由 Agent 决定(0 到 N 次) |
| **查询形式** | 原始 query 直接检索 | Query Rewriting / Sub-query 分解 / HyDE |
| **数据源** | 单一向量库 | 多源路由:向量库 / 知识图谱 / SQL / Web |
| **结果处理** | Top-K 直接拼接到 prompt | 相关性评估 + 充分性判断 + 矛盾检测 |
| **可解释性** | 低(黑盒检索) | 高(可展示推理链与检索轨迹) |
| **失败模式** | 检索失败则生成失败 | 可自我纠错,补充检索 |
| **成本** | 低且可预测 | 高且不可预测(可能多轮 LLM 调用) |

**本质区别**: 传统 RAG 是**检索增强的生成**,Agent 只在最后一步介入;Agentic RAG 是**生成驱动的检索**,Agent 贯穿整个流程,把检索当作可调用的工具(Tool)。可以类比为:传统 RAG 像"查字典造句",Agentic RAG 像"研究员查资料写报告"——研究员会判断资料够不够、要不要换关键词再查、要不要查别的数据库。

**代码层面对比**:

```python
# 传统 RAG(固定管线)
def traditional_rag(query):
    docs = vector_db.search(query, k=5)  # 固定检索
    return llm.generate(query, docs)      # 直接生成

# Agentic RAG(决策循环)
def agentic_rag(query):
    state = {"query": query, "evidence": [], "iterations": 0}
    while state["iterations"] < MAX_ITER:
        action = agent.decide(state)      # Agent 决策下一步
        if action.type == "sufficient":
            return llm.generate(query, state["evidence"])
        elif action.type == "retrieve":
            new_docs = retrieve(action.query, action.source)
            state["evidence"].extend(evaluate(new_docs))
        state["iterations"] += 1
    return llm.generate(query, state["evidence"])
```

**面试加分点**: 提到 Agentic RAG 的核心是**把检索从"一次性的检索调用"变成"Agent 的工具集"**,并强调这种范式的代价是更高的延迟和成本,因此需要检索门控(后续 Q5)来平衡。

</details>

---

### Q2: 请详细说明 Agentic RAG 的五大核心能力

<details>
<summary>点击查看答案</summary>

Agentic RAG 的五大核心能力构成一个完整的决策闭环,每个能力对应 Agent 的一个"思考维度"。

#### 1. 检索路由(Retrieval Routing)

**作用**: 决定"从哪里检索"。根据 query 的意图和属性,将检索请求分发到最合适的数据源或索引。

**实现方式**:
- **语义路由**: 用一个小模型或 LLM 判断 query 类型(事实型/推理型/时效型/关系型),路由到不同索引
- **数据源路由**: 
  - 事实型 → 向量库(文档语料)
  - 关系型 → 知识图谱(GraphRAG)
  - 数值型 → SQL 数据库(Text-to-SQL)
  - 时效型 → Web Search
  - 代码型 → 代码索引
- **策略路由**: 单次检索 / 多跳检索 / 迭代检索

```python
def retrieval_router(query: str) -> Route:
    intent = llm.classify(query, labels=["factual", "relational", "temporal", "numerical"])
    routing_map = {
        "factual": Route(source="vector_db", strategy="single"),
        "relational": Route(source="graph", strategy="multi_hop"),
        "temporal": Route(source="web_search", strategy="single"),
        "numerical": Route(source="sql_db", strategy="single"),
    }
    return routing_map[intent]
```

#### 2. 查询构造(Query Construction)

**作用**: 决定"用什么 query 检索"。原始用户问题往往不适合直接检索,需要改写或分解。

**主要技术**:
- **Query Rewriting**: 用 LLM 把口语化问题改写为关键词形式。例如"苹果最近怎么样" → "Apple Inc quarterly earnings 2026"
- **Sub-query Decomposition**: 把复杂问题拆成多个子问题。例如"比较 GPT-4 和 Claude 在代码任务上的表现" → ["GPT-4 code task benchmarks", "Claude code task benchmarks"]
- **HyDE(Hypothetical Document Embeddings)**: 先让 LLM 生成一个"假设性答案文档",用该文档的 embedding 检索。原理:答案比问题更接近目标文档的语义空间
- **Step-back Prompting**: 把具体问题抽象到更高层级。例如"2024 年诺贝尔物理学奖得主是谁" → "诺贝尔物理学奖近年得主列表"

```python
def query_constructor(query: str) -> list[str]:
    # 子问题分解
    sub_queries = llm.decompose(query)
    # 对每个子问题做 HyDE 增强
    hyde_queries = []
    for sq in sub_queries:
        hyp_doc = llm.generate(f"Write a passage answering: {sq}")
        hyde_queries.append(hyp_doc)
    return sub_queries + hyde_queries
```

#### 3. 结果评估(Result Evaluation)

**作用**: 决定"检索结果好不好,够不够"。这是 Agentic RAG 区别于传统 RAG 的关键能力。

**三个评估维度**:
- **相关性(Relevance)**: 检索文档与 query 是否相关。方法:Cross-Encoder 重排、LLM-as-Judge 打分
- **充分性(Sufficiency)**: 当前证据是否足以回答问题。方法:LLM 判断 "Given the evidence, can you fully answer the question?"
- **矛盾性(Conflict)**: 多源证据是否冲突。方法:LLM 检测矛盾,冲突时优先高可信度源

```python
def evaluate_results(query: str, docs: list[Doc]) -> EvalResult:
    # 相关性过滤
    relevant = [d for d in docs if cross_encoder.score(query, d) > 0.5]
    # 充分性判断
    sufficiency = llm.judge(
        f"Query: {query}\nEvidence: {relevant}\nCan you fully answer? (yes/no/partial)"
    )
    # 矛盾检测
    conflicts = llm.detect_conflicts(relevant)
    return EvalResult(relevant=relevant, sufficient=(sufficiency=="yes"), conflicts=conflicts)
```

#### 4. 迭代检索(Iterative Retrieval)

**作用**: 当结果不充分时,基于"信息缺口"生成新 query,补充检索。

**核心机制**:
- **缺口识别**: LLM 输出"还缺少什么信息"
- **新 query 生成**: 基于缺口生成针对性 query
- **终止条件**: 充分 / 最大迭代数 / 置信度收敛

```python
def iterative_retrieve(query: str, max_iter: int = 5):
    evidence = []
    for i in range(max_iter):
        if i == 0:
            q = query
        else:
            gap = llm.identify_gap(query, evidence)
            q = llm.generate_query_for_gap(gap)
        docs = retrieve(q)
        evidence.extend(filter_relevant(query, docs))
        if llm.is_sufficient(query, evidence):
            break
    return evidence
```

#### 5. 多跳推理(Multi-hop Reasoning)

**作用**: 处理需要跨文档、跨步骤推理的复杂问题。

**典型场景**: "Tesla CEO 在 2024 年收购的那家公司的总部在哪个城市?"
- Hop 1: Tesla CEO → Elon Musk
- Hop 2: Elon Musk 2024 年收购的公司 → Twitter(X)
- Hop 3: X 的总部 → San Francisco

**实现方式**:
- **链式推理**: 前一跳结果作为后一跳的 query 上下文
- **并行子问题**: 独立子问题并行检索后合并
- **推理链记录**: 每一跳的 query/docs/中间结论都记录,便于可解释

```python
def multi_hop_reasoning(question: str, max_hops: int = 4):
    chain = []
    current_q = question
    for hop in range(max_hops):
        docs = retrieve(current_q)
        sub_answer = llm.extract_partial_answer(question, docs, chain)
        chain.append({"hop": hop, "query": current_q, "docs": docs, "answer": sub_answer})
        next_q = llm.generate_next_query(question, chain)
        if next_q is None:  # 推理完成
            break
        current_q = next_q
    return llm.synthesize(question, chain), chain
```

**面试加分点**: 这五大能力不是孤立的,而是**层层递进**的:路由决定"去哪",构造决定"怎么查",评估决定"够不够",迭代决定"要不要再来",多跳决定"怎么串起来"。一个成熟的 Agentic RAG 系统需要把这五者编排成一个状态机(如 LangGraph 实现)。

</details>

---

### Q3: Agentic RAG 的迭代检索如何实现?如何防止无限循环?

<details>
<summary>点击查看答案</summary>

**迭代检索的本质**: 一个 while 循环,每次根据当前证据状态决定是否继续检索、检索什么。这是 Agentic RAG 最具 Agent 特色的部分——传统 RAG 没有这个循环。

**完整实现骨架**:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RetrievalState:
    question: str
    evidence: list = field(default_factory=list)
    iterations: int = 0
    history_queries: list = field(default_factory=list)  # 防重复
    confidence: float = 0.0
    done: bool = False

class IterativeRetriever:
    def __init__(self, max_iterations=5, confidence_threshold=0.85,
                 duplicate_query_threshold=0.9, max_tokens_per_iter=4000):
        self.max_iter = max_iterations
        self.conf_thresh = confidence_threshold
        self.dup_thresh = duplicate_query_threshold
        self.max_tokens = max_tokens_per_iter

    def run(self, question: str) -> tuple[str, RetrievalState]:
        state = RetrievalState(question=question)
        while not state.done and state.iterations < self.max_iter:
            # Step 1: 生成下一跳 query(首轮用原问题)
            if state.iterations == 0:
                query = question
            else:
                gap = self.identify_gap(state)
                if gap is None:  # 无缺口,直接收敛
                    break
                query = self.generate_query_for_gap(gap, state)
                # 防重复 query
                if self.is_duplicate_query(query, state.history_queries):
                    break

            # Step 2: 检索
            docs = self.retrieve(query)
            # Token 预算控制
            docs = self.truncate_to_budget(docs, self.max_tokens)

            # Step 3: 评估
            scored = self.score_and_filter(question, docs)
            state.evidence.extend(scored)
            state.history_queries.append(query)

            # Step 4: 充分性 & 置信度判断
            state.confidence = self.estimate_confidence(state)
            if state.confidence >= self.conf_thresh:
                state.done = True
                break

            # Step 5: 收敛检测(置信度不再提升)
            if self.is_converged(state):
                break

            state.iterations += 1

        answer = self.synthesize(state)
        return answer, state

    def identify_gap(self, state) -> Optional[str]:
        """让 LLM 输出当前证据还缺什么"""
        return llm.call(
            f"Question: {state.question}\nEvidence: {state.evidence}\n"
            f"What information is still missing? If nothing, return NONE."
        )

    def is_duplicate_query(self, query, history) -> bool:
        """嵌入相似度判断是否重复 query"""
        q_emb = embed(query)
        for h in history:
            if cosine_sim(q_emb, embed(h)) > self.dup_thresh:
                return True
        return False

    def is_converged(self, state) -> bool:
        """连续两轮置信度提升小于阈值则收敛"""
        if len(state.confidence_history) < 2:
            return False
        return abs(state.confidence_history[-1] - state.confidence_history[-2]) < 0.02
```

**防止无限循环的五大机制**:

| 机制 | 说明 | 典型阈值 |
|------|------|----------|
| **1. 最大迭代数** | 硬性上限,最简单兜底 | 3-5 次 |
| **2. 重复 query 检测** | 嵌入相似度 > 阈值则停止 | cosine > 0.9 |
| **3. 置信度阈值** | 答案置信度达标即停 | 0.85 |
| **4. 收敛检测** | 置信度提升 < δ 则停止 | δ = 0.02 |
| **5. Token / 时间预算** | 每轮检索 token 上限,总时间上限 | 4k tokens/轮,30s 总时长 |

**为什么这五个机制缺一不可**:
- 只用最大迭代数:可能浪费成本(已经够好但还在检索)
- 只用置信度:LLM 自评不准,可能过早收敛或永不收敛
- 只用重复检测:Agent 可能持续生成相似但不同的 query
- 只用预算:粗糙,无法优雅降级

**进阶:状态机视角**

迭代检索本质是一个状态机,LangGraph 是实现它的理想框架:

```
START → retrieve → evaluate → (sufficient?) 
                              ├─ yes → generate → END
                              ├─ no, < max_iter → rewrite_query → retrieve(循环)
                              └─ no, ≥ max_iter → generate(best_effort) → END
```

**面试加分点**:
1. 强调"防无限循环"不是单一机制,而是**多层防御**
2. 提到 LLM 自评置信度不可靠,需要结合**外部信号**(如交叉编码器分数、证据数量)
3. 提到"优雅降级":达到上限时不应直接失败,而应基于已有证据 best-effort 生成,并在答案中标注"信息可能不完整"

</details>

---

### Q4: 什么是多跳推理(Multi-hop Reasoning)?如何构建跨文档推理链?

<details>
<summary>点击查看答案</summary>

**多跳推理定义**: 需要跨越多个文档、通过多个推理步骤才能得到答案的问题求解范式。每一跳的中间结论是下一跳检索/推理的输入。

**典型多跳问题示例**:

| 问题 | 跳数 | 推理链 |
|------|------|--------|
| "Tesla CEO 在 2024 年收购的公司的总部在哪?" | 3 | Tesla CEO → Elon Musk → 2024 收购 X → X 总部 San Francisco |
| "获得 2023 年图灵奖的学者的导师是谁?" | 2 | 2023 图灵奖得主 → Ajit Agrawal → 导师是谁 |
| "对比 RAG 和 GraphRAG 在 HotpotQA 上的表现" | 4 | RAG 在 HotpotQA 分数 + GraphRAG 在 HotpotQA 分数 + 对比 + 结论 |

**单跳 vs 多跳对比**:

```
单跳:Q → Retrieve(1次) → A
多跳:Q → Retrieve(hop1) → A1 → Retrieve(A1+Q) → A2 → ... → Retrieve(An-1+Q) → An
```

**跨文档推理链构建的三种范式**:

#### 范式 1: 链式推理(Sequential / Chain)

最直观,前跳结果指导后跳 query:

```python
def chain_multi_hop(question: str, max_hops: int = 4):
    chain = []
    current_query = question
    for hop in range(max_hops):
        docs = retrieve(current_query)
        partial = llm.extract_answer(question, docs, chain)
        chain.append({"hop": hop, "query": current_query, "docs": docs, "partial": partial})
        # 让 LLM 判断是否需要继续
        next_query = llm.generate_next_hop_query(question, chain)
        if next_query == "DONE":
            break
        current_query = next_query
    final = llm.synthesize(question, chain)
    return final, chain
```

**优点**: 简单、可解释、推理链清晰
**缺点**: 错误会沿链传播(error propagation),前跳错误导致后跳全错

#### 范式 2: 并行子问题(Parallel Sub-questions)

把复杂问题分解为独立子问题,并行检索后合并:

```python
def parallel_multi_hop(question: str):
    sub_qs = llm.decompose(question)  # ["RAG HotpotQA score", "GraphRAG HotpotQA score"]
    # 并行检索
    sub_results = []
    with ThreadPoolExecutor() as executor:
        futures = {sq: executor.submit(retrieve_and_answer, sq) for sq in sub_qs}
        for sq, fut in futures.items():
            sub_results.append({"sub_q": sq, "result": fut.result()})
    # 合并
    final = llm.combine(question, sub_results)
    return final, sub_results
```

**优点**: 子问题独立、可并行、错误隔离
**缺点**: 需要问题本身可分解,不适用于"必须先得到 A 才能问 B"的强依赖场景

#### 范式 3: 树形推理(Tree-of-Thought / ReST)

结合链式与并行,在每一步生成多个候选推理路径,择优扩展:

```python
def tree_multi_hop(question: str, beam_width: int = 3, max_depth: int = 4):
    frontier = [{"query": question, "chain": [], "score": 1.0}]
    for depth in range(max_depth):
        candidates = []
        for node in frontier:
            docs = retrieve(node["query"])
            # 生成多个候选下一步
            next_steps = llm.generate_candidates(question, node["chain"], docs, k=beam_width)
            for step in next_steps:
                new_chain = node["chain"] + [step]
                score = self.score_chain(question, new_chain)
                candidates.append({"query": step.next_query, "chain": new_chain, "score": score})
        # Beam Search:保留 top-k
        frontier = sorted(candidates, key=lambda x: x["score"], reverse=True)[:beam_width]
        if frontier[0]["score"] > 0.9:  # 高置信度提前终止
            break
    return llm.synthesize(question, frontier[0]["chain"]), frontier[0]["chain"]
```

**优点**: 容错性强、能探索多种推理路径
**缺点**: 成本最高(每跳多次 LLM 调用)

**多跳推理的关键挑战**:

1. **错误传播**: 前跳错误导致后跳偏离 → 缓解:每跳置信度评估,低置信度时回溯
2. **检索漂移**: 中间 query 偏离原问题 → 缓解:每跳 query 都携带原问题作为上下文
3. **跳数不可预测**: 不知道需要几跳 → 缓解:让 LLM 自主判断"是否完成"
4. **可解释性要求**: 需要展示推理链 → 缓解:结构化记录每跳的 query/docs/结论

**评测基准**:
- **HotpotQA**: 维基百科多跳问答,2-4 跳
- **2WikiMultiHopQA**: 跨维基百科多跳
- **MuSiQue**: 多步推理,跳数 2-4
- **BEIR**: 多任务检索基准

**面试加分点**:
1. 强调"多跳不是简单的多次检索",关键是**前跳结果作为后跳的输入**
2. 提到错误传播是核心挑战,需要**置信度评估 + 回溯机制**
3. 提到 GraphRAG(Q6-Q8)天然适合多跳,因为图结构直接编码了实体间关系

</details>

---

### Q5: 什么是检索门控(Retrieval Gating)?如何判断是否需要检索?

<details>
<summary>点击查看答案</summary>

**检索门控定义**: 在 Agentic RAG 中,不是每个 query 都需要检索。检索门控是一个**前置决策模块**,判断当前 query 是否触发检索,以及触发什么类型的检索。它是降低成本、降低延迟、避免无关检索污染答案的关键。

**为什么需要检索门控**:

| 场景 | 是否需要检索 | 原因 |
|------|-------------|------|
| "你好,介绍下自己" | 否 | 闲聊,参数知识足够 |
| "1+1 等于几" | 否 | 简单事实,LLM 已知 |
| "Python 怎么写 for 循环" | 否 | 通用编程知识,LLM 训练数据中有 |
| "2026 年最新的 GPT 模型是什么" | 是 | 时效性信息,需 Web Search |
| "公司 Q3 财报里提到了哪些风险" | 是 | 私有数据,需检索内部知识库 |
| "对比特斯拉和比亚迪 2024 年销量" | 是 | 需要具体数据 + 多跳 |

**门控决策的三种实现方式**:

#### 方式 1: 规则 + 关键词(最轻量)

```python
def rule_based_gate(query: str) -> bool:
    # 闲聊/简单事实 → 不检索
    trivial_patterns = [r"^(hi|hello|你好|谢谢)", r"\d+\s*[\+\-\*/]\s*\d+"]
    for p in trivial_patterns:
        if re.match(p, query, re.I):
            return False
    # 时效性关键词 → 必须检索
    temporal_keywords = ["最新", "今天", "2025", "2026", "recent", "current"]
    if any(k in query.lower() for k in temporal_keywords):
        return True
    # 默认检索
    return True
```

**优点**: 成本极低(无 LLM 调用)、延迟 < 10ms
**缺点**: 覆盖不全、难维护

#### 方式 2: 分类器(平衡)

训练一个小型分类模型(BERT/MiniLM),输入 query,输出 "need_retrieval" / "no_retrieval":

```python
class RetrievalGateClassifier:
    def __init__(self):
        self.model = AutoModelForSequenceClassification.from_pretrained("./gate_model")
        self.tokenizer = AutoTokenizer.from_pretrained("./gate_model")

    def predict(self, query: str) -> tuple[bool, float]:
        inputs = self.tokenizer(query, return_tensors="pt")
        logits = self.model(**inputs).logits
        prob = torch.softmax(logits, dim=-1)[0]
        need = prob[1] > 0.5
        return need, prob[1].item()
```

**训练数据来源**:
- 正例:用户 query + 检索后答案被采纳(隐式反馈)
- 负例:用户 query + 检索后答案被拒绝,或直接用参数知识回答得很好
- 也可用 LLM 合成训练数据

**优点**: 成本低(小模型推理)、可在线学习
**缺点**: 需要训练数据、对新领域泛化弱

#### 方式 3: LLM 判断(最灵活)

让 LLM 直接判断,可结合上下文:

```python
def llm_based_gate(query: str, conversation_history: list) -> tuple[bool, str]:
    prompt = f"""
    Conversation: {conversation_history}
    User query: {query}
    
    Decide if retrieval is needed. Consider:
    1. Is this a casual chat or simple fact LLM already knows?
    2. Is this about recent events or private data?
    3. Does this need citations?
    
    Output JSON: {{"need_retrieval": bool, "reason": str, "retrieval_type": "vector|graph|web|sql"}}
    """
    decision = llm.call(prompt, model="cheap_model")  # 用小模型降本
    return decision["need_retrieval"], decision["retrieval_type"]
```

**优点**: 最灵活、可结合上下文
**缺点**: 多一次 LLM 调用,增加延迟和成本

#### 进阶: 分层门控(推荐生产使用)

```python
class HierarchicalRetrievalGate:
    def decide(self, query, context) -> GateDecision:
        # Layer 1: 规则快筛(0ms)
        if self.rule_gate.is_trivial(query):
            return GateDecision(need=False, reason="trivial")
        
        # Layer 2: 缓存命中检查(1ms)
        cached = self.cache.lookup(query)
        if cached and cached.confidence > 0.9:
            return GateDecision(need=False, reason="cached", answer=cached.answer)
        
        # Layer 3: 分类器(50ms)
        prob = self.classifier.predict(query)
        if prob < 0.2:
            return GateDecision(need=False, reason="low_retrieval_prob")
        
        # Layer 4: LLM 精判(仅模糊情况,200ms)
        if 0.2 <= prob < 0.7:
            return self.llm_gate.decide(query, context)
        
        # 高概率需要检索
        return GateDecision(need=True, source=self.classifier.route(query))
```

**Self-RAG 的门控思路**(论文:Self-RAG, 2023):

Self-RAG 训练 LLM 输出**反思 token**(reflection tokens):
- `[Retrieve]`: 是否需要检索
- `[IsRel]`: 检索文档是否相关
- `[IsSup]`: 答案是否被证据支持
- `[IsUse]`: 答案是否有用

通过这些 token,LLM 自主控制检索行为,实现细粒度门控。

**门控的评估指标**:
- **门控准确率**: 判断"是否需要检索"的正确率
- **成本节省率**: 跳过的检索占比 × 单次检索成本
- **答案质量影响**: 门控导致的答案质量下降幅度(应 < 2%)

**面试加分点**:
1. 强调检索门控是**成本与质量的平衡器**,生产系统必备
2. 提到分层门控:规则 → 缓存 → 分类器 → LLM,逐级增加成本
3. 提到 Self-RAG 的反思 token 机制,展示对前沿工作的了解

</details>

---

### Q6: GraphRAG 与向量 RAG 有什么区别?各自优劣和适用场景?

<details>
<summary>点击查看答案</summary>

**核心区别**: 向量 RAG 基于**语义相似性**检索文档片段;GraphRAG 基于**知识图谱结构**检索实体与关系。前者回答"什么和什么像",后者回答"什么和什么有关系"。

**详细对比表**:

| 维度 | 向量 RAG | GraphRAG |
|------|---------|----------|
| **数据结构** | 高维向量空间 | 图(节点=实体,边=关系) |
| **检索原理** | 余弦相似度 Top-K | 图遍历 + 社区摘要 |
| **擅长问题** | 事实型、语义相似型 | 关系型、多跳型、全局主题型 |
| **多跳能力** | 弱(需多次检索) | 强(图结构天然支持) |
| **全局问题** | 差(只能检索局部片段) | 强(社区摘要覆盖全局) |
| **构建成本** | 低(Embedding 一次) | 高(实体抽取/关系抽取/社区检测,大量 LLM 调用) |
| **更新成本** | 低(增量 Embedding) | 高(新增实体需重新社区检测) |
| **可解释性** | 中(可看检索文档) | 高(推理路径明确) |
| **冷启动** | 快 | 慢(需先构建图谱) |
| **对 LLM 依赖** | 仅生成阶段 | 构图 + 查询都依赖 |
| **典型框架** | LangChain / LlamaIndex | Microsoft GraphRAG / Neo4j |

**适用场景对比**:

**向量 RAG 适用**:
- 问答型:"公司的差旅政策是什么?"
- 语义相似:"找一段讲 RAG 的文档"
- 单跳事实:"Transformer 是哪一年提出的?"
- 大规模文档检索:百万级文档,需快速 Top-K
- 频繁更新:文档经常增删

**GraphRAG 适用**:
- 多跳推理:"A 公司的 CEO 的母校在哪个城市?"
- 关系查询:"X 和 Y 之间有什么关联?"
- 全局主题:"这份 1000 页财报的主要议题有哪些?"
- 实体中心:"所有提到 Elon Musk 的文档,以及他相关的人和公司"
- 跨文档关联:多份文档共同涉及的人物/事件/组织

**经典案例**:

| 问题 | 向量 RAG | GraphRAG | 谁更优 |
|------|---------|----------|--------|
| "什么是 RAG?" | 直接检索到定义段落 | 找到 RAG 实体及关联 | 向量 RAG(简单事实) |
| "RAG 的提出者还提出过什么?" | 难以多跳 | 沿图遍历即可 | GraphRAG |
| "这份文档的主题有哪些?" | 只能采样部分段落 | 遍历社区摘要 | GraphRAG(全局) |
| "找一段讲 GPT 训练的文档" | 语义检索直接命中 | 需先定位实体 | 向量 RAG |

**Microsoft GraphRAG 论文关键发现**(2024):

在 GraphRAG 论文中,对比向量 RAG:
- **全局问题**(如"数据集的主要主题是什么"):GraphRAG 在人类评测中全面胜出,全面性、多样性、赋能性都提升 50%+
- **局部问题**(具体事实):两者相当,向量 RAG 甚至略优(成本低)
- **结论**: GraphRAG 是向量 RAG 的**补充**而非替代

**融合方案: Hybrid RAG(生产推荐)**

```
Query → 路由器
        ├─ 事实型 → 向量 RAG
        ├─ 关系型 → GraphRAG(局部查询)
        ├─ 全局型 → GraphRAG(全局查询)
        └─ 混合型 → 并行两路 + 融合重排
```

**融合重排策略**:
1. 向量检索召回 Top-20 文档片段
2. 图谱检索召回相关实体 + 邻居文档片段
3. 合并去重
4. Cross-Encoder 重排 Top-5
5. 生成

**成本对比示例**(处理 100 万 token 文档):
- 向量 RAG:Embedding 调用 ~$0.1(一次性)
- GraphRAG:实体抽取 + 关系抽取 + 社区摘要 ~$10-50(取决于 LLM 选择)
- **GraphRAG 构图成本约为向量 RAG 的 100-500 倍**

**面试加分点**:
1. 强调"不是替代,是融合"——成熟系统应该 Hybrid
2. 提到 GraphRAG 的全局查询能力是**向量 RAG 的根本性短板**(向量检索无法回答"整个数据集的主题")
3. 提到 GraphRAG 构图成本高,需要权衡文档规模与频率

</details>

---

### Q7: GraphRAG 的图谱构建流程是怎样的?详细说明实体抽取、关系抽取、社区检测(Leiden 算法)

<details>
<summary>点击查看答案</summary>

**GraphRAG 图谱构建总流程**:

```
原始文档 → 切分(Chunking) → 实体抽取 → 关系抽取 → 实体消歧合并 → 社区检测 → 社区摘要 → 索引
```

#### Step 1: 文档切分(Chunking)

与向量 RAG 类似,但 chunk 大小通常更大(如 1200 tokens),因为需要给 LLM 足够上下文抽取实体关系。

```python
chunks = split_documents(docs, chunk_size=1200, overlap=100)
```

#### Step 2: 实体抽取(Entity Extraction)

**目标**: 从每个 chunk 中识别实体(人/组织/地点/概念等)。

**两种主流方法**:

**方法 A: 传统 NER(轻量)**
```python
def ner_extract(text):
    entities = spacy_ner(text)  # 用 spaCy 等 NER 工具
    return [{"name": e.text, "type": e.label_, "span": e.start} for e in entities]
```
- 优点:快、便宜
- 缺点:只能识别预定义类型(PERSON/ORG/GPE),无法抽取概念性实体

**方法 B: LLM 抽取(灵活,Microsoft GraphRAG 使用)**

```python
ENTITY_PROMPT = """
You are an entity extractor. From the text below, extract all entities.
For each entity, output:
- entity_name: canonical name
- entity_type: [organization|person|geo|event|concept]
- entity_description: brief description from context

Text: {chunk_text}

Output as JSON list.
"""

def llm_extract_entities(chunk):
    return llm.call(ENTITY_PROMPT.format(chunk_text=chunk), response_format="json")
```

- 优点:能抽取概念性实体(如"RAG"、"检索增强生成"),描述丰富
- 缺点:贵(每个 chunk 一次 LLM 调用)、可能不一致

**Microsoft GraphRAG 的抽取策略**:
- 使用 GPT-4 级模型确保抽取质量
- Prompt 中包含 few-shot 示例
- 支持自定义实体类型(领域适配)

#### Step 3: 关系抽取(Relation Extraction)

**目标**: 识别实体对之间的关系。

```python
RELATION_PROMPT = """
Given the text and the extracted entities, identify relationships between entity pairs.
For each relationship, output:
- source_entity: name
- target_entity: name
- relation_type: brief description (e.g., "CEO of", "acquired by", "located in")
- relation_strength: 1-10 (how strongly supported by text)
- evidence: the supporting sentence

Text: {chunk_text}
Entities: {entities}

Output as JSON list.
"""

def llm_extract_relations(chunk, entities):
    return llm.call(RELATION_PROMPT.format(chunk_text=chunk, entities=entities))
```

**关键细节**:
- **共现关系**: 同一 chunk 中的实体更可能有关系(GraphRAG 假设)
- **关系强度**: 不是所有关系同等重要,需打分
- **证据追溯**: 保留支持句,便于审计

#### Step 4: 实体消歧与合并(Entity Resolution)

**问题**: 同一实体在不同 chunk 中可能有不同写法:
- "Elon Musk" / "Musk" / "埃隆·马斯克" / "Tesla CEO"
- "OpenAI" / "OpenAI Inc" / "OpenAI, Inc."

**解决方案**:

```python
def entity_resolution(entities: list[Entity]) -> list[Entity]:
    # 1. 嵌入聚类
    embeddings = [embed(e.name + " " + e.description) for e in entities]
    clusters = cluster(embeddings, threshold=0.85)  # 余弦相似度聚类
    
    # 2. LLM 精判合并
    merged = []
    for cluster in clusters:
        if len(cluster) == 1:
            merged.append(cluster[0])
        else:
            canonical = llm.canonicalize(cluster)  # 选最规范的名称
            merged.append(canonical)
    return merged
```

**进阶**: Microsoft GraphRAG 还支持**实体摘要**——把同一实体的多个描述合并为一段统一描述。

#### Step 5: 社区检测(Community Detection)— Leiden 算法

**目标**: 把图中紧密关联的实体聚成"社区",每个社区代表一个主题/子领域。这是 GraphRAG 支持全局查询的关键。

**为什么需要社区**:
- 直接遍历全图不现实(百万节点)
- 社区形成层次结构,顶层社区摘要可回答"全局主题"

**Leiden 算法详解**:

Leiden 是 Louvain 的改进版,用于**模块度最大化**的层次化社区检测。

**模块度 Q(Modularity)定义**:

$$Q = \frac{1}{2m} \sum_{ij} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

其中:
- $A_{ij}$:邻接矩阵(节点 i,j 之间的边权)
- $k_i$:节点 i 的度数
- $m$:总边数
- $\delta(c_i, c_j)$:若 i,j 同社区则为 1,否则 0

直观理解:Q 衡量"社区内边数"相对"随机图期望边数"的偏离,越大说明社区结构越显著。

**Louvain 算法的三阶段**(Leiden 的基础):
1. **局部优化**: 每个节点尝试加入邻居所在社区,使 Q 最大化
2. **社区聚合**: 把每个社区缩成一个超级节点,边权为社区间边之和
3. **迭代**: 重复 1-2 直到 Q 不再提升

**Louvain 的问题**: 可能产生**断开的社区**(社区内某些节点之间无路径),称为"badly connected communities"。

**Leiden 的改进**: 在 Louvain 基础上增加一个**细化阶段(Refinement)**:
1. 局部优化(同 Louvain)
2. **社区细化**: 拆分社区为更小的连通子社区,确保每个社区是连通的
3. 社区聚合(同 Louvain)
4. 迭代

**Leiden 的优势**:
- 保证社区连通性
- 收敛更快
- 社区质量更高(模块度略优)
- 支持层次化聚类(多层级社区树)

**Python 实现(igraph)**:

```python
from igraph import Graph
import leidenalg

def detect_communities(entities, relations):
    # 构建图
    g = Graph()
    g.add_vertices([e.name for e in entities])
    for r in relations:
        g.add_edge(r.source, r.target, weight=r.strength)
    
    # Leiden 算法,层次化聚类
    partition = leidenalg.find_partition(
        g,
        leidenalg.RBConfigurationVertexPartition,
        resolution_parameter=1.0,
        n_iterations=10
    )
    
    # 层次化输出
    hierarchical = leidenalg.find_partition_hierarchy(g, leidenalg.RBConfigurationVertexPartition)
    return partition, hierarchical
```

**层次化社区示例**:

```
Level 0(顶层):{所有实体} - 1个大社区
Level 1:{科技, 金融, 政治} - 3个社区
Level 2:{科技.AI, 科技.硬件, 金融.银行, ...} - 12个社区
Level 3:{科技.AI.RAG, 科技.AI.LLM, ...} - 50个社区
```

#### Step 6: 社区摘要(Community Summarization)

**目标**: 给每个社区生成一段 LLM 摘要,用于全局查询时无需遍历实体。

```python
def summarize_community(community_id, entities, relations):
    members = [e for e in entities if e.community == community_id]
    internal_relations = [r for r in relations 
                          if r.source.community == community_id 
                          and r.target.community == community_id]
    
    prompt = f"""
    Summarize this community of entities and their relationships.
    Focus on: key themes, main entities, notable relationships.
    
    Entities: {members}
    Relations: {internal_relations}
    """
    return llm.call(prompt)
```

**层次化摘要**: 从最底层社区开始摘要,逐层向上,父社区摘要基于子社区摘要生成(节省 token)。

#### Step 7: 索引构建

构建三类索引:
1. **实体索引**: name → entity_id, description, community_id
2. **关系索引**: (source, target) → relation_type, strength
3. **社区摘要索引**: community_id → summary, level, member_entities

**完整流程成本估算**(100 万 token 文档):
- 切分:~830 个 chunks(1200 token/chunk)
- 实体抽取:830 次 LLM 调用 ≈ $5(GPT-4-mini)
- 关系抽取:830 次 LLM 调用 ≈ $8
- 社区摘要:50-200 次 LLM 调用 ≈ $3
- **总计**: ~$15-20(GPT-4-mini),~$100-200(GPT-4)

**面试加分点**:
1. 强调 Leiden 优于 Louvain 的关键点是**保证社区连通性**
2. 提到层次化社区是支持全局查询的基础
3. 提到构图成本是 GraphRAG 落地的主要障碍,可通过小模型/批量推理降低

</details>

---

### Q8: GraphRAG 的局部查询和全局查询有何区别?Microsoft GraphRAG 框架是如何实现的?

<details>
<summary>点击查看答案</summary>

**局部查询 vs 全局查询**:

| 维度 | 局部查询(Local Search) | 全局查询(Global Search) |
|------|----------------------|----------------------|
| **问题类型** | 具体实体相关问题 | 全局主题/概览类问题 |
| **示例** | "Elon Musk 关联的公司有哪些?" | "这份财报讨论了哪些主要主题?" |
| **检索范围** | 从种子实体出发,扩展邻居 | 遍历所有社区摘要 |
| **算法** | 图遍历(BFS/DFS)+ 实体上下文 | Map-Reduce 聚合社区摘要 |
| **延迟** | 低(局部遍历) | 中(Map-Reduce 多轮) |
| **依赖** | 实体索引 + 关系索引 | 社区摘要索引 |
| **典型层级** | 叶子社区(Level 3) | 顶层社区(Level 0-1) |

#### 局部查询(Local Search)详解

**流程**:
1. **实体识别**: 从 query 中识别种子实体(可用 NER 或 LLM)
2. **图扩展**: 从种子实体出发,BFS 扩展到 N 跳邻居
3. **上下文组装**: 收集相关实体、关系、社区摘要、原始文档片段
4. **生成**: 把组装的上下文喂给 LLM 生成答案

```python
def local_search(query: str, graph: Graph, max_hops: int = 2) -> str:
    # Step 1: 识别种子实体
    seed_entities = llm.extract_entities_from_query(query)
    
    # Step 2: 图遍历
    context_entities = set()
    context_relations = []
    context_chunks = []
    for seed in seed_entities:
        neighbors = graph.bfs(seed, max_hops=max_hops)
        context_entities.update(neighbors)
        context_relations.extend(graph.relations_in_subgraph(neighbors))
        context_chunks.extend(graph.chunks_mentioning(neighbors))
    
    # Step 3: 组装上下文(优先级排序)
    context = prioritize_and_truncate(
        entities=context_entities,
        relations=context_relations,
        chunks=context_chunks,
        max_tokens=4000
    )
    
    # Step 4: 生成
    return llm.generate(query, context)
```

**Microsoft GraphRAG 局部查询特点**:
- 上下文包含 5 类信息:实体描述、关系描述、声明(原文片段)、社区摘要、原始 chunks
- 用**token budget**机制控制每类信息的占比
- 优先级:种子实体 > 一跳邻居 > 二跳邻居

#### 全局查询(Global Search)详解

**问题**: "整个数据集的主题是什么?" 这类问题无法通过局部遍历回答,需要综合所有信息。

**流程(Map-Reduce)**:
1. **Map 阶段**: 对每个社区摘要,让 LLM 生成多个候选答案片段(带分值)
2. **Reduce 阶段**: 聚合所有候选片段,生成最终答案

```python
def global_search(query: str, community_summaries: list[str], level: int = 0) -> str:
    # 只用顶层社区的摘要
    top_level = [c for c in community_summaries if c.level == level]
    
    # Map: 每个社区并行生成候选答案
    candidates = []
    with ThreadPoolExecutor() as executor:
        futures = {
            c.id: executor.submit(
                llm.generate_partial,
                query,
                c.summary,
                prompt=PARTIAL_ANSWER_PROMPT
            )
            for c in top_level
        }
        for cid, fut in futures.items():
            partial = fut.result()
            # partial 包含多个 key points,每个带分值
            candidates.extend(partial.key_points)
    
    # Reduce: 聚合所有 key points
    ranked = sorted(candidates, key=lambda x: x.score, reverse=True)[:50]
    final = llm.synthesize(query, ranked)
    return final
```

**Partial Answer Prompt 示例(Microsoft GraphRAG)**:

```
You are an analyst. Based on the community report below, answer the user question.
Generate 1-5 key points. Each point should include:
- description: the key point
- score: 0-100, how relevant and important

Community Report: {summary}
Question: {query}

Output JSON: {{"points": [{{"description": str, "score": int}}]}}
```

**为什么用 Map-Reduce 而非直接拼接**:
- 上下文长度限制:几百个社区摘要可能超 100k token
- Map-Reduce 让每个社区独立贡献,再聚合,避免注意力稀释
- 每个社区的"分值"用于排序,过滤低贡献内容

#### Microsoft GraphRAG 框架详解

**GitHub**: github.com/microsoft/graphrag(2024 开源)

**架构**:

```
┌─────────────────────────────────────┐
│           Indexing Pipeline          │
│  Docs → Chunks → Entities → Relations│
│       → Communities → Summaries      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│           Query Engine               │
│  ┌─────────┐  ┌──────────────────┐  │
│  │ Local   │  │ Global           │  │
│  │ Search  │  │ Search(MapReduce)│  │
│  └─────────┘  └──────────────────┘  │
└─────────────────────────────────────┘
```

**关键配置参数**:

```yaml
# settings.yaml(Microsoft GraphRAG)
chunks:
  size: 1200
  overlap: 100

entity_extraction:
  model: gpt-4o-mini
  prompt: prompts/entity_extraction.txt
  max_entities_per_chunk: 50

community_detection:
  algorithm: leiden
  resolution: 1.0
  max_levels: 5

community_summarization:
  model: gpt-4o-mini
  max_tokens: 1500

query:
  local:
    max_tokens: 4000
    include_chunks: true
  global:
    level: 0  # 用哪一层社区
    max_tokens: 8000
```

**命令行使用**:

```bash
# 构建索引
python -m graphrag.index --root ./my_project --method standard

# 局部查询
python -m graphrag.query --method local --query "Elon Musk 的公司有哪些?"

# 全局查询
python -m graphrag.query --method global --query "数据集的主要主题?"
```

**性能数据**(Microsoft 论文,100 篇新闻文档):
- 局部查询延迟:3-5 秒
- 全局查询延迟:15-30 秒(Map-Reduce 多次 LLM 调用)
- 全局查询在"全面性"(comprehensiveness)指标上击败向量 RAG 70-80%
- 构图成本:~$5(GPT-4o-mini)

#### 局部 vs 全局如何选择

**自动路由(推荐)**:

```python
def graphrag_router(query: str) -> str:
    intent = llm.classify(query, labels=["entity_specific", "global_theme"])
    if intent == "entity_specific":
        return local_search(query, graph)
    else:
        return global_search(query, community_summaries)
```

**判断标准**:
- query 中有具体实体名 → 局部
- query 是"主要主题/概览/总结"类 → 全局
- 不确定 → 默认局部(更便宜)

**面试加分点**:
1. 强调全局查询的 Map-Reduce 模式是为了**绕过上下文长度限制**
2. 提到层次化社区让用户可以选择查询层级(level 0 最粗,level 3 最细)
3. 提到 Microsoft GraphRAG 的开源实现是当前最成熟的 GraphRAG 框架
4. 提到局部查询和全局查询的**自动路由**是生产落地的关键设计

</details>

---

### Q9: 手撕代码 — 实现一个 Agentic RAG 系统(支持检索路由、迭代检索、多跳推理、结果评估)

<details>
<summary>点击查看完整代码</summary>

下面是一个完整的 Agentic RAG 系统实现,使用 mock 函数模拟 LLM 和检索器,可直接运行。

```python
"""
Agentic RAG 完整实现
支持:检索路由、查询构造、结果评估、迭代检索、多跳推理、检索门控
依赖:无(全部 mock),实际使用时替换 llm_call / retrieve_xxx 即可
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable
import re
import hashlib
import time


# ============================================================
# Part 1: 数据结构定义
# ============================================================

class RouteType(Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    WEB = "web"
    SQL = "sql"
    NONE = "none"  # 不需要检索


class AgentAction(Enum):
    RETRIEVE = "retrieve"
    GENERATE = "generate"
    REWRITE_QUERY = "rewrite_query"
    DECOMPOSE = "decompose"
    MULTI_HOP = "multi_hop"
    FINISH = "finish"


@dataclass
class Document:
    """检索返回的文档片段"""
    content: str
    source: str
    score: float = 0.0
    metadata: dict = field(default_factory=dict)


@dataclass
class EvalResult:
    """结果评估"""
    relevant_docs: list  # Document
    sufficient: bool  # 是否充分
    confidence: float  # 置信度 0-1
    gap: Optional[str]  # 信息缺口描述
    conflicts: list  # 矛盾点


@dataclass
class HopStep:
    """多跳推理中的一跳"""
    hop: int
    query: str
    docs: list  # Document
    partial_answer: str
    confidence: float


@dataclass
class AgentState:
    """Agent 的全局状态(状态机视角)"""
    original_question: str
    current_query: str
    evidence: list = field(default_factory=list)  # 累积证据 Document
    iterations: int = 0
    max_iterations: int = 5
    hop_chain: list = field(default_factory=list)  # HopStep
    history_queries: list = field(default_factory=list)  # 防重复
    confidence_history: list = field(default_factory=float)
    route: RouteType = RouteType.VECTOR
    done: bool = False
    final_answer: Optional[str] = None
    trace: list = field(default_factory=list)  # 调试轨迹


# ============================================================
# Part 2: Mock 函数(实际使用时替换为真实实现)
# ============================================================

def llm_call(prompt: str, model: str = "gpt-4o-mini") -> str:
    """Mock LLM 调用。实际替换为 OpenAI/Anthropic/本地模型调用。"""
    # 这里用简单规则模拟,实际应调用真实 LLM
    prompt_lower = prompt.lower()
    if "classify intent" in prompt_lower:
        if any(k in prompt_lower for k in ["最新", "今天", "2025", "2026"]):
            return "temporal"
        if any(k in prompt_lower for k in ["关系", "关联", "连接", "ceo"]):
            return "relational"
        if any(k in prompt_lower for k in ["多少", "销量", "收入"]):
            return "numerical"
        return "factual"
    if "rewrite query" in prompt_lower:
        return "apple inc quarterly earnings 2026 financial report"
    if "decompose" in prompt_lower:
        return "What is RAG?\n|||What is GraphRAG?\n|||How do they compare?"
    if "sufficient" in prompt_lower:
        return "YES" if len(prompt) > 500 else "NO"
    if "gap" in prompt_lower:
        return "Need more info on GraphRAG performance metrics"
    if "extract partial" in prompt_lower:
        return "Based on evidence, partial answer: Tesla CEO is Elon Musk."
    if "next hop" in prompt_lower:
        return "DONE" if "musk" in prompt_lower else "What did Elon Musk acquire in 2024?"
    if "synthesize" in prompt_lower:
        return "Based on retrieved evidence, here is the synthesized answer."
    if "need retrieval" in prompt_lower:
        return '{"need_retrieval": true, "reason": "factual query needs grounding"}'
    return f"[Mock LLM response for prompt: {prompt[:80]}...]"


def embed(text: str) -> list:
    """Mock embedding。实际用 sentence-transformers / OpenAI embedding。"""
    # 简单 hash 模拟向量
    h = hashlib.md5(text.encode()).digest()
    return [b / 255 for b in h[:16]]


def cosine_sim(a: list, b: list) -> float:
    """余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb + 1e-8)


def retrieve_vector(query: str, k: int = 5) -> list:
    """Mock 向量检索"""
    return [
        Document(content=f"Vector doc {i} for: {query}", source="vector_db",
                 score=0.9 - i * 0.1)
        for i in range(k)
    ]


def retrieve_graph(query: str, hops: int = 2) -> list:
    """Mock 图谱检索"""
    return [
        Document(content=f"Graph entity {i} related to: {query}",
                 source="graph_db", score=0.85 - i * 0.1)
        for i in range(3)
    ]


def retrieve_web(query: str) -> list:
    """Mock Web 检索"""
    return [Document(content=f"Web result for: {query}",
                     source="web_search", score=0.7)]


def retrieve_sql(query: str) -> list:
    """Mock SQL 检索"""
    return [Document(content=f"SQL query result for: {query}",
                     source="sql_db", score=0.8)]


def cross_encoder_score(query: str, doc: Document) -> float:
    """Mock 交叉编码器重排"""
    # 实际用 BGE-Reranker / Cohere Rerank
    return doc.score * 0.9 + 0.1 * (len(doc.content) % 10) / 10


# ============================================================
# Part 3: 检索门控(Retrieval Gating)
# ============================================================

class RetrievalGate:
    """分层检索门控:规则 → 分类器 → LLM"""

    def __init__(self):
        self.trivial_patterns = [
            r"^(hi|hello|你好|嘿|hey|thanks|谢谢)",
            r"\d+\s*[\+\-\*/]\s*\d+\s*=\s*\?",
        ]

    def is_trivial(self, query: str) -> bool:
        for p in self.trivial_patterns:
            if re.match(p, query, re.I):
                return True
        return False

    def decide(self, query: str) -> tuple[bool, str]:
        # Layer 1: 规则
        if self.is_trivial(query):
            return False, "trivial_query"
        # Layer 2: 简单启发式
        if len(query) < 5:
            return False, "too_short"
        # Layer 3: LLM 精判(实际用小模型降本)
        decision = llm_call(f"need retrieval? query: {query}")
        return "true" in decision.lower(), "llm_decision"


# ============================================================
# Part 4: 检索路由(Retrieval Routing)
# ============================================================

class RetrievalRouter:
    """根据 query 意图路由到不同数据源"""

    ROUTING_MAP = {
        "factual": RouteType.VECTOR,
        "relational": RouteType.GRAPH,
        "temporal": RouteType.WEB,
        "numerical": RouteType.SQL,
    }

    def route(self, query: str) -> RouteType:
        intent = llm_call(f"classify intent: {query}")
        return self.ROUTING_MAP.get(intent, RouteType.VECTOR)

    def retrieve(self, query: str, route: RouteType, k: int = 5) -> list:
        if route == RouteType.VECTOR:
            return retrieve_vector(query, k)
        elif route == RouteType.GRAPH:
            return retrieve_graph(query)
        elif route == RouteType.WEB:
            return retrieve_web(query)
        elif route == RouteType.SQL:
            return retrieve_sql(query)
        return []


# ============================================================
# Part 5: 查询构造(Query Construction)
# ============================================================

class QueryConstructor:
    """Query Rewriting + Sub-query Decomposition + HyDE"""

    def rewrite(self, query: str) -> str:
        return llm_call(f"rewrite query for better retrieval: {query}")

    def decompose(self, query: str) -> list:
        result = llm_call(f"decompose into sub-queries, separate by |||: {query}")
        return [q.strip() for q in result.split("|||") if q.strip()]

    def hyde(self, query: str) -> str:
        """Hypothetical Document Embedding: 先生成假设答案,用答案检索"""
        hyp_doc = llm_call(f"Generate a hypothetical passage answering: {query}")
        return hyp_doc


# ============================================================
# Part 6: 结果评估(Result Evaluation)
# ============================================================

class ResultEvaluator:
    """相关性 + 充分性 + 矛盾检测"""

    def evaluate(self, query: str, docs: list, accumulated: list) -> EvalResult:
        # 1. 相关性过滤(交叉编码器)
        scored = [(d, cross_encoder_score(query, d)) for d in docs]
        relevant = [d for d, s in scored if s > 0.5]

        # 2. 充分性判断
        all_evidence = accumulated + relevant
        evidence_text = " ".join(d.content for d in all_evidence)
        sufficient_resp = llm_call(
            f"Is evidence sufficient to answer: {query}? Evidence: {evidence_text[:500]}"
        )
        sufficient = "yes" in sufficient_resp.lower()

        # 3. 置信度估计(基于证据数量 + 平均分数)
        if all_evidence:
            confidence = min(1.0, len(all_evidence) * 0.2 +
                             sum(d.score for d in all_evidence) / len(all_evidence) * 0.5)
        else:
            confidence = 0.1

        # 4. 信息缺口
        gap = None if sufficient else llm_call(
            f"What information is missing to answer: {query}? Current evidence: {evidence_text[:300]}"
        )

        return EvalResult(
            relevant_docs=relevant,
            sufficient=sufficient,
            confidence=confidence,
            gap=gap,
            conflicts=[]
        )


# ============================================================
# Part 7: 多跳推理(Multi-hop Reasoning)
# ============================================================

class MultiHopReasoner:
    """链式多跳推理"""

    def __init__(self, router: RetrievalRouter, evaluator: ResultEvaluator, max_hops: int = 4):
        self.router = router
        self.evaluator = evaluator
        self.max_hops = max_hops

    def reason(self, question: str, state: AgentState) -> tuple[str, list]:
        chain = []
        current_query = question
        for hop in range(self.max_hops):
            # 检索
            route = self.router.route(current_query)
            docs = self.router.retrieve(current_query, route)
            # 提取部分答案
            partial = llm_call(
                f"extract partial answer. Question: {question}\n"
                f"Docs: {[d.content for d in docs]}\n"
                f"Previous: {chain}"
            )
            # 评估置信度
            eval_result = self.evaluator.evaluate(question, docs, [d for s in chain for d in s.docs])
            step = HopStep(
                hop=hop, query=current_query, docs=docs,
                partial_answer=partial, confidence=eval_result.confidence
            )
            chain.append(step)
            state.trace.append(f"Multi-hop {hop}: query={current_query[:50]}, conf={eval_result.confidence:.2f}")

            # 生成下一跳 query
            next_q = llm_call(
                f"next hop query? Question: {question}\nChain so far: {chain}. "
                f"If done, return 'DONE'."
            )
            if next_q.strip().upper() == "DONE":
                break
            current_query = next_q

        # 合成最终答案
        final = llm_call(
            f"synthesize final answer. Question: {question}\nReasoning chain: {chain}"
        )
        return final, chain


# ============================================================
# Part 8: Agentic RAG 主类(状态机编排)
# ============================================================

class AgenticRAG:
    """
    完整的 Agentic RAG 系统
    状态机:gate → route → retrieve → evaluate → (iterate / multi-hop) → generate
    """

    def __init__(self,
                 max_iterations: int = 5,
                 confidence_threshold: float = 0.85,
                 duplicate_threshold: float = 0.9,
                 convergence_delta: float = 0.02):
        self.gate = RetrievalGate()
        self.router = RetrievalRouter()
        self.constructor = QueryConstructor()
        self.evaluator = ResultEvaluator()
        self.reasoner = MultiHopReasoner(self.router, self.evaluator)

        self.max_iter = max_iterations
        self.conf_thresh = confidence_threshold
        self.dup_thresh = duplicate_threshold
        self.conv_delta = convergence_delta

    def run(self, question: str) -> tuple[str, AgentState]:
        # 初始化状态
        state = AgentState(
            original_question=question,
            current_query=question,
            max_iterations=self.max_iter,
        )

        # Step 0: 检索门控
        need_retrieval, reason = self.gate.decide(question)
        state.trace.append(f"Gate: need={need_retrieval}, reason={reason}")
        if not need_retrieval:
            state.final_answer = llm_call(f"Answer directly from param knowledge: {question}")
            state.done = True
            return state.final_answer, state

        # Step 1: 路由
        state.route = self.router.route(question)
        state.trace.append(f"Route: {state.route.value}")

        # Step 2: 多跳场景识别(relational → 多跳)
        if state.route == RouteType.GRAPH:
            answer, chain = self.reasoner.reason(question, state)
            state.final_answer = answer
            state.hop_chain = chain
            state.done = True
            return answer, state

        # Step 3: 迭代检索循环
        while not state.done and state.iterations < self.max_iter:
            # 3.1 查询构造(首轮原问题,后续基于缺口)
            if state.iterations == 0:
                query = self.constructor.rewrite(question)
            else:
                gap = self.evaluator.evaluate(question, [], state.evidence).gap
                if gap is None:
                    break
                query = llm_call(f"Generate query to fill gap: {gap}")

            # 3.2 防重复 query
            if self._is_duplicate(query, state.history_queries):
                state.trace.append(f"Iter {state.iterations}: duplicate query, stopping")
                break
            state.history_queries.append(query)
            state.current_query = query

            # 3.3 检索
            docs = self.router.retrieve(query, state.route)
            state.trace.append(f"Iter {state.iterations}: retrieved {len(docs)} docs for '{query[:50]}'")

            # 3.4 评估
            eval_result = self.evaluator.evaluate(question, docs, state.evidence)
            state.evidence.extend(eval_result.relevant_docs)
            state.confidence_history.append(eval_result.confidence)
            state.trace.append(
                f"Iter {state.iterations}: conf={eval_result.confidence:.2f}, "
                f"sufficient={eval_result.sufficient}"
            )

            # 3.5 终止判断
            if eval_result.sufficient and eval_result.confidence >= self.conf_thresh:
                state.done = True
                break
            # 3.6 收敛判断
            if self._is_converged(state):
                state.trace.append(f"Iter {state.iterations}: converged, stopping")
                break

            state.iterations += 1

        # Step 4: 生成最终答案
        evidence_text = "\n".join(d.content for d in state.evidence)
        state.final_answer = llm_call(
            f"synthesize final answer. Question: {question}\nEvidence: {evidence_text[:1000]}"
        )
        state.done = True
        return state.final_answer, state

    def _is_duplicate(self, query: str, history: list) -> bool:
        if not history:
            return False
        q_emb = embed(query)
        for h in history:
            if cosine_sim(q_emb, embed(h)) > self.dup_thresh:
                return True
        return False

    def _is_converged(self, state: AgentState) -> bool:
        if len(state.confidence_history) < 2:
            return False
        delta = abs(state.confidence_history[-1] - state.confidence_history[-2])
        return delta < self.conv_delta


# ============================================================
# Part 9: 测试 & 演示
# ============================================================

def demo():
    """演示 Agentic RAG 运行"""
    rag = AgenticRAG(max_iterations=5, confidence_threshold=0.85)

    test_cases = [
        "你好,介绍下自己",  # 闲聊 → 门控拒绝
        "Tesla CEO 在 2024 年收购的公司的总部在哪?",  # 多跳
        "对比 RAG 和 GraphRAG 在多跳问答上的表现",  # 迭代检索
        "2026 年最新的 GPT 模型是什么",  # Web 检索
    ]

    for q in test_cases:
        print(f"\n{'='*70}")
        print(f"Question: {q}")
        print(f"{'='*70}")
        start = time.time()
        answer, state = rag.run(q)
        elapsed = time.time() - start

        print(f"Answer: {answer}")
        print(f"Route: {state.route.value}")
        print(f"Iterations: {state.iterations}")
        print(f"Hops: {len(state.hop_chain)}")
        print(f"Evidence count: {len(state.evidence)}")
        print(f"Time: {elapsed:.2f}s")
        print(f"Trace:")
        for t in state.trace:
            print(f"  - {t}")


if __name__ == "__main__":
    demo()
```

**代码要点说明**:

1. **状态机视角**: `AgentState` 集中管理所有状态,符合 LangGraph 的设计哲学
2. **分层门控**: 规则 → 启发式 → LLM,逐层降本
3. **路由分发**: 不同意图走不同数据源,relational 自动触发多跳
4. **迭代终止**: 四道防线——最大迭代数 + 重复 query + 置信度 + 收敛
5. **多跳推理**: 链式实现,每跳记录 HopStep 便于可解释
6. **可观测性**: `state.trace` 完整记录决策轨迹,便于调试
7. **mock 友好**: 所有外部依赖(LLM/检索器)都是 mock,易替换为真实实现

**面试讲解要点**:
- 强调"状态机"思维,而非"线性流程"
- 强调"多层防无限循环"机制
- 强调"可观测性"——trace 是生产调试的关键
- 提到生产实现会用 LangGraph 替代手写状态机

</details>

---

### Q10: 系统设计题 — 设计一个研究助手系统,结合 Agentic RAG 和 GraphRAG

<details>
<summary>点击查看系统设计方案</summary>

**题目**: 设计一个"AI 研究助手"系统,帮助研究人员从海量论文、内部文档、Web 资源中快速完成文献综述、关系挖掘、趋势分析。系统需要:
1. 支持自然语言提问
2. 能处理多跳推理("A 论文作者还和谁合作过?")
3. 能回答全局性问题("2025 年 LLM Agent 领域的主要研究方向?")
4. 提供引用追溯
5. 支持增量更新(新论文每天加入)

请给出系统架构、关键模块、数据流、技术选型、容量估算、降级方案。

---

## 一、系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                         用户层                                 │
│   Web UI  /  IDE 插件  /  API  /  Slack Bot                    │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                    API Gateway                                 │
│   鉴权 / 限流 / 请求路由 / 用量计量                              │
└──────────────────────────┬───────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                 Agentic RAG Orchestrator                       │
│   (LangGraph 状态机,核心决策中枢)                              │
│                                                               │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│   │ 检索门控  │→│ 意图分类  │→│ 路由决策  │→│ 查询构造  │    │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│         │                                       │            │
│         ▼                                       ▼            │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│   │ 检索执行  │→│ 结果评估  │→│ 迭代决策  │→│ 答案合成  │    │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────┬───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Vector RAG  │  │  GraphRAG    │  │  Web Search  │
│              │  │              │  │              │
│ • 向量库      │  │ • 图数据库    │  │ • Search API │
│ • 语义检索    │  │ • 局部/全局   │  │ • 时效信息   │
│ • 单跳事实    │  │ • 多跳/主题   │  │ • 外部知识   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────────────────────────────────────────────────────┐
│                       数据层                                   │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│   │ 论文库    │  │ 实体关系图 │  │ 社区摘要  │  │ 引用网络  │    │
│   │ (Milvus) │  │ (Neo4j)   │  │ (Redis)  │  │ (Neo4j)  │    │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                  离线 Indexing Pipeline                        │
│   论文抓取 → PDF 解析 → 切分 → Embedding → 实体抽取            │
│   → 关系抽取 → 社区检测(Leiden) → 社区摘要 → 入库              │
└──────────────────────────────────────────────────────────────┘
```

## 二、关键模块设计

### 模块 1: Agentic RAG Orchestrator(LangGraph 状态机)

**职责**: 决策中枢,编排检索-评估-迭代循环。

**状态机定义**:

```python
from langgraph.graph import StateGraph, END

class ResearchState(TypedDict):
    question: str
    intent: str  # factual / relational / global / temporal
    route: str  # vector / graph_local / graph_global / web / hybrid
    query: str  # 当前查询(可能被改写)
    evidence: list[Document]
    iterations: int
    confidence: float
    answer: str
    citations: list[Citation]
    trace: list[str]

# 节点
def gate_node(state): ...      # 检索门控
def classify_node(state): ...  # 意图分类
def route_node(state): ...     # 路由决策
def construct_node(state): ... # 查询构造
def retrieve_node(state): ...  # 执行检索
def evaluate_node(state): ...  # 结果评估
def decide_node(state): ...    # 迭代决策
def synthesize_node(state): ...# 答案合成

# 图
workflow = StateGraph(ResearchState)
workflow.add_node("gate", gate_node)
workflow.add_node("classify", classify_node)
workflow.add_node("route", route_node)
workflow.add_node("construct", construct_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("decide", decide_node)
workflow.add_node("synthesize", synthesize_node)

workflow.set_entry_point("gate")
workflow.add_edge("gate", "classify")
workflow.add_edge("classify", "route")
workflow.add_edge("route", "construct")
workflow.add_edge("construct", "retrieve")
workflow.add_edge("retrieve", "evaluate")
workflow.add_edge("evaluate", "decide")
# 条件边:decide 决定迭代 or 合成
workflow.add_conditional_edges(
    "decide",
    lambda s: "retrieve" if s["iterations"] < 5 and s["confidence"] < 0.85 else "synthesize",
    {"retrieve": "construct", "synthesize": "synthesize"}
)
workflow.add_edge("synthesize", END)

graph = workflow.compile()
```

### 模块 2: 检索路由策略

```python
class ResearchRouter:
    def route(self, question: str) -> str:
        intent = llm.classify(question, labels=[
            "factual",        # 事实型 → 向量
            "relational",     # 关系型 → GraphRAG 局部
            "global",         # 全局主题 → GraphRAG 全局
            "temporal",       # 时效型 → Web
            "hybrid"          # 混合 → 多源融合
        ])
        return {
            "factual": "vector",
            "relational": "graph_local",
            "global": "graph_global",
            "temporal": "web",
            "hybrid": "hybrid"
        }[intent]

    def hybrid_retrieve(self, question: str) -> list:
        """混合检索:并行向量 + 图谱,融合重排"""
        with ThreadPoolExecutor() as ex:
            vec_future = ex.submit(vector_search, question, k=20)
            graph_future = ex.submit(graph_local_search, question)
        vec_docs = vec_future.result()
        graph_docs = graph_future.result()
        # 融合去重 + Cross-Encoder 重排
        merged = dedup(vec_docs + graph_docs)
        reranked = cross_encoder.rerank(question, merged, top_k=10)
        return reranked
```

### 模块 3: GraphRAG 索引流水线(离线)

```python
class GraphRAGIndexer:
    def __init__(self):
        self.entity_extractor = EntityExtractor(model="gpt-4o-mini")
        self.relation_extractor = RelationExtractor(model="gpt-4o-mini")
        self.community_detector = CommunityDetector(algorithm="leiden")
        self.summarizer = CommunitySummarizer(model="gpt-4o-mini")

    def index(self, papers: list[Paper]):
        # 1. PDF 解析 + 切分
        chunks = []
        for p in papers:
            text = pdf_parser.extract(p.path)
            chunks.extend(split(text, chunk_size=1200, overlap=100))

        # 2. 实体抽取(并行)
        entities = parallel_map(self.entity_extractor.extract, chunks, workers=20)

        # 3. 关系抽取
        relations = parallel_map(
            lambda c, e: self.relation_extractor.extract(c, e),
            zip(chunks, entities), workers=20
        )

        # 4. 实体消歧
        entities = entity_resolution(flatten(entities))

        # 5. 构建图
        graph = build_graph(entities, flatten(relations))

        # 6. 社区检测(层次化 Leiden)
        communities = self.community_detector.detect(graph, max_levels=5)

        # 7. 社区摘要(从叶子层向上)
        summaries = self.summarizer.summarize_hierarchical(graph, communities)

        # 8. 入库
        self.vector_store.upsert(chunks)
        self.graph_store.upsert(graph)
        self.summary_store.upsert(summaries)

    def incremental_update(self, new_papers: list[Paper]):
        """增量更新:新论文入库,局部重新社区检测"""
        # 1. 抽取新实体/关系
        new_entities, new_relations = self.extract(new_papers)
        # 2. 合并到已有图
        self.graph_store.merge(new_entities, new_relations)
        # 3. 只对受影响社区重新检测(局部更新)
        affected = self.find_affected_communities(new_entities)
        self.community_detector.redetect(affected)
        # 4. 重新生成受影响社区的摘要
        self.summarizer.update_summaries(affected)
```

### 模块 4: 引用追溯

```python
@dataclass
class Citation:
    doc_id: str
    title: str
    authors: list[str]
    year: int
    span: str  # 引用的具体片段
    score: float

class CitationTracker:
    def track(self, answer: str, evidence: list[Document]) -> list[Citation]:
        """为答案中的每个论断匹配引用"""
        # 1. 把答案拆成句子(claims)
        claims = split_sentences(answer)
        # 2. 每个 claim 找最匹配的 evidence
        citations = []
        for claim in claims:
            best_doc, best_score = max(
                ((d, cross_encoder.score(claim, d)) for d in evidence),
                key=lambda x: x[1]
            )
            if best_score > 0.5:
                citations.append(Citation(
                    doc_id=best_doc.id,
                    title=best_doc.metadata["title"],
                    authors=best_doc.metadata["authors"],
                    year=best_doc.metadata["year"],
                    span=best_doc.content[:200],
                    score=best_score
                ))
        return citations

    def render_with_citations(self, answer: str, citations: list[Citation]) -> str:
        """生成带引用标记的答案:...[1]...[2]..."""
        # 在答案对应位置插入 [n] 标记
        # 末尾列出参考文献
        ...
```

### 模块 5: 评估与反馈闭环

```python
class EvaluationLoop:
    """离线评测 + 在线反馈"""

    def offline_eval(self):
        """定期跑基准测试集"""
        benchmarks = ["HotpotQA", "2WikiMultiHopQA", "自建论文QA集"]
        results = {}
        for b in benchmarks:
            results[b] = self.run_benchmark(b)
            # 指标:accuracy, recall@k, citation_precision, latency, cost
        return results

    def online_feedback(self, query_id: str, feedback: str):
        """收集用户点击/赞踩,反哺门控与路由训练"""
        # feedback: "good" / "bad" / "missing_info" / "wrong_citation"
        self.feedback_store.log(query_id, feedback)
        # 定期重训分类器
        if self.feedback_store.size() % 1000 == 0:
            self.retrain_gate_classifier()
```

## 三、数据流(典型查询)

```
用户: "Elon Musk 在 2024 年收购的公司,其总部所在城市的市长是谁?"

1. Gate: 需要检索(多跳事实)
2. Classify: relational(关系型)
3. Route: graph_local(GraphRAG 局部)
4. Construct: 子问题分解
   - "Elon Musk acquired companies in 2024"
   - "Headquarters of [acquired company]"
   - "Mayor of [headquarters city]"
5. Multi-hop Retrieve:
   - Hop 1: 图谱查 "Elon Musk -[acquired]-> ?(2024)" → Twitter(X)
   - Hop 2: 图谱查 "X -[headquartered_in]-> ?" → San Francisco
   - Hop 3: Web 查 "Mayor of San Francisco 2024" → London Breed
6. Evaluate: 三跳证据完整,confidence=0.92
7. Synthesize: "Elon Musk 在 2024 年收购了 X(原 Twitter),其总部位于 San Francisco,
                2024 年市长为 London Breed。"
8. Citation: [1] X 收购公告, [2] X 总部信息, [3] SF 市政府官网
```

## 四、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| **向量库** | Milvus | 开源、支持百万级向量、有 GPU 索引 |
| **图数据库** | Neo4j | 成熟、Cypher 查询、社区版够用 |
| **Embedding** | BGE-M3 / OpenAI text-embedding-3 | 多语言、SOTA |
| **重排器** | BGE-Reranker-v2 | 开源、中文友好 |
| **LLM(主)** | GPT-4o / Claude 3.5 | 综合能力强 |
| **LLM(辅,门控/分类)** | GPT-4o-mini / Haiku | 降本 |
| **实体抽取** | GPT-4o-mini + few-shot | 灵活、成本可控 |
| **社区检测** | leidenalg(igraph) | Python 生态、层次化 |
| **Orchestrator** | LangGraph | 状态机原生、可观测 |
| **缓存** | Redis | 社区摘要、热点 query |
| **任务队列** | Celery + Redis | 离线索引流水线 |
| **监控** | LangSmith + Prometheus | Trace + 指标 |

## 五、容量估算

**假设**: 100 万篇论文,平均每篇 8000 token。

| 指标 | 估算 | 说明 |
|------|------|------|
| **向量库** | 100 万 × 8 chunks × 1536 维 × 4 字节 ≈ 50 GB | Milvus 可承载 |
| **图节点** | 100 万篇 × 20 实体/篇 ≈ 2000 万实体 | Neo4j 企业版 |
| **图边** | 2000 万 × 5 关系/实体 ≈ 1 亿关系 | Neo4j 可承载 |
| **社区摘要** | 5 层 × 平均 100 社区/层 × 1500 token ≈ 75 万 token | Redis 缓存 |
| **构图成本** | 800 万 chunks × $0.005/chunk ≈ $40,000(GPT-4o-mini) | 一次性 |
| **增量成本** | 每天 1000 篇 × $0.04/篇 ≈ $40/天 | 可控 |
| **查询延迟** | 局部 3-5s,全局 15-30s,多跳 10-20s | LLM 调用主导 |
| **查询成本** | 平均 5 次 LLM 调用 × $0.005 ≈ $0.025/查询 | 可优化 |
| **QPS** | 单机 50 QPS(API 限流) | 横向扩展 |

## 六、降级与容错

| 场景 | 降级方案 |
|------|---------|
| **LLM 服务不可用** | 切换备用模型(本地 vLLM 部署的 Qwen) |
| **向量库超时** | 降级到关键词检索(BM25) |
| **图数据库超时** | 降级到向量检索(牺牲多跳能力) |
| **Web 搜索不可用** | 提示"时效信息不可用,基于已知数据回答" |
| **检索门控误判** | 用户可手动触发"重新检索"按钮 |
| **构图失败** | 保留上一版本图谱,降级到向量 RAG |
| **成本超限** | 自动降低 max_iterations,改用便宜模型 |
| **延迟过高** | 流式返回中间结果,边检索边输出 |

## 七、面试加分点

1. **Hybrid RAG 路由**: 不是"二选一",而是根据 query 意图动态路由到向量/图谱/Web,甚至并行融合
2. **增量更新**: GraphRAG 的痛点是构图成本,需要设计局部社区重检测机制
3. **引用追溯**: 研究助手必须可信,每句答案标注来源,这是与"普通聊天机器人"的本质区别
4. **成本控制**: 分层 LLM(贵模型用于关键决策,便宜模型用于门控/分类),缓存热点 query
5. **评估闭环**: 离线基准 + 在线反馈,持续优化门控与路由模型

</details>

---

## 核心知识回顾表

| 主题 | 关键要点 | 一句话记忆 |
|------|---------|-----------|
| **Agentic RAG 定义** | Agent 自主决策检索的"何时/什么/哪里/是否够" | 把检索从"管线"变成"工具" |
| **五大核心能力** | 路由/构造/评估/迭代/多跳 | 去哪、怎么查、够不够、再来、串起来 |
| **检索门控** | 规则→分类器→LLM 分层判断 | 不是每个问题都要检索 |
| **迭代检索防循环** | 最大迭代+重复检测+置信度+收敛+预算 | 五道防线,缺一不可 |
| **多跳推理** | 链式/并行/树形,前跳结果指导后跳 | 不是多次检索,是结果驱动检索 |
| **GraphRAG 定义** | 知识图谱增强检索,捕获实体关系 | 向量擅长"相似",图谱擅长"关联" |
| **图谱构建** | 切分→实体抽取→关系抽取→消歧→Leiden→摘要 | LLM 抽取 + Leiden 聚类 |
| **Leiden 算法** | 改进 Louvain,保证社区连通性,层次化 | Louvain 的"连通性修复版" |
| **局部查询** | 种子实体 → BFS 扩展 → 组装上下文 | 具体 entity 问题 |
| **全局查询** | Map-Reduce 聚合社区摘要 | "整个数据集主题"类问题 |
| **MS GraphRAG** | 开源框架,局部+全局,层次社区 | 当前最成熟 GraphRAG 实现 |
| **Hybrid RAG** | 向量 + 图谱 + Web,融合重排 | 不是替代,是融合 |
| **构图成本** | GraphRAG 构图约为向量 RAG 的 100-500 倍 | 贵在 LLM 抽取调用 |
| **Self-RAG** | 反思 token([Retrieve]/[IsRel]/[IsSup]) | LLM 自我控制检索 |
| **引用追溯** | 每个 claim 匹配 evidence,标注来源 | 研究助手必备 |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────┐
│                  Day 09 速记卡                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Agentic RAG = Agent + RAG,把检索变成工具                    │
│  五大能力:路由/构造/评估/迭代/多跳                            │
│  防循环:最大迭代+重复检测+置信度+收敛+预算                    │
│                                                              │
│  GraphRAG = 知识图谱增强检索                                  │
│  构图:实体抽取→关系抽取→消歧→Leiden→社区摘要                 │
│  查询:局部(BFS扩展) / 全局(Map-Reduce社区摘要)              │
│                                                              │
│  Leiden > Louvain:保证社区连通性                             │
│  Hybrid RAG = 向量 + 图谱 + Web,融合重排                     │
│                                                              │
│  成本:GraphRAG 构图是向量 RAG 的 100-500 倍                  │
│  场景:向量擅相似/局部,图谱擅关联/多跳/全局                    │
│                                                              │
│  Self-RAG:反思 token 机制([Retrieve]/[IsRel]/[IsSup])      │
│  HyDE:用假设答案的 embedding 检索                            │
│  Step-back:具体问题抽象到高层                                │
│                                                              │
│  评测:HotpotQA / 2WikiMultiHopQA / MuSiQue                  │
│  框架:LangGraph / LlamaIndex / MS GraphRAG                  │
│                                                              │
│  系统设计:研究助手 = Agentic Orchestrator + Hybrid 检索      │
│           + 引用追溯 + 增量更新 + 评估闭环                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒

1. **Agentic RAG ≠ 多次检索**: 不是"多检索几次就是 Agentic",核心是 Agent **自主决策**(何时/什么/哪里/够不够)。简单多次检索没有决策循环。

2. **多跳推理 ≠ 多次向量检索**: 多跳的关键是"前一跳结果作为后一跳的输入",而非简单并行多次检索。如果只是 top-k 多次,那只是迭代检索。

3. **GraphRAG 不能完全替代向量 RAG**: 对于"找一段讲 X 的文档"这类语义相似查询,向量 RAG 更快更便宜。Hybrid 才是生产答案。

4. **Leiden ≠ Louvain**: Leiden 解决了 Louvain 的"断开社区"问题,保证社区连通性。面试时别说成一样的。

5. **社区检测不是聚类**: Leiden 优化的是**模块度 Q**,不是简单的 K-Means 聚类。聚类是基于距离,社区检测基于图结构。

6. **全局查询不是遍历所有节点**: 而是 Map-Reduce **社区摘要**,绕过上下文长度限制。遍历所有节点是不可行的。

7. **检索门控不是简单的"是否检索"**: 还有"检索什么类型"——门控 + 路由是一体的决策。

8. **HyDE 不是万能的**: HyDE 在事实型问题上有效,但在推理型问题上可能引入幻觉(假设文档错误反而误导检索)。

9. **GraphRAG 增量更新不是简单加节点**: 新实体可能改变社区结构,需要**局部重新社区检测**,这是工程难点。

10. **置信度阈值不能定太低也不能太高**: 太低(如 0.5)导致过早停止、答案不完整;太高(如 0.99)导致永不收敛、成本爆炸。生产建议 0.8-0.9。

---

## 自测检查清单

### 概念题(10 项)

- [ ] 1. 能否用一句话说清 Agentic RAG 与传统 RAG 的本质区别?
- [ ] 2. 能否列出 Agentic RAG 的五大核心能力并各举一个技术实现?
- [ ] 3. 能否画出迭代检索的状态机,并说明 5 个防无限循环机制?
- [ ] 4. 能否区分链式多跳、并行子问题、树形推理三者的适用场景?
- [ ] 5. 能否说明检索门控的三层架构(规则→分类器→LLM)及各层优劣?
- [ ] 6. 能否说出向量 RAG 和 GraphRAG 各自擅长的 3 类问题?
- [ ] 7. 能否完整描述 GraphRAG 图谱构建的 7 步流程?
- [ ] 8. 能否解释 Leiden 相比 Louvain 的改进点(连通性)?
- [ ] 9. 能否区分 GraphRAG 的局部查询和全局查询的实现差异?
- [ ] 10. 能否说出 Self-RAG 的 4 类反思 token 及作用?

### 代码题(3 项)

- [ ] 1. 手撕一个 Agentic RAG 主循环(状态机 + 迭代 + 防循环)
- [ ] 2. 手撕多跳推理(链式,记录 HopStep,支持提前终止)
- [ ] 3. 手撕一个简化版 GraphRAG 图谱构建(实体抽取 mock + Leiden 调用 + 社区摘要)

### 系统设计题(2 项)

- [ ] 1. 设计研究助手系统(Agentic + GraphRAG + 引用追溯 + 增量更新)
- [ ] 2. 设计一个企业知识库问答系统,要求:百万级文档、多部门数据隔离、支持权限控制、低成本。如何选型?如何用 Hybrid RAG?

---

## 延伸阅读

### 论文
1. **Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection** (Asai et al., 2023) — 反思 token 机制
2. **GraphRAG: Unlocking LLM's Potential for Global Queries** (Microsoft, 2024) — GraphRAG 原始论文
3. **Corrective Retrieval Augmented Generation (CRAG)** (Yan et al., 2024) — 检索结果纠错
4. **HyDE: Precise Zero-Shot Dense Retrieval without Real Labels** (Gao et al., 2022) — 假设性文档嵌入
5. **ReAct: Synergizing Reasoning and Acting in Language Models** (Yao et al., 2022) — ReAct 模式
6. **Adaptive-RAG** (Jeong et al., 2024) — 自适应检索策略
7. **Multi-hop Reasoning on Knowledge Graphs** (综述) — 多跳推理综述

### 开源项目
1. **Microsoft GraphRAG**: github.com/microsoft/graphrag — 最成熟 GraphRAG 实现
2. **LangGraph**: github.com/langchain-ai/langgraph — 状态机编排
3. **LlamaIndex Workflow**: github.com/run-llama/llama_index — Agent Workflow
4. **leidenalg**: github.com/vtraag/leidenalg — Leiden 算法 Python 实现
5. **Neo4j GraphRAG**: github.com/neo4j/neo4j-graphrag-python — Neo4j 官方 RAG 包

### 博客与文档
1. **Microsoft GraphRAG 官方文档**: microsoft.github.io/graphrag
2. **LangGraph Agentic RAG 教程**: langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag
3. **LlamaIndex Agentic RAG**: docs.llamaindex.ai/en/stable/optimizing/agentic_rag
4. **From Local to Global: A Graph RAG Approach to Query-Focused Summarization** — MS GraphRAG 博客

### 评测基准
1. **HotpotQA**: hotpotqa.github.io — 多跳问答
2. **2WikiMultiHopQA**: github.com/Alab-NII/2wikimultihop — 跨维基多跳
3. **MuSiQue**: github.com/stonybrooknlp/musique — 多步推理
4. **BEIR**: github.com/beir-cellar/beir — 检索基准

---

## 明日预告

**Day 10 — 向量数据库选型与优化**

明天将深入向量数据库这个 RAG 系统的"地基":

1. **主流向量库对比**: Milvus / Pinecone / Weaviate / Qdrant / Chroma / FAISS / pgvector,从性能、成本、易用性、扩展性四维评估
2. **索引算法**: HNSW / IVF / PQ / ScaNN,各自的原理、复杂度、适用场景
3. **量化与压缩**: PQ(乘积量化)/ SQ(标量量化)/ 二值量化,如何用 1/4 内存换 5% 召回率
4. **分布式与分片**: 大规模向量的水平扩展策略,如何应对 10 亿级向量
5. **混合检索**: 向量 + BM25 + 重排的多路融合
6. **工程实践**: 索引构建、增量更新、冷热分层、监控指标
7. **面试真题**: "百万级 / 亿级向量如何选型?"、"向量检索延迟 P99 < 50ms 如何保证?"

预告提醒: Day10 是 Day08(RAG 全链路)和 Day09(Agentic RAG / GraphRAG)的"基础设施层",三者构成完整的 RAG 技术栈。建议今晚回顾下 Day08 的 Embedding 与 Chunking 部分,明天会用到。

---

> **学习建议**: Day09 内容密度大,建议分两次学——第一次重点看 Q1-Q5(Agentic RAG)和 Q9(手撕代码),第二次看 Q6-Q8(GraphRAG)和 Q10(系统设计)。代码题务必自己敲一遍,系统设计题画一遍架构图。
```
