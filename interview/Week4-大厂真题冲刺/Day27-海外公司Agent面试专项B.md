### Q9: 手撕代码题 — Production-grade Agent with Retry / Error Handling / Observability / Cost Tracking

**题目**: Implement a production-grade agent loop in Python with: (1) tool calling with retry and exponential backoff, (2) structured error handling, (3) observability (tracing/logging/metrics), (4) cost tracking (token usage and $ cost), (5) a max-steps guard, (6) duplicate-action detection. Use English comments. Make it runnable with a mock LLM.

<details>
<summary>查看答案</summary>

#### 完整实现

```python
"""
Production-grade Agent Loop.

Features:
  - Tool calling with retry + exponential backoff
  - Structured error handling (tool errors fed back to model)
  - Observability: structured logging, tracing spans, metrics
  - Cost tracking (token usage and dollar cost per call)
  - Max-steps guard (prevents infinite loops)
  - Duplicate-action detection (breaks stuck loops)

Run: python agent.py
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging: structured JSON lines for production observability.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='{"ts": "%(asctime)s", "level": "%(levelname)s", "msg": %(message)s}',
)
logger = logging.getLogger("agent")


# ---------------------------------------------------------------------------
# Cost model: price per 1M tokens (input, output). Extend as needed.
# ---------------------------------------------------------------------------
MODEL_PRICING = {
    "gpt-4o":      {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini": {"input": 0.15,  "output": 0.60},
    "claude-sonnet": {"input": 3.00, "output": 15.00},
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ToolCall:
    """A single tool invocation requested by the model."""
    call_id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """The outcome of executing a tool call."""
    call_id: str
    ok: bool
    content: str           # human/model-readable result or error description
    raw: Any = None         # optional structured payload


@dataclass
class Usage:
    """Token usage for one LLM call."""
    input_tokens: int = 0
    output_tokens: int = 0

    def cost(self, model: str) -> float:
        p = MODEL_PRICING.get(model, {"input": 0.0, "output": 0.0})
        return (self.input_tokens * p["input"] + self.output_tokens * p["output"]) / 1_000_000


@dataclass
class Span:
    """A tracing span for observability."""
    span_id: str
    name: str
    start: float
    end: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    status: str = "ok"

    def finish(self, status: str = "ok") -> None:
        self.end = time.time()
        self.status = status

    def duration_ms(self) -> float:
        return ((self.end or time.time()) - self.start) * 1000


@dataclass
class AgentMetrics:
    """Aggregate metrics for a single agent run."""
    llm_calls: int = 0
    tool_calls: int = 0
    tool_failures: int = 0
    tool_retries: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    steps: int = 0
    elapsed_ms: float = 0.0

    def summary(self) -> str:
        return (
            f"steps={self.steps} llm_calls={self.llm_calls} "
            f"tool_calls={self.tool_calls} tool_failures={self.tool_failures} "
            f"tool_retries={self.tool_retries} "
            f"tokens={self.total_input_tokens}+{self.total_output_tokens} "
            f"cost=${self.total_cost:.4f} elapsed={self.elapsed_ms:.0f}ms"
        )


# ---------------------------------------------------------------------------
# Tool registry: each tool is a function + a JSON-schema-ish description.
# ---------------------------------------------------------------------------
ToolFn = Callable[[Dict[str, Any]], Any]


@dataclass
class Tool:
    name: str
    description: str
    parameters: Dict[str, Any]      # JSON schema (simplified)
    fn: ToolFn
    max_retries: int = 3
    base_backoff: float = 0.5       # seconds


class ToolRegistry:
    """Registry of tools available to the agent."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def schemas(self) -> List[Dict[str, Any]]:
        """Return tool definitions in the format the LLM API expects."""
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
class AgentError(Exception):
    """Base error for agent-level failures."""


class MaxStepsExceeded(AgentError):
    pass


class DuplicateActionDetected(AgentError):
    pass


class ToolExecutionError(Exception):
    """Raised when a tool ultimately fails after all retries."""

    def __init__(self, tool_name: str, last_error: str) -> None:
        super().__init__(f"Tool '{tool_name}' failed: {last_error}")
        self.tool_name = tool_name
        self.last_error = last_error


# ---------------------------------------------------------------------------
# LLM client abstraction. In production, swap MockLLM for the real SDK.
# ---------------------------------------------------------------------------
class LLMClient:
    """Interface for an LLM that supports tool calling."""

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
             model: str) -> Tuple[str, List[ToolCall], Usage]:
        raise NotImplementedError


class MockLLM(LLMClient):
    """
    Deterministic mock LLM for testing.

    It produces a scripted sequence of tool calls, then a final answer.
    This lets the whole agent loop run end-to-end without network access.
    """

    def __init__(self, script: List[Tuple[str, List[ToolCall]]]) -> None:
        # Each script entry: (text_response, tool_calls)
        self._script = script
        self._idx = 0

    def chat(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]],
             model: str) -> Tuple[str, List[ToolCall], Usage]:
        if self._idx >= len(self._script):
            # Default: no more tool calls, return a done message.
            return "Task completed.", [], Usage(input_tokens=500, output_tokens=20)
        text, calls = self._script[self._idx]
        self._idx += 1
        # Simulate realistic token usage.
        usage = Usage(input_tokens=800 + 50 * len(messages), output_tokens=50 + 30 * len(calls))
        return text, calls, usage


# ---------------------------------------------------------------------------
# The Agent
# ---------------------------------------------------------------------------
class Agent:
    """
    A production-grade ReAct-style agent loop.

    Flow per step:
      1. Call LLM with conversation + tool schemas.
      2. If LLM returns tool calls, execute them (with retry/backoff).
      3. Append tool results to the conversation.
      4. Repeat until LLM returns no tool calls (final answer) or limits hit.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        model: str = "gpt-4o",
        max_steps: int = 15,
        max_duplicate_actions: int = 3,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.model = model
        self.max_steps = max_steps
        self.max_duplicate_actions = max_duplicate_actions
        # Observability
        self.metrics = AgentMetrics()
        self.spans: List[Span] = []
        # Duplicate detection: track (tool_name, arguments_frozen) counts.
        self._action_counter: Counter = Counter()

    # -- public API --------------------------------------------------------
    def run(self, user_query: str) -> str:
        """Run the agent on a user query; return the final text answer."""
        run_start = time.time()
        root_span = self._start_span("agent.run", {"query": user_query})
        logger.info(json.dumps({"event": "agent.run.start", "query": user_query}))

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": "You are a helpful agent. Use tools when needed. "
                                          "When the task is complete, respond with the final answer and no tool calls."},
            {"role": "user", "content": user_query},
        ]

        try:
            final_text = self._loop(messages)
            root_span.finish("ok")
            logger.info(json.dumps({"event": "agent.run.ok", "answer": final_text[:200]}))
            return final_text
        except AgentError as exc:
            root_span.finish("error")
            logger.error(json.dumps({"event": "agent.run.error", "error": str(exc)}))
            raise
        finally:
            self.metrics.elapsed_ms = (time.time() - run_start) * 1000
            logger.info(json.dumps({"event": "agent.run.metrics", "summary": self.metrics.summary()}))
            self.spans.append(root_span)

    # -- core loop ---------------------------------------------------------
    def _loop(self, messages: List[Dict[str, Any]]) -> str:
        for step in range(1, self.max_steps + 1):
            self.metrics.steps = step
            step_span = self._start_span("agent.step", {"step": step})

            text, tool_calls, usage = self._call_llm(messages)
            self._record_usage(usage)
            messages.append({"role": "assistant", "content": text, "tool_calls": tool_calls})

            logger.info(json.dumps({
                "event": "step", "step": step,
                "tool_calls": [c.name for c in tool_calls],
                "tokens_in": usage.input_tokens, "tokens_out": usage.output_tokens,
            }))

            if not tool_calls:
                # No tool calls means the model produced the final answer.
                step_span.finish("ok")
                self.spans.append(step_span)
                return text

            # Execute tool calls and feed results back.
            for call in tool_calls:
                self._check_duplicate(call)
                result = self._execute_tool(call)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.call_id,
                    "name": call.name,
                    "content": result.content,
                })

            step_span.finish("ok")
            self.spans.append(step_span)

        # Exhausted steps.
        raise MaxStepsExceeded(
            f"Agent exceeded max_steps={self.max_steps} without producing a final answer."
        )

    # -- LLM call ----------------------------------------------------------
    def _call_llm(self, messages: List[Dict[str, Any]]) -> Tuple[str, List[ToolCall], Usage]:
        llm_span = self._start_span("llm.chat", {"model": self.model})
        try:
            text, raw_calls, usage = self.llm.chat(
                messages=messages, tools=self.tools.schemas(), model=self.model
            )
            llm_span.attributes["input_tokens"] = usage.input_tokens
            llm_span.attributes["output_tokens"] = usage.output_tokens
            llm_span.finish("ok")
            self.spans.append(llm_span)
            self.metrics.llm_calls += 1
            return text, raw_calls, usage
        except Exception as exc:
            llm_span.finish("error")
            self.spans.append(llm_span)
            # In production: retry the LLM call itself, fallback model, etc.
            raise AgentError(f"LLM call failed: {exc}") from exc

    # -- tool execution with retry ----------------------------------------
    def _execute_tool(self, call: ToolCall) -> ToolResult:
        tool = self.tools.get(call.name)
        if tool is None:
            # Unknown tool: feed the error back to the model so it can recover.
            self.metrics.tool_failures += 1
            return ToolResult(call_id=call.call_id, ok=False,
                              content=f"Error: tool '{call.name}' is not available. "
                                      f"Available tools: {list(self.tools._tools.keys())}")

        tool_span = self._start_span("tool.exec", {"tool": call.name, "args": call.arguments})
        last_error = ""
        for attempt in range(1, tool.max_retries + 1):
            try:
                raw = tool.fn(call.arguments)
                content = self._stringify(raw)
                tool_span.finish("ok")
                self.spans.append(tool_span)
                self.metrics.tool_calls += 1
                logger.info(json.dumps({
                    "event": "tool.ok", "tool": call.name,
                    "attempt": attempt, "content_preview": content[:200],
                }))
                return ToolResult(call_id=call.call_id, ok=True, content=content, raw=raw)
            except Exception as exc:
                # Catch a broad but explicit set; never use bare except in production.
                last_error = f"{type(exc).__name__}: {exc}"
                self.metrics.tool_retries += 1
                logger.warning(json.dumps({
                    "event": "tool.retry", "tool": call.name,
                    "attempt": attempt, "error": last_error,
                }))
                if attempt < tool.max_retries:
                    backoff = tool.base_backoff * (2 ** (attempt - 1))
                    time.sleep(min(backoff, 10.0))  # cap backoff at 10s

        # All retries exhausted.
        self.metrics.tool_failures += 1
        tool_span.finish("error")
        self.spans.append(tool_span)
        # Feed a structured, model-actionable error back rather than crashing.
        return ToolResult(
            call_id=call.call_id, ok=False,
            content=f"Error: tool '{call.name}' failed after {tool.max_retries} attempts. "
                    f"Last error: {last_error}. Please try a different approach.",
        )

    # -- helpers -----------------------------------------------------------
    @staticmethod
    def _stringify(raw: Any) -> str:
        if isinstance(raw, str):
            return raw
        try:
            return json.dumps(raw, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            return str(raw)

    def _record_usage(self, usage: Usage) -> None:
        self.metrics.total_input_tokens += usage.input_tokens
        self.metrics.total_output_tokens += usage.output_tokens
        self.metrics.total_cost += usage.cost(self.model)

    def _check_duplicate(self, call: ToolCall) -> None:
        """Detect when the agent repeats the same action too many times."""
        key = (call.name, json.dumps(call.arguments, sort_keys=True))
        self._action_counter[key] += 1
        if self._action_counter[key] > self.max_duplicate_actions:
            raise DuplicateActionDetected(
                f"Agent called {call.name} with identical arguments "
                f"{self._action_counter[key]} times. Likely stuck in a loop."
            )

    def _start_span(self, name: str, attrs: Optional[Dict[str, Any]] = None) -> Span:
        return Span(span_id=uuid.uuid4().hex[:8], name=name, start=time.time(),
                    attributes=attrs or {})


# ---------------------------------------------------------------------------
# Example tools (mocked so the script runs standalone).
# ---------------------------------------------------------------------------
def mock_search(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query", "")
    if not query:
        raise ValueError("query is required")
    # Simulate occasional flakiness to exercise retry logic.
    if "flaky" in query.lower():
        if time.time() % 1 < 0.5:  # roughly 50% failure
            raise RuntimeError("transient search backend error")
    return {"results": [f"{query} result 1", f"{query} result 2"], "count": 2}


def mock_calculator(args: Dict[str, Any]) -> Dict[str, Any]:
    expr = args.get("expression", "")
    if not expr:
        raise ValueError("expression is required")
    # VERY limited safe evaluator for demo only.
    allowed = set("0123456789+-*/(). ")
    if not set(expr) <= allowed:
        raise ValueError("expression contains disallowed characters")
    result = eval(expr, {"__builtins__": {}}, {})  # noqa: S307 (sandboxed demo)
    return {"expression": expr, "result": float(result)}


def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(Tool(
        name="search",
        description="Search the web for information. Input: {query: string}.",
        parameters={"type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"]},
        fn=mock_search,
        max_retries=3,
        base_backoff=0.1,
    ))
    reg.register(Tool(
        name="calculator",
        description="Evaluate a math expression. Input: {expression: string}.",
        parameters={"type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"]},
        fn=mock_calculator,
        max_retries=2,
        base_backoff=0.1,
    ))
    return reg


# ---------------------------------------------------------------------------
# Demo run
# ---------------------------------------------------------------------------
def main() -> None:
    # Script the mock LLM: step 1 calls search, step 2 calls calculator,
    # step 3 returns the final answer with no tool calls.
    script = [
        ("I'll search for the latest model pricing.", [
            ToolCall(call_id="c1", name="search", arguments={"query": "GPT-4o pricing"}),
        ]),
        ("Now let me compute the monthly cost for 10M tokens.", [
            ToolCall(call_id="c2", name="calculator", arguments={"expression": "2.5 * 10 + 10 * 2"}),
        ]),
        ("Based on the search and calculation, the estimated monthly cost is $45 for 10M tokens (10M input at $2.5/M + 2M output at $10/M).", []),
    ]
    llm = MockLLM(script)
    agent = Agent(llm=llm, tools=build_registry(), model="gpt-4o", max_steps=10)

    answer = agent.run("What is the monthly cost of using GPT-4o for 10M input and 2M output tokens?")
    print("FINAL ANSWER:")
    print(answer)
    print("\nMETRICS:")
    print(agent.metrics.summary())
    print("\nTRACE SPANS:")
    for s in agent.spans:
        dur = f"{s.duration_ms():.1f}ms"
        print(f"  {s.name:20s} {s.status:6s} {dur:10s} attrs={s.attributes}")


if __name__ == "__main__":
    main()
```

