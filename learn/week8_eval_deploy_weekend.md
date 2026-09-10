## Day 6：综合实战——完整 Agent 上线

> 把本周所有知识整合：构建一个带评测、测试、优化的 Agent 服务，Docker 化部署。

### 6.1 项目结构

```
agent-project/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI 入口
│   ├── agent.py          # Agent 核心
│   ├── evaluator.py      # 评测模块
│   ├── cache.py          # 缓存模块
│   └── middleware.py     # 中间件
├── tests/
│   ├── __init__.py
│   ├── test_agent.py     # Agent 测试
│   ├── test_api.py       # API 测试
│   └── conftest.py       # 共享 fixture
├── eval/
│   └── golden_set.json   # 评测数据集
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

### 6.2 核心代码

```python
"""
Agent 核心
文件: app/agent.py
"""

import os
from typing import TypedDict, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    query: str
    route: str
    result: str
    tokens_used: int

def make_llm(temp=0, model=None):
    return ChatOpenAI(
        model=model or os.environ.get("MODEL_NAME", "glm-4-flash"),
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

def router(state: AgentState) -> dict:
    """路由节点：判断任务类型"""
    llm = make_llm(0)
    query = state["query"]
    resp = llm.invoke([HumanMessage(
        content=f"判断任务类型，只回答一个词:\n"
                f"code（编程） / chat（闲聊） / qa（问答）\n"
                f"任务: {query}"
    )])
    route = resp.content.strip().lower()
    for r in ["code", "chat", "qa"]:
        if r in route:
            return {"route": r}
    return {"route": "chat"}

def coder(state: AgentState) -> dict:
    llm = make_llm(0.2)
    resp = llm.invoke([HumanMessage(
        content=f"你是 Python 编程专家。请完成以下任务:\n{state['query']}"
    )])
    tokens = 0
    if resp.usage_metadata:
        tokens = resp.usage_metadata.get("total_tokens", 0)
    return {
        "result": resp.content,
        "tokens_used": tokens,
        "messages": [AIMessage(content=resp.content, name="coder")],
    }

def chatter(state: AgentState) -> dict:
    llm = make_llm(0.7)
    resp = llm.invoke([HumanMessage(content=state["query"])])
    tokens = 0
    if resp.usage_metadata:
        tokens = resp.usage_metadata.get("total_tokens", 0)
    return {
        "result": resp.content,
        "tokens_used": tokens,
        "messages": [AIMessage(content=resp.content, name="chatter")],
    }

def qa_agent(state: AgentState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(
        content=f"你是知识助手。简洁回答:\n{state['query']}"
    )])
    tokens = 0
    if resp.usage_metadata:
        tokens = resp.usage_metadata.get("total_tokens", 0)
    return {
        "result": resp.content,
        "tokens_used": tokens,
        "messages": [AIMessage(content=resp.content, name="qa")],
    }

def route_fn(state: AgentState) -> str:
    return state.get("route", "chat")

# 构建图
builder = StateGraph(AgentState)
builder.add_node("router", router)
builder.add_node("coder", coder)
builder.add_node("chat", chatter)
builder.add_node("qa", qa_agent)
builder.add_edge(START, "router")
builder.add_conditional_edges("router", route_fn, {
    "coder": "coder", "chat": "chat", "qa": "qa",
})
builder.add_edge("coder", END)
builder.add_edge("chat", END)
builder.add_edge("qa", END)

# 全局 Agent 实例
checkpointer = MemorySaver()
agent = builder.compile(checkpointer=checkpointer)
```

```python
"""
缓存模块
文件: app/cache.py
"""

import time
import hashlib
from collections import OrderedDict

class LRUCache:
    """带 TTL 的 LRU 缓存"""

    def __init__(self, max_size: int = 100, ttl: int = 600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _key(self, prompt: str, model: str) -> str:
        return hashlib.md5(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str = "glm-4-flash") -> str | None:
        key = self._key(prompt, model)
        if key in self.cache:
            value, ts = self.cache[key]
            if time.time() - ts < self.ttl:
                self.hits += 1
                self.cache.move_to_end(key)
                return value
            else:
                del self.cache[key]
        self.misses += 1
        return None

    def set(self, prompt: str, value: str, model: str = "glm-4-flash"):
        key = self._key(prompt, model)
        self.cache[key] = (value, time.time())
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": self.hits / total if total > 0 else 0,
            "size": len(self.cache),
        }

