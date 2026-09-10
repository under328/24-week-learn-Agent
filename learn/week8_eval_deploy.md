# 第2月第8周：Agent 评测与部署

> 适用对象：已完成 Week 1-7（Python基础 + LLM核心 + Prompt Engineering + RAG/Multi-Tool Agent + LangChain框架 + LangGraph状态机 + Multi-Agent系统）的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：掌握 Agent 系统的评测方法论、自动化测试框架、性能优化与成本控制策略，能用 FastAPI + Docker 将 Agent 部署到生产环境

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month2/week8
cd month2/week8

python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 本周新增依赖
pip install langchain langchain-core langchain-openai langgraph httpx pydantic
pip install fastapi uvicorn pytest asyncio aiohttp
pip freeze > requirements.txt
```

**关于 Agent 评测与部署**：前面 7 周我们学会了构建 Agent——从单 Agent 到 Multi-Agent，从 RAG 到工具调用。但"能跑"和"能上线"之间有巨大鸿沟：Agent 输出不稳定怎么办？延迟太高怎么办？API 费用超预算怎么办？线上出 bug 怎么定位？本周解决这些工程化问题。

**本周核心问题**：
- 如何量化评估 Agent 的质量？（评测指标）
- 如何自动化测试 Agent？（测试框架）
- 如何降低延迟和成本？（性能优化）
- 如何部署到生产环境？（部署方案）
- 如何监控线上 Agent？（可观测性）

---

## Day 1：Agent 评测指标体系

> 评测是部署的前提。你不能改进你无法衡量的东西。

### 1.1 为什么 Agent 评测难

传统软件测试：输入确定 → 输出确定 → 断言容易

Agent 测试：输入确定 → 输出**不确定**（LLM 有随机性）→ 断言困难

```
传统函数测试：
  assert add(1, 2) == 3          # 每次都一样

Agent 测试：
  result = agent.invoke("写一首诗")
  assert result == ???           # 每次都不一样！
```

**Agent 评测的三个层次**：

```
┌──────────────────────────────────────────────────┐
│  层次            │  评测什么        │  方法        │
│──────────────────┼─────────────────┼─────────────│
│  组件级          │  单个工具/Prompt │  单元测试    │
│  端到端级        │  完整任务执行    │  黄金集+评分 │
│  在线级          │  线上真实表现    │  A/B + 监控  │
└──────────────────────────────────────────────────┘
```

### 1.2 核心评测指标

**1. 准确性指标（Accuracy）**

```python
"""Agent 准确性评测：任务完成率"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 评测数据集 ===

EVAL_DATASET = [
    {
        "id": "q001",
        "input": "2+3等于几？只回答数字",
        "expected_keywords": ["5"],
        "category": "math",
    },
    {
        "id": "q002",
        "input": "中国的首都是哪里？只回答城市名",
        "expected_keywords": ["北京"],
        "category": "knowledge",
    },
    {
        "id": "q003",
        "input": "将以下英文翻译为中文：Hello World",
        "expected_keywords": ["你好", "世界"],
        "category": "translation",
    },
    {
        "id": "q004",
        "input": "Python 中 list 和 tuple 的区别？用一句话回答",
        "expected_keywords": ["可变", "不可变"],  # 或 "mutable"
        "category": "coding",
    },
    {
        "id": "q005",
        "input": "写一个 Python 函数判断回文数",
        "expected_keywords": ["def", "return", "str"],
        "category": "coding",
    },
]

# === 关键词匹配评测 ===

def keyword_match_eval(response: str, expected_keywords: list[str]) -> dict:
    """简单关键词匹配：检查响应是否包含期望关键词"""
    response_lower = response.lower()
    matched = []
    missed = []
    for kw in expected_keywords:
        if kw.lower() in response_lower:
            matched.append(kw)
        else:
            missed.append(kw)
    passed = len(matched) > 0  # 至少匹配一个
    return {
        "passed": passed,
        "matched": matched,
        "missed": missed,
        "score": len(matched) / len(expected_keywords),
    }

# === 运行评测 ===

def run_keyword_eval():
    llm = make_llm(0)
    results = []
    for case in EVAL_DATASET:
        resp = llm.invoke([HumanMessage(content=case["input"])])
        content = resp.content
        eval_result = keyword_match_eval(content, case["expected_keywords"])
        results.append({
            "id": case["id"],
            "category": case["category"],
            "response": content[:80],
            **eval_result,
        })

    # 汇总
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"=== 关键词匹配评测 ===")
    print(f"通过: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"平均得分: {sum(r['score'] for r in results)/total:.2f}")
    print()
    for r in results:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']} ({r['category']}): {r['response']}")
        if r["missed"]:
            print(f"         缺失关键词: {r['missed']}")

run_keyword_eval()
```

**2. 质量评分指标（LLM-as-Judge）**

关键词匹配太粗糙——它不能判断回答的质量。更好的方案是用另一个 LLM 来评分：

```python
"""LLM-as-Judge：用 LLM 评价 Agent 输出质量"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 评分 Prompt ===

JUDGE_PROMPT = """你是一个严格的评分员。请对以下回答进行评分。

问题: {question}
回答: {answer}
评分标准（1-5分）:
  5分: 完全正确，内容完整，表述清晰
  3分: 基本正确，但有遗漏或表述不清
  1分: 完全错误或答非所问

请用 JSON 格式输出:
{{"score": <1-5>, "reason": "<简短理由>"}}
"""

def llm_judge(question: str, answer: str) -> dict:
    """用 LLM 对回答进行 1-5 评分"""
    judge_llm = make_llm(0)
    prompt = JUDGE_PROMPT.format(question=question, answer=answer)
    resp = judge_llm.invoke([HumanMessage(content=prompt)])
    try:
        content = resp.content
        s, e = content.find("{"), content.rfind("}") + 1
        if s >= 0 and e > s:
            result = json.loads(content[s:e])
            return {"score": int(result.get("score", 0)), "reason": result.get("reason", "")}
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return {"score": 0, "reason": "评分解析失败"}

# === 测试集 ===

TEST_CASES = [
    {"q": "解释什么是递归", "a": "递归是指函数调用自身来解决子问题的方式，需要终止条件防止无限循环。"},
    {"q": "解释什么是递归", "a": "递归就是函数调用自己。"},
    {"q": "解释什么是递归", "a": "递归是一种算法。"},  # 模糊回答
]

for case in TEST_CASES:
    result = llm_judge(case["q"], case["a"])
    print(f"问题: {case['q']}")
    print(f"回答: {case['a']}")
    print(f"评分: {result['score']}/5 - {result['reason']}")
    print()
