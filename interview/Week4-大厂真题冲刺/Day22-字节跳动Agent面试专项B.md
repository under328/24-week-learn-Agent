### Q9: 手撕代码题 — 实现一个支持流式输出的 Agent(含 SSE / 工具调用流式 / 前端渲染)

<details>
<summary>查看完整代码</summary>

**题目**: 实现一个支持流式输出的 Agent,要求:
1. 后端用 Python,通过 SSE (Server-Sent Events) 流式返回
2. 支持工具调用,工具调用过程也要流式(边生成参数边返回)
3. 前端用 HTML/JS 渲染流式输出,区分"思考"、"工具调用"、"最终回答"
4. 包含死循环检测和错误处理

**完整实现**:

```python
"""
流式 Agent 完整实现
运行: python streaming_agent.py
访问: http://localhost:8000
依赖: pip install fastapi uvicorn httpx
"""

import asyncio
import json
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse

# ============================================================
# 第一部分: 流式 LLM 客户端(模拟豆包 API)
# ============================================================

class StreamingLLMClient:
    """流式 LLM 客户端,模拟 SSE 流式返回"""
    
    def __init__(self, api_key: str = "mock-key", base_url: str = "https://api.doubao.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60)

    async def stream_chat(
        self, 
        messages: list, 
        tools: list = None,
        model: str = "doubao-pro"
    ) -> AsyncGenerator[dict, None]:
        """
        流式调用 LLM,逐 Token 返回事件:
        - {"type": "text", "content": "你"}    # 文本 Token
        - {"type": "tool_call_start", "id": "...", "name": "search"}  # 工具调用开始
        - {"type": "tool_call_arg", "id": "...", "arg_chunk": '{"quer'}  # 工具参数(流式)
        - {"type": "tool_call_end", "id": "...", "arguments": '{"query": "..."}'}  # 工具调用完成
        - {"type": "done", "finish_reason": "stop"}  # 结束
        """
        # 模拟流式返回(实际应调用真实 API)
        # 这里用模拟数据演示流式协议
        mock_response = self._generate_mock_response(messages, tools)
        
        for chunk in mock_response:
            yield chunk
            await asyncio.sleep(0.05)  # 模拟网络延迟

    def _generate_mock_response(self, messages, tools):
        """生成模拟流式响应(真实场景应解析 API SSE 流)"""
        last_msg = messages[-1]["content"].lower()
        
        # 模拟需要调用工具的场景
        if "天气" in last_msg or "weather" in last_msg:
            return [
                {"type": "text", "content": "让我"},
                {"type": "text", "content": "查一下"},
                {"type": "text", "content": "天气"},
                {"type": "text", "content": "信息"},
                {"type": "text", "content": "。\n"},
                {"type": "tool_call_start", "id": "call_001", "name": "get_weather"},
                {"type": "tool_call_arg", "id": "call_001", "arg_chunk": '{"cit'},
                {"type": "tool_call_arg", "id": "call_001", "arg_chunk": 'y": "Bei'},
                {"type": "tool_call_arg", "id": "call_001", "arg_chunk": 'jing"}'},
                {"type": "tool_call_end", "id": "call_001", "arguments": '{"city": "Beijing"}'},
                {"type": "done", "finish_reason": "tool_calls"},
            ]
        elif "搜索" in last_msg or "search" in last_msg:
            return [
                {"type": "text", "content": "我来"},
                {"type": "text", "content": "搜索一下"},
                {"type": "text", "content": "。\n"},
                {"type": "tool_call_start", "id": "call_002", "name": "search_web"},
                {"type": "tool_call_arg", "id": "call_002", "arg_chunk": '{"quer'},
                {"type": "tool_call_arg", "id": "call_002", "arg_chunk": 'y": "最新的AI新闻"}'},
                {"type": "tool_call_end", "id": "call_002", "arguments": '{"query": "最新的AI新闻"}'},
                {"type": "done", "finish_reason": "tool_calls"},
            ]
        else:
            # 直接回答
            answer = f"这是一个关于「{last_msg[:20]}」的回答。我认为这个问题很有趣,需要从多个角度来分析..."
            chunks = [answer[i:i+3] for i in range(0, len(answer), 3)]
            events = [{"type": "text", "content": c} for c in chunks]
            events.append({"type": "done", "finish_reason": "stop"})
            return events


# ============================================================
# 第二部分: 工具定义
# ============================================================

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    
    async def execute(self, **kwargs) -> str:
        raise NotImplementedError


class WeatherTool(Tool):
    def __init__(self):
        super().__init__(
            name="get_weather",
            description="获取指定城市的天气信息",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string", "description": "城市名"}},
                "required": ["city"]
            }
        )
    
    async def execute(self, city: str) -> str:
        await asyncio.sleep(1)  # 模拟 API 调用
        return json.dumps({"city": city, "weather": "晴", "temp": 25, "humidity": 60})


class SearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="search_web",
            description="搜索互联网获取信息",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string", "description": "搜索词"}},
                "required": ["query"]
            }
        )
    
    async def execute(self, query: str) -> str:
        await asyncio.sleep(1.5)  # 模拟搜索延迟
        return json.dumps({
            "results": [
                {"title": f"关于{query}的最新报道", "snippet": "这是搜索结果摘要..."},
                {"title": f"{query}深度分析", "snippet": "详细内容..."},
            ]
        })


# ============================================================
# 第三部分: 死循环检测器
# ============================================================

class LoopGuard:
    def __init__(self, max_steps=8, max_same_action=2, max_time=30):
        self.max_steps = max_steps
        self.max_same_action = max_same_action
        self.max_time = max_time
        self.action_history = []
        self.start_time = time.time()
    
    def check(self, action_name: str = "") -> tuple[bool, str]:
        """返回 (should_stop, reason)"""
        elapsed = time.time() - self.start_time
        
        if len(self.action_history) >= self.max_steps:
            return True, f"超过最大步数 {self.max_steps}"
        if elapsed > self.max_time:
            return True, f"超过最大时间 {self.max_time}s"
        
        if action_name:
            self.action_history.append(action_name)
            recent = self.action_history[-5:]
            counter = Counter(recent)
            most_common, count = counter.most_common(1)[0]
            if count >= self.max_same_action:
                return True, f"动作 {most_common} 重复 {count} 次"
        
        return False, ""


# ============================================================
# 第四部分: 流式 Agent 核心实现
# ============================================================

class StreamingAgent:
    def __init__(self, llm_client: StreamingLLMClient, tools: list[Tool]):
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}
        self.loop_guard = LoopGuard()
    
    async def run(self, user_query: str, conversation_history: list = None) -> AsyncGenerator[str, None]:
        """
        流式运行 Agent,产出 SSE 格式事件:
        data: {"type": "thinking", "content": "..."}
        data: {"type": "text", "content": "..."}
        data: {"type": "tool_call", "name": "...", "arguments": {...}}
        data: {"type": "tool_result", "name": "...", "result": "..."}
        data: {"type": "done"}
        """
        messages = conversation_history or []
        messages.append({"role": "user", "content": user_query})
        
        tool_schemas = [
            {"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}}
            for t in self.tools.values()
        ]
        
        while True:
            # 死循环检测
            should_stop, reason = self.loop_guard.check()
            if should_stop:
                yield self._sse({"type": "error", "content": f"Agent 终止: {reason}"})
                break
            
            # 流式调用 LLM
            full_text = ""
            tool_calls = {}  # id -> {"name": ..., "arguments": ""}
            
            yield self._sse({"type": "thinking", "content": "正在思考..."})
            
            async for event in self.llm.stream_chat(messages, tools=tool_schemas):
                if event["type"] == "text":
                    full_text += event["content"]
                    yield self._sse({"type": "text", "content": event["content"]})
                
                elif event["type"] == "tool_call_start":
                    tool_calls[event["id"]] = {"name": event["name"], "arguments": ""}
                    yield self._sse({
                        "type": "tool_call_start", 
                        "id": event["id"], 
                        "name": event["name"]
                    })
                
                elif event["type"] == "tool_call_arg":
                    tool_calls[event["id"]]["arguments"] += event["arg_chunk"]
                    yield self._sse({
                        "type": "tool_call_arg",
                        "id": event["id"],
                        "chunk": event["arg_chunk"]
                    })
                
                elif event["type"] == "tool_call_end":
                    yield self._sse({
                        "type": "tool_call_end",
                        "id": event["id"],
                        "name": tool_calls[event["id"]]["name"],
                        "arguments": json.loads(tool_calls[event["id"]]["arguments"])
                    })
                
                elif event["type"] == "done":
                    if event["finish_reason"] == "stop":
                        # 无工具调用,直接结束
                        messages.append({"role": "assistant", "content": full_text})
                        yield self._sse({"type": "done"})
                        return
                    # finish_reason == "tool_calls" 继续执行工具
                    break
            
            # 执行工具调用(并发)
            if tool_calls:
                # 把 assistant 消息加入历史(含 tool_calls)
                messages.append({
                    "role": "assistant",
                    "content": full_text,
                    "tool_calls": [
                        {"id": tc_id, "name": tc["name"], "arguments": tc["arguments"]}
                        for tc_id, tc in tool_calls.items()
                    ]
                })
                
                # 并发执行所有工具
                tasks = []
                for tc_id, tc in tool_calls.items():
                    tool = self.tools.get(tc["name"])
                    if tool:
                        tasks.append(self._execute_tool_streaming(tc_id, tool, tc["arguments"]))
                    else:
                        tasks.append(self._tool_not_found(tc_id, tc["name"]))
                
                results = await asyncio.gather(*tasks)
                
                for tc_id, result in results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": result
                    })
            
            # 继续下一轮循环(把工具结果送回 LLM)
    
    async def _execute_tool_streaming(self, call_id, tool, arguments_str):
        """执行单个工具,流式返回状态"""
        try:
            args = json.loads(arguments_str)
            yield_event = self._sse({"type": "tool_executing", "id": call_id, "name": tool.name})
            # 注意: 这里不能 yield,改用返回值
            result = await tool.execute(**args)
            return call_id, result
        except json.JSONDecodeError:
            return call_id, json.dumps({"error": f"参数解析失败: {arguments_str}"})
        except Exception as e:
            return call_id, json.dumps({"error": str(e)})
    
    async def _tool_not_found(self, call_id, tool_name):
        return call_id, json.dumps({"error": f"工具 {tool_name} 不存在"})
    
    @staticmethod
    def _sse(data: dict) -> str:
        """格式化为 SSE 事件"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ============================================================
# 第五部分: FastAPI 后端
# ============================================================

app = FastAPI()
llm_client = StreamingLLMClient()
agent = StreamingAgent(llm_client, tools=[WeatherTool(), SearchTool()])

@app.get("/")
async def index():
    """返回前端页面"""
    return HTMLResponse(HTML_PAGE)

@app.post("/chat")
async def chat(request: Request):
    """流式聊天接口"""
    body = await request.json()
    query = body.get("query", "")
    history = body.get("history", [])
    
    async def event_stream():
        try:
            async for sse_event in agent.run(query, history):
                yield sse_event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================
# 第六部分: 前端页面(内嵌 HTML)
# ============================================================

HTML_PAGE = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>流式 Agent Demo</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 50px auto; }
        #chat { border: 1px solid #ddd; padding: 20px; height: 400px; overflow-y: auto; margin-bottom: 10px; }
        .msg { margin: 10px 0; padding: 8px 12px; border-radius: 8px; }
        .user { background: #e3f2fd; text-align: right; }
        .assistant { background: #f5f5f5; }
        .thinking { color: #999; font-style: italic; }
        .tool-call { background: #fff3e0; border-left: 3px solid #ff9800; }
        .tool-result { background: #e8f5e9; border-left: 3px solid #4caf50; font-family: monospace; font-size: 0.9em; }
        .error { background: #ffebee; color: #c62828; }
        #input { width: 75%; padding: 10px; }
        #send { width: 20%; padding: 10px; }
        .cursor { display: inline-block; width: 2px; height: 1em; background: #333; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0; } }
    </style>
</head>
<body>
    <h2>流式 Agent Demo (SSE + 工具调用)</h2>
    <div id="chat"></div>
    <input id="input" placeholder="输入问题(试试: 北京天气怎么样?)" />
    <button id="send" onclick="send()">发送</button>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        let currentMsg = null;
        let currentType = null;

        input.addEventListener('keypress', e => { if (e.key === 'Enter') send(); });

        async function send() {
            const query = input.value.trim();
            if (!query) return;
            input.value = '';
            
            // 显示用户消息
            chat.innerHTML += `<div class="msg user">${escapeHtml(query)}</div>`;
            chat.scrollTop = chat.scrollHeight;

            // SSE 连接
            const resp = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, history: [] })
            });

            const reader = resp.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value);
                const lines = buffer.split('\\n\\n');
                buffer = lines.pop();  // 保留不完整的

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        handleEvent(data);
                    }
                }
            }
        }

        function handleEvent(data) {
            switch (data.type) {
                case 'thinking':
                    currentMsg = addMsg('thinking', '💭 ' + data.content);
                    currentType = 'thinking';
                    break;
                case 'text':
                    if (currentType !== 'assistant') {
                        currentMsg = addMsg('assistant', '');
                        currentType = 'assistant';
                    }
                    currentMsg.innerHTML += escapeHtml(data.content);
                    chat.scrollTop = chat.scrollHeight;
                    break;
                case 'tool_call_start':
                    currentMsg = addMsg('tool-call', `🔧 调用工具: ${data.name}`);
                    currentType = 'tool-call';
                    break;
                case 'tool_call_end':
                    currentMsg.innerHTML += `<br>参数: <code>${JSON.stringify(data.arguments)}</code>`;
                    break;
                case 'tool_executing':
                    currentMsg = addMsg('tool-call', `⏳ 执行 ${data.name}...`);
                    break;
                case 'tool_result':
                    if (currentType !== 'tool-result') {
                        currentMsg = addMsg('tool-result', '');
                    }
                    currentMsg.innerHTML += `✅ 结果: ${escapeHtml(data.result)}`;
                    currentType = 'tool-result';
                    break;
                case 'done':
                    currentMsg = null;
                    currentType = null;
                    break;
                case 'error':
                    addMsg('error', '❌ ' + data.content);
                    break;
            }
            chat.scrollTop = chat.scrollHeight;
        }

        function addMsg(cls, text) {
            const div = document.createElement('div');
            div.className = 'msg ' + cls;
            div.innerHTML = escapeHtml(text);
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
            return div;
        }

        function escapeHtml(s) {
            const d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }
    </script>
</body>
</html>
"""
```

