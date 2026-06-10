with open('.env', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 OPENAI_API_KEY 后面添加压缩模型配置
old_section = '''OPENAI_API_KEY=sk-fc0744f4f16e430e8722860e1c6ab0f7

# OpenAI Configuration (Optional)'''

new_section = '''OPENAI_API_KEY=sk-fc0744f4f16e430e8722860e1c6ab0f7

# Compression Model Configuration (for RAG context compression)
COMPRESSION_API_KEY=
COMPRESSION_BASE_URL=
COMPRESSION_MODEL=gpt-4o-mini
COMPRESSION_MAX_TOKENS=500
COMPRESSION_TEMPERATURE=0.3

# RAG Configuration
RAG_ENABLED=true
RAG_COMPRESSION_TARGET=0.3
RAG_MAX_CONTEXT_CHUNKS=10
RAG_EMBEDDING_DIMENSION=768

# OpenAI Configuration (Optional)'''

content = content.replace(old_section, new_section)

with open('.env', 'w', encoding='utf-8') as f:
    f.write(content)

print(".env updated with compression and RAG settings!")