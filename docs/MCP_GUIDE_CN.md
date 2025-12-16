# MCP 集成指南（中文版）

本指南详细说明如何在A2A Agent系统中配置和使用 Model Context Protocol (MCP) 服务器。

## 目录

1. [什么是 MCP？](#什么是-mcp)
2. [MCP 服务器配置](#mcp-服务器配置)
3. [Agent 如何调用 MCP 服务](#agent-如何调用-mcp-服务)
4. [常见 MCP 服务器配置示例](#常见-mcp-服务器配置示例)
5. [技术实现原理](#技术实现原理)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)

---

## 什么是 MCP？

Model Context Protocol (MCP) 是一个开放协议，使 AI 应用能够安全地连接到外部数据源和工具。MCP 服务器可以提供：

- **工具 (Tools)**：Agent 可以调用的功能函数
- **资源 (Resources)**：Agent 可以访问的数据源
- **提示 (Prompts)**：预定义的提示模板

在本系统中，MCP 让您的 Agent 能够：
- 访问文件系统
- 查询数据库
- 调用 GitHub API
- 进行网络搜索
- 执行浏览器自动化
- 以及更多自定义功能...

---

## MCP 服务器配置

### 配置格式

在创建或更新 Agent 时，通过 `mcp_servers` 字段配置 MCP 服务器：

```json
{
  "name": "服务器名称",
  "command": "可执行命令",
  "args": ["参数1", "参数2", "..."],
  "env": {
    "环境变量名": "环境变量值"
  }
}
```

### 配置说明

- **name**：服务器的唯一标识符，用于在系统中引用该服务器
- **command**：启动 MCP 服务器的命令（如 `npx`、`python`、`node` 等）
- **args**：传递给命令的参数列表
- **env**：环境变量字典，用于传递 API 密钥等敏感信息

### 在前端界面配置

1. 在创建或编辑 Agent 时，找到 "MCP 服务器" 部分
2. 点击 "添加 MCP 服务器" 按钮
3. 填写以下信息：
   - **服务器名称**：服务器的唯一标识（如 `filesystem`、`github`、`brave_search` 等）
   - **命令**：启动服务器的命令（如 `npx`、`python`、`node` 等）
   - **参数**：命令的参数列表，每行一个参数（例如 `-y` 和 `@modelcontextprotocol/server-filesystem` 各占一行）
   - **环境变量**：使用 `KEY=VALUE` 格式，每行一个（用于传递 API 密钥等敏感信息）
4. 点击 "添加 MCP 服务器" 保存配置

**配置示例**（以网络搜索为例）：
- 服务器名称: `brave_search`
- 命令: `npx`
- 参数（每行一个）:
  ```
  -y
  @modelcontextprotocol/server-brave-search
  ```
- 环境变量（每行一个）:
  ```
  BRAVE_API_KEY=你的_api_key
  ```

### 通过 API 配置

发送 POST 请求到 `/api/agents/`：

```bash
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "name": "研究助手",
      "description": "具有网络搜索能力的研究助手",
      "provider": "google",
      "model": "gemini-2.0-flash-exp",
      "system_prompt": "你是一个研究助手，可以使用网络搜索工具。",
      "mcp_servers": [
        {
          "name": "brave_search",
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-brave-search"],
          "env": {
            "BRAVE_API_KEY": "你的_brave_api_key"
          }
        }
      ]
    }
  }'
```

---

## Agent 如何调用 MCP 服务

### 自动工具调用

当您与 Agent 对话时，Agent 会**自动判断**何时需要使用 MCP 工具。您无需手动指定工具调用。

**工作流程：**

1. **用户发送消息**：您向 Agent 提问或发出指令
2. **Agent 分析请求**：Agent 的 LLM 模型分析您的请求，判断是否需要使用工具
3. **工具发现**：Agent 查看其可用的 MCP 工具列表
4. **工具选择**：Agent 选择最合适的工具来完成任务
5. **工具执行**：Agent 调用 MCP 服务器上的工具
6. **结果整合**：Agent 将工具返回的结果整合到回复中
7. **返回响应**：Agent 向用户返回完整的回答

### 示例对话

```
用户: "搜索量子计算的最新进展"

Agent 内部过程:
1. 识别需要网络搜索
2. 发现可用的 brave_search 工具
3. 调用 brave_web_search(query="量子计算最新进展")
4. 获取搜索结果
5. 分析和总结搜索结果

Agent 回复: "根据最新的搜索结果，量子计算领域有以下重要进展..."
```

### 查看可用工具

#### 在聊天界面中查看

当您与 Agent 聊天时，可以点击聊天窗口右上角的 **工具图标** (🔧) 来查看该 Agent 可用的所有工具：

1. 打开与 Agent 的聊天窗口
2. 点击右上角的工具图标
3. 工具面板将显示：
   - 所有 MCP 服务器及其提供的工具
   - 内置工具列表
   - 每个工具的名称和描述

**Agent 会自动知道这些工具的存在**：在对话开始时，Agent 会收到一条系统消息，告知其可用的工具列表，使其能够智能地选择和使用合适的工具。

#### 通过 API 查看

使用 API 查看 Agent 的可用工具：

```bash
curl http://localhost:8000/api/mcp/agents/{agent_id}/tools
```

响应示例：

```json
{
  "tools": {
    "brave_search": [
      {
        "name": "brave_web_search",
        "description": "使用 Brave Search 进行网络搜索",
        "input_schema": {
          "type": "object",
          "properties": {
            "query": {
              "type": "string",
              "description": "搜索查询"
            }
          }
        }
      }
    ]
  }
}
```

### 手动调用工具（可选）

虽然通常不需要，但您也可以手动调用 MCP 工具：

```bash
curl -X POST http://localhost:8000/api/mcp/agents/{agent_id}/tools/brave_search/brave_web_search \
  -H "Content-Type: application/json" \
  -d '{"query": "量子计算 2024"}'
```

---

## 常见 MCP 服务器配置示例

### 1. 文件系统访问（Filesystem Server）

允许 Agent 读取和操作本地文件。

```json
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"],
  "env": {}
}
```

**使用场景**：
- 读取项目文档
- 分析代码文件
- 处理本地数据文件

**注意**：出于安全考虑，只授予必要目录的访问权限。

### 2. GitHub 集成（GitHub Server）

与 GitHub 仓库交互。

```json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_你的_token"
  }
}
```

**使用场景**：
- 查看仓库信息
- 读取 issues 和 PRs
- 分析代码变更
- 创建和更新 issues

**获取 Token**：在 GitHub Settings → Developer settings → Personal access tokens 创建。

### 3. PostgreSQL 数据库（PostgreSQL Server）

查询 PostgreSQL 数据库。

```json
{
  "name": "postgres",
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-postgres",
    "postgresql://username:password@localhost:5432/database"
  ],
  "env": {}
}
```

**使用场景**：
- 数据分析
- 生成报告
- 查询业务数据

**安全提示**：建议使用只读数据库用户。

### 4. SQLite 数据库（SQLite Server）

访问 SQLite 数据库文件。

```json
{
  "name": "sqlite",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-sqlite", "/path/to/database.db"],
  "env": {}
}
```

**使用场景**：
- 本地数据分析
- 小型数据库查询
- 配置数据读取

### 5. 网络搜索（Brave Search Server）

提供网络搜索能力。

```json
{
  "name": "brave_search",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": {
    "BRAVE_API_KEY": "BSA_你的_api_key"
  }
}
```

**使用场景**：
- 实时信息检索
- 研究和调查
- 市场分析

**获取 API Key**：在 [Brave Search API](https://brave.com/search/api/) 注册。

### 6. 浏览器自动化（Puppeteer Server）

执行网页抓取和浏览器操作。

```json
{
  "name": "puppeteer",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
  "env": {}
}
```

**使用场景**：
- 网页内容抓取
- 截图和 PDF 生成
- 自动化测试

### 7. 多服务器配置示例

一个 Agent 可以同时配置多个 MCP 服务器：

```json
{
  "name": "全能助手",
  "description": "具有多种工具的全能助手",
  "provider": "google",
  "model": "gemini-2.0-flash-exp",
  "system_prompt": "你是一个全能助手，可以访问文件系统、搜索网络和查询 GitHub。",
  "mcp_servers": [
    {
      "name": "filesystem",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/workspace"],
      "env": {}
    },
    {
      "name": "brave_search",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "你的_api_key"
      }
    },
    {
      "name": "github",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "你的_token"
      }
    }
  ]
}
```

---

## 技术实现原理

### 系统架构

```
┌─────────────┐
│   用户界面   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────┐
│           FastAPI 后端服务                       │
│  ┌────────────────────────────────────────┐    │
│  │      A2A Agent Manager                  │    │
│  │  ┌──────────────────────────────────┐  │    │
│  │  │   LLM Agent Executor              │  │    │
│  │  │  ┌────────────────────────────┐  │  │    │
│  │  │  │  Enhanced Tool Manager     │  │  │    │
│  │  │  │  - 工具发现                 │  │  │    │
│  │  │  │  - 工具执行跟踪             │  │  │    │
│  │  │  │  - 结果缓存                 │  │  │    │
│  │  │  └────────┬───────────────────┘  │  │    │
│  │  │           │                       │  │    │
│  │  │           ▼                       │  │    │
│  │  │  ┌────────────────────────────┐  │  │    │
│  │  │  │    MCP Client              │  │  │    │
│  │  │  └────────┬───────────────────┘  │  │    │
│  │  └───────────┼───────────────────────┘  │    │
│  └──────────────┼──────────────────────────┘    │
└─────────────────┼─────────────────────────────┘
                  │
                  ▼
      ┌───────────────────────┐
      │   MCP 服务器实例       │
      ├───────────────────────┤
      │  • Filesystem Server  │
      │  • GitHub Server      │
      │  • Database Servers   │
      │  • Search Servers     │
      │  • Custom Servers     │
      └───────────────────────┘
```

### 代码执行流程

#### 1. Agent 创建时的 MCP 初始化

位置：`backend/agents/a2a_executor.py` 中的 `initialize_mcp()` 方法

```python
async def initialize_mcp(self):
    """初始化 MCP 服务器和内存系统"""
    # 初始化内存数据库
    await self.memory.initialize()
    
    # 如果配置了 MCP 服务器，则初始化
    if self.config.mcp_servers:
        # 为此 Agent 创建 MCP 客户端
        self.mcp_client = await mcp_manager.create_client(self.agent_id)
        
        # 连接每个配置的 MCP 服务器
        for mcp_config in self.config.mcp_servers:
            await self.mcp_client.connect_server(
                name=mcp_config.name,
                command=mcp_config.command,
                args=mcp_config.args,
                env=mcp_config.env
            )
    
    # 初始化增强工具管理器
    self.tool_manager = EnhancedToolManager(
        agent_id=self.agent_id,
        mcp_client=self.mcp_client
    )
    
    # 发现可用工具
    await self.tool_manager.discover_tools()
```

**关键点**：
- 每个 Agent 都有独立的 MCP 客户端
- MCP 服务器在 Agent 创建时自动启动
- 工具列表在初始化时自动发现

#### 2. MCP 客户端连接服务器

位置：`backend/mcp/client.py` 中的 `connect_server()` 方法

```python
async def connect_server(self, name: str, command: str, args: List[str] = None, env: Dict[str, str] = None):
    """连接到 MCP 服务器"""
    # 创建服务器参数
    server_params = StdioServerParameters(
        command=command,  # 例如: "npx"
        args=args,        # 例如: ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
        env=env           # 例如: {"API_KEY": "xxx"}
    )
    
    # 启动服务器进程（通过标准输入输出通信）
    stdio_transport = await self.exit_stack.enter_async_context(
        stdio_client(server_params)
    )
    stdio, write = stdio_transport
    
    # 创建客户端会话
    session = await self.exit_stack.enter_async_context(
        ClientSession(stdio, write)
    )
    
    # 初始化会话
    await session.initialize()
    
    # 保存会话以供后续使用
    self.sessions[name] = session
```

**关键点**：
- 使用 stdio（标准输入输出）与 MCP 服务器通信
- 每个服务器一个独立的会话
- 支持环境变量传递（用于 API 密钥等）

#### 3. 工具发现

位置：`backend/agents/tools.py` 中的 `discover_tools()` 方法

```python
async def discover_tools(self) -> List[ToolCapability]:
    """从 MCP 服务器发现所有可用工具"""
    if not self.mcp_client:
        return list(self.tools.values())
    
    # 从所有 MCP 服务器获取工具列表
    mcp_tools = await self.mcp_client.list_tools()
    
    # 注册每个工具
    for server_name, server_tools in mcp_tools.items():
        for tool in server_tools:
            tool_name = f"{server_name}_{tool['name']}"
            
            self.tools[tool_name] = ToolCapability(
                name=tool_name,
                description=tool.get('description', ''),
                category=server_name,
                parameters=tool.get('input_schema', {}),
                server_name=server_name,
                is_builtin=False
            )
```

**关键点**：
- 工具名称格式：`{服务器名}_{工具名}`
- 例如：`brave_search_brave_web_search`
- 工具描述和参数从 MCP 服务器自动获取

#### 4. Agent 执行工具调用

当 Agent 的 LLM 决定调用工具时，系统会：

1. **解析工具调用请求**：从 LLM 响应中提取工具名称和参数
2. **查找对应的 MCP 服务器**：根据工具名称找到对应的服务器
3. **调用 MCP 工具**：通过 MCP 客户端发送工具调用请求
4. **等待结果**：接收 MCP 服务器返回的结果
5. **记录执行**：记录工具调用的统计信息
6. **缓存结果**（如果适用）：缓存结果以提高性能
7. **返回给 LLM**：将结果传回 LLM 继续处理

位置：`backend/mcp/client.py` 中的 `call_tool()` 方法

```python
async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
    """在 MCP 服务器上调用工具"""
    if server_name not in self.sessions:
        raise ValueError(f"服务器 {server_name} 未连接")
    
    # 调用工具并获取结果
    result = await self.sessions[server_name].call_tool(tool_name, arguments)
    return result
```

### 工具执行跟踪和缓存

系统还包含高级功能：

- **执行跟踪**：记录每次工具调用的统计信息
- **结果缓存**：缓存工具结果以避免重复调用
- **性能监控**：跟踪工具调用的成功率和执行时间

---

## 最佳实践

### 1. 安全性

**永远不要将 API 密钥提交到版本控制**

❌ 错误做法：
```json
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxxxxxxxxx"
  }
}
```

✅ 正确做法：
- 使用环境变量
- 将密钥存储在 `.env` 文件中
- 在前端界面通过安全输入框输入

**限制文件系统访问**

❌ 错误：
```json
{
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"]
}
```

✅ 正确：
```json
{
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/safe-directory"]
}
```

**使用只读数据库连接**

对于数据库 MCP 服务器，使用只读用户：
```sql
CREATE USER readonly_user WITH PASSWORD 'password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

### 2. 性能优化

**限制每个 Agent 的 MCP 服务器数量**

推荐：3-5 个服务器
- 太多会增加初始化时间
- 太多工具可能会混淆 Agent

**使用工具类别进行组织**

将相关工具分组在同一个服务器中，而不是为每个功能创建单独的服务器。

### 3. 可维护性

**为服务器使用描述性名称**

✅ 好的命名：
```json
{"name": "github_repos"}
{"name": "company_database"}
{"name": "web_search"}
```

❌ 不好的命名：
```json
{"name": "server1"}
{"name": "mcp"}
{"name": "test"}
```

**在 Agent 的 system_prompt 中说明可用工具**

```
你是一个研究助手。你有以下工具：
1. web_search - 用于搜索最新信息
2. github - 用于访问代码仓库
3. filesystem - 用于读取本地文档

在需要时使用这些工具来帮助用户。
```

### 4. 错误处理

**MCP 服务器可能会失败**

- Agent 会继续运行，即使某些 MCP 服务器无法连接
- 检查后端日志以诊断连接问题
- 在部署到生产环境前测试 MCP 服务器

---

## 故障排除

### 问题 1：MCP 服务器无法连接

**症状**：Agent 创建成功，但工具列表为空或 Agent 不使用工具

**排查步骤**：

1. **检查命令是否安装**

```bash
# 对于 npx 服务器
npx -y @modelcontextprotocol/server-filesystem --help

# 对于 Python 服务器
python -c "import mcp; print(mcp.__version__)"
```

2. **验证环境变量**

确保在配置中正确设置了所需的环境变量（如 API 密钥）。

3. **查看后端日志**

启动后端时查看控制台输出：
```
Agent xxx: Error connecting to MCP server filesystem: ...
```

4. **测试服务器独立运行**

在命令行中手动运行 MCP 服务器命令：
```bash
npx -y @modelcontextprotocol/server-filesystem /tmp
```

### 问题 2：工具没有被使用

**症状**：Agent 有可用工具，但从不使用它们

**解决方案**：

1. **明确 system prompt**

在 system prompt 中明确说明工具的存在和用途：
```
你是一个助手，拥有网络搜索工具。当用户询问需要最新信息的问题时，请使用搜索工具。
```

2. **使用明确的提示**

用户提示要清楚地表明需要工具：
```
❌ "量子计算怎么样？"
✅ "搜索量子计算的最新新闻"
```

3. **检查工具可用性**

通过 API 验证工具确实可用：
```bash
curl http://localhost:8000/api/mcp/agents/{agent_id}/tools
```

### 问题 3：工具调用超时

**症状**：Agent 调用工具时长时间无响应

**解决方案**：

1. **检查网络连接**（对于需要网络的服务器）
2. **增加超时设置**（如果可配置）
3. **使用更轻量级的替代方案**

### 问题 4：权限错误

**症状**：文件系统或数据库访问被拒绝

**解决方案**：

1. **验证文件路径权限**
```bash
ls -la /path/to/directory
```

2. **检查数据库用户权限**
```sql
SHOW GRANTS FOR 'username'@'localhost';
```

3. **在 Docker 中运行时注意卷挂载**

### 问题 5：API 密钥无效

**症状**：需要认证的 MCP 服务器返回认证错误

**解决方案**：

1. **验证 API 密钥格式**
2. **检查密钥是否过期**
3. **确认密钥具有所需权限**
4. **测试密钥**：
```bash
# 对于 GitHub
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user

# 对于 Brave Search
curl -H "X-Subscription-Token: YOUR_KEY" "https://api.search.brave.com/res/v1/web/search?q=test"
```

### 问题 6：npm 包不存在

**症状**：配置了 MCP 服务器但无法连接，后端日志显示 npm 错误

**常见原因**：

1. **使用了不存在的 npm 包名**

例如，`@copilotkit/mcp-websearch-server` 这个包 **不存在**。

❌ **错误配置**：
```json
{
  "name": "websearch",
  "command": "npx",
  "args": ["@copilotkit/mcp-websearch-server"]
}
```

✅ **正确配置**（使用 Brave Search）：
```json
{
  "name": "brave_search",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-brave-search"],
  "env": {
    "BRAVE_API_KEY": "你的API密钥"
  }
}
```

2. **验证 npm 包是否存在**

```bash
npm info @modelcontextprotocol/server-brave-search
```

如果包存在，会显示包信息；如果不存在，会显示 404 错误。

3. **缺少 -y 参数**

使用 npx 时必须添加 `-y` 参数来自动确认安装：

❌ `"args": ["@modelcontextprotocol/server-brave-search"]`

✅ `"args": ["-y", "@modelcontextprotocol/server-brave-search"]`

**可用的网络搜索 MCP 服务器**：

| 包名 | 描述 | 需要 API 密钥 |
|------|------|--------------|
| `@modelcontextprotocol/server-brave-search` | Brave Search | 是 (BRAVE_API_KEY) |
| `@modelcontextprotocol/server-puppeteer` | 网页抓取/浏览器自动化 | 否 |

### 问题 7：使用诊断 API 检查 MCP 状态

您可以使用诊断 API 来检查 Agent 的 MCP 服务器连接状态：

```bash
curl http://localhost:8000/api/mcp/agents/{agent_id}/status
```

**返回示例**（正常状态）：
```json
{
  "status": "ok",
  "message": "Agent has 1 MCP server(s) connected with 3 tool(s) available.",
  "connected_servers": [
    {
      "name": "brave_search",
      "status": "connected",
      "tools_count": 3
    }
  ],
  "tools_available": 3
}
```

**返回示例**（无连接）：
```json
{
  "status": "no_client",
  "message": "No MCP client found for this agent. The agent may not have any MCP servers configured, or the agent hasn't been initialized yet.",
  "connected_servers": [],
  "tools_available": 0
}
```

---

## 总结

通过本指南，您应该能够：

1. ✅ 理解 MCP 在系统中的作用
2. ✅ 配置常见的 MCP 服务器
3. ✅ 了解 Agent 如何自动调用工具
4. ✅ 掌握系统的技术实现原理
5. ✅ 应用最佳实践确保安全和性能
6. ✅ 诊断和解决常见问题

## 更多资源

- [MCP 官方文档](https://modelcontextprotocol.io)
- [MCP 服务器注册表](https://github.com/modelcontextprotocol/servers)
- [创建自定义 MCP 服务器](https://modelcontextprotocol.io/docs/building-servers)
- [项目 README](../README.md)
- [英文版 MCP 指南](./MCP_GUIDE.md)

---

**编写日期**：2024年

**版本**：1.0

**维护者**：A2A Agent System 团队
