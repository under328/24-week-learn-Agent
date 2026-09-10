# 第2月第6周：LangGraph + 状态机 Agent

> 适用对象：已完成 Week 1-5（Python基础 + LLM核心 + Prompt Engineering + RAG/Multi-Tool Agent + LangChain框架）的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：掌握 LangGraph 图状态机编程模型，能用 LangGraph 构建复杂多步骤工作流 Agent，理解从 ReAct 循环到图编排的演进

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month2/week6
cd month2/week6

python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 本周依赖
pip install langchain langchain-core langchain-community langchain-openai langgraph httpx pydantic chromadb
pip freeze > requirements.txt
```

**关于 LangGraph**：LangGraph 是 LangChain 团队推出的图编排框架，专门用于构建有状态的、多步骤的 Agent 工作流。它解决了 LangChain AgentExecutor 的局限——当 Agent 流程不再是简单的"循环调用工具"，而是需要复杂的条件分支、并行执行、人机交互时，LangGraph 用状态图（StateGraph）来精确控制流程。

**与 LangChain 的关系**：
- LangChain 提供 LCEL 链式组合和基础 Agent
- LangGraph 建立在 LangChain 之上，提供图结构编排能力
- LangChain 的 `AgentExecutor` 内部实际上也在迁移到 LangGraph 实现

---

## Day 1：LangGraph 全景 + 基础概念

> 从 ReAct 循环到图状态机——理解为什么需要 LangGraph，以及它的核心抽象。

### 1.1 为什么需要 LangGraph？

```
┌────────────── 从 AgentExecutor 到 LangGraph ──────────────┐
│                                                             │
│  AgentExecutor 的局限：                                      │
│  ┌─────────────────────────────────┐                       │
│  │  while not finished:             │                       │
│  │      action = llm.decide(tools)  │  ← 单一循环           │
│  │      result = execute(action)    │  ← 无条件分支          │
│  │      scratchpad += result        │  ← 无并行执行          │
│  │      if iter > max: break        │  ← 无人机交互          │
│  └─────────────────────────────────┘                       │
│                                                             │
│  LangGraph 的解决方案：                                      │
│  ┌─────────────────────────────────┐                       │
│  │  StateGraph                     │                       │
│  │    ├── Node A → Node B          │  ← 任意拓扑            │
│  │    ├── Node B → (condition)     │  ← 条件路由            │
│  │    │     ├── Node C             │  ← 分支执行            │
│  │    │     └── Node D             │                       │
│  │    ├── Node C → Node E, F       │  ← 并行扇出            │
│  │    ├── Node G → human_review    │  ← 人机交互            │
│  │    └── Cycle: E → B             │  ← 循环               │
│  └─────────────────────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 LangGraph 核心概念

```
┌────────────── LangGraph 五大核心概念 ──────────────────┐
│                                                         │
│  1. State（状态）                                       │
│     └── 一个 TypedDict 或 Pydantic Model               │
│     └── 在图的节点之间传递的共享数据                     │
│     └── 每个节点接收 state，返回 state 的更新部分         │
│                                                         │
│  2. Node（节点）                                        │
│     └── 一个函数：接收 state，返回 state 更新             │
│     └── 每个节点负责一个具体的处理步骤                    │
│     └── 可以调用 LLM、执行工具、做任何 Python 操作       │
│                                                         │
│  3. Edge（边）                                          │
│     ├── 普通边：A → B（A 完成后必定执行 B）              │
│     ├── 条件边：A → (条件函数) → B 或 C                  │
│     └── 决定了执行流程的走向                             │
│                                                         │
│  4. Graph（图）                                         │
│     └── StateGraph(state_schema)                        │
│     └── add_node() 添加节点                              │
│     └── add_edge() 添加边                               │
│     └── add_conditional_edges() 添加条件边               │
│     └── set_entry_point() / set_finish_point()          │
│                                                         │
│  5. Compile & Run                                       │
│     └── graph = builder.compile()                       │
│     └── graph.invoke(state)  /  stream(state)           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 1.3 第一个 LangGraph 程序

创建文件 `day1_basics.py`：

```python
"""
Day 1: LangGraph 基础
- State 定义
- Node 与 Edge
- 编译与运行
"""

import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# === 1. 定义 State ===

class MyState(TypedDict):
    question: str        # 用户问题
    answer: str          # AI 回答
    steps: list[str]     # 执行步骤记录

# === 2. 定义节点函数 ===

def think_node(state: MyState) -> dict:
    """思考节点：分析问题"""
    question = state["question"]
    return {"steps": state.get("steps", []) + [f"分析问题: {question}"]}

def answer_node(state: MyState) -> dict:
    """回答节点：调用 LLM 生成回答"""
    llm = ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=0.7,
    )
    response = llm.invoke(state["question"])
    return {
        "answer": response.content,
        "steps": state.get("steps", []) + ["调用 LLM 生成回答"],
    }

# === 3. 构建图 ===

builder = StateGraph(MyState)

# 添加节点
builder.add_node("think", think_node)
builder.add_node("answer", answer_node)

# 添加边（定义执行顺序）
builder.add_edge(START, "think")     # 入口 → think
builder.add_edge("think", "answer")  # think → answer
builder.add_edge("answer", END)      # answer → 结束

# 编译
graph = builder.compile()

# === 4. 运行 ===

result = graph.invoke({"question": "什么是状态机？", "steps": []})
print(f"问题: {result['question']}")
print(f"回答: {result['answer']}")
print(f"步骤: {result['steps']}")

# === 5. 流式运行（查看每步状态变化） ===

print("\n--- 流式运行 ---")
for event in graph.stream({"question": "什么是递归？", "steps": []}):
    for node_name, node_output in event.items():
        print(f"  节点 [{node_name}] 输出: {node_output}")
```

### 1.4 State 进阶：Reducer 与 Annotated

```python
"""
State 进阶：使用 Reducer 控制状态合并方式
默认行为：后写的覆盖先写的
Reducer：自定义合并逻辑（如列表追加）
"""

from typing import TypedDict, Annotated
from operator import add

# 默认行为：覆盖
class StateOverride(TypedDict):
    messages: list[str]

# 使用 Reducer：列表追加
class StateAppend(TypedDict):
    # Annotated[list[str], add] 表示：
    # 字段类型是 list[str]，合并时用 operator.add（列表拼接）
    messages: Annotated[list[str], add]

# 对比演示
def node_a(state: StateAppend) -> dict:
    return {"messages": ["来自A的消息"]}

def node_b(state: StateAppend) -> dict:
    return {"messages": ["来自B的消息"]}

# 如果用 StateOverride，B 的消息会覆盖 A 的
# 如果用 StateAppend（带 add reducer），B 的消息会追加到 A 的后面

builder = StateGraph(StateAppend)
builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("b", END)

graph = builder.compile()
result = graph.invoke({"messages": ["初始消息"]})
print(f"结果: {result['messages']}")
# 输出: ["初始消息", "来自A的消息", "来自B的消息"]
# 如果没有 add reducer，则只会是: ["来自B的消息"]
```

### 1.5 可视化图结构

```python
"""可视化 LangGraph 图结构"""

# 方式一：打印 ASCII 图（无需额外依赖）
print(graph.get_graph().draw_ascii())

# 方式二：导出 Mermaid 图（可在 Markdown 中渲染）
mermaid_str = graph.get_graph().draw_mermaid()
print(f"\nMermaid 图:\n{mermaid_str}")

