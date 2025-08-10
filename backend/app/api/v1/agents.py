"""
Agent API endpoints for the AI Study Architect multi-agent system.

This provides access to specialized AI agents that work together to create
personalized learning experiences with cognitive strength building.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
import logging

from app.api.dependencies import get_current_user
from app.models.user import User
from app.agents.lead_tutor import LeadTutorAgent
from app.schemas.agents import (
    AgentRequest,
    AgentResponse as AgentResponseSchema,
    CreateStudyPlanRequest,
    ExplainConceptRequest,
    CheckUnderstandingRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents")

# Agent registry - could be moved to a service layer
_agent_registry = {}

def get_agent(agent_type: str, user_id: str) -> Any:
    """Get or create an agent instance for a user"""
    agent_key = f"{agent_type}_{user_id}"
    
    if agent_key not in _agent_registry:
        if agent_type == "lead_tutor":
            _agent_registry[agent_key] = LeadTutorAgent(
                agent_id=agent_key,
                model_preference="claude"  # Use Claude for best educational experience
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown agent type: {agent_type}"
            )
    
    return _agent_registry[agent_key]


@router.post("/chat", response_model=AgentResponseSchema)
async def agent_chat(
    request: AgentRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Chat with a specialized AI agent.
    
    Available agents:
    - lead_tutor: Orchestrates learning experience, creates study plans
    """
    try:
        # Get the appropriate agent
        agent = get_agent(request.agent_type, str(current_user.id))
        
        # Prepare input data for the agent
        input_data = {
            "user_input": request.message,
            "user_id": str(current_user.id),
            "action": request.action or "general",
            **request.context
        }
        
        # Process the request
        logger.info(f"Processing {request.agent_type} request for user {current_user.id}")
        response = agent.process(input_data)
        
        # Convert to API response format
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data or {},
            "errors": response.errors or [],
            "metadata": {
                **response.metadata,
                "agent_type": request.agent_type,
                "user_id": str(current_user.id)
            }
        }
        
    except Exception as e:
        logger.error(f"Agent chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing failed: {str(e)}"
        )


@router.post("/study-plan", response_model=AgentResponseSchema)
async def create_study_plan(
    request: CreateStudyPlanRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create a personalized study plan using the Lead Tutor agent.
    
    This leverages Claude's superior educational reasoning to create
    comprehensive study plans tailored to the student's needs.
    """
    try:
        agent = get_agent("lead_tutor", str(current_user.id))
        
        input_data = {
            "user_input": request.learning_goal,
            "user_id": str(current_user.id),
            "action": "create_plan",
            "knowledge_level": request.knowledge_level,
            "time_available": request.time_available,
            "learning_style": request.learning_style
        }
        
        logger.info(f"Creating study plan for user {current_user.id}: {request.learning_goal}")
        response = agent.process(input_data)
        
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data or {},
            "errors": response.errors or [],
            "metadata": {
                **response.metadata,
                "agent_type": "lead_tutor",
                "action": "create_plan",
                "user_id": str(current_user.id)
            }
        }
        
    except Exception as e:
        logger.error(f"Study plan creation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Study plan creation failed: {str(e)}"
        )


@router.post("/explain", response_model=AgentResponseSchema)
async def explain_concept(
    request: ExplainConceptRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a detailed explanation of a concept from the Lead Tutor.
    
    Uses Claude's superior reasoning to provide clear, educational explanations
    tailored to the student's learning style and prior knowledge.
    """
    try:
        agent = get_agent("lead_tutor", str(current_user.id))
        
        input_data = {
            "user_input": request.concept,
            "user_id": str(current_user.id),
            "action": "explain_concept",
            "learning_style": request.learning_style,
            "prior_knowledge": request.prior_knowledge or []
        }
        
        logger.info(f"Explaining concept for user {current_user.id}: {request.concept}")
        response = agent.process(input_data)
        
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data or {},
            "errors": response.errors or [],
            "metadata": {
                **response.metadata,
                "agent_type": "lead_tutor",
                "action": "explain_concept",
                "user_id": str(current_user.id)
            }
        }
        
    except Exception as e:
        logger.error(f"Concept explanation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Concept explanation failed: {str(e)}"
        )


@router.post("/check-understanding", response_model=AgentResponseSchema)
async def check_understanding(
    request: CheckUnderstandingRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Generate questions to check understanding of a topic.
    
    The Lead Tutor creates thoughtful questions designed to reveal
    true comprehension rather than surface-level memorization.
    """
    try:
        agent = get_agent("lead_tutor", str(current_user.id))
        
        input_data = {
            "user_input": request.topic,
            "user_id": str(current_user.id),
            "action": "check_understanding"
        }
        
        logger.info(f"Generating understanding check for user {current_user.id}: {request.topic}")
        response = agent.process(input_data)
        
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data or {},
            "errors": response.errors or [],
            "metadata": {
                **response.metadata,
                "agent_type": "lead_tutor",
                "action": "check_understanding",
                "user_id": str(current_user.id)
            }
        }
        
    except Exception as e:
        logger.error(f"Understanding check error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Understanding check failed: {str(e)}"
        )


@router.get("/status")
async def agent_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get status of all agents for the current user"""
    try:
        user_agents = {}
        
        # Find all agents for this user
        for key, agent in _agent_registry.items():
            if key.endswith(f"_{current_user.id}"):
                agent_type = key.replace(f"_{current_user.id}", "")
                user_agents[agent_type] = {
                    "active": True,
                    "memory_length": len(agent.get_messages()),
                    "state": agent.get_state()
                }
        
        return {
            "user_id": str(current_user.id),
            "active_agents": len(user_agents),
            "agents": user_agents,
            "available_agents": ["lead_tutor"],
            "system_status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Agent status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.delete("/clear-memory")
async def clear_agent_memory(
    agent_type: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Clear conversation memory for a specific agent"""
    try:
        agent_key = f"{agent_type}_{current_user.id}"
        
        if agent_key in _agent_registry:
            agent = _agent_registry[agent_key]
            agent.clear_memory()
            
            logger.info(f"Cleared memory for {agent_type} agent for user {current_user.id}")
            
            return {
                "success": True,
                "message": f"Cleared memory for {agent_type} agent",
                "agent_type": agent_type,
                "user_id": str(current_user.id)
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"No active {agent_type} agent found for user"
            )
            
    except Exception as e:
        logger.error(f"Clear memory error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear agent memory: {str(e)}"
        )