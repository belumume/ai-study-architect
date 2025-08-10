# API Reference - AI Study Architect

## Base URL
- Development: `http://localhost:8000`
- Production: `https://ai-study-architect.onrender.com`
- Documentation: `/docs` (Swagger UI)
- ReDoc: `/redoc`

## Authentication
All protected endpoints require JWT Bearer token in Authorization header:
```
Authorization: Bearer <access_token>
```

## AI Service Priority
The API uses cloud-only architecture for reliability and performance:
1. **Claude (Anthropic)** - Primary, best for Socratic teaching (93.7% HumanEval)
2. **OpenAI** - Automatic fallback for seamless operation

## Endpoints

### Authentication

#### POST `/api/v1/auth/register`
Register a new user.

**Request Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "password": "string",
  "full_name": "string"
}
```

#### POST `/api/v1/auth/login`
Login and receive access token.

**Form Data:**
- `username`: string
- `password`: string

**Response:**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "username": "string"
}
```

### Chat

#### POST `/api/v1/chat/`
Main chat endpoint with Socratic questioning.

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "string"
    }
  ],
  "content_ids": ["uuid"],  // Optional: IDs of uploaded content
  "stream": true,  // Enable real-time streaming
  "temperature": 0.7,
  "max_tokens": null
}
```

**Response (Streaming):**
Server-Sent Events with real-time text chunks

**Response (Non-streaming):**
```json
{
  "message": {
    "role": "assistant",
    "content": "Socratic response asking clarifying questions..."
  },
  "session_id": "string",
  "usage": {}
}
```

#### POST `/api/v1/chat/qa`
Q&A about specific uploaded content.

**Request Body:**
```json
{
  "question": "string",
  "content_ids": ["uuid"],
  "include_summary": true,
  "include_full_text": false,
  "max_context_chars": 3000
}
```

### Content

#### POST `/api/v1/content/upload`
Upload educational materials (PDF, DOCX, PPTX, etc.).

**Form Data:**
- `file`: Binary file
- `metadata`: JSON string with title, content_type, subject

**Response:**
```json
{
  "id": "uuid",
  "message": "Content uploaded successfully",
  "title": "string",
  "content_type": "PDF|DOCX|PPTX|TEXT",
  "processing_status": "processing|completed|failed"
}
```

#### GET `/api/v1/content/`
List user's uploaded content.

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 100)

### Tutor (Lead Agent)

#### POST `/api/v1/tutor/chat`
Chat with the Lead Tutor Agent using Socratic method.

**Request Body:**
```json
{
  "message": "string",
  "action": "general|create_plan|explain_concept|check_understanding|provide_feedback",
  "context": {},
  "session_id": "string"
}
```

#### POST `/api/v1/tutor/create-study-plan`
Create a personalized study plan.

**Request Body:**
```json
{
  "goal": "string",
  "knowledge_level": "beginner|intermediate|advanced|expert",
  "time_available": "string",
  "learning_style": "visual|auditory|kinesthetic"
}
```

### Agents (7-Agent System)

#### POST `/api/v1/agents/content-understanding`
Process educational materials with the Content Understanding Agent.

**Request Body:**
```json
{
  "content": "string",
  "content_type": "PDF|DOCX|TEXT",
  "extract_concepts": true,
  "create_embeddings": true
}
```

#### POST `/api/v1/agents/knowledge-synthesis`
Create connections between concepts with the Knowledge Synthesis Agent.

**Request Body:**
```json
{
  "concepts": ["string"],
  "learning_objectives": ["string"],
  "create_personalized_explanations": true
}
```

#### POST `/api/v1/agents/practice-generation`
Generate custom exercises with the Practice Generation Agent.

**Request Body:**
```json
{
  "topic": "string",
  "difficulty_level": "beginner|intermediate|advanced",
  "exercise_type": "multiple_choice|short_answer|essay",
  "target_weaknesses": ["string"]
}
```

#### POST `/api/v1/agents/progress-tracking`
Monitor learning patterns with the Progress Tracking Agent.

**Request Body:**
```json
{
  "session_data": {},
  "performance_metrics": {},
  "adjust_difficulty": true
}
```

#### POST `/api/v1/agents/assessment`
Evaluate true comprehension with the Assessment Agent.

**Request Body:**
```json
{
  "student_response": "string",
  "expected_concepts": ["string"],
  "evaluate_understanding": true
}
```

#### POST `/api/v1/agents/collaboration`
Enable collective intelligence with the Collaboration Agent.

**Request Body:**
```json
{
  "learning_patterns": {},
  "anonymous_sharing": true,
  "collective_insights": true
}
```

### Admin

#### GET `/api/v1/admin/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "ai_service": "claude|openai",
  "timestamp": "2025-08-06T00:00:00Z"
}
```

## Streaming Response Format

When `stream: true`, responses use Server-Sent Events:

```javascript
// Connection established
data: {"type": "connection", "session_id": "..."}

// Content chunks
data: {"type": "content", "content": "char", "index": 0}

// Completion
data: {"type": "complete", "message": {...}, "usage": {...}}

// Error
data: {"type": "error", "error": "..."}
```

## Error Responses

All errors follow this format:
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

Common status codes:
- `401`: Unauthorized - Invalid or missing token
- `403`: Forbidden - CSRF validation failed or insufficient permissions
- `404`: Not Found - Resource doesn't exist
- `422`: Validation Error - Invalid request data
- `429`: Too Many Requests - Rate limit exceeded
- `503`: Service Unavailable - AI service not available

## Rate Limits

- Authentication: 5 requests/minute
- Chat endpoints: 20 requests/minute
- Content upload: 10 requests/minute
- General API: 60 requests/minute

## CSRF Protection

For state-changing requests, include CSRF token in header:
```
X-CSRF-Token: <token_from_cookie>
```

Exempt endpoints:
- `/api/v1/auth/*`
- `/api/v1/chat/` (uses JWT authentication)
- `/api/v1/health`

## WebSocket Support (Planned)

Future real-time features will use WebSocket at:
```
ws://localhost:8000/ws
```