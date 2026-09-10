## Day 6：综合实战——Multi-Agent 研发团队

> 用 LangGraph 构建一个模拟软件研发团队的 Multi-Agent 系统，涵盖本周所有知识点。

### 6.1 系统架构

```
┌─────── Multi-Agent 研发团队架构 ───────┐
│                                         │
│  START → Project Manager (Supervisor)   │
│            │                            │
│    ┌───────┼───────┐                   │
│    ↓       ↓       ↓                   │
│  [PM拆分任务为子任务]                   │
│    │       │       │                   │
│    ↓       ↓       ↓                   │
│  研究    开发    文档                   │
│  Agent   Agent   Agent                  │
│    │       │       │                   │
│    └───────┼───────┘                   │
│            ↓                            │
│  QA Agent (测试+审查)                   │
│            │                            │
│            ↓                            │
│  PM 检查质量 → 通过则结束 / 不通过则回开发│
│                                         │
└─────────────────────────────────────────┘
```

创建文件 `day6_dev_team.py`：

```python
"""
Day 6: Multi-Agent 研发团队
- PM + 研究员 + 开发员 + QA + 文档员
- Supervisor 模式 + 质量门控
"""

import os
import sys
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === State ===

class DevTeamState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    project: str               # 项目描述
    subtasks: list[str]        # PM 拆分的子任务
    current_phase: str         # research / dev / qa / docs / done
    research_output: str
    dev_output: str
    qa_output: str
    docs_output: str
    qa_passed: bool
    iteration: int
    final_report: str

# === PM（Supervisor） ===

def pm_node(state: DevTeamState) -> dict:
    """项目经理：拆分任务、决定阶段"""
    llm = make_llm(0)

    # 防死循环：迭代超过 4 次强制进入文档阶段
    if state.get("iteration", 0) >= 4 and state.get("current_phase") not in ("docs", "done"):
        return {"current_phase": "docs"}

    # 第一次调用：拆分任务
    if not state.get("subtasks"):
        resp = llm.invoke(
            f"你是项目经理。将项目拆分为3个子任务（研究/开发/文档），"
            f"用换行分隔，每行一个子任务:\n{state['project']}"
        )
        subtasks = [s.strip() for s in resp.content.strip().split("\n") if s.strip()][:3]
        return {"subtasks": subtasks, "current_phase": "research"}

    # QA 不通过：回到开发
    if state.get("current_phase") == "qa" and not state.get("qa_passed", False):
        return {"current_phase": "dev", "iteration": state["iteration"] + 1}

    # 正常流程
    phase = state.get("current_phase", "research")
    if phase == "research":
        return {"current_phase": "dev"}
    elif phase == "dev":
        return {"current_phase": "qa"}
    elif phase == "qa":
        if state.get("qa_passed"):
            return {"current_phase": "docs"}
        return {"current_phase": "dev", "iteration": state["iteration"] + 1}
    elif phase == "docs":
        return {"current_phase": "done"}

    return {"current_phase": "done"}

# === 研究 Agent ===

def research_agent(state: DevTeamState) -> dict:
    """研究员"""
    llm = make_llm(0)
    task = state["subtasks"][0] if state.get("subtasks") else state["project"]
    resp = llm.invoke(f"你是技术研究员。研究以下内容:\n{task}")
    return {
        "research_output": resp.content,
        "messages": [AIMessage(content=f"[Research] {resp.content[:100]}", name="researcher")],
    }

# === 开发 Agent ===

def dev_agent(state: DevTeamState) -> dict:
    """开发员"""
    llm = make_llm(0.2)
    task = state["subtasks"][1] if len(state.get("subtasks", [])) > 1 else state["project"]
    research = state.get("research_output", "")
    feedback = state.get("qa_output", "") if state.get("iteration", 0) > 0 else ""

    prompt = f"你是开发工程师。任务: {task}\n"
    if research:
        prompt += f"研究参考: {research[:300]}\n"
    if feedback:
        prompt += f"QA反馈（请修改）: {feedback[:200]}\n"
    prompt += "请提供完整代码。"

    resp = llm.invoke(prompt)
    return {
        "dev_output": resp.content,
        "messages": [AIMessage(content=f"[Dev] {resp.content[:100]}", name="developer")],
    }

# === QA Agent ===

def qa_agent(state: DevTeamState) -> dict:
    """QA 工程师：测试 + 审查"""
    llm = make_llm(0)
    code = state.get("dev_output", "")

    resp = llm.invoke(
        f"你是 QA 工程师。审查以下代码:\n{code[:500]}\n\n"
        f"如果有问题，说明需要修改的内容。如果没问题，回复'通过'。"
    )

    passed = "通过" in resp.content
    return {
        "qa_output": resp.content,
        "qa_passed": passed,
        "messages": [AIMessage(content=f"[QA] {resp.content[:100]}", name="qa")],
    }

# === 文档 Agent ===

def docs_agent(state: DevTeamState) -> dict:
    """文档工程师"""
    llm = make_llm(0.5)
    task = state["subtasks"][2] if len(state.get("subtasks", [])) > 2 else "编写项目文档"
    research = state.get("research_output", "")[:200]
    code = state.get("dev_output", "")[:200]

    resp = llm.invoke(
        f"你是文档工程师。任务: {task}\n"
        f"研究: {research}\n代码: {code}\n"
        f"请编写项目文档。"
    )
    return {
        "docs_output": resp.content,
        "messages": [AIMessage(content=f"[Docs] {resp.content[:100]}", name="docs")],
    }

# === 汇总节点 ===

def report_node(state: DevTeamState) -> dict:
    """生成最终报告"""
    llm = make_llm(0.3)
    report = (
        f"项目: {state['project']}\n\n"
        f"研究:\n{state.get('research_output', '无')[:200]}\n\n"
        f"代码:\n{state.get('dev_output', '无')[:200]}\n\n"
        f"QA:\n{state.get('qa_output', '无')[:200]}\n\n"
        f"文档:\n{state.get('docs_output', '无')[:200]}"
    )
    resp = llm.invoke(f"生成项目完成报告:\n{report}")
    return {"final_report": resp.content}

# === 路由 ===

def route_pm(state: DevTeamState) -> str:
    phase = state.get("current_phase", "done")
    if phase == "research": return "researcher"
    if phase == "dev": return "developer"
    if phase == "qa": return "qa"
    if phase == "docs": return "docs"
    return "report"

# === 构建图 ===

builder = StateGraph(DevTeamState)

builder.add_node("pm", pm_node)
builder.add_node("researcher", research_agent)
builder.add_node("developer", dev_agent)
builder.add_node("qa", qa_agent)
builder.add_node("docs", docs_agent)
builder.add_node("report", report_node)

builder.add_edge(START, "pm")
builder.add_conditional_edges("pm", route_pm, {
    "researcher": "researcher",
    "developer": "developer",
    "qa": "qa",
    "docs": "docs",
    "report": "report",
})
# 每个 Agent 执行后回到 PM
builder.add_edge("researcher", "pm")
builder.add_edge("developer", "pm")
builder.add_edge("qa", "pm")
builder.add_edge("docs", "pm")
builder.add_edge("report", END)

checkpointer = MemorySaver()
dev_team_graph = builder.compile(checkpointer=checkpointer)

# === 交互循环 ===

async def main():
    print("=" * 55)
    print("Multi-Agent 研发团队")
    print("输入项目描述，团队将协作完成")
    print("=" * 55)

    while True:
        try:
            project = input("\n项目> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not project or project == "/quit":
            break

        print("\n团队开始工作...\n")
        config = {"configurable": {"thread_id": f"project_{hash(project) % 10000}"}}

        for event in dev_team_graph.stream({
            "messages": [HumanMessage(content=project)],
            "project": project,
            "subtasks": [], "current_phase": "",
            "research_output": "", "dev_output": "", "qa_output": "",
            "docs_output": "", "qa_passed": False, "iteration": 0,
            "final_report": "",
        }, config):
            for node, output in event.items():
                phase = output.get("current_phase", "")
                if phase:
                    print(f"  [PM] → 阶段: {phase}")
                elif node != "pm":
                    name_map = {"researcher": "研究", "developer": "开发",
                               "qa": "QA", "docs": "文档", "report": "报告"}
                    print(f"  [{name_map.get(node, node)}] 完成")

        result = dev_team_graph.get_state(config)
        print(f"\n{'='*55}")
        print(f"项目完成报告:")
        print(f"{'='*55}")
        print(result.values.get("final_report", "无报告"))

if __name__ == "__main__":
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

### 6.2 三种模式对比总结

```
┌────────────────────────────────────────────────────────────────┐
│  对比维度         │  Supervisor   │  Swarm      │  Hierarchical │
│──────────────────┼───────────────┼─────────────┼───────────────│
│  控制方式         │  中心化        │  去中心化    │  多层中心化   │
│  决策者           │  Supervisor   │  各 Agent   │  各层 Boss    │
│  通信路径         │  A→S→B        │  A→B        │  A→Sub→Top    │
│  全局视野         │  有            │  有限       │  顶层有       │
│  可控性           │  ★★★★★       │  ★★★       │  ★★★★        │
│  灵活性           │  ★★★         │  ★★★★★     │  ★★★★        │
│  实现复杂度       │  中            │  中高       │  高           │
│  适合规模         │  3-5 Agent   │  2-4 Agent │  5+ Agent    │
│──────────────────┼───────────────┼─────────────┼───────────────│
│  推荐场景         │  通用场景      │  流水线     │  大型项目     │
│                   │  （首选）      │            │               │
└────────────────────────────────────────────────────────────────┘
```

### Day 6 练习

1. 给研发团队添加一个 `architect` Agent——在研究之后、开发之前做架构设计
2. 添加人机交互——PM 拆分任务后，让用户确认子任务列表再继续
3. 用 SQLite 持久化，支持项目中途暂停、恢复

<details>
<summary>参考答案</summary>

```python
"""Day 6 练习答案：Architect + 人机交互 + 持久化"""

