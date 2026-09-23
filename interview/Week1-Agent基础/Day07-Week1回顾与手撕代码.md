# Day 07 — Week 1 回顾与手撕代码特训

> **本周进度**: Day1 ✅ → Day2 ✅ → Day3 ✅ → Day4 ✅ → Day5 ✅ → Day6 ✅ → **Day7 回顾与手撕**

---

## 一、Week 1 知识图谱总览

```
                     Agent 核心能力栈
                          │
        ┌────────┬────────┼────────┬────────┐
        │        │        │        │        │
     基础概念  ReAct    工具调用   记忆系统  推理规划
     (Day1)  (Day2)   (Day3)    (Day5)   (Day6)
        │        │        │        │        │
     Agent     循环    Function   四层     CoT/ToT
     =Harness  Thought  Calling   记忆架构  Plan-Execute
     +Model    +Action  +MCP协议  向量DB   Reflexion
              +Observation         遗忘     多Agent
                                          协作
        │                 │
        └────────┬────────┘
                 │
              可靠性保障
         循环安全/防护栏/
         人机回环/沙箱
```

### 六天核心知识点串联

| Day | 主题 | 核心公式/概念 | 一句话 |
|-----|------|-------------|--------|
| 1 | Agent 基础 | Agent = Harness + Model + Loop | Agent 不是聊天机器人，是能自主行动的循环 |
| 2 | ReAct | Thought → Action → Observation 循环 | 推理与行动交错，边想边做 |
| 3 | Function Calling | LLM 输出结构化工具调用 JSON | 模型决定"调什么"，代码决定"怎么调" |
| 4 | MCP | M×N → M+N 的工具协议标准 | 统一工具接口，解耦 Agent 与工具 |
| 5 | 记忆系统 | Score = 0.45×sim + 0.20×recency + 0.20×imp + 0.15×freq | 四层记忆 + 多因子检索 + 遗忘 |
| 6 | 推理规划 | CoT(线性) → ToT(树) → GoT(图) → Reflexion(反思) | 根据复杂度选择推理策略 |

---

## 二、高频手撕代码题（6 道）

### 手撕题1: 实现一个完整的 Agent Loop（含循环安全网）

<details>
<summary>点击查看参考答案</summary>

```python
"""
最小可用 Agent Loop 实现
要求: 支持工具调用、循环安全网、token 预算、超时控制
"""

import json
import time
from typing import Callable

class AgentLoop:
    def __init__(
        self,
        llm_fn: Callable,          # LLM 调用函数
        tools: dict,                # {tool_name: callable}
        system_prompt: str,
        max_iterations: int = 20,   # 循环安全网
        max_tokens: int = 50000,    # Token 预算
        timeout_seconds: int = 120, # 超时
    ):
        self.llm_fn = llm_fn
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.max_tokens = max_tokens
        self.timeout = timeout_seconds

    def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input},
        ]

        tool_schemas = self._get_tool_schemas()
        total_tokens = 0
        start_time = time.time()

        for iteration in range(1, self.max_iterations + 1):
            # 超时检查
            if time.time() - start_time > self.timeout:
                return f"[超时] 已运行 {iteration} 轮"

            # Token 预算检查
            if total_tokens > self.max_tokens:
                return f"[Token 超限] 已用 {total_tokens}"

            # LLM 推理
            response = self.llm_fn(messages, tools=tool_schemas)
            total_tokens += response.get("usage", {}).get("total_tokens", 0)

            # 检查是否有工具调用
            if response.get("tool_calls"):
                for tool_call in response["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    arguments = json.loads(tool_call["function"]["arguments"])

                    # 安全检查
                    if tool_name not in self.tools:
                        result = f"[错误] 未知工具: {tool_name}"
                    else:
                        try:
                            result = self.tools[tool_name](**arguments)
                        except Exception as e:
                            result = f"[工具执行错误] {e}"

                    messages.append({
                        "role": "assistant",
                        "tool_calls": response["tool_calls"],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": str(result),
                    })
                continue  # 继续循环

            # 无工具调用 → 最终回答
            return response["content"]

        return f"[达到最大轮次 {self.max_iterations}] Agent 未完成"

    def _get_tool_schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": fn.__doc__ or "",
                    "parameters": {"type": "object", "properties": {}},
                }
            }
            for name, fn in self.tools.items()
        ]
```

**面试评分要点**：
- ✅ 有循环安全网（max_iterations）
- ✅ 有 token 预算
- ✅ 有超时控制
- ✅ 工具调用错误处理
- ✅ 未知工具防护

