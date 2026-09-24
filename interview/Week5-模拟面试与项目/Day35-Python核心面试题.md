# Day 35 — Python 核心面试题(接口、数据库、并发)

> **学习目标**: 补齐 Agent 工程师面试中 Python 语言本身的高频考点。完成后你应该能讲清楚:GIL 为什么存在以及如何绕过、asyncio 事件循环怎么运转、FastAPI 为什么快、SQLAlchemy 的 N+1 问题怎么解、装饰器能手写出来。这是区分"会写 Python 脚本"和"懂 Python 工程化"的分水岭。
>
> **适用人群**: 转型 Agent 方向的工程师(尤其是移动端/前端背景,Python 作为第二语言),面试前快速补齐 Python 工程化知识。
>
> **今日时长**: 5-6 小时,10 道题逐道消化,Q3 装饰器、Q5 asyncio、Q7 FastAPI、Q8 SQLAlchemy 的代码务必亲手敲一遍。
>
> **核心心法**: Agent 工程师写 Python 不是写脚本,是写**线上服务**。面试官在问 Python 时实际在问四件事 —— ①你懂不懂 GIL 对并发的影响(线程模型选型); ②你会不会异步编程(LLM 调用是 IO 密集型); ③你能不能设计 API 接口(Agent 服务化); ④你了不了解数据库操作(会话/日志持久化)。

---

## 为什么 Agent 工程师必须精通 Python?

"我用 Python 就是调 LangChain API" —— 这个想法在面试中会被直接戳穿。四个原因:

1. **Agent 生态以 Python 为中心**:LangChain、LangGraph、LlamaIndex、AutoGen、CrewAI 全部是 Python 优先。不懂 Python 底层等于在生态里"半盲"。
2. **并发是 Agent 的命脉**:Agent 一次请求可能并发调用 3-5 个工具(LLM + 检索 + 数据库 + API),不懂 asyncio 就写不出高性能 Agent。
3. **服务化必须懂接口**:Agent 上线不是跑个脚本,是起一个 FastAPI 服务,暴露 SSE 流式接口。接口设计、数据验证、错误处理全是 Python 工程能力。
4. **持久化必须懂数据库**:Agent 的会话历史、用户画像、工具调用日志要存数据库。SQLAlchemy ORM 是 Python 生态标配,N+1 查询、连接池、事务管理不会就是裸奔。

---

## 今日知识图谱

```
Python 面试知识体系 (Agent 工程师必备)
│
├── 1. 语言基础 ★★★★★ (必问)
│   ├── GIL (全局解释器锁) ──── 为什么多线程不能利用多核 (Q1)
│   ├── 可变/不可变类型 ─────── int/str/tuple 不可变, list/dict/set 可变 (Q2)
│   ├── 深浅拷贝 ───────────── copy vs deepcopy, 嵌套对象陷阱 (Q2)
│   ├── 装饰器 ─────────────── 闭包原理 / 带参装饰器 / functools.wraps (Q3)
│   ├── 生成器/迭代器 ───────── yield / __iter__ / __next__ / 惰性求值 (Q4)
│   ├── 上下文管理器 ────────── with 语句 / __enter__/__exit__ / contextlib (Q9)
│   └── 作用域 ─────────────── LEGB 规则 / 闭包变量捕获 / nonlocal/global
│
├── 2. 并发编程 ★★★★★ (Agent 核心)
│   ├── 多线程 (threading) ──── GIL 限制 / 适合 IO 密集 (Q1)
│   ├── 多进程 (multiprocessing) ─ 绕过 GIL / 适合 CPU 密集 (Q1)
│   ├── 协程 (asyncio) ──────── 事件循环 / async/await / Task (Q5)
│   ├── 线程池/进程池 ───────── concurrent.futures / ThreadPoolExecutor (Q6)
│   ├── 异步生态 ────────────── aiohttp / httpx / asyncpg / aiomysql
│   └── 并发 vs 并行 ────────── 并发(交替执行) vs 并行(同时执行)
│
├── 3. Web 接口 ★★★★☆ (服务化)
│   ├── FastAPI ────────────── 异步 / Pydantic / 自动文档 / 依赖注入 (Q7)
│   ├── Flask ──────────────── 同步 / 轻量 / 路由 / Jinja2
│   ├── RESTful 设计 ────────── 资源/方法/状态码/版本管理
│   ├── SSE 流式输出 ────────── StreamingResponse / EventSource (Q7)
│   ├── 中间件 ──────────────── CORS / 认证 / 日志 / 限流
│   └── WebSocket ───────────── 双向通信 / Agent 交互
│
├── 4. 数据库 ★★★★☆ (持久化)
│   ├── SQLAlchemy ORM ─────── Session / Model / Query / Relationship (Q8)
│   ├── 连接池 ─────────────── pool_size / max_overflow / 超时回收 (Q8)
│   ├── N+1 查询问题 ────────── joinedload / selectinload / subqueryload (Q8)
│   ├── 异步数据库 ──────────── asyncpg / aiomysql / async SQLAlchemy
│   ├── 事务管理 ────────────── commit / rollback / savepoint / 嵌套事务
│   └── 数据库迁移 ──────────── Alembic / 自动生成迁移脚本
│
├── 5. 数据验证 ★★★☆☆
│   ├── Pydantic ───────────── BaseModel / Field / validator / JSON Schema (Q10)
│   ├── dataclass ──────────── @dataclass / field / 默认值陷阱
│   ├── 类型提示 ────────────── typing / Generic / Protocol / TypeVar
│   └── Pydantic vs dataclass ── 运行时验证 vs 纯类型标注
│
├── 6. 面向对象 ★★★☆☆
│   ├── MRO ────────────────── C3 线性化 / 多继承顺序
│   ├── 元类 (metaclass) ────── type / __init_subclass__ / 类工厂
│   ├── 抽象类 ──────────────── ABC / @abstractmethod / 接口约束
│   ├── 魔术方法 ────────────── __init__ / __new__ / __call__ / __repr__
│   └── 描述符 ──────────────── __get__ / __set__ / __delete__ / property
│
├── 7. 内存管理 ★★☆☆☆
│   ├── 引用计数 ────────────── 主回收机制 / 循环引用问题
│   ├── 垃圾回收 ────────────── 分代回收 (0/1/2 代) / gc 模块
│   ├── 内存泄漏 ────────────── 循环引用 / 全局变量 / 闭包捕获
│   └── __slots__ ──────────── 固定属性 / 节省内存
│
└── 8. 性能优化 ★★☆☆☆
    ├── cProfile ───────────── 函数级性能分析
    ├── line_profiler ──────── 逐行分析
    ├── 内存分析 ────────────── memory_profiler / tracemalloc
    ├── Cython ─────────────── 编译加速 / 类型声明
    └── PyPy ───────────────── JIT 编译 / 兼容性限制
```

---

## 面试题(共 10 道)

> **使用建议**:先看题目自己默答一遍(可以用费曼技巧讲出来),再展开 `<details>` 对照参考答案。能讲出来 ≠ 答得对。

### Q1 GIL 与 Python 并发模型:多线程 vs 多进程 vs 协程

**题目**:Python 的 GIL 是什么?为什么 Python 多线程不能利用多核 CPU?在 Agent 开发中,你如何选择多线程、多进程和协程?

<details>
<summary>展开参考答案</summary>

#### 1. GIL 是什么

**GIL(Global Interpreter Lock,全局解释器锁)** 是 CPython 解释器中的一把互斥锁,确保**同一时刻只有一个线程执行 Python 字节码**。

```
线程1 ─████████████░░░░░░░░░░██████████░░░░──
线程2 ─░░░░░░░░░░░░██████████░░░░░░░░░░████──  ← 交替执行,不能并行
       ↑ 持有GIL    ↑ 释放GIL(IO等待/超时)
```

**为什么有 GIL**:
- CPython 的内存管理(引用计数)不是线程安全的
- 如果没有 GIL,多个线程同时修改引用计数会导致内存泄漏或提前释放
- 简化 C 扩展开发,不需要自己处理线程安全

**GIL 的影响**:
- **CPU 密集型**:多线程**无法**利用多核,甚至比单线程更慢(线程切换开销)
- **IO 密集型**:多线程**有效**,因为 IO 等待时会释放 GIL(如 `socket.recv`、`time.sleep`、文件读写)

#### 2. 多线程 vs 多进程 vs 协程

| 维度 | 多线程 (threading) | 多进程 (multiprocessing) | 协程 (asyncio) |
|------|-------------------|------------------------|---------------|
| 并行 | 否(GIL 限制) | 是(独立进程) | 否(单线程) |
| 并发 | 是(IO 时释放 GIL) | 是 | 是(协作式调度) |
| 适合 | IO 密集型 | CPU 密集型 | IO 密集型(高并发) |
| 切换成本 | 中(内核态) | 高(进程创建/切换) | 低(用户态) |
| 内存 | 共享(需加锁) | 独立(需 IPC) | 共享(单线程无需锁) |
| 并发量 | 几十~几百 | 几十(进程数有限) | 几千~几万 |
| 编程复杂度 | 中(锁/竞态) | 高(IPC/序列化) | 中(async/await) |

#### 3. Agent 开发中的选择

```python
# 场景 1: 调用 LLM API (IO 密集) → asyncio
async def call_llm(prompt: str) -> str:
    response = await openai.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# 场景 2: 并行调用多个工具 (IO 密集) → asyncio.gather
async def run_tools(tools: list) -> list:
    results = await asyncio.gather(*[tool.run() for tool in tools])
    return results

# 场景 3: 向量检索 + Embedding 计算 (CPU 密集) → multiprocessing
from multiprocessing import Pool
with Pool(4) as p:
    embeddings = p.map(encode, texts)  # 4 个进程并行编码

# 场景 4: 简单后台任务 (IO 密集, 低并发) → threading
import threading
threading.Thread(target=save_log, args=(log_data,)).start()
```

