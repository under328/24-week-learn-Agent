# Day 06 — Agent 规划与推理范式

> **本周进度**: Day1 ✅ → Day2 ✅ → Day3 ✅ → Day4 ✅ → Day5 ✅ 记忆系统 → **Day6 规划与推理** → Day7 回顾与手撕

---

## 一、知识图谱

```
              Agent 推理与规划
                    │
        ┌───────────┼───────────┐
        │           │           │
     推理范式      规划策略     自我改进
        │           │           │
   ┌────┼────┐   ┌──┼──┐    ┌───┼───┐
   │    │    │   │  │  │    │   │   │
  CoT  ToT  GoT  前向 逆向  Plan Reflexion
   │    │    │   规划 规划  &   自省
  PoT  ReAct    │           Execute  │
       │      分解           模式    Self-Refine
      循环    抽象                  │
                                     LATS
```

**核心关系链**: 感知 → 推理(CoT/ToT) → 规划(分解/排序) → 执行 → 反思(Reflexion) → 改进

---

## 二、面试题（10 道）

### Q1: 什么是 Chain-of-Thought (CoT) 推理？为什么它能提升 LLM 的推理能力？

<details>
<summary>点击查看参考答案</summary>

**Chain-of-Thought (CoT)** 是一种引导 LLM 在给出最终答案前，先逐步展示推理过程的提示技术。

#### CoT 的两种形式

**1. Zero-shot CoT** — 简单触发词
```
问: 一个商店有 23 个苹果，卖了 17 个，又进了 12 个，现在有多少个？
答: Let's think step by step.
    1. 初始有 23 个苹果
    2. 卖了 17 个：23 - 17 = 6 个
    3. 又进了 12 个：6 + 12 = 18 个
    答案: 18
```

**2. Few-shot CoT** — 提供带推理过程的示例
```
示例:
Q: Roger有5个网球，又买了2筒，每筒3个。他有多少个网球？
A: Roger开始有5个。买了2筒×3个=6个。5+6=11。答案: 11。

Q: [新问题]
A: [模型模仿推理格式]
```

#### 为什么 CoT 有效？

| 原因 | 说明 |
|------|------|
| **分解复杂问题** | 将多步推理分解为简单步骤，降低每步难度 |
| **分配更多计算** | 更多中间 token = 更多前向计算 = 更强推理 |
| **减少跳步错误** | 强制逐步推理，避免直觉跳跃 |
| **可调试性** | 中间步骤可见，便于定位推理错误 |

#### CoT 的适用边界

```python
# CoT 对不同任务的提升幅度不同
cot_benefits = {
    "多步数学推理": "显著提升 (+20-40%)",
    "逻辑推理": "显著提升",
    "常识推理": "中等提升",
    "简单问答": "几乎无提升，甚至降低",
    "创意写作": "可能降低（过度结构化）",
}
```

#### 与 Function Calling 的关系

现代 LLM（GPT-4, Claude 3.5）已将 CoT 内化为"隐式推理"——模型在生成 tool call 前内部完成推理，不一定输出可见的 CoT 文本。但在复杂任务中，显式 CoT 仍有价值。

</details>

---

### Q2: Tree of Thoughts (ToT) 是什么？与 CoT 有什么区别？

<details>
<summary>点击查看参考答案</summary>

**Tree of Thoughts (ToT)** 将推理过程从线性链扩展为树形搜索——在每个推理步骤生成多个候选想法，评估后选择最优路径继续探索。

#### CoT vs ToT 对比

```
CoT (线性):
  想法1 → 想法2 → 想法3 → 答案
  (一条路走到底，走错了无法回头)

ToT (树形):
              想法1-A ─→ 想法2-A ─→ 答案 ✓
             /
  想法1 ──┤
             \
              想法1-B ─→ 想法2-B ─→ 死路 ✗
                              \
                               想法2-C ─→ 答案 ✓
  (多路探索，可以剪枝和回溯)
```

#### ToT 的四个核心步骤

```python
class TreeOfThoughts:
    def __init__(self, llm, max_depth=5, branching=3):
        self.llm = llm
        self.max_depth = max_depth
        self.branching = branching  # 每步生成几个候选

    def solve(self, problem):
        # 1. 思维分解：将问题分解为多个思考步骤
        steps = self.decompose(problem)

        # 2. 思维生成：每步生成多个候选想法
        # 3. 状态评估：给每个候选想法打分
        # 4. 搜索：BFS/DFS + 剪枝
        return self.search(problem, depth=0)

    def search(self, state, depth):
        if depth >= self.max_depth:
            return self.evaluate(state)

        # 生成多个候选想法
        thoughts = self.generate_thoughts(state, n=self.branching)

        # 评估每个想法
        evaluated = [(t, self.evaluate(t)) for t in thoughts]

        # 按分数排序，剪枝低分分支
        evaluated.sort(key=lambda x: -x[1])
        for thought, score in evaluated[:self.branching]:
            result = self.search(thought, depth + 1)
            if result is not None:
                return result
        return None

    def generate_thoughts(self, state, n):
        """生成 n 个候选想法"""
        prompt = f"当前状态: {state}\n生成 {n} 个不同的下一步推理:"
        return self.llm.generate(prompt).split("\n")[:n]

    def evaluate(self, state):
        """评估状态：返回 0-1 分数"""
        prompt = f"评估以下推理状态是否接近正确答案 (0-1):\n{state}"
        return float(self.llm.generate(prompt))
```

#### ToT 的适用场景

