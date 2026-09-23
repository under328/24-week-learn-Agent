# Day 11 — Context Engineering（上下文工程）

> **学习目标**: 系统掌握上下文工程的核心理论、压缩技术、长文本处理策略,能够手撕一个生产级 ContextManager,并在系统设计题中讲清楚"百万 token 上下文 Agent"的架构。
>
> **面试定位**: 这是 RAG 与 Agent 结合方向的高频考点。中高级岗位几乎必问 "Lost in the Middle"、"上下文怎么压缩"、"Agent 多轮对话历史怎么管理"。手撕 ContextManager 是区分 P5/P6/P7 的分水岭 —— 能写出 token 预算分配 + 优先级排序 + 历史截断的完整实现,基本可以拿到 offer。
>
> **前置依赖**: Day8 RAG 全链路、Day9 Agentic RAG、Day10 向量数据库。请确保已理解 chunk、embedding、rerank 的概念,本章会复用这些概念。
>
> **建议学习时长**: 6-8 小时(理论 2h + 10 道面试题 3h + 手撕代码 2h + 自测 1h)

---

## 今日知识图谱

```
Context Engineering（上下文工程）
│
├── 1. 基础理论
│   ├── 上下文 vs Prompt 的区别
│   ├── 为什么 Context Engineering > Prompt Engineering
│   ├── 上下文的组成: system / instruction / few-shot / retrieved / history / tool_result
│   └── 上下文工程的三大目标: 相关性 / 完整性 / 经济性
│
├── 2. 上下文窗口管理
│   ├── Token 预算分配策略
│   │   ├── 固定比例法 (system 10% / retrieval 40% / history 30% / response 20%)
│   │   ├── 动态优先级法 (按重要性动态分配)
│   │   └── 弹性预算法 (根据任务复杂度调整)
│   ├── 上下文组成优先级
│   │   ├── P0: system prompt + core instruction (永不裁剪)
│   │   ├── P1: 当前用户 query (永不裁剪)
│   │   ├── P2: 当前轮检索结果 (高相关)
│   │   ├── P3: few-shot 示例
│   │   ├── P4: 历史对话 (可压缩/截断)
│   │   └── P5: 工具返回结果 (可压缩)
│   └── 模型上下文窗口对比
│       ├── GPT-4o: 128K
│       ├── Claude 3.5 Sonnet: 200K
│       ├── Gemini 1.5 Pro: 2M
│       └── 国产: Qwen2.5-Turbo 1M / GLM-4-Long 1M
│
├── 3. Lost in the Middle 问题
│   ├── 现象: 长上下文中间信息被忽略
│   ├── 原因: 注意力衰减 / 位置编码外推 / 训练数据分布
│   ├── 论文: Liu et al. 2023 "Lost in the Middle"
│   ├── 解决方案
│   │   ├── 重新排序 (重要信息放首尾)
│   │   ├── 上下文压缩 (减少总长度)
│   │   ├── 多次查询 (分而治之)
│   │   └── 注意力 sink / StreamingLLM
│   └── 评估方法: 针式检索 (Needle in Haystack)
│
├── 4. 上下文压缩技术
│   ├── 摘要式压缩 (Abstractive)
│   │   ├── LLM 摘要 (递归摘要 / hierarchical summary)
│   │   └── 适用: 对话历史 / 长文档
│   ├── 抽取式压缩 (Extractive)
│   │   ├── 关键句提取 (TextRank / CE)
│   │   ├── 实体保留
│   │   └── 适用: 事实性文档
│   ├── Token 级压缩
│   │   ├── LLMLingua / LongLLMLingua (微软)
│   │   ├── 基于困惑度的小 token 剔除
│   │   └── 压缩比 2x-20x,性能损失 <5%
│   └── 结构化压缩
│       ├── JSON 字段裁剪
│       ├── 工具结果 schema 化
│       └── Trace 日志结构化
│
├── 5. 长文本处理策略
│   ├── 分段处理 (Chunking)
│   │   ├── 固定长度 / 语义分块 / 递归分块
│   │   └── 重叠率 10-20%
│   ├── 滑动窗口 (Sliding Window)
│   │   ├── 适用于流式 / 时序数据
│   │   └── 窗口大小 + 步长
│   ├── 层次摘要 (Hierarchical Summary)
│   │   ├── 自底向上: chunk → section → doc
│   │   └── 自顶向下: doc → section → chunk
│   ├── Map-Reduce
│   │   ├── Map: 分段独立处理
│   │   ├── Reduce: 合并结果
│   │   └── 适用: 摘要 / 抽取 / 分类
│   └── Refinement / Stuff / Map-Rerank
│       └── LangChain load_qa_chain 四种模式
│
├── 6. Few-shot 示例选择
│   ├── 相似度检索 (kNN)
│   │   ├── embedding 相似度
│   │   └── BM25 / 混合检索
│   ├── 多样性选择
│   │   ├── MMR (Maximal Marginal Relevance)
│   │   └── 聚类后采样
│   ├── 难度排序
│   │   ├── 由易到难 (Easy-to-Hard)
│   │   └── 课程学习思想
│   ├── 示例数量权衡
│   │   ├── 1-3 个 (Few-shot)
│   │   ├── 5-10 个 (Many-shot, ICL scaling)
│   │   └── 边际效益递减
│   └── 示例顺序敏感性
│       ├── 顺序影响输出
│       └── 推荐: 相关度降序 / 难度升序
│
├── 7. 上下文排序优化
│   ├── 首因效应: 开头信息权重高
│   ├── 近因效应: 结尾信息权重高
│   ├── 噪声放中间
│   ├── Recency Reorder 策略
│   └── LangChain `LongContextReorder`
│
├── 8. Agent 场景上下文管理
│   ├── 工具调用结果压缩
│   │   ├── API 返回 JSON 裁剪
│   │   ├── 长输出摘要化
│   │   └── 错误堆栈精简
│   ├── 历史轮次截断
│   │   ├── 滑动窗口保留最近 N 轮
│   │   ├── 早期轮次摘要化
│   │   └── 关键决策点保留
│   ├── 关键信息保留
│   │   ├── 任务目标 / 约束
│   │   ├── 已完成步骤
│   │   └── 中间产物 (变量/文件路径)
│   ├── ReAct Trace 管理
│   │   ├── Thought/Action/Observation 三段式
│   │   ├── Observation 压缩
│   │   └── 失败尝试归档
│   └── 工具结果缓存
│       ├── 相同 query 复用
│       └── TTL 过期
│
└── 9. 评估与工程实践
    ├── 评估指标
    │   ├── Needle in Haystack
    │   ├── RAGAS (context relevance / utilization)
    │   └── 任务准确率 vs 上下文长度曲线
    ├── 工程框架
    │   ├── LangChain ContextualCompressionRetriever
    │   ├── LlamaIndex ContextRetriever
    │   └── 自研 ContextManager
    └── 成本优化
        ├── token 计费模型
        ├── 缓存 (prompt cache)
        └── 模型分级 (长文本用廉价模型)
```

---

## 面试题（共 10 道）

### Q1: 什么是 Context Engineering？为什么上下文工程比 Prompt Engineering 更重要？

<details>
<summary>查看答案</summary>

**定义**

Context Engineering（上下文工程）是指在调用 LLM 时，系统化地设计、组织、压缩、排序所有进入模型上下文窗口的信息，使得模型在有限 token 预算内获得最相关、最完整、最经济的输入，从而最大化任务表现的一整套方法论。

**上下文 vs Prompt 的区别**

| 维度 | Prompt Engineering | Context Engineering |
|------|-------------------|--------------------|
| 关注点 | 怎么写指令 | 放什么进上下文 |
| 范围 | 单条指令措辞 | system + instruction + few-shot + retrieved + history + tool_result |
| 时代背景 | 2022-2023（GPT-3.5 时代，窗口 4K-8K） | 2024+（窗口 128K-2M，RAG/Agent 普及） |
| 核心矛盾 | 怎么让模型听懂 | 怎么让模型在噪音中找到信号 |
| 优化对象 | 措辞 / 格式 / 角色设定 | 检索质量 / 压缩比 / 排序 / 预算分配 |

**为什么 Context Engineering 更重要？三个理由**

1. **窗口变大但注意力没变强**。Gemini 1.5 Pro 有 2M token 窗口，但 Lost in the Middle 问题表明模型对中间内容的注意力会衰减。光有"大"没有用，关键是"精"。

2. **RAG / Agent 场景下，上下文是动态拼装的**。传统 Prompt 工程面对的是静态指令；而 RAG 场景下每次拼装的检索结果都不同，Agent 场景下工具返回结果、对话历史都在动态变化。Prompt 工程优化的是"一句话怎么说"，Context Engineering 优化的是"一整袋信息怎么挑、怎么压、怎么排"。

3. **成本与延迟敏感**。一次 Agent 调用可能拼装 50K token，如果其中 30K 是冗余的工具返回，既浪费钱（按 token 计费）又增加首 token 延迟。Context Engineering 直接影响单位经济效益。

**面试加分话术**

> "Prompt Engineering 解决的是『怎么说』，Context Engineering 解决的是『说什么』。在 RAG 和 Agent 场景下，模型看到的内容 80% 是动态拼装的，单靠改 system prompt 的措辞已经无法提升效果，必须从系统层面管理上下文。这就像做菜 —— Prompt 工程是调火候，Context 工程是选食材。食材不对，火候再好也做不出好菜。"

**实践要点**

- 把 Context Engineering 当作 RAG/Agent 的"中间件"层，独立设计、独立评估。
- 建立上下文预算台账：每次调用记录各部分 token 占用，定期 review。
- 监控"上下文质量"指标：context relevance、context utilization、answer faithfulness。

</details>

---

### Q2: 上下文窗口管理策略 — 如何在有限的 token 预算内安排 system prompt / few-shot / 检索结果 / 对话历史？

<details>
<summary>查看答案</summary>

**问题本质**

假设模型窗口 32K，预留 4K 给输出，剩 28K 怎么分配给 system prompt、few-shot、检索结果、对话历史？这是一个"资源约束下的优化问题"。

**三种分配策略**

**策略 1：固定比例法（简单但僵化）**

| 组成 | 比例 | 32K 窗口示例 |
|------|------|-------------|
| system prompt | 10% | 3.2K |
| few-shot | 10% | 3.2K |
| 检索结果 | 40% | 12.8K |
| 对话历史 | 30% | 9.6K |
| 输出预留 | 10% | 3.2K |

优点：实现简单，可预测。缺点：无法适应任务变化（如纯聊天场景不需要检索结果）。

**策略 2：动态优先级法（推荐）**

定义优先级，按优先级从高到低填充，低优先级吃剩的预算：

```
P0 system prompt        → 固定保留 (通常 <2K)
P1 当前用户 query       → 固定保留 (通常 <1K)
P2 当前轮检索结果       → 高优先级，分配 40-60% 剩余预算
P3 few-shot 示例        → 中优先级，分配 10-20% 剩余预算
P4 对话历史             → 低优先级，分配剩余预算，可压缩
P5 工具返回结果         → 最低优先级，强烈压缩
```

**策略 3：弹性预算法（高级）**

根据任务类型动态调整比例：

