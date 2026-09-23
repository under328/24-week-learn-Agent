# Day 18 — Agent 评测与可观测性

> **学习目标**: 系统掌握 Agent 系统的评测方法论(任务/轨迹/基准)与可观测性体系(Tracing/Logging/Metrics),能独立设计线上监控平台并完成核心代码实现。
>
> **面试定位**: 中高级 Agent 工程师必考。面试官通过此模块考察候选人对"Agent 上线后如何保证质量"的工程化思维,以及与传统 LLM/ML 系统在评测、监控上的差异理解。属于区分"会写 Demo"与"能落地生产"的分水岭题型。
>
> **预计学习时长**: 4-5 小时(含手撕代码)。
>
> **前置知识**: Day17 Multi-Agent 协作、Day14 LangChain/LangGraph 框架、Day10 ReAct/Plan-Execute 模式。

---

## 今日知识图谱

```
Agent 评测与可观测性
│
├── 1. Agent 评测 (Evaluation)
│   ├── 1.1 核心挑战
│   │   ├── 长轨迹 vs 单轮输出
│   │   ├── 工具调用副作用 (外部状态变化)
│   │   ├── 多路径达成同一目标
│   │   └── 成本/延迟与质量的权衡
│   ├── 1.2 评测维度
│   │   ├── 任务完成率 (Success Rate)
│   │   ├── 效率 (Steps / Tokens / Time)
│   │   ├── 成本 (Cost per task)
│   │   ├── 安全 (Safety / Hallucination)
│   │   └── 鲁棒性 (Robustness)
│   ├── 1.3 评估方法
│   │   ├── 端到端评估 (End-to-End)
│   │   ├── 步骤级评估 (Step-level)
│   │   └── 轨迹评估 (Trajectory)
│   ├── 1.4 基准测试
│   │   ├── AgentBench (8 类任务)
│   │   ├── ToolBench (API 调用)
│   │   ├── WebArena (Web 交互)
│   │   ├── SWE-bench (真实 issue 修复)
│   │   ├── GAIA (通用助手)
│   │   └── τ-bench (工具调用对齐)
│   └── 1.5 LLM-as-Judge
│       ├── 适用场景
│       ├── 偏差 (位置/冗长/自我偏好)
│       └── 缓解策略 (多裁判/参考答案/校准)
│
├── 2. 可观测性三支柱 (Observability)
│   ├── 2.1 Tracing (分布式追踪)
│   │   ├── Span / Trace 模型
│   │   ├── 因果关系与嵌套
│   │   └── OpenTelemetry 语义约定
│   ├── 2.2 Logging (结构化日志)
│   │   ├── 请求/响应/Prompt/工具IO
│   │   ├── 关联 TraceID
│   │   └── 采样与脱敏
│   └── 2.3 Metrics (指标)
│   │   ├── RED (Rate/Errors/Duration)
│   │   ├── USE (Utilization/Saturation/Errors)
│   │   └── Agent 专属指标
│
├── 3. 可观测性工具
│   ├── 3.1 LangSmith (LangChain 官方)
│   ├── 3.2 Langfuse (开源)
│   ├── 3.3 Arize Phoenix
│   ├── 3.4 OpenLLMetry / OpenInference
│   └── 3.5 Helicone / Weights & Biases
│
├── 4. 调试技术
│   ├── 4.1 回放调试 (Replay)
│   ├── 4.2 断点调试 (Breakpoint)
│   ├── 4.3 Trace 分析 (瓶颈/循环)
│   └── 4.4 Token 审计 (成本归因)
│
└── 5. 监控告警系统
    ├── 5.1 监控指标设计
    │   ├── 延迟 P50/P95/P99
    │   ├── 成本 (token/美元)
    │   ├── 错误率与错误分类
    │   ├── 工具调用成功率
    │   └── 循环检测
    ├── 5.2 告警策略
    │   ├── 阈值告警
    │   ├── 异常检测 (同比环比)
    │   └── 多维根因定位
    └── 5.3 线上平台架构
        ├── 数据采集层
        ├── 存储层 (TSDB + Object Store)
        ├── 计算层 (流批结合)
        └── 可视化层
```

---

## 面试题

### Q1: Agent 评测的核心挑战是什么?为什么比传统 ML 评测更难?请列举 Agent 的主要评测维度。

<details>
<summary>点击展开答案</summary>

**核心挑战 — 为什么 Agent 评测更难:**

| 维度 | 传统 ML / 单轮 LLM | Agent |
|------|-------------------|-------|
| 输出形态 | 单次预测 (分类/生成) | 多步骤、多轮、多工具的**轨迹** |
| 评估对象 | 最终输出 vs 标签 | 过程 + 结果都要评估 |
| 副作用 | 无 (纯函数) | 工具调用改变外部状态 (发邮件/写库),**不可重放** |
| 路径多样性 | 通常一条最优解 | 同一目标可由多条合理路径达成,需评估**轨迹合理性** |
| 成本敏感 | 推理一次即可 | 一次任务可能调几十次 LLM + 工具,成本/延迟爆炸 |
| 标注难度 | 单条输出易标注 | 整条轨迹需专家逐 step 判断,标注成本 10-100x |
| 环境依赖 | 静态测试集 | 依赖真实环境 (Web/DB/API),环境会变,结果不可复现 |
| 长尾与安全 | 较少涉及 | 长时间运行可能触发安全/伦理边界 |

**Agent 的主要评测维度:**

1. **任务完成率 (Success Rate)** — 最终是否达成用户目标。最核心,但单看它不够。
2. **效率 (Efficiency)** — 完成任务所需的步数、token 数、轮数。同样成功,3 步优于 10 步。
3. **成本 (Cost)** — 单次任务的美元成本 (LLM 调用 + 工具调用)。生产环境必须算。
4. **延迟 (Latency)** — 端到端时延,以及各阶段 (规划/工具/反思) 的时延分布。
5. **安全性 (Safety)** — 是否产生幻觉、是否执行危险工具、是否泄露敏感信息。
6. **鲁棒性 (Robustness)** — 工具失败、网络抖动、Prompt 注入下的恢复能力。
7. **轨迹合理性 (Trajectory Quality)** — 是否走了最优路径,有无冗余步骤、循环、回溯。
8. **用户满意度 (User Satisfaction)** — 主观维度,通常通过反馈按钮或重试率代理。

**面试加分点:**
- 强调"**结果指标 vs 过程指标**"的区分。生产 Agent 不仅要结果对,过程也要可控。
- 提到"**离线评测 vs 在线评测**":离线用基准测能力,在线用 A/B + 真实用户行为测体验。
- 提到"**评估本身的不确定性**":LLM 输出非确定性,同一任务多次运行成功率要统计置信区间。

</details>

---

### Q2: 请对比 Agent 的三种评估方法 — 端到端评估、步骤级评估、轨迹评估,各自的优劣与适用场景。

<details>
<summary>点击展开答案</summary>

**三种评估方法对比:**

| 方法 | 评估对象 | 判定方式 | 优点 | 缺点 | 适用场景 |
|------|---------|---------|------|------|---------|
| **端到端评估 (E2E)** | 最终输出/最终状态 | 与 ground truth 比对 / 规则校验 / LLM 判分 | 标注便宜;贴近用户感知;易自动化 | 无法定位失败步骤;鼓励"绕路也能到" | 离线基准测试、回归测试、A/B 主指标 |
| **步骤级评估 (Step-level)** | 每个动作 (Thought/Action/Observation) | 人工或 LLM 逐 step 打分 | 可定位问题步骤;支持细粒度奖励 (RL) | 标注成本高;步骤间依赖导致单步分数有偏 | 训练阶段 reward shaping、错误归因 |
| **轨迹评估 (Trajectory)** | 整条轨迹 (动作序列) | 与参考轨迹比对 / 路径合理性打分 | 评估过程质量;识别冗余/循环;鼓励最优路径 | 参考轨迹难获得;多解问题下判定主观 | 生产监控、效率优化、Agent 比较选型 |

**关键细节:**

**端到端评估的两种实现:**
- **状态校验 (State-based)**:任务定义最终状态,运行后检查状态是否满足。例:"帮我订明天北京的机票" → 检查日历是否有明天北京的机票记录。适合有明确状态变化的任务。
- **输出校验 (Output-based)**:对比最终答案。例:GAIA 用精确匹配 + 软匹配。适合 QA 类任务。

**步骤级评估的难点 — 步骤依赖:**
```
Step1: 搜索天气   → 正确
Step2: 基于错误搜索结果推理 → 看似错误,但根因在 Step1
```
单看 Step2 会误判。缓解:用**反事实** (给 Step2 正确的 Step1 输入,看是否正确) 或**因果归因**。

**轨迹评估的两种范式:**
- **参考轨迹比对 (Reference-based)**:需要专家示范轨迹。用编辑距离 / 子序列匹配。问题:多解场景下,与参考不同 ≠ 错误。
- **无参考轨迹评估 (Reference-free)**:用 LLM 判断轨迹是否"高效、无冗余、无循环"。更灵活但引入 LLM 偏差。

