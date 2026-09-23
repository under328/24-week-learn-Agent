# Day 20 — 系统设计题专项

> **学习目标**: 掌握 AI Agent 系统设计的通用方法论,能够独立完成大厂面试中的白板系统设计题,覆盖需求分析、架构设计、容量估算、技术选型、容错降级、演进规划全链路。
>
> **面试定位**: 系统设计题是大厂高级/资深岗的核心区分题,通常 45-60 分钟。面试官不只看"画图能力",更考察**结构化思维、技术权衡、边界意识、演进思考**。Agent 方向的系统设计题与传统 CRUD 不同,核心难点在于:**LLM 的非确定性、Token 成本、长链路延迟、工具调用的可靠性、多轮上下文管理、多 Agent 协作的协调复杂度**。
>
> **今日投入**: 6-8 小时(每题 30-40 分钟思考 + 30 分钟对照答案复盘)。

---

## 今日知识图谱

```
AI Agent 系统设计核心组件
│
├── 1. 接入层 (Gateway)
│   ├── 多租户鉴权 / 配额限流
│   ├── 会话路由 (Sticky Session)
│   └── 协议适配 (HTTP / WebSocket / SSE / gRPC)
│
├── 2. 编排层 (Orchestration)
│   ├── Planner (任务分解 / ReAct / Plan-and-Execute)
│   ├── Executor (工具调度 / 并行编排)
│   ├── State Manager (短期记忆 / 长期记忆 / 检查点)
│   └── Memory (向量库 / KV / 关系库 / 上下文压缩)
│
├── 3. 能力层 (Capability)
│   ├── LLM Router (模型路由 / Fallback / 缓存)
│   ├── Tool Registry (注册中心 / Schema 校验 / 权限)
│   ├── RAG Pipeline (检索 / 重排 / 引用)
│   └── Skill Library (可复用技能包)
│
├── 4. 数据层 (Data)
│   ├── 对话存储 (时序 / 可回放)
│   ├── 知识库 (向量 + 全文 + 图谱)
│   ├── Trace 日志 (全链路可观测)
│   └── 评测集 (离线 + 在线)
│
├── 5. 可观测层 (Observability)
│   ├── Metrics (QPS / Token / 延迟 / 成本 / 成功率)
│   ├── Tracing (LangSmith / Arize / 自建 OTel)
│   ├── Logging (Prompt / Output / Tool Call)
│   └── Eval (在线 A/B + 离线回归)
│
├── 6. 容错层 (Resilience)
│   ├── 重试 / 降级 / 熔断
│   ├── 幂等 / 补偿 / Saga
│   ├── 预算控制 (Token 上限 / 费用熔断)
│   └── 人工接管 (Human-in-the-loop)
│
└── 7. 演进层 (Evolution)
    ├── 灰度发布 / 影子流量
    ├── 模型热替换 / Prompt 版本管理
    ├── 在线学习 / 反馈闭环
    └── 成本优化 (缓存 / 蒸馏 / 路由分层)
```

---

## 面试题

### Q1: Agent 系统设计通用框架 — 六步法

**题目**: 面试官让你"设计一个 XX Agent 系统",你应该按什么框架回答?请给出可复用的六步法,并说明每一步的关键产出和常见坑。

<details>
<summary>查看答案</summary>

#### 六步法总览

| 步骤 | 名称 | 时长建议 | 关键产出 |
|------|------|---------|---------|
| 1 | 需求分析 | 5-8 min | 功能性需求 + 非功能性需求 + 规模假设 |
| 2 | 容量估算 | 3-5 min | QPS / Token / 存储 / 成本 |
| 3 | 架构设计 | 10-15 min | 核心模块图 + 数据流 + 关键接口 |
| 4 | 模块拆解 | 8-10 min | 每个模块的职责、技术选型、关键算法 |
| 5 | 容错与演进 | 5-8 min | 降级 / 灰度 / 扩展性 |
| 6 | 权衡与总结 | 3-5 min | 方案优缺点 + 替代方案 + 演进路线 |

#### Step 1: 需求分析

**做法**: 先问澄清问题,再画"用例矩阵"。

关键问题清单:
- 用户画像是谁?B 端还是 C 端?
- 核心场景有哪几个?优先级?
- 响应是同步还是流式?
- 是否需要多轮?上下文窗口多长?
- 数据隐私 / 合规要求?
- SLA 要求(可用性 / 延迟 P99 / 准确率)?

**产出**: 一张功能需求表 + 一张非功能需求表。

**常见坑**:
- 不澄清就开始画图 → 方向跑偏
- 只列功能,忽略非功能(成本/延迟/安全)
- 把"AI 能做的"当需求,而非"用户要的"

#### Step 2: 容量估算

**做法**: 自顶向下估算,先 DAU 再 QPS 再 Token 再成本。

公式模板:
```
DAU = 100w
人均会话 = 5 次/天
会话平均轮数 = 10 轮
每轮 Token = 输入 2000 + 输出 500 = 2500
日总 Token = 100w * 5 * 10 * 2500 = 1.25e11 = 1250 亿 Token/天
峰值 QPS = 日均 QPS * 3 ≈ (100w*5*10 / 86400) * 3 ≈ 1740 QPS
日成本(按 $5/M input, $15/M output 粗算)≈ ...
```

**产出**: 一张容量估算表(QPS / Token / 存储 / 延迟 / 成本)。

**常见坑**:
- 忘记算峰值系数(通常 3-5x)
- 只算 LLM 成本,不算向量库/存储/带宽
- 不区分 input/output Token 价格

#### Step 3: 架构设计

**做法**: 画分层架构图,标明数据流方向。

通用分层(对应今日知识图谱):
```
Client → Gateway → Orchestrator(Planner/Executor/Memory) → LLM Router + Tool Registry + RAG
                                    ↓
                            Data Layer + Observability + Resilience
```

**产出**: 一张架构图 + 数据流时序 + 关键接口定义。

**常见坑**:
- 图太详细,看不清主线
- 缺少异步/流式链路
- 没有标注哪些是已有基础设施,哪些是新建

#### Step 4: 模块拆解

**做法**: 选 2-3 个核心模块深入讲,其余略过。

每个模块要讲清:
- **职责**: 做什么、不做什么
- **技术选型**: A vs B vs C,为什么选 X
- **关键算法/策略**: 如 Planner 用 ReAct 还是 Plan-and-Execute
- **接口**: 输入/输出 Schema

**常见坑**:
- 每个模块都讲一样深 → 时间不够
- 只讲"用什么",不讲"为什么"
- 忽略 LLM 调用的幂等与重试

#### Step 5: 容错与演进

**做法**: 列出 Top 3 故障场景 + 降级方案 + 未来 6 个月演进。

典型故障:
- LLM 厂商超时/限流 → Fallback 到次优模型 + 缓存
- 工具调用失败 → 重试 + 降级返回 + 人工兜底
- 知识库检索质量差 → Rerank + Query 改写 + Hybrid 检索

演进方向:
- v1: 单 Agent + RAG
- v2: 多 Agent 协作 + 工具市场
- v3: 自学习 + 个性化 + 成本优化

#### Step 6: 权衡与总结

**做法**: 主动指出方案缺点,给出替代方案,体现批判思维。

模板:
- 当前方案的 3 个优点
- 当前方案的 2 个缺点
- 如果重做会怎么改
- 6 个月演进路线

#### 通用话术(开场)

> "我先用 5 分钟澄清需求和规模,然后用 10 分钟画整体架构,再深入 2-3 个核心模块,最后讲容错和演进。如果时间紧张,您希望我重点讲哪部分?"

这句话能让面试官觉得你**有节奏感、可控场**。

</details>

---

### Q2: 设计一个 AI 编程助手 Agent(类似 Cursor/Copilot)

**题目**: 设计一个支持代码补全、重构、调试、测试生成的 AI 编程助手,服务百万级开发者。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- 代码补全(行级 / 块级 / 多文件)
- 自然语言改代码(重构 / 修 Bug / 加功能)
- 调试辅助(错误解释 / 修复建议)
- 测试生成(单测 / 集成测试)
- 代码库问答(基于全仓库上下文)

**非功能性需求**:
- 补全延迟 P99 < 300ms(行级)/ < 2s(块级)
- Chat 延迟首 Token < 800ms,流式输出
- 准确率:补全采纳率 > 30%,改代码任务成功率 > 70%
- 隐私:代码不出本地(企业版)/ 脱敏后上云(SaaS 版)
- 可用性 99.9%

#### 2. 容量估算

