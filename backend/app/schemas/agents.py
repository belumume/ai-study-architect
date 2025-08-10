"""
Pydantic schemas for agent API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from enum import Enum


class AgentType(str, Enum):
    """Available agent types"""
    LEAD_TUTOR = "lead_tutor"


class LearningStyle(str, Enum):
    """Learning style preferences"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"
    MIXED = "mixed"


class KnowledgeLevel(str, Enum):
    """Knowledge level options"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class AgentRequest(BaseModel):
    """Base request for agent interactions"""
    agent_type: AgentType = Field(..., description="Type of agent to interact with")
    message: str = Field(..., description="Message or question for the agent", min_length=1)
    action: Optional[str] = Field(None, description="Specific action to perform")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class AgentResponse(BaseModel):
    """Standard response from agents"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    errors: List[str] = Field(default_factory=list, description="Any errors that occurred")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Response metadata")


class CreateStudyPlanRequest(BaseModel):
    """Request to create a personalized study plan"""
    learning_goal: str = Field(..., description="The main learning objective", min_length=5)
    knowledge_level: KnowledgeLevel = Field(default=KnowledgeLevel.INTERMEDIATE, description="Current knowledge level")
    time_available: str = Field(default="flexible", description="Available time for study")
    learning_style: LearningStyle = Field(default=LearningStyle.MIXED, description="Preferred learning style")


class ExplainConceptRequest(BaseModel):
    """Request to explain a concept"""
    concept: str = Field(..., description="The concept to explain", min_length=2)
    learning_style: LearningStyle = Field(default=LearningStyle.MIXED, description="Preferred learning style")
    prior_knowledge: Optional[List[str]] = Field(None, description="Relevant prior knowledge")


class CheckUnderstandingRequest(BaseModel):
    """Request to generate understanding check questions"""
    topic: str = Field(..., description="The topic to create questions for", min_length=2)


# Study Plan Related Schemas
class LearningObjective(BaseModel):
    """A learning objective within a study plan"""
    id: str = Field(..., description="Unique identifier")
    title: str = Field(..., description="Objective title")
    description: str = Field(..., description="Detailed description")
    estimated_hours: int = Field(..., description="Estimated time to complete")
    difficulty: str = Field(default="intermediate", description="Difficulty level")
    topics: List[str] = Field(default_factory=list, description="Related topics")
    prerequisites: List[str] = Field(default_factory=list, description="Required prerequisites")
    resources: List[str] = Field(default_factory=list, description="Recommended resources")


class StudyPlan(BaseModel):
    """A complete study plan"""
    title: str = Field(..., description="Plan title")
    description: str = Field(..., description="Plan description")
    objectives: List[LearningObjective] = Field(..., description="Learning objectives")
    total_hours: int = Field(..., description="Total estimated hours")
    created_by: str = Field(..., description="Agent that created the plan")


class StudyMilestone(BaseModel):
    """A milestone in the study plan"""
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Milestone description")
    objectives_required: List[str] = Field(..., description="Objectives needed to reach this milestone")


class Question(BaseModel):
    """A comprehension check question"""
    id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="The question text")
    type: str = Field(..., description="Question type (comprehension, application, analysis)")
    options: List[str] = Field(default_factory=list, description="Multiple choice options")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Explanation of the correct answer")


class UnderstandingCheckResponse(BaseModel):
    """Response containing understanding check questions"""
    topic: str = Field(..., description="The topic being tested")
    questions: List[Question] = Field(..., description="Generated questions")