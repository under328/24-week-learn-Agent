# Day 31 — 真实项目实战经验面试题

> **学习目标**: 训练面试者回答"你在实际项目中遇到过什么问题、怎么解决的"。这一天不再是纯理论考察,而是经验型问题的深度演练。面试官想听到的不是"RAG 是检索增强生成",而是"我在某次 RAG 项目里,因为 chunk 切分粒度问题导致召回率从 72% 掉到 41%,后来通过……"这种带血泪经验的故事。
>
> **适用人群**: 有过 Agent/RAG/LLM 应用项目经验的候选人(哪怕是 demo 级项目,也要能讲出工程化思考)。
>
> **今日时长**: 建议 4-5 小时,10 道题逐道打磨自己的"项目故事库"。
>
> **核心心法**: 面试官考察实战经验时,本质是在问三件事 —— ①你有没有真正做过(区分"看过论文"和"踩过坑"); ②你做的深度如何(区分"调 API"和"做工程"); ③你能不能反思和复盘(区分"做完就忘"和"沉淀方法论")。

---

## 今日知识图谱

下面这张 ASCII 树状图展示了 Agent 项目全生命周期,以及每个阶段最容易被面试官追问的考点。建议先整体扫一遍,理解"一个真实项目从 0 到 1 再到持续运营"的全貌,再逐题对照自己的项目经历。

```
Agent 项目全生命周期
│
├── 1. 需求澄清阶段 (Day 1-7)
│   ├── 业务场景拆解 ──── 考点: 你怎么判断"该不该用 Agent"? (Q1, Q10)
│   ├── ROI 预估 ─────── 考点: 怎么算清这笔账? (Q5)
│   ├── 边界与降级 ───── 考点: Agent 做不了的事怎么兜底? (Q1, Q8)
│   └── 里程碑规划 ───── 考点: 30/60/90 天计划合理性 (Q10)
│
├── 2. 技术选型阶段 (Day 3-10)
│   ├── 框架选型 ─────── 考点: LangChain / LlamaIndex / 自研, 为什么? (Q3)
│   ├── 模型选型 ─────── 考点: GPT-4 / 开源模型 / 混合路由, 成本 vs 效果 (Q3, Q5)
│   ├── 向量库选型 ───── 考点: Milvus / Qdrant / pgvector, 选型依据 (Q3)
│   └── 评估方案 ─────── 考点: 用什么指标? 怎么搭评估集? (Q5)
│
├── 3. 数据建设阶段 (Day 5-20) ★ 最容易翻车
│   ├── 知识库构建 ───── 考点: 文档清洗 / chunk 策略 / 元数据 (Q4)
│   ├── 数据质量治理 ─── 考点: 怎么发现脏数据? 怎么持续治理? (Q4)
│   ├── 评估集搭建 ───── 考点: golden set 怎么来? 多少条够? (Q5)
│   └── 数据安全合规 ─── 考点: 敏感数据脱敏 / 权限隔离 (Q4)
│
├── 4. 核心开发阶段 (Day 10-40)
│   ├── 检索增强 (RAG) ── 考点: chunk 切分 / hybrid search / rerank (Q1, Q2, Q9A)
│   ├── Agent 决策引擎 ── 考点: ReAct / Plan-Execute / 工具调用 (Q9B)
│   ├── Multi-Agent ──── 考点: 角色划分 / 通信协议 / 状态同步 (Q9C)
│   ├── Prompt 工程 ──── 考点: 怎么迭代 prompt? 怎么版本管理? (Q1, Q7)
│   └── 可观测性 ─────── 考点: trace / metrics / log 三件套 (Q2, Q7)
│
├── 5. 测试评估阶段 (Day 30-50)
│   ├── 离线评估 ─────── 考点: 准确率 / 召回率 / 端到端指标 (Q5)
│   ├── 在线 A/B ─────── 考点: 实验设计 / 流量切分 / 显著性 (Q5, Q7)
│   ├── 红队测试 ─────── 考点: 注入攻击 / 越狱 / 幻觉触发 (Q2)
│   └── 压力测试 ─────── 考点: QPS / 延迟 / 成本上限 (Q2)
│
├── 6. 上线部署阶段 (Day 45-60)
│   ├── 灰度发布 ─────── 考点: 怎么从小流量到全量? (Q1, Q2)
│   ├── 降级兜底 ─────── 考点: 模型挂了怎么办? 检索空了怎么办? (Q2)
│   ├── 成本控制 ─────── 考点: token 预算 / 缓存策略 / 模型路由 (Q5)
│   └── 监控告警 ─────── 考点: 哪些指标要告警? 阈值怎么定? (Q2, Q7)
│
├── 7. 运营迭代阶段 (Day 60+) ★ 长期价值
│   ├── 用户反馈闭环 ─── 考点: 怎么收集 bad case? 怎么回流? (Q7)
│   ├── 模型版本管理 ─── 考点: 模型升级怎么做回滚? (Q7)
│   ├── 持续优化机制 ─── 考点: 迭代节奏 / 效果追踪 (Q7)
│   └── 业务价值复盘 ─── 考点: ROI 真实核算 / 边际收益 (Q5)
│
└── 8. 团队协作贯穿全程
    ├── 角色分工 ─────── 考点: Agent 开发需要哪些角色? (Q6)
    ├── 跨职能沟通 ──── 考点: 和产品/业务/算法怎么对齐? (Q6, Q8)
    └── 冲突处理 ─────── 考点: 技术分歧怎么决策? (Q8)

★ 标记的是面试中最容易拉开差距的环节 —— 多数候选人只讲"我用了 X 技术",
  少数候选人能讲"我在 X 环节踩过 Y 坑,沉淀了 Z 方法论"。
```

---

## 面试题(共 10 道)

> **答题建议**: 每道题先自己口头答一遍(录音),再对照"加分回答"找差距。重点不是背答案,而是把"项目故事库"打磨到能脱口而出。建议每道题准备 2-3 个真实案例(不同项目),根据面试官追问方向灵活调用。

---

### Q1: 你在 RAG 项目中,从需求到上线完整经历了哪些阶段? 每个阶段最大的坑是什么?

<details>
<summary>点击展开答案</summary>

**问题背景**

这是一道"开场必问"题,面试官想通过你对项目全流程的描述,判断你是"做过完整项目"还是"只做了某一段"。坑点问得越具体,越能区分"真做过"和"看过教程"。这道题答好了,后续追问会顺着你提到的坑深挖,所以讲故事时要"埋钩子"——提到某个坑但不要全讲完,等面试官追问。

**常见回答(及格线)**

> "我们做了一个企业知识库问答项目。需求是让员工能查公司文档。我负责 RAG 部分,用 LangChain + Milvus + GPT-4,把文档切片存向量库,用户提问时检索 top-5 拼到 prompt 里给 GPT-4 生成答案。上线后效果还行,准确率大概 80%。"

这个回答的问题:①没有阶段划分; ②没说坑; ③"准确率 80%"怎么来的没说; ④"效果还行"是模糊描述。面试官听完只会觉得你是个执行者,不是主导者。

**加分回答(80 分以上)**

按"需求 → 数据 → 检索 → 生成 → 评估 → 上线"六阶段讲,每阶段带一个具体坑:

> **阶段 1: 需求澄清(2 周)**
> 最大的坑是"业务方以为 RAG 是万能的"。我们最初接到需求是"做一个能回答所有公司问题的机器人",后来花了 1 周和业务方一起把问题分类,发现 60% 是 FAQ 类(直接走知识库精准匹配),30% 是文档检索类(走 RAG),10% 是需要多文档推理的(走 Agent + 多轮检索)。如果一上来就全走 RAG,既慢又贵还容易幻觉。
> **坑**: 需求边界没谈清,导致第一版做了个"四不像"。
> **复盘**: 现在我做需求澄清时,一定让业务方给 50 个真实问题样本,按问题类型分类后,再决定每类用什么技术方案。

> **阶段 2: 数据建设(3 周)**
> 最大的坑是"chunk 切分粒度"。我们最初按固定 512 token 切,结果发现表格、代码块被切烂,召回的内容是半截的。后来改成"按结构切分"——markdown 按标题层级,PDF 用 layout 解析,代码按函数边界。还加了 overlap 50 token 防止边界信息丢失。
> **坑**: 切分策略直接决定召回质量,但很多人只调 embedding 模型不调切分。
> **复盘**: 我们做了一个"chunk 可视化工具",能高亮显示每个 chunk 的边界,方便人工抽检。这个工具后来成了团队标准件。

> **阶段 3: 检索优化(2 周)**
> 最大的坑是"纯向量检索召回不全"。用户问"去年 Q3 的财报",向量检索召回的是"今年 Q3 的财报"(语义相似但时间不对)。后来加了元数据过滤(时间范围) + BM25 关键词检索,做 hybrid search,rerank 用 bge-reranker。召回率从 72% 提到 89%。
> **坑**: 向量检索擅长语义匹配,但精确匹配(数字、日期、专有名词)反而不如 BM25。

> **阶段 4: 生成优化(1 周)**
> 最大的坑是"prompt 里塞太多 context 反而降低效果"。我们最初把 top-10 检索结果全塞进去,结果 GPT-4 会被无关内容带偏,出现"幻觉式引用"。后来改成: top-3 + 每条加来源标注 + 明确告诉模型"如果信息不足以回答,就说不知道"。
> **坑**: context 不是越多越好,信噪比比信息量更重要。

> **阶段 5: 评估(2 周)**
> 最大的坑是"没有评估集就上线"。我们第一版直接灰度给 20 个用户,结果 bad case 一堆却没法量化。后来花了 1 周让业务专家标注 200 条 golden set,覆盖常见问题、边界问题、对抗问题三类。之后每次迭代都能用这套评估集回归。
> **坑**: 评估集是 RAG 项目的"地基",但很多人图快跳过这步。

> **阶段 6: 上线(1 周)**
> 最大的坑是"成本超预算"。上线第一天 token 消耗是预估的 3 倍,因为很多用户问重复问题。紧急加了语义缓存(Similarity Cache, 相似度 > 0.95 直接返回缓存答案),成本降了 60%。
> **坑**: 不做缓存,RAG 的边际成本会吃掉所有利润。

