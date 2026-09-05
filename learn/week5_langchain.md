# 第2月第5周：LangChain 框架实战

> 适用对象：已完成 Week 1-4（Python基础 + LLM核心 + Prompt Engineering + RAG/Multi-Tool Agent）的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：掌握 LangChain 核心组件，能用 LangChain 重构 Week 4 的 RAG Agent，理解框架的设计哲学与适用场景

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month2/week5
cd month2/week5

python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 本周依赖
pip install langchain langchain-core langchain-community langchain-openai httpx pydantic chromadb pypdf
pip freeze > requirements.txt
```

**关于 LangChain 版本**：本教程基于 LangChain 0.3+（2024 年底大重构后的版本），核心包拆分为：
- `langchain-core`：基础抽象（BaseMessage、Runnable 等）
- `langchain-community`：第三方集成（Chroma、HuggingFace 等）
- `langchain-openai`：OpenAI 兼容模型集成
- `langchain`：高层链和 Agent 编排

**关于智谱 API**：LangChain 没有官方的智谱集成包，但智谱 API 兼容 OpenAI 格式，我们通过 `langchain-openai` 的 `ChatOpenAI` 配置 `base_url` 来使用。

---

## Day 1：LangChain 全景 + Model I/O

> LangChain 是目前最流行的 LLM 应用框架。今天先搞懂它的整体架构，然后从最基础的 Model I/O 开始。

### 1.1 LangChain 是什么？

```
┌────────────────── LangChain 全景 ──────────────────┐
│                                                     │
│  核心理念：组合（Composition）                        │
│  把 LLM 应用拆成可复用的组件，像搭积木一样组装        │
│                                                     │
│  六大组件：                                           │
│  1. Model I/O     ── 模型调用（输入/输出）            │
│  2. Retrieval     ── 检索（RAG 相关）                │
│  3. Chains        ── 链（组件串联）                   │
│  4. Agents        ── 智能体（动态决策）               │
│  5. Memory        ── 记忆（对话历史）                 │
│  6. Callbacks     ── 回调（日志/监控/流式）            │
│                                                     │
│  贯穿理念：                                          │
│  Runnable 协议 ── 所有组件都实现 invoke/ainvoke 等    │
│  LCEL（LangChain Expression Language）── 管道语法      │
│                                                     │
└─────────────────────────────────────────────────────┘

本周按天推进：
  Day 1: Model I/O（模型调用 + 提示词模板 + 输出解析）
  Day 2: LCEL 链式组合
  Day 3: RAG 检索链
  Day 4: Agent 与 Tool
  Day 5: Memory 对话记忆
  Day 6: Callbacks + 综合实战（用 LangChain 重构知识库 Agent）
  Day 7: 复习 + 总结 + 周测
```

### 1.2 为什么学 LangChain？

| 自己写（Week 1-4 方式） | LangChain 方式 |
|---|---|
| 手动拼接 prompt 字符串 | PromptTemplate 模板化 |
| 手动解析 JSON 输出 | OutputParser 自动解析 |
| 手动写 RAG 流程 | RetrievalChain 一键串联 |
| 手动实现 ReAct 循环 | create_react_agent 内置 |
| 手动管理对话历史 | Memory 组件自动管理 |
| 每个功能从头实现 | 社区集成开箱即用 |

**但也要注意**：LangChain 不是万能的——复杂场景下，自己写的 Agent 可能更灵活。学 LangChain 是为了理解框架设计思想，掌握标准范式，然后能根据场景选择"用框架"还是"自己写"。

### 1.3 连接智谱 GLM

创建文件 `day1_model_io.py`：

```python
"""
Day 1: LangChain Model I/O
- ChatOpenAI 连接智谱 GLM
- PromptTemplate 模板
- OutputParser 解析
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# === 1. 连接智谱 GLM（兼容 OpenAI 格式） ===

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.7,
    max_tokens=1024,
)

# 最简单的调用
response = llm.invoke("用一句话解释什么是 LangChain")
print(f"回答: {response.content}")
print(f"类型: {type(response)}")  # AIMessage
print(f"元数据: {response.response_metadata}")

# === 2. 使用消息列表调用 ===

messages = [
    SystemMessage(content="你是一个 Python 编程助手，回答简洁。"),
    HumanMessage(content="Python 的列表推导式是什么？给一个例子。"),
]

response = llm.invoke(messages)
print(f"\n回答: {response.content}")

# === 3. 流式输出 ===

print("\n--- 流式输出 ---")
for chunk in llm.stream("用三句话介绍 Python 的 asyncio"):
    print(chunk.content, end="", flush=True)
print()

# === 4. 批量调用 ===

print("\n--- 批量调用 ---")
batch_results = llm.batch([
    "1+1=?",
    "2+2=?",
    "3+3=?",
])
for i, result in enumerate(batch_results):
    print(f"  问题{i+1}: {result.content}")
```

运行前设置环境变量：

```bash
export ZHIPU_API_KEY="你的智谱API Key"
python day1_model_io.py
```

### 1.4 PromptTemplate 提示词模板

```python
"""PromptTemplate 与 ChatPromptTemplate"""

from langchain_core.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

# === 1. 基础 PromptTemplate ===

# 单变量模板
template = PromptTemplate.from_template("给我讲一个关于{topic}的笑话")
prompt = template.invoke({"topic": "程序员"})
print(prompt.text)  # 给我讲一个关于程序员的笑话

# 多变量模板
template = PromptTemplate(
    input_variables=["language", "task"],
    template="用{language}语言实现：{task}",
)
prompt = template.invoke({"language": "Python", "task": "快速排序"})
print(prompt.text)

# === 2. ChatPromptTemplate（更常用） ===

# 方式一：from_messages
chat_template = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}，回答用{style}风格。"),
    ("human", "{question}"),
])

messages = chat_template.invoke({
    "role": "Python 专家",
    "style": "简洁专业",
    "question": "装饰器是什么？",
})
print(f"\n消息列表: {messages.to_messages()}")

# 方式二：from_template 简写
simple_template = ChatPromptTemplate.from_template("翻译成英文：{text}")
messages = simple_template.invoke({"text": "今天天气很好"})
print(f"翻译提示: {messages.to_messages()}")

# === 3. MessagesPlaceholder（用于对话历史） ===

chat_with_history = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的AI助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# 模拟对话历史
from langchain_core.messages import HumanMessage, AIMessage

history = [
    HumanMessage(content="我叫小明"),
    AIMessage(content="你好小明！很高兴认识你。"),
]

messages = chat_with_history.invoke({
    "history": history,
    "input": "我叫什么名字？",
})
print(f"\n带历史的消息: {messages.to_messages()}")
```

### 1.5 OutputParser 输出解析

```python
"""OutputParser：让 LLM 输出变成结构化数据"""

import json
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
    CommaSeparatedListOutputParser,
)
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 1. StrOutputParser（最常用：提取字符串） ===

# 不用 parser：返回 AIMessage 对象
# 用 parser：直接返回字符串内容
str_parser = StrOutputParser()

result = llm.invoke("说一个Python关键词")
print(f"原始类型: {type(result)}")      # AIMessage
parsed = str_parser.invoke(result)
print(f"解析后类型: {type(parsed)}")    # str
print(f"内容: {parsed}")

# === 2. JsonOutputParser（结构化输出） ===

class BookRecommendation(BaseModel):
    title: str = Field(description="书名")
    author: str = Field(description="作者")
    reason: str = Field(description="推荐理由，一句话")

json_parser = JsonOutputParser(pydantic_object=BookRecommendation)

prompt = PromptTemplate(
    template="推荐一本关于{topic}的书。\n{format_instructions}",
    input_variables=["topic"],
    partial_variables={"format_instructions": json_parser.get_format_instructions()},
)

chain = prompt | llm | json_parser

result = chain.invoke({"topic": "Python编程"})
print(f"\n推荐书籍: {result}")
print(f"类型: {type(result)}")  # dict

# === 3. CommaSeparatedListOutputParser ===

list_parser = CommaSeparatedListOutputParser()

prompt = PromptTemplate(
    template="列出5个{category}相关的技术。\n{format_instructions}",
    input_variables=["category"],
    partial_variables={"format_instructions": list_parser.get_format_instructions()},
)

chain = prompt | llm | list_parser
result = chain.invoke({"category": "前端框架"})
print(f"\n技术列表: {result}")
print(f"类型: {type(result)}")  # list
```

### 1.6 LCEL 管道语法初体验

```python
"""LCEL (LangChain Expression Language) 管道语法"""

# LCEL 用 | 操作符把组件串联起来，类似 Unix 管道
# prompt | llm | parser  →  组合成一个链

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.7,
)

# 构建链
chain = (
    ChatPromptTemplate.from_template("用{style}风格解释：{concept}")
    | llm
    | StrOutputParser()
)

# 调用（同步）
result = chain.invoke({"style": "给小学生讲", "concept": "递归"})
print(f"回答: {result}")

# 流式调用
print("\n--- 流式 ---")
for chunk in chain.stream({"style": "专业", "concept": "向量数据库"}):
    print(chunk, end="", flush=True)
print()

# 批量调用
results = chain.batch([
    {"style": "简洁", "concept": "JSON"},
    {"style": "详细", "concept": "API"},
])
for r in results:
    print(f"  - {r[:50]}...")
```

### Day 1 小结

```
Day 1 核心概念：
┌─────────────────────────────────────────────┐
│  Model I/O 三层架构                           │
│                                               │
│  Input          Process         Output        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Prompt   │→ │   LLM    │→ │ Parser   │   │
│  │ Template │  │ (Chat)   │  │ (Str/JSON)│   │
│  └──────────┘  └──────────┘  └──────────┘   │
│       │              │              │         │
│    变量注入      模型调用       结构化解析      │
│                                               │
│  LCEL：prompt | llm | parser 管道组合          │
│  支持：invoke / stream / batch / ainvoke      │
└─────────────────────────────────────────────┘
```

### Day 1 练习

1. 用 `ChatPromptTemplate` 构建一个"代码审查助手"——输入代码片段，输出改进建议
2. 用 `JsonOutputParser` 让 LLM 输出 `{"score": int, "issues": [str], "suggestion": str}` 结构
3. 用 LCEL 管道串联以上组件，并测试流式输出

---

## Day 2：LCEL 链式组合

> LCEL 是 LangChain 的核心语法。掌握 LCEL，你就能灵活组合任何组件。

### 2.1 Runnable 协议

```
┌──────────────── Runnable 协议 ────────────────┐
│                                                │
│  所有 LangChain 组件都实现 Runnable 接口：       │
│                                                │
│  同步方法：                                     │
│    invoke(input)       → 单次调用               │
│    batch(inputs)       → 批量调用               │
│    stream(input)       → 流式迭代器             │
│                                                │
│  异步方法：                                     │
│    ainvoke(input)      → 异步单次               │
│    abatch(inputs)      → 异步批量               │
│    astream(input)      → 异步流式               │
│                                                │
│  组合方法：                                     │
│    a | b               → 顺序链（管道）          │
│    RunnableParallel    → 并行执行               │
│    RunnablePassthrough → 透传输入               │
│    RunnableLambda      → 包装自定义函数          │
│    RunnableBranch      → 条件分支               │
│                                                │
└────────────────────────────────────────────────┘
```

创建文件 `day2_lcel.py`：

```python
"""
Day 2: LCEL 链式组合
- Runnable 协议详解
- RunnableParallel / Passthrough / Lambda / Branch
- 链的调试与异常处理
"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import (
    RunnableParallel,
    RunnablePassthrough,
    RunnableLambda,
    RunnableBranch,
)

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 1. RunnablePassthrough（透传输入） ===

