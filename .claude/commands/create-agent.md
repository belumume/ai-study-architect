# Create New AI Agent

Create a new AI agent following our established patterns and best practices.

## Steps:

1. First read the existing agents in `backend/app/agents/` to understand our patterns, especially:
   - LeadTutorAgent for orchestration patterns
   - Base agent class structure and interfaces
   - How agents communicate with each other

2. Think about the agent's specific responsibilities and how it fits into the multi-agent system

3. Write comprehensive unit tests FIRST (TDD approach) in `backend/tests/test_agents.py`:
   - Test the agent's core functionality
   - Test error handling
   - Test integration with other agents
   - Mock external dependencies (Ollama, databases, etc.)

4. Implement the agent in `backend/app/agents/`:
   - Follow existing naming conventions
   - Use type hints for all methods
   - Include docstrings with examples
   - Implement proper error handling
   - Use async/await patterns

5. Add integration tests to verify agent interactions

6. Update the agent registry/configuration

7. Run all tests and ensure they pass:
   ```bash
   pytest backend/tests/test_agents.py::TestYourAgent -v
   ```

8. Run linting and type checking:
   ```bash
   ruff check backend/ && mypy backend/
   ```

Agent name and description: $ARGUMENTS