**Agent 选型决策树**:

```
是 CPU 密集型?
├── 是 → multiprocessing(绕过 GIL) 或 C 扩展/NumPy(释放 GIL)
└── 否 (IO 密集型)
    ├── 并发量 > 1000? → asyncio
    ├── 并发量 10-1000? → asyncio(推荐) 或 threading
    └── 并发量 < 10? → threading(简单)
```

#### 4. 如何绕过 GIL

1. **multiprocessing**:每个进程有独立 GIL
2. **C 扩展**:NumPy/Cython 在计算时手动释放 GIL(`Py_BEGIN_ALLOW_THREADS`)
3. **Jython/PyPy**:Jython 无 GIL(JVM 线程),PyPy 有 GIL 但 JIT 优化好
4. **Python 3.13+ Free-threading**:PEP 703 提议的可选无 GIL 模式(实验阶段)

</details>

---

### Q2 可变/不可变类型与深浅拷贝

**题目**:Python 中哪些类型是可变的,哪些不可变?深拷贝和浅拷贝的区别是什么?以下代码输出什么?

```python
a = [[1, 2], [3, 4]]
b = copy.copy(a)
c = copy.deepcopy(a)
a[0][0] = 99
# b[0][0] = ?  c[0][0] = ?
```

<details>
<summary>展开参考答案</summary>

#### 1. 可变 vs 不可变

| 不可变 (Immutable) | 可变 (Mutable) |
|-------------------|---------------|
| int, float, bool | list |
| str | dict |
| tuple | set |
| frozenset | bytearray |
| bytes | 自定义类(默认) |

**关键区别**:
- 不可变类型:修改值会创建**新对象**,旧对象不变
- 可变类型:修改值在**原对象**上操作,地址不变

```python
# 不可变:int 修改 -> 新对象
a = 1
b = a
a += 1  # a=2 (新对象), b=1 (旧对象不变)

# 可变:list 修改 -> 原对象
x = [1, 2]
y = x
x.append(3)  # x=[1,2,3], y=[1,2,3] (同一个对象)
```

#### 2. 函数参数传递——"传对象的引用"

Python 既不是值传递也不是引用传递,而是**传对象的引用(pass by object reference)**:

```python
def modify_list(lst):
    lst.append(4)       # 修改原对象(可变)
    lst = [10, 20]      # 重新赋值,只影响局部变量

my_list = [1, 2, 3]
modify_list(my_list)
print(my_list)  # [1, 2, 3, 4] —— append 生效,重新赋值不影响外部
```

**陷阱:默认参数使用可变对象**:

```python
# 经典陷阱!
def add_item(item, lst=[]):  # 默认值在函数定义时只创建一次
    lst.append(item)
    return lst

print(add_item(1))  # [1]
print(add_item(2))  # [1, 2] —— 不是 [2]!因为共享同一个默认 list

# 正确做法
def add_item(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

#### 3. 深浅拷贝

```python
import copy

a = [[1, 2], [3, 4]]

# 浅拷贝:创建新外层对象,内层对象仍共享引用
b = copy.copy(a)
# 等价于: b = a.copy()  或  b = list(a)  或  b = a[:]

# 深拷贝:递归创建所有层级的新对象
c = copy.deepcopy(a)

a[0][0] = 99
# b[0][0] = 99  ← 内层共享,受影响
# c[0][0] = 1   ← 完全独立,不受影响
```

**内存图解**:

```
浅拷贝 (copy):
  a ─→ [[1,2], [3,4]]    ← 外层新对象
              ↑    ↑
  b ─→ [list, list]      ← 内层共享同一个 list 对象

深拷贝 (deepcopy):
  a ─→ [[1,2], [3,4]]    ← 原对象
  c ─→ [[1,2], [3,4]]    ← 完全新的对象,递归复制
```

#### 4. Agent 中的常见陷阱

```python
# 陷阱 1: 字典浅拷贝
config = {"model": "gpt-4", "params": {"temperature": 0.7}}
config_copy = config.copy()  # 浅拷贝
config_copy["params"]["temperature"] = 0.9
print(config["params"]["temperature"])  # 0.9! 被篡改了

# 正确:深拷贝
config_copy = copy.deepcopy(config)

# 陷阱 2: 类属性共享
class Agent:
    history = []  # 类属性,所有实例共享!

a1 = Agent()
a2 = Agent()
a1.history.append("msg")
print(a2.history)  # ["msg"]! 不符合预期

# 正确:实例属性
class Agent:
    def __init__(self):
        self.history = []  # 每个实例独立
```

</details>

---

### Q3 装饰器原理与手写

**题目**:Python 装饰器的本质是什么?请手写一个带参数的装饰器,用于记录 Agent 工具调用的执行时间和参数。

<details>
<summary>展开参考答案</summary>

#### 1. 装饰器本质

装饰器是一个**函数**,接收一个函数作为参数,返回一个新函数。本质是**高阶函数 + 语法糖**。

```python
# @decorator 语法糖等价于:
@decorator
def func(): ...
# func = decorator(func)  ← 这就是装饰器的本质
```

#### 2. 闭包——装饰器的基础

闭包 = 函数 + 该函数定义时的环境(外层变量):

```python
def make_counter():
    count = 0           # 外层变量
    def inner():
        nonlocal count  # 捕获外层变量
        count += 1
        return count
    return inner        # 返回闭包

counter = make_counter()
print(counter())  # 1
print(counter())  # 2  ← count 在闭包中保持状态
```

**LEGB 作用域规则**:Local → Enclosing → Global → Built-in

#### 3. 手写带参数的装饰器

```python
import functools
import time
import logging

logger = logging.getLogger(__name__)

def log_tool_call(tool_name: str, log_level: str = "INFO"):
    """
    带参数的装饰器:记录 Agent 工具调用的执行时间、参数和返回值。

    用法:
        @log_tool_call("search", "DEBUG")
        def search(query: str) -> list:
            ...
    """
    def decorator(func):
        @functools.wraps(func)  # 保留原函数的 __name__, __doc__ 等
        def wrapper(*args, **kwargs):
            # 记录调用前信息
            start_time = time.perf_counter()
            logger.log(
                getattr(logging, log_level),
                f"[Tool: {tool_name}] 调用开始, args={args}, kwargs={kwargs}"
            )

            try:
                # 执行原函数
                result = func(*args, **kwargs)
                # 记录成功
                elapsed = time.perf_counter() - start_time
                logger.log(
                    getattr(logging, log_level),
                    f"[Tool: {tool_name}] 调用成功, 耗时={elapsed:.3f}s, result={result}"
                )
                return result
            except Exception as e:
                # 记录异常
                elapsed = time.perf_counter() - start_time
                logger.error(
                    f"[Tool: {tool_name}] 调用失败, 耗时={elapsed:.3f}s, error={e}"
                )
                raise  # 重新抛出异常,不吞掉

        return wrapper
    return decorator


# 使用示例
@log_tool_call("web_search", "DEBUG")
def web_search(query: str, max_results: int = 5) -> list:
    """模拟网页搜索工具"""
    time.sleep(0.5)  # 模拟网络延迟
    return [f"result_{i}_{query}" for i in range(max_results)]

# 调用
results = web_search("Agent framework", max_results=3)
# 日志输出:
# [Tool: web_search] 调用开始, args=('Agent framework',), kwargs={'max_results': 3}
# [Tool: web_search] 调用成功, 耗时=0.501s, result=['result_0_Agent framework', ...]
```

#### 4. functools.wraps 的作用

不加 `@functools.wraps(func)` 会有什么问题:

```python
# 不加 wraps
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def my_func():
    """这是我的函数"""
    pass

print(my_func.__name__)  # 'wrapper'  ← 名字丢了!
print(my_func.__doc__)   # None       ← 文档丢了!

# 加了 wraps
@functools.wraps(func)  # 复制 __name__, __doc__, __module__, __wrapped__
# print(my_func.__name__)  # 'my_func'  ← 正确
```

#### 5. 类装饰器(面试加分)

```python
class CallCounter:
    """类装饰器:统计函数被调用的次数"""
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"[{self.func.__name__}] 第 {self.count} 次调用")
        return self.func(*args, **kwargs)

@CallCounter
def llm_call(prompt: str) -> str:
    return f"response to {prompt}"