```
DAU = 100w 开发者
人均补全请求 = 200 次/天(编辑高频)
人均 Chat 请求 = 20 次/天
补全 QPS = 100w * 200 / 28800(8小时工作日) ≈ 7000 QPS,峰值 2w QPS
Chat QPS ≈ 700 QPS,峰值 2000 QPS
补全 Token 极小(输入 500 + 输出 50),走小模型
Chat Token 较大(输入 8k + 输出 1k),走大模型
日成本估算:补全 $2000 + Chat $5000 ≈ $7000/天
```

#### 3. 架构设计

```
IDE Plugin
   ↓ (LSP / 自定义协议)
Edge Gateway (鉴权 / 配额 / 路由)
   ↓
┌──────────────┬──────────────┐
│ 补全服务      │ Chat 服务     │
│ (小模型 FIM)  │ (大模型 Agent)│
└──────┬───────┴──────┬───────┘
       │              │
  Code Context    Agent Orchestrator
  (AST/检索)      (Planner + Tool)
       │              │
   本地索引库     ┌────┴────┬───────┐
                 RAG       LLM     Tool
              (仓库检索)  Router   (LSP/Shell/Git)
```

#### 4. 核心模块深入

**(1) 代码上下文构建(Context Builder)**

最核心的模块,决定补全质量。

策略(分层):
- **局部上下文**: 当前文件 + 光标前后 200 行
- **跨文件上下文**: 通过 AST 检索相关函数定义/调用
- **仓库级上下文**: 向量检索 + BM25 混合,召回 Top-K 相关片段
- **项目元信息**: 语言、框架、依赖、代码风格

关键技术:
- **Tree-sitter** 做增量 AST 解析
- **FIM (Fill-in-the-Middle)** 格式: `<prefix> <suffix> <middle>`,让模型理解光标位置
- **召回重排**: 向量召回 Top-50 → Cross-encoder 重排 Top-5
- **上下文压缩**: 保留签名 + 注释,丢弃实现细节

**(2) 补全服务(Completion)**

- 走 **小模型**(如 CodeLlama-7B / 自蒸馏模型),部署在 GPU 推理服务
- 用 **投机解码(Speculative Decoding)** 加速: 小模型草拟 + 大模型校验
- **缓存**: 相同 prefix 直接命中缓存(命中率 30%+)
- **拒绝策略**: 低置信度不返回,避免误导

**(3) Chat Agent**

Planner 策略: **ReAct + Plan-and-Execute 混合**
- 简单问答 → 单轮 RAG
- 改代码任务 → Plan(拆步骤)→ Execute(读/改/测)→ Verify(跑测试)

工具集:
- `read_file` / `search_code` / `run_tests` / `apply_diff` / `git_commit`

**(4) 仓库索引服务**

- 增量索引: 监听文件变更,只重算变更文件
- 索引粒度: 函数级 + 类级
- 索引存储: 本地 SQLite(SaaS) / 向量库(企业版)

#### 5. 容错与降级

| 故障 | 降级 |
|------|------|
| 大模型超时 | 降级到小模型 + 提示用户 |
| 仓库索引未就绪 | 只用局部上下文 |
| 测试运行失败 | 返回 diff 但不自动应用,人工确认 |
| Token 超限 | 上下文压缩 + 分段处理 |

#### 6. 演进路线

- v1: 单文件补全 + Chat
- v2: 跨文件上下文 + Agent 改代码
- v3: 多 Agent(写代码 + 审代码 + 测试)协作 + 个性化风格学习

#### 关键权衡

- **本地 vs 云端**: 本地隐私好但模型小;云端模型强但有合规风险 → 双模式
- **延迟 vs 质量**: 补全优先延迟,Chat 优先质量 → 分流不同模型
- **自动应用 vs 人工确认**: 自动应用体验好但有风险 → 改代码必须人工 confirm diff

</details>

---

### Q3: 设计一个智能客服系统

**题目**: 设计一个支持多轮对话、知识库检索、工单创建、人工转接、质量评估的智能客服系统,日咨询量百万级。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- 多轮对话(澄清意图 / 追问信息)
- 知识库检索(FAQ / 产品文档 / 历史工单)
- 工单创建与流转
- 人工转接(带上下文交接)
- 质量评估(满意度 / 解决率 / 合规)

**非功能性需求**:
- 首响 < 1s,首 Token < 800ms
- 自助解决率 > 60%
- 转人工率 < 30%
- 7x24 可用
- 合规:对话留存、敏感词过滤、可审计

#### 2. 容量估算

```
日咨询量 = 100w 会话
平均轮数 = 6 轮
每轮 Token = 输入 1500 + 输出 300
日 Token = 100w * 6 * 1800 = 1.08e10 ≈ 108 亿/天
QPS 峰值 = (100w / 86400) * 3 ≈ 35 QPS(看起来不高,但并发会话数高)
同时在线会话 = 1w-5w
```

#### 3. 架构设计

```
用户端(Web/APP/小程序)
   ↓
统一接入网关 (会话路由 / 限流 / 鉴权)
   ↓
对话编排器 (Orchestrator)
   ├─ 意图识别 (Router: FAQ / 业务办理 / 转人工)
   ├─ RAG 检索 (知识库 + 历史工单)
   ├─ LLM 生成 (带引用)
   ├─ 工具调用 (查订单 / 退款 / 建工单)
   └─ 转人工决策 (情绪 / 复杂度 / 用户等级)
   ↓
┌────────┬────────┬────────┐
坐席工作台  工单系统   质检系统
└────────┴────────┴────────┘
   ↓
数据层: 对话日志 / 知识库 / 向量库 / 质检结果
```

#### 4. 核心模块深入

**(1) 意图路由(Intent Router)**

不是所有 query 都走 LLM,要做分层:
- **FAQ 精确匹配**: 向量 + 关键词 → 命中直接返回(60% 流量)
- **业务办理**: 走 Agent + 工具(查/改/退)
- **闲聊/复杂咨询**: 走 LLM + RAG
- **转人工**: 情绪检测 + 复杂度评分超阈值

技术: 小模型分类器(BERT 微调)+ 规则引擎兜底

**(2) RAG Pipeline**

知识库分层:
- **L1 公告/FAQ**: 高频标准问题,精确召回
- **L2 产品文档**: 向量检索 + Rerank
- **L3 历史工单**: 相似工单检索(用户相似 + 问题相似)

优化点:
- **Query 改写**: 多轮对话中,把"那个怎么办"改写为完整 query
- **Hybrid 检索**: 向量 + BM25 + 元数据过滤
- **引用标注**: 每句话标来源,便于质检和可信度
- **缓存**: 高频问题答案缓存(命中率 40%+)

**(3) 转人工策略**

触发条件(任一满足):
- 情绪检测: 负面情绪强度 > 0.7
- 复杂度: Agent 连续 3 轮未解决
- 用户主动要求
- VIP 用户 + 业务敏感
- 敏感词命中(投诉/法律)

交接内容:
- 对话摘要(自动生成)
- 用户画像 + 历史工单
- 已尝试方案 + 卡点
- 推荐处理建议

**(4) 质量评估**

三层质检:
- **实时**: 敏感词 / 合规规则 / 幻觉检测(引用核对)
- **离线全量**: 满意度 / 解决率 / 转人工率 / 平均轮数
- **抽检**: 人工抽 5% 打分(准确性 / 态度 / 合规)

#### 5. 容错与降级

| 场景 | 降级 |
|------|------|
| LLM 不可用 | 降级到 FAQ 模板回复 + 直接转人工 |
| 知识库检索失败 | 提示"信息查询中"+ 转人工 |
| 工具调用失败 | 建工单 + 告知 SLA |
| 流量洪峰 | 排队 + 预计等待时间 |

#### 6. 演进路线

- v1: 单轮 FAQ + 关键词路由
- v2: 多轮 LLM + RAG + 转人工
- v3: Agent 主动外呼(满意度回访 / 预警)
- v4: 个性化(基于历史) + 预测式服务

#### 关键权衡

- **解决率 vs 成本**: 全走大模型质量好但贵 → 分层路由
- **自动化 vs 体验**: 强行自助会激怒用户 → 设转人工兜底
- **通用 vs 垂直**: 通用模型灵活但易幻觉 → 业务知识微调 + 强 RAG

</details>

---

### Q4: 设计一个 AI 数据分析 Agent

**题目**: 设计一个支持自然语言查询、SQL 生成、图表生成、洞察发现的 AI 数据分析 Agent,服务企业内部数据团队。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- 自然语言转 SQL(Text-to-SQL)
- 自动图表选型与生成
- 异常检测与洞察发现
- 多轮追问(下钻 / 对比 / 预测)
- 报告导出(PPT / Excel / 邮件订阅)

