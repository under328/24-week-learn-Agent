# Day 12 — RAG 评估与评测框架

> **学习目标**:掌握 RAG 系统评估的完整方法论,包括三层评估框架、RAGAS 核心指标、检索/生成质量度量、LLM-as-Judge 实现、A/B 测试设计、持续监控体系,并能手撕评估代码与设计企业级评估平台。
>
> **面试定位**:这是 RAG 方向的高频考点,也是区分"会调 API"和"会做工程"的分水岭。面试官常通过"你的 RAG 系统怎么评估"这一开放题,考察候选人是否真正上过线、踩过坑。今天内容在中等难度面试中出现概率 **>85%**,在资深岗(>=P6)中**必考**。
>
> **预计学习时长**:4-5 小时(含代码实操)
>
> **前置依赖**:Day8-RAG 全链路、Day9-Agentic RAG、Day10-向量数据库、Day11-上下文工程

---

## 今日知识图谱

```
RAG 评估与评测框架
│
├── 1. 评估方法论 (Why & How)
│   ├── 三层评估框架: 检索 → 生成 → 端到端
│   ├── 与传统 NLP 评估的本质差异
│   └── 离线评估 vs 在线评估
│
├── 2. RAGAS 框架 (核心)
│   ├── Faithfulness (忠实度) ──── 生成答案是否忠于上下文
│   ├── Answer Relevancy (答案相关性) ── 答案是否回应了问题
│   ├── Context Precision (上下文精度) ── 检索结果中相关比例
│   └── Context Recall (上下文召回) ── 检索是否覆盖了答案所需信息
│
├── 3. 检索质量指标 (Retrieval Metrics)
│   ├── Recall@K ──────── 前 K 个结果中命中相关文档的比例
│   ├── Hit@K ─────────── 前 K 个中是否至少命中一个
│   ├── MRR ───────────── 第一个相关文档的倒数排名
│   └── NDCG@K ────────── 考虑相关度分级和位置折扣的累积增益
│
├── 4. 生成质量评估 (Generation Metrics)
│   ├── Faithfulness vs Answer Relevancy 的正交关系
│   ├── LLM-as-Judge 实现 (单评分/成对比较/参考答案对比)
│   ├── 人工评估 (Likert/成对/Best-Worst Scaling)
│   └── 自动化指标陷阱 (BLEU/ROUGE 为何不适合 RAG)
│
├── 5. 评估数据集构建
│   ├── 用户查询日志挖掘
│   ├── LLM 合成生成 (Synthetic Data)
│   ├── 数据增强 (改写/扰动)
│   ├── 人工标注规范设计
│   └── 低成本方案分层策略
│
├── 6. A/B 测试与实验设计
│   ├── 假设设计 (H0/H1)
│   ├── 指标体系 (OEC + 护栏指标)
│   ├── 样本量计算 (功效分析)
│   ├── 显著性检验 (含多重比较校正)
│   └── 辛普森悖论与分流哈希
│
├── 7. 持续监控体系
│   ├── L1 系统指标 (延迟/QPS/错误率)
│   ├── L2 业务指标 (满意度/采纳率/重写率)
│   └── L3 质量指标 (Faithfulness 离线采样/在线 LLM 抽检)
│
└── 8. 工程实战
    ├── Faithfulness 突然下降的排查 SOP
    ├── 评估平台设计 (多项目/版本/实验)
    └── 常见反模式与避坑
```

---

## 面试题(共 10 道)

### Q1: 为什么 RAG 评估比传统 NLP 评估复杂? 请描述 RAG 评估的三层框架。

<details>
<summary>展开答案</summary>

#### 传统 NLP 评估为何"简单"

传统任务(MT、NER、分类)有**固定输入 → 固定输出**的映射,评估指标确定(MT 用 BLEU,分类用 F1),且人工标注成本可控。但 RAG 系统的输出依赖三个高度不确定的环节:

1. **检索器**输出是文档集合,且不同 embedding/top-k 策略差异巨大;
2. **生成器**输出是自然语言,同样的上下文可生成多个合法答案;
3. **用户查询**本身可能模糊、口语化、多轮,没有"标准答案"。

#### 三层评估框架

| 层次 | 评估对象 | 关键指标 | 是否需要标注 | 频率 |
|------|---------|---------|-------------|------|
| **L1 检索层** | Retriever 召回质量 | Recall@K、MRR、NDCG | 需要相关文档标注 | 离线 |
| **L2 生成层** | Generator 给定上下文的表现 | Faithfulness、Answer Relevancy | 可用 LLM-as-Judge | 离线+在线 |
| **L3 端到端** | 用户问题到答案的完整链路 | 用户满意度、答案正确性 | 需要人工/用户反馈 | 在线为主 |

#### 三层为何要分开

一个高频面试追问:**为什么不直接评估最终答案?**

答:因为**问题归因**。如果端到端准确率下降,你无法判断是检索没召回相关文档,还是召回了但生成器"幻觉"了。三层分离后:

- 检索层指标低 → 优化 embedding/chunk/retrieval top-k
- 生成层 Faithfulness 低但 Context Recall 高 → 优化 prompt/生成模型
- 生成层 Faithfulness 高但端到端差 → 检查 query rewriting / 多轮理解

#### 与传统 NLP 的本质差异总结

1. **无单一标准答案**:同一个问题可以有多个正确表述;
2. **链路长**:错误会累积,需要分层归因;
3. **依赖外部知识**:检索结果随知识库更新而变化,指标不可复现性高;
4. **评估成本高**:相关文档标注需领域专家,LLM-as-Judge 又引入"评估器偏差"。

**面试加分点**:提到"评估器偏差(Evaluator Bias)"——用 GPT-4 评估 GPT-3.5 生成的答案会有系统性偏好,需要做评估器校准(评估器自身用人工标注对齐)。

</details>

---

### Q2: 详细解释 RAGAS 框架的四大核心指标(Faithfulness / Answer Relevancy / Context Precision / Context Recall)的定义、计算方式,并指出每个指标对应哪一层评估。

<details>
<summary>展开答案</summary>

RAGAS(Retrieval-Augmented Generation Assessment)是 Esmaeilzadeh 等人 2023 年提出的 RAG 专用评估框架,核心思想是**尽量减少对人工标注的依赖**——只需要 `(query, generated_answer, retrieved_contexts)` 三元组即可计算大部分指标;若额外提供 `ground_truth_answer` 可解锁 Context Recall。

#### 指标全景

```
                 需要的输入
指标              | query | answer | context | ground_truth | 评估层
------------------|-------|--------|---------|--------------|--------
Faithfulness      |  ✓    |   ✓    |   ✓     |     ✗        |  生成层
Answer Relevancy  |  ✓    |   ✓    |   ✗     |     ✗        |  生成层
Context Precision |  ✓    |   ✗    |   ✓     |     ✓        |  检索层
Context Recall    |  ✓    |   ✗    |   ✓     |     ✓        |  检索层
```

#### (1) Faithfulness(忠实度)

**定义**:生成答案中的每个陈述是否都能从检索到的上下文中找到支持。衡量"幻觉"程度。

**计算步骤**(RAGAS 原始实现):
1. 用 LLM 将答案拆解为**原子陈述**(atomic statements)列表;
2. 对每个陈述,用 LLM 判断是否能从上下文中推断(verifiable);
3. 计算:`Faithfulness = 可验证陈述数 / 总陈述数`。

**示例**:
- Query: "GPT-4 的发布时间是?"
- Context: "GPT-4 于 2023 年 3 月 14 日由 OpenAI 发布,支持多模态输入。"
- Answer: "GPT-4 于 2023 年 3 月发布,它是 Anthropic 开发的模型。"

拆解为 3 个陈述:
1. "GPT-4 于 2023 年 3 月发布" → 可验证 ✓
2. "它是 Anthropic 开发的" → 不可验证 ✗(上下文说是 OpenAI)
3. (隐含"由某公司开发") → 部分可验证

Faithfulness = 1/2 = 0.5(注:具体拆解逻辑依实现而定)

#### (2) Answer Relevancy(答案相关性)

**定义**:生成的答案是否真正回应了用户的查询(不偏题、不啰嗦)。

**计算方式**(RAGAS 反向生成法):
1. 用 LLM 根据答案**反向生成 N 个可能的问题**;
2. 计算这些反向生成的问题与原始 query 的**余弦相似度**(用 embedding);
3. 取平均相似度作为 Answer Relevancy。

**直觉**:如果答案跑题了,反向生成的问题会与原 query 差异大;如果答案切题,反向问题应高度相似。

**示例**:答案是"巴黎是法国首都",原 query 是"法国首都是哪?"——反向生成的问题会是"某国的首都是哪?""哪个城市是法国首都?"等,与原 query 高度相似,得分高。

#### (3) Context Precision(上下文精度)

**定义**:检索结果中**相关文档排名靠前**的程度(类似 Precision 但考虑顺序)。

**计算公式**(RAGAS 使用 `precision@k` 的加权平均):

```
Context Precision = (1/总相关数) * Σ [ Precision@k * rel(k) ]
其中 Precision@k = (前k个中相关文档数) / k
     rel(k) = 第k个文档是否相关 (0或1)
```

**示例**:检索返回 5 个文档,相关标记为 `[1, 0, 1, 0, 0]`(第1、3个相关):
- Precision@1 = 1/1 = 1.0, rel(1)=1
- Precision@2 = 1/2 = 0.5, rel(2)=0
- Precision@3 = 2/3 = 0.67, rel(3)=1
- Precision@4 = 2/4 = 0.5, rel(4)=0
- Precision@5 = 2/5 = 0.4, rel(5)=0

Context Precision = (1/2) * (1.0*1 + 0.5*0 + 0.67*1 + 0.5*0 + 0.4*0) = (1/2) * 1.67 = **0.835**

#### (4) Context Recall(上下文召回)

**定义**:标准答案(ground truth)中的信息是否都被检索到的上下文覆盖。

**计算方式**:
1. 将 ground truth answer 拆解为原子陈述;
2. 对每个陈述,判断是否能从检索上下文中找到支持;
3. `Context Recall = 可支持陈述数 / 总陈述数`。

**直觉**:如果标准答案说"GPT-4 支持多模态,2023年3月发布",但检索上下文只包含发布时间没包含多模态信息,则 Context Recall = 1/2 = 0.5,说明检索召回不全。

#### 指标对应层次与诊断逻辑

| 指标低 | 病因 | 处方 |
|--------|------|------|
| Context Precision 低 | 检索器把相关文档排在后面 | 调 top-k、换 reranker、优化 embedding |
| Context Recall 低 | 检索器漏召回了相关文档 | 扩大 top-k、改善 chunk 策略、加入 query rewriting |
| Faithfulness 低 | 生成器编造了上下文中没有的内容 | 优化 prompt(加"仅基于上下文回答")、换更小但更服从的模型 |
| Answer Relevancy 低 | 答案跑题或冗余 | 优化 prompt、检查 query 理解环节 |

**面试加分点**:
1. 指出 RAGAS 的**自参考问题**——用 LLM 拆解陈述、用 LLM 判断可验证性,评估器本身可能出错,需要校准;
2. 提到 **RAGAS 之外的替代方案**:TruLens(RAG Triad: Context Relevance + Groundedness + Answer Relevance)、DeepEval、ARES,体现广度。

</details>

---

### Q3: 详细解释检索质量指标 Recall@K、Hit@K、MRR、NDCG@K 的定义、计算公式,能手算给定场景下的值,并说明各自适用场景。