- **24 点游戏**：需要尝试多种运算组合
- **创意写作**：探索多个故事走向
- **数学证明**：多条证明路径尝试
- **填字游戏**：需要全局搜索

#### ToT 的代价

| 维度 | CoT | ToT |
|------|-----|-----|
| LLM 调用次数 | 1 次 | O(branching^depth) 次 |
| 延迟 | 低 | 高（可并行部分缓解） |
| 成本 | 低 | 高 |
| 准确率提升 | 基线 | +10-30%（复杂任务） |

**面试要点**：ToT 用更多计算换取更高准确率，适合"对"比"快"重要的场景。

</details>

---

### Q3: Plan-and-Execute 模式如何工作？与 ReAct 有什么区别？

<details>
<summary>点击查看参考答案</summary>

**Plan-and-Execute** 是一种两阶段 Agent 模式：先一次性生成完整计划，再逐步执行。

#### 工作流程

```
阶段1: Planning
  用户请求 → Planner LLM → 生成步骤列表

阶段2: Execution
  Step 1 → Executor → 结果
  Step 2 → Executor → 结果
  ...
  Step N → Executor → 结果

阶段3: Re-planning (可选)
  如果某步失败或发现新信息 → 重新规划剩余步骤
```

#### Plan-and-Execute vs ReAct

| 维度 | ReAct | Plan-and-Execute |
|------|-------|-----------------|
| **规划方式** | 每步即时决策 | 先全局规划再执行 |
| **上下文消耗** | 每步都带完整历史 | 执行时只需当前步骤 |
| **适合任务** | 探索性、不确定性强 | 步骤明确、可预先分解 |
| **错误恢复** | 自然适应 | 需要 re-planning |
| **Token 效率** | 低（重复传上下文） | 高（执行器只看单步） |
| **延迟** | 每步等待 LLM | 计划阶段集中，执行可并行 |

#### 代码实现

```python
class PlanAndExecuteAgent:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def run(self, task: str):
        # 阶段1: 规划
        plan = self.create_plan(task)

        # 阶段2: 逐步执行
        results = []
        for i, step in enumerate(plan):
            # 执行单步（执行器只需当前步骤+前序结果摘要）
            result = self.execute_step(step, results)

            if result.get("needs_replan"):
                # 阶段3: 重新规划剩余部分
                remaining = self.replan(task, plan[:i+1], results, plan[i+1:])
                plan = plan[:i+1] + remaining
                continue

            results.append({"step": step, "result": result})

        return results

    def create_plan(self, task: str) -> list[str]:
        prompt = f"""将以下任务分解为具体可执行步骤。
每步应能用一个工具调用完成。

任务: {task}

输出格式:
1. [步骤描述]
2. [步骤描述]
...
"""
        response = self.llm.generate(prompt)
        return [line.split(". ", 1)[1] for line in response.strip().split("\n") if line[0].isdigit()]

    def execute_step(self, step: str, previous_results: list) -> dict:
        # 执行器只需当前步骤 + 前序结果摘要
        context = "\n".join([f"{r['step']}: {str(r['result'])[:200]}" for r in previous_results[-3:]])

        prompt = f"""执行以下步骤。如果发现原计划不可行，标记 needs_replan=true。

前序结果摘要:
{context}

当前步骤: {step}
可用工具: {list(self.tools.keys())}
"""
        response = self.llm.generate(prompt)
        # 解析工具调用并执行...
        return {"output": response, "needs_replan": "replan" in response.lower()}

    def replan(self, task, completed_steps, results, remaining_steps):
        prompt = f"""重新规划任务。

原任务: {task}
已完成步骤: {completed_steps}
执行结果: {results}
原计划剩余: {remaining_steps}

基于当前情况，重新规划剩余步骤:"""
        response = self.llm.generate(prompt)
        return [line.split(". ", 1)[1] for line in response.strip().split("\n") if line[0].isdigit()]
```

#### 何时选择 Plan-and-Execute？

- **多步研究任务**：先列出搜索关键词，再逐一搜索
- **数据处理管道**：先定义 ETL 步骤，再执行
- **代码重构**：先规划改动范围，再逐文件修改
- **长任务**：上下文窗口装不下完整的 ReAct 循环

</details>

---

### Q4: Reflexion 机制是什么？如何让 Agent 从失败中学习？

<details>
<summary>点击查看参考答案</summary>

**Reflexion** 是一种自我反思机制——Agent 在任务失败后，生成反思总结存入记忆，下次尝试时利用反思避免重复错误。

#### Reflexion 循环

```
┌─────────────────────────────────────────┐
│           Reflexion 循环                │
│                                         │
│  Attempt 1: 执行任务 → 失败             │
│       ↓                                 │
│  Reflect: "为什么失败？该怎么改进？"     │
│       ↓                                 │
│  存储反思到记忆                         │
│       ↓                                 │
│  Attempt 2: 执行任务（带反思记忆）→ 成功 │
│       ↓                                 │
│  Reflect: "这次做对了什么？"             │
│           (强化成功经验)                 │
└─────────────────────────────────────────┘
```

#### 核心实现

