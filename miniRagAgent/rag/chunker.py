"""
RAG 模块 - 文档分块器(Chunker)

【对应学习日】Day08: RAG 全链路 —— 分块策略
【核心概念】
  - 递归分块:先按段落(\\n\\n)切,再按句子切,最后按字符切
  - 重叠窗口:相邻块有 overlap,避免语义断裂(如一句话被切成两半)
  - 元数据:每个 chunk 记录来源、位置,方便溯源

【面试考点】
  Q: 为什么 chunk size 重要?
  A: 太大 → 噪声多、检索不准、浪费 token;太小 → 语义不完整、上下文不足。
     经验值:中文 300-500 token,英文 512-1024 token,需根据文档类型实验调优。
"""
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Chunk:
    """一个文档块"""
    content: str                          # 块文本内容
    source: str = ""                      # 来源文件名
    chunk_index: int = 0                  # 块在原文中的序号
    start_char: int = 0                   # 在原文中的起始字符位置
    metadata: dict = field(default_factory=dict)  # 额外元数据(标题、时间等)

    def __repr__(self):
        preview = self.content[:50].replace("\n", " ")
        return f"Chunk(src={self.source}, idx={self.chunk_index}, len={len(self.content)}, preview='{preview}...')"


class RecursiveChunker:
    """
    递归分块器(对应 LangChain 的 RecursiveCharacterTextSplitter)

    工作原理:
      1. 先用大分隔符(段落 \\n\\n)切分
      2. 如果某块仍超过 chunk_size,用小分隔符(句子 。!?)继续切
      3. 如果还超过,用更小的分隔符(空格、字符)切
      4. 相邻块之间保留 overlap 个字符的重叠

    为什么递归?因为不同文档结构不同 —— 有的段落短(FAQ),有的段落长(论文)。
    递归确保无论文档结构如何,最终块大小都接近目标值。
    """

    def __init__(self, chunk_size: int = 300, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # 分隔符优先级:从大到小(段落 > 句子 > 空格 > 字符)
        self.separators = ["\n\n", "\n", "。", "！", "？", ". ", "! ", "? ", " ", ""]

    def chunk_text(self, text: str, source: str = "") -> list[Chunk]:
        """
        将长文本分块。

        Args:
            text: 原始文本
            source: 来源标识(文件名等)

        Returns:
            Chunk 列表
        """
        # Step 1: 递归切分到不超过 chunk_size 的片段
        segments = self._recursive_split(text, self.separators)

        # Step 2: 合并过小的片段 + 添加重叠
        chunks = self._merge_with_overlap(segments)

        # Step 3: 构造 Chunk 对象
        result = []
        current_pos = 0
        for i, chunk_text in enumerate(chunks):
            result.append(Chunk(
                content=chunk_text.strip(),
                source=source,
                chunk_index=i,
                start_char=current_pos,
            ))
            # 估算下一个块的起始位置(减去 overlap)
            current_pos += len(chunk_text) - self.chunk_overlap

        # 过滤空块
        return [c for c in result if c.content]

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        """递归切分:用当前分隔符切,如果块仍太大,用下一个分隔符继续切"""
        if len(text) <= self.chunk_size:
            return [text]

        # 尝试用第一个分隔符切分
        sep = separators[0]
        if sep == "":
            # 最后兜底:按字符数硬切
            return [text[i:i+self.chunk_size] for i in range(0, len(text), self.chunk_size)]

        parts = text.split(sep)
        result = []

        for part in parts:
            if len(part) <= self.chunk_size:
                result.append(part)
            else:
                # 这个部分仍然太大,用更小的分隔符递归切
                sub_parts = self._recursive_split(part, separators[1:])
                result.extend(sub_parts)

        return result

    def _merge_with_overlap(self, segments: list[str]) -> list[str]:
        """合并过小的片段,并在相邻块之间添加重叠"""
        if not segments:
            return []

        chunks = []
        current_chunk = ""

        for segment in segments:
            # 如果当前块 + 新片段不超过目标大小,合并
            if len(current_chunk) + len(segment) <= self.chunk_size:
                current_chunk += segment
            else:
                # 当前块已满,保存
                if current_chunk:
                    chunks.append(current_chunk)

                # 新块从当前块的尾部 overlap 处开始(实现重叠)
                if self.chunk_overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + segment
                else:
                    current_chunk = segment

        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks
