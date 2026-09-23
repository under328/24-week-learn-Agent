# Day 24 — 腾讯百度 Agent 面试专项

> **学习目标**: 掌握腾讯(混元/微信AI/QQ/游戏NPC)和百度(文心一言/搜索/知识图谱)两大厂的 Agent 面试高频考点,能够独立完成社交场景 Agent 系统设计与搜索增强 Agent 代码实现。
>
> **面试定位**: Day22-23 已攻下字节、阿里两大厂的 Agent 面试套路。今日聚焦腾讯和百度——腾讯偏社交/游戏/多模态场景落地,百度偏搜索/知识图谱/Function Calling 工程化。两者考察侧重点截然不同:腾讯重"产品 + 场景 + 体验",百度重"原理 + 工程 + 知识"。
>
> **预计耗时**: 4-5 小时(含手撕代码与系统设计推演)
>
> **适用岗位**: Agent 算法工程师 / 大模型应用工程师 / AI 架构师 / 智能体产品经理

---

## 今日知识图谱

```
腾讯百度 Agent 面试专项
│
├── 腾讯 (Tencent)
│   ├── 团队分布
│   │   ├── 腾讯 AI Lab — 基础研究,偏学术
│   │   ├── 微信 AI — 场景落地,偏产品体验
│   │   ├── 混元大模型团队 — 基座模型 + 多模态
│   │   └── 互动娱乐事业群(IEG) — 游戏 NPC / 玩法 AI
│   │
│   ├── 面试风格
│   │   ├── 二面技术 + 一面 HR,通常 3-4 轮
│   │   ├── 重场景理解:社交/游戏/内容
│   │   ├── 重产品思维:用户体验 > 技术炫技
│   │   └── 重工程落地:并发/延迟/成本权衡
│   │
│   ├── 高频考点
│   │   ├── 微信/QQ 社交场景 Agent 设计
│   │   ├── 游戏 NPC Agent(对话+决策+情感)
│   │   ├── 混元基座 + 场景微调适配
│   │   ├── 多模态 Agent(图文/语音/视频)
│   │   └── 低延迟推理优化(KV Cache/Speculative)
│   │
│   └── 真题方向
│       ├── 微信智能助手 Agent(消息摘要/日程/翻译/搜索)
│       ├── 群聊 AI 助手(多人理解/任务分配/隐私)
│       ├── 游戏 NPC 智能体(开放世界对话)
│       └── 混元 + RAG 客服系统
│
├── 百度 (Baidu)
│   ├── 团队分布
│   │   ├── 文心一言团队 — 对话/Function Calling
│   │   ├── 百度搜索团队 — 搜索增强/答案抽取
│   │   ├── 知识图谱部门 — 大规模 KG 构建
│   │   └── 智能云千帆平台 — Agent 平台化
│   │
│   ├── 面试风格
│   │   ├── 3 轮技术 + 1 轮经理,通常 4 轮
│   │   ├── 重原理深度:Function Calling/检索/排序
│   │   ├── 重工程能力:大规模数据处理
│   │   └── 重知识体系:KG/搜索/推荐交叉
│   │
│   ├── 高频考点
│   │   ├── 搜索 + Agent 融合架构
│   │   ├── 大规模知识图谱构建与查询
│   │   ├── Function Calling 原理与优化
│   │   ├── Query 理解(意图/实体/改写)
│   │   └── 答案抽取与引用溯源
│   │
│   └── 真题方向
│       ├── 百度搜索 Agent 全链路设计
│       ├── ERNIE Bot 插件系统设计
│       ├── 医疗/法律 KG Agent
│       └── 千帆平台 Agent 编排
│
└── 通用能力(两家都考)
    ├── 手撕代码:RAG/搜索/工具调用
    ├── 系统设计:多轮对话/多 Agent 协作
    ├── 场景拆解:从需求到架构
    └── Trade-off 分析:精度 vs 延迟 vs 成本
```

---

## 面试题(共 10 道)

### Q1: 腾讯面试风格 — 腾讯 AI Lab / 微信 AI / 混元团队的面试流程和考察重点是什么?

<details>
<summary>展开答案</summary>

**腾讯 Agent 相关团队分布与考察重点**:

| 团队 | 业务方向 | 面试侧重 | 典型问题 |
|------|---------|---------|---------|
| 腾讯 AI Lab | 基础研究(西雅图/北京/深圳) | 学术深度、论文复现 | "讲一篇你最近看的 Agent 论文,如何改进?" |
| 微信 AI | 微信智能助手、输入法AI、对话引擎 | 产品体验、低延迟 | "设计微信消息摘要 Agent,延迟 < 2s" |
| 混元大模型团队 | 基座模型、多模态、对齐 | 训练原理、SFT/RLHF | "混元做 Agent 底座,如何场景适配?" |
| 互动娱乐(IEG) | 游戏 NPC、玩法 AI | 强化学习、行为树 | "设计开放世界 NPC Agent" |
| 智能客服(CSIG) | 企业客服、营销 Agent | 工程落地、ROI | "客服 Agent 如何降本 30%?" |

**面试流程(典型)**:
1. **一面(60-90min)**:自我介绍 + 项目深挖 + 2 道算法题 + 反问
2. **二面(60min)**:系统设计题 + 技术原理追问 + 场景题
3. **三面(45-60min)**:总监面,看综合能力、产品思维、职业规划
4. **HR 面(30min)**:薪资、稳定性、文化匹配

**腾讯面试的三个鲜明特点**:

**特点一:产品思维优先**
腾讯面试官特别看重"用户视角"。同样一道系统设计题,字节可能追问"架构怎么 scale",腾讯会追问"用户第一次用会怎样?群聊里 AI 会不会插嘴打断?隐私怎么处理?"。建议准备时,每个方案都要从用户视角过一遍体验。

**特点二:低延迟硬指标**
微信生态对延迟极敏感。面试官常给硬指标:"消息摘要 P99 < 2s","翻译首字 < 800ms","NPC 响应 < 500ms"。回答时必须给出延迟拆解(模型推理/网络/排队),并提优化手段(KV Cache、Speculative Decoding、流式输出、模型蒸馏)。

**特点三:社交场景复杂度高**
群聊、朋友圈、小程序、视频号——这些场景天然多角色、多模态、多上下文。面试官喜欢出"多人场景"题:群里有 5 个人 + 1 个 AI,AI 该如何决策要不要回复?这种题考的不是单纯技术,而是"边界感"设计。

**回答模板**:
> "腾讯面试我准备了三点:一是把微信/QQ 等社交场景的 Agent 设计案例各准备一个;二是延迟优化方案储备(KV Cache/Speculative/流式/蒸馏);三是产品体验视角的 trade-off 思考,比如 AI 主动介入 vs 被动响应的边界。"

</details>

---

### Q2: 设计微信智能助手 Agent(消息摘要 / 日程 / 翻译 / 搜索)

<details>
<summary>展开答案</summary>

**题目背景**:这是微信 AI 团队经典系统设计题,考察多技能 Agent 的编排、低延迟、隐私安全。

#### 一、需求拆解

**功能需求**:
- **消息摘要**:用户长时间未读群聊,触发"一键摘要",生成 3-5 句话总结
- **日程管理**:从聊天中识别时间/地点/事件,提醒用户加日历
- **翻译**:多语言消息实时翻译(中英日韩等)
- **搜索**:基于聊天记录回答用户问题("上周和小明约了什么时候吃饭?")

**非功能需求**:
- 摘要 P99 < 2s,翻译首字 < 800ms
- 端侧优先(隐私),云端兜底
- 多设备同步(手机/PC/平板)
- 日活 10 亿级,峰值 QPS 50 万

#### 二、整体架构

```
┌─────────────────────────────────────────────────────┐
│                微信客户端(端侧 Agent)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ 意图路由  │→│ 技能执行  │→│ 结果渲染  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
│        ↓            ↓              ↓                │
│   端侧小模型    端侧/云端        流式 UI             │
│  (意图分类)    混元大模型                          │
└─────────────────────┬───────────────────────────────┘
                      │ HTTPS
┌─────────────────────┴───────────────────────────────┐
│                  微信 Agent 网关                      │
│   鉴权 / 限流 / 路由 / 隐私脱敏                       │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│              Agent 编排层(ReAct + 技能路由)          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │摘要技能│ │日程技能│ │翻译技能│ │搜索技能│        │
│  └────────┘ └────────┘ └────────┘ └────────┘        │
└─────┬──────────┬──────────┬──────────┬──────────────┘
      │          │          │          │
┌─────┴────┐┌────┴────┐┌────┴────┐┌────┴────┐
│混元摘要  ││NER+日历 ││NMT翻译  ││向量检索│
│模型     ││API     ││模型    ││+重排   │
└─────────┘└─────────┘└─────────┘└─────────┘
```

#### 三、关键模块设计

**1. 意图路由(端侧)**
- 用 0.5B 小模型做 4 分类:summary/schedule/translate/search/none
- 端侧推理 < 50ms,准确率 > 95%
- 不确定时上抛云端二次确认

**2. 消息摘要技能**
- 输入:最近 100 条未读消息 + 上下文(群成员/时间/话题)
- 长上下文压缩:先用小模型做 chunk 摘要,再用大模型合并
- 流式输出:边生成边显示,首字延迟 < 800ms
- **难点**:群聊多人发言,要做"谁说了什么"的归因

**3. 日程管理技能**
- NER 抽取:时间(下周三)、地点(星巴克国贸店)、事件(产品评审)
- 时间归一化:"下周三 14:00" → ISO 8601
- 与系统日历 API 对接,弹卡片让用户一键确认
- **难点**:模糊表达("到时候再说" → 不抽取;改时间场景处理)

**4. 翻译技能**
- 端侧 NMT 小模型(中英),云端大模型兜底(小语种)
- 增量翻译:用户每输入一个 token 翻译一次
- 术语库:用户自定义词表(人名/产品名不翻译)

**5. 搜索技能(RAG)**
- 索引:用户聊天记录做向量索引(端侧 SQLite + FAISS)
- 检索:Query 改写 → 向量召回 → 时间衰减重排
- 生成:混元 + 引用溯源(引用具体聊天记录片段)
- **难点**:隐私——所有检索必须在端侧完成

#### 四、延迟与成本优化

| 优化手段 | 收益 | 代价 |
|---------|------|------|
| 端侧小模型做意图路由 | -1.5s 网络往返 | 端侧模型 200MB |
| KV Cache 复用(多轮对话) | 推理提速 2-3x | 显存占用增加 |
| Speculative Decoding | 提速 1.5-2x | 小模型训练成本 |
| 流式输出 | 首字延迟降低 70% | UI 复杂度增加 |
| 模型蒸馏(混元 → 7B) | 推理成本降 5x | 蒸馏数据 + 训练 |
| 分级调用(简单任务用小模型) | 成本降 60% | 路由准确率要求高 |

#### 五、隐私安全设计