**实际工程中的组合策略:**
```
生产评估 = E2E 主指标 (Success Rate) 
         + 轨迹指标 (平均步数、循环率) 
         + 失败案例的步骤级归因 (采样)
```

**面试加分点:**
- 提到 **τ-bench (tau-bench)** 的设计:它用"用户模拟器 + 状态校验"做 E2E,同时记录轨迹用于轨迹分析,是工业级评估的范例。
- 强调"**评估成本本身也是成本**":步骤级评估用 LLM-as-Judge 时,评估成本可能超过被评估任务。需要采样。
- 提到 **"评估的评估" (Meta-evaluation)**:评估方法本身也要验证 (与人工标注的一致性),否则评估方法不可信。

</details>

---

### Q3: 请介绍 AgentBench、ToolBench、WebArena、SWE-bench 等主流基准测试,它们各自评估 Agent 的什么能力?

<details>
<summary>点击展开答案</summary>

**主流 Agent 基准测试一览:**

| 基准 | 发布 | 任务数 | 评估能力 | 环境 | 评估方式 |
|------|------|--------|---------|------|---------|
| **AgentBench** | 2023 (THU) | 8 类环境 | 综合推理+决策+工具 | OS/DB/Web/Game/KG/... | 状态校验 |
| **ToolBench** | 2023 (THU) | 16k+ 真实 API | 工具调用、API 组合 | RapidAPI | Pass/Win-Rate |
| **WebArena** | 2023 (CMU) | 812 Web 任务 | 真实网页交互 | 自托管网站 | 状态校验 |
| **SWE-bench** | 2023 (Princeton) | 2294 真实 issue | 代码修复全流程 | GitHub repo + 测试 | 测试通过率 |
| **GAIA** | 2023 (Meta) | 466 通用任务 | 真实世界通用助手 | 多模态+Web+工具 | 精确匹配 |
| **τ-bench** | 2024 (Sierra) | 165 工具任务 | 工具调用对齐 (策略合规) | 模拟客服系统 | 状态校验 + 用户模拟 |
| **MLE-bench** | 2024 (OpenAI) | 75 Kaggle 竞赛 | ML 工程能力 | Kaggle 环境 | 奖牌率 |
| **AndroidWorld** | 2024 (Google) | 116 Android 任务 | 移动端 UI 自动化 | Android 模拟器 | 状态校验 |

**重点解析:**

**1. AgentBench — 综合能力体检:**
- 8 类环境:操作系统 (Linux)、数据库 (SQL)、知识图谱 (KG)、卡片游戏、家用模拟 (ALFWorld)、网页购物、思维实验、数据库查询。
- 贡献:首次系统化对比 LLM 在多环境的 Agent 能力,揭示"强 LLM ≠ 强 Agent" (GPT-4 在某些环境仍远低于人类)。

**2. ToolBench — 工具调用规模:**
- 从 RapidAPI 爬取 16464 个真实 API,构造多工具调用任务。
- 评估指标:**Pass Rate** (单工具) + **Win Rate** (多工具,用 LLM 比对两个答案)。
- 贡献:大规模真实 API,考验工具选择与组合能力。

**3. WebArena — 真实网页交互:**
- 自托管一套真实网站 (Reddit/GitHub/电商/内容管理),避免"网页变化导致不可复现"。
- 任务需多步点击、表单填写、跨站点操作。
- 贡献:首个**可复现**的真实 Web 交互基准,State 校验精确。

**4. SWE-bench — 真实软件工程:**
- 从 12 个开源 Python 仓库的真实 GitHub issue 构造,任务:给 issue + repo,提交 patch。
- 评估:**测试通过率** (FAIL_TO_PASS + PASS_TO_PASS)。
- 贡献:最难的 Agent 基准之一。截至 2024 年初,最佳模型仅 ~20% 解决率。**揭示 Agent 在长上下文 + 复杂代码库上的瓶颈**。

**5. GAIA — 通用助手真实任务:**
- 由人类标注的真实世界任务,需要多步推理 + 工具 + 多模态。
- 三级难度,Level 3 人类平均 92% 正确,最佳模型 <15%。
- 贡献:证明"通用 Agent"远未达到人类水平。

**6. τ-bench (tau-bench) — 工具调用对齐:**
- 模拟零售/航空客服,Agent 需在遵守业务**策略**的前提下调用工具。
- 用用户模拟器多轮交互,最后校验**数据库状态**是否正确。
- 贡献:首次系统化评估"**策略合规**",而非单纯任务完成。揭示模型会"完成任务但违反策略"。

**面试加分点:**
- 强调"**基准污染**":很多基准数据可能进入训练集,导致分数虚高。SWE-bench 通过"时间切分" (只用某日期前的 issue) 部分缓解。
- 提到"**基准≠生产**":基准是标准化沙盘,生产环境有更多长尾、噪声、安全约束。基准 SOTA 不代表生产可用。
- 提到"**基准演化**":Agent 能力提升后,旧基准饱和 (如 ALFWorld 接近满分),需新基准。SWE-bench Verified、τ-bench 是 2024 演化方向。

</details>

---

### Q4: LLM-as-Judge 在 Agent 评估中如何应用?有哪些已知偏差和缓解策略?

<details>
<summary>点击展开答案</summary>

**LLM-as-Judge 在 Agent 评估中的应用:**

**1. 应用场景:**
- **轨迹评估**:让 LLM 判断整条轨迹是否合理、高效、无循环。
- **步骤级评估**:逐 step 让 LLM 判断 Thought/Action 是否恰当。
- **开放式任务打分**:无标准答案的任务 (如"写一份调研报告"),用 LLM 按多维度打分。
- **成对比较 (Pairwise)**:让 LLM 比较两个 Agent 的输出哪个更好 (Chatbot Arena 范式)。
- **工具调用合理性**:判断工具选择、参数构造是否合理。

**2. 典型 Prompt 模板 (轨迹评估):**
```
你是一名 Agent 评估专家。请评估以下轨迹:

任务: {task}
轨迹: {trajectory}

请按以下维度打分 (1-5):
1. 任务完成度: 是否达成目标
2. 路径效率: 是否有冗余步骤
3. 工具使用: 工具选择与参数是否合理
4. 推理质量: Thought 是否清晰、无幻觉
5. 安全性: 是否有危险操作

输出 JSON: {"完成度": x, "效率": x, ...}
```

**已知偏差:**

| 偏差 | 表现 | 原因 |
|------|------|------|
| **位置偏差 (Position Bias)** | 成对比较时偏好第一个/第二个 | 训练数据分布 |
| **冗长偏差 (Verbosity Bias)** | 偏好更长的回答 | 长文本看起来更"用心" |
| **自我偏好 (Self-Bias)** | GPT-4 偏好 GPT-4 的输出 | 同源风格熟悉度高 |
| **格式偏差 (Format Bias)** | 偏好结构化 (列表/表格) 输出 | 训练数据中结构化文本质量高 |
| **锚定偏差 (Anchoring)** | 受参考答案影响过大 | 参考答案限制了 LLM 的判断空间 |
| **一致性偏差 (Consistency)** | 同一输入多次评判结果不同 | LLM 采样温度 |
| **能力上限偏差** | 判官 LLM 弱于被评估 LLM 时不可靠 | 弱模型判不动强模型 |
| **仁慈偏差 (Leniency)** | 倾向给高分 | "讨好"倾向 |

**缓解策略:**

1. **多裁判集成 (Multi-Judge)**:用多个不同模型投票,GPT-4 + Claude + Gemini 取平均,降低单模型偏差。
2. **位置交换 (Position Swap)**:成对比较时交换位置两次,只有都赢才算赢。
3. **参考答案校准 (Reference-Guided)**:提供高质量参考答案作为锚点,但允许"超越参考"。
4. **细粒度 Rubric**:给出明确的打分细则,而非"凭感觉打分",减少仁慈偏差。
5. **CoT + 校准**:让 LLM 先解释再打分,并要求"重新审视"机制。
6. **人工校准**:抽样 5-10% 人工标注,计算 LLM-Judge 与人工的 Cohen's Kappa,低于阈值则不可信。
7. **强模型判弱模型**:判官 LLM 必须强于或至少等于被评估模型,否则不可靠。
8. **去冗长化**:先对被评估输出做长度归一化,或用"信息密度"代替原始长度。

**LLM-as-Judge 的局限:**
- **成本高**:评估一个长轨迹可能消耗 10k+ token,大规模评测贵。
- **不可复现**:温度 >0 时同一输入打分不同,需多次平均。
- **领域弱**:专业领域 (医疗/法律/代码细节) 判断可能不如领域专家。
- **奖励黑客**:被评估 Agent 可能学到"投其所好" (生成 LLM-Judge 偏好的格式而非真正好答案)。

**面试加分点:**
- 提到 **"评估的scaling law"**:用更多弱 LLM 投票,可能比单个强 LLM 更准,成本更低。
- 提到 **过程奖励模型 (PRM)**:OpenAI 的 "Let's Verify Step by Step" — 用步骤级人工标注训练 PRM,比 LLM-as-Judge 更便宜且更准。
- 强调"**LLM-as-Judge 是过渡方案**":最终需要训练专门的 Reward Model,LLM-as-Judge 只是数据标注阶段的工具。

</details>