**面试讲解要点**:

1. **SSE 协议**: `data: {json}\n\n` 格式,单向推送,比 WebSocket 轻量,适合流式输出
2. **工具调用流式**: LLM 边生成 JSON 参数边返回,前端实时渲染"正在输入参数..."效果
3. **部分 JSON 解析**: 实际生产中需要处理不完整 JSON(用 json-repair 库或增量解析器)
4. **并发工具执行**: `asyncio.gather` 并发执行多个工具,降低延迟
5. **死循环检测**: 内置 LoopGuard,步数/时间/重复动作三重检测
6. **前端渲染**: 用 `ReadableStream` 读取 SSE 流,区分不同事件类型渲染

**字节面试追问**:
- "如果 LLM 返回的工具调用 JSON 不完整怎么办?" → 用 json-repair 修复 + 重试
- "SSE 断连了怎么恢复?" → 客户端记录已接收位置,重连时从断点继续(需要后端支持)
- "多个用户同时请求怎么隔离?" → 每个 Agent 实例独立(无状态),或用 session_id 隔离上下文
- "怎么压测流式接口?" → 关注并发连接数、首 Token 延迟、吞吐量; 用 locust + websocket 插件

</details>

---

### Q10: 系统设计 — 设计飞书智能助手的 Agent 系统(日程管理/文档摘要/会议纪要/任务分配)

