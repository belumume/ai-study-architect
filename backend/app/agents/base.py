"""Base Agent class for all AI agents in the system"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import logging
import asyncio
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Base state model for agents"""
    agent_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in the Study Architect system.
    
    This class provides common functionality for:
    - Cloud AI integration (Claude/OpenAI via ai_service_manager)
    - Memory management
    - State persistence
    - Error handling
    - Logging
    """
    
    def __init__(
        self,
        agent_id: str,
        model_preference: str = "claude",  # claude, openai, or auto
        temperature: float = 0.7,
        **kwargs
    ) -> None:
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            model_preference: Preferred AI service (claude, openai, auto for fallback)
            temperature: LLM temperature setting
            **kwargs: Additional configuration options
        """
        self.agent_id = agent_id
        self.model_preference = model_preference
        self.temperature = temperature
        
        # Initialize cloud AI service manager
        from app.services.ai_service_manager import ai_service_manager
        self.ai_service_manager = ai_service_manager
        
        # Initialize simple conversation memory
        self.memory = []  # List of messages
        
        # Agent state
        self.state = AgentState(agent_id=agent_id)
        
        logger.info(f"Initialized {self.__class__.__name__} with ID: {agent_id} (AI: {model_preference})")
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        Must be implemented by subclasses.
        """
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process input and generate a response.
        Must be implemented by subclasses.
        
        Args:
            input_data: Input data to process
            
        Returns:
            AgentResponse with the result
        """
        pass
    
    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the conversation memory"""
        self.memory.append(message)
    
    def get_messages(self) -> List[BaseMessage]:
        """Get all messages from memory"""
        return self.memory
    
    def clear_memory(self) -> None:
        """Clear the conversation memory"""
        self.memory = []
    
    def format_prompt(self, user_input: str) -> List[BaseMessage]:
        """
        Format the prompt with system message and conversation history.
        
        Args:
            user_input: The user's input text
            
        Returns:
            List of messages including system prompt and history
        """
        messages = [SystemMessage(content=self.get_system_prompt())]
        
        # Add conversation history
        messages.extend(self.get_messages())
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))
        
        return messages
    
    def invoke_llm(self, prompt: str, use_cache: bool = True) -> str:
        """
        Invoke the cloud AI service with a prompt, with optional caching.
        
        Args:
            prompt: The prompt to send to the AI service
            use_cache: Whether to use Redis caching for this request
            
        Returns:
            The AI service response
        """
        try:
            # Try cache first if enabled
            if use_cache:
                from app.core.cache import ai_cache
                
                # Generate cache key based on preferred model and prompt
                model_name = f"{self.model_preference}-agent"
                cached_response = ai_cache.get_llm_response(
                    model=model_name,
                    prompt=prompt,
                    agent_id=self.agent_id
                )
                
                if cached_response:
                    logger.debug(f"Cache hit for {self.agent_id} - model {model_name}")
                    return cached_response["response"]
            
            # Cache miss - invoke cloud AI service
            logger.debug(f"Cache miss for {self.agent_id} - invoking cloud AI")
            
            # Convert prompt to messages format for ai_service_manager
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            # Handle asyncio event loop properly
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If loop is running, we need to use a different approach
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.ai_service_manager.chat_completion(
                                messages=messages,
                                temperature=self.temperature,
                                prefer_service=self.model_preference if self.model_preference != "auto" else None
                            )
                        )
                        result = future.result()
                else:
                    # Loop exists but not running
                    result = loop.run_until_complete(
                        self.ai_service_manager.chat_completion(
                            messages=messages,
                            temperature=self.temperature,
                            prefer_service=self.model_preference if self.model_preference != "auto" else None
                        )
                    )
            except RuntimeError:
                # No event loop exists, create one
                result = asyncio.run(
                    self.ai_service_manager.chat_completion(
                        messages=messages,
                        temperature=self.temperature,
                        prefer_service=self.model_preference if self.model_preference != "auto" else None
                    )
                )
            
            if result.get("error"):
                logger.error(f"AI service error: {result['error']}")
                response = f"AI service error: {result['error']}"
            else:
                response = result.get("response", "No response received")
            
            # Cache the response if caching is enabled and response is valid
            if use_cache and response and not result.get("error"):
                from app.core.cache import ai_cache
                from datetime import timedelta
                
                model_name = f"{self.model_preference}-agent"
                ai_cache.set_llm_response(
                    model=model_name,
                    prompt=prompt,
                    response=response,
                    ttl=timedelta(hours=6),  # Cache agent responses for 6 hours
                    agent_id=self.agent_id
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking cloud AI service: {str(e)}")
            raise
    
    async def invoke_llm_async(self, prompt: str, use_cache: bool = True) -> str:
        """
        Async version of invoke_llm for better async/await compatibility.
        
        Args:
            prompt: The prompt to send to the AI service
            use_cache: Whether to use Redis caching for this request
            
        Returns:
            The AI service response
        """
        try:
            # Try cache first if enabled
            if use_cache:
                from app.core.cache import ai_cache
                
                # Generate cache key based on preferred model and prompt
                model_name = f"{self.model_preference}-agent"
                cached_response = ai_cache.get_llm_response(
                    model=model_name,
                    prompt=prompt,
                    agent_id=self.agent_id
                )
                
                if cached_response:
                    logger.debug(f"Cache hit for {self.agent_id} - model {model_name}")
                    return cached_response["response"]
            
            # Cache miss - invoke cloud AI service
            logger.debug(f"Cache miss for {self.agent_id} - invoking cloud AI (async)")
            
            # Convert prompt to messages format for ai_service_manager
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            # Call the async ai_service_manager directly
            result = await self.ai_service_manager.chat_completion(
                messages=messages,
                temperature=self.temperature,
                prefer_service=self.model_preference if self.model_preference != "auto" else None
            )
            
            if result.get("error"):
                logger.error(f"AI service error: {result['error']}")
                response = f"AI service error: {result['error']}"
            else:
                response = result.get("response", "No response received")
            
            # Cache the response if caching is enabled and response is valid
            if use_cache and response and not result.get("error"):
                from app.core.cache import ai_cache
                from datetime import timedelta
                
                model_name = f"{self.model_preference}-agent"
                ai_cache.set_llm_response(
                    model=model_name,
                    prompt=prompt,
                    response=response,
                    ttl=timedelta(hours=6),  # Cache agent responses for 6 hours
                    agent_id=self.agent_id
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error invoking cloud AI service (async): {str(e)}")
            raise
    
    def update_state(self, **kwargs) -> None:
        """Update the agent's state"""
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
        self.state.updated_at = datetime.utcnow()
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current agent state as a dictionary"""
        return self.state.model_dump()
    
    def handle_error(self, error: Exception, context: str = "") -> AgentResponse:
        """
        Standard error handling for agents.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            AgentResponse with error information
        """
        error_msg = f"Error in {self.__class__.__name__}"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"
        
        logger.error(error_msg, exc_info=True)
        
        return AgentResponse(
            success=False,
            message="An error occurred while processing your request",
            errors=[error_msg],
            metadata={"agent_id": self.agent_id, "error_type": type(error).__name__}
        )