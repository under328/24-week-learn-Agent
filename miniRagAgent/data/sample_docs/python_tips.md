# Python 工程化要点

## GIL 全局解释器锁

GIL(Global Interpreter Lock)是 CPython 中的互斥锁,确保同一时刻只有一个线程执行 Python 字节码。

GIL 对 CPU 密集型任务无效(多线程不能利用多核),对 IO 密集型任务有效(IO 等待时释放 GIL)。

CPU 密集用多进程(multiprocessing),IO 密集用协程(asyncio)或多线程。

## asyncio 异步编程

asyncio 是 Python 的异步 IO 框架,基于事件循环(Event Loop)实现单线程并发。

async/await 是协程的语法糖。当协程 await 一个 IO 操作时,事件循环切换到其他协程执行,避免阻塞。

asyncio.gather 可以并发执行多个协程,适合并行调用多个 LLM API。

## FastAPI

FastAPI 是基于 asyncio 的现代 Web 框架,特点:异步原生、Pydantic 数据验证、自动 Swagger 文档、依赖注入。

Agent 服务化通常用 FastAPI 暴露 API,支持 SSE 流式输出让用户实时看到 Agent 的思考过程。

## SQLAlchemy ORM

SQLAlchemy 是 Python 最流行的 ORM 框架。核心概念:Engine(连接工厂)、Session(工作单元)、Model(ORM 模型)。

N+1 查询问题是 ORM 常见陷阱:查 N 条记录后,访问关系字段时每条触发一次查询。解决方案:joinedload(JOIN)、selectinload(IN 查询,推荐)、subqueryload(子查询)。

## Pydantic 数据验证

Pydantic 用 Python 类型提示做运行时数据验证。BaseModel 自动验证字段类型和约束,广泛用于 FastAPI 和 LangChain。

Pydantic vs dataclass:Pydantic 有运行时验证(适合 API 边界),dataclass 无验证(适合内部数据结构)。