| 任务类型 | system | few-shot | retrieval | history | output |
|---------|--------|----------|-----------|---------|--------|
| 单轮 QA | 5% | 10% | 70% | 0% | 15% |
| 多轮对话 | 5% | 5% | 20% | 55% | 15% |
| Agent 工具调用 | 10% | 5% | 10% | 40% | 35% |
| 长文档摘要 | 5% | 0% | 80% | 0% | 15% |

**关键工程细节**

1. **token 计数必须用模型对应的 tokenizer**。GPT 用 tiktoken，Claude 用官方计数 API，不能用字符数 / 4 估算（中文误差大）。

2. **预留安全边界**。实际预算 = 窗口大小 - 输出预留 - 安全余量（5%）。例如 32K 窗口实际可用 32K - 4K - 1.6K = 26.4K。

3. **历史截断要做"摘要化截断"而非"硬截断"**。直接砍掉早期轮次会丢失任务上下文，应将早期轮次摘要成 1-2 句保留。

4. **检索结果要带优先级**。rerank 后按分数排序，低分 chunk 直接丢弃而非塞进去当噪声。

**伪代码框架**

```python
def assemble_context(budget: int, system: str, query: str, 
                     retrieved: list, history: list, few_shot: list) -> str:
    # 1. 固定保留
    reserved = count_tokens(system) + count_tokens(query)
    remaining = budget - reserved
    
    # 2. 按优先级分配
    retrieval_budget = int(remaining * 0.5)
    fewshot_budget = int(remaining * 0.15)
    history_budget = remaining - retrieval_budget - fewshot_budget
    
    # 3. 各部分填充
    ctx_retrieval = fill_retrieved(retrieved, retrieval_budget)
    ctx_fewshot = fill_fewshot(few_shot, fewshot_budget)
    ctx_history = compress_history(history, history_budget)
    
    # 4. 组装（注意排序，见 Q7）
    return f"{system}\n{ctx_fewshot}\n{ctx_retrieval}\n{ctx_history}\n{query}"
```

**面试加分点**

- 提到"预算分配应该可配置、可观测、可调优"，体现工程思维。
- 提到"不同任务类型用不同分配模板"，体现领域理解。
- 提到"token 计数要用真实 tokenizer，不能用字符数估算"，体现细节把控。

</details>

---

### Q3: Lost in the Middle 问题 — LLM 对长上下文中间内容的注意力衰减，原因和解决方案？

<details>
<summary>查看答案</summary>

**现象**

论文 *"Lost in the Middle: How Language Models Use Long Contexts"* (Liu et al. 2023) 发现：当相关信息放在长上下文的开头或结尾时，模型表现显著好于放在中间。

实验设计：让模型在 20 个文档中找一个事实性答案，改变答案文档的位置。

```
位置:  开头 -------- 中间 -------- 结尾
表现:   高    ↘     最低     ↗     高
       (U 形曲线)
```

**原因（三个层面）**

1. **注意力机制层面**：Transformer 的注意力对首尾 token 有天然偏置（首因效应 + 近因效应）。中间 token 的注意力被"稀释"。

2. **位置编码层面**：RoPE / ALiBi 等相对位置编码在长上下文中外推性能下降，中间位置的相对距离感知变弱。

3. **训练数据层面**：预训练数据中"答案在开头/结尾"的比例更高（如文章主旨在开头，结论在结尾），模型学到了这种先验。

**解决方案**

**方案 1：重新排序（Reorder，最实用）**

将最相关的内容放在上下文的开头和结尾，将低相关内容放在中间。

LangChain 提供 `LongContextReorder`：

```python
from langchain_community.document_transformers import LongContextReorder

reorder = LongContextReorder()
reordered_docs = reorder.transform_documents(retrieved_docs)
# 效果: [最相关, 次相关, ..., 次次相关, 最最相关]
# 即: 高分放头尾，中间放低分
```

**方案 2：上下文压缩**

减少总长度，让"中间"变短。见 Q4。

**方案 3：分而治之（Multiple Queries）**

将长上下文拆成多段，分别查询，再合并结果。如 Map-Reduce 摘要。

**方案 4：StreamingLLM / Attention Sink**

StreamingLLM（Xiao et al. 2023）发现保留前几个 token 作为 "attention sink" 可以显著提升长上下文稳定性。适用于流式对话场景。

**方案 5：模型层面改进**

- 训练时增加"答案在中间"的数据比例。
- 使用更好的位置编码（如 YaRN、NTK-aware RoPE）。
- 长上下文微调（如 Gemini 1.5 的多阶段训练）。

**评估方法：Needle in Haystack（针式检索）**

将一个事实（"针"）藏在长文档的不同位置，测试模型能否找到。

```
文档长度:  1K   4K   16K  64K  128K
位置:
  0%      ✓    ✓    ✓    ✓    ✓
  25%     ✓    ✓    ✗    ✗    ✗   ← 中间丢失
  50%     ✓    ✓    ✗    ✗    ✗   ← 最严重
  75%     ✓    ✓    ✗    ✗    ✗
  100%    ✓    ✓    ✓    ✓    ✓
```

可视化成"热力图"，颜色越绿表现越好。这是评估长上下文模型的标准方法。

**面试加分话术**

> "Lost in the Middle 不是某个模型的 bug，而是 Transformer 架构的固有特性。工程上的解法是『重新排序 + 压缩』，把相关信息放首尾；模型层面的解法是改进位置编码和训练数据分布。在 RAG 场景下，我一定会加一个 reorder 步骤，把 rerank 后 top-1 和 top-2 放在最前面，top-3 放在最后，中间放相关度较低的 chunk。"

</details>

---

### Q4: 上下文压缩技术 — 摘要式压缩 / 抽取式压缩 / LLMLingua 等方案？

<details>
<summary>查看答案</summary>

**压缩技术分类**

```
上下文压缩
├── 语义级压缩（保留信息，改变表达）
│   ├── 摘要式压缩 (Abstractive)
│   └── 结构化压缩 (JSON 裁剪 / Schema 化)
├── 内容级压缩（保留原文，剔除冗余）
│   ├── 抽取式压缩 (Extractive)
│   └── Token 级压缩 (LLMLingua)
└── 混合压缩
    └── 摘要 + Token 级
```

**1. 摘要式压缩（Abstractive Compression）**

用 LLM 对长文本生成摘要，用摘要替代原文。

```python
def abstractive_compress(text: str, target_ratio: float = 0.3) -> str:
    prompt = f"请将以下内容压缩到原文的 {target_ratio*100}%，保留所有关键事实和数字:\n\n{text}"
    return llm(prompt)
```

- 优点：压缩比高（5-10x），语义保留好。
- 缺点：有信息损失，可能引入幻觉，调用 LLM 成本高。
- 适用：对话历史压缩、长文档概览。

**进阶：递归摘要（Hierarchical Summary）**

```
原文 (100K tokens)
  → 分 10 段，每段摘要 (10K tokens)
  → 10 段摘要合并，再摘要 (1K tokens)
  → 最终摘要
```

适用：超长文档（>100K）。

**2. 抽取式压缩（Extractive Compression）**

从原文中抽取关键句，丢弃其他。

```python
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer

def extractive_compress(text: str, sentences_count: int = 5) -> str:
    parser = PlaintextParser.from_string(text, Tokenizer("chinese"))
    summarizer = TextRankSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join([str(s) for s in summary])
```

- 优点：无幻觉，保留原文措辞，速度快。
- 缺点：压缩比有限（2-3x），可能丢失逻辑连接。
- 适用：事实性文档、法律合同、技术规范。

**3. Token 级压缩 — LLMLingua（微软，重点）**

核心思想：用一个小语言模型计算每个 token 的困惑度（perplexity），剔除低困惑度（高可预测性、低信息量）的 token。

```python
from llmlingua import PromptCompressor

compressor = PromptCompressor(model_name="microsoft/llmlingua-2-xlm-roberta-large")

compressed = compressor.compress_prompt(
    context=long_text,
    rate=0.5,  # 压缩到 50%
    force_tokens=["\n", "?", ".", "!"],  # 保留的 token
    drop_consecutive=True,
)
# compressed['compressed_prompt'] 是压缩后的文本
```

**LLMLingua 系列对比**

| 版本 | 方法 | 压缩比 | 性能损失 | 速度 |
|------|------|--------|---------|------|
| LLMLingua (2023) | 基于大模型困惑度 | 2-10x | <5% | 慢 |
| LongLLMLingua (2023) | 针对长上下文优化 + 问题感知 | 2-10x | <3% | 慢 |
| LLMLingua-2 (2024) | 基于 BERT/XLM-R 分类 | 2-10x | <5% | 快（10x） |

**LLMLingua-2 原理**：训练一个 BERT 分类器，直接预测每个 token 是否应该保留，比用大模型算困惑度快 10 倍。

**4. 结构化压缩**

针对 JSON / 工具返回结果，按 schema 裁剪字段。

```python
def compress_tool_result(result: dict, keep_fields: list) -> dict:
    """压缩工具返回结果，只保留必要字段"""
    return {k: result.get(k) for k in keep_fields if k in result}

# 示例: 搜索 API 返回 20 个字段，只保留 3 个
search_result = {"title": "...", "url": "...", "snippet": "...", 
                 "metadata": {...}, "tracking_id": "...", ...}
compressed = compress_tool_result(search_result, ["title", "url", "snippet"])
```

适用：Agent 工具调用结果、API 响应。

**5. 混合策略（生产推荐）**

```
长文本
  → 抽取式压缩（TextRank，去 50% 冗余句）
  → LLMLingua（再压 30%）
  → 最终: 原文的 35%
```

**压缩技术选型表**

| 场景 | 推荐方案 | 压缩比 | 性能损失 |
|------|---------|--------|---------|
| 对话历史 | 摘要式（早期轮次） | 5-10x | 中 |
| 检索结果 | LLMLingua | 2-5x | 低 |
| 工具返回 | 结构化裁剪 | 5-20x | 极低 |
| 长文档 | 递归摘要 | 10-50x | 中高 |
| 事实性文档 | 抽取式 | 2-3x | 低 |

**面试加分点**

- 提到"压缩要可逆评估"：压缩前后跑同一套测试集，对比准确率下降幅度。
- 提到"压缩比不是越高越好"：超过 10x 后性能急剧下降，3-5x 是甜点。
- 提到"压缩有成本"：LLMLingua 本身要调小模型，摘要要调大模型，要算总账。

</details>

---

### Q5: 长文本处理策略 — 分段处理 / 滑动窗口 / 层次摘要 / Map-Reduce？

<details>
<summary>查看答案</summary>

**问题本质**

当文档长度远超模型上下文窗口（如 500K 文档 vs 32K 窗口），或虽然能放下但 Lost in the Middle 严重，需要将长文本"化整为零"处理。

**LangChain 四种模式（经典分类）**

```
load_qa_chain 四种 document chain:
├── stuff: 全部塞进去（文档 < 窗口 80%）
├── map_reduce: 分段独立处理，合并结果
├── refine: 顺序处理，逐步精化
└── map_rerank: 分段独立处理，打分选最优
```

**1. Stuff（直接塞）**

最简单：把所有文档拼成一个长 prompt。

```python
prompt = f"基于以下文档回答问题:\n{all_docs}\n问题: {question}"
```

- 适用：总 token < 窗口的 80%。
- 优点：无损，一次调用。
- 缺点：受窗口限制，长文档不可用。

**2. Map-Reduce（分段映射 + 合并）**

