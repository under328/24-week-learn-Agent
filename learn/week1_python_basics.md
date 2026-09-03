# 第1月第1周：Python 基础速通

> 适用对象：有 Vue/JavaScript/TypeScript 前端经验的开发者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：能独立写 Python 脚本，掌握后续 Agent 开发所需的 Python 核心能力

---

## Day 1：Python 环境搭建 + 基础语法

### 1.1 环境安装

**安装 Python 3.11+**（推荐 3.12）

```bash
# Windows: 去 python.org 下载安装包，安装时勾选 "Add Python to PATH"
# 验证安装
python --version    # 应显示 Python 3.11.x 或更高
pip --version       # 应显示 pip 对应版本
```

**创建项目目录**

```bash
mkdir -p ~/agent-learning/week1
cd ~/agent-learning/week1
```

### 1.2 与 JavaScript 的速查对照

你已经有 JS 基础，以下是核心语法对照，帮你快速迁移：

| 概念 | JavaScript | Python |
|---|---|---|
| 变量声明 | `let x = 1; const y = 2` | `x = 1` （无 let/const，全靠约定） |
| 常量约定 | `const MAX = 100` | `MAX = 100` （全大写命名约定，语言不强制） |
| 字符串格式化 | `` `Hello ${name}` `` | `f"Hello {name}"` （f-string） |
| 数组 | `[1, 2, 3]` | `[1, 2, 3]` （叫 list） |
| 对象/字典 | `{a: 1, b: 2}` | `{"a": 1, "b": 2}` （叫 dict） |
| 箭头函数 | `(x) => x * 2` | `lambda x: x * 2` |
| 解构 | `const {a, b} = obj` | `a, b = obj["a"], obj["b"]` |
| 空值 | `null`, `undefined` | `None` |
| 布尔 | `true`, `false` | `True`, `False` |
| 逻辑运算 | `&&`, `\|\|`, `!` | `and`, `or`, `not` |
| 包管理 | `npm install xxx` | `pip install xxx` |
| 导入 | `import { x } from 'mod'` | `from mod import x` |

### 1.3 必练基础语法

创建文件 `day1_basics.py`：

```python
# === 1. 变量与数据类型 ===
name = "Agent开发者"
age = 25
score = 98.5
is_active = True
nothing = None

# f-string 格式化（最常用）
print(f"你好，{name}，年龄{age}，分数{score}")

# === 2. 列表（List）—— 对应 JS 数组 ===
tools = ["search", "calculator", "code_runner"]
print(tools[0])           # "search"
print(len(tools))         # 3
tools.append("translator")  # 末尾添加
tools.remove("search")      # 按值删除

# 列表推导式（超常用！JS 没有直接对应）
squares = [x**2 for x in range(10)]           # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
even_squares = [x**2 for x in range(10) if x % 2 == 0]  # [0, 4, 16, 36, 64]

# === 3. 字典（Dict）—— 对应 JS 对象 ===
agent_config = {
    "name": "helper",
    "model": "gpt-4",
    "temperature": 0.7,
    "tools": ["search", "calculator"]
}
print(agent_config["name"])         # "helper"
agent_config["max_tokens"] = 2048   # 添加键值

# 遍历字典
for key, value in agent_config.items():
    print(f"{key}: {value}")

# 安全取值（不存在不会报错）
model = agent_config.get("model", "gpt-3.5")  # 有则取值，无则默认

# === 4. 条件判断 ===
score = 85
if score >= 90:
    print("优秀")
elif score >= 60:
    print("及格")
else:
    print("不及格")

# === 5. 循环 ===
for tool in tools:
    print(f"可用工具: {tool}")

# range 用法
for i in range(5):       # 0,1,2,3,4
    print(i)

for i in range(2, 8):    # 2,3,4,5,6,7
    print(i)

for i in range(0, 10, 2): # 0,2,4,6,8
    print(i)

# === 6. 函数 ===
def greet(name, greeting="你好"):
    """打招呼函数（三引号是文档字符串）"""
    return f"{greeting}，{name}！"

print(greet("小明"))              # 你好，小明！
print(greet("小明", "Hello"))     # Hello，小明！

# 关键字参数（JS 没有的特性）
print(greet(greeting="Hi", name="小红"))  # Hi，小红！
```

### 1.4 今日练习

写一个 `practice_day1.py`，完成以下任务：

1. 创建一个字典 `agent_profile`，包含 name、role、tools（列表）、capabilities（字典）
2. 写一个函数 `describe_agent(profile)`，返回格式化描述字符串
3. 用列表推导式从 tools 列表筛选出长度大于 5 的工具名
4. 写一个函数 `merge_configs(*configs)`，接收多个字典并合并（后面的覆盖前面的）