<details>
<summary>展开答案</summary>

这四个是信息检索(IR)经典指标,RAG 评估中常用于评估 Retriever 召回质量。**必须能手算**。

#### 设定场景

假设有一个查询 q,知识库中**与 q 相关的文档**有 3 个:`D1, D3, D7`。检索器返回了 top-5 排序结果:`[D2, D1, D5, D3, D4]`。

相关标记(按返回顺序):`[0, 1, 0, 1, 0]`

#### (1) Hit@K

**定义**:top-K 个结果中**是否至少命中一个**相关文档。二元指标(0 或 1)。

**公式**:`Hit@K = 1 if 至少一个相关文档在 top-K 中 else 0`

**手算 Hit@5**:
- top-5 中有 D1、D3 两个相关文档 → **Hit@5 = 1**

**手算 Hit@1**:
- top-1 是 D2,不相关 → **Hit@1 = 0**

**适用场景**:用户只看第一个结果(如语音助手、单答案 QA),关心"有没有命中"。

#### (2) Recall@K

**定义**:top-K 个结果中命中的相关文档数占**所有相关文档总数**的比例。

**公式**:`Recall@K = |top-K 中相关文档数| / |所有相关文档数|`

**手算 Recall@5**:
- top-5 中相关:D1、D3 → 2 个
- 所有相关:3 个(D1、D3、D7)
- **Recall@5 = 2/3 ≈ 0.667**

**手算 Recall@1**:
- top-1 中相关:0 个
- **Recall@1 = 0/3 = 0**

**适用场景**:需要召回**全部**相关信息的场景(法律检索、文献综述、RAG 中的多文档聚合回答)。

#### (3) MRR(Mean Reciprocal Rank)

**定义**:第一个相关文档的**倒数排名**的均值(跨多个 query)。

**公式**:
- 单个 query:`RR = 1 / rank_of_first_relevant`
- 多 query 平均:`MRR = (1/Q) * Σ RR_q`

**手算(单 query)**:
- 第一个相关文档 D1 在第 2 位 → `RR = 1/2 = 0.5`
- **MRR(单 query) = 0.5**

**适用场景**:用户只关心**第一个正确答案**的场景(问答系统、搜索引擎第一页)。MRR 不关心后续相关文档的位置。

#### (4) NDCG@K(Normalized Discounted Cumulative Gain)

**定义**:考虑**相关度分级**(不仅 0/1)和**位置折扣**(靠后权重低)的指标,归一化到 [0,1]。

**计算三步**:

**Step 1: DCG@K** —— 累积增益,位置折扣

```
DCG@K = Σ_{i=1}^{K} (rel_i / log2(i + 1))
```

其中 `rel_i` 是第 i 位文档的相关度(可以是 0/1,也可以是分级如 0/1/2/3)。

**Step 2: IDCG@K** —— 理想情况下的 DCG(相关文档全排在最前)

```
IDCG@K = DCG@K when documents sorted by relevance descending
```

**Step 3: NDCG@K**

```
NDCG@K = DCG@K / IDCG@K
```

**手算 NDCG@5(二值相关)**:

返回序列相关性:`[0, 1, 0, 1, 0]`,K=5

DCG@5:
- i=1: rel=0, log2(2)=1 → 0/1 = 0
- i=2: rel=1, log2(3)≈1.585 → 1/1.585 ≈ 0.631
- i=3: rel=0, log2(4)=2 → 0/2 = 0
- i=4: rel=1, log2(5)≈2.322 → 1/2.322 ≈ 0.431
- i=5: rel=0, log2(6)≈2.585 → 0/2.585 = 0

DCG@5 = 0 + 0.631 + 0 + 0.431 + 0 = **1.062**

IDCG@5(理想排序:相关文档排在最前 [1, 1, 1, 0, 0],因为只有 3 个相关):
- i=1: 1/log2(2) = 1
- i=2: 1/log2(3) ≈ 0.631
- i=3: 1/log2(4) = 0.5
- i=4: 0
- i=5: 0

IDCG@5 = 1 + 0.631 + 0.5 = **2.131**

**NDCG@5 = 1.062 / 2.131 ≈ 0.498**

#### 四指标对比表

| 指标 | 是否考虑顺序 | 是否支持分级相关 | 是否需要全部相关数 | 典型场景 |
|------|------------|----------------|------------------|---------|
| Hit@K | ✗ | ✗ | ✗ | 单答案 QA |
| Recall@K | ✗ | ✗ | ✓ | 法律/文献综述 |
| MRR | ✓(仅第一个) | ✗ | ✗ | 搜索引擎 |
| NDCG@K | ✓(全部位置) | ✓ | ✓ | 推荐系统、多答案 RAG |

#### 选型建议

- **RAG 通用场景**:用 **Recall@K + NDCG@K** 组合,前者保召回下限,后者保排序质量;
- **单答案 QA**:用 **Hit@1 + MRR**;
- **有 reranker 的系统**:必看 **NDCG@K**(reranker 的价值就在于排序)。

**面试加分点**:提到 **MRR vs MAP** 的区别——MAP(Map Average Precision)考虑所有相关文档的位置,而 MRR 只考虑第一个;在多相关文档场景 MAP 更全面但 RAG 中 MRR 更常用(因为 RAG 通常只用 top-1 或 top-3 的内容生成)。

</details>

---

### Q4: 生成质量评估中 Faithfulness 和 Answer Relevancy 有什么区别? 如何用 LLM-as-Judge 实现? LLM-as-Judge 有哪些常见模式与陷阱?

<details>
<summary>展开答案</summary>

#### Faithfulness vs Answer Relevancy 的正交关系

这两个指标是**正交**的——可以一个高一个低:

```
                        Answer Relevancy
                        高              低
              ┌────────────────┬────────────────┐
Faithfulness  │  理想区域        │  答非所问       │
高            │  答案忠于上下文   │  但内容真实      │
              │  且回应了问题     │  却没回答问题    │
              ├────────────────┼────────────────┤
Faithfulness  │  幻觉式讨好       │  最差区域       │
低            │  看似回答了问题   │  既幻觉又跑题    │
              │  但编造了内容     │               │
              └────────────────┴────────────────┘
```

**示例对比**:

Query: "GPT-4 何时发布?"

| 答案 | Faithfulness | Answer Relevancy |
|------|--------------|------------------|
| "GPT-4 于 2023 年 3 月 14 日由 OpenAI 发布。" (上下文支持) | 高 | 高 |
| "GPT-4 于 2023 年 3 月发布,Anthropic 开发。" (编造公司) | 低 | 高 |
| "OpenAI 是一家 AI 公司,成立于 2015 年。" (上下文支持但跑题) | 高 | 低 |
| "GPT-4 由 Google 在 2022 年发布。" (编造且跑题) | 低 | 低 |

#### LLM-as-Judge 的三种常见模式

##### 模式 1: 单答案评分(Single Answer Scoring)

给 LLM 一个评分标准(rubric),让它对单个答案打分(1-5 分)。

```python
prompt = f"""
你是一个严格的评估员。请根据以下标准对答案打分(1-5):

评分标准:
- 5分: 答案完全忠于上下文,且完整回应了问题
- 3分: 答案基本忠于上下文,部分回应问题
- 1分: 答案与上下文矛盾,或完全未回应问题

问题: {query}
上下文: {context}
答案: {answer}

请输出 JSON: {{"score": <1-5>, "reason": "<理由>"}}
"""
```

**优点**:简单、可解释。
**缺点**:绝对评分不稳定(同一答案多次评分可能不同)。

##### 模式 2: 成对比较(Pairwise Comparison)

给 LLM 两个答案 A 和 B,问哪个更好。

```python
prompt = f"""
请比较以下两个答案,判断哪个更好。

问题: {query}
上下文: {context}
答案 A: {answer_a}
答案 B: {answer_b}

输出: "A"/"B"/"平局", 并说明理由。
"""
```

**优点**:相对判断更稳定,适合 A/B 测试。
**缺点**:**位置偏差**——LLM 倾向于选第一个;需要做 swap(交换 A/B 顺序评两次,只有一致才算)。

##### 模式 3: 参考答案对比(Reference-guided)

提供 ground truth reference,让 LLM 判断生成答案与 reference 的语义一致性。

```python
prompt = f"""
判断以下答案是否与参考答案语义一致(允许表述不同,核心事实一致即可)。

问题: {query}
参考答案: {reference}
待评答案: {candidate}

输出 JSON: {{"consistent": true/false, "reason": "..."}}
"""
```

**优点**:更客观,适合有标准答案的 QA 任务。
**缺点**:需要 ground truth,成本高。

#### LLM-as-Judge 的常见陷阱

| 陷阱 | 表现 | 缓解策略 |
|------|------|---------|
| **位置偏差** | 成对比较中倾向选第一个 | 交换顺序评两次,不一致视为平局 |
| **冗长偏差(Verbosity Bias)** | 倾向给更长的答案高分 | 评分标准中明确"长度不影响评分" |
| **自我偏好(Self-enhancement)** | GPT-4 评分时偏好 GPT 系列生成的内容 | 用与生成器不同厂商的模型做 judge |
| **同质偏好** | 偏好风格相似的内容 | 多 judge 投票(ensemble) |
| **评分不稳定** | 同一输入多次评分不一致 | 设 temperature=0,多次评分取众数 |
| **能力上限** | Judge 模型能力不足时无法识别细微错误 | 用比生成器更强的模型做 judge(GPT-4 评 GPT-3.5) |
| **领域偏差** | 通用 LLM 在专业领域判断不准 | 领域微调 judge 或加入领域 rubric |

#### LLM-as-Judge 的校准(Calibration)

**关键工程实践**:
1. 构建一个**人工标注的黄金集**(golden set, 100-500 条);
2. 用 LLM-judge 评分,计算与人工评分的**相关系数**(Spearman/Kendall);
3. 若相关系数 < 0.7,需要调整 rubric 或更换 judge 模型;
4. 定期用黄金集回归测试 judge 模型版本升级后的稳定性。

```python
from scipy.stats import spearmanr

human_scores = [5, 3, 4, 2, 5, 1, 4, 3]
llm_scores   = [5, 4, 4, 2, 5, 2, 4, 3]

rho, p = spearmanr(human_scores, llm_scores)
print(f"Spearman: {rho:.3f}, p={p:.4f}")
# rho > 0.7 视为 judge 可用
```

**面试加分点**:提到 **Chatbot Arena** 的 Bradley-Terry 模型——通过成对比较的胜负关系拟合 Elo 评分,是业界 LLM 评估的事实标准之一。

</details>

---

### Q5: 如何构建 RAG 评估数据集? 有哪些低成本方案? 请给出分层策略。

<details>
<summary>展开答案</summary>

评估数据集是 RAG 评估的"基础设施",但人工标注成本极高(每条 5-20 元,领域专家更贵)。下面是 4 种构建方法 + 分层低成本策略。

#### 方法 1: 用户查询日志挖掘(最高价值)

**来源**:生产环境的用户真实 query 日志。

**流程**:
1. **采样**:从日志中按业务场景分层采样(不要只取热门 query,冷启动 query 更有价值);
2. **去敏**:脱敏处理(用户 PII);
3. **聚类去重**:用 embedding 聚类,每类取代表 query,避免重复;
4. **人工标注**:为每个 query 标注标准答案 + 相关文档;
5. **难度分级**:简单(事实型)/ 中等(推理型)/ 困难(多跳/模糊)。

