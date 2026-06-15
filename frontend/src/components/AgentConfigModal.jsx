import React, { useState, useEffect } from 'react';
import { X, Plus, Trash2, Save } from 'lucide-react';
import { storageService } from '../services/storage';
import { agentService } from '../services/api';
import './AgentConfigModal.css';

// Constants
const SETTINGS_SAVE_DEBOUNCE_MS = 1000; // Debounce delay for auto-save

// Supported models for each provider
const GEMINI_MODELS = [
  { value: 'gemini-3.5-flash', label: 'Gemini 3.5 Flash' },
  { value: 'gemini-3.1-pro', label: 'Gemini 3.1 Pro' }
];

const GPT_MODELS = [
  { value: 'gpt-5.5-pro', label: 'GPT-5.5 Pro' },
  { value: 'gpt-5.5', label: 'GPT-5.5' },
  { value: 'gpt-5.4', label: 'GPT-5.4' }
];

const CLAUDE_MODELS = [
  { value: 'claude-opus-4.8', label: 'Claude Opus 4.8' },
  { value: 'claude-sonnet-4.6', label: 'Claude Sonnet 4.6' },
  { value: 'claude-haiku-4.5', label: 'Claude Haiku 4.5' }
];

const DEEPSEEK_MODELS = [
  { value: 'deepseek-v4-pro', label: 'DeepSeek V4 Pro' },
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' }
];

const KIMI_MODELS = [
  { value: 'kimi-2.6', label: 'Kimi 2.6' },
  { value: 'kimi-2.5', label: 'Kimi 2.5' }
];

const MIMO_MODELS = [
  { value: 'mimo-v2.5-pro', label: 'MiMo V2.5 Pro' },
  { value: 'mimo-v2.5', label: 'MiMo V2.5' }
];

const MINIMAX_MODELS = [
  { value: 'minimax-m3', label: 'MiniMax M3' },
  { value: 'minimax-m2.7', label: 'MiniMax M2.7' }
];

const GLM_MODELS = [
  { value: 'glm-5.1', label: 'GLM-5.1' },
  { value: 'glm-5', label: 'GLM-5' },
  { value: 'glm-4.7', label: 'GLM-4.7' }
];

const QWEN_MODELS = [
  { value: 'qwen3.7', label: 'Qwen 3.7' },
  { value: 'qwen3.7-max', label: 'Qwen 3.7 Max' },
  { value: 'qwen3.5-flash', label: 'Qwen 3.5 Flash' },
  { value: 'qwen3-max', label: 'Qwen 3 Max' },
  { value: 'qwen3-coder', label: 'Qwen 3 Coder' }
];

