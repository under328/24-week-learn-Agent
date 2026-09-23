# Day 02 — ReAct 框架原理

> **学习目标**：深入理解 ReAct（Reasoning + Acting）这一 Agent 最经典的推理范式，掌握 Thought/Action/Observation 循环的底层逻辑，能手写 ReAct Agent 并在面试中讲清其优劣与改进方向。
>
> **预计用时**：3-4 小时（阅读 + 理解 + 手撕代码 + 口述练习）
>
> **面试频率**：⭐⭐⭐⭐（字节 3/11 面经出现，Agent 岗核心考点）
>
> **使用方式**：先看题目自己思考，再点开"点击查看参考答案"对照。建议把每道题口述一遍，模拟面试场景。

---

## 一、知识地图

```
ReAct 框架
│
├── 1. ReAct 的起源与核心思想
│   ├── 论文：ReAct: Synergizing Reasoning and Acting (Yao et al., 2022)
│   ├── 核心洞察：推理和行动交替 → 互相增强
│   └── 与纯推理(CoT)和纯行动(Act-Only)的对比
│
├── 2. Thought / Action / Observation 格式
│   ├── Thought：LLM 的推理过程（自然语言）
│   ├── Action：工具调用决策（结构化）
│   ├── Observation：工具返回结果（注入上下文）
│   └── 终止条件：Action 为 finish
│
├── 3. ReAct vs CoT vs Plan-and-Execute vs Reflection
│   ├── CoT：纯推理链，无行动
│   ├── ReAct：推理+行动交替
│   ├── Plan-and-Execute：先规划全流程再执行
│   └── Reflection：执行后自我反思修正
│
├── 4. ReAct 的实现方式
│   ├── Prompt-based ReAct（文本解析 Thought/Action/Observation）
│   ├── Function Calling-based ReAct（原生 tool_calls）
│   └── 两种方式的优劣对比
│
├── 5. ReAct 的局限性与改进
│   ├── 上下文膨胀、错误传播、步数多
│   └── 改进：ReWOO、Reflexion、LATS
│
└── 6. 面试高频追问
    ├── ReAct 的核心创新点是什么？
    ├── ReAct 和 Function Calling 是什么关系？
    └── ReAct 在生产环境有什么问题？怎么改进？
```

---

## 二、面试题与参考答案

> 以下 10 道题覆盖 ReAct 框架的高频考点。**先自己思考，再展开答案对照。**

---

### Q1：ReAct 框架的核心思想是什么？它解决了什么问题？⭐⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、阿里通义、百度文心

**考点**：ReAct 论文核心洞察、推理与行动的协同关系

<details>
<summary>点击查看参考答案</summary>

#### 起源

ReAct 来自 2022 年 Yao 等人的论文 *"ReAct: Synergizing Reasoning and Acting in Language Models"*。名字是 **Re**asoning + **Act**ing 的缩写。

#### 核心洞察

在 ReAct 之前，LLM 的能力被分成两个独立的研究方向：

- **推理（Reasoning）**：CoT（Chain-of-Thought）让 LLM 一步步推理，但不与外部世界交互 → 信息可能过时或错误
- **行动（Acting）**：让 LLM 调用工具获取信息，但没有推理过程 → 无法处理复杂多步任务

ReAct 的核心创新：**把推理和行动交替进行，互相增强**。

```
纯推理 (CoT)：
  Thought → Thought → Thought → Answer
  问题：无法获取外部信息，可能幻觉

纯行动 (Act-Only)：
  Action → Observation → Action → Observation → Answer
  问题：没有推理，不知道为什么调这个工具

ReAct：
  Thought → Action → Observation → Thought → Action → Observation → Answer
  推理指导行动，行动反馈信息给推理
```

#### 解决的问题

1. **幻觉问题**：CoT 纯推理可能编造事实。ReAct 在推理过程中调用工具获取真实信息，减少幻觉。
2. **盲目行动**：Act-Only 模式下 LLM 调工具没有理由，容易选错工具或传错参数。ReAct 的 Thought 让每步行动有理可据。
3. **错误恢复**：如果工具返回意外结果，ReAct 可以在 Thought 中分析错误并调整策略，而 Act-Only 只会继续盲目行动。

#### 具体例子

```
问题：奥巴马的妻子是哪所大学毕业的？

纯 CoT（可能幻觉）：
  Thought: 奥巴马的妻子是米歇尔·奥巴马，她毕业于普林斯顿大学和哈佛法学院。
  Answer: 普林斯顿大学和哈佛法学院。
  ⚠️ 如果模型记错了，无法纠正。

ReAct（调用工具验证）：
  Thought 1: 我需要先确认奥巴马的妻子是谁。
  Action 1: search("奥巴马妻子")
  Observation 1: 米歇尔·奥巴马，美国前第一夫人。
  
  Thought 2: 现在我需要查米歇尔·奥巴马的教育背景。
  Action 2: search("米歇尔·奥巴马 教育经历")
  Observation 2: 1985年普林斯顿大学社会学学士，1988年哈佛法学院法学博士。
  
  Thought 3: 我得到了答案，可以回答了。
  Action 3: finish("米歇尔·奥巴马毕业于普林斯顿大学（学士）和哈佛法学院（博士）")
```

#### 面试加分点

1. 能说出论文名和作者（Yao et al., 2022），展示学术功底
2. 能解释"协同（Synergy）"这个词的含义 —— 不是简单拼接，而是推理和行动互相增强
3. 能对比三种模式（CoT / Act-Only / ReAct）的优劣，而不是只夸 ReAct

</details>

---

### Q2：详细描述 ReAct 的 Thought / Action / Observation 格式 ⭐⭐⭐⭐⭐

**来源**：字节飞书智能助手（2025.10）、阿里 coding 面

**考点**：ReAct 的文本格式、解析逻辑、Prompt 设计

<details>
<summary>点击查看参考答案</summary>

#### ReAct 的三段式循环

ReAct 的每一轮交互由三个部分组成：

```
┌──────────────────────────────────────────────┐
│              ReAct 单轮循环                    │
│                                              │
│  ┌─────────────┐                            │
│  │  Thought     │ LLM 的推理过程（自然语言）  │
│  │  (思考)      │ "我需要先查..."            │
│  └──────┬──────┘                            │
│         │                                    │
│  ┌──────▼──────┐                            │
│  │  Action      │ 工具调用决策（结构化）     │
│  │  (行动)      │ search("query")           │
│  └──────┬──────┘                            │
│         │                                    │
│  ┌──────▼──────┐                            │
│  │  Observation │ 工具返回结果（注入上下文） │
│  │  (观察)      │ "搜索结果：..."           │
│  └─────────────┘                            │
└──────────────────────────────────────────────┘
```