# 透传：输入直接传到输出，不做任何变换
passthrough_chain = RunnablePassthrough()
print(f"透传: {passthrough_chain.invoke('hello')}")

# 常见用法：在 Parallel 中保留原始输入
# 例如：同时生成摘要和翻译，但保留原文

# === 2. RunnableParallel（并行执行） ===

# 多个分支同时执行，结果合并为字典
parallel_chain = RunnableParallel({
    "original": RunnablePassthrough(),
    "summary": (
        ChatPromptTemplate.from_template("用一句话总结：{text}")
        | llm
        | StrOutputParser()
    ),
    "keywords": (
        ChatPromptTemplate.from_template("列出3个关键词：{text}")
        | llm
        | StrOutputParser()
    ),
})

result = parallel_chain.invoke({"text": "LangChain是一个用于构建LLM应用的开源框架，它提供了模块化的组件和链式组合语法。"})
print(f"\n并行结果:")
print(f"  原文: {result['original']}")
print(f"  摘要: {result['summary']}")
print(f"  关键词: {result['keywords']}")

# === 3. RunnableLambda（自定义函数） ===

# 把任意 Python 函数包装成 Runnable
def count_words(text: str) -> int:
    return len(text.split())

def format_result(word_count: int) -> str:
    return f"字数: {word_count}"

# 用法一：单独包装
count_chain = RunnableLambda(count_words)
print(f"\n字数统计: {count_chain.invoke('Hello World Python')}")

# 用法二：嵌入 LCEL 管道
full_chain = (
    ChatPromptTemplate.from_template("用50字以内解释：{concept}")
    | llm
    | StrOutputParser()
    | RunnableLambda(count_words)
    | RunnableLambda(format_result)
)

result = full_chain.invoke({"concept": "机器学习"})
print(f"结果: {result}")

# === 4. RunnableBranch（条件分支） ===

# 根据输入选择不同的处理链
branch_chain = RunnableBranch(
    # (条件函数, 执行链) 对
    (
        lambda x: x["language"] == "Python",
        ChatPromptTemplate.from_template("用Python实现：{task}") | llm | StrOutputParser(),
    ),
    (
        lambda x: x["language"] == "JavaScript",
        ChatPromptTemplate.from_template("用JavaScript实现：{task}") | llm | StrOutputParser(),
    ),
    # 默认分支
    ChatPromptTemplate.from_template("用伪代码实现：{task}") | llm | StrOutputParser(),
)

result = branch_chain.invoke({"language": "Python", "task": "快速排序"})
print(f"\n分支结果(Python): {result[:100]}...")

# === 5. 字典输入与 itemgetter ===

from operator import itemgetter

# 复杂链：输入是字典，各组件从字典中取不同字段
review_chain = (
    RunnableParallel({
        "review_summary": (
            ChatPromptTemplate.from_template("总结这条评价的核心观点：{review}")
            | llm
            | StrOutputParser()
        ),
        "sentiment": (
            ChatPromptTemplate.from_template(
                "判断评价的情感倾向，只回答'正面'或'负面'：{review}"
            )
            | llm
            | StrOutputParser()
        ),
    })
    | RunnableLambda(lambda x: f"[{x['sentiment']}] {x['review_summary']}")
)

result = review_chain.invoke({
    "review": "这个产品非常好用，界面简洁，功能强大，但偶尔会卡顿。"
})
print(f"\n评价分析: {result}")
```

### 2.2 异步链

```python
"""LCEL 异步链"""

import asyncio
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# 异步 invoke
chain = (
    ChatPromptTemplate.from_template("用一句话解释：{concept}")
    | llm
    | StrOutputParser()
)

async def demo_ainvoke():
    result = await chain.ainvoke({"concept": "协程"})
    print(f"异步结果: {result}")

# 异步流式
async def demo_astream():
    print("异步流式: ", end="")
    async for chunk in chain.astream({"concept": "事件循环"}):
        print(chunk, end="", flush=True)
    print()