**优点**:分布真实,直接反映线上问题。
**缺点**:隐私合规问题,冷启动场景覆盖不足。

#### 方法 2: LLM 合成生成(Synthetic Data)

**核心思路**:用强模型(GPT-4)从知识库文档反向生成 query。

```python
prompt = f"""
基于以下文档,生成 3 个用户可能提出的问题。
要求:
1. 答案必须能从文档中找到
2. 问题风格多样:事实型/推理型/对比型
3. 避免直接复制文档原文

文档: {document}

输出 JSON: [{{"question": "...", "answer": "...", "difficulty": "easy/medium/hard"}}]
"""
```

**进化策略(Evolution)**:参考 Evol-Instruct,对简单 query 做以下变换增加难度:
- **加约束**:增加条件("在 2023 年的数据中...")
- **多跳**:要求结合多个文档("对比 A 和 B 在 X 方面的差异")
- **深层推理**:增加推理链("为什么...?请解释原因")
- **模糊化**:用代词/省略("它的价格是多少?"——需要上下文消解)

**优点**:可批量、低成本、覆盖广。
**缺点**:
- **分布偏差**:LLM 生成的问题比真实用户问题更"标准",线上分布不匹配;
- **答案可能错**:LLM 生成的"标准答案"本身可能有错,需人工抽检。

#### 方法 3: 数据增强(Data Augmentation)

对已有 query 做扰动,生成变体,测试鲁棒性。

| 扰动类型 | 示例 | 测试目标 |
|---------|------|---------|
| 同义改写 | "GPT-4 何时发布" → "GPT-4 是哪天推出的" | 检索鲁棒性 |
| 口语化 | "GPT-4 啥时候发的" | query 理解 |
| 拼写错误 | "GPT4 何时发部" | 容错性 |
| 多语言混合 | "GPT-4 何时 release" | 多语言支持 |
| 增加噪声 | "嗯我想问下,GPT-4 是什么时候发布的呀" | 鲁棒性 |
| 实体替换 | "GPT-5 何时发布"(假设文档没有) | 拒答能力 |

**优点**:低成本扩展,专测边界。
**缺点**:扰动可能改变语义,需人工校验。

#### 方法 4: 人工标注规范设计

**标注规范要点**:
1. **明确标注对象**:相关文档是"完全相关"还是"部分相关"?用 0/1/2 三级;
2. **多标注者一致性**:每条至少 2 人标注,计算 Cohen's Kappa,< 0.6 需要修订规范;
3. **难度标签**:同时标注难度,便于分层评估;
4. **错误类型标签**:幻觉/跑题/拒答/部分正确,便于归因。

#### 分层低成本策略(面试重点)

针对不同阶段,用不同成本的数据组合:

```
┌─────────────────────────────────────────────────────────┐
│ 阶段 1: 研发期 (0 成本)                                  │
│ - 100% LLM 合成                                          │
│ - 目标: 快速迭代,发现明显问题                            │
│ - 风险: 分布偏差,可能过拟合 LLM 生成的"标准问题"         │
├─────────────────────────────────────────────────────────┤
│ 阶段 2: 上线前 (中等成本)                                │
│ - 70% LLM 合成 + 30% 真实日志采样(人工标注)             │
│ - 加入 100 条黄金集(专家标注)校准 LLM-judge             │
│ - 目标: 上线前回归测试                                   │
├─────────────────────────────────────────────────────────┤
│ 阶段 3: 线上 (持续低成本)                                │
│ - 5% 流量 LLM-judge 在线抽检(自动)                      │
│ - 1% 流量用户反馈(点赞/点踩,隐式标注)                   │
│ - 每月 200 条人工抽检(质量护栏)                         │
│ - 目标: 持续监控 + 漂移检测                              │
└─────────────────────────────────────────────────────────┘
```

#### 数据集规模建议

| 用途 | 推荐规模 | 标注成本 |
|------|---------|---------|
| 单元测试(开发自测) | 50-100 条 LLM 合成 | ~0 元 |
| 回归测试(上线前) | 500-1000 条混合 | 5000-20000 元 |
| 线上监控基准 | 200 条人工黄金集 | 2000-4000 元 |
| A/B 测试 | 1000-5000 条线上流量 | 0(用业务指标) |

**面试加分点**:提到 **"评估数据集的版本管理"**——评估集要和知识库版本、模型版本绑定,否则不同时期的指标不可比。这是很多团队踩过的坑。

</details>

---

### Q6: 如何为 RAG 系统设计 A/B 测试? 从假设到显著性检验的完整流程。

<details>
<summary>展开答案</summary>

A/B 测试是 RAG 上线决策的最终依据。下面是完整流程,以"将 retriever 从 BM25 换为 dense embedding"为例。

#### Step 1: 假设设计

```
H0(零假设): 新方案(dense)与旧方案(BM25)在用户满意度上无显著差异
H1(备择假设): 新方案用户满意度显著高于旧方案

方向性: 单尾(我们只关心新方案是否"更好",不关心是否更差)
```

**陷阱**:假设要在**看到数据前**定好,不能看完数据再反过来编假设(p-hacking)。

#### Step 2: 指标体系设计

##### OEC(Overall Evaluation Criterion)—— 核心决策指标

RAG 系统的 OEC 通常是**用户满意度**的复合指标:

```
OEC = w1 * 答案采纳率(用户点击"有用")
    + w2 * 重写率(1 - 用户重新提问率,重写说明不满意)
    + w3 * (1 - 人工点踩率)
```

权重 `w1, w2, w3` 需根据业务对齐。

##### 护栏指标(Guardrail Metrics)—— 不能变差的指标

- **延迟 P99**:新方案不能比旧方案慢 20% 以上;
- **错误率**:不能上升;
- **成本**:每次调用 token 成本不能超过预算;
- **Faithfulness 离线采样**:不能下降(防止幻觉加剧)。

##### 调试指标(Debugging Metrics)—— 用于归因

- 检索 Recall@5(离线评估集)
- 答案长度分布
- 拒答率

#### Step 3: 样本量计算(功效分析)

**公式**(两比例比较,适用于采纳率这类二元指标):

```
n = (Z_{α/2} + Z_{β})^2 * (p1*(1-p1) + p2*(1-p2)) / (p1 - p2)^2
```

其中:
- `α = 0.05`(显著性水平)→ `Z_{α/2} = 1.96`
- `β = 0.2`(即 power = 0.8)→ `Z_β = 0.84`
- `p1` = 旧方案采纳率(假设 0.60)
- `p2` = 期望新方案采纳率(假设 0.65,即提升 5 个百分点)

```python
import math
from scipy.stats import norm

alpha = 0.05
beta = 0.2
p1, p2 = 0.60, 0.65

z_alpha = norm.ppf(1 - alpha/2)  # 1.96
z_beta = norm.ppf(1 - beta)      # 0.84

n = (z_alpha + z_beta)**2 * (p1*(1-p1) + p2*(1-p2)) / (p2 - p1)**2
print(f"每组样本量: {math.ceil(n)}")
# 每组样本量: ~2800
```

**关键陷阱**:
- **最小可检测效应(MDE)**:如果 p2-p1 设太小(如 1%),样本量会爆炸(几十万),需权衡;
- **流量** = 样本量 / 实验天数,要算每天能不能跑够。

#### Step 4: 分流设计

##### 哈希分流

```python
import hashlib

def assign_group(user_id, experiment_id):
    """基于用户ID哈希分桶,保证同一用户始终在同一组"""
    key = f"{user_id}_{experiment_id}"
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    bucket = h % 100  # 0-99
    return "treatment" if bucket < 50 else "control"
```

**关键点**:
- 用 `user_id + experiment_id` 联合哈希,避免不同实验流量相关;
- **分层正交实验**:不同实验用不同 hash slot,允许多实验并行(参考字节 Overlap 系统);
- 检查分流是否均匀(`Chi-square test` 检验组间用户特征均衡)。

##### 辛普森悖论(Simpson's Paradox)防范

如果新方案在整体看更好,但在每个子群体(iOS/Android、新用户/老用户)都更差,说明分流有混淆。**必须按关键维度分层检查**。

#### Step 5: 显著性检验

##### 连续指标(如 OEC 评分)

```python
from scipy.stats import ttest_ind

control = [4.1, 3.8, 4.2, ...]
treatment = [4.3, 4.0, 4.5, ...]

t_stat, p_value = ttest_ind(treatment, control, alternative='greater')
print(f"t={t_stat:.3f}, p={p_value:.4f}")

if p_value < 0.05:
    print("拒绝 H0,新方案显著更优")
```

##### 比例指标(如采纳率)

```python
from scipy.stats import norm

def two_proportion_z_test(x1, n1, x2, n2):
    """x1/n1 = 对照组采纳数/总数, x2/n2 = 实验组"""
    p_pool = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    z = (x2/n2 - x1/n1) / se
    p = 1 - norm.cdf(z)  # 单尾
    return z, p

# 对照组: 1680/2800 采纳, 实验组: 1820/2800
z, p = two_proportion_z_test(1680, 2800, 1820, 2800)
print(f"z={z:.3f}, p={p:.4f}")
```

##### 多重比较校正(Bonferroni)

如果同时检验 K 个指标,整体 FWER 会膨胀。用 Bonferroni 校正:`α' = α / K`。

```python
alpha = 0.05
n_metrics = 5  # 同时看 5 个指标
adjusted_alpha = alpha / n_metrics  # 0.01
# 每个指标的 p 值要 < 0.01 才算显著
```

**注意**:OEC 通常作为单一决策指标,不需要校正;护栏指标若多个则需校正。

#### Step 6: 决策框架

```
┌─────────────────────────────────────────────────────────────┐
│ 决策矩阵                                                      │
├──────────────┬──────────────────────────────────────────────┤
│ OEC 显著提升  │ 护栏指标无显著恶化 → 全量上线                │
│              │ 护栏指标显著恶化    → 不上线,分析权衡        │
├──────────────┼──────────────────────────────────────────────┤
│ OEC 无显著差异│ 护栏指标有改善      → 视业务优先级决定        │
│              │ 护栏指标无变化      │ 延长实验 或 不上线       │
├──────────────┼──────────────────────────────────────────────┤
│ OEC 显著下降  │ 不上线(无论护栏如何)                       │
└──────────────┴──────────────────────────────────────────────┘
```

#### RAG A/B 测试的特殊坑

1. **学习效应(Novelty Effect)**:新方案初期用户不熟悉,指标先差后好,需观察 1-2 周;
2. **延迟反馈**:用户可能当天没反馈,第二天才点踩,需考虑归因窗口;
3. **冷热知识库差异**:新 embedding 在某些领域更好,某些更差,需按领域分桶;
4. **样本污染**:同一用户多次提问,样本不独立,需以 user 为单位聚类分析。

**面试加分点**:提到 **CUPED(Controlled-experiment Using Pre-Experiment Data)**——用实验前的协变量降低方差,可减少 30-50% 样本量,是业界 A/B 测试标配。

</details>

---

### Q7: 设计 RAG 系统的持续监控体系,需要哪几层指标? 各包含哪些核心项?

<details>
<summary>展开答案</summary>

监控体系是 RAG 上线后的"心电图"。设计原则:**分层、可归因、有告警阈值**。

#### 三层监控体系