1. **端侧优先**:摘要、翻译、搜索尽量端侧完成
2. **云端脱敏**:必须上云时,人名/电话/地址先脱敏
3. **用户授权**:每类技能独立授权开关
4. **不持久化**:云端处理完即删,不留日志
5. **审计日志**:端侧记录调用链,用户可查看

#### 六、面试加分点

- **多模态扩展**:支持图片消息摘要、语音消息转文字
- **个性化**:基于用户画像调整摘要风格(简洁/详细)
- **冷启动**:新用户没有历史,用通用模板 + 用户反馈微调
- **降级方案**:模型不可用时,退化为关键词高亮 + 折叠

</details>

---

### Q3: Agent 在游戏 NPC 中的应用(对话 / 决策 / 情感)

<details>
<summary>展开答案</summary>

**题目背景**:腾讯 IEG(互动娱乐事业群)高频题,考察 RL + LLM Agent 在游戏场景的融合。

#### 一、传统 NPC vs Agent NPC

| 维度 | 传统 NPC(行为树/状态机) | Agent NPC(LLM/RL 驱动) |
|------|------------------------|------------------------|
| 对话 | 预写脚本,有限分支 | 开放对话,千人千面 |
| 决策 | if-else 规则 | 基于目标的规划 |
| 情感 | 表情符号切换 | 多维情感模型 |
| 开发成本 | 每个剧情手工写 | 一次训练,多场景复用 |
| 一致性 | 100% 一致 | 可能 OOC(人设崩塌) |
| 延迟 | < 10ms | 100-500ms |

#### 二、Agent NPC 架构

```
┌──────────────────────────────────────────────────┐
│              游戏世界状态(World State)            │
│   时间/地点/NPC关系/任务进度/玩家行为             │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────┴───────────────────────────────┐
│              Agent NPC 核心模块                    │
│                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐      │
│  │ 感知模块  │→ │ 记忆模块  │→ │ 思考模块  │      │
│  │Perception│   │ Memory   │   │ Planning │      │
│  └──────────┘   └──────────┘   └──────────┘      │
│                                      ↓           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐      │
│  │ 情感模块  │← │ 对话模块  │← │ 决策模块  │      │
│  │ Emotion  │   │ Dialog   │   │ Action   │      │
│  └──────────┘   └──────────┘   └──────────┘      │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────┴───────────────────────────────┐
│              游戏引擎(Unity/UE)                  │
│        动作执行 / 动画播放 / 物理碰撞             │
└──────────────────────────────────────────────────┘
```

#### 三、五大模块详解

**1. 感知模块(Perception)**
- 输入:玩家对话文本、玩家行为(攻击/送礼/逃跑)、环境事件(天气/时间)
- 处理:多模态融合,文本走 LLM,行为走事件编码
- 输出:结构化感知向量

**2. 记忆模块(Memory)**
- **短期记忆**:最近 10 轮对话,token 级别精确
- **长期记忆**:与该玩家的所有交互,向量化检索
- **世界知识**:NPC 的背景故事、人设、关系网(注入 prompt)
- **群体记忆**:该 NPC 群体共享的记忆(如"村民都知道村长被杀")

```python
# 记忆检索示例
def retrieve_memory(npc_id, player_id, query, top_k=5):
    # 短期记忆:最近对话
    short_term = get_recent_dialogs(npc_id, player_id, limit=10)
    # 长期记忆:向量检索
    long_term = vector_search(
        collection=f"npc_{npc_id}_player_{player_id}",
        query=embed(query),
        top_k=top_k
    )
    # 世界知识:固定注入
    world_knowledge = load_npc_profile(npc_id)
    return short_term + long_term + world_knowledge
```

**3. 思考模块(Planning)**
- 目标:基于人设和当前状态,决定下一步行动
- 方法:ReAct / Tree of Thought
- 输出:结构化计划(对话/移动/战斗/等待)

**4. 情感模块(Emotion)**
- **OCC 模型**:22 种基础情感(喜悦/悲伤/愤怒/恐惧/惊讶...)
- **维度模型**:Valence(正负) × Arousal(激活) × Dominance(支配)
- **动态更新**:玩家行为影响情感值,情感值影响对话风格

```python
# 情感状态机
class EmotionState:
    def __init__(self):
        self.valence = 0.0   # [-1, 1] 负面到正面
        self.arousal = 0.0   # [-1, 1] 平静到激动
        self.dominance = 0.5 # [0, 1]  弱到强

    def update(self, event):
        if event.type == "player_attack":
            self.valence -= 0.3
            self.arousal += 0.5
            self.dominance -= 0.2
        elif event.type == "player_gift":
            self.valence += 0.4
            self.arousal += 0.2
        # 衰减回归基线
        self.valence *= 0.95
        self.arousal *= 0.9
```

**5. 对话模块(Dialog)**
- Prompt 模板:人设 + 情感状态 + 记忆 + 玩家输入
- 输出约束:语气/口癖/称谓/长度
- 一致性校验:检测 OOC,违反人设时重生成

#### 四、关键挑战与解法

**挑战一:延迟**
- 问题:LLM 推理 100-500ms,玩家感知卡顿
- 解法:预生成 + 缓存;简单对话用小模型;关键剧情用大模型

**挑战二:一致性(OOC)**
- 问题:NPC 突然说出不符合人设的话
- 解法:
  - 强化人设 prompt(开头注入"你必须是 XXX,性格 YY")
  - 输出后做一致性校验(分类器判断是否 OOC)
  - RLHF 训练时加入 OOC 惩罚

**挑战三:成本**
- 问题:每 NPC 每次对话都调 LLM,成本爆炸
- 解法:
  - 重要 NPC 用大模型,路人 NPC 用模板
  - 离线预生成常见对话分支,运行时检索
  - 玩家不在场时,NPC 行为用规则模拟

**挑战四:多 NPC 协作**
- 问题:多个 NPC 同时在场,需要协调
- 解法:Multi-Agent 框架,每个 NPC 独立 Agent,通过"广播事件"通信

#### 五、面试加分

- **提到腾讯游戏案例**:《王者荣耀》AI 对战(NPC 智能体)、《和平精英》AI 队友
- **提到 RL 训练**:Self-play 训练 NPC 战斗策略
- **提到蒸馏**:把大 LLM 蒸馏到 1B 模型部署
- **提到 A/B 实验**:Agent NPC vs 传统 NPC,玩家留存/付费提升

</details>

---

### Q4: 混元大模型做 Agent 底座,如何做场景适配?

<details>
<summary>展开答案</summary>

**题目背景**:混元团队核心题,考察大模型从通用到垂直场景的适配方法论。

#### 一、场景适配的三个层次

```
通用混元基座(万亿参数,全量预训练)
        ↓
行业适配(百亿参数,行业数据 SFT)
        ↓
场景精调(几十亿参数,场景数据 DPO/RLHF)
```

#### 二、适配方法对比

| 方法 | 数据量 | 成本 | 效果 | 适用场景 |
|------|--------|------|------|---------|
| **Prompt Engineering** | 0 | 极低 | 中 | 快速验证、长尾场景 |
| **In-Context Learning** | 几十条 | 低 | 中高 | 少样本场景 |
| **LoRA / QLoRA** | 千-万条 | 低 | 高 | 中等规模场景 |
| **全参 SFT** | 万-百万条 | 中 | 高 | 核心业务场景 |
| **DPO / RLHF** | 万条偏好对 | 中高 | 极高 | 对齐敏感场景 |
| **继续预训练(CPT)** | 亿级 tokens | 高 | 高(领域知识) | 垂直行业(医疗/法律) |
| **模型蒸馏** | 大模型生成数据 | 中 | 中高 | 端侧部署 |

#### 三、场景适配完整流程

**Step 1:场景定义**
- 明确任务类型(对话/抽取/生成/推理)
- 明确输入输出格式
- 定义评估指标(准确率/BLEU/人工评分)

**Step 2:数据准备**
- 真实业务数据采样(脱敏)
- 数据清洗(去重/去噪/质量评分)
- 数据增强(回译/改写/自我对弈)
- 偏好对构建(人工标注 + 模型辅助)

**Step 3:适配训练**
- 先 LoRA 快速验证(2-3 天看效果)
- 效果达标后全参 SFT(1-2 周)
- 必要时 DPO 对齐(1-2 周)
- 评估集持续监控过拟合

**Step 4:Agent 能力注入**
- Function Calling 数据:SFT 时加入工具调用样本
- ReAct 数据:构造 Thought-Action-Observation 链路
- 多轮对话:训练时模拟真实多轮交互

**Step 5:评估与迭代**
- 自动评估:业务指标 + 通用 benchmark
- 人工评估:盲评打分 + 错例分析
- 线上 A/B:核心业务指标(留存/转化/满意度)

#### 四、典型场景适配案例

**案例一:微信客服 Agent**
- 基座:混元 70B
- 适配:LoRA + 10 万条客服对话
- 工具:订单查询/退款/物流/工单创建
- 评估:首次解决率(FCR)从 60% → 78%

**案例二:游戏 NPC Agent**
- 基座:混元 13B(蒸馏版)
- 适配:SFT + 5 万条人设对话 + DPO(避免 OOC)
- 工具:游戏内动作 API
- 评估:OOC 率从 15% → 3%

**案例三:医疗问答 Agent**
- 基座:混元 70B + 医疗 CPT
- 适配:继续预训练(20 亿医疗 tokens)+ SFT
- 工具:医学知识图谱检索
- 评估:准确率从 65% → 89%

#### 五、关键 Trade-off

**Trade-off 一:通用能力 vs 专用能力**
- 全参 SFT 容易"灾难遗忘",通用能力下降
- 解法:混合训练数据(80% 专用 + 20% 通用)

**Trade-off 二:模型大小 vs 延迟**
- 大模型效果好但延迟高
- 解法:蒸馏 + 量化(INT8/INT4)

**Trade-off 三:数据质量 vs 数据数量**
- 低质量数据反而损害效果
- 解法:质量评分模型 + 人工抽检

**Trade-off 四:安全 vs 能力**
- 过度对齐导致拒绝率升高
- 解法:红队测试 + 分级安全策略

#### 六、面试加分

- **提到混元多模态**:文本 + 图像 + 语音统一编码
- **提到 MoE 架构**:混元采用 MoE,推理时只激活部分专家
- **提到腾讯太极训练平台**:大规模分布式训练
- **提到 AngelPTM**:腾讯自研训练框架

</details>

---

### Q5: 百度面试风格 — 文心一言 / 搜索团队的面试流程和考察重点

<details>
<summary>展开答案</summary>

**百度 Agent 相关团队分布与考察重点**:

