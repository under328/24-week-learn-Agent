# 第2月第7周：Multi-Agent 系统

> 适用对象：已完成 Week 1-6（Python基础 + LLM核心 + Prompt Engineering + RAG/Multi-Tool Agent + LangChain框架 + LangGraph状态机）的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：掌握多 Agent 协作的核心模式，能用 LangGraph 构建 Multi-Agent 系统，理解 Supervisor/Swarm/Hierarchical 三种编排架构

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month2/week7
cd month2/week7

python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 本周依赖（延续 Week 5-6）
pip install langchain langchain-core langchain-community langchain-openai langgraph httpx pydantic chromadb
pip freeze > requirements.txt
```

**关于 Multi-Agent**：单个 Agent 能力有限——一个 Agent 既要做 RAG 检索、又要写代码、还要做数据分析，prompt 会变得冗长，工具列表会变得复杂，LLM 的决策质量会下降。Multi-Agent 系统把复杂任务拆分给多个专业 Agent，每个 Agent 专注于一个领域，通过协作完成整体任务。

**本周核心问题**：
- 多个 Agent 如何分工？（任务分配）
- Agent 之间如何通信？（消息传递）
- 谁来协调 Agent？（编排模式）
- 如何避免无限循环？（终止条件）

---

## Day 1：Multi-Agent 全景 + 基础概念

> 理解为什么需要 Multi-Agent，以及三种经典编排模式。

### 1.1 从单 Agent 到 Multi-Agent

```
┌────────────── 单 Agent vs Multi-Agent ──────────────┐
│                                                      │
│  单 Agent（Week 4-6）：                               │
│  ┌──────────────────────────────────┐               │
│  │           一个 Agent              │               │
│  │  工具: RAG + 代码 + 计算 + 搜索   │               │
│  │  问题: prompt 冗长、工具冲突      │               │
│  │        决策质量随工具增多而下降   │               │
│  └──────────────────────────────────┘               │
│                                                      │
│  Multi-Agent（Week 7）：                             │
│  ┌──────────────────────────────────────┐           │
│  │  Supervisor（协调者）                  │           │
│  │  ┌──────┐ ┌──────┐ ┌──────┐         │           │
│  │  │ RAG  │ │ Code │ │ Data │  ...    │           │
│  │  │Agent │ │Agent │ │Agent │         │           │
│  │  └──────┘ └──────┘ └──────┘         │           │
│  │  每个 Agent 专注一个领域              │           │
│  │  优点: prompt 精简、专业度高          │           │
│  └──────────────────────────────────────┘           │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 1.2 三种经典编排模式

```
┌────────────── 三种 Multi-Agent 编排模式 ──────────────┐
│                                                        │
│  1. Supervisor（主管模式）                              │
│  ┌────────────┐                                        │
│  │  Supervisor │──→ 分配任务                            │
│  └─────┬──────┘                                        │
│        ├──→ Agent A ──→ 结果返回 Supervisor             │
│        ├──→ Agent B ──→ 结果返回 Supervisor             │
│        └──→ Agent C ──→ 结果返回 Supervisor             │
│  特点：中心化控制，Supervisor 决定调用谁                 │
│  适用：任务有明确分工，需要统一决策                      │
│                                                        │
│  2. Swarm（群智模式）                                   │
│  ┌──────┐    ┌──────┐    ┌──────┐                    │
│  │Agent A│───→│Agent B│───→│Agent C│                 │
│  └──────┘    └──────┘    └──────┘                    │
│  特点：去中心化，Agent 之间直接传递控制权                │
│  适用：流水线式任务，每个 Agent 处理一个阶段             │
│                                                        │
│  3. Hierarchical（层级模式）                            │
│  ┌──────────────┐                                      │
│  │  Top Supervisor │                                   │
│  └───────┬───────┘                                     │
│     ┌────┴────┐                                        │
│     ↓         ↓                                        │
│  ┌──────┐  ┌──────────┐                               │
│  │Sub-A │  │Sub-Boss  │                                │
│  └──────┘  └────┬─────┘                                │
│                ├──────┐                                │
│                ↓      ↓                                │
│             ┌──────┐ ┌──────┐                         │
│             │Agent │ │Agent │                          │
│             └──────┘ └──────┘                         │
│  特点：多层管理，大任务拆成子任务再分配                   │
│  适用：复杂项目，需要多级拆解                            │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 1.3 Agent 通信机制

```
┌────────────── Agent 通信方式 ──────────────┐
│                                             │
│  1. 共享 State（LangGraph 主要方式）        │
│     所有 Agent 读写同一个 State 对象        │
│     通过 State 字段传递信息                 │
│     优点：简单直接                          │
│     缺点：State 可能变得很大                │
│                                             │
│  2. 消息传递（Message Passing）             │
│     Agent 之间发送结构化消息                │
│     类似微服务的 API 调用                   │
│     优点：解耦                              │
│     缺点：需要定义消息协议                  │
│                                             │
│  3. 黑板模式（Blackboard）                  │
│     共享一个"黑板"区域                      │
│     Agent 向黑板写入结果，其他 Agent 读取   │
│     优点：灵活                              │
│     缺点：可能产生竞争                      │
│                                             │
│  本周主要使用 LangGraph 的共享 State 方式   │
│                                             │
└─────────────────────────────────────────────┘
```

### 1.4 第一个 Multi-Agent 程序

创建文件 `day1_basics.py`：

```python
"""
Day 1: 第一个 Multi-Agent 程序
- 两个专业 Agent + 一个 Supervisor
- Supervisor 根据问题类型分配任务
"""

import os
from typing import TypedDict, Annotated, Literal
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

# === 配置 ===

def make_llm(temperature: float = 0.3) -> ChatOpenAI:
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temperature,
    )

# === State 定义 ===

class MultiAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str               # 当前任务
    route: str              # 路由决策
    result: str             # 最终结果
    agent_history: Annotated[list[str], add]  # 记录哪些 Agent 参与了

# === Supervisor 节点 ===

def supervisor_node(state: MultiAgentState) -> dict:
    """Supervisor：分析任务，决定分配给哪个 Agent"""
    llm = make_llm(temperature=0)
    task = state["task"]

    response = llm.invoke(
        f"你是一个任务调度器。根据用户任务选择最合适的处理者，只回答一个词：\n"
        f"- coder（代码编写/技术实现）\n"
        f"- writer（文案/文档/创意写作）\n"
        f"- done（任务已完成，无需更多处理）\n"
        f"任务: {task}"
    )
    route = response.content.strip().lower()

    # 清洗
    if "coder" in route:
        route = "coder"
    elif "writer" in route:
        route = "writer"
    elif "done" in route:
        route = "done"
    else:
        route = "coder"  # 默认

    return {"route": route, "agent_history": [f"supervisor→{route}"]}

# === Coder Agent ===

def coder_agent_node(state: MultiAgentState) -> dict:
    """代码 Agent：专注代码相关任务"""
    llm = make_llm(temperature=0.2)
    response = llm.invoke(
        f"你是一个 Python 编程专家。请完成以下任务，提供代码和简要说明：\n"
        f"任务: {state['task']}"
    )
    return {
        "result": response.content,
        "task": "done",  # 标记任务完成
        "agent_history": ["coder"],
    }

# === Writer Agent ===

def writer_agent_node(state: MultiAgentState) -> dict:
    """文案 Agent：专注写作任务"""
    llm = make_llm(temperature=0.7)
    response = llm.invoke(
        f"你是一个专业文案。请完成以下写作任务：\n"
        f"任务: {state['task']}"
    )
    return {
        "result": response.content,
        "task": "done",
        "agent_history": ["writer"],
    }

# === 路由函数 ===

def route_from_supervisor(state: MultiAgentState) -> str:
    route = state.get("route", "done")
    if route == "coder":
        return "coder"
    elif route == "writer":
        return "writer"
    return END

# === 构建图 ===

