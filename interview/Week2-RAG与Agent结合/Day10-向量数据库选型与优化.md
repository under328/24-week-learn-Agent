# Day 10 — 向量数据库选型与优化

> **学习目标**: 系统掌握向量数据库的核心需求、主流方案选型、索引算法原理(HNSW/IVF)、量化技术、混合检索、分布式架构设计,能够独立完成十亿级向量检索系统的选型与设计。
>
> **面试定位**: 高频考点。面试官常从"你用过哪个向量数据库?"切入,逐步追问索引原理、调参经验、混合检索实现、分布式设计。中高级 Agent 岗位必考,系统设计题的高频方向之一。
>
> **前置知识**: Day08 RAG 全链路、Day09 Agentic RAG/GraphRAG。
>
> **预计学习时长**: 4-5 小时(含手撕代码)。

---

## 今日知识图谱

```
向量数据库选型与优化
├── 1. 核心需求
│   ├── ANN 近似最近邻检索 (Recall vs Latency 权衡)
│   ├── 持久化存储 (内存 / 磁盘 / 混合)
│   ├── 元数据过滤 (Structured + Unstructured)
│   ├── 分布式扩展 (水平扩展 / 副本 / 故障恢复)
│   └── CRUD 支持 (增量更新 / 删除 / 一致性)
│
├── 2. 主流方案对比
│   ├── Pinecone (全托管 Serverless)
│   ├── Milvus (开源 分布式 工业级)
│   ├── Weaviate (开源 模块化 向量+图谱)
│   ├── Qdrant (Rust 高性能 过滤强)
│   ├── Chroma (轻量 原型开发)
│   ├── pgvector (PostgreSQL 扩展)
│   └── ElasticSearch / OpenSearch (kNN 插件)
│
├── 3. 索引算法
│   ├── HNSW (层级小世界图)
│   │   ├── 原理: 多层跳跃图, 上层稀疏快速导航, 下层密集精确搜索
│   │   ├── 参数: M (邻居数) / efConstruction (构建宽度) / efSearch (查询宽度)
│   │   └── 优点: 高召回率, 低延迟 / 缺点: 内存大, 构建慢
│   │
│   ├── IVF (倒排文件)
│   │   ├── 原理: K-Means 聚类, 查询只扫描 nprobe 个簇
│   │   ├── 变体: IVF-Flat (原始向量) / IVF-PQ (量化压缩)
│   │   └── 参数: nlist (聚类数) / nprobe (查询簇数)
│   │
│   ├── 暴力扫描 (Flat)
│   │   └── 适用: 小数据集 (<10万) 精确结果
│   │
│   └── 其他: Annoy (树) / ScaNN / DiskANN (磁盘索引)
│
├── 4. 量化技术
│   ├── PQ (Product Quantization) 乘积量化
│   ├── SQ (Scalar Quantization) 标量量化
│   ├── 二值化 (Binary Quantization)
│   └── 权衡: 内存 vs 精度 vs 速度
│
├── 5. 混合检索
│   ├── 向量检索 + 关键词检索 (BM25)
│   ├── 元数据过滤
│   │   ├── Pre-filter (先过滤再检索)
│   │   ├── Post-filter (先检索再过滤)
│   │   └── Hybrid-filter (过滤下推到索引)
│   └── 融合策略: RRF / 加权平均 / Reranker
│
├── 6. 性能优化
│   ├── 分片 (Sharding) — 按向量 ID / 元数据哈希
│   ├── 副本 (Replication) — 读写分离 / 高可用
│   ├── 批量写入 (Batch Insert)
│   ├── 缓存 (Query Cache / Embedding Cache)
│   └── 索引重建策略 (增量 / 全量)
│
└── 7. 分布式架构
    ├── 数据分片 (一致性哈希 / 范围分片)
    ├── 副本一致性 (Leader-Follower / Quorum)
    ├── 查询路由 ( Scatter-Gather )
    ├── 故障恢复 (WAL / 增量回放)
    └── 十亿级系统设计要点
```

---

## 面试题(共 10 道)

### Q1: 向量数据库的核心需求是什么?与传统关系型数据库的本质区别在哪里?

<details>
<summary>点击查看参考答案</summary>

**核心需求**(5 个维度):

| 需求维度 | 说明 | 典型指标 |
|---------|------|---------|
| ANN 近似最近邻检索 | 给定查询向量,快速返回 Top-K 最相似向量 | 召回率(Recall@K)、延迟 P99 |
| 持久化存储 | 向量数据量大(GB-TB 级),需内存+磁盘混合存储 | 内存占用、磁盘 IO |
| 元数据过滤 | 业务场景几乎都需结合属性过滤(filter) | 过滤效率、下推能力 |
| 分布式扩展 | 十亿级向量需水平扩展,单机无法承载 | 分片数、副本数、扩展性 |
| CRUD 支持 | 实时插入、更新、删除,且不能破坏索引结构 | 写入 TPS、更新延迟 |

**与传统数据库的本质区别**:

1. **相似度 vs 精确匹配**: 传统数据库基于 B+Tree 做等值/范围查询;向量数据库基于近似最近邻做相似度查询(余弦/欧氏/内积),本质是"模糊匹配"。

2. **索引结构完全不同**:
   - 传统: B+Tree、Hash Index,针对"精确点查"优化
   - 向量: HNSW(图索引)、IVF(倒排聚类)、PQ(量化),针对"高维空间近邻"优化
   - 高维空间不存在传统意义上的"排序",无法用 B+Tree 高效索引

3. **查询语言差异**: 传统 SQL `WHERE` 是精确谓词;向量查询是 `ORDER BY distance LIMIT K`,距离计算本身是 O(D) 复杂度(D 为维度)。

4. **精度-性能权衡**: 传统数据库结果是"精确"的;向量数据库通常是"近似"的(ANN),需在召回率和延迟间权衡。

5. **内存模型**: 传统数据库行存/列存;向量数据库通常是"向量列+元数据列"的混合存储,向量列需常驻内存以加速距离计算。

**追问:为什么不能用传统数据库做向量检索?**

- 理论上可以(暴力扫描 `SELECT * ORDER BY cosine_sim(v, query) LIMIT 10`),但复杂度 O(N*D),10 亿向量查询需数小时。
- ANN 算法把复杂度降到 O(log N) ~ O(N^0.5),延迟从小时级降到毫秒级,代价是召回率略降(95%-99%)。
- pgvector / ElasticSearch 的 kNN 功能本质是在传统数据库内嵌入 ANN 索引(HNSW/IVF),而非用传统索引加速。

**追问:向量数据库的"ACID"是什么?**

- 大多数向量数据库弱化 ACID,强调**最终一致性** + **高可用**。
- Milvus 2.x 支持"强一致性"(查询时强制读主副本)和"有界一致性"(默认,读副本可滞后几秒)。
- 写入通常异步构建索引(写入 → WAL → 后台 Compaction → 索引更新),查询可能查到"未索引"的数据,需注意"写入即可见"的语义保证。

</details>

---

### Q2: 主流向量数据库(Pinecone/Milvus/Weaviate/Qdrant/Chroma/pgvector)如何对比选型?请给出选型维度和决策建议。

<details>
<summary>点击查看参考答案</summary>

**选型维度矩阵**:

| 维度 | Pinecone | Milvus | Weaviate | Qdrant | Chroma | pgvector |
|------|----------|--------|----------|--------|--------|----------|
| 部署模式 | 全托管 Serverless | 自部署 / Zilliz Cloud | 自部署 / Cloud | 自部署 / Cloud | 本地 / 嵌入式 | PostgreSQL 扩展 |
| 开源 | 否 | 是(Apache 2.0) | 是(BSD) | 是(Apache 2.0) | 是(Apache 2.0) | 是(PostgreSQL) |
| 语言 | 闭源 | Go | Go | Rust | Python + Rust | C |
| 十亿级支持 | 是(Serverless) | 是(分布式) | 部分(单机较强) | 是(分片) | 否(<千万) | 否(<千万) |
| 索引算法 | 专有(Proprietary) | HNSW/IVF/DiskANN/ANNOY | HNSW | HNSW | HNSW | HNSW / IVFFlat |
| 元数据过滤 | 强 | 强 | 强 | **极强**(过滤下推) | 弱 | SQL WHERE |
| 量化 | 自动 | PQ/SQ | PQ | SQ/Binary | 无 | 无 |
| 混合检索 | 内置 | 内置(BM25+向量) | 内置(BM25+向量) | 内置 | 弱 | 需自实现 |
| 实时更新 | 是 | 是 | 是 | 是 | 是 | 是 |
| 一致性 | 最终 | 强/有界/最终 | 强 | 强 | 单机 | 事务(ACID) |
| 学习曲线 | 低(API 简单) | 高(组件多) | 中 | 中 | 极低 | 低(熟悉 PG) |
| 成本 | 按量计费贵 | 自部署低 / Cloud 中 | 中 | 自部署低 | 极低 | 复用现有 PG |

**决策建议**(分场景):

**场景 1: 创业公司 / 快速原型验证**
- 推荐: **Chroma**(本地开发) + **Pinecone**(生产托管)
- 理由: Chroma 几行代码就能跑,Pinecone 免运维,但成本高。数据量 <1000 万时性价比可接受。

**场景 2: 中型企业 / 数据敏感需私有部署**
- 推荐: **Qdrant** 或 **Weaviate**
- 理由: 单机性能强(Qdrant Rust 实现,过滤下推优秀),中等规模(千万级)无需分布式,运维简单。Qdrant 在"向量+复杂过滤"场景性能最佳。