<details>
<summary>参考答案</summary>

```python
# 1
agent_profile = {
    "name": "CodeHelper",
    "role": "编程助手",
    "tools": ["search", "calculator", "code_runner", "translator"],
    "capabilities": {
        "language": "Python",
        "max_tokens": 4096
    }
}

# 2
def describe_agent(profile):
    tools_str = ", ".join(profile["tools"])
    return f"{profile['name']}({profile['role']}), 工具: [{tools_str}]"

print(describe_agent(agent_profile))

# 3
long_tools = [t for t in agent_profile["tools"] if len(t) > 5]
print(long_tools)  # ["calculator", "code_runner", "translator"]

# 4
def merge_configs(*configs):
    result = {}
    for config in configs:
        result.update(config)
    return result

c1 = {"a": 1, "b": 2}
c2 = {"b": 3, "c": 4}
print(merge_configs(c1, c2))  # {"a": 1, "b": 3, "c": 4}
```

</details>

---

## Day 2：类型提示（Type Hints）

> Agent 开发中类型提示极其重要 —— LLM 的输入输出都是结构化数据，类型提示是文档也是保障。

### 2.1 基础类型标注

创建 `day2_type_hints.py`：

```python
# === 1. 基本类型 ===
name: str = "Agent"
age: int = 25
score: float = 98.5
is_active: bool = True

# === 2. 容器类型（需要从 typing 导入） ===
from typing import List, Dict, Tuple, Optional, Union

tools: List[str] = ["search", "calculator"]
config: Dict[str, any] = {"temperature": 0.7}
coord: Tuple[float, float] = (39.9, 116.4)

# Optional：可能为 None
# 等价于 Union[str, None]
nickname: Optional[str] = None

# Union：多种可能类型
result: Union[str, int] = "success"  # 可以是字符串或整数

# === 3. 函数类型标注 ===
def search(query: str, top_k: int = 5) -> List[str]:
    """搜索相关文档"""
    return [f"结果{i}" for i in range(top_k)]

def get_agent_name(agent_id: int) -> Optional[str]:
    """根据ID获取名称，找不到返回None"""
    agents = {1: "helper", 2: "coder"}
    return agents.get(agent_id)

# === 4. Pydantic 模型（重点！Agent 开发必备） ===
# pip install pydantic
from pydantic import BaseModel, Field

class ToolDefinition(BaseModel):
    """工具定义 —— 这是 Agent 中最常见的数据结构"""
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具功能描述")
    parameters: Dict[str, any] = Field(default_factory=dict, description="参数定义")

class AgentConfig(BaseModel):
    """Agent 配置"""
    name: str = Field(..., min_length=1, max_length=50)
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.7, ge=0, le=2)
    tools: List[ToolDefinition] = Field(default_factory=list)
    max_tokens: int = Field(default=2048, gt=0)

# 使用
tool = ToolDefinition(
    name="calculator",
    description="数学计算器",
    parameters={"expression": {"type": "string", "description": "数学表达式"}}
)

config = AgentConfig(
    name="CodeHelper",
    tools=[tool]
)

# 自动类型转换（Pydantic 的强大之处）
config2 = AgentConfig(name="Test", temperature="0.5")  # 字符串会自动转为 float
print(config2.temperature)  # 0.5 (float)

# 序列化
print(config.model_dump_json(indent=2))  # 转JSON字符串
print(config.model_dump())               # 转字典

# === 5. 现代 Python 3.10+ 语法（更简洁） ===
# 3.10+ 可以用 | 代替 Union
# result: str | int = "hello"
# 3.9+ 可以直接用内置类型
# tools: list[str] = ["search"]
```

### 2.2 为什么 Pydantic 对 Agent 开发如此重要

