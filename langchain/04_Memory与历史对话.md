# Day 4:Memory 与历史对话

> 今日主题:Memory 机制、历史对话管理、不同记忆策略对比
> 预计学习时长:2-3 小时
> 前置条件:已完成 Day 1-3,理解 LCEL 和消息类型

---

## 一、当日目标

1. 理解为什么需要 Memory,以及 LangChain v0.3 中 Memory 的现状
2. 掌握用 LCEL + MessagesPlaceholder 手动管理历史对话(推荐方式)
3. 了解不同记忆策略(Buffer、Window、Summary、Token Buffer)的区别
4. 实现一个带持久化记忆的对话机器人

---

## 二、核心概念讲解

### 2.1 为什么需要 Memory

LLM 本身是**无状态的**——每次调用都是独立的,模型不记得上一次说了什么。但对话应用需要"记住"历史,否则:

```
用户: 我叫张三
AI:   你好张三!
用户: 我叫什么?
AI:   抱歉,我不知道你叫什么。  ← 忘了!
```

解决方案:每次调用时把**历史对话**作为消息列表一起传入。Memory 就是管理这个历史列表的机制。

### 2.2 LangChain v0.3 中 Memory 的变化

**重要**:LangChain v0.3 中,旧的 `ConversationBufferMemory`、`ConversationChain` 等 Memory 类**已不推荐使用**。官方推荐的方式是:

> **用 LCEL + `MessagesPlaceholder` 手动管理历史消息**

原因:
- 旧的 Memory 类与 LCEL 不兼容,是遗留设计
- 手动管理历史更灵活、更透明,你能完全控制传入什么消息
- LangGraph(进阶)提供了更强大的状态管理方案

本教程会简要介绍旧 Memory 类(因为你在老代码中可能看到),但**重点教 LCEL 手动管理方式**。

### 2.3 手动管理历史(LCEL 方式)

核心模式:

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个助手。"),
    MessagesPlaceholder(variable_name="history"),  # 历史消息插这里
    ("human", "{question}"),                        # 当前问题
])

chain = prompt | model

# 维护一个历史列表
history = []

def chat(question):
    response = chain.invoke({"history": history, "question": question})
    # 把这一轮加入历史
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=response.content))
    return response.content
```

### 2.4 旧 Memory 策略(了解即可)

LangChain 历史上提供了多种 Memory 策略,各有适用场景:

| Memory 类型 | 策略 | 适用场景 |
|-------------|------|----------|
| `ConversationBufferMemory` | 保留所有历史 | 短对话 |
| `ConversationBufferWindowMemory` | 只保留最近 N 轮 | 控制上下文长度 |
| `ConversationSummaryMemory` | 用 LLM 总结历史 | 长对话 |
| `ConversationTokenBufferMemory` | 按 Token 数限制 | 精确控制 Token |

**为什么需要不同策略?** 因为 LLM 有**上下文窗口限制**(如 GPT-4o 是 128K tokens),历史太长会超限且增加成本。

### 2.5 手动实现 Window 策略

最实用的优化:只保留最近 N 轮对话:

```python
# 只保留最近 5 轮(10 条消息)
history = history[-10:]
```

### 2.6 手动实现 Summary 策略

当历史较长时,定期让 LLM 总结之前的对话:

```python
# 当历史超过 20 条时,让 LLM 总结
if len(history) > 20:
    summary = summarize_chain.invoke({"history": history})
    history = [SystemMessage(content=f"之前对话的摘要: {summary}")] + history[-4:]
```

### 2.7 持久化存储

对话重启后历史会丢失。要持久化,可以把历史存到文件或数据库:

```python
import json

# 保存
def save_history(history, filepath):
    data = [{"type": m.type, "content": m.content} for m in history]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 加载
def load_history(filepath):
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    history = []
    for m in data:
        if m["type"] == "human":
            history.append(HumanMessage(content=m["content"]))
        elif m["type"] == "ai":
            history.append(AIMessage(content=m["content"]))
        elif m["type"] == "system":
            history.append(SystemMessage(content=m["content"]))
    return history
