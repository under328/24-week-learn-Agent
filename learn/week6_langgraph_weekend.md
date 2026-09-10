## Day 6：综合实战——用 LangGraph 构建知识库 Agent

> 用 LangGraph 从零构建一个完整的知识库问答 Agent，集成 RAG、工具调用、对话记忆和人机交互。

### 6.1 架构设计

```
┌────────── 知识库 Agent 架构（LangGraph） ──────────┐
│                                                      │
│                    START                             │
│                      │                               │
│                      ↓                               │
│              ┌──────────────┐                        │
│              │  understand  │  理解用户意图           │
│              └──────┬───────┘                        │
│                     │                                │
│              ┌──────┴──────┐                         │
│              ↓             ↓                         │
│        [need_rag]     [need_tool]    [direct]       │
│              │             │             │           │
│              ↓             │             │           │
│        ┌─────────┐         │             │           │
│        │ retrieve │         │             │           │
│        └────┬────┘         │             │           │
│             ↓               │             │           │
│        ┌─────────┐         │             │           │
│        │ generate │         │             │           │
│        └────┬────┘         │             │           │
│             │               │             │           │
│             ↓               ↓             ↓           │
│        ┌──────────────────────────────┐             │
│        │          respond             │  统一响应    │
│        └──────────────┬───────────────┘             │
│                       │                              │
│                       ↓                              │
│                      END                             │
│                                                      │
└──────────────────────────────────────────────────────┘
```

创建文件 `day6_kb_agent.py`：