```python
class ReflexionAgent:
    def __init__(self, llm, tools, max_attempts=3):
        self.llm = llm
        self.tools = tools
        self.max_attempts = max_attempts
        self.reflections: list[str] = []  # 反思记忆

    def run(self, task: str):
        for attempt in range(1, self.max_attempts + 1):
            # 执行任务（注入历史反思）
            result = self.execute(task, attempt)

            # 评估结果
            if self.is_success(result):
                return result

            # 失败 → 生成反思
            reflection = self.reflect(task, result, attempt)
            self.reflections.append(reflection)
            print(f"Attempt {attempt} 失败。反思: {reflection}")

        return {"success": False, "reflections": self.reflections}

    def execute(self, task: str, attempt: int):
        # 将历史反思注入 prompt
        reflection_block = ""
        if self.reflections:
            reflection_block = "\n## 过去的反思（避免重复错误）\n"
            for i, r in enumerate(self.reflections):
                reflection_block += f"{i+1}. {r}\n"

        prompt = f"""任务: {task}
{reflection_block}

这是第 {attempt} 次尝试。请执行任务。"""
        # 执行 Agent 循环...
        return self.llm.generate(prompt)

    def reflect(self, task, result, attempt):
        prompt = f"""你刚才尝试完成以下任务但失败了。

任务: {task}
尝试结果: {result}
这是第 {attempt} 次失败。

请反思:
1. 失败的具体原因是什么？
2. 哪一步做错了？
3. 下次应该怎么避免？

用 2-3 句话总结反思:"""
        return self.llm.generate(prompt)

    def is_success(self, result):
        # 根据任务定义成功标准
        return "success" in result.lower()
```

#### Reflexion vs Self-Refine

| 维度 | Reflexion | Self-Refine |
|------|-----------|-------------|
| **触发条件** | 失败后反思 | 主动自我审查 |
| **改进方式** | 存储反思到记忆 | 直接修改输出 |
| **跨任务学习** | ✅ 反思可跨任务复用 | ❌ 只改进当前输出 |
| **迭代方式** | 整个任务重试 | 单次输出迭代改进 |

#### Reflexion 的适用场景

- **编程题**：运行失败 → 反思代码错误 → 修改重试
- **数学题**：答案错误 → 分析推理过程 → 重新推导
- **搜索任务**：没找到答案 → 反思搜索策略 → 换关键词重搜

</details>

---

### Q5: Graph of Thoughts (GoT) 和 Program of Thoughts (PoT) 分别解决什么问题？

<details>
<summary>点击查看参考答案</summary>

#### Graph of Thoughts (GoT) — 图结构推理

**核心改进**：ToT 是树形搜索，但有些推理需要**合并**不同分支的见解。GoT 将推理结构从树扩展为有向图。

```
ToT (树):                    GoT (图):
  A                             A
 / \                           / \
B   C                         B   C
|   |          →              |   |
D   E                         D   E
    |                          \ /
    F                           F (合并 B+D 和 C+E 的见解)
```

**GoT 支持的操作**：
- **聚合（Aggregation）**：合并多个推理分支
- **精炼（Refinement）**：改进某个中间想法
- **回溯（Backtracking）**：放弃某分支返回上游

```python
class GraphOfThoughts:
    def __init__(self, llm):
        self.llm = llm
        self.graph = {}  # 节点 -> 后继节点

    def solve(self, problem):
        # 1. 生成初始想法
        initial = self.generate(problem, n=3)

        # 2. 并行扩展
        expanded = [self.expand(idea) for idea in initial]

        # 3. 聚合多个分支
        merged = self.aggregate(expanded)

        # 4. 精炼
        refined = self.refine(merged)

        return refined

    def aggregate(self, branches):
        """合并多个推理分支的见解"""
        prompt = f"""合并以下多个推理路径的见解，形成一个更完整的推理:

路径1: {branches[0]}
路径2: {branches[1]}
路径3: {branches[2]}

合并后的推理:"""
        return self.llm.generate(prompt)
```

**适用场景**：需要综合多个角度的分析任务（如：多角度评估一个方案）

#### Program of Thoughts (PoT) — 程序化推理

**核心思想**：让 LLM 生成代码来执行推理，而不是用自然语言推理。数值和逻辑运算交给解释器，LLM 只负责翻译问题为代码。

```
PoT 流程:
  问题 → LLM 生成 Python 代码 → 执行代码 → 结果

对比 CoT:
  问题 → LLM 自然语言推理 → 结果
  (LLM 不擅长精确算术，容易算错)
```

```python
# PoT 示例
problem = "一个班级有32个学生，男生比女生多4人，男生有多少人？"

# CoT 可能出错: "32-4=28, 28/2=14, 14+4=18" (如果中间算错就全错)
# PoT 生成代码:
code = """
total = 32
diff = 4
girls = (total - diff) / 2
boys = girls + diff
print(boys)
"""
# 执行代码 → 18 (精确无误)
```

**PoT 的优势**：
- 算术运算零错误（解释器保证）
- 可以处理复杂数据结构
- 可验证、可调试

**PoT 的局限**：
- 需要代码执行环境
- 非数值推理（如语义理解）不适用
- 增加系统复杂度

#### 四种推理范式对比

| 范式 | 结构 | 适用场景 | 计算成本 |
|------|------|----------|---------|
| CoT | 线性链 | 通用推理 | 低 |
| ToT | 树形搜索 | 需要探索多个方向 | 中高 |
| GoT | 图结构 | 需要合并多角度见解 | 高 |
| PoT | 代码执行 | 数值/逻辑计算 | 中 |

</details>

---

### Q6: 什么是前向规划与逆向规划？各有什么优劣？

<details>
<summary>点击查看参考答案</summary>

#### 前向规划（Forward Planning）

从当前状态出发，逐步向目标推进。

```
当前状态 → 动作1 → 状态1 → 动作2 → 状态2 → ... → 目标
```

