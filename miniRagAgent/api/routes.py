"""
API 模块 - FastAPI 路由

【对应学习日】Day35: FastAPI 接口设计 + SSE 流式输出
【核心概念】
  - FastAPI:异步 Web 框架,原生 async/await 支持
  - SSE (Server-Sent Events):服务端推送,逐 token 发送
  - 依赖注入:Depends() 管理数据库连接
  - Pydantic:自动参数验证 + JSON Schema

  SSE 格式: data: {json}\n\n
  客户端用 EventSource API 接收。
"""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession

from api.schemas import (
    ChatRequest, ChatResponse, MessageInfo,
    KnowledgeUploadRequest, KnowledgeStatsResponse, HealthResponse,
)
from db.database import get_db_dependency
from db.models import Session as SessionModel, Message as MessageModel
import config

router = APIRouter()

# ============================================================
# 全局 Agent 实例(在 main.py 中初始化)
# ============================================================
# 为什么用全局变量?
# Agent 包含 LLM 连接、知识库索引、记忆系统等重型资源,
# 每次请求创建新实例会重复加载。用全局单例复用资源。
# 生产环境可用 FastAPI 的 Dependency Injection + lru_cache 替代。
_agent = None
_knowledge_base = None
_memory = None


def init_agent(agent, knowledge_base, memory):
    """初始化全局 Agent 实例(在 main.py 中调用)"""
    global _agent, _knowledge_base, _memory
    _agent = agent
    _knowledge_base = knowledge_base
    _memory = memory


# ============================================================
# 核心接口
# ============================================================

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: DBSession = Depends(get_db_dependency)):
    """
    同步聊天接口(非流式)

    流程:
      1. 创建/恢复会话
      2. Agent 执行 ReAct 循环
      3. 保存消息到数据库
      4. 返回完整结果
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    # 1. 会话管理
    session_id = request.session_id or str(uuid.uuid4())
    if not request.session_id:
        # 新会话,存入数据库
        db_session = SessionModel(id=session_id, user_id="default", title=request.query[:50])
        db.add(db_session)
    else:
        # 恢复记忆(从数据库加载历史)
        _load_history_to_memory(db, session_id)

    # 2. Agent 执行
    result = _agent.run(request.query)

    # 3. 保存消息到数据库
    db.add(MessageModel(
        session_id=session_id, role="user", content=request.query,
    ))
    db.add(MessageModel(
        session_id=session_id, role="assistant", content=result.answer,
        tool_calls=json.dumps(result.tool_calls, ensure_ascii=False),
    ))
    db.commit()

    # 4. 返回
    return ChatResponse(
        answer=result.answer,
        session_id=session_id,
        steps=[
            {"step": s.step_num, "thought": s.thought, "action": s.action,
             "action_input": s.action_input, "observation": s.observation[:200],
             "is_final": s.is_final}
            for s in result.steps
        ],
        tool_calls=result.tool_calls,
        elapsed=result.total_elapsed,
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, db: DBSession = Depends(get_db_dependency)):
    """
    SSE 流式聊天接口

    返回 Server-Sent Events 流,逐步推送 Agent 的思考过程:
      data: {"type": "thought", "content": "..."}
      data: {"type": "action", "name": "search_knowledge", "input": "..."}
      data: {"type": "observation", "content": "..."}
      data: {"type": "answer", "content": "最终答案"}
      data: {"type": "done"}

    客户端用 EventSource API 接收:
      const es = new EventSource("/chat/stream");
      es.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent 未初始化")

    session_id = request.session_id or str(uuid.uuid4())
    if not request.session_id:
        db.add(SessionModel(id=session_id, user_id="default", title=request.query[:50]))
    else:
        _load_history_to_memory(db, session_id)

    async def event_stream():
        """SSE 事件生成器"""
        final_answer = ""
        tool_calls = []

        # 流式执行 Agent
        for step in _agent.run_stream(request.query):
            if step.is_final:
                final_answer = step.action_input
                yield f"data: {json.dumps({'type': 'answer', 'content': step.action_input}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'thought', 'step': step.step_num, 'content': step.thought}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'action', 'step': step.step_num, 'name': step.action, 'input': step.action_input}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'observation', 'step': step.step_num, 'content': step.observation[:500]}, ensure_ascii=False)}\n\n"
                tool_calls.append({
                    "tool": step.action, "input": step.action_input,
                    "output": step.observation[:200],
                })

        yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"

        # 保存到数据库(流结束后用新 Session,因为请求级 Session 已关闭)
        from db.database import SessionLocal
        save_db = SessionLocal()
        try:
            save_db.add(MessageModel(
                session_id=session_id, role="user", content=request.query,
            ))
            save_db.add(MessageModel(
                session_id=session_id, role="assistant", content=final_answer,
                tool_calls=json.dumps(tool_calls, ensure_ascii=False),
            ))
            save_db.commit()
        except Exception as e:
            save_db.rollback()
        finally:
            save_db.close()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 不缓冲(确保实时推送)
        },
    )


# ============================================================
# 会话管理接口
# ============================================================

@router.get("/sessions/{session_id}/messages", response_model=list[MessageInfo])
async def get_messages(session_id: str, db: DBSession = Depends(get_db_dependency)):
    """获取会话的所有消息"""
    messages = db.query(MessageModel).filter(
        MessageModel.session_id == session_id
    ).order_by(MessageModel.created_at.asc()).all()

    if not messages:
        raise HTTPException(status_code=404, detail="会话不存在或无消息")

    return [MessageInfo(
        id=m.id, role=m.role, content=m.content, created_at=m.created_at
    ) for m in messages]


# ============================================================
# 知识库管理接口
# ============================================================

@router.post("/knowledge/upload")
async def upload_knowledge(request: KnowledgeUploadRequest):
    """上传文档到知识库"""
    if _knowledge_base is None:
        raise HTTPException(status_code=503, detail="知识库未初始化")

    _knowledge_base.add_document(request.content, source=request.source)
    stats = _knowledge_base.get_stats()

    return {"message": "文档已添加", "stats": stats}


@router.get("/knowledge/stats", response_model=KnowledgeStatsResponse)
async def knowledge_stats():
    """获取知识库统计"""
    if _knowledge_base is None:
        raise HTTPException(status_code=503, detail="知识库未初始化")

    stats = _knowledge_base.get_stats()
    return KnowledgeStatsResponse(
        total_chunks=stats["total_chunks"],
        sources=stats["sources"],
        embedding_dim=stats["embedding_dim"],
    )


# ============================================================
# 健康检查
# ============================================================

@router.get("/health", response_model=HealthResponse)
async def health():
    """健康检查"""
    memory_stats = _memory.get_stats() if _memory else {}
    kb_stats = _knowledge_base.get_stats() if _knowledge_base else {}

    return HealthResponse(
        status="ok",
        llm_mode=config.LLM_MODE,
        knowledge_chunks=kb_stats.get("total_chunks", 0),
        memory_stats=memory_stats,
    )


# ============================================================
# 辅助函数
# ============================================================

def _load_history_to_memory(db: DBSession, session_id: str):
    """从数据库加载历史消息到记忆系统"""
    if _memory is None:
        return

    messages = db.query(MessageModel).filter(
        MessageModel.session_id == session_id
    ).order_by(MessageModel.created_at.asc()).all()

    _memory.clear_short_term()
    for msg in messages:
        _memory.short_term.add(msg.role, msg.content)
