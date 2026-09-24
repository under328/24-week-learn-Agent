# Day 34 — LLM 与 Transformer 基础

> **学习目标**: 补齐 Agent 工程师最关键的底层知识缺口 —— LLM 模型本身的原理。完成后你应该能讲清楚:Transformer 的注意力机制怎么算、为什么用多头、Pre-training 到 RLHF 的完整流程、LoRA 为什么省参数、KV-Cache 为什么能加速。这是区分"会调 API"和"懂原理"的分水岭。
>
> **适用人群**: 转型 Agent 方向的工程师(尤其是后端/移动端背景,缺乏 ML/DL 基础),面试前快速补齐 LLM 底层知识。
>
> **今日时长**: 5-6 小时,10 道题逐道消化,Q2 手算和 Q9 代码题务必亲手做一遍。
>
> **核心心法**: Agent 工程师不需要会训模型,但必须懂模型。面试官挖底层时在问四件事 —— ①你知不知道 Agent 背后"大脑"怎么工作(选型有依据); ②你能不能诊断模型相关问题(幻觉/重复/长上下文失效); ③你理不理解成本与效果的 trade-off(量化/部署); ④你有没有持续学习能力。

---

## 为什么 Agent 工程师必须懂模型底层?

"我用 LangChain 调 API 就够了" —— 这个想法在 2026 年面试中会直接被淘汰。四个原因:

1. **面试区分度**: 当所有人都会讲 ReAct/RAG,面试官往下挖"ReAct 里 Thought 为什么能遵循格式" → 你得知道自回归生成和指令微调;不懂底层追问两层就崩。
2. **模型选型有依据**: 选 GPT-4o 还是 Llama-3?你得知道 Decoder-only 特点、KV-Cache 内存、量化对效果影响,否则选型就是"听说这个好"。
3. **问题诊断**: Agent 幻觉/重复/长上下文遗忘,根因在模型层。不懂 Attention 不知道"中间遗忘"(attention 稀释);不懂采样不知道 temperature=0 为什么还不稳定。
4. **成本优化**: 部署 7B 模型要不要量化?KV-Cache 占多少显存?这些是工程问题,前提是懂模型结构。

---

## 今日知识图谱

```
LLM 知识体系 (Agent 工程师必备)
│
├── 1. 模型架构层 ★★★★★ (必问)
│   ├── Transformer 基础 ──── Encoder-Decoder / Self-Attention (Q1,Q2)
│   ├── Multi-Head Attention ─ 为什么多头 / 头数选择 (Q3)
│   ├── Position Encoding ─── 正余弦 / RoPE / ALiBi (Q4)
│   ├── Feed-Forward / LayerNorm / 残差 ─ (Q1)
│   └── 架构变体 ──────────── GPT vs BERT vs T5 vs Llama (Q6)
│
├── 2. 训练流程层 ★★★★★ (区分度高)
│   ├── Pre-training ──── 自回归 / MLM / 数据规模 (Q5)
│   ├── SFT ──────────── 指令数据 / loss masking (Q5,Q8)
│   ├── RLHF ─────────── 奖励模型 / PPO / KL 散度 (Q5)
│   ├── DPO ──────────── 无需 RM / 偏好直接优化 (Q5)
│   └── Fine-tuning ──── LoRA / QLoRA / Prefix Tuning (Q8)
│
├── 3. 推理优化层 ★★★★ (工程必考)
│   ├── KV-Cache ──────── 原理 / 内存占用 (Q7)
│   ├── 量化 ──────────── INT8/INT4 / GPTQ / AWQ (Q7)
│   ├── 投机解码 ──────── Draft 模型 / 接受率 (Q7)
│   ├── Flash Attention ─ IO-aware / tiling (Q7)
│   └── PagedAttention ── vLLM / 分页管理 (Q7)
│
└── 4. 前沿方向 ★★★ (加分)
    ├── 长上下文 ── RoPE 外推 / Ring Attention
    ├── MoE ─────── 路由 / 稀疏激活 / DeepSeek
    └── 推理模型 ── o1 / CoT / Process Reward
```

---

## 面试题(共 10 道)

> 每道题先自己口头答一遍(录音),再对照参考答案。Q2 手算和 Q9 代码题务必亲做,面试会现场推导或写代码。

---

### Q1: 完整描述 Transformer 架构,包括 Encoder-Decoder、Self-Attention、Multi-Head Attention、Position Encoding、FFN、Layer Norm、残差连接。画架构图。

<details>
<summary>点击查看参考答案</summary>

#### 整体架构

Transformer 是 2017 年 Google《Attention is All You Need》提出的完全基于 Attention 的序列建模架构。原始是 Encoder-Decoder(机器翻译),后续演化出三种变体:
- **Encoder-only** (BERT): 适合理解类任务(分类/NER/检索)
- **Decoder-only** (GPT 系列): 适合生成类任务,现代 LLM 主流
- **Encoder-Decoder** (T5/BART): 适合 Seq2Seq(翻译/摘要)

#### 架构图

```
                Encoder (×N)                    Decoder (×N)
┌──────────────────────────┐    ┌──────────────────────────────────┐
│ Input Embedding          │    │ Output Embedding (偏移)           │
│   + Position Encoding    │    │   + Position Encoding             │
│         │                │    │         │                         │
│         ▼                │    │         ▼                         │
│ ┌────────────────────┐   │    │ ┌──────────────────────┐  残差    │
│ │ Multi-Head         │◄──┼────┼─│ Masked Multi-Head    │◄────┐   │
│ │ Self-Attention     │   │    │ │ Attention (因果mask) │     │   │
│ └────────┬───────────┘   │    │ └──────────┬───────────┘     │   │
│          ▼               │    │            ▼                 │   │
│      Add + LayerNorm     │    │       Add + LayerNorm ───────┘   │
│          │               │    │            │                     │
│          ▼               │    │            ▼                     │
│ ┌────────────────────┐   │    │ ┌──────────────────────┐  残差    │
│ │ Feed-Forward       │◄──┼────┼─│ Cross-Attention      │◄────┐   │
│ │ Network (两层MLP)  │   │    │ │ (Q←Dec, K/V←Enc)    │     │   │
│ └────────┬───────────┘   │    │ └──────────┬───────────┘     │   │
│          ▼               │    │            ▼                 │   │
│      Add + LayerNorm     │    │       Add + LayerNorm ───────┘   │
└──────────┬───────────────┘    │            │                     │
           │                    │            ▼                     │
           └────────────────────┤ ┌──────────────────────┐  残差    │
                                │ │ Feed-Forward Network │◄────┐   │
                                │ └──────────┬───────────┘     │   │
                                │            ▼                 │   │
                                │       Add + LayerNorm ───────┘   │
                                │            │                     │
                                │            ▼                     │
                                │   Linear + Softmax → 概率分布    │
                                └──────────────────────────────────┘
```

#### 各组件详解

**(1) Self-Attention**: 序列每个位置"看到"所有其他位置(Decoder 只能看前面),通过 Q/K/V 三元组计算注意力权重。详见 Q2。

**(2) Multi-Head Attention**: 将 Q/K/V 投影到多个子空间分别做 Attention 再拼接。让模型在不同子空间关注不同模式(语法/语义/指代)。详见 Q3。

**(3) Position Encoding**: Self-Attention 是排列不变的(打乱顺序结果不变),需显式注入位置信息。原始论文用正弦/余弦,现代 LLM 用 RoPE。详见 Q4。

**(4) Feed-Forward Network**: 每个位置独立过两层线性变换 + 激活:
```
FFN(x) = activation(x·W1 + b1) · W2 + b2
```
- 第一层 d_model → d_ff(通常 4×d_model),第二层压缩回 d_model
- 激活:原始 ReLU,现代 Llama 用 SwiGLU(门控机制,效果更好但参数多 1/3)
- Attention 负责跨位置信息融合,FFN 负责单位置非线性变换,两者互补

