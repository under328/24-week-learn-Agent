# Day 17 — Multi-Agent 协作架构

> **学习目标**: 深入理解 Multi-Agent 协作的五大模式、通信机制、角色设计与挑战;能手撕一个 Supervisor + 专家 Agent 的协作系统;能完成"软件开发 Multi-Agent 系统"的端到端设计。
>
> **面试定位**: 大厂 Agent 岗高频考点。考察点集中在"什么时候用 Multi-Agent"、"如何避免协作失控"、"如何控制成本与延迟"、"MetaGPT/AutoGen/CrewAI/LangGraph 的协作机制差异"。回答时务必结合真实落地经验,而不是泛泛而谈"分工合作"。
>
> **前置知识**: Day15 的 LangChain/LangGraph 基础、Day16 的框架横评(尤其是 LangGraph 的图模型与 CrewAI 的角色模型)。
>
> **建议学习时长**: 6-8 小时(其中手撕代码 2 小时、系统设计 2 小时)。

---

## 今日知识图谱

```
Multi-Agent 协作架构
│
├── 1. 协作模式 (Topology)
│   ├── Hierarchical 层级式
│   │   ├── Supervisor / Orchestrator 模式 (主从调度)
│   │   └── Manager-Worker 模式 (任务分发)
│   ├── Sequential 串行式 (Pipeline 流水线)
│   │   └── 代表: CrewAI 的 process="sequential"
│   ├── Parallel 并行式 (Map-Reduce)
│   │   └── 代表: 同一任务分片多 Agent 处理后聚合
│   ├── Debate 辩论式 (Adversarial)
│   │   └── 代表: Multi-Agent Debate 提升推理质量
│   └── Network 网络式 (Peer-to-Peer)
│       └── 代表: AutoGen GroupChat、AgentVerse
│
├── 2. 通信机制 (Communication)
│   ├── 直接调用 (Function Call / RPC)
│   ├── 消息队列 (Async Message Passing)
│   ├── 黑板模式 (Blackboard / Shared Memory)
│   └── 共享状态 (Shared State / Shared Scratchpad)
│
├── 3. 主流框架协作机制
│   ├── LangGraph: 图模型 (StateGraph + Edges + Reducer)
│   ├── AutoGen: GroupChat + Speaker Selection
│   ├── CrewAI: Role + Task + Crew (SOP 内嵌)
│   ├── MetaGPT: SOP + Environment + Message
│   └── CAMEL: Role-Playing Inception Prompting
│
├── 4. 角色设计 (Role Engineering)
│   ├── 角色定义 (Profile / Persona)
│   ├── 能力边界 (Capability Boundary)
│   ├── 冲突处理 (Conflict Resolution)
│   └── 终止条件 (Termination Criteria)
│
├── 5. 核心挑战 (Challenges)
│   ├── 一致性 (Consistency / Hallucination Drift)
│   ├── 死锁 (Deadlock / Infinite Loop)
│   ├── 成本控制 (Token / Latency / API 费用)
│   ├── 调试困难 (Trace / Replay / Attribution)
│   └── 级联失败 (Cascading Failure / Error Propagation)
│
└── 6. 工程实践 (Engineering)
    ├── 任务分解 (Task Decomposition)
    ├── 结果聚合 (Result Aggregation)
    ├── 状态管理 (State Management / Checkpoint)
    └── 可观测性 (Tracing / Metrics / Logging)
```

---

## 面试题(共 10 道)

> **使用方式**: 先合上答案自己口述一遍,再展开对照。每道题标注了【高频】/【中频】/【手撕】/【系统设计】标签,代表面试出现概率。

### Q1 【高频】为什么需要 Multi-Agent? 单 Agent 的局限性是什么? Multi-Agent 又带来哪些新优势?

<details>
<summary>点击查看参考答案</summary>

**单 Agent 的四大局限性**:

1. **Context 膨胀与注意力稀释**: 单 Agent 把所有工具描述、历史对话、知识库全部塞进一个 Context Window。工具超过 20 个时,LLM 选择正确工具的准确率显著下降(参考 ToolLLM 论文的"工具数量-准确率"曲线)。同时,长对话历史会让注意力被稀释到无关内容上。
2. **角色冲突与 Prompt 撕扯**: 一个 Prompt 同时扮演"严谨的代码审查者"和"富有创意的需求分析师"会导致行为漂移——LLM 会在这两种风格间反复横跳,输出不稳定。这就是 Prompt Engineering 里著名的 "role conflict"。
3. **不可扩展的决策树**: 单 Agent 的 ReAct 循环在任务复杂度上升时,需要越来越长的思维链,容易陷入"思考死循环"或"过早收敛到错误路径"。研究表明,单 Agent 在超过 5-6 步推理后,错误率呈指数上升。
4. **缺乏专业分工**: 单 Agent 是"通才",无法针对子任务使用不同的模型/温度/工具集。比如代码生成用 DeepSeek-Coder、推理用 GPT-4o、文档润色用 Claude,单 Agent 难以灵活切换。

**Multi-Agent 的五大优势**:

| 优势 | 说明 | 典型场景 |
|------|------|----------|
| 关注点分离 (SoC) | 每个 Agent 只看自己角色相关的 Context,降低注意力负担 | 软件开发流水线 |
| 模型异构 (Model Heterogeneity) | 不同 Agent 用不同模型,成本与质量平衡 | 推理用 GPT-4o、编码用 Codestral |
| 并行加速 (Parallelism) | 独立子任务并行执行,降低端到端延迟 | 多文档摘要、批量代码审查 |
| 容错隔离 (Fault Isolation) | 单个 Agent 失败可重试,不影响整体流程 | Web 搜索 Agent 网络抖动重试 |
| 可观测性增强 | 每个 Agent 的输入输出独立可追溯,debug 更容易 | 复杂任务归因分析 |

**关键回答要点(面试加分项)**:

- **不要无脑用 Multi-Agent**: 当任务能在 1-2 步 ReAct 内完成、或工具数 < 10 时,单 Agent 更简单、更便宜。Multi-Agent 的协调开销(消息序列化、状态同步、Agent 间往返)可能抵消分工收益。
- **量化收益**: 一个常见经验值是——当单 Agent 的 Context 超过 16K tokens、工具超过 15 个、或需要 > 8 步推理时,才考虑拆分为 Multi-Agent。
- **真实案例**: 微软 AutoGen 的论文里举了一个例子——单 GPT-4 写一个简单游戏的成功率约 60%,而用 "Coder + Reviewer" 双 Agent 协作可提升到 85%+;但用 5+ 个 Agent 时反而下降到 70%(过度协作导致信息丢失)。

**追问应对**: "那为什么 ChatGPT/Claude 单 Agent 也能做很多复杂任务?" —— 答:它们通过 **内部工具路由 + 子任务隐式分解 + 长 Context 优化** 模拟了部分 Multi-Agent 行为,本质上是"单进程多协程",而 Multi-Agent 是"多进程",各有取舍。

</details>

---

### Q2 【高频】Multi-Agent 的五大协作模式是什么? 各自的适用场景和典型实现?

<details>
<summary>点击查看参考答案</summary>

**五大协作模式速查表**:

| 模式 | 拓扑 | 控制流 | 通信开销 | 适用场景 | 典型实现 |
|------|------|--------|----------|----------|----------|
| Hierarchical 层级式 | 树 | 自上而下 | 低 | 任务可清晰分解、有明确主从 | LangGraph Supervisor、CrewAI hierarchical |
| Sequential 串行式 | 链 | 单向流动 | 极低 | 流水线任务、阶段不可并行 | CrewAI sequential、LangChain LCEL |
| Parallel 并行式 | 扇出扇入 | 一次分发一次聚合 | 中 | 同质任务分片、Map-Reduce | LangGraph Send API、多 Agent 摘要 |
| Debate 辩论式 | 全互联 | 多轮交互 | 高 | 需要校验推理、减少幻觉 | Multi-Agent Debate、CAMEL |
| Network 网络式 | 图 | 动态路由 | 高 | 开放式探索、复杂依赖 | AutoGen GroupChat、AgentVerse |

**详细分析**:

**1. Hierarchical 层级式 (Supervisor / Orchestrator)**
- 结构: 一个 Supervisor Agent 接收用户请求,分解为子任务,分发给多个 Worker Agent,Worker 完成后回报 Supervisor,Supervisor 聚合结果。
- 优点: 控制流清晰、易调试、易扩展 Worker。
- 缺点: Supervisor 是单点瓶颈,任务分解质量决定整体上限。
- 适用: 客服系统(路由 Agent + 多领域专家 Agent)、软件开发(PM + 工程师 + 测试)、数据分析(规划 Agent + 取数 Agent + 可视化 Agent)。
- LangGraph 实现: Supervisor 作为图的入口节点,根据状态路由到不同 Worker 节点,Worker 返回后 Supervisor 决定下一步。

**2. Sequential 串行式 (Pipeline)**
- 结构: Agent A → Agent B → Agent C,前一个的输出是后一个的输入。
- 优点: 实现简单、可追溯、无并发问题。
- 缺点: 无并行、单点失败、无法反馈回环。
- 适用: 内容生产(选题 → 写作 → 校对 → 排版)、数据处理(采集 → 清洗 → 分析 → 可视化)。
- CrewAI 实现: `Crew(process=Process.sequential)`,Task 按 `expected_output` 顺序串联,前一个 Task 的输出自动注入下一个 Agent 的 context。

**3. Parallel 并行式 (Map-Reduce)**
- 结构: 一个 Fan-out 节点把任务分成 N 份,N 个 Agent 并行处理,Fan-in 节点聚合结果。
- 优点: 延迟低(取最慢 Agent 时间)、吞吐高。
- 缺点: 子任务必须相互独立,聚合逻辑复杂。
- 适用: 多文档摘要(N 篇文档分别摘要再汇总)、批量代码审查(N 个 PR 并行 review)、多视角分析(财务/技术/法律三视角并行)。
- LangGraph 实现: 使用 `Send` API 在节点返回时动态生成多个目标节点调用,Reducer 函数负责聚合。

**4. Debate 辩论式 (Adversarial)**
- 结构: 多个 Agent 持不同立场,多轮交替发言,最后由 Judge Agent 综合裁决。
- 优点: 显著降低幻觉(错误观点会被对手反驳)、推理更鲁棒。
- 缺点: Token 成本高(多轮交互)、容易陷入"礼貌性同意"或"无意义纠缠"。
- 适用: 数学推理、科学假设验证、安全审查(红蓝对抗)。
- 论文依据: Du et al. 2023 "Improving Factuality and Reasoning in Language Models through Multiagent Debate" 证明两轮 Debate 可让 GPT-4 在数学推理上的准确率从 53% 提升到 87%。

