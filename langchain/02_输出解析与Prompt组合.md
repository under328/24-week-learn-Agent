# Day 2:Output Parsers 与 Prompt 组合

> 今日主题:Output Parsers(输出解析器)、消息类型详解、Prompt 组合(LCEL 入门)
> 预计学习时长:2-3 小时
> 前置条件:已完成 Day 1,能使用 ChatOpenAI 和 ChatPromptTemplate

---

## 一、当日目标

1. 理解为什么需要 Output Parsers,掌握常用的解析器类型
2. 深入理解消息类型,学会构造复杂对话
3. 学会用 LCEL 将 Prompt、Model、Parser 组合成链
4. 实现从 LLM 获取结构化数据(JSON、列表、Pydantic 对象)的能力

---

## 二、核心概念讲解

### 2.1 为什么需要 Output Parsers

LLM 的输出是**自然语言字符串**,但在实际应用中,我们往往需要**结构化数据**:

- 让 LLM 返回 JSON,供程序解析使用
- 让 LLM 返回一个列表,逐项展示
- 让 LLM 返回符合特定 Schema 的对象(如"用户信息")

Output Parsers 就是负责把 LLM 的文本输出**转换成结构化数据**的组件。它通常做两件事:
1. **格式指令**(format instructions):告诉 LLM 应该按什么格式输出(通常注入到 Prompt 中)
2. **解析**(parse):把 LLM 的文本输出解析成目标数据结构

### 2.2 常用 Output Parsers

| 解析器 | 作用 | 输出类型 |
|--------|------|----------|
| `StrOutputParser` | 最简单,直接提取消息的 content 字符串 | `str` |
| `JsonOutputParser` | 解析 JSON,可配合 Pydantic 定义 Schema | `dict` 或 Pydantic 对象 |
| `PydanticOutputParser` | 用 Pydantic 模型校验并解析输出 | Pydantic 对象 |
| `CommaSeparatedListOutputParser` | 解析逗号分隔的列表 | `list[str]` |
| `XMLOutputParser` | 解析 XML 格式输出 | `dict` |

### 2.3 StrOutputParser

最常用的解析器,把 `AIMessage` 对象转成纯字符串:

```python
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()
# AIMessage(content="你好") -> "你好"
```

这样 `chain = prompt | model | StrOutputParser()` 的输出就直接是字符串,不用再 `.content`。

### 2.4 PydanticOutputParser 与 JsonOutputParser

当你需要 LLM 返回结构化数据时,用 Pydantic 定义 Schema:

```python
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser

class Movie(BaseModel):
    title: str = Field(description="电影名称")
    director: str = Field(description="导演姓名")
    year: int = Field(description="上映年份")

parser = JsonOutputParser(pydantic_object=Movie)
```

`parser.get_format_instructions()` 会生成一段格式说明,你把它放进 Prompt 里,LLM 就知道要返回什么格式的 JSON。

### 2.5 消息类型详解

回顾 Day1 的消息类型,这里深入讲解:

**SystemMessage**:设定全局行为,通常只放一条在开头
```python
SystemMessage(content="你是一个严谨的科学助手,回答要准确。")
```

**HumanMessage**:用户消息
```python
HumanMessage(content="光速是多少?")
```

**AIMessage**:AI 的回复,可以包含 `tool_calls`(工具调用信息)
```python
AIMessage(content="光速约为 299792458 米/秒。")
```

**ToolMessage**:工具调用的返回结果,必须带 `tool_call_id`
```python
ToolMessage(content="299792458", tool_call_id="call_xxx")
```

**占位符消息**(在模板中使用):
- `MessagesPlaceholder`:用于在模板中插入一个消息列表(如历史对话)
- 在 `from_messages` 中用 `("placeholder", "{history}")` 简写

### 2.6 LCEL 入门:管道组合

LCEL(LangChain Expression Language)用 `|` 把组件串联成链:

```python
chain = prompt | model | parser
```

执行 `chain.invoke(input)` 时,数据流是:
```
input -> prompt.invoke(input) -> 消息列表
     -> model.invoke(消息列表) -> AIMessage
     -> parser.invoke(AIMessage) -> 最终输出
```