```

**3. 轨迹评测（Trajectory Evaluation）**

Agent 不仅仅是最终回答——**调用工具的路径**也很重要。好的 Agent 应该用最少的步骤得到正确答案。

```python
"""轨迹评测：检查 Agent 的工具调用路径是否合理"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 轨迹评测指标 ===

def evaluate_trajectory(
    steps: list[dict],
    expected_tools: list[str],
    forbidden_tools: list[str] | None = None,
) -> dict:
    """
    评测 Agent 的工具调用轨迹

    Args:
        steps: Agent 执行步骤列表，每个步骤含 tool 和 input
        expected_tools: 期望使用的工具列表
        forbidden_tools: 不应该使用的工具列表
    """
    forbidden_tools = forbidden_tools or []
    used_tools = [s["tool"] for s in steps]

    # 指标 1: 工具覆盖率——是否用到了所有期望工具
    expected_set = set(expected_tools)
    used_set = set(used_tools)
    tool_coverage = len(expected_set & used_set) / len(expected_set) if expected_set else 1.0

    # 指标 2: 禁用工具违规——是否使用了不该用的工具
    violations = [t for t in used_tools if t in forbidden_tools]

    # 指标 3: 步骤效率——实际步骤数 vs 期望步骤数
    step_count = len(steps)
    expected_steps = len(expected_tools)
    efficiency = min(expected_steps / step_count, 1.0) if step_count > 0 else 0

    # 指标 4: 冗余调用——同一工具被重复调用多次
    from collections import Counter
    tool_counts = Counter(used_tools)
    redundant = {tool: count for tool, count in tool_counts.items() if count > 2}

    return {
        "tool_coverage": tool_coverage,
        "violations": violations,
        "step_count": step_count,
        "efficiency": efficiency,
        "redundant_calls": redundant,
        "used_tools": used_tools,
    }

# === 模拟评测 ===

# 场景：用户问"今天北京天气怎样"，期望 Agent 调用天气工具
trajectory_1 = [
    {"tool": "weather_api", "input": "北京"},
    {"tool": "format_response", "input": "sunny, 25C"},
]

# 场景：低效 Agent——重复调用同一工具
trajectory_2 = [
    {"tool": "weather_api", "input": "北京"},
    {"tool": "weather_api", "input": "北京"},  # 冗余
    {"tool": "weather_api", "input": "北京"},  # 冗余
    {"tool": "format_response", "input": "sunny"},
]

# 场景：用了不该用的工具
trajectory_3 = [
    {"tool": "web_search", "input": "北京天气"},   # 不应该搜索
    {"tool": "weather_api", "input": "北京"},
    {"tool": "format_response", "input": "result"},
]

for i, traj in enumerate([trajectory_1, trajectory_2, trajectory_3], 1):
    result = evaluate_trajectory(
        traj,
        expected_tools=["weather_api", "format_response"],
        forbidden_tools=["web_search"],
    )
    print(f"=== 轨迹 {i} ===")
    print(f"  工具覆盖: {result['tool_coverage']:.0%}")
    print(f"  步骤数: {result['step_count']}, 效率: {result['efficiency']:.0%}")
    print(f"  违规工具: {result['violations'] or '无'}")
    print(f"  冗余调用: {result['redundant_calls'] or '无'}")
    print()
```

### 1.3 评测数据集构建

```python
"""构建评测数据集：Golden Set"""

import json
import os

# === Golden Set 结构 ===

GOLDEN_SET = {
    "version": "1.0",
    "description": "Agent 基础能力评测集",
    "cases": [
        {
            "id": "math_001",
            "category": "数学计算",
            "difficulty": "easy",
            "input": "计算 15 * 24 = ?",
            "expected_output": "360",
            "eval_method": "exact_match",  # 精确匹配
            "eval_params": {},
        },
        {
            "id": "math_002",
            "category": "数学计算",
            "difficulty": "medium",
            "input": "一个长方形长8米宽5米，求面积和周长",
            "expected_output": "面积40平方米，周长26米",
            "eval_method": "keyword_match",
            "eval_params": {"keywords": ["40", "26"]},
        },
        {
            "id": "code_001",
            "category": "代码生成",
            "difficulty": "easy",
            "input": "写一个 Python 函数，返回两个数的较大值",
            "expected_output": "def max_val(a, b): return a if a > b else b",
            "eval_method": "llm_judge",
            "eval_params": {"criteria": "功能正确 + 语法正确"},
        },
        {
            "id": "reason_001",
            "category": "逻辑推理",
            "difficulty": "hard",
            "input": "所有的鸟都会飞，企鹅是鸟，企鹅会飞吗？",
            "expected_output": "前提'所有的鸟都会飞'不成立，企鹅不会飞",
            "eval_method": "llm_judge",
            "eval_params": {"criteria": "识别前提错误 + 正确结论"},
        },
        {
            "id": "rag_001",
            "category": "RAG 检索",
            "difficulty": "medium",
            "input": "根据文档回答：LangGraph 的核心组件是什么？",
            "expected_output": "StateGraph、Node、Edge、State",
            "eval_method": "keyword_match",
            "eval_params": {"keywords": ["StateGraph", "Node", "Edge"]},
        },
    ],
}

# === 保存到文件 ===

def save_golden_set(filepath: str, dataset: dict):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Golden Set 已保存: {filepath} ({len(dataset['cases'])} 条)")

def load_golden_set(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

# === 通用评测器 ===

def evaluate(agent_fn, golden_set: dict) -> dict:
    """
    通用评测函数

    Args:
        agent_fn: 接收 input 返回 response 的函数
        golden_set: 评测数据集
    """
    results = []
    for case in golden_set["cases"]:
        response = agent_fn(case["input"])
        method = case["eval_method"]
        params = case["eval_params"]

        if method == "exact_match":
            passed = response.strip() == case["expected_output"].strip()
            score = 1.0 if passed else 0.0
        elif method == "keyword_match":
            keywords = params.get("keywords", [])
            matched = sum(1 for kw in keywords if kw.lower() in response.lower())
            score = matched / len(keywords) if keywords else 0
            passed = score >= 0.5
        elif method == "llm_judge":
            # 这里简化为关键词检查，实际应调用 llm_judge
            keywords = params.get("keywords", [])
            matched = sum(1 for kw in keywords if kw.lower() in response.lower())
            score = matched / len(keywords) if keywords else 0.5
            passed = score >= 0.5
        else:
            score = 0
            passed = False

        results.append({
            "id": case["id"],
            "category": case["category"],
            "difficulty": case["difficulty"],
            "passed": passed,
            "score": score,
            "response": response[:80],
        })

    # 汇总报告
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    avg_score = sum(r["score"] for r in results) / total if total else 0

    # 分类统计
    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0, "scores": []}
        by_category[cat]["total"] += 1
        by_category[cat]["passed"] += int(r["passed"])
        by_category[cat]["scores"].append(r["score"])

    print("=" * 50)
    print("评测报告")
    print("=" * 50)
    print(f"总通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"平均得分: {avg_score:.2f}")
    print()
    print("分类统计:")
    for cat, stats in by_category.items():
        cat_avg = sum(stats["scores"]) / stats["total"]
        print(f"  {cat}: {stats['passed']}/{stats['total']} ({stats['passed']/stats['total']*100:.1f}%) 平均分={cat_avg:.2f}")

    return {"total": total, "passed": passed, "avg_score": avg_score, "details": results}

# === 运行评测 ===

def simple_agent(query: str) -> str:
    """被测 Agent"""
    llm = make_llm(0)
    return llm.invoke([HumanMessage(content=query)]).content

save_golden_set("golden_set.json", GOLDEN_SET)
loaded = load_golden_set("golden_set.json")
evaluate(simple_agent, loaded)
```

### Day 1 小结

```
Day 1 核心概念：
┌──────────────────────────────────────────────────┐
│  Agent 评测三层体系                                │
│                                                    │
│  组件级 → 单个工具/Prompt 的单元测试               │
│  端到端 → 完整任务的 Golden Set 评测               │
│  在线级 → 线上 A/B 测试 + 实时监控                 │
│                                                    │
│  核心评测方法：                                     │
│  1. 关键词匹配（粗筛）                             │
│  2. LLM-as-Judge（质量评分 1-5）                   │
│  3. 轨迹评测（工具调用路径是否合理）               │
│  4. 精确匹配（数学/事实类问题）                    │
│                                                    │
│  评测数据集（Golden Set）结构：                    │
│  - id, category, difficulty                       │
│  - input, expected_output                         │
│  - eval_method, eval_params                       │
│                                                    │
│  关键原则：                                         │
│  - 评测集要覆盖多难度、多类别                      │
│  - 不同类别用不同评测方法                         │
│  - 评测结果要分类统计，发现短板                   │
└──────────────────────────────────────────────────┘
```

### Day 1 练习

1. 扩展 `EVAL_DATASET`，添加 5 个新的评测用例（至少覆盖 3 个新类别，如摘要、分类、推理）
2. 实现 `exact_match` 评测方法，支持忽略大小写和首尾空白的精确匹配
3. 为 `llm_judge` 添加多轮评分机制——运行 3 次取平均分，减少评分的随机性

<details>
<summary>参考答案</summary>

```python
"""Day 1 练习答案"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 练习 1：扩展评测数据集 ===