**5. Network 网络式 (Peer-to-Peer / GroupChat)**
- 结构: 多个 Agent 处于同一"群聊"环境,由 Speaker Selection 机制决定下一个发言者,发言内容对所有 Agent 可见。
- 优点: 灵活、能涌现复杂协作行为、适合开放式任务。
- 缺点: 通信成本随 Agent 数量平方增长、难以预测终止、调试困难。
- 适用: 头脑风暴、复杂问题探索、模拟社会(如斯坦福 Smallville)。
- AutoGen 实现: `GroupChat(agents=[...], speaker_selection_method="auto")`,由 LLM 校据当前对话历史动态选择下一个发言者。

**面试加分回答**:

> "实际工程中很少用单一模式,而是组合使用。比如软件开发系统:外层是 Hierarchical(Supervisor 调度),内部是 Sequential(需求→设计→编码→测试),某些阶段(如多模块并行编码)用 Parallel,代码审查环节用 Debate(Coder vs Reviewer)。这种'分层混合'是工业级 Multi-Agent 系统的常见形态。"

</details>

---

### Q3 【高频】详细讲讲 Supervisor 模式。如何做任务分解和结果聚合? 有哪些坑?

<details>
<summary>点击查看参考答案</summary>

**Supervisor 模式的核心思想**: 一个"主控 Agent"作为大脑,负责理解用户意图、分解任务、调度子 Agent、聚合结果、决定终止。子 Agent 是"执行器官",只关心自己领域内的子任务。

**架构图**:

```
                    ┌─────────────────┐
   User Query ───►  │   Supervisor    │
                    │   (Orchestrator)│
                    └────────┬────────┘
                             │ decompose
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
       ┌─────────┐      ┌─────────┐      ┌─────────┐
       │ Agent A │      │ Agent B │      │ Agent C │
       │ (搜索)  │      │ (计算)  │      │ (写作)  │
       └────┬────┘      └────┬────┘      └────┬────┘
            │                │                │
            └────────────────┼────────────────┘
                             │ results
                             ▼
                    ┌─────────────────┐
                    │   Supervisor    │
                    │   (Aggregator)  │
                    └────────┬────────┘
                             ▼
                       Final Answer
```

**任务分解的三种策略**:

1. **LLM 驱动分解 (Prompt-based)**: 让 Supervisor LLM 输出结构化的子任务列表(JSON)。灵活但不可控,可能分解出子 Agent 无法处理的任务。
2. **模板分解 (Template-based)**: 针对特定任务类型预设分解模板,如"研究报告"固定拆为"资料搜集 + 数据分析 + 撰写"。可控但泛化弱。
3. **混合分解 (Hybrid)**: LLM 在模板约束下分解,既保留灵活性又保证子任务可执行。这是工业界主流做法。

**结果聚合的三种策略**:

1. **拼接式 (Concatenation)**: 直接按顺序拼接子结果,适合相互独立的子任务(如多文档摘要)。
2. **总结式 (Summarization)**: Supervisor LLM 把多个子结果总结成最终答案,适合子结果有重叠或矛盾(如多源搜索)。
3. **投票式 (Voting)**: 多个 Agent 给出多个答案,Supervisor 选多数或最佳,适合需要高可靠性的场景(如代码审查)。

**关键代码骨架(LangGraph 风格)**:

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
import operator

class AgentState(TypedDict):
    query: str
    subtasks: list[dict]
    results: Annotated[list[str], operator.add]
    final_answer: str

def supervisor_decompose(state: AgentState) -> AgentState:
    """Supervisor 把用户查询分解为子任务列表"""
    prompt = f"""你是一个任务调度器。把以下用户请求分解为最多3个子任务,
    每个子任务标注应该由哪个 Agent 处理 (searcher/calculator/writer)。
    输出 JSON 列表: [{{"agent": "searcher", "task": "..."}}]
    用户请求: {state['query']}"""
    subtasks = call_llm(prompt, response_format="json")
    return {"subtasks": subtasks}

def route_to_workers(state: AgentState) -> list[Send]:
    """把每个子任务路由到对应 Worker Agent (并行)"""
    return [Send(item["agent"], {"task": item["task"]}) for item in state["subtasks"]]

def searcher(state): return {"results": [web_search(state["task"])]}
def calculator(state): return {"results": [eval_expr(state["task"])]}
def writer(state): return {"results": [draft(state["task"])]}

def supervisor_aggregate(state: AgentState) -> AgentState:
    """Supervisor 聚合所有子结果"""
    prompt = f"基于以下子结果回答用户原始问题:\n查询: {state['query']}\n子结果: {state['results']}"
    return {"final_answer": call_llm(prompt)}

graph = StateGraph(AgentState)
graph.add_node("supervisor_decompose", supervisor_decompose)
graph.add_node("searcher", searcher)
graph.add_node("calculator", calculator)
graph.add_node("writer", writer)
graph.add_node("supervisor_aggregate", supervisor_aggregate)
graph.add_edge(START, "supervisor_decompose")
graph.add_conditional_edges("supervisor_decompose", route_to_workers, ["searcher","calculator","writer"])
for w in ["searcher","calculator","writer"]:
    graph.add_edge(w, "supervisor_aggregate")
graph.add_edge("supervisor_aggregate", END)
app = graph.compile()
```

**五大典型坑**:

1. **分解粒度过细**: Supervisor 把任务拆成 10+ 个子任务,每个子任务都需要一轮 LLM 调用,延迟和成本爆炸。经验值:子任务数控制在 2-4 个。
2. **子任务依赖未识别**: Supervisor 把"先查 A 再用 A 的结果查 B"误判为并行任务,导致 B 拿不到 A 的结果。解决:让 Supervisor 显式标注子任务间的依赖关系(DAG),而非简单列表。
3. **聚合时 Context 超长**: 5 个子 Agent 各返回 2K tokens,聚合时 Supervisor Context 10K+,聚合质量下降。解决:子 Agent 返回前先做摘要,或分批聚合。
4. **Supervisor 单点故障**: Supervisor 是 LLM,可能分解错误或聚合错误,且无重试。解决:对 Supervisor 输出做 JSON Schema 校验,失败则重试;关键决策用"双 Supervisor 投票"。
5. **无终止条件导致死循环**: Supervisor 判断"子结果不完整"反复重派任务,陷入死循环。解决:设置最大轮次(如 max_iterations=3)和"满意阈值"(LLM 评分 > 7/10 即停止)。

**追问应对**: "Supervisor 自己也是 LLM,会不会'将帅无能累死三军'?" —— 会。所以工业界常做两件事:(1) 用强模型(GPT-4o / Claude Opus)做 Supervisor,弱模型做 Worker,降低成本;(2) 对 Supervisor 的分解结果做规则校验(如子任务必须落在已注册 Agent 能力范围内),不合规则用规则兜底而非盲信 LLM。

</details>

---

### Q4 【中频】Agent 间通信协议有哪些? 直接调用 / 消息队列 / 黑板模式 / 共享状态 各有什么特点?

<details>
<summary>点击查看参考答案</summary>

**四种通信机制对比表**:

| 机制 | 耦合度 | 时序 | 状态管理 | 可扩展性 | 典型框架 |
|------|--------|------|----------|----------|----------|
| 直接调用 (RPC/Function Call) | 高 | 同步 | 无状态 | 弱 | LangChain Tool、CrewAI Task |
| 消息队列 (Message Queue) | 低 | 异步 | 持久化 | 强 | AutoGen(部分)、自定义 Kafka |
| 黑板模式 (Blackboard) | 中 | 解耦 | 集中存储 | 中 | AgentVerse、经典 AI |
| 共享状态 (Shared State) | 中 | 同步/异步 | 集中 + 增量 | 中 | LangGraph StateGraph |

**1. 直接调用 (Direct Invocation)**

Agent A 直接调用 Agent B 的接口(类似函数调用),A 阻塞等待 B 返回。

- 优点: 实现简单、调用栈清晰、易于调试。
- 缺点: 强耦合(A 必须知道 B 的存在和接口)、同步阻塞、难扩展(新增 Agent 需改 A)。
- 适用: Agent 数量少(2-3 个)、调用关系固定、对延迟敏感的场景。
- 代码示例:

```python
class ResearchAgent:
    def __init__(self, writer: WriterAgent):
        self.writer = writer  # 强依赖
    def run(self, topic):
        facts = self.collect(topic)
        return self.writer.run(facts)  # 同步阻塞调用
```

**2. 消息队列 (Message Queue / Pub-Sub)**

Agent 之间通过队列传递消息,生产者发布消息后不等待消费者,消费者异步处理。

- 优点: 解耦、异步、削峰填谷、易扩展(新 Agent 订阅即可)。
- 缺点: 调试复杂(消息流向难追踪)、需处理消息丢失/重复/乱序、最终一致性。
- 适用: Agent 数量多(10+)、长任务(分钟级)、跨进程/跨机器部署。
- 代码示例:

```python
import asyncio
class MessageBus:
    def __init__(self):
        self.subscribers: dict[str, list] = {}
    def subscribe(self, topic, handler):
        self.subscribers.setdefault(topic, []).append(handler)
    async def publish(self, topic, message):
        for handler in self.subscribers.get(topic, []):
            asyncio.create_task(handler(message))  # 异步分发

bus = MessageBus()
async def search_agent(msg): ...
async def writer_agent(msg): ...
bus.subscribe("search_done", writer_agent)
await bus.publish("search_done", {"facts": [...]})
```

**3. 黑板模式 (Blackboard)**

所有 Agent 共享一块"黑板"(数据结构),Agent 各自读黑板上的信息、写入自己的产出,互不直接通信。

- 优点: 极度解耦、Agent 之间无需知道彼此、易增加新 Agent。
- 缺点: 黑板可能膨胀、需并发控制(锁)、Agent 何时触发执行难定义(需"控制器"或"触发规则")。
- 适用: 知识工程、复杂问题逐步求解(经典 AI 黑板架构)、Agent 数量动态变化。
- 代码示例:

```python
class Blackboard:
    def __init__(self):
        self.data: dict = {}
        self.lock = threading.Lock()
    def read(self, key): return self.data.get(key)
    def write(self, key, value):
        with self.lock:
            self.data[key] = value

bb = Blackboard()
def searcher(bb):
    bb.write("facts", web_search())
def writer(bb):
    while not bb.read("facts"):  # 轮询等待
        time.sleep(0.1)
    draft(bb.read("facts"))
