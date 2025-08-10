"""
AI Service Manager - Intelligent fallback system for AI services
Priority: Claude (best for education) → OpenAI (fallback)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from app.services.claude_service import claude_service
from app.services.openai_fallback import openai_fallback

logger = logging.getLogger(__name__)


class AIServiceManager:
    """Manages AI services with intelligent fallback"""
    
    def __init__(self):
        # Use the same services in dev and prod for consistency
        self.services = [
            ("Claude", claude_service),      # Primary: Best for education
            ("OpenAI", openai_fallback)      # Fallback: Reliable backup
        ]
        logger.info(f"AI Services initialized: {[name for name, _ in self.services]}")
    
    async def get_available_service(self):
        """Get the first available AI service"""
        for name, service in self.services:
            try:
                # Check if service is enabled and healthy
                if hasattr(service, 'enabled') and not service.enabled:
                    logger.debug(f"{name} service not enabled (no API key)")
                    continue
                
                if hasattr(service, 'health_check'):
                    is_healthy = await service.health_check()
                    if is_healthy:
                        logger.info(f"Using {name} service for AI chat")
                        return name, service
                    else:
                        logger.debug(f"{name} service health check failed")
                else:
                    # If no health check, assume it works if enabled
                    if hasattr(service, 'enabled') and service.enabled:
                        logger.info(f"Using {name} service for AI chat")
                        return name, service
            except Exception as e:
                logger.error(f"Error checking {name} service: {e}")
                continue
        
        logger.error("No AI services available!")
        return None, None
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        prefer_service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get chat completion from the best available service
        
        Args:
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
            stream: Whether to stream response
            prefer_service: Preferred service name (Claude, OpenAI)
        """
        
        # Try preferred service first if specified
        if prefer_service:
            for name, service in self.services:
                if name.lower() == prefer_service.lower():
                    try:
                        logger.info(f"Trying preferred service: {name}")
                        
                        # Call the service directly
                        result = await service.chat_completion(
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=stream
                        )
                        # For streaming, return the generator directly
                        if stream:
                            return result
                        # For non-streaming, check for errors
                        if not result.get("error"):
                            return result
                    except Exception as e:
                        logger.error(f"Preferred service {name} failed: {e}")
        
        # Fall back to priority order
        for name, service in self.services:
            try:
                logger.info(f"Trying {name} service...")
                
                # Check if service is enabled
                if hasattr(service, 'enabled') and not service.enabled:
                    continue
                
                result = await service.chat_completion(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream
                )
                
                if not result.get("error"):
                    logger.info(f"Successfully used {name} service")
                    return result
                else:
                    logger.warning(f"{name} returned error: {result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Error with {name} service: {e}")
                continue
        
        # All services failed
        logger.error("All AI services failed!")
        return {
            "error": "All AI services unavailable",
            "response": "I'm unable to connect to any AI service at the moment. Please try again later."
        }
    
    async def analyze_content(
        self,
        content: str,
        content_type: str,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Analyze content using the best available service"""
        
        # Try services in priority order
        for name, service in self.services:
            try:
                if hasattr(service, 'analyze_content'):
                    if hasattr(service, 'enabled') and service.enabled:
                        result = await service.analyze_content(content, content_type, instructions)
                        if not result.get("error"):
                            return result
            except Exception as e:
                logger.error(f"Error analyzing with {name}: {e}")
                continue
        
        return {
            "error": "Content analysis failed",
            "summary": "Unable to analyze content",
            "key_concepts": []
        }


# Global instance
ai_service_manager = AIServiceManager()