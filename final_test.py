# -*- coding: utf-8 -*-
import requests
import json
import sys

print("=" * 60)
print("DeepSeek V4 Agent 最终验证")
print("=" * 60)

# 1. 创建 DeepSeek V4 Flash Agent
print("\n[1/2] 创建 DeepSeek V4 Flash Agent...")
data = {
    "config": {
        "name": "DeepSeek-V4-Final",
        "description": "最终验证 DeepSeek V4 模型",
        "provider": "deepseek",
        "model": "deepseek-v4-flash",
        "temperature": 0.7,
        "system_prompt": "You are a helpful AI assistant."
    }
}

try:
    response = requests.post("http://localhost:8000/api/agents/", json=data, timeout=30)
    if response.status_code != 200:
        print(f"创建 Agent 失败: {response.status_code}")
        sys.exit(1)
    
    agent = response.json()
    agent_id = agent["id"]
    print(f"Agent ID: {agent_id}")
    print(f"模型: {agent['config']['model']}")
    
    # 2. 发送消息测试
    print("\n[2/2] 发送测试消息...")
    message_data = {
        "agent_id": agent_id,
        "message": "Hello! How are you today?",
        "stream": False
    }
    
    response = requests.post("http://localhost:8000/api/agents/message", json=message_data, timeout=120)
    if response.status_code != 200:
        print(f"发送消息失败: {response.status_code}")
        sys.exit(1)
    
    result = response.json()
    response_text = result.get("response", "")
    
    print(f"\n响应状态: 成功")
    print(f"响应长度: {len(response_text)} 字符")
    
    # 检查是否为真实响应
    if "Mock Response" in response_text or "Agent processed your request" in response_text:
        print("\n状态: 失败 - Agent 返回了模拟响应")
        sys.exit(1)
    else:
        print("\n状态: 成功!")
        print("\n响应内容预览:")
        print("-" * 60)
        # 尝试打印响应（如果包含特殊字符可能失败）
        try:
            print(response_text[:500])
        except:
            print("响应包含特殊字符，无法在终端显示")
        print("-" * 60)
        print("\n" + "=" * 60)
        print("SUCCESS! DeepSeek V4 Agent 正常工作!")
        print("=" * 60)
        
except Exception as e:
    print(f"\n错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)