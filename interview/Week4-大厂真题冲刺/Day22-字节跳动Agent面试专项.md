# Day 22 — 字节跳动 Agent 面试专项

> **学习目标**: 掌握字节跳动(抖音/飞书/豆包团队)Agent 岗位面试的核心考点、高频题型与答题套路,能在 60 分钟内完成一道字节风格的 Agent 系统设计题。
>
> **面试定位**: 字节跳动的 Agent 岗位主要分布在三个团队 ——
> - **豆包 / Doubao**: 偏 LLM 应用、对话 Agent、Function Calling、模型评测
> - **飞书 AI 助手**: 偏 ToB 场景、多 Agent 协作、工作流编排、企业知识库 RAG
> - **抖音 / TikTok**: 偏多模态 Agent、推荐+Agent、内容理解、视频生成 Agent
>
> 字节面试特点是 **节奏快、追问狠、爱考成本与工程落地、必考手撕代码(尤其是流式)**。一面通常 2-3 道八股 + 1 道系统设计 + 1 道代码,二面追问深度,三面看综合判断与业务理解。

---

## 今日知识图谱

```
字节跳动 Agent 面试考点树
├── 1. 基础概念 (字节爱考底层原理)
│   ├── Function Calling vs ReAct vs Plan-and-Execute
│   ├── Agent 循环机制 (Thought-Action-Observation)
│   ├── 上下文窗口管理 (长对话压缩、Memory)
│   └── 多 Agent 协作模式 (Manager-Worker / Debate / Voting)
│
├── 2. 系统设计 (字节面试核心战场)
│   ├── 豆包 Agent 架构 (对话 + 工具 + 知识库)
│   ├── 飞书智能助手 (多场景 Agent 编排)
│   ├── 抖音多模态 Agent (图/视频/文理解)
│   └── 成本与延迟优化 (Token 优化、模型路由、缓存)
│
├── 3. RAG 优化 (字节高频追问)
│   ├── 召回率提升 (混合检索、Query 改写、Rerank)
│   ├── 排序优化 (Cross-Encoder、LLM Rerank)
│   ├── 知识库构建 (分块策略、元数据、增量更新)
│   └── 评测体系 (召回率/准确率/相关性/时延)
│
├── 4. 工程能力 (字节必考)
│   ├── 流式输出 (SSE、WebSocket、Token 级流式)
│   ├── 工具调用流式渲染 (部分 JSON 解析)
│   ├── 死循环检测与恢复 (超时、步数上限、状态机)
│   └── 可观测性 (Trace、日志、指标、回放)
│
├── 5. 评估方法论 (字节重视)
│   ├── 离线评测 (LLM-as-Judge、人工标注、回归集)
│   ├── 在线 A/B (北极星指标、Guardrail 指标)
│   ├── Agent 专项评测 (任务完成率、工具调用准确率、步数)
│   └── Bad Case 治理 (归因、聚类、修复闭环)
│
└── 6. 手撕代码 (字节面试特色)
    ├── 流式 Agent (SSE + 工具调用 + 前端渲染)
    ├── Agent 循环主逻辑 (含死循环检测)
    ├── 工具调用 JSON 解析 (容错解析)
    └── 并发工具调用 (asyncio.gather)
```

---

## 面试题

### Q1: 字节面试风格 — 字节 Agent 岗位偏好什么样的人才? 面试流程和考察重点是什么?

<details>
<summary>查看答案</summary>

**字节 Agent 岗位的人才画像**:

字节跳动对 Agent 岗位的候选人偏好可以总结为 **"工程能力强 + 业务理解深 + 有自驱力"**:

1. **工程落地能力优先**: 字节非常看重"能不能把东西做出来"。面试官会追问细节 —— 不是问你"知不知道 ReAct",而是问"你在实际项目里怎么处理工具调用失败? 重试几次? 退避策略?"。
2. **成本意识**: 字节是国内最早关注 Token 成本的大厂之一(豆包的定价就是行业最低)。面试官特别爱问"如何降低 50% 的 Token 消耗",这是字节的灵魂考题。
3. **数据敏感度**: 字节是数据驱动到极致的公司。Agent 评估、A/B 实验、Bad Case 归因,面试官会问得很细。
4. **快速学习能力**: 字节技术栈变化快(从 GPT 到豆包、从 LangChain 到自研 Eino),需要候选人能快速跟上。
5. **业务理解**: 字节不喜欢纯技术派,会问"你觉得豆包的 Agent 在抖音场景下能怎么用?"

**面试流程(典型 4 轮)**:

| 轮次 | 面试官 | 时长 | 考察重点 |
|------|--------|------|----------|
| 一面 | 同级工程师 | 60-75 min | 八股(2-3道) + 代码(1道) + 简单系统设计 |
| 二面 | 资深工程师/Tech Lead | 60-90 min | 深度追问 + 完整系统设计 + 代码 |
| 三面 | 团队负责人 | 45-60 min | 综合判断 + 业务理解 + 职业规划 |
| 四面 | HRBP / 加面 | 30-45 min | 价值观 + 稳定性 + 薪资 |

**字节面试的 4 个"灵魂拷问"风格**:

1. **"为什么不是 X 方案?"**: 你说用 RAG,他会问"为什么不用微调?"; 你说用 ReAct,他会问"为什么不用 Plan-and-Execute?"
2. **"线上出问题了怎么办?"**: 给你一个线上故障场景,问你排查思路、止血方案、根因分析、预防措施。
3. **"数据呢?"**: 你说你的方案好,他会问"怎么证明? 指标是什么? A/B 实验怎么设计?"
4. **"成本呢?"**: 任何方案都要算成本,Token 数、QPS、机器数、月度费用。

**字节 vs 其他大厂的面试差异**:

| 维度 | 字节跳动 | 阿里 | 腾讯 |
|------|----------|------|------|
| 代码题难度 | 中-高(必考流式) | 中 | 中 |
| 系统设计深度 | 深(必问成本) | 深(必问稳定性) | 中(偏业务) |
| 追问风格 | 连环追问、压力面 | 启发式、引导式 | 聊天式 |
| 业务理解权重 | 高 | 中 | 高 |
| 英语要求 | 中(看团队) | 低 | 中 |
| 面试节奏 | 快、紧凑 | 中 | 中 |

**备考建议**:
- 把豆包、飞书 AI 助手、剪映 AI 都用一遍,记下交互细节,面试时会问"你用过豆包吗? 你觉得它有什么问题?"
- 准备 2-3 个完整的 Agent 项目,能画出架构图、说出数据指标、讲清踩过的坑
- 代码题重点练: 流式输出、asyncio 并发、JSON 容错解析、状态机
- 系统设计准备 3 套模板: 对话 Agent、多模态 Agent、企业知识库 Agent

</details>

---

### Q2: 设计豆包(或飞书 AI 助手)的 Agent 系统 — 字节经典系统设计题,完整解答

<details>
<summary>查看答案</summary>

**题目**: 请设计豆包的 Agent 系统,支持多轮对话、工具调用、知识库问答、联网搜索,日活 5000 万,QPS 峰值 5 万。

**一、需求澄清(面试官互动环节)**

| 维度 | 问题 | 假设答案 |
|------|------|----------|
| 功能 | 需要支持哪些能力? | 多轮对话、Function Calling、知识库 RAG、联网搜索、多模态(图片) |
| 用户 | 用户规模? | DAU 5000 万,QPS 峰值 5 万 |
| 时延 | 首 Token 延迟要求? | P95 < 1.5s(首 Token),完整回复 P95 < 8s |
| 成本 | 单次对话成本目标? | < ¥0.03/次 |
| 可用性 | SLA? | 99.9% |
| 模型 | 用自研还是第三方? | 自研豆包模型为主,关键场景兜底用更强模型 |