EXTENDED_DATASET = [
    # 原有用例
    {"id": "math_001", "category": "数学", "difficulty": "easy",
     "input": "计算 15 * 24 = ?", "expected_output": "360", "eval_method": "exact_match"},
    # 新增：摘要
    {"id": "summary_001", "category": "摘要", "difficulty": "medium",
     "input": "用一句话概括：Python 是一种解释型、面向对象、动态类型的高级编程语言，"
             "以简洁易读著称，广泛用于数据分析、Web开发、AI等领域。",
     "expected_output": "Python是简洁易读的高级编程语言",
     "eval_method": "llm_judge",
     "eval_params": {"criteria": "概括准确 + 一句话"}},
    # 新增：分类
    {"id": "classify_001", "category": "分类", "difficulty": "easy",
     "input": "以下情感是正面还是负面？'这家餐厅的服务太差了'", "expected_output": "负面",
     "eval_method": "keyword_match", "eval_params": {"keywords": ["负面"]}},
    # 新增：推理
    {"id": "reason_002", "category": "推理", "difficulty": "hard",
     "input": "如果 A > B, B > C, 那么 A 和 C 的关系？", "expected_output": "A > C",
     "eval_method": "keyword_match", "eval_params": {"keywords": ["A > C", "A>C"]}},
    # 新增：代码理解
    {"id": "code_002", "category": "代码理解", "difficulty": "medium",
     "input": "以下代码做什么？[x for x in range(10) if x % 2 == 0]",
     "expected_output": "生成 0-9 中的偶数列表",
     "eval_method": "llm_judge",
     "eval_params": {"criteria": "理解正确 + 提到偶数/列表"}},
]

# === 练习 2：exact_match 支持忽略大小写和空白 ===

def exact_match_eval(response: str, expected: str, ignore_case: bool = True, ignore_whitespace: bool = True) -> dict:
    """精确匹配评测，支持忽略大小写和首尾空白"""
    r = response
    e = expected
    if ignore_whitespace:
        r = r.strip()
        e = e.strip()
    if ignore_case:
        r = r.lower()
        e = e.lower()
    passed = r == e
    return {"passed": passed, "response": response[:60], "expected": expected[:60]}

# 测试
print("=== 练习 2: exact_match ===")
print(exact_match_eval("  360  ", "360"))
print(exact_match_eval("Hello", "hello"))
print(exact_match_eval("360", "361"))

# === 练习 3：多轮 LLM 评分 ===

JUDGE_PROMPT = """你是评分员。请对以下回答评分 1-5 分。

问题: {question}
回答: {answer}

用 JSON 输出: {{"score": <1-5>, "reason": "<理由>"}}
"""

def llm_judge_multi(question: str, answer: str, rounds: int = 3) -> dict:
    """多轮 LLM 评分取平均"""
    judge_llm = make_llm(0.3)  # 稍高温度增加多样性
    scores = []
    for i in range(rounds):
        resp = judge_llm.invoke([HumanMessage(content=JUDGE_PROMPT.format(question=question, answer=answer))])
        try:
            content = resp.content
            s, e = content.find("{"), content.rfind("}") + 1
            if s >= 0 and e > s:
                result = json.loads(content[s:e])
                scores.append(int(result.get("score", 0)))
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    if not scores:
        return {"score": 0, "reason": "所有评分轮次都解析失败"}

    avg_score = sum(scores) / len(scores)
    return {
        "score": round(avg_score, 2),
        "scores": scores,
        "reason": f"{len(scores)} 轮评分: {scores}, 平均: {avg_score:.2f}",
    }

print("\n=== 练习 3: 多轮评分 ===")
result = llm_judge_multi("解释什么是递归", "递归是函数调用自身解决子问题的方法，需要终止条件。")
print(f"评分: {result['score']}/5")
print(f"详情: {result['reason']}")
```

</details>

---

## Day 2：自动化测试框架

> 手动评测不可持续。我们需要可重复、可回归的自动化测试。

### 2.1 用 pytest 测试 Agent 组件

```python
"""
Agent 组件单元测试
文件: test_agent_components.py
运行: pytest test_agent_components.py -v
"""

import os
import sys
import pytest
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 被测组件 ===

def math_agent(query: str) -> str:
    """数学 Agent：处理数学问题"""
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(content=f"只回答数字结果，不要解释:\n{query}")])
    return resp.content.strip()

def translation_agent(text: str, target_lang: str = "中文") -> str:
    """翻译 Agent"""
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(content=f"将以下内容翻译为{target_lang}，只输出译文:\n{text}")])
    return resp.content.strip()

def summary_agent(text: str, max_words: int = 50) -> str:
    """摘要 Agent"""
    llm = make_llm(0.3)
    resp = llm.invoke([HumanMessage(
        content=f"用{max_words}字以内概括以下内容:\n{text}"
    )])
    return resp.content.strip()

# === 测试用例 ===

class TestMathAgent:
    """数学 Agent 测试"""

    def test_addition(self):
        result = math_agent("2+3=?")
        assert "5" in result

    def test_multiplication(self):
        result = math_agent("12*8=?")
        assert "96" in result

    def test_division(self):
        result = math_agent("100/4=?")
        assert "25" in result

    def test_negative_number(self):
        result = math_agent("-5+3=?")
        assert "-2" in result


class TestTranslationAgent:
    """翻译 Agent 测试"""

    def test_en_to_zh(self):
        result = translation_agent("Hello World", "中文")
        assert "你好" in result or "世界" in result

    def test_empty_input(self):
        """边界测试：空输入"""
        result = translation_agent("", "中文")
        assert isinstance(result, str)

    def test_long_text(self):
        """边界测试：长文本"""
        long_text = "This is a test. " * 50
        result = translation_agent(long_text, "中文")
        assert len(result) > 0


class TestSummaryAgent:
    """摘要 Agent 测试"""

    def test_basic_summary(self):
        text = "Python是一种解释型语言。它支持面向对象编程。Python有丰富的标准库。Python在数据科学领域很流行。"
        result = summary_agent(text, max_words=30)
        assert len(result) > 0
        assert len(result) < 200  # 摘要应比原文短

    def test_short_input(self):
        """短文本摘要"""
        result = summary_agent("Python很好用。", max_words=20)
        assert len(result) > 0

# === 运行 ===
# pytest test_agent_components.py -v --tb=short
```

### 2.2 Agent 集成测试

```python
"""
Agent 集成测试：测试完整的 Agent 流程
文件: test_agent_integration.py
"""

import os
import sys
import pytest
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 被测 Agent 管道 ===

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个{role}。请简洁回答。"),
    ("human", "{question}"),
])

def create_agent(role: str):
    """创建一个角色 Agent"""
    llm = make_llm(0)
    chain = prompt | llm
    def agent(question: str) -> str:
        resp = chain.invoke({"role": role, "question": question})
        return resp.content
    return agent

# === 集成测试 ===

class TestAgentPipeline:
    """Agent 管道集成测试"""

    @pytest.fixture
    def coder_agent(self):
        return create_agent("Python 编程专家")

    @pytest.fixture
    def teacher_agent(self):
        return create_agent("耐心的编程老师")

    def test_coder_generates_code(self, coder_agent):
        """Coder Agent 应该生成代码"""
        result = coder_agent("写一个冒泡排序函数")
        assert "def" in result
        assert "sort" in result.lower() or "bubble" in result.lower()

    def test_teacher_explains_concept(self, teacher_agent):
        """Teacher Agent 应该解释概念"""
        result = teacher_agent("什么是变量？")
        assert len(result) > 20
        # 应该提到"存储"或"数据"相关概念
        assert any(kw in result for kw in ["存储", "数据", "赋值", "值"])

    def test_agent_consistency(self, coder_agent):
        """Agent 一致性测试（同一问题多次调用）"""
        question = "2+2等于几？"
        results = [coder_agent(question) for _ in range(3)]
        # 所有结果都应该包含 "4"
        for r in results:
            assert "4" in r

    def test_different_roles_different_style(self, coder_agent, teacher_agent):
        """不同角色应有不同回答风格"""
        question = "解释什么是列表"
        coder_result = coder_agent(question)
        teacher_result = teacher_agent(question)
        # 两个回答不应完全相同
        assert coder_result != teacher_result


# === LangGraph Agent 集成测试 ===

from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END

class TestState(TypedDict):
    query: str
    route: str
    result: str

