# AI Study Architect Glossary

---
Document Level: 4
Created: August 2025
Last Updated: August 2025 (Comprehensive Expansion)
Supersedes: None
Status: Active
---

This glossary establishes consistent terminology across all AI Study Architect documentation.

## Core Architecture Terms

### Multi-Agent System
The architecture of AI Study Architect consisting of 7 specialized AI agents working together to create personalized learning experiences. Each agent has a specific responsibility and communicates through standardized interfaces.

### The Seven Agents (Canonical Definition)
1. **Lead Tutor Agent**: Orchestrates the entire learning experience and coordinates other agents
2. **Content Understanding Agent**: Processes educational materials (PDFs, lectures, notes) into structured knowledge
3. **Knowledge Synthesis Agent**: Creates connections between concepts and generates personalized explanations
4. **Practice Generation Agent**: Develops custom exercises targeting specific learning opportunities
5. **Progress Tracking Agent**: Monitors learning patterns and adjusts challenge level
6. **Assessment Agent**: Evaluates true comprehension, not just correctness
7. **Collaboration Agent**: Enables collective intelligence through privacy-preserving group learning

### Sub-Agents (Claude Code Development)
1. **content-processor**: Processes uploaded educational content (PDFs, videos, notes)
2. **test-writer**: Creates comprehensive tests with 80% coverage target
3. **security-auditor**: Reviews code for security vulnerabilities
4. **ai-tutor**: Implements AI-powered educational features using LangChain/Ollama
5. **db-optimizer**: Optimizes database queries and adds indexes

### Multi-Agent Architecture
The use of seven specialized AI agents working in concert to provide comprehensive learning support, each focusing on a specific aspect of the educational experience.

### Understanding-Focused Collaboration
The ability to share learning insights and patterns across users to amplify collective intelligence, using anonymization techniques where appropriate.

## Vision & Philosophy Terms

### Great Work
Following Paul Graham's definition: work that outlives its creators and fundamentally advances human capability. AI Study Architect aspires to be "great work" in educational technology.

### Individual to Collective Evolution
The transformation from helping individual students learn to enabling humanity to advance collectively through shared insights and networked learning.

### Understanding Over Answers
Our core philosophy that optimizes for deep comprehension rather than quick solutions. The system introduces appropriate challenges when they aid learning.

### The Core Problem (AI Learning Paradox)
"86% of students use AI in their studies, yet research shows they perform worse when AI support is removed. Students are receiving surface-level help instead of building cognitive strength."

### Uplift Team Human
From Andrej Karpathy's challenge: creating technology specifically designed to help humanity rise alongside AI advancement.

## Technical Terms

### Ollama
AI model server that enables flexible AI processing with user control over data handling. Used for chat functionality and content processing.

### FastAPI
Modern Python web framework used for building the backend API. Chosen for its performance, automatic documentation, and type hints support.

### pg8000
Pure Python PostgreSQL database driver used for Windows compatibility, avoiding binary dependencies.

### Alembic
Database migration tool used with SQLAlchemy to manage database schema changes over time.

### Pydantic
Data validation library that uses Python type annotations to validate, serialize, and document data structures.

### Agent Orchestration
The process by which the Lead Tutor Agent coordinates the activities of other agents to create a coherent learning experience.

### Vector Store
Database optimized for storing and searching vector embeddings of educational content, enabling semantic search and concept matching.

### Embedding
Numerical representation of text or concepts that captures semantic meaning, allowing AI to understand relationships between ideas.

### Streaming Response
Real-time delivery of AI-generated content as it's being created, rather than waiting for complete generation.

### Server-Sent Events (SSE)
Web standard for pushing real-time updates from server to browser, used for streaming AI responses.

### CSRF Token
Cross-Site Request Forgery protection token that verifies request authenticity using double-submit cookie pattern.

### JWT (JSON Web Token)
Secure method for transmitting information between parties as JSON objects, used for user authentication.

### Magic Byte Detection
File type validation technique that examines the actual file content rather than relying on file extensions.

### Multimodal Processing
The ability to understand and process different types of content: text, images, PDFs, audio, video, and handwritten notes.

## User Experience Terms

### Content Processing Pipeline
The complete workflow from file upload through text extraction, AI analysis, and storage of processed content.

### Q&A Functionality
System capability to answer questions about uploaded content using AI with context from extracted text.

### Chat History Persistence
Feature to maintain conversation context across browser sessions (currently not implemented).

### Graceful Degradation
System design principle where features continue to work even when optional services (like Redis or Ollama) are unavailable.

### Study Circle
A small group of learners working together with AI facilitation, where insights compound through collaboration.

### Teach-Back Protocol
Learning verification method where students explain concepts to prove mastery, following the principle "you don't understand something until you can teach it."

### Adaptive Difficulty
The system's ability to automatically adjust challenge level based on demonstrated comprehension and learning speed.

### Knowledge Artifact
Student-created explanations or materials that become learning resources for future students.

### Learning Loop
The complete cycle from encountering a new concept to achieving mastery, facilitated by the multi-agent system.

## Implementation Status Terms

### Karpathy Challenge
Andrej Karpathy's call to "uplift team human" - creating technology designed to help humanity rise alongside AI advancement.

### Windows/WSL Compatibility
Development considerations for running the system on Windows with Windows Subsystem for Linux, including sync-only database operations.

### Understanding-First Architecture
Design philosophy prioritizing effective learning and comprehension with flexible processing options for different use cases.

### Implemented
Features or agents that are currently functional in the codebase.

### Planned
Features or agents that are designed but not yet implemented.

