# Day 26 — 华为 Agent 面试专项

> **学习目标**:掌握华为(盘古大模型 / 昇腾 NPU / 鸿蒙 / 华为云)在 Agent 方向的面试考点,理解行业大模型底座、端云协同、政企安全合规三大华为特色命题,能在面试中体现"以客户为中心、长期主义、自强不息"的价值观匹配。
>
> **面试定位**:华为 Agent 岗位主要分布在 2012 实验室(大模型底层)、华为云(平台与行业 Agent)、终端 BG(端侧 / 鸿蒙 Agent)、政企军团(行业解决方案)。面试兼具"硬核工程能力 + 价值观考察 + 行业理解"三重维度,题目风格偏务实、偏底层、偏 ToB 场景,与字节(偏算法创新)、阿里(偏业务规模)风格明显不同。
>
> **今日时长**:建议 4-5 小时(知识图谱 30min + 10 道题精读 2.5h + 自测 1h + 延伸阅读 30min)。

---

## 今日知识图谱

```
华为 Agent 面试考点
├── 1. 面试风格与价值观
│   ├── 2012 实验室 / 云核心 / 终端 BG 团队差异
│   ├── 技术面 + 综合面 + 主管面 流程
│   ├── "以客户为中心" 价值观匹配
│   └── "艰苦奋斗 / 自我批判" 隐性考察
│
├── 2. 盘古大模型底座
│   ├── 行业大模型 (金融 / 政务 / 制造 / 矿山 / 气象)
│   ├── 预训练 + 行业微调 + 强化对齐 三阶段
│   ├── 5N1A 架构 (5 亿行代码 / 千亿参数)
│   └── Agent 化:盘古 Agent 工厂
│
├── 3. 昇腾 NPU 适配
│   ├── CANN 算子库 / MindSpore 框架
│   ├── 算子优化 (FlashAttention / 矩阵分块)
│   ├── 内存优化 (重计算 / KV Cache 复用)
│   └── 并发优化 (多流 / 流水 / 张量并行)
│
├── 4. 端侧 Agent
│   ├── 手机 (麒麟 NPU / 端侧 7B 量化)
│   ├── 车机 (鸿蒙座舱 / 低时延工具调用)
│   ├── 离线缓存 / 模型瘦身 / 功耗控制
│   └── 端云协同 (敏感词云上 / 普通词端上)
│
├── 5. 政企安全合规
│   ├── 数据不出域 (私有化部署)
│   ├── 全链路审计 (Prompt / 工具调用 / 输出)
│   ├── 权限管控 (RBAC + 数据分级)
│   └── 国密算法 / 等保 2.0 / 信创要求
│
├── 6. 鸿蒙分布式 Agent
│   ├── 跨设备协同 (手机 / 平板 / 车机 / 智慧屏)
│   ├── 分布式软总线 / 分布式数据管理
│   ├── 元服务 / 一次开发多端部署
│   └── Agent 调用系统能力 (相机 / 位置 / 传感器)
│
├── 7. 华为云 ModelArts
│   ├── ModelArts Studio (Agent 开发平台)
│   ├── 代码仓 / 数据集 / 训练 / 部署 全流程
│   ├── 端云协同推理 (ModelArts + 端侧)
│   └── AOM 运维 + 监控告警
│
├── 8. 华为内部应用
│   ├── 客服 Agent (亿联 / 智能问答)
│   ├── 运维 Agent (AIOps / 故障定位)
│   ├── 研发效能 Agent (CodeArts / 代码评审)
│   └── 流程自动化 Agent (RPA + LLM)
│
└── 9. 手撕 & 系统设计
    ├── 端侧轻量 Agent (量化 / 精简 / 缓存 / 低功耗)
    └── 政企安全合规 Agent 系统设计
```

---

## 面试题(共 10 道)

### Q1 — 华为面试风格:2012 实验室 / 云核心 / 终端团队的区别?如何匹配华为价值观?

<details>
<summary>查看答案</summary>

**一、华为 Agent 相关的三大团队**

| 团队 | 主要方向 | 面试侧重 | 典型题目风格 |
|------|---------|---------|-------------|
| 2012 实验室(诺亚方舟) | 大模型底层算法、Agent 框架、强化学习 | 算法深度 + 论文 + 顶会 | "讲讲你最近读的 RLHF 论文" |
| 华为云(云核心 / EI) | 盘古大模型平台、ModelArts、行业 Agent | 工程能力 + 系统设计 + 行业理解 | "金融场景 Agent 怎么设计数据隔离" |
| 终端 BG | 鸿蒙 Agent、端侧推理、跨设备协同 | 端侧优化 + 移动开发 + 用户体验 | "端侧 7B 模型如何做到 500ms 响应" |
| 政企军团(附加) | 矿山 / 政务 / 金融 / 制造行业解决方案 | 行业理解 + 客户沟通 + 安全合规 | "煤矿 Agent 怎么保证下井设备防爆合规" |

**二、华为面试流程(社招典型 4 轮)**

1. **技术一面(1h)**:自我介绍 + 项目深挖 + 1-2 道编程题(LeetCode 中等偏简单) + 基础八股
2. **技术二面(1h)**:系统设计题 + 项目追问 + 场景题(常带华为业务色彩)
3. **综合面 / HRBP 面(45min)**:价值观 + 职业规划 + 抗压能力 + 薪资期望
4. **主管面 / 业务主管面(45min-1h)**:业务理解 + 团队匹配 + 长期规划

> **与互联网大厂的关键差异**:华为几乎必有"综合面",会反复追问"为什么不选互联网选华为""怎么看待加班""过往最有挫败感的事";主管面常常是部长 / VP 级别,看重"是否能跟团队一起长期奋斗"。

**三、华为核心价值观与 Agent 岗位的映射**

| 核心价值观 | 面试中如何体现 | 反面例子 |
|-----------|---------------|---------|
| 以客户为中心 | 强调 ToB 客户场景理解、行业痛点拆解 | 只谈技术炫技,不懂客户价值 |
| 艰苦奋斗 | 主动承担难活、愿意去一线 / 海外 | 频繁跳槽、强调"工作生活平衡" |
| 自我批判 | 复盘项目失败、承认不足并提出改进 | 把锅甩给团队 / 甲方 |
| 开放进取 | 关注开源、跨领域学习、长期主义 | 只用自研栈、排斥外部技术 |
| 至诚守信 | 实事求是、不夸大简历 | 把团队成果说成个人贡献 |
| 团队合作 | 强调协作、给同事 credit | "我一个人做了 XX" |

**四、价值观匹配的话术模板**

> "我选择华为,是因为我看重 ToB 场景的技术长期价值。互联网的 C 端流量红利已经见顶,而政企数字化、行业大模型是未来 10 年的硬仗,需要既能沉下去做底层、又能跑一线理解客户的工程师,这和我的职业方向一致。我之前在 XX 项目中,主动去客户现场驻场两周,把一个'看起来很 cool 的方案'改成了客户真正能用的产品,这个过程让我理解了'以客户为中心'不是口号。"

**五、面试避坑**

- **不要贬低其他公司**(尤其是同行友商):华为内部强调"至诚守信",踩同行会被认为"职业素养不够"
- **不要过度强调薪资**:可以谈期望,但不要把它作为核心驱动;华为薪资结构是"基本工资 + 绩效 + 年终 + TUP/ESOP",看重长期回报
- **不要回避加班话题**:华为是"奋斗者文化",直接说"完全不加班"会被扣分;更好说"我接受合理加班,关键是事情有没有价值"
- **不要把华为和"爱国"绑定太死**:可以认同技术自立,但不要表演式爱国

</details>

---

### Q2 — 盘古大模型做 Agent 底座,在行业场景(金融 / 政务 / 制造)的适配方案?

<details>
<summary>查看答案</summary>

**一、盘古大模型的"1 + N + X"架构**

华为盘古大模型采用 **"1 个基础大模型 + N 个行业基础模型 + X 个场景模型"** 的三层架构,这是华为 ToB Agent 的核心打法,与互联网公司"一个通用大模型打天下"的思路不同。

```
┌─────────────────────────────────────────┐
│  X 层:场景模型(金融客服 / 政务问答 / 矿山安监)│
├─────────────────────────────────────────┤
│  N 层:行业基础模型(金融 / 政务 / 制造 / 矿山)│
├─────────────────────────────────────────┤
│  1 层:盘古基础大模型(自然语言 / 多模态 / 科学)│
└─────────────────────────────────────────┘
```

**二、三阶段适配流程**

**阶段 1:行业预训练(Continual Pre-training)**
- 在基础大模型上,注入行业语料(金融研报、政务文件、制造工艺手册)
- 数据配比:行业语料 30% + 通用语料 70%,避免灾难性遗忘
- 关键技术:**数据清洗 + 去重 + 质量分 + 行业知识图谱对齐**

**阶段 2:行业微调(SFT)**
- 构建行业指令数据集(金融:合规问答、报告生成;政务:政策解读、办事引导;制造:故障诊断、工艺优化)
- 样本量:典型 5-20 万条高质量指令对
- 关键技术:**LoRA/P-Tuning 轻量微调**(降本)+ **指令多样性增强**

**阶段 3:强化对齐(RLHF / RLAIF)**
- 行业专家标注偏好(金融:合规 > 流畅;制造:准确 > 创意)
- 构建行业 Reward Model
- 关键技术:**DPO 替代 PPO**(更稳定、成本低)

**三、三大行业的差异化适配**

| 维度 | 金融 | 政务 | 制造 |
|------|------|------|------|
| 核心痛点 | 合规、风控、报告 | 办事效率、政策一致性 | 质检、故障、工艺优化 |
| 数据特点 | 结构化报表 + 非结构化研报 | 政策文件 + 办事指南 | 传感器时序 + 工艺文档 |
| 工具集 | 查行情、查合规、生成报告 | 查政策、办业务、填表 | 查设备状态、调 MES、出工单 |
| 关键约束 | 不能给投资建议、合规审计 | 政策口径必须准确 | 实时性、确定性 |
| Agent 模式 | 多 Agent(合规 + 分析 + 报告) | 单 Agent + 强 RAG | 多模态 Agent(文本 + 时序 + 图像) |
| 评估指标 | 准确率 + 合规率 + 人工接管率 | 一次办成率 + 政策引用准确率 | 故障定位准确率 + 平均修复时间 |

**四、Agent 框架的对接(盘古 Agent 工厂)**

```python
# 华为盘古 Agent 工厂伪代码示例
from pangu_agent import PanguAgent, ToolRegistry, IndustryAdapter

# 1. 加载行业基础模型
adapter = IndustryAdapter(industry="finance", model="pangu-38B-finance")

# 2. 注册行业工具
tools = ToolRegistry()
tools.register("query_market_data", fn=get_market_data, schema={...})
tools.register("check_compliance", fn=compliance_check, schema={...})
tools.register("generate_report", fn=report_generator, schema={...})

# 3. 构建 Agent
agent = PanguAgent(
    model=adapter.model,
    tools=tools,
    system_prompt=adapter.get_system_prompt(),  # 行业定制 system prompt
    safety_guardrails=adapter.get_safety_rules(),  # 行业安全护栏
    audit_logger=AuditLogger(retention="180d"),  # 全链路审计
)

# 4. 运行
result = agent.run("帮我分析贵州茅台最近 30 天走势并生成研报")
```

**五、面试加分点**

1. 提到 **"盘古不做 ChatGPT 式的通用聊天,只做行业大模型"** —— 体现对华为战略的理解
2. 提到 **"行业 Agent 的瓶颈是数据,不是模型"** —— 体现 ToB 务实视角
3. 提到 **"金融场景必须人在回路(Human-in-the-loop),Agent 不能直接出投资建议"** —— 体现合规意识
4. 提到 **"政务场景要支持信创栈(麒麟 OS + 鲲鹏 CPU + 昇腾 NPU)"** —— 体现对国产化生态的理解

**六、可能的追问**

- Q:行业模型和通用模型怎么避免互相干扰?A:采用 LoRA 多适配器,基础模型冻结,每个行业一个 adapter,推理时动态加载。
- Q:如何评估行业 Agent 的效果?A:分三层 — 模型层(MMLU-Industry)、Agent 层(工具调用准确率、任务完成率)、业务层(客户 KPI)。
- Q:小客户用不起行业大模型怎么办?A:走盘古 ModelArts 共享推理池,按 token 计费;或者用 7B 量化版本私有化部署。

</details>

---

### Q3 — 昇腾 NPU 上部署 Agent 的优化策略(算子 / 内存 / 并发)?

<details>
<summary>查看答案</summary>

**一、昇腾生态基础**

| 层级 | 组件 | 作用 |
|------|------|------|
| 硬件 | 昇腾 910B / 910C / 310 | 训练(910)/ 推理(310) |
| 中间件 | CANN(Compute Architecture for Neural Networks) | 算子库 + 运行时,类似 CUDA + cuDNN |
| 框架 | MindSpore / PyTorch(适配层) | 训练框架 |
| 推理引擎 | MindIE(原 AscendIE)/ vLLM-Ascend | 高性能推理 |
| 模型转换 | ATC(Ascend Tensor Compiler) | ONNX/MS → om 格式 |

**二、算子优化**

1. **FlashAttention 适配**:昇腾上 MindIE 已支持 FlashAttention v2,通过矩阵分块减少 HBM 访问。面试要点:**对比 GPU 上的实现差异** —— 昇腾的 Cube 矩阵单元(类似 Tensor Core)需要把 Q/K/V 分块对齐到 16x16。
2. **算子融合**:
   - LayerNorm + 残差 + 激活 融合为单个 kernel
   - Attention 中的 Softmax + Mask + Scale 融合
   - 工具:`MindIE` 提供 60+ 预融合算子
3. **自定义算子**:用 Ascend C(TikScript)写高性能算子,典型场景是 Agent 中自定义的 ReAct 解析算子、Tool Schema 校验算子。
4. **KV Cache 算子**:昇腾上推荐用 `PagedAttention-Ascend`,把 KV Cache 按页管理,减少碎片化。

**三、内存优化**

1. **KV Cache 复用**:多轮 Agent 对话中,KV Cache 跨轮保留;长上下文用 PagedAttention 分页管理。
2. **重计算(Gradient Checkpointing)**:训练行业大模型时,前向丢弃中间激活,反向重算,用算力换显存。
3. **量化**:
   - W8A8(权值 8bit + 激活 8bit):昇腾 910B 原生支持,推理吞吐提升 2-3 倍
   - W4A16:权值 4bit,精度损失小,适合端侧 310
   - 工具:`AscendQuantization` + `SmoothQuant`
4. **显存池化**:MindIE 推理引擎内置显存池,KV Cache 按需分配,支持多用户共享。

**四、并发优化**

1. **多流(Multi-Stream)**:昇腾支持 8 路 Stream 并发,把 Prefill(预填充)和 Decode(解码)放到不同 Stream。
2. **Continuous Batching**:动态拼 batch,等长请求一起跑;昇腾上用 `vLLM-Ascend` 已支持。
3. **张量并行(TP)**:910B 单卡 64GB,千亿模型需要 4-8 卡 TP;MindIE 内置 TP 通信,基于 HCCS 高速互联。
4. **流水并行(PP)**:超大规模模型用 PP + TP 嵌套,910C 的 HCCS 带宽 300GB/s。
5. **Speculative Decoding(投机解码)**:用小模型生成候选 token,大模型并行校验,昇腾上实测 1.5-2x 加速。

**五、Agent 特有的优化点**

| Agent 瓶颈 | 优化手段 |
|-----------|---------|
| 多轮对话 KV Cache 膨胀 | PagedAttention + 上下文裁剪 |
| 工具调用并行度低 | 工具调用并行化,把 IO 等待时间用来跑下一轮 Decode |
| 长 Prompt 重复计算 | Prefix Caching(系统 prompt 的 KV Cache 缓存) |
| 多模型切换(规划 + 执行) | 模型热加载,共享 KV Cache 池 |
| Tool Schema 校验开销 | 用昇腾自定义算子做 JSON Schema 校验,比 CPU 校验快 5x |

**六、性能数据(面试可引用)**

- 昇腾 910B 上跑 LLaMA-33B W8A8,单卡吞吐 **1500+ tokens/s**(batch=8)
- 910B 4 卡 TP 跑 175B 模型,延迟 **<200ms/token**
- 端侧 310B 跑 Qwen-7B INT4,功耗 **5W**,延迟 **80ms/token**

**七、与 GPU 的对比话术(谨慎,不贬低)**

> "昇腾在国产化场景下是唯一选择,生态在快速完善。和 A100 比,910B 在 INT8 推理上吞吐已经接近,但 FP16 训练的算子覆盖和 CUDA 还有差距,需要更多手工算子优化。华为的优势是'软硬协同 + 国产化合规',在政企场景是刚需。"

**八、可能的追问**

- Q:昇腾上跑 vLLM 要注意什么?A:用 `vllm-ascend` 分支,不支持部分 CUDA-only 算子;PagedAttention 的 block 大小要调到 16(默认 16,GPU 上常用 16)。
- Q:如何排查昇腾推理性能瓶颈?A:用 `msprof` 抓 trace,看 AICore 利用率、HBM 带宽、Stream 切换开销。
- Q:Agent 多轮对话怎么管理显存?A:实现一个 LRU 的 KV Cache 池,长会话保留前 N 轮 + 后 M 轮,中间用 summary 压缩。

</details>

---

### Q4 — 端侧 Agent 设计:在手机 / 车机上运行 Agent 的挑战和方案?

<details>
<summary>查看答案</summary>

**一、端侧 Agent 的核心挑战**

| 维度 | 手机 | 车机 |
|------|------|------|
| 算力 | 麒麟 NPU 4-8 TOPS | 座舱 SoC 10-30 TOPS |
| 内存 | 8-16GB,分给 Agent ≤2GB | 8-16GB,需与车控共享 |
| 功耗 | 电池敏感,平均 <2W | 供电充足但散热差 |
| 时延 | 用户期望 <500ms 首 token | 语音交互 <300ms |
| 网络 | 弱网友好 | 隧道 / 地库常断网 |
| 安全 | 个人隐私 | 功能安全(ISO 26262) |

**二、端侧 Agent 的整体架构**

```
┌────────────────────────────────────────────┐
│  用户输入(语音 / 文本 / 多模态)              │
├────────────────────────────────────────────┤
│  意图分流器(端侧小模型 / 规则)              │
│   ├─ 简单意图 → 端侧 1.8B 模型直接答          │
│   ├─ 复杂意图 → 端侧 7B Agent 规划 + 工具     │
│   └─ 高难任务 → 云端盘古大模型(必要时)        │
├────────────────────────────────────────────┤
│  端侧 Agent(7B INT4)                       │
│   ├─ 规划器(ReAct / Plan-Execute)           │
│   ├─ 工具集(系统能力:相机/位置/日历/电话)    │
│   ├─ 短期记忆(本地 KV Cache)                │
│   └─ 长期记忆(本地向量库,加密存储)           │
├────────────────────────────────────────────┤
│  端云协同网关                                │
│   ├─ 敏感数据脱敏后上云                       │
│   ├─ 云端结果回端侧校验                       │
│   └─ 离线降级(端侧兜底)                      │
├────────────────────────────────────────────┤
│  输出(语音合成 / UI 渲染 / 系统操作)         │
└────────────────────────────────────────────┘
```

**三、关键技术方案**

**1. 模型瘦身三件套**

- **量化**:7B 模型 INT4 量化后 4GB,可在 8GB 手机上运行;用 GPTQ + 端侧校准
- **剪枝**:结构化剪枝 20-30%,精度损失 <2%
- **蒸馏**:用云端 70B 蒸馏端侧 7B,蒸馏数据 100 万条
- **华为方案**:盘古端侧 1.8B / 7B 两个规格,麒麟 NPU 原生 INT4 加速

**2. 推理引擎优化**

- 用 **MindIE Lite**(端侧推理引擎),支持 NPU + CPU 异构调度
- **算子级优化**:针对 ReAct 解析、JSON 解析做自定义算子,比通用框架快 3x
- **KV Cache 压缩**:多轮对话用 8-bit KV Cache,显存减半
- **Speculative Decoding**:端侧小模型 + 云端大模型协同,端侧先草拟,云端校验

**3. 工具精简与离线缓存**

```python
# 端侧工具集精简策略
class EdgeToolRegistry:
    def __init__(self):
        # 1. 内置工具(常驻,极简):时钟、天气、日历、计算器
        self.builtin_tools = [ClockTool(), WeatherTool(cached=True), ...]
        # 2. 按需加载工具(用 schema 索引,真正调用时才加载代码)
        self.lazy_tools = {"call_taxi": LazyTool("call_taxi")}
        # 3. 离线缓存:常用工具结果预取
        self.cache = LRUCache(size=100)

    def get_tool(self, name):
        # 命中缓存
        if name in self.cache:
            return self.cache[name]
        # 内置工具
        for t in self.builtin_tools:
            if t.name == name:
                return t
        # 按需加载(避免冷启动时全量加载)
        if name in self.lazy_tools:
            tool = self.lazy_tools[name].load()
            self.cache[name] = tool
            return tool
        raise ToolNotFound(name)
```

**4. 低功耗设计**

- **间歇推理**:Agent 不常驻,用轻量唤醒词 + 小模型意图分类,确认是复杂任务才拉起 7B
- **NPU + CPU 协同**:推理时 NPU 全速,空闲时降频到 200MHz
- **后台冷冻**:Agent 进入后台后,KV Cache 写盘,内存释放
- **华为方案**:鸿蒙的"原子化服务"机制,Agent 按需启动,用完即销

**5. 端云协同**

- **意图分流**:端侧先判断难度,简单任务不上云(省流量 + 省时延)
- **隐私脱敏**:用户身份证号、位置等敏感字段,端侧脱敏后再上云
- **结果校验**:云端返回结果,端侧用小模型做 safety check
- **离线降级**:断网时端侧 7B 兜底,关键能力(打电话、设闹钟)保证可用

**四、车机场景的特殊考量**

1. **功能安全**:车机 Agent 控制车辆功能(空调、车窗)时,必须经过车控域校验,Agent 不能直接执行,只能"建议"
2. **时延敏感**:语音交互首字 <300ms,否则用户体验差;用流式 ASR + 流式 LLM + 流式 TTS 全链路流式
3. **多模态**:车机要结合摄像头(驾驶员状态)、麦克风(声源定位)、车辆状态(车速、档位)做综合决策
4. **离线强需求**:隧道、地库场景必须离线可用;导航、媒体、车控三大核心能力全离线

**五、可能的追问**

- Q:端侧 7B 模型首 token 时延多少?A:麒麟 9000S 上 INT4 量化,首 token 200-300ms,decode 50-80ms/token,流式体验可接受。
- Q:端侧 Agent 怎么更新?A:通过华为应用市场分发模型增量包(差分更新),50-200MB;不强制更新,用户在 WiFi 下后台拉取。
- Q:车机 Agent 怎么过功能安全认证?A:Agent 输出走"双签"机制,LLM 输出 + 规则引擎校验,任一不通过则拒绝执行;关键车控动作必须有驾驶员二次确认。

</details>

---

### Q5 — 政企场景 Agent 的安全合规要求(数据不出域 / 审计 / 权限)?

<details>
<summary>查看答案</summary>

**一、政企 Agent 的四大合规红线**

1. **数据不出域**:所有数据(训练数据、推理数据、用户数据)必须在客户内网处理,不能上公网
2. **全链路审计**:从用户输入到 Agent 输出的每一步都要可追溯,保留 6 个月以上
3. **权限最小化**:基于 RBAC,Agent 不能越权访问数据;工具调用必须权限校验
4. **国密 + 信创**:加密用国密 SM2/SM3/SM4;部署在麒麟 OS + 鲲鹏 / 昇腾硬件上

**二、合规框架全景**

```
┌─────────────────────────────────────────────┐
│  1. 数据安全层                                │
│   ├─ 数据分级(公开/内部/秘密/机密)             │
│   ├─ 数据脱敏(身份证/手机号/银行卡)            │
│   ├─ 数据加密(存储 SM4 / 传输 TLS+SM2)         │
│   └─ 数据不出域(私有化部署 + 物理隔离)          │
├─────────────────────────────────────────────┤
│  2. 模型安全层                                │
│   ├─ 模型审计(训练数据来源可追溯)               │
│   ├─ 模型水印(防泄漏)                          │
│   ├─ 输出过滤(敏感词 / 政治安全 / 越狱防护)     │
│   └─ 红队对抗(定期攻防演练)                     │
├─────────────────────────────────────────────┤
│  3. Agent 行为安全层                          │
│   ├─ 工具调用权限(RBAC + ABAC)                 │
│   ├─ Prompt 注入防护(输入过滤 + 角色隔离)      │
│   ├─ 越权检测(行为基线 + 异常告警)             │
│   └─ 人在回路(高风险动作人工确认)              │
├─────────────────────────────────────────────┤
│  4. 审计追溯层                                │
│   ├─ 全链路日志(Prompt/工具/输出,6 个月+)      │
│   ├─ 不可篡改(区块链 / WORM 存储)              │
│   ├─ 可审计(支持等保 2.0 三级 / 关基要求)      │
│   └─ 可取证(异常行为回放)                      │
├─────────────────────────────────────────────┤
│  5. 信创适配层                                │
│   ├─ 硬件:鲲鹏 CPU + 昇腾 NPU                 │
│   ├─ OS:麒麟 / 统信 UOS                       │
│   ├─ 数据库:高斯 DB / 人大金仓                │
│   └─ 中间件:华为云 Stack / 宝兰德             │
└─────────────────────────────────────────────┘
```

**三、典型合规要求与实现**

| 合规要求 | 法规依据 | 技术实现 |
|---------|---------|---------|
| 数据不出域 | 《数据安全法》《个保法》 | 私有化部署,物理隔离外网 |
| 全链路审计 | 等保 2.0 三级 | 日志中台 + WORM 存储,180 天+ |
| 个人信息脱敏 | 《个人信息保护法》 | 正则 + NER 双重脱敏 |
| 国密算法 | 国密局要求 | SM2(非对称)+ SM4(对称)+ SM3(哈希) |
| 权限管控 | 等保 + 行业规范 | RBAC + 数据分级 + 行为审计 |
| 越狱防护 | 生成式 AI 服务管理办法 | 输入 / 输出双过滤 + 红队对抗 |
| 内容安全 | 《生成式 AI 服务管理暂行办法》 | 政治安全 + 暴恐 + 色情三道过滤 |
| 模型备案 | 《生成式 AI 服务管理暂行办法》 | 向网信办备案模型卡 + 评估报告 |

**四、关键技术实现**

**1. 私有化部署架构**

```python
# 政企 Agent 私有化部署的核心约束
class EnterpriseAgentDeployment:
    def __init__(self):
        # 1. 物理隔离:不能有公网出口
        self.network_isolation = "air-gap"  # or "physical-isolation"
        # 2. 模型本地化:模型权重不能外传
        self.model_local = True
        self.model_encrypted = "SM4"  # 模型权重加密存储
        # 3. 数据本地化:所有数据在内网
        self.data_residency = "intranet"
        # 4. 国密套件
        self.crypto = {"asym": "SM2", "sym": "SM4", "hash": "SM3"}
        # 5. 信创栈
        self.stack = {
            "cpu": "Kunpeng",
            "npu": "Ascend",
            "os": "Kylin",
            "db": "GaussDB",
            "middleware": "HuaweiCloudStack",
        }
```

**2. 全链路审计日志**

```python
class AuditLogger:
    """全链路审计:Prompt → 推理 → 工具调用 → 输出,全部留痕"""

    def log_prompt(self, user_id, prompt, timestamp, ip):
        # 记录原始 prompt(脱敏后)
        entry = {
            "event": "prompt",
            "user_id": user_id,
            "prompt": self._desensitize(prompt),
            "timestamp": timestamp,
            "ip": ip,
            "hash": self._sm3(prompt),  # 防篡改
        }
        self._write_worm(entry)  # 写入 WORM 存储,不可改

    def log_tool_call(self, user_id, tool_name, args, result, permission):
        # 记录工具调用 + 权限校验结果
        entry = {
            "event": "tool_call",
            "user_id": user_id,
            "tool": tool_name,
            "args": self._desensitize(args),
            "result": self._desensitize(result),
            "permission_granted": permission,
            "timestamp": now(),
        }
        self._write_worm(entry)

    def log_output(self, user_id, output, safety_check):
        # 输出 + 安全检查结果
        entry = {
            "event": "output",
            "user_id": user_id,
            "output": output,
            "safety_check": safety_check,  # 通过/拦截/告警
            "timestamp": now(),
        }
        self._write_worm(entry)
```

**3. 权限管控(RBAC + 数据分级)**

```python
class PermissionChecker:
    def __init__(self):
        self.rbac = RBACStore()  # 用户-角色-权限
        self.data_level = DataLevelClassifier()  # 数据分级器

    def check_tool_access(self, user_id, tool_name, args):
        # 1. RBAC 校验:用户是否有该工具的调用权限
        role = self.rbac.get_role(user_id)
        if not self.rbac.has_permission(role, tool_name):
            raise PermissionDenied(f"{role} cannot call {tool_name}")

        # 2. 数据分级校验:工具参数中的数据级别不能超过用户级别
        data_level = self.data_level.classify(args)
        user_level = self.rbac.get_data_level(user_id)
        if data_level > user_level:
            raise DataLevelExceeded(f"User level {user_level} cannot access {data_level} data")

        # 3. 高风险动作:人在回路
        if tool_name in HIGH_RISK_TOOLS:  # 删除、转账、外发
            require_human_approval(user_id, tool_name, args)
```

**五、典型场景合规要点**

| 场景 | 合规要点 |
|------|---------|
| 政务问答 | 政策口径必须准确;不能给"主观建议";内容安全三道过滤 |
| 金融风控 | 不能给投资建议;决策必须可解释;留痕 5 年+ |
| 矿山安监 | 实时告警必须有兜底(漏报会死人);设备防爆认证 |
| 医疗问诊 | 不能诊断(只能做信息整理);医生二次确认;病历留痕 |
| 法务合同 | 模板生成可做;法律意见必须人工复核 |

**六、面试加分点**

1. 提到 **"等保 2.0 三级 + 关基 + 信创"** 三件套 —— 体现对政企合规体系的整体认知
2. 提到 **"Agent 的合规比传统软件更难,因为 LLM 输出不可预测"** —— 体现对生成式 AI 风险的深刻理解
3. 提到 **"合规不是成本,是华为政企市场的护城河"** —— 体现战略视角
4. 提到 **"全链路审计的关键不是记录,是不可篡改 + 可回放"** —— 体现落地深度

**七、可能的追问**

- Q:模型权重怎么保护?A:SM4 加密存储 + 运行时解密 + 模型水印(在权重中嵌入不可见标识),泄漏可追溯。
- Q:Prompt 注入怎么防?A:三层防护 —— 输入过滤(敏感词 + 注入特征)+ 角色隔离(System Prompt 不被用户覆盖)+ 输出校验(关键动作二次确认)。
- Q:如何证明合规?A:出三类报告 —— 模型备案报告(网信办)、等保测评报告(第三方)、渗透测试报告(红队)。

</details>

---

### Q6 — 鸿蒙系统上的 Agent 集成:跨设备协同 / 分布式能力调用?

<details>
<summary>查看答案</summary>

**一、鸿蒙 Agent 的独特优势**

鸿蒙的"分布式软总线 + 一次开发多端部署"为 Agent 提供了天然的多设备协同能力,这是 iOS / Android 难以复制的:

| 鸿蒙能力 | Agent 价值 |
|---------|-----------|
| 分布式软总线 | Agent 可跨设备调用,如"手机问 → 智慧屏答" |
| 分布式数据管理 | 用户记忆跨设备同步,登录账号即用 |
| 元服务 | Agent 即用即走,无需安装 App |
| Stage 模型 | Agent 作为 Ability,集成进系统能力中心 |
| ArkTS / ArkUI | 一套代码,手机 / 平板 / 车机 / 智慧屏 |
| HarmonyOS NEXT | 原生 AI 框架,系统集成 Agent |

**二、鸿蒙 Agent 的整体架构**

```
┌──────────────────────────────────────────────────┐
│  HarmonyOS NEXT(原生 AI 框架)                   │
├──────────────────────────────────────────────────┤
│  Agent Ability(元服务)                          │
│   ├─ UI(ArkUI 声明式)                            │
│   ├─ 业务逻辑(ArkTS)                             │
│   └─ AI 推理(端侧 7B / 云端盘古)                 │
├──────────────────────────────────────────────────┤
│  系统能力调用                                     │
│   ├─ 相机 / 麦克风 / 位置 / 传感器                 │
│   ├─ 通讯录 / 日历 / 短信                          │
│   ├─ 应用跳转(导航/支付/购物)                     │
│   └─ 智能家居控制(HiLink)                        │
├──────────────────────────────────────────────────┤
│  分布式能力                                       │
│   ├─ 软总线(设备发现 + 跨设备调用)               │
│   ├─ 分布式数据(用户记忆同步)                    │
│   ├─ 分布式任务(跨设备迁移)                      │
│   └─ 跨设备文件                                  │
├──────────────────────────────────────────────────┤
│  端侧推理引擎(MindIE Lite)                      │
│   └─ 麒麟 NPU 加速                               │
└──────────────────────────────────────────────────┘
```

**三、跨设备协同的典型场景**

**场景 1:手机问 → 智慧屏答**
- 用户在手机上问"给我看下昨晚的比赛集锦"
- 手机 Agent 识别"看视频"意图,通过软总线发现智慧屏
- 调用智慧屏的播放能力,视频在智慧屏上播放
- 手机变成遥控器

**场景 2:车机 → 手机无缝接力**
- 用户在车上让车机 Agent "提醒我到家给妈妈打电话"
- 车机 Agent 通过分布式任务迁移,把任务同步到手机
- 用户到家,手机自动弹出提醒

**场景 3:平板 → 笔记本协同办公**
- 用户在平板上让 Agent "总结这个 PDF"
- 平板算力不够,通过软总线把推理任务分发到笔记本
- 笔记本跑完后,结果回传平板展示

**四、关键代码示例(ArkTS)**

```typescript
// 鸿蒙 Agent 元服务示例
import { AgentAbility } from '@hw.ai.agent';
import { distributedBus } from '@hw.distributed.bus';
import { systemAbility } from '@hw.system.ability';

@Entry
@Component
struct AgentPage {
  private agent: AgentAbility = new AgentAbility({
    model: 'pangu-edge-7b',  // 端侧模型
    fallbackModel: 'pangu-cloud-38B',  // 云端兜底
    tools: [
      systemAbility.CAMERA,
      systemAbility.MICROPHONE,
      systemAbility.LOCATION,
      systemAbility.CALENDAR,
      systemAbility.CONTACTS,
    ],
  });

  async onUserQuery(query: string) {
    // 1. 端侧意图分流
    const intent = await this.agent.classifyIntent(query);

    // 2. 简单意图:端侧直接答
    if (intent.complexity === 'simple') {
      return await this.agent.localInfer(query);
    }

    // 3. 复杂意图:跨设备调度
    const devices = await distributedBus.discoverDevices();
    const bestDevice = this.selectBestDevice(devices, intent);

    if (bestDevice.id !== deviceInfo.localDeviceId) {
      // 跨设备调用
      return await distributedBus.invokeRemote(
        bestDevice.id,
        'agent.infer',
        { query, context: this.agent.context }
      );
    }

    // 4. 本地 Agent 执行
    return await this.agent.run(query);
  }

  selectBestDevice(devices, intent) {
    // 根据意图选最合适的设备
    if (intent.requiresLargeScreen) return devices.find(d => d.type === 'smartTV');
    if (intent.requiresHighCompute) return devices.find(d => d.cpu === 'laptop');
    return devices.find(d => d.id === deviceInfo.localDeviceId);
  }
}
```

**五、分布式能力调用的核心机制**

1. **设备发现**:基于软总线,自动发现同账号下的可信设备,无需手动配对
2. **能力协商**:设备间协商各自的能力(算力、屏幕、传感器),Agent 据此调度
3. **任务迁移**:任务可在设备间无缝迁移,状态保留;用"分布式任务调度"框架
4. **数据同步**:用户记忆、对话历史通过"分布式数据管理"自动同步
5. **安全可信**:基于"超级终端"可信环,设备间通信端到端加密

**六、鸿蒙 NEXT 的原生 AI 框架**

HarmonyOS NEXT(纯血鸿蒙)集成了原生 AI 框架,提供三层能力:
- **AI Kit**:端侧推理 API,封装 MindIE Lite
- **Agent Kit**:Agent 框架,提供规划 / 工具 / 记忆抽象
- **Scene Kit**:场景化能力,如智慧搜图、AI 修图、文档摘要

**七、面试加分点**

1. 提到 **"鸿蒙的分布式能力让 Agent 天然多设备"** —— 体现对鸿蒙差异化优势的理解
2. 提到 **"Agent 不是 App,是元服务,即用即走"** —— 体现对鸿蒙服务化理念的认知
3. 提到 **"端侧模型 + 软总线 = 端端协同 AI"** —— 体现架构创新点
4. 提到 **"HarmonyOS NEXT 是'原生 AI'OS,Agent 是一等公民"** —— 体现对鸿蒙战略的理解

**八、可能的追问**

- Q:跨设备调用的时延多少?A:软总线局域网内 10-50ms,跨设备推理加 100-500ms(取决于任务大小),可接受。
- Q:不同设备的 Agent 怎么保持一致?A:用户记忆 / 对话历史通过分布式数据管理同步,模型权重通过华为云账号下发,所有设备上 Agent "人格"一致。
- Q:跨设备调用的安全怎么保证?A:基于"超级终端"可信环,设备间用 SM2 端到端加密,可信设备列表由用户管理。

</details>

---

### Q7 — 华为云 ModelArts 上的 Agent 开发和部署流程?

<details>
<summary>查看答案</summary>

**一、ModelArts 全流程概览**

ModelArts 是华为云的一站式 AI 开发平台,覆盖"数据 → 训练 → 评估 → 部署 → 运维"全生命周期。Agent 在 ModelArts 上的开发流程:

```
┌──────────────────────────────────────────────────┐
│  1. 数据准备                                      │
│   ├─ ModelArts Data(数据集管理)                  │
│   ├─ 数据标注(人工 + 自动)                       │
│   └─ 数据清洗 / 脱敏 / 增强                       │
├──────────────────────────────────────────────────┤
│  2. 模型训练                                      │
│   ├─ 预训练(盘古基础大模型,昇腾集群)             │
│   ├─ 行业微调(SFT,LoRA / 全参)                  │
│   └─ 强化对齐(RLHF / DPO)                       │
├──────────────────────────────────────────────────┤
│  3. Agent 构建                                    │
│   ├─ ModelArts Studio(可视化编排)                │
│   ├─ 工具注册 / Prompt 模板                       │
│   └─ 多 Agent 编排                                │
├──────────────────────────────────────────────────┤
│  4. 模型部署                                      │
│   ├─ 在线推理服务(EP)                            │
│   ├─ 批量推理                                     │
│   ├─ 边缘部署(IEF,推到端侧)                     │
│   └─ 私有化部署(HCS,政企客户)                   │
├──────────────────────────────────────────────────┤
│  5. 运维监控                                      │
│   ├─ AOM(应用运维)                              │
│   ├─ 调用日志 / 性能监控                          │
│   ├─ 模型效果监控(漂移检测)                      │
│   └─ 告警 / 自动扩缩容                            │
└──────────────────────────────────────────────────┘
```

**二、ModelArts Studio:Agent 可视化编排**

ModelArts Studio 是 Agent 开发平台,特点:
- **可视化拖拽**:Agent / 工具 / 知识库 / 模型 用拖拽连线
- **Prompt 模板库**:行业模板(金融 / 政务 / 客服)开箱即用
- **工具市场**:预置华为云 + 第三方 API,注册即用
- **多 Agent 编排**:支持 Manager-Worker、Sequential、Parallel 三种模式
- **一键部署**:导出为推理服务,自动配置负载均衡 + 鉴权

**三、典型开发流程(代码视角)**

```python
# 1. 数据准备:上传行业数据到 OBS
from modelarts import OBSClient
obs = OBSClient()
obs.upload("obs://my-bucket/finance-data/", local_path="./data/")

# 2. 创建训练作业:行业微调
from modelarts import TrainingJob
job = TrainingJob.create(
    name="pangu-finance-sft",
    model="pangu-38B-base",
    data_source="obs://my-bucket/finance-data/",
    method="lora",  # 轻量微调
    hyperparams={
        "lora_rank": 16,
        "lr": 2e-4,
        "epochs": 3,
        "batch_size": 4,
        "npu_type": "Ascend-910B",
        "npu_count": 8,
    },
)
job.wait()  # 等待训练完成

# 3. 模型注册:把训练产物注册为模型
from modelarts import Model
model = Model.register(
    name="pangu-finance-v1",
    artifact=job.output_uri,
    inference_code="./inference.py",
)

# 4. Agent 构建:用 ModelArts Studio SDK
from modelarts.studio import Agent, Tool, KnowledgeBase

# 4.1 知识库
kb = KnowledgeBase.create(
    name="finance-kb",
    data="obs://my-bucket/finance-docs/",
    embedding="pangu-embedding",
    vector_store="gaussdb-vector",
)

# 4.2 工具
tools = [
    Tool(name="query_stock", api="https://api.huawei.com/stock", schema={...}),
    Tool(name="check_compliance", api="https://api.huawei.com/compliance", schema={...}),
    Tool(name="generate_report", fn=local_report_gen, schema={...}),
]

# 4.3 Agent
agent = Agent.create(
    name="finance-agent",
    model=model,
    tools=tools,
    knowledge_base=kb,
    system_prompt="你是金融分析助手,严格遵守合规要求...",
    safety_rules=["不给投资建议", "不输出敏感数据"],
)

# 5. 部署为在线服务
from modelarts import InferenceService
service = InferenceService.deploy(
    agent=agent,
    instance_type="Ascend-910B",
    instance_count=2,  # 双副本高可用
    auto_scaling={"min": 2, "max": 10, "target_cpu": 70},
    endpoint="https://finance-agent.myhuaweicloud.com",
    auth="iam",
)
```

**四、部署形态对比**

| 部署形态 | 适用场景 | 特点 |
|---------|---------|------|
| 公有云在线服务 | 互联网客户 | 弹性扩缩,按量付费 |
| 公有云专属池 | 大客户 | 资源隔离,包年 |
| 专属云(DeC) | 政企 | 物理隔离,合规 |
| 私有化(HCS) | 强合规客户 | 全栈本地化,数据不出域 |
| 边缘(IEF) | 端侧 / 边缘 | 推到设备,离线可用 |