**非功能性需求**:
- 查询准确率 > 85%(可执行 + 结果正确)
- 端到端延迟 < 10s(简单查询)/ < 30s(复杂分析)
- 数据安全:行级权限 / 列脱敏 / SQL 注入防护
- 可解释:每条 SQL 可追溯,每个洞察有依据

#### 2. 容量估算

```
日活分析师 = 5000
人均查询 = 20 次/天
日查询 = 10w 次
QPS 峰值 = 10w / 28800 * 3 ≈ 10 QPS(低 QPS,高复杂度)
单次 Token = 输入 5k(Schema + 样例)+ 输出 1k(SQL + 解释)= 6k
日 Token = 10w * 6k = 6 亿/天
存储:查询历史 + 结果缓存,日增 10GB
```

#### 3. 架构设计

```
用户(分析师)
   ↓
对话网关 (鉴权 / 权限上下文)
   ↓
Analysis Agent (Orchestrator)
   ├─ Query 理解 (意图 / 范围 / 时间)
   ├─ Schema 检索 (相关表/字段召回)
   ├─ SQL 生成 (Few-shot + 微调模型)
   ├─ SQL 校验 (语法 / 权限 / 注入)
   ├─ 执行引擎 (SQL → 数仓)
   ├─ 可视化 (图表选型 + 渲染)
   └─ 洞察生成 (异常 / 趋势 / 对比)
   ↓
数据层: 数仓 / 元数据 / 查询缓存 / 报告库
```

#### 4. 核心模块深入

**(1) Schema 检索(Metadata Retrieval)**

Text-to-SQL 的最大难点是 Schema 太大,不能全塞进 Prompt。

策略:
- **Schema 向量化**: 表名 / 字段名 / 注释 → Embedding,检索 Top-K 相关表
- **Schema 图谱**: 表关系(外键/JOIN 路径),用图检索扩展关联表
- **Few-shot 召回**: 历史相似问题 + 对应 SQL,作为 in-context 示例
- **Schema 摘要**: 大表只给字段名 + 注释,不给全量数据

**(2) SQL 生成与校验**

生成策略: **多候选 + 投票**
- 一次生成 3-5 个 SQL 候选
- 用执行计划 + 自一致性(结果一致)投票
- 选最优 + 解释

校验链(必做):
- **语法校验**: SQL Parser
- **权限校验**: 表级 / 行级权限过滤
- **注入防护**: 白名单 + AST 分析,禁止 DDL/DML
- **成本预估**: 扫描行数超阈值 → 提示加条件或拒绝
- **Dry-run**: EXPLAIN 验证可执行

**(3) 可视化自动选型**

规则 + LLM 混合:
- 规则: 时序 → 折线,占比 → 饼图,对比 → 柱状,分布 → 直方图
- LLM: 复杂场景(多维 / 组合)由 LLM 选型 + 配置坐标轴
- 输出 ECharts/Vega-Lite 配置 JSON

**(4) 洞察发现**

三类洞察:
- **异常**: 同比/环比突变 > 阈值,3-sigma 异常点
- **趋势**: 上升/下降/周期性
- **对比**: 维度间差异 Top-N

技术: 统计规则预筛 → LLM 生成自然语言解读(带数字 + 原因假设)

#### 5. 容错与降级

| 故障 | 降级 |
|------|------|
| SQL 执行超时 | 提示加过滤条件 / 降级采样 |
| 数仓不可用 | 返回缓存结果 + 标注时效 |
| 模型生成错误 SQL | 多候选 + 人工确认模式 |
| 敏感数据误查 | 权限拦截 + 审计告警 |

#### 6. 演进路线

- v1: 单表 Text-to-SQL + 固定图表
- v2: 多表 JOIN + 自动可视化 + 洞察
- v3: 主动洞察(订阅推送) + 归因分析 + 预测
- v4: 自然语言建模(Semantic Layer) + 增量学习

#### 关键权衡

- **准确率 vs 灵活性**: 强约束模板准确但僵硬;纯 LLM 灵活但易错 → 混合
- **自助 vs 审核**: 自动执行快但有风险 → 默认审核模式,白名单用户可直执行
- **通用 vs 垂直**: 通用 Schema 难覆盖业务语义 → 建语义层(Business Glossary)

</details>

---

### Q5: 设计一个自动化运营 Agent

**题目**: 设计一个支持内容生成、多平台发布、数据监控、策略调整的自动化运营 Agent,服务自媒体团队。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- 内容生成(图文 / 短文 / 标题 / 封面)
- 多平台发布(公众号 / 抖音 / 小红书 / 微博,适配格式)
- 数据监控(阅读 / 互动 / 涨粉 / 转化)
- 策略调整(选题优化 / 发布时间 / 风格迭代)
- 竞品监控

**非功能性需求**:
- 日产出 50-100 篇内容
- 发布成功率 > 99%
- 内容原创度 > 80%(查重)
- 人工干预率 < 20%
- 合规:平台规则 / 广告法 / 敏感内容

#### 2. 容量估算

```
日内容量 = 100 篇
每篇 Token = 生成 5k + 改写适配 2k * 4 平台 = 13k
日 Token = 100 * 13k = 130w/天
QPS 不高,但单任务链路长(10-20 步)
存储:内容库 + 素材库 + 数据库,日增 1GB
```

#### 3. 架构设计

```
运营人员(目标设定 / 审核)
   ↓
策略中心 (选题 / 排期 / 目标)
   ↓
Content Agent Pipeline
   ├─ 选题 Agent (热点 + 竞品 + 历史)
   ├─ 素材 Agent (检索 / 生成图片)
   ├─ 撰写 Agent (大纲 → 正文 → 标题)
   ├─ 合规审核 (敏感词 / 原创度 / 平台规则)
   ├─ 适配 Agent (多平台改写 / 封面)
   ├─ 发布 Agent (定时 / API 对接)
   └─ 数据 Agent (回收 / 分析 / 归因)
   ↓
反馈闭环 → 策略中心
```

#### 4. 核心模块深入

**(1) 选题 Agent**

输入: 账号定位 + 历史表现 + 热点 + 竞品
输出: 选题清单(含预期 CTR / 难度 / 相关度)

策略:
- **热点抓取**: 微博热搜 / 抖音热榜 / 百度指数 API
- **竞品监控**: RSS / 爬虫,抽取高互动内容
- **历史归因**: 哪类选题效果好(主题 / 形式 / 时间)
- **LLM 打分**: 相关性 + 时效性 + 差异化

**(2) 撰写 Agent(多步链路)**

不要一步生成全文,要拆步骤:
1. 生成大纲(3-5 个要点)
2. 逐段扩写
3. 生成标题(5 选 1)
4. 润色 + 风格统一
5. 配图建议

每步可人工介入调整。

**(3) 多平台适配**

| 平台 | 适配点 |
|------|--------|
| 公众号 | 长文 + 排版 + 封面 2.35:1 |
| 小红书 | 短文 + emoji + 9 图 + 标签 |
| 抖音 | 脚本 + 分镜 + 口播文案 |
| 微博 | 140 字 + 话题 + 配图 |

技术: 每平台一个适配 Prompt 模板 + 后处理(字数/格式/标签)

**(4) 数据反馈闭环**

关键指标:
- 曝光 → 阅读率(标题/封面决定)
- 阅读 → 互动率(内容质量决定)
- 互动 → 转化率(CTA 决定)

策略调整:
- 标题 CTR 低 → A/B 测试 + LLM 复盘
- 发布时间差 → 按粉丝活跃时段排期
- 选题效果差 → 调整选题池权重

#### 5. 容错与降级

| 场景 | 降级 |
|------|------|
| 平台 API 限流 | 排队重试 + 切备用账号 |
| 生成内容违规 | 敏感词过滤 + 人工审核 |
| 数据回收失败 | 缓存最后数据 + 标注 |
| 模型超时 | 降级到模板化内容 |

#### 6. 演进路线

- v1: 单平台 + 人工选题 + AI 撰写
- v2: 多平台 + 自动选题 + 数据闭环
- v3: 主动学习(粉丝画像)+ 风格个性化
- v4: 多 Agent 协作(策划/文案/设计/运营)

#### 关键权衡

- **自动化 vs 质量**: 全自动快但同质化 → 关键环节人工卡点
- **数量 vs 精品**: 高频发文有流量但伤号 → 平衡 80% 量 + 20% 精品
- **通用模型 vs 微调**: 通用灵活但风格不稳 → 用历史优质内容微调

