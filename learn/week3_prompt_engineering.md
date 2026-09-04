# 第1月第3周：Prompt Engineering 实战

> 适用对象：已完成 Week 1 Python 基础 + Week 2 LLM 核心概念的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：掌握系统提示词设计、Few-shot、CoT、结构化输出和 Function Calling，能独立设计 Agent 的提示词体系

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month1/week3
cd month1/week3

python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

pip install httpx pydantic tiktoken jsonschema
pip freeze > requirements.txt
```

---

## Day 1：系统提示词设计

> 系统提示词（System Prompt）是 Agent 的"灵魂"——它定义了 Agent 的身份、行为边界、输出格式和决策规则。一个差的系统提示词会让 Agent 胡言乱语，一个优秀的系统提示词能让 Agent 稳定可靠。

### 1.1 系统提示词的核心结构

```
一个完整的系统提示词通常包含以下部分（按重要性排序）：

1. 角色定义     —— 你是谁
2. 任务描述     —— 你要做什么
3. 行为规则     —— 你必须遵守的约束
4. 输出格式     —— 你应该怎么回答
5. 知识背景     —— 你需要知道的信息
6. 示例         —— 展示期望的输入输出
7. 边界处理     —— 遇到超出能力的问题怎么办

不是每个提示词都需要全部7部分，但角色+规则+格式是最低配置。
```

### 1.2 从差到好的系统提示词演进

```python
# === 版本0：最差的提示词（几乎无用） ===
BAD_PROMPT_V0 = "你是一个助手"

# 问题：没有任何约束，LLM 可以用任何风格回答任何内容

# === 版本1：加了角色但不够具体 ===
BAD_PROMPT_V1 = "你是一个Python编程助手，帮助用户解决编程问题。"

# 问题：没有输出格式要求，可能回答太长或太短，可能跑题

# === 版本2：加了规则但规则冲突 ===
BAD_PROMPT_V2 = """你是一个Python编程助手。
请给出详细的解释。
请尽量简短回答。
如果不确定就说不知道。
给出完整的代码示例。
"""

# 问题：详细解释 vs 简短回答，规则矛盾；给代码 vs 简短也矛盾

# === 版本3：好的提示词 ===
GOOD_PROMPT_V3 = """你是一个Python编程专家。

## 你的任务
帮助用户解决Python编程问题，提供准确的代码和解释。

## 行为规则
1. 优先给出可运行的代码示例，再补充解释
2. 解释控制在3-5句话以内
3. 如果用户问题不明确，先提问澄清，不要猜测
4. 如果问题超出Python范围，礼貌说明你的专长是Python
5. 不要编造不存在的API或函数

## 输出格式
- 代码块使用 ```python 包裹
- 关键要点用列表形式呈现
- 如果有多个方案，标注推荐方案

## 边界处理
- 不确定时回答："我不确定，但据我了解..."，不要伪装确定
- 遇到危险操作（如删除文件）时给出警告
"""

# 为什么好：
# 1. 角色明确：Python专家
# 2. 规则清晰无冲突：5条规则互不矛盾
# 3. 输出格式具体：代码块、列表、标注推荐
# 4. 边界处理：不确定和危险操作都有预案
```

### 1.3 系统提示词设计原则

```python
# === 原则1：具体 > 抽象 ===

# 差
abstract_rule = "回答要准确"
# 好
specific_rule = "引用API时必须给出具体的函数签名和版本号"

# === 原则2：正面 > 负面（告诉它做什么，而不是不做什么） ===

# 差（负面）
negative_rule = "不要回答与编程无关的问题"
# 好（正面）
positive_rule = "只回答与Python编程相关的问题，其他问题请礼貌拒绝"

# 为什么？LLM 对负面指令的遵循度不如正面指令。
# "不要想大象" → 你脑子里出现大象了

# === 原则3：结构化 > 散文式 ===

# 差（散文式）
prose_prompt = """你是一个代码审查助手，你需要审查用户提交的代码，找出bug和潜在问题，
给出改进建议，还要注意代码风格，如果是安全问题要特别标注出来，
最后给一个总体评分。"""

# 好（结构化）
structured_prompt = """你是一个代码审查助手。请按以下步骤审查代码：

## 审查维度
1. **正确性**：是否存在逻辑错误或运行时错误
2. **安全性**：是否存在注入、泄露等安全风险（用 ⚠️ 标注）
3. **性能**：是否存在明显的性能问题
4. **风格**：是否符合 PEP8 规范

## 输出格式
### 问题列表
- [严重程度: 高/中/低] 问题描述 + 修改建议

### 总评
- 评分: A/B/C/D
- 一句话总结
"""

# === 原则4：分优先级（避免规则冲突） ===

priority_prompt = """你是一个客服助手。在回答时遵循以下优先级（高优先级规则覆盖低优先级）：

1. [最高] 安全规则：不透露用户隐私，不处理违规请求
2. [高]   准确规则：不确定的不编造，明确标注"待确认"
3. [中]   效率规则：优先给出直接答案，不啰嗦
4. [低]   友好规则：语气友善，但不得影响准确性
"""

# === 原则5：给一个"逃生出口" ===

escape_prompt = """如果你无法回答某个问题，请使用以下格式：
"我目前无法回答这个问题，原因是：[具体原因]。建议你[替代方案]。"
不要编造答案，不要回避问题。
"""
```

### 1.4 实战：为不同 Agent 角色设计系统提示词

```python
# === 场景1：RAG 文档问答 Agent ===

RAG_AGENT_PROMPT = """你是一个文档问答助手。根据提供的文档内容回答用户问题。

## 核心规则
1. 只根据提供的文档内容回答，不要使用外部知识
2. 如果文档中没有相关信息，明确回答"根据现有文档无法回答该问题"
3. 引用文档内容时标注来源段落

## 输出格式
### 回答
[你的回答]

### 来源
- 文档段落: [引用的原文片段]

### 置信度
- 高/中/低（基于文档内容与问题的相关程度）
"""

# === 场景2：代码生成 Agent ===

CODE_AGENT_PROMPT = """你是一个代码生成助手。

## 任务
根据用户需求生成高质量代码。

## 编码规范
- 使用类型提示（Type Hints）
- 添加 docstring（Google 风格）
- 函数单一职责，不超过50行
- 错误处理：使用具体的异常类型，不使用裸 except
- 命名：变量用 snake_case，类用 PascalCase

## 输出格式
1. 代码（```python 代码块）
2. 简要说明（3句话以内，解释设计决策）
3. 使用示例（展示如何调用）

## 注意
- 不确定需求时先提问
- 需要外部依赖时明确标注 `pip install xxx`
"""

# === 场景3：数据分析 Agent ===

DATA_AGENT_PROMPT = """你是一个数据分析助手。

## 能力
- 读取和分析数据
- 生成 Python 数据分析代码（pandas/matplotlib）
- 解释分析结果

## 工作流程
1. 理解用户的分析需求
2. 检查数据是否支持该分析
3. 生成分析代码
4. 解释结果和洞察

## 输出格式
### 分析方案
[简述你打算怎么分析]

### 代码
```python
# 分析代码
```

### 结果解读

- 关键发现: [最重要的3个发现]
- 数据局限: [分析可能的偏差或不足]

### 建议

[基于数据的行动建议]
"""

```

### 1.5 系统提示词的 Token 优化

```python
import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")

def count_prompt_tokens(prompt: str) -> int:
    return len(encoding.encode(prompt))

# 对比不同风格提示词的 Token 消耗
prompts = {
    "散文式(冗长)": """你是一个编程助手，你需要帮助用户解决编程问题。当用户提问时，你应该先仔细阅读用户的问题，
然后思考最佳的解决方案，接着给出代码示例，最后用简洁的语言解释代码的工作原理。
如果用户的问题不够明确，你应该主动询问更多细节。如果你不确定答案，请诚实地告诉用户你不确定，
而不是编造一个可能错误的答案。回答时请使用中文。""",

    "结构化(紧凑)": """编程助手规则：
1. 先理解问题，再给代码+解释
2. 代码在前，解释3句以内
3. 需求不清→先提问
4. 不确定→直说不确定，不编造
5. 用中文回答""",
}

for name, prompt in prompts.items():
    tokens = count_prompt_tokens(prompt)
    print(f"{name}: {tokens} tokens")