```python
"""
Day 6: 用 LangGraph 构建知识库 Agent
- 意图理解 → 路由
- RAG 检索
- 工具调用
- 对话记忆（持久化）
- 流式输出
"""

import os
import sys
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# === 配置 ===

LLM_CONFIG = {
    "model": "glm-4-flash",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "api_key": os.environ.get("ZHIPU_API_KEY"),
}

llm = ChatOpenAI(**LLM_CONFIG, temperature=0.3)
embeddings = OpenAIEmbeddings(
    model="embedding-3",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
)

# === 知识库初始化 ===

def init_knowledge_base(db_dir: str = "./kb_agent_graph") -> Chroma:
    """初始化知识库"""
    if os.path.exists(db_dir):
        return Chroma(persist_directory=db_dir, embedding_function=embeddings)

    # 创建示例文档
    docs_dir = "./kb_docs"
    os.makedirs(docs_dir, exist_ok=True)
    sample_docs = {
        "python_basics.txt": """Python 基础知识
Python 是一种高级编程语言，由 Guido van Rossum 于 1991 年创建。
Python 使用缩进表示代码块，而不是大括号。
Python 支持面向对象、函数式和过程式编程。
Python 的标准库非常丰富，被称为"内置电池"。
常用数据类型：int, float, str, list, dict, tuple, set, bool。
""",
        "langchain_guide.txt": """LangChain 框架指南
LangChain 是构建 LLM 应用的开源框架。
核心组件：Model I/O、Retrieval、Chains、Agents、Memory、Callbacks。
LCEL（LangChain Expression Language）用管道符 | 组合组件。
LangChain 0.3+ 将核心包拆分为 langchain-core、langchain-community、langchain-openai。
""",
        "langgraph_guide.txt": """LangGraph 框架指南
LangGraph 是 LangChain 团队的图编排框架。
核心概念：State（状态）、Node（节点）、Edge（边）、Graph（图）。
支持条件路由、循环、并行执行、人机交互。
使用 Checkpointer 实现状态持久化。
适合构建复杂多步骤的 Agent 工作流。
""",
    }
    for name, content in sample_docs.items():
        with open(os.path.join(docs_dir, name), "w", encoding="utf-8") as f:
            f.write(content)

    # 加载并索引
    all_docs = []
    for name in sample_docs:
        loader = TextLoader(os.path.join(docs_dir, name), encoding="utf-8")
        all_docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=30)
    splits = splitter.split_documents(all_docs)
    vs = Chroma.from_documents(splits, embeddings, persist_directory=db_dir)
    print(f"知识库已创建: {len(splits)} 个文档块")
    return vs

vectorstore = init_knowledge_base()

# === 工具定义 ===

@tool
def knowledge_search(query: str) -> str:
    """从知识库搜索信息。输入为搜索关键词或问题。"""
    docs = vectorstore.similarity_search(query, k=3)
    if not docs:
        return "未在知识库中找到相关信息"
    return "\n\n".join(f"[{d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs)

@tool
def calculator(expression: str) -> str:
    """计算数学表达式。输入为数学表达式字符串。"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：只支持基本数学运算"
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"

tools = [knowledge_search, calculator]
tools_map = {t.name: t for t in tools}
llm_with_tools = llm.bind_tools(tools)

# === State 定义 ===

class KBAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    iterations: int
    route: str           # 路由结果: "rag", "tools", "direct"
    rag_context: str     # RAG 检索结果
    final_answer: str

# === 节点定义 ===

def understand_node(state: KBAgentState) -> dict:
    """理解用户意图，决定路由"""
    last_msg = state["messages"][-1]
    if not isinstance(last_msg, HumanMessage):
        return {"route": "direct"}

    response = llm.invoke(
        f"判断以下问题需要什么处理方式，只回答一个词：\n"
        f"- rag（需要检索知识库）\n"
        f"- tools（需要使用计算器等工具）\n"
        f"- direct（可以直接回答）\n"
        f"问题: {last_msg.content}"
    )
    route = response.content.strip().lower()
    if "rag" in route:
        route = "rag"
    elif "tool" in route:
        route = "tools"
    else:
        route = "direct"
    return {"route": route, "iterations": state["iterations"] + 1}

def rag_node(state: KBAgentState) -> dict:
    """RAG 检索 + 生成"""
    question = state["messages"][-1].content

    # 检索
    docs = vectorstore.similarity_search(question, k=3)
    context = "\n\n".join(d.page_content for d in docs)

    # 生成
    prompt = ChatPromptTemplate.from_messages([
        ("system", "根据文档内容回答问题。如文档中无相关信息，请如实说明。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "文档内容:\n{context}\n\n问题: {question}"),
    ])

    history = state["messages"][:-1]  # 除了最后一条
    response = llm.invoke(prompt.invoke({
        "context": context,
        "question": question,
        "history": history,
    }).to_messages())

    return {"rag_context": context, "final_answer": response.content}

def tools_node(state: KBAgentState) -> dict:
    """工具调用节点"""
    response = llm_with_tools.invoke(state["messages"])

    if hasattr(response, "tool_calls") and response.tool_calls:
        results = []
        for tc in response.tool_calls:
            func = tools_map.get(tc["name"])
            r = func.invoke(tc["args"]) if func else "未知工具"
            results.append(ToolMessage(content=str(r), tool_call_id=tc["id"]))

        # 用工具结果再次调用 LLM 生成最终回答
        all_msgs = state["messages"] + [response] + results
        final_response = llm.invoke(all_msgs)
        return {
            "messages": [response] + results + [final_response],
            "final_answer": final_response.content,
        }
    else:
        return {"final_answer": response.content}

def direct_node(state: KBAgentState) -> dict:
    """直接回答"""
    response = llm.invoke(state["messages"])
    return {"final_answer": response.content}

def respond_node(state: KBAgentState) -> dict:
    """统一响应节点"""
    answer = state.get("final_answer", "")
    return {"messages": [AIMessage(content=answer)]}

# === 路由函数 ===

def route_by_intent(state: KBAgentState) -> str:
    return state.get("route", "direct")

# === 构建图 ===

builder = StateGraph(KBAgentState)

builder.add_node("understand", understand_node)
builder.add_node("rag", rag_node)
builder.add_node("tools", tools_node)
builder.add_node("direct", direct_node)
builder.add_node("respond", respond_node)

builder.add_edge(START, "understand")
builder.add_conditional_edges("understand", route_by_intent, {
    "rag": "rag",
    "tools": "tools",
    "direct": "direct",
})
builder.add_edge("rag", "respond")
builder.add_edge("tools", "respond")
builder.add_edge("direct", "respond")
builder.add_edge("respond", END)

# 编译（带 checkpointer 支持对话记忆）
checkpointer = MemorySaver()
kb_agent_graph = builder.compile(checkpointer=checkpointer)

# === 交互循环 ===

async def main():
    print("=" * 50)
    print("知识库 Agent（LangGraph 版）")
    print("命令: /quit 退出 | /history 查看历史")
    print("=" * 50)

    session_id = "default"
    config = {"configurable": {"thread_id": session_id}}

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input == "/quit":
            print("再见！")
            break
        if user_input == "/history":
            state = kb_agent_graph.get_state(config)
            msgs = state.values.get("messages", [])
            print(f"消息数: {len(msgs)}")
            for m in msgs[-6:]:  # 最近6条
                role = type(m).__name__
                print(f"  {role}: {m.content[:60]}...")
            continue

        # 运行图
        try:
            result = kb_agent_graph.invoke(
                {"messages": [HumanMessage(content=user_input)],
                 "iterations": 0, "route": "", "rag_context": "", "final_answer": ""},
                config,
            )
            print(f"\nAI: {result['final_answer']}")
            print(f"   (路由: {result['route']})")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

### 6.2 流式输出集成

```python
"""
为知识库 Agent 添加流式输出
"""

