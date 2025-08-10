"""Lead Tutor Agent - Orchestrates the learning experience with Redis caching"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.agents.base import BaseAgent, AgentResponse
from app.models.user import User
from app.models.study_session import StudySession
from app.models.content import Content
from app.schemas.study_session import StudyPlan, LearningObjective
from app.core.cache import cached_ai_response, ai_cache

logger = logging.getLogger(__name__)


class LeadTutorState(BaseModel):
    """State specific to the Lead Tutor Agent"""
    current_topic: Optional[str] = None
    learning_style: Optional[str] = None
    difficulty_level: str = "intermediate"
    session_goals: List[str] = Field(default_factory=list)
    completed_objectives: List[str] = Field(default_factory=list)
    current_plan: Optional[StudyPlan] = None


class LeadTutorAgent(BaseAgent):
    """
    The Lead Tutor Agent orchestrates the entire learning experience.
    
    Responsibilities:
    - Understand student's learning goals and current knowledge
    - Create personalized study plans
    - Coordinate with other agents for content processing and practice generation
    - Adapt difficulty based on student performance
    - Provide encouragement and motivation
    - Track progress and suggest next steps
    """
    
    def __init__(self, agent_id: str = "lead_tutor", **kwargs) -> None:
        # Default to Claude for educational tasks - it excels at Socratic questioning
        super().__init__(agent_id=agent_id, model_preference="claude", **kwargs)
        self.tutor_state = LeadTutorState()
        
        # Initialize output parser for structured responses
        self.json_parser = JsonOutputParser()
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for the Lead Tutor"""
        return """You are an expert AI tutor in the Study Architect system. Your role is to:

1. Understand the student's learning goals, current knowledge level, and preferred learning style
2. Create personalized study plans that adapt to the student's progress
3. Break down complex topics into manageable learning objectives
4. Provide clear explanations and guide students through difficult concepts
5. Offer encouragement and maintain student motivation
6. Monitor progress and adjust difficulty appropriately
7. Suggest relevant practice problems and additional resources

You should be:
- Patient and encouraging
- Clear and concise in explanations
- Adaptive to different learning styles
- Focused on building deep understanding, not just memorization
- Proactive in identifying knowledge gaps

Always structure your responses clearly and provide actionable next steps."""
    
    def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process student input and orchestrate the learning experience.
        
        Expected input_data keys:
        - user_input: The student's message or question
        - user_id: The student's ID
        - session_id: Current study session ID (optional)
        - action: Specific action requested (optional): 'create_plan', 'explain_concept', 'check_understanding'
        """
        try:
            user_input = input_data.get("user_input", "")
            user_id = input_data.get("user_id")
            session_id = input_data.get("session_id")
            action = input_data.get("action", "general")
            
            # Update state
            self.update_state(user_id=user_id, session_id=session_id)
            
            # Route to appropriate handler based on action
            if action == "create_plan":
                return self._create_study_plan(user_input, input_data)
            elif action == "explain_concept":
                return self._explain_concept(user_input, input_data)
            elif action == "check_understanding":
                return self._check_understanding(user_input, input_data)
            elif action == "provide_feedback":
                return self._provide_feedback(input_data)
            else:
                return self._general_interaction(user_input, input_data)
                
        except Exception as e:
            return self.handle_error(e, f"processing {action} action")
    
    def _create_study_plan(self, user_input: str, context: Dict[str, Any]) -> AgentResponse:
        """Create a personalized study plan based on student goals"""
        
        # Create prompt for study plan generation
        plan_prompt = ChatPromptTemplate.from_messages([
            ("system", self.get_system_prompt()),
            ("human", """Based on the following learning goal, create a detailed study plan:

Goal: {goal}
Current Knowledge Level: {knowledge_level}
Available Time: {time_available}
Learning Style: {learning_style}

Please provide a structured study plan with:
1. Clear learning objectives (3-5 main objectives)
2. Recommended sequence of topics
3. Estimated time for each section
4. Suggested resources and practice methods
5. Milestones to track progress