# 全局缓存实例
response_cache = LRUCache(max_size=200, ttl=600)
```

```python
"""
FastAPI 主应用
文件: app/main.py
"""

import os
import time
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent import agent, make_llm
from .cache import response_cache

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("agent")

app = FastAPI(title="Agent Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(f"{request.method} {request.url.path} {response.status_code} {duration:.3f}s")
    return response

# === 请求/响应模型 ===

class QueryRequest(BaseModel):
    query: str
    thread_id: str = "default"
    use_cache: bool = True

class QueryResponse(BaseModel):
    route: str
    result: str
    tokens_used: int
    cached: bool
    latency_ms: int

# === 接口 ===

@app.get("/health")
async def health():
    return {"status": "ok", "cache": response_cache.stats()}

@app.post("/agent", response_model=QueryResponse)
async def run_agent(req: QueryRequest):
    if not req.query:
        raise HTTPException(status_code=400, detail="query 不能为空")

    start = time.time()
    cached = False

    # 查缓存
    if req.use_cache:
        cached_result = response_cache.get(req.query)
        if cached_result is not None:
            cached = True
            latency = int((time.time() - start) * 1000)
            return QueryResponse(
                route="cached",
                result=cached_result,
                tokens_used=0,
                cached=True,
                latency_ms=latency,
            )

    # 调用 Agent
    config = {"configurable": {"thread_id": req.thread_id}}
    try:
        result = await agent.ainvoke({
            "messages": [],
            "query": req.query,
            "route": "",
            "result": "",
            "tokens_used": 0,
        }, config)
    except Exception as e:
        logger.error(f"Agent 执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Agent 执行失败")

    response_text = result.get("result", "")
    tokens = result.get("tokens_used", 0)
    route = result.get("route", "")

    # 写缓存
    if req.use_cache and response_text:
        response_cache.set(req.query, response_text)

    latency = int((time.time() - start) * 1000)
    return QueryResponse(
        route=route,
        result=response_text,
        tokens_used=tokens,
        cached=False,
        latency_ms=latency,
    )

@app.get("/cache/stats")
async def cache_stats():
    return response_cache.stats()

@app.delete("/cache")
async def clear_cache():
    response_cache.cache.clear()
    response_cache.hits = 0
    response_cache.misses = 0
    return {"status": "cache cleared"}
```

```python
"""
评测模块
文件: app/evaluator.py
"""

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

GOLDEN_SET = {
    "version": "1.0",
    "cases": [
        {"id": "qa_001", "category": "qa", "input": "中国首都是哪？",
         "keywords": ["北京"], "method": "keyword"},
        {"id": "code_001", "category": "code", "input": "写一个 hello world",
         "keywords": ["print", "hello"], "method": "keyword"},
        {"id": "chat_001", "category": "chat", "input": "你好",
         "keywords": ["你好", "您好", "Hi"], "method": "keyword"},
    ],
}

def run_evaluation(agent_fn) -> dict:
    """运行评测"""
    results = []
    for case in GOLDEN_SET["cases"]:
        response = agent_fn(case["input"])
        keywords = case["keywords"]
        matched = sum(1 for kw in keywords if kw.lower() in response.lower())
        score = matched / len(keywords) if keywords else 0
        results.append({
            "id": case["id"],
            "category": case["category"],
            "score": score,
            "passed": score > 0,
            "response": response[:80],
        })

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    return {
        "total": total,
        "passed": passed,
        "pass_rate": passed / total if total else 0,
        "details": results,
    }
```

### 6.3 测试文件

```python
"""
共享 fixture
文件: tests/conftest.py
"""

import os
import pytest

@pytest.fixture(autouse=True)
def check_api_key():
    if not os.environ.get("ZHIPU_API_KEY"):
        pytest.skip("ZHIPU_API_KEY 未设置")

@pytest.fixture
def sample_queries():
    return [
        "1+1等于几？",
        "写一个 Python 排序函数",
        "你好",
        "什么是人工智能？",
    ]
```

```python
"""
Agent 测试
文件: tests/test_agent.py
"""

import pytest
from app.agent import agent

class TestAgentRouting:

    def test_qa_routing(self):
        result = agent.invoke({
            "messages": [], "query": "中国首都是哪？",
            "route": "", "result": "", "tokens_used": 0,
        })
        assert result["route"] in ["qa", "chat"]
        assert len(result["result"]) > 0

    def test_code_routing(self):
        result = agent.invoke({
            "messages": [], "query": "写一个 Python 函数",
            "route": "", "result": "", "tokens_used": 0,
        })
        assert len(result["result"]) > 0

    def test_chat_routing(self):
        result = agent.invoke({
            "messages": [], "query": "你好",
            "route": "", "result": "", "tokens_used": 0,
        })
        assert len(result["result"]) > 0

class TestAgentQuality:

    def test_qa_correctness(self):
        result = agent.invoke({
            "messages": [], "query": "2+3等于几？只回答数字",
            "route": "", "result": "", "tokens_used": 0,
        })
        assert "5" in result["result"]

    def test_code_has_function(self):
        result = agent.invoke({
            "messages": [], "query": "写一个 Python 函数计算两数之和",
            "route": "", "result": "", "tokens_used": 0,
        })
        assert "def" in result["result"]
```

### 6.4 评测脚本

```python
"""
评测脚本
文件: eval/run_eval.py
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import agent
from app.evaluator import run_evaluation

def agent_fn(query: str) -> str:
    result = agent.invoke({
        "messages": [], "query": query,
        "route": "", "result": "", "tokens_used": 0,
    })
    return result.get("result", "")

if __name__ == "__main__":
    print("=== Agent 评测 ===\n")
    report = run_evaluation(agent_fn)

    print(f"通过率: {report['passed']}/{report['total']} ({report['pass_rate']*100:.1f}%)")
    print()
    for r in report["details"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['id']} ({r['category']}): {r['response']}")

    # 保存报告
    with open("eval/report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n报告已保存: eval/report.json")
```

### Day 6 小结

```
Day 6 核心概念：
┌──────────────────────────────────────────────────┐
│  Agent 上线完整流程                                 │
│                                                    │
│  项目结构：                                         │
│  app/     → 生产代码（agent + cache + API）        │
│  tests/   → 测试代码（单元 + 集成）                │
│  eval/    → 评测数据集 + 评测脚本                  │
│  Docker   → 容器化部署                             │
│                                                    │
│  核心模块：                                         │
│  1. agent.py: LangGraph Agent（路由→执行→返回）    │
│  2. cache.py: LRU + TTL 缓存                       │
│  3. main.py: FastAPI 服务（含中间件）              │
│  4. evaluator.py: Golden Set 评测                  │
│                                                    │
│  生产级特性：                                       │
│  ✓ 路由分流（code/chat/qa）                       │
│  ✓ 缓存（减少重复调用）                            │
│  ✓ 日志（请求耗时记录）                            │
│  ✓ CORS（跨域支持）                                │
│  ✓ 异常处理（不暴露堆栈）                         │
│  ✓ 健康检查端点                                    │
│  ✓ Token 用量追踪                                  │
│  ✓ 延迟统计                                        │
│                                                    │
│  开发流程：                                         │
│  1. 编写 Agent → 2. 编写测试 → 3. 运行评测        │
│  → 4. Docker 化 → 5. 部署 → 6. 验证               │
└──────────────────────────────────────────────────┘
```

### Day 6 练习

1. 为项目添加 `/agent/eval` 端点——调用评测模块，返回当前 Agent 的评测报告
2. 在 Agent 中添加 `architect` 路由（架构设计类任务），并编写对应的测试
3. 添加 `config.py` 配置管理模块——从环境变量读取所有配置（模型名、温度、缓存大小等），支持 `.env` 文件

<details>
<summary>参考答案</summary>

```python
"""Day 6 练习答案"""

# === 练习 1：评测端点 ===
# 添加到 app/main.py

from app.evaluator import run_evaluation
from app.agent import agent

@app.post("/agent/eval")
async def evaluate_agent():
    """运行 Agent 评测"""
    def agent_fn(query: str) -> str:
        result = agent.invoke({
            "messages": [], "query": query,
            "route": "", "result": "", "tokens_used": 0,
        })
        return result.get("result", "")

    report = run_evaluation(agent_fn)
    return report


# === 练习 2：添加 architect 路由 ===
# 添加到 app/agent.py

def architect(state: AgentState) -> dict:
    """架构师节点"""
    llm = make_llm(0.1)
    resp = llm.invoke([HumanMessage(
        content=f"你是系统架构师。请设计架构方案:\n{state['query']}"
    )])
    tokens = 0
    if resp.usage_metadata:
        tokens = resp.usage_metadata.get("total_tokens", 0)
    return {
        "result": resp.content,
        "tokens_used": tokens,
        "messages": [AIMessage(content=resp.content, name="architect")],
    }

# 更新路由判断
def router(state: AgentState) -> dict:
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(
        content=f"判断任务类型，只回答一个词:\n"
                f"code（编程） / chat（闲聊） / qa（问答） / arch（架构设计）\n"
                f"任务: {state['query']}"
    )])
    route = resp.content.strip().lower()
    for r in ["code", "chat", "qa", "arch"]:
        if r in route:
            return {"route": r}
    return {"route": "chat"}

# 更新图
builder.add_node("arch", architect)
builder.add_conditional_edges("router", route_fn, {
    "coder": "coder", "chat": "chat", "qa": "qa", "arch": "arch",
})
builder.add_edge("arch", END)

# 测试
def test_architect_routing():
    result = agent.invoke({
        "messages": [], "query": "设计一个微服务架构",
        "route": "", "result": "", "tokens_used": 0,
    })
    assert len(result["result"]) > 0


# === 练习 3：配置管理 ===
# file: app/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置，从环境变量读取"""

    # LLM 配置
    model_name: str = "glm-4-flash"
    base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    api_key: str = ""
    temperature: float = 0.0

    # 缓存配置
    cache_max_size: int = 200
    cache_ttl: int = 600

    # API 配置
    api_port: int = 8000
    rate_limit_max: int = 10
    rate_limit_window: int = 60

    # 日志
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

</details>

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

```
Agent 评测指标：
[ ] 能说出 Agent 评测的三个层次（组件/端到端/在线）
[ ] 能实现关键词匹配评测
[ ] 能实现 LLM-as-Judge 评测
[ ] 能实现轨迹评测（工具调用路径）
[ ] 能构建 Golden Set 评测数据集

自动化测试：
[ ] 能用 pytest 编写 Agent 单元测试
[ ] 能编写 Agent 集成测试
[ ] 能编写回归测试（防退化）
[ ] 能用 conftest.py 共享 fixture
[ ] 能用 @pytest.mark.parametrize 参数化测试

性能优化：
[ ] 能用 asyncio.gather 并行调用 LLM
[ ] 能实现 LLM 响应缓存
[ ] 能追踪 API token 用量和成本
[ ] 能实现模型分级策略（简单/复杂任务用不同模型）

FastAPI 部署：
[ ] 能用 FastAPI 创建 Agent 服务
[ ] 能实现流式响应（SSE）
[ ] 能添加 CORS、日志、限流中间件
[ ] 能实现 API Key 认证

Docker 容器化：
[ ] 能编写 Dockerfile
[ ] 能编写 docker-compose.yml
[ ] 能用 .dockerignore 减小镜像体积
[ ] 能配置 Nginx 反向代理
[ ] 能编写部署验证脚本
```

### 7.2 综合练习题

**项目：Agent 上线完整方案**

为之前构建的任意一个 Agent（Week 5-7 中的）编写完整的上线方案：

1. **评测**：为 Agent 构建至少 10 条 Golden Set，包含 3 种评测方法
2. **测试**：编写至少 5 个 pytest 测试用例，覆盖正常和边界场景
3. **优化**：实现缓存 + 异步并行，量化性能提升
4. **部署**：FastAPI 服务化 + Docker 容器化
5. **监控**：健康检查 + 日志 + 评测端点

> 完成这个项目后，你就具备了 Agent 从开发到上线的完整工程能力。

<details>
<summary>参考答案框架</summary>

```python
"""
Agent 上线完整方案 - 答案框架
以 Week 6 的 ReAct Agent 为例
"""

import os
import sys
import time
import asyncio
import hashlib
import json
import pytest
from typing import TypedDict, Annotated
from operator import add
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage

# ============ 1. Agent 核心 ============

def make_llm(temp=0):
    return ChatOpenAI(
        model="glm-4-flash",
        base_url="https://open.bigmodel.cn/api/paas/v4",
        api_key=os.environ.get("ZHIPU_API_KEY"),
        temperature=temp,
    )

class ReActState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    query: str
    thought: str
    action: str
    observation: str
    answer: str
    iteration: int

def think(state: ReActState) -> dict:
    """ReAct: 思考阶段"""
    llm = make_llm(0)
    query = state["query"]
    iteration = state.get("iteration", 0)

    if iteration >= 3:  # 最多 3 轮
        resp = llm.invoke([HumanMessage(content=f"直接回答: {query}")])
        return {"answer": resp.content}

    prev = state.get("observation", "")
    prompt = f"""分析任务并决定下一步:
任务: {query}
{'上一步结果: ' + prev if prev else ''}

用 JSON 回答: {{"thought": "...", "action": "answer/observe"}}
action=answer 表示可以直接回答，action=observe 表示需要更多信息。"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    try:
        content = resp.content
        s, e = content.find("{"), content.rfind("}") + 1
        if s >= 0 and e > s:
            parsed = json.loads(content[s:e])
            return {"thought": parsed.get("thought", ""),
                    "action": parsed.get("action", "answer"),
                    "iteration": iteration + 1}
    except (json.JSONDecodeError, ValueError):
        pass
    return {"action": "answer", "iteration": iteration + 1}

def observe(state: ReActState) -> dict:
    """观察阶段（简化：用 LLM 获取信息）"""
    llm = make_llm(0)
    resp = llm.invoke([HumanMessage(content=f"查找信息: {state['query']}")])
    return {"observation": resp.content[:200]}

def answer(state: ReActState) -> dict:
    """回答阶段"""
    if state.get("answer"):
        return {}
    llm = make_llm(0)
    context = state.get("observation", "")
    prompt = f"回答问题: {state['query']}"
    if context:
        prompt += f"\n参考信息: {context[:300]}"
    resp = llm.invoke([HumanMessage(content=prompt)])
    return {"answer": resp.content}

def route(state: ReActState) -> str:
    if state.get("answer"):
        return "answer"
    if state.get("action") == "observe":
        return "observe"
    return "answer"

builder = StateGraph(ReActState)
builder.add_node("think", think)
builder.add_node("observe", observe)
builder.add_node("answer", answer)
builder.add_edge(START, "think")
builder.add_conditional_edges("think", route, {"observe": "observe", "answer": "answer"})
builder.add_edge("observe", "think")
builder.add_edge("answer", END)
react_agent = builder.compile(checkpointer=MemorySaver())

# ============ 2. 评测集 ============

GOLDEN_SET = [
    {"id": "g001", "input": "1+1=?", "keywords": ["2"], "method": "keyword"},
    {"id": "g002", "input": "中国首都是哪？", "keywords": ["北京"], "method": "keyword"},
    {"id": "g003", "input": "Python 的发明者？", "keywords": ["Guido"], "method": "keyword"},
    {"id": "g004", "input": "水由什么元素组成？", "keywords": ["氢", "氧", "H", "O"], "method": "keyword"},
    {"id": "g005", "input": "写一个 hello world", "keywords": ["print", "hello"], "method": "keyword"},
    {"id": "g006", "input": "地球绕太阳一圈多久？", "keywords": ["365", "一年", "年"], "method": "keyword"},
    {"id": "g007", "input": "list 和 tuple 区别", "keywords": ["可变", "不可变"], "method": "keyword"},
    {"id": "g008", "input": "什么是递归", "keywords": ["调用自身", "自己调用"], "method": "keyword"},
    {"id": "g009", "input": "翻译 Hello", "keywords": ["你好"], "method": "keyword"},
    {"id": "g010", "input": "True and False 等于？", "keywords": ["False"], "method": "keyword"},
]

def run_eval(agent_fn) -> dict:
    results = []
    for case in GOLDEN_SET:
        resp = agent_fn(case["input"])
        matched = sum(1 for kw in case["keywords"] if kw.lower() in resp.lower())
        score = matched / len(case["keywords"])
        results.append({"id": case["id"], "score": score, "passed": score > 0})
    passed = sum(1 for r in results if r["passed"])
    return {"total": len(results), "passed": passed, "pass_rate": passed / len(results)}

# ============ 3. 缓存 ============

class SimpleCache:
    def __init__(self, ttl=600):
        self.ttl = ttl
        self.cache = {}
        self.hits = 0
        self.misses = 0

    def get(self, key):
        if key in self.cache:
            val, ts = self.cache[key]
            if time.time() - ts < self.ttl:
                self.hits += 1
                return val
            del self.cache[key]
        self.misses += 1
        return None

    def set(self, key, val):
        self.cache[key] = (val, time.time())

    def stats(self):
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": self.hits / total if total else 0}

cache = SimpleCache()

# ============ 4. FastAPI 服务 ============

app = FastAPI(title="ReAct Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class QueryReq(BaseModel):
    query: str
    use_cache: bool = True

class QueryResp(BaseModel):
    answer: str
    cached: bool
    latency_ms: int

@app.get("/health")
async def health():
    return {"status": "ok", "cache": cache.stats()}

@app.post("/agent", response_model=QueryResp)
async def run(req: QueryReq):
    start = time.time()
    cached = False

    if req.use_cache:
        cached_ans = cache.get(req.query)
        if cached_ans is not None:
            cached = True
            return QueryResp(answer=cached_ans, cached=True,
                             latency_ms=int((time.time() - start) * 1000))

    result = await react_agent.ainvoke({
        "messages": [], "query": req.query, "thought": "",
        "action": "", "observation": "", "answer": "", "iteration": 0,
    })
    answer_text = result.get("answer", "")
    if req.use_cache and answer_text:
        cache.set(req.query, answer_text)

    return QueryResp(answer=answer_text, cached=cached,
                     latency_ms=int((time.time() - start) * 1000))

@app.post("/agent/eval")
async def eval_agent():
    def agent_fn(q):
        r = react_agent.invoke({
            "messages": [], "query": q, "thought": "",
            "action": "", "observation": "", "answer": "", "iteration": 0,
        })
        return r.get("answer", "")
    return run_eval(agent_fn)

@app.delete("/cache")
async def clear_cache():
    cache.cache.clear()
    cache.hits = 0
    cache.misses = 0
    return {"status": "cleared"}

# ============ 5. 测试（pytest）============

class TestReActAgent:

    def test_basic_qa(self):
        r = react_agent.invoke({
            "messages": [], "query": "1+1=?", "thought": "",
            "action": "", "observation": "", "answer": "", "iteration": 0,
        })
        assert "2" in r.get("answer", "")

    def test_knowledge(self):
        r = react_agent.invoke({
            "messages": [], "query": "中国首都是哪？", "thought": "",
            "action": "", "observation": "", "answer": "", "iteration": 0,
        })
        assert "北京" in r.get("answer", "")

    def test_code_generation(self):
        r = react_agent.invoke({
            "messages": [], "query": "写一个 hello world 函数", "thought": "",
            "action": "", "observation": "", "answer": "", "iteration": 0,
        })
        assert "def" in r.get("answer", "") or "print" in r.get("answer", "")

    def test_empty_query(self):
        """空查询不应崩溃"""
        r = react_agent.invoke({
            "messages": [], "query": "", "thought": "",
            "action": "", "observation": "", "answer": "", "iteration": 0,
        })
        assert "answer" in r

    def test_iteration_limit(self):
        """迭代限制：复杂问题不应无限循环"""
        r = react_agent.invoke({
            "messages": [], "query": "解释量子力学的测不准原理", "thought": "",
            "action": "", "observation": "", "answer": "", "iteration": 0,
        })
        assert len(r.get("answer", "")) > 0

# ============ 6. Docker 部署 ============
# Dockerfile、docker-compose.yml 参见 Day 5
# 部署验证: python deploy_check.py
```

</details>

### 7.3 Week 8 回顾与 6 个月学习总结

```
Week 8 学习路径回顾：

Day 1: Agent 评测指标体系
  → 关键词匹配、LLM-as-Judge、轨迹评测、Golden Set

Day 2: 自动化测试框架
  → pytest 单元/集成/回归测试、conftest fixture

Day 3: 性能优化与成本控制
  → 异步并行、缓存、成本追踪、模型分级

Day 4: FastAPI 部署
  → REST API、流式 SSE、中间件、错误处理

Day 5: Docker 容器化
  → Dockerfile、Compose、Nginx、部署验证

Day 6: 综合实战
  → 完整 Agent 项目：评测+测试+优化+部署

Day 7: 复习周测
  → 自测清单 + 综合项目


=== 6 个月学习计划完成总结 ===

Month 1: 基础筑基
  Week 1: Python 基础          → 变量/函数/类/异常/文件
  Week 2: LLM 核心原理         → API 调用/Token/Prompt/流式
  Week 3: Prompt Engineering   → 技巧/模板/思维链/角色扮演
  Week 4: RAG + Multi-Tool     → 向量检索/工具调用/ReAct

Month 2: 框架进阶
  Week 5: LangChain 框架       → LCEL/Runnable/工具/Agent
  Week 6: LangGraph 状态机     → StateGraph/条件路由/循环/子图
  Week 7: Multi-Agent 系统     → Supervisor/Swarm/Hierarchical
  Week 8: 评测与部署           → 评测/测试/优化/FastAPI/Docker


你已具备的能力：
✓ Python 编程基础
✓ LLM API 调用与 Prompt 工程
✓ RAG 系统构建（检索+生成）
✓ Tool-using Agent 开发
✓ LangChain/LangGraph 框架使用
✓ Multi-Agent 系统设计
✓ Agent 评测与自动化测试
✓ 性能优化与成本控制
✓ FastAPI 服务化
✓ Docker 容器化部署

下一步方向：
→ Agent 内存与长期记忆（Mem0/Zep）
→ Agent 工作流自动化（n8n/Dify）
→ Agent 安全与对齐
→ 多模态 Agent（图像/语音）
→ Agent 评测基准（AgentBench/SWE-bench）
```

---

## 本周知识图谱

```
Agent 评测与部署
├── 评测指标体系（Day 1）
│   ├── 准确性（关键词/精确匹配）
│   ├── 质量评分（LLM-as-Judge）
│   ├── 轨迹评测（工具调用路径）
│   └── Golden Set 数据集
│
├── 自动化测试（Day 2）
│   ├── pytest 单元测试
│   ├── 集成测试（管道/图）
│   ├── 回归测试（防退化）
│   ├── 性能测试（响应时间）
│   └── conftest.py 共享 fixture
│
├── 性能优化（Day 3）
│   ├── 异步并行（asyncio.gather）
│   ├── 缓存（LRU + TTL）
│   ├── 成本追踪（Token 计数）
│   └── 模型分级（简单/复杂路由）
│
├── FastAPI 部署（Day 4）
│   ├── REST API（Pydantic 模型）
│   ├── 流式响应（SSE）
│   ├── 中间件（CORS/日志/限流）
│   └── 错误处理
│
├── Docker 容器化（Day 5）
│   ├── Dockerfile（多阶段构建）
│   ├── docker-compose（多服务）
│   ├── Nginx 反向代理
│   └── 部署验证脚本
│
└── 综合实战（Day 6）
    ├── 项目结构（app/tests/eval）
    ├── Agent + Cache + API
    ├── 评测模块
    └── 端到端上线流程
```

## Agent 评测与部署速查表

```
┌──────────────────────────────────────────────────────────┐
│            Agent 评测与部署速查表                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  评测方法：                                               │
│  keyword_match: 检查关键词是否出现                        │
│  exact_match:   精确匹配（忽略大小写/空白）               │
│  llm_judge:     LLM 评分 1-5                             │
│  trajectory:    检查工具调用路径                          │
│                                                          │
│  pytest 关键命令：                                        │
│  pytest -v              # 详细输出                        │
│  pytest -k "test_name"  # 按名筛选                        │
│  pytest -x              # 首个失败即停                    │
│  pytest --tb=short      # 简短 traceback                  │
│  pytest -m "slow"       # 按标记筛选                      │
│                                                          │
│  性能优化：                                               │
│  asyncio.gather(*tasks)     # 并行调用                    │
│  llm.batch(inputs)          # 批量调用                    │
│  cache.get/set              # 缓存命中                     │
│  CostTracker.record()       # 记录 token                  │
│                                                          │
│  FastAPI 核心：                                           │
│  @app.get/post(path)        # 路由                        │
│  @app.middleware("http")    # 中间件                      │
│  StreamingResponse(gen)      # SSE 流式                   │
│  HTTPException(404)         # 错误响应                     │
│  BaseModel                   # 请求/响应模型               │
│                                                          │
│  Docker 命令：                                            │
│  docker build -t name .     # 构建镜像                    │
│  docker run -p 8000:8000    # 运行容器                    │
│  docker compose up -d       # 编排启动                    │
│  docker logs -f container   # 查看日志                    │
│  docker exec -it container  # 进入容器                    │
│                                                          │
│  部署检查清单：                                           │
│  [ ] /health 返回 200                                     │
│  [ ] /docs 可访问                                         │
│  [ ] POST /agent 返回正确结果                             │
│  [ ] SSE 流式正常                                         │
│  [ ] 日志正常输出                                         │
│  [ ] 缓存命中率 > 0                                       │
│  [ ] 评测通过率 > 80%                                     │
│                                                          │
└──────────────────────────────────────────────────────────┘
```
