# Day 23 — 阿里巴巴 Agent 面试专项

> **学习目标**: 掌握阿里巴巴(通义千问/达摩院/阿里云)Agent 岗位的面试套路,熟悉电商场景、云运维场景的 Agent 系统设计,能独立手撕电商客服 Agent 与 AIOps Agent。
>
> **面试定位**: 阿里的 Agent 岗位分布在三条主线 —— 通义实验室(大模型底座 + Agent 框架)、达摩院(算法研究 + 垂直 Agent)、阿里云(企业级 Agent 落地 + AIOps)。面试官偏爱"从业务场景反推系统设计、再落到模型与工程细节"的答题路径,且对**电商知识图谱、RAG 增量更新、Function Calling 原理、推理性能优化**有极高要求。
>
> **建议用时**: 6-8 小时(知识图谱 30min + 10 道题 4-5h + 自测 1h + 延伸阅读 30min)。

---

## 今日知识图谱

```
阿里 Agent 面试考点
├── 1. 岗位与流程
│   ├── 通义实验室 — 大模型底座/Agent框架/通义千问
│   ├── 达摩院 — 算法研究/垂直Agent(医疗/法律/金融)
│   ├── 阿里云 — 企业级落地/AIOps/智能客服
│   └── 考察重点 — 场景反推设计 + 模型原理 + 工程深度
│
├── 2. 电商场景 (核心战场)
│   ├── 智能客服 Agent
│   │   ├── 意图识别 (LLM + 规则双通道)
│   │   ├── 商品检索 (向量召回 + 精排)
│   │   ├── 订单/物流查询 (API + 知识图谱)
│   │   ├── 售后处理 (退换货/退款/补偿)
│   │   └── 人工转接 (情绪检测 + 复杂度判断)
│   ├── RAG 知识库
│   │   ├── 商品信息增量更新 (双流: 离线全量 + 在线增量)
│   │   ├── 多模态检索 (图文/视频)
│   │   └── 个性化重排 (用户画像 + 实时行为)
│   └── 多 Agent 协作
│       ├── 导购 Agent → 推荐 Agent → 议价 Agent
│       └── 供应链优化 (库存/物流/选品)
│
├── 3. 云服务场景 (阿里云重点)
│   ├── AIOps Agent
│   │   ├── 故障检测 (指标异常/日志聚类/调用链)
│   │   ├── 根因分析 (知识图谱 + 因果推断)
│   │   ├── 自动修复 (预案库 + 安全沙箱)
│   │   └── 报告生成 (LLM + 结构化模板)
│   └── 企业级 Agent 平台
│       ├── 百炼平台 (Agent构建/编排/部署)
│       └── 模型即服务 (MaaS) 选型
│
├── 4. 模型与原理
│   ├── 通义千问选型
│   │   ├── Qwen-Max / Qwen-Plus / Qwen-Turbo 取舍
│   │   ├── 开源版 (Qwen2.5/Qwen3) 微调
│   │   └── Function Calling 原生支持
│   ├── Function Calling 底层
│   │   ├── SFT 训练 (工具描述 → 调用格式)
│   │   ├── ReAct vs FC 范式对比
│   │   └── 并行调用 / 嵌套调用
│   └── 推理优化
│       ├── 模型层 (量化/KV Cache/投机解码)
│       ├── Prompt 层 (压缩/缓存/分段)
│       └── 系统层 (并发/批处理/边缘)
│
└── 5. 工程与落地
    ├── 评测体系 (业务指标 + Agent指标)
    ├── 成本控制 (Token/调用/模型分级路由)
    ├── 安全合规 (内容审核/数据脱敏/权限)
    └── 灰度发布 (AB实验/流量切分/回滚)
```

---

## 面试题(共 10 道)

### Q1: 阿里 Agent 岗位有什么特点? 面试流程和考察重点是什么?

<details>
<summary>点击展开答案</summary>

**一、阿里 Agent 三大岗位线**

| 岗位线 | 团队 | 重点方向 | 技术栈特点 |
|--------|------|----------|-----------|
| 通义实验室 | 通义千问团队 | 大模型底座 + Agent 框架(百炼/通义灵码) | 偏模型自研、训练微调、推理优化 |
| 达摩院 | NLP/决策智能/医疗AI | 垂直 Agent 算法研究 | 偏论文、SOTA 追踪、创新性 |
| 阿里云 | 智能客服/AIOps/百炼平台 | 企业级 Agent 落地 | 偏工程、稳定性、商业化 |

**二、面试流程(典型 4-5 轮)**

1. **一面(技术面, 1h)**: 基础八股 + 算法题。重点考 LLM 原理(Function Calling、RAG、Attention)、手撕代码(中等难度)。
2. **二面(技术面, 1h)**: 项目深挖 + 系统设计。会追问"为什么这么设计、有没有更好的方案、上线后指标怎么定"。
3. **三面(交叉面/主管面, 1h)**: 综合能力。考业务理解、技术规划、跨团队协作。常问"如果让你从 0 到 1 搭一个 XX Agent,你怎么做"。
4. **四面(高管面, 45min)**: 价值观(阿里的"客户第一、拥抱变化")+ 职业规划 + 开放性问题。
5. **HR 面(30min)**: 稳定性、薪资、离职原因。阿里 HR 一票否决权,务必重视。

**三、考察重点(阿里特色)**

- **业务反推能力**: 阿里面试官喜欢从一个业务场景出发,让你反推系统设计、模型选型、指标定义。例如"双 11 客服峰值 10w QPS,你的 Agent 怎么扛"。
- **模型原理深度**: 不只是会用 API,要能讲清 Function Calling 的训练原理、RAG 的检索-生成联合优化、KV Cache 的内存计算。
- **工程落地思维**: 上线指标怎么定? 灰度怎么做? 成本怎么控? 故障怎么 recover? 阿里特别看重"能把 Demo 变成生产系统"的能力。
- **数据驱动**: 强调用数据说话。"你怎么知道你的 Agent 比上版好? 评测集怎么建? AB 实验怎么设计?"
- **阿里技术生态**: 熟悉通义千问、百炼平台、PAI、SLS、Sentinel 等阿里技术栈是加分项。

**四、答题策略**

- 用 **STAR + 业务指标** 框架答项目: Situation(业务场景) → Task(目标 + 指标) → Action(技术方案) → Result(数据结果)。
- 系统设计题按 **业务拆解 → 架构分层 → 模型选型 → 工程保障 → 指标评测** 五段式回答。
- 遇到不会的,先承认,再给出"我会怎么去查/去验证"的思路,阿里喜欢有方法论的人。

</details>

---

### Q2: 设计淘宝/天猫智能客服 Agent,支持商品咨询、订单查询、售后处理

<details>
<summary>点击展开答案</summary>

**一、需求拆解**

| 模块 | 核心诉求 | 量化指标 |
|------|----------|----------|
| 商品咨询 | 用户问"这款手机续航多久",Agent 基于商品详情/参数/评价回答 | 准确率 ≥ 92%,延迟 P95 ≤ 2s |
| 订单查询 | 查物流、查订单状态、改地址 | 意图识别 F1 ≥ 0.95 |
| 售后处理 | 退换货、退款、补偿协商 | 自动解决率 ≥ 60% |
| 人工转接 | 情绪激动/复杂问题转人工 | 转接准确率 ≥ 90% |
| 峰值承载 | 双 11 峰值 10w+ QPS | 可用性 ≥ 99.95% |

**二、整体架构(分层)**

```
┌─────────────────────────────────────────────┐
│  接入层: Web/App/小程序/电话 → 统一 Gateway  │
├─────────────────────────────────────────────┤
│  对话管理层                                  │
│   ├── 多轮状态机 (Session/Context)           │
│   ├── 意图路由 (LLM + 规则双通道)            │
│   └── 槽位填充 (Slot Filling)                │
├─────────────────────────────────────────────┤
│  Agent 编排层 (多 Agent 协作)                │
│   ├── Router Agent (主控)                    │
│   ├── 商品 Agent (RAG + 商品图谱)            │
│   ├── 订单 Agent (API + 工具调用)            │
│   ├── 售后 Agent (流程引擎 + 规则)           │
│   └── 安抚 Agent (情绪检测 → 转人工)         │
├─────────────────────────────────────────────┤
│  能力层                                      │
│   ├── RAG 引擎 (商品知识库 + 增量更新)        │
│   ├── 工具服务 (订单/物流/库存 API)          │
│   ├── 商品图谱 (品类/参数/关联)              │
│   └── 用户画像 (历史/偏好/VIP)               │
├─────────────────────────────────────────────┤
│  模型层 (分级路由)                           │
│   ├── Qwen-Turbo (简单意图, 低延迟低成本)    │
│   ├── Qwen-Plus (常规对话)                   │
│   └── Qwen-Max (复杂推理/情绪安抚)           │
├─────────────────────────────────────────────┤
│  基础设施: Sentinel限流 / SLS日志 / 监控告警 │
└─────────────────────────────────────────────┘
```

**三、关键设计点**

1. **意图路由双通道**: 规则(正则 + 关键词)处理高频确定意图(查物流/查订单),LLM 处理长尾模糊意图。双通道并行,LLM 兜底,既快又准。

