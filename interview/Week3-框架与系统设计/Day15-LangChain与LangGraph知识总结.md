## 核心知识回顾表

| 知识点 | 核心结论 | 面试高频度 |
|--------|----------|-----------|
| **LangChain 五大模块** | Chains / Agents / Memory / Tools / Callbacks,统一于 Runnable 协议 | ★★★★★ |
| **LCEL 管道符** | `__or__` 算子重载,返回 RunnableSequence,顺序执行 | ★★★★☆ |
| **LCEL vs Legacy Chain** | LCEL 原生支持流式/异步/批量/重试/回退,Legacy 已 deprecated | ★★★★☆ |
| **AgentExecutor** | while 循环 + intermediate_steps,已 deprecated | ★★★★☆ |
| **LangGraph 核心概念** | StateGraph / Node / Edge / Conditional Edge / Reducer / Checkpointer | ★★★★★ |
| **Reducer** | 字段合并策略,默认覆盖,`add` 追加,可自定义 | ★★★★☆ |
| **Checkpointer** | 每超步后持久化,支持断点续跑/HITL/Time Travel | ★★★★★ |
| **Conditional Edge** | 路由函数返回值必须映射到节点,实现动态分支 | ★★★★☆ |
| **Supervisor 模式** | 一个调度器 + N 个工人,控制流清晰 | ★★★★☆ |
| **Hierarchical 模式** | 子图作为节点,适合大规模多团队 | ★★★☆☆ |
| **Network 模式** | hand-off 工具,Agent 间点对点,易死循环 | ★★★☆☆ |
| **HITL** | interrupt_before + update_state + invoke(None) 三步走 | ★★★★★ |
| **Time Travel** | get_state_history + update_state,回到任意快照重放 | ★★★★☆ |
| **Memory 三种** | Buffer 全留 / Summary 摘要 / VectorStore 检索 | ★★★★☆ |
| **Memory 趋势** | 0.1+ 推荐 RunnableWithMessageHistory,LangGraph 用 State 替代 | ★★★☆☆ |
| **@tool 装饰器** | docstring → description,类型注解 → args_schema | ★★★★★ |
| **StructuredTool** | Pydantic 显式 schema,支持 Field 约束 | ★★★★☆ |
| **BaseTool** | 类继承,有实例状态,需实现 _run 和 _arun | ★★★☆☆ |
| **ToolException** | handle_tool_error=True 让 LLM 看到错误自适应重试 | ★★★★☆ |
| **工具数量** | 建议 < 10 个,超过 15 个 LLM 决策显著下降 | ★★★☆☆ |

---

## 面试速记卡

