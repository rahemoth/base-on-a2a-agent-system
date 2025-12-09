# 基于A2A协议的多agent协作系统

一个使用**A2A Python SDK**（[a2a-sdk](https://github.com/a2aproject/a2a-python)）构建的复杂多agent协作系统，实现 Google 的 Agent2Agent (A2A) 协议，支持 Model Context Protocol (MCP）。

## 功能

🤖 **多agent系统**
- 创建和管理多个 AI agent
- **使用 A2A SDK 构建 (a2a-sdk v0.3.20+)**
- 符合 A2A 协议
- 支持多种 AI 模型：
  - **Google Gemini**：2.0 Flash、1.5 Pro、1.5 Flash
  - **OpenAI GPT**：GPT-4、GPT-4 Turbo、GPT-4o、GPT-3.5 Turbo
  - **本地大模型**：LM Studio、LocalAI、Ollama 等通过 OpenAI 兼容 API
- 可自定义代理配置
- **每个agent独立 API 密钥配置** - 不同代理使用不同密钥
- **每个agent独立 API 端点配置** 以实现灵活的大模型服务器设置

🤝 **多agent协作**
- **交互式协作界面** 用于协调多个agent
- 通过直观界面选择agent并定义协作任务
- 实时可视化agent讨论和贡献
- 基于轮次的协作，支持配置迭代次数
- 可选择协调者agent来管理协作流程
- 完整的对话历史记录，带时间戳和元数据
- 灵感来源于 CrewAI 的多代理模式和 A2A 协议标准

🔧 **MCP 集成**
- 完整 Model Context Protocol 支持
- 将agent连接到 MCP 服务器
- 访问 MCP 服务器提供的工具和资源
- 无缝工具执行

💬 **代理通信**
- 与单个agent实时聊天
- 符合 A2A 协议的消息传递
- 对话历史跟踪
- 支持流式响应

## 架构

### 后端 (Python/FastAPI)
- **A2A SDK**： Agent2Agent 协议 Python SDK
- **FastAPI**： API 服务器
- **Google GenAI**：Gemini 模型提供商
- **OpenAI**：GPT 模型提供商
- **MCP Client**：Model Context Protocol 集成
- **Pydantic**：数据验证和设置管理

### 前端 (React/Vite)
- **React 18**：现代 UI 库
- **Vite**：快速构建工具和开发服务器
- **Lucide Icons**：图标集
- **Axios**：HTTP  API 通信

## 快速开始

> **注意**: 如果你遇到 agent 无法响应的问题，请查看 [LM Studio 集成修复文档](docs/LM_STUDIO_FIX.md) 了解详情。

### 前置要求
- Python 3.10+
- Node.js 18+
- Google API Key（用于 Gemini 模型）和/或 OpenAI API Key（用于 GPT 模型）

### 安装

1. **克隆仓库**
```bash
git clone <repository-url>
cd base-on-a2a-agent-system
```

2. **设置后端**
```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 创建环境文件
cp .env.example .env
# 编辑 .env 并添加你的 GOOGLE_API_KEY 和/或 OPENAI_API_KEY
```

3. **设置前端**
```bash
cd frontend
npm install
```

### 运行应用

1. **启动后端服务器**
```bash
# 从项目根目录
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

2. **启动前端开发服务器**
```bash
# 从 frontend 目录
cd frontend
npm run dev
```

3. **访问应用**
在浏览器中打开：`http://localhost:5173`

后端 API 文档地址：`http://localhost:8000/docs`

## 使用方法

### 创建agent

1. 在仪表盘点击 "Create Agent" 按钮
2. 填写代理agent：
   - **Name**：给agent起个描述性名字
   - **Description**：描述agent的用途
   - **Provider**：选择 Google (Gemini) 或 OpenAI (GPT)
   - **Model**：从选中提供商中选择模型
   - **API Key** (可选)：为单个agent配置 API 密钥
     - **Google API Key**：用于 Google (Gemini) 提供商
     - **OpenAI API Key**：用于 OpenAI (GPT) 提供商
     - 留空则使用 .env 文件中的全局密钥
     - 单个agent密钥会覆盖全局设置
   - **OpenAI API Base URL** (仅 OpenAI)：配置自定义 API 端点
     - 从常用本地大模型服务器预设中选择 (LM Studio、LocalAI、Ollama 等)
     - 或输入自定义 URL
     - 留空则使用官方 OpenAI API
   - **System Prompt**：定义agent的行为和性格
   - **Temperature**：控制随机性 (0.0 - 2.0)
   - **Max Tokens**：设置输出长度限制 (可选)

3. **添加 MCP 服务器** (可选)：
   - Server Name：MCP 服务器标识符
   - Command：可执行命令 (例如 `npx`、`python`)
   - Args：额外命令参数

4. 点击 "Create Agent"

### 与agent聊天

1. 点击代理卡片上的聊天图标
2. 在输入框中输入你的消息
3. 按回车或点击发送按钮
4. 代理将使用 A2A 协议回复

### 多代理协作

利用多个agent一起解决复杂任务：

**通过界面使用：**
1. 创建至少 2 个具有不同能力的agent
2. 点击仪表盘顶部的 "Collaborate" 按钮
3. 选择要协作的agent
4. 输入任务描述 (越具体越好)
5. 可选选择一个协调agent理 (或让系统自动选择)
6. 设置最大协作轮次
7. 点击 "Start Collaboration"
8. 观看agent们一起工作，每人贡献自己的专业知识
9. 查看完整的对话历史和所有agent的贡献

**通过 API 使用：**

使用 API 端点 `/api/agents/collaborate` 启动多agent协作：

```bash
curl -X POST http://localhost:8000/api/agents/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["agent-id-1", "agent-id-2"],
    "task": "设计一个 Web 应用架构",
    "max_rounds": 5
  }'
```

**协作功能：**
- **符合 A2A 协议**：遵循 Google 的 Agent-to-Agent 协议标准
- **灵活协调**：可选择协调者agent或自动选择
- **基于轮次**：控制agent协作的迭代次数
- **完整历史**：查看带元数据和时间戳的完整对话
- **实时更新**：实时看agent们一起工作

## API 文档

### 代理端点

- `POST /api/agents/` - 创建新agent
- `GET /api/agents/` - 列出所有agent
- `GET /api/agents/{agent_id}` - 获取agent详情
- `PUT /api/agents/{agent_id}` - 更新agent配置
- `DELETE /api/agents/{agent_id}` - 删除agent
- `POST /api/agents/message` - 向agent发送消息
- `POST /api/agents/collaborate` - 启动agent协作

### MCP 端点

- `GET /api/mcp/agents/{agent_id}/tools` - 获取可用工具
- `GET /api/mcp/agents/{agent_id}/resources` - 获取可用资源
- `POST /api/mcp/agents/{agent_id}/tools/{server_name}/{tool_name}` - 调用工具

## 配置

### 环境变量

在根目录创建 `.env` 文件：

```env
# 至少需要其中一个
GOOGLE_API_KEY=你的_google_api_key
OPENAI_API_KEY=你的_openai_api_key

# 可选
ANTHROPIC_API_KEY=你的_anthropic_api_key

# OpenAI 配置 (可选)
# 用于连接 OpenAI 兼容的 API，如 LM Studio、LocalAI 等
# 如果未设置，使用官方 OpenAI API 端点
# 注意：不要包含 /v1 后缀 - OpenAI SDK 会自动添加
OPENAI_BASE_URL=http://localhost:1234

HOST=0.0.0.0
PORT=8000
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./agents.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 使用 OpenAI 兼容 API (LM Studio、LocalAI 等)

系统支持任意 OpenAI 兼容 API 端点，有两种配置方式：

#### 方法 1：逐个agent配置 (推荐)

通过界面直接在agent设置中配置 base URL：

1. **启动本地大模型服务器** (例如 LM Studio、LocalAI)
2. **在仪表盘创建或编辑agent**
3. **选择 "OpenAI (GPT)" 作为提供商**
4. **在 "OpenAI API Base URL" 下拉菜单中选择预设**：
   - LM Studio (默认)：`http://localhost:1234`
   - LocalAI：`http://localhost:8080`
   - Ollama：`http://localhost:11434`
   - Text Generation WebUI：`http://localhost:5000`
   - 或选择 "Custom URL..." 输入自定义地址
   - **注意**：不要在 URL 末尾添加 `/v1` - OpenAI SDK 会自动添加
5. **配置 API 密钥** (本地模型时可填任意字符串)
6. **选择模型** (使用本地服务器支持的模型名称)

此方法允许不同agent使用不同 API 端点。

#### 方法 2：全局环境变量

通过环境变量为所有agent设置默认 base URL：

1. **启动 LM Studio** 并加载模型
2. **在 LM Studio 中启用本地服务器** (通常运行在 `http://localhost:1234`)
3. **配置 .env 文件**：
   ```env
   OPENAI_API_KEY=lm-studio  # 本地模型时可为任意字符串
   OPENAI_BASE_URL=http://localhost:1234
   ```
   **注意**：不要在 URL 末尾添加 `/v1` - OpenAI SDK 会自动添加
4. **创建agent** 时使用 `provider: "openai"` 并选择 LM Studio 支持的模型名称

**注意**：逐个agent配置优先于全局环境变量。

**支持的 OpenAI 兼容平台：**
- LM Studio
- LocalAI
- Ollama (带 OpenAI 兼容层)
- Text Generation WebUI (带 OpenAI 扩展)
- vLLM
- 任何其他实现 OpenAI API 格式的服务

### agent配置结构

```json
{
  "name": "string",
  "description": "string",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "string",
  "temperature": 0.7,
  "max_tokens": null,
  "openai_base_url": "http://localhost:1234",
  "mcp_servers": [
    {
      "name": "string",
      "command": "string",
      "args": [],
      "env": {}
    }
  ],
  "capabilities": [],
  "metadata": {}
}
```

## MCP 集成

系统支持完整的 MCP (Model Context Protocol) 集成。可以将agent连接到 MCP 服务器以提供工具和资源。

### 示例 MCP 服务器配置

```json
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
```

### 可用的 MCP 服务器

- **filesystem**：文件系统操作
- **github**：GitHub API 集成
- **postgres**：PostgreSQL 数据库访问
- **sqlite**：SQLite 数据库访问
- **brave-search**：网页搜索功能
- 以及 MCP 生态中的更多服务器

## 开发

### 项目结构

```
base-on-a2a-agent-system/
├── backend/
│   ├── agents/          # agent实现
│   ├── api/             # FastAPI 路由
│   ├── config/          # 配置
│   ├── mcp/             # MCP 集成
│   ├── models/          # 数据模型
│   └── main.py          # 应用入口
├── frontend/
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API 服务
│   │   └── styles/      # CSS 样式
│   └── package.json
├── requirements.txt
└── README.md
```

### 生产构建

**后端：**
```bash
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**前端：**
```bash
cd frontend
npm run build
```

构建好的前端将位于 `frontend/dist`，后端会自动提供服务。

## 使用技术

- **后端**：Python、FastAPI、**A2A SDK (官方)**、Google GenAI SDK、OpenAI SDK、MCP、SQLAlchemy
- **前端**：React、Vite、Axios、Lucide Icons
- **AI**：Google Gemini 模型、OpenAI GPT 模型
- **协议**：Agent2Agent (A2A) 协议、Model Context Protocol (MCP)

## 贡献

欢迎贡献！请随时提交 Pull Request。

## 许可证

本项目开源，采用 MIT 许可证。

## 故障排除

### Agent 无响应或返回空消息
**问题**: Agent 创建成功但发送消息后没有响应或返回空内容。

**解决方案**: 这通常是因为 LLM 服务未运行或配置不正确。请：
1. 确保 LM Studio/LocalAI 等本地服务正在运行
2. 检查 API 端点配置是否正确（默认 LM Studio: `http://localhost:1234`，不要包含 `/v1`）
3. 查看后端日志中的连接错误
4. 参阅 [LM Studio 集成修复文档](docs/LM_STUDIO_FIX.md)

### 连接错误 (Connection Error)
**问题**: 后端日志显示 "Connection error" 或 "All connection attempts failed"

**解决方案**:
1. 确认 LM Studio 服务器已启动并加载了模型
2. 验证端口是否正确（默认 1234）
3. 检查防火墙设置是否阻止了连接
4. 尝试直接访问 `http://localhost:1234/v1/models` 验证 API 是否可访问
   **注意**：虽然在配置中不包含 `/v1`，但 API 端点本身仍然使用 `/v1` 路径

### 空响应内容 (Empty content in response)
**问题**: API 返回 "Empty content in response" 错误

**解决方案**:
1. 确保在 LM Studio 中加载了模型
2. 检查模型是否正确响应（可以在 LM Studio 中直接测试）
3. 验证模型名称配置是否与 LM Studio 中的模型匹配

详细故障排除指南请参阅 [文档目录](docs/)。

## 支持

如有问题和疑问，请在 GitHub 上开 issue。

## 致谢

- [A2A Project](https://a2a-protocol.org/) - 官方 Agent2Agent 协议
- [A2A Python SDK](https://github.com/a2aproject/a2a-python) - 官方 Python SDK
- Model Context Protocol (MCP) 社区
