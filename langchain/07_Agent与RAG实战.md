# Day 7:Agents 与 Tools、完整 RAG 项目实战

> 今日主题:Agent(代理)与 Tool(工具)、完整 RAG 项目实战
> 预计学习时长:3 小时
> 前置条件:已完成 Day 1-6,掌握 LCEL、RAG 基础流程

---

## 一、当日目标

1. 理解 Agent 的概念,知道它和普通 Chain 的区别
2. 掌握 Tool 的定义方式,能创建自定义工具
3. 学会使用 `create_tool_calling_agent` 创建 Agent
4. 完成一个完整的本地 RAG 知识库问答系统项目

---

## 二、核心概念讲解

### 2.1 什么是 Agent

**Chain(链)**:流程是固定的,你预先定义好 `prompt | model | parser` 的执行顺序。

**Agent(代理)**:流程是**动态的**,LLM 自主决定:
- 调用哪些工具
- 按什么顺序调用
- 是否需要调用多次
- 何时给出最终答案

举例:
```
用户: "今天北京天气怎么样?然后帮我算一下 23 * 45"

Agent 思考:
  1. 需要先查天气 -> 调用 weather_tool("北京")
  2. 需要算乘法 -> 调用 calculator_tool("23 * 45")
  3. 综合两个结果 -> 生成最终答案
```

Agent 适合需要**多步推理**或**动态决策**的场景。

### 2.2 LangChain v0.3 中的 Agent

LangChain v0.3 推荐的 Agent 创建方式:

| 方式 | 说明 |
|------|------|
| `create_tool_calling_agent` | 通用方式,支持能做 tool calling 的模型(GPT-4o、Claude 等) |
| `create_react_agent` | ReAct 模式,用 Prompt 引导推理 |
| LangGraph Agent | 最新的状态机方式(进阶,本教程不深入) |

本教程使用 `create_tool_calling_agent`,这是最通用的方式。

### 2.3 Tool(工具)

Tool 是 Agent 可以调用的函数。定义 Tool 的方式:

**方式一:`@tool` 装饰器(推荐)**

```python
from langchain_core.tools import tool

@tool
def search_weather(city: str) -> str:
    """查询指定城市的天气"""
    # 实际调用天气 API
    return f"{city} 今天晴,25度"
```

**关键点**:
- 函数的**类型注解**和**docstring**非常重要,LLM 会根据它们决定是否调用
- docstring 描述要清晰,告诉 LLM 这个工具做什么、什么时候用

**方式二:`StructuredTool`**

```python
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str
    max_results: int = 5

def search_func(query: str, max_results: int = 5) -> str:
    return f"搜索 {query},返回 {max_results} 条结果"

search_tool = StructuredTool.from_function(
    func=search_func,
    name="search",
    description="搜索网络信息",
    args_schema=SearchInput,
)
```

### 2.4 Agent 执行流程

```
1. 用户提问
2. LLM 分析问题,决定是否需要调用工具
3. 如果需要,LLM 输出工具调用请求(工具名 + 参数)
4. LangChain 执行工具,把结果返回给 LLM
5. LLM 根据工具结果,决定是否继续调用工具或给出最终答案
6. 重复 3-5 直到 LLM 给出最终答案
```

### 2.5 AgentExecutor

`AgentExecutor` 是 Agent 的运行环境,负责循环执行上述流程:

```python
from langchain.agents import AgentExecutor

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = agent_executor.invoke({"input": "你的问题"})
```

`verbose=True` 会打印 Agent 的思考过程,方便调试。

### 2.6 RAG + Agent 结合

Agent 可以把 RAG 检索器作为一个工具:

```python
@tool
def knowledge_search(query: str) -> str:
    """从本地知识库搜索相关信息"""
    docs = retriever.invoke(query)
    return "\n\n".join(doc.page_content for doc in docs)
```

这样 Agent 可以自主决定:什么时候检索知识库,什么时候用其他工具。