builder = StateGraph(MultiAgentState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("coder", coder_agent_node)
builder.add_node("writer", writer_agent_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_from_supervisor, {
    "coder": "coder",
    "writer": "writer",
    END: END,
})
# Agent 执行完后回到 supervisor（支持多步分配）
builder.add_edge("coder", "supervisor")
builder.add_edge("writer", "supervisor")

graph = builder.compile()

# === 测试 ===

tasks = [
    "用 Python 实现快速排序",
    "写一篇关于 AI 发展趋势的短文",
    "写一个计算斐波那契数列的函数",
]

for task in tasks:
    result = graph.invoke({
        "messages": [HumanMessage(content=task)],
        "task": task,
        "route": "",
        "result": "",
        "agent_history": [],
    })
    print(f"\n任务: {task}")
    print(f"执行路径: {result['agent_history']}")
    print(f"结果: {result['result'][:80]}...")
```

### Day 1 小结

```
Day 1 核心概念：
┌──────────────────────────────────────────────┐
│  Multi-Agent 三种编排模式                     │
│                                                │
│  Supervisor：中心化，主管分配任务               │
│  Swarm：去中心化，Agent 间传递控制权            │
│  Hierarchical：多层管理，任务逐级拆解          │
│                                                │
│  LangGraph 实现 Multi-Agent 的方式：           │
│  1. 每个 Agent 是图中的一个节点                │
│  2. Supervisor 是路由节点                      │
│  3. 条件边决定 Supervisor → 哪个 Agent        │
│  4. Agent 执行后回到 Supervisor（循环）        │
│  5. Supervisor 判断是否完成 → END              │
│                                                │
│  共享 State 通信：                             │
│  所有 Agent 读写同一个 State 对象              │
│  通过 task/result/route 等字段传递信息         │
└──────────────────────────────────────────────┘
```

### Day 1 练习

1. 在 Day 1 示例中添加第三个 Agent（如 `analyst` 数据分析 Agent），让 Supervisor 能路由到三个 Agent
2. 修改 Supervisor，支持"多步任务"——先让 coder 写代码，再让 writer 写文档说明
3. 用 `graph.stream()` 查看 Supervisor 模式的完整执行流程

<details>
<summary>参考答案</summary>

```python
"""Day 1 练习答案：三 Agent + 多步任务 + 流式查看"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str
    route: str
    result: str
    agent_history: Annotated[list[str], add]
    code_result: str   # coder 的结果

def supervisor(state: State) -> dict:
    llm = make_llm(0)
    task = state["task"]
    # 检查是否已有代码结果，如果有则让 writer 写文档
    if state.get("code_result"):
        return {"route": "writer", "agent_history": ["supervisor→writer"]}

    response = llm.invoke(
        f"选择处理者（只回答一个词）:\n"
        f"coder / writer / analyst / done\n"
        f"任务: {task}"
    )
    route = response.content.strip().lower()
    for r in ["coder", "writer", "analyst", "done"]:
        if r in route:
            return {"route": r, "agent_history": [f"supervisor→{r}"]}
    return {"route": "coder", "agent_history": ["supervisor→coder"]}

def coder(state: State) -> dict:
    llm = make_llm(0.2)
    resp = llm.invoke(f"用 Python 完成: {state['task']}")
    return {"code_result": resp.content, "agent_history": ["coder"]}

def writer(state: State) -> dict:
    llm = make_llm(0.7)
    code = state.get("code_result", "")
    if code:
        resp = llm.invoke(f"为以下代码写使用文档: {code}")
    else:
        resp = llm.invoke(f"完成写作任务: {state['task']}")
    return {"result": resp.content, "task": "done", "agent_history": ["writer"]}

def analyst(state: State) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"作为数据分析师，分析: {state['task']}")
    return {"result": resp.content, "task": "done", "agent_history": ["analyst"]}

def router(state: State) -> str:
    r = state.get("route", "done")
    if r == "coder": return "coder"
    if r == "writer": return "writer"
    if r == "analyst": return "analyst"
    return END

builder = StateGraph(State)
builder.add_node("supervisor", supervisor)
builder.add_node("coder", coder)
builder.add_node("writer", writer)
builder.add_node("analyst", analyst)
builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", router, {
    "coder": "coder", "writer": "writer", "analyst": "analyst", END: END})
builder.add_edge("coder", "supervisor")
builder.add_edge("writer", "supervisor")
builder.add_edge("analyst", "supervisor")

graph = builder.compile()

# 练习 3：流式查看
print("=== 流式执行 ===")
for event in graph.stream({
    "messages": [HumanMessage(content="写一个排序函数并附上文档")],
    "task": "写一个排序函数并附上文档",
    "route": "", "result": "", "agent_history": [], "code_result": "",
}):
    for node, output in event.items():
        print(f"  [{node}] route={output.get('route', '-')}")
```

</details>

---

## Day 2：Supervisor 模式深入

> Supervisor 是最常用的 Multi-Agent 模式。今天深入实现一个完整的 Supervisor 系统。

### 2.1 Supervisor 架构详解

```
┌─────────── Supervisor 模式执行流程 ───────────┐
│                                                 │
│  START → Supervisor                             │
│            │                                    │
│            ├─ route=coder ──→ Coder ──→ Supervisor
│            ├─ route=writer ──→ Writer ──→ Supervisor
│            ├─ route=analyst ─→ Analyst ─→ Supervisor
│            └─ route=done ───→ END               │
│                                                 │
│  关键点：                                       │
│  1. Supervisor 是一个 LLM 节点（智能路由）      │
│  2. Agent 执行后返回 Supervisor（循环）         │
│  3. Supervisor 判断"任务是否完成"               │
│  4. 需要防止无限循环（最大轮次限制）            │
│                                                 │
│  State 设计要点：                               │
│  - messages: 完整对话历史                       │
│  - current_task: 当前未完成的子任务             │
│  - results: 各 Agent 的结果记录                 │
│  - next: Supervisor 的路由决策                  │
│  - iteration: 当前轮次（防死循环）              │
│                                                 │
└─────────────────────────────────────────────────┘
```

创建文件 `day2_supervisor.py`：

```python
"""
Day 2: Supervisor 模式深入
- 完整的 Supervisor 系统
- 多轮任务分配
- 结果汇总
"""

import os
from typing import TypedDict, Annotated, Literal
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, SystemMessage

# === 配置 ===

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === State 定义 ===

class SupervisorState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    original_task: str          # 原始用户请求
    next: str                   # Supervisor 路由决策
    results: Annotated[list[dict], add]  # 各 Agent 的结果
    iteration: int              # 当前轮次
    final_output: str           # 最终汇总输出

# === Agent 定义 ===

def research_agent(state: SupervisorState) -> dict:
    """研究 Agent：负责信息检索和分析"""
    llm = make_llm(0)
    context = f"原始任务: {state['original_task']}\n"
    if state.get("results"):
        prev = "; ".join(r["summary"] for r in state["results"])
        context += f"已有结果: {prev}\n"
    context += "请检索并分析相关信息，给出研究结论。"

    response = llm.invoke(context)
    return {
        "results": [{"agent": "researcher", "summary": response.content[:200]}],
        "messages": [AIMessage(content=f"[Researcher] {response.content}", name="researcher")],
        "iteration": state["iteration"] + 1,
    }

def coding_agent(state: SupervisorState) -> dict:
    """编码 Agent：负责代码编写"""
    llm = make_llm(0.2)
    context = f"原始任务: {state['original_task']}\n"
    if state.get("results"):
        prev = "; ".join(r["summary"] for r in state["results"])
        context += f"已有结果: {prev}\n"
    context += "请编写代码完成任务，提供完整的 Python 代码。"

    response = llm.invoke(context)
    return {
        "results": [{"agent": "coder", "summary": response.content[:200]}],
        "messages": [AIMessage(content=f"[Coder] {response.content}", name="coder")],
        "iteration": state["iteration"] + 1,
    }

def review_agent(state: SupervisorState) -> dict:
    """审查 Agent：负责代码审查和质量检查"""
    llm = make_llm(0)
    context = f"原始任务: {state['original_task']}\n"
    if state.get("results"):
        prev = "\n".join(f"[{r['agent']}]: {r['summary']}" for r in state["results"])
        context += f"已有结果:\n{prev}\n"
    context += "请审查以上结果，检查是否有问题，给出改进建议。"

    response = llm.invoke(context)
    return {
        "results": [{"agent": "reviewer", "summary": response.content[:200]}],
        "messages": [AIMessage(content=f"[Reviewer] {response.content}", name="reviewer")],
        "iteration": state["iteration"] + 1,
    }

# === Supervisor 节点 ===

def supervisor_node(state: SupervisorState) -> dict:
    """Supervisor：分析当前状态，决定下一步"""
    llm = make_llm(0)

    # 检查轮次限制
    if state["iteration"] >= 5:
        return {"next": "finish"}

    # 如果没有任何结果，从用户任务开始
    if not state.get("results"):
        # 第一步通常是研究
        response = llm.invoke(
            f"你是任务调度器。根据用户任务决定第一步做什么，只回答一个词:\n"
            f"researcher / coder / reviewer / finish\n"
            f"任务: {state['original_task']}"
        )
    else:
        # 根据已有结果决定下一步
        agents_used = [r["agent"] for r in state["results"]]
        last_agent = agents_used[-1]
        results_summary = "; ".join(r["summary"] for r in state["results"])

        response = llm.invoke(
            f"你是任务调度器。根据当前进度决定下一步，只回答一个词:\n"
            f"researcher / coder / reviewer / finish\n"
            f"原始任务: {state['original_task']}\n"
            f"已执行: {agents_used}\n"
            f"结果摘要: {results_summary}\n"
            f"请决定下一步（如果任务已完成则回答 finish）"
        )

    decision = response.content.strip().lower()
    for option in ["researcher", "coder", "reviewer", "finish"]:
        if option in decision:
            return {"next": option}

    return {"next": "finish"}

# === 汇总节点 ===

def finish_node(state: SupervisorState) -> dict:
    """汇总所有 Agent 的结果"""
    llm = make_llm(0.3)
    results_text = "\n\n".join(
        f"[{r['agent']}]: {r['summary']}" for r in state["results"]
    )
    response = llm.invoke(
        f"请汇总以下各 Agent 的结果，给出最终回答:\n"
        f"原始任务: {state['original_task']}\n"
        f"各 Agent 结果:\n{results_text}"
    )
    return {"final_output": response.content}

# === 路由函数 ===

def route_supervisor(state: SupervisorState) -> str:
    nxt = state.get("next", "finish")
    if nxt == "researcher":
        return "researcher"
    elif nxt == "coder":
        return "coder"
    elif nxt == "reviewer":
        return "reviewer"
    return "finish"

# === 构建图 ===

builder = StateGraph(SupervisorState)

builder.add_node("supervisor", supervisor_node)
builder.add_node("researcher", research_agent)
builder.add_node("coder", coding_agent)
builder.add_node("reviewer", review_agent)
builder.add_node("finish", finish_node)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", route_supervisor, {
    "researcher": "researcher",
    "coder": "coder",
    "reviewer": "reviewer",
    "finish": "finish",
})
# Agent 执行后回到 Supervisor
builder.add_edge("researcher", "supervisor")
builder.add_edge("coder", "supervisor")
builder.add_edge("reviewer", "supervisor")
builder.add_edge("finish", END)

supervisor_graph = builder.compile()

# === 测试 ===

result = supervisor_graph.invoke({
    "messages": [HumanMessage(content="写一个 Python 函数计算斐波那契数列，并确保代码质量")],
    "original_task": "写一个 Python 函数计算斐波那契数列，并确保代码质量",
    "next": "",
    "results": [],
    "iteration": 0,
    "final_output": "",
})

print("=== Supervisor 执行结果 ===")
print(f"轮次: {result['iteration']}")
print(f"参与 Agent: {[r['agent'] for r in result['results']]}")
print(f"\n最终输出:\n{result['final_output'][:200]}...")

# 流式查看执行流程
print("\n=== 流式执行 ===")
for event in supervisor_graph.stream({
    "messages": [HumanMessage(content="分析 Python 和 JavaScript 的优缺点")],
    "original_task": "分析 Python 和 JavaScript 的优缺点",
    "next": "", "results": [], "iteration": 0, "final_output": "",
}):
    for node, output in event.items():
        nxt = output.get("next", "")
        it = output.get("iteration", "")
        print(f"  [{node}] next={nxt} iter={it}")
```

### Day 2 小结

```
Day 2 核心概念：
┌─────────────────────────────────────────────────┐
│  Supervisor 模式完整实现                          │
│                                                   │
│  核心流程：                                        │
│  Supervisor → Agent → Supervisor → Agent → ...   │
│           → finish → END                          │
│                                                   │
│  Supervisor 的职责：                               │
│  1. 分析当前进度（已执行哪些 Agent）                │
│  2. 决定下一步（路由到哪个 Agent 或 finish）       │
│  3. 防止死循环（iteration 限制）                   │
│                                                   │
│  State 设计：                                      │
│  - results: 记录每个 Agent 的输出                  │
│  - iteration: 轮次计数                             │
│  - next: 路由决策                                  │
│  - final_output: 汇总结果                          │
│                                                   │
│  finish 节点：                                     │
│  汇总所有 Agent 的结果，生成最终回答               │
└─────────────────────────────────────────────────┘
```

### Day 2 练习

1. 给 Supervisor 添加一个 `tester` Agent——在 coder 写完代码后，tester 负责生成测试用例
2. 修改 Supervisor 的 prompt，让它考虑"执行顺序"——例如总是 researcher → coder → reviewer → finish
3. 添加一个"质量门控"——reviewer 如果发现问题，Supervisor 应该让 coder 重新修改

<details>
<summary>参考答案</summary>

```python
"""Day 2 练习答案：Tester Agent + 执行顺序 + 质量门控"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    original_task: str
    next: str
    results: Annotated[list[dict], add]
    iteration: int
    needs_fix: bool       # reviewer 是否要求修改
    final_output: str

def supervisor(state: State) -> dict:
    if state["iteration"] >= 6:
        return {"next": "finish"}

    llm = make_llm(0)
    agents_used = [r["agent"] for r in state.get("results", [])]

    # 练习 2：固定执行顺序
    # researcher → coder → tester → reviewer → (fix?) → finish
    if not agents_used:
        return {"next": "researcher"}
    if agents_used == ["researcher"]:
        return {"next": "coder"}
    if agents_used == ["researcher", "coder"]:
        return {"next": "tester"}  # 练习 1：tester
    if "tester" in agents_used and "reviewer" not in agents_used:
        return {"next": "reviewer"}

    # 练习 3：质量门控
    if state.get("needs_fix"):
        return {"next": "coder"}

    return {"next": "finish"}

def researcher(state: State) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"研究以下任务的技术背景: {state['original_task']}")
    return {"results": [{"agent": "researcher", "summary": resp.content[:200]}],
            "messages": [AIMessage(content=resp.content, name="researcher")],
            "iteration": state["iteration"] + 1}