**场景 3: 大厂 / 十亿级向量 / 工业级**
- 推荐: **Milvus**(自部署)或 **Zilliz Cloud**(托管)
- 理由: Milvus 是唯一经过大厂大规模验证的开源方案,支持多种索引、分片、副本、磁盘索引(DiskANN)。缺点是组件多(etcd/MinIO/Pulsar),运维复杂。

**场景 4: 已有 PostgreSQL 技术栈 / 数据量不大**
- 推荐: **pgvector**
- 理由: 复用现有 PG 运维、事务、SQL 生态,向量检索和业务查询可联表。适合 <1000 万向量的小到中规模场景。缺点是性能和扩展性受限。

**场景 5: 已有 ElasticSearch / 想要 BM25+向量深度融合**
- 推荐: **ElasticSearch kNN** 或 **OpenSearch k-NN**
- 理由: ES 的 BM25 是工业级标准,加上 kNN 插件后混合检索开箱即用。适合"全文搜索为主,向量检索为辅"的场景。

**面试加分点 — 选型三原则**:

1. **数据规模决定上限**: <1000 万选 pgvector/Chroma;千万-亿级选 Qdrant/Weaviate;十亿级以上选 Milvus/Pinecone Serverless。
2. **过滤复杂度决定下限**: 如果业务有大量结构化过滤,Qdrant 的"过滤下推"是杀手锏,post-filter 的方案会出现"查不到"问题。
3. **团队能力决定选谁**: 没有专职运维团队别选 Milvus 自部署,Pinecone/Zilliz Cloud 托管更稳。

**追问:为什么 Qdrant 的过滤下推比其他强?**

- 大多数向量库的过滤是 post-filter: 先做 ANN 检索取 Top-K(假设 K=100),再用 filter 过滤,可能只剩 5 条,且不是"全局最相似的 100 条过滤后结果"。
- Qdrant 把 filter 下推到 HNSW 遍历过程: 遍历时跳过不满足 filter 的节点,继续扩展邻居,直到收集够 K 条。结果是"过滤后全局最相似的 K 条",且不会因 filter 过严导致结果不足。
- 代价: 遍历的节点数增加,延迟略升,但 Recall 大幅提升。

</details>

---

### Q3: 请详细讲解 HNSW 索引算法的原理,以及核心参数 M、efConstruction、efSearch 的调优经验。

<details>
<summary>点击查看参考答案</summary>

**HNSW (Hierarchical Navigable Small World) 原理**:

HNSW 是"分层小世界图",灵感来自跳表(Skip List)。核心思想是构建多层图,上层稀疏(节点少,跨越远距离),下层密集(节点多,精确近邻)。

```
Layer 2:  A ----------------------- G          (稀疏,远距离跳跃)
          |                         |
Layer 1:  A ------- D ------------- G - I       (中等密度)
          |         |               |   |
Layer 0:  A - B - C - D - E - F - G - H - I - J (全量节点,密集)
```

**查询过程**(从上层到下层):
1. 从 Layer 2 的入口节点 A 开始,在当前层做"贪心搜索"(每步走向距离 query 更近的邻居)直到局部最优。
2. 把结果作为下一层入口,在 Layer 1 继续贪心搜索,覆盖更广范围。
3. 在 Layer 0(最密集层)做精细搜索,返回 Top-K。

**构建过程**:
1. 为新节点随机分配一个层级 l(指数衰减分布,大部分节点在 Layer 0)。
2. 从顶层开始贪心搜索找到该层最近邻,作为入口。
3. 在 l 层及以下,每层找 M 个最近邻居建立双向连接。
4. 剪枝: 控制每个节点的连接数不超过 Mmax(通常 Mmax0 = 2*M)。

**核心参数详解**:

| 参数 | 含义 | 典型值 | 调优方向 |
|------|------|--------|---------|
| `M` | 每个节点的邻居数(除 Layer 0) | 16-48 | 越大召回越高,内存越大 |
| `Mmax0` | Layer 0 节点最大邻居数 | 2*M | 通常不需手动调 |
| `efConstruction` | 构建时搜索宽度 | 200-500 | 越大索引质量越好,构建越慢 |
| `efSearch` | 查询时搜索宽度 | 50-200 | 越大召回越高,延迟越大 |

**调优经验**(实战建议):

**场景 1: 召回率优先(对精度敏感,如知识库 RAG)**
```
M = 32, efConstruction = 500, efSearch = 200
预期: Recall@10 = 98%+,延迟 P99 = 5-10ms(百万级数据)
内存: 约 4-6 倍原始向量大小
```

**场景 2: 延迟优先(实时推荐)**
```
M = 16, efConstruction = 200, efSearch = 50
预期: Recall@10 = 92-95%,延迟 P99 = 1-3ms
内存: 约 2-3 倍原始向量大小
```

**场景 3: 内存优先(嵌入式 / 边缘)**
```
M = 12, efConstruction = 100, efSearch = 30
配合 PQ 量化,内存可降到原始向量的 1/8
预期: Recall@10 = 85-90%
```

**调优口诀**:
- **先调 efConstruction**(一次性成本,越大越好,影响索引质量上限)
- **再调 efSearch**(运行时可调,是召回 vs 延迟的"主旋钮")
- **最后调 M**(影响内存,需重建索引才能改)

**调优流程**:
1. 用 `efConstruction = 400, M = 16` 构建索引。
2. 准备测试集(100-1000 条 query + ground truth)。
3. 二分搜索 `efSearch`:从 50 开始,翻倍直到 Recall@10 达标(通常 95%),记录此时延迟。
4. 如果 efSearch 调到 500 仍不达标,增大 M 到 32 重建。
5. 如果延迟超标,降低 M 或配合 PQ 量化。

**HNSW 的优缺点**:

| 优点 | 缺点 |
|------|------|
| 召回率高(95%+) | 内存占用大(图结构 + 原始向量) |
| 查询延迟低(亚毫秒-毫秒) | 构建慢(每插入一个节点都要搜索) |
| 支持动态插入(无需全量重建) | 不支持高效删除(需软删除+定期重建) |
| 参数少,调优直观 | 并行构建困难(图结构有依赖) |
| 对数据分布不敏感 | 高维(>1000 维)性能下降 |

**追问:HNSW 为什么比 IVF 快?**

- IVF 是"分桶"思路: 查询时只扫描 nprobe 个桶,但每个桶内是暴力扫描,桶大小不均(某些桶很大)。
- HNSW 是"图导航"思路: 每步都向更近的节点移动,搜索路径长度是 O(log N) 级别,远小于 IVF 的桶内扫描。
- 但 HNSW 内存更大(图结构开销),且随机访问模式对缓存不友好。在内存充足时 HNSW 通常优于 IVF;内存受限时 IVF-PQ 更优。

**追问:HNSW 的删除怎么处理?**

- HNSW 的图结构难以高效删除节点(删除后需修复邻居连接)。
- 主流方案: **软删除**(标记 tombstone,查询时跳过)+ **定期全量重建**(后台 Compact)。
- Milvus/Qdrant 都用类似策略,删除后短期内磁盘占用不会立即降低。

</details>

---

### Q4: IVF 索引的原理是什么?IVF-Flat 和 IVF-PQ 有何区别?如何选择 nlist 和 nprobe?

<details>
<summary>点击查看参考答案</summary>

**IVF (Inverted File) 原理**:

IVF 借鉴了文本检索的"倒排索引"思路:

1. **训练阶段**: 对所有向量做 K-Means 聚类,得到 `nlist` 个聚类中心(质心)。
2. **构建阶段**: 每个向量分配到最近的质心,形成 `nlist` 个"倒排桶"(inverted list)。
3. **查询阶段**:
   - 计算 query 与所有 `nlist` 个质心的距离,选最近的 `nprobe` 个桶。
   - 只在这 `nprobe` 个桶内做暴力扫描(Flat)或量化扫描(PQ),返回 Top-K。

```
质心: C1, C2, C3, ..., C_nlist
桶1: [v1, v5, v12, ...]      <- 离 C1 最近的向量
桶2: [v2, v3, v8, ...]       <- 离 C2 最近的向量
...
查询: 找离 query 最近的 nprobe=2 个桶 (如 C1, C3),在桶内暴力扫描
```

**复杂度**:
- 训练: O(N * nlist * iterations * D)
- 查询: O(nlist * D) + O(nprobe * |桶大小| * D)
- 关键: `nprobe` 越大,扫描越多,召回越高,延迟越大。

**IVF-Flat vs IVF-PQ**:

| 维度 | IVF-Flat | IVF-PQ |
|------|----------|--------|
| 桶内存储 | 原始向量(float32) | PQ 量化后的编码(uint8) |
| 内存 | N * D * 4 bytes | N * D / 4 bytes (PQ 压缩 ~16x) |
| 距离计算 | 精确(浮点) | 近似(查表 ADC) |
| 召回率 | 高(只受 nprobe 影响) | 中(受 PQ 量化损失影响) |
| 查询速度 | 中(浮点计算) | 快(整数查表 + SIMD) |
| 适用场景 | 内存充足,精度优先 | 大规模数据,内存受限 |

**IVF-PQ 详解**:

PQ (Product Quantization) 把 D 维向量切分成 `m` 个子向量,每个子向量用 1 字节(256 个码字)编码:

```
原始: [0.12, 0.45, 0.78, 0.23, 0.56, 0.91, 0.34, 0.67]  (8维, 32 bytes)
切成 m=2 段:
  子向量1: [0.12, 0.45, 0.78, 0.23] -> K-Means(256) -> 码字 ID: 142 (1 byte)
  子向量2: [0.56, 0.91, 0.34, 0.67] -> K-Means(256) -> 码字 ID: 87  (1 byte)
编码后: [142, 87]  (2 bytes, 压缩 16x)
```

查询时用 ADC (Asymmetric Distance Computation): 用原始 query 向量对各子空间码本预计算距离表,再查表累加得到近似距离。

