# Day6 - 子图与多 Agent 编排

> 一个 Agent 能力有限,一群 Agent 协作才能解决复杂问题。今天我们学习子图(把图当节点用)、Supervisor 模式(主管分配任务)、Swarm 模式(群智协作),构建多 Agent 系统。

---

## 一、当日目标

1. 掌握子图(Subgraph)的创建与使用:把一个编译好的图作为另一个图的节点。
2. 理解子图与父图的状态共享机制,能正确传递和接收状态。
3. 掌握 Supervisor 模式:用一个"主管 Agent"协调多个"工人 Agent"。
4. 了解 Swarm 模式:Agent 之间通过移交(handoff)传递控制权。
5. 实现一个"研究 + 写作"的双 Agent 协作系统。

---

## 二、子图(Subgraph)

### 2.1 什么是子图

子图就是把一个**编译好的 LangGraph 图**作为另一个图的**节点**。好处:
- 模块化:把复杂流程封装成独立单元。
- 复用:同一个子图可在多个父图中使用。
- 团队协作:不同人负责不同子图,最后拼装。

### 2.2 最简子图示例

```python
"""Day6 最简子图:把"翻译图"作为节点嵌入"主图""""
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


# === 子图:翻译流程 ===
class TranslateState(TypedDict):
    text: str
    translated: str


def to_upper(state: TranslateState) -> dict:
    return {"text": state["text"].upper()}


def add_prefix(state: TranslateState) -> dict:
    return {"translated": f"[EN] {state['text']}"}


translate_builder = StateGraph(TranslateState)
translate_builder.add_node("to_upper", to_upper)
translate_builder.add_node("add_prefix", add_prefix)
translate_builder.add_edge(START, "to_upper")
translate_builder.add_edge("to_upper", "add_prefix")
translate_builder.add_edge("add_prefix", END)
translate_graph = translate_builder.compile()  # 编译成可执行图


# === 父图:主流程 ===
class MainState(TypedDict):
    raw_text: str
    text: str          # 与子图共享
    translated: str    # 与子图共享
    final_report: str


def prepare(state: MainState) -> dict:
    return {"text": state["raw_text"].strip()}


def make_report(state: MainState) -> dict:
    return {"final_report": f"翻译完成:{state['translated']}"}


main_builder = StateGraph(MainState)
main_builder.add_node("prepare", prepare)
# 关键:把编译好的子图直接作为节点添加
main_builder.add_node("translate", translate_graph)
main_builder.add_node("report", make_report)

main_builder.add_edge(START, "prepare")
main_builder.add_edge("prepare", "translate")
main_builder.add_edge("translate", "report")
main_builder.add_edge("report", END)

main_graph = main_builder.compile()

result = main_graph.invoke({
    "raw_text": "  hello world  ",
    "text": "",
    "translated": "",
    "final_report": "",
})
print(result["final_report"])  # 翻译完成:[EN] HELLO WORLD
```

### 2.3 状态共享规则

父图和子图**共享同名字段**:
- 父图 `MainState` 有 `text` 和 `translated`,子图 `TranslateState` 也有这两个字段。
- 父图调用子图节点时,会把所有同名字段传给子图。
- 子图执行完,返回的字段更新到父图状态(同名覆盖)。
- 父图独有字段(如 `raw_text`、`final_report`)子图看不到。
- 子图独有字段(如果有)父图也看不到。

如果父图和子图状态完全不同(无同名字段),子图节点会收到空状态——这通常不是你想要的。设计时要规划好共享字段。

### 2.4 带状态转换的子图

如果父图和子图状态结构差异大,可以包一个"适配节点"做转换:

```python
def translate_adapter(state: MainState) -> dict:
    # 把父图状态转成子图需要的输入
    sub_input = {"text": state["raw_text"], "translated": ""}
    sub_result = translate_graph.invoke(sub_input)
    # 把子图输出转回父图字段
    return {"translated": sub_result["translated"]}

main_builder.add_node("translate", translate_adapter)
```

这种方式更灵活,但要手动调用子图,失去了"图即节点"的声明式简洁。

---

## 三、Supervisor 模式

### 3.1 模式介绍

Supervisor(主管)模式:一个"主管 Agent"接收用户请求,决定把任务分给哪个"工人 Agent",工人完成后汇报给主管,主管决定是否结束或继续分配。