import os
import sys
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

class DevState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    project: str
    subtasks: list[str]
    current_phase: str
    research_output: str
    arch_output: str    # 练习 1：架构设计
    dev_output: str
    qa_output: str
    docs_output: str
    qa_passed: bool
    iteration: int
    final_report: str

def pm(state: DevState) -> dict:
    llm = make_llm(0)
    if not state.get("subtasks"):
        resp = llm.invoke(f"拆分项目为4个子任务（研究/架构/开发/文档），换行分隔:\n{state['project']}")
        subtasks = [s.strip() for s in resp.content.strip().split("\n") if s.strip()][:4]
        return {"subtasks": subtasks, "current_phase": "confirm"}  # 练习 2：先确认

    if state.get("current_phase") == "confirm":
        return {"current_phase": "research"}

    phase = state.get("current_phase", "research")
    transitions = {"research": "arch", "arch": "dev", "dev": "qa",
                   "qa": "docs" if state.get("qa_passed") else "dev",
                   "docs": "done"}
    next_phase = transitions.get(phase, "done")
    if next_phase == "dev" and phase == "qa":
        return {"current_phase": "dev", "iteration": state.get("iteration", 0) + 1}
    return {"current_phase": next_phase}

def confirm_tasks(state: DevState) -> dict:
    """练习 2：人机交互确认子任务"""
    human = interrupt({
        "prompt": "请确认子任务列表",
        "subtasks": state.get("subtasks", []),
    })
    if human.get("approved"):
        return {}  # 不改 phase，让 PM 将 "confirm" → "research"
    # 用户修改了子任务
    return {"subtasks": human.get("subtasks", state["subtasks"])}