#### Prompt-based ReAct 格式

最早的 ReAct 用文本格式，通过 Prompt 约束 LLM 输出：

```
Question: 奥巴马的妻子是哪所大学毕业的？

Thought 1: 我需要先确认奥巴马的妻子是谁。
Action 1: search["奥巴马妻子"]
Observation 1: 米歇尔·奥巴马，美国前第一夫人。

Thought 2: 现在我需要查米歇尔·奥巴马的教育背景。
Action 2: search["米歇尔·奥巴马 教育经历"]
Observation 2: 1985年普林斯顿大学社会学学士，1988年哈佛法学院法学博士。

Thought 3: 我得到了答案，可以回答了。
Action 3: finish["米歇尔·奥巴马毕业于普林斯顿大学和哈佛法学院"]
```

#### ReAct Prompt 模板

```
你是一个能使用工具的助手。请按以下格式回答问题：

可用工具：
- search[query]: 搜索互联网
- calculate[expression]: 数学计算
- finish[answer]: 完成任务并给出最终答案

格式要求：
Thought: 你的推理过程
Action: 工具调用（格式：工具名[参数]）

Question: {用户问题}

{历史 Thought/Action/Observation 记录}

Thought: {下一步推理}
Action: {下一步行动}
```

#### 文本解析逻辑

```python
import re

def parse_react_output(text: str) -> dict:
    """
    解析 ReAct 格式的 LLM 输出
    返回 {"thought": str, "action": str, "action_input": str}
    """
    # 提取 Thought
    thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|$)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""

    # 提取 Action（格式：工具名[参数] 或 工具名(参数)）
    action_match = re.search(r"Action:\s*(\w+)[\[\(](.+?)[\]\)]", text)
    if action_match:
        action_name = action_match.group(1)
        action_input = action_match.group(2).strip()
    else:
        action_name = ""
        action_input = ""

    return {
        "thought": thought,
        "action": action_name,
        "action_input": action_input,
    }

def is_finished(action_name: str) -> bool:
    """判断是否为终止 Action"""
    return action_name.lower() in ("finish", "done", "answer")
```

#### Function Calling-based ReAct

现代实现不再需要文本解析，而是用原生 Function Calling：

```python
# LLM 直接输出结构化 tool_calls，不需要解析文本
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=TOOLS,  # 工具定义
    tool_choice="auto",
)

# tool_calls 就是 Action
# msg.content 中的推理就是 Thought（如果开启了 reasoning）
# 工具返回结果就是 Observation
```

#### 两种实现方式对比

| 维度 | Prompt-based ReAct | Function Calling ReAct |
|------|-------------------|----------------------|
| 解析方式 | 正则解析文本 | 原生结构化输出 |
| 可靠性 | 低（LLM 可能格式错） | 高（API 保证格式） |
| Thought 可见性 | 显式输出 | 需开启 reasoning/extend-thinking |
| 模型支持 | 任何模型 | 需支持 function calling |
| 灵活性 | 高（可自定义格式） | 受 API 格式约束 |

#### 面试加分点

1. 能说出两种实现方式的优劣 —— Prompt-based 灵活但不可靠，Function Calling 可靠但受 API 约束
2. 能解释为什么现代 Agent 基本用 Function Calling 而非文本解析 —— 格式可靠性是生产环境的前提
3. 提到 Thought 的可见性问题：GPT-4o 的 function calling 默认不输出 Thought，但 Claude 3.5 的 extended thinking 可以显式输出推理过程

</details>

---

### Q3：ReAct、CoT、Plan-and-Execute、Reflection 四种范式有什么区别？⭐⭐⭐⭐⭐

**来源**：字节飞书（2025.10）、阿里达摩院、腾讯 AI Lab

**考点**：四种推理范式的原理对比、各自优劣、适用场景

<details>
<summary>点击查看参考答案</summary>

#### 四种范式全景

```
复杂度 / 自主性递增 ►

CoT ──► ReAct ──► Plan-and-Execute ──► Reflection
(纯推理)  (推理+行动)  (先规划再执行)     (自我反思修正)
```

#### 详细对比

| 维度 | CoT | ReAct | Plan-and-Execute | Reflection |
|------|-----|-------|-----------------|------------|
| **核心思想** | 一步步推理 | 推理+行动交替 | 先规划全流程再执行 | 执行后自我反思修正 |
| **工具调用** | 无 | 有 | 有 | 有 |
| **规划方式** | 无显式规划 | 边推理边行动 | 先生成完整计划 | 可结合任何范式 |
| **错误恢复** | 无 | 下一轮可调整 | 需重新规划 | 显式反思并修正 |
| **上下文消耗** | 低 | 中（每步累积） | 高（计划+执行） | 高（反思额外消耗） |
| **适用场景** | 数学推理、常识问答 | 信息检索、多步问答 | 复杂任务、长流程 | 高质量要求场景 |
| **典型论文** | Wei et al., 2022 | Yao et al., 2022 | LangChain | Shinn et al., 2023 |

#### 各范式详解

**1. CoT (Chain-of-Thought)**

```
问题：一个商店有 23 个苹果，卖了 17 个，又进了 12 个，现在有几个？

CoT 推理：
  原有 23 个苹果
  卖了 17 个：23 - 17 = 6
  又进了 12 个：6 + 12 = 18
  答案：18 个

特点：纯推理，不调用工具，不与外部交互。
适用：数学题、逻辑推理、常识问答。
局限：无法获取外部信息，可能幻觉。
```

**2. ReAct (Reasoning + Acting)**

```
问题：特斯拉 2024 年的营收是多少？

Thought 1: 我需要搜索特斯拉 2024 年的财务数据。
Action 1: search["特斯拉 2024 营收"]
Observation 1: 特斯拉 2024 年总营收 976.9 亿美元。

Thought 2: 我得到了答案。
Action 2: finish["976.9 亿美元"]

特点：推理和行动交替，每步都先想再做。
适用：需要外部信息的问答、多步检索。
局限：没有全局规划，可能走弯路；错误会传播。
```

**3. Plan-and-Execute**