**二、顶层架构**

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│   豆包 App / 飞书 / 网页 / 开放平台 SDK                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ SSE / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                    API 网关 (ByteGateway)                    │
│   鉴权 / 限流 / 灰度 / 日志 / 计费                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Agent 编排层 (核心)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 对话管理 │  │ 工具路由 │  │ 意图识别 │  │ Memory   │    │
│  │ Dialog   │→ │ Tool     │→ │ Intent   │  │ Manager  │    │
│  │ Manager  │  │ Router   │  │ Detector │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
│       │              │             │              │          │
│       └──────────────┴─────────────┴──────────────┘          │
│                          │                                   │
│              ┌───────────▼───────────┐                       │
│              │  Plan & Execute Engine│                       │
│              │  (ReAct + Plan 混合)  │                       │
│              └───────────┬───────────┘                       │
└──────────────────────────┼───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
│  模型服务层   │  │  工具服务层   │  │  知识服务层   │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │豆包-Lite  │ │  │ │ 搜索 API  │ │  │ │ 向量库    │ │
│ │豆包-Pro   │ │  │ │ 天气 API  │ │  │ │ (自研)    │ │
│ │兜底模型   │ │  │ │ 代码执行  │ │  │ │ ES        │ │
│ └───────────┘ │  │ │ 日历/邮件 │ │  │ │ Rerank    │ │
└───────────────┘  │ └───────────┘ │  └───────────┘ │
                   └───────────────┘  └───────────────┘
```

**三、核心模块详解**

**1. Agent 编排层 —— 混合 ReAct + Plan-and-Execute**

纯 ReAct 的问题: 每一步都调 LLM,Token 消耗大、延迟高。纯 Plan-and-Execute 的问题: 计划容易出错,执行时无法自适应。
豆包采用 **混合策略**:
- 简单任务(1-2 步)直接 ReAct,快
- 复杂任务(3+ 步)先 Plan 再 Execute,执行中允许 Replan
- 每步执行后做"是否需要 Replan"判断

```python
class HybridAgent:
    def __init__(self, llm, tools, planner, executor):
        self.llm = llm
        self.tools = tools
        self.planner = planner  # Plan 模型
        self.executor = executor  # Execute 模型
        self.max_steps = 10
        self.max_replans = 2

    async def run(self, query: str, context: str):
        # Step 1: 意图判断 + 复杂度评估
        complexity = await self.assess_complexity(query)
        
        if complexity <= 2:
            # 简单任务: 直接 ReAct
            return await self.react_loop(query, context)
        else:
            # 复杂任务: Plan then Execute with Replan
            return await self.plan_execute_loop(query, context)

    async def plan_execute_loop(self, query, context):
        plan = await self.planner.create_plan(query, context)
        results = []
        replan_count = 0
        
        for i, step in enumerate(plan.steps):
            # 执行单步(内部是 ReAct)
            result = await self.executor.execute_step(step, context, results)
            results.append({"step": step, "result": result})
            
            # 判断是否需要 Replan
            if replan_count < self.max_replans:
                need_replan = await self.check_replan(query, plan, results)
                if need_replan:
                    plan = await self.planner.replan(query, plan, results)
                    replan_count += 1
        
        # 最终汇总
        return await self.llm.summarize(query, results)
```

**2. 模型路由 —— 成本优化关键**

不同复杂度的请求路由到不同模型,豆包内部叫 **"Model Cascade"**:

| 请求类型 | 路由模型 | 成本(相对) | 占比 |
|----------|----------|------------|------|
| 闲聊/简单 QA | 豆包-Lite (4B) | 1x | 60% |
| 工具调用/中等推理 | 豆包-Pro (32B) | 5x | 30% |
| 复杂推理/数学/代码 | 豆包-Pro-Max (175B) | 20x | 8% |
| 兜底(其他都失败) | 兜底大模型 | 30x | 2% |

路由策略: 先用豆包-Lite 做意图分类(成本低),再决定用哪个模型执行。

**3. Memory 管理 —— 分层 Memory**

```
┌─────────────────────────────────────────┐
│  Short-term Memory (当前对话窗口)        │
│  最近 N 轮对话原文,存 Redis (TTL 24h)    │
│  容量: 最近 8K Token                     │
└──────────────────┬──────────────────────┘
                   │ 超过窗口触发压缩
┌──────────────────▼──────────────────────┐
│  Working Memory (会话级摘要)              │
│  LLM 生成对话摘要,存 Redis (TTL 7d)      │
│  容量: 摘要 1K Token + 关键事实表         │
└──────────────────┬──────────────────────┘
                   │ 会话结束触发持久化