def researcher(state: DevState) -> dict:
    llm = make_llm(0)
    task = state["subtasks"][0] if state.get("subtasks") else state["project"]
    resp = llm.invoke(f"研究: {task}")
    return {"research_output": resp.content}

def architect(state: DevState) -> dict:
    """练习 1：架构师"""
    llm = make_llm(0.1)
    research = state.get("research_output", "")[:300]
    task = state["subtasks"][1] if len(state.get("subtasks", [])) > 1 else "架构设计"
    resp = llm.invoke(f"设计架构:\n研究: {research}\n任务: {task}")
    return {"arch_output": resp.content}

def developer(state: DevState) -> dict:
    llm = make_llm(0.2)
    task = state["subtasks"][2] if len(state.get("subtasks", [])) > 2 else state["project"]
    arch = state.get("arch_output", "")[:200]
    feedback = state.get("qa_output", "") if state.get("iteration", 0) > 0 else ""
    prompt = f"开发: {task}\n架构: {arch}"
    if feedback:
        prompt += f"\nQA反馈: {feedback[:200]}"
    resp = llm.invoke(prompt)
    return {"dev_output": resp.content}

def qa(state: DevState) -> dict:
    llm = make_llm(0)
    code = state.get("dev_output", "")[:400]
    resp = llm.invoke(f"审查代码（有问题说明，没问题回复'通过'）:\n{code}")
    return {"qa_output": resp.content, "qa_passed": "通过" in resp.content}