# LangGraph 的 stream 方法返回每步的状态变化
# 可以结合 LLM 的 stream 实现 token 级流式

def stream_agent_response(graph, user_input: str, config: dict):
    """流式输出 Agent 响应"""
    print("AI: ", end="", flush=True)

    for event in graph.stream(
        {"messages": [HumanMessage(content=user_input)],
         "iterations": 0, "route": "", "rag_context": "", "final_answer": ""},
        config,
        stream_mode="updates",  # "updates" 每步返回变更, "values" 返回完整状态
    ):
        for node_name, node_output in event.items():
            if node_name == "respond":
                # respond 节点的输出就是最终回答
                answer = node_output.get("messages", [{}])[-1]
                if hasattr(answer, "content"):
                    print(answer.content, end="", flush=True)
            elif node_name in ("rag", "tools", "direct"):
                # 中间节点的处理信息
                route = node_output.get("route", "")
                if route:
                    print(f"[路由: {route}] ", end="", flush=True)
    print()  # 换行

# 使用
# stream_agent_response(kb_agent_graph, "什么是 LangGraph？", config)
```

### 6.3 对比：LangChain AgentExecutor vs LangGraph

```
┌────────────────────────────────────────────────────────────────┐
│  对比维度         │  AgentExecutor      │  LangGraph             │
│──────────────────┼─────────────────────┼────────────────────────│
│  流程控制         │  单一循环            │  任意拓扑图             │
│  条件分支         │  不支持              │  add_conditional_edges │
│  并行执行         │  不支持              │  多边扇出              │
│  人机交互         │  不支持              │  interrupt + resume    │
│  状态管理         │  Memory 组件         │  State + Checkpointer  │
│  调试可视化       │  verbose=True        │  graph.draw_ascii()    │
│  循环控制         │  max_iterations      │  条件边 + 自定义终止   │
│  子流程复用       │  不支持              │  子图                  │
│  回溯重放         │  不支持              │  checkpoint 历史       │
│──────────────────┼─────────────────────┼────────────────────────│
│  适用场景         │  简单工具调用 Agent  │  复杂多步骤工作流       │
│  学习曲线         │  低                  │  中                    │
│  灵活性           │  ★★★               │  ★★★★★                │
│  生产就绪         │  ★★★               │  ★★★★                 │
└────────────────────────────────────────────────────────────────┘
```

### Day 6 练习

1. 为知识库 Agent 添加一个 `summarize` 节点——当对话超过 10 条消息时自动生成摘要
2. 给 Agent 添加人机交互——当路由到 `tools` 且工具是 `calculator` 时，先确认再执行
3. 用 `SqliteSaver` 替换 `MemorySaver`，实现持久化对话

<details>
<summary>参考答案</summary>

```python
"""Day 6 练习答案：摘要节点 + 工具审批 + SQLite 持久化"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.3,
)

# === 练习 1：摘要节点 ===

class SummaryState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    summarized: bool

def maybe_summarize(state: SummaryState) -> dict:
    """超过 10 条消息时生成摘要"""
    msgs = state["messages"]
    if len(msgs) <= 10:
        return {"summarized": False}

    # 生成摘要
    old_msgs = msgs[:-4]
    recent = msgs[-4:]
    dialog = "\n".join(
        f"{'用户' if isinstance(m, HumanMessage) else 'AI'}: {m.content[:50]}"
        for m in old_msgs
    )
    resp = llm.invoke(f"总结以下对话（100字以内）:\n{dialog}")

    # 重建消息列表
    new_msgs = [SystemMessage(content=f"之前对话摘要: {resp.content}")] + recent
    return {"messages": new_msgs, "summarized": True}

def chat_node(state: SummaryState) -> dict:
    resp = llm.invoke(state["messages"])
    return {"messages": [resp]}

builder = StateGraph(SummaryState)
builder.add_node("summarize", maybe_summarize)
builder.add_node("chat", chat_node)
builder.add_edge(START, "summarize")
builder.add_edge("summarize", "chat")
builder.add_edge("chat", END)

summary_graph = builder.compile(checkpointer=MemorySaver())

# 测试
config = {"configurable": {"thread_id": "summary_test"}}
for i in range(6):
    summary_graph.invoke(
        {"messages": [HumanMessage(content=f"消息 {i+1}")]}, config
    )
# 第 6 轮后有 12 条消息，下次会触发摘要
result = summary_graph.invoke(
    {"messages": [HumanMessage(content="触发摘要")]}, config
)
print(f"已摘要: {result.get('summarized', False)}")
print(f"消息数: {len(result['messages'])}")

# === 练习 2：工具审批 ===

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
    """搜索信息。"""
    return f"模拟搜索: {query}"

tools = [calculator, search_info]
tools_map = {t.name: t for t in tools}
llm_tools = llm.bind_tools(tools)

class ApproveState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    iterations: int
    final_answer: str

def agent_node(state: ApproveState) -> dict:
    resp = llm_tools.invoke(state["messages"])
    return {"messages": [resp], "iterations": state["iterations"] + 1}

def check_and_maybe_approve(state: ApproveState) -> dict:
    last = state["messages"][-1]
    if not hasattr(last, "tool_calls") or not last.tool_calls:
        return {"final_answer": last.content}

    # 检查是否包含 calculator（需要审批）
    has_calc = any(tc["name"] == "calculator" for tc in last.tool_calls)
    if has_calc:
        human = interrupt({
            "prompt": "计算器工具需要确认",
            "tool_calls": last.tool_calls,
        })
        if not human.get("approved"):
            return {
                "messages": [ToolMessage(content="用户拒绝", tool_call_id=tc["id"])]
                for tc in last.tool_calls
            }

    # 执行工具
    results = []
    for tc in last.tool_calls:
        func = tools_map.get(tc["name"])
        r = func.invoke(tc["args"]) if func else "未知"
        results.append(ToolMessage(content=str(r), tool_call_id=tc["id"]))
    return {"messages": results}

def should_continue(state: ApproveState) -> str:
    if state["iterations"] >= 5:
        return END
    if state.get("final_answer"):
        return END
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "check"
    return END

builder = StateGraph(ApproveState)
builder.add_node("agent", agent_node)
builder.add_node("check", check_and_maybe_approve)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", should_continue, {"check": "check", END: END})
builder.add_edge("check", "agent")

approve_graph = builder.compile(checkpointer=MemorySaver())

# 测试
config2 = {"configurable": {"thread_id": "approve_test"}}
result = approve_graph.invoke({
    "messages": [HumanMessage(content="计算 123*456")],
    "iterations": 0, "final_answer": "",
}, config2)
# 会中断等待审批
print("等待审批...")
result = approve_graph.invoke(Command(resume={"approved": True}), config2)
print(f"结果: {result.get('final_answer', '完成')[:60]}")

# === 练习 3：SQLite 持久化 ===

print("\n=== 练习 3: SQLite 持久化 ===")
db_path = "./kb_agent_sqlite.db"

class SimpleChatState(TypedDict):
    messages: Annotated[list[AnyMessage], add]

def simple_chat(state: SimpleChatState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

chat_builder = StateGraph(SimpleChatState)
chat_builder.add_node("chat", simple_chat)
chat_builder.add_edge(START, "chat")
chat_builder.add_edge("chat", END)

with SqliteSaver.from_conn_string(db_path) as checkpointer:
    sqlite_graph = chat_builder.compile(checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": "sqlite_chat"}}

    # 第一轮
    r = sqlite_graph.invoke(
        {"messages": [HumanMessage(content="记住：我在学 LangGraph")]}, cfg
    )
    print(f"AI: {r['messages'][-1].content[:60]}...")

    # 第二轮（验证持久化）
    r = sqlite_graph.invoke(
        {"messages": [HumanMessage(content="我在学什么？")]}, cfg
    )
    print(f"AI: {r['messages'][-1].content[:60]}...")

print(f"检查点已保存到 {db_path}")
```

</details>

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

```
LangGraph 基础：
[ ] 理解 State / Node / Edge / Graph 四大核心概念
[ ] 能定义 TypedDict State 并使用 Annotated + add reducer
[ ] 能用 StateGraph 构建简单线性图
[ ] 能用 invoke 和 stream 运行图

条件路由与循环：
[ ] 能用 add_conditional_edges 实现条件分支
[ ] 能用条件边 + 回边构建循环（ReAct 模式）
[ ] 能设置循环终止条件（迭代次数 / 无工具调用）
[ ] 理解路由函数的返回值如何映射到目标节点

并行执行与子图：
[ ] 能用多边扇出实现并行执行
[ ] 能用多边扇入实现结果合并
[ ] 能定义子图并嵌入父图
[ ] 理解子图状态与父图状态的关系

人机交互：
[ ] 理解 interrupt() 和 Command(resume=...) 的机制
[ ] 能用 checkpointer + thread_id 管理中断/恢复
[ ] 能实现审批模式（approve / reject / edit）
[ ] 能实现危险工具调用前的人类确认

状态持久化：
[ ] 能用 MemorySaver 实现内存持久化
[ ] 能用 SqliteSaver 实现文件持久化
[ ] 理解 thread_id 的作用和会话隔离
[ ] 能查看 checkpoint 历史和状态回溯

综合实战：
[ ] 能用 LangGraph 构建带 RAG + 工具 + 记忆的完整 Agent
[ ] 能对比 LangChain AgentExecutor 和 LangGraph 的优劣
[ ] 能根据场景选择合适的框架
```

### 7.2 综合练习题

**项目：智能客服 Agent（LangGraph 版）**

用 LangGraph 构建一个智能客服 Agent，功能要求：

1. **意图识别**：判断用户意图（咨询/投诉/技术支持/闲聊）
2. **RAG 检索**：对咨询和技术支持类问题检索知识库
3. **工具调用**：支持查询订单状态、计算退款金额等工具
4. **人机交互**：投诉类问题需要人工审核后再回复
5. **对话记忆**：用 SQLite 持久化，重启可恢复

技术要求：
- 使用 StateGraph 构建图
- 使用条件路由实现意图分流
- 使用 interrupt 实现投诉审核
- 使用 SqliteSaver 实现持久化
- 使用并行执行同时检索多个知识源

> 完成这个项目后，你就掌握了 LangGraph 的核心能力，可以应对生产级 Agent 的复杂工作流需求。

<details>
<summary>参考答案框架</summary>

```python
"""智能客服 Agent（LangGraph 版）- 答案框架"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt, Command
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.3,
)

