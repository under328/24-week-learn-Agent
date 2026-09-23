## 核心知识回顾表

| 知识点 | 核心内容 | 关键数字/公式 | 面试一句话总结 |
|--------|----------|---------------|----------------|
| 单 Agent 局限 | Context 膨胀、角色冲突、决策树不可扩展、无专业分工 | 工具>15、Context>16K、步骤>8 时考虑拆分 | "单 Agent 是通才,Multi-Agent 是专业分工" |
| 五大协作模式 | Hierarchical / Sequential / Parallel / Debate / Network | Debate 2 轮可让数学准确率 53%→87% | "拓扑决定控制流,场景决定拓扑" |
| Supervisor 模式 | 主控分解+调度+聚合 | 子任务数 2-4 个最佳 | "Supervisor 是大脑,Worker 是器官" |
| 通信机制 | 直接调用/消息队列/黑板/共享状态 | LangGraph 用共享状态 | "耦合度 vs 灵活性的权衡" |
| MetaGPT SOP | 结构化产出+显式流程+共享环境 | Token 成本降 30-50% | "用流程约束弥补 LLM 不可靠" |
| AutoGen GroupChat | 群聊+Speaker Selection | 4 种策略:auto/manual/random/round_robin | "自由对话+发言者调度" |
| 五大挑战 | 一致性/死锁/成本/调试/级联失败 | 成本公式: Σ(次数×token×单价) | "分布式问题+LLM 不确定性" |
| 角色设计四原则 | 单一职责/最小权限/冲突升级/多维终止 | max_rounds + 收敛检测 | "Agent 角色设计=组织设计" |
| 模型分级 | Supervisor 强模型,Worker 便宜模型 | 成本可降 70% | "强模型做决策,便宜模型做执行" |
| 终止条件 | 任务完成+轮次+预算+超时+收敛+人工 | 6 个维度 | "无终止条件的 Multi-Agent 必死循环" |

---

## 面试速记卡

> **使用方法**: 遮住右侧,看左侧关键词,口述完整回答。每张卡 30 秒内说完。

| # | 关键词 | 速记口诀 |
|---|--------|----------|
| 1 | 单 Agent 局限 | "膨胀、冲突、不扩展、不专业" → Context 膨胀 + 角色冲突 + 决策树不扩展 + 无专业分工 |
| 2 | 五大模式 | "层、串、并、辩、网" → Hierarchical/Sequential/Parallel/Debate/Network |
| 3 | Supervisor | "分解→分层→并行→聚合" + 冲突时 Judge 仲裁 + max_rounds 防死循环 |
| 4 | 通信机制 | "直调、队列、黑板、共享态" → 耦合度递减,LangGraph 用共享状态 |
| 5 | MetaGPT SOP | "结构产出+显式流程+共享环境" → PM→Arch→Dev→QA 流水线 |
| 6 | AutoGen GroupChat | "群聊+选人" → auto/manual/random/round_robin + max_round + TERMINATE |
| 7 | 五大挑战 | "一、死、钱、调、联" → 一致性、死锁、成本、调试、级联失败 |
| 8 | 挑战应对 | "共识+DAG+分级+Trace+熔断" → 对应五大挑战 |
| 9 | 角色四原则 | "单一职责、最小权限、冲突升级、多维终止" |
| 10 | 模型分级 | "强模型做决策(PM/Supervisor/Judge),便宜模型做执行(Worker)" |
| 11 | 成本公式 | "Σ 调用次数 × (in_token×in价 + out_token×out价) × 模型倍率" |
| 12 | 终止六维 | "完成、轮次、预算、超时、收敛、人工" |

---

## 易错点提醒(10 个)

1. **"Multi-Agent 一定比单 Agent 好"** —— 错!任务简单时单 Agent 更快更便宜。Multi-Agent 有协调开销(消息序列化、状态同步、Agent 间往返),当分工收益 < 协调成本时,单 Agent 更优。经验阈值:工具>15、Context>16K、步骤>8 才考虑拆分。

