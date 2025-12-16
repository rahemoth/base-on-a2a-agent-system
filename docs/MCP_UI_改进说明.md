# MCP 配置界面改进说明

## 改进概述

根据您的反馈，我们对 MCP 服务器配置和 Agent 聊天界面进行了以下改进：

### 1. 完善 MCP 服务器配置表单

**之前的问题**：
- 前端只有 2 个字段（服务器名称和命令）
- 无法配置参数 (args) 和环境变量 (env)
- 用户不知道如何添加完整的 MCP 服务器配置

**现在的改进**：
- ✅ 添加了 **参数 (args)** 输入框（支持多行，每行一个参数）
- ✅ 添加了 **环境变量 (env)** 输入框（KEY=VALUE 格式，每行一个）
- ✅ 显示完整的 MCP 服务器详情（包括参数和环境变量）
- ✅ 添加了配置指南链接和帮助文本

#### 配置表单字段说明

**必填字段**：
1. **服务器名称***：MCP 服务器的唯一标识
   - 示例：`filesystem`, `github`, `brave_search`

2. **命令***：启动 MCP 服务器的可执行命令
   - 示例：`npx`, `python`, `node`

**可选字段**：
3. **参数**（每行一个）：传递给命令的参数列表
   ```
   -y
   @modelcontextprotocol/server-brave-search
   ```

4. **环境变量**（KEY=VALUE 格式，每行一个）：用于传递 API 密钥等敏感信息
   ```
   BRAVE_API_KEY=BSA_xxxxxx
   GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxx
   ```

#### 配置示例

**示例 1：文件系统访问**
- 服务器名称: `filesystem`
- 命令: `npx`
- 参数:
  ```
  -y
  @modelcontextprotocol/server-filesystem
  /home/user/documents
  ```
- 环境变量: （留空）

**示例 2：GitHub 集成**
- 服务器名称: `github`
- 命令: `npx`
- 参数:
  ```
  -y
  @modelcontextprotocol/server-github
  ```
- 环境变量:
  ```
  GITHUB_PERSONAL_ACCESS_TOKEN=ghp_你的token
  ```

**示例 3：网络搜索**
- 服务器名称: `brave_search`
- 命令: `npx`
- 参数:
  ```
  -y
  @modelcontextprotocol/server-brave-search
  ```
- 环境变量:
  ```
  BRAVE_API_KEY=BSA_你的api_key
  ```

### 2. Agent 工具意识增强

**之前的问题**：
- Agent 不知道自己有哪些 MCP 服务器和工具可用
- 用户无法在聊天界面查看可用工具
- Agent 可能不会主动使用配置好的工具

**现在的改进**：
- ✅ 聊天界面新增 **工具面板** 按钮（工具图标 🔧）
- ✅ 点击后显示所有可用的 MCP 工具和内置工具
- ✅ Agent 在对话开始时自动接收工具列表信息
- ✅ Agent 知道自己可以使用哪些工具并主动使用它们

#### 工具面板功能

**如何访问**：
1. 打开与 Agent 的聊天窗口
2. 点击右上角的工具图标（🔧）
3. 工具面板将展开显示

**面板内容**：
- **MCP 服务器分组**：按服务器名称分组显示
  - 显示每个服务器提供的工具列表
  - 每个工具显示名称和描述
  
- **内置工具**：系统提供的默认工具
  - 文本处理工具
  - 其他辅助工具

**示例显示**：
```
🔧 可用工具

【brave_search】服务器
  - brave_web_search: 使用 Brave Search 进行网络搜索

【filesystem】服务器
  - read_file: 读取文件内容
  - list_directory: 列出目录内容
  - write_file: 写入文件内容

内置工具
  - text_summarize: 总结长文本的关键要点
  - text_extract_keywords: 从文本中提取关键词
```

#### Agent 工具意识机制

当用户首次向 Agent 发送消息时，系统会自动在上下文中添加一条系统消息：

```
你配置了以下 MCP 服务器和工具:

【brave_search】服务器:
  - brave_web_search: 使用 Brave Search 进行网络搜索

【github】服务器:
  - get_repository: 获取仓库信息
  - list_issues: 列出仓库的 issues

你还有以下内置工具:
  - text_summarize: 总结长文本的关键要点
  - text_extract_keywords: 从文本中提取关键词

请在需要时主动使用这些工具来帮助用户完成任务。
```

这样 Agent 就明确知道自己拥有哪些工具，并能在适当的时候主动使用它们。

### 3. 文档更新

更新了以下文档：
- ✅ `docs/MCP_GUIDE_CN.md` - 添加了前端配置的详细说明
- ✅ 添加了工具面板的使用指南
- ✅ 说明了 Agent 如何知道可用工具

## 使用流程

### 配置 MCP 服务器

1. **创建或编辑 Agent**
2. **找到 "MCP 服务器" 部分**
3. **填写完整信息**：
   - 服务器名称（必填）
   - 命令（必填）
   - 参数（可选，每行一个）
   - 环境变量（可选，KEY=VALUE 格式）
4. **点击 "添加 MCP 服务器"**
5. **保存 Agent 配置**

### 使用配置好的工具

1. **打开聊天窗口**
2. **（可选）点击工具图标查看可用工具**
3. **正常与 Agent 对话**
4. **Agent 会自动判断何时需要使用工具**

例如：
```
用户: "搜索一下最新的量子计算新闻"

Agent 内部操作：
1. 识别需要搜索功能
2. 发现可用的 brave_web_search 工具
3. 自动调用该工具
4. 返回搜索结果的总结

Agent 回复: "根据最新搜索，量子计算领域有以下进展..."
```

## 技术实现细节

### 前端改进

**文件**: `frontend/src/components/AgentConfigModal.jsx`
- 添加 `mcpArgsText` 和 `mcpEnvText` 状态
- 解析多行文本输入为数组和对象
- 显示完整的 MCP 服务器配置详情

**文件**: `frontend/src/components/ChatModal.jsx`
- 添加工具面板组件
- 加载并显示 MCP 和内置工具
- 在首次对话时注入工具信息系统消息

**文件**: `frontend/src/components/AgentConfigModal.css`
- 新增工具面板样式
- 改进 MCP 服务器列表显示

**文件**: `frontend/src/components/ChatModal.css`
- 工具面板布局和样式
- 工具列表项样式

### API 调用

使用以下 API 获取工具信息：
- `mcpService.getAgentTools(agentId)` - 获取 MCP 工具
- `toolsService.listTools(agentId)` - 获取所有工具（包括内置）

## 总结

通过这些改进：

1. **配置更简单**：用户可以在前端完整配置 MCP 服务器，包括参数和环境变量
2. **工具可见**：用户可以在聊天界面直接查看 Agent 拥有的所有工具
3. **Agent 更智能**：Agent 知道自己有哪些工具，能够主动使用它们来完成任务
4. **文档更完善**：提供了详细的配置指南和使用说明

这些改进解决了您提出的两个主要问题：
- ✅ 前端添加 MCP 服务器现在有完整的配置选项
- ✅ Agent 在聊天时知道自己有哪些 MCP 服务器和工具可用

---

**更新日期**：2024年12月16日  
**版本**：1.1