#### 设计要点说明

1. **Retry with exponential backoff**: `_execute_tool` 重试 `max_retries` 次,backoff = `base_backoff * 2^(attempt-1)`,封顶 10s。区分可重试错误(网络、超时)和不可重试错误(参数错误)是生产中的下一步优化(此处简化)。
2. **Structured error feedback**: 工具失败不 crash,而是把可读的错误信息作为 `tool` message 喂回模型,让模型自行恢复(换工具/换参数/放弃)。这是 ReAct 范式的关键。
3. **Observability**: 三层 — (a) 结构化 JSON 日志(便于 ELK/Loki 摄取),(b) tracing spans(便于 Jaeger/Tempo 链路分析),(c) 聚合 metrics(便于 Prometheus/Grafana 监控)。
4. **Cost tracking**: `Usage.cost()` 按模型定价表计算;每次 LLM 调用累加。生产中还需:按租户/用户/会话维度聚合、预算熔断。
5. **Max-steps guard**: 防止模型无限调工具不收敛。15 步是常见默认值,复杂任务可调高。
6. **Duplicate detection**: 同一 (tool, args) 出现超过阈值即中断 — 这是最常见的"agent 卡死"模式。
7. **Mock LLM**: 用脚本化 mock 让整个 loop 可离线运行,便于 CI/单元测试。生产中替换为真实 SDK 即可。