# 方式三：导出 PNG（需要安装 pygraphviz 或使用 mermaid API）
# pip install grandalf  → 纯 Python ASCII 渲染
```

### Day 1 小结

```
Day 1 核心概念：
┌───────────────────────────────────────────────┐
│  LangGraph = 状态机 + 图编排                    │
│                                                 │
│  State   → TypedDict，节点间共享的数据           │
│  Node    → 函数，接收 state 返回更新             │
│  Edge    → 连接，定义执行顺序                    │
│  Graph   → StateGraph，组装节点和边              │
│                                                 │
│  Reducer → Annotated[type, reducer_fn]         │
│           控制状态字段的合并方式                   │
│           默认覆盖，add 追加                      │
│                                                 │
│  运行方式：                                      │
│  graph.invoke(state)    → 一次性执行            │
│  graph.stream(state)    → 逐步查看              │
│  graph.astream(state)   → 异步流式              │
└───────────────────────────────────────────────┘
```

### Day 1 练习

1. 构建一个三节点图：`分析问题 → 搜索信息 → 生成回答`，每步都记录到 `steps` 列表
2. 用 `Annotated[list[str], add]` 实现 steps 的累加，对比不加 reducer 的效果
3. 用 `graph.stream()` 查看每一步的状态变化

<details>
<summary>参考答案</summary>

```python
"""Day 1 练习答案：三节点图 + Reducer 对比"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# 带 reducer 的 State
class WorkState(TypedDict):
    question: str
    search_result: str
    answer: str
    steps: Annotated[list[str], add]  # 追加合并

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

def analyze_node(state: WorkState) -> dict:
    """分析问题"""
    q = state["question"]
    return {"steps": [f"分析: {q}"]}

def search_node(state: WorkState) -> dict:
    """模拟搜索"""
    return {
        "search_result": f"关于'{state['question']}'的模拟搜索结果",
        "steps": ["搜索: 模拟搜索完成"],
    }

def generate_node(state: WorkState) -> dict:
    """生成回答"""
    prompt = f"根据以下信息回答问题。\n搜索结果: {state['search_result']}\n问题: {state['question']}"
    response = llm.invoke(prompt)
    return {
        "answer": response.content,
        "steps": ["生成: LLM 回答完成"],
    }

# 构建图
builder = StateGraph(WorkState)
builder.add_node("analyze", analyze_node)
builder.add_node("search", search_node)
builder.add_node("generate", generate_node)

builder.add_edge(START, "analyze")
builder.add_edge("analyze", "search")
builder.add_edge("search", "generate")
builder.add_edge("generate", END)

graph = builder.compile()

# 运行
result = graph.invoke({"question": "什么是 Python GIL？", "steps": []})
print(f"回答: {result['answer']}")
print(f"步骤: {result['steps']}")
# steps 会累加所有节点添加的内容，因为有 add reducer

# 流式运行
print("\n--- 流式运行 ---")
for event in graph.stream({"question": "什么是协程？", "steps": []}):
    for node, output in event.items():
        print(f"  [{node}] → {output}")

# 对比：不带 reducer 的版本（steps 会被覆盖）
class NoReducerState(TypedDict):
    question: str
    steps: list[str]  # 无 Annotated，默认覆盖

def step_a(state: NoReducerState) -> dict:
    return {"steps": ["步骤A"]}

def step_b(state: NoReducerState) -> dict:
    return {"steps": ["步骤B"]}

builder2 = StateGraph(NoReducerState)
builder2.add_node("a", step_a)
builder2.add_node("b", step_b)
builder2.add_edge(START, "a")
builder2.add_edge("a", "b")
builder2.add_edge("b", END)

graph2 = builder2.compile()
result2 = graph2.invoke({"question": "test", "steps": []})
print(f"\n无 reducer: {result2['steps']}")  # 只有 ["步骤B"]，被覆盖了
```

</details>

---

## Day 2：条件路由 + 循环

> LangGraph 的核心能力：根据状态动态决定下一步走哪个节点，以及构建循环（ReAct 的基础）。

### 2.1 条件边（Conditional Edges）

```
┌────────────── 条件路由示意 ──────────────┐
│                                           │
│       ┌──────────┐                       │
│       │  Router  │                       │
│       └────┬─────┘                       │
│            │                              │
│    ┌───────┼───────┐                     │
│    ↓       ↓       ↓                     │
│  [代码]  [概念]  [调试]                  │
│    │       │       │                     │
│    └───────┼───────┘                     │
│            ↓                              │
│       [合并结果]                          │
│                                           │
└───────────────────────────────────────────┘
```

创建文件 `day2_routing.py`：

```python
"""
Day 2: 条件路由 + 循环
- add_conditional_edges
- 构建循环（ReAct 模式）
- 循环终止条件
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# === 1. 基础条件路由 ===

class RouteState(TypedDict):
    question: str
    category: str
    answer: str

def classify_node(state: RouteState) -> dict:
    """分类节点：判断问题类型"""
    llm = ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=0,
    )
    response = llm.invoke(
        f"判断以下问题属于哪个类别，只回答一个词：code（代码实现）、concept（概念解释）、debug（调试问题）。\n问题: {state['question']}"
    )
    category = response.content.strip().lower()
    # 简单清洗
    if "code" in category:
        category = "code"
    elif "debug" in category:
        category = "debug"
    else:
        category = "concept"
    return {"category": category}

def answer_code(state: RouteState) -> dict:
    """代码问题处理"""
    llm = ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=0.2,
    )
    response = llm.invoke(f"作为编程专家，请回答以下代码问题，提供代码示例：\n{state['question']}")
    return {"answer": response.content}

def answer_concept(state: RouteState) -> dict:
    """概念问题处理"""
    llm = ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=0.5,
    )
    response = llm.invoke(f"作为技术导师，请用通俗的语言解释：\n{state['question']}")
    return {"answer": response.content}

def answer_debug(state: RouteState) -> dict:
    """调试问题处理"""
    llm = ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=0,
    )
    response = llm.invoke(f"作为调试专家，请分析以下问题并给出排查步骤：\n{state['question']}")
    return {"answer": response.content}

# 路由函数：根据 category 决定走哪个节点
def route_by_category(state: RouteState) -> str:
    """条件路由函数：返回目标节点名"""
    category = state.get("category", "concept")
    if category == "code":
        return "answer_code"
    elif category == "debug":
        return "answer_debug"
    else:
        return "answer_concept"

# 构建图
builder = StateGraph(RouteState)
builder.add_node("classify", classify_node)
builder.add_node("answer_code", answer_code)
builder.add_node("answer_concept", answer_concept)
builder.add_node("answer_debug", answer_debug)

# 条件边：classify 之后根据 category 路由
builder.add_edge(START, "classify")
builder.add_conditional_edges(
    "classify",           # 源节点
    route_by_category,    # 路由函数
    {                     # 路由映射（可选，用于明确映射关系）
        "answer_code": "answer_code",
        "answer_concept": "answer_concept",
        "answer_debug": "answer_debug",
    },
)

# 所有回答节点都指向 END
builder.add_edge("answer_code", END)
builder.add_edge("answer_concept", END)
builder.add_edge("answer_debug", END)

graph = builder.compile()

# 测试
questions = [
    "用 Python 实现快速排序",
    "什么是 RESTful API？",
    "我的程序报 KeyError 怎么办？",
]

for q in questions:
    result = graph.invoke({"question": q})
    print(f"\n问题: {q}")
    print(f"分类: {result['category']}")
    print(f"回答: {result['answer'][:80]}...")
```

### 2.2 构建循环：ReAct Agent

```python
"""
用 LangGraph 构建 ReAct 循环
这是 LangGraph 最核心的用例——实现 Agent 的"思考-行动-观察"循环
"""

import os
import json
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

# === State 定义 ===

class AgentState(TypedDict):
    messages: Annotated[list, add]    # 消息历史（追加）
    iterations: int                    # 当前迭代次数
    final_answer: str                  # 最终答案

# === 工具定义 ===

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入为数学表达式字符串，如 '2+3*4'。"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：只支持基本数学运算"
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def search_info(query: str) -> str:
    """搜索信息（模拟）。输入为搜索关键词。"""
    mock = {
        "python": "Python 是一种高级编程语言，由 Guido van Rossum 创建。",
        "langgraph": "LangGraph 是 LangChain 团队的图编排框架。",
        "agent": "AI Agent 是能自主决策和执行任务的智能体。",
    }
    for key, val in mock.items():
        if key in query.lower():
            return val
    return f"搜索 '{query}'：未找到相关信息（模拟）"

tools = [calculator, search_info]
tools_by_name = {t.name: t for t in tools}

