# 第1月第4周：RAG 系统 + Multi-Tool Agent

> 适用对象：已完成 Week 1-3（Python基础 + LLM核心 + Prompt Engineering）的学习者
> 预计时长：每天 2-3 小时，共 7 天
> 学习目标：掌握 RAG 全流程实现、向量数据库实战、多工具 Agent 编排，完成一个完整的知识库问答 Agent

---

## 本周前置准备

```bash
cd ~/agent-learning
mkdir -p month1/week4
cd month1/week4

python -m venv venv
source venv/Scripts/activate  # Windows Git Bash

# 本周依赖
pip install httpx pydantic tiktoken chromadb numpy pypdf
pip freeze > requirements.txt
```

**关于向量数据库**：本周使用 ChromaDB（完全本地运行，无需服务端，零配置，适合学习）。

**关于 PDF 解析**：安装 `pypdf` 用于读取 PDF 文档做 RAG 练习。

---

## Day 1：文档处理与文本切分

> RAG 的第一步是把文档变成可检索的"块"。切分质量直接决定检索质量，检索质量直接决定回答质量。

### 1.1 RAG 全流程概览

```
┌─────────────────── RAG 全流程 ───────────────────┐
│                                                   │
│  离线阶段（索引）：                                 │
│  文档 → 解析 → 切分 → Embedding → 存入向量数据库    │
│                                                   │
│  在线阶段（查询）：                                 │
│  用户问题 → Embedding → 向量检索 → 上下文拼接       │
│         → LLM 生成回答 → 返回用户                   │
│                                                   │
└───────────────────────────────────────────────────┘

本周按天推进：
  Day 1: 文档处理与切分（离线-前半段）
  Day 2: 向量数据库 ChromaDB（离线-后半段）
  Day 3: 检索策略与重排序（在线-前半段）
  Day 4: RAG 生成与评测（在线-后半段）
  Day 5: Multi-Tool Agent 编排
  Day 6: 综合实战 - 知识库问答 Agent
  Day 7: 复习 + 周测
```

### 1.2 支持的文档格式

```python
# === 文本文件 ===
from pathlib import Path

def load_text(file_path: str) -> str:
    """加载纯文本文件"""
    return Path(file_path).read_text(encoding="utf-8")

# === PDF 文件 ===
from pypdf import PdfReader

def load_pdf(file_path: str) -> str:
    """加载 PDF 文件，提取全部文本"""
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(f"[第{i+1}页]\n{text}")
    return "\n\n".join(pages)

# === Markdown 文件 ===
def load_markdown(file_path: str) -> str:
    """加载 Markdown 文件（直接读取，保留格式）"""
    return Path(file_path).read_text(encoding="utf-8")

# === 统一加载器 ===

SUPPORTED_EXTENSIONS = {
    ".txt": load_text,
    ".md": load_markdown,
    ".pdf": load_pdf,
}

def load_document(file_path: str) -> str:
    """根据文件扩展名自动选择加载器"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    ext = path.suffix.lower()
    loader = SUPPORTED_EXTENSIONS.get(ext)
    if not loader:
        raise ValueError(f"不支持的文件格式: {ext}，支持: {list(SUPPORTED_EXTENSIONS.keys())}")

    content = loader(file_path)
    print(f"已加载: {path.name} ({len(content)} 字符)")
    return content

# === 批量加载目录 ===

def load_directory(dir_path: str) -> list[dict]:
    """加载目录下所有支持的文档"""
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"不是目录: {dir_path}")

    documents = []
    for file_path in path.rglob("*"):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                content = load_document(str(file_path))
                documents.append({
                    "source": str(file_path),
                    "filename": file_path.name,
                    "content": content,
                })
            except Exception as e:
                print(f"加载失败 {file_path.name}: {e}")

    print(f"\n共加载 {len(documents)} 个文档")
    return documents
```

### 1.3 文本切分策略

```python
import tiktoken
from typing import Optional
from dataclasses import dataclass, field

@dataclass
class TextChunk:
    """文本块"""
    content: str
    index: int
    token_count: int
    source: str = ""
    metadata: dict = field(default_factory=dict)

class TextSplitter:
    """文本切分器"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, model: str = "gpt-4"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        return self.encoding.decode(tokens[:max_tokens])

    # === 策略1：固定 Token 数切分（最基础） ===

    def split_by_tokens(self, text: str, source: str = "") -> list[TextChunk]:
        """按 Token 数切分，带重叠"""
        tokens = self.encoding.encode(text)
        chunks = []
        start = 0
        idx = 0

        while start < len(tokens):
            end = start + self.chunk_size
            chunk_tokens = tokens[start:end]
            content = self.encoding.decode(chunk_tokens)
            chunks.append(TextChunk(
                content=content,
                index=idx,
                token_count=len(chunk_tokens),
                source=source,
            ))
            start += self.chunk_size - self.chunk_overlap
            idx += 1

        return chunks

    # === 策略2：按段落切分（保留语义完整性） ===

    def split_by_paragraphs(self, text: str, source: str = "") -> list[TextChunk]:
        """按段落切分，短段落合并，长段落再切分"""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current_text = ""
        current_tokens = 0
        idx = 0

        for para in paragraphs:
            para_tokens = self._count_tokens(para)

            # 单个段落就超过限制，需要再切分
            if para_tokens > self.chunk_size:
                # 先把当前积累的写入
                if current_text:
                    chunks.append(TextChunk(
                        content=current_text.strip(),
                        index=idx,
                        token_count=current_tokens,
                        source=source,
                    ))
                    idx += 1
                    current_text = ""
                    current_tokens = 0

                # 对长段落按 token 切分
                sub_chunks = self.split_by_tokens(para, source)
                for sc in sub_chunks:
                    sc.index = idx
                    chunks.append(sc)
                    idx += 1

            # 加入当前块不会超限
            elif current_tokens + para_tokens + 1 <= self.chunk_size:
                current_text += para + "\n\n"
                current_tokens += para_tokens + 1

            # 加入会超限，先写入当前块
            else:
                if current_text:
                    chunks.append(TextChunk(
                        content=current_text.strip(),
                        index=idx,
                        token_count=current_tokens,
                        source=source,
                    ))
                    idx += 1
                current_text = para + "\n\n"
                current_tokens = para_tokens

        # 写入最后一块
        if current_text:
            chunks.append(TextChunk(
                content=current_text.strip(),
                index=idx,
                token_count=current_tokens,
                source=source,
            ))

        return chunks

    # === 策略3：Markdown 按标题切分（最推荐） ===

    def split_by_headers(self, text: str, source: str = "") -> list[TextChunk]:
        """按 Markdown 标题（# ## ###）切分，保持层级结构"""
        import re

        # 按标题分割
        sections = re.split(r'(?=^#{1,6}\s)', text, flags=re.MULTILINE)
        sections = [s.strip() for s in sections if s.strip()]

        chunks = []
        idx = 0

        for section in sections:
            # 提取标题
            header_match = re.match(r'^(#{1,6})\s+(.+)', section)
            header = header_match.group(2) if header_match else ""

            section_tokens = self._count_tokens(section)

            if section_tokens <= self.chunk_size:
                chunks.append(TextChunk(
                    content=section,
                    index=idx,
                    token_count=section_tokens,
                    source=source,
                    metadata={"header": header},
                ))
                idx += 1
            else:
                # 超长章节按段落再切分，但保留标题作为上下文
                header_line = header_match.group(0) + "\n\n" if header_match else ""
                body = section[len(header_match.group(0)):] if header_match else section

                sub_chunks = self.split_by_paragraphs(body, source)
                for sc in sub_chunks:
                    # 在每个子块前面加上标题上下文
                    sc.content = header_line + sc.content
                    sc.token_count = self._count_tokens(sc.content)
                    sc.index = idx
                    sc.metadata = {"header": header}
                    chunks.append(sc)
                    idx += 1

        return chunks

# === 使用示例 ===

sample_markdown = """# Python 异步编程指南

## 什么是异步编程

异步编程是一种并发编程模式，允许程序在等待 I/O 操作时执行其他任务，而不是阻塞等待。Python 通过 async/await 语法提供原生支持。

## 核心概念

### 协程（Coroutine）

协程是异步编程的基本单元。使用 async def 定义的函数就是协程函数，调用它返回一个协程对象。

    async def fetch_data(url):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.json()

### 事件循环（Event Loop）

事件循环是异步编程的引擎，负责调度和执行协程。asyncio.run() 会创建并运行一个事件循环。

### async/await 语法

- `async def` 定义协程函数
- `await` 等待一个异步操作完成
- `asyncio.gather()` 并发运行多个协程

## 实际应用

### HTTP 请求

异步 HTTP 请求是最常见的应用场景。使用 httpx 的 AsyncClient 可以实现高并发请求。

### 文件操作

使用 aiofiles 库进行异步文件读写，避免阻塞事件循环。

### 数据库操作

大多数现代数据库驱动都支持异步接口，如 asyncpg、motor 等。
"""

splitter = TextSplitter(chunk_size=200, chunk_overlap=30)

print("=== 按 Token 切分 ===")
for chunk in splitter.split_by_tokens(sample_markdown, "async_guide.md"):
    print(f"  块{chunk.index}: {chunk.token_count} tokens | {chunk.content[:60]}...")

print("\n=== 按段落切分 ===")
for chunk in splitter.split_by_paragraphs(sample_markdown, "async_guide.md"):
    print(f"  块{chunk.index}: {chunk.token_count} tokens | {chunk.content[:60]}...")

print("\n=== 按标题切分 ===")
for chunk in splitter.split_by_headers(sample_markdown, "async_guide.md"):
    header = chunk.metadata.get("header", "")
    print(f"  块{chunk.index}: {chunk.token_count} tokens | [{header}] {chunk.content[:50]}...")
```