#### 追问:如何扩展到生产

- **真实 LLM 集成**: 实现 `LLMClient` 的真实版本(OpenAI/Anthropic SDK),处理流式、限流、多 provider fallback。
- **并发工具执行**: 同一轮多个 tool_calls 无依赖时可并行(`asyncio.gather`)。
- **持久化 trace**: spans 写入 OTel collector,而非内存列表。
- **Budget enforcement**: 在 `_record_usage` 中检查累计成本,超预算抛 `BudgetExceeded`。
- **Streaming**: 改为流式 LLM 输出,首字延迟更低;但工具调用解析更复杂。

</details>

---

### Q10: 系统设计题 — "Design an AI agent platform for enterprise customers (multi-tenant / security / compliance / cost management)" — Microsoft / Google 真题风格

**题目**: Design a multi-tenant AI agent platform that enterprises can use to build, deploy, and operate custom agents on their own data. Requirements: each tenant's data is isolated; compliance with GDPR/SOC2/HIPAA; per-tenant cost tracking and budgets; ability to connect agents to enterprise systems (SharePoint, Salesforce, internal APIs); and a control plane for admins to govern agent behavior. This is a Microsoft Copilot / Google Vertex AI Agent Builder / AWS Bedrock Agents style question.

<details>
<summary>查看答案</summary>

