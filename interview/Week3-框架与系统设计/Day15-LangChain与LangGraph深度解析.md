# Day 15 — LangChain 与 LangGraph 深度解析

> **Week 3 · Day 1** | AI Agent 面试 31 天冲刺计划
> 学习时长建议: 3.5-4.5 小时 | 难度: ★★★★☆ | 面试频率: ★★★★★

## 学习目标

经过 Week 1 的 Agent 基础(ReAct / Function Calling / MCP / 记忆 / 规划)和 Week 2 的 RAG 结合训练,我们已经能从"零"手搓一个 Agent。但真实工程中,绝大多数团队不会从零写 ReAct 循环和状态机,而是依赖成熟的 Agent 框架。Week 3 转向**框架与系统设计**——这是从"能 demo"到"能上线"的关键一跃。

Day 15 作为 Week 3 开篇,聚焦**两个事实上的工业标准框架:LangChain 与 LangGraph**。前者是 LLM 应用最早的"瑞士军刀",后者是 LangChain 团队 2024 年推出的、面向"有状态、可循环、可控"Agent 的新一代编排引擎。完成今天的学习后,你应该能够:

1. 说清楚 LangChain 的五大核心模块(Chains / Agents / Memory / Tools / Callbacks)各自职责与协作关系,并能讲清楚 LCEL 表达式语言的底层实现;
2. 讲明白 Legacy AgentExecutor 是如何驱动 ReAct 循环的,以及为什么 LangChain 官方现在推荐用 LangGraph 替代它;
3. 画出 LangGraph 的 StateGraph / Node / Edge / Conditional Edge / Checkpointer 的概念图,并能解释 Reducer、Channel、Time Travel 这些机制;
4. 用 LangGraph 手写一个带条件分支、人机回环(Human-in-the-loop)、状态持久化的多步骤 Agent 工作流;
5. 用 LangChain + LangGraph 完成一个客服 Agent 系统设计(多轮对话 / 工单创建 / 人工转接 / 质量监控)。

## 面试定位说明

LangChain 是国内面试中**被问得最多、也最容易被问深**的 Agent 框架。面试官常从四个层次切入:

- **概念层**:LangChain 五大模块、LCEL 是什么、为什么要有 LangGraph —— 考察你是否真用过,而不是只看过教程;
- **原理层**:LCEL 管道符的 Runnable 机制、AgentExecutor 的循环驱动、LangGraph 的 Pregel 计算模型 —— 考察你能否讲清楚"框架替你做了什么";
- **取舍层**:为什么 LangGraph 要替代 AgentExecutor?LCEL vs Legacy Chain?Memory 三种方案怎么选 —— 考察你有没有工程判断力;
- **实战层**:手撕 LangGraph 工作流、客服 Agent 系统设计 —— 考察你能不能落地。

今天的 10 道题覆盖这四个层次,务必做到**能讲原理、能写代码、能做选型**。

---

## 今日知识图谱

```
LangChain 与 LangGraph 深度解析 (Day 15)
│
├── 1. LangChain 核心架构
│   ├── Chains (链式调用: Legacy Chain vs LCEL)
│   ├── Agents (Agent + AgentExecutor + ReAct 循环)
│   ├── Memory (Buffer / Summary / VectorStore / KnowledgeGraph)
│   ├── Tools (@tool / StructuredTool / BaseTool / Toolkit)
│   └── Callbacks (BaseCallbackHandler / 事件流 / 追踪)
│
├── 2. LCEL (LangChain Expression Language)
│   ├── Runnable 协议 (invoke / batch / stream / ainvoke)
│   ├── | 管道符 (RunnableSequence + 算子重载)
│   ├── 组合原语 (RunnablePassthrough / RunnableLambda / RunnableBranch)
│   └── 流式与异步 (stream / astream / astream_events)
│
├── 3. AgentExecutor 工作原理
│   ├── ReAct 循环 (Thought → Action → Observation)
│   ├── 停止条件 (max_iterations / early_stopping / finish)
│   ├── 输出解析 (OutputParser / ReActSingleInputOutputParser)
│   └── 局限性 (状态黑盒 / 难分支 / 难回环 / 难人工介入)
│
├── 4. LangGraph 核心概念
│   ├── StateGraph (有状态有向图)
│   ├── Node (节点 = 函数 / Runnable)
│   ├── Edge (普通边 = 固定跳转)
│   ├── Conditional Edge (条件边 = 动态路由)
│   ├── State + Reducer (状态合并策略)
│   ├── Channels (通道 = 通信抽象)
│   └── Checkpointer (状态持久化 + Time Travel)
│
├── 5. LangGraph 多 Agent 协作
│   ├── Supervisor 模式 (一个调度器 + 多个工人)
│   ├── Hierarchical 模式 (多层 Supervisor)
│   ├── Network 模式 (Agent 间互相通信)
│   └── Hand-off 机制 (Agent 之间交接控制权)
│
├── 6. Memory 机制对比
│   ├── ConversationBufferMemory (全量缓存)
│   ├── ConversationSummaryMemory (LLM 摘要压缩)
│   ├── ConversationBufferWindowMemory (滑动窗口)
│   ├── VectorStoreRetrieverMemory (向量检索记忆)
│   └── KnowledgeGraphMemory (知识图谱记忆)
│
├── 7. Tools 自定义开发
│   ├── @tool 装饰器 (docstring 推断 schema)
│   ├── StructuredTool (Pydantic 显式 schema)
│   ├── BaseTool 继承 (完整生命周期)
│   ├── Tool 错误处理 (ToolException + handle_tool_error)
│   └── Toolkit 组合 (工具集合封装)
│
└── 8. 实战
    ├── 手撕 LangGraph 多步 Agent (条件分支 + HITL + 持久化)
    └── 客服 Agent 系统设计 (LangChain + LangGraph)
```

---

## 面试题(共 10 道)

### Q1: LangChain 的核心架构是怎样的?Chains / Agents / Memory / Tools / Callbacks 各自的职责与协作关系?

<details>
<summary>点击展开答案</summary>

**LangChain** 是 2022 年 10 月由 Harrison Chase 开源的 LLM 应用开发框架,目标是把" Prompt 编排 + 模型调用 + 工具使用 + 记忆管理"这些重复劳动标准化。它的核心架构可以归纳为**五大模块 + 一个统一抽象(Runnable)**。

#### 1. 五大核心模块

| 模块 | 职责 | 核心抽象 | 典型类 |
|------|------|----------|--------|
| **Chains** | 把多个步骤(Prompt → LLM → OutputParser)串成一条流水线 | `Chain`(Legacy)/ `Runnable`(LCEL) | `LLMChain`, `SequentialChain`, `RunnableSequence` |
| **Agents** | 让 LLM 自主决定调用哪个工具、调用几次,实现"思考-行动"循环 | `AgentExecutor`, `Agent` | `create_react_agent`, `create_tool_calling_agent` |
| **Memory** | 跨轮次保存对话历史,让"无状态"的 LLM 拥有记忆 | `BaseChatMemory` | `ConversationBufferMemory`, `ConversationSummaryMemory` |
| **Tools** | 把外部能力(API、数据库、计算器)封装成 LLM 可调用的函数 | `BaseTool` | `@tool`, `StructuredTool`, `Tool` |
| **Callbacks** | 在链路各阶段触发钩子,用于日志、追踪、流式输出、监控 | `BaseCallbackHandler` | `StdOutCallbackHandler`, LangSmith Handler |

#### 2. 模块协作关系(数据流视角)

```
用户输入
   │
   ▼
[Memory] ──读取历史──► [Chain / Agent]
                          │
                          ├──► [Prompt] 组装(含历史 + 工具描述)
                          │
                          ▼
                       [LLM] 调用模型
                          │
                ┌─────────┴─────────┐
                │                   │
        直接回答              决定调用工具
                │                   │
                │                   ▼
                │             [Tools] 执行
                │                   │
                │       ┌───────────┘
                │       ▼ (Observation 回灌)
                │     [LLM] 再次思考 ...
                │       (ReAct 循环)
                │                   │
                └─────► 最终输出 ◄──┘
                          │
                  [Callbacks] 全程触发
                          │
                  [Memory] 写入新历史
                          │
                          ▼
                       返回用户
```

#### 3. 统一抽象:Runnable

LangChain 0.1 之后,所有模块都被统一为 `Runnable` 协议,提供四套标准接口:

- `invoke(input)`:单次同步调用
- `batch(inputs)`:批量并发调用
- `stream(input)`:流式输出 token
- `ainvoke / abatch / astream`:异步版本

这意味着 `Prompt | LLM | OutputParser` 这种管道式组合成为可能(LCEL),所有模块可以像 Unix 管道一样拼接。

#### 4. 面试金句

> "LangChain 的本质是把 LLM 应用的四个高频动作——编排、记忆、工具、观测——标准化。五大模块是表面,真正统一它们的是 Runnable 协议:任何模块只要实现了 invoke/batch/stream,就能用 `|` 管道自由组合。这也是 LCEL 能取代 Legacy Chain 的根本原因。"

#### 5. 易混淆点

- **Chain 不等于 Agent**:Chain 是固定流水线(步骤写死),Agent 是动态决策(LLM 决定下一步)。Agent 内部通常包了一个 Chain。
- **Memory 不是必须的**:单轮 QA 不需要 Memory;多轮对话才需要。Memory 是 LangChain 的可插拔模块。
- **Callbacks 是横切的**:它不属于任何单一模块,而是在整条链路上广播事件,常用于接 LangSmith 做追踪。

</details>

### Q2: LCEL (LangChain Expression Language) 的原理是什么? `|` 管道符是如何实现的? 它与 Legacy Chain 有什么本质区别?

<details>
<summary>点击展开答案</summary>

**LCEL(LangChain Expression Language)** 是 LangChain 0.1 引入的声明式编排语法,允许用 `prompt | model | parser` 这种 Unix 管道风格组合组件。它的底层是 **Runnable 协议 + Python 的 `__or__` 算子重载**。

#### 1. `|` 管道符的实现机制

LCEL 的魔法在于 `Runnable.__or__` 和 `Runnable.__ror__` 两个 dunder 方法:

```python
# langchain_core/runnables/base.py (简化版)
class Runnable:
    def __or__(self, other):
        # self | other  →  RunnableSequence(self, other)
        return RunnableSequence(self, other)

    def __ror__(self, other):
        # other | self  →  RunnableSequence(coerce(other), self)
        return RunnableSequence(coerce_to_runnable(other), self)
```

当 Python 解析 `prompt | model | parser` 时,等价于:

```python
RunnableSequence(
    RunnableSequence(prompt, model),
    parser
)
```

`RunnableSequence` 内部维护一个 `steps: List[Runnable]`,调用 `invoke` 时依次把上一步的输出作为下一步的输入:

```python
class RunnableSequence(Runnable):
    def invoke(self, input, config=None):
        for step in self.steps:
            input = step.invoke(input, config)
        return input
```

这就是 LCEL 的全部魔法——**算子重载 + 顺序执行**。没有 DSL 解析器,没有 AST,纯 Python 语法糖。

#### 2. Runnable 协议的核心接口

```python
class Runnable:
    def invoke(self, input, config=None) -> Output: ...
    def batch(self, inputs, config=None) -> List[Output]: ...
    def stream(self, input, config=None) -> Iterator[Output]: ...
    async def ainvoke(self, input, config=None) -> Output: ...
    async def astream(self, input, config=None) -> AsyncIterator[Output]: ...
    def with_config(self, config): ...           # 注入配置
    def with_fallbacks(self, fallbacks): ...      # 容错降级
    def with_retry(self, retry_if): ...           # 重试
    def bind(self, **kwargs): ...                 # 绑定参数(如 tools)
    def assign(self, **kwargs): ...               # 给 dict 输入追加字段
```

#### 3. LCEL 的组合原语

| 原语 | 作用 | 典型用法 |
|------|------|----------|
| `RunnablePassthrough` | 透传输入,常用于保留原 query | `{"context": retriever, "question": RunnablePassthrough()}` |
| `RunnableLambda` | 把任意函数包装成 Runnable | `RunnableLambda(lambda x: x["text"])` |
| `RunnableParallel` | 并行执行多个 Runnable | `RunnableParallel(a=chain_a, b=chain_b)` |
| `RunnableBranch` | 条件路由(类似 switch) | `RunnableBranch([(cond1, chain1), (cond2, chain2)], default)` |
| `RunnableAssign` | 给 dict 输入追加字段 | `.assign(generated=llm)` |
| `RunnableWithMessageHistory` | 自动注入对话历史 | 给 chain 包一层 Memory |

#### 4. 一个完整 RAG 示例(LCEL 写法)

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

retriever = vectorstore.as_retriever()
prompt = ChatPromptTemplate.from_template("根据以下上下文回答问题:\n{context}\n\n问题: {question}")
llm = ChatOpenAI(model="gpt-4o")

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 流式输出
for chunk in rag_chain.stream("LangGraph 和 AgentExecutor 有什么区别?"):
    print(chunk, end="", flush=True)
```

注意第一行的 `dict | prompt`:dict 的每个 value 都会被 coerce 成 Runnable,并行执行,然后把结果组装成 dict 喂给 prompt。这是 LCEL 最优雅的地方。

#### 5. LCEL vs Legacy Chain 的本质区别

| 维度 | Legacy Chain (`LLMChain` 等) | LCEL (`prompt | llm | parser`) |
|------|------------------------------|--------------------------------|
| **组合方式** | 类继承 + 显式 `SequentialChain` | 管道符 `|`,声明式 |
| **流式支持** | 需要单独实现,多数不支持 | 原生 `stream()` / `astream()` |
| **异步支持** | 部分有 `arun`,不统一 | 原生 `ainvoke` / `abatch` |
| **批处理** | 需手动循环 | 原生 `batch()` 自动并发 |
| **回退与重试** | 手动 try/except | `.with_fallbacks()` / `.with_retry()` |
| **可观测性** | 需自己埋点 | 所有 Runnable 自动触发 Callback 事件 |
| **类型推断** | 弱,多为 Any | 较强,Input/Output Type 可声明 |
| **状态** | Chain 内部可变状态多 | 倾向无状态,状态交给 LangGraph |
| **官方态度** | 0.1 起标记 deprecated | 主推,长期演进 |

#### 6. 面试金句

> "LCEL 不是一门新的 DSL,它就是 Python。`|` 管道符本质是 `Runnable.__or__` 的算子重载,返回一个 `RunnableSequence`,invoke 时顺序执行。LCEL 相比 Legacy Chain 的核心优势是'统一了流式、异步、批量、重试、回退'五大能力——Legacy Chain 你得自己写,LCEL 是 Runnable 协议自带的。"

#### 7. 易错点

- **`|` 优先级**:Python 中 `|` 的优先级低于比较运算符但高于 `and/or`,组合时建议用括号。
- **dict 不是 Runnable**:但 LCEL 会自动用 `RunnableParallel` 包裹 dict 的每个 value。
- **流式不等于 token 流**:`stream()` 输出的是每个 Runnable 的中间结果流,LLM 节点才是 token 流,其他节点通常是单个 chunk。

</details>

### Q3: LangChain 的 Agent Executor 是如何工作的? 它如何驱动 ReAct 循环? 为什么官方现在推荐用 LangGraph 替代它?

<details>
<summary>点击展开答案</summary>

**AgentExecutor** 是 LangChain 早期实现 Agent 的核心类,它本质上是一个**while 循环 + 输出解析 + 工具调度器**。其工作原理可以拆成"循环体 + 停止条件 + 解析器"三部分。

#### 1. AgentExecutor 的核心循环(Python 伪代码)

```python
class AgentExecutor(Chain):
    def _call(self, inputs):
        intermediate_steps = []      # [(AgentAction, observation), ...]
        iterations = 0
        while iterations < self.max_iterations:
            # 1. 让 Agent 决定下一步
            output = self.agent.plan(
                inputs,
                intermediate_steps=intermediate_steps,
            )
            # 2. 判断是否结束
            if isinstance(output, AgentFinish):
                return output.return_values  # 返回最终答案
            # 3. 否则执行工具
            action: AgentAction = output
            observation = self.tool.run(
                action.tool,
                action.tool_input,
            )
            # 4. 累积步骤,进入下一轮
            intermediate_steps.append((action, observation))
            iterations += 1
        # 5. 超过最大迭代次数,触发 early stopping
        return self._return(self.handle_early_stop(intermediate_steps))
```

#### 2. ReAct 循环的四个阶段

```
┌─────────────────────────────────────────────────┐
│  1. Thought (思考)                              │
│     LLM 看到 [系统 Prompt + 工具描述 + 历史]    │
│     输出: "我需要先查天气"                       │
│                                                  │
│  2. Action (行动)                               │
│     OutputParser 解析出 tool_name + tool_input  │
│     例如: Action: get_weather                   │
│           Action Input: {"city": "北京"}         │
│                                                  │
│  3. Observation (观察)                          │
│     ToolExecutor 执行工具,返回结果              │
│     例如: Observation: 晴, 25°C                 │
│                                                  │
│  4. 回到 1,直到 LLM 输出 Final Answer          │
└─────────────────────────────────────────────────┘
```

#### 3. Agent 的两种实现风格

| Agent 类型 | Prompt 格式 | 输出解析 | 适用模型 |
|-----------|-------------|----------|----------|
| **ReAct (text)** | `Thought: ...\nAction: ...\nAction Input: ...` | 正则解析文本 | 旧模型、开源模型 |
| **Tool Calling (function calling)** | 模型原生 function calling API | 解析 `tool_calls` 字段 | GPT-4 / Claude / Qwen 等支持 FC 的模型 |

LangChain 0.2 起,**Tool Calling Agent 是默认推荐方式**,因为它不依赖正则解析,更稳定。

#### 4. 停止条件

AgentExecutor 有三种停止方式:

1. **AgentFinish**:LLM 主动输出"Final Answer",AgentExecutor 返回结果;
2. **max_iterations**:超过最大迭代次数(默认 15),触发 `handle_early_stopping_method`;
3. **max_execution_time**:超过最大执行时间(可选);
4. **抛出异常**:工具异常未被捕获,或 OutputParser 解析失败。

#### 5. AgentExecutor 的四大局限

这是面试重点——**为什么 LangChain 官方在 2024 年开始推荐用 LangGraph 替代 AgentExecutor?**

| 局限 | 表现 | LangGraph 的解法 |
|------|------|------------------|
| **状态黑盒** | `intermediate_steps` 是个 list,无法表达结构化状态(如"已下单"、"待审核") | StateGraph 用 TypedDict 显式定义 State |
| **难以分支** | 只能"工具 → 回到 LLM"线性循环,无法根据状态走不同节点 | Conditional Edge 动态路由 |
| **难以回环** | 无法表达"审核失败 → 回到上一步修改"这种非线性流程 | 图结构天然支持任意回环 |
| **难以人工介入** | 没有内置的"暂停-等待-恢复"机制 | Checkpointer + interrupt 实现 HITL |
| **难以多 Agent** | 单 Agent 单循环,多 Agent 需要嵌套 Executor,很别扭 | LangGraph 原生支持多 Agent 图 |
| **难以并行** | 工具只能串行调用(除非手动写 future) | Node 可以 fan-out 并行 |

LangChain 官方文档原话:
> "AgentExecutor is deprecated in favor of LangGraph. While AgentExecutor will not be removed in the near future, it is not recommended for new development."

#### 6. 面试金句

> "AgentExecutor 本质是一个 while 循环:让 LLM 看历史决定下一步,执行工具,把结果塞回 intermediate_steps,直到 LLM 输出 Final Answer 或超过 max_iterations。它的致命问题是'状态只有一个 list',无法表达结构化状态、条件分支、人工介入和多 Agent 协作——这正是 LangGraph 用'有状态有向图'来替代它的根本动机。"

#### 7. 易错点

- **Agent ≠ AgentExecutor**:`Agent` 负责"决定下一步"(生成 AgentAction/AgentFinish),`AgentExecutor` 负责"执行循环 + 调度工具"。两者是分离的。
- **max_iterations 不是"工具调用次数"**:它是"LLM 思考次数",一次思考可能不调用工具(Final Answer)。
- **early stopping 默认返回字符串**:不一定是好答案,生产环境需要自定义 `handle_early_stopping_method`。

</details>

### Q4: LangGraph 的核心概念有哪些? StateGraph / Nodes / Edges / Conditional Edge / Channels / Checkpointer 分别是什么? 与 Agent Executor 的本质区别?

<details>
<summary>点击展开答案</summary>

**LangGraph** 是 LangChain 团队 2024 年 1 月开源的"有状态、可循环、可控"的 Agent 编排引擎。它的核心思想是:**把 Agent 建模成一张有状态的有向图(StateGraph)**,而不是一个 while 循环。其灵感来自 Google Pregel 论文的"图计算 + 超步(Superstep)"模型。

#### 1. 六大核心概念

##### (1) StateGraph — 有状态有向图

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]   # Reducer: 追加而非覆盖
    next: str                         # 下一个节点
    retry_count: int

graph = StateGraph(AgentState)
```