```
问题：分析特斯拉和比亚迪 2024 年的财务表现对比。

Plan（先规划）:
  Step 1: 搜索特斯拉 2024 年营收和利润
  Step 2: 搜索比亚迪 2024 年营收和利润
  Step 3: 计算两者的差距
  Step 4: 生成对比分析报告

Execute（按计划执行）:
  执行 Step 1 → 结果
  执行 Step 2 → 结果
  执行 Step 3 → 结果
  执行 Step 4 → 最终报告

特点：先全局规划，再按步骤执行。
优势：有全局视野，不会走弯路。
劣势：计划可能不合理，中途无法灵活调整。
改进：Re-plan 机制——执行中发现计划不合理时重新规划。
```

**4. Reflection / Reflexion**

```
问题：写一个二分查找函数。

Round 1:
  生成代码 → 运行测试 → 2 个测试失败
  
Reflection（反思）:
  "测试失败的原因是边界条件处理错误。
   当 target 不在数组中时，应该返回 -1，
   但我的代码返回了 None。我需要修正返回值。"

Round 2:
  根据反思修正代码 → 运行测试 → 全部通过

特点：执行后反思，根据反馈修正。
优势：能从错误中学习，逐步提高。
劣势：多轮反思增加成本和延迟。
适用：代码生成、写作等需要反复打磨的任务。
```

#### 混合范式（面试加分）

生产环境通常**混合使用**多种范式：

```
Plan-and-Execute + ReAct + Reflection:

1. Plan: 先规划任务步骤（Plan-and-Execute）
2. Execute: 每步用 ReAct 执行（推理+行动）
3. Reflect: 关键步骤后做反思检查（Reflection）
4. Re-plan: 如果反思发现问题，重新规划

这是 LangGraph 推荐的生产级 Agent 架构。
```

#### 面试加分点

1. 能画出四种范式的关系图，而不是零散描述
2. 能说出每种范式的典型论文
3. 强调生产环境混合使用，而不是只选一种
4. 能举例说明什么时候用哪种："简单检索用 ReAct，复杂分析用 Plan-and-Execute，高质量要求加 Reflection"

</details>

---

### Q4：手写一个完整的 ReAct Agent（不依赖框架，含 Thought 解析）⭐⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、阿里 coding 面

**题目**：用 OpenAI SDK 手写一个 ReAct Agent，要求：
1. 支持 3 个以上工具
2. 包含 Thought/Action/Observation 完整循环
3. 有错误处理和死循环检测
4. 打印每步的 Thought（推理过程）

<details>
<summary>点击查看参考答案</summary>

#### 完整实现

```python
import json
import openai
from collections import deque

# ========== 1. 工具函数 ==========

def search_web(query: str) -> str:
    """模拟网络搜索"""
    db = {
        "特斯拉 2024 营收": "特斯拉 2024 年总营收 976.9 亿美元",
        "比亚迪 2024 营收": "比亚迪 2024 年总营收 7772 亿元人民币",
        "美元兑人民币汇率": "1 美元 ≈ 7.25 人民币",
    }
    for key, val in db.items():
        if key in query:
            return val
    return f"搜索 '{query}' 未找到相关结果"

def calculate(expression: str) -> str:
    """安全计算器"""
    try:
        allowed = set("0123456789+-*/(). ")
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "错误：包含不允许的字符"
    except ZeroDivisionError:
        return "错误：除以零"
    except (SyntaxError, NameError):
        return "错误：表达式无效"

def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """货币转换"""
    rates = {"USD_to_CNY": 7.25, "CNY_to_USD": 0.138}
    key = f"{from_currency}_to_{to_currency}"
    if key in rates:
        result = amount * rates[key]
        return f"{result:.2f}"
    return f"不支持 {from_currency} 到 {to_currency} 的转换"

# ========== 2. 工具注册表 ==========

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索互联网获取信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "数学表达式计算",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "货币转换",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "金额"},
                    "from_currency": {"type": "string", "description": "源货币代码，如 USD"},
                    "to_currency": {"type": "string", "description": "目标货币代码，如 CNY"}
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        }
    }
]

TOOL_MAP = {
    "search_web": search_web,
    "calculate": calculate,
    "convert_currency": convert_currency,
}

# ========== 3. ReAct Agent 核心 ==========

class ReActAgent:
    """
    ReAct Agent 完整实现
    
    特性：
    - Thought/Action/Observation 完整循环
    - 死循环检测（滑动窗口重复检测）
    - 步数限制与成本追踪
    - 详细的执行日志
    """

    def __init__(self, model: str = "gpt-4o", max_steps: int = 10):
        self.model = model
        self.max_steps = max_steps
        self.system_prompt = (
            "你是一个能使用工具的智能助手。请按 ReAct 模式工作：\n"
            "1. 先思考（Thought）：分析当前状态，决定下一步\n"
            "2. 再行动（Action）：选择合适的工具调用\n"
            "3. 观察结果（Observation）：根据工具返回调整策略\n"
            "4. 当你有足够信息时，直接给出最终回答（不调用工具）\n\n"
            "可用工具：\n"
            "- search_web: 搜索互联网\n"
            "- calculate: 数学计算\n"
            "- convert_currency: 货币转换"
        )

    def run(self, user_query: str, verbose: bool = True) -> str:
        """执行 ReAct 循环"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query},
        ]

        # 死循环检测：滑动窗口记录最近调用
        recent_calls = deque(maxlen=3)
        total_tokens = 0

        for step in range(self.max_steps):
            if verbose:
                print(f"\n{'='*60}")
                print(f"  ReAct Step {step + 1}/{self.max_steps}")
                print(f"{'='*60}")

            # --- Reasoning + Action：调用 LLM ---
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                )
            except openai.APIError as e:
                return f"LLM 调用失败：{e}"

            msg = response.choices[0].message
            messages.append(msg)

            # 记录 token 消耗
            if response.usage:
                total_tokens += response.usage.total_tokens

            # --- Thought：打印推理过程 ---
            if verbose and msg.content:
                print(f"\n💭 Thought: {msg.content}")

            # --- 终止判断 ---
            if not msg.tool_calls:
                if verbose:
                    print(f"\n✅ Final Answer: {msg.content}")
                    print(f"📊 Total tokens: {total_tokens}")
                return msg.content

            # --- Action：执行工具调用 ---
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                if verbose:
                    print(f"\n🔧 Action: {func_name}({json.dumps(func_args, ensure_ascii=False)})")

                # 死循环检测
                call_sig = (func_name, json.dumps(func_args, sort_keys=True))
                recent_calls.append(call_sig)
                if len(recent_calls) == 3 and len(set(recent_calls)) == 1:
                    if verbose:
                        print("\n⚠️ 检测到死循环（连续3次相同调用），强制终止")
                    return "检测到重复操作，Agent 陷入循环。"

                # 执行工具
                if func_name in TOOL_MAP:
                    try:
                        result = TOOL_MAP[func_name](**func_args)
                    except (TypeError, ValueError) as e:
                        result = f"工具执行错误：{type(e).__name__}: {e}"
                else:
                    result = f"未知工具：{func_name}，可用：{list(TOOL_MAP.keys())}"

                if verbose:
                    print(f"\n👁️ Observation: {result}")

                # --- Observation：注入上下文 ---
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })

        if verbose:
            print(f"\n⚠️ 达到最大步数 {self.max_steps}，强制终止")
            print(f"📊 Total tokens: {total_tokens}")
        return f"达到最大步数限制，未能完成任务。消耗 {total_tokens} tokens。"


# ========== 4. 运行示例 ==========

if __name__ == "__main__":
    agent = ReActAgent(model="gpt-4o", max_steps=10)

    # 示例：多步推理任务
    print("🚀 启动 ReAct Agent\n")
    answer = agent.run(
        "特斯拉 2024 年的营收换算成人民币是多少？"
        "和比亚迪 2024 年的营收相比，哪个更高？高多少？"
    )
```

