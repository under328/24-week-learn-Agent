# 第1月第2周：LLM 核心概念

> 适用对象：有前端开发经验，已完成 Week 1 Python 基础的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：深入理解 LLM 的工作机制，能熟练调用 LLM API 并理解每个参数的含义

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month1/week2
cd month1/week2

# 复用上周的虚拟环境或新建
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 安装本周依赖
pip install httpx pydantic tiktoken numpy matplotlib
pip freeze > requirements.txt
```

**关于 API Key**：本周需要调用 LLM API。推荐使用智谱 GLM（注册送免费额度）：

- 注册：https://open.bigmodel.cn/
- 免费额度足够本周学习使用
- 如果已有其他 API（OpenAI / 豆包 / 通义千问）也可以，代码会提供适配方式

---

## Day 1：Token 与分词机制

> Token 是 LLM 的"货币"——所有计费、上下文限制、性能优化都围绕 Token 展开。理解 Token 是理解 LLM 的第一步。

### 1.1 什么是 Token

```
Token ≠ 字符 ≠ 单词

LLM 处理文本的最小单位是 Token，而不是字符或单词。
不同模型的分词方式不同，同一个词的 Token 数也不同。

例子（GPT 系列的分词）：
  "Hello"           → 1 token:  [Hello]
  "Hello world"     → 2 tokens: [Hello] [world]
  "你好"             → 2 tokens: [你] [好]
  "人工智能"          → 3~5 tokens（取决于模型）
  "Agent"           → 1~2 tokens（取决于模型）

核心规则：
  - 1 个英文单词 ≈ 1~2 tokens
  - 1 个中文字 ≈ 1~3 tokens（中文 Token 效率低于英文）
  - 代码的 Token 效率较低（特殊符号多）
  - 数字和标点也占 Token
```

### 1.2 用 tiktoken 计算 Token 数

```python
# tiktoken 是 OpenAI 开源的分词库，适用于 GPT 系列
# 对于国产模型，分词方式不同，但概念和计算思路一致

import tiktoken

# 选择编码器（不同模型用不同编码器）
# cl100k_base: GPT-4 / GPT-3.5-turbo
# p50k_base:   GPT-3 (davinci 等)
# o200k_base:  GPT-4o 系列
encoding = tiktoken.get_encoding("cl100k_base")

# 基础用法
text = "Hello, world!"
tokens = encoding.encode(text)
print(f"原文: {text}")
print(f"Token IDs: {tokens}")         # [9906, 11, 1917, 0]
print(f"Token 数量: {len(tokens)}")    # 4

# 解码（Token ID → 文本）
decoded = encoding.decode(tokens)
print(f"解码: {decoded}")              # Hello, world!

# 逐个 Token 解码，直观看到每个 Token 对应什么
for token_id in tokens:
    print(f"  Token {token_id:>6} → {repr(encoding.decode([token_id]))}")

# === 中文 Token 分析 ===
chinese_texts = [
    "你好",
    "你好，世界！",
    "人工智能是未来的发展方向",
    "I love programming",
    "我爱编程",
]

print("\n=== 中英文 Token 对比 ===")
for text in chinese_texts:
    tokens = encoding.encode(text)
    print(f"  {text:<20} → {len(tokens):>2} tokens | {tokens}")

# === 代码的 Token 分析 ===
code_snippet = '''
def hello(name: str) -> str:
    """Say hello"""
    return f"Hello, {name}!"
'''
code_tokens = encoding.encode(code_snippet)
print(f"\n代码片段: {len(code_tokens)} tokens")
print(f"等价中文约: {len(code_tokens) * 2} 字")
```

### 1.3 Token 对 Agent 开发的影响

```python
# === 为什么 Agent 开发者必须关注 Token ===

# 1. 成本：API 按 Token 计费
def estimate_cost(input_tokens: int, output_tokens: int, model: str = "glm-4") -> float:
    """估算单次调用成本（人民币）"""
    pricing = {
        "glm-4":        {"input": 0.1 / 1000,  "output": 0.1 / 1000},   # 每千token
        "gpt-4":        {"input": 0.03 / 1000,  "output": 0.06 / 1000},  # 美元
        "gpt-4o":       {"input": 0.005 / 1000, "output": 0.015 / 1000}, # 美元
        "gpt-3.5-turbo":{"input": 0.0005 / 1000,"output": 0.0015 / 1000},
    }
    p = pricing.get(model, pricing["glm-4"])
    cost = input_tokens * p["input"] + output_tokens * p["output"]
    return round(cost, 6)

# 一次普通对话
print(f"单次对话成本: ¥{estimate_cost(500, 300, 'glm-4')}")
# Agent 多轮对话（10轮，上下文累积）
total_input = sum(500 + i * 200 for i in range(10))  # 上下文越来越长
total_output = 300 * 10
print(f"10轮对话成本: ¥{estimate_cost(total_input, total_output, 'glm-4')}")
# Agent 带工具调用（每次都带完整工具描述）
tool_overhead = 2000  # 工具定义的 token
total_input_with_tools = sum(tool_overhead + 500 + i * 200 for i in range(10))
print(f"10轮带工具对话: ¥{estimate_cost(total_input_with_tools, total_output, 'glm-4')}")

# 2. 上下文窗口限制
context_limits = {
    "gpt-3.5-turbo":  16385,
    "gpt-4":          8192,
    "gpt-4-32k":      32768,
    "gpt-4o":         128000,
    "glm-4":          128000,
    "claude-3.5":     200000,
}
# Agent 必须在限制内管理上下文，超出会报错或截断

# 3. 延迟：Token 越多，生成越慢
# 输出速度约 30-80 tokens/s，1000 tokens 输出需要 12-33 秒
```

### 1.4 实用 Token 计算器

```python
import tiktoken
from typing import Union