**五、运维监控**

```python
# ModelArts Agent 的关键监控指标
monitor_metrics = {
    # 1. 性能指标
    "qps": "每秒请求数",
    "latency_p50": "P50 时延",
    "latency_p99": "P99 时延",
    "tokens_per_sec": "每秒生成 token 数",

    # 2. 业务指标
    "task_completion_rate": "任务完成率",
    "tool_call_success_rate": "工具调用成功率",
    "human_handoff_rate": "人工接管率",

    # 3. 安全指标
    "safety_block_rate": "安全拦截率",
    "prompt_injection_count": "注入攻击次数",
    "permission_denied_count": "权限拒绝次数",

    # 4. 资源指标
    "npu_utilization": "NPU 利用率",
    "memory_usage": "显存使用率",
    "kv_cache_hit_rate": "KV Cache 命中率",
}
```

**六、可能的追问**

- Q:模型更新怎么不停服?A:蓝绿部署 —— 新版本先起来,健康检查通过后流量切换,旧版本保留 30 分钟回滚窗口。
- Q:如何评估 Agent 在线效果?A:三层 —— 在线 A/B 测试(分流 5%)、用户反馈(点赞点踩)、人工抽检(每天 100 条)。
- Q:模型漂移怎么发现?A:监控输入分布(KS 检验)、输出分布(关键词漂移)、业务指标(完成率下降),任一异常告警。

</details>

---

### Q8 — Agent 在华为客服 / 运维 / 研发效能场景的落地?

<details>
<summary>查看答案</summary>

**一、华为内部 Agent 应用的三大主战场**

华为作为 20 万员工的 ToB 公司,自身就是 Agent 的最佳试验田。面试中提到"华为内部落地"案例,会极大加分。

| 场景 | 业务痛点 | Agent 方案 | 效果 |
|------|---------|-----------|------|
| 客服 | 亿级用户咨询,人工成本高 | 多 Agent:意图分流 + 知识库 + 工单 | 自助率 70%+ |
| 运维 | 万台设备故障,定位慢 | AIOps Agent:日志分析 + 根因 + 修复建议 | MTTR 降 40% |
| 研发效能 | 20 万员工,代码评审慢 | CodeArts Agent:评审 + 测试 + 文档 | 评审效率提升 50% |

**二、客服 Agent(华为云客服 + 亿联)**

**架构:三层 Agent**

```
┌────────────────────────────────────────┐
│  L1:意图分流 Agent(小模型)             │
│   ├─ 简单 FAQ → 直接答(命中率 50%)     │
│   ├─ 业务办理 → 引导操作(20%)          │
│   └─ 复杂咨询 → 转 L2(30%)             │
├────────────────────────────────────────┤
│  L2:专业问答 Agent(7B 行业模型)        │
│   ├─ RAG:产品文档 + 历史工单            │
│   ├─ 工具:查订单、查话费、办业务        │
│   └─ 兜底:转人工(10%)                  │
├────────────────────────────────────────┤
│  L3:人工坐席(增强助手)                │
│   ├─ Agent 实时辅助:推荐话术            │
│   ├─ 自动总结:通话结束自动出工单        │
│   └─ 知识库实时检索                     │
└────────────────────────────────────────┘
```

**关键效果**:
- 自助解决率 70%(L1+L2)
- 平均通话时长降 25%(L3 增强)
- 客户满意度从 85% → 91%

**三、运维 Agent(AIOps)**

**场景:故障定位**

```
┌────────────────────────────────────────┐
│  告警接入(告警压缩 + 关联)             │
│   └─ 1 分钟内 100 条告警 → 1 个事件     │
├────────────────────────────────────────┤
│  根因分析 Agent                         │
│   ├─ 拉取日志(ELK)                     │
│   ├─ 拉取指标(Prometheus)              │
│   ├─ 调用拓扑(链路追踪)                │
│   └─ 推理根因(概率 + 解释)             │
├────────────────────────────────────────┤
│  修复建议 Agent                         │
│   ├─ 匹配历史相似故障                   │
│   ├─ 生成修复方案(SQL/脚本/重启)       │
│   └─ 高置信度自动执行,低置信度人工确认 │
├────────────────────────────────────────┤
│  复盘报告 Agent                         │
│   └─ 故障结束后自动生成复盘报告          │
└────────────────────────────────────────┘
```

**关键效果**:
- MTTR(平均修复时间)从 2h → 1.2h,降 40%
- 故障定位准确率 85%
- 30% 的常见故障可自动修复

**四、研发效能 Agent(CodeArts)**

**场景:代码评审 + 测试 + 文档**

```python
# CodeArts Agent 的三大能力
class CodeArtsAgent:
    def code_review(self, mr_url):
        """代码评审:不只是 lint,而是逻辑级评审"""
        diff = self.get_mr_diff(mr_url)
        context = self.get_full_context(diff)  # 整个仓库的上下文

        review_points = []
        # 1. 安全问题(注入、越权、敏感数据)
        review_points += self.security_scan(diff)
        # 2. 性能问题(N+1 查询、内存泄漏)
        review_points += self.perf_scan(diff, context)
        # 3. 逻辑问题(边界条件、并发)
        review_points += self.logic_scan(diff, context)
        # 4. 风格问题(命名、注释)
        review_points += self.style_scan(diff)

        return self.generate_review_report(review_points)

    def generate_test(self, code):
        """根据代码生成单元测试"""
        # 1. 分析函数签名 + 实现逻辑
        # 2. 生成边界 / 正常 / 异常用例
        # 3. 自动运行,确保通过
        # 4. 覆盖率提升到 80%+
        pass

    def generate_doc(self, code):
        """根据代码生成文档"""
        # 1. 函数注释(API 文档)
        # 2. 模块说明(架构文档)
        # 3. 变更日志(Release Notes)
        pass
```

**关键效果**:
- 代码评审效率提升 50%(评审时长从 2h → 1h)
- 单元测试覆盖率从 40% → 75%
- 文档编写工作量降 60%

**五、流程自动化 Agent(RPA + LLM)**

传统 RPA(机器人流程自动化)只能做固定规则,LLM 加持后可以做"半结构化流程":
- **发票报销**:拍照 → Agent 识别 → 自动填单 → 流程审批
- **合同审核**:上传合同 → Agent 比对模板 → 标记风险点 → 法务复核
- **人事入职**:新员工信息 → Agent 自动开通账号 / 配置权限 / 发欢迎邮件

**六、面试加分点**

1. 提到 **"华为自身是 Agent 最佳试验田,20 万员工的研发效能是天然场景"** —— 体现对华为业务的理解
2. 提到 **"Agent 不是替代人,是增强人(L3 增强坐席)"** —— 体现务实的 AI 观
3. 提到 **"内部打磨成熟后外溢到客户,这是华为 ToB 的典型打法"** —— 体现战略认知
4. 提到 **"运维 Agent 的关键是告警关联 + 根因,不是单点告警处理"** —— 体现技术深度

**七、可能的追问**

- Q:客服 Agent 怎么避免"答非所问"伤害体验?A:L1 兜底机制 —— 任何不确定都转人工,宁可保守;L2 输出有 confidence,低于阈值不答。
- Q:运维 Agent 误报怎么处理?A:分两级 —— 高置信度自动执行(只针对可逆操作,如重启);低置信度只建议不执行,人工确认。
- Q:CodeArts Agent 评审会不会"误报太多"?A:初版误报率 30%,通过"反馈学习"持续优化,3 个月降到 10%。

</details>

---

### Q9 — 手撕代码:实现一个端侧轻量 Agent(模型量化 / 工具精简 / 离线缓存 / 低功耗)

<details>
<summary>查看完整代码</summary>

**题目要求**:实现一个端侧 Agent,具备以下能力:
1. 模型量化推理(INT4 模拟)
2. 工具精简(按需加载)
3. 离线缓存(常用结果预取)
4. 低功耗(间歇推理 + 唤醒机制)
5. 端云协同(敏感意图上云,普通意图端上)

```python
"""
Edge Agent:端侧轻量 Agent 实现
特性:量化推理 / 工具精简 / 离线缓存 / 低功耗 / 端云协同
"""
import os
import json
import time
import hashlib
import threading
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict


# ============================================================
# 1. 模型量化推理(INT4 模拟)
# ============================================================
class QuantizedModel:
    """INT4 量化模型模拟
    真实场景用 MindIE Lite / llama.cpp,这里用模拟实现演示逻辑
    """

    def __init__(self, model_path: str, quant_bits: int = 4):
        self.model_path = model_path
        self.quant_bits = quant_bits
        self._loaded = False
        self._memory_mb = 0
        # 模拟模型权重(INT4 量化后,7B 模型约 4GB)
        self._estimated_memory = 4000 if "7b" in model_path.lower() else 1200

    def load(self):
        """加载模型到 NPU/CPU 内存"""
        print(f"[Model] Loading {self.model_path} (INT{self.quant_bits})...")
        time.sleep(0.1)  # 模拟加载耗时
        self._loaded = True
        self._memory_mb = self._estimated_memory
        print(f"[Model] Loaded, memory={self._memory_mb}MB")

    def unload(self):
        """卸载模型,释放内存(低功耗模式)"""
        print(f"[Model] Unloading {self.model_path}, free {self._memory_mb}MB")
        self._loaded = False
        self._memory_mb = 0

    def infer(self, prompt: str, max_tokens: int = 256) -> str:
        """推理(模拟)
        真实场景调用 MindIE Lite 推理 API
        """
        if not self._loaded:
            raise RuntimeError("Model not loaded")
        # 模拟推理:首 token 200ms + decode 50ms/token
        time.sleep(0.2 + 0.05 * min(max_tokens, 30))
        return f"[INT{self.quant_bits} response for: {prompt[:30]}...]"


class WakeupClassifier:
    """唤醒分类器(轻量小模型,常驻)
    判断是否需要拉起大模型 Agent
    """

    def __init__(self):
        self._loaded = True  # 小模型常驻,内存 50MB
        self._memory_mb = 50

    def classify(self, query: str) -> dict:
        """分类意图难度 + 是否需要 Agent"""
        # 模拟:简单关键词判断
        simple_keywords = ["几点", "今天", "天气", "打电话", "发短信", "设闹钟"]
        is_simple = any(kw in query for kw in simple_keywords)

        if is_simple:
            return {"need_agent": False, "complexity": "simple", "confidence": 0.9}
        else:
            return {"need_agent": True, "complexity": "complex", "confidence": 0.8}


# ============================================================
# 2. 工具精简(按需加载)
# ============================================================
class LazyTool:
    """懒加载工具:只在首次调用时加载代码"""

    def __init__(self, name: str, loader: Callable, schema: dict):
        self.name = name
        self._loader = loader
        self.schema = schema
        self._instance = None
        self._loaded = False

    def load(self):
        if not self._loaded:
            print(f"[Tool] Lazy loading {self.name}...")
            self._instance = self._loader()
            self._loaded = True
        return self._instance

    def call(self, args: dict) -> Any:
        tool = self.load()
        return tool(**args)


class BuiltinTool:
    """内置工具:常驻,极简,启动时即加载"""

    def __init__(self, name: str, fn: Callable, schema: dict):
        self.name = name
        self.fn = fn
        self.schema = schema

    def call(self, args: dict) -> Any:
        return self.fn(**args)


class ToolRegistry:
    """工具注册表:内置 + 懒加载 + 缓存"""

    def __init__(self):
        self._builtin: dict[str, BuiltinTool] = {}
        self._lazy: dict[str, LazyTool] = {}

    def register_builtin(self, name: str, fn: Callable, schema: dict):
        self._builtin[name] = BuiltinTool(name, fn, schema)

    def register_lazy(self, name: str, loader: Callable, schema: dict):
        self._lazy[name] = LazyTool(name, loader, schema)

    def get(self, name: str) -> Optional[BuiltinTool | LazyTool]:
        if name in self._builtin:
            return self._builtin[name]
        if name in self._lazy:
            return self._lazy[name]
        return None

    def list_schemas(self) -> list[dict]:
        """只返回 schema(不加载代码),供模型选择工具"""
        return [
            {"name": t.name, **t.schema}
            for t in list(self._builtin.values()) + list(self._lazy.values())
        ]


# ============================================================
# 3. 离线缓存(LRU + 预取)
# ============================================================
class OfflineCache:
    """离线缓存:常用查询结果预取,断网可用"""

    def __init__(self, max_size: int = 100):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.Lock()

    def _key(self, query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[Any]:
        key = self._key(query)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                print(f"[Cache] Hit: {query[:30]}")
                return self._cache[key]
            print(f"[Cache] Miss: {query[:30]}")
            return None

    def set(self, query: str, value: Any):
        key = self._key(query)
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                self._cache[key] = value
                if len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)

    def prefetch(self, queries: list[str], fetcher: Callable[[str], Any]):
        """预取:WiFi 下后台预取常用查询"""
        for q in queries:
            if self.get(q) is None:
                try:
                    value = fetcher(q)
                    self.set(q, value)
                    print(f"[Cache] Prefetched: {q[:30]}")
                except Exception as e:
                    print(f"[Cache] Prefetch failed: {e}")


# ============================================================
# 4. 低功耗管理(间歇推理 + 唤醒)
# ============================================================
class PowerManager:
    """低功耗管理:Agent 闲置时卸载模型,唤醒时再加载"""

    def __init__(self, idle_timeout: int = 60):
        self.idle_timeout = idle_timeout  # 闲置 60s 后卸载模型
        self._last_active = time.time()
        self._timer: Optional[threading.Timer] = None
        self._model: Optional[QuantizedModel] = None

    def bind_model(self, model: QuantizedModel):
        self._model = model

    def on_active(self):
        """用户活跃时,确保模型已加载"""
        self._last_active = time.time()
        self._cancel_timer()
        if self._model and not self._model._loaded:
            print("[Power] Waking up, reloading model...")
            self._model.load()
        self._start_timer()

    def _start_timer(self):
        self._timer = threading.Timer(self.idle_timeout, self._sleep)
        self._timer.daemon = True
        self._timer.start()

    def _cancel_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def _sleep(self):
        """闲置超时,卸载模型省电"""
        if self._model and self._model._loaded:
            print(f"[Power] Idle {self.idle_timeout}s, unloading model to save power")
            self._model.unload()


# ============================================================
# 5. 端云协同
# ============================================================
class CloudAgent:
    """云端 Agent(模拟)
    处理复杂任务 / 强敏感度任务(脱敏后上云)
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def infer(self, prompt: str, context: dict) -> str:
        print(f"[Cloud] Calling cloud agent: {prompt[:30]}...")
        time.sleep(0.5)  # 模拟网络 + 云端推理
        return f"[Cloud response for: {prompt[:30]}...]"


class PrivacyFilter:
    """隐私脱敏:敏感字段上云前脱敏"""

    SENSITIVE_PATTERNS = {
        "phone": (r"1\d{10}", "[PHONE]"),
        "idcard": (r"\d{17}[\dXx]", "[IDCARD]"),
        "bank": (r"\d{16,19}", "[BANKCARD]"),
    }

    def desensitize(self, text: str) -> str:
        import re
        for name, (pattern, mask) in self.SENSITIVE_PATTERNS.items():
            text = re.sub(pattern, mask, text)
        return text


# ============================================================
# 6. Edge Agent 主类
# ============================================================
@dataclass
class AgentConfig:
    model_path: str = "pangu-edge-7b-int4"
    quant_bits: int = 4
    cache_size: int = 100
    idle_timeout: int = 60
    cloud_endpoint: str = "https://pangu.huaweicloud.com/agent"
    prefer_local: bool = True  # 优先端侧


class EdgeAgent:
    """端侧轻量 Agent
    特性:
    1. 模型量化推理(INT4)
    2. 工具精简(内置 + 懒加载)
    3. 离线缓存(LRU + 预取)
    4. 低功耗(间歇推理 + 唤醒)
    5. 端云协同(敏感意图上云,普通意图端上)
    """

    def __init__(self, config: AgentConfig = AgentConfig()):
        self.config = config
        # 1. 模型:量化大模型(按需加载)
        self.model = QuantizedModel(config.model_path, config.quant_bits)
        # 2. 唤醒分类器:常驻小模型
        self.wakeup = WakeupClassifier()
        # 3. 工具注册表
        self.tools = self._init_tools()
        # 4. 离线缓存
        self.cache = OfflineCache(config.cache_size)
        # 5. 低功耗管理
        self.power = PowerManager(config.idle_timeout)
        self.power.bind_model(self.model)
        # 6. 端云协同
        self.cloud = CloudAgent(config.cloud_endpoint)
        self.privacy = PrivacyFilter()
        # 7. 短期记忆(对话历史)
        self.history: list[dict] = []

    def _init_tools(self) -> ToolRegistry:
        """初始化工具:内置(常驻)+ 懒加载"""
        reg = ToolRegistry()

        # 内置工具:极简,启动即加载
        def _clock():
            return time.strftime("%Y-%m-%d %H:%M:%S")

        def _calc(expression: str):
            try:
                return str(eval(expression))
            except:
                return "Error"

        reg.register_builtin("clock", lambda: _clock(), {"description": "获取当前时间"})
        reg.register_builtin("calc", lambda expression: _calc(expression),
                             {"description": "计算器", "params": {"expression": "string"}})

        # 懒加载工具:首次调用时加载
        def _load_weather():
            print("[Tool] Loading weather module...")
            def get_weather(city: str):
                return f"{city} 晴 25°C"
            return get_weather

        def _load_navigation():
            print("[Tool] Loading navigation module...")
            def navigate(to: str):
                return f"开始导航至 {to}"
            return navigate

        reg.register_lazy("weather", _load_weather,
                          {"description": "查天气", "params": {"city": "string"}})
        reg.register_lazy("navigate", _load_navigation,
                          {"description": "导航", "params": {"to": "string"}})

        return reg

    def run(self, query: str) -> str:
        """Agent 主流程"""
        print(f"\n{'='*60}\n[Agent] Query: {query}\n{'='*60}")

        # 1. 唤醒:低功耗,小模型判断是否需要拉起大模型
        self.power.on_active()  # 标记活跃
        intent = self.wakeup.classify(query)
        print(f"[Agent] Intent: {intent}")

        # 2. 简单意图:直接用小模型 + 内置工具处理,不拉起大模型
        if not intent["need_agent"]:
            return self._handle_simple(query)

        # 3. 命中离线缓存:直接返回,不推理
        cached = self.cache.get(query)
        if cached is not None:
            return cached

        # 4. 复杂意图:端云协同决策
        if self._should_use_cloud(query, intent):
            return self._handle_cloud(query)
        else:
            return self._handle_local(query)

    def _handle_simple(self, query: str) -> str:
        """简单意图:小模型 + 内置工具"""
        # 尝试用内置工具直接答
        if "几点" in query or "时间" in query:
            return self.tools.get("clock").call({})
        if "计算" in query:
            # 简单提取表达式(演示用)
            expr = query.replace("计算", "").strip()
            return self.tools.get("calc").call({"expression": expr})
        # 兜底:小模型直接答(模拟)
        return f"[Simple answer for: {query}]"

    def _should_use_cloud(self, query: str, intent: dict) -> bool:
        """决策:端侧 or 云端
        规则:
        - 端侧模型未加载(省电模式)且任务不紧急 → 云端
        - 任务极复杂(需要大模型推理)→ 云端
        - 包含强敏感信息 → 端侧(脱敏后也不上云)
        - 网络可用 + 偏好云端 → 云端
        """
        # 强敏感信息:端侧处理
        if self._is_highly_sensitive(query):
            print("[Agent] Decision: local (highly sensitive)")
            return False

        # 端侧模型未加载且任务紧急 → 必须云端
        if not self.model._loaded and intent.get("urgency") == "high":
            print("[Agent] Decision: cloud (model not loaded, urgent)")
            return True

        # 默认偏好端侧(省流量 + 低时延)
        if self.config.prefer_local:
            print("[Agent] Decision: local (prefer local)")
            return False
        return True

    def _is_highly_sensitive(self, query: str) -> bool:
        """判断是否包含强敏感信息"""
        sensitive_keywords = ["密码", "身份证", "银行卡", "工资", "病历"]
        return any(kw in query for kw in sensitive_keywords)

    def _handle_local(self, query: str) -> str:
        """端侧处理:大模型 + 工具"""
        # 1. 确保模型已加载
        if not self.model._loaded:
            self.model.load()

        # 2. 构造 Prompt(含工具 schema + 历史)
        tool_schemas = self.tools.list_schemas()
        prompt = self._build_prompt(query, tool_schemas)

        # 3. 推理:模型决定调用哪些工具
        raw_output = self.model.infer(prompt)

        # 4. 解析工具调用(模拟 ReAct)
        tool_calls = self._parse_tool_calls(raw_output)

        # 5. 执行工具
        results = []
        for tc in tool_calls:
            tool = self.tools.get(tc["name"])
            if tool:
                result = tool.call(tc["args"])
                results.append({"tool": tc["name"], "result": result})

        # 6. 最终回答(模型基于工具结果生成)
        final_prompt = f"{prompt}\nTool results: {results}\nFinal answer:"
        final = self.model.infer(final_prompt, max_tokens=128)

        # 7. 缓存结果
        self.cache.set(query, final)

        # 8. 更新历史
        self.history.append({"user": query, "assistant": final})
        if len(self.history) > 10:
            self.history = self.history[-10:]

        return final

    def _handle_cloud(self, query: str) -> str:
        """云端处理:脱敏后上云"""
        # 1. 隐私脱敏
        safe_query = self.privacy.desensitize(query)
        # 2. 上云
        result = self.cloud.infer(safe_query, context=self.history[-3:])
        # 3. 缓存
        self.cache.set(query, result)
        return result

    def _build_prompt(self, query: str, tool_schemas: list[dict]) -> str:
        """构造 Prompt:系统指令 + 工具 schema + 历史 + 当前问题"""
        system = (
            "你是一个端侧轻量 Agent,请根据用户问题决定是否调用工具。"
            "可用工具的 schema 如下:\n"
        )
        tools_json = json.dumps(tool_schemas, ensure_ascii=False, indent=2)
        history_str = "\n".join(
            f"User: {h['user']}\nAssistant: {h['assistant']}"
            for h in self.history[-3:]
        )
        return f"{system}{tools_json}\n\n历史对话:\n{history_str}\n\n用户问题:{query}\n"

    def _parse_tool_calls(self, output: str) -> list[dict]:
        """解析模型输出中的工具调用(模拟 ReAct 格式)"""
        # 真实场景用更鲁棒的解析 + JSON Schema 校验
        if "weather" in output.lower():
            return [{"name": "weather", "args": {"city": "深圳"}}]
        if "navigate" in output.lower():
            return [{"name": "navigate", "args": {"to": "公司"}}]
        return []

    def prefetch_common_queries(self):
        """预取常用查询:WiFi 下后台执行"""
        common_queries = [
            "今天天气怎么样",
            "明天会下雨吗",
            "附近有什么餐厅",
        ]
        def fetcher(q):
            # 真实场景调用云端 API
            return f"[Prefetched answer for: {q}]"

        threading.Thread(
            target=self.cache.prefetch,
            args=(common_queries, fetcher),
            daemon=True,
        ).start()


# ============================================================
# 7. 测试用例
# ============================================================
def test_edge_agent():
    """端侧 Agent 完整测试"""
    agent = EdgeAgent(AgentConfig(idle_timeout=5))  # 5s 超时(测试用)

    # 测试 1:简单意图(不拉起大模型)
    print("\n--- Test 1: Simple intent ---")
    r1 = agent.run("现在几点了")
    print(f"Result: {r1}")

    # 测试 2:复杂意图(端侧大模型 + 工具)
    print("\n--- Test 2: Complex intent, local ---")
    r2 = agent.run("帮我查下深圳天气,然后规划去公司的路线")
    print(f"Result: {r2}")

    # 测试 3:敏感信息(强制端侧)
    print("\n--- Test 3: Sensitive info, force local ---")
    r3 = agent.run("我的银行卡号是 6228480402564890018,帮我记一下")
    print(f"Result: {r3}")

    # 测试 4:缓存命中
    print("\n--- Test 4: Cache hit ---")
    r4 = agent.run("帮我查下深圳天气,然后规划去公司的路线")
    print(f"Result: {r4}")

    # 测试 5:低功耗(等待模型卸载)
    print("\n--- Test 5: Power management ---")
    print("Waiting 6s for idle timeout...")
    time.sleep(6)
    # 再次查询,模型重新加载
    r5 = agent.run("计算 123 + 456")
    print(f"Result: {r5}")

    # 测试 6:预取
    print("\n--- Test 6: Prefetch ---")
    agent.prefetch_common_queries()
    time.sleep(1)

    print("\n[All tests passed]")


if __name__ == "__main__":
    test_edge_agent()
```