def build_test_agent():
    """构建测试用 LangGraph Agent"""
    def router(state: TestState) -> dict:
        query = state["query"].lower()
        if "代码" in query or "code" in query:
            return {"route": "coder"}
        return {"route": "responder"}

    def coder(state: TestState) -> dict:
        llm = make_llm(0)
        resp = llm.invoke([HumanMessage(content=f"写代码: {state['query']}")])
        return {"result": resp.content}

    def responder(state: TestState) -> dict:
        llm = make_llm(0)
        resp = llm.invoke([HumanMessage(content=state["query"])])
        return {"result": resp.content}

    def route_fn(state: TestState) -> str:
        return state.get("route", "responder")

    builder = StateGraph(TestState)
    builder.add_node("router", router)
    builder.add_node("coder", coder)
    builder.add_node("responder", responder)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", route_fn, {"coder": "coder", "responder": "responder"})
    builder.add_edge("coder", END)
    builder.add_edge("responder", END)
    return builder.compile()

class TestLangGraphAgent:

    @pytest.fixture
    def agent(self):
        return build_test_agent()

    def test_routes_to_coder(self, agent):
        """包含'代码'的路由到 coder"""
        result = agent.invoke({"query": "写一个代码：排序", "route": "", "result": ""})
        assert "route" in result or "result" in result
        assert len(result.get("result", "")) > 0

    def test_routes_to_responder(self, agent):
        """普通问题路由到 responder"""
        result = agent.invoke({"query": "你好", "route": "", "result": ""})
        assert len(result.get("result", "")) > 0

    def test_empty_query(self, agent):
        """空查询不应崩溃"""
        result = agent.invoke({"query": "", "route": "", "result": ""})
        assert "result" in result
```

### 2.3 回归测试与 CI/CD 集成

```python
"""
回归测试：确保修改不破坏已有功能
文件: test_regression.py
"""

import os
import json
import pytest
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 回归测试集 ===

REGRESSION_CASES = [
    {"id": "reg_001", "input": "1+1=?", "must_contain": ["2"]},
    {"id": "reg_002", "input": "Hello 翻译为中文", "must_contain": ["你好"]},
    {"id": "reg_003", "input": "list 是可变的吗？", "must_contain": ["是"]},
    {"id": "reg_004", "input": "写一个 def 函数", "must_contain": ["def"]},
]

@pytest.mark.parametrize("case", REGRESSION_CASES)
def test_regression(case):
    """回归测试：确保基本功能不被破坏"""
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(content=case["input"])])
    content = resp.content
    for keyword in case["must_contain"]:
        assert keyword in content, (
            f"[{case['id']}] 期望包含 '{keyword}'，实际: {content[:80]}"
        )

# === 性能回归测试 ===

import time

class TestPerformanceRegression:
    """性能回归：确保响应时间不退化"""

    def test_response_time_under_5s(self):
        """单次响应应在 5 秒内"""
        llm = make_llm(0)
        start = time.time()
        resp = llm.invoke([HumanMessage(content="1+1=?")])
        elapsed = time.time() - start
        assert elapsed < 5.0, f"响应时间 {elapsed:.2f}s 超过 5s 阈值"

    def test_batch_response_time(self):
        """5 次请求总时间应在 20 秒内"""
        llm = make_llm(0)
        start = time.time()
        for i in range(5):
            llm.invoke([HumanMessage(content=f"{i}+1=?")])
        elapsed = time.time() - start
        assert elapsed < 20.0, f"批量响应时间 {elapsed:.2f}s 超过 20s 阈值"
```

### 2.4 conftest.py 共享 fixture

```python
"""
共享测试配置
文件: conftest.py
"""

import os
import pytest
from langchain_openai import ChatOpenAI

@pytest.fixture
def llm():
    """共享 LLM 实例"""
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=0,
    )

@pytest.fixture(scope="session")
def golden_cases():
    """会话级共享评测集"""
    return [
        {"input": "1+1=?", "expected": "2"},
        {"input": "中国的首都", "expected": "北京"},
    ]

@pytest.fixture(autouse=True)
def check_api_key():
    """自动检查 API Key"""
    if not os.environ.get("ZHIPU_API_KEY"):
        pytest.skip("ZHIPU_API_KEY 未设置，跳过测试")
```

### Day 2 小结

```
Day 2 核心概念：
┌──────────────────────────────────────────────────┐
│  Agent 测试金字塔                                  │
│                                                    │
│  /  \         端到端测试（少量，慢，贵）            │
│  /    \       集成测试（适量，中速）                │
│  /______\     单元测试（大量，快，便宜）            │
│                                                    │
│  pytest 关键用法：                                  │
│  - class TestXxx: 组织相关测试                     │
│  - @pytest.fixture: 共享 setup 逻辑               │
│  - @pytest.mark.parametrize: 参数化测试            │
│  - conftest.py: 跨文件共享 fixture                │
│                                                    │
│  Agent 测试策略：                                   │
│  1. 单元测试：测组件（prompt、parser、tool）       │
│  2. 集成测试：测管道（prompt|llm|parser）         │
│  3. 回归测试：固定用例，防退化                      │
│  4. 性能测试：响应时间不退化                        │
│                                                    │
│  运行命令：                                         │
│  pytest -v                 # 详细输出              │
│  pytest -k "math"          # 只跑匹配的测试        │
│  pytest --tb=short         # 简短错误信息          │
│  pytest -x                 # 第一个失败就停止      │
└──────────────────────────────────────────────────┘
```

### Day 2 练习

1. 为 Day 1 的 `summary_agent` 编写至少 4 个单元测试（含正常输入、空输入、超长输入、语言检查）
2. 创建一个 `test_rag_agent.py`，测试一个简单的 RAG Agent（构建→检索→回答→验证回答包含文档内容）
3. 编写性能回归测试：测试同一 Agent 3 次调用的响应时间标准差小于 2 秒

<details>
<summary>参考答案</summary>

```python
"""Day 2 练习答案"""

import os
import sys
import time
import statistics
import pytest
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 练习 1：summary_agent 单元测试 ===

def summary_agent(text: str, max_words: int = 50) -> str:
    llm = make_llm(0.3)
    resp = llm.invoke([HumanMessage(content=f"用{max_words}字以内概括:\n{text}")])
    return resp.content.strip()

class TestSummaryAgent:

    def test_normal_input(self):
        """正常输入：应返回非空摘要"""
        text = "Python是解释型语言。它支持面向对象。Python有丰富标准库。"
        result = summary_agent(text, 30)
        assert len(result) > 0
        assert len(result) < len(text) * 2  # 摘要不应比原文长太多

    def test_empty_input(self):
        """空输入：不应崩溃"""
        result = summary_agent("", 30)
        assert isinstance(result, str)

    def test_long_input(self):
        """超长输入：应正常处理"""
        text = "人工智能是计算机科学的一个分支。 " * 100
        result = summary_agent(text, 50)
        assert len(result) > 0
        assert len(result) < 500  # 摘要应该比原文短

    def test_language_check(self):
        """语言检查：中文输入应返回中文摘要"""
        result = summary_agent("机器学习是人工智能的核心技术。", 20)
        # 应该包含中文字符
        has_chinese = any('\u4e00' <= ch <= '\u9fff' for ch in result)
        assert has_chinese, f"摘要中无中文字符: {result}"

# === 练习 2：RAG Agent 测试 ===

class TestRAGAgent:
    """RAG Agent 测试"""

    @pytest.fixture
    def rag_agent(self):
        """构建简单 RAG Agent"""
        documents = [
            "LangChain 是一个用于开发 LLM 应用的框架。",
            "LangGraph 是 LangChain 的图编排工具。",
            "Chroma 是一个向量数据库。",
        ]

        def agent(query: str) -> str:
            llm = make_llm(0)
            # 简单关键词检索
            relevant = [d for d in documents if any(w in query for w in d.split()[:3])]
            if not relevant:
                relevant = documents
            context = "\n".join(relevant)
            resp = llm.invoke([HumanMessage(
                content=f"根据以下文档回答:\n{context}\n\n问题: {query}"
            )])
            return resp.content

        return agent

    def test_retrieves_correct_doc(self, rag_agent):
        """应检索到相关文档"""
        result = rag_agent("LangChain 是什么？")
        assert "框架" in result

    def test_answer_from_context(self, rag_agent):
        """回答应基于文档内容"""
        result = rag_agent("Chroma 是什么？")
        assert "向量" in result or "数据库" in result

    def test_empty_query(self, rag_agent):
        """空查询不崩溃"""
        result = rag_agent("")
        assert isinstance(result, str)