class TokenCounter:
    """Token 计算器 —— Agent 开发必备工具"""

    ENCODINGS = {
        "gpt-4":           "cl100k_base",
        "gpt-4o":          "o200k_base",
        "gpt-3.5-turbo":   "cl100k_base",
    }

    def __init__(self, model: str = "gpt-4"):
        encoding_name = self.ENCODINGS.get(model, "cl100k_base")
        self.encoding = tiktoken.get_encoding(encoding_name)
        self.model = model

    def count(self, text: str) -> int:
        """计算文本的 Token 数"""
        return len(self.encoding.encode(text))

    def count_messages(self, messages: list[dict]) -> int:
        """
        计算 Chat Messages 的总 Token 数（近似值）
        OpenAI 的实际计算包含额外的格式化开销，这里用近似公式
        """
        total = 0
        for msg in messages:
            # 每条消息的固定开销
            total += 4  # <im_start>{role/name}\n{content}<im_end>\n
            for key, value in msg.items():
                total += self.count(str(value))
                if key == "name":
                    total -= 1  # name 字段有特殊优惠
        total += 2  # 对话的固定开销
        return total

    def truncate(self, text: str, max_tokens: int) -> str:
        """截断文本到指定 Token 数以内"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        truncated = tokens[:max_tokens]
        return self.encoding.decode(truncated)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """
        将长文本按 Token 数分块（RAG 常用）
        chunk_size: 每块最大 Token 数
        overlap: 块之间的重叠 Token 数
        """
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunks.append(self.encoding.decode(chunk_tokens))
            start += chunk_size - overlap
        return chunks

# 使用示例
counter = TokenCounter("gpt-4")

text = "人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。"
print(f"Token 数: {counter.count(text)}")

messages = [
    {"role": "system", "content": "你是一个有帮助的AI助手"},
    {"role": "user", "content": "请解释什么是机器学习"},
    {"role": "assistant", "content": "机器学习是AI的一个子领域..."},
]
print(f"消息总 Token: {counter.count_messages(messages)}")

# 文本分块
long_text = "人工智能是..." * 200  # 模拟长文本
chunks = counter.chunk_text(long_text, chunk_size=100, overlap=20)
print(f"分块结果: {len(chunks)} 块，第一块 {counter.count(chunks[0])} tokens")
```

### 1.5 今日练习

1. 用 `tiktoken` 分析以下内容的 Token 数量，找出"最贵"的：
   - 一段 500 字中文文章
   - 一段 500 字英文文章
   - 一段 50 行 Python 代码
2. 写一个函数 `optimize_prompt(prompt: str, max_tokens: int) -> str`：如果 prompt 超过 max_tokens，从末尾截断并添加 `...[已截断]`
3. 写一个函数对比中英文的"Token 效率"（每个 Token 平均承载多少字符/字）

<details>
<summary>参考答案</summary>

```python
import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

# 1. 对比分析
chinese = "人工智能是计算机科学的一个重要分支，它致力于研究和开发能够模拟、延伸和扩展人类智能的理论、方法、技术及应用系统。人工智能技术的发展已经深刻地改变了人类社会的方方面面。" * 5
english = "Artificial intelligence is an important branch of computer science, dedicated to the research and development of theories, methods, technologies and application systems that can simulate, extend and expand human intelligence. The development of AI technology has profoundly changed all aspects of human society." * 3
code = '''
def fibonacci(n: int) -> list[int]:
    """Generate fibonacci sequence"""
    if n <= 0:
        return []
    if n == 1:
        return [0]
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

def is_prime(n: int) -> bool:
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True
''' * 10

for name, text in [("中文", chinese), ("英文", english), ("代码", code)]:
    tokens = count_tokens(text)
    chars = len(text)
    print(f"{name}: {chars} 字符, {tokens} tokens, 效率 {chars/tokens:.1f} 字符/token")

# 2. 截断优化
def optimize_prompt(prompt: str, max_tokens: int) -> str:
    tokens = encoding.encode(prompt)
    if len(tokens) <= max_tokens:
        return prompt
    truncated = tokens[:max_tokens - 5]  # 留空间给截断标记
    result = encoding.decode(truncated)
    return result + "...[已截断]"

# 3. Token 效率对比
def token_efficiency(texts: dict[str, str]) -> dict[str, float]:
    results = {}
    for name, text in texts.items():
        tokens = count_tokens(text)
        if tokens > 0:
            results[name] = len(text) / tokens
    return results

eff = token_efficiency({"中文": chinese, "英文": english, "代码": code})
for name, eff_val in eff.items():
    print(f"{name} Token 效率: {eff_val:.2f} 字符/token")
```

</details>

---

## Day 2：Context Window 与上下文管理

> Context Window 是 LLM 的"工作记忆"，所有对话历史、指令、工具定义都要塞进这个窗口。Agent 的很多难题本质上都是上下文管理问题。

### 2.1 Context Window 原理

```
┌─────────────────── Context Window ───────────────────┐
│                                                       │
│  [System Prompt] [工具定义] [对话历史] [当前用户输入]    │
│                                                       │
│  ──────────────────────────────────────────────────── │
│  总 Token 数 ≤ Context Window 上限                     │
│                                                       │
└───────────────────────────────────────────────────────┘

Context Window 的工作方式：
1. 每次调用 API，你要发送完整的上下文（LLM 没有记忆，靠你喂历史）
2. 输入 + 输出 的总 Token 不能超过 Context Window
3. 超出 → API 报错，或被静默截断（取决于模型）
```

```python
# 各模型 Context Window 对比
models_context = {
    # 模型名              上下文长度    单位: tokens
    "gpt-3.5-turbo":      16_385,
    "gpt-4":              8_192,
    "gpt-4-turbo":        128_000,
    "gpt-4o":             128_000,
    "glm-4":              128_000,
    "glm-4-flash":        128_000,
    "claude-3-haiku":     200_000,
    "claude-3.5-sonnet":  200_000,
    "gemini-1.5-pro":     1_000_000,  # 100万！
}

# 换算成"能装多少字"
for model, ctx in models_context.items():
    # 粗略估算：中文约 1.5 字/token，英文约 4 字符/token
    chinese_chars = int(ctx * 1.5)
    print(f"{model:<20} {ctx:>8,} tokens ≈ {chinese_chars:>10,} 中文字")
```

### 2.2 上下文累积问题

```python
# === Agent 对话中上下文会不断增长 ===

class ConversationSimulator:
    """模拟对话中的上下文增长"""

    def __init__(self, context_limit: int = 8192):
        self.context_limit = context_limit
        self.messages: list[dict] = []
        self.total_tokens = 0

    def add_message(self, role: str, content: str, token_count: int):
        self.messages.append({"role": role, "content": content})
        self.total_tokens += token_count + 4  # 4 是消息格式开销

    def is_over_limit(self) -> bool:
        return self.total_tokens > self.context_limit

    def status(self) -> str:
        usage_pct = self.total_tokens / self.context_limit * 100
        bar_filled = int(usage_pct / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        return f"[{bar}] {usage_pct:.1f}% ({self.total_tokens}/{self.context_limit})"

# 模拟一次 Agent 对话
sim = ConversationSimulator(context_limit=8192)

# 系统提示词
sim.add_message("system", "你是一个编程助手...", 50)

# 第1轮
sim.add_message("user", "帮我写一个排序函数", 20)
sim.add_message("assistant", "好的，这是一个快速排序...", 200)
print(f"第1轮后: {sim.status()}")

# 第3轮
sim.add_message("user", "能优化一下吗", 15)
sim.add_message("assistant", "可以用缓存优化...", 300)
sim.add_message("user", "加上单元测试", 10)
sim.add_message("assistant", "以下是测试用例...", 400)
print(f"第3轮后: {sim.status()}")

# 第6轮（假设每轮上下文增长 ~300 tokens）
for i in range(4, 7):
    sim.add_message("user", f"第{i}轮问题", 10)
    sim.add_message("assistant", f"第{i}轮回答..." * 30, 300)
print(f"第6轮后: {sim.status()}")

# 第10轮
for i in range(7, 11):
    sim.add_message("user", f"第{i}轮问题", 10)
    sim.add_message("assistant", f"第{i}轮回答..." * 30, 300)
print(f"第10轮后: {sim.status()}")
print(f"是否超限: {sim.is_over_limit()}")
```

### 2.3 上下文管理策略

```python
# === 策略1：滑动窗口（最简单） ===

def sliding_window(messages: list[dict], max_tokens: int, counter) -> list[dict]:
    """保留系统提示 + 最近的 N 轮对话"""
    if not messages:
        return messages

    # 始终保留系统提示
    system_msgs = [m for m in messages if m["role"] == "system"]
    chat_msgs = [m for m in messages if m["role"] != "system"]

    # 从最新消息开始，尽量多装
    result = []
    token_count = counter.count_messages(system_msgs)

    for msg in reversed(chat_msgs):
        msg_tokens = counter.count(str(msg["content"])) + 4
        if token_count + msg_tokens > max_tokens:
            break
        result.insert(0, msg)
        token_count += msg_tokens

    return system_msgs + result

# === 策略2：摘要压缩（更智能） ===

async def summarize_history(
    messages: list[dict],
    api_key: str,
    model: str = "glm-4-flash"
) -> str:
    """用 LLM 把早期对话压缩成摘要"""
    # 把需要压缩的消息拼成文本
    history_text = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"][:200]  # 截断过长的内容
        history_text += f"[{role}]: {content}\n"

    summary_prompt = f"""请将以下对话历史压缩为一段简洁的摘要，保留关键信息和结论：