**追问应对**

- **追问 1: "你说召回率从 72% 到 89%,这个召回率怎么算的?"**
  答: 我们用 200 条 golden set,每条标注了"正确答案应该来自哪些文档片段"。检索结果命中正确片段的比例就是召回率。具体公式: Recall = 命中的正确片段数 / 应该命中的片段总数。我们还会看 Recall@5 和 Recall@10,因为最终只用 top-k。

- **追问 2: "chunk 可视化工具是你自己做的吗? 用什么技术栈?"**
  答: 是我主导做的,Python + Streamlit。核心逻辑是: 加载文档 → 按切分策略生成 chunk → 在前端高亮显示每个 chunk 的起止位置 → 支持人工标注"这个 chunk 切得好不好"。标注结果会回写到评估集。这个工具现在是我们团队 RAG 项目的标配。

- **追问 3: "如果重新做这个项目,你会怎么改?"**
  答: 三点: ①需求阶段就引入评估集设计,而不是到阶段 5 才补; ②数据建设阶段就用上 LLM-as-judge 做自动评估,减少人工标注量; ③上线前做一次完整的红队测试,我们当时上线后第二周才被用户发现一个 prompt 注入漏洞。

</details>

---

### Q2: 你的 RAG 系统线上出现过什么故障? 如何排查和修复的?

<details>
<summary>点击展开答案</summary>

**问题背景**

这是一道"高 P 杀手题"。面试官想看你有没有真在半夜被叫起来过、有没有完整的故障复盘方法论。如果你只会说"重启大法好"或者"加了个 try-catch",基本就凉了。这道题要讲清楚: 故障现象 → 影响范围 → 排查过程(时间线) → 根因 → 修复 → 预防。最好讲一个 P0/P1 级故障,因为只有大故障才能逼出深度复盘。

**常见回答(不及格)**

> "有一次系统返回特别慢,我看了下日志发现是 Milvus 卡了,重启了一下就好了。后来加了个监控。"

问题: ①没有根因; ②"重启就好了"说明没真排查; ③没有时间线; ④没有预防措施。

**加分回答(90 分)**

讲一个完整的 P0 故障案例(以"检索突然全部返回空结果"为例):

> **故障现象**
> 某天下午 2:17,监控告警: RAG 问答接口错误率从 0.3% 飙升到 85%。用户反馈: 所有问题都返回"抱歉,我没有找到相关信息"。

> **影响范围**
> P0 级故障,影响全公司 800+ 知识库用户,持续 23 分钟。业务方在群里 @ 我的时候,我正在开另一个会。

> **排查时间线**
> - 14:17 告警触发(错误率 > 50% 持续 1 分钟)
> - 14:19 我介入,第一反应看 Grafana 大盘
> - 14:21 发现: 应用服务 QPS 正常,但 Milvus 检索延迟从 50ms 飙到 30s,且大量超时
> - 14:23 进一步看 Milvus 内部指标: 某个 collection 的 segment 数量从 12 暴涨到 3400
> - 14:25 怀疑是数据写入异常。查写入日志,发现 14:15 有一个批量导入任务,一次性写入 50 万条向量(正常单次导入不超过 1 万)
> - 14:27 定位根因: 数据同步脚本的一个 bug,把"增量同步"误执行成了"全量同步",而且去重逻辑失效,导致 50 万条重复向量写入,触发 Milvus 的 segment 大量分裂,检索性能断崖式下降。

> **应急修复(14:30)**
> ①先止血: 临时把检索切换到备用 collection(上次的快照),恢复服务; ②回滚数据同步脚本; ③Milvus 原集合做 compaction 合并 segment。

> **根因分析(事后)**
> 三个层面的问题:
> - **直接原因**: 数据同步脚本缺少"单次写入量上限"校验
> - **间接原因**: 数据同步任务没有独立监控,复用了业务接口的告警阈值,导致 50 万条写入没触发告警
> - **深层原因**: 没有"数据写入 → 检索可用性"的端到端混沌测试,只测了写入成功率,没测写入后检索性能

> **预防措施(一周内落地)**
> 1. **写入限流**: 同步脚本加单次写入上限(1 万条),超过自动分批
> 2. **独立监控**: 数据同步任务单独建监控面板,监控写入量、segment 数量、检索延迟三个指标
> 3. **熔断机制**: Milvus 检索延迟 > 2s 自动降级到备用 collection,并告警
> 4. **混沌测试**: 每周跑一次"异常写入"演练,模拟全量同步、重复写入、写入到一半失败等场景
> 5. **复盘文档**: 写了完整的 P0 故障复盘,同步给全团队,并把"数据同步检查清单"加入上线 SOP

**追问应对**

- **追问 1: "你说 23 分钟才恢复,这个时间能不能更短?"**
  答: 能。现在的方案是"延迟 > 2s 自动降级到备用 collection",如果是这个机制,14:21 发现延迟飙高时就会自动切流,用户基本无感,恢复时间能压到 1 分钟内。但当时还没有这个熔断机制,是这次故障后才加的。这也是故障复盘的价值——用一次痛换长期稳。

- **追问 2: "备用 collection 怎么保证数据是新的?"**
  答: 我们用"双写 + 定期快照"策略。写入时主 collection 实时写,备用 collection 每小时从主 collection 做一次快照。所以备用 collection 最多滞后 1 小时。对于知识库场景,1 小时滞后可以接受(用户很少问 1 小时内新入库的文档)。如果是强实时场景,可以改成双写同步,但成本会高。

- **追问 3: "你怎么看 RAG 系统的可观测性? 需要监控哪些指标?"**
  答: 我分三层:
  - **业务层**: 回答准确率(抽样人工评)、用户点赞率、bad case 率、首次解决率(FCR)
  - **服务层**: QPS、P50/P95/P99 延迟、错误率、token 消耗、成本
  - **组件层**: 检索召回率(离线)、embedding 延迟、向量库健康度、LLM 调用成功率、缓存命中率
  三个层都要有告警,但阈值不同: 业务层看趋势(连续 3 天下降才告警),服务层看绝对值(错误率 > 5% 立即告警),组件层看异常(缓存命中率突降 20% 告警)。

</details>

---

### Q3: 你如何从 0 到 1 搭建一个 Agent 项目的开发环境? 技术栈怎么选?

<details>
<summary>点击展开答案</summary>

**问题背景**

这道题考察工程化能力。面试官想看你是"只会调 OpenAI API"还是"能搭一套完整的研发体系"。重点不是你用了哪个具体框架,而是你"为什么选它"以及"怎么组织开发流程"。一个有经验的候选人会讲清楚: 开发/测试/生产环境隔离、依赖管理、Prompt 版本管理、评估流水线、CI/CD。

**常见回答(及格线)**

> "我用 Python,LangChain 做编排,OpenAI API 做 LLM,Milvus 做向量库,FastAPI 做服务,部署在 K8s 上。"

问题: ①没说为什么选这些; ②没说开发流程; ③没说 Prompt 和评估怎么管理; ④生产环境考量缺失。

**加分回答(85 分)**

按"技术选型 → 环境分层 → 开发流程 → 工程规范"四块讲:

> **一、技术选型(带理由)**
>
> | 层次 | 选型 | 理由 |
> |------|------|------|
> | 语言 | Python 3.11 | 生态最全;3.11 性能比 3.9 快 25% |
> | LLM 编排 | LangChain + 自研薄封装 | LangChain 生态好但抽象过重,自研封装保留灵活性 |
> | LLM 调用 | OpenAI GPT-4 + Azure 备份 | 主用 OpenAI,Azure 做灾备;敏感场景用本地 Qwen |
> | Embedding | bge-large-zh | 中文效果最好;自部署降成本 |
> | 向量库 | Milvus(生产) + Qdrant(测试) | Milvus 规模化好,Qdrant 轻量好调试 |
> | 重排 | bge-reranker-v2 | 中文 rerank 效果好 |
> | Web 框架 | FastAPI | 异步性能好,自动生成文档 |
> | 任务队列 | Celery + Redis | 异步任务(文档导入、批量评估) |
> | 监控 | Prometheus + Grafana + LangSmith | LangSmith 追踪 LLM 链路,Prometheus 看系统指标 |
> | 日志 | ELK + 结构化 JSON 日志 | 便于按 trace_id 串联全链路 |
> | 部署 | Docker + K8s | 标准化 |
>
> 选型原则: ①优先选社区活跃的(避免踩坑没人帮); ②LLM 相关组件保持可替换(写抽象层,不绑死一家); ③生产环境优先稳定性,开发环境优先开发效率。

> **二、环境分层**
>
> - **本地开发环境**: 用 docker-compose 一键起 Milvus + Redis + MinIO + 测试用 LLM(用 GPT-3.5 降成本)。每个开发者本地能跑全套。
> - **测试环境**: 接近生产配置,但用小模型(GPT-3.5)降成本。跑自动化测试和评估流水线。
> - **预发环境**: 和生产完全一致,但只接内部用户。做上线前回归。
> - **生产环境**: GPT-4 + 双可用区 + 自动伸缩。
>
> 关键点: 三个环境的 LLM 模型版本要一致(避免"测试用 3.5,生产用 4"导致的 prompt 不兼容),但可以用不同的 temperature/参数降成本。

> **三、开发流程**
>
> 1. **需求拆到 prompt 级别**: 每个功能拆成"prompt + 检索策略 + 后处理"三段,分别开发和测试。
> 2. **Prompt 版本管理**: 用 LangSmith 或自建的 prompt 仓库,prompt 改动走 PR Review,每次改动触发评估流水线回归。
> 3. **评估流水线**: 每次代码提交 → 跑 200 条 golden set → 输出准确率/召回率/延迟 → 和上次对比,下降 > 2% 阻断合并。
> 4. **CI/CD**: GitHub Actions 跑单元测试 + lint + 评估回归;通过后自动部署到测试环境;预发和生产需人工审批。
> 5. **Feature Flag**: 新功能用 feature flag 灰度,出问题秒级回滚(不用重新部署)。

