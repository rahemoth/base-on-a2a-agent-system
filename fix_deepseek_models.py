with open('frontend/src/components/AgentConfigModal.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

old_models = '''const DEEPSEEK_MODELS = [
  { value: 'deepseek-chat', label: 'DeepSeek Chat (V3)' },
  { value: 'deepseek-coder', label: 'DeepSeek Coder' },
  { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner' },
  { value: 'deepseek-chat-v4', label: 'DeepSeek Chat (V4)' },
  { value: 'deepseek-chat-v4.5', label: 'DeepSeek Chat (V4.5)' },
  { value: 'deepseek-chat-v4-turbo', label: 'DeepSeek Chat (V4 Turbo)' }
];'''

new_models = '''const DEEPSEEK_MODELS = [
  { value: 'deepseek-chat', label: 'DeepSeek Chat (V3)' },
  { value: 'deepseek-coder', label: 'DeepSeek Coder' },
  { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner' },
  { value: 'deepseek-v4-pro', label: 'DeepSeek V4 Pro' },
  { value: 'deepseek-v4-flash', label: 'DeepSeek V4 Flash' }
];'''

content = content.replace(old_models, new_models)

# 更新默认模型
old_default = '''    defaultModel: 'deepseek-chat-v4.5','''
new_default = '''    defaultModel: 'deepseek-chat','''

content = content.replace(old_default, new_default)

with open('frontend/src/components/AgentConfigModal.jsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("DeepSeek models updated!")