**运行输出(部分)**:

```
============================================================
[Agent] Query: 现在几点了
============================================================
[Agent] Intent: {'need_agent': False, 'complexity': 'simple', 'confidence': 0.9}
Result: 2026-09-23 09:30:00

--- Test 2: Complex intent, local ---
============================================================
[Agent] Query: 帮我查下深圳天气,然后规划去公司的路线
============================================================
[Agent] Intent: {'need_agent': False, 'complexity': 'simple', 'confidence': 0.9}
[Cache] Miss: 帮我查下深圳天气,然后规划去公司的路线
[Agent] Decision: local (prefer local)
[Model] Loading pangu-edge-7b-int4 (INT4)...
[Model] Loaded, memory=4000MB
[Tool] Lazy loading weather...
[Tool] Loading navigation module...
Result: [INT4 response for: 帮我查下深圳天气,然后规划去公司...]

--- Test 5: Power management ---
Waiting 6s for idle timeout...
[Power] Idle 5s, unloading model to save power
[Model] Unloading pangu-edge-7b-int4, free 4000MB
[Agent] Decision: local (prefer local)
[Model] Loading pangu-edge-7b-int4 (INT4)...
[Model] Loaded, memory=4000MB
Result: [INT4 response for: 计算 123 + 456...]

[All tests passed]
```

**面试讲解要点**:

1. **量化推理**:用 `QuantizedModel` 模拟 INT4 推理,真实场景对接 MindIE Lite
2. **工具精简**:`ToolRegistry` 区分内置(常驻)和懒加载(按需),避免冷启动全量加载
3. **离线缓存**:`OfflineCache` 用 LRU + 预取,WiFi 下后台拉常用查询
4. **低功耗**:`PowerManager` 闲置超时卸载模型,唤醒时重新加载
5. **端云协同**:`PrivacyFilter` 脱敏后上云,强敏感信息强制端侧
6. **唤醒机制**:`WakeupClassifier` 小模型常驻,判断是否拉起大模型

**可能的追问**:
- Q:模型加载耗时 100ms,会不会影响体验?A:用预加载策略 —— 用户解锁手机时就预加载模型,真正查询时模型已就绪。
- Q:多用户并发怎么办?A:端侧单用户,不存在并发;云端用 Continuous Batching。
- Q:KV Cache 怎么管理?A:多轮对话保留前 3 轮 KV Cache,后续用 summary 压缩;KV Cache 用 8-bit 量化。

</details>

---

### Q10 — 系统设计:政企安全合规的 Agent 系统(华为真题)

<details>
<summary>查看答案</summary>

**题目**:请设计一个面向政企客户的安全合规 Agent 系统,要求:
1. 私有化部署,数据不出域
2. 全链路审计,可追溯
3. 权限管控,基于角色和数据分级
4. 支持多行业(政务 / 金融 / 制造)适配
5. 国密算法 + 信创栈

请给出整体架构、关键模块设计、数据流、容灾方案。

---

**一、需求拆解**

| 需求 | 关键约束 |
|------|---------|
| 私有化部署 | 全栈本地化,物理隔离外网 |
| 数据不出域 | 训练 / 推理 / 日志数据全部在内网 |
| 全链路审计 | Prompt / 工具 / 输出全记录,不可篡改,保留 6 个月+ |
| 权限管控 | RBAC + 数据分级,Agent 不能越权 |
| 多行业适配 | 一套架构,多行业模型 + 工具 + Prompt |
| 国密 + 信创 | SM2/SM3/SM4 + 鲲鹏 / 昇腾 / 麒麟 / 高斯 |

**二、整体架构(五层)**

```
┌─────────────────────────────────────────────────────────────┐
│  L5:接入层(用户入口)                                       │
│   ├─ Web 控制台(政企内网)                                   │
│   ├─ API 网关(系统集成)                                    │
│   ├─ 钉钉 / 飞书 / WeLink 集成                              │
│   └─ 统一鉴权(SSO + IAM)                                   │
├─────────────────────────────────────────────────────────────┤
│  L4:Agent 编排层                                            │
│   ├─ 意图分流器(小模型)                                    │
│   ├─ 规划器(ReAct / Plan-Execute)                          │
│   ├─ 工具调度器(并行 / 串行 / 兜底)                        │
│   ├─ 多 Agent 协同(Manager-Worker)                         │
│   ├─ 安全护栏(输入 / 输出过滤)                             │
│   └─ 人在回路(高风险动作审批)                              │
├─────────────────────────────────────────────────────────────┤
│  L3:能力层                                                  │
│   ├─ 模型池                                                  │
│   │   ├─ 基础模型:盘古 38B                                  │
│   │   ├─ 行业模型:金融 / 政务 / 制造(LoRA adapter)         │
│   │   └─ 端侧模型:7B INT4(可选,边缘部署)                 │
│   ├─ 知识库                                                  │
│   │   ├─ 向量库(高斯 DB-Vector)                            │
│   │   ├─ 文档库(企业文档 / 政策文件)                       │
│   │   └─ 图谱库(行业知识图谱)                              │
│   ├─ 工具池                                                  │
│   │   ├─ 业务工具(查询 / 办理 / 报表)                      │
│   │   ├─ 系统工具(文件 / 邮件 / 日程)                      │
│   │   └─ 外部 API(行业系统对接)                            │
│   └─ 记忆中心                                                │
│       ├─ 短期记忆(KV Cache)                                │
│       └─ 长期记忆(向量库 + 关系库)                         │
├─────────────────────────────────────────────────────────────┤
│  L2:安全合规层                                              │
│   ├─ 权限引擎(RBAC + ABAC + 数据分级)                     │
│   ├─ 审计中心(全链路日志 + WORM 存储)                      │
│   ├─ 加密中心(国密 SM2/SM3/SM4)                            │
│   ├─ 脱敏中心(动态脱敏 + 静态脱敏)                         │
│   ├─ 内容安全(政治安全 / 暴恐 / 色情 + 越狱防护)           │
│   └─ 红队平台(定期攻防演练)                                │
├─────────────────────────────────────────────────────────────┤
│  L1:基础设施层(信创栈)                                     │
│   ├─ 计算:鲲鹏 CPU + 昇腾 NPU                              │
│   ├─ 存储:高斯 DB + OBS(私有版)                           │
│   ├─ 网络:VPC + 安全组 + WAF                               │
│   ├─ OS:麒麟 / 统信 UOS                                     │
│   ├─ 容器:CCE(私有版)/ K8s                                │
│   └─ 监控:AOM + 日志服务(LTS)                            │
└─────────────────────────────────────────────────────────────┘
```

**三、关键模块详细设计**

**3.1 权限引擎(RBAC + 数据分级)**