┌──────────────────▼──────────────────────┐
│  Long-term Memory (用户级记忆)            │
│  用户偏好/事实,存 MySQL + 向量库(永久)    │
│  容量: 每用户最多 100 条结构化记忆         │
└─────────────────────────────────────────┘
```

关键设计: **摘要触发时机** —— 不是每轮都摘要(成本高),而是当 Token 数超过阈值(如 6K)时,把最早的一半对话摘要压缩。这样在 8K 窗口内始终保持"近期原文 + 早期摘要"。

**4. 工具调用 —— 并发 + 容错**

```python
class ToolExecutor:
    def __init__(self, tools: dict, timeout=10, max_retries=2):
        self.tools = tools
        self.timeout = timeout
        self.max_retries = max_retries

    async def execute(self, tool_calls: list):
        # 并发执行多个工具调用
        tasks = [self._execute_one(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            {"tool_call_id": tc.id, "result": r if not isinstance(r, Exception) else f"Error: {r}"}
            for tc, r in zip(tool_calls, results)
        ]

    async def _execute_one(self, tool_call):
        tool = self.tools.get(tool_call.name)
        if not tool:
            return f"Tool {tool_call.name} not found"
        
        # 指数退避重试
        for attempt in range(self.max_retries + 1):
            try:
                return await asyncio.wait_for(
                    tool.arun(**tool_call.arguments),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                if attempt == self.max_retries:
                    return f"Tool {tool_call.name} timeout after {self.timeout}s"
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                if attempt == self.max_retries:
                    return f"Tool error: {e}"
                await asyncio.sleep(2 ** attempt)
```

**5. 知识库 RAG —— 混合检索**

豆包知识库采用 **向量检索 + BM25 关键词检索 + Rerank** 三路融合:
- 向量检索: 召回语义相近 chunk,Top 20
- BM25 检索: 召回关键词命中 chunk,Top 20
- 融合去重后,用 Cross-Encoder Rerank 取 Top 5
- 关键优化: **Query 改写** —— 用户问"他最近怎么样",根据上下文改写成"张三最近的工作进展"

**四、容量估算**

| 指标 | 估算 |
|------|------|
| 日活 DAU | 5000 万 |
| 人均对话轮次 | 15 轮/天 |
| 日均请求量 | 7.5 亿次 |
| 峰值 QPS | 5 万 |
| 平均输入 Token | 800(含历史) |
| 平均输出 Token | 300 |
| 日均 Token 消耗 | 8250 亿 Token |
| GPU 卡数(推理) | 约 2000 张 A100(假设单卡 200 QPS) |
| 月度推理成本 | 约 ¥3000-5000 万(自部署) |

**五、成本优化策略**

1. **KV Cache 复用**: 多轮对话共享前缀,缓存 KV,减少 40% 计算量
2. **Prompt 压缩**: 历史对话用摘要,工具描述动态裁剪(只保留相关工具)
3. **模型路由**: 60% 流量走 Lite 模型,节省 70% 成本
4. **结果缓存**: 相同 Query 在 1 小时内命中缓存,命中率约 15%
5. **Batch 推理**: 低峰期合并请求做 Batch,提升 GPU 利用率

**六、可观测性**

- **Trace**: 每个请求一个 trace_id,串联 LLM 调用、工具调用、检索全链路(字节用自研 ARMS)
- **指标**: 首 Token 延迟、完整延迟、工具成功率、Replan 率、Token 消耗、错误率
- **日志**: 全量 Prompt/Response 落 Hive,供 Bad Case 分析(脱敏后)
- **告警**: 错误率 > 1% / 延迟 P95 > 10s / 工具失败率 > 5% 触发飞书告警

**七、面试加分点**

1. 主动提"豆包的合规要求": 内容安全过滤、政治敏感词、未成年保护
2. 主动提"多端一致性": App / 网页 / 飞书会话同步
3. 主动提"灰度发布": 新模型先 1% 流量灰度,观察指标再放量
4. 主动提"降级方案": 模型挂了降级到规则引擎 / 缓存 / 静态回复

</details>

---

### Q3: Agent 循环卡死了怎么办? — 字节高频追问,死循环检测和恢复策略

<details>
<summary>查看答案</summary>

**这是字节面试最高频的追问之一**,面试官想考察你对生产环境异常场景的处理经验。

**一、Agent 卡死的常见场景**

| 场景 | 表现 | 根因 |
|------|------|------|
| 工具调用死循环 | Agent 反复调用同一个工具 | 工具返回结果 LLM 无法理解,以为没成功 |
| 思考死循环 | Agent 不断 "Thought" 但不 "Action" | 任务超出能力,LLM 陷入纠结 |
| 相同输出循环 | Agent 输出完全相同的 Thought+Action | 上下文污染 / 温度太低 |
| 工具阻塞 | 工具调用一直不返回 | 下游服务超时 / 死锁 |
| Token 爆炸 | 上下文越来越长,直到超限 | Memory 压缩失效,历史无限增长 |

**二、死循环检测策略(分层防御)**

```python
class AgentLoopGuard:
    def __init__(self):
        self.max_steps = 15              # 最大步数硬限制
        self.max_total_tokens = 50000    # Token 硬限制
        self.max_time_seconds = 60       # 时间硬限制
        self.max_same_action = 3         # 相同 Action 重复次数
        self.recent_actions = []         # 最近动作历史

    def check_loop(self, step: int, action: str, tokens: int, start_time: float) -> dict:
        """返回 {"should_stop": bool, "reason": str, "strategy": str}"""
        
        # 1. 硬限制检测
        if step >= self.max_steps:
            return {"should_stop": True, "reason": "max_steps_exceeded", "strategy": "force_summarize"}
        if tokens >= self.max_total_tokens:
            return {"should_stop": True, "reason": "token_limit", "strategy": "truncate_context"}
        if time.time() - start_time > self.max_time_seconds:
            return {"should_stop": True, "reason": "timeout", "strategy": "return_partial"}
        
        # 2. 重复动作检测 (滑动窗口)
        self.recent_actions.append(action)
        if len(self.recent_actions) > 5:
            self.recent_actions.pop(0)
        
        # 检测最近 5 步中某个动作出现 >= 3 次
        from collections import Counter
        counter = Counter(self.recent_actions)
        most_common, count = counter.most_common(1)[0]
        if count >= self.max_same_action:
            return {"should_stop": True, "reason": f"action_{most_common}_repeated_{count}_times", 
                    "strategy": "inject_hint"}
        
        # 3. 相邻步骤完全相同检测 (输出无变化)
        if len(self.recent_actions) >= 2 and self.recent_actions[-1] == self.recent_actions[-2]:
            return {"should_stop": True, "reason": "identical_consecutive_actions", 
                    "strategy": "increase_temperature"}
        
        return {"should_stop": False, "reason": "", "strategy": ""}

    def get_recovery_strategy(self, reason: str) -> str:
        """根据卡死原因返回恢复策略"""
        strategies = {
            "max_steps_exceeded": "force_summarize",   # 强制总结已有结果
            "token_limit": "truncate_context",          # 截断早期上下文
            "timeout": "return_partial",                # 返回部分结果
            "action_repeated": "inject_hint",           # 注入提示打破循环
            "identical_consecutive": "increase_temp",   # 提高温度增加多样性
        }
        return strategies.get(reason, "force_summarize")
```

**三、恢复策略详解**

**策略 1: 注入提示打破循环(Inject Hint)**

当检测到 Agent 反复调用同一工具时,在 Prompt 中注入一条"系统观察":

```
[System Observation] 你已经调用了 search_web 工具 3 次,得到的结果都相似。
请尝试:
1. 改用不同的搜索关键词
2. 换一个工具(如 search_knowledge_base)
3. 如果信息已足够,请直接给出答案
```

**策略 2: 强制总结**

```python
async def force_summarize(self, conversation_history):
    summary_prompt = f"""
    对话已经进行了 {len(conversation_history)} 步,超出了预设限制。
    请基于已有信息,给用户一个尽可能完整的回答。
    如果信息不足,请说明缺少什么。
    
    已有对话:
    {conversation_history}
    """
    return await self.llm.arun(summary_prompt)
```

**策略 3: 上下文截断 + 压缩**

保留最近 3 轮原文,更早的用摘要替代。截断后重试。

**策略 4: 工具级超时与熔断**

```python
class ToolCircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = {}
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = {}
        self.circuit_state = {}  # "closed", "open", "half_open"

    def can_call(self, tool_name: str) -> bool:
        state = self.circuit_state.get(tool_name, "closed")
        if state == "open":
            # 检查是否到了半开尝试时间
            if time.time() - self.last_failure_time[tool_name] > self.recovery_timeout:
                self.circuit_state[tool_name] = "half_open"
                return True
            return False
        return True

    def record_failure(self, tool_name: str):
        self.failure_count[tool_name] = self.failure_count.get(tool_name, 0) + 1
        self.last_failure_time[tool_name] = time.time()
        if self.failure_count[tool_name] >= self.failure_threshold:
            self.circuit_state[tool_name] = "open"
            # 告警
            alert(f"Tool {tool_name} circuit breaker opened!")

    def record_success(self, tool_name: str):
        self.failure_count[tool_name] = 0
        self.circuit_state[tool_name] = "closed"
```

**四、预防措施(治本)**

1. **工具结果可读性**: 工具返回要结构化、带状态码、带人类可读描述,避免 LLM 误判
2. **Few-shot 示例**: 在 System Prompt 里给出"工具失败后该怎么处理"的示例
3. **温度参数调优**: Agent 循环温度建议 0.3-0.7,太低易重复,太高易发散
4. **早停机制**: 如果连续 2 步 LLM 输出 "Final Answer",提前结束
5. **监控大盘**: 实时监控 P95 步数、Replan 率、重复动作率,异常时告警

**五、字节面试加分回答**

> "在生产环境里,我们做了三层防御: **实例级**(max_steps/timeout 硬限制)、**模式级**(重复动作检测 + 熔断)、**系统级**(全局限流 + 降级)。一旦触发死循环,先注入 Hint 尝试恢复,3 次失败后强制总结返回,同时把这次 Case 自动归集到 Bad Case 库,离线分析根因。我们曾经遇到 search_web 工具因为返回格式变更导致 Agent 死循环,上线熔断机制后 5 分钟内止血,离线修复后灰度恢复。"

</details>

---

### Q4: 你的 RAG 系统召回率只有 60%,怎么优化? — 字节 RAG 优化连环问

<details>
<summary>查看答案</summary>

**字节风格的连环问**: 面试官不会一次问完,会根据你的回答逐步追问。这里给出完整的优化框架。

**一、先定位问题: 60% 召回率,问题出在哪一环?**

RAG 链路: `Query → 检索 → 召回 → Rerank → 生成`。召回率 60% 要先分清是 **检索阶段没找到** 还是 **Rerank 阶段排丢了**。

```python
def diagnose_rag(query, expected_doc_ids, retrieved_doc_ids, reranked_doc_ids):
    """诊断 RAG 各阶段指标"""
    # 检索阶段召回率
    retrieval_recall = len(set(expected_doc_ids) & set(retrieved_doc_ids)) / len(expected_doc_ids)
    # Rerank 阶段召回率
    rerank_recall = len(set(expected_doc_ids) & set(reranked_doc_ids)) / len(expected_doc_ids)
    # Rerank 是否丢了相关文档
    rerank_drop = len(set(expected_doc_ids) & set(retrieved_doc_ids)) - len(set(expected_doc_ids) & set(reranked_doc_ids))
    
    return {
        "retrieval_recall": retrieval_recall,
        "rerank_recall": rerank_recall,
        "rerank_dropped_relevant": rerank_drop,
        "bottleneck": "retrieval" if retrieval_recall < 0.7 else "rerank"
    }
```

**二、检索阶段优化(如果是检索瓶颈)**

**优化 1: Query 改写 —— 最重要的优化**

用户 Query 往往很短/有歧义,直接检索召回率低。

| 技术 | 说明 | 适用场景 |
|------|------|----------|
| Query 扩展 | 用 LLM 生成 3-5 个语义相近的 Query | Query 太短 |
| Query 分解 | 把复杂 Query 拆成多个子问题 | 多跳问答 |
| HyDE | 让 LLM 先生成假设答案,用答案去检索 | Query 与文档措辞差异大 |
| 对话式改写 | 根据上下文补全指代 | 多轮对话 |

```python
async def hyde_rewrite(query, llm):
    """HyDE: 让 LLM 生成假设答案,用答案向量检索"""
    prompt = f"请回答以下问题(即使不确定也请给出你的猜测):\n问题: {query}\n回答:"
    hypothetical_answer = await llm.arun(prompt)
    # 用假设答案做检索(而非原 Query)
    return hypothetical_answer

async def multi_query_rewrite(query, llm, n=3):
    """Multi-Query: 生成 n 个语义相近的 Query,分别检索后融合"""
    prompt = f"请把以下问题改写成 {n} 个语义相近但表述不同的版本,用于检索:\n{query}\n输出 JSON 数组。"
    queries = await llm.arun(prompt)
    return json.loads(queries) + [query]  # 包含原 Query
```

**优化 2: 混合检索(向量 + BM25)**

纯向量检索对 **关键词型 Query**(如产品型号、人名)效果差,纯 BM25 对 **语义型 Query** 效果差。混合后用 RRF(Reciprocal Rank Fusion)融合:

```python
def reciprocal_rank_fusion(result_lists, k=60):
    """RRF 融合多路检索结果"""
    fused_scores = {}
    for result_list in result_lists:
        for rank, doc in enumerate(result_list):
            if doc.id not in fused_scores:
                fused_scores[doc.id] = 0
            fused_scores[doc.id] += 1 / (k + rank + 1)
    
    # 按融合分数排序
    return sorted(fused_scores.items(), key=lambda x: -x[1])
```

**优化 3: 分块策略优化**

| 分块方式 | 适用 | 优劣 |
|----------|------|------|
| 固定长度 | 通用 | 简单,但可能切断语义 |
| 按句子/段落 | 文档 | 语义完整,但长度不一 |
| 递归分块 | 长文档 | 层级化,保留结构 |
| 语义分块 | 高质量场景 | 用模型找语义边界,成本高 |
| 父子分块 | 长文档 | 检索小块,返回大块(父)给 LLM |

**关键优化: 父子分块(Small-to-Big)** —— 把文档切成小 chunk(200 Token)用于精准检索,但返回时把 chunk 所属的大段落(1000 Token)返回给 LLM,兼顾检索精度和上下文完整。

**优化 4: 元数据过滤**

```python
# 检索时带上元数据过滤,大幅提升精度
results = vector_store.search(
    query=query_embedding,
    filter={
        "source": "official_docs",  # 只搜官方文档
        "date": {"$gte": "2025-01-01"},  # 只搜今年
        "department": "技术部",
    },
    top_k=20
)
```

**三、Rerank 阶段优化(如果是排序瓶颈)**

**优化 1: 用 Cross-Encoder 替代 Bi-Encoder**

向量检索用的是 Bi-Encoder(Query 和 Doc 分别编码),精度有限。Rerank 用 Cross-Encoder(Query 和 Doc 拼接编码),精度高但慢。典型: 召回 Top 50 → Cross-Encoder Rerank → 取 Top 5。

**优化 2: LLM Rerank**

让 LLM 对每个召回文档打分(0-10),按分数排序。成本高但效果最好,适合对质量要求极高的场景。

```python
async def llm_rerank(query, documents, llm, top_k=5):
    prompt = f"""
    用户问题: {query}
    请对以下文档的相关性打分(0-10),输出 JSON 数组 [{{"id": "doc_id", "score": 8}}, ...]:
    {json.dumps([{"id": d.id, "text": d.text[:500]} for d in documents])}
    """
    scores = await llm.arun(prompt)
    scored = json.loads(scores)
    scored.sort(key=lambda x: -x["score"])
    return [get_doc_by_id(s["id"]) for s in scored[:top_k]]
```

**四、知识库构建优化**

1. **增量更新**: 文档变更时,只重新 embedding 变更部分,而非全量
2. **去重**: 用 MinHash 或 embedding 相似度去重,避免冗余
3. **质量分级**: 给文档打质量分,检索时优先高质量文档
4. **时效性标记**: 给文档加有效期,过期的降权

**五、效果评估闭环**

```
Bad Case 收集 → 归因分析(检索/Rerank/生成) → 针对性优化 → 回归测试 → 上线
     ↑                                                                    │
     └────────────────────────── 持续监控 ────────────────────────────────┘
```

**六、字节面试连环追问模拟**

| 面试官追问 | 你的回答要点 |
|-----------|-------------|
| "Query 改写本身也要调 LLM,成本怎么算?" | 改写用 Lite 模型,成本约 ¥0.001/次; 召回率提升 15% 带来的收益远大于成本 |
| "HyDE 生成错误答案怎么办?" | HyDE 只是用来找语义相近文档,答案对错不影响检索; 实测 HyDE 对长尾 Query 提升显著 |
| "混合检索的权重怎么调?" | RRF 不需要调权重(k=60 是经验值); 如果要用加权融合,需要在标注集上 grid search |
| "Rerank 模型怎么选?" | 自研场景可微调 Cross-Encoder; 通用场景用 bge-reranker-large / Cohere Rerank |
| "怎么知道是检索的问题还是生成的问题?" | 看生成的引用来源,如果引用了正确文档但答案错了,是生成问题; 如果没引用到,是检索问题 |
| "线上 A/B 怎么设计?" | 北极星: 答案准确率(人工评分); 护栏: 延迟、成本、Bad Case 率; 实验 1-2 周 |

**七、预期效果**

| 优化组合 | 召回率 | 成本增幅 |
|----------|--------|----------|
| 基线 | 60% | 1x |
| + Query 改写 | 70% | 1.1x |
| + 混合检索 | 78% | 1.3x |
| + 父子分块 | 83% | 1.4x |
| + Cross-Encoder Rerank | 88% | 1.6x |
| + 元数据过滤 | 92% | 1.5x |

</details>

---

### Q5: 如何降低 Agent 的 Token 消耗 50%? — 字节成本优化题

<details>
<summary>查看答案</summary>

**字节灵魂考题**。字节内部对 Token 成本极其敏感(豆包定价就是靠成本优势打的),这道题答得好非常加分。

**一、Token 消耗拆解**

先搞清楚 Token 花在哪:

| 组成 | 占比(典型) | 优化空间 |
|------|------------|----------|
| System Prompt | 15% | 高 |
| 工具描述 | 20% | 高 |
| 历史对话 | 35% | 高 |
| 当前 Query | 5% | 低 |
| 输出 Token | 25% | 中 |

**二、八大优化手段**

**手段 1: Prompt 压缩(立省 20-30%)**

```python
# 优化前 (冗长)
SYSTEM_PROMPT_BAD = """
你是一个智能助手,可以帮助用户回答各种问题。你可以使用以下工具:
1. search_web: 搜索互联网获取最新信息。当你需要查找最新的新闻、天气、股票等信息时使用此工具。
   参数: query (字符串, 搜索关键词)
2. get_weather: 获取指定城市的天气信息。当你需要查询某个城市的天气时使用此工具。
   参数: city (字符串, 城市名称)
... (10 个工具,每个 100+ Token)
"""

# 优化后 (精简)
SYSTEM_PROMPT_GOOD = """
Assistant with tools:
- search_web(query): web search
- get_weather(city): weather
... (10 个工具,每个 10 Token)
"""
```

**进阶: 动态工具裁剪** —— 不是把所有工具都放进 Prompt,而是根据 Query 意图只放相关工具。

```python
async def select_relevant_tools(query, all_tools, llm, max_tools=5):
    """根据 Query 选最相关的 N 个工具"""
    tool_names = [t.name for t in all_tools]
    prompt = f"Query: {query}\n可选工具: {tool_names}\n请选出最相关的 {max_tools} 个(输出 JSON 数组):"
    selected = await llm.arun(prompt)  # 用 Lite 模型,成本低
    return [t for t in all_tools if t.name in json.loads(selected)]
```

**手段 2: 历史对话压缩(立省 30-40%)**

三层 Memory 策略(见 Q2): 近期原文 + 早期摘要 + 关键事实表。

```python
class ConversationCompressor:
    def __init__(self, max_tokens=6000, summary_trigger=4000):
        self.max_tokens = max_tokens
        self.summary_trigger = summary_trigger

    async def compress_if_needed(self, messages, llm):
        total_tokens = count_tokens(messages)
        if total_tokens <= self.summary_trigger:
            return messages
        
        # 把最早的 50% 对话压缩成摘要
        split_point = len(messages) // 2
        old_messages = messages[:split_point]
        recent_messages = messages[split_point:]
        
        summary = await self.summarize(old_messages, llm)
        
        return [{"role": "system", "content": f"Earlier conversation summary:\n{summary}"}] + recent_messages

    async def summarize(self, messages, llm):
        # 用 Lite 模型做摘要,成本低
        prompt = f"Summarize key facts and decisions:\n{format_messages(messages)}"
        return await llm_lite.arun(prompt)
```

**手段 3: 模型路由 / Cascade(立省 40-60%)**

60% 简单请求走 Lite 模型(成本 1x),30% 走 Pro(5x),10% 走 Max(20x)。加权平均成本只有原来的 35%。

```python
class ModelRouter:
    async def route(self, query, context):
        # 用最便宜的模型做意图判断
        intent = await self.classify_intent(query, model="lite")
        
        if intent in ["chitchat", "simple_qa"]:
            return "doubao-lite"
        elif intent in ["tool_use", "moderate_reasoning"]:
            return "doubao-pro"
        else:  # complex_reasoning, math, code
            return "doubao-pro-max"
```

**手段 4: KV Cache 复用(省 30-50% 计算量)**

多轮对话中,System Prompt + 工具描述 + 早期对话是不变的,这些 Token 的 KV 可以缓存,后续请求直接复用。

```python
# 主流推理框架都支持 Prefix Caching
# vLLM 示例
response = llm.generate(
    prompt=new_user_message,
    prefix_cache_key=session_id,  # 同一会话复用前缀 KV
    use_prefix_cache=True
)
```

**手段 5: 输出长度控制(省 10-20%)**

```python
# 在 Prompt 中限制输出长度
SYSTEM_PROMPT += "\n回答简洁,不超过 200 字,除非用户要求详细。"

# 或者在 decode 参数中限制
response = llm.generate(prompt, max_tokens=300)  # 硬限制
```

**手段 6: 结果缓存(省 15%)**

```python
class ResponseCache:
    def __init__(self, redis_client, ttl=3600):
        self.redis = redis_client
        self.ttl = ttl

    async def get_or_compute(self, query, context_hash, compute_fn):
        # 对相同 Query + 相同上下文做缓存
        cache_key = f"rag:{hashlib.md5((query + context_hash).encode()).hexdigest()}"
        
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        result = await compute_fn(query)
        await self.redis.setex(cache_key, self.ttl, json.dumps(result))
        return result
```

**7. 批处理(Batch API)**

非实时场景(如离线数据处理)用 Batch API,成本降低 50%。OpenAI / 字节豆包都提供 Batch API,24 小时内返回结果。

**8. Few-shot 示例动态选取**

不要把所有 Few-shot 示例都放 Prompt,而是根据 Query 动态选 2-3 个最相似的:

```python
async def dynamic_few_shot(query, example_pool, embedding_model, k=2):
    query_emb = embedding_model.encode(query)
    # 按相似度选 top-k 示例
    examples = sorted(example_pool, key=lambda e: cosine_sim(query_emb, e.embedding), reverse=True)[:k]
    return [e.prompt for e in examples]
```

**三、成本优化效果汇总**

| 优化手段 | Token 节省 | 成本节省 | 实现难度 |
|----------|-----------|---------|---------|
| Prompt 压缩 | 20% | 20% | 低 |
| 历史对话压缩 | 30% | 25% | 中 |
| 模型路由 | 0% | 50% | 中 |
| KV Cache | 0% | 35%(计算量) | 低 |
| 输出长度控制 | 15% | 15% | 低 |
| 结果缓存 | 15% | 15% | 低 |
| Batch API | 0% | 50%(非实时) | 低 |
| Few-shot 动态选取 | 10% | 10% | 中 |

**组合效果**: Prompt 压缩 + 历史压缩 + 模型路由 + 缓存 = **Token 减少 50%,成本降低 70%**。

**四、字节面试加分回答**

> "降低 50% Token 只是手段,真正要做的是 **降本不降质**。我的做法是: 先建评测集,每次优化都跑回归,确保准确率不降。优先做 ROI 高的优化 —— Prompt 压缩和历史压缩实现成本低、效果大,先上; 模型路由需要训练分类器,放第二批; KV Cache 依赖推理框架支持,和 infra 团队对齐后上线。最终我们在豆包某场景做到 Token 减少 52%、成本降低 71%、准确率反而提升 2%(因为短 Prompt 模型更聚焦)。"

</details>

---

### Q6: Function Calling 和 ReAct 有什么区别? 各适用什么场景? — 字节基础概念题

<details>
<summary>查看答案</summary>

**一、核心区别**

| 维度 | Function Calling | ReAct |
|------|-----------------|-------|
| 提出 | OpenAI 2023.6(API 原生支持) | Yao et al. 2022(论文) |
| 机制 | 模型微调后直接输出结构化 JSON | Prompt 工程引导输出 Thought/Action/Obs |
| 依赖 | 需要模型原生支持 | 任何 LLM 都能用(Prompt 驱动) |
| 输出格式 | 标准 JSON | 自由文本(需解析) |
| 多步能力 | 需要外层循环驱动 | 内置循环(Thought→Action→Obs→Thought) |
| 可控性 | 高(结构化) | 中(需解析) |
| 灵活性 | 低(模型决定调什么) | 高(Prompt 可定制) |
| Token 效率 | 高(JSON 紧凑) | 低(Thought 冗长) |
| 出错率 | 低(模型原生) | 中(解析可能失败) |

**二、Function Calling 工作流程**

```
用户 Query
    │
    ▼
[LLM + 工具描述] ──→ 模型原生输出:
                      {
                        "tool": "search_web",
                        "arguments": {"query": "北京天气"}
                      }
    │
    ▼
[执行工具] ──→ 返回结果
    │
    ▼
[LLM + 工具结果] ──→ 最终答案 或 下一个工具调用
```

特点: **模型被训练过如何输出工具调用**,不需要 Prompt 工程。调用是"一步"的(模型决定调一次工具),多步需要外层循环。

**三、ReAct 工作流程**

```
用户 Query
    │
    ▼
[Prompt: Thought-Action-Observation 循环]
    │
    ▼
LLM 输出:
  Thought: 我需要先搜索北京天气
  Action: search_web
  Action Input: 北京天气
    │
    ▼
[解析文本,执行工具]
    │
    ▼
Observation: 北京今天晴,25度
    │
    ▼
LLM 继续:
  Thought: 我已经知道天气了,可以回答
  Action: Final Answer
  Action Input: 北京今天晴天,气温25度
```

特点: **通过 Prompt 引导 LLM 输出特定格式**,需要文本解析(可能出错)。循环是内置的,LLM 自己决定何时结束。

**四、代码对比**

```python
# === Function Calling (OpenAI 风格) ===
import openai

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "北京天气怎么样?"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取天气",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"]
            }
        }
    }],
    tool_choice="auto"
)