</details>

---

### Q6: 设计一个 AI 代码审查 Agent

**题目**: 设计一个支持 PR 分析、缺陷检测、安全扫描、建议生成的 AI 代码审查 Agent,集成到企业研发流程。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- PR 自动分析(变更摘要 / 影响范围)
- 缺陷检测(逻辑 / 边界 / 性能 / 并发)
- 安全扫描(注入 / 越权 / 密钥泄露)
- 修复建议(带代码 diff)
- 复审提醒(复杂变更 / 关键模块)
- 评审报告生成

**非功能性需求**:
- 审查延迟 < 3min(PR < 1000 行)
- 误报率 < 15%
- 漏报率 < 5%(关键缺陷)
- 集成 GitLab/GitHub/CodeHub
- 不阻断流程(异步评审 + 评论)

#### 2. 容量估算

```
日 PR 数 = 5000(中型企业)
平均变更 = 300 行
审查 Token = 输入 10k(代码 + 上下文)+ 输出 2k = 12k
日 Token = 5000 * 12k = 6000w/天
并发审查 = 50-200
存储: 审查报告 + 历史记录,日增 5GB
```

#### 3. 架构设计

```
CodeHub Webhook (PR 事件)
   ↓
事件网关 (去重 / 限流 / 队列)
   ↓
Review Agent Pipeline
   ├─ Diff 解析 (变更文件 / 影响范围)
   ├─ 上下文构建 (依赖 / 调用链 / 历史)
   ├─ 多维度检查
   │   ├─ 规则引擎 (静态规则 / SonarQube)
   │   ├─ 安全扫描 (Semgrep / 自研)
   │   └─ LLM 审查 (逻辑 / 设计 / 可维护性)
   ├─ 建议生成 (代码 diff + 解释)
   ├─ 优先级排序 (Critical/High/Medium/Low)
   └─ 报告输出 (PR 评论 / 工单 / 仪表盘)
   ↓
反馈闭环: 开发者修复 → 复审 → 通过
```

#### 4. 核心模块深入

**(1) 上下文构建**

只看 diff 不够,要构建"变更影响面":
- **调用链分析**: 谁调用了变更函数(影响面)
- **依赖分析**: 变更依赖哪些模块(回归范围)
- **历史 PR**: 同文件近期变更(冲突检测)
- **代码库规范**: 团队编码规范 / 架构约束

技术: CodeGraph(代码图谱)+ Tree-sitter AST

**(2) 多维度检查策略**

分层检查,避免 LLM 过载:
- **L1 规则引擎**: 静态规则(命名 / 圈复杂度 / 空指针),毫秒级,覆盖 70% 问题
- **L2 安全扫描**: Semgrep + 密钥扫描 + 依赖漏洞
- **L3 LLM 深审**: 逻辑正确性 / 边界 / 并发 / 设计合理性

LLM 审查 Prompt 结构:
```
[角色] 你是资深代码审查专家
[规范] <团队编码规范>
[变更] <diff 内容>
[上下文] <相关函数定义 + 调用方>
[任务] 找出: 1)逻辑缺陷 2)边界问题 3)性能风险 4)可维护性
[输出] JSON: [{severity, category, line, issue, suggestion, fixed_code}]
```

**(3) 建议生成**

不只是"指出问题",要给"可应用的 diff":
- 生成修复代码
- 用 `git apply` 格式输出
- 标注 confidence,低置信度只评论不建议改

**(4) 反馈闭环与学习**

- 开发者对建议的采纳/拒绝 → 训练数据
- 误报标记 → 规则优化
- 高频问题 → 沉淀为新规则

#### 5. 容错与降级

| 故障 | 降级 |
|------|------|
| LLM 超时 | 只返回规则引擎结果 |
| 代码库过大 | 分片审查 + 聚合 |
| 误报过多 | 置信度阈值动态调整 |
| 阻塞 PR | 默认非阻断,仅评论 |

#### 6. 演进路线

- v1: 规则引擎 + LLM 评论
- v2: 自动修复 diff + 影响面分析
- v3: 多 Agent(安全/性能/架构专家)+ 历史学习
- v4: 预防式(提交前实时提示)

#### 关键权衡

- **阻断 vs 非阻断**: 阻断质量高但伤效率 → 默认非阻断,仅 Critical 阻断
- **规则 vs LLM**: 规则准确但僵硬;LLM 灵活但慢且贵 → 分层
- **全量 vs 采样**: 全量覆盖好但成本高 → 大文件采样 + 关键路径全量

</details>

---

### Q7: 设计一个 Multi-Agent 协作的软件研发平台

**题目**: 设计一个 Multi-Agent 协作的软件研发平台,覆盖需求分析、架构设计、编码、测试、部署全流程。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- 需求分析 Agent(需求拆解 / 验收标准 / Story 生成)
- 架构设计 Agent(技术选型 / 模块设计 / 接口定义)
- 编码 Agent(多文件 / 多语言 / Git 操作)
- 测试 Agent(单测 / 集成 / E2E 生成与执行)
- 部署 Agent(CI/CD / 灰度 / 回滚)
- 项目经理 Agent(协调 / 卡点 / 风险)

**非功能性需求**:
- 端到端交付一个中等功能 < 4 小时
- 人工介入点 < 5 个
- 测试覆盖率 > 70%
- 部署成功率 > 95%

#### 2. 架构设计

```
用户(产品经理 / Tech Lead)
   ↓
PM Agent (任务分解 / 协调 / 状态管理)
   ↓
┌─────────────────────────────────────┐
│       Multi-Agent 协作总线           │
│  (消息队列 + 状态机 + 工作流引擎)      │
└──┬──────┬──────┬──────┬──────┬─────┘
   ↓      ↓      ↓      ↓      ↓
需求     架构    编码    测试    部署
Agent    Agent   Agent   Agent   Agent
   │      │      │      │      │
   └──────┴──┬───┴──────┴──────┘
             ↓
      共享工作空间
   (代码 / 文档 / 任务 / 制品)
             ↓
      人工卡点(关键决策)
```

#### 3. 核心模块深入

**(1) PM Agent(协调者)**

职责:
- 把需求拆成子任务,分配给专业 Agent
- 监控进度,处理卡点
- 决定何时需人工介入
- 汇总产出,生成交付报告

实现: **Plan-and-Execute** 范式
- Plan: 生成 DAG 任务图(依赖关系)
- Execute: 按拓扑序调度,并行 + 串行混合
- Monitor: 超时 / 失败 / 质量不达标 → 重试或升级

**(2) 协作总线**

这是 Multi-Agent 的核心难点。

设计要点:
- **消息协议**: 标准化消息格式(发送方 / 接收方 / 类型 / 内容 / 引用)
- **状态机**: 每个任务有明确状态(pending/running/blocked/done/failed)
- **工作流引擎**: 用 Temporal / Airflow 管理长链路,支持补偿
- **共享黑板(Blackboard)**: 所有 Agent 读写共享上下文(代码 / 决策 / 文档)

**(3) 专业 Agent 设计**

| Agent | 输入 | 输出 | 关键工具 |
|-------|------|------|---------|
| 需求 | PRD | Story + 验收标准 | 文档解析 / 模板 |
| 架构 | Story + 现有系统 | 架构图 + 接口 | CodeGraph / 模板库 |
| 编码 | 架构 + Story | 代码 + PR | Git / LSP / 编译器 |
| 测试 | 代码 + Story | 测试用例 + 报告 | 测试框架 / 覆盖率工具 |
| 部署 | 制品 + 配置 | 部署结果 | CI/CD / K8s |

**(4) 冲突与对齐**

多 Agent 会产出冲突(架构说 A,编码做 B):
- **协议层**: 每个 Agent 产出必须带"理由 + 依据"
- **仲裁者**: PM Agent 检测冲突,触发对齐会议(再调一次 LLM 协调)
- **版本化**: 所有决策可追溯,可回滚

**(5) 人工卡点(Human-in-the-loop)**

关键决策必须人工确认:
- 架构方案确定前
- PR 合并前
- 生产部署前
- 需求变更时

技术: 工作流引擎的 `pause` + 通知 + 审批 UI

#### 4. 容错与降级

| 故障 | 降级 |
|------|------|
| 单个 Agent 失败 | 重试 3 次 → 升级人工 |
| Agent 间死锁 | PM 超时检测 → 强制推进 |
| 代码质量不达标 | 测试 Agent 拒绝 → 编码 Agent 重做 |
| 部署失败 | 自动回滚 + 告警 |