---

## 三、代码示例

### 3.1 安装依赖

```bash
pip install langchain langchain-community langchain-openai langchain-chroma
pip install chromadb pypdf
```

### 3.2 创建自定义工具

```python
"""
Day7 示例 1:用 @tool 装饰器创建自定义工具
"""
from langchain_core.tools import tool
import datetime

@tool
def get_current_time() -> str:
    """获取当前日期和时间。当用户问到现在几点、今天日期时使用此工具。"""
    now = datetime.datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。当需要数学计算时使用此工具。
    参数 expression: 数学表达式字符串,如 "23 * 45" 或 "100 / 4"
    """
    try:
        # 安全地计算表达式(只允许数字和运算符)
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "错误:表达式包含非法字符"
        result = eval(expression)  # 注意:生产环境应使用更安全的计算方式
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "错误:除以零"
    except SyntaxError:
        return f"错误:表达式语法不正确: {expression}"
    except Exception as e:
        return f"错误: {type(e).__name__}: {e}"

@tool
def search_knowledge(query: str) -> str:
    """搜索本地知识库。当用户询问 LangChain、RAG、LLM 相关技术问题时使用此工具。
    参数 query: 搜索关键词
    """
    # 模拟知识库
    knowledge = {
        "langchain": "LangChain 是一个用于构建 LLM 应用的开源框架,提供模型接口、Prompt、链、检索器等组件。",
        "rag": "RAG(检索增强生成)是结合检索和生成的技术,从知识库检索相关文档,作为上下文传给 LLM 生成答案。",
        "agent": "Agent 是能自主调用工具的 LLM,根据用户需求动态决定调用哪些工具。",
        "lcel": "LCEL 是 LangChain 表达式语言,用管道符 | 连接组件,支持流式、批量、异步等特性。",
    }

    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower:
            return value
    return f"未找到关于'{query}'的信息。"

# 测试工具
print("=== 测试工具 ===")
print(get_current_time.invoke({}))
print(calculate.invoke({"expression": "23 * 45"}))
print(search_knowledge.invoke({"query": "什么是 RAG?"}))
```

### 3.3 创建并运行 Agent

```python
"""
Day7 示例 2:创建 Tool Calling Agent
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import tool
import datetime

# 工具定义
@tool
def get_current_time() -> str:
    """获取当前日期和时间。当用户问到现在几点、今天日期时使用。"""
    now = datetime.datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。参数 expression: 如 "23 * 45" 或 "100 / 4" """
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误:表达式包含非法字符"
        result = eval(expression)
        return f"{expression} = {result}"
    except ZeroDivisionError:
        return "错误:除以零"
    except SyntaxError:
        return f"错误:语法不正确: {expression}"

@tool
def search_knowledge(query: str) -> str:
    """搜索本地知识库。当用户询问 LangChain、RAG、Agent 等技术问题时使用。"""
    knowledge = {
        "langchain": "LangChain 是构建 LLM 应用的开源框架,核心组件包括模型接口、Prompt、链、检索器。",
        "rag": "RAG 是检索增强生成技术,从知识库检索文档作为上下文传给 LLM。",
        "agent": "Agent 是能自主调用工具的 LLM。",
        "lcel": "LCEL 是 LangChain 表达式语言,用管道符连接组件。",
    }
    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower:
            return value
    return f"未找到关于'{query}'的信息。"

tools = [get_current_time, calculate, search_knowledge]

# 初始化模型
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Agent 的 Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手,可以调用工具来回答问题。请根据用户问题决定是否使用工具。"),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),  # Agent 思考过程
])

# 创建 Agent
agent = create_tool_calling_agent(model, tools, prompt)

# 创建执行器
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 测试
print("=== 测试 1:需要计算 ===")
result = agent_executor.invoke({"input": "帮我算一下 123 * 456"})
print(f"\n最终答案: {result['output']}")

print("\n=== 测试 2:需要查时间 ===")
result = agent_executor.invoke({"input": "现在几点了?"})
print(f"\n最终答案: {result['output']}")

print("\n=== 测试 3:需要查知识 ===")
result = agent_executor.invoke({"input": "什么是 LCEL?"})
print(f"\n最终答案: {result['output']}")

print("\n=== 测试 4:多工具组合 ===")
result = agent_executor.invoke({"input": "现在几点?另外帮我算 100 / 4"})
print(f"\n最终答案: {result['output']}")
```