| 团队 | 业务方向 | 面试侧重 | 典型问题 |
|------|---------|---------|---------|
| 文心一言(ERNIE Bot) | 对话、Function Calling | 模型原理、训练细节 | "Function Calling 怎么实现的?" |
| 百度搜索 | 搜索增强、答案抽取 | 检索排序、NLP 经典 | "Query 理解怎么做?" |
| 知识图谱部门 | 大规模 KG | 图数据库、实体链接 | "如何构建亿级 KG?" |
| 千帆大模型平台 | Agent 平台化 | 工程架构、编排 | "设计 Agent 编排引擎" |
| 智能云(ACG) | 企业 Agent 落地 | 行业方案、ROI | "金融 Agent 怎么做?" |

**面试流程(典型)**:
1. **一面(60min)**:八股 + 项目 + 1-2 道算法题(偏中等难度)
2. **二面(60-90min)**:系统设计 + 深度原理追问 + 场景题
3. **三面(60min)**:技术总监面,看综合技术深度
4. **四面(45min)**:经理面,看职业规划、稳定性

**百度面试的三个鲜明特点**:

**特点一:NLP 基本功扎实**
百度是 NLP 老牌强厂(从搜索时代积累),面试官特别看重基本功。会问得很细:"BERT 的 Masked LM 为什么不用 15% 全部替换为 [MASK]?"、"Transformer 的位置编码为什么用 sin/cos?"、"BM25 公式写出来"。**建议**重温 NLP 经典论文(BERT/GPT/Transformer)。

**特点二:搜索思维根深蒂固**
百度面试官天然带着"搜索视角"看 Agent。他们把 Agent 视为"搜索 + 生成"的升级版。常见追问:
- "Agent 和传统搜索有什么本质区别?"
- "Query 改写在 Agent 里怎么做?"
- "搜索结果如何排序后喂给 LLM?"

**特点三:知识图谱必考**
百度是国内 KG 落地最深的厂(百度知心、百科图谱)。Agent 岗位几乎必问 KG:
- "如何用 KG 增强 Agent?"
- "实体链接怎么做?"
- "KBQA(基于知识库的问答)架构?"

**回答模板**:
> "百度面试我准备了三块:一是 NLP 八股(Transformer/BERT/位置编码/注意力机制)扎实过一遍;二是搜索 + Agent 融合架构(Query 理解/检索/排序/生成);三是知识图谱构建与查询(实体链接/关系抽取/SPARQL)。"

**与腾讯的对比**:

| 维度 | 腾讯 | 百度 |
|------|------|------|
| 考察重心 | 产品体验、场景设计 | 原理深度、工程能力 |
| 系统设计题 | 社交/游戏场景 | 搜索/知识场景 |
| 算法题难度 | 中等,偏实际 | 中等偏上,偏经典 |
| 八股深度 | 中等 | 深(NLP 经典必问) |
| 文化关键词 | 产品导向、用户至上 | 技术导向、数据说话 |

</details>

---

### Q6: Agent 如何与搜索引擎结合?(百度搜索 Agent)

<details>
<summary>展开答案</summary>

**题目背景**:百度搜索团队核心题,考察搜索与 LLM Agent 的深度融合架构。

#### 一、传统搜索 vs 搜索 Agent

| 维度 | 传统搜索 | 搜索 Agent |
|------|---------|-----------|
| 交互 | 单轮 Query → 结果列表 | 多轮对话 → 直接答案 |
| 理解 | 关键词匹配 | 意图理解 + 上下文 |
| 输出 | 10 条蓝色链接 | 结构化答案 + 引用 |
| 工具 | 无 | 可调用计算器/地图/天气 |
| 个性化 | 弱(Cookie 级) | 强(对话历史 + 用户画像) |

#### 二、百度搜索 Agent 全链路架构

```
用户输入 Query
      ↓
┌─────────────────────────────────────┐
│  1. Query 理解                       │
│  - 意图识别(导航/信息/交易)          │
│  - 实体识别(人/地/时/事)             │
│  - Query 改写(扩展/纠错/同义)        │
│  - 多轮上下文拼接                     │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  2. 检索(Retrieval)                  │
│  - 召回:倒排 + 向量 + KG 多路        │
│  - 粗排:LR/GBDT 百级特征            │
│  - 精排:DNN 千级特征                │
│  - 重排:多样性 + 时效性             │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  3. 答案生成(Generation)             │
│  - 答案抽取(段落级/句子级)           │
│  - 答案合成(LLM 生成 + 引用)         │
│  - 事实校验(与检索结果对齐)          │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  4. 工具调用(可选)                   │
│  - 计算器/地图/天气/股票             │
│  - 实时数据 API                      │
└─────────────┬───────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  5. 答案渲染                         │
│  - 文字 + 图表 + 卡片                │
│  - 引用溯源(角标链接)                │
│  - 追问建议                          │
└─────────────────────────────────────┘
```

#### 三、关键模块深度

**1. Query 理解**

```python
class QueryUnderstanding:
    def __init__(self):
        self.intent_classifier = load_model("ernie-intent")  # 意图分类
        self.ner_model = load_model("ernie-ner")             # 实体识别
        self.rewriter = load_model("ernie-rewrite")          # Query 改写

    def understand(self, query, context=None):
        # 1. 多轮上下文拼接
        if context:
            query = self.resolve_coreference(query, context)
        # 2. 意图识别
        intent = self.intent_classifier.predict(query)
        # 3. 实体识别
        entities = self.ner_model.extract(query)
        # 4. Query 改写
        rewritten = self.rewriter.rewrite(query, intent, entities)
        return {
            "original": query,
            "rewritten": rewritten,
            "intent": intent,
            "entities": entities
        }
```

**Query 改写策略**:
- **同义扩展**:"iPhone 15 价格" → "iPhone 15 售价 多少钱"
- **纠错**:"泰达希尔" → "泰迪熊"
- **指代消解**:"他那本书怎么样"(上下文:小明 三体) → "三体 这本书怎么样"
- **子 Query 拆分**:"北京和上海天气对比" → ["北京天气", "上海天气"]

**2. 多路召回融合**

| 召回通道 | 索引类型 | 优势 | 劣势 |
|---------|---------|------|------|
| 倒排召回 | BM25 | 精确匹配、速度快 | 语义理解弱 |
| 向量召回 | ANN(FAISS/HNSW) | 语义匹配 | 长尾词弱 |
| KG 召回 | 图查询 | 实体关系强 | 覆盖率低 |
| 交互式召回 | Cross-Encoder | 精度高 | 速度慢(用于精排) |

**3. 答案抽取与生成**

两种模式的选择:
- **抽取式**:直接从 Top 文档抽取答案片段(适合事实型查询)
- **生成式**:LLM 基于检索结果生成答案(适合复杂问题)

```python
def answer_generation(query, retrieved_docs, mode="hybrid"):
    if mode == "extractive":
        # 抽取式:用 MRC 模型
        answer = mrc_model.extract(query, retrieved_docs)
    elif mode == "generative":
        # 生成式:LLM + 引用
        prompt = build_prompt(query, retrieved_docs)
        answer = llm.generate(prompt, citations=True)
    else:  # hybrid
        # 先抽取候选,再生成润色
        candidates = mrc_model.extract_candidates(query, retrieved_docs)
        answer = llm.refine(query, candidates, retrieved_docs)
    return answer
```

**4. 引用溯源**

- 生成时每个句子标注来源 [1][2]
- 角标对应底部引用列表
- 点击跳转原文位置
- **难点**:LLM 生成时容易"幻觉引用",需要后处理校验

**5. 事实校验**

- 答案中的实体与检索结果做交叉验证
- 数字/日期严格校验
- 不一致时降级为"根据多个来源..."

#### 四、Agent 化的关键能力

**能力一:多轮对话**
- 维护对话状态
- 指代消解
- 上下文追问

**能力二:工具调用**
- Query 识别为"计算类" → 调计算器
- "附近餐厅" → 调地图 API
- "今天天气" → 调天气 API

**能力三:主动澄清**
- Query 模糊时反问:"您是想问 X 还是 Y?"
- 信息不足时追问:"请告诉我具体城市"

**能力四:规划与拆解**
- 复杂问题拆分为子问题
- 并行检索子问题
- 合并答案

#### 五、面试加分

- **提到百度"知心"**:百度知识图谱增强搜索
- **提到文心 ERNIE Bot**:百度自研大模型,与搜索深度结合
- **提到千帆平台**:百度 Agent 开发平台
- **提到 BES(百度 Elasticsearch)**:大规模检索引擎
- **提到时效性处理**:新闻类 Query 走实时索引

</details>

---

### Q7: 知识图谱在 Agent 中的作用?如何构建大规模知识图谱?

<details>
<summary>展开答案</summary>

**题目背景**:百度知识图谱部门核心题,考察 KG 在 Agent 中的定位与工程能力。

#### 一、知识图谱在 Agent 中的四大作用

**作用一:事实增强(减少幻觉)**
- LLM 容易幻觉(胡编事实)
- KG 提供确定性事实,作为"外挂记忆"
- 例:用户问"姚明的妻子是谁?",KG 直接返回"叶莉",LLM 基于此回答

**作用二:推理增强(多跳推理)**
- LLM 多跳推理弱(超过 3 跳准确率骤降)
- KG 天然支持多跳推理(图遍历)
- 例:"姚明妻子的家乡是哪里?" → 姚明 → 叶莉 → 出生地 → 上海

**作用三:实体消歧**
- "苹果"是水果还是公司?KG 提供实体上下文
- 帮助 Agent 准确理解 Query

**作用四:可解释性**
- LLM 黑盒,Agent 答案难以解释
- KG 提供推理路径,可解释"为什么是这个答案"

#### 二、KG + Agent 融合架构

```
用户 Query
    ↓
┌────────────────┐
│ 1. 实体链接     │  Query → KG 实体
│ (Entity Linking)│
└───────┬────────┘
        ↓
┌────────────────┐
│ 2. 关系抽取     │  Query → KG 关系
│(Rel Extraction)│
└───────┬────────┘
        ↓
┌────────────────┐
│ 3. 子图检索     │  实体周边子图
│ (Subgraph)     │
└───────┬────────┘
        ↓
┌────────────────┐
│ 4. 路径推理     │  多跳推理
│ (Reasoning)    │
└───────┬────────┘
        ↓
┌────────────────┐
│ 5. 答案生成     │  LLM + KG 证据
│ (Generation)   │
└────────────────┘
```

#### 三、大规模 KG 构建流程

**Step 1:本体设计(Ontology)**
- 定义实体类型(人/地/组织/事件...)
- 定义关系类型(出生地/任职于/配偶...)
- 定义属性(出生日期/人口/GDP...)
- **难点**:跨行业本体对齐

**Step 2:知识抽取**
- **实体抽取(NER)**:BERT/ERNIE 序列标注
- **关系抽取(RE)**:句法分析 + 分类模型
- **属性抽取(AE)**:正则 + 模型
- **事件抽取(EE)**:触发词 + 论元