def coder(state: State) -> dict:
    llm = make_llm(0.2)
    context = f"任务: {state['original_task']}"
    if state.get("results"):
        prev = "; ".join(r["summary"] for r in state["results"])
        context += f"\n已有结果: {prev}"
    if state.get("needs_fix"):
        context += "\n请根据 reviewer 的反馈修改代码。"
    resp = llm.invoke(f"编写代码: {context}")
    return {"results": [{"agent": "coder", "summary": resp.content[:200]}],
            "messages": [AIMessage(content=resp.content, name="coder")],
            "iteration": state["iteration"] + 1, "needs_fix": False}

def tester(state: State) -> dict:
    """练习 1：测试 Agent"""
    llm = make_llm(0)
    code = ""
    for r in state.get("results", []):
        if r["agent"] == "coder":
            code = r["summary"]
    resp = llm.invoke(f"为以下代码生成3个测试用例:\n{code}")
    return {"results": [{"agent": "tester", "summary": resp.content[:200]}],
            "messages": [AIMessage(content=resp.content, name="tester")],
            "iteration": state["iteration"] + 1}

def reviewer(state: State) -> dict:
    """练习 3：质量门控"""
    llm = make_llm(0)
    results = "; ".join(r["summary"] for r in state.get("results", []))
    resp = llm.invoke(
        f"审查以下结果是否有问题（回答'通过'或'需要修改'）:\n{results}"
    )
    needs_fix = "修改" in resp.content
    return {"results": [{"agent": "reviewer", "summary": resp.content[:200]}],
            "messages": [AIMessage(content=resp.content, name="reviewer")],
            "iteration": state["iteration"] + 1, "needs_fix": needs_fix}

def finish(state: State) -> dict:
    llm = make_llm(0.3)
    results = "\n".join(f"[{r['agent']}]: {r['summary']}" for r in state["results"])
    resp = llm.invoke(f"汇总结果:\n{results}")
    return {"final_output": resp.content}

def router(state: State) -> str:
    nxt = state.get("next", "finish")
    if nxt in ["researcher", "coder", "tester", "reviewer"]:
        return nxt
    return "finish"

builder = StateGraph(State)
for name, func in [("supervisor", supervisor), ("researcher", researcher),
                    ("coder", coder), ("tester", tester),
                    ("reviewer", reviewer), ("finish", finish)]:
    builder.add_node(name, func)

builder.add_edge(START, "supervisor")
builder.add_conditional_edges("supervisor", router, {
    "researcher": "researcher", "coder": "coder",
    "tester": "tester", "reviewer": "reviewer", "finish": "finish"})
for agent in ["researcher", "coder", "tester", "reviewer"]:
    builder.add_edge(agent, "supervisor")
builder.add_edge("finish", END)

graph = builder.compile()

result = graph.invoke({
    "messages": [HumanMessage(content="实现一个字符串反转函数")],
    "original_task": "实现一个字符串反转函数",
    "next": "", "results": [], "iteration": 0,
    "needs_fix": False, "final_output": "",
})
print(f"路径: {[r['agent'] for r in result['results']]}")
print(f"输出: {result['final_output'][:100]}...")
```

</details>

---

## Day 3：Swarm 群智模式

> Swarm 模式中，Agent 之间直接传递控制权，没有中心化的 Supervisor。

### 3.1 Swarm 架构

```
┌────────────── Swarm 模式执行流程 ──────────────┐
│                                                 │
│  START → Agent A                                │
│            │                                    │
│            ├─ handoff to B ──→ Agent B          │
│            │                     │              │
│            │                     ├─ handoff to C│
│            │                     │              │
│            │                     └─ handoff to END
│            │                                    │
│  关键概念：handoff（交接）                      │
│  Agent 完成自己的部分后，决定把控制权交给谁     │
│  每个 Agent 自己判断"下一步给谁"                │
│                                                 │
│  vs Supervisor：                                │
│  Supervisor: Agent → Supervisor → Agent        │
│  Swarm: Agent → Agent → Agent（直接传递）       │
│                                                 │
└─────────────────────────────────────────────────┘
```

创建文件 `day3_swarm.py`：

```python
"""
Day 3: Swarm 群智模式
- Agent 之间直接 handoff
- 每个 Agent 自主决定下一步
"""

import os
from typing import TypedDict, Annotated, Literal
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === State 定义 ===

class SwarmState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    current_agent: str        # 当前持有控制权的 Agent
    task: str
    research_result: str
    code_result: str
    test_result: str
    final_output: str
    handoff_to: str           # 下一个 Agent

# === 工具：Agent 自主决策 handoff ===