```
用户 → Supervisor → (选择)→ Worker A / Worker B / Worker C
                         ↑_______________|
                         (汇报结果)
Supervisor → 最终回答 → 用户
```

这是最常用的多 Agent 模式,适合"任务可拆分、需要协调"的场景。

### 3.2 完整实现:研究 + 写作 Supervisor

我们构建一个 Supervisor,管理两个工人:
- `researcher`:负责查资料(模拟)。
- `writer`:负责根据资料写文章。

```python
"""Day6 Supervisor 模式:研究 + 写作"""
import os
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command

load_dotenv()


class TeamState(TypedDict):
    messages: Annotated[list, add_messages]
    topic: str
    research_notes: str
    draft: str
    next: str  # supervisor 决定的下一步


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# === Supervisor 节点 ===
def supervisor(state: TeamState) -> Command:
    """主管:决定下一步派谁干活"""
    # 用结构化输出让 LLM 返回决策
    decision_llm = llm.bind_tools([{
        "name": "route",
        "description": "选择下一步要执行的工人",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {
                    "type": "string",
                    "enum": ["researcher", "writer", "FINISH"],
                },
                "reason": {"type": "string"},
            },
            "required": ["next"],
        },
    }], tool_choice="route")

    prompt = f"""你是团队主管。当前状态:
- 主题:{state.get('topic', '(未定)')}
- 研究笔记:{state.get('research_notes', '(无)')[:200] or '(无)'}
- 当前草稿:{state.get('draft', '(无)')[:200] or '(无)'}

决策规则:
- 如果还没有研究笔记,派 researcher 去研究。
- 如果有研究笔记但没有草稿,派 writer 去写。
- 如果草稿已完成,返回 FINISH。
"""
    response = decision_llm.invoke([HumanMessage(content=prompt)])
    tool_call = response.tool_calls[0]
    next_step = tool_call["args"]["next"]

    if next_step == "FINISH":
        return Command(
            update={"messages": [AIMessage(content="任务完成,以下是最终草稿。")]},
            goto=END,
        )
    return Command(update={"next": next_step}, goto=next_step)


# === Researcher 工人节点 ===
def researcher(state: TeamState) -> dict:
    """研究员:收集资料(模拟)"""
    topic = state["topic"]
    # 实际可调用搜索工具,这里用 LLM 模拟
    prompt = f"针对主题'{topic}',列出 3 个关键要点(模拟研究),简短输出。"
    notes = llm.invoke(prompt).content
    return {
        "research_notes": notes,
        "messages": [AIMessage(content=f"[研究完成]\n{notes}")],
    }


# === Writer 工人节点 ===
def writer(state: TeamState) -> dict:
    """写手:根据研究笔记写文章"""
    notes = state["research_notes"]
    prompt = f"根据以下研究笔记,写一篇 150 字左右的短文:\n{notes}"
    draft = llm.invoke(prompt).content
    return {
        "draft": draft,
        "messages": [AIMessage(content=f"[写作完成]\n{draft}")],
    }


# === 构建图 ===
builder = StateGraph(TeamState)
builder.add_node("supervisor", supervisor)
builder.add_node("researcher", researcher)
builder.add_node("writer", writer)

builder.add_edge(START, "supervisor")
# 工人完成后回到 supervisor
builder.add_edge("researcher", "supervisor")
builder.add_edge("writer", "supervisor")
# supervisor 用 Command 路由,不需要显式 conditional_edges

graph = builder.compile()


def main():
    result = graph.invoke(
        {
            "topic": "人工智能在移动开发中的应用",
            "messages": [],
            "research_notes": "",
            "draft": "",
            "next": "",
        },
        config={"recursion_limit": 10},
    )
    print("=== 最终草稿 ===")
    print(result["draft"])
    print(f"\n消息轮数:{len(result['messages'])}")


if __name__ == "__main__":
    main()
```

### 3.3 流程解析

1. `START → supervisor`:主管看状态,没研究笔记 → 派 `researcher`。
2. `researcher`:研究主题,返回 `research_notes`。
3. `researcher → supervisor`:主管看状态,有笔记没草稿 → 派 `writer`。
4. `writer`:根据笔记写文章,返回 `draft`。
5. `writer → supervisor`:主管看状态,草稿完成 → `FINISH` → `END`。