> **四、工程规范**
>
> - **Prompt 规范**: 每个 prompt 文件包含"system prompt + few-shot + 变量声明 + 版本号 + 作者"。禁止在代码里硬编码 prompt。
> - **评估规范**: 任何 prompt 改动必须附带评估报告(对比改前改后的指标)。
> - **文档规范**: 每个 Agent 的"能力边界"必须写在 README 里(能做什么、不能做什么、降级策略)。
> - **成本规范**: 每个接口有 token 预算,超预算告警。

**追问应对**

- **追问 1: "为什么用 LangChain 又自研封装? 直接用 LangChain 不行吗?"**
  答: LangChain 的抽象层次太多,简单需求要绕好几层,而且版本升级 breaking change 频繁。我们的做法是: 用 LangChain 的基础组件(embedding、vectorstore、document loader),但 Agent 编排逻辑自己写。这样既享受 LangChain 生态,又保留控制力。如果项目简单,纯 LangChain 也够用;如果要做复杂 Agent,自研核心更可控。

- **追问 2: "Prompt 版本管理具体怎么做?"**
  答: 我们建了一个 prompt 仓库(独立 Git 仓库),每个 prompt 是一个 YAML 文件,包含: name、version、system、user_template、variables、metadata。代码里通过 prompt 名称 + 版本号加载。改动 prompt 走 PR,必须附评估报告。生产环境用 prompt 的稳定版本,测试环境可以用最新版本。好处是: prompt 改动可追溯、可回滚、可 A/B。

- **追问 3: "评估流水线跑 200 条要多久? 会不会太慢?"**
  答: 大约 15 分钟(200 条 × 平均 4.5 秒/条,并行 10 路)。我们把它放在 CI 的"夜间构建"里,每次合并到 main 跑一次完整评估。PR 级别只跑 50 条核心用例(3 分钟),保证不阻塞开发。如果评估失败,会自动评论 PR 并 @ 作者。

</details>

---

### Q4: Agent 项目中的数据质量和数据管理怎么做? 知识库怎么维护?

<details>
<summary>点击展开答案</summary>

**问题背景**

这是"区分菜鸟和老手"的题。菜鸟觉得 RAG 就是"把文档塞进向量库",老手知道数据质量决定 80% 的效果。面试官想看你对"数据全生命周期"的理解: 采集 → 清洗 → 切分 → 标注 → 入库 → 监控 → 更新 → 淘汰。

**常见回答(不及格)**

> "我们每周同步一次文档,用 LangChain 的 document loader 加载,切片后存 Milvus。"

问题: ①没有清洗逻辑; ②没有质量监控; ③没有更新策略; ④没有权限/版本管理。

**加分回答(85 分)**

按"数据全生命周期"讲:

> **一、数据采集: 多源接入 + 权限隔离**
>
> 知识库来源: ①Confluence(产品文档); ②飞书 Wiki(技术文档); ③GitLab(代码 README); ④人工录入(FAQ)。
>
> 关键设计: 每条数据带"权限标签"(部门、密级),检索时先按权限过滤再做向量检索。避免"普通员工问出高管才能看的内容"。
>
> 采集方式: 增量同步为主(每个数据源有"最后更新时间"水印),全量同步只在初始化和异常重建时用。

> **二、数据清洗: 6 道工序**
>
> 1. **格式归一化**: PDF/Word/HTML 都转成统一 markdown 结构
> 2. **噪声去除**: 去页眉页脚、水印、目录页、空白页
> 3. **表格修复**: PDF 表格用 Camelot 解析,错位的表格人工抽检
> 4. **图文分离**: 图片用多模态模型生成描述文字,单独入库
> 5. **去重**: 用 MinHash 去近似重复文档(避免同一份文档多个版本污染检索)
> 6. **敏感信息脱敏**: 正则 + NER 识别身份证、手机号、内部代号,脱敏后入库
>
> 每道工序都有"通过率"指标,低于阈值的文档进入人工审核队列。

> **三、chunk 切分: 策略化切分**
>
> 不是一刀切 512 token,而是按文档类型用不同策略:
> - **技术文档(markdown)**: 按标题层级切,每个 chunk 是一个完整的"小节"
> - **PDF 报告**: 用 layout 解析识别段落边界,按段落切,表格/图表保持完整
> - **代码**: 按函数/类边界切
> - **FAQ**: 一问一答作为一个 chunk,不切
>
> 每个 chunk 带元数据: source、section、page、update_time、permission、chunk_id。
> overlap 设置 50 token,避免边界信息丢失。

> **四、质量监控: 入库后持续盯**
>
> 上线后不是一劳永逸,要持续监控数据质量:
> - **检索空率**: 某些问题检索不到任何结果 → 可能是知识库覆盖不全
> - **top-1 命中率低**: 检索到但不是用户想要的 → 可能是 chunk 切分或 embedding 问题
> - **文档使用率**: 哪些文档从不被检索 → 可能是过时文档,考虑淘汰
> - **bad case 追溯**: 每个错误回答都能追到是哪个 chunk 导致的,标记后进入优化队列
>
> 我们做了一个"知识库健康度看板",每周生成报告: 本周新增文档数、检索 top-10 命中率、零检索问题数、待清理文档数。

> **五、更新与淘汰机制**
>
> - **更新**: 文档有更新时间戳,每周增量同步。更新的文档重新切分入库,旧 chunk 标记为 deprecated(不立即删,保留 1 个月供回溯)。
> - **淘汰**: 连续 3 个月零检索的文档进入"待归档"队列,业务方确认后归档(从向量库移除,源文件保留)。
> - **版本管理**: 每个 chunk 有 version 字段,同一文档的不同版本可以共存(用于回答"历史版本"类问题)。

> **六、知识库的"二次加工"**
>
> 原始文档不够,还要做"知识增强":
> - **FAQ 抽取**: 从历史问答记录里,用 LLM 提取高频问题,生成 FAQ 补充进知识库
> - **同义词扩展**: 用 LLM 生成"同一个问题的不同问法",作为评估集和检索增强
> - **摘要文档**: 长文档生成摘要,作为"导航 chunk"放在检索最前面

**追问应对**

- **追问 1: "权限隔离怎么实现? 会不会影响检索效果?"**
  答: 我们用"预过滤"方案: 检索前先按用户权限过滤出可见文档集合,再在这个集合里做向量检索。优点是安全,缺点是过滤后候选集变小可能影响召回。优化方案: 给每个权限组维护独立的 collection,用户只检索自己有权限的 collection。这样既安全又不影响召回,但会增加存储成本(同文档多权限组要重复入库)。我们根据场景权衡: 高密级用预过滤,普通密级用独立 collection。

- **追问 2: "怎么发现脏数据?"**
  答: 三个渠道: ①入库时的清洗通过率监控(格式异常、解析失败); ②运行时的检索异常监控(检索到明显无关内容); ③用户反馈(点"回答无用"会触发 bad case 追溯)。每条 bad case 都会追到对应的 chunk,标记后进入"脏数据待审队列",由数据治理同学每周清理一次。

- **追问 3: "知识库多大算够? 怎么判断要扩?"**
  答: 看两个指标: ①检索空率(用户问题检索不到任何结果),持续 > 5% 说明覆盖不足; ②"我不知道"率(模型回答无法回答),持续 > 10% 说明知识库不够。扩的方向: 先扩高频问题的覆盖(从 bad case 里找 top 问题),再扩长尾。不要盲目堆量,知识库越大检索噪声越多,质量比数量重要。

</details>

---

### Q5: 你做过的 Agent 项目,效果如何衡量? ROI 怎么算?

<details>
<summary>点击展开答案</summary>

**问题背景**

这是"业务价值"题。技术 leader 和业务方最关心这个,因为它决定项目能不能活下去。很多候选人只会说"准确率 85%",但说不清"这 85% 对业务意味着什么"。面试官想看你能不能把技术指标翻译成业务价值,以及会不会算经济账。

**常见回答(不及格)**

> "我们用准确率衡量,大概 85%。ROI 就是节省了客服人力。"

问题: ①准确率怎么算没说; ②"节省人力"没量化; ③ROI 没有具体数字; ④没有长期价值评估。

**加分回答(85 分)**

按"技术指标 → 业务指标 → ROI 核算 → 持续追踪"四层讲:

> **一、技术指标(离线评估)**
>
> | 指标 | 定义 | 我们的水平 |
> |------|------|-----------|
> | 检索 Recall@5 | top-5 命中正确文档的比例 | 89% |
> | 答案准确率 | 人工评 200 条,5 分制 ≥4 分占比 | 82% |
> | 答案相关性 | LLM-as-judge 评分(1-5) | 4.1 |
> | 引用准确率 | 答案引用的来源是否正确 | 91% |
> | 拒答准确率 | 该拒答时拒答的比例 | 76%(待优化) |
> | 幻觉率 | 编造内容的比例 | 4.3% |
>
> 评估集: 200 条 golden set,分三类: 常见问题 100 条(高频)、边界问题 60 条(知识库有但难找)、对抗问题 40 条(知识库没有或需拒答)。
>
> 评估方式: 人工评估(业务专家) + LLM-as-judge(GPT-4)双轨。人工评估每月一次,LLM 评估每次迭代都跑。

> **二、业务指标(在线评估)**
>
> | 指标 | 定义 | 上线后表现 |
> |------|------|-----------|
> | 首次解决率(FCR) | 用户第一次提问就解决问题的比例 | 68%(目标 70%) |
> | 用户满意度 | 回答后"有用"按钮点击率 | 74% |
> | 转人工率 | 用户提问后转人工客服的比例 | 22%(原 45%) |
> | 平均会话轮数 | 解决一个问题平均几轮对话 | 1.8 轮 |
> | 日活/月活 | 每日/月使用人数 | 800 / 3200 |
> | bad case 率 | 用户点"无用"的比例 | 11% |