# 异步批量
async def demo_abatch():
    results = await chain.abatch([
        {"concept": "装饰器"},
        {"concept": "生成器"},
        {"concept": "上下文管理器"},
    ])
    for r in results:
        print(f"  - {r[:50]}...")

# 异步并行
async def demo_parallel():
    parallel = RunnableParallel({
        "cn": ChatPromptTemplate.from_template("用中文解释：{word}") | llm | StrOutputParser(),
        "en": ChatPromptTemplate.from_template("Explain in English: {word}") | llm | StrOutputParser(),
    })
    result = await parallel.ainvoke({"word": "递归"})
    print(f"\n中文: {result['cn'][:80]}...")
    print(f"英文: {result['en'][:80]}...")

async def main():
    await demo_ainvoke()
    await demo_astream()
    await demo_abatch()
    await demo_parallel()

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

### 2.3 链的异常处理与 fallback

```python
"""异常处理与 Fallback 链"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Fallback：主链失败时自动切换到备用链
cheap_llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

powerful_llm = ChatOpenAI(
    model="glm-4-plus",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# 主链用强力模型，失败后降级到便宜模型
main_chain = (
    ChatPromptTemplate.from_template("详细解释：{concept}")
    | powerful_llm
    | StrOutputParser()
)

fallback_chain = (
    ChatPromptTemplate.from_template("简要解释：{concept}")
    | cheap_llm
    | StrOutputParser()
)

# with_fallbacks：依次尝试，直到成功
robust_chain = main_chain.with_fallbacks([fallback_chain])

# with_retry：自动重试（可配置重试次数和间隔）
retry_chain = main_chain.with_retry(stop_after_attempt=3)

# 使用示例
try:
    result = robust_chain.invoke({"concept": "Transformer架构"})
    print(f"结果: {result[:100]}...")
except Exception as e:
    print(f"所有链均失败: {e}")
```

### 2.4 链的调试

```python
"""链的调试方法"""

from langchain_core.globals import set_debug, set_verbose

# 方式一：全局调试开关（最简单）
set_debug(True)   # 打印每一步的输入输出
set_verbose(True)  # 打印更详细的信息

# 调试完成后关闭
set_debug(False)
set_verbose(False)

# 方式二：使用 get_graph 可视化链结构
chain = (
    ChatPromptTemplate.from_template("解释：{concept}")
    | cheap_llm
    | StrOutputParser()
)

# 打印链的执行图
graph = chain.get_graph()
print(graph.draw_ascii())

# 方式三：使用 callbacks（更精细，Day 6 详解）
from langchain_core.callbacks import BaseCallbackHandler

class DebugCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"[LLM开始] prompts: {prompts}")

    def on_llm_end(self, response, **kwargs):
        print(f"[LLM结束] response: {response}")

    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"[链开始] inputs: {inputs}")

    def on_chain_end(self, outputs, **kwargs):
        print(f"[链结束] outputs: {outputs}")

# 使用 callback
result = chain.invoke(
    {"concept": "LCEL"},
    config={"callbacks": [DebugCallback()]},
)
```

### Day 2 小结

```
Day 2 核心概念：
┌───────────────────────────────────────────────┐
│  LCEL 五大组合原语                              │
│                                                 │
│  | (管道)      → 顺序执行 a | b | c             │
│  Parallel     → 并行执行，结果合并为字典         │
│  Passthrough  → 透传输入                        │
│  Lambda       → 包装自定义函数                   │
│  Branch       → 条件分支                        │
│                                                 │
│  异常处理：                                      │
│  with_fallbacks  → 降级策略                     │
│  with_retry      → 自动重试                     │
│                                                 │
│  调试：                                          │
│  set_debug(True) → 全局调试                     │
│  get_graph()     → 查看链结构                   │
│  callbacks       → 精细监控                     │
└───────────────────────────────────────────────┘
```

### Day 2 练习

1. 构建一个"多语言翻译链"：输入文本 + 目标语言列表，并行翻译成所有语言
2. 用 `RunnableBranch` 实现：输入问题 → 判断是代码问题/概念问题/调试问题 → 分别用不同的 prompt 模板处理
3. 为你的链添加 fallback：主模型 glm-4-plus 失败后降级到 glm-4-flash

---

## Day 3：RAG 检索链

> 用 LangChain 重构 Week 4 的 RAG 系统，对比"自己写"和"用框架"的差异。

### 3.1 LangChain RAG 组件概览

```
┌────────────── LangChain RAG 组件 ──────────────┐
│                                                  │
│  文档加载（Document Loaders）                     │
│  ├── TextLoader      ── 纯文本                   │
│  ├── PyPDFLoader     ── PDF                      │
│  ├── UnstructuredLoader ── 各种格式              │
│  └── DirectoryLoader ── 批量加载目录              │
│                                                  │
│  文档切分（Text Splitters）                       │
│  ├── RecursiveCharacterTextSplitter ── 最常用    │
│  ├── TokenTextSplitter             ── 按 Token   │
│  └── MarkdownHeaderTextSplitter    ── 按标题     │
│                                                  │
│  Embedding 模型                                   │
│  └── 通过 OpenAI 兼容接口使用智谱 Embedding       │
│                                                  │
│  向量数据库（Vector Stores）                      │
│  ├── Chroma   ── 本地轻量（本周使用）             │
│  ├── FAISS    ── Meta 开源，纯内存                │
│  └── Pinecone ── 云端服务                        │
│                                                  │
│  检索器（Retrievers）                             │
│  ├── vectorstore.as_retriever() ── 基础检索      │
│  ├── ContextualCompressionRetriever ── 压缩      │
│  ├── EnsembleRetriever          ── 混合检索      │
│  └── MultiQueryRetriever        ── 多查询        │
│                                                  │
└──────────────────────────────────────────────────┘
```

创建文件 `day3_rag_chain.py`：