`Command(goto=...)` 让 supervisor 灵活路由,工人完成后固定回到 supervisor 形成循环。

---

## 四、Swarm 模式(进阶)

### 4.1 模式介绍

Swarm(群)模式:没有中央主管,Agent 之间通过**移交(handoff)**直接把控制权传给另一个 Agent。每个 Agent 决定"我自己处理"还是"交给别人"。

适合"对话流转、职责切换"场景,如客服:售前 Agent 发现用户要退款,移交给售后 Agent。

### 4.2 简化 Swarm 实现

```python
"""Day6 Swarm 模式:客服 handoff"""
import os
from typing import TypedDict, Annotated, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command

load_dotenv()


class SwarmState(TypedDict):
    messages: Annotated[list, add_messages]
    current_agent: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def make_agent(name: str, system_prompt: str, can_handoff_to: list):
    """工厂函数:生成一个 Agent 节点"""

    def agent_fn(state: SwarmState) -> Command:
        tools = [{
            "name": "transfer_to",
            "description": f"把对话移交给另一个 Agent。可选:{can_handoff_to}",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "enum": can_handoff_to + [name]},
                    "reason": {"type": "string"},
                },
                "required": ["agent"],
            },
        }]
        agent_llm = llm.bind_tools(tools)

        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        response = agent_llm.invoke(messages)

        # 检查是否要移交
        if response.tool_calls:
            tc = response.tool_calls[0]
            target = tc["args"]["agent"]
            if target != name:
                return Command(
                    update={
                        "current_agent": target,
                        "messages": [AIMessage(content=f"[移交] 转接给 {target}: {tc['args'].get('reason', '')}")],
                    },
                    goto=target,
                )
        # 自己处理
        return Command(
            update={"messages": [response], "current_agent": name},
            goto=END,
        )

    return agent_fn


# 定义三个 Agent
sales_agent = make_agent(
    "sales",
    "你是售前客服,负责介绍产品和价格。如果用户要退款或投诉,移交给 support。如果用户问技术细节,移交给 tech。",
    ["support", "tech"],
)

support_agent = make_agent(
    "support",
    "你是售后客服,负责退款和投诉处理。如果用户要买产品,移交给 sales。技术问题移交给 tech。",
    ["sales", "tech"],
)

tech_agent = make_agent(
    "tech",
    "你是技术支持,负责解答技术问题。购买问题移交给 sales,退款移交给 support。",
    ["sales", "support"],
)


# 路由入口:根据 current_agent 决定第一个进哪个 Agent
def entry_router(state: SwarmState) -> str:
    return state.get("current_agent", "sales")


builder = StateGraph(SwarmState)
builder.add_node("sales", sales_agent)
builder.add_node("support", support_agent)
builder.add_node("tech", tech_agent)

builder.add_conditional_edges(START, entry_router)
# 各 Agent 内部用 Command goto,不显式声明边
# 但为了让图结构可分析,声明可能的转移
for n in ["sales", "support", "tech"]:
    builder.add_edge(n, END)  # 默认到 END,实际由 Command 覆盖

graph = builder.compile()


def main():
    # 测试:从 sales 开始,用户要退款 → 移交 support
    result = graph.invoke({
        "messages": [HumanMessage(content="我昨天买的手机想退款")],
        "current_agent": "sales",
    })
    print("最终 current_agent:", result["current_agent"])
    print("最后消息:", result["messages"][-1].content)
    print("消息历史:")
    for m in result["messages"]:
        print(f"  [{m.type}] {m.content}")


if __name__ == "__main__":
    main()
```

### 4.3 Swarm vs Supervisor

| 维度 | Supervisor | Swarm |
|------|-----------|-------|
| 控制方式 | 中心化,主管调度 | 去中心化,Agent 互相移交 |
| 适合场景 | 任务拆分、流水线 | 对话流转、职责切换 |
| 扩展性 | 加工人需更新主管 prompt | 加 Agent 各自声明 handoff |
| 可控性 | 高(主管把关) | 中(可能乱跑) |
| 复杂度 | 中等 | 较高 |

LangGraph 官方还提供了 `langgraph-supervisor` 和 `langgraph-swarm` 包,封装了更完善的实现,生产可直接用:

```bash
pip install langgraph-supervisor
pip install langgraph-swarm
```

