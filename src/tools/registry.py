"""代码开发工具注册表

提供文件读写、代码执行、搜索等工具，供慎思层调用。
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from langchain_core.tools import tool


@tool
def read_file(file_path: str) -> str:
    """读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        文件内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"错误：文件不存在 {file_path}"
    except Exception as e:
        return f"读取文件失败: {e}"


@tool
def write_file(file_path: str, content: str) -> str:
    """写入文件内容（会覆盖已有文件）

    Args:
        file_path: 文件路径
        content: 要写入的内容

    Returns:
        操作结果
    """
    try:
        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"文件写入成功: {file_path}"
    except Exception as e:
        return f"写入文件失败: {e}"


@tool
def list_directory(dir_path: str, pattern: str = "*") -> str:
    """列出目录内容

    Args:
        dir_path: 目录路径
        pattern: 文件匹配模式，默认 *

    Returns:
        目录内容列表
    """
    import glob

    try:
        matches = glob.glob(os.path.join(dir_path, pattern))
        if not matches:
            return f"目录为空或不存在: {dir_path}"
        return "\n".join(sorted(matches))
    except Exception as e:
        return f"列出目录失败: {e}"


@tool
def execute_code(code: str, language: str = "python", timeout: int = 30) -> str:
    """执行代码并返回输出

    Args:
        code: 要执行的代码
        language: 编程语言，目前支持 python
        timeout: 超时时间（秒）

    Returns:
        执行输出
    """
    if language != "python":
        return f"暂不支持 {language} 语言执行"

    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout
        if result.returncode != 0:
            output += f"\n[错误] {result.stderr}"
        return output or "(无输出)"
    except subprocess.TimeoutExpired:
        return f"执行超时（{timeout}秒限制）"
    except Exception as e:
        return f"执行失败: {e}"


@tool
def search_in_files(directory: str, pattern: str, file_type: str = "") -> str:
    """在文件中搜索文本模式

    Args:
        directory: 搜索目录
        pattern: 搜索模式（支持正则表达式）
        file_type: 文件类型过滤，如 .py, .js

    Returns:
        匹配结果
    """
    import re

    results = []
    try:
        for root, dirs, files in os.walk(directory):
            # 跳过隐藏目录和常见忽略目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in (
                "node_modules", "__pycache__", ".git", "venv", ".venv"
            )]
            for fname in files:
                if file_type and not fname.endswith(file_type):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                results.append(f"{fpath}:{i}: {line.strip()}")
                                if len(results) >= 50:
                                    return "\n".join(results) + "\n...(结果过多，已截断)"
                except Exception:
                    continue
    except Exception as e:
        return f"搜索失败: {e}"

    return "\n".join(results) if results else "未找到匹配结果"


@tool
def validate_json(json_string: str) -> str:
    """校验JSON格式是否正确

    Args:
        json_string: JSON字符串

    Returns:
        校验结果
    """
    try:
        json.loads(json_string)
        return "JSON格式正确"
    except json.JSONDecodeError as e:
        return f"JSON格式错误: {e}"


@tool
def install_package(package_name: str) -> str:
    """安装Python包

    Args:
        package_name: 包名

    Returns:
        安装结果
    """
    try:
        result = subprocess.run(
            ["pip", "install", package_name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return f"安装成功: {package_name}"
        return f"安装失败: {result.stderr}"
    except Exception as e:
        return f"安装异常: {e}"


class ToolRegistry:
    """工具注册表：管理和执行所有可用工具"""

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """注册默认工具"""
        default_tools = [
            read_file,
            write_file,
            list_directory,
            execute_code,
            search_in_files,
            validate_json,
            install_package,
        ]
        for t in default_tools:
            self._tools[t.name] = t

    def register(self, tool_func: Any) -> None:
        """注册自定义工具"""
        self._tools[tool_func.name] = tool_func

    def get_tool(self, name: str) -> Any | None:
        """获取工具"""
        return self._tools.get(name)

    def get_all_tools(self) -> list[Any]:
        """获取所有工具"""
        return list(self._tools.values())

    def get_langchain_tools(self) -> list[Any]:
        """获取 LangChain 格式的工具列表"""
        return self.get_all_tools()

    def get_tools_description(self) -> str:
        """获取工具描述文本"""
        descriptions = []
        for name, t in self._tools.items():
            desc = t.description if hasattr(t, "description") else ""
            descriptions.append(f"- **{name}**: {desc}")
        return "\n".join(descriptions)

    def execute(self, tool_name: str, tool_args: dict[str, Any]) -> Any:
        """执行工具调用

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            工具执行结果
        """
        t = self._tools.get(tool_name)
        if not t:
            return f"未知工具: {tool_name}"

        try:
            return t.invoke(tool_args)
        except Exception as e:
            return f"工具执行失败 [{tool_name}]: {e}"