# 结构化版本通常节省 40-60% Token
```

### 1.6 今日练习

1. 为以下 Agent 角色各写一个系统提示词，控制在 200 token 以内：
   - 技术面试官 Agent（模拟面试，逐步追问）
   - 代码 Review Agent（审查代码质量，给出改进建议）
   - 翻译 Agent（中英互译，保持术语一致）
2. 对你写的每个提示词，用"反面测试"验证：
   - 问一个超出范围的问题，看 Agent 是否正确拒绝
   - 给一个模糊的输入，看 Agent 是否主动澄清
   - 给一个有陷阱的问题，看 Agent 是否上当

<details>
<summary>参考答案</summary>

```python
# 技术面试官 Agent
INTERVIEWER_PROMPT = """你是一个高级技术面试官。

## 角色
模拟真实技术面试，考察候选人的技术深度。

## 规则
1. 每次只问一个问题，等候选人回答后再追问
2. 根据回答质量调整难度：答对→加深，答错→简化
3. 追问方向：原理、边界情况、性能、权衡取舍
4. 不直接给答案，用提示引导候选人思考
5. 每轮结束时给出简短评价（1-2句）

## 输出格式
**面试官**: [问题]
[候选人回答后]
**评价**: [简要评价] → **下一个问题**: [追问]

## 开始
自我介绍后，请候选人选择面试方向（前端/后端/AI），然后开始第一题。"""

# 代码 Review Agent
REVIEW_AGENT_PROMPT = """你是代码审查专家。

## 审查清单
1. 正确性：逻辑错误、运行时异常风险
2. 安全性：⚠️ SQL注入/XSS/敏感信息泄露
3. 性能：O(n²)可优化处、内存泄漏
4. 可读性：命名/注释/复杂度
5. 规范：类型提示/错误处理/代码风格

## 输出格式
### 问题（按严重度排序）
- 🔴 [必须修复] 问题描述 → 修改建议
- 🟡 [建议优化] 问题描述 → 修改建议
- 🔵 [风格建议] 问题描述 → 修改建议

### 总评
评级: A(优秀) B(良好) C(需修改) D(重写)
一句话总结

## 规则
- 给出具体行号和修改后代码，不说空话
- 不确定的问题标注"待确认"
- 不改变代码的原有意图"""

# 翻译 Agent
TRANSLATOR_PROMPT = """你是专业中英互译助手。

## 规则
1. 自动检测输入语言，翻译为另一种
2. 技术术语保持原文或使用业界通用译法（首次出现时标注原文）
3. 保留代码块、Markdown格式不变
4. 专有名词不翻译（如 React、Docker、Pydantic）
5. 意译为主，不逐字翻译，保证目标语言自然流畅

## 输出格式
### 译文
[翻译结果]

### 术语表
| 原文 | 译文 | 说明 |
"""
```

</details>

---

## Day 2：Few-Shot Learning（少样本学习）

> Few-Shot 是指在提示词中给 LLM 几个"输入→输出"的示例，让它学会你期望的模式。这是让 Agent 行为可控的核心技巧。

### 2.1 Zero-Shot vs One-Shot vs Few-Shot

```python
# === Zero-Shot：不给示例，直接提问 ===

zero_shot_prompt = """请对以下用户反馈进行情感分类（正面/负面/中性）：

用户反馈：这个产品的用户体验太差了，经常崩溃。"""

# 可能的输出："负面" 或 "这条反馈的情感是负面的" 或 其他不确定格式

# === One-Shot：给1个示例 ===

one_shot_prompt = """请对用户反馈进行情感分类。

示例：
用户反馈：物流很快，包装完好，非常满意！
分类：正面

请分类：
用户反馈：这个产品的用户体验太差了，经常崩溃。
分类："""

# 输出几乎一定是："负面"（因为示例教会了它只输出标签）

# === Few-Shot：给多个示例 ===

few_shot_prompt = """请对用户反馈进行情感分类。

用户反馈：物流很快，包装完好，非常满意！
分类：正面

用户反馈：客服态度好，但产品质量一般。
分类：中性

用户反馈：用了一周就坏了，退货流程还特别麻烦。
分类：负面

用户反馈：这个产品的用户体验太差了，经常崩溃。
分类："""

# 输出稳定为："负面"
# 而且示例覆盖了正面/中性/负面，模型不会偏向某个类别
```

### 2.2 Few-Shot 的核心原则

```python
# === 原则1：示例要覆盖所有可能的输出类别 ===

# 差：只有正面和负面示例，模型遇到中性反馈可能不知道怎么分
bad_examples = [
    ("物流很快！", "正面"),
    ("质量太差", "负面"),
    # 缺少中性示例！
]

# 好：覆盖所有类别
good_examples = [
    ("物流很快！", "正面"),
    ("客服态度好但产品一般", "中性"),
    ("用一周就坏了", "负面"),
]

# === 原则2：示例的顺序影响输出（位置偏差） ===

# LLM 倾向于模仿最后看到的示例
# 如果最后几个示例都是负面，模型可能过度倾向负面

# 建议：如果类别均衡，随机打乱顺序
# 如果类别不均衡，把少数类放在后面（提高其权重）

# === 原则3：示例要和真实输入的复杂度一致 ===

# 差：示例太简单，真实输入很复杂
simple_examples = [
    ("好", "正面"),
    ("差", "负面"),
]

# 好：示例和真实输入复杂度匹配
complex_examples = [
    ("虽然价格比预期高了一点，但功能确实很强大，性价比还是不错的", "正面"),
    ("包装还行，但说明书太简陋了，很多功能要自己摸索", "中性"),
    ("用了三天就出现闪退，联系客服三天没人回，非常失望", "负面"),
]

# === 原则4：用格式一致的示例 ===

# 差：格式不一致
inconsistent_examples = """
Input: 物流很快！
Output: 这条反馈是正面的

用户说：质量太差
情感：负面
"""

# 好：格式严格一致
consistent_examples = """
用户反馈：物流很快！
情感：正面

用户反馈：质量太差
情感：负面
"""
```

### 2.3 Few-Shot 实战：构建结构化输出模式

```python
from pydantic import BaseModel
from typing import Optional
import json

# 场景：让 LLM 从自然语言中提取结构化信息

class BugReport(BaseModel):
    title: str
    severity: str  # critical/major/minor
    component: str
    description: str
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str

FEW_SHOT_EXTRACTION_PROMPT = """你是一个Bug报告提取助手。从用户的描述中提取结构化的Bug信息。

## 示例1
用户输入：
"我在用搜索功能的时候发现一个问题。每次输入中文关键词搜索，页面就会卡住大概5秒钟，然后显示'请求超时'。英文搜索就没这个问题。我用的Chrome浏览器，版本120.0。"

提取结果：
```json
{
  "title": "中文关键词搜索导致页面卡住并超时",
  "severity": "major",
  "component": "搜索模块",
  "description": "输入中文关键词搜索时页面卡住约5秒后显示请求超时，英文搜索正常",
  "steps_to_reproduce": ["1. 打开搜索功能", "2. 输入中文关键词", "3. 观察页面响应"],
  "expected_behavior": "中文搜索应在2秒内返回结果",
  "actual_behavior": "中文搜索导致页面卡住5秒后显示请求超时"
}
```

## 示例2

用户输入：
"系统完全登不上去了！输入账号密码点登录，直接白屏。好几个同事都这样，急！！！"

提取结果：

```json
{
  "title": "登录后白屏，多用户受影响",
  "severity": "critical",
  "component": "登录模块",
  "description": "输入账号密码点击登录后页面白屏，多个用户受影响",
  "steps_to_reproduce": ["1. 打开登录页面", "2. 输入账号密码", "3. 点击登录按钮", "4. 观察页面状态"],
  "expected_behavior": "登录成功后跳转到首页",
  "actual_behavior": "登录后页面白屏"
}
```

## 请提取以下用户输入

用户输入：
{user_input}

提取结果："""

# 使用函数

async def extract_bug_report(user_input: str, api_key: str) -> BugReport:
prompt = FEW_SHOT_EXTRACTION_PROMPT.format(user_input=user_input)

```
url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
headers = {"Authorization": f"Bearer {api_key}"}
payload = {
    "model": "glm-4-flash",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0,
    "max_tokens": 1024,
}

async with httpx.AsyncClient(timeout=30.0) as client:
    resp = await client.post(url, json=payload, headers=headers)
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
```

# 提取 JSON

```
import re
match = re.search(r'\{[\s\S]*\}', content)
if match:
    data = json.loads(match.group())
    return BugReport(**data)
raise ValueError(f"无法提取结构化数据: {content[:200]}")
```

```

### 2.4 Few-Shot 的 Token 开销管理

```python
import tiktoken

encoding = tiktoken.get_encoding("cl100k_base")

def estimate_few_shot_cost(
    examples: list[tuple[str, str]],
    input_format: str,  # 如 "用户反馈：{input}\n情感："
    max_input_length: int = 100,
    model: str = "glm-4",
) -> dict:
    """估算 Few-Shot 提示词的 Token 开销"""
    total_text = ""
    for ex_input, ex_output in examples:
        total_text += input_format.format(input=ex_input) + ex_output + "\n\n"

    example_tokens = len(encoding.encode(total_text))
    single_input_tokens = len(encoding.encode(
        input_format.format(input="x" * max_input_length)
    ))

    return {
        "example_count": len(examples),
        "example_tokens": example_tokens,
        "per_input_overhead": single_input_tokens,
        "total_overhead": example_tokens + single_input_tokens,
        "recommendation": (
            "开销可接受" if example_tokens < 500
            else "考虑减少示例数" if example_tokens < 1500
            else "警告：示例消耗过多上下文，考虑压缩或改用 Fine-tuning"
        ),
    }