# === LLM 绑定工具 ===

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)

# === 节点定义 ===

def agent_node(state: AgentState) -> dict:
    """Agent 节点：LLM 决定下一步做什么"""
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)

    # 检查是否有工具调用
    if response.tool_calls:
        return {
            "messages": [response],
            "iterations": state["iterations"] + 1,
        }
    else:
        # 没有工具调用，说明 LLM 给出了最终答案
        return {
            "messages": [response],
            "iterations": state["iterations"] + 1,
            "final_answer": response.content,
        }

def tool_node(state: AgentState) -> dict:
    """工具执行节点：执行 LLM 要求的工具调用"""
    last_message = state["messages"][-1]
    results = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_func = tools_by_name.get(tool_name)

        if tool_func:
            result = tool_func.invoke(tool_args)
        else:
            result = f"未知工具: {tool_name}"

        # 创建工具响应消息
        from langchain_core.messages import ToolMessage
        results.append(ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"],
        ))

    return {"messages": results}

# === 路由函数 ===

def should_continue(state: AgentState) -> str:
    """决定是否继续循环"""
    # 最大迭代次数限制
    if state["iterations"] >= 5:
        return END

    last_message = state["messages"][-1]
    # 如果有工具调用，继续循环
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    # 否则结束
    return END

# === 构建图 ===

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END},
)
builder.add_edge("tools", "agent")  # 工具执行后回到 agent（循环）

graph = builder.compile()

# === 测试 ===

from langchain_core.messages import HumanMessage

result = graph.invoke({
    "messages": [HumanMessage(content="搜索一下 Python 是什么，然后计算 2024 * 365")],
    "iterations": 0,
    "final_answer": "",
})

print(f"最终答案: {result['final_answer']}")
print(f"迭代次数: {result['iterations']}")
print(f"消息数: {len(result['messages'])}")

# 流式查看执行过程
print("\n--- 流式执行 ---")
for event in graph.stream({
    "messages": [HumanMessage(content="计算 15 * 37")],
    "iterations": 0,
    "final_answer": "",
}):
    for node, output in event.items():
        print(f"  [{node}] iterations={output.get('iterations', '-')}")
```

### Day 2 小结

```
Day 2 核心概念：
┌─────────────────────────────────────────────────┐
│  条件路由                                        │
│  add_conditional_edges(source, router_fn, map)  │
│  router_fn(state) → 返回目标节点名               │
│                                                   │
│  循环模式（ReAct 核心）                           │
│  agent → should_continue → tools → agent → ...  │
│  通过条件边 + 回边实现循环                         │
│  需要设置最大迭代次数防止死循环                     │
│                                                   │
│  关键模式：                                        │
│  1. 条件边路由：根据 state 动态选分支              │
│  2. 循环：条件边 + 回边（tools → agent）          │
│  3. 终止条件：迭代次数 / 无工具调用 / 自定义条件   │
└─────────────────────────────────────────────────┘
```

### Day 2 练习

1. 构建一个"多语言路由器"——根据输入的语言（中文/英文/日文）路由到不同的翻译节点
2. 修改 ReAct Agent，添加第三个工具（如 `word_count`），测试多工具循环
3. 给 ReAct Agent 添加一个 `max_iterations` 参数，超过时直接返回当前最佳结果

<details>
<summary>参考答案</summary>

```python
"""Day 2 练习答案：多语言路由 + 多工具 Agent + 迭代限制"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 练习 1：多语言路由器 ===

class TranslateState(TypedDict):
    text: str
    target_lang: str
    translation: str

def detect_lang(state: TranslateState) -> dict:
    """检测目标语言"""
    return {"target_lang": state["target_lang"]}

def translate_en(state: TranslateState) -> dict:
    resp = llm.invoke(f"翻译成英文，只输出译文: {state['text']}")
    return {"translation": resp.content}

def translate_ja(state: TranslateState) -> dict:
    resp = llm.invoke(f"翻译成日文，只输出译文: {state['text']}")
    return {"translation": resp.content}

def translate_zh(state: TranslateState) -> dict:
    resp = llm.invoke(f"翻译成中文，只输出译文: {state['text']}")
    return {"translation": resp.content}

def route_lang(state: TranslateState) -> str:
    lang = state.get("target_lang", "en").lower()
    if "ja" in lang or "日" in lang:
        return "translate_ja"
    elif "zh" in lang or "中" in lang:
        return "translate_zh"
    return "translate_en"

builder = StateGraph(TranslateState)
builder.add_node("detect", detect_lang)
builder.add_node("translate_en", translate_en)
builder.add_node("translate_ja", translate_ja)
builder.add_node("translate_zh", translate_zh)

builder.add_edge(START, "detect")
builder.add_conditional_edges("detect", route_lang, {
    "translate_en": "translate_en",
    "translate_ja": "translate_ja",
    "translate_zh": "translate_zh",
})
builder.add_edge("translate_en", END)
builder.add_edge("translate_ja", END)
builder.add_edge("translate_zh", END)

translate_graph = builder.compile()

for lang in ["en", "ja", "zh"]:
    result = translate_graph.invoke({"text": "你好世界", "target_lang": lang})
    print(f"  {lang}: {result['translation']}")

# === 练习 2 + 3：多工具 Agent + 迭代限制 ===

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：只支持基本运算"
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {e}"

@tool
def search_info(query: str) -> str:
    """搜索信息（模拟）。"""
    mock = {"python": "Python 是高级编程语言。", "agent": "Agent 是智能体。"}
    for k, v in mock.items():
        if k in query.lower():
            return v
    return f"未找到: {query}"

@tool
def word_count(text: str) -> str:
    """统计文本词数。"""
    return f"词数: {len(text.split())}"

tools = [calculator, search_info, word_count]
tools_map = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list, add]
    iterations: int
    final_answer: str

def agent_node(state: AgentState) -> dict:
    response = llm_with_tools.invoke(state["messages"])
    if response.tool_calls:
        return {"messages": [response], "iterations": state["iterations"] + 1}
    return {
        "messages": [response],
        "iterations": state["iterations"] + 1,
        "final_answer": response.content,
    }

def tool_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        func = tools_map.get(tc["name"])
        result = func.invoke(tc["args"]) if func else f"未知工具: {tc['name']}"
        results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
    return {"messages": results}

MAX_ITERS = 3  # 练习 3：迭代限制

def should_continue(state: AgentState) -> str:
    if state["iterations"] >= MAX_ITERS:
        # 超过限制，用最后一条消息作为答案
        last = state["messages"][-1]
        return END
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

agent_graph = builder.compile()

# 测试多工具
result = agent_graph.invoke({
    "messages": [HumanMessage(content="搜索 Python，然后统计搜索结果有几句话，再算 100*200")],
    "iterations": 0,
    "final_answer": "",
})
print(f"\n迭代: {result['iterations']}")
print(f"答案: {result.get('final_answer', '达到最大迭代限制')[:100]}...")
```

</details>

---

## Day 3：并行执行 + 子图

> 当多个任务互相独立时，并行执行可以大幅提升效率。子图则让你把复杂图拆成可复用的模块。

### 3.1 并行扇出（Fan-out）

```
┌────────────── 并行执行示意 ──────────────┐
│                                           │
│         ┌──────────┐                     │
│         │  Source  │                     │
│         └──┬───┬───┘                     │
│            │   │                          │
│    ┌───────┘   └───────┐                 │
│    ↓           ↓       ↓                 │
│  [摘要]    [关键词]  [翻译]              │
│    │           │       │                 │
│    └───────┬───┘───────┘                 │
│            ↓                              │
│         [合并]                            │
│                                           │
└───────────────────────────────────────────┘
```

创建文件 `day3_parallel_subgraph.py`：

```python
"""
Day 3: 并行执行 + 子图
- 并行扇出（Fan-out）
- 结果合并（Fan-in）
- 子图（Subgraph）
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 1. 并行执行 ===

class ParallelState(TypedDict):
    text: str
    summary: str
    keywords: str
    translation: str
    result: str