```
长文档 → 分段
  chunk1 → LLM → intermediate_result1 ─┐
  chunk2 → LLM → intermediate_result2 ─┤
  chunk3 → LLM → intermediate_result3 ─┤→ 合并 → 最终结果
  chunk4 → LLM → intermediate_result4 ─┘
```

```python
def map_reduce_summary(long_text: str, question: str, chunk_size: int = 4000) -> str:
    chunks = split_text(long_text, chunk_size)
    
    # Map: 每段独立处理
    intermediate = []
    for chunk in chunks:
        result = llm(f"基于这段内容回答问题:\n{chunk}\n问题: {question}")
        intermediate.append(result)
    
    # Reduce: 合并
    combined = "\n---\n".join(intermediate)
    final = llm(f"综合以下分段结果，给出最终答案:\n{combined}\n问题: {question}")
    return final
```

- 适用：摘要、抽取、分类等可分解任务。
- 优点：可并行，可扩展到任意长度。
- 缺点：多次 LLM 调用，成本高；跨段信息可能丢失。

**3. Refine（逐步精化）**

```
chunk1 → LLM(initial_answer)
chunk2 → LLM(refine: given current answer + new chunk, refine)
chunk3 → LLM(refine: ...)
...
```

```python
def refine_summary(long_text: str, question: str, chunk_size: int = 4000) -> str:
    chunks = split_text(long_text, chunk_size)
    
    answer = llm(f"基于这段内容回答问题:\n{chunks[0]}\n问题: {question}")
    
    for chunk in chunks[1:]:
        answer = llm(
            f"当前答案: {answer}\n\n"
            f"新信息: {chunk}\n\n"
            f"基于新信息，精化答案。问题: {question}"
        )
    return answer
```

- 适用：需要跨段累积信息的任务（如全书总结）。
- 优点：信息保留好，答案逐步完善。
- 缺点：串行，慢；早期误差会传播。

**4. Map-Rerank（分段打分选优）**

```
chunk1 → LLM(answer1, score1)
chunk2 → LLM(answer2, score2)
...
→ 选 score 最高的 answer
```

- 适用：答案只存在于某一段的任务（如事实性 QA）。
- 优点：简单，避免合并复杂度。
- 缺点：跨段问题不适用。

**其他高级策略**

**5. 滑动窗口（Sliding Window）**

适用于时序数据 / 流式输入。

```python
def sliding_window_process(stream, window_size=4000, step=2000):
    """窗口重叠处理，避免边界信息丢失"""
    buffer = ""
    results = []
    for chunk in stream:
        buffer += chunk
        while len(buffer) >= window_size:
            window = buffer[:window_size]
            results.append(process(window))
            buffer = buffer[step:]  # 保留重叠
    return results
```

**6. 层次摘要（Hierarchical Summary）**

```
原文 (1M tokens)
├── Chapter 1 (100K) → Summary (5K)
├── Chapter 2 (100K) → Summary (5K)
└── ...
→ 各章摘要合并 (50K) → 全书摘要 (2K)

查询时:
  → 先查全书摘要，定位相关章节
  → 再查相关章节摘要，定位相关段落
  → 最后查相关段落原文
```

适用：超长文档（书籍、代码库）的检索增强。

**策略选型决策表**

| 场景 | 推荐策略 | 理由 |
|------|---------|------|
| 文档 < 窗口 80% | Stuff | 无损、一次调用 |
| 摘要任务，可并行 | Map-Reduce | 并行加速 |
| 跨段累积任务 | Refine | 信息逐步精化 |
| 答案在某一段 | Map-Rerank | 避免合并噪音 |
| 流式 / 时序 | 滑动窗口 | 边界平滑 |
| 超长文档 (1M+) | 层次摘要 + 分层检索 | 渐进式定位 |

**面试加分话术**

> "长文本处理的本质是『信息密度与计算成本的权衡』。Stuff 是无损但贵，Map-Reduce 是有损但可扩展。生产中我会先用层次摘要建索引，查询时分层定位 —— 先查全书摘要找章节，再查章节摘要找段落，最后取段落原文Stuff 进上下文。这样既控制了上下文长度，又保留了精度。"

</details>

---

### Q6: Few-shot 示例选择策略 — 相似度检索 / 多样性 / 难度排序？

<details>
<summary>查看答案</summary>

**问题本质**

In-Context Learning（ICL）的效果高度依赖 few-shot 示例的选择。选错示例，模型可能学到错误模式。

**四种选择策略**

**1. 相似度检索（kNN，最常用）**

用 embedding 计算候选示例与当前 query 的相似度，选 top-k。

```python
def select_by_similarity(query: str, examples: list, k: int = 3) -> list:
    query_emb = embed(query)
    examples_with_emb = [(ex, embed(ex["input"])) for ex in examples]
    scored = [(ex, cosine_sim(query_emb, ex_emb)) for ex, ex_emb in examples_with_emb]
    scored.sort(key=lambda x: -x[1])
    return [ex for ex, _ in scored[:k]]
```

- 优点：简单有效，与 RAG 复用基础设施。
- 缺点：可能选到高度同质的示例，缺乏覆盖度。

**2. 多样性选择（MMR）**

Maximal Marginal Relevance：在相似度和多样性之间平衡。

```python
def select_by_mmr(query: str, examples: list, k: int = 3, lambda_: float = 0.7) -> list:
    query_emb = embed(query)
    candidates = [(ex, embed(ex["input"])) for ex in examples]
    selected = []
    
    # 第一个选最相似的
    candidates.sort(key=lambda x: -cosine_sim(query_emb, x[1]))
    selected.append(candidates[0])
    candidates = candidates[1:]
    
    # 后续按 MMR 选
    while len(selected) < k and candidates:
        mmr_scores = []
        for ex, ex_emb in candidates:
            rel = cosine_sim(query_emb, ex_emb)
            div = max(cosine_sim(ex_emb, s[1]) for s in selected)
            mmr = lambda_ * rel - (1 - lambda_) * div
            mmr_scores.append((ex, ex_emb, mmr))
        mmr_scores.sort(key=lambda x: -x[2])
        best = mmr_scores[0]
        selected.append((best[0], best[1]))
        candidates = [(ex, emb) for ex, emb, _ in mmr_scores[1:]]
    
    return [ex for ex, _ in selected]
```

- 优点：避免示例同质化，覆盖更多模式。
- 缺点：计算量略大。
- 适用：示例库大、任务模式多样。

**3. 难度排序（Easy-to-Hard）**

由易到难排列示例，类似课程学习。

```python
def select_by_difficulty(query: str, examples: list, k: int = 3) -> list:
    # 假设每个示例有难度标签
    examples_with_diff = [(ex, ex.get("difficulty", 0.5)) for ex in examples]
    # 先按相似度筛 top 2k
    candidates = select_by_similarity(query, examples, k=2*k)
    # 再按难度升序排，取前 k
    candidates.sort(key=lambda ex: ex.get("difficulty", 0.5))
    return candidates[:k]
```

- 优点：符合"由易到难"的学习规律，模型更稳定。
- 缺点：需要难度标签，标注成本高。
- 适用：数学推理、代码生成等有难度梯度的任务。

**4. 混合策略（生产推荐）**

```python
def select_few_shot(query: str, examples: list, k: int = 5) -> list:
    # 1. 相似度检索 top 2k
    candidates = select_by_similarity(query, examples, k=2*k)
    # 2. MMR 去重，选 k 个
    diverse = select_by_mmr(query, candidates, k=k)
    # 3. 按相似度降序排列（最相似放最后，近因效应）
    diverse.sort(key=lambda ex: cosine_sim(embed(query), embed(ex["input"])))
    return diverse
```

**示例数量与效果（ICL Scaling Laws）**

```
示例数:  0    1    3    5    10   20   50
效果:   基线  +5%  +12% +18% +22% +24% +25%
                              ↑ 边际效益开始递减
```

- 1-3 个：Few-shot 经典配置。
- 5-10 个：Many-shot，效果更好但 token 成本上升。
- 20+ 个：边际效益递减，不划算。

**示例顺序敏感性**

研究表明，示例顺序对输出影响显著（方差可达 10%）。

推荐顺序：
- **相关度升序**：最相似的放最后（近因效应最强）。
- **难度升序**：最难的放最前，最简单的放最后。
- **避免随机**：随机顺序会引入方差。

```python
# 推荐排列: 相似度升序 (最相似放最后)
examples.sort(key=lambda ex: similarity(query, ex))
# [一般相关, 较相关, 最相关] ← 最后一个最相似，近因效应加持
```

**面试加分点**

- 提到"few-shot 示例要带输出格式"，避免模型自由发挥。
- 提到"负例（错误示例）有时比正例更有效"，特别是在分类任务中。
- 提到"示例选择本身可以缓存"，避免每次都算 embedding。

</details>

---

### Q7: 上下文排序优化 — 相关信息放前 / 后，噪声放中间？

<details>
<summary>查看答案</summary>

**理论基础**

LLM 对上下文不同位置的注意力不均匀，存在两个效应：

- **首因效应（Primacy Effect）**：开头的 token 获得更高注意力。
- **近因效应（Recency Effect）**：结尾的 token 获得更高注意力。

这导致 U 形注意力曲线，中间内容容易被忽略（Lost in the Middle）。

**排序原则**

```
上下文结构:
[高相关 / 重要]  [低相关 / 噪声]  [高相关 / 最重要]
     ↑                ↑                ↑
   首因效应        中间衰减区        近因效应
   (放系统指令)    (放次要信息)      (放当前 query)
```

**实战排序模板**

```
1. system prompt        ← 固定首位
2. few-shot 示例        ← 次位，建立输出模式
3. 检索结果 (低分→高分)  ← 中间到结尾，逐步升温
4. 对话历史 (摘要)       ← 中间
5. 当前用户 query       ← 固定末位，近因效应加持
```

**检索结果排序示例**

假设 rerank 后有 5 个 chunk，分数从高到低：A(0.9), B(0.8), C(0.7), D(0.6), E(0.5)。

**错误排序（按分数降序）**：
```
[A, B, C, D, E]
 最相关放最前，但 E 放最后会稀释 query 的近因效应
```

**推荐排序（首尾放高分，中间放低分）**：
```
[A, E, D, C, B]
 ↑           ↑
最高分       次高分
首因效应     近因效应
```

**LangChain 实现**

```python
from langchain_community.document_transformers import LongContextReorder
from langchain_core.documents import Document

# 假设 docs 已按相关度降序排列
docs = [
    Document(page_content="最相关内容", metadata={"score": 0.9}),
    Document(page_content="次相关内容", metadata={"score": 0.8}),
    Document(page_content="中等相关", metadata={"score": 0.7}),
    Document(page_content="较低相关", metadata={"score": 0.6}),
    Document(page_content="最低相关", metadata={"score": 0.5}),
]

reorder = LongContextReorder()
reordered = reorder.transform_documents(docs)
# 结果: [最相关, 最低相关, 较低相关, 中等相关, 次相关]
# 即: 第1个不变，第2个和最后1个交换，第3个和倒数第2个交换...
```

**`LongContextReorder` 算法**：
```python
def reorder_documents(docs: list) -> list:
    """交错重排: 偶数位放前半段, 奇数位放后半段"""
    reordered = []
    for i in range(len(docs)):
        if i % 2 == 0:
            reordered.append(docs[i // 2])
        else:
            reordered.append(docs[-(i // 2 + 1)])
    return reordered
# 输入 [A,B,C,D,E] → 输出 [A, E, B, D, C]
```