```

---

## 三、代码示例

### 3.1 基础:手动管理历史对话

```python
"""
Day4 示例 1:手动管理历史对话(LCEL 推荐方式)
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的中文助手,回答简洁。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = prompt | model | StrOutputParser()

# 维护历史消息列表
history = [
    SystemMessage(content="你是一个友好的中文助手,回答简洁。"),
]

def chat(question: str) -> str:
    """单轮对话,自动维护历史"""
    # 调用模型,传入历史和当前问题
    answer = chain.invoke({"history": history[1:], "question": question})

    # 更新历史
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))

    return answer

# 测试多轮对话
print(f"AI: {chat('你好,我叫小明!')}")
print(f"AI: {chat('我喜欢吃火锅。')}")
print(f"AI: {chat('我叫什么名字?')}")          # 应该记得"小明"
print(f"AI: {chat('我喜欢吃什么?')}")            # 应该记得"火锅"

print("\n=== 当前历史消息 ===")
for msg in history:
    print(f"[{msg.type}] {msg.content}")
```

### 3.2 Window 策略:限制历史长度

```python
"""
Day4 示例 2:Window 策略 - 只保留最近 N 轮
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

WINDOW_SIZE = 3  # 保留最近 3 轮(6 条消息)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的中文助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = prompt | model | StrOutputParser()

history = []

def chat(question: str) -> str:
    # 只取最近 WINDOW_SIZE*2 条消息(每轮一问一答)
    recent_history = history[-(WINDOW_SIZE * 2):]

    answer = chain.invoke({"history": recent_history, "question": question})

    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))

    return answer

# 测试:问很多问题,早期信息会被遗忘
questions = [
    "记住密码是 123456",
    "今天天气怎么样?",
    "1+1 等于几?",
    "2+2 等于几?",
    "3+3 等于几?",
    "我的密码是多少?",  # 可能已经忘了,因为超过了窗口
]

for q in questions:
    print(f"我: {q}")
    print(f"AI: {chat(q)}\n")
```

### 3.3 Summary 策略:总结长历史

```python
"""
Day4 示例 3:Summary 策略 - 历史过长时自动总结
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# 主对话链
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的中文助手。{summary}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])
chat_chain = chat_prompt | model | StrOutputParser()

# 总结链
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", "请将以下对话历史总结为一段简洁的中文摘要,保留关键信息(如人名、偏好等)。"),
    ("human", "{history_text}"),
])
summary_chain = summary_prompt | model | StrOutputParser()

history = []
summary = ""  # 历史摘要
MAX_HISTORY_LENGTH = 6  # 超过 6 条消息就总结

def chat(question: str) -> str:
    global summary

    recent_history = history[-MAX_HISTORY_LENGTH:]

    answer = chat_chain.invoke({
        "history": recent_history,
        "question": question,
        "summary": f"之前对话摘要: {summary}" if summary else "",
    })

    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))

    # 历史过长时,总结较早的对话
    if len(history) > MAX_HISTORY_LENGTH * 2:
        old_messages = history[:-MAX_HISTORY_LENGTH]
        history_text = "\n".join(f"{m.type}: {m.content}" for m in old_messages)
        summary = summary_chain.invoke({"history_text": history_text})
        # 只保留最近的消息
        history[:] = history[-MAX_HISTORY_LENGTH:]
        print(f"[系统] 已生成摘要: {summary[:50]}...\n")

    return answer

# 测试
conversation = [
    "我叫小华,在华为工作",
    "我是做 HarmonyOS 开发的",
    "我用的语言主要是 ArkTS",
    "今天想聊聊 RAG 技术",
    "RAG 和微调有什么区别?",
    "那向量数据库怎么选?",
    "你还记得我是做什么的吗?",  # 靠摘要记住
]

for q in conversation:
    print(f"我: {q}")
    print(f"AI: {chat(q)}\n")
```

### 3.4 持久化:保存和加载对话

```python
"""
Day4 示例 4:对话持久化 - 保存到文件和加载
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, BaseMessage
)
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个友好的中文助手。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])
chain = prompt | model | StrOutputParser()

def save_history(history: list[BaseMessage], filepath: str) -> None:
    """保存历史消息到 JSON 文件"""
    data = [{"type": m.type, "content": m.content} for m in history]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"历史已保存到 {filepath}({len(history)} 条消息)")

def load_history(filepath: str) -> list[BaseMessage]:
    """从 JSON 文件加载历史消息"""
    type_map = {
        "human": HumanMessage,
        "ai": AIMessage,
        "system": SystemMessage,
    }
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    history = []
    for m in data:
        msg_class = type_map.get(m["type"])
        if msg_class:
            history.append(msg_class(content=m["content"]))
    print(f"已从 {filepath} 加载 {len(history)} 条消息")
    return history

# 模拟对话
history = []