def docs(state: DevState) -> dict:
    llm = make_llm(0.5)
    task = state["subtasks"][3] if len(state.get("subtasks", [])) > 3 else "写文档"
    resp = llm.invoke(f"写文档: {task}\n代码: {state.get('dev_output','')[:200]}")
    return {"docs_output": resp.content}

def report(state: DevState) -> dict:
    llm = make_llm(0.3)
    resp = llm.invoke(f"汇总项目:\n研究: {state.get('research_output','')[:100]}\n"
                       f"架构: {state.get('arch_output','')[:100]}\n"
                       f"代码: {state.get('dev_output','')[:100]}\n"
                       f"文档: {state.get('docs_output','')[:100]}")
    return {"final_report": resp.content}

def route(state: DevState) -> str:
    phase = state.get("current_phase", "done")
    mapping = {"confirm": "confirm", "research": "researcher", "arch": "architect",
               "dev": "developer", "qa": "qa", "docs": "docs", "done": "report"}
    return mapping.get(phase, "report")

builder = StateGraph(DevState)
for name, func in [("pm", pm), ("confirm", confirm_tasks), ("researcher", researcher),
                    ("architect", architect), ("developer", developer),
                    ("qa", qa), ("docs", docs), ("report", report)]:
    builder.add_node(name, func)

builder.add_edge(START, "pm")
builder.add_conditional_edges("pm", route, {
    "confirm": "confirm", "researcher": "researcher", "architect": "architect",
    "developer": "developer", "qa": "qa", "docs": "docs", "report": "report"})
for node in ["confirm", "researcher", "architect", "developer", "qa", "docs"]:
    builder.add_edge(node, "pm")
builder.add_edge("report", END)

# 练习 3：SQLite 持久化
checkpointer = MemorySaver()  # 生产环境可用 SqliteSaver
dev_graph = builder.compile(checkpointer=checkpointer)

