# RAG 检索增强生成

## 什么是 RAG?

RAG(Retrieval-Augmented Generation,检索增强生成)是一种结合检索和生成的技术。

RAG 的全链路:文档 → 解析 → 分块(Chunk) → Embedding → 存入向量库 → 检索 → Rerank → 上下文组装 → LLM 生成。

RAG 解决了 LLM 的两大问题:知识时效性(模型训练后的新知识)和幻觉(无依据的编造)。

## 文档分块策略

分块是 RAG 的第一步,直接影响检索质量。

常见策略:固定长度分块(简单但可能切断语义)、递归分块(先段落再句子,LangChain 默认)、语义分块(按语义相似度切分)、父子分块(小块检索,大块提供上下文)。

经验值:中文 chunk size 300-500 token,overlap 50-100 token,需根据文档类型实验调优。

## 混合检索

混合检索结合关键词检索(BM25)和语义检索(向量),取长补短。

BM25 擅长精确关键词匹配,向量检索擅长语义理解。用 RRF(Reciprocal Rank Fusion)融合两路结果。

RRF 公式:RRF(d) = Σ 1/(k + rank_i(d)),k=60。

## Rerank 重排序

向量检索是"双塔"模型,query 和 doc 独立编码,精度有限。Rerank 用 Cross-Encoder 将 query 和 doc 拼接后编码,精度更高但速度慢。

所以先用向量检索粗筛 Top-20,再用 Rerank 精排 Top-3,兼顾速度和精度。

## RAGAS 评估

RAGAS 是 RAG 系统的评估框架,四个核心指标:Faithfulness(答案是否忠于上下文)、Answer Relevancy(答案是否切题)、Context Precision(检索上下文精度)、Context Recall(检索上下文召回)。