<details>
<summary>查看完整解答</summary>

**题目**: 设计飞书智能助手 Agent 系统,支持四大场景: 日程管理、文档摘要、会议纪要、任务分配。要求覆盖 1000 万飞书企业用户,日请求量 1 亿次。

**一、需求澄清**

| 维度 | 假设 |
|------|------|
| 场景 | 日程管理、文档摘要、会议纪要、任务分配 |
| 用户 | 1000 万企业用户,日请求 1 亿次 |
| 时延 | 首 Token < 2s,简单任务 < 5s,复杂任务 < 30s |
| 准确率 | 日程操作 > 99%(不能约错会),摘要 > 90% |
| 安全 | 企业数据隔离,不跨企业泄露,支持私有化部署 |
| 集成 | 飞书生态(日历/文档/会议/任务/审批) |

**二、核心挑战(飞书场景特有)**

1. **企业数据隔离**: 每个企业的知识库严格隔离,Agent 不能跨企业读取
2. **权限控制**: 用户只能访问有权限的文档/日历,Agent 要继承用户权限
3. **操作类任务容错**: 日程操作(创建/修改/删除)一旦出错影响大,需要确认机制
4. **实时性**: 会议纪要需要实时生成,不能等会开完
5. **多租户**: 1000 万用户、几十万家企业,多租户架构

