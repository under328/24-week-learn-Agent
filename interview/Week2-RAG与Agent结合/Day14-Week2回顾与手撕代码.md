# Day 14 — Week 2 回顾与手撕代码特训

> **本周进度**: Day8 ✅ → Day9 ✅ → Day10 ✅ → Day11 ✅ → Day12 ✅ → Day13 ✅ → **Day14 回顾与手撕**
>
> **本日定位**: Week2 收官日。前六天把 RAG 与 Agent 结合的全链路知识铺开了,今天做三件事 ——
> (1) 把六天知识串成一张图;(2) 手撕 6 道高频代码题;(3) 用自测清单验收,为 Week3 框架与系统设计打基础。
>
> **学习时长建议**: 3-4 小时(手撕代码 2h + 综合问答 1h + 自测 1h)

---

## 一、Week 2 知识图谱总览

```
                        RAG + Agent 能力栈
                              │
       ┌─────────┬───────────┼───────────┬───────────┬──────────┐
       │         │           │           │           │          │
    RAG全链路  Agentic     向量DB      Context    RAG评估    实战Demo
    (Day8)    RAG/Graph   选型优化    Engineering  框架      规划
              (Day9)      (Day10)      (Day11)    (Day12)    (Day13)
       │         │           │           │           │          │
    分块        检索路由    HNSW       Token预算   Recall@K   选题立项
    Embedding   迭代检索    IVF        Lost-in-    MRR        架构设计
    检索        多跳推理    PQ         Middle      NDCG       面试话术
    Rerank      知识图谱    混合检索   压缩/排序    LLM-Judge  简历呈现
    生成        社区检测    十亿级     优先级       A/B测试    STAR叙事
       │         │           │           │           │          │
       └─────────┴─────┬─────┴───────────┴───────────┴──────────┘
                       │
                  可靠性 & 可评估性
          引用溯源 / 防幻觉 / 防无限循环 / 可复现评测 / 成本控制
```

### 六天核心知识点串联

| Day | 主题 | 核心公式 / 概念 | 一句话总结 |
|-----|------|---------------|-----------|
| 8 | RAG 全链路 | `chunk → embed → retrieve → rerank → generate` | 五段式流水线,每一段都是可替换的"插槽" |
| 9 | Agentic RAG / GraphRAG | `route → retrieve → reflect → (loop) → synthesize`;社区 = Louvain 模块度最大化 | 把"一次检索"升级成"按需迭代检索",图结构补多跳推理短板 |
| 10 | 向量库选型 | HNSW: `O(log n)` 近邻图;RRF: `score = Σ 1/(k+rank_i)`;PQ: `m×log256` 字节/向量 | 索引 = 召回率 × 内存 × 延迟 的三角权衡 |
| 11 | Context Engineering | `budget = system + history + retrieved + answer`;Lost-in-the-Middle 重排 | Token 是稀缺资源,谁进上下文、谁排前面、谁该被压缩,是工程核心 |
| 12 | RAG 评估 | `Recall@K = |R∩A_K|/|R|`;`MRR = 1/rank`;`NDCG = DCG/iDCG`;LLM-as-Judge 三维 | 没有评测的 RAG 都是玩具,检索看 Recall/MRR,生成看 Faithfulness/Relevancy |
| 13 | 实战 Demo 规划 | STAR = Situation-Task-Action-Result;架构图三段 = 离线建库 / 在线查询 / 评估闭环 | 项目不是用来背的,是用来"被追问时还能自圆其说"的 |

---

## 二、高频手撕代码题(6 道)

> **答题纪律**: 每道题先口述思路 30 秒(数据结构 → 主流程 → 边界),再写代码。面试官看的是"工程化习惯",不是"背得多快"。

### 手撕题 1: 实现完整的 RAG 查询引擎(分块 + Embedding + 检索 + Rerank + 生成 + 引用溯源)

<details>
<summary>点击查看参考答案</summary>

**思路口述**:
- 数据结构: `Chunk` 持有 `text/source/page`,检索结果用 `RetrievalHit` 带 `score`,最终答案用 `Answer` 持有 `text + citations`。
- 主流程: 离线 `index()` 做分块+Embedding 入库;在线 `query()` 做 retrieve → rerank → build_context → generate → attach_citations。
- 边界: 空检索结果走兜底 prompt;引用编号必须与 context 中序号对应;Rerank 只对 top-K 重排,不扩大候选。

```python
"""
完整 RAG 查询引擎
- 离线: 文档分块 + Embedding 入库
- 在线: 检索 → Rerank → 上下文构建 → 生成 → 引用溯源
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str        # 文档名/URL
    page: int          # 页码或位置
    embedding: Optional[list] = None


@dataclass
class RetrievalHit:
    chunk: Chunk
    vector_score: float
    rerank_score: Optional[float] = None


@dataclass
class Answer:
    text: str
    citations: list        # [(chunk_id, source, page)]
    used_chunks: int
    latency_ms: float


class RAGQueryEngine:
    def __init__(
        self,
        embed_fn: Callable[[str], list],          # 文本 → 向量
        vector_store: dict,                         # 简化: {chunk_id: (embedding, chunk)}
        rerank_fn: Callable[[str, str], float],    # (query, doc) → 相关性分
        llm_fn: Callable[[str], str],              # prompt → 回答
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        retrieve_top_k: int = 20,                   # 初检候选
        rerank_top_n: int = 5,                      # 重排后保留
    ):
        self.embed_fn = embed_fn
        self.vector_store = vector_store
        self.rerank_fn = rerank_fn
        self.llm_fn = llm_fn
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.retrieve_top_k = retrieve_top_k
        self.rerank_top_n = rerank_top_n

    # ---------- 离线建库 ----------
    def index(self, doc_text: str, source: str) -> int:
        chunks = self._split_text(doc_text, source)
        for c in chunks:
            c.embedding = self.embed_fn(c.text)
            self.vector_store[c.chunk_id] = (c.embedding, c)
        return len(chunks)

    def _split_text(self, text: str, source: str) -> list:
        """滑动窗口分块,带重叠"""
        chunks = []
        start = 0
        idx = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(Chunk(
                chunk_id=f"{source}_c{idx}",
                text=text[start:end],
                source=source,
                page=idx,
            ))
            start += self.chunk_size - self.chunk_overlap
            idx += 1
        return chunks

    # ---------- 在线查询 ----------
    def query(self, question: str) -> Answer:
        import time
        t0 = time.time()

        # 1. Embedding
        q_vec = self.embed_fn(question)

        # 2. 向量检索(简化: 线性扫描 + 余弦)
        hits = self._vector_search(q_vec, self.retrieve_top_k)

        # 3. Rerank(Cross-Encoder 对 top-K 重排)
        for h in hits:
            h.rerank_score = self.rerank_fn(question, h.chunk.text)
        hits.sort(key=lambda h: h.rerank_score, reverse=True)
        top_hits = hits[: self.rerank_top_n]

        # 4. 构建带引用编号的上下文
        context_blocks = []
        for i, h in enumerate(top_hits, start=1):
            context_blocks.append(
                f"[{i}] (source={h.chunk.source}, page={h.chunk.page})\n{h.chunk.text}"
            )
        context = "\n\n".join(context_blocks) if context_blocks else "(无相关上下文)"

        # 5. 生成
        prompt = self._build_prompt(question, context)
        raw_answer = self.llm_fn(prompt)

        # 6. 引用溯源(把答案中出现的 [n] 映射回 chunk)
        citations = self._extract_citations(raw_answer, top_hits)

        return Answer(
            text=raw_answer,
            citations=citations,
            used_chunks=len(top_hits),
            latency_ms=round((time.time() - t0) * 1000, 1),
        )

    def _vector_search(self, q_vec: list, top_k: int) -> list:
        import math
        scored = []
        for cid, (emb, chunk) in self.vector_store.items():
            sim = self._cosine(q_vec, emb)
            scored.append(RetrievalHit(chunk=chunk, vector_score=sim))
        scored.sort(key=lambda h: h.vector_score, reverse=True)
        return scored[:top_k]

    @staticmethod
    def _cosine(a: list, b: list) -> float:
        import math
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-9)

    def _build_prompt(self, question: str, context: str) -> str:
        return (
            "你是严谨的问答助手。只能基于下方【上下文】回答问题,"
            "并在答案中用 [n] 标注引用来源。若上下文不足以回答,请回答"
            "'根据现有资料无法回答'。\n\n"
            f"【上下文】\n{context}\n\n"
            f"【问题】{question}\n\n"
            f"【答案】(请带 [n] 引用):"
        )

    @staticmethod
    def _extract_citations(answer: str, hits: list) -> list:
        import re
        refs = set(int(m) for m in re.findall(r"\[(\d+)\]", answer))
        out = []
        for n in sorted(refs):
            if 1 <= n <= len(hits):
                h = hits[n - 1]
                out.append((h.chunk.chunk_id, h.chunk.source, h.chunk.page))
        return out


# ---------- Mock 演示 ----------
if __name__ == "__main__":
    import random
    random.seed(0)

    def mock_embed(text: str) -> list:
        # 用字符 hash 模拟稳定向量
        return [random.uniform(-1, 1) for _ in range(8)]

    def mock_rerank(q: str, d: str) -> float:
        # 词重叠率模拟 Cross-Encoder
        qs = set(q.lower().split())
        ds = set(d.lower().split())
        return len(qs & ds) / (len(qs) + 1e-9)

    def mock_llm(prompt: str) -> str:
        return "根据资料,RAG 由分块、Embedding、检索、Rerank、生成五步组成 [1][2]。"

    store: dict = {}
    engine = RAGQueryEngine(mock_embed, store, mock_rerank, mock_llm)
    engine.index("RAG 流水线包括分块和 Embedding 两个离线步骤。", "rag_doc.md")
    engine.index("在线阶段做检索、Rerank 和生成,并标注引用。", "rag_doc.md")

    ans = engine.query("RAG 由哪些步骤组成?")
    print(ans)
```

