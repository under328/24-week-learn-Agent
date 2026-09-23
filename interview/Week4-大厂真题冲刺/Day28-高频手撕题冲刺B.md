## Week4 知识回顾表

> 总结 Week4 四周大厂面试重点(Week1-4 覆盖完整知识体系)

| 周次 | 主题 | 核心知识点 | 大厂高频考点 | 手撕题覆盖 |
|------|------|-----------|-------------|-----------|
| **Week1** | Agent 基础 | Agent 定义/架构/感知-规划-行动循环/记忆分类/工具使用 | Agent vs Chatbot 区别、ReAct 原理、记忆机制(短期/长期/工作记忆) | Day07 手撕:基础 Agent Loop |
| **Week2** | RAG 与 Agent | 文档分块/Embedding/向量检索/混合检索/Rerank/Agentic RAG | 分块策略选择、BM25 vs 向量、RRF 融合、多跳推理 | Day14 手撕:基础 RAG |
| **Week3** | 框架与系统设计 | LangChain/LlamaIndex/AutoGPT/MetaGPT/系统设计 | 框架对比、Multi-Agent 架构、生产部署、评估方法 | Day21 手撕:框架核心抽象 |
| **Week4** | 大厂真题冲刺 | 字节/阿里/腾讯/百度/美团/华为真题 + 高频手撕 | 场景题(客服/代码/分析 Agent)、系统设计题、手撕代码 | Day22-27 真题 + Day28 手撕10题 |

### Week4 每日重点速览

| 日期 | 主题 | 核心收获 |
|------|------|---------|
| Day22 | 字节跳动专项 | 场景设计(抖音客服 Agent)、高并发 Agent、推荐+Agent 结合 |
| Day23 | 阿里巴巴专项 | 电商 Agent、多轮对话管理、Agent 中台化、通义千问生态 |
| Day24 | 腾讯百度专项 | 微信生态 Agent、搜索 Agent、文心一言、知识增强 |
| Day25 | 美团华为专项 | 本地生活 Agent、鸿蒙 Agent、端侧部署、隐私计算 |
| Day26 | 系统设计大题 | 百万级 Agent 并发、成本控制、灰度发布、SLA 保障 |
| Day27 | 前沿技术 | Multi-Agent、Self-evolving Agent、Agent OS、世界模型 |
| **Day28** | **手撕冲刺** | **10 道高频手撕题,覆盖 Agent 全栈核心代码** |

---

## 面试速记卡

> 10 道手撕题的核心骨架,面试前快速过一遍。

