# Day 3:Chains 与 LCEL 表达式语言

> 今日主题:LCEL(LangChain Expression Language)深入、Runnable 接口、复杂链的构建
> 预计学习时长:2-3 小时
> 前置条件:已完成 Day 1 和 Day 2,理解 Prompt、Model、Parser 的基本用法

---

## 一、当日目标

1. 深入理解 LCEL 的设计理念和核心优势
2. 掌握 Runnable 接口的标准方法(invoke/stream/batch/ainvoke 等)
3. 学会使用 `RunnablePassthrough`、`RunnableLambda`、`RunnableParallel` 等组合工具
4. 能用 LCEL 构建包含数据流转的复杂链

---

## 二、核心概念讲解

### 2.1 LCEL 是什么

LCEL(LangChain Expression Language)是 LangChain v0.3+ 推荐的链构建方式。它用 `|` 管道符把 Runnable 组件串联起来:

```python
chain = prompt | model | parser
```

**为什么推荐 LCEL 而非旧的 `LLMChain`?**

LCEL 构建的链自动获得以下能力(无需额外代码):

| 能力 | 说明 |
|------|------|
| 流式输出 | `chain.stream()` 逐块输出,无需特殊处理 |
| 批量处理 | `chain.batch([input1, input2])` 并发处理多个输入 |
| 异步支持 | `chain.ainvoke()` / `chain.abatch()` 异步调用 |
| 后台执行 | `chain.with_config(callbacks=...)` 支持回调 |
| 重试与回退 | `.with_retry()` 自动重试失败请求 |
| 可观测性 | 自动集成 LangSmith 追踪 |
| 配置灵活 | `.with_config()` 运行时配置 |

### 2.2 Runnable 接口

LCEL 中所有组件都实现了 `Runnable` 接口,提供统一的方法:

| 方法 | 说明 | 同步/异步 |
|------|------|-----------|
| `invoke(input)` | 处理单个输入,返回完整输出 | 同步 |
| `stream(input)` | 处理单个输入,返回输出块迭代器 | 同步 |
| `batch(inputs)` | 处理多个输入,返回输出列表 | 同步 |
| `ainvoke(input)` | 同 invoke,异步版本 | 异步 |
| `astream(input)` | 同 stream,异步版本 | 异步 |
| `abatch(inputs)` | 同 batch,异步版本 | 异步 |
| `astream_events(input)` | 流式输出并捕获中间事件 | 异步 |

**核心思想**:任何 Runnable 都可以用 `|` 连接,只要前一个的输出类型匹配后一个的输入类型。

### 2.3 RunnablePassthrough

`RunnablePassthrough` 是一个"透传"组件:它把输入原样传给输出。乍看没用,但在组合链时非常重要——它让你能在链中**同时传递原始数据和加工数据**。

```python
from langchain_core.runnables import RunnablePassthrough

# 输入 {"question": "..."} -> 输出 {"question": "..."}(原样透传)
chain = RunnablePassthrough()
```

典型用法:在 RAG 中,既要检索文档,又要保留原始问题:

```python
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
)
```

这里 `RunnablePassthrough()` 把原始的 question 字符串透传给 `question` 字段,而 `retriever` 用 question 去检索文档。

### 2.4 RunnableLambda

`RunnableLambda` 把一个普通 Python 函数包装成 Runnable,这样就能用 `|` 连接:

```python
from langchain_core.runnables import RunnableLambda

def to_upper(text: str) -> str:
    return text.upper()

chain = RunnableLambda(to_upper)
# 或者在链中
chain = prompt | model | RunnableLambda(lambda x: x.content.upper())
```

### 2.5 RunnableParallel

`RunnableParallel` 同时执行多个 Runnable,把结果合并成一个字典:

```python
from langchain_core.runnables import RunnableParallel

parallel = RunnableParallel(
    summary=lambda x: summarize(x),
    keywords=lambda x: extract_keywords(x),
)
# 输入 text -> 输出 {"summary": ..., "keywords": ...}
```

在 LCEL 中,用字典语法是 `RunnableParallel` 的简写:
```python
chain = {"summary": chain1, "keywords": chain2} | merge_chain
```
等价于 `RunnableParallel(summary=chain1, keywords=chain2) | merge_chain`。

### 2.6 链中的数据流转

理解 LCEL 链的关键是**追踪数据类型**:

```
invoke({"question": "什么是RAG"})
  -> prompt.invoke({"question": "什么是RAG"}) -> ChatPromptValue(消息列表)
  -> model.invoke(ChatPromptValue) -> AIMessage(content="...")
  -> parser.invoke(AIMessage) -> "RAG是..."(字符串)
```