2. **商品 RAG 增量更新**(阿里重点):
   - 离线全量: 每天凌晨 T+1 全量重建向量索引(商品上下架频繁)。
   - 在线增量: 监听商品变更消息( Canal 订阅 binlog),实时 upsert 向量。
   - 双写策略: 写入时同时更新 ES(关键词检索) + 向量库(语义检索),检索时做混合召回。

3. **多轮上下文管理**: 用 SessionStore(Redis)存最近 N 轮对话,超过 token 预算时做摘要压缩。关键信息(订单号、商品 ID)用结构化 slot 持久化,避免 LLM 遗忘。

4. **情绪检测转人工**: 用一个小模型(蒸馏的 BERT)做实时情绪打分,分数超阈值或检测到"投诉/差评/12315"等关键词,立即转人工并带上完整上下文摘要。

5. **峰值保障**:
   - 模型分级路由: 80% 流量走 Qwen-Turbo,15% 走 Plus,5% 走 Max。
   - 高频问答缓存: 对"查物流""查订单状态"等高频 query 做 Redis 缓存,命中率 40%+。
   - 降级策略: 模型超时 → 走规则模板 → 转人工,保证不崩。

**四、评测指标体系**

| 维度 | 指标 | 目标 |
|------|------|------|
| 业务 | 自动解决率 | ≥ 60% |
| 业务 | 转人工率 | ≤ 25% |
| 业务 | 用户满意度(CSAT) | ≥ 4.3/5 |
| 技术 | 意图识别 F1 | ≥ 0.95 |
| 技术 | RAG 准确率(人工标注) | ≥ 92% |
| 技术 | P95 延迟 | ≤ 2s |
| 技术 | 可用性 | ≥ 99.95% |
| 成本 | 单次对话成本 | ≤ 0.05 元 |

**五、面试加分点**

- 主动提"商品信息时效性": 阿里电商场景商品上下架极频繁,RAG 必须做增量更新,这是区别于通用 RAG 的关键。
- 提"双 11 降级预案": 体现工程思维。
- 提"人工坐席协同": Agent 不是替代人,是辅助人,转接时要带摘要、带建议、带用户画像。

</details>

---

### Q3: 通义千问做 Agent 底座有什么优势? 如何做模型选型?

<details>
<summary>点击展开答案</summary>

**一、通义千问做 Agent 底座的优势**

| 优势维度 | 具体说明 |
|----------|----------|
| **中文能力** | 中文语料占比高,电商/政务/金融中文场景表现优于同规模海外模型 |
| **Function Calling 原生支持** | Qwen 从 1.5 版本起原生训练 FC 能力,工具调用格式稳定、准确率高 |
| **长上下文** | Qwen-Plus/Max 支持 128K~1M 上下文,适合长对话 + 大 RAG |
| **多模态** | Qwen-VL 支持图文理解,适合商品图、截图、发票等电商场景 |
| **开源生态** | Qwen2.5/Qwen3 全系列开源,可私有化部署 + 微调,数据不出域 |
| **阿里云集成** | 与百炼平台、PAI、SLS 深度集成,部署运维成本低 |
| **成本** | Qwen-Turbo 价格仅为 GPT-4 的 1/10,大规模商用可承受 |
| **合规** | 国内备案完成,政企/金融场景合规无忧 |

**二、模型选型矩阵**

```
┌──────────────┬─────────────┬──────────────┬──────────────┬──────────────┐
│   场景       │  推荐模型    │  延迟         │  成本        │  典型用法     │
├──────────────┼─────────────┼──────────────┼──────────────┼──────────────┤
│ 简单意图分类  │ Qwen-Turbo  │ 200-500ms    │ 极低         │ 路由/槽位填充  │
│ 常规对话      │ Qwen-Plus  │ 500ms-1.5s   │ 中           │ 客服主对话    │
│ 复杂推理      │ Qwen-Max   │ 1-3s         │ 高           │ 售后协商/规划  │
│ 多模态理解    │ Qwen-VL-Max│ 1-2s         │ 中高         │ 商品图/发票    │
│ 私有化部署    │ Qwen2.5-72B│ 取决于硬件    │ 一次性投入    │ 金融/政务     │
│ 端侧 Agent   │ Qwen2.5-7B │ 100-300ms    │ 免费         │ 离线/低延迟   │
│ 代码 Agent   │ Qwen-Coder │ 500ms-2s     │ 中           │ 通义灵码      │
└──────────────┴─────────────┴──────────────┴──────────────┴──────────────┘
```

**三、选型方法论(答题框架)**

1. **先定场景与指标**: 业务场景是什么? 延迟、成本、准确率、合规要求分别是什么?
2. **再做能力评估**: 在评测集(业务真实数据)上跑 benchmark,对比候选模型。
3. **分级路由**: 单一模型无法满足所有场景,按"难度 → 模型"分级路由,80% 流量用小模型控成本,20% 用大模型保效果。
4. **微调兜底**: 对垂直场景(电商/法律),用业务数据做 SFT 或 LoRA,小模型微调后可逼近大模型效果。
5. **持续评测**: 上线后建在线评测 pipeline,每日跑评测集,模型退化时自动切回旧版。

**四、面试加分话术**

> "模型选型不是选'最强的',是选'最匹配业务约束的'。我会先用业务真实数据建一个 500-1000 条的评测集,然后跑 Qwen-Turbo/Plus/Max + 开源模型的对比,看哪个在'准确率 vs 成本 vs 延迟'三角上最契合。线上一般用分级路由: 简单意图走 Turbo,复杂推理走 Max,中间走 Plus,这样整体成本可控、体验有保障。"

**五、易错提醒**

- 不要只说"Qwen-Max 最强所以用它" —— 阿里面试官会追问成本和延迟。
- 不要忽略开源版: 政企/金融客户要私有化,必须能讲清 Qwen2.5 系列的部署方案。
- 提到通义灵码(Qwen-Coder)是加分项,显示你了解阿里最新产品矩阵。

</details>

---

### Q4: RAG 在电商知识库中的应用,如何处理商品信息频繁更新?

<details>
<summary>点击展开答案</summary>

**一、电商 RAG 的特殊性(对比通用 RAG)**

| 维度 | 通用 RAG | 电商 RAG |
|------|----------|----------|
| 知识更新频率 | 周/月级 | 分钟级(价格/库存/促销实时变) |
| 知识规模 | 万~百万文档 | 亿级 SKU,每个 SKU 多版本 |
| 查询特征 | 语义问答 | 语义 + 属性过滤 + 个性化 |
| 准确性要求 | 高 | 极高(价格错了直接资损) |
| 多模态 | 少 | 多(图文/视频/直播切片) |

**二、增量更新架构(核心答题点)**

```
┌────────────────────────────────────────────────┐
│  数据源: 商品中心/库存/价格/促销 (binlog)        │
└─────────────────┬──────────────────────────────┘
                  │ Canal 订阅
                  ▼
┌────────────────────────────────────────────────┐
│  变更消息队列 (RocketMQ)                         │
│   ├── 价格变更 → 高优, 实时处理                  │
│   ├── 库存变更 → 高优, 实时处理                  │
│   ├── 详情变更 → 中优, 准实时(5min)              │
│   └── 评价变更 → 低优, 离线 T+1                  │
└─────────────────┬──────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌──────────────┐   ┌──────────────────┐
│ 实时增量管道  │   │ 离线全量重建      │
│ - Embedding  │   │ - 每天凌晨全量    │
│ - 向量 upsert│   │ - 重建索引        │
│ - 版本号管理 │   │ - 对账修正        │
└──────────────┘   └──────────────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
┌────────────────────────────────────────────────┐
│  检索层 (双库 + 混合召回)                        │
│   ├── 向量库 (Milvus/Ha3) — 语义召回            │
│   ├── ES/HA3 — 关键词 + 属性过滤                │
│   └── 融合排序 (RRF + 业务重排)                 │
└────────────────────────────────────────────────┘
```

**三、关键设计点**

1. **变更分级处理**: 不是所有变更都走实时。价格、库存走实时(资损风险);商品详情走准实时;评价走离线。按业务影响分级,平衡成本和时效。

2. **向量增量更新**: 用 `upsert` 而非 `delete + insert`,带版本号(`version_id`),检索时过滤掉过期版本。避免"删了旧的、新的还没写入"的空窗期。

3. **双库冗余 + 灰度切换**: 向量库分主备两套,更新时先写备库,校验通过后切流量。避免更新过程中检索到不一致数据。

4. **价格/库存走 API 不走 RAG**: 价格和库存是强一致性字段,绝不能靠 LLM 从 RAG 生成,必须实时调 API。RAG 只负责"商品描述、参数、使用说明"等弱时效字段。**这是阿里面试高频陷阱题**。

5. **混合召回(语义 + 关键词 + 属性)**:
   - 语义召回: Qwen-Embedding 向量检索,解决"手机续航"→"电池容量"的语义匹配。
   - 关键词召回: BM25/ES,解决 SKU 编号、品牌名等精确匹配。
   - 属性过滤: 先按品类/价格区间/品牌过滤,再在结果集内做向量召回,效率更高。
   - 融合: RRF(Reciprocal Rank Fusion)合并多路结果,再用业务重排模型(CTR 预估)排序。