**nlist 和 nprobe 调优**:

**nlist (聚类数)**:
- 经验公式: `nlist ≈ sqrt(N)` 到 `nlist ≈ 4 * sqrt(N)`
- N=100万 → nlist=1024-4096
- N=1亿 → nlist=10000-40000
- 太小: 桶太大,扫描慢;太大: 训练慢,质心计算开销增加。

**nprobe (查询桶数)**:
- 经验: `nprobe ≈ nlist / 100` 到 `nlist / 10`
- 召回率 vs nprobe 曲线是"凸函数",前期增长快,后期饱和。
- 调优方法: 准备测试集,二分搜索 nprobe 直到 Recall@10 达标。

**典型组合**:

| 数据量 | nlist | nprobe | 预期召回 | 预期延迟 |
|--------|-------|--------|---------|---------|
| 100万 | 1024 | 16-64 | 95-98% | 2-5ms |
| 1000万 | 4096 | 64-128 | 95-97% | 5-10ms |
| 1亿 | 16384 | 128-256 | 93-96% | 10-30ms |

**选择建议**:

- **数据量小 (<100万) + 精度优先**: HNSW > IVF-Flat > IVF-PQ
- **数据量中 (100万-1亿) + 内存充足**: HNSW 或 IVF-Flat
- **数据量大 (>1亿) + 内存受限**: **IVF-PQ** 是首选,配合 DiskANN 可支持十亿级磁盘索引
- **需要频繁更新**: IVF 系列更新更友好(新向量直接进桶,无需重训),HNSW 增量插入虽支持但内存压力大

**追问:IVF-PQ 的召回损失有多大?如何缓解?**

- 单纯 IVF-PQ 召回通常比 IVF-Flat 低 5-15%(取决于向量分布和 PQ 参数)。
- 缓解手段:
  1. **增大 m**(PQ 子向量数): m 越大压缩率越低但精度越高。如 m=D/2 每子向量 2 维,精度接近原始。
  2. **IVFPQ-R (Refine)**: PQ 查 Top-K*5 候选,再用原始向量重排(refine)取 Top-K。Milvus 支持。
  3. **OPQ (Optimized PQ)**: 训练前对向量做旋转矩阵优化,使子向量分布更均衡,Faiss 有 OPQ 实现。
  4. **增加 nprobe**: 多扫描桶,弥补量化损失。

</details>

---

### Q5: 向量量化技术有哪些?如何平衡精度、内存和速度?

<details>
<summary>点击查看参考答案</summary>

**主流量化技术**:

| 量化技术 | 原理 | 压缩率 | 精度损失 | 速度提升 | 适用场景 |
|---------|------|--------|---------|---------|---------|
| **PQ** (Product Quantization) | 子向量 K-Means 量化 | 8-32x | 中(5-15%) | 2-5x | 大规模内存压缩 |
| **SQ** (Scalar Quantization) | 每维独立量化(float32→int8) | 4x | 小(1-3%) | 2-3x | 中等压缩,精度友好 |
| **Binary** (二值量化) | 每维符号化(>0→1, <=0→0) | 32x | 大(10-25%) | 10x+ (Hamming 距离) | 极致压缩,粗筛 |
| **OPQ** (Optimized PQ) | PQ + 旋转优化 | 8-32x | 小(比 PQ 好 2-5%) | 同 PQ | PQ 精度不够时 |
| **ScaNN** (各向异性量化) | 区分误差方向加权量化 | 8-16x | 小 | 3-5x | Google 内部,开源版可用 |

**详细原理**:

**1. SQ (Scalar Quantization)**:
- 对每一维独立做线性映射: `q = round((x - min) / (max - min) * 255)` 存为 uint8。
- 距离计算: 用 uint8 查 LUT(查找表)或 SIMD 加速。
- 优点: 实现简单,精度损失小,适合"中等压缩+精度优先"。
- 缺点: 压缩率上限 4x(float32→int8)。

**2. PQ (Product Quantization)**:
- 见 Q4 详解,切分子向量+独立 K-Means。
- 优点: 压缩率高(8-32x),ADC 查表快。
- 缺点: 子向量间相关性丢失,精度损失比 SQ 大。

**3. 二值化 (Binary Quantization)**:
- `b = 1 if x > 0 else 0`,每维 1 bit。
- 距离用 Hamming 距离(异或+popcount,CPU 有硬件指令)。
- 优点: 压缩 32x,Hamming 计算极快(SIMD 单指令 256 位)。
- 缺点: 精度损失大,通常配合"二值粗筛 + float 精排"使用。
- OpenAI embeddings、Cohere 都内置了二值化方案,配合 refine 使用。

**4. OPQ (Optimized Product Quantization)**:
- PQ 假设子向量独立,实际高维向量各维相关性强,直接切分会丢失信息。
- OPQ 训练一个旋转矩阵 R,使变换后向量 `y = R * x` 的各子空间方差均衡。
- 精度比 PQ 提升 2-5%,训练成本增加(需联合优化 R 和码本)。

**平衡策略 — 多级量化**:

工业级方案通常用"多级级联",而非单一量化:

```
查询: query (float32)
   ↓
第1级: 二值量化粗筛
  - 库中向量二值化,Hamming 距离取 Top-K*100
  - 极快(SIMD),精度粗
   ↓
第2级: PQ 量化精筛
  - 候选用 PQ 距离重排,取 Top-K*10
  - 内存友好,精度中
   ↓
第3级: 原始向量精排 (Refine)
  - 候选用 float32 精确距离重排,返回 Top-K
  - 精度最高,仅小量候选走这步
```

这种"漏斗"策略兼顾速度、内存、精度:
- 99% 的计算走二值/PQ,极快;
- 原始向量只对 Top-K*10 候选计算,内存可只放量化版本,原始向量存磁盘按需加载。

**选型决策树**:

```
内存是否充足?
├── 是 → 不量化或仅 SQ (精度损失最小)
└── 否
    ├── 数据量 <1亿 → PQ (压缩 16x)
    ├── 数据量 1-10亿 → OPQ + Refine
    └── 数据量 >10亿 → Binary 粗筛 + PQ 精筛 + 磁盘 Refine (DiskANN)
```

**实战经验**:

1. **先试 SQ**: 4x 压缩、精度损失 <3%,大多数场景够用,实现简单。Qdrant 默认支持 SQ8。
2. **PQ 注意 m 选择**: m 太小精度崩,太大压缩率低。经验 `m = D / 4`(每子向量 4 维)是不错的起点。
3. **Refine 是免费午餐**: PQ + Refine 几乎无精度损失(比纯 PQ 召回提升 3-8%),代价仅是少量原始向量重排。
4. **向量归一化对量化友好**: L2 归一化后向量分布更集中,量化边界更清晰,精度损失更小。
5. **二值化需配合短向量**: 1536 维 OpenAI 向量二值化后 192 字节,效果尚可;768 维以下二值化精度损失大,慎用。

**追问:为什么 PQ 精度损失比 SQ 大?**

- SQ 每维独立量化,信息损失是"逐维均匀"的,误差上限可控(max-min / 256)。
- PQ 把 D 维切分成 m 段,每段 K-Means 量化。K-Means 假设子向量服从 m 个高斯混合,实际分布不一定是,且子向量间的相关性被完全丢弃(切分点硬边界)。
- 改进: OPQ 通过旋转矩阵让子向量更"独立均匀",但训练成本高。

</details>

---

### Q6: 混合检索如何实现?重点讲解 pre-filter 和 post-filter 的区别及工程实现。

<details>
<summary>点击查看参考答案</summary>

**为什么需要混合检索?**

纯向量检索的问题:
1. **语义模糊**: "苹果"指水果还是公司?向量相似但语义不同,需元数据过滤。
2. **关键词缺失**: 向量对专有名词、型号、代码等"罕见词"编码弱,BM25 更强。
3. **业务约束**: "只搜用户可见的文档"、"价格 <100 的商品",必须结构化过滤。

**混合检索的三种"混合"**:

| 混合类型 | 说明 | 典型实现 |
|---------|------|---------|
| 向量 + 关键词 | 向量召回 + BM25 召回 + 融合 | RRF / 加权融合 |
| 向量 + 元数据过滤 | 向量召回 + 结构化条件 | pre/post-filter |
| 向量 + 关键词 + 过滤 | 三路结合 | 工业级完整方案 |

**Pre-filter vs Post-filter**:

```
Post-filter:
  ANN(query, top_k=100) → 候选100条
  → filter(候选) → 剩余30条
  → 返回30条 (可能不足 K,且不是全局最优)

Pre-filter:
  filter(全量) → 满足条件的1万条
  → ANN(query, top_k=10, 候选集=1万条) → 返回10条
  → 精确全局最优,但需扫描全部满足条件的数据
```

| 维度 | Pre-filter | Post-filter |
|------|-----------|-------------|
| 结果质量 | 全局最优 | 可能不足 K,非全局最优 |
| 延迟 | 取决于过滤后数据量 | 取决于 ANN K |
| 适用 | 过滤选择性好(过滤后 <10%) | 过滤选择性差(过滤后 >50%) |
| 实现 | 难(需把 filter 下推到索引) | 易(ANN 后 SQL filter) |

**Hybrid-filter (过滤下推)**:

Qdrant、Milvus 2.x 的优化: 把 filter 下推到 HNSW 遍历过程:
- 遍历图节点时,跳过不满足 filter 的节点,继续扩展其邻居。
- 既保证全局最优(不会因 post-filter 不足 K),又避免 pre-filter 扫描全量。
- 代价: 遍历节点数增加,延迟略升。

