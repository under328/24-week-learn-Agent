# Day 25 — 美团蚂蚁 Agent 面试专项

> **学习目标**: 深入掌握美团(本地生活/配送/到店/客服)和蚂蚁集团(风控/客服/金融/财富)两大互联网巨头的 Agent 面试套路与高频考点;能够独立设计美团智能客服、配送调度、商家知识库 RAG 等系统,能够设计蚂蚁金融风控 Agent、智能理财助手、合规审计体系;手撕金融场景 Agent 代码,理解金融级安全合规要求。
>
> **面试定位**: 美团偏向"业务落地+工程化+多业务线协同",看重候选人对本地生活场景的理解和 Agent 在真实复杂业务中的可用性;蚂蚁偏向"金融安全+合规审计+高可用",看重候选人对金融场景特殊性(强合规、强审计、强风控)的把握,以及对 LLM 在金融领域落地风险的认知。两家都属于 Agent 应用层最成熟的厂商之一,面试难度 ★★★★☆。
>
> **预计学习时长**: 6-8 小时(含手撕代码 + 系统设计画图)
>
> **配套前置**: Day22 字节、Day23 阿里、Day24 腾讯百度面试专项(已学完)

---

## 今日知识图谱

```
美团蚂蚁 Agent 面试专项
│
├── 美团系(本地生活 / 工程化导向)
│   ├── 面试风格
│   │   ├── 团队划分: 到家(外卖/配送)、到店(餐饮/酒旅)、AI 平台(NLP/搜索/客服)
│   │   ├── 考察重点: 业务理解 + 落地能力 + 多业务线协同 + ROI 思维
│   │   └── 流程: 3 轮技术 + 1 轮 HR,系统设计题占比高
│   │
│   ├── 高频考点
│   │   ├── 智能客服 Agent(外卖/退款/投诉/骑手)
│   │   ├── 配送调度 Agent(智能调度/异常处理/动态定价)
│   │   ├── 商家知识库 RAG(百万商家 + 多模态菜单)
│   │   ├── 多业务线知识共享与隔离
│   │   └── Agent 与骑手/商家/用户三方协同
│   │
│   └── 技术栈特点
│       ├── 多模态(菜单图、商家视频、用户评价)
│       ├── 实时性(配送 ETA、订单状态)
│       └── 大规模(百万商家、千万订单/日)
│
├── 蚂蚁系(金融 / 合规导向)
│   ├── 面试风格
│   │   ├── 团队划分: CTO 线、风控(大安全)、财富、客服、网商银行
│   │   ├── 考察重点: 金融合规 + 安全审计 + 高可用 + 风险识别
│   │   └── 流程: 3-4 轮技术 + HR,金融背景问题多
│   │
│   ├── 高频考点
│   │   ├── 金融风控 Agent(智能审批/欺诈检测/风险评估)
│   │   ├── 智能理财助手(投顾/资产配置/风险偏好)
│   │   ├── 金融客服(账务/纠纷/反洗钱)
│   │   ├── 合规审查与审计日志(可追溯/可回放)
│   │   └── LLM 幻觉在金融场景的防控
│   │
│   └── 技术栈特点
│       ├── 强合规(监管要求、白名单、灰度)
│       ├── 强审计(全链路日志、不可篡改)
│       ├── 强风控(实时拦截、人工复核)
│       └── 高可用(金融级 SLA、双活容灾)
│
├── 共性考点(两家都考)
│   ├── Agent 架构(ReAct / Plan-Execute / Multi-Agent)
│   ├── RAG 工程(召回率、时效性、多源融合)
│   ├── 工具调用(Function Calling / MCP)
│   ├── 记忆与上下文管理
│   ├── 评测体系(人工 + 自动化 + 在线 A/B)
│   └── 人工协作(Human-in-the-loop / 兜底策略)
│
└── 手撕与系统设计
    ├── 手撕: 金融场景 Agent(意图识别 + 风险检查 + 工具调用 + 合规审查 + 审计日志)
    └── 系统设计: 智能客服中台(多业务线 + 统一知识库 + 人工协作 + 质量监控)
```

---

## 面试题

### Q1 美团面试风格 — 美团 AI/到家/到店团队,面试流程和考察重点是什么?

<details>
<summary>展开答案</summary>

**1. 团队划分与 Agent 相关方向**

美团与 Agent/LLM 强相关的团队主要有:

- **AI 平台部 / NLP 中心**: 负责大模型基础设施建设、美团自研 LongCat 模型、Agent 框架、对话平台,是 Agent 技术的"中央厨房"。
- **到家事业群(外卖/配送)**: 智能客服、骑手语音助手、商家助手、配送调度 Agent,场景复杂度高、实时性要求强。
- **到店事业群(餐饮/酒旅/医美)**: 商家知识库、点评智能摘要、到店推荐 Agent、商家经营助手。
- **美团平台 / 搜索推荐**: 多模态搜索、对话式推荐、Query 意图理解 Agent。

**2. 面试流程(社招典型)**

| 轮次 | 时长 | 考察内容 | 备注 |
|------|------|---------|------|
| 一面(技术) | 60-90 min | 八股 + 算法(1 道 medium) + 项目深挖 | 重视基础 |
| 二面(技术) | 60-90 min | 系统设计题(高频:智能客服/调度/RAG) + 项目 | 美团最爱系统设计 |
| 三面(技术/GM) | 60 min | 业务理解 + 架构权衡 + 团队匹配 | 看业务 sense |
| 四面(HR) | 30-45 min | 离职原因 + 稳定性 + 薪资 | 标准流程 |

校招通常 3 轮技术 + HR,实习生 2-3 轮。

**3. 考察重点(美团特色)**

- **业务理解优先**: 美团面试官特别在意候选人是否"懂本地生活",会问"你点外卖遇到过哪些问题?如果让你用 Agent 改进,你会怎么设计?"——这种开放题几乎必考。
- **工程化落地能力**: 美团是出了名的"重工程",会追问"线上 QPS 多少?""灰度方案是什么?""出问题怎么回滚?""ROI 怎么算?",纯讲论文会被怼。
- **多业务线协同**: 美团业务多且相互关联(外卖+到店+酒旅),会问"Agent 如何复用又如何隔离?""知识库怎么统一管理?"。
- **数据驱动**: A/B 实验、北极星指标、漏斗分析是家常便饭,候选人要能讲清楚 Agent 上线后怎么量化收益。
- **务实风格**: 美团反感"过度包装",讲方案要落地、有数据、有取舍,不要讲"我用 GPT-5 + 1000 个 Agent 做了个万能助手"这种空话。

**4. 美团 Agent 方向的真实工作**

- 智能客服(外卖投诉自动处理、退款决策、骑手问题分流),日均千万级会话。
- 骑手语音助手(接单、导航、异常上报),低延迟、强噪声场景。
- 商家助手(自动回复、菜单优化、经营分析),百万级商家。
- 配送调度(动态 ETA、异常订单重派、恶劣天气策略),毫秒级决策。
- 内部 Copilot(研发、运营、客服坐席辅助)。

**5. 备考建议**

- 熟悉美团技术博客(tech.meituan.com),尤其是 NLP、搜索推荐、客服相关文章。
- 至少能讲清楚 1 个美团业务场景的 Agent 设计(推荐:智能客服 or 配送调度)。
- 准备 2-3 个量化指标(准确率、解决率、人工转接率、成本节省),面试时主动抛。
- 了解 LongCat 美团自研模型的基本情况,显示对公司的关注。

</details>

---

### Q2 设计美团智能客服 Agent(外卖/退款/投诉/骑手问题)

<details>
<summary>展开答案</summary>

**题目背景**: 这是美团到家最常见的系统设计题。外卖客服场景复杂度高:涉及用户、商家、骑手三方;问题类型多(配送延迟、餐品问题、退款纠纷、骑手态度);情绪化严重(用户饿了等不及);且需要与订单系统、支付系统、调度系统联动。

**1. 需求澄清(面试官互动)**

- **业务范围**: 仅外卖,还是含到店/酒旅?——先做外卖,后续扩展。
- **接入渠道**: App 在线客服、电话客服、商家端?——先做 App 在线,预留多渠道。
- **解决率目标**: 当前人工解决率 70%,Agent 目标自助解决率 60%+。
- **延迟要求**: 首响 < 3s,完整解决 < 30s。
- **成本目标**: 单会话成本下降 50%。

**2. 整体架构(分层)**

```
┌─────────────────────────────────────────────────┐
│  接入层: App / 电话(ASR+TTS) / 商家端           │
├─────────────────────────────────────────────────┤
│  对话编排层(Orchestrator)                        │
│  ├─ 意图识别(精细到 50+ 子意图)                  │
│  ├─ 情绪识别 + 紧急度判断                        │
│  ├─ 多 Agent 路由(退款/投诉/骑手/咨询)          │
│  └─ 上下文管理(订单 ID 自动带入)                │
├─────────────────────────────────────────────────┤
│  Agent 执行层                                    │
│  ├─ 退款 Agent: 查订单 → 规则判定 → 自动退款     │
│  ├─ 投诉 Agent: 收集证据 → 分级 → 工单流转       │
│  ├─ 骑手 Agent: 查骑手状态 → 联系/催单/换人      │
│  ├─ 咨询 Agent: RAG(商家信息/活动/规则)         │
│  └─ 兜底 Agent: 转人工                          │
├─────────────────────────────────────────────────┤
│  能力层(Tools / RAG)                            │
│  ├─ 订单 API / 支付 API / 调度 API              │
│  ├─ 商家知识库(向量 + 关键词混合召回)            │
│  ├─ 规则引擎(退款规则/投诉分级)                 │
│  └─ 工单系统                                    │
├─────────────────────────────────────────────────┤
│  保障层                                          │
│  ├─ 风控(防薅羊毛、防恶意退款)                  │
│  ├─ 审计日志(全链路可回放)                      │
│  ├─ 质检(实时 + 离线抽检)                       │
│  └─ 监控告警(解决率/转人工率/客诉)              │
└─────────────────────────────────────────────────┘
```

**3. 关键设计点**

**(a) 意图识别 — 两阶段**

- 一阶段:粗分类(7 大类:配送/餐品/退款/骑手/活动/账户/其他),用小模型(BERT 级别)+ 规则,延迟 < 50ms。
- 二阶段:细分类(50+ 子意图,如"配送-延迟-未送达"、"餐品-少件-部分缺失"),用 LLM few-shot,延迟 < 500ms。
- 兜底:LLM 不确定时直接走人工,不强行答。