**三、顶层架构**

```
┌────────────────────────────────────────────────────────────────┐
│                      飞书客户端                                  │
│   飞书 App / 网页 / 机器人 / 侧边栏                               │
└────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────┐
│                   飞书网关 (Gateway)                            │
│   鉴权 / 租户路由 / 限流 / 审计日志                               │
└────────────────────────┬───────────────────────────────────────┘
                         │
┌────────────────────────▼───────────────────────────────────────┐
│                Agent 编排层 (Multi-Agent)                       │
│                                                                │
│   ┌──────────┐                                                 │
│   │ Router   │ ← 意图识别,分发到子 Agent                        │
│   │ Agent    │                                                 │
│   └────┬─────┘                                                 │
│        ├──────────────┬──────────────┬──────────────┐           │
│   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐   ┌────▼────┐       │
│   │ 日程    │   │ 文档    │   │ 会议    │   │ 任务    │       │
│   │ Agent   │   │ Agent   │   │ Agent   │   │ Agent   │       │
│   └────┬────┘   └────┬────┘   └────┬────┘   └────┬────┘       │
│        │              │              │              │            │
│   ┌────▼──────────────▼──────────────▼──────────────▼────┐     │
│   │              共享 Memory & Context                    │     │
│   └───────────────────────────────────────────────────────┘     │
└────────────────────────┬───────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼───────┐ ┌──────▼──────┐ ┌───────▼───────┐
│  飞书数据层   │ │  LLM 服务   │ │  知识库层     │
│ ┌───────────┐ │ │ ┌─────────┐ │ │ ┌───────────┐ │
│ │ 日历 API  │ │ │ │豆包-Pro │ │ │ │ 企业知识库│ │
│ │ 文档 API  │ │ │ │豆包-Lite│ │ │ │ (向量库)  │ │
│ │ 会议 API  │ │ │ │语音模型 │ │ │ │ ES        │ │
│ │ 任务 API  │ │ │ └─────────┘ │ │ └───────────┘ │
│ └───────────┘ │ └─────────────┘ └───────────────┘
└───────────────┘
```

**四、四大场景 Agent 设计**

**场景 1: 日程管理 Agent**

```python
class ScheduleAgent:
    """日程管理 Agent —— 高准确率要求,带确认机制"""
    
    def __init__(self, llm, calendar_api):
        self.llm = llm
        self.calendar_api = calendar_api  # 飞书日历 API
    
    async def handle(self, user_input: str, user_id: str, tenant_id: str):
        # Step 1: 意图识别(创建/查询/修改/删除)
        intent = await self.classify_intent(user_input)
        
        # Step 2: 参数提取
        params = await self.extract_params(user_input, intent)
        # params = {"action": "create", "title": "产品评审", "time": "明天下午3点", "attendees": ["张三"]}
        
        # Step 3: 时间解析(中文时间 → 绝对时间)
        params["start_time"], params["end_time"] = await self.parse_time(
            params["time"], 
            user_timezone=await self.get_timezone(user_id)
        )
        
        # Step 4: 冲突检测
        conflicts = await self.calendar_api.check_conflict(
            user_id, params["start_time"], params["end_time"]
        )
        
        if conflicts:
            return {
                "need_confirm": True,
                "message": f"该时段已有会议: {conflicts}, 是否仍然创建?",
                "params": params
            }
        
        # Step 5: 确认机制(创建/修改/删除需要用户确认)
        return {
            "need_confirm": True,
            "message": f"将创建会议「{params['title']}」,时间 {params['start_time']},参会人 {params.get('attendees', [])}。确认?",
            "params": params
        }
    
    async def execute_confirmed(self, params, user_id, tenant_id):
        """用户确认后执行"""
        try:
            result = await self.calendar_api.create_event(
                user_id=user_id,
                tenant_id=tenant_id,
                title=params["title"],
                start_time=params["start_time"],
                end_time=params["end_time"],
                attendees=params.get("attendees", [])
            )
            return {"success": True, "event_id": result["id"], "message": "会议已创建"}
        except Exception as e:
            return {"success": False, "message": f"创建失败: {e}"}
```