```

**4. 共享状态 (Shared State)**

LangGraph 的标志性机制。所有 Agent 共享一个 `TypedDict` 状态对象,每个 Agent 是一个节点,读取并修改状态,图引擎负责调度和状态合并。

- 优点: 状态显式可见、Reducer 可定义合并策略(如 list 用 `operator.add` 累加)、易做 Checkpoint 和回放。
- 缺点: 状态结构需预先定义(强 schema)、并发更新需 Reducer 处理冲突。
- 适用: LangGraph 生态、需要状态持久化和人机交互(checkpoint + resume)的场景。
- 代码示例:

```python
from typing import TypedDict, Annotated
import operator
class State(TypedDict):
    messages: Annotated[list, operator.add]  # Reducer: 列表拼接
    facts: str
    draft: str

def searcher(state): return {"facts": search(state["messages"][-1])}
def writer(state): return {"draft": write(state["facts"])}
```

**面试加分点**:

> "通信机制的选择本质是'耦合度 vs 灵活性'的权衡。工业实践中,大多数 Multi-Agent 系统用'共享状态 + 少量直接调用'的混合模式——LangGraph 的 StateGraph 就是典型。只有当 Agent 跨进程/跨机器、或需要异步长任务时,才引入消息队列。黑板模式更多见于学术研究,工业落地少。"

**追问应对**: "为什么 LangGraph 选共享状态而不是消息队列?" —— 答: LangGraph 的核心价值是"可持久化、可回放、可人机交互",共享状态天然支持 Checkpoint(序列化整个 State);消息队列的异步语义会让状态散落在多条消息里,checkpoint 困难。LangGraph 用"同步图执行 + 共享状态"换来可调试性,牺牲了横向扩展性(但可通过分布式 Checkpointer 缓解)。

</details>

---

### Q5 【中频】MetaGPT 的 SOP(Standard Operating Procedure)理念是什么? 它如何用软件工程流程组织 Agent?

<details>
<summary>点击查看参考答案</summary>

**SOP 的核心思想**: MetaGPT 论文(2023, Hong et al.)提出——把人类组织的"标准作业流程"显式编码到 Multi-Agent 系统中,让 Agent 像一个软件公司里的不同角色那样协作,而不是自由对话。

**核心论点**: 早期 Multi-Agent(如 AutoGen、CAMEL)让 Agent 自由对话,容易出现"无意义寒暄""重复确认""话题漂移"。SOP 通过预定义角色、流程、产出物(artifact),把协作约束在"结构化流水线"内,显著降低无效交互。

**MetaGPT 模拟的软件公司 SOP**:

```
用户需求 (PRD 输入)
        │
        ▼
┌─────────────────┐
│  Product Manager │  产出: PRD 文档(结构化)
└────────┬────────┘
         ▼
┌─────────────────┐
│   Architect     │  产出: 系统设计、接口定义、数据结构
└────────┬────────┘
         ▼
┌─────────────────┐
│ Project Manager  │  产出: 任务分解、分配
└────────┬────────┘
         ▼
┌─────────────────┐
│   Engineer(s)   │  产出: 代码实现
└────────┬────────┘
         ▼
┌─────────────────┐
│      QA         │  产出: 测试用例、Bug 报告
└────────┬────────┘
         ▼
   可交付软件
```

**SOP 的三个关键机制**:

**1. 结构化产出物 (Structured Artifacts)**
每个角色的输出不是自由文本,而是有严格 Schema 的文档(如 PRD 必须包含 Original Requirements、Product Goals、User Stories、Competitive Analysis 等字段)。下游 Agent 解析上游的 JSON/Markdown 文档,而非依赖自然语言理解。这大幅减少信息丢失和幻觉。

**2. 显式流程 (Explicit Procedure)**
角色之间的流转不是 LLM 自由决定,而是预定义的 Directed Graph。PM 完成后必然到 Architect,Architect 完成后必然到 Engineer。流程的"刚性"换来可预测性。

**3. 共享环境 (Shared Environment)**
所有 Agent 通过一个 `Environment` 对象共享消息和文档。每个 Agent 发布的产出物会广播给所有相关 Agent,但每个 Agent 根据 Role 决定是否读取。这是"黑板模式 + 角色过滤"的混合。

**MetaGPT 的核心抽象**:

```python
# MetaGPT 简化版核心抽象
class Role:
    def __init__(self, name, profile, goal, constraints):
        self.name = name
        self.profile = profile  # 角色画像
        self.goal = goal
        self.constraints = constraints
        self.actions = []  # 该角色能执行的动作
    async def run(self, environment):
        # 监听环境消息,执行自己的 action,产出新消息
        ...

class Action:
    def __init__(self, name, instruction, output_schema):
        self.instruction = instruction  # Prompt 模板
        self.output_schema = output_schema  # 结构化输出 Schema
    async def run(self, context):
        return call_llm(self.instruction + context, response_format=self.output_schema)

class Environment:
    def __init__(self):
        self.members: list[Role] = []
        self.history: list[Message] = []
    def publish(self, message: Message):
        self.history.append(message)
    async def run(self, rounds: int = 3):
        for _ in range(rounds):
            for role in self.members:
                await role.run(self)  # 每个角色按 SOP 顺序执行
```

**MetaGPT 的两种协作模式**:

| 模式 | 描述 | 适用 |
|------|------|------|
| Standard Operating Procedure | 预定义角色和流程,Agent 按 SOP 顺序执行 | 重复性高的任务(如软件开发) |
| Debate / Discussion | Agent 自由讨论,通过多轮交互达成共识 | 开放式探索 |

**SOP 的优势与局限**:

优势:
- 显著减少无效交互(Token 成本降低 30-50%)。
- 流程可预测、易调试、易复现。
- 结构化产出物可作为下游程序的输入(可执行性)。

局限:
- SOP 设计需要领域专家,泛化弱(换一个任务就要重新设计 SOP)。
- 流程刚性,难以处理"非标准"任务(如用户突然改需求)。
- 对 LLM 输出结构化的能力要求高(早期模型 JSON 输出不稳定)。

**与其他框架对比**:

- **vs AutoGen**: AutoGen 强调"自由对话",SOP 隐式涌现;MetaGPT 强调"显式 SOP",流程刚性。前者灵活,后者可控。
- **vs CrewAI**: CrewAI 的 Role + Task + Process 也借鉴了 SOP 思想,但更轻量,无结构化产出物的强约束。
- **vs LangGraph**: LangGraph 把"流程定义"交给开发者用图建模,灵活性最高但工作量大;MetaGPT 把"流程"内化为框架预设,开发者只需定义角色。

**面试加分回答**:

> "MetaGPT 的 SOP 思想本质是'用工程约束弥补 LLM 协作的不可靠性'。这与软件工程的'流程规范'一脉相承——人也需要 SOP 来保证协作质量,何况是 LLM。但 SOP 的代价是泛化性差,所以最新研究(如 MetaGPT v2、AgentVerse)在探索'自适应 SOP'——让 LLM 根据任务动态生成 SOP,再按 SOP 执行。这是'结构化与灵活性'的新平衡。"

</details>

---

### Q6 【高频】AutoGen 的 GroupChat 机制是如何工作的? Speaker Selection 有哪几种策略?

<details>
<summary>点击查看参考答案</summary>

**GroupChat 核心思想**: AutoGen(微软)把多个 Agent 放入一个"群聊"环境,所有 Agent 共享同一份对话历史,由一个"Manager Agent"(或规则)决定下一个发言者。Agent 通过自然语言交互,直到满足终止条件。

**GroupChat 架构**:

```
┌────────────────────────────────────────────────┐
│                GroupChat Manager               │
│  (选择下一个发言者,维护对话历史,判断终止)        │
└────────────────────┬───────────────────────────┘
                     │
   ┌─────────────────┼─────────────────┐
   ▼                 ▼                 ▼
┌─────────┐    ┌─────────┐      ┌─────────┐
│ Agent A │    │ Agent B │      │ Agent C │
│ (Coder) │    │(Tester)│      │(Reviewer)│
└─────────┘    └─────────┘      └─────────┘
   │                │                 │
   └────────────────┼─────────────────┘
                    │
              共享对话历史
```

**GroupChat 的关键参数**:

```python
from autogen import GroupChat, GroupChatManager

groupchat = GroupChat(
    agents=[coder, tester, reviewer],
    messages=[],
    max_round=20,                    # 最大轮次(防死循环)
    speaker_selection_method="auto", # 发言者选择策略
    allow_repeat_speaker=False,      # 是否允许同一 Agent 连续发言
)
manager = GroupChatManager(groupchat=groupchat)
user.initiate_chat(manager, message="写一个贪吃蛇游戏")
```

**Speaker Selection 的四种策略**:

| 策略 | 机制 | 优点 | 缺点 |
|------|------|------|------|
| `"auto"` (默认) | LLM 根据对话历史和各 Agent 的 system prompt 决定 | 灵活、智能 | 一次额外 LLM 调用(成本)、可能选错 |
| `"manual"` | 每轮暂停,人工选择下一个发言者 | 完全可控 | 无法自动化、不适合生产 |
| `"random"` | 随机选择 | 无成本、可作 baseline | 协作无意义 |
| `"round_robin"` | 按 agents 列表顺序轮流 | 简单、可预测 | 不考虑上下文,可能选不合适的 Agent |
| 自定义函数 | 传入 `speaker_selection_method=callable` | 完全可控、可注入业务规则 | 需自己实现逻辑 |

**自定义 Speaker Selection 示例**:

```python
def custom_speaker_selection(last_speaker, groupchat):
    """规则:Reviewer 发言后必须回到 Coder 修改"""
    history = groupchat.messages
    if last_speaker is reviewer and "bug" in history[-1]["content"].lower():
        return coder
    if last_speaker is coder:
        return tester  # Coder 写完先让 Tester 测
    return None  # None 表示让 Manager 自动选

groupchat = GroupChat(
    agents=[coder, tester, reviewer],
    speaker_selection_method=custom_speaker_selection,
    max_round=15,
)
```

**GroupChat 的终止机制**:

1. **max_round**: 硬上限,达到轮次即停(防死循环,必设)。
2. **Agent 主动终止**: 某个 Agent 的回复中包含 "TERMINATE" 字样,Manager 检测到后结束。
3. **is_termination_msg**: 自定义函数判断某条消息是否应终止。

```python
def is_termination_msg(msg):
    content = msg.get("content", "")
    return content.endswith("APPROVED") or "TERMINATE" in content