#### 预期输出

```
🚀 启动 ReAct Agent

============================================================
  ReAct Step 1/10
============================================================

💭 Thought: 我需要分几步来回答这个问题：
  1. 查特斯拉 2024 年营收（美元）
  2. 查美元兑人民币汇率
  3. 将特斯拉营收换算成人民币
  4. 查比亚迪 2024 年营收（人民币）
  5. 比较两者并计算差值
  先查特斯拉的营收。

🔧 Action: search_web({"query": "特斯拉 2024 营收"})

👁️ Observation: 特斯拉 2024 年总营收 976.9 亿美元

============================================================
  ReAct Step 2/10
============================================================

💭 Thought: 特斯拉营收是 976.9 亿美元。现在需要换算成人民币。

🔧 Action: convert_currency({"amount": 976.9, "from_currency": "USD", "to_currency": "CNY"})

👁️ Observation: 7082.53

============================================================
  ReAct Step 3/10
============================================================

💭 Thought: 特斯拉营收约 7082.53 亿人民币。现在查比亚迪的营收。

🔧 Action: search_web({"query": "比亚迪 2024 营收"})

👁️ Observation: 比亚迪 2024 年总营收 7772 亿元人民币

============================================================
  ReAct Step 4/10
============================================================

💭 Thought: 比亚迪 7772 亿 > 特斯拉 7082.53 亿。计算差值。

🔧 Action: calculate({"expression": "7772 - 7082.53"})

👁️ Observation: 689.47

============================================================
  ReAct Step 5/10
============================================================

💭 Thought: 比亚迪比特斯拉高 689.47 亿人民币。现在可以回答了。

✅ Final Answer: 比亚迪 2024 年营收（7772 亿人民币）高于特斯拉（约 7082.53 亿人民币），
  高出约 689.47 亿人民币。

📊 Total tokens: 4520
```

#### 面试追问链

**Q：为什么用 `deque(maxlen=3)` 做死循环检测？**
A：`deque` 有固定长度，自动淘汰旧记录。3 次相同调用是死循环的典型信号。比 list 更高效，不需要手动 pop。

**Q：如果工具调用之间有依赖，怎么处理并行？**
A：有依赖时不能并行。可以通过 LLM 在一轮中返回多个 tool_calls 来并行无依赖的工具。但需要 Harness 层做依赖分析。

**Q：这个 ReAct Agent 和 Day 01 的 Agent Loop 有什么区别？**
A：本质相同，ReAct 是 Agent Loop 的一种具体范式。区别在于 ReAct 强调 Thought 的显式推理，而 Day 01 的实现中 LLM 的推理是隐式的（在 content 中但不强制输出）。

**Q：如果要加 Reflection 怎么改？**
A：在每步 Observation 后加一个反思节点：让 LLM 评估当前进展是否正确，如果不正确则调整策略。可以用另一个 LLM 调用做反思，或用决策模型做快速判断。

</details>

---

### Q5：ReAct 在生产环境有哪些局限性？如何改进？⭐⭐⭐⭐

**来源**：字节 AI 应用研发（2026.01）、阿里达摩院

**考点**：ReAct 的工程缺陷、改进方案（ReWOO/Reflexion/LATS）

<details>
<summary>点击查看参考答案</summary>

#### ReAct 的四大局限

| 局限 | 表现 | 根因 | 影响 |
|------|------|------|------|
| **上下文膨胀** | 每步累积 Thought+Action+Observation | 循环设计使然 | 长任务超 token 限制 |
| **错误传播** | 一步错步步错 | 无全局规划，每步只看局部 | 任务失败率高 |
| **步数过多** | 简单任务也走很多步 | 没有全局优化路径 | 成本高、延迟大 |
| **无反思能力** | 犯了错不知道 | 缺乏自我评估机制 | 重复犯同类错误 |

#### 改进方案一：ReWOO (Reasoning WithOut Observation)

**核心思想**：把推理和观察解耦 —— 先一次性规划所有步骤，再依次执行，不需要每步等观察结果。

```
ReAct（串行）：
  Thought1 → Action1 → Obs1 → Thought2 → Action2 → Obs2 → ...
  每步都依赖前一步的观察结果

ReWOO（规划+执行分离）：
  Plan: Step1: search("特斯拉营收")
        Step2: search("比亚迪营收")  
        Step3: calculate(Step1 - Step2)
  
  Execute: Step1 → Step2 → Step3
  无需中间推理，减少 LLM 调用次数
```

| 维度 | ReAct | ReWOO |
|------|-------|-------|
| LLM 调用次数 | N 步 = N 次调用 | 1 次规划 + 1 次合成 = 2 次 |
| 上下文消耗 | 线性增长 | 固定（只存计划+结果） |
| 灵活性 | 高（可动态调整） | 低（计划固定） |
| 适用场景 | 信息逐步揭示 | 步骤可预先确定 |

#### 改进方案二：Reflexion

**核心思想**：在 ReAct 循环后加一个反思步骤，让 LLM 评估自己的表现并记录教训。