#### 5. 演进路线

- v1: 单流程串行(需求→编码→测试),人工衔接
- v2: PM Agent 协调 + 并行 + 人工卡点
- v3: 多 Agent 自适应(失败学习)+ 跨项目知识复用
- v4: 自演化(代码库自我重构 / 技术债清理)

#### 关键权衡

- **自主 vs 可控**: 全自主快但风险大 → 关键节点人工卡点
- **串行 vs 并行**: 并行快但冲突多 → DAG + 仲裁
- **通用 vs 领域**: 通用灵活但质量不稳 → 垂直场景微调 + 强约束

#### Multi-Agent 系统的通用陷阱(面试加分点)

1. **过度协作**: Agent 间消息爆炸,Token 浪费 → 限制消息轮数
2. **责任不清**: 出错不知谁的问题 → 每步带 Agent 签名
3. **上下文丢失**: 长链路信息衰减 → 共享黑板 + 摘要传递
4. **死锁/活锁**: 互相等待 → 超时 + 强制仲裁
5. **评估困难**: 端到端指标难定义 → 分层评测 + 人工抽检

</details>

---

### Q8: Agent 系统设计的容量估算

**题目**: 给定一个 Agent 系统(DAU 50w,人均 10 次会话,每次 8 轮),请估算 QPS、Token 消耗、延迟、存储、成本,并给出优化建议。

<details>
<summary>查看答案</summary>

#### 1. 基础数据假设

| 指标 | 假设值 |
|------|--------|
| DAU | 50w |
| 人均会话/天 | 10 |
| 每会话轮数 | 8 |
| 每轮输入 Token | 2000(含上下文累积) |
| 每轮输出 Token | 400 |
| 工具调用次数/轮 | 1.5 |
| 知识库检索/轮 | 1 |
| 活跃时段 | 12 小时 |
| 峰值系数 | 3x |

#### 2. QPS 估算

```
日总会话 = 50w * 10 = 500w
日总轮数 = 500w * 8 = 4000w
日总请求 = 4000w * (1 LLM + 1.5 工具 + 1 检索) = 1.4 亿次
平均 QPS = 1.4e8 / (12 * 3600) ≈ 3240 QPS
峰值 QPS = 3240 * 3 ≈ 9720 QPS

分项:
- LLM QPS 峰值 ≈ 930
- 工具调用 QPS 峰值 ≈ 1400
- 检索 QPS 峰值 ≈ 930
```

#### 3. Token 消耗

```
日输入 Token = 4000w * 2000 = 800 亿
日输出 Token = 4000w * 400 = 160 亿
日总 Token = 960 亿

注意: 多轮上下文累积,第 N 轮输入 ≈ N * 单轮新增 + 系统提示
更精确: 假设单轮新增 300 Token,系统提示 500
第 N 轮输入 = 500 + 300 * N + 400 * (N-1) [历史输出累积]
8 轮总输入 = Σ(500 + 300n + 400(n-1)) for n=1..8 ≈ 1.5w Token/会话
日总输入 = 500w * 1.5w = 7500 亿(累积算法)

→ 提示: 上下文管理极其重要!用摘要/压缩可降 50%+
```

#### 4. 延迟估算

```
单轮端到端延迟构成:
- 网关 + 路由: 50ms
- 检索(向量库): 100-200ms
- LLM 首 Token: 500-1000ms
- LLM 流式输出: 400 Token * 30ms/Token = 12s
- 工具调用: 200-2000ms(看具体工具)
- 总计: P50 ≈ 2s 首响, 15s 完整;P99 ≈ 5s 首响, 30s 完整

优化点:
- 流式输出 → 用户感知延迟降到首 Token
- 工具并行 → 工具延迟取 max 而非 sum
- 检索预取 → 隐藏检索延迟
```

#### 5. 存储估算

```
对话日志: 500w 会话 * 8 轮 * 2KB(含元数据)= 80GB/天
向量库: 知识库 1M 文档 * 2KB 向量 ≈ 2GB(不大,但索引开销 3-5x)
Trace 日志: 1.4 亿次 * 5KB = 700GB/天(可采样 10% → 70GB)
评测数据: 日增 1GB
合计: 日增约 150-200GB,月增 5-6TB

→ Trace 日志是大头,需采样 + 分级保留(热 7 天,温 30 天,冷 1 年)
```

#### 6. 成本估算

```
LLM 成本(按 GPT-4 级别定价):
- Input: 7500 亿 * $5/M = $3750/天
- Output: 160 亿 * $15/M = $240/天
- 小计: ~$4000/天 = $12w/月

向量库: 自建 ≈ $5000/月
存储: $2000/月
带宽: $1000/月
GPU 推理(小模型): $1w/月
合计: ~$14w/月 ≈ $170w/年

→ LLM 成本占 85%,优化 LLM 是核心
```

#### 7. 成本优化建议(面试加分)

| 优化手段 | 预期收益 |
|---------|---------|
| 模型分层路由(简单走小模型) | -40% |
| Prompt 缓存(命中 30%) | -15% |
| 上下文压缩(摘要/裁剪) | -20% |
| 批处理(离线任务用 Batch API) | -50% |
| 自蒸馏小模型替代部分场景 | -30% |
| 长上下文用 KV Cache 复用 | -10% |

组合优化后,预计可降到 $5-7w/月。

#### 8. 容量规划建议

```
LLM 推理: 多厂商接入,主备 + 负载均衡
向量库: 分片 + 副本,QPS 1w+ 用 Milvus 集群
网关: 水平扩展,K8s HPA 按 QPS 自动伸缩
对话存储: 时序数据库(InfluxDB/TDengine)+ 冷热分层
监控: Prometheus + Grafana,关键指标: QPS/Token/延迟/成本/成功率
```

#### 容量估算速记公式

```
日 Token = DAU × 会话/人 × 轮/会话 × (输入 + 输出)
峰值 QPS = (日请求 / 活跃秒数) × 峰值系数
LLM 月成本 ≈ (日 Token / 1e6) × 单价 × 30
存储日增 = 会话数 × 轮数 × 单轮大小 + Trace 采样后大小
```

</details>

---

### Q9: 手撕代码题 — 实现通用 Agent 系统框架骨架

**题目**: 用 Python 实现一个通用的 Agent 系统框架骨架,需包含:任务调度、工具注册、状态管理、监控、容错。代码要完整可运行。

<details>
<summary>查看答案</summary>

下面是一个完整的、可运行的 Agent 框架骨架,涵盖面试要求的五大模块。