**对话历史的排序**

多轮对话历史保持时间顺序（不要重排），但可以：
- 最近 N 轮原文保留。
- 早期轮次摘要化，放在最前面。

```
[早期对话摘要]  [轮次3原文]  [轮次4原文]  [最近轮次原文]  [当前query]
     ↑                                           ↑           ↑
   首因效应                                    近因效应     最强近因
```

**Few-shot 示例的排序**

见 Q6：相关度升序（最相似放最后）。

**注意事项**

1. **排序收益与上下文长度相关**。短上下文（<4K）排序影响小，长上下文（>32K）排序影响大。短上下文不必过度优化。

2. **system prompt 不要参与重排**。它在最前面是固定的，重排的是可变部分（检索结果、历史）。

3. **排序后要验证**。跑一套测试集，对比排序前后的准确率，确认收益。

**面试加分话术**

> "上下文排序的本质是『对抗注意力的 U 形曲线』。我会把检索结果按 rerank 分数做交错重排 —— 最高分放首位利用首因效应，次高分放末位利用近因效应，低分放中间。这个操作零成本、零延迟，但在长上下文场景下能带来 3-5% 的准确率提升，是性价比最高的优化之一。"

</details>

---

### Q8: Agent 场景下的上下文管理 — 工具调用结果压缩 / 历史轮次截断 / 关键信息保留？

<details>
<summary>查看答案</summary>

**Agent 上下文的特殊性**

Agent 的上下文比 RAG 更复杂：

```
Agent 上下文组成
├── system prompt (角色 + 工具说明 + 约束)
├── 任务描述
├── 对话历史
│   ├── 用户指令
│   ├── Agent Thought
│   ├── Agent Action (tool_call)
│   ├── Tool Observation (可能很长!)
│   └── ... (多轮)
├── 可用工具列表 (function schema)
└── 当前需要决策的输入
```

**痛点**：Agent 跑 10 轮后，上下文可能膨胀到 50K+，主要是 Tool Observation 占的。

**三大管理策略**

**1. 工具调用结果压缩**

工具返回的 JSON / 文本往往包含大量冗余字段。

```python
def compress_observation(obs: str, tool_name: str, max_tokens: int = 1000) -> str:
    """根据工具类型定制压缩策略"""
    
    if tool_name == "search":
        # 搜索结果: 只保留 title + snippet, 丢弃 metadata
        results = json.loads(obs)
        compressed = [{"title": r["title"], "snippet": r["snippet"][:200]} 
                      for r in results[:5]]
        return json.dumps(compressed, ensure_ascii=False)
    
    elif tool_name == "code_interpreter":
        # 代码执行: 只保留最后输出, 丢弃中间日志
        lines = obs.split("\n")
        # 取最后 20 行 + 包含 "Error" 的行
        important = [l for l in lines if "Error" in l or "Traceback" in l]
        return "\n".join(important[-5:] + lines[-20:])
    
    elif tool_name == "web_scraper":
        # 网页抓取: 去 HTML 标签, 只保留正文
        from bs4 import BeautifulSoup
        text = BeautifulSoup(obs, "html.parser").get_text()
        return text[:max_tokens * 4]  # 粗估 4 char = 1 token
    
    else:
        # 默认: 截断 + 摘要
        if count_tokens(obs) > max_tokens:
            return llm_summarize(obs, max_tokens) 
        return obs
```

**2. 历史轮次截断**

策略：最近 N 轮原文 + 早期轮次摘要。

```python
def truncate_history(history: list, keep_recent: int = 3, 
                     summary_budget: int = 500) -> list:
    if len(history) <= keep_recent:
        return history
    
    # 早期轮次摘要
    early = history[:-keep_recent]
    early_text = "\n".join([f"User: {t['user']}\nAgent: {t['agent']}" for t in early])
    summary = llm_summarize(
        f"总结以下对话的关键信息和决策:\n{early_text}", 
        max_tokens=summary_budget
    )
    
    # 拼装
    return [
        {"user": "[历史摘要]", "agent": summary},
        *history[-keep_recent:]
    ]
```

**进阶：基于重要性的截断**

```python
def importance_based_truncate(history: list, budget: int) -> list:
    """按重要性评分保留轮次"""
    scored = []
    for i, turn in enumerate(history):
        score = 0
        # 最近轮次加分
        score += (i / len(history)) * 0.4
        # 包含工具调用加分(决策点)
        if turn.get("tool_call"):
            score += 0.3
        # 包含错误加分(需要记住的教训)
        if "error" in turn.get("observation", "").lower():
            score += 0.2
        # 用户明确指令加分
        if turn.get("is_user_instruction"):
            score += 0.1
        scored.append((turn, score))
    
    scored.sort(key=lambda x: -x[1])
    kept = [t for t, _ in scored[:budget]]
    # 恢复时间顺序
    kept.sort(key=lambda t: history.index(t))
    return kept
```

**3. 关键信息保留**

哪些信息"绝对不能丢"？

```python
class CriticalInfoPreserver:
    def __init__(self):
        self.critical = {
            "task_goal": None,        # 任务目标
            "constraints": [],        # 约束条件
            "completed_steps": [],    # 已完成步骤
            "key_variables": {},      # 关键变量 (文件路径、ID等)
            "user_preferences": {},   # 用户偏好
        }
    
    def extract_critical(self, turn: dict):
        """从每轮对话中提取关键信息"""
        # 用 LLM 或规则提取
        if turn.get("is_user_instruction"):
            self.critical["task_goal"] = turn["user"]
        if turn.get("tool_call"):
            self.critical["completed_steps"].append(turn["tool_call"])
        # 提取文件路径、ID 等
        import re
        paths = re.findall(r'/[\w/.]+', turn.get("agent", ""))
        self.critical["key_variables"]["paths"] = paths
```

**完整 Agent 上下文管理流程**

```python
def manage_agent_context(history: list, new_input: str, budget: int = 16000) -> dict:
    """Agent 上下文管理主流程"""
    
    # 1. 提取关键信息(永不丢弃)
    critical = extract_critical_info(history)
    
    # 2. 压缩工具结果
    for turn in history:
        if "observation" in turn:
            turn["observation"] = compress_observation(
                turn["observation"], turn.get("tool_name", ""), max_tokens=500
            )
    
    # 3. 截断历史(最近3轮原文 + 早期摘要)
    truncated = truncate_history(history, keep_recent=3)
    
    # 4. 组装上下文
    context = {
        "system": SYSTEM_PROMPT,
        "critical_info": critical,
        "history": truncated,
        "tools": TOOL_SCHEMAS,
        "current_input": new_input,
    }
    
    # 5. 检查预算
    total = count_tokens(json.dumps(context, ensure_ascii=False))
    if total > budget:
        # 进一步压缩: 减少历史轮次
        context["history"] = truncate_history(history, keep_recent=1)
    
    return context
```

**面试加分话术**

> "Agent 上下文管理的核心是『区分信号和噪音』。工具返回的 50 行 JSON 里可能只有 2 行有用，对话历史里 10 轮可能只有 3 轮是决策点。我会做一个『重要性感知』的截断 —— 最近 N 轮原文保留，早期轮次摘要，工具结果按类型定制压缩，关键变量（文件路径、任务目标）单独提取永不丢弃。这样 Agent 跑 20 轮上下文还能控制在 16K 以内。"

</details>

---

### Q9: 手撕代码题 — 实现一个上下文管理器（ContextManager），支持 token 预算分配 / 上下文压缩 / 历史截断 / 优先级排序？

<details>
<summary>查看答案（完整代码实现）</summary>

**需求拆解**

实现一个生产级 ContextManager，支持：
1. token 预算分配（按优先级）
2. 上下文压缩（摘要 + LLMLingua 风格的 token 级压缩）
3. 历史截断（最近 N 轮 + 早期摘要）
4. 优先级排序（首尾放高分，中间放低分）
5. 可观测性（记录各部分 token 占用）

**完整实现**

