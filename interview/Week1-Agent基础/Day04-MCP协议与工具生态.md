# Day 04 — MCP 协议与工具生态

> **学习目标**：深入理解 MCP（Model Context Protocol）的架构设计、三种能力、与 Function Calling 的本质区别，能开发 MCP Server 并理解企业级部署方案。
>
> **预计用时**：3-4 小时（阅读 + 理解 + 手撕代码 + 口述练习）
>
> **面试频率**：⭐⭐⭐⭐（字节 4/11 面经出现，2025-2026 高频新考点）
>
> **使用方式**：先看题目自己思考，再点开"点击查看参考答案"对照。

---

## 一、知识地图

```
MCP (Model Context Protocol)
│
├── 1. MCP 是什么
│   ├── Anthropic 提出的开放标准
│   ├── 连接 LLM 和外部工具/数据源的标准化协议
│   └── 类比：USB-C 之于充电器，MCP 之于工具接入
│
├── 2. MCP 架构
│   ├── Host（宿主应用）：Claude Desktop / Cursor / 自建 Agent
│   ├── Client（客户端）：嵌入 Host 中，管理连接
│   ├── Server（服务端）：暴露工具/资源/提示
│   └── 传输层：stdio / SSE / WebSocket
│
├── 3. MCP 三种能力
│   ├── Tools：可执行的函数/操作
│   ├── Resources：可读取的数据/文件
│   └── Prompts：预定义的提示模板
│
├── 4. MCP vs Function Calling
│   ├── Function Calling：API 级，静态定义，厂商绑定
│   ├── MCP：应用协议级，动态发现，开放标准
│   └── 类比：各品牌充电器 vs USB-C
│
├── 5. MCP Server 开发
│   ├── Python SDK / TypeScript SDK
│   ├── 工具注册与实现
│   └── 传输方式选择
│
├── 6. 企业级 MCP 部署
│   ├── MCP Gateway / 代理
│   ├── 权限与审计
│   └── 工具治理
│
└── 7. 面试高频追问
    ├── MCP 解决了什么问题？
    ├── MCP 和 Function Calling 能一起用吗？
    └── MCP 的局限性是什么？
```

---

## 二、面试题与参考答案

---

### Q1：MCP 是什么？它解决了什么问题？⭐⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、阿里通义、字节飞书（2025.10）

**考点**：MCP 定义、核心动机、行业痛点

<details>
<summary>点击查看参考答案</summary>

#### 定义

MCP（Model Context Protocol）由 Anthropic 于 2024 年底提出，是一个**连接 LLM 应用和外部工具/数据源的标准化开放协议**。

#### 解决的问题：M×N 问题

在 MCP 之前，每接入一个新工具，需要为每个 LLM 厂商写一套适配：

```
没有 MCP 的世界（M × N 问题）：

  M 个 LLM 应用 × N 个工具 = M×N 个适配

  Claude ──→ 适配 ──→ GitHub
  Claude ──→ 适配 ──→ Slack
  Claude ──→ 适配 ──→ 数据库

  Cursor ──→ 适配 ──→ GitHub   （不同的适配方式）
  Cursor ──→ 适配 ──→ Slack
  Cursor ──→ 适配 ──→ 数据库

  自建Agent ──→ 适配 ──→ GitHub  （又要写一遍）
  ...

  每个应用接入每个工具都要单独开发适配代码
```

```
有了 MCP 的世界（M + N 问题）：

  M 个 LLM 应用 → MCP 协议 ← N 个工具

  Claude ──→ MCP ──→ GitHub MCP Server
  Cursor ──→ MCP ──→ GitHub MCP Server   （同一个 Server）
  自建Agent──→ MCP ──→ GitHub MCP Server

  工具只需实现一次 MCP Server
  应用只需实现一次 MCP Client
  连接方式标准化
```

#### 类比

| 类比 | 之前 | 之后 |
|------|------|------|
| 充电器 | 各品牌专用充电器 | USB-C 统一标准 |
| 数据库连接 | 每个框架写不同 driver | JDBC/ODBC 标准 |
| Web API | 各自定义协议 | HTTP/REST 标准 |
| LLM 工具接入 | 每个应用单独适配 | MCP 标准协议 |

#### MCP 的三个核心价值

1. **一次实现，处处可用**：工具开发者只需实现一次 MCP Server，所有支持 MCP 的 LLM 应用都能用
2. **动态工具发现**：不需要预定义工具列表，Client 连接 Server 后自动发现可用工具
3. **标准化通信**：统一的 JSON-RPC 协议，不再需要为每个厂商适配

#### 面试加分点

1. 能说出"M×N → M+N"这个核心价值
2. 能用 USB-C 类比解释
3. 强调 MCP 是"开放标准"而非 Anthropic 私有协议
4. 提到动态发现是区别于 Function Calling 的关键特性

</details>

---

### Q2：详细描述 MCP 的架构和通信方式 ⭐⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、字节飞书（2025.10）

**考点**：架构组件、通信流程、传输层选择

<details>
<summary>点击查看参考答案</summary>