llm_call("hello")  # [llm_call] 第 1 次调用
llm_call("world")  # [llm_call] 第 2 次调用
print(llm_call.count)  # 2
```

#### 6. Agent 中的装饰器应用

```python
# LangChain 中的 @tool 装饰器(简化版原理)
def tool(func=None, name=None, description=None):
    """将普通函数注册为 Agent 工具"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        wrapper.tool_name = name or f.__name__
        wrapper.tool_description = description or f.__doc__
        wrapper.tool_schema = extract_schema(f)  # 从类型提示提取参数 Schema
        return wrapper
    if func:
        return decorator(func)
    return decorator

@tool(name="search", description="搜索网页内容")
def search(query: str, max_results: int = 5) -> list:
    """搜索网页内容"""
    ...
```

</details>

---

### Q4 生成器与迭代器

**题目**:Python 的迭代器和生成器有什么区别?yield 的工作原理是什么?在 Agent 开发中,生成器有哪些典型应用场景?

<details>
<summary>展开参考答案</summary>

#### 1. 迭代器(Iterator)

迭代器是实现了 `__iter__()` 和 `__next__()` 的对象:

```python
class Counter:
    """自定义迭代器"""
    def __init__(self, start, end):
        self.current = start
        self.end = end

    def __iter__(self):
        return self  # 迭代器返回自身

    def __next__(self):
        if self.current >= self.end:
            raise StopIteration  # 迭代结束
        value = self.current
        self.current += 1
        return value

# 使用
for num in Counter(1, 5):
    print(num)  # 1, 2, 3, 4
```

**可迭代(Iterable)vs 迭代器(Iterator)**:
- 可迭代:实现了 `__iter__()`(如 list、dict、str)
- 迭代器:额外实现了 `__next__()`,且 `__iter__()` 返回自身
- `iter(iterable)` → 返回一个迭代器
- `next(iterator)` → 返回下一个值,结束时 raise StopIteration

#### 2. 生成器(Generator)

生成器是**创建迭代器的简便方式**,用 `yield` 关键字:

```python
def counter(start, end):
    """生成器函数:用 yield 代替 return"""
    current = start
    while current < end:
        yield current  # 暂停并返回值
        current += 1   # 下次调用从此处继续

for num in counter(1, 5):
    print(num)  # 1, 2, 3, 4
```

**yield 工作原理**:
1. 调用生成器函数不执行函数体,而是返回一个**生成器对象**
2. 每次调用 `next()` 时,函数执行到 `yield` 处**暂停**,返回 yield 后的值
3. 再次调用 `next()` 时,从上次暂停处**恢复执行**
4. 函数结束(或 return)时 raise StopIteration

```python
gen = counter(1, 3)
print(next(gen))  # 1  (执行到 yield 1, 暂停)
print(next(gen))  # 2  (从 current += 1 恢复, 执行到 yield 2, 暂停)
print(next(gen))  # StopIteration  (current=2, while 条件不满足, 函数结束)
```

#### 3. 生成器 vs 迭代器

| 维度 | 迭代器(类) | 生成器(函数) |
|------|------------|-------------|
| 实现方式 | 类 + `__iter__` + `__next__` | 函数 + `yield` |
| 代码量 | 多 | 少(自动实现协议) |
| 状态管理 | 手动维护实例属性 | 自动(局部变量保持) |
| 灵活性 | 高(可自定义复杂逻辑) | 中(线性执行) |

#### 4. 生成器表达式

```python
# 列表推导:一次性生成所有元素,占内存
squares_list = [x**2 for x in range(1000000)]  # ~8MB 内存

# 生成器表达式:惰性求值,几乎不占内存
squares_gen = (x**2 for x in range(1000000))  # ~120 bytes
```

#### 5. Agent 中的典型应用

**场景 1:流式输出 LLM 响应(最重要)**

```python
def stream_llm_response(prompt: str):
    """流式输出 LLM 响应,逐 token yield"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=True  # 开启流式
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content  # 逐 token yield

# FastAPI 中用 StreamingResponse 消费这个生成器
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.get("/chat")
def chat(prompt: str):
    return StreamingResponse(
        stream_llm_response(prompt),
        media_type="text/event-stream"  # SSE
    )
```

**场景 2:大数据分块处理**

```python
def read_large_file(file_path, chunk_size=1000):
    """分块读取大文件,避免一次性加载到内存"""
    with open(file_path, 'r') as f:
        while True:
            lines = [f.readline() for _ in range(chunk_size)]
            if not any(lines):
                break
            yield lines

# 处理 10GB 文件,内存占用仅 1000 行
for chunk in read_large_file("huge_dataset.jsonl"):
    process(chunk)  # 逐块处理
```

**场景 3:ReAct Agent 的循环生成**

```python
def react_agent_loop(query: str, max_steps: int = 10):
    """ReAct Agent 循环:每一步 yield 中间状态"""
    thought = ""
    for step in range(max_steps):
        # Thought
        thought = llm_generate(f"问题: {query}\n已有信息: {thought}\n下一步思考:")
        yield {"step": step, "type": "thought", "content": thought}

        # Action
        action = parse_action(thought)
        if action["type"] == "finish":
            yield {"step": step, "type": "answer", "content": action["answer"]}
            return  # 结束

        # Observation
        observation = execute_tool(action)
        yield {"step": step, "type": "observation", "content": observation}
        thought += f"\nObservation: {observation}"

# 调用方可以逐步展示 Agent 的思考过程
for event in react_agent_loop("什么是 RAG?"):
    display(event)  # 实时展示每一步
```

**场景 4:管道/数据处理链**

```python
def tokenize(texts):
    for text in texts:
        yield text.lower().split()

def remove_stopwords(token_streams, stopwords):
    for tokens in token_streams:
        yield [t for t in tokens if t not in stopwords]

def vectorize(token_streams, model):
    for tokens in token_streams:
        yield model.encode(" ".join(tokens))

# 构建 pipeline(惰性,不占额外内存)
texts = read_large_file("corpus.txt")
tokens = tokenize(texts)
filtered = remove_stopwords(tokens, {"the", "a", "an"})
vectors = vectorize(filtered, embedding_model)

for vec in vectors:  # 一步触发整条链
    save_to_db(vec)
```

#### 6. yield from — 委托生成器

```python
def sub_generator():
    yield 1
    yield 2
    yield 3

def main_generator():
    yield "start"
    yield from sub_generator()  # 委托给子生成器
    yield "end"

list(main_generator())  # ['start', 1, 2, 3, 'end']
```

#### 7. send() — 向生成器发送值

```python
def echo_generator():
    while True:
        received = yield  # 接收外部 send 的值
        print(f"收到: {received}")

gen = echo_generator()
next(gen)        # 启动生成器(必须先 next 一次)
gen.send("hello")  # 收到: hello
gen.send("world")  # 收到: world
```

</details>

---

### Q5 asyncio 异步编程

**题目**:asyncio 的事件循环是怎么工作的?async/await 的执行流程是什么?请用 asyncio 实现一个并发限制器,限制同时调用 LLM API 的并发数为 5。

<details>
<summary>展开参考答案</summary>

#### 1. 事件循环(Event Loop)

事件循环是 asyncio 的核心,本质是一个**单线程的任务调度器**:

```
事件循环 (单线程)
┌──────────────────────────────────────┐
│  1. 取出就绪的 Task                    │
│  2. 执行 Task 到 await 处(暂停)       │
│  3. 注册 IO 回调                       │
│  4. 跳到下一个就绪 Task                │
│  5. IO 完成后唤醒 Task 继续            │
│  6. 循环 1-5                          │
└──────────────────────────────────────┘
```

**关键**:asyncio 是**单线程并发**(不是并行),通过**协作式调度**在多个协程间切换。当一个协程 await(IO 等待)时,事件循环切换到另一个协程执行。

#### 2. async/await 执行流程

```python
import asyncio

async def fetch_data(url: str) -> str:
    print(f"开始请求 {url}")
    await asyncio.sleep(1)  # 模拟 IO 等待(非阻塞)
    print(f"完成请求 {url}")
    return f"data from {url}"

async def main():
    # 并发执行 3 个协程
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3"),
    )
    print(results)

asyncio.run(main())

# 输出(总耗时 ~1s,不是 3s):
# 开始请求 url1
# 开始请求 url2
# 开始请求 url3
# (1 秒后)
# 完成请求 url1
# 完成请求 url2
# 完成请求 url3
# ['data from url1', 'data from url2', 'data from url3']
```

**执行流程详解**:
1. `asyncio.run(main())` 启动事件循环,创建 main Task
2. `asyncio.gather()` 创建 3 个子 Task,提交给事件循环
3. 每个 Task 执行到 `await asyncio.sleep(1)` 时**挂起**,控制权还给事件循环
4. 事件循环切换到下一个 Task(三个 Task 都挂起在 sleep)
5. 1 秒后,sleep 完成,3 个 Task 依次被唤醒
6. gather 收集所有结果,返回给 main

#### 3. 核心概念

| 概念 | 说明 |
|------|------|
| Coroutine | `async def` 定义的函数,调用后返回协程对象(不执行) |
| Task | 对协程的包装,由事件循环调度执行 |
| Future | 低层级异步结果的占位对象 |
| `await` | 挂起当前协程,等待 awaitable 完成 |
| `asyncio.gather` | 并发执行多个协程,等全部完成 |
| `asyncio.create_task` | 将协程包装为 Task 并调度 |
| `asyncio.wait_for` | 为协程设置超时 |
| `asyncio.Queue` | 异步队列,协程间通信 |

```python
# 协程对象 vs Task
async def my_coro():
    await asyncio.sleep(1)
    return "done"

# 直接 await(串行,等当前 Task 调度)
result = await my_coro()

# create_task(并发,立即调度)
task = asyncio.create_task(my_coro())
# 做其他事情...
result = await task  # 等 task 完成
```

#### 4. 手写并发限制器

```python
import asyncio
from typing import Any, Coroutine

class AsyncSemaphore:
    """
    异步并发限制器:限制同时执行的协程数量。
    用于限制 LLM API 并发调用,避免触发 rate limit。
    """

    def __init__(self, max_concurrent: int):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def run(self, coro: Coroutine) -> Any:
        """限制并发地执行一个协程"""
        async with self._semaphore:
            return await coro

    async def gather_with_limit(
        self, coroutines: list[Coroutine], max_concurrent: int = 5
    ) -> list[Any]:
        """
        并发执行多个协程,但限制同时运行的数量为 max_concurrent。

        用法:
            limiter = AsyncSemaphore(5)
            results = await limiter.gather_with_limit(
                [call_llm(prompt) for prompt in prompts],
                max_concurrent=5
            )
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _run_with_limit(coro: Coroutine) -> Any:
            async with semaphore:
                return await coro

        return await asyncio.gather(
            *[_run_with_limit(coro) for coro in coroutines]
        )


# 更简洁的版本(无需类)
async def gather_with_limit(
    coroutines: list[Coroutine],
    max_concurrent: int = 5
) -> list[Any]:
    """并发执行协程列表,限制最大并发数"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _limited(coro: Coroutine) -> Any:
        async with semaphore:
            return await coro

    return await asyncio.gather(*[_limited(coro) for coro in coroutines])