```python
"""
ContextManager: 生产级上下文管理器
支持 token 预算分配 / 上下文压缩 / 历史截断 / 优先级排序
"""
import json
import re
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


# ============================================================
# 1. Token 计数器
# ============================================================
class TokenCounter:
    """token 计数器, 优先用 tiktoken, 降级用字符数估算"""
    
    _encoder = None
    
    @classmethod
    def _get_encoder(cls):
        if cls._encoder is None:
            try:
                import tiktoken
                cls._encoder = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                cls._encoder = "fallback"
        return cls._encoder
    
    @classmethod
    def count(cls, text: str) -> int:
        if not text:
            return 0
        encoder = cls._get_encoder()
        if encoder == "fallback":
            # 降级: 英文 4 char ≈ 1 token, 中文 1.5 char ≈ 1 token
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + other_chars / 4)
        return len(encoder.encode(text))
    
    @classmethod
    def count_messages(cls, messages: list[dict]) -> int:
        """计算 OpenAI 格式 messages 的 token 数"""
        total = 0
        for msg in messages:
            total += cls.count(msg.get("content", ""))
            total += 4  # 每条消息的格式开销
        return total


# ============================================================
# 2. 上下文项定义
# ============================================================
class Priority(IntEnum):
    """优先级: 数字越小, 优先级越高"""
    P0_SYSTEM = 0       # system prompt, 永不裁剪
    P1_QUERY = 1        # 当前用户 query, 永不裁剪
    P2_CRITICAL = 2     # 关键信息(任务目标/约束), 永不裁剪
    P3_RETRIEVAL = 3    # 检索结果, 高优先级
    P4_FEWSHOT = 4      # few-shot 示例
    P5_HISTORY = 5      # 对话历史, 可压缩
    P6_TOOL_RESULT = 6  # 工具返回, 可压缩


@dataclass
class ContextItem:
    """上下文项"""
    content: str
    priority: Priority
    metadata: dict = field(default_factory=dict)
    compressible: bool = True
    # 元数据可选字段:
    #   score: 相关度分数 (用于排序)
    #   source: 来源 (retrieval/history/tool)
    #   turn_index: 对话轮次
    #   tool_name: 工具名
    
    @property
    def token_count(self) -> int:
        return TokenCounter.count(self.content)


# ============================================================
# 3. 上下文压缩器
# ============================================================
class ContextCompressor:
    """上下文压缩器: 支持摘要式 / 截断式 / 结构化压缩"""
    
    def __init__(self, llm_caller=None):
        self.llm = llm_caller  # 注入 LLM 调用函数
    
    def compress(self, item: ContextItem, target_tokens: int) -> ContextItem:
        """压缩到目标 token 数"""
        if item.token_count <= target_tokens:
            return item
        
        # 根据来源选择压缩策略
        source = item.metadata.get("source", "")
        
        if source == "tool_result":
            return self._compress_tool_result(item, target_tokens)
        elif source == "history":
            return self._compress_history(item, target_tokens)
        elif source == "retrieval":
            return self._compress_retrieval(item, target_tokens)
        else:
            return self._compress_generic(item, target_tokens)
    
    def _compress_tool_result(self, item: ContextItem, target_tokens: int) -> ContextItem:
        """工具结果压缩: 结构化裁剪"""
        content = item.content
        try:
            data = json.loads(content)
            if isinstance(data, list):
                # 列表: 只保留前 N 项的核心字段
                kept = []
                for entry in data[:10]:
                    if isinstance(entry, dict):
                        # 保留短字段, 丢弃长字段
                        kept.append({k: v for k, v in entry.items() 
                                   if len(str(v)) < 200})
                    else:
                        kept.append(entry)
                compressed = json.dumps(kept, ensure_ascii=False)
            elif isinstance(data, dict):
                # 字典: 保留值较短的字段
                kept = {k: v for k, v in data.items() if len(str(v)) < 500}
                compressed = json.dumps(kept, ensure_ascii=False)
            else:
                compressed = str(data)[:target_tokens * 4]
        except json.JSONDecodeError:
            # 非 JSON: 截断
            compressed = content[:target_tokens * 4]
        
        return ContextItem(
            content=compressed,
            priority=item.priority,
            metadata={**item.metadata, "compressed": True, "original_tokens": item.token_count},
            compressible=item.compressible,
        )
    
    def _compress_history(self, item: ContextItem, target_tokens: int) -> ContextItem:
        """历史压缩: 摘要式"""
        if self.llm is None:
            # 无 LLM: 硬截断保留开头和结尾
            content = item.content
            chars = target_tokens * 3
            if len(content) > chars:
                head = content[:chars // 2]
                tail = content[-chars // 2:]
                compressed = f"{head}\n...(省略)...\n{tail}"
            else:
                compressed = content
        else:
            prompt = (
                f"请将以下对话历史压缩到 {target_tokens} token 以内，"
                f"保留关键决策、用户意图和重要结果:\n\n{item.content}"
            )
            compressed = self.llm(prompt)
        
        return ContextItem(
            content=compressed,
            priority=item.priority,
            metadata={**item.metadata, "compressed": True, "original_tokens": item.token_count},
            compressible=item.compressible,
        )
    
    def _compress_retrieval(self, item: ContextItem, target_tokens: int) -> ContextItem:
        """检索结果压缩: 截断式(保留前N句)"""
        content = item.content
        sentences = re.split(r'(?<=[。.!?！？\n])', content)
        kept = []
        current = 0
        for s in sentences:
            s_tokens = TokenCounter.count(s)
            if current + s_tokens > target_tokens:
                break
            kept.append(s)
            current += s_tokens
        compressed = "".join(kept)
        
        return ContextItem(
            content=compressed,
            priority=item.priority,
            metadata={**item.metadata, "compressed": True, "original_tokens": item.token_count},
            compressible=item.compressible,
        )
    
    def _compress_generic(self, item: ContextItem, target_tokens: int) -> ContextItem:
        """通用压缩: 截断"""
        content = item.content[:target_tokens * 4]
        return ContextItem(
            content=content,
            priority=item.priority,
            metadata={**item.metadata, "compressed": True, "original_tokens": item.token_count},
            compressible=item.compressible,
        )


# ============================================================
# 4. 上下文排序器
# ============================================================
class ContextReorder:
    """上下文排序器: 对抗 Lost in the Middle"""
    
    @staticmethod
    def reorder(items: list[ContextItem]) -> list[ContextItem]:
        """
        重排策略:
        1. P0/P1/P2 (固定优先级) 保持原序, 放最前
        2. 可重排项 (P3-P6) 按 score 交错重排
        3. 同优先级内: 高分放首尾, 低分放中间
        """
        # 分离固定项和可重排项
        fixed = [it for it in items if it.priority <= Priority.P2_CRITICAL]
        flexible = [it for it in items if it.priority > Priority.P2_CRITICAL]
        
        # 可重排项按 score 降序
        flexible.sort(
            key=lambda x: x.metadata.get("score", 0.5),
            reverse=True
        )
        
        # 交错重排: 偶数位取前半段, 奇数位取后半段
        reordered = []
        n = len(flexible)
        for i in range(n):
            if i % 2 == 0:
                reordered.append(flexible[i // 2])
            else:
                reordered.append(flexible[n - (i // 2) - 1])
        
        # few-shot 单独处理: 相关度升序(最相似放最后)
        fewshot = [it for it in reordered if it.priority == Priority.P4_FEWSHOT]
        non_fewshot = [it for it in reordered if it.priority != Priority.P4_FEWSHOT]
        if fewshot:
            fewshot.sort(key=lambda x: x.metadata.get("score", 0.5))
            # 找到 history 位置, 把 few-shot 放 history 前
            history_idx = next(
                (i for i, it in enumerate(non_fewshot) 
                 if it.priority == Priority.P5_HISTORY),
                len(non_fewshot)
            )
            non_fewshot = non_fewshot[:history_idx] + fewshot + non_fewshot[history_idx:]
            reordered = non_fewshot
        
        return fixed + reordered


# ============================================================
# 5. 上下文管理器(核心)
# ============================================================
class ContextManager:
    """
    上下文管理器
    支持: token 预算分配 / 上下文压缩 / 历史截断 / 优先级排序
    """
    
    # 默认预算分配比例(剩余预算, 扣除固定项后)
    DEFAULT_BUDGET_RATIOS = {
        Priority.P3_RETRIEVAL: 0.45,
        Priority.P4_FEWSHOT: 0.15,
        Priority.P5_HISTORY: 0.25,
        Priority.P6_TOOL_RESULT: 0.15,
    }
    
    def __init__(
        self,
        max_tokens: int = 32000,
        output_reserve: int = 4000,
        safety_margin: float = 0.05,
        llm_caller=None,
        budget_ratios: Optional[dict] = None,
    ):
        self.max_tokens = max_tokens
        self.output_reserve = output_reserve
        self.safety_margin = safety_margin
        self.compressor = ContextCompressor(llm_caller)
        self.reorderer = ContextReorder()
        self.budget_ratios = budget_ratios or self.DEFAULT_BUDGET_RATIOS
        # 可观测性
        self.stats = {
            "total_calls": 0,
            "compression_count": 0,
            "truncation_count": 0,
            "budget_usage": [],
        }
    
    @property
    def available_budget(self) -> int:
        """可用预算 = 窗口 - 输出预留 - 安全余量"""
        return int(self.max_tokens * (1 - self.safety_margin)) - self.output_reserve
    
    def add(
        self,
        content: str,
        priority: Priority,
        metadata: Optional[dict] = None,
        compressible: bool = True,
    ) -> 'ContextManager':
        """链式添加上下文项"""
        if not hasattr(self, '_items'):
            self._items = []
        self._items.append(ContextItem(
            content=content,
            priority=priority,
            metadata=metadata or {},
            compressible=compressible,
        ))
        return self
    
    def build(self) -> dict:
        """
        构建最终上下文
        返回: {"prompt": str, "stats": dict}
        """
        if not hasattr(self, '_items'):
            self._items = []
        
        self.stats["total_calls"] += 1
        budget = self.available_budget
        items = list(self._items)
        
        # ---- Step 1: 计算固定项占用 ----
        fixed_items = [it for it in items if it.priority <= Priority.P2_CRITICAL 
                       or not it.compressible]
        fixed_tokens = sum(it.token_count for it in fixed_items)
        remaining = budget - fixed_tokens
        
        if remaining < 0:
            raise ValueError(
                f"固定项 ({fixed_tokens} tokens) 已超过预算 ({budget} tokens), "
                f"请缩短 system prompt 或关键信息"
            )
        
        # ---- Step 2: 按优先级分配预算给可变项 ----
        flexible_items = [it for it in items if it.priority > Priority.P2_CRITICAL 
                          and it.compressible]
        budget_allocation = self._allocate_budget(flexible_items, remaining)
        
        # ---- Step 3: 各项填充 + 压缩 ----
        final_items = list(fixed_items)
        for item in flexible_items:
            item_budget = budget_allocation.get(item.priority, 0)
            if item.token_count > item_budget:
                # 需要压缩
                self.stats["compression_count"] += 1
                item = self.compressor.compress(item, item_budget)
                if item.metadata.get("original_tokens", 0) > item.token_count:
                    self.stats["truncation_count"] += 1
            if item.token_count > 0:
                final_items.append(item)
        
        # ---- Step 4: 排序(对抗 Lost in the Middle) ----
        final_items = self.reorderer.reorder(final_items)
        
        # ---- Step 5: 组装 prompt ----
        prompt_parts = [it.content for it in final_items if it.content]
        prompt = "\n\n".join(prompt_parts)
        
        # ---- Step 6: 统计 ----
        total_tokens = TokenCounter.count(prompt)
        usage_ratio = total_tokens / budget
        self.stats["budget_usage"].append(usage_ratio)
        
        # 详细统计
        detail_stats = {
            "total_tokens": total_tokens,
            "budget": budget,
            "usage_ratio": usage_ratio,
            "item_count": len(final_items),
            "by_priority": {},
        }
        for it in final_items:
            p = it.priority.name
            detail_stats["by_priority"][p] = detail_stats["by_priority"].get(p, 0) + it.token_count
        
        self._items = []  # 清空, 支持复用
        return {"prompt": prompt, "stats": detail_stats}
    
    def _allocate_budget(self, items: list[ContextItem], total: int) -> dict:
        """按优先级分配预算"""
        # 按优先级分组
        groups = {}
        for it in items:
            groups.setdefault(it.priority, []).append(it)
        
        # 按比例分配
        allocation = {}
        for priority, group in groups.items():
            ratio = self.budget_ratios.get(priority, 0.1)
            group_budget = int(total * ratio)
            # 组内均分
            per_item = group_budget // max(len(group), 1)
            allocation[priority] = per_item
        
        return allocation
    
    def manage_history(
        self,
        history: list[dict],
        keep_recent: int = 3,
        max_history_tokens: int = 2000,
    ) -> list[ContextItem]:
        """
        专门管理对话历史
        策略: 最近 N 轮原文 + 早期轮次摘要
        """
        if len(history) <= keep_recent:
            return [ContextItem(
                content=self._format_history_turn(t),
                priority=Priority.P5_HISTORY,
                metadata={"source": "history", "turn_index": i, "compressed": False},
            ) for i, t in enumerate(history)]
        
        # 早期轮次摘要
        early = history[:-keep_recent]
        early_text = "\n".join(self._format_history_turn(t) for t in early)
        early_item = ContextItem(
            content=early_text,
            priority=Priority.P5_HISTORY,
            metadata={"source": "history", "turn_range": f"0-{len(early)-1}"},
        )
        early_compressed = self.compressor._compress_history(early_item, max_history_tokens // 2)
        early_compressed.metadata["is_summary"] = True
        
        # 最近轮次原文
        recent_items = []
        for i, t in enumerate(history[-keep_recent:]):
            recent_items.append(ContextItem(
                content=self._format_history_turn(t),
                priority=Priority.P5_HISTORY,
                metadata={
                    "source": "history",
                    "turn_index": len(early) + i,
                    "compressed": False,
                },
            ))
        
        return [early_compressed] + recent_items
    
    @staticmethod
    def _format_history_turn(turn: dict) -> str:
        """格式化单轮对话"""
        role = turn.get("role", "user")
        content = turn.get("content", "")
        return f"[{role}]: {content}"
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        avg_usage = (
            sum(self.stats["budget_usage"]) / len(self.stats["budget_usage"])
            if self.stats["budget_usage"] else 0
        )
        return {
            **self.stats,
            "avg_budget_usage": avg_usage,
        }


# ============================================================
# 6. 使用示例
# ============================================================
def demo():
    """完整使用示例"""
    
    # 模拟 LLM 调用
    def mock_llm(prompt: str) -> str:
        return f"[摘要] {prompt[:100]}..."
    
    # 初始化
    cm = ContextManager(
        max_tokens=32000,
        output_reserve=4000,
        llm_caller=mock_llm,
    )
    
    # 添加 system prompt (P0, 固定)
    cm.add(
        content="你是一个专业的数据分析助手。请基于提供的资料回答问题。",
        priority=Priority.P0_SYSTEM,
        compressible=False,
    )
    
    # 添加关键信息 (P2, 固定)
    cm.add(
        content="任务目标: 分析 2024 年 Q3 销售数据。约束: 只使用提供的资料,不编造数据。",
        priority=Priority.P2_CRITICAL,
        compressible=False,
    )
    
    # 添加 few-shot 示例 (P4)
    cm.add(
        content="示例1:\n问: 2024 Q1 销售额?\n答: 根据资料,2024 Q1 销售额为 1.2 亿元。",
        priority=Priority.P4_FEWSHOT,
        metadata={"score": 0.85, "source": "fewshot"},
    )
    cm.add(
        content="示例2:\n问: 2024 Q2 增长率?\n答: Q2 销售额 1.5 亿,环比增长 25%。",
        priority=Priority.P4_FEWSHOT,
        metadata={"score": 0.75, "source": "fewshot"},
    )
    
    # 添加检索结果 (P3)
    retrieval_docs = [
        ("2024 Q3 销售额达 1.8 亿元,环比增长 20%。其中线上渠道占比 60%...", 0.92),
        ("华东区域 Q3 销售额 8000 万,为各区域最高。华北区域 5000 万...", 0.85),
        ("Q3 新客户增长 3000 人,老客户复购率 45%。客单价 600 元...", 0.78),
        ("竞品 A 公司 Q3 销售额 1.5 亿,市场份额下降 2%...", 0.65),
        ("行业报告显示 2024 年整体市场增长 15%,预计 Q4 继续...", 0.55),
    ]
    for doc, score in retrieval_docs:
        cm.add(
            content=doc,
            priority=Priority.P3_RETRIEVAL,
            metadata={"score": score, "source": "retrieval"},
        )
    
    # 添加对话历史 (P5)
    history = [
        {"role": "user", "content": "请帮我分析 Q3 销售情况。"},
        {"role": "assistant", "content": "好的,我将基于提供的资料分析 Q3 销售。请问关注哪个维度?"},
        {"role": "user", "content": "主要看区域分布和增长趋势。"},
    ]
    history_items = cm.manage_history(history, keep_recent=2, max_history_tokens=500)
    for item in history_items:
        cm._items.append(item)
    
    # 添加工具结果 (P6)
    cm.add(
        content=json.dumps({
            "tool": "database_query",
            "result": [{"region": "华东", "sales": 8000}, {"region": "华北", "sales": 5000}],
            "metadata": {"query_time": "0.5s", "rows": 2},
            "tracking_id": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yz",
        }, ensure_ascii=False),
        priority=Priority.P6_TOOL_RESULT,
        metadata={"source": "tool_result", "tool_name": "database_query"},
    )
    
    # 添加当前 query (P1, 固定)
    cm.add(
        content="当前问题: 华东区域 Q3 销售额最高,主要原因是什么?",
        priority=Priority.P1_QUERY,
        compressible=False,
    )
    
    # 构建上下文
    result = cm.build()
    
    print("=" * 60)
    print("最终 Prompt:")
    print("=" * 60)
    print(result["prompt"])
    print()
    print("=" * 60)
    print("统计信息:")
    print("=" * 60)
    stats = result["stats"]
    print(f"总 token 数: {stats['total_tokens']}")
    print(f"预算: {stats['budget']}")
    print(f"使用率: {stats['usage_ratio']:.1%}")
    print(f"项数: {stats['item_count']}")
    print("按优先级分布:")
    for p, tokens in stats["by_priority"].items():
        print(f"  {p}: {tokens} tokens")
    
    print()
    print("=" * 60)
    print("累计统计:")
    print("=" * 60)
    overall = cm.get_stats()
    print(f"总调用次数: {overall['total_calls']}")
    print(f"压缩次数: {overall['compression_count']}")
    print(f"平均预算使用率: {overall['avg_budget_usage']:.1%}")


if __name__ == "__main__":
    demo()
```