### MVP (Minimum Viable Product)
The core features required for initial launch: authentication, file upload, content processing, and basic AI chat.

### Post-MVP
Features planned for implementation after initial launch, such as collaborative learning and advanced analytics.

## Privacy & Security Terms

### Differential Privacy
Mathematical technique for sharing insights from datasets while protecting individual privacy through controlled noise addition.

### Federated Learning
Machine learning approach where models are trained on distributed data without centralizing sensitive information.

### Zero-Knowledge Proofs
Cryptographic method for proving knowledge of information without revealing the information itself.

### Homomorphic Encryption
Encryption technique that allows computation on encrypted data without decrypting it first.

### CRDTs (Conflict-free Replicated Data Types)
Data structures that can be replicated across multiple systems and updated in parallel seamlessly.

### Double-Submit Cookie Pattern
CSRF protection method using both cookies and headers to verify request authenticity.

### RS256
The JWT signing algorithm using RSA public/private key pairs, more secure than HS256.

### PII (Personally Identifiable Information)
Any data that could identify a specific individual, handled with extra security measures.

### Anonymized Insights
Learning patterns and successful strategies shared without any identifying information.

## Educational Terms

### Delta Mindset
Philosophy from Delta Residency focusing on rapid iteration and public building to "increase surface area of luck."

### 80/20 Rule
Principle of focusing on the 20% of features that deliver 80% of the value, emphasized in Delta's MVP approach.

### Press Release Approach
Starting with the end goal in mind, thinking about the final outcome before beginning implementation.

### Effective Learning
Appropriate challenge that promotes deeper learning through well-calibrated engagement with material.

### Comprehension vs Completion
Measuring true understanding of concepts rather than just task completion or correct answers.

### Spaced Repetition
Learning technique where concepts are reviewed at increasing intervals to optimize retention.

### Zone of Proximal Development
The sweet spot between what a learner can do alone and what they can't do even with help - where optimal learning occurs.

## Usage Guidelines

1. **Consistency**: Always use these terms as defined across all documentation
2. **Clarity**: When introducing a term for the first time in a document, consider linking to this glossary
3. **Evolution**: As new terms emerge, add them here with clear definitions
4. **Context**: Some terms may have different meanings in other contexts - these definitions apply specifically to AI Study Architect

## Development Terms

### Browser Cache Issue
Common development problem where Chrome aggressively caches ES modules, resolved by using DevTools "Disable cache" option.

### Agent Orchestration (Development)
Coordination between Claude Code sub-agents for specialized tasks while preserving main conversation context.

### Proactive Agent Activation
Sub-agents automatically engaging based on context triggers without explicit user requests.

### Magic Byte Validation
Security technique examining actual file content headers to verify file types beyond extension checking.

### Rate Limiting
Security mechanism that restricts the number of requests a user can make within a time period.

### Connection Pooling
Database optimization technique that reuses connections to improve performance and resource management.

## Collective Intelligence Terms

### Study Circles
Small collaborative learning groups facilitated by AI where insights compound through group interaction.

### Teach-Back Protocol
Learning verification method where students explain concepts to prove mastery, based on "you don't understand until you can teach it."

### Creation Challenges
Learning activities where students build something new after mastering content, transitioning from consumption to creation.

### Knowledge Artifacts
Student-created explanations or materials that become learning resources for future students.

### Anonymized Insights
Learning patterns and successful strategies shared across the collective without revealing individual identity.

### Understanding-Focused Collaboration
Techniques enabling group learning and knowledge sharing while maintaining appropriate privacy and user control.

### Collective Problem Solving
Approach where groups tackle challenges that no individual could solve alone, leveraging distributed intelligence.

### Network Effects
Value increase that occurs when more people use the platform, creating compounding benefits for all participants.

## Architecture Evolution Terms

### Hub and Spoke (Current)
Architecture pattern where individual students connect directly to AI agents without peer interaction.

### Network of Networks (Future)
Evolved architecture enabling peer collaboration while maintaining individual AI agent relationships.

### Insight Networks
System where breakthrough moments from one learner ripple to benefit others through privacy-preserving sharing.

### Flywheel Effect
Business concept where small actions compound into momentum, emphasized in Delta's rapid iteration philosophy.

### Surface Area of Luck
Delta concept that increasing public activity and iterations creates more opportunities for success.

## Platform-Specific Terms

### Material-UI
React component library used for consistent and accessible user interface design.

### Vite
Fast build tool for modern web projects, used for the frontend development server.

### TypeScript
Statically-typed superset of JavaScript that helps catch errors during development.

### SQLAlchemy
Python ORM (Object-Relational Mapping) library used for database operations.

### Redis
In-memory data structure store used for caching and session management.

### WebRTC
Web standard for peer-to-peer communication, planned for future collaborative features.

### IPFS (InterPlanetary File System)
Distributed storage protocol planned for decentralized knowledge sharing.

## Common Misconceptions to Avoid

- **"6 agents" or "5 agents"**: The canonical definition is 7 main agents plus 5 development sub-agents
- **"Making learning easier"**: We optimize for effectiveness and understanding, which may include effective challenges
- **"Just another AI tutor"**: We're building a multi-agent system focused on deep understanding, not quick answers
- **"Cloud-only"**: We offer flexible processing options for different privacy needs
- **"Individual vs Collective"**: These aren't in tension - strong individuals make strong collectives
- **"Redis vs Browser Cache"**: These are separate systems - server-side caching vs client-side JavaScript caching

---

This glossary is a living document. Update it whenever new terms are introduced or existing terms need clarification.