**Qdrant 过滤下推伪代码**:
```python
def hnsw_search_with_filter(query, k, filter_fn):
    visited = set()
    candidates = []  # min-heap by distance
    results = []     # max-heap by distance, size k
    entry = get_entry_point()
    push(candidates, (distance(query, entry), entry))

    while candidates:
        dist, node = pop_min(candidates)
        if dist > max(results) and len(results) == k:
            break  # 早停
        if node in visited:
            continue
        visited.add(node)
        # 关键: filter 不满足的节点也加入 visited (避免重复),
        # 但不加入 results,继续扩展其邻居
        if filter_fn(node.metadata):
            push(results, (dist, node))
        for neighbor in node.neighbors:
            if neighbor not in visited:
                push(candidates, (distance(query, neighbor), neighbor))

    return results[:k]
```

**向量 + BM25 + RRF 融合**:

RRF (Reciprocal Rank Fusion) 是最常用的融合策略,公式:
```
RRF_score(d) = sum_{r in retrievers} 1 / (k + rank_r(d))
```
其中 `k` 通常取 60(经验值),`rank_r(d)` 是文档 d 在检索器 r 中的排名(从 1 开始)。

**RRF 的优点**:
1. 不需要分数归一化(向量距离和 BM25 分数尺度不同,直接加权困难)。
2. 只用排名,对异常分数鲁棒。
3. 简单有效,工业界广泛使用。

**工程实现要点**:

1. **过滤选择性预估**: 收集过滤条件的统计信息(如某个 tag 的文档比例),选择性高时(<10%)用 pre-filter,低时用 post-filter。
2. **倒排索引辅助过滤**: 对高频过滤字段(如 category, user_id)建倒排索引,pre-filter 时快速定位候选集。
3. **分段策略**: 大型 filter(如时间范围)用倒排+位图(Bitmap),小型 filter 用 HNSW 遍历下推。
4. **缓存过滤结果**: 高频 query 的 filter 结果缓存(如 Redis),TTL 设置合理。
5. **BM25 + 向量并行召回**: 两路检索并发执行,RRF 融合,延迟由慢的路径决定,可设置超时降级。

**面试加分点 — 过滤失效场景**:

面试官常问: "post-filter 为什么会返回结果不足?"

- ANN 取 Top-100 是"全局最相似的 100 条",但其中可能只有 5 条满足 filter。
- 用户要 K=10,实际返回 5 条,且这 5 条不是"满足 filter 的全局最相似的 10 条"。
- 解决: 增大 ANN 的 K(如 K=1000 再过滤),或用 pre-filter / 过滤下推。

**追问:向量+BM25 哪个权重更高?**

- 没有固定答案,取决于场景:
  - **事实型查询**(型号、人名、术语): BM25 权重高,向量易召回"语义相似但事实错误"的内容。
  - **语义型查询**(概念、意图): 向量权重高,BM25 对同义词无能为力。
  - **混合查询**: RRF 是"排名级融合",隐式给了两者接近的权重,实测优于固定加权。
- 进阶: 用 Reranker(Cross-Encoder)对 RRF 候选重排,Reranker 自动学习权重,效果最好。

</details>

---

### Q7: 大规模向量检索的性能优化有哪些手段?请从分片、副本、批量写入、缓存等维度展开。

<details>
<summary>点击查看参考答案</summary>

**性能优化的核心思路**: 减少单点负载,提升并行度,降低 IO 和计算开销。

**1. 分片 (Sharding)**

**分片策略**:
- **随机分片**: 向量 ID 哈希后均匀分布,负载均衡好,但跨分片查询多。
- **基于元数据分片**: 按 tenant_id / category 分片,过滤下推到单分片,减少 fan-out。
- **基于向量聚类分片**: 用 K-Means 把语义相近的向量分到同一片,查询时只扫描相关分片(类似 IVF 的分布式版本)。

**分片数选择**:
- 经验: 单分片不超过 1000 万向量(内存 ~10GB,HNSW 索引 ~30GB)。
- 十亿向量 → 100-200 个分片,部署在 10-20 个节点(每节点 5-10 分片)。

**查询路由**:
- Scatter-Gather: 协调节点广播到所有分片,各分片返回 Top-K,协调节点合并取全局 Top-K。
- 优化: 配合"分片剪枝",只查询与 query 相关的分片(基于聚类中心距离),减少 fan-out。

**2. 副本 (Replication)**

**副本作用**:
- **高可用**: 主副本故障,从副本接管。
- **读写分离**: 写入主副本,查询走从副本,提升读 QPS。
- **就近访问**: 跨地域部署,查询走本地副本。

**副本一致性**:
- **强一致**: 写主后同步从,延迟高但一致。Milvus 的"强一致"模式。
- **最终一致**: 写主后异步同步从,延迟低但查询可能读到旧数据。大多数向量库默认。
- **Quorum**: W + R > N,如 N=3, W=2, R=2,平衡一致性和可用性。

**3. 批量写入 (Batch Insert)**

**单条 vs 批量**:
- 单条插入: 每次触发索引更新(如 HNSW 的图遍历),开销大。
- 批量插入: 攒一批(如 1000-10000 条)一起构建索引,效率提升 10-100x。

**写入流程优化**:
```
Client → Batch Buffer (攒批) → WAL (持久化日志)
  → Segments (分段存储) → 后台 Build Index (HNSW/IVF 构建)
  → 可查询状态 (Visible)
```

**关键参数**:
- `batch_size`: 1000-10000(太小开销大,太大内存压力)
- `flush_interval`: 1-10 秒(平衡延迟和吞吐)
- `index_build_threshold`: 段内向量数达到阈值后构建索引(如 1000)

**4. 缓存 (Caching)**

**多级缓存**:

| 缓存层 | 内容 | 命中条件 | 失效策略 |
|--------|------|---------|---------|
| Query Cache | query → Top-K 结果 | 完全相同 query | TTL 5-30min |
| Embedding Cache | query 文本 → 向量 | 完全相同文本 | LRU,容量限制 |
| HNSW 节点 Cache | 热点节点的邻居列表 | 访问模式 | LRU |
| 过滤结果 Cache | filter → 候选 ID 集合 | 完全相同 filter | TTL 1-5min |

**Embedding Cache 价值最大**: Embedding 计算本身(API 调用)延迟 50-200ms,缓存命中可降到 1ms。推荐场景: 电商搜索、FAQ 机器人等高频 query。

**5. 索引构建优化**

**增量构建 vs 全量重建**:
- HNSW 支持增量插入,但长期碎片化导致性能下降。
- 策略: 增量插入 + 后台定期 Compact(合并段 + 重建索引)。
- Milvus 的 Compact 策略: 段大小超阈值或删除比例超 20% 触发。

**并行构建**:
- IVF 训练可并行(K-Means 可 MapReduce)。
- HNSW 构建天然串行(图结构依赖),但有"分片并行"方案: 数据分片后各片独立建 HNSW,查询时 Scatter-Gather。

**6. 查询优化**

**早停 (Early Termination)**:
- HNSW 遍历时,候选节点距离 > 当前 Top-K 最差距离且队列无更优节点,提前终止。
- 配合 `efSearch` 动态调整: 候选充足时降低 ef,候选不足时提升 ef。

**向量化距离计算**:
- SIMD 指令(AVX2/AVX-512): 单指令计算多维度距离,提速 4-8x。
- Faiss、Milvus 都重度使用 SIMD,自实现务必启用 `-mavx2 -mfma`。

**近似距离**:
- 用量化距离(PQ/SQ)粗排,原始距离精排(Refine),见 Q5。

**7. 监控与调优指标**

```
关键指标:
- 查询延迟 P50/P95/P99
- 写入 TPS
- 召回率 Recall@K (定期用标注集评估)
- 内存利用率 / 磁盘 IO
- 索引构建延迟 / 段数量

调优循环:
1. 监控发现 P99 延迟上升
2. 分析: 是否写入压力? 是否缓存命中率下降? 是否某分片热点?
3. 调整: 加副本 / 调 efSearch / 加缓存 / 分片再平衡
4. 验证: P99 恢复 + Recall 不降
```

**面试加分点 — 性能瓶颈定位**:

面试官问: "如果查询 P99 突然上升到 100ms,如何排查?"

回答框架:
1. **看监控**: 是所有分片都慢还是个别分片?(热点分片)
2. **看负载**: CPU / 内存 / 磁盘 IO 哪个打满?
   - CPU 满: efSearch 太大或 QPS 过高 → 加副本或降 efSearch
   - 内存满: 索引 swap 到磁盘 → 扩内存或量化压缩
   - IO 满: DiskANN 场景磁盘随机读 → SSD 升级或加大缓存
3. **看查询模式**: 是否有"毒 query"(异常向量导致遍历全图)? → 限流 + query 归一化
4. **看写入**: 是否有大规模写入触发 Compact? → 错峰写入

</details>

---

### Q8: 请设计一个分布式向量数据库的架构,要支持十亿级向量、高可用、强一致性写入。重点讲解数据分片、副本一致性、故障恢复。

<details>
<summary>点击查看参考答案</summary>

**整体架构(Milvus 2.x 风格)**:

```
                    ┌──────────────────┐
                    │  Coordinator     │  (元数据 / 调度 / 查询路由)
                    │  (etcd 强一致)   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Query Node    │   │ Query Node    │   │ Query Node    │  (查询节点,持有分片副本)
│ (Shard1-Leader│   │ (Shard2-Leader│   │ (Shard1-Follow│
│  Shard2-Follow│   │  Shard3-Follow│   │  Shard3-Leader│
│  ...)         │   │  ...)         │   │  ...)         │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│              Message Queue (Pulsar / Kafka)              │  (WAL 日志)
└─────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Data Node     │   │ Data Node     │   │ Data Node     │  (数据节点,持久化段)
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│              Object Storage (S3 / MinIO)                 │  (段文件 / 索引文件)
└─────────────────────────────────────────────────────────┘
```