StateGraph 把状态作为"一等公民":每个节点都接收 State、返回 State 的部分更新,框架用 Reducer 合并。

##### (2) Node — 节点(函数 / Runnable)

```python
def call_llm(state: AgentState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}   # 返回更新,Reducer 会追加

graph.add_node("llm", call_llm)
graph.add_node("tool", call_tool)
graph.add_node("human_review", human_review)
```

Node 就是一个 `State -> Partial<State>` 的函数,或一个 Runnable。它**只关心"我接收什么、输出什么"**,不关心"我从哪来、到哪去"——这是图解耦的关键。

##### (3) Edge — 普通边(固定跳转)

```python
graph.add_edge(START, "llm")
graph.add_edge("tool", "llm")        # 工具执行后回到 LLM
graph.add_edge("llm", END)           # 默认情况,LLM 后结束
```

普通边是"硬编码"的跳转,适合确定性流程。

##### (4) Conditional Edge — 条件边(动态路由)

```python
def should_continue(state: AgentState) -> str:
    last_msg = state["messages"][-1]
    if last_msg.tool_calls:
        return "tool"
    return END

graph.add_conditional_edges(
    "llm",                            # 源节点
    should_continue,                  # 路由函数
    {                                 # 路由映射
        "tool": "tool",
        END: END,
    },
)
```

条件边是 LangGraph 的灵魂——它让"LLM 决定下一步"变成图的一等公民。`should_continue` 就是 AgentExecutor 里 LLM 决策的逻辑,但被显式建模为图的边。

##### (5) Channels / Reducer — 状态合并策略

```python
from operator import add
from typing import Annotated

class State(TypedDict):
    messages: Annotated[list, add]        # 追加: 新旧 list 拼接
    counter: int                            # 覆盖: 默认行为
    votes: Annotated[dict, dict_merge]      # 字典合并
```

- **Channel** 是状态的"槽位",每个字段是一个 Channel;
- **Reducer** 是 Channel 的合并函数:节点返回 `{"messages": [new_msg]}` 时,框架用 `add` 把它追加到原 list,而不是覆盖。这是 LangGraph 处理"多节点并发更新同一字段"的关键机制。
- 不指定 Reducer 时默认是"覆盖"(last-write-wins)。

##### (6) Checkpointer — 状态持久化 + Time Travel

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("agent.db")
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"],   # 人机回环: 进入节点前暂停
)

# 每次调用都会自动 checkpoint
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(inputs, config=config)

# Time Travel: 回到任意历史快照
history = list(app.get_state_history(config))
app.invoke(None, config={**config, "checkpoint_id": history[3].config["configurable"]["checkpoint_id"]})
```

Checkpointer 在**每个超步(Superstep)结束后**把完整 State 序列化到存储(SQLite / Postgres / Redis),带来三个能力:

1. **断点续跑**:进程崩溃后从最近 checkpoint 恢复;
2. **人机回环(HITL)**:`interrupt_before` / `interrupt_after` 在指定节点暂停,等人工审核后 `invoke(None)` 恢复;
3. **Time Travel**:可以回到任意历史快照,修改 State 后从该点重新执行(用于调试、A/B 实验)。

#### 2. LangGraph vs AgentExecutor 的本质区别

| 维度 | AgentExecutor | LangGraph |
|------|---------------|-----------|
| **抽象模型** | while 循环 + intermediate_steps list | 有状态有向图 (StateGraph) |
| **状态** | 隐式 (list of (action, obs)) | 显式 (TypedDict + Reducer) |
| **分支** | 难,只能回到 LLM | Conditional Edge 原生支持 |
| **回环** | 单一循环 | 任意回环 |
| **并行** | 难 | Node 可 fan-out / fan-in |
| **人工介入** | 无内置 | interrupt + Checkpointer |
| **持久化** | 无 | Checkpointer (SQLite/Postgres) |
| **多 Agent** | 嵌套 Executor | 子图 / Supervisor / Hierarchical |
| **可观测性** | Callbacks | 状态快照 + Time Travel + LangSmith |
| **理论根基** | ReAct 论文 | Pregel 图计算 + Actor 模型 |
| **官方推荐** | deprecated | 主推 |

#### 3. 一个最小 LangGraph Agent(对比 ReAct)

```python
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage
from typing import TypedDict, Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]

def call_model(state):
    return {"messages": [llm.bind_tools(tools).invoke(state["messages"])]}

def should_continue(state):
    return "tools" if state["messages"][-1].tool_calls else END

g = StateGraph(State)
g.add_node("agent", call_model)
g.add_node("tools", ToolNode(tools))
g.add_edge(START, "agent")
g.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
g.add_edge("tools", "agent")    # 工具执行后回到 agent

app = g.compile()
result = app.invoke({"messages": [HumanMessage("北京天气怎么样?")]})
```

注意:这段代码功能上等价于 AgentExecutor,但**所有状态、所有跳转都是显式的**——这是 LangGraph 的核心价值。

#### 4. 面试金句

> "LangGraph 把 Agent 从'while 循环'升级为'有状态有向图'。State 是一等公民(TypedDict + Reducer),节点是 `State -> Partial<State>` 的纯函数,边分为普通边和条件边。Checkpointer 在每个超步后持久化状态,带来断点续跑、人机回环、Time Travel 三大能力。它的本质优势是'把 Agent 的控制流从代码里的 while 变成图里的边',于是分支、回环、并行、多 Agent、人工介入都成了图的天然能力。"

#### 5. 易错点

- **State 必须是 TypedDict**:否则 Reducer 注解(Annotated)无法生效。
- **Reducer 不是默认追加**:不写 `Annotated[list, add]` 就是覆盖,这是新手最常踩的坑。
- **Conditional Edge 的返回值必须是映射里的 key**:否则报错,这是为了避免"路由到不存在的节点"。
- **Checkpointer 按 thread_id 隔离**:不传 thread_id 不会持久化,这是多用户隔离的关键。

</details>

### Q5: LangGraph 如何实现多 Agent 协作? Supervisor / Hierarchical / Network 三种模式各自适合什么场景?

<details>
<summary>点击展开答案</summary>

多 Agent 协作是 LangGraph 相对 AgentExecutor 最显著的差异化能力。LangGraph 官方提供三种经典模式,都在 `langgraph-supervisor` / `langgraph-swarm` 等库里有预置实现。

#### 1. 三种模式概览

```
模式一: Supervisor (单层调度)
                ┌──► Agent A (搜索)
   Supervisor ──┼──► Agent B (写作)
   (调度器)     └──► Agent C (校对)

模式二: Hierarchical (多层调度)
                ┌──► [Sub-Supervisor 1] ──┬──► Agent A
   Supervisor ──┤                          └──► Agent B
   (顶层)       └──► [Sub-Supervisor 2] ──┬──► Agent C
                                          └──► Agent D

模式三: Network (网状协作)
   Agent A ◄────► Agent B
      ▲               ▲
      │               │
      ▼               ▼
   Agent C ◄────► Agent D
   (任意 Agent 可把控制权交给任意其他 Agent)
```

#### 2. Supervisor 模式 — 单层调度器

**结构**:一个 Supervisor Agent + N 个 Worker Agent。Supervisor 是"路由器",根据当前任务决定下一步交给哪个 Worker,Worker 完成后回到 Supervisor。

**典型实现**:

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]
    next: str

# Supervisor: LLM 看历史决定路由
def supervisor(state):
    prompt = f"""你是调度器。根据当前对话,决定下一步交给哪个 Agent:
    - "researcher": 需要查资料
    - "writer": 需要写文章
    - "reviewer": 需要校对
    - "FINISH": 任务完成
    当前对话: {state["messages"]}
    返回一个 JSON: {{"next": "agent_name"}}"""
    decision = llm.invoke(prompt)
    return {"next": parse_json(decision)["next"]}

def researcher(state):
    return {"messages": [research_agent.invoke(state["messages"])]}

def writer(state):
    return {"messages": [write_agent.invoke(state["messages"])]}

def reviewer(state):
    return {"messages": [review_agent.invoke(state["messages"])]}

def route(state):
    return state["next"]

g = StateGraph(State)
g.add_node("supervisor", supervisor)
g.add_node("researcher", researcher)
g.add_node("writer", writer)
g.add_node("reviewer", reviewer)

g.add_edge(START, "supervisor")
g.add_conditional_edges("supervisor", route, {
    "researcher": "researcher",
    "writer": "writer",
    "reviewer": "reviewer",
    "FINISH": END,
})
# 每个 worker 完成后回到 supervisor
g.add_edge("researcher", "supervisor")
g.add_edge("writer", "supervisor")
g.add_edge("reviewer", "supervisor")

app = g.compile()
```

**适合场景**:
- 任务可拆成 N 个**职责清晰的子角色**(研究、写作、校对);
- Supervisor 的决策成本可接受(每次都要调一次 LLM);
- Agent 之间**不需要直接通信**,只跟 Supervisor 汇报。

**优点**:控制流清晰、可观测、易调试。
**缺点**:Supervisor 是单点瓶颈和延迟瓶颈;Worker 之间无法直接协作。

#### 3. Hierarchical 模式 — 多层调度

**结构**:把 Supervisor 套娃——顶层 Supervisor 管几个 Sub-Supervisor,每个 Sub-Supervisor 再管自己的 Worker 团队。每个 Sub-Supervisor 本身是一个子图(Subgraph)。

**典型场景**:大型复杂任务,例如"做一份行业研究报告":
- 顶层 Supervisor 决定:数据收集 / 分析 / 报告撰写;
- "数据收集" Sub-Supervisor 再决定:爬虫 / 数据库查询 / 问卷;
- "分析" Sub-Supervisor 决定:统计分析 / 案例分析 / 趋势预测。

```python
# 子图: 数据收集团队
data_team = build_data_team_graph()      # 返回一个 CompiledGraph
# 子图: 分析团队
analysis_team = build_analysis_team_graph()

# 顶层图
g = StateGraph(State)
g.add_node("top_supervisor", top_supervisor)
g.add_node("data_team", data_team)         # 子图直接作为节点
g.add_node("analysis_team", analysis_team)
g.add_node("writer", writer)

g.add_edge(START, "top_supervisor")
g.add_conditional_edges("top_supervisor", route, {
    "data": "data_team",
    "analysis": "analysis_team",
    "write": "writer",
    "FINISH": END,
})
g.add_edge("data_team", "top_supervisor")
g.add_edge("analysis_team", "top_supervisor")
g.add_edge("writer", "top_supervisor")
```

