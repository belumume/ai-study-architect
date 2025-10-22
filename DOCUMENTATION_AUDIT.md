# Documentation Audit: Stale/Outdated Content

**Date**: October 22, 2025
**Context**: After strategic pivot to mastery-based learning
**Status**: CRITICAL - Multiple files claim features that don't exist

---

## Executive Summary

After the strategic pivot, **multiple documentation files still claim all 7 agents are "LIVE"** when only the Lead Tutor Agent exists. This creates confusion and misrepresents the current state.

**Files Actually Exist**:
- `backend/app/agents/base.py`
- `backend/app/agents/lead_tutor.py`

**Files Claimed to Exist**: 6 additional agent files that don't exist

---

## Priority 1: CRITICAL MISREPRESENTATIONS

### 1. README.md - Lines 64-79
**Status**: ❌ **MISLEADING**

**Claims**:
```markdown
### Multi-Agent System
The project is designed around seven specialized AI agents working together (currently in phased implementation):

1. **Lead Tutor Agent**: [LIVE]
2. **Content Understanding Agent**: [PLANNED]
3. **Knowledge Synthesis Agent**: [PLANNED]
4. **Practice Generation Agent**: [PLANNED]
5. **Progress Tracking Agent**: [PLANNED]
6. **Assessment Agent**: [PLANNED]
7. **Collaboration Agent**: [PLANNED]
```

**Reality**: ✅ This was actually updated in our earlier PR! It correctly shows only Lead Tutor as [LIVE].

**Action**: ✅ No change needed

---

### 2. docs/ARCHITECTURE.md - Lines 15-22
**Status**: ❌ **FALSE - CRITICAL**

**Claims**:
```markdown
### The Seven Specialized Agents
1. **Lead Tutor Agent** - Orchestrates the learning experience ✅ LIVE
2. **Content Understanding Agent** - Processes any educational material ✅ LIVE
3. **Knowledge Synthesis Agent** - Creates personalized connections ✅ LIVE
4. **Practice Generation Agent** - Builds exercises ✅ LIVE
5. **Progress Tracking Agent** - Monitors true understanding ✅ LIVE
6. **Assessment Agent** - Evaluates comprehension ✅ LIVE
7. **Collaboration Agent** - Enables collective intelligence ✅ LIVE
```

**Reality**: Only Lead Tutor exists. The other 6 files don't exist in `/backend/app/agents/`.

**Action**: ⚠️ **MUST UPDATE** to match new mastery-based direction

---

### 3. docs/ARCHITECTURE.md - Lines 61-67
**Status**: ❌ **FALSE - CRITICAL**

**Claims**:
```markdown
├── agents/                   # Multi-agent system
│   ├── base.py              # Base agent class
│   ├── lead_tutor.py        # Orchestration agent ✅ Live
│   ├── content_understanding.py  # ✅ Live
│   ├── knowledge_synthesis.py    # ✅ Live
│   ├── practice_generation.py    # ✅ Live
│   ├── progress_tracking.py      # ✅ Live
│   ├── assessment.py             # ✅ Live
│   └── collaboration.py          # ✅ Live
```

**Reality**: Only `base.py` and `lead_tutor.py` exist.

**Action**: ⚠️ **MUST UPDATE** - remove false claims or mark as planned

---

## Priority 2: OUTDATED VISION DOCUMENTS

### 4. docs/UNIQUE_VALUE_PROPOSITION.md
**Status**: ⚠️ **OUTDATED**

**Issue**: Still describes 7-agent system as primary differentiator

**Action**: Update to reflect mastery-based differentiation (knowledge graphs, spaced repetition, retention tracking)

---

### 5. docs/COLLECTIVE_INTELLIGENCE_VISION.md
**Status**: ⚠️ **ASPIRATIONAL**

**Issue**: Describes Phase 3 features as if they're near-term

**Action**: Add prominent note: "Long-term vision (Year 2+). Current focus: mastery-based learning (see NEW_DIRECTION_2025.md)"

---

### 6. docs/AGENT_EVOLUTION.md
**Status**: ⚠️ **OUTDATED** (if exists)

**Action**: Either delete or update to reflect new architecture

---

## Priority 3: MISLEADING FUTURE VISION

### 7. README.md - Lines 162-171
**Status**: ⚠️ **MISALIGNED**

**Claims**:
```markdown
## Future Vision
- **Practice Problem Generation**: AI creates exercises based on your materials
- **Collaborative Learning**: Match students with complementary strengths
- **Spaced Repetition**: Optimize review timing for maximum retention
- **Multi-Modal Support**: Process images, audio, and video content
```

**Issue**: These ARE the new pivot direction, not "future vision"! They should be "Current Development Plan"

**Action**: Reframe as "Active Development Roadmap" with timeline from DAILY_DEV_PLAN.md