# 评估不同数量的示例
examples_3 = [
    ("物流很快！", "正面"),
    ("客服态度好但产品一般", "中性"),
    ("用一周就坏了", "负面"),
]
examples_10 = examples_3 * 3 + [("还行吧", "中性")]

for name, examples in [("3-shot", examples_3), ("10-shot", examples_10)]:
    cost = estimate_few_shot_cost(examples, "用户反馈：{input}\n情感：")
    print(f"{name}: {cost['example_tokens']} tokens → {cost['recommendation']}")
```



### 2.5 今日练习

1. 为以下任务设计 Few-Shot 提示词（每个至少 3 个示例）：
   - 意图识别：将用户输入分为"查天气/订餐/问路/闲聊/其他"
   - 代码注释生成：给函数添加中文注释
   - SQL 生成：自然语言转 SQL
2. 对比 Zero-Shot 和 Few-Shot 在同一任务上的效果差异（至少测 5 个输入）
3. 实现一个动态 Few-Shot 选择器：根据用户输入的语义相似度，从示例库中挑选最相关的 3 个示例

<details>
<summary>参考答案（动态 Few-Shot 选择器）</summary>

```python
import numpy as np
from typing import Callable

class DynamicFewShotSelector:
"""根据输入语义相似度动态选择最相关的示例"""

```
def __init__(
    self,
    examples: list[dict],
    embed_fn: Callable[[str], np.ndarray],
    top_k: int = 3,
):
    """
    examples: [{"input": "...", "output": "..."}]
    embed_fn: 文本转向量的函数
    """
    self.examples = examples
    self.embed_fn = embed_fn
    self.top_k = top_k

    # 预计算所有示例的 embedding
    self.example_embeddings = [
        embed_fn(ex["input"]) for ex in examples
    ]

def select(self, user_input: str) -> list[dict]:
    """选择与用户输入最相关的示例"""
    query_embedding = self.embed_fn(user_input)

    similarities = []
    for i, ex_emb in enumerate(self.example_embeddings):
        sim = float(np.dot(query_embedding, ex_emb) /
                   (np.linalg.norm(query_embedding) * np.linalg.norm(ex_emb)))
        similarities.append((sim, i))

    # 按相似度降序排序，取 top_k
    similarities.sort(reverse=True)
    selected = [self.examples[idx] for _, idx in similarities[:self.top_k]]
    return selected

def build_prompt(
    self,
    user_input: str,
    template: str = "输入：{input}\n输出：{output}\n\n",
) -> str:
    """构建包含动态选择示例的提示词"""
    selected = self.select(user_input)
    examples_text = ""
    for ex in selected:
        examples_text += template.format(input=ex["input"], output=ex["output"])
    examples_text += f"输入：{user_input}\n输出："
    return examples_text
```

# 使用示例（需要提供 embed_fn）

# selector = DynamicFewShotSelector(

# examples=[

# {"input": "帮我查北京天气", "output": "意图：查天气，城市：北京"},

# {"input": "我想吃火锅", "output": "意图：订餐，菜系：火锅"},

# {"input": "怎么去国贸", "output": "意图：问路，目的地：国贸"},

# {"input": "你好啊", "output": "意图：闲聊"},

# {"input": "上海今天冷吗", "output": "意图：查天气，城市：上海"},

# {"input": "附近有什么好吃的", "output": "意图：订餐，偏好：附近"},

# ],

# embed_fn=my_embed_function,

# top_k=3,

# )

# prompt = selector.build_prompt("北京今天热吗")

# → 会选中 "查北京天气" 和 "上海今天冷吗" 等相关示例

```
</details>

---

## Day 3：Chain of Thought（CoT）推理链

> CoT 是让 LLM "显式思考" 的技术。Agent 的决策质量高度依赖推理过程，CoT 是提升 Agent 可靠性的关键。

### 3.1 为什么需要 CoT

```

不使用 CoT：
用户：一个商店打8折后是240元，原价多少？
LLM：300元（可能正确，也可能错误，你不知道它怎么算的）

使用 CoT：
用户：一个商店打8折后是240元，原价多少？
LLM：让我一步步思考：
1. 打8折意味着价格是原价的80%
2. 原价 × 0.8 = 240
3. 原价 = 240 / 0.8 = 300
所以原价是300元。

CoT 的价值：

1. 准确性提升：复杂推理任务的正确率显著提高
2. 可调试性：你能看到推理过程，知道哪一步出错了
3. 可信度：用户能看到"为什么"，而不只是"是什么"

```

### 3.2 CoT 的三种触发方式

```python
# === 方式1：零样本 CoT（最简单） ===
# 在 prompt 末尾加上 "让我们一步步思考" 或 "Let's think step by step"

ZERO_SHOT_COT_PROMPT = """请解决以下问题。

问题：{question}

请一步步思考。"""

# 这是最简单的方式，研究发现仅加这句话就能显著提升推理准确率
# 适用于：不想写示例，但想引导模型推理的场景

# === 方式2：Few-Shot CoT（最常用） ===
# 在示例中展示推理过程

FEW_SHOT_COT_PROMPT = """请解决数学问题。

问题：小明有5个苹果，给了小红2个，又买了3个，现在有几个苹果？
推理：小明原来有5个苹果。给了小红2个，剩下5-2=3个。又买了3个，3+3=6个。
答案：6

问题：一件商品原价200元，先涨价20%，再降价20%，现价是多少？
推理：原价200元。涨价20%后：200×1.2=240元。降价20%后：240×0.8=192元。
答案：192

问题：{question}
推理："""

# Few-Shot CoT 的效果比 Zero-Shot CoT 更好
# 因为示例教会了模型"推理的格式和深度"

# === 方式3：自动 CoT（Auto-CoT） ===
# 让 LLM 先自己生成推理链，再用这些推理链作为示例
# 高级用法，了解即可
```



### 3.3 Agent 中的 CoT 应用



```python
# === 场景1：Agent 决策推理 ===

AGENT_COT_PROMPT = """你是一个智能助手，需要决定如何响应用户请求。

## 可用工具
1. search(query) - 搜索知识库
2. calculator(expression) - 计算数学表达式
3. weather_api(city) - 查询天气
4. code_execute(code) - 执行代码

## 推理格式
对于每个用户请求，请按以下步骤推理：

思考：
1. 用户想做什么？→ [理解意图]
2. 需要哪些信息？→ [识别信息需求]
3. 需要调用工具吗？→ [决策]
4. 调用什么工具，参数是什么？→ [执行计划]

然后给出回答或工具调用。

## 示例
用户：北京明天会不会下雨？我应该带伞吗？

思考：
1. 用户想知道北京明天的天气，以及是否需要带伞
2. 需要北京的天气预报信息
3. 是，需要调用 weather_api
4. 调用 weather_api("北京")，根据结果判断是否下雨

工具调用：weather_api("北京")

[获得结果：北京明天小雨，气温15-20°C]

回答：北京明天有小雨，气温15-20°C。建议带伞出门，同时可以穿一件薄外套。

---

用户：{user_input}

思考："""

# === 场景2：代码调试 CoT ===

DEBUG_COT_PROMPT = """你是一个代码调试助手。请按以下步骤分析Bug：

1. **理解预期**：代码应该做什么？
2. **定位问题**：哪一行/哪个函数出错了？
3. **分析原因**：为什么会出错？（类型错误？逻辑错误？边界情况？）
4. **验证假设**：这个原因能解释观察到的现象吗？
5. **给出修复**：最小改动方案

## 示例
代码：
```python
def find_max(numbers):
    max_val = 0
    for n in numbers:
        if n > max_val:
            max_val = n
    return max_val
```

报错：find_max([-1, -2, -3]) 返回 0 而不是 -1

分析：

1. 预期：返回列表中的最大值，对 [-1,-2,-3] 应返回 -1
2. 定位：max_val 初始化为 0 有问题
3. 原因：当所有数字都是负数时，0 比它们都大，永远不会被更新
4. 验证：-1 > 0 为 False，所以 max_val 保持 0。确实如此。
5. 修复：将 `max_val = 0` 改为 `max_val = numbers[0]`（或 `float('-inf')`）

## 请分析以下代码

代码：

```python
{code}
```

报错：{error}

分析："""

# === 场景3：多步骤任务规划 ===