# === State ===
class CustomerServiceState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    intent: str          # inquiry / complaint / tech / chat
    rag_context: str
    needs_human: bool
    final_answer: str

# === 意图识别节点 ===
def classify_intent(state: CustomerServiceState) -> dict:
    last = state["messages"][-1].content
    resp = llm.invoke(
        f"判断用户意图，只回答一个词:\n"
        f"inquiry（咨询）/ complaint（投诉）/ tech（技术支持）/ chat（闲聊）\n"
        f"用户: {last}"
    )
    intent = resp.content.strip().lower()
    for valid in ["inquiry", "complaint", "tech", "chat"]:
        if valid in intent:
            return {"intent": valid}
    return {"intent": "chat"}

# === RAG 检索节点 ===
def rag_retrieve(state: CustomerServiceState) -> dict:
    # 这里接入知识库检索
    question = state["messages"][-1].content
    # vectorstore.similarity_search(question, k=3)
    return {"rag_context": f"模拟检索结果 for: {question}"}

# === RAG 生成节点 ===
def rag_generate(state: CustomerServiceState) -> dict:
    context = state.get("rag_context", "")
    question = state["messages"][-1].content
    resp = llm.invoke(f"根据以下信息回答:\n{context}\n问题: {question}")
    return {"final_answer": resp.content}

