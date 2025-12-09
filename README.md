A2A 多智能体协作系统
 
一个基于 官方 A2A Python SDK (a2a-sdk) 构建的高级多智能体协作系统，实现了谷歌的 Agent2Agent (A2A) 协议，支持模型上下文协议 (MCP)，并配备美观、现代的 Web 界面。
 
功能特性
 
🤖 多智能体系统
 
- 创建和管理多个 AI 智能体
- 基于官方 A2A SDK (a2a-sdk v0.3.20+) 构建
- 完全兼容 A2A 协议
- 支持多种 AI 模型：
- Google Gemini：2.0 Flash、1.5 Pro、1.5 Flash
- OpenAI GPT：GPT-4、GPT-4 Turbo、GPT-4o、GPT-3.5 Turbo
- 本地大语言模型：LM Studio、LocalAI、Ollama，及更多兼容 OpenAI API 的本地模型
- 可自定义智能体配置
- 智能体独立 API 密钥配置（新增功能！） - 为每个智能体分配不同 API 密钥
- 智能体独立 API 端点配置，适配灵活的大语言模型服务器部署
 
🤝 多智能体协作（新增功能！）
 
- 用于协调多个智能体的 交互式协作界面
- 通过直观界面选择智能体并定义协作任务
- 实时可视化智能体对话过程与贡献内容
- 支持可配置迭代次数的轮次式协作
- 可选择协调智能体，管理协作流程
- 包含时间戳和元数据的完整对话历史
- 借鉴 CrewAI 多智能体模式与 A2A 协议标准设计
 
🔧 MCP 集成
 
- 完全支持模型上下文协议 (MCP)
- 连接智能体与 MCP 服务器
- 从 MCP 服务器访问工具和资源
- 工具执行无缝衔接
 
💬 智能体通信
 
- 与单个智能体实时聊天
- 符合 A2A 协议的消息传递
- 对话历史跟踪
- 支持流式响应
 
🎨 美观 UI 界面
 
- 现代、响应式设计
- 优化长时间使用体验的深色主题
- 直观的智能体管理操作
- 实时状态更新
- 内置热门本地大语言模型服务器预设的 LM Studio 地址配置
 
系统架构
 
后端（Python/FastAPI）
 
- A2A SDK：Agent2Agent 协议官方 Python SDK
- FastAPI：高性能异步 API 服务器
- Google GenAI：Gemini 系列模型服务提供商
- OpenAI：GPT 系列模型服务提供商
- MCP Client：模型上下文协议集成组件
- Pydantic：数据验证与配置管理
 
前端（React/Vite）
 
- React 18：现代 UI 开发库
- Vite：快速构建工具与开发服务器
- Lucide Icons：高品质图标集
- Axios：API 通信 HTTP 客户端
 
快速开始
 
前置要求
 
- Python 3.10+
- Node.js 18+
- Google API 密钥（用于 Gemini 模型）和/或 OpenAI API 密钥（用于 GPT 模型）
 
安装步骤
 
1. 克隆代码仓库
 
bash  
git clone <repository-url>
cd base-on-a2a-agent-system
 
 
2. 配置后端
 
bash  
# 安装 Python 依赖包
pip install -r requirements.txt

# 创建环境变量文件
cp .env.example .env
# 编辑 .env 文件，填入你的 GOOGLE_API_KEY 和/或 OPENAI_API_KEY
 
 
3. 配置前端
 
bash  
cd frontend
npm install
 
 
运行应用
 
1. 启动后端服务器
 
bash  
# 在项目根目录执行
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
 
 
2. 启动前端开发服务器
 
bash  
# 进入 frontend 目录执行
cd frontend
npm run dev
 
 
3. 访问应用
打开浏览器，访问地址： http://localhost:5173 
 
后端 API 文档地址： http://localhost:8000/docs 
 
使用说明
 
创建智能体
 