# 实际应用:批量调用 LLM API
async def call_llm(prompt: str) -> str:
    """模拟 LLM API 调用"""
    await asyncio.sleep(0.5)  # 模拟网络延迟
    return f"回答: {prompt[:20]}..."

async def batch_llm_calls(prompts: list[str]) -> list[str]:
    """批量调用 LLM,限制并发为 5(避免 rate limit)"""
    results = await gather_with_limit(
        [call_llm(p) for p in prompts],
        max_concurrent=5
    )
    return results

# 测试
async def main():
    prompts = [f"问题{i}" for i in range(20)]  # 20 个问题
    results = await batch_llm_calls(prompts)
    # 总耗时 ~2s (20 / 5 = 4 批, 每批 0.5s)
    # 如果不限制并发:~0.5s (但可能触发 rate limit)
    print(f"完成 {len(results)} 个调用")

asyncio.run(main())
```

#### 5. asyncio 常见陷阱

**陷阱 1:在 async 函数中调用同步阻塞代码**

```python
# 错误! time.sleep 会阻塞整个事件循环
async def bad_example():
    time.sleep(5)  # 其他所有协程都会被阻塞 5 秒!

# 正确:用 asyncio.sleep
async def good_example():
    await asyncio.sleep(5)  # 非阻塞,其他协程可以执行
```

**陷阱 2:忘记 await**

```python
# 错误! 忘记 await,协程不会执行
async def forgot_await():
    result = async_function()  # 返回协程对象,不执行!
    return result  # RuntimeWarning: coroutine was never awaited

# 正确
async def correct():
    result = await async_function()
    return result
```

**陷阱 3:在同步代码中运行 async 函数**

```python
# 错误! 不能在同步函数中直接 await
def sync_func():
    result = await async_func()  # SyntaxError: 'await' outside async function

# 方案 1: asyncio.run()
def sync_func():
    result = asyncio.run(async_func())

# 方案 2: 在已有事件循环中用 asyncio.create_task()
async def async_wrapper():
    task = asyncio.create_task(async_func())
    result = await task
```

**陷阱 4:混合使用 threading 和 asyncio**

```python
# 在线程中运行 async 函数需要新建事件循环
import threading

def run_in_thread():
    # 每个线程需要自己的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(async_func())
    finally:
        loop.close()
```

#### 6. Agent 中的实际应用

```python
import asyncio
import httpx

class Agent:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30)
        self.semaphore = asyncio.Semaphore(5)  # 限制并发

    async def call_llm(self, messages: list) -> str:
        async with self.semaphore:  # 限制 LLM 并发
            response = await self.client.post(
                "https://api.openai.com/v1/chat/completions",
                json={"model": "gpt-4", "messages": messages}
            )
            return response.json()["choices"][0]["message"]["content"]

    async def call_tool(self, tool_name: str, args: dict) -> str:
        """并发调用多个工具"""
        async with self.semaphore:
            # 模拟工具调用
            await asyncio.sleep(0.5)
            return f"{tool_name} result"

    async def run(self, query: str) -> str:
        """Agent 主循环"""
        # 并发检索 + LLM 规划
        retrieval_task = asyncio.create_task(self.call_tool("search", {"q": query}))
        plan_task = asyncio.create_task(
            self.call_llm([{"role": "user", "content": f"规划: {query}"}])
        )

        # 等待两个任务完成
        retrieval_result, plan = await asyncio.gather(retrieval_task, plan_task)

        # 用检索结果 + 规划生成最终答案
        answer = await self.call_llm([
            {"role": "user", "content": query},
            {"role": "assistant", "content": plan},
            {"role": "system", "content": f"参考信息: {retrieval_result}"},
        ])
        return answer

# 使用
async def main():
    agent = Agent()
    answer = await agent.run("什么是 Agentic RAG?")
    print(answer)

asyncio.run(main())
```

</details>

---

### Q6 线程池与 concurrent.futures

**题目**:Python 的 `concurrent.futures` 模块怎么用?ThreadPoolExecutor 和 ProcessPoolExecutor 的区别?如何用线程池并行处理 Agent 的多个工具调用?

<details>
<summary>展开参考答案</summary>

#### 1. concurrent.futures 概述

`concurrent.futures` 是 Python 3.2+ 引入的高层并发 API,提供线程池和进程池的统一接口:

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# 线程池:适合 IO 密集型
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(io_task, arg) for arg in args]
    for future in as_completed(futures):
        result = future.result()

# 进程池:适合 CPU 密集型
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(cpu_task, args))
```

#### 2. ThreadPoolExecutor vs ProcessPoolExecutor

| 维度 | ThreadPoolExecutor | ProcessPoolExecutor |
|------|-------------------|-------------------|
| 并行 | 受 GIL 限制(不能多核并行) | 真并行(独立进程) |
| 适合 | IO 密集型 | CPU 密集型 |
| 内存 | 低(共享进程内存) | 高(每个进程独立内存) |
| 数据传递 | 直接引用(需加锁) | 序列化(pickle,需可序列化) |
| 启动成本 | 低 | 高(创建进程) |
| max_workers | 通常 5-50 | 通常 = CPU 核心数 |

#### 3. 核心 API

```python
# submit:提交单个任务,返回 Future
future = executor.submit(func, arg1, arg2)
result = future.result()       # 阻塞等待结果
future.done()                   # 是否完成
future.exception()              # 获取异常(无异常返回 None)

# map:批量提交,按顺序返回结果
results = executor.map(func, iterable)  # 按提交顺序返回

# as_completed:批量提交,按完成顺序返回
futures = [executor.submit(func, arg) for arg in args]
for future in as_completed(futures):  # 谁先完成谁先返回
    result = future.result()
```

#### 4. Agent 工具并行调用

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable

class ToolExecutor:
    """Agent 工具执行器:支持并行调用多个工具"""

    def __init__(self, max_workers: int = 5):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.tools: dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """注册工具"""
        self.tools[name] = func

    def run_parallel(self, tool_calls: list[dict]) -> dict[str, Any]:
        """
        并行执行多个工具调用。

        tool_calls 格式:
            [
                {"name": "search", "args": {"query": "RAG"}},
                {"name": "calculator", "args": {"expr": "2+3"}},
            ]

        返回:
            {"search": "...", "calculator": 5}
        """
        futures = {}
        for call in tool_calls:
            name = call["name"]
            args = call.get("args", {})
            func = self.tools[name]
            future = self.executor.submit(func, **args)
            futures[future] = name  # 映射 future → 工具名

        results = {}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                results[name] = f"Error: {e}"

        return results


# 使用示例
def web_search(query: str) -> str:
    import time
    time.sleep(1)  # 模拟网络延迟
    return f"搜索结果: {query}"

def calculator(expr: str) -> float:
    return eval(expr)  # 简化示例(生产环境不可用 eval)

def weather_api(city: str) -> str:
    import time
    time.sleep(0.5)
    return f"{city}: 晴天 25°C"

executor = ToolExecutor(max_workers=5)
executor.register("search", web_search)
executor.register("calculator", calculator)
executor.register("weather", weather_api)

# Agent 并行调用 3 个工具(总耗时 ~1s,不是 2.5s)
results = executor.run_parallel([
    {"name": "search", "args": {"query": "Agent"}},
    {"name": "calculator", "args": {"expr": "123 * 456"}},
    {"name": "weather", "args": {"city": "深圳"}},
])
print(results)
# {'search': '搜索结果: Agent', 'calculator': 56088, 'weather': '深圳: 晴天 25°C'}
```

#### 5. 回调函数

```python
from concurrent.futures import ThreadPoolExecutor

def on_complete(future):
    """任务完成回调"""
    try:
        result = future.result()
        print(f"任务完成: {result}")
    except Exception as e:
        print(f"任务失败: {e}")

with ThreadPoolExecutor(max_workers=3) as executor:
    future = executor.submit(long_running_task, "arg")
    future.add_done_callback(on_complete)  # 注册回调
    # 主线程可以继续做其他事情
    print("任务已提交,主线程继续执行...")
```

#### 6. 何时用线程池 vs asyncio

| 场景 | 推荐 |
|------|------|
| 调用 LLM API(httpx/aiohttp 异步库) | asyncio |
| 调用同步 SDK(requests/openai 同步模式) | ThreadPoolExecutor |
| CPU 密集计算(Embedding/向量计算) | ProcessPoolExecutor |
| 混合同步/异步代码 | ThreadPoolExecutor(包装异步调用) |

```python
# 在 asyncio 中使用同步代码 → run_in_executor
import asyncio
import requests

async def async_fetch(url: str) -> str:
    """在 asyncio 中调用同步的 requests 库"""
    loop = asyncio.get_event_loop()
    # 用线程池运行同步函数,不阻塞事件循环
    response = await loop.run_in_executor(
        None,  # 使用默认线程池
        lambda: requests.get(url)
    )
    return response.text