#### Step 1: Clarify Requirements

**Functional**:
- Tenants (enterprises) self-service create agents: define tools, connect data sources, configure behavior
- Agents answer questions and take actions over enterprise data (RAG + tool-use)
- Admin controls: approve agents, set allowed tools, audit logs, data residency
- Developer experience: SDK + console + APIs
- Integrations: SharePoint, Salesforce, ServiceNow, Jira, custom REST/SQL

**Non-functional**:
- Multi-tenant isolation: tenant A cannot access tenant B's data, ever
- Compliance: GDPR (right to deletion, data residency), SOC2 (audit trails), HIPAA (PHI handling) optional per tenant
- Scale: 1000 tenants, each with 1-100 agents, each agent serving 1-10K users
- Cost: per-tenant metering and billing; budgets with soft/hard caps
- Latency: p95 < 3s for chat responses
- Availability: 99.9% for control plane, 99.5% for data plane

**Assumptions**:
- "I'll assume a B2B SaaS model: we host the platform; tenants' data may be in our cloud or bring-your-own-cloud."
- "I'll assume agents are primarily RAG + tool-use over enterprise data, not autonomous web agents."

#### Step 2: Architecture Overview

```
                         ┌──────────────────────────┐
                         │   Tenant Admin Console    │  (per-tenant UI)
                         │   - Create/manage agents  │
                         │   - Connect data sources  │
                         │   - Set policies/budgets  │
                         └────────────┬─────────────┘
                                      │
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐    │
│  │ Tenant   │ │ Agent    │ │ Policy   │ │ Billing &     │    │
│  │ Mgmt     │ │ Registry │ │ Engine   │ │ Metering      │    │
│  └──────────┘ └──────────┘ └──────────┘ └───────────────┘    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                      │
│  │ Auth &   │ │ Audit    │ │ Connector│                      │
│  │ RBAC     │ │ Log      │ │ Catalog  │                      │
│  └──────────┘ └──────────┘ └──────────┘                      │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      │ deploy agent config
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Plane (per-request)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Gateway      │─▶│ Agent        │─▶│ Tool Executor    │    │
│  │ (auth,       │  │ Runtime      │  │ (connectors)     │    │
│  │  rate limit, │  │ (LLM + RAG + │  │                  │    │
│  │  tenant      │  │  orchestrate)│  │                  │    │
│  │  routing)    │  │              │  │                  │    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
│         │                 │                    │             │
│         ▼                 ▼                    ▼             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │ Tenant Data  │  │ Vector Index │  │ Connector Pool   │    │
│  │ Isolation    │  │ (per-tenant) │  │ (SharePoint,     │    │
│  │ Layer        │  │              │  │  Salesforce, ...)│    │
│  └──────────────┘  └──────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Cross-cutting: Observability (logs/metrics/traces),         │
│  Audit Log (immutable, per-tenant), Cost Metering            │
└─────────────────────────────────────────────────────────────┘
```

