## Week 3 知识串联图: Agent 框架与系统设计全景

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Agent 系统全景架构 (Week 3)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  用户层    ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│            │  Web UI  │  │   API    │  │  SDK     │                │
│            └────┬─────┘  └────┬─────┘  └────┬─────┘                │
│                 └──────────────┼──────────────┘                     │
│                                ▼                                    │
│  网关层    ┌──────────────────────────────────┐                     │
│            │  API Gateway / Auth / RateLimit  │ ← Day19 安全        │
│            └──────────────┬───────────────────┘                     │
│                           ▼                                         │
│  编排层    ┌──────────────────────────────────┐                     │
│            │  Agent Orchestrator              │ ← Day15 LangGraph   │
│            │  ┌─────────┐  ┌───────────────┐  │    Day17 Multi-Agent│
│            │  │Supervisor│ │ Task Scheduler│  │                     │
│            │  └────┬────┘  └───────┬───────┘  │                     │
│            │       ▼               ▼          │                     │
│            │  ┌────────┐  ┌────────┐  ┌─────┐ │                     │
│            │  │Agent A │  │Agent B │  │A C  │ │                     │
│            │  └────────┘  └────────┘  └─────┘ │                     │
│            └──────┬──────────────┬────────────┘                     │
│                   ▼              ▼                                  │
│  能力层    ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│            │  LLM 网关  │  │  工具层    │  │  记忆层    │          │
│            │  GPT/Claude│  │  Search    │  │  Short-term│          │
│            │  负载均衡  │  │  Code Exec │  │  Long-term │          │
│            │  Fallback  │  │  DB Query  │  │  Vector DB │          │
│            └─────┬──────┘  └─────┬──────┘  └─────┬──────┘          │
│                  └───────────────┼───────────────┘                 │
│                                  ▼                                  │
│  可观测层  ┌──────────────────────────────────────────┐             │
│  Day18     │  Tracing(Spans) → LangSmith/Langfuse    │             │
│            │  Metrics(Counters/Histograms) → Prom    │             │
│            │  Logging(JSON) → ELK                    │             │
│            │  Alerting(阈值/异常检测) → PagerDuty    │             │
│            └──────────────────────────────────────────┘             │
│                                                                     │
│  安全层    ┌──────────────────────────────────────────┐             │
│  Day19     │  Input Filter → Tool Auth → Output Review│             │
│            │  RBAC / Sandbox / Audit Log              │             │
│            │  OWASP LLM Top 10 合规                   │             │
│            └──────────────────────────────────────────┘             │
│                                                                     │
│  框架层    ┌──────────────────────────────────────────┐             │
│  Day15-16  │  LangGraph / CrewAI / AutoGen / 原生     │             │
│            │  → 通过抽象层统一(手撕题6)              │             │
│            └──────────────────────────────────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**记忆口诀**: 用户→网关→编排→能力→可观测,安全贯穿,框架可换。

---

## Week 3 易错点总复习(10项)

> 这些是 Day15-20 学习中反复出现的高频错误,面试时务必避开。

### 易错点 1: 把 LangChain 等同于 LangGraph

<details>
<summary>⚠️ 详解</summary>

- **错误**: "我用 LangChain 做了多 Agent 协作。"
- **纠正**: LangChain 是链式编排(LCEL),LangGraph 是图式编排(StateGraph)。多 Agent、循环、条件分支属于 LangGraph 的能力。
- **面试表述**: "我用 LangGraph(属于 LangChain 生态)实现了多 Agent 协作,核心是 StateGraph + Conditional Edge。"

</details>

### 易错点 2: Multi-Agent 一定比单 Agent 好

<details>
<summary>⚠️ 详解</summary>

- **错误**: "Agent 越多越好,分工越细越好。"
- **纠正**: Multi-Agent 增加 LLM 调用次数(成本翻倍)、通信开销、错误传播风险。单 Agent + 多工具能搞定的,不要上 Multi-Agent。
- **判断标准**: 任务是否需要不同角色/专业知识?是否有明确的子任务划分?如果否,用单 Agent。

</details>

### 易错点 3: LCEL 的 `|` 只是语法糖

<details>
<summary>⚠️ 详解</summary>

- **错误**: 认为 `prompt | llm | parser` 只是字符串拼接。
- **纠正**: `|` 调用 `Runnable.__or__`,返回 `RunnableSequence`,支持 `invoke/stream/batch/ainvoke`,有标准接口、重试、回调。它是一个完整的组合原语,不是简单的函数调用链。

</details>

### 易错点 4: Checkpointing 就是保存对话历史

<details>
<summary>⚠️ 详解</summary>