```

</details>

---

### Q7 FastAPI 接口设计与 SSE 流式输出

**题目**:FastAPI 的核心特性有哪些?如何用 FastAPI 实现 Agent 的 SSE 流式接口?请设计一个 Agent 问答 API,支持流式输出和会话管理。

<details>
<summary>展开参考答案</summary>

#### 1. FastAPI 核心特性

| 特性 | 说明 |
|------|------|
| 异步原生 | 基于 Starlette + asyncio,原生 async/await |
| 类型提示 | 用 Python 类型提示自动做参数验证和序列化 |
| Pydantic | 请求/响应模型用 Pydantic,自动 JSON Schema |
| 自动文档 | Swagger UI (`/docs`) + ReDoc (`/redoc`) 零配置 |
| 依赖注入 | `Depends()` 管理数据库连接、认证等共享逻辑 |
| 中间件 | CORS、认证、日志、限流等插件化 |

#### 2. 基础接口

```python
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional
import uuid

app = FastAPI(title="Agent API", version="1.0.0")

# ---- 数据模型 (Pydantic) ----
class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    session_id: Optional[str] = Field(None, description="会话 ID,首次对话不传")
    temperature: float = Field(0.7, ge=0, le=2, description="采样温度")

class ChatResponse(BaseModel):
    answer: str
    session_id: str
    tool_calls: list[dict] = []
    usage: dict

# ---- 接口 ----
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """非流式问答接口"""
    session_id = request.session_id or str(uuid.uuid4())
    # 调用 Agent
    answer = await run_agent(request.query, session_id, request.temperature)
    return ChatResponse(
        answer=answer,
        session_id=session_id,
        tool_calls=[],
        usage={"tokens": 150}
    )
```

#### 3. SSE 流式输出

```python
from fastapi.responses import StreamingResponse
import asyncio
import json

async def stream_agent_response(query: str, session_id: str):
    """
    SSE 流式生成器:逐 token yield Agent 响应。
    SSE 格式: data: {json}\n\n
    """
    # 1. 发送 session_id
    yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

    # 2. 流式输出 Agent 思考过程
    async for step in agent_think_stream(query, session_id):
        if step["type"] == "thought":
            yield f"data: {json.dumps({'type': 'thought', 'content': step['content']})}\n\n"
        elif step["type"] == "tool_call":
            yield f"data: {json.dumps({'type': 'tool_call', 'name': step['name'], 'args': step['args']})}\n\n"
        elif step["type"] == "tool_result":
            yield f"data: {json.dumps({'type': 'tool_result', 'name': step['name'], 'result': step['result']})}\n\n"
        elif step["type"] == "token":
            yield f"data: {json.dumps({'type': 'token', 'content': step['content']})}\n\n"

    # 3. 发送结束标记
    yield f"data: {json.dumps({'type': 'done', 'usage': {'tokens': 150}})}\n\n"


async def agent_think_stream(query: str, session_id: str):
    """模拟 Agent 流式思考"""
    # 模拟思考
    yield {"type": "thought", "content": "我需要搜索相关信息..."}

    # 模拟工具调用
    yield {"type": "tool_call", "name": "search", "args": {"query": query}}
    await asyncio.sleep(0.3)
    yield {"type": "tool_result", "name": "search", "result": "搜索到 3 条结果"}

    # 模拟流式 token 生成
    answer = "根据搜索结果,Agent 是一个能自主决策并调用工具的 AI 系统。"
    for char in answer:
        yield {"type": "token", "content": char}
        await asyncio.sleep(0.02)  # 模拟生成延迟


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE 流式问答接口"""
    session_id = request.session_id or str(uuid.uuid4())
    return StreamingResponse(
        stream_agent_response(request.query, session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 不缓冲
        }
    )
```

#### 4. 依赖注入(认证 + 数据库)

```python
from fastapi import Depends, Header, HTTPException

# ---- 认证依赖 ----
async def verify_token(authorization: str = Header(...)):
    """验证 Bearer Token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization[7:]
    # 验证 token 逻辑...
    if not validate(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"user_id": "user_123"}

# ---- 数据库依赖 ----
async def get_db():
    """获取数据库 Session(依赖注入)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ---- 使用依赖 ----
@app.get("/history/{session_id}")
async def get_history(
    session_id: str,
    user: dict = Depends(verify_token),
    db = Depends(get_db),
):
    """获取会话历史(需认证 + 数据库)"""
    history = await db.execute(
        "SELECT * FROM messages WHERE session_id = :sid AND user_id = :uid",
        {"sid": session_id, "uid": user["user_id"]}
    )
    return {"history": history.fetchall()}
```

#### 5. 中间件

```python
from fastapi.middleware.cors import CORSMiddleware
import time

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    print(f"{request.method} {request.url.path} → {response.status_code} ({elapsed:.3f}s)")
    return response

# 限流中间件(简化版)
from collections import defaultdict
rate_limit = defaultdict(list)  # {ip: [timestamps]}

@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    client_ip = request.client.host
    now = time.time()
    # 清理 1 分钟前的记录
    rate_limit[client_ip] = [t for t in rate_limit[client_ip] if now - t < 60]
    if len(rate_limit[client_ip]) >= 30:  # 每分钟 30 次
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    rate_limit[client_ip].append(now)
    return await call_next(request)
```

#### 6. 完整 Agent API 架构

```
客户端
  │
  ├── POST /chat           → 同步问答(非流式)
  ├── POST /chat/stream    → SSE 流式问答
  ├── GET  /history/{id}   → 获取会话历史
  ├── POST /feedback       → 用户反馈
  ├── GET  /health         → 健康检查
  └── GET  /docs           → Swagger 文档
  │
  ▼
FastAPI 应用
  ├── 中间件层: CORS / 日志 / 限流 / 认证
  ├── 路由层:   ChatRouter / HistoryRouter / FeedbackRouter
  ├── 依赖层:   verify_token / get_db / get_agent
  ├── 服务层:   AgentService / SessionService / FeedbackService
  └── 数据层:   PostgreSQL(会话) + Redis(缓存) + Milvus(向量)
```

</details>

---

### Q8 SQLAlchemy ORM 与数据库操作

**题目**:SQLAlchemy 的 Session 是什么?什么是 N+1 查询问题?如何用 SQLAlchemy 实现会话历史的 CRUD?连接池怎么配置?

<details>
<summary>展开参考答案</summary>

#### 1. SQLAlchemy 核心概念

```
SQLAlchemy 架构
├── Engine        → 连接工厂(管理连接池)
├── Session       → 工作单元(对象级别的 CRUD)
├── Model         → ORM 模型(Python 类 ↔ 数据库表)
├── Query         → 查询构建器
└── Transaction   → 事务管理(Session 级别)
```

#### 2. 模型定义

```python
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Session(Base):
    """会话表:一个用户的一个对话会话"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)       # UUID
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(200), default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系:一个 Session 有多条 Message
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