def decide_handoff(current_agent: str, task: str, state: SwarmState) -> str:
    """让 LLM 决定 handoff 目标"""
    llm = make_llm(0)
    # 检查哪些步骤已完成
    done = []
    if state.get("research_result"):
        done.append("research")
    if state.get("code_result"):
        done.append("code")
    if state.get("test_result"):
        done.append("test")

    response = llm.invoke(
        f"你是 {current_agent}。你已完成你的部分。\n"
        f"任务: {task}\n已完成: {done}\n"
        f"决定下一步交给谁，只回答一个词:\n"
        f"researcher / coder / tester / finish\n"
    )
    decision = response.content.strip().lower()
    for opt in ["researcher", "coder", "tester", "finish"]:
        if opt in decision:
            return opt
    return "finish"

# === Agent 定义 ===

def researcher_agent(state: SwarmState) -> dict:
    """研究 Agent"""
    llm = make_llm(0)
    response = llm.invoke(f"作为研究员工，分析任务: {state['task']}")

    # 自主决定 handoff
    next_agent = decide_handoff("researcher", state["task"], state)

    return {
        "research_result": response.content,
        "current_agent": "researcher",
        "handoff_to": next_agent,
        "messages": [AIMessage(content=f"[Researcher] {response.content}", name="researcher")],
    }

def coder_agent(state: SwarmState) -> dict:
    """编码 Agent"""
    llm = make_llm(0.2)
    context = f"任务: {state['task']}"
    if state.get("research_result"):
        context += f"\n研究结果: {state['research_result'][:300]}"
    response = llm.invoke(f"作为程序员，完成编码任务:\n{context}")

    next_agent = decide_handoff("coder", state["task"], state)

    return {
        "code_result": response.content,
        "current_agent": "coder",
        "handoff_to": next_agent,
        "messages": [AIMessage(content=f"[Coder] {response.content}", name="coder")],
    }

def tester_agent(state: SwarmState) -> dict:
    """测试 Agent"""
    llm = make_llm(0)
    code = state.get("code_result", "无代码")
    response = llm.invoke(f"作为测试工程师，为以下代码生成测试:\n{code}")

    # 测试完成后通常就结束了
    next_agent = "finish"

    return {
        "test_result": response.content,
        "current_agent": "tester",
        "handoff_to": next_agent,
        "messages": [AIMessage(content=f"[Tester] {response.content}", name="tester")],
    }

def finish_node(state: SwarmState) -> dict:
    """汇总"""
    llm = make_llm(0.3)
    summary = (
        f"研究: {state.get('research_result', '无')[:100]}\n"
        f"代码: {state.get('code_result', '无')[:100]}\n"
        f"测试: {state.get('test_result', '无')[:100]}"
    )
    response = llm.invoke(f"汇总以下结果:\n{summary}")
    return {"final_output": response.content}

# === 路由：根据 handoff_to 决定 ===

def route_from_agent(state: SwarmState) -> str:
    handoff = state.get("handoff_to", "finish")
    if handoff == "researcher":
        return "researcher"
    elif handoff == "coder":
        return "coder"
    elif handoff == "tester":
        return "tester"
    return "finish"

def initial_route(state: SwarmState) -> str:
    """初始路由：从 researcher 开始"""
    return "researcher"

# === 构建图 ===

builder = StateGraph(SwarmState)

builder.add_node("researcher", researcher_agent)
builder.add_node("coder", coder_agent)
builder.add_node("tester", tester_agent)
builder.add_node("finish", finish_node)

# 初始路由到 researcher
builder.add_conditional_edges(START, initial_route, {"researcher": "researcher"})

# 每个 Agent 执行后根据 handoff_to 路由
builder.add_conditional_edges("researcher", route_from_agent, {
    "researcher": "researcher",
    "coder": "coder",
    "tester": "tester",
    "finish": "finish",
})
builder.add_conditional_edges("coder", route_from_agent, {
    "researcher": "researcher",
    "coder": "coder",
    "tester": "tester",
    "finish": "finish",
})
builder.add_conditional_edges("tester", route_from_agent, {
    "researcher": "researcher",
    "coder": "coder",
    "tester": "tester",
    "finish": "finish",
})
builder.add_edge("finish", END)

swarm_graph = builder.compile()

# === 测试 ===

result = swarm_graph.invoke({
    "messages": [HumanMessage(content="实现一个二分查找函数")],
    "current_agent": "",
    "task": "实现一个二分查找函数",
    "research_result": "",
    "code_result": "",
    "test_result": "",
    "final_output": "",
    "handoff_to": "",
})

print("=== Swarm 执行结果 ===")
print(f"研究: {result.get('research_result', '')[:80]}...")
print(f"代码: {result.get('code_result', '')[:80]}...")
print(f"测试: {result.get('test_result', '')[:80]}...")
print(f"\n最终:\n{result['final_output'][:200]}...")

# 流式查看 handoff 过程
print("\n=== 流式（handoff 过程）===")
for event in swarm_graph.stream({
    "messages": [HumanMessage(content="写一个计算器类")],
    "current_agent": "", "task": "写一个计算器类",
    "research_result": "", "code_result": "", "test_result": "",
    "final_output": "", "handoff_to": "",
}):
    for node, output in event.items():
        handoff = output.get("handoff_to", "")
        print(f"  [{node}] handoff→{handoff}")
```

### 3.2 Swarm vs Supervisor 对比

```python
"""Swarm vs Supervisor 对比演示"""

comparison = """
┌──────────────────────────────────────────────────────────┐
│  对比维度        │  Supervisor           │  Swarm          │
│─────────────────┼───────────────────────┼────────────────│
│  控制方式        │  中心化               │  去中心化       │
│  决策者          │  Supervisor 统一决策  │  每个 Agent 自主│
│  通信路径        │  Agent→Supervisor→Agent│ Agent→Agent    │
│  全局视野        │  Supervisor 有        │  每个 Agent 有限│
│  循环控制        │  Supervisor 管理轮次  │  Agent 自主终止  │
│  灵活性          │  ★★★★               │  ★★★★★        │
│  可预测性        │  ★★★★★              │  ★★★           │
│  适合场景        │  需要统一决策         │  流水线式任务    │
│  实现复杂度      │  中                   │  中高           │
└──────────────────────────────────────────────────────────┘

选择建议：
- 任务有明确的分工和顺序 → Supervisor
- 任务是流水线式（A→B→C）→ Swarm
- 需要全局优化 → Supervisor
- 每个 Agent 独立性强 → Swarm
- 生产环境推荐 → Supervisor（更可控）
"""