```python
"""
Day 3: LangChain RAG 检索链
- 文档加载与切分
- 向量数据库与检索
- RAG 链完整实现
"""

import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from langchain_community.vectorstores import Chroma

# === 1. 文档加载 ===

# 加载纯文本
txt_loader = TextLoader("sample.txt", encoding="utf-8")
txt_docs = txt_loader.load()
print(f"加载了 {len(txt_docs)} 个文本文档")

# 加载 PDF
# pdf_loader = PyPDFLoader("sample.pdf")
# pdf_docs = pdf_loader.load()
# print(f"加载了 {len(pdf_docs)} 个 PDF 页面")

# === 2. 文档切分 ===

# RecursiveCharacterTextSplitter（最常用）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # 每块最大字符数
    chunk_overlap=50,     # 块间重叠字符数
    separators=["\n\n", "\n", "。", "，", " ", ""],  # 分隔符优先级
)

# 准备示例文档
sample_text = """
Python 是一种广泛使用的高级编程语言。它的设计哲学强调代码的可读性。

Python 支持多种编程范式，包括面向对象、命令式、函数式和过程式编程。
它有一个全面的标准库，通常被称为"内置电池"。

Python 的应用领域非常广泛，包括 Web 开发、数据分析、人工智能、
自动化脚本等。Django 和 Flask 是最流行的 Web 框架。

NumPy 和 Pandas 是数据分析的核心库。TensorFlow 和 PyTorch
是深度学习的主流框架。LangChain 是构建 LLM 应用的框架。
""".strip()

docs = splitter.create_documents([sample_text])
print(f"\n切分为 {len(docs)} 个块：")
for i, doc in enumerate(docs):
    print(f"  块{i+1}: {doc.page_content[:60]}...")

# Markdown 按标题切分
md_text = """# Python指南

## 基础语法

Python 使用缩进表示代码块，而不是大括号。

## 数据结构

### 列表

列表是有序的可变序列。

### 字典

字典是键值对的集合。
"""

md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
)
md_docs = md_splitter.split_text(md_text)
print(f"\nMarkdown 切分结果:")
for doc in md_docs:
    print(f"  [{doc.metadata}] {doc.page_content[:40]}...")

# === 3. Embedding + 向量数据库 ===

# 智谱 Embedding（兼容 OpenAI 接口）
embeddings = OpenAIEmbeddings(
    model="embedding-3",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
)

# 创建 Chroma 向量数据库
vectorstore = Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    collection_name="python_guide",
    persist_directory="./chroma_db",
)

# 相似度检索
results = vectorstore.similarity_search("Python 有哪些应用领域？", k=2)
print(f"\n检索结果:")
for doc in results:
    print(f"  {doc.page_content[:80]}...")

# 带分数的检索
results_with_scores = vectorstore.similarity_search_with_score(
    "深度学习框架", k=2
)
for doc, score in results_with_scores:
    print(f"  [距离={score:.4f}] {doc.page_content[:60]}...")

# === 4. 检索器（Retriever） ===

# 基础检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",  # "mmr" 或 "similarity_score_threshold"
    search_kwargs={"k": 3},
)

retrieved_docs = retriever.invoke("Python Web 框架")
print(f"\nRetriever 返回 {len(retrieved_docs)} 个文档")

# === 5. 完整 RAG 链 ===

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.3,
)

# RAG 提示词模板
rag_prompt = ChatPromptTemplate.from_template(
    """根据以下检索到的文档内容回答问题。如果文档中没有相关信息，请说明"根据已有文档无法回答"。

**检索到的文档内容**
{context}

**问题**
{question}

**回答**"""
)

# 格式化文档的辅助函数
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 构建 RAG 链（LCEL）
rag_chain = (
    # 并行：检索文档 + 透传问题
    RunnableParallel({
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    })
    # 填入提示词
    | rag_prompt
    # 调用 LLM
    | llm
    # 解析输出
    | StrOutputParser()
)

# 调用
answer = rag_chain.invoke("Python 有哪些 Web 框架？")
print(f"\nRAG 回答: {answer}")

# 流式 RAG
print("\n--- 流式 RAG ---")
for chunk in rag_chain.stream("Python 数据分析用什么库？"):
    print(chunk, end="", flush=True)
print()
```

### 3.2 高级检索策略

```python
"""高级检索：多查询 + 压缩 + 混合"""

import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

embeddings = OpenAIEmbeddings(
    model="embedding-3",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
)

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# 加载已有向量数据库
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="python_guide",
)

# === 1. MultiQueryRetriever（多查询检索） ===
# 自动用 LLM 生成多个变体查询，分别检索后合并

mq_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
    llm=llm,
)

# 自定义查询生成提示词
QUERY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个AI助手。根据用户的问题，生成3个不同角度的变体问题，每行一个。"),
    ("human", "{question}"),
])

mq_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 2}),
    llm=llm,
    prompt=QUERY_PROMPT,
)

docs = mq_retriever.invoke("Python 做数据分析用什么？")
print(f"多查询检索: {len(docs)} 个文档")

# === 2. ContextualCompressionRetriever（上下文压缩） ===
# 先检索，再用 LLM 提取与查询相关的片段

compressor = LLMChainExtractor.from_llm(llm)

compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
)

compressed_docs = compression_retriever.invoke("Python Web 框架")
print(f"\n压缩检索: {len(compressed_docs)} 个文档片段")
for doc in compressed_docs:
    print(f"  {doc.page_content[:80]}...")

# === 3. 自定义混合检索（向量 + 关键词） ===

from langchain_community.retrievers import BM25Retriever

# BM25 关键词检索（需要 jieba 分词）
# pip install jieba rank_bm25

try:
    import jieba  # noqa: F401
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False

if HAS_JIEBA:
    from langchain_community.retrievers import BM25Retriever

    # 准备文档
    all_docs = vectorstore.get()["documents"]
    from langchain_core.documents import Document

    doc_objects = [
        Document(page_content=d, metadata={})
        for d in all_docs
    ]

    bm25_retriever = BM25Retriever.from_documents(
        doc_objects, k=2
    )

    # 手动融合向量检索和 BM25 检索结果
    def hybrid_retrieve(query: str, top_k: int = 4):
        """混合检索：向量 + BM25"""
        vector_results = vectorstore.similarity_search(query, k=top_k)
        bm25_results = bm25_retriever.invoke(query)

        # 简单去重合并
        seen = set()
        merged = []
        for doc in vector_results + bm25_results:
            key = doc.page_content[:50]
            if key not in seen:
                seen.add(key)
                merged.append(doc)
        return merged[:top_k]

    results = hybrid_retrieve("Python 机器学习")
    print(f"\n混合检索: {len(results)} 个文档")
else:
    print("\n跳过 BM25 混合检索（需安装 jieba: pip install jieba rank_bm25）")
```

### 3.3 对比：自己写 vs LangChain

```python
"""对比 Week 4 自己写的 RAG vs LangChain RAG"""

# ┌──────────────────────────────────────────────────────────┐
# │  自己写（Week 4）                │  LangChain（Week 5）  │
# │──────────────────────────────────┼──────────────────────│
# │  手动 httpx 调用 Embedding API   │  OpenAIEmbeddings    │
# │  手动 ChromaDB CRUD              │  Chroma.from_docs    │
# │  手动拼接 context 字符串          │  format_docs + LCEL  │
# │  手动构建 Chat 消息              │  ChatPromptTemplate  │
# │  手动 httpx 流式解析             │  chain.stream()      │
# │  手动实现 ReAct 循环             │  create_react_agent  │
# │──────────────────────────────────┼──────────────────────│
# │  优点：完全掌控，灵活             │  优点：快速原型       │
# │  缺点：重复造轮子                │  缺点：黑盒，调试难   │
# └──────────────────────────────────────────────────────────┘

# 建议：
# - 学习阶段：先自己写（Week 1-4），理解原理
# - 生产阶段：用 LangChain 快速搭建，需要时深入源码定制
# - 复杂场景：混合使用——核心逻辑自己写，工具集成用 LangChain
```

### Day 3 小结

```
Day 3 核心概念：
┌─────────────────────────────────────────────────┐
│  LangChain RAG 链                                │
│                                                   │
│  文档加载 → 切分 → Embedding → 向量数据库          │
│                                                   │
│  检索策略：                                        │
│  ├── similarity       基础向量检索                 │
│  ├── mmr              最大边际相关性（去重）        │
│  ├── multi_query      多查询变体                   │
│  ├── compression      LLM 压缩相关片段             │
│  └── hybrid           向量 + BM25 混合             │
│                                                   │
│  RAG 链 LCEL 写法：                               │
│  retriever | format_docs  →  获取并格式化文档       │
│  Parallel({context, question})  →  并行准备输入    │
│  | prompt | llm | parser  →  生成并解析回答        │
└─────────────────────────────────────────────────┘
```

### Day 3 练习

1. 用 `DirectoryLoader` 批量加载一个目录下的所有 `.md` 文件
2. 实现 MMR 检索（`search_type="mmr"`），对比与 `similarity` 的结果差异
3. 用 LangChain RAG 链重构你 Week 4 的知识库 Agent，对比代码量

---

## Day 4：Agent 与 Tool

> Agent 是 LangChain 最强大的组件。今天学习如何用 LangChain 的 Tool 系统和 Agent 来构建智能体。

### 4.1 LangChain Agent 体系

```
┌────────────── LangChain Agent 体系 ──────────────┐
│                                                    │
│  Agent 类型（0.3+ 推荐）：                          │
│  ├── create_react_agent     ── ReAct 推理+行动     │
│  ├── create_tool_calling_agent ── 原生工具调用     │
│  └── 自定义 Agent          ── 继承 BaseAgent       │
│                                                    │
│  Agent 执行器：                                     │
│  └── AgentExecutor          ── 管理循环/异常/记忆   │
│                                                    │
│  Tool 定义：                                        │
│  ├── @tool 装饰器           ── 最简单              │
│  ├── StructuredTool         ── 结构化参数           │
│  └── DynamicTool            ── 动态创建            │
│                                                    │
│  工具集成：                                         │
│  ├── langchain-community   ── 社区工具集           │
│  ├── 自定义 Python 函数    ── 包装成 Tool           │
│  └── RetrieverTool         ── RAG 作为工具          │
│                                                    │
└────────────────────────────────────────────────────┘
```