#### 架构总览

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Host       │     │   Client     │     │   MCP Server     │
│  (宿主应用)  │────→│  (客户端)    │────→│                  │
│              │     │              │     │  ┌────────────┐  │
│  Claude      │     │  管理连接     │     │  │  Tools     │  │
│  Desktop     │     │  发现工具     │     │  │  Resources │  │
│  Cursor      │     │  转发调用     │     │  │  Prompts   │  │
│  自建 Agent  │     │              │     │  └────────────┘  │
│              │←────│              │←────│                  │
└──────────────┘     └──────────────┘     └──────────────────┘
                          │
                     传输层
                  stdio / SSE / WebSocket
```

#### 四个核心组件

| 组件 | 职责 | 例子 |
|------|------|------|
| **Host** | 宿主应用，用户交互的入口 | Claude Desktop、Cursor、自建 Agent |
| **Client** | 嵌在 Host 中，管理与 Server 的连接 | 每个 Server 对应一个 Client 实例 |
| **Server** | 暴露工具/资源/提示的服务端 | GitHub MCP Server、数据库 MCP Server |
| **传输层** | Client 和 Server 之间的通信方式 | stdio（本地）、SSE（远程）、WebSocket（远程） |

#### 通信协议：JSON-RPC 2.0

MCP 基于 JSON-RPC 2.0 协议通信：

```json
// Client → Server: 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {}
}

// Server → Client: 响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "search_repos",
        "description": "搜索 GitHub 仓库",
        "inputSchema": {
          "type": "object",
          "properties": {
            "query": {"type": "string"}
          },
          "required": ["query"]
        }
      }
    ]
  }
}

// Client → Server: 调用工具
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "search_repos",
    "arguments": {"query": "langchain"}
  }
}

// Server → Client: 工具结果
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [{"type": "text", "text": "找到 123 个仓库..."}]
  }
}
```

#### 三种传输方式

| 传输方式 | 场景 | 特点 |
|---------|------|------|
| **stdio** | 本地运行 | Server 作为 Host 的子进程，通过标准输入输出通信。最简单，适合本地工具。 |
| **SSE** | 远程运行 | Server-Sent Events，单向流。适合远程工具。 |
| **WebSocket** | 远程运行 | 双向通信。适合需要 Server 主动推送的场景。 |

#### 通信流程

```
1. 启动连接
   Host 启动 → Client 连接 Server（stdio/SSE/WS）

2. 能力协商
   Client ←→ Server 交换支持的能力（tools/resources/prompts）

3. 工具发现
   Client 发送 tools/list → Server 返回工具列表
   Client 将工具列表注册到 Host 的 LLM prompt 中

4. 工具调用
   LLM 输出 tool_call → Client 转发给 Server → Server 执行 → 返回结果

5. 断开
   Host 关闭 → Client 断开与 Server 的连接
```

#### 面试加分点

1. 能画出 Host/Client/Server 三层架构
2. 能说出 JSON-RPC 2.0 这个具体协议
3. 能解释三种传输方式的适用场景
4. 强调"能力协商"和"动态发现"是与 Function Calling 的关键区别

</details>

---

### Q3：MCP 的三种能力（Tools / Resources / Prompts）分别是什么？⭐⭐⭐⭐

**来源**：字节飞书（2025.10）、阿里通义

**考点**：三种能力的区别、使用场景

<details>
<summary>点击查看参考答案</summary>

#### 三种能力对比

| 能力 | 作用 | 方向 | 类比 |
|------|------|------|------|
| **Tools** | 可执行的函数/操作 | LLM → 外部（执行动作） | POST API |
| **Resources** | 可读取的数据/文件 | 外部 → LLM（提供上下文） | GET API |
| **Prompts** | 预定义的提示模板 | 用户 → LLM（标准化交互） | 模板引擎 |

#### Tools（工具）

Tools 是 LLM 可以调用的函数，和 Function Calling 中的工具一样：

```python
# MCP Server 注册一个工具
@server.tool()
def search_repos(query: str, language: str = "") -> str:
    """搜索 GitHub 仓库
    
    Args:
        query: 搜索关键词
        language: 编程语言筛选（可选）
    """
    # 调用 GitHub API
    results = github.search(query, language)
    return json.dumps(results)
```

特点：
- LLM **主动调用**
- 可以执行操作（搜索、发送邮件、修改数据）
- 有副作用

#### Resources（资源）

Resources 是 Server 暴露给 LLM 读取的数据源：

```python
# MCP Server 暴露一个资源
@server.resource("file:///{path}")
def read_file(path: str) -> str:
    """读取本地文件内容"""
    with open(path, "r") as f:
        return f.read()