[Pydantic](https://github.com/pydantic/PYDANTIC)
[Pydantic使用指南](https://blog.csdn.net/footless_bird/article/details/134183693?ops_request_misc=&request_id=&biz_id=102&utm_term=Pydantic&utm_medium=distribute.pc_search_result.none-task-blog-2~all~sobaiduweb~default-8-134183693.142^v102^pc_search_result_base4&spm=1018.2226.3001.4187)

```
Agent 的核心数据流：

用户输入 → Pydantic 验证 → LLM 调用 → Pydantic 解析输出 → 工具调用 → Pydantic 验证参数 → ...

每个环节都需要严格的类型校验，Pydantic 就是干这个的。
LangChain、OpenAI SDK、LlamaIndex 内部都大量使用 Pydantic。
```

### 2.3 今日练习

写一个 `practice_day2.py`：

1. 用 Pydantic 定义一个 `ChatMessage` 模型：role（system/user/assistant）、content、name（可选）
2. 定义 `ChatResponse` 模型：message（ChatMessage）、finish_reason、usage（prompt_tokens + completion_tokens）
3. 写一个函数 `build_messages(prompt: str, system: str = "") -> List[ChatMessage]`
4. 给 ChatMessage 的 role 加校验，只允许 "system"、"user"、"assistant"

<details>
<summary>参考答案</summary>

```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

# Literal（用于指定变量只能是特定的 literal 值）
# Color = Literal['red', 'green', 'blue']

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"] = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    name: Optional[str] = Field(default=None, description="发送者名称")

class Usage(BaseModel):
    prompt_tokens: int = Field(..., ge=0)
    completion_tokens: int = Field(..., ge=0)

class ChatResponse(BaseModel):
    message: ChatMessage
    finish_reason: str = Field(default="stop")
    usage: Usage

def build_messages(prompt: str, system: str = "") -> List[ChatMessage]:
    messages = []
    if system:
        messages.append(ChatMessage(role="system", content=system))
    messages.append(ChatMessage(role="user", content=prompt))
    return messages

# 测试
msgs = build_messages("你好", "你是一个助手")
for m in msgs:
    print(f"[{m.role}] {m.content}")

response = ChatResponse(
    message=ChatMessage(role="assistant", content="你好！有什么可以帮你？"),
    finish_reason="stop",
    usage=Usage(prompt_tokens=10, completion_tokens=8)
)
print(response.model_dump_json(indent=2))
```

</details>

---

## Day 3：包管理 + 虚拟环境

> 这一天解决 "在我电脑上能跑" 的问题，是工程化的第一步。

### 3.1 虚拟环境

```bash
# 为什么需要虚拟环境？—— 隔离项目依赖，避免版本冲突
# 就像 Node.js 的 node_modules，但更底层

# 创建虚拟环境
cd ~/agent-learning/week1
python -m venv venv

# 激活虚拟环境（Windows Git Bash）
source venv/Scripts/activate

# 激活后命令行前面会出现 (venv)
# 验证
which python  # 应该指向 venv 内的 python

# 退出虚拟环境
# deactivate
```

### 3.2 pip 包管理

```bash
# 安装包
pip install requests httpx pydantic

# 查看已安装的包
pip list

# 导出依赖清单（类似 package.json）
pip freeze > requirements.txt

# 从清单安装（别人拿到你的项目后）
pip install -r requirements.txt

# 升级包
pip install --upgrade requests

# 卸载包
pip uninstall requests
```

### 3.3 项目结构规范

```
agent-learning/
└── week1/
    ├── venv/                  # 虚拟环境（不提交到git）
    ├── requirements.txt       # 依赖清单
    ├── day1_basics.py
    ├── day2_type_hints.py
    ├── day3_http_requests.py
    ├── day4_async.py
    ├── day5_file_io.py
    └── practice/              # 练习目录
```

### 3.4 httpx —— 比 requests 更现代的 HTTP 客户端

> 选 httpx 而不是 requests 的原因：httpx 同时支持同步和异步，Agent 开发大量使用异步

创建 `day3_http_requests.py`：

```python
# pip install httpx
import httpx

# === 同步请求 ===

# GET 请求
response = httpx.get("https://httpbin.org/get", params={"key": "value"})
print(response.status_code)   # 200
print(response.json())        # 自动解析 JSON

# POST 请求（JSON body）
response = httpx.post(
    "https://httpbin.org/post",
    json={"message": "hello", "model": "gpt-4"}
)
print(response.json())

# === 带超时和错误处理 ===
try:
    response = httpx.get("https://httpbin.org/delay/5", timeout=3.0)
except httpx.TimeoutException:
    print("请求超时")
except httpx.HTTPStatusError as e:
    print(f"HTTP错误: {e.response.status_code}")

# === 使用 Client（推荐，复用连接） ===
with httpx.Client(base_url="https://httpbin.org", timeout=10.0) as client:
    # 会话内所有请求共享连接池
    r1 = client.get("/get")
    r2 = client.post("/post", json={"data": "test"})
    print(r1.json()["args"])
    print(r2.json()["json"])

# === 模拟调用 LLM API（重点练习） ===
def call_llm(messages: list, model: str = "glm-4", api_key: str = "your-key"):
    """调用智谱 GLM API 的函数模板"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

# 实际调用时替换 api_key
# answer = call_llm([{"role": "user", "content": "你好"}])
```

### 3.5 今日练习

写一个 `practice_day3.py`：

1. 创建虚拟环境并安装 httpx、pydantic
2. 用 httpx 请求 https://httpbin.org/get 并打印所有响应头
3. 写一个函数 `download_json(url: str) -> dict`，带超时和错误处理
4. 模拟 LLM API 调用：封装一个 `ChatClient` 类，支持多轮对话（维护 messages 列表）

<details>
<summary>参考答案</summary>

```python
import httpx
from typing import List, Dict, Optional

def download_json(url: str, timeout: float = 10.0) -> dict:
    """下载JSON并解析"""
    try:
        response = httpx.get(url, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        print(f"请求超时: {url}")
        return {}
    except httpx.HTTPStatusError as e:
        print(f"HTTP错误 {e.response.status_code}: {url}")
        return {}

# 测试
data = download_json("https://httpbin.org/get")
print(data.get("headers", {}))

class ChatClient:
    """模拟LLM聊天客户端"""

    def __init__(self, api_key: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model
        self.messages: List[Dict[str, str]] = []

    def set_system(self, content: str):
        self.messages.insert(0, {"role": "system", "content": content})

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        # 实际调用API（这里用mock演示）
        # reply = call_llm(self.messages, self.model, self.api_key)
        reply = f"[Mock回复] 收到: {user_input}"
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def show_history(self):
        for msg in self.messages:
            print(f"[{msg['role']}] {msg['content']}")

# 测试
client = ChatClient(api_key="test-key")
client.set_system("你是一个Python编程助手")
client.chat("Python怎么读文件？")
client.chat("那异步读取呢？")
client.show_history()
```

</details>

---

## Day 4：async/await 异步编程

> Agent 开发大量使用异步：并发调用多个 LLM、流式输出、同时执行多个工具。这是本周最重要的内容。

### 4.1 与 JS async/await 对照

```python
# === JS 中的异步 ===
# async function fetchData() {
#     const res = await fetch(url);
#     const data = await res.json();
#     return data;
# }

# === Python 中的异步（几乎一样的语法） ===
import asyncio

async def fetch_data(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

### 4.2 核心概念

创建 `day4_async.py`：

```python
import asyncio
import httpx
import time

# === 1. 基础异步函数 ===
async def say_hello(name: str, delay: float):
    """异步函数用 async def 定义"""
    await asyncio.sleep(delay)  # 非阻塞等待（类似 JS 的 await sleep）
    print(f"Hello, {name}! (等待了{delay}秒)")

# 运行异步函数
# asyncio.run(say_hello("世界", 1))

# === 2. 并发执行（核心！） ===
async def concurrent_demo():
    """对比串行 vs 并发"""
    start = time.time()

    # 串行：总共等待 3 秒
    await asyncio.sleep(1)
    await asyncio.sleep(1)
    await asyncio.sleep(1)
    print(f"串行耗时: {time.time() - start:.1f}秒")  # ~3秒

    start = time.time()

    # 并发：总共等待 1 秒
    await asyncio.gather(
        asyncio.sleep(1),
        asyncio.sleep(1),
        asyncio.sleep(1),
    )
    print(f"并发耗时: {time.time() - start:.1f}秒")  # ~1秒

# asyncio.run(concurrent_demo())

# === 3. 并发请求多个 URL ===
async def fetch_urls(urls: list[str]):
    """并发请求多个URL"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for url, resp in zip(urls, responses):
            if isinstance(resp, Exception):
                print(f"失败: {url} - {resp}")
                results.append(None)
            else:
                results.append(resp.json())
        return results

# === 4. 实际场景：并发调用多个 LLM ===
async def call_llm_async(client: httpx.AsyncClient, prompt: str, model: str, api_key: str):
    """异步调用LLM"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }
    response = await client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

async def multi_prompt(api_key: str):
    """同一个问题问不同模型，取先回来的答案"""
    prompts = [
        "用一句话解释什么是Agent",
        "Agent和传统程序有什么区别",
        "列举3个Agent应用场景",
    ]
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [
            call_llm_async(client, prompt, "glm-4", api_key)
            for prompt in prompts
        ]
        results = await asyncio.gather(*tasks)
        for prompt, result in zip(prompts, results):
            print(f"Q: {prompt}\nA: {result}\n")

# === 5. 流式输出（SSE）—— Agent 对话的核心 ===
async def stream_chat(api_key: str, prompt: str):
    """流式接收LLM响应，像ChatGPT那样逐字输出"""
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "glm-4",
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,  # 开启流式
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            async for line in response.aiter_lines():
                if not line.strip():
                    continue  # 跳过空行
                if line.startswith("data: "):
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break  # 流式结束标志
                    # 解析 SSE 数据并输出
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            print(content, end="", flush=True)
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue  # 忽略无法解析的行
    print()  # 换行

# === 6. asyncio 常用工具 ===
async def async_tools_demo():
    # 超时控制
    try:
        await asyncio.wait_for(asyncio.sleep(5), timeout=2.0)
    except asyncio.TimeoutError:
        print("操作超时")

    # 等待任意一个完成
    done, pending = await asyncio.wait(
        [asyncio.sleep(1), asyncio.sleep(2), asyncio.sleep(3)],
        timeout=2.5,
        return_when=asyncio.FIRST_COMPLETED
    )
    print(f"完成了 {len(done)} 个任务")

    # 信号量（限制并发数）
    sem = asyncio.Semaphore(3)  # 最多3个并发

    async def limited_task(i):
        async with sem:
            await asyncio.sleep(1)
            print(f"任务{i}完成")

    await asyncio.gather(*[limited_task(i) for i in range(10)])

# === 主入口 ===
async def main():
    await concurrent_demo()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.3 今日练习

写一个 `practice_day4.py`：

1. 写一个异步函数 `fetch_with_retry(url, max_retries=3)`，失败自动重试，带指数退避（1s, 2s, 4s）
2. 用 `asyncio.gather` 并发请求 5 个 URL，打印每个请求的耗时
3. 用 `asyncio.Semaphore(2)` 限制同时最多 2 个并发请求
4. 模拟流式输出：写一个 `mock_stream()` 函数，每隔 0.1 秒产出一个词，模拟 LLM 流式响应

<details>
<summary>参考答案</summary>

```python
import asyncio
import httpx
import time

# 1. 带重试的异步请求
async def fetch_with_retry(url: str, max_retries: int = 3):
    async with httpx.AsyncClient(timeout=5.0) as client:
        for attempt in range(max_retries):
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                wait_time = 2 ** attempt  # 1, 2, 4
                print(f"第{attempt+1}次失败，{wait_time}秒后重试: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise

# 2+3. 限制并发的批量请求
async def fetch_limited(urls: list[str], concurrency: int = 2):
    sem = asyncio.Semaphore(concurrency)
    results = []

    async def fetch_one(url):
        async with sem:
            start = time.time()
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url)
                    elapsed = time.time() - start
                    print(f"完成: {url[:40]}... ({elapsed:.2f}s)")
                    return resp.status_code
            except Exception as e:
                print(f"失败: {url[:40]}... - {e}")
                return None

    return await asyncio.gather(*[fetch_one(url) for url in urls])

# 4. 模拟流式输出
async def mock_stream(text: str):
    """模拟LLM流式输出"""
    words = text.split()
    for word in words:
        await asyncio.sleep(0.1)
        yield word  # 注意：这是 async generator

async def demo_stream():
    async for word in mock_stream("你好 我 是 一个 AI 助手 很高兴 认识 你"):
        print(word, end=" ", flush=True)
    print()

# 运行
async def main():
    # 测试重试
    try:
        data = await fetch_with_retry("https://httpbin.org/get")
        print("重试成功:", type(data))
    except Exception as e:
        print("全部重试失败:", e)

    # 测试并发限制
    urls = [f"https://httpbin.org/delay/{i}" for i in range(1, 4)]
    await fetch_limited(urls, concurrency=2)

    # 测试流式
    await demo_stream()

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

---

## Day 5：文件读写 + JSON 处理

> Agent 开发中大量涉及配置文件、日志、文档处理

### 5.1 文件操作

创建 `day5_file_io.py`：

```python
import json
import os
from pathlib import Path
from typing import Any

# === 1. Path 对象（推荐，比 os.path 更好用） ===
# 对比 JS：path.join() → Path / 语法

base_dir = Path("~/agent-learning/week1").expanduser()
data_dir = base_dir / "data"  # 路径拼接
data_dir.mkdir(parents=True, exist_ok=True)  # 创建目录

file_path = data_dir / "config.json"
print(file_path.exists())   # 是否存在
print(file_path.suffix)     # ".json"
print(file_path.stem)       # "config"
print(file_path.parent)     # 目录路径

# === 2. 读写文本文件 ===
# 写文件
file_path.write_text("Hello, Agent!", encoding="utf-8")

# 读文件
content = file_path.read_text(encoding="utf-8")
print(content)

# 更安全的方式（自动关闭）
with open(file_path, "w", encoding="utf-8") as f:
    f.write("Hello again!")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 逐行读取
lines_path = data_dir / "tools.txt"
lines_path.write_text("search\ncalculator\ncode_runner\n", encoding="utf-8")

with open(lines_path, "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())  # strip() 去掉换行符

# === 3. JSON 读写（Agent 开发最频繁的操作） ===
agent_config = {
    "name": "CodeHelper",
    "model": "gpt-4",
    "temperature": 0.7,
    "tools": [
        {"name": "search", "description": "搜索文档"},
        {"name": "calculator", "description": "数学计算"}
    ]
}

# 写 JSON
config_path = data_dir / "agent_config.json"
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(agent_config, f, ensure_ascii=False, indent=2)
# ensure_ascii=False 让中文正常显示

# 读 JSON
with open(config_path, "r", encoding="utf-8") as f:
    loaded_config = json.load(f)
print(loaded_config["tools"][0]["name"])  # "search"

# JSON 字符串 ↔ Python 对象
json_str = json.dumps(agent_config, ensure_ascii=False, indent=2)
parsed = json.loads(json_str)

# === 4. 日志记录（生产环境必备） ===
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # 控制台
        logging.FileHandler(data_dir / "agent.log", encoding="utf-8")  # 文件
    ]
)

logger = logging.getLogger("agent")
logger.info("Agent 启动")
logger.warning("温度值偏高: 0.9")
logger.error("API调用失败: 401")

# === 5. 异步文件操作（处理大文件时用） ===
import aiofiles  # pip install aiofiles

async def async_write_json(path: Path, data: Any):
    """异步写入JSON"""
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))

