"""API endpoints for the Lead Tutor Agent"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.study_session import StudySession
from app.agents.lead_tutor import LeadTutorAgent
from app.core.agent_manager import agent_manager
from app.core.config import settings
from app.core.exceptions import AgentProcessingError
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutor", tags=["tutor"])
limiter = Limiter(key_func=get_remote_address)

class TutorRequest(BaseModel):
    """Request model for tutor interactions"""
    message: str = Field(..., description="User's message or question")
    action: Optional[str] = Field(
        default="general",
        description="Specific action: create_plan, explain_concept, check_understanding, provide_feedback"
    )
    context: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional context for the request"
    )
    session_id: Optional[str] = Field(None, description="Study session ID")


class TutorResponse(BaseModel):
    """Response model for tutor interactions"""
    success: bool
    message: str
    response: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    session_id: str


class StudyPlanRequest(BaseModel):
    """Request model for creating a study plan"""
    goal: str = Field(..., description="Learning goal")
    knowledge_level: str = Field(default="beginner", description="Current knowledge level")
    time_available: str = Field(default="flexible", description="Time available for study")
    learning_style: str = Field(default="visual", description="Preferred learning style")


class AdaptDifficultyRequest(BaseModel):
    """Request model for difficulty adaptation"""
    performance_score: float = Field(..., ge=0.0, le=1.0, description="Performance score between 0 and 1")


def get_or_create_agent(user_id: str, session_id: Optional[str] = None) -> LeadTutorAgent:
    """Get existing agent or create new one for user via Agent Manager"""
    agent = agent_manager.get_agent(
        user_id=user_id,
        agent_type="lead_tutor",
        session_id=session_id,
        create_if_missing=True,
        model_name="claude-3-5-sonnet-20241022",  # Default to Claude
        base_url="https://api.anthropic.com/v1",
        temperature=0.7
    )
    
    if agent is None:
        logger.error(f"Failed to create Lead Tutor Agent for user {user_id}")
        raise AgentProcessingError(detail="Failed to initialize tutor agent")
    
    return agent


@router.post("/chat", response_model=TutorResponse)
@limiter.limit("20/minute")
def chat_with_tutor(
    request: Request,
    tutor_request: TutorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Chat with the Lead Tutor Agent.
    
    Actions:
    - general: General tutoring conversation
    - create_plan: Create a personalized study plan
    - explain_concept: Get detailed explanation of a concept
    - check_understanding: Generate questions to test understanding
    - provide_feedback: Get feedback on performance
    """
    try:
        # Get or create agent for this user
        agent = get_or_create_agent(str(current_user.id), tutor_request.session_id)
        
        # Prepare input data
        input_data = {
            "user_input": tutor_request.message,
            "user_id": str(current_user.id),
            "action": tutor_request.action,
            "session_id": tutor_request.session_id,
            **tutor_request.context
        }
        
        # Process with the agent
        agent_response = agent.process(input_data)
        
        # Save agent state back to Redis
        agent_manager.save_agent(str(current_user.id), "lead_tutor", agent, tutor_request.session_id)
        
        # Create response
        response_text = None
        if tutor_request.action == "general" and agent_response.data:
            response_text = agent_response.data.get("response")
        elif tutor_request.action == "explain_concept" and agent_response.data:
            response_text = agent_response.data.get("explanation")
        elif tutor_request.action == "provide_feedback" and agent_response.data:
            response_text = agent_response.data.get("feedback")
        
        return TutorResponse(
            success=agent_response.success,
            message=agent_response.message,
            response=response_text,
            data=agent_response.data,
            session_id=agent.state.session_id or f"session_{current_user.id}"
        )
        
    except ConnectionError as e:
        logger.error(f"AI service connection error: {str(e)}")
        raise AgentProcessingError(detail="AI service connection failed")
    except Exception as e:
        logger.error(f"Error in tutor chat: {str(e)}")
        raise AgentProcessingError(detail=f"Failed to process request: {str(e)}")


@router.post("/create-study-plan", response_model=TutorResponse)
@limiter.limit("10/minute")
def create_study_plan(
    request: Request,  # Changed from api_request to request
    plan_request: StudyPlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a personalized study plan"""
    tutor_request = TutorRequest(
        message=plan_request.goal,
        action="create_plan",
        context={
            "knowledge_level": plan_request.knowledge_level,
            "time_available": plan_request.time_available,
            "learning_style": plan_request.learning_style
        }
    )
    
    return chat_with_tutor(request, tutor_request, current_user, db)


@router.get("/progress")
@limiter.limit("30/minute")
def get_learning_progress(
    request: Request,
    current_user: User = Depends(get_current_user),
    session_id: Optional[str] = None
):
    """Get the user's learning progress"""
    agent = agent_manager.get_agent(
        user_id=str(current_user.id),
        agent_type="lead_tutor",
        session_id=session_id,
        create_if_missing=False
    )
    
    if not agent:
        return {
            "message": "No active learning session found",
            "progress": None
        }
    
    progress = agent.get_progress_summary()
    
    return {
        "message": "Progress retrieved successfully",
        "progress": progress
    }


@router.post("/clear-session")
@limiter.limit("10/minute")
def clear_tutor_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    session_id: Optional[str] = None
):
    """Clear the tutor session for the current user"""
    success = agent_manager.delete_agent(
        user_id=str(current_user.id),
        agent_type="lead_tutor",
        session_id=session_id
    )
    
    if success:
        logger.info(f"Cleared tutor session for user {current_user.id}")
        return {
            "message": "Tutor session cleared successfully",
            "success": True
        }
    
    return {
        "message": "No active session to clear",
        "success": False
    }


@router.post("/adapt-difficulty")
@limiter.limit("20/minute")
def adapt_difficulty(
    request: Request,
    adapt_request: AdaptDifficultyRequest,
    current_user: User = Depends(get_current_user),
    session_id: Optional[str] = None
):
    """Manually trigger difficulty adaptation based on performance"""
    agent = get_or_create_agent(str(current_user.id), session_id)
    
    old_difficulty = agent.tutor_state.difficulty_level
    agent.adapt_difficulty(adapt_request.performance_score)
    new_difficulty = agent.tutor_state.difficulty_level
    
    # Save updated agent state
    agent_manager.save_agent(str(current_user.id), "lead_tutor", agent, session_id)
    
    return {
        "message": "Difficulty adapted",
        "old_difficulty": old_difficulty,
        "new_difficulty": new_difficulty,
        "performance_score": adapt_request.performance_score
    }