// Provider definitions with their characteristics
const PROVIDERS = {
  deepseek: {
    label: 'DeepSeek（深度求索）',
    models: DEEPSEEK_MODELS,
    requiresApiKey: true,
    apiKeyField: 'openai_api_key',
    apiKeyLabel: 'DeepSeek API 密钥',
    defaultModel: 'deepseek-v4-pro',
    defaultBaseUrl: 'https://api.deepseek.com/v1',
    isLocal: false
  },
  kimi: {
    label: 'Kimi（月之暗面）',
    models: KIMI_MODELS,
    requiresApiKey: true,
    apiKeyField: 'kimi_api_key',
    apiKeyLabel: 'Kimi API 密钥',
    defaultModel: 'kimi-2.6',
    defaultBaseUrl: 'https://api.moonshot.cn/v1',
    isLocal: false
  },
  mimo: {
    label: 'MiMo（小米）',
    models: MIMO_MODELS,
    requiresApiKey: true,
    apiKeyField: 'mimo_api_key',
    apiKeyLabel: 'MiMo API 密钥',
    defaultModel: 'mimo-v2.5-pro',
    defaultBaseUrl: 'https://api.xiaomimimo.com/v1',
    isLocal: false
  },
  minimax: {
    label: 'MiniMax',
    models: MINIMAX_MODELS,
    requiresApiKey: true,
    apiKeyField: 'minimax_api_key',
    apiKeyLabel: 'MiniMax API 密钥',
    defaultModel: 'minimax-m3',
    defaultBaseUrl: 'https://api.minimax.chat/v1/text/chatcompletion',
    isLocal: false
  },
  glm: {
    label: 'GLM（智谱AI）',
    models: GLM_MODELS,
    requiresApiKey: true,
    apiKeyField: 'zhipu_api_key',
    apiKeyLabel: '智谱 API 密钥',
    defaultModel: 'glm-5.1',
    defaultBaseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    isLocal: false
  },
  claude: {
    label: 'Claude',
    models: CLAUDE_MODELS,
    requiresApiKey: true,
    apiKeyField: 'anthropic_api_key',
    apiKeyLabel: 'Anthropic API 密钥',
    defaultModel: 'claude-opus-4.8',
    defaultBaseUrl: 'https://api.anthropic.com/v1',
    isLocal: false
  },
  gpt: {
    label: 'GPT',
    models: GPT_MODELS,
    requiresApiKey: true,
    apiKeyField: 'openai_api_key',
    apiKeyLabel: 'OpenAI API 密钥',
    defaultModel: 'gpt-5.5-pro',
    defaultBaseUrl: 'https://api.openai.com/v1',
    isLocal: false
  },
  gemini: {
    label: 'Gemini',
    models: GEMINI_MODELS,
    requiresApiKey: true,
    apiKeyField: 'google_api_key',
    apiKeyLabel: 'Google API 密钥',
    defaultModel: 'gemini-3.5-flash',
    isLocal: false
  },
  qwen: {
    label: 'QWEN',
    models: QWEN_MODELS,
    requiresApiKey: true,
    apiKeyField: 'qwen_api_key',
    apiKeyLabel: 'Qwen API 密钥',
    defaultModel: 'qwen3.7',
    defaultBaseUrl: 'https://dashscope.aliyuncs.com/api/text-generation/v1',
    isLocal: false
  },
  custom: {
    label: '自定义 API (OpenAI 兼容)',
    requiresApiKey: false,
    requiresModelInput: true,
    defaultBaseUrl: 'http://localhost:1234/v1',
    defaultModel: 'custom-model',
    isLocal: true
  }
};