> **三、ROI 核算(季度复盘)**
>
> **成本侧**:
> - LLM 调用: 月均 80 万 token × ¥0.06/1k token × 30 天 = ¥1440/月
> - 向量库 + 服务器: ¥3000/月
> - 人力维护(0.5 FTE): ¥15000/月
> - 总成本: 约 ¥2 万/月,¥24 万/年
>
> **收益侧**:
> - 客服人力节省: 转人工率从 45% 降到 22%,日均工单从 200 降到 110,节省 90 工单/天 × ¥15/工单 × 22 天 = ¥2.97 万/月
> - 员工效率提升: 知识查询从平均 8 分钟(人工找文档)降到 1 分钟(问 Agent),800 用户 × 1 次/天 × 7 分钟 × 22 天 × ¥0.5/分钟 = ¥6.16 万/月
> - 总收益: 约 ¥9 万/月,¥108 万/年
>
> **ROI = (收益 - 成本) / 成本 = (108 - 24) / 24 = 350%**
>
> 回本周期: 约 2.5 个月(前期开发投入约 20 万)。

> **四、持续追踪**
>
> ROI 不是算一次就完了,要持续追踪:
> - **月度**: 看业务指标趋势(FCR、满意度、bad case 率)
> - **季度**: 重新核算 ROI(成本随用量变化,收益随用户增长)
> - **年度**: 评估是否值得继续投入,还是应该转向新场景
>
> 关键提醒: ROI 核算要保守,别把"可能节省"算成"实际节省"。我们第一版 ROI 算出 800%,被业务 leader 质疑"员工效率提升那部分是不是太乐观",后来改成只算"明确节省的客服成本",ROI 变成 180%,反而更有说服力。

**追问应对**

- **追问 1: "LLM-as-judge 可信吗? 怎么保证评估质量?"**
  答: 不能全信,要和人工评估对齐。我们的做法: 每月用人工评估 200 条作为"基准",LLM-as-judge 跑同样 200 条,算两者的"一致率"。目前一致率 83%(5 分制误差 ≤1 分算一致)。低于 80% 就要调整 LLM 评估的 prompt。另外,LLM-as-judge 容易"打分偏高",我们会做校准: 如果 LLM 平均分比人工高 0.5 分以上,就在 LLM 评分里减去偏移量。

- **追问 2: "拒答准确率 76% 偏低,怎么优化?"**
  答: 这是我们的重点优化方向。问题在于模型"过度回答"——知识库里没有的内容它也会编。优化方案: ①prompt 里强化"信息不足时必须说不知道"; ②检索 top-1 相似度 < 0.7 时直接拒答,不送 LLM; ③用"拒答评估集"(40 条知识库没有的问题)专项优化。目标做到 90% 以上。

- **追问 3: "ROI 350% 听起来很高,业务方信吗?"**
  答: 一开始不信。我们的破法是: ①只算"硬收益"(明确节省的成本),不算"软收益"(效率提升); ②做 A/B 对照: 一组用户用 Agent,一组不用,对比工单量和解决时间; ③让业务方自己参与 ROI 核算,而不是技术方单方面报数。当业务方自己算出来的 ROI 和我们接近时,信任就建立了。

</details>

---

### Q6: 项目中团队协作怎么做的? Agent 开发需要哪些角色? 你承担什么角色?

<details>
<summary>点击展开答案</summary>

**问题背景**

这道题考察"团队视野"和"自我认知"。面试官想看你是只懂自己那一亩三分地,还是理解整个团队的协作方式。Agent 项目是典型的"跨职能协作"——算法、工程、产品、业务、设计都要参与,角色不清就会互相扯皮。回答时要体现: 你知道每个角色的职责、你清楚自己的定位、你能说清协作流程。

**常见回答(及格线)**

> "我们团队 5 个人,1 个产品、2 个后端、1 个算法、1 个测试。我是后端,负责 API 开发。"

问题: ①角色划分太粗; ②没说协作流程; ③没说自己角色的独特价值; ④没说跨职能沟通。

**加分回答(85 分)**

> **一、Agent 项目的角色矩阵**
>
> Agent 项目和传统 Web 项目不同,需要更多"AI 特有角色":
>
> | 角色 | 职责 | 我们团队的配置 |
> |------|------|---------------|
> | 产品经理 | 需求定义、场景拆解、效果验收 | 1 人(全职) |
> | AI 算法工程师 | 模型选型、prompt 工程、效果优化 | 1 人(全职) |
> | 后端工程师 | 系统架构、API、向量库、可观测性 | 2 人(全职) |
> | 数据工程师 | 数据清洗、知识库维护、评估集 | 1 人(半职,兼) |
> | 前端工程师 | 对话 UI、反馈交互 | 1 人(半职,借) |
> | 业务专家(SME) | 评估集标注、bad case 审核 | 2 人(业务部门借) |
> | 测试工程师 | 功能测试、压力测试、红队测试 | 1 人(半职,借) |
> | 运维/SRE | 部署、监控、故障响应 | 1 人(半职,借) |
>
> 总计: 全职 4 人 + 半职 5 人。规模不大,但角色齐全。

> **二、协作流程(双周迭代)**
>
> 1. **需求评审(双周第 1 天)**: PM 主导,所有角色参与。输出: 需求文档 + 验收标准 + 评估指标。
> 2. **技术方案(第 2-3 天)**: AI 算法 + 后端主导,输出技术方案文档(含 prompt 设计、检索策略、接口定义)。
> 3. **开发(第 4-9 天)**: 算法做 prompt 和模型,后端做系统和接口,数据工程师准备评估集。每天 15 分钟站会。
> 4. **评估(第 10 天)**: 业务专家 + LLM-as-judge 双轨评估,输出评估报告。
> 5. **验收(第 11 天)**: PM + 业务专家验收,不达标返工。
> 6. **上线(第 12 天)**: 灰度发布,SRE 保障。
> 7. **复盘(第 14 天)**: 全员复盘,看指标、聊问题、定下迭代方向。
>
> 关键节点: "评估"是硬卡点,不达标不上线。这避免了"开发完就上线,效果烂再返工"的死循环。

> **三、我的角色: AI 应用工程师(算法 + 后端的桥梁)**
>
> 我的正式 title 是后端工程师,但在这个项目里我承担的是"AI 应用工程师"角色——既懂算法又懂工程:
> - **算法侧**: 我参与 prompt 设计和评估,虽然不是主责,但能提出工程可行性建议(比如"这个 prompt 在 GPT-3.5 上效果会打折,建议加 few-shot")。
> - **工程侧**: 我负责 RAG 系统的架构设计和核心代码,确保算法同学的"好 prompt"能在工程上高效落地。
> - **桥梁作用**: 算法同学说"我要 top-10 检索结果",我会追问"为什么是 10 不是 5? 多 5 个会增加 token 成本和延迟"。通过这种对话,把"算法需求"翻译成"工程约束",避免算法和工程脱节。
>
> 我主动承担的额外职责: ①搭了评估流水线(原本没人做); ②写了团队 RAG 开发 SOP(把踩过的坑沉淀下来); ③每周和业务专家对一次 bad case,把业务反馈翻译成技术优化项。

> **四、跨职能沟通的关键经验**
>
> 1. **和 PM 沟通**: 用"评估指标"对齐,不用"技术细节"。不说"我用了 hybrid search",说"召回率从 72% 提到 89%,用户能找到更多答案"。
> 2. **和业务专家沟通**: 让他们做"选择题"不做"问答题"。不问"这个答案好不好",问"这个答案和理想答案的差距是 A 内容缺失 B 逻辑错误 C 表达不好"。
> 3. **和运维沟通**: 提供"可观测性清单",明确告警阈值和应急手册,不让运维猜。
> 4. **和算法沟通**: 用"工程约束"说话,说"这个方案延迟 > 5s 不能接受,能不能改成异步"。

**追问应对**

- **追问 1: "你说自己是'桥梁',但万一算法和后端都不认你怎么办?"**
  答: 这是个真实风险。我的做法是: ①不抢功,算法的成果归算法,后端的成果归后端,我只做"翻译和连接"; ②用产出说话,评估流水线是大家都需要但没人愿意做的,我做出来大家自然认可; ③遇到分歧时不站队,而是用数据说话——拉评估结果、跑 A/B 实验,让数据决定。

- **追问 2: "业务专家只有'借'的,不配合怎么办?"**
  答: 这是常态。我们的破法: ①让 PM 出面和业务部门 leader 对齐,把"配合 AI 项目"写进业务方 KPI; ②降低业务专家的参与成本,把标注工具做得尽量简单(飞书表格就能标,不用学新工具); ③给反馈,每月把"你的标注帮我们优化了 X 个问题"反馈给业务专家,让他们有成就感。

- **追问 3: "Agent 项目最容易扯皮的是哪个环节?"**
  答: "效果不达标是谁的责任"。算法说"prompt 我调了,是工程检索没召回",工程说"检索召回率 89%,是 prompt 没写好"。破法: ①拆指标——检索召回率归工程,答案准确率归算法,端到端满意度共同承担; ②每个 bad case 都做"归因分析",明确是检索问题还是生成问题; ③建立"共同目标",比如"季度 bad case 率降到 8% 以下,全团队共担"。

</details>

---

### Q7: 你的 Agent 项目上线后,持续优化的机制是什么? 多久迭代一次?

<details>
<summary>点击展开答案</summary>

**问题背景**

这道题考察"长期主义"。很多候选人项目上线后就"撒手不管"了,但真实项目 70% 的价值来自上线后的持续优化。面试官想看你有没有"数据驱动的迭代闭环"——从用户反馈到问题定位到优化上线的效果追踪。

**常见回答(不及格)**

> "上线后我们会定期看用户反馈,有问题就改。大概一个月迭代一次。"

问题: ①没有闭环机制; ②反馈怎么收集没说; ③优化优先级怎么定没说; ④没有效果追踪。

**加分回答(85 分)**

按"反馈收集 → 问题定位 → 优化决策 → 迭代上线 → 效果追踪"五步讲闭环:

