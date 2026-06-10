with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加 RAG 路由导入
old_imports = '''from backend.api import mcp_router
from backend.api.agents_a2a import router as agents_router
from backend.api.agent_capabilities import router as capabilities_router'''

new_imports = '''from backend.api import mcp_router
from backend.api.agents_a2a import router as agents_router
from backend.api.agent_capabilities import router as capabilities_router
from backend.api.rag import router as rag_router'''

content = content.replace(old_imports, new_imports)

# 添加 RAG 路由注册
old_routers = '''# Include routers
app.include_router(agents_router)
app.include_router(capabilities_router)
app.include_router(mcp_router)'''

new_routers = '''# Include routers
app.include_router(agents_router)
app.include_router(capabilities_router)
app.include_router(mcp_router)
app.include_router(rag_router)'''

content = content.replace(old_routers, new_routers)

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("main.py updated with RAG routes!")