**(5) Layer Normalization**: 每个样本在特征维度归一化: `LN(x) = γ·(x-μ)/√(σ²+ε) + β`。稳定训练。
- **Post-LN**(原始): `LN(x + Sublayer(x))` —— 训练不稳定,需 warmup
- **Pre-LN**(GPT/Llama): `x + Sublayer(LN(x))` —— 训练稳定,现代主流
- **RMSNorm**(Llama): 去掉均值中心化,只做方差归一化,更快

**(6) 残差连接**: `output = x + Sublayer(x)`,每个 Attention/FFN 外都包一层。缓解梯度消失,允许网络更深,信息可"绕过"某些层。

#### 追问应对

**为什么 Decoder-only 成为主流?** ①训练效率高 —— 每个位置都是监督信号(预测下一个 token),数据利用率高;②Scaling Law 表现好 —— 足够规模下效果最好(GPT-3 论证);③工程简单 —— 统一架构,自回归推理容易优化(KV-Cache)。

**SwiGLU 为什么比 ReLU 好?** SwiGLU = Swish × 门控。引入门控机制让网络动态选择信息通过;Swish 比 ReLU 更平滑(处处可导),梯度流更好。代价是参数多 1/3,所以 d_ff 缩到 2/3 倍。

</details>

---

### Q2: 详细描述 Self-Attention 计算过程(Q/K/V、缩放点积、Softmax、权重)。手算一个简单示例。为什么除以 √d_k?

<details>
<summary>点击查看参考答案</summary>

#### 计算公式

```
Attention(Q, K, V) = Softmax(Q · K^T / √d_k) · V
```
- **Q (Query)**: (seq_len, d_k),"我要找什么"
- **K (Key)**: (seq_len, d_k),"我有什么可被找"
- **V (Value)**: (seq_len, d_v),"我的实际内容"

#### 计算步骤

```
Step 1: Q = X·W_Q, K = X·W_K, V = X·W_V   (投影)
Step 2: scores = Q · K^T                    (注意力分数, seq×seq)
Step 3: scaled = scores / √d_k              (缩放)
Step 4: weights = Softmax(scaled, axis=-1)  (归一化, 每行和为1)
Step 5: output = weights · V                (加权求和)
```

#### 手算示例(seq=2, d_k=2)

```
X = [[1,0],[0,1]]
W_Q = W_K = [[1,0],[0,1]]  →  Q = K = [[1,0],[0,1]]
W_V = [[1,2],[3,4]]        →  V = [[1,2],[3,4]]

Step 2: scores = Q·K^T = [[1,0],[0,1]]  (单位矩阵)

Step 3: √d_k = √2 ≈ 1.414
  scaled = [[0.707, 0], [0, 0.707]]

Step 4: Softmax(每行):
  第一行 [0.707, 0]: exp=[2.028, 1.000], 和=3.028
    weights[0] = [0.670, 0.330]
  第二行 [0, 0.707]: exp=[1.000, 2.028], 和=3.028
    weights[1] = [0.330, 0.670]

Step 5: output = weights · V
  output[0] = 0.670×[1,2] + 0.330×[3,4] = [1.660, 2.660]
  output[1] = 0.330×[1,2] + 0.670×[3,4] = [2.340, 3.340]

output = [[1.660, 2.660], [2.340, 3.340]]
```

**直觉**: 位置 0 更关注自己(权重 0.67),所以输出偏向 V[0]=[1,2];位置 1 同理偏向 V[1]=[3,4]。

#### 为什么除以 √d_k?

**核心:控制点积方差,防止 Softmax 饱和。**

假设 Q/K 元素独立、均值 0、方差 1,点积 `Q·K^T = Σ_{i=1}^{d_k} q_i·k_i` 的方差为 d_k,标准差 √d_k。d_k 大时(如 64,标准差 8),点积数值大,Softmax 进入饱和区(梯度≈0)。

例: d_k=512 时点积可能 ±22,`exp(22)/(exp(22)+exp(-22))≈1.0`(只关注一个位置),梯度≈0 无法学习。除以 √d_k 后方差归一到 1,Softmax 处于平滑区,梯度健康。

**直觉**: 像考试评分,满分 1000 分时 99% 的人集中在 800-1000 区分度低;归一化到 100 分制区分度就出来了。√d_k 就是换算系数。

#### 追问应对

**Q/K/V 为什么用不同矩阵?** 直接用 X 的话 Query=Key,attention 退化为自相似度,表达力受限。不同投影矩阵让模型学习"用什么查""暴露什么被查""提供什么内容"三个语义角色。

**Attention 复杂度?** 时间 O(seq²·d_k)(Q·K^T),空间 O(seq²)(权重矩阵)。这是长上下文瓶颈,Flash Attention/稀疏 Attention 要解决的。

</details>

---

### Q3: 为什么用 Multi-Head Attention?多头怎么计算?头数怎么选?参数量分析。

<details>
<summary>点击查看参考答案</summary>

#### 为什么用多头?

单头只能学一种关注模式,但语言关系是多维的(语法/语义/指代同时存在)。多头把 Q/K/V 投影到多个子空间,每个头学不同模式:
- Head 1: 语法依赖(动词→名词)
- Head 2: 指代消解(代词→先行词)
- Head 3: 长距离依赖(句首→句尾)

类似 CNN 用多个卷积核检测不同特征。

#### 计算过程

```
输入 X: (seq_len, d_model), 头数 h, d_k = d_model/h

Step 1: 每个头独立投影
  Q_i = X·W_Q^i, K_i = X·W_K^i, V_i = X·W_V^i  (seq, d_k)
  head_i = Attention(Q_i, K_i, V_i)              (seq, d_k)

Step 2: 拼接
  concat = [head_1; ...; head_h]  (seq, h·d_k) = (seq, d_model)

Step 3: 输出投影
  output = concat · W_O  (seq, d_model)
```

#### 参数量分析

```
Q/K/V/O 各: d_model × d_model
总计: 4 × d_model²

关键: 无论头数 h 多少,总参数量 = 4×d_model²(因 h×d_k = d_model)
头数改变"如何分组",不改变"总参数量"
```

例: d_model=768(BERT-base),4×768² ≈ 2.36M,无论 h=12(每头 64 维)还是 h=8(每头 96 维)都一样。

#### 头数选择

经验: d_k 在 64~128 是甜点区。
- BERT-base: d_model=768, h=12, d_k=64
- GPT-3: d_model=12288, h=96, d_k=128
- Llama-3-70B: d_model=8192, h=64, d_k=128

头数太少 → 模式不够多样;头数太多 → 单头维度过小,表达力不足。

**MHA vs MQA vs GQA**(减少 KV-Cache):
- MHA: 每头独立 Q/K/V(标准)
- MQA: Q 多头,K/V 共享一个(省显存但效果略掉)
- GQA: Q 分组,K/V 每组共享(Llama-2/3 用,平衡效果和效率)

#### 追问应对

**GQA 为什么省 KV-Cache?** KV-Cache 大小 ∝ num_kv_heads。MQA 降到 1,GQA 降到 num_q_heads/group_size。Llama-3-70B: Q 头 64,KV 头 8(GQA group=8),KV-Cache 省 8 倍,效果几乎不掉。

**多头一定比单头好?** 不一定。d_model 小时(如 256)强行拆 16 头,每头 16 维表达力不够。多头价值在大模型(大 d_model)时更明显。有研究("Are Sixteen Heads Really Better than One?")发现很多头可剪枝。

</details>

---

### Q4: 讲讲 Position Encoding。正弦余弦、RoPE、ALiBi 各是什么?为什么需要位置信息?

<details>
<summary>点击查看参考答案</summary>

#### 为什么需要位置信息?

Self-Attention 是**排列不变的** —— 打乱输入顺序,输出只是重排,数值对应。"猫追狗"和"狗追猫"在 Attention 看来一样,必须显式注入位置。

两种方式:绝对位置编码(加到 embedding)、相对位置编码(在 Attention 计算时考虑相对距离)。

#### 正弦余弦位置编码(Sinusoidal)

原始 Transformer 方法:
```
PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
x = embedding(token) + PE(pos)
```
- 固定(非学习),不同维度不同频率正弦波
- 理论可外推(公式对任意 pos 成立),但实际外推效果差(没见过那些位置)

#### RoPE(旋转位置编码,Llama/GLM/Qwen 用)