6. **个性化重排**: 同一个 query,不同用户看到不同结果。结合用户画像(历史浏览/购买/VIP 等级)对召回结果重排。

**四、一致性保障**

- **对账机制**: 每天离线全量重建后,与商品中心主数据对账,发现不一致自动修正。
- **TTL 控制**: 向量库每条记录带 TTL,超过 24h 未更新的标记为"待校验",检索时降权。
- **熔断**: 当增量管道积压超过阈值,自动切到"只读全量索引"模式,避免读到半新半旧数据。

**五、面试加分点**

- 主动区分"强一致字段(API) vs 弱时效字段(RAG)" —— 显示对电商业务的深刻理解。
- 提"双 11 价格秒级变动"场景,讲清为什么价格绝不能进 RAG。
- 提"HA3"(阿里自研检索引擎)是加分项。

</details>

---

### Q5: Agent 在阿里云运维场景的应用 —— 智能诊断与自动修复

<details>
<summary>点击展开答案</summary>

**一、AIOps Agent 的核心场景**

| 场景 | 输入 | 输出 | 难点 |
|------|------|------|------|
| 故障检测 | 指标/日志/调用链 | 异常事件 | 误报率控制 |
| 根因分析 | 异常事件 + 拓扑 | 根因定位 | 因果推断 |
| 自动修复 | 根因 + 预案 | 修复动作 | 安全性 |
| 报告生成 | 故障全过程 | 结构化报告 | 信息完整性 |

**二、整体架构**

```
┌─────────────────────────────────────────────────┐
│  数据采集层 (SLS/CloudMonitor/ARMS)              │
│   指标 / 日志 / 调用链 / 事件                    │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  感知 Agent (故障检测)                           │
│   ├── 时序异常检测 (EWMA/Prophet/孤立森林)       │
│   ├── 日志聚类 + 异常分类 (LLM)                  │
│   └── 调用链分析 (拓扑 + 传播路径)               │
└─────────────────┬───────────────────────────────┘
                  ▼ 故障事件
┌─────────────────────────────────────────────────┐
│  诊断 Agent (根因分析)                           │
│   ├── 知识图谱查询 (服务依赖/变更/容量)          │
│   ├── 因果推断 (Granger/DoCalculus)              │
│   ├── LLM 推理 (结合变更单/告警历史)             │
│   └── 多假设打分 → Top-K 根因                    │
└─────────────────┬───────────────────────────────┘
                  ▼ 根因
┌─────────────────────────────────────────────────┐
│  执行 Agent (自动修复)                           │
│   ├── 预案库匹配 (根因 → 修复动作)               │
│   ├── 安全沙箱预演 (灰度/回滚预案)               │
│   ├── 人工确认 (高危动作)                        │
│   └── 执行 + 验证 (指标恢复确认)                 │
└─────────────────┬───────────────────────────────┘
                  ▼ 修复结果
┌─────────────────────────────────────────────────┐
│  复盘 Agent (报告生成)                           │
│   ├── 时间线梳理 (LLM + 事件流)                  │
│   ├── 影响面评估 (受影响服务/用户/订单)          │
│   ├── 根因总结 + 改进建议                        │
│   └── 结构化报告 (Markdown/Confluence)           │
└─────────────────────────────────────────────────┘
```

**三、关键设计点**

1. **多 Agent 协作 + 人在回路**: 感知 → 诊断 → 执行 → 复盘四个 Agent 串联。高危动作(重启、扩容、切流量)必须人工确认,低危动作(清缓存、重试)可自动执行。安全边界用"动作风险等级 × 影响面"矩阵决定。

2. **根因分析的双重路径**:
   - **知识图谱路径**: 构建服务依赖图、变更图、容量图,故障发生时沿图遍历找最近变更点。
   - **LLM 推理路径**: 把告警、变更单、日志摘要喂给 Qwen-Max,让它做"像 SRE 一样的推理"。
   - 两路结果做融合打分,Top-K 候选根因再由人工或规则确认。

3. **预案库 + 安全沙箱**:
   - 预案库: 历史故障 → 修复动作的映射,按根因类型索引。
   - 沙箱预演: 高危动作先在影子环境/灰度节点试运行,验证无害后再全量执行。
   - 回滚预案: 每个修复动作都配套回滚方案,执行后 5min 内指标未恢复自动回滚。

4. **变更关联分析**: 阿里云 80% 故障由变更引起。诊断 Agent 优先排查最近 30min 的发布、配置变更、扩缩容,这是 SRE 经验的工程化。

5. **报告生成**: LLM 不直接生成报告,而是按结构化模板填空(时间线/影响面/根因/改进项),LLM 只负责"自然语言润色 + 改进建议生成",保证报告完整可控。

**四、评测指标**

| 维度 | 指标 | 目标 |
|------|------|------|
| 检测 | 异常检出率 | ≥ 95% |
| 检测 | 误报率 | ≤ 5% |
| 检测 | 平均检测时间(MTTD) | ≤ 1min |
| 诊断 | 根因 Top-3 命中率 | ≥ 80% |
| 诊断 | 平均诊断时间 | ≤ 5min |
| 修复 | 自动修复成功率 | ≥ 70% |
| 修复 | 平均修复时间(MTTR) | 降低 50% |
| 安全 | 误操作率 | 0(红线) |

**五、面试加分点**

- 强调"人在回路"和"安全边界": 阿里云对线上操作零容忍误操作,自动修复必须有兜底。
- 提"变更关联优先": 体现 SRE 实战经验。
- 提"预案库沉淀": AIOps 不是纯算法,是"经验工程化 + 算法增强"。

</details>

---

### Q6: 如何实现一个支持 Function Calling 的 Agent? 底层原理是什么?

<details>
<summary>点击展开答案</summary>

**一、Function Calling 的本质**

Function Calling(FC)是让 LLM 能"调用外部工具"的能力。本质是: **模型在 SFT 阶段学会了"给定工具描述 + 用户 query,输出结构化的工具调用 JSON"的能力**。它不是模型真的去执行函数,而是模型输出一个"调用意图",由外部执行器去真正执行。

**二、底层原理(训练 + 推理)**

```
┌────────────────────────────────────────────────┐
│  训练阶段 (SFT)                                 │
│  输入: 系统提示 + 工具描述(JSON Schema) + query │
│  标签: 工具调用 JSON (name + arguments)         │
│  损失: 只在工具调用 token 上计算 loss           │
│  数据: 大量(工具描述, query, 调用JSON)三元组    │
└────────────────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│  推理阶段                                       │
│  1. 拼接 system + tools_schema + user_query    │
│  2. 模型生成 → 解析输出                          │
│     ├── 普通文本 → 直接返回用户                  │
│     └── tool_calls JSON → 执行器调用真实函数     │
│  3. 把函数结果作为 tool_result 回填              │
│  4. 模型基于 result 继续生成(可能再次调用)       │
│  5. 循环直到模型输出 final_answer               │
└────────────────────────────────────────────────┘
```

**三、FC vs ReAct 对比**

| 维度 | Function Calling | ReAct |
|------|------------------|-------|
| 输出格式 | 结构化 JSON | 自由文本(Thought/Action/Observation) |
| 解析可靠性 | 高(JSON Schema 约束) | 中(正则解析易错) |
| 训练要求 | 需专门 SFT | Prompt 即可,零训练 |
| 并行调用 | 原生支持多工具并行 | 需特殊 prompt 设计 |
| 通用性 | 绑定特定模型 | 任何 LLM 都能用 |
| 适用场景 | 生产环境、工具多 | 原型、跨模型迁移 |

**四、最小实现(Python)**

```python
import json
from typing import Callable

# 工具注册表
TOOL_REGISTRY: dict[str, Callable] = {}
TOOL_SCHEMAS: list[dict] = []

def tool(name: str, description: str, parameters: dict):
    """工具装饰器,自动注册 schema"""
    def decorator(func: Callable):
        TOOL_REGISTRY[name] = func
        TOOL_SCHEMAS.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        })
        return func
    return decorator

# 定义工具
@tool(
    name="query_order",
    description="根据订单号查询订单状态和物流信息",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "订单编号"}
        },
        "required": ["order_id"]
    }
)
def query_order(order_id: str) -> dict:
    # 实际场景调用订单服务
    return {"order_id": order_id, "status": "shipped", "logistics": "SF1234, 已到杭州"}

@tool(
    name="search_product",
    description="根据关键词搜索商品,返回价格和库存",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "搜索关键词"},
            "top_k": {"type": "integer", "description": "返回数量", "default": 3}
        },
        "required": ["keyword"]
    }
)
def search_product(keyword: str, top_k: int = 3) -> list[dict]:
    return [{"id": f"P{i}", "name": f"{keyword}型号{i}", "price": 1000+i*100, "stock": 50-i} for i in range(top_k)]

# 模拟 LLM(实际替换为 Qwen API)
def llm_call(messages: list[dict], tools: list[dict]) -> dict:
    """模拟支持 FC 的 LLM,真实场景调用 Qwen/OpenAI API"""
    # 这里用规则模拟,真实场景是模型生成
    last_msg = messages[-1]["content"]
    if "订单" in last_msg and any(c.isdigit() for c in last_msg):
        import re
        match = re.search(r"\d{10,}", last_msg)
        if match:
            return {
                "content": None,
                "tool_calls": [{"id": "call_1", "function": {"name": "query_order", "arguments": json.dumps({"order_id": match.group()})}}]
            }
    if "搜" in last_msg or "找" in last_msg:
        return {
            "content": None,
            "tool_calls": [{"id": "call_1", "function": {"name": "search_product", "arguments": json.dumps({"keyword": "手机", "top_k": 3})}}]
        }
    return {"content": f"已收到您的问题: {last_msg}", "tool_calls": None}

# Agent 主循环
def run_agent(user_query: str, max_turns: int = 5) -> str:
    messages = [
        {"role": "system", "content": "你是淘宝智能客服,可以查询订单和搜索商品。"},
        {"role": "user", "content": user_query}
    ]
    for turn in range(max_turns):
        # 1. 调 LLM
        resp = llm_call(messages, TOOL_SCHEMAS)
        # 2. 无工具调用,直接返回
        if not resp.get("tool_calls"):
            return resp["content"]
        # 3. 有工具调用,执行并回填
        messages.append({"role": "assistant", "content": None, "tool_calls": resp["tool_calls"]})
        for tc in resp["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"])
            print(f"[Turn {turn}] 调用工具: {fn_name}({fn_args})")
            result = TOOL_REGISTRY[fn_name](**fn_args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False)
            })
    return "达到最大轮次,转人工"

# 测试
if __name__ == "__main__":
    print(run_agent("帮我查一下订单 1234567890 的物流"))
    print("---")
    print(run_agent("帮我搜一下手机"))
```