**场景 2: 文档摘要 Agent**

```python
class DocSummaryAgent:
    """文档摘要 Agent —— 处理长文档,分段摘要 + 汇总"""
    
    MAX_CHUNK_TOKENS = 3000  # 每段最大 Token
    
    async def summarize(self, doc_id: str, user_id: str, instruction: str = None):
        # Step 1: 获取文档内容(通过飞书文档 API,继承用户权限)
        doc = await self.doc_api.get_doc(doc_id, user_id=user_id)
        
        if not doc["content"]:
            return {"error": "无法访问该文档(权限不足或文档为空)"}
        
        # Step 2: 分块
        chunks = self.split_doc(doc["content"], self.MAX_CHUNK_TOKENS)
        
        # Step 3: 并发分段摘要
        chunk_summaries = await asyncio.gather(*[
            self.summarize_chunk(chunk, instruction) for chunk in chunks
        ])
        
        # Step 4: 汇总
        if len(chunk_summaries) == 1:
            final_summary = chunk_summaries[0]
        else:
            final_summary = await self.merge_summaries(chunk_summaries, instruction)
        
        # Step 5: 提取关键信息
        key_points = await self.extract_key_points(final_summary)
        action_items = await self.extract_action_items(final_summary)
        
        return {
            "summary": final_summary,
            "key_points": key_points,        # 关键要点
            "action_items": action_items,    # 待办事项
            "doc_id": doc_id
        }
    
    def split_doc(self, content, max_tokens):
        """按段落分块,保持语义完整"""
        paragraphs = content.split("\n\n")
        chunks, current_chunk, current_tokens = [], [], 0
        
        for para in paragraphs:
            para_tokens = count_tokens(para)
            if current_tokens + para_tokens > max_tokens and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk, current_tokens = [], 0
            current_chunk.append(para)
            current_tokens += para_tokens
        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        return chunks
```

**场景 3: 会议纪要 Agent(实时)**

```python
class MeetingMinutesAgent:
    """会议纪要 Agent —— 实时流式生成"""
    
    async def real_time_minutes(self, meeting_id: str, user_id: str):
        """
        实时会议纪要: 订阅会议音频流,实时转写 + 摘要
        """
        # Step 1: 订阅会议 ASR 流(飞书会议 API)
        asr_stream = self.meeting_api.subscribe_asr(meeting_id)
        
        # Step 2: 滑动窗口累积转录
        buffer = ""
        last_summary_time = time.time()
        summary_interval = 60  # 每 60 秒更新一次摘要
        
        async for utterance in asr_stream:
            # utterance = {"speaker": "张三", "text": "...", "timestamp": 123.45}
            buffer += f"[{utterance['speaker']}]: {utterance['text']}\n"
            
            # 流式推送转录
            yield {"type": "transcript", "data": utterance}
            
            # 定期生成/更新摘要
            if time.time() - last_summary_time > summary_interval:
                summary = await self.generate_summary(buffer)
                yield {"type": "summary_update", "data": summary}
                last_summary_time = time.time()
        
        # 会议结束,生成最终纪要
        final_minutes = await self.generate_final_minutes(buffer)
        yield {"type": "final_minutes", "data": final_minutes}
    
    async def generate_final_minutes(self, transcript):
        """生成最终会议纪要"""
        prompt = f"""
        请基于以下会议转录,生成结构化会议纪要:
        
        ## 会议主题
        (推断)
        
        ## 参会人
        (从转录提取)
        
        ## 讨论要点
        (3-5 条)
        
        ## 决议
        (明确的决定)
        
        ## 待办事项
        (责任人 + 截止时间)
        
        转录:
        {transcript[:8000]}
        """
        return await self.llm.arun(prompt)
```

**场景 4: 任务分配 Agent**

```python
class TaskAssignmentAgent:
    """任务分配 Agent —— 理解任务 + 匹配成员 + 生成分配建议"""
    
    async def assign_task(self, task_description: str, team_id: str, user_id: str):
        # Step 1: 解析任务
        task = await self.parse_task(task_description)
        # task = {"title": "...", "type": "开发", "skills": ["Python", "AI"], "deadline": "7天", "priority": "高"}
        
        # Step 2: 获取团队成员及能力(飞书组织架构 API)
        members = await self.org_api.get_team_members(team_id, user_id)
        # members = [{"id": "...", "name": "张三", "skills": ["Python"], "workload": 0.8, "role": "开发"}, ...]
        
        # Step 3: 匹配(任务需求 vs 成员能力 + 当前负载)
        candidates = await self.match_members(task, members)
        
        # Step 4: 生成分配建议
        recommendation = await self.llm.arun(f"""
        任务: {json.dumps(task, ensure_ascii=False)}
        候选成员: {json.dumps(candidates, ensure_ascii=False)}
        
        请推荐最合适的负责人(1-2人),说明理由,并生成分配消息。
        """)
        
        return {
            "task": task,
            "recommendation": recommendation,
            "candidates": candidates
        }
    
    async def match_members(self, task, members):
        """综合技能匹配 + 负载均衡,打分排序"""
        scored = []
        for m in members:
            skill_score = self.calc_skill_match(task["skills"], m.get("skills", []))
            workload_score = 1 - m.get("workload", 1)  # 负载越低分越高
            role_score = 1.0 if task["type"] == m.get("role") else 0.3
            total = skill_score * 0.5 + workload_score * 0.3 + role_score * 0.2
            scored.append({**m, "score": total})
        scored.sort(key=lambda x: -x["score"])
        return scored[:3]
```