```
┌─────────────────────────────────────────────────────────────┐
│ L3 质量指标 (Quality) ── 最重要也最贵                        │
│   Faithfulness 离线采样 / LLM-judge 在线抽检 / 人工抽检      │
│   频率: 每日 / 每周                                          │
├─────────────────────────────────────────────────────────────┤
│ L2 业务指标 (Business) ── 反映用户真实感受                   │
│   满意度 / 采纳率 / 重写率 / 拒答率 / 会话深度              │
│   频率: 实时                                                 │
├─────────────────────────────────────────────────────────────┤
│ L1 系统指标 (System) ── 最基础,运维视角                     │
│   延迟 P50/P99 / QPS / 错误率 / Token 成本 / 检索耗时       │
│   频率: 秒级                                                 │
└─────────────────────────────────────────────────────────────┘
```

#### L1 系统指标(基础运维)

| 指标 | 含义 | 告警阈值(示例) |
|------|------|----------------|
| **P50/P99 延迟** | 50%/99% 请求的响应时间 | P99 > 5s 告警 |
| **QPS** | 每秒查询数 | 突增/突降 50% 告警 |
| **错误率** | HTTP 5xx + LLM API 失败 | > 1% 告警 |
| **检索耗时** | Retriever 阶段耗时 | P99 > 2s 告警 |
| **生成耗时** | Generator 阶段耗时 | P99 > 8s 告警 |
| **Token 成本** | 每次请求 token 消耗 | 日成本超预算 20% 告警 |
| **向量库健康** | 索引大小、内存占用 | 内存 > 90% 告警 |

**实现**:Prometheus + Grafana,标准 SRE 实践。

#### L2 业务指标(用户感受)

| 指标 | 含义 | 采集方式 |
|------|------|---------|
| **答案采纳率** | 用户点击"有用"/复制答案的比例 | 前端埋点 |
| **重写率** | 用户在同一会话中重新提问的比例(降序) | 会话日志 |
| **点踩率** | 用户点踩的比例 | 前端埋点 |
| **拒答率** | 系统回答"我不知道"的比例 | LLM 输出分类 |
| **会话深度** | 平均每个会话的轮数 | 会话日志 |
| **首次满意率** | 单轮即满意的比例 | 会话日志 |
| **人工介入率** | 转人工的比例(客服场景) | 工单系统 |

**关键洞察**:
- **重写率** 是最强负向信号——用户重写说明答案不满意;
- **会话深度增加 + 满意度未提升** = 系统在浪费用户时间;
- 按业务维度(用户类型/查询类型)分桶看,避免被均值掩盖问题。

#### L3 质量指标(RAG 特有,最贵)

| 指标 | 采集方式 | 频率 | 成本 |
|------|---------|------|------|
| **Faithfulness 在线抽检** | 5% 流量用 LLM-judge 打分 | 每日 | 中 |
| **Answer Relevancy 在线抽检** | 同上 | 每日 | 中 |
| **人工质检** | 抽 200 条专家评分 | 每周 | 高 |
| **知识库漂移检测** | 监控 query 分布与知识库覆盖 | 每周 | 中 |
| **幻觉率** | Faithfulness 低分样本人工复核 | 每日 | 高 |
| **拒答合理性** | 拒答样本中"本应能答"的比例 | 每周 | 高 |

##### 在线 LLM-judge 抽检实现

```python
import random
from datetime import datetime

async def online_quality_check(query, context, answer):
    """5% 流量抽检,异步执行不影响主链路"""
    if random.random() > 0.05:
        return  # 不抽检

    # 异步调用 LLM-judge
    score = await llm_judge_faithfulness(query, context, answer)

    # 上报到监控
    metrics.record("faithfulness_score", score, tags={
        "date": datetime.now().strftime("%Y-%m-%d"),
        "domain": classify_domain(query),
    })

    # 低分告警
    if score < 0.6:
        alert.send(f"Faithfulness 低分: {score}, query: {query[:50]}")
```

#### 监控告警分级

```
P0(立即响应,15分钟内):
- 错误率 > 5%
- P99 延迟 > 10s
- 完全无流量(可能服务挂了)

P1(1小时内):
- Faithfulness 日均下降 > 10%
- 采纳率下降 > 5%
- 拒答率上升 > 10%

P2(1个工作日):
- 单一业务线指标异常
- 成本超预算 10%
- 知识库覆盖率下降
```

#### 漂移检测(Data Drift)

RAG 系统的隐藏风险:**用户 query 分布漂移**——新话题出现,知识库没覆盖,Faithfulness 看起来还行(因为 LLM 编造了看似合理的答案)但实际是幻觉。

**检测方法**:
1. 每周对 query embedding 聚类,与上周对比,新增簇可能是新话题;
2. 监控 query 中 OOV(知识库未覆盖)实体的比例;
3. 监控 top-10 检索结果的相关度均值,持续下降说明知识库没跟上。

```python
from sklearn.cluster import HDBSCAN
import numpy as np

def detect_query_drift(this_week_queries, last_week_centroids):
    """检测本周 query 是否有新话题簇"""
    embeddings = embed(this_week_queries)
    clusterer = HDBSCAN(min_cluster_size=5)
    labels = clusterer.fit_predict(embeddings)

    # 找出与上周所有中心距离都很远的新簇
    new_topics = []
    for cluster_id in set(labels):
        if cluster_id == -1:
            continue
        cluster_emb = embeddings[labels == cluster_id]
        centroid = cluster_emb.mean(axis=0)

        # 与上周所有中心的最大相似度
        max_sim = max(
            cosine_sim(centroid, old_c)
            for old_c in last_week_centroids
        )
        if max_sim < 0.7:  # 阈值
            new_topics.append(cluster_id)

    return new_topics
```

**面试加分点**:提到 **"评估指标的指标"**——监控评估系统本身是否健康。例如:LLM-judge 的评分分布是否突然偏移?人工标注的 Kappa 是否下降?这是元监控(Meta-monitoring),很多团队忽略。

</details>

---

### Q8: 假设你负责的 RAG 系统 Faithfulness 指标在 24 小时内从 0.85 突然下降到 0.55, 请给出完整的排查 SOP(止血 → 根因 → 修复 → 复盘)。

<details>
<summary>展开答案</summary>

这是资深岗高频场景题,考察**故障排查思维**和**RAG 工程经验**。Faithfulness 突降说明系统在大量"编造"上下文中没有的内容。

#### Phase 1: 止血(0-30 分钟)—— 优先恢复服务

##### Step 1.1: 确认指标真实,排除监控故障

```bash
# 1. 检查 LLM-judge 模型是否正常(模型升级会改变评分倾向)
curl -X POST $LLM_JUDGE_ENDPOINT/health
# 2. 用黄金集(golden set)回归测试 judge
python eval_judge_on_golden.py
# 如果 golden set 评分也突降 → judge 故障,不是业务问题
```

##### Step 1.2: 确认影响范围

```sql
-- 按维度拆分,定位是全局问题还是局部
SELECT
    domain,
    DATE(ts) as date,
    AVG(faithfulness) as avg_f,
    COUNT(*) as n
FROM eval_records
WHERE ts > NOW() - INTERVAL 2 DAY
GROUP BY domain, DATE(ts);
```

可能的发现:
- **所有 domain 都降** → 全局问题(模型/embedding/知识库);
- **特定 domain 降** → 该 domain 知识库问题;
- **特定时间段降** → 可能是某次发布引入。

##### Step 1.3: 紧急回滚(如确认是发布导致)

```bash
# 查看最近 24h 的发布记录
git log --since="24 hours ago" --oneline
# 查看模型版本是否变更
kubectl get deployment rag-generator -o yaml | grep image
# 如果是模型升级导致 → 回滚到上一版本
kubectl rollout undo deployment/rag-generator
```

##### Step 1.4: 临时降级保护(若无法快速回滚)

```python
# 临时加强 prompt 约束,降低幻觉(虽然可能增加拒答率)
EMERGENCY_PROMPT = """
你必须严格基于以下上下文回答。如果上下文中没有相关信息,
必须回答"我没有找到相关信息",绝对不要编造。

上下文: {context}
问题: {query}
"""
```

#### Phase 2: 根因分析(30 分钟 - 2 小时)

##### 排查清单(按 RAG 链路顺序)

```
Query 理解 → Retriever → Reranker → Context 组装 → Generator → 输出
   ↑             ↑          ↑            ↑              ↑
  改写了?      召回变了?   排序变了?   截断方式变了?  模型升级?
```

##### Step 2.1: 检查知识库是否被污染

```python
# 检查最近 24h 知识库是否有大批量更新
recent_updates = kb_client.query(
    filter={"update_time": "> 2026-09-22 00:00"},
    fields=["doc_id", "content", "source"]
)
print(f"最近更新 {len(recent_updates)} 条")

# 抽查更新内容质量
for doc in recent_updates[:10]:
    print(doc["content"][:200])
# 可能发现: 新入库的文档内容残缺/编码错误/HTML 标签未清洗
```

**常见根因 1**: 知识库 ETL 流程故障,入库的文档是乱码或截断的,LLM 看到垃圾上下文只能编造。

##### Step 2.2: 检查 Embedding 模型是否变更

```bash
# 检查 embedding 服务版本
curl $EMBEDDING_SERVICE/version
# 对比同一文档的 embedding 是否变化
python -c "
from embedding import embed
v1 = embed('测试文本')  # 当前
# 与昨日存储的 embedding 对比
import numpy as np
print(np.linalg.norm(v1 - v_yesterday))
"
```

**常见根因 2**: Embedding 模型升级但**没有重建索引**,导致检索结果与文档语义不匹配,召回了无关文档。

##### Step 2.3: 检查 Generator 模型是否升级

```bash
# 检查 LLM 服务是否更新
kubectl get deployment llm-server -o yaml | grep image
# 查看模型版本日志
grep "model_version" /var/log/rag/generator.log | tail -20
```

**常见根因 3**: 生成模型版本升级,新版本"更聪明"但也"更爱发挥",在上下文不足时倾向于补充常识(幻觉)。

##### Step 2.4: 检查 Context 组装逻辑

```python
# 抓取最近 Faithfulness 低分的样本
low_score_samples = db.query(
    "SELECT * FROM eval_records WHERE faithfulness < 0.5 ORDER BY ts DESC LIMIT 20"
)

for s in low_score_samples:
    print(f"Query: {s['query']}")
    print(f"Context length: {len(s['context'])}")
    print(f"Context preview: {s['context'][:300]}")
    print(f"Answer: {s['answer']}")
    print("---")
# 可能发现: context 为空 / context 被截断 / context 是错的文档
```

**常见根因 4**: Context window 策略调整(如从 top-5 改成 top-3),或 truncation 策略变化导致上下文不完整。

##### Step 2.5: 检查 Query Rewriting

```python
# 检查 query rewriting 是否引入异常
recent_queries = db.query("SELECT original, rewritten FROM query_log WHERE ts > ...")
for q in recent_queries:
    if "删除" in q["rewritten"] or q["rewritten"] == "":
        print(f"异常重写: {q}")
```

**常见根因 5**: Query rewriting 模块故障,把用户 query 改写成了无意义内容,导致检索召回错误文档。

##### Step 2.6: 双盲对比实验

```python
# 用同一批 query,分别跑"当前版本"和"昨日快照",对比
queries = load_fixed_test_set()
results_current = run_rag(queries, version="current")
results_yesterday = run_rag(queries, version="yesterday_snapshot")

# 对比检索结果差异
for q, r_c, r_y in zip(queries, results_current, results_yesterday):
    if r_c["contexts"] != r_y["contexts"]:
        print(f"检索结果变化: {q}")
        print(f"  昨日: {r_y['contexts'][:2]}")
        print(f"  今日: {r_c['contexts'][:2]}")
```