class Message(Base):
    """消息表:会话中的每条消息"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    tool_calls = Column(Text)  # JSON 格式的工具调用记录
    tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系:多对一
    session = relationship("Session", back_populates="messages")
```

#### 3. Engine 与连接池

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 同步引擎 + 连接池
engine = create_engine(
    "postgresql://user:password@localhost:5432/agent_db",
    poolclass=QueuePool,
    pool_size=10,          # 连接池大小(常驻连接数)
    max_overflow=20,       # 超出 pool_size 后允许的临时连接数
    pool_timeout=30,       # 获取连接超时(秒),超时抛异常
    pool_recycle=3600,     # 连接回收时间(秒),避免 MySQL 8 小时断连
    pool_pre_ping=True,    # 使用前 ping 一下,避免使用已断开的连接
    echo=False,            # True 时打印 SQL 日志(调试用)
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
```

**连接池参数解释**:

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| pool_size | 常驻连接数 | 5-20(取决于并发量) |
| max_overflow | 临时连接数 | pool_size 的 1-2 倍 |
| pool_timeout | 等待连接超时 | 30s |
| pool_recycle | 连接最大存活时间 | 3600s(比数据库 wait_timeout 短) |
| pool_pre_ping | 使用前检查连接 | True(生产环境必开) |

#### 4. CRUD 操作

```python
from sqlalchemy.orm import Session as DBSession
from typing import Optional
import uuid

# ---- Create ----
def create_session(db: DBSession, user_id: str, title: str = "新对话") -> Session:
    """创建新会话"""
    session = Session(id=str(uuid.uuid4()), user_id=user_id, title=title)
    db.add(session)
    db.commit()
    db.refresh(session)  # 刷新获取数据库生成的字段
    return session

def add_message(db: DBSession, session_id: str, role: str, content: str, tokens: int = 0) -> Message:
    """添加消息"""
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        tokens=tokens,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

# ---- Read ----
def get_session(db: DBSession, session_id: str) -> Optional[Session]:
    """获取会话(含消息)"""
    return db.query(Session).filter(Session.id == session_id).first()

def get_messages(db: DBSession, session_id: str, limit: int = 50) -> list[Message]:
    """获取会话消息(按时间排序)"""
    return (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )

def get_user_sessions(db: DBSession, user_id: str, page: int = 1, size: int = 20) -> list[Session]:
    """获取用户的会话列表(分页)"""
    offset = (page - 1) * size
    return (
        db.query(Session)
        .filter(Session.user_id == user_id)
        .order_by(Session.updated_at.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

# ---- Update ----
def update_session_title(db: DBSession, session_id: str, title: str):
    """更新会话标题"""
    db.query(Session).filter(Session.id == session_id).update({"title": title})
    db.commit()

# ---- Delete ----
def delete_session(db: DBSession, session_id: str):
    """删除会话(级联删除消息)"""
    session = db.query(Session).filter(Session.id == session_id).first()
    if session:
        db.delete(session)  # cascade="all, delete-orphan" 会自动删除关联消息
        db.commit()
```

#### 5. N+1 查询问题(面试重点)

```python
# ---- N+1 问题 ----
sessions = db.query(Session).all()  # 1 次查询:获取 10 个 session
for s in sessions:
    print(len(s.messages))  # 10 次查询:每个 session 懒加载 messages
# 总共:1 + 10 = 11 次 SQL 查询! 性能灾难

# ---- 解决方案 1:joinedload (JOIN) ----
from sqlalchemy.orm import joinedload
sessions = db.query(Session).options(
    joinedload(Session.messages)  # 一次 JOIN 查询
).all()
# 总共:1 次 SQL(LEFT JOIN)

# ---- 解决方案 2:selectinload (IN 查询, 推荐) ----
from sqlalchemy.orm import selectinload
sessions = db.query(Session).options(
    selectinload(Session.messages)  # 先查 sessions, 再用 IN 查 messages
).all()
# 总共:2 次 SQL(SELECT sessions + SELECT messages WHERE session_id IN (...))
# 优势:避免 JOIN 产生的笛卡尔积,适合一对多关系

# ---- 解决方案 3:subqueryload (子查询) ----
from sqlalchemy.orm import subqueryload
sessions = db.query(Session).options(
    subqueryload(Session.messages)
).all()
# 总共:2 次 SQL(子查询方式)
```

**三种加载策略对比**:

| 策略 | SQL 次数 | 方式 | 适合场景 |
|------|---------|------|---------|
| 懒加载(默认) | 1 + N | 访问关系时才查 | 不确定是否需要关联数据 |
| joinedload | 1 | LEFT JOIN | 一对一 / 多对一 |
| selectinload | 2 | IN 查询 | 一对多(推荐) |
| subqueryload | 2 | 子查询 | 一对多(复杂场景) |

#### 6. 异步 SQLAlchemy

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# 异步引擎
async_engine = create_async_engine(
    "postgresql+asyncpg://user:password@localhost:5432/agent_db",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 异步 CRUD
async def get_messages_async(db: AsyncSession, session_id: str) -> list[Message]:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    return result.scalars().all()

# FastAPI 中使用
@app.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_async_db),
):
    messages = await get_messages_async(db, session_id)
    return {"messages": [{"role": m.role, "content": m.content} for m in messages]}
```

#### 7. 事务管理

```python
# 方式 1:手动 commit/rollback
def transfer_credits(db: DBSession, from_id: str, to_id: str, amount: int):
    try:
        db.query(User).filter(User.id == from_id).update({"credits": User.credits - amount})
        db.query(User).filter(User.id == to_id).update({"credits": User.credits + amount})
        db.commit()
    except Exception:
        db.rollback()
        raise

# 方式 2:上下文管理器(推荐)
from contextlib import contextmanager

@contextmanager
def db_transaction(db: DBSession):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

# 使用
with db_transaction(db) as tx:
    tx.query(User).filter(User.id == "123").update({"credits": 100})

# 方式 3:嵌套事务(SAVEPOINT)
db.begin()  # 开启事务
try:
    db.query(User).filter(User.id == "123").update({"name": "Alice"})
    db.begin_nested()  # SAVEPOINT
    try:
        db.query(User).filter(User.id == "456").update({"name": "Bob"})
        # 可能失败的操作
        db.query(User).filter(User.id == "789").update({"name": "Charlie"})
    except Exception:
        db.rollback()  # 回滚到 SAVEPOINT,不影响外层
    db.commit()  # 提交外层
except Exception:
    db.rollback()
```

#### 8. 数据库迁移(Alembic)

```bash
# 初始化
alembic init alembic

# 自动生成迁移脚本(检测 Model 变化)
alembic revision --autogenerate -m "add messages table"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

</details>

---

### Q9 上下文管理器与魔术方法

**题目**:Python 的 `with` 语句原理是什么?`__enter__` 和 `__exit__` 怎么工作?请实现一个数据库连接的上下文管理器,并说明 `contextlib.contextmanager` 的用法。

<details>
<summary>展开参考答案</summary>

#### 1. with 语句原理

`with` 语句是上下文管理协议的语法糖,确保资源被正确释放(即使发生异常):

```python
# with 语句等价于:
with obj as var:
    body

# 等价于:
var = obj.__enter__()
try:
    body
finally:
    obj.__exit__(exc_type, exc_val, exc_tb)
```

#### 2. 实现上下文管理器(类方式)

```python
from sqlalchemy.orm import Session as DBSession
from contextlib import contextmanager

class DatabaseConnection:
    """数据库连接上下文管理器"""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: DBSession = None

    def __enter__(self) -> DBSession:
        """进入 with 块时调用,返回值赋给 as 后的变量"""
        self.session = self.session_factory()
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """离开 with 块时调用(无论是否异常)"""
        if self.session:
            if exc_type is None:
                # 无异常,提交事务
                self.session.commit()
            else:
                # 有异常,回滚事务
                self.session.rollback()
            self.session.close()
        # 返回 False(或不返回)→ 异常继续传播
        # 返回 True → 异常被吞掉(不推荐)
        return False

# 使用
with DatabaseConnection(SessionLocal) as db:
    user = db.query(User).first()
    user.credits += 100
    # 离开 with 块自动 commit;如果异常自动 rollback
```

#### 3. contextlib.contextmanager(函数方式,更简洁)

```python
from contextlib import contextmanager
from sqlalchemy.orm import Session as DBSession

@contextmanager
def db_session(session_factory):
    """用装饰器实现上下文管理器(推荐,更简洁)"""
    session = session_factory()
    try:
        yield session  # yield 之前 = __enter__, yield 之后 = __exit__
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# 使用
with db_session(SessionLocal) as db:
    user = db.query(User).first()
    user.credits += 100
```

**原理**:
- `@contextmanager` 将生成器函数转为上下文管理器
- `yield` 之前的代码 = `__enter__`
- `yield` 的值 = `as` 变量接收的值
- `yield` 之后的代码 = `__exit__`(无论是否异常都会执行)
- 如果 `with` 块内抛异常,异常会在 `yield` 处被重新抛出

#### 4. Agent 中的应用

```python
@contextmanager
def agent_context(agent, query: str):
    """Agent 执行上下文:记录开始/结束时间、token 用量"""
    import time
    start = time.perf_counter()
    agent.start_token_count = agent.get_token_count()

    print(f"[Agent] 开始处理: {query}")
    try:
        yield agent
    except Exception as e:
        print(f"[Agent] 执行失败: {e}")
        raise
    finally:
        elapsed = time.perf_counter() - start
        tokens_used = agent.get_token_count() - agent.start_token_count
        print(f"[Agent] 完成, 耗时={elapsed:.2f}s, tokens={tokens_used}")

# 使用
with agent_context(agent, "什么是 RAG?") as a:
    result = a.run("什么是 RAG?")
    print(result)
# [Agent] 开始处理: 什么是 RAG?
# (Agent 执行中...)
# [Agent] 完成, 耗时=2.34s, tokens=512
```

#### 5. 常见魔术方法

| 方法 | 触发场景 | 用途 |
|------|---------|------|
| `__init__` | 对象创建后 | 初始化 |
| `__new__` | 对象创建前 | 控制创建过程(单例模式) |
| `__del__` | 对象被 GC 回收时 | 资源清理(不推荐用,时间不确定) |
| `__enter__` / `__exit__` | `with` 语句 | 资源管理 |
| `__call__` | `obj()` 调用 | 使实例可调用 |
| `__str__` / `__repr__` | `print()` / `repr()` | 字符串表示 |
| `__len__` / `__getitem__` / `__setitem__` | `len()` / `obj[k]` | 容器协议 |
| `__iter__` / `__next__` | `for` 循环 | 迭代器协议 |
| `__eq__` / `__hash__` | `==` / `hash()` | 比较/哈希 |
| `__getattr__` / `__setattr__` | 属性访问 | 动态属性/代理 |
| `__contains__` | `in` 操作 | 成员判断 |

```python
class Agent:
    """演示常见魔术方法"""

    def __init__(self, name: str, model: str = "gpt-4"):
        self.name = name
        self.model = model
        self.history: list = []

    def __call__(self, query: str) -> str:
        """使 Agent 实例可直接调用: agent("问题")"""
        response = self._call_llm(query)
        self.history.append({"query": query, "response": response})
        return response

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r}, model={self.model!r})"

    def __len__(self) -> int:
        return len(self.history)

    def __getitem__(self, index: int) -> dict:
        return self.history[index]

    def __enter__(self):
        print(f"Agent {self.name} 启动")
        return self

    def __exit__(self, *args):
        print(f"Agent {self.name} 关闭,共 {len(self.history)} 轮对话")

    def _call_llm(self, query: str) -> str:
        return f"回答: {query}"

# 使用
with Agent("助手") as agent:
    print(agent("你好"))       # __call__
    print(agent("什么是RAG"))   # __call__
    print(len(agent))          # __len__ → 2
    print(agent[0])            # __getitem__ → {"query": "你好", ...}
    print(repr(agent))         # __repr__ → Agent(name='助手', model='gpt-4')
```

#### 6. __new__ 与单例模式

```python
class Singleton:
    """单例模式:全局唯一实例"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# 使用
a = Singleton()
b = Singleton()
print(a is b)  # True ← 同一个实例