2. **"AutoGen GroupChat 的 speaker_selection_method='auto' 是最优的"** —— 不一定。`auto` 每轮多一次 LLM 调用(成本+延迟),且可能选错。对流程明确的任务,`round_robin` 或自定义函数更可控、更便宜。

3. **"Supervisor 用最便宜模型就行"** —— 错!Supervisor 的任务分解和结果聚合质量直接决定整体上限,是"将帅"。Supervisor 和 Judge 应用强模型(GPT-4o/Claude Opus),Worker 用便宜模型。这是"模型分级"的核心。

4. **"Debate 模式 Agent 越多越好"** —— 错!研究表明 2-3 个 Agent 的 Debate 效果最好,超过 5 个反而下降(信息过载、达成共识困难、成本爆炸)。Du et al. 论文:2 Agent × 2 轮已达最佳性价比。

5. **"Agent 之间用自然语言通信就够了"** —— 不够。纯自然语言通信容易信息丢失、格式不稳。工业实践要求 Agent 间用**结构化 JSON** 通信,每个 Agent 的输出有 Schema 校验,不合规则重试。这是 MetaGPT SOP 的核心洞察。

6. **"max_round 设大一点更安全"** —— 错!max_round 过大会导致死循环时成本爆炸。正确做法:max_round 设保守值(如 3-5),配合"收敛检测"(连续 N 轮相似度 > 阈值则提前终止)和"满意度评分"(LLM 打分 > 7/10 即停)。

7. **"共享状态不需要 Reducer"** —— 错!LangGraph 中并行节点写同一字段时,若无 Reducer 会互相覆盖。必须用 `Annotated[list, operator.add]` 等声明合并策略,否则数据丢失。这是 LangGraph 最常见的 bug。

8. **"冲突处理就是投票"** —— 错!技术决策不适合民主投票(可能选出妥协方案)。正确做法:事实冲突用外部工具锚定(查文档/API);风格冲突用 Judge 仲裁;安全冲突一票否决(升级人工)。

9. **"Multi-Agent 不需要 Tracing"** —— 错!Multi-Agent 比单 Agent 更需要全链路 Tracing。因为错误会"蝴蝶效应"——一个 Agent 的小错误被下游放大,不 Trace 根本不知道错在哪。必须用 LangSmith/Langfuse 记录每次 LLM 调用的 input/output/latency/cost。

10. **"Agent 角色定义越详细越好"** —— 不一定。System Prompt 过长会稀释注意力,反而降低输出质量。经验:每个 Agent 的 system prompt 控制在 300-500 tokens,聚焦"身份+目标+约束+工具",不要写小说。MetaGPT 的 prompt 都很精炼。

---

## 自测检查清单

### 概念题(10 题,每题口述 < 1 分钟)

- [ ] 1. 单 Agent 的四大局限是什么?何时该拆为 Multi-Agent?
- [ ] 2. 画出五大协作模式的拓扑图,各举一个适用场景。
- [ ] 3. Supervisor 模式的任务分解有哪三种策略?各有什么优劣?
- [ ] 4. LangGraph 的共享状态和 AutoGen 的 GroupChat 在通信机制上的本质区别?
- [ ] 5. MetaGPT SOP 的三个关键机制是什么?为什么比自由协作更有效?
- [ ] 6. AutoGen 的 speaker_selection_method 有哪几种?何时用自定义函数?
- [ ] 7. Multi-Agent 的五大挑战分别用什么机制应对?
- [ ] 8. Agent 角色设计的四大原则是什么?各举一个反模式。
- [ ] 9. 模型分级策略:Supervisor/Worker/Judge 分别该用什么档次的模型?为什么?
- [ ] 10. 终止条件的六个维度是什么?为什么不能只靠"任务完成"判断?

### 代码题(3 题)

- [ ] 11. 手写一个简化版 Supervisor(不依赖框架),实现任务分解 + 并行执行 + 聚合(不要求 LLM 真实调用,可 mock)。
- [ ] 12. 实现 `detect_loop(history, threshold=0.9, window=3)` 函数,检测 Agent 是否陷入循环。
- [ ] 13. 用 LangGraph 的 StateGraph + Send API 实现一个 Parallel 模式:一个 Fan-out 节点分发 3 个 Worker,一个 Fan-in 节点聚合结果(Reducer 用 `operator.add`)。