1. 在控制台点击 "Create Agent" 按钮
2. 填写智能体配置信息：
- Name：为智能体设置描述性名称
- Description：说明智能体的用途
- Provider：选择 Google（Gemini）或 OpenAI（GPT）
- Model：从所选提供商中挑选模型
- API Key（可选 - 新增功能！）：配置智能体独立 API 密钥
- Google API Key：适用于 Google（Gemini）提供商
- OpenAI API Key：适用于 OpenAI（GPT）提供商
- 留空则使用  .env  文件中的全局 API 密钥
- 智能体独立密钥优先级高于全局设置
- OpenAI API Base URL（仅 OpenAI 可用）：配置自定义 API 端点
- 从预设本地大语言模型服务器中选择（LM Studio、LocalAI、Ollama 等）
- 或输入任意兼容 OpenAI API 的自定义地址
- 留空则使用 OpenAI 官方 API
- System Prompt：定义智能体的行为模式与性格
- Temperature：控制输出随机性（0.0 - 2.0）
- Max Tokens：设置输出长度限制（可选）
3. 添加 MCP 服务器（可选）：
- Server Name：MCP 服务器的标识名称
- Command：可执行命令（如  npx 、 python ）
- Args：额外命令参数
4. 点击 "Create Agent" 完成创建
 
与智能体聊天
 
1. 点击智能体卡片上的聊天图标
2. 在输入框中输入消息
3. 按回车键或点击发送按钮
4. 智能体将通过 A2A 协议返回响应
 
多智能体协作（新增功能！）
 
借助多个智能体协同工作，高效完成复杂任务：
 
通过 UI 操作：
 
1. 创建至少 2 个具备不同能力或视角的智能体
2. 点击控制台顶部的 "Collaborate" 按钮
3. 选择参与协作的智能体
4. 输入任务描述（明确说明需完成的目标）
5. 可选：选择协调智能体（或由系统自动选择）
6. 设置最大协作轮次
7. 点击 "Start Collaboration"
8. 实时查看智能体协同过程，各智能体发挥专业优势贡献内容
9. 查看包含所有智能体贡献的完整对话历史
 
通过 API 操作：
 
调用 API 端点  /api/agents/collaborate  启动多智能体协作：
 
bash  
curl -X POST http://localhost:8000/api/agents/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["agent-id-1", "agent-id-2"],
    "task": "Design a web application architecture",
    "max_rounds": 5
  }'
 
 
协作核心功能：
 
- 兼容 A2A 协议：遵循谷歌 Agent-to-Agent 协议标准
- 灵活协调机制：可手动选择协调智能体或自动分配
- 轮次式协作：可控制智能体协作迭代次数
- 完整历史记录：查看含元数据与时间戳的全量对话
- 实时更新：实时观察智能体协同过程
 
API 文档
 
智能体相关端点
 
-  POST /api/agents/  - 创建新智能体
-  GET /api/agents/  - 查看所有智能体列表
-  GET /api/agents/{agent_id}  - 查看单个智能体详情
-  PUT /api/agents/{agent_id}  - 更新智能体配置
-  DELETE /api/agents/{agent_id}  - 删除智能体
-  POST /api/agents/message  - 向智能体发送消息
-  POST /api/agents/collaborate  - 启动智能体协作
 
MCP 相关端点
 
-  GET /api/mcp/agents/{agent_id}/tools  - 查看可用工具
-  GET /api/mcp/agents/{agent_id}/resources  - 查看可用资源
-  POST /api/mcp/agents/{agent_id}/tools/{server_name}/{tool_name}  - 调用工具
 
配置说明
 
环境变量
 
在项目根目录创建  .env  文件，配置内容如下：
 
env  
# 必填（至少配置一个）
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# 可选
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpenAI 配置（可选）
# 用于连接 LM Studio、LocalAI 等兼容 OpenAI API 的服务
# 未设置则使用 OpenAI 官方 API 端点
OPENAI_BASE_URL=http://localhost:1234/v1

HOST=0.0.0.0
PORT=8000
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./agents.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
 
 
连接兼容 OpenAI API 的服务（LM Studio、LocalAI 等）
 
系统支持两种配置方式，适配任意兼容 OpenAI API 的端点：
 
方式 1：智能体独立配置（推荐）
 