**(b) 上下文管理 — 订单驱动**

- 用户进入客服会话时,自动拉取最近 7 天订单列表。
- 意图识别后,自动锁定目标订单(可通过"是哪一单?"追问确认)。
- 上下文 token 控制:订单信息压缩(JSON → 关键字段),避免 LLM 上下文爆炸。

**(c) 退款 Agent — 规则 + LLM 协同**

```
输入: 用户诉求 + 订单信息
步骤:
  1. 规则引擎先判:订单状态、是否已退款、金额阈值、用户信用
     - 命中"自动退款白名单" → 直接退款(秒退)
     - 命中"高风险"标签 → 转人工
  2. 规则未覆盖 → LLM 综合判断(用户历史、商家评分、骑手轨迹)
  3. 退款金额 > 阈值 → 人工复核
  4. 退款执行后 → 发送通知 + 询问满意度
```

**(d) 投诉 Agent — 证据收集 + 工单分级**

- 引导用户上传图片(餐品问题、包装破损)。
- LLM 分析图片(多模态)+ 文字,自动分级(L1-L4)。
- L1-L2 自动处理(退款/补偿券),L3-L4 转人工 + 商家核实。
- 工单流转至商家端,SLA 监控。

**(e) 骑手 Agent — 状态查询 + 主动干预**

- 接入调度系统,实时查骑手位置、ETA、是否异常(超时/离线/事故)。
- 自动安抚用户("骑手还有 8 分钟到达,已为您催单")。
- 异常订单自动触发重派逻辑(联动调度系统)。
- 骑手态度问题 → 转人工 + 记录骑手档案。

**(f) RAG 知识库**

- 内容:商家信息、活动规则、平台政策、常见 FAQ。
- 召回:向量(BGE-M3)+ 关键词(BM25)混合,top-k=10 → rerank → top-3。
- 时效性:商家营业时间、活动有效期实时查询 API,不入向量库(避免脏数据)。
- 兜底:RAG 召回分数 < 阈值时,不答而转人工。

**(g) 人工协作(Human-in-the-loop)**

- 转人工策略:情绪激动(关键词 + 情绪模型)、连续 2 轮未解决、用户主动要求、高风险场景。
- 转人工时携带完整上下文摘要(LLM 生成 100 字以内),坐席秒级接手。
- 坐席可看到 Agent 的推理过程,便于决策。

**(h) 评测体系**

- 离线:准确率(意图识别)、解决率(自助闭环)、转人工合理性。
- 在线 A/B:解决率、CSAT(满意度)、NPS、单会话成本、二次进线率。
- 质检:每日抽检 5% 会话,人工标注 Agent 表现,反哺训练。

**4. 量化收益(给面试官的数字)**

- 自助解决率:30% → 60%
- 平均处理时长:180s → 60s
- 单会话成本:1.2 元 → 0.5 元
- CSAT:85% → 88%(快速响应对冲了 Agent 误判)

**5. 难点与权衡**

- **幻觉防控**: 退款金额、订单状态绝不能 LLM 直答,必须以系统数据为准。
- **情绪处理**: Agent 不能"硬刚"用户,要有共情话术,情绪阈值触发转人工。
- **多轮上下文**: 长会话 token 控制,采用摘要压缩 + 关键槽位保留。
- **灰度**: 按 user_id 哈希灰度,先 1% → 5% → 50% → 100%,每阶段观察指标。

</details>

---

### Q3 Agent 在美团配送调度中的应用(智能调度/异常处理)

<details>
<summary>展开答案</summary>

**题目背景**: 美团日均千万级订单,配送调度是核心壁垒。传统调度是运筹优化问题(车辆路径规划 VRP),Agent 的引入不是替代运筹,而是在异常处理、动态策略、骑手交互上做增强。

**1. 调度系统的两层架构**

```
┌──────────────────────────────────────┐
│  上层:Agent 决策层(策略 + 异常)      │
│  ├─ 异常订单 Agent(超时/取消/事故)   │
│  ├─ 动态定价 Agent(恶劣天气/高峰)    │
│  ├─ 骑手助手 Agent(语音交互)         │
│  └─ 区域调度 Agent(运力调配)         │
├──────────────────────────────────────┤
│  下层:运筹优化层(传统 VRP/RL)        │
│  ├─ 订单-骑手匹配(毫秒级)            │
│  ├─ 路径规划(地图 API + 自研引擎)    │
│  └─ ETA 预测(ML 模型)               │
└──────────────────────────────────────┘
```

**关键认知**: Agent 不直接做毫秒级匹配(运筹更擅长),而是做"策略层决策"和"异常兜底"。

**2. 异常订单 Agent 设计**

异常类型:
- 骑手超时未取餐
- 骑手配送中离线
- 骑手事故/车辆故障
- 商家出餐极慢
- 用户取消
- 恶劣天气批量延迟

Agent 处理流程(ReAct 模式):

```
Thought: 订单 O123 骑手已超时 15 分钟,距离商家 2km,处于离线状态
Action: query_rider_history(rider_id=R456)
Observation: 该骑手近 30 天准时率 95%,无事故记录,今日已在线 8 小时
Thought: 可能是临时下线或手机问题,先尝试联系
Action: call_rider(rider_id=R456)
Observation: 联系失败
Thought: 联系失败 + 已超时,触发重派
Action: reassign_order(order_id=O123, strategy="nearby_high_score")
Observation: 已派给骑手 R789,预计 5 分钟到达商家
Thought: 通知用户 + 记录异常
Action: notify_user(order_id=O123, msg="骑手临时更换,新骑手 5 分钟到店")
```

**3. 动态定价 Agent**

场景:暴雨天、节假日、夜间,供需失衡。

Agent 决策维度:
- 区域实时供需比(订单/运力)
- 天气 API(降雨量、能见度)
- 历史同时段数据
- 竞品定价(爬虫/数据合作)

Agent 输出:
- 配送费调整系数(1.0-3.0)
- 骑手补贴金额
- 是否暂停接单(极端情况)

**关键约束**: 定价调整不能太频繁(用户感知差),5-15 分钟一次;不能超过监管上限。

**4. 骑手助手 Agent(语音)**

骑手场景痛点:骑车中无法看手机,需要语音交互。

能力:
- 接单确认("你有新订单,商家 XX,取餐后送 XX,确认接单?")
- 导航播报(集成地图 SDK)
- 异常上报("商家没出餐"→ Agent 自动记录 + 通知用户)
- 收入查询("今天跑了多少单?收入多少?")

技术挑战:
- 噪声环境 ASR(风噪、交通噪音)→ 降噪模型 + 专属声学模型
- 方言识别(骑手多来自不同省份)→ 多方言模型
- 低延迟(端侧模型 + 云端协同),首响 < 800ms
- 安全(骑行中不能让骑手长时间对话)→ 主动挂断 + 简短播报

**5. 区域调度 Agent(多 Agent 协作)**

将城市划分为网格,每个网格一个 Agent,负责本区域运力调配。

- 网格 Agent 之间通信:相邻网格运力互助(高峰时跨网格调骑手)。
- 全局协调 Agent:监控全市状态,处理跨网格问题。
- 冲突解决:多个网格抢同一骑手时,全局 Agent 仲裁。

**6. Agent 与运筹的边界**

| 场景 | 谁主导 | 原因 |
|------|--------|------|
| 海量订单实时匹配 | 运筹 | 毫秒级、可证明最优 |
| ETA 预测 | ML | 数据驱动、连续值 |
| 异常订单处理 | Agent | 多步推理、跨系统联动 |
| 动态定价策略 | Agent + 规则 | 业务策略 + 实时判断 |
| 骑手交互 | Agent | 自然语言、复杂意图 |
| 区域运力调配 | Agent + 运筹 | Agent 决策 + 运筹执行 |

**7. 量化收益**

- 异常订单处理时长:平均 8 分钟 → 3 分钟
- 骑手事故响应:30 分钟 → 5 分钟
- 恶劣天气订单完成率:85% → 92%
- 骑手助手覆盖:已服务 100 万+ 骑手,日均千万次交互

**8. 面试加分点**

- 强调 Agent 不替代运筹,而是补充——显示工程认知。
- 提到"骑手安全第一",不为了效率牺牲骑手——显示价值观。
- 提到与地图、调度、支付等多团队协同——显示跨团队经验。

</details>

---

### Q4 RAG 在美团商家知识库中的应用,百万商家如何管理?

<details>
<summary>展开答案</summary>

**题目背景**: 美团有千万级商家,每家商家有菜单、营业信息、活动、评价、资质等丰富信息。构建统一的商家知识库,服务于智能客服、商家助手、用户咨询、搜索推荐,是 RAG 落地的典型大场景。

**1. 数据规模与特点**

- 商家数量:千万级(在线百万级)
- 单商家数据:菜单(图文)、营业时间、地址、电话、活动、资质、评价(万条/家)
- 数据更新频率:菜单天级、活动小时级、评价分钟级
- 多模态:菜单图、商家视频、用户上传图
- 质量参差:连锁店规范、个体户粗糙

**2. 整体架构**

```
┌──────────────────────────────────────────────┐
│  数据源层                                     │
│  商家后台 / App / 第三方 / 运营录入            │
├──────────────────────────────────────────────┤
│  数据处理层(离线 + 实时)                     │
│  ├─ ETL:清洗、去重、结构化                   │
│  ├─ 多模态解析:菜单图 OCR、视频 ASR          │
│  ├─ 信息抽取:菜品实体、价格、规格            │
│  └─ 质量评分:可信度、时效性                  │
├──────────────────────────────────────────────┤
│  索引层(双路)                               │
│  ├─ 向量索引:语义召回(分商家/分品类)        │
│  ├─ 关键词索引:精确召回(BM25/ES)            │
│  └─ 结构化索引:属性过滤(SQL/Redis)          │
├──────────────────────────────────────────────┤
│  召回层                                       │
│  ├─ 商家路由:先定位商家,再查知识            │
│  ├─ 多路召回:向量 + 关键词 + 结构化          │
│  └─ rerank:cross-encoder 精排                │
├──────────────────────────────────────────────┤
│  生成层                                       │
│  ├─ Prompt 模板(分场景:客服/助手/搜索)      │
│  ├─ 引用溯源(每条回答标注来源)              │
│  └─ 兜底(低置信度不答)                      │
├──────────────────────────────────────────────┤
│  应用层                                       │
│  智能客服 / 商家助手 / 用户咨询 / 搜索推荐    │
└──────────────────────────────────────────────┘
```