**关键点**:LangGraph 的子图(CompiledGraph)可以**直接作为节点**加入父图,State 通过字段名对齐自动透传。这是 Hierarchical 模式的基础。

**适合场景**:
- 任务规模大,单层 Supervisor 决策维度过多;
- 团队职责有天然层级(产品 → 前端 / 后端 / 测试);
- 需要把不同团队的工具、Prompt、Memory 隔离。

**缺点**:调试复杂、延迟叠加(每层 Supervisor 一次 LLM 调用)、State 传递要小心字段冲突。

#### 4. Network 模式 — 网状协作

**结构**:没有中央 Supervisor,任何 Agent 都可以把控制权"递交"(hand-off)给任何其他 Agent。这是 OpenAI Swarm 论文推广的模式,LangGraph 在 `langgraph-swarm` 库里实现。

**核心机制 — Hand-off Tool**:

```python
def make_handoff_tool(target_agent: str):
    @tool
    def handoff(task: str) -> str:
        """把当前任务交给 {target_agent} 处理。
        Args:
            task: 需要交接的任务描述
        """
        return f"HANDOFF_TO:{target_agent}:{task}"
    return handoff

# 每个 Agent 都把其他 Agent 的 handoff 工具挂上
agent_a_tools = [search_tool, make_handoff_tool("agent_b"), make_handoff_tool("agent_c")]

def route_handoff(state):
    last = state["messages"][-1]
    if isinstance(last, ToolMessage) and last.content.startswith("HANDOFF_TO:"):
        _, target, _ = last.content.split(":", 2)
        return target
    return END
```

**适合场景**:
- Agent 之间需要**点对点直接协作**(客服 → 技术 → 客服,不需要回到中央);
- 任务流是**动态、非结构化**的,无法预先设计层级;
- 对延迟敏感(省掉 Supervisor 这一跳)。

**缺点**:容易"Agent 之间互相踢皮球"无限循环;可观测性差;调试困难。需要明确的终止条件(如 max_iterations 或 "FINISH" 工具)。

#### 5. 三种模式对比

| 维度 | Supervisor | Hierarchical | Network |
|------|-----------|--------------|---------|
| **结构** | 一对多 | 树形 | 网状 |
| **决策中心** | 单一 Supervisor | 多层 Supervisor | 无中心,Agent 自决 |
| **延迟** | 中(每轮 1 次 Supervisor LLM) | 高(每层 1 次) | 低(无 Supervisor) |
| **可观测** | 强 | 中 | 弱 |
| **可控性** | 强 | 中 | 弱 |
| **扩展性** | 中(Supervisor 负担重) | 强(分层扩展) | 强(点对点) |
| **典型场景** | 研究员-写作员-校对员 | 大型项目多团队协作 | 客服多技能切换 |
| **死循环风险** | 低(Supervisor 把控) | 低 | 高(需明确终止) |
| **实现复杂度** | 低 | 中 | 高 |

#### 6. 面试金句

> "LangGraph 多 Agent 协作有三种模式。Supervisor 是'调度器+工人',适合职责清晰、Worker 不需要直接通信的场景,控制流清晰但 Supervisor 是延迟瓶颈。Hierarchical 是 Supervisor 套娃,适合大型任务分团队,子图可直接作为父图节点。Network 是 Agent 之间互相 hand-off,适合点对点动态协作,但容易死循环。选型口诀:'职责清选 Supervisor,规模大选 Hierarchical,要灵活选 Network 但必加终止条件'。"

#### 7. 易错点

- **Supervisor 也要有 FINISH 出口**:否则图永远到不了 END,会超时。
- **Hierarchical 子图的 State 字段要和父图对齐**:否则子图收不到父图的输入。
- **Network 模式必须设置 max_iterations**:Agent 互相 hand-off 容易死循环。
- **不要把所有工具给所有 Agent**:会让 LLM 决策困难,职责模糊——这是新手最常犯的"工具膨胀"问题。

</details>

### Q6: LangGraph 的状态管理机制是怎样的? State / Reducer / Channels / Checkpointing / Time Travel 分别如何工作?

<details>
<summary>点击展开答案</summary>

状态管理是 LangGraph 区别于所有其他 Agent 框架的核心竞争力。它把"状态"从 AgentExecutor 里的隐式 list 提升为**一等公民**,并提供 Reducer 合并、Checkpointer 持久化、Time Travel 时间旅行三大能力。

#### 1. State — 显式状态定义

```python
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]              # 对话历史,追加
    retrieved_docs: Annotated[list, add]        # 检索文档,追加
    user_id: str                                  # 用户ID,覆盖
    retry_count: int                              # 重试计数,覆盖
    pending_approval: dict                        # 待审批内容,覆盖
```

State 必须是 `TypedDict`(或 Pydantic Model),原因有二:
- Python 的类型注解让 Reducer 可以挂在字段上(`Annotated[list, add]`);
- 框架据此做 schema 校验和序列化。

**关键设计**:State 是"全局共享的",所有节点都能读写,但每个节点只返回**部分更新**,框架负责合并。

#### 2. Reducer — 状态合并策略

Reducer 回答的问题是:**当节点返回 `{"messages": [new_msg]}` 时,如何把它和现有 State 的 `messages` 合并?**

| Reducer | 行为 | 适用场景 |
|---------|------|----------|
| 默认(无注解) | 覆盖(last-write-wins) | 标量字段:user_id, retry_count |
| `operator.add` | 列表追加 / 字典合并 | 对话历史、检索结果累积 |
| 自定义函数 | 任意合并逻辑 | 去重、按 ID 更新、最大值 |

**自定义 Reducer 示例 — 按 ID 去重更新**:

```python
def merge_by_id(existing: list, new: list) -> list:
    by_id = {item["id"]: item for item in (existing or [])}
    for item in new:
        by_id[item["id"]] = item     # 同 ID 覆盖
    return list(by_id.values())

class State(TypedDict):
    documents: Annotated[list, merge_by_id]
```

**Reducer 在并行节点的作用**:当两个节点同时更新 `messages` 时,没有 Reducer 会"后写覆盖前写"丢数据;有 `add` Reducer 会把两边的输出都追加进去。这是 LangGraph 支持 fan-out 并行的关键。

#### 3. Channels — 通信通道抽象

Channel 是 Reducer 的"底层抽象"。LangGraph 内部把每个 State 字段实现为一个 Channel,有 `update` 和 `get` 两个操作。普通用户不需要直接操作 Channel,但理解它有助于看懂源码。

```python
# 概念上等价:
class Channel:
    value: Any
    reducer: Callable
    def update(self, new): self.value = self.reducer(self.value, new)
    def get(self): return self.value
```

特殊 Channel 类型:
- `LastValue`:默认 Channel,覆盖语义;
- `Topic`:发布订阅,用于多 Agent 通信;
- `BinaryOperatorAggregate`:自定义 Reducer 的通用 Channel。

#### 4. Checkpointing — 状态持久化

Checkpointer 在**每个 Superstep(超步)结束后**自动把完整 State 序列化到存储。

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver

# 生产环境用 Postgres
checkpointer = PostgresSaver.from_conn_string("postgresql://...")
app = graph.compile(checkpointer=checkpointer)

# 用 thread_id 隔离不同会话
config = {"configurable": {"thread_id": "user-123-session-1"}}
result = app.invoke(inputs, config=config)
```

**Checkpoint 的内容**:
- 完整 State 快照;
- 当前所在节点;
- 下一步要执行的边;
- 元数据(时间戳、版本)。

**存储后端对比**:

| 后端 | 适合场景 | 持久性 | 性能 |
|------|----------|--------|------|
| `MemorySaver` | 开发调试 | 进程内,重启丢 | 最快 |
| `SqliteSaver` | 单机生产 | 文件持久 | 中 |
| `PostgresSaver` | 分布式生产 | 强持久 | 中(需连接池) |
| `RedisSaver` | 高频短会话 | 可配置 TTL | 最快(持久化版) |

#### 5. Time Travel — 时间旅行

由于每个超步都有 Checkpoint,LangGraph 可以**回到任意历史快照**,从该点重新执行或继续。

```python
config = {"configurable": {"thread_id": "session-1"}}
app.invoke(inputs, config=config)

# 列出所有历史快照
states = list(app.get_state_history(config))
for i, s in enumerate(states):
    print(f"[{i}] node={s.next}, msgs={len(s.values['messages'])}")

# 回到第 3 个快照,修改 messages 后重新执行
target = states[3]
new_config = target.config                      # 包含 checkpoint_id
app.update_state(new_config, {"messages": [HumanMessage("换个问法: ...")]})
# 从该 checkpoint 继续执行
result = app.invoke(None, config=new_config)
```

**Time Travel 的三大用途**:
1. **调试**:回放某次执行,定位哪一步出错;
2. **A/B 实验**:从同一分叉点用不同参数跑两条;
3. **分支探索**:让 Agent 回到决策点,尝试不同路径(类似 AlphaZero 的 MCTS)。

#### 6. interrupt — 人机回环(HITL)

Checkpointer + interrupt 是 LangGraph 实现 HITL 的核心机制:

```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review"],   # 进入该节点前暂停
)

config = {"configurable": {"thread_id": "t1"}}
# 第一次调用:执行到 human_review 前暂停
app.invoke(inputs, config=config)

# 人工审核,可能修改 state
state = app.get_state(config)
if needs_edit(state.values):
    app.update_state(config, {"messages": [HumanMessage("改成...")]})

# 恢复执行
app.invoke(None, config=config)          # 传 None 表示从断点继续
```

**工作原理**:`interrupt_before` 让编译后的图在指定节点之前"暂停",此时 Checkpointer 已保存当前 State。`invoke(None)` 表示"不传新输入,从当前 checkpoint 继续",框架会从下一个节点开始执行。

#### 7. 完整状态管理流程图

```
用户调用 app.invoke(inputs, config={thread_id})
       │
       ▼
[加载该 thread_id 的最新 checkpoint] (如果有)
       │
       ▼
[执行 Superstep 1: Node A]
       │
       ▼
[Checkpoint 1 保存] ◄── 自动持久化
       │
       ▼
[执行 Superstep 2: Node B]
       │
       ▼
[Checkpoint 2 保存]
       │
       ▼
[... 直到 END 或 interrupt]
       │
       ▼
[最终 State] + 完整 Checkpoint 历史
       │
       ▼
