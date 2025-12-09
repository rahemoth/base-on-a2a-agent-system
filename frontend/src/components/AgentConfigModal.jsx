import React, { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import './AgentConfigModal.css';

// Supported models for each provider
const GOOGLE_MODELS = [
  { value: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash' },
  { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' }
];

const OPENAI_MODELS = [
  { value: 'gpt-4', label: 'GPT-4' },
  { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
  { value: 'gpt-4o', label: 'GPT-4o' },
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
];

// Provider definitions with their characteristics
const PROVIDERS = {
  google: {
    label: 'Google (Gemini)',
    models: GOOGLE_MODELS,
    requiresApiKey: true,
    apiKeyField: 'google_api_key',
    apiKeyLabel: 'Google API 密钥',
    defaultModel: 'gemini-2.0-flash-exp'
  },
  openai: {
    label: 'OpenAI (GPT)',
    models: OPENAI_MODELS,
    requiresApiKey: true,
    apiKeyField: 'openai_api_key',
    apiKeyLabel: 'OpenAI API 密钥',
    defaultModel: 'gpt-4o-mini'
  },
  lmstudio: {
    label: '本地 AI 模型 (LM Studio, Ollama 等)',
    requiresApiKey: false,
    requiresModelInput: true,
    defaultBaseUrl: 'http://localhost:1234',
    defaultModel: 'local-model',
    isLocal: true
  }
};

const AgentConfigModal = ({ agent, onClose, onSave }) => {
  const [config, setConfig] = useState(agent?.config || {
    name: '',
    description: '',
    provider: 'google',
    model: 'gemini-2.0-flash-exp',
    system_prompt: '',
    temperature: 0.7,
    max_tokens: null,
    google_api_key: null,
    openai_api_key: null,
    api_base_url: null,
    openai_base_url: null, // Keep for backward compatibility
    mcp_servers: [],
    capabilities: [],
    metadata: {}
  });

  // State for custom model name input (for local providers)
  const [customModel, setCustomModel] = useState(() => {
    if (!agent?.config?.model || !agent?.config?.provider) return '';
    if (agent.config.provider === 'lmstudio' || agent.config.provider === 'localai' || 
        agent.config.provider === 'ollama' || agent.config.provider === 'textgen-webui' || 
        agent.config.provider === 'custom') {
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

  const [urlWarning, setUrlWarning] = useState('');

  // Track if mouse was pressed on overlay for proper drag handling
  const overlayClickStarted = React.useRef(false);
  
  // Track timeout for clearing URL warning
  const warningTimeoutRef = React.useRef(null);

  // Cleanup warning timeout on unmount
  React.useEffect(() => {
    return () => {
      if (warningTimeoutRef.current) {
        clearTimeout(warningTimeoutRef.current);
      }
    };
  }, []);

  // Helper function to clean and validate base URL
  const handleBaseUrlChange = (value) => {
    let cleanedUrl = value || null;
    let warning = '';
    
    if (cleanedUrl && cleanedUrl.endsWith('/v1')) {
      // Auto-remove /v1 suffix and show warning
      cleanedUrl = cleanedUrl.replace(/\/v1$/, '');
      warning = '⚠️ 已自动移除 /v1 后缀 - OpenAI SDK 会自动添加';
    }
    
    setUrlWarning(warning);
    setConfig({ ...config, api_base_url: cleanedUrl });
    
    // Clear warning after 3 seconds, clearing any previous timeout
    if (warning) {
      if (warningTimeoutRef.current) {
        clearTimeout(warningTimeoutRef.current);
      }
      warningTimeoutRef.current = setTimeout(() => setUrlWarning(''), 3000);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(config);
  };

  const addMcpServer = () => {
    if (newMcpServer.name && newMcpServer.command) {
      setConfig({
        ...config,
        mcp_servers: [...config.mcp_servers, { ...newMcpServer }]
      });
      setNewMcpServer({ name: '', command: '', args: [], env: {} });
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
              <select
                value={config.provider}
                onChange={(e) => handleProviderChange(e.target.value)}
              >
                {Object.entries(PROVIDERS).map(([key, provider]) => (
                  <option key={key} value={key}>{provider.label}</option>
                ))}
              </select>
            </div>

            {!isLocalProvider && (
              <div className="form-group">
                <label>模型 *</label>
                <select
                  value={config.model}
                  onChange={(e) => handleModelChange(e.target.value)}
                >
                  {providerInfo.models.map(model => (
                    <option key={model.value} value={model.value}>{model.label}</option>
                  ))}
                </select>
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

            {config.provider === 'google' && (
              <div className="form-group">
                <label>Google API 密钥 (可选)</label>
                <input
                  type="password"
                  value={config.google_api_key || ''}
                  onChange={(e) => setConfig({ ...config, google_api_key: e.target.value || null })}
                  placeholder="留空则使用 .env 文件中的全局 API 密钥"
                />
                <small className="form-hint">
                  单个 Agent 的 API 密钥会覆盖全局 GOOGLE_API_KEY 设置
                </small>
              </div>
            )}

            {config.provider === 'openai' && (
              <div className="form-group">
                <label>OpenAI API 密钥 (可选)</label>
                <input
                  type="password"
                  value={config.openai_api_key || ''}
                  onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value || null })}
                  placeholder="留空则使用 .env 文件中的全局 API 密钥"
                />
                <small className="form-hint">
                  单个 Agent 的 API 密钥会覆盖全局 OPENAI_API_KEY 设置
                </small>
              </div>
            )}

            {isLocalProvider && (
              <div className="form-group">
                <label>API 基础 URL *</label>
                <input
                  type="text"
                  value={config.api_base_url || ''}
                  onChange={(e) => handleBaseUrlChange(e.target.value)}
                  placeholder={providerInfo.defaultBaseUrl || 'http://localhost:8080'}
                  required
                />
                <small className="form-hint">
                  {providerInfo.defaultBaseUrl 
                    ? `默认值: ${providerInfo.defaultBaseUrl} (不要包含 /v1 后缀)` 
                    : '输入您的 OpenAI 兼容 API 端点的基础 URL (不要包含 /v1 后缀)'}
                </small>
                {urlWarning && (
                  <small className="form-hint" style={{ color: '#ff9800', fontWeight: 'bold' }}>
                    {urlWarning}
                  </small>
                )}
              </div>
            )}

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
            
            {config.mcp_servers.map((server, index) => (
              <div key={index} className="mcp-server-item">
                <div>
                  <strong>{server.name}</strong>
                  <div className="server-command">{server.command}</div>
                </div>
                <button
                  type="button"
                  className="btn btn-icon btn-danger"
                  onClick={() => removeMcpServer(index)}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}

            <div className="add-mcp-server">
              <div className="form-group">
                <input
                  type="text"
                  value={newMcpServer.name}
                  onChange={(e) => setNewMcpServer({ ...newMcpServer, name: e.target.value })}
                  placeholder="服务器名称"
                />
              </div>
              <div className="form-group">
                <input
                  type="text"
                  value={newMcpServer.command}
                  onChange={(e) => setNewMcpServer({ ...newMcpServer, command: e.target.value })}
                  placeholder="命令 (例如: npx, python)"
                />
              </div>
              <button type="button" className="btn btn-secondary" onClick={addMcpServer}>
                <Plus size={16} /> 添加服务器
              </button>
            </div>
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