Format your response as a JSON object with the following structure:
{{
    "title": "Study plan title",
    "description": "Brief overview of the plan",
    "total_hours": estimated total hours,
    "objectives": [
        {{
            "id": "obj1",
            "title": "Objective title",
            "description": "What the student will learn",
            "estimated_hours": hours,
            "topics": ["topic1", "topic2"],
            "prerequisites": ["prereq1"],
            "resources": ["resource1", "resource2"]
        }}
    ],
    "milestones": [
        {{
            "title": "Milestone title",
            "description": "What indicates this milestone is reached",
            "objectives_required": ["obj1", "obj2"]
        }}
    ],
    "recommendations": ["recommendation1", "recommendation2"]
}}""")
        ])
        
        # Extract context
        knowledge_level = context.get("knowledge_level", "beginner")
        time_available = context.get("time_available", "flexible")
        learning_style = context.get("learning_style", self.tutor_state.learning_style or "visual")
        
        # Generate the plan
        messages = plan_prompt.format_messages(
            goal=user_input,
            knowledge_level=knowledge_level,
            time_available=time_available,
            learning_style=learning_style
        )
        
        response = self.invoke_llm(messages[0].content + "\n" + messages[1].content)
        
        try:
            # Log the raw response for debugging
            logger.info(f"Raw LLM response for study plan: {response[:200]}...")
            
            # Parse the JSON response
            plan_data = self.json_parser.parse(response)
            
            # Create StudyPlan object
            study_plan = StudyPlan(
                title=plan_data["title"],
                description=plan_data["description"],
                objectives=[
                    LearningObjective(**obj) for obj in plan_data["objectives"]
                ],
                total_hours=plan_data["total_hours"],
                created_by=self.agent_id
            )
            
            # Update state
            self.tutor_state.current_plan = study_plan
            self.tutor_state.current_topic = user_input
            
            # Add to conversation memory
            self.add_message(HumanMessage(content=user_input))
            self.add_message(AIMessage(content=f"I've created a personalized study plan for: {plan_data['title']}"))
            
            return AgentResponse(
                success=True,
                message="Study plan created successfully",
                data={
                    "study_plan": study_plan.model_dump(),
                    "milestones": plan_data.get("milestones", []),
                    "recommendations": plan_data.get("recommendations", [])
                },
                metadata={"action": "create_plan", "agent_id": self.agent_id}
            )
            
        except Exception as e:
            logger.error(f"Error parsing study plan response: {str(e)}")
            logger.error(f"Raw response was: {response}")
            
            # Fallback to a simpler approach
            try:
                # Create a basic study plan from the text response
                study_plan = StudyPlan(
                    title=f"Study Plan: {user_input[:50]}",
                    description=f"A personalized learning plan for {user_input}",
                    objectives=[
                        LearningObjective(
                            id="obj1",
                            title="Foundation",
                            description="Build foundational knowledge",
                            estimated_hours=10,
                            difficulty="beginner"
                        ),
                        LearningObjective(
                            id="obj2", 
                            title="Practice",
                            description="Apply knowledge through practice",
                            estimated_hours=15,
                            difficulty="intermediate"
                        )
                    ],
                    total_hours=25,
                    created_by=self.agent_id
                )
                
                return AgentResponse(
                    success=True,
                    message="Created a basic study plan. For a more detailed plan, please try again.",
                    data={
                        "study_plan": study_plan.model_dump(),
                        "raw_response": response[:500],
                        "note": "The AI generated a text response instead of structured data"
                    },
                    metadata={"action": "create_plan", "agent_id": self.agent_id}
                )
            except Exception as fallback_error:
                return AgentResponse(
                    success=False,
                    message="Failed to create study plan",
                    errors=[f"Could not parse plan: {str(e)}", f"Fallback also failed: {str(fallback_error)}"],
                    metadata={"action": "create_plan", "agent_id": self.agent_id}
                )
    
    def _explain_concept(self, concept: str, context: Dict[str, Any]) -> AgentResponse:
        """Explain a concept in a way tailored to the student's learning style"""
        
        learning_style = context.get("learning_style", self.tutor_state.learning_style or "visual")
        prior_knowledge = context.get("prior_knowledge", [])
        
        explanation_prompt = f"""Explain the concept: {concept}

Student's learning style: {learning_style}
Prior knowledge: {', '.join(prior_knowledge) if prior_knowledge else 'Basic understanding'}

Provide a clear, engaging explanation that:
1. Starts with a simple overview
2. Uses analogies or examples relevant to the learning style
3. Breaks down complex parts into smaller pieces
4. Highlights key points to remember
5. Suggests ways to practice or apply this knowledge

Format your response with clear sections and emphasis on important terms."""
        
        messages = self.format_prompt(explanation_prompt)
        response = self.invoke_llm(messages[0].content + "\n" + messages[-1].content)
        
        # Add to conversation memory
        self.add_message(HumanMessage(content=f"Explain: {concept}"))
        self.add_message(AIMessage(content=response))
        
        return AgentResponse(
            success=True,
            message="Concept explained",
            data={
                "concept": concept,
                "explanation": response,
                "learning_style": learning_style
            },
            metadata={"action": "explain_concept", "agent_id": self.agent_id}
        )
    
    def _check_understanding(self, topic: str, context: Dict[str, Any]) -> AgentResponse:
        """Generate questions to check student understanding"""
        
        check_prompt = f"""Create 3-5 questions to check understanding of: {topic}

Difficulty level: {self.tutor_state.difficulty_level}

Include:
1. One basic comprehension question
2. One application question
3. One analysis or synthesis question
4. Clear explanations for why each answer is correct

Format as JSON:
{{
    "questions": [
        {{
            "id": "q1",
            "question": "Question text",
            "type": "comprehension|application|analysis",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Why this is correct"
        }}
    ]
}}"""
        
        response = self.invoke_llm(check_prompt)
        
        try:
            questions_data = self.json_parser.parse(response)
            
            return AgentResponse(
                success=True,
                message="Understanding check questions generated",
                data={
                    "topic": topic,
                    "questions": questions_data["questions"]
                },
                metadata={"action": "check_understanding", "agent_id": self.agent_id}
            )
            
        except Exception as e:
            return self.handle_error(e, "generating understanding check questions")
    
    def _provide_feedback(self, context: Dict[str, Any]) -> AgentResponse:
        """Provide feedback on student performance"""
        
        performance_data = context.get("performance", {})
        completed_objectives = context.get("completed_objectives", [])
        
        feedback_prompt = f"""Provide constructive feedback based on the following performance:

Correct answers: {performance_data.get('correct', 0)}
Total questions: {performance_data.get('total', 0)}
Topics struggled with: {', '.join(performance_data.get('struggled_topics', []))}
Time taken: {performance_data.get('time_taken', 'unknown')}

Be encouraging while identifying areas for improvement. Suggest specific next steps."""
        
        response = self.invoke_llm(feedback_prompt)
        
        # Update completed objectives
        self.tutor_state.completed_objectives.extend(completed_objectives)
        
        return AgentResponse(
            success=True,
            message="Feedback provided",
            data={
                "feedback": response,
                "performance_summary": performance_data,
                "next_steps": self._generate_next_steps(performance_data)
            },
            metadata={"action": "provide_feedback", "agent_id": self.agent_id}
        )
    
    def _general_interaction(self, user_input: str, context: Dict[str, Any]) -> AgentResponse:
        """Handle general tutoring interactions"""
        
        # Use conversation history for context
        messages = self.format_prompt(user_input)
        response = self.invoke_llm(messages[0].content + "\n" + messages[-1].content)
        
        # Add to conversation memory
        self.add_message(HumanMessage(content=user_input))
        self.add_message(AIMessage(content=response))
        
        # Try to extract any actionable items from the response
        actionable_items = self._extract_actionable_items(response)
        
        return AgentResponse(
            success=True,
            message="Response generated",
            data={
                "response": response,
                "actionable_items": actionable_items,
                "conversation_length": len(self.get_messages())
            },
            metadata={"action": "general", "agent_id": self.agent_id}
        )
    
    def _generate_next_steps(self, performance_data: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps based on performance"""
        accuracy = performance_data.get('correct', 0) / max(performance_data.get('total', 1), 1)
        
        next_steps = []
        
        if accuracy >= 0.9:
            next_steps.append("Excellent work! Consider moving to more advanced topics.")
            next_steps.append("Try teaching this concept to someone else to solidify understanding.")
        elif accuracy >= 0.7:
            next_steps.append("Good progress! Review the topics you struggled with.")
            next_steps.append("Practice more problems in those specific areas.")
        else:
            next_steps.append("Let's revisit the fundamentals of this topic.")
            next_steps.append("Break down the concepts into smaller parts.")
            next_steps.append("Consider different learning resources or approaches.")
        
        return next_steps
    
    def _extract_actionable_items(self, response: str) -> List[str]:
        """Extract actionable items from a response"""
        actionable_keywords = [
            "try", "practice", "review", "study", "complete",
            "solve", "work through", "focus on", "consider"
        ]
        
        items = []
        sentences = response.split('.')
        
        for sentence in sentences:
            sentence_lower = sentence.lower().strip()
            if any(keyword in sentence_lower for keyword in actionable_keywords):
                items.append(sentence.strip() + ".")
        
        return items[:5]  # Limit to 5 actionable items
    
    def adapt_difficulty(self, performance_score: float) -> None:
        """Adapt difficulty based on student performance"""
        if performance_score >= 0.9:
            if self.tutor_state.difficulty_level == "beginner":
                self.tutor_state.difficulty_level = "intermediate"
            elif self.tutor_state.difficulty_level == "intermediate":
                self.tutor_state.difficulty_level = "advanced"
        elif performance_score < 0.5:
            if self.tutor_state.difficulty_level == "advanced":
                self.tutor_state.difficulty_level = "intermediate"
            elif self.tutor_state.difficulty_level == "intermediate":
                self.tutor_state.difficulty_level = "beginner"
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of the student's progress"""
        total_objectives = len(self.tutor_state.session_goals)
        completed = len(self.tutor_state.completed_objectives)
        
        return {
            "total_objectives": total_objectives,
            "completed_objectives": completed,
            "progress_percentage": (completed / total_objectives * 100) if total_objectives > 0 else 0,
            "current_topic": self.tutor_state.current_topic,
            "difficulty_level": self.tutor_state.difficulty_level,
            "completed_items": self.tutor_state.completed_objectives
        }