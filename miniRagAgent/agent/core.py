"""
Agent 模块 - ReAct Agent 核心循环

【对应学习日】Day02: ReAct 框架原理; Day06: 规划与推理范式
【核心概念】
  ReAct = Reasoning + Acting,核心循环:
    Thought(思考) → Action(行动) → Observation(观察) → Thought → ... → Finish

  这个循环是几乎所有 Agent 的基础:
    - LangChain AgentExecutor 的核心
    - LangGraph 的 StateGraph 循环
    - AutoGen 的对话循环

【ReAct 循环图解】

  用户问题 ──→ ┌─────────────────────────────────┐
               │  Step 1: LLM 决策               │
               │  Thought: 我需要先搜索...        │
               │  Action: search_knowledge        │
               │  Action Input: "什么是 Agent"    │
               └──────────┬──────────────────────┘
                          │
                          ▼
               ┌─────────────────────────────────┐
               │  Step 2: 执行工具                │
               │  Observation: Agent 是...        │
               └──────────┬──────────────────────┘
                          │
                          ▼
               ┌─────────────────────────────────┐
               │  Step 3: LLM 决策               │
               │  Thought: 信息足够了             │
               │  Action: finish                  │
               │  Action Input: 最终答案...       │
               └──────────┬──────────────────────┘
                          │
                          ▼
                    返回最终答案

【面试考点】
  Q: ReAct vs CoT 的区别?
  A: CoT 只做推理(Think step by step),不与外部交互。
     ReAct 推理+行动交替,能调用工具获取信息,形成闭环。
     ReAct 适合需要外部信息(API/检索/计算)的场景。

  Q: 如何防止 Agent 无限循环?
  A: 1. 设置 max_steps 上限; 2. 检测重复 Action; 3. 设置超时; 4. 总 token 预算限制。
"""
import re
import time
from dataclasses import dataclass, field
from typing import Generator, Optional
import config
from agent.llm import LLMBase, create_llm
from agent.tools import ToolRegistry
from agent.memory import AgentMemory


@dataclass
class AgentStep:
    """Agent 执行的一步"""
    step_num: int
    thought: str = ""           # LLM 的思考
    action: str = ""            # 选择的工具
    action_input: str = ""      # 工具参数
    observation: str = ""       # 工具返回结果
    is_final: bool = False      # 是否是最终答案
    elapsed: float = 0.0        # 本步耗时(秒)


@dataclass
class AgentResult:
    """Agent 执行结果"""
    answer: str                         # 最终答案
    steps: list[AgentStep] = field(default_factory=list)  # 执行步骤
    total_elapsed: float = 0.0          # 总耗时
    tool_calls: list[dict] = field(default_factory=list)  # 工具调用记录

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "steps": [
                {
                    "step": s.step_num,
                    "thought": s.thought,
                    "action": s.action,
                    "action_input": s.action_input,
                    "observation": s.observation[:200] + "..." if len(s.observation) > 200 else s.observation,
                    "is_final": s.is_final,
                }
                for s in self.steps
            ],
            "total_elapsed": round(self.total_elapsed, 3),
            "tool_calls": self.tool_calls,
        }