```python
class ForwardPlanner:
    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

    def plan(self, current_state, goal):
        steps = []
        state = current_state
        max_steps = 20

        while not self.is_goal_reached(state, goal) and len(steps) < max_steps:
            # 从当前状态选择下一步动作
            action = self.choose_action(state, goal)
            steps.append(action)
            # 模拟执行（预测下一状态）
            state = self.predict_next_state(state, action)

        return steps

    def choose_action(self, state, goal):
        prompt = f"""当前状态: {state}
目标: {goal}
可用工具: {list(self.tools.keys())}

选择下一步操作:"""
        return self.llm.generate(prompt)
```

#### 逆向规划（Backward Planning）

从目标倒推，确定达到目标需要什么前提条件。

```
目标 → 需要什么前提？ → 前提A → 需要什么前提？ → ... → 当前状态
```

```python
class BackwardPlanner:
    def __init__(self, llm):
        self.llm = llm

    def plan(self, goal, current_state):
        steps = []
        sub_goal = goal
        max_steps = 20

        while not self.is_satisfied(sub_goal, current_state) and len(steps) < max_steps:
            # 从目标倒推：达到这个目标需要什么前提？
            prerequisite, action = self.find_prerequisite(sub_goal, current_state)
            steps.insert(0, action)  # 逆序插入
            sub_goal = prerequisite  # 前提成为新的子目标

        return steps

    def find_prerequisite(self, goal, current_state):
        prompt = f"""要实现以下目标，需要什么前提条件？用什么操作可以达到？

目标: {goal}
当前状态: {current_state}

输出:
前提条件: [什么条件满足后可以做]
操作: [具体操作]
"""
        response = self.llm.generate(prompt)
        # 解析前提和操作...
        return prerequisite, action
```

#### 对比分析

| 维度 | 前向规划 | 逆向规划 |
|------|---------|---------|
| **起点** | 当前状态 | 目标状态 |
| **思维方向** | "我现在能做什么？" | "要达到目标需要什么？" |
| **适合场景** | 探索性任务、状态空间大 | 目标明确、状态空间大 |
| **分支因子** | 可能很高（很多可选动作） | 通常较低（达到目标路径有限） |
| **例子** | "写一篇博客"（从大纲开始写） | "部署到生产"（倒推需要的步骤） |

**类比理解**：
- 前向规划：从家出发，看到路口就选一个方向走，直到到达目的地
- 逆向规划：从目的地出发，倒推"要到B得先到A，要到A得先到..."

**实际 Agent 中的混合使用**：
```python
class HybridPlanner:
    def plan(self, task):
        # 1. 逆向规划：从目标分解出关键里程碑
        milestones = self.backward_plan(task.goal, task.current_state)

        # 2. 前向规划：对每个里程碑，从当前状态规划到达路径
        full_plan = []
        state = task.current_state
        for milestone in milestones:
            sub_plan = self.forward_plan(state, milestone)
            full_plan.extend(sub_plan)
            state = self.simulate(state, sub_plan)

        return full_plan
```

</details>

---

### Q7: 多 Agent 协作规划有哪些模式？如何设计协作策略？

<details>
<summary>点击查看参考答案</summary>

#### 多 Agent 协作的五种经典模式

```
1. 层级模式 (Hierarchical)
   Manager → Worker1, Worker2, Worker3

2. 顺序模式 (Sequential Pipeline)
   Agent A → Agent B → Agent C

3. 并行模式 (Parallel)
   Agent A ─┐
   Agent B ─┤→ Aggregator
   Agent C ─┘

4. 辩论模式 (Debate)
   Agent A ↔ Agent B → Judge

5. 竞争模式 (Competition)
   Agent A ─┐
   Agent B ─┤→ Judge (选最佳)
   Agent C ─┘
```

#### 各模式详解

```python
# 1. 层级模式
class HierarchicalTeam:
    """Manager 分配任务，Workers 执行并汇报"""
    def __init__(self, manager_llm, workers: dict):
        self.manager = manager_llm
        self.workers = workers  # {role: agent}

    def run(self, task):
        # Manager 分解并分配
        assignments = self.manager.assign(task, list(self.workers.keys()))

        results = {}
        for role, subtask in assignments.items():
            results[role] = self.workers[role].run(subtask)

        # Manager 汇总
        return self.manager.synthesize(results)


# 2. 辩论模式
class DebateTeam:
    """多个 Agent 从不同角度辩论，Judge 裁决"""
    def __init__(self, debaters: list, judge_llm):
        self.debaters = debaters
        self.judge = judge_llm

    def run(self, question, rounds=3):
        positions = [d.initial_position(question) for d in self.debaters]

        for r in range(rounds):
            for i, debater in enumerate(self.debaters):
                # 看到其他人的观点后反驳
                others = [p for j, p in enumerate(positions) if j != i]
                positions[i] = debater.respond(question, positions[i], others)

        # Judge 裁决
        return self.judge.decide(question, positions)


# 3. 并行模式
class ParallelTeam:
    """多个 Agent 独立解决同一问题，聚合结果"""
    def __init__(self, agents: list, aggregator_llm):
        self.agents = agents
        self.aggregator = aggregator_llm

    async def run(self, task):
        # 并行执行
        results = await asyncio.gather(*[a.run(task) for a in self.agents])

        # 聚合
        return self.aggregator.merge(results)
```

#### 协作规划的核心问题

| 问题 | 解决方案 |
|------|---------|
| **任务分配** | Manager 根据能力画像分配 |
| **信息共享** | 共享黑板模式 / 消息传递 |
| **冲突处理** | Judge 仲裁 / 投票 / 优先级 |
| **终止条件** | 轮次上限 / 共识达成 | 
| **成本控制** | 限制参与Agent数和轮次 |

