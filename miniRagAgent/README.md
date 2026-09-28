# Mini RAG Agent — 智能知识库问答系统

> 一个"小而全"的 Agent 实战项目。
> **零配置可运行** —— 不需要 API Key、不需要外部数据库、不需要向量库,`python main.py` 直接启动。

---

## 一、项目简介

这是一个基于 ReAct 框架的 RAG Agent 问答系统,包含:

- **Agent 核心**:ReAct 循环(Thought → Action → Observation → Finish)
- **RAG 检索**:文档分块 → TF-IDF 向量化 → 余弦相似度检索 → Rerank
- **记忆系统**:短期记忆(对话窗口)+ 长期记忆(向量检索)
- **工具调用**:知识检索、计算器、时间查询(Function Calling)
- **FastAPI 接口**:同步问答 + SSE 流式输出 + 知识库管理
- **数据持久化**:SQLAlchemy ORM + SQLite(会话、消息)

---

## 二、快速开始

### 环境要求

- Python 3.10+
- pip install -r requirements.txt

### 启动

```bash
cd Demo
pip install -r requirements.txt
python main.py
```

启动后访问:
- **Swagger 文档**:http://localhost:8000/docs
- **API 根路径**:http://localhost:8000/

### 使用真实 LLM(可选)

```bash
# 设置 OpenAI API Key
export OPENAI_API_KEY="sk-xxxxxxxx"
export LLM_MODE="openai"

# 或使用兼容 OpenAI 接口的模型(如通义千问)
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_API_KEY="sk-xxxxxxxx"
export OPENAI_MODEL="qwen-plus"

python main.py
```

不设置 API Key 时,默认使用内置 Mock LLM,也能完整演示 ReAct 循环。

---

## 三、API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 同步问答(返回完整结果) |
| POST | `/chat/stream` | SSE 流式问答(逐步推送思考过程) |
| GET | `/sessions/{id}/messages` | 获取会话历史 |
| POST | `/knowledge/upload` | 上传文档到知识库 |
| GET | `/knowledge/stats` | 知识库统计 |
| GET | `/health` | 健康检查 |

### 示例:同步问答

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是 RAG?"}'
```

响应:
```json
{
  "answer": "根据知识库中的信息,关于\"什么是 RAG?\":\nRAG 是...",
  "session_id": "abc-123",
  "steps": [
    {"step": 1, "thought": "用户询问了技术相关问题...", "action": "search_knowledge", ...},
    {"step": 2, "thought": "我已经获得了相关信息...", "action": "finish", ...}
  ],
  "tool_calls": [{"tool": "search_knowledge", "input": "什么是 RAG?", ...}],
  "elapsed": 0.52
}
```

### 示例:SSE 流式问答

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "计算 123 * 456"}'
```

流式响应(SSE 格式):
```
data: {"type": "thought", "step": 1, "content": "用户问了一个数学计算问题..."}

data: {"type": "action", "step": 1, "name": "calculator", "input": "123 * 456"}

data: {"type": "observation", "step": 1, "content": "计算结果: 123 * 456 = 56088"}

data: {"type": "answer", "content": "根据计算结果,123 * 456 = 56088"}

data: {"type": "done", "session_id": "abc-123"}
```

---

## 四、项目架构

```
用户请求
  │
  ▼
┌─────────────────────────────────────────────┐
│            FastAPI (api/routes.py)           │
│  POST /chat  │  POST /chat/stream (SSE)     │
│  Pydantic 验证  │  依赖注入 (Depends)        │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          ReAct Agent (agent/core.py)         │
│  Thought → Action → Observation → Finish    │
│  循环最多 MAX_AGENT_STEPS 步                │
└──────┬────────┬──────────┬──────────────────┘
       │        │          │
       ▼        ▼          ▼
┌──────────┐ ┌────────┐ ┌────────────────┐
│   LLM    │ │ Tools  │ │    Memory      │
│ (llm.py) │ │(tools  │ │ (memory.py)    │
│ Mock /   │ │ .py)   │ │ 短期+长期       │
│ OpenAI   │ │        │ │                │
└──────────┘ │ 检索   │ └────────────────┘
             │ 计算器  │
             │ 时间    │
             └───┬────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│        RAG 引擎 (rag/)                      │
│  Chunker → Embedder → Retriever → Rerank   │
│  知识库 (knowledge_base.py)                 │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        数据库 (db/)                          │
│  SQLAlchemy ORM + SQLite                    │
│  Session 表 + Message 表                    │
└─────────────────────────────────────────────┘
```