def summarize_node(state: ParallelState) -> dict:
    """生成摘要"""
    chain = (
        lambda text: f"用一句话总结: {text}"
    )
    response = llm.invoke(f"用一句话总结以下文本: {state['text']}")
    return {"summary": response.content}

def extract_keywords_node(state: ParallelState) -> dict:
    """提取关键词"""
    response = llm.invoke(f"列出以下文本的3个关键词，用逗号分隔: {state['text']}")
    return {"keywords": response.content}

def translate_node(state: ParallelState) -> dict:
    """翻译成英文"""
    response = llm.invoke(f"翻译成英文，只输出译文: {state['text']}")
    return {"translation": response.content}

def merge_node(state: ParallelState) -> dict:
    """合并所有并行结果"""
    result = (
        f"摘要: {state['summary']}\n"
        f"关键词: {state['keywords']}\n"
        f"英文翻译: {state['translation']}"
    )
    return {"result": result}

# 构建并行图
builder = StateGraph(ParallelState)

builder.add_node("summarize", summarize_node)
builder.add_node("extract_keywords", extract_keywords_node)
builder.add_node("translate", translate_node)
builder.add_node("merge", merge_node)

# 扇出：START 同时连到三个节点（并行执行）
builder.add_edge(START, "summarize")
builder.add_edge(START, "extract_keywords")
builder.add_edge(START, "translate")

# 扇入：三个节点都连到 merge
builder.add_edge("summarize", "merge")
builder.add_edge("extract_keywords", "merge")
builder.add_edge("translate", "merge")

builder.add_edge("merge", END)

parallel_graph = builder.compile()

# 测试
result = parallel_graph.invoke({
    "text": "LangGraph 是 LangChain 团队推出的图编排框架，专门用于构建有状态的 Agent 工作流。它支持条件路由、循环和并行执行。",
    "summary": "",
    "keywords": "",
    "translation": "",
    "result": "",
})
print(f"结果:\n{result['result']}")

# 流式查看并行执行
print("\n--- 流式（并行） ---")
for event in parallel_graph.stream({
    "text": "Python 是一种广泛使用的高级编程语言。",
    "summary": "", "keywords": "", "translation": "", "result": "",
}):
    for node, output in event.items():
        print(f"  [{node}] done")
```

### 3.2 子图（Subgraph）

```python
"""
子图：把复杂图拆成可复用的模块
子图可以作为一个节点嵌入到更大的图中
"""

# === 定义子图：RAG 检索子图 ===

class RAGState(TypedDict):
    query: str
    retrieved_docs: str
    rag_answer: str

def retrieve_node(state: RAGState) -> dict:
    """模拟检索"""
    return {"retrieved_docs": f"关于'{state['query']}'的模拟文档内容..."}

def generate_node(state: RAGState) -> dict:
    """模拟生成"""
    response = llm.invoke(
        f"根据以下文档回答问题: {state['retrieved_docs']}\n问题: {state['query']}"
    )
    return {"rag_answer": response.content}

# 构建子图
rag_builder = StateGraph(RAGState)
rag_builder.add_node("retrieve", retrieve_node)
rag_builder.add_node("generate", generate_node)
rag_builder.add_edge(START, "retrieve")
rag_builder.add_edge("retrieve", "generate")
rag_builder.add_edge("generate", END)
rag_subgraph = rag_builder.compile()

# === 定义主图 ===

class MainState(TypedDict):
    question: str
    need_rag: bool
    rag_result: str
    direct_answer: str
    final_answer: str

def check_need_rag(state: MainState) -> dict:
    """判断是否需要 RAG 检索"""
    response = llm.invoke(
        f"判断以下问题是否需要检索知识库才能回答，只回答 yes 或 no: {state['question']}"
    )
    need = "yes" in response.content.lower()
    return {"need_rag": need}

def rag_node(state: MainState) -> dict:
    """使用 RAG 子图"""
    # 直接调用子图
    rag_result = rag_subgraph.invoke({"query": state["question"]})
    return {"rag_result": rag_result["rag_answer"]}

def direct_answer_node(state: MainState) -> dict:
    """直接回答"""
    response = llm.invoke(state["question"])
    return {"direct_answer": response.content}

def final_merge_node(state: MainState) -> dict:
    """合并最终结果"""
    if state.get("rag_result"):
        return {"final_answer": f"[RAG] {state['rag_result']}"}
    return {"final_answer": f"[直接] {state['direct_answer']}"}

def route_by_rag(state: MainState) -> str:
    return "rag_node" if state["need_rag"] else "direct_answer"

# 构建主图
main_builder = StateGraph(MainState)
main_builder.add_node("check", check_need_rag)
main_builder.add_node("rag_node", rag_node)
main_builder.add_node("direct_answer", direct_answer_node)
main_builder.add_node("merge", final_merge_node)

main_builder.add_edge(START, "check")
main_builder.add_conditional_edges("check", route_by_rag, {
    "rag_node": "rag_node",
    "direct_answer": "direct_answer",
})
main_builder.add_edge("rag_node", "merge")
main_builder.add_edge("direct_answer", "merge")
main_builder.add_edge("merge", END)

main_graph = main_builder.compile()

# 测试
questions = ["1+1等于几？", "LangGraph 是什么？"]
for q in questions:
    result = main_graph.invoke({
        "question": q,
        "need_rag": False,
        "rag_result": "",
        "direct_answer": "",
        "final_answer": "",
    })
    print(f"\n问题: {q}")
    print(f"需要RAG: {result['need_rag']}")
    print(f"最终: {result['final_answer'][:80]}...")