# 模型直接输出结构化工具调用
if response.choices[0].message.tool_calls:
    tool_call = response.choices[0].message.tool_calls[0]
    args = json.loads(tool_call.function.arguments)  # 标准 JSON
    result = get_weather(**args)
    # 把结果送回模型生成最终答案
    ...


# === ReAct (Prompt 驱动) ===
REACT_PROMPT = """
Answer the question using Thought/Action/Action Input/Observation format.

Question: {question}

Thought: 
"""

def react_loop(question, llm, tools, max_steps=5):
    prompt = REACT_PROMPT.format(question=question)
    scratchpad = ""
    
    for step in range(max_steps):
        output = llm.generate(prompt + scratchpad)
        
        # 解析文本(可能失败)
        if "Final Answer:" in output:
            return extract_final_answer(output)
        
        try:
            action = extract_action(output)        # 正则解析
            action_input = extract_action_input(output)
            
            result = tools[action](action_input)
            scratchpad += output + f"\nObservation: {result}\nThought: "
        except ParseError:
            scratchpad += output + "\n(解析失败,请重新格式化)\nThought: "
    
    return "超出最大步数"
```

**五、各自适用场景**

**Function Calling 适用**:
- 模型原生支持(OpenAI GPT-4、Claude、豆包等)
- 工具数量固定、定义明确
- 对可靠性要求高(生产环境)
- 单轮或简单多轮工具调用
- 需要 API 级别的集成

**ReAct 适用**:
- 模型不支持 Function Calling(开源模型、小模型)
- 需要复杂的推理链(每步需要"思考")
- 需要 Prompt 级别的灵活定制
- 研究 / 原型开发
- 需要 Thought 可解释性(看到推理过程)

**六、字节面试常见追问**

| 追问 | 回答要点 |
|------|---------|
| "豆包用的是 Function Calling 还是 ReAct?" | 豆包原生支持 Function Calling,内部 Agent 框架基于 FC; 但复杂场景会用 ReAct 思路定制 Prompt |
| "ReAct 解析失败怎么办?" | 容错解析(正则 + JSON 降级) + Few-shot 示例 + 重试机制; 或改用结构化输出(如 XML 标签) |
| "两者能结合吗?" | 可以。用 FC 保证工具调用可靠性,同时在 Prompt 中加入 "think step by step" 引导推理 |
| "Function Calling 支持并行调用吗?" | GPT-4 Turbo / 豆包 Pro 支持 parallel_function_calls,一次返回多个工具调用 |
| "ReAct 的 Thought 有必要吗?" | 有。Thought 让模型"显式推理",减少幻觉; 但增加 Token 消耗,简单任务可去掉 |

**七、总结一句话**

> **Function Calling 是"模型原生能力",ReAct 是"Prompt 工程"**。生产环境优先 FC(可靠),复杂推理场景用 ReAct(灵活),最佳实践是 **FC 为主 + ReAct 思路定制 Prompt**。

</details>

---

### Q7: 如何评估一个 Agent 的好坏? — 字节评估方法论题

<details>
<summary>查看答案</summary>

字节非常重视数据驱动,这道题考察你是否有完整的评估体系。

**一、Agent 评估的难点**

| 难点 | 说明 |
|------|------|
| 非确定性 | 同一输入,Agent 可能走不同路径 |
| 多步骤 | 中间步骤错了,最终结果可能对(也可能错) |
| 依赖外部 | 工具调用依赖外部服务,环境不可控 |
| 评价主观 | "回答好不好"往往需要人工判断 |
| 成本高 | 跑一次评测可能要调几十次 LLM |

**二、评估维度框架(5 层)**

```
┌─────────────────────────────────────────────┐
│  Level 5: 业务指标                          │
│  用户满意度 / 留存 / DAU / 付费转化          │
├─────────────────────────────────────────────┤
│  Level 4: 端到端任务指标                    │
│  任务完成率 / 完成时间 / 用户修正次数        │
├─────────────────────────────────────────────┤
│  Level 3: Agent 行为指标                    │
│  工具调用准确率 / 步数 / Replan 率 / 死循环率│
├─────────────────────────────────────────────┤
│  Level 2: 模型能力指标                      │
│  意图识别准确率 / 规划合理性 / 总结质量      │
├─────────────────────────────────────────────┤
│  Level 1: 基础质量指标                      │
│  准确性 / 流畅性 / 安全性 / 时延 / 成本      │
└─────────────────────────────────────────────┘
```

**三、各层指标详解**

**Level 1: 基础质量指标**

| 指标 | 定义 | 评估方法 |
|------|------|----------|
| 准确性 | 答案是否事实正确 | 人工标注 / LLM-as-Judge |
| 流畅性 | 语言是否通顺 | 困惑度 / 人工评分 |
| 安全性 | 是否有违规内容 | 规则 + 模型审核 |
| 首 Token 时延 | TTFT (P95) | 日志统计 |
| 完整时延 | E2E latency (P95) | 日志统计 |
| Token 消耗 | 平均 Token/次 | 日志统计 |

**Level 2: 模型能力指标**

| 指标 | 定义 | 评估方法 |
|------|------|----------|
| 意图识别准确率 | 是否正确理解用户意图 | 标注集对比 |
| 规划合理性 | Plan 是否合理、无遗漏 | LLM-as-Judge 评分 |
| 工具选择准确率 | 选对工具的比例 | 标注集对比 |
| 参数提取准确率 | 工具参数是否正确 | 标注集对比 |
| 总结质量 | 最终答案是否涵盖关键信息 | LLM-as-Judge |

**Level 3: Agent 行为指标**

| 指标 | 定义 | 理想值 |
|------|------|--------|
| 任务完成率 | 完成任务的比例 | > 85% |
| 平均步数 | 完成任务所需步数 | 越少越好 |
| Replan 率 | 需要重新规划的比例 | < 20% |
| 死循环率 | 触发死循环检测的比例 | < 1% |
| 工具调用成功率 | 工具执行成功比例 | > 95% |
| 重复动作率 | 无效重复动作比例 | < 5% |

**Level 4: 端到端任务指标**

| 指标 | 定义 |
|------|------|
| 任务完成率 | 用户目标达成的比例 |
| 首次成功率 | 不需用户修正就完成 |
| 修正次数 | 用户平均修正几次 |
| 完成时间 | 从开始到完成任务的时间 |
| 放弃率 | 用户中途放弃的比例 |

**Level 5: 业务指标**

| 指标 | 定义 |
|------|------|
| 用户满意度 (CSAT) | 1-5 星评分 |
| 净推荐值 (NPS) | 推荐意愿 |
| 次日留存 | 次日是否继续使用 |
| DAU / MAU | 日活 / 月活 |
| 付费转化率 | 免费 → 付费转化 |

**四、评估方法**

**方法 1: 人工标注(金标准)**

构建标注集(500-1000 条),人工标注"正确答案"。每次迭代跑回归,看准确率变化。成本高但最可靠。

**方法 2: LLM-as-Judge(可扩展)**

用更强的 LLM(如 GPT-4 / 豆包-Pro-Max)给 Agent 输出打分:

```python
JUDGE_PROMPT = """
你是一个严格的评估专家。请对以下 Agent 回答打分(1-5 分):

用户问题: {question}
Agent 回答: {answer}
参考答案: {reference}

评分维度:
1. 准确性(事实是否正确)
2. 完整性(是否涵盖关键信息)
3. 相关性(是否切题)
4. 安全性(是否有违规内容)

输出 JSON: {{"accuracy": 5, "completeness": 4, "relevance": 5, "safety": 5, "overall": 4.75, "reason": "..."}}
"""