# Agent 应用:全局只有一个 Agent 实例
class AgentSingleton:
    _instance = None

    def __new__(cls, model="gpt-4"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = model
            cls._instance.history = []
        return cls._instance
```

</details>

---

### Q10 Pydantic 数据验证与类型提示

**题目**:Pydantic 的 BaseModel 是怎么工作的?它和 Python 的 dataclass 有什么区别?在 LangChain/LangGraph 中,Pydantic 扮演什么角色?

<details>
<summary>展开参考答案</summary>

#### 1. Pydantic 基础

Pydantic 用 Python 类型提示做**运行时数据验证**,广泛用于 FastAPI、LangChain、LangGraph:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class ChatMessage(BaseModel):
    """Agent 消息模型(自动验证)"""
    role: str = Field(..., description="消息角色: user/assistant/system")
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: Optional[datetime] = None
    tokens: int = Field(0, ge=0)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "assistant", "system", "tool"):
            raise ValueError(f"Invalid role: {v}")
        return v

# 自动验证
msg = ChatMessage(role="user", content="你好", tokens=50)
print(msg.model_dump())  # 转字典
# {"role": "user", "content": "你好", "timestamp": None, "tokens": 50}

# 验证失败
ChatMessage(role="invalid", content="test")
# ValidationError: Invalid role: invalid

# 类型自动转换
msg = ChatMessage(role="user", content="test", tokens="100")  # str → int 自动转换
print(msg.tokens)  # 100 (int)
```

#### 2. Pydantic vs dataclass

| 维度 | Pydantic BaseModel | dataclass |
|------|-------------------|-----------|
| 运行时验证 | 有(自动类型检查) | 无(纯类型标注) |
| 类型转换 | 有(str→int 等) | 无 |
| JSON 序列化 | `model_dump_json()` | 需手动实现 |
| JSON 反序列化 | `model_validate_json()` | 需手动实现 |
| Schema 导出 | `model_json_schema()` | 无 |
| 性能 | 中(有验证开销) | 高(无验证) |
| 依赖 | 需安装 pydantic | 标准库 |
| 适合 | API/外部数据 | 内部数据结构 |

```python
from dataclasses import dataclass, field

# dataclass:无验证,纯数据容器
@dataclass
class ChatMessageDC:
    role: str
    content: str
    tokens: int = 0

# dataclass 不会验证类型
msg = ChatMessageDC(role="invalid_role", content="", tokens=-10)
# 不报错!dataclass 不做验证

# Pydantic:有验证
class ChatMessagePD(BaseModel):
    role: str
    content: str = Field(..., min_length=1)
    tokens: int = Field(0, ge=0)

# Pydantic 会验证
ChatMessagePD(role="invalid", content="", tokens=-10)
# ValidationError!
```

#### 3. Pydantic 在 LangChain/LangGraph 中的角色

**场景 1:Agent 状态定义(LangGraph)**

```python
from pydantic import BaseModel, Field
from typing import Annotated
from langgraph.graph import StateGraph
import operator

class AgentState(BaseModel):
    """LangGraph Agent 状态(用 Pydantic 定义)"""
    messages: Annotated[list[dict], operator.add] = Field(default_factory=list)
    current_step: str = "start"
    retrieved_docs: list[str] = Field(default_factory=list)
    tool_calls: list[dict] = Field(default_factory=list)
    final_answer: Optional[str] = None
    iteration: int = Field(0, ge=0)

# LangGraph 使用这个 State 在节点间传递数据
graph = StateGraph(AgentState)
```

**场景 2:工具参数 Schema(Function Calling)**

```python
from pydantic import BaseModel, Field
from langchain.tools import tool

class SearchInput(BaseModel):
    """搜索工具的参数 Schema(自动生成 JSON Schema 给 LLM)"""
    query: str = Field(..., description="搜索关键词")
    max_results: int = Field(5, ge=1, le=20, description="最大返回结果数")
    language: str = Field("zh", description="搜索语言: zh/en")

@tool(args_schema=SearchInput)
def search(query: str, max_results: int = 5, language: str = "zh") -> list:
    """搜索网页内容"""
    # Pydantic Schema 自动转为 Function Calling 的 JSON Schema
    return [{"title": f"结果{i}", "url": f"https://example.com/{i}"}]

# LLM 看到的 JSON Schema:
# {
#   "name": "search",
#   "description": "搜索网页内容",
#   "parameters": {
#     "type": "object",
#     "properties": {
#       "query": {"type": "string", "description": "搜索关键词"},
#       "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20},
#       "language": {"type": "string", "default": "zh"}
#     },
#     "required": ["query"]
#   }
# }
```

**场景 3:LLM 输出结构化解析**

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

class AgentPlan(BaseModel):
    """Agent 规划的结构化输出"""
    thought: str = Field(..., description="思考过程")
    action: str = Field(..., description="下一步动作: search/calculate/finish")
    action_input: str = Field(..., description="动作参数")
    confidence: float = Field(..., ge=0, le=1, description="置信度")

parser = PydanticOutputParser(pydantic_object=AgentPlan)

# LLM 输出 → Pydantic 对象(自动验证)
llm = ChatOpenAI(model="gpt-4")
response = llm.invoke("分析问题: 2+3=? 生成 ReAct 格式计划")
plan = parser.parse(response.content)
# plan.thought, plan.action, plan.action_input, plan.confidence
# 如果 LLM 输出格式不对 → ValidationError
```

#### 4. Pydantic v2 高级特性

```python
from pydantic import BaseModel, Field, model_validator, field_validator

class AgentConfig(BaseModel):
    """Agent 配置(高级验证)"""
    model: str = "gpt-4"
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2000, ge=1)
    tools: list[str] = Field(default_factory=list)
    api_key: str = Field(..., min_length=10)

    # 字段级验证
    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        allowed = {"gpt-4", "gpt-4o", "gpt-3.5-turbo", "claude-3", "qwen-72b"}
        if v not in allowed:
            raise ValueError(f"Unsupported model: {v}. Allowed: {allowed}")
        return v

    # 模型级验证(多字段联合)
    @model_validator(mode="after")
    def validate_config(self):
        if self.model == "gpt-4" and self.max_tokens > 4096:
            raise ValueError("gpt-4 max_tokens 不能超过 4096")
        return self

    # 计算字段
    @property
    def is_gpt(self) -> bool:
        return self.model.startswith("gpt")

# 嵌套模型
class MultiAgentConfig(BaseModel):
    name: str
    agents: list[AgentConfig]  # 嵌套 Pydantic 模型
    max_concurrent: int = Field(5, ge=1, le=20)

config = MultiAgentConfig(
    name="research-team",
    agents=[
        AgentConfig(model="gpt-4", api_key="sk-xxxxxxxxxx"),
        AgentConfig(model="claude-3", api_key="sk-yyyyyyyyyy"),
    ]
)
print(config.model_dump_json(indent=2))  # JSON 序列化
```

#### 5. Python 类型提示(typing)

```python
from typing import Optional, Union, List, Dict, Any, Callable, TypeVar, Generic, Protocol

# 基本类型提示
def process(query: str, max_results: int = 5) -> list[str]:
    ...

# Optional (可能为 None)
def get_user(user_id: str) -> Optional[dict]:
    ...  # 返回 dict 或 None

# Union (多种类型)
def parse(value: Union[str, int, float]) -> Any:
    ...

# Python 3.10+ 更简洁的写法
def parse(value: str | int | float) -> Any:  # 等价于 Union
    ...

# Callable (函数类型)
def run_tool(tool: Callable[[str], str], input: str) -> str:
    return tool(input)

# TypeVar + Generic (泛型)
T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self):
        self._items: list[T] = []
    def push(self, item: T) -> None:
        self._items.append(item)
    def pop(self) -> T:
        return self._items.pop()

# Protocol (结构化子类型 / 鸭子类型的类型安全版)
class Tool(Protocol):
    def run(self, query: str) -> str: ...

def execute(tool: Tool) -> str:
    return tool.run("test")  # 任何有 run(str) -> str 方法的对象都行