> **一、反馈收集: 三条渠道**
>
> 1. **显式反馈**: 用户在答案下方点"有用/无用",无用可填具体原因(内容错误/没答到/看不懂/太长)。转化率约 8%(100 人里 8 人会点)。
> 2. **隐式反馈**: 用户行为数据——是否转人工、是否重新提问、会话时长、是否复制答案。这些比显式反馈更真实(用户嘴上说没用,但实际复制了答案,说明其实有用)。
> 3. **主动监测**: 每周从对话日志里随机抽 100 条,人工标注质量,算"抽检准确率"。
>
> 所有反馈都进入"bad case 池",每条带: 用户问题、检索结果、模型答案、反馈类型、严重度。

> **二、问题定位: 归因分析**
>
> 每个 bad case 都做归因,分四类:
> - **检索问题(约 40%)**: 没召回正确文档。细分: 知识库没有(补数据)、切分不对(改 chunk)、embedding 不行(换模型)。
> - **生成问题(约 35%)**: 召回了但答错了。细分: prompt 不行(改 prompt)、模型能力不足(换模型)、context 太多干扰(减 top-k)。
> - **数据问题(约 15%)**: 知识库内容本身错或过时。处理: 修源文档或加新文档。
> - **产品问题(约 10%)**: 用户问法不在设计场景内。处理: 加 FAQ 或调整产品边界。
>
> 归因由 AI 算法工程师主导,我作为工程提供工具支持(做了归因标注工具,能快速看一个 bad case 的检索结果和 prompt)。

> **三、优化决策: 优先级矩阵**
>
> 不是所有 bad case 都值得改,要排优先级:
>
> | | 高频问题 | 低频问题 |
> |---|---|---|
> | **易修复** | P0: 立即改(1-2 天) | P2: 攒一批一起改 |
> | **难修复** | P1: 排入迭代(1-2 周) | P3: 记录待办,定期评估 |
>
> "高频"看出现次数(周出现 > 10 次算高频),"易修复"看改动范围(改 prompt/chunk 算易,换模型/重构算难)。
>
> 每周开一次"bad case 评审会",算法 + 工程 + PM 一起,把本周 top-20 bad case 排优先级,分配到迭代。

> **四、迭代节奏: 双周迭代 + 紧急修复**
>
> - **双周迭代**: 和团队开发节奏对齐。每个迭代处理 5-10 个 P0/P1 bad case,产出一个小版本。
> - **紧急修复**: 出现影响 > 10% 用户的 bad case,24 小时内热修复(改 prompt,不走完整迭代)。
> - **大版本(季度)**: 做结构性优化,比如换 embedding 模型、重构检索策略、上 Agent 能力。需要完整评估和灰度。
>
> 每次迭代必须带"评估报告": 改前改后指标对比,bad case 率变化,新引入的问题。

> **五、效果追踪: 三个看板**
>
> 1. **实时看板**: 当天的准确率、bad case 率、用户满意度。异常波动立即告警。
> 2. **趋势看板**: 周/月维度的指标趋势,看是否持续改善。关键指标: FCR、满意度、bad case 率、转人工率。
> 3. **ROI 看板**: 月度的成本和收益核算,看边际收益是否递减(如果优化的投入产出比 < 2,说明该收尾或转方向了)。

> **六、我的经验沉淀**
>
> 上线 6 个月,我们做了 12 个双周迭代 + 3 次紧急修复 + 1 次大版本(上 Agent)。效果: FCR 从 58% 到 68%,bad case 率从 18% 到 11%,满意度从 65% 到 74%。
>
> 最重要的经验: **持续优化的关键不是"改得快",而是"改得准"**。前 3 个月我们改了 50 个 bad case,但 FCR 只涨了 3 个点——因为改的都是低频问题。后来用优先级矩阵聚焦高频问题,1 个月就涨了 5 个点。

**追问应对**

- **追问 1: "怎么判断一个项目该继续优化还是该停了?"**
  答: 看边际收益。我们设了"止损线": 连续 2 个迭代,核心指标提升 < 1 个百分点,就触发"项目复盘",评估是否该: ①转向新场景(把已有能力复制到新业务); ②降低投入(从全职改成维护模式); ③下线(如果 ROI 已经为负)。Agent 项目不是"永远优化下去",该止损就止损。

- **追问 2: "用户反馈只有 8% 转化率,会不会样本偏差?"**
  答: 会。点反馈的往往是"特别满意"或"特别不满意"的,中间地带沉默。破法: ①看隐式反馈(转人工率、重问率)作为补充,这些是全量数据; ②主动抽检,每周随机抽 100 条人工评,避免幸存者偏差; ③做"满意度调研",每月给随机用户发问卷,覆盖沉默用户。

- **追问 3: "你说的优先级矩阵,实际执行中会不会有政治因素?"**
  答: 会有。比如业务方坚持某个低频但"领导关注"的问题要优先改。我的处理: ①尊重业务方诉求,但要明确"这会挤占 X 个高频问题的优化资源,FCR 预期少涨 Y 个点"; ②如果业务方坚持,就做,但把"资源置换"记录在迭代复盘里,让决策透明; ③长期看,用数据说话——如果按业务方优先级改了 1 个月,FCR 没涨,下次就有底气用数据推回去。

</details>

---

### Q8: 在 Agent 项目中,你和技术 leader/产品/业务方有分歧时怎么处理?

<details>
<summary>点击展开答案</summary>

**问题背景**

这是"软技能"题,但面试官非常看重。Agent 项目不确定性高、技术新、效果难量化,分歧几乎是常态。面试官想看你是不是"只会技术不会沟通"的书呆子,以及有没有"用数据说话、对事不对人"的成熟度。回答时避免两个极端: ①"我都听 leader 的"(没主见); ②"我用数据说服了所有人"(太理想化)。

**常见回答(不及格)**

> "我会用数据说服他们。如果说服不了就听 leader 的。"

问题: ①太套路; ②没有具体案例; ③没说分歧的本质是什么; ④"听 leader 的"显得没主见。

**加分回答(85 分)**

讲一个具体案例,体现"分歧类型 → 处理原则 → 具体过程 → 结果反思":

> **案例: "要不要上 Agent"的分歧**
>
> **背景**: 我们的 RAG 知识库问答运行 3 个月后,业务方提出"能不能让机器人主动调用工具(查订单、查库存),而不只是查文档"。产品经理很兴奋,觉得这是"从 RAG 升级到 Agent"的大升级,想立刻排期。我和另一个后端同学认为: 当前 RAG 还没优化到位(bad case 率 11%),贸然上 Agent 会引入更多不确定性(Agent 决策失败、工具调用错误),可能两边都做不好。技术 leader 态度中立,让我们自己 PK。
>
> **分歧本质**: 不是"技术能不能做",而是"现在是不是做的时候"。这是典型的"机会成本"分歧——做 Agent 的资源,本来可以用来优化 RAG。
>
> **处理过程**:
>
> 1. **先听对方**: 我让 PM 先讲为什么觉得现在该做。PM 的理由: 业务方有明确诉求,竞品已经有 Agent 能力,不做会掉用户。我听完发现 PM 不是"拍脑袋",是有业务依据的。
>
> 2. **表达我的顾虑**: 我没说"Agent 不行",而是说"我担心同时做两件事都做不好"。具体: ①目前 RAG 的 bad case 率 11%,每降 1 个点需要 1 个迭代,降到 8% 还要 3 个迭代; ②Agent 的工具调用准确率业界普遍 70-80%,叠加到现有 RAG 上,端到端准确率可能从 82% 掉到 70%。
>
> 3. **找共识**: 我们都认同"Agent 是方向",分歧在节奏。于是讨论"有没有折中方案"。
>
> 4. **折中方案**: 我提议分两步走: ①先用 1 个迭代做"Agent MVP"——只接 1 个工具(查订单),只对 10% 用户灰度,验证工具调用准确率; ②同时 RAG 优化不停,继续降 bad case 率; ③如果 MVP 的工具调用准确率 > 85%,再扩大 Agent 范围; ④如果 < 85%,说明 Agent 时机未到,继续聚焦 RAG。
>
> 5. **结果**: PM 接受了这个方案。MVP 上线后,工具调用准确率只有 72%(低于 85% 阈值),我们分析发现是"用户意图识别"环节太弱。于是暂停 Agent 扩展,花 2 个迭代做意图识别优化,再上 Agent 时准确率到 88%。最终 Agent 能力在 4 个月后全量上线,且没有拖累 RAG 的优化进度。
>
> **反思**: 这次分歧让我学到三点:
> 1. **分歧不是对抗,是信息差**: PM 有业务视角,我有技术视角,合起来才是完整决策。如果我直接"用数据否决",会失去 PM 的业务输入。
> 2. **用"实验"代替"争论"**: 与其争论"该不该做",不如做个小实验让数据说话。MVP 用 1 周时间,比无休止的会议高效。
> 3. **保留体面**: 即使最终证明"我当初的担心是对的"(Agent 时机未到),也不要说"我早说过了"。而是说"这次实验帮我们搞清楚了节奏"。

> **我对"分歧处理"的方法论**:
>
> 1. **对事不对人**: 永远讨论"这个方案的问题",不讨论"你这个人"。
> 2. **先听后说**: 先复述对方观点,确认理解无误,再表达自己。避免"自说自话"。
> 3. **数据优先**: 有数据用数据,没数据先做实验拿数据,而不是"我觉得"。
> 4. **找共识点**: 即使整体分歧,也能找到局部共识(比如"Agent 是方向"是共识,"什么时候做"是分歧)。从共识出发推进。
> 5. **决策后执行**: 一旦定了,即使和我的意见不同,也全力执行。不在执行中"消极怠工"。
> 6. **复盘归档**: 分歧的结论要记录下来,成为团队经验。避免下次同样问题再吵一遍。

**追问应对**

- **追问 1: "如果 leader 强行决定一个你认为错的方案,你怎么办?"**
  答: 分情况。①如果是"我 90% 确定会出问题",我会再争取一次,用最简短的方式说清风险,然后说"如果决定做,我全力执行,但风险记录在案"; ②如果是"我只有 60% 把握",我会承认"我可能错了",先按 leader 的方案做,用结果验证。技术 leader 站位更高,可能看到了我没看到的东西。最忌讳的是"消极执行"——明明定了方案,执行时留一手,等着出问题证明自己对。这是对团队不负责任。