每个组件都是一个 **Runnable**,都实现了 `invoke`、`stream`、`batch` 方法。这是 LCEL 的核心:所有组件遵循统一接口,可以自由组合。

---

## 三、代码示例

### 3.1 StrOutputParser 基础用法

```python
"""
Day2 示例 1:StrOutputParser 基础用法
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个中文助手,回答简洁。"),
    ("human", "{question}"),
])

# 不用 parser 时,输出是 AIMessage 对象
chain_no_parser = prompt | model
result = chain_no_parser.invoke({"question": "什么是 RAG?"})
print(f"类型: {type(result).__name__}")
print(f"内容: {result.content}")

# 用 StrOutputParser 后,输出是纯字符串
chain = prompt | model | StrOutputParser()
result = chain.invoke({"question": "什么是 RAG?"})
print(f"\n类型: {type(result).__name__}")
print(f"内容: {result}")
```

### 3.2 CommaSeparatedListOutputParser

```python
"""
Day2 示例 2:解析逗号分隔列表
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import CommaSeparatedListOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

parser = CommaSeparatedListOutputParser()

# 获取格式指令,告诉 LLM 按逗号分隔输出
format_instructions = parser.get_format_instructions()
print(f"格式指令: {format_instructions}\n")

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个知识丰富的助手。{format_instructions}"),
    ("human", "列出 {n} 种常见的编程语言。"),
])

# 部分填充变量(固定 format_instructions)
prompt = prompt.partial(format_instructions=format_instructions)

chain = prompt | model | parser

result = chain.invoke({"n": 5})
print(f"类型: {type(result).__name__}")
print(f"结果: {result}")

# 结果是一个列表,可以遍历
for i, lang in enumerate(result, 1):
    print(f"  {i}. {lang}")
```

### 3.3 PydanticOutputParser 获取结构化数据

```python
"""
Day2 示例 3:用 Pydantic 定义 Schema,获取结构化数据
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# 1. 定义数据模型(Schema)
class PersonInfo(BaseModel):
    name: str = Field(description="人物姓名")
    age: int = Field(description="人物年龄")
    occupation: str = Field(description="职业")
    skills: list[str] = Field(description="技能列表")

# 2. 创建解析器
parser = PydanticOutputParser(pydantic_object=PersonInfo)

# 3. 创建 Prompt,注入格式指令
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个信息提取助手。根据用户的描述提取人物信息。\n{format_instructions}"),
    ("human", "{description}"),
])

prompt = prompt.partial(format_instructions=parser.get_format_instructions())

# 4. 组成链
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | model | parser

# 5. 调用
description = "张三今年28岁,是一名全栈工程师,擅长 Python、JavaScript 和 Go。"
result = chain.invoke({"description": description})

print(f"类型: {type(result).__name__}")
print(f"姓名: {result.name}")
print(f"年龄: {result.age}")
print(f"职业: {result.occupation}")
print(f"技能: {result.skills}")
```

### 3.4 JsonOutputParser(更灵活的 JSON 解析)

```python
"""
Day2 示例 4:JsonOutputParser 解析 JSON
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class Book(BaseModel):
    title: str = Field(description="书名")
    author: str = Field(description="作者")
    summary: str = Field(description="一句话简介")
    rating: float = Field(description="推荐评分 0-10")

parser = JsonOutputParser(pydantic_object=Book)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个图书推荐专家。{format_instructions}"),
    ("human", "推荐一本关于{topic}的书。"),
]).partial(format_instructions=parser.get_format_instructions())

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
chain = prompt | model | parser

result = chain.invoke({"topic": "人工智能"})
print(f"类型: {type(result).__name__}")
print(f"书名: {result['title']}")
print(f"作者: {result['author']}")
print(f"简介: {result['summary']}")
print(f"评分: {result['rating']}")
```

> 注意:`JsonOutputParser` 的输出是 `dict`(即使传了 pydantic_object),而 `PydanticOutputParser` 的输出是 Pydantic 对象(有属性访问和校验)。根据需要选择。

### 3.5 MessagesPlaceholder 与历史对话