{history_text}

摘要："""

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": summary_prompt}],
        "temperature": 0,
        "max_tokens": 500,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

# === 策略3：混合策略（Agent 实战最常用） ===

async def manage_context(
    messages: list[dict],
    max_tokens: int,
    counter,
    api_key: str,
    keep_recent: int = 4,  # 保留最近几轮
) -> list[dict]:
    """
    混合上下文管理：
    - 系统提示：始终保留
    - 早期对话：压缩为摘要
    - 最近 N 轮：完整保留
    """
    current_tokens = counter.count_messages(messages)
    if current_tokens <= max_tokens:
        return messages  # 不需要处理

    system_msgs = [m for m in messages if m["role"] == "system"]
    chat_msgs = [m for m in messages if m["role"] != "system"]

    # 分割：早期 + 最近
    split_point = max(0, len(chat_msgs) - keep_recent * 2)  # *2 因为一轮=2条消息
    old_msgs = chat_msgs[:split_point]
    recent_msgs = chat_msgs[split_point:]

    # 压缩早期消息
    if old_msgs:
        summary = await summarize_history(old_msgs, api_key)
        summary_msg = {
            "role": "system",
            "content": f"[对话历史摘要]\n{summary}"
        }
        return system_msgs + [summary_msg] + recent_msgs

    return system_msgs + recent_msgs
```

### 2.4 今日练习

1. 写一个 `ContextManager` 类，实现：
   - `add_message(role, content)` —— 添加消息并自动计算 token
   - `get_context(max_tokens)` —— 返回不超过限制的消息列表（滑动窗口策略）
   - `usage()` —— 返回当前上下文使用率（百分比）
2. 模拟一个 20 轮对话，观察上下文增长曲线，找出"安全轮次"（不超限的最大轮数）
3. 实现"优先级裁剪"：工具定义和系统提示不能裁剪，只能裁剪历史对话

<details>
<summary>参考答案</summary>

```python
import tiktoken
from typing import Optional

class ContextManager:
    def __init__(self, model: str = "gpt-4", context_limit: int = 8192):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.context_limit = context_limit
        self.messages: list[dict] = []

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def _count_message_tokens(self, msg: dict) -> int:
        return self._count_tokens(str(msg.get("content", ""))) + 4

    def add_message(self, role: str, content: str):
        msg = {"role": role, "content": content}
        self.messages.append(msg)

    def get_context(self, max_tokens: Optional[int] = None) -> list[dict]:
        limit = max_tokens or self.context_limit
        system_msgs = [m for m in self.messages if m["role"] == "system"]
        chat_msgs = [m for m in self.messages if m["role"] != "system"]

        # 计算系统消息占用
        system_tokens = sum(self._count_message_tokens(m) for m in system_msgs)
        remaining = limit - system_tokens - 2  # 2 为固定开销

        # 从最新开始填充
        result = []
        for msg in reversed(chat_msgs):
            tokens = self._count_message_tokens(msg)
            if remaining - tokens < 0:
                break
            result.insert(0, msg)
            remaining -= tokens

        return system_msgs + result

    def usage(self) -> float:
        total = sum(self._count_message_tokens(m) for m in self.messages) + 2
        return total / self.context_limit * 100

    def total_tokens(self) -> int:
        return sum(self._count_message_tokens(m) for m in self.messages) + 2

# 模拟 20 轮对话
import random

mgr = ContextManager(model="gpt-4", context_limit=8192)
mgr.add_message("system", "你是一个编程助手", 20)

for i in range(1, 21):
    user_len = random.randint(10, 50)
    assistant_len = random.randint(100, 400)
    mgr.add_message("user", f"第{i}轮问题" + "x" * user_len)
    mgr.add_message("assistant", f"第{i}轮回答" + "y" * assistant_len)
    context = mgr.get_context()
    actual_tokens = mgr.total_tokens()
    safe = "✓" if actual_tokens <= 8192 else "✗ 超限"
    print(f"第{i:>2}轮: 总{actual_tokens:>5} tokens, 上下文使用{mgr.usage():>5.1f}%, 裁剪后{len(context)}条消息 {safe}")

# 优先级裁剪：系统提示+工具定义不可裁剪
def priority_prune(messages: list[dict], max_tokens: int, counter) -> list[dict]:
    """系统消息和工具定义不可裁剪，只裁剪历史对话"""
    # 分离不可裁剪和可裁剪的消息
    protected = []
    prunable = []
    for m in messages:
        role = m.get("role", "")
        # 系统提示和含 tool 定义的不可裁剪
        if role == "system" or m.get("content", "").startswith("工具定义"):
            protected.append(m)
        else:
            prunable.append(m)

    # 计算不可裁剪部分占用
    protected_tokens = sum(counter.count(str(m["content"])) + 4 for m in protected)
    remaining = max_tokens - protected_tokens - 2

    # 从最新开始保留可裁剪消息
    result = []
    for msg in reversed(prunable):
        tokens = counter.count(str(msg["content"])) + 4
        if remaining - tokens < 0:
            break
        result.insert(0, msg)
        remaining -= tokens

    return protected + result
```

</details>

---

## Day 3：采样参数（Temperature、Top_P 等）

> 这些参数直接控制 LLM 输出的"创造力"和"确定性"。Agent 中不同场景需要不同参数。

### 3.1 核心参数详解

```
┌─────────────────────────────────────────────────┐
│           LLM 生成过程（简化）                     │
│                                                   │
│  输入 → Transformer → 每个位置输出一个概率分布      │
│       → 采样策略从中选一个 token → 重复直到结束      │
│                                                   │
│  Temperature 和 Top_P 控制的就是"采样策略"          │
└─────────────────────────────────────────────────┘
```

```python
# === Temperature（温度） ===

"""
温度控制概率分布的"尖锐程度"：

  temperature = 0    → 完全确定性（总是选概率最高的token）
  temperature = 0.3  → 非常保守（偏向高概率token）
  temperature = 0.7  → 适度随机（默认值，平衡创造力和准确性）
  temperature = 1.0  → 按原始概率采样
  temperature = 1.5  → 非常随机（更有多样性，但可能不连贯）
  temperature = 2.0  → 极度随机（基本不可用）

Agent 中的参数选择：
  - 代码生成：0 ~ 0.2（需要精确）
  - 文本摘要：0 ~ 0.3（需要准确）
  - 一般对话：0.5 ~ 0.7（平衡）
  - 创意写作：0.8 ~ 1.2（需要多样性）
  - 头脑风暴：1.0 ~ 1.5（最大化创意）
"""

# === Top_P（核采样 / Nucleus Sampling） ===

"""
Top_P 控制采样范围：
  top_p = 0.1  → 只从概率最高的前10%累积概率的token中选
  top_p = 0.5  → 前50%
  top_p = 0.9  → 前90%（默认值）
  top_p = 1.0  → 考虑所有token（不做过滤）

与 Temperature 的关系：
  两者可以组合使用，但通常只调一个
  Temperature 先调整分布形状，Top_P 再裁剪范围
  一般建议：调 Temperature 时 Top_P 保持 0.9~1.0