```
┌──────────────────────────────────────────────────────────────┐
│                  Day 15 速记卡 (随身复习)                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  【LangChain 五模块】 Chains/Agents/Memory/Tools/Callbacks   │
│  统一抽象: Runnable (invoke/batch/stream/ainvoke)            │
│                                                              │
│  【LCEL 管道符】 | = __or__ 重载 → RunnableSequence           │
│  原语: Passthrough/Lambda/Parallel/Branch/Assign            │
│  优势: 原生流式/异步/批量/重试/回退                          │
│                                                              │
│  【AgentExecutor】 while循环 + intermediate_steps(list)       │
│  停止: AgentFinish / max_iterations / 异常                  │
│  致命缺陷: 状态黑盒/难分支/难回环/难HITL/难多Agent          │
│                                                              │
│  【LangGraph 六概念】                                         │
│  - StateGraph: 有状态有向图                                   │
│  - Node: State → Partial<State> 的纯函数                     │
│  - Edge: 固定跳转                                            │
│  - Conditional Edge: 路由函数 → 动态分支                      │
│  - Reducer: Annotated[list, add] 合并策略                    │
│  - Checkpointer: 每超步持久化 → 断点续跑/HITL/Time Travel    │
│                                                              │
│  【HITL 三步走】                                              │
│  1. interrupt_before=["node"] → 暂停                         │
│  2. update_state(config, {...}) → 注入人工决定                │
│  3. invoke(None, config) → 从断点恢复                        │
│                                                              │
│  【多Agent三模式】                                            │
│  Supervisor: 调度器+工人,清晰但瓶颈                          │
│  Hierarchical: 子图作节点,大规模分团队                       │
│  Network: hand-off 互相转交,灵活但易死循环                   │
│                                                              │
│  【Memory 三种】                                              │
│  Buffer: 全留(短对话)                                       │
│  Summary: LLM摘要压缩(长对话)                              │
│  VectorStore: 检索相关历史(跨session)                       │
│  口诀: 短用Buffer,长用Summary,跨session用Vector             │
│  趋势: 用State+Checkpointer替代,不用Memory类                │
│                                                              │
│  【Tools 三种】                                               │
│  @tool: docstring推断schema(最简)                           │
│  StructuredTool: Pydantic显式schema(生产)                   │
│  BaseTool: 类继承,有状态(复杂)                             │
│  错误: ToolException + handle_tool_error=True               │
│  数量: <10个,超过15个LLM决策显著下降                         │
│                                                              │
│  【面试金句】                                                 │
│  "AgentExecutor 是 while 循环,LangGraph 是有状态有向图"      │
│  "LCEL 不是新DSL,就是Python的__or__重载"                    │
│  "确定性流程用节点,不确定性流程才用LLM决策"                 │
│  "Memory类已停止演进,用State+Checkpointer替代"              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

<details>
<summary>1. Reducer 不写就覆盖,messages 会丢</summary>

**错误**:
```python
class State(TypedDict):
    messages: list        # 没 Annotated,默认覆盖!
```
每个节点返回 `{"messages": [new_msg]}`,框架会**覆盖**而不是追加,最后只剩最后一条。

**正确**:
```python
class State(TypedDict):
    messages: Annotated[list, add]    # 追加
```
这是 LangGraph 新手最常踩的坑,面试中如果让你写代码,一定要写对 Reducer。
</details>

<details>
<summary>2. Conditional Edge 返回值必须是映射里的 key</summary>

```python
g.add_conditional_edges("node", router, {"a": "node_a", "b": "node_b"})
# router 返回 "c" → 报错 KeyError
```
路由函数的返回值必须严格等于映射表的 key,否则运行时报错。这是 LangGraph 的强约束,目的是防止"路由到不存在的节点"。
</details>

<details>
<summary>3. thread_id 必传,否则 Checkpointer 不工作</summary>

```python
# 错误: 不传 thread_id
app.invoke(inputs)
# Checkpointer 不会持久化,状态丢失

# 正确
config = {"configurable": {"thread_id": "user-123"}}
app.invoke(inputs, config=config)
```
thread_id 是 Checkpointer 隔离不同会话的唯一标识,生产环境通常用 `user_id + session_id` 组合。
</details>

<details>
<summary>4. update_state 不会执行图,要继续得 invoke(None)</summary>

```python
app.update_state(config, {"human_decision": "approve"})   # 只改 state
app.invoke(None, config=config)                            # 才会继续执行
```
`update_state` 是纯状态修改,不会触发任何节点执行。要从断点恢复,必须 `invoke(None)`(None 表示不传新输入)。
</details>

<details>
<summary>5. @tool 的 docstring 是 LLM 看到的工具说明,写不好 LLM 不会用</summary>

```python
@tool
def search(q: str) -> str:
    """搜索"""           # 太简略!LLM 不知道什么时候用、怎么用
    ...

@tool
def search(query: str) -> str:
    """在知识库中搜索相关文档。
    适用场景: 用户询问产品功能、政策、流程等事实性问题。
    参数:
        query: 搜索关键词,应为用户问题的核心名词。
    """
    ...
```
docstring 直接影响 LLM 的工具选择准确率,生产环境务必详细写。
</details>

<details>
<summary>6. ToolException 不开 handle_tool_error 会中断 Agent</summary>

```python
@tool
def query_db(sql: str) -> str:
    if invalid(sql):
        raise ToolException("SQL 非法")    # 不开 handle_tool_error → Agent 中断
    ...