### 3.4 完整 RAG 项目实战

下面是今天的重头戏:一个完整的本地 RAG 知识库问答系统。

```python
"""
Day7 示例 3:完整 RAG 知识库问答系统

功能:
1. 加载本地文档(TXT/Markdown)
2. 切分并嵌入到 Chroma 向量库
3. 构建 RAG 问答链
4. 支持多轮对话(带历史记忆)
5. 可选:用 Agent 让模型自主决定是否检索
"""

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser


class RAGChatbot:
    """完整的 RAG 知识库问答机器人"""

    def __init__(
        self,
        persist_dir: str = "./rag_chroma_db",
        model_name: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 300,
        chunk_overlap: int = 50,
    ):
        self.persist_dir = persist_dir
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.model = ChatOpenAI(model=model_name, temperature=0)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", " ", ""],
        )
        self.vectorstore = None
        self.retriever = None
        self.history: list = []

        # 问答 Prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个知识库问答助手。请根据以下上下文回答用户问题。

规则:
1. 只根据上下文回答,不要编造信息
2. 如果上下文没有相关信息,说"根据知识库,我无法回答这个问题"
3. 回答要简洁准确

上下文:
{context}"""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])

    def ingest_document(self, filepath: str) -> int:
        """加载并索引一个文档文件"""
        loader = TextLoader(filepath, encoding="utf-8")
        docs = loader.load()
        chunks = self.splitter.split_documents(docs)

        # 如果向量库已存在,加载它;否则创建新的
        if os.path.exists(self.persist_dir):
            self.vectorstore = Chroma(
                persist_directory=self.persist_dir,
                embedding_function=self.embeddings,
            )
            self.vectorstore.add_documents(chunks)
        else:
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_dir,
            )

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        print(f"已索引 {filepath}: {len(chunks)} 个片段")
        return len(chunks)

    def ingest_text(self, text: str, source: str = "user_input") -> int:
        """直接索引一段文本"""
        from langchain_core.documents import Document
        doc = Document(page_content=text, metadata={"source": source})
        chunks = self.splitter.split_documents([doc])

        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_dir,
            )
        else:
            self.vectorstore.add_documents(chunks)

        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        print(f"已索引文本: {len(chunks)} 个片段")
        return len(chunks)

    def _format_docs(self, docs) -> str:
        """格式化文档列表为字符串"""
        return "\n\n".join(doc.page_content for doc in docs)

    def ask(self, question: str) -> str:
        """提问并获取答案(带历史记忆)"""
        if self.retriever is None:
            return "知识库为空,请先添加文档。"

        # 检索相关文档
        docs = self.retriever.invoke(question)
        context = self._format_docs(docs)

        # 调用模型
        chain = self.prompt | self.model | StrOutputParser()
        answer = chain.invoke({
            "context": context,
            "history": self.history,
            "question": question,
        })

        # 更新历史
        self.history.append(HumanMessage(content=question))
        self.history.append(AIMessage(content=answer))

        return answer

    def clear_history(self):
        """清空对话历史"""
        self.history = []
        print("[系统] 对话历史已清空")


# ===================== 使用示例 =====================

def demo():
    """演示 RAG 问答系统"""

    # 准备知识库内容
    knowledge_base = """
    **华为 HarmonyOS 简介**

    HarmonyOS(鸿蒙操作系统)是华为开发的分布式操作系统,于 2019 年首次发布。
    它采用分布式架构,支持手机、平板、智能穿戴、车机等多种设备的协同工作。

    HarmonyOS 的核心特性包括:分布式软总线、分布式数据管理、分布式任务调度。
    这些特性让多设备之间能无缝协同,提供一致的用户体验。

    **ArkTS 开发语言**

    ArkTS 是 HarmonyOS 应用开发的主力语言,基于 TypeScript 扩展。
    它在 TypeScript 基础上增加了声明式 UI 语法和状态管理能力。
    ArkTS 代码以 .ets 为文件扩展名。

    ArkTS 的声明式 UI 使用 @Component、@Entry、@State 等装饰器。
    开发者通过链式调用的方式描述 UI 结构,如 Column().child(Text('Hello'))。

    **ArkUI 框架**

    ArkUI 是 HarmonyOS 的 UI 开发框架,支持声明式和命令式两种开发范式。
    声明式范式基于 ArkTS,是官方推荐的开发方式。
    ArkUI 提供了丰富的内置组件,如 Text、Button、Image、List 等。

    ArkUI 的布局组件包括 Column(纵向)、Row(横向)、Flex(弹性)、Grid(网格)等。
    开发者可以通过这些组件组合出复杂的界面布局。

    **Stage 模型**

    Stage 模型是 HarmonyOS 3.1 开始引入的应用开发模型,取代了早期的 FA 模型。
    Stage 模型以 UIAbility 为核心,提供了更好的生命周期管理和组件化能力。
    每个 Ability 对应一个用户交互场景,如一个页面或一项功能。

    Stage 模型中,应用由一个或多个 Module 组成,每个 Module 包含 Ability 和页面。
    Module 分为 Entry 类型和 Feature 类型,Entry 是主入口,Feature 是功能模块。
    """

    # 创建 RAG 机器人
    bot = RAGChatbot(persist_dir="./harmony_kb")

    # 索引知识
    print("=== 步骤1:构建知识库 ===")
    bot.ingest_text(knowledge_base, source="harmonyos_doc")

    # 问答测试
    print("\n=== 步骤2:问答测试 ===")
    questions = [
        "HarmonyOS 是什么?",
        "ArkTS 和 TypeScript 有什么关系?",
        "ArkUI 有哪些布局组件?",
        "Stage 模型中的 Module 有哪几种类型?",
        "今天天气怎么样?",  # 知识库中没有的问题
    ]

    for q in questions:
        print(f"\n问: {q}")
        print(f"答: {bot.ask(q)}")

    # 测试多轮对话记忆
    print("\n=== 步骤3:多轮对话记忆测试 ===")
    bot.clear_history()
    print(f"问: ArkTS 的文件扩展名是什么?")
    print(f"答: {bot.ask('ArkTS 的文件扩展名是什么?')}")
    print(f"问: 你刚才说的扩展名能再重复一遍吗?")  # 测试是否记得上一轮
    print(f"答: {bot.ask('你刚才说的扩展名能再重复一遍吗?')}")


if __name__ == "__main__":
    demo()
```