可 Time Travel / 可 resume / 可 replay
```

#### 8. 面试金句

> "LangGraph 的状态管理有三层。第一层是 State(TypedDict)+ Reducer(Annotated 注解),解决'多节点如何合并状态',默认覆盖,`add` 追加,可自定义。第二层是 Checkpointer,每个超步后自动序列化 State 到 SQLite/Postgres,带来断点续跑和 HITL。第三层是 Time Travel,基于 Checkpoint 历史可回到任意快照重放,用于调试和分支探索。这三层叠加,让 Agent 第一次拥有了'可暂停、可恢复、可回溯'的工程能力,这是 AgentExecutor 完全不具备的。"

#### 9. 易错点

- **忘写 Reducer 导致消息丢失**:`messages: list`(没 Annotated)→ 每个节点覆盖,只有最后一条。必须 `Annotated[list, add]`。
- **thread_id 必传**:不传 thread_id,Checkpointer 不工作,状态不会持久化。
- **update_state 不是 invoke**:它只更新 State 不执行图,要继续执行得 `invoke(None)`。
- **Time Travel 改 State 后是从下一节点继续**:不是从图开头,理解这点对调试很重要。

</details>

### Q7: LangChain 的 Memory 机制有哪些? ConversationBufferMemory / SummaryMemory / VectorStoreRetrieverMemory 各自原理与适用场景?

<details>
<summary>点击展开答案</summary>

LLM 本身是无状态的,每次调用都是独立的。**Memory 的作用是在多次调用之间保留对话上下文**,让 Agent 拥有"记住之前说过什么"的能力。LangChain 提供多种 Memory 实现,核心区别在于"如何存储历史"和"如何取舍历史"。

#### 1. Memory 的工作模型

```
Round N:
   用户输入
       │
       ▼
[Memory.load_memory_variables] ──► 取出历史
       │
       ▼
[拼接到 Prompt] (历史 + 当前问题)
       │
       ▼
[LLM 调用]
       │
       ▼
[生成回复]
       │
       ▼
[Memory.save_context] ──► 保存本轮 (user, ai)
       │
       ▼
   返回用户
```

两个核心方法:
- `load_memory_variables(inputs) -> dict`:返回 `{"history": "..."}` 注入 Prompt;
- `save_context(inputs, outputs)`:把本轮对话存入 Memory。

#### 2. 五种主流 Memory 对比

| Memory 类型 | 存储方式 | 取舍策略 | Token 成本 | 适合场景 |
|------------|----------|----------|-----------|----------|
| **ConversationBufferMemory** | 全量字符串/list | 不取舍,全量保留 | 线性增长 | 短对话、Demo |
| **ConversationBufferWindowMemory** | 全量 list | 只保留最近 K 轮 | 固定上限 | 中等对话 |
| **ConversationSummaryMemory** | 摘要字符串 | LLM 实时摘要压缩 | 低(摘要长度) | 长对话、需全局上下文 |
| **VectorStoreRetrieverMemory** | 向量库 | 按相关性检索 Top-K | 固定 Top-K | 超长对话、跨 session 记忆 |
| **ConversationKGMemory** | 知识图谱 | 抽取实体关系存图 | 低 | 实体关系密集场景 |
| **CombinedMemory** | 组合 | 多种 Memory 叠加 | 累加 | 复杂场景 |

#### 3. ConversationBufferMemory — 全量缓存

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True)
memory.save_context({"input": "我叫张三"}, {"output": "你好,张三"})
memory.save_context({"input": "我喜欢Python"}, {"output": "Python很棒"})

print(memory.load_memory_variables({}))
# {'history': [HumanMessage("我叫张三"), AIMessage("你好,张三"), ...]}
```

**原理**:简单地把每轮对话 append 到 list,加载时全量返回。
**优点**:实现简单、信息无损。
**缺点**:Token 数线性增长,长对话会撑爆 context window。
**适合**:对话轮数 < 10 的短场景、Demo、单元测试。

#### 4. ConversationSummaryMemory — LLM 摘要压缩

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=llm, return_messages=False)
memory.save_context({"input": "我叫张三,在北京工作"}, {"output": "记下了"})
memory.save_context({"input": "我是后端工程师,用Java"}, {"output": "了解"})
# 内部会用 LLM 把历史摘要成:
# "用户叫张三,在北京工作,是Java后端工程师。"
print(memory.load_memory_variables({}))
# {'history': '用户叫张三,在北京工作,是Java后端工程师。'}
```

**原理**:`save_context` 时,**异步触发 LLM** 把"已有摘要 + 新一轮对话"压缩成新摘要。
**摘要 Prompt 示例**:
```
你是对话摘要器。请把已有摘要和新对话合并成新摘要,保留关键信息:
已有摘要: {summary}
新对话:
Human: {input}
AI: {output}
新摘要:
```

**优点**:Token 成本恒定(摘要长度可控),适合超长对话。
**缺点**:
- 每次 save 多一次 LLM 调用,延迟和成本上升;
- 摘要会丢失细节(如具体数字、人名可能被省略);
- 摘要质量依赖 LLM,偶发幻觉。

**适合**:客服长对话、需保留全局印象但不需逐字回忆的场景。

#### 5. ConversationBufferWindowMemory — 滑动窗口

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=5)    # 只保留最近 5 轮
```

**原理**:维护 list,加载时只取最后 K 条。
**优点**:Token 成本固定,无 LLM 调用开销。
**缺点**:K 轮之前的信息完全丢失。
**适合**:多轮但不依赖早期上下文的场景(如持续问答)。

#### 6. VectorStoreRetrieverMemory — 向量检索记忆

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_community.vectorstores import Chroma