</details>

---

### 手撕题2: 实现 ReAct Agent（含死循环检测）

<details>
<summary>点击查看参考答案</summary>

```python
"""
ReAct Agent 实现
核心: Thought → Action → Observation 循环
附加: 死循环检测（连续重复动作检测）
"""

import re
import json
from collections import deque

class ReActAgent:
    def __init__(self, llm_fn, tools: dict, max_steps=15):
        self.llm_fn = llm_fn
        self.tools = tools
        self.max_steps = max_steps
        self.action_history = deque(maxlen=5)  # 用于死循环检测

    def run(self, task: str) -> str:
        prompt = self._build_initial_prompt(task)
        trajectory = []

        for step in range(self.max_steps):
            # LLM 生成 Thought + Action
            output = self.llm_fn(prompt)

            thought, action_name, action_input = self._parse(output)
            trajectory.append({"step": step, "thought": thought,
                              "action": action_name, "input": action_input})

            # 死循环检测：连续3次相同动作
            action_key = f"{action_name}:{action_input}"
            self.action_history.append(action_key)
            if self._is_looping():
                return self._handle_loop(trajectory)

            # 检查是否完成
            if action_name.lower() == "finish":
                return action_input

            # 执行工具
            if action_name not in self.tools:
                observation = f"[错误] 工具 {action_name} 不存在。可用: {list(self.tools.keys())}"
            else:
                try:
                    observation = self.tools[action_name](action_input)
                except Exception as e:
                    observation = f"[执行错误] {e}"

            trajectory[-1]["observation"] = observation

            # 追加到 prompt 继续
            prompt += f"\nThought: {thought}\nAction: {action_name}[{action_input}]\nObservation: {observation}\n"

        return f"[达到最大步数] 最后状态: {trajectory[-1]}"

    def _build_initial_prompt(self, task):
        tool_desc = "\n".join([f"- {name}: {fn.__doc__ or ''}" for name, fn in self.tools.items()])
        return f"""你是一个 ReAct Agent。使用 Thought/Action/Observation 格式解决问题。

可用工具:
{tool_desc}

格式:
Thought: [你的推理]
Action: [工具名][输入参数]

任务: {task}

Thought:"""

    def _parse(self, output: str):
        """解析 LLM 输出为 thought, action_name, action_input"""
        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|$)", output, re.DOTALL)
        action_match = re.search(r"Action:\s*(\w+)\[?(.+?)\]?$", output, re.MULTILINE)

        thought = thought_match.group(1).strip() if thought_match else ""
        action_name = action_match.group(1).strip() if action_match else "finish"
        action_input = action_match.group(2).strip() if action_match else ""

        return thought, action_name, action_input

    def _is_looping(self):
        """检测连续3次相同动作"""
        if len(self.action_history) < 3:
            return False
        last_three = list(self.action_history)[-3:]
        return last_three[0] == last_three[1] == last_three[2]

    def _handle_loop(self, trajectory):
        return f"[死循环检测] Agent 连续重复同一动作。轨迹: {trajectory[-3:]}"
```

</details>

---

### 手撕题3: 实现带优先级的并行工具调用

<details>
<summary>点击查看参考答案</summary>

```python
"""
并行工具调用 Agent
要求: 多工具并行执行、按优先级合并结果、超时控制
"""

import asyncio
import json
from typing import Any

class ParallelToolAgent:
    def __init__(self, llm_fn, tools: dict, tool_priorities: dict = None):
        self.llm_fn = llm_fn
        self.tools = tools
        self.tool_priorities = tool_priorities or {}

    async def run(self, query: str) -> str:
        # 1. LLM 决定调用哪些工具
        tool_calls = self._decide_tools(query)

        # 2. 并行执行所有工具
        results = await asyncio.gather(*[
            self._call_tool(tc) for tc in tool_calls
        ], return_exceptions=True)

        # 3. 按优先级合并结果
        merged = self._merge_results(tool_calls, results)

        # 4. LLM 综合结果生成最终回答
        return self._synthesize(query, merged)

    async def _call_tool(self, tool_call: dict) -> dict:
        """带超时的工具调用"""
        name = tool_call["name"]
        args = tool_call["arguments"]
        timeout = tool_call.get("timeout", 10)

        try:
            if asyncio.iscoroutinefunction(self.tools[name]):
                result = await asyncio.wait_for(
                    self.tools[name](**args), timeout=timeout
                )
            else:
                result = await asyncio.to_thread(self.tools[name], **args)
            return {"name": name, "success": True, "result": result}
        except asyncio.TimeoutError:
            return {"name": name, "success": False, "error": "timeout"}
        except Exception as e:
            return {"name": name, "success": False, "error": str(e)}

    def _merge_results(self, calls, results):
        """按工具优先级合并"""
        merged = []
        for call, result in zip(calls, results):
            priority = self.tool_priorities.get(call["name"], 5)
            merged.append({
                "tool": call["name"],
                "priority": priority,
                "data": result,
            })
        # 高优先级排前面
        merged.sort(key=lambda x: -x["priority"])
        return merged

    def _synthesize(self, query, merged):
        result_text = "\n".join([
            f"[{m['tool']}] (优先级:{m['priority']}) {m['data']}"
            for m in merged
        ])
        return self.llm_fn(f"问题: {query}\n工具结果:\n{result_text}\n综合回答:")

    def _decide_tools(self, query):
        """LLM 决定调用哪些工具（简化版）"""
        # 实际应通过 Function Calling 让 LLM 决定
        return [{"name": "search", "arguments": {"q": query}, "timeout": 5}]
```