```python
# 知识抽取流水线
class KnowledgeExtractor:
    def __init__(self):
        self.ner = load_model("ernie-ner-large")
        self.re = load_model("ernie-re-large")
        self.ae = load_model("ernie-ae")

    def extract(self, text):
        # 1. 实体抽取
        entities = self.ner.predict(text)
        # 2. 关系抽取(实体对)
        relations = []
        for e1, e2 in combinations(entities, 2):
            rel = self.re.predict(text, e1, e2)
            if rel.confidence > 0.8:
                relations.append((e1, rel.type, e2))
        # 3. 属性抽取
        attributes = self.ae.extract(text, entities)
        return entities, relations, attributes
```

**Step 3:知识融合**
- **实体对齐**:"姚明"和"Yao Ming"是同一实体
- **实体消歧**:"李娜"(网球)vs"李娜"(歌手)
- **冲突解决**:多来源数据矛盾时,按可信度排序

**Step 4:知识存储**
- **图数据库**:Neo4j / JanusGraph / 百度自研 HUGEGRAPH
- **RDF 三元组**:(主体, 关系, 客体)
- **属性图**:节点和边都有属性

**Step 5:知识推理**
- **规则推理**:IF (X, 妻子, Y) AND (Y, 出生地, Z) THEN (X, 妻子出生地, Z)
- **图神经网络(GNN)**:R-GCN / TransE 学习实体表示
- **LLM 推理**:用大模型做零样本关系推理

**Step 6:质量评估**
- **完整性**:覆盖率、缺失关系
- **正确性**:人工抽检、交叉验证
- **时效性**:知识更新频率

#### 四、百度 KG 规模与挑战

**百度知识图谱规模**:
- 实体数:数十亿级
- 关系数:数百亿级
- 数据来源:百科、网页、结构化数据、用户行为
- 更新频率:分钟级(热点)、日级(常规)、月级(全量)

**三大挑战**:

**挑战一:规模与延迟**
- 亿级图谱查询延迟 < 100ms
- 解法:多级缓存 + 子图预计算 + 图分区

**挑战二:时效性**
- 知识过时(明星结婚、公司并购)
- 解法:增量更新 + 事件触发更新 + 置信度衰减

**挑战三:质量与成本**
- 自动抽取错误率高
- 解法:人工审核 + 主动学习 + 众包

#### 五、KG Agent 实战案例

**案例:医疗 KG Agent**
```python
class MedicalKGAgent:
    def __init__(self):
        self.kg = MedicalGraph()  # 医疗知识图谱
        self.llm = ERNIEBot()

    def answer(self, query):
        # 1. 实体链接
        entities = self.entity_linking(query)
        # 2. 子图检索
        subgraph = self.kg.get_subgraph(entities, hop=2)
        # 3. 路径推理
        reasoning_paths = self.kg.reason(subgraph, query)
        # 4. LLM 生成
        prompt = self.build_prompt(query, reasoning_paths)
        answer = self.llm.generate(prompt)
        return {
            "answer": answer,
            "evidence": reasoning_paths,  # 可解释
            "disclaimer": "仅供参考,请遵医嘱"
        }
```

**KG 内容**:
- 疾病、症状、药物、检查、科室
- 关系:疾病-症状、疾病-药物、药物-禁忌
- 来源:医学文献、临床指南、药品说明书

#### 六、面试加分

- **提到百度知心**:百度知识中台
- **提到 HUGEGRAPH**:百度开源图数据库
- **提到 KG-BERT**:用 BERT 增强 KG 任务
- **提到 KBQA**:基于 KG 的问答
- **提到与 LLM 结合的趋势**:KG 作为 LLM 的外挂记忆、LLM 辅助 KG 构建

</details>

---

### Q8: 文心一言的 Function Calling 实现原理和优化

<details>
<summary>展开答案</summary>

**题目背景**:文心一言团队核心题,考察 Function Calling 从原理到工程的完整理解。

#### 一、Function Calling 是什么

让 LLM 能够"调用外部函数",从而:
- 获取实时信息(天气、股票)
- 执行计算(数学、单位转换)
- 操作外部系统(发邮件、订机票)
- 访问私有数据(数据库查询)

#### 二、实现原理

**2.1 训练阶段**

```
┌─────────────────────────────────────┐
│ 1. 构造训练数据                      │
│    用户 Query + 工具描述 + 期望调用   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. SFT 训练                         │
│    输入:Query + Tools Schema        │
│    输出:tool_call JSON              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. RLHF 优化                        │
│    奖励:调用正确性 + 用户体验        │
└─────────────────────────────────────┘
```

**训练数据格式**:
```json
{
  "messages": [
    {"role": "user", "content": "北京明天天气怎么样?"},
    {"role": "assistant", "content": null,
     "tool_calls": [{
       "name": "get_weather",
       "arguments": {"city": "北京", "date": "明天"}
     }]},
    {"role": "tool", "name": "get_weather",
     "content": "{\"temp\": 15, \"weather\": \"晴\"}"},
    {"role": "assistant", "content": "北京明天天气晴,气温 15°C。"}
  ],
  "tools": [{
    "name": "get_weather",
    "description": "查询指定城市天气",
    "parameters": {
      "type": "object",
      "properties": {
        "city": {"type": "string", "description": "城市名"},
        "date": {"type": "string", "description": "日期"}
      }
    }
  }]
}
```

**2.2 推理阶段**

```python
def function_calling(query, tools, llm):
    # 1. 构造 Prompt(注入工具描述)
    prompt = build_prompt(query, tools)
    # 2. LLM 决策:调用工具 or 直接回答
    response = llm.generate(prompt)
    # 3. 解析 tool_call
    if response.has_tool_call:
        tool_name = response.tool_call.name
        args = response.tool_call.arguments
        # 4. 执行工具
        result = execute_tool(tool_name, args)
        # 5. 二次调用 LLM,融合结果
        final_answer = llm.generate(query, tool_result=result)
        return final_answer
    else:
        return response.content
```

#### 三、关键技术点

**3.1 工具描述格式**
- OpenAI 风格:JSON Schema
- 文心风格:类似但有自己的 schema 扩展
- **难点**:工具数量多时,prompt 过长

**3.2 工具选择策略**

| 策略 | 描述 | 优势 | 劣势 |
|------|------|------|------|
| 全量注入 | 所有工具 schema 塞进 prompt | 简单 | token 爆炸 |
| 检索式 | 先检索相关工具,再注入 | 节省 token | 检索准确率 |
| 分层路由 | 先分类,再选工具 | 高效 | 分类错误传播 |
| 函数名 embedding | 向量检索工具 | 灵活 | 描述不充分时失效 |

```python
# 检索式工具选择
def select_tools(query, tool_db, top_k=5):
    query_vec = embed(query)
    tool_vecs = [embed(t.description) for t in tool_db]
    scores = cosine_similarity(query_vec, tool_vecs)
    top_tools = sorted(zip(tool_db, scores), key=lambda x: -x[1])[:top_k]
    return [t for t, s in top_tools]
```

**3.3 多工具调用(并行/串行)**

```python
# 并行调用:多个独立工具同时执行
def parallel_tool_calls(tool_calls):
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(execute_tool, tc) for tc in tool_calls]
        results = [f.result() for f in futures]
    return results

# 串行调用:有依赖关系的工具链
def sequential_tool_calls(tool_calls, dependencies):
    # 拓扑排序后依次执行
    order = topological_sort(tool_calls, dependencies)
    results = {}
    for tc in order:
        tc.args = resolve_args(tc.args, results)  # 注入前序结果
        results[tc.id] = execute_tool(tc)
    return results
```

**3.4 参数提取与校验**
- LLM 生成的参数可能不合法
- 用 JSON Schema 校验
- 不合法时反问用户或重生成

**3.5 错误处理**
- 工具调用失败:重试 / 降级 / 提示用户
- 参数错误:反馈给 LLM 重新生成
- 超时:默认值 / 兜底回答

#### 四、优化方向

**优化一:准确率提升**
- 高质量 SFT 数据(10万+)
- DPO 对齐:正确调用 > 错误调用 > 不调用
- 工具描述优化:加 few-shot 示例

**优化二:延迟降低**
- 流式输出 tool_call,边生成边执行
- 工具预加载:预测可能调用的工具,预热连接
- Speculative Decoding

**优化三:成本降低**
- 简单 Query 用小模型判断是否需要工具
- 工具调用结果缓存(相同参数直接返回)
- 减少 prompt 长度(工具描述压缩)

**优化四:安全**
- 工具白名单
- 敏感工具人工确认(发邮件/转账)
- 参数沙箱校验(防注入)

#### 五、文心一言 Function Calling 特色

- **ERNIE 定制训练**:Function Calling 数据混入预训练
- **千帆平台集成**:可视化配置工具
- **插件生态**:官方 + 第三方插件市场
- **中文优化**:对中文工具名/参数理解更准

#### 六、面试加分

- **提到 ReAct**:Thought-Action-Observation 范式
- **提到 Toolformer**:Meta 的工具学习论文
- **提到 Gorilla**:UC Berkeley 的工具调用模型
- **提到与 LangChain/AutoGPT 的关系**:Function Calling 是这些框架的底层能力

</details>

---

### Q9: 手撕代码 — 实现一个搜索增强 Agent(查询理解 / 搜索调用 / 结果抽取 / 答案生成 / 引用溯源)

<details>
<summary>展开完整代码</summary>

**题目要求**:实现一个完整的搜索增强 Agent,包含五个核心模块。Python 实现,可直接运行(用 mock 数据)。

