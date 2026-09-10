# Day 6:Vector Stores 与 Retriever、RAG 基础

> 今日主题:向量数据库、检索器(Retriever)、RAG 问答基础
> 预计学习时长:2-3 小时
> 前置条件:已完成 Day 1-5,理解文档加载、切分和嵌入

---

## 一、当日目标

1. 理解 Vector Store(向量数据库)的作用,掌握 Chroma 的基本用法
2. 掌握 Retriever(检索器)的概念和用法,能检索相关文档片段
3. 理解 RAG 的完整流程,能用 LCEL 构建 RAG 问答链
4. 实现一个基础的文档问答 demo

---

## 二、核心概念讲解

### 2.1 Vector Store(向量数据库)

Vector Store 是专门存储和检索**向量**的数据库。它的核心能力:

- **存储**:把文本片段及其向量存入数据库
- **检索**:给定一个查询向量,快速找到最相似的 N 个片段(近似最近邻搜索)

常用 Vector Store:

| 向量库 | 类型 | 安装 | 适用场景 |
|--------|------|------|----------|
| **Chroma** | 本地 | `pip install chromadb` | **入门推荐**,无需服务 |
| FAISS | 本地 | `pip install faiss-cpu` | 高性能,Facebook 出品 |
| Milvus | 服务 | 需部署 | 大规模生产 |
| Pinecone | 云服务 | 需注册 | 托管云服务 |
| PGVector | PostgreSQL 扩展 | 需 PostgreSQL | 已有 PG 基础设施 |

本教程用 **Chroma**,因为它纯本地、零配置、适合学习和原型。

### 2.2 Chroma 基本用法

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 嵌入模型
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 创建向量库并添加文档
vectorstore = Chroma.from_texts(
    texts=["文本1", "文本2", "文本3"],
    embedding=embeddings,
    persist_directory="./chroma_db",  # 持久化目录(可选)
)

# 检索
results = vectorstore.similarity_search("查询文本", k=3)  # 返回最相似的3个
```

### 2.3 Retriever(检索器)

Retriever 是 Vector Store 的**封装接口**,返回 `Document` 列表。它是 LCEL 链中的标准组件:

```python
# 把 VectorStore 转成 Retriever
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 使用
docs = retriever.invoke("查询文本")  # 返回最相关的3个Document
```

**为什么用 Retriever 而非直接用 VectorStore?**
- Retriever 是 Runnable,可以用 `|` 接入 LCEL 链
- 接口统一,可以替换为其他检索方式(如关键词检索、混合检索)

### 2.4 检索策略

| 方法 | 说明 |
|------|------|
| `similarity_search` | 相似度搜索(默认) |
| `max_marginal_relevance_search` | MMR 搜索,平衡相关性和多样性 |
| `as_retriever(search_type="mmr")` | 用 MMR 策略的 Retriever |

**MMR(Maximal Marginal Relevance)**:不只是选最相似的,还考虑结果之间的多样性,避免返回内容高度重复的片段。

### 2.5 RAG 完整流程

RAG 问答链的核心思路:

```
用户问题 -> Retriever 检索相关片段
         -> 把片段作为"上下文"放入 Prompt
         -> LLM 根据上下文回答问题
```

用 LCEL 实现:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "根据以下上下文回答问题。如果上下文没有答案,说'我不知道'。\n\n上下文: {context}"),
    ("human", "{question}"),
])

# RunnablePassthrough 把原始问题透传给 question 字段
# retriever 用问题检索文档,结果给 context 字段
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

answer = rag_chain.invoke("什么是 RAG?")
```

### 2.6 格式化检索结果

Retriever 返回的是 `Document` 列表,需要拼成字符串放入 Prompt:

```python
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

---

## 三、代码示例

### 3.1 安装依赖

```bash
pip install langchain-chroma chromadb
```

### 3.2 创建向量数据库并存储文档

```python
"""
Day6 示例 1:创建 Chroma 向量数据库
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 嵌入模型
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 准备文档片段
texts = [
    "LangChain 是一个用于构建 LLM 应用的开源框架",
    "LangChain 的核心组件包括模型接口、Prompt 模板、链和检索器",
    "LCEL 是 LangChain 的表达式语言,用管道符连接组件",
    "RAG 是检索增强生成技术,结合检索和生成",
    "Embedding 把文本转换成向量,用于语义相似度计算",
    "Chroma 是一个轻量级的本地向量数据库",
    "FAISS 是 Facebook 开发的高效向量检索库",
    "Agent 是能自主调用工具的 LLM",
    "Memory 让对话机器人记住历史消息",
    "Vector Store 专门用于存储和检索向量数据",
]

# 创建向量库(内存模式,不持久化)
vectorstore = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    collection_name="langchain_knowledge",
)

print(f"向量库已创建,存储了 {len(texts)} 条文档")

# 相似度搜索
query = "什么是 LangChain?"
results = vectorstore.similarity_search(query, k=3)

print(f"\n查询: {query}")
print(f"返回 {len(results)} 个结果:")
for i, doc in enumerate(results):
    print(f"  {i+1}. {doc.page_content}")
```

### 3.3 持久化向量数据库

```python
"""
Day6 示例 2:持久化向量数据库到磁盘
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