```python
"""
Day2 示例 5:用 MessagesPlaceholder 插入历史对话
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# MessagesPlaceholder 用于在模板中插入一个消息列表
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个耐心的中文助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

# 模拟历史对话
history = [
    HumanMessage(content="我叫小明。"),
    AIMessage(content="你好小明!有什么可以帮你的吗?"),
]

chain = prompt | model | StrOutputParser()

# 模型能"记住"历史,知道用户叫小明
result = chain.invoke({
    "history": history,
    "question": "我刚才告诉你我叫什么?",
})

print(result)
```

### 3.6 综合示例:结构化信息提取管道

```python
"""
Day2 示例 6:综合示例 - 从新闻文本提取结构化事件
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import Optional

class NewsEvent(BaseModel):
    title: str = Field(description="事件标题")
    date: str = Field(description="发生日期,格式 YYYY-MM-DD,无法判断则为空")
    location: Optional[str] = Field(default=None, description="发生地点")
    people: list[str] = Field(default_factory=list, description="涉及的人物列表")
    summary: str = Field(description="一句话摘要")

parser = PydanticOutputParser(pydantic_object=NewsEvent)

prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个新闻事件提取助手。从用户提供的新闻文本中提取结构化事件信息。
{format_instructions}
注意:日期格式为 YYYY-MM-DD,如果文本中没有明确日期,日期字段填空字符串。"""),
    ("human", "{news_text}"),
]).partial(format_instructions=parser.get_format_instructions())

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | model | parser

news = """
2026年3月15日,华为在上海发布了全新的 HarmonyOS 5.0 系统。
余承东在发布会上表示,新系统在性能和 AI 能力上有大幅提升。
此次发布会吸引了数千名开发者参与。
"""

event = chain.invoke({"news_text": news})

print("=== 提取结果 ===")
print(f"标题: {event.title}")
print(f"日期: {event.date}")
print(f"地点: {event.location}")
print(f"人物: {event.people}")
print(f"摘要: {event.summary}")
```

---

## 四、当日小结

| 要点 | 内容 |
|------|------|
| Output Parsers 作用 | 把 LLM 的文本输出转换成结构化数据 |
| StrOutputParser | 最常用,提取纯字符串,替代 `.content` |
| PydanticOutputParser | 用 Pydantic 定义 Schema,输出为 Pydantic 对象 |
| JsonOutputParser | 解析 JSON,输出为 dict,可配合 Pydantic |
| CommaSeparatedListOutputParser | 解析逗号分隔列表,输出为 `list[str]` |
| 格式指令 | `parser.get_format_instructions()` 生成格式说明,注入到 Prompt |
| MessagesPlaceholder | 在模板中插入消息列表(如历史对话) |
| LCEL 管道 | `prompt \| model \| parser`,数据自动流转 |

---

## 五、练习题

### 选择题

**1. `StrOutputParser` 的作用是什么?**
A. 把字符串转成 AIMessage
B. 把 AIMessage 的 content 提取为纯字符串
C. 把 JSON 转成字符串
D. 把列表转成字符串

**2. 以下哪个解析器适合让 LLM 返回符合特定 Schema 的 Pydantic 对象?**
A. `StrOutputParser`
B. `CommaSeparatedListOutputParser`
C. `PydanticOutputParser`
D. `JsonOutputParser`

**3. `parser.get_format_instructions()` 的返回值通常用在哪里?**
A. 作为模型的 temperature 参数
B. 作为 `invoke()` 的输入
C. 注入到 Prompt 模板中,告诉 LLM 输出格式
D. 作为最终输出打印

**4. `MessagesPlaceholder` 的作用是什么?**
A. 创建一个空消息
B. 在模板中插入一个消息列表(如历史对话)
C. 替换系统消息
D. 删除消息

### 填空题

**5.** LCEL 中,用 `______` 符号将 prompt、model、parser 串联成链。

**6.** `JsonOutputParser` 即使传入了 `pydantic_object` 参数,其输出类型仍然是 `______`(填 Python 数据类型)。

### 编程题

**7.** 编写一个 LangChain 程序:定义一个 Pydantic 模型 `Recipe`(菜谱),包含 `name`(菜名)、`ingredients`(食材列表)、`steps`(步骤列表)、`cook_time`(烹饪时间,分钟)。用 `PydanticOutputParser` 让 LLM 根据用户输入的菜名返回结构化菜谱,并打印各字段。