每一步的输出就是下一步的输入。如果类型不匹配,链就会报错。

---

## 三、代码示例

### 3.1 Runnable 基础方法对比

```python
"""
Day3 示例 1:Runnable 的 invoke / stream / batch
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个中文助手,用一句话回答。"),
    ("human", "{question}"),
])

chain = prompt | model | StrOutputParser()

# 1. invoke: 单次调用
print("=== invoke ===")
result = chain.invoke({"question": "什么是 Python?"})
print(result)

# 2. stream: 流式输出
print("\n=== stream ===")
for chunk in chain.stream({"question": "什么是 Java?"}):
    print(chunk, end="", flush=True)
print()

# 3. batch: 批量处理
print("\n=== batch ===")
questions = [
    {"question": "什么是 C++?"},
    {"question": "什么是 Go?"},
    {"question": "什么是 Rust?"},
]
results = chain.batch(questions)
for q, r in zip(questions, results):
    print(f"Q: {q['question']} -> A: {r}")
```

### 3.2 RunnablePassthrough 透传

```python
"""
Day3 示例 2:RunnablePassthrough 保留原始输入
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个翻译助手,将用户输入翻译成英文。"),
    ("human", "{text}"),
])

# 场景:用户输入一个字符串,我们要同时保留原文和翻译
chain = (
    # RunnablePassthrough 把原始字符串放到 "original" 字段
    # 同时把原始字符串也放到 "text" 字段供 prompt 使用
    {
        "original": RunnablePassthrough(),
        "text": RunnablePassthrough(),
    }
    | prompt
    | model
    | StrOutputParser()
)

result = chain.invoke("今天天气真好")
print(f"注意: 这种写法的结果只是翻译后的字符串: {result}")

# 如果想同时拿到原文和翻译,需要用 RunnableParallel 分开
from langchain_core.runnables import RunnableParallel

chain2 = RunnableParallel(
    original=RunnablePassthrough(),
    translation=prompt | model | StrOutputParser(),
)

result2 = chain2.invoke("今天天气真好")
print(f"\n原文: {result2['original']}")
print(f"翻译: {result2['translation']}")
```

### 3.3 RunnableLambda 自定义处理

```python
"""
Day3 示例 3:用 RunnableLambda 插入自定义逻辑
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
import json

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个天气助手。根据城市名返回该城市的虚构天气信息,用 JSON 格式:{{\"city\": \"...\", \"temp\": 数字, \"condition\": \"...\"}}"),
    ("human", "{city}"),
])

# 自定义函数:把 JSON 字符串解析后格式化输出
def format_weather(weather_json_str: str) -> str:
    """解析 LLM 返回的 JSON 并格式化"""
    try:
        data = json.loads(weather_json_str)
        return (
            f"城市: {data.get('city', '未知')}\n"
            f"温度: {data.get('temp', '未知')}°C\n"
            f"天气: {data.get('condition', '未知')}"
        )
    except json.JSONDecodeError as e:
        return f"解析失败: {e}\n原始输出: {weather_json_str}"

# 用 RunnableLambda 把普通函数包装成 Runnable
chain = (
    prompt
    | model
    | StrOutputParser()
    | RunnableLambda(format_weather)
)

result = chain.invoke({"city": "北京"})
print(result)
```

### 3.4 RunnableParallel 并行执行

```python
"""
Day3 示例 4:RunnableParallel 同时生成摘要和关键词
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, CommaSeparatedListOutputParser
from langchain_core.runnables import RunnableParallel

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 摘要链
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "用一句话总结以下文本。"),
    ("human", "{text}"),
])
summary_chain = summary_prompt | model | StrOutputParser()

# 关键词链
keywords_prompt = ChatPromptTemplate.from_messages([
    ("system", "从以下文本中提取 3-5 个关键词。{format_instructions}"),
    ("human", "{text}"),
])
keywords_parser = CommaSeparatedListOutputParser()
keywords_prompt = keywords_prompt.partial(
    format_instructions=keywords_parser.get_format_instructions()
)
keywords_chain = keywords_prompt | model | keywords_parser

# 并行执行
parallel_chain = RunnableParallel(
    summary=summary_chain,
    keywords=keywords_chain,
)

text = """
LangChain 是一个用于构建 LLM 应用的开源框架。
它提供了 Prompt 管理、链式调用、RAG 检索、Agent 工具调用等功能。
LangChain 支持多种大模型,包括 OpenAI、Anthropic 等。
"""

result = parallel_chain.invoke({"text": text})
print("=== 摘要 ===")
print(result["summary"])
print("\n=== 关键词 ===")
print(result["keywords"])
```

