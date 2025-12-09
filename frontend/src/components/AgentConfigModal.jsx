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

const AgentConfigModal = ({ agent, onClose, onSave }) => {
  const [config, setConfig] = useState(agent?.config || {
    name: '',
    description: '',
    provider: 'google',
    model: 'gemini-2.0-flash-exp',
    system_prompt: '',
    temperature: 0.7,
    max_tokens: null,
    mcp_servers: [],
    capabilities: [],
    metadata: {}
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
                onChange={(e) => {
                  const provider = e.target.value;
                  const defaultModel = provider === 'openai' 
                    ? OPENAI_MODELS[0].value 
                    : GOOGLE_MODELS[0].value;
                  setConfig({ ...config, provider, model: defaultModel });
                }}
              >
                <option value="google">Google (Gemini)</option>
                <option value="openai">OpenAI (GPT)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Model *</label>
              <select
                value={config.model}
                onChange={(e) => setConfig({ ...config, model: e.target.value })}
              >
                {config.provider === 'google' 
                  ? GOOGLE_MODELS.map(model => (
                      <option key={model.value} value={model.value}>{model.label}</option>
                    ))
                  : OPENAI_MODELS.map(model => (
                      <option key={model.value} value={model.value}>{model.label}</option>
                    ))
                }
              </select>
            </div>

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
