"""
Agent Manager with Redis-backed storage for persistent agent instances
"""

import json
import pickle
from typing import Dict, List, Optional, Type, Any
from datetime import datetime, timedelta
import logging
from dataclasses import asdict
import threading

from app.core.cache import redis_cache
from app.agents.base import BaseAgent
from app.agents.lead_tutor import LeadTutorAgent

logger = logging.getLogger(__name__)


class AgentManager:
    """
    Manages agent instances with Redis-backed persistence
    
    Features:
    - Persistent agent storage across server restarts
    - Agent lifecycle management (creation, retrieval, cleanup)
    - Session-based agent isolation
    - Memory optimization with TTL expiration
    - Thread-safe operations
    """
    
    def __init__(self):
        self._local_cache: Dict[str, BaseAgent] = {}
        self._cache_lock = threading.RLock()
        self.default_agent_ttl = timedelta(hours=2)  # Agents expire after 2 hours of inactivity
        self.max_local_cache_size = 50  # Keep max 50 agents in memory
        
        # Registry of available agent classes
        self.agent_classes = {
            "lead_tutor": LeadTutorAgent,
            # Add more agent types here as they're implemented
        }
    
    def get_agent_key(self, user_id: str, agent_type: str, session_id: Optional[str] = None) -> str:
        """Generate Redis key for agent storage"""
        if session_id:
            return f"agent:{agent_type}:{user_id}:{session_id}"
        return f"agent:{agent_type}:{user_id}"
    
    def create_agent(
        self,
        user_id: str,
        agent_type: str,
        session_id: Optional[str] = None,
        **agent_kwargs
    ) -> Optional[BaseAgent]:
        """
        Create a new agent instance
        
        Args:
            user_id: User identifier
            agent_type: Type of agent to create
            session_id: Optional session identifier for isolation
            **agent_kwargs: Additional arguments for agent initialization
            
        Returns:
            Created agent instance or None if creation failed
        """
        try:
            if agent_type not in self.agent_classes:
                logger.error(f"Unknown agent type: {agent_type}")
                return None
            
            agent_class = self.agent_classes[agent_type]
            
            # Create unique agent ID
            if session_id:
                agent_id = f"{agent_type}_{user_id}_{session_id}"
            else:
                agent_id = f"{agent_type}_{user_id}"
            
            # Initialize agent with unique ID
            agent = agent_class(agent_id=agent_id, **agent_kwargs)
            
            # Update agent state with user/session info
            agent.update_state(user_id=user_id, session_id=session_id)
            
            # Store in Redis and local cache
            self._store_agent(user_id, agent_type, agent, session_id)
            
            logger.info(f"Created agent {agent_id} for user {user_id}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to create agent {agent_type} for user {user_id}: {e}")
            return None
    
    def get_agent(
        self,
        user_id: str,
        agent_type: str,
        session_id: Optional[str] = None,
        create_if_missing: bool = True,
        **agent_kwargs
    ) -> Optional[BaseAgent]:
        """
        Retrieve an existing agent or create one if it doesn't exist
        
        Args:
            user_id: User identifier
            agent_type: Type of agent to retrieve
            session_id: Optional session identifier
            create_if_missing: Whether to create agent if not found
            **agent_kwargs: Arguments for agent creation if needed
            
        Returns:
            Agent instance or None if not found/created
        """
        cache_key = self.get_agent_key(user_id, agent_type, session_id)
        
        with self._cache_lock:
            # Check local cache first
            if cache_key in self._local_cache:
                agent = self._local_cache[cache_key]
                self._update_agent_activity(agent)
                return agent
            
            # Try to load from Redis
            agent = self._load_agent_from_redis(cache_key)
            if agent:
                # Store in local cache
                self._local_cache[cache_key] = agent
                self._update_agent_activity(agent)
                self._cleanup_local_cache()
                return agent
            
            # Create new agent if requested
            if create_if_missing:
                return self.create_agent(user_id, agent_type, session_id, **agent_kwargs)
            
            return None
    
    def save_agent(
        self,
        user_id: str,
        agent_type: str,
        agent: BaseAgent,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Save agent state to Redis
        
        Args:
            user_id: User identifier
            agent_type: Type of agent
            agent: Agent instance to save
            session_id: Optional session identifier
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            return self._store_agent(user_id, agent_type, agent, session_id)
        except Exception as e:
            logger.error(f"Failed to save agent {agent.agent_id}: {e}")
            return False
    
    def delete_agent(
        self,
        user_id: str,
        agent_type: str,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Delete an agent from storage
        
        Args:
            user_id: User identifier
            agent_type: Type of agent
            session_id: Optional session identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        cache_key = self.get_agent_key(user_id, agent_type, session_id)
        
        with self._cache_lock:
            # Remove from local cache
            self._local_cache.pop(cache_key, None)
            
            # Remove from Redis
            try:
                success = redis_cache.delete(cache_key)
                if success:
                    logger.info(f"Deleted agent {cache_key}")
                return success
            except Exception as e:
                logger.error(f"Failed to delete agent {cache_key}: {e}")
                return False
    
    def list_user_agents(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all agents for a specific user
        
        Args:
            user_id: User identifier
            
        Returns:
            List of agent metadata dictionaries
        """
        try:
            # Search Redis for agent keys
            pattern = f"agent:*:{user_id}:*"
            keys = redis_cache._get_client().keys(pattern) if redis_cache.is_connected else []
            
            agents = []
            for key in keys:
                # Parse key to extract agent info
                parts = key.split(':')
                if len(parts) >= 3:
                    agent_type = parts[1]
                    session_id = parts[3] if len(parts) > 3 else None
                    
                    # Get basic info without loading full agent
                    agent_info = {
                        "agent_type": agent_type,
                        "user_id": user_id,
                        "session_id": session_id,
                        "redis_key": key,
                        "last_activity": self._get_agent_last_activity(key)
                    }
                    agents.append(agent_info)
            
            return agents
            
        except Exception as e:
            logger.error(f"Failed to list agents for user {user_id}: {e}")
            return []
    
    def cleanup_expired_agents(self) -> int:
        """
        Clean up expired agents from storage
        
        Returns:
            Number of agents cleaned up
        """
        try:
            if not redis_cache.is_connected:
                return 0
            
            pattern = "agent:*"
            keys = redis_cache._get_client().keys(pattern)
            
            expired_count = 0
            cutoff_time = datetime.utcnow() - self.default_agent_ttl
            
            for key in keys:
                last_activity = self._get_agent_last_activity(key)
                if last_activity and last_activity < cutoff_time:
                    redis_cache.delete(key)
                    # Also remove from local cache
                    with self._cache_lock:
                        self._local_cache.pop(key, None)
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired agents")
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired agents: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent manager statistics"""
        try:
            if not redis_cache.is_connected:
                return {
                    "redis_connected": False,
                    "local_cache_size": len(self._local_cache),
                    "total_agents": 0,
                    "error": "Redis not connected"
                }
            
            # Count agents in Redis
            pattern = "agent:*"
            keys = redis_cache._get_client().keys(pattern)
            
            # Group by agent type
            agent_types = {}
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 2:
                    agent_type = parts[1]
                    agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
            
            return {
                "redis_connected": True,
                "local_cache_size": len(self._local_cache),
                "max_local_cache_size": self.max_local_cache_size,
                "total_agents": len(keys),
                "agents_by_type": agent_types,
                "default_ttl_hours": self.default_agent_ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent manager stats: {e}")
            return {"error": str(e)}
    
    def _store_agent(
        self,
        user_id: str,
        agent_type: str,
        agent: BaseAgent,
        session_id: Optional[str] = None
    ) -> bool:
        """Store agent in Redis and local cache"""
        cache_key = self.get_agent_key(user_id, agent_type, session_id)
        
        try:
            # Prepare agent data for serialization
            agent_data = {
                "agent_id": agent.agent_id,
                "agent_type": agent_type,
                "user_id": user_id,
                "session_id": session_id,
                "model_name": agent.model_name,
                "temperature": agent.temperature,
                "memory": [msg.dict() for msg in agent.memory],
                "state": agent.get_state(),
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            }
            
            # Special handling for LeadTutorAgent state
            if hasattr(agent, 'tutor_state'):
                agent_data["tutor_state"] = agent.tutor_state.model_dump()
            
            # Store in Redis
            success = redis_cache.set(cache_key, agent_data, ttl=self.default_agent_ttl)
            
            if success:
                # Also store in local cache
                with self._cache_lock:
                    self._local_cache[cache_key] = agent
                    self._cleanup_local_cache()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store agent {cache_key}: {e}")
            return False
    
    def _load_agent_from_redis(self, cache_key: str) -> Optional[BaseAgent]:
        """Load agent from Redis storage"""
        try:
            agent_data = redis_cache.get(cache_key)
            if not agent_data:
                return None
            
            # Extract agent type and create instance
            agent_type = agent_data.get("agent_type")
            if agent_type not in self.agent_classes:
                logger.error(f"Unknown agent type in stored data: {agent_type}")
                return None
            
            agent_class = self.agent_classes[agent_type]
            
            # Recreate agent
            agent = agent_class(
                agent_id=agent_data["agent_id"],
                model_name=agent_data.get("model_name", "llama3.2"),
                temperature=agent_data.get("temperature", 0.7)
            )
            
            # Restore memory
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
            message_types = {
                "human": HumanMessage,
                "ai": AIMessage,
                "system": SystemMessage
            }
            
            for msg_data in agent_data.get("memory", []):
                msg_type = msg_data.get("type", "human")
                if msg_type in message_types:
                    message = message_types[msg_type](content=msg_data.get("content", ""))
                    agent.add_message(message)
            
            # Restore state
            state_data = agent_data.get("state", {})
            agent.update_state(**state_data)
            
            # Restore special agent state (e.g., LeadTutorAgent)
            if hasattr(agent, 'tutor_state') and "tutor_state" in agent_data:
                from app.agents.lead_tutor import LeadTutorState
                agent.tutor_state = LeadTutorState(**agent_data["tutor_state"])
            
            logger.debug(f"Loaded agent {agent.agent_id} from Redis")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to load agent from Redis {cache_key}: {e}")
            return None
    
    def _update_agent_activity(self, agent: BaseAgent) -> None:
        """Update agent's last activity timestamp"""
        agent.update_state(last_activity=datetime.utcnow())
    
    def _get_agent_last_activity(self, redis_key: str) -> Optional[datetime]:
        """Get agent's last activity from Redis"""
        try:
            agent_data = redis_cache.get(redis_key)
            if agent_data and "last_activity" in agent_data:
                return datetime.fromisoformat(agent_data["last_activity"])
        except Exception:
            pass
        return None
    
    def _cleanup_local_cache(self) -> None:
        """Remove excess agents from local cache (LRU-style)"""
        if len(self._local_cache) > self.max_local_cache_size:
            # Remove oldest 25% of cached agents
            remove_count = len(self._local_cache) - self.max_local_cache_size + 10
            
            # Sort by last access (approximated by creation order for now)
            sorted_keys = list(self._local_cache.keys())[:remove_count]
            
            for key in sorted_keys:
                self._local_cache.pop(key, None)
            
            logger.debug(f"Cleaned up {remove_count} agents from local cache")


# Global agent manager instance
agent_manager = AgentManager()