```

**GroupChat 的两大经典模式**:

**模式一: 任务完成型 (Task-Oriented)**
- Coder 写代码 → Tester 写测试 → Reviewer 审查 → Coder 修复 → ... → APPROVED
- 适合软件开发、文档撰写等有明确"完成态"的任务。

**模式二: 探索讨论型 (Exploratory)**
- 多个 Agent 持不同视角讨论,Manager 总结。
- 适合头脑风暴、方案评估。

**GroupChat 的常见问题与解决**:

| 问题 | 现象 | 解决 |
|------|------|------|
| 死循环 | 两个 Agent 互相"好的""好的" | 设 max_round、禁 allow_repeat_speaker |
| 一个人霸权 | 某个 Agent 一直发言 | speaker_selection 加权随机、设每个 Agent 最大发言次数 |
| 上下文爆炸 | 对话历史过长,Token 超限 | 用 `clear_history`、或 Manager 做摘要压缩 |
| 选错发言者 | LLM 选了不相关的 Agent | 用自定义 speaker_selection 注入业务规则 |
| 静默 Agent | 某个 Agent 从不发言 | 在 system prompt 中明确"何时该你发言"的触发条件 |

**vs MetaGPT 的关键区别**:

- AutoGen GroupChat 是"自由对话 + 发言者选择",流程是涌现的。
- MetaGPT 是"预设 SOP + 角色顺序",流程是确定的。
- AutoGen 更灵活但更不可控;MetaGPT 更可控但更不灵活。
- 实践经验: 软件开发等"有标准流程"的任务用 MetaGPT 风格;头脑风暴等"开放探索"用 AutoGen GroupChat。

**面试加分回答**:

> "AutoGen GroupChat 的本质是'用对话历史作为共享黑板,用 Speaker Selection 作为调度器'。它的核心创新是让 LLM 自己决定谁该发言,但这也是双刃剑——灵活但不可预测。工业落地时,我通常会:(1) 用自定义 speaker_selection 注入业务规则,而非纯靠 LLM;(2) 设严格的 max_round 和 termination 条件;(3) 对 Manager Agent 用更强模型,Worker 用便宜模型,平衡成本与质量。"

</details>

---

### Q7 【高频】Multi-Agent 系统的核心挑战有哪些? 如何应对一致性、死锁、成本、调试、级联失败?

<details>
<summary>点击查看参考答案</summary>

**五大核心挑战及应对**:

**挑战一: 一致性 (Consistency / Hallucination Drift)**

- **现象**: 多个 Agent 对同一事实给出矛盾信息;或一个 Agent 幻觉的内容被另一个 Agent 当真并放大(幻觉传染)。
- **根因**: Agent 之间无"共识机制",每个 Agent 独立生成,可能基于不同的隐式假设。
- **应对**:
  1. **共享事实库 (Shared Fact Base)**: Agent 的关键结论写入共享状态,其他 Agent 引用而非重新生成。
  2. **辩论式校验 (Debate)**: 对关键决策用 Debate 模式,让 Agent 互相质疑,过滤幻觉。
  3. **外部事实锚定**: 关键事实用 RAG/搜索锚定到外部知识,而非纯靠 LLM 生成。
  4. **一致性检查 Agent**: 专门的"Reviewer"Agent 检查其他 Agent 输出是否自洽。

**挑战二: 死锁与无限循环 (Deadlock / Infinite Loop)**

- **现象**: Agent A 等 Agent B 的结果,Agent B 等 Agent A;或 Supervisor 反复"任务不达标"重新分派,永不终止。
- **根因**: 循环依赖、无终止条件、满意度判断失效。
- **应对**:
  1. **DAG 化任务依赖**: 显式建模任务依赖为有向无环图,避免循环。
  2. **硬性 max_round**: 每个 Agent 和整体系统都设最大轮次,达到即强制终止。
  3. **超时机制**: 单个 Agent 调用设超时,超时则返回 fallback。
  4. **满意度阈值**: Supervisor 用 LLM 对结果打分,超过阈值即停止,而非追求"完美"。
  5. **重复检测**: 检测连续 N 轮输出相似度 > 阈值,判定为循环,终止。

```python
# 重复检测示例
from difflib import SequenceMatcher
def detect_loop(history, threshold=0.9, window=3):
    if len(history) < window * 2:
        return False
    recent = history[-window:]
    prev = history[-window*2:-window]
    for r, p in zip(recent, prev):
        if SequenceMatcher(None, r, p).ratio() < threshold:
            return False
    return True  # 检测到循环
```

**挑战三: 成本与延迟控制 (Cost & Latency)**

- **现象**: N 个 Agent 串行调用 LLM,延迟 = N × 单次延迟;Token 成本随 Agent 数量和轮次指数增长。
- **根因**: Agent 数量过多、轮次过多、用强模型做简单任务。
- **应对**:
  1. **模型分级**: Supervisor/关键决策用 GPT-4o/Claude Opus,Worker/机械任务用 GPT-4o-mini/Haiku。
  2. **并行化**: 独立子任务用 Parallel 模式,延迟取最慢 Agent,而非累加。
  3. **缓存**: 相同输入的 Agent 输出缓存(LRU),避免重复调用。
  4. **早停**: Agent 输出置信度足够高时跳过后续 Agent。
  5. **Token Budget**: 整体设 Token 预算,超出则降级(用更便宜模型或减少 Agent)。
  6. **流式输出**: 用 streaming 降低首 Token 延迟(改善用户体验,不降低总延迟)。

**成本估算公式**:

```
总成本 = Σ(Agent_i 的调用次数 × 平均输入 Token × 输入单价
         + 平均输出 Token × 输出单价) × 模型倍率

例: 5 个 Agent,平均每个调用 3 次,每次 in=2K/out=1K,GPT-4o ($2.5/M in, $10/M out)
成本 = 5 × 3 × (2000×2.5/1M + 1000×10/1M) = 5 × 3 × 0.015 = $0.225/任务
若每天 10K 任务,月成本 ≈ $67,500 —— 必须做模型分级和缓存!
```

**挑战四: 调试困难 (Debugging / Traceability)**

- **现象**: 最终结果错误,但不知道是哪个 Agent 的哪次调用出错;Agent 间的因果链不可追溯。
- **根因**: Agent 输出是 LLM 生成,不确定性高;多轮交互导致"蝴蝶效应"。
- **应对**:
  1. **全链路 Tracing**: 每次 LLM 调用记录 input/output/latency/cost/token,用 LangSmith/Langfuse/Phoenix 追踪。
  2. **结构化日志**: Agent 间消息用 JSON 结构化,而非自由文本,便于过滤和分析。
  3. **Replay 能力**: 保存所有中间状态,支持从任意 checkpoint 重放(共享状态 + Checkpointer 的优势)。
  4. **归因分析**: 错误时,反向追溯是哪个 Agent 的输出引入了错误,做根因分析。
  5. **单元测试 Agent**: 把每个 Agent 当作函数做单元测试(固定输入→期望输出范围),CI 中跑。

**挑战五: 级联失败 (Cascading Failure / Error Propagation)**

- **现象**: 一个 Agent 失败(如 API 超时、输出格式错),导致下游 Agent 拿到错误输入,继续放大错误,最终整个系统崩溃。
- **根因**: 无错误隔离、无降级策略、Agent 之间强依赖。
- **应对**:
  1. **重试与退避**: 单个 Agent 调用失败自动重试(指数退避),重试 N 次仍失败则返回 fallback。
  2. **熔断 (Circuit Breaker)**: 某 Agent 连续失败超阈值,熔断该 Agent,Supervisor 用兜底策略。
  3. **输出校验**: 每个 Agent 输出用 Pydantic Schema 校验,不合规则重试或降级。
  4. **Fallback Agent**: 关键 Agent 失败时,切换到规则引擎或更简单的 Agent 兜底。
  5. **隔离舱 (Bulkhead)**: 不同 Agent 用独立资源池(API Key、并发数),避免一个 Agent 耗尽资源影响其他。

```python
# 输出校验 + 重试示例
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

class CodeReviewResult(BaseModel):
    issues: list[str]
    score: int  # 1-10
    suggestion: str

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def review_agent(code: str) -> CodeReviewResult:
    raw = call_llm(f"审查代码: {code}", response_format="json")
    try:
        return CodeReviewResult.model_validate_json(raw)
    except ValidationError as e:
        log.error(f"输出格式错误: {e}, raw: {raw}")
        raise  # 触发重试
```

**总结表**:

| 挑战 | 核心应对 | 关键工具/机制 |
|------|----------|---------------|
| 一致性 | 共享事实库 + Debate + RAG 锚定 | Shared State、Reviewer Agent |
| 死锁 | DAG + max_round + 超时 + 满意度阈值 | 有向无环图、重复检测 |
| 成本 | 模型分级 + 并行 + 缓存 + Token Budget | 路由模型、LRU Cache |
| 调试 | 全链路 Tracing + Replay + 归因 | LangSmith、Langfuse、Checkpoint |
| 级联失败 | 重试 + 熔断 + 校验 + Fallback | Tenacity、Pydantic、Circuit Breaker |

**面试加分回答**:

> "Multi-Agent 的挑战本质是'分布式系统的经典问题 + LLM 不确定性的叠加'。一致性对应分布式共识,死锁对应资源依赖,成本对应资源调度,调试对应可观测性,级联失败对应容错隔离。所以分布式系统的工程经验(熔断、降级、重试、隔离舱、可观测性)几乎可以平移到 Multi-Agent。区别在于——Multi-Agent 的'计算单元'是 LLM,输出不确定,所以需要更强的'输出校验'和'置信度感知'。这是 Agent 工程师必须建立的思维。"

</details>

---

### Q8 【中频】Agent 角色设计的原则是什么? 如何定义角色、划定能力边界、处理冲突、设定终止条件?

<details>
<summary>点击查看参考答案</summary>

**Agent 角色设计的四大原则**:

**原则一: 角色定义 (Role Definition) — "单一职责 + 明确画像"**

每个 Agent 应遵循"单一职责原则"(SRP),只负责一个明确的功能领域。角色定义包含四个要素:

| 要素 | 说明 | 示例(Coder Agent) |
|------|------|---------------------|
| Profile (画像) | 身份描述,塑造 LLM 的"人格" | "你是一名资深 Python 工程师,10 年经验" |
| Goal (目标) | 该角色的核心目标 | "写出高质量、可维护、有测试的代码" |
| Constraints (约束) | 行为边界,防止越界 | "只写 Python 3.11+ 代码,必须有类型注解,不要写文档" |
| Tools (工具) | 可用的工具集 | `python_exec`、`file_write`、`unit_test_runner` |

**反面案例**: 一个 Agent 同时是"代码审查者"和"代码修改者"——职责冲突,LLM 会自己审自己,失去审查意义。
**正面案例**: Coder 只写代码,Reviewer 只提意见,Coder 再根据意见修改——分离"执行"与"监督"。

**原则二: 能力边界 (Capability Boundary) — "最小权限 + 显式声明"**

- **最小权限**: Agent 只能访问完成任务所需的最小工具集。如 Writer Agent 不应有 `shell_exec` 权限。
- **显式声明**: Agent 的能力用结构化方式注册,Supervisor 只能调用已注册的能力,避免"幻觉调用"不存在的工具。
- **工具白名单**: 每个 Agent 维护一个 `allowed_tools` 列表,框架层拦截越权调用。

```python
class AgentRole:
    name: str
    allowed_tools: list[str]  # 显式白名单
    forbidden_actions: list[str]  # 显式黑名单
    max_tokens_per_call: int  # 单次调用上限
    max_consecutive_calls: int  # 连续调用上限(防霸权)