---

### Q5: 什么是 Agent 可观测性的三支柱?它们在 Agent 系统中分别解决什么问题?

<details>
<summary>点击展开答案</summary>

**可观测性三支柱 (Three Pillars of Observability):**

| 支柱 | 定义 | 传统系统作用 | Agent 系统特殊价值 |
|------|------|------------|------------------|
| **Tracing (追踪)** | 单次请求经过的所有服务/步骤的因果链路 | 微服务调用链路定位瓶颈 | 一次 Agent 任务可能 100+ LLM/工具调用,无 Trace 无法定位卡在哪步 |
| **Logging (日志)** | 离散事件的结构化记录 | 错误日志、审计日志 | 必须记录完整 Prompt/Response/工具IO,用于回放和合规审计 |
| **Metrics (指标)** | 聚合的数值时序数据 | QPS/延迟/错误率 | Token 成本、工具成功率、循环率等 Agent 专属指标 |

**三者的关系 (面试关键):**
```
Metrics  → 告诉你"有问题" (系统慢了/贵了/错了)
Tracing  → 告诉你"问题在哪" (哪个步骤慢/哪个工具错)  
Logging  → 告诉你"为什么" (具体的 Prompt/Response/参数)
```
三者通过 **TraceID + SpanID** 关联,从指标下钻到 trace,再下钻到 log,是标准排障路径。

**1. Tracing — Agent 场景的核心:**

**Span 模型 (OpenTelemetry 语义):**
```python
# Span 数据结构示意 (实际用 dataclass 或 protobuf 定义)
span = {
    "trace_id": "abc123",       # 一次 Agent 任务唯一
    "span_id": "def456",        # 当前步骤唯一
    "parent_span_id": "ghi789", # 父步骤 (构建嵌套树)
    "name": "tool_call:search",
    "kind": "INTERNAL",         # INTERNAL/CLIENT/SERVER
    "start_time": ...,
    "end_time": ...,
    "attributes": {
        "llm.model": "gpt-4",
        "llm.tokens.prompt": 1200,
        "llm.tokens.completion": 300,
        "tool.name": "search",
        "tool.input": "...",
        "tool.output": "...",
    },
    "status": "OK",
    "events": [...]             # 步骤内事件 (重试/反思)
}
```

**Agent Trace 的典型树形结构:**
```
Agent.run (root span)
├── LLM.call (planning)
│   ├── prompt: ...
│   └── response: ...
├── Tool.search
│   ├── HTTP.call
│   └── Parse.response
├── LLM.call (reasoning)
└── Tool.write_db
```

**为什么 Agent 特别需要 Trace:**
- 一次任务调用链路深 (10-100 层),日志看不出层级关系。
- 性能瓶颈常在某一两个工具 (如某个慢 API),Trace 一眼可见。
- 成本归因:哪个步骤烧了最多 token,Trace 的 attributes 直接统计。

**2. Logging — Agent 场景的特殊性:**

**必须记录的字段:**
- 完整 Prompt (含 system + few-shot + user)
- 完整 Response (含 reasoning)
- 工具名、工具输入、工具输出
- 模型名、温度、token 数
- TraceID / SpanID (关联 trace)
- 用户 ID、会话 ID

**关键挑战:**
- **体量大**:一次任务可能产生 MB 级日志 (含完整 Prompt)。
- **脱敏**:Prompt 中可能含 PII,日志需脱敏后存储。
- **采样**:全量存储贵,通常对成功任务采样、失败任务全量。
- **合规**:某些行业 (金融/医疗) 要求 Prompt/Response 可审计。

**3. Metrics — Agent 专属指标体系:**

**RED 指标 (Rate/Errors/Duration) 在 Agent 上的扩展:**
| 指标 | 定义 | 告警阈值示例 |
|------|------|------------|
| Task Success Rate | 任务成功率 | <80% 告警 |
| Task Duration P95 | 任务端到端时延 | >60s 告警 |
| LLM Call Rate | 每分钟 LLM 调用次数 | 突增 50% 告警 |
| Tool Error Rate | 工具调用失败率 | >5% 告警 |
| Token Cost / Task | 单任务平均 token 成本 | 同比上涨 30% 告警 |
| Loop Rate | 出现循环的任务占比 | >2% 告警 |
| Hallucination Rate | 幻觉率 (抽样人工) | >3% 告警 |
| Tool Call Distribution | 工具调用分布 | 单工具占比 >70% 告警 (退化) |

**面试加分点:**
- 强调"**Agent 可观测性 ≠ 传统可观测性**":Agent 的"逻辑"是 LLM 生成的,不是代码硬编码的。同一个任务,两次执行的代码路径完全不同。所以 Trace 必须记录"语义层" (Thought/Action) 而不仅是"代码层" (函数调用)。
- 提到 **OpenTelemetry GenAI 语义约定**:OTel 社区正在标准化 LLM/Agent 的 span attributes (`gen_ai.*`),这是工业界共识方向。
- 提到"**可观测性是 Agent 安全的基础**":没有 Trace,根本无法发现 Prompt 注入、越权工具调用等问题。

</details>

---

### Q6: 对比 LangSmith、Langfuse、Phoenix 等 Agent 可观测性工具,如何选型?

<details>
<summary>点击展开答案</summary>

**主流 Agent 可观测性工具对比:**

| 工具 | 厂商 | 开源 | 部署方式 | 核心定位 | Agent 支持 | 成本 |
|------|------|------|---------|---------|----------|------|
| **LangSmith** | LangChain | 闭源 | SaaS / 自托管 (企业版) | LangChain 生态深度集成 | 原生支持 LangChain/LangGraph | 免费 5k traces/月,付费按量 |
| **Langfuse** | Langfuse | 开源 (MIT) | SaaS / 自托管 | 框架无关,通用 LLM 可观测性 | 通过 SDK 集成任意框架 | 自托管免费,SaaS 按量 |
| **Arize Phoenix** | Arize | 开源 (Apache 2.0) | 本地 / SaaS | 侧重评估 + 评测 | OpenInference 标准,支持多框架 | 本地免费,SaaS 按量 |
| **Helicone** | Helicone | 开源 | SaaS / 自托管 | 轻量代理层 (Proxy 模式) | 代理 LLM 调用即可 | 免费额度,按量 |
| **Weights & Biases** | W&B | 闭源 | SaaS | 实验跟踪 + 评估 | 集成 LangChain | 按席位 |
| **OpenLLMetry** | Traceloop | 开源 (Apache 2.0) | 库 + 后端 | OTel 标准实现 | 任何 OTel 后端 (Jaeger/Tempo) | 开源免费 |
| **Datadog LLM** | Datadog | 闭源 | SaaS | 企业级 APM 扩展 | 集成主流框架 | 按 APM 计费 |

**深入解析:**

**1. LangSmith — LangChain 用户的首选:**
- **优势**:
  - 与 LangChain/LangGraph 深度集成,零配置开箱即用。
  - 强大的 Trace 可视化 (树形展开 + Prompt/Response 详情)。
  - 内置 Datasets + Evaluator,支持离线评测流水线。
  - 支持回放 (Replay) 和 Prompt Hub。
- **劣势**:
  - 与 LangChain 强绑定,非 LangChain 项目集成成本高。
  - 闭源,自托管需企业版付费。
  - 数据出境合规问题 (SaaS 在美区)。

**2. Langfuse — 开源通用方案:**
- **优势**:
  - **框架无关**,通过 SDK 或 OTel 集成任意框架 (LangChain/LlamaIndex/自定义)。
  - 开源 MIT,可自托管,数据不出公司。
  - 支持 Tracing + Evaluation + Prompt Management + Analytics 全套。
  - 提供 REST API,易扩展。
- **劣势**:
  - 可视化体验略逊 LangSmith。
  - 评估流水线需自己搭,不如 LangSmith 开箱即用。

**3. Arize Phoenix — 评估导向:**
- **优势**:
  - 定义 **OpenInference** 标准 (OpenTelemetry 的 LLM 扩展),推动标准化。
  - 强大的评估能力,内置 LLM-as-Judge 模板。
  - 本地运行免费,适合开发调试。
  - 与 Arize 生产监控平台打通。
- **劣势**:
  - 生产级监控需搭配 Arize SaaS (付费)。
  - Trace 可视化偏数据科学风格,工程化弱。

**4. OpenLLMetry — OTel 原生:**
- **优势**:
  - 完全遵循 OpenTelemetry 标准,与现有 APM (Jaeger/Tempo/Datadog) 无缝集成。
  - 适合已有 OTel 体系的企业,无需新栈。
  - 自动埋点主流 LLM 库 (OpenAI/Anthropic/LangChain)。
- **劣势**:
  - 只做数据采集,可视化依赖后端。
  - Agent 语义层 (Thought/Action) 支持弱。

**选型决策树:**
```
是否用 LangChain 为主?
├── 是 → 是否介意数据出境 + 付费?
│   ├── 否 → LangSmith
│   └── 是 → Langfuse (开源自托管) + LangChain callback
└── 否 → 是否已有 OTel/APM 体系?
    ├── 是 → OpenLLMetry + 现有后端
    └── 否 → 是否需要强评估能力?
        ├── 是 → Arize Phoenix
        └── 否 → Langfuse (最通用)
```