### 1.4 切分策略选择指南

```
┌─────────────────────────────────────────────────────┐
│            切分策略选择                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│  纯文本/无结构   → split_by_tokens（基础兜底）        │
│  有段落结构      → split_by_paragraphs               │
│  Markdown/文档   → split_by_headers（推荐）           │
│  代码文件        → 按函数/类切分（自定义）             │
│                                                     │
│  通用建议：                                         │
│  - chunk_size: 300-500 tokens（检索粒度适中）         │
│  - chunk_overlap: 10-20% 的 chunk_size              │
│  - 太大：检索不精确，噪声多                           │
│  - 太小：上下文不完整，语义断裂                       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 1.5 今日练习

1. 写一个函数 `split_python_code(source: str)` —— 按 `def` / `class` 切分 Python 代码，每个函数/类是一个块
2. 加载一个真实的 PDF 文件（可以用你自己的技术文档），对比三种切分策略的效果
3. 写一个"切分质量评估器"：统计每个块的 Token 数分布（最大/最小/平均/标准差），判断切分是否均匀

<details>
<summary>参考答案（Python 代码切分器）</summary>

```python
import re

def split_python_code(source: str, chunk_size: int = 500) -> list[TextChunk]:
    """按函数/类切分 Python 代码"""
    # 按顶层 def/class 分割
    pattern = r'(?=^(?:class |def |async def ))'
    parts = re.split(pattern, source, flags=re.MULTILINE)
    parts = [p.strip() for p in parts if p.strip()]

    # 分离非函数/类的顶层代码（import、全局变量等）
    encoding = tiktoken.get_encoding("cl100k_base")

    chunks = []
    idx = 0

    for part in parts:
        tokens = len(encoding.encode(part))
        # 提取名称
        name_match = re.match(r'(?:async )?(?:class |def )(\w+)', part)
        name = name_match.group(1) if name_match else "module_level"

        if tokens <= chunk_size:
            chunks.append(TextChunk(
                content=part,
                index=idx,
                token_count=tokens,
                metadata={"type": "function" if part.startswith(("def", "async def")) else "class", "name": name},
            ))
            idx += 1
        else:
            # 超长函数，按 token 切分
            splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=50)
            sub = splitter.split_by_tokens(part)
            for s in sub:
                s.index = idx
                s.metadata = {"type": "function_part", "name": name}
                chunks.append(s)
                idx += 1

    return chunks
```

</details>

---

## Day 2：向量数据库 ChromaDB

> 向量数据库是 RAG 的存储层。今天用 ChromaDB 实现文档的 Embedding 索引和检索。

### 2.1 ChromaDB 基础

```python
import chromadb

# === 创建客户端（纯本地，数据存在内存或磁盘） ===

# 内存模式（重启丢失，适合测试）
client = chromadb.Client()

# 持久化模式（数据保存到磁盘）
# client = chromadb.PersistentClient(path="~/agent-learning/week4/chroma_db")

# === 创建/获取 Collection（类似数据库的"表"） ===

collection = client.get_or_create_collection(
    name="knowledge_base",
    metadata={"description": "技术文档知识库"}
)

print(f"集合: {collection.name}")
print(f"文档数: {collection.count()}")

# === 基本操作 ===

# 添加文档（自动生成 Embedding，ChromaDB 内置了默认 Embedding 模型）
collection.add(
    documents=[
        "Python 是一种解释型编程语言",
        "JavaScript 是运行在浏览器中的脚本语言",
        "Vue 是一个渐进式前端框架",
    ],
    ids=["doc1", "doc2", "doc3"],
    metadatas=[
        {"source": "python_intro.md", "category": "编程语言"},
        {"source": "js_intro.md", "category": "编程语言"},
        {"source": "vue_intro.md", "category": "前端框架"},
    ],
)

# 查询（语义搜索）
results = collection.query(
    query_texts=["前端开发用什么语言"],
    n_results=2,
)
print("查询结果:")
for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
    print(f"  [{dist:.4f}] {doc} ({meta})")

# 按 ID 获取
doc = collection.get(ids=["doc1"])
print(f"\n获取 doc1: {doc['documents'][0]}")

# 删除
# collection.delete(ids=["doc3"])
```

### 2.2 使用自定义 Embedding 函数

```python
# ChromaDB 默认使用 sentence-transformers 的 all-MiniLM-L6-v2
# 如果想用智谱/其他 API 的 Embedding，需要自定义

import httpx
import asyncio
import numpy as np
from chromadb.api.types import EmbeddingFunction

class ZhipuEmbeddingFunction(EmbeddingFunction):
    """智谱 Embedding 适配器"""

    def __init__(self, api_key: str, model: str = "embedding-3"):
        self.api_key = api_key
        self.model = model

    def __call__(self, input: list[str]) -> list[list[float]]:
        """ChromaDB 调用此方法获取 Embedding"""
        # ChromaDB 的 EmbeddingFunction 是同步接口
        # 用 asyncio.run 在同步方法中运行异步代码
        return asyncio.run(self._get_embeddings(input))

    async def _get_embeddings(self, texts: list[str]) -> list[list[float]]:
        url = "https://open.bigmodel.cn/api/paas/v4/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # 分批处理（API 通常有批量限制）
        batch_size = 10
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            payload = {"model": self.model, "input": batch}

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            for item in data["data"]:
                all_embeddings.append(item["embedding"])

        return all_embeddings

# 使用自定义 Embedding
# embedding_fn = ZhipuEmbeddingFunction(api_key="your-key")
# collection = client.get_or_create_collection(
#     name="knowledge_base",
#     embedding_function=embedding_fn,
# )
```

### 2.3 批量索引文档

```python
from typing import Optional
import uuid