```python
class SharedBlackboard:
    """共享黑板：所有 Agent 读写同一信息空间"""
    def __init__(self):
        self.board = []

    def write(self, agent_name, content):
        self.board.append({"agent": agent_name, "content": content,
                           "timestamp": time.time()})

    def read(self, since=0):
        return [e for e in self.board if e["timestamp"] > since]
```

#### 真实案例

- **AutoGen**：微软的多 Agent 对话框架，支持角色扮演和群聊
- **MetaGPT**：模拟软件团队（PM/架构师/工程师/QA）
- **CrewAI**：角色驱动的多 Agent 协作

</details>

---

### Q8: Agent 规划失败的常见原因有哪些？如何设计恢复策略？

<details>
<summary>点击参考答案</summary>

#### 规划失败的 7 大原因

| # | 失败原因 | 示例 | 频率 |
|---|---------|------|------|
| 1 | **过度规划** | 计划太详细，第一步就偏离 | 高 |
| 2 | **前提假设错误** | 假设 API 可用但已下线 | 高 |
| 3 | **步骤依赖断裂** | Step 3 依赖 Step 2 的结果，但 Step 2 输出格式不符 | 高 |
| 4 | **状态空间爆炸** | 分支太多，搜索无法收敛 | 中 |
| 5 | **目标漂移** | 执行过程中偏离原始目标 | 中 |
| 6 | **循环依赖** | Step A 依赖 B，B 依赖 A | 低 |
| 7 | **资源耗尽** | Token/时间/成本超出预算 | 中 |

#### 恢复策略设计

```python
class PlanRecovery:
    """多层级规划恢复策略"""

    def __init__(self, llm, max_retries=3):
        self.llm = llm
        self.max_retries = max_retries

    def recover(self, plan, failed_step, error, context):
        # Level 1: 重试（瞬时错误）
        if self.is_transient(error):
            return {"action": "retry", "step": failed_step}

        # Level 2: 微调当前步骤
        adjusted = self.adjust_step(failed_step, error, context)
        if adjusted:
            return {"action": "adjust", "new_step": adjusted}

        # Level 3: 局部重新规划（只重做剩余步骤）
        new_plan = self.replan_remaining(
            original_plan=plan,
            failed_step=failed_step,
            error=error,
            completed=context.get("completed_steps", [])
        )
        if new_plan:
            return {"action": "replan_remaining", "new_steps": new_plan}

        # Level 4: 全局重新规划
        full_replan = self.full_replan(
            original_task=context["task"],
            what_we_know=context["results_so_far"],
            what_failed=error
        )
        if full_replan:
            return {"action": "full_replan", "new_plan": full_replan}

        # Level 5: 降级（返回部分结果 + 人工介入）
        return {"action": "degrade", "partial_results": context["results_so_far"],
                "escalation": True}

    def adjust_step(self, step, error, context):
        """微调失败步骤"""
        prompt = f"""步骤执行失败，请调整步骤。

原步骤: {step}
错误: {error}
已有信息: {context}

请给出调整后的步骤（只改必要部分）:"""
        return self.llm.generate(prompt)

    def replan_remaining(self, original_plan, failed_step, error, completed):
        """重新规划剩余步骤"""
        prompt = f"""原计划的某步失败了，请重新规划剩余部分。

已完成: {completed}
失败步骤: {failed_step}
错误: {error}
原计划剩余: {[s for s in original_plan if s not in completed]}

基于已有结果，重新规划剩余步骤:"""
        response = self.llm.generate(prompt)
        return self.parse_steps(response)
```

#### 预防性设计

```python
class RobustPlanner:
    """带预防机制的规划器"""

    def plan(self, task):
        raw_plan = self.generate_plan(task)

        # 验证1: 步骤间依赖是否合理
        if not self.validate_dependencies(raw_plan):
            raw_plan = self.fix_dependencies(raw_plan)

        # 验证2: 每步是否有明确的成功条件
        for step in raw_plan:
            if not step.get("success_criteria"):
                step["success_criteria"] = self.define_success_criteria(step)

        # 验证3: 添加检查点（每 N 步验证一次）
        plan_with_checkpoints = self.add_checkpoints(raw_plan, every=3)

        # 验证4: 设置预算上限
        plan_with_checkpoints["budget"] = {
            "max_steps": 20,
            "max_tokens": 50000,
            "max_cost": 1.0,  # USD
            "timeout": 300     # seconds
        }

        return plan_with_checkpoints
```

</details>

---

### Q9: 手撕一个支持多种推理范式的 Agent 框架

<details>
<summary>点击查看参考答案</summary>