```

### Day 3 小结

```
Day 3 核心概念：
┌──────────────────────────────────────────────┐
│  并行执行                                     │
│  add_edge(START, A) + add_edge(START, B)    │
│  → A 和 B 并行执行                            │
│  add_edge(A, C) + add_edge(B, C)            │
│  → C 等待 A 和 B 都完成后执行                 │
│                                                │
│  子图                                         │
│  子图 = 一个编译好的 graph                    │
│  可作为节点嵌入父图: add_node("x", subgraph) │
│  也可以在节点函数内调用: subgraph.invoke()   │
│                                                │
│  适用场景：                                    │
│  并行 → 多角度分析、多语言翻译                 │
│  子图 → RAG 检索模块、代码执行模块复用         │
└──────────────────────────────────────────────┘
```

### Day 3 练习

1. 构建一个并行图：同时生成"正面评价"和"反面评价"，然后合并为综合分析
2. 把 Day 2 的 ReAct Agent 封装成子图，嵌入到一个更大的工作流中（先判断是否需要工具，需要则调用 Agent 子图，不需要直接回答）
3. 给并行图添加超时处理——如果某个分支超过 10 秒，跳过该分支

<details>
<summary>参考答案</summary>

```python
"""Day 3 练习答案：并行评价 + Agent 子图 + 超时处理"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.3,
)

# === 练习 1：并行正反评价 ===

class ReviewState(TypedDict):
    topic: str
    pros: str
    cons: str
    summary: str

def pros_node(state: ReviewState) -> dict:
    resp = llm.invoke(f"列出 {state['topic']} 的3个优点")
    return {"pros": resp.content}

def cons_node(state: ReviewState) -> dict:
    resp = llm.invoke(f"列出 {state['topic']} 的3个缺点")
    return {"cons": resp.content}

def summary_node(state: ReviewState) -> dict:
    resp = llm.invoke(
        f"综合以下正反评价给出总结: \n优点: {state['pros']}\n缺点: {state['cons']}"
    )
    return {"summary": resp.content}

builder = StateGraph(ReviewState)
builder.add_node("pros", pros_node)
builder.add_node("cons", cons_node)
builder.add_node("summary", summary_node)

builder.add_edge(START, "pros")
builder.add_edge(START, "cons")
builder.add_edge("pros", "summary")
builder.add_edge("cons", "summary")
builder.add_edge("summary", END)

review_graph = builder.compile()
result = review_graph.invoke({"topic": "Python", "pros": "", "cons": "", "summary": ""})
print(f"优点: {result['pros'][:80]}...")
print(f"缺点: {result['cons'][:80]}...")
print(f"总结: {result['summary'][:80]}...")

# === 练习 2：Agent 子图嵌入 ===

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {e}"

@tool
def search_info(query: str) -> str:
    """搜索信息（模拟）。"""
    return f"模拟搜索: {query}"

tools = [calculator, search_info]
tools_map = {t.name: t for t in tools}
llm_tools = llm.bind_tools(tools)

class AgentState(TypedDict):
    messages: Annotated[list, add]
    iterations: int
    final_answer: str

def agent_node(state: AgentState) -> dict:
    resp = llm_tools.invoke(state["messages"])
    if resp.tool_calls:
        return {"messages": [resp], "iterations": state["iterations"] + 1}
    return {"messages": [resp], "iterations": state["iterations"] + 1,
            "final_answer": resp.content}

def tool_node(state: AgentState) -> dict:
    last = state["messages"][-1]
    results = []
    for tc in last.tool_calls:
        func = tools_map.get(tc["name"])
        r = func.invoke(tc["args"]) if func else "未知工具"
        results.append(ToolMessage(content=str(r), tool_call_id=tc["id"]))
    return {"messages": results}

def should_continue(state: AgentState) -> str:
    if state["iterations"] >= 5:
        return END
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

# Agent 子图
agent_builder = StateGraph(AgentState)
agent_builder.add_node("agent", agent_node)
agent_builder.add_node("tools", tool_node)
agent_builder.add_edge(START, "agent")
agent_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
agent_builder.add_edge("tools", "agent")
agent_subgraph = agent_builder.compile()

# 主图
class MainState(TypedDict):
    question: str
    needs_tools: bool
    direct_answer: str
    agent_result: str
    final_answer: str

def check_tools(state: MainState) -> dict:
    resp = llm.invoke(
        f"判断以下问题是否需要使用计算器或搜索工具，只回答 yes 或 no: {state['question']}"
    )
    return {"needs_tools": "yes" in resp.content.lower()}

def use_agent(state: MainState) -> dict:
    result = agent_subgraph.invoke({
        "messages": [HumanMessage(content=state["question"])],
        "iterations": 0, "final_answer": "",
    })
    return {"agent_result": result.get("final_answer", "Agent 未能完成")}

def direct_answer(state: MainState) -> dict:
    resp = llm.invoke(state["question"])
    return {"direct_answer": resp.content}

def merge(state: MainState) -> dict:
    answer = state.get("agent_result") or state.get("direct_answer")
    return {"final_answer": answer}

def route(state: MainState) -> str:
    return "use_agent" if state["needs_tools"] else "direct_answer"

main_builder = StateGraph(MainState)
main_builder.add_node("check", check_tools)
main_builder.add_node("use_agent", use_agent)
main_builder.add_node("direct_answer", direct_answer)
main_builder.add_node("merge", merge)
main_builder.add_edge(START, "check")
main_builder.add_conditional_edges("check", route, {
    "use_agent": "use_agent", "direct_answer": "direct_answer"})
main_builder.add_edge("use_agent", "merge")
main_builder.add_edge("direct_answer", "merge")
main_builder.add_edge("merge", END)
main_graph = main_builder.compile()

# 测试
for q in ["1+1等于几", "计算 123*456", "什么是人工智能"]:
    r = main_graph.invoke({"question": q, "needs_tools": False,
                           "direct_answer": "", "agent_result": "", "final_answer": ""})
    print(f"\n  Q: {q} → needs_tools={r['needs_tools']} → {r['final_answer'][:60]}...")

# === 练习 3：超时处理 ===

import asyncio

class TimeoutState(TypedDict):
    query: str
    fast_result: str
    slow_result: str
    final: str

async def fast_node(state: TimeoutState) -> dict:
    await asyncio.sleep(0.5)
    return {"fast_result": "快速完成"}

async def slow_node(state: TimeoutState) -> dict:
    await asyncio.sleep(15)  # 模拟超时
    return {"slow_result": "慢速完成"}

async def merge_with_timeout(state: TimeoutState) -> dict:
    fast = state.get("fast_result", "")
    slow = state.get("slow_result", "")
    return {"final": f"快速: {fast}, 慢速: {slow or '(超时跳过)'}"}

# 超时通过 async 调用 + asyncio.wait_for 实现
# LangGraph 本身不直接支持节点级超时，但可以在节点内部使用 asyncio.wait_for
async def fast_node_with_timeout(state: TimeoutState) -> dict:
    try:
        result = await asyncio.wait_for(asyncio.sleep(0.5), timeout=10)
        return {"fast_result": "快速完成"}
    except asyncio.TimeoutError:
        return {"fast_result": "(超时)"}

async def slow_node_with_timeout(state: TimeoutState) -> dict:
    try:
        await asyncio.wait_for(asyncio.sleep(15), timeout=10)
        return {"slow_result": "慢速完成"}
    except asyncio.TimeoutError:
        return {"slow_result": "(超时跳过)"}

print("\n练习3完成: 超时通过 asyncio.wait_for 在节点内部实现")
```

</details>

---

## Day 4：人机交互（Human-in-the-Loop）

> 很多 Agent 场景需要人类介入审批、修改或确认。LangGraph 原生支持中断（interrupt）和恢复（resume）。

### 4.1 人机交互模式

```
┌────────── 人机交互（HITL）模式 ──────────┐
│                                           │
│  ┌──────┐    ┌──────┐    ┌──────┐       │
│  │  AI  │ →  │ 审核 │ →  │ 执行 │       │
│  │ 生成 │    │ 中断 │    │ 继续 │       │
│  └──────┘    └──┬───┘    └──────┘       │
│                 │                         │
│           ┌─────┴─────┐                  │
│           ↓           ↓                  │
│       [人类审批]   [人类修改]             │
│           │           │                  │
│       approve      edit                 │
│           │           │                  │
│           └─────┬─────┘                  │
│                 ↓                        │
│           [恢复执行]                     │
│                                           │
└───────────────────────────────────────────┘
```

创建文件 `day4_hitl.py`：

```python
"""
Day 4: 人机交互（Human-in-the-Loop）
- interrupt 中断
- Command 恢复
- 审批/修改/拒绝
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 1. 基础中断：审批模式 ===

class ReviewState(TypedDict):
    task: str
    draft: str          # AI 生成的草稿
    approved: bool       # 是否被批准
    final_output: str    # 最终输出

def generate_draft(state: ReviewState) -> dict:
    """AI 生成草稿"""
    response = llm.invoke(f"请为以下任务生成一个执行方案（50字以内）: {state['task']}")
    return {"draft": response.content}

def human_review(state: ReviewState) -> dict:
    """人类审核——中断等待人类输入"""
    draft = state["draft"]

    # interrupt() 会暂停图执行，等待外部输入
    # 输入内容会作为 interrupt() 的返回值
    human_input = interrupt({
        "prompt": "请审核以下方案",
        "draft": draft,
        "options": ["approve", "reject", "edit"],
    })

    # 人类输入的格式: {"action": "approve"} 或 {"action": "edit", "content": "修改后的内容"}
    action = human_input.get("action", "approve")

    if action == "approve":
        return {"approved": True, "final_output": draft}
    elif action == "edit":
        edited = human_input.get("content", draft)
        return {"approved": True, "final_output": edited}
    else:  # reject
        return {"approved": False, "final_output": ""}

def execute_task(state: ReviewState) -> dict:
    """执行已批准的任务"""
    return {"final_output": f"已执行: {state['final_output']}"}

def rejected_handler(state: ReviewState) -> dict:
    """拒绝处理"""
    return {"final_output": "任务被拒绝"}

def route_after_review(state: ReviewState) -> str:
    return "execute" if state["approved"] else "rejected"

# 构建图
builder = StateGraph(ReviewState)
builder.add_node("generate", generate_draft)
builder.add_node("review", human_review)
builder.add_node("execute", execute_task)
builder.add_node("rejected", rejected_handler)

