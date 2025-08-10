"""
Claude (Anthropic) service for superior educational AI interactions
Primary service for AI Study Architect based on research showing Claude's advantages:
- Built-in Socratic questioning approach
- Superior context window (200k tokens)
- Better safety for educational content
- More natural, human-like responses
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional, AsyncIterator
import httpx
from httpx import AsyncClient

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Anthropic's Claude API"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")  # Latest as of Nov 2024
        self.base_url = "https://api.anthropic.com/v1"
        self.enabled = bool(self.api_key)
        self.api_version = "2023-06-01"
        self.timeout = httpx.Timeout(60.0, connect=5.0)  # Claude can take longer for complex reasoning
        
    async def health_check(self) -> bool:
        """Check if Claude API is accessible"""
        if not self.enabled:
            return False
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/messages",
                    headers=self._get_headers(),
                    timeout=5.0
                )
                # Claude returns 405 for GET on messages endpoint, which means API is reachable
                return response.status_code in [405, 401, 403]
        except Exception as e:
            logger.error(f"Claude health check failed: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Claude API requests"""
        return {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json"
        }
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any] | AsyncIterator[str]:
        """
        Chat completion using Claude API
        
        Claude excels at:
        - Socratic questioning (asking clarifying questions)
        - Deep explanations with reasoning
        - Safe, educational content
        - Large context understanding
        """
        if not self.enabled:
            return {
                "error": "Claude API key not configured",
                "response": "Claude service not available. Please configure ANTHROPIC_API_KEY."
            }
        
        # Convert messages to Claude format
        # Claude expects system message separately
        system_message = None
        claude_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                # Combine multiple system messages if present
                if system_message:
                    system_message += "\n\n" + msg["content"]
                else:
                    system_message = msg["content"]
            else:
                # Claude uses "user" and "assistant" roles
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Ensure conversation starts with user message (Claude requirement)
        if not claude_messages or claude_messages[0]["role"] != "user":
            claude_messages.insert(0, {
                "role": "user",
                "content": "Please help me learn."
            })
        
        # Build request payload
        payload = {
            "model": self.model,
            "messages": claude_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096  # Claude default
        }
        
        # Add system message if present
        if system_message:
            payload["system"] = system_message
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if stream:
                    # Real streaming support for Claude
                    return self._stream_claude_response(client, payload)
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=self._get_headers(),
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Convert to standard format for compatibility
                return {
                    "response": data["content"][0]["text"],
                    "done": True,
                    "model": self.model,
                    "usage": {
                        "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                        "output_tokens": data.get("usage", {}).get("output_tokens", 0)
                    }
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Claude API HTTP error: {e.response.status_code} - {e.response.text}")
            
            # Parse error message
            try:
                error_data = e.response.json()
                error_message = error_data.get("error", {}).get("message", str(e))
            except:
                error_message = str(e)
            
            return {
                "error": f"Claude API error: {error_message}",
                "response": "Failed to get response from Claude."
            }
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "error": str(e),
                "response": "Failed to get AI response."
            }
    
    async def _stream_claude_response(self, client: AsyncClient, payload: Dict[str, Any]) -> AsyncIterator[str]:
        """Stream response from Claude API"""
        import json
        
        # Add streaming flag to payload
        payload["stream"] = True
        
        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                headers=self._get_headers(),
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        if data_str == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(data_str)
                            
                            # Claude streaming format
                            if data.get("type") == "content_block_delta":
                                text = data.get("delta", {}).get("text", "")
                                if text:
                                    # Return in standard streaming format
                                    yield json.dumps({
                                        "response": text,
                                        "done": False
                                    })
                            elif data.get("type") == "message_stop":
                                yield json.dumps({
                                    "response": "",
                                    "done": True
                                })
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse Claude stream: {data_str}")
                            continue
                            
        except Exception as e:
            logger.error(f"Claude streaming error: {e}")
            yield json.dumps({"error": str(e)})
    
    async def analyze_content(
        self,
        content: str,
        content_type: str,
        instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze educational content using Claude's superior reasoning
        
        Claude advantages:
        - Better at identifying key concepts
        - More thoughtful difficulty assessment
        - Generates better learning objectives
        """
        system_prompt = f"""You are an expert educational content analyzer using the AI Study Architect system.

Analyze this {content_type} content and extract insights that promote deep understanding, not surface-level memorization.

Focus on:
1. Core concepts that build foundational understanding
2. Common misconceptions students might have
3. Connections to prior knowledge
4. Questions that encourage critical thinking

Provide your analysis in JSON format:
{{
    "summary": "Brief summary focusing on key insights",
    "key_concepts": ["concept1", "concept2", ...],
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_study_time": "time in minutes",
    "learning_objectives": ["objective1", "objective2", ...],
    "suggested_prerequisites": ["prerequisite1", ...],
    "socratic_questions": ["question1", "question2", ...],
    "common_misconceptions": ["misconception1", ...]
}}"""

        if instructions:
            system_prompt += f"\n\nAdditional instructions: {instructions}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please analyze this content:\n\n{content[:8000]}"}  # Claude can handle more
        ]
        
        response = await self.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower for more consistent analysis
            max_tokens=2000
        )
        
        if "error" in response:
            return {
                "error": response["error"],
                "summary": "Failed to analyze content",
                "key_concepts": []
            }
        
        try:
            # Extract JSON from response
            response_text = response.get("response", "{}")
            import re
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {
                    "summary": response_text,
                    "key_concepts": [],
                    "socratic_questions": []
                }
            
            return analysis
            
        except json.JSONDecodeError:
            return {
                "summary": response.get("response", "Analysis completed"),
                "key_concepts": [],
                "difficulty_level": "unknown",
                "socratic_questions": []
            }


# Global instance
claude_service = ClaudeService()


# Convenience functions
async def chat_with_claude(
    messages: List[Dict[str, str]], 
    **kwargs
) -> Dict[str, Any]:
    """Chat with Claude model - primary AI service"""
    return await claude_service.chat_completion(messages, **kwargs)