@server.resource("db://users/{user_id}")
def get_user(user_id: str) -> str:
    """从数据库读取用户信息"""
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")
```

特点：
- LLM **被动读取**（不是主动调用）
- 提供上下文信息（文件内容、数据库记录、配置）
- 无副作用（只读）

**Resources vs RAG**：Resources 是 MCP 提供的一种标准化数据接入方式，功能上类似 RAG 的检索部分，但更通用 —— 任何数据源都可以作为 Resource 暴露。

#### Prompts（提示模板）

Prompts 是 Server 预定义的提示模板，用户可以选择使用：

```python
# MCP Server 提供一个提示模板
@server.prompt()
def code_review(code: str, language: str) -> str:
    """代码审查提示模板"""
    return f"""请审查以下 {language} 代码：

{code}

请从以下维度分析：
1. 代码质量
2. 潜在 bug
3. 性能问题
4. 安全风险
"""
```

特点：
- **用户选择**使用（不是 LLM 自动调用）
- 标准化常见任务的提示
- 可以带参数

#### 使用场景对比

```
场景：让 LLM 帮你审查一个代码文件

方式 1: 用 Resources
  → LLM 读取 file:///path/to/code.py（Resource）
  → LLM 自动审查

方式 2: 用 Prompts
  → 用户选择 "code_review" 提示模板
  → 填入 code 和 language 参数
  → 生成标准化审查提示

方式 3: 用 Tools
  → LLM 调用 read_file(path="code.py")（Tool）
  → 拿到内容后审查

三种方式都能实现，但语义不同：
  Resources = 提供数据（被动）
  Prompts = 标准化交互（用户选择）
  Tools = 执行操作（主动）
```

#### 面试加分点

1. 能区分三种能力的方向（主动/被动/用户选择）
2. 能举出每种能力的具体例子
3. 提到 Resources 和 RAG 的关系
4. 能解释同一个需求可以用不同能力实现，但语义不同

</details>

---

### Q4：MCP vs Function Calling 的本质区别？⭐⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、字节飞书（2025.10）、阿里通义

**考点**：概念辨析、层次差异、互补关系

<details>
<summary>点击查看参考答案</summary>

#### 本质区别：不同层次的东西

```
Function Calling 是 LLM 的能力（模型层）
  → LLM 能输出结构化的工具调用请求
  
MCP 是工具接入的协议（应用层）
  → 定义工具怎么发现、怎么连接、怎么通信

二者不是互斥的，而是互补的：
  MCP 发现工具 → 转化为 Function Calling 格式 → LLM 调用
```

#### 详细对比

| 维度 | Function Calling | MCP |
|------|-----------------|-----|
| **层次** | 模型层（LLM 的能力） | 应用层（工具接入协议） |
| **制定方** | OpenAI / Anthropic / Google（各厂商） | Anthropic（开放标准） |
| **工具定义** | 静态写在代码里 | 动态从 Server 发现 |
| **工具发现** | 开发者手动维护工具列表 | Client 自动从 Server 获取 |
| **工具复用** | 每个应用单独接入 | 一次实现，处处可用 |
| **通信协议** | HTTP API（各厂商不同） | JSON-RPC 2.0（统一） |
| **传输方式** | HTTP | stdio / SSE / WebSocket |
| **类比** | 各品牌充电线 | USB-C 标准 |

#### 关系图

```
┌──────────────────────────────────────────────┐
│              LLM 应用 (Host)                  │
│                                              │
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │  LLM        │    │  MCP Client         │ │
│  │  Function   │    │                     │ │
│  │  Calling    │◄───│  发现工具           │ │
│  │  (模型能力) │    │  转换为 FC 格式     │ │
│  └─────────────┘    │  转发调用           │ │
│                     └─────────┬───────────┘ │
└───────────────────────────────┼─────────────┘
                                │ MCP 协议
                                ▼
                     ┌─────────────────────┐
                     │  MCP Server         │
                     │  - GitHub           │
                     │  - Slack            │
                     │  - 数据库            │
                     └─────────────────────┘

工作流程：
1. MCP Client 从 Server 发现工具
2. 转换为 Function Calling 的 tools 格式
3. LLM 用 Function Calling 选择并调用工具
4. MCP Client 将调用转发给 Server
5. Server 执行并返回结果
6. 结果注入 LLM 上下文
```

#### 能否一起用？

**能，而且通常是一起用的**。MCP 负责工具的发现和通信，Function Calling 负责工具的选择和调用。典型流程：

```python
# 1. MCP Client 从 Server 发现工具
mcp_tools = await mcp_client.list_tools()

# 2. 转换为 OpenAI Function Calling 格式
fc_tools = [
    {
        "type": "function",
        "function": {
            "name": t.name,
            "description": t.description,
            "parameters": t.inputSchema,
        }
    }
    for t in mcp_tools
]

# 3. LLM 用 Function Calling 选择工具
response = openai.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=fc_tools,  # 用 MCP 发现的工具
)

# 4. 通过 MCP 执行选中的工具
for tc in response.choices[0].message.tool_calls:
    result = await mcp_client.call_tool(tc.function.name, json.loads(tc.function.arguments))
    # 5. 结果注入 LLM
    messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
```

#### 面试加分点

1. 强调"不同层次"这个核心区别 —— Function Calling 是模型能力，MCP 是应用协议
2. 能画出二者协作的流程图
3. 能说出"通常一起用"这个结论
4. 提到动态发现是 MCP 最大的差异化优势

</details>

---

### Q5：手写一个 MCP Server（Python）⭐⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、阿里 coding 面

**题目**：用 Python MCP SDK 实现一个简单的 MCP Server，暴露 2 个工具（搜索 + 计算）和 1 个资源（读取配置文件）。

<details>
<summary>点击查看参考答案</summary>

#### 安装依赖

```bash
pip install mcp
```

#### 完整实现

```python
# server.py — MCP Server 实现
from mcp.server.fastmcp import FastMCP
import json
import os