```python
"""
多范式推理 Agent 框架
支持: CoT, ToT, Plan-and-Execute, Reflexion
根据任务复杂度自动选择推理策略
"""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TaskContext:
    task: str
    complexity: str = "medium"  # simple/medium/complex
    max_steps: int = 10
    max_retries: int = 3
    history: list = field(default_factory=list)
    reflections: list = field(default_factory=list)


class ReasoningStrategy(ABC):
    """推理策略抽象基类"""

    @abstractmethod
    def solve(self, ctx: TaskContext, llm_fn, tools: dict) -> dict:
        pass


# ============ 策略1: CoT ============

class CoTStrategy(ReasoningStrategy):
    """Chain-of-Thought: 线性逐步推理"""

    def solve(self, ctx, llm_fn, tools):
        prompt = f"""任务: {ctx.task}

请逐步思考并完成任务。每步说明你的推理过程。

Let's think step by step."""
        response = llm_fn(prompt)
        return {"strategy": "CoT", "result": response, "steps": 1}


# ============ 策略2: ToT ============

class ToTStrategy(ReasoningStrategy):
    """Tree of Thoughts: 树形搜索推理"""

    def __init__(self, branching=3, max_depth=4):
        self.branching = branching
        self.max_depth = max_depth

    def solve(self, ctx, llm_fn, tools):
        best = None
        best_score = -1

        # BFS 搜索
        frontier = [("", 0)]  # (state, depth)

        while frontier:
            state, depth = frontier.pop(0)

            if depth >= self.max_depth:
                score = self._evaluate(state, ctx.task, llm_fn)
                if score > best_score:
                    best_score = score
                    best = state
                continue

            # 生成候选
            candidates = self._generate(state, ctx.task, llm_fn, self.branching)
            for cand in candidates:
                score = self._evaluate(cand, ctx.task, llm_fn)
                if score > 0.3:  # 剪枝阈值
                    frontier.append((cand, depth + 1))

        return {"strategy": "ToT", "result": best, "score": best_score}

    def _generate(self, state, task, llm_fn, n):
        prompt = f"任务: {task}\n当前推理: {state or '(开始)'}\n生成 {n} 个不同的下一步推理:"
        return [l.strip() for l in llm_fn(prompt).split("\n") if l.strip()][:n]

    def _evaluate(self, state, task, llm_fn):
        prompt = f"任务: {task}\n推理: {state}\n这个推理方向有多接近正确答案？(0.0-1.0)"
        try:
            return float(llm_fn(prompt).strip())
        except ValueError:
            return 0.5


# ============ 策略3: Plan-and-Execute ============

class PlanExecuteStrategy(ReasoningStrategy):
    """先规划再执行"""

    def solve(self, ctx, llm_fn, tools):
        # 阶段1: 规划
        plan = self._plan(ctx.task, llm_fn)
        ctx.history.append({"phase": "plan", "output": plan})

        # 阶段2: 执行
        results = []
        for i, step in enumerate(plan):
            result = self._execute(step, results, llm_fn, tools)
            results.append({"step": step, "result": result})
            ctx.history.append({"phase": "execute", "step": i, "output": result})

            # 检查是否需要重新规划
            if self._needs_replan(result):
                remaining = plan[i+1:]
                new_plan = self._replan(ctx.task, results, remaining, llm_fn)
                plan = plan[:i+1] + new_plan

        return {"strategy": "PlanExecute", "plan": plan, "results": results}

    def _plan(self, task, llm_fn):
        prompt = f"将任务分解为步骤:\n{task}\n\n格式:\n1. ...\n2. ..."
        response = llm_fn(prompt)
        return [l.split(". ", 1)[1] for l in response.split("\n") if l and l[0].isdigit()]

    def _execute(self, step, prev_results, llm_fn, tools):
        prompt = f"执行步骤: {step}\n前序结果: {prev_results[-3:]}"
        return llm_fn(prompt)

    def _needs_replan(self, result):
        return "无法完成" in result or "错误" in result

    def _replan(self, task, completed, remaining, llm_fn):
        prompt = f"重新规划:\n任务: {task}\n已完成: {completed}\n失败原因需调整\n原剩余: {remaining}"
        response = llm_fn(prompt)
        return [l.split(". ", 1)[1] for l in response.split("\n") if l and l[0].isdigit()]


# ============ 策略4: Reflexion ============

class ReflexionStrategy(ReasoningStrategy):
    """自我反思：失败后学习"""

    def __init__(self, inner_strategy: ReasoningStrategy = None):
        self.inner = inner_strategy or CoTStrategy()

    def solve(self, ctx, llm_fn, tools):
        for attempt in range(1, ctx.max_retries + 1):
            # 注入历史反思
            reflection_block = ""
            if ctx.reflections:
                reflection_block = "\n## 过去反思\n" + "\n".join(ctx.reflections)

            # 用内部策略执行
            result = self.inner.solve(ctx, llm_fn, tools)
            result["attempt"] = attempt

            # 评估
            if self._is_success(result):
                result["reflections_used"] = len(ctx.reflections)
                return result

            # 反思
            reflection = self._reflect(ctx.task, result, attempt, llm_fn)
            ctx.reflections.append(reflection)

        return {"strategy": "Reflexion", "success": False,
                "reflections": ctx.reflections}

    def _is_success(self, result):
        return result.get("score", 0) > 0.7 or result.get("result", "")

    def _reflect(self, task, result, attempt, llm_fn):
        prompt = f"""任务: {task}
尝试 {attempt} 结果: {result.get('result', 'N/A')}

反思失败原因，用2-3句话总结:"""
        return llm_fn(prompt)


# ============ 策略选择器 ============

class StrategyRouter:
    """根据任务特征自动选择推理策略"""

    def __init__(self):
        self.strategies = {
            "simple": CoTStrategy(),
            "medium": PlanExecuteStrategy(),
            "complex": ToTStrategy(branching=3, max_depth=4),
        }

    def assess_complexity(self, task: str, llm_fn) -> str:
        prompt = f"""评估任务复杂度 (simple/medium/complex):
- simple: 单步可完成
- medium: 需要3-5步
- complex: 需要探索多个方向、可能需要回溯

任务: {task}
复杂度:"""
        result = llm_fn(prompt).strip().lower()
        return result if result in self.strategies else "medium"

    def solve(self, task: str, llm_fn, tools: dict):
        ctx = TaskContext(task=task)
        ctx.complexity = self.assess_complexity(task, llm_fn)

        strategy = self.strategies.get(ctx.complexity, self.strategies["medium"])

        # 对 medium/complex 任务叠加 Reflexion
        if ctx.complexity in ("medium", "complex"):
            strategy = ReflexionStrategy(inner_strategy=strategy)

        return strategy.solve(ctx, llm_fn, tools)


# ============ 使用示例 ============

if __name__ == "__main__":
    def mock_llm(prompt: str) -> str:
        return f"[LLM] {prompt[:80]}..."

    router = StrategyRouter()

    # 简单任务 → CoT
    print(router.solve("1+1等于几？", mock_llm, {}))

    # 中等任务 → Plan-and-Execute + Reflexion
    print(router.solve("帮我分析这份报告并写摘要", mock_llm, {}))

    # 复杂任务 → ToT + Reflexion
    print(router.solve("设计一个支持百万并发的聊天系统", mock_llm, {}))
```