# === 练习 3：性能标准差测试 ===

class TestPerformanceConsistency:

    def test_response_time_stddev(self):
        """3 次调用响应时间标准差 < 2 秒"""
        llm = make_llm(0)
        times = []
        for _ in range(3):
            start = time.time()
            llm.invoke([HumanMessage(content="1+1=?")])
            times.append(time.time() - start)

        stddev = statistics.stdev(times)
        print(f"响应时间: {[f'{t:.2f}s' for t in times]}")
        print(f"标准差: {stddev:.2f}s")
        assert stddev < 2.0, f"响应时间标准差 {stddev:.2f}s 过大"
```

</details>

---

## Day 3：性能优化与成本控制

> Agent 的两大生产问题：太慢和太贵。今天解决这两个问题。

### 3.1 延迟分析

```python
"""Agent 延迟分析与优化"""

import os
import time
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 延迟测量工具 ===

class LatencyTracker:
    """追踪 Agent 各阶段耗时"""

    def __init__(self):
        self.stages = []

    def record(self, name: str, duration: float):
        self.stages.append({"stage": name, "duration": duration})

    def report(self) -> str:
        total = sum(s["duration"] for s in self.stages)
        lines = [f"总耗时: {total:.3f}s\n"]
        for s in self.stages:
            pct = s["duration"] / total * 100 if total > 0 else 0
            lines.append(f"  {s['stage']}: {s['duration']:.3f}s ({pct:.0f}%)")
        return "\n".join(lines)

# === 同步 vs 异步 vs 批量 ===

def test_sync_latency():
    """同步调用：串行执行"""
    llm = make_llm(0)
    tracker = LatencyTracker()

    start = time.time()
    r1 = llm.invoke([HumanMessage(content="1+1=?")])
    tracker.record("call_1", time.time() - start)

    start = time.time()
    r2 = llm.invoke([HumanMessage(content="2+2=?")])
    tracker.record("call_2", time.time() - start)

    start = time.time()
    r3 = llm.invoke([HumanMessage(content="3+3=?")])
    tracker.record("call_3", time.time() - start)

    print("=== 同步调用（串行）===")
    print(tracker.report())

async def test_async_latency():
    """异步调用：并行执行"""
    llm = make_llm(0)

    start = time.time()
    # 三个调用同时发出
    results = await asyncio.gather(
        llm.ainvoke([HumanMessage(content="1+1=?")]),
        llm.ainvoke([HumanMessage(content="2+2=?")]),
        llm.ainvoke([HumanMessage(content="3+3=?")]),
    )
    total = time.time() - start

    print(f"\n=== 异步调用（并行）===")
    print(f"3 个请求总耗时: {total:.3f}s")
    for i, r in enumerate(results, 1):
        print(f"  结果 {i}: {r.content.strip()}")

def test_batch_latency():
    """批量调用"""
    llm = make_llm(0)
    inputs = [
        [HumanMessage(content="1+1=?")],
        [HumanMessage(content="2+2=?")],
        [HumanMessage(content="3+3=?")],
    ]

    start = time.time()
    results = llm.batch(inputs)
    total = time.time() - start

    print(f"\n=== 批量调用 ===")
    print(f"3 个请求总耗时: {total:.3f}s")
    for i, r in enumerate(results, 1):
        print(f"  结果 {i}: {r.content.strip()}")

# 运行
test_sync_latency()
asyncio.run(test_async_latency())
test_batch_latency()
```

### 3.2 缓存策略

```python
"""LLM 响应缓存：避免重复调用"""

import os
import time
import hashlib
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 内存缓存 ===

class LLMCache:
    """简单的 LLM 响应缓存"""

    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def _key(self, prompt: str, model: str) -> str:
        return hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str = "glm-4-flash") -> str | None:
        key = self._key(prompt, model)
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None

    def set(self, prompt: str, response: str, model: str = "glm-4-flash"):
        key = self._key(prompt, model)
        self.cache[key] = response

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "cache_size": len(self.cache),
        }

# === 带缓存的 Agent ===

class CachedAgent:
    """带缓存的 Agent"""

    def __init__(self):
        self.llm = make_llm(0)
        self.cache = LLMCache()

    def invoke(self, prompt: str) -> str:
        # 先查缓存
        cached = self.cache.get(prompt)
        if cached is not None:
            return cached + " [cached]"

        # 未命中：调用 LLM
        resp = self.llm.invoke([HumanMessage(content=prompt)])
        result = resp.content
        self.cache.set(prompt, result)
        return result

# === 测试缓存效果 ===

agent = CachedAgent()
questions = [
    "什么是 Python？",
    "什么是 Python？",   # 重复
    "什么是 Python？",   # 重复
    "什么是 Java？",
    "什么是 Python？",   # 重复
]

for q in questions:
    start = time.time()
    result = agent.invoke(q)
    elapsed = time.time() - start
    print(f"Q: {q} | 耗时: {elapsed:.3f}s | {result[:30]}...")

