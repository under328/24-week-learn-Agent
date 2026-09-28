"""
RAG 模块 - Embedding 模型

【对应学习日】Day08-10: Embedding 与向量检索
【核心概念】
  - Embedding:把文本映射为固定维度的浮点向量,使语义相近的文本向量也相近
  - TF-IDF:词频-逆文档频率,经典的文本向量化方法(无需预训练模型)
  - 余弦相似度:衡量两个向量方向的一致性,值域 [-1, 1],越接近 1 越相似

【为什么用 TF-IDF 而不是 BGE/OpenAI?】
  本项目追求"零配置可运行"。TF-IDF 纯 Python+NumPy 实现,无需下载模型。
  生产环境应替换为 bge-large-zh / text-embedding-3 等预训练模型(效果更好)。

【面试考点】
  Q: TF-IDF 和深度 Embedding 的区别?
  A: TF-IDF 基于词频统计,无法理解同义词(如"手机"和"手机"匹配,但"手机"和"智能手机"不匹配)。
     深度 Embedding(BGE 等)基于语义理解,能捕捉同义关系,效果显著更好。
     但 TF-IDF 零成本、可解释、适合 Demo 和基线对比。
"""
import math
import re
from collections import Counter
import numpy as np


class TfidfEmbedder:
    """
    TF-IDF Embedding 模型

    工作原理:
      1. Fit 阶段:统计所有文档的词频,计算 IDF(逆文档频率)
      2. Embed 阶段:对每段文本计算 TF-IDF 向量
      3. 相似度:用余弦相似度比较两个向量

    TF-IDF 公式:
      TF(t, d) = 词 t 在文档 d 中出现的次数 / 文档 d 的总词数
      IDF(t) = log(N / (1 + df(t)))    N=文档总数, df(t)=包含词 t 的文档数
      TF-IDF(t, d) = TF(t, d) × IDF(t)
    """

    def __init__(self, max_features: int = 500):
        self.max_features = max_features  # 词汇表大小(向量维度)
        self.vocabulary: dict[str, int] = {}  # 词 → 索引
        self.idf: np.ndarray = None       # IDF 权重向量

    def fit(self, documents: list[str]):
        """
        训练:构建词汇表 + 计算 IDF

        Args:
            documents: 所有文档文本列表
        """
        # Step 1: 对所有文档分词,统计词频
        all_tokens = [self._tokenize(doc) for doc in documents]

        # Step 2: 统计每个词出现在多少个文档中(文档频率 df)
        df = Counter()
        for tokens in all_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        # Step 3: 选 top max_features 个词作为词汇表(按 df 排序,太罕见的词不要)
        top_words = sorted(df.items(), key=lambda x: -x[1])[:self.max_features]
        self.vocabulary = {word: idx for idx, (word, _) in enumerate(top_words)}

        # Step 4: 计算 IDF = log(N / (1 + df))
        N = len(documents)
        self.idf = np.zeros(len(self.vocabulary))
        for word, idx in self.vocabulary.items():
            self.idf[idx] = math.log(N / (1 + df[word]))

    def embed(self, text: str) -> np.ndarray:
        """
        将文本转为 TF-IDF 向量

        Args:
            text: 输入文本

        Returns:
            归一化的 TF-IDF 向量(维度 = max_features)
        """
        if not self.vocabulary:
            # 未训练,返回零向量
            return np.zeros(self.max_features)

        tokens = self._tokenize(text)
        tf = Counter(tokens)

        # 构建 TF-IDF 向量
        vec = np.zeros(len(self.vocabulary))
        for word, count in tf.items():
            if word in self.vocabulary:
                idx = self.vocabulary[word]
                vec[idx] = count * self.idf[idx]

        # L2 归一化(使余弦相似度简化为点积)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm

        return vec

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """批量向量化"""
        return np.array([self.embed(t) for t in texts])

    def _tokenize(self, text: str) -> list[str]:
        """
        简易中文分词(按字符 + 英文按单词)

        生产环境应使用 jieba(中文)或 tiktoken(英文)。
        这里简化:中文按单字切,英文按单词切,全部小写。
        """
        # 英文:按非字母字符分割
        words = re.findall(r'[a-zA-Z]+', text.lower())
        # 中文:按单字切
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        return words + chinese_chars

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        余弦相似度 = dot(v1, v2) / (|v1| × |v2|)

        如果向量已归一化,则 cosine_sim = dot(v1, v2)
        """
        dot = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot / (norm1 * norm2))
