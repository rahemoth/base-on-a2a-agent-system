"""
Quick test to verify the agent message API is working
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.a2a_manager import a2a_agent_manager, A2AAgentManager
from backend.models import AgentConfig, ModelProvider
from a2a import types


async def test_send_message():
    """Test sending a message to an agent"""
    print("Testing A2A Agent Manager...")
    
    # Create a test agent config
    config = AgentConfig(
        name="Test Agent",
        provider=ModelProvider.DEEPSEEK,  # or any other provider
        model="deepseek-chat",
        system_prompt="You are a helpful assistant.",
        temperature=0.7
    )
    
    # Create agent
    print("Creating agent...")
    agent_response = await a2a_agent_manager.create_agent(config)
    agent_id = agent_response.id
    print(f"Agent created with ID: {agent_id}")
    
    # Send a test message
    print("\nSending test message...")
    try:
        response = await a2a_agent_manager.send_message(
            agent_id=agent_id,
            message_text="Hello, this is a test message."
        )
        
        print(f"Response type: {type(response).__name__}")
        
        if isinstance(response, types.Message):
            print(f"Response is a valid Message object")
            print(f"Response parts: {response.parts}")
            
            # Extract text
            from backend.utils.a2a_utils import extract_text_from_parts
            text = extract_text_from_parts(response.parts)
            print(f"Extracted text: {text[:100]}...")
            
            if "Agent processed your request" in text:
                print("\n⚠️ WARNING: Got fallback response instead of actual LLM response!")
                print("This means the event queue didn't return the expected message.")
            else:
                print("\n✅ SUCCESS: Got actual LLM response!")
        else:
            print(f"❌ ERROR: Response is not a Message object: {response}")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\nCleaning up...")
    await a2a_agent_manager.delete_agent(agent_id)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(test_send_message())