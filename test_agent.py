"""简单测试脚本"""
import sys

# 测试1: 反应层
print("--- 反应层测试 ---")
from src.reactive.layer import ReactiveLayer
reactive = ReactiveLayer()

cases = [
    "SyntaxError: invalid syntax on line 5",
    "ImportError: No module named requests",
    "FileNotFoundError: config.json not found",
    "TypeError: unsupported operand type(s)",
    "KeyError: 'user_id'",
    "PermissionError: [Errno 13] Permission denied",
    "IndentationError: unexpected indent",
]
for c in cases:
    r = reactive.handle(c)
    print(f"  [{'OK' if r.handled else 'FAIL'}] {c[:40]:40s} -> {r.response[:60]}")

# 测试2: 仲裁器
print("\n--- 仲裁器测试 ---")
from src.arbitrator.scheduler import Arbitrator
arb = Arbitrator()

cases = [
    ("SyntaxError: invalid syntax", "reactive"),
    ("ImportError: No module", "reactive"),
    ("帮我设计一个用户认证系统", "deliberative"),
    ("帮我写一个快速排序算法", "deliberative"),
    ("重构这个模块的代码结构", "deliberative"),
    ("如何优化数据库查询性能", "deliberative"),
    ("紧急！服务器崩溃了", "reactive"),
    ("检查这个JSON格式", "reactive"),
]
for task, expected in cases:
    r = arb.arbitrate(task)
    ok = r.mode.value == expected
    print(f"  [{'OK' if ok else 'FAIL'}] {task:30s} -> {r.mode.value:12s} (score={r.complexity_score:.2f})")

# 测试3: 慎思层
print("\n--- 慎思层测试 ---")
from src.deliberative.layer import DeliberativeLayer
from src.tools.registry import ToolRegistry
try:
    dl = DeliberativeLayer(tool_registry=ToolRegistry())
    result = dl.process_with_tools("写一个Python的hello world")
    print(f"  响应: {result['content'][:200]}")
    print(f"  迭代次数: {result['iterations']}")
except Exception as e:
    print(f"  慎思层调用失败: {type(e).__name__}: {str(e)[:150]}")

# 测试4: 完整图
print("\n--- LangGraph完整图测试 ---")
from src.graph import create_agent
agent = create_agent()

r = agent.invoke({"task": "SyntaxError: invalid syntax", "context": {}, "messages": []})
print(f"  反应层路由: layer={r.get('processing_layer')}, score={r.get('complexity_score')}")
print(f"  响应: {r.get('final_response')[:100]}")

try:
    r2 = agent.invoke({"task": "帮我写一个快速排序算法", "context": {}, "messages": []})
    print(f"  慎思层路由: layer={r2.get('processing_layer')}, score={r2.get('complexity_score')}")
    print(f"  响应: {r2.get('final_response')[:200]}")
except Exception as e:
    print(f"  慎思层调用失败: {type(e).__name__}: {str(e)[:150]}")

print("\n--- 测试完成 ---")