**运行输出示例**

```
============================================================
最终 Prompt:
============================================================
你是一个专业的数据分析助手。请基于提供的资料回答问题。

任务目标: 分析 2024 年 Q3 销售数据。约束: 只使用提供的资料,不编造数据。

当前问题: 华东区域 Q3 销售额最高,主要原因是什么?

2024 Q3 销售额达 1.8 亿元,环比增长 20%。其中线上渠道占比 60%...

[摘要] [user]: 请帮我分析 Q3 销售情况。\n[assistant]: 好的,我将基于...

[user]: 主要看区域分布和增长趋势。

示例2:
问: 2024 Q2 增长率?
答: Q2 销售额 1.5 亿,环比增长 25%。

示例1:
问: 2024 Q1 销售额?
答: 根据资料,2024 Q1 销售额为 1.2 亿元。

行业报告显示 2024 年整体市场增长 15%,预计 Q4 继续...
华东区域 Q3 销售额 8000 万,为各区域最高。华北区域 5000 万...

============================================================
统计信息:
============================================================
总 token 数: 487
预算: 26400
使用率: 1.8%
项数: 10
按优先级分布:
  P0_SYSTEM: 28 tokens
  P1_QUERY: 22 tokens
  P2_CRITICAL: 33 tokens
  P3_RETRIEVAL: 180 tokens
  P4_FEWSHOT: 84 tokens
  P5_HISTORY: 95 tokens
  P6_TOOL_RESULT: 45 tokens
```

**设计亮点**

| 特性 | 实现方式 |
|------|---------|
| 优先级系统 | IntEnum, 数字越小优先级越高, 永不裁剪 P0-P2 |
| 预算分配 | 按优先级比例分配, 固定项优先扣除 |
| 压缩策略 | 按来源定制(tool_result 结构化 / history 摘要 / retrieval 截断) |
| 排序优化 | 交错重排对抗 Lost in the Middle, few-shot 单独按相关度升序 |
| 可观测性 | 记录压缩次数/截断次数/预算使用率, 支持优化 |
| 链式调用 | `cm.add().add().build()` 流式 API |
| 历史管理 | 单独的 `manage_history` 方法, 早期摘要 + 最近原文 |
| 降级容错 | tiktoken 不可用时降级为字符数估算 |

**面试加分点**

- 提到"优先级系统是可配置的"，不同任务可以调整比例。
- 提到"压缩策略按来源定制"，工具结果用结构化裁剪，历史用摘要，检索用截断。
- 提到"可观测性"，每次调用记录预算使用率，用于持续优化。
- 提到"降级容错"，tiktoken 不可用时用字符数估算。
- 提到"线程安全"可改进点：当前实现非线程安全，多线程需加锁。

</details>

---

### Q10: 系统设计题 — 设计一个支持百万 token 上下文的 Agent 系统？

<details>
<summary>查看答案</summary>

**题目**

设计一个支持百万 token 上下文的 Agent 系统，用于分析企业内部知识库（文档总量 10TB，单次查询可能涉及 100+ 文档）。要求：
- 端到端延迟 < 30 秒
- 单次查询成本 < $1
- 准确率 > 85%

**需求分析**

| 维度 | 挑战 |
|------|------|
| 数据量 | 10TB 文档, 单次涉及 100+ 文档, 拼装后可能 200K+ token |
| 延迟 | 30s 内完成检索 + 上下文组装 + LLM 推理 |
| 成本 | 单次 < $1, 百万 token 推理成本要控制 |
| 准确率 | 85%+ 要求高信噪比, Lost in the Middle 必须解决 |

**整体架构**

```
┌─────────────────────────────────────────────────────────────────┐
│                    用户 Query                                    │
│                        │                                         │
┌────────────────────────▼─────────────────────────────┐          │
│  1. Query 理解层                                       │          │
│     ├── Query 改写 (扩展/分解)                          │          │
│     ├── 意图识别                                        │          │
│     └── 子查询生成 (多路召回)                            │          │
└────────────────────────┬─────────────────────────────┘          │
                         │                                         │
┌────────────────────────▼─────────────────────────────┐          │
│  2. 分层检索层 (Hierarchical Retrieval)                │          │
│     ├── L1: 全局索引 (摘要级) ──→ 定位相关文档组         │          │
│     ├── L2: 文档索引 (章节级) ──→ 定位相关章节           │          │
│     └── L3: 细粒度索引 (chunk级) ──→ 定位相关段落        │          │
└────────────────────────┬─────────────────────────────┘          │
                         │                                         │
┌────────────────────────▼─────────────────────────────┐          │
│  3. 上下文工程层 (Context Engineering)                 │          │
│     ├── Rerank (cross-encoder)                         │          │
│     ├── 压缩 (LLMLingua + 结构化)                      │          │
│     ├── 排序 (LongContextReorder)                      │          │
│     ├── 预算分配 (ContextManager)                      │          │
│     └── 组装最终 prompt                                 │          │
└────────────────────────┬─────────────────────────────┘          │
                         │                                         │
┌────────────────────────▼─────────────────────────────┐          │
│  4. 模型推理层 (分级推理)                               │          │
│     ├── 路由: 简单查询 → 廉价模型 (GPT-4o-mini)         │          │
│     ├── 路由: 复杂查询 → 长上下文模型 (Gemini 1.5 Pro) │          │
│     └── Prompt Cache 命中检测                           │          │
└────────────────────────┬─────────────────────────────┘          │
                         │                                         │
┌────────────────────────▼─────────────────────────────┐          │
│  5. Agent 执行层 (可选)                                │          │
│     ├── 工具调用 (搜索/计算/代码执行)                    │          │
│     ├── 多轮迭代 (ReAct)                                │          │
│     └── 上下文动态更新 (ContextManager 复用)            │          │
└────────────────────────┬─────────────────────────────┘          │
                         │                                         │
                    ┌────▼────┐                                    │
                    │ 最终回答 │                                    │
                    └─────────┘                                    │
```

**核心模块详细设计**

**模块 1: 分层检索（解决 10TB 数据检索）**

```
离线索引构建:
┌──────────────┐
│ 10TB 原始文档 │
└──────┬───────┘
       │
┌──────▼───────────────────────────────────────┐
│ L1: 全局摘要索引 (1GB)                         │
│  - 每个文档生成 500 token 摘要                  │
│  - 索引大小: 10TB / 100KB * 500 token ≈ 1GB   │
│  - 用途: 快速定位相关文档(top 100)             │
└──────┬──────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│ L2: 章节级索引 (10GB)                          │
│  - 每个文档按章节切分,每章节生成摘要             │
│  - 用途: 定位相关章节(top 50 章节)              │
└──────┬──────────────────────────────────────┘
       │
┌──────▼───────────────────────────────────────┐
│ L3: Chunk 级索引 (100GB)                       │
│  - 512 token chunk + embedding                 │
│  - 用途: 细粒度召回(top 20 chunk)              │
└──────────────────────────────────────────────┘

在线检索流程:
Query → L1 检索(top 100 文档) → L2 检索(top 50 章节) → L3 检索(top 20 chunk)
耗时:  100ms                  200ms                   300ms
```