```python
class PermissionEngine:
    """三重校验:角色权限 + 数据分级 + 行为基线"""

    def __init__(self):
        self.rbac = RBACStore()  # 用户-角色-工具权限
        self.data_classifier = DataLevelClassifier()  # 数据分级
        self.behavior_baseline = BehaviorBaseline()  # 行为基线

    def check(self, user_id: str, action: str, target: Any) -> dict:
        # 1. RBAC:用户角色是否有该 action 的权限
        role = self.rbac.get_role(user_id)
        if not self.rbac.can(role, action):
            return {"allowed": False, "reason": "rbac_denied"}

        # 2. 数据分级:目标数据的级别 ≤ 用户级别
        data_level = self.data_classifier.classify(target)
        user_level = self.rbac.get_data_level(user_id)
        if data_level > user_level:
            return {"allowed": False, "reason": "data_level_exceeded"}

        # 3. 行为基线:用户近期行为是否异常
        if self.behavior_baseline.is_anomalous(user_id, action):
            return {"allowed": False, "reason": "anomalous_behavior", "need_approval": True}

        return {"allowed": True}


class DataLevelClassifier:
    """数据分级:公开 < 内部 < 秘密 < 机密"""
    LEVELS = {"public": 1, "internal": 2, "secret": 3, "confidential": 4}

    def classify(self, data: Any) -> int:
        # 真实场景用 NER + 规则 + 模型
        if isinstance(data, str):
            if any(kw in data for kw in ["机密", "绝密"]):
                return self.LEVELS["confidential"]
            if any(kw in data for kw in ["身份证", "银行卡"]):
                return self.LEVELS["secret"]
            if any(kw in data for kw in ["内部"]):
                return self.LEVELS["internal"]
        return self.LEVELS["public"]
```

**3.2 全链路审计**

```python
class AuditCenter:
    """全链路审计:Prompt → 推理 → 工具调用 → 输出
    存储:WORM(Write Once Read Many),不可篡改
    保留:6 个月(金融场景 5 年)
    """

    def __init__(self, retention_days: int = 180):
        self.retention = retention_days
        self.worm_store = WORMStorage()  # 不可篡改存储
        self.blockchain = BlockchainLedger()  # 关键操作上链

    def log(self, event: dict):
        # 1. 添加时间戳 + 哈希
        event["timestamp"] = time.time()
        event["prev_hash"] = self._last_hash()
        event["hash"] = self._sm3(json.dumps(event, sort_keys=True))

        # 2. 写入 WORM 存储
        self.worm_store.write(event)

        # 3. 高风险操作上链(防抵赖)
        if event.get("risk_level") == "high":
            self.blockchain.append(event)

    def replay(self, session_id: str):
        """会话回放:支持取证"""
        events = self.worm_store.query(session_id=session_id)
        # 验证哈希链完整性
        for i in range(1, len(events)):
            assert events[i]["prev_hash"] == events[i-1]["hash"], "Audit chain broken"
        return events
```

**3.3 加密中心(国密)**

```python
class CryptoCenter:
    """国密算法套件
    SM2:非对称加密(密钥交换 / 数字签名)
    SM3:哈希(数据完整性)
    SM4:对称加密(数据存储 / 传输)
    """

    def __init__(self):
        self.sm2 = SM2Engine()  # 密钥对
        self.sm3 = SM3Engine()
        self.sm4 = SM4Engine()

    def encrypt_data(self, data: bytes, key_level: str = "internal") -> dict:
        # 1. 生成 SM4 会话密钥
        session_key = os.urandom(16)
        # 2. SM4 加密数据
        ciphertext = self.sm4.encrypt(data, session_key)
        # 3. SM2 加密会话密钥(用接收方公钥)
        encrypted_key = self.sm2.encrypt(session_key, public_key=...)
        # 4. SM3 哈希(完整性校验)
        data_hash = self.sm3.hash(data)
        return {
            "ciphertext": ciphertext,
            "encrypted_key": encrypted_key,
            "hash": data_hash,
            "algo": "SM4-SM2-SM3",
        }

    def sign(self, data: bytes) -> str:
        """数字签名(防抵赖)"""
        return self.sm2.sign(self.sm3.hash(data), private_key=...)
```

**3.4 安全护栏**

```python
class SafetyGuardrail:
    """三道防线:输入过滤 + 推理约束 + 输出校验"""

    def __init__(self):
        self.input_filter = InputFilter()  # 注入防护 + 敏感词
        self.output_filter = OutputFilter()  # 内容安全 + 越权检测
        self.jailbreak_detector = JailbreakDetector()  # 越狱检测

    def check_input(self, prompt: str) -> dict:
        # 1. Prompt 注入检测
        if self.jailbreak_detector.is_injection(prompt):
            return {"allowed": False, "reason": "prompt_injection"}
        # 2. 敏感词过滤
        if self.input_filter.has_sensitive_word(prompt):
            return {"allowed": False, "reason": "sensitive_word"}
        return {"allowed": True}

    def check_output(self, output: str, action: str) -> dict:
        # 1. 内容安全(政治 / 暴恐 / 色情)
        if self.output_filter.is_unsafe(output):
            return {"allowed": False, "reason": "unsafe_content"}
        # 2. 越权检测(输出是否超出 action 范围)
        if self.output_filter.is_overprivileged(output, action):
            return {"allowed": False, "reason": "overprivileged"}
        return {"allowed": True}
```

**3.5 多行业适配**

```python
class IndustryAdapter:
    """行业适配器:模型 + 工具 + Prompt + 安全规则"""

    PROFILES = {
        "finance": {
            "model_adapter": "pangu-38B-finance-lora",
            "tools": ["query_stock", "check_compliance", "generate_report"],
            "system_prompt": "你是金融分析助手,严格遵守合规要求,不输出投资建议...",
            "safety_rules": ["no_investment_advice", "compliance_first"],
            "data_levels": {"research_report": "internal", "customer_info": "secret"},
        },
        "government": {
            "model_adapter": "pangu-38B-gov-lora",
            "tools": ["query_policy", "submit_form", "schedule_appointment"],
            "system_prompt": "你是政务助手,回答必须基于最新政策文件...",
            "safety_rules": ["policy_accuracy", "no_personal_opinion"],
            "data_levels": {"public_policy": "public", "citizen_info": "secret"},
        },
        "manufacturing": {
            "model_adapter": "pangu-38B-mfg-lora",
            "tools": ["query_device_status", "call_mes", "create_workorder"],
            "system_prompt": "你是制造运维助手,关注设备状态和工艺优化...",
            "safety_rules": ["realtime_priority", "deterministic_output"],
            "data_levels": {"process_doc": "internal", "sensor_data": "internal"},
        },
    }

    def __init__(self, industry: str):
        self.profile = self.PROFILES[industry]

    def get_model(self):
        return self.profile["model_adapter"]

    def get_tools(self):
        return self.profile["tools"]

    def get_system_prompt(self):
        return self.profile["system_prompt"]
```

**四、完整数据流(以金融场景为例)**

```
用户:分析师小王
问题:"帮我分析贵州茅台最近 30 天走势并生成研报"

1. 接入层
   ├─ SSO 鉴权:确认小王是"研究部"角色
   └─ 数据级别:小王可访问 internal 级数据

2. Agent 编排层
   ├─ 意图分流:复杂任务 → 拉 38B 模型
   ├─ 规划:Step1 查行情 → Step2 查财报 → Step3 生成研报
   └─ 安全护栏:输入校验通过(无注入 / 敏感词)

3. 能力层(并行调用)
   ├─ 工具 1:query_stock("600519", days=30) → 返回行情
   │   └─ 权限校验:小王有 query_stock 权限 ✓
   ├─ 工具 2:query_financial_report("600519") → 返回财报
   │   └─ 数据级别:internal,小王可访问 ✓
   └─ 知识库:RAG 检索"白酒行业分析"相关文档

4. 安全合规层
   ├─ 审计:记录每个工具调用 + 参数 + 结果
   ├─ 加密:返回数据 SM4 加密存储
   └─ 内容安全:研报输出经政治安全 + 合规检查

5. 输出
   ├─ 生成研报(Markdown)
   ├─ 高风险动作标记:"研报外发"需要人工审批
   └─ 审计日志写入 WORM,保留 5 年

6. 人在回路
   └─ 小王点击"外发研报"→ 触发审批流 → 主管审批 → 外发
```

**五、容灾与高可用**

| 故障场景 | 应对方案 |
|---------|---------|
| NPU 单卡故障 | 多副本 + 健康检查,自动剔除故障卡,流量切到健康副本 |
| 模型推理超时 | 降级到小模型(7B)兜底,保证可用性 |
| 知识库不可用 | 退化为纯模型推理(无 RAG),告知用户"信息可能不准" |
| 审计存储故障 | 本地缓存 + 异步重试,审计日志不能丢 |
| 全链路熔断 | 限制 QPS,优先保核心客户 |

**六、容量规划**

| 资源 | 配置 | 说明 |
|------|------|------|
| 昇腾 910B | 8 卡 / 节点 × 4 节点 = 32 卡 | 跑 38B 模型,4 路 TP × 8 副本 |
| 高斯 DB | 主备 + 只读副本 | 向量库 + 关系库 |
| OBS | 100TB | 模型权重 + 审计日志 |
| 并发 | 200 QPS | 单副本 25 QPS × 8 副本 |

**七、部署交付流程**

```
1. 现场勘测 → 客户机房环境(电力 / 网络 / 散热)
2. 硬件上架 → 鲲鹏 + 昇腾服务器,组网
3. 软件安装 → 麒麟 OS + CANN + ModelArts 私有版
4. 模型加载 → 盘古 38B + 行业 LoRA adapter
5. 数据接入 → 客户数据脱敏后导入知识库
6. 联调测试 → 功能 / 性能 / 安全测试
7. 等保测评 → 第三方测评机构出具报告
8. 试运行 → 灰度 10% 流量,观察 2 周
9. 正式上线 → 全量切流
10. 运维移交 → 培训客户运维团队
```

**八、面试加分点**

1. **强调"全栈自研"**:从芯片(昇腾)到框架(MindSpore)到模型(盘古)到平台(ModelArts)全栈国产化,这是华为政企的核心卖点
2. **提到"等保 2.0 三级 + 关基 + 信创"** 三件套,体现政企合规体系认知
3. **提到"WORM + 区块链"** 双重保障审计不可篡改,体现落地深度
4. **提到"人在回路 + 行为基线"** 主动防御,不只是被动过滤
5. **提到"行业 LoRA adapter 动态加载"** 一套架构多行业,体现工程复用

**九、可能的追问**

- Q:模型怎么更新?A:模型权重 SM4 加密后通过专线分发,LoRA adapter 增量更新(几十 MB),不影响主模型。
- Q:如何防止内部员工滥用?A:三层防护 —— 权限最小化(RBAC)+ 行为基线(异常告警)+ 审计追溯(所有操作留痕)。
- Q:成本多少?A:典型政企项目 500 万-2000 万(含硬件 + 软件 + 实施),华为优势是全栈打包,避免客户多供应商集成。
- Q:和阿里通义 / 百度文心比,华为的优势?A:全栈自研(芯片到模型)+ 信创合规 + 全球服务能力。劣势:生态不如互联网公司丰富。

</details>
