with open('frontend/src/components/AgentConfigModal.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_openai_key = '''            {config.provider === 'openai' && (
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
            )}'''

new_openai_and_deepseek_key = '''            {config.provider === 'openai' && (
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

            {config.provider === 'deepseek' && (
              <div className="form-group">
                <label>DeepSeek API 密钥 (可选)</label>
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
            )}'''

content = content.replace(old_openai_key, new_openai_and_deepseek_key)

with open('frontend/src/components/AgentConfigModal.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('DeepSeek API key input added!')