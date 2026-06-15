"""
Test RAG Semantic Search Integration
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.memory import AgentMemory


async def test_semantic_search():
    """Test semantic search functionality"""
    
    print("="*60)
    print("RAG Semantic Search Test")
    print("="*60)
    
    # Create memory instance
    memory = AgentMemory(agent_id="test-semantic", db_path="./data/test_semantic.db")
    await memory.initialize()
    
    # Test data
    test_memories = [
        ("role", "用户设定AI角色为: 猫娘", 1.0),
        ("conversation", "意图:身份 | 身份:我是你的猫娘助手 | 用户:你是谁", 0.5),
        ("conversation", "意图:创作 | AI:星光下的猫娘契约 | 用户:写一篇小说", 0.5),
        ("conversation", "意图:个人信息 | 用户:我的生日是6月11日", 0.7),
        ("conversation", "角色:助手 | 用户:你是我的AI助手", 0.5),
    ]
    
    print("\n[SETUP] Adding test memories...")
    for mem_type, content, importance in test_memories:
        await memory.add_to_long_term(
            memory_type=mem_type,
            content=content,
            importance=importance
        )
        print(f"  Added: {content[:50]}...")
    
    print(f"\n[INFO] RAG indexed documents: {memory.rag_system.retrieval_system.get_stats()['num_documents']}")
    
    # Test semantic search
    print("\n[TEST 1] Search: '你是谁'")
    print("-"*40)
    results = await memory.semantic_search("你是谁", top_k=3)
    for i, r in enumerate(results):
        print(f"  [{i+1}] Similarity: {r['similarity']:.2f} | {r['content'][:50]}...")
    
    print("\n[TEST 2] Search: '猫娘'")
    print("-"*40)
    results = await memory.semantic_search("猫娘", top_k=3)
    for i, r in enumerate(results):
        print(f"  [{i+1}] Similarity: {r['similarity']:.2f} | {r['content'][:50]}...")
    
    print("\n[TEST 3] Search: '写小说'")
    print("-"*40)
    results = await memory.semantic_search("写小说", top_k=3)
    for i, r in enumerate(results):
        print(f"  [{i+1}] Similarity: {r['similarity']:.2f} | {r['content'][:50]}...")
    
    print("\n[TEST 4] Search: '生日'")
    print("-"*40)
    results = await memory.semantic_search("生日", top_k=3)
    for i, r in enumerate(results):
        print(f"  [{i+1}] Similarity: {r['similarity']:.2f} | {r['content'][:50]}...")
    
    print("\n[TEST 5] Search with role filter")
    print("-"*40)
    results = await memory.semantic_search("猫娘", top_k=3, memory_type="role")
    print(f"  Found {len(results)} role memories")
    for i, r in enumerate(results):
        print(f"  [{i+1}] Similarity: {r['similarity']:.2f} | {r['content'][:50]}...")
    
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_semantic_search())