创建文件 `day4_agent_tool.py`：

```python
"""
Day 4: LangChain Agent 与 Tool
- 自定义 Tool
- create_react_agent
- AgentExecutor
- RAG 作为 Tool
"""

import os
import json
import math
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool, StructuredTool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
from pydantic import BaseModel, Field

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

# === 1. 用 @tool 装饰器定义工具 ===

@tool
def calculator(expression: str) -> str:
    """计算数学表达式的结果。输入为一个数学表达式字符串，如 '2+3*4'。"""
    try:
        # 安全计算：只允许数学运算
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "错误：只支持数字和基本运算符"
        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def word_count(text: str) -> str:
    """统计文本的字数和词数。输入为要统计的文本。"""
    char_count = len(text)
    word_count = len(text.split())
    return f"字数: {char_count}, 词数: {word_count}"

@tool
def get_current_time(format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """获取当前时间。可选参数 format 为时间格式，默认 '%Y-%m-%d %H:%M:%S'。"""
    from datetime import datetime
    return datetime.now().strftime(format)

# 测试工具
print(calculator.invoke({"expression": "2+3*4"}))
print(word_count.invoke({"text": "Hello World Python LangChain"}))
print(get_current_time.invoke({}))

# === 2. StructuredTool（结构化参数工具） ===

class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    num_results: int = Field(default=5, description="返回结果数量")

def search_function(query: str, num_results: int = 5) -> str:
    """模拟搜索功能（实际项目中替换为真实搜索API）"""
    mock_results = [
        f"搜索结果{i+1}: 关于'{query}'的相关信息..."
        for i in range(num_results)
    ]
    return "\n".join(mock_results)

search_tool = StructuredTool.from_function(
    func=search_function,
    name="search",
    description="搜索互联网获取信息。输入搜索关键词和结果数量。",
    args_schema=SearchInput,
)

print(f"\n{search_tool.invoke({'query': 'Python', 'num_results': 3})}")

# === 3. create_react_agent ===

# 获取 ReAct 提示词模板
# 注意：hub.pull 需要网络，如果不可用可以用自定义模板
try:
    react_prompt = hub.pull("hwchase17/react")
except Exception:
    # 自定义 ReAct 模板
    react_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个有帮助的AI助手，可以使用工具来回答问题。

你可以使用以下工具：
{tools}

使用工具时，请严格按照以下格式：

Question: 你必须回答的输入问题
Thought: 你应该总是思考下一步做什么
Action: 要使用的工具，必须是 [{tool_names}] 中的一个
Action Input: 工具的输入参数
Observation: 工具的返回结果
... (Thought/Action/Action Input/Observation 可以重复N次)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终回答

开始！
Question: {input}
Thought: {agent_scratchpad}"""),
    ])

# 创建工具列表
tools = [calculator, word_count, get_current_time, search_tool]

# 创建 ReAct Agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt,
)

# 创建 AgentExecutor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,           # 打印思考过程
    max_iterations=5,       # 最大推理步数
    handle_parsing_errors=True,  # 解析错误时自动恢复
)

# 测试 Agent
print("\n=== 测试 1: 计算 ===")
result = agent_executor.invoke({"input": "123 * 456 + 789 等于多少？"})
print(f"结果: {result['output']}")

print("\n=== 测试 2: 多步推理 ===")
result = agent_executor.invoke({
    "input": "现在几点了？然后把当前时间的秒数乘以2算一下。"
})
print(f"结果: {result['output']}")

# === 4. RAG 作为 Tool ===

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import Tool

# 复用 Day 3 的向量数据库
embeddings = OpenAIEmbeddings(
    model="embedding-3",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
)

def rag_search_func(query: str) -> str:
    """RAG 检索函数"""
    try:
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            embedding_function=embeddings,
            collection_name="python_guide",
        )
        docs = vectorstore.similarity_search(query, k=3)
        if not docs:
            return "未找到相关文档"
        return "\n\n".join(doc.page_content for doc in docs)
    except Exception as e:
        return f"检索错误: {e}"

rag_tool = Tool(
    name="knowledge_base",
    description="从知识库中检索相关文档。输入为检索关键词或问题。",
    func=rag_search_func,
)

# 带 RAG 的 Agent
all_tools = [calculator, word_count, get_current_time, search_tool, rag_tool]

rag_agent = create_react_agent(llm=llm, tools=all_tools, prompt=react_prompt)
rag_agent_executor = AgentExecutor(
    agent=rag_agent,
    tools=all_tools,
    verbose=True,
    max_iterations=6,
    handle_parsing_errors=True,
)

print("\n=== 测试 3: RAG Agent ===")
result = rag_agent_executor.invoke({
    "input": "Python 有哪些数据分析库？帮我算一下'数据分析'这个词有几个字。"
})
print(f"结果: {result['output']}")
```

### 4.2 Tool Calling Agent（原生工具调用）

```python
"""Tool Calling Agent：利用 LLM 原生 function calling 能力"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

@tool
def add(a: int, b: int) -> int:
    """计算两个数的和"""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """计算两个数的乘积"""
    return a * b

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气（模拟）"""
    mock_data = {
        "北京": "晴天，25°C",
        "上海": "多云，22°C",
        "武汉": "小雨，20°C",
        "深圳": "阴天，28°C",
    }
    return mock_data.get(city, f"{city}：暂无天气数据")

tools = [add, multiply, get_weather]

# Tool Calling Agent 提示词（更简洁）
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的AI助手，可以使用工具来回答问题。"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 创建 Tool Calling Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
)

# 测试
result = agent_executor.invoke({"input": "北京和上海的天气怎么样？3+5等于多少？"})
print(f"结果: {result['output']}")
```

### Day 4 小结

```
Day 4 核心概念：
┌─────────────────────────────────────────────────┐
│  LangChain Agent 两种模式                         │
│                                                   │
│  ReAct Agent:                                     │
│  - 基于文本推理（Thought→Action→Observation）     │
│  - 任何 LLM 都能用                                │
│  - 但依赖 prompt 格式，解析可能失败                │
│                                                   │
│  Tool Calling Agent:                              │
│  - 利用 LLM 原生 function calling                 │
│  - 结构化输出，更可靠                              │
│  - 需要 LLM 支持 function calling（GLM-4 支持）   │
│                                                   │
│  Tool 定义方式：                                   │
│  @tool          → 最简单，装饰器                   │
│  StructuredTool → Pydantic 参数验证               │
│  Tool           → 包装已有函数                    │
│                                                   │
│  AgentExecutor 管理循环：                          │
│  max_iterations        → 最大步数                 │
│  handle_parsing_errors → 解析容错                 │
│  verbose=True          → 打印推理过程             │
└─────────────────────────────────────────────────┘
```

### Day 4 练习

1. 创建一个"代码执行工具"——接收 Python 代码字符串，用 `exec` 在受限环境中执行并返回结果
2. 创建一个带 3 个工具的 Agent：文件读取 + 计算 + 搜索，处理复合问题
3. 对比 ReAct Agent 和 Tool Calling Agent 在同一问题上的表现差异

---

## Day 5：Memory 对话记忆

> 没有 Memory 的 Agent 是"金鱼记忆"——每次对话都从头开始。今天学习如何给 Agent 加上记忆。

### 5.1 Memory 体系