**面试加分点:**
- 强调"**OpenTelemetry 是终局**":各家私有 SDK 终会被 OTel GenAI 语义约定统一。选型时优先考虑 OTel 兼容性。
- 提到"**数据合规**":金融/政务场景必须自托管,Langfuse 开源版是首选。
- 提到"**成本陷阱**":Trace 全量上报,token 量可能占总成本 5-10%。需采样策略 (错误全量 + 成功采样)。
- 提到"**评估一体化**":未来趋势是"可观测性 + 评估"融合,Trace 直接喂给 Evaluator 做线上质量监控。

</details>

---

### Q7: Agent 调试有哪些技术?回放调试、断点调试、Trace 分析、Token 审计分别解决什么问题?

<details>
<summary>点击展开答案</summary>

**Agent 调试技术全景:**

| 技术 | 解决的问题 | 实现方式 | 适用阶段 |
|------|----------|---------|---------|
| **回放调试 (Replay)** | "为什么这次任务失败了?重跑要复现" | 录制 + 回放 (mock LLM/工具响应) | 线上问题排查 |
| **断点调试 (Breakpoint)** | "在某一步暂停,看状态" | LangGraph 的 interrupt / IDE 断点 | 开发调试 |
| **Trace 分析** | "瓶颈/循环在哪" | Trace 可视化 + 自动分析 | 性能优化、循环检测 |
| **Token 审计** | "成本花在哪、有无浪费" | 按 span 聚合 token + 异常检测 | 成本优化 |
| **Diff 调试** | "两次运行结果不同,差异在哪" | 两条 Trace diff | 回归测试 |
| **反事实调试** | "如果这步换种做法会怎样" | 修改某步输入,重跑后续 | 错误归因 |

**1. 回放调试 (Replay Debugging):**

**核心思想**:录制 Agent 运行时的所有 LLM/工具调用 IO,回放时用录制的响应 mock 掉非确定性组件,实现**确定性复现**。

**实现要点:**
```python
# 录制
class Recorder:
    def __init__(self, storage):
        self.storage = storage
    
    def wrap_llm(self, llm):
        original = llm.invoke
        def wrapped(prompt, **kwargs):
            response = original(prompt, **kwargs)
            self.storage.save({
                "prompt": prompt, 
                "response": response,
                "model": llm.model,
                "hash": hash(prompt)
            })
            return response
        llm.invoke = wrapped

# 回放
class Replayer:
    def __init__(self, recording):
        self.recording = recording
    
    def wrap_llm(self, llm):
        def mock_invoke(prompt, **kwargs):
            # 按顺序返回录制的响应,不真正调 LLM
            return self.recording.next_response(prompt)
        llm.invoke = mock_invoke
```

**挑战:**
- 工具副作用 (写库/发邮件) 不能真正重放,需 mock。
- 随机性 (温度采样) 通过 mock LLM 响应消除。
- 录制数据量大,需采样 + 压缩。

**2. 断点调试 (Breakpoint):**

**LangGraph 的 interrupt 机制:**
```python
from langgraph.graph import StateGraph

graph = build_agent_graph()

# 方式1: 在特定节点前暂停
graph.compile(
    interrupt_before=["tool_node"]  # 工具调用前暂停,人工审核
)

# 方式2: 条件断点
def should_break(state):
    if "delete" in state["next_action"].lower():
        return True  # 危险操作前断点
    return False
```

**应用场景:**
- 高风险工具调用前人工审核 (Human-in-the-loop)。
- 开发时逐步检查 state 演化。
- 调试循环:在疑似循环点断点,手动改 state 跳出。

**3. Trace 分析:**

**自动瓶颈检测:**
```python
def analyze_trace(trace):
    spans = flatten(trace)
    
    # 1. 最慢 span
    slowest = max(spans, key=lambda s: s.duration)
    
    # 2. 循环检测:相同 (tool, input_hash) 出现多次
    tool_calls = [(s.name, hash(s.input)) for s in spans if s.kind == "tool"]
    loops = [c for c in Counter(tool_calls).items() if c[1] > 2]
    
    # 3. token 浪费:相同 prompt 重复调用
    llm_calls = [(s.model, hash(s.prompt)) for s in spans if s.kind == "llm"]
    redundant = [c for c in Counter(llm_calls).items() if c[1] > 1]
    
    return {"slowest": slowest, "loops": loops, "redundant": redundant}
```

**Trace 可视化要点:**
- 瀑布图 (Waterfall) 看并行/串行。
- 火焰图 (Flame Graph) 看嵌套深度。
- 甘特图看时序。

**4. Token 审计:**

**成本归因:**
```python
def token_audit(trace):
    audit = {}
    for span in flatten(trace):
        path = span_path(span)  # "Agent.run > LLM.plan > ..."
        cost = span.tokens_prompt * 0.01/1000 + span.tokens_completion * 0.03/1000
        audit[path] = audit.get(path, 0) + cost
    return audit
# 输出: {"Agent.run > LLM.plan": $0.12, "Agent.run > Tool.search > LLM.parse": $0.05}
```

**异常检测:**
- Prompt 突然变长 (可能上下文累积)。
- 同一 prompt 重复调用 (缓存失效)。
- Completion 远超预期 (模型跑飞)。

**面试加分点:**
- 强调"**LLM 的非确定性是调试核心痛点**":传统软件相同输入相同输出,Agent 不是。回放调试通过 mock 消除非确定性,是 Agent 调试的"杀手锏"。
- 提到"**Time-Travel Debugging**":基于录制,可以"回到过去"任意一步,改 state 重跑。这是 Agent 调试的理想形态 (参考 Redux DevTools)。
- 提到"**生产环境调试**":线上不能断点,主要靠 Trace + 日志 + 回放。开发环境用断点。
- 提到"**调试自动化**":Trace 自动分析发现循环/冗余,无需人工翻日志,是生产级 Agent 必备能力。

</details>

---

### Q8: 设计一个 Agent 监控系统,需要监控哪些指标?如何设计告警策略?

<details>
<summary>点击展开答案</summary>

**Agent 监控指标体系 (分层):**

```
┌─────────────────────────────────────────┐
│  业务层 (Business)                       │
│  - 任务成功率 / 用户满意度 / 任务价值     │
├─────────────────────────────────────────┤
│  Agent 层 (Agent-specific)               │
│  - 步骤数 / 循环率 / 工具分布 / 幻觉率   │
├─────────────────────────────────────────┤
│  LLM 层 (Model)                          │
│  - Token 数 / 延迟 / 模型版本 / 缓存率   │
├─────────────────────────────────────────┤
│  工具层 (Tool)                           │
│  - 调用成功率 / 延迟 / 错误分类          │
├─────────────────────────────────────────┤
│  基础设施层 (Infra)                      │
│  - CPU/Memory/网络 / 队列长度            │
└─────────────────────────────────────────┘
```

**核心指标详解:**

| 指标 | 计算方式 | 告警阈值 (示例) | 业务含义 |
|------|---------|---------------|---------|
| **任务成功率** | 成功任务数/总任务数 | <80% (5min 滑窗) | 核心健康度 |
| **任务 P95 延迟** | 任务端到端时延 95 分位 | >60s | 用户体验 |
| **任务 P99 延迟** | 99 分位 | >180s | 长尾体验 |
| **平均步数** | 平均动作步数 | 同比 +30% | Agent 是否退化 (绕路) |
| **循环率** | 出现循环的任务占比 | >2% | Agent 卡死前兆 |
| **Token 成本/任务** | 平均美元成本 | 同比 +30% | 成本失控 |
| **LLM 调用错误率** | LLM 调用失败/总调用 | >1% | 模型服务异常 |
| **工具调用成功率** | 工具成功/工具总调用 | <95% | 工具或参数问题 |
| **工具调用分布熵** | 各工具调用占比的熵 | 熵 <0.5 | 退化为单工具 |
| **幻觉率** | 抽样人工/LLM-Judge | >3% | 模型质量问题 |
| **危险工具调用率** | 高危工具调用占比 | >0.1% | 安全风险 |
| **Prompt 长度 P95** | Prompt token 95 分位 | >80% 上下文窗口 | 上下文溢出风险 |
| **缓存命中率** | 缓存命中/总 LLM 调用 | <20% | 成本优化空间 |

**告警策略设计:**

**1. 阈值告警 (静态):**
```
IF task_success_rate < 0.8 FOR 5min THEN alert(severity=p2)
IF task_p95_latency > 60s FOR 5min THEN alert(severity=p2)
IF tool_error_rate > 0.05 FOR 10min THEN alert(severity=p3)
```
适用:有明确 SLA 的指标。

**2. 同比/环比告警 (动态):**
```
IF cost_per_task > 1.5 * avg(last_7_days) THEN alert  # 成本突增
IF step_count > 1.5 * avg(last_7_days) THEN alert     # 退化
```
适用:无固定阈值,关注异常变化的指标。

**3. 异常检测 (统计/ML):**
- 用 Holt-Winters / Prophet 对时序建模,残差超 3σ 告警。
- 适合周期性强的指标 (如昼夜流量)。

