"""
RAG 模块 - 检索器(Retriever)

【对应学习日】Day09-10: 向量检索 + Rerank
【核心概念】
  - 向量检索:把 query 向量化,与知识库所有 chunk 计算相似度,取 Top-K
  - Rerank:用更精细的模型对 Top-K 重新排序(本 Demo 用关键词匹配模拟)
  - 混合检索:BM25(关键词) + 向量(语义) → RRF 融合(本 Demo 简化为纯向量)

【面试考点】
  Q: 为什么需要 Rerank?
  A: 向量检索是"双塔"模型(query 和 doc 独立编码),精度有限。
     Rerank 用"交叉编码"(query 和 doc 拼接后编码),精度更高但速度慢。
     所以先用向量检索粗筛 Top-20,再用 Rerank 精排 Top-3,兼顾速度和精度。

  Q: RRF 融合公式?
  A: RRF(d) = Σ 1/(k + rank_i(d)), k=60。对每路检索结果按排名倒数求和,融合多路结果。
"""
import numpy as np
from typing import Optional
from rag.chunker import Chunk
from rag.embedder import TfidfEmbedder


class VectorRetriever:
    """
    向量检索器

    工作流程:
      1. 知识库初始化时:所有 chunk → embed → 存入向量矩阵
      2. 查询时:query → embed → 与矩阵做余弦相似度 → Top-K
      3. Rerank:对 Top-K 用关键词重排 → Top-N
    """

    def __init__(self, embedder: TfidfEmbedder, top_k: int = 5, rerank_top_k: int = 3):
        self.embedder = embedder
        self.top_k = top_k
        self.rerank_top_k = rerank_top_k

        # 知识库存储
        self.chunks: list[Chunk] = []          # 所有文档块
        self.chunk_vectors: np.ndarray = None   # 对应的向量矩阵 (N × dim)

    def add_chunks(self, chunks: list[Chunk]):
        """添加文档块到知识库,并计算向量"""
        self.chunks.extend(chunks)
        # 重新计算所有向量(简化实现;生产环境应增量计算)
        texts = [c.content for c in self.chunks]
        self.chunk_vectors = self.embedder.embed_batch(texts)

    def retrieve(self, query: str) -> list[tuple[Chunk, float]]:
        """
        检索:query → Top-K chunks → Rerank → Top-N

        Args:
            query: 用户查询

        Returns:
            [(chunk, score), ...] 按相关度降序
        """
        if self.chunk_vectors is None or len(self.chunks) == 0:
            return []

        # Step 1: 向量检索(粗筛)
        query_vec = self.embedder.embed(query)
        scores = self._batch_cosine_similarity(query_vec, self.chunk_vectors)

        # 取 Top-K
        top_indices = np.argsort(scores)[::-1][:self.top_k]
        candidates = [(self.chunks[i], float(scores[i])) for i in top_indices]

        # Step 2: Rerank(精排)
        reranked = self._rerank(query, candidates)

        # 取 Top-N
        return reranked[:self.rerank_top_k]

    def _batch_cosine_similarity(self, query_vec: np.ndarray, doc_vectors: np.ndarray) -> np.ndarray:
        """
        批量余弦相似度计算

        query_vec: (dim,)
        doc_vectors: (N, dim)
        returns: (N,) 每个文档与 query 的相似度
        """
        # 矩阵乘法:query · doc = (dim,) · (N, dim) → (N,)
        dot_products = doc_vectors @ query_vec
        # L2 范数
        query_norm = np.linalg.norm(query_vec)
        doc_norms = np.linalg.norm(doc_vectors, axis=1)
        # 避免除零
        denominators = doc_norms * query_norm + 1e-8
        return dot_products / denominators

    def _rerank(self, query: str, candidates: list[tuple[Chunk, float]]) -> list[tuple[Chunk, float]]:
        """
        简易 Rerank:用关键词重叠度重排序

        生产环境应用 Cross-Encoder 模型(如 bge-reranker-large)做 Rerank。
        这里用关键词匹配数量作为 rerank 分数,模拟"精排"效果。

        Rerank 分数 = 0.5 × 向量相似度 + 0.5 × 关键词重叠度
        """
        query_words = set(query.lower().split())
        reranked = []

        for chunk, vec_score in candidates:
            # 关键词重叠度:query 中的词有多少出现在 chunk 中
            chunk_words = set(chunk.content.lower().split())
            overlap = len(query_words & chunk_words)
            overlap_score = overlap / max(len(query_words), 1)

            # 综合分数
            final_score = 0.5 * vec_score + 0.5 * overlap_score
            reranked.append((chunk, final_score))

        # 按综合分数降序
        reranked.sort(key=lambda x: -x[1])
        return reranked