**3. 百万商家的索引管理(核心难点)**

**(a) 分商家隔离**

- 不把所有商家数据混在一个索引里(召回会乱)。
- 方案 1:物理分片(每 N 个商家一个索引),路由层先定位分片。
- 方案 2:元数据过滤(所有数据一个索引,但带商家 ID 字段,召回时强制过滤)。
- 美团规模:推荐方案 1 + 方案 2 结合,大商家单独索引,小商家共享索引 + 过滤。

**(b) 分层索引**

- L1:商家基础信息(高频查,Redis 缓存)
- L2:菜单/活动(中频,向量库 + 关键词)
- L3:评价/历史问答(低频,冷数据归档)

**(c) 增量更新**

- 菜单变更:商家后台提交 → ETL → 增量重建该商家索引(分钟级)。
- 评价新增:流式处理,实时 append(不重建)。
- 活动变更:不进向量库,实时查 API(避免脏数据)。

**(d) 索引压缩与成本**

- 向量量化:PQ/SQ 压缩,空间降至 1/4。
- 冷热分离:30 天未查询的商家索引归档到 OSS。
- 多租户:共享集群,按业务线(QPS)配额。

**4. 多模态菜单处理**

菜单是商家知识库的核心,但大量商家只有图片菜单。

```
菜单图 → OCR(文字识别)
      → 菜品实体识别(LLM few-shot)
      → 价格/规格抽取
      → 菜品分类(热菜/凉菜/主食)
      → 入库(结构化 + 向量)
```

- OCR:自研模型 + PaddleOCR 兜底,准确率 95%+。
- 实体识别:LLM few-shot,人工抽检校正。
- 模糊菜品名("招牌菜 1")→ 标注为低置信度,不进入向量库,只在结构化字段保留。

**5. 召回策略**

**(a) 商家路由优先**

用户问"海底捞朝阳大悦城店有什么推荐?",先做实体识别(商家名 + 门店),定位到具体商家,再在其知识库内召回。

避免:全局召回导致混入其他海底捞门店或竞品信息。

**(b) 多路召回融合**

- 向量召回(BGE-M3):top 20
- 关键词召回(BM25):top 20
- 结构化召回(菜品名精确匹配):top 5
- RRF(Reciprocal Rank Fusion)融合 → top 10
- rerank(bge-reranker):top 3

**(c) 时效性过滤**

- 营业时间:实时查 Redis,打烊了直接告知用户。
- 活动:实时查 API,不依赖向量库。
- 菜品:天级更新,可接受向量库内延迟。

**6. 生成层设计**

- Prompt 模板分场景:客服(简短准确)、助手(详细推荐)、搜索(摘要)。
- 引用溯源:每条回答标注"来自商家菜单/活动/评价",用户可点击查看。
- 兜底:rerank 分数 < 0.5 → 不答,转人工或推荐用户直接联系商家。
- 多语言:支持中英日韩(游客场景)。

**7. 质量与评测**

- 离线:召回率(top-k 命中)、准确率(回答正确性)、引用准确率。
- 在线:用户反馈(点赞/点踩)、二次咨询率、转人工率。
- 商家侧:商家投诉率(回答错误导致的纠纷)。

**8. 难点与权衡**

- **数据质量**: 个体户菜单图模糊、文字不规范 → 人工运营 + LLM 校验。
- **时效性**: 活动频繁变更 → 实时 API + 不入库。
- **成本**: 千万级向量 → 量化 + 冷热分离 + 多租户。
- **跨商家比较**: "海底捞和呷哺呷哺哪个划算?"——不能只召回一家,需要 Multi-Query + 汇总。

**9. 量化指标**

- 召回 top-3 命中率:92%
- 回答准确率:88%
- 商家知识库查询 P99:200ms
- 月活商家助手用户:500 万+

</details>

---

### Q5 蚂蚁集团面试风格 — 蚂蚁 CTO 线/风控/财富团队,面试流程和考察重点是什么?

<details>
<summary>展开答案</summary>

**1. 团队划分与 Agent 相关方向**

蚂蚁与 Agent/LLM 强相关的团队:

- **CTO 线 / AI 平台**: 大模型基础设施、AntSense、金融大模型 AntCoder/智蚁,Agent 框架"语控"。
- **大安全(风控)**: 智能风控 AlphaRisk、反欺诈、反洗钱、信贷风控,Agent 用于智能审批和欺诈检测。
- **财富事业群**: 智能投顾"帮你投"、理财助手、资产配置 Agent。
- **客服(智能客服中心)**: 支付宝客服、账务纠纷、智能坐席辅助。
- **网商银行**: 小微企业信贷 Agent、风控 Agent。
- **保险(相互宝后续)**: 智能核保、理赔 Agent。

**2. 面试流程(社招典型)**

| 轮次 | 时长 | 考察内容 | 备注 |
|------|------|---------|------|
| 一面(技术) | 60-90 min | 八股 + 算法 + 项目 | 重视基础 |
| 二面(技术) | 60-90 min | 系统设计(金融场景) + 项目深挖 | 金融特色强 |
| 三面(交叉面) | 60 min | 跨团队视角 + 架构能力 | 防止本位主义 |
| 四面(GM/Hiring Manager) | 60 min | 业务理解 + 团队匹配 + 价值观 | 阿里系重价值观 |
| 五面(HR) | 45 min | 稳定性 + 薪资 + 价值观 | 阿里 HR 有否决权 |

校招 3-4 轮技术 + HR,价值观面(阿里味)权重较高。

**3. 考察重点(蚂蚁特色)**

- **金融合规意识**: 几乎必问"LLM 在金融场景的风险"、"如何保证不违规"、"监管要求怎么落地"。回答不出合规要点,基本挂。
- **安全与审计**: 全链路日志、可追溯、不可篡改、人工复核,这些词要主动抛。
- **高可用与稳定性**: 金融级 SLA(99.99%+)、双活容灾、灰度方案、回滚预案。
- **风险识别能力**: 候选人要能识别 LLM 幻觉、提示注入、数据泄露等风险,并提出工程化防控。
- **业务深度**: 风控团队会问"欺诈有哪些类型?""信贷风控的流程是什么?";财富团队会问"资产配置的理论基础?"——不能只懂技术不懂业务。
- **价值观(阿里味)**: 客户第一、拥抱变化、团队合作,面试中可能问"你做过最有挑战的事?""你怎么处理和同事的分歧?"。

**4. 蚂蚁 Agent 方向的真实工作**

- 智能风控引擎 AlphaRisk(实时欺诈检测,毫秒级决策)。
- 智能信贷审批(网商银行小微企业贷,Agent 辅助决策)。
- 智能投顾"帮你投"(资产配置、风险偏好匹配)。
- 支付宝智能客服(账务、纠纷、退款,日均亿级会话)。
- 智能核保/理赔(保险场景)。
- 反洗钱 Agent(交易链路分析、可疑交易识别)。
- 内部 Copilot(坐席辅助、运营辅助、研发辅助)。

**5. 备考建议**

- 熟悉蚂蚁技术博客(蚂蚁技术 ATEC、InfoQ 蚂蚁专栏),尤其是 AlphaRisk、智能投顾相关。
- 至少能讲清楚 1 个金融场景的 Agent 设计(推荐:智能审批 or 智能投顾)。
- 准备金融合规相关知识:监管要求(央行、银保监)、数据安全法、个人信息保护法。
- 了解蚂蚁自研模型(Bailing、AntCoder),显示对公司技术的关注。
- 价值观准备:想 2-3 个"挑战/合作/客户第一"的故事,用 STAR 法则讲。

**6. 美团 vs 蚂蚁面试对比**

| 维度 | 美团 | 蚂蚁 |
|------|------|------|
| 业务导向 | 本地生活、效率 | 金融、合规 |
| 技术风格 | 重工程、务实 | 重架构、严谨 |
| 系统设计题 | 客服/调度/RAG | 风控/投顾/客服中台 |
| 必考 | 业务理解、ROI | 合规、安全、审计 |
| 价值观 | 简单直接 | 阿里味较重 |
| 难点 | 多业务线协同 | 金融级稳定性 |

</details>

---

### Q6 Agent 在金融风控中的应用(智能审批/欺诈检测/风险评估)

<details>
<summary>展开答案</summary>

**题目背景**: 蚂蚁风控是行业标杆,AlphaRisk 已实现毫秒级欺诈检测。Agent 在风控中的引入,不是为了替代传统风控模型(XGBoost/图神经网络),而是在"复杂案件研判"、"跨系统联动"、"可解释决策"上做增强。

**1. 风控场景的三层架构**

```
┌──────────────────────────────────────────┐
│  L3: Agent 研判层(复杂案件)              │
│  ├─ 智能审批 Agent(信贷/开户/提额)       │
│  ├─ 欺诈研判 Agent(可疑案件深度分析)     │
│  ├─ 反洗钱 Agent(交易链路追溯)          │
│  └─ 风险评估 Agent(企业/个人综合评估)    │
├──────────────────────────────────────────┤
│  L2: 规则 + 模型层(实时决策)             │
│  ├─ 规则引擎(黑白名单、阈值)             │
│  ├─ ML 模型(XGBoost 评分)               │
│  └─ 图神经网络(团伙识别)                 │
├──────────────────────────────────────────┤
│  L1: 数据层(特征 + 关系)                 │
│  ├─ 实时特征(交易/设备/位置)             │
│  ├─ 离线特征(历史行为/信用)              │
│  └─ 关系图谱(账户/设备/资金流向)         │
└──────────────────────────────────────────┘
```

**关键认知**: Agent 在 L3,处理 L2 难以决策的"灰色地带"。

**2. 智能审批 Agent(信贷场景)**

场景:小微企业贷、消费贷、信用卡提额。

传统流程:申请 → 规则过滤 → 模型评分 → 人工复核 → 决策。
Agent 增强:对"模型分数中等、规则未拦截"的灰色地带,Agent 做深度研判。

