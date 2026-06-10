with open('frontend/src/components/AgentConfigModal.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加压缩模型选项
compression_models = '''

// Compression models (small/fast models for context compression)
const COMPRESSION_MODELS = [
  { value: 'gpt-4o-mini', label: 'GPT-4o Mini (推荐)' },
  { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
  { value: 'deepseek-chat-v4', label: 'DeepSeek Chat V4' },
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' },
  { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
  { value: 'local-model', label: '本地模型' }
];'''

# 在 PROVIDERS 定义后添加压缩模型
content = content.replace('};', '};\n' + compression_models)

# 添加默认配置中的压缩设置
old_default_config = '''return agent?.config || {
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
    };'''

new_default_config = '''return agent?.config || {
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
      metadata: {},
      rag_enabled: false,
      compression: {
        enabled: false,
        provider: 'openai',
        model: 'gpt-4o-mini',
        api_key: null,
        base_url: null,
        max_tokens: 500,
        temperature: 0.3,
        target_ratio: 0.3
      }
    };'''

content = content.replace(old_default_config, new_default_config)

# 在 MCP 服务器部分之后添加 RAG 配置部分
old_mcp_section_end = '''              <button type="button" className="btn btn-secondary" onClick={addMcpServer}>
                <Plus size={16} /> 添加 MCP 服务器
              </button>
            </div>
          </div>

          <div className="modal-footer">'''

new_rag_section = '''              <button type="button" className="btn btn-secondary" onClick={addMcpServer}>
                <Plus size={16} /> 添加 MCP 服务器
              </button>
            </div>
          </div>

          <div className="form-section">
            <h3>RAG 配置</h3>
            <p className="form-help-text">配置检索增强生成 (RAG) 和上下文压缩功能。</p>
            
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.rag_enabled || false}
                  onChange={(e) => setConfig({ ...config, rag_enabled: e.target.checked })}
                />
                启用 RAG 记忆系统
              </label>
              <small className="form-hint">启用后，Agent 将使用向量数据库存储和检索对话历史</small>
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={config.compression?.enabled || false}
                  onChange={(e) => setConfig({ 
                    ...config, 
                    compression: { 
                      ...config.compression, 
                      enabled: e.target.checked 
                    } 
                  })}
                />
                启用上下文压缩
              </label>
              <small className="form-hint">使用小模型压缩长对话历史，减少 token 消耗</small>
            </div>

            {(config.compression?.enabled || false) && (
              <div className="compression-settings">
                <div className="form-group">
                  <label>压缩模型</label>
                  <select
                    value={config.compression?.model || 'gpt-4o-mini'}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      compression: { 
                        ...config.compression, 
                        model: e.target.value 
                      } 
                    })}
                  >
                    {COMPRESSION_MODELS.map(model => (
                      <option key={model.value} value={model.value}>{model.label}</option>
                    ))}
                  </select>
                </div>

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
                  <label>压缩 API 基础 URL (可选)</label>
                  <input
                    type="text"
                    value={config.compression?.base_url || ''}
                    onChange={(e) => setConfig({ 
                      ...config, 
                      compression: { 
                        ...config.compression, 
                        base_url: e.target.value || null 
                      } 
                    })}
                    placeholder="例如: https://api.deepseek.com/v1"
                  />
                  <small className="form-hint">用于指定非默认的 API 端点</small>
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

          <div className="modal-footer">'''

content = content.replace(old_mcp_section_end, new_rag_section)

with open('frontend/src/components/AgentConfigModal.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("AgentConfigModal updated with RAG and compression settings!")