#### Step 3: Multi-Tenancy & Isolation (核心难点)

Isolation is the #1 enterprise concern. Three strategies, increasing isolation / cost:

| Strategy | Isolation | Cost | Complexity | When to use |
|----------|-----------|------|-----------|-------------|
| Shared everything (logical isolation) | Low | Low | Low | Small tenants, non-sensitive |
| Shared DB, per-tenant schema/namespace | Medium | Medium | Medium | Default for most tenants |
| Dedicated infra per tenant (silos) | High | High | High | Regulated / large tenants |

**Recommended: hybrid (tiered)**:
- Default: logical isolation with strict tenant_id enforcement on every query + per-tenant encryption keys
- For regulated tenants (HIPAA, govt): dedicated data plane deployment (separate cluster, separate KMS keys, optional bring-your-own-cloud)

**Implementation details**:
- Every record carries `tenant_id`; every DB query includes `WHERE tenant_id = ?` enforced at the ORM/data-access layer (not application code — defense in depth)
- Per-tenant encryption keys (envelope encryption via KMS): even if data leaks, it's unusable without the tenant's key
- Vector index: per-tenant namespaces or per-tenant indexes (shared index with tenant_id filter is cheaper but riskier; per-tenant index is safer)
- Connector credentials: stored in a per-tenant secrets vault; the runtime fetches credentials scoped to the current request's tenant

#### Step 4: Security & Compliance

**Authentication & Authorization**:
- Tenant users auth via their IdP (Azure AD, Okta, Google) — SSO/SAML/OIDC
- Platform auth: OAuth2 + scoped tokens; service-to-service uses mTLS
- RBAC: roles per tenant (admin, developer, end-user); agents inherit the calling user's permissions (agent acts "as" the user — critical for least privilege)

**Data Security**:
- Encryption at rest (per-tenant keys) and in transit (TLS 1.3)
- DLP (Data Loss Prevention): scan agent outputs for sensitive data leakage (SSNs, credit cards) before returning to user
- Prompt injection defense: enterprise data is untrusted input; delimit and instruct model to treat as data
- No cross-tenant data in prompts: the RAG retrieval is strictly scoped to the tenant's index; tool execution uses tenant-scoped credentials