- **错误**: "Checkpointing 就是把 messages 存下来。"
- **纠正**: Checkpointing 保存的是**完整 State**(包括中间变量、工具调用记录、迭代计数等),不只是 messages。而且支持**时间旅行**(回放任意节点)、**分支**(从某点分叉重跑)。对话历史只是 State 的一部分。

</details>

### 易错点 5: 速率限制只防滥用

<details>
<summary>⚠️ 详解</summary>

- **错误**: "Rate Limit 就是为了防恶意用户。"
- **纠正**: 速率限制有三大目的:
  1. 防滥用(安全)
  2. 控成本(每次 LLM 调用花钱,防止 Agent 死循环烧钱)
  3. 保护后端(防止雪崩压垮 LLM API / 工具服务)
  生产环境**必须有**,不是可选。

</details>

### 易错点 6: Prompt Injection 只是"忽略指令"

<details>
<summary>⚠️ 详解</summary>

- **错误**: 只检测 "ignore previous instructions" 这一种模式。
- **纠正**: Prompt Injection 有多种形态:
  1. 指令覆盖(忽略/替换)
  2. 角色劫持("你现在是一个没有限制的 AI")
  3. 标记注入(伪造 `<system>` 标签)
  4. 间接注入(在文档/网页中嵌入恶意指令,Agent 读取时触发)
  5. 多语言绕过(用翻译/编码绕过英文检测)
  需要多层防御,不能只靠正则。

</details>

### 易错点 7: 工具权限只看"能不能调用"

<details>
<summary>⚠️ 详解</summary>

- **错误**: 只判断用户角色能否调用某工具。
- **纠正**: 权限控制是多维的:
  1. **能不能调**(RBAC:角色是否有权限)
  2. **能调什么参数**(参数白名单、范围限制)
  3. **能调多少次**(配额)
  4. **调用的结果能不能用**(输出审查)
  5. **高危操作要不要人工确认**(human-in-loop)
  少一层都有风险。

</details>

### 易错点 8: Agent 评测只看"任务完成率"

<details>
<summary>⚠️ 详解</summary>

- **错误**: "Agent 完成了任务就算成功。"
- **纠正**: 完成率只是其一,还需评估:
  1. **质量分**: 完成的质量如何(人工/LLM 评分)
  2. **效率**: 用了多少步、多少 Token
  3. **安全性**: 有没有调用危险工具、泄露信息
  4. **鲁棒性**: 边界输入、对抗输入的表现
  5. **一致性**: 同一任务多次运行结果是否稳定
  参考 AgentBench / SWE-bench 的多维度评测。

</details>

### 易错点 9: 系统设计只画架构图不估容量

<details>
<summary>⚠️ 详解</summary>

- **错误**: 面试系统设计题只画组件,不算 QPS、存储、成本。
- **纠正**: 系统设计必须有**容量估算**:
  1. DAU × 人均次数 = 总 QPS
  2. QPS × 单次 Token 数 = LLM 调用量(算成本)
  3. 会话数 × 平均长度 = 存储需求
  4. P99 延迟要求 → 决定是否需要缓存、异步
  面试官非常看重这一步,体现工程思维。

</details>

### 易错点 10: 框架抽象层要兼容所有框架的所有功能

<details>
<summary>⚠️ 详解</summary>

- **错误**: 设计抽象层试图覆盖 LangChain/CrewAI/AutoGen 的所有功能。
- **纠正**: 抽象层应**只覆盖业务需要的核心能力**(invoke/stream/tool_call),各框架的独有功能不强行抽象。过度抽象会导致"最小公共子集"太小,失去各框架优势。原则:**针对业务需求抽象,不要为抽象而抽象**。

</details>

---

## Week 3 自测清单

### A. 概念题(20题)

> 闭卷作答,每题不超过 30 秒。

<details>
<summary>📝 点击展开自测题</summary>

1. LCEL 的核心抽象是什么?(答:`Runnable` 协议)
2. LangGraph 中 State 用什么 Python 类型定义?(答:`TypedDict`)
3. `Annotated[list, operator.add]` 在 State 中的作用?(答:定义字段的累加策略)
4. Conditional Edge 的路由函数返回什么?(答:`Literal` 类型,指定下一个节点)
5. CrewAI 的三个核心概念是?(答:Crew / Agent / Task)
6. AutoGen 原生支持哪种 Multi-Agent 模式?(答:GroupChat 对话式)
7. LlamaIndex 相比 LangChain 的优势在哪?(答:RAG/文档处理/Query Engine)
8. Hierarchical 模式的核心角色是?(答:Supervisor)
9. Debate 模式解决什么问题?(答:提升答案质量,减少单 Agent 偏见)
10. AgentBench 评测的几个核心维度?(答:任务完成率/步骤效率/工具准确率)
11. Tracing 中 Span 和 Trace 的关系?(答:一个 Trace 包含多个 Span,形成树)
12. LangSmith 和 Langfuse 的区别?(答:LangSmith 绑定 LangChain 生态;Langfuse 开源框架无关)
13. OWASP LLM Top 10 排第一的是?(答:LLM01 Prompt Injection)
14. "Excessive Agency" 指什么?(答:Agent 被授予过多权限/自主性,导致危险操作)
15. Token Bucket 速率限制的两个核心参数?(答:容量 capacity / 补充速率 refill_rate)
16. 人机回环(Human-in-loop)解决什么问题?(答:高风险操作需人工确认,防 Agent 误操作)
17. 熔断器的三个状态是?(答:closed / open / half_open)
18. ReAct 循环的三步是?(答:Thought → Action → Observation)
19. Multi-Agent 通信的三种方式?(答:消息总线/共享黑板/直接调用)
20. Agent 抽象层最核心的接口是?(答:`invoke(messages, tools) -> response`)