```
Round 1:
  ReAct 循环 → 任务失败
  
Reflection:
  "失败原因：我在 Step 2 搜索了错误的关键词。
   教训：搜索财务数据时应该加上'财报'关键词。"

Round 2:
  带着教训重新执行 ReAct → 任务成功
```

Reflexion 的关键设计：
- 用一个"记忆"存储反思教训
- 每轮失败后，反思教训注入下一轮的上下文
- 通常 2-3 轮就能收敛

#### 改进方案三：LATS (Language Agent Tree Search)

**核心思想**：把 ReAct 的线性搜索变成树搜索，维护多个候选路径，用评估函数选最优。

```
ReAct（线性）：
  Step1 → Step2 → Step3 → ...（只有一条路径）

LATS（树搜索）：
       Step1
      /     \
   Step2a   Step2b
   /    \       \
 Step3a Step3b  Step3c
 
 用评估函数对每个节点打分，选最优路径
```

LATS 效果最好但成本最高，适合对质量要求极高的场景。

#### 生产环境的实际做法

```
生产级 ReAct 改进架构：

┌─ Planner ──────────────────────┐
│  先生成粗粒度计划               │
│  （Plan-and-Execute 思路）      │
└──────────────┬─────────────────┘
               ▼
┌─ ReAct Executor ───────────────┐
│  每步用 ReAct 执行              │
│  + 上下文压缩（控制膨胀）       │
│  + 步数预算                     │
└──────────────┬─────────────────┘
               ▼
┌─ Reflector ────────────────────┐
│  关键节点做反思检查             │
│  失败时重新规划                 │
└────────────────────────────────┘
```

#### 面试加分点

1. 能说出 ReAct 的四个具体局限，而不是笼统说"不好"
2. 能讲出至少两个改进方案（ReWOO/Reflexion/LATS）的原理
3. 强调生产环境不是纯 ReAct，而是 Plan + ReAct + Reflection 的混合
4. 提到上下文膨胀是 ReAct 最实际的问题，并给出解法（压缩、ReWOO 解耦）

</details>

---

### Q6：ReAct 和 Function Calling 是什么关系？⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、OpenAI 面经

**考点**：概念关系辨析，避免混淆

<details>
<summary>点击查看参考答案</summary>

#### 概念层次

```
ReAct 是一种推理范式（方法论）
Function Calling 是一种技术能力（工具）

ReAct 定义了"怎么想、怎么做"的循环
Function Calling 实现了"怎么做"的具体机制

ReAct 可以用 Function Calling 来实现 Action
Function Calling 可以被非 ReAct 范式使用（如 Plan-and-Execute 也用 Function Calling）
```

#### 关系图

```
┌────────────────────────────────────────────┐
│            推理范式层                       │
│  CoT  /  ReAct  /  Plan-Execute  /  ...    │
│                    │                       │
│         Action 用什么实现？                 │
│                    │                       │
│            ┌───────┴───────┐               │
│            ▼               ▼               │
│     Prompt 解析      Function Calling      │
│     (文本格式)       (API 原生)             │
│                                            │
│            技术实现层                       │
└────────────────────────────────────────────┘
```

#### 两种实现 ReAct 的方式

**方式一：Prompt + 文本解析（早期 ReAct）**

```python
# LLM 输出纯文本
prompt = """
按以下格式回答：
Thought: 你的推理
Action: 工具名[参数]
"""
# 需要 regex 解析 LLM 输出
```

**方式二：Function Calling（现代 ReAct）**

```python
# LLM 输出结构化 tool_calls
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=TOOLS,  # 工具定义
)
# 直接用 response.choices[0].message.tool_calls
# 不需要文本解析
```

#### 为什么容易混淆

面试官问"你用 ReAct 吗？"，很多人回答"用，我用 Function Calling"—— 这个回答不准确。

正确的回答：
- "我用 ReAct 范式，Action 部分用 Function Calling 实现。"
- 或者："我用 Function Calling 实现 ReAct 模式的 Agent。"

#### 面试加分点

1. 能清晰区分"范式"和"实现"两个层次
2. 能说出 ReAct 早期用 Prompt 解析实现，现在用 Function Calling 实现
3. 能指出其他范式（如 Plan-and-Execute）也可以用 Function Calling，二者不是绑定关系

</details>

---

### Q7：ReAct 的 Prompt 怎么设计？有哪些最佳实践？⭐⭐⭐

**来源**：美团 AI 平台、字节飞书

**考点**：Prompt 工程能力、ReAct 格式约束

<details>
<summary>点击查看参考答案</summary>

#### ReAct Prompt 的核心要素

一个好的 ReAct Prompt 需要包含以下要素：

```
1. 角色定义 — 你是谁
2. 工具说明 — 你能用什么
3. 格式约束 — 你怎么输出
4. 示例（Few-shot）— 正确示范
5. 终止条件 — 什么时候结束
6. 注意事项 — 常见错误提醒
```

#### 完整 Prompt 模板

```python
REACT_SYSTEM_PROMPT = """你是一个能使用工具的智能助手。

## 可用工具

{tool_descriptions}

## 工作格式

每次回复必须包含以下格式：

Thought: 你的推理过程（分析当前状态，决定下一步）
Action: 工具调用（格式：工具名(参数)）

当你有足够信息回答时，不要调用工具，直接给出最终回答。

## 示例

Question: 美国第46任总统是谁？他上任时多大？

Thought 1: 我需要先查美国第46任总统是谁。
Action 1: search(query="美国第46任总统")
Observation 1: 美国第46任总统是乔·拜登。

Thought 2: 现在我需要查拜登出生日期，计算上任时的年龄。
Action 2: search(query="乔·拜登出生日期 就任日期")
Observation 2: 拜登1942年11月20日出生，2021年1月20日就任。

Thought 3: 拜登就任时 78 岁。我可以回答了。
Action 3: finish(answer="美国第46任总统是乔·拜登，上任时78岁。")

## 注意事项

- 每次只调用一个工具
- 仔细检查工具参数是否正确
- 如果工具返回错误，分析原因并调整策略
- 不要编造信息，不确定时调用工具查询
- 完成任务后必须用 finish 给出最终答案
"""
```

#### 最佳实践