```python
"""
通用 Agent 系统框架骨架
包含: 任务调度 / 工具注册 / 状态管理 / 监控 / 容错
"""
import asyncio
import json
import time
import uuid
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from collections import defaultdict

# ============================================================
# 1. 状态管理 (State Management)
# ============================================================

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_TOOL = "awaiting_tool"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class TaskState:
    """单个任务的状态"""
    task_id: str
    input: str
    status: TaskStatus = TaskStatus.PENDING
    steps: list = field(default_factory=list)       # 执行步骤记录
    tool_calls: list = field(default_factory=list)  # 工具调用历史
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    context: dict = field(default_factory=dict)     # 上下文(对话历史/中间结果)

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.updated_at = time.time()

class StateManager:
    """全局状态管理器: 存储所有任务状态,支持查询/恢复"""

    def __init__(self):
        self._states: dict[str, TaskState] = {}
        self._checkpoints: dict[str, list] = defaultdict(list)  # 检查点(用于恢复)

    def create(self, task_input: str) -> TaskState:
        task_id = str(uuid.uuid4())[:8]
        state = TaskState(task_id=task_id, input=task_input)
        self._states[task_id] = state
        return state

    def get(self, task_id: str) -> Optional[TaskState]:
        return self._states.get(task_id)

    def checkpoint(self, task_id: str):
        """保存检查点(深拷贝关键状态)"""
        state = self.get(task_id)
        if state:
            snapshot = {
                "status": state.status,
                "steps": state.steps.copy(),
                "context": json.dumps(state.context, default=str),
                "retry_count": state.retry_count,
            }
            self._checkpoints[task_id].append(snap_shot)

    def restore(self, task_id: str) -> bool:
        """从最近检查点恢复"""
        cps = self._checkpoints.get(task_id, [])
        if not cps:
            return False
        snap = cps[-1]
        state = self.get(task_id)
        if state:
            state.status = TaskStatus(snap["status"])
            state.steps = snap["steps"]
            state.context = json.loads(snap["context"])
            return True
        return False

# ============================================================
# 2. 工具注册 (Tool Registry)
# ============================================================

@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict          # JSON Schema
    handler: Callable
    timeout: float = 10.0
    retryable: bool = True

class ToolRegistry:
    """工具注册中心: 注册/校验/调用工具"""

    def __init__(self):
        self._tools: dict[str, ToolSchema] = {}

    def register(self, tool: ToolSchema):
        # 校验 schema 合法性
        if not tool.parameters.get("type") == "object":
            raise ValueError(f"Tool {tool.name} parameters must be object schema")
        self._tools[tool.name] = tool
        logging.info(f"Tool registered: {tool.name}")

    def unregister(self, name: str):
        self._tools.pop(name, None)

    def list_tools(self) -> list[dict]:
        """返回 OpenAI function-calling 格式的工具描述"""
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def get(self, name: str) -> Optional[ToolSchema]:
        return self._tools.get(name)

    def validate_args(self, tool: ToolSchema, args: dict) -> bool:
        """简易参数校验(生产用 jsonschema 库)"""
        required = tool.parameters.get("required", [])
        return all(r in args for r in required)

# ============================================================
# 3. 监控 (Monitoring)
# ============================================================

@dataclass
class Metric:
    task_id: str
    metric_name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: dict = field(default_factory=dict)

class Monitor:
    """监控: 指标采集 + 告警 + Trace"""

    def __init__(self):
        self._metrics: list[Metric] = []
        self._traces: dict[str, list] = defaultdict(list)
        self._alerts: list[dict] = []
        self._counters = defaultdict(int)
        self._latencies = defaultdict(list)

    def record(self, task_id: str, name: str, value: float, tags: dict = None):
        m = Metric(task_id=task_id, metric_name=name, value=value, tags=tags or {})
        self._metrics.append(m)
        self._counters[name] += 1
        if "latency" in name:
            self._latencies[name].append(value)

    def trace(self, task_id: str, step: str, data: dict):
        self._traces[task_id].append({
            "step": step, "data": data, "ts": time.time()
        })

    def alert(self, level: str, message: str, task_id: str = None):
        alert = {"level": level, "message": message, "task_id": task_id, "ts": time.time()}
        self._alerts.append(alert)
        logging.warning(f"[ALERT][{level}] {message}")

    def summary(self) -> dict:
        return {
            "total_metrics": len(self._metrics),
            "counters": dict(self._counters),
            "avg_latencies": {
                k: sum(v) / len(v) for k, v in self._latencies.items() if v
            },
            "total_alerts": len(self._alerts),
            "alerts": self._alerts[-10:],
        }

# ============================================================
# 4. 容错 (Resilience)
# ============================================================

class ResiliencePolicy:
    """容错策略: 重试 / 超时 / 熔断 / 降级"""

    def __init__(self, max_retries=3, timeout=30, failure_threshold=5):
        self.max_retries = max_retries
        self.timeout = timeout
        self.failure_threshold = failure_threshold
        self._failure_counts = defaultdict(int)
        self._circuit_open = defaultdict(bool)

    def should_retry(self, key: str, retry_count: int) -> bool:
        if self._circuit_open[key]:
            return False
        return retry_count < self.max_retries

    def record_failure(self, key: str):
        self._failure_counts[key] += 1
        if self._failure_counts[key] >= self.failure_threshold:
            self._circuit_open[key] = True
            logging.error(f"Circuit breaker OPEN for {key}")

    def record_success(self, key: str):
        self._failure_counts[key] = 0
        self._circuit_open[key] = False

    def is_open(self, key: str) -> bool:
        return self._circuit_open[key]

# ============================================================
# 5. 任务调度 (Scheduler / Orchestrator)
# ============================================================

class AgentOrchestrator:
    """Agent 编排器: ReAct 循环 + 工具调度 + 容错"""

    def __init__(
        self,
        state_manager: StateManager,
        tool_registry: ToolRegistry,
        monitor: Monitor,
        policy: ResiliencePolicy,
        llm_call: Callable = None,
        max_steps: int = 10,
    ):
        self.sm = state_manager
        self.tools = tool_registry
        self.monitor = monitor
        self.policy = policy
        self.llm_call = llm_call or self._mock_llm
        self.max_steps = max_steps

    async def _mock_llm(self, prompt: str, tools: list = None) -> dict:
        """模拟 LLM 返回(生产中替换为真实 API)"""
        await asyncio.sleep(0.1)
        if "天气" in prompt:
            return {"content": "让我查一下天气", "tool_call": {"name": "get_weather", "args": {"city": "北京"}}}
        return {"content": "任务完成", "tool_call": None}

    async def _call_tool(self, tool_name: str, args: dict, task_id: str) -> Any:
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown tool: {tool_name}")
        if not self.tools.validate_args(tool, args):
            raise ValueError(f"Invalid args for {tool_name}: {args}")
        if self.policy.is_open(tool_name):
            raise RuntimeError(f"Tool {tool_name} circuit open")

        start = time.time()
        try:
            result = await asyncio.wait_for(tool.handler(**args), timeout=tool.timeout)
            latency = time.time() - start
            self.monitor.record(task_id, "tool_latency", latency, {"tool": tool_name})
            self.monitor.record(task_id, "tool_success", 1, {"tool": tool_name})
            self.policy.record_success(tool_name)
            return result
        except asyncio.TimeoutError:
            self.policy.record_failure(tool_name)
            self.monitor.alert("WARN", f"Tool {tool_name} timeout", task_id)
            raise
        except Exception as e:
            self.policy.record_failure(tool_name)
            self.monitor.alert("ERROR", f"Tool {tool_name} failed: {e}", task_id)
            raise

    async def run(self, task_input: str) -> TaskState:
        """主执行循环: ReAct(Reason → Act → Observe)"""
        state = self.sm.create(task_input)
        state.update(status=TaskStatus.RUNNING)
        self.monitor.trace(state.task_id, "start", {"input": task_input})

        for step in range(self.max_steps):
            self.sm.checkpoint(state.task_id)
            state.steps.append({"step": step, "phase": "reason"})

            try:
                # 1. Reason: LLM 决策
                prompt = self._build_prompt(state)
                llm_resp = await self.llm_call(prompt, self.tools.list_tools())
                state.context.setdefault("history", []).append({"role": "assistant", "content": llm_resp.get("content", "")})
                self.monitor.trace(state.task_id, "llm_call", {"resp": llm_resp})

                tool_call = llm_resp.get("tool_call")
                if not tool_call:
                    state.update(status=TaskStatus.COMPLETED, result=llm_resp.get("content"))
                    self.monitor.record(state.task_id, "task_success", 1)
                    break

                # 2. Act: 调用工具
                state.update(status=TaskStatus.AWAITING_TOOL)
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                retry = 0
                tool_result = None
                while self.policy.should_retry(tool_name, retry):
                    try:
                        tool_result = await self._call_tool(tool_name, tool_args, state.task_id)
                        break
                    except Exception as e:
                        retry += 1
                        state.update(retry_count=retry, status=TaskStatus.RETRYING)
                        self.monitor.record(state.task_id, "tool_retry", 1, {"tool": tool_name})
                        if not self.policy.should_retry(tool_name, retry):
                            state.update(status=TaskStatus.FAILED, error=str(e))
                            self.monitor.record(state.task_id, "task_failed", 1)
                            return state
                        await asyncio.sleep(0.5 * retry)  # 退避

                # 3. Observe: 记录结果
                state.tool_calls.append({"tool": tool_name, "args": tool_args, "result": str(tool_result)[:200]})
                state.context["history"].append({
                    "role": "tool", "name": tool_name, "content": str(tool_result)
                })
                self.monitor.trace(state.task_id, "tool_result", {"tool": tool_name})

            except Exception as e:
                state.update(status=TaskStatus.FAILED, error=str(e))
                self.monitor.alert("ERROR", f"Task failed at step {step}: {e}", state.task_id)
                self.monitor.record(state.task_id, "task_failed", 1)
                return state

        else:
            state.update(status=TaskStatus.FAILED, error="Max steps exceeded")
            self.monitor.alert("WARN", "Max steps exceeded", state.task_id)

        return state

    def _build_prompt(self, state: TaskState) -> str:
        history = state.context.get("history", [])
        recent = history[-6:]  # 只取最近 3 轮
        return f"用户输入: {state.input}\n历史: {json.dumps(recent, ensure_ascii=False)[:1000]}"

# ============================================================
# 6. 演示运行
# ============================================================

async def demo_weather_tool(city: str) -> dict:
    await asyncio.sleep(0.2)
    return {"city": city, "temp": 25, "weather": "晴"}

async def demo_calc_tool(expression: str) -> dict:
    await asyncio.sleep(0.1)
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    # 初始化各组件
    sm = StateManager()
    tools = ToolRegistry()
    monitor = Monitor()
    policy = ResiliencePolicy(max_retries=3, timeout=5)

    # 注册工具
    tools.register(ToolSchema(
        name="get_weather",
        description="查询城市天气",
        parameters={
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
        handler=demo_weather_tool,
    ))
    tools.register(ToolSchema(
        name="calculator",
        description="数学计算",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        handler=demo_calc_tool,
    ))

    orchestrator = AgentOrchestrator(sm, tools, monitor, policy)

    # 运行任务
    tasks = ["今天北京天气怎么样?", "计算 1+2*3"]
    results = await asyncio.gather(*[orchestrator.run(t) for t in tasks])

    for r in results:
        print(f"\n=== Task {r.task_id} ===")
        print(f"Input: {r.input}")
        print(f"Status: {r.status.value}")
        print(f"Result: {r.result}")
        print(f"Tool calls: {len(r.tool_calls)}, Retries: {r.retry_count}")

    print("\n=== Monitor Summary ===")
    print(json.dumps(monitor.summary(), indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(main())
```