核心: 不直接加位置编码,而在 Attention 时对 Q/K 做旋转,使 `Q·K^T` 只依赖相对位置。

```
q'_m = R(m) · q_m   (R(m) 是旋转矩阵)

结果: q_m · k_n = |q||k|·cos((m-n)·θ)  ← 只依赖 (m-n)
```

**优点**: 相对位置 → 泛化好;可外推(配合 scaling);计算高效(只旋转不加参数)。

**外推问题与解决**:
- 原始 RoPE 训练 2k 推理 4k 效果会掉
- Position Interpolation(PI): 位置压缩到训练范围
- NTK-aware scaling: 调整 θ 基数,高频不外推、低频外推
- YaRN: 分频率段精细处理

#### ALiBi(Attention with Linear Biases)

完全不用位置编码,在 Attention 分数加线性 bias:
```
scores[i][j] = Q[i]·K[j] - m·|i - j|   (m 是每个头的固定斜率)
```
- 无任何位置参数,天然支持外推(长序列只是 bias 更大)
- 绝对位置信息弱,对需精确位置的任务(代码)不如 RoPE

#### 对比表

| 特性 | Sinusoidal | Learned PE | RoPE | ALiBi |
|------|-----------|------------|------|-------|
| 位置类型 | 绝对 | 绝对 | 相对 | 相对 |
| 可学习 | 否 | 是 | 否 | 否 |
| 外推能力 | 差 | 差 | 中(配scaling好) | 好 |
| 代表模型 | 原始Transformer | BERT/GPT-2 | Llama/Qwen | BLOOM |

#### 追问应对

**为什么主流 LLM 用 RoPE?** ①相对位置符合语言直觉("我爱你"vs"你爱我"差别在相对顺序);②外推能力强(配合 PI/YaRN 扩展上下文);③实验效果好(相同数据下长文本优于绝对位置)。

**RoPE 怎么做长上下文扩展?** 核心"位置缩放"。训练 seq=4096 想推理 32768:PI 把位置 m 缩为 m×(4096/32768);NTK 调大 θ 基数让低频外推高频不变;YaRN 分频段处理(高频不插值/中频线性/低频外推)。

</details>

---

### Q5: 完整描述 LLM 训练流程:Pre-training → SFT → RLHF → DPO。各阶段目标和方法。

<details>
<summary>点击查看参考答案</summary>

#### 全景图

```
Stage 1: Pre-training (预训练)
  目标: 语言基础能力(语法/知识/推理)
  数据: 万亿 token 无标注(网页/书籍/代码)
  方法: 自回归预测下一个 token
  产出: Base Model (Llama-3-8B-Base)
  成本: 千万~亿美元
        │
        ▼
Stage 2: Post-training (后训练/对齐)
  ├── 2a. SFT (监督微调)
  │     目标: 遵循指令,格式化回答
  │     数据: 万~百万指令对
  │     产出: Instruct Model
  │
  ├── 2b. RLHF (人类反馈强化学习)
  │     目标: 对齐人类偏好
  │     方法: RM + PPO + KL 惩罚
  │
  └── 2c. DPO (直接偏好优化)
        目标: 同 RLHF,更简单
        方法: 偏好对直接优化
```

#### Stage 1: Pre-training

**目标**: 学语言统计规律(语法/世界知识/基础推理)。

**数据**: GPT-3 用 300B token,Llama-3 用 15T token。来源:网页(Common Crawl)/书籍/代码/数学。清洗:去重(MinHash)/质量过滤/去隐私。

**方法(自回归)**:
```
输入 "The cat sat on the" → 预测 "mat"
P(x_1..x_n) = Π P(x_t | x_{<t})
Loss = -Σ log P(x_t | x_{<t})
```
每个 token 都是监督信号,数据效率高(对比 BERT 的 MLM 只对 15% token 有损失)。

**关键概念**:
- Scaling Law: 效果取决于参数 N、数据 D、算力 C
- Chinchilla 法则: 最优数据量 ≈ 20×参数量(70B 模型用 1.4T token)
- 现代实践(Llama-3): "过训练" —— 更多数据训更小模型,推理更便宜

#### Stage 2a: SFT(监督微调)

**目标**: 让 Base Model"听指令" —— 给 instruction 输出格式化有帮助回答。

**数据**: 万~百万条 `{"instruction":..., "output":...}`。来源:人工标注(贵但质量高)/GPT-4 生成(Distillation,Alpaca 52k)/开源数据集(ShareGPT)。**质量 > 数量**(LIMA 论证 1000 条高质量就能 SFT)。

**方法**: 
```
序列: "<instruction>{instr}</instruction><output>{out}</output>"
Loss 只在 output 部分计算(loss masking) —— 不让模型记住指令,只学如何回答
```

**效果**: Base 只会"续写"(给"什么是 RAG?"可能续写"什么是 RAG?它是一种..."),SFT 后能直接回答。

#### Stage 2b: RLHF

**动机**: SFT 学了"怎么回答",但不知道"什么是好回答"。人类偏好复杂(更安全/更有帮助/更简洁),SFT 难捕捉。

**三步走**:
```
Step 1: 训练 Reward Model (RM)
  - 收集偏好数据: 同一 prompt 生成多回答,人工排序(A>B>C)
  - RM: 输入(prompt, response) → 标量分数
  - Loss (Bradley-Terry): -log σ(r(chosen) - r(rejected))
  - RM 通常用 SFT Model 初始化,换输出 head

Step 2: PPO 优化策略
  - 生成回答 → RM 打分 → PPO 更新模型最大化 reward
  - 关键: 加 KL 散度防止 reward hacking
    Loss = -E[r(response)] + β·KL(π_new ‖ π_SFT)
  - β 控制"偏离 SFT 程度"

Step 3: 可多轮迭代(收集偏好→更新RM→PPO)
```

**问题**: 流程复杂(RM+PPO+KL);训练不稳定;Reward Hacking;需同时维护 4 个模型(policy/ref/RM/value)。

#### Stage 2c: DPO(直接偏好优化)

**动机**: RLHF 太复杂,能否跳过 RM 和 PPO?

**核心 insight**: RLHF 最优解有闭式形式:
```
π*(y|x) = π_SFT(y|x) · exp(r(x,y)/β) / Z(x)
→ 反推: r(x,y) = β·log(π(y|x)/π_SFT(y|x)) + β·log Z(x)
```
代入 Bradley-Terry 偏好损失,得 DPO Loss:
```
L_DPO = -E[log σ(β·(log π(y_w|x)/π_SFT(y_w|x) - log π(y_l|x)/π_SFT(y_l|x)))]
  y_w = chosen, y_l = rejected, π_SFT 冻结, π 待优化
```

**优势**: 无需 RM;无需 PPO(离线训练);只用偏好对标准交叉熵;训练稳定;效果接近 RLHF。
**劣势**: 离线(不能 on-policy 探索);对数据质量敏感;可能过度优化。

#### 对比表

| 阶段 | 目标 | 数据 | 方法 | 难度 |
|------|------|------|------|------|
| Pre-training | 语言能力 | 万亿token无标注 | 自回归 | 极高(算力) |
| SFT | 遵循指令 | 万~百万指令对 | 监督学习 | 中 |
| RLHF | 对齐偏好 | 人工排序 | RM+PPO | 高(工程) |
| DPO | 对齐偏好 | 偏好对 | 直接优化 | 低 |

#### 追问应对

**为什么不能直接用偏好数据 SFT?** SFT 需"标准答案",但偏好数据只有"哪个更好"无绝对正确答案。DPO 巧妙之处:不需绝对 label,只比较 chosen/rejected 的 log-prob 差。

**RLHF 和 DPO 哪个好?** 无绝对结论。早期 DPO 略逊(离线),后续改进(SimPO/ORPO)追平甚至超过。Llama-3 同时用 RLHF+DPO;GPT-4 仍以 RLHF 为主。选型看团队能力和数据。

</details>

---

### Q6: 对比主流 LLM 架构:GPT(Decoder-only)、BERT(Encoder-only)、T5(Encoder-Decoder)、Llama(改进)。为什么 GPT 选 Decoder-only?