### 3.5 RAG + Agent 结合版

```python
"""
Day7 示例 4:RAG + Agent - 让模型自主决定是否检索
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
import datetime

# 嵌入和模型
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 假设已有向量库(复用示例3的数据)
knowledge_base = """
HarmonyOS 是华为开发的分布式操作系统,支持多设备协同。
ArkTS 是 HarmonyOS 开发语言,基于 TypeScript 扩展。
ArkUI 是 UI 框架,支持声明式开发范式。
Stage 模型以 UIAbility 为核心,提供生命周期管理。
"""

vectorstore = Chroma.from_texts(
    texts=[knowledge_base],
    embedding=embeddings,
    collection_name="harmony_agent_kb",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 定义工具
@tool
def search_knowledge_base(query: str) -> str:
    """搜索 HarmonyOS 技术知识库。当用户询问 HarmonyOS、ArkTS、ArkUI、Stage 模型等技术问题时使用此工具。
    参数 query: 搜索关键词
    """
    docs = retriever.invoke(query)
    return "\n\n".join(doc.page_content for doc in docs)

@tool
def get_current_time() -> str:
    """获取当前时间。当用户询问时间、日期时使用。"""
    return datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。参数 expression: 如 "12 * 34" """
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误:非法字符"
        return str(eval(expression))
    except ZeroDivisionError:
        return "错误:除以零"
    except SyntaxError:
        return f"错误:语法错误"

tools = [search_knowledge_base, get_current_time, calculate]

# 创建 Agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手。你可以使用工具来回答问题。对于技术问题,请使用知识库搜索工具。"),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 测试:Agent 会自主决定用哪个工具
print("=== 测试 1:技术问题(应该用知识库) ===")
result = agent_executor.invoke({"input": "ArkTS 是什么?"})
print(f"答案: {result['output']}")

print("\n=== 测试 2:计算问题(应该用计算器) ===")
result = agent_executor.invoke({"input": "帮我算 56 * 78"})
print(f"答案: {result['output']}")

print("\n=== 测试 3:时间问题(应该用时间工具) ===")
result = agent_executor.invoke({"input": "现在几点?"})
print(f"答案: {result['output']}")

print("\n=== 测试 4:闲聊(不需要工具) ===")
result = agent_executor.invoke({"input": "你好,你是谁?"})
print(f"答案: {result['output']}")

print("\n=== 测试 5:复合问题(多个工具) ===")
result = agent_executor.invoke({"input": "HarmonyOS 是什么?另外帮我算 100 + 200"})
print(f"答案: {result['output']}")
```