**五、Router Agent —— 多 Agent 路由**

```python
class RouterAgent:
    """意图路由 Agent —— 把用户请求分发给对应子 Agent"""
    
    ROUTING_PROMPT = """
    判断用户意图属于哪个场景,输出场景名:
    - schedule: 日程管理(创建/查询/修改会议、日程)
    - doc_summary: 文档摘要(总结文档、提取要点)
    - meeting: 会议纪要(开会记录、会议总结)
    - task: 任务分配(派活、分工)
    - general: 通用问答(不属于以上)
    
    用户输入: {input}
    输出(单个词):
    """
    
    async def route(self, user_input: str) -> str:
        # 用 Lite 模型快速分类
        intent = await self.llm_lite.arun(self.ROUTING_PROMPT.format(input=user_input))
        return intent.strip().lower()
```

**六、多租户与权限设计**

```python
class TenantContext:
    """多租户上下文,每次请求必须携带"""
    tenant_id: str      # 企业 ID
    user_id: str        # 用户 ID
    permissions: list   # 用户权限列表
    
    def can_access_doc(self, doc_id) -> bool:
        """检查用户是否有权访问某文档"""
        return self.doc_acl.check(self.user_id, doc_id)

# Agent 所有数据访问都必须经过 TenantContext 校验
# 知识库按 tenant_id 物理隔离(不同企业存不同 index)
```

**七、容量估算**

| 指标 | 估算 |
|------|------|
| 企业用户 | 1000 万 |
| 日请求量 | 1 亿次 |
| QPS 峰值 | 5000 |
| 平均 Token/次 | 1200 |
| 日 Token 量 | 1200 亿 |
| GPU 推理卡 | 约 800 张 A100 |
| 知识库存储 | 50TB(向量) + 200TB(原文) |
| 月度成本 | 约 ¥2000-3000 万 |

**八、安全与合规**

1. **数据隔离**: 知识库按 tenant_id 物理隔离,LLM 请求带 tenant_id 标签
2. **权限继承**: Agent 调用飞书 API 时用用户 token,继承用户权限
3. **脱敏**: 日志中敏感信息(手机号/身份证)脱敏
4. **审计**: 所有 Agent 操作(特别是日程修改)记录审计日志
5. **私有化**: 大客户支持私有化部署,模型和数据都在企业内网
6. **合规**: 满足等保三级、ISO 27001

**九、字节面试加分点**

1. 主动提"飞书生态深度集成": Agent 不只是聊天,要能调用飞书所有 API(日历/文档/会议/审批/人事)
2. 主动提"企业知识库": 飞书文档天然是企业知识库,Agent + RAG 能做企业大脑
3. 主动提"操作类任务的确认机制": 日程/任务操作影响大,需要"提议→确认→执行"三步
4. 主动提"实时会议纪要": 这是飞书的杀手锏功能,需要 ASR 流 + 实时摘要
5. 主动提"多租户隔离": ToB 产品的核心要求,数据不能串

</details>

---

## 核心知识回顾表

| 知识点 | 核心内容 | 字节考察频率 |
|--------|----------|------------|
| 字节 Agent 人才画像 | 工程能力强 + 成本意识 + 数据驱动 + 业务理解 | 必考 |
| 豆包 Agent 架构 | 混合 ReAct+Plan、模型路由、分层 Memory、KV Cache | 高频 |
| 死循环检测 | 步数限制 + 重复检测 + 熔断 + 恢复策略 | 高频追问 |
| RAG 优化 | Query 改写 + 混合检索 + 父子分块 + Rerank | 高频 |
| Token 成本优化 | Prompt 压缩 + 历史压缩 + 模型路由 + 缓存 | 必考 |
| Function Calling vs ReAct | FC 原生可靠 / ReAct 灵活可定制 | 中频 |
| Agent 评估 | 5 层指标 + LLM-as-Judge + A/B + Trajectory | 高频 |
| 多模态 Agent | 关键帧抽取 + ASR + VLM + 混合对齐 | 中频 |
| 流式输出 | SSE + 工具调用流式 + 前端渲染 | 必考代码 |
| 飞书智能助手 | Multi-Agent + 多租户 + 权限继承 + 确认机制 | 系统设计高频 |

---

## 面试速记卡 — 字节面试技巧