**面试评分要点**:
- ✅ 五段式职责清晰,每段都可单独替换(Embedding 模型/向量库/Reranker/LLM)
- ✅ 引用溯源用 `[n]` 双向绑定,答案可追溯,这是"防幻觉"工程标配
- ✅ Rerank 只对 top-K 重排,不扩大候选 —— 体现"成本意识"
- ✅ 兜底 prompt 处理空检索,避免 LLM 编造
- ⚠️ 追问 1: 分块策略? 答: 中文按句号/换行切再补滑动窗口,长文档做层级分块(章节→段落→句)
- ⚠️ 追问 2: 为什么不直接用向量得分排序? 答: 向量检索是双塔Bi-Encoder,粗排快但精度低;Cross-Encoder 单塔精排贵但准,所以"先粗后精"
- ⚠️ 追问 3: 如何避免引用错配? 答: 答案生成后用正则提取 `[n]`,再与 context 序号映射;生产环境可用 LLM 二次校验引用一致性

</details>

---

### 手撕题 2: 实现 Agentic RAG(检索路由 + 迭代检索 + 多跳推理 + 结果评估 + 防无限循环)

<details>
<summary>点击查看参考答案</summary>

**思路口述**:
- 数据结构: `AgentState` 持有 `question / retrieved / hops / history / status`,状态机驱动。
- 主流程: `route()` 决定走向量/图/直接答 → `retrieve()` → `evaluate()` 判断是否够答 → 不够则 `rewrite_query()` 再检索 → 够则 `synthesize()`。
- 边界: `max_hops` 防无限循环;`confidence < threshold` 走兜底;"无新增信息"即停。

```python
"""
Agentic RAG: 把"一次检索"升级为"按需迭代检索"
核心机制: 路由 → 检索 → 评估 → (rewrite → 再检索) → 综合
"""

from dataclasses import dataclass, field
from typing import Callable, Literal


@dataclass
class AgentState:
    question: str
    retrieved: list = field(default_factory=list)        # 累积检索到的 chunk
    hops: int = 0
    history: list = field(default_factory=list)          # 每跳的 (query, hit_count)
    status: Literal["running", "ok", "no_progress", "max_hops", "low_conf"] = "running"
    final_answer: str = ""
    confidence: float = 0.0


class AgenticRAG:
    def __init__(
        self,
        llm_fn: Callable[[str], str],
        vector_retrieve: Callable[[str], list],          # query → [chunk]
        graph_retrieve: Callable[[str], list],           # query → [chunk]
        max_hops: int = 3,
        min_new_chunks: int = 1,                         # 每跳至少新增多少 chunk 才算有进展
        confidence_threshold: float = 0.6,
    ):
        self.llm_fn = llm_fn
        self.vector_retrieve = vector_retrieve
        self.graph_retrieve = graph_retrieve
        self.max_hops = max_hops
        self.min_new_chunks = min_new_chunks
        self.confidence_threshold = confidence_threshold

    def run(self, question: str) -> AgentState:
        state = AgentState(question=question)
        existing_ids = set()

        while state.status == "running":
            # 1. 检索路由
            route = self._route(question, state)
            query = self._rewrite_query(state) if state.hops > 0 else question

            # 2. 执行检索
            if route == "vector":
                new_chunks = self.vector_retrieve(query)
            elif route == "graph":
                new_chunks = self.graph_retrieve(query)
            else:  # direct
                state.final_answer = self._llm_direct(question)
                state.status = "ok"
                state.confidence = 1.0
                break

            # 3. 去重 + 记录进展
            fresh = [c for c in new_chunks if c["id"] not in existing_ids]
            for c in new_chunks:
                existing_ids.add(c["id"])
            state.retrieved.extend(fresh)
            state.history.append({"hop": state.hops, "query": query, "new": len(fresh)})
            state.hops += 1

            # 4. 防无限循环: 无新进展
            if len(fresh) < self.min_new_chunks:
                state.status = "no_progress"
                break

            # 5. 评估是否够答
            state.confidence, enough = self._evaluate(question, state.retrieved)
            if enough:
                state.status = "ok"
                state.final_answer = self._synthesize(question, state.retrieved)
                break

            # 6. 防无限循环: 超最大跳数
            if state.hops >= self.max_hops:
                state.status = "max_hops"
                state.final_answer = self._synthesize(question, state.retrieved)
                break

        # 7. 低置信兜底
        if state.status == "ok" and state.confidence < self.confidence_threshold:
            state.status = "low_conf"
            state.final_answer = (
                "(置信度较低,仅供参考)" + state.final_answer
            )

        return state

    # ---------- 路由 ----------
    def _route(self, question: str, state: AgentState) -> str:
        """简化版路由: 含多跳关键词走图,闲聊走直答,其余向量"""
        multi_hop_hints = ["对比", "关系", "影响", "原因", "链路", "A 和 B"]
        if any(k in question for k in multi_hop_hints) and state.hops == 0:
            return "graph"
        if any(k in question for k in ["你好", "谢谢", "天气"]) and state.hops == 0:
            return "direct"
        return "vector"

    # ---------- 查询改写 ----------
    def _rewrite_query(self, state: AgentState) -> str:
        """根据已检索内容生成下一跳的更具体 query"""
        seen = " | ".join(c["text"][:40] for c in state.retrieved[-3:])
        prompt = (
            f"原始问题: {state.question}\n"
            f"已检索片段: {seen}\n"
            "请生成一个更具体、补充信息缺口的检索查询(一句话,不要解释):"
        )
        return self.llm_fn(prompt).strip()

    # ---------- 评估 ----------
    def _evaluate(self, question: str, retrieved: list) -> tuple:
        """LLM 判断当前证据是否足够回答,返回 (confidence, enough)"""
        context = "\n".join(c["text"] for c in retrieved[:8])
        prompt = (
            "判断以下证据是否足以回答问题。输出两行:\n"
            "第一行: 0.0-1.0 的置信度\n"
            "第二行: YES 或 NO\n\n"
            f"问题: {question}\n证据:\n{context}"
        )
        out = self.llm_fn(prompt).strip().splitlines()
        try:
            conf = float(out[0])
        except (ValueError, IndexError):
            conf = 0.3
        enough = len(out) > 1 and out[1].strip().upper().startswith("Y")
        return conf, enough

    # ---------- 综合 ----------
    def _synthesize(self, question: str, retrieved: list) -> str:
        context = "\n\n".join(f"[{i+1}] {c['text']}" for i, c in enumerate(retrieved[:6]))
        prompt = f"基于以下证据回答问题,标注 [n] 引用。\n证据:\n{context}\n\n问题: {question}\n答案:"
        return self.llm_fn(prompt)

    def _llm_direct(self, question: str) -> str:
        return self.llm_fn(f"直接回答: {question}")


# ---------- Mock 演示 ----------
if __name__ == "__main__":
    def mock_llm(prompt: str) -> str:
        if "更具体" in prompt:
            return "RAG 系统中 Rerank 的具体算法是什么"
        if "置信度" in prompt:
            return "0.85\nYES"
        if "证据" in prompt:
            return "RAG 在线阶段使用 Cross-Encoder 做 Rerank [1]。"
        return "RAG 由五步组成 [1]。"

    def mock_vec(q: str) -> list:
        return [{"id": f"v{hash(q)%100}", "text": f"向量结果: {q}"}]

    def mock_graph(q: str) -> list:
        return [{"id": f"g{hash(q)%100}", "text": f"图谱结果: {q}"}]

    agent = AgenticRAG(mock_llm, mock_vec, mock_graph, max_hops=3)
    s = agent.run("对比 RAG 和 GraphRAG 的检索链路差异")
    print(f"status={s.status}, hops={s.hops}, conf={s.confidence}")
    print(f"answer={s.final_answer}")
    print(f"history={s.history}")
```

**面试评分要点**:
- ✅ 状态机驱动,`status` 枚举清晰,每一停都有明确语义(no_progress / max_hops / low_conf)
- ✅ 双重防无限循环: 跳数上限 + 新增 chunk 下限,任一触发即停
- ✅ 路由策略可插拔,演示版用关键词,生产版换成 LLM 分类器或小模型
- ✅ 查询改写只在"不够答"时触发,不是无脑迭代 —— 体现"按需"
- ⚠️ 追问 1: 多跳推理如何避免"漂移"? 答: 每跳 query 改写必须锚定原始问题,prompt 中带原问题+已检索摘要;同时累积检索而非替换
- ⚠️ 追问 2: 迭代检索和 GraphRAG 多跳有什么区别? 答: 迭代检索是"查询空间"的多跳(改写query);GraphRAG 是"实体空间"的多跳(沿关系边走)。二者可叠加
- ⚠️ 追问 3: evaluate 用 LLM 贵且慢,有没有轻量替代? 答: 用已检索 chunk 对问题的覆盖度评分(关键词召回率 / Embedding 相似度阈值),LLM 评估只在边界 case 触发

</details>

---

### 手撕题 3: 实现混合检索系统(向量检索 + BM25 + RRF 融合 + Cross-Encoder Reranker)

<details>
<summary>点击查看参考答案</summary>

**思路口述**:
- 两路并行: 向量路走余弦相似度(Bi-Encoder 粗排),词频路走 BM25(精确关键词命中)。
- RRF 融合: `score = Σ 1/(k + rank_i)`,只依赖排名不依赖原始分,天然解决两路分值不可比问题。
- 最后 Cross-Encoder 对融合后 top-N 精排,产出最终结果。