print(comparison)
```

### Day 3 小结

```
Day 3 核心概念：
┌─────────────────────────────────────────────────┐
│  Swarm 群智模式                                   │
│                                                   │
│  核心机制：handoff（交接）                        │
│  Agent 完成自己的部分后，自主决定交给谁            │
│  不需要中心化的 Supervisor                        │
│                                                   │
│  实现方式：                                       │
│  1. 每个 Agent 节点执行后设置 handoff_to          │
│  2. 条件边根据 handoff_to 路由到下一个 Agent      │
│  3. Agent 之间通过共享 State 传递结果             │
│                                                   │
│  与 Supervisor 的区别：                           │
│  Supervisor: Agent → Sup → Agent（多一跳）       │
│  Swarm: Agent → Agent（直接传递）                 │
│                                                   │
│  风险：                                           │
│  Agent 可能做出不好的 handoff 决策                │
│  需要设置最大 handoff 次数防止死循环              │
└─────────────────────────────────────────────────┘
```

### Day 3 练习

1. 给 Swarm 添加一个 `reviewer` Agent——在 tester 之后执行，reviewer 决定是否需要回到 coder
2. 添加 handoff 次数限制——超过 5 次强制结束
3. 实现 Swarm 的"动态加入"——Agent 可以 handoff 给一个尚未执行的 Agent

<details>
<summary>参考答案</summary>

```python
"""Day 3 练习答案：Reviewer + 限制 + 动态加入"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

class SwarmState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str
    research_result: str
    code_result: str
    test_result: str
    review_result: str
    handoff_to: str
    handoff_count: int    # 练习 2：handoff 次数
    final_output: str

def researcher(state: SwarmState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"分析任务: {state['task']}")
    # 练习 3：动态决定 handoff
    next_a = "coder"  # 研究后总是交给 coder
    return {"research_result": resp.content, "handoff_to": next_a,
            "handoff_count": state.get("handoff_count", 0) + 1,
            "messages": [AIMessage(content=resp.content[:100], name="researcher")]}

def coder(state: SwarmState) -> dict:
    llm = make_llm(0.2)
    ctx = f"任务: {state['task']}"
    if state.get("research_result"):
        ctx += f"\n研究: {state['research_result'][:200]}"
    if state.get("review_result"):  # reviewer 要求修改
        ctx += f"\n审查反馈: {state['review_result'][:200]}\n请修改代码。"
    resp = llm.invoke(f"编写代码: {ctx}")
    return {"code_result": resp.content, "handoff_to": "tester",
            "handoff_count": state["handoff_count"] + 1, "review_result": "",
            "messages": [AIMessage(content=resp.content[:100], name="coder")]}

def tester(state: SwarmState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"测试代码: {state.get('code_result', '')[:300]}")
    return {"test_result": resp.content, "handoff_to": "reviewer",
            "handoff_count": state["handoff_count"] + 1,
            "messages": [AIMessage(content=resp.content[:100], name="tester")]}

def reviewer(state: SwarmState) -> dict:
    """练习 1：Reviewer Agent"""
    llm = make_llm(0)
    code = state.get("code_result", "")
    tests = state.get("test_result", "")
    resp = llm.invoke(
        f"审查代码和测试（回答'通过'或'需要修改'）:\n代码: {code[:200]}\n测试: {tests[:200]}"
    )
    if "修改" in resp.content:
        # 需要修改，handoff 回 coder
        return {"review_result": resp.content, "handoff_to": "coder",
                "handoff_count": state["handoff_count"] + 1,
                "messages": [AIMessage(content=resp.content[:100], name="reviewer")]}
    return {"review_result": resp.content, "handoff_to": "finish",
            "handoff_count": state["handoff_count"] + 1,
            "messages": [AIMessage(content=resp.content[:100], name="reviewer")]}

def finish(state: SwarmState) -> dict:
    llm = make_llm(0.3)
    resp = llm.invoke(f"汇总: 研究={state.get('research_result','')[:100]}, "
                       f"代码={state.get('code_result','')[:100]}, "
                       f"测试={state.get('test_result','')[:100]}")
    return {"final_output": resp.content}

def route(state: SwarmState) -> str:
    # 练习 2：handoff 次数限制
    if state.get("handoff_count", 0) >= 6:
        return "finish"
    nxt = state.get("handoff_to", "finish")
    if nxt in ["researcher", "coder", "tester", "reviewer"]:
        return nxt
    return "finish"

builder = StateGraph(SwarmState)
for name, func in [("researcher", researcher), ("coder", coder),
                    ("tester", tester), ("reviewer", reviewer), ("finish", finish)]:
    builder.add_node(name, func)

builder.add_edge(START, "researcher")
for agent in ["researcher", "coder", "tester", "reviewer"]:
    builder.add_conditional_edges(agent, route, {
        "researcher": "researcher", "coder": "coder",
        "tester": "tester", "reviewer": "reviewer", "finish": "finish"})
builder.add_edge("finish", END)

graph = builder.compile()

result = graph.invoke({
    "messages": [HumanMessage(content="实现栈数据结构")],
    "task": "实现栈数据结构", "research_result": "", "code_result": "",
    "test_result": "", "review_result": "", "handoff_to": "",
    "handoff_count": 0, "final_output": "",
})
print(f"handoff 次数: {result['handoff_count']}")
print(f"最终: {result['final_output'][:100]}...")
```

</details>

---

## Day 4：Hierarchical 层级模式

> 当任务非常复杂时，单一层级的 Supervisor 不够用——需要多层管理，把大任务逐级拆解。

### 4.1 Hierarchical 架构

```
┌────────── Hierarchical 层级模式 ──────────┐
│                                             │
│        ┌──────────────┐                    │
│        │  Top Boss    │  顶层主管           │
│        │  (拆任务)    │                    │
│        └──────┬───────┘                    │
│          ┌────┴────┐                       │
│          ↓         ↓                       │
│    ┌─────────┐ ┌──────────┐               │
│    │ Team A  │ │ Team B   │  子团队主管    │
│    │ Sub-Boss│ │ Sub-Boss │               │
│    └────┬────┘ └────┬─────┘               │
│      ┌──┴──┐     ┌─┴─┐                    │
│      ↓     ↓     ↓   ↓                    │
│    [A1]  [A2]  [B1] [B2]  执行 Agent      │
│                                             │
│  Top Boss: 拆分大任务为子任务               │
│  Sub-Boss: 管理子任务执行                   │
│  Agent: 执行具体工作                        │
│                                             │
└─────────────────────────────────────────────┘
```

创建文件 `day4_hierarchical.py`：

```python
"""
Day 4: Hierarchical 层级模式
- 顶层 Supervisor 拆分任务
- 子团队 Supervisor 管理执行
- 用子图实现子团队
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 顶层 State ===

class TopState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str
    subtask_a: str          # 拆分给团队 A 的子任务
    subtask_b: str          # 拆分给团队 B 的子任务
    result_a: str           # 团队 A 的结果
    result_b: str           # 团队 B 的结果
    final_output: str

# === 顶层 Supervisor ===

def top_boss(state: TopState) -> dict:
    """顶层 Boss：拆分任务"""
    llm = make_llm(0)
    response = llm.invoke(
        f"你是项目总监。将以下任务拆分为两个子任务，用 JSON 格式输出:\n"
        f'格式: {{"subtask_a": "...", "subtask_b": "..."}}\n'
        f"任务: {state['task']}"
    )
    import json
    try:
        # 尝试解析 JSON
        content = response.content
        # 简单提取 JSON
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            tasks = json.loads(content[start:end])
            return {
                "subtask_a": tasks.get("subtask_a", state["task"]),
                "subtask_b": tasks.get("subtask_b", state["task"]),
            }
    except (json.JSONDecodeError, ValueError):
        pass
    # fallback：简单拆分
    return {
        "subtask_a": f"研究部分: {state['task']}",
        "subtask_b": f"实现部分: {state['task']}",
    }

# === 子团队 State（团队 A：研究团队） ===

class TeamAState(TypedDict):
    subtask: str
    research_result: str
    analysis_result: str
    team_output: str

def team_a_researcher(state: TeamAState) -> dict:
    """团队 A 的研究员"""
    llm = make_llm(0)
    resp = llm.invoke(f"研究: {state['subtask']}")
    return {"research_result": resp.content}

def team_a_analyst(state: TeamAState) -> dict:
    """团队 A 的分析师"""
    llm = make_llm(0)
    resp = llm.invoke(f"分析: {state['research_result']}")
    return {"analysis_result": resp.content}

def team_a_summarizer(state: TeamAState) -> dict:
    """团队 A 的汇总"""
    llm = make_llm(0.3)
    resp = llm.invoke(f"汇总研究和分析:\n研究: {state['research_result'][:200]}\n分析: {state['analysis_result'][:200]}")
    return {"team_output": resp.content}

# 构建团队 A 子图
team_a_builder = StateGraph(TeamAState)
team_a_builder.add_node("researcher", team_a_researcher)
team_a_builder.add_node("analyst", team_a_analyst)
team_a_builder.add_node("summarizer", team_a_summarizer)
team_a_builder.add_edge(START, "researcher")
team_a_builder.add_edge("researcher", "analyst")
team_a_builder.add_edge("analyst", "summarizer")
team_a_builder.add_edge("summarizer", END)
team_a_graph = team_a_builder.compile()

# === 子团队 State（团队 B：开发团队） ===

class TeamBState(TypedDict):
    subtask: str
    code_result: str
    test_result: str
    team_output: str

def team_b_coder(state: TeamBState) -> dict:
    """团队 B 的编码者"""
    llm = make_llm(0.2)
    resp = llm.invoke(f"编写代码: {state['subtask']}")
    return {"code_result": resp.content}

def team_b_tester(state: TeamBState) -> dict:
    """团队 B 的测试者"""
    llm = make_llm(0)
    resp = llm.invoke(f"测试代码: {state['code_result'][:300]}")
    return {"test_result": resp.content}

def team_b_summarizer(state: TeamBState) -> dict:
    """团队 B 的汇总"""
    llm = make_llm(0.3)
    resp = llm.invoke(f"汇总代码和测试:\n代码: {state['code_result'][:200]}\n测试: {state['test_result'][:200]}")
    return {"team_output": resp.content}

# 构建团队 B 子图
team_b_builder = StateGraph(TeamBState)
team_b_builder.add_node("coder", team_b_coder)
team_b_builder.add_node("tester", team_b_tester)
team_b_builder.add_node("summarizer", team_b_summarizer)
team_b_builder.add_edge(START, "coder")
team_b_builder.add_edge("coder", "tester")
team_b_builder.add_edge("tester", "summarizer")
team_b_builder.add_edge("summarizer", END)
team_b_graph = team_b_builder.compile()

# === 顶层节点：调用子团队 ===

def team_a_node(state: TopState) -> dict:
    """执行团队 A 子图"""
    result = team_a_graph.invoke({"subtask": state["subtask_a"], "research_result": "", "analysis_result": "", "team_output": ""})
    return {"result_a": result["team_output"]}

def team_b_node(state: TopState) -> dict:
    """执行团队 B 子图"""
    result = team_b_graph.invoke({"subtask": state["subtask_b"], "code_result": "", "test_result": "", "team_output": ""})
    return {"result_b": result["team_output"]}

def merge_node(state: TopState) -> dict:
    """合并两个团队的结果"""
    llm = make_llm(0.3)
    resp = llm.invoke(
        f"你是项目总监。合并两个团队的结果:\n"
        f"研究团队: {state['result_a'][:300]}\n\n"
        f"开发团队: {state['result_b'][:300]}\n\n"
        f"给出最终项目总结。"
    )
    return {"final_output": resp.content}

# === 构建顶层图 ===

top_builder = StateGraph(TopState)
top_builder.add_node("top_boss", top_boss)
top_builder.add_node("team_a", team_a_node)
top_builder.add_node("team_b", team_b_node)
top_builder.add_node("merge", merge_node)

# Top Boss 拆分任务后，两个团队并行执行
top_builder.add_edge(START, "top_boss")
top_builder.add_edge("top_boss", "team_a")
top_builder.add_edge("top_boss", "team_b")
top_builder.add_edge("team_a", "merge")
top_builder.add_edge("team_b", "merge")
top_builder.add_edge("merge", END)