PLANNING_COT_PROMPT = """你是一个任务规划助手。请将复杂任务分解为可执行的步骤。

## 规则

1. 每个步骤必须是单一、明确的操作
2. 标注步骤间的依赖关系
3. 标注哪些步骤可以并行执行
4. 估算每个步骤的难度（简单/中等/困难）

## 输出格式

### 任务分析

[整体理解]

### 执行计划

1. [步骤1] (简单) - 无依赖
2. [步骤2] (中等) - 依赖步骤1
3. [步骤3] (简单) - 可与步骤2并行
   ...

### 风险点

- [可能的问题和应对方案]

---

任务：{task}"""

```

### 3.4 CoT 的局限性与改进

```python
# === 局限1：Token 消耗增加 ===
# CoT 的推理过程本身消耗 Token，可能比直接回答多 2-5 倍

# 改进：按需 CoT
CONDITIONAL_COT = """你是一个助手。请根据问题复杂度决定是否展示推理过程：

- 简单问题（事实查询、简单计算）：直接回答
- 中等问题（需要2-3步推理）：简要推理后回答
- 复杂问题（需要多步推理或多个信息源）：完整推理后回答

判断标准：如果你需要在脑中做2步以上的推理，就展示推理过程。"""

# === 局限2：推理可能出错但看起来合理 ===
# CoT 不保证推理正确，只是让推理可见

# 改进：自我验证
SELF_VERIFY_COT = """请按以下步骤回答问题：

1. 先写出你的推理过程
2. 得出初步答案
3. 验证：用不同的方法或角度检验你的答案
4. 如果验证不通过，重新推理
5. 给出最终答案

验证示例：
问题：3 × 7 = ?
推理：3 × 7 = 21
验证：7 + 7 + 7 = 21 ✓
答案：21"""

# === 局限3：中文 CoT 效果有时不如英文 ===
# 部分模型的推理能力在英文下更强

# 改进：中英混合 CoT
BILINGUAL_COT = """请用以下方式回答：

思考过程（可以用英文思考，更精确）：
[English thinking process]

回答（用中文）：
[中文回答]"""
```



### 3.5 今日练习

1. 对比 Zero-Shot、Zero-Shot CoT、Few-Shot CoT 在以下问题上的表现：
   - "一个水池有两个进水管，A管3小时注满，B管5小时注满，同时开几小时注满？"
   - "如果所有的猫都怕水，Tom是猫，那Tom怕水吗？"
2. 为一个"技术方案评估 Agent"设计 CoT 提示词，让它从可行性、成本、风险三个维度分析技术方案
3. 实现 `COTChatSession` 类：自动在复杂问题后追加"请一步步思考"，简单问题直接回答

<details>
<summary>参考答案（COTChatSession）</summary>

```python
import re

class COTChatSession:
"""自动判断是否需要 CoT 的聊天会话"""

```
COT_TRIGGER_PATTERNS = [
    r"多少|几个|计算|等于",           # 数学/数量问题
    r"为什么|原因|为什么",             # 因果推理
    r"是否|会不会|能不能",             # 判断推理
    r"比较|区别|差异|优劣",            # 比较分析
    r"如何|怎么|步骤|流程",            # 过程推理
    r"如果|假设|假如",                 # 假设推理
]

SIMPLE_PATTERNS = [
    r"是什么|什么是|定义",             # 定义类
    r"翻译|英文|中文",                 # 翻译类
    r"帮我写|生成|创建",               # 生成类（不需要显式推理）
]

def __init__(self, api_key: str, model: str = "glm-4-flash"):
    self.api_key = api_key
    self.model = model
    self.messages: list[dict] = []

def _needs_cot(self, user_input: str) -> bool:
    """判断是否需要 CoT"""
    for pattern in self.COT_TRIGGER_PATTERNS:
        if re.search(pattern, user_input):
            return True
    for pattern in self.SIMPLE_PATTERNS:
        if re.search(pattern, user_input):
            return False
    # 默认：短问题不需要，长问题可能需要
    return len(user_input) > 50

async def chat(self, user_input: str) -> str:
    if self._needs_cot(user_input):
        enhanced_input = f"{user_input}\n\n请一步步思考，给出推理过程。"
    else:
        enhanced_input = user_input

    self.messages.append({"role": "user", "content": enhanced_input})

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {self.api_key}"}
    payload = {
        "model": self.model,
        "messages": self.messages,
        "temperature": 0.3 if self._needs_cot(user_input) else 0.7,
        "max_tokens": 2048,
        "stream": True,
    }

    full_content = ""
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
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            print(content, end="", flush=True)
                            full_content += content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    print()
    self.messages.append({"role": "assistant", "content": full_content})
    return full_content
```

```
</details>

---

## Day 4：结构化输出进阶

> Agent 需要可靠地从 LLM 获取结构化数据。本周 Day 2 已经用了 Few-Shot + JSON，今天深入更健壮的方案。

### 4.1 为什么结构化输出是 Agent 的命脉

```

Agent 的核心循环：

用户输入 → LLM 思考 → 输出结构化决策 → 程序解析 → 执行动作 → 结果回传 → LLM 继续思考

如果 LLM 输出的 JSON 格式不对 → 解析失败 → Agent 崩溃

所以：结构化输出的可靠性 = Agent 的可靠性

```

### 4.2 方案对比

```python
# === 方案1：Few-Shot + JSON（Day 2 已学） ===
# 优点：简单，所有模型都支持
# 缺点：不保证 100% 输出合法 JSON，需要后处理

# === 方案2：JSON Mode（API 原生支持） ===
# OpenAI / 智谱 的部分模型支持 response_format={"type": "json_object"}
# 优点：保证输出合法 JSON
# 缺点：不保证 JSON 的 schema 正确（字段名可能不对）

async def json_mode_chat(messages: list[dict], api_key: str) -> dict:
    """使用 JSON Mode 获取结构化输出"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "glm-4",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 1024,
        # 智谱 GLM-4 支持 JSON Mode
        # OpenAI: response_format={"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)

# === 方案3：Schema 约束 + 严格解析（推荐） ===
# 结合 JSON Mode + Pydantic 校验 + 修复重试
```



### 4.3 健壮的结构化输出方案



```python
import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

class StructuredOutput:
    """健壮的结构化输出获取器"""

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model

    def _extract_json(self, text: str) -> str:
        """从 LLM 输出中提取 JSON（处理各种异常格式）"""
        # 1. 尝试直接解析
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
                
        # 2. 提取 ```json ... ``` 代码块
        match = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if match:
            try:
                json.loads(match.group(1))
                return match.group(1)
            except json.JSONDecodeError:
                pass

        # 3. 找最外层的 { } 或 [ ]
        for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
            match = re.search(pattern, text)
            if match:
                try:
                    json.loads(match.group())
                    return match.group()
                except json.JSONDecodeError:
                    pass

        # 4. 修复常见问题
        # 去掉尾部逗号
        cleaned = re.sub(r',\s*([}\]])', r'\1', text)
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass

        raise ValueError(f"无法从输出中提取有效 JSON: {text[:300]}")

    def _build_extraction_prompt(self, user_input: str, schema: Type[T]) -> str:
        """构建结构化提取的提示词"""
        # 从 Pydantic 模型自动生成 JSON Schema 描述
        schema_json = schema.model_json_schema()
        properties = schema_json.get("properties", {})

        field_descriptions = []
        for name, info in properties.items():
            desc = info.get("description", name)
            field_type = info.get("type", "string")
            field_descriptions.append(f'  "{name}": {desc} (类型: {field_type})')

        fields_text = "\n".join(field_descriptions)

        return f"""请从用户输入中提取以下信息，以JSON格式返回。

需要提取的字段：
{fields_text}

## 规则
1. 只返回JSON，不要任何其他文字
2. 缺少的字段用 null
3. 数组字段如果只有一个元素也要用数组格式

## 用户输入
{user_input}

## JSON输出"""

    async def extract(
        self,
        user_input: str,
        schema: Type[T],
        max_retries: int = 2,
    ) -> T:
        """
        从用户输入中提取结构化数据
        自动构建提示词 → 调用 LLM → 解析 JSON → Pydantic 校验 → 失败重试
        """
        prompt = self._build_extraction_prompt(user_input, schema)

        for attempt in range(max_retries + 1):
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 1024,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]

            try:
                json_str = self._extract_json(content)
                data = json.loads(json_str)
                return schema(**data)
            except (ValueError, json.JSONDecodeError, ValidationError) as e:
                if attempt < max_retries:
                    # 把错误信息反馈给 LLM，让它修正
                    prompt += f"\n\n上次输出有误：{str(e)[:200]}\n请修正后重新输出。"
                else:
                    raise ValueError(
                        f"经过 {max_retries + 1} 次尝试仍无法获取有效结构化输出: {e}"
                    )

# === 使用示例 ===

from pydantic import Field
from typing import Optional

class MeetingInfo(BaseModel):
    title: str = Field(description="会议标题")
    date: str = Field(description="会议日期，格式 YYYY-MM-DD")
    time: str = Field(description="会议时间，格式 HH:MM")
    location: Optional[str] = Field(default=None, description="会议地点")
    participants: list[str] = Field(default_factory=list, description="参会人员")
    duration_minutes: Optional[int] = Field(default=None, description="会议时长（分钟）")