# 正确: 开启后 LLM 能看到错误信息并重试
query_db = query_db.with_config(handle_tool_error=True)
```
ToolException 默认行为和普通 Exception 一样会中断,必须显式开启 handle_tool_error。
</details>

<details>
<summary>7. BaseTool 不实现 _arun,异步调用会抛 NotImplementedError</summary>

```python
class MyTool(BaseTool):
    def _run(self, x: str) -> str: ...
    # 没实现 _arun → await tool.ainvoke(...) 报错
```
异步场景必须实现 `_arun`,即使只是 `return await asyncio.to_thread(self._run, ...)`。
</details>

<details>
<summary>8. ConversationSummaryMemory 的 save 是同步阻塞的</summary>

```python
memory = ConversationSummaryMemory(llm=llm)
memory.save_context(inputs, outputs)   # 内部会同步调 LLM 做摘要,阻塞!
```
每次 save 多一次 LLM 调用,延迟翻倍。生产环境要设 `awaitable=True` 走异步,或改用 LangGraph State 自己做摘要。
</details>

<details>
<summary>9. 工具数量过多,LLM 决策准确率显著下降</summary>

研究表明:工具数 < 10 时准确率 > 90%;> 15 时下降到 < 70%;> 30 时 < 50%。
**解法**:
- 用 Toolkit 按场景动态加载;
- 用意图分类先选工具集,再给 Agent;
- 把相似工具合并(如 `search_web` 和 `search_news` 合并为带参数的 `search`)。
</details>

<details>
<summary>10. LangGraph 子图的 State 字段要和父图对齐</summary>

```python
# 父图 State
class ParentState(TypedDict):
    messages: Annotated[list, add]
    user_id: str

# 子图 State (字段少一些可以,但 messages 必须有)
class ChildState(TypedDict):
    messages: Annotated[list, add]    # 必须和父图对齐