**核心组件**:

| 组件 | 职责 | 存储 |
|------|------|------|
| Coordinator | 元数据管理(集合/分片/索引 schema)、查询路由、调度 | etcd(强一致) |
| Query Node | 加载索引到内存,执行 ANN 查询,持有分片副本 | 内存(RAM) |
| Data Node | 接收写入,持久化为段(Segment),后台构建索引 | 对象存储 |
| Message Queue | WAL 日志,保证写入顺序和持久性 | Pulsar/Kafka |
| Object Storage | 段文件、索引文件持久化 | S3/MinIO |
| etcd | 元数据强一致(集合 schema、分片分配、节点状态) | etcd Raft |

**1. 数据分片 (Sharding)**

**分片粒度**: Collection → Shard(分片) → Segment(段)。
- Collection: 逻辑表,如 "user_embeddings"。
- Shard: 按 ID 哈希分片,如 100 个 shard。
- Segment: shard 内的"段",每段 10-100 万向量,是索引构建和加载的最小单位。

**分片策略**:
- **哈希分片**(默认): `shard_id = hash(vector_id) % N_shards`,负载均衡好。
- **基于聚类分片**(进阶): 离线对向量聚类,语义相近的分到同 shard,查询时只扫相关 shard(剪枝)。
- **基于元数据分片**(业务): 按 tenant/category 分片,过滤下推到单 shard,减少 fan-out。

**2. 副本一致性**

**副本组 (Replica Group)**:
- 每个 shard 有 1 个 Leader + N 个 Follower(通常 N=2,共 3 副本)。
- Leader 负责写入,Follower 同步。

**一致性级别**(用户可选):

| 级别 | 机制 | 延迟 | 适用 |
|------|------|------|------|
| Strong | 写 Leader 后,等 Follower 同步完才返回 | 高 | 写后立即读 |
| Bounded | 读 Follower,允许滞后 N 秒 | 中 | 默认,大多数场景 |
| Eventually | 读任意副本,可能滞后 | 低 | 离线分析 |

**写入流程(强一致)**:
```
1. Client → Coordinator: 路由到 shard Leader
2. Leader → WAL: 写日志(顺序持久化)
3. Leader → Follower: 同步日志(Raft 协议)
4. Follower ACK → Leader
5. Leader → Client: 写入成功
6. 后台: Data Node 消费 WAL,构建 Segment → 索引
7. Query Node 加载新段,提供查询
```

**查询流程**:
```
1. Client → Coordinator: 路由到所有相关 shard
2. 各 shard: Leader 或 Follower 执行本地 ANN,返回 Top-K
3. Coordinator: 合并各 shard 结果,取全局 Top-K
4. Client: 收到结果
```

**3. 故障恢复**

**Query Node 故障**:
- Coordinator 检测心跳超时(如 30s)。
- 故障节点的 shard 副本转移到其他节点(从对象存储重新加载索引)。
- 如果 Leader 故障,从 Follower 选举新 Leader(Raft)。
- 恢复时间: 取决于索引大小,GB 级索引需 10-60s。

**Data Node 故障**:
- WAL 在消息队列中未消费,新 Data Node 接管后继续消费。
- 已持久化到对象存储的段不受影响。

**Coordinator 故障**:
- etcd 是 Raft 集群,自动选举。
- 元数据完整,查询路由短时间中断后恢复。

**对象存储故障**:
- S3/MinIO 通常多副本,数据不丢。
- 极端情况(整个对象存储挂),系统不可写但可读(内存索引仍在)。

**4. 写入即可见的挑战**

向量数据库的"写入即可见"比传统数据库难:
- 写入 → WAL → Segment → 索引构建 → 可查询,链路长。
- 索引构建异步(批量),用户写入后立即查询可能查不到。

**解决方案**:
- **Growing Segment**: 写入先进入"增长段"(无索引,暴力扫描),与"密封段"(有索引)合并查询。
- 增长段小(几万向量),暴力扫描仍快(<10ms)。
- 段密封后触发索引构建,完成后变为密封段。

**5. 容量规划**

**十亿向量规模估算**:
- 向量维度 D=768,float32,每向量 3KB。
- 原始数据: 10亿 * 3KB = 3TB
- HNSW 索引(2-3x 原始): 6-9TB
- PQ 量化(压缩 8x): 0.375TB(可放内存)
- 副本(3 副本): 总存储 30-90GB(量化后)~ 30TB(原始)

**节点规划**:
- Query Node: 64GB 内存 / 节点,加载量化索引(0.375TB / 3 副本 = 125GB),需 2-3 节点(每节点 60GB 索引)。
- 加上元数据、缓存,实际需 5-10 个 Query Node。
- Data Node: 主要 IO 密集,10 节点足够。

**6. 跨地域部署**

- 主集群写,异地区域异步同步(类似 CDC)。
- 异地查询走本地副本,延迟低。
- 故障时切换到异地区域(DR),RPO 取决于同步延迟(秒级)。

**面试加分点 — 一致性 vs 性能权衡**:

面试官问: "强一致写入会拖慢查询,如何平衡?"

- 强一致写入只影响"写后立即读"场景,实际业务可接受"最终一致"(几秒延迟)。
- 默认 Bounded Staleness: 读 Follower 允许滞后 5-10s,99% 业务可接受。
- 关键场景(如刚写入的知识立即检索)用 Strong 模式,牺牲延迟换一致。
- 进阶: 用"读自己的写"(Read Your Writes)一致性,Client 缓存自己写入的向量 ID,查询时本地合并,既快又准。

</details>

---

### Q9: 手撕代码 — 实现一个混合检索系统(向量检索 + BM25 + RRF 融合 + Reranker),Python 完整实现。

<details>
<summary>点击查看参考答案</summary>

**系统设计**:

```
Query
  ├── 向量检索 (Faiss HNSW) → Top-20
  ├── BM25 检索 (rank_bm25) → Top-20
  └── (可选)元数据过滤 → 应用 filter
       ↓
  RRF 融合 (k=60) → Top-50 候选
       ↓
  Reranker (Cross-Encoder) → Top-10 最终结果
       ↓
  返回
```

**依赖安装**:
```bash
pip install faiss-cpu rank-bm25 sentence-transformers numpy
```

**完整代码**:

```python
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Dict, Any, Optional
import time


class HybridRetriever:
    """
    混合检索系统: 向量检索 + BM25 + RRF 融合 + Reranker
    支持元数据过滤。
    """

    def __init__(
        self,
        embedding_model_name: str = "BAAI/bge-small-zh-v1.5",
        reranker_model_name: str = "BAAI/bge-reranker-base",
        faiss_index_type: str = "hnsw",
        hnsw_m: int = 16,
        hnsw_ef_construction: int = 200,
        hnsw_ef_search: int = 64,
        rrf_k: int = 60,
        use_reranker: bool = True,
    ):
        # 加载 Embedding 模型 (双塔,用于向量召回)
        self.embedder = SentenceTransformer(embedding_model_name)
        self.dim = self.embedder.get_sentence_embedding_dimension()

        # 加载 Reranker 模型 (Cross-Encoder, 用于精排)
        self.use_reranker = use_reranker
        if use_reranker:
            self.reranker = CrossEncoder(reranker_model_name)

        # Faiss 索引
        self.index_type = faiss_index_type
        self.hnsw_m = hnsw_m
        self.hnsw_ef_construction = hnsw_ef_construction
        self.hnsw_ef_search = hnsw_ef_search
        self._build_faiss_index()

        # BM25 索引 (初始化时为空, add_documents 后构建)
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []

        # 文档存储
        self.documents: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None

        # RRF 参数
        self.rrf_k = rrf_k

    def _build_faiss_index(self):
        """构建 Faiss 索引"""
        if self.index_type == "hnsw":
            self.index = faiss.IndexHNSWFlat(self.dim, self.hnsw_m)
            self.index.hnsw.efConstruction = self.hnsw_ef_construction
            self.index.hnsw.efSearch = self.hnsw_ef_search
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatIP(self.dim)
            nlist = 100  # 实际按 sqrt(N) 调
            self.index = faiss.IndexIVFFlat(quantizer, self.dim, nlist)
            self.index.nprobe = 10
            self.ivf_trained = False
        elif self.index_type == "flat":
            self.index = faiss.IndexFlatIP(self.dim)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """批量生成向量并 L2 归一化 (用于内积 = 余弦相似度)"""
        embs = self.embedder.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype(np.float32)
        return embs

    def add_documents(self, docs: List[Dict[str, Any]]):
        """
        增量添加文档。
        每个文档: {"id": str, "text": str, "metadata": {...}}
        """
        texts = [d["text"] for d in docs]
        new_embs = self._embed_texts(texts)

        # 写入 Faiss
        if self.index_type == "ivf" and not self.ivf_trained:
            # IVF 需先训练 (聚类), 数据量太少时退化为 Flat
            if len(self.documents) + len(docs) < 100:
                self.index = faiss.IndexFlatIP(self.dim)
                self.index_type = "flat"
            else:
                self.index.train(new_embs)
                self.ivf_trained = True
        self.index.add(new_embs)

        # 写入 BM25
        new_tokenized = [self._tokenize(t) for t in texts]
        self.tokenized_corpus.extend(new_tokenized)
        self.bm25 = BM25Okapi(self.tokenized_corpus)

        # 存储文档
        self.documents.extend(docs)
        if self.embeddings is None:
            self.embeddings = new_embs
        else:
            self.embeddings = np.vstack([self.embeddings, new_embs])

    def _tokenize(self, text: str) -> List[str]:
        """简单分词 (中文按字符,英文按空格; 生产环境用 jieba/HanLP)"""
        import re
        # 中文字符按字切,英文按词切
        tokens = re.findall(r"[\u4e00-\u9fa5]|[a-zA-Z0-9]+", text.lower())
        return tokens

    def vector_search(
        self,
        query: str,
        top_k: int = 20,
        filter_fn=None,
    ) -> List[Dict[str, Any]]:
        """向量检索,可选过滤"""
        query_emb = self._embed_texts([query])
        # 多取一些以应对 post-filter 损耗
        fetch_k = top_k * 5 if filter_fn else top_k
        distances, indices = self.index.search(query_emb, fetch_k)

        results = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            doc = self.documents[idx]
            if filter_fn and not filter_fn(doc["metadata"]):
                continue
            results.append({
                "doc": doc,
                "score": float(dist),
                "rank": rank + 1,
                "retriever": "vector",
            })
            if len(results) >= top_k:
                break
        return results

    def bm25_search(
        self,
        query: str,
        top_k: int = 20,
        filter_fn=None,
    ) -> List[Dict[str, Any]]:
        """BM25 检索,可选过滤"""
        if self.bm25 is None:
            return []
        tokens = self._tokenize(query)
        scores = self.bm25.get_scores(tokens)

        # 取 Top-N (考虑过滤)
        ranked_indices = np.argsort(scores)[::-1]
        results = []
        for rank, idx in enumerate(ranked_indices):
            if scores[idx] <= 0:
                break
            doc = self.documents[idx]
            if filter_fn and not filter_fn(doc["metadata"]):
                continue
            results.append({
                "doc": doc,
                "score": float(scores[idx]),
                "rank": rank + 1,
                "retriever": "bm25",
            })
            if len(results) >= top_k:
                break
        return results

    def rrf_fuse(
        self,
        result_lists: List[List[Dict[str, Any]]],
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """RRF (Reciprocal Rank Fusion) 融合多路检索结果"""
        scores_map: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        for results in result_lists:
            for r in results:
                doc_id = r["doc"]["id"]
                # RRF 公式: 1 / (k + rank)
                scores_map[doc_id] = scores_map.get(doc_id, 0) + \
                    1.0 / (self.rrf_k + r["rank"])
                doc_map[doc_id] = r["doc"]

        # 按 RRF 分数排序
        sorted_ids = sorted(scores_map.keys(), key=lambda x: scores_map[x], reverse=True)
        return [{
            "doc": doc_map[did],
            "rrf_score": scores_map[did],
        } for did in sorted_ids[:top_k]]

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Cross-Encoder Reranker 精排"""
        if not self.use_reranker or not candidates:
            return candidates[:top_k]

        pairs = [[query, c["doc"]["text"]] for c in candidates]
        scores = self.reranker.predict(pairs, batch_size=32)

        ranked = sorted(
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        return [{
            "doc": c["doc"],
            "rerank_score": float(s),
            "rrf_score": c.get("rrf_score", 0),
        } for c, s in ranked[:top_k]]

    def search(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
        filter_fn=None,
    ) -> Dict[str, Any]:
        """
        完整混合检索流程:
        1. 向量检索 + BM25 检索 (并行)
        2. RRF 融合
        3. Reranker 精排
        """
        t0 = time.time()

        # Step 1: 多路召回 (实际可 asyncio 并行)
        vec_results = self.vector_search(query, top_k=candidate_k, filter_fn=filter_fn)
        bm25_results = self.bm25_search(query, top_k=candidate_k, filter_fn=filter_fn)

        # Step 2: RRF 融合
        fused = self.rrf_fuse([vec_results, bm25_results], top_k=candidate_k * 2)

        # Step 3: Reranker 精排
        final = self.rerank(query, fused, top_k=top_k)

        return {
            "query": query,
            "results": final,
            "stats": {
                "vector_hits": len(vec_results),
                "bm25_hits": len(bm25_results),
                "fused_candidates": len(fused),
                "final_results": len(final),
                "latency_ms": (time.time() - t0) * 1000,
            },
        }


# ============ 测试 Demo ============
def demo():
    # 1. 准备语料
    documents = [
        {"id": "1", "text": "Python 是一种广泛使用的高级编程语言,由 Guido van Rossum 创建",
         "metadata": {"category": "编程", "lang": "python"}},
        {"id": "2", "text": "Java 是一种面向对象的编程语言,广泛应用于企业级开发",
         "metadata": {"category": "编程", "lang": "java"}},
        {"id": "3", "text": "向量数据库用于存储和检索高维向量,是 RAG 系统的核心组件",
         "metadata": {"category": "AI", "lang": ""}},
        {"id": "4", "text": "HNSW 是一种基于图的近似最近邻索引算法,具有高召回率和低延迟",
         "metadata": {"category": "AI", "lang": ""}},
        {"id": "5", "text": "Python 的 pandas 库是数据分析的利器,支持 DataFrame 操作",
         "metadata": {"category": "编程", "lang": "python"}},
        {"id": "6", "text": "Milvus 是一款开源的分布式向量数据库,支持十亿级向量检索",
         "metadata": {"category": "AI", "lang": ""}},
        {"id": "7", "text": "BM25 是一种基于词频的文本检索算法,对关键词查询效果好",
         "metadata": {"category": "检索", "lang": ""}},
        {"id": "8", "text": "Reranker 使用 Cross-Encoder 对候选结果精排,提升最终效果",
         "metadata": {"category": "检索", "lang": ""}},
    ]

    # 2. 初始化检索器
    retriever = HybridRetriever(
        embedding_model_name="BAAI/bge-small-zh-v1.5",
        reranker_model_name="BAAI/bge-reranker-base",
        faiss_index_type="hnsw",
        use_reranker=True,
    )
    retriever.add_documents(documents)

    # 3. 测试查询
    queries = [
        "Python 数据分析",
        "向量检索算法",
        "BM25 文本搜索",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"Query: {q}")
        print(f"{'='*60}")

        # 无过滤
        result = retriever.search(q, top_k=3)
        print(f"\n[无过滤] 延迟: {result['stats']['latency_ms']:.1f}ms")
        for r in result["results"]:
            print(f"  - [{r['rerank_score']:.4f}] {r['doc']['text'][:50]}")

        # 带过滤: 只看 AI 类别
        result_filtered = retriever.search(
            q, top_k=3,
            filter_fn=lambda m: m.get("category") == "AI",
        )
        print(f"\n[过滤 category=AI] 延迟: {result_filtered['stats']['latency_ms']:.1f}ms")
        for r in result_filtered["results"]:
            print(f"  - [{r['rerank_score']:.4f}] {r['doc']['text'][:50]}")


if __name__ == "__main__":
    demo()
```

**输出示例**(实际分数因模型版本而异):

```
============================================================
Query: Python 数据分析
============================================================

[无过滤] 延迟: 187.3ms
  - [0.9821] Python 的 pandas 库是数据分析的利器,支持 DataFrame 操作
  - [0.9234] Python 是一种广泛使用的高级编程语言,由 Guido van Rossum 创建
  - [0.7654] Java 是一种面向对象的编程语言,广泛应用于企业级开发

[过滤 category=AI] 延迟: 192.1ms
  - [0.8123] 向量数据库用于存储和检索高维向量,是 RAG 系统的核心组件
  - [0.7892] HNSW 是一种基于图的近似最近邻索引算法,具有高召回率和低延迟
```

**关键设计点**:

1. **向量检索用 HNSW + 内积(L2 归一化后 = 余弦)**: 兼顾速度和精度。
2. **BM25 用 rank-bm25 库**: 纯 Python 实现,生产可换 Elasticsearch。
3. **RRF 融合**: 不需分数归一化,只看 rank,鲁棒。
4. **Reranker 用 Cross-Encoder**: 比 Bi-Encoder 精度高,但慢(候选少时用)。
5. **过滤函数 `filter_fn`**: 灵活支持任意元数据条件。
6. **post-filter + fetch_k 扩大**: 取 `top_k * 5` 应对过滤损耗,避免结果不足。
7. **延迟统计**: 便于优化,生产应分阶段统计(向量召回 / BM25 / RRF / Reranker 各占多少)。

**生产化改进方向**:

- **并行召回**: 用 `asyncio` 并行执行向量检索和 BM25,延迟由慢路径决定。
- **BM25 换 ES**: rank-bm25 是纯 Python,百万文档以上慢,换 Elasticsearch。
- **Embedding 缓存**: 高频 query 的 embedding 用 Redis 缓存,省 API 调用。
- **增量更新**: 当前实现每次 add_documents 都重建 BM25,生产需支持增量。
- **Faiss GPU**: 亿级数据用 `faiss-gpu`,HNSW 构建快 10-100x。

</details>

---

### Q10: 系统设计 — 设计一个支持十亿级向量检索的系统,要求 P99 延迟 <100ms、可用性 99.9%、成本可控。

<details>
<summary>点击查看参考答案</summary>

**需求拆解**:

| 指标 | 目标 | 隐含约束 |
|------|------|---------|
| 数据量 | 10 亿向量 | D=768, 原始 3TB,HNSW 索引 ~9TB |
| 查询 P99 | <100ms | 含 Embedding 计算 + 检索 + Rerank |
| 可用性 | 99.9% | 年停机 <8.76 小时 |
| 写入 TPS | 1万/秒 | 增量更新 |
| 成本 | 可控 | 内存型 vs 磁盘型权衡 |