</details>

---

### 手撕题4: 实现带摘要压缩的上下文管理器

<details>
<summary>点击查看参考答案</summary>

```python
"""
上下文管理器
当 token 超限时自动压缩旧消息为摘要
"""

import tiktoken

class ContextWindowManager:
    def __init__(self, llm_fn, max_tokens: int = 8000, keep_recent: int = 6):
        self.llm_fn = llm_fn
        self.max_tokens = max_tokens
        self.keep_recent = keep_recent
        self.running_summary = ""
        self.encoder = tiktoken.encoding_for_model("gpt-4")

    def count_tokens(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += len(self.encoder.encode(msg.get("content", "")))
            total += 4  # 消息开销
        return total

    def manage(self, messages: list[dict]) -> list[dict]:
        """管理上下文：超限时自动压缩"""
        while self.count_tokens(messages) > self.max_tokens and len(messages) > self.keep_recent:
            # 取出最旧的消息（保留 system 消息）
            system_msgs = [m for m in messages if m["role"] == "system"]
            non_system = [m for m in messages if m["role"] != "system"]

            if len(non_system) <= self.keep_recent:
                break

            # 取前2条压缩
            to_compress = non_system[:2]
            non_system = non_system[2:]

            # 生成摘要
            compress_text = "\n".join([f"{m['role']}: {m['content']}" for m in to_compress])
            self.running_summary = self.llm_fn(
                f"更新对话摘要:\n当前摘要: {self.running_summary}\n新增: {compress_text}\n新摘要:"
            )

            # 重组
            messages = system_msgs + [
                {"role": "system", "content": f"## 对话摘要\n{self.running_summary}"}
            ] + non_system

        return messages
```

</details>

---

### 手撕题5: 实现多因子记忆检索器

<details>
<summary>点击查看参考答案</summary>

```python
"""
记忆检索器
融合: 向量相似度 + 时间衰减 + 重要性 + 访问频率
"""

import math
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Memory:
    id: str
    content: str
    embedding: list
    importance: float       # 1-10
    timestamp: str          # ISO格式
    access_count: int

class MemoryRetriever:
    def __init__(self, embed_fn, half_life_days=30):
        self.embed_fn = embed_fn
        self.half_life = half_life_days
        # 权重
        self.w_sim = 0.45
        self.w_recency = 0.20
        self.w_importance = 0.20
        self.w_frequency = 0.15

    def retrieve(self, query: str, memories: list[Memory], top_k: int = 5) -> list[Memory]:
        query_emb = self.embed_fn(query)
        now = datetime.now()

        scored = []
        for mem in memories:
            # 向量相似度
            sim = self._cosine(query_emb, mem.embedding)

            # 时间衰减
            age = (now - datetime.fromisoformat(mem.timestamp)).days
            recency = math.exp(-age / self.half_life)

            # 重要性
            importance = mem.importance / 10.0

            # 频率
            frequency = min(mem.access_count / 10.0, 1.0)

            # 融合分数
            score = (self.w_sim * sim +
                    self.w_recency * recency +
                    self.w_importance * importance +
                    self.w_frequency * frequency)

            scored.append((mem, score))

        scored.sort(key=lambda x: -x[1])

        # 更新访问计数
        result = []
        for mem, score in scored[:top_k]:
            mem.access_count += 1
            result.append(mem)

        return result

    def _cosine(self, a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-8)
```