```
子图作为父图节点时,State 通过**字段名匹配**自动透传。子图没有的字段会被忽略,但子图输出的字段父图必须有对应位置接收。
</details>

---

## 自测检查清单

### 概念题(10 道)

- [ ] 1. 我能用一句话说清楚 LangChain 五大模块各自的职责,并讲清楚它们的协作数据流。
- [ ] 2. 我能解释 LCEL 的 `|` 管道符底层是 `__or__` 算子重载,返回 RunnableSequence。
- [ ] 3. 我能列出 LCEL 相比 Legacy Chain 的五大优势(流式/异步/批量/重试/回退)。
- [ ] 4. 我能画出 AgentExecutor 的 while 循环伪代码,并说出三种停止条件。
- [ ] 5. 我能讲清楚 AgentExecutor 的四大局限,以及 LangGraph 如何解决。
- [ ] 6. 我能解释 LangGraph 的 State、Node、Edge、Conditional Edge、Reducer、Checkpointer 六个概念。
- [ ] 7. 我能说出 Supervisor / Hierarchical / Network 三种多 Agent 模式的适用场景。
- [ ] 8. 我能对比 ConversationBufferMemory / SummaryMemory / VectorStoreRetrieverMemory 的原理与适用场景。
- [ ] 9. 我能说出 @tool / StructuredTool / BaseTool 三种工具定义方式的区别和选型建议。
- [ ] 10. 我能讲清楚 ToolException + handle_tool_error 的机制,以及为什么生产环境必须开。

### 代码题(3 道)

- [ ] 11. 我能徒手写出一个最小 LangGraph Agent(含 State、Node、Conditional Edge、编译),实现 ReAct 循环。
- [ ] 12. 我能写出 HITL 三步走代码:interrupt_before 暂停 → update_state 注入 → invoke(None) 恢复。
- [ ] 13. 我能写出一个带 Pydantic Schema 和 Field 约束的 StructuredTool,并正确处理 ToolException。

### 系统设计题(2 道)

- [ ] 14. 我能用 LangGraph 设计一个客服 Agent 系统的完整工作流图,包含意图路由、RAG、工单、HITL、满意度。
- [ ] 15. 我能讲清楚客服系统的三层监控(Callbacks 技术指标 / State 业务指标 / CSAT 闭环),以及容量、延迟、成本、可用性的设计取舍。

---

## 延伸阅读

### 官方文档(必读)

1. **LangChain 官方文档 — LCEL**: https://python.langchain.com/docs/concepts/lcel/
   - 重点读 "Runnable protocol" 和 "Why LCEL" 两节

2. **LangGraph 官方文档**: https://langchain-ai.github.io/langgraph/
   - 重点读 Concepts → StateGraph / Persistence / Human-in-the-loop 三章

3. **LangGraph Multi-Agent Tutorial**: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/
   - Supervisor / Hierarchical / Network 三种模式的官方实现

### 关键源码(选读)

4. **LangChain `runnables/base.py`**: 看 `Runnable.__or__` 和 `RunnableSequence.invoke` 的实现,理解 LCEL 本质
   - 路径: `langchain_core/runnables/base.py`

5. **LangGraph `graph/state.py`**: 看 StateGraph 如何用 Reducer 合并 State
   - 路径: `langgraph/graph/state.py`

6. **LangGraph `checkpoint/sqlite.py`**: 看 SqliteSaver 如何序列化/反序列化 State
   - 路径: `langgraph/checkpoint/sqlite.py`

### 论文(加分)

7. **Pregel: A System for Large-Scale Graph Processing**(Google, 2010): LangGraph 的理论根基
   - 重点理解 "superstep" 和 "message passing" 模型

8. **ReAct: Synergizing Reasoning and Acting in Language Models**(Yao et al., 2022): AgentExecutor 的理论根基

9. **AutoGen / CrewAI / OpenAI Swarm 对比**:理解不同多 Agent 框架的设计哲学差异(明日 Day16 会讲)

### 实战资源

10. **LangSmith**: https://smith.langchain.com/
    - 注册账号,跑一遍本地的 LangGraph demo,在 LangSmith 里看 trace,理解"全链路追踪"的价值

11. **LangGraph Studio**: https://github.com/langchain-ai/langgraph-studio
    - 可视化 LangGraph 图,调试时极其有用

12. **langgraph-examples**: https://github.com/langchain-ai/langgraph/tree/main/examples
    - 官方示例库,涵盖 HITL / 多 Agent / 持久化 / Time Travel 各类场景

---

## 明日预告

> **Day 16 — 主流 Agent 框架横评: LangGraph vs AutoGen vs CrewAI vs OpenAI Swarm**

今天我们深入 LangChain + LangGraph 这一对"亲儿子"框架,理解了它们的设计哲学:LangChain 做"积木"(组件标准化),LangGraph 做"编排"(有状态有向图)。但 Agent 框架的江湖远不止 LangChain 一家——明天我们将横向对比四大主流框架:

- **LangGraph**:图驱动,强调可控性与状态管理,适合复杂工作流;
- **AutoGen**(微软):对话驱动,Agent 之间通过 message 交流,适合"多 Agent 讨论"场景;
- **CrewAI**:角色驱动,强调"团队角色分工",API 最简洁,适合快速搭建多角色协作;
- **OpenAI Swarm**:轻量级 hand-off 模式,极简实现,适合理解多 Agent 本质。

明天我们将从**抽象模型、多 Agent 协作、状态管理、HITL、生态、生产成熟度**六个维度做横向对比,并给出"不同场景选哪个框架"的决策树。这是面试中"你为什么选 LangGraph 而不是 AutoGen"这类选型题的核心弹药。

**预习建议**:
- 今天写的 LangGraph 代码再跑一遍,明天对比时会更有体感;
- 浏览 AutoGen 和 CrewAI 的 README,对它们的 API 风格有个初印象;
- 思考一个问题:如果你要做一个"多 Agent 讨论股票投资策略"的系统,你会选哪个框架?为什么?

---

> **Day 15 完** | 今日学习时长: 约 4 小时 | 明日进入 Day 16: 主流 Agent 框架横评