async def demo(api_key: str):
    extractor = StructuredOutput(api_key)

    user_input = "下周一上午10点，在3号会议室开项目评审会，张三、李四、王五参加，大概1个半小时"
    result = await extractor.extract(user_input, MeetingInfo)
    print(result.model_dump_json(indent=2))

# asyncio.run(demo("your-api-key"))
```



### 4.4 JSON Schema 约束提示词



```python
# 更高级的方案：在提示词中嵌入 JSON Schema，让 LLM 严格遵循

def build_schema_prompt(
    task_description: str,
    schema: Type[BaseModel],
    examples: list[tuple[str, dict]] | None = None,
) -> str:
    """
    构建 Schema 约束的结构化输出提示词
    自动从 Pydantic 模型生成 JSON Schema
    """
    schema_json = schema.model_json_schema()

    prompt = f"""{task_description}

## 输出格式要求
严格按照以下 JSON Schema 输出：

```json
{json.dumps(schema_json, ensure_ascii=False, indent=2)}
```



## 规则

1. 输出必须是合法的 JSON
2. 严格遵循上述 Schema，不要添加额外字段
3. required 字段不能为 null
4. 枚举类型的值必须在允许的列表中
   """
   
   if examples:
   prompt += "\n## 示例\n"
   for ex_input, ex_output in examples:
   prompt += f"\n输入：{ex_input}\n"
   prompt += f"输出：\n```json\n{json.dumps(ex_output, ensure_ascii=False, indent=2)}\n```\n"
   
   return prompt

# 使用

from enum import Enum

class Priority(str, Enum):
HIGH = "high"
MEDIUM = "medium"
LOW = "low"

class TaskItem(BaseModel):
name: str = Field(description="任务名称")
priority: Priority = Field(description="优先级")
assignee: Optional[str] = Field(default=None, description="负责人")
deadline: Optional[str] = Field(default=None, description="截止日期")
subtasks: list[str] = Field(default_factory=list, description="子任务列表")

prompt = build_schema_prompt(
task_description="请将用户的需求分解为任务列表",
schema=TaskItem,
examples=[
("明天之前完成首页设计", {
"name": "完成首页设计",
"priority": "high",
"assignee": None,
"deadline": "明天",
"subtasks": ["设计首页布局", "选择配色方案", "制作交互原型"]
}),
],
)

```

### 4.5 今日练习

1. 用 `StructuredOutput` 类实现一个"简历信息提取器"：输入一段自然语言简历，输出结构化的个人信息、教育经历、工作经历
2. 测试 `_extract_json` 的鲁棒性：构造以下异常格式的 LLM 输出，验证能否正确提取：
   - 输出前后有额外文字
   - JSON 在 ```json 代码块中
   - 有尾部逗号
   - 字段值中包含换行符
3. 实现"Schema 自修复"：如果 Pydantic 校验失败，自动把错误信息反馈给 LLM 重试

<details>
<summary>参考答案（简历提取器）</summary>

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Education(BaseModel):
    school: str = Field(description="学校名称")
    major: str = Field(description="专业")
    degree: str = Field(description="学历：本科/硕士/博士")
    start_date: Optional[str] = Field(default=None, description="开始时间")
    end_date: Optional[str] = Field(default=None, description="结束时间")

class WorkExperience(BaseModel):
    company: str = Field(description="公司名称")
    position: str = Field(description="职位")
    start_date: Optional[str] = Field(default=None, description="开始时间")
    end_date: Optional[str] = Field(default=None, description="结束时间")
    description: Optional[str] = Field(default=None, description="工作描述")

class Resume(BaseModel):
    name: str = Field(description="姓名")
    phone: Optional[str] = Field(default=None, description="手机号")
    email: Optional[str] = Field(default=None, description="邮箱")
    education: list[Education] = Field(default_factory=list, description="教育经历")
    work_experience: list[WorkExperience] = Field(default_factory=list, description="工作经历")
    skills: list[str] = Field(default_factory=list, description="技能列表")

async def extract_resume(text: str, api_key: str) -> Resume:
    extractor = StructuredOutput(api_key)
    return await extractor.extract(text, Resume)

# 测试
test_resume = """
张三，手机13800138000，邮箱zhangsan@email.com。
2018-2022年在华中科技大学读计算机科学本科。
2022-2024年在清华大学读人工智能硕士。
2024年至今在华为担任前端开发工程师，负责鸿蒙应用开发。
技能：Vue、ArkTS、ArkUI、Python、Git
"""

# result = await extract_resume(test_resume, "your-api-key")
```

</details>

---

## Day 5：Function Calling 初探

> Function Calling 是 Agent 的核心机制——让 LLM 能够"调用工具"。今天是入门，Week 4 会深入。

### 5.1 什么是 Function Calling



```
没有 Function Calling 时：
  用户 → LLM → 文本回答（只能说话，不能做事）

有了 Function Calling 时：
  用户 → LLM → "我想调用 get_weather('北京')" → 程序执行 → 结果回传 → LLM → 最终回答

Function Calling 不是让 LLM 真的执行代码，
而是让 LLM 输出"我想调用什么函数，参数是什么"，
由你的程序来决定是否执行。
```



### 5.2 工具定义格式



```python
# OpenAI / 智谱 统一的 Function 定义格式

TOOLS_DEFINITION = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，默认摄氏度"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2 + 3 * 4'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "在知识库中搜索相关文档",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量，默认3"
                    }
                },
                "required": ["query"]
            }
        }
    }
]
```



### 5.3 用 Pydantic 管理工具定义



```python
# 手动写 JSON Schema 容易出错，用 Pydantic 自动生成

from pydantic import BaseModel, Field
from typing import Optional

class GetWeatherParams(BaseModel):
    """获取天气的参数"""
    city: str = Field(description="城市名称，如'北京'、'上海'")
    unit: Optional[str] = Field(
        default="celsius",
        description="温度单位：celsius 或 fahrenheit"
    )

class CalculateParams(BaseModel):
    """计算数学表达式的参数"""
    expression: str = Field(description="数学表达式，如 '2 + 3 * 4'")

class SearchDocsParams(BaseModel):
    """搜索知识库的参数"""
    query: str = Field(description="搜索关键词")
    top_k: int = Field(default=3, description="返回结果数量")

def pydantic_to_tool(name: str, description: str, params_model: type[BaseModel]) -> dict:
    """将 Pydantic 模型转换为 OpenAI Function Calling 的工具定义"""
    schema = params_model.model_json_schema()
    # 移除 Pydantic 自动添加的 title 字段
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        prop.pop("title", None)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": schema,
        }
    }

# 自动生成工具定义
weather_tool = pydantic_to_tool("get_weather", "获取指定城市的天气信息", GetWeatherParams)
calc_tool = pydantic_to_tool("calculate", "计算数学表达式", CalculateParams)
search_tool = pydantic_to_tool("search_docs", "在知识库中搜索相关文档", SearchDocsParams)

tools = [weather_tool, calc_tool, search_tool]
# 打印查看
import json
print(json.dumps(tools, ensure_ascii=False, indent=2))
```



### 5.4 完整的 Function Calling 流程



```python
import httpx
import json
from typing import Callable, Any

class SimpleAgent:
    """带工具调用的简易 Agent"""

    def __init__(self, api_key: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model
        self.messages: list[dict] = []
        self.tools: list[dict] = []
        self.tool_handlers: dict[str, Callable] = {}

    def register_tool(self, name: str, description: str, params_model: type[BaseModel], handler: Callable):
        """注册一个工具"""
        tool_def = pydantic_to_tool(name, description, params_model)
        self.tools.append(tool_def)
        self.tool_handlers[name] = handler

    def set_system(self, content: str):
        self.messages.insert(0, {"role": "system", "content": content})

    async def run(self, user_input: str, max_iterations: int = 5) -> str:
        """
        运行 Agent 循环：
        用户输入 → LLM 思考 → 可能调用工具 → 结果回传 → LLM 继续思考 → 最终回答
        """
        self.messages.append({"role": "user", "content": user_input})

        for iteration in range(max_iterations):
            # 1. 调用 LLM
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.model,
                "messages": self.messages,
                "tools": self.tools,
                "temperature": 0.1,  # 工具调用用低温度
                "max_tokens": 1024,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]
            message = choice["message"]

            # 2. 检查是否需要调用工具
            tool_calls = message.get("tool_calls")

            if not tool_calls:
                # 没有工具调用 → LLM 给出了最终回答
                self.messages.append(message)
                return message.get("content", "")

            # 3. 有工具调用 → 执行工具
            self.messages.append(message)

            for tool_call in tool_calls:
                func_name = tool_call["function"]["name"]
                func_args = json.loads(tool_call["function"]["arguments"])
                tool_call_id = tool_call.get("id", func_name)

                print(f"  [工具调用] {func_name}({func_args})")

                # 执行工具
                if func_name in self.tool_handlers:
                    try:
                        result = self.tool_handlers[func_name](**func_args)
                        result_str = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
                    except Exception as e:
                        result_str = f"工具执行错误: {str(e)}"
                else:
                    result_str = f"未知工具: {func_name}"

                print(f"  [工具结果] {result_str[:100]}")

                # 4. 将工具结果回传给 LLM
                self.messages.append({
                    "role": "tool",
                    "content": result_str,
                    "tool_call_id": tool_call_id,
                })

        return "达到最大迭代次数，Agent 停止。"