```

**原则三: 冲突处理 (Conflict Resolution) — "分级升级 + 仲裁机制"**

Agent 之间可能出现意见冲突(如 Coder 说"代码没问题",Reviewer 说"有 Bug")。冲突处理的三层机制:

1. **协商 (Negotiation)**: 冲突双方多轮对话,尝试达成共识。适合低风险冲突。
2. **仲裁 (Arbitration)**: 引入第三方"Judge Agent"裁决。Judge 应是更高权限或更强调模型的 Agent。适合中等风险冲突。
3. **升级 (Escalation)**: 冲突无法自动解决,升级到人工介入。适合高风险冲突(如涉及安全、合规)。

```python
class ConflictResolver:
    def __init__(self, judge_agent: Agent, max_rounds: int = 3):
        self.judge = judge_agent
        self.max_rounds = max_rounds
    async def resolve(self, agent_a_opinion, agent_b_opinion):
        # 第一层: 协商
        for _ in range(self.max_rounds):
            a_resp = await agent_a.discuss(agent_b_opinion)
            b_resp = await agent_b.discuss(a_resp)
            if self._agree(a_resp, b_resp):
                return self._merge(a_resp, b_resp)
        # 第二层: 仲裁
        return await self.judge.arbitrate(agent_a_opinion, agent_b_opinion)
        # 第三层: 升级(在 judge 内部判断,若不确定则抛 HumanInterventionNeeded)
```

**冲突类型与对应策略**:

| 冲突类型 | 示例 | 处理策略 |
|----------|------|----------|
| 事实冲突 | Agent A 说 API 限速 100/s,B 说 1000/s | 调用外部工具(查文档)确认 |
| 风格冲突 | A 说用类,B 说用函数 | Judge 仲裁,依据项目规范 |
| 安全冲突 | A 说可发布,B 说有 SQL 注入 | 升级人工,安全一票否决 |
| 优先级冲突 | A 先做功能,B 先做性能 | PM Agent 仲裁,依据用户优先级 |

**原则四: 终止条件 (Termination Criteria) — "多维判定 + 显式信号"**

Multi-Agent 系统必须显式定义终止条件,否则容易死循环。终止条件的四个维度:

1. **任务完成 (Task Completion)**: 目标达成,如"代码通过所有测试"、"文档字数达标"。
2. **轮次上限 (Round Limit)**: 硬性 max_round,达到即终止(无论是否完成)。
3. **Token/成本上限 (Budget Limit)**: 累计 Token 或费用超预算,强制终止。
4. **超时 (Timeout)**: 端到端时间超限,强制终止。
5. **人工终止 (Human Stop)**: 用户主动中断(人机交互场景)。
6. **收敛信号 (Convergence)**: 连续 N 轮无新进展(输出相似度 > 阈值),判定收敛,终止。

```python
class TerminationChecker:
    def __init__(self, max_rounds=20, max_tokens=100000, timeout=300, conv_threshold=0.95):
        self.max_rounds = max_rounds
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.conv_threshold = conv_threshold
        self.start_time = time.time()
        self.total_tokens = 0
        self.history = []
    def should_stop(self, current_round, current_output, task_done: bool) -> tuple[bool, str]:
        if task_done:
            return True, "task_completed"
        if current_round >= self.max_rounds:
            return True, "max_rounds_reached"
        if self.total_tokens >= self.max_tokens:
            return True, "budget_exceeded"
        if time.time() - self.start_time > self.timeout:
            return True, "timeout"
        if self._is_converged(current_output):
            return True, "converged"
        return False, ""
    def _is_converged(self, output):
        if len(self.history) < 3:
            self.history.append(output)
            return False
        recent = self.history[-3:] + [output]
        sims = [SequenceMatcher(None, recent[i], recent[i+1]).ratio() for i in range(3)]
        return all(s > self.conv_threshold for s in sims) and 0 < sum(sims) / 3
```

**角色设计的常见反模式**:

| 反模式 | 描述 | 后果 | 改进 |
|--------|------|------|------|
| 上帝 Agent | 一个 Agent 什么都做 | Context 膨胀、角色冲突 | 拆分为多个单一职责 Agent |
| 无边界 Agent | Agent 可调用所有工具 | 越权、安全风险 | 最小权限白名单 |
| 礼貌循环 | 两个 Agent 互相"你说得对" | 死循环、浪费 Token | 禁连续发言、设终止条件 |
| 民主暴政 | 用投票决定技术细节 | 妥协方案、技术债 | 关键决策用专家仲裁 |
| 永不终止 | 无 max_round、无完成判定 | 死循环、成本爆炸 | 多维终止条件 |

**面试加分回答**:

> "Agent 角色设计的本质是'组织设计'——把一个公司的人力资源管理原则平移到 Agent 系统。单一职责对应岗位说明书,能力边界对应权限管理,冲突处理对应升级机制,终止条件对应项目验收标准。MetaGPT 论文的核心贡献就是证明了'用组织 SOP 约束 Agent 比让 Agent 自由协作更有效'。这也是为什么 Agent 工程师需要懂一点'组织管理'和'流程设计'——这是 Agent 系统设计的元能力。"

</details>

---

### Q9 【手撕】实现一个 Multi-Agent 协作系统: Supervisor + 3 个专家 Agent,支持任务分解 / 并行执行 / 结果聚合 / 冲突处理。Python 完整实现。

<details>
<summary>点击查看参考答案</summary>

**需求分析**:
- 1 个 Supervisor Agent(主控)+ 3 个专家 Agent(搜索/计算/写作)
- Supervisor 把用户查询分解为子任务,分发给对应专家
- 专家 Agent 并行执行
- Supervisor 聚合结果,若专家结果冲突则触发仲裁
- 支持重试、超时、终止条件

**完整实现(可直接运行,依赖仅 `openai` 和标准库)**:

```python
"""
Multi-Agent Collaboration System
Supervisor + 3 Expert Agents (Searcher / Calculator / Writer)
支持: 任务分解 / 并行执行 / 结果聚合 / 冲突处理 / 重试 / 超时 / 终止条件
"""
from __future__ import annotations
import asyncio
import json
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from difflib import SequenceMatcher
from concurrent.futures import TimeoutError as AsyncTimeoutError


# ============================================================
# 第一部分: 基础抽象
# ============================================================

class AgentRole(str, Enum):
    SUPERVISOR = "supervisor"
    SEARCHER = "searcher"
    CALCULATOR = "calculator"
    WRITER = "writer"
    JUDGE = "judge"


@dataclass
class SubTask:
    """子任务: Supervisor 分解后的单元"""
    agent: str          # 目标 Agent 角色名
    task: str           # 任务描述
    dependencies: list[str] = field(default_factory=list)  # 依赖的其他 subtask id


@dataclass
class AgentResult:
    """Agent 执行结果"""
    agent: str
    task: str
    output: str
    success: bool
    latency: float
    error: str | None = None


@dataclass
class LLMConfig:
    """LLM 调用配置(模型分级)"""
    model: str
    temperature: float = 0.0
    max_tokens: int = 2000
    timeout: float = 30.0


# 模型分级: Supervisor 用强模型,Worker 用便宜模型
MODEL_CONFIGS = {
    AgentRole.SUPERVISOR: LLMConfig(model="gpt-4o", temperature=0.0, max_tokens=2000),
    AgentRole.SEARCHER:   LLMConfig(model="gpt-4o-mini", temperature=0.0, max_tokens=1500),
    AgentRole.CALCULATOR: LLMConfig(model="gpt-4o-mini", temperature=0.0, max_tokens=1000),
    AgentRole.WRITER:     LLMConfig(model="gpt-4o-mini", temperature=0.7, max_tokens=2000),
    AgentRole.JUDGE:      LLMConfig(model="gpt-4o", temperature=0.0, max_tokens=1000),
}


# ============================================================
# 第二部分: LLM 调用封装(含重试 / 超时 / 缓存)
# ============================================================