```
┌─────────────────────────────────────────────────────────────┐
│ 手撕题1: Agent Loop                                          │
│ 骨架: for iter in range(max_iter):                          │
│        check_token_budget()                                 │
│        resp = llm_with_timeout(messages)                    │
│        if not resp.tool_calls: return resp.content          │
│        for tc in resp.tool_calls:                           │
│            result = execute_tool_with_retry(tc)             │
│            messages.append(tool_msg)                        │
│ 安全网: max_iter + token_budget + llm_timeout               │
├─────────────────────────────────────────────────────────────┤
│ 手撕题2: ReAct Agent                                         │
│ 骨架: for step in range(max_steps):                         │
│        output = llm(prompt)                                 │
│        parsed = parse_Thought_Action(output)                │
│        if parsed.final_answer: return it                    │
│        if detect_loop(action_history): return STOP          │
│        obs = execute_tool(action, input)                    │
│        prompt += Thought/Action/Observation                 │
│ 关键: 正则解析 + 死循环检测(deque)                            │
├─────────────────────────────────────────────────────────────┤
│ 手撕题3: 并行工具调用                                         │
│ 骨架: with ThreadPoolExecutor() as ex:                      │
│        futures = {ex.submit(exec, tc): tc for tc in calls}  │
│        for f in as_completed(futures, timeout):             │
│            results[f.call_id] = f.result()                  │
│ 关键: call_id 保序 + 错误隔离 + 双层超时                       │
├─────────────────────────────────────────────────────────────┤
│ 手撕题4: 多策略分块器                                         │
│ 骨架: class ChunkStrategy(Protocol):                        │
│          def chunk(self, text) -> list[str]                 │
│        FixedSize: step = size - overlap                     │
│        Recursive: 分隔符层级递归 ["\n\n","\n","。"," ",""]    │
│        Semantic: 相邻句子相似度 < 阈值则断开                   │
│        Markdown: 按 ^#{1,6} 标题切,超长递归兜底              │
├─────────────────────────────────────────────────────────────┤
│ 手撕题5: 混合检索                                             │
│ 骨架: bm25_results = BM25.search(query, k=10)               │
│        vec_results = Vector.search(query, k=10)             │
│        fused = RRF([bm25, vec], k=60)  # 1/(60+rank)        │
│        reranked = Reranker.rerank(query, fused, k=3)        │
│ 关键: RRF 用排名不用分数 + Reranker 在融合后                   │
├─────────────────────────────────────────────────────────────┤
│ 手撕题6: Agentic RAG                                         │
│ 骨架: strategy = route(question)                            │
│        for iter in range(max_iter):                         │
│            results = retrieve(query, strategy)              │
│            if evaluate(question, results): break            │
│            query = rewrite_query(question, results, reason) │
│        answer = generate(question, all_results)             │
│ 关键: 路由 + 迭代 + 评估 + 改写                                │
├─────────────────────────────────────────────────────────────┤
│ 手撕题7: 上下文管理器                                         │
│ 骨架: budget = {system:10%, user:20%, history:35%,          │
│                retrieval:25%, early:10%}                    │
│        messages = [system, retrieval, compressed_history,   │
│                    user_current]                            │
│ 压缩: 首轮 + 中间摘要 + 最近N轮                                │
│ 优先级: system > user > recent > retrieval > early          │
├─────────────────────────────────────────────────────────────┤
│ 手撕题8: Multi-Agent (Supervisor)                           │
│ 骨架: subtasks = supervisor.decompose(task)                 │
│        while not all_done:                                  │
│            ready = [st for st if deps satisfied]            │
│            parallel_execute(ready)                          │
│            pass_outputs_to_dependents()                     │
│        if quality_check(results): aggregate()               │
│ 关键: 依赖处理(拓扑) + 死锁检测 + 并行就绪任务                   │
├─────────────────────────────────────────────────────────────┤
│ 手撕题9: 安全防护层                                           │
│ 骨架: check_input(速率+过滤) → check_tool(权限+限流)          │
│        → execute → check_output(脱敏+拦截)                   │
│ 速率: 滑动窗口 deque + 时间戳                                 │
│ 权限: role → tool_set 映射(最小权限)                          │
│ 输出: 脱敏(不拦截) vs 有害内容(拦截)                           │
├─────────────────────────────────────────────────────────────┤
│ 手撕题10: 可观测性                                            │
│ 骨架: Tracing: Span树(parent_id + children, 栈维护)          │
│        Logging: 结构化JSON(timestamp+level+context)          │
│        Metrics: Counter + Histogram(p50/p95/p99)            │
│        Alerting: 规则函数 + 阈值触发                          │
│ 优雅: with trace_span("name"): 自动管理生命周期               │
└─────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

> 手撕代码中最容易犯的错误,面试时务必避免。

| # | 易错点 | 错误示例 | 正确做法 |
|---|--------|---------|---------|
| 1 | **Agent Loop 无安全网** | `while True:` 无限循环 | 必须有 `max_iter` + `token_budget` + `timeout` 三重保护 |
| 2 | **工具调用未捕获异常** | `result = tool(**args)` 裸调用 | `try/except` 包裹,异常转为 error 消息返回 LLM |
| 3 | **ReAct 解析顺序错误** | 先解析 Action 再看 Final Answer | 先检查 Final Answer(优先级更高),否则误判 |
| 4 | **并行工具结果乱序** | `for f in as_completed: results.append(f.result())` | 用 `call_id` 索引存储 `results[call_id] = ...` |
| 5 | **RRF 用分数而非排名** | `score += bm25_score + vec_score` | `score += 1/(k+rank)`,只用排名不用原始分数 |
| 6 | **上下文压缩丢弃首轮** | 只保留最近 N 轮 | 首轮(system/首条 user)必须保留,中间摘要,最近完整 |
| 7 | **速率限制用固定窗口** | `if count_in_minute > limit: reject` | 滑动窗口(deque + 时间戳),避免窗口边界突刺 |
| 8 | **Multi-Agent 无死锁检测** | 依赖未满足就死等 | 无就绪任务但仍有未完成 → 报告死锁而非 hang |
| 9 | **Tracing 无父子关系** | 所有 span 平铺 | 用栈维护 `current_span`,新 span 的 parent 是栈顶 |
| 10 | **裸 except 吞异常** | `except: pass` | `except Exception as e: log(e)`,至少记录日志 |

---

## 自测检查清单

### 概念题(10 道)

- [ ] 1. 能口述 Agent Loop 的三重安全网是什么?(迭代/token/超时)
- [ ] 2. 能解释 ReAct 中 Thought/Action/Observation 的循环机制?
- [ ] 3. 能说出并行工具调用中"结果保序"的实现方式?(call_id 索引)
- [ ] 4. 能对比 4 种分块策略的适用场景?(固定/递归/语义/Markdown)
- [ ] 5. 能写出 RRF 公式并解释 k=60 的含义?
- [ ] 6. 能描述 Agentic RAG 的 4 个核心环节?(路由/迭代/评估/改写)
- [ ] 7. 能说出上下文预算分配的优先级顺序?(system>user>recent>retrieval>early)
- [ ] 8. 能解释 Supervisor 模式中依赖处理和死锁检测?
- [ ] 9. 能列出安全防护的 4 个层面?(输入/权限/限流/输出)
- [ ] 10. 能区分 Tracing/Span/Metrics/Logging 的职责?

### 代码题(10 道)

- [ ] 1. 能默写 Agent Loop 的 while 循环骨架(含安全网)?
- [ ] 2. 能写出 ReAct 的正则解析(Thought/Action/Action Input/Final Answer)?
- [ ] 3. 能用 `ThreadPoolExecutor + as_completed` 实现并行工具调用?
- [ ] 4. 能实现递归分块的层级分隔符逻辑?
- [ ] 5. 能写出 BM25 的 TF-IDF 公式 + RRF 融合?
- [ ] 6. 能实现 Agentic RAG 的迭代检索循环(含评估和改写)?
- [ ] 7. 能写出上下文压缩的三段式逻辑(首轮+摘要+最近N轮)?
- [ ] 8. 能用拓扑排序思路实现 Multi-Agent 的依赖调度?
- [ ] 9. 能实现滑动窗口速率限制器(deque + 时间戳)?
- [ ] 10. 能用 `with` 上下文管理器实现自动 Span 管理?

---

## 明日预告

### Day 29 — 模拟面试:项目深挖

明天进入 **Week5:模拟面试与项目**,Day29 主题是**项目深挖模拟面试**:

1. **简历项目包装**:如何把学习项目包装成简历亮点
2. **STAR 法则回答**:Situation-Task-Action-Result 结构化描述项目
3. **技术深挖模拟**:面试官追问"为什么这么设计?""有什么替代方案?"
4. **项目弱点应对**:如何回答"这个项目有什么不足?"
5. **Mock Interview 实战**:模拟 3 轮面试(初筛/技术/总监)

### Week5 整体预告

| 日期 | 主题 |
|------|------|
| Day29 | 模拟面试:项目深挖 |
| Day30 | 模拟面试:系统设计 |
| Day31 | 最终复盘 + 面试策略总览 |

**Week5 目标**:从"会知识"到"会面试",完成知识到表达的最后一公里。

---

> **今日复盘建议**:Day28 是 Week4 收官,也是整个知识体系手撕代码的总集。建议今晚把 10 道手撕题的**核心骨架**(速记卡)默写一遍,不看书能在白纸上写出 7/10 即达标。明天开始进入面试表达训练阶段,知识储备到此基本完成,接下来是"如何讲好"的问题。

**加油,Day28 冲刺完成,距离面试就差最后的表达了!**
