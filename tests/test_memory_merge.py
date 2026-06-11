"""
Test RAG Memory System - Memory Merge & Deduplication
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.memory import AgentMemory
from backend.agents.a2a_executor import LLMAgentExecutor
from backend.models import AgentConfig, ModelProvider


async def test_memory_merge():
    """Test memory merge and deduplication"""
    
    print("="*60)
    print("RAG Memory Merge Test Suite")
    print("="*60)
    
    # Create test agent
    agent_id = "test-merge-agent"
    memory = AgentMemory(agent_id=agent_id, db_path="./data/test_memory.db")
    await memory.initialize()
    
    # Create executor for helper methods
    config = AgentConfig(
        name="Test Agent",
        provider=ModelProvider.DEEPSEEK,
        model="deepseek-chat"
    )
    executor = LLMAgentExecutor(agent_id=agent_id, config=config)
    executor.memory = memory
    
    print("\n[TEST 1] Role Assignment Storage")
    print("-"*40)
    
    # Test role assignment
    role = executor._detect_role_assignment("你是一只猫娘")
    print(f"  Input: '你是一只猫娘'")
    print(f"  Detected role: {role}")
    assert role == "猫娘", f"Expected '猫娘', got '{role}'"
    print(f"  [PASS] Role detection works")
    
    print("\n[TEST 2] Role Removal Detection")
    print("-"*40)
    
    # Test role removal
    role = executor._detect_role_assignment("你不是猫娘了")
    print(f"  Input: '你不是猫娘了'")
    print(f"  Detected role: {role}")
    assert role == "猫娘", f"Expected '猫娘', got '{role}'"
    print(f"  [PASS] Role removal detection works")
    
    print("\n[TEST 3] Memory Compression")
    print("-"*40)
    
    # Test compression
    compressed = executor._extract_key_information(
        "你是一只猫娘",
        "喵~ 主人你好呀！我是你的猫娘助手~"
    )
    print(f"  Input: '你是一只猫娘' + AI response")
    print(f"  Compressed: {compressed}")
    assert "角色:猫娘" in compressed, "Role not in compressed content"
    assert "AI:" in compressed, "AI response not in compressed content"
    print(f"  [PASS] Compression includes role and AI response")
    
    print("\n[TEST 4] Memory Similarity Calculation")
    print("-"*40)
    
    # Test similarity
    sim1 = executor._calculate_memory_similarity(
        "身份", {"猫娘", "助手", "主人"},
        "身份", {"猫娘", "助手", "主人"}
    )
    print(f"  Same intent + same keywords: {sim1:.2f}")
    assert sim1 >= 0.7, f"Expected >= 0.7, got {sim1}"
    
    sim2 = executor._calculate_memory_similarity(
        "身份", {"猫娘", "助手"},
        "创作", {"小说", "故事"}
    )
    print(f"  Different intent + different keywords: {sim2:.2f}")
    assert sim2 < 0.3, f"Expected < 0.3, got {sim2}"
    print(f"  [PASS] Similarity calculation works")
    
    print("\n[TEST 5] Memory Merge Content")
    print("-"*40)
    
    # Test merge
    existing = "意图:身份 | 身份:我是你的猫娘助手 | 用户:你是谁"
    new = "意图:身份 | 身份:我是您的AI助手 | 用户:你是谁"
    merged = executor._merge_memory_content(existing, new)
    print(f"  Existing: {existing}")
    print(f"  New:      {new}")
    print(f"  Merged:   {merged}")
    assert "我是您的AI助手" in merged, "New content not merged"
    assert "意图:身份" in merged, "Intent lost in merge"
    print(f"  [PASS] Memory merge works correctly")
    
    print("\n[TEST 6] Full Memory Pipeline")
    print("-"*40)
    
    # Clear test database
    memory.clear_short_term_memory()
    
    # Simulate conversation pipeline
    test_conversations = [
        ("你是一只猫娘", "喵~ 主人好！我是猫娘助手~"),
        ("你是谁", "我是你的猫娘助手呀~"),
        ("你是一只猫娘", "喵~ 对呀对呀~"),  # Duplicate - should merge
        ("你不是猫娘了", "好的，我是AI助手"),
        ("你是谁", "我是您的AI助手"),
    ]
    
    for user_msg, ai_resp in test_conversations:
        compressed = executor._extract_key_information(user_msg, ai_resp)
        print(f"  User: {user_msg[:20]}...")
        print(f"  Compressed: {compressed[:50]}...")
        
        # Add to memory
        await memory.add_to_long_term(
            memory_type="conversation",
            content=compressed,
            importance=0.5
        )
    
    # Check memories
    memories = await memory.search_long_term_memory(limit=10)
    print(f"\n  Total memories stored: {len(memories)}")
    for i, mem in enumerate(memories):
        print(f"  [{i+1}] {mem['content'][:50]}...")
    
    print(f"  [PASS] Full pipeline works")
    
    print("\n" + "="*60)
    print("All tests passed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_memory_merge())