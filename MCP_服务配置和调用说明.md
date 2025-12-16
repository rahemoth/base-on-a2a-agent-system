# MCP 服务配置和调用说明

## 问题回答

您询问：**"这个项目的MCP服务该怎么填写，和agent是怎么调用mcp服务器的"**

我已经为您创建了详细的中文指南，请查看：**[docs/MCP_GUIDE_CN.md](docs/MCP_GUIDE_CN.md)**

---

## 快速回答

### 一、MCP 服务该怎么填写？

MCP 服务配置包含 4 个字段：

```json
{
  "name": "服务器名称",
  "command": "可执行命令",
  "args": ["参数列表"],
  "env": {
    "环境变量名": "环境变量值"
  }
}
```

**实际例子 - 配置文件系统访问：**

```json
{
  "name": "filesystem",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/documents"],
  "env": {}
}
```

**实际例子 - 配置 GitHub 访问：**

```json
{
  "name": "github",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_你的token"
  }
}
```

**实际例子 - 配置网络搜索：**

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

### 二、Agent 是怎么调用 MCP 服务器的？

**简单回答：自动调用，无需手动操作！**

#### 工作流程：

```
1. 创建 Agent 时 → 系统自动启动配置的 MCP 服务器
                ↓
2. Agent 初始化 → 自动发现所有可用的工具
                ↓
3. 用户发消息   → Agent 的 LLM 分析是否需要工具
                ↓
4. 需要工具时   → Agent 自动选择并调用相应的 MCP 工具
                ↓
5. 获取结果     → Agent 将结果整合到回复中
                ↓
6. 返回响应     → 用户收到包含工具执行结果的完整回答
```

#### 实际例子：

**场景 1：配置了文件系统 MCP 服务器**

```
用户: "请读取 /home/user/report.txt 文件的内容"

Agent 内部操作：
1. 识别需要读取文件
2. 发现可用的 filesystem 工具
3. 自动调用 filesystem_read_file(path="/home/user/report.txt")
4. 获取文件内容
5. 整合到回复中

Agent 回复: "文件内容如下：[文件实际内容]..."
```

**场景 2：配置了网络搜索 MCP 服务器**

```
用户: "搜索一下 2024 年人工智能的最新进展"

Agent 内部操作：
1. 识别需要搜索最新信息
2. 发现可用的 brave_search 工具
3. 自动调用 brave_web_search(query="2024年人工智能最新进展")
4. 获取搜索结果
5. 分析和总结搜索结果

Agent 回复: "根据最新搜索结果，2024年AI领域有以下重要进展：..."
```

---

## 在界面中如何配置？

### 步骤 1：创建 Agent

点击 "Create Agent" 按钮

### 步骤 2：填写基本信息

- Name: 给 Agent 起个名字
- Description: 描述 Agent 的用途
- Provider: 选择模型提供商（Google 或 OpenAI）
- Model: 选择具体模型

### 步骤 3：添加 MCP 服务器

在 "MCP Servers" 部分：

1. 点击 "Add MCP Server"
2. 填写：
   - **Server Name**: `brave_search`（举例）
   - **Command**: `npx`
   - **Arguments**: 
     ```
     -y
     @modelcontextprotocol/server-brave-search
     ```
   - **Environment Variables**:
     ```
     BRAVE_API_KEY = 你的API密钥
     ```

### 步骤 4：创建 Agent

点击 "Create Agent"，系统会自动：
- 启动 MCP 服务器
- 连接到服务器
- 发现可用工具
- 准备好接收用户消息

---

## 通过 API 如何配置？

发送 POST 请求到 `/api/agents/`：

```bash
curl -X POST http://localhost:8000/api/agents/ \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "name": "研究助手",
      "description": "可以搜索网络的研究助手",
      "provider": "google",
      "model": "gemini-2.0-flash-exp",
      "system_prompt": "你是一个研究助手，可以使用网络搜索工具帮助用户。",
      "mcp_servers": [
        {
          "name": "brave_search",
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-brave-search"],
          "env": {
            "BRAVE_API_KEY": "你的API密钥"
          }
        }
      ]
    }
  }'
```

---

## 常见 MCP 服务器配置速查表

| 服务器类型 | name | command | args | env |
|-----------|------|---------|------|-----|
| 文件系统 | `filesystem` | `npx` | `["-y", "@modelcontextprotocol/server-filesystem", "/路径"]` | `{}` |
| GitHub | `github` | `npx` | `["-y", "@modelcontextprotocol/server-github"]` | `{"GITHUB_PERSONAL_ACCESS_TOKEN": "token"}` |
| 网络搜索 | `brave_search` | `npx` | `["-y", "@modelcontextprotocol/server-brave-search"]` | `{"BRAVE_API_KEY": "key"}` |
| PostgreSQL | `postgres` | `npx` | `["-y", "@modelcontextprotocol/server-postgres", "postgresql://..."]` | `{}` |
| SQLite | `sqlite` | `npx` | `["-y", "@modelcontextprotocol/server-sqlite", "/路径/db.db"]` | `{}` |

---

## 技术实现原理（简化版）

### 代码位置：

1. **MCP 客户端管理**: `backend/mcp/client.py`
2. **Agent 执行器**: `backend/agents/a2a_executor.py`
3. **工具管理器**: `backend/agents/tools.py`

### 关键代码片段：

**初始化 MCP（在 Agent 创建时）**

```python
# backend/agents/a2a_executor.py
async def initialize_mcp(self):
    if self.config.mcp_servers:
        # 为此 Agent 创建 MCP 客户端
        self.mcp_client = await mcp_manager.create_client(self.agent_id)
        
        # 连接每个 MCP 服务器
        for mcp_config in self.config.mcp_servers:
            await self.mcp_client.connect_server(
                name=mcp_config.name,
                command=mcp_config.command,
                args=mcp_config.args,
                env=mcp_config.env
            )
        
        # 发现可用工具
        await self.tool_manager.discover_tools()
```

**连接 MCP 服务器**

```python
# backend/mcp/client.py
async def connect_server(self, name, command, args, env):
    # 创建服务器参数
    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env
    )
    
    # 启动服务器进程
    stdio_transport = await stdio_client(server_params)
    
    # 创建会话
    session = await ClientSession(stdio, write)
    await session.initialize()
    
    # 保存会话
    self.sessions[name] = session
```

**调用工具**

```python
# backend/mcp/client.py
async def call_tool(self, server_name, tool_name, arguments):
    # 找到对应的服务器会话
    session = self.sessions[server_name]
    
    # 调用工具
    result = await session.call_tool(tool_name, arguments)
    
    return result
```

---

## 更多详细信息

请查看完整的中文指南：**[docs/MCP_GUIDE_CN.md](docs/MCP_GUIDE_CN.md)**

该指南包含：
- ✅ 详细的配置说明
- ✅ 多个实际配置示例
- ✅ 完整的技术实现原理
- ✅ 系统架构图
- ✅ 代码执行流程详解
- ✅ 最佳实践建议
- ✅ 故障排除指南

---

**最后更新**: 2024年12月16日
