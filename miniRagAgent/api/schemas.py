"""
API 模块 - Pydantic 数据模型(Schemas)

【对应学习日】Day35: Pydantic 数据验证
【核心概念】
  - Pydantic BaseModel:运行时数据验证 + 类型转换
  - Field:字段约束(min_length, max_length, ge, le)
  - 自动 JSON Schema:FastAPI 据此生成 Swagger 文档

  Pydantic vs dataclass:
    - Pydantic:运行时验证,适合 API 边界(外部输入)
    - dataclass:无验证,适合内部数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================================
# 请求模型(客户端 → 服务端)
# ============================================================

class ChatRequest(BaseModel):
    """聊天请求"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="用户问题",
        examples=["什么是 RAG?"],
    )
    session_id: Optional[str] = Field(
        None,
        description="会话 ID,首次对话不传则自动创建",
    )

class KnowledgeUploadRequest(BaseModel):
    """知识库上传请求"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="文档内容(Markdown 或纯文本)",
    )
    source: str = Field(
        "upload",
        max_length=200,
        description="文档来源标识",
    )


# ============================================================
# 响应模型(服务端 → 客户端)
# ============================================================

class ChatResponse(BaseModel):
    """聊天响应(非流式)"""
    answer: str = Field(..., description="Agent 的回答")
    session_id: str = Field(..., description="会话 ID")
    steps: list[dict] = Field(
        default_factory=list,
        description="Agent 推理步骤(Thought/Action/Observation)",
    )
    tool_calls: list[dict] = Field(
        default_factory=list,
        description="工具调用记录",
    )
    elapsed: float = Field(..., description="总耗时(秒)")


class SessionInfo(BaseModel):
    """会话信息"""
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class MessageInfo(BaseModel):
    """消息信息"""
    id: int
    role: str
    content: str
    created_at: datetime


class KnowledgeStatsResponse(BaseModel):
    """知识库统计"""
    total_chunks: int
    sources: list[str]
    embedding_dim: int


class HealthResponse(BaseModel):
    """健康检查"""
    status: str = "ok"
    llm_mode: str = ""
    knowledge_chunks: int = 0
    memory_stats: dict = {}