```python
"""
混合检索 = 向量检索 + BM25 + RRF 融合 + Cross-Encoder Rerank
关键点: RRF 用 rank 而非 score,避免两路分值尺度不一致
"""

import math
import re
from dataclasses import dataclass
from typing import Callable


@dataclass
class Doc:
    doc_id: str
    text: str
    embedding: list = None


class HybridRetriever:
    def __init__(
        self,
        embed_fn: Callable[[str], list],
        cross_encoder_fn: Callable[[str, str], float],
        rrf_k: int = 60,                # RRF 经验值 60
        vector_top_k: int = 20,
        bm25_top_k: int = 20,
        final_top_n: int = 5,
    ):
        self.embed_fn = embed_fn
        self.cross_encoder_fn = cross_encoder_fn
        self.rrf_k = rrf_k
        self.vector_top_k = vector_top_k
        self.bm25_top_k = bm25_top_k
        self.final_top_n = final_top_n
        self.docs: list[Doc] = []
        self.bm25: BM25 = None

    def index(self, docs: list[Doc]) -> None:
        for d in docs:
            d.embedding = self.embed_fn(d.text)
        self.docs = docs
        self.bm25 = BM25([d.text for d in docs])

    def search(self, query: str) -> list:
        q_vec = self.embed_fn(query)

        # 1. 向量路
        vec_scored = [
            (d.doc_id, self._cosine(q_vec, d.embedding)) for d in self.docs
        ]
        vec_scored.sort(key=lambda x: x[1], reverse=True)
        vec_ranking = [d[0] for d in vec_scored[: self.vector_top_k]]

        # 2. BM25 路
        bm25_scored = self.bm25.search(query, k=self.bm25_top_k)
        bm25_ranking = [d[0] for d in bm25_scored]

        # 3. RRF 融合
        rrf_scores: dict[str, float] = {}
        for rank, did in enumerate(vec_ranking, start=1):
            rrf_scores[did] = rrf_scores.get(did, 0) + 1 / (self.rrf_k + rank)
        for rank, did in enumerate(bm25_ranking, start=1):
            rrf_scores[did] = rrf_scores.get(did, 0) + 1 / (self.rrf_k + rank)

        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        candidate_ids = [d[0] for d in fused[: self.final_top_n * 2]]  # 留余量给 rerank

        # 4. Cross-Encoder Rerank
        doc_map = {d.doc_id: d for d in self.docs}
        reranked = []
        for did in candidate_ids:
            d = doc_map[did]
            score = self.cross_encoder_fn(query, d.text)
            reranked.append((did, score, rrf_scores[did]))
        reranked.sort(key=lambda x: x[1], reverse=True)

        return [
            {"doc_id": did, "ce_score": score, "rrf_score": rrf, "text": doc_map[did].text}
            for did, score, rrf in reranked[: self.final_top_n]
        ]

    @staticmethod
    def _cosine(a: list, b: list) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-9)


class BM25:
    """简化版 BM25,适合手撕演示"""

    def __init__(self, corpus: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus = [self._tokenize(t) for t in corpus]
        self.df: dict[str, int] = {}
        for tokens in self.corpus:
            for tok in set(tokens):
                self.df[tok] = self.df.get(tok, 0) + 1
        self.N = len(corpus)
        self.avgdl = sum(len(t) for t in self.corpus) / max(self.N, 1)
        self.idf = {
            tok: math.log(1 + (self.N - df + 0.5) / (df + 0.5))
            for tok, df in self.df.items()
        }

    def _tokenize(self, text: str) -> list:
        return re.findall(r"\w+", text.lower())

    def search(self, query: str, k: int = 10) -> list:
        q_tokens = self._tokenize(query)
        scores = []
        for i, doc_tokens in enumerate(self.corpus):
            score = 0.0
            dl = len(doc_tokens)
            tf_map: dict[str, int] = {}
            for t in doc_tokens:
                tf_map[t] = tf_map.get(t, 0) + 1
            for qt in q_tokens:
                if qt not in tf_map:
                    continue
                tf = tf_map[qt]
                idf = self.idf.get(qt, 0.0)
                score += idf * (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1))
                )
            scores.append((f"d{i}", score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:k]


# ---------- Mock 演示 ----------
if __name__ == "__main__":
    import random
    random.seed(1)

    def mock_embed(text: str) -> list:
        return [random.uniform(-1, 1) for _ in range(8)]

    def mock_ce(q: str, d: str) -> float:
        return len(set(q.lower().split()) & set(d.lower().split())) / (len(q.split()) + 1)

    docs = [
        Doc("d0", "RAG retrieval augmented generation combines search with LLM"),
        Doc("d1", "BM25 is a probabilistic ranking function for keyword search"),
        Doc("d2", "Cross encoder reranks candidates with higher accuracy"),
        Doc("d3", "HNSW graph index enables fast approximate nearest neighbor"),
        Doc("d4", "Hybrid retrieval combines dense and sparse signals via RRF"),
    ]

    retriever = HybridRetriever(mock_embed, mock_ce)
    retriever.index(docs)
    res = retriever.search("hybrid retrieval RRF dense sparse")
    for r in res:
        print(r)
```

**面试评分要点**:
- ✅ RRF 公式正确 `1/(k+rank)`,k=60 是 SIGIR 论文经验值,只看排名不看分值,天然归一化
- ✅ BM25 实现完整: TF 饱和项 `(k1+1)*tf/(tf+k1*(...))` + IDF + 文档长度归一化 b
- ✅ 两路并行 + 融合 + 精排三段式,职责清晰,可独立调参
- ✅ Cross-Encoder 只对融合后候选精排,体现"先粗后精"的成本控制
- ⚠️ 追问 1: 为什么不直接加权 `α*vec + (1-α)*bm25`? 答: 两路分值尺度差几个数量级,α 难调;RRF 用 rank 绕过尺度问题,鲁棒性强
- ⚠️ 追问 2: BM25 的 k1/b 怎么调? 答: k1 控制 TF 饱和速度(1.2-2.0),b 控制文档长度惩罚(0.75 常用);实际用验证集网格搜索
- ⚠️ 追问 3: 中文 BM25 怎么分词? 答: jieba/HanLP 分词后建倒排;不分词的退化方案是字级 BM25,召回率略低但零依赖

</details>

---

### 手撕题 4: 实现上下文管理器(Token 预算分配 + 压缩 + 截断 + 优先级排序)

<details>
<summary>点击查看参考答案</summary>

**思路口述**:
- 预算四段分配: `system(固定) + history(衰减保留) + retrieved(按优先级) + answer(预留)`。
- 优先级: 系统提示 > 最新用户问题 > 最近 N 轮历史 > 高相关检索块 > 旧历史 > 低相关检索块。
- 三种策略可选: 截断(粗暴)、压缩(LLM 摘要)、滑动窗口(只保留最近 K 轮)。
- Lost-in-the-Middle: 把高优先块放在 context 首尾,低优先块放中间。

```python
"""
Context Manager: 在有限 token 预算内,智能组装上下文
- 四段预算: system / history / retrieved / answer
- 三种策略: truncate / compress / sliding_window
- Lost-in-the-Middle: 高优先级放首尾
"""

from dataclasses import dataclass
from typing import Callable, Literal


@dataclass
class Message:
    role: str
    content: str


@dataclass
class RetrievedChunk:
    text: str
    score: float          # 相关性分
    source: str


@dataclass
class AssembledContext:
    messages: list        # 组装后的 messages 数组
    token_usage: dict     # 各段实际占用
    dropped: list         # 被丢弃的内容(用于日志)
    strategy: str


class ContextManager:
    def __init__(
        self,
        count_tokens_fn: Callable[[str], int],
        llm_summarize_fn: Callable[[str], str],
        max_total_tokens: int = 8000,
        reserve_answer: int = 1000,
        system_ratio: float = 0.1,
        history_ratio: float = 0.3,
        retrieved_ratio: float = 0.6,
    ):
        self.count = count_tokens_fn
        self.summarize = llm_summarize_fn
        self.max_total = max_total_tokens
        self.reserve_answer = reserve_answer
        self.system_ratio = system_ratio
        self.history_ratio = history_ratio
        self.retrieved_ratio = retrieved_ratio

    def assemble(
        self,
        system_prompt: str,
        history: list[Message],
        retrieved: list[RetrievedChunk],
        current_question: str,
        strategy: Literal["truncate", "compress", "sliding_window"] = "truncate",
    ) -> AssembledContext:
        budget = self.max_total - self.reserve_answer
        sys_budget = int(budget * self.system_ratio)
        hist_budget = int(budget * self.history_ratio)
        ret_budget = int(budget * self.retrieved_ratio)

        dropped = []

        # 1. system(高优先,尽量全留)
        sys_tokens = self.count(system_prompt)
        if sys_tokens > sys_budget:
            # system 一般不砍,允许超出预算
            sys_text = system_prompt
        else:
            sys_text = system_prompt

        # 2. history 策略处理
        if strategy == "sliding_window":
            hist_msgs, hist_drop = self._sliding_window(history, hist_budget)
        elif strategy == "compress":
            hist_msgs, hist_drop = self._compress_history(history, hist_budget)
        else:
            hist_msgs, hist_drop = self._truncate_history(history, hist_budget)
        dropped.extend(hist_drop)

        # 3. retrieved 按相关性排序 + 截断到预算
        retrieved_sorted = sorted(retrieved, key=lambda c: c.score, reverse=True)
        ret_blocks, ret_drop = self._pack_retrieved(retrieved_sorted, ret_budget)
        dropped.extend(ret_drop)

        # 4. Lost-in-the-Middle 重排: 高分放首尾
        ret_blocks = self._lost_in_middle_reorder(ret_blocks)

        # 5. 组装 messages
        messages: list[Message] = [Message("system", sys_text)]
        messages.extend(hist_msgs)
        if ret_blocks:
            context_text = "\n\n".join(ret_blocks)
            messages.append(Message("user", f"【参考资料】\n{context_text}"))
        messages.append(Message("user", current_question))

        token_usage = {
            "system": self.count(sys_text),
            "history": sum(self.count(m.content) for m in hist_msgs),
            "retrieved": sum(self.count(b) for b in ret_blocks),
            "question": self.count(current_question),
            "answer_reserved": self.reserve_answer,
            "total_planned": self.count(sys_text)
            + sum(self.count(m.content) for m in hist_msgs)
            + sum(self.count(b) for b in ret_blocks)
            + self.count(current_question)
            + self.reserve_answer,
        }

        return AssembledContext(
            messages=messages,
            token_usage=token_usage,
            dropped=dropped,
            strategy=strategy,
        )

    # ---------- 历史策略 ----------
    def _truncate_history(self, history: list, budget: int) -> tuple:
        kept, dropped = [], []
        # 从最新往回取(最近最重要)
        for msg in reversed(history):
            t = self.count(msg.content)
            if sum(self.count(m.content) for m in kept) + t > budget:
                dropped.append(msg)
            else:
                kept.insert(0, msg)
        return kept, [f"dropped history: {m.role}" for m in dropped]

    def _sliding_window(self, history: list, budget: int, k: int = 4) -> tuple:
        recent = history[-k:]
        kept, dropped = [], []
        for msg in reversed(recent):
            t = self.count(msg.content)
            if sum(self.count(m.content) for m in kept) + t > budget:
                dropped.append(msg)
            else:
                kept.insert(0, msg)
        all_dropped = [f"dropped(out of window): {m.role}" for m in history[:-k]]
        all_dropped += [f"dropped(over budget): {m.role}" for m in dropped]
        return kept, all_dropped

    def _compress_history(self, history: list, budget: int) -> tuple:
        full_text = "\n".join(f"{m.role}: {m.content}" for m in history)
        if self.count(full_text) <= budget:
            return history, []
        # 把旧历史压缩成摘要,保留最近 2 轮原文
        old = history[:-4]
        recent = history[-4:]
        if old:
            old_text = "\n".join(f"{m.role}: {m.content}" for m in old)
            summary = self.summarize(old_text)
            compressed = [Message("system", f"[历史摘要] {summary}")]
            return compressed + recent, [f"compressed {len(old)} old msgs into 1 summary"]
        return recent, []

    # ---------- 检索块打包 ----------
    def _pack_retrieved(self, sorted_chunks: list, budget: int) -> tuple:
        blocks, dropped = [], []
        used = 0
        for c in sorted_chunks:
            t = self.count(c.text)
            if used + t > budget:
                dropped.append(f"dropped chunk: {c.source} (score={c.score:.3f})")
                continue
            blocks.append(f"[{c.source}] {c.text}")
            used += t
        return blocks, dropped

    # ---------- Lost-in-the-Middle 重排 ----------
    @staticmethod
    def _lost_in_middle_reorder(blocks: list) -> list:
        """
        高分放首尾,低分放中间,规避 LLM 对中间位置注意力衰减
        输入已按分数降序,输出: [0, 2, 4, ...中间..., 5, 3, 1]
        """
        if len(blocks) <= 2:
            return blocks
        head, tail = [], []
        for i, b in enumerate(blocks):
            if i % 2 == 0:
                head.append(b)
            else:
                tail.append(b)
        return head + list(reversed(tail))


# ---------- Mock 演示 ----------
if __name__ == "__main__":
    def mock_count(text: str) -> int:
        # 粗略: 1 token ≈ 4 字符
        return len(text) // 4

    def mock_summarize(text: str) -> str:
        return f"(摘要: {text[:30]}...)"

    cm = ContextManager(mock_count, mock_summarize, max_total_tokens=2000, reserve_answer=300)

    history = [
        Message("user", "什么是 RAG?"),
        Message("assistant", "RAG 是检索增强生成的缩写,通过外部知识提升 LLM 回答准确性。"),
        Message("user", "它和微调有什么区别?"),
        Message("assistant", "RAG 改变输入,微调改变模型参数;RAG 适合知识频繁更新的场景。"),
        Message("user", "分块策略有哪些?"),
        Message("assistant", "固定窗口、滑动窗口、语义分块、层级分块等。"),
    ]
    retrieved = [
        RetrievedChunk("Rerank 用 Cross-Encoder 对候选重排", 0.92, "doc_a"),
        RetrievedChunk("HNSW 是基于图的近似最近邻索引", 0.88, "doc_b"),
        RetrievedChunk("BM25 是经典概率检索模型", 0.85, "doc_c"),
        RetrievedChunk("RRF 融合多路检索结果", 0.80, "doc_d"),
        RetrievedChunk("Context Compression 用 LLM 摘要历史", 0.70, "doc_e"),
    ]

    for strat in ["truncate", "sliding_window", "compress"]:
        result = cm.assemble(
            "你是严谨的 RAG 助手。",
            history,
            retrieved,
            "如何在有限上下文中做检索?",
            strategy=strat,
        )
        print(f"\n=== strategy={strat} ===")
        print(f"token_usage={result.token_usage}")
        print(f"dropped={result.dropped}")
        print(f"messages count={len(result.messages)}")
```