print(f"\n缓存统计: {agent.cache.stats()}")
```

### 3.3 成本估算与控制

```python
"""API 成本估算与控制"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === Token 计数与成本估算 ===

# 智谱 GLM 定价（示例，实际请查阅官方定价）
PRICING = {
    "glm-4-flash": {"input": 0.0001, "output": 0.0001},   # 元/千token
    "glm-4-plus": {"input": 0.05, "output": 0.05},
    "glm-4": {"input": 0.1, "output": 0.1},
}

class CostTracker:
    """API 成本追踪器"""

    def __init__(self, model: str = "glm-4-flash"):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0

    def record(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.call_count += 1

    def estimate_cost(self) -> dict:
        pricing = PRICING.get(self.model, {"input": 0, "output": 0})
        input_cost = self.total_input_tokens / 1000 * pricing["input"]
        output_cost = self.total_output_tokens / 1000 * pricing["output"]
        return {
            "model": self.model,
            "calls": self.call_count,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "input_cost": round(input_cost, 4),
            "output_cost": round(output_cost, 4),
            "total_cost": round(input_cost + output_cost, 4),
        }

# === 带成本追踪的 Agent ===

class CostAwareAgent:
    """带成本追踪的 Agent"""

    def __init__(self, model: str = "glm-4-flash", budget: float = 1.0):
        self.llm = make_llm(0)
        self.tracker = CostTracker(model)
        self.budget = budget  # 预算上限（元）

    def invoke(self, prompt: str) -> str:
        # 检查预算
        cost = self.tracker.estimate_cost()
        if cost["total_cost"] >= self.budget:
            return f"[预算已用尽] 已花费 {cost['total_cost']} 元"

        resp = self.llm.invoke([HumanMessage(content=prompt)])

        # 记录 token 使用量
        input_tokens = resp.usage_metadata.get("input_tokens", 0) if resp.usage_metadata else 0
        output_tokens = resp.usage_metadata.get("output_tokens", 0) if resp.usage_metadata else 0
        self.tracker.record(input_tokens, output_tokens)

        return resp.content

    def report(self) -> dict:
        return self.tracker.estimate_cost()

# === 测试 ===

agent = CostAwareAgent(model="glm-4-flash", budget=0.5)
questions = [
    "什么是人工智能？",
    "用 Python 写一个 hello world",
    "解释什么是 REST API",
    "翻译：Hello World",
]

for q in questions:
    result = agent.invoke(q)
    print(f"Q: {q}")
    print(f"A: {result[:50]}...\n")

print("=== 成本报告 ===")
report = agent.report()
for k, v in report.items():
    print(f"  {k}: {v}")
```

### 3.4 模型选择策略

```python
"""模型选择策略：简单问题用便宜模型，复杂问题用贵模型"""

import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(model="glm-4-flash", temp=0):
    return ChatOpenAI(
        model=model,
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 任务复杂度路由 ===

def classify_complexity(query: str) -> str:
    """用便宜模型判断任务复杂度"""
    cheap_llm = make_llm("glm-4-flash", 0)
    resp = cheap_llm.invoke([HumanMessage(
        content=f"判断以下任务的复杂度，只回答一个词（simple/medium/complex）:\n{query}"
    )])
    result = resp.content.strip().lower()
    for level in ["simple", "medium", "complex"]:
        if level in result:
            return level
    return "medium"

# === 分级模型 Agent ===

MODEL_MAP = {
    "simple": "glm-4-flash",    # 最便宜
    "medium": "glm-4-flash",     # 中等
    "complex": "glm-4-plus",     # 最强（如果可用）
}

class TieredAgent:
    """分级 Agent：根据复杂度选择模型"""

    def __init__(self):
        self.model_calls = {"simple": 0, "medium": 0, "complex": 0}

    def invoke(self, query: str) -> str:
        # 先判断复杂度
        complexity = classify_complexity(query)
        model = MODEL_MAP.get(complexity, "glm-4-flash")
        self.model_calls[complexity] += 1

        llm = make_llm(model, 0)
        resp = llm.invoke([HumanMessage(content=query)])
        return f"[{complexity}/{model}] {resp.content}"

    def stats(self):
        return self.model_calls

# === 测试 ===

agent = TieredAgent()
queries = [
    "1+1=?",                           # simple
    "解释什么是递归",                    # medium
    "设计一个分布式缓存系统的架构",       # complex
    "翻译：Hello",                      # simple
]

for q in queries:
    result = agent.invoke(q)
    print(f"Q: {q}")
    print(f"A: {result[:60]}...\n")

print(f"模型调用统计: {agent.stats()}")
```

### Day 3 小结

```
Day 3 核心概念：
┌──────────────────────────────────────────────────┐
│  性能优化三板斧                                     │
│                                                    │
│  1. 异步并行（asyncio.gather）                     │
│     - 串行 3 请求 → 总时间 = 3 × 单次              │
│     - 并行 3 请求 → 总时间 ≈ 1 × 单次             │
│                                                    │
│  2. 缓存（Cache）                                   │
│     - 相同 prompt 不重复调用                       │
│     - 命中率 = hits / (hits + misses)              │
│     - 适合：FAQ、固定模板、重复查询                 │
│                                                    │
│  3. 模型分级（Tiered）                              │
│     - 简单任务 → glm-4-flash（便宜快）             │
│     - 复杂任务 → glm-4-plus（强但贵）              │
│     - 用便宜模型做路由判断                         │
│                                                    │
│  成本控制：                                         │
│  - CostTracker 追踪 token 使用量                   │
│  - 设置预算上限，超限拒绝调用                      │
│  - 定价 = 输入token × 输入单价 + 输出token × 输出单价│
│                                                    │
│  延迟分析：                                         │
│  - LatencyTracker 分阶段计时                       │
│  - 找到瓶颈：是 LLM 调用还是工具执行？             │
└──────────────────────────────────────────────────┘
```

### Day 3 练习

1. 实现一个带 TTL（过期时间）的缓存——缓存项 10 分钟后自动失效
2. 对比同步 5 次调用 vs 异步 5 次调用的总耗时，计算加速比
3. 实现 `BudgetAgent`——设置月度预算（如 10 元），每次调用扣减余额，余额不足时降级到更便宜的模型

<details>
<summary>参考答案</summary>

```python
"""Day 3 练习答案"""

import os
import time
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def make_llm(model="glm-4-flash", temp=0):
    return ChatOpenAI(
        model=model,
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 练习 1：TTL 缓存 ===

class TTLCache:
    """带过期时间的缓存"""

    def __init__(self, ttl_seconds: int = 600):
        self.ttl = ttl_seconds
        self.cache = {}  # key -> (value, timestamp)
        self.hits = 0
        self.misses = 0

    def get(self, key: str):
        if key in self.cache:
            value, ts = self.cache[key]
            if time.time() - ts < self.ttl:
                self.hits += 1
                return value
            else:
                del self.cache[key]  # 过期删除
        self.misses += 1
        return None

    def set(self, key: str, value: str):
        self.cache[key] = (value, time.time())

    def stats(self):
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": self.hits / total if total else 0}

print("=== 练习 1: TTL 缓存 ===")
cache = TTLCache(ttl_seconds=2)  # 2 秒过期
cache.set("key1", "value1")
print(f"立即查: {cache.get('key1')}")  # hit
time.sleep(3)
print(f"3秒后查: {cache.get('key1')}")  # miss（已过期）
print(f"统计: {cache.stats()}")

# === 练习 2：同步 vs 异步对比 ===

async def compare_sync_async():
    queries = ["1+1=?", "2+2=?", "3+3=?", "4+4=?", "5+5=?"]

    # 同步
    llm = make_llm(0)
    start = time.time()
    for q in queries:
        llm.invoke([HumanMessage(content=q)])
    sync_time = time.time() - start

    # 异步
    start = time.time()
    await asyncio.gather(*[
        llm.ainvoke([HumanMessage(content=q)]) for q in queries
    ])
    async_time = time.time() - start

    speedup = sync_time / async_time if async_time > 0 else 0
    print(f"\n=== 练习 2: 同步 vs 异步 ===")
    print(f"同步 5 次: {sync_time:.2f}s")
    print(f"异步 5 次: {async_time:.2f}s")
    print(f"加速比: {speedup:.1f}x")

asyncio.run(compare_sync_async())

# === 练习 3：BudgetAgent ===

PRICING = {
    "glm-4-flash": {"input": 0.0001, "output": 0.0001},
    "glm-4-plus": {"input": 0.05, "output": 0.05},
}

class BudgetAgent:
    """月度预算 Agent"""

    def __init__(self, monthly_budget: float = 10.0):
        self.budget = monthly_budget
        self.spent = 0.0
        self.llm = make_llm("glm-4-flash", 0)

    def invoke(self, prompt: str) -> str:
        # 检查预算
        if self.spent >= self.budget:
            # 降级：使用更简单的方式
            return "[预算不足，降级处理] 请稍后重试或简化问题。"

        # 选择模型：剩余预算多就用贵的，少就用便宜的
        remaining = self.budget - self.spent
        model = "glm-4-plus" if remaining > self.budget * 0.5 else "glm-4-flash"
        llm = make_llm(model, 0)

        resp = llm.invoke([HumanMessage(content=prompt)])

        # 估算花费（简化）
        usage = resp.usage_metadata or {}
        input_tk = usage.get("input_tokens", 0)
        output_tk = usage.get("output_tokens", 0)
        pricing = PRICING.get(model, {"input": 0, "output": 0})
        cost = (input_tk / 1000 * pricing["input"]) + (output_tk / 1000 * pricing["output"])
        self.spent += cost

        return f"[{model}] 花费 {cost:.4f}元, 余额 {self.budget - self.spent:.4f}元\n{resp.content[:50]}"

print("\n=== 练习 3: BudgetAgent ===")
agent = BudgetAgent(monthly_budget=0.01)  # 很小的预算用于测试
for q in ["1+1=?", "2+2=?", "3+3=?", "4+4=?"]:
    result = agent.invoke(q)
    print(f"Q: {q}")
    print(f"A: {result}\n")
```

</details>

---

## Day 4：生产环境部署——FastAPI

> 从本地脚本到线上服务，FastAPI 是 Python Agent 的首选部署方案。

### 4.1 FastAPI 基础

```python
"""
Agent API 服务
文件: app.py
运行: uvicorn app:app --reload --port 8000
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

app = FastAPI(title="Agent API", version="1.0.0")

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === 请求/响应模型 ===

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    temperature: float = 0.0

class ChatResponse(BaseModel):
    """聊天响应"""
    response: str
    model: str
    tokens_used: int

# === 接口 ===

@app.get("/")
async def root():
    return {"status": "ok", "service": "Agent API"}

@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """聊天接口"""
    if not req.message:
        raise HTTPException(status_code=400, detail="message 不能为空")

    try:
        llm = make_llm(req.temperature)
        resp = llm.invoke([HumanMessage(content=req.message)])
        tokens = 0
        if resp.usage_metadata:
            tokens = resp.usage_metadata.get("total_tokens", 0)
        return ChatResponse(
            response=resp.content,
            model="glm-4-flash",
            tokens_used=tokens,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === 启动 ===
# uvicorn app:app --reload --port 8000
# 访问 http://localhost:8000/docs 查看 API 文档
```

### 4.2 流式响应

```python
"""
流式 API：逐 token 返回，前端可以实时显示
"""

import os
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

app = FastAPI(title="Streaming Agent API")

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
        streaming=True,
    )