</details>

---

### Q10: 系统设计题 — 设计一个能处理复杂研究任务的 Agent 系统

<details>
<summary>点击查看参考答案</summary>

#### 需求

设计一个 Agent 系统，能够接受复杂研究问题（如"分析2026年AI Agent领域的投资趋势"），自主规划研究步骤、搜索信息、分析数据、生成报告。

#### 系统架构

```
┌────────────────────────────────────────────────────────┐
│                   Research Agent System                │
│                                                        │
│  ┌──────────┐   ┌───────────┐   ┌──────────────┐     │
│  │  Planner │──→│  Executor │──→│  Synthesizer │     │
│  │ (规划器) │   │  (执行器)  │   │   (综合器)   │     │
│  └────┬─────┘   └─────┬─────┘   └──────┬───────┘     │
│       │               │                │              │
│       │         ┌─────┼─────┐          │              │
│       │         │     │     │          │              │
│       │      Search  Analyze Write     │              │
│       │      Agent  Agent  Agent       │              │
│       │               │                │              │
│  ┌────┴───────────────┴────────────────┴───────┐     │
│  │              Memory & State                  │     │
│  │  ┌────────┐  ┌──────────┐  ┌────────────┐  │     │
│  │  │计划状态│  │研究结果库│  │ 反思记忆   │  │     │
│  │  └────────┘  └──────────┘  └────────────┘  │     │
│  └─────────────────────────────────────────────┘     │
│                                                        │
│  ┌─────────────────────────────────────────────┐     │
│  │              Tool Layer                      │     │
│  │  Web Search | Vector DB | Code Exec | Charts │     │
│  └─────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────┘
```

#### 核心组件设计

**1. Planner（规划器）**
```python
class ResearchPlanner:
    def create_research_plan(self, question: str) -> dict:
        prompt = f"""你是一个研究规划专家。为以下研究问题制定计划:

问题: {question}

输出 JSON:
{{
  "sub_questions": ["子问题1", "子问题2", ...],
  "search_queries": ["搜索关键词1", ...],
  "data_sources": ["数据源1", ...],
  "analysis_steps": ["分析步骤1", ...],
  "report_structure": ["报告章节1", ...]
}}"""
        return json.loads(self.llm.generate(prompt))
```

**2. Executor（执行器）— 多 Agent 并行**
```python
class ResearchExecutor:
    async def execute(self, plan: dict):
        # 并行搜索
        search_results = await asyncio.gather(*[
            self.search_agent.search(q) for q in plan["search_queries"]
        ])

        # 并行分析
        analyses = await asyncio.gather(*[
            self.analyze_agent.analyze(r, sq)
            for r, sq in zip(search_results, plan["sub_questions"])
        ])

        return {
            "raw_data": search_results,
            "analyses": analyses
        }
```

**3. Reflexion 层 — 质量检查**
```python
class ResearchReflector:
    def check_quality(self, research_result: dict, original_question: str):
        prompt = f"""评估研究质量:

原问题: {original_question}
研究发现: {research_result['analyses']}

评分 (1-10):
- 信息覆盖度: ?
- 数据准确性: ?
- 分析深度: ?
- 是否有遗漏？

如果总分 < 7，列出需要补充研究的方面。"""
        return self.llm.generate(prompt)
```

**4. Synthesizer（综合器）— 报告生成**
```python
class ReportSynthesizer:
    def synthesize(self, analyses: list, structure: list, question: str):
        # 按报告结构逐章生成
        report = {}
        for section in structure:
            relevant = self._filter_relevant(analyses, section)
            report[section] = self.llm.generate(
                f"章节: {section}\n相关分析: {relevant}\n写这一章:"
            )

        # 生成摘要
        report["summary"] = self.llm.generate(
            f"总结以下报告:\n{json.dumps(report, ensure_ascii=False)}"
        )
        return report
```

#### 关键设计决策

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 推理策略 | Plan-and-Execute + Reflexion | 研究任务步骤明确但可能失败 |
| 并行度 | 搜索/分析阶段并行 | 子问题独立，可并行 |
| 质量控制 | Reflexion 评分 + 补充研究 | 确保覆盖度 |
| 上下文管理 | 研究结果外部化到向量DB | 避免上下文溢出 |
| 成本控制 | 搜索用小模型，综合用大模型 | 模型路由 |

#### 面试讨论点