**面试评分要点**:
- ✅ 四段预算 + answer 预留,避免"答案写到一半 token 用完"
- ✅ 三种策略可切换: truncate 简单粗暴、sliding_window 适合长对话、compress 省空间但有损
- ✅ Lost-in-the-Middle 重排算法正确(偶数位头插、奇数位尾插反转),规避中间注意力衰减
- ✅ dropped 日志记录,便于后续调优和审计
- ⚠️ 追问 1: 压缩历史的摘要本身也要消耗 token,怎么权衡? 答: 当 `len(history) > N` 才触发压缩;摘要只保留"事实/决策",丢弃寒暄;摘要可缓存
- ⚠️ 追问 2: 为什么 answer 也要预留? 答: 生成是自回归,若上下文撑满窗口,生成到一半就触达 max_tokens,答案被截断;预留量根据任务复杂度设(简单 QA 500,长文生成 2000)
- ⚠️ 追问 3: Lost-in-the-Middle 在哪些模型上最明显? 答: 长上下文(>8K)模型上最显著;短上下文或经过 position-interpolation 训练的模型影响较小,但仍建议重排

</details>

---

### 手撕题 5: 实现 RAG 评估系统(Recall@K / MRR / NDCG 计算 + LLM-as-Judge + 诊断分析)

<details>
<summary>点击查看参考答案</summary>

**思路口述**:
- 检索指标: Recall@K(召回率)、MRR(第一个相关文档的倒数排名)、NDCG(带位置衰减的相关性累积)。
- 生成指标: 用 LLM-as-Judge 打 Faithfulness(答案是否忠于检索)/ Relevancy(是否切题)两个维度。
- 诊断: 把"检索好但生成差"和"检索差但生成好"分离出来,定位瓶颈在检索还是生成。

```python
"""
RAG 评估系统
- 检索: Recall@K / MRR / NDCG
- 生成: LLM-as-Judge (Faithfulness + Relevancy)
- 诊断: 分桶定位瓶颈(检索 vs 生成)
"""

import math
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class EvalCase:
    question: str
    relevant_ids: set           # 标注的相关 doc_id 集合(ground truth)
    retrieved_ids: list         # 系统检索返回的有序 doc_id 列表
    answer: str
    retrieved_texts: list       # 与 retrieved_ids 对应的文本(供 judge 用)


@dataclass
class RetrievalMetrics:
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    mrr: float
    ndcg_at_5: float


@dataclass
class GenerationMetrics:
    faithfulness: float         # 答案是否忠于检索内容 [0,1]
    relevancy: float            # 答案是否切题 [0,1]


@dataclass
class DiagnosisReport:
    total: int
    retrieval_good_gen_good: int
    retrieval_good_gen_bad: int     # 生成是瓶颈
    retrieval_bad_gen_good: int     # 检索是瓶颈
    retrieval_bad_gen_bad: int
    bottleneck: str                 # "retrieval" / "generation" / "both" / "none"


class RAGEvaluator:
    def __init__(
        self,
        llm_judge_fn: Callable[[str, str, str], tuple],
        recall_threshold: float = 0.5,
        gen_threshold: float = 0.7,
    ):
        self.llm_judge_fn = llm_judge_fn
        self.recall_threshold = recall_threshold
        self.gen_threshold = gen_threshold

    # ---------- 检索指标 ----------
    @staticmethod
    def recall_at_k(relevant: set, retrieved: list, k: int) -> float:
        if not relevant:
            return 0.0
        top_k = retrieved[:k]
        hit = len(set(top_k) & relevant)
        return hit / len(relevant)

    @staticmethod
    def mrr(relevant: set, retrieved: list) -> float:
        for i, did in enumerate(retrieved, start=1):
            if did in relevant:
                return 1.0 / i
        return 0.0

    @staticmethod
    def ndcg_at_k(relevant: set, retrieved: list, k: int) -> float:
        """简化版: 二值相关性(相关=1,不相关=0)"""
        dcg = 0.0
        for i, did in enumerate(retrieved[:k], start=1):
            if did in relevant:
                dcg += 1.0 / math.log2(i + 1)
        # iDCG: 所有相关文档都排在最前
        ideal_hits = min(len(relevant), k)
        idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
        return dcg / idcg if idcg > 0 else 0.0

    def eval_retrieval(self, cases: list[EvalCase]) -> RetrievalMetrics:
        r1 = sum(self.recall_at_k(c.relevant_ids, c.retrieved_ids, 1) for c in cases) / len(cases)
        r3 = sum(self.recall_at_k(c.relevant_ids, c.retrieved_ids, 3) for c in cases) / len(cases)
        r5 = sum(self.recall_at_k(c.relevant_ids, c.retrieved_ids, 5) for c in cases) / len(cases)
        mrr_val = sum(self.mrr(c.relevant_ids, c.retrieved_ids) for c in cases) / len(cases)
        ndcg = sum(self.ndcg_at_k(c.relevant_ids, c.retrieved_ids, 5) for c in cases) / len(cases)
        return RetrievalMetrics(
            recall_at_1=r1, recall_at_3=r3, recall_at_5=r5,
            mrr=mrr_val, ndcg_at_5=ndcg,
        )

    # ---------- 生成指标 ----------
    def eval_generation(self, cases: list[EvalCase]) -> GenerationMetrics:
        faith_sum, rel_sum = 0.0, 0.0
        for c in cases:
            context = "\n".join(c.retrieved_texts[:5])
            faith, rel = self.llm_judge_fn(c.question, context, c.answer)
            faith_sum += faith
            rel_sum += rel
        n = len(cases)
        return GenerationMetrics(faithfulness=faith_sum / n, relevancy=rel_sum / n)

    # ---------- 诊断分析 ----------
    def diagnose(self, cases: list[EvalCase]) -> DiagnosisReport:
        buckets = {
            "gg": 0, "gb": 0, "bg": 0, "bb": 0,
        }
        for c in cases:
            r = self.recall_at_k(c.relevant_ids, c.retrieved_ids, 5)
            _, rel = self.llm_judge_fn(c.question, "\n".join(c.retrieved_texts[:5]), c.answer)
            r_good = r >= self.recall_threshold
            g_good = rel >= self.gen_threshold
            if r_good and g_good:
                buckets["gg"] += 1
            elif r_good and not g_good:
                buckets["gb"] += 1
            elif not r_good and g_good:
                buckets["bg"] += 1
            else:
                buckets["bb"] += 1

        total = len(cases)
        # 瓶颈判定: 哪一类占比最高
        if buckets["gb"] > max(buckets["gg"], buckets["bg"], buckets["bb"]):
            bottleneck = "generation"
        elif buckets["bg"] >= max(buckets["gg"], buckets["gb"], buckets["bb"]):
            bottleneck = "retrieval"
        elif buckets["bb"] > max(buckets["gg"], buckets["gb"], buckets["bg"]):
            bottleneck = "both"
        else:
            bottleneck = "none"

        return DiagnosisReport(
            total=total,
            retrieval_good_gen_good=buckets["gg"],
            retrieval_good_gen_bad=buckets["gb"],
            retrieval_bad_gen_good=buckets["bg"],
            retrieval_bad_gen_bad=buckets["bb"],
            bottleneck=bottleneck,
        )


# ---------- Mock 演示 ----------
if __name__ == "__main__":
    def mock_judge(question: str, context: str, answer: str) -> tuple:
        # 简化: 答案含问句关键词 → 高 relevancy;答案词都在 context 中 → 高 faithfulness
        q_words = set(question.lower().split())
        a_words = set(answer.lower().split())
        c_words = set(context.lower().split())
        relevancy = len(q_words & a_words) / (len(q_words) + 1e-9)
        faithfulness = len(a_words & c_words) / (len(a_words) + 1e-9)
        return min(faithfulness, 1.0), min(relevancy, 1.0)

    cases = [
        EvalCase(
            question="什么是 RAG",
            relevant_ids={"d1", "d2"},
            retrieved_ids=["d1", "d3", "d2", "d4", "d5"],
            answer="RAG 是检索增强生成",
            retrieved_texts=["RAG 是检索增强生成", "BM25 是关键词检索", "RAG 五步流水线", "x", "y"],
        ),
        EvalCase(
            question="BM25 算法原理",
            relevant_ids={"d3"},
            retrieved_ids=["d3", "d1", "d2"],
            answer="BM25 基于 TF-IDF 改进",
            retrieved_texts=["BM25 基于 TF-IDF 改进", "RAG 是检索增强生成", "RAG 五步"],
        ),
        EvalCase(
            question="HNSW 索引",
            relevant_ids={"d5"},
            retrieved_ids=["d1", "d2", "d3", "d4", "d5"],   # 相关文档排在第5,检索差
            answer="HNSW 是图索引",
            retrieved_texts=["RAG", "BM25", "Cross-Encoder", "RRF", "HNSW 是图索引"],
        ),
    ]

    ev = RAGEvaluator(mock_judge)
    print("=== 检索指标 ===")
    print(ev.eval_retrieval(cases))
    print("\n=== 生成指标 ===")
    print(ev.eval_generation(cases))
    print("\n=== 诊断报告 ===")
    print(ev.diagnose(cases))
```

