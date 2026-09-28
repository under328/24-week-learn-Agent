"""
Agent 模块 - LLM 接口

【对应学习日】Day01, Day34: LLM 调用与模型理解
【核心概念】
  - LLM 是 Agent 的"大脑":接收文本输入,生成文本输出
  - 本项目支持两种模式:Mock(零配置)和 OpenAI(真实 LLM)
  - 统一接口:generate(prompt) → response,切换模式只需改配置

【设计模式】
  策略模式:定义统一接口,运行时切换具体实现(Mock / OpenAI)。
  生产环境可扩展更多后端:Anthropic、本地模型(Ollama)等。
"""
import re
import config


class LLMBase:
    """LLM 接口基类(策略模式的抽象接口)"""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """生成文本"""
        raise NotImplementedError


class MockLLM(LLMBase):
    """
    模拟 LLM(零配置,无需 API Key)

    【设计思路】
    真实的 LLM 通过训练学会了"遵循指令"。Mock LLM 用规则模拟这个过程:
      1. 如果 prompt 中包含 ReAct 格式要求 → 生成 ReAct 格式响应
      2. 如果问题是数学计算 → 调用计算器工具
      3. 如果问题需要知识 → 调用知识检索工具
      4. 否则 → 直接回答

    这样即使没有 API Key,也能完整演示 ReAct 循环和工具调用流程。
    """

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """
        模拟 LLM 生成响应

        Mock LLM 的"智能"体现在:
          - 能识别是否需要工具(根据 prompt 中的可用工具列表)
          - 能生成 ReAct 格式(Thought/Action/Action Input)
          - 能根据 Observation 生成最终答案
        """
        prompt_lower = prompt.lower()

        # ---- 情况 1:ReAct 决策步骤(prompt 含工具列表和 Question) ----
        if "以下工具" in prompt or "available tools" in prompt_lower:
            return self._react_decide(prompt)

        # ---- 情况 2:ReAct 总结步骤(有 Observation) ----
        if "observation:" in prompt_lower or "观察结果:" in prompt:
            return self._react_summarize(prompt)

        # ---- 情况 3:普通问答(无工具) ----
        return self._direct_answer(prompt)

    def _react_decide(self, prompt: str) -> str:
        """模拟 ReAct 的决策:选择工具还是直接回答"""

        # 提取用户问题(prompt 中 "Question:" 后的内容)
        question_match = re.search(r'[Qq]uestion[:：]\s*(.+?)(?:\n|$)', prompt)
        question = question_match.group(1).strip() if question_match else ""
        q_lower = question.lower()

        # 判断是否需要计算器
        if re.search(r'\d+\s*[+\-*/×÷]\s*\d+', question) or "计算" in question:
            # 提取数学表达式
            expr_match = re.search(r'([\d+\-*/().×÷\s]+)', question)
            expr = expr_match.group(1).strip() if expr_match else "0"
            # 标准化运算符
            expr = expr.replace("×", "*").replace("÷", "/")
            return (
                f"Thought: 用户问了一个数学计算问题,我需要使用计算器工具来准确计算。\n"
                f"Action: calculator\n"
                f"Action Input: {expr}"
            )

        # 判断是否需要知识检索(问题中包含 Agent/RAG/Python/LLM 等关键词)
        knowledge_keywords = ["agent", "rag", "python", "llm", "transformer", "attention",
                             "retrieval", "embedding", "向量", "检索", "知识库", "模型"]
        if any(kw in q_lower for kw in knowledge_keywords):
            return (
                f"Thought: 用户询问了技术相关问题,我需要从知识库中检索相关信息来回答。\n"
                f"Action: search_knowledge\n"
                f"Action Input: {question}"
            )

        # 判断是否问时间
        if "时间" in question or "time" in q_lower or "几点" in question:
            return (
                f"Thought: 用户询问当前时间,我需要调用时间工具。\n"
                f"Action: get_time\n"
                f"Action Input: "
            )

        # 默认:直接回答(不需要工具)
        return (
            f"Thought: 这个问题我可以直接回答,不需要使用工具。\n"
            f"Action: finish\n"
            f"Action Input: 关于'{question}',这是一个我能直接回答的问题。"
            f"(注:这是 Mock LLM 的模拟回答,配置 OpenAI API Key 后可获得真实回复)"
        )

    def _react_summarize(self, prompt: str) -> str:
        """模拟 ReAct 的总结:根据 Observation 生成最终答案"""

        # 提取 Observation
        obs_match = re.search(r'[Oo]bservation[:：]\s*(.+?)(?:\n\n|$)', prompt, re.DOTALL)
        observation = obs_match.group(1).strip() if obs_match else ""

        # 提取原始问题
        q_match = re.search(r'[Qq]uestion[:：]\s*(.+?)(?:\n|$)', prompt)
        question = q_match.group(1).strip() if q_match else ""

        if observation and observation != "(无)":
            # 有检索结果,生成基于上下文的回答
            return (
                f"Thought: 我已经获得了相关信息,现在可以综合回答用户的问题了。\n"
                f"Action: finish\n"
                f"Action Input: 根据知识库中的信息,关于'{question}':\n\n"
                f"{observation[:500]}\n\n"
                f"(注:以上内容来自知识库检索,配置真实 LLM 后将获得更自然的总结)"
            )
        else:
            return (
                f"Thought: 检索没有返回相关信息,我需要基于自身知识回答。\n"
                f"Action: finish\n"
                f"Action Input: 抱歉,知识库中未找到关于'{question}'的相关信息。"
                f"(Mock LLM 回答,配置 OpenAI API Key 后可用真实模型)"
            )

    def _direct_answer(self, prompt: str) -> str:
        """直接回答(无 ReAct 格式)"""
        return f"[Mock LLM 回答] 我收到了你的请求。配置 OPENAI_API_KEY 后我将提供真实的 AI 回复。"


class OpenAILLM(LLMBase):
    """
    OpenAI LLM(真实 LLM,需要 API Key)

    使用 OpenAI Chat Completions API。
    支持 GPT-4o / GPT-4o-mini / GPT-3.5-turbo 等模型。
    """

    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL,
        )
        self.model = config.OPENAI_MODEL

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """调用 OpenAI API 生成响应"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content


def create_llm() -> LLMBase:
    """
    工厂函数:根据配置创建 LLM 实例

    - config.LLM_MODE = "mock"   → MockLLM(零配置)
    - config.LLM_MODE = "openai" → OpenAILLM(需要 API Key)
    """
    if config.LLM_MODE == "openai":
        if not config.OPENAI_API_KEY:
            print("[LLM] 警告: LLM_MODE=openai 但未设置 OPENAI_API_KEY,回退到 Mock 模式")
            return MockLLM()
        return OpenAILLM()
    return MockLLM()