```

</details>

---

## 手撕代码(3 道)

### 手撕 1:带参数的装饰器(计时 + 日志)

```python
import functools
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timed(name: str = "function", log_result: bool = False):
    """
    带参数的装饰器:记录函数执行时间和可选的结果。

    用法:
        @timed("llm_call", log_result=True)
        def call_llm(prompt): ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                msg = f"[{name}] {func.__name__} 完成, 耗时={elapsed:.3f}s"
                if log_result:
                    msg += f", result={result}"
                logger.info(msg)
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(f"[{name}] {func.__name__} 失败, 耗时={elapsed:.3f}s, error={e}")
                raise
        return wrapper
    return decorator

# 测试
@timed("search", log_result=True)
def search(query: str) -> list:
    time.sleep(0.3)
    return [f"result_{query}"]

search("Agent")
# INFO: [search] search 完成, 耗时=0.301s, result=['result_Agent']
```

### 手撕 2:异步并发限制器

```python
import asyncio
from typing import Coroutine, Any, Callable

class AsyncRateLimiter:
    """
    异步并发限制器 + 速率限制。
    - max_concurrent: 最大并发数
    - rate_per_minute: 每分钟最大调用次数
    """

    def __init__(self, max_concurrent: int = 5, rate_per_minute: int = 60):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rate = rate_per_minute
        self._timestamps: list[float] = []

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """限速 + 限并发地执行异步函数"""
        async with self._semaphore:
            # 速率控制
            now = asyncio.get_event_loop().time()
            self._timestamps = [t for t in self._timestamps if now - t < 60]
            if len(self._timestamps) >= self._rate:
                wait_time = 60 - (now - self._timestamps[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            self._timestamps.append(asyncio.get_event_loop().time())

            return await func(*args, **kwargs)

    async def batch(
        self, func: Callable, items: list, *args, **kwargs
    ) -> list[Any]:
        """批量执行"""
        tasks = [self.call(func, item, *args, **kwargs) for item in items]
        return await asyncio.gather(*tasks)

# 测试
async def llm_call(prompt: str) -> str:
    await asyncio.sleep(0.2)
    return f"回答: {prompt[:10]}"

async def main():
    limiter = AsyncRateLimiter(max_concurrent=3, rate_per_minute=100)
    prompts = [f"问题{i}" for i in range(10)]
    results = await limiter.batch(llm_call, prompts)
    print(f"完成 {len(results)} 个调用")

asyncio.run(main())
```

### 手撕 3:SQLAlchemy 会话管理 + CRUD

```python
from sqlalchemy import Column, String, Text, Integer, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from contextlib import contextmanager
from typing import Optional
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    title = Column(String(200), default="新对话")
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 引擎 + 连接池
engine = create_engine(
    "sqlite:///agent.db",
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

# 上下文管理器
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# CRUD
def create_conversation(db: Session, user_id: str, title: str = "新对话") -> Conversation:
    conv = Conversation(id=str(uuid.uuid4()), user_id=user_id, title=title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def add_message(db: Session, conv_id: str, role: str, content: str) -> Message:
    msg = Message(conversation_id=conv_id, role=role, content=content)
    db.add(msg)
    db.query(Conversation).filter(Conversation.id == conv_id).update(
        {"message_count": Conversation.message_count + 1}
    )
    db.commit()
    db.refresh(msg)
    return msg

def get_conversation_messages(db: Session, conv_id: str) -> list[Message]:
    return db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at).all()

# 使用
with get_db() as db:
    conv = create_conversation(db, "user_123", "RAG 讨论")
    add_message(db, conv.id, "user", "什么是 RAG?")
    add_message(db, conv.id, "assistant", "RAG 是检索增强生成...")
    msgs = get_conversation_messages(db, conv.id)
    print(f"会话 {conv.id}: {len(msgs)} 条消息")
```

---

## 综合题(5 道)

### C1 设计:Agent 服务的 Python 后端架构

**题目**:用 Python 设计一个 Agent 问答服务的后端架构,要求支持流式输出、会话管理、工具调用、高并发。

**参考要点**:

```
                    客户端 (Web/App)
                         │
                    ┌────▼────┐
                    │  Nginx  │  ← 负载均衡 + SSE 代理
                    └────┬────┘
                         │
              ┌──────────▼──────────┐
              │   FastAPI (async)   │  ← uvicorn + gunicorn
              │  ├── /chat (SSE)    │
              │  ├── /chat (sync)   │
              │  ├── /history       │
              │  └── /feedback      │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
     │ Agent   │   │  Session  │  │  Tool   │
     │ Engine  │   │  Service  │  │ Service │
     │(asyncio)│   │           │  │         │
     └────┬────┘   └─────┬─────┘  └────┬────┘
          │              │              │
     ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
     │  LLM    │   │PostgreSQL │  │  Redis  │
     │  API    │   │ (会话/消息)│  │ (缓存)  │
     └─────────┘   └───────────┘  └─────────┘
```

**技术选型**:
- Web 框架:FastAPI(异步 + Pydantic + 自动文档)
- ASGI 服务器:uvicorn + gunicorn(多 worker)
- 数据库:PostgreSQL + SQLAlchemy ORM(异步 asyncpg)
- 缓存:Redis(会话缓存 + 语义缓存)
- 并发:asyncio(SSE 流式) + ThreadPoolExecutor(同步 SDK)
- 消息队列:Celery + Redis(长任务异步执行)

### C2 Python 陷阱题

```python
# 以下代码输出什么?
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])
# 答案: [2, 2, 2]
# 原因: lambda 捕获的是变量 i 的引用,不是值
# 循环结束时 i=2,所以所有 lambda 返回 2

# 修复
funcs = [lambda i=i: i for i in range(3)]  # 默认参数捕获当前值
print([f() for f in funcs])  # [0, 1, 2]
```

### C3 GIL 对 Agent 性能的影响

**题目**:你的 Agent 需要同时做 3 件事:(1)调用 LLM API(2)本地 Embedding 计算(3)向量检索。如何设计并发方案?

**参考**:
- (1) LLM API → asyncio(纯 IO,不涉及 GIL)
- (2) Embedding 计算 → ProcessPoolExecutor(CPU 密集,绕过 GIL)或用 NumPy(释放 GIL)
- (3) 向量检索 → asyncio(如果用 Milvus 远程)或 ThreadPool(如果用本地 FAISS)
- 三者并行:asyncio.gather + run_in_executor 混合

### C4 数据库设计:Agent 会话管理

**题目**:设计 Agent 会话管理的数据库表结构,要求支持多用户、多会话、消息历史、工具调用记录。

**参考表结构**:
- `users`:用户表(id, name, email, created_at)
- `sessions`:会话表(id, user_id, title, model, created_at, updated_at)
- `messages`:消息表(id, session_id, role, content, tokens, created_at)
- `tool_calls`:工具调用表(id, message_id, tool_name, args, result, latency_ms)
- `feedbacks`:用户反馈表(id, message_id, rating, comment)

### C5 FastAPI + SSE 完整流程

**题目**:描述从客户端发起 SSE 请求到 Agent 流式返回的完整流程。

**参考**:
1. 客户端 POST `/chat/stream`,携带 query 和 session_id
2. FastAPI 接收请求,Pydantic 验证参数
3. 认证中间件验证 token
4. 创建 StreamingResponse,media_type="text/event-stream"
5. Agent 开始执行:检索 → 规划 → 工具调用 → 生成
6. 每步通过 `yield f"data: {json}\n\n"` 推送到客户端
7. 客户端 EventSource 实时接收并渲染
8. Agent 完成后发送 `{"type": "done"}`,关闭流

---

## 易错点提醒(10 个)

1. **"多线程能加速 CPU 计算"** —— 错,GIL 导致同一时刻只有一个线程执行字节码。CPU 密集用多进程。

2. **"asyncio 是多线程"** —— 错,asyncio 是**单线程协作式并发**。所有协程在同一个线程中通过事件循环调度。

3. **"浅拷贝会复制所有内容"** —— 错,浅拷贝只复制外层容器,内层对象共享引用。嵌套结构修改内层会影响原对象。

4. **"默认参数 [] 每次调用都创建新列表"** —— 错,默认参数在函数定义时只创建一次,后续调用共享。用 `None` 做默认值。

5. **"lambda 闭包捕获的是值"** —— 错,捕获的是变量引用。循环中的 lambda 会共享最后一个值。用默认参数 `lambda i=i: i` 捕获当前值。

6. **"在 async 函数中可以用 time.sleep()"** —— 错,`time.sleep()` 阻塞整个事件循环。用 `await asyncio.sleep()`。

7. **"SQLAlchemy Session 是线程安全的"** —— 错,Session 不是线程安全的。每个线程/请求应该有自己的 Session(用 `sessionmaker` + 依赖注入)。

8. **"N+1 问题是 SQL 写错了"** —— 错,N+1 是 ORM 懒加载导致的:查 N 条记录后,访问关系字段时每条触发一次查询。用 `selectinload` / `joinedload` 解决。

9. **"Pydantic 和 dataclass 一样"** —— 错,Pydantic 有运行时验证和类型转换,dataclass 只是类型标注不做验证。API 边界用 Pydantic,内部数据用 dataclass。

10. **"with 语句就是 try-finally 的语法糖"** —— 不完全对。with 是上下文管理协议(`__enter__`/`__exit__`),还支持异常处理(`__exit__` 返回 True 可吞掉异常)和资源管理,比简单 try-finally 更规范。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 我能解释 GIL 是什么、为什么存在、对并发的影响
- [ ] 我能区分多线程/多进程/协程的适用场景
- [ ] 我能画出 asyncio 事件循环的工作流程
- [ ] 我能解释深浅拷贝的区别和内存结构
- [ ] 我能手写带参数的装饰器(含 functools.wraps)
- [ ] 我能解释 yield 的工作原理和生成器的惰性求值
- [ ] 我能用 FastAPI 实现 SSE 流式接口
- [ ] 我能解释 SQLAlchemy 的 N+1 问题及三种解决方案
- [ ] 我能解释 Pydantic BaseModel 和 dataclass 的区别
- [ ] 我能用 contextmanager 实现数据库会话管理

### 代码题(3 个)

- [ ] 我能 5 分钟内手写带参数的装饰器
- [ ] 我能 10 分钟内手写异步并发限制器
- [ ] 我能 10 分钟内手写 SQLAlchemy CRUD + 连接池配置

---

## 延伸阅读

### 必读
- 《Effective Python》Brett Slatkin — 90+ 条 Python 最佳实践
- 《Fluent Python》Luciano Ramalho — Python 进阶圣经(第 2 版覆盖 3.10)
- FastAPI 官方文档 — https://fastapi.tiangolo.com/(最好的教程就是官方文档)
- SQLAlchemy 官方 ORM 教程 — https://docs.sqlalchemy.org/en/20/tutorial/

### 选读
- 《Python Cookbook》David Beazley — 实用技巧大全
- PEP 703 — Free-threaded CPython(无 GIL 方案)
- asyncio 官方文档 — https://docs.python.org/3/library/asyncio.html

### 实战
- 用 FastAPI + SQLAlchemy + SSE 实现一个 Agent 问答服务(本 Day Q7+Q8)
- 用 asyncio 实现一个支持并发限制的 LLM 批量调用工具(本 Day Q5)
- 用 Pydantic 设计 Agent 的状态模型和工具参数 Schema(本 Day Q10)

---

> **今日小结**:Python 是 Agent 生态的"母语",面试官在问 Python 时实际在问你的工程化能力。核心三件事:**并发**(GIL/asyncio 决定你能不能写出高性能 Agent)、**接口**(FastAPI/SSE 决定你能不能把 Agent 服务化)、**数据**(SQLAlchemy/Pydantic 决定你能不能做好持久化和数据验证)。Q1(GIL)、Q5(asyncio)、Q7(FastAPI)是面试高频中的高频,务必能脱稿讲清楚。