<details>
<summary>点击查看参考答案</summary>

#### 三大架构对比

```
┌──────────────┬────────────────┬─────────────────┬─────────────────┐
│    架构       │  Encoder-only   │   Decoder-only   │ Encoder-Decoder │
│              │   (BERT)        │   (GPT)          │   (T5)          │
├──────────────┼────────────────┼─────────────────┼─────────────────┤
│ 结构         │ 只有Encoder     │ 只有Decoder      │ Enc+Dec         │
│ Attention    │ 双向            │ 因果(单向)      │ Enc双向,Dec因果 │
│ 训练目标     │ MLM(完形填空)  │ Next Token(续写)│ Span Corruption │
│ 适合任务     │ 理解(分类/NER)│ 生成(对话/代码)│ Seq2Seq(翻译)  │
│ 代表模型     │ BERT/RoBERTa   │ GPT/Llama/Qwen   │ T5/BART/Whisper │
└──────────────┴────────────────┴─────────────────┴─────────────────┘
```

**BERT**: 双向 Attention,MLM 训练(随机 mask 15% token 预测)。理解能力强,适合分类/NER/检索。但不能生成,做 Agent 必须用 Decoder。**Agent 中的应用**: RAG 的 embedding 模型(BGE/E5)常基于 Encoder。

**GPT**: 因果 Attention,预测下一个 token。天然支持生成,统一架构(所有任务转"续写"),Scaling Law 最好。现代 LLM 主流。

**T5**: 完整 Enc-Dec,Span Corruption 训练(还原被替换的 span)。适合 Seq2Seq,但参数效率不如 Decoder-only,2024 年后新 LLM 很少用。

#### 为什么 GPT 选 Decoder-only?

1. **生成能力**: LLM 核心是生成(对话/代码/推理),Decoder-only 天然支持
2. **统一性**: 所有任务用"续写"完成,无需任务特定 head
3. **Scaling Law**: 实证足够规模下 Decoder-only 效果最好(GPT-3 论证)
4. **训练效率**: 每 token 都是监督信号(MLM 只 15%),数据效率高
5. **推理友好**: 自回归 + KV-Cache,serving 容易优化

#### Llama 的改进

```
┌─────────────┬──────────────┬─────────────────┐
│    组件      │  GPT-2/3      │   Llama-1/2/3   │
├─────────────┼──────────────┼─────────────────┤
│ Position    │ Learned绝对   │ RoPE (旋转相对) │
│ Norm        │ LayerNorm     │ RMSNorm (更快)  │
│ 激活函数     │ GELU          │ SwiGLU (门控)   │
│ Attention   │ MHA           │ GQA (省KV-Cache)│
│ 上下文长度   │ 2k-4k         │ 8k-128k         │
│ 训练数据     │ Web/Books     │ 15T token       │
│ Post-train  │ SFT           │ SFT+RLHF+DPO    │
└─────────────┴──────────────┴─────────────────┘
```

关键改进: RoPE 支持长上下文外推;RMSNorm 去均值中心化更快;SwiGLU 门控效果更好(d_ff 调小);GQA 减少 KV-Cache 内存;更大数据更久训练(推理更便宜)。

#### 追问应对

**为什么 Decoder-only Scaling Law 更好?** 假说:①每 token 都参与预测,梯度信号充分;Encoder-Decoder 的 Encoder 部分只有 mask token 有梯度。②单一架构更易 scale。③实证多篇论文 controlled 实验中 Decoder-only zero-shot 最优。

**BERT 为什么不能做 Agent?** BERT 是 Encoder-only,无自回归生成能力,无法"说话"。Agent 需生成能力(思考/规划/工具调用),必须用 Decoder。但 BERT 在 Agent"感知"环节有用 —— RAG 的 embedding 模型。

</details>

---

### Q7: 模型推理优化有哪些技术?讲讲 KV-Cache、量化(INT8/INT4/GPTQ/AWQ)、投机解码、Flash Attention、PagedAttention。

<details>
<summary>点击查看参考答案</summary>

#### KV-Cache(键值缓存)

自回归生成时,之前 token 的 K/V 不变,可缓存复用。每步只算新 token 的 q/k/v,attention 用缓存的历史 k/v。

```
生成第 t 个 token: 只算 q_t, k_t, v_t
  attention(q_t, [k_1..k_t 缓存], [v_1..v_t 缓存])
  cache 追加 k_t, v_t
```
复杂度从 O(seq²·d) 降到 O(seq·d) 每步。

**内存占用**:
```
KV-Cache = 2(K+V) × L(层数) × n_kv_heads × seq_len × d_k × batch × dtype_bytes

例: Llama-3-70B, FP16, seq=4096, batch=1
  = 2 × 80 × 8 × 4096 × 128 × 1 × 2 ≈ 5.2 GB
seq=32768 时 ≈ 41 GB (超过模型参数本身!)
```
这就是 GQA/MQA 重要 —— 减 n_kv_heads,KV-Cache 线性下降。

#### 量化(Quantization)

把 FP16 权重压缩到 INT8/INT4,减显存加速计算。

| 方式 | 精度 | 显存减少 | 效果损失 |
|------|------|---------|---------|
| FP16 | 16bit | 基准 | 基准 |
| INT8 | 8bit | 50% | 极小(<1%) |
| INT4 | 4bit | 75% | 小(1-3%, 配GPTQ/AWQ) |

**GPTQ**: 基于二阶信息(Hessian)的逐层量化,量化时用 Hessian 补偿其他权重影响。适合 INT4,需校准数据。
**AWQ**: 激活值大的通道对应权重更敏感,对重要通道保持高精度其他量化 INT4。效果比 GPTQ 略好,推理更快。
**GGUF**: 面向 CPU/边缘设备,支持 2-8 bit,适合 Mac/笔记本。

**对 Agent 影响**: INT4 对话/RAG/工具调用通常 OK;精确数学/代码可能更敏感,建议 INT8 或 FP16。

#### 投机解码(Speculative Decoding)

小模型先"草拟" k 个 token,大模型一次 forward 并行验证。

```
1. Draft 模型(1B)生成 [t1..tk]
2. Target 模型(70B)并行验证,比较 P_target 和 P_draft
3. 找第一个不接受的 token,丢弃之后的
4. 从 Target 分布重新采样替代
```

**接受规则**(rejection sampling): `r < min(1, P_target(t_i)/P_draft(t_i))` 则接受。

**效果**: 接受率 50-70% 时加速 2-3 倍;**数学上无损**(输出分布与纯 Target 相同)。
**变体**: Medusa(多头预测,无需 Draft 模型)/EAGLE(hidden state 层面投机,接受率更高)。

#### Flash Attention

**瓶颈不是计算,是内存读写(HBM 带宽)**。标准 Attention 要把 seq² 大小的中间矩阵 S/P 反复读写 HBM。

**核心**: Tiling(分块,在 SRAM 完成计算)+ Online Softmax(不需完整 S 矩阵就能算 softmax,用 running max/sum)+ 反向重算(不存中间矩阵)。

**效果**: HBM 读写从 O(seq²) 降到 O(seq²·d/M);2-4 倍加速;显存大幅下降。是长上下文(4k→128k)的基础。

#### PagedAttention(vLLM)

**动机**: KV-Cache 内存管理。传统预分配连续内存浪费(实际生成长度未知)+ 碎片化。

**方法**(借鉴 OS 虚拟内存): KV-Cache 分成固定大小"页"(如 16 token),每个请求通过"页表"映射到不连续物理页。

**效果**: 内存利用率 40%→96%;batch size 更大 → 吞吐 2-4 倍;支持 Continuous Batching(请求完成立即返回,空位填新请求,无队头阻塞)。vLLM 吞吐比 HF transformers 高 10-20 倍。

#### 技术栈全景

```
├── 算子层: Flash Attention / Flash Decoding / Fused Kernel
├── 内存层: KV-Cache / PagedAttention / GQA / 量化
├── 调度层: Continuous Batching / Chunked Prefill / 模型并行(TP/PP)
├── 算法层: 投机解码 / Medusa / EAGLE
└── 系统层: DistServe(prefill/decode分离) / Prefix Cache / Model Router
```