class DocumentIndexer:
    """文档索引器：将切分后的文档块批量写入 ChromaDB"""

    def __init__(
        self,
        collection: chromadb.Collection,
        batch_size: int = 100,
    ):
        self.collection = collection
        self.batch_size = batch_size

    def index_chunks(self, chunks: list[TextChunk]) -> int:
        """
        批量索引文本块
        返回成功索引的数量
        """
        total_indexed = 0

        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i+self.batch_size]

            documents = [chunk.content for chunk in batch]
            ids = [str(uuid.uuid4()) for _ in batch]
            metadatas = [
                {
                    "source": chunk.source,
                    "chunk_index": chunk.index,
                    "token_count": chunk.token_count,
                    **chunk.metadata,
                }
                for chunk in batch
            ]

            try:
                self.collection.add(
                    documents=documents,
                    ids=ids,
                    metadatas=metadatas,
                )
                total_indexed += len(batch)
                print(f"  已索引 {total_indexed}/{len(chunks)} 块")
            except Exception as e:
                print(f"  索引批次 {i} 失败: {e}")

        return total_indexed

    def index_documents(self, documents: list[dict], splitter: TextSplitter) -> int:
        """
        完整流程：加载文档 → 切分 → 索引
        documents: [{"source": "path", "content": "...", "filename": "..."}]
        """
        all_chunks = []
        for doc in documents:
            # 根据文件类型选择切分策略
            ext = Path(doc["source"]).suffix.lower()
            if ext == ".md":
                chunks = splitter.split_by_headers(doc["content"], doc["filename"])
            else:
                chunks = splitter.split_by_paragraphs(doc["content"], doc["filename"])
            all_chunks.extend(chunks)

        print(f"共切分为 {len(all_chunks)} 个文本块")
        return self.index_chunks(all_chunks)


# === 使用示例 ===

async def build_knowledge_base(api_key: str, docs_dir: str):
    """构建知识库的完整流程"""

    # 1. 加载文档
    documents = load_directory(docs_dir)
    if not documents:
        print("没有找到可索引的文档")
        return None

    # 2. 创建 Collection
    embedding_fn = ZhipuEmbeddingFunction(api_key)
    client = chromadb.Client()
    collection = client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=embedding_fn,
    )

    # 3. 切分并索引
    splitter = TextSplitter(chunk_size=400, chunk_overlap=50)
    indexer = DocumentIndexer(collection)
    count = indexer.index_documents(documents, splitter)
    print(f"\n知识库构建完成，共索引 {count} 个文本块")

    return collection

# collection = await build_knowledge_base("your-api-key", "~/agent-learning/week4/docs")
```

### 2.4 基本检索

```python
class DocumentRetriever:
    """文档检索器"""

    def __init__(self, collection: chromadb.Collection):
        self.collection = collection

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        """
        语义搜索
        where: 元数据过滤，如 {"category": "编程语言"}
        where_document: 文档内容过滤，如 {"$contains": "Python"}
        """
        query_params = {
            "query_texts": [query],
            "n_results": top_k,
        }
        if where:
            query_params["where"] = where
        if where_document:
            query_params["where_document"] = where_document

        results = self.collection.query(**query_params)

        # 整理结果
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        return items

    def search_by_embedding(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """用预计算的 Embedding 搜索（节省重复计算）"""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return items

    def format_context(self, results: list[dict], max_tokens: int = 3000) -> str:
        """将检索结果格式化为 LLM 上下文"""
        encoding = tiktoken.get_encoding("cl100k_base")
        context_parts = []
        total_tokens = 0

        for i, item in enumerate(results, 1):
            source = item["metadata"].get("source", "未知来源")
            header = item["metadata"].get("header", "")
            content = item["content"]

            part = f"[文档{i}] (来源: {source}"
            if header:
                part += f", 章节: {header}"
            part += f")\n{content}\n"

            part_tokens = len(encoding.encode(part))
            if total_tokens + part_tokens > max_tokens:
                # 截断最后一块
                remaining = max_tokens - total_tokens
                if remaining > 50:
                    tokens = encoding.encode(content)[:remaining]
                    truncated = encoding.decode(tokens)
                    part = f"[文档{i}] (来源: {source})\n{truncated}...[已截断]\n"
                    context_parts.append(part)
                break

            context_parts.append(part)
            total_tokens += part_tokens

        return "\n".join(context_parts)

# === 使用示例 ===

# retriever = DocumentRetriever(collection)
# results = retriever.search("Python 异步编程怎么用？", top_k=3)
# for r in results:
#     print(f"  距离: {r['distance']:.4f} | 来源: {r['metadata'].get('source', '')} | {r['content'][:60]}...")
# context = retriever.format_context(results)
# print(context)
```

### 2.5 今日练习

1. 创建一个包含至少 5 个技术文档的知识库（可以自己写几个小 .md 文件），用 ChromaDB 索引
2. 实现"增量索引"：如果文档已存在则更新，不存在则新增（用文件路径作为唯一标识）
3. 测试 ChromaDB 的元数据过滤：按文件名、分类等条件过滤检索结果

<details>
<summary>参考答案（增量索引）</summary>

```python
import hashlib

class IncrementalIndexer:
    """增量索引器：已存在的文档更新，不存在的新增"""

    def __init__(self, collection: chromadb.Collection, splitter: TextSplitter):
        self.collection = collection
        self.splitter = splitter

    def _get_doc_hash(self, content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def index_document(self, document: dict) -> int:
        """索引单个文档，如果已存在则先删除旧版本再重新索引"""
        source = document["source"]
        content = document["content"]
        filename = document.get("filename", Path(source).name)

        # 查找已有的该文档的块
        existing = self.collection.get(
            where={"source": filename}
        )

        if existing["ids"]:
            # 删除旧版本
            self.collection.delete(ids=existing["ids"])
            print(f"  更新文档: {filename} (删除 {len(existing['ids'])} 个旧块)")

        # 切分并索引
        ext = Path(source).suffix.lower()
        if ext == ".md":
            chunks = self.splitter.split_by_headers(content, filename)
        else:
            chunks = self.splitter.split_by_paragraphs(content, filename)

        if not chunks:
            return 0

        # 为每个块生成确定性 ID（基于来源+索引）
        ids = [f"{self._get_doc_hash(source)}_{i}" for i in range(len(chunks))]
        documents = [c.content for c in chunks]
        metadatas = [
            {
                "source": filename,
                "chunk_index": c.index,
                "token_count": c.token_count,
                "content_hash": self._get_doc_hash(c.content),
                **c.metadata,
            }
            for c in chunks
        ]

        self.collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"  索引文档: {filename} ({len(chunks)} 个块)")
        return len(chunks)
```

</details>

---

## Day 3：检索策略与重排序

> 基础的向量检索经常不够好——可能检索到语义相关但无用的块，或者遗漏真正关键的块。今天的策略能显著提升检索质量。

### 3.1 检索问题分析

```
基础向量检索的常见问题：

1. 语义漂移：查询"Python性能优化"→ 检索到"Java性能优化"（语义相似但不对）
2. 关键词缺失：查询"asyncio.gather"→ 检索到"asyncio.run"（概念相关但不够精确）
3. 顺序错误：最相关的块排第3，前2个不够相关
4. 上下文断裂：检索到的块缺少前后文，LLM 无法理解
5. 信息冗余：多个块内容重复，浪费上下文空间
```

### 3.2 多路召回 + 融合

```python
class HybridRetriever:
    """混合检索器：向量检索 + 关键词检索 + 融合"""

    def __init__(self, collection: chromadb.Collection):
        self.collection = collection

    def vector_search(self, query: str, top_k: int = 10) -> list[dict]:
        """向量语义检索"""
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "content": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # 距离转相似度
                "source": "vector",
            })
        return items

    def keyword_search(self, query: str, top_k: int = 10) -> list[dict]:
        """关键词检索（ChromaDB 的 where_document）"""
        # 提取关键词
        keywords = [w for w in query.split() if len(w) > 1][:3]

        items = []
        for keyword in keywords:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where_document={"$contains": keyword},
                )
                for i in range(len(results["ids"][0])):
                    items.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": 1 - results["distances"][0][i],
                        "source": f"keyword:{keyword}",
                    })
            except Exception:
                pass

        return items

    def reciprocal_rank_fusion(
        self,
        result_lists: list[list[dict]],
        k: int = 60,
    ) -> list[dict]:
        """
        倒数排名融合（RRF）
        多路检索结果的合并策略，不依赖分数的绝对值，只依赖排名
        """
        rrf_scores: dict[str, float] = {}
        doc_map: dict[str, dict] = {}

        for results in result_lists:
            for rank, item in enumerate(results):
                doc_id = item["id"]
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0
                    doc_map[doc_id] = item
                rrf_scores[doc_id] += 1 / (k + rank + 1)

        # 按 RRF 分数排序
        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)

        fused = []
        for doc_id in sorted_ids:
            item = doc_map[doc_id].copy()
            item["rrf_score"] = rrf_scores[doc_id]
            item["source"] = "fusion"
            fused.append(item)

        return fused

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """混合检索：向量 + 关键词 → RRF 融合"""
        vector_results = self.vector_search(query, top_k=top_k * 2)
        keyword_results = self.keyword_search(query, top_k=top_k * 2)

        fused = self.reciprocal_rank_fusion([vector_results, keyword_results])
        return fused[:top_k]