#### 框架设计要点说明

| 模块 | 关键设计 | 面试可讲点 |
|------|---------|-----------|
| StateManager | 检查点 + 恢复 | 长任务可恢复,降低重试成本 |
| ToolRegistry | Schema 校验 + 动态注册 | 类似 OpenAI function calling,MCP 协议 |
| Monitor | 指标 + Trace + 告警 | 可观测性是生产 Agent 的命脉 |
| ResiliencePolicy | 重试 + 超时 + 熔断 | LLM/工具都会挂,必须容错 |
| Orchestrator | ReAct 循环 + 退避重试 | 通用范式,可扩展为 Plan-and-Execute |

#### 扩展方向(面试可主动提)

1. **持久化**: StateManager 接 Redis/DB,支持跨进程恢复
2. **并行工具**: 多工具调用用 `asyncio.gather`
3. **流式输出**: LLM 调用改为 async generator
4. **多 Agent**: Orchestrator 嵌套,子 Agent 作为工具
5. **预算控制**: 在 Monitor 加 Token/费用累计,超限熔断
6. **Human-in-the-loop**: 在 AWAITING_TOOL 状态可暂停等人工确认

</details>

---

### Q10: 设计一个支撑百万用户的 Agent 平台

**题目**: 设计一个支撑百万用户的 Agent 平台,要求多租户、弹性伸缩、成本控制、SLA 保障。

<details>
<summary>查看答案</summary>

#### 1. 需求分析

**功能性需求**:
- 多租户隔离(企业/团队/个人)
- Agent 创建与配置(自定义 Prompt/工具/知识库)
- Agent 发布与调用(API/SDK/Web)
- 监控与计费

**非功能性需求**:
- 百万级用户,10w+ 租户
- 单租户 QPS 上限可配,平台总 QPS 10w+
- 可用性 99.95%
- 成本可追溯、可分摊
- 弹性伸缩(分钟级扩容)

#### 2. 容量估算

```
用户: 100w,租户: 10w
日活: 30w,人均调用 50 次
日调用: 1500w 次
峰值 QPS: 1w-2w
每调用 Token: 输入 2k + 输出 500 = 2.5k
日 Token: 1500w * 2.5k = 375 亿
LLM 月成本: ~$50w(需大力优化)
存储: 日增 500GB(日志 + 向量)
```

#### 3. 架构设计

```
                    ┌─────────────┐
                    │  CDN / WAF  │
                    └──────┬──────┘
                           ↓
                    ┌─────────────┐
                    │ API Gateway │  鉴权 / 限流 / 路由
                    └──────┬──────┘
                           ↓
        ┌──────────────────┴──────────────────┐
        ↓                 ↓                    ↓
   ┌─────────┐      ┌──────────┐        ┌──────────┐
   │ 租户服务 │      │ Agent服务 │        │ 计费服务  │
   │ (隔离/配额)│   │ (编排/执行)│       │ (Token/费用)│
   └────┬────┘      └─────┬────┘        └─────┬────┘
        ↓                 ↓                    ↓
   ┌─────────┐      ┌──────────┐        ┌──────────┐
   │ 配额中心 │      │ LLM 路由  │        │ 用量采集  │
   │ (Redis)  │      │ (多厂商)  │        │ (Kafka)   │
   └─────────┘      └─────┬────┘        └──────────┘
                         ↓
              ┌──────────┬──────────┐
              ↓          ↓          ↓
          ┌──────┐  ┌──────┐  ┌──────┐
          │ 向量库 │  │ 工具池 │  │ 模型池 │
              Milvus   自建     GPU集群
              ↓          ↓          ↓
              └──────────┴──────────┘
                         ↓
              ┌─────────────────────┐
              │  可观测 + 成本控制    │
              │  Prometheus/ELK/计费 │
              └─────────────────────┘
```

#### 4. 核心模块深入

**(1) 多租户隔离**

三层隔离:
- **逻辑隔离(默认)**: 租户 ID 贯穿所有数据,行级过滤
- **命名空间隔离**: 向量库按租户分 collection,知识库按租户分 bucket
- **物理隔离(企业版)**: 独立 K8s namespace / 独立 DB / 独立模型实例

配额管理:
- 每租户 QPS 限流(令牌桶)
- 每租户日 Token 上限(预算保护)
- 每租户并发会话上限

技术: Redis 存配额,网关层校验,超限返回 429

**(2) 弹性伸缩**

分层伸缩策略:
- **无状态层**(Gateway/编排): K8s HPA,按 QPS/CPU 伸缩,秒级
- **有状态层**(向量库/对话存储): 分片 + 副本,手动/定时扩容
- **模型推理层**: GPU 节点池,按队列深度伸缩,分钟级
- **LLM 外部调用**: 多厂商 + 负载均衡 + 配额池

关键: 模型推理层伸缩最慢,需**预测式扩容**(按时段历史流量预热)

**(3) 成本控制**

四层成本治理:

| 层级 | 手段 |
|------|------|
| 请求层 | 模型路由(简单→小模型,复杂→大模型)|
| 缓存层 | 语义缓存(相同问题命中)|
| 上下文层 | 自动压缩/摘要,控制 Token |
| 计费层 | 实时计费 + 预算告警 + 超限熔断 |

实时计费架构:
```
调用 → Token 计算 → Kafka → 计费服务 → 实时累计(Redis) → 告警 → 熔断
                                       → 落库(ClickHouse) → 账单
```

**(4) SLA 保障**

| SLA 指标 | 目标 | 保障手段 |
|---------|------|---------|
| 可用性 | 99.95% | 多可用区 + 故障转移 |
| 首响延迟 | P99 < 1s | 流式 + 缓存 + 预热 |
| 成功率 | > 99% | 重试 + 降级 + 多厂商 |
| 一致性 | 最终一致 | 幂等 + 补偿 |

降级链:
```
大模型超时 → 小模型 → 模板回复 → 缓存兜底 → 错误页
```

**(5) Agent 配置与发布**

- Agent 定义: YAML/JSON(含 Prompt / 工具 / 模型参数 / 知识库)
- 版本管理: Git 化,Prompt 可回滚
- 灰度发布: 按租户/流量比例灰度
- A/B 测试: 双版本并行,按指标决策

#### 5. 容错与降级

| 故障 | 影响 | 降级 |
|------|------|------|
| LLM 厂商全挂 | 无法生成 | 缓存兜底 + 降级模板 |
| 向量库挂 | RAG 失效 | 纯 LLM 回答 + 告警 |
| 计费服务挂 | 无法计费 | 本地累计 + 延迟结算 |
| 单租户突发流量 | 影响他人 | 租户级限流 + 隔离 |

#### 6. 演进路线

- v1: 单租户 + 单模型 + 基础编排
- v2: 多租户 + 多模型路由 + 监控
- v3: 弹性伸缩 + 成本治理 + SLA 保障
- v4: Agent 市场 + 自学习 + 个性化

#### 关键权衡

- **隔离强度 vs 成本**: 物理隔离安全但贵 → 默认逻辑,企业版物理
- **弹性 vs 稳定**: 弹性省成本但冷启动慢 → 预测式扩容 + 保留缓冲
- **成本 vs 质量**: 强降级省钱但伤体验 → 分租户分级(SLA 驱动)