```python
# 官方 Supervisor 包用法(示意)
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

researcher = create_react_agent(llm, tools=[search_tool], name="researcher")
writer = create_react_agent(llm, tools=[write_tool], name="writer")

supervisor = create_supervisor(
    agents=[researcher, writer],
    model=llm,
    prompt="你是主管,协调 researcher 和 writer。",
)
app = supervisor.compile()
```

---

## 五、Agent 通信机制

### 5.1 共享状态通信

最常见:所有 Agent 读写同一个 `TeamState`。Supervisor 模式就是这种——researcher 写 `research_notes`,writer 读它。简单直接,但状态会越来越大。

### 5.2 消息通道通信

用 `messages` 字段作为"公告板":每个 Agent 发消息时标注自己是谁,其他 Agent 通过读消息历史了解上下文。Swarm 模式常用这种。

### 5.3 私有信道

给每个 Agent 一个私有字段(如 `researcher_notes`、`writer_notes`),互不干扰,只有 supervisor 能看所有:

```python
class TeamState(TypedDict):
    messages: Annotated[list, add_messages]
    researcher_notes: str   # 只有 researcher 写
    writer_notes: str       # 只有 writer 写
    shared_brief: str       # 交换用的公共区
```

---

## 六、实战:多 Agent 文档分析工作流

构建一个三 Agent 系统:摘要 Agent + 翻译 Agent + 审校 Agent,用 Supervisor 协调。

```python
"""Day6 实战:多 Agent 文档分析工作流"""
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command

load_dotenv()


class DocState(TypedDict):
    messages: Annotated[list, add_messages]
    document: str
    summary: str
    translation: str
    polished: str
    next: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def supervisor(state: DocState) -> Command:
    decision_llm = llm.bind_tools([{
        "name": "route",
        "description": "选择下一个 Agent",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {"type": "string", "enum": ["summarizer", "translator", "polisher", "FINISH"]},
            },
            "required": ["next"],
        },
    }], tool_choice="route")

    prompt = f"""你是文档分析主管。当前状态:
- 文档已提供:{"是" if state.get("document") else "否"}
- 摘要完成:{"是" if state.get("summary") else "否"}
- 翻译完成:{"是" if state.get("translation") else "否"}
- 审校完成:{"是" if state.get("polished") else "否"}

流程:summarizer → translator → polisher → FINISH。按顺序派遣未完成的步骤。
"""
    resp = decision_llm.invoke([HumanMessage(content=prompt)])
    nxt = resp.tool_calls[0]["args"]["next"]
    if nxt == "FINISH":
        return Command(update={"messages": [AIMessage(content="文档分析全流程完成")]}, goto=END)
    return Command(update={"next": nxt}, goto=nxt)


def summarizer(state: DocState) -> dict:
    prompt = f"用中文把以下文档总结成 3 句话:\n{state['document']}"
    summary = llm.invoke(prompt).content
    return {"summary": summary, "messages": [AIMessage(content=f"[摘要]\n{summary}")]}


def translator(state: DocState) -> dict:
    prompt = f"把以下中文摘要翻译成英文,只输出译文:\n{state['summary']}"
    translation = llm.invoke(prompt).content
    return {"translation": translation, "messages": [AIMessage(content=f"[翻译]\n{translation}")]}


def polisher(state: DocState) -> dict:
    prompt = f"润色以下英文翻译,使其更地道,只输出润色后文本:\n{state['translation']}"
    polished = llm.invoke(prompt).content
    return {"polished": polished, "messages": [AIMessage(content=f"[审校]\n{polished}")]}


builder = StateGraph(DocState)
builder.add_node("supervisor", supervisor)
builder.add_node("summarizer", summarizer)
builder.add_node("translator", translator)
builder.add_node("polisher", polisher)

builder.add_edge(START, "supervisor")
builder.add_edge("summarizer", "supervisor")
builder.add_edge("translator", "supervisor")
builder.add_edge("polisher", "supervisor")

graph = builder.compile()


def main():
    document = """
    LangGraph 是一个用于构建有状态、多角色 LLM 应用的框架。
    它采用图结构来建模工作流,支持循环、条件分支、持久化和人机协同。
    通过 Checkpointer,应用可以拥有跨会话的记忆能力。
    """
    result = graph.invoke(
        {
            "document": document,
            "messages": [],
            "summary": "",
            "translation": "",
            "polished": "",
            "next": "",
        },
        config={"recursion_limit": 15},
    )
    print("=== 中文摘要 ===")
    print(result["summary"])
    print("\n=== 英文翻译 ===")
    print(result["translation"])
    print("\n=== 润色后 ===")
    print(result["polished"])
    print(f"\n总消息数:{len(result['messages'])}")


if __name__ == "__main__":
    main()
```