```

### 3.3 查询改写

```python
class QueryRewriter:
    """查询改写器：优化用户的原始查询以提升检索效果"""

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model

    async def rewrite(self, query: str) -> str:
        """改写查询，使其更适合检索"""
        prompt = f"""请将以下用户问题改写为更适合在知识库中检索的查询。
要求：
1. 提取核心概念和关键词
2. 去除口语化表达
3. 补充隐含的技术术语
4. 只输出改写后的查询，不要解释

原问题：{query}
改写后："""

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 200,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            rewritten = resp.json()["choices"][0]["message"]["content"].strip()

        return rewritten

    async def expand(self, query: str, num_variants: int = 3) -> list[str]:
        """生成多个查询变体，增加召回率"""
        prompt = f"""请为以下问题生成 {num_variants} 个不同角度的查询，用于在技术文档中检索相关信息。
每个查询一行，不要编号。

原问题：{query}
"""

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 300,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        variants = [line.strip() for line in content.split("\n") if line.strip()]
        return [query] + variants[:num_variants]  # 原始查询 + 变体


# 使用示例
# rewriter = QueryRewriter("your-api-key")
# rewritten = await rewriter.rewrite("Python怎么处理大文件")
# → "Python 大文件读取 流式处理 逐行读取 内存优化"
#
# variants = await rewriter.expand("Python异步编程")
# → ["Python async await 协程", "Python asyncio 事件循环", "Python 异步IO 并发"]
```

### 3.4 上下文窗口扩展

```python
class ContextExpander:
    """上下文扩展：检索到块后，将其前后的块也加入上下文"""

    def __init__(self, collection: chromadb.Collection):
        self.collection = collection

    def expand_with_neighbors(
        self,
        results: list[dict],
        before: int = 1,
        after: int = 1,
    ) -> list[dict]:
        """
        对于每个检索结果，获取其前后相邻的块
        before: 前面取几块
        after: 后面取几块
        """
        expanded_ids = set()
        expanded_items = {}

        for item in results:
            source = item["metadata"].get("source", "")
            chunk_idx = item["metadata"].get("chunk_index", 0)

            # 获取同一文档的所有块
            try:
                same_doc = self.collection.get(
                    where={"source": source}
                )
            except Exception:
                continue

            # 建立 chunk_index → id 的映射
            idx_map = {}
            for i, meta in enumerate(same_doc["metadatas"]):
                ci = meta.get("chunk_index", 0)
                idx_map[ci] = {
                    "id": same_doc["ids"][i],
                    "content": same_doc["documents"][i],
                    "metadata": meta,
                }

            # 收集相邻块
            for offset in range(-before, after + 1):
                neighbor_idx = chunk_idx + offset
                if neighbor_idx in idx_map:
                    neighbor = idx_map[neighbor_idx]
                    nid = neighbor["id"]
                    if nid not in expanded_ids:
                        expanded_ids.add(nid)
                        neighbor["is_primary"] = (offset == 0)
                        neighbor["distance"] = item.get("distance", 0) if offset == 0 else None
                        expanded_items[nid] = neighbor

        # 排序：先按来源分组，再按 chunk_index
        result_list = list(expanded_items.values())
        result_list.sort(key=lambda x: (
            x["metadata"].get("source", ""),
            x["metadata"].get("chunk_index", 0)
        ))

        return result_list
```

### 3.5 今日练习

1. 实现完整的混合检索流程：查询改写 → 多路召回 → RRF 融合 → 上下文扩展
2. 对比"纯向量检索"和"混合检索"在你知识库上的效果差异（至少 5 个查询）
3. 实现"自动查询分类"：判断用户查询适合向量检索还是关键词检索

<details>
<summary>参考答案（完整检索流程）</summary>

```python
class AdvancedRetriever:
    """高级检索器：整合所有策略"""

    def __init__(
        self,
        collection: chromadb.Collection,
        api_key: str,
        model: str = "glm-4-flash",
    ):
        self.hybrid = HybridRetriever(collection)
        self.rewriter = QueryRewriter(api_key, model)
        self.expander = ContextExpander(collection)

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        rewrite: bool = True,
        expand: bool = True,
        expand_before: int = 1,
        expand_after: int = 1,
    ) -> list[dict]:
        """完整检索流程"""

        # 1. 查询改写
        if rewrite:
            rewritten = await self.rewriter.rewrite(query)
            print(f"  查询改写: {query} → {rewritten}")
            search_query = rewritten
        else:
            search_query = query

        # 2. 混合检索
        results = self.hybrid.search(search_query, top_k=top_k * 2)

        # 3. 上下文扩展
        if expand:
            results = self.expander.expand_with_neighbors(
                results[:top_k],
                before=expand_before,
                after=expand_after,
            )
        else:
            results = results[:top_k]

        return results

    def format_for_llm(self, results: list[dict], max_tokens: int = 3000) -> str:
        """格式化为 LLM 可用的上下文"""
        encoding = tiktoken.get_encoding("cl100k_base")
        parts = []
        total_tokens = 0

        for i, item in enumerate(results, 1):
            source = item["metadata"].get("source", "未知")
            idx = item["metadata"].get("chunk_index", "")
            is_primary = item.get("is_primary", True)

            prefix = "★" if is_primary else "·"  # 标记主要结果
            part = f"{prefix} [文档{i}] (来源: {source}, 块{idx})\n{item['content']}\n\n"

            tokens = len(encoding.encode(part))
            if total_tokens + tokens > max_tokens:
                break

            parts.append(part)
            total_tokens += tokens

        return "".join(parts)