**面试评分要点**:
- ✅ Recall@K 公式正确 `|R∩A_K|/|R|`,空 relevant 保护
- ✅ MRR 只看第一个命中,`1/rank`,适合"用户只看第一条"场景
- ✅ NDCG 用 `1/log2(i+1)` 位置衰减,iDCG 归一化;简化版二值相关性,生产可扩展为分级
- ✅ 诊断分桶(检索好生成差 / 检索差生成好)直接定位瓶颈,这是 RAG 调优的核心方法论
- ⚠️ 追问 1: LLM-as-Judge 有什么偏差? 答: (1) 偏好长答案;(2) 自我偏好(同模型评分偏高);(3) 顺序偏差。缓解: 交换顺序、用强模型评弱模型、加 rubric 约束
- ⚠️ 追问 2: 没有人工标注的相关文档怎么办? 答: (1) 用 LLM 生成 pseudo-relevant 标注;(2) 用点击日志做弱监督;(3) 跑 A/B 让用户隐式投票
- ⚠️ 追问 3: NDCG 和 MRR 的适用场景? 答: MRR 适合"唯一正确答案"(FAQ);NDCG 适合"多个相关文档有不同相关度"(搜索);RAG 系统通常 NDCG 更全面

</details>

---

### 手撕题 6: 实现 GraphRAG(实体抽取 + 关系抽取 + 社区检测 + 局部/全局查询)

<details>
<summary>点击查看参考答案</summary>

**思路口述**:
- 离线: LLM 抽取 (实体, 关系, 实体) 三元组 → 构图 → Louvain 社区检测 → 每个社区生成摘要。
- 在线局部查询: 找问题相关实体 → 取其邻居子图 → 用子图+社区摘要回答。
- 在线全局查询: 把所有社区摘要 map-reduce 式汇总,适合"全局总结"类问题。

```python
"""
GraphRAG 简化实现
- 离线: 实体/关系抽取 → 构图 → Louvain 社区检测 → 社区摘要
- 在线: 局部查询(实体子图) / 全局查询(社区摘要 map-reduce)
"""

from dataclasses import dataclass, field
from typing import Callable
from collections import defaultdict


@dataclass
class Entity:
    name: str
    entity_type: str
    description: str


@dataclass
class Relation:
    head: str          # 实体名
    tail: str          # 实体名
    relation: str
    description: str


@dataclass
class Community:
    community_id: int
    entities: list           # 实体名列表
    summary: str = ""


class GraphRAG:
    def __init__(
        self,
        llm_fn: Callable[[str], str],
        resolution: float = 1.0,       # Louvain 分辨率参数
    ):
        self.llm_fn = llm_fn
        self.resolution = resolution
        self.entities: dict[str, Entity] = {}
        self.relations: list[Relation] = []
        self.adjacency: dict[str, set] = defaultdict(set)
        self.communities: list[Community] = []
        self.entity_to_community: dict[str, int] = {}

    # ---------- 离线建库 ----------
    def build_from_documents(self, documents: list[str]) -> None:
        # 1. 实体/关系抽取
        for doc in documents:
            ents, rels = self._extract_triples(doc)
            for e in ents:
                if e.name not in self.entities:
                    self.entities[e.name] = e
            self.relations.extend(rels)
            for r in rels:
                self.adjacency[r.head].add(r.tail)
                self.adjacency[r.tail].add(r.head)

        # 2. 社区检测(Louvain 简化版)
        communities = self._louvain(self.adjacency)
        for cid, ent_list in communities.items():
            comm = Community(community_id=cid, entities=ent_list)
            self.communities.append(comm)
            for e in ent_list:
                self.entity_to_community[e] = cid

        # 3. 社区摘要
        for comm in self.communities:
            ent_descriptions = "; ".join(
                f"{e}({self.entities[e].entity_type})" for e in comm.entities if e in self.entities
            )
            rel_in_comm = [
                r for r in self.relations
                if r.head in comm.entities and r.tail in comm.entities
            ]
            rel_text = "; ".join(f"{r.head}-{r.relation}->{r.tail}" for r in rel_in_comm[:20])
            comm.summary = self._summarize_community(ent_descriptions, rel_text)

    def _extract_triples(self, text: str) -> tuple:
        """调用 LLM 抽取实体和关系(简化 mock)"""
        prompt = (
            "从以下文本抽取实体和关系,输出格式:\n"
            "ENTITIES: 实体名|类型|描述; 实体名|类型|描述\n"
            "RELATIONS: 头实体|关系|尾实体|描述; ...\n\n"
            f"文本: {text}"
        )
        out = self.llm_fn(prompt)
        entities, relations = [], []
        for line in out.splitlines():
            if line.startswith("ENTITIES:"):
                for item in line[len("ENTITIES:"):].strip().split(";"):
                    item = item.strip()
                    if not item:
                        continue
                    parts = item.split("|")
                    if len(parts) >= 3:
                        entities.append(Entity(parts[0].strip(), parts[1].strip(), parts[2].strip()))
            elif line.startswith("RELATIONS:"):
                for item in line[len("RELATIONS:"):].strip().split(";"):
                    item = item.strip()
                    if not item:
                        continue
                    parts = item.split("|")
                    if len(parts) >= 3:
                        desc = parts[3].strip() if len(parts) > 3 else ""
                        relations.append(Relation(parts[0].strip(), parts[2].strip(), parts[1].strip(), desc))
        return entities, relations

    def _summarize_community(self, entities_text: str, rel_text: str) -> str:
        prompt = f"请用一段话概括以下实体和关系构成的主题:\n实体: {entities_text}\n关系: {rel_text}"
        return self.llm_fn(prompt)

    # ---------- Louvain 简化实现 ----------
    def _louvain(self, adjacency: dict) -> dict:
        """
        简化版 Louvain: 贪心模块度优化
        生产环境用 networkx.community.louvain_communities
        这里用标签传播近似
        """
        nodes = list(adjacency.keys())
        if not nodes:
            return {}
        labels = {n: i for i, n in enumerate(nodes)}

        changed = True
        iterations = 0
        while changed and iterations < 10:
            changed = False
            iterations += 1
            for n in nodes:
                neighbor_labels = [labels[m] for m in adjacency[n] if m in labels]
                if not neighbor_labels:
                    continue
                # 选邻居中最多的标签
                from collections import Counter
                most_common = Counter(neighbor_labels).most_common(1)[0][0]
                if labels[n] != most_common:
                    labels[n] = most_common
                    changed = True

        # 聚合同标签节点
        communities: dict[int, list] = defaultdict(list)
        for n, lbl in labels.items():
            communities[lbl].append(n)
        return dict(enumerate(communities.values()))

    # ---------- 在线查询 ----------
    def query_local(self, question: str, top_k_entities: int = 3, hop: int = 1) -> str:
        """局部查询: 找相关实体 → 取邻居子图 → 回答"""
        related_entities = self._find_entities(question, top_k_entities)
        subgraph_entities = set(related_entities)
        for _ in range(hop):
            new = set()
            for e in subgraph_entities:
                new.update(self.adjacency.get(e, set()))
            subgraph_entities.update(new)

        sub_relations = [
            r for r in self.relations
            if r.head in subgraph_entities and r.tail in subgraph_entities
        ]
        ent_text = "; ".join(
            f"{e}({self.entities[e].entity_type}): {self.entities[e].description}"
            for e in subgraph_entities if e in self.entities
        )
        rel_text = "\n".join(f"- {r.head} {r.relation} {r.tail}: {r.description}" for r in sub_relations[:30])

        prompt = (
            f"基于以下实体和关系子图回答问题。\n"
            f"实体:\n{ent_text}\n\n关系:\n{rel_text}\n\n问题: {question}\n答案:"
        )
        return self.llm_fn(prompt)

    def query_global(self, question: str) -> str:
        """全局查询: map 每个社区摘要 → reduce 汇总"""
        # Map: 每个社区对问题给出部分答案
        partial_answers = []
        for comm in self.communities:
            prompt = (
                f"基于以下社区摘要,回答问题(若不相关请回复'N/A'):\n"
                f"社区摘要: {comm.summary}\n问题: {question}"
            )
            ans = self.llm_fn(prompt)
            if "N/A" not in ans:
                partial_answers.append(f"[社区{comm.community_id}] {ans}")

        # Reduce: 汇总所有部分答案
        if not partial_answers:
            return self.llm_fn(f"直接回答: {question}")
        combined = "\n\n".join(partial_answers)
        prompt = f"综合以下多个视角的信息,给出最终答案:\n{combined}\n\n问题: {question}\n最终答案:"
        return self.llm_fn(prompt)

    def _find_entities(self, question: str, top_k: int) -> list:
        """简化: 用问题中出现的实体名匹配"""
        return [e for e in self.entities if e in question][:top_k]


# ---------- Mock 演示 ----------
if __name__ == "__main__":
    def mock_llm(prompt: str) -> str:
        if "抽取实体" in prompt:
            return (
                "ENTITIES: RAG|技术|检索增强生成; Embedding|技术|向量化; 向量库|组件|存储向量\n"
                "RELATIONS: RAG|使用|Embedding|; Embedding|存入|向量库|"
            )
        if "概括" in prompt:
            return "该社区围绕 RAG 的向量检索基础组件。"
        if "社区摘要" in prompt:
            return "RAG 使用 Embedding,Embedding 存入向量库。"
        if "综合" in prompt:
            return "综合各社区信息:RAG 全链路包括向量化和存储。"
        return "RAG 通过 Embedding 和向量库实现检索。"

    graph = GraphRAG(mock_llm)
    graph.build_from_documents(["RAG 使用 Embedding 技术,Embedding 结果存入向量库。"])
    print(f"实体数: {len(graph.entities)}, 关系数: {len(graph.relations)}, 社区数: {len(graph.communities)}")
    print(f"\n[局部查询] {graph.query_local('RAG 如何做向量化?')}")
    print(f"\n[全局查询] {graph.query_global('RAG 系统的整体架构?')}")
```