</details>

---

### 手撕题6: 实现策略路由的推理 Agent

<details>
<summary>点击查看参考答案</summary>

```python
"""
推理策略路由器
根据任务复杂度选择: CoT / Plan-Execute / ToT + Reflexion
"""

class ReasoningRouter:
    def __init__(self, llm_fn, tools: dict):
        self.llm_fn = llm_fn
        self.tools = tools

    def solve(self, task: str) -> dict:
        # 1. 评估复杂度
        complexity = self._assess(task)

        # 2. 选择策略
        if complexity == "simple":
            return self._cot(task)
        elif complexity == "medium":
            return self._plan_execute(task)
        else:
            return self._tot_with_reflexion(task)

    def _assess(self, task: str) -> str:
        prompt = f"""评估任务复杂度，只回答 simple/medium/complex:
- simple: 单步可完成，无需工具
- medium: 需要3-5步，可能需要工具
- complex: 需要探索多个方向，可能需要回溯

任务: {task}
复杂度:"""
        result = self.llm_fn(prompt).strip().lower()
        return result if result in ("simple", "medium", "complex") else "medium"

    def _cot(self, task):
        response = self.llm_fn(f"逐步思考:\n{task}\n\nLet's think step by step.")
        return {"strategy": "CoT", "result": response}

    def _plan_execute(self, task):
        # 规划
        plan = self.llm_fn(f"分解为步骤:\n{task}\n格式:\n1. ...\n2. ...")
        steps = [l for l in plan.split("\n") if l and l[0].isdigit()]

        # 执行
        results = []
        for step in steps:
            result = self.llm_fn(f"执行: {step}\n已有结果: {results[-3:]}")
            results.append(result)

        return {"strategy": "PlanExecute", "plan": steps, "results": results}

    def _tot_with_reflexion(self, task, max_attempts=2):
        reflections = []
        for attempt in range(max_attempts):
            # ToT: 生成多个候选
            candidates = self.llm_fn(
                f"任务: {task}\n生成3个不同的解决思路:\n"
                + ("\n".join(reflections) if reflections else "")
            ).split("\n")[:3]

            # 评估并选最优
            best = max(candidates, key=lambda c: self._evaluate(c, task))
            result = self.llm_fn(f"基于思路: {best}\n完整解决:\n{task}")

            if self._evaluate(result, task) > 0.7:
                return {"strategy": "ToT+Reflexion", "result": result,
                       "attempts": attempt + 1}

            # 反思
            reflections.append(
                self.llm_fn(f"方案失败，反思: {result}")
            )

        return {"strategy": "ToT+Reflexion", "result": result,
                "attempts": max_attempts, "reflections": reflections}

    def _evaluate(self, solution, task):
        try:
            return float(self.llm_fn(f"评估方案质量(0-1):\n任务:{task}\n方案:{solution}\n分数:"))
        except ValueError:
            return 0.5
```

</details>

---

## 三、Week 1 模拟面试（10 道综合题）

### Q1: "请从零设计一个客服 Agent 系统"

<details>
<summary>点击参考答案</summary>

**架构要点**：
1. **Agent Loop**: 接收用户消息 → 检索知识库 → 生成回复 → 用户确认
2. **工具**: 知识库搜索(RAG)、工单系统API、用户信息查询、订单查询
3. **记忆**: 短期(当前会话) + 长期(用户历史偏好)
4. **可靠性**: 最大轮次限制、敏感操作人机回环、输出过滤
5. **降级**: LLM 不可用时回退到关键词匹配 FAQ
6. **评估**: 成功率、平均轮次、用户满意度、转人工率

**关键设计**:
```python
# 分级处理
Level 1: FAQ 匹配（无需 LLM）
Level 2: RAG + LLM 生成（标准流程）
Level 3: Agent + 工具调用（需要查订单/开工单）
Level 4: 转人工（Agent 无法解决）
```

</details>

---

### Q2: "Agent 的循环为什么会失控？如何防止？"

<details>
<summary>点击查看参考答案</summary>

**失控原因**：
1. 工具返回错误，Agent 反复重试
2. 工具结果格式不符预期，Agent 反复调用
3. 目标条件永远无法满足

**防护措施**：
1. **最大轮次限制**（硬停止）
2. **Token 预算**（资源限制）
3. **超时控制**（时间限制）
4. **死循环检测**（连续N次相同动作 → 强制终止或注入新提示）
5. **进度检测**（连续5轮无新进展 → 转人工）

