"""
Agent 模块 - 记忆系统(Memory)

【对应学习日】Day05: Agent 记忆系统
【核心概念】
  - 短期记忆(Working Memory):当前对话的最近 N 轮,直接放入 prompt
  - 长期记忆(Long-term Memory):历史对话向量化存储,按相关度检索
  - 记忆评分公式:Score = 0.45×sim + 0.20×recency + 0.20×importance + 0.15×freq

【架构】
  ┌───────────────────────────────────────┐
  │           Agent Memory                 │
  │  ┌─────────────────────────────────┐  │
  │  │  短期记忆 (对话窗口)              │  │ ← 最近 N 轮,直接拼接
  │  │  [user: 什么是RAG?]              │  │
  │  │  [assistant: RAG是...]           │  │
  │  │  [user: 和Agent什么区别?]        │  │
  │  └─────────────────────────────────┘  │
  │  ┌─────────────────────────────────┐  │
  │  │  长期记忆 (向量检索)              │  │ ← 按相似度检索 Top-K
  │  │  [历史对话1] [历史对话2] ...     │  │
  │  └─────────────────────────────────┘  │
  └───────────────────────────────────────┘

【面试考点】
  Q: 短期记忆和长期记忆的区别?
  A: 短期记忆是当前对话上下文窗口(如最近 10 轮),直接放入 prompt,消耗 token。
     长期记忆是跨会话的历史,向量化后存入向量库,按相关度检索,不占 token 预算。
"""
import time
from dataclasses import dataclass, field
from collections import deque
import numpy as np
from rag.embedder import TfidfEmbedder


@dataclass
class Message:
    """一条对话消息"""
    role: str           # "user" 或 "assistant"
    content: str        # 消息内容
    timestamp: float = field(default_factory=time.time)  # 时间戳(用于 recency 衰减)
    importance: float = 0.5  # 重要度(0-1,默认 0.5)


class ShortTermMemory:
    """
    短期记忆:固定长度的对话窗口

    用 deque(maxlen=N) 实现,超出窗口自动丢弃最早的消息。
    对应 Day11 Context Engineering:管理有限的上下文窗口。
    """

    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.messages: deque[Message] = deque(maxlen=window_size)

    def add(self, role: str, content: str, importance: float = 0.5):
        """添加消息"""
        self.messages.append(Message(
            role=role, content=content, importance=importance
        ))

    def get_context(self) -> str:
        """获取格式化的对话历史(放入 prompt)"""
        if not self.messages:
            return "(无历史对话)"
        lines = []
        for msg in self.messages:
            prefix = "用户" if msg.role == "user" else "助手"
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)

    def clear(self):
        """清空记忆"""
        self.messages.clear()

    def __len__(self):
        return len(self.messages)


class LongTermMemory:
    """
    长期记忆:向量化的历史对话,按相关度检索

    工作流程:
      1. 每轮对话结束后,将 user+assistant 消息存入长期记忆
      2. 新对话开始时,用当前 query 检索最相关的 N 条历史
      3. 检索结果作为额外上下文放入 prompt

    记忆评分(对应 Generative Agents 论文):
      Score = 0.45 × similarity + 0.20 × recency + 0.20 × importance + 0.15 × frequency
    """

    def __init__(self, embedder: TfidfEmbedder, top_k: int = 3, decay_lambda: float = 0.995):
        self.embedder = embedder
        self.top_k = top_k
        self.decay_lambda = decay_lambda  # 时间衰减系数

        self.memories: list[dict] = []     # [{"text": ..., "timestamp": ..., "importance": ...}]
        self.vectors: list[np.ndarray] = []
        self.frequency: dict[int, int] = {}  # memory_index → 被检索次数

    def add(self, text: str, importance: float = 0.5):
        """添加一条长期记忆"""
        vec = self.embedder.embed(text)
        self.memories.append({
            "text": text,
            "timestamp": time.time(),
            "importance": importance,
        })
        self.vectors.append(vec)
        self.frequency[len(self.memories) - 1] = 0

    def retrieve(self, query: str) -> list[str]:
        """
        检索最相关的记忆

        评分公式: Score = 0.45×sim + 0.20×recency + 0.20×imp + 0.15×freq
        """
        if not self.memories:
            return []

        query_vec = self.embedder.embed(query)
        now = time.time()

        scores = []
        for i, (mem, vec) in enumerate(zip(self.memories, self.vectors)):
            # 1. 相似度(余弦相似度)
            sim = TfidfEmbedder.cosine_similarity(query_vec, vec)

            # 2. 时间近度(指数衰减)
            time_diff = now - mem["timestamp"]
            recency = self.decay_lambda ** (time_diff / 3600)  # 按小时衰减

            # 3. 重要度
            importance = mem["importance"]

            # 4. 频率(被检索次数,归一化)
            max_freq = max(self.frequency.values()) if self.frequency else 1
            freq = self.frequency[i] / max_freq if max_freq > 0 else 0

            # 综合评分
            score = 0.45 * sim + 0.20 * recency + 0.20 * importance + 0.15 * freq
            scores.append((i, score))

        # 按评分降序,取 Top-K
        scores.sort(key=lambda x: -x[1])
        results = []
        for idx, score in scores[:self.top_k]:
            results.append(self.memories[idx]["text"])
            self.frequency[idx] += 1  # 更新被检索次数

        return results

    def __len__(self):
        return len(self.memories)


class AgentMemory:
    """
    Agent 记忆系统:整合短期记忆 + 长期记忆

    使用流程:
      1. memory = AgentMemory(embedder)
      2. memory.add("user", "什么是RAG?")
      3. memory.add("assistant", "RAG是检索增强生成...")
      4. context = memory.get_context(query)  # 获取完整记忆上下文
    """

    def __init__(self, embedder: TfidfEmbedder, window_size: int = 10, long_term_top_k: int = 3):
        self.short_term = ShortTermMemory(window_size=window_size)
        self.long_term = LongTermMemory(embedder, top_k=long_term_top_k)
        self.embedder = embedder

    def add(self, role: str, content: str, importance: float = 0.5):
        """添加一轮对话"""
        self.short_term.add(role, content, importance)
        # 将完整对话存入长期记忆(user+assistant 合并)
        if role == "assistant":
            # 获取最近的 user 消息
            recent = list(self.short_term.messages)
            if len(recent) >= 2:
                user_msg = recent[-2].content
                assistant_msg = recent[-1].content
                long_term_text = f"用户: {user_msg}\n助手: {assistant_msg}"
                self.long_term.add(long_term_text, importance)

    def get_context(self, query: str = "") -> str:
        """
        获取完整记忆上下文(放入 prompt)

        包含:
          1. 短期记忆:最近 N 轮对话
          2. 长期记忆:与当前 query 最相关的历史对话
        """
        parts = []

        # 短期记忆
        short_ctx = self.short_term.get_context()
        if short_ctx != "(无历史对话)":
            parts.append(f"=== 最近对话 ===\n{short_ctx}")

        # 长期记忆(如果当前不在该对话的延续中)
        if query:
            long_results = self.long_term.retrieve(query)
            if long_results:
                long_text = "\n---\n".join(long_results)
                parts.append(f"=== 相关历史记忆 ===\n{long_text}")

        return "\n\n".join(parts) if parts else ""

    def clear_short_term(self):
        """清空短期记忆(开始新会话)"""
        self.short_term.clear()

    def get_stats(self) -> dict:
        """获取记忆系统统计"""
        return {
            "short_term_count": len(self.short_term),
            "long_term_count": len(self.long_term),
        }
