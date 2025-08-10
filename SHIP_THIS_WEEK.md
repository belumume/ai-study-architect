# Ship This Week

*Stop dreaming. Start shipping. Concrete tasks with code.*

## Week of August 5, 2025

### ✅ Monday: Thinking-First Timer
**What**: Force 2 minutes of thinking before AI responds
**Why**: MIT study shows starting with AI harms learning
**How**:
```python
# backend/app/api/v1/chat.py
async def chat_message(request: ChatRequest):
    if request.enable_thinking_timer:
        # Store question with timestamp
        await redis_cache.set(f"thinking:{user_id}", {
            "question": request.message,
            "asked_at": datetime.now(),
            "unlock_at": datetime.now() + timedelta(minutes=2)
        })
        return {"message": "Think about this for 2 minutes. I'll respond then."}
```
**Ship by**: End of day
**Success metric**: Feature live, 10 users try it

### 🚧 Tuesday: Teach-Back Mode
**What**: AI plays confused student, user explains
**Why**: Teaching deepens understanding (rubber duck effect amplified)
**How**:
```python
CONFUSED_STUDENT_PROMPT = """
You are a confused student. Ask clarifying questions like:
- "Wait, why does that happen?"
- "Can you explain that differently?"
- "I don't get how that connects to..."
Never provide answers, only questions.
"""
```
**Ship by**: End of day
**Success metric**: Mode switchable, generates questions

### 🚧 Wednesday: Just Chat (No Upload)
**What**: Start learning without materials
**Why**: Best learning happens from curiosity
**How**:
```typescript
// frontend/src/components/chat/QuickStart.tsx
<Button onClick={() => navigate('/chat/explore')}>
  Just Start Chatting (No Upload Needed)
</Button>
```
**Ship by**: End of day
**Success metric**: New route works, chat functions without content

### 🚧 Thursday: Confusion Tracker
**What**: Measure how long users stay confused
**Why**: 3-8 minutes is golden for breakthroughs
**How**:
```python
# Track keywords indicating confusion
CONFUSION_SIGNALS = ["don't understand", "confused", "lost", "why"]
if any(signal in message.lower() for signal in CONFUSION_SIGNALS):
    await track_confusion_start(user_id)
```
**Ship by**: End of day
**Success metric**: Metrics logged to database

### 🚧 Friday: First Customer Demo
**What**: Live demo for potential customer
**Why**: Week 3 Delta requirement
**Prep**:
- Fix any bugs from week's features
- Practice 5-minute demo
- Prepare pricing proposal
**Ship by**: 3 PM
**Success metric**: Get commitment or clear feedback

## Next Week Preview

### Monday Aug 12: A/B Testing Framework
```python
@ab_test("thinking_timer_duration")
async def get_timer_duration(user_id: str):
    return random.choice([60, 120, 180])  # Test 1, 2, 3 minutes
```

### Tuesday Aug 13: Struggle Patterns
Track unique struggle fingerprints per user

### Wednesday Aug 14: Public Launch Post
Ship to ProductHunt/HackerNews

## Code First, Philosophy Later

Each feature:
1. **Code it** (working prototype)
2. **Ship it** (behind feature flag)
3. **Measure it** (add metrics)
4. **Iterate it** (based on data)

No feature takes more than 1 day.
No discussion without working code.
No perfection before shipping.

## This Week's Mantras

- "Does it work?" > "Is it perfect?"
- "Ship daily" > "Plan weekly"
- "User feedback" > "Internal debate"
- "Running code" > "Documentation"
- "Try it" > "Discuss it"

## Definition of Shipped

A feature is SHIPPED when:
- [ ] Code is in main branch
- [ ] Users can access it (even behind flag)
- [ ] Metrics are being collected
- [ ] You've moved to the next feature

Not when:
- It's fully tested
- Everyone agrees
- It's beautiful
- It's complete

## Anti-Patterns to Avoid

❌ "Let's discuss the architecture more"
✅ Build prototype, then discuss

❌ "We need more research"
✅ Ship experiment, gather data

❌ "What if users don't like it?"
✅ Ship it, find out

❌ "The code isn't clean enough"
✅ Ship messy, refactor later

## Daily Standup Format

```
Yesterday: [What shipped]
Today: [What ships]
Blockers: [What prevents shipping]
```

Not:
- What I thought about
- What I planned
- What I researched

## Metrics Dashboard

```python
# Track everything
@track_metric
async def every_user_action():
    # Time to ship > Time to perfect
    pass
```

## The Only Question That Matters

**"What did you ship today?"**

If the answer is "nothing," tomorrow ship two things.

---

*Updated daily at 9 AM. If it's not on this list, it doesn't get built this week.*