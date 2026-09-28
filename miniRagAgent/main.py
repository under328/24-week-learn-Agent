"""
Mini RAG Agent - 主入口

【项目】智能知识库问答系统
【启动】python main.py
【访问】http://localhost:8000/docs (Swagger UI)

启动流程:
  1. 初始化数据库(SQLite,自动建表)
  2. 加载知识库(从 data/sample_docs/ 读取文档)
  3. 初始化 Agent(LLM + 工具 + 记忆)
  4. 启动 FastAPI 服务

这个文件是整个项目的"胶水",把各模块组装在一起。
"""
import sys
import os

# 确保项目根目录在 Python 路径中(让 import agent / rag / api / db 能工作)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import config
from db.database import init_db
from db.models import Session as SessionModel, Message as MessageModel
from rag.knowledge_base import KnowledgeBase
from rag.embedder import TfidfEmbedder
from agent.llm import create_llm
from agent.tools import create_default_registry
from agent.memory import AgentMemory
from agent.core import ReActAgent
from api.routes import router, init_agent


def create_app() -> FastAPI:
    """
    创建并配置 FastAPI 应用

    这是依赖注入的体现:所有组件在这里组装,然后注入到路由中。
    """
    # ============================================================
    # Step 1: 初始化数据库
    # ============================================================
    print("\n" + "=" * 60)
    print("  Mini RAG Agent - 启动中...")
    print("=" * 60)

    print("\n[1/4] 初始化数据库...")
    init_db()

    # ============================================================
    # Step 2: 加载知识库
    # ============================================================
    print("\n[2/4] 加载知识库...")
    knowledge_base = KnowledgeBase()
    knowledge_base.load_from_directory(config.KNOWLEDGE_DIR)
    stats = knowledge_base.get_stats()
    print(f"  → 文档块: {stats['total_chunks']}, 来源: {stats['sources']}")

    # ============================================================
    # Step 3: 初始化 Agent
    # ============================================================
    print("\n[3/4] 初始化 Agent...")
    print(f"  → LLM 模式: {config.LLM_MODE}")

    # 共享 embedder(知识库和记忆系统共用同一个向量化模型)
    embedder = knowledge_base.embedder

    # 创建记忆系统
    memory = AgentMemory(
        embedder=embedder,
        window_size=config.SHORT_TERM_WINDOW,
        long_term_top_k=config.LONG_TERM_TOP_K,
    )
    print(f"  → 记忆系统: 短期窗口={config.SHORT_TERM_WINDOW}, 长期检索={config.LONG_TERM_TOP_K}")

    # 创建工具注册器(注入知识库)
    tools = create_default_registry(knowledge_base=knowledge_base)
    print(f"  → 工具: {list(tools.tools.keys())}")

    # 创建 LLM
    llm = create_llm()

    # 创建 Agent
    agent = ReActAgent(
        llm=llm,
        tools=tools,
        memory=memory,
        max_steps=config.MAX_AGENT_STEPS,
    )
    print(f"  → 最大推理步数: {config.MAX_AGENT_STEPS}")

    # ============================================================
    # Step 4: 创建 FastAPI 应用
    # ============================================================
    print("\n[4/4] 配置 FastAPI...")
    app = FastAPI(
        title="Mini RAG Agent",
        description="""
        智能知识库问答系统 Demo

        ## 功能
        - **问答**:Agent 使用 ReAct 循环回答问题
        - **知识库**:支持上传文档,自动分块、索引、检索
        - **流式输出**:SSE 逐步推送 Agent 的思考过程
        - **会话管理**:对话历史持久化到 SQLite

        ## 技术栈
        - Agent: ReAct 循环 + Function Calling
        - RAG: 分块 + TF-IDF Embedding + 向量检索 + Rerank
        - Memory: 短期对话窗口 + 长期向量记忆
        - API: FastAPI + Pydantic + SSE
        - DB: SQLAlchemy + SQLite
        """,
        version="1.0.0",
    )

    # CORS 中间件(允许跨域,前端开发需要)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注入 Agent 实例到路由模块
    init_agent(agent, knowledge_base, memory)

    # 注册路由
    app.include_router(router, tags=["Agent API"])

    # 根路由
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "service": "Mini RAG Agent",
            "version": "1.0.0",
            "docs": "/docs",
            "endpoints": {
                "chat": "POST /chat",
                "chat_stream": "POST /chat/stream",
                "messages": "GET /sessions/{session_id}/messages",
                "upload": "POST /knowledge/upload",
                "stats": "GET /knowledge/stats",
                "health": "GET /health",
            },
        }

    print("\n" + "=" * 60)
    print(f"  启动成功! 访问 http://localhost:{config.API_PORT}/docs")
    print("=" * 60 + "\n")

    return app


# 创建应用(uvicorn 直接引用)
app = create_app()


if __name__ == "__main__":
    # 开发模式:直接运行 python main.py
    # 生产模式:uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    uvicorn.run(
        "main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,  # 代码修改自动重启(开发模式)
        log_level="info",
    )