# 创建 MCP Server
mcp = FastMCP("my-tools-server")

# ========== 1. 工具定义 ==========

@mcp.tool()
def search_web(query: str) -> str:
    """
    搜索互联网获取信息。
    
    Args:
        query: 搜索关键词
    """
    # 模拟搜索
    db = {
        "特斯拉": "特斯拉 2024 年营收 976.9 亿美元",
        "比亚迪": "比亚迪 2024 年营收 7772 亿人民币",
    }
    for key, val in db.items():
        if key in query:
            return val
    return f"未找到 '{query}' 的搜索结果"

@mcp.tool()
def calculate(expression: str) -> str:
    """
    数学表达式计算。
    
    Args:
        expression: 数学表达式，如 '2+3*4'
    """
    try:
        allowed = set("0123456789+-*/(). ")
        if all(c in allowed for c in expression):
            return str(eval(expression))
        return "错误：包含不允许的字符"
    except (SyntaxError, ZeroDivisionError):
        return "错误：表达式无效"

# ========== 2. 资源定义 ==========

@mcp.resource("config://app")
def get_config() -> str:
    """读取应用配置"""
    config = {
        "app_name": "My Agent",
        "version": "1.0.0",
        "max_steps": 10,
        "model": "gpt-4o",
    }
    return json.dumps(config, indent=2)

# ========== 3. 提示模板 ==========

@mcp.prompt()
def analyze_data(data: str, question: str) -> str:
    """
    数据分析提示模板
    
    Args:
        data: 要分析的数据
        question: 分析问题
    """
    return f"""请分析以下数据并回答问题：

数据：
{data}

问题：{question}

请给出：
1. 数据概要
2. 问题回答
3. 关键发现
"""

# ========== 4. 启动 Server ==========

if __name__ == "__main__":
    # stdio 传输（本地运行，最简单）
    mcp.run(transport="stdio")
```

#### 配置到 Claude Desktop

```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "my-tools": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

#### 配置到 Cursor

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "my-tools": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

#### 配置到自建 Agent

```python
# client.py — 在自建 Agent 中使用 MCP
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_mcp_tools():
    # 连接 MCP Server
    server_params = StdioServerParameters(
        command="python",
        args=["/path/to/server.py"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            await session.initialize()
            
            # 发现工具
            tools = await session.list_tools()
            print("可用工具：", [t.name for t in tools.tools])
            
            # 调用工具
            result = await session.call_tool("search_web", {"query": "特斯拉营收"})
            print("搜索结果：", result.content[0].text)
            
            # 读取资源
            config = await session.read_resource("config://app")
            print("配置：", config.contents[0].text)

asyncio.run(use_mcp_tools())
```

#### 面试追问

**Q：MCP Server 用 stdio 和 SSE 有什么区别？**
A：stdio 是本地进程通信，Server 作为 Host 的子进程运行，最简单但只能本地用。SSE 是远程通信，Server 独立部署，可以跨网络访问。

**Q：一个 Host 能连接多个 MCP Server 吗？**
A：能。Host 可以为每个 Server 创建一个 Client 实例，管理多个连接。所有 Server 的工具都会汇总到 LLM 的工具列表中。

**Q：MCP Server 怎么做权限控制？**
A：MCP 协议本身不定义权限模型，由 Host 和 Server 各自实现。常见做法：Server 端校验调用者身份，Host 端做风险分级和 HITL。

</details>

---

### Q6：MCP 的动态工具发现机制是怎么工作的？⭐⭐⭐

**来源**：字节 AI 应用研发（2026.01）

**考点**：发现流程、与静态注册的对比

<details>
<summary>点击查看参考答案</summary>

#### 动态发现流程

```
1. Host 启动 → 创建 MCP Client

2. Client 连接 Server
   stdio: 启动 Server 子进程
   SSE:   建立 HTTP 连接

3. 能力协商（Initialize）
   Client → Server: {
     "method": "initialize",
     "params": {"capabilities": {"tools": {}, "resources": {}}}
   }
   Server → Client: {
     "result": {"capabilities": {"tools": {}, "resources": {}, "prompts": {}}}
   }

4. 工具发现（tools/list）
   Client → Server: {"method": "tools/list"}
   Server → Client: {
     "result": {
       "tools": [
         {"name": "search_web", "description": "...", "inputSchema": {...}},
         {"name": "calculate", "description": "...", "inputSchema": {...}}
       ]
     }
   }

5. Client 将工具注册到 Host
   → 转换为 LLM 可用的 tools 格式
   → 放入 LLM prompt

6. 工具变更通知
   Server 可以通知 Client 工具列表变更
   → Client 重新拉取 tools/list
```

#### 与静态注册对比