#### Phase 3: 修复(2-4 小时)

根据根因对应修复:

| 根因 | 修复方案 |
|------|---------|
| 知识库污染 | 清洗 ETL 流程,回滚错误文档,加数据质量校验 |
| Embedding 变更 | 全量重建索引,或回滚 embedding 版本 |
| Generator 升级 | 回滚模型,或调整 prompt 加强约束 |
| Context 截断 | 修复 truncation 策略,恢复 top-k |
| Query 重写故障 | 临时关闭 rewriting,排查重写模型 |

#### Phase 4: 复盘(1-2 个工作日)

##### 复盘报告模板

```markdown
# Faithfulness 突降故障复盘 (2026-09-23)

## 1. 故障概述
- 时间: 2026-09-22 14:00 - 2026-09-23 10:00
- 影响: 12% 用户受影响,约 X 次查询
- 严重度: P1

## 2. 时间线
- 14:00 监控告警 Faithfulness 下降
- 14:15 确认非 judge 故障
- 14:30 紧急回滚 generator 模型
- 15:00 指标恢复
- 16:00 根因定位: 模型升级未评估 Faithfulness

## 3. 根因
新模型版本在 context 不足时倾向"常识补全",评估时未覆盖此场景。

## 4. 改进措施
- [ ] 模型升级必须经过离线评估集回归(含 context 不足场景)
- [ ] 增加监控: 按 context 长度分桶看 Faithfulness
- [ ] 灰度发布: 模型升级先 5% 灰度 24h
- [ ] 告警优化: Faithfulness 下降 > 5% 立即告警(原阈值 10%)
```

#### 预防性改进

1. **发布卡口**: 任何模型/embedding/知识库变更,必须通过离线评估集回归(Faithfulness 下降 > 3% 阻断发布);
2. **灰度发布**: 5% → 25% → 50% → 100%,每阶段观察 24h;
3. **监控细化**: 按维度(domain/context 长度/用户类型)分桶监控,避免均值掩盖;
4. **混沌演练**: 每月模拟一类故障(知识库污染/模型故障),验证 SOP 有效性。

**面试加分点**:提到 **"故障预算(Error Budget)"**——SLO 设定 99.9% 可用,每月故障预算 = 0.1% * 43200 分钟 = 43 分钟,超过则停止发布新功能,优先稳定性。这体现 SRE 思维。

</details>

---

### Q9: 手撕代码 — 实现一个完整的 RAG 评估系统,包含检索指标计算、LLM-as-Judge 生成评估、诊断分析报告。Python 完整可运行实现。

<details>
<summary>展开答案</summary>

下面是一个完整可运行的 RAG 评估系统实现,约 400 行,涵盖:
1. 检索指标(Recall@K、MRR、NDCG@K、Hit@K)
2. RAGAS 风格的 Faithfulness / Answer Relevancy 计算
3. LLM-as-Judge(单评分 + 成对比较 + 位置偏差消除)
4. 诊断分析(分层统计 + 异常归因)

```python
"""
RAG 评估系统 - 完整实现
依赖: pip install numpy scikit-learn openai pydantic
"""
import json
import math
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import numpy as np
from openai import OpenAI


# ============================================================
# Part 1: 数据结构定义
# ============================================================

@dataclass
class RetrievalResult:
    """单次检索结果"""
    query_id: str
    query: str
    retrieved_doc_ids: List[str]          # 按相关度排序的文档ID
    relevant_doc_ids: List[str]           # 真正相关的文档ID(标注)
    relevance_scores: Optional[List[int]] = None  # 分级相关度(可选)


@dataclass
class GenerationResult:
    """单次生成结果"""
    query_id: str
    query: str
    context: List[str]                    # 检索到的上下文(文档内容)
    answer: str                           # 生成的答案
    ground_truth: Optional[str] = None    # 标准答案(可选)


@dataclass
class EvalReport:
    """评估报告"""
    retrieval_metrics: Dict[str, float] = field(default_factory=dict)
    generation_metrics: Dict[str, float] = field(default_factory=dict)
    per_query_detail: List[Dict] = field(default_factory=list)
    diagnosis: Dict[str, str] = field(default_factory=dict)


# ============================================================
# Part 2: 检索指标计算
# ============================================================

class RetrievalMetrics:
    """检索质量指标计算器"""

    @staticmethod
    def hit_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Hit@K: top-K 中是否至少命中一个相关文档"""
        top_k = retrieved[:k]
        return 1.0 if any(d in relevant for d in top_k) else 0.0

    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Recall@K: top-K 中命中的相关文档数 / 所有相关文档数"""
        if not relevant:
            return 0.0
        top_k = retrieved[:k]
        hits = sum(1 for d in top_k if d in relevant)
        return hits / len(relevant)

    @staticmethod
    def mrr(retrieved: List[str], relevant: List[str]) -> float:
        """MRR: 第一个相关文档的倒数排名"""
        for i, doc in enumerate(retrieved, 1):
            if doc in relevant:
                return 1.0 / i
        return 0.0

    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevant: List[str],
                  relevance_scores: Optional[Dict[str, int]] = None,
                  k: int = 10) -> float:
        """
        NDCG@K: 归一化折扣累积增益
        relevance_scores: 文档ID -> 分级相关度(如 0/1/2/3),若为 None 则用二值
        """
        def dcg(rels: List[float]) -> float:
            return sum(r / math.log2(i + 2) for i, r in enumerate(rels))

        # 实际 DCG
        top_k = retrieved[:k]
        if relevance_scores:
            gains = [relevance_scores.get(d, 0) for d in top_k]
        else:
            gains = [1.0 if d in relevant else 0.0 for d in top_k]
        dcg_val = dcg(gains)

        # 理想 DCG
        if relevance_scores:
            ideal_gains = sorted(
                [relevance_scores.get(d, 0) for d in relevant],
                reverse=True
            )[:k]
        else:
            ideal_gains = [1.0] * min(len(relevant), k)
        idcg_val = dcg(ideal_gains)

        return dcg_val / idcg_val if idcg_val > 0 else 0.0

    @classmethod
    def evaluate(cls, results: List[RetrievalResult], k_values: List[int] = [1, 3, 5, 10]) -> Dict[str, float]:
        """批量计算所有检索指标"""
        metrics = defaultdict(list)

        for r in results:
            rel_scores = None
            if r.relevance_scores:
                rel_scores = dict(zip(r.retrieved_doc_ids, r.relevance_scores))

            metrics["MRR"].append(cls.mrr(r.retrieved_doc_ids, r.relevant_doc_ids))

            for k in k_values:
                metrics[f"Hit@{k}"].append(
                    cls.hit_at_k(r.retrieved_doc_ids, r.relevant_doc_ids, k)
                )
                metrics[f"Recall@{k}"].append(
                    cls.recall_at_k(r.retrieved_doc_ids, r.relevant_doc_ids, k)
                )
                metrics[f"NDCG@{k}"].append(
                    cls.ndcg_at_k(r.retrieved_doc_ids, r.relevant_doc_ids,
                                  rel_scores, k)
                )

        return {k: float(np.mean(v)) for k, v in metrics.items()}


# ============================================================
# Part 3: LLM-as-Judge 生成评估
# ============================================================

class LLMJudge:
    """LLM-as-Judge 实现,支持单评分和成对比较"""

    def __init__(self, model: str = "gpt-4o", api_key: str = None):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def _call(self, prompt: str, temperature: float = 0.0) -> str:
        """调用 LLM,temperature=0 保证可复现"""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content

    def score_faithfulness(self, query: str, context: List[str], answer: str) -> Dict:
        """
        Faithfulness 评估: 答案是否忠于上下文
        返回 {"score": 0-1, "statements": [...], "reason": "..."}
        """
        prompt = f"""你是严格的 RAG 评估员。请评估答案的忠实度(Faithfulness)。

步骤:
1. 将答案拆解为原子陈述(atomic statements)
2. 判断每个陈述是否能从上下文中找到支持
3. 计算 faithfulness = 支持的陈述数 / 总陈述数

问题: {query}
上下文: {json.dumps(context, ensure_ascii=False)}
答案: {answer}

输出 JSON:
{{
  "statements": [
    {{"text": "陈述内容", "supported": true/false, "reason": "为何支持/不支持"}}
  ],
  "score": 0.0-1.0,
  "reason": "总体说明"
}}"""
        try:
            result = json.loads(self._call(prompt))
            return result
        except Exception as e:
            return {"score": -1, "error": str(e)}

    def score_answer_relevancy(self, query: str, answer: str) -> Dict:
        """
        Answer Relevancy 评估: 答案是否回应了问题
        使用反向生成法: 根据答案生成问题,计算与原问题的相似度
        """
        # 步骤1: 反向生成问题
        gen_prompt = f"""基于以下答案,生成 3 个可能的问题。要求问题风格多样。

答案: {answer}

输出 JSON: {{"questions": ["问题1", "问题2", "问题3"]}}"""

        try:
            gen_result = json.loads(self._call(gen_prompt, temperature=0.3))
            gen_questions = gen_result.get("questions", [])
        except Exception:
            gen_questions = []

        if not gen_questions:
            return {"score": 0.0, "reason": "反向生成失败"}

        # 步骤2: 计算 embedding 相似度
        from sklearn.metrics.pairwise import cosine_similarity

        all_texts = [query] + gen_questions
        embeddings = self._embed(all_texts)
        query_emb = embeddings[0:1]
        gen_embs = embeddings[1:]

        sims = cosine_similarity(query_emb, gen_embs)[0]
        avg_sim = float(np.mean(sims))

        return {
            "score": avg_sim,
            "gen_questions": gen_questions,
            "similarities": sims.tolist()
        }

    def _embed(self, texts: List[str]) -> np.ndarray:
        """调用 embedding API"""
        resp = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return np.array([d.embedding for d in resp.data])

    def pairwise_compare(self, query: str, context: List[str],
                         answer_a: str, answer_b: str) -> Dict:
        """
        成对比较: 哪个答案更好
        消除位置偏差: 交换 A/B 顺序评两次,不一致则为平局
        """
        def _judge(first, second, first_label, second_label):
            prompt = f"""比较以下两个答案哪个更好。

问题: {query}
上下文: {json.dumps(context, ensure_ascii=False)}

答案 {first_label}: {first}
答案 {second_label}: {second}

评分维度:
1. 忠于上下文(无幻觉)
2. 回应了问题
3. 表述清晰

输出 JSON: {{"winner": "{first_label}"/"{second_label}"/"tie", "reason": "..."}}"""
            return json.loads(self._call(prompt))

        # 第一次: A 在前
        r1 = _judge(answer_a, answer_b, "A", "B")
        # 第二次: B 在前
        r2 = _judge(answer_b, answer_a, "B", "A")

        # 一致性判断
        w1 = r1.get("winner")
        w2 = r2.get("winner")

        # 归一化: r2 中 winner 是相对 "B在前" 的, 需要翻转
        w2_normalized = {"A": "B", "B": "A", "tie": "tie"}.get(w2, "tie")

        if w1 == w2_normalized:
            final = w1
        else:
            final = "tie"  # 不一致视为平局

        return {
            "winner": final,
            "r1": r1,
            "r2": r2,
            "consistent": w1 == w2_normalized
        }


# ============================================================
# Part 4: 评估器(整合检索 + 生成评估)
# ============================================================

class RAGEvaluator:
    """RAG 评估系统主类"""

    def __init__(self, judge_model: str = "gpt-4o", api_key: str = None):
        self.retrieval_metrics = RetrievalMetrics()
        self.judge = LLMJudge(model=judge_model, api_key=api_key)

    def evaluate(self,
                 retrieval_results: List[RetrievalResult],
                 generation_results: List[GenerationResult],
                 k_values: List[int] = [1, 3, 5]) -> EvalReport:
        """完整评估流程"""
        report = EvalReport()

        # Part A: 检索指标
        report.retrieval_metrics = self.retrieval_metrics.evaluate(
            retrieval_results, k_values
        )

        # Part B: 生成指标
        faithfulness_scores = []
        relevancy_scores = []
        per_query = []

        for gen in generation_results:
            f_result = self.judge.score_faithfulness(
                gen.query, gen.context, gen.answer
            )
            r_result = self.judge.score_answer_relevancy(
                gen.query, gen.answer
            )

            f_score = f_result.get("score", 0)
            r_score = r_result.get("score", 0)

            faithfulness_scores.append(f_score)
            relevancy_scores.append(r_score)

            per_query.append({
                "query_id": gen.query_id,
                "query": gen.query,
                "faithfulness": f_score,
                "answer_relevancy": r_score,
                "answer": gen.answer[:100],
                "context_count": len(gen.context),
                "f_detail": f_result,
                "r_detail": r_result,
            })

        report.generation_metrics = {
            "faithfulness_mean": float(np.mean(faithfulness_scores)),
            "faithfulness_std": float(np.std(faithfulness_scores)),
            "answer_relevancy_mean": float(np.mean(relevancy_scores)),
            "answer_relevancy_std": float(np.std(relevancy_scores)),
            "faithfulness_below_05_ratio": float(
                np.mean([1 if s < 0.5 else 0 for s in faithfulness_scores])
            ),  # 低分样本占比
        }

        report.per_query_detail = per_query

        # Part C: 诊断分析
        report.diagnosis = self._diagnose(report)

        return report

    def _diagnose(self, report: EvalReport) -> Dict[str, str]:
        """基于指标自动诊断问题归因"""
        diag = {}

        f_mean = report.generation_metrics.get("faithfulness_mean", 0)
        r_mean = report.generation_metrics.get("answer_relevancy_mean", 0)
        recall_5 = report.retrieval_metrics.get("Recall@5", 0)
        ndcg_5 = report.retrieval_metrics.get("NDCG@5", 0)

        # 检索层诊断
        if recall_5 < 0.6:
            diag["retrieval"] = (
                f"Recall@5={recall_5:.2f} 偏低,检索召回不全。"
                "建议: 扩大 top-k / 优化 chunk 策略 / 加入 query rewriting / 检查 embedding 模型"
            )
        elif ndcg_5 < 0.5:
            diag["retrieval"] = (
                f"NDCG@5={ndcg_5:.2f} 偏低但 Recall 可接受,排序质量差。"
                "建议: 引入 reranker / 调整 scoring 策略"
            )
        else:
            diag["retrieval"] = "检索层指标正常"

        # 生成层诊断
        if f_mean < 0.6 and recall_5 >= 0.6:
            diag["generation"] = (
                f"Faithfulness={f_mean:.2f} 偏低但检索召回正常,生成器在编造内容。"
                "建议: 加强 prompt 约束(仅基于上下文) / 换更服从的模型 / 检查 context 截断"
            )
        elif r_mean < 0.6:
            diag["generation"] = (
                f"Answer Relevancy={r_mean:.2f} 偏低,答案跑题。"
                "建议: 优化 prompt / 检查 query 理解环节 / 加入 query classification"
            )
        else:
            diag["generation"] = "生成层指标正常"

        # 低分样本聚类(简化版)
        low_f_count = sum(
            1 for q in report.per_query_detail
            if q["faithfulness"] < 0.5
        )
        if low_f_count > len(report.per_query_detail) * 0.2:
            diag["warning"] = (
                f"低 Faithfulness 样本占比 {low_f_count}/{len(report.per_query_detail)} "
                f"超过 20%,可能存在系统性问题,建议人工 review 低分样本"
            )

        return diag


# ============================================================
# Part 5: 演示运行
# ============================================================

def demo():
    """演示评估系统运行"""

    # 构造测试数据
    retrieval_data = [
        RetrievalResult(
            query_id="q1",
            query="GPT-4 何时发布?",
            retrieved_doc_ids=["d2", "d1", "d5", "d3", "d4"],  # d1, d3 相关
            relevant_doc_ids=["d1", "d3", "d7"],
        ),
        RetrievalResult(
            query_id="q2",
            query="Transformer 的核心机制是什么?",
            retrieved_doc_ids=["d10", "d11", "d12"],  # d10, d11 相关
            relevant_doc_ids=["d10", "d11"],
        ),
    ]

    generation_data = [
        GenerationResult(
            query_id="q1",
            query="GPT-4 何时发布?",
            context=[
                "GPT-4 于 2023 年 3 月 14 日由 OpenAI 发布,支持多模态输入。",
            ],
            answer="GPT-4 于 2023 年 3 月发布,由 OpenAI 开发,支持多模态。",
            ground_truth="GPT-4 于 2023 年 3 月 14 日发布。"
        ),
        GenerationResult(
            query_id="q2",
            query="Transformer 的核心机制是什么?",
            context=[
                "Transformer 的核心是自注意力机制(Self-Attention),"
                "允许模型在处理每个位置时关注序列中的所有其他位置。"
            ],
            answer="Transformer 的核心机制是自注意力(Self-Attention),"
                   "它由 Google 在 2017 年提出。",  # "Google 2017" 是幻觉
            ground_truth="自注意力机制。"
        ),
    ]

    # 初始化评估器(需要 OPENAI_API_KEY 环境变量)
    import os
    evaluator = RAGEvaluator(
        judge_model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # 执行评估
    print("=" * 60)
    print("开始 RAG 评估")
    print("=" * 60)

    report = evaluator.evaluate(retrieval_data, generation_data)

    # 打印报告
    print("\n【检索指标】")
    for k, v in report.retrieval_metrics.items():
        print(f"  {k}: {v:.4f}")

    print("\n【生成指标】")
    for k, v in report.generation_metrics.items():
        print(f"  {k}: {v:.4f}")

    print("\n【诊断分析】")
    for category, text in report.diagnosis.items():
        print(f"  [{category}] {text}")

    print("\n【逐条详情】")
    for q in report.per_query_detail:
        print(f"\n  Q{q['query_id']}: {q['query']}")
        print(f"    Faithfulness: {q['faithfulness']:.2f}")
        print(f"    Relevancy: {q['answer_relevancy']:.2f}")
        print(f"    Answer: {q['answer']}")

    # 导出完整报告
    with open("rag_eval_report.json", "w", encoding="utf-8") as f:
        json.dump({
            "retrieval_metrics": report.retrieval_metrics,
            "generation_metrics": report.generation_metrics,
            "diagnosis": report.diagnosis,
            "per_query_detail": report.per_query_detail,
        }, f, ensure_ascii=False, indent=2)
    print("\n完整报告已保存到 rag_eval_report.json")


if __name__ == "__main__":
    # 手算验证检索指标
    print("【手算验证】")
    print("场景: retrieved=[d2,d1,d5,d3,d4], relevant=[d1,d3,d7]")
    rm = RetrievalMetrics()
    print(f"  Hit@5: {rm.hit_at_k(['d2','d1','d5','d3','d4'], ['d1','d3','d7'], 5)}")  # 1.0
    print(f"  Recall@5: {rm.recall_at_k(['d2','d1','d5','d3','d4'], ['d1','d3','d7'], 5)}")  # 0.667
    print(f"  MRR: {rm.mrr(['d2','d1','d5','d3','d4'], ['d1','d3','d7'])}")  # 0.5
    print(f"  NDCG@5: {rm.ndcg_at_k(['d2','d1','d5','d3','d4'], ['d1','d3','d7'], k=5):.4f}")  # ~0.498

    # 运行完整 demo(需要 OpenAI API Key)
    # demo()
```