</details>

---

### Q3: "ReAct 和 Function Calling 有什么本质区别？"

<details>
<summary>点击查看参考答案</summary>

| 维度 | ReAct | Function Calling |
|------|-------|-----------------|
| 推理可见性 | 显式（Thought 可见） | 隐式（模型内部推理） |
| 格式 | 自由文本解析 | 结构化 JSON |
| 可靠性 | 依赖正则解析 | API 保证结构 |
| 通用性 | 任何 LLM | 需模型支持 |
| 调试性 | 高（可见推理） | 低 |

**本质区别**: ReAct 是一种**提示策略**，通过格式约束让 LLM 交替推理和行动；Function Calling 是**API 能力**，模型训练时就学会了输出结构化工具调用。现代实践中两者融合：用 Function Calling 的 API 保证可靠性，同时在 prompt 中要求 CoT 式推理。

</details>

---

### Q4: "MCP 解决了什么问题？为什么不直接用 Function Calling？"

<details>
<summary>点击查看参考答案</summary>

**MCP 解决的问题**: M 个 Agent × N 个工具 = M×N 个集成 → MCP 标准化后 = M+N

**为什么不直接用 Function Calling**:
- Function Calling 是**模型能力**（怎么调用），MCP 是**协议标准**（工具如何暴露）
- 没有 MCP: 每个 Agent 需要为每个工具单独写适配代码
- 有 MCP: 工具以 MCP Server 形式暴露，任何 MCP 兼容 Agent 都能使用
- MCP 还提供 Resources 和 Prompts，不仅仅是工具调用

**类比**: Function Calling 是"怎么打电话"，MCP 是"电话号码标准格式"。

</details>

---

### Q5: "如何评估一个 Agent 的质量？"

<details>
<summary>点击查看参考答案</summary>

**五维度评估**:
1. **成功率**: 任务完成的正确率
2. **过程质量**: 推理是否合理、步骤是否最优
3. **效率**: 平均轮次、Token 消耗、延迟
4. **安全性**: 是否执行危险操作、是否泄露信息
5. **用户体验**: 回复质量、用户满意度

**方法**:
- 端到端评估: 给定任务集，统计成功率
- 过程评估: 人工/LLM 评审每步决策
- 对比评估: A/B 测试不同策略
- 自动化: 用 LLM-as-Judge 批量评分

</details>

---

### Q6: "Agent 记忆系统中，如何处理记忆冲突？"

<details>
<summary>点击查看参考答案</summary>

**冲突场景**: 旧记忆说"用户喜欢 Java"，新记忆说"用户转用 Python 了"

**处理策略**:
1. **时间优先**: 最新记忆覆盖旧记忆
2. **重要性优先**: 高重要性记忆优先
3. **LLM 仲裁**: 让 LLM 判断哪个更可信
4. **标注分歧**: 保留两条，标注"偏好可能已变化"
5. **合并**: LLM 合并为"用户原喜欢 Java，近期转向 Python"

最佳实践: 时间 + LLM 仲裁 + 合并。

</details>

---

### Q7: "什么时候用 Plan-and-Execute，什么时候用 ReAct？"

<details>
<summary>点击查看参考答案</summary>

**用 ReAct**: 
- 探索性任务（不知道需要几步）
- 每步依赖前步结果
- 任务可能随时调整方向

**用 Plan-and-Execute**:
- 步骤可预先分解
- 长任务（ReAct 的上下文会溢出）
- Token 效率要求高
- 步骤可并行

**混合**: 先 Plan 生成大纲 → 逐段用 ReAct 执行（当前最流行）。

</details>

---

### Q8: "ToT 的代价是什么？什么时候值得用？"

<details>
<summary>点击查看参考答案</summary>

**代价**: O(branching^depth) 次 LLM 调用。如 branching=3, depth=4 → 最多 81 次调用。

**值得用的场景**:
- 答案正确性 >> 成本（如数学竞赛）
- 解空间大但有明确评估函数（可剪枝）
- 需要创造性探索（如创意写作）

**不值得**: 日常对话、简单问答、预算有限。

</details>

---

### Q9: "如何降低 Agent 的运行成本？"

<details>
<summary>点击查看参考答案</summary>

1. **模型路由**: 简单步骤用小模型（GPT-4o-mini），复杂推理用大模型（GPT-4）
2. **Prompt 缓存**: Claude/OpenAI 支持 prompt 前缀缓存，重复部分不计费
3. **上下文压缩**: 摘要旧消息，减少输入 token
4. **并行调用**: 独立工具并行执行，减少轮次
5. **提前终止**: 检测到已得到答案时立即终止循环
6. **缓存工具结果**: 相同输入不重复调用

