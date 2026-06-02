import requests
import json

# Test creating a Google agent
data = {
    "config": {
        "name": "test-agent",
        "provider": "google",
        "model": "gemini-2.0-flash-exp",
        "temperature": 0.7
    }
}

try:
    response = requests.post("http://localhost:8000/api/agents/", json=data)
    print(f"Google Agent - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print(f"Success: {response.json()}")
except Exception as e:
    print(f"Error: {e}")

# Test creating a DeepSeek agent
data_deepseek = {
    "config": {
        "name": "test-deepseek-agent",
        "provider": "deepseek",
        "model": "deepseek-chat-v4.5",
        "temperature": 0.7
    }
}

try:
    response = requests.post("http://localhost:8000/api/agents/", json=data_deepseek)
    print(f"\nDeepSeek Agent - Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
    else:
        print(f"Success: {response.json()}")
except Exception as e:
    print(f"Error: {e}")