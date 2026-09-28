"""
DB 模块 - SQLAlchemy ORM 模型

【对应学习日】Day35: SQLAlchemy ORM
【核心概念】
  - ORM:对象关系映射,Python 类 ↔ 数据库表
  - Session:工作单元,管理对象的增删改查
  - Relationship:表间关系(一对多、多对一)

  sessions 表(会话)  ──一对多──  messages 表(消息)
  id (PK)                         id (PK)
  user_id                         session_id (FK)
  title                           role
  created_at                      content
  updated_at                      tokens
                                  created_at
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Session(Base):
    """会话表:一个用户的一个对话会话"""
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)          # UUID
    user_id = Column(String(36), nullable=False, index=True)  # 用户 ID(建索引加速查询)
    title = Column(String(200), default="新对话")       # 会话标题
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 一对多:一个 Session 有多条 Message
    # cascade="all, delete-orphan" → 删除 Session 时自动删除关联的 Message
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, title={self.title})>"


class Message(Base):
    """消息表:会话中的每条消息"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)            # user / assistant / system
    content = Column(Text, nullable=False)               # 消息内容
    tool_calls = Column(Text)                            # JSON 格式的工具调用记录
    tokens = Column(Integer, default=0)                  # token 消耗
    created_at = Column(DateTime, default=datetime.utcnow)

    # 多对一:多条 Message 属于一个 Session
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role}, content={self.content[:30]}...)>"