#### 代码亮点解析

| 模块 | 亮点 |
|------|------|
| **RetrievalMetrics** | 4 个指标全部实现,支持分级相关度,NDCG 用 log2 折扣 |
| **LLMJudge** | Faithfulness 用陈述拆解法,Relevancy 用反向生成+embedding,成对比较做位置偏差消除 |
| **RAGEvaluator** | 整合检索+生成评估,自动诊断归因 |
| **_diagnose** | 基于指标组合自动给出优化建议,体现"评估驱动优化"思维 |

#### 面试中如何讲解这段代码

1. **先讲架构**:三层(数据结构 / 指标计算 / 整合评估),清晰解耦;
2. **重点讲 NDCG**:手推一遍 DCG/IDCG 公式,展示数学功底;
3. **讲 LLM-as-Judge 的工程细节**:temperature=0、JSON 输出、错误兜底、位置偏差消除;
4. **讲诊断逻辑**:展示你不只是"算指标",而是"用指标驱动决策"——这才是资深工程师的价值。

**面试加分点**:提到**评估结果的可复现性**——LLM-judge 即使 temperature=0 也可能因模型版本更新而不可复现,需要固定 judge 模型版本 + 定期用 golden set 回归。

</details>

---

### Q10: 系统设计题 — 设计一个企业级 RAG 评估平台,支持多项目、版本化、实验管理、自动报告生成。

<details>
<summary>展开答案</summary>

这是 P7+ 级别系统设计题,考察**架构能力**和**工程视野**。需要从需求出发,设计一个能服务多个业务团队的评估平台。

#### Step 1: 需求澄清

**功能性需求**:
1. **多项目隔离**:不同业务团队(客服/法务/医疗)的 RAG 系统独立管理;
2. **评估数据集管理**:版本化、可复用、可共享;
3. **实验管理**:对比不同配置(embedding/top-k/prompt/model)的指标;
4. **自动报告**:一键生成评估报告,支持导出 PDF/HTML;
5. **在线监控**:接入线上流量,持续评估;
6. **告警**:指标异常自动告警。

**非功能性需求**:
- 多租户隔离(数据安全);
- 评估任务并发(同时跑 10+ 实验);
- 评估成本可控(LLM-judge 调用费用);
- 评估结果可复现(版本绑定)。

#### Step 2: 容量估算

- 项目数:50 个业务团队;
- 每项目评估集:平均 1000 条;
- 每次评估 LLM-judge 调用:1000 次(每条 1 次 Faithfulness + 1 次 Relevancy);
- 单次评估成本:1000 * 2 * $0.01 = $20;
- 每日评估次数:每项目平均 2 次(开发期) → 50 * 2 = 100 次/天;
- 每日成本:100 * $20 = $2000 → 月 $60K,需做**成本优化**。