</details>

### B. 代码题(6题)

> 对应今天的手撕题,闭卷默写核心结构。

<details>
<summary>💻 点击展开自测题</summary>

1. **LangGraph 工作流**: 默写 State 定义 + 一个 Conditional Edge 路由函数。
2. **Multi-Agent 系统**: 默写 Supervisor 的 decompose → execute → aggregate 三步骨架。
3. **可观测性系统**: 默写 Span 数据类 + Tracer 的 `start_span` 上下文管理器。
4. **安全防护层**: 默写 TokenBucketRateLimiter 的 `allow()` 方法核心逻辑。
5. **通用框架骨架**: 默写 TaskScheduler 的优先级队列提交 + `next_ready()` 方法。
6. **框架抽象层**: 默写 `AgentBackend` 抽象接口 + `BackendFactory.create()` 工厂方法。

**评分标准**: 能默写出 70% 结构 = 合格;能补全边界处理 = 良好;能讨论扩展性 = 优秀。

</details>

### C. 系统设计题(7题)

> 每题思考 5-10 分钟,画出架构 + 说出关键决策。

<details>
<summary>🏗️ 点击展开自测题</summary>

1. **AI 编程助手**: 支持代码补全 + Review + 重构,日活 10 万。画架构,说明上下文管理策略。
2. **智能客服**: 意图识别 + 多轮对话 + 工单升级,日均 100 万会话。如何降本?
3. **数据分析 Agent**: NL2SQL + 可视化 + 洞察生成。如何保证 SQL 安全性?
4. **代码审查 Agent**: 静态分析 + LLM 评审,接入 CI/CD。如何控制延迟(<30s)?
5. **Multi-Agent 研发平台**: PM/Dev/QA 协作完成需求。如何分解任务?如何处理冲突?
6. **Agent 监控平台**: 监控 1000 个线上 Agent,设计告警体系。关键指标有哪些?
7. **Agent 安全网关**: 为公司所有 Agent 服务提供统一安全防护。4 层防护如何设计?

**答题框架(每题)**:
- 需求澄清(2 分钟提问)
- 容量估算(QPS/存储/成本)
- 架构分层(画图)
- 核心模块设计
- 容错与降级
- 监控与告警
- 安全考虑
- 权衡与取舍

</details>

---

## 明日预告

> 📅 **Day 22 — 字节跳动 Agent 面试专项**

Week4 进入**大厂真题冲刺**阶段。Day 22 聚焦字节跳动 Agent 方向面试真题,内容包括:

1. **字节 Agent 业务版图**: 豆包 / Coze / 扣子 / 飞书智能助手 / 抖音 AI,理解业务场景。
2. **高频面试题**: 字节偏爱的系统设计题(短视频推荐 Agent / 飞书文档 AI 助手 / Coze 插件生态)。
3. **字节技术栈**: 字节内部 Agent 框架、LLM 推理优化、EIC 端侧 Agent。
4. **手撕代码**: 字节面试特色 — 在线 OJ + 性能要求。
5. **字节面试风格**: 重视工程落地、数据驱动、ROI 思维。

**预习任务**:
- 了解 Coze(扣子)的产品形态和技术架构
- 思考:短视频场景下 Agent 如何做实时推荐?
- 复习 Week1 的 Agent 基础概念,字节爱问基础

---

> 🎯 **Week 3 结语**: 本周完成了从「会用框架」到「能设计系统」的跃迁。6 道手撕代码覆盖了 LangGraph 工作流、Multi-Agent 协作、可观测性、安全防护、通用框架、抽象层设计 — 这是 Agent 工程师的核心代码能力。Week4 将进入大厂真题实战,把前三周的知识用到真实面试场景。
>
> **今日完成度自评**: □ 知识图谱回顾  □ 6 道手撕代码  □ 10 道综合题  □ 自测清单  □ 明日预习