vectorstore = Chroma(embedding_function=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

memory = VectorStoreRetrieverMemory(retriever=retriever)
memory.save_context({"input": "我女儿2018年出生"}, {"output": "记下了"})
memory.save_context({"input": "我家狗叫旺财"}, {"output": "可爱的名字"})
# ... 100 轮后 ...
memory.load_memory_variables({"input": "我女儿多大了?"})
# 向量检索最相关的 5 条 → 返回 "我女儿2018年出生" 那条
```

**原理**:
- `save_context`:把每轮对话 embedding 后存入向量库,**以"对话内容"为 doc,"输入+输出"为 page_content**;
- `load_memory_variables`:把当前输入作为 query,**检索 Top-K 最相关的历史轮次**。

**优点**:
- 可跨 session 记忆(只要向量库不删);
- Token 成本固定(Top-K);
- 能"跳着"回忆相关历史,不受时间衰减限制。

**缺点**:
- 检索依赖 embedding 质量,口语化表达易召回不准;
- 顺序信息丢失(检索结果按相似度而非时间排序);
- 额外依赖向量库。

**适合**:超长对话、用户偏好记忆、跨 session 个性化。

#### 7. 三种 Memory 选型决策树

```
对话轮数 < 10?
   └─ 是 → ConversationBufferMemory
   └─ 否 → 需要全局摘要(用户画像、长期偏好)?
            └─ 是 → ConversationSummaryMemory
            └─ 否 → 需要跨 session 记忆 / 海量历史?
                     └─ 是 → VectorStoreRetrieverMemory
                     └─ 否 → 只关心最近几轮?
                              └─ 是 → ConversationBufferWindowMemory(k=5~10)
                              └─ 否 → CombinedMemory (摘要 + 向量 + 窗口)
```

#### 8. LCEL 时代的 Memory:RunnableWithMessageHistory

LangChain 0.1+ 推荐**不再直接用 Memory 类**,而是用 `RunnableWithMessageHistory` 包裹 LCEL chain,它内部基于 `BaseChatMessageHistory`(只负责存,不负责取舍)。

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory

def get_session_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(session_id, conn_string="sqlite:///memory.db")

chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history",
)

# 调用时指定 session_id
chain_with_history.invoke(
    {"question": "我是张三"},
    config={"configurable": {"session_id": "user-123"}},
)
```

**与旧 Memory 的区别**:
- `BaseChatMessageHistory` 只负责"存取",不负责"取舍";
- 取舍逻辑由开发者在 chain 里用 `RunnablePassthrough.assign` 自己实现(如取最近 K 条、做摘要);
- 更灵活、更 LCEL 原生、但需要更多手写代码。

**官方趋势**:Memory 类已停止演进,新项目推荐用 `RunnableWithMessageHistory` 或直接用 LangGraph 的 State + Checkpointer。

#### 9. 面试金句

> "LangChain 的 Memory 本质是'在无状态的 LLM 调用之间保留上下文'。三种主流方案对应三种取舍策略:Buffer 全留(短对话)、Summary 摘要压缩(长对话但需全局)、VectorStore 按需检索(超长或跨 session)。选型口诀:'短用 Buffer,长用 Summary,跨 session 用 Vector'。但要注意,LangChain 0.1+ 已停止演进 Memory 类,新项目推荐用 RunnableWithMessageHistory 或直接用 LangGraph 的 State——后者把记忆和图状态合一,是更彻底的方案。"

#### 10. 易错点

- **Memory 默认不持久化**:`ConversationBufferMemory` 进程重启就丢,生产要用 `SQLChatMessageHistory` 或 Redis 后端。
- **SummaryMemory 的 save 是同步阻塞的**(默认):会拖慢响应,可设 `awaitable=True` 改异步。
- **VectorStoreMemory 的检索不保证时序**:可能把 50 轮前的事和 1 轮前的事一起返回,需要在 Prompt 里加时间戳。
- **Memory 与 LangGraph 不兼容**:LangGraph 用 State + Checkpointer 替代 Memory,不要混用。

</details>

### Q8: LangChain 如何自定义开发 Tools? @tool 装饰器、StructuredTool、BaseTool 三种方式的区别? 工具错误如何处理?

<details>
<summary>点击展开答案</summary>

Tools 是 Agent 调用外部能力的桥梁。LangChain 提供三种自定义工具的方式,从简到繁分别是 `@tool` 装饰器、`StructuredTool.from_function`、继承 `BaseTool`。

#### 1. @tool 装饰器 — 最简方式

```python
from langchain_core.tools import tool

@tool
def search_weather(city: str, unit: str = "celsius") -> str:
    """查询指定城市的天气。

    Args:
        city: 城市名称,如 "北京"、"上海"。
        unit: 温度单位,"celsius" 或 "fahrenheit",默认摄氏度。

    Returns:
        天气描述字符串。
    """
    # 实际调用天气 API
    return f"{city}: 晴, 25°{unit[0].upper()}"

# 工具自动有 name, description, args_schema
print(search_weather.name)         # "search_weather"
print(search_weather.description)  # docstring 内容
print(search_weather.args)         # {"city": {"type": "string"}, "unit": {...}}
```

**原理**:
- `@tool` 把函数包装成 `StructuredTool` 实例;
- **函数名 → tool.name**;
- **docstring → tool.description**(LLM 看这个决定何时用);
- **类型注解 → tool.args_schema**(Pydantic Model,LLM 据此生成参数)。

**关键点**:
- **docstring 是 LLM 看到的工具说明**,写得好不好直接影响 LLM 调用准确率;
- **类型注解必须写**,LangChain 据此生成 JSON Schema 给 LLM;
- **不支持默认值参数会被视为必填**,LLM 必须填。

**进阶用法 — 控制工具元信息**:

```python
@tool("weather_search", return_direct=False, args_schema=WeatherSchema)
def search_weather(city: str) -> str:
    """..."""
```

#### 2. StructuredTool — 显式 Schema

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(..., description="城市名称,如 北京、上海")
    unit: str = Field("celsius", description="温度单位", pattern="^(celsius|fahrenheit)$")
    days: int = Field(1, description="预测天数,1-7", ge=1, le=7)

def _search_weather(city: str, unit: str = "celsius", days: int = 1) -> str:
    return f"{city} 未来{days}天: 晴, 25°{unit[0].upper()}"

search_weather = StructuredTool.from_function(
    func=_search_weather,
    name="weather_search",
    description="查询城市天气,支持1-7天预报",
    args_schema=WeatherInput,
    return_direct=False,
    handle_tool_error=True,        # 自动捕获异常返回错误信息
)
```

**与 @tool 的区别**:
- Schema 用 Pydantic 显式定义,可加 `Field` 约束(description、pattern、ge/le);
- 函数和 schema 分离,适合函数已有但 schema 需要定制的场景;
- 可注入更多元信息(handle_tool_error、return_direct)。

**适合场景**:
- 参数有复杂约束(正则、范围、枚举);
- 函数已有但 docstring 不规范,不想改函数;
- 需要为同一函数生成多个不同 schema 的工具。

#### 3. BaseTool 继承 — 完整生命周期

```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import asyncio

class SearchInput(BaseModel):
    query: str = Field(..., description="搜索关键词")
    max_results: int = Field(5, description="最大结果数")

class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = "在互联网上搜索信息"
    args_schema: Type[BaseModel] = SearchInput
    api_key: str = ""        # 可作为实例属性注入

    def _run(self, query: str, max_results: int = 5) -> str:
        """同步执行"""
        # 调用搜索 API
        return self._call_api(query, max_results)

    async def _arun(self, query: str, max_results: int = 5) -> str:
        """异步执行(必须实现,否则 ainvoke 报错)"""
        return await self._acall_api(query, max_results)

    def _call_api(self, query, n):
        # 实际调用逻辑
        return f"搜索 {query} 的前 {n} 条结果"

# 使用
tool = WebSearchTool(api_key="sk-xxx")
result = tool.invoke({"query": "LangGraph", "max_results": 3})
```

**与 @tool / StructuredTool 的区别**:
- 是一个**类**,可以有**实例状态**(如 api_key、缓存);
- 必须实现 `_run`(同步)和 `_arun`(异步);
- 可重写更多生命周期方法:`_parse_input`、`_format_output` 等;
- 适合复杂工具:需要初始化、需要缓存、需要连接池。

#### 4. 三种方式对比

| 维度 | @tool | StructuredTool | BaseTool |
|------|-------|----------------|----------|
| **代码量** | 最少 | 中 | 最多 |
| **Schema 定义** | docstring + 类型注解自动推断 | Pydantic 显式 | Pydantic 显式 |
| **Schema 约束** | 弱(只有类型) | 强(Field 约束) | 强(Field 约束) |
| **异步支持** | 自动(若函数是 async) | 自动(若函数是 async) | 必须显式实现 `_arun` |
| **实例状态** | 无 | 无 | 有(类属性) |
| **生命周期 hook** | 无 | 无 | 多个 hook 可重写 |
| **适合场景** | 简单工具、Demo | 复杂 schema | 有状态工具、生产级 |

**选型建议**:
- 内部 Demo / Hackathon → `@tool`
- 生产环境、参数有约束 → `StructuredTool`
- 需要连接池 / 缓存 / 复杂初始化 → `BaseTool`

#### 5. 工具错误处理

工具调用难免出错(网络异常、参数非法、API 限流)。LangChain 提供 `ToolException` + `handle_tool_error` 机制:

```python
from langchain_core.tools import ToolException, tool

@tool
def query_db(sql: str) -> str:
    """执行 SQL 查询"""
    if "DROP" in sql.upper():
        raise ToolException("禁止执行 DROP 语句")
    try:
        return db.execute(sql)
    except ConnectionError as e:
        raise ToolException(f"数据库连接失败: {e}")
    except TimeoutError:
        raise ToolException("查询超时,请缩小范围重试")

# 关键:handle_tool_error 决定异常如何被 LLM 看到
query_db = query_weather.with_config(
    handle_tool_error=True,            # True: 把异常 message 返回给 LLM
)

# 或自定义错误处理函数
def custom_error_handler(e: ToolException) -> str:
    if "超时" in str(e):
        return "工具调用超时,建议改用更小的查询范围"
    return f"工具出错: {e}"

query_db = query_db.with_config(handle_tool_error=custom_error_handler)
```

**关键设计**:
- `ToolException` 是"可恢复"的异常,LLM 看到错误信息后可以**调整参数重试**;
- 普通 `Exception` 默认会**中断整个 Agent**;
- `handle_tool_error=True` 把 `ToolException` 的 message 作为 Observation 返回给 LLM;
- `handle_tool_error=callable` 可以自定义返回内容(如翻译错误、给 LLM 更友好的提示)。

**LLM 看到的循环**:
```
Thought: 我需要查数据库
Action: query_db
Action Input: {"sql": "SELECT * FROM users"}
Observation: 数据库连接失败: Connection refused
Thought: 数据库连不上,我换一种方式回答
Final Answer: 抱歉,数据库暂时不可用...
```

#### 6. Toolkit — 工具集合封装

当一个场景需要多个相关工具(如"搜索引擎工具集":搜索、摘要、去重),可用 Toolkit 封装:

```python
from langchain_core.tools import BaseToolkit

class SearchToolkit(BaseToolkit):
    def get_tools(self) -> list:
        return [self._search, self._summarize, self._dedup]

    @tool
    def _search(query: str) -> str:
        """搜索"""
        ...

    @tool
    def _summarize(text: str) -> str:
        """摘要"""
        ...
```

Toolkit 便于**按场景加载工具集**,避免一次性把所有工具塞给 LLM(工具越多,LLM 决策越差)。

#### 7. 面试金句

> "LangChain 自定义工具有三种方式,本质是'简洁度 vs 控制力'的权衡。@tool 装饰器最简,靠 docstring 和类型注解自动推断 schema,适合 Demo。StructuredTool 用 Pydantic 显式定义 schema,支持 Field 约束(正则、范围),适合生产。BaseTool 是类,可以有实例状态和完整生命周期,适合需要连接池、缓存的复杂工具。错误处理上,抛 ToolException + handle_tool_error=True 可以让 LLM 看到错误并自适应重试,而普通 Exception 会直接中断 Agent——这是生产环境的必备设计。"

#### 8. 易错点

- **docstring 写不好,LLM 不会用工具**:docstring 是 LLM 唯一的工具说明,要写清楚"什么情况下用、参数什么意思"。
- **@tool 不支持 **kwargs**:必须用显式参数。
- **异步工具必须实现 _arun**:`BaseTool` 默认 `_arun` 抛 NotImplementedError,异步调用会失败。
- **handle_tool_error 默认是 False**:ToolException 也会中断 Agent,必须显式开启。
- **工具数量不宜超过 10 个**:研究表明工具越多 LLM 调用准确率越低,超过 15 个会显著下降,建议用 Toolkit 按场景动态加载。

</details>

### Q9: 手撕代码题 — 用 LangGraph 实现一个多步骤 Agent 工作流,包含条件分支、人机回环(HITL)、状态持久化,Python 完整实现

<details>
<summary>点击展开答案</summary>

**题目**:用 LangGraph 实现一个"文档审核 Agent"工作流:
1. 用户提交文档;
2. LLM 自动审核(条件分支:通过 / 需修改 / 拒绝);
3. 若"需修改",进入人机回环——人工审核并决定批准/打回;
4. 若人工打回,回到 LLM 自动审核;
5. 全程状态持久化,支持中断恢复。

**完整可运行代码**:

```python
"""
LangGraph 多步骤 Agent 工作流示例
功能: 文档审核 Agent (自动审核 + 人机回环 + 状态持久化)
依赖: pip install langgraph langchain-openai langchain-core
"""
from __future__ import annotations

import os
from typing import TypedDict, Annotated, Literal
from operator import add
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3


# ============================================================
# 1. 状态定义 (State + Reducer)
# ============================================================
class ReviewState(TypedDict):
    document: str                                   # 待审核文档
    review_result: str                              # 审核结果: pass / revise / reject
    review_comment: str                             # 审核意见
    human_decision: str                             # 人工决定: approve / reject
    retry_count: int                                # 重试次数
    messages: Annotated[list, add]                  # 对话历史(追加)
    final_output: str                               # 最终输出


# ============================================================
# 2. 节点定义 (Nodes)
# ============================================================
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def auto_review(state: ReviewState) -> dict:
    """节点 1: LLM 自动审核文档"""
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content="""你是一个文档审核员。请审核用户提交的文档,给出结论:
- pass: 文档质量良好,直接通过
- revise: 文档需要修改,请给出具体修改建议
- reject: 文档严重不合格,拒绝

请严格按以下 JSON 格式输出(不要其他内容):
{{"result": "pass|revise|reject", "comment": "审核意见"}}"""),
        HumanMessage(content="请审核以下文档:\n\n{document}"),
    ])
    response = llm.invoke(prompt.format_messages(document=state["document"]))

    # 解析 JSON (实际生产应加 try/except + 重试)
    import json
    try:
        parsed = json.loads(response.content)
        result = parsed.get("result", "revise")
        comment = parsed.get("comment", "")
    except Exception:
        result, comment = "revise", f"LLM 输出解析失败: {response.content[:200]}"

    return {
        "review_result": result,
        "review_comment": comment,
        "messages": [AIMessage(content=f"自动审核: {result} - {comment}")],
        "retry_count": state.get("retry_count", 0),
    }


def human_review_node(state: ReviewState) -> dict:
    """节点 2: 人机回环节点(实际逻辑在 interrupt 之后由外部填充)"""
    # 这个节点本身不做事,真正的"人工操作"通过 update_state 完成
    # 它只是占位,让 interrupt_before 在它之前暂停
    return {
        "messages": [AIMessage(content=f"等待人工审核... 当前重试次数: {state.get('retry_count', 0)}")],
    }


