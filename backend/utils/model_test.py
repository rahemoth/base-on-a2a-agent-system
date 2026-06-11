"""
Utility functions for testing model connections
"""
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from google import genai

from backend.models import AgentConfig, ModelProvider

logger = logging.getLogger(__name__)

async def test_model_connection(config: AgentConfig) -> Dict[str, Any]:
    """
    Test if the model configuration is valid and can connect to the API.
    
    Args:
        config: AgentConfig containing provider, model, and API key information
    
    Returns:
        Dictionary with success status and message
    """
    try:
        provider = config.provider
        model = config.model
        
        logger.info(f"Testing model connection: {provider.value} - {model}")
        
        if provider == ModelProvider.GEMINI:
            api_key = config.google_api_key
            if not api_key:
                return {"success": False, "message": "Google API key is required"}
            
            try:
                client = genai.Client(api_key=api_key)
                # Test by listing models
                models = list(client.list_models())
                if models:
                    return {"success": True, "message": "Successfully connected to Gemini API"}
                return {"success": False, "message": "Connected but no models found"}
            except Exception as e:
                return {"success": False, "message": f"Gemini API error: {str(e)}"}
        
        elif provider in [ModelProvider.GPT, ModelProvider.DEEPSEEK, ModelProvider.KIMI, 
                          ModelProvider.MIMO, ModelProvider.MINIMAX, ModelProvider.GLM, 
                          ModelProvider.QWEN, ModelProvider.CLAUDE, ModelProvider.CUSTOM]:
            # Get API key based on provider
            api_key = None
            base_url = None
            
            if provider == ModelProvider.GPT:
                api_key = config.openai_api_key
                base_url = config.api_base_url or "https://api.openai.com/v1"
            elif provider == ModelProvider.CLAUDE:
                api_key = config.anthropic_api_key
                base_url = "https://api.anthropic.com/v1"
            elif provider == ModelProvider.DEEPSEEK:
                api_key = config.openai_api_key
                base_url = config.api_base_url or "https://api.deepseek.com/v1"
            elif provider == ModelProvider.KIMI:
                api_key = config.kimi_api_key
                base_url = config.api_base_url or "https://api.moonshot.cn/v1"
            elif provider == ModelProvider.MIMO:
                api_key = config.mimo_api_key
                base_url = config.api_base_url or "https://api.xiaomi.com/v1"
            elif provider == ModelProvider.MINIMAX:
                api_key = config.minimax_api_key
                base_url = config.api_base_url or "https://api.minimax.chat/v1/text/chatcompletion"
            elif provider == ModelProvider.GLM:
                api_key = config.zhipu_api_key
                base_url = config.api_base_url or "https://open.bigmodel.cn/api/paas/v4"
            elif provider == ModelProvider.QWEN:
                api_key = config.qwen_api_key
                base_url = config.api_base_url or "https://dashscope.aliyuncs.com/api/text-generation/v1"
            elif provider == ModelProvider.CUSTOM:
                api_key = config.openai_api_key
                base_url = config.api_base_url or "http://localhost:1234/v1"
            
            if not api_key and provider != ModelProvider.CUSTOM:
                return {"success": False, "message": "API key is required"}
            
            try:
                client = AsyncOpenAI(api_key=api_key or "dummy-key", base_url=base_url)
                
                # Test connection by calling list_models or creating a completion
                try:
                    # First try listing models
                    models = await client.models.list()
                    if models.data:
                        return {"success": True, "message": f"Successfully connected to {provider.value} API"}
                    return {"success": False, "message": "Connected but no models found"}
                except Exception as list_error:
                    # Some APIs don't support list_models, try a simple completion
                    try:
                        response = await client.chat.completions.create(
                            model=model,
                            messages=[{"role": "user", "content": "Hello"}],
                            max_tokens=10
                        )
                        if response.choices:
                            return {"success": True, "message": f"Successfully connected to {provider.value} API"}
                        return {"success": False, "message": "Connected but no response"}
                    except Exception as completion_error:
                        return {"success": False, "message": f"{provider.value} API error: {str(completion_error)}"}
            
            except Exception as client_error:
                return {"success": False, "message": f"Failed to create client: {str(client_error)}"}
        
        return {"success": False, "message": f"Unsupported provider: {provider.value}"}
    
    except Exception as e:
        logger.error(f"Error testing model connection: {str(e)}")
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