**4. 组合告警 (多条件):**
```
IF error_rate > 5% AND latency_p95 > 60s THEN alert(severity=p1)
# 同时错和慢,通常是系统性故障
```
减少误报。

**5. 告警分级:**
| 级别 | 触发 | 响应 |
|------|------|------|
| P0 | 成功率 <50% 或 模型完全不可用 | 立即拉群,5min 响应 |
| P1 | 成功率 <70% 或 危险工具调用 | 30min 响应 |
| P2 | 成功率 <80% 或 延迟/成本超标 | 2h 响应 |
| P3 | 单工具错误率超标 | 工作日处理 |

**6. 告警去噪:**
- **聚合**:同一指标 5min 内只发一次。
- **关联**:同一根因的多个告警合并 (如 LLM 服务挂导致成功率+工具率同时告警)。
- **抑制**:维护期抑制告警。
- **智能路由**:P0 → 电话,P1 → IM,P2 → 邮件。

**7. 循环检测专项告警:**
```python
def detect_loop(trace, window=3):
    actions = [s.action_signature for s in trace.steps]
    for i in range(len(actions) - window):
        if actions[i:i+window] == actions[i+window:i+2*window]:
            return True  # 连续 window 步重复 → 循环
    return False
```
循环是 Agent 特有的"卡死"模式,必须专项监控,否则会烧光预算。

**面试加分点:**
- 强调"**指标分层下钻**":告警触发后,从业务层 → Agent 层 → LLM/工具层逐层下钻定位根因。
- 提到"**SLI/SLO/SLA**":成功率是 SLI,SLO 是内部目标 (如 95%),SLA 是对外承诺 (如 90% 退款)。监控围绕 SLO 设计。
- 提到"**告警疲劳**":过多告警会让工程师忽视。告警系统本身要监控 (告警数趋势)。
- 提到"**Agent 专属指标 vs 通用指标**":通用 APM 监控不了"循环率""步数""工具分布",这是 Agent 监控平台的差异化价值。

</details>

---

### Q9: 手撕代码 — 实现一个 Agent 可观测性系统,包含 Tracing、Logging、Metrics 和告警,Python 完整实现。

<details>
<summary>点击展开答案</summary>

**完整实现 (约 400 行,可直接运行):**