Agent 工作流(Plan-Execute):

```
Plan:
  1. 拉取申请人画像(基本信息、信用历史)
  2. 拉取企业经营数据(流水、税务、社保)
  3. 关系图谱查询(关联企业、法人、股东)
  4. 行业风险查询(当前行业政策、市场情况)
  5. 综合评估 + 生成审批意见

Execute:
  - tool: query_applicant_profile(id=xxx) → 画像
  - tool: query_company_finance(company_id=xxx) → 财务数据
  - tool: query_relation_graph(entity=xxx, depth=2) → 关联关系
  - tool: query_industry_risk(industry="餐饮") → 行业风险
  - tool: query_credit_history(id=xxx) → 信用记录

Synthesize:
  - LLM 综合分析:经营稳定、流水正常、无不良关联、行业中等风险
  - 决策建议:批准,额度 50 万,利率 6.5%
  - 风险点:关联企业有 1 条被执行记录,建议人工复核

Output:
  - 决策: approve(额度 50 万,利率 6.5%)
  - 置信度: 0.82
  - 理由:经营稳定 + 信用良好 + 行业可控
  - 风险提示:关联企业被执行,建议贷后重点关注
  - 是否人工复核:是(关联风险点)
```

**关键设计**:
- Agent 不直接放款,只给决策建议,最终决策由审批系统 + 人工确认。
- 每一步推理都可追溯(审计日志),监管可回放。
- 置信度 < 0.7 → 强制人工复核。
- 额度 > 100 万 → 强制人工复核。

**3. 欺诈检测 Agent**

场景:盗刷、套现、营销薅羊毛、虚假交易。

传统:规则 + 模型实时拦截(毫秒级),但复杂欺诈(团伙、慢刷)漏报多。

Agent 用途:对"模型分数中等、疑似但不确定"的案件做深度分析。

Agent 能力:
- 设备指纹分析(同一设备多账号?)
- 交易链路追溯(资金从哪来、到哪去)
- 行为序列分析(短时间内异常操作模式)
- 关联团伙识别(图查询,关联其他可疑账户)

输出:
- 欺诈概率(0-1)
- 欺诈类型(盗刷/套现/薅羊毛)
- 关联团伙(如有)
- 处置建议(拦截/限额/人工核实)
- 证据链(每条判断的依据)

**4. 反洗钱 Agent**

场景:大额可疑交易、跨境资金流动、账户拆分转账。

Agent 工作流:
- 识别可疑模式(分散转入集中转出、快进快出、夜间大额)
- 资金链路追溯(多层转账还原)
- 关联账户分析(图查询)
- 行业/地区风险叠加
- 生成可疑交易报告(STR)

合规要求:
- 报告必须可追溯,每条结论有证据。
- Agent 不直接上报,人工复核后上报监管。
- 全程留痕,保留 5 年以上。

**5. 风险评估 Agent(企业/个人综合评估)**

场景:信贷准入、合作方尽调、商户入驻审核。

Agent 输入:工商信息、司法信息、舆情、财务、关联关系。
Agent 输出:综合风险评分 + 风险点清单 + 建议。

特色:
- 多源信息融合(结构化 + 非结构化舆情)。
- LLM 分析舆情(负面新闻、监管处罚)。
- 关联企业风险传导(母公司/子公司/股东)。

**6. Agent 与传统风控的协同**

| 场景 | 传统模型 | Agent | 协同方式 |
|------|---------|-------|---------|
| 实时交易拦截 | 主导(毫秒级) | 不参与 | - |
| 信贷审批 | 模型评分 | 灰色地带研判 | 模型筛 → Agent 复核 |
| 复杂欺诈识别 | 初筛 | 深度分析 | 模型标记 → Agent 调查 |
| 反洗钱上报 | 规则触发 | 链路分析 | 规则触发 → Agent 还原 |
| 综合风险评估 | - | 主导 | Agent 全流程 |

**7. 安全合规要求**

- **可解释**: 每个决策必须能解释,LLM 生成自然语言解释 + 结构化证据。
- **可追溯**: 全链路日志,输入/推理/输出/人工操作全部记录。
- **可回放**: 监管要求时,能复现任意一次决策。
- **人工兜底**: 高风险、低置信度、大金额 → 强制人工。
- **数据安全**: 敏感数据脱敏,LLM 不接触原始身份证号、卡号。
- **模型版本**: 每次决策记录模型版本,便于回溯。

**8. 量化收益**

- 信贷审批自动化率:60% → 80%(灰色地带由 Agent 处理)
- 复杂欺诈识别率:70% → 88%
- 反洗钱上报准确率:75% → 90%
- 审批时效:平均 2 天 → 4 小时
- 人工复核量:下降 40%

**9. 难点与权衡**

- **LLM 幻觉**: 风控决策绝不能幻觉,必须以数据为准,LLM 只做综合分析。
- **数据合规**: 个人信息保护法、数据安全法,LLM 调用第三方数据要合规。
- **监管可解释**: 监管要求"算法可解释",LLM 黑盒部分要补充规则解释。
- **实时性**: Agent 推理慢(秒级),不能用于实时拦截,只用于准实时和离线。
- **成本**: LLM 调用贵,只对"值得研判"的案件用 Agent(模型分数中等 + 金额较大)。

</details>

---

### Q7 设计支付宝智能理财助手 Agent

<details>
<summary>展开答案</summary>

**题目背景**: 蚂蚁财富"帮你投"是行业标杆智能投顾产品。Agent 增强后,可以从"标准化推荐"升级为"个性化对话式理财顾问",处理用户咨询、资产配置建议、市场解读、风险提醒等。

**1. 需求澄清**

- **用户**: 支付宝财富用户(千万级),理财小白到资深投资者。
- **场景**: 投资咨询、持仓分析、市场解读、风险提醒、产品推荐。
- **合规**: 必须持牌投顾,不能给具体买卖点位建议(违规),只能做资产配置建议。
- **目标**: 提升用户理财体验 + AUM 增长 + 客户粘性。

**2. 整体架构**

```
┌──────────────────────────────────────────────┐
│  接入层: 支付宝 App / 财富号 / 客服          │
├──────────────────────────────────────────────┤
│  对话编排层                                   │
│  ├─ 意图识别(咨询/持仓/市场/推荐/风险)       │
│  ├─ 用户画像(风险偏好/资产/历史)             │
│  ├─ 合规前置检查(持牌范围/禁止话术)          │
│  └─ 多 Agent 路由                             │
├──────────────────────────────────────────────┤
│  Agent 层                                     │
│  ├─ 投资咨询 Agent(产品/规则问答)            │
│  ├─ 资产配置 Agent(组合建议 + 再平衡)        │
│  ├─ 市场解读 Agent(行情/新闻/热点)           │
│  ├─ 持仓分析 Agent(盈亏/归因/优化)           │
│  └─ 风险提醒 Agent(回撤/集中度/期限错配)     │
├──────────────────────────────────────────────┤
│  能力层                                       │
│  ├─ 行情 API(实时/历史)                      │
│  ├─ 产品数据库(基金/理财/保险)               │
│  ├─ 资讯 RAG(研报/新闻/政策)                 │
│  ├─ 资产配置模型(马科维茨/BL/风险平价)       │
│  └─ 合规规则引擎                              │
├──────────────────────────────────────────────┤
│  保障层                                       │
│  ├─ 合规审查(话术 + 建议)                    │
│  ├─ 风险揭示(每次建议带风险提示)             │
│  ├─ 审计日志(全链路)                         │
│  └─ 人工投顾兜底                              │
└──────────────────────────────────────────────┘
```

**3. 关键设计点**

**(a) 用户画像(KYC)**

风险偏好评估(问卷 + 行为推断):
- 主观:风险承受能力问卷(标准化,合规要求)
- 客观:年龄、收入、资产、投资期限、流动性需求
- 行为:历史交易风格(追涨杀跌?稳健?保守?)

输出:风险等级(C1-C5)+ 投资目标 + 期限偏好。

**(b) 资产配置 Agent(核心)**

输入:用户画像 + 当前持仓 + 市场状态。
流程:
1. 确定战略配置(长期,基于风险等级)
   - C3(平衡型):股 50% 债 30% 商品 10% 现金 10%
2. 战术调整(短期,基于市场状态)
   - 当前股市估值偏高 → 股降至 45%
3. 产品映射(配置到具体基金)
   - 股票部分:沪深 300 ETF + 中证 500 ETF
4. 再平衡建议(偏离阈值时)
   - 当前股票占比 55% → 建议卖出 5% 调回 50%
5. 输出建议 + 风险提示

**关键约束**:
- 不给具体买卖点位(违规)。
- 必须带风险提示("投资有风险,过往业绩不代表未来")。
- 推荐产品必须在持牌范围内。
- 单只产品集中度 < 30%。

**(c) 市场解读 Agent**

- 资讯 RAG:接入研报、新闻、政策,实时更新。
- 多源融合:券商研报 + 财经媒体 + 官方公告。
- LLM 摘要:每日市场早报、热点解读、政策影响。
- 个性化:基于用户持仓,推送相关资讯(持有新能源基金 → 推送新能源行业动态)。

**合规要求**:
- 不做预测("明天涨/跌")。
- 引用来源(哪家券商、哪份报告)。
- 风险提示。

**(d) 持仓分析 Agent**

- 盈亏分析:总收益、单只收益、对比基准。
- 归因分析:资产配置贡献 + 选品贡献 + 择时贡献。
- 风险分析:波动率、最大回撤、夏普比率。
- 优化建议:偏离目标配置、集中度过高、风格漂移。

**(e) 风险提醒 Agent**

- 回撤提醒:组合回撤 > 10% → 提醒用户。
- 集中度提醒:单只产品 > 30% → 提醒。
- 期限错配:短期资金买长期产品 → 提醒。
- 市场风险:重大事件(如股市暴跌)→ 推送风险提示。

**(f) 合规审查(贯穿全程)**

- 输入审查:用户问"明天哪只股票涨停?"→ 识别违规意图,拒绝回答。
- 过程审查:Agent 输出前,规则引擎检查话术(禁用"保本"、"稳赚"、"必涨")。
- 输出审查:每条建议必须带风险提示 + 持牌声明。
- 事后审查:全量日志审计,合规团队抽检。

**(g) 人工投顾协作**