---

## 四、当日小结

| 要点 | 内容 |
|------|------|
| Agent vs Chain | Chain 流程固定,Agent 流程动态(LLM 自主决策) |
| Tool 定义 | 用 `@tool` 装饰器,类型注解和 docstring 是关键 |
| create_tool_calling_agent | v0.3 推荐的 Agent 创建方式 |
| AgentExecutor | Agent 运行环境,循环执行"思考-调用工具-观察"流程 |
| RAG + Agent | 把检索器封装成 Tool,让 Agent 自主决定是否检索 |
| 完整 RAG 系统 | 加载 -> 切分 -> 嵌入 -> 存储 -> 检索 -> 生成 |
| 多轮对话 | 用 `MessagesPlaceholder` + history 列表管理历史 |

### 7 天知识体系总览

```
Day 1: 基础入门     -> ChatOpenAI、消息类型、PromptTemplate
Day 2: 输出解析     -> Output Parsers、MessagesPlaceholder、LCEL 入门
Day 3: LCEL 深入    -> Runnable 接口、RunnablePassthrough/Lambda/Parallel
Day 4: Memory       -> 手动管理历史、Window/Summary 策略、持久化
Day 5: 文档处理     -> Document Loaders、Text Splitters、Embeddings
Day 6: 向量检索     -> Chroma、Retriever、MMR、RAG 问答链
Day 7: Agent 实战   -> Tools、Agent、完整 RAG 项目
```

---

## 五、练习题

### 选择题

**1. Agent 和 Chain 的核心区别是?**
A. Agent 速度更快
B. Chain 流程固定,Agent 流程由 LLM 动态决策
C. Agent 不需要 LLM
D. Chain 不支持工具

**2. 用 `@tool` 装饰器定义工具时,以下哪个最重要?**
A. 函数名的长度
B. 函数的类型注解和 docstring(LLM 据此决定是否调用)
C. 函数的返回值类型
D. 函数的参数个数

**3. `create_tool_calling_agent` 需要哪些参数?**
A. 只有 model
B. model 和 tools
C. model、tools 和 prompt
D. model、tools、prompt 和 AgentExecutor