| 维度 | 静态注册（Function Calling） | 动态发现（MCP） |
|------|---------------------------|----------------|
| 工具列表 | 开发者在代码中硬编码 | 运行时从 Server 获取 |
| 新增工具 | 改代码、重新部署 | Server 端更新即可 |
| 工具版本 | 手动管理 | Server 可以返回版本信息 |
| 多应用复用 | 每个应用单独写 | 所有应用共享一个 Server |
| 适用场景 | 工具固定且少 | 工具多、需要灵活扩展 |

#### 动态发现的挑战

1. **Schema 兼容性**：Server 返回的 inputSchema 需要适配不同 LLM 厂商的格式
2. **工具命名冲突**：多个 Server 可能有同名工具，需要命名空间隔离
3. **工具数量控制**：多个 Server 的工具加起来可能太多，需要路由

```python
# 多 Server 命名空间隔离
tools = []
for server_name, client in mcp_clients.items():
    server_tools = await client.list_tools()
    for tool in server_tools:
        # 加前缀避免冲突
        tools.append({
            "name": f"{server_name}__{tool.name}",
            "description": tool.description,
            "parameters": tool.inputSchema,
        })
```

#### 面试加分点

1. 能说出发现的完整流程（连接→协商→发现→注册）
2. 能对比静态和动态的优劣
3. 提到工具命名冲突这个实际问题
4. 提到工具变更通知这个高级特性

</details>

---

### Q7：企业级 MCP 部署怎么做？有哪些架构考虑？⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、阿里钉钉

**考点**：生产部署、网关设计、治理

<details>
<summary>点击查看参考答案</summary>

#### 企业级 MCP 架构

```
┌─ Agent 应用 ─────────────────────────────────┐
│  多个 Agent 实例                             │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─ MCP Gateway (网关) ─────────────────────────┐
│  - 统一入口                                  │
│  - 认证鉴权                                  │
│  - 工具路由（多个 Server 的工具聚合）         │
│  - 限流熔断                                  │
│  - 审计日志                                  │
└──────────────────┬──────────────────────────┘
                   │
      ┌────────────┼────────────┐
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ MCP      │ │ MCP      │ │ MCP      │
│ Server   │ │ Server   │ │ Server   │
│ (内部API)│ │ (数据库) │ │ (第三方) │
└──────────┘ └──────────┘ └──────────┘
```

#### MCP Gateway 的核心职责

| 职责 | 说明 |
|------|------|
| **认证鉴权** | 校验 Agent 的身份和权限，不同 Agent 可用不同工具集 |
| **工具聚合** | 聚合多个 Server 的工具，统一暴露给 Agent |
| **命名空间** | 避免不同 Server 的工具名冲突 |
| **限流熔断** | 防止某个工具被过度调用 |
| **审计日志** | 记录所有工具调用，用于合规和安全审计 |
| **灰度发布** | 新工具先灰度给部分 Agent 使用 |

#### 部署模式

**模式一：本地 stdio（开发环境）**

```
Agent ← stdio → MCP Server（本地进程）
最简单，适合开发和本地工具
```

**模式二：远程 SSE + Gateway（生产环境）**

```
Agent ← HTTPS → MCP Gateway ← 内部网络 → 多个 MCP Server
适合生产部署，支持多实例、负载均衡
```

**模式三：混合模式**

```
Agent ← stdio → 本地工具（文件读取、代码执行）
Agent ← SSE → 远程 Gateway → 企业服务（CRM/ERP/数据库）
```

#### 安全考虑

```
┌─ 安全层 ──────────────────────────────────┐
│                                           │
│  1. 传输安全：TLS 加密所有通信             │
│  2. 认证：Agent → Gateway 用 API Key      │
│  3. 授权：不同 Agent 有不同工具权限        │
│  4. 审计：记录所有工具调用的 Trace         │
│  5. 沙箱：第三方 Server 在容器中运行       │
│  6. 敏感数据脱敏：工具返回前过滤           │
│                                           │
└───────────────────────────────────────────┘
```

#### 面试加分点

1. 能画出 Gateway 架构，不只是简单连接
2. 提到命名空间、限流、审计这些生产级需求
3. 能对比三种部署模式的适用场景
4. 强调安全层次（传输+认证+授权+审计+沙箱）

</details>

---

### Q8：MCP 有哪些局限性？你觉得未来会怎么发展？⭐⭐⭐

**来源**：字节安全与治理（2026.02）、阿里达摩院

**考点**：批判性思维、前瞻性

<details>
<summary>点击查看参考答案</summary>

#### 当前局限性

| 局限 | 说明 | 影响 |
|------|------|------|
| **生态不成熟** | 工具数量和种类还在早期 | 很多场景找不到现成 MCP Server |
| **性能开销** | 每次工具调用经过 Client→Server 转发 | 比直接调函数多一层网络/进程开销 |
| **无标准权限模型** | 权限由各方自己实现 | 安全实现不统一，容易有漏洞 |
| **无状态** | MCP Server 通常无状态 | 复杂工作流需 Host 管理 |
| **调试困难** | 跨进程通信，调试链路长 | 出问题难定位 |
| **厂商支持不均** | Anthropic 全面支持，OpenAI 尚未原生支持 | 跨厂商体验不一致 |