| 实践 | 说明 | 原因 |
|------|------|------|
| **显式格式约束** | 用 "Thought:" "Action:" 等前缀 | LLM 遵循格式更稳定 |
| **提供 Few-shot 示例** | 至少 1-2 个完整示例 | 比纯描述更有效 |
| **说明终止条件** | "有足够信息时不调工具，直接回答" | 防止无限循环 |
| **限制单步工具数** | "每次只调用一个工具" | 降低复杂度 |
| **错误处理提示** | "如果工具返回错误，调整策略" | 提高错误恢复率 |
| **反幻觉提示** | "不要编造信息" | 减少 LLM 幻觉 |

#### Function Calling 时代的 Prompt 变化

用 Function Calling 后，格式约束和解析不再需要，但 Prompt 仍需优化：

```python
# Function Calling 时代的 ReAct Prompt（精简版）
SYSTEM_PROMPT = """你是一个智能助手，可以使用提供的工具来回答问题。

工作原则：
1. 如果你能直接回答，不要调用工具
2. 需要外部信息时，选择最合适的工具
3. 仔细检查工具参数，确保类型正确
4. 收到工具结果后，分析是否需要进一步查询
5. 完成任务后直接给出最终回答

注意：不要编造信息，不确定时用工具验证。"""
```

#### 面试加分点

1. 能说出 Prompt 的六个核心要素
2. 强调 Few-shot 示例的重要性
3. 提到 Function Calling 时代 Prompt 精简了格式约束，但推理引导仍然重要
4. 能举一个因为 Prompt 设计不当导致 Agent 出问题的例子

</details>

---

### Q8：ReAct 中的错误恢复机制怎么设计？⭐⭐⭐

**来源**：蚂蚁集团、美团

**考点**：错误处理策略、降级机制

<details>
<summary>点击查看参考答案</summary>

#### 错误类型分类

```python
# Agent 执行中可能遇到的错误类型

class AgentError(Exception):
    """Agent 错误基类"""

class ToolExecutionError(AgentError):
    """工具执行失败"""
    
class ToolTimeoutError(ToolExecutionError):
    """工具超时"""

class ToolParamError(ToolExecutionError):
    """参数错误"""

class LLMCallError(AgentError):
    """LLM 调用失败"""

class BudgetExceededError(AgentError):
    """预算超限"""

class LoopDetectedError(AgentError):
    """死循环检测"""
```

#### 错误恢复策略矩阵

| 错误类型 | 恢复策略 | 示例 |
|---------|---------|------|
| **工具超时** | 重试（指数退避）→ 换工具 → 降级 | 搜索超时 → 重试 → 换另一个搜索 API |
| **参数错误** | 返回错误信息给 LLM → LLM 自行修正 | LLM 传了字符串给数字参数 → 告知 LLM → 修正 |
| **工具不存在** | 返回可用工具列表 → LLM 重新选择 | 幻觉工具名 → 列出真实工具 |
| **LLM 调用失败** | 重试（指数退避）→ 降级到小模型 | API 限流 → 等待重试 → 换 GPT-4o-mini |
| **预算超限** | 强制终止 → 返回部分结果 | token 超预算 → 停止 + 返回已有信息 |
| **死循环** | 强制终止 → 返回错误说明 | 连续相同调用 → 停止 |
| **结果不相关** | 重新搜索 → 换关键词 | 搜索结果无关 → LLM 改写 query |