# === 定义工具实现 ===

def get_weather(city: str, unit: str = "celsius") -> dict:
    """模拟天气API"""
    # 实际场景中这里调用真实 API
    mock_data = {
        "北京": {"temp": 25, "condition": "晴", "humidity": 40},
        "上海": {"temp": 28, "condition": "多云", "humidity": 65},
        "武汉": {"temp": 30, "condition": "小雨", "humidity": 75},
    }
    result = mock_data.get(city, {"temp": 20, "condition": "未知", "humidity": 50})
    if unit == "fahrenheit":
        result["temp"] = result["temp"] * 9/5 + 32
    result["city"] = city
    result["unit"] = unit
    return result

def calculate(expression: str) -> dict:
    """安全地计算数学表达式"""
    # 安全限制：只允许数字和基本运算符
    import re
    if not re.match(r'^[\d\s\+\-\*/\.\(\)]+$', expression):
        return {"error": "不安全的表达式"}
    try:
        result = eval(expression)  # 注意：生产环境不要用 eval，这里仅作演示
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}

def search_docs(query: str, top_k: int = 3) -> dict:
    """模拟知识库搜索"""
    mock_docs = {
        "Vue": [
            {"title": "Vue3 组合式API指南", "content": "setup() 函数是组合式API的入口..."},
            {"title": "Pinia 状态管理", "content": "Pinia 是 Vue3 推荐的状态管理方案..."},
        ],
        "Python": [
            {"title": "Python 异步编程", "content": "async/await 是 Python 异步编程的核心..."},
            {"title": "Pydantic 数据验证", "content": "Pydantic 使用类型提示进行数据验证..."},
        ],
    }
    results = []
    for key, docs in mock_docs.items():
        if key.lower() in query.lower():
            results.extend(docs[:top_k])
    if not results:
        results = [{"title": "未找到相关文档", "content": "请尝试其他关键词"}]
    return {"query": query, "results": results[:top_k]}


# === 使用 Agent ===

async def agent_demo(api_key: str):
    agent = SimpleAgent(api_key, model="glm-4")

    # 注册工具
    agent.register_tool("get_weather", "获取指定城市的天气信息", GetWeatherParams, get_weather)
    agent.register_tool("calculate", "计算数学表达式", CalculateParams, calculate)
    agent.register_tool("search_docs", "在知识库中搜索相关文档", SearchDocsParams, search_docs)

    # 设置系统提示词
    agent.set_system("你是一个智能助手，可以使用工具来帮助用户。根据用户的问题选择合适的工具。")

    # 测试1：需要调用工具
    print("=== 测试1：天气查询 ===")
    result = await agent.run("武汉今天天气怎么样？")
    print(f"最终回答: {result}\n")

    # 测试2：需要计算
    agent.messages.clear()
    agent.set_system("你是一个智能助手，可以使用工具来帮助用户。根据用户的问题选择合适的工具。")
    print("=== 测试2：数学计算 ===")
    result = await agent.run("(15 + 27) * 3 等于多少？")
    print(f"最终回答: {result}\n")

    # 测试3：不需要工具
    agent.messages.clear()
    agent.set_system("你是一个智能助手，可以使用工具来帮助用户。根据用户的问题选择合适的工具。")
    print("=== 测试3：普通对话 ===")
    result = await agent.run("你好，请自我介绍")
    print(f"最终回答: {result}\n")

# asyncio.run(agent_demo("your-api-key"))
```



### 5.5 Function Calling 的注意事项



```python
# === 1. 工具描述的质量直接影响调用准确率 ===

# 差：描述模糊
bad_tool = {
    "name": "search",
    "description": "搜索东西",
    "parameters": {"type": "object", "properties": {"q": {"type": "string"}}}
}

# 好：描述具体
good_tool = {
    "name": "search_docs",
    "description": "在Python编程知识库中搜索相关文档，返回标题和内容摘要",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词，如'异步编程'、'列表推导式'"
            }
        },
        "required": ["query"]
    }
}

# === 2. 工具数量不宜过多 ===
# 超过 10-15 个工具时，LLM 的选择准确率会下降
# 工具定义也消耗 Token

# 优化：按需加载工具（根据用户意图先分类，再加载对应工具子集）

# === 3. 参数的 description 很关键 ===
# LLM 根据 description 理解参数的含义，决定传什么值

# === 4. 永远不要信任 LLM 的参数 ===
# LLM 可能传入非法参数，你的工具实现必须做校验

def safe_get_weather(city: str, unit: str = "celsius") -> dict:
    # 校验参数
    if not city or len(city) > 50:
        return {"error": "无效的城市名称"}

    allowed_cities = ["北京", "上海", "武汉", "深圳", "广州"]
    if city not in allowed_cities:
        return {"error": f"暂不支持{city}的天气查询，支持的城市：{', '.join(allowed_cities)}"}

    if unit not in ["celsius", "fahrenheit"]:
        unit = "celsius"  # 回退到默认值

    # ... 实际查询逻辑
```



### 5.6 今日练习

1. 给 `SimpleAgent` 添加以下工具并测试：
   - `get_time()` —— 获取当前时间
   - `send_email(to, subject, body)` —— 模拟发送邮件
   - `list_files(directory)` —— 列出目录下的文件
2. 测试"多工具场景"：问一个需要调用多个工具的问题（如"武汉热还是上海热？"需要调用两次天气 API）
3. 测试"工具选择错误"：故意问一个模糊的问题，观察 LLM 是否选对了工具

<details>
<summary>参考答案</summary>

```python
from datetime import datetime
import os

class GetCurrentTimeParams(BaseModel):
timezone: Optional[str] = Field(default="Asia/Shanghai", description="时区")

class SendEmailParams(BaseModel):
to: str = Field(description="收件人邮箱")
subject: str = Field(description="邮件主题")
body: str = Field(description="邮件正文")

class ListFilesParams(BaseModel):
directory: str = Field(description="目录路径")
pattern: Optional[str] = Field(default="*", description="文件匹配模式")

def get_current_time(timezone: str = "Asia/Shanghai") -> dict:
now = datetime.now()
return {
"current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
"timezone": timezone,
"weekday": ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()],
}

def send_email(to: str, subject: str, body: str) -> dict:
# 模拟发送
print(f"  [邮件已发送] To: {to}, Subject: {subject}")
return {"status": "sent", "to": to, "subject": subject}

def list_files(directory: str, pattern: str = "*") -> dict:
try:
path = Path(directory).expanduser()
if not path.exists():
return {"error": f"目录不存在: {directory}"}
files = [f.name for f in path.iterdir() if f.match(pattern)]
return {"directory": str(path), "files": files, "count": len(files)}
except Exception as e:
return {"error": str(e)}

# 注册

# agent.register_tool("get_current_time", "获取当前日期和时间", GetCurrentTimeParams, get_current_time)

# agent.register_tool("send_email", "发送电子邮件", SendEmailParams, send_email)

# agent.register_tool("list_files", "列出目录下的文件", ListFilesParams, list_files)

# 测试多工具调用

# result = await agent.run("武汉热还是上海热？")

# 预期：调用两次 get_weather，然后对比

# 测试模糊问题

# result = await agent.run("帮我查查信息")

# 预期：可能问用户查什么，或者选择 search_docs

```
</details>

---

## Day 6：综合实战 —— 多功能 Agent 系统

> 把本周所有知识整合，构建一个完整的、带 CoT 推理 + Function Calling + 结构化输出的 Agent。

### 项目目标

```

$ python multi_agent.py --api-key your-key

🤖 SmartAgent v1.0
已加载工具: weather, calculator, search, time, file_list

> 武汉明天适合户外运动吗？
> 思考：需要查武汉天气，再根据天气判断是否适合户外运动
> [工具调用] get_weather({"city": "武汉"})
> [工具结果] {"temp": 30, "condition": "小雨", "humidity": 75}

回答：武汉明天有小雨，气温30°C，湿度75%。不太适合户外运动，
建议选择室内活动，或者带伞进行短时间户外散步。

> 帮我算一下团队5个人团建的预算，每人预算200元
> 思考：这是一个简单的乘法计算
> [工具调用] calculate({"expression": "5 * 200"})
> [工具结果] {"result": 1000}