**五、关键工程细节**

1. **工具描述要精准**: Schema 写得越清楚,模型调用越准。参数 description 要写清"格式、取值范围、示例"。
2. **错误处理**: 工具执行失败要把错误信息回填给模型(而不是直接抛异常),让模型决定重试还是换工具。
3. **并行调用**: Qwen-Max 支持一次输出多个 tool_calls,执行器可并行执行,降低延迟。
4. **嵌套调用**: 工具 A 的结果作为工具 B 的参数,需要多轮循环,设 max_turns 防死循环。
5. **token 控制**: 工具描述会占 token,工具多时要做"工具检索"(先检索 Top-K 相关工具再喂给模型)。

**六、面试加分点**

- 能讲清"FC 是 SFT 学出来的能力,不是 Prompt 工程" —— 体现原理深度。
- 提"工具检索": 当工具数量超过 50 个,全部塞进 prompt 会爆 token,需要先检索 —— 显示工程经验。
- 对比 ReAct 的优劣,说明什么场景用哪个。

</details>

---

### Q7: 多 Agent 在供应链优化中的应用

<details>
<summary>点击展开答案</summary>

**一、场景背景**

阿里供应链覆盖: 选品 → 采购 → 库存 → 物流 → 履约 → 售后。传统用运筹优化求解器(如 Gurobi),但面对"需求不确定、突发事件多、目标多元"的复杂场景,纯数学规划不够,多 Agent + LLM 能做"定性决策 + 定量优化"结合。

**二、多 Agent 架构**

```
┌────────────────────────────────────────────────┐
│  协调 Agent (Supervisor, Qwen-Max)              │
│   全局目标: 最小化成本 + 最大化履约率 + 满意度    │
└──────┬─────────┬─────────┬─────────┬───────────┘
       │         │         │         │
       ▼         ▼         ▼         ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│需求预测  ││库存 Agent││物流 Agent││供应商    │
│Agent     ││          ││          ││Agent     │
│- 销量预测││- 补货决策││- 路径规划││- 寻源    │
│- 趋势分析││- 调拨决策││- 容量调度││- 议价    │
│- 异常预警││- 滞销处理││- 突发应对││- 风险评估│
└──────────┘└──────────┘└──────────┘└──────────┘
       │         │         │         │
       └─────────┴─────────┴─────────┘
                  │ 共享状态
                  ▼
┌────────────────────────────────────────────────┐
│  共享黑板 (Blackboard)                          │
│   需求预测 / 库存水位 / 物流容量 / 供应商状态    │
└────────────────────────────────────────────────┘
```

**三、各 Agent 职责**

| Agent | 输入 | 输出 | 模型/算法 |
|-------|------|------|----------|
| 需求预测 | 历史销量/促销/天气/舆情 | 未来 7-30 天销量预测 | LLM(舆情) + 时序模型(销量) |
| 库存 Agent | 预测 + 当前水位 + 在途 | 补货量/调拨方案 | LLM 规则 + 运筹优化 |
| 物流 Agent | 订单 + 仓配容量 + 路况 | 路径规划/分仓决策 | 运筹 + LLM 突发应对 |
| 供应商 Agent | 采购需求 + 供应商画像 | 寻源/议价策略 | LLM 议价 + 规则筛选 |
| 协调 Agent | 各 Agent 提案 + 全局目标 | 冲突仲裁/最终决策 | Qwen-Max 多目标推理 |

**四、协作机制**

1. **共享黑板模式**: 各 Agent 把中间结果写到共享黑板,其他 Agent 可读取,解耦 Agent 间通信。
2. **提案-仲裁**: 各 Agent 基于自身目标提方案,协调 Agent 做全局仲裁(如库存要补货 vs 物流容量不足,协调 Agent 决定推迟补货还是加运力)。
3. **迭代优化**: 多轮协商,每轮各 Agent 根据黑板更新提案,直到收敛或达到轮次上限。
4. **人在回路**: 高影响决策(千万级采购、关仓)人工确认。

**五、关键技术点**

- **LLM + 运筹结合**: LLM 负责"定性决策"(该不该补货、该不该寻新源),运筹负责"定量优化"(补多少、选哪家)。两者不是替代是互补。
- **突发事件应对**: LLM 优势在于处理"未见过"的事件(如疫情封路、供应商倒闭),基于常识推理给出应对,这是规则系统做不到的。
- **多目标权衡**: 成本 vs 履约率 vs 满意度,用 LLM 做 Pareto 前沿上的"语义权衡",比纯加权更灵活。

**六、面试加分点**

- 强调"LLM 不替代运筹,是增强" —— 避免被质疑"为什么不用 Gurobi"。
- 提"突发事件应对是 LLM 独有价值" —— 体现对 LLM 能力边界的清晰认知。
- 提"共享黑板 + 提案仲裁"是经典多 Agent 协作模式,显示理论功底。

</details>

---

### Q8: Agent 推理速度慢,如何优化? (模型/Prompt/缓存/并发)

<details>
<summary>点击展开答案</summary>

**一、优化全景图**

```
┌─────────────────────────────────────────────────┐
│  模型层优化 (单次推理加速)                        │
│   ├── 量化 (INT8/INT4)                          │
│   ├── KV Cache 优化 (PagedAttention)            │
│   ├── 投机解码 (Speculative Decoding)           │
│   ├── Flash Attention / MLA                     │
│   └── Continuous Batching                       │
├─────────────────────────────────────────────────┤
│  Prompt 层优化 (减少输入 token)                  │
│   ├── Prompt 压缩 (LLMLingua)                   │
│   ├── 上下文摘要 (长对话压缩)                    │
│   ├── Few-shot 精简 (动态选样本)                 │
│   └── 工具描述精简 (按需加载)                    │
├─────────────────────────────────────────────────┤
│  缓存层优化 (避免重复计算)                        │
│   ├── 语义缓存 (query → response 近似匹配)      │
│   ├── 前缀缓存 (system prompt 复用 KV)          │
│   └── 工具结果缓存 (相同参数不重复调用)          │
├─────────────────────────────────────────────────┤
│  系统层优化 (吞吐与并发)                          │
│   ├── 模型分级路由 (简单走小模型)                │
│   ├── 并行调用 (多工具同时执行)                  │
│   ├── 流式输出 (首 token 延迟优化)               │
│   └── 异步 pipeline (检索/工具/生成重叠)         │
└─────────────────────────────────────────────────┘
```

**二、各层详解**

**1. 模型层**

| 技术 | 原理 | 加速比 | 代价 |
|------|------|--------|------|
| INT8 量化 | 权重从 FP16 → INT8,内存减半 | 1.5-2x | 轻微精度损失 |
| INT4 量化(GPTQ/AWQ) | 权重 4bit | 2-3x | 精度损失较大 |
| KV Cache | 缓存已计算 K/V,避免重复 | 显著 | 占显存 |
| PagedAttention | 分页管理 KV Cache,减少碎片 | 2-4x 吞吐 | 实现复杂(vLLM) |
| 投机解码 | 小模型先_draft,大模型并行验证 | 1.5-2x | 需双模型 |
| Flash Attention | 优化 Attention 计算的 IO | 1.5-3x | 无精度损失 |
| Continuous Batching | 动态拼 batch,提升 GPU 利用率 | 3-8x 吞吐 | 需框架支持 |

**2. Prompt 层**

- **Prompt 压缩**: 用 LLMLingua 等工具,去除 prompt 中冗余 token,可压缩 2-10x,精度损失可控。
- **上下文摘要**: 长对话超过阈值时,用小模型对历史对话做摘要,只保留摘要 + 最近 N 轮。
- **动态 Few-shot**: 不固定 few-shot 样本,根据 query 检索最相似的 2-3 个样本,既准又省 token。
- **工具描述按需加载**: 工具多时,先检索 Top-K 相关工具,只把这 K 个的 schema 塞进 prompt。