class LLMClient:
    """LLM 客户端: 重试 + 超时 + 简单缓存"""

    def __init__(self, api_key: str, base_url: str | None = None):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.cache: dict[str, str] = {}  # 简单内存缓存

    def _cache_key(self, model: str, prompt: str) -> str:
        return hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()

    async def call(
        self,
        prompt: str,
        config: LLMConfig,
        response_format: str = "text",  # text | json_object
        max_retries: int = 3,
    ) -> str:
        """带重试和超时的 LLM 调用"""
        key = self._cache_key(config.model, prompt)
        if key in self.cache:
            return self.cache[key]

        last_error: Exception | None = None
        for attempt in range(max_retries):
            try:
                kwargs: dict[str, Any] = {
                    "model": config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": config.temperature,
                    "max_tokens": config.max_tokens,
                }
                if response_format == "json_object":
                    kwargs["response_format"] = {"type": "json_object"}

                resp = await asyncio.wait_for(
                    self.client.chat.completions.create(**kwargs),
                    timeout=config.timeout,
                )
                content = resp.choices[0].message.content or ""
                self.cache[key] = content  # 缓存
                return content
            except (AsyncTimeoutError, asyncio.TimeoutError) as e:
                last_error = e
                wait = 2 ** attempt  # 指数退避
                print(f"[LLM] 超时, {wait}s 后重试 (attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait)
            except Exception as e:
                last_error = e
                wait = 2 ** attempt
                print(f"[LLM] 错误: {type(e).__name__}: {e}, {wait}s 后重试")
                await asyncio.sleep(wait)

        raise RuntimeError(f"LLM 调用失败({max_retries}次重试后): {last_error}")


# ============================================================
# 第三部分: Agent 基类与专家 Agent
# ============================================================

class BaseAgent:
    """Agent 基类: 定义角色画像、工具、执行接口"""

    def __init__(self, role: AgentRole, llm: LLMClient):
        self.role = role
        self.llm = llm
        self.config = MODEL_CONFIGS[role]
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        """子类覆写: 构建角色 system prompt"""
        return ""

    async def run(self, task: str, context: dict | None = None) -> AgentResult:
        """执行任务,返回 AgentResult"""
        start = time.time()
        try:
            prompt = f"{self.system_prompt}\n\n任务: {task}"
            if context:
                prompt += f"\n\n上下文: {json.dumps(context, ensure_ascii=False)}"
            output = await self.llm.call(prompt, self.config)
            return AgentResult(
                agent=self.role.value,
                task=task,
                output=output,
                success=True,
                latency=time.time() - start,
            )
        except Exception as e:
            return AgentResult(
                agent=self.role.value,
                task=task,
                output="",
                success=False,
                latency=time.time() - start,
                error=str(e),
            )


class SearcherAgent(BaseAgent):
    """搜索专家: 负责信息检索(此处用 LLM 模拟,可替换为真实搜索 API)"""

    def __init__(self, llm: LLMClient):
        super().__init__(AgentRole.SEARCHER, llm)

    def _build_system_prompt(self) -> str:
        return (
            "你是一名资深信息检索专家。你的职责是根据任务描述,提供准确、简洁的事实信息。\n"
            "要求:\n"
            "1. 只输出与任务直接相关的事实,不臆测\n"
            "2. 如果不确定,明确说'不确定'\n"
            "3. 输出不超过 300 字\n"
            "4. 用 JSON 格式输出: {\"facts\": \"...\", \"confidence\": 0.0-1.0}"
        )


class CalculatorAgent(BaseAgent):
    """计算专家: 负责数值计算与逻辑推理"""

    def __init__(self, llm: LLMClient):
        super().__init__(AgentRole.CALCULATOR, llm)

    def _build_system_prompt(self) -> str:
        return (
            "你是一名数学与逻辑计算专家。你的职责是进行精确的数值计算和逻辑推理。\n"
            "要求:\n"
            "1. 逐步推导,展示关键步骤\n"
            "2. 最终结果必须用 JSON 输出: {\"result\": 数值或字符串, \"steps\": [\"...\"], \"confidence\": 0.0-1.0}\n"
            "3. 不确定时给出置信度 < 0.6 并说明原因"
        )

    async def run(self, task: str, context: dict | None = None) -> AgentResult:
        """覆写: Calculator 额外做数值校验"""
        result = await super().run(task, context)
        if not result.success:
            return result
        try:
            parsed = json.loads(result.output)
            if "result" not in parsed:
                return AgentResult(
                    agent=self.role.value, task=task, output=result.output,
                    success=False, latency=result.latency,
                    error="输出缺少 'result' 字段",
                )
        except json.JSONDecodeError as e:
            return AgentResult(
                agent=self.role.value, task=task, output=result.output,
                success=False, latency=result.latency,
                error=f"JSON 解析失败: {e}",
            )
        return result


class WriterAgent(BaseAgent):
    """写作专家: 负责文案、报告、代码文档撰写"""

    def __init__(self, llm: LLMClient):
        super().__init__(AgentRole.WRITER, llm)

    def _build_system_prompt(self) -> str:
        return (
            "你是一名资深技术写作专家。你的职责是基于提供的事实和计算结果,撰写清晰、结构化的文案。\n"
            "要求:\n"
            "1. 用 Markdown 格式输出\n"
            "2. 包含: 概述、关键发现、结论三部分\n"
            "3. 语言简洁,避免冗余\n"
            "4. 如果输入信息不足,在开头声明'信息不足,以下为基于有限信息的草稿'"
        )


# ============================================================
# 第四部分: Judge Agent(冲突仲裁)
# ============================================================

class JudgeAgent(BaseAgent):
    """仲裁 Agent: 当专家结果冲突时,裁决哪个更可信"""

    def __init__(self, llm: LLMClient):
        super().__init__(AgentRole.JUDGE, llm)

    def _build_system_prompt(self) -> str:
        return (
            "你是一名中立仲裁人。两个专家对同一任务给出了不同结果,你需要判断哪个更可信。\n"
            "输出 JSON: {\"winner\": \"A\" 或 \"B\" 或 \"tie\", \"reason\": \"...\", \"merged\": \"综合两者的最终答案\"}"
        )

    async def arbitrate(self, task: str, result_a: AgentResult, result_b: AgentResult) -> str:
        prompt = (
            f"任务: {task}\n\n"
            f"专家A({result_a.agent}): {result_a.output}\n\n"
            f"专家B({result_b.agent}): {result_b.output}\n\n"
            "请仲裁。"
        )
        return await self.llm.call(prompt, self.config, response_format="json_object")


# ============================================================
# 第五部分: Supervisor Agent(核心)
# ============================================================

class SupervisorAgent:
    """Supervisor: 任务分解 + 并行调度 + 结果聚合 + 冲突处理"""

    # 可调度的专家 Agent 映射
    EXPERT_ROLES = {AgentRole.SEARCHER, AgentRole.CALCULATOR, AgentRole.WRITER}

    def __init__(
        self,
        llm: LLMClient,
        experts: dict[AgentRole, BaseAgent],
        judge: JudgeAgent,
        max_rounds: int = 3,
        max_subtasks: int = 4,
        convergence_threshold: float = 0.92,
    ):
        self.llm = llm
        self.config = MODEL_CONFIGS[AgentRole.SUPERVISOR]
        self.experts = experts
        self.judge = judge
        self.max_rounds = max_rounds
        self.max_subtasks = max_subtasks
        self.convergence_threshold = convergence_threshold

    def _decompose_prompt(self, query: str) -> str:
        expert_names = [r.value for r in self.EXPERT_ROLES]
        return (
            "你是一个任务调度器。把用户请求分解为最多 "
            f"{self.max_subtasks} 个子任务,每个子任务分配给一个专家 Agent。\n"
            f"可选专家: {expert_names}\n"
            "- searcher: 信息检索、事实查询\n"
            "- calculator: 数值计算、逻辑推理\n"
            "- writer: 文案撰写、报告生成\n\n"
            "规则:\n"
            "1. 子任务数量 1-4 个,宁少勿多\n"
            "2. 如果任务涉及多个领域,才拆分;单一领域不拆\n"
            "3. 如果 writer 依赖 searcher/calculator 的结果,在 dependencies 中标注\n"
            "4. 同一任务可分配给两个相同专家(用于交叉验证),但不要超过两个\n\n"
            "输出 JSON: {\"subtasks\": [{\"agent\": \"searcher\", \"task\": \"...\", \"dependencies\": []}]}\n"
            f"用户请求: {query}"
        )

    async def decompose(self, query: str) -> list[SubTask]:
        """任务分解: LLM 驱动 + Schema 校验"""
        prompt = self._decompose_prompt(query)
        for attempt in range(3):
            try:
                raw = await self.llm.call(prompt, self.config, response_format="json_object")
                data = json.loads(raw)
                subtasks_data = data.get("subtasks", [])
                # 校验: agent 必须在白名单内
                subtasks: list[SubTask] = []
                for item in subtasks_data[: self.max_subtasks]:
                    agent_name = item.get("agent", "")
                    if agent_name not in {r.value for r in self.EXPERT_ROLES}:
                        print(f"[Supervisor] 跳过非法 agent: {agent_name}")
                        continue
                    subtasks.append(SubTask(
                        agent=agent_name,
                        task=item.get("task", ""),
                        dependencies=item.get("dependencies", []),
                    ))
                if not subtasks:
                    # 兜底: 至少一个 writer 任务
                    subtasks = [SubTask(agent="writer", task=query)]
                return subtasks
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"[Supervisor] 分解失败 (attempt {attempt+1}): {e}")
                if attempt == 2:
                    return [SubTask(agent="writer", task=query)]  # 最终兜底

        return [SubTask(agent="writer", task=query)]  # 不可达,保险

    def _topological_sort(self, subtasks: list[SubTask]) -> list[list[SubTask]]:
        """拓扑排序: 把有依赖的子任务分层,同层可并行"""
        # 简化版: 按 dependencies 分层
        layers: list[list[SubTask]] = []
        remaining = list(subtasks)
        completed: set[str] = set()
        # 用 task 内容前 20 字符作 id(简化)
        def task_id(t: SubTask) -> str:
            return t.task[:20]
        while remaining:
            current_layer = []
            for st in remaining[:]:
                deps = st.dependencies
                # 简化: dependencies 为空则可执行;否则需所有 dep 已完成
                if not deps or all(d in completed for d in deps):
                    current_layer.append(st)
                    remaining.remove(st)
            if not current_layer:
                # 出现循环依赖,强制打破
                current_layer = remaining
                remaining = []
            for st in current_layer:
                completed.add(task_id(st))
            layers.append(current_layer)
        return layers

    async def _execute_layer(self, layer: list[SubTask], context: dict) -> list[AgentResult]:
        """并行执行同一层的所有子任务"""
        async def execute_one(st: SubTask) -> AgentResult:
            role = AgentRole(st.agent)
            expert = self.experts[role]
            # 注入依赖结果到 context
            ctx = {k: v for k, v in context.items() if k in st.dependencies}
            return await expert.run(st.task, ctx if ctx else None)

        results = await asyncio.gather(*[execute_one(st) for st in layer], return_exceptions=True)
        # 把异常转为失败的 AgentResult
        final: list[AgentResult] = []
        for st, r in zip(layer, results):
            if isinstance(r, Exception):
                final.append(AgentResult(
                    agent=st.agent, task=st.task, output="",
                    success=False, latency=0.0, error=str(r),
                ))
            else:
                final.append(r)
        return final

    def _detect_conflict(self, results: list[AgentResult]) -> tuple[AgentResult, AgentResult] | None:
        """检测同 agent 类型的两个结果是否冲突"""
        # 按 agent 分组,同 agent 有多个结果时比对
        by_agent: dict[str, list[AgentResult]] = {}
        for r in results:
            by_agent.setdefault(r.agent, []).append(r)
        for agent, group in by_agent.items():
            if len(group) >= 2:
                a, b = group[0], group[1]
                sim = SequenceMatcher(None, a.output, b.output).ratio()
                if sim < self.convergence_threshold and a.success and b.success:
                    print(f"[Supervisor] 检测到冲突: agent={agent}, 相似度={sim:.2f}")
                    return a, b
        return None

    async def _resolve_conflict(self, task: str, a: AgentResult, b: AgentResult) -> str:
        """用 Judge Agent 仲裁冲突"""
        try:
            verdict = await self.judge.arbitrate(task, a, b)
            data = json.loads(verdict)
            return data.get("merged", a.output)  # 优先用 merged,否则回退 A
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[Judge] 仲裁失败: {e}, 回退到结果A")
            return a.output

    async def aggregate(self, query: str, results: list[AgentResult]) -> str:
        """聚合结果: LLM 总结"""
        # 先检查冲突
        conflict = self._detect_conflict(results)
        if conflict:
            a, b = conflict
            resolved = await self._resolve_conflict(query, a, b)
            # 用 resolved 替换 a 和 b
            results = [r for r in results if r is not a and r is not b]
            results.append(AgentResult(
                agent=a.agent, task=a.task, output=resolved,
                success=True, latency=a.latency + b.latency,
            ))

        # 构造聚合 prompt
        parts = []
        for i, r in enumerate(results, 1):
            status = "成功" if r.success else f"失败({r.error})"
            parts.append(f"[{i}] Agent={r.agent}, 状态={status}\n输出:\n{r.output}")
        combined = "\n\n".join(parts)

        prompt = (
            "你是一个结果聚合器。基于以下多个专家 Agent 的输出,回答用户的原始问题。\n"
            "要求:\n"
            "1. 综合所有成功的结果,忽略失败的\n"
            "2. 如果结果有矛盾,说明矛盾点并给出你的判断\n"
            "3. 用 Markdown 输出,结构清晰\n"
            "4. 不要简单拼接,要提炼和总结\n\n"
            f"用户原始问题: {query}\n\n"
            f"专家结果:\n{combined}"
        )
        return await self.llm.call(prompt, self.config)

    async def run(self, query: str) -> dict:
        """Supervisor 主流程: 分解 → 并行执行(分层) → 聚合"""
        print(f"\n[Supervisor] 收到查询: {query}")
        start_time = time.time()

        # 1. 任务分解
        subtasks = await self.decompose(query)
        print(f"[Supervisor] 分解为 {len(subtasks)} 个子任务:")
        for st in subtasks:
            print(f"  - {st.agent}: {st.task[:50]}...")

        # 2. 拓扑排序分层
        layers = self._topological_sort(subtasks)
        print(f"[Supervisor] 分为 {len(layers)} 层执行")

        # 3. 逐层并行执行
        all_results: list[AgentResult] = []
        context: dict[str, str] = {}
        for i, layer in enumerate(layers):
            print(f"\n[Supervisor] === 执行第 {i+1} 层 ({len(layer)} 个任务) ===")
            layer_results = await self._execute_layer(layer, context)
            all_results.extend(layer_results)
            # 把本层结果加入 context,供下层依赖使用
            for st, r in zip(layer, layer_results):
                context[st.task[:20]] = r.output
            for r in layer_results:
                status = "OK" if r.success else f"FAIL: {r.error}"
                print(f"  [{r.agent}] {status} ({r.latency:.2f}s)")

        # 4. 结果聚合
        print(f"\n[Supervisor] === 聚合结果 ===")
        final_answer = await self.aggregate(query, all_results)

        total_time = time.time() - start_time
        total_latency = sum(r.latency for r in all_results)
        print(f"\n[Supervisor] 完成! 总耗时={total_time:.2f}s, "
              f"串行延迟={total_latency:.2f}s, 并行收益={total_latency - total_time:.2f}s")

        return {
            "query": query,
            "subtasks": [{"agent": st.agent, "task": st.task} for st in subtasks],
            "results": [
                {
                    "agent": r.agent, "task": r.task,
                    "success": r.success, "latency": r.latency,
                    "output_preview": r.output[:200], "error": r.error,
                } for r in all_results
            ],
            "final_answer": final_answer,
            "stats": {
                "total_time": total_time,
                "serial_latency": total_latency,
                "parallel_speedup": total_latency / total_time if total_time > 0 else 1.0,
                "success_count": sum(1 for r in all_results if r.success),
                "fail_count": sum(1 for r in all_results if not r.success),
            },
        }


