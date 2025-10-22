# AI Study Architect
#### Video Demo: https://youtu.be/YOUR_VIDEO_ID
#### Description:

## Live Deployment

- **Backend API**: https://ai-study-architect.onrender.com
- **API Documentation**: https://ai-study-architect.onrender.com/docs
- **Frontend**: https://ai-study-architect.onrender.com (Vercel hosted)

## What is AI Study Architect?

AI Study Architect is a revolutionary **AI-powered learning system** that transforms how students learn by **making them think deeper, not think less** through Socratic questioning. 

**The Core Philosophy**: In a world flooded with AI tutoring tools that simply give answers, AI Study Architect stands apart by optimizing for deep understanding. We believe the best AI doesn't replace human thinking - it makes human thinking more powerful.

**What Makes Us Different**:
- **Socratic Method**: Instead of giving answers, we ask questions that guide you to discover solutions yourself
- **Smart AI Priority**: Claude (best for education) → OpenAI (fallback)
- **Understanding Over Answers**: We guide you to insights rather than handing you solutions
- **Personalized to YOUR Materials**: We read and understand your specific course content, not generic examples
- **Optimized for Performance**: Cloud AI services for best educational experience
- **Effective Learning**: We optimize for deep understanding through appropriate challenge and support

## Project Genesis

This project was born from a simple yet powerful observation during a CS50 final project brainstorming session:

> **"I realized students are using AI to get answers, but they're not actually learning."**

Starting from "I'm clueless about idea," through collaborative brainstorming with Claude.ai, we discovered what MIT research now calls "cognitive debt" - students using AI in ways that harm rather than help their learning. This insight became the foundation for AI Study Architect - an AI system that builds thinking skills rather than replacing them.

[Read the full genesis story →](docs/PROJECT_GENESIS.md)

## The AI Learning Paradox We Solve

**86% of students use AI in their studies, yet research shows they perform worse when AI support is removed.** Students are creating cognitive debt instead of building cognitive strength.

MIT research reveals students using AI tools show lower cognitive engagement and worse recall. Swiss studies find AI usage correlates with reduced critical thinking. The University of Pennsylvania found students performed worse after their AI tutor was removed.

**The Problem**: Current AI tools provide immediate answers that optimize for quick answers, not capability. Students get quick help but don't develop deep understanding.

## Our Solution: Making You Think, Not Just Answer

AI Study Architect takes a fundamentally different approach from other AI tutors:

**Our Approach**:
- Guided discovery through Socratic questioning
- Personalized to YOUR actual course materials
- Works with various AI model providers
- Seven specialized agents orchestrating together
- Understanding-focused collective intelligence
- Deep understanding through effective learning

**How It Works**:
1. **Process YOUR Materials**: Upload lectures, PDFs, notes - we understand YOUR specific content
2. **Orchestrate Learning**: 7 specialized agents work together like a teaching team
3. **Guide, Don't Tell**: We lead you to insights through effective learning
4. **Track True Understanding**: Measure comprehension, not just correct answers
5. **Evolve Together**: Your learning patterns help others (anonymously) while preserving privacy

## Technical Architecture

### Multi-Agent System
The project is designed around seven specialized AI agents working together (currently in phased implementation):

1. **Lead Tutor Agent**: Orchestrates the entire learning experience with Socratic questioning [LIVE]
   - Creates personalized study plans
   - Explains concepts tailored to learning style
   - Generates understanding check questions
   - Provides feedback and adapts difficulty
2. **Content Understanding Agent**: Processes educational materials (PDFs, lectures, notes) into structured knowledge [PLANNED]
3. **Knowledge Synthesis Agent**: Creates connections between concepts and generates personalized explanations [PLANNED]
4. **Practice Generation Agent**: Develops custom exercises targeting specific weaknesses [PLANNED]
5. **Progress Tracking Agent**: Monitors learning patterns and adjusts difficulty [PLANNED]
6. **Assessment Agent**: Evaluates true comprehension, not just correctness [PLANNED]
7. **Collaboration Agent**: Enables collective intelligence through privacy-preserving group learning [PLANNED]

Note: While only the Lead Tutor Agent is fully implemented, it provides multiple educational functions through specialized actions. The remaining agents are part of the full vision and will be implemented in future phases.

### Technology Stack

**Backend (FastAPI + Python)**:
- FastAPI for high-performance async API endpoints
- SQLAlchemy with PostgreSQL for robust data persistence
- pg8000 driver for Windows compatibility
- Redis for caching and session management
- JWT authentication with RS256 for security
- Multi-part form handling for file uploads

**Frontend (React + TypeScript)**:
- React 18 with TypeScript for type-safe development
- Material-UI for professional, responsive design
- Axios with interceptors for API communication
- Real-time streaming for AI responses
- Drag-and-drop file upload interface