**3. 缓存层**

- **语义缓存**: 对用户 query 做 embedding,在缓存库找相似度 > 0.95 的历史 query,直接返回其答案。电商客服场景命中率 30-50%。
- **前缀缓存**: system prompt + few-shot 是固定的,这部分 KV Cache 可跨请求复用,vLLM/SGLang 原生支持。
- **工具结果缓存**: 相同参数的工具调用结果缓存(如查同一个订单 5 分钟内不重复调)。

**4. 系统层**

- **分级路由**: 80% 简单 query 走 Qwen-Turbo(200ms),20% 走 Qwen-Plus/Max(1-3s),整体 P95 由小模型决定。
- **并行工具调用**: Qwen 支持一次返回多个 tool_calls,执行器并行跑,延迟从 Σ 变 max。
- **流式输出**: 首 token 延迟(TTFT)对体验影响最大,流式输出让用户在 200ms 内看到响应开始。
- **异步 pipeline**: 检索、工具调用、生成三个阶段用异步 pipeline 重叠,如检索阶段就预启动生成。

**三、量化收益估算(电商客服场景)**

| 优化项 | 优化前 | 优化后 | 收益 |
|--------|--------|--------|------|
| 原始(无优化) | P95 5s | - | - |
| 分级路由 | 5s | 2.5s | -50% |
| +语义缓存(40%命中) | 2.5s | 1.8s | -28% |
| +Prompt 压缩 | 1.8s | 1.4s | -22% |
| +并行工具调用 | 1.4s | 1.1s | -21% |
| +流式(TTFT) | TTFT 800ms | TTFT 200ms | -75% |
| **综合** | **P95 5s** | **P95 1.1s** | **-78%** |

**四、面试加分点**

- 给出"量化收益估算表": 阿里面试官喜欢数据驱动的回答。
- 提"分级路由是 ROI 最高的优化": 80% 流量走小模型,成本和延迟双降。
- 提"语义缓存要兜底": 缓存命中也要做"答案时效性校验",避免返回过期信息(如价格变了)。
- 区分"延迟优化" vs "吞吐优化": 单请求看延迟,高并发看吞吐,Continuous Batching 是吞吐利器。

</details>

---

### Q9: 手撕代码 — 实现一个电商客服 Agent

<details>
<summary>点击展开完整代码</summary>

**需求**: 实现一个支持商品检索、订单查询、退换货处理、人工转接的电商客服 Agent。