转人工场景:
- 用户主动要求人工投顾。
- 高净值用户(VIP)专属服务。
- 复杂需求(税务规划、家族信托)Agent 不处理。
- 合规风险事件。

转人工时携带:用户画像 + 历史对话摘要 + Agent 初步建议。

**4. 评测体系**

- **业务指标**: AUM 增长、用户活跃、留存、转化率。
- **体验指标**: CSAT、NPS、问题解决率。
- **合规指标**: 违规话术率(目标 0)、投诉率、监管通报。
- **风险指标**: 用户亏损率、风险事件数。

**5. 量化目标**

- 理财助手月活:1000 万+
- 资产配置建议采纳率:25%
- AUM 增长贡献:+15%
- 合规违规率:0(红线)
- 用户 CSAT:90%+

**6. 难点与权衡**

- **合规 vs 体验**: 合规要求多风险提示,体验上嫌啰嗦 → 用自然语言柔和表达,关键节点提示。
- **个性化 vs 标准化**: 完全个性化成本高 + 合规难 → 分层(标准化组合 + 个性化微调)。
- **LLM 幻觉**: 金融数据绝不能错 → 行情/产品数据走 API,LLM 只做组织和表达。
- **监管变化**: 政策变化快 → 合规规则引擎可热更新,LLM Prompt 同步更新。

</details>

---

### Q8 金融场景 Agent 的安全和合规要求,如何实现?

<details>
<summary>展开答案</summary>

**题目背景**: 金融场景对 Agent 的安全和合规要求是其他行业的 10 倍以上。这道题考察候选人对金融监管、数据安全、模型风险的系统性认知,是蚂蚁面试的高频题。

**1. 金融场景的特殊性**

| 维度 | 普通场景 | 金融场景 |
|------|---------|---------|
| 错误代价 | 体验差 | 资金损失、监管处罚 |
| 合规要求 | 宽松 | 严格(央行/银保监/证监会) |
| 数据敏感度 | 中 | 极高(身份证/卡号/资产) |
| 审计要求 | 一般 | 全链路 + 5 年留存 |
| 可解释性 | 可选 | 必须 |
| 兜底机制 | 转人工 | 多重兜底 + 人工 + 熔断 |

**2. 安全合规的六大支柱**

```
┌─────────────────────────────────────────┐
│  1. 数据安全(脱敏 + 权限 + 加密)        │
├─────────────────────────────────────────┤
│  2. 模型安全(幻觉 + 注入 + 越狱)        │
├─────────────────────────────────────────┤
│  3. 决策安全(可解释 + 可追溯 + 可回放)  │
├─────────────────────────────────────────┤
│  4. 输出安全(合规审查 + 风险提示)       │
├─────────────────────────────────────────┤
│  5. 运行安全(熔断 + 限流 + 兜底)        │
├─────────────────────────────────────────┤
│  6. 持续合规(审计 + 复盘 + 迭代)        │
└─────────────────────────────────────────┘
```

**3. 数据安全**

**(a) 敏感数据脱敏**

- 身份证号:脱敏后传入 LLM(110101****1234)。
- 银行卡号:仅传末 4 位。
- 手机号:脱敏(138****5678)。
- 资产金额:分级脱敏(大额仅传范围"10-50 万")。
- 原始数据:仅在内部系统流转,LLM 不接触。

**(b) 数据权限**

- 基于角色 RBAC,Agent 只能查询其业务范围内的数据。
- 跨业务数据访问需审计 + 审批。
- LLM 推理日志脱敏存储,不留存原始敏感信息。

**(c) 加密传输与存储**

- 传输:TLS 1.3。
- 存储:AES-256 加密 + KMS 托管密钥。
- 日志:敏感字段加密 + 字段级权限。

**(d) 数据出境合规**

- 用户数据不出境(数据安全法、个人信息保护法)。
- 跨境业务使用本地化部署的 LLM。
- 第三方 LLM 调用需合规评估(大部分金融场景禁用境外 LLM)。

**4. 模型安全**

**(a) 幻觉防控**

- 事实性数据(金额、利率、规则)走 API,不依赖 LLM 生成。
- RAG 引用溯源,每条回答标注来源。
- 置信度阈值,低于阈值不答或转人工。
- 关键决策(放款、投资建议)强制人工复核。

**(b) 提示注入防御**

- 用户输入与系统 Prompt 隔离(分隔符 + 标记)。
- 输入净化(过滤"忽略上述指令"等)。
- 输出审查(检测是否泄露系统 Prompt)。
- 红队测试(定期攻击测试)。

**(c) 越狱防御**

- 系统 Prompt 强约束("你是金融助手,不能讨论非金融话题")。
- 输入分类器(检测越狱意图)。
- 输出分类器(检测违规内容)。
- 拒答策略(明确拒绝 + 引导合规话题)。

**(d) 模型版本管理**

- 每次决策记录模型版本 + Prompt 版本。
- 模型升级需回归测试 + 灰度。
- 旧版本可回滚(监管要求时复现历史决策)。

**5. 决策安全**

**(a) 可解释性**

- 每个决策输出自然语言解释 + 结构化证据。
- 关键决策(放款、风控)附加规则解释(哪些规则触发)。
- 监管要求时,能提供决策报告。

**(b) 可追溯**

- 全链路日志:输入 → 意图识别 → Agent 推理 → 工具调用 → 输出 → 人工操作。
- 日志不可篡改(区块链 / WORM 存储)。
- 保留期限:5 年以上(监管要求)。

**(c) 可回放**

- 任意一次决策,能用历史输入复现输出。
- 模型版本 + Prompt 版本 + 数据快照均留存。
- 监管检查时,能演示决策过程。

**6. 输出安全**

**(a) 合规审查**

- 话术审查:禁用"保本"、"稳赚"、"必涨"、"无风险"等违规词。
- 建议审查:投资建议必须在持牌范围内。
- 风险提示:每条投资建议带"投资有风险"提示。
- 误导审查:不能夸大收益、隐瞒风险。

**(b) 内容过滤**

- 政治敏感、违法、欺诈内容过滤。
- 不当建议(具体股票买卖点位)过滤。
- 用户隐私(无意中泄露他人信息)过滤。

**7. 运行安全**

**(a) 熔断机制**

- 错误率 > 阈值(如 5%)→ 自动熔断,降级到规则引擎或人工。
- 延迟 > 阈值 → 限流 + 降级。
- 监控指标:错误率、延迟、投诉率、合规违规率。

**(b) 限流**

- 按 user_id 限流(防滥用)。
- 按 API 限流(保护下游)。
- 按业务线限流(隔离故障)。

**(c) 多重兜底**

```
Agent 决策(高置信度)→ 直接执行
  ↓ 置信度不足
Agent 决策 + 人工复核 → 人工确认后执行
  ↓ Agent 异常
规则引擎兜底 → 规则决策
  ↓ 规则未覆盖
人工兜底 → 转人工
```

**8. 持续合规**

**(a) 审计**

- 内部审计:定期抽检决策日志,合规团队评审。
- 外部审计:配合监管检查,提供决策报告。
- 第三方审计:年度合规审计( ISO 27001、等保)。

**(b) 复盘**

- 重大事件(违规、投诉、损失)复盘,根因分析。
- 模型问题修复 → 灰度上线 → 全量。
- 规则更新 → 合规评审 → 发布。

**(c) 迭代**

- 合规规则引擎热更新(政策变化快速响应)。
- Prompt 版本管理 + A/B 测试。
- 模型迭代 + 回归测试。

**9. 监管要求清单**

| 法规 | 关键要求 |
|------|---------|
| 个人信息保护法 | 知情同意、最小必要、可删除 |
| 数据安全法 | 数据分级、出境合规 |
| 网络安全法 | 等保、关键信息基础设施 |
| 金融消费者权益保护 | 不得误导、风险提示 |
| 互联网贷款新规 | 风控自主、不得过度授信 |
| 算法推荐管理规定 | 算法可解释、用户可关闭 |
| 持牌投顾要求 | 持牌范围内建议、不得代客决策 |

**10. 量化指标**

- 合规违规率:0(红线)
- 决策可解释率:100%
- 日志完整率:100%
- 审计通过率:100%
- 熔断触发后恢复时间:< 5 分钟

</details>

---

### Q9 手撕代码:实现一个金融场景 Agent(意图识别/风险检查/工具调用/合规审查/审计日志)

<details>
<summary>展开代码</summary>

**题目要求**: 用 Python 实现一个金融场景 Agent,包含意图识别、风险检查、工具调用、合规审查、审计日志五大模块。代码需完整可运行,体现金融级安全和合规。