# === 投诉处理节点（需人机交互） ===
def handle_complaint(state: CustomerServiceState) -> dict:
    complaint = state["messages"][-1].content
    human = interrupt({
        "prompt": "收到投诉，需要人工审核",
        "complaint": complaint,
    })
    return {"final_answer": human.get("response", "您的投诉已收到，我们会尽快处理。")}

# === 工具节点 ===
@tool
def check_order(order_id: str) -> str:
    """查询订单状态。"""
    return f"订单 {order_id}: 已发货"

@tool
def calc_refund(amount: str) -> str:
    """计算退款金额。"""
    try:
        amt = float(amount)
        return f"退款金额: {amt * 0.9:.2f}（扣除10%手续费）"
    except ValueError:
        return "金额格式错误"

tools = [check_order, calc_refund]
tools_map = {t.name: t for t in tools}
llm_tools = llm.bind_tools(tools)

def tech_support_node(state: CustomerServiceState) -> dict:
    resp = llm_tools.invoke(state["messages"])
    if hasattr(resp, "tool_calls") and resp.tool_calls:
        results = []
        for tc in resp.tool_calls:
            func = tools_map.get(tc["name"])
            r = func.invoke(tc["args"]) if func else "未知工具"
            results.append(ToolMessage(content=str(r), tool_call_id=tc["id"]))
        final = llm.invoke(state["messages"] + [resp] + results)
        return {"messages": [resp] + results, "final_answer": final.content}
    return {"final_answer": resp.content}

