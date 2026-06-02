import sys
sys.path.insert(0, '.')

from backend.config import settings

print("=" * 60)
print("调试 Settings 配置")
print("=" * 60)
print(f"google_api_key: {repr(settings.google_api_key)}")
print(f"openai_api_key: {repr(settings.openai_api_key)}")
print(f"openai_base_url: {repr(settings.openai_base_url)}")
print(f"port: {repr(settings.port)}")
print("=" * 60)

if settings.openai_api_key:
    print(f"\nAPI Key 已加载，长度: {len(settings.openai_api_key)}")
    print(f"API Key 前10位: {settings.openai_api_key[:10]}...")
else:
    print("\n警告: API Key 未加载!")
    print("请检查 .env 文件是否存在且 OPENAI_API_KEY 已设置")