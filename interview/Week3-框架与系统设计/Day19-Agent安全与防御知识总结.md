## 核心知识回顾表

| 主题 | 核心要点 | 关键词 |
|------|---------|--------|
| 六大威胁模型 | Prompt Injection / Tool Abuse / Data Exfiltration / Jailbreak / DoW / Supply Chain | 威胁建模先行 |
| Prompt Injection 原理 | LLM 无法区分指令与数据;直接注入 vs 间接注入 | SQL Injection for LLMs |
| Prompt Injection 防御 | 输入过滤 / 指令隔离 / 输出检测 / 权限分级 | 纵深防御 |
| 工具安全 | 最小权限 / 沙箱 / 参数校验 / 速率限制 | 默认拒绝 |
| 数据安全 | PII 脱敏 / 上下文隔离 / 审计日志 | 合规红线 |
| 权限设计 | 最小权限原则 / HITL / 操作分级 | 默认无权限 |
| OWASP LLM Top 10 | LLM01-LLM10,Agent 重点关注 Excessive Agency | 安全风向标 |
| 多 Agent 安全 | 零信任 / 权限不传播 / 级联攻击防御 | 通信中转层 |
| 安全防护层代码 | 5 大模块: 输入/工具/输出/速率/审计 | 可运行 |
| 企业级系统设计 | 策略引擎 / 安全网关 / 审计服务 / 合规报告 | 集中策略,分布执行 |

---

## 面试速记卡

