"""LangGraph 混合智能体状态图

三层架构通过 LangGraph 状态图实现协作：
- 反应层节点：快速处理简单任务
- 仲裁器节点：判别任务复杂度，决定路由
- 慎思层节点：大模型深度推理处理复杂任务

状态流转：
  用户输入 → 仲裁器 → 反应层（简单） → 输出
                    → 慎思层（复杂） → 输出
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langgraph.graph import END, StateGraph

from src.arbitrator.scheduler import Arbitrator, ProcessingMode
from src.deliberative.layer import DeliberativeLayer
from src.reactive.layer import ReactiveLayer
from src.tools.registry import ToolRegistry

load_dotenv()


# ---- 状态定义 ----

class AgentState(dict):
    """智能体状态

    在 LangGraph 的各节点之间传递的状态字典。
    """

    # 用户输入
    task: str

    # 上下文信息
    context: dict[str, Any]

    # 历史对话
    messages: list[dict[str, Any]]

    # 仲裁结果
    arbitration_mode: str          # "reactive" | "deliberative"
    arbitration_confidence: float
    arbitration_reason: str
    complexity_score: float

    # 反应层结果
    reactive_handled: bool
    reactive_response: str

    # 慎思层结果
    deliberative_content: str
    deliberative_tool_results: list[dict[str, Any]]
    deliberative_iterations: int

    # 最终输出
    final_response: str
    processing_layer: str  # "reactive" | "deliberative"


# ---- 节点函数 ----

def reactive_node(state: AgentState) -> dict[str, Any]:
    """反应层节点：尝试快速处理"""
    reactive = ReactiveLayer()
    result = reactive.handle(state["task"], state.get("context"))

    return {
        "reactive_handled": result.handled,
        "reactive_response": result.response,
    }


def arbitrator_node(state: AgentState) -> dict[str, Any]:
    """仲裁器节点：判别任务复杂度"""
    arbitrator = Arbitrator()
    result = arbitrator.arbitrate(
        task=state["task"],
        context=state.get("context"),
        reactive_handled=state.get("reactive_handled", False),
    )

    return {
        "arbitration_mode": result.mode.value,
        "arbitration_confidence": result.confidence,
        "arbitration_reason": result.reason,
        "complexity_score": result.complexity_score,
    }


def deliberative_node(state: AgentState) -> dict[str, Any]:
    """慎思层节点：大模型深度推理"""
    tool_registry = ToolRegistry()
    deliberative = DeliberativeLayer(tool_registry=tool_registry)

    result = deliberative.process_with_tools(
        task=state["task"],
        messages=state.get("messages", []),
        context=state.get("context", {}),
        max_iterations=10,
    )

    return {
        "deliberative_content": result["content"],
        "deliberative_tool_results": result.get("tool_results", []),
        "deliberative_iterations": result.get("iterations", 1),
    }


def output_node(state: AgentState) -> dict[str, Any]:
    """输出节点：整合结果，生成最终响应"""
    mode = state.get("arbitration_mode", "reactive")

    if mode == "reactive" and state.get("reactive_handled", False):
        response = state["reactive_response"]
        layer = "反应层"
    elif mode == "deliberative":
        response = state.get("deliberative_content", "")
        layer = "慎思层"
    else:
        # 反应层未处理且未路由到慎思层，降级到慎思层
        response = state.get("deliberative_content", state.get("reactive_response", "无法处理"))
        layer = "慎思层(降级)"

    # 添加仲裁信息
    complexity = state.get("complexity_score", 0)
    reason = state.get("arbitration_reason", "")
    header = f"[{layer} | 复杂度: {complexity:.2f} | {reason}]\n\n"

    return {
        "final_response": header + response,
        "processing_layer": layer,
    }


# ---- 路由函数 ----

def route_after_arbitrator(state: AgentState) -> str:
    """仲裁后路由：决定进入反应层还是慎思层"""
    mode = state.get("arbitration_mode", "deliberative")

    if mode == "reactive":
        # 先尝试反应层
        if state.get("reactive_handled", False):
            return "output"
        return "reactive"
    else:
        return "deliberative"


def route_after_reactive(state: AgentState) -> str:
    """反应层处理后路由"""
    if state.get("reactive_handled", False):
        return "output"
    # 反应层无法处理，升级到慎思层
    return "deliberative"


# ---- 构建状态图 ----

def build_agent_graph() -> StateGraph:
    """构建混合智能体状态图

    图结构:
        input → arbitrator → reactive → output (简单任务)
                        → deliberative → output (复杂任务)

        reactive 失败时 → deliberative (升级处理)
    """
    graph = StateGraph(AgentState)

    # 添加节点
    graph.add_node("arbitrator", arbitrator_node)
    graph.add_node("reactive", reactive_node)
    graph.add_node("deliberative", deliberative_node)
    graph.add_node("output", output_node)

    # 设置入口
    graph.set_entry_point("arbitrator")

    # 仲裁器 → 反应层/慎思层
    graph.add_conditional_edges(
        "arbitrator",
        route_after_arbitrator,
        {
            "reactive": "reactive",
            "deliberative": "deliberative",
            "output": "output",
        },
    )

    # 反应层 → 输出/慎思层
    graph.add_conditional_edges(
        "reactive",
        route_after_reactive,
        {
            "output": "output",
            "deliberative": "deliberative",
        },
    )

    # 慎思层 → 输出
    graph.add_edge("deliberative", "output")

    # 输出 → 结束
    graph.add_edge("output", END)

    return graph


def create_agent():
    """创建并编译混合智能体"""
    graph = build_agent_graph()
    return graph.compile()
