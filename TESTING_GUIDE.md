# 测试指南 / Testing Guide

## 前置要求 / Prerequisites

### 软件要求 / Software Requirements
- Python 3.10+
- Node.js 18+
- LM Studio 或其他 OpenAI 兼容的本地 AI 服务器

### 安装依赖 / Install Dependencies

**后端 / Backend:**
```bash
pip install -r requirements.txt
```

**前端 / Frontend:**
```bash
cd frontend
npm install
```

## 测试场景 / Test Scenarios

### 1. 测试 Google Gemini Agent

**前置条件**: 需要有效的 Google API Key

**步骤**:
1. 配置 `.env` 文件，添加 `GOOGLE_API_KEY=你的密钥`
2. 启动后端: `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000`
3. 启动前端: `cd frontend && npm run dev`
4. 打开浏览器访问 `http://localhost:5173`
5. 点击"创建 Agent"
6. 选择 "Google (Gemini)" 作为提供商
7. 选择模型（如 "Gemini 2.0 Flash"）
8. 填写其他信息，点击"创建 Agent"
9. 点击 Agent 卡片上的聊天图标
10. 发送消息测试

**预期结果**:
- Agent 创建成功
- 能够正常发送和接收消息
- 消息内容正确显示

### 2. 测试 OpenAI GPT Agent

**前置条件**: 需要有效的 OpenAI API Key

**步骤**:
1. 配置 `.env` 文件，添加 `OPENAI_API_KEY=你的密钥`
2. 按照与 Google Gemini 类似的步骤
3. 选择 "OpenAI (GPT)" 作为提供商
4. 选择模型（如 "GPT-4o Mini"）

**预期结果**:
- Agent 创建成功
- 能够正常发送和接收消息

### 3. 测试本地 AI 模型 (LM Studio)

**前置条件**: 
- LM Studio 已安装并运行
- 已加载一个模型（如 google/gemma-3-4b）

**LM Studio 配置步骤**:
1. 启动 LM Studio
2. 在左侧菜单选择一个模型并下载
3. 点击 "Local Server" 标签
4. 点击 "Start Server" 启动本地服务器
5. 记下服务器地址（如 `http://192.168.175.1:1234`）
6. 记下模型标识符（如 `google/gemma-3-4b`）

**创建 Agent 步骤**:
1. 启动前端应用
2. 点击"创建 Agent"
3. 选择 "本地 AI 模型 (LM Studio, Ollama 等)" 作为提供商
4. 在"模型名称"输入框输入模型标识符（如 `google/gemma-3-4b`）
5. 在"API 基础 URL"输入框输入 LM Studio 服务器地址（如 `http://192.168.175.1:1234`）
   **注意**: 不要包含 `/v1` 后缀，OpenAI SDK 会自动添加
6. 填写其他信息（名称、描述、系统提示词等）
7. 点击"创建 Agent"

**测试对话**:
1. 点击新创建的 Agent 卡片上的聊天图标
2. 发送测试消息（如 "你好，请介绍一下你自己"）
3. 等待响应

**预期结果**:
- Agent 创建成功
- 能够发送消息到 LM Studio
- 收到 LM Studio 返回的响应
- 响应内容显示在聊天窗口

**调试日志检查**:
在后端终端中应该能看到类似以下的日志：
```
DEBUG:backend.agents.a2a_executor:Sending request to lmstudio with model google/gemma-3-4b
DEBUG:backend.agents.a2a_executor:Received response: 你好！我是一个AI助手...
```

### 4. 测试多 Agent 协作

**前置条件**: 
- 至少创建 2 个不同的 Agents
- 每个 Agent 可以使用不同的模型或提供商

**步骤**:
1. 创建至少 2 个 Agents（可以是 Google + OpenAI，或 Google + LM Studio 等组合）
2. 点击顶部的"协作"按钮
3. 选择要协作的 Agents（至少 2 个）
4. 输入任务描述（如 "设计一个简单的待办事项应用的架构"）
5. 可选择协调员 Agent
6. 设置最大轮数（如 3）
7. 点击"开始协作"
8. 观察协作过程

**预期结果**:
- 协作成功启动
- 能看到每个 Agent 的贡献
- 协作历史显示在界面上
- 每条消息标注了 Agent 名称和时间戳

### 5. 测试 UI 功能