#### 面试加分点

主动提出这些"平台级"思考:
1. **FinOps**: 把 LLM 成本当一等公民,每个调用可追溯到租户/用户/Agent
2. **多租户噪声**: 单租户突发不能拖垮平台 → 舱壁模式
3. **模型治理**: 模型版本 / Prompt 版本 / 评测回归 / 灰度
4. **可观测性**: 不只是监控,还要"可解释"(为什么这个回答慢/贵/错)

</details>

---

## 核心知识回顾表

| 知识点 | 关键内容 | 面试考察点 |
|--------|---------|-----------|
| 六步法 | 需求→容量→架构→模块→容错→权衡 | 结构化思维,节奏控制 |
| 容量估算 | DAU→QPS→Token→成本,峰值系数 3-5x | 数字直觉,成本意识 |
| Agent 架构分层 | 接入/编排/能力/数据/可观测/容错 | 架构完整性 |
| Planner 范式 | ReAct / Plan-and-Execute / 混合 | 范式选择依据 |
| RAG 优化 | Hybrid 检索 + Rerank + Query 改写 | 检索质量 |
| 上下文管理 | 压缩 / 摘要 / 滑窗 / 检查点 | 长对话处理 |
| 工具调用可靠性 | Schema 校验 / 重试 / 熔断 / 超时 | 容错设计 |
| Multi-Agent 协作 | 消息总线 / 状态机 / 黑板 / 仲裁 | 协作复杂度 |
| 成本优化 | 模型路由 / 缓存 / 蒸馏 / 批处理 | FinOps |
| 多租户隔离 | 逻辑/命名空间/物理三级 | 平台化思维 |
| SLA 保障 | 多可用区 / 降级链 / 熔断 | 可用性 |
| 可观测性 | Metrics / Trace / Log / Eval | 生产成熟度 |

---

## 面试速记卡 — 系统设计六步法

```
┌──────────────────────────────────────────────┐
│  系统设计六步法(45min 版)                      │
├──────────────────────────────────────────────┤
│  1. 需求分析 (5-8min)                         │
│     → 澄清问题 + 功能/非功能需求表              │
│                                              │
│  2. 容量估算 (3-5min)                         │
│     → DAU→QPS→Token→成本,记得峰值系数          │
│                                              │
│  3. 架构设计 (10-15min)                       │
│     → 分层图 + 数据流 + 关键接口                │
│                                              │
│  4. 模块拆解 (8-10min)                        │
│     → 选 2-3 个核心模块深入,讲"为什么"          │
│                                              │
│  5. 容错与演进 (5-8min)                       │
│     → Top3 故障降级 + 6 个月演进路线            │
│                                              │
│  6. 权衡与总结 (3-5min)                       │
│     → 主动说缺点 + 替代方案                    │
├──────────────────────────────────────────────┤
│  开场话术:                                    │
│  "我先用 5 分钟澄清需求,10 分钟画架构,         │
│   再深入核心模块,最后讲容错和演进。              │
│   时间紧张的话,您希望我重点讲哪部分?"           │
├──────────────────────────────────────────────┤
│  Agent 系统特有要点(必讲):                     │
│  • LLM 非确定性 → 幂等 + 重试 + 评测           │
│  • Token 成本 → 模型路由 + 缓存 + 压缩         │
│  • 长链路延迟 → 流式 + 并行 + 预取             │
│  • 工具可靠性 → Schema 校验 + 熔断             │
│  • 上下文管理 → 压缩 + 检查点 + 摘要           │
│  • 可观测性 → Trace 每一步,可回放              │
└──────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

1. **不澄清就画图**: 面试官说"设计 XX 系统",你不问规模/场景/SLA 就开始画 → 必挂。前 5 分钟必须澄清。

2. **只画不估**: 跳过容量估算直接画架构 → 面试官会追问"能支撑多少用户",你答不上来。容量估算决定架构选型。

3. **架构图太细节**: 把每个微服务都画出来,主线被淹没 → 抓大放小,画到模块级即可,细节口头讲。

4. **不讲技术选型理由**: 只说"用 Milvus",不说"为什么不用 Pinecone/Weaviate" → 必须有对比和权衡。

5. **忽略 LLM 成本**: 算了 QPS 没算 Token 成本 → Agent 系统的成本核心是 LLM,必须算清。

6. **没有容错方案**: 假设一切正常 → 面试官会问"LLM 挂了怎么办",没准备就崩。必须讲降级链。

7. **多 Agent 过度设计**: 简单场景上 5 个 Agent → 过度工程。要根据复杂度选单/多 Agent。

8. **忽视可观测性**: 不讲监控/Trace/Eval → 生产系统无法运维。Agent 黑盒,可观测性是命脉。

9. **不主动讲缺点**: 只讲优点 → 显得不够成熟。主动指出 2 个缺点 + 改进方向,加分。

10. **代码题只写主流程**: Q9 这种手撕框架题,只写 `run()` 不写容错/监控 → 面试官要看工程化能力。五大模块缺一不可。

---

## 自测检查清单

### 概念题(10 题)

- [ ] 能默写系统设计六步法的顺序和每步时长?
- [ ] 能说出 Agent 系统的 7 层架构分别是什么?
- [ ] 能解释 ReAct 和 Plan-and-Execute 的区别及适用场景?
- [ ] 能说出 RAG 的 3 个核心优化手段?
- [ ] 能给出多租户隔离的三种级别及适用场景?
- [ ] 能说出 LLM 成本优化的 5 种手段及预期收益?
- [ ] 能解释什么是熔断、降级、限流的区别?
- [ ] 能说出 Multi-Agent 协作的 5 个常见陷阱?
- [ ] 能解释 Agent 系统的"可观测性"包含哪四部分?
- [ ] 能给出 SLA 99.95% 对应的月停机时间上限?

### 代码题(3 题)

- [ ] 能手写 Agent 框架的 StateManager(含检查点/恢复)?
- [ ] 能手写 ToolRegistry(含 Schema 校验)?
- [ ] 能手写 Orchestrator 的 React 循环(含重试/容错)?

### 系统设计题(2 题)

- [ ] 能在 30 分钟内完成"AI 编程助手"的完整设计(六步法)?
- [ ] 能在 30 分钟内完成"百万用户 Agent 平台"的完整设计(含多租户/弹性/成本/SLA)?

---

## 延伸阅读

### 系统设计方法论
- 《System Design Interview》(Alex Xu)— 系统设计面试经典
- 《Designing Data-Intensive Applications》— 数据密集型系统设计圣经
- ByteByteGo Newsletter — 系统设计时事通讯

### LLM/Agent 系统设计
- **LangChain Architecture**(官方文档)— Agent 编排架构参考
- **LlamaIndex**(官方文档)— RAG 系统设计参考
- **AutoGen 论文**(Microsoft)— Multi-Agent 框架设计
- **CrewAI 文档** — Multi-Agent 角色协作模式
- **OpenAI Cookbook** — 生产级 LLM 应用模式

### 真实系统案例剖析
- **Cursor 架构分析**(多篇博客)— 编程助手设计
- **ChatGPT 系统提示词泄露分析** — 系统设计借鉴
- **LangSmith / Langfuse** — Agent 可观测性平台
- **Dify / Coze 架构** — Agent 平台设计参考

### 容量与成本
- **LLM Pricing 对比**(各厂商定价页)
- **Token 计数工具**(tiktoken / transformers tokenizer)
- **向量库 Benchmark**(ann-benchmarks.com)

### 可观测性与评测
- **OpenTelemetry for LLM** — Trace 标准
- **Arize Phoenix** — LLM 可观测性
- **Ragas / DeepEval** — RAG/Agent 评测框架

---

## 明日预告

**Day 21 — Week 3 回顾与手撕代码**

明天是 Week 3 的收官,内容安排:
1. **Week 3 知识总览**: 框架(LangChain/LlamaIndex)→ Multi-Agent → 评测 → 安全 → 系统设计,串成完整知识链
2. **Week 3 高频面试题精选**: 从 Day15-20 中精选 20 道最高频题,快速过一遍
3. **手撕代码强化**: Agent 框架骨架进阶版(增加流式输出 / 并行工具 / Human-in-the-loop)
4. **Week 3 模拟面试**: 60 分钟模拟面试(30min 概念 + 30min 系统设计)
5. **Week 4 预告**: 进入实战项目与面试冲刺阶段

> **今日作业**: 选 2 道系统设计题(Q2/Q10),各用 30 分钟白板计时练习,录音复盘自己的节奏和遗漏点。