```python
"""
电商客服 Agent 完整实现
- 商品检索: 向量召回 + 关键词混合
- 订单查询: 调用订单 API
- 退换货处理: 状态机驱动
- 人工转接: 情绪检测 + 复杂度判断
- 多轮对话: 上下文管理 + 摘要压缩
"""
import json
import re
import time
import hashlib
from typing import Callable, Any
from dataclasses import dataclass, field
from enum import Enum

# ============================================================
# 第一部分: 工具系统 (Function Calling 基础设施)
# ============================================================

TOOL_REGISTRY: dict[str, Callable] = {}
TOOL_SCHEMAS: list[dict] = []

def tool(name: str, description: str, parameters: dict):
    def decorator(func):
        TOOL_REGISTRY[name] = func
        TOOL_SCHEMAS.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            }
        })
        return func
    return decorator

# ============================================================
# 第二部分: 模拟数据与服务
# ============================================================

# 模拟商品库
PRODUCT_DB = [
    {"id": "P001", "name": "华为 Mate60 Pro", "price": 6999, "stock": 120,
     "category": "手机", "desc": "麒麟9000S, 卫星通话, 5000mAh"},
    {"id": "P002", "name": "小米14 Ultra", "price": 6499, "stock": 80,
     "category": "手机", "desc": "骁龙8Gen3, 徕卡光学, 2K屏"},
    {"id": "P003", "name": "AirPods Pro 2", "price": 1899, "stock": 300,
     "category": "耳机", "desc": "主动降噪, 空间音频, USB-C"},
    {"id": "P004", "name": "MacBook Pro M3", "price": 14999, "stock": 50,
     "category": "笔记本", "desc": "M3芯片, 14寸, 18GB内存"},
]

# 模拟订单库
ORDER_DB = {
    "ORD20240001": {"user": "u123", "product": "P001", "qty": 1,
                    "status": "shipped", "logistics": "顺丰SF1234, 已到杭州转运中心",
                    "amount": 6999, "address": "杭州市余杭区XX路1号"},
    "ORD20240002": {"user": "u123", "product": "P003", "qty": 2,
                    "status": "delivered", "logistics": "已签收, 签收人: 本人",
                    "amount": 3798, "address": "杭州市余杭区XX路1号"},
}

# 模拟用户库
USER_DB = {
    "u123": {"name": "张三", "vip_level": 5, "emotion_baseline": 0.7},
}

# ============================================================
# 第三部分: 工具实现
# ============================================================

@tool(
    name="search_product",
    description="根据关键词搜索商品,返回商品列表(含价格、库存、描述)",
    parameters={
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "搜索关键词,如'手机''耳机'"},
            "category": {"type": "string", "description": "商品类目,可选"},
            "top_k": {"type": "integer", "description": "返回数量,默认3", "default": 3}
        },
        "required": ["keyword"]
    }
)
def search_product(keyword: str, category: str = "", top_k: int = 3) -> list[dict]:
    """商品检索: 模拟向量召回 + 关键词匹配"""
    results = []
    for p in PRODUCT_DB:
        # 关键词匹配(实际用向量检索)
        if keyword.lower() in p["name"].lower() or keyword in p["desc"]:
            if category and p["category"] != category:
                continue
            results.append(p)
    return results[:top_k]

@tool(
    name="query_order",
    description="根据订单号查询订单状态、物流、金额等信息",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "订单编号,如ORD20240001"}
        },
        "required": ["order_id"]
    }
)
def query_order(order_id: str) -> dict:
    """订单查询"""
    order = ORDER_DB.get(order_id)
    if not order:
        return {"error": f"订单 {order_id} 不存在"}
    product = next((p for p in PRODUCT_DB if p["id"] == order["product"]), None)
    return {
        "order_id": order_id,
        "product_name": product["name"] if product else "未知商品",
        "quantity": order["qty"],
        "amount": order["amount"],
        "status": order["status"],
        "logistics": order["logistics"],
        "address": order["address"]
    }

@tool(
    name="initiate_return",
    description="发起退换货申请,需指定订单号和退换货类型",
    parameters={
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "订单编号"},
            "return_type": {"type": "string", "enum": ["退款", "退货", "换货"], "description": "退换货类型"},
            "reason": {"type": "string", "description": "退换货原因"}
        },
        "required": ["order_id", "return_type", "reason"]
    }
)
def initiate_return(order_id: str, return_type: str, reason: str) -> dict:
    """发起退换货"""
    order = ORDER_DB.get(order_id)
    if not order:
        return {"error": "订单不存在"}
    if order["status"] == "shipped":
        return {"status": "pending", "message": f"已发起{return_type}申请,请等商品签收后寄回",
                "return_id": f"RET{int(time.time())}"}
    elif order["status"] == "delivered":
        return {"status": "approved", "message": f"{return_type}申请已通过,请在7天内寄回",
                "return_id": f"RET{int(time.time())}"}
    else:
        return {"error": f"当前订单状态{order['status']}不支持退换货"}

@tool(
    name="transfer_to_human",
    description="转接人工客服,当用户情绪激动或问题复杂时使用",
    parameters={
        "type": "object",
        "properties": {
            "reason": {"type": "string", "description": "转接原因"},
            "priority": {"type": "string", "enum": ["低", "中", "高"], "description": "优先级"}
        },
        "required": ["reason"]
    }
)
def transfer_to_human(reason: str, priority: str = "中") -> dict:
    return {"transferred": True, "reason": reason, "priority": priority,
            "ticket_id": f"TKT{int(time.time())}", "queue_position": 3}

# ============================================================
# 第四部分: 情绪检测 (轻量规则版,实际用小模型)
# ============================================================

NEGATIVE_WORDS = ["投诉", "差评", "骗子", "12315", "垃圾", "退钱", "过分", "无语", "气死"]
URGENT_WORDS = ["急", "马上", "立刻", "赶紧", "今天必须"]

def detect_emotion(text: str) -> dict:
    """情绪检测,返回情绪分数和是否需要转人工"""
    score = 0.5  # 基线
    for w in NEGATIVE_WORDS:
        if w in text:
            score -= 0.2
    for w in URGENT_WORDS:
        if w in text:
            score -= 0.1
    # 感叹号和问号
    score -= 0.05 * text.count("!")
    score -= 0.03 * text.count("?")
    score = max(0.0, min(1.0, score))
    need_human = score < 0.3 or any(w in text for w in ["投诉", "12315"])
    return {"score": round(score, 2), "need_human": need_human}

# ============================================================
# 第五部分: 上下文管理 (多轮对话)
# ============================================================

@dataclass
class Message:
    role: str
    content: str | None = None
    tool_calls: list | None = None
    tool_call_id: str | None = None

@dataclass
class Session:
    user_id: str
    messages: list[Message] = field(default_factory=list)
    slots: dict = field(default_factory=dict)  # 结构化槽位: order_id, product_id 等
    max_context_tokens: int = 4000

    def add(self, msg: Message):
        self.messages.append(msg)
        self._compress_if_needed()

    def _compress_if_needed(self):
        """上下文超长时,摘要压缩早期对话"""
        total = sum(len(m.content or "") for m in self.messages)
        if total > self.max_context_tokens and len(self.messages) > 6:
            # 保留 system + 最近 4 轮,中间做摘要
            early = self.messages[1:-4]
            summary = f"[历史摘要] 用户询问了{len(early)}轮,主要涉及: " + \
                      ", ".join(m.content[:20] for m in early if m.content)
            self.messages = [self.messages[0], Message("system", summary)] + self.messages[-4:]

    def get_prompt_messages(self) -> list[dict]:
        return [m.__dict__ for m in self.messages]

# ============================================================
# 第六部分: LLM 模拟 (实际替换为 Qwen API)
# ============================================================

def llm_call(messages: list[dict], tools: list[dict]) -> dict:
    """模拟支持 FC 的 LLM。真实场景调用 Qwen API:
       import dashscope
       resp = dashscope.Generation.call(model="qwen-plus", messages=messages, tools=tools, ...)
    """
    user_msg = ""
    for m in reversed(messages):
        if m["role"] == "user" and m.get("content"):
            user_msg = m["content"]
            break

    # 规则模拟工具调用(真实场景模型自动决定)
    order_match = re.search(r"ORD\d{8}", user_msg)
    if order_match:
        return {"content": None, "tool_calls": [
            {"id": "c1", "function": {"name": "query_order",
             "arguments": json.dumps({"order_id": order_match.group()})}}]}

    if any(w in user_msg for w in ["退货", "退款", "换货"]):
        if "ORD" in user_msg:
            oid = re.search(r"ORD\d{8}", user_msg).group()
        else:
            return {"content": "请问您要退换货的订单号是多少?", "tool_calls": None}
        rtype = "退款" if "退款" in user_msg else ("换货" if "换货" in user_msg else "退货")
        return {"content": None, "tool_calls": [
            {"id": "c1", "function": {"name": "initiate_return",
             "arguments": json.dumps({"order_id": oid, "return_type": rtype, "reason": "用户申请"})}}]}

    if any(w in user_msg for w in ["搜", "找", "买", "推荐", "有没有"]):
        keyword = "手机"  # 实际用 LLM 抽取
        return {"content": None, "tool_calls": [
            {"id": "c1", "function": {"name": "search_product",
             "arguments": json.dumps({"keyword": keyword, "top_k": 3})}}]}

    # 默认回复
    return {"content": f"您好,我是淘宝智能客服,可以帮您查订单、搜商品、处理退换货。请问有什么可以帮您?", "tool_calls": None}

def llm_summarize_tool_result(tool_name: str, tool_result: Any, user_query: str) -> str:
    """基于工具结果生成自然语言回复(真实场景调 LLM)"""
    if tool_name == "query_order":
        if "error" in tool_result:
            return f"抱歉,{tool_result['error']},请您确认订单号是否正确。"
        return (f"您的订单 {tool_result['order_id']} 当前状态: {tool_result['status']}。\n"
                f"商品: {tool_result['product_name']} x{tool_result['quantity']}, 金额: ¥{tool_result['amount']}\n"
                f"物流: {tool_result['logistics']}\n收货地址: {tool_result['address']}")

    if tool_name == "search_product":
        if not tool_result:
            return "没有找到相关商品,换个关键词试试?"
        lines = ["为您找到以下商品:"]
        for p in tool_result:
            lines.append(f"- {p['name']} | ¥{p['price']} | 库存{p['stock']}件 | {p['desc']}")
        return "\n".join(lines)

    if tool_name == "initiate_return":
        if "error" in tool_result:
            return tool_result["error"]
        return f"{tool_result['message']}。退换货单号: {tool_result['return_id']}"

    if tool_name == "transfer_to_human":
        return f"已为您转接人工客服,排队位置: 第{tool_result['queue_position']}位,单号: {tool_result['ticket_id']}"

    return str(tool_result)

# ============================================================
# 第七部分: Agent 主循环
# ============================================================

class EcommerceAgent:
    def __init__(self, user_id: str = "u123"):
        self.session = Session(user_id=user_id)
        self.session.add(Message("system",
            "你是淘宝智能客服小蜜,可以帮用户搜索商品、查询订单、处理退换货。"
            "用户情绪激动或问题复杂时主动转人工。"))

    def chat(self, user_input: str) -> str:
        # 1. 情绪检测
        emotion = detect_emotion(user_input)
        if emotion["need_human"]:
            result = transfer_to_human("用户情绪激动", "高")
            reply = llm_summarize_tool_result("transfer_to_human", result, user_input)
            self.session.add(Message("user", user_input))
            self.session.add(Message("assistant", reply))
            return reply

        # 2. 加入用户消息
        self.session.add(Message("user", user_input))

        # 3. Agent 循环(调 LLM → 执行工具 → 回填 → 再调 LLM)
        for turn in range(5):
            resp = llm_call(self.session.get_prompt_messages(), TOOL_SCHEMAS)

            if not resp.get("tool_calls"):
                self.session.add(Message("assistant", resp["content"]))
                return resp["content"]

            # 执行工具
            self.session.add(Message("assistant", None, resp["tool_calls"]))
            for tc in resp["tool_calls"]:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])
                print(f"  [工具调用] {fn_name}({fn_args})")
                try:
                    result = TOOL_REGISTRY[fn_name](**fn_args)
                except Exception as e:
                    result = {"error": str(e)}
                # 回填工具结果
                self.session.add(Message("tool", json.dumps(result, ensure_ascii=False), None, tc["id"]))
                # 生成自然语言回复
                reply = llm_summarize_tool_result(fn_name, result, user_input)

            # 下一轮 LLM 基于工具结果继续
            # (这里简化为直接返回,实际 LLM 会基于 result 决定是否再调工具或直接回答)
            self.session.add(Message("assistant", reply))
            return reply

        return "抱歉,问题较复杂,为您转接人工。"

# ============================================================
# 第八部分: 测试用例
# ============================================================

def test():
    print("=" * 60)
    print("测试1: 商品搜索")
    print("=" * 60)
    agent = EcommerceAgent()
    print(agent.chat("帮我搜一下手机"))

    print("\n" + "=" * 60)
    print("测试2: 订单查询")
    print("=" * 60)
    agent2 = EcommerceAgent()
    print(agent2.chat("查一下我的订单 ORD20240001"))

    print("\n" + "=" * 60)
    print("测试3: 退换货")
    print("=" * 60)
    agent3 = EcommerceAgent()
    print(agent3.chat("我要退货,订单号 ORD20240001,东西坏了"))

    print("\n" + "=" * 60)
    print("测试4: 情绪检测转人工")
    print("=" * 60)
    agent4 = EcommerceAgent()
    print(agent4.chat("你们这是什么垃圾服务!我要投诉!12315!"))

    print("\n" + "=" * 60)
    print("测试5: 多轮对话(先查订单再退换货)")
    print("=" * 60)
    agent5 = EcommerceAgent()
    print(agent5.chat("查一下订单 ORD20240001"))
    print(agent5.chat("那我要退货"))

if __name__ == "__main__":
    test()
```

**运行输出示例**:

```
============================================================
测试1: 商品搜索
============================================================
  [工具调用] search_product({'keyword': '手机', 'top_k': 3})
为您找到以下商品:
- 华为 Mate60 Pro | ¥6999 | 库存120件 | 麒麟9000S, 卫星通话, 5000mAh
- 小米14 Ultra | ¥6499 | 库存80件 | 骁龙8Gen3, 徕卡光学, 2K屏

============================================================
测试4: 情绪检测转人工
============================================================
已为您转接人工客服,排队位置: 第3位,单号: TKT1695xxxxxxx
```

**代码要点解析**:

1. **工具注册装饰器**: 用 `@tool` 自动注册 schema,解耦工具实现与 Agent 主循环,新增工具只需加装饰器。
2. **情绪检测前置**: 在进入 LLM 循环前先做情绪检测,避免情绪化用户被 Agent 反复折腾,直接转人工。
3. **Session 上下文管理**: 用 dataclass 管理多轮对话,超长时自动摘要压缩,槽位(`slots`)存结构化信息防 LLM 遗忘。
4. **工具错误回填**: 工具执行异常不抛中断,而是把 error 回填给 LLM,让 LLM 决定重试或换策略。
5. **真实场景替换点**: `llm_call` 和 `llm_summarize_tool_result` 是模拟版,真实场景替换为 Qwen API 调用即可,其余代码不动。

</details>

---

### Q10: 系统设计 — 设计阿里云智能运维 Agent 系统

<details>
<summary>点击展开答案</summary>

**一、需求理解(面试先澄清需求)**

