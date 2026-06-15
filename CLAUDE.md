# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基于 A2A (Agent-to-Agent) 协议的多 agent 协作系统，集成 MCP (Model Context Protocol) 和 RAG 记忆系统。前后端分离架构，UI 和 README 主要使用中文。

## Common Commands

### 后端 (Python)
```bash
# 启动后端服务器 (端口 8000)
python run_backend.py

# 直接使用 uvicorn 启动 (支持热重载)
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 安装 Python 依赖
pip install -r requirements.txt

# 运行所有测试
pytest tests/ -v

# 运行单个测试文件
pytest tests/test_rag_memory_system.py -v

# 运行异步测试
pytest tests/ -v --asyncio-mode=auto
```

### 前端 (React/Vite)
```bash
cd frontend

# 开发服务器 (端口 5173，自动代理 /api 到 localhost:8000)
npm run dev

# 生产构建 (输出到 frontend/dist，后端自动托管)
npm run build

# 预览生产构建
npm run preview
```

### 环境配置
```bash
cp .env.example .env  # 然后填写 API keys
```
关键环境变量见 `.env.example` 和 `backend/config/settings.py`。

## Architecture

### 整体结构
- **backend/** — FastAPI 应用，所有 agent 逻辑、RAG、MCP 在此
- **frontend/** — React SPA (JSX, 无 TypeScript)，单页面 Dashboard + 模态框交互
- **data/** — SQLite 数据库文件 (agents.db, agent_memory.db)
- **tests/** — pytest 测试 (无 conftest.py，默认配置发现)
- **docs/** — 详细文档 (中文为主)

### 后端核心模块
```
backend/
  main.py                 — FastAPI 入口，lifespan 管理，CORS，静态文件托管
  config/settings.py      — pydantic-settings 配置，从 .env 加载 API keys 和服务参数
  database_manager.py     — SQLAlchemy async + aiosqlite，两个表: agents, conversations
  models/
    database.py           — ORM 模型 (Agent, Conversation)
    schemas.py            — Pydantic schemas (AgentConfig, ModelProvider enum 等)
  api/
    agents_a2a.py         — 主路由 /api/agents/ (CRUD, 消息, 协作, A2A JSON-RPC)
    agent_capabilities.py — 能力/记忆/认知/工具端点
    mcp.py                — /api/mcp/ MCP 工具和资源
    rag.py                — /api/rag/ RAG 记忆系统
    agents.py             — 旧版 agent 路由 (向后兼容)
  agents/
    a2a_manager.py        — Agent 生命周期管理器，多 agent 协作编排 (核心)
    a2a_executor.py       — A2A 任务执行器 (最大文件 51KB)
    a2a_agent.py          — A2A agent 实现
    cognitive.py          — 认知状态管理
    memory.py             — Agent 记忆系统
    tools.py              — 工具管理
    rag_*.py              — RAG 子系统 (向量索引/HNSW, 记忆图, 混合检索, 对话压缩, 一致性管理)
  mcp/client.py           — MCP 客户端，连接外部 MCP 服务器
```

### 前端结构
```
frontend/src/
  main.jsx / App.jsx      — 入口，渲染 Dashboard
  pages/Dashboard.jsx     — 唯一页面：agent 列表/CRUD/聊天/协作/洞察
  components/
    AgentConfigModal.jsx  — Agent 创建/编辑表单 (最大组件 33KB)
    ChatModal.jsx         — 实时聊天界面 (SSE 流式)
    CollaborationModal.jsx — 多 agent 协作设置
    AgentInsightsModal.jsx — 认知/记忆洞察查看
    CustomToolModal.jsx   — 自定义工具定义
  services/
    api.js                — 集中 API 客户端 (agentService, mcpService, memoryService, cognitiveService, toolsService)
    storage.js            — localStorage 持久化自定义工具
```

### 关键架构决策
- **前后端分离**：开发时 Vite 代理 /api 到后端；生产时后端直接托管 frontend/dist 静态文件
- **多 LLM 提供商**：每个 agent 可独立配置 API key 和端点 (支持 DeepSeek/Gemini/GPT/Claude/Kimi/MiMo/MiniMax/GLM/Qwen/自定义 OpenAI 兼容)
- **A2A 协议合规**：JSON-RPC 端点、agent card (`/.well-known/agent-card.json`)、task 管理
- **RAG 子系统**：自定义向量索引 (HNSW) + 记忆图 (beam search) + 混合检索 + 对话压缩，使用 numpy/scipy
- **无 TypeScript**：前端纯 JSX；后端 Pydantic 提供类型安全
- **数据库**：SQLite 文件存储在 data/ 目录，启动时自动创建

## Key API Routes

| 路径 | 说明 |
|------|------|
| `/api/agents/` | Agent CRUD |
| `/api/agents/message` | 发送消息给 agent |
| `/api/agents/collaborate` | 多 agent 协作 (支持 SSE 流式) |
| `/api/agents/test-connection` | 测试模型 API 连通性 |
| `/api/agents/{id}/a2a` | A2A JSON-RPC (sendMessage, getTask, cancelTask) |
| `/api/agents/{id}/memory/*` | Agent 记忆端点 |
| `/api/agents/{id}/cognitive/*` | 认知状态端点 |
| `/api/mcp/agents/{id}/tools` | MCP 工具列表 |
| `/api/rag/*` | RAG 系统 (compress, query, add, stats) |
| `/health` | 健康检查 |