#### 追问应对

**70B 部署在单张 80G A100 可行吗?** INT4 量化后参数约 35GB + KV-Cache(seq=4k 约 5GB),理论可行但很紧。实际通常 2 张 A100 做 TP=2,或 4 张 TP=4 更安全。

**量化损失多少?** INT8 几乎无损(<1%)。INT4 配 GPTQ/AWQ 常见 benchmark 损失 1-3%。复杂推理(数学/代码)可能掉 5%+;长上下文误差累积;多轮对话噪声放大。

</details>

---

### Q8: Fine-tuning 技术有哪些?全量微调、LoRA、QLoRA、Prefix Tuning、P-Tuning。LoRA 原理和优势?参数量怎么算?

<details>
<summary>点击查看参考答案</summary>

#### 为什么需要 Fine-tuning 技术?

预训练模型通用,直接用可能不懂业务领域/格式不符/风格不匹配。但全量微调大模型成本太高(70B 需数百 GB 显存),所以有参数高效微调(PEFT)。

#### 全量微调(Full Fine-Tuning)

更新所有参数。训练显存约 `16 × N bytes`(混合精度:参数2N + 梯度2N + 优化器8N + 激活值)。
- 7B → ~112GB(至少 2×80G GPU)
- 70B → ~1120GB(8 卡以上)
- 优点:效果最好;缺点:显存巨大、易灾难性遗忘、每任务存完整模型

#### LoRA(Low-Rank Adaptation)

**核心**: 不更新原始权重,学习低秩增量加到原始权重上。

```
原始 W (d_out × d_in),全量要更新整个 W
LoRA 假设 ΔW 低秩,分解:
  ΔW = B · A
  A: (r × d_in)  降维,初始化随机高斯
  B: (d_out × r) 升维,初始化为零
  r: 秩,通常 4~64

前向: h = W·x + B·A·x = (W + B·A)·x
```

**B 初始化为零**: 训练开始 ΔW=0,模型行为与原始一致,不破坏预训练知识。

**参数量**:
```
全量: d_out × d_in
LoRA: r × (d_in + d_out)
压缩比: r×(d_in+d_out) / (d_out×d_in)

例: d_in=d_out=4096, r=8
  全量: 16.7M
  LoRA: 65K
  压缩: 0.4% (只训 0.4% 参数!)
```

通常对 Attention 的 Q/K/V/O 投影加 LoRA,也可对 FFN 加。

**优势**:
1. 显存省(只存 LoRA 参数的梯度/优化器)
2. **无推理开销**(训练后 B·A 可合并到 W)
3. 避免遗忘(原始权重不变)
4. 多任务友好(每任务一个 LoRA,几十 MB,切换即可)

**超参数**: r(秩,4-64,通常 8-16 够);alpha(缩放,实际增量 = alpha/r × B·A,通常 alpha=2r)。

#### QLoRA(Quantized LoRA)

原始权重 4-bit(NF4)存储,LoRA 参数 FP16 训练。
```
7B 模型:
  全量: ~112GB
  LoRA: ~16GB
  QLoRA: ~6GB  → 单张消费级 GPU(3090/4090 24GB)可微调 7B!
```
效果接近全量微调(<1% 差距)。NF4 是专为正态分布权重设计的 4-bit 格式。

#### Prefix Tuning / P-Tuning v2

在每层 Attention 前加可学习 "virtual prefix" tokens,只训练 prefix。
- 参数量 ~0.1%,效果略逊 LoRA
- 推理需拼接 prefix,有开销
- 2024 年已较少使用(易用性和效果不如 LoRA)

#### 对比表

| 方法 | 训练参数 | 显存(7B) | 效果 | 推理开销 |
|------|---------|----------|------|---------|
| 全量 | 100% | ~112GB | 最好 | 无 |
| LoRA | 0.1-1% | ~16GB | 接近全量 | 无(可合并) |
| QLoRA | 0.1-1% | ~6GB | 接近全量 | 无(可合并) |
| Prefix | ~0.1% | ~14GB | 略逊 | 有 |

**2024 主流**: LoRA / QLoRA。

#### 追问应对

**LoRA 秩 r 怎么选?** 经验 8-16 适合多数任务。简单(风格调整)r=4 够;复杂(注入新知识)可能 r=32-64。r 越大不一定越好(可能过拟合)。建议从 r=8 开始。

**LoRA 能注入新知识吗?** 有限度。低秩假设意味着擅长"调整已有能力"(格式/风格),不擅长"学习全新知识"。注入大量知识建议:增大 r + 对 FFN 也加 LoRA,或用 Continued Pre-training(全量微调一小段)。

**QLoRA 为何不反向传播到 4-bit 权重?** 4-bit 权重冻结(requires_grad=False),只作前向计算一部分。梯度只流经 LoRA 参数。类似 "frozen backbone + trainable head"。

</details>

---

### Q9: 手撕代码 —— 用 NumPy 实现 Scaled Dot-Product Attention 和 Multi-Head Attention。含完整代码和数值验证。

<details>
<summary>点击查看参考答案</summary>

#### Scaled Dot-Product Attention

```python
import numpy as np


def softmax(x, axis=-1):
    """数值稳定的 Softmax,减去最大值防止 exp 溢出"""
    x_max = np.max(x, axis=axis, keepdims=True)
    exp_x = np.exp(x - x_max)
    return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q: (seq_q, d_k), K: (seq_k, d_k), V: (seq_v, d_v)
    mask: (seq_q, seq_k) 可选, 0 表示屏蔽
    返回: output (seq_q, d_v), weights (seq_q, seq_k)
    """
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)          # 缩放点积
    if mask is not None:
        scores = np.where(mask == 0, -1e9, scores)
    weights = softmax(scores, axis=-1)        # 归一化
    output = weights @ V                      # 加权求和
    return output, weights


# === 测试 1: 复现 Q2 手算示例 ===
print("测试 1: Scaled Dot-Product Attention")
X = np.array([[1.0, 0.0], [0.0, 1.0]])
W_Q = np.array([[1.0, 0.0], [0.0, 1.0]])
W_K = np.array([[1.0, 0.0], [0.0, 1.0]])
W_V = np.array([[1.0, 2.0], [3.0, 4.0]])

Q, K, V = X @ W_Q, X @ W_K, X @ W_V
output, weights = scaled_dot_product_attention(Q, K, V)

print("weights =\n", np.round(weights, 4))
print("output  =\n", np.round(output, 4))
assert np.allclose(weights, [[0.670, 0.330], [0.330, 0.670]], atol=0.01)
assert np.allclose(output, [[1.660, 2.660], [2.340, 3.340]], atol=0.01)
print("✓ 与 Q2 手算结果一致!")

# === 测试 2: Causal Mask ===
print("\n测试 2: Causal Mask")
np.random.seed(42)
Q_t, K_t, V_t = np.random.randn(4,8), np.random.randn(4,8), np.random.randn(4,8)
causal_mask = np.tril(np.ones((4, 4)))  # 下三角为 1
out_m, w_m = scaled_dot_product_attention(Q_t, K_t, V_t, mask=causal_mask)
print("带 mask 的 weights =\n", np.round(w_m, 4))
assert np.allclose(w_m[np.triu_indices(4, k=1)], 0, atol=1e-6)  # 上三角为 0
assert np.allclose(w_m.sum(axis=-1), 1.0)                       # 行和为 1
print("✓ 上三角为 0, 行和为 1!")
```

#### Multi-Head Attention