```python
"""
搜索增强 Agent(Search-Augmented Agent)
=====================================
模块:
1. QueryUnderstanding  - 查询理解(意图识别 + 实体识别 + Query 改写)
2. SearchEngine        - 搜索调用(模拟多路召回 + 排序)
3. AnswerExtractor     - 答案抽取(段落级抽取)
4. AnswerGenerator     - 答案生成(LLM + 引用)
5. CitationTracker     - 引用溯源(句子级引用)
"""

import re
import json
import time
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


# ============================================================
# 数据结构定义
# ============================================================

class Intent(Enum):
    """查询意图"""
    FACTUAL = "factual"        # 事实型(谁/什么时候/哪里)
    COMPARATIVE = "comparative"  # 对比型(A vs B)
    PROCEDURAL = "procedural"   # 流程型(怎么做)
    OPINION = "opinion"        # 观点型(好不好)
    NAVIGATIONAL = "navigational"  # 导航型(官网)


@dataclass
class Entity:
    """实体"""
    text: str
    type: str  # person/location/time/organization/...
    start: int
    end: int


@dataclass
class Document:
    """检索文档"""
    doc_id: str
    title: str
    content: str
    url: str
    score: float = 0.0
    source: str = ""  # 来源(web/kg/news...)


@dataclass
class AnswerCandidate:
    """答案候选片段"""
    text: str
    doc_id: str
    score: float
    start: int = 0
    end: int = 0


@dataclass
class Citation:
    """引用"""
    citation_id: int
    doc_id: str
    title: str
    url: str
    snippet: str


@dataclass
class AgentResponse:
    """Agent 最终响应"""
    answer: str
    citations: List[Citation]
    reasoning: str
    intent: str
    entities: List[Dict]
    latency_ms: float


# ============================================================
# 模块 1:查询理解
# ============================================================

class QueryUnderstanding:
    """查询理解:意图识别 + 实体识别 + Query 改写"""

    # 意图关键词规则(实际用模型,这里用规则模拟)
    INTENT_RULES = {
        Intent.FACTUAL: ["谁", "什么时候", "哪里", "哪一年", "多少"],
        Intent.COMPARATIVE: ["对比", "比较", "区别", "vs", "和...哪个"],
        Intent.PROCEDURAL: ["怎么", "如何", "步骤", "方法"],
        Intent.OPINION: ["好不好", "怎么样", "推荐"],
        Intent.NAVIGATIONAL: ["官网", "网站", "首页"],
    }

    # 实体类型词典(实际用 NER 模型)
    ENTITY_DICT = {
        "person": ["姚明", "叶莉", "李彦宏", "马化腾", "雷军"],
        "location": ["北京", "上海", "深圳", "杭州", "广州"],
        "organization": ["百度", "腾讯", "阿里巴巴", "字节跳动"],
        "time": ["今天", "明天", "昨天", "2024年", "2025年"],
    }

    # 同义词改写
    SYNONYM_MAP = {
        "价格": ["售价", "多少钱", "价位"],
        "老婆": ["妻子", "配偶"],
        "老公": ["丈夫"],
        "公司": ["企业", "组织"],
    }

    def understand(self, query: str, context: Optional[str] = None) -> Dict:
        """完整查询理解流程"""
        start_time = time.time()

        # 1. 多轮上下文拼接(指代消解)
        resolved_query = self.resolve_coreference(query, context)

        # 2. 意图识别
        intent = self.classify_intent(resolved_query)

        # 3. 实体识别
        entities = self.extract_entities(resolved_query)

        # 4. Query 改写
        rewritten = self.rewrite_query(resolved_query, intent, entities)

        # 5. 子 Query 拆分(对比型)
        sub_queries = self.split_query(resolved_query, intent)

        return {
            "original": query,
            "resolved": resolved_query,
            "rewritten": rewritten,
            "intent": intent.value,
            "entities": [{"text": e.text, "type": e.type} for e in entities],
            "sub_queries": sub_queries,
            "latency_ms": (time.time() - start_time) * 1000,
        }

    def resolve_coreference(self, query: str, context: Optional[str]) -> str:
        """指代消解(简化版)"""
        if not context:
            return query
        # 简化:把"他"替换为上下文最后一个人物实体
        pronouns = ["他", "她", "它", "他们"]
        last_entity = context.split()[-1] if context else ""
        for p in pronouns:
            if p in query and last_entity:
                query = query.replace(p, last_entity)
        return query

    def classify_intent(self, query: str) -> Intent:
        """意图分类(规则版,实际用模型)"""
        for intent, keywords in self.INTENT_RULES.items():
            for kw in keywords:
                if kw in query.lower():
                    return intent
        return Intent.FACTUAL  # 默认事实型

    def extract_entities(self, query: str) -> List[Entity]:
        """实体识别(词典版)"""
        entities = []
        for ent_type, words in self.ENTITY_DICT.items():
            for word in words:
                idx = query.find(word)
                while idx != -1:
                    entities.append(Entity(
                        text=word, type=ent_type,
                        start=idx, end=idx + len(word)
                    ))
                    idx = query.find(word, idx + 1)
        return entities

    def rewrite_query(self, query: str, intent: Intent,
                      entities: List[Entity]) -> str:
        """Query 改写:同义扩展"""
        rewritten = query
        for word, syns in self.SYNONYM_MAP.items():
            if word in rewritten:
                # 加入第一个同义词作为扩展
                rewritten += f" {syns[0]}"
        return rewritten

    def split_query(self, query: str, intent: Intent) -> List[str]:
        """对比型 Query 拆分"""
        if intent != Intent.COMPARATIVE:
            return [query]
        # 简化:按"和"/"vs"拆分
        if "和" in query:
            parts = query.split("和", 1)
            return [p.strip() for p in parts]
        if "vs" in query.lower():
            parts = re.split(r"vs", query, flags=re.IGNORECASE)
            return [p.strip() for p in parts]
        return [query]


# ============================================================
# 模块 2:搜索引擎(模拟)
# ============================================================

class SearchEngine:
    """搜索引擎:多路召回 + 排序(用 mock 数据模拟)"""

    # 模拟文档库
    MOCK_DOCS = [
        Document(
            doc_id="d1",
            title="姚明 - 百度百科",
            content="姚明,1980年生于上海市,前中国职业篮球运动员,司职中锋。"
                    "姚明的妻子是叶莉,两人于2007年结婚。"
                    "姚明曾效力于休斯顿火箭队,2011年退役。"
                    "现任中国篮球协会主席。",
            url="https://baike.baidu.com/item/姚明",
            source="web"
        ),
        Document(
            doc_id="d2",
            title="叶莉 - 百度百科",
            content="叶莉,1981年出生于上海,前中国女子篮球运动员。"
                    "2007年与姚明结婚,育有一女姚沁蕾。",
            url="https://baike.baidu.com/item/叶莉",
            source="web"
        ),
        Document(
            doc_id="d3",
            title="姚明职业生涯回顾 - 新浪体育",
            content="姚明是 NBA 历史上最成功的中国球员, "
                    "2002年以状元身份加盟火箭队。"
                    "职业生涯场均19分9.2篮板。",
            url="https://sports.sina.com.cn/yao",
            source="news"
        ),
        Document(
            doc_id="d4",
            title="上海简介 - 维基百科",
            content="上海是中国直辖市,位于长江入海口。"
                    "常住人口约2500万,2024年GDP达4.7万亿元。",
            url="https://zh.wikipedia.org/wiki/上海",
            source="web"
        ),
    ]

    # 倒排索引(简化)
    def _build_inverted_index(self) -> Dict[str, List[str]]:
        index = defaultdict(list)
        for doc in self.MOCK_DOCS:
            # 简单分词(按字)
            for i in range(len(doc.content) - 1):
                word = doc.content[i:i+2]
                index[word].append(doc.doc_id)
        return index

    def __init__(self):
        self.inverted_index = self._build_inverted_index()

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """搜索:多路召回 + 排序"""
        # 1. 倒排召回(BM25 模拟)
        bm25_results = self._bm25_search(query)
        # 2. 向量召回(用词重叠模拟)
        vec_results = self._vector_search(query)
        # 3. 融合去重
        fused = self._fuse(bm25_results, vec_results)
        # 4. 排序
        ranked = self._rank(fused, query)
        return ranked[:top_k]

    def _bm25_search(self, query: str) -> List[Document]:
        """BM25 倒排召回"""
        scores = defaultdict(float)
        for i in range(len(query) - 1):
            word = query[i:i+2]
            for doc_id in self.inverted_index.get(word, []):
                scores[doc_id] += 1.0
        results = []
        for doc in self.MOCK_DOCS:
            if doc.doc_id in scores:
                doc_copy = Document(
                    doc_id=doc.doc_id, title=doc.title,
                    content=doc.content, url=doc.url,
                    score=scores[doc.doc_id], source=doc.source
                )
                results.append(doc_copy)
        return sorted(results, key=lambda x: -x.score)

    def _vector_search(self, query: str) -> List[Document]:
        """向量召回(用字符重叠模拟)"""
        query_chars = set(query)
        results = []
        for doc in self.MOCK_DOCS:
            doc_chars = set(doc.content + doc.title)
            overlap = len(query_chars & doc_chars)
            if overlap > 0:
                score = overlap / len(query_chars)
                doc_copy = Document(
                    doc_id=doc.doc_id, title=doc.title,
                    content=doc.content, url=doc.url,
                    score=score * 0.8, source=doc.source  # 向量权重略低
                )
                results.append(doc_copy)
        return sorted(results, key=lambda x: -x.score)

    def _fuse(self, *result_lists) -> List[Document]:
        """多路融合(RRF 简化版)"""
        fused_scores = defaultdict(float)
        doc_map = {}
        for results in result_lists:
            for rank, doc in enumerate(results):
                # RRF: 1 / (k + rank)
                fused_scores[doc.doc_id] += 1.0 / (60 + rank)
                doc_map[doc.doc_id] = doc
        result = []
        for doc_id, score in fused_scores.items():
            doc = doc_map[doc_id]
            doc.score = score
            result.append(doc)
        return result

    def _rank(self, docs: List[Document], query: str) -> List[Document]:
        """精排(用查询相关度)"""
        for doc in docs:
            # 标题命中加权
            if any(w in doc.title for w in query.split()):
                doc.score *= 1.5
            # 时效性(新闻加分)
            if doc.source == "news":
                doc.score *= 1.1
        return sorted(docs, key=lambda x: -x.score)


# ============================================================
# 模块 3:答案抽取
# ============================================================

class AnswerExtractor:
    """答案抽取:从文档中抽取候选答案片段"""

    def extract(self, query: str, docs: List[Document],
                top_k: int = 5) -> List[AnswerCandidate]:
        """抽取答案候选"""
        candidates = []
        for doc in docs:
            # 按句子切分
            sentences = self._split_sentences(doc.content)
            for sent in sentences:
                score = self._score_sentence(query, sent, doc)
                if score > 0:
                    candidates.append(AnswerCandidate(
                        text=sent,
                        doc_id=doc.doc_id,
                        score=score
                    ))
        # 排序取 Top-K
        candidates.sort(key=lambda x: -x.score)
        return candidates[:top_k]

    def _split_sentences(self, text: str) -> List[str]:
        """句子切分(中文)"""
        # 按句号/问号/感叹号切分
        sentences = re.split(r"[。?!;]", text)
        return [s.strip() for s in sentences if s.strip()]

    def _score_sentence(self, query: str, sentence: str,
                        doc: Document) -> float:
        """句子打分(相关度)"""
        score = 0.0
        # 字符重叠
        query_chars = set(query)
        sent_chars = set(sentence)
        overlap = len(query_chars & sent_chars)
        score += overlap / max(len(query_chars), 1)
        # 文档得分加权
        score *= (1 + doc.score)
        # 长度惩罚(太长太短都不好)
        if len(sentence) < 5 or len(sentence) > 100:
            score *= 0.5
        return score


# ============================================================
# 模块 4:引用追踪
# ============================================================

class CitationTracker:
    """引用溯源:管理引用与答案的对应关系"""

    def __init__(self):
        self.citations: List[Citation] = []
        self.citation_map: Dict[int, Citation] = {}

    def add_citation(self, doc: Document, snippet: str) -> int:
        """添加引用,返回引用 ID"""
        # 去重:相同 doc 不重复添加
        for cid, cite in self.citation_map.items():
            if cite.doc_id == doc.doc_id:
                return cid
        cite_id = len(self.citations) + 1
        citation = Citation(
            citation_id=cite_id,
            doc_id=doc.doc_id,
            title=doc.title,
            url=doc.url,
            snippet=snippet[:100] + "..." if len(snippet) > 100 else snippet
        )
        self.citations.append(citation)
        self.citation_map[cite_id] = citation
        return cite_id

    def get_citation_marker(self, cite_id: int) -> str:
        """获取引用标记,如 [1]"""
        return f"[{cite_id}]"

    def format_citations(self) -> str:
        """格式化引用列表"""
        lines = ["\n\n参考来源:"]
        for cite in self.citations:
            lines.append(f"[{cite.citation_id}] {cite.title} - {cite.url}")
        return "\n".join(lines)


# ============================================================
# 模块 5:答案生成器(模拟 LLM)
# ============================================================

class AnswerGenerator:
    """答案生成:基于检索结果生成最终答案(模拟 LLM)"""

    def __init__(self):
        self.citation_tracker = CitationTracker()

    def generate(self, query: str, docs: List[Document],
                 candidates: List[AnswerCandidate],
                 query_info: Dict) -> Tuple[str, str]:
        """生成答案 + 推理过程"""
        if not candidates:
            return "抱歉,未找到相关信息。", "无相关文档"

        # 构造推理过程
        reasoning = self._build_reasoning(query, docs, candidates, query_info)

        # 生成答案(模拟:拼接候选 + 引用)
        answer_parts = []
        seen_sents = set()
        for cand in candidates[:3]:  # 取 Top-3
            if cand.text in seen_sents:
                continue
            seen_sents.add(cand.text)
            # 找到对应文档
            doc = next(d for d in docs if d.doc_id == cand.doc_id)
            # 添加引用
            cite_id = self.citation_tracker.add_citation(doc, cand.text)
            marker = self.citation_tracker.get_citation_marker(cite_id)
            answer_parts.append(f"{cand.text}{marker}")

        answer = "。".join(answer_parts) + "。"
        answer += self.citation_tracker.format_citations()
        return answer, reasoning

    def _build_reasoning(self, query: str, docs: List[Document],
                         candidates: List[AnswerCandidate],
                         query_info: Dict) -> str:
        """构造推理过程(可解释)"""
        steps = [
            f"1. 查询理解:意图={query_info['intent']},"
            f"实体={[e['text'] for e in query_info['entities']]}",
            f"2. 检索召回:获取 {len(docs)} 篇相关文档",
            f"3. 答案抽取:抽取 {len(candidates)} 个候选片段",
            f"4. 答案合成:选取 Top-{min(3, len(candidates))} 候选,"
            f"添加引用溯源",
        ]
        return "\n".join(steps)


# ============================================================
# 搜索增强 Agent(编排所有模块)
# ============================================================

class SearchAugmentedAgent:
    """搜索增强 Agent:完整链路编排"""

    def __init__(self):
        self.query_understander = QueryUnderstanding()
        self.search_engine = SearchEngine()
        self.answer_extractor = AnswerExtractor()
        self.answer_generator = AnswerGenerator()

    def answer(self, query: str,
               context: Optional[str] = None) -> AgentResponse:
        """Agent 完整回答流程"""
        total_start = time.time()

        # Step 1: 查询理解
        print(f"\n[Step 1] 查询理解...")
        query_info = self.query_understander.understand(query, context)
        print(f"  意图: {query_info['intent']}")
        print(f"  实体: {query_info['entities']}")
        print(f"  改写: {query_info['rewritten']}")

        # Step 2: 搜索召回
        print(f"\n[Step 2] 搜索召回...")
        search_query = query_info["rewritten"]
        docs = self.search_engine.search(search_query, top_k=5)
        print(f"  召回 {len(docs)} 篇文档:")
        for d in docs:
            print(f"    - [{d.doc_id}] {d.title} (score={d.score:.3f})")

        # Step 3: 答案抽取
        print(f"\n[Step 3] 答案抽取...")
        candidates = self.answer_extractor.extract(query, docs, top_k=5)
        print(f"  抽取 {len(candidates)} 个候选:")
        for c in candidates:
            print(f"    - [{c.doc_id}] {c.text[:50]}... "
                  f"(score={c.score:.3f})")

        # Step 4: 答案生成
        print(f"\n[Step 4] 答案生成...")
        answer, reasoning = self.answer_generator.generate(
            query, docs, candidates, query_info
        )
        print(f"  推理过程:\n{reasoning}")

        latency = (time.time() - total_start) * 1000

        return AgentResponse(
            answer=answer,
            citations=self.answer_generator.citation_tracker.citations,
            reasoning=reasoning,
            intent=query_info["intent"],
            entities=query_info["entities"],
            latency_ms=latency
        )


# ============================================================
# 运行测试
# ============================================================

def main():
    """主函数:测试搜索增强 Agent"""
    agent = SearchAugmentedAgent()

    test_cases = [
        "姚明的妻子是谁?",
        "姚明是哪一年出生的?",
        "上海的人口有多少?",
        "姚明和叶莉什么时候结婚的?",
    ]

    for query in test_cases:
        print("\n" + "=" * 60)
        print(f"用户问题: {query}")
        print("=" * 60)

        response = agent.answer(query)

        print("\n" + "-" * 60)
        print("最终答案:")
        print(response.answer)
        print(f"\n[总延迟: {response.latency_ms:.1f}ms]")
        print("-" * 60)


if __name__ == "__main__":
    main()
```

