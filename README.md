# Case-Agent-Hybrid

基于 LangGraph 的混合智能体代码开发助手，采用**三层混合架构**（反应层 → 仲裁器 → 慎思层），根据任务复杂度自动路由，兼顾简单任务的响应速度与复杂任务的推理深度。

## 架构概览

```
用户输入
   │
   ▼
┌──────────────┐
│   仲裁器      │  评估任务复杂度 (0.0~1.0)，决定路由方向
│  Arbitrator   │
└──────┬───────┘
       │
       ├─ 复杂度 < 阈值 ──▶ ┌──────────────┐
       │                    │   反应层      │  规则引擎 + 轻量函数，毫秒级响应
       │                    │  ReactiveLayer│
       │                    └──────┬───────┘
       │                           │ 处理失败时升级
       │                           ▼
       ├─ 复杂度 ≥ 阈值 ──▶ ┌──────────────┐
       │                    │   慎思层      │  大模型深度推理 + 工具调用
       │                    │DeliberativeLayer│
       │                    └──────┬───────┘
       │                           │
       ▼                           ▼
┌──────────────┐
│   输出节点    │  整合结果，生成最终响应
│  OutputNode  │
└──────────────┘
```

## 三层架构详解

### 1. 反应层 (Reactive Layer)

底层快速响应层，基于**规则引擎 + 轻量函数调用**，处理高频简单重复任务。

- **规则引擎**：通过关键词匹配和正则表达式，即时识别常见错误（SyntaxError、ImportError、FileNotFoundError 等）并给出修复建议
- **轻量函数**：JSON 格式校验、文件存在性检查、简单代码执行（带安全限制）
- **升级机制**：无法处理时自动升级到慎思层

### 2. 仲裁器 (Arbitrator)

中层调度器，通过多维度信号评估任务复杂度，决定路由方向。

**复杂度评分维度：**

| 信号维度   | 权重 | 说明                                 |
| ---------- | ---- | ------------------------------------ |
| 关键词信号 | 0.45 | 匹配复杂/简单/紧急关键词             |
| 结构信号   | 0.25 | 任务长度、步骤数、代码块检测         |
| 上下文信号 | 0.20 | 重试次数、跨模块、多文件             |
| 时效信号   | 0.10 | 紧急程度（降低复杂度，倾向快速响应） |

默认复杂度阈值为 0.4，超过阈值路由到慎思层。

### 3. 慎思层 (Deliberative Layer)

顶层深度推理层，基于**大模型（qwen3.6-plus）+ 工具调用**，处理复杂任务。

- **核心能力**：复杂任务拆解、长期目标规划、工具调用编排、多步骤逻辑推理、方案复盘优化
- **工具系统**：支持文件读写、代码执行、文件搜索、JSON 校验、包安装等
- **多轮迭代**：支持最多 10 轮工具调用迭代，自动处理工具返回结果

## 项目结构

```
agent-hybrid/
├── main.py                          # 入口文件，支持命令行和交互式模式
├── src/
│   ├── graph.py                     # LangGraph 状态图定义，节点与路由逻辑
│   ├── arbitrator/
│   │   └── scheduler.py             # 仲裁器：复杂度评估与路由决策
│   ├── deliberative/
│   │   └── layer.py                 # 慎思层：大模型推理 + 工具调用
│   ├── reactive/
│   │   └── layer.py                 # 反应层：规则引擎 + 轻量函数
│   └── tools/
│       └── registry.py              # 工具注册表：文件读写、代码执行等
├── auth_system/                     # 用户认证系统（慎思层生成的示例模块）
│   ├── config.py                    # JWT/数据库/CORS 配置
│   ├── database.py                  # SQLAlchemy 数据库连接
│   ├── schemas.py                   # Pydantic 数据验证模型
│   ├── models/
│   │   └── user.py                  # 用户 ORM 模型
│   ├── api/                         # API 路由
│   ├── services/                    # 业务逻辑
│   └── utils/                       # 工具函数
├── test_agent.py                    # 测试脚本
├── requirements.txt                 # 依赖
└── .env                             # 环境变量
```

## 状态流转

LangGraph 状态图中的核心流转路径：

```
input → arbitrator ─┬─→ reactive ─┬─→ output (简单任务，反应层处理成功)
                     │              └─→ deliberative → output (反应层失败，升级)
                     └─→ deliberative → output (复杂任务，直接路由慎思层)
```

**AgentState** 在节点间传递的关键字段：

- `task` / `context` / `messages` — 用户输入
- `arbitration_mode` / `complexity_score` — 仲裁结果
- `reactive_handled` / `reactive_response` — 反应层结果
- `deliberative_content` / `deliberative_tool_results` — 慎思层结果
- `final_response` / `processing_layer` — 最终输出

## 内置工具

慎思层可通过工具调用完成代码开发任务：

| 工具              | 说明                 |
| ----------------- | -------------------- |
| `read_file`       | 读取文件内容         |
| `write_file`      | 写入文件             |
| `list_directory`  | 列出目录内容         |
| `execute_code`    | 执行 Python 代码     |
| `search_in_files` | 在文件中搜索文本模式 |
| `validate_json`   | 校验 JSON 格式       |
| `install_package` | 安装 Python 包       |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `.env` 文件中设置：

```
DASHSCOPE_API_KEY=your-api-key-here
```

### 3. 运行

**命令行模式：**

```bash
python main.py "帮我写一个快速排序算法"
python main.py "SyntaxError: invalid syntax"
```

**交互式模式：**

```bash
python main.py
```

## 技术栈

- **LangGraph** — 状态图编排，定义节点与条件路由
- **LangChain** — 大模型调用与工具绑定
- **ChatOpenAI (DashScope)** — qwen3.6-plus 模型接口
- **SQLAlchemy** — ORM 数据库操作（auth_system 模块）
- **Pydantic** — 数据验证（auth_system 模块）
