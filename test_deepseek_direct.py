import asyncio
from openai import AsyncOpenAI

async def test_deepseek():
    print("=" * 60)
    print("直接测试 DeepSeek API")
    print("=" * 60)
    
    client = AsyncOpenAI(
        api_key="sk-fc0744f4f16e430e8722860e1c6ab0f7",
        base_url="https://api.deepseek.com/v1"
    )
    
    try:
        print("\n发送请求到 DeepSeek API...")
        response = await client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "Hello! Please introduce yourself."}
            ],
            temperature=0.7
        )
        
        print(f"\n状态: 成功")
        print(f"模型: {response.model}")
        print(f"响应:")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)
        print("\nSUCCESS! DeepSeek API is working correctly!")
        
    except Exception as e:
        print(f"\n错误: {e}")
    
    print("\n" + "=" * 60)

asyncio.run(test_deepseek())