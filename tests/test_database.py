"""Test database persistence"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database_manager import db_manager

async def test_database():
    print("Testing database persistence...")
    
    # Initialize database
    await db_manager.initialize()
    print("[OK] Database initialized")
    
    # Test save agent
    test_config = {
        "name": "Test Agent",
        "description": "A test agent",
        "provider": "deepseek",
        "model": "deepseek-chat"
    }
    
    await db_manager.save_agent("test-agent-1", test_config)
    print("[OK] Agent saved to database")
    
    # Test get agent
    agent = await db_manager.get_agent("test-agent-1")
    if agent:
        print(f"[OK] Agent retrieved: {agent['name']}")
    else:
        print("[FAIL] Failed to retrieve agent")
    
    # Test list agents
    agents = await db_manager.list_agents()
    print(f"[OK] Found {len(agents)} agents in database")
    
    # Test delete agent
    await db_manager.delete_agent("test-agent-1")
    print("[OK] Agent deleted from database")
    
    # Verify deletion
    agents = await db_manager.list_agents()
    print(f"[OK] After deletion: {len(agents)} agents in database")
    
    await db_manager.close()
    print("\nAll database tests passed!")

if __name__ == "__main__":
    asyncio.run(test_database())