#### 完整错误恢复实现

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1.0):
    """指数退避重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError) as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    return f"工具重试 {max_retries} 次后仍失败：{e}"
                except (ValueError, TypeError) as e:
                    # 参数错误不重试，直接返回
                    return f"参数错误（不重试）：{e}"
            return "重试次数耗尽"
        return wrapper
    return decorator

def execute_tool_safely(tool_func, tool_name, args, max_retries=3):
    """
    安全执行工具，带完整的错误恢复
    
    返回 (success: bool, result: str, error_type: str)
    """
    # 参数校验
    if tool_name not in TOOL_MAP:
        return False, f"未知工具：{tool_name}，可用：{list(TOOL_MAP.keys())}", "unknown_tool"

    try:
        result = retry_with_backoff(max_retries)(tool_func)(**args)
        return True, str(result), None
    except (TypeError, ValueError) as e:
        # 参数错误：返回给 LLM 让它修正
        return False, f"参数错误：{e}。请检查参数类型和必填项。", "param_error"
    except TimeoutError:
        return False, f"工具 {tool_name} 执行超时，请尝试其他方式。", "timeout"
    except PermissionError:
        return False, f"权限不足，需要人工确认。", "permission"
    except Exception as e:
        return False, f"未知错误：{type(e).__name__}: {e}", "unknown"


# 在 Agent Loop 中使用
for step in range(max_steps):
    # ... LLM 调用 ...
    
    for tool_call in msg.tool_calls:
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)
        
        # 安全执行
        success, result, error_type = execute_tool_safely(
            TOOL_MAP.get(func_name, lambda **k: ""),
            func_name,
            func_args,
        )
        
        if not success and error_type == "param_error":
            # 参数错误：返回错误信息给 LLM，让它自行修正
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": f"⚠️ {result} 请调整参数后重试。",
            })
        elif not success and error_type == "timeout":
            # 超时：建议 LLM 换一个工具
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": f"⚠️ {result} 建议尝试其他方式获取信息。",
            })
        else:
            # 成功或可恢复：正常注入结果
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
```

#### 关键原则

1. **可重试错误自动重试**（超时、限流）
2. **不可重试错误返回给 LLM**（参数错、工具不存在）—— 错误信息是 LLM 调整策略的信号
3. **高风险错误触发 HITL**（权限不足）
4. **永远不要静默吞掉错误** —— 要么重试，要么告知 LLM，要么告知用户

#### 面试加分点

1. 能区分"可重试"和"不可重试"错误
2. 强调"错误信息是 LLM 的信号"这个观点
3. 能给出指数退避的具体实现
4. 提到不同错误类型的不同处理策略，而不是一刀切

</details>

---

### Q9：如何用 LangGraph 实现 ReAct Agent？和手写有什么区别？⭐⭐⭐

**来源**：字节飞书（2025.10）、阿里钉钉

**考点**：LangGraph 基础、框架 vs 手写的取舍

<details>
<summary>点击查看参考答案</summary>

#### LangGraph 实现 ReAct

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from typing import Annotated
from typing_extensions import TypedDict

# 1. 定义状态
class AgentState(TypedDict):
    messages: Annotated[list, "messages"]

# 2. 定义工具
@tool
def search_web(query: str) -> str:
    """搜索互联网"""
    return f"搜索结果：{query}"

@tool
def calculate(expression: str) -> str:
    """数学计算"""
    try:
        allowed = set("0123456789+-*/(). ")
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "错误：不允许的字符"
    except (SyntaxError, ZeroDivisionError):
        return "错误：表达式无效"

tools = [search_web, calculate]

# 3. 定义 Agent 节点
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    """ReAct 推理节点：LLM 决定下一步"""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: AgentState):
    """路由：有工具调用 → 继续执行；无 → 结束"""
    last_msg = state["messages"][-1]
    if last_msg.tool_calls:
        return "tools"
    return END

# 4. 构建状态图
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

# 添加边
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")  # 工具执行后回到 agent

# 5. 编译运行
app = workflow.compile()

result = app.invoke({
    "messages": [{"role": "user", "content": "123 * 456 是多少？"}]
})
print(result["messages"][-1].content)
```

#### LangGraph 的执行流程

```
用户输入
    │
    ▼
  agent 节点（LLM 推理）
    │
    ├── 有 tool_calls? ──► tools 节点（执行工具）
    │                         │
    │                         └──► 回到 agent 节点
    │
    └── 无 tool_calls? ──► END（返回最终答案）
```

#### LangGraph vs 手写对比

| 维度 | 手写 ReAct | LangGraph ReAct |
|------|-----------|-----------------|
| 代码量 | ~100 行 | ~40 行 |
| 可读性 | 直观，逻辑清晰 | 需理解 StateGraph 概念 |
| 状态管理 | 手动管理 messages | 自动管理 State |
| 条件路由 | if/else | `add_conditional_edges` |
| 持久化 | 需自己实现 | 内置 checkpointer |
| 可调试性 | print 日志 | 内置 Trace + LangSmith |
| 灵活性 | 最高 | 受框架约束 |
| 学习成本 | 低 | 中（需学 LangGraph API） |
| 生产就绪 | 需补很多 | 开箱即用 |

#### 什么时候用手写，什么时候用框架

**手写适合**：
- 学习和理解 ReAct 原理（面试准备）
- 极简场景，不想引入框架依赖
- 需要完全控制循环逻辑

**LangGraph 适合**：
- 生产环境，需要持久化/可观测性
- 复杂状态机（多条件路由、子图）
- 团队协作（框架提供统一抽象）

#### 面试加分点

1. 能手写也能用框架，说明理解原理且有工程经验
2. 能说出两者的具体差异，而不是"框架更方便"
3. 提到 LangGraph 的 checkpointer（持久化）和 LangSmith（可观测性）是生产优势
4. 强调面试时先展示手写原理，再展示框架使用，体现"知其然知其所以然"

</details>

---

### Q10：大厂面试场景题 — 用 ReAct 设计一个研究助手 Agent ⭐⭐⭐⭐

**来源**：字节 TikTok（2025.11）、阿里通义

**题目**：设计一个"行业研究助手"Agent，用户输入一个行业名称，Agent 自主搜索信息、整理数据、生成研究报告。

<details>
<summary>点击查看参考答案</summary>

#### 需求分析

```
输入："帮我研究一下 2024 年中国新能源汽车行业"

预期输出：
  一份结构化研究报告，包含：
  - 行业概览
  - 市场规模与增长
  - 主要玩家与竞争格局
  - 技术趋势
  - 未来展望
```

#### 架构设计

```
用户输入: "2024 年中国新能源汽车行业"
    │
    ▼
┌─ Planner (规划节点) ─────────────────────┐
│  LLM 生成研究大纲：                       │
│  1. 行业概览                              │
│  2. 市场规模                              │
│  3. 主要企业                              │
│  4. 技术趋势                              │
│  5. 未来展望                              │
└──────────────┬───────────────────────────┘
               ▼
┌─ ReAct Researcher (研究节点) ─────────────┐
│  对大纲每个章节，用 ReAct 循环：           │
│                                           │
│  Thought: 需要查新能源汽车市场规模         │
│  Action: search("2024 中国新能源汽车 市场规模") │
│  Observation: 2024 年销量 1286 万辆...    │
│                                           │
│  Thought: 需要查同比增长率                │
│  Action: search("2024 新能源汽车 同比增长") │
│  Observation: 同比增长 35.5%...           │
│                                           │
│  Thought: 信息足够，整理本章内容          │
│  Action: finish(章节内容)                 │
└──────────────┬───────────────────────────┘
               ▼
┌─ Synthesizer (合成节点) ──────────────────┐
│  将各章节内容合成为完整报告                │
│  + 引用标注                               │
│  + 格式美化                               │
└──────────────┬───────────────────────────┘
               ▼
┌─ Reflector (反思节点) ────────────────────┐
│  检查报告：                               │
│  - 数据是否有来源？                       │
│  - 各章节是否连贯？                       │
│  - 是否有遗漏？                           │
│  如有问题 → 回到 Researcher 补充          │
└──────────────┬───────────────────────────┘
               ▼
          输出研究报告
```

#### 为什么是 Plan + ReAct + Reflection 的混合

- **Plan**：研究任务需要全局视野，先规划大纲再执行
- **ReAct**：每个章节的研究需要边搜索边推理，信息逐步揭示
- **Reflection**：研究报告需要质量保证，反思检查不可少

#### 关键设计细节

**1. 搜索工具设计**

```python
@tool
def search_web(query: str) -> str:
    """搜索互联网，返回前 5 条结果的摘要"""
    # 实际实现调用搜索 API
    pass

@tool
def get_market_data(industry: str, metric: str) -> str:
    """获取行业市场数据"""
    # 从数据库或 API 获取结构化数据
    pass

@tool
def get_company_info(company_name: str) -> str:
    """获取公司基本信息"""
    pass
```

**2. 上下文管理**

每个章节的研究是独立的 ReAct 循环，互不干扰：
- 避免上下文膨胀（每个章节独立循环）
- 章节结果做摘要后传递给合成节点

**3. 引用溯源**

```python
# 每条搜索结果记录来源
search_results.append({
    "content": "2024 年新能源汽车销量 1286 万辆",
    "source": "中国汽车工业协会",
    "url": "https://...",
    "timestamp": "2024-12-01"
})
# 最终报告中标注引用
```

**4. 成本控制**

```
模型路由：
  - Planner: GPT-4o（需要强规划能力）
  - Researcher: GPT-4o-mini（搜索+整理，小模型够用）
  - Synthesizer: GPT-4o（需要强写作能力）
  - Reflector: GPT-4o-mini（检查即可）

预估成本：单次研究约 $0.05-0.10
```

#### 面试加分点

1. 不是纯 ReAct，而是 Plan + ReAct + Reflection 混合架构
2. 考虑了上下文管理（每章节独立循环）
3. 考虑了引用溯源（研究类 Agent 的关键要求）
4. 考虑了成本控制（模型路由）
5. 能画出完整架构图，并解释每个节点的选择理由

</details>

---

## 三、当日小结

### 核心知识点回顾

| 序号 | 知识点 | 一句话总结 | 面试频率 |
|------|--------|------------|---------|
| 1 | ReAct 核心思想 | 推理(Thought)和行动(Action)交替进行，互相增强 | ⭐⭐⭐⭐⭐ |
| 2 | Thought/Action/Observation | 三段式循环：思考→行动→观察→循环 | ⭐⭐⭐⭐⭐ |
| 3 | 四种范式对比 | CoT(纯推理) < ReAct(推理+行动) < Plan-Exec(先规划) < Reflection(自我纠错) | ⭐⭐⭐⭐⭐ |
| 4 | 手撕 ReAct Agent | while循环 + tool_calls + 错误处理 + 死循环检测 | ⭐⭐⭐⭐⭐ |
| 5 | ReAct 局限性 | 上下文膨胀、错误传播、步数多、无反思 | ⭐⭐⭐⭐ |
| 6 | ReAct vs Function Calling | ReAct是范式，Function Calling是实现方式，不是同一层次概念 | ⭐⭐⭐⭐ |
| 7 | ReAct Prompt 设计 | 六要素：角色+工具+格式+示例+终止+注意事项 | ⭐⭐⭐ |
| 8 | 错误恢复 | 可重试错误自动重试，不可重试错误返回给LLM | ⭐⭐⭐ |
| 9 | LangGraph 实现 | StateGraph + 条件路由，生产环境优先用框架 | ⭐⭐⭐ |
| 10 | 研究助手设计 | Plan+ReAct+Reflection 混合架构 | ⭐⭐⭐⭐ |

### 面试速记卡

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：ReAct 的核心思想？
答：Reasoning + Acting 交替进行，推理指导行动，行动反馈信息给推理。
    来自 Yao et al., 2022。
    解决 CoT 幻觉和 Act-Only 盲目行动的问题。
    格式：Thought → Action → Observation → 循环。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：ReAct 和 CoT 的区别？
答：CoT 是纯推理链，不与外部交互，可能幻觉。
    ReAct 在推理中插入工具调用，获取真实信息。
    ReAct = CoT + Tool Use + Loop。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：ReAct 和 Function Calling 是什么关系？
答：ReAct 是推理范式（方法论），定义"怎么想怎么做"。
    Function Calling 是技术能力（工具），实现"怎么做"。
    ReAct 的 Action 可以用 Function Calling 实现。
    但 Function Calling 不只服务于 ReAct，其他范式也能用。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：ReAct 有什么局限？怎么改进？
答：四大局限：
    1. 上下文膨胀 → ReWOO 解耦推理和观察
    2. 错误传播 → Plan-and-Execute 先规划全局
    3. 步数过多 → ReWOO 一次性规划
    4. 无反思 → Reflexion 加反思步骤
    生产环境：Plan + ReAct + Reflection 混合。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：ReAct 的终止条件？
答：三种终止——
    1. LLM 不再调用工具 → 任务完成，输出最终答案
    2. 达到 max_steps → 防死循环
    3. 重复检测 → 连续相同调用强制终止

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 易错点提醒

| 易错点 | 错误回答 | 正确理解 |
|--------|---------|---------|
| "ReAct 就是调工具" | ❌ 只说了 Action | ✅ 核心是 Thought+Action 交替，推理指导行动 |
| "ReAct 和 Function Calling 是同一回事" | ❌ 混淆层次 | ✅ ReAct 是范式，Function Calling 是实现 |
| "ReAct 是最完美的 Agent 范式" | ❌ 过度吹捧 | ✅ 有上下文膨胀、错误传播等局限，生产环境需混合 |
| "ReAct 不需要规划" | ❌ 忽略局限 | ✌️ 复杂任务需要 Plan-and-Execute 先规划全局 |
| "Prompt-based ReAct 更好" | ❌ 忽视可靠性 | ✅ Function Calling 更可靠，Prompt 解析容易出错 |

### 自测检查清单

- [ ] 能否在 1 分钟内说出 ReAct 的核心思想和解决的问题？
- [ ] 能否画出 Thought/Action/Observation 的循环流程？
- [ ] 能否对比 CoT、ReAct、Plan-and-Execute、Reflection 四种范式？
- [ ] 能否手写一个包含错误处理和死循环检测的 ReAct Agent？
- [ ] 能否说出 ReAct 的四个局限性及对应改进方案？
- [ ] 能否解释 ReAct 和 Function Calling 的关系？
- [ ] 能否说出 ReAct Prompt 的六个核心要素？
- [ ] 能否设计一个完整的错误恢复策略矩阵？
- [ ] 能否用 LangGraph 实现 ReAct Agent？
- [ ] 能否设计一个 Plan+ReAct+Reflection 混合架构的研究助手？

### 今日延伸阅读（可选）

| 资源 | 类型 | 说明 |
|------|------|------|
| ReAct 论文 | 论文 | Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", 2022 |
| Reflexion 论文 | 论文 | Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", 2023 |
| ReWOO 论文 | 论文 | Xu et al., "ReWOO: Decoupling Reasoning from Observations", 2023 |
| LangGraph 文档 | 文档 | langchain-ai.github.io/langgraph |
| LATS 论文 | 论文 | Zhou et al., "Language Agent Tree Search", 2023 |

### 明日预告

Day 03 将深入 **Function Calling 与 Tool Use**，包括：
- Function Calling 的工作原理（OpenAI / Anthropic / Google 三家实现对比）
- Tool Schema 设计最佳实践
- 工具发现与注册机制
- 并行工具调用与依赖管理
- 工具调用的安全防御
- 手撕一个支持并行工具调用的 Agent

---

> **学习建议**：今天重点是"理解原理 + 手撕代码"。建议：
> 1. 对着面试速记卡练 2-3 遍口述
> 2. 手撕代码部分自己敲一遍，特别注意错误处理和死循环检测
> 3. 完成自测检查清单
> 4. 如果有时间，读一读 ReAct 原论文（只有 10 页）
