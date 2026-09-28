"""
Mini RAG Agent - 全局配置

这个文件集中管理所有配置项,方便面试时讲"配置中心"的设计思路。
生产环境应改为从环境变量/配置文件读取(如 pydantic-settings)。
"""
import os

# ============================================================
# LLM 配置
# ============================================================
# 模式: "mock" 或 "openai"
# - mock:   内置模拟 LLM,无需 API Key,用于演示 ReAct 循环
# - openai: 调用 OpenAI API(需要 OPENAI_API_KEY 环境变量)
LLM_MODE = os.getenv("LLM_MODE", "mock")

# OpenAI 配置(仅 LLM_MODE=openai 时生效)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# ============================================================
# RAG 配置
# ============================================================
# 分块参数(对应 Day08: 文档分块策略)
CHUNK_SIZE = 300           # 每块目标 token 数(小文档用 300,大文档用 512)
CHUNK_OVERLAP = 50         # 块间重叠(避免语义断裂)

# 检索参数(对应 Day10: 向量检索)
RETRIEVAL_TOP_K = 5        # 初步检索返回数量
RERANK_TOP_K = 3           # Rerank 后保留数量(喂给 LLM 的上下文数)

# Embedding 维度(TF-IDF 特征空间大小,真实场景用 768/1024/1536)
EMBEDDING_DIM = 500

# ============================================================
# Agent 配置
# ============================================================
# ReAct 循环最大步数(防止无限循环)
MAX_AGENT_STEPS = 8

# 记忆系统(对应 Day05)
SHORT_TERM_WINDOW = 10     # 短期记忆:保留最近 N 轮对话
LONG_TERM_TOP_K = 3        # 长期记忆:检索最相关的 N 条历史

# ============================================================
# 数据库配置
# ============================================================
# SQLite(零配置,文件即数据库)
DATABASE_URL = "sqlite:///./mini_agent.db"

# 连接池参数(对应 Day35: SQLAlchemy 连接池)
DB_POOL_SIZE = 5           # 常驻连接数
DB_MAX_OVERFLOW = 10       # 临时连接数
DB_POOL_RECYCLE = 3600     # 连接回收时间(秒)

# ============================================================
# API 配置
# ============================================================
API_HOST = "0.0.0.0"
API_PORT = 8000

# 知识库文档目录
KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "data", "sample_docs")