builder.add_edge(START, "generate")
builder.add_edge("generate", "review")
builder.add_conditional_edges("review", route_after_review, {
    "execute": "execute",
    "rejected": "rejected",
})
builder.add_edge("execute", END)
builder.add_edge("rejected", END)

# 注意：interrupt() 需要 checkpointer 支持
# 节点内部的 interrupt() 会暂停执行，等待外部 Command(resume=...) 恢复

# === 运行（模拟人类交互） ===

# 第一次调用：会在 review 节点的 interrupt() 处中断
print("=== 第一次调用（会被中断） ===")
config = {"configurable": {"thread_id": "thread_1"}}

# 使用 Checkpointer 来支持中断/恢复
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
graph = builder.compile(
    checkpointer=checkpointer,
)

result = graph.invoke({"task": "写一篇关于 Python 的技术博客", "draft": "", "approved": False, "final_output": ""}, config)
print(f"草稿: {result['draft']}")
print("（图已暂停，等待人类审核）")

# 模拟人类审核（实际应用中由 UI 触发）
print("\n=== 恢复执行（模拟人类批准） ===")
result = graph.invoke(
    Command(resume={"action": "approve"}),
    config,
)
print(f"最终: {result['final_output']}")

# === 2. 模拟拒绝 ===

print("\n=== 第二次调用（模拟拒绝） ===")
config2 = {"configurable": {"thread_id": "thread_2"}}
result = graph.invoke({"task": "删除数据库", "draft": "", "approved": False, "final_output": ""}, config2)
print(f"草稿: {result['draft']}")
print("（等待审核）")

result = graph.invoke(
    Command(resume={"action": "reject"}),
    config2,
)
print(f"最终: {result['final_output']}")

# === 3. 模拟修改 ===

print("\n=== 第三次调用（模拟修改） ===")
config3 = {"configurable": {"thread_id": "thread_3"}}
result = graph.invoke({"task": "发送邮件通知", "draft": "", "approved": False, "final_output": ""}, config3)
print(f"草稿: {result['draft']}")

result = graph.invoke(
    Command(resume={"action": "edit", "content": "修改后的方案：先发测试邮件，确认格式无误后再群发"}),
    config3,
)
print(f"最终: {result['final_output']}")
```

### 4.2 实用场景：工具调用前审批

```python
"""
实用场景：危险工具调用前需要人类确认
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# 需要审批的工具
DANGEROUS_TOOLS = {"delete_file", "send_email", "run_shell"}

@tool
def read_file(path: str) -> str:
    """读取文件（安全工具）"""
    return f"文件内容: {path}"

@tool
def delete_file(path: str) -> str:
    """删除文件（危险工具，需要审批）"""
    return f"已删除: {path}"

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件（危险工具，需要审批）"""
    return f"已发送邮件到 {to}"

@tool
def calculator(expression: str) -> str:
    """计算数学表达式（安全工具）"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {e}"

tools = [read_file, delete_file, send_email, calculator]
tools_map = {t.name: t for t in tools}
llm_tools = llm.bind_tools(tools)

class SafeAgentState(TypedDict):
    messages: Annotated[list, add]
    iterations: int
    pending_tool: dict     # 待审批的工具调用
    approved: bool
    final_answer: str

def agent_node(state: SafeAgentState) -> dict:
    resp = llm_tools.invoke(state["messages"])
    return {"messages": [resp], "iterations": state["iterations"] + 1}

def check_tool_safety(state: SafeAgentState) -> dict:
    """检查工具是否需要审批"""
    last = state["messages"][-1]
    if not hasattr(last, "tool_calls") or not last.tool_calls:
        return {"final_answer": last.content, "pending_tool": None}

    # 检查工具是否危险
    tool_calls = last.tool_calls
    needs_approval = any(tc["name"] in DANGEROUS_TOOLS for tc in tool_calls)

    if not needs_approval:
        # 安全工具，直接执行
        results = []
        for tc in tool_calls:
            func = tools_map.get(tc["name"])
            r = func.invoke(tc["args"]) if func else "未知工具"
            results.append(ToolMessage(content=str(r), tool_call_id=tc["id"]))
        return {"messages": results, "pending_tool": None}

    # 危险工具，中断等待审批
    first_dangerous = next(tc for tc in tool_calls if tc["name"] in DANGEROUS_TOOLS)
    return {"pending_tool": first_dangerous}

def human_approve(state: SafeAgentState) -> dict:
    """人类审批"""
    tool_info = state["pending_tool"]
    human_input = interrupt({
        "prompt": "以下工具调用需要审批",
        "tool": tool_info["name"],
        "args": tool_info["args"],
    })

    if human_input.get("approved"):
        # 执行工具
        func = tools_map.get(tool_info["name"])
        result = func.invoke(tool_info["args"]) if func else "未知工具"
        return {
            "messages": [ToolMessage(content=str(result), tool_call_id=tool_info["id"])],
            "approved": True,
            "pending_tool": None,
        }
    else:
        return {
            "messages": [ToolMessage(content="用户拒绝了此操作", tool_call_id=tool_info["id"])],
            "approved": False,
            "pending_tool": None,
        }

def route_safety(state: SafeAgentState) -> str:
    if state.get("final_answer"):
        return END
    if state.get("pending_tool"):
        return "approve"
    return "tools_execute"

def execute_tools(state: SafeAgentState) -> dict:
    """安全工具直接执行的结果已在 check_tool_safety 中处理"""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        # 安全工具已被执行，消息已添加
        pass
    return {}

def should_continue(state: SafeAgentState) -> str:
    if state["iterations"] >= 5:
        return END
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "check_safety"
    return END

# 构建图
builder = StateGraph(SafeAgentState)
builder.add_node("agent", agent_node)
builder.add_node("check_safety", check_tool_safety)
builder.add_node("approve", human_approve)
builder.add_node("tools_execute", execute_tools)

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"check_safety": "check_safety", END: END})
builder.add_conditional_edges("check_safety", route_safety, {
    "approve": "approve",
    "tools_execute": "tools_execute",
    END: END,
})
builder.add_edge("approve", "agent")
builder.add_edge("tools_execute", "agent")

checkpointer = MemorySaver()
safe_graph = builder.compile(checkpointer=checkpointer)

# 测试：安全工具（直接执行）
print("=== 安全工具测试 ===")
config = {"configurable": {"thread_id": "safe_1"}}
result = safe_graph.invoke({
    "messages": [HumanMessage(content="计算 2+2")],
    "iterations": 0, "pending_tool": None, "approved": False, "final_answer": "",
}, config)
print(f"结果: {result.get('final_answer', '已完成')[:80]}")

# 测试：危险工具（需要审批）
print("\n=== 危险工具测试（需审批） ===")
config2 = {"configurable": {"thread_id": "safe_2"}}
result = safe_graph.invoke({
    "messages": [HumanMessage(content="删除 /tmp/test.txt 文件")],
    "iterations": 0, "pending_tool": None, "approved": False, "final_answer": "",
}, config2)
print(f"待审批: {result.get('pending_tool')}")

# 模拟批准
result = safe_graph.invoke(Command(resume={"approved": True}), config2)
print(f"最终: {result.get('final_answer', '已执行')[:80]}")
```

### Day 4 小结

```
Day 4 核心概念：
┌─────────────────────────────────────────────────┐
│  人机交互（Human-in-the-Loop）                    │
│                                                   │
│  核心机制：                                        │
│  interrupt(data)     → 暂停执行，等待人类输入      │
│  Command(resume=...) → 恢复执行，传入人类输入      │
│                                                   │
│  实现要素：                                        │
│  1. checkpointer     → 保存图状态（MemorySaver）   │
│  2. thread_id        → 标识会话                    │
│  3. interrupt_before → 在指定节点前中断            │
│  4. interrupt()      → 在节点内部主动中断          │
│                                                   │
│  常见模式：                                        │
│  ├── 审批模式：approve / reject                   │
│  ├── 修改模式：edit + 新内容                      │
│  ├── 危险工具确认：执行前人类确认                  │
│  └── 交互式对话：中途补充信息                     │
└─────────────────────────────────────────────────┘
```

### Day 4 练习

1. 构建一个"邮件发送审批流"：AI 起草邮件 → 人类审核（可修改） → 发送/取消
2. 构建一个"代码执行审批流"：AI 生成代码 → 人类审核 → 执行/修改/拒绝
3. 添加"自动审批"模式——对于安全操作（如 print）自动通过，危险操作（如 `os.remove`）才中断

<details>
<summary>参考答案</summary>

```python
"""Day 4 练习答案：邮件审批 + 代码审批 + 自动审批"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 练习 1：邮件发送审批流 ===

