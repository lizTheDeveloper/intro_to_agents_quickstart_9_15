"""
LM Studio client for First Mate Agent using OpenAI-compatible API
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
from .config import config
from .logger import logger


class LMStudioClient:
    """Client for interacting with LM Studio via OpenAI-compatible API"""
    
    def __init__(self):
        self.client = OpenAI(
            base_url=config.lm_studio.base_url,
            api_key=config.lm_studio.api_key
        )
        self.model_name = config.lm_studio.model
        self.temperature = config.lm_studio.temperature
        self.max_tokens = config.lm_studio.max_tokens
        logger.info(f"LM Studio client initialized with model: {self.model_name}")
    
    def test_connection(self) -> bool:
        """Test connection to LM Studio"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello, are you working?"}],
                max_tokens=50,
                temperature=0.1
            )
            logger.info("LM Studio connection test successful")
            return True
        except Exception as error:
            logger.error(f"LM Studio connection test failed: {error}")
            return False
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a chat completion using OpenAI-compatible API"""
        try:
            completion_params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens
            }
            
            if tools:
                completion_params["tools"] = tools
                completion_params["tool_choice"] = tool_choice
            
            response = self.client.chat.completions.create(**completion_params)
            
            result = {
                "content": response.choices[0].message.content,
                "tool_calls": response.choices[0].message.tool_calls,
                "usage": response.usage,
                "model": response.model
            }
            
            logger.debug(f"Chat completion successful, tokens used: {response.usage.total_tokens}")
            return result
            
        except Exception as error:
            logger.error(f"Chat completion failed: {error}")
            raise
    
    def consolidate_context(self, messages: List[Dict[str, str]]) -> str:
        """Consolidate context using LM Studio"""
        try:
            consolidation_prompt = (
                "Consolidate the following conversation messages into a single, "
                "comprehensive summary. Preserve all important information, decisions, "
                "and context. Do not lose any details:\n\n"
                + "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            )
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": consolidation_prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            logger.info("Context consolidation completed")
            return response.choices[0].message.content
            
        except Exception as error:
            logger.error(f"Context consolidation failed: {error}")
            raise


# Global client instance
lm_client = LMStudioClient()
