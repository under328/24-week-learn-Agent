"""
Agent 模块 - 工具定义(Tools / Function Calling)

【对应学习日】Day03: Function Calling 与 Tool Use
【核心概念】
  - 工具是 Agent 的"手脚":让 LLM 能与外部世界交互(检索、计算、查询等)
  - 每个工具 = 名称 + 描述 + 参数 Schema + 执行函数
  - LLM 根据用户意图选择工具 → 生成参数 → Harness 执行 → 结果返回 LLM

【面试考点】
  Q: Function Calling 的本质是什么?
  A: LLM 输出结构化 JSON(函数名+参数),由 Harness 层执行函数,结果喂回 LLM。
     LLM 本身不执行代码,只做"决策"。

  Q: 工具描述怎么写最好?
  A: description 要清晰说明"什么时候用这个工具";参数 Schema 用 JSON Schema 格式,
     每个参数加 description。LLM 靠这些文字理解工具能力。
"""
import ast
import json
import operator
from datetime import datetime
from typing import Any, Callable
from dataclasses import dataclass, field


# ============================================================
# 工具数据结构
# ============================================================

@dataclass
class ToolDefinition:
    """
    工具定义(对应 LangChain 的 @tool 装饰器)

    每个工具包含:
      - name: 工具名称(LLM 用这个名字调用)
      - description: 工具描述(告诉 LLM 什么时候用)
      - parameters: 参数描述(告诉 LLM 怎么传参)
      - func: 实际执行函数(Harness 层调用)
    """
    name: str
    description: str
    parameters: dict[str, Any]          # JSON Schema 格式
    func: Callable[..., str]
    required: list[str] = field(default_factory=list)

    def to_prompt(self) -> str:
        """转为 LLM 可读的工具描述文本"""
        params_str = json.dumps(self.parameters, ensure_ascii=False, indent=2)
        return f"  - {self.name}: {self.description}\n    参数: {params_str}"

    def execute(self, **kwargs) -> str:
        """执行工具"""
        try:
            return self.func(**kwargs)
        except Exception as e:
            return f"工具执行错误: {e}"


# ============================================================
# 内置工具实现
# ============================================================

def search_knowledge(query: str, knowledge_base=None) -> str:
    """
    知识检索工具:从知识库中检索与 query 相关的内容

    这个工具是 RAG 的核心 —— Agent 通过它获取外部知识。
    """
    if knowledge_base is None:
        return "(知识库未初始化)"

    results = knowledge_base.search(query, top_k=3)
    if not results:
        return "(未找到相关内容)"

    # 格式化检索结果
    parts = []
    for chunk, score in results:
        parts.append(f"[来源: {chunk.source}, 相关度: {score:.3f}]\n{chunk.content}")
    return "\n\n".join(parts)


def calculator(expression: str) -> str:
    """
    计算器工具:安全地计算数学表达式

    【安全设计】不用 eval()!用 AST 解析,只允许算术运算。
    对应 Day19: Agent 安全 —— 防止代码注入。
    """
    # 安全的运算符映射
    allowed_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,   # 负号
        ast.UAdd: operator.pos,   # 正号
    }

    def _safe_eval(node):
        """递归安全求值"""
        if isinstance(node, ast.Expression):
            return _safe_eval(node.body)
        elif isinstance(node, ast.Constant):  # 数字
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量: {node.value}")
        elif isinstance(node, ast.BinOp):      # 二元运算 a + b
            left = _safe_eval(node.left)
            right = _safe_eval(node.right)
            op_func = allowed_ops.get(type(node.op))
            if op_func is None:
                raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
            return op_func(left, right)
        elif isinstance(node, ast.UnaryOp):    # 一元运算 -a
            operand = _safe_eval(node.operand)
            op_func = allowed_ops.get(type(node.op))
            if op_func is None:
                raise ValueError(f"不支持的一元运算符: {type(node.op).__name__}")
            return op_func(operand)
        else:
            raise ValueError(f"不支持的语法: {type(node).__name__}")

    try:
        tree = ast.parse(expression.strip(), mode="eval")
        result = _safe_eval(tree)
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


def get_time() -> str:
    """时间工具:获取当前时间"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')} ({now.strftime('%A')})"


# ============================================================
# 工具注册器
# ============================================================

class ToolRegistry:
    """
    工具注册中心

    管理所有可用工具,提供:
      - register(): 注册工具
      - get(): 按名称获取工具
      - list_tools(): 列出所有工具(给 LLM 看的描述)
      - execute(): 执行工具
    """

    def __init__(self):
        self.tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        """注册工具"""
        self.tools[tool.name] = tool

    def get(self, name: str) -> ToolDefinition | None:
        """按名称获取工具"""
        return self.tools.get(name)

    def list_tools(self) -> str:
        """生成所有工具的描述文本(放入 LLM prompt)"""
        if not self.tools:
            return "(无可用工具)"
        return "\n".join(tool.to_prompt() for tool in self.tools.values())

    def execute(self, name: str, **kwargs) -> str:
        """执行指定工具"""
        tool = self.get(name)
        if tool is None:
            return f"错误: 未知工具 '{name}'"
        return tool.execute(**kwargs)


def create_default_registry(knowledge_base=None) -> ToolRegistry:
    """
    创建默认工具注册器

    包含 3 个工具:
      1. search_knowledge: 知识库检索(RAG 核心)
      2. calculator: 安全计算器
      3. get_time: 时间查询
    """
    registry = ToolRegistry()

    # 注册知识检索工具
    registry.register(ToolDefinition(
        name="search_knowledge",
        description="从知识库中检索与问题相关的文档内容。当用户询问技术问题、概念解释时使用。",
        parameters={
            "query": {"type": "string", "description": "检索关键词或问题"}
        },
        required=["query"],
        func=lambda query: search_knowledge(query, knowledge_base),
    ))

    # 注册计算器工具
    registry.register(ToolDefinition(
        name="calculator",
        description="计算数学表达式。支持加减乘除、幂运算、取模。当用户需要数学计算时使用。",
        parameters={
            "expression": {"type": "string", "description": "数学表达式,如 '2+3*4'"}
        },
        required=["expression"],
        func=calculator,
    ))

    # 注册时间工具
    registry.register(ToolDefinition(
        name="get_time",
        description="获取当前日期和时间。当用户询问时间时使用。",
        parameters={},
        required=[],
        func=get_time,
    ))

    return registry