"""

# === 其他参数 ===

"""
top_k:      只从概率最高的 k 个 token 中选（OpenAI 不支持，Claude/Llama 支持）
max_tokens: 生成的最大 token 数（不是"达到就停"，是"不超过"）
frequency_penalty:  -2.0 ~ 2.0，惩罚已出现的token，减少重复
presence_penalty:   -2.0 ~ 2.0，惩罚已出现过的token（不管出现几次），鼓励新话题
stop:       停止词列表，遇到这些词就停止生成
"""
```

### 3.2 用数学直观理解 Temperature

```python
import numpy as np

# 模拟 LLM 输出的原始概率分布（logits → softmax）
def softmax(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """带温度的 softmax"""
    scaled = logits / temperature
    exp_scaled = np.exp(scaled - np.max(scaled))  # 数值稳定
    return exp_scaled / exp_scaled.sum()

# 假设模型对下一个 token 的原始得分（logits）
logits = np.array([5.0, 3.0, 1.0, 0.5, 0.1])  # 第一个token概率远高于其他
token_names = ["def", "class", "import", "from", "print"]

print("=== Temperature 对概率分布的影响 ===\n")
for temp in [0.1, 0.3, 0.7, 1.0, 1.5, 2.0]:
    probs = softmax(logits, temp)
    print(f"Temperature = {temp}")
    for name, prob in zip(token_names, probs):
        bar = "█" * int(prob * 50)
        print(f"  {name:>6}: {prob:.4f} {bar}")
    print()
```

### 3.3 实验对比：不同参数的实际效果

```python
import httpx
import json
import asyncio

async def compare_parameters(
    prompt: str,
    api_key: str,
    temperatures: list[float] = [0, 0.3, 0.7, 1.0, 1.5],
    model: str = "glm-4-flash"
):
    """用相同 prompt，不同 temperature 对比输出"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}

    async def call_once(temp: float) -> dict:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "max_tokens": 200,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return {
                "temperature": temp,
                "content": data["choices"][0]["message"]["content"],
                "usage": data.get("usage", {}),
            }

    # 并发调用不同 temperature
    tasks = [call_once(t) for t in temperatures]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, Exception):
            print(f"请求失败: {r}")
            continue
        print(f"\n{'='*50}")
        print(f"Temperature = {r['temperature']}")
        print(f"{'='*50}")
        print(r['content'])
        print(f"(Tokens: {r['usage']})")

# 使用示例（替换为你的 API Key）
# asyncio.run(compare_parameters(
#     "用一句话描述春天",
#     api_key="your-api-key",
#     temperatures=[0, 0.3, 0.7, 1.0, 1.5]
# ))
```

### 3.4 Agent 场景的参数配置模板

```python
from pydantic import BaseModel, Field
from typing import Optional

class AgentParameters(BaseModel):
    """Agent 不同场景的推荐参数配置"""

    temperature: float = Field(ge=0, le=2)
    top_p: float = Field(default=0.9, ge=0, le=1)
    max_tokens: int = Field(default=2048, gt=0)
    frequency_penalty: float = Field(default=0, ge=-2, le=2)
    presence_penalty: float = Field(default=0, ge=-2, le=2)

# 预设配置
AGENT_PRESETS = {
    "code_generation": AgentParameters(
        temperature=0.1, top_p=0.9, max_tokens=4096
    ),
    "code_review": AgentParameters(
        temperature=0.2, top_p=0.9, max_tokens=2048
    ),
    "qa_assistant": AgentParameters(
        temperature=0.5, top_p=0.9, max_tokens=1024
    ),
    "creative_writing": AgentParameters(
        temperature=0.9, top_p=0.95, max_tokens=2048
    ),
    "tool_calling": AgentParameters(
        temperature=0, top_p=1.0, max_tokens=1024  # 工具调用需要确定性
    ),
    "summarization": AgentParameters(
        temperature=0.2, top_p=0.9, max_tokens=500
    ),
    "classification": AgentParameters(
        temperature=0, top_p=1.0, max_tokens=50  # 分类只需要一个标签
    ),
}

def get_preset(task_type: str) -> AgentParameters:
    """根据任务类型获取推荐参数"""
    return AGENT_PRESETS.get(task_type, AgentParameters(temperature=0.7))
```

### 3.5 今日练习

1. 用 `softmax` 函数绘制 Temperature 从 0.1 到 2.0 的概率分布变化图（用 matplotlib）
2. 调用 API，用同一个 prompt + 5 个不同 temperature，对比输出差异
3. 给以下 Agent 场景选择合适的参数并说明理由：
   - RAG 检索后的答案生成
   - Agent 决定调用哪个工具
   - 用户闲聊
   - 生成测试用例

<details>
<summary>参考答案</summary>

```python
# 1. 绘图（需要 matplotlib）
import numpy as np
import matplotlib.pyplot as plt

def softmax(logits, temperature=1.0):
    scaled = logits / temperature
    exp_scaled = np.exp(scaled - np.max(scaled))
    return exp_scaled / exp_scaled.sum()

logits = np.array([5.0, 3.0, 1.0, 0.5, 0.1])
token_names = ["def", "class", "import", "from", "print"]
temps = [0.1, 0.3, 0.7, 1.0, 1.5, 2.0]

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
for ax, temp in zip(axes.flat, temps):
    probs = softmax(logits, temp)
    ax.bar(token_names, probs)
    ax.set_title(f"Temperature = {temp}")
    ax.set_ylim(0, 1)
    for i, p in enumerate(probs):
        ax.text(i, p + 0.02, f"{p:.2f}", ha="center")
plt.tight_layout()
plt.savefig("temperature_comparison.png", dpi=150)
print("图表已保存到 temperature_comparison.png")

# 3. 场景参数选择
answers = {
    "RAG检索后答案生成": AgentParameters(
        temperature=0.3, top_p=0.9, max_tokens=1024
    ),  # 需要基于检索结果准确回答，不要胡编
    "Agent决定调用工具": AgentParameters(
        temperature=0, top_p=1.0, max_tokens=200
    ),  # 必须确定性，选错工具会导致错误行为
    "用户闲聊": AgentParameters(
        temperature=0.7, top_p=0.9, max_tokens=512
    ),  # 需要一定多样性，但不应该太随机
    "生成测试用例": AgentParameters(
        temperature=0.5, top_p=0.9, max_tokens=2048
    ),  # 需要正确性，但也需要覆盖边界情况（适度创造）
}
```

</details>

---

## Day 4：Embedding 与向量表示

> Embedding 是 RAG 和语义搜索的基石。理解 Embedding 是做 Agent 检索能力的前提。

### 4.1 什么是 Embedding

```
Embedding = 把文本转换成高维数字向量
          = 把"语义"映射到"空间距离"

例子：
  "猫"       → [0.2, -0.5, 0.8, 0.1, ...]  (1536维)
  "狗"       → [0.3, -0.4, 0.7, 0.2, ...]  (和"猫"距离近)
  "汽车"     → [-0.5, 0.9, -0.2, 0.8, ...]  (和"猫"距离远)

核心直觉：
  语义相似的文本 → 向量距离近
  语义不同的文本 → 向量距离远
```

```python
import numpy as np

