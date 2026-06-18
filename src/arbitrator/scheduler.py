"""中层仲裁调度器：任务复杂度判别 + 模式切换

判断当前任务是否需要调用大模型深度思考，还是可以由反应层快速处理。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProcessingMode(Enum):
    """处理模式"""
    REACTIVE = "reactive"       # 反应式：简单任务，规则引擎快速响应
    DELIBERATIVE = "deliberative"  # 慎思式：复杂任务，大模型深度推理


@dataclass
class ArbitrationResult:
    """仲裁结果"""
    mode: ProcessingMode
    confidence: float  # 0.0 ~ 1.0，判别置信度
    reason: str        # 判别理由
    complexity_score: float  # 复杂度评分 0.0 ~ 1.0


class Arbitrator:
    """中层仲裁调度器

    通过多维度信号评估任务复杂度，决定路由到反应层还是慎思层：
    - 关键词信号：特定关键词暗示任务类型
    - 结构信号：任务长度、步骤数、是否包含多步逻辑
    - 上下文信号：历史对话、错误重试次数
    - 时效信号：紧急程度
    """

    # 复杂任务关键词（倾向慎思层）
    COMPLEX_KEYWORDS = [
        "设计", "架构", "重构", "优化", "分析", "实现",
        "开发", "编写", "创建", "构建", "部署",
        "写一个", "帮我写", "设计一个", "实现一个",
        "debug", "修复", "排查", "定位",
        "多步骤", "流程", "方案", "规划",
        "为什么", "如何", "怎么",
        "设计模式", "最佳实践", "性能",
        "算法", "排序", "搜索", "数据结构",
        "explain", "design", "implement", "refactor",
        "optimize", "architect",
    ]

    # 简单任务关键词（倾向反应层）
    SIMPLE_KEYWORDS = [
        "格式校验", "语法检查", "文件是否存在",
        "报错", "错误信息", "异常",
        "SyntaxError", "TypeError", "ImportError",
        "KeyError", "FileNotFoundError",
        "简单", "检查",
        "是什么", "定义",
    ]

    # 紧急信号关键词（倾向反应层快速响应）
    URGENT_KEYWORDS = [
        "紧急", "立刻", "马上", "赶紧",
        "urgent", "asap", "immediately",
        "崩溃", "crash", "挂了",
    ]

    def __init__(self, complexity_threshold: float = 0.4) -> None:
        """
        Args:
            complexity_threshold: 复杂度阈值，超过此值路由到慎思层
        """
        self.complexity_threshold = complexity_threshold

    def arbitrate(
        self,
        task: str,
        context: dict[str, Any] | None = None,
        reactive_handled: bool = False,
    ) -> ArbitrationResult:
        """仲裁任务应该由哪一层处理

        Args:
            task: 任务描述
            context: 上下文信息
            reactive_handled: 反应层是否已处理过

        Returns:
            ArbitrationResult: 仲裁结果
        """
        context = context or {}

        # 如果反应层已经处理了，直接返回反应式
        if reactive_handled:
            return ArbitrationResult(
                mode=ProcessingMode.REACTIVE,
                confidence=0.9,
                reason="反应层已成功处理",
                complexity_score=0.0,
            )

        # 计算复杂度评分
        complexity = self._calculate_complexity(task, context)

        # 判断模式
        if complexity >= self.complexity_threshold:
            mode = ProcessingMode.DELIBERATIVE
            reason = self._get_deliberative_reason(task, complexity)
        else:
            mode = ProcessingMode.REACTIVE
            reason = self._get_reactive_reason(task, complexity)

        confidence = abs(complexity - self.complexity_threshold) / 0.5
        confidence = min(confidence, 1.0)

        return ArbitrationResult(
            mode=mode,
            confidence=confidence,
            reason=reason,
            complexity_score=complexity,
        )

    def _calculate_complexity(
        self, task: str, context: dict[str, Any]
    ) -> float:
        """计算任务复杂度评分 (0.0 ~ 1.0)"""
        score = 0.0

        # 1. 关键词信号 (权重: 0.45) - 关键词是最直接的复杂度信号
        keyword_score = self._keyword_signal(task)
        score += keyword_score * 0.45

        # 2. 结构信号 (权重: 0.25)
        structure_score = self._structure_signal(task)
        score += structure_score * 0.25

        # 3. 时效信号 (权重: 0.1) - 紧急任务降低复杂度
        urgency_score = self._urgency_signal(task)
        score -= urgency_score * 0.1

        # 4. 上下文信号 (权重: 0.2)
        context_score = self._context_signal(task, context)
        score += context_score * 0.2

        return max(0.0, min(1.0, score))

    def _keyword_signal(self, task: str) -> float:
        """关键词信号评分"""
        task_lower = task.lower()
        complex_count = sum(1 for kw in self.COMPLEX_KEYWORDS if kw.lower() in task_lower)
        simple_count = sum(1 for kw in self.SIMPLE_KEYWORDS if kw.lower() in task_lower)

        if complex_count + simple_count == 0:
            return 0.5  # 无明确信号，中性

        return complex_count / (complex_count + simple_count)

    def _structure_signal(self, task: str) -> float:
        """结构信号评分：任务越长、步骤越多，越复杂"""
        score = 0.0

        # 长度信号
        length = len(task)
        if length > 200:
            score += 0.3
        elif length > 100:
            score += 0.2
        elif length > 50:
            score += 0.1

        # 多步骤信号
        step_patterns = [r"然后", r"接着", r"之后", r"第一步", r"第二步", r"首先", r"其次", r"最后"]
        step_count = sum(1 for p in step_patterns if re.search(p, task))
        score += min(step_count * 0.15, 0.4)

        # 代码块信号
        if "```" in task or "def " in task or "class " in task:
            score += 0.3

        return min(score, 1.0)

    def _urgency_signal(self, task: str) -> float:
        """时效信号评分：紧急程度越高，越倾向反应层"""
        task_lower = task.lower()
        count = sum(1 for kw in self.URGENT_KEYWORDS if kw.lower() in task_lower)
        return min(count * 0.5, 1.0)

    def _context_signal(self, task: str, context: dict[str, Any]) -> float:
        """上下文信号评分"""
        score = 0.0

        # 重试次数越多，问题越复杂
        retry_count = context.get("retry_count", 0)
        score += min(retry_count * 0.2, 0.5)

        # 是否涉及多个文件
        files = context.get("related_files", [])
        if len(files) > 1:
            score += 0.3

        # 是否涉及跨模块
        if context.get("cross_module", False):
            score += 0.2

        return min(score, 1.0)

    def _get_deliberative_reason(self, task: str, complexity: float) -> str:
        return (
            f"任务复杂度评分 {complexity:.2f} 超过阈值 {self.complexity_threshold}，"
            f"需要大模型深度推理。"
        )

    def _get_reactive_reason(self, task: str, complexity: float) -> str:
        return (
            f"任务复杂度评分 {complexity:.2f} 低于阈值 {self.complexity_threshold}，"
            f"可由反应层快速响应。"
        )