```python
"""
Agent 可观测性系统 - 最小可用实现
包含: Tracing (Span 树) + Logging (结构化) + Metrics (聚合) + 告警
依赖: 无第三方依赖,纯标准库
"""
import time
import uuid
import json
import threading
import statistics
from collections import defaultdict, deque
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional, Callable
from contextlib import contextmanager


# ============================================================
# 1. Tracing 模块
# ============================================================

class SpanKind(Enum):
    INTERNAL = "internal"
    LLM = "llm"
    TOOL = "tool"
    AGENT = "agent"


class SpanStatus(Enum):
    OK = "ok"
    ERROR = "error"


@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: float
    end_time: Optional[float] = None
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    status: SpanStatus = SpanStatus.OK
    children: list = field(default_factory=list, repr=False)

    @property
    def duration(self) -> float:
        if self.end_time is None:
            return 0.0
        return self.end_time - self.start_time

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, attrs: dict = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attrs or {}
        })

    def end(self):
        self.end_time = time.time()

    def to_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status.value,
        }


class Tracer:
    """线程安全的 Tracer,维护 span 栈和完成的 trace。"""

    def __init__(self, trace_storage: "TraceStorage"):
        self._storage = trace_storage
        self._local = threading.local()

    def _get_stack(self) -> list:
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    @contextmanager
    def start_span(self, name: str, kind: SpanKind = SpanKind.INTERNAL,
                   attributes: dict = None):
        stack = self._get_stack()
        parent_id = stack[-1].span_id if stack else None
        trace_id = stack[0].trace_id if stack else str(uuid.uuid4())

        span = Span(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_id,
            name=name,
            kind=kind,
            start_time=time.time(),
            attributes=attributes or {},
        )
        if stack:
            stack[-1].children.append(span)
        stack.append(span)
        try:
            yield span
        except Exception as e:
            span.status = SpanStatus.ERROR
            span.add_event("exception", {"error": str(e)})
            raise
        finally:
            span.end()
            stack.pop()
            if not stack:  # 根 span 结束,存储整条 trace
                self._storage.save(span)


class TraceStorage:
    """存储完成的 trace,支持查询和分析。"""

    def __init__(self, max_size: int = 10000):
        self._traces = {}  # trace_id -> root_span
        self._lock = threading.Lock()
        self.max_size = max_size

    def save(self, root_span: Span):
        with self._lock:
            if len(self._traces) >= self.max_size:
                # 简单 FIFO 淘汰
                oldest = next(iter(self._traces))
                del self._traces[oldest]
            self._traces[root_span.trace_id] = root_span

    def get(self, trace_id: str) -> Optional[Span]:
        return self._traces.get(trace_id)

    def recent(self, n: int = 100) -> list:
        with self._lock:
            return list(self._traces.values())[-n:]

    def find_loops(self, trace_id: str, window: int = 3) -> list:
        """检测 trace 中是否有循环 (连续重复动作)。"""
        root = self.get(trace_id)
        if not root:
            return []
        actions = []
        def collect(span):
            if span.kind in (SpanKind.TOOL, SpanKind.LLM):
                sig = f"{span.name}:{span.attributes.get('input_hash', '')}"
                actions.append(sig)
            for c in span.children:
                collect(c)
        collect(root)
        loops = []
        for i in range(len(actions) - window):
            if actions[i:i+window] == actions[i+window:i+2*window]:
                loops.append({"start": i, "pattern": actions[i:i+window]})
        return loops


# ============================================================
# 2. Logging 模块
# ============================================================

class StructuredLogger:
    """结构化日志,关联 trace_id/span_id。"""

    def __init__(self, log_file: str = "agent.log"):
        self._file = open(log_file, "a", encoding="utf-8")
        self._lock = threading.Lock()

    def log(self, level: str, message: str, trace_id: str = None,
            span_id: str = None, **kwargs):
        entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "trace_id": trace_id,
            "span_id": span_id,
            **kwargs,
        }
        with self._lock:
            self._file.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
            self._file.flush()

    def info(self, message, **kwargs):
        self.log("INFO", message, **kwargs)

    def error(self, message, **kwargs):
        self.log("ERROR", message, **kwargs)

    def close(self):
        self._file.close()


# ============================================================
# 3. Metrics 模块
# ============================================================

class MetricsCollector:
    """聚合指标收集器:Counter / Histogram / Gauge。"""

    def __init__(self):
        self._counters = defaultdict(float)
        self._histograms = defaultdict(list)
        self._gauges = defaultdict(float)
        self._lock = threading.Lock()

    def increment(self, name: str, value: float = 1, tags: dict = None):
        key = self._key(name, tags)
        with self._lock:
            self._counters[key] += value

    def observe(self, name: str, value: float, tags: dict = None):
        key = self._key(name, tags)
        with self._lock:
            self._histograms[key].append(value)
            if len(self._histograms[key]) > 10000:
                self._histograms[key] = self._histograms[key][-5000:]

    def gauge(self, name: str, value: float, tags: dict = None):
        key = self._key(name, tags)
        with self._lock:
            self._gauges[key] = value

    def percentile(self, name: str, p: float, tags: dict = None) -> float:
        key = self._key(name, tags)
        values = sorted(self._histograms.get(key, []))
        if not values:
            return 0.0
        idx = int(len(values) * p)
        return values[min(idx, len(values)-1)]

    def get_counter(self, name: str, tags: dict = None) -> float:
        return self._counters.get(self._key(name, tags), 0.0)

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {
                    k: {
                        "count": len(v),
                        "p50": statistics.median(v) if v else 0,
                        "p95": sorted(v)[int(len(v)*0.95)] if v else 0,
                        "p99": sorted(v)[int(len(v)*0.99)] if v else 0,
                        "avg": statistics.mean(v) if v else 0,
                    } for k, v in self._histograms.items()
                },
            }

    @staticmethod
    def _key(name: str, tags: dict = None) -> str:
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"


# ============================================================
# 4. 告警模块
# ============================================================

@dataclass
class AlertRule:
    name: str
    metric: str
    condition: str  # "gt", "lt", "gt_ratio"
    threshold: float
    window_seconds: int
    severity: str  # p0/p1/p2/p3
    message: str
    tags: dict = field(default_factory=dict)
    last_fired: float = 0
    cooldown: int = 300  # 5min 冷却

    def evaluate(self, metrics: MetricsCollector) -> Optional[dict]:
        # 滑动窗口实现简化:直接用当前累积值
        value = metrics.get_counter(self.metric, self.tags)
        if self.condition == "gt" and value > self.threshold:
            return self._fire(value)
        if self.condition == "lt" and value < self.threshold:
            return self._fire(value)
        return None

    def _fire(self, value: float) -> Optional[dict]:
        now = time.time()
        if now - self.last_fired < self.cooldown:
            return None  # 冷却中
        self.last_fired = now
        return {
            "alert": self.name,
            "severity": self.severity,
            "metric": self.metric,
            "value": value,
            "threshold": self.threshold,
            "message": self.message,
            "timestamp": now,
        }


class AlertManager:
    """告警管理器:规则评估 + 通知。"""

    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.rules: list[AlertRule] = []
        self.notifiers: list[Callable] = []
        self._history = deque(maxlen=1000)

    def add_rule(self, rule: AlertRule):
        self.rules.append(rule)

    def add_notifier(self, notifier: Callable):
        self.notifiers.append(notifier)

    def check(self):
        """周期性调用,评估所有规则。"""
        for rule in self.rules:
            alert = rule.evaluate(self.metrics)
            if alert:
                self._history.append(alert)
                for notifier in self.notifiers:
                    try:
                        notifier(alert)
                    except Exception as e:
                        print(f"Notifier error: {e}")

    def history(self) -> list:
        return list(self._history)


# ============================================================
# 5. 可观测性门面 - 统一入口
# ============================================================

class Observability:
    """统一门面,集成 Tracing/Logging/Metrics/Alerting。"""

    def __init__(self, service_name: str = "agent"):
        self.service_name = service_name
        self.trace_storage = TraceStorage()
        self.tracer = Tracer(self.trace_storage)
        self.logger = StructuredLogger(f"{service_name}.log")
        self.metrics = MetricsCollector()
        self.alerts = AlertManager(self.metrics)
        self._setup_default_alerts()
        self._current_trace_id = threading.local()

    def _setup_default_alerts(self):
        self.alerts.add_rule(AlertRule(
            name="high_error_rate",
            metric="agent.errors",
            condition="gt",
            threshold=10,
            window_seconds=300,
            severity="p1",
            message="Agent 错误数过高",
        ))
        self.alerts.add_rule(AlertRule(
            name="high_cost",
            metric="agent.cost_usd",
            condition="gt",
            threshold=5.0,
            window_seconds=300,
            severity="p2",
            message="Agent 成本超阈值",
        ))

    @contextmanager
    def trace(self, name: str, kind: SpanKind = SpanKind.AGENT, **attrs):
        with self.tracer.start_span(name, kind, attrs) as span:
            self._current_trace_id.value = span.trace_id
            self.logger.info(f"span start: {name}",
                             trace_id=span.trace_id, span_id=span.span_id)
            try:
                yield span
                self.metrics.increment("agent.tasks.success" if kind == SpanKind.AGENT else "agent.spans.ok",
                                       tags={"kind": kind.value})
            except Exception as e:
                self.metrics.increment("agent.errors",
                                       tags={"kind": kind.value, "error": type(e).__name__})
                self.logger.error(f"span error: {name}: {e}",
                                  trace_id=span.trace_id, span_id=span.span_id)
                raise

    def record_llm_call(self, span: Span, model: str, prompt_tokens: int,
                        completion_tokens: int, latency: float):
        """记录 LLM 调用指标。"""
        span.set_attribute("llm.model", model)
        span.set_attribute("llm.tokens.prompt", prompt_tokens)
        span.set_attribute("llm.tokens.completion", completion_tokens)
        # 成本 (GPT-4 示例价)
        cost = prompt_tokens * 0.01 / 1000 + completion_tokens * 0.03 / 1000
        span.set_attribute("llm.cost_usd", cost)
        # 上报指标
        self.metrics.increment("agent.llm.calls", tags={"model": model})
        self.metrics.observe("agent.llm.latency", latency, tags={"model": model})
        self.metrics.increment("agent.llm.tokens.prompt", prompt_tokens,
                               tags={"model": model})
        self.metrics.increment("agent.llm.tokens.completion", completion_tokens,
                               tags={"model": model})
        self.metrics.increment("agent.cost_usd", cost)

    def record_tool_call(self, span: Span, tool: str, success: bool,
                         latency: float, error: str = None):
        """记录工具调用指标。"""
        span.set_attribute("tool.name", tool)
        span.set_attribute("tool.success", success)
        self.metrics.increment("agent.tool.calls", tags={"tool": tool})
        if success:
            self.metrics.increment("agent.tool.success", tags={"tool": tool})
        else:
            self.metrics.increment("agent.tool.errors",
                                   tags={"tool": tool, "error": error or "unknown"})
        self.metrics.observe("agent.tool.latency", latency, tags={"tool": tool})

    def check_alerts(self):
        self.alerts.check()

    def dashboard(self) -> dict:
        """生成监控快照。"""
        snap = self.metrics.snapshot()
        recent = self.trace_storage.recent(100)
        # 计算衍生指标
        total = sum(v for k, v in snap["counters"].items()
                    if "tasks.success" in k)
        errors = snap["counters"].get("agent.errors", 0)
        return {
            "service": self.service_name,
            "metrics": snap,
            "recent_traces": len(recent),
            "alerts_fired": len(self.alerts.history()),
            "success_count": total,
            "error_count": errors,
        }


# ============================================================
# 6. 示例:用可观测性系统跑一个模拟 Agent
# ============================================================

def demo():
    obs = Observability(service_name="research-agent")

    # 模拟工具
    def fake_search(query: str) -> str:
        time.sleep(0.1)
        return f"results for {query}"

    def fake_llm(prompt: str, model: str = "gpt-4") -> tuple[str, int, int]:
        time.sleep(0.2)
        return f"answer to: {prompt[:30]}", len(prompt) // 4, 50

    # 模拟一次 Agent 任务
    def run_task(task: str):
        with obs.trace("agent.run", SpanKind.AGENT, task=task) as root:
            # Step 1: 规划
            with obs.tracer.start_span("llm.plan", SpanKind.LLM) as plan_span:
                t0 = time.time()
                resp, pt, ct = fake_llm(f"plan: {task}")
                obs.record_llm_call(plan_span, "gpt-4", pt, ct, time.time() - t0)

            # Step 2: 工具调用
            with obs.tracer.start_span("tool.search", SpanKind.TOOL) as tool_span:
                t0 = time.time()
                try:
                    result = fake_search(task)
                    obs.record_tool_call(tool_span, "search", True, time.time() - t0)
                except Exception as e:
                    obs.record_tool_call(tool_span, "search", False,
                                         time.time() - t0, str(e))
                    raise

            # Step 3: 总结
            with obs.tracer.start_span("llm.summarize", SpanKind.LLM) as sum_span:
                t0 = time.time()
                resp, pt, ct = fake_llm(f"summarize: {result}")
                obs.record_llm_call(sum_span, "gpt-4", pt, ct, time.time() - t0)

            root.set_attribute("result", resp)
            return resp

    # 跑 5 个任务
    for i in range(5):
        try:
            run_task(f"research topic {i}")
        except Exception as e:
            obs.logger.error(f"task failed: {e}")

    # 模拟一个失败任务
    try:
        with obs.trace("agent.run", SpanKind.AGENT, task="bad task"):
            with obs.tracer.start_span("tool.fail", SpanKind.TOOL) as s:
                raise RuntimeError("tool broken")
    except RuntimeError:
        pass

    # 检查告警
    obs.check_alerts()

    # 输出监控面板
    print("=" * 60)
    print("Agent Observability Dashboard")
    print("=" * 60)
    dash = obs.dashboard()
    print(json.dumps(dash, indent=2, default=str))

    print("\nAlerts:")
    for a in obs.alerts.history():
        print(f"  [{a['severity']}] {a['alert']}: {a['message']} (value={a['value']:.2f})")

    print("\nRecent trace tree:")
    for root in obs.trace_storage.recent(2):
        def print_tree(span, depth=0):
            print("  " * depth + f"└─ {span.name} [{span.kind.value}] "
                  f"dur={span.duration:.2f}s status={span.status.value}")
            for c in span.children:
                print_tree(c, depth + 1)
        print_tree(root)


if __name__ == "__main__":
    demo()
```

**代码要点解析:**

1. **Tracing**:用线程局部栈维护 span 嵌套关系,根 span 结束时存入 TraceStorage。支持循环检测。
2. **Logging**:结构化 JSON 日志,带 trace_id/span_id,便于关联 trace。
3. **Metrics**:Counter/Histogram/Gauge 三种类型,Histogram 支持 P50/P95/P99 分位计算。
4. **Alerting**:规则引擎 + 冷却机制 + 多通知器,避免告警风暴。
5. **门面模式**:`Observability` 统一入口,业务代码只依赖它,降低耦合。

**面试加分点:**
- 提到线程安全:多线程 Agent (如并行工具调用) 必须用 `threading.local` 隔离 span 栈。
- 提到采样:生产环境全量 trace 贵,需采样 (错误全量 + 成功 1%)。
- 提到 OTel 兼容:生产实现应基于 OpenTelemetry SDK,而非自研。

</details>

---

### Q10: 系统设计题 — 设计一个 Agent 线上监控平台,支持多 Agent、实时告警、Trace 可视化、成本分析。

<details>
<summary>点击展开答案</summary>

**需求拆解:**
- **功能需求**:接入多 Agent、实时监控、Trace 查询可视化、成本分析与归因、告警。
- **非功能需求**:低延迟 (告警 <1min)、高吞吐 (10k tasks/s)、高可用 (99.9%)、可扩展 (新指标/新 Agent 快速接入)、数据保留 (Trace 30 天,指标 1 年)。
- **约束**:支持自托管 (金融客户数据不出域)。