```python
def multi_head_attention(X, W_Q, W_K, W_V, W_O, num_heads, mask=None):
    """
    X: (seq, d_model), W_Q/K/V/O: (d_model, d_model)
    返回: output (seq, d_model), all_weights list
    """
    seq_len, d_model = X.shape
    d_k = d_model // num_heads

    Q = X @ W_Q
    K = X @ W_K
    V = X @ W_V

    # reshape: (seq, d_model) → (seq, heads, d_k) → (heads, seq, d_k)
    Q_h = Q.reshape(seq_len, num_heads, d_k).transpose(1, 0, 2)
    K_h = K.reshape(seq_len, num_heads, d_k).transpose(1, 0, 2)
    V_h = V.reshape(seq_len, num_heads, d_k).transpose(1, 0, 2)

    head_outputs = []
    all_weights = []
    for i in range(num_heads):
        out_i, w_i = scaled_dot_product_attention(
            Q_h[i], K_h[i], V_h[i], mask=mask
        )
        head_outputs.append(out_i)
        all_weights.append(w_i)

    # 拼接: (heads, seq, d_k) → (seq, heads, d_k) → (seq, d_model)
    concat = np.stack(head_outputs, axis=0).transpose(1, 0, 2)
    concat = concat.reshape(seq_len, d_model)
    output = concat @ W_O
    return output, all_weights


# === 测试 3: Multi-Head (4头, d_model=8) ===
print("\n测试 3: Multi-Head Attention")
np.random.seed(123)
seq_len, d_model, num_heads = 5, 8, 4
X_m = np.random.randn(seq_len, d_model)
WQ = np.random.randn(d_model, d_model) * 0.5
WK = np.random.randn(d_model, d_model) * 0.5
WV = np.random.randn(d_model, d_model) * 0.5
WO = np.random.randn(d_model, d_model) * 0.5

out_mha, w_mha = multi_head_attention(X_m, WQ, WK, WV, WO, num_heads)
print(f"输出 shape: {out_mha.shape} (期望 {(seq_len, d_model)})")
assert out_mha.shape == (seq_len, d_model)
assert len(w_mha) == num_heads
for w in w_mha:
    assert np.allclose(w.sum(axis=-1), 1.0)  # 每头行和为 1
print("✓ shape 正确, 所有头权重行和为 1!")

# 参数量验证
param_count = WQ.size + WK.size + WV.size + WO.size
assert param_count == 4 * d_model * d_model
print(f"✓ 参数量 = {param_count} = 4 × d_model²")

# === 测试 4: 单头 MHA 等价于 SDPA ===
print("\n测试 4: 单头 MHA 等价于 SDPA")
d_s = 4
X_s = np.random.randn(3, d_s)
WQ_s = np.random.randn(d_s, d_s)
WK_s = np.random.randn(d_s, d_s)
WV_s = np.random.randn(d_s, d_s)
WO_s = np.eye(d_s)  # 单位矩阵简化验证

out_mha1, _ = multi_head_attention(X_s, WQ_s, WK_s, WV_s, WO_s, num_heads=1)
out_sdpa, _ = scaled_dot_product_attention(
    X_s @ WQ_s, X_s @ WK_s, X_s @ WV_s
)
assert np.allclose(out_mha1, out_sdpa, atol=1e-6)
print("✓ 单头 MHA 等价于直接 SDPA!")
```

#### 验证逻辑总结

1. SDPA 输出与 Q2 手算一致(数值正确性)
2. Causal mask 后上三角权重为 0(掩码正确性)
3. 每行权重和为 1(Softmax 正确性)
4. MHA 输出 shape 正确,每头权重行和为 1
5. 参数量 = 4 × d_model²
6. 单头 MHA 等价于 SDPA(实现一致性)

#### 追问应对

**softmax 为什么减最大值?** 数值稳定。scores 很大时 exp(1000) 溢出 inf。减最大值后最大 exp(0)=1,其他在 (0,1),不溢出。数学上 softmax(x) == softmax(x-max(x)) 不变。

**怎么支持 batch?** 加 batch 维度,Q/K/V 变 (batch, heads, seq, d_k),用 np.matmul 支持 batch 广播,mask 扩展到 (batch, 1, seq, seq)。

**PyTorch 里怎么实现?** 核心一样,但:用 F.scaled_dot_product_attention(Flash Attention 后端);支持自动微分;CUDA kernel 融合算子;支持 TP(多卡切分头)。

</details>

---

### Q10: 系统设计题 —— 从零训练一个垂直领域 Agent 的 LLM(如法律/医疗/代码),完整方案设计。

<details>
<summary>点击查看参考答案</summary>

#### 需求分析

**场景**: 训练"法律 Agent LLM"用于法律咨询/文书起草/法条检索/案例分析。

**关键约束**: 准确性极高(幻觉=法律事故);需引用法条(可追溯);时效性(新法规要更新);合规(必须加免责声明)。

**选型**: 基于 Llama-3-8B 做 Continued Pre-training + SFT + DPO(性价比高,推荐)。

#### 整体方案

```
Phase 1: 数据准备 (4周)
  ├── 法律语料收集 (法规/裁判文书/问答/教材/文书模板)
  ├── 清洗去重脱敏
  ├── 配比设计 (法律60% + 通用40% 防遗忘)
  └── 评估集 (1000题法律MMLU + 200题golden + 50题安全)

Phase 2: Continued Pre-training (2周)
  ├── Llama-3-8B-Base 继续自回归训练
  ├── 600M token (法律+通用混合)
  └── 学习率 1e-5, 防遗忘

Phase 3: SFT (2周)
  ├── 50000条指令对 (人工标注2000 + GPT-4生成20000 + 脱敏真实问题)
  ├── Agent 格式对齐 (Thought/Action/Observation)
  └── 全量SFT 或 LoRA(r=32)

Phase 4: 偏好对齐 (2周)
  ├── 10000对偏好数据 (律师排序: 准确>完整>简洁>风格)
  └── DPO (β=0.1)

Phase 5: 评估 (1周)
  ├── 自动评估 (法律MMLU>75%/法条引用>90%/通用不掉3%)
  ├── 人工评估 (50题律师盲评)
  └── 红队测试 (诱导违规/编造法条/越狱)

Phase 6: 部署迭代 (持续)
  ├── INT4量化 + vLLM部署 (2×A100)
  ├── RAG + Agent框架集成
  ├── Bad case回流 + 月度迭代
  └── 法规更新: 更新RAG库 + 增量SFT
```

#### Phase 1: 数据准备

| 数据类型 | 来源 | 规模 | 用途 |
|---------|------|------|------|
| 法律法规 | 国家法律法规数据库 | ~50M token | CPT |
| 裁判文书 | 中国裁判文书网 | ~500M token | CPT+SFT |
| 法律问答 | 法律咨询平台/12348 | ~20M token | SFT |
| 法律教材 | 法学院教材/法考资料 | ~30M token | CPT |
| 通用语料 | RedPajama 开源 | ~500M token | 防遗忘 |

清洗: MinHash去重(裁判文书大量重复)/classifier质量过滤/当事人脱敏。配比: 法律60% + 通用40%。

#### Phase 2: Continued Pre-training

```
模型: Llama-3-8B-Base (FP16)
数据: 600M token
学习率: 1e-5 (比从零训小1-2数量级)
Batch: 256 (有效, 梯度累积)
Seq: 4096, Epoch: 2-3
硬件: 8 × A100 80G (DeepSpeed ZeRO-3), ~7天
```
防遗忘: 混入通用数据40%/学习率小/定期验证通用benchmark。

#### Phase 3: SFT

指令数据格式:
```
格式1 问答: {"instruction":"公司拖欠工资怎么维权?", "output":"根据《劳动合同法》第85条...\n免责声明:仅供参考"}
格式2 文书: {"instruction":"起草民间借贷起诉状", "output":"民事起诉状\n原告...被告...诉讼请求..."}
格式3 Agent: {"instruction":"查询劳动合同法第85条", "output":"Thought:需检索法条\nAction:search_law_db[...]\nObservation:..."}
```
来源: 律师标注2000条(种子) + GPT-4生成审核20000条 + 脱敏真实问题。总量50000条。
训练: 全量SFT(lr=2e-5)或LoRA(r=32, lr=1e-4),3 epoch,loss只在output部分计算。

#### Phase 4: 偏好对齐(DPO)

收集: 对每prompt用SFT模型生成2-4个回答,3-5名律师排序(准确性>完整性>简洁性>风格),10000对。
DPO训练: 参考模型=SFT(冻结),β=0.1,lr=5e-7,1 epoch。
关键: 法律错误=严重负面;引用错误法条=负面;缺免责声明=轻微负面。

#### Phase 5: 评估