async def async_read_json(path: Path) -> Any:
    """异步读取JSON"""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)
```

### 5.2 今日练习

1. 写一个 `ConfigManager` 类，支持：
   - 从 JSON 文件加载配置
   - 保存配置到 JSON 文件
   - 合并默认配置和用户配置
   - 用 Pydantic 做配置验证

<details>
<summary>参考答案</summary>

```python
import json
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    name: str = "default_agent"
    model: str = "glm-4"
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    tools: list[str] = Field(default_factory=list)

class ConfigManager:
    DEFAULT_CONFIG = AgentConfig()

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)
        self.config: AgentConfig = self.DEFAULT_CONFIG.model_copy()

    def load(self) -> AgentConfig:
        if not self.config_path.exists():
            return self.config
        with open(self.config_path, "r", encoding="utf-8") as f:
            user_data = json.load(f)
        # 合并：用户配置覆盖默认值
        merged = {**self.DEFAULT_CONFIG.model_dump(), **user_data}
        self.config = AgentConfig(**merged)
        return self.config

    def save(self, config: Optional[AgentConfig] = None):
        target = config or self.config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(target.model_dump(), f, ensure_ascii=False, indent=2)

    def update(self, **kwargs) -> AgentConfig:
        current = self.config.model_dump()
        current.update(kwargs)
        self.config = AgentConfig(**current)
        return self.config