```
┌─────────────────────────────────────────────────────────────┐
│              Agent 安全 — 30 秒速记                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  六大威胁: PI(注入) / TA(工具滥用) / DE(数据泄露)          │
│           JB(越狱) / DoW(钱包耗尽) / SC(供应链)            │
│                                                             │
│  PI 防御四层: 输入过滤 → 指令隔离 → 输出检测 → 权限分级     │
│                                                             │
│  工具安全四件套: 最小权限 / 沙箱 / 参数校验 / 速率限制      │
│                                                             │
│  权限设计: 最小权限 + HITL + 操作分级(L0-L4)               │
│                                                             │
│  OWASP Top10 Agent 优先级:                                  │
│    LLM01(PI) > LLM06(Excessive Agency) >                   │
│    LLM05(Output Handling) > LLM02(数据泄露)                │
│                                                             │
│  多 Agent: 零信任 / 权限不传播 / 通信中转层 / 级联隔离      │
│                                                             │
│  企业系统四模块:                                            │
│    策略引擎(大脑) + 安全网关(必经) +                       │
│    审计服务(底线) + 合规报告(通行证)                       │
│                                                             │
│  金句: "Prompt Injection 不是 bug,是 LLM 架构的固有特性"    │
│  金句: "能力越大,制动系统必须越强"                          │
│  金句: "默认无权限,按需授权,高危人工确认"                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 易错点提醒(10 个)

1. **"Prompt Injection 可以被彻底修复"** — 错。这是 LLM 架构的固有特性,只能降低风险,无法根除。类比 XSS 存在 20 年仍未消灭。

2. **"间接注入只影响 RAG 场景"** — 错。任何 Agent 读取外部数据的场景都受影响:网页抓取、邮件处理、工具返回值、文件读取。

3. **"指令隔离(分隔符)能防住所有注入"** — 错。攻击者可以说"忽略 `<data>` 标签"。指令隔离只是纵深防御一层,不能单独依赖。

4. **"关键词过滤足够防护注入"** — 错。同义词/编码/多语言/多步注入都能绕过。需配合分类器与语义理解。

5. **"Agent 间权限应该自动传播以提升效率"** — 错。权限传播失控是多 Agent 安全的核心风险。子 Agent 权限必须独立计算,取交集。

6. **"所有操作都要 HITL 审批才安全"** — 错。审批疲劳会导致用户习惯性点同意,HITL 形同虚设。应基于风险等级分级触发。

7. **"沙箱执行只是代码工具的事"** — 错。文件工具(路径隔离)、网络工具(域名白名单)、Shell 工具(容器隔离)都需要沙箱思维。

8. **"审计日志只是存下来就行"** — 错。日志需要:不可篡改(哈希链)、脱敏存储、完整覆盖、可检索、有保留周期、访问控制。日志本身可能是泄露源。

9. **"OWASP Top 10 顺序就是 Agent 的优先级"** — 错。Agent 场景下 Excessive Agency(LLM06)的实际危害远高于其排名,应优先处理。

10. **"安全网关宕机时默认放行以保证可用性"** — 错。安全系统应"Fail-Secure"——默认拒绝。宁可不可用,不可不安全。

---

## 自测检查清单

### 概念题(10 个)

- [ ] 1. 能否在 30 秒内说出六大威胁模型及其核心区别?
- [ ] 2. 能否区分直接注入与间接注入,并各举一个攻击示例?
- [ ] 3. Prompt Injection 的四层防御分别是什么?为何不能只靠一层?
- [ ] 4. 工具安全的"最小权限"如何落地?给一个动态权限分配的例子。
- [ ] 5. PII 脱敏为什么需要"输入侧 + 输出侧 + 持久化前"三处都做?
- [ ] 6. HITL 的三种模式(审批式/监督式/复核式)分别适合什么场景?
- [ ] 7. OWASP LLM Top 10 中,为何 Excessive Agency 对 Agent 尤其重要?
- [ ] 8. 多 Agent 场景下,级联攻击如何发生?防御核心原则是什么?
- [ ] 9. 审计日志的"哈希链"如何防止篡改?
- [ ] 10. 企业级安全系统的四个核心模块是什么?为何缺一不可?

### 代码题(3 个)

- [ ] 1. 手写一个 InputFilter,支持注入检测 + PII 脱敏,给出测试用例。
- [ ] 2. 手写一个 RateLimiter,支持滑动窗口 + 按工具分级限流。
- [ ] 3. 手写一个 ToolPermissionManager,支持角色权限 + Schema 校验 + 路径穿越检查。

### 系统设计题(2 个)

- [ ] 1. 设计企业级 Agent 安全管控系统的总体架构,说明四个核心模块的职责与交互。
- [ ] 2. 若企业有 50+ Agent、10 万用户,安全网关如何保证 < 50ms 延迟与 99.99% 可用性?

---

## 延伸阅读

### 论文
1. **"Not what you've signed up for: Compromising Real-World LLM-integrated Applications with Indirect Prompt Injection"** (Greshake et al., 2023) — 间接注入的开山之作
2. **"Prompt Injection attack against LLM-integrated Applications"** (Liu et al., 2023) — 系统性分析注入攻击
3. **"Jailbreak and Guard Aligned Language Models"** (Wei et al., 2023) — 越狱与防御
4. **"Red Teaming Language Models to Reduce Harms"** (Anthropic, 2022) — 红队测试方法

### 标准与框架
5. **OWASP LLM Top 10 (2025)** — https://owasp.org/www-project-top-10-for-large-language-model-applications/
6. **NIST AI Risk Management Framework** — https://www.nist.gov/itl/ai-risk-management-framework
7. **EU AI Act** — 欧盟 AI 法案,高风险 AI 系统需人工监督
8. **GB/T 42888-2023** — 中国 AI 安全评估国标

### 博客与文章
9. **Simon Willison's Weblog** — Prompt Injection 系列文章(https://simonwillison.net/tag/prompt-injection/)
10. **LangChain Security Best Practices** — https://python.langchain.com/docs/guides/security/
11. **OpenAI Usage Policies & Safety** — https://openai.com/policies/usage-policies/
12. **Anthropic Constitutional AI** — https://www.anthropic.com/constitutional-ai

### 工具与开源项目
13. **LlamaGuard** (Meta) — 输入输出安全分类器
14. **PromptGuard** — 注入检测模型
15. **garak** — LLM 漏洞扫描器(https://github.com/leondz/garak)
16. **Rebuff** — Prompt Injection 检测框架

### 相关书籍
17. **"AI Security"** — Hyrum Anderson et al.
18. **"Red Team AI"** — 红队测试实战

---

## 明日预告

**Day 20 — 系统设计题专项**

明天将进入系统设计题的集中训练,这是 Agent 面试的"压轴大题"。我们将覆盖:

1. **设计一个企业级 RAG 系统**(向量库选型/检索策略/重排序/更新机制)
2. **设计一个多 Agent 协作系统**(角色分工/通信协议/任务分解/冲突解决)
3. **设计一个 Agent 评测平台**(指标体系/自动化评测/人工标注/A-B 测试)
4. **设计一个 AI 编程助手**(代码上下文/工具调用/反馈学习/安全沙箱)
5. **设计一个客服 Agent 系统**(意图识别/知识库/人工转接/质量评估)

每道题按"需求澄清 → 容量估算 → 架构设计 → 数据流 → 异常处理 → 扩展性"六步法展开,目标是 30 分钟内画出完整架构图并讲清关键决策。

> **学习建议**: 今晚复习 Day 1-19 的核心知识点,明天系统设计题会综合调用前 19 天的所有知识。重点是"如何把碎片知识组织成完整方案"——这是区分"会用"和"会设计"的关键。

---

> **今日总结**: Agent 安全是大厂面试的"必考题中的必考题"。核心掌握三条线:**威胁模型(攻) → 防御策略(防) → 系统设计(建)**。代码题务必手写一遍 SecurityLayer,系统设计题务必画出四模块架构图。记住:安全不是功能,是底线——没有安全,Agent 能力越强,灾难越大。