class EmailState(TypedDict):
    recipient: str
    topic: str
    draft: str
    final_email: str
    status: str

def draft_email(state: EmailState) -> dict:
    resp = llm.invoke(f"请起草一封邮件给{state['recipient']}，主题是{state['topic']}，100字以内")
    return {"draft": resp.content}

def review_email(state: EmailState) -> dict:
    human = interrupt({"prompt": "请审核邮件", "draft": state["draft"]})
    action = human.get("action", "send")
    if action == "send":
        return {"final_email": state["draft"], "status": "sent"}
    elif action == "edit":
        return {"final_email": human.get("content", state["draft"]), "status": "sent"}
    return {"status": "cancelled"}

def send_email(state: EmailState) -> dict:
    return {"status": f"已发送给 {state['recipient']}: {state['final_email'][:50]}..."}

builder = StateGraph(EmailState)
builder.add_node("draft", draft_email)
builder.add_node("review", review_email)
builder.add_node("send", send_email)
builder.add_edge(START, "draft")
builder.add_edge("draft", "review")
builder.add_conditional_edges("review", lambda s: "send" if s["status"] == "sent" else END,
                              {"send": "send", END: END})
builder.add_edge("send", END)

checkpointer = MemorySaver()
email_graph = builder.compile(checkpointer=checkpointer)

# 测试
config = {"configurable": {"thread_id": "email_1"}}
result = email_graph.invoke({"recipient": "张三", "topic": "项目进度更新",
                             "draft": "", "final_email": "", "status": ""}, config)
print(f"草稿: {result['draft'][:60]}...")

# 模拟批准
result = email_graph.invoke(Command(resume={"action": "send"}), config)
print(f"状态: {result['status']}")

# === 练习 2：代码执行审批流 ===

class CodeState(TypedDict):
    task: str
    code: str
    result: str
    status: str

def generate_code(state: CodeState) -> dict:
    resp = llm.invoke(f"用 Python 实现以下任务，只输出代码: {state['task']}")
    return {"code": resp.content}

def review_code(state: CodeState) -> dict:
    human = interrupt({"prompt": "审核代码", "code": state["code"]})
    action = human.get("action", "run")
    if action == "run":
        return {"status": "approved"}
    elif action == "edit":
        return {"code": human.get("content", state["code"]), "status": "approved"}
    return {"status": "rejected"}

def run_code(state: CodeState) -> dict:
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(state["code"], {"__builtins__": {"print": print, "range": range,
                "len": len, "str": str, "int": int, "list": list, "sum": sum}})
        return {"result": buf.getvalue().strip(), "status": "completed"}
    except Exception as e:
        return {"result": f"错误: {e}", "status": "error"}

builder = StateGraph(CodeState)
builder.add_node("generate", generate_code)
builder.add_node("review", review_code)
builder.add_node("run", run_code)
builder.add_edge(START, "generate")
builder.add_edge("generate", "review")
builder.add_conditional_edges("review", lambda s: "run" if s["status"] == "approved" else END,
                              {"run": "run", END: END})
builder.add_edge("run", END)

code_graph = builder.compile(checkpointer=checkpointer)

config2 = {"configurable": {"thread_id": "code_1"}}
result = code_graph.invoke({"task": "计算1到100的和", "code": "", "result": "", "status": ""}, config2)
print(f"\n生成代码: {result['code'][:60]}...")
result = code_graph.invoke(Command(resume={"action": "run"}), config2)
print(f"执行结果: {result.get('result', '')[:60]}")

# === 练习 3：自动审批 ===

SAFE_PATTERNS = ["print", "len", "range", "sum", "sorted", "max", "min", "abs"]
DANGEROUS_PATTERNS = ["os.remove", "os.system", "subprocess", "open(", "shutil", "__import__"]

def auto_approve(code: str) -> bool:
    """安全操作自动通过，危险操作需要人工审批"""
    code_lower = code.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in code_lower:
            return False  # 需要人工审批
    return True  # 自动通过