回答：5人团建，每人200元预算，总预算为1000元。

> /tools
> 已注册工具：

1. get_weather - 获取城市天气信息
2. calculate - 计算数学表达式
3. search_docs - 搜索知识库
4. get_current_time - 获取当前时间
5. list_files - 列出目录文件

> /quit

```

### 完整实现

创建 `smart_agent.py`：

```python
"""
SmartAgent —— 带推理链和工具调用的智能 Agent
功能：
1. CoT 推理（自动判断是否需要）
2. Function Calling（工具注册与调用）
3. 结构化输出（Pydantic 校验）
4. 多轮对话 + 上下文管理
5. 交互式命令行界面
"""

import asyncio
import json
import re
import time
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

import httpx
import tiktoken
from pydantic import BaseModel, Field

# === 1. 工具注册系统 ===

class ToolRegistry:
    """工具注册中心"""

    def __init__(self):
        self.tools: list[dict] = []
        self.handlers: dict[str, Callable] = {}
        self.descriptions: dict[str, str] = {}

    def register(
        self,
        name: str,
        description: str,
        params_model: type[BaseModel],
        handler: Callable,
    ):
        schema = params_model.model_json_schema()
        schema.pop("title", None)
        for prop in schema.get("properties", {}).values():
            prop.pop("title", None)

        self.tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": schema,
            }
        })
        self.handlers[name] = handler
        self.descriptions[name] = description

    def execute(self, name: str, arguments: dict) -> str:
        if name not in self.handlers:
            return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)
        try:
            result = self.handlers[name](**arguments)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"工具执行错误: {str(e)}"}, ensure_ascii=False)

    def list_tools(self) -> str:
        lines = ["已注册工具："]
        for i, tool in enumerate(self.tools, 1):
            name = tool["function"]["name"]
            desc = self.descriptions[name]
            lines.append(f"  {i}. {name} - {desc}")
        return "\n".join(lines)

# === 2. 内置工具实现 ===

def get_weather(city: str, unit: str = "celsius") -> dict:
    mock = {
        "北京": {"temp": 25, "condition": "晴", "humidity": 40, "wind": "北风3级"},
        "上海": {"temp": 28, "condition": "多云", "humidity": 65, "wind": "东南风2级"},
        "武汉": {"temp": 30, "condition": "小雨", "humidity": 75, "wind": "南风2级"},
        "深圳": {"temp": 32, "condition": "雷阵雨", "humidity": 80, "wind": "南风3级"},
    }
    result = mock.get(city, {"temp": 22, "condition": "晴", "humidity": 50, "wind": "微风"})
    if unit == "fahrenheit":
        result["temp"] = round(result["temp"] * 9/5 + 32, 1)
    return {"city": city, **result, "unit": unit}

def calculate(expression: str) -> dict:
    if not re.match(r'^[\d\s\+\-\*/\.\(\)%]+$', expression):
        return {"error": "表达式包含不允许的字符"}
    try:
        result = eval(expression)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}

def search_docs(query: str, top_k: int = 3) -> dict:
    mock_db = [
        {"title": "Vue3 组合式API", "content": "setup()是入口...", "tags": ["vue", "前端"]},
        {"title": "Python异步编程", "content": "async/await核心...", "tags": ["python"]},
        {"title": "Agent设计模式", "content": "ReAct模式...", "tags": ["ai", "agent"]},
        {"title": "RAG检索增强", "content": "向量检索+LLM...", "tags": ["ai", "rag"]},
    ]
    results = [d for d in mock_db if any(kw in d["title"] or kw in " ".join(d["tags"])
               for kw in query.split())]
    if not results:
        results = mock_db[:top_k]  # 默认返回前几个
    return {"query": query, "results": results[:top_k]}

def get_current_time(timezone: str = "Asia/Shanghai") -> dict:
    now = datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": ["周一","周二","周三","周四","周五","周六","周日"][now.weekday()],
    }

def list_files(directory: str, pattern: str = "*") -> dict:
    try:
        path = Path(directory).expanduser()
        if not path.exists():
            return {"error": f"目录不存在: {directory}"}
        files = sorted([f.name for f in path.iterdir() if f.match(pattern)])[:20]
        return {"directory": str(path), "files": files, "count": len(files)}
    except Exception as e:
        return {"error": str(e)}

# Pydantic 参数模型
class WeatherParams(BaseModel):
    city: str = Field(description="城市名称")
    unit: Optional[str] = Field(default="celsius", description="温度单位")

class CalcParams(BaseModel):
    expression: str = Field(description="数学表达式")

class SearchParams(BaseModel):
    query: str = Field(description="搜索关键词")
    top_k: int = Field(default=3, description="结果数量")

class TimeParams(BaseModel):
    timezone: Optional[str] = Field(default="Asia/Shanghai", description="时区")

class ListFilesParams(BaseModel):
    directory: str = Field(description="目录路径")
    pattern: Optional[str] = Field(default="*", description="匹配模式")

# === 3. Agent 核心 ===

class SmartAgent:
    def __init__(self, api_key: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model
        self.messages: list[dict] = []
        self.registry = ToolRegistry()
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self._register_default_tools()

    def _register_default_tools(self):
        self.registry.register("get_weather", "获取指定城市的天气信息", WeatherParams, get_weather)
        self.registry.register("calculate", "计算数学表达式", CalcParams, calculate)
        self.registry.register("search_docs", "在知识库中搜索相关文档", SearchParams, search_docs)
        self.registry.register("get_current_time", "获取当前日期和时间", TimeParams, get_current_time)
        self.registry.register("list_files", "列出目录下的文件", ListFilesParams, list_files)

    def set_system(self, content: str):
        self.messages = [m for m in self.messages if m["role"] != "system"]
        self.messages.insert(0, {"role": "system", "content": content})

    async def run(self, user_input: str, max_iterations: int = 5) -> str:
        self.messages.append({"role": "user", "content": user_input})

        for iteration in range(max_iterations):
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": self.model,
                "messages": self.messages,
                "tools": self.registry.tools,
                "temperature": 0.1,
                "max_tokens": 2048,
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]
            message = choice["message"]
            finish_reason = choice.get("finish_reason", "")

            # 工具调用
            tool_calls = message.get("tool_calls")
            if tool_calls:
                self.messages.append(message)
                for tc in tool_calls:
                    func_name = tc["function"]["name"]
                    func_args = json.loads(tc["function"]["arguments"])
                    print(f"  [工具调用] {func_name}({json.dumps(func_args, ensure_ascii=False)})")

                    result = self.registry.execute(func_name, func_args)
                    print(f"  [工具结果] {result[:80]}")

                    self.messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tc.get("id", func_name),
                    })
                continue  # 继续循环，让 LLM 处理工具结果

            # 最终回答
            content = message.get("content", "")
            self.messages.append(message)
            return content

        return "（达到最大迭代次数）"

# === 4. 命令行界面 ===

SYSTEM_PROMPT = """你是一个智能助手，可以使用工具帮助用户。

## 行为规则
1. 根据用户问题选择合适的工具
2. 如果问题不需要工具，直接回答
3. 使用工具后，基于工具结果给出完整的回答
4. 如果工具返回错误，告知用户并建议替代方案
5. 用中文回答，简洁清晰
"""