```

</details>

---

## Day 4：RAG 生成与评测

> 检索到内容后，如何让 LLM 基于检索结果生成高质量回答？如何衡量 RAG 系统的效果？

### 4.1 RAG 生成提示词设计

```python
RAG_SYSTEM_PROMPT = """你是一个知识库问答助手。请严格根据提供的文档内容回答用户问题。

**核心规则**
1. 只根据提供的文档内容回答，不要使用外部知识
2. 如果文档中没有相关信息，明确回答"根据现有文档无法回答该问题"
3. 如果文档信息不完整，说明已有信息并指出缺失部分
4. 引用文档内容时标注来源
5. 不要编造文档中不存在的信息

**输出格式**
**回答**
[基于文档的回答]

**来源**
- [文档编号]: [引用的关键片段]

**可靠性**
- 高/中/低（文档内容与问题的相关程度）"""

RAG_USER_TEMPLATE = """**检索到的文档内容**

{context}

**用户问题**
{question}

请根据以上文档内容回答问题。"""


class RAGGenerator:
    """RAG 生成器"""

    def __init__(self, api_key: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model

    async def generate(
        self,
        question: str,
        context: str,
        temperature: float = 0.3,
        stream: bool = True,
    ) -> str:
        """基于检索上下文生成回答"""
        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": RAG_USER_TEMPLATE.format(
                context=context, question=question
            )},
        ]

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 2048,
            "stream": stream,
        }

        full_content = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            if stream:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0].get("delta", {}).get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                                    full_content += content
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                print()
            else:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                full_content = resp.json()["choices"][0]["message"]["content"]

        return full_content
```

### 4.2 RAG 评测指标

```
RAG 评测的三个维度：

1. 检索质量（Retrieval Quality）
   - 召回率 (Recall)：相关文档被检索到的比例
   - 精确率 (Precision)：检索结果中相关文档的比例
   - MRR：第一个相关文档的平均排名倒数

2. 生成质量（Generation Quality）
   - 忠实度 (Faithfulness)：回答是否忠于检索到的文档（不编造）
   - 答案相关性 (Answer Relevance)：回答是否针对问题
   - 完整性 (Completeness)：回答是否覆盖了文档中的关键信息

3. 端到端质量
   - 准确性：回答是否事实正确
   - 用户满意度：主观评价
```

### 4.3 简易 RAG 评测实现

```python
from pydantic import BaseModel, Field

class RAGEvaluation(BaseModel):
    """RAG 回答评测结果"""
    question: str
    answer: str
    faithfulness: float = Field(ge=0, le=1, description="忠实度：回答是否忠于文档")
    answer_relevance: float = Field(ge=0, le=1, description="答案相关性")
    context_relevance: float = Field(ge=0, le=1, description="上下文相关性：检索到的文档是否相关")
    overall_score: float = Field(ge=0, le=1, description="综合评分")

