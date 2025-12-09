A2A多智能体协作系统
 
基于官方A2A Python SDK（a2a-sdk）构建的高级多智能体协作系统，实现了谷歌Agent2Agent（A2A）协议，支持模型上下文协议（MCP），并配备美观现代的Web界面。
 
核心功能
 
🤖 多智能体系统
 
- 创建并管理多个AI智能体
- 基于官方A2A SDK（a2a-sdk v0.3.20+） 开发
- 完全兼容A2A协议
- 支持多种AI模型：
- 谷歌Gemini：2.0 Flash、1.5 Pro、1.5 Flash
- OpenAI GPT：GPT-4、GPT-4 Turbo、GPT-4o、GPT-3.5 Turbo
- 本地大语言模型：LM Studio、LocalAI、Ollama，及其他兼容OpenAI API的本地模型
- 可自定义智能体配置
- 支持智能体独立API密钥配置（新增功能）——为每个智能体分配不同API密钥
- 支持智能体独立API端点配置，适配灵活的大语言模型服务器部署需求
 
🤝 多智能体协作（新增功能）
 
- 用于协调多智能体的交互式协作界面
- 通过直观界面选择智能体、定义协作任务
- 实时可视化智能体对话过程与贡献内容
- 支持可配置迭代次数的轮次式协作
- 可选择协调智能体，管理协作流程
- 包含时间戳与元数据的完整对话历史
- 借鉴CrewAI多智能体模式与A2A协议标准设计
 
🔧 MCP协议集成
 
- 完全支持模型上下文协议（MCP）
- 连接智能体与MCP服务器
- 从MCP服务器调用工具与资源
- 工具执行流程无缝衔接
 
💬 智能体通信
 
- 与单个智能体实时聊天
- 符合A2A协议的消息传递机制
- 对话历史跟踪记录
- 支持流式响应输出
 
🎨 美观UI界面
 
- 现代感响应式设计
- 优化长时间使用体验的深色主题
- 直观的智能体管理操作
- 实时状态更新
- 内置热门本地大语言模型服务器预设的LM Studio地址配置功能
 
系统架构
 
后端（Python/FastAPI）
 
- A2A SDK：Agent2Agent协议官方Python开发工具包
- FastAPI：高性能异步API服务器
- Google GenAI：Gemini系列模型服务提供商
- OpenAI：GPT系列模型服务提供商
- MCP Client：模型上下文协议集成组件
- Pydantic：数据验证与配置管理工具
 
前端（React/Vite）
 
- React 18：现代UI开发库
- Vite：快速构建工具与开发服务器
- Lucide Icons：高品质图标集
- Axios：API通信HTTP客户端
 
快速开始
 
前置要求
 
- Python 3.10及以上版本
- Node.js 18及以上版本
- 谷歌API密钥（用于Gemini模型）和/或OpenAI API密钥（用于GPT模型）
 
安装步骤
 
1. 克隆代码仓库
 
bash  
git clone <仓库地址>
cd base-on-a2a-agent-system
 
 
2. 配置后端
 
bash  
# 安装Python依赖包
pip install -r requirements.txt

# 创建环境变量文件
cp .env.example .env
# 编辑.env文件，填入你的GOOGLE_API_KEY和/或OPENAI_API_KEY
 
 
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
# 进入frontend目录执行
cd frontend
npm run dev
 
 
3. 访问应用
打开浏览器，访问地址： http://localhost:5173 
 
后端API文档地址： http://localhost:8000/docs 
 
使用说明
 
创建智能体
 