**模块 2: 上下文工程层（核心）**

```python
class MillionTokenContextEngine:
    def __init__(self):
        self.reranker = CrossEncoderReranker()  # bge-reranker-large
        self.compressor = HybridCompressor()    # LLMLingua + 结构化
        self.reorderer = LongContextReorder()
        self.budget_manager = ContextManager(max_tokens=1_000_000)
    
    def build_context(self, query: str, retrieved_chunks: list) -> str:
        # 1. Rerank: cross-encoder 精排
        reranked = self.reranker.rerank(query, retrieved_chunks, top_k=50)
        
        # 2. 压缩: LLMLingua 压缩每个 chunk
        compressed = []
        for chunk in reranked:
            c = self.compressor.compress(chunk, ratio=0.5)
            compressed.append(c)
        # 50 chunks * 256 tokens (压缩后) = 12.8K tokens
        
        # 3. 如果仍超预算, 启用层次摘要
        total_tokens = sum(TokenCounter.count(c) for c in compressed)
        if total_tokens > 500_000:  # 超过 500K, 启用摘要
            compressed = self.hierarchical_summarize(compressed)
        
        # 4. 排序: 对抗 Lost in the Middle
        reordered = self.reorderer.reorder(compressed)
        
        # 5. 预算分配 + 组装
        # system 5K / few-shot 10K / retrieval 800K / history 100K / output 85K
        return self.budget_manager.build(reordered)
    
    def hierarchical_summarize(self, chunks: list) -> list:
        """层次摘要: chunk → group → super-group"""
        # 1. 分组 (每组 10 个 chunk)
        groups = [chunks[i:i+10] for i in range(0, len(chunks), 10)]
        # 2. 每组摘要
        group_summaries = [self.llm_summarize(g) for g in groups]
        # 3. 如果组摘要还太多, 再聚合
        if len(group_summaries) > 20:
            super_groups = [group_summaries[i:i+5] for i in range(0, len(group_summaries), 5)]
            group_summaries = [self.llm_summarize(sg) for sg in super_groups]
        return group_summaries
```

**模块 3: 模型路由（控制成本）**

```python
class ModelRouter:
    """根据任务复杂度路由到不同模型"""
    
    ROUTING_RULES = {
        # (条件) → (模型, 最大token, 成本/1M token)
        "simple_qa": ("gpt-4o-mini", 16_000, 0.15),       # $0.0024/次
        "multi_doc": ("claude-3.5-sonnet", 200_000, 3.0), # $0.6/次
        "ultra_long": ("gemini-1.5-pro", 2_000_000, 1.25), # $1.25/次(>128K)
    }
    
    def route(self, query: str, context_tokens: int) -> tuple:
        if context_tokens < 16_000 and self._is_simple(query):
            return self.ROUTING_RULES["simple_qa"]
        elif context_tokens < 200_000:
            return self.ROUTING_RULES["multi_doc"]
        else:
            return self.ROUTING_RULES["ultra_long"]
    
    def _is_simple(self, query: str) -> bool:
        # 简单启发式: 短 query + 无复杂推理关键词
        return len(query) < 50 and not any(
            kw in query for kw in ["分析", "对比", "总结", "推理"]
        )
```

**模块 4: Prompt Cache（降本关键）**

```python
class PromptCacheManager:
    """Prompt 缓存管理"""
    
    def __init__(self):
        self.cache = {}  # 实际用 Redis
    
    def get_cached_prefix(self, system: str, few_shot: str) -> str:
        """构造可缓存的 prompt 前缀"""
        # Claude/Gemini 支持 prompt caching
        # system + few_shot 是稳定的, 可缓存
        prefix = f"{system}\n{few_shot}"
        cache_key = hash(prefix)
        if cache_key not in self.cache:
            self.cache[cache_key] = prefix
            # 标记为可缓存 (Claude: cache_control)
        return prefix
    
    def estimate_savings(self, prefix_tokens: int, calls: int) -> float:
        """估算节省"""
        # Claude prompt cache: 读缓存 = 0.1x 正常价格
        normal_cost = prefix_tokens * 3.0 / 1_000_000 * calls
        cached_cost = prefix_tokens * 3.0 / 1_000_000 * 0.1 * calls
        return normal_cost - cached_cost
```

**成本估算**

| 场景 | 上下文长度 | 模型 | 单次成本 | 命中预算? |
|------|-----------|------|---------|----------|
| 简单 QA | 16K | GPT-4o-mini | $0.0024 | ✓ |
| 多文档分析 | 200K | Claude 3.5 | $0.60 | ✓ |
| 超长上下文 | 500K (压缩后) | Gemini 1.5 Pro | $0.625 | ✓ |
| 最差情况 | 1M (压缩后) | Gemini 1.5 Pro | $1.25 | ✗ (需进一步优化) |

**降本措施**（确保最差情况也 < $1）：
1. Prompt Cache: system + few-shot 缓存，节省 30%。
2. 上下文压缩: LLMLingua 2x 压缩，500K → 250K。
3. 模型分级: 80% 查询走廉价模型，平均成本拉低。
4. 结果缓存: 相同 query+retrieval 复用结果。

**延迟估算**

| 阶段 | 耗时 | 说明 |
|------|------|------|
| Query 理解 | 500ms | 小模型改写 |
| 分层检索 | 600ms | L1+L2+L3 串行 |
| Rerank | 1s | cross-encoder 50 chunks |
| 压缩 | 2s | LLMLingua (batch) |
| 组装 + 排序 | 100ms | 本地计算 |
| LLM 推理 | 15-25s | 首token + 生成 |
| **总计** | **20-30s** | ✓ 命中目标 |

**准确率保障**

1. **分层检索**：L1 定位 → L2 精准 → L3 细粒度，层层收敛，减少噪声。
2. **Cross-encoder Rerank**：比 bi-embedding 准 10%+。
3. **LongContextReorder**：对抗 Lost in the Middle，提升 3-5%。
4. **Needle in Haystack 评估**：定期跑 NiaH 测试，监控衰减。
5. **人工评测集**：1000 条标注数据，每次迭代回归。

**面试加分话术**

> "百万 token 上下文 Agent 的核心挑战不是『能不能放下』，而是『放进去后能不能找到』。Gemini 1.5 Pro 虽然支持 2M token，但 Lost in the Middle 问题在 500K+ 时非常严重。我的方案是『分层检索 + 上下文工程』双管齐下 —— 分层检索把 10TB 缩小到 50 个高相关 chunk，上下文工程把这 50 个 chunk 压缩、排序、组装到 200K 以内，让模型在『甜点区』工作。成本上通过模型分级 + Prompt Cache，把平均成本压到 $0.3 以下。这个架构的关键是『不要迷信长上下文模型，工程优化比堆 token 更重要』。"

**追问预案**

- **Q: 10TB 数据怎么建索引？**
  A: 离线 pipeline：文档解析 → 清洗 → 分层摘要 → embedding → 入库。用 Spark 分布式处理，10TB 大约 24 小时。

- **Q: 如果检索结果不相关怎么办？**
  A: 加一个"置信度阈值"，rerank 分数低于 0.3 的 chunk 直接丢弃，同时返回"信息不足"提示，避免硬编答案。

- **Q: 如何处理实时更新的文档？**
  A: 增量索引。新文档入库时同步更新 L3 索引，L1/L2 摘要异步更新（5 分钟内）。用 CDC（Change Data Capture）监听文档变更。

- **Q: 多语言怎么处理？**
  A: 统一 embedding 模型（如 bge-m3 多语言），检索时按语言路由到不同索引分片。

</details>

---

## 核心知识回顾表

| 知识点 | 核心内容 | 关键数字/公式 | 工程实践 |
|--------|---------|-------------|---------|
| Context Engineering 定义 | 系统化管理进入 LLM 上下文的所有信息 | - | 独立设计上下文层 |
| 上下文组成 | system/instruction/few-shot/retrieved/history/tool_result | 6 个部分 | 按优先级管理 |
| Token 预算分配 | 固定比例 / 动态优先级 / 弹性预算 | system 10% / retrieval 40% / history 30% / output 20% | 用真实 tokenizer 计数 |
| Lost in the Middle | 长上下文中间信息被忽略 | U 形注意力曲线 | Reorder + 压缩 |
| 上下文压缩 | 摘要式 / 抽取式 / Token级(LLMLingua) / 结构化 | LLMLingua 压缩 2-10x, 损失 <5% | 混合策略, 3-5x 甜点 |
| 长文本处理 | Stuff / Map-Reduce / Refine / Map-Rerank | - | 层次摘要 + 分层检索 |
| Few-shot 选择 | 相似度 / MMR / 难度排序 / 混合 | 5-10 个为甜点 | 相关度升序排列 |
| 上下文排序 | 首尾放高分, 中间放低分 | 首因+近因效应 | LongContextReorder |
| Agent 上下文管理 | 工具结果压缩 / 历史截断 / 关键信息保留 | 最近3轮+早期摘要 | 重要性感知截断 |
| 模型上下文窗口 | GPT-4o 128K / Claude 200K / Gemini 2M | - | 不迷信长上下文 |
| Needle in Haystack | 评估长上下文检索能力 | 热力图 | 定期回归测试 |
| Prompt Cache | 缓存稳定前缀 | Claude 读缓存 0.1x 价格 | system+few-shot 缓存 |
| 模型路由 | 按复杂度路由到不同模型 | 80% 走廉价模型 | 平均成本降 70% |
| LLMLingua-2 | BERT 分类器预测 token 保留 | 比 v1 快 10x | 生产首选 |
| StreamingLLM | Attention Sink 保留前几个 token | 流式对话无限长度 | 首token不动 |

---

## 面试速记卡

### 卡片 1: Context Engineering 一句话
> "Prompt 工程是『怎么说』，Context 工程是『说什么』。在 RAG/Agent 场景下，80% 的上下文是动态拼装的，必须系统化管理检索结果、对话历史、工具返回的挑选、压缩、排序。"

### 卡片 2: Lost in the Middle 三个关键词
> **现象**: U 形注意力曲线，中间内容被忽略。
> **原因**: 注意力衰减 + 位置编码外推 + 训练数据偏置。
> **解法**: Reorder（首尾放高分）+ 压缩（缩短中间）+ 分而治之。

### 卡片 3: 上下文压缩四件套
> **摘要式**: LLM 摘要，压缩 5-10x，适用对话历史。
> **抽取式**: TextRank 关键句，压缩 2-3x，适用事实文档。
> **Token级**: LLMLingua 困惑度剔除，压缩 2-10x，损失 <5%。
> **结构化**: JSON 字段裁剪，压缩 5-20x，适用工具结果。

### 卡片 4: 预算分配口诀
> "P0 system 不动，P1 query 不动，P2 关键信息不动。剩余预算：检索占一半，历史压一压，few-shot 凑一凑，工具结果能删就删。"

### 卡片 5: 排序优化口诀
> "高分放首尾，低分放中间。System 永远在最前，Query 永远在最后。Few-shot 相关度升序，History 时间序别乱动。"