hierarchical_graph = top_builder.compile()

# === 测试 ===

result = hierarchical_graph.invoke({
    "messages": [HumanMessage(content="构建一个 Web 爬虫系统")],
    "task": "构建一个 Web 爬虫系统",
    "subtask_a": "", "subtask_b": "",
    "result_a": "", "result_b": "",
    "final_output": "",
})

print("=== Hierarchical 执行结果 ===")
print(f"原始任务: {result['task']}")
print(f"\n子任务 A: {result['subtask_a'][:80]}...")
print(f"子任务 B: {result['subtask_b'][:80]}...")
print(f"\n团队 A 结果: {result['result_a'][:100]}...")
print(f"团队 B 结果: {result['result_b'][:100]}...")
print(f"\n最终输出:\n{result['final_output'][:200]}...")

# 流式查看
print("\n=== 流式执行 ===")
for event in hierarchical_graph.stream({
    "messages": [HumanMessage(content="开发一个聊天机器人")],
    "task": "开发一个聊天机器人",
    "subtask_a": "", "subtask_b": "", "result_a": "", "result_b": "", "final_output": "",
}):
    for node, output in event.items():
        print(f"  [{node}] keys={list(output.keys())}")
```

### Day 4 小结

```
Day 4 核心概念：
┌─────────────────────────────────────────────────┐
│  Hierarchical 层级模式                            │
│                                                   │
│  核心思想：                                       │
│  顶层 Supervisor 拆分任务                          │
│  子团队 Supervisor 管理执行                       │
│  用子图实现子团队                                 │
│                                                   │
│  实现方式：                                       │
│  1. 顶层图：top_boss → team_a, team_b → merge   │
│  2. 子团队是独立的子图（StateGraph）              │
│  3. 顶层节点调用子图: subgraph.invoke()           │
│  4. 子团队内部有自己的流程                        │
│                                                   │
│  关键点：                                         │
│  - 顶层和子团队的 State 是独立的                  │
│  - 顶层节点负责 State 转换（顶层→子团队→顶层）    │
│  - 并行执行：top_boss 后 team_a 和 team_b 并行   │
│                                                   │
│  适用场景：                                       │
│  大型项目、多阶段任务、需要分工协作               │
└─────────────────────────────────────────────────┘
```

### Day 4 练习

1. 添加第三个团队（团队 C：文档团队），在 A 和 B 完成后编写项目文档
2. 让团队 A 内部也用 Supervisor 模式——子团队内部有一个 Sub-Boss 管理研究员和分析师
3. 给顶层 Boss 添加"任务复杂度评估"——简单任务不拆分，直接执行；复杂任务才拆分给子团队

<details>
<summary>参考答案</summary>

```python
"""Day 4 练习答案：三团队 + 子团队 Supervisor + 复杂度评估"""

import os
import json
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 练习 3：复杂度评估 ===
class TopState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str
    complexity: str         # simple / complex
    subtask_a: str
    subtask_b: str
    subtask_c: str
    result_a: str
    result_b: str
    result_c: str
    final_output: str

def top_boss(state: TopState) -> dict:
    llm = make_llm(0)
    # 练习 3：评估复杂度
    resp = llm.invoke(
        f"评估任务复杂度，只回答 simple 或 complex:\n任务: {state['task']}"
    )
    complexity = "complex" if "complex" in resp.content.lower() else "simple"

    if complexity == "simple":
        # 简单任务不拆分
        return {"complexity": "simple", "subtask_a": state["task"],
                "subtask_b": "无需执行", "subtask_c": "无需执行"}

    # 复杂任务拆分为三个子任务
    resp = llm.invoke(
        f"将任务拆分为三个子任务（研究/开发/文档），JSON格式:\n"
        f'{{"a": "...", "b": "...", "c": "..."}}\n任务: {state["task"]}'
    )
    try:
        content = resp.content
        s, e = content.find("{"), content.rfind("}") + 1
        tasks = json.loads(content[s:e]) if s >= 0 and e > s else {}
        return {"complexity": "complex",
                "subtask_a": tasks.get("a", state["task"]),
                "subtask_b": tasks.get("b", state["task"]),
                "subtask_c": tasks.get("c", state["task"])}
    except (json.JSONDecodeError, ValueError):
        return {"complexity": "complex",
                "subtask_a": f"研究: {state['task']}",
                "subtask_b": f"开发: {state['task']}",
                "subtask_c": f"文档: {state['task']}"}

# 团队 A（练习 2：内部 Supervisor）
class TeamAState(TypedDict):
    subtask: str
    next: str
    research_result: str
    analysis_result: str
    team_output: str

def team_a_boss(state: TeamAState) -> dict:
    """团队 A 的 Sub-Boss"""
    if not state.get("research_result"):
        return {"next": "researcher"}
    if not state.get("analysis_result"):
        return {"next": "analyst"}
    return {"next": "done"}

def team_a_researcher(state: TeamAState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"研究: {state['subtask']}")
    return {"research_result": resp.content}

def team_a_analyst(state: TeamAState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"分析: {state['research_result'][:300]}")
    return {"analysis_result": resp.content}

def team_a_route(state: TeamAState) -> str:
    nxt = state.get("next", "done")
    if nxt == "researcher": return "researcher"
    if nxt == "analyst": return "analyst"
    return END

# 团队 A 子图（带内部 Supervisor）
a_builder = StateGraph(TeamAState)
a_builder.add_node("boss", team_a_boss)
a_builder.add_node("researcher", team_a_researcher)
a_builder.add_node("analyst", team_a_analyst)
a_builder.add_edge(START, "boss")
a_builder.add_conditional_edges("boss", team_a_route, {
    "researcher": "researcher", "analyst": "analyst", END: END})
a_builder.add_edge("researcher", "boss")
a_builder.add_edge("analyst", "boss")
team_a_graph = a_builder.compile()

# 团队 B
class TeamBState(TypedDict):
    subtask: str
    code_result: str
    test_result: str
    team_output: str

def team_b_coder(state: TeamBState) -> dict:
    llm = make_llm(0.2)
    resp = llm.invoke(f"编码: {state['subtask']}")
    return {"code_result": resp.content}