**整体架构:**

```
┌────────────────────────────────────────────────────────────┐
│                     Agent 线上监控平台                       │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ Agent A  │  │ Agent B  │  │ Agent C  │  ... (多 Agent) │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│       │ SDK/OTel    │             │                        │
│       ▼             ▼             ▼                        │
│  ┌──────────────────────────────────┐                      │
│  │     采集层 (Collector)            │  ← OTel Collector    │
│  │  - gRPC/HTTP 接收                 │     负载均衡 + 缓冲  │
│  │  - 采样 (错误全量,成功 10%)       │                      │
│  │  - 脱敏 (PII 过滤)                │                      │
│  └─────────────┬────────────────────┘                      │
│                │                                           │
│       ┌────────┼────────┬─────────────┐                    │
│       ▼        ▼        ▼             ▼                    │
│  ┌────────┐ ┌──────┐ ┌────────┐ ┌──────────┐              │
│  │ Trace  │ │ Log  │ │ Metric │ │  Alert   │              │
│  │ Store  │ │Store │ │ TSDB   │ │  Engine  │              │
│  │(ES/ClickHouse)│ │(Loki) │(VictoriaMetrics│(自研+Prom)  │
│  └───┬────┘ └──┬───┘ └───┬────┘ └─────┬────┘              │
│      │         │         │            │                    │
│      └─────────┴────┬────┴────────────┘                    │
│                     ▼                                      │
│  ┌──────────────────────────────────┐                      │
│  │     查询/可视化层 (API + UI)      │                      │
│  │  - Trace 树形可视化              │                      │
│  │  - 指标 Dashboard (Grafana)       │                      │
│  │  - 成本分析报表                  │                      │
│  │  - 告警事件流                    │                      │
│  └──────────────────────────────────┘                      │
│                                                            │
│  ┌──────────────────────────────────┐                      │
│  │     评估层 (Online Eval)          │  ← 可选              │
│  │  - LLM-as-Judge 线上抽样          │                      │
│  │  - 真实用户反馈采集              │                      │
│  └──────────────────────────────────┘                      │
└────────────────────────────────────────────────────────────┘
```

**核心模块详细设计:**

**1. 采集层 — OTel Collector:**

```
Agent SDK (OTel)  →  OTel Collector  →  多后端导出
                      ├─ trace → ClickHouse
                      ├─ log   → Loki
                      ├─ metric→ VictoriaMetrics
                      └─ alert → Alertmanager
```

**关键决策:**
- 用 OTel 协议 (OTLP) 统一接入,Agent 侧只装 OTel SDK,与后端解耦。
- Collector 做采样 + 脱敏 + 重试,减轻后端压力。
- 采样策略:错误任务全量、成功任务 10%、慢任务 (P99) 全量。

**2. 存储层 — 选型:**

| 数据类型 | 选型 | 理由 |
|---------|------|------|
| Trace | ClickHouse | 列存,高频写 + 复杂查询 (按 trace_id/属性筛选),压缩比高 |
| Log | Loki | 与 Grafana 集成,成本低,日志查询模式简单 |
| Metric | VictoriaMetrics | 兼容 PromQL,高性能,成本低 |
| 告警事件 | PostgreSQL | 关系型,需关联规则/通知/认领 |
| 长期归档 | S3/OSS | 冷数据,Trace 30天后归档 |

**3. Trace 数据模型 (ClickHouse):**

```sql
CREATE TABLE spans (
    trace_id String,
    span_id String,
    parent_span_id String,
    name String,
    kind LowCardinality(String),
    agent_name LowCardinality(String),
    start_time DateTime64(3),
    end_time DateTime64(3),
    duration_ms Float64,
    attributes Map(String, String),
    status LowCardinality(String),
    tokens_prompt UInt32,
    tokens_completion UInt32,
    cost_usd Float64,
    INDEX idx_trace (trace_id) TYPE bloom,
    INDEX idx_agent (agent_name) TYPE set(100),
    INDEX idx_time (start_time) TYPE minmax
) ENGINE = MergeTree 
PARTITION BY toYYYYMM(start_time)
ORDER BY (agent_name, start_time, trace_id);
```

**4. 实时告警引擎:**

```
VictoriaMetrics (Vmalert)  →  Alertmanager  →  通知渠道
        ↑                                       ├─ IM (企微/钉钉)
   PromQL 规则                                 ├─ 邮件
                                               ├─ 电话 (P0)
                                               └─ Webhook (自动拉群)
```

**告警规则示例 (PromQL):**
```promql
# 任务成功率
agent_tasks_success_rate = 
  rate(agent_tasks_success[5m]) / rate(agent_tasks_total[5m])
ALERT LowSuccessRate IF avg_over_time(agent_tasks_success_rate[5m]) < 0.8
  FOR 5m LABELS { severity="p1" }

# 循环检测 (基于 counter)
ALERT LoopDetected IF increase(agent_loops_total[10m]) > 5
  LABELS { severity="p2" }

# 成本突增
ALERT CostSpike IF 
  rate(agent_cost_usd[5m]) > 3 * avg_over_time(rate(agent_cost_usd[5m])[1d:1h])
  LABELS { severity="p2" }
```

**5. 成本分析模块:**

**归因维度:**
- 按 Agent (哪个 Agent 最贵)
- 按模型 (GPT-4 vs GPT-3.5 占比)
- 按任务类型 (哪类任务最贵)
- 按阶段 (规划/工具/反思各占多少)
- 按用户 (TOP 消费用户)

**实现:**
```sql
-- 按阶段成本归因
SELECT 
    agent_name,
    arrayJoin(splitByChar('/', span_path)) as stage,
    sum(cost_usd) as cost,
    sum(cost_usd) / total_cost as ratio
FROM spans
WHERE start_time > now() - INTERVAL 1 DAY
GROUP BY agent_name, stage
ORDER BY cost DESC;

-- 异常成本任务 (TOP 1% 高成本)
SELECT trace_id, agent_name, cost_usd, duration_ms
FROM spans
WHERE cost_usd > quantile(0.99)(cost_usd)
  AND start_time > now() - INTERVAL 1 DAY
ORDER BY cost_usd DESC LIMIT 100;
```

**6. Trace 可视化:**

**前端组件:**
- **树形视图**:展开 span 嵌套,显示耗时、状态、属性。
- **瀑布图**:并行/串行时序,看哪些步骤可并行化。
- **火焰图**:嵌套深度 + 耗时占比。
- **Span 详情**:Prompt/Response/工具 IO 完整展示 (脱敏后)。
- **对比视图**:两条 trace diff,定位回归。

**实现参考**:LangSmith 的 Trace 视图、Jaeger UI。

**7. 多 Agent 接入:**

**Agent 注册中心:**
```json
{
  "agent_name": "research-agent",
  "version": "1.2.0",
  "sla": {"success_rate": 0.9, "p95_latency_ms": 30000},
  "owner": "team-alpha",
  "oncall": "rotation-alpha",
  "alert_routing": {"p0": "#incident", "p1": "#team-alpha-alerts"}
}
```
新 Agent 接入只需注册 + 装 OTel SDK,告警自动路由到对应团队。

**容量估算:**
- 假设 100 个 Agent,每个 100 tasks/min,平均每任务 50 spans。
- Span QPS = 100 * 100 * 50 / 60 ≈ 8.3k spans/s。
- ClickHouse 单节点可扛 100k inserts/s,够用。
- 存储:每 span ~500B,8.3k * 86400 * 30 ≈ 10TB/月,压缩后 ~2TB。

**高可用设计:**
- Collector 无状态,水平扩展。
- ClickHouse 用副本 + 分片集群。
- 告警引擎主备,避免单点。

**面试加分点:**
- 强调"**OTel 是接入标准**":不要自研 SDK,用 OTel 协议,Agent 侧零改动可切换后端。
- 提到"**采样是成本关键**":Trace 全量存储成本爆炸,需智能采样 (错误全量 + 成功采样 + 慢任务全量)。
- 提到"**评估一体化**":监控平台不仅看技术指标,还接入 LLM-as-Judge 做线上质量评估,这是 Agent 监控区别于传统 APM 的核心。
- 提到"**成本可观测性是 Agent 独有需求**":传统 APM 不关心"每次调用多少钱",Agent 监控必须做成本归因,直接影响 ROI。
- 提到"**数据合规**":金融客户要自托管 + 数据加密 + 审计日志,平台需支持私有化部署。

</details>

---

## 核心知识回顾表

