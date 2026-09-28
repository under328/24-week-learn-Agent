"""
RAG 模块 - 知识库管理(KnowledgeBase)

【对应学习日】Day08, Day13: RAG 全链路整合
【核心概念】
  - 知识库 = 文档集合 → 分块 → Embedding → 向量索引
  - 增量更新:新文档加入时重新计算向量(本 Demo 简化为全量重建)
  - 检索门控:低相关度时返回空,避免幻觉(对应 Day09: Agentic RAG)

【面试考点】
  Q: 知识库更新后如何不影响在线服务?
  A: 双索引策略 —— 新索引构建完成后原子切换;或蓝绿部署,新文档先写入新索引,
     验证无误后切换流量。生产环境用 Milvus 的分区功能实现。
"""
import os
from typing import Optional
from rag.chunker import RecursiveChunker, Chunk
from rag.embedder import TfidfEmbedder
from rag.retriever import VectorRetriever
import config


class KnowledgeBase:
    """
    知识库:整合 Chunker + Embedder + Retriever

    使用流程:
      1. kb = KnowledgeBase()
      2. kb.add_document(text, source="file.md")   # 添加文档
      3. kb.load_from_directory("./data/docs")      # 批量加载
      4. results = kb.search("什么是 Agent?")       # 检索
    """

    def __init__(
        self,
        chunk_size: int = config.CHUNK_SIZE,
        chunk_overlap: int = config.CHUNK_OVERLAP,
        top_k: int = config.RETRIEVAL_TOP_K,
        rerank_top_k: int = config.RERANK_TOP_K,
        embedding_dim: int = config.EMBEDDING_DIM,
    ):
        self.chunker = RecursiveChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embedder = TfidfEmbedder(max_features=embedding_dim)
        self.retriever = VectorRetriever(self.embedder, top_k=top_k, rerank_top_k=rerank_top_k)
        self._all_chunks: list[Chunk] = []

    def add_document(self, text: str, source: str = ""):
        """添加单个文档到知识库"""
        chunks = self.chunker.chunk_text(text, source=source)
        self._all_chunks.extend(chunks)
        self._rebuild_index()

    def load_from_directory(self, dir_path: str):
        """批量加载目录下的所有 .md / .txt 文件"""
        if not os.path.exists(dir_path):
            print(f"[KnowledgeBase] 目录不存在: {dir_path}")
            return

        for filename in sorted(os.listdir(dir_path)):
            if filename.endswith((".md", ".txt")):
                filepath = os.path.join(dir_path, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                self.add_document(text, source=filename)
                print(f"[KnowledgeBase] 已加载: {filename} ({len(text)} 字符)")

        print(f"[KnowledgeBase] 知识库就绪: {len(self._all_chunks)} 个文档块")

    def search(self, query: str, top_k: Optional[int] = None) -> list[tuple[Chunk, float]]:
        """
        检索知识库

        Args:
            query: 查询文本
            top_k: 返回数量(默认用配置值)

        Returns:
            [(chunk, score), ...] 按相关度降序
        """
        results = self.retriever.retrieve(query)
        if top_k:
            results = results[:top_k]
        return results

    def get_context(self, query: str) -> str:
        """
        检索并格式化为 LLM 上下文

        格式:
          [来源: file.md] 内容...
          [来源: file.md] 内容...
        """
        results = self.search(query)
        if not results:
            return "(知识库中未找到相关内容)"

        context_parts = []
        for chunk, score in results:
            context_parts.append(
                f"[来源: {chunk.source}, 相关度: {score:.3f}]\n{chunk.content}"
            )
        return "\n\n---\n\n".join(context_parts)

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        return {
            "total_chunks": len(self._all_chunks),
            "sources": list(set(c.source for c in self._all_chunks)),
            "embedding_dim": self.embedder.max_features,
        }

    def _rebuild_index(self):
        """重建索引:重新 fit embedder + 重新计算所有向量"""
        if not self._all_chunks:
            return

        # Fit embedder(用所有 chunk 文本训练 TF-IDF)
        texts = [c.content for c in self._all_chunks]
        self.embedder.fit(texts)

        # 重建检索器向量
        self.retriever.chunks = self._all_chunks.copy()
        self.retriever.chunk_vectors = self.embedder.embed_batch(texts)