**4. RAG + Agent 结合的好处是?**
A. 速度更快
B. 让 LLM 自主决定是否需要检索知识库,避免不必要的检索
C. 不需要向量数据库
D. 不需要 Prompt

### 填空题

**5.** Agent 的运行环境类叫 `______`,它负责循环执行"思考-调用工具-观察"流程。

**6.** 在 Agent 的 Prompt 中,`MessagesPlaceholder(variable_name="______")` 用于存储 Agent 的中间思考过程和工具调用记录。

### 编程题

**7.** 创建一个 Agent,包含以下工具:
- `get_word_count(text)`: 统计文本字数
- `reverse_string(text)`: 反转字符串
- `search_knowledge(query)`: 模拟知识库搜索(返回一段固定文本)
让 Agent 处理用户请求:"帮我统计'Hello World'有多少个字符,然后把它反转,再搜索一下 Python 的知识"。打印 Agent 的执行过程和最终答案。

**8.** (实战项目)基于 Day7 示例 3 的 `RAGChatbot` 类,构建一个你自己的知识库问答系统:
- 准备 3 段以上关于你感兴趣主题的文本(如 AI、编程、音乐等)
- 用 `ingest_text` 方法索引到向量库
- 进行至少 5 轮问答,包括:3 个知识库中有的问题、1 个知识库中没有的问题、1 个追问(测试记忆)
- 打印所有问答结果

---

## 六、练习题答案

### 1. 答案:B
**解析**:Chain 的执行流程是预先定义好的(如 `prompt | model | parser`),每次都按固定顺序执行。Agent 的流程是动态的,由 LLM 根据用户输入自主决定调用哪些工具、调用几次、何时给出最终答案。

### 2. 答案:B
**解析**:LLM 通过函数的类型注解(参数名和类型)和 docstring(描述工具功能和适用场景)来理解工具的用途,并决定是否调用。docstring 写得越清晰,Agent 越能正确使用工具。

### 3. 答案:C
**解析**:`create_tool_calling_agent(model, tools, prompt)` 需要三个参数:模型、工具列表和 Prompt 模板。Prompt 中必须包含 `agent_scratchpad` 占位符。

### 4. 答案:B
**解析**:把 RAG 检索封装成 Tool,Agent 可以根据问题性质自主决定是否检索。对于闲聊或简单问题不需要检索,对于知识性问题才检索,提高效率和准确性。

### 5. 答案:`AgentExecutor`
**解析**:`AgentExecutor(agent=agent, tools=tools)` 是 Agent 的运行环境,负责循环执行 Agent 的推理和工具调用流程,直到给出最终答案。

### 6. 答案:`agent_scratchpad`
**解析**:`agent_scratchpad` 是 Agent Prompt 中的特殊占位符,用于存储 Agent 的中间思考过程(包括工具调用请求和工具返回结果),让 LLM 能看到自己之前的操作。

### 7. 参考答案:

```python
"""
练习题 7:多工具 Agent
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

@tool
def get_word_count(text: str) -> str:
    """统计文本的字符数(不含空格)。当用户需要统计字数时使用。
    参数 text: 要统计的文本
    """
    count = len(text.replace(" ", ""))
    return f"'{text}' 的字符数(不含空格)为: {count}"

@tool
def reverse_string(text: str) -> str:
    """反转字符串。当用户需要反转文本时使用。
    参数 text: 要反转的文本
    """
    return f"'{text}' 反转后为: '{text[::-1]}'"

@tool
def search_knowledge(query: str) -> str:
    """搜索知识库。当用户需要查询技术知识时使用。
    参数 query: 搜索关键词
    """
    knowledge = "Python 是一种高级编程语言,以简洁易读著称,广泛用于 Web 开发、数据科学、AI 等领域。"
    return f"知识库搜索结果: {knowledge}"

tools = [get_word_count, reverse_string, search_knowledge]

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个智能助手,可以调用多个工具来完成任务。"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = agent_executor.invoke({
    "input": "帮我统计'Hello World'有多少个字符,然后把它反转,再搜索一下 Python 的知识"
})
print(f"\n最终答案: {result['output']}")
```