**运行输出示例**:

```
============================================================
用户问题: 姚明的妻子是谁?
============================================================

[Step 1] 查询理解...
  意图: factual
  实体: [{'text': '姚明', 'type': 'person'}]
  改写: 姚明的妻子是谁? 配偶

[Step 2] 搜索召回...
  召回 4 篇文档:
    - [d1] 姚明 - 百度百科 (score=0.033)
    - [d2] 叶莉 - 百度百科 (score=0.025)
    - [d3] 姚明职业生涯回顾 - 新浪体育 (score=0.020)
    - [d4] 上海简介 - 维基百科 (score=0.017)

[Step 3] 答案抽取...
  抽取 5 个候选:
    - [d1] 姚明的妻子是叶莉,两人于2007年结婚 (score=2.033)
    - [d2] 2007年与姚明结婚,育有一女姚沁蕾 (score=1.525)
    ...

[Step 4] 答案生成...
  推理过程:
1. 查询理解:意图=factual,实体=['姚明']
2. 检索召回:获取 4 篇相关文档
3. 答案抽取:抽取 5 个候选片段
4. 答案合成:选取 Top-3 候选,添加引用溯源

------------------------------------------------------------
最终答案:
姚明的妻子是叶莉,两人于2007年结婚[1]。2007年与姚明结婚,育有一女姚沁蕾[2]。姚明,1980年生于上海市,前中国职业篮球运动员,司职中锋[1]。

参考来源:
[1] 姚明 - 百度百科 - https://baike.baidu.com/item/姚明
[2] 叶莉 - 百度百科 - https://baike.baidu.com/item/叶莉

[总延迟: 12.3ms]
------------------------------------------------------------
```

**代码亮点**:
1. **完整五模块**:查询理解 + 搜索 + 抽取 + 生成 + 引用
2. **可解释推理**:输出推理过程,便于调试
3. **引用溯源**:每个答案句子标注来源
4. **多路召回融合**:BM25 + 向量,RRF 融合
5. **延迟统计**:每个环节计时
6. **易扩展**:用 mock 数据,真实场景替换为模型即可

</details>

---

### Q10: 系统设计 — 设计一个社交场景的 AI Agent(微信群助手),支持多人群聊理解 / 任务分配 / 隐私保护

<details>
<summary>展开答案</summary>

**题目背景**:腾讯微信 AI 真题,考察复杂社交场景下的 Agent 架构能力,特别是多人、隐私、边界感设计。

#### 一、需求分析

**功能需求**:
1. **多人群聊理解**:理解 10-500 人群聊的上下文,识别话题、关键人、待办
2. **任务分配**:从聊天中识别任务,自动 @ 责任人,跟踪进度
3. **隐私保护**:不泄露未发言者信息,不存储敏感内容,用户可控
4. **主动服务**:适时介入(摘要/提醒/答疑),不 spam

**非功能需求**:
- 群聊规模:10-500 人
- 消息量:日均 1000-10000 条
- 响应延迟:被动 < 2s,主动 > 30s(避免打扰)
- 可用性:99.9%
- 隐私:符合《个人信息保护法》

**场景示例**:
```
群"产品评审组"(20人)
张三:下周三要做 V2.0 评审,谁负责 PPT?
李四:@王五 你之前做的模板不错,你来?
王五:OK,我周三前出初稿
[AI 助手应识别]:
- 任务:V2.0 评审 PPT
- 责任人:王五
- 截止:下周三
- 主动提醒:下周二检查进度
```

#### 二、整体架构

```
┌─────────────────────────────────────────────────────────┐
│                  微信群聊客户端                          │
│   消息流 → AI 助手触发器 → UI 卡片展示                  │
└────────────────────────┬────────────────────────────────┘
                         │ 消息流(脱敏后)
┌────────────────────────┴────────────────────────────────┐
│                  AI 助手网关                             │
│   鉴权 / 限流 / 隐私脱敏 / 审计                          │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│            群聊 Agent 编排层(Multi-Agent)              │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │理解 Agent│  │任务 Agent│  │摘要 Agent│  │提醒Agent│ │
│  │Understand│  │  Task    │  │ Summary  │  │ Reminder│ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│        ↓             ↓             ↓             ↓       │
│  ┌──────────────────────────────────────────────────┐   │
│  │           共享记忆层(Group Memory)              │   │
│  │   群画像 / 话题历史 / 任务池 / 用户偏好           │   │
│  └──────────────────────────────────────────────────┘   │
│        ↓             ↓             ↓             ↓       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ 混元 LLM │  │NER 模型  │  │ 摘要模型 │  │定时调度 │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────┘
```

#### 三、核心模块详解

**3.1 群聊理解 Agent(Understand Agent)**

目标:实时理解群聊动态,产出结构化信号。