```python
"""
金融场景 Agent 完整实现
=======================
包含: 意图识别 / 风险检查 / 工具调用 / 合规审查 / 审计日志
体现: 金融级安全(脱敏)、合规(话术审查)、可追溯(全链路日志)
"""

import json
import time
import uuid
import re
import logging
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional, Callable
from datetime import datetime


# ============================================================
# 1. 审计日志模块(不可篡改,全链路可回放)
# ============================================================

class AuditLogger:
    """金融级审计日志:全链路记录,带哈希链防篡改"""

    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self._last_hash = "0" * 64  # 创世哈希
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def log(self, event: str, data: dict, session_id: str):
        """记录一条审计日志,带前一条哈希形成链"""
        import hashlib
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
            "event": event,
            "data": data,
            "prev_hash": self._last_hash,
        }
        entry_str = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        cur_hash = hashlib.sha256(entry_str.encode()).hexdigest()
        entry["hash"] = cur_hash
        self._last_hash = cur_hash
        self.logger.info(json.dumps(entry, ensure_ascii=False))
        return entry


# ============================================================
# 2. 数据脱敏模块
# ============================================================

class DataMasker:
    """敏感数据脱敏,确保 LLM 不接触原始敏感信息"""

    @staticmethod
    def mask_id_card(id_card: str) -> str:
        """身份证: 110101199001011234 → 110101********1234"""
        if len(id_card) >= 14:
            return id_card[:6] + "*" * 8 + id_card[-4:]
        return "***"

    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号: 13812345678 → 138****5678"""
        if len(phone) == 11:
            return phone[:3] + "****" + phone[-4:]
        return "***"

    @staticmethod
    def mask_bank_card(card: str) -> str:
        """银行卡: 仅保留末 4 位"""
        if len(card) >= 4:
            return "*" * (len(card) - 4) + card[-4:]
        return "***"

    @staticmethod
    def mask_amount(amount: float) -> str:
        """金额: 分级脱敏,返回区间"""
        if amount < 10000:
            return "1万以下"
        elif amount < 100000:
            return "1-10万"
        elif amount < 1000000:
            return "10-100万"
        else:
            return "100万以上"

    @staticmethod
    def mask_user_profile(profile: dict) -> dict:
        """脱敏用户画像"""
        masked = profile.copy()
        if "id_card" in masked:
            masked["id_card"] = DataMasker.mask_id_card(masked["id_card"])
        if "phone" in masked:
            masked["phone"] = DataMasker.mask_phone(masked["phone"])
        if "bank_card" in masked:
            masked["bank_card"] = DataMasker.mask_bank_card(masked["bank_card"])
        if "asset" in masked:
            masked["asset"] = DataMasker.mask_amount(masked["asset"])
        return masked


# ============================================================
# 3. 合规审查模块
# ============================================================

class ComplianceChecker:
    """金融合规审查: 话术 + 建议 + 风险提示"""

    # 违规词清单(可热更新)
    FORBIDDEN_WORDS = [
        "保本", "稳赚", "必涨", "必跌", "无风险", "零风险",
        "保证收益", "绝对盈利", "稳赚不赔", "包赚",
    ]

    # 必须包含的风险提示(投资类建议)
    REQUIRED_RISK_WARNINGS = [
        "投资有风险",
        "过往业绩不代表未来",
    ]

    @classmethod
    def check_forbidden_words(cls, text: str) -> list:
        """检查违规词,返回命中的违规词列表"""
        hits = []
        for word in cls.FORBIDDEN_WORDS:
            if word in text:
                hits.append(word)
        return hits

    @classmethod
    def check_risk_warning(cls, text: str, intent: str) -> bool:
        """检查投资类建议是否带风险提示"""
        if intent not in ["investment_advice", "product_recommendation"]:
            return True
        for warning in cls.REQUIRED_RISK_WARNINGS:
            if warning in text:
                return True
        return False

    @classmethod
    def check_specific_stock_advice(cls, text: str) -> bool:
        """检查是否给出具体股票买卖点位(违规)"""
        # 简化:检测"买入/卖出 XX 元"等模式
        patterns = [
            r"(买入|卖出|加仓|减仓).{0,10}(元|块)",
            r"目标价.{0,5}\d+",
            r"止损.{0,5}\d+",
        ]
        for p in patterns:
            if re.search(p, text):
                return True
        return False

    @classmethod
    def review(cls, text: str, intent: str) -> dict:
        """合规审查总入口"""
        forbidden = cls.check_forbidden_words(text)
        has_warning = cls.check_risk_warning(text, intent)
        specific_advice = cls.check_specific_stock_advice(text)
        passed = (len(forbidden) == 0) and has_warning and (not specific_advice)
        return {
            "passed": passed,
            "forbidden_words": forbidden,
            "has_risk_warning": has_warning,
            "has_specific_advice": specific_advice,
            "reason": cls._build_reason(forbidden, has_warning, specific_advice),
        }

    @classmethod
    def _build_reason(cls, forbidden, has_warning, specific) -> str:
        reasons = []
        if forbidden:
            reasons.append(f"命中违规词: {forbidden}")
        if not has_warning:
            reasons.append("缺少风险提示")
        if specific:
            reasons.append("包含具体买卖点位建议(违规)")
        return "; ".join(reasons) if reasons else "OK"


# ============================================================
# 4. 风险检查模块
# ============================================================

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class RiskCheckResult:
    level: RiskLevel
    score: float  # 0-1
    reasons: list = field(default_factory=list)


class RiskChecker:
    """风险检查: 用户风险等级 + 操作风险 + 反欺诈"""

    @staticmethod
    def check_user_risk(user_profile: dict) -> RiskCheckResult:
        """用户风险等级评估"""
        score = 0.0
        reasons = []
        # 信用评分
        credit_score = user_profile.get("credit_score", 600)
        if credit_score < 500:
            score += 0.4
            reasons.append("信用评分低")
        elif credit_score < 650:
            score += 0.2
            reasons.append("信用评分中等")
        # 历史违规
        if user_profile.get("violation_count", 0) > 0:
            score += 0.3
            reasons.append(f"历史违规 {user_profile['violation_count']} 次")
        # 账户年龄
        account_age_months = user_profile.get("account_age_months", 0)
        if account_age_months < 3:
            score += 0.2
            reasons.append("新开户(小于3个月)")
        # 实名认证
        if not user_profile.get("verified", False):
            score += 0.3
            reasons.append("未实名认证")

        if score >= 0.6:
            level = RiskLevel.HIGH
        elif score >= 0.3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return RiskCheckResult(level=level, score=min(score, 1.0), reasons=reasons)

    @staticmethod
    def check_operation_risk(intent: str, amount: float, user_profile: dict) -> RiskCheckResult:
        """操作风险检查"""
        score = 0.0
        reasons = []
        # 大额操作
        asset = user_profile.get("asset", 0)
        if intent == "investment_advice" and amount > asset * 0.5:
            score += 0.4
            reasons.append("建议金额超过资产50%")
        if amount > 1000000:
            score += 0.3
            reasons.append("大额操作(>100万)")
        # 频繁操作(简化)
        if user_profile.get("recent_op_count", 0) > 10:
            score += 0.2
            reasons.append("近期操作频繁")
        # 异常时段
        hour = datetime.now().hour
        if hour < 6 or hour > 23:
            score += 0.2
            reasons.append("异常时段操作")

        if score >= 0.6:
            level = RiskLevel.HIGH
        elif score >= 0.3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return RiskCheckResult(level=level, score=min(score, 1.0), reasons=reasons)

    @classmethod
    def check(cls, intent: str, amount: float, user_profile: dict) -> dict:
        """风险检查总入口"""
        user_risk = cls.check_user_risk(user_profile)
        op_risk = cls.check_operation_risk(intent, amount, user_profile)
        # 综合风险 = max(用户风险, 操作风险)
        total_score = max(user_risk.score, op_risk.score)
        if total_score >= 0.6:
            level = RiskLevel.HIGH
        elif total_score >= 0.3:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        return {
            "level": level.value,
            "score": total_score,
            "user_risk": {"level": user_risk.level.value, "reasons": user_risk.reasons},
            "operation_risk": {"level": op_risk.level.value, "reasons": op_risk.reasons},
            "need_human_review": level == RiskLevel.HIGH,
        }


# ============================================================
# 5. 工具定义(金融工具集)
# ============================================================

@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    risk_level: RiskLevel = RiskLevel.LOW


class FinanceTools:
    """金融工具集: 模拟真实金融API"""

    @staticmethod
    def query_account(user_id: str) -> dict:
        """查询账户信息(脱敏后返回)"""
        # 模拟数据
        raw = {
            "user_id": user_id,
            "name": "张**",
            "id_card": "110101199001011234",
            "phone": "13812345678",
            "bank_card": "6222021234567890123",
            "asset": 500000,
            "credit_score": 720,
        }
        return DataMasker.mask_user_profile(raw)

    @staticmethod
    def query_market(stock_code: str) -> dict:
        """查询行情"""
        # 模拟行情数据
        return {
            "code": stock_code,
            "name": "示例基金",
            "nav": 1.2345,
            "daily_change": 0.0123,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def query_product(product_id: str) -> dict:
        """查询产品信息"""
        return {
            "product_id": product_id,
            "name": "示例稳健理财",
            "type": "bond_fund",
            "risk_level": "R2",
            "historical_return": "3.5%(过去一年)",
            "min_invest": 1000,
        }

    @staticmethod
    def calculate_portfolio(risk_level: str, amount: float) -> dict:
        """资产配置建议(基于风险等级)"""
        portfolios = {
            "C1": {"cash": 0.7, "bond": 0.3, "stock": 0.0, "commodity": 0.0},
            "C2": {"cash": 0.5, "bond": 0.4, "stock": 0.1, "commodity": 0.0},
            "C3": {"cash": 0.1, "bond": 0.3, "stock": 0.5, "commodity": 0.1},
            "C4": {"cash": 0.05, "bond": 0.2, "stock": 0.6, "commodity": 0.15},
            "C5": {"cash": 0.0, "bond": 0.1, "stock": 0.7, "commodity": 0.2},
        }
        alloc = portfolios.get(risk_level, portfolios["C2"])
        return {
            "risk_level": risk_level,
            "amount": amount,
            "allocation": {k: round(v * amount, 2) for k, v in alloc.items()},
            "risk_warning": "投资有风险,过往业绩不代表未来",
        }


# ============================================================
# 6. 意图识别模块
# ============================================================

class Intent(Enum):
    ACCOUNT_QUERY = "account_query"
    MARKET_QUERY = "market_query"
    PRODUCT_QUERY = "product_query"
    INVESTMENT_ADVICE = "investment_advice"
    COMPLAINT = "complaint"
    OTHER = "other"


class IntentRecognizer:
    """意图识别: 规则 + 关键词(生产环境会用小模型 + LLM)"""

    INTENT_KEYWORDS = {
        Intent.ACCOUNT_QUERY: ["账户", "余额", "资产", "我的钱", "持仓"],
        Intent.MARKET_QUERY: ["行情", "涨跌", "净值", "大盘", "走势"],
        Intent.PRODUCT_QUERY: ["产品", "基金", "理财", "保险", "存款"],
        Intent.INVESTMENT_ADVICE: ["建议", "推荐", "怎么配置", "买什么", "投什么"],
        Intent.COMPLAINT: ["投诉", "举报", "不满", "纠纷"],
    }

    @classmethod
    def recognize(cls, text: str) -> tuple:
        """返回 (intent, confidence)"""
        scores = {}
        for intent, kws in cls.INTENT_KEYWORDS.items():
            score = sum(1 for kw in kws if kw in text)
            scores[intent] = score
        best = max(scores, key=scores.get)
        total = sum(scores.values()) or 1
        confidence = scores[best] / total
        if confidence == 0:
            return Intent.OTHER, 0.0
        return best, round(confidence, 2)


# ============================================================
# 7. 金融 Agent 主体
# ============================================================

class FinanceAgent:
    """金融场景 Agent 主流程"""

    # 高风险意图需要人工复核
    HIGH_RISK_INTENTS = {Intent.INVESTMENT_ADVICE}

    def __init__(self):
        self.audit = AuditLogger()
        self.tools = {
            "query_account": Tool("query_account", "查询账户", FinanceTools.query_account),
            "query_market": Tool("query_market", "查询行情", FinanceTools.query_market),
            "query_product": Tool("query_product", "查询产品", FinanceTools.query_product),
            "calculate_portfolio": Tool(
                "calculate_portfolio", "资产配置", FinanceTools.calculate_portfolio,
                risk_level=RiskLevel.MEDIUM,
            ),
        }

    def chat(self, user_id: str, user_input: str, user_profile: dict) -> dict:
        """主入口: 处理用户请求"""
        session_id = str(uuid.uuid4())
        start_time = time.time()

        # 审计: 会话开始
        self.audit.log("session_start", {
            "user_id": user_id,
            "input": user_input,
        }, session_id)

        try:
            # Step 1: 意图识别
            intent, confidence = IntentRecognizer.recognize(user_input)
            self.audit.log("intent_recognized", {
                "intent": intent.value,
                "confidence": confidence,
            }, session_id)

            if confidence < 0.3:
                return self._fallback(session_id, user_id, "意图不明确,建议转人工")

            # Step 2: 风险检查
            amount = self._extract_amount(user_input)
            risk_result = RiskChecker.check(intent.value, amount, user_profile)
            self.audit.log("risk_checked", risk_result, session_id)

            # 高风险 → 直接转人工
            if risk_result["level"] == "high":
                return self._fallback(
                    session_id, user_id,
                    f"检测到高风险(原因: {risk_result['user_risk']['reasons']}),已转人工"
                )

            # Step 3: 工具调用 + 生成响应
            response = self._generate_response(
                intent, user_input, user_id, user_profile, risk_result
            )

            # Step 4: 合规审查
            compliance = ComplianceChecker.review(response["content"], intent.value)
            self.audit.log("compliance_review", compliance, session_id)

            if not compliance["passed"]:
                # 合规不通过 → 替换为安全响应
                response["content"] = (
                    "抱歉,该问题暂无法回答。投资有风险,过往业绩不代表未来。"
                    "如需详细建议,请联系人工投顾。"
                )
                response["compliance_blocked"] = True
                response["compliance_reason"] = compliance["reason"]

            # Step 5: 高风险意图人工复核
            need_human = (
                intent in self.HIGH_RISK_INTENTS
                or risk_result["level"] == "medium"
            )
            if need_human:
                response["need_human_review"] = True
                response["content"] += "\n\n[本建议仅供参考,请确认后操作]"

            # 审计: 最终输出
            elapsed = round(time.time() - start_time, 3)
            self.audit.log("response_sent", {
                "response": response,
                "elapsed_sec": elapsed,
            }, session_id)

            response["session_id"] = session_id
            response["elapsed_sec"] = elapsed
            return response

        except Exception as e:
            self.audit.log("error", {"error": str(e)}, session_id)
            return self._fallback(session_id, user_id, f"系统异常,已转人工: {e}")

    def _generate_response(self, intent: Intent, user_input: str,
                           user_id: str, user_profile: dict,
                           risk_result: dict) -> dict:
        """根据意图调用工具并生成响应(模拟 LLM 生成)"""
        if intent == Intent.ACCOUNT_QUERY:
            account = self.tools["query_account"].func(user_id)
            content = (
                f"您的账户信息如下:\n"
                f"- 姓名: {account['name']}\n"
                f"- 资产: {account['asset']}\n"
                f"- 信用评分: {account.get('credit_score', 'N/A')}\n"
                f"(敏感信息已脱敏)"
            )
            return {"content": content, "tools_used": ["query_account"]}

        elif intent == Intent.MARKET_QUERY:
            market = self.tools["query_market"].func("SH000300")
            content = (
                f"沪深300行情:\n"
                f"- 净值: {market['nav']}\n"
                f"- 日涨跌: {market['daily_change']}\n"
                f"投资有风险,过往业绩不代表未来。"
            )
            return {"content": content, "tools_used": ["query_market"]}

        elif intent == Intent.PRODUCT_QUERY:
            product = self.tools["query_product"].func("P001")
            content = (
                f"产品信息:\n"
                f"- 名称: {product['name']}\n"
                f"- 类型: {product['type']}\n"
                f"- 风险等级: {product['risk_level']}\n"
                f"- 历史收益: {product['historical_return']}\n"
                f"投资有风险,过往业绩不代表未来。"
            )
            return {"content": content, "tools_used": ["query_product"]}

        elif intent == Intent.INVESTMENT_ADVICE:
            amount = self._extract_amount(user_input)
            risk_level = user_profile.get("risk_tolerance", "C2")
            portfolio = self.tools["calculate_portfolio"].func(risk_level, amount)
            content = (
                f"基于您的风险等级 {risk_level},建议配置如下:\n"
                f"- 现金类: {portfolio['allocation']['cash']} 元\n"
                f"- 债券类: {portfolio['allocation']['bond']} 元\n"
                f"- 股票类: {portfolio['allocation']['stock']} 元\n"
                f"- 商品类: {portfolio['allocation']['commodity']} 元\n"
                f"投资有风险,过往业绩不代表未来。本建议仅供参考。"
            )
            return {"content": content, "tools_used": ["calculate_portfolio"]}

        elif intent == Intent.COMPLAINT:
            content = (
                "您的反馈已记录,将由人工客服跟进处理。"
                "投诉编号: " + str(uuid.uuid4())[:8]
            )
            return {"content": content, "tools_used": []}

        else:
            content = "抱歉,暂不支持此类问题,建议转人工。"
            return {"content": content, "tools_used": []}

    def _extract_amount(self, text: str) -> float:
        """从文本中提取金额(简化版)"""
        # 匹配"X 万" 或 "X 元"
        m = re.search(r"(\d+(?:\.\d+)?)\s*万", text)
        if m:
            return float(m.group(1)) * 10000
        m = re.search(r"(\d+(?:\.\d+)?)\s*元", text)
        if m:
            return float(m.group(1))
        return 0.0

    def _fallback(self, session_id: str, user_id: str, msg: str) -> dict:
        """兜底: 转人工"""
        self.audit.log("fallback_human", {"reason": msg}, session_id)
        return {
            "content": msg,
            "need_human_review": True,
            "session_id": session_id,
            "tools_used": [],
        }


# ============================================================
# 8. 测试运行
# ============================================================

def demo():
    """演示金融场景 Agent"""
    agent = FinanceAgent()

    # 模拟用户画像
    user_profile = {
        "user_id": "U001",
        "credit_score": 720,
        "violation_count": 0,
        "account_age_months": 24,
        "verified": True,
        "asset": 500000,
        "risk_tolerance": "C3",
        "recent_op_count": 2,
    }

    test_cases = [
        ("U001", "查一下我的账户余额", user_profile),
        ("U001", "沪深300今天行情怎么样", user_profile),
        ("U001", "帮我推荐一款稳健的理财产品", user_profile),
        ("U001", "我有 20 万,该怎么配置资产", user_profile),
        ("U001", "我要投诉你们的服务", user_profile),
        # 违规测试: 试图让 Agent 给具体买卖建议
        ("U001", "帮我看看明天买入 10000 元的股票能不能赚钱", user_profile),
    ]

    print("=" * 70)
    print("金融场景 Agent 演示")
    print("=" * 70)

    for user_id, user_input, profile in test_cases:
        print(f"\n[用户] {user_input}")
        result = agent.chat(user_id, user_input, profile)
        print(f"[Agent] {result['content']}")
        print(f"  意图: {result.get('intent', 'N/A')}")
        print(f"  工具: {result.get('tools_used', [])}")
        print(f"  需人工: {result.get('need_human_review', False)}")
        print(f"  耗时: {result.get('elapsed_sec', 0)}s")
        if result.get("compliance_blocked"):
            print(f"  [合规拦截] {result.get('compliance_reason')}")
        print("-" * 70)


if __name__ == "__main__":
    demo()
```