**模态框拖动测试**:
1. 点击"创建 Agent"打开配置弹窗
2. 在弹窗内部按下鼠标左键
3. 保持按下状态将鼠标拖出弹窗到遮罩层区域
4. 释放鼠标

**预期结果**:
- 弹窗不应该关闭
- 只有当鼠标在遮罩层上按下和释放时才关闭弹窗

**中文化测试**:
1. 检查所有按钮文本是否为中文
2. 检查所有标签和提示是否为中文
3. 检查表单字段是否为中文
4. 检查错误消息是否为中文

**预期结果**:
- 所有可见文本都应该是中文
- 翻译应该准确、自然

## 常见问题 / Troubleshooting

### 问题 1: 本地模型无响应

**症状**: 消息发送成功，但没有收到响应

**可能原因**:
1. LM Studio 服务器未启动
2. 模型名称输入错误
3. API URL 配置错误
4. 网络连接问题

**解决方案**:
1. 确认 LM Studio 服务器正在运行
2. 检查模型名称是否与 LM Studio 中显示的完全一致
3. 确保 URL 以 `/v1` 结尾
4. 检查后端日志查看详细错误信息
5. 尝试在 LM Studio 中直接测试模型

### 问题 2: 后端启动失败

**症状**: 运行 uvicorn 命令后报错

**可能原因**:
1. 缺少依赖包
2. Python 版本不兼容
3. 端口被占用

**解决方案**:
1. 重新安装依赖: `pip install -r requirements.txt`
2. 确认 Python 版本 >= 3.10
3. 更换端口或停止占用端口的程序

### 问题 3: 前端构建失败

**症状**: `npm run build` 报错

**可能原因**:
1. Node.js 版本过低
2. 依赖安装不完整

**解决方案**:
1. 升级 Node.js 到 18 或更高版本
2. 删除 `node_modules` 文件夹和 `package-lock.json`
3. 重新运行 `npm install`

### 问题 4: CORS 错误

**症状**: 浏览器控制台显示 CORS 相关错误

**可能原因**:
后端 CORS 配置不包含前端 URL

**解决方案**:
在 `.env` 文件中添加或修改:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 性能测试 / Performance Testing

### 响应时间测试

**测试目标**: 确保响应时间在合理范围内

**步骤**:
1. 发送简单问题（如 "你好"）
2. 记录从发送到收到响应的时间
3. 重复测试 5 次取平均值

**预期结果**:
- Google Gemini: < 3 秒
- OpenAI GPT: < 3 秒
- 本地模型: 取决于硬件，但应该 < 10 秒

### 并发测试

**测试目标**: 确保系统能处理多个并发请求

**步骤**:
1. 创建多个 Agents
2. 同时向多个 Agents 发送消息
3. 观察系统响应

**预期结果**:
- 所有请求都能得到响应
- 没有请求超时或失败
- 响应顺序可能不同，但都能正确返回

## 回归测试 / Regression Testing

在每次代码更新后，应运行以下测试确保没有破坏现有功能：

1. ✓ Agent 创建功能正常
2. ✓ Agent 编辑功能正常
3. ✓ Agent 删除功能正常
4. ✓ 聊天功能正常
5. ✓ 协作功能正常
6. ✓ MCP 服务器配置功能正常
7. ✓ 所有 UI 文本都是中文
8. ✓ 模态框行为正常

## 安全测试 / Security Testing

### 代码扫描

已运行 CodeQL 扫描，结果：
- Python: 0 个警告
- JavaScript: 0 个警告

### API 密钥保护

**测试**:
1. 创建 Agent 时输入 API 密钥
2. 刷新页面
3. 编辑 Agent
4. 检查 API 密钥字段

**预期结果**:
- API 密钥应该以密码形式显示（隐藏字符）
- 不应该在浏览器开发者工具的网络标签中明文显示

## 报告问题 / Reporting Issues

如果发现问题，请提供以下信息：

1. 操作系统和版本
2. Python 版本
3. Node.js 版本
4. 浏览器和版本
5. 详细的复现步骤
6. 后端日志（如果有）
7. 浏览器控制台错误（如果有）
8. 屏幕截图（如果有）

## 总结 / Summary

本测试指南涵盖了系统的主要功能和常见场景。在部署到生产环境之前，建议完成所有测试场景并确保通过。