```python
@dataclass
class GroupContext:
    """群聊上下文"""
    group_id: str
    topic: str               # 当前话题
    active_speakers: List[str]  # 活跃发言者
    key_persons: List[str]    # 关键人物(决策者)
    sentiment: str           # 群体情绪
    pending_questions: List[str]  # 未回答的问题
    recent_messages: List[Dict]   # 最近 N 条


class UnderstandAgent:
    def __init__(self):
        self.topic_model = load_model("topic-clf")  # 话题分类
        self.ner = load_model("ernie-ner")           # 实体识别
        self.sentiment_model = load_model("senti")   # 情感分析

    def understand(self, messages: List[Dict],
                   history: GroupContext) -> GroupContext:
        # 1. 话题识别(每 10 条消息更新一次)
        if len(messages) % 10 == 0:
            history.topic = self.topic_model.predict(messages[-20:])
        # 2. 活跃度统计
        speaker_counts = Counter(m["sender"] for m in messages[-50:])
        history.active_speakers = speaker_counts.most_common(5)
        # 3. 关键人物识别(@某人/被@/决策词)
        history.key_persons = self._identify_key_persons(messages)
        # 4. 情感分析
        history.sentiment = self.sentiment_model.predict(messages[-10:])
        # 5. 未回答问题检测
        history.pending_questions = self._detect_questions(messages)
        return history

    def _identify_key_persons(self, messages):
        """识别关键人物:被 @ 多 / 出现决策词"""
        key_words = ["决定", "拍板", "就这么定", "同意", "OK"]
        ...
        return key_persons

    def _detect_questions(self, messages):
        """检测未回答的问题"""
        questions = []
        for m in messages:
            if "?" in m["content"] or "?" in m["content"]:
                # 检查后续 5 条是否有回答
                if not self._has_reply(m, messages):
                    questions.append(m)
        return questions
```

**3.2 任务分配 Agent(Task Agent)**

目标:从聊天中识别任务,自动 @ 责任人,跟踪进度。

```python
@dataclass
class Task:
    task_id: str
    description: str       # 任务描述
    assignee: str          # 责任人
    deadline: str          # 截止时间
    status: str            # pending/in_progress/done
    created_at: str
    related_messages: List[str]  # 相关消息


class TaskAgent:
    def __init__(self):
        self.llm = HunYuanLLM()
        self.task_store = TaskStore()  # 持久化

    def detect_and_assign(self, messages, group_ctx):
        """检测任务并分配"""
        # 1. LLM 抽取任务
        prompt = self._build_prompt(messages, group_ctx)
        tasks = self.llm.extract(prompt)
        # 2. 校验任务合理性
        valid_tasks = [t for t in tasks if self._validate(t, group_ctx)]
        # 3. 持久化
        for t in valid_tasks:
            self.task_store.save(t)
            # 4. 主动 @ 责任人确认
            self._notify_assignee(t)
        return valid_tasks

    def _build_prompt(self, messages, ctx):
        return f"""
你是群聊任务助手。从以下消息中识别待办任务。
群当前话题: {ctx.topic}
活跃成员: {ctx.active_speakers}

最近消息:
{format_messages(messages[-20:])}

请输出 JSON 数组,每个任务包含:
- description: 任务描述
- assignee: 责任人(必须@到具体人)
- deadline: 截止时间(ISO 8601,模糊则不填)
- confidence: 置信度(0-1)
只输出 confidence > 0.7 的任务。
"""

    def _validate(self, task, ctx):
        """校验任务合理性"""
        # 责任人必须在群里
        if task.assignee not in ctx.active_speakers:
            return False
        # 截止时间不能是过去
        if task.deadline and is_past(task.deadline):
            return False
        return True

    def track_progress(self, task_id, new_messages):
        """跟踪任务进度"""
        task = self.task_store.get(task_id)
        # 检查是否有完成信号
        for m in new_messages:
            if m["sender"] == task.assignee:
                if any(kw in m["content"]
                       for kw in ["完成了", "已提交", "done"]):
                    task.status = "done"
                    self.task_store.update(task)
                    return True
        return False
```

**3.3 主动介入策略(Reminder Agent)**

目标:决定 AI 何时主动说话,避免打扰。

```python
class ReminderAgent:
    """主动提醒:基于规则 + LLM 判断"""

    def should_intervene(self, group_ctx, trigger_type):
        """决定是否介入"""
        # 规则一:刚有人发言,避免打断
        if time_since_last_msg() < 30:
            return False
        # 规则二:深夜不主动
        if current_hour() < 8 or current_hour() > 22:
            return False
        # 规则三:用户设置勿扰
        if group_ctx.do_not_disturb:
            return False
        # 规则四:今日主动次数未超限
        if group_ctx.today_interventions >= 3:
            return False
        # 规则五:触发类型判断
        if trigger_type == "task_deadline":
            return True  # 任务截止必提醒
        if trigger_type == "unanswered_question":
            return time_since_question() > 300  # 5 分钟未回答
        if trigger_type == "summary":
            return group_ctx.unread_count > 100  # 100 条未读
        return False

    def intervene(self, group_ctx, trigger_type):
        """执行介入"""
        if not self.should_intervene(group_ctx, trigger_type):
            return None
        if trigger_type == "task_deadline":
            return self._remind_task()
        elif trigger_type == "unanswered_question":
            return self._answer_question()
        elif trigger_type == "summary":
            return self._summarize()
```

**3.4 隐私保护模块(Privacy Module)**

这是本题最关键的差异化设计。

```python
class PrivacyModule:
    """隐私保护:脱敏 / 授权 / 审计"""

    # 敏感信息正则
    SENSITIVE_PATTERNS = {
        "phone": r"1[3-9]\d{9}",
        "id_card": r"\d{17}[\dXx]",
        "bank_card": r"\d{16,19}",
        "email": r"[\w.-]+@[\w.-]+\.\w+",
        "address": r"[\u4e00-\u9fa5]{2,}(省|市|区|县|路|街|号)",
    }

    def desensitize(self, message: Dict) -> Dict:
        """脱敏处理"""
        content = message["content"]
        for pii_type, pattern in self.SENSITIVE_PATTERNS.items():
            content = re.sub(pattern, f"[{pii_type}]", content)
        message["content"] = content
        return message

    def filter_unspoken(self, messages, group_members):
        """过滤未发言者信息"""
        spoken = {m["sender"] for m in messages}
        # AI 只能"看到"发言过的人
        visible_members = [m for m in group_members if m in spoken]
        return visible_members

    def check_consent(self, user_id, action):
        """检查用户授权"""
        consent = self.consent_store.get(user_id)
        return consent.get(action, False)

    def audit_log(self, action, user_id, group_id, detail):
        """审计日志:可追溯"""
        log = {
            "timestamp": now(),
            "action": action,
            "user_id": hash(user_id),  # 哈希存储
            "group_id": hash(group_id),
            "detail": detail,
        }
        self.audit_store.save(log)
```

**隐私保护的五层设计**:

| 层级 | 措施 | 说明 |
|------|------|------|
| 数据采集 | 最小化 | 只采集必要消息,不抓取群成员列表 |
| 数据传输 | 端到端加密 | 客户端到服务端加密 |
| 数据处理 | 实时脱敏 | PII 替换为占位符 |
| 数据存储 | 不持久化原文 | 处理完即删,只存结构化结果 |
| 数据使用 | 用户授权 | 每类功能独立授权,可撤回 |

#### 四、关键挑战与解法

**挑战一:群聊噪声大**
- 问题:500 人群消息混杂,任务识别准确率低
- 解法:
  - 话题分桶,只在相关话题内识别
  - 多模型投票(规则 + LLM + NER)
  - 置信度阈值 + 用户反馈学习

**挑战二:多指代消解**
- 问题:"让他来做"——"他"是谁?
- 解法:
  - 上下文窗口内做指代消解
  - 结合 @ 信息和发言顺序
  - 不确定时不分配,反问群内

**挑战三:边界感(何时介入)**
- 问题:AI 太主动招人烦,太被动无价值
- 解法:
  - 严格规则 + LLM 判断双保险
  - 用户反馈环(被 @ 或被赞 → 提升;被忽略 → 降低)
  - 分群策略(工作群主动,闲聊群被动)

**挑战四:跨设备同步**
- 问题:手机/PC/平板,任务状态需同步
- 解法:服务端统一存储,客户端增量同步

**挑战五:成本控制**
- 问题:500 人群每天 1 万条消息,全过 LLM 成本爆炸
- 解法:
  - 分层处理:80% 消息用小模型,20% 用大模型
  - 增量处理:只处理新增消息
  - 缓存:相似 Query 复用结果

#### 五、评估指标

| 维度 | 指标 | 目标 |
|------|------|------|
| 任务识别 | 准确率 | > 85% |
| 任务识别 | 召回率 | > 75% |
| 介入合理性 | 用户接受率 | > 70% |
| 介入合理性 | 打扰投诉率 | < 5% |
| 隐私 | PII 泄露次数 | 0 |
| 延迟 | 被动响应 P99 | < 2s |
| 满意度 | NPS | > 40 |

#### 六、面试加分

- **提到 A/B 实验设计**:如何科学验证 AI 助手的价值
- **提到冷启动**:新群没有历史数据,如何启动
- **提到多语言**:海外群(WeChat 国际版)的处理
- **提到合规**:GDPR / 个人信息保护法
- **提到与微信生态结合**:小程序 / 视频号 / 朋友圈联动

</details>

---

## 核心知识回顾表

| 模块 | 腾讯重点 | 百度重点 | 通用要点 |
|------|---------|---------|---------|
| **面试风格** | 产品思维、低延迟、社交场景 | NLP 八股、搜索思维、KG 深度 | 系统设计 + 手撕代码 |
| **Agent 架构** | 多技能编排、端云协同 | 搜索增强、KG 增强 | ReAct + 工具调用 |
| **场景适配** | 微信/QQ/游戏 NPC | 搜索/客服/医疗 | SFT + DPO + 蒸馏 |
| **延迟优化** | KV Cache/流式/蒸馏 | 缓存/分级/量化 | 模型小 + 推理快 |
| **隐私安全** | 端侧优先、脱敏、授权 | 数据合规、审计 | 最小化采集 |
| **核心模块** | 意图路由/记忆/情感 | Query 理解/检索/抽取 | 规划 + 执行 + 反思 |
| **评估指标** | 用户留存、NPS、FCR | 准确率、MRR、覆盖率 | 业务 + 技术 |
| **特色技术** | 混元/太极/MoE | 文心/知心/HUGEGRAPH | LLM + 工具 + 检索 |

### 腾讯 vs 百度 Agent 技术栈对比

| 维度 | 腾讯 | 百度 |
|------|------|------|
| 基座模型 | 混元(万亿参数 MoE) | 文心 ERNIE(多版本) |
| 训练框架 | 太极 / AngelPTM | PaddlePaddle / 飞桨 |
| 推理引擎 | 自研(混元推理) | 自研 + 开源结合 |
| 向量检索 | 内部(基于 FAISS) | BES(百度 ES) |
| 图数据库 | 内部图引擎 | HUGEGRAPH(开源) |
| Agent 平台 | 微信智能体平台 | 千帆大模型平台 |
| 知识图谱 | 偏业务场景 | 大规模通用 KG |
| 特色场景 | 社交、游戏、内容 | 搜索、地图、自动驾驶 |

### 大模型 Function Calling 横向对比