**Compliance**:
- GDPR: data residency (deploy data plane in tenant's region); right to deletion (cascade delete tenant data including vector indexes and logs); data processing agreements
- SOC2: immutable audit logs (append-only, tamper-evident — e.g., backed by a hash chain or blockchain-style ledger); access logging; change management
- HIPAA (opt-in tier): BAA with the tenant; PHI tagging and extra access controls; audit log retention 6+ years
- Audit log: every agent action (tool call, data access, output) logged with (tenant_id, user_id, agent_id, timestamp, action, result_hash) — queryable by tenant admins and exportable for compliance

**Data Residency**:
- Tenant chooses region at provisioning; all data (docs, vectors, logs, backups) stays in that region
- Model inference: route to a provider endpoint in the same region, or self-host the model in-region for strict requirements

#### Step 5: Cost Management & Metering

**Metering dimensions**:
| Dimension | Unit | Notes |
|-----------|------|-------|
| LLM tokens | per 1K tokens | input/output separately; per model |
| Vector index storage | GB-month | per-tenant index size |
| Connector API calls | per call | proxy through platform |
| Agent invocations | per request | platform overhead |
| Data ingestion | per GB | document processing pipeline |

**Billing pipeline**:
```
Agent Runtime → emit usage events → Metering Queue (Kafka) →
Aggregation Service (per-tenant rollups) → Billing DB →
Invoice Generation + Budget Enforcement
```

**Budget enforcement**:
- Each tenant sets monthly budgets (per agent or aggregate)
- Soft cap (80%): alert admins
- Hard cap (100%): throttle or pause non-critical agents; always allow admin to increase budget
- Per-request pre-check: estimate cost before executing (based on context length); reject if over remaining budget — prevents surprise overages

**Cost allocation**:
- Tag agents with cost centers (tenant-configured)
- Reports: cost by agent, by user, by tool, by day — exportable for tenant's internal chargeback

#### Step 6: Connector Architecture

Connectors let agents access enterprise systems. Design:

- **Connector Catalog**: registry of supported connectors (SharePoint, Salesforce, ServiceNow, Jira, custom REST, SQL, Snowflake)
- **Per-tenant connector config**: credentials (in vault), sync schedule, data scope (which sites/objects)
- **Sync vs on-demand**:
  - Sync: periodically index data into the tenant's vector store (better latency, stale risk)
  - On-demand: query the source at request time (fresh, slower) — use for transactional data (e.g., "what's the status of ticket X?")
  - Hybrid: sync for knowledge base, on-demand for live data
- **Connector permissions**: connector runs with the tenant's OAuth tokens (delegated permissions); the agent's data access is bounded by what the connector has access to
- **Custom connectors**: tenants build connectors via a SDK (OpenAPI spec → auto-generated connector); platform reviews/publishes

#### Step 7: Agent Governance (Control Plane)

Tenant admins need to govern agent behavior without code changes:

- **Tool allowlist**: admin approves which tools each agent can use (prevent an agent from calling a deletion API)
- **Model allowlist**: admin chooses which models (e.g., disallow certain models for compliance)
- **Guardrail policies**: input/output content filters (profanity, PII, confidential info) configurable per agent
- **Approval workflow**: new agents or agent changes require admin approval before production
- **Audit & observability**: admin can view all agent interactions, filter by user/agent/time, export for compliance
- **Kill switch**: admin can instantly disable an agent (e.g., if it's behaving incorrectly) — propagates to data plane in < 10s

#### Step 8: Failure Modes & Mitigations

| Failure | Mitigation |
|---------|-----------|
| Cross-tenant data leak (worst case) | Defense in depth: tenant_id on every record + per-tenant encryption keys + per-tenant indexes + automated tests that attempt cross-tenant access in CI |
| Connector credential leak | Credentials only in secrets vault; never logged; rotate automatically; audit all credential access |
| LLM provider outage | Multi-provider routing; fallback models; graceful degradation (RAG-only if LLM down) |
| Runaway cost (agent loops) | Per-request token budget + max-steps + duplicate detection (as in Q9) + hard tenant budget cap |
| Compliance audit failure | Immutable audit log + automated compliance checks in CI + third-party auditor (SOC2) |
| Tenant onboarding bottleneck | Self-service provisioning; automated data residency setup; templated agent configurations |

#### Step 9: Trade-offs & Evolution

- **Trade-off: shared vs dedicated infra** — shared is cheaper but requires ironclad logical isolation; dedicated is expensive but simplifies compliance. Start shared with tiered dedicated for high-needs tenants.
- **Trade-off: sync vs on-demand connectors** — sync is fast but stale; on-demand is fresh but slow and rate-limited by the source. Hybrid per data type.
- **Trade-off: platform-managed vs bring-your-own LLM** — platform-managed is simpler; BYO-LLM (tenant deploys their own model) gives control for regulated industries. Support both.
- **Evolution**: (1) agent marketplace (tenants share agent templates); (2) fine-tuning service (tenant-specific models on their data, isolated); (3) human-in-the-loop workflows (agents escalate to human reviewers for sensitive actions); (4) cross-agent collaboration within a tenant (multiple specialized agents cooperate).

#### 一句话总结

"The platform is a multi-tenant control plane (tenant/agent/policy/billing management) and a per-request data plane (agent runtime + connectors + per-tenant data isolation). The hardest problems are ironclad tenant isolation (enforced at data layer + per-tenant encryption keys), compliance (immutable audit logs, data residency, GDPR deletion), and cost governance (metering + budget enforcement + pre-request cost checks). The architectural pattern is tiered isolation: shared infra by default, dedicated deployments for regulated tenants."

</details>

---

## 核心知识回顾表

| 主题 | 核心要点 | 一句话记忆 |
|------|---------|-----------|
| 海外面试流程 | OpenAI重研究品味、Anthropic重安全价值观、DeepMind重学术严谨、Meta重规模工程、Microsoft重企业场景 | 五家文化不同,准备策略各异 |
| CAI vs RLHF | CAI用AI judge+宪法替代人类标注;两阶段=critique-revise(SFT)+RLAIF(RL) | 宪法替代人类标注,AI judge自己教自己 |
| Multi-Agent Research | 层级架构:PI编排+文献/假设/实验/审稿/写作/验证agent;强制独立复现 | 研究agent必须有独立验证,否则会造假 |
| Tool Use 对比 | GPT-4用JSON tool_calls+strict mode;Claude用content blocks混排text+tool_use | 都post-trained,格式不同,ACI设计是关键 |
| Agent Eval | 四层:单元/轨迹/在线/元评估;LLM-as-judge需防self-preference | eval自己也要eval,离线指标要与在线相关 |
| Long Context | 丢失中间、上下文稀释、成本爆炸;用层级摘要+选择性加载的混合方案 | 长上下文不等于用得好,层级摘要+选择性加载 |
| Web Agent | 感知(AX tree+截图)→规划→低层动作→验证;不可逆动作必须确认门;页面内容是不可信输入 | 网页内容是prompt injection来源,不可逆动作必须人工确认 |
| Production Agent | retry+backoff、错误喂回模型、结构化日志+trace+metrics、成本追踪、max-steps、重复检测 | 生产agent六件套:重试、容错、可观测、成本、限步、防循环 |
| Enterprise Platform | 多租户隔离(逻辑+加密密钥)、合规(审计日志/数据驻留)、成本计量+预算熔断、连接器架构、治理控制面 | 企业agent平台=隔离+合规+成本+治理,隔离是第一要务 |
| 英文面试表达 | STAR/CIRCLES框架、假设驱动、量化估算、权衡分析、坦诚不确定 | 结构化表达+假设驱动+量化估算 |

---

## 面试速记卡 — 英文面试关键术语和表达

### 开场与框架

| 场景 | 英文表达 |
|------|---------|
| 开始系统设计 | "Let me start by clarifying the requirements, then I'll outline the architecture, and we can dive deeper where you'd like." |
| 做假设 | "I'm going to assume X — happy to revisit if that's off." / "Let me state my assumptions up front: ..." |
| 量化估算 | "Let me do a quick back-of-the-envelope calculation: ..." / "Roughly speaking, that's about X per day." |
| 讨论权衡 | "The trade-off here is between A and B. I'd lean toward A because ..., but the cost is ..." |
| 承认不确定 | "I'm not 100% sure, but my intuition is ... I'd verify by ..." / "I don't know the exact number, but I'd estimate it at ..." |
| 收尾 | "To summarize, the key design decisions are ... The biggest risk is ... A natural next step would be ..." |
| 反问 | "Could you tell me more about how the team evaluates agent quality in production?" |

### 技术术语

| 术语 | 含义 |
|------|------|
| idempotent | 幂等的(重复执行结果相同) |
| backpressure | 背压(下游过载时反向施压) |
| eventual consistency | 最终一致性 |
| defense in depth | 纵深防御(多层安全) |
| blast radius | 影响半径(故障波及范围) |
| graceful degradation | 优雅降级 |
| canary deployment | 金丝雀发布 |
| shadow deployment | 影子部署(并行不暴露) |
| prompt injection | 提示注入攻击 |
| PII / DLP | 个人身份信息 / 数据防泄漏 |
| SOC2 / GDPR / HIPAA | 合规框架 |
| multi-tenant isolation | 多租户隔离 |
| envelope encryption | 信封加密(用DEK加密数据,KEK加密DEK) |
| RAG / long-context | 检索增强生成 / 长上下文 |
| trajectory | 轨迹(agent的动作序列) |
| LLM-as-judge | 用LLM做评估裁判 |
| self-preference | 自我偏好(judge偏向同族模型) |
| Constitutional AI | 宪法AI |
| RLAIF | AI反馈强化学习 |
| ACI (Agent-Computer Interface) | 智能体-计算机界面(工具描述即UI) |

### 高频追问英文应答模板

- "That's a great question. Let me think about the failure mode you're pointing at..." (争取思考时间)
- "There are a few ways to handle this. The simplest is X, but if we need more robustness, we could Y." (分层回答)
- "In practice, I'd start with X and evolve to Y once we have data on the failure rate." (展示演进思维)
- "The key assumption here is X. If that doesn't hold, the approach would need to change to Y." (暴露假设)

---

## 易错点提醒(10个)

1. **把"长上下文窗口"等同于"能用好长上下文"**: 200K context 不代表模型能均匀注意所有内容。Lost-in-the-middle 问题真实存在,生产中必须用层级摘要+选择性加载,而非暴力全塞。海外面试官特别爱考这个误区。

2. **混淆 RLHF 和 RLAIF**: RLHF 用人类标注做偏好数据;RLAIF 用 AI judge(参考宪法或标准)做偏好数据。CAI 的 Phase 2 是 RLAIF,不是 RLHF。说错会被认为没读论文。

3. **Web agent 忽略 prompt injection 来自网页本身**: 网页内容是不可信输入。一个恶意页面可以包含"ignore previous instructions"。必须用分隔符标记+意图校验+输出过滤的纵深防御。

4. **Agent eval 只看离线指标,不验证离线-在线相关性**: 离线 task-success-rate 涨了,但在线 CSAT 没涨 → 离线指标在被 gaming。必须做 meta-eval,定期校准。

5. **LLM-as-judge 不防 self-preference**: 用 GPT-4 judge 评 GPT-4 生成的输出,会有自我偏好。要用不同模型族做 judge,并用人类标注定期校准 judge-human agreement。

6. **企业平台多租户隔离只靠应用层 tenant_id**: 这不够。必须在数据层强制(ORM/查询层注入 tenant_id)、加密层隔离(每租户独立密钥)、向量索引隔离(每租户独立索引或命名空间)。应用层 bug 不应导致跨租户泄漏。

7. **生产 agent 没有重复动作检测**: agent 反复调用同一工具同一参数是最常见的"卡死"模式。max-steps 只防无限循环,不防"转圈"。必须加 (tool, args) 重复计数检测。

8. **英文面试不暴露假设、不量化估算**: 海外面试官期望你主动说"I'm assuming X, which gives us about Y per day"。沉默地画图不说话是大忌。要边画边说,假设驱动。

9. **把 Constitutional AI 说成"只是 prompt engineering"**: CAI 的 Phase 1 是 SFT(用 critique-revise 数据微调),Phase 2 是 RL(用 AI 偏好数据训练 reward model + PPO/DPO)。它是训练方法,不是运行时 prompt。说成 prompt 会被认为没理解本质。

10. **Multi-agent research 设计忽略"独立验证"**: 没有 Verifier Agent 独立复现实验,系统可以伪造结果。这是信任的基石。设计自主研究系统时,独立验证是 mandatory,不是 optional。

---

## 自测检查清单

### 概念题(10个)

- [ ] 能用英文说出 OpenAI / Anthropic / DeepMind / Meta / Microsoft 各自的面试 loop 和文化关键词
- [ ] 能解释 Constitutional AI 的两个阶段(critique-revise SFT + RLAIF),并说清与 RLHF 的区别
- [ ] 能画出 multi-agent 自主研究系统的架构,并指出"独立验证"为何 mandatory
- [ ] 能对比 GPT-4 和 Claude 的 tool-use 机制(JSON tool_calls vs content blocks),并说出 ACI 概念
- [ ] 能说出 agent eval 的四层(单元/轨迹/在线/元评估)和 LLM-as-judge 的三个坑(self-preference/position/verbosity bias)
- [ ] 能解释 lost-in-the-middle 问题,并说出长文档分析的混合架构(层级摘要+选择性加载)
- [ ] 能说出 web agent 的三个独特挑战(视觉/不可逆/对抗环境)和两个关键安全措施(确认门+prompt injection 防御)
- [ ] 能列出生产 agent 的六件套(retry/容错/可观测/成本/限步/防循环)
- [ ] 能说出企业 agent 平台多租户隔离的三层(数据层 tenant_id/加密层独立密钥/索引层隔离)
- [ ] 能用英文做一段结构化的系统设计开场(clarify → assume → estimate → architect → deep-dive → trade-off)

### 代码题(3个)

- [ ] 能手写一个带 retry + exponential backoff 的工具执行函数(Python)
- [ ] 能手写一个 agent loop 的核心循环(LLM 调用 → 工具执行 → 结果回填 → 终止判断)
- [ ] 能手写一个 token 成本追踪器(累加 input/output token,按模型定价计算 $)

### 系统设计题(2个)

- [ ] 能在 30 分钟内英文白板完成 "Automated code review at scale" 的系统设计(需求→容量→架构→模块→容错→权衡)
- [ ] 能在 30 分钟内英文白板完成 "Enterprise agent platform" 的系统设计,重点讲清多租户隔离和合规

---

## 延伸阅读 — 海外公司技术博客 / 论文

### 论文(必读)

| 论文 | 公司 | 主题 |
|------|------|------|
| Constitutional AI: Harmlessness from AI Feedback | Anthropic | CAI 原始论文 |
| Training Language Models to Follow Instructions (InstructGPT) | OpenAI | RLHF 基础 |
| Toolformer: Language Models Can Teach Themselves to Use Tools | Meta | Tool use 训练 |
| ReAct: Synergizing Reasoning and Acting | Princeton/Google | ReAct 范式 |
| Reflexion: Language Agents with Verbal Reinforcement Learning | NEU | Self-reflection agent |
| SWE-agent: Agent-Computer Interfaces Enable Software Engineering | Princeton | SWE-agent |
| The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery | Sakana AI | 自主研究系统 |
| Lost in the Middle: How Language Models Use Long Contexts | Stanford | 长上下文失效 |
| Sleeper Agents: Training Deceptive LLMs that Persist Through Safety Training | Anthropic | 安全对抗 |
| Asleep at the Keyboard: Assessing the Security of GitHub Copilot's Code Contributions | Stanford | 代码 agent 安全 |

### 技术博客

| 来源 | 内容 |
|------|------|
| Anthropic blog — "Building effective agents" | Agent 构建实践(必读) |
| Anthropic — "Computer Use" 系列博客 | Web/computer agent 设计 |
| OpenAI — "Practices for governing agentic AI systems" | Agent 治理 |
| OpenAI — o1 system card / model cards | 推理时扩展、安全评估 |
| Google Research blog — Agent / Gemini 相关 | Google 的 agent 方向 |
| Meta AI blog — Llama / tool use | 开源生态 |
| Microsoft Research blog — Copilot / AutoGen | 企业 agent / 多 agent 框架 |
| Eugene Yan's blog — "Evaluating LLM Applications" | 评估方法论(工程视角) |
| Lil'Log (Lilian Weng) — "LLM Powered Autonomous Agents" | Agent 综述(经典) |

### 英文面试准备资源

- Tech Interview Handbook — 系统设计框架
- "Designing Data-Intensive Applications" (Martin Kleppmann) — 系统设计圣经
- AlphaSignal / The Batch — 跟踪前沿论文
- 实际刷: LeetCode 中 hard 题(DeepMind 考),系统设计用 "System Design Interview" (Alex Xu) 练英文口述

---

## 明日预告

**Day 28 — 高频手撕题冲刺**

明天聚焦 Agent 方向高频手撕代码题的限时训练:
- ReAct agent loop 从零实现(限时 20 分钟)
- RAG pipeline 完整实现(分块/embedding/检索/重排/生成)
- Multi-agent 协作框架(消息传递 + 状态管理)
- Tool registry + 动态工具加载
- 流式输出 + SSE 解析
- 成本/Token 预算控制器
- 评估脚本(LLM-as-judge + 多采样)

每题限时 20-30 分钟,模拟面试白板环境(无 IDE 补全、无搜索),目标是肌肉记忆。今天学的生产级 agent 代码(Q9)是明天所有手撕题的基础架构,务必先跑通。

> **今日复盘建议**: 用英文对着镜子(或录音)把 Q2 和 Q10 的系统设计各讲一遍,限时 30 分钟。听录音检查:是否结构化?是否暴露假设?是否量化?是否讨论权衡?这是海外面试最拉开差距的能力。