class StreamRequest(BaseModel):
    message: str

async def generate_stream(message: str):
    """生成流式响应"""
    llm = make_llm(0)
    async for chunk in llm.astream([HumanMessage(content=message)]):
        if chunk.content:
            # SSE 格式：data: 内容\n\n
            yield f"data: {chunk.content}\n\n"
    yield "data: [DONE]\n\n"

@app.post("/chat/stream")
async def chat_stream(req: StreamRequest):
    """流式聊天接口（SSE）"""
    return StreamingResponse(
        generate_stream(req.message),
        media_type="text/event-stream",
    )

# === 测试 ===
# curl -N -X POST http://localhost:8000/chat/stream \
#   -H "Content-Type: application/json" \
#   -d '{"message": "写一首关于秋天的诗"}'
```

### 4.3 Agent 服务化

```python
"""
完整的 Agent 服务：集成 LangGraph + FastAPI
文件: agent_service.py
运行: uvicorn agent_service:app --reload --port 8000
"""

import os
from typing import TypedDict, Annotated
from operator import add
from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

app = FastAPI(title="Agent Service")

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === Agent 定义 ===

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    query: str
    route: str
    result: str

def router(state: AgentState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(
        content=f"判断任务类型，只回答一个词: code（编程）/ chat（聊天）\n任务: {state['query']}"
    )])
    route = "coder" if "code" in resp.content.lower() else "chat"
    return {"route": route}

def coder(state: AgentState) -> dict:
    llm = make_llm(0.2)
    resp = llm.invoke([HumanMessage(content=f"你是编程专家。{state['query']}")])
    return {"result": resp.content, "messages": [AIMessage(content=resp.content)]}

def chat(state: AgentState) -> dict:
    llm = make_llm(0.7)
    resp = llm.invoke([HumanMessage(content=state["query"])])
    return {"result": resp.content, "messages": [AIMessage(content=resp.content)]}

def route_fn(state: AgentState) -> str:
    return state.get("route", "chat")

# 构建图
builder = StateGraph(AgentState)
builder.add_node("router", router)
builder.add_node("coder", coder)
builder.add_node("chat", chat)
builder.add_edge(START, "router")
builder.add_conditional_edges("router", route_fn, {"coder": "coder", "chat": "chat"})
builder.add_edge("coder", END)
builder.add_edge("chat", END)
agent = builder.compile()

# === API 接口 ===

class AgentRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    route: str
    result: str

@app.post("/agent", response_model=AgentResponse)
async def run_agent(req: AgentRequest):
    result = agent.invoke({
        "messages": [HumanMessage(content=req.query)],
        "query": req.query,
        "route": "",
        "result": "",
    })
    return AgentResponse(
        route=result.get("route", ""),
        result=result.get("result", ""),
    )

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### 4.4 中间件与错误处理

```python
"""
API 中间件：日志、限流、CORS
"""

import os
import time
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_api")

app = FastAPI(title="Agent API with Middleware")

# === CORS 中间件 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 生产环境应限制域名
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# === 日志中间件 ===
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录每个请求的耗时和路径"""
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration:.3f}s)")
    return response

# === 简单限流 ===
from collections import defaultdict

class RateLimiter:
    """简单的内存限流器"""

    def __init__(self, max_requests: int = 10, window: int = 60):
        self.max_requests = max_requests
        self.window = window  # 秒
        self.requests = defaultdict(list)

    def check(self, client_id: str) -> bool:
        now = time.time()
        # 清理过期记录
        self.requests[client_id] = [
            t for t in self.requests[client_id] if now - t < self.window
        ]
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter(max_requests=10, window=60)

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """限流中间件"""
    client_id = request.client.host if request.client else "unknown"
    if not rate_limiter.check(client_id):
        raise HTTPException(status_code=429, detail="请求过于频繁，请稍后再试")
    return await call_next(request)

# === 全局异常处理 ===
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})

# === 接口 ===
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    return {"response": f"Echo: {req.message}"}

@app.get("/health")
async def health():
    return {"status": "ok"}
```

### Day 4 小结

```
Day 4 核心概念：
┌──────────────────────────────────────────────────┐
│  FastAPI Agent 部署                                │
│                                                    │
│  基础结构：                                         │
│  1. Pydantic 模型定义请求/响应                     │
│  2. @app.post/@app.get 定义路由                    │
│  3. /health 端点供健康检查                         │
│  4. /docs 自动生成 API 文档                        │
│                                                    │
│  流式响应（SSE）：                                  │
│  - StreamingResponse + text/event-stream           │
│  - async for chunk in llm.astream()               │
│  - data: [DONE]\n\n 标记结束                      │
│                                                    │
│  Agent 服务化：                                     │
│  - LangGraph 编译后的 graph 作为全局单例           │
│  - POST /agent 接收查询，返回路由+结果             │
│                                                    │
│  生产中间件：                                       │
│  - CORS：跨域支持                                  │
│  - 日志：记录请求耗时和路径                        │
│  - 限流：RateLimiter 防止滥用                      │
│  - 异常处理：全局兜底，不暴露堆栈                  │
│                                                    │
│  启动命令：                                         │
│  uvicorn app:app --host 0.0.0.0 --port 8000       │
└──────────────────────────────────────────────────┘
```

### Day 4 练习

1. 为 Agent API 添加 `/agent/batch` 端点，支持批量查询（接收 queries 列表，并行执行，返回 results 列表）
2. 添加 API Key 认证中间件——请求头中必须包含 `X-API-Key`，否则返回 401
3. 实现 `/agent/history/{thread_id}` 端点，配合 LangGraph Checkpointer 返回对话历史

<details>
<summary>参考答案</summary>

```python
"""Day 4 练习答案：增强 Agent API"""

import os
import asyncio
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

app = FastAPI(title="Enhanced Agent API")

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

# === Agent 定义 ===

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    query: str
    result: str

def agent_node(state: AgentState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(content=state["query"])])
    return {"result": resp.content, "messages": [AIMessage(content=resp.content)]}

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)
agent_graph = builder.compile(checkpointer=MemorySaver())

# === 练习 1：批量查询 ===

class BatchRequest(BaseModel):
    queries: list[str]

class BatchResponse(BaseModel):
    results: list[str]

@app.post("/agent/batch", response_model=BatchResponse)
async def batch_agent(req: BatchRequest):
    """批量查询：并行执行"""
    if not req.queries:
        raise HTTPException(status_code=400, detail="queries 不能为空")
    if len(req.queries) > 10:
        raise HTTPException(status_code=400, detail="单次最多 10 个查询")

    async def run_single(q: str, idx: int) -> str:
        config = {"configurable": {"thread_id": f"batch_{idx}"}}
        result = await agent_graph.ainvoke(
            {"messages": [HumanMessage(content=q)], "query": q, "result": ""},
            config,
        )
        return result.get("result", "")

    results = await asyncio.gather(*[
        run_single(q, i) for i, q in enumerate(req.queries)
    ])
    return BatchResponse(results=results)

# === 练习 2：API Key 认证 ===

VALID_API_KEYS = {"test-key-001", "test-key-002"}

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """API Key 认证中间件"""
    # 健康检查不需要认证
    if request.url.path in ["/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key")
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="无效或缺失的 API Key")
    return await call_next(request)

# === 练习 3：对话历史 ===

@app.get("/agent/history/{thread_id}")
async def get_history(thread_id: str):
    """获取对话历史"""
    config = {"configurable": {"thread_id": thread_id}}
    state = agent_graph.get_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="未找到对话历史")

    messages = state.values.get("messages", [])
    history = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        history.append({"role": role, "content": msg.content})

    return {"thread_id": thread_id, "messages": history}

# === 基础接口 ===

class AgentRequest(BaseModel):
    query: str
    thread_id: str = "default"

@app.post("/agent")
async def run_agent(req: AgentRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    result = await agent_graph.ainvoke(
        {"messages": [HumanMessage(content=req.query)], "query": req.query, "result": ""},
        config,
    )
    return {"result": result.get("result", "")}

@app.get("/health")
async def health():
    return {"status": "ok"}

# === 测试 ===
# 启动: uvicorn answer:app --reload --port 8000
# 测试批量: curl -X POST http://localhost:8000/agent/batch \
#   -H "X-API-Key: test-key-001" -H "Content-Type: application/json" \
#   -d '{"queries": ["1+1=?", "2+2=?"]}'
# 测试历史: curl http://localhost:8000/agent/history/default \
#   -H "X-API-Key: test-key-001"
```

