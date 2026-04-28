# DevFlow Engine

AI-Driven Development Pipeline Engine - 用 AI 重新定义研发流程

## 功能特性

- **Pipeline 引擎**: 可配置的流水线引擎，支持阶段定义、排序与依赖管理
- **Agent 编排**: 每个流程阶段有对应的 AI Agent，支持多模型切换
- **Human-in-the-Loop**: 人工检查点，支持审批/拒绝/回退
- **代码上下文感知**: 支持代码库上下文理解

## 技术栈

- **Web**: FastAPI + Pydantic v2
- **Agent**: LangChain + SimpleAgent
- **LLM**: LangChain (OpenAI GPT-4, Anthropic Claude, Google Gemini)
- **数据库**: SQLAlchemy 2.0 + SQLite/PostgreSQL

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

编辑 `.env` 文件，填入你的 API Key：

```env
# 选择一个 LLM Provider
DEFAULT_PROVIDER=openai

# OpenAI（GPT-4）
OPENAI_API_KEY=sk-your-openai-key

# 或者使用 Claude
# DEFAULT_PROVIDER=anthropic
# ANTHROPIC_API_KEY=sk-ant-your-key
```

### 3. 启动服务

```bash
# 开发模式（热重载）
uvicorn devflow.api.main:app --reload

# 生产模式
uvicorn devflow.api.main:app --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 项目结构

```
src/devflow/
├── __init__.py
├── api/                        # REST API 层
│   ├── main.py                # FastAPI 应用入口
│   ├── schemas.py             # Pydantic 请求/响应模型
│   ├── service.py             # 业务逻辑服务
│   └── routes/
│       ├── pipeline.py         # Pipeline CRUD API
│       ├── execution.py        # 执行管理 API
│       └── checkpoint.py       # 检查点审批 API
├── agents/                     # Agent 层
│   ├── base.py                # Agent 基类
│   ├── simple_agent.py        # 简单 Agent 实现
│   ├── demand_agent.py        # 需求分析 Agent
│   ├── scheme_agent.py        # 方案设计 Agent
│   ├── code_agent.py          # 代码生成 Agent
│   ├── review_agent.py        # 代码评审 Agent
│   ├── delivery_agent.py      # 交付 Agent
│   └── factory.py             # Agent 工厂
├── core/                       # 核心引擎
│   ├── state.py               # Pipeline State 定义
│   ├── engine.py              # Pipeline 引擎
│   ├── context.py             # 代码上下文构建器
│   └── checkpoint.py          # 检查点管理器
├── llm/                        # LLM Provider 层
│   ├── langchain_llm.py       # LangChain 统一封装
│   └── factory.py             # Provider 工厂
├── models/                     # 数据模型
│   ├── pipeline.py             # Pipeline 定义
│   ├── execution.py           # 执行状态
│   └── agent.py               # Agent 模型
└── utils/                      # 工具模块
    ├── config.py              # 配置管理
    ├── logging.py              # 日志配置
    └── exceptions.py           # 异常定义

tests/                          # 单元测试
examples/
└── demo.py                     # 演示脚本
docs/
└── API.md                      # API 文档
pyproject.toml                   # 项目配置
.env                            # 环境变量（需创建）
.env.example                    # 环境变量模板
```

## 默认 Pipeline 流程

```
需求输入 → 需求分析 → 方案设计 → 代码生成 → 代码评审 → 交付
              ↓           ↓
           (自动)     人工审批
                        ↓
                    (拒绝则回退)
```

## API 使用示例

以下示例展示完整的执行流程。

### QuickStart（同步执行）

使用 `POST /executions/test-run` 接口可以直接同步执行流水线，生成的代码文件会自动写入 `output` 目录：
```
{
  "pipeline_id": "default",
  "demand": "创建一个简单的计算器应用"
}
```
--------------------------------------------

```bash
curl -X POST http://localhost:8000/executions/test-run \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "default",
    "demand": "创建一个简单的计算器应用"
  }'
```

响应示例：

```json
{
  "status": "completed",
  "result": {
    "status": "completed",
    "output": {
      "files_written": [
        "D:/Github/feishu_code/output/calculator/index.html",
        "D:/Github/feishu_code/output/calculator/script.js"
      ],
      "count": 2
    }
  }
}
```

> **注意**: 这个接口是同步的，会等待所有阶段完成后一次性返回。适合快速测试和简单场景。

### 1. 创建执行

```bash
curl -X POST http://localhost:8000/executions \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "default",
    "demand": "我需要一个用户登录功能"
  }'