async def llm_judge(question, answer, reference, judge_llm):
    prompt = JUDGE_PROMPT.format(question=question, answer=answer, reference=reference)
    result = await judge_llm.arun(prompt)
    return json.loads(result)
```

**LLM-as-Judge 的坑**:
- 位置偏差: LLM 倾向给排在前面的答案更高分 → 随机打乱顺序
- 长度偏差: LLM 倾向给长答案更高分 → 控制长度或归一化
- 自我偏好: GPT-4 评 GPT-4 的答案偏高 → 用不同模型族交叉评

**方法 3: 在线 A/B 测试**

```python
# A/B 实验设计
experiment_config = {
    "name": "agent_v2_rerank_optimization",
    "duration_days": 14,
    "traffic_percentage": 10,  # 实验组 10% 流量
    "metrics": {
        "north_star": "task_completion_rate",  # 北极星
        "guardrail": ["latency_p95", "cost_per_query", "bad_case_rate", "csat"],  # 护栏
    },
    "success_criteria": {
        "task_completion_rate": "+3%以上",
        "guardrail_no_regression": "所有护栏指标不劣化"
    }
}
```

**方法 4: Trajectory 评估(评估中间步骤)**

不只看最终结果,还要看中间步骤对不对:

```python
def evaluate_trajectory(trajectory, expected_steps):
    """
    trajectory: Agent 实际执行轨迹 [(action, result), ...]
    expected_steps: 标注的期望步骤 [(action, expected_result), ...]
    """
    scores = {
        "step_accuracy": 0,      # 步骤正确率
        "tool_selection": 0,     # 工具选择准确率
        "efficiency": 0,         # 效率(实际步数/期望步数)
        "redundancy": 0,         # 冗余(无效步骤比例)
    }
    
    correct_steps = sum(1 for a, _ in trajectory if a in [e[0] for e in expected_steps])
    scores["step_accuracy"] = correct_steps / len(expected_steps)
    scores["efficiency"] = len(expected_steps) / len(trajectory) if trajectory else 0
    # ...
    return scores