</details>

---

### Q10: "如果要你从零搭建一个 Agent 框架，核心模块有哪些？"

<details>
<summary>点击查看参考答案</summary>

```
Agent Framework 核心模块:
1. Loop Engine      — Agent 循环（含安全网）
2. Tool Registry    — 工具注册与发现
3. Tool Executor    — 工具执行（含权限/沙箱）
4. Memory Module    — 四层记忆管理
5. Planner          — 规划器（CoT/Plan/ToT）
6. Context Manager  — 上下文窗口管理
7. Safety Guard     — 输入/输出过滤 + 人机回环
8. Evaluator        — 质量评估与监控
9. State Manager    — 状态持久化与恢复
10. Observability   — 日志/追踪/指标
```

</details>

---

## 四、Week 1 易错点总复习

| # | 易错点 | 正确理解 | 相关Day |
|---|--------|---------|---------|
| 1 | Agent = LLM | ❌ Agent = Harness + Model + Loop + Tools + Memory | Day1 |
| 2 | Agent 和 Workflow 一样 | ❌ Workflow 路径固定，Agent 路径动态 | Day1 |
| 3 | ReAct 就是 CoT + 工具 | ❌ ReAct 强调交替循环，不仅是叠加 | Day2 |
| 4 | Function Calling 是 LLM 调工具 | ❌ LLM 只输出 JSON，代码执行工具 | Day3 |
| 5 | MCP 替代 Function Calling | ❌ MCP 标准化工具暴露，FC 是调用机制，互补 | Day4 |
| 6 | 记忆就是存对话历史 | ❌ 需要提取关键信息，遗忘同样重要 | Day5 |
| 7 | 向量检索就够了 | ❌ 需要多因子：相似度+时间+重要性+频率 | Day5 |
| 8 | CoT 总是有益 | ❌ 简单任务过度思考反而降低性能 | Day6 |
| 9 | ToT 总比 CoT 好 | ❌ ToT 代价高，需按场景选择 | Day6 |
| 10 | 规划越详细越好 | ❌ 过度规划脆弱，应保持计划可调整 | Day6 |

---

## 五、自测检查清单

### 概念理解（10项）
- [ ] 能用一句话向非技术人员解释什么是 Agent
- [ ] 能画出 Agent Loop 的流程图并标注安全网位置
- [ ] 能解释 ReAct 的 Thought/Action/Observation 循环
- [ ] 能对比 Function Calling 在 OpenAI/Anthropic/Google 的差异
- [ ] 能解释 MCP 的 M×N → M+N 价值
- [ ] 能画出四层记忆架构图
- [ ] 能写出记忆检索的多因子评分公式
- [ ] 能对比 CoT/ToT/GoT/PoT 的结构差异
- [ ] 能解释 Reflexion 的自我反思循环
- [ ] 能列出 5 种多 Agent 协作模式

### 代码能力（6项）
- [ ] 能手写 Agent Loop（含安全网、超时、预算）
- [ ] 能手写 ReAct Agent（含死循环检测）
- [ ] 能手写并行工具调用（含超时控制）
- [ ] 能手写上下文压缩管理器
- [ ] 能手写多因子记忆检索器
- [ ] 能手写策略路由推理 Agent

### 系统设计（3项）
- [ ] 能设计客服 Agent 系统
- [ ] 能设计百万用户记忆系统
- [ ] 能设计多 Agent 研究系统

---

## 六、Week 2 预告

> **Week 2 — RAG 与 Agent 结合** 将涵盖：
>
> | Day | 主题 | 要点 |
> |-----|------|------|
> | 08 | RAG 基础与架构 | 检索增强生成原理、朴素RAG vs 高级RAG |
> | 09 | 文档处理与分块策略 | Chunk 策略、语义分块、父子分块 |
> | 10 | Embedding 与向量检索 | 模型选型、混合检索、重排序 |
> | 11 | RAG 进阶：查询改写与多路召回 | HyDE、子查询、RAG-Fusion |
> | 12 | GraphRAG 与知识图谱增强 | 图谱构建、社区检测、全局查询 |
> | 13 | Agentic RAG — Agent 驱动的 RAG | Agent 自主检索、迭代检索、多跳推理 |
> | 14 | RAG 评估与优化 | RAGAS 框架、评估指标、A/B 测试 |