### 8. 参考答案:

```python
"""
练习题 8:自定义知识库问答系统
"""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

# 准备知识库内容(主题:人工智能)
ai_knowledge = """
**机器学习基础**

机器学习是人工智能的一个分支,让计算机从数据中学习规律,而不需要显式编程。
主要分为监督学习、无监督学习和强化学习三大类。
监督学习使用标注数据训练,无监督学习发现数据结构,强化学习通过试错学习。

**深度学习**

深度学习是机器学习的子领域,使用多层神经网络。
深度学习在图像识别、自然语言处理、语音识别等领域取得了突破性进展。
著名的深度学习框架有 TensorFlow、PyTorch、MindSpore 等。

**大语言模型**

大语言模型(LLM)是基于 Transformer 架构的深度学习模型,通过预训练学习语言规律。
GPT、BERT、LLaMA 等都是著名的大语言模型。
LLM 通过预训练和微调两个阶段获得语言理解和生成能力。

**RAG 技术**

RAG(检索增强生成)是将检索和生成结合的技术。
它从外部知识库检索相关文档,作为上下文传给 LLM,增强回答的准确性。
RAG 能有效缓解 LLM 的知识过时和幻觉问题。
"""

# 初始化组件
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=30)

# 切分并存储
from langchain_core.documents import Document
doc = Document(page_content=ai_knowledge, metadata={"source": "ai_knowledge"})
chunks = splitter.split_documents([doc])
vectorstore = Chroma.from_documents(chunks, embeddings, collection_name="ai_kb")
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", """根据以下上下文回答问题。如果上下文没有相关信息,说"根据知识库无法回答"。

上下文:
{context}"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = prompt | model | StrOutputParser()
history = []

def ask(question: str) -> str:
    docs = retriever.invoke(question)
    context = "\n\n".join(d.page_content for d in docs)
    answer = chain.invoke({"context": context, "history": history, "question": question})
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))
    return answer

# 5 轮问答
questions = [
    "机器学习有哪几大类?",                    # 知识库有
    "深度学习在哪些领域有突破?",               # 知识库有
    "RAG 解决了什么问题?",                    # 知识库有
    "怎么做红烧肉?",                         # 知识库没有
    "你刚才说 RAG 解决了什么问题?能再说说吗?",  # 追问,测试记忆
]

for q in questions:
    print(f"问: {q}")
    print(f"答: {ask(q)}\n")
```

---

## 恭喜完成 7 天学习!

你已经完成了 LangChain 7 天学习计划的全部内容!回顾一下你的成就:

- **Day 1**:搭建环境,跑通第一个 LangChain 程序
- **Day 2**:掌握 Output Parsers,实现结构化输出
- **Day 3**:理解 LCEL 和 Runnable 接口,构建复杂链
- **Day 4**:掌握 Memory,实现带记忆的对话机器人
- **Day 5**:学会文档加载、切分和嵌入
- **Day 6**:掌握向量数据库和 RAG 问答链
- **Day 7**:理解 Agent,完成完整 RAG 项目实战

### 下一步建议

1. **深入学习 LangGraph**:LangChain 官方推荐用 LangGraph 构建复杂的多步 Agent 工作流,它基于状态机,比 AgentExecutor 更强大灵活
2. **接入真实数据源**:把 RAG 系统接入你的真实文档(华为内部 Wiki、技术文档等)
3. **尝试不同模型**:对比 OpenAI、通义千问、智谱等不同模型在 RAG 场景下的表现
4. **学习高级 RAG 技巧**:查询重写、重排序(reranking)、混合检索、多路召回等
5. **部署上线**:用 FastAPI 把你的 RAG 系统封装成 API 服务,或结合 HarmonyOS 开发一个 AI 助手 App

祝你在这条 AI 学习之路上越走越远!