---

### 8. README.md - Lines 223-224
**Status**: ⚠️ **OUTDATED REFERENCE**

**Claims**:
```markdown
**August 2025 Update**: Inspired by Andrej Karpathy's challenge to "uplift team human,"
we're expanding our vision from individual learning to collective human advancement.
```

**Issue**: This was before the October pivot to mastery-based learning

**Action**: Add October 2025 update about mastery-based pivot

---

## Priority 4: INCONSISTENT DESCRIPTIONS

### 9. README.md - Lines 13-23
**Status**: ⚠️ **PARTIALLY OUTDATED**

**Current Description**:
```markdown
AI Study Architect is a revolutionary **AI-powered learning system** that transforms
how students learn by **making them think deeper, not think less** through Socratic questioning.
```

**Issue**: Emphasizes Socratic questioning but doesn't mention mastery-based system, knowledge graphs, or retention tracking

**Action**: Update to include mastery-based approach as primary differentiator

---

### 10. README.md - Lines 47-60
**Status**: ⚠️ **VAGUE**

**Claims**:
```markdown
**Our Approach**:
- Seven specialized agents orchestrating together
- Understanding-focused collective intelligence
```

**Issue**: Still emphasizes 7 agents, not mastery-based features

**Action**: Update to:
- Knowledge graph extraction
- Mastery-based progression (90%+ gates)
- Spaced repetition scheduling
- Retention tracking and proof of learning

---

## Files That Are CORRECT

### ✅ CLAUDE.md
**Status**: ✅ **UP TO DATE**

Updated in latest PR to reflect mastery-based pivot.

### ✅ docs/NEW_DIRECTION_2025.md
**Status**: ✅ **CURRENT**

Comprehensive strategic pivot document (this is the source of truth).

### ✅ docs/IMPLEMENTATION_PLAN_WEEK1.md
**Status**: ✅ **CURRENT**

Detailed implementation plan with improved schema.

### ✅ DAILY_DEV_PLAN.md
**Status**: ✅ **CURRENT**

14-day development roadmap.

### ✅ docs/IMPLEMENTATION_STATUS.md
**Status**: ✅ **UPDATED**

Already updated in earlier PR to reflect reality.

---

## Recommended Action Plan

### Immediate (Before Day 1)

**Must Fix** (blocking start):
1. ❌ **docs/ARCHITECTURE.md** - Update to reflect mastery-based system (or archive)
2. ❌ **README.md** - Update "Our Approach" section to emphasize mastery-based features
3. ❌ **README.md** - Reframe "Future Vision" as "Development Roadmap"

**Time**: ~30 minutes

### Short-term (This Week)

**Should Fix** (improves clarity):
4. ⚠️ **docs/UNIQUE_VALUE_PROPOSITION.md** - Update differentiation strategy
5. ⚠️ **docs/COLLECTIVE_INTELLIGENCE_VISION.md** - Add "Long-term vision" disclaimer
6. ⚠️ **README.md** - Add October 2025 pivot update

**Time**: ~1 hour

### Long-term (As Needed)

**Nice to Have** (polish):
7. Review all files in `docs/` for consistency
8. Create DEPRECATED.md for old vision docs
9. Archive aspirational content to `docs/archive/future_vision/`

**Time**: ~2 hours

---

## The Core Issue

**Problem**: Documentation written aspirationally (describing the desired system) conflicts with NEW_DIRECTION_2025.md (describing what we're actually building).

**Root Cause**: Original docs were vision-forward ("here's what we want to build"), but after the pivot, we need reality-forward docs ("here's what exists + clear roadmap").

**Solution**:
1. Mark aspirational content as "Long-term Vision (Year 2+)"
2. Emphasize current focus: Mastery-based learning (Week 1-12)
3. Link everything to NEW_DIRECTION_2025.md as source of truth

---

## Severity Breakdown

| Priority | Files | Impact | Time to Fix |
|----------|-------|--------|-------------|
| 🔴 P1 Critical | 1 file | Misleading about what exists | 15 min |
| 🟡 P2 Outdated | 3 files | Confusing vision/reality | 1 hour |
| 🟢 P3 Polish | 5+ files | Minor inconsistencies | 2 hours |

---

## Recommendation

**Before starting Day 1**:

Fix the P1 critical issue (docs/ARCHITECTURE.md) so there's no confusion about what actually exists vs. what's planned.

**After Day 1** (when you have momentum):

Spend 1 hour fixing P2 issues (README updates).

**Rationale**: Don't let documentation cleanup block actual development. The mastery-based system is documented in NEW_DIRECTION_2025.md and DAILY_DEV_PLAN.md - that's sufficient to build. Polish the rest gradually.

---

**Bottom Line**: docs/ARCHITECTURE.md is the most misleading file. Fix it (15 min), then start coding.