**面试评分要点**:
- ✅ 三元组抽取 + 构图 + 社区检测 + 摘要 四步离线流水线完整
- ✅ 局部查询走"实体子图"路径,适合具体问题;全局查询走"社区摘要 map-reduce",适合总结性问题
- ✅ Louvain 用标签传播近似(手撕可接受),注明生产用 networkx
- ✅ 社区摘要在离线阶段预计算,在线只做检索+拼接,成本可控
- ⚠️ 追问 1: GraphRAG vs 传统 RAG 的核心区别? 答: 传统 RAG 按"文本相似"检索独立 chunk;GraphRAG 按"实体关系"检索结构化子图,天然支持多跳推理,但建图成本高
- ⚠️ 追问 2: 社区检测的分辨率参数怎么调? 答: resolution 越大社区越多越小(细粒度),越小社区越少越大(粗粒度);经验值 1.0,根据实体规模调
- ⚠️ 追问 3: 全局查询 map-reduce 的成本怎么控? 答: (1) 社区摘要预计算并缓存;(2) 只对 top-K 相关社区做 map;(3) 用小模型做 map,大模型做 reduce

</details>

---

## 三、综合面试题(10 道)

> **答题节奏**: 每题先给"一句话结论",再展开"原理 + 代码/案例 + 追问应对"。面试官最怕"绕半天没结论"。

### 综合题 1: 从用户提问到最终答案,RAG 系统经过哪些阶段?每阶段的"可优化旋钮"是什么?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 五段式流水线 `分块 → Embedding → 检索 → Rerank → 生成`,每段都有 2-3 个关键旋钮。

**展开**:

| 阶段 | 可优化旋钮 | 对应 Day |
|------|-----------|---------|
| 分块 | chunk_size / overlap / 语义分块 vs 固定窗口 / 层级分块 | Day8 |
| Embedding | 模型选型(中英/领域) / 维度 / 归一化 / 多向量 | Day8/10 |
| 检索 | top-K / 索引类型(HNSW/IVF) / 混合检索 / 路由 | Day9/10 |
| Rerank | Cross-Encoder 模型 / rerank_top_n / 阈值过滤 | Day8 |
| 生成 | prompt 模板 / 引用格式 / 上下文排序 / 兜底策略 | Day11 |

**追问应对**:
- "哪一段投入产出比最高?" → Rerank。一段 Cross-Encoder 代码就能把准确率提 10-15%,成本只增加几十毫秒。
- "哪一段最难调?" → 分块。chunk 太大召回噪声多,太小语义割裂;没有银弹,必须按文档类型 A/B 测试。

</details>

### 综合题 2: Agentic RAG 的"迭代检索"什么时候该停?如何防止无限循环?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 四道刹车 —— 跳数上限、无新进展、置信度达标、Token 预算,任一触发即停。

**展开**:
- **跳数上限**: `max_hops=3`,经验值,多数问题 2 跳内能解。
- **无新进展**: 连续两跳没有新增有效 chunk(去重后),说明检索饱和。
- **置信度达标**: LLM 评估当前证据足够回答(`confidence > 0.7`),不必继续。
- **Token 预算**: 累积 context 超预算,强制进入生成。

**代码骨架**(见手撕题 2):
```python
if state.hops >= self.max_hops:
    state.status = "max_hops"
elif len(fresh) < self.min_new_chunks:
    state.status = "no_progress"
elif state.confidence >= self.confidence_threshold:
    state.status = "ok"
```

**追问应对**:
- "为什么不直接用向量相似度判断够不够?" → 向量相似度只衡量"query 和 chunk 像",不衡量"chunk 能不能答";需要 LLM 做语义充分性判断。
- "无限循环的代价?" → 每跳一次 LLM 调用 + 检索,成本和延迟线性增长;3 跳以上用户体验明显劣化。

</details>

### 综合题 3: 混合检索中 RRF 为什么比加权融合更常用?k=60 怎么来的?

<details>
<summary>点击查看参考答案</summary>

**一句话**: RRF 只用 rank 不用 score,天然规避多路分值尺度不一致;k=60 是原论文经验值,对大多数场景鲁棒。

**展开**:
- **问题**: 向量相似度在 [0,1],BM25 分值可能在 [0, 50],直接加权 `α*vec + (1-α)*bm25` 需要 normalize 且 α 难调。
- **RRF 公式**: `score(d) = Σ_i 1/(k + rank_i(d))`,只用排名,分值天然归一到 `(0, 1/k]`。
- **k 的含义**: k 越大,排名差异越被平滑(更民主);k 越小,头部权重越集中。k=60 来自 SIGIR 2009 原论文,在大规模 web 搜索验证稳健。
- **实践**: 多数系统直接用 60;若检索路数多(>3 路)或候选少(<20),可调到 30-100。

**追问应对**:
- "三路检索时 RRF 还适用吗?" → 适用,公式天然支持 N 路,每路贡献 `1/(k+rank)` 累加。
- "RRF 的缺点?" → 忽略原始分值差异:排名第 1 的 BM25(分=50)和排名第 1 的向量(分=0.51)贡献相同,可能丢失"强相关"信号;可用 Weighted RRF 缓解。

</details>

### 综合题 4: Lost-in-the-Middle 现象是什么?如何在 RAG 上下文组装中规避?

<details>
<summary>点击查看参考答案</summary>

**一句话**: LLM 对长上下文中段位置的注意力衰减,首尾信息利用率高,中间低;规避方式是"高优先放首尾,低优先放中间"。

**展开**:
- **现象**: Stanford 2023 论文发现,无论模型上下文窗口多大,放在中间的关键信息被正确利用的概率显著低于首尾。
- **RAG 场景**: 若把最相关的 chunk 放在 context 第 3 位(中间),反而不如放第 1 位或最后 1 位效果好。
- **规避策略**:
  1. **首尾重排**: 按 Rerank 分排序后,偶数位放头部、奇数位反转放尾部(见手撕题 4)。
  2. **控制 context 长度**: 不超过 8-10 个 chunk,缩短"中间区域"。
  3. **关键信息显式标记**: 用 `<important>` 标签或重复放置关键 chunk。
- **代码**:
  ```python
  def lost_in_middle_reorder(blocks):
      head, tail = [], []
      for i, b in enumerate(blocks):
          (head if i % 2 == 0 else tail).append(b)
      return head + list(reversed(tail))
  ```

**追问应对**:
- "所有模型都有这个问题吗?" → 长上下文(>8K)模型更明显;经过 position-interpolation 或 YaRN 训练的模型有缓解,但仍建议重排。
- "为什么不直接只放 top-3?" → 减少 chunk 会损失 Recall;重排是在"保留信息量"和"规避位置偏差"之间的零成本折中。

</details>

### 综合题 5: RAG 系统的评估指标分哪几层?各自关注什么?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 三层 —— 检索层(Recall/MRR/NDCG)、生成层(Faithfulness/Relevancy)、端到端层(用户满意度/延迟/成本)。

**展开**:

| 层 | 指标 | 公式 | 关注点 |
|----|------|------|--------|
| 检索 | Recall@K | `|R∩A_K|/|R|` | 相关文档有没有进 top-K |
| 检索 | MRR | `1/rank_first_hit` | 第一个相关文档排第几 |
| 检索 | NDCG@K | `DCG/iDCG`,`DCG=Σ rel_i/log2(i+1)` | 排序质量(带位置衰减) |
| 生成 | Faithfulness | LLM 判断答案是否忠于检索 | 防幻觉 |
| 生成 | Relevancy | LLM 判断答案是否切题 | 防答非所问 |
| 端到端 | 用户满意度 | 点赞率/重写率 | 真实体验 |
| 端到端 | 延迟 P95 | 检索+生成总耗时 | 体验下限 |
| 端到端 | 成本 | 每次查询 $ | 商业可行性 |

**追问应对**:
- "检索好但生成差怎么诊断?" → 看 Faithfulness 低但 Recall 高 → 生成是瓶颈,调 prompt 或换模型(见手撕题 5 诊断分桶)。
- "没有人工标注怎么评 Recall?" → (1) LLM 生成 pseudo-relevant;(2) 点击日志弱监督;(3) 跑 A/B 对比相对指标。