#### 发展趋势

1. **更多厂商支持**：OpenAI、Google 预计会逐步支持 MCP，形成统一生态
2. **MCP Gateway 标准化**：网关层的认证、路由、审计能力可能标准化
3. **A2A（Agent-to-Agent）协议**：MCP 解决 Agent↔Tool，还需要 Agent↔Agent 的标准协议
4. **工具市场**：类似 App Store 的 MCP Server 市场，开发者上传/销售工具
5. **与 Function Calling 深度融合**：LLM 原生理解 MCP，不需要 Client 做格式转换

#### 面试加分点

1. 不盲目吹捧 MCP，能说出具体局限
2. 能区分"MCP 解决了什么"和"还没解决什么"
3. 提到 A2A 协议这个更前沿的方向
4. 表达"标准会演进，但方向正确"的观点

</details>

---

### Q9：如何在自建 Agent 中集成 MCP？完整流程是什么？⭐⭐⭐⭐

**来源**：字节飞书（2025.10）、美团 AI 平台

**考点**：集成能力、工程实践

<details>
<summary>点击查看参考答案</summary>

#### 集成架构

```
自建 Agent
├── Agent Loop（ReAct 循环）
├── MCP Client Manager（管理多个 MCP Server 连接）
│   ├── Client 1 → GitHub MCP Server
│   ├── Client 2 → 数据库 MCP Server
│   └── Client 3 → 自定义工具 MCP Server
└── Tool Router（工具路由，当工具太多时筛选）
```

#### 完整集成代码

```python
import asyncio
import json
import openai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPAgent:
    """集成 MCP 的 Agent"""
    
    def __init__(self, server_configs: list, model: str = "gpt-4o"):
        """
        server_configs: MCP Server 配置列表
            [{"name": "github", "command": "python", "args": ["github_server.py"]},
             {"name": "db", "command": "python", "args": ["db_server.py"]}]
        """
        self.model = model
        self.server_configs = server_configs
        self.sessions = {}      # server_name → ClientSession
        self.all_tools = []     # 所有 Server 的工具汇总
    
    async def connect_servers(self):
        """连接所有 MCP Server 并发现工具"""
        for config in self.server_configs:
            name = config["name"]
            params = StdioServerParameters(
                command=config["command"],
                args=config.get("args", []),
                env=config.get("env"),
            )
            
            # 建立连接
            read, write = await stdio_client(params).__aenter__()
            session = await ClientSession(read, write).__aenter__()
            await session.initialize()
            
            # 发现工具
            tools_result = await session.list_tools()
            
            self.sessions[name] = session
            
            # 转换为 OpenAI Function Calling 格式
            for tool in tools_result.tools:
                self.all_tools.append({
                    "type": "function",
                    "function": {
                        "name": f"{name}__{tool.name}",  # 命名空间隔离
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                    "_server": name,       # 记录来源 Server
                    "_original_name": tool.name,
                })
            
            print(f"已连接 {name}，发现 {len(tools_result.tools)} 个工具")
    
    async def call_tool(self, tool_meta: dict, args: dict) -> str:
        """通过 MCP 调用工具"""
        server_name = tool_meta["_server"]
        original_name = tool_meta["_original_name"]
        session = self.sessions[server_name]
        
        result = await session.call_tool(original_name, args)
        return result.content[0].text if result.content else ""
    
    async def run(self, user_query: str, max_steps: int = 10) -> str:
        """Agent Loop"""
        messages = [
            {"role": "system", "content": "你是一个能使用工具的智能助手。"},
            {"role": "user", "content": user_query},
        ]
        
        # 准备 OpenAI 格式的工具列表
        fc_tools = [{"type": "function", "function": t["function"]} for t in self.all_tools]
        tool_map = {t["function"]["name"]: t for t in self.all_tools}
        
        for step in range(max_steps):
            print(f"\n--- Step {step+1} ---")
            
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model=self.model,
                messages=messages,
                tools=fc_tools,
                tool_choice="auto",
            )
            
            msg = response.choices[0].message
            messages.append(msg)
            
            if not msg.tool_calls:
                return msg.content
            
            for tc in msg.tool_calls:
                func_name = tc.function.name
                func_args = json.loads(tc.function.arguments)
                
                print(f"调用: {func_name}({func_args})")
                
                if func_name in tool_map:
                    result = await self.call_tool(tool_map[func_name], func_args)
                else:
                    result = f"未知工具: {func_name}"
                
                print(f"结果: {result}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        
        return "达到最大步数"
    
    async def close(self):
        """关闭所有连接"""
        for session in self.sessions.values():
            await session.__aexit__(None, None, None)


# 使用示例
async def main():
    agent = MCPAgent(
        server_configs=[
            {"name": "search", "command": "python", "args": ["search_server.py"]},
            {"name": "db", "command": "python", "args": ["db_server.py"]},
        ]
    )
    
    await agent.connect_servers()
    answer = await agent.run("查一下特斯拉的营收，然后从数据库查历史数据对比")
    print(answer)
    await agent.close()

asyncio.run(main())
```