```

响应示例：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "pipeline_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "pending",
  "current_stage_id": null,
  "created_at": "2026-04-24T10:00:00"
}
```

记录返回的 `id` 作为 `{execution_id}`。

### 2. 轮询执行状态

```bash
# 查看执行状态和进度
curl http://localhost:8000/executions/{execution_id}
```

执行会经历以下状态：
- `pending` → `running` → `waiting_approval` → `running` → `completed`

当到达 checkpoint 阶段（方案设计、代码评审）时，状态会变为 `waiting_approval`。

### 3. 查看待审批的检查点

```bash
# 查看所有待审批的检查点
curl "http://localhost:8000/checkpoints?execution_id={execution_id}"

# 查看检查点汇总信息
curl http://localhost:8000/checkpoints/{execution_id}/summary
```

当 pipeline 运行到 checkpoint 阶段时，`scheme-design` 检查点会出现在待审批列表中。

### 4. 审批检查点

```bash
# 批准检查点，继续执行
curl -X POST http://localhost:8000/checkpoints/{execution_id}/scheme-design/approve \
  -H "Content-Type: application/json" \
  -d '{"comment": "方案通过，继续执行"}'

# 或拒绝检查点，触发回滚
curl -X POST http://localhost:8000/checkpoints/{execution_id}/scheme-design/reject \
  -H "Content-Type: application/json" \
  -d '{"comment": "方案需要调整，请重新设计"}'
```

检查点 `stage_id` 可选值：
| stage_id | 名称 | 说明 |
|----------|------|------|
| `demand-analysis` | 需求分析 | 无需审批 |
| `scheme-design` | 方案设计 | 需要审批 |
| `code-generation` | 代码生成 | 无需审批 |
| `code-review` | 代码评审 | 需要审批 |
| `delivery` | 交付集成 | 无需审批 |

## Swagger 使用指南

访问 `http://localhost:8000/docs` 打开 Swagger UI。

### 完整使用流程

#### 1. 创建执行

1. 展开 **Execution** 分组
2. 点击 `POST /executions` → **Try it out**
3. 输入请求体：

```json
{
  "pipeline_id": "default",
  "demand": "我需要一个用户登录功能"
}
```

4. 点击 **Execute** 执行
5. 复制返回的 `id` 字段

#### 2. 轮询执行状态

1. 点击 `GET /executions/{execution_id}` → **Try it out**
2. 粘贴刚才复制的 `execution_id`
3. 点击 **Execute**
4. 观察返回的 `status` 字段：
   - `pending` → 等待中
   - `running` → 执行中
   - `waiting_approval` → 等待审批
   - `completed` → 已完成
   - `failed` → 失败

#### 3. 审批检查点

当状态变为 `waiting_approval` 时：

1. 展开 **Checkpoint** 分组
2. 点击 `GET /checkpoints` → **Try it out**
3. 输入 `execution_id` 参数
4. 点击 **Execute** 查看待审批的检查点
5. 记录 `items[].stage_id`（如 `scheme-design`）
6. 点击 `POST /checkpoints/{execution_id}/{stage_id}/approve` → **Try it out**
7. 输入 `execution_id` 和 `stage_id`
8. 请求体输入：

```json
{
  "comment": "方案通过，继续执行"
}
```

9. 点击 **Execute** 批准

#### 4. 继续轮询

批准后回到步骤 2，继续轮询执行状态，直到完成。

```bash
# Step 1: 创建执行
EXECUTION_ID=$(curl -s -X POST http://localhost:8000/executions \
  -H "Content-Type: application/json" \
  -d '{"pipeline_id": "default", "demand": "用户登录功能"}' | jq -r '.id')
echo "Execution ID: $EXECUTION_ID"

# Step 2: 等待 pipeline 运行（轮询状态）
while true; do
  STATUS=$(curl -s "http://localhost:8000/executions/$EXECUTION_ID" | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "waiting_approval" ]; then
    echo "Pipeline is waiting for approval!"
    break
  fi
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 3
done

# Step 3: 查看待审批检查点
curl "http://localhost:8000/checkpoints?execution_id=$EXECUTION_ID"

# Step 4: 批准检查点
curl -X POST "http://localhost:8000/checkpoints/$EXECUTION_ID/scheme-design/approve" \
  -H "Content-Type: application/json" \
  -d '{"comment": "通过"}'

# Step 5: 继续轮询直到完成
curl "http://localhost:8000/executions/$EXECUTION_ID"
```

## 开发

```bash
# 代码检查
ruff check src tests

# 类型检查
mypy src

# 运行测试
pytest tests/ -v
```

## License

MIT