1. **如何处理搜索结果矛盾？** → 辩论模式或标注分歧
2. **如何确保时效性？** → 优先用最近来源、标注日期
3. **如何评估报告质量？** → 人工评估 + 自动评分（覆盖度/准确性/深度）
4. **成本估算** → 约 $2-5 per 研究报告（10-20 次 LLM 调用）

</details>

---

## 三、当日小结

### 核心知识点回顾

| # | 知识点 | 一句话总结 | 重要程度 |
|---|--------|-----------|---------|
| 1 | CoT | 逐步推理，分解复杂问题，分配更多计算 | ⭐⭐⭐⭐⭐ |
| 2 | ToT | 树形搜索推理，多路探索+剪枝，代价更高 | ⭐⭐⭐⭐ |
| 3 | GoT | 图结构推理，支持分支合并 | ⭐⭐⭐ |
| 4 | PoT | 生成代码执行推理，数值计算零误差 | ⭐⭐⭐ |
| 5 | Plan-and-Execute | 先全局规划再逐步执行，Token 效率高 | ⭐⭐⭐⭐⭐ |
| 6 | Reflexion | 失败后自我反思，存入记忆避免重复错误 | ⭐⭐⭐⭐ |
| 7 | 前向 vs 逆向规划 | 前向从现状出发，逆向从目标倒推 | ⭐⭐⭐⭐ |
| 8 | 多 Agent 协作 | 层级/顺序/并行/辩论/竞争五种模式 | ⭐⭐⭐⭐ |
| 9 | 规划失败恢复 | 重试→微调→局部重规划→全局重规划→降级 | ⭐⭐⭐⭐⭐ |
| 10 | 策略路由 | 根据任务复杂度自动选择推理范式 | ⭐⭐⭐⭐ |

### 面试速记卡

| 卡片 | 正面 | 背面 |
|------|------|------|
| 卡1 | CoT 为什么有效？ | ①分解问题 ②分配更多计算 ③减少跳步错误 ④可调试 |
| 卡2 | ToT 的四步？ | 思维分解 → 思维生成 → 状态评估 → 搜索(剪枝) |
| 卡3 | Plan-Execute vs ReAct？ | P&E 先规划再执行(Token高效)，ReAct 每步即时决策(灵活) |
| 卡4 | Reflexion 循环？ | 执行→失败→反思→存记忆→重试(带反思) |
| 卡5 | 前向 vs 逆向规划？ | 前向"现在能做什么"，逆向"达到目标需要什么" |
| 卡6 | 多Agent协作五模式？ | 层级/顺序管道/并行/辩论/竞争 |
| 卡7 | 规划恢复五层级？ | 重试 → 微调步骤 → 局部重规划 → 全局重规划 → 降级人工 |
| 卡8 | PoT 适合什么？ | 数值计算/逻辑推理 — LLM生成代码，解释器执行，零算术错误 |

### 易错点提醒

| # | 易错点 | 正确理解 |
|---|--------|---------|
| 1 | "CoT 总是有益" | ❌ 简单任务上 CoT 可能降低性能（过度思考） |
| 2 | "ToT 一定比 CoT 好" | ❌ ToT 代价高，简单问题不值得树搜索 |
| 3 | "规划越详细越好" | ❌ 过度规划脆弱，第一步偏离则全盘崩溃 |
| 4 | "Reflexion = 重试" | ❌ Reflexion 是带反思的重试，不是简单重试 |
| 5 | "多Agent一定比单Agent好" | ❌ 多Agent增加协调成本，简单任务单Agent更优 |
| 6 | "前向规划和逆向规划是对立的" | ❌ 实际系统常混合使用：逆向定里程碑+前向填步骤 |
| 7 | "GoT 就是 ToT" | ❌ GoT 支持分支合并（图），ToT 只有树形展开 |
| 8 | "规划失败就应该完全重来" | ❌ 应分级恢复，尽量复用已完成步骤 |

### 自测检查清单

- [ ] 能解释 CoT 有效的原因和适用边界
- [ ] 能画出 ToT 的搜索流程并说明剪枝机制
- [ ] 能对比 Plan-and-Execute 和 ReAct 的优劣
- [ ] 能写出 Reflexion 循环的伪代码
- [ ] 能区分前向规划和逆向规划的适用场景
- [ ] 能列出多 Agent 协作的五种模式并各举一例
- [ ] 能描述规划恢复的五级策略
- [ ] 能解释 PoT 为什么在数值推理上优于 CoT
- [ ] 能设计一个根据任务复杂度自动选择策略的路由器
- [ ] 能讨论推理范式选择的成本-准确率权衡

### 延伸阅读

| 资源 | 类型 | 价值 |
|------|------|------|
| [Chain-of-Thought Prompting (Wei et al.)](https://arxiv.org/abs/2201.11903) | 论文 | CoT 原始论文 |
| [Tree of Thoughts (Yao et al.)](https://arxiv.org/abs/2305.10601) | 论文 | ToT 框架 |
| [Graph of Thoughts](https://arxiv.org/abs/2308.09687) | 论文 | GoT 图结构推理 |
| [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) | 论文 | Reflexion 机制 |
| [Plan-and-Execute Agents (LangChain)](https://blog.langchain.dev/plan-and-execute-agents/) | 博客 | 工程实现视角 |

---

## 四、明日预告

> **Day 07** 将进行 **Week 1 回顾与手撕代码特训**，包括：
> - Day1-6 核心知识点串联与知识图谱
> - 高频手撕代码题（Agent Loop / ReAct / 记忆系统 / 工具调用）
> - Week 1 模拟面试（10 道综合题）
> - 易错点总复习
> - Week 2 预告（RAG 与 Agent 结合）