texts = [
    "Python 是一种流行的编程语言",
    "Java 是一种面向对象的编程语言",
    "JavaScript 是网页开发的脚本语言",
    "Go 是 Google 开发的并发编程语言",
    "Rust 是一种内存安全的系统编程语言",
]

# 持久化到磁盘
vectorstore = Chroma.from_texts(
    texts=texts,
    embedding=embeddings,
    persist_directory="./chroma_db",  # 指定持久化目录
    collection_name="programming_languages",
)

print("向量库已持久化到 ./chroma_db")

# 重新加载(模拟程序重启)
vectorstore_loaded = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="programming_languages",
)

# 验证:搜索
results = vectorstore_loaded.similarity_search("哪种语言适合系统编程?", k=2)
print(f"\n从磁盘加载后搜索:")
for i, doc in enumerate(results):
    print(f"  {i+1}. {doc.page_content}")
```

### 3.4 从文档创建向量库

```python
"""
Day6 示例 3:加载文档 -> 切分 -> 存入向量库
"""
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

# 准备文档
article = """
向量数据库简介

向量数据库是专门用于存储和检索高维向量的数据库系统。
随着大语言模型的兴起,向量数据库成为 AI 基础设施的重要组成部分。

向量数据库的核心功能包括:向量索引、近似最近邻搜索、元数据过滤等。
常见的向量数据库有 Chroma、FAISS、Milvus、Pinecone 等。

Chroma 数据库

Chroma 是一个开源的向量数据库,主打轻量级和易用性。
它支持本地嵌入式运行,无需单独部署服务端,非常适合开发和测试。
Chroma 也支持持久化存储,数据可以保存到磁盘。

FAISS 数据库

FAISS 是 Facebook AI Research 开发的向量检索库。
它专注于高效的相似度搜索和稠密向量聚类,性能非常高。
FAISS 支持 GPU 加速,适合处理大规模向量数据。

Milvus 数据库

Milvus 是一个分布式向量数据库,支持水平扩展。
它由 Zilliz 公司开发,适合生产环境的大规模向量检索。
Milvus 支持多种索引类型,包括 IVF、HNSW 等。
"""

with open("vector_db_article.txt", "w", encoding="utf-8") as f:
    f.write(article)

# 加载并切分
loader = TextLoader("vector_db_article.txt", encoding="utf-8")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=150, chunk_overlap=30)
chunks = splitter.split_documents(docs)

print(f"切分得到 {len(chunks)} 个片段")

# 存入向量库
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db",
    collection_name="vector_db_article",
)

print(f"已存入向量库,集合名: vector_db_article")

# 搜索
query = "Chroma 有什么特点?"
results = vectorstore.similarity_search(query, k=2)
print(f"\n查询: {query}")
for i, doc in enumerate(results):
    print(f"  {i+1}. {doc.page_content}")
```

### 3.5 使用 Retriever

```python
"""
Day6 示例 4:使用 Retriever
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 加载已有向量库
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="vector_db_article",
)

# 转成 Retriever
# search_kwargs={"k": 3} 表示每次返回 3 个最相关的片段
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# Retriever 是 Runnable,用 invoke 调用
query = "FAISS 是什么?"
docs = retriever.invoke(query)

print(f"查询: {query}")
print(f"返回 {len(docs)} 个文档:")
for i, doc in enumerate(docs):
    print(f"\n  片段 {i+1}: {doc.page_content}")

# 也可以用 stream / batch
print("\n=== batch 检索 ===")
queries = ["Milvus 适合什么场景?", "什么是向量索引?"]
batch_results = retriever.batch(queries)
for q, docs in zip(queries, batch_results):
    print(f"\n查询: {q} -> {len(docs)} 个结果")
```

### 3.6 MMR 检索(多样性)

```python
"""
Day6 示例 5:MMR 检索 - 平衡相关性和多样性
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="vector_db_article",
)

# 普通相似度检索
print("=== 普通相似度检索 ===")
results = vectorstore.similarity_search("向量数据库", k=3)
for i, doc in enumerate(results):
    print(f"  {i+1}. {doc.page_content[:50]}...")