</details>

### 综合题 6: 向量数据库选 HNSW 还是 IVF?十亿级数据怎么选?

<details>
<summary>点击查看参考答案</summary>

**一句话**: HNSW 查询快但内存大,适合百万级且低延迟场景;IVF+PQ 内存省,适合十亿级且可接受召回略降。

**展开**:

| 维度 | HNSW | IVF + PQ |
|------|------|---------|
| 查询复杂度 | `O(log n)` | `O(nlist + nprobe)` |
| 内存 | 高(存全精度向量+图) | 低(PQ 压缩到 m 字节) |
| 召回率 | 高(>95%@10) | 中(85-90%@10,可调) |
| 构建速度 | 慢(逐点插入) | 快(聚类一次) |
| 增量更新 | 支持但有代价 | 支持(重新聚类) |
| 适用规模 | <1000 万 | 1 亿 - 100 亿 |

**十亿级方案**:
1. **IVF + PQ + HNSW 混合**: 用 HNSW 加速 IVF 的 coarse quantizer 查找(Meta Faiss 方案)。
2. **分片**: 按业务维度(时间/地域)水平分片,每片独立索引,并行检索后合并。
3. **分级存储**: 热数据全精度 HNSW,冷数据 PQ 压缩 + 磁盘 IVF。
4. **GPU 加速**: Faiss GPU 版做 batch 检索,吞吐提升 10-50x。

**追问应对**:
- "HNSW 的 M 和 ef_construction 怎么调?" → M 控制图度数(16-48),大则准但费内存;ef_construction 控制建图质量(200-500),大则慢但召回高。
- "PQ 的 m 怎么选?" → m 越大压缩率越低但精度高;经验: 128 维向量用 m=16(每段 8 维),压缩 16 倍,召回损失 <5%。

</details>

### 综合题 7: GraphRAG 相比传统 RAG 解决了什么问题?代价是什么?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 解决多跳推理和全局总结问题;代价是建图成本高、更新慢、存储翻倍。

**展开**:
- **解决的问题**:
  1. **多跳推理**: "A 影响 B,B 影响 C" 类问题,传统 RAG 检索到的 chunk 可能只含 A→B,漏掉 C;GraphRAG 沿关系边走能拿到完整链路。
  2. **全局总结**: "整个文档集的主题是什么" 类问题,传统 RAG 检索局部 chunk 无法概括;GraphRAG 的社区摘要天然适合。
  3. **实体消歧**: 同名实体在不同 chunk 中,图结构能通过关系区分。
- **代价**:
  1. **建图成本**: 每个文档都要 LLM 抽取三元组,成本是传统 RAG 的 5-10 倍。
  2. **更新慢**: 新增文档要重新抽取实体、可能影响社区结构,增量更新复杂。
  3. **存储翻倍**: 图数据 + 社区摘要 + 原始 chunk,存储是传统 RAG 的 2-3 倍。
  4. **查询复杂**: 局部/全局查询路径不同,路由策略更复杂。

**适用场景**:
- 适合: 知识密集、多跳推理、文档间关系丰富(法律/医疗/金融研报)。
- 不适合: 知识更新频繁、查询以事实检索为主(电商 FAQ/新闻)。

**追问应对**:
- "GraphRAG 和 Agentic RAG 的多跳有什么区别?" → GraphRAG 是"实体空间"多跳(沿图边走);Agentic RAG 是"查询空间"多跳(改写 query 再检索)。可叠加: Agentic RAG 路由到 GraphRAG 做图多跳。
- "如何降低建图成本?" → (1) 只对长文档建图,短文档走传统 RAG;(2) 用小模型抽取三元组,大模型只做社区摘要;(3) 增量建图,只处理新增文档。

</details>

### 综合题 8: Context Engineering 中,如何决定"谁进上下文,谁被丢掉"?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 优先级排序 + 预算分配 —— 系统提示 > 当前问题 > 最近历史 > 高相关检索块 > 旧历史 > 低相关检索块,按预算从高到低装填。

**展开**:
- **优先级来源**:
  - 系统提示: 不可丢(定义 Agent 行为)。
  - 当前问题: 不可丢(用户意图)。
  - 历史: 时间衰减(越近越重要) + 角色权重(用户比 assistant 重要,因含意图)。
  - 检索块: Rerank 分数(越高越重要)。
- **预算分配**(见手撕题 4):
  ```
  budget = max_total - reserve_answer
  system = 10%  history = 30%  retrieved = 60%
  ```
- **丢弃策略**:
  1. 低分检索块直接截断(最常用)。
  2. 旧历史用 LLM 压缩成摘要(省空间但有损)。
  3. 滑动窗口只保留最近 K 轮(简单,适合长对话)。
- **进阶**: 动态预算 —— 简单问题给检索块少分(20%),复杂多跳问题给检索块多分(70%),由 query 分类器决定。

**追问应对**:
- "压缩 vs 截断怎么选?" → 压缩保留信息但慢且有损,适合"长对话历史";截断快且确定,适合"检索块"——块之间无强依赖,丢掉不致命。
- "answer 预留多少?" → 简单 QA 500 token,代码生成 2000,长文摘要 3000;根据任务类型预设。

</details>

### 综合题 9: 面试官问"你的 RAG 项目遇到过什么线上问题,怎么解决的?",如何用 STAR 回答?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 用 STAR 结构 —— Situation(场景) + Task(任务) + Action(动作) + Result(结果),结果必须量化。

**模板回答**(以"检索召回率低"为例):

> **Situation**: 我们做的是企业知识库 RAG,文档约 50 万篇,涵盖产品手册、FAQ、工单。上线初期用户反馈"答非所问",排查发现 top-5 召回率只有 62%。
>
> **Task**: 我的职责是在不显著增加延迟(P95 < 2s)的前提下,把召回率提到 85%+。
>
> **Action**: 分三步 ——
> 1. **诊断**: 用 200 条人工标注评测集跑评估,发现 Recall@5=62% 但 MRR=0.45,说明"相关文档在但排得靠后",问题在排序而非检索。
> 2. **优化**: (a) 加 Cross-Encoder Rerank(从 top-20 重排到 top-5);(b) 引入 BM25+向量 RRF 融合,解决纯向量检索对精确关键词(产品型号、错误码)的漏召;(c) 分块从固定 300 字改为按章节语义分块。
> 3. **验证**: A/B 测试两周,实验组 vs 对照组。
>
> **Result**: Recall@5 从 62% 提到 88%,MRR 从 0.45 提到 0.71;用户"答非所问"反馈下降 73%;P95 延迟从 1.8s 到 1.95s,仍在预算内。

**关键技巧**:
- 数字必须具体(62% → 88%,不是"提升了很多")。
- Action 要体现"诊断 → 优化 → 验证"闭环,不是"我加了 Rerank 就好了"。
- 准备 2-3 个不同类型的问题(召回率、延迟、幻觉、成本),应对追问。

**追问应对**:
- "为什么不用更大的 Embedding 模型?" → 试过,从 768 维换 1536 维,召回只提 2% 但内存翻倍,投入产出比不如 Rerank。
- "A/B 测试怎么设计的?" → 流量 50/50 分流,指标是 Recall@5 + 用户点赞率 + 重写率,跑两周确保统计显著。

</details>

### 综合题 10: 如果让你从零设计一个支持千万级文档、日查询千万次的 RAG 系统,架构怎么画?

<details>
<summary>点击查看参考答案</summary>

**一句话**: 三段式架构 —— 离线建库(分片索引)+ 在线查询(检索+生成)+ 评估闭环(监控+迭代)。

**架构图**:

```
┌──────────────────────── 离线建库 ────────────────────────┐
│                                                          │
│  文档源 → ETL → 分块 → Embedding(GPU batch) → 向量库    │
│              ↓                                            │
│         BM25 倒排索引(并行)                              │
│              ↓                                            │
│         索引分片(按时间/业务维度,每片 100-500 万)       │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────── 在线查询 ────────────────────────┐
│                                                          │
│  用户Query                                                │
│    ↓                                                      │
│  Query 改写/扩展(可选 LLM)                              │
│    ↓                                                      │
│  ┌─────────────┬──────────────┐                          │
│  │ 向量检索     │ BM25 检索     │  (并行,各取 top-50)    │
│  │(HNSW 分片)  │(倒排分片)    │                          │
│  └──────┬──────┴──────┬───────┘                          │
│         └──────┬──────┘                                  │
│           RRF 融合                                        │
│              ↓                                            │
│  Cross-Encoder Rerank(top-20 → top-5)                    │
│              ↓                                            │
│  Context Manager(预算+压缩+Lost-in-Middle)              │
│              ↓                                            │
│  LLM 生成(带引用溯源)                                   │
│              ↓                                            │
│  答案 + citations                                         │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────── 评估闭环 ────────────────────────┐
│                                                          │
│  在线监控: 延迟 P95 / 召回率采样 / 用户反馈 / 成本        │
│     ↓                                                    │
│  离线评测: 每周跑 1000 条标注集 → Recall/MRR/Faithfulness │
│     ↓                                                    │
│  迭代: 调参 / 换模型 / 补标注 / 重建索引                  │
└──────────────────────────────────────────────────────────┘
```

**关键设计决策**:
1. **分片**: 按"业务域 + 时间"分片,避免单索引过大;查询时按 query 路由到相关分片,减少扫描量。
2. **混合检索**: 向量 + BM25 并行,RRF 融合,兼顾语义和关键词。
3. **缓存**: Query Embedding 缓存(同问不重算)+ 答案缓存(高相似 query 复用)。
4. **降级**: 检索超时 → 降级到 BM25 单路;LLM 超时 → 返回检索结果 + 模板拼接。
5. **成本控制**: Rerank 只对 top-20 做;LLM 用小模型兜底,大模型只处理高价值查询。

**追问应对**:
- "千万 QPS 怎么扛?" → 检索层无状态,水平扩容;向量库用读副本;LLM 走 API 限流 + 队列削峰。
- "如何保证数据更新后检索及时?" → 增量索引(新文档实时入库)+ 全量重建(夜间低峰,每周一次)双轨制。

</details>

---

## Week 2 知识串联图:数据流全景