- **追问 2: "和业务方分歧时,业务方说'我不懂技术但我就是要这个效果',怎么办?"**
  答: 这种情况下,我会: ①承认业务方的"效果诉求"是合理的,不该用"你不懂技术"反驳; ②把"效果诉求"翻译成"技术可行性"——不说"做不到",说"做到这个效果需要 X 成本 Y 时间,你愿意接受吗"; ③提供"降级方案"——"100% 做不到,但 80% 可以做到,先上 80% 的版本看看?"。核心是: 不拒绝业务诉求,而是把"能不能做"变成"以什么成本做"。

- **追问 3: "你有没有遇到过'数据也说服不了'的情况?"**
  答: 有。有时候分歧不是"事实之争"而是"价值观之争"——比如"要不要为了效果牺牲延迟",这是产品取舍,不是数据能决定的。这种情况我不再纠结数据,而是: ①明确这是"取舍"不是"对错"; ②把取舍的两个选项和后果列清楚,让决策方(通常是产品或业务)选; ③选定后我执行,但要确保"可回退"——做 feature flag,出问题能快速切回去。

</details>

---

### Q9: 手撕代码题 — 现场实现一个你做过的 Agent 项目的核心模块(限时 30 分钟)

<details>
<summary>点击展开答案</summary>

**问题背景**

这是"代码真功夫"题。面试官给你 30 分钟,让你现场写一个核心模块。考的不是"能不能跑通",而是"代码质量、工程思维、对问题的理解"。三个方向选一个,建议选自己最熟的方向,把"可运行 + 有设计 + 边界处理"做到位。

---

#### 方向 A: RAG 检索增强模块

**要求**: 实现一个 RAG 检索模块,支持: ①hybrid search(向量 + BM25); ②rerank; ③来源标注; ④空结果兜底。输入是用户 query,输出是增强后的 prompt context。

```python
"""
RAG 检索增强模块
支持: hybrid search (vector + BM25) + rerank + 来源标注 + 空结果兜底
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class Chunk:
    """知识库 chunk 数据结构"""
    chunk_id: str
    content: str
    source: str          # 来源文档
    section: str         # 所属章节
    metadata: Dict       # 其他元数据(时间、权限等)


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: Chunk
    score: float
    retrieval_type: str  # vector / bm25 / rerank


class HybridRetriever:
    """混合检索器: 向量检索 + BM25 关键词检索"""

    def __init__(
        self,
        embedding_model: str = "BAAI/bge-large-zh",
        vector_weight: float = 0.6,
        bm25_weight: float = 0.4,
    ):
        self.embedder = SentenceTransformer(embedding_model)
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.chunks: List[Chunk] = []
        self.chunk_embeddings: Optional[np.ndarray] = None
        self.bm25: Optional[BM25Okapi] = None

    def add_chunks(self, chunks: List[Chunk]) -> None:
        """添加 chunks 到检索库"""
        if not chunks:
            return
        self.chunks.extend(chunks)
        # 重新计算 embedding(生产环境应增量更新)
        new_embeddings = self.embedder.encode(
            [c.content for c in chunks], normalize_embeddings=True
        )
        if self.chunk_embeddings is None:
            self.chunk_embeddings = new_embeddings
        else:
            self.chunk_embeddings = np.vstack([self.chunk_embeddings, new_embeddings])
        # 重建 BM25 索引
        tokenized = [c.content.split() for c in self.chunks]
        self.bm25 = BM25Okapi(tokenized)

    def _vector_search(self, query: str, top_k: int = 20) -> List[RetrievalResult]:
        """向量检索"""
        if self.chunk_embeddings is None or len(self.chunks) == 0:
            return []
        query_emb = self.embedder.encode([query], normalize_embeddings=True)
        sims = cosine_similarity(query_emb, self.chunk_embeddings)[0]
        top_idx = np.argsort(sims)[::-1][:top_k]
        return [
            RetrievalResult(
                chunk=self.chunks[i],
                score=float(sims[i]),
                retrieval_type="vector",
            )
            for i in top_idx
        ]

    def _bm25_search(self, query: str, top_k: int = 20) -> List[RetrievalResult]:
        """BM25 关键词检索"""
        if self.bm25 is None or len(self.chunks) == 0:
            return []
        scores = self.bm25.get_scores(query.split())
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [
            RetrievalResult(
                chunk=self.chunks[i],
                score=float(scores[i]),
                retrieval_type="bm25",
            )
            for i in top_idx if scores[i] > 0
        ]

    def _merge_results(
        self,
        vector_results: List[RetrievalResult],
        bm25_results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """融合两路检索结果(score 归一化后加权)"""
        # 归一化
        def normalize(results: List[RetrievalResult]) -> Dict[str, float]:
            if not results:
                return {}
            scores = [r.score for r in results]
            min_s, max_s = min(scores), max(scores)
            denom = max_s - min_s if max_s > min_s else 1.0
            return {r.chunk.chunk_id: (r.score - min_s) / denom for r in results}

        vec_norm = normalize(vector_results)
        bm25_norm = normalize(bm25_results)

        # 加权融合
        all_ids = set(vec_norm.keys()) | set(bm25_norm.keys())
        chunk_map = {r.chunk.chunk_id: r.chunk for r in vector_results + bm25_results}
        merged = []
        for cid in all_ids:
            v_score = vec_norm.get(cid, 0.0) * self.vector_weight
            b_score = bm25_norm.get(cid, 0.0) * self.bm25_weight
            merged.append(
                RetrievalResult(
                    chunk=chunk_map[cid],
                    score=v_score + b_score,
                    retrieval_type="hybrid",
                )
            )
        merged.sort(key=lambda x: x.score, reverse=True)
        return merged

    def search(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """混合检索主入口"""
        vec_results = self._vector_search(query, top_k=top_k * 4)
        bm25_results = self._bm25_search(query, top_k=top_k * 4)
        merged = self._merge_results(vec_results, bm25_results)
        return merged[:top_k]


class Reranker:
    """重排器: 用 cross-encoder 对初筛结果精排"""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name)

    def rerank(
        self, query: str, results: List[RetrievalResult], top_k: int = 3
    ) -> List[RetrievalResult]:
        if not results:
            return []
        pairs = [(query, r.chunk.content) for r in results]
        scores = self.model.predict(pairs)
        ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
        return [
            RetrievalResult(
                chunk=r.chunk,
                score=float(s),
                retrieval_type="rerank",
            )
            for r, s in ranked[:top_k]
        ]


class RAGContextBuilder:
    """RAG Context 构建器: 检索 + rerank + 拼接 + 兜底"""

    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: Optional[Reranker] = None,
        max_context_chars: int = 3000,
        min_score_threshold: float = 0.3,
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.max_context_chars = max_context_chars
        self.min_score_threshold = min_score_threshold

    def _format_context(self, results: List[RetrievalResult]) -> str:
        """把检索结果格式化为带来源标注的 context"""
        if not results:
            return ""
        parts = []
        for i, r in enumerate(results, 1):
            part = (
                f"[{i}] 来源: {r.chunk.source} > {r.chunk.section}\n"
                f"内容: {r.chunk.content}\n"
            )
            parts.append(part)
        return "\n---\n".join(parts)

    def _fallback_prompt(self, query: str) -> Dict:
        """空结果兜底"""
        return {
            "context": "",
            "has_context": False,
            "prompt": (
                f"用户问题: {query}\n\n"
                "注意: 知识库中没有找到相关信息。"
                "请如实告知用户你无法回答,不要编造内容。"
                "可以建议用户换一种问法或联系人工客服。"
            ),
            "sources": [],
        }

    def build(self, query: str) -> Dict:
        """主入口: 构建增强 prompt context"""
        # 1. 混合检索
        results = self.retriever.search(query, top_k=10)

        # 2. 过滤低分结果
        results = [r for r in results if r.score >= self.min_score_threshold]

        # 3. 空结果兜底
        if not results:
            return self._fallback_prompt(query)

        # 4. Rerank 精排(可选)
        if self.reranker:
            results = self.reranker.rerank(query, results, top_k=3)
        else:
            results = results[:3]

        # 5. 拼接 context(控制长度)
        context = self._format_context(results)
        if len(context) > self.max_context_chars:
            context = context[: self.max_context_chars] + "\n...(内容已截断)"

        # 6. 构建最终 prompt
        prompt = (
            f"请基于以下参考资料回答用户问题。\n"
            f"要求: 1) 只用资料中的信息; 2) 引用来源编号; "
            f"3) 资料不足时明确说明。\n\n"
            f"参考资料:\n{context}\n\n"
            f"用户问题: {query}"
        )

        return {
            "context": context,
            "has_context": True,
            "prompt": prompt,
            "sources": [
                {"source": r.chunk.source, "section": r.chunk.section, "score": r.score}
                for r in results
            ],
        }


# ===== 使用示例 =====
if __name__ == "__main__":
    # 1. 准备知识库
    chunks = [
        Chunk("c1", "公司的年假政策: 入职满1年有5天年假,满3年有10天,满10年有15天。",
              "员工手册.pdf", "年假章节", {"permission": "all"}),
        Chunk("c2", "请假流程: 在OA系统提交申请,直属领导审批,超过3天需二级审批。",
              "员工手册.pdf", "请假流程", {"permission": "all"}),
        Chunk("c3", "2024年Q3财报: 营收同比增长12%,净利润增长8%。",
              "2024Q3财报.pdf", "财务概要", {"permission": "manager"}),
    ]

    # 2. 初始化检索器
    retriever = HybridRetriever()
    retriever.add_chunks(chunks)

    # 3. 构建 context(可选 reranker)
    builder = RAGContextBuilder(retriever=retriever, reranker=None)

    # 4. 测试
    result = builder.build("我有几天年假?")
    print("=== 有结果 ===")
    print(result["prompt"])
    print("来源:", result["sources"])

    result = builder.build("公司食堂今天吃什么?")
    print("\n=== 空结果兜底 ===")
    print(result["prompt"])
```

---

#### 方向 B: Agent 决策引擎

