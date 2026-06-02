with open('backend/agents/a2a_executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加 settings 导入
old_import = '''from backend.models import AgentConfig, ModelProvider
from backend.mcp import mcp_manager'''

new_import = '''from backend.models import AgentConfig, ModelProvider
from backend.mcp import mcp_manager
from backend.config import settings'''

content = content.replace(old_import, new_import)

with open('backend/agents/a2a_executor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed settings import!")