**AI Integration**:
- **Cloud-Only Architecture**: Enterprise-grade AI services for reliability and performance
- **Primary Service**: Claude (Anthropic) for superior educational reasoning and Socratic questioning
- **Automatic Fallback**: Claude → OpenAI for high availability (99.9%+ uptime)
- **Real Streaming**: Server-sent events (SSE) for live AI response streaming
- **Content Analysis**: AI-powered extraction of key concepts and learning objectives from uploaded materials
- **Socratic Questioning**: Built-in educational prompts optimized for deep learning, not just answers

### Security & Privacy

We implement security best practices throughout:

- **RS256 JWT tokens** for enhanced authentication security
- **CSRF protection** with double-submit cookie pattern
- **Input validation** on all user data with sanitization
- **Rate limiting** on all endpoints to prevent abuse
- **Content validation** for uploaded materials
- **Comprehensive file validation** including content checking
- **Text-only storage** - we extract and store text, not original files

## Design Decisions

### Why Multi-Agent Architecture?

Learning is complex and multifaceted. Our specialized agents provide:
- Focused expertise for different aspects of learning
- Better performance through specialized optimization
- Scalable architecture that grows with new capabilities
- More nuanced and contextual responses
- Separate concerns for better maintainability
- Enable future expansion with new capabilities

### Why FastAPI + React?

This combination provides:
- Type safety across the full stack
- Excellent developer experience
- Production-ready performance
- Strong ecosystem support
- Easy deployment options

## Key Features Implemented

1. **Secure Authentication**: JWT-based auth with refresh tokens
2. **File Upload & Processing**: Support for multiple file types with validation
3. **Content Extraction**: Automated text extraction from various formats
4. **AI-Powered Q&A**: Context-aware responses based on uploaded materials
5. **Real-time Chat**: Streaming responses for natural conversation flow
6. **Progress Tracking**: Database persistence of learning sessions

## Challenges Overcome

### PostgreSQL Connection Issues
Spent 12+ hours debugging connection issues that turned out to be port configuration (5433 vs 5432). Built comprehensive diagnostic tools to identify the root cause.

### Browser Caching
Discovered Chrome aggressively caches ES modules. Implemented cache-busting strategies and documented the solution for future developers.

### Windows Compatibility
Converted from async SQLAlchemy to sync version for Windows compatibility. Adapted Redis configuration for WSL environment.

### Content Processing
Implemented robust file type detection using magic bytes rather than relying on file extensions, preventing security vulnerabilities.

## Future Vision

This project is designed to "outlive the course" as CS50 encourages. Future enhancements include:

- **Practice Problem Generation**: AI creates exercises based on your materials
- **Collaborative Learning**: Match students with complementary strengths
- **Spaced Repetition**: Optimize review timing for maximum retention
- **Multi-Modal Support**: Process images, audio, and video content
- **Institutional Integration**: API for schools to integrate with LMS
- **Open Source Community**: Build ecosystem of educational AI tools

## Running the Project

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis (for caching and agent state)
- API keys for Claude (primary) or OpenAI (fallback)

### Live Demo
- Backend API: https://ai-study-architect.onrender.com
- Interactive docs: https://ai-study-architect.onrender.com/docs

### Backend Setup
```bash
cd backend
python -m venv venv
./venv/Scripts/activate  # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Environment Configuration
Create `.env` files in both backend and frontend directories with required variables (see `.env.example` files).

## Testing

The project includes comprehensive testing strategies:
- Unit tests for critical functions
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Manual testing protocols documented

## Conclusion

AI Study Architect represents more than just a CS50 final project - it's a vision for the future of education. By combining cutting-edge AI technology with a deep understanding of student needs, we're building a tool designed to genuinely improve learning outcomes. The project demonstrates proficiency across the entire CS50 curriculum: from low-level file processing in Python to high-level React interfaces, from SQL database design to advanced AI integration.

Most importantly, this project solves a real problem that affects millions of students worldwide. In an age where AI is transforming every industry, education cannot be left behind. AI Study Architect ensures that students have access to personalized, intelligent tutoring regardless of their economic circumstances or geographic location.

This is just the beginning. With the foundation we've built, AI Study Architect has the potential to transform how humanity learns, making quality education accessible to everyone, everywhere.

## The Vision Evolution

**August 2025 Update**: Inspired by Andrej Karpathy's challenge to "uplift team human," we're expanding our vision from individual learning to collective human advancement. Students will not only learn better individually but contribute to humanity's collective intelligence through privacy-preserving collaboration. See our [Collective Intelligence Vision](docs/COLLECTIVE_INTELLIGENCE_VISION.md) for details.

---

*Built with passion for CS50x 2025*