class ReActAgent:
    """
    ReAct Agent:核心循环实现

    这是整个项目最核心的文件 —— 展示了 Agent 如何"思考-行动-观察"循环。

    使用流程:
      agent = ReActAgent(llm, tools, memory)
      result = agent.run("什么是 RAG?")
      print(result.answer)
      for step in result.steps:
          print(f"Thought: {step.thought}")
          print(f"Action: {step.action}({step.action_input})")
          print(f"Observation: {step.observation}")
    """

    # ReAct Prompt 模板(对应 LangChain 的 create_react_agent)
    REACT_PROMPT_TEMPLATE = """你是一个智能助手,通过 ReAct(Reasoning + Acting)模式回答问题。

你可以使用以下工具:
{tools}

使用规则:
1. 每一步先输出 Thought(你的思考过程)
2. 然后输出 Action(选择的工具名称)和 Action Input(工具参数)
3. 等待 Observation(工具返回结果)
4. 如果信息足够,使用 Action: finish 并在 Action Input 中给出最终答案
5. 如果信息不足,继续选择工具获取信息

格式(严格遵循):
Thought: <你的思考>
Action: <工具名称>
Action Input: <工具参数>

历史对话:
{history}

Question: {question}

{previous_steps}

Thought:"""  # 注意:最后留 "Thought:" 让 LLM 续写

    def __init__(
        self,
        llm: Optional[LLMBase] = None,
        tools: Optional[ToolRegistry] = None,
        memory: Optional[AgentMemory] = None,
        max_steps: int = config.MAX_AGENT_STEPS,
    ):
        self.llm = llm or create_llm()
        self.tools = tools or ToolRegistry()
        self.memory = memory
        self.max_steps = max_steps

    def run(self, query: str) -> AgentResult:
        """
        运行 ReAct 循环(同步,返回完整结果)

        内部消费 run_stream 生成器,收集最终返回值。
        不能直接用 next() —— 生成器 return 的值在 StopIteration.value 中。

        Args:
            query: 用户问题

        Returns:
            AgentResult:包含最终答案和所有中间步骤
        """
        gen = self.run_stream(query)
        try:
            while True:
                next(gen)  # 消费所有 yield 的 step(不展示)
        except StopIteration as e:
            return e.value  # 生成器 return 的 AgentResult

    def run_stream(self, query: str) -> Generator[AgentStep, None, AgentResult]:
        """
        运行 ReAct 循环(流式,yield 每一步)

        用于 SSE 流式输出:每完成一步就 yield,前端实时展示。

        Args:
            query: 用户问题

        Yields:
            AgentStep:每一步的执行结果

        Returns:
            AgentResult:最终完整结果(通过 StopIteration.value 返回)
        """
        start_time = time.perf_counter()
        steps: list[AgentStep] = []
        tool_calls: list[dict] = []
        previous_steps_text = ""  # 累积的 Thought/Action/Observation 历史

        for step_num in range(1, self.max_steps + 1):
            step_start = time.perf_counter()

            # ---- Step 1: 构造 Prompt ----
            history = self.memory.get_context(query) if self.memory else "(无)"
            prompt = self.REACT_PROMPT_TEMPLATE.format(
                tools=self.tools.list_tools(),
                history=history,
                question=query,
                previous_steps=previous_steps_text,
            )

            # ---- Step 2: LLM 生成决策 ----
            llm_response = self.llm.generate(prompt)

            # ---- Step 3: 解析 LLM 输出 ----
            thought, action, action_input = self._parse_react_response(llm_response)

            step = AgentStep(
                step_num=step_num,
                thought=thought,
                action=action,
                action_input=action_input,
                elapsed=time.perf_counter() - step_start,
            )

            # ---- Step 4: 判断是否结束 ----
            if action.lower() == "finish":
                # 最终答案
                step.is_final = True
                step.observation = ""
                steps.append(step)
                yield step  # 流式:yield 最终步

                # 保存到记忆
                if self.memory:
                    self.memory.add("user", query)
                    self.memory.add("assistant", action_input)

                total_elapsed = time.perf_counter() - start_time
                return AgentResult(
                    answer=action_input,
                    steps=steps,
                    total_elapsed=total_elapsed,
                    tool_calls=tool_calls,
                )

            # ---- Step 5: 执行工具 ----
            observation = self._execute_tool(action, action_input)
            step.observation = observation
            steps.append(step)

            # 记录工具调用
            tool_calls.append({
                "step": step_num,
                "tool": action,
                "input": action_input,
                "output": observation[:200],
            })

            yield step  # 流式:yield 中间步

            # ---- Step 6: 累积上下文 ----
            previous_steps_text += (
                f"Thought: {thought}\n"
                f"Action: {action}\n"
                f"Action Input: {action_input}\n"
                f"Observation: {observation}\n\n"
            )

        # ---- 超过最大步数,强制终止 ----
        fallback_answer = "抱歉,我在处理这个问题时遇到了困难,超过了最大推理步数。"
        if steps:
            last_obs = steps[-1].observation
            if last_obs:
                fallback_answer = f"基于已获取的信息:\n{last_obs[:500]}"

        total_elapsed = time.perf_counter() - start_time

        if self.memory:
            self.memory.add("user", query)
            self.memory.add("assistant", fallback_answer)

        return AgentResult(
            answer=fallback_answer,
            steps=steps,
            total_elapsed=total_elapsed,
            tool_calls=tool_calls,
        )

    def _parse_react_response(self, response: str) -> tuple[str, str, str]:
        """
        解析 LLM 的 ReAct 格式响应

        期望格式:
          Thought: xxx
          Action: xxx
          Action Input: xxx

        返回: (thought, action, action_input)
        """
        thought = ""
        action = ""
        action_input = ""

        # 提取 Thought
        thought_match = re.search(r'Thought[:：]\s*(.+?)(?:\nAction[:：]|$)', response, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # 提取 Action
        action_match = re.search(r'Action[:：]\s*(.+?)(?:\nAction Input[:：]|$)', response, re.DOTALL)
        if action_match:
            action = action_match.group(1).strip()

        # 提取 Action Input
        input_match = re.search(r'Action Input[:：]\s*(.+?)(?:\n|$)', response, re.DOTALL)
        if input_match:
            action_input = input_match.group(1).strip()

        # 兜底:如果没解析到 Action,默认 finish
        if not action:
            action = "finish"
            action_input = response.strip()

        return thought, action, action_input

    def _execute_tool(self, tool_name: str, tool_input: str) -> str:
        """
        执行工具(由 Harness 层执行,不是 LLM 执行)

        对应 Day03: Function Calling —— LLM 只输出"调什么工具+参数",
        实际执行由 Harness(本代码)完成,结果作为 Observation 喂回 LLM。
        """
        tool = self.tools.get(tool_name)
        if tool is None:
            return f"错误: 未知工具 '{tool_name}'. 可用工具: {list(self.tools.tools.keys())}"

        # 根据工具参数 Schema 解析输入
        try:
            if tool.required:
                # 简化:单参数工具直接传 query/expression
                params = {}
                for param_name in tool.parameters:
                    params[param_name] = tool_input
                return self.tools.execute(tool_name, **params)
            else:
                # 无参数工具
                return self.tools.execute(tool_name)
        except Exception as e:
            return f"工具执行异常: {e}"