```
┌────────────── LangChain Memory 体系 ──────────────┐
│                                                     │
│  历史方案（0.1.x，已弃用）：                         │
│  ├── ConversationBufferMemory       ── 全量保存     │
│  ├── ConversationBufferWindowMemory ── 滑动窗口     │
│  └── ConversationSummaryMemory      ── 摘要压缩     │
│                                                     │
│  新方案（0.3+，推荐）：                              │
│  ├── RunnableWithMessageHistory     ── LCEL 原生    │
│  └── ChatMessageHistory             ── 底层存储     │
│                                                     │
│  存储后端：                                          │
│  ├── InMemoryChatMessageHistory ── 内存（学习用）   │
│  ├── FileChatMessageHistory    ── 文件持久化        │
│  ├── RedisChatMessageHistory   ── Redis            │
│  └── SQLChatMessageHistory     ── 数据库            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

创建文件 `day5_memory.py`：

```python
"""
Day 5: LangChain Memory 对话记忆
- ChatMessageHistory
- RunnableWithMessageHistory
- 持久化存储
- Agent + Memory
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0.7,
)

# === 1. ChatMessageHistory（底层存储） ===

# 内存存储（重启丢失）
history = InMemoryChatMessageHistory()

# 添加消息
history.add_user_message("你好，我叫小明")
history.add_ai_message("你好小明！很高兴认识你。")
history.add_user_message("我喜欢 Python")
history.add_ai_message("Python 是一门很棒的语言！")

# 读取历史
messages = history.messages
print(f"历史消息数: {len(messages)}")
for msg in messages:
    print(f"  {type(msg).__name__}: {msg.content}")

# === 2. RunnableWithMessageHistory（LCEL 原生记忆） ===

# 用字典管理多个会话的历史
session_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """根据 session_id 获取或创建会话历史"""
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

# 创建带记忆的链
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的AI助手，请记住用户告诉你的信息。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm | StrOutputParser()

# 包装成带记忆的链
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 模拟多轮对话
session_id = "user_001"

print("\n=== 第一轮对话 ===")
response1 = chain_with_history.invoke(
    {"input": "你好，我叫小红，我是一名前端工程师"},
    config={"configurable": {"session_id": session_id}},
)
print(f"AI: {response1}")

print("\n=== 第二轮对话 ===")
response2 = chain_with_history.invoke(
    {"input": "我叫什么名字？我做什么工作？"},
    config={"configurable": {"session_id": session_id}},
)
print(f"AI: {response2}")

# 新会话——不会记住之前的对话
print("\n=== 新会话 ===")
response3 = chain_with_history.invoke(
    {"input": "我叫什么名字？"},
    config={"configurable": {"session_id": "user_002"}},
)
print(f"AI: {response3}")

# === 3. 对话窗口限制（自定义实现） ===

class WindowedChatHistory:
    """限制历史消息窗口大小"""

    def __init__(self, max_messages: int = 10):
        self.histories = {}
        self.max_messages = max_messages

    def get_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self.histories:
            self.histories[session_id] = InMemoryChatMessageHistory()
        return self.histories[session_id]

    def trim_history(self, session_id: str):
        """裁剪历史，只保留最近 N 条消息"""
        history = self.get_history(session_id)
        if len(history.messages) > self.max_messages:
            # 保留最近的消息
            trimmed = history.messages[-self.max_messages:]
            history.clear()
            for msg in trimmed:
                history.add_message(msg)

windowed_manager = WindowedChatHistory(max_messages=6)

def get_windowed_history(session_id: str) -> InMemoryChatMessageHistory:
    windowed_manager.trim_history(session_id)
    return windowed_manager.get_history(session_id)

windowed_chain = RunnableWithMessageHistory(
    chain,
    get_windowed_history,
    input_messages_key="input",
    history_messages_key="history",
)

# === 4. 文件持久化 ===

from langchain_community.chat_message_histories import FileChatMessageHistory

def get_file_history(session_id: str) -> FileChatMessageHistory:
    """将对话历史保存到文件"""
    return FileChatMessageHistory(f"./chat_history/{session_id}.json")

# 确保目录存在
os.makedirs("./chat_history", exist_ok=True)

persistent_chain = RunnableWithMessageHistory(
    chain,
    get_file_history,
    input_messages_key="input",
    history_messages_key="history",
)

print("\n=== 持久化对话 ===")
response = persistent_chain.invoke(
    {"input": "请记住：我最喜欢的颜色是蓝色"},
    config={"configurable": {"session_id": "persistent_001"}},
)
print(f"AI: {response}")

# 重新加载（即使程序重启，历史仍在文件中）
response = persistent_chain.invoke(
    {"input": "我最喜欢的颜色是什么？"},
    config={"configurable": {"session_id": "persistent_001"}},
)
print(f"AI: {response}")

# === 5. Agent + Memory ===

from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

@tool
def remember_fact(fact: str) -> str:
    """记住一个事实。输入为要记住的事实内容。"""
    return f"已记住: {fact}"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"

tools = [remember_fact, calculate]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有帮助的AI助手。你可以使用工具来记住信息和计算。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
)

# 包装 Agent 为带记忆的链
agent_with_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

print("\n=== Agent + Memory ===")
result = agent_with_history.invoke(
    {"input": "请记住：我明天有一个会议"},
    config={"configurable": {"session_id": "agent_001"}},
)
print(f"结果: {result['output']}")

result = agent_with_history.invoke(
    {"input": "我明天有什么安排？"},
    config={"configurable": {"session_id": "agent_001"}},
)
print(f"结果: {result['output']}")
```

### Day 5 小结

```
Day 5 核心概念：
┌────────────────────────────────────────────────┐
│  Memory 新范式（0.3+）                           │
│                                                  │
│  核心组件：                                       │
│  ChatMessageHistory     → 底层消息存储            │
│  RunnableWithMessageHistory → LCEL 记忆包装      │
│                                                  │
│  关键配置：                                       │
│  input_messages_key   → 用户输入的键名            │
│  history_messages_key → 历史消息的键名            │
│  session_id           → 会话标识                 │
│                                                  │
│  存储选项：                                       │
│  InMemory  → 内存（学习用，重启丢失）             │
│  File      → JSON 文件持久化                     │
│  Redis/SQL → 生产级持久化                        │
│                                                  │
│  窗口策略：                                       │
│  自定义 trim → 保留最近 N 条消息                  │
│  摘要压缩 → LLM 生成历史摘要（省 Token）          │
└────────────────────────────────────────────────┘
```

### Day 5 练习

1. 实现一个"摘要记忆"——当历史超过 10 条消息时，用 LLM 生成摘要替换旧消息
2. 将对话历史保存到 SQLite（使用 `SQLChatMessageHistory`）
3. 构建一个带记忆的 RAG Agent：能记住用户偏好，在后续检索中优先返回偏好相关的结果

---

## Day 6：Callbacks + 综合实战

> Callbacks 是 LangChain 的可观测性基础。今天先学 Callbacks，然后用 LangChain 重构 Week 4 的知识库 Agent。

### 6.1 Callbacks 系统

```python
"""
Day 6 Part 1: Callbacks 回调系统
- 自定义 Callback Handler
- 流式输出监控
- 日志记录
"""

import os
import time
import json
from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.callbacks import BaseCallbackHandler

# === 1. 自定义 Callback Handler ===

class TimingCallback(BaseCallbackHandler):
    """计时回调：记录每步耗时"""

    def __init__(self):
        self.start_times = {}
        self.timings = {}

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.start_times["llm"] = time.time()

    def on_llm_end(self, response, **kwargs):
        elapsed = time.time() - self.start_times.get("llm", time.time())
        self.timings["llm"] = elapsed
        print(f"  [LLM] 耗时: {elapsed:.2f}s")

    def on_chain_start(self, serialized, inputs, **kwargs):
        name = serialized.get("name", "unknown")
        self.start_times[name] = time.time()

    def on_chain_end(self, outputs, **kwargs):
        # 链结束时不一定有对应的 start（嵌套链）
        pass

class LoggingCallback(BaseCallbackHandler):
    """日志回调：记录所有事件"""

    def __init__(self, log_file: str = "langchain_log.jsonl"):
        self.log_file = log_file
        self.events = []

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._log("llm_start", {"prompts": prompts})

    def on_llm_end(self, response, **kwargs):
        content = response.generations[0][0].text if response.generations else ""
        self._log("llm_end", {"response_length": len(content)})

    def on_tool_start(self, serialized, input_str, **kwargs):
        self._log("tool_start", {"tool": serialized.get("name"), "input": input_str})

    def on_tool_end(self, output, **kwargs):
        self._log("tool_end", {"output": str(output)[:200]})

    def _log(self, event_type: str, data: dict):
        event = {
            "timestamp": time.time(),
            "event": event_type,
            **data,
        }
        self.events.append(event)
        # 追加写入文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

# 使用 Callback
llm = ChatOpenAI(
    model="glm-4-flash",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
    temperature=0,
)

chain = (
    ChatPromptTemplate.from_template("用一句话解释：{concept}")
    | llm
    | StrOutputParser()
)

timing_cb = TimingCallback()
logging_cb = LoggingCallback()

result = chain.invoke(
    {"concept": "向量数据库"},
    config={"callbacks": [timing_cb, logging_cb]},
)
print(f"结果: {result}")
print(f"计时: {timing_cb.timings}")

# === 2. 流式 Token 计数 ===

class TokenCountCallback(BaseCallbackHandler):
    """流式 Token 计数"""

    def __init__(self):
        self.token_count = 0
        self.start_time = None

    def on_llm_start(self, serialized, prompts, **kwargs):
        self.token_count = 0
        self.start_time = time.time()

    def on_llm_new_token(self, token: str, **kwargs):
        self.token_count += 1

    def on_llm_end(self, response, **kwargs):
        elapsed = time.time() - self.start_time if self.start_time else 0
        speed = self.token_count / elapsed if elapsed > 0 else 0
        print(f"  Token 数: {self.token_count}, 耗时: {elapsed:.2f}s, 速度: {speed:.1f} tokens/s")

# 流式 + 计数
token_cb = TokenCountCallback()
print("\n--- 流式 + Token 计数 ---")
for chunk in chain.stream(
    {"concept": "Transformer"},
    config={"callbacks": [token_cb]},
):
    print(chunk, end="", flush=True)
print()
```

### 6.2 综合实战：用 LangChain 重构知识库 Agent

```python
"""
Day 6 Part 2: 用 LangChain 重构知识库 Agent
对比 Week 4 手写版本，体验框架的威力
"""

import os
import sys
import asyncio
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.tools import tool, StructuredTool
from langchain_core.callbacks import BaseCallbackHandler
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

# === 配置 ===

LLM_CONFIG = {
    "model": "glm-4-flash",
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "api_key": os.environ.get("ZHIPU_API_KEY"),
}

embeddings = OpenAIEmbeddings(
    model="embedding-3",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    api_key=os.environ.get("ZHIPU_API_KEY"),
)

llm = ChatOpenAI(**LLM_CONFIG, temperature=0.3)

# === 1. 文档索引（复用 Day 3 逻辑） ===

def build_knowledge_base(docs_dir: str, db_dir: str = "./kb_chroma"):
    """构建知识库"""
    if os.path.exists(db_dir):
        print(f"加载已有知识库: {db_dir}")
        return Chroma(
            persist_directory=db_dir,
            embedding_function=embeddings,
            collection_name="kb_agent",
        )

    # 加载文档
    if not os.path.exists(docs_dir):
        # 创建示例文档
        os.makedirs(docs_dir, exist_ok=True)
        sample_content = """Python 异步编程指南