**8.** 扩展第 7 题,使用 `MessagesPlaceholder` 加入历史对话功能:用户可以先说"我做菜不想太复杂",然后再问菜谱,模型应结合上下文推荐简单菜谱。

---

## 六、练习题答案

### 1. 答案:B
**解析**:`StrOutputParser` 把 `AIMessage` 对象的 `content` 字段提取为纯字符串。它不做任何格式转换,只是方便你直接拿到字符串而不用写 `.content`。

### 2. 答案:C
**解析**:`PydanticOutputParser` 配合 Pydantic 模型,能校验输出并返回 Pydantic 对象(支持属性访问如 `result.name`)。`JsonOutputParser` 返回的是 dict,不是 Pydantic 对象。

### 3. 答案:C
**解析**:`get_format_instructions()` 返回一段文本说明(如"请输出符合以下 JSON Schema 的数据..."),需要注入到 Prompt 的 system 或 human 消息中,让 LLM 知道输出格式要求。

### 4. 答案:B
**解析**:`MessagesPlaceholder` 在模板中预留一个位置,运行时用消息列表填充,典型场景是插入历史对话。用法:`MessagesPlaceholder(variable_name="history")`。

### 5. 答案:`|`(管道符)
**解析**:LCEL 使用 `|` 管道符串联组件,如 `chain = prompt | model | parser`。数据从左到右流过每个组件。

### 6. 答案:dict(字典)
**解析**:`JsonOutputParser` 输出的是 Python dict,即使传了 `pydantic_object` 参数,它也只是用 Pydantic 生成格式指令,解析结果仍是 dict。如果需要 Pydantic 对象,应该用 `PydanticOutputParser`。

### 7. 参考答案:

```python
"""
练习题 7:结构化菜谱提取
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class Recipe(BaseModel):
    name: str = Field(description="菜名")
    ingredients: list[str] = Field(description="食材列表")
    steps: list[str] = Field(description="制作步骤")
    cook_time: int = Field(description="烹饪时间(分钟)")

parser = PydanticOutputParser(pydantic_object=Recipe)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个美食专家。根据菜名提供详细菜谱。\n{format_instructions}"),
    ("human", "请告诉我{dish}的做法。"),
]).partial(format_instructions=parser.get_format_instructions())

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | model | parser

recipe = chain.invoke({"dish": "番茄炒蛋"})

print(f"菜名: {recipe.name}")
print(f"烹饪时间: {recipe.cook_time} 分钟")
print(f"食材:")
for ing in recipe.ingredients:
    print(f"  - {ing}")
print(f"步骤:")
for i, step in enumerate(recipe.steps, 1):
    print(f"  {i}. {step}")
```

### 8. 参考答案:

```python
"""
练习题 8:带历史对话的菜谱推荐
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

class Recipe(BaseModel):
    name: str = Field(description="菜名")
    ingredients: list[str] = Field(description="食材列表")
    steps: list[str] = Field(description="制作步骤")
    cook_time: int = Field(description="烹饪时间(分钟)")

parser = PydanticOutputParser(pydantic_object=Recipe)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个美食专家。根据用户的需求推荐菜谱,要考虑用户之前提过的偏好。\n{format_instructions}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{dish}"),
]).partial(format_instructions=parser.get_format_instructions())

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | model | parser

# 模拟历史:用户说不想太复杂
history = [
    HumanMessage(content="我做菜不想太复杂,食材要少,步骤要简单。"),
    AIMessage(content="明白了!我会推荐简单易做的菜谱,食材少、步骤简洁。"),
]

recipe = chain.invoke({"dish": "推荐一道家常菜", "history": history})

print(f"菜名: {recipe.name}")
print(f"烹饪时间: {recipe.cook_time} 分钟")
print(f"食材:")
for ing in recipe.ingredients:
    print(f"  - {ing}")
print(f"步骤:")
for i, step in enumerate(recipe.steps, 1):
    print(f"  {i}. {step}")
```

---

**恭喜完成 Day 2!** 明天我们将深入学习 LCEL(LangChain Expression Language)和 Runnable 接口,理解链的底层机制。