# === 闲聊节点 ===
def chat_node(state: CustomerServiceState) -> dict:
    resp = llm.invoke(state["messages"])
    return {"final_answer": resp.content}

# === 响应节点 ===
def respond(state: CustomerServiceState) -> dict:
    return {"messages": [AIMessage(content=state["final_answer"])]}

# === 路由 ===
def route_intent(state: CustomerServiceState) -> str:
    return state.get("intent", "chat")

# === 构建图 ===
builder = StateGraph(CustomerServiceState)
builder.add_node("classify", classify_intent)
builder.add_node("rag_retrieve", rag_retrieve)
builder.add_node("rag_generate", rag_generate)
builder.add_node("complaint", handle_complaint)
builder.add_node("tech", tech_support_node)
builder.add_node("chat", chat_node)
builder.add_node("respond", respond)

builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route_intent, {
    "inquiry": "rag_retrieve",
    "complaint": "complaint",
    "tech": "tech",
    "chat": "chat",
})
builder.add_edge("rag_retrieve", "rag_generate")
builder.add_edge("rag_generate", "respond")
builder.add_edge("complaint", "respond")
builder.add_edge("tech", "respond")
builder.add_edge("chat", "respond")
builder.add_edge("respond", END)

# === 编译 + 运行 ===
db_path = "./customer_service.db"
with SqliteSaver.from_conn_string(db_path) as checkpointer:
    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "customer_001"}}

    # 测试咨询
    r = graph.invoke({"messages": [HumanMessage(content="你们的退款政策是什么？")],
                      "intent": "", "rag_context": "", "needs_human": False,
                      "final_answer": ""}, config)
    print(f"咨询: {r['final_answer'][:60]}...")

    # 测试投诉（会中断）
    r = graph.invoke({"messages": [HumanMessage(content="我要投诉，服务太差了！")],
                      "intent": "", "rag_context": "", "needs_human": False,
                      "final_answer": ""}, config)
    print("投诉等待审核...")
    r = graph.invoke(Command(resume={"response": "非常抱歉，已为您加急处理。"}), config)
    print(f"回复: {r['final_answer'][:60]}...")
```

</details>

### 7.3 Week 6 回顾与 Week 7 预告

```
Week 6 学习路径回顾：

Day 1: LangGraph 全景 + 基础概念
  → State / Node / Edge / Graph、Reducer、第一个图

Day 2: 条件路由 + 循环
  → add_conditional_edges、ReAct 循环、循环终止

Day 3: 并行执行 + 子图
  → Fan-out/Fan-in、子图复用、模块化设计