**1. 总体架构**

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│  (限流 / 鉴权 / Embedding Cache)                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Query Coordinator                           │
│  (查询路由 / Scatter-Gather / 结果合并)                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Shard 1     │   │  Shard 2     │   │  Shard N     │
│  (Leader)    │   │  (Leader)    │   │  (Leader)    │
│  + Replica   │   │  + Replica   │   │  + Replica   │
│  HNSW + PQ   │   │  HNSW + PQ   │   │  HNSW + PQ   │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            Object Storage (S3) + WAL (Kafka)                 │
│  (持久化段文件 / 索引文件 / 写入日志)                          │
└─────────────────────────────────────────────────────────────┘
```

**2. 分片策略**

**核心决策: 分片数 = 100,每分片 1000 万向量**

理由:
- 单分片 1000 万 * 768 * 4B = 30GB(原始),HNSW 索引 ~90GB。
- PQ 量化后: 30GB / 8 = 3.75GB(可常驻内存)。
- 单 Query Node 加载 2-3 个分片,内存 64GB 足够。
- 100 分片 / 3 副本 = 300 副本,分布在 30-50 个 Query Node。

**分片方式**:
- **第一阶段(默认)**: 哈希分片 `shard = hash(id) % 100`,简单均衡。
- **第二阶段(优化)**: 离线对向量做 K-Means 聚类(100 类),语义相近的进同分片。查询时只扫与 query 最近的 10-20 个分片(剪枝),fan-out 减少 5-10x。

**3. 索引选型**

**核心: HNSW + PQ + Refine**

```
索引层级:
├── 内存层 (热数据)
│   ├── PQ 量化向量 (8x 压缩) → 用于 HNSW 距离计算
│   └── HNSW 图结构 → 导航
└── 磁盘层 (冷数据 / Refine)
    └── 原始 float32 向量 → Top-K 候选精排
```

**为什么不用纯 DiskANN?**
- DiskANN 适合"内存放不下"的超大规模(百亿级),十亿级用 HNSW+PQ 内存够。
- DiskANN 随机读磁盘,SSD 也比内存慢 100x,P99 难保证。
- HNSW+PQ 全内存,延迟稳定 <50ms。

**参数选择**:
- M=16, efConstruction=400(一次性构建,质量优先)
- efSearch=64(动态调整,根据负载)
- PQ m=96(768 维 / 8 = 96 子向量,每子向量 1 字节)

**4. 查询流程**

```
1. Client → API Gateway: query text
2. Gateway: 查 Embedding Cache (Redis)
   ├── 命中: 直接拿向量
   └── 未命中: 调 Embedding API (50-200ms) + 写缓存
3. Coordinator: 路由到所有分片 (或剪枝后的 10-20 个)
4. 各分片并行:
   a. HNSW 遍历 (用 PQ 距离) → Top-50 候选
   b. 候选 ID → 磁盘读原始向量 → Refine 精排 → Top-20
   c. 返回 Top-20
5. Coordinator: 合并各分片 Top-20 → 全局 Top-50
6. (可选) Reranker: Cross-Encoder 精排 → Top-10
7. 返回 Client
```

**延迟分解(P99 目标 100ms)**:

| 阶段 | 延迟 | 优化 |
|------|------|------|
| Embedding (缓存命中) | 1ms | Redis LRU |
| Embedding (未命中) | 80ms | 本地部署 Embedding 模型 |
| Coordinator 路由 | 2ms | - |
| 分片查询 (HNSW+PQ) | 15ms | 全内存 |
| Refine (磁盘读) | 20ms | SSD + 预读 |
| Scatter-Gather 网络 | 10ms | 同机房 |
| Rerank (Cross-Encoder) | 30ms | GPU 批量 |
| **总计 (缓存命中 + 无 Rerank)** | **~50ms** | - |
| **总计 (缓存未命中 + Rerank)** | **~150ms** | 需优化 |

**降级策略**:
- Embedding 未命中且延迟敏感: 用轻量模型(如 MiniLM)替代,40ms → 15ms。
- Rerank 慢: 候选数减到 20,或跳过 Rerank 用 RRF 融合分数。

**5. 写入流程**

```
1. Client → API Gateway: batch insert (1000 条)
2. Gateway → WAL (Kafka): 顺序写日志 (<1ms)
3. WAL 消费者 (Data Node):
   a. 攒批到 Segment (10万向量)
   b. 构建 HNSW 索引 + PQ 量化
   c. 上传到 S3