| 维度 | 明确 |
|------|------|
| 业务场景 | 阿里云 ECS/RDS/SLB 等云产品故障的智能运维 |
| 核心能力 | 故障检测 → 根因分析 → 自动修复 → 报告生成 |
| 规模 | 监控指标百万级、日志 TB/天、服务万级 |
| 时延 | 检测 < 1min,诊断 < 5min,修复 < 10min |
| 安全 | 误操作率 = 0(红线),高危动作必须人工确认 |

**二、整体架构**

```
┌─────────────────────────────────────────────────────────────┐
│  数据接入层                                                  │
│   ├── CloudMonitor (指标, 秒级)                              │
│   ├── SLS (日志, 准实时)                                     │
│   ├── ARMS (调用链, 准实时)                                  │
│   └── 变更平台 (发布/配置/扩缩容事件)                        │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  数据处理层                                                  │
│   ├── 流计算 (Flink) — 实时指标异常检测                       │
│   ├── 日志聚类 (LLM + 向量化) — 异常日志归并                  │
│   └── 拓扑构建 — 服务依赖图 + 变更图                         │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Agent 编排层 (多 Agent 协作)                                │
│   ┌──────────────┐  故障事件  ┌──────────────┐              │
│   │ 感知 Agent    │───────────▶│ 诊断 Agent    │              │
│   │ (检测+去噪)   │            │ (根因+影响)   │              │
│   └──────────────┘            └──────┬───────┘              │
│                                        │ 根因                 │
│                                        ▼                      │
│   ┌──────────────┐  修复结果  ┌──────────────┐              │
│   │ 复盘 Agent    │◀───────────│ 执行 Agent    │              │
│   │ (报告+改进)   │            │ (修复+验证)   │              │
│   └──────────────┘            └──────────────┘              │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  知识与能力层                                                │
│   ├── 故障知识图谱 (服务/变更/容量/历史故障)                  │
│   ├── 预案库 (根因 → 修复动作, 含回滚方案)                    │
│   ├── 运维工具集 (扩缩容/重启/切流/清缓存 API)                │
│   └── 沙箱环境 (灰度节点/影子集群)                           │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  模型层                                                      │
│   ├── Qwen-Max (复杂根因推理)                                │
│   ├── Qwen-Plus (常规诊断)                                   │
│   ├── Qwen-Turbo (日志分类/摘要)                             │
│   └── 专项小模型 (时序异常/日志聚类)                         │
└──────────────────┬──────────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  安全与管控层                                                │
│   ├── 动作风险评级 (低/中/高/极高)                           │
│   ├── 人工审批网关 (高危动作)                                │
│   ├── 回滚机制 (修复失败自动回滚)                            │
│   └── 审计日志 (全链路留痕)                                  │
└─────────────────────────────────────────────────────────────┘
```

**三、各 Agent 详细设计**

**1. 感知 Agent(故障检测)**

- **输入**: 实时指标流、日志流、调用链。
- **能力**:
  - 时序异常检测: 用 EWMA + Prophet + 孤立森林三模型集成,降低单模型误报。
  - 日志异常: 日志聚类后,新出现的 cluster 或频率突增的 cluster 标记异常,LLM 做语义分类(是 ERROR 还是 WARN)。
  - 调用链分析: 检测延迟突增的 span,沿调用链溯源。
  - 去噪聚合: 同一故障可能在多个指标/日志上告警,用时间窗口 + 拓扑关系聚合成一个"故障事件"。
- **输出**: 结构化故障事件 `{event_id, time, scope, severity, symptoms}`。

**2. 诊断 Agent(根因分析)**

- **双重路径**:
  - **知识图谱路径**: 从故障节点出发,查故障知识图谱(服务依赖图、变更图、容量图)。优先排查最近 30min 变更(发布、配置、扩缩容),这是阿里云 80% 故障的根因。
  - **LLM 推理路径**: 把"故障症状 + 最近变更 + 历史相似故障"喂给 Qwen-Max,让它生成 Top-3 根因假设,每个假设带置信度和证据链。
- **融合**: 两路结果做加权打分,输出 Top-K 候选根因。
- **输出**: `{root_causes: [{rank, hypothesis, confidence, evidence, suggested_fix}]}`。

**3. 执行 Agent(自动修复)**

- **风险评级矩阵**:

  | 动作 | 风险等级 | 执行方式 |
  |------|----------|----------|
  | 清缓存 | 低 | 自动执行 |
  | 重启单实例 | 中 | 自动 + 事后验证 |
  | 扩容 | 中 | 自动(预设上限内) |
  | 切流量 | 高 | 人工确认 |
  | 回滚发布 | 高 | 人工确认 |
  | 关闭服务 | 极高 | 人工 + 双人审批 |

- **流程**: 预案库匹配 → 沙箱预演(高危) → 人工审批(高危) → 执行 → 5min 内指标未恢复自动回滚。
- **输出**: 修复结果 + 验证指标。

**4. 复盘 Agent(报告生成)**

- **结构化模板**: 不让 LLM 自由生成,而是按模板填空:
  - 故障概要(时间、影响、等级)
  - 时间线(检测、诊断、修复各节点时间)
  - 根因分析(直接原因 + 深层原因)
  - 影响面(受影响服务、用户数、订单量、资损)
  - 处理过程(执行的修复动作、是否回滚)
  - 改进项(短期修复 + 长期优化,带 owner 和 deadline)
- **LLM 角色**: 只负责"自然语言润色 + 改进建议生成",结构化数据由程序填充,保证报告完整可控。

**四、关键设计点**

1. **变更关联优先**: 阿里云 80% 故障由变更引起。诊断 Agent 第一步永远是查最近 30min 变更,而非从零推理。这是 SRE 经验的工程化。

2. **预案库沉淀**: 每次人工处理的故障,事后由复盘 Agent 自动抽取"根因 → 修复动作"对,沉淀进预案库。预案库越用越准,这是飞轮效应。

3. **安全边界三道防线**:
   - 第一道: 风险评级,低危自动执行。
   - 第二道: 沙箱预演,高危动作先在灰度节点试。
   - 第三道: 人工审批 + 自动回滚兜底。
   - 误操作率 = 0 是红线,宁可多人工确认也不误操作。

4. **知识图谱构建**:
   - 服务依赖图: 从 ARMS 调用链自动构建。
   - 变更图: 关联发布平台、配置中心、扩缩容记录。
   - 历史故障图: 复盘 Agent 每次故障后自动更新。
   - 图谱是诊断 Agent 的"记忆",没有图谱 LLM 推理就是空中楼阁。

5. **模型分级**:
   - 感知层: 专项小模型(时序、日志),低延迟高吞吐。
   - 诊断层: Qwen-Max 做复杂推理,Qwen-Plus 做常规分类。
   - 复盘层: Qwen-Plus 做报告润色。
   - 分级降低成本,单次故障诊断成本控制在 1 元内。

**五、评测指标**

| 维度 | 指标 | 目标 |
|------|------|------|
| 检测 | MTTD(平均检测时间) | ≤ 1min |
| 检测 | 异常检出率 | ≥ 95% |
| 检测 | 误报率 | ≤ 5% |
| 诊断 | 根因 Top-3 命中率 | ≥ 80% |
| 诊断 | 平均诊断时间 | ≤ 5min |
| 修复 | 自动修复成功率 | ≥ 70% |
| 修复 | MTTR | 降低 50% |
| 修复 | 误操作率 | 0(红线) |
| 报告 | 报告完整度 | ≥ 90% |
| 成本 | 单次故障诊断成本 | ≤ 1 元 |

**六、面试加分点**

- **强调"人在回路"和"误操作率为 0"**: 阿里云对线上操作零容忍,这是红线,答不出这个直接挂。
- **"变更关联优先"**: 体现 SRE 实战经验,阿里面试官有 SRE 背景。
- **"预案库飞轮"**: 体现"算法 + 经验"双轮驱动,纯算法派会被质疑不懂运维。
- **"知识图谱是诊断的记忆"**: 体现对 LLM 能力边界的清醒认知,LLM 没有图谱就是空中楼阁。
- **"报告结构化生成"**: 不让 LLM 自由生成,而是模板填空 + LLM 润色,体现工程克制。

</details>

---

## 核心知识回顾表

| 考点 | 核心要点 | 阿里特色 | 易错提醒 |
|------|----------|----------|----------|
| 阿里 Agent 岗位 | 通义/达摩院/阿里云三线 | 业务反推 + 模型原理 + 工程落地 | 别只讲算法,工程落地是重点 |
| 电商客服 Agent | 意图路由 + 多Agent + 情绪转人工 | 商品RAG增量更新是核心 | 价格/库存走API不走RAG |
| 通义千问选型 | Turbo/Plus/Max分级路由 | 中文+FC原生+开源+阿里云集成 | 别只选最强的,要看成本延迟 |
| 电商RAG | 离线全量+在线增量双流 | 商品变更分级处理 | 强一致字段不进RAG |
| AIOps Agent | 感知→诊断→执行→复盘四Agent | 变更关联优先+人在回路 | 误操作率为0是红线 |
| Function Calling | SFT学的能力,非Prompt工程 | Qwen原生FC支持 | 工具多时要做工具检索 |
| 多Agent供应链 | 共享黑板+提案仲裁 | LLM+运筹互补不替代 | 别说LLM替代Gurobi |
| 推理优化 | 模型/Prompt/缓存/系统四层 | 分级路由ROI最高 | 区分延迟优化vs吞吐优化 |
| 手撕客服Agent | 工具注册+情绪检测+Session | 上下文摘要压缩 | 错误回填不抛异常 |
| AIOps系统设计 | 风险评级+沙箱+回滚三道防线 | 预案库飞轮+知识图谱 | 报告结构化生成,别让LLM自由发挥 |

