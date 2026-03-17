"""Tests for the Lead Tutor Agent"""

from unittest.mock import Mock

import pytest

from app.agents.lead_tutor import LeadTutorAgent


class TestLeadTutorAgent:
    """Test suite for Lead Tutor Agent"""

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM responses for different scenarios"""
        return {
            "create_plan": """
            {
                "title": "Python Programming Fundamentals",
                "description": "Learn Python basics and build practical projects",
                "total_hours": 20,
                "objectives": [
                    {
                        "id": "obj1",
                        "title": "Python Basics",
                        "description": "Variables, data types, and control flow",
                        "estimated_hours": 5,
                        "topics": ["variables", "data types", "if statements", "loops"],
                        "prerequisites": [],
                        "resources": ["Python official tutorial", "Practice exercises"]
                    },
                    {
                        "id": "obj2",
                        "title": "Functions and Modules",
                        "description": "Creating reusable code",
                        "estimated_hours": 5,
                        "topics": ["functions", "parameters", "return values", "modules"],
                        "prerequisites": ["obj1"],
                        "resources": ["Function exercises", "Module examples"]
                    }
                ],
                "milestones": [
                    {
                        "title": "Complete Basics",
                        "description": "Can write simple Python programs",
                        "objectives_required": ["obj1"]
                    }
                ],
                "recommendations": [
                    "Practice coding daily for 30 minutes",
                    "Build small projects to reinforce learning"
                ]
            }
            """,
            "explain_concept": """
            Understanding Functions in Python
            
            **Overview**: Functions are reusable blocks of code that perform specific tasks.
            
            **Key Concepts**:
            1. **Definition**: Use 'def' keyword to create a function
            2. **Parameters**: Input values the function accepts
            3. **Return Values**: Output the function produces
            
            **Example**:
            ```python
            def greet(name):
                return f"Hello, {name}!"
            ```
            
            **Practice**: Try creating functions for common tasks you do repeatedly.
            """,
            "check_understanding": """
            {
                "questions": [
                    {
                        "id": "q1",
                        "question": "What keyword is used to define a function in Python?",
                        "type": "comprehension",
                        "options": ["def", "func", "function", "define"],
                        "correct_answer": "def",
                        "explanation": "The 'def' keyword is used to define functions in Python"
                    },
                    {
                        "id": "q2",
                        "question": "What will this function return? def add(a, b): return a + b",
                        "type": "application",
                        "options": ["The sum of a and b", "Nothing", "An error", "The string 'a + b'"],
                        "correct_answer": "The sum of a and b",
                        "explanation": "The function returns the sum of the two parameters"
                    }
                ]
            }
            """,
            "general": "I understand you want to learn Python. Let's start with the basics and build from there. What specific aspect would you like to focus on first?",
        }

    @pytest.fixture
    def lead_tutor(self):
        """Create a Lead Tutor Agent instance"""
        agent = LeadTutorAgent(agent_id="test_tutor", temperature=0.7)
        return agent

    def test_create_study_plan(self, lead_tutor, mock_llm_response):
        """Test creating a personalized study plan"""
        # Mock the LLM response
        lead_tutor.invoke_llm = Mock(return_value=mock_llm_response["create_plan"])

        # Test input
        input_data = {
            "user_input": "I want to learn Python programming",
            "user_id": "test_user_123",
            "action": "create_plan",
            "knowledge_level": "beginner",
            "time_available": "2 weeks",
            "learning_style": "visual",
        }

        # Process the request
        response = lead_tutor.process(input_data)

        # Assertions
        assert response.success is True
        assert response.message == "Study plan created successfully"
        assert "study_plan" in response.data
        assert response.data["study_plan"]["title"] == "Python Programming Fundamentals"
        assert len(response.data["study_plan"]["objectives"]) == 2
        assert response.data["study_plan"]["total_hours"] == 20

        # Check state update
        assert lead_tutor.tutor_state.current_topic == "I want to learn Python programming"
        assert lead_tutor.tutor_state.current_plan is not None

    def test_explain_concept(self, lead_tutor, mock_llm_response):
        """Test explaining a concept"""
        # Mock the LLM response
        lead_tutor.invoke_llm = Mock(return_value=mock_llm_response["explain_concept"])

        # Test input
        input_data = {
            "user_input": "functions in Python",
            "user_id": "test_user_123",
            "action": "explain_concept",
            "learning_style": "visual",
            "prior_knowledge": ["variables", "basic syntax"],
        }

        # Process the request
        response = lead_tutor.process(input_data)

        # Assertions
        assert response.success is True
        assert response.message == "Concept explained"
        assert "explanation" in response.data
        assert "Functions" in response.data["explanation"]
        assert response.data["concept"] == "functions in Python"
        assert response.data["learning_style"] == "visual"

    def test_check_understanding(self, lead_tutor, mock_llm_response):
        """Test generating understanding check questions"""
        # Mock the LLM response
        lead_tutor.invoke_llm = Mock(return_value=mock_llm_response["check_understanding"])

        # Test input
        input_data = {
            "user_input": "Python functions",
            "user_id": "test_user_123",
            "action": "check_understanding",
        }

        # Process the request
        response = lead_tutor.process(input_data)

        # Assertions
        assert response.success is True
        assert response.message == "Understanding check questions generated"
        assert "questions" in response.data
        assert len(response.data["questions"]) == 2
        assert response.data["questions"][0]["correct_answer"] == "def"

    def test_provide_feedback(self, lead_tutor):
        """Test providing feedback on performance"""
        # Mock the LLM response
        lead_tutor.invoke_llm = Mock(return_value="Great job! You got 4 out of 5 correct.")

        # Test input
        input_data = {
            "user_id": "test_user_123",
            "action": "provide_feedback",
            "performance": {
                "correct": 4,
                "total": 5,
                "struggled_topics": ["recursion"],
                "time_taken": "10 minutes",
            },
            "completed_objectives": ["obj1"],
        }

        # Process the request
        response = lead_tutor.process(input_data)

        # Assertions
        assert response.success is True
        assert response.message == "Feedback provided"
        assert "feedback" in response.data
        assert "next_steps" in response.data
        assert len(response.data["next_steps"]) > 0
        assert "obj1" in lead_tutor.tutor_state.completed_objectives

    def test_general_interaction(self, lead_tutor, mock_llm_response):
        """Test general tutoring interaction"""
        # Mock the LLM response
        lead_tutor.invoke_llm = Mock(return_value=mock_llm_response["general"])

        # Test input
        input_data = {"user_input": "I want to learn Python", "user_id": "test_user_123"}

        # Process the request
        response = lead_tutor.process(input_data)

        # Assertions
        assert response.success is True
        assert response.message == "Response generated"
        assert "response" in response.data
        assert "Python" in response.data["response"]
        assert "actionable_items" in response.data

    def test_adapt_difficulty(self, lead_tutor):
        """Test difficulty adaptation based on performance"""
        # Test increasing difficulty
        lead_tutor.tutor_state.difficulty_level = "beginner"
        lead_tutor.adapt_difficulty(0.95)
        assert lead_tutor.tutor_state.difficulty_level == "intermediate"

        lead_tutor.adapt_difficulty(0.92)
        assert lead_tutor.tutor_state.difficulty_level == "advanced"

        # Test decreasing difficulty
        lead_tutor.adapt_difficulty(0.3)
        assert lead_tutor.tutor_state.difficulty_level == "intermediate"

        lead_tutor.adapt_difficulty(0.4)
        assert lead_tutor.tutor_state.difficulty_level == "beginner"

    def test_get_progress_summary(self, lead_tutor):
        """Test getting progress summary"""
        # Set up some progress
        lead_tutor.tutor_state.session_goals = ["goal1", "goal2", "goal3"]
        lead_tutor.tutor_state.completed_objectives = ["goal1", "goal2"]
        lead_tutor.tutor_state.current_topic = "Python basics"
        lead_tutor.tutor_state.difficulty_level = "intermediate"

        # Get summary
        summary = lead_tutor.get_progress_summary()

        # Assertions
        assert summary["total_objectives"] == 3
        assert summary["completed_objectives"] == 2
        assert summary["progress_percentage"] == pytest.approx(66.67, 0.01)
        assert summary["current_topic"] == "Python basics"
        assert summary["difficulty_level"] == "intermediate"

    def test_extract_actionable_items(self, lead_tutor):
        """Test extracting actionable items from response"""
        response = """
        Let's start with the basics. Try writing a simple Hello World program.
        Practice using variables and data types. Review the Python documentation.
        Once comfortable, consider building a small calculator project.
        """

        items = lead_tutor._extract_actionable_items(response)

        # Should find actionable items
        assert len(items) > 0
        assert any("Try writing" in item for item in items)
        assert any("Practice using" in item for item in items)
        assert any("Review the" in item for item in items)

    def test_error_handling(self, lead_tutor):
        """Test error handling in the agent"""
        # Mock LLM to raise an exception
        lead_tutor.invoke_llm = Mock(side_effect=Exception("LLM connection failed"))

        # Test input
        input_data = {
            "user_input": "Explain functions",
            "user_id": "test_user_123",
            "action": "explain_concept",
        }

        # Process the request
        response = lead_tutor.process(input_data)

        # Assertions
        assert response.success is False
        assert "error occurred" in response.message.lower()
        assert len(response.errors) > 0
        assert "LLM connection failed" in response.errors[0]

    def test_create_study_plan_fallback_on_invalid_json(self, lead_tutor):
        """Test fallback study plan when LLM returns unparseable response."""
        lead_tutor.invoke_llm = Mock(
            return_value="Here's a study plan for Python: start with variables, then functions..."
        )

        input_data = {
            "user_input": "I want to learn Python",
            "user_id": "test_user_123",
            "action": "create_plan",
            "knowledge_level": "beginner",
            "time_available": "2 weeks",
            "learning_style": "visual",
        }

        response = lead_tutor.process(input_data)

        assert response.success is True
        assert (
            "basic study plan" in response.message.lower()
            or "study plan" in response.message.lower()
        )
        assert "study_plan" in response.data
        plan = response.data["study_plan"]
        assert plan["title"].startswith("Study Plan:")
        assert len(plan["objectives"]) == 2
        assert plan["objectives"][0]["title"] == "Foundation"
        assert plan["objectives"][1]["title"] == "Practice"
        assert plan["total_hours"] == 25
        assert "raw_response" in response.data

    def test_create_study_plan_fallback_on_partial_json(self, lead_tutor):
        """Test fallback when LLM returns truncated/malformed JSON."""
        lead_tutor.invoke_llm = Mock(
            return_value='{"title": "Python Plan", "description": "Learn Python", "total_hours": 20, "objectives": [{'
        )

        input_data = {
            "user_input": "Learn Python",
            "user_id": "test_user_123",
            "action": "create_plan",
        }

        response = lead_tutor.process(input_data)

        assert response.success is True
        assert "study_plan" in response.data
        plan = response.data["study_plan"]
        assert plan["total_hours"] == 25
        assert len(plan["objectives"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
