# Study Architect
#### Video Demo: https://youtu.be/YOUR_VIDEO_ID

**Mastery-based AI study companion that proves you learned it.**

*By [Quantelect](https://quantelect.com)*

---

## Status

MVP in progress (~25% of full vision built):

| Component | Status |
|-----------|--------|
| User authentication (JWT/RS256) | Live |
| File upload & content extraction | Live |
| Lead Tutor Agent (Socratic chat) | Live |
| Streaming AI responses (SSE) | Live |
| Analytics dashboard | Designed ([see mockups](design/)) |
| Subject time tracking | Planned |
| Knowledge graphs | Phase 2 |
| Spaced repetition (SM-2) | Phase 2 |
| Mastery gates (90%+) | Phase 2 |

**Live**: [ai-study-architect.onrender.com](https://ai-study-architect.onrender.com) | [aistudyarchitect.com](https://aistudyarchitect.com)

## The Problem

**86% of students use AI in their studies, yet research shows they perform worse when AI support is removed.**

Students are creating cognitive debt instead of building cognitive strength. MIT research reveals AI tools reduce cognitive engagement. Swiss studies find AI usage correlates with reduced critical thinking. UPenn found students performed worse after their AI tutor was removed.

Current AI tools optimize for quick answers, not capability. Study Architect takes the opposite approach.

## The Solution

Study Architect builds cognitive strength through mastery-based learning:

- **Guided discovery** — Socratic questioning that leads to insight, not answers
- **Personalized to YOUR materials** — Upload lectures, PDFs, notes; the AI understands your specific content
- **Measurable retention** — Prove you learned it before moving on (planned: 90%+ mastery gates)
- **Analytics dashboard** — Track study time, subject progress, and learning velocity

The design follows a "tactical cyberpunk telemetry" aesthetic — see [`design/PRD.md`](design/PRD.md) for the full design system.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python), SQLAlchemy, Alembic |
| Frontend | React 18, TypeScript, Material-UI |
| Database | PostgreSQL 17 |
| AI | Claude API (primary), OpenAI (fallback), LangChain |
| Auth | JWT (RS256) with CSRF protection |
| Hosting | Render (backend), Vercel (frontend), Cloudflare (routing) |

## Running Locally

### Prerequisites
- Python 3.11+, Node.js 18+, PostgreSQL 14+
- API keys: Claude (primary) or OpenAI (fallback)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

Environment variables: see `.env.example` in both directories.

## Documentation

- **[Current direction](docs/direction/NEW_DIRECTION_2025.md)** — Mastery-based pivot rationale
- **[Architecture](docs/technical/ARCHITECTURE.md)** — System design and components
- **[Design assets](design/)** — Stitch mockups and design system
- **[Full docs index](docs/README.md)** — All documentation organized by category

## Vision

This project was born from a CS50 final project brainstorming session and grew into something larger. The long-term vision includes collective intelligence, spaced repetition scheduling, and knowledge graphs — see [`docs/vision/`](docs/vision/) for the aspirational roadmap including insights from Andrej Karpathy's "uplift team human" challenge and Paul Graham's "How to Do Great Work" framework.

## License

All rights reserved. Copyright Quantelect.