# === 1. 余弦相似度（最常用的向量距离度量） ===

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """计算两个向量的余弦相似度"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# 模拟 Embedding（实际是 1024~3072 维，这里用 3 维演示）
cat     = np.array([0.2, -0.5, 0.8])
dog     = np.array([0.3, -0.4, 0.7])
car     = np.array([-0.5, 0.9, -0.2])
kitten  = np.array([0.25, -0.45, 0.75])

print("=== 余弦相似度 ===")
print(f"猫 vs 狗:    {cosine_similarity(cat, dog):.4f}")   # 接近1 = 很相似
print(f"猫 vs 汽车:  {cosine_similarity(cat, car):.4f}")   # 接近0或不相关
print(f"猫 vs 小猫:  {cosine_similarity(cat, kitten):.4f}") # 最相似
print(f"狗 vs 汽车:  {cosine_similarity(dog, car):.4f}")
```

### 4.2 调用 Embedding API

```python
import httpx
import asyncio

async def get_embeddings(
    texts: list[str],
    api_key: str,
    model: str = "embedding-3"
) -> list[list[float]]:
    """
    调用智谱 Embedding API
    返回每个文本的向量表示
    """
    url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "input": texts,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]

# 使用示例
async def embedding_demo(api_key: str):
    texts = [
        "我喜欢吃苹果",
        "我爱吃水果",
        "Python是一种编程语言",
        "Java也是一种编程语言",
        "今天天气真好",
    ]

    embeddings = await get_embeddings(texts, api_key)

    # 计算两两之间的相似度
    print("=== 语义相似度矩阵 ===")
    print(f"{'':>12}", end="")
    for i, t in enumerate(texts):
        print(f"  [{i}]", end="")
    print()

    for i, (t_i, e_i) in enumerate(zip(texts, embeddings)):
        v_i = np.array(e_i)
        print(f"[{i}] {t_i[:8]:>8}", end="")
        for j, (_, e_j) in enumerate(zip(texts, embeddings)):
            v_j = np.array(e_j)
            sim = cosine_similarity(v_i, v_j)
            print(f" {sim:.2f}", end="")
        print()

# asyncio.run(embedding_demo("your-api-key"))
```

### 4.3 用 Embedding 实现简单语义搜索

```python
class SimpleSemanticSearch:
    """基于 Embedding 的简单语义搜索引擎"""

    def __init__(self, api_key: str, model: str = "embedding-3"):
        self.api_key = api_key
        self.model = model
        self.documents: list[str] = []
        self.embeddings: list[np.ndarray] = []

    async def add_documents(self, documents: list[str]):
        """添加文档到索引"""
        self.documents.extend(documents)
        new_embeddings = await get_embeddings(documents, self.api_key, self.model)
        self.embeddings.extend([np.array(e) for e in new_embeddings])

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        """语义搜索，返回最相关的 top_k 个文档"""
        query_embeddings = await get_embeddings([query], self.api_key, self.model)
        query_vec = np.array(query_embeddings[0])

        results = []
        for i, doc_vec in enumerate(self.embeddings):
            sim = cosine_similarity(query_vec, doc_vec)
            results.append({
                "index": i,
                "document": self.documents[i],
                "score": float(sim),
            })

        # 按相似度降序排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

# 使用示例
async def search_demo(api_key: str):
    engine = SimpleSemanticSearch(api_key)

    # 添加文档
    docs = [
        "Python 是一种解释型、面向对象的高级编程语言",
        "JavaScript 是运行在浏览器中的脚本语言，也用于后端开发",
        "机器学习是人工智能的子领域，通过数据训练模型",
        "深度学习使用多层神经网络处理复杂数据",
        "Vue.js 是一个渐进式前端框架，由尤雨溪创建",
        "React 是 Facebook 开发的声明式 UI 库",
        "Docker 是容器化技术，用于应用部署",
        "Git 是分布式版本控制系统",
    ]
    await engine.add_documents(docs)

    # 搜索
    queries = ["前端开发", "AI技术", "代码管理"]
    for query in queries:
        print(f"\n查询: {query}")
        results = await engine.search(query, top_k=3)
        for r in results:
            print(f"  [{r['score']:.4f}] {r['document']}")

# asyncio.run(search_demo("your-api-key"))
```

### 4.4 今日练习

1. 调用 Embedding API，计算以下句子的相似度矩阵，验证"语义相似度"：
   - "这个手机很贵" / "这部电话价格高" / "今天天气不错"
2. 实现一个 `EmbeddingCache` 类，缓存已计算过的 Embedding，避免重复调用 API
3. 用 Embedding 实现"相似问题推荐"：给定一个问题，从问题库中找出最相似的 3 个

<details>
<summary>参考答案</summary>

```python
import json
import hashlib
from pathlib import Path
from typing import Optional

class EmbeddingCache:
    """Embedding 缓存，避免重复调用 API"""

    def __init__(self, cache_dir: str = "~/agent-learning/week1/data/embedding_cache"):
        self.cache_dir = Path(cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: dict[str, list[float]] = {}

    def _get_cache_key(self, text: str, model: str) -> str:
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def get(self, text: str, model: str) -> Optional[list[float]]:
        # 先查内存
        key = self._get_cache_key(text, model)
        if key in self._memory_cache:
            return self._memory_cache[key]
        # 再查文件
        path = self._get_cache_path(key)
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                self._memory_cache[key] = data["embedding"]
                return data["embedding"]
        return None

    def set(self, text: str, model: str, embedding: list[float]):
        key = self._get_cache_key(text, model)
        self._memory_cache[key] = embedding
        path = self._get_cache_path(key)
        with open(path, "w") as f:
            json.dump({"text": text, "model": model, "embedding": embedding}, f)

    async def get_embeddings_cached(
        self, texts: list[str], api_key: str, model: str = "embedding-3"
    ) -> list[list[float]]:
        """带缓存的 Embedding 获取"""
        results = []
        uncached_indices = []
        uncached_texts = []

        for i, text in enumerate(texts):
            cached = self.get(text, model)
            if cached is not None:
                results.append(cached)
            else:
                results.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)

        # 批量获取未缓存的
        if uncached_texts:
            new_embeddings = await get_embeddings(uncached_texts, api_key, model)
            for idx, embedding in zip(uncached_indices, new_embeddings):
                results[idx] = embedding
                self.set(texts[idx], model, embedding)

        return results
```

</details>

---

## Day 5：Chat Completion API 深入

> 这一天把 Chat API 的所有参数和高级用法吃透，为后续 Agent 开发打基础。

### 5.1 Chat API 完整参数解析

```python
# === OpenAI / 智谱 兼容的 Chat Completion API ===

async def chat_complete(
    messages: list[dict],
    api_key: str,
    model: str = "glm-4",
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 2048,
    frequency_penalty: float = 0,
    presence_penalty: float = 0,
    stop: list[str] | None = None,
    stream: bool = False,
    response_format: dict | None = None,  # JSON mode
    seed: int | None = None,  # 可重复性
) -> dict:
    """
    Chat Completion API 完整参数

    参数说明：
    ────────────────────────────────────────────
    messages:           对话消息列表（必填）
    model:              模型名称
    temperature:        采样温度 0~2
    top_p:              核采样阈值 0~1
    max_tokens:         最大生成 token 数
    frequency_penalty:  频率惩罚 -2~2
    presence_penalty:   存在惩罚 -2~2
    stop:               停止词列表
    stream:             是否流式输出
    response_format:    输出格式 {"type": "json_object"}
    seed:               随机种子（相同seed+参数→相似输出）
    ────────────────────────────────────────────
    """
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "stream": stream,
    }

    # 可选参数
    if stop:
        payload["stop"] = stop
    if response_format:
        payload["response_format"] = response_format
    if seed is not None:
        payload["seed"] = seed

    async with httpx.AsyncClient(timeout=60.0) as client:
        if stream:
            return await _handle_stream(client, url, payload, headers)
        else:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()


async def _handle_stream(client, url, payload, headers):
    """处理流式响应"""
    full_content = ""
    async with client.stream("POST", url, json=payload, headers=headers) as resp:
        async for line in resp.aiter_lines():
            if not line.strip():
                continue
            if line.startswith("data: "):
                data = line[6:]
                if data.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                    content = chunk["choices"][0].get("delta", {}).get("content", "")
                    if content:
                        print(content, end="", flush=True)
                        full_content += content
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
    print()
    return full_content
```

### 5.2 响应结构详解

```python
# === Chat API 响应结构 ===

response_example = {
    "id": "chatcmpl-abc123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": "glm-4",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "你好！有什么可以帮你的？"
            },
            "finish_reason": "stop"  # stop | length | content_filter | tool_calls
        }
    ],
    "usage": {
        "prompt_tokens": 20,      # 输入 token 数
        "completion_tokens": 10,  # 输出 token 数
        "total_tokens": 30        # 总计
    }
}

# finish_reason 含义：
# ──────────────────────────────
# stop:          正常结束（模型自己决定说完了）
# length:        达到 max_tokens 被截断（可能没说完）
# content_filter: 内容被安全过滤拦截
# tool_calls:    模型想调用工具（Agent 核心！下周会深入）
# ──────────────────────────────

# === 解析响应的工具函数 ===

from pydantic import BaseModel
from typing import Literal

class ChatMessageResponse(BaseModel):
    role: str
    content: str | None = None
    tool_calls: list | None = None  # Day 5 先了解，下周深入

class ChatUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ParsedResponse(BaseModel):
    content: str
    finish_reason: Literal["stop", "length", "content_filter", "tool_calls"]
    usage: ChatUsage
    model: str

    @property
    def is_complete(self) -> bool:
        """回答是否完整（没被截断）"""
        return self.finish_reason == "stop"

    @property
    def cost_estimate(self) -> float:
        """估算成本（人民币，智谱定价）"""
        input_cost = self.usage.prompt_tokens * 0.1 / 1000
        output_cost = self.usage.completion_tokens * 0.1 / 1000
        return round(input_cost + output_cost, 6)

def parse_response(raw: dict) -> ParsedResponse:
    """解析 API 原始响应"""
    choice = raw["choices"][0]
    return ParsedResponse(
        content=choice["message"].get("content", ""),
        finish_reason=choice["finish_reason"],
        usage=ChatUsage(**raw["usage"]),
        model=raw["model"],
    )
```

### 5.3 多轮对话的正确姿势

```python
class ChatSession:
    """完整的 Chat 会话管理"""

    def __init__(self, api_key: str, model: str = "glm-4", system_prompt: str = ""):
        self.api_key = api_key
        self.model = model
        self.messages: list[dict] = []
        self.total_usage = ChatUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    async def chat(
        self,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = True,
    ) -> str:
        """发送消息并获取回复"""
        self.messages.append({"role": "user", "content": user_input})

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": self.messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        full_content = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                                    full_content += content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                print()
            else:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                full_content = data["choices"][0]["message"]["content"]
                # 累计 usage
                usage = data.get("usage", {})
                self.total_usage.prompt_tokens += usage.get("prompt_tokens", 0)
                self.total_usage.completion_tokens += usage.get("completion_tokens", 0)
                self.total_usage.total_tokens += usage.get("total_tokens", 0)
                print(full_content)

        self.messages.append({"role": "assistant", "content": full_content})
        return full_content

    def get_history(self) -> list[dict]:
        """获取完整对话历史"""
        return self.messages.copy()

    def clear_history(self, keep_system: bool = True):
        """清空历史"""
        if keep_system:
            self.messages = [m for m in self.messages if m["role"] == "system"]
        else:
            self.messages = []

# 使用示例
async def session_demo(api_key: str):
    session = ChatSession(
        api_key=api_key,
        model="glm-4-flash",
        system_prompt="你是一个Python编程专家，回答简洁准确。"
    )

    await session.chat("Python中list和tuple的区别？")
    await session.chat("那什么时候应该用tuple？")
    await session.chat("给我一个实际例子")

    print(f"\n总Token使用: {session.total_usage}")

# asyncio.run(session_demo("your-api-key"))
```

### 5.4 JSON Mode（结构化输出）

> Agent 经常需要 LLM 返回结构化数据（如工具参数），JSON Mode 是关键能力。

```python
async def chat_json(
    prompt: str,
    api_key: str,
    model: str = "glm-4",
    system_prompt: str = "",
) -> dict:
    """
    让 LLM 返回 JSON 格式的响应
    关键：在 prompt 中明确要求 JSON 格式，并给出示例
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    else:
        messages.append({
            "role": "system",
            "content": "你是一个数据提取助手。请始终以JSON格式回答，不要包含其他文字。"
        })

    messages.append({"role": "user", "content": prompt})

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,  # JSON 输出用 0 温度
        "max_tokens": 1024,
    }

    # 部分 API 支持 response_format 参数
    # payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

    # 解析 JSON（处理 LLM 可能返回的额外内容）
    try:
        # 尝试直接解析
        return json.loads(content)
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        import re
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            return json.loads(match.group())
        raise ValueError(f"无法解析为JSON: {content[:200]}")