class RAGEvaluator:
    """RAG 评测器（基于 LLM-as-Judge）"""

    def __init__(self, api_key: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model

    async def evaluate(
        self,
        question: str,
        answer: str,
        context: str,
    ) -> RAGEvaluation:
        """评测单条 RAG 回答"""

        eval_prompt = f"""请评测以下 RAG 系统的回答质量。

**问题**
{question}

**检索到的文档**
{context}

**系统回答**
{answer}

请从以下维度评分（0-1），并以JSON格式返回：
{{
  "faithfulness": "回答是否完全基于文档内容，不编造信息。1=完全忠于文档，0=大量编造",
  "answer_relevance": "回答是否针对了问题。1=完全切题，0=完全跑题",
  "context_relevance": "检索到的文档是否与问题相关。1=高度相关，0=完全无关",
  "overall_score": "综合评分"
}}

只返回JSON，不要解释。"""

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": eval_prompt}],
            "temperature": 0,
            "max_tokens": 300,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        import re
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            data = json.loads(match.group())
            return RAGEvaluation(
                question=question,
                answer=answer,
                faithfulness=float(data.get("faithfulness", 0)),
                answer_relevance=float(data.get("answer_relevance", 0)),
                context_relevance=float(data.get("context_relevance", 0)),
                overall_score=float(data.get("overall_score", 0)),
            )

        return RAGEvaluation(
            question=question, answer=answer,
            faithfulness=0, answer_relevance=0,
            context_relevance=0, overall_score=0,
        )

    async def evaluate_batch(
        self,
        qa_pairs: list[dict],
        rag_pipeline,  # 完整 RAG 流程
    ) -> list[RAGEvaluation]:
        """批量评测"""
        results = []
        for qa in qa_pairs:
            question = qa["question"]
            # 运行 RAG 流程获取回答和上下文
            rag_result = await rag_pipeline.query(question)
            answer = rag_result["answer"]
            context = rag_result["context"]

            evaluation = await self.evaluate(question, answer, context)
            results.append(evaluation)

            print(f"Q: {question}")
            print(f"  忠实度: {evaluation.faithfulness:.2f} | "
                  f"相关性: {evaluation.answer_relevance:.2f} | "
                  f"上下文: {evaluation.context_relevance:.2f} | "
                  f"综合: {evaluation.overall_score:.2f}")

        # 汇总
        avg_faith = sum(r.faithfulness for r in results) / len(results)
        avg_rel = sum(r.answer_relevance for r in results) / len(results)
        avg_ctx = sum(r.context_relevance for r in results) / len(results)
        avg_overall = sum(r.overall_score for r in results) / len(results)

        print(f"\n平均指标: 忠实度={avg_faith:.2f}, 相关性={avg_rel:.2f}, "
              f"上下文={avg_ctx:.2f}, 综合={avg_overall:.2f}")

        return results
```

### 4.4 今日练习

1. 用你自己的知识库构建至少 5 个"问题-预期答案"对，运行 RAG 流程并评测
2. 对比不同参数对评测分数的影响：
   - chunk_size: 200 vs 500 vs 800
   - top_k: 3 vs 5 vs 10
   - temperature: 0 vs 0.3 vs 0.7
3. 改进 RAG 提示词，观察评测分数变化

---

## Day 5：Multi-Tool Agent 编排

> 真正的 Agent 不只是 RAG，它需要根据用户意图选择不同工具，编排复杂的工作流。

### 5.1 Agent 编排模式

```
┌─────────────────────────────────────────────────────┐
│         Agent 编排模式                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  模式1：单工具路由                                    │
│  用户 → LLM 判断意图 → 选择1个工具 → 执行 → 回答     │
│  适合：工具功能互斥，一次只用一个                       │
│                                                     │
│  模式2：顺序链                                       │
│  用户 → 工具A → 工具B → 工具C → 回答                  │
│  适合：有固定流程（如：搜索→提取→生成）                 │
│                                                     │
│  模式3：并行执行                                     │
│  用户 → 同时调用工具A + 工具B → 合并结果 → 回答       │
│  适合：工具间无依赖（如：同时查天气+查日程）            │
│                                                     │
│  模式4：ReAct 循环                                   │
│  用户 → LLM思考 → 选工具 → 执行 → 观察 → 继续思考    │
│       → 选工具 → 执行 → 观察 → 最终回答               │
│  适合：不确定需要几步的复杂任务                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 5.2 工具路由器

```python
from enum import Enum
from pydantic import BaseModel

class ToolCategory(str, Enum):
    RAG = "rag"
    WEATHER = "weather"
    CALCULATOR = "calculator"
    SEARCH = "search"
    GENERAL = "general"

class RoutingResult(BaseModel):
    category: ToolCategory
    confidence: float = Field(ge=0, le=1)
    reasoning: str
    rewritten_query: str = ""

ROUTING_PROMPT = """你是一个查询路由器。根据用户输入，判断应该使用哪种工具来处理。

**可用工具**
- rag: 知识库问答（基于已索引的文档回答问题）
- weather: 天气查询（获取城市天气信息）
- calculator: 数学计算（计算数学表达式）
- search: 网络搜索（搜索最新信息）
- general: 通用对话（不需要工具，直接回答）

**判断规则**
1. 如果问题是关于知识库文档的内容 → rag
2. 如果问天气/气温/是否下雨 → weather
3. 如果是明确的数学计算 → calculator
4. 如果需要最新信息（新闻、实时数据） → search
5. 闲聊/打招呼/常识问题 → general

同时，将用户输入改写为最适合所选工具的查询。

**输出格式（JSON）**
{
  "category": "工具类别",
  "confidence": 0.9,
  "reasoning": "判断理由",
  "rewritten_query": "改写后的查询"
}

用户输入：{user_input}"""


class ToolRouter:
    """工具路由器"""

    def __init__(self, api_key: str, model: str = "glm-4-flash"):
        self.api_key = api_key
        self.model = model

    async def route(self, user_input: str) -> RoutingResult:
        """路由用户输入到合适的工具"""
        prompt = ROUTING_PROMPT.format(user_input=user_input)

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 300,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

        import re
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            data = json.loads(match.group())
            return RoutingResult(
                category=ToolCategory(data.get("category", "general")),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", ""),
                rewritten_query=data.get("rewritten_query", user_input),
            )

        return RoutingResult(
            category=ToolCategory.GENERAL,
            confidence=0.5,
            reasoning="解析失败，回退到通用对话",
            rewritten_query=user_input,
        )
```

### 5.3 Multi-Tool Agent 实现

```python
class MultiToolAgent:
    """多工具 Agent：路由 + RAG + 工具调用 + 通用对话"""

    def __init__(
        self,
        api_key: str,
        collection: chromadb.Collection,
        model: str = "glm-4",
    ):
        self.api_key = api_key
        self.model = model
        self.messages: list[dict] = []
        self.router = ToolRouter(api_key, model)
        self.rag_retriever = AdvancedRetriever(collection, api_key, model)
        self.rag_generator = RAGGenerator(api_key, model)
        self.conversation_history: list[dict] = []

        # 注册非 RAG 工具
        self.tools = {
            "get_weather": {
                "handler": self._get_weather,
                "description": "获取城市天气",
            },
            "calculate": {
                "handler": self._calculate,
                "description": "计算数学表达式",
            },
        }

    def _get_weather(self, city: str, **kwargs) -> str:
        mock = {
            "北京": "晴，25°C，湿度40%，北风3级",
            "上海": "多云，28°C，湿度65%，东南风2级",
            "武汉": "小雨，30°C，湿度75%，南风2级",
        }
        return mock.get(city, f"{city}：晴，22°C")

    def _calculate(self, expression: str, **kwargs) -> str:
        import re
        if not re.match(r'^[\d\s\+\-\*/\.\(\)]+$', expression):
            return "错误：不安全的表达式"
        try:
            return f"计算结果: {eval(expression)}"
        except Exception as e:
            return f"计算错误: {e}"

    async def run(self, user_input: str) -> str:
        """运行 Agent"""
        # 1. 路由
        routing = await self.router.route(user_input)
        print(f"  [路由] {routing.category.value} (置信度: {routing.confidence:.2f}) - {routing.reasoning}")

        query = routing.rewritten_query or user_input

        # 2. 根据路由执行
        if routing.category == ToolCategory.RAG:
            return await self._handle_rag(query, user_input)
        elif routing.category == ToolCategory.WEATHER:
            return await self._handle_tool("get_weather", {"city": query}, user_input)
        elif routing.category == ToolCategory.CALCULATOR:
            return await self._handle_tool("calculate", {"expression": query}, user_input)
        else:
            return await self._handle_general(user_input)

    async def _handle_rag(self, query: str, original_input: str) -> str:
        """处理 RAG 查询"""
        # 检索
        results = await self.rag_retriever.retrieve(query, top_k=3, rewrite=False)
        context = self.rag_retriever.format_for_llm(results)

        if not context.strip():
            return "抱歉，知识库中没有找到与您问题相关的文档。"

        # 生成
        answer = await self.rag_generator.generate(original_input, context)

        # 记录历史
        self.conversation_history.append({"role": "user", "content": original_input})
        self.conversation_history.append({"role": "assistant", "content": answer})

        return answer

    async def _handle_tool(self, tool_name: str, params: dict, original_input: str) -> str:
        """处理工具调用"""
        tool = self.tools.get(tool_name)
        if not tool:
            return f"工具 {tool_name} 不可用"

        result = tool["handler"](**params)
        print(f"  [工具结果] {result}")

        # 让 LLM 基于工具结果组织回答
        prompt = f"""用户问题：{original_input}
工具返回结果：{result}
请基于工具结果，用自然语言回答用户问题。"""

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 512,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            answer = resp.json()["choices"][0]["message"]["content"]

        self.conversation_history.append({"role": "user", "content": original_input})
        self.conversation_history.append({"role": "assistant", "content": answer})
        return answer

    async def _handle_general(self, user_input: str) -> str:
        """处理通用对话"""
        self.messages.append({"role": "user", "content": user_input})

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content": "你是一个友善的AI助手。"},
                *self.messages[-10:],  # 保留最近10条
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": True,
        }

        full_content = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content:
                                print(content, end="", flush=True)
                                full_content += content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        print()

        self.messages.append({"role": "assistant", "content": full_content})
        return full_content
```

### 5.4 今日练习

1. 给 `MultiToolAgent` 添加"日程管理"工具（添加日程/查询日程），测试路由是否能正确区分"查天气"和"查日程"
2. 实现并行工具调用：当用户问"北京和上海哪个更热"时，同时调用两次天气 API
3. 给路由器添加"兜底策略"：当置信度低于 0.5 时，列出可能的工具让用户选择

<details>
<summary>参考答案（并行工具调用）</summary>

```python
class MultiToolAgentV2(MultiToolAgent):
    """支持并行工具调用的 Agent"""

    async def run(self, user_input: str) -> str:
        routing = await self.router.route(user_input)

        # 检测是否需要多次调用同一工具
        if routing.category == ToolCategory.WEATHER:
            # 尝试提取多个城市
            cities = self._extract_cities(user_input)
            if len(cities) > 1:
                return await self._handle_parallel_weather(cities, user_input)

        # 其他情况走原有逻辑
        return await super().run(user_input)

    def _extract_cities(self, text: str) -> list[str]:
        """从文本中提取城市名"""
        city_list = ["北京", "上海", "武汉", "深圳", "广州", "杭州", "成都"]
        found = [c for c in city_list if c in text]
        return found if found else ["未知城市"]

    async def _handle_parallel_weather(self, cities: list[str], original_input: str) -> str:
        """并行查询多个城市天气"""
        import asyncio

        tasks = []
        for city in cities:
            tasks.append(asyncio.to_thread(self._get_weather, city=city))

        results = await asyncio.gather(*tasks)
        print(f"  [并行工具] 查询了 {len(cities)} 个城市")

        # 让 LLM 对比
        weather_info = "\n".join(f"- {city}: {result}" for city, result in zip(cities, results))
        prompt = f"""用户问题：{original_input}

各城市天气：
{weather_info}

请基于以上信息回答用户问题，进行对比分析。"""

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 512,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
```

</details>

---

## Day 6：综合实战 —— 知识库问答 Agent

> 把 Day 1-5 的所有组件整合为一个完整的、可运行的知识库问答 Agent。

### 项目目标

```
$ python kb_agent.py --docs ./docs --api-key your-key

📚 知识库问答 Agent v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
正在构建知识库...
  加载: python_async.md (2340 字符)
  加载: vue3_guide.md (3100 字符)
  加载: rag_intro.md (1800 字符)
  切分为 18 个文本块
  索引完成

可用命令：
  /search <query>  - 搜索知识库
  /stats           - 查看知识库统计
  /evaluate        - 运行评测
  /help            - 帮助
  /quit            - 退出

> Python的asyncio.gather怎么用？
  [路由] rag (置信度: 0.95) - 关于异步编程的知识库查询
  [检索] 找到 3 个相关文档块

Python的asyncio.gather()用于并发运行多个协程。用法如下：
```python
results = await asyncio.gather(
    coroutine1(),
    coroutine2(),
    coroutine3()
)
```

它会同时启动所有协程，等待全部完成后返回结果列表。

来源：python_async.md - asyncio.gather 章节
可靠性：高

> 北京明天天气怎么样
> [路由] weather (置信度: 0.92) - 天气查询
> [工具结果] 晴，25°C，湿度40%，北风3级

北京明天天气晴朗，气温25°C，湿度40%，有北风3级。适合户外活动。

> /quit
> 再见！

```

### 完整实现

创建 `kb_agent.py`：

```python
"""
知识库问答 Agent
完整功能：
1. 文档加载（txt/md/pdf）
2. 智能切分 + ChromaDB 索引
3. 混合检索 + 查询改写
4. 工具路由（RAG/天气/计算/通用对话）
5. RAG 生成 + 来源标注
6. 简易评测
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import httpx
import chromadb
import tiktoken

# 导入 Day 1-5 的组件（假设在同目录下或已模块化）
# 这里为了完整性，把核心类内联

# [此处应包含 Day1-5 的所有类定义]
# 由于篇幅限制，以下只展示主程序逻辑
# 实际使用时请将前面 Day1-5 的类定义复制到此处或作为模块导入

class KnowledgeBaseAgent:
    """知识库问答 Agent 主类"""

    def __init__(self, api_key: str, docs_dir: str, model: str = "glm-4"):
        self.api_key = api_key
        self.model = model
        self.docs_dir = docs_dir
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # 初始化组件
        self._init_components()

    def _init_components(self):
        """初始化所有组件"""
        # 向量数据库
        self.client = chromadb.Client()
        self.embedding_fn = ZhipuEmbeddingFunction(self.api_key)
        self.collection = self.client.get_or_create_collection(
            name="kb_agent",
            embedding_function=self.embedding_fn,
        )

        # 切分器
        self.splitter = TextSplitter(chunk_size=400, chunk_overlap=50)

        # 检索器
        self.retriever = AdvancedRetriever(self.collection, self.api_key)

        # 生成器
        self.generator = RAGGenerator(self.api_key, self.model)

        # 路由器
        self.router = ToolRouter(self.api_key)

        # 评测器
        self.evaluator = RAGEvaluator(self.api_key)

        # 对话历史
        self.conversation_history: list[dict] = []

    async def build_index(self):
        """构建知识库索引"""
        print("正在构建知识库...")

        # 加载文档
        documents = load_directory(self.docs_dir)
        if not documents:
            print("未找到可索引的文档！")
            return

        # 切分
        all_chunks = []
        for doc in documents:
            ext = Path(doc["source"]).suffix.lower()
            if ext == ".md":
                chunks = self.splitter.split_by_headers(doc["content"], doc["filename"])
            else:
                chunks = self.splitter.split_by_paragraphs(doc["content"], doc["filename"])
            all_chunks.extend(chunks)

        print(f"  切分为 {len(all_chunks)} 个文本块")

        # 索引
        indexer = DocumentIndexer(self.collection)
        count = indexer.index_chunks(all_chunks)
        print(f"  索引完成 ({count} 块)")

    def get_stats(self) -> str:
        """获取知识库统计"""
        count = self.collection.count()
        # 获取所有元数据
        all_meta = self.collection.get(include=["metadatas"])
        sources = set()
        total_tokens = 0
        for meta in all_meta["metadatas"]:
            sources.add(meta.get("source", "未知"))
            total_tokens += meta.get("token_count", 0)

        return (
            f"📊 知识库统计\n"
            f"  文档数: {len(sources)}\n"
            f"  文本块: {count}\n"
            f"  总Token: {total_tokens}\n"
            f"  文档列表: {', '.join(sorted(sources))}"
        )

    async def query(self, user_input: str) -> str:
        """处理用户查询"""
        # 1. 路由
        routing = await self.router.route(user_input)
        print(f"  [路由] {routing.category.value} (置信度: {routing.confidence:.2f})")

        # 2. 执行
        if routing.category == ToolCategory.RAG:
            return await self._handle_rag(routing.rewritten_query or user_input, user_input)
        elif routing.category == ToolCategory.WEATHER:
            return await self._handle_weather(user_input)
        elif routing.category == ToolCategory.CALCULATOR:
            return await self._handle_calculate(user_input)
        else:
            return await self._handle_general(user_input)

    async def _handle_rag(self, search_query: str, original: str) -> str:
        """RAG 查询"""
        results = await self.retriever.retrieve(search_query, top_k=3)
        context = self.retriever.format_for_llm(results, max_tokens=2500)

        if not context.strip():
            return "抱歉，知识库中没有找到相关文档。"

        print(f"  [检索] 找到 {len(results)} 个相关文档块")
        answer = await self.generator.generate(original, context)
        return answer

    async def _handle_weather(self, user_input: str) -> str:
        """天气查询"""
        import re
        cities = ["北京", "上海", "武汉", "深圳", "广州", "杭州", "成都"]
        found = [c for c in cities if c in user_input]
        if not found:
            found = ["北京"]  # 默认

        weather_info = []
        for city in found:
            mock = {"北京": "晴25°C", "上海": "多云28°C", "武汉": "小雨30°C"}.get(city, "晴22°C")
            weather_info.append(f"{city}: {mock}")

        result = "\n".join(weather_info)
        prompt = f"用户问：{user_input}\n天气数据：{result}\n请基于数据回答。"

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "glm-4-flash", "messages": [{"role": "user", "content": prompt}],
                   "temperature": 0.3, "max_tokens": 256}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _handle_calculate(self, user_input: str) -> str:
        """数学计算"""
        return "计算功能已就绪。（完整实现请参考 Day 5 代码）"

    async def _handle_general(self, user_input: str) -> str:
        """通用对话"""
        self.conversation_history.append({"role": "user", "content": user_input})

        messages = [
            {"role": "system", "content": "你是一个友善的AI助手，简洁回答。"},
            *self.conversation_history[-10:],
        ]

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": "glm-4-flash", "messages": messages,
                   "temperature": 0.7, "max_tokens": 1024, "stream": True}

        full = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                async for line in resp.aiter_lines():
                    if not line.strip(): continue
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            c = chunk["choices"][0].get("delta", {}).get("content", "")
                            if c:
                                print(c, end="", flush=True)
                                full += c
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
        print()
        self.conversation_history.append({"role": "assistant", "content": full})
        return full


# === 主程序 ===

async def main():
    print("📚 知识库问答 Agent v1.0")
    print("━" * 35)

    # 配置
    config_path = Path("~/agent-learning/week1/data/chat_config.json").expanduser()
    api_key = ""
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            api_key = json.load(f).get("api_key", "")
    if not api_key:
        api_key = input("API Key: ").strip()

    docs_dir = input("文档目录路径 (默认: ./docs): ").strip() or "./docs"

    # 创建示例文档（如果目录为空）
    docs_path = Path(docs_dir).expanduser()
    if not docs_path.exists() or not list(docs_path.glob("*")):
        docs_path.mkdir(parents=True, exist_ok=True)
        (docs_path / "sample.md").write_text("""# Python 异步编程

## 概述
异步编程允许程序在等待 I/O 时执行其他任务。Python 通过 async/await 提供原生支持。

## 核心概念

### 协程
使用 async def 定义的函数。调用时返回协程对象，需要用 await 或事件循环执行。

### 事件循环
asyncio.run() 创建并运行事件循环，是异步程序的入口点。

### asyncio.gather
并发运行多个协程，等待全部完成后返回结果列表。
```python
results = await asyncio.gather(task1(), task2())
```

## 常见应用

- HTTP 请求（httpx.AsyncClient）
- 文件操作（aiofiles）
- 数据库（asyncpg, motor）
  """, encoding="utf-8")
  print(f"已创建示例文档: {docs_path / 'sample.md'}")
  
  # 初始化 Agent
  
  agent = KnowledgeBaseAgent(api_key, str(docs_path))
  await agent.build_index()
  
  print("\n可用命令：")
  print("  /search <query>  - 搜索知识库")
  print("  /stats           - 知识库统计")
  print("  /help            - 帮助")
  print("  /quit            - 退出")
  
  while True:
  try:
  user_input = input("\n> ").strip()
  except (EOFError, KeyboardInterrupt):
  print("\n再见！")
  break
  
  ```
  if not user_input:
        continue
  
    if user_input == "/quit":
        print("再见！")
        break
    elif user_input.startswith("/search "):
        query = user_input[8:]
        results = await agent.retriever.retrieve(query, top_k=5)
        for r in results:
            src = r["metadata"].get("source", "")
            print(f"  [{r.get('rrf_score', r.get('distance', 0)):.4f}] {src} | {r['content'][:60]}...")
    elif user_input == "/stats":
        print(agent.get_stats())
    elif user_input == "/help":
        print("直接输入问题即可。命令：/search /stats /help /quit")
    else:
        try:
            answer = await agent.query(user_input)
            if not user_input.startswith("/"):
                print(f"\n{answer}")
        except httpx.HTTPStatusError as e:
            print(f"API错误: {e.response.status_code}")
        except Exception as e:
            print(f"错误: {e}")
  ```

if __name__ == "__main__":
if sys.platform == "win32":
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())

```

### Day 6 练习

1. 将 Day 1-5 的所有类整合到 `kb_agent.py` 中，确保程序可以直接运行
2. 添加 `/add_doc <path>` 命令 —— 动态添加新文档到知识库
3. 添加 `/evaluate` 命令 —— 用预设的 QA 对快速评测 RAG 效果

---

## Day 7：复习 + 总结 + 周测

### 7.1 自测清单

```

文档处理与切分：
[ ] 能加载 txt/md/pdf 文件
[ ] 理解三种切分策略（按Token/段落/标题）
[ ] 知道 chunk_size 和 overlap 的选择原则
[ ] 能实现按代码结构的切分

向量数据库：
[ ] 能用 ChromaDB 创建 Collection 并添加文档
[ ] 能自定义 Embedding Function
[ ] 能批量索引文档
[ ] 能执行基本的向量检索
[ ] 能使用元数据过滤

检索策略：
[ ] 理解基础向量检索的局限性
[ ] 能实现混合检索（向量+关键词）
[ ] 能实现 RRF 融合
[ ] 能实现查询改写和查询扩展
[ ] 能实现上下文窗口扩展（相邻块）

RAG 生成与评测：
[ ] 能设计 RAG 提示词
[ ] 理解 RAG 评测的三个维度
[ ] 能用 LLM-as-Judge 实现 RAG 评测
[ ] 知道 chunk_size/top_k/temperature 对效果的影响

Multi-Tool Agent：
[ ] 理解四种编排模式
[ ] 能实现工具路由器
[ ] 能实现 ReAct 循环
[ ] 能处理并行工具调用
[ ] 能构建完整的多工具 Agent

```

### 7.2 综合练习题

**构建你自己的"编程学习助手"**：

1. 收集 5+ 篇技术文档（Python/前端/AI 相关），建立知识库
2. 实现以下工具：
   - RAG：基于文档的知识问答
   - Code：执行简单 Python 代码（用 `exec` + 沙箱）
   - Web：模拟网络搜索
   - Quiz：根据文档生成练习题
3. 实现路由器，自动判断用户意图并选择工具
4. 设计评测集（10个问题），跑评测并记录分数
5. 调优：调整 chunk_size、top_k、提示词，看分数变化

> 完成这个项目，你就拥有了第一个完整的 Agent 作品，可以作为简历项目展示。

### 7.3 Month 1 回顾

```

第1月学习路径回顾：

Week 1: Python 基础
→ 变量、类型、异步、文件操作、CLI 工具

Week 2: LLM 核心概念
→ Token、Context Window、采样参数、Embedding、Chat API

Week 3: Prompt Engineering
→ 系统提示词、Few-Shot、CoT、结构化输出、Function Calling

Week 4: RAG + Multi-Tool Agent
→ 文档处理、向量数据库、检索策略、RAG 评测、Agent 编排

你已经掌握的能力：
✓ 用 Python 构建 LLM 应用
✓ 设计高质量的 Prompt
✓ 实现 RAG 检索增强生成
✓ 构建 Multi-Tool Agent
✓ 评测和优化 Agent 效果

接下来（Month 2 预告）：
Week 5: LangChain 框架
Week 6: LangGraph + 状态机 Agent
Week 7: Multi-Agent 系统
Week 8: Agent 评测与部署

```

---

## 本周知识图谱

```

RAG + Multi-Tool Agent
├── 文档处理（Day 1）
│   ├── 多格式加载（txt/md/pdf）
│   ├── 切分策略（Token/段落/标题/代码）
│   └── 切分参数选择
│
├── 向量数据库（Day 2）
│   ├── ChromaDB 基础 CRUD
│   ├── 自定义 Embedding Function
│   ├── 批量索引
│   └── 元数据过滤
│
├── 检索策略（Day 3）
│   ├── 混合检索（向量+关键词）
│   ├── RRF 融合
│   ├── 查询改写与扩展
│   └── 上下文窗口扩展
│
├── RAG 生成与评测（Day 4）
│   ├── RAG 提示词设计
│   ├── 评测三维度（忠实度/相关性/上下文）
│   ├── LLM-as-Judge
│   └── 参数调优
│
├── Multi-Tool Agent（Day 5）
│   ├── 四种编排模式
│   ├── 工具路由器
│   ├── 并行工具调用
│   └── 兜底策略
│
└── 综合实战（Day 6-7）
├── 知识库问答 Agent
└── 编程学习助手

```

## RAG 调优速查表

```

┌──────────────────────────────────────────────────────────┐
│               RAG 调优速查表                               │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  问题：回答不相关                                          │
│  → 增大 top_k（5→10）                                     │
│  → 使用查询改写                                           │
│  → 使用混合检索                                           │
│                                                          │
│  问题：回答编造信息                                        │
│  → 加强"只基于文档"的提示词                                │
│  → 降低 temperature（0.7→0.3）                            │
│  → 添加 Few-Shot 示例（正确引用 vs 编造）                   │
│                                                          │
│  问题：检索不到相关文档                                    │
│  → 调整 chunk_size（太大→不精确，太小→不完整）              │
│  → 增大 overlap（50→100）                                 │
│  → 使用查询扩展（多角度检索）                               │
│  → 检查 Embedding 模型是否合适                             │
│                                                          │
│  问题：回答不完整                                          │
│  → 增大 max_tokens                                       │
│  → 增加上下文窗口（3000→5000 tokens）                      │
│  → 使用上下文扩展（包含相邻块）                             │
│  → 检查 finish_reason 是否为 "length"                     │
│                                                          │
│  问题：Token 消耗太高                                     │
│  → 减小 top_k（10→3）                                    │
│  → 减小 chunk_size                                       │
│  → 压缩系统提示词                                         │
│  → 使用更便宜的模型做检索（glm-4-flash）                    │
│                                                          │
└──────────────────────────────────────────────────────────┘

```

```
