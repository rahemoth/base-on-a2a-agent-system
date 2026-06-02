import requests
import json

print("=" * 60)
print("测试 DeepSeek V4 Agent")
print("=" * 60)

# 1. 创建 DeepSeek V4 Flash Agent
print("\n1. 创建 DeepSeek V4 Flash Agent...")
data = {
    "config": {
        "name": "DeepSeek-V4",
        "description": "测试 DeepSeek V4 模型",
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "temperature": 0.7,
        "system_prompt": "You are a helpful AI assistant."
    }
}

try:
    response = requests.post("http://localhost:8000/api/agents/", json=data, timeout=30)
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        agent = response.json()
        agent_id = agent["id"]
        print(f"Agent ID: {agent_id}")
        print(f"Agent 名称: {agent['config']['name']}")
        print(f"模型: {agent['config']['model']}")
        
        # 2. 发送消息测试
        print("\n2. 发送测试消息...")
        message_data = {
            "agent_id": agent_id,
            "message": "Hello! Please introduce yourself.",
            "stream": False
        }
        
        response = requests.post("http://localhost:8000/api/agents/message", json=message_data, timeout=120)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "No response")
            print(f"\nAgent 响应:")
            print("-" * 60)
            print(response_text)
            print("-" * 60)
            
            # 检查是否为模拟响应
            if "Mock Response" in response_text or "Agent processed your request" in response_text:
                print("\nWARNING: Agent returned mock response.")
            else:
                print("\nSUCCESS! DeepSeek V4 Agent is working correctly!")
        else:
            print(f"错误: {response.text}")
    else:
        print(f"创建失败: {response.text}")
        
except Exception as e:
    print(f"错误: {e}")

print("\n" + "=" * 60)