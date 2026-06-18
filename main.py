"""混合智能体代码开发助手 - 入口文件

使用方法:
    python main.py "你的任务描述"

示例:
    python main.py "帮我写一个快速排序算法"
    python main.py "SyntaxError: invalid syntax"
    python main.py "设计一个用户认证系统"
"""

from __future__ import annotations

import sys

from dotenv import load_dotenv

load_dotenv()

from src.graph import create_agent


def run(task: str, context: dict | None = None) -> str:
    """运行混合智能体

    Args:
        task: 任务描述
        context: 上下文信息

    Returns:
        智能体响应
    """
    agent = create_agent()

    initial_state = {
        "task": task,
        "context": context or {},
        "messages": [],
    }

    result = agent.invoke(initial_state)
    return result.get("final_response", "处理失败")


def interactive_mode():
    """交互式模式"""
    print("=" * 60)
    print("  混合智能体代码开发助手 (Hybrid Agent)")
    print("  三层架构: 反应层 → 仲裁器 → 慎思层")
    print("  输入 'quit' 退出")
    print("=" * 60)

    agent = create_agent()
    messages = []

    while True:
        try:
            task = input("\n🧑 你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not task:
            continue
        if task.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        initial_state = {
            "task": task,
            "context": {},
            "messages": messages,
        }

        result = agent.invoke(initial_state)
        response = result.get("final_response", "处理失败")
        layer = result.get("processing_layer", "未知")

        # 保存对话历史
        messages.append({"role": "user", "content": task})
        messages.append({"role": "assistant", "content": response})

        print(f"\n🤖 [{layer}]: {response}")


def main():
    if len(sys.argv) > 1:
        # 命令行模式
        task = " ".join(sys.argv[1:])
        response = run(task)
        print(response)
    else:
        # 交互式模式
        interactive_mode()


if __name__ == "__main__":
    main()