```

**方法 5: 对抗测试 / Red Teaming**

构造"刁钻"用例测试 Agent 鲁棒性:
- 工具失败场景(模拟工具超时/返回错误)
- 越狱攻击(试图让 Agent 做违规的事)
- 长尾问题(罕见但合理的问题)
- 多轮对话中改变话题

**五、评估闭环**

```
┌──────────────────────────────────────────────────────┐
│  线上监控                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 日志采集 │→ │ Bad Case │→ │ 归因分析 │           │
│  │          │  │ 自动归集 │  │          │           │
│  └──────────┘  └──────────┘  └────┬─────┘           │
└───────────────────────────────────┼──────────────────┘
                                    │
┌───────────────────────────────────▼──────────────────┐
│  离线评估                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 标注集   │→ │ 回归测试 │→ │ A/B 实验 │           │
│  │ 扩充     │  │          │  │          │           │
│  └──────────┘  └──────────┘  └────┬─────┘           │
└───────────────────────────────────┼──────────────────┘
                                    │
                              ┌─────▼─────┐
                              │ 模型/Prompt│
                              │ 迭代优化   │
                              └───────────┘
```

**六、字节面试加分回答**

> "Agent 评估要分层做。我习惯先建一个 500 条的黄金标注集,覆盖核心场景 + 长尾 + 边界 Case。日常迭代用 LLM-as-Judge 做快速回归(成本低),每月用人工标注做一次校准(防止 LLM-Judge 漂移)。线上做 A/B,北极星看任务完成率,护栏看延迟/成本/Bad Case 率。最重要的是 **Bad Case 闭环** —— 线上自动归集低分 Case,人工归因后补充到标注集,形成飞轮。我们在豆包某场景用这套体系,3 个月把任务完成率从 72% 提到 89%。"

</details>

---

### Q8: 设计一个多模态 Agent(图片理解 + 视频分析 + 文本)— 字节多模态方向题

<details>
<summary>查看答案</summary>

**题目**: 为抖音设计一个多模态 Agent,能理解图片、分析视频、回答文本问题,支持用户上传混合内容(如"看看这个视频讲的啥 + 配上这几张图")。

**一、需求澄清**

| 维度 | 假设 |
|------|------|
| 输入 | 图片(JPG/PNG)、视频(MP4, 最长 10 分钟)、文本 |
| 输出 | 文本回答、生成图片(可选)、视频时间线标注 |
| 场景 | 抖音内容理解、创作者辅助、内容审核 |
| QPS | 1000 |
| 延迟 | 首 Token < 3s,完整分析 < 30s(视频) |

**二、核心挑战**

1. **模态对齐**: 图片、视频、文本要在同一语义空间对齐
2. **视频处理**: 视频帧数多,不能每帧都送 LLM(Token 爆炸)
3. **时序理解**: 视频有时间维度,需要理解"先后顺序"
4. **混合输入**: 用户可能同时给图+视频+文本,要能关联理解
5. **工具编排**: 不同模态需要不同工具,编排复杂

**三、架构设计**

```
┌──────────────────────────────────────────────────────────────┐
│                     多模态 Agent                              │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ 图片理解 │  │ 视频分析 │  │ 文本理解 │  │ 混合对齐 │    │
│  │ Tool     │  │ Tool     │  │ Tool     │  │ Tool     │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │              │              │              │          │
│       └──────────────┴──────────────┴──────────────┘          │
│                          │                                   │
│              ┌───────────▼───────────┐                       │
│              │  多模态 LLM (豆包-VL) │                       │
│              │  Vision-Language Model│                       │
│              └───────────┬───────────┘                       │
│                          │                                   │
│              ┌───────────▼───────────┐                       │
│              │  Agent 编排器 (ReAct) │                       │
│              └───────────┬───────────┘                       │
└──────────────────────────┼───────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼───────┐  ┌───────▼───────┐  ┌───────▼───────┐
│  图片处理     │  │  视频处理     │  │  文本处理     │
│ ┌───────────┐ │  │ ┌───────────┐ │  │ ┌───────────┐ │
│ │ VLM 编码  │ │  │ │ 关键帧抽取│ │  │ │ LLM 理解  │ │
│ │ OCR       │ │  │ │ ASR 转录  │ │  │ │ NLU       │ │
│ │ 目标检测  │ │  │ │ VLM 理解  │ │  │ │ 情感分析  │ │
│ └───────────┘ │  │ └───────────┘ │  │ └───────────┘ │
└───────────────┘  └───────────────┘  └───────────────┘
```

**四、核心模块实现**

**1. 视频处理: 关键帧抽取 + ASR**

视频不能逐帧送 LLM,需要先"压缩"成关键信息:

```python
class VideoProcessor:
    def __init__(self, vlm, asr_model, keyframe_interval=2.0):
        self.vlm = vlm
        self.asr_model = asr_model
        self.keyframe_interval = keyframe_interval  # 每 2 秒抽一帧

    async def process_video(self, video_path: str) -> dict:
        # 1. 抽取关键帧
        keyframes = await self.extract_keyframes(video_path)
        # keyframes = [{"timestamp": 0.0, "path": "frame_0.jpg"}, ...]
        
        # 2. ASR 转录语音
        transcript = await self.asr_model.transcribe(video_path)
        # transcript = [{"start": 0.0, "end": 2.5, "text": "大家好今天..."}, ...]
        
        # 3. VLM 理解每个关键帧(并发)
        frame_descriptions = await asyncio.gather(*[
            self.vlm.describe_frame(kf["path"], kf["timestamp"])
            for kf in keyframes
        ])
        
        # 4. 构建视频结构化表示
        video_repr = {
            "duration": get_duration(video_path),
            "keyframes": [
                {"timestamp": kf["timestamp"], "description": desc}
                for kf, desc in zip(keyframes, frame_descriptions)
            ],
            "transcript": transcript,
            "summary": await self.summarize_video(frame_descriptions, transcript)
        }
        return video_repr

    async def extract_keyframes(self, video_path):
        """按固定间隔抽取关键帧(也可用场景检测算法)"""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = []
        frame_interval = int(fps * self.keyframe_interval)
        
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % frame_interval == 0:
                timestamp = idx / fps
                frame_path = f"/tmp/frame_{idx}.jpg"
                cv2.imwrite(frame_path, frame)
                frames.append({"timestamp": timestamp, "path": frame_path})
            idx += 1
        cap.release()
        return frames