def apply_human_decision(state: ReviewState) -> dict:
    """节点 3: 应用人工决定"""
    decision = state.get("human_decision", "reject")
    if decision == "approve":
        output = f"文档已通过(人工批准)。审核意见: {state['review_comment']}"
    else:
        output = f"文档被人工打回,需重新审核。打回原因: {state.get('review_comment', '')}"
    return {
        "messages": [AIMessage(content=output)],
        "retry_count": state.get("retry_count", 0) + (1 if decision == "reject" else 0),
    }


def finalize(state: ReviewState) -> dict:
    """节点 4: 终结"""
    return {
        "final_output": f"审核完成。最终结果: {state['review_result']}, 重试次数: {state.get('retry_count', 0)}",
        "messages": [AIMessage(content="审核流程结束")],
    }


# ============================================================
# 3. 路由函数 (Conditional Edges)
# ============================================================
def route_after_auto_review(state: ReviewState) -> str:
    """自动审核后路由"""
    result = state.get("review_result", "revise")
    if result == "pass":
        return "finalize"
    elif result == "reject":
        return "finalize"
    else:  # revise
        return "human_review"


def route_after_human_decision(state: ReviewState) -> str:
    """人工决定后路由"""
    decision = state.get("human_decision", "reject")
    if decision == "approve":
        return "finalize"
    else:
        # 打回,但限制最多重试 3 次
        if state.get("retry_count", 0) >= 3:
            return "finalize"
        return "auto_review"


# ============================================================
# 4. 构建图 (StateGraph)
# ============================================================
def build_review_graph():
    g = StateGraph(ReviewState)

    # 添加节点
    g.add_node("auto_review", auto_review)
    g.add_node("human_review", human_review_node)
    g.add_node("apply_decision", apply_human_decision)
    g.add_node("finalize", finalize)

    # 添加边
    g.add_edge(START, "auto_review")

    # 条件分支 1: 自动审核后
    g.add_conditional_edges(
        "auto_review",
        route_after_auto_review,
        {
            "human_review": "human_review",
            "finalize": "finalize",
        },
    )

    # 人机回环节点 → apply_decision (interrupt_before 会在 human_review 之前暂停)
    g.add_edge("human_review", "apply_decision")

    # 条件分支 2: 人工决定后
    g.add_conditional_edges(
        "apply_decision",
        route_after_human_decision,
        {
            "auto_review": "auto_review",
            "finalize": "finalize",
        },
    )

    g.add_edge("finalize", END)

    return g


# ============================================================
# 5. 编译图 (含 Checkpointer + interrupt)
# ============================================================
def compile_app():
    """编译图,带状态持久化和人机回环中断点"""
    graph = build_review_graph()

    # SQLite 持久化
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    # 在 human_review 节点之前暂停,实现 HITL
    app = graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_review"],
    )
    return app


# ============================================================
# 6. 运行演示
# ============================================================
def demo_run():
    app = compile_app()

    # --- 第一次调用: 会自动审核,然后停在 human_review 之前 ---
    config = {"configurable": {"thread_id": "doc-review-001"}}
    initial_state = {
        "document": "## 产品介绍\n我们的产品是一个AI助手,可以帮你写代码。\n(内容偏简单,需要补充)",
        "retry_count": 0,
        "messages": [],
    }

    print("=== 第一次调用: 自动审核 ===")
    result = app.invoke(initial_state, config=config)
    print(f"审核结果: {result['review_result']}")
    print(f"审核意见: {result['review_comment']}")

    # 查看当前状态 (停在 human_review 之前)
    state = app.get_state(config)
    print(f"\n当前停在哪: {state.next}")    # ('human_review',)

    # --- 人工介入: 决定打回 ---
    print("\n=== 人工决定: 打回(模拟) ===")
    app.update_state(config, {
        "human_decision": "reject",
        "review_comment": "文档太简短,需要补充产品特性和应用场景",
    })
    # 恢复执行
    result = app.invoke(None, config=config)
    print(f"打回后,审核结果: {result.get('review_result')}")

    # 因为 retry_count=1 < 3, 会再次走 auto_review → 又停在 human_review
    state = app.get_state(config)
    print(f"当前停在哪: {state.next}")

    # --- 人工介入: 这次批准 ---
    print("\n=== 人工决定: 批准 ===")
    app.update_state(config, {"human_decision": "approve"})
    result = app.invoke(None, config=config)
    print(f"最终输出: {result.get('final_output')}")
    print(f"重试次数: {result.get('retry_count')}")

    # --- Time Travel: 看历史 ---
    print("\n=== 历史快照 ===")
    for i, snapshot in enumerate(app.get_state_history(config)):
        print(f"[{i}] next={snapshot.next}, retry={snapshot.values.get('retry_count', 0)}, "
              f"result={snapshot.values.get('review_result', '-')}")


if __name__ == "__main__":
    os.environ.setdefault("OPENAI_API_KEY", "sk-xxx")
    demo_run()
```

#### 代码结构说明

| 部分 | 作用 |
|------|------|
| `ReviewState` | TypedDict 定义状态,`messages` 用 `add` Reducer 追加 |
| `auto_review` 节点 | LLM 审核文档,输出 pass/revise/reject |
| `human_review` 节点 | HITL 占位节点,interrupt_before 会在它之前暂停 |
| `apply_human_decision` 节点 | 应用人工决定,更新 retry_count |
| `route_after_auto_review` | 条件路由: pass/reject → finalize, revise → human_review |
| `route_after_human_decision` | 条件路由: approve → finalize, reject → auto_review(带重试上限) |
| `compile_app` | 编译图,注入 SqliteSaver 和 interrupt_before |
| `demo_run` | 演示完整流程:自动审核→人工打回→重新审核→人工批准 |

#### 关键设计点(面试可重点讲)

1. **条件分支**:`add_conditional_edges` 实现 pass/revise/reject 三分支路由;
2. **回环**:人工 reject 后回到 `auto_review`,形成循环;
3. **重试上限**:`retry_count >= 3` 强制终止,防止死循环;
4. **人机回环**:`interrupt_before=["human_review"]` 在节点前暂停,`update_state` 注入人工决定,`invoke(None)` 恢复;
5. **状态持久化**:SqliteSaver 自动 checkpoint,进程重启可恢复;
6. **Time Travel**:`get_state_history` 可回溯任意快照,支持调试和分支探索。

#### 图结构可视化

```
           START
             │
             ▼
       auto_review (LLM 审核)
             │
      ┌──────┼──────┐
      │      │      │
    pass  revise  reject
      │      │      │
      │      ▼      │
      │  human_review (interrupt_before 暂停)
      │      │      │
      │      ▼      │
      │  apply_decision
      │      │
      │   ┌──┴──┐
      │ approve reject
      │   │     │ (retry<3)
      │   │     └──► auto_review (回环)
      │   │
      ▼   ▼
       finalize ───► END
```

#### 面试金句

> "这段代码体现了 LangGraph 的三大核心能力:条件分支用 `add_conditional_edges` 实现三路由,人机回环用 `interrupt_before` + `update_state` + `invoke(None)` 三步走,状态持久化用 SqliteSaver 自动 checkpoint。注意几个工程细节:retry_count 防死循环、human_review 是占位节点、route 函数返回值必须和映射表 key 一致。这是 LangGraph 区别于 AgentExecutor 的根本——控制流是图,不是 while 循环。"

</details>

### Q10: 系统设计题 — 用 LangChain + LangGraph 设计一个客服 Agent 系统,含多轮对话 / 工单创建 / 人工转接 / 质量监控

<details>
<summary>点击展开答案</summary>

**题目**:设计一个面向电商场景的客服 Agent 系统,要求:
1. 支持多轮对话,记住用户身份和历史问题;
2. 自动回答常见问题(基于知识库 RAG);
3. 无法解决时自动创建工单并流转;
4. 复杂问题转人工,人工接入后能看到完整上下文;
5. 全程质量监控(响应延迟、解决率、用户满意度)。

#### 1. 系统总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        客服 Agent 系统                          │
│                                                                 │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────────┐    │
│  │ 用户接入 │──►│  意图路由层  │──►│   LangGraph 工作流   │    │
│  │ (Web/IM) │   │ (LLM Classifier)│  │  (StateGraph 编排)  │    │
│  └──────────┘   └──────────────┘   └──────────────────────┘    │
│                                              │                  │
│                       ┌──────────────────────┴───────┐          │
│                       │                              │          │
│                       ▼                              ▼          │
│              ┌──────────────┐              ┌──────────────┐    │
│              │  FAQ RAG 节点│              │ 工单创建节点 │    │
│              │ (LangChain)  │              │ (CRM API)    │    │
│              └──────────────┘              └──────────────┘    │
│                       │                              │          │
│                       │                              ▼          │
│                       │                   ┌──────────────┐    │
│                       │                   │ 人工转接节点 │    │
│                       │                   │ (HITL)       │    │
│                       │                   └──────────────┘    │
│                       │                              │          │
│                       └──────────────┬───────────────┘          │
│                                      ▼                          │
│                            ┌──────────────────┐                │
│                            │  质量监控 Callback│                │
│                            │  (LangSmith + 自建)│                │
│                            └──────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
```

#### 2. 核心组件选型

| 组件 | 选型 | 理由 |
|------|------|------|
| **对话编排** | LangGraph StateGraph | 多分支、HITL、状态持久化 |
| **RAG 检索** | LangChain LCEL chain | 检索是固定流水线,LCEL 最合适 |
| **Memory** | LangGraph State + Checkpointer | 不用 ConversationBufferMemory,与图状态合一 |
| **LLM** | GPT-4o-mini(路由/对话) + GPT-4o(复杂推理) | 分级使用控成本 |
| **向量库** | Milvus / pgvector | 企业级,支持过滤 |
| **持久化** | Postgres Checkpointer + Redis 缓存 | 强持久 + 低延迟 |
| **监控** | LangSmith + Prometheus + 自建 Dashboard | 全链路追踪 + 业务指标 |
| **工单系统** | 内部 CRM API(包装为 Tool) | 复用现有系统 |
| **人工接入** | LangGraph interrupt + IM SDK(如声网) | HITL 原生支持 |

#### 3. LangGraph 工作流设计