```
┌──────────────────────────────────────────────────────────────┐
│                  字节 Agent 面试速记卡                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  【面试风格】                                                 │
│  • 节奏快: 一面 60-75 min, 不拖沓                             │
│  • 追问狠: 连环 why, 追到答不出为止                            │
│  • 重落地: "线上怎么部署?" "成本多少?" "怎么监控?"             │
│  • 必撕码: 流式输出 / asyncio / JSON 解析                     │
│                                                              │
│  【答题套路】                                                 │
│  1. 先澄清需求(不急于画架构)                                  │
│  2. 先给方案再讨论 tradeoff                                   │
│  3. 任何方案都要算成本(Token / QPS / 机器)                    │
│  4. 任何方案都要说监控(指标 / 告警 / 降级)                    │
│  5. 主动提 A/B 实验设计                                       │
│                                                              │
│  【字节特色考点】                                             │
│  • 成本优化(灵魂考题)                                        │
│  • 流式输出(必考代码)                                        │
│  • 死循环检测(高频追问)                                      │
│  • 多模态(抖音团队)                                          │
│  • 多租户(飞书团队)                                          │
│  • 数据驱动评估                                               │
│                                                              │
│  【加分项】                                                   │
│  • 用过豆包/飞书AI/剪映AI, 能说出现状和问题                   │
│  • 有完整的 Agent 项目经历(架构图+指标+踩坑)                  │
│  • 了解字节技术栈(Eino框架 / 豆包模型 / 火山引擎)            │
│  • 能讲清 tradeoff(为什么用A不用B)                           │
│                                                              │
│  【减分项】                                                   │
│  • 只讲理论不讲落地                                           │
│  • 答不出成本数字                                             │
│  • 不会写流式代码                                             │
│  • 对字节产品不熟悉                                           │
│  • 回答没有数据支撑                                           │
│                                                              │
│  【一句话总结】                                               │
│  字节要的是"能打仗的工程师",不是"会背书的研究生"。              │
│  每个回答都要落地、要算账、要数据。                            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒

### 1. 把 Agent 说成"万能的"

<details>
<summary>展开</summary>

**错误**: "Agent 能自动完成所有任务,不需要人工干预。"
**正确**: Agent 有能力边界,复杂/高风险场景需要人工确认(Human-in-the-loop)。特别是操作类任务(日程修改、发邮件、付款)必须有确认机制。
**字节面试官点评**: "你说 Agent 全自动,那它把 CEO 的日程删了怎么办?"

</details>

### 2. 答系统设计不画图

<details>
<summary>展开</summary>

**错误**: 纯口头描述架构,不画图。
**正确**: 字节面试(线上)通常有共享白板,一定要画架构图。先画顶层 3-4 层,再逐层展开。图比文字更清晰。
**建议**: 练习用 ASCII / Mermaid 快速画架构图。

</details>

### 3. 答成本题只说"用小模型"

<details>
<summary>展开</summary>

**错误**: "降低成本就是用小模型。"
**正确**: 成本优化是系统工程 —— Prompt 压缩、历史压缩、模型路由、KV Cache、结果缓存、Batch API、输出长度控制,多管齐下。只说"用小模型"显得没深度。
**字节面试官**: "小模型效果差怎么办? 你怎么保证不降质?"

</details>

### 4. RAG 优化只说"加 Rerank"

<details>
<summary>展开</summary>

**错误**: "召回率低就加 Rerank。"
**正确**: Rerank 只能优化排序,不能提升召回。如果检索阶段就没找到相关文档,Rerank 无能为力。要先定位瓶颈(检索 vs Rerank),再针对性优化。Query 改写和混合检索往往比 Rerank 更重要。

</details>

### 5. 流式代码不处理断连

<details>
<summary>展开</summary>

**错误**: 流式代码只写正常流程,不处理断连/超时/错误。
**正确**: 生产级流式必须处理: 网络断连、客户端取消、LLM 超时、JSON 解析失败。要加 try-catch、超时机制、断连恢复。
```python
# 错误写法
async for chunk in llm.stream():
    yield chunk

# 正确写法
try:
    async with timeout(30):
        async for chunk in llm.stream():
            yield chunk
except asyncio.TimeoutError:
    yield error_event("timeout")
except Exception as e:
    yield error_event(str(e))
