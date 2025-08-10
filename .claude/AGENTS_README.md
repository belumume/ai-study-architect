# AI Study Architect Sub-Agents

This directory contains specialized sub-agents for the AI Study Architect project. Each agent has specific expertise and will be automatically invoked by Claude Code when appropriate.

## Available Agents

### 🔍 content-processor
**Purpose**: Process uploaded educational content (PDFs, videos, notes)
**Triggers**: 
- File uploads
- Content analysis requests
- Text extraction needs

**Example usage**:
```
> Use the content-processor agent to extract key concepts from the uploaded PDF
```

### 🧪 test-writer
**Purpose**: Create comprehensive tests with 80% coverage target
**Triggers**:
- After implementing new features
- When test coverage is low
- TDD workflows

**Example usage**:
```
> Have the test-writer create tests for the new content upload endpoint
```

### 🔒 security-auditor
**Purpose**: Review code for security vulnerabilities
**Triggers**:
- After authentication changes
- New API endpoints
- Before deployments

**Example usage**:
```
> Ask the security-auditor to review the file upload implementation
```

### 🤖 ai-tutor
**Purpose**: Implement AI-powered educational features
**Triggers**:
- LangChain/LangGraph implementation
- Ollama integration
- Educational AI features

**Example usage**:
```
> Use the ai-tutor agent to implement the practice problem generator
```

### ⚡ db-optimizer
**Purpose**: Optimize database queries and add indexes
**Triggers**:
- Slow query detection
- New database queries
- Performance issues

**Example usage**:
```
> Have the db-optimizer analyze the content listing query for N+1 problems
```

## How Sub-Agents Work

1. **Automatic Invocation**: Claude Code will automatically delegate tasks based on the agent descriptions
2. **Explicit Requests**: You can specifically request an agent by mentioning it
3. **Separate Context**: Each agent works in its own context window
4. **Specialized Tools**: Each agent has access to specific tools needed for their tasks

## Best Practices

1. **Let agents be proactive**: The descriptions include "PROACTIVELY" and "MUST BE USED" to encourage automatic use
2. **Combine agents**: Multiple agents can work on different aspects of the same feature
3. **Trust the expertise**: Each agent has detailed domain knowledge

## Managing Agents

To view or modify agents:
```
/agents
```

This opens an interactive interface where you can:
- View all agents
- Edit agent configurations
- Modify tool permissions
- Create new agents

## Tips

- Agents will preserve your main conversation context
- Results from agents are integrated into your main workflow
- Agents can call other agents when needed
- Check agent performance in the Claude Code output