# 测试
config = {"configurable": {"thread_id": "dev_project_1"}}
result = dev_graph.invoke({
    "messages": [HumanMessage(content="开发一个任务管理系统")],
    "project": "开发一个任务管理系统",
    "subtasks": [], "current_phase": "", "research_output": "",
    "arch_output": "", "dev_output": "", "qa_output": "", "docs_output": "",
    "qa_passed": False, "iteration": 0, "final_report": "",
}, config)
# 会在 confirm 节点中断
print("等待确认子任务...")
result = dev_graph.invoke(Command(resume={"approved": True}), config)
print(f"最终: {result['final_report'][:150]}...")
```

</details>

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

```
Multi-Agent 基础：
[ ] 理解为什么需要 Multi-Agent（单 Agent 的局限）
[ ] 能说出三种编排模式的名称和特点
[ ] 理解 Agent 通信的三种方式
[ ] 能用 LangGraph 实现基本的 Multi-Agent 系统

Supervisor 模式：
[ ] 能实现 Supervisor 路由节点
[ ] 能实现多轮任务分配（Agent → Sup → Agent 循环）
[ ] 能设置迭代限制防止死循环
[ ] 能实现 finish 节点汇总结果

Swarm 群智模式：
[ ] 理解 handoff 机制
[ ] 能实现 Agent 之间的直接 handoff
[ ] 理解 Swarm 和 Supervisor 的区别
[ ] 能设置 handoff 次数限制

Hierarchical 层级模式：
[ ] 能用子图实现子团队
[ ] 能实现顶层 Boss 拆分任务
[ ] 能实现并行子团队执行
[ ] 理解顶层和子团队 State 的独立性

Agent 通信与任务分配：
[ ] 能实现共享 State 通信
[ ] 能实现消息传递模式
[ ] 能实现混合路由（规则 + LLM）
[ ] 理解能力声明路由的概念