4. Query Node: 加载新 Segment 到内存
5. Client 可查询 (写入可见延迟 5-30s)
```

**6. 高可用与容灾**

**99.9% 可用性 = 月停机 <43 分钟**

**单点故障应对**:
- Coordinator: Raft 3 节点,1 故障不影响。
- Query Node: 每分片 3 副本,1 故障仍 2 副本可用。
- Kafka: 3 副本,1 故障不影响。
- S3: 11 个 9 持久性,几乎不丢数据。

**故障切换时间**:
- Query Node 故障: 30s 心跳超时 + 60s 索引重加载 = 90s
- 每月故障次数: 30 节点 * 0.5 故障/月 = 15 次
- 总停机: 15 * 90s / 3 (副本分担) = 450s ≈ 7.5 分钟 < 43 分钟 ✓

**跨地域容灾**:
- 主集群(北京)+ DR 集群(上海)
- 异步同步: Kafka MirrorMaker,延迟 1-5s
- DR 切换: RPO <10s,RTO <5 分钟

**7. 成本估算**

**内存型方案(HNSW+PQ 全内存)**:

| 资源 | 数量 | 规格 | 月成本(估算) |
|------|------|------|--------------|
| Query Node | 30 | 64GB 内存, 16 核 | 30 * $300 = $9000 |
| Data Node | 10 | 32GB 内存, 8 核, 1TB SSD | 10 * $200 = $2000 |
| Coordinator | 3 | 16GB 内存, 4 核 | 3 * $100 = $300 |
| Kafka | 3 | 32GB 内存, 1TB | 3 * $150 = $450 |
| S3 | - | 10TB 索引 + 3TB 原始 | ~$300 |
| **总计** | | | **~$12000/月** |

**磁盘型方案(DiskANN,成本减半但延迟翻倍)**:

| 资源 | 数量 | 规格 | 月成本 |
|------|------|------|--------|
| Query Node | 15 | 32GB 内存, 4TB NVMe SSD | 15 * $250 = $3750 |
| 其他同上 | | | ~$3000 |
| **总计** | | | **~$6750/月** |

**选型**: 如果 SLA 要求 P99 <100ms,选内存型;若能接受 P99 <200ms,磁盘型省 40%。

**8. 监控与运维**

**关键指标**:
- 查询: P50/P95/P99 延迟、QPS、错误率
- 写入: TPS、WAL 积压、索引构建延迟
- 系统: 内存利用率、CPU、磁盘 IO、网络
- 业务: Recall@K (定期离线评估)、缓存命中率

**告警阈值**:
- P99 > 80ms(预警)/ > 120ms(告警)
- 内存 > 85%(预警)/ > 95%(告警)
- Recall@10 < 95%(告警)
- 副本数 < 2(告警)

**9. 扩展性**

**横向扩展**:
- 数据增长 → 增加 Query Node,自动再平衡分片。
- QPS 增长 → 增加副本数,读负载分担。

**纵向优化**:
- 向量维度从 768 降到 512(PCA 降维),内存省 33%,延迟降 20%。
- 量化从 PQ 换 OPQ,召回提升 3-5%。
- Embedding 模型升级(如 bge-large),召回提升但延迟增加。

**10. 面试加分点 — 追问应对**

**Q: 如何应对"写入突发流量"?**
- WAL(Kafka)削峰: 写入只入日志,后台消费构建索引。
- 限流: Gateway 层限流,保护 Embedding API 和 Data Node。
- 弹性扩容: Data Node 自动扩容,加快索引构建。

**Q: 如何保证 Recall 不下降?**
- 每日离线评估: 1000 条标注 query,计算 Recall@10。
- 数据漂移检测: 新数据分布与历史差异大时,触发索引重建。
- A/B 测试: 新参数(如 efSearch)灰度上线,对比 Recall。

**Q: 如果向量需要频繁更新(如用户画像)?**
- HNSW 增量插入,但删除需软删除 + 定期 Compact。
- 用户画像场景: 按 user_id 分片,单用户向量更新只影响一个分片。
- 版本化: 保留 N 个版本向量,支持回滚。

**Q: 多租户如何隔离?**
- 方案 1: 每租户独立 Collection(强隔离,资源浪费)。
- 方案 2: 共享 Collection,metadata.tenant_id 过滤(高效,需过滤下推)。
- 方案 3: 大租户独立,小租户共享(混合)。

</details>

---

## 核心知识回顾表

| 知识点 | 核心内容 | 关键参数/指标 | 易忘点 |
|--------|---------|--------------|--------|
| 向量数据库核心需求 | ANN检索+持久化+过滤+分布式+CRUD | Recall@K, P99延迟 | 区别于传统数据库:相似度vs精确匹配 |
| 主流方案对比 | Pinecone/Milvus/Weaviate/Qdrant/Chroma/pgvector | 选型:规模/过滤复杂度/团队能力 | Qdrant过滤下推最强,Milvus唯一工业级十亿开源 |
| HNSW原理 | 多层小世界图,上层稀疏导航,下层密集搜索 | M(16-48), efConstruction(200-500), efSearch(50-200) | efSearch是运行时主旋钮;M改需重建索引 |
| IVF原理 | K-Means聚类倒排,查询只扫nprobe个桶 | nlist≈sqrt(N), nprobe≈nlist/100 | IVF-PQ压缩16x但召回降5-15% |
| 量化技术 | PQ/SQ/Binary/OPQ | PQ: 8-32x压缩, SQ: 4x, Binary: 32x | 多级级联:Binary粗筛+PQ精筛+原始Refine |
| 混合检索 | 向量+BM25+过滤,RRF融合 | RRF: 1/(k+rank), k=60 | Pre-filter全局最优,Post-filter可能不足K |
| 过滤下推 | filter下推到HNSW遍历 | Qdrant/Milvus2.x支持 | 遍历跳过不满足节点,继续扩展邻居 |
| 性能优化 | 分片+副本+批量写+缓存 | 单分片<1000万,批量1000-10000 | Embedding Cache价值最大(省API调用) |
| 分布式架构 | Coordinator+QueryNode+DataNode+WAL+S3 | 副本3, Quorum W+R>N | 写入即可见用Growing Segment(暴力扫描) |
| RRF融合 | 倒数排名融合,不需分数归一化 | k=60(经验值) | 只用rank,对异常分数鲁棒 |
| Reranker | Cross-Encoder精排,比Bi-Encoder精 | 候选Top-50→精排Top-10 | 慢,候选少时用;可跳过用RRF分数降级 |

---

## 面试速记卡

**30秒电梯陈述**:
> 向量数据库是RAG系统的核心存储,核心需求是ANN近似最近邻检索+元数据过滤+分布式扩展。选型上,小规模用pgvector/Chroma,中等规模用Qdrant(过滤下推强),十亿级用Milvus。索引算法主流是HNSW(图导航,高召回低延迟,内存大)和IVF(聚类倒排,配合PQ压缩)。混合检索用向量+BM25+RRF融合+Reranker精排,过滤下推到HNSW可避免post-filter结果不足问题。十亿级系统设计核心是:分片100*1000万、HNSW+PQ+Refine三段式、3副本Quorum、WAL削峰。

**高频追问应对**:

| 追问 | 一句话回答 |
|------|----------|
| HNSW为什么快? | 多层图导航,每步贪心向更近节点移动,路径长度O(log N) |
| HNSW和IVF怎么选? | 内存充足选HNSW(快),内存受限选IVF-PQ(省) |
| PQ为什么精度损失比SQ大? | PQ切分子向量丢失相关性,SQ逐维量化误差可控 |
| RRF为什么用rank不用score? | 向量距离和BM25分数尺度不同,rank归一化鲁棒 |
| post-filter为什么结果不足? | ANN Top-K是全局相似,过滤后可能只剩几条,非过滤后全局最优 |
| 十亿级怎么部署? | 100分片*1000万,30个Query Node,HNSW+PQ全内存,P99<100ms |
| 向量数据库的ACID? | 大多数弱化ACID,强调最终一致+高可用;Milvus支持强/有界/最终三档 |
| 删除怎么做? | 软删除(tombstone)+定期Compact全量重建 |

**调参口诀**:
- HNSW: **先efConstruction(大),再efSearch(调),最后M(重建)**
- IVF: **nlist=sqrt(N), nprobe二分搜索到Recall达标**
- PQ: **m=D/4起步,配合Refine免费提升召回**

---

## 易错点提醒(10 个)

1. **混淆 Recall@K 和 Precision@K**:
   - Recall@K = 返回的 Top-K 中正确的 / 全集正确的总数
   - 向量检索关注 **Recall@K**(召回率),不是 Precision
   - 易错: 说"HNSW 精度 95%" 应明确是 "Recall@10 = 95%"

2. **HNSW 的 M 改了不重建索引会失效**:
   - M 决定图结构,改了必须重建
   - efSearch 运行时可调,无需重建
   - 易错: 以为调 M 和调 efSearch 一样轻量

3. **L2 归一化后内积 = 余弦相似度**:
   - 不归一化直接用内积(IP)是错的,数值大的向量会"霸榜"
   - 余弦相似度 = 归一化后的 IP
   - 易错: Faiss 用 `IndexFlatIP` 但忘记 `normalize_embeddings=True`

4. **post-filter 不是"全局最优"**:
   - ANN 取 Top-100 是全局最相似的 100 条
   - 过滤后剩余的 10 条**不是**"满足条件的全局最相似 10 条"
   - 易错: 以为 post-filter 结果等同 pre-filter

5. **RRF 的 k 不是 Top-K 的 K**:
   - RRF 公式 `1/(k+rank)`,k 是平滑常数(通常 60)
   - Top-K 的 K 是返回数量(如 10)
   - 易错: 把 RRF 的 k 设成 10,导致排名差异被放大

6. **IVF 训练和构建是两步**:
   - 训练: 对数据做 K-Means 得到 nlist 个质心
   - 构建: 把每个向量分配到质心
   - 易错: 以为 `index.add()` 自动训练,IVF 需先 `index.train()`

7. **PQ 的 m 必须能整除维度 D**:
   - m 是子向量数,每子向量 D/m 维
   - D=768, m=96 可以; D=768, m=100 不行(7.68 维)
   - 易错: 随意设 m 导致维度不整除

8. **向量数据库的"写入即可见"不保证**:
   - 写入 → WAL → Segment → 索引构建 → 可查询,链路长
   - 立即查询可能查不到(Milvus 默认有界一致,滞后几秒)
   - 易错: 以为写入成功就能立即查到,需用强一致模式或 Growing Segment

9. **Embedding 维度变化需重建索引**:
   - 换 Embedding 模型(如 bge-small → bge-large)维度可能变
   - 维度变了 Faiss 索引必须重建
   - 易错: 热切换 Embedding 模型但没重建索引,查询报错

10. **二值化适合长向量,短向量精度崩**:
    - 1536 维 OpenAI 向量二值化效果尚可
    - 384 维以下二值化 Recall 暴跌
    - 易错: 以为二值化"万能压缩",对短向量也用

---

## 自测检查清单

### 概念题(10 个)

- [ ] 1. 能说出向量数据库与传统数据库的 3 个本质区别?
- [ ] 2. 能列出 6 种主流向量数据库并说明各自适用场景?
- [ ] 3. 能画出 HNSW 的多层图结构并解释查询过程?
- [ ] 4. 能说出 HNSW 三个核心参数的典型值和调优顺序?
- [ ] 5. 能解释 IVF-Flat 和 IVF-PQ 的区别及选择依据?
- [ ] 6. 能写出 RRF 融合公式并说明为什么用 rank 不用 score?
- [ ] 7. 能区分 pre-filter、post-filter、过滤下推的效果差异?
- [ ] 8. 能说出 PQ/SQ/Binary 三种量化的压缩率和精度损失?
- [ ] 9. 能画出分布式向量数据库的架构图(5 个核心组件)?
- [ ] 10. 能解释"写入即可见"的挑战和 Growing Segment 方案?

### 代码题(3 个)

- [ ] 1. 能手写 RRF 融合函数(输入多路检索结果,输出融合排名)?
- [ ] 2. 能用 Faiss 实现 HNSW 索引的构建和查询(含参数设置)?
- [ ] 3. 能实现一个完整的混合检索类(向量+BM25+RRF+Reranker+过滤)?

### 系统设计题(2 个)

- [ ] 1. 能设计十亿级向量检索系统(分片/索引/查询路由/容灾/成本)?
- [ ] 2. 能针对"查询 P99 突然上升到 100ms"给出排查思路?

---

## 延伸阅读

**论文**:
- *Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs* (Malkov & Yashunin, HNSW 原论文, 2016)
- *Product Quantization for Nearest Neighbor Search* (Jégou et al., PQ 原论文, 2011)
- *DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node* (Subramanya et al., DiskANN, 2019)
- *Accelerating Large-Scale Inference with Anisotropic Vector Quantization* (Guo et al., ScaNN, 2020)

**开源项目**:
- [Faiss](https://github.com/facebookresearch/faiss) — Meta 的向量检索库,索引算法最全
- [Milvus](https://github.com/milvus-io/milvus) — 工业级分布式向量数据库
- [Qdrant](https://github.com/qdrant/qdrant) — Rust 实现,过滤下推强
- [hnswlib](https://github.com/nmslib/hnswlib) — HNSW 的参考实现,轻量易读
- [ann-benchmarks](https://github.com/erikbern/ann-benchmarks) — ANN 算法基准测试

**博客/文档**:
- [Milvus 官方文档 — Index Types](https://milvus.io/docs/index.md)
- [Qdrant 官方文档 — Filtering](https://qdrant.tech/documentation/filtering/)
- [Pinecone — Learning Center](https://www.pinecone.io/learn/)
- [Zilliz — Vector Search Field Guide](https://zilliz.com/learn)

**面试相关**:
- [向量数据库面试题汇总 — 掘金](https://juejin.cn/)
- [AI Agent 面试冲刺 — 本系列其他 Day](.)

---

## 明日预告

**Day 11 — Context-Engineering: 上下文工程**

Day10 我们深入了向量数据库的"存储和检索"环节。但 RAG 的核心不止是"召回",更是"如何把召回的内容组织成 LLM 能高效利用的上下文"。

明日将聚焦:
1. **Context Window 管理**: 长上下文模型的挑战(注意力衰减、Lost in the Middle)
2. **上下文压缩**: 摘要式压缩、抽取式压缩、LLMLingua 等方案
3. **上下文排序**: 重要的放前面还是后面?Reorder 策略
4. **Few-Shot 选择**: 动态挑选最相关示例(ICL, In-Context Learning)
5. **多轮对话上下文管理**: 滑动窗口、摘要记忆、向量记忆
6. **Agent 的上下文工程**: 工具描述、观察历史、ReAct 轨迹压缩

**预习建议**:
- 阅读 *Lost in the Middle: How Language Models Use Long Contexts* (Liu et al., 2023)
- 思考: 为什么把最相关的文档放在中间反而被忽略?

---

> **学习建议**: Day10 内容密集,建议分两次学。第一次过概念(Q1-Q8),第二次动手敲代码(Q9)和画系统架构图(Q10)。代码题务必运行一遍,加深对 Faiss/HNSW/RRF 的体感。
