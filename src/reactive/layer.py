"""底层反应层：规则引擎 + 轻量函数调用，处理高频简单重复任务"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReactiveResult:
    """反应层处理结果"""
    handled: bool  # 是否已被反应层处理
    response: str  # 处理结果文本
    data: dict[str, Any] = field(default_factory=dict)


class RuleEngine:
    """规则引擎：基于关键词匹配和正则表达式的快速响应"""

    def __init__(self) -> None:
        self._rules: list[dict[str, Any]] = []
        self._register_default_rules()

    def add_rule(
        self,
        name: str,
        pattern: str | re.Pattern,
        handler: callable,
        priority: int = 0,
    ) -> None:
        """添加规则

        Args:
            name: 规则名称
            pattern: 匹配模式（字符串精确匹配或正则表达式）
            handler: 处理函数 (match_result) -> str
            priority: 优先级，数值越大越先匹配
        """
        compiled = re.compile(pattern) if isinstance(pattern, str) else pattern
        self._rules.append({
            "name": name,
            "pattern": compiled,
            "handler": handler,
            "priority": priority,
        })
        self._rules.sort(key=lambda r: r["priority"], reverse=True)

    def match(self, text: str) -> ReactiveResult | None:
        """尝试匹配规则，返回第一个匹配结果"""
        for rule in self._rules:
            m = rule["pattern"].search(text)
            if m:
                response = rule["handler"](m)
                return ReactiveResult(
                    handled=True,
                    response=response,
                    data={"rule": rule["name"]},
                )
        return None

    def _register_default_rules(self) -> None:
        """注册默认的代码开发相关规则"""

        # 语法错误快速识别
        self.add_rule(
            name="syntax_error_python",
            pattern=r"SyntaxError[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 检测到Python语法错误: {m.group(1)}。请检查括号、冒号、缩进是否正确。",
            priority=10,
        )

        # 缩进错误
        self.add_rule(
            name="indentation_error",
            pattern=r"IndentationError[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 检测到缩进错误: {m.group(1)}。请统一使用4空格缩进。",
            priority=10,
        )

        # 导入错误
        self.add_rule(
            name="import_error",
            pattern=r"(?:ImportError|ModuleNotFoundError)[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 检测到模块导入错误: {m.group(1)}。请确认依赖已安装，可运行 pip install 安装缺失模块。",
            priority=10,
        )

        # 文件不存在
        self.add_rule(
            name="file_not_found",
            pattern=r"(?:FileNotFoundError|No such file or directory)[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 文件未找到: {m.group(1)}。请检查文件路径是否正确。",
            priority=10,
        )

        # 权限错误
        self.add_rule(
            name="permission_error",
            pattern=r"PermissionError[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 权限不足: {m.group(1)}。请检查文件/目录权限。",
            priority=10,
        )

        # 类型错误
        self.add_rule(
            name="type_error",
            pattern=r"TypeError[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 类型错误: {m.group(1)}。请检查变量类型是否匹配。",
            priority=5,
        )

        # 键错误
        self.add_rule(
            name="key_error",
            pattern=r"KeyError[:\s]+(.+)",
            handler=lambda m: f"[反应层-快速响应] 键错误: {m.group(1)}。请检查字典键是否存在。",
            priority=5,
        )

        # 简单格式校验请求
        self.add_rule(
            name="format_check",
            pattern=r"(?:检查|校验|验证).*(?:格式|JSON|json|yaml|YAML)",
            handler=lambda m: "[反应层-快速响应] 格式校验服务就绪，请提供需要校验的内容。",
            priority=3,
        )


class ReactiveLayer:
    """底层反应层：即时处理紧急和简单任务"""

    def __init__(self) -> None:
        self.rule_engine = RuleEngine()

    def handle(self, task: str, context: dict[str, Any] | None = None) -> ReactiveResult:
        """处理任务，尝试用规则引擎快速响应

        Args:
            task: 用户任务描述
            context: 上下文信息

        Returns:
            ReactiveResult: 处理结果
        """
        context = context or {}

        # 1. 尝试规则引擎匹配
        result = self.rule_engine.match(task)
        if result:
            return result

        # 2. 尝试轻量函数调用处理
        result = self._try_lightweight_handlers(task, context)
        if result:
            return result

        # 3. 无法处理，返回未处理
        return ReactiveResult(handled=False, response="")

    def _try_lightweight_handlers(
        self, task: str, context: dict[str, Any]
    ) -> ReactiveResult | None:
        """轻量级函数调用处理"""

        # JSON格式校验
        if self._is_json_validation(task, context):
            return self._validate_json(task, context)

        # 文件存在性检查
        if self._is_file_check(task, context):
            return self._check_file(task, context)

        # 简单代码执行（安全限制）
        if self._is_simple_execution(task, context):
            return self._execute_simple(task, context)

        return None

    def _is_json_validation(self, task: str, context: dict[str, Any]) -> bool:
        keywords = ["json", "JSON", "格式校验", "验证格式", "格式检查"]
        return any(kw in task for kw in keywords) and "json_string" in context

    def _validate_json(self, task: str, context: dict[str, Any]) -> ReactiveResult:
        json_str = context.get("json_string", "")
        try:
            json.loads(json_str)
            return ReactiveResult(
                handled=True,
                response="[反应层] JSON格式校验通过。",
                data={"valid": True},
            )
        except json.JSONDecodeError as e:
            return ReactiveResult(
                handled=True,
                response=f"[反应层] JSON格式错误: {e}",
                data={"valid": False, "error": str(e)},
            )

    def _is_file_check(self, task: str, context: dict[str, Any]) -> bool:
        keywords = ["文件是否存在", "检查文件", "file exists", "文件存在"]
        return any(kw in task for kw in keywords) and "file_path" in context

    def _check_file(self, task: str, context: dict[str, Any]) -> ReactiveResult:
        file_path = context.get("file_path", "")
        exists = os.path.exists(file_path)
        return ReactiveResult(
            handled=True,
            response=f"[反应层] 文件{'存在' if exists else '不存在'}: {file_path}",
            data={"exists": exists},
        )

    def _is_simple_execution(self, task: str, context: dict[str, Any]) -> bool:
        keywords = ["执行", "运行", "run", "execute"]
        code = context.get("code", "")
        # 仅允许简单安全的代码片段
        dangerous = ["import os", "import subprocess", "import sys", "rm ", "rmdir", "shutil"]
        is_safe = not any(d in code for d in dangerous) and len(code) < 500
        return any(kw in task for kw in keywords) and code and is_safe

    def _execute_simple(self, task: str, context: dict[str, Any]) -> ReactiveResult:
        code = context.get("code", "")
        try:
            result = subprocess.run(
                ["python3", "-c", code],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = result.stdout if result.returncode == 0 else result.stderr
            return ReactiveResult(
                handled=True,
                response=f"[反应层] 执行结果:\n{output}",
                data={"returncode": result.returncode, "output": output},
            )
        except subprocess.TimeoutExpired:
            return ReactiveResult(
                handled=True,
                response="[反应层] 执行超时（5秒限制），此任务需要升级到慎思层处理。",
                data={"timeout": True},
            )