**要求**: 实现一个基于 ReAct 模式的 Agent 决策引擎,支持: ①工具注册; ②Thought-Action-Observation 循环; ③最大步数限制; ④错误兜底; ⑤历史记录。

```python
"""
Agent 决策引擎 (ReAct 模式)
支持: 工具注册 + Thought-Action-Observation 循环 + 步数限制 + 错误兜底
"""
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import re
from openai import OpenAI


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    func: Callable[[str], str]
    usage: str  # 参数说明


@dataclass
class Step:
    """Agent 执行的一步"""
    thought: str
    action: str
    action_input: str
    observation: str


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    answer: str
    steps: List[Step] = field(default_factory=list)
    error: Optional[str] = None


class Agent:
    """ReAct Agent 决策引擎"""

    SYSTEM_PROMPT = """你是一个能使用工具的 AI Agent。请按以下格式思考并行动:

Thought: 我需要思考下一步该做什么
Action: 工具名称
Action Input: 工具输入参数(字符串)

当你观察到结果后,继续思考下一步。当你有足够信息回答用户问题时,使用:

Thought: 我现在可以回答了
Final Answer: 最终答案

可用工具:
{tools_desc}

注意:
1. 每次只能调用一个工具
2. Action 必须是上面列出的工具之一
3. 如果工具返回错误,调整策略重试
4. 最多 {max_steps} 步,要高效行动
"""

    def __init__(
        self,
        llm_client: OpenAI,
        model: str = "gpt-4",
        max_steps: int = 5,
        temperature: float = 0.0,
    ):
        self.llm = llm_client
        self.model = model
        self.max_steps = max_steps
        self.temperature = temperature
        self.tools: Dict[str, Tool] = {}

    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.tools[tool.name] = tool

    def _build_system_prompt(self) -> str:
        """构建 system prompt(含工具描述)"""
        tools_desc = "\n".join(
            f"- {t.name}: {t.description}\n  用法: {t.usage}"
            for t in self.tools.values()
        )
        return self.SYSTEM_PROMPT.format(
            tools_desc=tools_desc, max_steps=self.max_steps
        )

    def _parse_response(self, text: str) -> Dict:
        """解析 LLM 响应,提取 Thought/Action/Action Input/Final Answer"""
        result = {"thought": "", "action": None, "action_input": "", "final_answer": None}

        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction:|\nFinal Answer:|$)",
                                  text, re.DOTALL)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()

        if "Final Answer:" in text:
            answer_match = re.search(r"Final Answer:\s*(.+)$", text, re.DOTALL)
            if answer_match:
                result["final_answer"] = answer_match.group(1).strip()
            return result

        action_match = re.search(r"Action:\s*(.+?)(?=\nAction Input:|$)", text)
        if action_match:
            result["action"] = action_match.group(1).strip()

        input_match = re.search(r"Action Input:\s*(.+?)(?=\nThought:|$)", text, re.DOTALL)
        if input_match:
            result["action_input"] = input_match.group(1).strip()

        return result

    def _call_tool(self, action: str, action_input: str) -> str:
        """调用工具,带错误兜底"""
        if action not in self.tools:
            return f"错误: 工具 '{action}' 不存在。可用工具: {list(self.tools.keys())}"
        try:
            return self.tools[action].func(action_input)
        except Exception as e:
            return f"工具执行出错: {type(e).__name__}: {str(e)}"

    def run(self, user_query: str) -> AgentResult:
        """Agent 主循环"""
        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_query},
        ]
        steps: List[Step] = []

        for step_num in range(self.max_steps):
            # 1. 调 LLM 决策
            try:
                response = self.llm.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                )
                llm_output = response.choices[0].message.content
            except Exception as e:
                return AgentResult(
                    success=False,
                    answer="",
                    steps=steps,
                    error=f"LLM 调用失败: {e}",
                )

            # 2. 解析响应
            parsed = self._parse_response(llm_output)

            # 3. 如果有最终答案,返回
            if parsed["final_answer"]:
                return AgentResult(
                    success=True,
                    answer=parsed["final_answer"],
                    steps=steps,
                )

            # 4. 执行工具
            action = parsed["action"]
            action_input = parsed["action_input"]

            if not action:
                messages.append({"role": "assistant", "content": llm_output})
                messages.append({
                    "role": "user",
                    "content": "请按格式输出(Thought/Action/Action Input 或 Final Answer)。",
                })
                continue

            observation = self._call_tool(action, action_input)

            step = Step(
                thought=parsed["thought"],
                action=action,
                action_input=action_input,
                observation=observation,
            )
            steps.append(step)

            # 5. 更新对话历史
            messages.append({"role": "assistant", "content": llm_output})
            messages.append({
                "role": "user",
                "content": f"Observation: {observation}",
            })

        # 6. 超过最大步数
        return AgentResult(
            success=False,
            answer="",
            steps=steps,
            error=f"超过最大步数 {self.max_steps},Agent 未能给出最终答案。",
        )


# ===== 使用示例 =====
if __name__ == "__main__":
    client = OpenAI(api_key="your-api-key")

    # 定义工具
    def search_weather(city: str) -> str:
        # 模拟天气查询
        return f"{city} 今天晴,气温 25 度,湿度 60%。"

    def search_stock(code: str) -> str:
        # 模拟股票查询
        return f"股票 {code} 当前价格 100.5 元,涨跌 +2.3%。"

    agent = Agent(llm_client=client, model="gpt-4", max_steps=5)
    agent.register_tool(Tool("search_weather", "查询城市天气", search_weather, "城市名称"))
    agent.register_tool(Tool("search_stock", "查询股票价格", search_stock, "股票代码"))

    result = agent.run("北京今天天气怎么样? 顺便查下 600519 股价。")
    print("成功:", result.success)
    print("答案:", result.answer)
    for i, step in enumerate(result.steps, 1):
        print(f"\n--- 步骤 {i} ---")
        print("Thought:", step.thought)
        print("Action:", step.action, "| Input:", step.action_input)
        print("Observation:", step.observation)
```

---

#### 方向 C: Multi-Agent 协作框架

**要求**: 实现一个简单的 Multi-Agent 协作框架,支持: ①Agent 角色定义; ②消息传递; ③任务分发; ④结果汇总; ⑤冲突处理。

```python
"""
Multi-Agent 协作框架
支持: 角色定义 + 消息传递 + 任务分发 + 结果汇总
场景: 多个 Agent 协作完成一份技术调研报告
"""
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from openai import OpenAI


class AgentRole(Enum):
    """Agent 角色"""
    COORDINATOR = "coordinator"   # 协调者: 分发任务、汇总结果
    RESEARCHER = "researcher"     # 研究员: 搜集信息
    ANALYST = "analyst"           # 分析师: 分析数据
    WRITER = "writer"                # 撰写者: 整合报告
    REVIEWER = "reviewer"         # 审稿者: 质量把关


@dataclass
class Message:
    """Agent 间消息"""
    from_agent: str
    to_agent: str
    content: str
    msg_type: str  # task / result / feedback
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])


@dataclass
class Task:
    """任务定义"""
    task_id: str
    description: str
    assigned_to: str
    status: str = "pending"  # pending / running / done / failed
    result: Optional[str] = None


class MultiAgent:
    """单个 Agent 实体"""

    def __init__(
        self,
        name: str,
        role: AgentRole,
        system_prompt: str,
        llm_client: OpenAI,
        model: str = "gpt-4",
    ):
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = llm_client
        self.model = model
        self.inbox: List[Message] = []

    def receive(self, msg: Message) -> None:
        """接收消息"""
        self.inbox.append(msg)

    def act(self) -> Optional[str]:
        """根据收到的消息行动,返回输出"""
        if not self.inbox:
            return None
        # 拼接所有未处理消息
        context = "\n".join(
            f"[来自 {m.from_agent}]: {m.content}" for m in self.inbox
        )
        self.inbox.clear()

        try:
            response = self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Agent {self.name} 出错: {e}]"


class MultiAgentOrchestrator:
    """Multi-Agent 协作编排器"""

    def __init__(self, llm_client: OpenAI):
        self.llm = llm_client
        self.agents: Dict[str, MultiAgent] = {}
        self.message_log: List[Message] = []

    def add_agent(self, agent: MultiAgent) -> None:
        self.agents[agent.name] = agent

    def _send(self, from_name: str, to_name: str, content: str, msg_type: str) -> None:
        """发送消息(并记录日志)"""
        if to_name not in self.agents:
            print(f"[警告] Agent '{to_name}' 不存在")
            return
        msg = Message(from_name, to_name, content, msg_type)
        self.agents[to_name].receive(msg)
        self.message_log.append(msg)
        print(f"[{from_name} -> {to_name}] ({msg_type}) {content[:80]}...")

    def run_report_pipeline(self, topic: str) -> str:
        """运行技术调研报告生成流水线"""
        print(f"\n=== 开始 Multi-Agent 协作,主题: {topic} ===\n")

        # 阶段 1: 协调者分发任务给研究员
        self._send("coordinator", "researcher",
                   f"请调研主题: {topic}。搜集核心概念、关键技术、代表产品。", "task")

        # 阶段 2: 研究员产出,发给分析师
        research_result = self.agents["researcher"].act()
        if research_result:
            self._send("researcher", "analyst",
                       f"调研结果如下,请分析优势和挑战:\n{research_result}", "result")

        # 阶段 3: 分析师产出,发给撰写者
        analysis_result = self.agents["analyst"].act()
        if analysis_result:
            self._send("analyst", "writer",
                       f"分析结果如下,请整合成报告:\n调研: {research_result}\n分析: {analysis_result}",
                       "result")

        # 阶段 4: 撰写者产出,发给审稿者
        draft = self.agents["writer"].act()
        if draft:
            self._send("writer", "reviewer",
                       f"请审阅报告草稿:\n{draft}", "result")

        # 阶段 5: 审稿者反馈给协调者
        review = self.agents["reviewer"].act()
        if review:
            self._send("reviewer", "coordinator", f"审稿意见:\n{review}", "feedback")

        # 阶段 6: 协调者最终决策
        final = self.agents["coordinator"].act()
        print(f"\n=== 协作完成 ===\n")
        return final or "协作未产出结果"


# ===== 使用示例 =====
if __name__ == "__main__":
    client = OpenAI(api_key="your-api-key")
    orch = MultiAgentOrchestrator(client)

    orch.add_agent(MultiAgent(
        "coordinator", AgentRole.COORDINATOR,
        "你是项目协调者。负责分配任务、汇总结果、做最终决策。输出简洁明确。",
        client,
    ))
    orch.add_agent(MultiAgent(
        "researcher", AgentRole.RESEARCHER,
        "你是技术研究员。搜集主题的核心概念、关键技术、代表产品。结构化输出。",
        client,
    ))
    orch.add_agent(MultiAgent(
        "analyst", AgentRole.ANALYST,
        "你是技术分析师。基于调研结果,分析技术优势、挑战、趋势。给出独立判断。",
        client,
    ))
    orch.add_agent(MultiAgent(
        "writer", AgentRole.WRITER,
        "你是报告撰写者。把调研和分析整合成结构化报告(含摘要、正文、结论)。",
        client,
    ))
    orch.add_agent(MultiAgent(
        "reviewer", AgentRole.REVIEWER,
        "你是审稿者。检查报告的事实准确性、逻辑完整性、表达清晰度。给出修改建议。",
        client,
    ))

    report = orch.run_report_pipeline("大模型 Agent 技术现状")
    print("\n=== 最终报告 ===")
    print(report)
```