通过 UI 直接为单个智能体配置基础地址：
 
1. 启动本地大语言模型服务器（如 LM Studio、LocalAI）
2. 在控制台创建或编辑智能体
3. 选择 "OpenAI (GPT)" 作为服务提供商
4. 从 "OpenAI API Base URL" 下拉框中选择预设选项：
- LM Studio（默认）： http://localhost:1234/v1 
- LocalAI： http://localhost:8080/v1 
- Ollama： http://localhost:11434/v1 
- Text Generation WebUI： http://localhost:5000/v1 
- 或选择 "Custom URL..." 输入专属地址
5. 配置 API 密钥（本地模型可填任意字符串）
6. 选择本地服务器支持的模型名称
 
该方式支持不同智能体连接不同 API 端点。
 
方式 2：全局环境变量配置
 
通过环境变量设置所有智能体的默认基础地址：
 
1. 启动 LM Studio 并加载模型
2. 在 LM Studio 中启用本地服务器（通常运行在  http://localhost:1234 ）
3. 配置 .env 文件：
env  
OPENAI_API_KEY=lm-studio  # 本地模型可填任意字符串
OPENAI_BASE_URL=http://localhost:1234/v1
 
4. 创建服务提供商为 "openai" 的智能体，选择本地服务器支持的模型名称
 
注意：智能体独立配置优先级高于全局环境变量配置。
 
支持的兼容 OpenAI API 的平台：
 
- LM Studio
- LocalAI
- Ollama（需开启 OpenAI 兼容层）
- Text Generation WebUI（需安装 OpenAI 扩展）
- vLLM
- 其他所有实现 OpenAI API 格式的服务
 
智能体配置 Schema
 
json  
{
  "name": "string",
  "description": "string",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "string",
  "temperature": 0.7,
  "max_tokens": null,
  "openai_base_url": "http://localhost:1234/v1",
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
 
 
MCP 集成
 
系统完全支持模型上下文协议 (MCP)，可连接智能体与 MCP 服务器，为智能体提供工具和资源调用能力。
 
MCP 服务器配置示例
 
json  
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
 
 
可用 MCP 服务器
 
- filesystem：文件系统操作工具
- github：GitHub API 集成工具
- postgres：PostgreSQL 数据库访问工具
- sqlite：SQLite 数据库访问工具
- brave-search：网页搜索工具
- 及 MCP 生态中的其他各类工具
 
开发说明
 
项目结构
 
plaintext  
base-on-a2a-agent-system/
├── backend/
│   ├── agents/          # 智能体实现代码
│   ├── api/             # FastAPI 接口路由
│   ├── config/          # 配置文件
│   ├── mcp/             # MCP 协议集成代码
│   ├── models/          # 数据模型
│   └── main.py          # 应用入口文件
├── frontend/
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API 服务代码
│   │   └── styles/      # CSS 样式文件
│   └── package.json
├── requirements.txt
└── README.md
 
 
生产环境构建
 
后端：
 
bash  
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
 
 
前端：
 
bash  
cd frontend
npm run build
 
 
构建后的前端文件位于  frontend/dist  目录，可由后端自动托管。
 
所用技术栈
 
- 后端：Python、FastAPI、A2A SDK（官方）、Google GenAI SDK、OpenAI SDK、MCP、SQLAlchemy
- 前端：React、Vite、Axios、Lucide Icons
- AI 模型：Google Gemini 系列、OpenAI GPT 系列
- 协议标准：Agent2Agent (A2A) Protocol、Model Context Protocol (MCP)
 
贡献指南
 
欢迎各类贡献！请直接提交 Pull Request 即可参与项目优化。
 
开源协议
 
本项目开源，遵循 MIT 许可协议。
 
支持说明
 
如有问题或疑问，请在 GitHub 上提交 issue 反馈。
 
致谢
 
- A2A Project - 官方 Agent2Agent 协议
- A2A Python SDK - 官方 Python SDK
- Model Context Protocol (MCP) 社区
- FastAPI 框架开发团队
- React 与 Vite 开发团队