1. 在控制台点击「创建智能体」按钮
2. 填写智能体配置信息：
- 名称：为智能体设置描述性名称
- 描述：说明智能体的用途
- 服务提供商：选择谷歌（Gemini）或OpenAI（GPT）
- 模型：从所选提供商中挑选模型
- API密钥（可选 - 新增功能）：配置智能体独立API密钥
- 谷歌API密钥：适用于谷歌（Gemini）服务提供商
- OpenAI API密钥：适用于OpenAI（GPT）服务提供商
- 留空则使用.env文件中的全局API密钥
- 智能体独立密钥优先级高于全局设置
- OpenAI API基础地址（仅OpenAI可用）：配置自定义API端点
- 从预设本地大语言模型服务器中选择（LM Studio、LocalAI、Ollama等）
- 或输入任意兼容OpenAI API的自定义地址
- 留空则使用OpenAI官方API
- 系统提示词：定义智能体的行为模式与性格
- 温度值：控制输出随机性（取值范围0.0-2.0）
- 最大令牌数：设置输出长度限制（可选）
3. 添加MCP服务器（可选）：
- 服务器名称：MCP服务器的标识名称
- 命令：可执行命令（如 npx 、 python ）
- 参数：额外命令参数
4. 点击「创建智能体」完成操作
 
与智能体聊天
 
1. 点击智能体卡片上的聊天图标
2. 在输入框中输入消息
3. 按回车键或点击发送按钮
4. 智能体将通过A2A协议返回响应
 
多智能体协作（新增功能）
 
借助多个智能体协同工作，高效完成复杂任务：
 
通过UI操作：
 
1. 创建至少2个具备不同能力或视角的智能体
2. 点击控制台顶部的「协作」按钮
3. 选择参与协作的智能体
4. 输入任务描述（明确说明需完成的目标）
5. 可选：选择协调智能体（或由系统自动选择）
6. 设置最大协作轮次
7. 点击「开始协作」
8. 实时查看智能体协同过程与各自贡献
9. 查看包含所有智能体内容的完整对话历史
 
通过API操作：
调用API接口 /api/agents/collaborate 启动多智能体协作：
 
bash  
curl -X POST http://localhost:8000/api/agents/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "agents": ["agent-id-1", "agent-id-2"],
    "task": "设计一个Web应用架构",
    "max_rounds": 5
  }'
 
 
协作核心功能：
 
- 兼容A2A协议：遵循谷歌Agent-to-Agent协议标准
- 灵活协调机制：可手动选择协调智能体或自动分配
- 轮次式协作：可控制智能体协作迭代次数
- 完整历史记录：查看含元数据与时间戳的全量对话
- 实时更新：实时观察智能体协同过程
 
API文档
 
智能体相关接口
 
-  POST /api/agents/  - 创建新智能体
-  GET /api/agents/  - 查看所有智能体列表
-  GET /api/agents/{agent_id}  - 查看单个智能体详情
-  PUT /api/agents/{agent_id}  - 更新智能体配置
-  DELETE /api/agents/{agent_id}  - 删除智能体
-  POST /api/agents/message  - 向智能体发送消息
-  POST /api/agents/collaborate  - 启动智能体协作
 
MCP相关接口
 
-  GET /api/mcp/agents/{agent_id}/tools  - 查看可用工具
-  GET /api/mcp/agents/{agent_id}/resources  - 查看可用资源
-  POST /api/mcp/agents/{agent_id}/tools/{server_name}/{tool_name}  - 调用工具
 
配置说明
 
环境变量
 
在项目根目录创建.env文件，配置内容如下：
 
env  
# 必填（至少配置一个）
GOOGLE_API_KEY=你的谷歌API密钥
OPENAI_API_KEY=你的OpenAI API密钥

# 可选
ANTHROPIC_API_KEY=你的Anthropic API密钥

# OpenAI配置（可选）
# 用于连接LM Studio、LocalAI等兼容OpenAI API的服务
# 未设置则使用OpenAI官方API端点
OPENAI_BASE_URL=http://localhost:1234/v1

HOST=0.0.0.0
PORT=8000
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./agents.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
 
 
连接兼容OpenAI API的服务（LM Studio、LocalAI等）
 
系统支持两种配置方式，适配任意兼容OpenAI API的端点：
 
方式1：智能体独立配置（推荐）
 
通过UI直接为单个智能体配置基础地址：
 