```

**2. 图片理解工具**

```python
class ImageUnderstandingTool:
    def __init__(self, vlm, ocr_engine, detection_model):
        self.vlm = vlm
        self.ocr = ocr_engine
        self.detection = detection_model

    async def understand_image(self, image_path: str, question: str = None) -> dict:
        # 并发执行多种理解任务
        vlm_desc, ocr_text, objects = await asyncio.gather(
            self.vlm.describe(image_path, question),
            self.ocr.extract_text(image_path),
            self.detection.detect(image_path)
        )
        
        return {
            "description": vlm_desc,       # VLM 整体描述
            "text_in_image": ocr_text,     # 图中文字
            "objects": objects,            # 检测到的物体
            "image_path": image_path
        }
```

**3. 多模态 Agent 编排**

```python
class MultimodalAgent:
    def __init__(self, vlm, tools):
        self.vlm = vlm  # 多模态大模型
        self.tools = {
            "understand_image": ImageUnderstandingTool(...),
            "analyze_video": VideoProcessor(...),
            "text_qa": TextQATool(...),
            "generate_image": ImageGenerationTool(...),
        }

    async def run(self, user_input: dict) -> AsyncGenerator:
        """
        user_input: {
            "text": "看看这个视频讲的啥,配的这几张图相关吗?",
            "images": ["img1.jpg", "img2.jpg"],
            "videos": ["video.mp4"]
        }
        """
        # Step 1: 预处理各模态(并发)
        image_results, video_results = await asyncio.gather(
            asyncio.gather(*[self.tools["understand_image"].understand_image(img) 
                             for img in user_input.get("images", [])]),
            asyncio.gather(*[self.tools["analyze_video"].process_video(v) 
                             for v in user_input.get("videos", [])])
        )

        # Step 2: 构建多模态上下文
        context = self.build_multimodal_context(user_input["text"], image_results, video_results)

        # Step 3: Agent 循环(ReAct)
        async for chunk in self.react_loop(context, user_input["text"]):
            yield chunk

    def build_multimodal_context(self, text, image_results, video_results):
        context = f"用户问题: {text}\n\n"
        
        if image_results:
            context += "图片理解结果:\n"
            for i, img in enumerate(image_results):
                context += f"[图片{i+1}] 描述: {img['description']}, 文字: {img['text_in_image']}, 物体: {img['objects']}\n"
        
        if video_results:
            context += "\n视频分析结果:\n"
            for v in video_results:
                context += f"视频摘要: {v['summary']}\n"
                context += f"转录: {' '.join([t['text'] for t in v['transcript']])}\n"
                context += f"关键帧: {len(v['keyframes'])} 帧\n"
        
        return context