---

## 七、当日小结

- **子图**:把编译好的图作为节点,实现模块化。父图与子图共享同名字段。
- **Supervisor 模式**:中心化,主管用 `Command(goto=...)` 调度工人,工人完成后回主管。适合任务拆分。
- **Swarm 模式**:去中心化,Agent 之间通过 handoff 移交控制权。适合对话流转。
- **Agent 通信**:共享状态、消息通道、私有信道三种方式。
- 官方 `langgraph-supervisor` 和 `langgraph-swarm` 包提供生产级实现。
- 多 Agent 系统注意 `recursion_limit`,Agent 越多越容易触发循环限制。

---

## 八、练习题

### 选择题

**1. 关于子图与父图的状态共享,正确的是?**
A. 子图能看到父图的所有字段
B. 父图和子图共享同名字段,各自独有字段互不可见
C. 子图必须和父图用同一个 State 类型
D. 子图无法向父图返回数据

**2. Supervisor 模式中,工人 Agent 完成任务后通常?**
A. 直接结束图
B. 回到 supervisor,由 supervisor 决定下一步
C. 调用下一个工人
D. 等待用户输入

**3. Swarm 模式的核心机制是?**
A. 主管调度
B. Agent 之间通过 handoff 移交控制权
C. 投票表决
D. 随机选择执行者

### 填空题

**4.** 把编译好的子图加入父图,使用 `______.add_node("名称", 编译后的图)`。

**5.** Supervisor 路由通常用 `______` 对象的 `goto` 参数指定下一个工人。

**6.** 官方封装的 Supervisor 实现包名是 `langgraph-______`。

### 编程题

**7.** 构建一个 Supervisor + 两个工人的图:工人 `add` 负责把 state 里的 `number` 加 10,工人 `double` 负责把 `number` 翻倍。Supervisor 根据规则派遣:如果 `number < 100` 派 `add`,如果 `number >= 100` 且 `number < 200` 派 `double`,否则 FINISH。初始 number=0,运行后观察结果。

**8.** 扩展本日的"文档分析工作流",新增一个 `keyword_extractor` 工人:在 summarizer 之后、translator 之前,提取文档的 3 个关键词存入 state 的 `keywords` 字段。调整 supervisor 的派遣逻辑,确保流程为 summarizer → keyword_extractor → translator → polisher → FINISH。

---

## 九、练习题答案

### 1. 答案:B
解析:LangGraph 子图通过"同名字段"与父图共享状态。父图独有的字段子图看不到(传过去时被过滤),子图独有的字段父图也看不到(返回时被过滤)。这是设计子图时要规划共享字段的原因。

### 2. 答案:B
解析:Supervisor 模式的标志性结构是"工人 → supervisor"的回边。工人只管完成自己的任务并返回结果,由 supervisor 统一决定下一步,避免工人之间直接耦合。

### 3. 答案:B
解析:Swarm 模式中,每个 Agent 自主决定是否 handoff 给另一个 Agent,没有中央调度。这种去中心化结构适合对话流转场景。

### 4. 答案:`builder`(或 StateGraph 实例)
解析:`main_builder.add_node("translate", translate_graph)`,直接把编译后的图对象作为第二参数。

### 5. 答案:`Command`
解析:`from langgraph.types import Command; Command(update={...}, goto="worker_name")`。Day3 学的 Command 在多 Agent 编排中大量使用。

### 6. 答案:`supervisor`
解析:`pip install langgraph-supervisor`,然后 `from langgraph_supervisor import create_supervisor`。

### 7. 参考代码