---

## 五、文件说明与知识点映射

| 文件 | 功能 | 对应学习日 | 核心知识点 |
|------|------|-----------|-----------|
| **config.py** | 全局配置 | — | 配置管理、环境变量 |
| **main.py** | 入口,组装各模块 | — | 依赖注入、应用初始化 |
| | | | |
| **agent/core.py** | ReAct 循环 | Day02, 06 | Thought/Action/Observation 闭环、流式 yield |
| **agent/llm.py** | LLM 接口 | Day01, 34 | 策略模式、Mock/OpenAI 双模式 |
| **agent/tools.py** | 工具定义 | Day03 | Function Calling、工具 Schema、安全计算器 |
| **agent/memory.py** | 记忆系统 | Day05 | 短期窗口 + 长期向量记忆、记忆评分公式 |
| | | | |
| **rag/chunker.py** | 文档分块 | Day08 | 递归分块、重叠窗口、Chunk 元数据 |
| **rag/embedder.py** | TF-IDF 向量化 | Day08-10 | TF-IDF、L2 归一化、余弦相似度 |
| **rag/retriever.py** | 向量检索 + Rerank | Day09-10 | 批量余弦相似度、关键词 Rerank |
| **rag/knowledge_base.py** | 知识库管理 | Day08, 13 | 全链路整合、增量索引、检索门控 |
| | | | |
| **api/routes.py** | FastAPI 路由 | Day35 | SSE 流式输出、Pydantic 验证、依赖注入 |
| **api/schemas.py** | Pydantic 模型 | Day35 | BaseModel、Field 约束、请求/响应模型 |
| | | | |
| **db/models.py** | ORM 模型 | Day35 | SQLAlchemy、一对多关系、cascade |
| **db/database.py** | 数据库连接 | Day35 | 连接池、上下文管理器、FastAPI 依赖注入 |
| | | | |
| **data/sample_docs/** | 示例知识库 | — | Agent/RAG/Python 三篇文档 |

---

## 六、核心代码导读

### 6.1 ReAct 循环(agent/core.py)

这是整个项目最核心的部分。ReAct 循环的流程:

```python
# agent/core.py 中的 _run_internal 方法(简化版)

for step_num in range(1, max_steps + 1):
    # 1. 构造 Prompt(工具列表 + 历史 + 问题 + 之前的步骤)
    prompt = build_prompt(tools, history, question, previous_steps)

    # 2. LLM 生成决策(Thought + Action + Action Input)
    response = llm.generate(prompt)
    thought, action, action_input = parse(response)

    # 3. 如果 Action = finish,返回最终答案
    if action == "finish":
        return action_input  # 最终答案

    # 4. 否则执行工具,得到 Observation
    observation = tools.execute(action, action_input)

    # 5. 把 Observation 加入上下文,继续循环
    previous_steps += f"Observation: {observation}\n"
```

**关键设计**:
- `run()`:同步执行,返回完整结果
- `run_stream()`:流式执行,yield 每一步(用于 SSE)
- `max_steps`:防止无限循环
- `_parse_react_response()`:用正则解析 LLM 输出的 Thought/Action/Action Input

### 6.2 记忆评分公式(agent/memory.py)

```python
# 长期记忆检索评分(对应 Generative Agents 论文)
Score = 0.45 × similarity   # 余弦相似度
      + 0.20 × recency      # 时间近度(指数衰减)
      + 0.20 × importance   # 重要度
      + 0.15 × frequency    # 被检索频率
```

### 6.3 RAG 检索链路(rag/knowledge_base.py)

```python
# 全链路:文档 → 分块 → Embedding → 检索 → Rerank → 上下文
kb = KnowledgeBase()
kb.add_document(text, source="file.md")  # 分块 + 向量化
results = kb.search("什么是 Agent?")      # 向量检索 + Rerank
context = kb.get_context(query)           # 格式化为 LLM 上下文
```

### 6.4 SSE 流式输出(api/routes.py)

```python
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_stream():
        for step in agent.run_stream(request.query):
            yield f"data: {json.dumps({'type': 'thought', ...})}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### 6.5 安全计算器(agent/tools.py)

```python
# 不用 eval()!用 AST 解析,只允许算术运算
def calculator(expression: str) -> str:
    tree = ast.parse(expression, mode="eval")
    result = _safe_eval(tree)  # 递归安全求值
    return f"计算结果: {expression} = {result}"
```

---

## 七、面试中如何讲这个项目

### 30 秒电梯演讲

> "我开发了一个 Mini RAG Agent 问答系统,用 ReAct 框架实现 Agent 的推理-行动循环,
> 包含 RAG 全链路(分块→TF-IDF→检索→Rerank)、双层记忆系统(短期窗口+长期向量检索)、
> Function Calling 工具调用、FastAPI SSE 流式输出、SQLAlchemy 持久化。
> 零配置可运行,Mock LLM 模式下也能完整演示 Agent 的工作流程。"

### 技术亮点(分层递进)

**第一层(架构理解)**:
- Agent = LLM + Tools + Memory + Loop,每个组件解耦,可独立替换
- 策略模式切换 LLM(Mock / OpenAI),不影响上层逻辑

**第二层(技术决策)**:
- 为什么用 TF-IDF 而不是 BGE?→ Demo 追求零配置,生产环境替换为 BGE
- 为什么用 SQLite 而不是 PostgreSQL?→ Demo 零依赖,生产环境换连接字符串即可
- 为什么用 SSE 而不是 WebSocket?→ SSE 更简单,Agent 输出是单向推送

**第三层(实现细节)**:
- ReAct 循环如何防止无限循环?→ max_steps + finish 检测
- 记忆评分公式的权重?→ 0.45/0.20/0.20/0.15,对应论文 Generative Agents
- 计算器为什么不用 eval?→ AST 安全解析,防止代码注入(对应 Day19 安全)
- Rerank 怎么做的?→ 0.5×向量相似度 + 0.5×关键词重叠度

### 常见追问

| 追问 | 回答要点 |
|------|---------|
| 如何接入真实 LLM? | 设置 OPENAI_API_KEY 环境变量,LLM_MODE=openai,支持任意 OpenAI 兼容接口 |
| 如何提升检索效果? | 替换 TF-IDF 为 BGE、加 BM25 混合检索 + RRF、用 Cross-Encoder 做 Rerank |
| 如何支持多用户? | 加认证中间件、Session 按 user_id 隔离、记忆系统按用户分离 |
| 如何做评估? | 用 RAGAS 评估 Faithfulness/Answer Relevancy,构建测试集 |
| 如何降低延迟? | asyncio 并发工具调用、缓存高频 Query、流式输出降低体感延迟 |

---

## 八、扩展练习

可升级模块,后续优化以下扩展:

1. **替换 Embedding**:把 TF-IDF 换成 `sentence-transformers` 的 BGE 模型
2. **加 BM25 混合检索**:实现 BM25 + 向量 + RRF 融合
3. **加 Cross-Encoder Rerank**:用 `bge-reranker-base` 做真实 Rerank
4. **加 LangGraph 编排**:用 StateGraph 替换手写 ReAct 循环
5. **加异步数据库**:用 `asyncpg` + `async SQLAlchemy` 替换同步 ORM
6. **加评估框架**:用 RAGAS 跑离线评估,输出 Faithfulness 等指标
7. **加 Multi-Agent**:扩展为 Planer + Executor + Reviewer 三 Agent 协作
8. **加 Tracing**:集成 Langfuse,记录每一步的 Trace/Span