#### 关键设计点

1. **命名空间隔离**：工具名加 `server_name__` 前缀，避免冲突
2. **异步连接管理**：所有 MCP 操作都是异步的
3. **工具来源记录**：每个工具记录来自哪个 Server，调用时路由到正确的 Session
4. **生命周期管理**：Agent 结束时关闭所有连接

#### 面试加分点

1. 能写出完整的集成代码，不只是概念
2. 处理了命名空间冲突
3. 考虑了连接生命周期管理
4. 能解释 MCP Client 如何与 Agent Loop 集成

</details>

---

### Q10：大厂面试场景题 — 设计一个企业内部 MCP 工具平台 ⭐⭐⭐⭐

**来源**：字节 Agent 平台（2025.12）、阿里钉钉

**题目**：为公司设计一个内部 MCP 工具平台，让各部门的 Agent 都能安全地使用公司内部工具（HR 系统、财务系统、代码仓库等）。

<details>
<summary>点击查看参考答案</summary>

#### 需求分析

```
用户：公司内部多个部门的 Agent
  - HR Agent → 需要 HR 系统工具
  - 财务 Agent → 需要财务系统工具
  - 研发 Agent → 需要代码仓库工具
  - 通用 Agent → 可能需要跨部门工具

挑战：
  1. 各系统有不同认证方式
  2. 不同 Agent 有不同权限
  3. 工具调用需要审计
  4. 部门间工具隔离
```

#### 架构设计

```
┌─ 各部门 Agent ────────────────────────────────┐
│  HR Agent  │  财务 Agent  │  研发 Agent  │ ...│
└──────┬────────┬──────────────┬────────────┬───┘
       │        │              │            │
       ▼        ▼              ▼            ▼
┌─ MCP Gateway ─────────────────────────────────┐
│                                               │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ 认证    │  │ 权限      │  │ 工具路由    │ │
│  │ (SSO)   │  │ (RBAC)   │  │ (按部门)    │ │
│  └─────────┘  └──────────┘  └─────────────┘ │
│  ┌─────────┐  ┌──────────┐  ┌─────────────┐ │
│  │ 限流    │  │ 审计      │  │ 监控告警    │ │
│  └─────────┘  └──────────┘  └─────────────┘ │
└──────────────────┬────────────────────────────┘
                   │
      ┌────────────┼─────────────┐
      ▼            ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ HR MCP   │ │ 财务 MCP │ │ 研发 MCP │
│ Server   │ │ Server   │ │ Server   │
│          │ │          │ │          │
│- 查员工  │ │- 查预算  │ │- 查代码  │
│- 请假    │ │- 报销    │ │- 提PR    │
│- 考勤    │ │- 审批    │ │- 查bug   │
└──────────┘ └──────────┘ └──────────┘
```

#### 关键设计

**1. 权限模型（RBAC）**

```python
TOOL_PERMISSIONS = {
    "hr_agent": ["hr__get_employee", "hr__submit_leave"],
    "finance_agent": ["finance__get_budget", "finance__submit_expense"],
    "dev_agent": ["dev__search_code", "dev__create_pr", "dev__get_bug"],
    "general_agent": ["hr__get_employee", "dev__search_code"],  # 只读权限
}

def check_permission(agent_id: str, tool_name: str) -> bool:
    allowed = TOOL_PERMISSIONS.get(agent_id, [])
    return tool_name in allowed
```

**2. 审计日志**

```python
async def audit_log(agent_id, tool_name, args, result, timestamp):
    """记录审计日志"""
    log_entry = {
        "timestamp": timestamp,
        "agent_id": agent_id,
        "tool": tool_name,
        "args": sanitize_args(args),  # 脱敏
        "result_size": len(str(result)),
        "success": "错误" not in str(result),
    }
    await audit_db.insert(log_entry)
```

**3. 工具发现按权限过滤**

```python
async def list_tools_for_agent(agent_id: str) -> list:
    """根据 Agent 权限返回可用工具"""
    all_tools = await gateway.list_all_tools()
    allowed = TOOL_PERMISSIONS.get(agent_id, [])
    return [t for t in all_tools if t["name"] in allowed]
```

**4. 敏感操作分级**

```python
SENSITIVE_TOOLS = {
    "finance__transfer_money": "high",    # 转账：需审批
    "hr__modify_salary": "high",          # 改薪资：需审批
    "dev__merge_pr": "medium",            # 合PR：需确认
    "hr__get_employee": "low",            # 查员工：自动
}

async def execute_with_permission(agent_id, tool_name, args):
    risk = SENSITIVE_TOOLS.get(tool_name, "low")
    if risk == "high":
        # 发送审批请求给部门主管
        approval = await request_approval(agent_id, tool_name, args)
        if not approval.approved:
            return "操作未获批准"
    # 执行工具
    return await mcp_gateway.call_tool(tool_name, args)
```

#### 面试加分点

1. 考虑了权限隔离（不同 Agent 不同工具集）
2. 设计了审计日志（合规需求）
3. 敏感操作分级 + 审批流
4. 工具发现按权限过滤
5. 能和前面学过的安全、成本控制知识串联