**运行结果(预期)**:

```
======================================================================
金融场景 Agent 演示
======================================================================

[用户] 查一下我的账户余额
[Agent] 您的账户信息如下:
- 姓名: 张**
- 资产: 10-100万
- 信用评分: N/A
(敏感信息已脱敏)
  工具: ['query_account']
  需人工: False
  耗时: 0.001s
----------------------------------------------------------------------

[用户] 我有 20 万,该怎么配置资产
[Agent] 基于您的风险等级 C3,建议配置如下:
- 现金类: 20000.0 元
- 债券类: 60000.0 元
- 股票类: 100000.0 元
- 商品类: 20000.0 元
投资有风险,过往业绩不代表未来。本建议仅供参考。

[本建议仅供参考,请确认后操作]
  需人工: True
  耗时: 0.002s
----------------------------------------------------------------------

[用户] 帮我看看明天买入 10000 元的股票能不能赚钱
[Agent] 抱歉,该问题暂无法回答。投资有风险,过往业绩不代表未来。如需详细建议,请联系人工投顾。
  需人工: True
  [合规拦截] 包含具体买卖点位建议(违规)
----------------------------------------------------------------------
```

**代码亮点(面试加分)**:

1. **审计日志哈希链**: 每条日志带前一条哈希,防篡改,满足金融监管可追溯要求。
2. **多层脱敏**: 身份证/手机/银行卡/金额分级脱敏,LLM 不接触原始数据。
3. **合规审查三重检查**: 违规词 + 风险提示 + 具体买卖点位检测。
4. **风险检查二维评估**: 用户风险 + 操作风险,取最大值,高风险强制转人工。
5. **多重兜底**: 高风险 → 转人工;合规不通过 → 安全响应替换;异常 → 转人工。
6. **可扩展工具**: Tool dataclass,新工具即插即用,带风险等级标记。
7. **意图置信度**: 低于阈值直接转人工,不强行答。

**面试官可能追问**:

- 如何扩展到真实 LLM? → 把 `_generate_response` 替换为 LLM 调用,工具调用走 Function Calling,合规审查作为输出过滤层。
- 审计日志如何防止内部篡改? → 哈希链 + WORM 存储 + 第三方审计。
- 如何处理 LLM 调用超时? → 熔断 + 降级到规则引擎 + 转人工。
- 如何做合规规则热更新? → 合规配置中心 + 监听推送 + 不重启生效。