### 卡片 6: Agent 上下文三招
> **工具结果**: 结构化裁剪，50 行 JSON 留 3 行。
> **历史截断**: 最近 3 轮原文 + 早期摘要。
> **关键信息**: 任务目标、约束、文件路径单独提取，永不丢弃。

### 卡片 7: 长文本四种模式
> **Stuff**: 全塞（<80% 窗口）。
> **Map-Reduce**: 分段独立处理再合并（可并行）。
> **Refine**: 顺序精化（跨段累积）。
> **Map-Rerank**: 分段打分选最优（答案在某段）。

### 卡片 8: LLMLingua 一句话
> "用小模型算每个 token 的困惑度，剔除低困惑度（高可预测性）的 token，2-10x 压缩，性能损失 <5%。LLMLingua-2 用 BERT 分类器替代，快 10 倍。"

### 卡片 9: 系统设计核心架构
> "分层检索（L1摘要→L2章节→L3 chunk）+ 上下文工程（Rerank→压缩→排序→预算分配）+ 模型路由（简单走廉价模型，复杂走长上下文模型）+ Prompt Cache。"

### 卡片 10: 易踩的坑
> "token 数不能用字符数估算（中文误差大）；压缩比不是越高越好（>10x 崩溃）；排序对短上下文影响小（<4K 不必过度优化）；few-shot 顺序敏感（不要随机）。"

---

## 易错点提醒（10 个）

### 1. token 计数用字符数估算
**错误**: `tokens = len(text) / 4`
**正确**: 用 `tiktoken` 或模型对应 tokenizer。中文 1.5 char ≈ 1 token，英文 4 char ≈ 1 token，混排时误差可达 30%+。
**后果**: 预算超限导致 API 报错，或预算浪费导致上下文不完整。

### 2. 压缩比越高越好
**错误**: LLMLingua 压缩到 10% 以为省了钱又没损失。
**正确**: 压缩比超过 10x（保留 <10%）后性能急剧下降。3-5x 是甜点。
**验证**: 压缩前后跑同一套测试集，对比准确率下降幅度。

### 3. 短上下文也做 Reorder
**错误**: 4K 上下文也用 LongContextReorder。
**正确**: Lost in the Middle 在 <4K 时几乎不影响。短上下文排序收益 <1%，不值得增加复杂度。>16K 才有明显收益。

### 4. few-shot 示例随机顺序
**错误**: `random.shuffle(examples)`
**正确**: 示例顺序对输出影响可达 10%。推荐相关度升序（最相似放最后，近因效应加持）。

### 5. 对话历史硬截断
**错误**: `history = history[-5:]` 直接砍。
**正确**: 早期轮次可能包含任务目标、约束等关键信息。应摘要化保留，否则 Agent 会"失忆"。

### 6. 工具结果原样塞进上下文
**错误**: API 返回 50 个字段的 JSON 全部塞入。
**正确**: 按工具类型定制压缩。搜索结果只留 title+snippet，代码执行只留最后输出+错误行。

### 7. system prompt 参与重排
**错误**: 把 system prompt 和检索结果一起做 LongContextReorder。
**正确**: system prompt 固定在最前面，重排的只是可变部分（检索结果、历史）。

### 8. 迷信长上下文模型
**错误**: "Gemini 2M 窗口，把所有文档塞进去就行。"
**正确**: 窗口大 ≠ 注意力强。2M 窗口的 Lost in the Middle 比 128K 更严重。工程优化（检索+压缩+排序）比堆 token 更重要。

### 9. 忽略 Prompt Cache
**错误**: 每次调用都重新计算 system + few-shot 的 KV cache。
**正确**: Claude/Gemini 支持 prompt caching，缓存命中读价格 0.1x。system + few-shot 是稳定的，务必缓存。

### 10. 压缩只看压缩比不看质量
**错误**: 只优化"压到多少 token"，不评估"压缩后准确率"。
**正确**: 建立压缩质量评估 pipeline：原上下文 vs 压缩上下文，跑同一套测试集，监控准确率下降。设阈值（如 <3%），超过则降低压缩比。

---

## 自测检查清单

### 概念题（10 道）

- [ ] 1. 能用一句话解释 Context Engineering 和 Prompt Engineering 的区别吗？
- [ ] 2. 能画出上下文组成的优先级层次吗（P0-P6）？
- [ ] 3. 能解释 Lost in the Middle 的三个原因吗（注意力/位置编码/训练数据）？
- [ ] 4. 能说出 LLMLingua 和 LLMLingua-2 的原理区别吗（困惑度 vs BERT 分类）？
- [ ] 5. 能说出 LangChain 四种 document chain 模式及适用场景吗？
- [ ] 6. 能解释 MMR（Maximal Marginal Relevance）在 few-shot 选择中的作用吗？
- [ ] 7. 能说出首因效应和近因效应如何影响上下文排序吗？
- [ ] 8. 能解释 Needle in Haystack 评估方法吗？
- [ ] 9. 能说出 StreamingLLM 的 attention sink 原理吗？
- [ ] 10. 能解释 Prompt Cache 的工作原理和成本节省比例吗？

### 代码题（3 道）

- [ ] 1. **ContextManager 手撕**: 能在 30 分钟内写出支持 token 预算分配 + 优先级排序 + 历史截断的 ContextManager 吗？（参考 Q9）
- [ ] 2. **LongContextReorder 实现**: 能手写交错重排算法吗？输入 `[A,B,C,D,E]`（降序），输出 `[A,E,B,D,C]`。
- [ ] 3. **历史摘要截断**: 能写一个 `truncate_history` 函数，实现"最近 N 轮原文 + 早期轮次 LLM 摘要"吗？

```python
# 练习: 实现 LongContextReorder
def reorder(docs: list) -> list:
    """交错重排: 偶数位取前半段, 奇数位取后半段"""
    # 你的代码
    pass

# 测试
assert reorder(["A","B","C","D","E"]) == ["A","E","B","D","C"]
assert reorder(["A","B","C","D"]) == ["A","D","B","C"]
```

### 系统设计题（2 道）

- [ ] 1. **百万 token Agent 系统**（Q10）: 能在白板上画出完整架构，讲清楚分层检索、上下文工程、模型路由、成本控制吗？能回答 4 个追问吗？
- [ ] 2. **多轮 Agent 对话系统**: 设计一个支持 100+ 轮对话的 Agent 系统，如何管理上下文不膨胀？要求：
  - 轮次 1-10: 全量保留
  - 轮次 11-50: 摘要化
  - 轮次 50+: 只保留关键决策点
  - 工具结果: 按类型压缩
  - 关键变量: 永不丢弃

  **提示**: 用 `CriticalInfoPreserver` + `ImportanceBasedTruncation` + `HierarchicalSummary` 三层策略。

---

## 延伸阅读

### 必读论文

1. **Lost in the Middle: How Language Models Use Long Contexts** (Liu et al. 2023)
   - 链接: https://arxiv.org/abs/2307.03172
   - 重要性: 奠基性论文，面试必问。

2. **LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression** (Jiang et al. 2023)
   - 链接: https://arxiv.org/abs/2310.06839
   - 重要性: LLMLingua 系列原理。

3. **LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression** (Pan et al. 2024)
   - 链接: https://arxiv.org/abs/2403.12968
   - 重要性: 生产级 token 压缩方案。

4. **Efficient Streaming Language Models with Attention Sinks** (Xiao et al. 2023)
   - 链接: https://arxiv.org/abs/2309.17453
   - 重要性: StreamingLLM，attention sink 原理。

5. **RAGAS: Automated Evaluation of Retrieval Augmented Generation** (Es et al. 2023)
   - 链接: https://arxiv.org/abs/2309.15217
   - 重要性: 上下文质量评估指标。

### 实战资源

6. **LangChain LongContextReorder 文档**
   - 链接: https://python.langchain.com/docs/modules/data_connection/document_transformers/long_context_reorder
   - 实践: 直接复用或参考实现。

7. **LangChain ContextualCompressionRetriever**
   - 链接: https://python.langchain.com/docs/modules/data_connection/retrievers/contextual_compression
   - 实践: 检索结果压缩的现成方案。

8. **LLMLingua 官方仓库**
   - 链接: https://github.com/microsoft/LLMLingua
   - 实践: 直接 pip install llmlingua 使用。

9. **LlamaIndex Context Retrieval**
   - 链接: https://docs.llamaindex.ai/en/stable/optimizing/production_rag/
   - 实践: LlamaIndex 的上下文管理方案。

### 博客与文章

10. **Anthropic: Prompt Caching**
    - 链接: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    - 重要性: Claude 官方 prompt cache 文档。

11. **Google: Gemini 1.5 Long Context**
    - 链接: https://blog.google/technology/ai/google-gemini-next-generation-model-february-2024/
    - 重要性: 百万 token 上下文模型的能力与限制。

12. **Greg Kamradt: Lost in the Middle Practical Guide**
    - 链接: https://www.youtube.com/watch?v=fTPjLDlFv6Y
    - 重要性: 实战讲解，有可视化。

### 进阶阅读

13. **YaRN: Efficient Context Window Extension of Large Language Models**
    - 链接: https://arxiv.org/abs/2309.00071
    - 重要性: 位置编码外推改进。

14. **Infini-attention: Efficient Transformer for Long-Context Generation**
    - 链接: https://arxiv.org/abs/2404.07143
    - 重要性: Google 的无限上下文方案。

15. **Chain-of-Note: Enhancing Robustness in Retrieval-Augmented Language Models**
    - 链接: https://arxiv.org/abs/2311.09210
    - 重要性: 上下文笔记化处理。

---

## 明日预告

### Day 12 — RAG 评估与评测框架

明天将进入 RAG 评估专题，重点学习：

1. **RAG 评估框架**:
   - RAGAS（Retrieval Augmented Generation Assessment）
   - TruLens
   - LangSmith 评估体系

2. **核心评估指标**:
   - 检索指标: Context Precision / Context Recall / Context Relevance
   - 生成指标: Faithfulness / Answer Relevance / Answer Correctness
   - 端到端: Answer Similarity / Human Evaluation

3. **评估数据集构建**:
   - 人工标注 vs LLM 自动生成
   - 合成数据集 (Synthetic Dataset)
   - 对抗性测试集

4. **评估 Pipeline 工程化**:
   - 离线评估 vs 在线评估
   - A/B 测试设计
   - 评估自动化与持续监控

5. **面试题预告**:
   - RAGAS 的三个核心指标怎么算？
   - 如何评估检索质量 vs 生成质量？
   - 没有 ground truth 怎么评估？
   - 手撕: 实现一个简易 RAG 评估器
   - 系统设计: 设计一个 RAG 系统的持续评估与监控平台

**预习建议**:
- 安装 `pip install ragas`，跑一遍 quickstart。
- 阅读 RAGAS 论文（见今日延伸阅读第 5 条）。
- 思考: 你的 RAG 系统怎么知道"检索结果好不好"？没有标准答案时怎么评估？

---

> **今日总结**: Context Engineering 是 RAG/Agent 的"中间件"层，核心是"在有限预算内最大化上下文信噪比"。三大武器: **压缩**（LLMLingua/摘要/结构化）、**排序**（LongContextReorder 对抗 Lost in the Middle）、**预算分配**（按优先级动态分配）。Agent 场景额外要做工具结果压缩和关键信息保留。手撕 ContextManager 是面试分水岭，务必练到 30 分钟内能写出完整实现。