#### Step 3: 高层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     RAG 评估平台                                 │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Web UI   │  │ CLI SDK  │  │ API 网关  │  │ 告警服务  │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       └─────────────┴─────────────┴─────────────┘               │
│                         │                                        │
│  ┌──────────────────────▼──────────────────────────┐            │
│  │            评估调度服务 (Orchestrator)            │            │
│  │  - 任务队列 - 资源调度 - 成本控制 - 并发限制      │            │
│  └──┬──────────┬──────────┬──────────┬─────────────┘            │
│     │          │          │          │                           │
│  ┌──▼───┐ ┌───▼──┐ ┌────▼────┐ ┌───▼─────┐                     │
│  │检索指标│ │LLM   │ │人工评估  │ │在线采样  │                    │
│  │计算器  │ │Judge │ │管理器    │ │Agent    │                     │
│  └──┬───┘ └───┬──┘ └────┬────┘ └───┬─────┘                     │
│     │          │          │          │                           │
│  ┌──▼──────────▼──────────▼──────────▼───────────┐              │
│  │              数据层 (Data Layer)                │              │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐ │              │
│  │  │项目元数据│ │评估数据集│ │实验结果 │ │时序指标 │ │              │
│  │  │PostgreSQL│ │  S3    │ │PostgreSQL│ │InfluxDB│ │              │
│  │  └────────┘ └────────┘ └────────┘ └─────────┘ │              │
│  └────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

#### Step 4: 核心模块设计

##### 模块 1: 多项目管理

**数据模型**:
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    team VARCHAR(100),
    owner_id UUID,
    created_at TIMESTAMP,
    config JSONB  -- 默认评估配置
);

CREATE TABLE datasets (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    name VARCHAR(200),
    version VARCHAR(50),  -- 语义化版本,如 v1.2.0
    size INT,
    created_at TIMESTAMP,
    content_s3_uri VARCHAR(500),  -- 数据集内容存 S3
    UNIQUE(project_id, name, version)
);