# ============================================================
# 第六部分: 组装与运行
# ============================================================

async def main():
    import os
    api_key = os.getenv("OPENAI_API_KEY", "sk-your-key")
    base_url = os.getenv("OPENAI_BASE_URL")  # 可选: 兼容 OpenAI 协议的代理

    llm = LLMClient(api_key=api_key, base_url=base_url)

    # 组装专家 Agent
    experts = {
        AgentRole.SEARCHER: SearcherAgent(llm),
        AgentRole.CALCULATOR: CalculatorAgent(llm),
        AgentRole.WRITER: WriterAgent(llm),
    }
    judge = JudgeAgent(llm)
    supervisor = SupervisorAgent(llm, experts, judge)

    # 测试用例
    queries = [
        "对比 Python 和 Rust 在 Web 后端的性能差异,并计算: 如果 QPS 要求 10000,Python 需要多少台 4C8G 服务器?",
        "写一篇关于'2024 年大模型推理优化技术'的技术博客,要求包含 KV Cache、量化、投机解码的对比数据。",
    ]

    for q in queries:
        result = await supervisor.run(q)
        print("\n" + "=" * 70)
        print("最终答案:")
        print("=" * 70)
        print(result["final_answer"])
        print("\n统计:", json.dumps(result["stats"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
```

**代码设计要点解析(面试讲解时强调)**:

1. **模型分级**: `MODEL_CONFIGS` 给 Supervisor/Judge 用 GPT-4o,给 Worker 用 GPT-4o-mini,成本降 70%+。
2. **任务分解的兜底**: LLM 输出 JSON 可能失败,做 3 次重试 + 最终兜底(直接给 writer),永不抛错。
3. **拓扑排序**: 把有依赖的子任务分层,同层并行跨层串行,既支持依赖又最大化并行度。
4. **冲突检测**: 同类型 Agent 有多个结果时,用 `SequenceMatcher` 计算相似度,低于阈值则判为冲突,触发 Judge 仲裁。
5. **重试与退避**: LLM 调用层用指数退避重试,Agent 层用 `asyncio.gather` 隔离异常(单个 Agent 失败不影响其他)。
6. **可观测性**: 每个 AgentResult 记录 latency/success/error,Supervisor 统计并行加速比,便于性能分析。
7. **终止条件**: `max_subtasks` 限制分解数量,`max_rounds` 限制聚合轮次,避免失控。

**追问应对**:

- "如何扩展到更多 Agent?" —— `EXPERT_ROLES` 和 `experts` 字典加新角色即可,Supervisor 的 decompose prompt 同步更新专家说明。开闭原则。
- "如何做 Checkpoint?" —— 在每层执行后把 `context` 和 `all_results` 序列化到 Redis/DB,失败时从最近 checkpoint 恢复。
- "如何避免 Supervisor 分解错误?" —— (1) 用 Schema 校验;(2) 用"双 Supervisor"对分解结果做交叉验证;(3) 对常见任务类型预置分解模板,LLM 只在模板不匹配时自由分解。

</details>

---

### Q10 【系统设计】设计一个软件开发 Multi-Agent 系统: PM Agent + 架构师 Agent + 开发 Agent + 测试 Agent。要求支持需求分析、架构设计、编码、测试、Bug 修复的闭环。

<details>
<summary>点击查看参考答案</summary>

**一、需求理解与目标定义**

题目要求设计一个能完成"软件开发全流程"的 Multi-Agent 系统,涵盖: 需求分析 → 架构设计 → 编码 → 测试 → Bug 修复 → 交付。这是 MetaGPT 的典型场景,但要给出自己的设计权衡。

**核心目标**:
- 输入: 一句话需求(如"做一个待办清单 CLI 工具")
- 输出: 可运行的代码 + 测试 + 文档
- 约束: 闭环自动迭代,Bug 修复不超过 N 轮

**二、系统架构(分层)**

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│            (CLI / Web / API - 接收需求,展示进度)             │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Orchestrator (Supervisor)                   │
│   - 流程编排(SOP)  - 状态管理  - 终止判定  - 冲突仲裁        │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Layer (4 个角色)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ PM Agent │→ │Arch Agent│→ │ Dev Agent│↔ │ QA Agent │    │
│  │ 需求分析 │  │ 架构设计 │  │ 编码实现 │  │ 测试验证 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Shared State (Knowledge Base)                   │
│   PRD 文档 | 架构文档 | 代码 | 测试用例 | Bug 列表 | 日志    │
└──────────────────────────┬──────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Tool Layer (工具与外部服务)                     │
│  Git | File System | Linter | Test Runner | Build | Sandbox  │
└─────────────────────────────────────────────────────────────┘
```

**三、Agent 角色设计(详细)**

**1. PM Agent (产品经理)**

| 维度 | 设计 |
|------|------|
| 职责 | 把模糊需求转为结构化 PRD;与用户澄清需求;验收最终交付 |
| 输入 | 用户原始需求 |
| 输出 | PRD(JSON Schema: goals, user_stories, acceptance_criteria, non_functional_reqs) |
| 工具 | `ask_user`(向用户提问)、`search_similar_products` |
| 模型 | GPT-4o(需求理解需要强推理) |
| 终止 | PRD 通过 Schema 校验 + 用户确认(或自动评分 > 8/10) |

**2. Architect Agent (架构师)**

| 维度 | 设计 |
|------|------|
| 职责 | 基于 PRD 设计技术方案;定义模块、接口、数据结构;选型技术栈 |
| 输入 | PRD 文档 |
| 输出 | 设计文档(JSON: tech_stack, modules, interfaces, data_models, file_structure) |
| 工具 | `search_best_practices`、`read_existing_code` |
| 模型 | GPT-4o(架构决策影响全局) |
| 终止 | 设计文档通过 Schema 校验 + PM Agent 评审通过 |

**3. Dev Agent (开发)**

| 维度 | 设计 |
|------|------|
| 职责 | 基于架构设计编写代码;修复 QA 报告的 Bug;维护代码质量 |
| 输入 | 架构文档 + Bug 列表(若有) |
| 输出 | 代码文件 + 提交说明 |
| 工具 | `write_file`、`read_file`、`run_command`、`git_commit`、`lint` |
| 模型 | DeepSeek-Coder / GPT-4o(代码生成专项模型) |
| 终止 | 代码通过 Lint + 单元测试 + 编译 |

**4. QA Agent (测试)**

| 维度 | 设计 |
|------|------|
| 职责 | 基于 PRD 和架构编写测试用例;运行测试;报告 Bug;验证修复 |
| 输入 | PRD + 架构文档 + 代码 |
| 输出 | 测试用例 + 测试报告 + Bug 列表(JSON: case, expected, actual, severity) |
| 工具 | `write_test`、`run_test`、`coverage_report` |
| 模型 | GPT-4o-mini(测试用例生成不需要最强模型) |
| 终止 | 所有测试通过 或 Bug 数 < 阈值 且无 Critical Bug |

**四、SOP 流程编排(核心)**

```
[Start]
  │
  ▼
[Phase 1: 需求分析] ── PM Agent ──► PRD
  │                                    │
  │     (若 PRD 不达标,PM 与用户澄清)  │
  ▼                                    │
[Phase 2: 架构设计] ── Architect ──► 设计文档
  │                                    │
  │       (PM 评审设计,不通过则返工)   │
  ▼                                    │
[Phase 3: 编码] ── Dev Agent ──► 代码 v1
  │                                    │
  ▼                                    │
[Phase 4: 测试] ── QA Agent ──► 测试报告 + Bug 列表
  │                                    │
  │  ┌───── Bug 数 > 0 ? ─────┐         │
  │  ▼                        ▼         │
  │  Yes                       No       │
  │  │                        │         │
  │  ▼                        ▼         │
  │[Phase 5: 修复] Dev ◄── Bug 列表    │
  │  │                                  │
  │  └──► 回到 Phase 4(最多 3 轮)      │
  │                                     │
  ▼                                     │
[Phase 6: 交付] ── PM 验收 ──► 最终产物
  │
  ▼
[End]
```

**五、状态管理(Shared State Schema)**

```python
from pydantic import BaseModel, Field
from typing import Literal

class PRD(BaseModel):
    original_requirement: str
    goals: list[str]
    user_stories: list[str]
    acceptance_criteria: list[str]
    non_functional_reqs: list[str] = Field(default_factory=list)
    status: Literal["draft", "reviewed", "approved"] = "draft"

class Architecture(BaseModel):
    tech_stack: list[str]
    modules: list[dict]  # {name, responsibility, dependencies}
    interfaces: list[dict]  # {name, signature, description}
    data_models: list[dict]
    file_structure: dict  # 树形
    status: Literal["draft", "approved"] = "draft"

class Bug(BaseModel):
    id: str
    description: str
    severity: Literal["critical", "major", "minor"]
    file: str
    status: Literal["open", "fixed", "verified"] = "open"

class ProjectState(BaseModel):
    """全局共享状态"""
    requirement: str
    prd: PRD | None = None
    architecture: Architecture | None = None
    code_files: dict[str, str] = Field(default_factory=dict)  # path -> content
    test_files: dict[str, str] = Field(default_factory=dict)
    test_report: dict | None = None
    bugs: list[Bug] = Field(default_factory=list)
    fix_round: int = 0
    max_fix_rounds: int = 3
    phase: Literal["requirement", "design", "coding", "testing", "fixing", "done"] = "requirement"
    history: list[dict] = Field(default_factory=list)  # 审计日志
```

**六、Orchestrator 实现(简化骨架)**

```python
class DevOrchestrator:
    """软件开发 Multi-Agent 编排器"""

    def __init__(self, pm, architect, dev, qa, llm):
        self.pm = pm
        self.architect = architect
        self.dev = dev
        self.qa = qa
        self.llm = llm
        self.state = ProjectState(requirement="")

    async def run(self, requirement: str) -> ProjectState:
        self.state.requirement = requirement

        # Phase 1: 需求
        await self._phase_requirement()
        # Phase 2: 架构
        await self._phase_design()
        # Phase 3: 编码
        await self._phase_coding()
        # Phase 4-5: 测试-修复循环
        await self._phase_test_fix_loop()
        # Phase 6: 交付
        await self._phase_deliver()
        return self.state

    async def _phase_requirement(self):
        self.state.phase = "requirement"
        self.state.prd = await self.pm.analyze_requirement(self.state.requirement)
        # 校验 + 评审
        if not self._validate_prd(self.state.prd):
            self.state.prd = await self.pm.refine(self.state.prd)
        self._log("requirement_done", prd=self.state.prd.model_dump())

    async def _phase_design(self):
        self.state.phase = "design"
        self.state.architecture = await self.architect.design(self.state.prd)
        # PM 评审架构
        review = await self.pm.review_architecture(self.state.architecture)
        if review["approved"]:
            self.state.architecture.status = "approved"
        else:
            self.state.architecture = await self.architect.revise(self.state.architecture, review)
        self._log("design_done", arch=self.state.architecture.model_dump())

    async def _phase_coding(self):
        self.state.phase = "coding"
        # 按模块并行编码(独立模块可并行)
        independent_modules = self._get_independent_modules(self.state.architecture)
        tasks = [self.dev.implement_module(m, self.state.architecture, self.state.prd)
                 for m in independent_modules]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for m, r in zip(independent_modules, results):
            if isinstance(r, Exception):
                self._log("coding_failed", module=m.name, error=str(r))
            else:
                self.state.code_files.update(r)
        self._log("coding_done", files=list(self.state.code_files.keys()))

    async def _phase_test_fix_loop(self):
        """测试-修复循环: 最多 max_fix_rounds 轮"""
        while self.state.fix_round < self.state.max_fix_rounds:
            self.state.phase = "testing"
            self.state.test_report = await self.qa.run_tests(
                self.state.code_files, self.state.test_files, self.state.prd
            )
            self.state.bugs = self.qa.extract_bugs(self.state.test_report)

            if not self.state.bugs:
                self._log("all_tests_passed")
                break

            # 检查是否有 critical bug
            critical = [b for b in self.state.bugs if b.severity == "critical"]
            if not critical and self.state.fix_round >= 1:
                self._log("only_minor_bugs_remain", bugs=[b.id for b in self.state.bugs])
                break  # 只有 minor bug 且已修过一轮,接受

            self.state.phase = "fixing"
            self.state.fix_round += 1
            # 并行修复(不同文件的 bug 可并行)
            bugs_by_file: dict[str, list[Bug]] = {}
            for b in self.state.bugs:
                bugs_by_file.setdefault(b.file, []).append(b)
            fix_tasks = [
                self.dev.fix_bugs(file, bugs, self.state.code_files[file])
                for file, bugs in bugs_by_file.items()
            ]
            fixes = await asyncio.gather(*fix_tasks, return_exceptions=True)
            for (file, _), fix in zip(bugs_by_file.items(), fixes):
                if not isinstance(fix, Exception):
                    self.state.code_files[file] = fix
            self._log("fix_round_done", round=self.state.fix_round)

        if self.state.fix_round >= self.state.max_fix_rounds:
            self._log("max_fix_rounds_reached", remaining_bugs=len(self.state.bugs))

    async def _phase_deliver(self):
        self.state.phase = "done"
        # PM 验收
        acceptance = await self.pm.acceptance_review(self.state)
        self._log("delivered", acceptance=acceptance)

    def _log(self, event: str, **kwargs):
        self.state.history.append({
            "timestamp": time.time(),
            "event": event,
            **kwargs,
        })

    def _validate_prd(self, prd: PRD) -> bool:
        return bool(prd.goals and prd.user_stories and prd.acceptance_criteria)

    def _get_independent_modules(self, arch: Architecture) -> list:
        """返回无依赖关系的模块(可并行编码)"""
        return [m for m in arch.modules if not m.get("dependencies")]
```

**七、关键设计决策与权衡(面试重点)**

| 决策点 | 选择 | 理由 | 替代方案 |
|--------|------|------|----------|
| 协作模式 | Hierarchical + Sequential + 局部 Parallel | 软件开发有明确 SOP,层级式可控;独立模块并行加速 | 纯 GroupChat(不可控) |
| 通信机制 | 共享状态(Pydantic Model) | 结构化、可序列化、可 Checkpoint | 消息队列(过重) |
| 模型分级 | PM/Arch 用 GPT-4o,QA 用 mini,Dev 用 Coder | 决策影响全局的用强模型,机械任务用便宜模型 | 全用 GPT-4o(成本 5x) |
| Bug 修复循环 | max_rounds=3 + severity 判断 | 防死循环,接受 minor bug | 无限修复(成本爆炸) |
| 冲突处理 | PM 评审架构;Dev/QA 冲突由 Orchestrator 仲裁 | PM 是"产品owner",有最终决定权 | Judge Agent(增加成本) |
| 终止条件 | PRD 质量分 + 测试通过 + max_rounds + 无 critical | 多维判定,避免单一条件失效 | 仅"测试通过"(可能死循环) |

**八、扩展性设计**

1. **新角色扩展**: 加一个 `Reviewer Agent` 做代码审查(独立于 QA),只需注册到 Orchestrator 并在 SOP 中插入 Phase。
2. **工具扩展**: Agent 工具用插件化设计(`@tool` 装饰器注册),新增工具无需改 Orchestrator。
3. **模型替换**: `LLMClient` 抽象层,支持 OpenAI/Anthropic/本地模型切换,Agent 不感知。
4. **并行度扩展**: 模块级并行已支持;可扩展到"多 Dev Agent 并行写不同模块",用 work-queue 模式。

**九、容错与可观测性**

- **容错**: 每个 Agent 调用包 `try/except` + 重试;Bug 修复循环有 `max_rounds`;状态 Checkpoint 到 DB,失败可恢复。
- **Tracing**: `self._log()` 记录每个 Phase 的事件;集成 LangSmith 追踪每次 LLM 调用。
- **Metrics**: 记录每个 Agent 的 latency/success_rate/token_cost;Bug 修复轮次;最终测试覆盖率。
- **Replay**: `ProjectState` 可序列化,从任意 checkpoint 重放。

**十、面试加分总结**

> "这个设计的核心是'用 SOP 约束流程 + 用共享状态保证一致性 + 用模型分级控制成本 + 用多维终止条件防止失控'。它借鉴了 MetaGPT 的 SOP 思想,但在三个地方做了工程化增强:(1) 独立模块并行编码,而非纯串行;(2) Bug 修复有 severity 感知的早停策略,而非无脑循环;(3) 全状态 Checkpoint,支持失败恢复和人机交互暂停。实际落地时,最大的挑战不是架构设计,而是'如何让 Dev Agent 写出的代码能通过 QA Agent 的测试'——这需要在 Dev 和 QA 之间共享'测试规范'和'代码规范'的知识库,否则两个 Agent 各说各话,永远修不完 Bug。"

</details>
