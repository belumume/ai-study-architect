# Pragmatic Execution: Fix Broken AI Tutoring First

---
Document Level: 2
Created: August 2025
Last Updated: August 2025
Supersedes: None
Status: Active
---

## The Problem We're Actually Solving

AI tutoring is broken. Students paste questions, get answers, don't learn. We fix this.

## What "Fixed" Looks Like (MVP)

1. **AI reads YOUR content** ✓ (Done)
2. **Asks questions that make you think** (Partial - needs work)
3. **Tracks what works** (Not done - critical)
4. **Creates practice from YOUR material** (Not done - critical)

That's it. Everything else is future vision.

## The Minimal Path

### Phase 1: Make Current Chat Smarter (1-2 weeks)
Instead of just answering, the AI should:
- Ask clarifying questions back
- Challenge assumptions
- Force explanation ("explain this to a 5-year-old")
- Refuse to give direct answers too quickly

**Implementation**: Modify system prompts in `ollama_service.py`

### Phase 2: Track Learning Progress (2-3 weeks)
Simple tracking:
- What questions get asked repeatedly
- Time between questions on same topic
- Confidence indicators (user rates understanding)
- Simple spaced repetition reminders

**Implementation**: Add `learning_sessions` table, track interactions

### Phase 3: Generate Practice (2-3 weeks)
From uploaded content, create:
- Multiple choice questions
- Fill-in-the-blank exercises
- "Explain this concept" prompts
- Real-world application scenarios

**Implementation**: New endpoint `/api/v1/practice/generate`

## What We're NOT Building (Yet)

❌ 7 specialized agents (for now)
❌ Collective intelligence networks (later)
❌ B2B institutional features
❌ Revenue optimization
❌ Multi-modal processing (beyond text)
❌ Complex architectures

## Success Metrics

1. **User can't fool the AI** - It catches when they don't really understand
2. **Practice matches content** - Actually from their materials, not standardized
3. **Progress is visible** - User sees what they're learning over time
4. **It just works** - No complex setup, immediate value

## Technical Execution

### Use What's Built
- Existing auth system ✓
- File upload/processing ✓
- Chat interface ✓
- Ollama integration ✓

### Add Only What's Needed
```python
# Smarter prompting
SOCRATIC_PROMPT = """
You're a tutor helping with: {content_summary}
Never give direct answers immediately.
Ask clarifying questions.
Make the student explain their thinking.
"""

# Simple progress tracking
class LearningProgress:
    topic: str
    attempts: int
    last_seen: datetime
    confidence: float

# Practice generation
def generate_practice(content: str, level: str):
    # Use Ollama to create questions FROM the content
    pass
```

### Database Changes (Minimal)
```sql
-- Just two new tables
CREATE TABLE learning_sessions (
    user_id,
    topic,
    confidence,
    timestamp
);

CREATE TABLE practice_items (
    content_id,
    question,
    answer,
    level
);
```

## Development Order

1. **Today**: Make chat Socratic (modify prompts)
2. **This Week**: Add basic progress tracking
3. **Next Week**: Generate first practice questions
4. **Week After**: Polish and test with real students

## The Litmus Test

Before adding ANY feature, ask:
"Does this directly fix broken AI tutoring?"

If no → Skip it
If yes → Build the simplest version first

## Why This Matters

The vision docs describe the destination. This describes the first steps. Without fixing basic AI tutoring first, the grand vision is just philosophy.

Great work starts with solving real problems for real people. Everything else follows.

---

**Remember**: A working bicycle beats a blueprint for a spaceship.