```

**4. 混合对齐 —— 关键创新点**

当用户同时给图和视频时,需要理解它们的关联:

```python
async def align_modalities(self, image_results, video_results, user_text):
    """判断图和视频的关联性"""
    align_prompt = f"""
    用户问题: {user_text}
    
    图片内容: {[img['description'] for img in image_results]}
    视频内容: {[v['summary'] for v in video_results]}
    
    请分析:
    1. 图片和视频在内容上是否相关?
    2. 图片是否是视频的截图/补充?
    3. 用户想了解什么?
    """
    return await self.vlm.arun(align_prompt)
```

**五、成本与时延优化**

| 优化手段 | 效果 |
|----------|------|
| 关键帧抽取(不逐帧) | Token 减少 90% |
| ASR + VLM 并发 | 延迟降低 40% |
| 视频摘要缓存(相同视频) | 成本降低 30% |
| 轻量 VLM 做初筛,复杂送大 VLM | 成本降低 50% |
| 图片缩放(长边 1024) | Token 减少 60% |

**六、字节面试加分点**

1. 主动提 **抖音场景**: "抖音有大量 UGC 视频,Agent 可以帮创作者自动生成标题、标签、摘要"
2. 主动提 **内容审核**: "多模态 Agent 可以做图文视频一致性审核,检测违规内容"
3. 主动提 **豆包-VL**: "字节自研的豆包视觉语言模型,支持图文视频理解,内部很多场景在用"
4. 主动提 **流式输出**: "视频分析耗时长,可以先流式返回'正在分析视频...已完成转录...发现关键画面...'"

</details>