Day 4: 人机交互（HITL）
  → interrupt / Command(resume)、审批模式、危险工具确认

Day 5: State 管理 + 持久化
  → MemorySaver / SqliteSaver、多会话、状态回溯

Day 6: 综合实战
  → 用 LangGraph 构建知识库 Agent、对比 AgentExecutor

你已经掌握的能力：
✓ 用 StateGraph 构建有状态的图工作流
✓ 用条件路由实现动态分支
✓ 用循环实现 ReAct Agent
✓ 用并行执行提升效率
✓ 用子图实现模块复用
✓ 用 interrupt 实现人机交互
✓ 用 Checkpointer 实现状态持久化
✓ 根据场景选择 LangChain 或 LangGraph

接下来（Week 7 预告）：
Week 7: Multi-Agent 系统
  → 多 Agent 协作模式
  → Supervisor / Swarm / Hierarchical
  → Agent 间通信与任务分配
  → LangGraph Multi-Agent 实战
```

---

## 本周知识图谱

```
LangGraph + 状态机 Agent
├── 基础概念（Day 1）
│   ├── State（TypedDict + Annotated）
│   ├── Node（函数：state → state update）
│   ├── Edge（普通边 + 条件边）
│   ├── Graph（StateGraph + compile）
│   └── Reducer（add / 自定义合并）

├── 条件路由与循环（Day 2）
│   ├── add_conditional_edges
│   ├── 路由函数（state → node name）
│   ├── 循环（条件边 + 回边）
│   ├── ReAct Agent 实现
│   └── 循环终止条件

├── 并行执行与子图（Day 3）
│   ├── Fan-out（多边扇出）
│   ├── Fan-in（多边扇入）
│   ├── 子图定义与编译
│   └── 子图嵌入父图

├── 人机交互（Day 4）
│   ├── interrupt() 中断
│   ├── Command(resume=) 恢复
│   ├── Checkpointer + thread_id
│   ├── 审批模式（approve/reject/edit）
│   └── 危险工具确认

├── 状态持久化（Day 5）
│   ├── MemorySaver（内存）
│   ├── SqliteSaver（文件）
│   ├── 多会话隔离
│   ├── Checkpoint 历史
│   └── 状态回溯与重放

└── 综合实战（Day 6）
    ├── 知识库 Agent（LangGraph 版）
    ├── 意图路由 + RAG + 工具 + 记忆
    ├── 流式输出集成
    └── LangChain vs LangGraph 对比
```

## LangGraph 速查表

```
┌──────────────────────────────────────────────────────────┐
│               LangGraph 常用代码速查                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  定义 State：                                            │
│  class State(TypedDict):                                 │
│      messages: Annotated[list, add]                      │
│      count: int                                          │
│                                                          │
│  定义节点：                                              │
│  def my_node(state: State) -> dict:                      │
│      return {"count": state["count"] + 1}                │
│                                                          │
│  构建图：                                                │
│  builder = StateGraph(State)                             │
│  builder.add_node("a", node_a)                           │
│  builder.add_node("b", node_b)                           │
│  builder.add_edge(START, "a")                            │
│  builder.add_edge("a", "b")                              │
│  builder.add_edge("b", END)                              │
│                                                          │
│  条件路由：                                              │
│  builder.add_conditional_edges(                          │
│      "a", router_fn,                                     │
│      {"b": "b", "c": "c"}                                │
│  )                                                       │
│                                                          │
│  循环：                                                  │
│  builder.add_edge("tools", "agent")  # 回边              │
│                                                          │
│  并行：                                                  │
│  builder.add_edge(START, "a")  # 同时                    │
│  builder.add_edge(START, "b")  # 并行                    │
│                                                          │
│  编译 + 持久化：                                         │
│  graph = builder.compile(checkpointer=MemorySaver())    │
│                                                          │
│  运行：                                                  │
│  config = {"configurable": {"thread_id": "t1"}}         │
│  graph.invoke(state, config)                             │
│  graph.stream(state, config)                             │
│                                                          │
│  人机交互：                                              │
│  human = interrupt({"prompt": "确认?"})                  │
│  graph.invoke(Command(resume={"approved": True}), cfg)  │
│                                                          │
│  查看状态：                                              │
│  graph.get_state(config)                                 │
│  graph.get_state_history(config)                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