const AgentConfigModal = ({ agent, onClose, onSave }) => {
  // Load saved settings from localStorage if available for editing
  const [config, setConfig] = useState(() => {
    if (agent?.id) {
      const savedSettings = storageService.getAgentSettings(agent.id);
      if (savedSettings) {
        return savedSettings;
      }
    }
    return agent?.config || {
      name: '',
      description: '',
      provider: 'deepseek',
      model: 'deepseek-v4-pro',
      system_prompt: '',
      temperature: 0.7,
      max_tokens: null,
      google_api_key: null,
      openai_api_key: null,
      anthropic_api_key: null,
      kimi_api_key: null,
      mimo_api_key: null,
      minimax_api_key: null,
      zhipu_api_key: null,
      qwen_api_key: null,
      api_base_url: null,
      openai_base_url: null, // Keep for backward compatibility
      mcp_servers: [],
      capabilities: [],
      metadata: {},
      rag_enabled: false,
      compression: {
        enabled: false,
        provider: 'deepseek',
        model: 'deepseek-v4-pro',
        api_key: null,
        base_url: null,
        max_tokens: 500,
        temperature: 0.3,
        target_ratio: 0.3
      }
    };


  });

  // Save settings to localStorage when config changes (debounced)
  useEffect(() => {
    if (agent?.id && config.name) {
      const timeoutId = setTimeout(() => {
        storageService.saveAgentSettings(agent.id, config);
      }, SETTINGS_SAVE_DEBOUNCE_MS);

      return () => clearTimeout(timeoutId);
    }
  }, [config, agent?.id]);

  // State for custom model name input (for local/custom providers)
  const [customModel, setCustomModel] = useState(() => {
    if (!agent?.config?.model || !agent?.config?.provider) return '';
    const providerInfo = PROVIDERS[agent.config.provider];
    if (providerInfo?.requiresModelInput) {
      return agent.config.model;
    }
    return '';
  });

  const [newMcpServer, setNewMcpServer] = useState({
    name: '',
    command: '',
    args: [],
    env: {}
  });

  // State for MCP server args and env input (text format)
  const [mcpArgsText, setMcpArgsText] = useState('');
  const [mcpEnvText, setMcpEnvText] = useState('');

  // State for test connection
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  
  // State for compression model test connection
  const [isCompressionTesting, setIsCompressionTesting] = useState(false);
  const [compressionTestResult, setCompressionTestResult] = useState(null);

  // Track if mouse was pressed on overlay for proper drag handling
  const overlayClickStarted = React.useRef(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(config);
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await agentService.testConnection(config);
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || error.message || '测试连接失败'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleCompressionTestConnection = async () => {
    setIsCompressionTesting(true);
    setCompressionTestResult(null);
    
    try {
      const compressionConfig = {
        provider: config.compression?.provider || 'deepseek',
        model: config.compression?.model || '',
        api_base_url: config.compression?.api_base_url,
        openai_api_key: config.compression?.api_key,
        anthropic_api_key: config.compression?.api_key,
        kimi_api_key: config.compression?.api_key,
        mimo_api_key: config.compression?.api_key,
        minimax_api_key: config.compression?.api_key,
        zhipu_api_key: config.compression?.api_key,
        qwen_api_key: config.compression?.api_key,
        google_api_key: config.compression?.api_key,
      };
      
      const result = await agentService.testConnection(compressionConfig);
      setCompressionTestResult(result);
    } catch (error) {
      setCompressionTestResult({
        success: false,
        message: error.response?.data?.detail || error.message || '测试压缩模型连接失败'
      });
    } finally {
      setIsCompressionTesting(false);
    }
  };

  const addMcpServer = () => {
    if (newMcpServer.name && newMcpServer.command) {
      // Parse args from text (one per line)
      const args = mcpArgsText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
      
      // Parse env from text (KEY=VALUE format, one per line)
      const env = {};


      mcpEnvText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .forEach(line => {
          const [key, ...valueParts] = line.split('=');
          if (key && valueParts.length > 0) {
            env[key.trim()] = valueParts.join('=').trim();
          }
        });
      
      setConfig({
        ...config,
        mcp_servers: [...config.mcp_servers, { 
          name: newMcpServer.name,
          command: newMcpServer.command,
          args,
          env
        }]
      });
      setNewMcpServer({ name: '', command: '', args: [], env: {} });
      setMcpArgsText('');
      setMcpEnvText('');
    }
  };

  const removeMcpServer = (index) => {
    const updated = [...config.mcp_servers];
    updated.splice(index, 1);
    setConfig({ ...config, mcp_servers: updated });
  };

  const handleProviderChange = (newProvider) => {
    const providerInfo = PROVIDERS[newProvider];
    const newConfig = {
      ...config,
      provider: newProvider,
      model: providerInfo.defaultModel
    };
    
    // Set default base URL for local providers
    if (providerInfo.defaultBaseUrl) {
      newConfig.api_base_url = providerInfo.defaultBaseUrl;
    } else {
      newConfig.api_base_url = null;
    }
    
    setConfig(newConfig);
    // For local providers, initialize customModel with the default model name
    if (providerInfo.requiresModelInput) {
      setCustomModel(providerInfo.defaultModel);
    } else {
      setCustomModel('');
    }
  };

  const handleModelChange = (newModel) => {
    setConfig({ ...config, model: newModel });
    setCustomModel('');
  };

  const handleCustomModelChange = (value) => {
    setCustomModel(value);
    setConfig({ ...config, model: value || 'custom-model' });
  };

  // Compression provider handlers
  const handleCompressionProviderChange = (newProvider) => {
    const providerInfo = PROVIDERS[newProvider];
    setConfig({
      ...config,
      compression: {
        ...config.compression,
        provider: newProvider,
        model: providerInfo.defaultModel,
        base_url: providerInfo.defaultBaseUrl || null
      }
    });
  };

  const handleCompressionModelChange = (newModel) => {
    setConfig({
      ...config,
      compression: {
        ...config.compression,
        model: newModel
      }
    });
  };

  const currentProvider = PROVIDERS[config.provider];
  if (!currentProvider) {
    console.error(`Invalid provider: ${config.provider}`);
  }
  const providerInfo = currentProvider || PROVIDERS.google;
  const isLocalProvider = providerInfo.isLocal;

  // Fix the modal drag bug: prevent closing on mousedown and drag out
  const handleOverlayMouseDown = (e) => {
    // Only set flag if the click started on the overlay (not dragged from modal content)
    if (e.target.classList.contains('modal-overlay')) {
      overlayClickStarted.current = true;
    }
  };

  const handleOverlayClick = (e) => {
    // Only close if we started the click on the overlay
    if (e.target.classList.contains('modal-overlay') && overlayClickStarted.current) {
      onClose();
    }
    overlayClickStarted.current = false;
  };

  return (
    <div 
      className="modal-overlay" 
      onMouseDown={handleOverlayMouseDown}
      onClick={handleOverlayClick}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{agent ? '配置 Agent' : '创建新 Agent'}</h2>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-section">
            <h3>基本信息</h3>
            
            <div className="form-group">
              <label>Agent 名称 *</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                placeholder="我的 AI Agent"
                required
              />
            </div>

            <div className="form-group">
              <label>描述</label>
              <textarea
                value={config.description}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                placeholder="描述这个 Agent 的用途..."
                rows={3}
              />
            </div>

            <div className="form-group">
              <label>模型提供商 *</label>
              <div className="magic-select">
                <select
                  value={config.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                >
                  {Object.entries(PROVIDERS).map(([key, provider]) => (
                    <option key={key} value={key}>{provider.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {!isLocalProvider && (
              <div className="form-group">
                <label>模型 *</label>
                <div className="magic-select">
                  <select
                    value={config.model}
                    onChange={(e) => handleModelChange(e.target.value)}
                  >
                    {providerInfo.models.map(model => (
                      <option key={model.value} value={model.value}>{model.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {isLocalProvider && (
              <div className="form-group">
                <label>模型名称 *</label>
                <input
                  type="text"
                  value={customModel}
                  onChange={(e) => handleCustomModelChange(e.target.value)}
                  placeholder="输入模型名称 (例如: google/gemma-3-4b, llama2, mistral 等)"
                  required
                />
                <small className="form-hint">
                  输入您本地 LLM 服务器中配置的确切模型名称
                </small>
              </div>
            )}

            {providerInfo.requiresApiKey && (
              <div className="form-group">
                <label>{providerInfo.apiKeyLabel} (可选)</label>
                <input
                  type="password"
                  value={config[providerInfo.apiKeyField] || ''}
                  onChange={(e) => setConfig({ ...config, [providerInfo.apiKeyField]: e.target.value || null })}
                  placeholder="留空则使用 .env 文件中的全局 API 密钥"
                />
                <small className="form-hint">
                  单个 Agent 的 API 密钥会覆盖全局设置
                </small>
              </div>
            )}

            {(providerInfo.defaultBaseUrl && !isLocalProvider) && (
              <div className="form-group">
                <label>API 基础 URL (可选)</label>
                <input
                  type="text"
                  value={config.api_base_url || ''}
                  onChange={(e) => setConfig({ ...config, api_base_url: e.target.value || null })}
                  placeholder={providerInfo.defaultBaseUrl}
                />
                <small className="form-hint">
                  留空则使用默认端点: {providerInfo.defaultBaseUrl}
                </small>
              </div>
            )}

            {isLocalProvider && (
              <div className="custom-api-config">
                <div className="form-group">
                  <label>API 基础 URL *</label>
                  <input
                    type="text"
                    value={config.api_base_url || ''}
                    onChange={(e) => setConfig({ ...config, api_base_url: e.target.value || null })}
                    placeholder={providerInfo.defaultBaseUrl || 'http://localhost:8080/v1'}
                    required
                  />
                  <small className="form-hint">
                    {providerInfo.defaultBaseUrl 
                      ? `默认值: ${providerInfo.defaultBaseUrl}`
                      : '输入您的 OpenAI 兼容 API 端点的基础 URL'}
                  </small>
                </div>
                
                <div className="form-group">
                  <label>API 密钥 (可选)</label>
                  <input
                    type="password"
                    value={config.openai_api_key || ''}
                    onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value || null })}
                    placeholder="本地模型可留空或填任意字符串"
                  />
                  <small className="form-hint">
                    某些服务（如 Together AI）需要 API 密钥，本地模型通常不需要
                  </small>
                </div>

                {providerInfo.description && (
                  <div className="form-hint-box">
                    <strong>支持的服务：</strong>{providerInfo.description}
                  </div>
                )}


              </div>
            )}

            <div className="form-group">
              <label>测试模型连接</label>
              <button
                type="button"
                className="btn btn-primary btn-block"
                onClick={handleTestConnection}
                disabled={isTesting}
              >
                {isTesting ? (
                  <span className="btn-loading">
                    <span className="spinner"></span>
                    测试中...
                  </span>
                ) : (
                  '测试连接'
                )}
              </button>
              {testResult && (
                <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
                  {testResult.success ? (
                    <span className="result-icon">✓</span>
                  ) : (
                    <span className="result-icon">✗</span>
                  )}
                  {testResult.message}
                </div>
              )}
            </div>

            <div className="form-group">
              <label>系统提示词</label>
              <textarea
                value={config.system_prompt || ''}
                onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
                placeholder="你是一个有帮助的 AI 助手..."
                rows={4}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>温度 (Temperature)</label>
                <input
                  type="number"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                  min="0"
                  max="2"
                  step="0.1"
                />
              </div>

              <div className="form-group">
                <label>最大令牌数</label>
                <input
                  type="number"
                  value={config.max_tokens || ''}
                  onChange={(e) => setConfig({ ...config, max_tokens: e.target.value ? parseInt(e.target.value) : null })}
                  placeholder="自动"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>MCP 服务器</h3>
            <p className="form-help-text">配置 Model Context Protocol 服务器以提供工具和资源。<a href="https://github.com/rahemoth/base-on-a2a-agent-system/blob/main/docs/MCP_GUIDE_CN.md" target="_blank" rel="noopener noreferrer">查看配置指南</a></p>
            
            {config.mcp_servers.map((server, index) => (
              <div key={index} className="mcp-server-item">
                <div className="mcp-server-details">
                  <div><strong>{server.name}</strong></div>
                  <div className="server-command">{server.command} {server.args && server.args.length > 0 && `(${server.args.length} 个参数)`}</div>
                  {server.args && server.args.length > 0 && (
                    <div className="server-args">参数: {server.args.join(', ')}</div>
                  )}
                  {server.env && Object.keys(server.env).length > 0 && (
                    <div className="server-env">环境变量: {Object.keys(server.env).join(', ')}</div>
                  )}
                </div>
                <button
                  type="button"
                  className="btn btn-icon btn-danger"
                  onClick={() => removeMcpServer(index)}
                  title="删除服务器"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}

            <div className="add-mcp-server">
              <div className="form-group">
                <label>服务器名称 *</label>
                <input
                  type="text"
                  value={newMcpServer.name}
                  onChange={(e) => setNewMcpServer({ ...newMcpServer, name: e.target.value })}
                  placeholder="例如: filesystem, github, brave_search"
                />
              </div>
              <div className="form-group">
                <label>命令 *</label>
                <input
                  type="text"
                  value={newMcpServer.command}
                  onChange={(e) => setNewMcpServer({ ...newMcpServer, command: e.target.value })}
                  placeholder="例如: npx, python, node"
                />
              </div>
              <div className="form-group">
                <label>参数 (每行一个)</label>
                <textarea
                  value={mcpArgsText}
                  onChange={(e) => setMcpArgsText(e.target.value)}
                  placeholder={`例如:\n-y\n@modelcontextprotocol/server-filesystem\n/path/to/directory`}
                  rows={3}
                />
                <small className="form-help-text">每行一个参数，按顺序传递给命令</small>
              </div>
              <div className="form-group">
                <label>环境变量 (KEY=VALUE 格式，每行一个)</label>
                <textarea
                  value={mcpEnvText}
                  onChange={(e) => setMcpEnvText(e.target.value)}
                  placeholder={`例如:\nGITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxx\nBRAVE_API_KEY=BSA_xxxxx`}
                  rows={2}
                />
                <small className="form-help-text">用于传递 API 密钥等敏感信息</small>
              </div>
              <button type="button" className="btn btn-secondary" onClick={addMcpServer}>
                <Plus size={16} /> 添加 MCP 服务器
              </button>
            </div>
          </div>

          <div className="form-section">
            <h3>RAG 配置</h3>
            <p className="form-help-text">配置检索增强生成 (RAG) 和上下文压缩功能。</p>
            
            <div className="form-group">
              <div className="magic-checkbox">
                <input
                  type="checkbox"
                  id="rag_enabled"
                  checked={config.rag_enabled || false}
                  onChange={(e) => setConfig({ ...config, rag_enabled: e.target.checked })}
                />
                <span className="checkmark"></span>
                <span>启用 RAG 记忆系统</span>
              </div>
              <small className="form-hint">启用后，Agent 将使用向量数据库存储和检索对话历史</small>
            </div>

            <div className="form-group">
              <div className="magic-checkbox">
                <input
                  type="checkbox"
                  id="compression_enabled"
                  checked={config.compression?.enabled || false}
                  onChange={(e) => setConfig({ 
                    ...config, 
                    compression: { 
                      ...config.compression, 
                      enabled: e.target.checked 
                    } 
                  })}
                />
                <span className="checkmark"></span>
                <span>启用上下文压缩</span>
              </div>
              <small className="form-hint">使用小模型压缩长对话历史，减少 token 消耗</small>
            </div>

            {(config.compression?.enabled || false) && (
              <div className="compression-settings">
                <div className="form-group">
                  <label>压缩模型提供商 *</label>
                  <div className="magic-select">
                    <select
                      value={config.compression?.provider || 'deepseek'}
                      onChange={(e) => handleCompressionProviderChange(e.target.value)}
                    >
                      {Object.entries(PROVIDERS).map(([key, provider]) => (
                        <option key={key} value={key}>{provider.label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {(() => {
                  const compressionProvider = PROVIDERS[config.compression?.provider];
                  if (!compressionProvider) return null;
                  
                  if (!compressionProvider.isLocal) {
                    return (
                      <div className="form-group">
                        <label>压缩模型 *</label>
                        <div className="magic-select">
                          <select
                            value={config.compression?.model || compressionProvider.defaultModel}
                            onChange={(e) => handleCompressionModelChange(e.target.value)}
                          >
                            {compressionProvider.models?.map(model => (
                              <option key={model.value} value={model.value}>{model.label}</option>
                            ))}
                          </select>
                        </div>
                      </div>
                    );
                  } else {
                    return (
                      <div className="form-group">
                        <label>压缩模型名称 *</label>
                        <input
                          type="text"
                          value={config.compression?.model || ''}
                          onChange={(e) => handleCompressionModelChange(e.target.value)}
                          placeholder="输入模型名称 (例如: google/gemma-3-4b, llama2, mistral 等)"
                          required
                        />
                      </div>
                    );
                  }
                })()}

                <div className="form-group">
                  <label>压缩 API 密钥 (可选)</label>
                  <input
                    type="password"
                    value={config.compression?.api_key || ''}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      compression: { 
                        ...config.compression, 
                        api_key: e.target.value || null 
                      } 
                    })}
                    placeholder="留空则使用 .env 文件中的全局配置"
                  />
                  <small className="form-hint">
                    用于压缩的独立 API 密钥，可使用比主模型更小更便宜的模型
                  </small>
                </div>

                <div className="form-group">
                  <label>测试压缩模型连接</label>
                  <button
                    type="button"
                    className="btn btn-primary btn-block"
                    onClick={handleCompressionTestConnection}
                    disabled={isCompressionTesting}
                  >
                    {isCompressionTesting ? (
                      <span className="btn-loading">
                        <span className="spinner"></span>
                        测试中...
                      </span>
                    ) : (
                      '测试连接'
                    )}
                  </button>
                  {compressionTestResult && (
                    <div className={`test-result ${compressionTestResult.success ? 'success' : 'error'}`}>
                      {compressionTestResult.success ? (
                        <span className="result-icon">✓</span>
                      ) : (
                        <span className="result-icon">✗</span>
                      )}
                      {compressionTestResult.message}
                    </div>
                  )}
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label>最大令牌数</label>
                    <input
                      type="number"
                      value={config.compression?.max_tokens || 500}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        compression: { 
                          ...config.compression, 
                          max_tokens: parseInt(e.target.value) || 500 
                        } 
                      })}
                      min="100"
                      max="2000"
                    />
                  </div>

                  <div className="form-group">
                    <label>温度</label>
                    <input
                      type="number"
                      value={config.compression?.temperature || 0.3}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        compression: { 
                          ...config.compression, 
                          temperature: parseFloat(e.target.value) || 0.3 
                        } 
                      })}
                      min="0"
                      max="1"
                      step="0.1"
                    />
                  </div>

                  <div className="form-group">
                    <label>压缩目标比率</label>
                    <input
                      type="number"
                      value={config.compression?.target_ratio || 0.3}
                      onChange={(e) => setConfig({ 
                        ...config, 
                        compression: { 
                          ...config.compression, 
                          target_ratio: parseFloat(e.target.value) || 0.3 
                        } 
                      })}
                      min="0.1"
                      max="0.8"
                      step="0.1"
                    />
                    <small className="form-hint">压缩后保留的内容比例</small>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              取消
            </button>
            <button type="submit" className="btn btn-primary">
              {agent ? '更新 Agent' : '创建 Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AgentConfigModal;