</details>

---

## Day 5：Docker 容器化部署

> Docker 让 Agent 应用"一次构建，到处运行"。

### 5.1 Dockerfile

```dockerfile
# file: Dockerfile
FROM python:3.11-slim

# 工作目录
WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

# 先复制依赖文件（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 requirements.txt 与 .dockerignore

```text
# file: requirements.txt
langchain>=0.3.0
langchain-core>=0.3.0
langchain-openai>=0.2.0
langgraph>=0.2.0
fastapi>=0.115.0
uvicorn>=0.30.0
pydantic>=2.0.0
httpx>=0.27.0
```

```text
# file: .dockerignore
__pycache__
*.pyc
venv/
.venv/
.git/
*.md
.env
golden_set.json
test_*.py
conftest.py
```

### 5.3 Docker Compose

```yaml
# file: docker-compose.yml
version: "3.8"

services:
  agent-api:
    build: .
    container_name: agent-api
    ports:
      - "8000:8000"
    environment:
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
      - PYTHONUNBUFFERED=1
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"

  # 可选：Redis 缓存
  redis:
    image: redis:7-alpine
    container_name: agent-redis
    ports:
      - "6379:6379"
    restart: unless-stopped

  # 可选：Nginx 反向代理
  nginx:
    image: nginx:alpine
    container_name: agent-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - agent-api
    restart: unless-stopped
```

### 5.4 Nginx 反向代理配置

```nginx
# file: nginx.conf
upstream agent_api {
    server agent-api:8000;
}

server {
    listen 80;
    server_name localhost;

    # API 路由
    location / {
        proxy_pass http://agent_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # SSE 流式响应（不缓冲）
    location /chat/stream {
        proxy_pass http://agent_api;
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection "";
        proxy_http_version 1.1;
        chunked_transfer_encoding on;
    }

    # 健康检查
    location /health {
        proxy_pass http://agent_api;
        access_log off;
    }
}
```

### 5.5 .env 与环境管理

```bash
# file: .env
ZHIPU_API_KEY=your_api_key_here
MODEL_NAME=glm-4-flash
TEMPERATURE=0
MAX_TOKENS=2000

# 速率限制
RATE_LIMIT_MAX=10
RATE_LIMIT_WINDOW=60

# 日志
LOG_LEVEL=INFO
```

### 5.6 Docker 构建与运行

```bash
# === 构建镜像 ===
docker build -t agent-api:1.0 .

# === 运行容器 ===
docker run -d \
  --name agent-api \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  agent-api:1.0

# === 查看日志 ===
docker logs -f agent-api

# === 进入容器调试 ===
docker exec -it agent-api bash

# === Docker Compose 一键启动 ===
docker compose up -d

# === 查看服务状态 ===
docker compose ps

# === 停止所有服务 ===
docker compose down

# === 重新构建并启动 ===
docker compose up -d --build
```

### 5.7 Python 健康检查脚本

```python
"""
部署后验证脚本
文件: deploy_check.py
"""

import httpx
import time
import sys

BASE_URL = "http://localhost:8000"

def check_health() -> bool:
    """健康检查"""
    try:
        resp = httpx.get(f"{BASE_URL}/health", timeout=5)
        return resp.status_code == 200
    except Exception as e:
        print(f"健康检查失败: {e}")
        return False

def check_chat() -> bool:
    """聊天接口检查"""
    try:
        resp = httpx.post(
            f"{BASE_URL}/chat",
            json={"message": "1+1=?", "temperature": 0},
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            print(f"  聊天响应: {data.get('response', '')[:50]}...")
            return True
        return False
    except Exception as e:
        print(f"聊天接口失败: {e}")
        return False

def check_docs() -> bool:
    """API 文档检查"""
    try:
        resp = httpx.get(f"{BASE_URL}/docs", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

def main():
    print("=== 部署验证 ===")

    checks = [
        ("健康检查", check_health),
        ("聊天接口", check_chat),
        ("API 文档", check_docs),
    ]

    all_passed = True
    for name, check_fn in checks:
        print(f"\n[{name}]", end=" ")
        passed = check_fn()
        status = "PASS" if passed else "FAIL"
        print(status)
        if not passed:
            all_passed = False

    print(f"\n{'='*30}")
    if all_passed:
        print("所有检查通过！")
        sys.exit(0)
    else:
        print("有检查未通过，请排查！")
        sys.exit(1)

if __name__ == "__main__":
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(3)
    main()
```

### Day 5 小结

```
Day 5 核心概念：
┌──────────────────────────────────────────────────┐
│  Docker 部署流程                                    │
│                                                    │
│  1. Dockerfile                                     │
│     - python:3.11-slim 基础镜像                    │
│     - 先 COPY requirements.txt 再 pip install     │
│       （利用层缓存，代码变更不重装依赖）           │
│     - HEALTHCHECK 定期健康检查                     │
│                                                    │
│  2. .dockerignore                                  │
│     - 排除 __pycache__, venv, .git, .env          │
│     - 减小镜像体积，避免敏感信息泄露               │
│                                                    │
│  3. Docker Compose                                 │
│     - 一键启动多个服务                             │
│     - 资源限制：memory + cpus                     │
│     - 依赖管理：depends_on                        │
│     - 重启策略：unless-stopped                    │
│                                                    │
│  4. Nginx 反向代理                                 │
│     - 负载均衡（可扩展多实例）                     │
│     - SSE 流式响应：proxy_buffering off            │
│     - 隐藏内部端口                                 │
│                                                    │
│  5. 环境管理                                        │
│     - .env 文件管理密钥                            │
│     - --env-file 传入容器                         │
│     - 敏感信息不进镜像                             │
│                                                    │
│  常用命令：                                         │
│  docker build / docker run / docker compose up    │
│  docker logs -f / docker exec -it / docker ps     │
└──────────────────────────────────────────────────┘
```

### Day 5 练习

1. 为 Agent API 创建一个多阶段 Dockerfile——第一阶段安装依赖，第二阶段只复制 .py 文件和依赖，减小最终镜像体积
2. 在 docker-compose.yml 中添加 Prometheus + Grafana 监控服务
3. 编写 `stop_and_clean.sh` 脚本——停止所有容器、删除镜像、清理 volumes

<details>
<summary>参考答案</summary>

```dockerfile
# 练习 1：多阶段 Dockerfile
# file: Dockerfile.multistage

# === 阶段 1: 构建依赖 ===
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# === 阶段 2: 运行时 ===
FROM python:3.11-slim

WORKDIR /app

# 从 builder 阶段复制已安装的依赖
COPY --from=builder /install /usr/local

# 只复制应用代码
COPY app.py .
COPY requirements.txt .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# 练习 2：Docker Compose + 监控
# file: docker-compose.monitoring.yml
version: "3.8"

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ZHIPU_API_KEY=${ZHIPU_API_KEY}
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: agent-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: agent-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - prometheus
    restart: unless-stopped
```

```yaml
# file: prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "agent-api"
    static_configs:
      - targets: ["agent-api:8000"]
    metrics_path: /metrics
```

```bash
#!/bin/bash
# 练习 3：stop_and_clean.sh
# 停止所有容器、删除镜像、清理 volumes

echo "=== 停止所有容器 ==="
docker compose down --remove-orphans

echo "=== 删除 Agent 镜像 ==="
docker rmi -f agent-api:1.0 2>/dev/null || echo "镜像不存在或已删除"

echo "=== 清理悬空资源 ==="
docker system prune -f --volumes

echo "=== 清理完成 ==="
docker images
docker ps -a
```

</details>

---
