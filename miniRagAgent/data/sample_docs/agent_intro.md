# Agent 基础概念

## 什么是 AI Agent?

AI Agent 是一个能够感知环境、自主决策并执行行动来完成目标的智能系统。

Agent 的核心公式:Agent = LLM(大脑) + Planning(规划) + Memory(记忆) + Tools(工具)。

与普通聊天机器人不同,Agent 不仅能对话,还能主动调用工具、检索信息、执行代码,形成"感知-决策-行动"的闭环。

## ReAct 框架

ReAct 是 Reasoning + Acting 的缩写,是 Agent 最经典的推理范式。

ReAct 的核心循环:Thought(思考) → Action(行动) → Observation(观察) → Thought → ... → Finish。

每一步 Agent 先思考"我该做什么",然后选择一个工具执行,观察结果后再决定下一步。这种推理与行动交替的模式让 Agent 能动态适应复杂任务。

## Function Calling

Function Calling 是 LLM 调用外部工具的机制。LLM 根据用户意图,输出结构化的 JSON(函数名+参数),由 Harness 层执行函数后,将结果作为 Observation 喂回 LLM。

LLM 本身不执行代码,只做"决策"——这是安全设计的关键。

## MCP 协议

MCP(Model Context Protocol)是 Anthropic 提出的工具协议标准,类似"AI 的 USB-C"。

MCP 解耦了工具实现与模型调用:工具开发者按 MCP 协议实现一次,任何支持 MCP 的模型都能使用。这解决了工具碎片化问题。