# 使用示例：提取结构化信息
async def extract_info_demo(api_key: str):
    prompt = """
    从以下文本中提取信息，以JSON格式返回：
    {
        "name": "人名",
        "age": 年龄,
        "skills": ["技能1", "技能2"],
        "location": "城市"
    }

    文本：张三，28岁，擅长Python和Vue开发，目前在北京工作。
    """

    result = await chat_json(prompt, api_key)
    print(f"提取结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

# asyncio.run(extract_info_demo("your-api-key"))
```

### 5.5 今日练习

1. 用 `ChatSession` 完成一次 5 轮以上的多轮对话，记录每轮的 token 消耗
2. 用 JSON Mode 实现一个"文本分类器"：输入一段文本，返回 `{"category": "科技/体育/娱乐/其他", "confidence": 0.9, "keywords": ["词1", "词2"]}`
3. 实现自动重试：如果 `finish_reason == "length"`，自动追加"请继续"获取剩余内容

<details>
<summary>参考答案</summary>

```python
class ChatSessionWithRetry(ChatSession):
    """支持自动续写的 Chat 会话"""

    async def chat_with_retry(
        self,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_retries: int = 3,
    ) -> str:
        """如果回复被截断，自动续写"""
        self.messages.append({"role": "user", "content": user_input})

        full_content = ""
        for attempt in range(max_retries + 1):
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.model,
                "messages": self.messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            chunk = data["choices"][0]["message"]["content"]
            finish_reason = data["choices"][0]["finish_reason"]
            full_content += chunk

            if finish_reason != "length":
                break  # 正常结束

            # 被截断，追加续写请求
            print(f"\n[回复被截断，正在续写...({attempt+1})]")
            self.messages.append({"role": "assistant", "content": full_content})
            self.messages.append({"role": "user", "content": "请继续"})

        # 最终把完整回复加入历史
        # 移除续写相关的消息，只保留最终完整回复
        while self.messages and self.messages[-1]["role"] != "user" or \
              (len(self.messages) >= 2 and self.messages[-1]["content"] == "请继续"):
            self.messages.pop()

        # 替换原始 assistant 消息为完整版
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i]["role"] == "assistant":
                self.messages[i]["content"] = full_content
                break

        self.messages.append({"role": "assistant", "content": full_content})
        return full_content
```

</details>

---

## Day 6：综合实战 —— LLM Token 分析与成本监控工具

> 把本周所有知识串起来，做一个能实际使用的工具。

### 项目目标

```
$ python llm_monitor.py --api-key your-key

🤖 LLM Monitor v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

> 帮我解释什么是Agent
[助手回复中...]
✓ 完成 | Tokens: 28+156=184 | 成本: ¥0.0184 | 耗时: 2.3s

> Agent需要哪些技术
[助手回复中...]
✓ 完成 | Tokens: 312+203=515 | 成本: ¥0.0515 | 耗时: 1.8s

> /stats
📊 会话统计：
   总轮次: 2
   总Token: 699 (输入540 + 输出359)
   总成本: ¥0.0699
   平均延迟: 2.05s

> /analyze 输入一段文本
Token分析: 42 tokens | 中文效率 1.4 字/token | 预估成本 ¥0.0042

