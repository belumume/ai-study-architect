"""
Pydantic schemas for agent API endpoints.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
    action: str | None = Field(None, description="Specific action to perform")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context")


class AgentResponse(BaseModel):
    """Standard response from agents"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: dict[str, Any] = Field(default_factory=dict, description="Response data")
    errors: list[str] = Field(default_factory=list, description="Any errors that occurred")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Response metadata")


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
    prior_knowledge: list[str] | None = Field(None, description="Relevant prior knowledge")


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
    topics: list[str] = Field(default_factory=list, description="Related topics")
    prerequisites: list[str] = Field(default_factory=list, description="Required prerequisites")
    resources: list[str] = Field(default_factory=list, description="Recommended resources")


class StudyPlan(BaseModel):
    """A complete study plan"""
    title: str = Field(..., description="Plan title")
    description: str = Field(..., description="Plan description")
    objectives: list[LearningObjective] = Field(..., description="Learning objectives")
    total_hours: int = Field(..., description="Total estimated hours")
    created_by: str = Field(..., description="Agent that created the plan")


class StudyMilestone(BaseModel):
    """A milestone in the study plan"""
    title: str = Field(..., description="Milestone title")
    description: str = Field(..., description="Milestone description")
    objectives_required: list[str] = Field(..., description="Objectives needed to reach this milestone")


class Question(BaseModel):
    """A comprehension check question"""
    id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="The question text")
    type: str = Field(..., description="Question type (comprehension, application, analysis)")
    options: list[str] = Field(default_factory=list, description="Multiple choice options")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Explanation of the correct answer")


class UnderstandingCheckResponse(BaseModel):
    """Response containing understanding check questions"""
    topic: str = Field(..., description="The topic being tested")
    questions: list[Question] = Field(..., description="Generated questions")