### 3.5 复杂链:多步推理管道

```python
"""
Day3 示例 5:多步推理 - 先分类再回答
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 第一步:分类问题类型
classify_prompt = ChatPromptTemplate.from_messages([
    ("system", "将用户问题分类为以下类别之一,只输出类别名:技术/生活/科学/其他"),
    ("human", "{question}"),
])
classify_chain = classify_prompt | model | StrOutputParser()

# 第二步:根据类别选择不同的回答风格
answer_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{style}助手,用对应的风格回答问题。"),
    ("human", "问题类别: {category}\n问题: {question}"),
])
answer_chain = answer_prompt | model | StrOutputParser()

# 组合:先分类,再根据分类结果回答
def build_answer_input(input_data):
    """把分类结果和原始问题组合成回答链的输入"""
    return {
        "category": input_data["category"],
        "question": input_data["question"],
        "style": {
            "技术": "严谨专业的技术",
            "生活": "亲切温暖的生活",
            "科学": "深入浅出的科学",
            "其他": "通用",
        }.get(input_data["category"], "通用"),
    }

full_chain = (
    # 同时保留原始问题和分类结果
    {
        "question": RunnablePassthrough() | (lambda x: x["question"] if isinstance(x, dict) else x),
        "category": classify_chain,
    }
    | RunnableLambda(build_answer_input)
    | answer_chain
)

# 测试
questions = [
    {"question": "Python 的 GIL 是什么?"},
    {"question": "怎么做出好吃的红烧肉?"},
    {"question": "黑洞是怎么形成的?"},
]

for q in questions:
    print(f"\n问题: {q['question']}")
    result = full_chain.invoke(q)
    print(f"回答: {result}")
```

### 3.6 异步与重试

```python
"""
Day3 示例 6:异步调用与自动重试
"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "用一句话回答。"),
    ("human", "{question}"),
])

# 带重试机制的链
chain = (
    prompt
    | model
    | StrOutputParser()
).with_retry(stop_after_attempt=3)

async def main():
    # 异步单次调用
    print("=== ainvoke ===")
    result = await chain.ainvoke({"question": "什么是异步编程?"})
    print(result)

    # 异步批量调用
    print("\n=== abatch ===")
    questions = [
        {"question": "什么是协程?"},
        {"question": "什么是事件循环?"},
        {"question": "什么是 async/await?"},
    ]
    results = await chain.abatch(questions)
    for q, r in zip(questions, results):
        print(f"Q: {q['question']} -> A: {r}")

asyncio.run(main())
```

---

## 四、当日小结

| 要点 | 内容 |
|------|------|
| LCEL 优势 | 自动支持流式、批量、异步、重试、可观测性 |
| Runnable 接口 | `invoke`/`stream`/`batch`/`ainvoke`/`abatch` 等统一方法 |
| `|` 管道符 | 串联 Runnable,前者的输出是后者的输入 |
| RunnablePassthrough | 透传输入,用于在链中保留原始数据 |
| RunnableLambda | 把普通函数包装成 Runnable |
| RunnableParallel | 并行执行多个链,结果合并为字典 |
| 字典语法简写 | `{"a": chain1, "b": chain2}` 等价于 `RunnableParallel(a=chain1, b=chain2)` |
| with_retry | `.with_retry(stop_after_attempt=N)` 自动重试 |

---

## 五、练习题

### 选择题

**1. LCEL 构建的链自动获得以下哪个能力?**
A. 自动缓存所有结果
B. 流式输出(stream)
C. 自动翻译语言
D. 自动优化 Prompt

**2. `RunnablePassthrough` 的作用是?**
A. 跳过当前步骤
B. 把输入原样传给输出
C. 删除输入中的某些字段
D. 把输入转成 JSON

**3. 以下哪种写法等价于 `RunnableParallel(a=chain1, b=chain2)`?**
A. `[chain1, chain2]`
B. `(chain1, chain2)`
C. `{"a": chain1, "b": chain2}`
D. `chain1 + chain2`

**4. 如何让普通 Python 函数加入 LCEL 链?**
A. 直接用 `|` 连接
B. 用 `RunnableLambda` 包装
C. 用 `RunnablePassthrough` 包装
D. 用 `RunnableParallel` 包装

### 填空题

**5.** Runnable 接口的异步批量处理方法是 `______`。