def team_b_tester(state: TeamBState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke(f"测试: {state['code_result'][:300]}")
    return {"test_result": resp.content}

def team_b_summarizer(state: TeamBState) -> dict:
    llm = make_llm(0.3)
    resp = llm.invoke(f"汇总: 代码={state['code_result'][:150]}, 测试={state['test_result'][:150]}")
    return {"team_output": resp.content}

b_builder = StateGraph(TeamBState)
b_builder.add_node("coder", team_b_coder)
b_builder.add_node("tester", team_b_tester)
b_builder.add_node("summarizer", team_b_summarizer)
b_builder.add_edge(START, "coder")
b_builder.add_edge("coder", "tester")
b_builder.add_edge("tester", "summarizer")
b_builder.add_edge("summarizer", END)
team_b_graph = b_builder.compile()

# 练习 1：团队 C（文档团队）
class TeamCState(TypedDict):
    subtask: str
    doc_result: str
    team_output: str

def team_c_writer(state: TeamCState) -> dict:
    llm = make_llm(0.5)
    resp = llm.invoke(f"编写项目文档: {state['subtask']}")
    return {"doc_result": resp.content, "team_output": resp.content}

c_builder = StateGraph(TeamCState)
c_builder.add_node("writer", team_c_writer)
c_builder.add_edge(START, "writer")
c_builder.add_edge("writer", END)
team_c_graph = c_builder.compile()

# 顶层节点
def team_a_node(state: TopState) -> dict:
    r = team_a_graph.invoke({"subtask": state["subtask_a"], "next": "",
                             "research_result": "", "analysis_result": "", "team_output": ""})
    output = f"研究: {r.get('research_result','')[:100]}\n分析: {r.get('analysis_result','')[:100]}"
    return {"result_a": output}

def team_b_node(state: TopState) -> dict:
    r = team_b_graph.invoke({"subtask": state["subtask_b"], "code_result": "",
                             "test_result": "", "team_output": ""})
    return {"result_b": r["team_output"]}

def team_c_node(state: TopState) -> dict:
    r = team_c_graph.invoke({"subtask": state["subtask_c"], "doc_result": "", "team_output": ""})
    return {"result_c": r["team_output"]}

def merge_node(state: TopState) -> dict:
    llm = make_llm(0.3)
    parts = []
    if state.get("result_a"): parts.append(f"研究: {state['result_a'][:200]}")
    if state.get("result_b"): parts.append(f"开发: {state['result_b'][:200]}")
    if state.get("result_c"): parts.append(f"文档: {state['result_c'][:200]}")
    resp = llm.invoke(f"汇总结果:\n{chr(10).join(parts)}")
    return {"final_output": resp.content}

def top_route(state: TopState) -> str:
    return "complex" if state.get("complexity") == "complex" else "simple_exec"

def simple_exec(state: TopState) -> dict:
    llm = make_llm(0.3)
    resp = llm.invoke(f"直接完成: {state['task']}")
    return {"final_output": resp.content}

# 构建顶层图
top_builder = StateGraph(TopState)
top_builder.add_node("top_boss", top_boss)
top_builder.add_node("team_a", team_a_node)
top_builder.add_node("team_b", team_b_node)
top_builder.add_node("team_c", team_c_node)
top_builder.add_node("merge", merge_node)
top_builder.add_node("simple_exec", simple_exec)

top_builder.add_edge(START, "top_boss")
top_builder.add_conditional_edges("top_boss", top_route, {
    "complex": "team_a", "simple_exec": "simple_exec"})
# 复杂任务：A 和 B 并行，然后 C（需要 A、B 的结果）
top_builder.add_edge("team_a", "team_c")
top_builder.add_edge("team_b", "team_c")
top_builder.add_edge("team_c", "merge")
top_builder.add_edge("merge", END)
top_builder.add_edge("simple_exec", END)

hierarchical_graph = top_builder.compile()

# 测试
result = hierarchical_graph.invoke({
    "messages": [HumanMessage(content="构建一个分布式 Web 爬虫系统")],
    "task": "构建一个分布式 Web 爬虫系统",
    "complexity": "", "subtask_a": "", "subtask_b": "", "subtask_c": "",
    "result_a": "", "result_b": "", "result_c": "", "final_output": "",
})
print(f"复杂度: {result['complexity']}")
print(f"最终: {result['final_output'][:150]}...")
```

</details>

---

## Day 5：Agent 通信与任务分配

> 今天的重点不是编排模式，而是 Agent 之间的通信细节和任务分配策略。

### 5.1 通信模式对比

```
┌────────── 三种通信模式 ──────────┐
│                                    │
│  1. 共享 State（已学过）           │
│  ┌─────────────────────────┐      │
│  │  State: {a:1, b:2, c:3} │      │
│  │  Agent A → 写 a          │      │
│  │  Agent B → 读 a, 写 b    │      │
│  │  Agent C → 读 a+b, 写 c  │      │
│  └─────────────────────────┘      │
│  简单但耦合                        │
│                                    │
│  2. 消息通道（Channel）            │
│  ┌─────────┐    ┌─────────┐       │
│  │ Agent A  │──→│ Agent B  │       │
│  │ send(msg)│    │ recv()   │       │
│  └─────────┘    └─────────┘       │
│  解耦但复杂                        │
│                                    │
│  3. 共享黑板（Blackboard）         │
│  ┌─────────────────────────┐      │
│  │  Blackboard              │      │
│  │  ┌───┐ ┌───┐ ┌───┐     │      │
│  │  │ A │ │ B │ │ C │     │      │
│  │  └─┬─┘ └─┬─┘ └─┬─┘     │      │
│  │    │     │     │        │      │
│  │  read/write shared      │      │
│  └─────────────────────────┘      │
│  灵活但需管理竞争                  │
│                                    │
└────────────────────────────────────┘
```

创建文件 `day5_communication.py`：

```python
"""
Day 5: Agent 通信与任务分配
- 共享 State 通信（深入）
- 消息传递模式
- 任务分配策略
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 1. 共享 State 通信（深入） ===

class SharedState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str
    # 各 Agent 的输出区域（黑板模式）
    research_data: str       # 研究员写入
    code_solution: str       # 编码员读取 research_data，写入 code_solution
    test_report: str         # 测试员读取 code_solution，写入 test_report
    review_feedback: str     # 审查员读取所有，写入 review_feedback
    final_output: str

def researcher(state: SharedState) -> dict:
    """研究员：读取 task，写入 research_data"""
    llm = make_llm(0)
    resp = llm.invoke(f"研究任务: {state['task']}")
    return {"research_data": resp.content}

def coder(state: SharedState) -> dict:
    """编码员：读取 research_data，写入 code_solution"""
    llm = make_llm(0.2)
    research = state.get("research_data", "")
    resp = llm.invoke(f"根据研究写代码:\n研究: {research[:300]}\n任务: {state['task']}")
    return {"code_solution": resp.content}

def tester(state: SharedState) -> dict:
    """测试员：读取 code_solution，写入 test_report"""
    llm = make_llm(0)
    code = state.get("code_solution", "")
    resp = llm.invoke(f"测试代码:\n{code[:300]}")
    return {"test_report": resp.content}

def reviewer(state: SharedState) -> dict:
    """审查员：读取所有，写入 review_feedback"""
    llm = make_llm(0)
    all_data = (
        f"研究: {state.get('research_data', '')[:100]}\n"
        f"代码: {state.get('code_solution', '')[:100]}\n"
        f"测试: {state.get('test_report', '')[:100]}"
    )
    resp = llm.invoke(f"审查所有结果:\n{all_data}")
    return {"review_feedback": resp.content}

def summarize(state: SharedState) -> dict:
    """汇总"""
    llm = make_llm(0.3)
    all_data = (
        f"研究: {state.get('research_data', '')[:150]}\n"
        f"代码: {state.get('code_solution', '')[:150]}\n"
        f"测试: {state.get('test_report', '')[:150]}\n"
        f"审查: {state.get('review_feedback', '')[:150]}"
    )
    resp = llm.invoke(f"最终汇总:\n{all_data}")
    return {"final_output": resp.content}

# 构建（流水线式）
builder = StateGraph(SharedState)
builder.add_node("researcher", researcher)
builder.add_node("coder", coder)
builder.add_node("tester", tester)
builder.add_node("reviewer", reviewer)
builder.add_node("summarize", summarize)

builder.add_edge(START, "researcher")
builder.add_edge("researcher", "coder")
builder.add_edge("coder", "tester")
builder.add_edge("tester", "reviewer")
builder.add_edge("reviewer", "summarize")
builder.add_edge("summarize", END)

pipeline_graph = builder.compile()

result = pipeline_graph.invoke({
    "messages": [HumanMessage(content="实现一个 LRU 缓存")],
    "task": "实现一个 LRU 缓存",
    "research_data": "", "code_solution": "", "test_report": "",
    "review_feedback": "", "final_output": "",
})
print("=== 共享 State 流水线 ===")
print(f"最终: {result['final_output'][:150]}...")

# === 2. 消息传递模式 ===

class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    task: str
    # 消息队列：每个 Agent 有一个收件箱
    inbox_researcher: Annotated[list[str], add]
    inbox_coder: Annotated[list[str], add]
    inbox_tester: Annotated[list[str], add]
    final_output: str

def dispatcher(state: MessageState) -> dict:
    """分发器：将任务拆解为消息发送给各 Agent"""
    llm = make_llm(0)
    resp = llm.invoke(
        f"将任务拆解为3条指令，分别给研究员、编码员、测试员，"
        f"用 JSON 格式: {{\"researcher\": \"...\", \"coder\": \"...\", \"tester\": \"...\"}}\n"
        f"任务: {state['task']}"
    )
    import json
    try:
        content = resp.content
        s, e = content.find("{"), content.rfind("}") + 1
        instructions = json.loads(content[s:e]) if s >= 0 and e > s else {}
    except (json.JSONDecodeError, ValueError):
        instructions = {}

    return {
        "inbox_researcher": [instructions.get("researcher", f"研究: {state['task']}")],
        "inbox_coder": [instructions.get("coder", f"编码: {state['task']}")],
        "inbox_tester": [instructions.get("tester", f"测试: {state['task']}")],
    }

def msg_researcher(state: MessageState) -> dict:
    """研究员：从收件箱读取任务"""
    llm = make_llm(0)
    task_msg = state.get("inbox_researcher", ["无任务"])[0]
    resp = llm.invoke(f"指令: {task_msg}")
    # 将结果发送给编码员的收件箱
    return {"inbox_coder": [f"研究结果: {resp.content[:200]}"]}

def msg_coder(state: MessageState) -> dict:
    """编码员：从收件箱读取任务和研究结果"""
    llm = make_llm(0.2)
    msgs = state.get("inbox_coder", [])
    context = "\n".join(msgs)
    resp = llm.invoke(f"根据以下信息编码:\n{context}")
    # 将结果发送给测试员
    return {"inbox_tester": [f"代码: {resp.content[:200]}"]}

def msg_tester(state: MessageState) -> dict:
    """测试员：从收件箱读取代码"""
    llm = make_llm(0)
    msgs = state.get("inbox_tester", [])
    context = "\n".join(msgs)
    resp = llm.invoke(f"测试:\n{context}")
    return {"final_output": resp.content}

# 构建消息传递图
msg_builder = StateGraph(MessageState)
msg_builder.add_node("dispatcher", dispatcher)
msg_builder.add_node("researcher", msg_researcher)
msg_builder.add_node("coder", msg_coder)
msg_builder.add_node("tester", msg_tester)

msg_builder.add_edge(START, "dispatcher")
msg_builder.add_edge("dispatcher", "researcher")
msg_builder.add_edge("researcher", "coder")
msg_builder.add_edge("coder", "tester")
msg_builder.add_edge("tester", END)

msg_graph = msg_builder.compile()

result = msg_graph.invoke({
    "messages": [HumanMessage(content="实现栈数据结构")],
    "task": "实现栈数据结构",
    "inbox_researcher": [], "inbox_coder": [], "inbox_tester": [],
    "final_output": "",
})
print("\n=== 消息传递模式 ===")
print(f"最终: {result['final_output'][:150]}...")
```

### 5.2 任务分配策略

```python
"""
任务分配策略对比
"""

STRATEGIES = """
┌────────────── 任务分配策略 ──────────────┐
│                                           │
│  1. LLM 路由（已学过）                    │
│  Supervisor 用 LLM 决定分配给谁           │
│  优点：智能、灵活                         │
│  缺点：慢、有 LLM 调用成本                │
│                                           │
│  2. 规则路由                              │
│  用关键词/正则匹配决定路由                │
│  优点：快、零成本                         │
│  缺点：不智能                             │
│                                           │
│  3. 混合路由                              │
│  先用规则快速匹配，匹配不到再用 LLM       │
│  优点：兼顾速度和智能                     │
│                                           │
│  4. 能力声明                              │
│  每个 Agent 声明自己的能力                │
│  Supervisor 匹配任务需求和 Agent 能力     │
│                                           │
└───────────────────────────────────────────┘
"""

# 混合路由示例
def hybrid_router(task: str, agents: dict) -> str:
    """混合路由：先规则匹配，再 LLM 兜底"""
    # 规则匹配
    rules = {
        "coder": ["代码", "函数", "实现", "编程", "code", "debug", "bug"],
        "writer": ["写", "文档", "文章", "文案", "翻译", "write"],
        "analyst": ["分析", "数据", "统计", "报表", "analyze"],
    }

    task_lower = task.lower()
    for agent_name, keywords in rules.items():
        if any(kw in task_lower for kw in keywords):
            return agent_name

    # LLM 兜底
    llm = make_llm(0)
    agent_list = ", ".join(agents.keys())
    resp = llm.invoke(
        f"选择最合适的 Agent（只回答名字）: {agent_list}\n任务: {task}"
    )
    for name in agents:
        if name in resp.content.lower():
            return name
    return list(agents.keys())[0]  # 默认

# 测试
agents = {"coder": None, "writer": None, "analyst": None}
test_tasks = [
    "用 Python 写一个排序算法",     # 规则→coder
    "写一篇技术博客",              # 规则→writer
    "分析用户增长数据",            # 规则→analyst
    "设计系统架构",                # LLM 兜底
]

print(STRATEGIES)
print("=== 混合路由测试 ===")
for task in test_tasks:
    routed = hybrid_router(task, agents)
    print(f"  '{task}' → {routed}")
```

### Day 5 小结

```
Day 5 核心概念：
┌─────────────────────────────────────────────────┐
│  Agent 通信                                       │
│                                                   │
│  1. 共享 State：最简单，直接读写同一个 State      │
│  2. 消息传递：各 Agent 有收件箱，通过消息通信     │
│  3. 黑板模式：共享区域，Agent 自由读写            │
│                                                   │
│  任务分配策略                                     │
│                                                   │
│  1. LLM 路由：智能但慢                            │
│  2. 规则路由：快但不智能                          │
│  3. 混合路由：先规则后 LLM，兼顾速度和智能        │
│  4. 能力声明：Agent 声明能力，按需匹配            │
│                                                   │
│  生产建议：                                       │
│  - 高频简单任务 → 规则路由                        │
│  - 复杂任务 → LLM 路由                            │
│  - 混合路由是最实用的方案                         │
└─────────────────────────────────────────────────┘
```

### Day 5 练习

1. 实现一个"能力声明"路由——每个 Agent 声明自己的能力标签，Supervisor 根据标签匹配
2. 用消息传递模式实现一个"客服转接"系统——客服 A 无法处理时转给客服 B
3. 实现一个"优先级队列"——多个任务按优先级排序，高优先级先执行

<details>
<summary>参考答案</summary>

```python
"""Day 5 练习答案：能力声明 + 客服转接 + 优先级队列"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 练习 1：能力声明路由 ===

# Agent 能力声明
AGENT_CAPABILITIES = {
    "coder": {"name": "Coder", "skills": ["python", "code", "debug", "算法", "编程"]},
    "writer": {"name": "Writer", "skills": ["写作", "文档", "文案", "翻译", "博客"]},
    "analyst": {"name": "Analyst", "skills": ["数据", "分析", "统计", "报表", "可视化"]},
}

def capability_router(task: str) -> str:
    """根据能力声明匹配 Agent"""
    task_lower = task.lower()
    best_match = None
    best_score = 0

    for agent_id, info in AGENT_CAPABILITIES.items():
        score = sum(1 for skill in info["skills"] if skill in task_lower)
        if score > best_score:
            best_score = score
            best_match = agent_id

    if best_match and best_score > 0:
        return best_match

    # 兜底：LLM
    llm = make_llm(0)
    resp = llm.invoke(f"选择 Agent: {', '.join(AGENT_CAPABILITIES.keys())}\n任务: {task}")
    for aid in AGENT_CAPABILITIES:
        if aid in resp.content.lower():
            return aid
    return "coder"

class CapabilityState(TypedDict):
    task: str
    routed_to: str
    result: str

def router_node(state: CapabilityState) -> dict:
    return {"routed_to": capability_router(state["task"])}

def execute_node(state: CapabilityState) -> dict:
    agent_name = AGENT_CAPABILITIES[state["routed_to"]]["name"]
    llm = make_llm(0.3)
    resp = llm.invoke(f"你是{agent_name}。完成任务: {state['task']}")
    return {"result": resp.content}

builder = StateGraph(CapabilityState)
builder.add_node("router", router_node)
builder.add_node("execute", execute_node)
builder.add_edge(START, "router")
builder.add_edge("router", "execute")
builder.add_edge("execute", END)
cap_graph = builder.compile()

print("=== 练习 1: 能力声明路由 ===")
for task in ["用 Python 写排序算法", "写技术博客", "分析销售数据", "设计架构"]:
    r = cap_graph.invoke({"task": task, "routed_to": "", "result": ""})
    print(f"  '{task}' → {r['routed_to']}")

# === 练习 2：客服转接 ===

class ServiceState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    query: str
    handler: str         # current / escalated
    response: str
    resolved: bool

def first_line_support(state: ServiceState) -> dict:
    """一线客服"""
    llm = make_llm(0.3)
    resp = llm.invoke(
        f"你是客服。尝试回答: {state['query']}\n"
        f"如果无法回答，回复 'ESCALATE'。"
    )
    if "ESCALATE" in resp.content:
        return {"handler": "escalated", "messages": [AIMessage(content="需转接", name="l1")]}
    return {"response": resp.content, "resolved": True,
            "messages": [AIMessage(content=resp.content, name="l1")]}

def second_line_support(state: ServiceState) -> dict:
    """二线客服（专家）"""
    llm = make_llm(0)
    resp = llm.invoke(f"你是技术专家。回答: {state['query']}")
    return {"response": resp.content, "resolved": True,
            "messages": [AIMessage(content=resp.content, name="l2")]}

def route_support(state: ServiceState) -> str:
    if state.get("resolved"):
        return END
    if state.get("handler") == "escalated":
        return "l2"
    return END

s_builder = StateGraph(ServiceState)
s_builder.add_node("l1", first_line_support)
s_builder.add_node("l2", second_line_support)
s_builder.add_edge(START, "l1")
s_builder.add_conditional_edges("l1", route_support, {"l2": "l2", END: END})
s_builder.add_edge("l2", END)
service_graph = s_builder.compile()

print("\n=== 练习 2: 客服转接 ===")
for q in ["你们的地址是什么？", "请解释 Transformer 的自注意力机制"]:
    r = service_graph.invoke({"messages": [HumanMessage(content=q)], "query": q,
                              "handler": "", "response": "", "resolved": False})
    print(f"  Q: {q}")
    print(f"  A: {r['response'][:60]}... (resolved={r['resolved']})")

# === 练习 3：优先级队列 ===

class PriorityState(TypedDict):
    tasks: list[dict]     # [{"task": "...", "priority": 1-5}]
    results: Annotated[list[str], add]
    current_index: int

def sort_by_priority(state: PriorityState) -> dict:
    """按优先级排序"""
    tasks = sorted(state["tasks"], key=lambda t: t.get("priority", 3), reverse=True)
    return {"tasks": tasks, "current_index": 0}

def process_task(state: PriorityState) -> dict:
    """处理当前任务"""
    idx = state["current_index"]
    tasks = state["tasks"]
    if idx >= len(tasks):
        return {"results": ["所有任务完成"]}

    task = tasks[idx]
    llm = make_llm(0.3)
    resp = llm.invoke(f"完成任务: {task['task']}")
    return {
        "results": [f"[P{task.get('priority', 3)}] {task['task']}: {resp.content[:50]}..."],
        "current_index": idx + 1,
    }

def has_more(state: PriorityState) -> str:
    if state["current_index"] < len(state["tasks"]):
        return "process"
    return END

p_builder = StateGraph(PriorityState)
p_builder.add_node("sort", sort_by_priority)
p_builder.add_node("process", process_task)
p_builder.add_edge(START, "sort")
p_builder.add_edge("sort", "process")
p_builder.add_conditional_edges("process", has_more, {"process": "process", END: END})
priority_graph = p_builder.compile()

print("\n=== 练习 3: 优先级队列 ===")
result = priority_graph.invoke({
    "tasks": [
        {"task": "写文档", "priority": 2},
        {"task": "修复紧急bug", "priority": 5},
        {"task": "代码审查", "priority": 3},
    ],
    "results": [], "current_index": 0,
})
for r in result["results"]:
    print(f"  {r}")
```

</details>

---