| 主题 | 关键点 | 面试高频度 |
|------|--------|-----------|
| Agent 评测挑战 | 长轨迹/副作用/多路径/成本敏感 | ★★★★★ |
| 评测维度 | 完成率/效率/成本/安全/鲁棒性 | ★★★★ |
| 评估方法 | E2E/步骤级/轨迹,组合使用 | ★★★★ |
| 基准测试 | AgentBench/ToolBench/WebArena/SWE-bench/τ-bench | ★★★ |
| LLM-as-Judge | 偏差(位置/冗长/自偏) + 缓解(多裁判/交换/校准) | ★★★★ |
| 可观测性三支柱 | Tracing + Logging + Metrics,通过 TraceID 关联 | ★★★★★ |
| Span 模型 | trace_id/span_id/parent_id,树形嵌套 | ★★★ |
| OTel GenAI 约定 | gen_ai.* 属性,标准化 LLM span | ★★★ |
| 工具选型 | LangSmith(LC生态)/Langfuse(开源)/Phoenix(评估)/OpenLLMetry(OTel) | ★★★★ |
| 调试技术 | 回放(确定性复现)/断点/Trace分析/Token审计 | ★★★ |
| 监控指标 | 业务层/Agent层/LLM层/工具层 四层 | ★★★★ |
| 告警策略 | 阈值/同比/异常检测/分级/去噪 | ★★★ |
| 循环检测 | Agent 卡死前兆,专项监控 | ★★★ |
| 成本归因 | 按Agent/模型/任务/阶段/用户多维归因 | ★★★★ |
| 采样策略 | 错误全量+成功采样+慢任务全量 | ★★★ |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────┐
│  Agent 评测三方法: E2E (结果) / 步骤级 (过程) / 轨迹 (路径)  │
│  评测五维度: 完成率 / 效率 / 成本 / 安全 / 鲁棒性           │
│                                                             │
│  基准测试:                                                  │
│   - AgentBench (综合8环境)  - ToolBench (16k API)          │
│   - WebArena (Web交互)     - SWE-bench (代码修复,最难)     │
│   - GAIA (通用助手)        - τ-bench (策略合规)            │
│                                                             │
│  LLM-as-Judge 偏差: 位置/冗长/自偏/仁慈                     │
│  缓解: 多裁判 / 位置交换 / Rubric / 人工校准               │
│                                                             │
│  可观测性三支柱:                                            │
│   Metrics (有问题) → Tracing (在哪) → Logging (为什么)    │
│   关联键: TraceID + SpanID                                 │
│                                                             │
│  工具选型:                                                  │
│   LangChain生态 → LangSmith                                 │
│   开源自托管 → Langfuse                                     │
│   评估导向   → Phoenix                                      │
│   已有OTel   → OpenLLMetry                                  │
│                                                             │
│  Agent 专属指标:                                            │
│   任务成功率 / 步数 / 循环率 / 工具分布熵                   │
│   Token成本/任务 / 工具调用成功率 / 幻觉率                  │
│                                                             │
│  调试四技: 回放(确定性复现) / 断点 / Trace分析 / Token审计 │
│  循环检测: 连续N步动作重复 → 卡死前兆                       │
│                                                             │
│  告警分级: P0(<50%成功率,电话) / P1 / P2 / P3              │
│  告警去噪: 聚合 / 关联 / 抑制 / 智能路由                   │
│                                                             │
│  采样策略: 错误全量 + 成功采样 + 慢任务全量                 │
│  成本归因: Agent/模型/任务/阶段/用户 多维                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒

1. **"Agent 评测 = 跑基准"是误解**。基准是离线沙盘,生产质量要靠线上 A/B + 真实用户反馈 + LLM-as-Judge 抽样。基准 SOTA ≠ 生产可用。

2. **端到端评估会"鼓励绕路"**。只看结果不看过程,Agent 可能用 50 步完成 3 步的任务,E2E 判成功但效率极差。必须配合轨迹指标。

3. **LLM-as-Judge 不能盲信**。判官 LLM 弱于被评估 LLM 时不可靠;有位置/冗长/自偏等系统性偏差;同一输入多次评判结果不同,需多次平均。

4. **Tracing ≠ Logging**。Trace 强调"因果链路 + 嵌套关系",日志是"离散事件"。把 Trace 当日志用会丢失树形结构,无法定位瓶颈步骤。

5. **Span 必须记录"语义层"而非仅"代码层"**。Agent 的逻辑是 LLM 生成的,两次执行代码路径不同。Span attributes 要记录 Thought/Action/工具名/模型名,而非仅函数名。

6. **全量 Trace 存储成本爆炸**。一次 Agent 任务可能产生 100+ spans,每个 span 含完整 Prompt (KB 级)。10k tasks/day → GB 级/天。必须采样。

7. **告警不分级 = 告警失效**。所有告警都发 IM,工程师会全部静音。必须 P0 电话/P1 IM/P2 邮件分级,且带冷却防风暴。

8. **循环检测是 Agent 独有需求,传统 APM 没有**。Agent 可能"卡在某个 Thought-Action 循环"烧光预算。必须专项监控"连续 N 步动作重复"。

9. **成本归因不是简单的"总 token × 单价"**。要下钻到 Agent/模型/任务类型/阶段/用户,否则找不到优化点。最贵的不一定是模型,可能是某个冗余工具调用。

10. **OTel 是接入标准,不要自研 SDK**。自研 SDK 看似灵活,但与生态工具 (Jaeger/Grafana/Prometheus) 集成成本高。用 OTel 协议,后端可随时切换。

---

## 自测检查清单

### 概念题 (10)

- [ ] 能说出 Agent 评测比传统 ML 难的 5 个原因吗?
- [ ] 能区分端到端/步骤级/轨迹评估,并说出各自的适用场景吗?
- [ ] 能列举 6 个主流 Agent 基准,并说出它们评估什么能力吗?
- [ ] 能说出 LLM-as-Judge 的 5 种偏差和 4 种缓解策略吗?
- [ ] 能解释可观测性三支柱的关系 (Metrics→Tracing→Logging 下钻路径) 吗?
- [ ] 能画出 Span 的数据模型,并解释 trace_id/span_id/parent_id 的作用吗?
- [ ] 能对比 LangSmith/Langfuse/Phoenix/OpenLLMetry,并给出选型决策树吗?
- [ ] 能说出 4 种 Agent 调试技术,以及回放调试如何解决"非确定性"问题吗?
- [ ] 能列举 Agent 监控的 4 层指标体系,以及 8 个核心指标吗?
- [ ] 能解释循环检测的实现原理和为什么它对 Agent 特别重要吗?

### 代码题 (3)

- [ ] 能用 Python 实现一个最小的 Tracer (含 span 嵌套、线程安全、trace 存储) 吗?
- [ ] 能实现一个 MetricsCollector (Counter/Histogram/Gauge + P95/P99 分位) 吗?
- [ ] 能实现一个循环检测函数 (基于 trace 的动作序列,窗口法) 吗?

### 系统设计题 (2)

- [ ] 能画出 Agent 线上监控平台架构 (采集/存储/计算/可视化/告警) 吗?
- [ ] 能设计一个成本分析模块,支持按 Agent/模型/任务/阶段/用户多维归因吗?

---

## 延伸阅读

**论文:**
1. *AgentBench: Evaluating LLMs as Agents* (Liu et al., 2023) — 综合基准设计。
2. *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* (Jimenez et al., 2023) — 真实软件工程基准。
3. *WebArena: A Realistic Web Environment for Building Autonomous Agents* (Zhou et al., 2023) — 可复现 Web 基准。
4. *τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains* (Yao et al., 2024) — 策略合规评估。
5. *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena* (Zheng et al., 2023) — LLM-as-Judge 偏差分析。
6. *Let's Verify Step by Step* (Lightman et al., 2023) — 步骤级 PRM,替代 LLM-as-Judge。

**开源项目:**
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — GenAI span 标准化。
- [Langfuse](https://github.com/langfuse/langfuse) — 开源 LLM 可观测性,自托管首选。
- [Arize Phoenix](https://github.com/Arize-ai/phoenix) — 评估导向可观测性。
- [OpenLLMetry](https://github.com/traceloop/openllmetry) — OTel 原生 LLM 追踪。

**博客:**
- LangSmith 官方文档 — Trace + Evaluation 流水线最佳实践。
- OpenAI Cookbook "Evaluating Agents" — Agent 评估实战。
- Hugging Face "Evaluating LLM Agents" — 开源评估工具链。

---

## 明日预告

**Day 19 — Agent 安全与防御**

明日将进入 Agent 安全领域,这是生产级 Agent 的红线议题:
- **Prompt 注入攻击**:直接注入 / 间接注入 (Indirect Prompt Injection via 工具返回内容) / 注入防御。
- **越权工具调用**:Agent 被诱导执行危险操作 (删库/发邮件/转账),如何用权限沙箱、人工审核 (HITL)、工具白名单防御。
- **数据泄露**:Prompt 中泄露敏感信息 / Agent 通过工具外传数据,如何做数据脱敏、输出审查。
- **对抗性攻击**:对 Agent 观察的扰动 (如网页中藏注入文本),鲁棒性测试。
- **安全对齐**:Constitutional AI / RLHF 在 Agent 安全中的应用。
- **面试重点**:手撕一个 Prompt 注入检测器 + 设计一个 Agent 安全沙箱架构。

安全是 Day18 可观测性的自然延伸 — **没有可观测性就发现不了攻击,没有安全防线可观测性就是事后验尸**。

---

> **学习建议**: Day18 内容偏工程,建议动手跑一遍 Q9 的代码,理解 Tracing/Metrics/Alerting 的协作。Q10 的系统设计题建议画一遍架构图,体会"采集-存储-计算-可视化"四层分离的工程范式。