async def main():
    import sys

    print("🤖 SmartAgent v1.0")
    print("━" * 40)

    # API Key
    config_path = Path("~/agent-learning/week1/data/chat_config.json").expanduser()
    api_key = ""
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            api_key = json.load(f).get("api_key", "")
    if not api_key:
        api_key = input("API Key: ").strip()

    agent = SmartAgent(api_key, model="glm-4")
    agent.set_system(SYSTEM_PROMPT)
    print(agent.registry.list_tools())

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("再见！")
            break
        elif user_input == "/tools":
            print(agent.registry.list_tools())
        elif user_input == "/history":
            for msg in agent.messages:
                role = msg["role"]
                content = str(msg.get("content", ""))[:80]
                print(f"  [{role}] {content}")
        elif user_input == "/clear":
            agent.messages.clear()
            agent.set_system(SYSTEM_PROMPT)
            print("历史已清空")
        elif user_input == "/help":
            print("命令：/tools /history /clear /help /quit")
        else:
            try:
                answer = await agent.run(user_input)
                print(f"\n{answer}")
            except httpx.HTTPStatusError as e:
                print(f"API错误: {e.response.status_code}")
            except Exception as e:
                print(f"错误: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
```



### Day 6 练习

1. 给 SmartAgent 添加"记忆功能"：将对话历史保存到 JSON 文件，下次启动时自动加载
2. 添加 `/retry` 命令：对上次回答不满意时重新生成
3. 添加工具调用的 CoT 展示：在调用工具前显示 LLM 的推理过程

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单



```
系统提示词设计：
[ ] 能写出包含角色、规则、格式、边界的完整系统提示词
[ ] 理解"正面指令 > 负面指令"原则
[ ] 理解结构化提示词 > 散文式提示词
[ ] 能根据 Agent 场景定制系统提示词
[ ] 知道如何优化系统提示词的 Token 开销

Few-Shot Learning：
[ ] 理解 Zero/One/Few-Shot 的区别和适用场景
[ ] 知道 Few-Shot 的4个核心原则
[ ] 能为不同任务设计 Few-Shot 示例
[ ] 理解动态 Few-Shot 选择器的原理
[ ] 知道 Few-Shot 的 Token 开销和取舍

Chain of Thought：
[ ] 理解 CoT 为什么能提升推理质量
[ ] 掌握三种 CoT 触发方式
[ ] 能为 Agent 决策场景设计 CoT 提示词
[ ] 理解 CoT 的局限性（Token 消耗、推理可能错误）
[ ] 知道按需 CoT 和自我验证的改进方法

结构化输出：
[ ] 能用 Few-Shot + JSON 获取结构化输出
[ ] 能用 JSON Mode 获取结构化输出
[ ] 能实现健壮的 JSON 提取和校验
[ ] 能用 Pydantic 自动生成 Schema 提示词
[ ] 能实现"校验失败 → 反馈重试"机制

Function Calling：
[ ] 理解 Function Calling 的工作原理
[ ] 能用 Pydantic 定义工具参数模型
[ ] 能实现完整的工具注册和调用流程
[ ] 理解工具描述对调用准确率的影响
[ ] 知道工具参数必须做校验，不能信任 LLM
```



### 7.2 综合练习题

实现一个 **面试模拟 Agent**，要求：

1. **系统提示词**：设计面试官角色的完整提示词
2. **Few-Shot**：提供 3 个不同难度的问题示例（简单/中等/困难）
3. **CoT 推理**：面试官根据候选人回答决定追问方向时，展示推理过程
4. **结构化输出**：每轮结束后输出 `InterviewEvaluation`：
   ```python
   class InterviewEvaluation(BaseModel):
       question: str
       answer_quality: str  # good/partial/poor
       follow_up: str       # 追问方向
       score: float         # 0-10
   ```
5. **Function Calling**：注册一个 `get_question_bank(topic, difficulty)` 工具，按主题和难度获取面试题
6. 完整的多轮面试流程：开场 → 提问 → 评价 → 追问 → 结束 → 总评

> 这个练习涵盖了本周所有知识点，做完说明你已掌握 Week 3 的核心内容。

<details>
<summary>参考答案框架</summary>

```python
"""
面试模拟 Agent
"""

class QuestionBankParams(BaseModel):
topic: str = Field(description="面试主题：前端/后端/AI/系统设计")
difficulty: str = Field(default="medium", description="难度：easy/medium/hard")

class InterviewEvaluation(BaseModel):
question: str = Field(description="面试问题")
answer_quality: str = Field(description="回答质量：good/partial/poor")
follow_up: str = Field(description="追问方向")
score: float = Field(ge=0, le=10, description="评分0-10")

def get_question_bank(topic: str, difficulty: str = "medium") -> dict:
questions = {
"前端": {
"easy": ["解释 CSS 盒模型", "Vue 的双向绑定原理"],
"medium": ["虚拟 DOM 的工作原理", "Webpack 和 Vite 的区别"],
"hard": ["如何实现一个微前端框架", "浏览器渲染管线优化"],
},
"AI": {
"easy": ["什么是过拟合", "解释 Transformer 的自注意力"],
"medium": ["RAG 的检索策略有哪些", "如何评估 LLM 输出质量"],
"hard": ["设计一个 Multi-Agent 系统", "LLM 的幻觉问题如何缓解"],
},
}
topic_questions = questions.get(topic, questions["前端"])
q_list = topic_questions.get(difficulty, topic_questions["medium"])
import random
return {"topic": topic, "difficulty": difficulty, "question": random.choice(q_list)}

INTERVIEWER_SYSTEM_PROMPT = """你是一个高级技术面试官。

## 角色

- 专业、友善但不放过薄弱点
- 根据候选人水平调整难度
- 每次只问一个问题

## 工作流程

1. 欢迎候选人，询问面试方向（前端/后端/AI/系统设计）
2. 使用 get_question_bank 获取面试题
3. 根据回答质量决定：答好→加难度追问，答差→简化或换方向
4. 每轮评价后输出结构化的 InterviewEvaluation
5. 5-8轮后给出总评

## 推理要求

在决定追问方向前，先思考：

1. 候选人回答的亮点是什么
2. 遗漏了什么关键点
3. 应该加深还是转向

## 输出格式

**面试官**: [问题/评价]

[候选人回答后]

**评价推理**:

- 亮点: ...
- 不足: ...
- 决策: 加深/简化/转向

**结构化评价**:

```json
{"question": "...", "answer_quality": "...", "follow_up": "...", "score": 8.0}
```"""

# 使用 SmartAgent 框架
# agent = SmartAgent(api_key)
# agent.registry.register("get_question_bank", "获取面试题库", QuestionBankParams, get_question_bank)
# agent.set_system(INTERVIEWER_SYSTEM_PROMPT)
# result = await agent.run("你好，我准备好了")
```

</details>

---

## 本周知识图谱



```
Prompt Engineering
├── 系统提示词设计（Day 1）
│   ├── 7要素结构（角色/任务/规则/格式/背景/示例/边界）
│   ├── 设计原则（具体>抽象 / 正面>负面 / 结构化>散文）
│   ├── 优先级规则
│   └── Token 优化
│
├── Few-Shot Learning（Day 2）
│   ├── Zero/One/Few-Shot 对比
│   ├── 4原则（覆盖全类别/顺序/复杂度一致/格式一致）
│   ├── 动态 Few-Shot 选择
│   └── Token 开销管理
│
├── Chain of Thought（Day 3）
│   ├── 三种触发方式（Zero-Shot CoT / Few-Shot CoT / Auto-CoT）
│   ├── Agent 决策推理
│   ├── 代码调试 CoT
│   ├── 任务规划 CoT
│   └── 局限与改进（按需CoT / 自我验证）
│
├── 结构化输出进阶（Day 4）
│   ├── 方案对比（Few-Shot+JSON / JSON Mode / Schema约束）
│   ├── 健壮的 JSON 提取
│   ├── Pydantic → JSON Schema 自动生成
│   └── 校验失败 → 反馈重试
│
├── Function Calling（Day 5）
│   ├── 工作原理
│   ├── 工具定义格式
│   ├── Pydantic 管理工具定义
│   ├── 完整调用循环
│   └── 注意事项（描述质量/数量/参数校验）
│
└── 综合实战（Day 6-7）
    ├── SmartAgent 系统
    └── 面试模拟 Agent
```



## Prompt Engineering 速查表



```
┌─────────────────────────────────────────────────────────┐
│              Prompt Engineering 速查表                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  系统提示词模板：                                         │
│  ┌─────────────────────────────────────────────┐        │
│  │ 你是[角色]。                                  │        │
│  │ ## 任务: [做什么]                             │        │
│  │ ## 规则: [N条清晰规则]                        │        │
│  │ ## 格式: [输出格式]                           │        │
│  │ ## 边界: [超出能力怎么办]                      │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
│  Few-Shot 模板：                                         │
│  ┌─────────────────────────────────────────────┐        │
│  │ [任务说明]                                    │        │
│  │ 输入: {ex1_input}                            │        │
│  │ 输出: {ex1_output}                           │        │
│  │ 输入: {ex2_input}                            │        │
│  │ 输出: {ex2_output}                           │        │
│  │ 输入: {user_input}                           │        │
│  │ 输出:                                        │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
│  CoT 触发：                                              │
│  ┌─────────────────────────────────────────────┐        │
│  │ Zero-Shot: "请一步步思考"                      │        │
│  │ Few-Shot:  示例中包含推理过程                   │        │
│  │ Agent:    "思考→工具调用→结果→回答"             │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
│  结构化输出：                                             │
│  ┌─────────────────────────────────────────────┐        │
│  │ 1. 提示词中给出 JSON Schema                    │        │
│  │ 2. Temperature = 0                            │        │
│  │ 3. 解析时提取 + 校验 + 重试                     │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
│  Function Calling：                                      │
│  ┌─────────────────────────────────────────────┐        │
│  │ 1. description 要具体                         │        │
│  │ 2. 参数校验不能省                              │        │
│  │ 3. 工具不超过 10-15 个                         │        │
│  │ 4. 工具结果要回传 LLM 做最终回答                │        │
│  └─────────────────────────────────────────────┘        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```



## 下周预告

Week 4 将进入 **RAG 系统 + Multi-Tool Agent**：

- 向量数据库实战（Chroma / Milvus Lite）
- RAG 全流程：文档处理 → Embedding → 检索 → 生成 → 评测
- 多工具 Agent 的编排策略
- Agent 评测方法
- 综合项目：知识库问答 Agent