# 测试
print("\n自动审批测试:")
print(f"  print('hello') → 自动通过: {auto_approve(\"print('hello')\")}")
print(f"  os.remove('x') → 需审批: {not auto_approve(\"os.remove('x')\")}")
```

</details>

---

## Day 5：State 管理 + 持久化

> 生产级 Agent 需要状态持久化——程序重启后能恢复对话，多用户并发不互相干扰。

### 5.1 Checkpointer 持久化

```
┌────────────── LangGraph 持久化体系 ──────────────┐
│                                                    │
│  Checkpointer（检查点存储）                         │
│  ├── MemorySaver       → 内存（学习/测试用）        │
│  ├── SqliteSaver       → SQLite 文件持久化          │
│  ├── PostgresSaver     → PostgreSQL 生产级          │
│  └── 自定义            → 实现 BaseCheckpointSaver  │
│                                                    │
│  核心概念：                                         │
│  thread_id   → 会话标识（一个用户一个 thread）      │
│  checkpoint  → 图在某个节点的完整状态快照            │
│  checkpoint_ns → 命名空间（子图隔离）               │
│                                                    │
│  恢复方式：                                         │
│  graph.invoke(state, config) → 同 thread_id 自动   │
│                                 加载历史状态         │
│                                                    │
└────────────────────────────────────────────────────┘
```

创建文件 `day5_state_persistence.py`：

```python
"""
Day 5: State 管理 + 持久化
- MemorySaver vs SqliteSaver
- 多会话管理
- 状态回溯
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, AnyMessage

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.7,
)

# === 1. 对话 Agent + MemorySaver ===

class ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add]

def chat_node(state: ChatState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

builder = StateGraph(ChatState)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

# 使用 MemorySaver
memory_checkpointer = MemorySaver()
chat_graph = builder.compile(checkpointer=memory_checkpointer)

# 多轮对话（同一 thread_id 共享状态）
config = {"configurable": {"thread_id": "user_001"}}

print("=== 多轮对话 ===")
for msg in ["你好，我叫小华", "我喜欢 Python", "我叫什么名字？"]:
    result = chat_graph.invoke({"messages": [HumanMessage(content=msg)]}, config)
    last = result["messages"][-1]
    print(f"  用户: {msg}")
    print(f"  AI: {last.content[:60]}...")

# 不同 thread_id —— 全新对话
config2 = {"configurable": {"thread_id": "user_002"}}
result = chat_graph.invoke({"messages": [HumanMessage(content="我叫什么名字？")]}, config2)
print(f"\n新会话: {result['messages'][-1].content[:60]}...")

# === 2. 查看历史状态 ===

print("\n=== 查看 thread 历史状态 ===")
for checkpoint in memory_checkpointer.list(config):
    print(f"  step={checkpoint.metadata.get('step', '?')}, "
          f"messages={len(checkpoint.values.get('messages', []))}")

# === 3. SQLite 持久化 ===

from langgraph.checkpoint.sqlite import SqliteSaver

# SQLite 持久化（文件保存，重启不丢失）
sqlite_path = "./chat_checkpoints.db"
sqlite_saver = SqliteSaver.from_conn_string(sqlite_path)

# 注意：SqliteSaver 需要上下文管理器
with SqliteSaver.from_conn_string(sqlite_path) as checkpointer:
    sqlite_graph = builder.compile(checkpointer=checkpointer)

    config3 = {"configurable": {"thread_id": "sqlite_001"}}
    result = sqlite_graph.invoke(
        {"messages": [HumanMessage(content="请记住：我是前端开发工程师")]},
        config3,
    )
    print(f"\nSQLite 持久化: {result['messages'][-1].content[:60]}...")

    # 第二次调用（同一 thread，自动加载历史）
    result = sqlite_graph.invoke(
        {"messages": [HumanMessage(content="我的职业是什么？")]},
        config3,
    )
    print(f"验证记忆: {result['messages'][-1].content[:60]}...")

# 重启后只需用相同的 db 文件和 thread_id 即可恢复
print("\nSQLite 检查点已保存到:", sqlite_path)

# === 4. 多用户并发 ===

print("\n=== 多用户并发 ===")
users = ["user_a", "user_b", "user_c"]
for user in users:
    cfg = {"configurable": {"thread_id": user}}
    result = chat_graph.invoke(
        {"messages": [
            SystemMessage(content="你是个人助手"),
            HumanMessage(content=f"你好，我是{user}"),
        ]},
        cfg,
    )
    print(f"  {user}: {result['messages'][-1].content[:40]}...")

# 验证每个用户的状态独立
for user in users:
    cfg = {"configurable": {"thread_id": user}}
    state = chat_graph.get_state(cfg)
    msgs = state.values.get("messages", [])
    print(f"  {user} 有 {len(msgs)} 条消息")
```

### 5.2 状态回溯与重放

```python
"""
状态回溯：回到之前的某个 checkpoint，修改输入后重新执行
"""

from langgraph.checkpoint.memory import MemorySaver

# 构建一个可回溯的图
class WorkState(TypedDict):
    input: str
    step1_result: str
    step2_result: str
    final: str

def step1(state: WorkState) -> dict:
    return {"step1_result": f"处理: {state['input']}"}

def step2(state: WorkState) -> dict:
    return {"step2_result": f"深化: {state['step1_result']}"}

def step3(state: WorkState) -> dict:
    return {"final": f"完成: {state['step2_result']}"}

builder = StateGraph(WorkState)
builder.add_node("step1", step1)
builder.add_node("step2", step2)
builder.add_node("step3", step3)
builder.add_edge(START, "step1")
builder.add_edge("step1", "step2")
builder.add_edge("step2", "step3")
builder.add_edge("step3", END)

checkpointer = MemorySaver()
work_graph = builder.compile(checkpointer=checkpointer)

# 第一次执行
config = {"configurable": {"thread_id": "replay_1"}}
result = work_graph.invoke({"input": "原始输入"}, config)
print(f"原始结果: {result['final']}")

# 查看所有 checkpoint
print("\n所有 checkpoint:")
states = list(checkpointer.list(config))
for s in states:
    print(f"  step={s.metadata.get('step')}, values={list(s.values.keys())}")

# 回溯到 step1 之后的状态，修改输入
if len(states) >= 2:
    # 获取历史状态
    history = list(checkpointer.get(config))
    print(f"\n历史记录数: {len(states)}")

# 重新执行（不同输入，同一 thread 会覆盖）
config2 = {"configurable": {"thread_id": "replay_2"}}
result2 = work_graph.invoke({"input": "修改后的输入"}, config2)
print(f"\n重放结果: {result2['final']}")
```

### Day 5 小结

```
Day 5 核心概念：
┌────────────────────────────────────────────────┐
│  Checkpointer 持久化                             │
│                                                  │
│  MemorySaver    → 内存，重启丢失                  │
│  SqliteSaver    → 文件持久化，重启恢复            │
│  PostgresSaver  → 生产级，多进程安全              │
│                                                  │
│  使用方式：                                       │
│  graph = builder.compile(checkpointer=saver)    │
│  config = {"configurable": {"thread_id": "xxx"}}│
│  graph.invoke(state, config)                     │
│                                                  │
│  关键能力：                                       │
│  1. 同 thread_id 自动加载历史状态                 │
│  2. 不同 thread_id 状态隔离（多用户）             │
│  3. checkpoint.list(config) 查看历史             │
│  4. graph.get_state(config) 获取当前状态          │
│  5. 可回溯到之前的状态重新执行                     │
└────────────────────────────────────────────────┘
```

### Day 5 练习

1. 用 `SqliteSaver` 构建一个持久化对话 Agent，关闭程序后重新打开能恢复对话
2. 创建 3 个用户的并发会话，验证每个用户的对话历史互不干扰
3. 实现一个"时间旅行"功能——列出所有 checkpoint，选择一个回到那个时间点重新对话

<details>
<summary>参考答案</summary>

```python
"""Day 5 练习答案：持久化对话 + 多用户 + 时间旅行"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AnyMessage

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.7,
)

class ChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add]

def chat_node(state: ChatState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(ChatState)
builder.add_node("chat", chat_node)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)

# === 练习 1：SQLite 持久化 ===

db_path = "./practice_checkpoints.db"

def run_persistent_chat():
    with SqliteSaver.from_conn_string(db_path) as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)
        config = {"configurable": {"thread_id": "persistent_user"}}

        # 第一轮
        result = graph.invoke(
            {"messages": [HumanMessage(content="你好，我叫小华，我在学 LangGraph")]},
            config,
        )
        print(f"AI: {result['messages'][-1].content[:60]}...")

        # 第二轮（验证记忆）
        result = graph.invoke(
            {"messages": [HumanMessage(content="我叫什么？我在学什么？")]},
            config,
        )
        print(f"AI: {result['messages'][-1].content[:60]}...")

print("=== 练习 1: SQLite 持久化 ===")
run_persistent_chat()
print(f"检查点已保存到 {db_path}，重启程序后用同一 thread_id 即可恢复\n")

# === 练习 2：多用户并发 ===

print("=== 练习 2: 多用户并发 ===")
memory_saver = MemorySaver()
multi_graph = builder.compile(checkpointer=memory_saver)

users = [
    ("alice", "我喜欢 Python"),
    ("bob", "我在学 JavaScript"),
    ("charlie", "我做后端开发"),
]

# 每个用户发送消息
for user_id, msg in users:
    cfg = {"configurable": {"thread_id": user_id}}
    multi_graph.invoke({"messages": [HumanMessage(content=msg)]}, cfg)

# 验证状态隔离
for user_id, _ in users:
    cfg = {"configurable": {"thread_id": user_id}}
    state = multi_graph.get_state(cfg)
    msgs = state.values.get("messages", [])
    first_human = next((m for m in msgs if isinstance(m, HumanMessage)), None)
    print(f"  {user_id}: {len(msgs)} 条消息, 首条: {first_human.content if first_human else '无'}")

# === 练习 3：时间旅行 ===

print("\n=== 练习 3: 时间旅行 ===")

# 用 MemorySaver 方便演示
time_saver = MemorySaver()
time_graph = builder.compile(checkpointer=time_saver)
config = {"configurable": {"thread_id": "time_travel"}}

# 多轮对话
for i in range(4):
    time_graph.invoke(
        {"messages": [HumanMessage(content=f"这是第 {i+1} 条消息")]},
        config,
    )

# 列出所有 checkpoint
print("历史 checkpoint:")
checkpoints = list(time_saver.list(config))
for cp in checkpoints:
    step = cp.metadata.get("step", "?")
    msg_count = len(cp.values.get("messages", []))
    print(f"  step={step}, messages={msg_count}")

# 回到第 2 步（时间旅行）
if len(checkpoints) >= 2:
    # 获取目标 checkpoint 的配置
    target_checkpoint = checkpoints[-3] if len(checkpoints) >= 3 else checkpoints[0]
    target_config = target_checkpoint.config

    # 从该 checkpoint 恢复
    time_graph.update_state(config, values={"messages": []}, as_node=None)

    # 实际使用中可以通过 graph.get_state_history(config) 遍历
    print("\n时间旅行：可从任意 checkpoint 恢复状态")
    print("API: graph.get_state_history(config) → 获取所有历史状态")
    print("API: graph.invoke(state, config) → 从指定状态继续")

# 演示 get_state_history
print("\n状态历史:")
for state in time_graph.get_state_history(config):
    step = state.metadata.get("step", "?")
    msgs = len(state.values.get("messages", []))
    print(f"  step={step}, messages={msgs}, config={state.config}")
```

</details>

---