| 评估集 | 指标 | 目标 |
|--------|------|------|
| 法律MMLU(1000题) | 准确率 | >75% |
| 法条引用准确率 | 引用正确率 | >90% |
| 通用C-Eval | 准确率 | 不低于Base 3% |
| 安全测试 | 违规率 | <1% |
| 人工盲评 | 律师1-5分 | 优于通用Llama-3 |

红队: 诱导给"确定法律建议"/编造法条/泄露隐私/越狱(扮演律师绕过限制)。

#### Phase 6: 部署

```
用户输入 → 前置过滤(敏感词/合规)
         → Agent编排(LangGraph): 意图识别 → RAG检索 → 工具调用 → 回答生成
         → 法律LLM(vLLM, INT4量化, 2×A100, KV-Cache+PagedAttention)
         → 后置审核(免责声明/引用校验/日志)
```

RAG补充: 即使训了模型也"记不准"法条,用RAG检索最新法条让模型基于检索回答,法条更新时无需重训模型。

#### 成本估算

| 阶段 | 资源 | 成本 |
|------|------|------|
| 数据准备 | 标注团队4周 | 10万 |
| CPT | 8×A100 1周 | 5万 |
| SFT+DPO | 8×A100 5天 | 3万 |
| 评估 | 律师1周 | 3万 |
| 部署 | 2×A100 持续 | 1万/月 |
| **总计** | | **~20万 + 1万/月** |

#### 追问应对

**为什么不直接用 GPT-4 + RAG?** ①成本:量大时自训更便宜;②隐私:法律数据敏感不能发第三方;③定制化:Agent格式/免责/引用风格通用模型难保证。但早期验证可先用GPT-4+RAG跑通,有量了再自训。

**怎么解决幻觉?** 多层防御:①训练用高质量数据,偏好对齐惩罚编造法条;②推理用RAG检索真实法条;③后处理校验引用法条是否真实存在;④产品强制免责声明+来源引用;⑤bad case回流迭代。单靠模型无法根除,必须训练+RAG+后处理+产品配合。

**法律更新了怎么办?** 不需重训全量:①短期更新RAG法条库;②中期收集新法条问答做增量SFT;③长期积累足够新数据后做一轮CPT。

</details>

---

## 核心知识回顾表

| 主题 | 核心要点 | 关键公式/概念 | 频率 |
|------|---------|--------------|------|
| Transformer | Enc-Dec/Self-Attention/FFN/残差/LN | `Attention(Q,K,V)=softmax(QK^T/√d_k)V` | ★★★★★ |
| Self-Attention | Q/K/V,缩放点积,Softmax | 缩放因子√d_k防饱和 | ★★★★★ |
| Multi-Head | 多子空间并行,拼接投影 | 参数量=4×d_model²(与头数无关) | ★★★★ |
| Position Encoding | 正余弦/RoPE/ALiBi | RoPE旋转使结果只依赖相对位置 | ★★★★ |
| Pre-training | 自回归,万亿token | `Loss=-Σlog P(x_t\|x_{<t})` | ★★★★ |
| SFT | 指令对,loss masking | 只在output部分计算loss | ★★★★ |
| RLHF | RM+PPO+KL惩罚 | `L=-E[r]+β·KL(π‖π_SFT)` | ★★★★ |
| DPO | 无需RM,偏好直接优化 | `L=-log σ(β·(logπ(y_w)/π_SFT - logπ(y_l)/π_SFT))` | ★★★ |
| 架构对比 | GPT/BERT/T5/Llama | Decoder-only成主流 | ★★★★ |
| KV-Cache | 缓存历史K/V | `2·L·n_kv·seq·d_k·batch·dtype` | ★★★★★ |
| 量化 | INT8/INT4,GPTQ/AWQ | 70B INT4≈35GB,损失1-3% | ★★★★ |
| 投机解码 | 小模型draft+大模型verify | 无损2-3x加速 | ★★★ |
| Flash Attention | Tiling+Online Softmax | HBM读写O(n²)→O(n²d/M) | ★★★ |
| PagedAttention | 分页KV-Cache,vLLM | 吞吐10-20x | ★★★★ |
| LoRA | 低秩分解ΔW=B·A | 参数r·(d_in+d_out),约0.1% | ★★★★★ |
| QLoRA | 4-bit权重+LoRA | 7B微调只需~6GB | ★★★★ |
| GQA | Q多头,K/V分组共享 | KV-Cache省group_size倍 | ★★★ |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────────┐
│                  LLM 面试速记卡 (Day 34)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ★ Attention 核心公式                                           │
│    Attention(Q,K,V) = Softmax(Q·K^T / √d_k) · V                │
│    FFN(x) = Swish(x·W1)⊙(x·W_gate)·W2  (SwiGLU)               │
│    残差: out = x + Sublayer(LN(x))  (Pre-LN)                   │
│                                                                 │
│  ★ 为什么除以 √d_k?                                             │
│    点积方差=d_k,标准差=√d_k。不缩放→Softmax饱和→梯度0          │
│    除以√d_k→方差归一化到1→Softmax平滑→梯度健康                 │
│                                                                 │
│  ★ Multi-Head 参数量                                            │
│    = 4 × d_model² (与头数 h 无关!)                              │
│    h×d_k = d_model, 分组不改变总参数                            │
│                                                                 │
│  ★ 位置编码                                                     │
│    Sinusoidal: 绝对, 固定正余弦                                 │
│    RoPE: 相对, 旋转Q/K (Llama用, 可外推)                       │
│    ALiBi: 无位置编码, attention加线性bias                       │
│                                                                 │
│  ★ 训练流程                                                     │
│    Pre-training → SFT → RLHF/DPO                                │
│    RLHF: RM + PPO + KL(π‖π_SFT)                                │
│    DPO: L=-log σ(β·(logπ(y_w)/π_SFT - logπ(y_l)/π_SFT))       │
│                                                                 │
│  ★ KV-Cache 内存                                                │
│    = 2·L·n_kv_heads·seq·d_k·batch·dtype                        │
│    Llama-3-70B seq=4k: ~5.2GB; seq=32k: ~41GB                  │
│    → GQA减n_kv_heads是关键                                      │
│                                                                 │
│  ★ LoRA                                                         │
│    ΔW = B·A, B初始化为零(不破坏预训练)                         │
│    参数 = r·(d_in+d_out), 约0.1%全量                            │
│    推理可合并: W_new = W + α/r·B·A (无额外开销)                │
│    QLoRA: 权重4-bit(NF4)+LoRA FP16, 7B只需6GB                 │
│                                                                 │
│  ★ 推理优化                                                     │
│    Flash Attention: Tiling+Online Softmax, 减HBM读写            │
│    PagedAttention: 分页KV-Cache, vLLM吞吐10-20x               │
│    投机解码: 小模型draft+大模型verify, 无损2-3x                │
│    量化: INT8无损, INT4损失1-3%(GPTQ/AWQ)                     │
│                                                                 │
│  ★ 架构选型                                                     │
│    GPT(Decoder-only): 生成主流, Scaling Law好                 │
│    BERT(Encoder-only): 理解/嵌入, 不能生成                     │
│    Llama: RoPE+RMSNorm+SwiGLU+GQA, 现代标配                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

1. **"Attention 复杂度是 O(n·d)"** —— 错,是 **O(n²·d)**(Q·K^T 是 n×d 乘 d×n)。空间也 O(n²)(权重矩阵)。这是长上下文核心瓶颈。

2. **"多头参数量随头数增加"** —— 错,总参数量 = **4×d_model²,与头数无关**。h×d_k=d_model,分组不改变总数。

3. **"除以 √d_k 是为了归一化到 [0,1]"** —— 错,是**控制方差**(标准差从 √d_k 变 1)防止 Softmax 饱和。归一化到概率是 Softmax 干的事。

4. **"RoPE 是绝对位置编码"** —— 错,RoPE 是**相对位置编码**。Q·K^T 结果只依赖 (m-n) 相对距离,这是外推能力好的根本。

5. **"RLHF 和 SFT 一回事"** —— 错。SFT 用"标准答案"做监督学习;RLHF 用"偏好排序"做强化学习。SFT 学"怎么回答",RLHF 学"什么是好回答"。