# MMR 检索(平衡多样性)
print("\n=== MMR 检索 ===")
results_mmr = vectorstore.max_marginal_relevance_search(
    "向量数据库",
    k=3,
    fetch_k=10,  # 先获取 10 个候选,再从中选 3 个多样化的
)
for i, doc in enumerate(results_mmr):
    print(f"  {i+1}. {doc.page_content[:50]}...")

# 用 Retriever 方式
print("\n=== MMR Retriever ===")
retriever_mmr = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 10},
)
results = retriever_mmr.invoke("向量数据库")
for i, doc in enumerate(results):
    print(f"  {i+1}. {doc.page_content[:50]}...")
```

### 3.7 完整 RAG 问答链

```python
"""
Day6 示例 6:完整 RAG 问答链(LCEL 实现)
"""
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 初始化组件
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 加载向量库
vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="vector_db_article",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# 格式化函数:把 Document 列表拼成字符串
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# RAG Prompt 模板
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个文档问答助手。请根据以下上下文回答用户问题。
如果上下文中没有相关信息,请说"根据已知信息无法回答",不要编造答案。

上下文:
{context}"""),
    ("human", "{question}"),
])

# 构建 RAG 链
rag_chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | model
    | StrOutputParser()
)

# 测试问答
questions = [
    "Chroma 是什么?有什么特点?",
    "FAISS 适合什么场景?",
    "Milvus 支持哪些索引类型?",
    "今天天气怎么样?",  # 上下文中没有的问题
]

for q in questions:
    print(f"\n问题: {q}")
    answer = rag_chain.invoke(q)
    print(f"回答: {answer}")
```

### 3.8 带来源追踪的 RAG

```python
"""
Day6 示例 7:带来源追踪的 RAG(返回答案和引用的来源)
"""
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

vectorstore = Chroma(
    persist_directory="./chroma_db",
    embedding_function=embeddings,
    collection_name="vector_db_article",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system", "根据以下上下文回答问题。上下文:\n{context}"),
    ("human", "{question}"),
])

# 单独的问答链
qa_chain = prompt | model | StrOutputParser()

# 完整链:同时返回答案和来源文档
def answer_with_sources(input_data):
    question = input_data["question"]
    docs = retriever.invoke(question)
    context = format_docs(docs)
    answer = qa_chain.invoke({"context": context, "question": question})
    return {
        "answer": answer,
        "sources": [doc.page_content for doc in docs],
    }

# 用 RunnableLambda 包装
rag_with_sources = RunnableLambda(answer_with_sources)

# 测试
result = rag_with_sources.invoke({"question": "Chroma 有什么优点?"})

print("=== 答案 ===")
print(result["answer"])
print("\n=== 引用来源 ===")
for i, source in enumerate(result["sources"], 1):
    print(f"  来源 {i}: {source[:60]}...")
```

---

## 四、当日小结

| 要点 | 内容 |
|------|------|
| Vector Store | 存储和检索向量的数据库,Chroma 是入门首选 |
| Chroma 创建 | `Chroma.from_texts()` 或 `Chroma.from_documents()` |
| Chroma 持久化 | `persist_directory` 参数指定磁盘目录 |
| Retriever | VectorStore 的 Runnable 封装,用 `as_retriever()` 转换 |
| 检索方法 | `similarity_search`(相似度)、`max_marginal_relevance_search`(MMR) |
| MMR | 平衡相关性和多样性,避免结果重复 |
| RAG 链结构 | `{"context": retriever, "question": RunnablePassthrough()} | prompt | model | parser` |
| format_docs | 把 Document 列表拼成字符串放入 Prompt |
| 防幻觉 | Prompt 中要求"上下文没有就说不知道",避免编造 |

---

## 五、练习题

### 选择题

**1. 以下哪个向量数据库适合本地开发和原型验证?**
A. Pinecone
B. Chroma
C. Milvus
D. PGVector

**2. `vectorstore.as_retriever(search_kwargs={"k": 3})` 中的 `k=3` 表示?**
A. 检索 3 次
B. 返回最相关的 3 个文档片段
C. 向量维度为 3
D. 切分为 3 个片段

**3. RAG 链中 `RunnablePassthrough()` 的作用是?**
A. 跳过当前步骤
B. 把用户原始问题透传给 Prompt 的 question 字段
C. 删除上下文
D. 格式化文档

**4. MMR(Maximal Marginal Relevance)检索的特点是?**
A. 只选最相似的
B. 平衡相关性和多样性,避免结果重复
C. 随机选择
D. 按时间排序

### 填空题

**5.** 把 `Document` 列表转换成字符串的常用方法是 `"______".join(doc.page_content for doc in docs)`。

**6.** RAG 的 Prompt 中,通常要求 LLM "如果上下文没有答案就说 ______",以防止幻觉。

### 编程题

**7.** 编写一个 RAG 程序:
- 创建 5 条关于"机器学习基础知识"的文本(如监督学习、无监督学习、过拟合等概念)
- 存入 Chroma 向量库
- 构建 RAG 问答链,能回答关于这些概念的问题
- 测试 3 个问题,包括 1 个文档中没有的问题(验证防幻觉)

**8.** 扩展第 7 题,改用 MMR 检索策略(`search_type="mmr"`),对比普通检索和 MMR 检索的结果差异。打印两种策略返回的文档片段。

---

## 六、练习题答案

### 1. 答案:B
**解析**:Chroma 是纯本地、零配置的向量数据库,非常适合开发和原型验证。Pinecone 是云服务,Milvus 需部署服务端,PGVector 需要 PostgreSQL。

### 2. 答案:B
**解析**:`k=3` 表示返回最相关的 3 个文档片段。`k` 是 top-K 检索的参数,控制返回结果数量。

### 3. 答案:B
**解析**:在 RAG 链 `{"context": retriever, "question": RunnablePassthrough()}` 中,`retriever` 用用户问题检索文档,`RunnablePassthrough()` 把原始问题透传给 `question` 字段,这样 Prompt 既能拿到上下文又能拿到问题。

### 4. 答案:B
**解析**:MMR(Maximal Marginal Relevance)在选择结果时,不仅考虑与查询的相似度,还考虑结果之间的差异性,避免返回内容高度重复的片段。

### 5. 答案:`\n\n`(两个换行符)
**解析**:常用 `"\n\n".join(doc.page_content for doc in docs)` 把多个文档片段用空行分隔拼成字符串,这样上下文段落清晰。

### 6. 答案:`"我不知道"`(或"根据已知信息无法回答"等类似表述)
**解析**:在 RAG Prompt 中加入防幻觉指令,要求 LLM 在上下文无相关信息时明确表示不知道,而非编造答案。

### 7. 参考答案:

```python
"""
练习题 7:机器学习知识 RAG
"""
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 5 条机器学习知识
texts = [
    "监督学习是使用标注数据训练模型,让模型学习输入到输出的映射。常见任务包括分类和回归。",
    "无监督学习使用未标注的数据,发现数据中的内在结构。常见方法包括聚类和降维。",
    "过拟合是指模型在训练数据上表现很好,但在新数据上表现差。可以通过正则化、增加数据来缓解。",
    "交叉验证是一种评估模型的方法,将数据分成多份,轮流用作训练集和验证集,提高评估可靠性。",
    "梯度下降是优化模型参数的常用算法,通过沿梯度反方向更新参数来最小化损失函数。",
]

vectorstore = Chroma.from_texts(texts=texts, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

prompt = ChatPromptTemplate.from_messages([
    ("system", "根据以下上下文回答问题。如果上下文没有相关信息,请说'根据已知信息无法回答'。\n\n上下文:\n{context}"),
    ("human", "{question}"),
])

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# 测试 3 个问题(第3个文档中没有)
questions = [
    "什么是监督学习?",
    "过拟合怎么解决?",
    "什么是强化学习?",  # 文档中没有
]

for q in questions:
    print(f"问题: {q}")
    print(f"回答: {rag_chain.invoke(q)}\n")
```

### 8. 参考答案:

```python
"""
练习题 8:对比普通检索和 MMR 检索
"""
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

texts = [
    "监督学习使用标注数据训练模型,任务包括分类和回归。",
    "监督学习的分类任务预测离散标签,回归任务预测连续值。",
    "监督学习需要大量标注数据,数据质量影响模型效果。",
    "无监督学习使用未标注数据,方法包括聚类和降维。",
    "梯度下降通过沿梯度反方向更新参数来最小化损失函数。",
]

vectorstore = Chroma.from_texts(texts=texts, embedding=embeddings)

query = "监督学习是什么?"

# 普通检索
print("=== 普通相似度检索 ===")
results_normal = vectorstore.similarity_search(query, k=3)
for i, doc in enumerate(results_normal):
    print(f"  {i+1}. {doc.page_content}")

# MMR 检索
print("\n=== MMR 检索 ===")
results_mmr = vectorstore.max_marginal_relevance_search(query, k=3, fetch_k=5)
for i, doc in enumerate(results_mmr):
    print(f"  {i+1}. {doc.page_content}")

print("\n分析:普通检索可能返回多条关于'监督学习'的相似片段,")
print("MMR 检索会加入更多样性的结果(如无监督学习或梯度下降)。")
```

---

**恭喜完成 Day 6!** 明天是最后一天,我们将学习 Agent(代理)与 Tools(工具),并完成一个完整的 RAG 项目实战。