1. 启动本地大语言模型服务器（如LM Studio、LocalAI）
2. 在控制台创建或编辑智能体
3. 选择「OpenAI（GPT）」作为服务提供商
4. 在「OpenAI API基础地址」下拉框中选择预设选项：
- LM Studio（默认）： http://localhost:1234/v1 
- LocalAI： http://localhost:8080/v1 
- Ollama： http://localhost:11434/v1 
- Text Generation WebUI： http://localhost:5000/v1 
- 或选择「自定义地址...」输入专属地址
5. 配置API密钥（本地模型可填任意字符串）
6. 选择本地服务器支持的模型名称
 
该方式支持不同智能体连接不同API端点。
 
方式2：全局环境变量配置
 
通过环境变量设置所有智能体的默认基础地址：
 
1. 启动LM Studio并加载模型
2. 在LM Studio中启用本地服务器（默认地址 http://localhost:1234 ）
3. 配置.env文件：
env  
OPENAI_API_KEY=lm-studio  # 本地模型可填任意字符串
OPENAI_BASE_URL=http://localhost:1234/v1
 
4. 创建服务提供商为 openai 的智能体，选择本地服务器支持的模型名称
 
注意：智能体独立配置优先级高于全局环境变量配置。
 
支持的兼容OpenAI API的平台：
 
- LM Studio
- LocalAI
- Ollama（需开启OpenAI兼容层）
- Text Generation WebUI（需安装OpenAI扩展）
- vLLM
- 其他所有实现OpenAI API格式的服务
 
智能体配置 schema
 
json  
{
  "name": "字符串",
  "description": "字符串",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "字符串",
  "temperature": 0.7,
  "max_tokens": null,
  "openai_base_url": "http://localhost:1234/v1",
  "mcp_servers": [
    {
      "name": "字符串",
      "command": "字符串",
      "args": [],
      "env": {}
    }
  ],
  "capabilities": [],
  "metadata": {}
}
 
 
MCP协议集成
 
系统完全支持模型上下文协议（MCP），可连接智能体与MCP服务器，为智能体提供工具与资源调用能力。
 
MCP服务器配置示例
 
json  
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
 
 
可用MCP服务器
 
- filesystem：文件系统操作工具
- github：GitHub API集成工具
- postgres：PostgreSQL数据库访问工具
- sqlite：SQLite数据库访问工具
- brave-search：网页搜索工具
- 及MCP生态中的其他各类工具
 
开发说明
 
项目结构
 
plaintext  
base-on-a2a-agent-system/
├── backend/
│   ├── agents/          # 智能体实现代码
│   ├── api/             # FastAPI接口路由
│   ├── config/          # 配置文件
│   ├── mcp/             # MCP协议集成代码
│   ├── models/          # 数据模型
│   └── main.py          # 应用入口文件
├── frontend/
│   ├── src/
│   │   ├── components/  # React组件
│   │   ├── pages/       # 页面组件
│   │   ├── services/    # API服务代码
│   │   └── styles/      # CSS样式文件
│   └── package.json
├── requirements.txt
└── README.md
 
 
生产环境构建
 
后端构建：
 
bash  
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
 
 
前端构建：
 
bash  
cd frontend
npm run build
 
 
构建后的前端文件位于 frontend/dist 目录，可由后端自动托管。
 
所用技术栈
 
- 后端：Python、FastAPI、A2A SDK（官方）、Google GenAI SDK、OpenAI SDK、MCP协议、SQLAlchemy
- 前端：React、Vite、Axios、Lucide Icons
- AI模型：谷歌Gemini系列、OpenAI GPT系列
- 协议标准：Agent2Agent（A2A）协议、模型上下文协议（MCP）
 
贡献指南
 
欢迎各类贡献！请直接提交Pull Request即可参与项目优化。
 
开源协议
 
本项目开源，遵循MIT许可协议。
 
支持说明
 
如有问题或疑问，请在GitHub上提交issue反馈。
 
致谢
 
- A2A项目 - 官方Agent2Agent协议
- A2A Python SDK - 官方Python开发工具包
- 模型上下文协议（MCP）社区
- FastAPI框架开发团队
- React与Vite开发团队