| 厂商 | 模型 | Function Calling 特色 |
|------|------|----------------------|
| 腾讯 | 混元 | 中文工具理解强,微信生态集成 |
| 百度 | 文心 | 千帆平台可视化编排,插件市场 |
| 字节 | 豆包 | Coze 平台,抖音/飞书生态 |
| 阿里 | 通义 | 百炼平台,电商/钉钉集成 |

---

## 面试速记卡

### 卡片 1:腾讯面试 30 秒自我介绍模板

```
面试官您好,我是 XXX,目前在做 Agent 方向,主要经验有:
1. 用 [混元/通义/GPT] 做过 [微信/QQ/客服/游戏] 场景的 Agent,
   日活 [X] 万,QPS [Y],延迟 P99 < [Z]ms;
2. 技术栈:ReAct + Function Calling + RAG + 多 Agent 协作;
3. 优化过 [KV Cache / 蒸馏 / 量化],成本降低 [N]%;
4. 对微信生态的社交场景 Agent 特别感兴趣,
   做过 [群聊助手 / 摘要 / 翻译] 的原型。
期待加入腾讯 [微信AI/混元/IEG] 团队,做出亿级用户的产品。
```

### 卡片 2:百度面试 30 秒自我介绍模板

```
面试官您好,我是 XXX,Agent 方向 [X] 年经验:
1. 做过 [搜索增强 / 知识图谱 / Function Calling] 相关项目,
   深入理解 [ERNIE/BERT/Transformer] 原理;
2. 在 [上家公司] 主导 [RAG/KBQA/智能客服] 系统,
   准确率从 [X]% 提升到 [Y]%;
3. 对搜索 + Agent 融合架构有深入实践,
   熟悉 [Query 理解/检索排序/答案抽取] 全链路;
4. 看过百度 [文心一言/千帆/知心] 的技术博客,
   对 [KG 增强 LLM / Function Calling 优化] 有自己的思考。
希望加入百度 [文心/搜索/KG] 团队,做大规模落地的 Agent。
```

### 卡片 3:系统设计万能框架

```
1. 需求澄清(2min):功能 + 非功能 + 规模
2. 容量估算(1min):QPS / 存储 / 带宽
3. 整体架构(3min):分层 + 模块 + 数据流
4. 核心模块深挖(8min):选 2-3 个最难的展开
5. 数据存储(2min):DB 选型 + 索引设计
6. 优化与 trade-off(3min):延迟/成本/准确性
7. 监控与容灾(1min):指标 + 降级方案
```

### 卡片 4:RAG 速记口诀

```
RAG 五步走:
一问(Query 理解:意图 + 实体 + 改写)
二找(检索:多路召回 + 排序)
三抽(抽取:段落/句子级)
四生(生成:LLM + 引用)
五验(校验:事实 + 一致性)
```

### 卡片 5:Agent 评估指标速记

```
Agent 三层评估:
- 模型层:准确率/召回率/BLEU/ROUGE
- 任务层:完成率/步骤数/纠错率
- 用户体验:NPS/留存/满意度/投诉率
```

---

## 易错点提醒(10 个)

1. **腾讯面试别只谈技术不谈产品**:腾讯面试官特别看重产品思维。答系统设计时,先讲用户场景和价值,再讲技术方案。直接画架构图不讲用户体验,基本挂。

2. **百度面试别答不出 NLP 八股**:百度是 NLP 老牌强厂,BERT/Transformer/位置编码/注意力机制这些基础必问。答"不太记得了"直接出局。建议面试前一天过一遍经典论文。

3. **延迟优化别只说"用小模型"**:这是面试大忌。正确回答应该包含:KV Cache 复用、Speculative Decoding、流式输出、模型蒸馏、量化(INT8/INT4)、分级调用。多维并举才显深度。

4. **群聊 Agent 别忽略"边界感"**:腾讯真题里"AI 何时介入"是核心考点。很多候选人只设计功能不设计"不作为"策略。必须包含:勿扰时段、介入频率限制、用户反馈环、分群策略。

5. **隐私保护别停留在"加密"**:社交场景隐私是系统工程,包含:最小化采集、端侧优先、实时脱敏、不持久化、用户授权、审计日志。只说"传输加密"太浅。

6. **Function Calling 别忽略错误处理**:很多候选人只讲 happy path。必须覆盖:工具不存在、参数错误、工具超时、工具返回异常、循环调用检测、成本控制。

7. **知识图谱别只说"三元组"**:百度面试官会追问"亿级 KG 怎么存?怎么查?怎么更新?"。必须答:图数据库选型(Neo4j/HUGEGRAPH)、多级缓存、子图预计算、增量更新、图分区。

8. **RAG 别只会"向量检索"**:完整 RAG 是 Query 理解 + 多路召回(倒排+向量+KG)+ 排序 + 抽取 + 生成 + 引用 + 校验。只说"embedding + 余弦相似度"显得太嫩。

9. **手撕代码别忽略引用溯源**:Q9 这种搜索 Agent 题,引用溯源是加分项。用 `[1][2]` 标记 + 底部参考来源列表,立刻显示出工程素养。

10. **系统设计别画完图就走**:画完架构图只是开始,面试官会追问:"瓶颈在哪?怎么扩展?挂了怎么办?成本多少?"。每个设计决策都要能说出 trade-off。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 1. 能说出腾讯 AI Lab / 微信 AI / 混元 / IEG 四个团队的考察侧重
- [ ] 2. 能画出微信智能助手 Agent 的完整架构(5 个技能 + 端云协同)
- [ ] 3. 能解释游戏 NPC Agent 的五大模块(感知/记忆/思考/情感/对话)
- [ ] 4. 能说出混元场景适配的三个层次(CPT → SFT → DPO)及 trade-off
- [ ] 5. 能说出百度面试与腾讯面试的 3 个核心差异
- [ ] 6. 能画出百度搜索 Agent 全链路(Query 理解 → 检索 → 抽取 → 生成)
- [ ] 7. 能说出知识图谱在 Agent 中的四大作用(事实/推理/消歧/可解释)
- [ ] 8. 能解释大规模 KG 构建的 6 步流程(本体 → 抽取 → 融合 → 存储 → 推理 → 评估)
- [ ] 9. 能说出 Function Calling 训练阶段和推理阶段的完整流程
- [ ] 10. 能说出 Function Calling 的 4 个优化方向(准确率/延迟/成本/安全)

### 代码题(3 个)

- [ ] 1. 能手撕搜索增强 Agent(查询理解 + 搜索 + 抽取 + 生成 + 引用),参考 Q9
- [ ] 2. 能实现多路召回融合(RRF 算法),输入多路文档列表,输出融合排序
- [ ] 3. 能实现 Function Calling 的工具选择器,输入 Query + 工具列表,输出 Top-K 工具

**代码题 2 参考骨架**:
```python
def rrf_fuse(result_lists, k=60):
    """RRF 多路融合"""
    scores = defaultdict(float)
    for results in result_lists:
        for rank, doc in enumerate(results):
            scores[doc.id] += 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])
```

**代码题 3 参考骨架**:
```python
def select_tools(query, tools, top_k=3):
    """工具选择:向量检索"""
    q_vec = embed(query)
    tool_vecs = [embed(t["description"]) for t in tools]
    scores = [cosine(q_vec, tv) for tv in tool_vecs]
    top_idx = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
    return [tools[i] for i in top_idx]
```

### 系统设计题(2 个)

- [ ] 1. 能独立完成"微信群助手 Agent"系统设计,覆盖多人群聊理解/任务分配/隐私保护,参考 Q10
- [ ] 2. 能独立完成"百度搜索 Agent"系统设计,覆盖 Query 理解/多路召回/答案抽取/引用溯源,参考 Q6

**自测方法**:闭卷在白纸上画出架构图 + 写出关键模块伪代码,然后对照答案查漏补缺。每个设计题限时 30 分钟。

---

## 延伸阅读

### 论文

| 论文 | 团队 | 与今日内容关系 |
|------|------|---------------|
| **HunYuan-Large** 論文 | 腾讯混元 | 混元 MoE 架构细节 |
| **ERNIE 4.0** 技术报告 | 百度文心 | 文心 Function Calling 训练 |
| **Toolformer** | Meta | Function Calling 经典论文 |
| **Gorilla** | UC Berkeley | 大规模工具调用 |
| **ReAct** | Princeton | Agent 推理 + 行动范式 |
| **RAG** (Lewis et al.) | Facebook | 检索增强生成奠基 |
| **GraphRAG** | Microsoft | KG + RAG 融合 |
| **Generative Agents** | Stanford | 多 Agent 社交模拟 |

### 博客与文档

- 腾讯混元技术博客:https://hunyuan.tencent.com/
- 百度文心一言:https://yiyan.baidu.com/
- 百度千帆平台:https://qianfan.cloud.baidu.com/
- 百度 HUGEGRAPH:https://hugegraph.apache.org/
- 腾讯 AI Lab 论文列表:https://ai.tencent.com/ailab/

### 往期回顾

- **Day 22**:字节跳动 Agent 面试专项(豆包/Coze/抖音场景)
- **Day 23**:阿里巴巴 Agent 面试专项(通义/百炼/电商场景)
- **Day 24**(今日):腾讯百度 Agent 面试专项
- **Day 25**(明日):美团蚂蚁 Agent 面试专项

### 推荐练习

1. **手撕练习**:把 Q9 的代码完整敲一遍,跑通后尝试替换 mock 模型为真实 API
2. **设计练习**:闭卷画 Q10 微信群助手的架构图,对照答案补全遗漏模块
3. **Mock 面试**:找同学互相出题,重点练腾讯的产品视角和百度的原理深度
4. **技术调研**:读一篇混元或文心的技术报告,总结 3 个面试可用的亮点

---

## 明日预告

### Day 25 — 美团蚂蚁 Agent 面试专项

明日将聚焦**美团**(外卖/到店/配送场景的 Agent 应用)和**蚂蚁集团**(支付宝/风控/客服 Agent)的面试题。

**美团方向**:
- 美团面试风格:重业务落地、ROI 思维
- 外卖智能客服 Agent 设计
- 配送调度 + Agent 决策
- 大规模实时推理优化

**蚂蚁方向**:
- 蚂蚁面试风格:重金融场景、安全合规
- 支付宝智能助理 Agent 设计
- 风控 Agent(反欺诈/反洗钱)
- 金融知识图谱 + Agent

**预习建议**:
1. 了解美团/蚂蚁的核心业务场景
2. 思考"金融场景 Agent"与"社交场景 Agent"的差异化挑战
3. 复习 Day24 的隐私保护设计,明日会延伸到"金融合规"
4. 准备一个"实时决策"场景的系统设计框架

> **今日金句**:腾讯问"用户爽不爽",百度问"原理深不深",美团问"算不过来账",蚂蚁问"安不安全"。四家大厂,四种 Agent 哲学。

---

**文档版本**: v1.0
**最后更新**: 2026-09-23
**适用计划**: AI Agent 面试 31 天冲刺 · Week4 · Day24
**字数统计**: 约 45KB