综合实战：
[ ] 能用 LangGraph 构建完整的 Multi-Agent 系统
[ ] 能根据场景选择合适的编排模式
[ ] 能实现质量门控（QA 不通过则回退）
[ ] 能集成人机交互和持久化
```

### 7.2 综合练习题

**项目：Multi-Agent 内容生产工厂**

构建一个 Multi-Agent 内容生产系统，功能要求：

1. **主编（Supervisor）**：接收内容需求，拆分为选题→写作→配图建议→审核
2. **选题 Agent**：根据需求生成 3 个选题方案
3. **写作 Agent**：选定选题后撰写文章
4. **配图 Agent**：为文章生成配图建议（文字描述）
5. **审核 Agent**：审核文章质量，不通过则退回写作
6. **持久化**：支持中途暂停、恢复
7. **质量门控**：最多修改 3 次

> 完成这个项目后，你就掌握了 Multi-Agent 系统的完整开发能力，可以作为简历中的亮点项目。

<details>
<summary>参考答案框架</summary>

```python
"""Multi-Agent 内容生产工厂 - 答案框架"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

def make_llm(temp=0.3):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

class ContentState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    requirement: str        # 用户的内容需求
    next: str               # Supervisor 路由
    topics: str             # 选题 Agent 输出
    selected_topic: str     # 选定的选题
    article: str            # 写作 Agent 输出
    image_suggestions: str  # 配图 Agent 输出
    review_result: str      # 审核 Agent 输出
    review_passed: bool
    revision_count: int
    final_output: str

def chief_editor(state: ContentState) -> dict:
    """主编 = Supervisor"""
    llm = make_llm(0)

    # 判断当前阶段
    if not state.get("topics"):
        return {"next": "topic_agent"}
    if not state.get("article"):
        return {"next": "writing_agent"}
    if not state.get("image_suggestions"):
        return {"next": "image_agent"}
    if not state.get("review_result"):
        return {"next": "review_agent"}

    # 审核后判断
    if state.get("review_passed"):
        return {"next": "finish"}
    if state.get("revision_count", 0) >= 3:
        return {"next": "finish"}  # 超过修改次数限制

    # 未通过，退回写作
    return {"next": "writing_agent"}

def topic_agent(state: ContentState) -> dict:
    """选题 Agent"""
    llm = make_llm(0.5)
    resp = llm.invoke(f"为以下需求生成3个选题方案:\n{state['requirement']}")
    return {"topics": resp.content}

def writing_agent(state: ContentState) -> dict:
    """写作 Agent"""
    llm = make_llm(0.7)
    topic = state.get("selected_topic") or state.get("topics", state["requirement"])
    feedback = state.get("review_result", "") if state.get("revision_count", 0) > 0 else ""
    prompt = f"根据选题写文章（500字以内）:\n选题: {topic}"
    if feedback:
        prompt += f"\n审核反馈（请修改）: {feedback[:200]}"
    resp = llm.invoke(prompt)
    return {"article": resp.content,
            "revision_count": state.get("revision_count", 0) + (1 if feedback else 0)}

def image_agent(state: ContentState) -> dict:
    """配图建议 Agent"""
    llm = make_llm(0.5)
    resp = llm.invoke(f"为文章生成3个配图建议:\n{state['article'][:300]}")
    return {"image_suggestions": resp.content}

def review_agent(state: ContentState) -> dict:
    """审核 Agent"""
    llm = make_llm(0)
    article = state.get("article", "")
    resp = llm.invoke(f"审核文章质量（回复'通过'或说明问题）:\n{article[:400]}")
    passed = "通过" in resp.content
    return {"review_result": resp.content, "review_passed": passed}

def finish_node(state: ContentState) -> dict:
    """汇总"""
    output = (
        f"选题: {state.get('topics', '')[:100]}\n\n"
        f"文章: {state.get('article', '')[:200]}\n\n"
        f"配图: {state.get('image_suggestions', '')[:100]}\n\n"
        f"审核: {state.get('review_result', '')[:100]}"
    )
    return {"final_output": output}

def route(state: ContentState) -> str:
    return state.get("next", "finish")

# 构建图
builder = StateGraph(ContentState)
for name, func in [("editor", chief_editor), ("topic_agent", topic_agent),
                    ("writing_agent", writing_agent), ("image_agent", image_agent),
                    ("review_agent", review_agent), ("finish", finish_node)]:
    builder.add_node(name, func)

builder.add_edge(START, "editor")
builder.add_conditional_edges("editor", route, {
    "topic_agent": "topic_agent", "writing_agent": "writing_agent",
    "image_agent": "image_agent", "review_agent": "review_agent",
    "finish": "finish"})
for agent in ["topic_agent", "writing_agent", "image_agent", "review_agent"]:
    builder.add_edge(agent, "editor")
builder.add_edge("finish", END)

content_graph = builder.compile(checkpointer=MemorySaver())

# 运行
config = {"configurable": {"thread_id": "content_1"}}
result = content_graph.invoke({
    "messages": [HumanMessage(content="写一篇关于 AI Agent 的科普文章")],
    "requirement": "写一篇关于 AI Agent 的科普文章",
    "next": "", "topics": "", "selected_topic": "", "article": "",
    "image_suggestions": "", "review_result": "", "review_passed": False,
    "revision_count": 0, "final_output": "",
}, config)
print(result["final_output"][:300])
```

</details>

### 7.3 Week 7 回顾与 Week 8 预告

```
Week 7 学习路径回顾：

Day 1: Multi-Agent 全景 + 基础概念
  → 三种编排模式、Agent 通信、第一个 Multi-Agent

Day 2: Supervisor 模式深入
  → 完整 Supervisor 系统、多轮分配、结果汇总

Day 3: Swarm 群智模式
  → handoff 机制、Agent 直接传递、vs Supervisor

Day 4: Hierarchical 层级模式
  → 子图实现子团队、顶层 Boss 拆分、并行执行

Day 5: Agent 通信与任务分配
  → 共享 State/消息传递/黑板、混合路由

Day 6: 综合实战
  → Multi-Agent 研发团队、PM+研究+开发+QA+文档

你已经掌握的能力：
✓ 理解 Multi-Agent 三种编排模式
✓ 用 LangGraph 实现 Supervisor/Swarm/Hierarchical
✓ 实现 Agent 间通信和任务分配
✓ 实现质量门控和迭代控制
✓ 构建完整的 Multi-Agent 系统
✓ 集成人机交互和持久化

接下来（Week 8 预告）：
Week 8: Agent 评测与部署
  → Agent 评测指标体系
  → 自动化测试框架
  → 性能优化与成本控制
  → 生产环境部署方案
```

---

## 本周知识图谱

```
Multi-Agent 系统
├── 基础概念（Day 1）
│   ├── 单 Agent vs Multi-Agent
│   ├── 三种编排模式
│   ├── Agent 通信方式
│   └── 第一个 Multi-Agent 程序
│
├── Supervisor 模式（Day 2）
│   ├── Supervisor 路由节点
│   ├── 多轮任务分配循环
│   ├── 迭代限制（防死循环）
│   ├── finish 汇总节点
│   └── 质量门控
│
├── Swarm 群智模式（Day 3）
│   ├── handoff 机制
│   ├── Agent 自主决策
│   ├── 直接传递控制权
│   ├── handoff 次数限制
│   └── vs Supervisor 对比
│
├── Hierarchical 层级模式（Day 4）
│   ├── 顶层 Boss 拆分任务
│   ├── 子图实现子团队
│   ├── 并行子团队执行
│   ├── 结果合并
│   └── 复杂度评估
│
├── 通信与任务分配（Day 5）
│   ├── 共享 State 通信
│   ├── 消息传递模式
│   ├── 混合路由（规则+LLM）
│   ├── 能力声明路由
│   └── 优先级队列
│
└── 综合实战（Day 6）
    ├── Multi-Agent 研发团队
    ├── PM + 研究 + 开发 + QA + 文档
    ├── 质量门控 + 迭代
    └── 三种模式对比总结
```

## Multi-Agent 速查表

```
┌──────────────────────────────────────────────────────────┐
│            Multi-Agent 常用代码速查                        │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Supervisor 模式核心结构：                                │
│  builder.add_node("supervisor", sup_node)               │
│  builder.add_node("agent_a", agent_a)                    │
│  builder.add_node("agent_b", agent_b)                    │
│  builder.add_edge(START, "supervisor")                   │
│  builder.add_conditional_edges("supervisor", router, {  │
│      "agent_a": "agent_a", "agent_b": "agent_b",        │
│      END: END})                                          │
│  builder.add_edge("agent_a", "supervisor")  # 回边      │
│  builder.add_edge("agent_b", "supervisor")  # 回边      │
│                                                          │
│  Swarm handoff：                                         │
│  # Agent 内部设置 handoff_to                             │
│  return {"handoff_to": "next_agent"}                    │
│  # 条件边根据 handoff_to 路由                            │
│  builder.add_conditional_edges("agent_a",               │
│      lambda s: s["handoff_to"], {...})                   │
│                                                          │
│  Hierarchical 子图：                                     │
│  sub_builder = StateGraph(SubState)                      │
│  ... sub_builder.compile()                               │
│  # 顶层节点调用子图                                      │
│  def team_node(state):                                   │
│      result = sub_graph.invoke({...})                    │
│      return {"result": result["output"]}                │
│                                                          │
│  质量门控：                                              │
│  def supervisor(state):                                  │
│      if state.get("needs_fix"):                          │
│          return {"next": "coder"}  # 退回修改            │
│      return {"next": "finish"}                           │
│                                                          │
│  防死循环：                                              │
│  if state["iteration"] >= MAX_ITERS:                    │
│      return {"next": "finish"}                           │
│                                                          │
│  并行执行：                                              │
│  builder.add_edge("boss", "team_a")  # 同时             │
│  builder.add_edge("boss", "team_b")  # 并行             │
│  builder.add_edge("team_a", "merge")  # 汇合            │
│  builder.add_edge("team_b", "merge")                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