异步编程是现代 Python 的重要特性。asyncio 是 Python 的标准异步框架。

协程使用 async def 定义，用 await 等待异步操作。

事件循环是 asyncio 的核心，负责调度协程的执行。

httpx 是支持异步 HTTP 请求的库，AsyncClient 可以发送并发请求。

Pydantic 用于数据验证和序列化，BaseModel 是核心类。

LangChain 是构建 LLM 应用的框架，核心概念包括链（Chain）、代理（Agent）、工具（Tool）。

RAG 是检索增强生成技术，通过检索外部知识来辅助 LLM 回答问题。

向量数据库存储文档的 Embedding，支持相似度检索。ChromaDB 是轻量级的选择。
"""
        with open(os.path.join(docs_dir, "python_guide.txt"), "w", encoding="utf-8") as f:
            f.write(sample_content)

    # 加载并切分
    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    docs = loader.load()
    print(f"加载了 {len(docs)} 个文档")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=30,
    )
    splits = splitter.split_documents(docs)
    print(f"切分为 {len(splits)} 个块")

    # 创建向量数据库
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        collection_name="kb_agent",
        persist_directory=db_dir,
    )
    print(f"知识库已创建: {db_dir}")
    return vectorstore

# === 2. 定义工具 ===

@tool
def knowledge_search(query: str) -> str:
    """从知识库中搜索相关信息。当需要查找文档中的知识时使用此工具。"""
    try:
        vs = Chroma(
            persist_directory="./kb_chroma",
            embedding_function=embeddings,
            collection_name="kb_agent",
        )
        docs = vs.similarity_search(query, k=3)
        if not docs:
            return "未在知识库中找到相关信息。"
        return "\n\n".join(f"[来源: {d.metadata.get('source', '未知')}]\n{d.page_content}" for d in docs)
    except Exception as e:
        return f"知识库检索失败: {e}"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。输入为一个数学表达式，如 '2+3*4'。"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "错误：只支持基本数学运算"
        result = eval(expression, {"__builtins__": {}}, {})
        return f"结果: {result}"
    except Exception as e:
        return f"计算错误: {e}"

@tool
def word_analyze(text: str) -> str:
    """分析文本的统计信息，包括字数、词数和行数。"""
    chars = len(text)
    words = len(text.split())
    lines = len(text.split("\n"))
    return f"字数: {chars}, 词数: {words}, 行数: {lines}"

tools = [knowledge_search, calculate, word_analyze]

# === 3. 构建 Agent ===

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个知识库问答助手。你可以：
1. 使用 knowledge_search 工具从知识库中搜索信息
2. 使用 calculate 工具进行数学计算
3. 使用 word_analyze 工具分析文本

请根据用户的问题选择合适的工具。如果知识库中没有相关信息，请如实告知。"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=6,
    handle_parsing_errors=True,
)

# === 4. 添加记忆 ===

session_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in session_store:
        session_store[session_id] = InMemoryChatMessageHistory()
    return session_store[session_id]

# 注意：AgentExecutor 的 input 键名是 "input"，历史键名是 "history"
agent_with_memory = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# === 5. 交互循环 ===

async def main():
    docs_dir = "./kb_docs"
    build_knowledge_base(docs_dir)

    print("\n" + "=" * 50)
    print("知识库问答 Agent（LangChain 版）")
    print("输入问题开始对话，输入 /quit 退出")
    print("=" * 50)

    session_id = "default"

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

        try:
            result = agent_with_memory.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}},
            )
            print(f"\nAI: {result['output']}")
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

### 6.3 对比：Week 4 手写 vs LangChain 重构

```
┌──────────────────────────────────────────────────────────────┐
│  对比维度        │  Week 4 手写    │  LangChain 重构          │
│─────────────────┼─────────────────┼─────────────────────────│
│  代码行数        │  ~500 行        │  ~200 行                 │
│  Embedding 调用  │  手动 httpx     │  OpenAIEmbeddings        │
│  向量数据库      │  手动 ChromaDB  │  Chroma.from_documents   │
│  文档切分        │  手动 TextSplitter │  RecursiveTextSplitter │
│  RAG 链         │  手动拼接        │  LCEL 管道               │
│  Agent 循环     │  手动 ReAct     │  AgentExecutor           │
│  对话记忆       │  手动 history   │  RunnableWithHistory     │
│  流式输出       │  手动 SSE 解析  │  chain.stream()          │
│  工具定义       │  手动 JSON Schema │  @tool 装饰器           │
│  异常处理       │  手动 try/catch │  with_fallbacks/retry    │
│─────────────────┼─────────────────┼─────────────────────────│
│  可控性          │  ★★★★★        │  ★★★                   │
│  开发速度        │  ★★★          │  ★★★★★                │
│  可维护性        │  ★★★          │  ★★★★                  │
│  学习曲线        │  ★★           │  ★★★★                  │
└──────────────────────────────────────────────────────────────┘
```

### Day 6 练习

1. 为知识库 Agent 添加一个 `summarize` 工具——输入文件路径，输出文件内容摘要
2. 用 `TokenCountCallback` 监控 Agent 的 Token 消耗，统计每次交互的总 Token 数
3. 添加文件持久化记忆，重启程序后能恢复之前的对话

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

```
Model I/O：
[ ] 能用 ChatOpenAI 连接智谱 GLM
[ ] 能用 ChatPromptTemplate 构建消息列表
[ ] 能用 StrOutputParser / JsonOutputParser 解析输出
[ ] 理解 LCEL 管道语法的含义

LCEL 链式组合：
[ ] 理解 Runnable 协议（invoke/stream/batch）
[ ] 能用 RunnableParallel 并行执行
[ ] 能用 RunnableLambda 包装自定义函数
[ ] 能用 RunnableBranch 实现条件分支
[ ] 能用 with_fallbacks 实现降级策略
[ ] 能用 set_debug 调试链

RAG 检索链：
[ ] 能用 DocumentLoader 加载文档
[ ] 能用 RecursiveCharacterTextSplitter 切分
[ ] 能用 Chroma 构建向量数据库
[ ] 能用 LCEL 构建 RAG 链
[ ] 了解 MultiQueryRetriever / CompressionRetriever

Agent 与 Tool：
[ ] 能用 @tool 定义工具
[ ] 能用 StructuredTool 定义参数化工具
[ ] 理解 ReAct Agent 和 Tool Calling Agent 的区别
[ ] 能用 AgentExecutor 管理循环
[ ] 能将 RAG 检索包装为 Tool

Memory 对话记忆：
[ ] 理解 ChatMessageHistory 的作用
[ ] 能用 RunnableWithMessageHistory 添加记忆
[ ] 理解 session_id 的作用
[ ] 能实现文件持久化记忆
[ ] 能实现窗口裁剪策略

Callbacks：
[ ] 理解 BaseCallbackHandler 的回调时机
[ ] 能自定义计时/日志回调
[ ] 能在流式输出中计数 Token
```

### 7.2 综合练习题

**项目：个人学习助手**

用 LangChain 构建一个个人学习助手，功能要求：

1. **知识库管理**：能加载并索引 Markdown 笔记文件
2. **智能问答**：基于知识库回答问题（RAG）
3. **代码运行**：能执行简单的 Python 代码片段
4. **记忆功能**：记住用户的学习偏好和进度
5. **Token 监控**：记录每次交互的 Token 消耗

技术要求：
- 使用 LCEL 管道语法
- 使用 `create_tool_calling_agent`
- 使用 `RunnableWithMessageHistory` + 文件持久化
- 添加自定义 Callback 监控 Token

> 完成这个项目后，你就同时有了"手写版"和"LangChain版"两个 Agent 作品，面试时可以对比讲解。

### 7.3 Week 5 回顾与 Week 6 预告

```
Week 5 学习路径回顾：

Day 1: Model I/O
  → ChatOpenAI、PromptTemplate、OutputParser、LCEL 初体验

Day 2: LCEL 链式组合
  → Runnable 协议、Parallel/Lambda/Branch、Fallback/Retry、调试

Day 3: RAG 检索链
  → DocumentLoader、TextSplitter、Chroma、高级检索策略

Day 4: Agent 与 Tool
  → @tool、StructuredTool、ReAct Agent、Tool Calling Agent

Day 5: Memory 对话记忆
  → ChatMessageHistory、RunnableWithMessageHistory、持久化、Agent+Memory

Day 6: Callbacks + 综合实战
  → 自定义 Callback、重构知识库 Agent、手写 vs 框架对比

你已经掌握的能力：
✓ 用 LangChain 组件构建 LLM 应用
✓ 用 LCEL 管道语法组合链
✓ 用 LangChain 实现 RAG
✓ 用 LangChain 构建 Agent
✓ 管理 Agent 对话记忆
✓ 监控 Agent 运行时行为

接下来（Week 6 预告）：
Week 6: LangGraph + 状态机 Agent
  → 从 ReAct 循环到图状态机
  → 节点、边、条件路由
  → 复杂工作流编排
```

---

## 本周知识图谱

```
LangChain 框架
├── Model I/O（Day 1）
│   ├── ChatOpenAI（连接智谱 GLM）
│   ├── ChatPromptTemplate
│   ├── OutputParser（Str/Json/List）
│   └── LCEL 管道语法
│
├── LCEL 链式组合（Day 2）
│   ├── Runnable 协议
│   ├── RunnableParallel
│   ├── RunnablePassthrough
│   ├── RunnableLambda
│   ├── RunnableBranch
│   ├── Fallback / Retry
│   └── 调试方法
│
├── RAG 检索链（Day 3）
│   ├── DocumentLoader
│   ├── TextSplitter
│   ├── Chroma 向量数据库
│   ├── Retriever
│   └── 高级检索策略
│
├── Agent 与 Tool（Day 4）
│   ├── @tool / StructuredTool
│   ├── ReAct Agent
│   ├── Tool Calling Agent
│   ├── AgentExecutor
│   └── RAG as Tool
│
├── Memory 对话记忆（Day 5）
│   ├── ChatMessageHistory
│   ├── RunnableWithMessageHistory
│   ├── 持久化存储
│   └── Agent + Memory
│
└── Callbacks + 实战（Day 6）
    ├── BaseCallbackHandler
    ├── 计时/日志回调
    ├── Token 计数
    └── 知识库 Agent 重构
```

## LangChain 速查表

```
┌──────────────────────────────────────────────────────────┐
│               LangChain 常用代码速查                       │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  连接模型：                                               │
│  llm = ChatOpenAI(model="glm-4-flash",                  │
│      base_url="https://open.bigmodel.cn/api/paas/v4",   │
│      api_key=os.environ["ZHIPU_API_KEY"])                │
│                                                          │
│  提示词模板：                                             │
│  prompt = ChatPromptTemplate.from_template("{x}")       │
│  chat = ChatPromptTemplate.from_messages([...])          │
│                                                          │
│  输出解析：                                               │
│  StrOutputParser()   → 直接取字符串                      │
│  JsonOutputParser()  → 解析为字典                        │
│                                                          │
│  LCEL 管道：                                             │
│  chain = prompt | llm | parser                           │
│  chain.invoke() / .stream() / .batch()                   │
│                                                          │
│  并行：                                                   │
│  RunnableParallel({"a": chain_a, "b": chain_b})          │
│                                                          │
│  RAG 链：                                                 │
│  ({"context": retriever | format, "q": pass})            │
│  | rag_prompt | llm | parser                             │
│                                                          │
│  Agent：                                                  │
│  @tool def my_tool(x: str) -> str: ...                  │
│  agent = create_tool_calling_agent(llm, tools, prompt)   │
│  executor = AgentExecutor(agent=agent, tools=tools)       │
│                                                          │
│  记忆：                                                   │
│  RunnableWithMessageHistory(chain, get_history,          │
│      input_messages_key="input",                         │
│      history_messages_key="history")                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