</details>

---

## 三、当日小结

### 核心知识点回顾

| 序号 | 知识点 | 一句话总结 | 面试频率 |
|------|--------|------------|---------|
| 1 | MCP 定义 | Anthropic 提出的工具接入开放标准，解决 M×N 问题 | ⭐⭐⭐⭐⭐ |
| 2 | MCP 架构 | Host → Client → Server，JSON-RPC 2.0 通信 | ⭐⭐⭐⭐⭐ |
| 3 | 三种能力 | Tools（执行）/ Resources（读取）/ Prompts（模板） | ⭐⭐⭐⭐ |
| 4 | MCP vs Function Calling | 不同层次：MCP 是协议（应用层），FC 是能力（模型层） | ⭐⭐⭐⭐⭐ |
| 5 | MCP Server 开发 | FastMCP + @mcp.tool() 装饰器 | ⭐⭐⭐⭐⭐ |
| 6 | 动态工具发现 | Client 连接 Server 后自动 list_tools | ⭐⭐⭐ |
| 7 | 企业部署 | MCP Gateway + 权限 + 审计 + 限流 | ⭐⭐⭐⭐ |
| 8 | MCP 局限性 | 生态早期、性能开销、无标准权限模型 | ⭐⭐⭐ |
| 9 | Agent 集成 | MCP Client Manager + 命名空间隔离 + 异步管理 | ⭐⭐⭐⭐ |
| 10 | 企业平台设计 | RBAC 权限 + 审计 + 分级 + Gateway | ⭐⭐⭐⭐ |

### 面试速记卡

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：MCP 是什么？解决了什么问题？
答：Anthropic 提出的工具接入开放标准。
    解决 M×N 问题：M 个应用 × N 个工具 → M+N。
    一次实现 MCP Server，所有支持 MCP 的应用都能用。
    类比：USB-C 之于充电器。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：MCP 和 Function Calling 是什么关系？
答：不同层次的东西——
    Function Calling 是 LLM 的能力（模型层），定义 LLM 怎么输出工具调用。
    MCP 是工具接入协议（应用层），定义工具怎么发现、连接、通信。
    通常一起用：MCP 发现工具 → 转为 FC 格式 → LLM 调用。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：MCP 的三种能力？
答：Tools（工具）→ LLM 主动调用，有副作用（如发邮件）
    Resources（资源）→ LLM 被动读取，无副作用（如读文件）
    Prompts（提示）→ 用户选择使用，标准化任务模板

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：MCP 的架构？
答：Host（宿主应用）→ Client（管理连接）→ Server（暴露工具）
    通信协议：JSON-RPC 2.0
    传输方式：stdio（本地）/ SSE（远程）/ WebSocket（远程）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问：企业级 MCP 怎么部署？
答：MCP Gateway 统一入口 →
    认证（SSO）+ 权限（RBAC）+ 限流 + 审计 + 监控
    → 多个 MCP Server（按部门/系统分）
    敏感操作分级：low 自动 / medium 确认 / high 审批

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 易错点提醒

| 易错点 | 错误回答 | 正确理解 |
|--------|---------|---------|
| "MCP 是 Function Calling 的替代" | ❌ | ✅ 不同层次，互补关系，通常一起用 |
| "MCP 是 Anthropic 私有协议" | ❌ | ✅ 是开放标准，任何厂商都可以实现 |
| "MCP 只能用于 Claude" | ❌ | ✅ Cursor、自建 Agent 等都支持 |
| "Resources 就是 RAG" | ❌ | ✅ Resources 更通用，RAG 是检索+生成，Resources 是数据暴露 |
| "stdio 和 SSE 效果一样" | ❌ | ✅ stdio 只能本地，SSE 支持远程 |

### 自测检查清单

- [ ] 能否在 1 分钟内说出 MCP 的定义和解决的问题？
- [ ] 能否画出 Host/Client/Server 架构和通信流程？
- [ ] 能否说出三种能力的区别和各自使用场景？
- [ ] 能否解释 MCP 和 Function Calling 的关系？
- [ ] 能否手写一个简单的 MCP Server？
- [ ] 能否说出动态工具发现的流程？
- [ ] 能否设计企业级 MCP Gateway 架构？
- [ ] 能否说出 MCP 的至少三个局限性？
- [ ] 能否在自建 Agent 中集成 MCP Client？
- [ ] 能否设计一个企业内部 MCP 工具平台？

### 明日预告

Day 05 将深入 **Agent 记忆系统**，包括：
- 四层记忆架构（工作记忆/短期/长期/外部）
- 记忆的写入、读取、遗忘策略
- 向量数据库在记忆系统中的角色
- 上下文压缩与摘要技术
- 记忆系统设计面试题

---

> **学习建议**：今天重点是"理解协议 + 动手实现"。建议：
> 1. 自己写一个简单的 MCP Server 并在 Claude Desktop 或 Cursor 中测试
> 2. 理解 MCP 和 Function Calling 的层次关系，这是面试最高频的追问
> 3. 完成自测检查清单
> 4. 思考：你公司内部有哪些系统可以封装成 MCP Server？
