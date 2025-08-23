"""
OpenAI fallback service for when Claude API is unavailable
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
import httpx

logger = logging.getLogger(__name__)


class OpenAIFallbackService:
    """Fallback to OpenAI when Claude is not available"""
    
    def __init__(self):
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.base_url = "https://api.openai.com/v1"
    
    @property
    def api_key(self):
        """Get API key at runtime, not import time"""
        return os.getenv("OPENAI_API_KEY")
    
    @property
    def enabled(self):
        """Check if service is enabled at runtime"""
        return bool(self.api_key)
        
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Chat completion using OpenAI API
        """
        if not self.enabled:
            return {
                "error": "OpenAI API key not configured",
                "response": "AI service not available. Please configure OpenAI API key."
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
            
        try:
            async with httpx.AsyncClient() as client:
                # Streaming not implemented yet for simplicity
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Convert to standard format
                return {
                    "response": data["choices"][0]["message"]["content"],
                    "done": True,
                    "model": self.model,
                    "usage": data.get("usage", {})
                }
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {
                "error": str(e),
                "response": "Failed to get AI response."
            }
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible"""
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False
    


# Global instance
openai_fallback = OpenAIFallbackService()