```
用户提问
   │
   ├─[Day11] Query 分析 + 改写(可选 LLM)
   │
   ▼
┌─────────────────────────────────────────────────┐
│           检索层(可路由/可迭代)                 │
│                                                 │
│  [Day9] 路由决策 ─┬─ 向量检索 [Day8/10]          │
│                  ├─ BM25 检索  [Day10]          │
│                  ├─ 图谱检索  [Day9 GraphRAG]   │
│                  └─ 直接答    (跳过检索)        │
│                                                 │
│  [Day10] RRF 融合 → 候选 top-20                 │
│  [Day8]  Cross-Encoder Rerank → top-5           │
│                                                 │
│  [Day9]  评估: 够答吗? ──No──→ 改写query再检索  │
│                  │                              │
│                 Yes                             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           上下文组装层                          │
│                                                 │
│  [Day11] Token 预算分配(system/history/ret/ans) │
│  [Day11] 压缩 / 截断 / 滑动窗口                 │
│  [Day11] Lost-in-the-Middle 重排                │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           生成层                                │
│                                                 │
│  [Day8]  Prompt 模板(带引用格式约束)           │
│  [Day8]  LLM 生成 + [n] 引用标注                │
│  [Day8]  引用溯源(答案 [n] ↔ context chunk)    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│           评估闭环                              │
│                                                 │
│  [Day12] 在线: 延迟 / 用户反馈 / 成本监控       │
│  [Day12] 离线: Recall@K / MRR / NDCG            │
│  [Day12]       Faithfulness / Relevancy (Judge) │
│  [Day12] 诊断: 检索瓶颈 vs 生成瓶颈             │
│  [Day13] 迭代: 调参 → 重建索引 → 再评测         │
└─────────────────────────────────────────────────┘
```

---

## Week 2 易错点总复习(10 项)

> 这些是六天学习中反复出现的"概念陷阱",面试中答错会被直接扣分。

| # | 易错点 | 错误认知 | 正确理解 |
|---|--------|---------|---------|
| 1 | Rerank 和检索的关系 | "Rerank 是另一种检索" | Rerank 是对检索结果的**精排**,不扩大候选池,只重排 top-K |
| 2 | RRF 的 k 值 | "k 越小越好(头部越集中)" | k=60 是经验值,**过小**会让低排名完全无贡献,丢失长尾相关文档 |
| 3 | BM25 的 b 参数 | "b 控制 TF 饱和" | b 控制**文档长度归一化**(0=不惩罚长文档,1=完全惩罚);k1 才控制 TF 饱和 |
| 4 | Recall@K 和 MRR 的适用场景 | "Recall@K 越高系统越好" | Recall 只看"有没有进 top-K",**不看排序**;FAQ 类需 MRR(用户只看第一条) |
| 5 | NDCG 的相关性分级 | "NDCG 只能二值相关" | 原始 NDCG 支持**分级相关性**(0/1/2/3),手撕简化为二值,生产可扩展 |
| 6 | Agentic RAG 的"迭代" | "迭代越多越好" | 迭代有**成本和漂移风险**,多数问题 1-2 跳即解,max_hops=3 是经验上限 |
| 7 | GraphRAG 的社区摘要 | "社区摘要在查询时生成" | 社区摘要**离线预计算**,在线只检索+拼接;若在线生成,延迟和成本不可控 |
| 8 | Lost-in-the-Middle | "只对 128K 上下文有效" | 即使 4K 上下文也存在位置偏差,**只要 context > 3 个 chunk 就建议重排** |
| 9 | LLM-as-Judge 的偏差 | "LLM 评分客观可信" | LLM 有**长度偏好、自我偏好、顺序偏差**;需交换顺序、用强模型评弱模型、加 rubric |
| 10 | Context 压缩 vs 截断 | "压缩总比截断好" | 压缩有**信息损失且增加延迟**;块间无强依赖时截断更优,历史对话才适合压缩 |

---

## Week 2 自测清单

> **使用方法**: 遮住右侧,逐题口述回答,答完对照。能流畅答出 80% 以上 = Week2 过关。

### 概念题(20 题)

| # | 问题 | 参考答案要点 |
|---|------|------------|
| 1 | RAG 五段式流水线是哪五段? | 分块 → Embedding → 检索 → Rerank → 生成 |
| 2 | 为什么需要 Rerank?向量检索不够吗? | Bi-Encoder 粗排快但精度低;Cross-Encoder 精排贵但准,先粗后精 |
| 3 | Agentic RAG 和 Naive RAG 的核心区别? | Agentic 按"是否够答"决定是否再检索;Naive 一次检索定生死 |
| 4 | 检索路由有哪几种策略? | 关键词路由 / 语义路由 / LLM 分类器路由 / 多路并行 |
| 5 | GraphRAG 用什么算法做社区检测? | Louvain(模块度最大化)/ Leiden(改进版) |
| 6 | HNSW 的查询复杂度? | O(log n),基于多层跳表图 |
| 7 | PQ 压缩的原理? | 把向量切 m 段,每段用码本量化到 1 字节,压缩 m 倍 |
| 8 | 混合检索为什么用 RRF 而非加权融合? | RRF 用 rank 绕过分值尺度不一致,鲁棒 |
| 9 | 十亿级向量库的典型方案? | IVF + PQ + HNSW(加速 coarse quantizer)+ 分片 |
| 10 | Lost-in-the-Middle 是什么? | LLM 对长上下文中段注意力衰减,首尾利用率高 |
| 11 | Context 预算四段分配? | system + history + retrieved + answer(reserve) |
| 12 | 压缩历史的代价? | LLM 调用延迟 + 摘要有信息损失 |
| 13 | Recall@K 的公式? | `|R ∩ A_K| / |R|`,R=相关文档集,A_K=top-K 检索结果 |
| 14 | MRR 适合什么场景? | "唯一正确答案"场景,如 FAQ,用户只看第一条 |
| 15 | NDCG 比 MRR 多了什么? | 位置衰减(`1/log2(i+1)`)+ 支持分级相关性 |
| 16 | LLM-as-Judge 的三个典型偏差? | 长度偏好 / 自我偏好 / 顺序偏差 |
| 17 | RAG 诊断分桶有哪四类? | 检索好生成好 / 检索好生成差 / 检索差生成好 / 都差 |
| 18 | GraphRAG 局部查询和全局查询的区别? | 局部走实体子图(具体问题);全局走社区摘要 map-reduce(总结问题) |
| 19 | 引用溯源的作用? | 防幻觉 + 可验证 + 用户信任 |
| 20 | STAR 叙事的四个字母? | Situation / Task / Action / Result |

### 代码题(6 题)

| # | 问题 | 关键实现点 |
|---|------|-----------|
| 1 | 手撕 RAG 查询引擎 | 五段式 + 引用 `[n]` 双向绑定 + 空检索兜底 |
| 2 | 手撕 Agentic RAG | 状态机 + max_hops + no_progress + confidence 三重刹车 |
| 3 | 手撕混合检索 | BM25 完整公式 + RRF(rank 不分值)+ CE 精排 |
| 4 | 手撕 Context Manager | 四段预算 + 三种策略 + Lost-in-Middle 重排 |
| 5 | 手撕 RAG 评估 | Recall/MRR/NDCG 公式 + LLM-Judge + 诊断分桶 |
| 6 | 手撕 GraphRAG | 三元组抽取 + 标签传播近似 Louvain + 局部/全局查询 |

### 系统设计题(7 题)

| # | 问题 | 设计要点 |
|---|------|---------|
| 1 | 设计千万级文档 RAG 系统架构 | 三段式(离线建库/在线查询/评估闭环)+ 分片 + 混合检索 + 降级 |
| 2 | 如何把 RAG 召回率从 60% 提到 85%? | 诊断(Recall vs MRR)→ Rerank + RRF 融合 + 语义分块 → A/B 验证 |
| 3 | 如何设计 RAG 的在线监控? | 延迟 P95 / 召回率采样 / 用户反馈率 / 单查询成本 / 错误率 |
| 4 | 如何控制 RAG 系统的成本? | Rerank 只排 top-20 / 答案缓存 / 小模型兜底 / Query 路由跳过检索 |
| 5 | Agentic RAG 何时该迭代,何时该停? | 评估"证据充分性"决定迭代;跳数/无进展/置信度/预算任一触发即停 |
| 6 | GraphRAG 适合什么场景,不适合什么? | 适合多跳推理/全局总结(法律/医疗);不适合频繁更新/事实检索(电商FAQ) |
| 7 | 如何设计 RAG 的 A/B 测试? | 50/50 分流 / 指标(Recall+点赞率+重写率) / 两周统计显著 / 灰度发布 |

---

## 明日预告:Week 3 Day 15 — LangChain 与 LangGraph 深度解析

Week2 我们把 RAG 与 Agent 结合的**原理和手撕**打牢了;Week3 进入**框架与系统设计**阶段,从"自己手撕"过渡到"用框架工程化"。

**Day 15 预习重点**:
1. **LangChain 核心抽象**: Chain / Prompt / Memory / Tool / Agent / LCEL 表达式语法。
2. **LangGraph 状态机**: 为什么从 Chain 升级到 Graph?有环图 vs 无环链,StateGraph 节点/边/条件路由。
3. **LangChain vs LangGraph vs LlamaIndex**: 三大框架对比,各自适用场景。
4. **面试高频**: "LangChain 的 Agent 和你自己手撕的 Agent Loop 有什么区别?什么场景该用框架,什么场景该自己写?"

**预习作业**:
- 跑通 LangChain 一个最小 RAG 示例(不需要 GPU,用 mock LLM 即可)。
- 思考: Week2 手撕的 6 个模块,哪些能直接用 LangChain 替换?哪些框架做不了还得自己写?

---

> **Week2 结语**: 这一周我们从 RAG 全链路到 Agentic RAG,从向量库到上下文工程,从评估到实战规划,最后用手撕代码把六天知识"焊"在了一起。
>
> 面试官真正考的不是"你知不知道 RRF 公式",而是"你能不能在白板上把混合检索写出来,并解释为什么用 RRF 而不是加权融合"。手撕过的代码,才是自己的。
>
> 休息一下,明天开始 Week3 —— 把手撕的能力装进框架,从"能写"到"能工程化交付"。