### 系统设计题(2 题)

- [ ] 14. 设计一个"学术论文撰写 Multi-Agent 系统":文献调研 Agent + 实验设计 Agent + 写作 Agent + 审稿 Agent。要求支持多轮修改闭环。画出架构图,定义状态 Schema,说明 SOP 流程和终止条件。
- [ ] 15. 设计一个"客服 Multi-Agent 系统":路由 Agent + 订单查询 Agent + 退换货 Agent + FAQ Agent + 升级人工 Agent。要求:90% 问题自动解决,平均响应 < 10s。重点讨论路由策略、降级方案、成本控制。

---

## 延伸阅读

**论文(按优先级)**:
1. MetaGPT: Meta Programming for Multi-Agent Collaborative Framework (Hong et al., 2023, ICLR 2024) —— SOP 思想的奠基论文,必读。
2. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation (Wu et al., 2023, Microsoft) —— GroupChat 机制的来源。
3. Improving Factuality and Reasoning in Language Models through Multiagent Debate (Du et al., 2023, MIT) —— Debate 模式的实证研究。
4. AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors (Chen et al., 2023) —— 网络式协作与涌现行为。
5. CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society (Li et al., 2023) —— Role-Playing Inception Prompting。
6. Cooperative Language Agents (CoALA survey, Sumers et al., 2023) —— Agent 协作的统一框架综述。

**框架文档**:
- LangGraph Multi-Agent 官方教程: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/multi-agent-collaboration/
- AutoGen 官方文档: https://microsoft.github.io/autogen/
- CrewAI 官方文档: https://docs.crewai.com/
- MetaGPT GitHub: https://github.com/FoundationAgents/MetaGPT

**博客与实战**:
- Lilian Weng "LLM Powered Autonomous Agents"(2023) —— Agent 综述经典。
- Andrew Ng "Agentic Design Patterns"(2024) —— 四种 Agent 设计模式(含 Multi-Agent)。
- LangChain Blog "Multi-Agent Collaboration with LangGraph" —— 工程实践向。

**开源项目(建议 star + 跑通 demo)**:
- MetaGPT: 跑通"软件公司"demo,观察 SOP 流程。
- AutoGen: 跑通 GroupChat demo,改 speaker_selection_method 对比效果。
- ChatDev: MetaGPT 思想的轻量实现,代码量小,易读。

---

## 明日预告: Day 18 — Agent 评测与可观测性

Day17 我们解决了"多个 Agent 如何协作"的问题,但留下了一个关键问题:**如何知道协作的结果是好的? 如何定位协作过程中的错误?** 这就是 Day18 的主题——Agent 评测与可观测性。

预告核心内容:
- **Agent 评测**: 任务成功率、轨迹质量、工具调用准确率、成本效率的指标体系;如何做 Agent 的"单元测试"和"集成测试";AgentBench、WebArena、SWE-bench 等基准。
- **可观测性**: 全链路 Tracing(LangSmith/Langfuse/Phoenix)、Metrics(延迟/Token/成本/成功率)、Logging(结构化日志)、Replay(从 Checkpoint 重放)。
- **调试技巧**: LLM 输出不稳定的归因方法、Prompt 回归测试、A/B 测试。
- **生产监控**: 在线指标告警、降级策略、SLA 保障。

> **思考题(明日开场用)**: 你的 Multi-Agent 系统上线后,用户反馈"结果时好时坏",但你不知道是哪个 Agent 的哪次调用出问题。你会怎么设计可观测性方案来定位根因?

---

> **今日学习建议**: Q9 的手撕代码一定要在本地跑通(可 mock LLM),Q10 的系统设计一定要画出完整架构图并口述一遍。这两个是 Day17 的"硬核输出",面试时大概率被要求现场写或画。