6. **"DPO 不需要偏好数据"** —— 错。DPO 仍需偏好对(chosen, rejected),只是不需单独训 RM 和用 PPO,数据需求不变。

7. **"LoRA 增加推理延迟"** —— 错。训练后 B·A 可合并到 W(`W_new = W + α/r·B·A`),合并后推理和全量微调完全一样,无额外开销。

8. **"量化一定大幅降低效果"** —— 错。INT8 几乎无损(<1%),INT4 配 GPTQ/AWQ 只损失 1-3%。多数 Agent 场景量化模型完全可用。

9. **"BERT 能做 Agent 的 LLM"** —— 错。BERT 是 Encoder-only 无自回归生成能力,无法"说话"。Agent 需生成必须用 Decoder。但 BERT 可做 RAG 的 embedding 模型。

10. **"Pre-training 和 SFT 数据一样多"** —— 错。Pre-training 万亿 token,SFT 万~百万条,差 4-5 数量级。Pre-training 教"语言",SFT 教"指令"。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 我能画出 Transformer 完整架构图(Enc/Dec/Attention/FFN/LN/残差)
- [ ] 我能手算简单 Self-Attention(2×2 矩阵,含 Q/K/V/scores/softmax/output)
- [ ] 我能解释为什么除以 √d_k(方差控制,防止 Softmax 饱和)
- [ ] 我能说清 Multi-Head 计算过程和参数量(4×d_model²,与头数无关)
- [ ] 我能对比 Sinusoidal/RoPE/ALiBi 原理和优劣
- [ ] 我能完整描述 Pre-training → SFT → RLHF/DPO 流程和各阶段目标
- [ ] 我能解释 RLHF 和 DPO 区别(RLHF 需 RM+PPO,DPO 直接用偏好对)
- [ ] 我能算出 KV-Cache 内存(公式 + Llama-3-70B 具体数值)
- [ ] 我能说清 LoRA 原理(ΔW=B·A 低秩)和参数量(r×(d_in+d_out))
- [ ] 我能解释为什么 GPT 选 Decoder-only(生成/统一/Scaling Law/效率)

### 代码题(3 个)

- [ ] 我能用 NumPy 实现 Scaled Dot-Product Attention(含 softmax 数值稳定)
- [ ] 我能用 NumPy 实现 Multi-Head Attention(含 reshape/transpose/拼接)
- [ ] 我的代码含数值验证(与手算对比,shape 检查,权重行和为 1)

### 系统设计题(2 个)

- [ ] 我能设计垂直领域 LLM 完整训练方案(数据/CPT/SFT/DPO/评估/部署)
- [ ] 我能说清什么场景用 RAG、什么场景用 Fine-tuning、什么场景两者结合

---

## 延伸阅读

### 经典论文(按重要性排序)

1. **Attention is All You Need** (Vaswani et al., 2017) —— Transformer 原始论文,必读。重点:第 3 节 Model Architecture。
2. **GPT-3: Language Models are Few-Shot Learners** (Brown et al., 2020) —— In-context learning,Scaling Law 和 few-shot 实验。
3. **Llama 3 Technical Report** (Meta, 2024) —— 开源 SOTA 训练细节,15T token 预训练 + RLHF+DPO 后训练。
4. **LoRA: Low-Rank Adaptation** (Hu et al., 2021) —— 参数高效微调,低秩分解数学推导。
5. **QLoRA** (Dettmers et al., 2023) —— 4-bit 量化+LoRA,单卡微调 65B,NF4 量化格式。
6. **InstructGPT** (Ouyang et al., 2022) —— RLHF 三步 pipeline 实践,RM 训练和 PPO。
7. **DPO** (Rafailov et al., 2023) —— 无需 RM 的偏好对齐,从 RLHF 最优解推导 DPO loss。
8. **FlashAttention** (Dao et al., 2022) —— IO-aware Attention,Tiling 和 online softmax。
9. **RoFormer** (Su et al., 2021) —— RoPE 旋转位置编码,旋转矩阵数学推导。
10. **GPT-4 Technical Report** (OpenAI, 2023) —— 闭源模型细节,RLHF+规模,多模态。

### 综述/博客

- **The Illustrated Transformer** (Jay Alammar) —— 图解 Transformer,入门首选
- **The Annotated Transformer** (Harvard NLP) —— 带代码注释的 Transformer 实现
- **Lil'Log: LLM Training** (Lilian Weng) —— 训练流程综述
- **HuggingFace PEFT 文档** —— LoRA/QLoRA 实践指南
- **vLLM Blog: PagedAttention** —— PagedAttention 原理

---

## 34 天计划毕业总结

恭喜完成 34 天 AI Agent 面试冲刺!回顾整个旅程。

### 34 天知识体系总览

```
AI Agent 面试 34 天冲刺
│
├── Week 1: Agent 基础 (Day 1-7)
│   概念定义 / 核心架构 / ReAct / Plan-Execute / Memory / Tool Use / Multi-Agent
│
├── Week 2: RAG 与 Agent (Day 8-14)
│   RAG 基础 / Chunk 策略 / Embedding / 混合检索 / 进阶RAG / 评估 / GraphRAG
│
├── Week 3: 框架与系统设计 (Day 15-21)
│   LangChain / LlamaIndex / LangGraph / 单Agent / Multi-Agent / 可观测 / 部署
│
├── Week 4: 大厂真题 (Day 22-28)
│   字节 / 阿里 / 腾讯 / 百度美团 / 华为 / OpenAI风格 / 创业公司
│
└── Week 5: 模拟面试与项目 (Day 29-34)
    项目深挖 / 简历策略 / 实战经验 / 前端基础 / 后端基础 / LLM底层 ← 今天

跨周串联:
  模型层(Day34) → 检索层(Day8-14) → 编排层(Day1-7,15-17) 
    → 系统层(Day18-21) → 工程层(Day29-33) → 面试通过
```

### 各 Week 与 Day 34 的串联

- **Week 1 → Day 34**: Week 1 学"Agent 怎么决策(ReAct)",Day 34 补"决策能力从哪来(LLM 训练)"。ReAct 的 Thought 能遵循格式因 SFT,能推理因 Pre-training。
- **Week 2 (RAG) → Day 34**: Day 34 补"Embedding 模型怎么来的(BERT 类)、为什么 RAG 减少幻觉"。懂模型才能选对 embedding。
- **Week 3 (框架/系统) → Day 34**: Day 34 补"怎么优化推理(KV-Cache/量化/vLLM)"。Agent 延迟成本主要来自 LLM 推理。
- **Week 4 (大厂真题) → Day 34**: 大厂追问很多指向模型底层,Day 34 系统化这些追问。区分度就在于"懂不懂模型"。

### 下一步学习建议

- **想做算法/训模型**: 跑 NanoGPT;用 LoRA 微调 Llama-3-8B;读 Llama-3/Qwen-2.5 技术报告
- **想做应用/平台**: 用 LangGraph 搭真实 Multi-Agent;研究 AutoGen/CrewAI/Swarm;关注 Agent 评估
- **想做 Infra**: 读 vLLM 源码;学 TensorRT-LLM/SGLang;研究分布式推理和 Disaggregated Serving
- **前沿关注**: 推理模型(o1/DeepSeek-R1)、长上下文(Ring Attention)、多模态 Agent、Agent 专用模型

### 面试准备最后建议

- 把 34 天笔记浓缩成 3-5 页"面试 cheatsheet"
- 准备 2-3 个项目故事(STAR 法则),5 分钟内讲清
- 做至少 3 次模拟面试,录音复盘
- 面试前一晚不熬夜,速记卡过一遍就好

---

> **毕业寄语**: 34 天前你可能只知道"Agent 就是调 API";今天你已掌握从 Transformer 架构到 Agent 系统设计的完整知识体系。面试不是终点而是起点,真正成长发生在把知识用进真实项目、踩坑、复盘、再迭代的过程。祝面试顺利,Agent 之路越走越宽。
>
> **"The best way to learn AI is to build AI. The best way to master Agent is to ship Agent."**

---

*Day 34 完成。34 天计划,毕业。*