**6.** 在 LCEL 中,链 `prompt | model | parser` 执行时,`prompt` 的输出类型是 ______(填 LangChain 数据类型名),它会作为 `model` 的输入。

### 编程题

**7.** 编写一个 LCEL 链,实现以下功能:
- 输入:一段中文文本
- 并行执行两个任务:(a) 翻译成英文 (b) 生成中文摘要
- 输出一个字典,包含 `english` 和 `summary` 两个字段
- 使用 `RunnableParallel` 和 `StrOutputParser`

**8.** 编写一个多步推理链:
- 第一步:让 LLM 判断用户问题是"事实性问题"还是"观点性问题",只输出类别名
- 第二步:根据类别,事实性问题用"严谨准确"风格回答,观点性问题用"开放讨论"风格回答
- 使用 `RunnableLambda` 在中间做数据转换
- 提示:用 `RunnablePassthrough` 保留原始问题

---

## 六、练习题答案

### 1. 答案:B
**解析**:LCEL 链自动支持流式输出(`stream`)、批量处理(`batch`)、异步(`ainvoke`/`abatch`)、重试(`with_retry`)等能力。不需要写额外代码。

### 2. 答案:B
**解析**:`RunnablePassthrough` 把输入原样传给输出。它常用于在并行组合中保留原始数据,例如 `{"context": retriever, "question": RunnablePassthrough()}`。

### 3. 答案:C
**解析**:在 LCEL 中,字典 `{"a": chain1, "b": chain2}` 是 `RunnableParallel(a=chain1, b=chain2)` 的语法糖,会并行执行两个链并合并结果。

### 4. 答案:B
**解析**:普通 Python 函数需要用 `RunnableLambda(func)` 包装成 Runnable,才能用 `|` 连接到链中。

### 5. 答案:`abatch`
**解析**:`batch` 是同步批量,`abatch` 是异步批量。命名规则:`a` 前缀表示 async。

### 6. 答案:ChatPromptValue(或 ChatPromptValue 实例 / 消息列表)
**解析**:`ChatPromptTemplate.invoke()` 返回一个 `ChatPromptValue` 对象,它内部包含消息列表,可以直接传给 `ChatOpenAI` 作为输入。

### 7. 参考答案:

```python
"""
练习题 7:并行翻译和摘要
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 翻译链
translate_prompt = ChatPromptTemplate.from_messages([
    ("system", "将以下中文文本翻译成英文,只输出译文。"),
    ("human", "{text}"),
])
translate_chain = translate_prompt | model | StrOutputParser()

# 摘要链
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "用一句话总结以下中文文本。"),
    ("human", "{text}"),
])
summary_chain = summary_prompt | model | StrOutputParser()

# 并行组合
# 注意:RunnableParallel 会把输入 {"text": "..."} 传给两个子链
parallel_chain = RunnableParallel(
    english=translate_chain,
    summary=summary_chain,
)

text = "LangChain 是一个用于构建 LLM 应用的开源框架,支持 Prompt 管理、链式调用、RAG 检索和 Agent 工具调用。"

result = parallel_chain.invoke({"text": text})
print(f"英文翻译: {result['english']}")
print(f"中文摘要: {result['summary']}")
```

### 8. 参考答案:

```python
"""
练习题 8:多步推理链 - 先分类再回答
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 分类链
classify_prompt = ChatPromptTemplate.from_messages([
    ("system", "判断用户问题是'事实性问题'还是'观点性问题',只输出这两个词之一。"),
    ("human", "{question}"),
])
classify_chain = classify_prompt | model | StrOutputParser()

# 回答链
answer_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{style}助手。"),
    ("human", "{question}"),
])
answer_chain = answer_prompt | model | StrOutputParser()

# 中间转换函数
def build_input(data):
    category = data["category"].strip()
    style = "严谨准确" if "事实" in category else "开放讨论"
    return {"question": data["question"], "style": style}

# 完整链
full_chain = (
    # 同时获取原始问题和分类结果
    {
        "question": lambda x: x["question"],
        "category": classify_chain,
    }
    | RunnableLambda(build_input)
    | answer_chain
)

# 测试
test_questions = [
    {"question": "地球到太阳有多远?"},
    {"question": "你觉得人工智能会取代人类吗?"},
]

for q in test_questions:
    print(f"\n问题: {q['question']}")
    result = full_chain.invoke(q)
    print(f"回答: {result}")
```

---

**恭喜完成 Day 3!** 你已经掌握了 LCEL 的核心。明天我们将学习 Memory(记忆),让对话机器人能记住历史。