def chat(question: str) -> str:
    answer = chain.invoke({"history": history, "question": question})
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))
    return answer

# 第一轮对话
print(f"AI: {chat('我叫小王,今天想学 LangChain')}")
print(f"AI: {chat('LangChain 有什么用?')}")

# 保存
save_history(history, "chat_history.json")

# 模拟程序重启:重新加载历史
print("\n=== 模拟程序重启 ===")
new_history = load_history("chat_history.json")

# 用新历史继续对话
def chat_with_history(question: str, hist: list) -> str:
    answer = chain.invoke({"history": hist, "question": question})
    hist.append(HumanMessage(content=question))
    hist.append(AIMessage(content=answer))
    return answer

print(f"AI: {chat_with_history('我叫什么名字?', new_history)}")  # 应该记得"小王"
```

### 3.5 综合示例:带系统设定的对话机器人

```python
"""
Day4 示例 5:综合 - 可配置人设的对话机器人
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.8)

class ChatBot:
    """带历史管理的对话机器人"""

    def __init__(self, persona: str, model_name: str = "gpt-4o-mini", window: int = 5):
        self.model = ChatOpenAI(model=model_name, temperature=0.8)
        self.window = window  # 保留轮数
        self.history: list = []

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", persona),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}"),
        ])
        self.chain = self.prompt | self.model | StrOutputParser()

    def chat(self, question: str) -> str:
        # Window 策略:只取最近 window 轮
        recent = self.history[-(self.window * 2):]
        answer = self.chain.invoke({"history": recent, "question": question})
        self.history.append(HumanMessage(content=question))
        self.history.append(AIMessage(content=answer))
        return answer

    def clear_history(self):
        """清空历史"""
        self.history = []
        print("[系统] 历史已清空")

# 使用:创建一个"李白"人设的机器人
li_bai_bot = ChatBot(
    persona="你是李白,唐代诗人。用古风回答问题,偶尔引用自己的诗句。回答要简洁。",
    window=3,
)

print("=== 李白机器人(输入 quit 退出)===")
questions = [
    "你是谁?",
    "最近有什么新作?",
    "你喜欢喝酒吗?",
]

for q in questions:
    print(f"我: {q}")
    print(f"李白: {li_bai_bot.chat(q)}\n")

# 清空历史后,机器人会忘记之前说的
li_bai_bot.clear_history()
print(f"我: 我们刚才聊了什么?")
print(f"李白: {li_bai_bot.chat('我们刚才聊了什么?')}")  # 应该不记得
```

---

## 四、当日小结

| 要点 | 内容 |
|------|------|
| Memory 的必要性 | LLM 无状态,需手动传入历史消息 |
| v0.3 推荐方式 | LCEL + `MessagesPlaceholder` 手动管理历史,而非旧的 Memory 类 |
| 核心模式 | 维护 `history` 列表,每次 `invoke` 时传入,调用后追加新消息 |
| Window 策略 | `history[-(N*2):]` 只保留最近 N 轮,控制上下文长度 |
| Summary 策略 | 历史过长时让 LLM 总结,用摘要替代旧消息 |
| 持久化 | 把历史序列化为 JSON 存文件,重启后加载 |
| MessagesPlaceholder | 在模板中预留历史消息的插入位置 |

---

## 五、练习题

### 选择题

**1. LangChain v0.3 中,管理历史对话的推荐方式是?**
A. 使用 `ConversationBufferMemory` 类
B. 使用 `ConversationChain`
C. 用 LCEL + `MessagesPlaceholder` 手动管理
D. 不需要管理,模型自带记忆

**2. LLM 为什么需要 Memory?**
A. 模型训练数据不够
B. LLM 是无状态的,每次调用独立,不记得之前的对话
C. 为了节省 Token
D. 为了提高准确率

**3. Window 策略(只保留最近 N 轮)的主要目的是?**
A. 提高回答质量
B. 控制上下文长度,避免超过 Token 限制
C. 增加历史信息
D. 加快模型推理速度

**4. `MessagesPlaceholder` 在 `ChatPromptTemplate` 中的作用是?**
A. 创建空消息
B. 在模板中预留位置,运行时插入消息列表(如历史对话)
C. 替换 system 消息
D. 删除多余消息

### 填空题

**5.** 要只保留历史列表 `history` 中最近 5 轮对话(10 条消息),代码应写为 `history = history[______]`。

**6.** 每轮对话后,需要把 `______` 和 `______` 两种消息追加到历史列表中。

### 编程题

**7.** 编写一个带 Window 策略(保留最近 3 轮)的对话机器人,系统设定为"你是一个 Python 编程老师"。进行 5 轮对话,验证机器人能记住最近 3 轮的内容但会忘记更早的内容。

**8.** 扩展第 7 题,给机器人增加 `save_session(filepath)` 和 `load_session(filepath)` 方法,实现对话历史的 JSON 持久化。模拟"程序重启"后能恢复之前的对话上下文。

---

## 六、练习题答案

### 1. 答案:C
**解析**:LangChain v0.3 不再推荐旧的 `ConversationBufferMemory`、`ConversationChain` 等(它们与 LCEL 不兼容)。官方推荐用 LCEL + `MessagesPlaceholder` 手动管理历史消息,更灵活透明。

### 2. 答案:B
**解析**:LLM 本身是无状态的,每次 API 调用都是独立的。要让模型"记住"之前说了什么,必须把历史消息作为上下文一起传入。Memory 就是管理这个历史的机制。

### 3. 答案:B
**解析**:LLM 有上下文窗口限制(如 128K tokens),历史太长会超限并增加成本。Window 策略只保留最近 N 轮,在记忆力和成本之间取平衡。

### 4. 答案:B
**解析**:`MessagesPlaceholder(variable_name="history")` 在模板中预留一个位置,运行时 `invoke({"history": [消息列表]})` 会在该位置插入这些消息。

### 5. 答案:`-10:`
**解析**:`history[-10:]` 取列表最后 10 个元素,即最近 5 轮(每轮一问一答共 10 条消息)。

### 6. 答案:`HumanMessage`、`AIMessage`
**解析**:每轮对话包含用户的问题(`HumanMessage`)和 AI 的回复(`AIMessage`),两者都要追加到历史列表中,下次调用时一起传入。

### 7. 参考答案:

```python
"""
练习题 7:带 Window 策略的 Python 编程老师
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个耐心的 Python 编程老师,回答简洁。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = prompt | model | StrOutputParser()

