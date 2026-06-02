with open('backend/agents/a2a_executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复 settings 属性名（改为小写）
old_line = 'api_key = self.config.openai_api_key or self.config.google_api_key or settings.OPENAI_API_KEY or settings.GOOGLE_API_KEY'
new_line = 'api_key = self.config.openai_api_key or self.config.google_api_key or settings.openai_api_key or settings.google_api_key'

content = content.replace(old_line, new_line)

with open('backend/agents/a2a_executor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed settings attribute names!")