```python
# ===== State 定义 =====
class CustomerServiceState(TypedDict):
    user_id: str
    session_id: str
    messages: Annotated[list, add]              # 对话历史
    intent: str                                  # 意图: faq / complaint / refund / complex
    rag_context: str                             # RAG 检索到的上下文
    ticket_id: str                               # 工单ID
    needs_human: bool                            # 是否需要人工
    human_agent_id: str                          # 人工客服ID
    satisfaction_score: int                      # 满意度评分
    retry_count: int
    resolved: bool
    metadata: dict                               # 监控元数据(latency 等)

# ===== 节点定义 =====
def classify_intent(state) -> dict:
    """意图分类: 用便宜模型做路由"""
    prompt = f"""判断用户意图,返回 JSON:
- faq: 常见问题咨询
- complaint: 投诉
- refund: 退款
- complex: 复杂问题需人工
用户: {state['messages'][-1].content}"""
    resp = small_llm.invoke(prompt)
    return {"intent": parse_json(resp)["intent"]}

def rag_answer(state) -> dict:
    """FAQ RAG 节点: LangChain LCEL chain"""
    # 检索 + 生成
    docs = retriever.invoke(state["messages"][-1].content)
    answer = rag_chain.invoke({
        "context": docs,
        "question": state["messages"][-1].content,
    })
    return {
        "messages": [AIMessage(content=answer)],
        "rag_context": format_docs(docs),
        "resolved": True,
    }

def create_ticket(state) -> dict:
    """工单创建节点: 调用 CRM Tool"""
    ticket = crm_tool.invoke({
        "user_id": state["user_id"],
        "issue": state["messages"][-1].content,
        "priority": "high" if state["intent"] == "complaint" else "normal",
    })
    return {
        "ticket_id": ticket["id"],
        "messages": [AIMessage(content=f"已为您创建工单 {ticket['id']},客服会在24小时内联系您")],
    }

def human_handoff(state) -> dict:
    """人工转接节点(占位,实际人工操作通过 update_state 注入)"""
    return {"messages": [AIMessage(content="正在为您转接人工客服,请稍候...")]}

def satisfaction_survey(state) -> dict:
    """满意度回访节点"""
    return {"messages": [AIMessage(content="请问本次服务您满意吗?1-5分")]}

# ===== 路由函数 =====
def route_by_intent(state) -> str:
    intent = state["intent"]
    if intent == "faq":
        return "rag_answer"
    elif intent in ("complaint", "refund"):
        return "create_ticket"
    else:
        return "human_handoff"

def route_after_rag(state) -> str:
    """RAG 回答后,判断是否需要人工兜底"""
    if state.get("resolved"):
        return "satisfaction_survey"
    return "human_handoff"          # RAG 没解决,转人工

# ===== 图构建 =====
def build_cs_graph():
    g = StateGraph(CustomerServiceState)
    g.add_node("classify", classify_intent)
    g.add_node("rag_answer", rag_answer)
    g.add_node("create_ticket", create_ticket)
    g.add_node("human_handoff", human_handoff)
    g.add_node("satisfaction", satisfaction_survey)

    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", route_by_intent, {
        "rag_answer": "rag_answer",
        "create_ticket": "create_ticket",
        "human_handoff": "human_handoff",
    })
    g.add_conditional_edges("rag_answer", route_after_rag, {
        "satisfaction_survey": "satisfaction",
        "human_handoff": "human_handoff",
    })
    g.add_edge("create_ticket", "satisfaction")
    g.add_edge("human_handoff", "satisfaction")
    g.add_edge("satisfaction", END)

    return g

# ===== 编译(含 HITL + 持久化) =====
app = build_cs_graph().compile(
    checkpointer=PostgresSaver(...),
    interrupt_before=["human_handoff"],   # 人工转接前暂停,等客服上线
)
```

#### 4. 工作流图示

```
            START
              │
              ▼
        classify (意图分类)
              │
    ┌─────────┼─────────┐
    │         │         │
  faq     complaint  complex
    │     /refund
    │         │         │
    ▼         ▼         ▼
 rag_answer  create_ticket  human_handoff (interrupt)
    │         │                 │
    │         │         (人工接入后 update_state)
    │         │                 │
    └────┬────┘                 │
         │                      │
         └──────────┬───────────┘
                    ▼
              satisfaction (满意度)
                    │
                    ▼
                   END
```

#### 5. 关键设计要点

##### (1) 多轮对话 — State + Checkpointer

```python
# 每个用户会话用 thread_id 隔离
config = {"configurable": {"thread_id": f"user-{user_id}-session-{session_id}"}}
result = app.invoke({"user_id": user_id, "messages": [HumanMessage(msg)]}, config=config)

# Checkpointer 自动持久化,下次同 thread_id 自动恢复
# 对话历史在 State["messages"] 里,Reducer 是 add,自动累积
```

**不用 ConversationBufferMemory 的原因**:LangGraph 的 State 已经承担了记忆职责,再用 Memory 类会双重管理、状态不一致。

##### (2) 工单创建 — Tool 包装

```python
@tool
def create_crm_ticket(user_id: str, issue: str, priority: str) -> dict:
    """在 CRM 系统创建工单"""
    resp = requests.post("https://crm.internal/api/tickets", json={
        "user_id": user_id, "issue": issue, "priority": priority,
    })
    return resp.json()
```

工单创建是确定性动作(不需要 LLM 决策),所以**直接在节点里调 tool,而不是让 Agent 自主调用**——这是"图编排"相比"纯 Agent"的优势:确定性流程用节点,不确定性流程才用 LLM 决策。

##### (3) 人工转接 — interrupt + 双向通信

```python
# Agent 侧: 暂停在 human_handoff 之前
app.invoke(inputs, config=config)       # 停住

# 人工客服侧: IM 系统通知客服,客服查看上下文
state = app.get_state(config)
context = state.values["messages"]      # 客服能看到完整对话历史

# 客服处理后,把结论写回
app.update_state(config, {
    "messages": [HumanMessage(content=f"[人工客服 {agent_id}]: {agent_reply}")],
    "resolved": True,
})
# 恢复执行
app.invoke(None, config=config)
```

**关键设计**:
- `get_state` 让人工客服看到完整上下文(对话、RAG 检索结果、已创建工单);
- `update_state` 让人工客服的回复无缝进入对话历史;
- 客服侧可用独立 IM 系统(声网/融云),只通过 Checkpointer 与 Agent 通信——这是**异步协作**,客服不需要实时盯着 Agent。

##### (4) 质量监控 — Callbacks + 业务埋点

**三层监控**:

```python
# 第一层: LangChain Callbacks(技术指标)
class MetricsCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        self.t0 = time.time()
    def on_llm_end(self, response, **kwargs):
        latency = time.time() - self.t0
        prometheus_llm_latency.observe(latency)
        langsmith.trace(response)

    def on_tool_error(self, error, **kwargs):
        prometheus_tool_errors.inc()

# 第二层: LangGraph 状态快照(业务指标)
def business_metrics_node(state):
    """每个节点后自动埋点"""
    metrics = {
        "session_id": state["session_id"],
        "node": current_node_name,
        "resolved": state.get("resolved"),
        "ticket_created": bool(state.get("ticket_id")),
        "human_handoff": state.get("needs_human"),
    }
    push_to_dashboard(metrics)

# 第三层: 满意度闭环
def satisfaction_survey(state):
    # 等用户打分,写入数据库
    db.save_satisfaction(state["session_id"], state["satisfaction_score"])
```

**监控指标体系**:

| 指标 | 类型 | 采集方式 |
|------|------|----------|
| LLM 调用延迟 | 技术 | Callbacks |
| 工具调用错误率 | 技术 | Callbacks |
| Token 消耗 | 技术 | Callbacks |
| RAG 召回准确率 | 业务 | 离线评估 |
| 一次解决率(FCR) | 业务 | State.resolved |
| 工单创建率 | 业务 | ticket_id 非空 |
| 人工转接率 | 业务 | needs_human |
| 平均对话轮数 | 业务 | messages 长度 |
| 用户满意度(CSAT) | 业务 | satisfaction_score |
| 意图分类准确率 | 业务 | 离线标注对比 |

#### 6. 容量与性能设计

| 维度 | 设计 |
|------|------|
| **并发** | LangGraph Checkpointer 用 Postgres,支持多实例水平扩展;Redis 缓存热点会话 |
| **延迟** | 意图分类用便宜小模型(GPT-4o-mini);RAG 走缓存;人工转接异步 |
| **成本** | 分级模型:路由用 mini,生成用 4o;RAG 命中率 > 60% 可降 50% LLM 调用 |
| **可用性** | LLM 多供应商 fallback(GPT + Claude + Qwen);工具调用 `.with_retry(3)` |
| **安全** | 用户 PII 脱敏后入库;Checkpointer 加密存储;权限按 user_id 隔离 |

#### 7. 与传统客服系统的对比

| 维度 | 传统客服(规则/IVR) | 本系统(LangGraph) |
|------|---------------------|---------------------|
| **对话能力** | 关键词匹配,死板 | LLM 多轮自然对话 |
| **知识更新** | 改规则表,运维重 | 更新知识库即可 |
| **意图识别** | 规则/小模型 | LLM 零样本分类 |
| **人工转接** | 转接后客服无上下文 | 完整历史 + RAG 上下文 |
| **可观测** | 通话录音 + 抽检 | 全链路追踪 + 自动指标 |
| **扩展性** | 加规则 | 加节点 / 加工具 |

#### 8. 面试金句

> "这个客服系统用 LangGraph 做编排、LangChain LCEL 做 RAG、Tool 做 CRM 对接、interrupt 做 HITL、Callbacks + State 做监控,体现了'确定性流程用节点,不确定性流程用 LLM 决策'的设计哲学。关键三点:第一,多轮对话不用 Memory 类,直接用 State + Checkpointer,与图状态合一;第二,工单创建是确定性动作,直接在节点里调 Tool 而非让 Agent 自主决策;第三,人工转接用 interrupt 暂停 + update_state 写回,客服与 Agent 异步协作,客服侧可用独立 IM。监控分三层:Callbacks 管技术指标、State 快照管业务指标、满意度问卷闭环 CSAT。"

#### 9. 易错点 / 加分项

- **别让所有节点都调 LLM**:意图分类、工单创建这些确定性流程,能用规则或便宜模型就用,别用 GPT-4o。
- **人工转接一定要带上下文**:`get_state` 拿到完整历史给客服,这是用户体验关键。
- **必须设重试上限**:`retry_count` 防止 RAG 没解决 → 转人工 → 又转回 RAG 的死循环。
- **CSAT 闭环**:不收集满意度就无法迭代,这是很多团队忽略的。
- **加分**:提到 LangSmith 做全链路 trace、提到 A/B 测试不同 Prompt、提到用 Time Travel 复现投诉 case。

</details>