# 测试
mgr = ConfigManager("~/agent-learning/week1/data/my_config.json")
config = mgr.load()
print(config)

mgr.update(temperature=0.5, tools=["search", "calculator"])
mgr.save()
print("配置已保存")
```

</details>

---

## Day 6：综合实战 —— 构建一个简单的 LLM 命令行工具

> 把本周学的所有内容串起来，做一个能用的东西

### 项目目标

```
$ python chat_cli.py --model glm-4 --temperature 0.7
> 你好
[助手] 你好！有什么可以帮你的？

> 帮我写一个Python函数计算斐波那契数列
[助手] 好的，这是一个计算斐波那契数列的函数：
       def fibonacci(n):
           ...

> /save
对话已保存到 chat_history.json

> /quit
再见！
```

### 实现步骤

创建 `chat_cli.py`：

```python
"""
简单的 LLM 命令行聊天工具
功能：
1. 多轮对话
2. 支持命令：/save（保存历史）、/clear（清空历史）、/config（查看配置）、/quit
3. 流式输出
4. 配置文件管理
"""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

# === 1. 数据模型 ===

class ChatConfig(BaseModel):
    api_key: str = Field(default="", description="API密钥")
    model: str = Field(default="glm-4")
    base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, gt=0)
    system_prompt: str = Field(default="你是一个有帮助的AI助手。")