```

</details>

### 6. Function Calling 和 ReAct 搞混

<details>
<summary>展开</summary>

**错误**: "ReAct 就是 Function Calling 的另一种叫法。"
**正确**: 两者本质不同 —— Function Calling 是模型原生能力(微调后直接输出 JSON),ReAct 是 Prompt 工程(用文本格式引导)。生产环境优先 FC,复杂推理用 ReAct,最佳实践是结合使用。

</details>

### 7. 评估只看准确率

<details>
<summary>展开</summary>

**错误**: "Agent 评估就看答案准确率。"
**正确**: Agent 评估要多维度 —— 任务完成率、工具调用准确率、步数效率、时延、成本、安全性。还要看 Trajectory(中间步骤对不对),不只看最终结果。线上要看业务指标(CSAT/留存),不只看离线指标。

</details>

### 8. 多模态说"逐帧送 LLM"

<details>
<summary>展开</summary>

**错误**: "视频理解就是把每帧都送 VLM。"
**正确**: 10 分钟视频 30fps 有 18000 帧,逐帧送 LLM 完全不可行。必须先抽取关键帧(每 2-5 秒一帧,或场景切换帧),配合 ASR 转录,用结构化表示送 LLM。Token 消耗从百万级降到千级。

</details>

### 9. 死循环只靠 max_steps

<details>
<summary>展开</summary>

**错误**: "加个 max_steps=10 就不会死循环了。"
**正确**: max_steps 是兜底,但不够。还要: 重复动作检测(同一工具调 3 次)、相邻步骤相同检测、工具熔断(失败 5 次禁用)、超时限制、Token 限制。并且要有恢复策略(注入 Hint / 强制总结),而不是简单终止。

</details>

### 10. 不了解字节自家产品

<details>
<summary>展开</summary>

**错误**: 面试字节但没用过豆包/飞书AI/剪映AI。
**正确**: 面试前务必体验字节 AI 产品,记下: 交互设计、响应速度、工具调用表现、优缺点。面试官一定会问"你用过豆包吗? 你觉得它有什么问题?"。答不上来直接减分。
**建议**: 至少用豆包聊 10 轮、用飞书AI做 3 个任务、用剪映AI剪 1 个视频。

</details>

---

## 自测检查清单

### 概念题(10 道)

- [ ] 1. 能说出字节 Agent 岗位的人才画像和面试流程(4 轮)
- [ ] 2. 能画出豆包 Agent 系统的完整架构(含模型路由、Memory、工具层)
- [ ] 3. 能说出 5 种 Agent 死循环场景 + 对应检测/恢复策略
- [ ] 4. 能说出 RAG 召回率从 60% 优化到 90% 的完整路径(6 种手段)
- [ ] 5. 能说出 8 种 Token 成本优化手段 + 组合后的预期效果
- [ ] 6. 能清晰对比 Function Calling 和 ReAct 的 6 个维度差异
- [ ] 7. 能说出 Agent 评估的 5 层指标框架 + 3 种评估方法
- [ ] 8. 能说出多模态 Agent 视频处理的关键帧抽取策略
- [ ] 9. 能说出飞书智能助手 Multi-Agent 架构的 4 个子 Agent
- [ ] 10. 能说出多租户场景下 Agent 的数据隔离和权限继承方案

### 代码题(3 道)

- [ ] 11. 能手写流式 Agent 的 SSE 事件格式(`data: {json}\n\n`)
- [ ] 12. 能手写工具调用的并发执行(`asyncio.gather` + 超时 + 重试)
- [ ] 13. 能手写死循环检测器(步数 + 重复 + 超时三重检测)

### 系统设计题(2 道)

- [ ] 14. 能在 30 分钟内画出豆包 Agent 系统架构(含容量估算和成本优化)
- [ ] 15. 能在 30 分钟内画出飞书智能助手 Multi-Agent 架构(含四大场景 + 多租户)

---

## 延伸阅读

### 字节 AI 团队技术博客

1. **火山引擎技术博客**: https://www.volcengine.com/product/ark
   - 豆包模型技术报告、推理优化实践

2. **字节跳动技术博客 (掘金)**: https://juejin.cn/user/4068403683509018
   - 飞书 AI 助手架构分享、Agent 工程实践

3. **Eino 框架文档**: https://www.cloudwego.io/zh/docs/eino/
   - 字节开源的 Go 语言 LLM 应用框架,对标 LangChain

4. **字节跳动技术沙龙(回放)**: 搜索"字节跳动 AI 技术沙龙"
   - Agent 专场、RAG 专场、多模态专场

### 论文

5. **ReAct 论文**: "ReAct: Synergizing Reasoning and Acting in Language Models" (Yao et al., 2022)
6. **Plan-and-Execute 论文**: "Plan-and-Solve Prompting" (Wang et al., 2023)
7. **HyDE 论文**: "Precise Zero-Shot Dense Retrieval without Relevance Labels" (Gao et al., 2022)
8. **Self-RAG 论文**: "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection" (Asai et al., 2023)

### 开源项目

9. **Eino**: https://github.com/cloudwego/eino —— 字节开源 Go LLM 框架
10. **Doubao API 文档**: https://www.volcengine.com/docs/82379 —— 豆包 API(含 Function Calling)

---

## 明日预告

> **Day 23 — 阿里巴巴 Agent 面试专项**
>
> 明天将聚焦阿里巴巴(通义千问团队 / 钉钉 AI / 淘宝 AI)的 Agent 面试题,重点准备:
> - 阿里面试风格(启发式、看稳定性、看大厂经验)
> - 通义千问 Agent 架构(百炼平台 / 通义系列模型)
> - 钉钉 AI 助手系统设计(企业级 Agent,与飞书对标)
> - 淘宝客服 Agent(高并发、多轮对话、推荐+Agent)
> - 阿里特别关注: **稳定性 / 灾备 / 降级** (双 11 级别的高可用)
> - 阿里特色: **中间件体系**(RocketMQ / Sentinel / Nacos)在 Agent 系统中的应用
>
> 预习建议: 体验通义千问 App、钉钉 AI 助手、淘宝客服; 了解阿里中间件体系; 复习高可用架构设计(限流/熔断/降级)。

---

> **今日总结**: 字节面试的核心是 **"工程落地 + 成本意识 + 数据驱动"**。系统设计要画图、要算账、要说监控; 代码题必考流式; 概念题要能说清 tradeoff。记住字节灵魂三问: **"为什么不是别的方案? 线上出问题怎么办? 成本多少?"**
