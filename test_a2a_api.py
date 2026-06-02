#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for A2A Multi-Agent System
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_health():
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_list_agents():
    print("\n=== Testing List Agents Endpoint ===")
    try:
        response = requests.get(f"{BASE_URL}/api/agents/", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_agent():
    print("\n=== Testing Create Agent Endpoint ===")
    agent_config = {
        "name": "TestAgent",
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are a helpful assistant.",
        "temperature": 0.7,
        "max_tokens": 1000,
        "mcp_servers": []
    }
    payload = {"config": agent_config}

    try:
        response = requests.post(
            f"{BASE_URL}/api/agents/",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        if response.status_code == 200:
            return response.json().get("id")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_send_message(agent_id):
    print(f"\n=== Testing Send Message to Agent: {agent_id} ===")
    payload = {
        "agent_id": agent_id,
        "message": "Hello! Can you introduce yourself?"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/agents/message",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_agent_card(agent_id):
    print(f"\n=== Testing Agent Card for: {agent_id} ===")
    try:
        response = requests.get(
            f"{BASE_URL}/api/agents/{agent_id}/.well-known/agent-card.json",
            timeout=5
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            card = response.json()
            print(f"Agent Name: {card.get('name', 'N/A')}")
            print(f"Description: {card.get('description', 'N/A')}")
            print(f"Version: {card.get('version', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_collaborate():
    print("\n=== Testing Multi-Agent Collaboration ===")

    agent1_config = {
        "name": "Coordinator",
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are a coordinator agent that helps coordinate tasks.",
        "temperature": 0.7,
        "max_tokens": 1000,
        "mcp_servers": []
    }
    agent2_config = {
        "name": "Worker",
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "system_prompt": "You are a worker agent that executes tasks.",
        "temperature": 0.7,
        "max_tokens": 1000,
        "mcp_servers": []
    }

    try:
        response1 = requests.post(
            f"{BASE_URL}/api/agents/",
            json={"config": agent1_config},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response2 = requests.post(
            f"{BASE_URL}/api/agents/",
            json={"config": agent2_config},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response1.status_code != 200 or response2.status_code != 200:
            print("Failed to create agents for collaboration")
            return False

        agent1_id = response1.json().get("id")
        agent2_id = response2.json().get("id")
        print(f"Created agents: {agent1_id}, {agent2_id}")

        payload = {
            "agents": [agent1_id, agent2_id],
            "task": "Write a haiku about artificial intelligence",
            "coordinator_agent": agent1_id,
            "max_rounds": 2
        }

        response = requests.post(
            f"{BASE_URL}/api/agents/collaborate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )

        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200

    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 60)
    print("A2A Multi-Agent System Test Suite")
    print("=" * 60)

    if not test_health():
        print("\n[FAIL] Backend is not running or not accessible")
        print("   Please start the backend with: python run_backend.py")
        return

    print("\n[PASS] Backend is accessible")

    test_list_agents()

    agent_id = test_create_agent()

    if agent_id:
        test_agent_card(agent_id)
        test_send_message(agent_id)

    test_collaborate()

    print("\n" + "=" * 60)
    print("Test Suite Completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