</details>

---

### Q10 系统设计题: 设计美团/蚂蚁的智能客服中台,支持多业务线接入/统一知识库/人工协作/质量监控

<details>
<summary>展开答案</summary>

**题目背景**: 这是美团和蚂蚁都会考的"中台型"系统设计题,考察候选人对"平台化思维"的理解。智能客服中台要服务外卖、到店、支付、理财等多个业务线,既要复用又要隔离,是典型的中台架构难题。

**1. 需求澄清**

- **业务线**: 美团外卖、到店、酒旅、支付(蚂蚁)、财富(蚂蚁)、保险(蚂蚁)等 6+ 业务线。
- **接入渠道**: App、Web、电话、商家端、小程序。
- **日均会话**: 千万级,峰值 QPS 万级。
- **目标**: 自助解决率 60%+,单会话成本下降 50%,客服坐席效率提升 30%。
- **特殊要求**: 金融业务线(支付/财富/保险)需强合规审计,与本地生活业务线隔离。

**2. 整体架构(中台分层)**

```
┌──────────────────────────────────────────────────────────────┐
│  接入层(多渠道)                                              │
│  App / Web / 电话(ASR+TTS) / 商家端 / 小程序 / 开放 API      │
├──────────────────────────────────────────────────────────────┤
│  业务线网关(路由 + 隔离)                                     │
│  ├─ 业务线识别(从入口标记:U=外卖,T=到店,P=支付,W=财富)  │
│  ├─ 配额限流(按业务线)                                     │
│  └─ 数据隔离(业务线间数据不互通)                           │
├──────────────────────────────────────────────────────────────┤
│  中台核心层(统一能力)                                       │
│  ┌────────────┬────────────┬────────────┬────────────┐      │
│  │ 对话编排    │ 知识库      │ 人工协作    │ 质量监控    │      │
│  │ Orchestrator│ KB Service  │ Human Svc  │ Quality    │      │
│  └────────────┴────────────┴────────────┴────────────┘      │
├──────────────────────────────────────────────────────────────┤
│  Agent 执行层(业务线定制)                                   │
│  ├─ 外卖 Agent(订单/退款/骑手)                              │
│  ├─ 到店 Agent(券/核销/评价)                                │
│  ├─ 支付 Agent(账务/盗刷/退款)                              │
│  ├─ 财富 Agent(理财/持仓/市场)                              │
│  └─ 通用兜底 Agent                                           │
├──────────────────────────────────────────────────────────────┤
│  能力层(共享工具 + 业务线专属工具)                          │
│  ├─ 共享:工单系统、知识库 API、用户画像                     │
│  └─ 专属:订单系统(外卖)、支付系统(蚂蚁)、产品库(财富)│
├──────────────────────────────────────────────────────────────┤
│  保障层(中台统一)                                           │
│  ├─ 风控(防薅羊毛、防恶意)                                 │
│  ├─ 审计(全链路日志,金融业务线增强)                       │
│  ├─ 监控(分业务线指标)                                     │
│  └─ 灰度发布(按业务线 + 用户双维度)                        │
└──────────────────────────────────────────────────────────────┘
```

**3. 关键模块设计**

**(a) 对话编排层(Orchestrator)**

职责:统一管理对话流程,路由到对应业务线 Agent。

```
用户消息 → 渠道识别 → 业务线识别 → 意图识别
                                          ↓
                                    Agent 路由
                                    ├─ 单业务线 → 该业务线 Agent
                                    └─ 跨业务线 → 协调 Agent
                                          ↓
                                    上下文管理(分业务线 session)
                                          ↓
                                    响应生成 + 合规审查
                                          ↓
                                    质量打分 + 审计
```

**关键设计**:
- 业务线识别:从入口参数(渠道 + 业务标识)+ 意图识别双确认,防止跨业务线乱窜。
- 跨业务线场景:用户从外卖进入但问支付问题 → 协调 Agent 处理,不切换 session。
- 上下文隔离:每业务线独立 session,但用户级统一画像(画像中台)。

**(b) 统一知识库(KB Service)**

挑战:6+ 业务线,知识库内容差异大(外卖菜单 vs 理财产品),如何统一管理又业务线隔离?

方案:**分层知识库 + 业务线命名空间**。

```
统一知识库
├─ 通用层(平台规则、账号、安全)—— 所有业务线共享
├─ 业务线层
│  ├─ 外卖知识空间(菜单、商家、活动)
│  ├─ 到店知识空间(团购、券、核销)
│  ├─ 支付知识空间(账务、风控、退款)
│  ├─ 财富知识空间(产品、行情、规则)
│  └─ ...
└─ 个性化层(用户专属:订单、持仓)
```

**索引设计**:
- 向量索引:按业务线命名空间隔离( Milvus collection per business)。
- 关键词索引:ES 索引 + business_line 字段过滤。
- 召回时:通用层 + 业务线层 + 个性化层,三路融合。

**更新机制**:
- 通用层:中台团队维护,变更走评审。
- 业务线层:各业务线自助维护,API + 后台。
- 个性化层:实时拉取(订单 API、持仓 API)。

**质量治理**:
- 知识条目生命周期:创建 → 审核 → 发布 → 监控 → 下线。
- 自动化质检:定期 LLM 抽检知识条目准确性。
- 反馈闭环:用户点踩 → 自动标记 → 人工复核 → 更新。

**(c) 人工协作层(Human Service)**

职责:Agent 与坐席的协同,转人工策略与上下文传递。

转人工触发:
- 主动:用户要求、情绪激动、连续 2 轮未解决。
- 被动:高风险、低置信度、合规要求、VIP 用户。

转人工流程:
```
Agent 判断需转人工
  ↓
生成会话摘要(LLM,100 字以内)
  ↓
打包上下文(用户画像 + 订单/账户信息 + 对话历史 + Agent 初步判断)
  ↓
路由到对应业务线坐席组(技能组路由)
  ↓
坐席接手(携带上下文,秒级接手)
  ↓
坐席处理后,反馈给 Agent(用于训练优化)
```

坐席辅助:
- Agent 实时辅助:坐席对话时,Agent 后台推荐话术、知识、操作建议。
- 自动小结:会话结束后,Agent 自动生成工单小结。

**(d) 质量监控层(Quality)**

四层质检:

| 层级 | 时机 | 方式 | 目的 |
|------|------|------|------|
| 实时质检 | 对话中 | 规则 + 小模型 | 防违规话术、防误导 |
| 准实时质检 | 会话结束 5min | LLM 抽检 | 体验问题、解决率 |
| 离线抽检 | 每日 | 人工抽 5% | 质量基线、训练数据 |
| 专项质检 | 事件触发 | 人工 | 投诉、监管、复盘 |

指标体系:
- **业务指标**: 自助解决率、转人工率、二次进线率、CSAT、NPS。
- **质量指标**: 意图准确率、回答准确率、合规违规率、引用准确率。
- **效率指标**: 首响时间、平均处理时长、坐席并发数。
- **成本指标**: 单会话成本、LLM 调用成本、坐席成本。

**4. 多业务线隔离与复用**

| 维度 | 复用 | 隔离 |
|------|------|------|
| 对话编排 | 统一框架 | 业务线路由独立 |
| 知识库 | 通用层共享 | 业务线层命名空间 |
| 工具 | 共享工具(工单/画像) | 专属工具(订单/支付) |
| Agent | 通用兜底 Agent | 业务线专属 Agent |
| 数据 | 用户画像中台 | 业务线数据不互通 |
| 配置 | 中台统一配置 | 业务线业务规则 |
| 监控 | 统一监控平台 | 分业务线指标 |
| 灰度 | 中台统一能力 | 业务线独立灰度 |

**5. 金融业务线特殊处理**

支付/财富/保险业务线的增强:
- **强审计**: 全链路日志保留 5 年+,不可篡改。
- **强合规**: 话术审查、风险提示、持牌范围检查。
- **强风控**: 高风险操作强制人工 + 二次确认。
- **数据隔离**: 金融数据独立存储,不与非金融数据混。
- **降级预案**: LLM 异常时降级到规则引擎,而非转人工(保证可用性)。

**6. 灰度发布**

中台能力升级影响所有业务线,灰度策略:
- 维度 1:业务线(先非金融,后金融)。
- 维度 2:用户(按 user_id 哈希,1% → 5% → 50% → 100%)。
- 维度 3:地域(先小城市,后全国)。
- 监控:每阶段观察 24h,指标达标才进下一阶段。
- 回滚:任何阶段指标异常,1 键回滚。

**7. 容量与高可用**

- QPS:峰值万级,水平扩展(无状态服务 + 负载均衡)。
- LLM 调用:多供应商(自研 + 第三方),降级 + 限流。
- 知识库:多副本 + 缓存,P99 < 200ms。
- 数据库:分库分表(按业务线 + user_id)。
- 容灾:同城双活 + 异地灾备,金融业务线 RPO=0。

**8. 量化目标**

- 自助解决率:30% → 60%
- 转人工率:70% → 40%
- 单会话成本:1.5 元 → 0.6 元
- 坐席效率:提升 30%(辅助 + 自动小结)
- CSAT:85% → 90%
- 知识库召回 top-3 命中率:90%
- 合规违规率:0(红线)

**9. 难点与权衡**

- **复用 vs 隔离**: 中台核心能力复用,但业务线数据/配置隔离,通过命名空间 + 网关实现。
- **统一 vs 定制**: Agent 逻辑统一框架,但业务线深度定制,通过配置 + 插件机制。
- **金融 vs 非金融**: 金融业务线强合规,不能简单复用本地生活的话术/流程,需独立增强。
- **实时性 vs 准确性**: 实时质检规则保守(快速),离线质检 LLM 深度(准确),分层处理。
- **成本 vs 体验**: LLM 调用贵,简单问题用规则 + 小模型,复杂问题才上 LLM。

**10. 面试加分点**

- 主动提"中台不是大一统,而是共享 + 隔离的平衡"——显示架构认知。
- 主动提"金融业务线不能简单复用本地生活流程"——显示业务理解。
- 主动提"灰度先非金融后金融"——显示风险意识。
- 主动提"坐席辅助 + 自动小结"——显示对真实客服场景的理解。
- 主动提"知识库生命周期治理"——显示工程化深度。

</details>