history = []
WINDOW = 3  # 保留最近 3 轮

def chat(question: str) -> str:
    recent = history[-(WINDOW * 2):]
    answer = chain.invoke({"history": recent, "question": question})
    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))
    return answer

# 5 轮对话
conversations = [
    "Python 的列表和元组有什么区别?",
    "字典是怎么存储数据的?",
    "集合(set)有什么用?",
    "那列表和元组的区别你还记得吗?",  # 第4轮,还在 3 轮窗口内
    "我最开始问的第一个问题是什么?",   # 第5轮,第1轮已超出窗口
]

for i, q in enumerate(conversations, 1):
    print(f"第{i}轮 我: {q}")
    print(f"老师: {chat(q)}\n")
```

### 8. 参考答案:

```python
"""
练习题 8:带持久化的 Python 编程老师
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser

model = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个耐心的 Python 编程老师,回答简洁。"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])

chain = prompt | model | StrOutputParser()

class ProgrammingTeacher:
    def __init__(self, window: int = 3):
        self.history = []
        self.window = window

    def chat(self, question: str) -> str:
        recent = self.history[-(self.window * 2):]
        answer = chain.invoke({"history": recent, "question": question})
        self.history.append(HumanMessage(content=question))
        self.history.append(AIMessage(content=answer))
        return answer

    def save_session(self, filepath: str):
        data = [{"type": m.type, "content": m.content} for m in self.history]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[系统] 已保存 {len(self.history)} 条消息到 {filepath}")

    def load_session(self, filepath: str):
        type_map = {"human": HumanMessage, "ai": AIMessage}
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.history = [type_map[m["type"]](content=m["content"]) for m in data if m["type"] in type_map]
        print(f"[系统] 已加载 {len(self.history)} 条消息")

# 第一轮对话
teacher = ProgrammingTeacher(window=3)
print(f"老师: {teacher.chat('Python 的装饰器是什么?')}")
print(f"老师: {teacher.chat('给我一个简单例子')}")
teacher.save_session("teacher_session.json")

# 模拟重启
print("\n=== 程序重启,加载历史 ===")
new_teacher = ProgrammingTeacher(window=3)
new_teacher.load_session("teacher_session.json")
print(f"老师: {new_teacher.chat('你刚才举的例子是什么?')}")  # 应该记得
```

---

**恭喜完成 Day 4!** 明天进入 RAG 篇章,学习如何加载和切分文档。
