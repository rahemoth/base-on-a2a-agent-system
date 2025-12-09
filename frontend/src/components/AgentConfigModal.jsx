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

// Common models for local providers - users can enter any model name
const LOCAL_MODELS = [
  { value: 'custom', label: 'Enter custom model name...' }
];

// Provider definitions with their characteristics
const PROVIDERS = {
  google: {
    label: 'Google (Gemini)',
    models: GOOGLE_MODELS,
    requiresApiKey: true,
    apiKeyField: 'google_api_key',
    apiKeyLabel: 'Google API Key',
    defaultModel: 'gemini-2.0-flash-exp'
  },
  openai: {
    label: 'OpenAI (GPT)',
    models: OPENAI_MODELS,
    requiresApiKey: true,
    apiKeyField: 'openai_api_key',
    apiKeyLabel: 'OpenAI API Key',
    defaultModel: 'gpt-4o-mini'
  },
  lmstudio: {
    label: 'LM Studio',
    models: LOCAL_MODELS,
    requiresApiKey: false,
    defaultBaseUrl: 'http://localhost:1234/v1',
    defaultModel: 'local-model'
  },
  localai: {
    label: 'LocalAI',
    models: LOCAL_MODELS,
    requiresApiKey: false,
    defaultBaseUrl: 'http://localhost:8080/v1',
    defaultModel: 'local-model'
  },
  ollama: {
    label: 'Ollama',
    models: LOCAL_MODELS,
    requiresApiKey: false,
    defaultBaseUrl: 'http://localhost:11434/v1',
    defaultModel: 'llama2'
  },
  'textgen-webui': {
    label: 'Text Generation WebUI',
    models: LOCAL_MODELS,
    requiresApiKey: false,
    defaultBaseUrl: 'http://localhost:5000/v1',
    defaultModel: 'local-model'
  },
  custom: {
    label: 'Custom (OpenAI-compatible)',
    models: LOCAL_MODELS,
    requiresApiKey: false,
    requiresBaseUrl: true,
    defaultModel: 'custom-model'
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

  // State for custom model name input
  const [customModel, setCustomModel] = useState(() => {
    if (!agent?.config?.model || !agent?.config?.provider) return '';
    const provider = PROVIDERS[agent.config.provider];
    if (!provider) return '';
    const modelExists = provider.models.find(m => m.value === agent.config.model);
    return modelExists ? '' : agent.config.model;
  });

  const [newMcpServer, setNewMcpServer] = useState({
    name: '',
    command: '',
    args: [],
    env: {}
  });

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
    }
    
    setConfig(newConfig);
    // For local providers, initialize customModel with the default model name
    if (providerInfo.models[0]?.value === 'custom') {
      setCustomModel(providerInfo.defaultModel);
    } else {
      setCustomModel('');
    }
  };

  const handleModelChange = (newModel) => {
    if (newModel === 'custom') {
      setConfig({ ...config, model: customModel || 'custom-model' });
    } else {
      setConfig({ ...config, model: newModel });
      setCustomModel('');
    }
  };

  const handleCustomModelChange = (value) => {
    setCustomModel(value);
    setConfig({ ...config, model: value || 'custom-model' });
  };

  const currentProvider = PROVIDERS[config.provider];
  if (!currentProvider) {
    console.error(`Invalid provider: ${config.provider}`);
    // Fallback to google but log the error
  }
  const providerInfo = currentProvider || PROVIDERS.google;
  const showCustomModelInput = config.model === 'custom' || 
    (providerInfo.models[0]?.value === 'custom');
  const isLocalProvider = !providerInfo.requiresApiKey;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{agent ? 'Configure Agent' : 'Create New Agent'}</h2>
          <button className="btn-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-section">
            <h3>Basic Information</h3>
            
            <div className="form-group">
              <label>Agent Name *</label>
              <input
                type="text"
                value={config.name}
                onChange={(e) => setConfig({ ...config, name: e.target.value })}
                placeholder="My AI Agent"
                required
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <textarea
                value={config.description}
                onChange={(e) => setConfig({ ...config, description: e.target.value })}
                placeholder="Describe what this agent does..."
                rows={3}
              />
            </div>

            <div className="form-group">
              <label>Provider *</label>
              <select
                value={config.provider}
                onChange={(e) => handleProviderChange(e.target.value)}
              >
                {Object.entries(PROVIDERS).map(([key, provider]) => (
                  <option key={key} value={key}>{provider.label}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Model *</label>
              <select
                value={providerInfo.models[0]?.value === 'custom' ? 'custom' : config.model}
                onChange={(e) => handleModelChange(e.target.value)}
              >
                {providerInfo.models.map(model => (
                  <option key={model.value} value={model.value}>{model.label}</option>
                ))}
              </select>
            </div>

            {showCustomModelInput && (
              <div className="form-group">
                <label>Model Name *</label>
                <input
                  type="text"
                  value={customModel}
                  onChange={(e) => handleCustomModelChange(e.target.value)}
                  placeholder="Enter model name (e.g., llama2, mistral, etc.)"
                  required
                />
                <small className="form-hint">
                  Enter the exact model name as configured in your local LLM server
                </small>
              </div>
            )}

            {config.provider === 'google' && (
              <div className="form-group">
                <label>Google API Key (Optional)</label>
                <input
                  type="password"
                  value={config.google_api_key || ''}
                  onChange={(e) => setConfig({ ...config, google_api_key: e.target.value || null })}
                  placeholder="Leave empty to use global API key from .env"
                />
                <small className="form-hint">
                  Per-agent API key overrides the global GOOGLE_API_KEY setting
                </small>
              </div>
            )}

            {config.provider === 'openai' && (
              <div className="form-group">
                <label>OpenAI API Key (Optional)</label>
                <input
                  type="password"
                  value={config.openai_api_key || ''}
                  onChange={(e) => setConfig({ ...config, openai_api_key: e.target.value || null })}
                  placeholder="Leave empty to use global API key from .env"
                />
                <small className="form-hint">
                  Per-agent API key overrides the global OPENAI_API_KEY setting
                </small>
              </div>
            )}

            {isLocalProvider && (
              <div className="form-group">
                <label>API Base URL {providerInfo.requiresBaseUrl ? '*' : ''}</label>
                <input
                  type="text"
                  value={config.api_base_url || ''}
                  onChange={(e) => setConfig({ ...config, api_base_url: e.target.value || null })}
                  placeholder={providerInfo.defaultBaseUrl || 'http://localhost:8080/v1'}
                  required={providerInfo.requiresBaseUrl}
                />
                <small className="form-hint">
                  {providerInfo.defaultBaseUrl 
                    ? `Default: ${providerInfo.defaultBaseUrl}` 
                    : 'Enter the base URL for your OpenAI-compatible API endpoint'}
                </small>
              </div>
            )}

            <div className="form-group">
              <label>System Prompt</label>
              <textarea
                value={config.system_prompt || ''}
                onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
                placeholder="You are a helpful AI assistant..."
                rows={4}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Temperature</label>
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
                <label>Max Tokens</label>
                <input
                  type="number"
                  value={config.max_tokens || ''}
                  onChange={(e) => setConfig({ ...config, max_tokens: e.target.value ? parseInt(e.target.value) : null })}
                  placeholder="Auto"
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h3>MCP Servers</h3>
            
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
                  placeholder="Server name"
                />
              </div>
              <div className="form-group">
                <input
                  type="text"
                  value={newMcpServer.command}
                  onChange={(e) => setNewMcpServer({ ...newMcpServer, command: e.target.value })}
                  placeholder="Command (e.g., npx, python)"
                />
              </div>
              <button type="button" className="btn btn-secondary" onClick={addMcpServer}>
                <Plus size={16} /> Add Server
              </button>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              {agent ? 'Update Agent' : 'Create Agent'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AgentConfigModal;