---

## 面试速记卡 — 阿里面试技巧

```
┌─────────────────────────────────────────────────────────────┐
│ 阿里 Agent 面试 · 速记卡                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ 【答题框架】                                                 │
│ 1. 系统设计: 业务拆解→架构分层→模型选型→工程保障→指标评测    │
│ 2. 项目深挖: STAR + 业务指标(Situation/Task/Action/Result)  │
│ 3. 不会的题: 承认 + 给"我会怎么查/怎么验证"的思路            │
│                                                             │
│ 【阿里高频追问点】                                           │
│ - "上线后指标怎么定? 评测集怎么建? AB实验怎么做?"            │
│ - "成本怎么控? 峰值怎么扛? 故障怎么recover?"                │
│ - "为什么这么设计? 有没有更好的方案?"                        │
│ - "双11/618这种峰值场景你的方案扛得住吗?"                    │
│                                                             │
│ 【加分话术】                                                 │
│ - "我会先建评测集,用业务真实数据benchmark"                  │
│ - "分级路由: 80%走小模型,20%走大模型"                       │
│ - "强一致字段走API,弱时效字段走RAG"                          │
│ - "误操作率为0是红线,人在回路+三道防线"                      │
│ - "LLM不替代运筹,是增强; LLM不替代SRE,是辅助"               │
│                                                             │
│ 【避坑提醒】                                                 │
│ - 别只讲算法不讲工程: 上线/灰度/成本/监控必须答               │
│ - 别忽略阿里技术栈: 通义/百炼/PAI/SLS/Sentinel是加分项        │
│ - 别说"LLM替代XX": 阿里强调人机协同,纯替代论会被怼            │
│ - 别忽视HR面: 阿里HR一票否决,价值观要准备                    │
│                                                             │
│ 【阿里价值观关键词】                                         │
│ 客户第一 / 拥抱变化 / 团队合作 / 诚信 / 激情 / 敬业          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

1. **价格/库存进 RAG**: 电商场景价格秒级变动,RAG 是异步的,会把过期价格喂给用户,直接资损。**强一致字段必须走 API 实时查**。

2. **Function Calling 当成 Prompt 工程**: FC 是 SFT 训练出来的能力,不是靠 Prompt 就能让任意模型学会的。开源小模型没经过 FC SFT,直接用 FC 模板会翻车,要用 ReAct。

3. **模型选型只看效果不看成本**: Qwen-Max 效果最好但贵且慢,全量上 Max 成本扛不住。必须分级路由,80% 流量走 Turbo。

4. **AIOps 自动修复不加安全边界**: 线上误操作一次就是 P0 故障。必须有风险评级 + 沙箱预演 + 人工审批 + 自动回滚四重保障,误操作率为 0 是红线。

5. **RAG 增量更新用 delete + insert**: 会有"删了旧的、新的没写入"的空窗期。要用带版本号的 upsert,检索时过滤过期版本。

6. **多轮对话不做上下文压缩**: 长对话 token 爆炸,既慢又贵。要做摘要压缩 + 结构化槽位持久化(订单号、商品ID存slot,不靠LLM记)。

7. **工具全部塞进 prompt**: 工具超过 50 个,描述 token 爆炸。要做"工具检索"——先检索 Top-K 相关工具,只把这 K 个喂给模型。

8. **情绪检测放 LLM 循环里**: 情绪化用户被 Agent 反复折腾体验极差。情绪检测要前置,检测到强负面情绪直接转人工带上下文摘要。

9. **报告生成让 LLM 自由发挥**: 故障报告缺关键信息是常见问题。必须用结构化模板填空,LLM 只做润色和改进建议,结构化数据程序填。

10. **说"LLM 替代运筹/替代 SRE"**: 阿里强调人机协同。LLM 增强运筹(定性+定量结合)、辅助 SRE(建议+执行+人在回路),不是替代。纯替代论会被面试官怼。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 1. 能说清阿里 Agent 三大岗位线(通义/达摩院/阿里云)的区别和考察重点?
- [ ] 2. 能画出电商客服 Agent 的分层架构,讲清意图路由双通道?
- [ ] 3. 能说清通义千问 Turbo/Plus/Max 的选型矩阵和分级路由逻辑?
- [ ] 4. 能讲清电商 RAG 增量更新的"离线全量+在线增量"双流架构?
- [ ] 5. 能区分"强一致字段走 API" vs "弱时效字段走 RAG"?
- [ ] 6. 能讲清 Function Calling 的 SFT 训练原理和 ReAct 的区别?
- [ ] 7. 能画出 AIOps Agent 的"感知→诊断→执行→复盘"四 Agent 架构?
- [ ] 8. 能说清自动修复的"风险评级+沙箱+人工审批+回滚"四重防线?
- [ ] 9. 能讲清推理优化的"模型/Prompt/缓存/系统"四层,各举2个技术?
- [ ] 10. 能说清多 Agent 协作的"共享黑板+提案仲裁"模式?

### 代码题(3 个)

- [ ] 11. 能手撕 Function Calling 的工具注册 + Agent 主循环(装饰器 + 循环)?
- [ ] 12. 能实现情绪检测 + 人工转接的前置逻辑(规则版或小模型版)?
- [ ] 13. 能实现多轮对话的 Session 管理 + 上下文摘要压缩?

### 系统设计题(2 个)

- [ ] 14. 能完整设计"淘宝智能客服 Agent",覆盖架构/模型/工程/指标四方面?
- [ ] 15. 能完整设计"阿里云智能运维 Agent 系统",覆盖四 Agent + 安全 + 知识图谱 + 评测?

> **自测标准**: 概念题能口述 3 分钟以上; 代码题能在 30 分钟内写出核心框架; 系统设计题能在 15 分钟内画出架构图并讲清 3 个关键设计点。

---

## 延伸阅读

### 阿里技术博客 & 论文

| 资源 | 链接/出处 | 重点 |
|------|-----------|------|
| Qwen 技术报告 | arXiv: "Qwen Technical Report" 系列 | 通义千问模型架构、训练数据、能力评测 |
| 阿里云开发者社区 | developer.aliyun.com/article | AIOps、智能客服、百炼平台实战文章 |
| 阿里技术(微信公众号) | 搜索"阿里技术" | 双11技术架构、供应链算法、客服系统 |
| 阿里达摩院官网 | damo.alibaba.com | 达摩院 Agent 相关论文和开源项目 |
| AgentScope(达摩院开源) | github.com/agentscope-ai/agentscope | 达摩院多 Agent 框架,看源码学架构 |
| 百炼平台文档 | help.aliyun.com/zh/dashscope | 通义千问 API、Function Calling、Agent 构建 |
| Qwen 开源仓库 | github.com/QwenLM/Qwen2.5 | 开源模型微调、部署、FC 训练数据 |
| 阿里云 AIOps 实践 | 搜索"阿里云 AIOps 白皮书" | 故障检测、根因分析、自动修复工程实践 |

### 推荐阅读顺序

1. **先读**: Qwen 技术报告(了解模型能力边界) + 百炼平台文档(了解 API 和 FC)。
2. **再读**: 阿里云 AIOps 白皮书(理解运维场景) + AgentScope 源码(学多 Agent 架构)。
3. **深读**: 选一个电商客服或 AIOps 的实战博客精读,提炼"架构图 + 关键设计 + 指标"。

### 相关面试真题(扩展)

- 阿里: "设计双11实时大屏,如何保证数据准确性和实时性?"
- 阿里: "通义灵码如何做代码补全的上下文管理?"
- 阿里: "如何评估一个 Agent 比上一个版本好? 评测集怎么建?"
- 阿里云: "设计一个支持多租户的 Agent 平台(百炼),如何做隔离和计费?"

---

## 明日预告

> **Day 24 — 腾讯百度 Agent 面试专项**
>
> Day23 攻克了阿里巴巴(电商 + 云运维 + 通义千问)。Day24 转向腾讯和百度:
> - **腾讯**: 微信生态 Agent(小程序/企业微信/视频号)、混元大模型、游戏 NPC Agent、社交场景 RAG。
> - **百度**: 文心一言/ERNIE、搜索增强 Agent、自动驾驶 Agent(百度 Apollo)、知识图谱增强。
>
> 两家共同关注: **Agent 在超级 App 中的落地、知识图谱与 LLM 结合、多模态 Agent**。
>
> **预习建议**: 提前了解腾讯混元、百度文心一言的模型特点,以及微信生态和百度搜索的 Agent 应用场景。

---

> **学习提示**: 本文档约 45KB,建议分两次学习 —— 上午攻 Q1-Q5(电商 + 模型 + RAG + AIOps),下午攻 Q6-Q10(FC 原理 + 供应链 + 性能 + 手撕 + 系统设计)。每个题先自己答一遍,再对照答案查漏补缺。手撕代码题务必在本地跑通,不要只看不动手。