**代码题答题建议**:

1. **先讲设计思路再写代码**(2-3 分钟): 说明你选什么方向、核心模块怎么拆、关键设计点。这展示"先想清楚再动手"的工程素养。
2. **代码要能跑通核心逻辑**: 不需要完美,但核心路径(检索→rerank→context / 循环→工具调用→答案 / 消息传递→协作)要跑通。
3. **边写边讲关键决策**: "这里用 dataclass 是因为...""这里加 min_score_threshold 是为了兜底..."。
4. **主动说边界情况**: 空结果、超长 context、工具调用失败、最大步数超限——这些兜底体现工程经验。
5. **留 3 分钟讲扩展**: 如果时间不够,说说"生产环境还会加什么"(缓存、监控、A/B、权限)。面试官会加分。

</details>

---

### Q10: 如果给你一个新的 Agent 项目,你第一周/第一个月/前三个月分别做什么?

<details>
<summary>点击展开答案</summary>

**问题背景**

这是"规划与执行"题,本质在问"你能不能独立 lead 一个项目"。面试官想看你有没有"30/60/90 天计划"的思维,以及能不能分清"什么阶段该做什么、不该做什么"。很多候选人一上来就想做 Agent 架构,但真正有经验的人知道: 第一周绝对不该写代码,而该搞清楚"到底要解决什么问题"。

**常见回答(不及格)**

> "第一周搭环境,第一个月做 MVP,前三个月上线优化。"

问题: ①太笼统; ②没有具体产出物; ③没有风险预判; ④没有和业务对齐的节点。

**加分回答(90 分)**

按"第一周 / 第一个月 / 前三个月"三段,每段讲"目标 + 关键动作 + 产出物 + 风险":

> **第一周: 搞清楚"要不要做、做什么、做成什么样"**
>
> **目标**: 不是写代码,是消除不确定性。
>
> **关键动作**:
> 1. **和业务方深聊(2 天)**: 不是听需求,是挖痛点。问三个问题: ①你现在最大的痛点是什么? ②这个痛点一年烧多少钱/时间? ③如果 AI 能解决 80%,你满意吗? 如果业务方说不清痛点或不算账,这个项目大概率是"伪需求"。
> 2. **收集真实问题样本(1 天)**: 让业务方给 30-50 个真实用户问题。这些是后续评估集的种子,也是判断"问题类型分布"的依据。
> 3. **技术可行性判断(2 天)**: 拿 10 个典型问题,用最简方式(直接调 GPT-4 + 简单 prompt)跑一遍,看效果。这叫"smoke test"——如果最简方案效果就不错,说明可行; 如果很差,要分析是"模型不行""数据不够"还是"问题本身不适合 AI"。
> 4. **竞品/方案调研(1 天)**: 看市面上类似场景怎么做的,避免重复造轮子。
> 5. **风险预判(1 天)**: 列出 top-5 风险(数据不够、效果不达标、成本超预算、合规问题、用户不买单),每个风险定一个"止损标准"。
>
> **产出物**:
> - 《项目可行性评估报告》(含痛点、ROI 预估、技术可行性、风险清单)
> - 30-50 条真实问题样本
> - Smoke test 结果
>
> **关键决策点**: 第一周末要决定"做还是不做、做多大范围"。如果可行性不足,敢于说"不做"比硬上更负责任。
>
> **风险**: 业务方期望过高。应对: 用 smoke test 结果对齐预期,明确"AI 能做到 X 程度,不是 100%"。

> **第一个月: 做出能用的 MVP,用数据证明价值**
>
> **目标**: 不是做完美系统,是做"最小可用"的东西,让真实用户用起来。
>
> **关键动作**:
> 1. **第 1-2 周: 搭基建 + 做核心链路**
>    - 技术选型定下来(参考 Q3)
>    - 搭开发环境 + 评估流水线
>    - 实现核心 RAG/Agent 链路(先用最简方案: 固定 chunk + 向量检索 + GPT-4 生成)
>    - 准备评估集(基于第一周的 50 条,扩展到 100 条,请业务专家标注)
> 2. **第 3 周: 内部测试 + 迭代优化**
>    - 内部团队试用,收集 bad case
>    - 针对 top-10 bad case 优化(调 chunk、调 prompt、补数据)
>    - 跑评估,目标: 核心指标达到"可用线"(准确率 > 70%,拒答率 < 20%)
> 3. **第 4 周: 灰度上线 + 数据验证**
>    - 灰度给 10-20 个种子用户
>    - 每天看 bad case,每天小迭代
>    - 收集用户满意度数据
>    - 月底出第一份《MVP 效果报告》
>
> **产出物**:
> - 可运行的 MVP 系统(部署在测试/预发环境)
> - 100 条评估集 + 评估报告
> - 灰度用户的真实使用数据
> - 《MVP 效果报告》(含技术指标 + 业务指标 + 用户反馈)
>
> **关键决策点**: 月末要决定"是否扩大灰度"。如果核心指标达标且用户反馈正向,扩大到 100-200 人; 如果不达标,分析根因,要么优化要么止损。
>
> **风险**: 范围蔓延(业务方不断加需求)。应对: MVP 阶段严格锁范围,新需求进 backlog,不进当前迭代。

> **前三个月: 从"能用"到"好用",建立长期运营机制**
>
> **目标**: 系统稳定、效果持续提升、有可复制的运营机制。
>
> **关键动作**:
> 1. **第 2 个月: 规模化 + 优化**
>    - 全量上线(所有目标用户)
>    - 建立监控告警(参考 Q2)
>    - 建立反馈闭环(参考 Q7)
>    - 持续优化: 每个双周迭代聚焦 top bad case
>    - 成本优化: 加缓存、调模型路由、降 token 消耗
>    - 月底目标: 核心指标比 MVP 提升 10 个百分点
> 2. **第 3 个月: 沉淀机制 + 探索扩展**
>    - 沉淀 SOP: 把踩过的坑、最佳实践写成文档
>    - 沉淀工具: 评估流水线、chunk 可视化、bad case 归因工具做成通用组件
>    - 探索扩展: 基于现有能力,看能否复制到相邻场景(比如从"知识库问答"扩展到"工单辅助")
>    - 季度复盘: 算真实 ROI(参考 Q5),决定下季度方向
>
> **产出物**:
> - 稳定运行的生产系统(99.5% 可用性)
> - 完整的监控告警 + 反馈闭环
> - 团队 SOP + 通用工具
> - 《季度复盘报告》(含真实 ROI、经验沉淀、下季度规划)
>
> **关键决策点**: 季末要决定"继续深化还是横向扩展"。如果当前场景 ROI 仍在上行,继续深化; 如果边际收益递减,横向复制到新场景。
>
> **风险**: 系统稳定性(用户量上来后暴露的瓶颈)。应对: 第 2 个月重点做压测和限流,别等出事再补。

> **30/60/90 天计划速览表**
>
> | 时间 | 核心目标 | 关键产出 | 决策点 |
> |------|---------|---------|--------|
> | 第 1 周 | 消除不确定性 | 可行性报告、问题样本、smoke test | 做不做 |
> | 第 1 个月 | MVP 证明价值 | 可用系统、评估集、灰度数据 | 扩大还是止损 |
> | 第 2 个月 | 规模化 + 优化 | 全量系统、监控闭环 | 持续投入 |
> | 第 3 个月 | 沉淀 + 探索 | SOP、工具、季度复盘 | 深化还是扩展 |

**追问应对**

- **追问 1: "第一周不写代码,业务方嫌你慢怎么办?"**
  答: 我会用"省时间"的话术沟通: "第一周搞清楚方向,能避免后面 3 周白做。"并给出"快速可见的产出"——smoke test 结果让业务方看到"AI 确实能做",他们会更耐心。如果业务方坚持"立刻写代码",我会妥协: 第一周前 2 天做可行性,后 5 天开始搭环境,但坚持"不搞清需求不动核心代码"。

- **追问 2: "如果三个月效果不达标,怎么办?"**
  答: 先分析是"技术不达标"还是"预期不合理"。如果是技术问题,看是模型能力不足(等模型升级或换模型)、数据不足(补数据)、还是方案选错(重构)。如果是预期问题,和业务方重新对齐"什么是可接受的效果"。如果两者都不行,止损下线——这不可耻,可耻的是"硬撑着烧钱"。

- **追问 3: "你怎么判断一个 Agent 项目成功还是失败?"**
  答: 三个层面: ①业务价值——ROI > 1 且用户在用(不是被强制用); ②技术效果——核心指标稳定达标且持续改善; ③团队成长——团队沉淀了可复制的方法论和工具。三者都有算成功; 只有业务价值没有团队成长,算"侥幸成功"(下个项目可能复现不了); 三者都没有,失败。

</details>
