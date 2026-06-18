"""顶层慎思层：大模型（qwen3.6-plus）深度推理

负责：复杂任务拆解、长期目标规划、工具调用编排、多步骤逻辑推理、方案复盘优化
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.tools.registry import ToolRegistry

load_dotenv()

# 系统提示词：定义慎思层的行为规范
SYSTEM_PROMPT = """你是一个专业的代码开发智能体，工作在混合智能体架构的慎思层。

## 你的核心能力
1. **复杂任务拆解**：将大型开发任务分解为可执行的子任务
2. **长期目标规划**：制定多步骤的开发计划和实施路径
3. **工具调用编排**：合理选择和组合工具完成开发任务
4. **多步骤逻辑推理**：通过链式思考解决复杂编程问题
5. **方案复盘优化**：评估已有方案并提出改进建议

## 工作原则
- 在编写代码前，先分析需求和设计思路
- 优先考虑代码的可读性、可维护性和健壮性
- 遵循项目的编码规范和最佳实践
- 遇到不确定的问题时，主动说明并给出多种可选方案
- 修改代码时，最小化变更范围，避免不必要的重构

## 可用工具
{tools_description}

## 输出格式
当需要使用工具时，请直接调用工具。
当不需要工具时，请直接给出分析和建议。
"""


class DeliberativeLayer:
    """顶层慎思层：大模型深度推理"""

    def __init__(
        self,
        model_name: str = "qwen3.6-plus",
        api_key: str | None = None,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature: float = 0.7,
        tool_registry: ToolRegistry | None = None,
    ) -> None:
        """
        Args:
            model_name: 模型名称
            api_key: DashScope API Key，默认从环境变量读取
            base_url: API 基础URL
            temperature: 生成温度
            tool_registry: 工具注册表
        """
        api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError("DASHSCOPE_API_KEY 未设置，请在 .env 文件中配置")

        self.tool_registry = tool_registry or ToolRegistry()
        self.model_name = model_name

        # 获取工具列表
        tools = self.tool_registry.get_langchain_tools()

        # 初始化大模型
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )

        # 绑定工具
        if tools:
            self.llm_with_tools = self.llm.bind_tools(tools)
        else:
            self.llm_with_tools = self.llm

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        tools_description = self.tool_registry.get_tools_description()
        return SYSTEM_PROMPT.format(tools_description=tools_description)

    def process(
        self,
        task: str,
        messages: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """处理复杂任务

        Args:
            task: 任务描述
            messages: 历史对话消息
            context: 上下文信息

        Returns:
            包含响应和工具调用的字典
        """
        context = context or {}

        # 构建消息列表
        full_messages = [{"role": "system", "content": self._build_system_prompt()}]

        # 添加历史消息
        if messages:
            full_messages.extend(messages)

        # 添加当前任务
        full_messages.append({"role": "user", "content": task})

        # 调用大模型
        response = self.llm_with_tools.invoke(full_messages)

        # 处理工具调用
        tool_calls = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_calls = response.tool_calls

        return {
            "content": response.content or "",
            "tool_calls": tool_calls,
            "response": response,
        }

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """执行工具调用

        Args:
            tool_calls: 工具调用列表

        Returns:
            工具执行结果列表
        """
        results = []
        for tc in tool_calls:
            tool_name = tc["name"] if isinstance(tc, dict) else tc.name
            tool_args = tc["args"] if isinstance(tc, dict) else tc.args

            result = self.tool_registry.execute(tool_name, tool_args)
            results.append({
                "tool": tool_name,
                "args": tool_args,
                "result": result,
            })

        return results

    def process_with_tools(
        self,
        task: str,
        messages: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
        max_iterations: int = 5,
    ) -> dict[str, Any]:
        """带工具调用的多轮处理

        Args:
            task: 任务描述
            messages: 历史对话消息
            context: 上下文信息
            max_iterations: 最大迭代次数

        Returns:
            最终处理结果
        """
        context = context or {}
        full_messages = [{"role": "system", "content": self._build_system_prompt()}]

        if messages:
            full_messages.extend(messages)

        full_messages.append({"role": "user", "content": task})

        all_tool_results = []

        try:
            for i in range(max_iterations):
                response = self.llm_with_tools.invoke(full_messages)

                # 没有工具调用，直接返回
                if not (hasattr(response, "tool_calls") and response.tool_calls):
                    return {
                        "content": response.content or "",
                        "tool_results": all_tool_results,
                        "iterations": i + 1,
                    }

                # 添加助手消息
                full_messages.append(response)

                # 执行工具调用
                for tc in response.tool_calls:
                    tool_name = tc["name"] if isinstance(tc, dict) else tc.name
                    tool_args = tc["args"] if isinstance(tc, dict) else tc.args

                    result = self.tool_registry.execute(tool_name, tool_args)
                    all_tool_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result,
                    })

                    # 添加工具结果消息
                    from langchain_core.messages import ToolMessage
                    full_messages.append(
                        ToolMessage(
                            content=str(result),
                            tool_call_id=tc["id"] if isinstance(tc, dict) else tc.id,
                        )
                    )
        except Exception as e:
            return {
                "content": f"[慎思层调用失败] {type(e).__name__}: {str(e)[:300]}",
                "tool_results": all_tool_results,
                "iterations": 0,
                "error": str(e),
            }

        return {
            "content": response.content or "达到最大迭代次数",
            "tool_results": all_tool_results,
            "iterations": max_iterations,
        }