# === 2. LLM 客户端 ===

class LLMClient:
    def __init__(self, config: ChatConfig):
        self.config = config
        self.messages: list[dict] = []

    def set_system(self, content: str):
        self.messages = [
            msg for msg in self.messages if msg["role"] != "system"
        ]
        self.messages.insert(0, {"role": "system", "content": content})

    async def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        url = f"{self.config.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        payload = {
            "model": self.config.model,
            "messages": self.messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "stream": True,
        }

        full_response = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue  # 跳过空行
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break  # 流式结束标志
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                full_response += content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue  # 忽略无法解析的行

        print()  # 换行
        self.messages.append({"role": "assistant", "content": full_response})
        return full_response

    def save_history(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "messages": self.messages
            }, f, ensure_ascii=False, indent=2)

# === 3. Mock模式（没有API Key时使用） ===

async def mock_chat(user_input: str) -> str:
    """本地模拟回复，不需要API"""
    await asyncio.sleep(0.5)  # 模拟网络延迟
    responses = {
        "你好": "你好！我是AI助手，很高兴和你聊天。",
        "帮助": "我可以帮你：\n1. 回答问题\n2. 写代码\n3. 分析文本\n请问需要什么帮助？",
    }
    for key, value in responses.items():
        if key in user_input:
            return value
    return f"[Mock回复] 收到你的消息: {user_input}"