> /quit
```

### 完整实现

创建 `llm_monitor.py`：

```python
"""
LLM Token 分析与成本监控工具
功能：
1. 多轮对话（流式输出）
2. 实时 Token 和成本统计
3. 文本 Token 分析
4. 参数对比实验
5. 会话历史管理
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx
import tiktoken
from pydantic import BaseModel, Field

# === 1. 数据模型 ===

class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens

class CallRecord(BaseModel):
    timestamp: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency: float  # 秒
    finish_reason: str

class SessionStats(BaseModel):
    total_calls: int = 0
    total_usage: TokenUsage = Field(default_factory=TokenUsage)
    total_cost: float = 0.0
    records: list[CallRecord] = Field(default_factory=list)

    @property
    def avg_latency(self) -> float:
        if not self.records:
            return 0.0
        return sum(r.latency for r in self.records) / len(self.records)

# === 2. 价格表 ===

PRICING = {
    # 每千 tokens 的价格（人民币）
    "glm-4":        {"input": 0.1,  "output": 0.1},
    "glm-4-flash":  {"input": 0.001,"output": 0.001},
    "glm-4-plus":   {"input": 0.05, "output": 0.05},
    "gpt-4":        {"input": 0.21, "output": 0.42},   # 美元换算
    "gpt-4o":       {"input": 0.035,"output": 0.105},
    "gpt-3.5-turbo":{"input": 0.0035,"output": 0.0105},
}

def calculate_cost(usage: TokenUsage, model: str) -> float:
    pricing = PRICING.get(model, PRICING["glm-4"])
    return (usage.prompt_tokens * pricing["input"] +
            usage.completion_tokens * pricing["output"]) / 1000

# === 3. Token 分析器 ===

class TokenAnalyzer:
    def __init__(self, model: str = "gpt-4"):
        encoding_name = "cl100k_base"
        self.encoding = tiktoken.get_encoding(encoding_name)

    def analyze(self, text: str) -> dict:
        tokens = self.encoding.encode(text)
        token_count = len(tokens)
        char_count = len(text)
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if w.isascii()])

        return {
            "token_count": token_count,
            "char_count": char_count,
            "chinese_chars": chinese_chars,
            "english_words": english_words,
            "efficiency_chars": round(char_count / token_count, 2) if token_count else 0,
            "efficiency_chinese": round(chinese_chars / token_count, 2) if token_count and chinese_chars else 0,
        }

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.encoding.decode(tokens[:max_tokens])

# === 4. LLM 客户端（带监控） ===

class MonitoredLLMClient:
    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model
        self.messages: list[dict] = []
        self.stats = SessionStats()
        self.analyzer = TokenAnalyzer()

    def set_system(self, content: str):
        self.messages = [m for m in self.messages if m["role"] != "system"]
        self.messages.insert(0, {"role": "system", "content": content})

    async def chat(self, user_input: str, temperature: float = 0.7) -> str:
        self.messages.append({"role": "user", "content": user_input})

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": self.messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": True,
        }

        start_time = time.time()
        full_content = ""
        usage = TokenUsage()

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                full_content += content
                            # 流式响应中 usage 可能在最后一个 chunk
                            if "usage" in chunk:
                                u = chunk["usage"]
                                usage = TokenUsage(
                                    prompt_tokens=u.get("prompt_tokens", 0),
                                    completion_tokens=u.get("completion_tokens", 0),
                                )
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

        print()
        latency = time.time() - start_time

        # 如果流式没有返回 usage，用估算
        if usage.total == 0:
            usage = TokenUsage(
                prompt_tokens=self.analyzer.analyze(user_input)["token_count"] + 50,
                completion_tokens=self.analyzer.analyze(full_content)["token_count"],
            )

        # 更新统计
        cost = calculate_cost(usage, self.model)
        self.stats.total_calls += 1
        self.stats.total_usage.prompt_tokens += usage.prompt_tokens
        self.stats.total_usage.completion_tokens += usage.completion_tokens
        self.stats.total_cost += cost
        self.stats.records.append(CallRecord(
            timestamp=datetime.now().isoformat(),
            model=self.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            latency=round(latency, 2),
            finish_reason="stop",
        ))

        # 输出统计行
        print(f"\n✓ Tokens: {usage.prompt_tokens}+{usage.completion_tokens}={usage.total} | "
              f"成本: ¥{cost:.4f} | 耗时: {latency:.1f}s")

        self.messages.append({"role": "assistant", "content": full_content})
        return full_content

# === 5. 命令行界面 ===

async def main():
    import sys

    print("🤖 LLM Monitor v1.0")
    print("━" * 40)

    # 获取 API Key
    api_key = ""
    # 尝试从配置文件读取
    config_path = Path("~/agent-learning/week1/data/chat_config.json").expanduser()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            api_key = config.get("api_key", "")

    if not api_key:
        api_key = input("请输入API Key: ").strip()
        # 保存配置
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump({"api_key": api_key}, f)

    client = MonitoredLLMClient(api_key=api_key, model="glm-4-flash")
    client.set_system("你是一个有帮助的AI助手，回答简洁准确。")
    analyzer = TokenAnalyzer()

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        # 命令处理
        if user_input == "/quit":
            # 退出时显示总统计
            stats = client.stats
            print(f"\n📊 总统计: {stats.total_calls}次调用, "
                  f"{stats.total_usage.total} tokens, "
                  f"¥{stats.total_cost:.4f}")
            print("再见！")
            break

        elif user_input == "/stats":
            stats = client.stats
            print(f"\n📊 会话统计：")
            print(f"   总轮次: {stats.total_calls}")
            print(f"   总Token: {stats.total_usage.total} (输入{stats.total_usage.prompt_tokens} + 输出{stats.total_usage.completion_tokens})")
            print(f"   总成本: ¥{stats.total_cost:.4f}")
            print(f"   平均延迟: {stats.avg_latency:.2f}s")

        elif user_input.startswith("/analyze "):
            text = user_input[9:]
            result = analyzer.analyze(text)
            cost_1k = calculate_cost(TokenUsage(prompt_tokens=result["token_count"]), client.model)
            print(f"Token分析: {result['token_count']} tokens | "
                  f"中文字符效率: {result['efficiency_chinese']} 字/token | "
                  f"预估输入成本: ¥{cost_1k:.4f}")

        elif user_input == "/help":
            print("命令列表：")
            print("  /analyze <文本>  - Token 分析")
            print("  /stats          - 会话统计")
            print("  /model <名称>   - 切换模型")
            print("  /temp <值>      - 设置 temperature")
            print("  /history        - 查看对话历史")
            print("  /clear          - 清空历史")
            print("  /help           - 显示帮助")
            print("  /quit           - 退出")

        elif user_input.startswith("/model "):
            new_model = user_input[7:].strip()
            client.model = new_model
            print(f"模型已切换为: {new_model}")

        elif user_input.startswith("/temp "):
            try:
                new_temp = float(user_input[6:].strip())
                print(f"Temperature 已设置为: {new_temp}")
            except ValueError:
                print("无效的温度值")

        elif user_input == "/history":
            for msg in client.messages:
                role = msg["role"]
                content = msg["content"][:100]
                print(f"  [{role}] {content}{'...' if len(msg['content']) > 100 else ''}")

        elif user_input == "/clear":
            client.messages.clear()
            client.set_system("你是一个有帮助的AI助手，回答简洁准确。")
            print("历史已清空")

        else:
            # 普通聊天
            try:
                await client.chat(user_input)
            except httpx.HTTPStatusError as e:
                print(f"API错误: {e.response.status_code}")
            except Exception as e:
                print(f"错误: {e}")

if __name__ == "__main__":
    # Windows asyncio 兼容
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

### Day 6 练习

给 `llm_monitor.py` 添加以下功能：

1. `/compare <prompt>` —— 用当前模型和 glm-4-flash 两个模型回答同一个问题，对比结果
2. `/export` —— 导出会话记录为 JSON 文件（包含所有对话和统计）
3. 在统计中增加"按模型分类统计"

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

```
Token 与分词：
[ ] 理解 Token 与字符/单词的区别
[ ] 能用 tiktoken 计算 Token 数量
[ ] 知道中文和英文的 Token 效率差异
[ ] 理解 Token 对成本和延迟的影响
[ ] 能实现文本分块（chunk）逻辑

Context Window：
[ ] 理解 Context Window 的工作原理
[ ] 知道各模型的上下文限制
[ ] 能实现滑动窗口上下文管理
[ ] 理解摘要压缩策略
[ ] 能计算上下文使用率

采样参数：
[ ] 理解 Temperature 对输出的影响
[ ] 理解 Top_P 的工作原理
[ ] 知道不同场景的推荐参数
[ ] 理解 frequency_penalty 和 presence_penalty
[ ] 知道 max_tokens 和 finish_reason 的关系

Embedding：
[ ] 理解 Embedding 的概念和用途
[ ] 能调用 Embedding API
[ ] 能计算余弦相似度
[ ] 能实现简单的语义搜索
[ ] 理解 Embedding 在 RAG 中的作用

Chat API：
[ ] 能正确构造 Chat API 请求
[ ] 理解消息角色（system/user/assistant）
[ ] 能处理流式和非流式响应
[ ] 能实现多轮对话管理
[ ] 能使用 JSON Mode 获取结构化输出
[ ] 理解 finish_reason 的各种取值
```

### 7.2 综合练习题

写一个 `week2_final.py`，实现一个 **智能文档问答系统（本地版）**：

要求：

1. 读取一个文本文件（如一篇技术文章）
2. 将文章按 500 token 分块
3. 对每个块计算 Embedding
4. 用户提问时，用 Embedding 检索最相关的 3 个块
5. 把检索到的块作为上下文，调用 Chat API 回答问题
6. 显示：使用的上下文块、token 消耗、成本估算
7. 用 Pydantic 定义所有数据模型

> 这其实就是最简单的 RAG 系统！是下周学习 RAG 的预演。

<details>
<summary>参考答案框架</summary>

```python
"""
简易 RAG 系统 —— 本地文档问答
"""

import asyncio
import json
import numpy as np
from pathlib import Path
from typing import Optional

import httpx
import tiktoken
from pydantic import BaseModel, Field

# === 数据模型 ===

class DocumentChunk(BaseModel):
    index: int
    content: str
    token_count: int

class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float

class QueryResult(BaseModel):
    question: str
    answer: str
    sources: list[SearchResult]
    usage: dict

# === 文档处理 ===

class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def load_file(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def chunk(self, text: str) -> list[DocumentChunk]:
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0
        idx = 0
        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            content = self.encoding.decode(chunk_tokens)
            chunks.append(DocumentChunk(
                index=idx,
                content=content,
                token_count=len(chunk_tokens),
            ))
            start += self.chunk_size - self.overlap
            idx += 1
        return chunks

# === 向量存储 ===

class VectorStore:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.chunks: list[DocumentChunk] = []
        self.embeddings: list[np.ndarray] = []

    async def index(self, chunks: list[DocumentChunk]):
        self.chunks = chunks
        texts = [c.content for c in chunks]
        self.embeddings = []
        # 批量获取 embedding
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {"model": "embedding-3", "input": batch}
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                for item in resp.json()["data"]:
                    self.embeddings.append(np.array(item["embedding"]))

    def search(self, query_embedding: np.ndarray, top_k: int = 3) -> list[SearchResult]:
        results = []
        for i, doc_emb in enumerate(self.embeddings):
            sim = float(np.dot(query_embedding, doc_emb) /
                       (np.linalg.norm(query_embedding) * np.linalg.norm(doc_emb)))
            results.append(SearchResult(chunk=self.chunks[i], score=sim))
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

# === RAG 问答 ===

class SimpleRAG:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.processor = DocumentProcessor()
        self.store = VectorStore(api_key)

    async def load_document(self, file_path: str):
        text = self.processor.load_file(Path(file_path))
        chunks = self.processor.chunk(text)
        await self.store.index(chunks)
        print(f"已索引 {len(chunks)} 个文档块")

    async def query(self, question: str, top_k: int = 3) -> QueryResult:
        # 1. 获取问题的 embedding
        url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "embedding-3", "input": [question]}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            query_emb = np.array(resp.json()["data"][0]["embedding"])

        # 2. 检索相关文档
        results = self.store.search(query_emb, top_k)

        # 3. 构造 prompt
        context = "\n\n".join(
            f"[文档{i+1}]\n{r.chunk.content}"
            for i, r in enumerate(results)
        )
        messages = [
            {"role": "system", "content": "根据以下文档内容回答用户问题。如果文档中没有相关信息，请说明。"},
            {"role": "user", "content": f"文档内容：\n{context}\n\n问题：{question}"},
        ]

        # 4. 调用 LLM
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        payload = {
            "model": "glm-4-flash",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        answer = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return QueryResult(
            question=question,
            answer=answer,
            sources=results,
            usage=usage,
        )

# === 主程序 ===

async def main():
    api_key = input("API Key: ").strip()
    rag = SimpleRAG(api_key)

    # 加载文档
    file_path = input("文档路径: ").strip()
    await rag.load_document(file_path)

    # 问答循环
    while True:
        question = input("\n问题 (q退出): ").strip()
        if question.lower() == "q":
            break
        result = await rag.query(question)
        print(f"\n回答: {result.answer}")
        print(f"\n来源: {len(result.sources)} 个文档块")
        for s in result.sources:
            print(f"  [{s.score:.4f}] 块{s.chunk.index} ({s.chunk.token_count} tokens)")
        print(f"Token消耗: {result.usage}")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```

</details>

---

## 本周知识图谱

```
LLM 核心概念
├── Token（Day 1）
│   ├── 分词机制（tiktoken）
│   ├── Token 计数与成本计算
│   └── 文本分块策略
│
├── Context Window（Day 2）
│   ├── 上下文限制与累积
│   ├── 滑动窗口管理
│   └── 摘要压缩策略
│
├── 采样参数（Day 3）
│   ├── Temperature（创造力 vs 确定性）
│   ├── Top_P（采样范围）
│   ├── Penalty 参数
│   └── Agent 场景参数选择
│
├── Embedding（Day 4）
│   ├── 向量表示原理
│   ├── 余弦相似度
│   ├── Embedding API
│   └── 语义搜索
│
├── Chat API（Day 5）
│   ├── 完整参数解析
│   ├── 响应结构
│   ├── 多轮对话管理
│   └── JSON Mode
│
└── 综合实战（Day 6-7）
    ├── LLM 监控工具
    └── 简易 RAG 系统
```

## 本周推荐阅读

| 资源 | 说明 |
|---|---|
| [OpenAI Token 文档](https://platform.openai.com/tokenizer) | 官方 Token 可视化工具 |
| [OpenAI API Reference](https://platform.openai.com/docs/api-reference/chat) | Chat API 完整文档 |
| [智谱 API 文档](https://open.bigmodel.cn/dev/api) | 国产模型 API 文档 |
| [BytePair Encoding 论文](https://arxiv.org/abs/1508.07909) | BPE 分词算法（选读） |
| [Sentence-BERT 论文](https://arxiv.org/abs/1908.10084) | 语义相似度（选读） |

## 下周预告

Week 3 将进入 **Prompt Engineering 实战**：

- 系统提示词设计（Agent 的灵魂）
- Few-shot Learning
- Chain of Thought（CoT）
- 结构化输出进阶
- Function Calling 初探