CREATE TABLE experiments (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    dataset_id UUID REFERENCES datasets(id),
    name VARCHAR(200),
    config JSONB,  -- 完整配置: embedding, top_k, prompt, model 等
    status VARCHAR(20),  -- pending/running/completed/failed
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE eval_results (
    id UUID PRIMARY KEY,
    experiment_id UUID REFERENCES experiments(id),
    query_id VARCHAR(100),
    metrics JSONB,  -- 该条样本的所有指标
    detail JSONB,   -- 原始 query/context/answer/判断详情
    created_at TIMESTAMP
);
```

**版本化策略**:
- 数据集用**语义化版本**:`MAJOR.MINOR.PATCH`,大改升 MAJOR,增补升 MINOR,修正升 PATCH;
- 实验结果不可变(append-only),保证可复现;
- 配置快照:每次实验保存完整配置 JSON,即使后续修改默认配置,历史实验仍可复现。

##### 模块 2: 评估调度服务

```python
@dataclass
class EvalTask:
    experiment_id: str
    project_id: str
    dataset_uri: str
    config: dict
    priority: int = 5

class EvalOrchestrator:
    """评估任务调度器"""

    def __init__(self, redis_client, llm_pool, max_concurrent=10):
        self.queue = redis_client  # 用 Redis 做任务队列
        self.llm_pool = llm_pool   # LLM 调用连接池
        self.max_concurrent = max_concurrent
        self.cost_tracker = CostTracker(daily_budget=2000)  # 日预算

    async def submit(self, task: EvalTask):
        """提交评估任务"""
        # 成本预估
        est_cost = self._estimate_cost(task)
        if not self.cost_tracker.can_spend(est_cost):
            raise BudgetExceeded("今日评估预算已用尽")

        # 加入队列
        await self.queue.zadd(
            "eval_queue",
            {task.experiment_id: task.priority},
        )

    async def worker(self):
        """工作协程: 从队列拉取任务并执行"""
        while True:
            task_id = await self.queue.zpopmax("eval_queue")
            if not task_id:
                await asyncio.sleep(1)
                continue

            task = await self._load_task(task_id)
            try:
                await self._run_experiment(task)
            except Exception as e:
                await self._mark_failed(task, e)

    async def _run_experiment(self, task: EvalTask):
        """执行单个评估实验"""
        # 1. 加载数据集
        dataset = await self._load_dataset(task.dataset_uri)

        # 2. 对每条样本执行 RAG(调用被评估系统) + 评估
        results = []
        for sample in dataset:
            # 调用被评估的 RAG 系统
            rag_output = await self._call_rag_system(
                task.config["rag_endpoint"], sample
            )

            # 计算 Faithfulness / Relevancy
            metrics = await self._evaluate_sample(sample, rag_output)
            results.append(metrics)

            # 成本追踪
            self.cost_tracker.spend(metrics.cost)

        # 3. 汇总指标,写入数据库
        await self._save_results(task.experiment_id, results)

        # 4. 生成报告
        report = self._generate_report(task, results)
        await self._save_report(task.experiment_id, report)
```

##### 模块 3: 实验对比分析

```python
class ExperimentComparator:
    """实验对比分析"""

    def compare(self, baseline_exp_id: str, treatment_exp_id: str) -> Dict:
        """对比两个实验的指标差异"""
        baseline = self._load_results(baseline_exp_id)
        treatment = self._load_results(treatment_exp_id)

        comparison = {
            "metrics_diff": {},
            "significance": {},
            "per_query_diff": [],
            "regression_samples": [],  # 变差的样本
            "improvement_samples": [],  # 变好的样本
        }

        # 指标均值对比
        for metric in ["faithfulness", "answer_relevancy", "recall@5"]:
            b_mean = np.mean([r[metric] for r in baseline])
            t_mean = np.mean([r[metric] for r in treatment])
            comparison["metrics_diff"][metric] = {
                "baseline": b_mean,
                "treatment": t_mean,
                "delta": t_mean - b_mean,
                "delta_pct": (t_mean - b_mean) / b_mean * 100,
            }

            # 显著性检验
            _, p_value = ttest_ind(
                [r[metric] for r in treatment],
                [r[metric] for r in baseline]
            )
            comparison["significance"][metric] = {
                "p_value": p_value,
                "significant": p_value < 0.05
            }

        # 逐 query 对比,找出回归样本
        for b, t in zip(baseline, treatment):
            if b["query_id"] == t["query_id"]:
                diff = t["faithfulness"] - b["faithfulness"]
                if diff < -0.1:  # 显著变差
                    comparison["regression_samples"].append({
                        "query_id": b["query_id"],
                        "query": b["query"],
                        "baseline_f": b["faithfulness"],
                        "treatment_f": t["faithfulness"],
                        "delta": diff,
                    })
                elif diff > 0.1:
                    comparison["improvement_samples"].append({...})

        return comparison
```

##### 模块 4: 自动报告生成

```python
class ReportGenerator:
    """评估报告生成器"""

    def generate_html(self, experiment_id: str) -> str:
        """生成 HTML 报告"""
        exp = self._load_experiment(experiment_id)
        results = exp.results
        config = exp.config

        # 报告结构
        report = f"""
        <html>
        <head><title>RAG 评估报告 - {exp.name}</title></head>
        <body>
        <h1>RAG 评估报告</h1>
        <h2>实验信息</h2>
        <ul>
          <li>项目: {exp.project_name}</li>
          <li>数据集: {exp.dataset_name} (v{exp.dataset_version}, {len(results)} 条)</li>
          <li>配置: {json.dumps(config, indent=2)}</li>
          <li>执行时间: {exp.created_at}</li>
        </ul>

        <h2>检索指标</h2>
        {self._render_metrics_table(exp.retrieval_metrics)}

        <h2>生成指标</h2>
        {self._render_metrics_table(exp.generation_metrics)}

        <h2>诊断分析</h2>
        {self._render_diagnosis(exp.diagnosis)}

        <h2>低分样本(需人工 review)</h2>
        {self._render_low_score_samples(results, threshold=0.5)}

        <h2>分布分析</h2>
        {self._render_distribution_charts(results)}
        </body>
        </html>
        """
        return report
```

##### 模块 5: 在线监控 Agent

```python
class OnlineMonitorAgent:
    """线上流量采样评估"""

    def __init__(self, sample_rate=0.05):
        self.sample_rate = sample_rate
        self.judge = LLMJudge()

    async def maybe_evaluate(self, request, response):
        """对线上请求做抽样评估(异步,不阻塞主链路)"""
        # 分流采样
        if hash(request.user_id) % 100 >= self.sample_rate * 100:
            return

        # 异步评估
        asyncio.create_task(self._eval_and_record(request, response))

    async def _eval_and_record(self, request, response):
        try:
            score = await self.judge.score_faithfulness(
                request.query, response.contexts, response.answer
            )

            # 写入时序数据库
            self.influx.write(
                measurement="faithfulness",
                tags={
                    "project": request.project_id,
                    "domain": request.domain,
                },
                fields={"score": score["score"]},
                timestamp=datetime.now()
            )

            # 异常告警
            if score["score"] < 0.5:
                await self.alert.send(
                    f"Faithfulness 低分: {score['score']:.2f}\n"
                    f"Query: {request.query[:100]}"
                )
        except Exception as e:
            logger.error(f"在线评估失败: {e}")
            # 监控不能影响主链路,吞掉异常
```

#### Step 5: 成本优化策略

| 策略 | 节省比例 | 实现 |
|------|---------|------|
| **缓存 LLM-judge 结果** | 30-50% | 相同 (query, answer, context) hash 缓存 |
| **分级评估** | 40% | 先用便宜模型(如 GPT-3.5)初筛,低分再用 GPT-4 复核 |
| **批量调用** | 20% | 多条样本打包一次调用(利用长上下文) |
| **采样评估** | 80% | 开发期全量,线上 5% 采样 |
| **本地模型 judge** | 90% | 用 Llama-3-70B 部署本地 judge,牺牲精度省成本 |

#### Step 6: 多租户与权限

```
RBAC 模型:
- Project Admin: 管理项目配置、成员
- Eval Editor: 创建/运行实验
- Eval Viewer: 只能查看结果
- 通过 project_id 做数据隔离,API 层强制校验
```

#### Step 7: 与现有系统集成

```
评估平台
   ↑↓
CI/CD 系统 ─── 发布卡口(评估不通过阻断发布)
   ↑↓
监控告警系统 ── 在线指标接入
   ↑↓
知识库管理系统 ── 评估数据集从知识库生成
   ↑↓
A/B 测试平台 ── 实验数据回流
```

#### 面试中如何呈现

1. **先讲需求**(2 分钟):澄清功能/非功能需求,展示产品思维;
2. **画架构图**(3 分钟):分层清晰,标注关键组件;
3. **深入一个模块**(5 分钟):选评估调度或实验对比,讲实现细节;
4. **讨论权衡**(3 分钟):成本 vs 精度、实时 vs 离线、单租户 vs 多租户;
5. **扩展性讨论**(2 分钟):如何支持新的评估指标、如何接入新的 LLM。

**面试加分点**:
1. 提到 **"评估即代码(Eval as Code)"**——评估配置用 YAML/代码管理,可版本化、可 review、可 CI 集成;
2. 提到 **"评估的评估(Meta-eval)"**——定期用 golden set 校准 LLM-judge,监控 judge 自身漂移;
3. 提到 **"评估结果的统计严谨性"**——报告置信区间、做显著性检验,而非只报均值。

</details>

---

## 核心知识回顾表

| 主题 | 核心要点 | 关键指标/公式 | 面试高频度 |
|------|---------|--------------|-----------|
| **三层评估框架** | 检索层/生成层/端到端,分离便于归因 | - | ★★★★★ |
| **RAGAS 四指标** | Faithfulness/Answer Relevancy/Context Precision/Context Recall | 各自计算逻辑 | ★★★★★ |
| **Recall@K** | top-K 命中相关数 / 总相关数 | 召回完整性 | ★★★★ |
| **MRR** | 第一个相关文档倒数排名 | 1/rank | ★★★★ |
| **NDCG@K** | 考虑分级+位置折扣,归一化 | DCG/IDCG | ★★★★ |
| **Hit@K** | top-K 是否命中至少一个 | 二元 | ★★★ |
| **LLM-as-Judge** | 单评分/成对/参考对比,需校准 | Spearman 相关 | ★★★★★ |
| **评估数据集** | 日志/合成/增强/人工,分层策略 | - | ★★★★ |
| **A/B 测试** | 假设/OEC/护栏/样本量/显著性 | 样本量公式 | ★★★★ |
| **持续监控** | L1系统/L2业务/L3质量三层 | - | ★★★★ |
| **故障排查 SOP** | 止血→根因→修复→复盘 | - | ★★★★★ |
| **CUPED** | 用实验前协变量降方差 | - | ★★★(加分) |
| **Bonferroni 校正** | 多重比较 α/K | - | ★★★(加分) |
| **辛普森悖论** | 分流混淆导致整体结论反转 | - | ★★★(加分) |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────────┐
│                  RAG 评估速记卡 (Day 12)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ 【一句话框架】                                                   │
│   三层评估(检索/生成/E2E) + RAGAS四指标 + LLM-as-Judge +        │
│   A/B测试 + 持续监控                                             │
│                                                                  │
│ 【RAGAS 四指标速记】                                             │
│   Faithfulness    = 可验证陈述数 / 总陈述数 (生成层,查幻觉)     │
│   Answer Relevancy = 反向生成query与原query的相似度 (生成层)     │
│   Context Precision= 加权Precision@K (检索层,查排序)            │
│   Context Recall   = ground truth可支持陈述数 / 总陈述数 (检索层)│
│                                                                  │
│ 【检索指标速记】                                                 │
│   Recall@K = 命中相关数 / 总相关数                               │
│   Hit@K    = top-K 有命中→1,否则0                               │
│   MRR      = 1 / 第一个相关文档排名                              │
│   NDCG@K   = DCG@K / IDCG@K,DCG=Σ rel_i/log2(i+1)              │
│                                                                  │
│ 【LLM-as-Judge 三模式】                                          │
│   1. 单评分 (rubric打分,简单但不稳)                              │
│   2. 成对比较 (更稳,需swap消除位置偏差)                          │
│   3. 参考对比 (最客观,需ground truth)                            │
│   陷阱: 位置偏差/冗长偏差/自我偏好 → 校准+多judge投票             │
│                                                                  │
│ 【A/B测试五步】                                                  │
│   1. 假设(H0/H1) 2. OEC+护栏 3. 样本量(功效分析)               │
│   4. 分流(哈希+正交) 5. 显著性检验(Bonferroni校正)              │
│                                                                  │
│ 【监控三层】                                                     │
│   L1 系统: 延迟/QPS/错误率/成本 (秒级)                           │
│   L2 业务: 采纳率/重写率/拒答率 (实时)                           │
│   L3 质量: Faithfulness抽检/人工质检 (每日/每周)                 │
│                                                                  │
│ 【Faithfulness突降排查 SOP】                                     │
│   止血: 确认非judge故障 → 定位范围 → 回滚 → 降级prompt           │
│   根因: 知识库污染? embedding变更? 模型升级? context截断?        │
│   修复: 对症下药                                                 │
│   复盘: 时间线+根因+改进措施+预防                                │
│                                                                  │
│ 【一句话答面试官】                                               │
│   "RAG评估不是单看最终答案,而是三层分离+指标归因。              │
│    RAGAS四指标覆盖检索和生成,LLM-as-Judge降低人工成本,          │
│    A/B测试做上线决策,三层监控保线上质量。"                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

1. **RAGAS 不需要 ground truth 也能算 Faithfulness 和 Answer Relevancy**——这两个指标只需要 `(query, answer, context)`,只有 Context Recall/Precision 需要 ground truth。面试时别说错依赖项。

2. **NDCG 的 IDCG 是基于"理想排序"计算的,不是基于"所有文档"**——如果只有 3 个相关文档,IDCG@5 只算前 3 个理想位置的增益,不是把所有 top-5 都当成相关的。

3. **MRR 只看第一个相关文档,后面的相关文档位置不影响 MRR**——这是 MRR 与 MAP 的核心区别。如果面试官问"为什么 MRR 不够全面",答"它忽略了后续相关文档的排序"。

4. **LLM-as-Judge 的 temperature 必须设为 0**——否则同一输入多次评分不一致,评估不可复现。但即使 temp=0,不同模型版本仍可能不一致,需固定 judge 版本。

5. **成对比较必须做 swap 消除位置偏差**——只评一次会有系统性偏差(LLM 倾向选第一个),必须交换 A/B 顺序评两次,不一致才视为平局。

6. **A/B 测试的样本量计算要在实验前做,不能事后补**——否则就是 p-hacking。同时 MDE(最小可检测效应)设太小会导致样本量爆炸,需权衡。

7. **Faithfulness 高不代表答案正确**——Faithfulness 只衡量"是否忠于上下文",如果上下文本身就是错的(检索召回了错误文档),Faithfulness 可能很高但答案是错的。需要结合 Context Recall 看。

8. **BLEU/ROUGE 不适合评估 RAG 生成质量**——它们衡量字面匹配,但 RAG 答案的正确性是语义层面的,同一答案可有多种正确表述。面试时别说"用 BLEU 评估 RAG"。

9. **评估数据集要和知识库版本绑定**——知识库更新后,旧的评估集可能失效(相关文档标注变化)。每次知识库大更新都需重新审视评估集,否则指标不可比。

10. **线上 LLM-judge 抽检不能阻塞主链路**——必须异步执行,且要做超时兜底和异常吞掉(监控故障不能影响业务)。曾有团队因同步 judge 导致 P99 延迟翻倍的故障。

---

## 自测检查清单

### 概念题(10 道)

- [ ] 1. 能口述 RAG 评估的三层框架及各层关键指标?
- [ ] 2. 能默写 RAGAS 四个指标的名称、定义、所需输入、对应层次?
- [ ] 3. 能手算给定场景下的 Recall@5、MRR、NDCG@5?
- [ ] 4. 能说出 Faithfulness 和 Answer Relevancy 的正交关系,并举例?
- [ ] 5. 能列出 LLM-as-Judge 的三种模式及至少 3 个陷阱?
- [ ] 6. 能说出评估数据集的 4 种构建方法及各自的优缺点?
- [ ] 7. 能口述 A/B 测试的完整 5 步流程?
- [ ] 8. 能说出 RAG 持续监控的三层指标及告警分级?
- [ ] 9. 能口述 Faithfulness 突降的排查 SOP(止血→根因→修复→复盘)?
- [ ] 10. 能解释为什么 BLEU/ROUGE 不适合评估 RAG?

### 代码题(3 道)

- [ ] 11. 能手写 Recall@K、MRR、NDCG@K 的 Python 实现(不看答案)?
- [ ] 12. 能实现一个 LLM-as-Judge 的成对比较函数(含 swap 消除位置偏差)?
- [ ] 13. 能写一个简单的评估报告生成函数,输出指标均值+低分样本列表?

### 系统设计题(2 道)

- [ ] 14. 能画出企业级 RAG 评估平台的高层架构图,标注核心组件?
- [ ] 15. 能讨论评估平台的成本优化策略(至少 3 种)和多租户隔离方案?

> **评分标准**:13-15 项全勾 = 面试稳过;10-12 项 = 需要补强;<10 项 = 建议重学。

---

## 延伸阅读

### 论文

1. **RAGAS: Automated Evaluation of Retrieval Augmented Generation** (Esmaeilzadeh et al., 2023) —— RAGAS 原始论文
2. **Evaluating RAG Systems with LLM-as-a-Judge** (Saad-Falcon et al., 2023) —— LLM-as-Judge 在 RAG 中的应用
3. **ARES: An Automated Evaluation Framework for RAG** (Yan et al., 2024) —— 用少量人工标注 + LLM 自动评估
4. **TruLens: RAG Triad** —— Context Relevance / Groundedness / Answer Relevance 三元组
5. **Evol-Instruct** (Xu et al., 2023) —— 用 LLM 进化指令增加难度
6. **CUPED: Controlled-experiment Using Pre-Experiment Data** (Deng et al., 2013) —— A/B 测试方差降低
7. **Chatbot Arena: Bradley-Terry 模型** —— 成对比较的 Elo 评分

### 开源框架

| 框架 | 特点 | 适用场景 |
|------|------|---------|
| **RAGAS** | RAG 专用,四指标开箱即用 | 快速评估 |
| **TruLens** | RAG Triad + 追踪(trace) | 全链路调试 |
| **DeepEval** | 类 PyTorch 风格,支持 CI 集成 | 工程化评估 |
| **LangSmith** | LangChain 官方,在线监控 | LangChain 用户 |
| **Phoenix** (Arize) | 可视化 + 漂移检测 | 线上监控 |
| **Promptfoo** | 配置驱动,CLI 友好 | 快速对比 |

### 博客与文章

- [Evaluating RAG: A Comprehensive Guide](https://docs.ragas.io/) —— RAGAS 官方文档
- [LLM-as-Judge: A Complete Guide](https://www.promptingguide.ai/evaluation/llm-based) —— Prompt Engineering Guide
- [A/B Testing at Scale](https://netflixtechblog.com/) —— Netflix 技术博客
- [Microsoft Experimentation Platform](https://www.microsoft.com/en-us/research/group/experimentation-platform-exp/) —— 微软实验平台

### 实战项目建议

1. **用 RAGAS 评估你的 Day8 RAG demo**:接入 RAGAS,跑一次完整评估,记录基线指标;
2. **实现一个简化版 LLM-judge**:用 GPT-4 实现 Faithfulness 评分,用 golden set 校准;
3. **设计一次 A/B 测试**:针对你的 RAG demo,设计 BM25 vs Dense 的 A/B 测试方案(不需真实流量,写方案即可)。

---

## 明日预告

### Day 13 — RAG-Agent 实战 Demo 规划

明天我们将进入 Week2 的实战环节,规划并启动一个**完整的 RAG-Agent 项目**:

- **项目选型**:从 3 个候选(个人知识库助手 / 代码问答 / 多文档研究助手)中选定一个;
- **架构设计**:基于 Day8-12 所学,设计完整链路(query rewriting → 检索 → rerank → 生成 → 评估闭环);
- **技术栈确定**:LangChain / LlamaIndex / 自研,向量库选型,模型选型;
- **评估集成**:把今天的评估框架嵌入项目,做到"开发即评估";
- **里程碑规划**:Day13-15 三天分阶段交付,Day15 完成一个可演示的 demo。

**预习建议**:
1. 思考你想做一个什么场景的 RAG-Agent(结合你的工作/学习需求);
2. 准备好开发环境(Python 3.10+,OpenAI API Key 或本地模型);
3. 复习 Day8 的 RAG 全链路图,明天会基于它做架构设计。

> 今日总结:**RAG 评估不是事后补丁,而是贯穿研发-上线-运维全生命周期的工程实践。三层框架给归因,RAGAS 给标尺,LLM-as-Judge 给低成本,A/B 测试给决策,监控给安全网。** 掌握今天的内容,你就从"能跑 RAG"升级到"能评估 RAG"——这是工程师与调包侠的分水岭。

---

*本文件为"AI Agent 面试 31 天冲刺计划"Day12 内容 | 更新日期: 2026-09-23*