# === 4. 命令行交互 ===

async def main():
    # 加载配置
    config_path = Path("~/agent-learning/week1/data/chat_config.json").expanduser()
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = ChatConfig(**json.load(f))
    else:
        config = ChatConfig()

    client = LLMClient(config)
    if config.system_prompt:
        client.set_system(config.system_prompt)

    print(f"ChatCLI v1.0 | 模型: {config.model} | 输入 /help 查看命令")

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        # 命令处理
        if user_input == "/quit":
            print("再见！")
            break
        elif user_input == "/help":
            print("命令列表：")
            print("  /save   - 保存对话历史")
            print("  /clear  - 清空对话历史")
            print("  /config - 查看当前配置")
            print("  /help   - 显示帮助")
            print("  /quit   - 退出")
            continue
        elif user_input == "/clear":
            client.messages = []
            if config.system_prompt:
                client.set_system(config.system_prompt)
            print("对话已清空")
            continue
        elif user_input == "/config":
            print(config.model_dump_json(indent=2))
            continue
        elif user_input == "/save":
            history_path = Path("~/agent-learning/week1/data/chat_history.json").expanduser()
            client.save_history(history_path)
            print(f"对话已保存到 {history_path}")
            continue

        # 聊天
        try:
            if config.api_key:
                await client.chat(user_input)
            else:
                print("[Mock模式] ", end="")
                reply = await mock_chat(user_input)
                print(reply)
                client.messages.append({"role": "assistant", "content": reply})
        except httpx.HTTPStatusError as e:
            print(f"\nAPI错误: {e.response.status_code}")
        except Exception as e:
            print(f"\n错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Day 6 练习

给 `chat_cli.py` 添加以下功能：

1. `/model <name>` 命令 —— 切换模型
2. `/system <prompt>` 命令 —— 修改系统提示词
3. 退出时自动保存对话历史
4. 加载上次的对话历史

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

对照以下清单，每项能做到就打勾：

```
Python 基础：
[ ] 能熟练使用 list、dict、f-string
[ ] 能写列表推导式
[ ] 能定义带默认参数和关键字参数的函数
[ ] 能用 try/except 处理异常

类型提示：
[ ] 能给函数标注参数和返回值类型
[ ] 能使用 Optional、Union、Literal
[ ] 能用 Pydantic 定义数据模型并做校验
[ ] 理解 Pydantic 在 Agent 开发中的作用

包管理：
[ ] 能创建和激活虚拟环境
[ ] 能用 pip 安装/管理依赖
[ ] 能生成和使用 requirements.txt

HTTP 请求：
[ ] 能用 httpx 发送 GET/POST 请求
[ ] 能处理请求超时和错误
[ ] 能调用 REST API 并解析 JSON 响应

异步编程：
[ ] 理解 async/await 语法
[ ] 能用 asyncio.gather 并发执行任务
[ ] 能用 asyncio.Semaphore 限制并发数
[ ] 理解流式输出(SSE)的原理

文件处理：
[ ] 能用 Path 对象操作路径
[ ] 能读写 JSON 文件
[ ] 能使用 logging 记录日志
```

### 7.2 综合练习题

写一个 `week1_final.py`，实现一个 **异步批量 URL 检测工具**：

要求：

1. 从 JSON 文件读取 URL 列表
2. 并发请求所有 URL（最多 5 个并发）
3. 记录每个 URL 的状态码、响应时间
4. 失败的自动重试 1 次
5. 结果保存为 JSON 文件
6. 用 Pydantic 定义输入输出数据模型
7. 用 logging 记录过程

<details>
<summary>参考答案</summary>

```python
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

import httpx
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("url_checker")

# 数据模型
class URLItem(BaseModel):
    url: str
    name: Optional[str] = None

class CheckInput(BaseModel):
    urls: list[URLItem]
    timeout: float = Field(default=10.0, gt=0)
    max_concurrency: int = Field(default=5, ge=1, le=20)
    retry: int = Field(default=1, ge=0, le=3)

class URLResult(BaseModel):
    url: str
    name: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    success: bool = False
    error: Optional[str] = None

class CheckOutput(BaseModel):
    total: int
    success_count: int
    fail_count: int
    results: list[URLResult]

# 核心逻辑
async def check_one(client: httpx.AsyncClient, item: URLItem, timeout: float, retry: int) -> URLResult:
    for attempt in range(retry + 1):
        try:
            start = time.time()
            resp = await client.get(item.url, timeout=timeout, follow_redirects=True)
            elapsed = time.time() - start
            logger.info(f"✓ {item.name or item.url[:40]} → {resp.status_code} ({elapsed:.2f}s)")
            return URLResult(
                url=item.url, name=item.name,
                status_code=resp.status_code,
                response_time=round(elapsed, 3),
                success=True
            )
        except Exception as e:
            if attempt < retry:
                logger.warning(f"重试 {item.name or item.url[:40]} ({attempt+1}/{retry})")
                await asyncio.sleep(1)
            else:
                logger.error(f"✗ {item.name or item.url[:40]} → {e}")
                return URLResult(
                    url=item.url, name=item.name,
                    error=str(e)
                )

async def check_urls(input_data: CheckInput) -> CheckOutput:
    sem = asyncio.Semaphore(input_data.max_concurrency)
    async with httpx.AsyncClient() as client:
        async def limited_check(item):
            async with sem:
                return await check_one(client, item, input_data.timeout, input_data.retry)

        results = await asyncio.gather(*[limited_check(item) for item in input_data.urls])

    success = sum(1 for r in results if r.success)
    return CheckOutput(
        total=len(results),
        success_count=success,
        fail_count=len(results) - success,
        results=results
    )

# 主程序
async def main():
    input_path = Path("~/agent-learning/week1/data/urls.json").expanduser()

    # 示例输入
    if not input_path.exists():
        sample = CheckInput(urls=[
            URLItem(url="https://httpbin.org/get", name="httpbin-get"),
            URLItem(url="https://httpbin.org/delay/1", name="httpbin-delay"),
            URLItem(url="https://httpbin.org/status/404", name="httpbin-404"),
            URLItem(url="https://httpbin.org/status/500", name="httpbin-500"),
            URLItem(url="https://nonexistent.invalid", name="bad-domain"),
        ])
        input_path.parent.mkdir(parents=True, exist_ok=True)
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(sample.model_dump(), f, ensure_ascii=False, indent=2)
        logger.info(f"已生成示例输入: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        input_data = CheckInput(**json.load(f))

    logger.info(f"开始检测 {len(input_data.urls)} 个URL...")
    output = await check_urls(input_data)

    output_path = input_path.parent / "check_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output.model_dump(), f, ensure_ascii=False, indent=2)

    logger.info(f"完成！成功 {output.success_count}/{output.total}，结果已保存到 {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

---

## 本周必装包清单

```bash
# 创建虚拟环境
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 安装依赖
pip install httpx pydantic aiofiles

# 导出
pip freeze > requirements.txt
```

## 本周推荐阅读

| 资源 | 说明 | 链接 |
|---|---|---|
| Python 官方教程 | 最权威 | docs.python.org/zh-cn/3/tutorial/ |
| Real Python | 高质量教程 | realpython.com |
| Pydantic 文档 | 必读 | docs.pydantic.dev |
| httpx 文档 | HTTP 客户端 | www.python-httpx.org |
| asyncio 文档 | 异步编程 | docs.python.org/zh-cn/3/library/asyncio.html |

## 常见问题

**Q: Python 2 还是 Python 3？**
A: 只用 Python 3（3.11+）。Python 2 已于 2020 年停止维护。

**Q: 用什么编辑器/IDE？**
A: VS Code + Python 插件，或 PyCharm Community（免费）。

**Q: 报错 `ModuleNotFoundError` 怎么办？**
A: 确认虚拟环境已激活，确认包已安装（`pip list` 查看）。

**Q: Windows 下 async 报错怎么办？**
A: Windows 的 asyncio 事件循环有特殊性，如果遇到 `Event loop is closed` 错误，在代码开头加：

```python
import sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```