```python
"""Day6 练习题7:Supervisor + add/double 工人"""
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command


class NumState(TypedDict):
    number: int
    next: str


def supervisor(state: NumState) -> Command:
    n = state["number"]
    if n < 100:
        return Command(update={"next": "add"}, goto="add")
    elif n < 200:
        return Command(update={"next": "double"}, goto="double")
    return Command(update={"next": "FINISH"}, goto=END)


def add_worker(state: NumState) -> dict:
    return {"number": state["number"] + 10}


def double_worker(state: NumState) -> dict:
    return {"number": state["number"] * 2}


builder = StateGraph(NumState)
builder.add_node("supervisor", supervisor)
builder.add_node("add", add_worker)
builder.add_node("double", double_worker)

builder.add_edge(START, "supervisor")
builder.add_edge("add", "supervisor")
builder.add_edge("double", "supervisor")

graph = builder.compile()
result = graph.invoke({"number": 0, "next": ""}, config={"recursion_limit": 30})
print("最终 number:", result["number"])
# 流程:0 →add→ 10 →add→ ... →add→ 100 →double→ 200 → FINISH
# 0+10*10=100, 100>=100 且 <200 → double → 200, >=200 → FINISH
```

### 8. 参考代码

```python
"""Day6 练习题8:文档分析 + 关键词提取"""
import os
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.types import Command

load_dotenv()


class DocState(TypedDict):
    messages: Annotated[list, add_messages]
    document: str
    summary: str
    keywords: str
    translation: str
    polished: str
    next: str


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def supervisor(state: DocState) -> Command:
    decision_llm = llm.bind_tools([{
        "name": "route",
        "description": "选择下一个 Agent",
        "parameters": {
            "type": "object",
            "properties": {
                "next": {"type": "string", "enum": ["summarizer", "keyword_extractor", "translator", "polisher", "FINISH"]},
            },
            "required": ["next"],
        },
    }], tool_choice="route")

    prompt = f"""你是文档分析主管。当前状态:
- 摘要完成:{"是" if state.get("summary") else "否"}
- 关键词完成:{"是" if state.get("keywords") else "否"}
- 翻译完成:{"是" if state.get("translation") else "否"}
- 审校完成:{"是" if state.get("polished") else "否"}

流程顺序:summarizer → keyword_extractor → translator → polisher → FINISH。派遣第一个未完成的步骤。
"""
    resp = decision_llm.invoke([HumanMessage(content=prompt)])
    nxt = resp.tool_calls[0]["args"]["next"]
    if nxt == "FINISH":
        return Command(update={"messages": [AIMessage(content="全流程完成")]}, goto=END)
    return Command(update={"next": nxt}, goto=nxt)


def summarizer(state: DocState) -> dict:
    s = llm.invoke(f"用中文总结以下文档为 3 句话:\n{state['document']}").content
    return {"summary": s, "messages": [AIMessage(content=f"[摘要]{s}")]}


def keyword_extractor(state: DocState) -> dict:
    k = llm.invoke(f"从以下摘要提取 3 个关键词,逗号分隔:\n{state['summary']}").content
    return {"keywords": k, "messages": [AIMessage(content=f"[关键词]{k}")]}


def translator(state: DocState) -> dict:
    t = llm.invoke(f"翻译成英文:\n{state['summary']}").content
    return {"translation": t, "messages": [AIMessage(content=f"[翻译]{t}")]}


def polisher(state: DocState) -> dict:
    p = llm.invoke(f"润色更地道:\n{state['translation']}").content
    return {"polished": p, "messages": [AIMessage(content=f"[审校]{p}")]}


builder = StateGraph(DocState)
builder.add_node("supervisor", supervisor)
builder.add_node("summarizer", summarizer)
builder.add_node("keyword_extractor", keyword_extractor)
builder.add_node("translator", translator)
builder.add_node("polisher", polisher)

builder.add_edge(START, "supervisor")
for n in ["summarizer", "keyword_extractor", "translator", "polisher"]:
    builder.add_edge(n, "supervisor")

graph = builder.compile()

if __name__ == "__main__":
    doc = "LangGraph 用图建模 LLM 应用,支持状态管理和持久化,适合构建复杂 Agent。"
    r = graph.invoke({"document": doc, "messages": [], "summary": "", "keywords": "", "translation": "", "polished": "", "next": ""},
                     config={"recursion_limit": 20})
    print("摘要:", r["summary"])
    print("关键词:", r["keywords"])
    print("翻译:", r["translation"])
    print("润色:", r["polished"])
```

---

你已掌握多 Agent 编排的核心模式。明天我们用这些能力完成一个完整实战项目。

下一站:[07-Day7-实战项目.md](07-Day7-实战项目.md)
