# Documentation Hierarchy & Authority Guide

**Last Updated**: August 4, 2025  
**Purpose**: Establish clear authority levels for all AI Study Architect documentation to ensure clarity and consistent information.

---

## Document Authority Levels

### Level 1: Vision Documents (Highest Authority)
These define the core philosophy and long-term direction. Changes require careful consideration and impact all lower-level documents.

1. **COLLECTIVE_INTELLIGENCE_VISION.md** (Latest Evolution - August 2025)
   - **Authority**: HIGHEST - Defines current north star and mission
   - **Supersedes**: All individual-only learning approaches
   - **Key Decision**: Evolution from individual to collective intelligence
   - **Status**: Active - This is our current true north

2. **GREAT_WORK_VISION.md**
   - **Authority**: HIGHEST - Core philosophy and principles
   - **Complements**: Collective Intelligence Vision
   - **Key Decision**: Building for lasting impact
   - **Status**: Active - Foundational principles remain valid

### Level 2: Architecture & Planning Documents
These translate vision into actionable technical plans. Updated with major architectural changes.

1. **ARCHITECTURE.md**
   - **Authority**: Technical architecture truth
   - **Updates**: With each agent addition/modification
   - **Status**: Must reflect latest vision evolution

2. **docs/planning/perfect-cs50-ai-project-2025.md**
   - **Authority**: Original project conception
   - **Status**: Historical reference only
   - **Key Decision**: Multi-agent architecture foundation

3. **IMPLEMENTATION_STATUS.md**
   - **Authority**: Current implementation reality
   - **Updates**: Weekly or after major milestones
   - **Purpose**: Bridge between vision and current state

### Level 3: Development Guides
These provide technical direction and patterns. Updated with each major release or session.

1. **CLAUDE.md**
   - **Authority**: Development patterns, learnings, and session history
   - **Updates**: After each development session
   - **Status**: Most current operational guide

2. **docs/guides/ai-study-architect-implementation-guide.md**
   - **Authority**: Technical implementation details
   - **Updates**: With architecture changes
   - **Purpose**: Onboarding and technical reference

### Level 4: Operational Documents
These guide daily operations and current project state. Updated frequently.

1. **README.md**
   - **Authority**: Current project state and quick start
   - **Updates**: With each feature addition
   - **Purpose**: First impression and setup guide

2. **SETUP.md**
   - **Authority**: Installation and environment setup
   - **Updates**: With dependency changes
   - **Purpose**: Getting started guide

---

## Conflict Resolution Protocol

When documents contain conflicting information, resolve using this strict hierarchy:

1. **Level 1 (Vision) overrides all others** - These are immutable truths
2. **Higher level overrides lower level** - Architecture overrides implementation
3. **Newer timestamp overrides older** - Within same level, recency wins
4. **Specific overrides general** - Detailed guidance beats generic advice
5. **Implementation status is reality** - What exists today vs. what's planned

### Emergency Conflicts
If critical conflicts exist that block development:
1. Document the conflict in this file immediately
2. Make explicit decision and document rationale
3. Update all affected documents within 24 hours
4. Never leave conflicts unresolved

---

## Canonical Definitions (Authoritative Truth)

### System Architecture: Dual-Agent Model

**AI Study Architect System Agents (7 Total)**:
1. **Lead Tutor Agent** - Orchestrates learning experience (✅ Basic implementation)
2. **Content Understanding Agent** - Processes multimodal inputs (❌ Planned)
3. **Knowledge Synthesis Agent** - Creates personalized materials (❌ Planned)
4. **Practice Generation Agent** - Develops adaptive problem sets (❌ Planned)
5. **Progress Tracking Agent** - Monitors and adjusts challenge level (❌ Planned)
6. **Assessment Agent** - Evaluates true comprehension (❌ Planned)
7. **Collaboration Agent** - Facilitates collective intelligence (❌ Planned)

**Claude Code Sub-Agents (5 Total)**:
Located in `.claude/agents/` - These are development assistants, NOT system agents:
1. **content-processor** - Educational content processing assistance
2. **test-writer** - TDD and coverage enforcement assistance
3. **security-auditor** - Security review assistance
4. **ai-tutor** - LangChain/Ollama implementation assistance
5. **db-optimizer** - Query optimization assistance

### Core Problem Statement
"Students use AI for learning, but current tools optimize for giving answers rather than building understanding. Students get answers but don't learn to think."

### Current Mission Statement (August 2025)
"Make learning so effective, so personal, so collaborative, and so profound that humanity advances together, leaving no one behind."

### Unique Value Proposition
"AI Study Architect is the first multi-agent learning system that enables collective human advancement through privacy-preserving collaborative intelligence, where individual learning agents work together to help students both master concepts deeply and contribute to shared human knowledge."

### Current Implementation Status (August 2025)
- **Overall Progress**: ~15% of full vision (Early Development/MVP)
- **MVP Core Features**: ✅ Complete (Auth, File Upload, AI Chat, Content Processing)
- **System Agents**: 1 of 7 implemented (Lead Tutor basic version)
- **Collective Intelligence**: ❌ Not yet implemented (next major phase)

---

## Document Metadata Standard

All documents MUST include this header:
```markdown
---
Document Level: [1-4]
Created: [YYYY-MM-DD]
Last Updated: [YYYY-MM-DD]
Supersedes: [Document names if any]
Status: [Active/Historical/Deprecated]
Authority: [What this document is the truth for]
---
```

---

## Update Protocol

### Vision Changes (Level 1)
1. **Requires**: Written rationale and impact analysis
2. **Process**: Document in separate vision evolution document first
3. **Timeline**: Minimum 48-hour review period
4. **Cascading**: Must update all dependent documents

### Architecture Changes (Level 2)
1. **Requires**: Technical feasibility assessment
2. **Process**: Update ARCHITECTURE.md first, then guides
3. **Timeline**: Update within 24 hours of decision
4. **Testing**: Must not break existing implementations

### Implementation Updates (Level 3-4)
1. **Frequency**: After each development session
2. **Requirements**: Accurate status reporting
3. **Timeline**: Real-time updates during development
4. **Validation**: Must match actual codebase state

---

## Critical Warnings

### ⚠️ Never Ignore These Conflicts
1. **Agent count mismatches** - System agents ≠ Claude Code sub-agents
2. **Implementation status discrepancies** - Reality must match documentation
3. **Vision evolution gaps** - Collective intelligence is now core, not optional
4. **Security requirement changes** - Never downgrade security based on outdated docs

### 🚨 Emergency Documentation Debt
If any of these exist, STOP development and fix immediately:
- Contradictory implementation percentages
- Conflicting agent architectures
- Outdated vision statements
- Missing metadata headers

---

## Quick Reference for Contributors

### New Contributors
1. **Start here**: COLLECTIVE_INTELLIGENCE_VISION.md (understand WHY)
2. **Then read**: IMPLEMENTATION_STATUS.md (understand WHAT EXISTS)
3. **Then check**: CLAUDE.md (understand HOW to develop)
4. **When uncertain**: This document is the tiebreaker

### Existing Contributors
1. **Before each session**: Check IMPLEMENTATION_STATUS.md
2. **After each session**: Update CLAUDE.md with new patterns
3. **Weekly**: Verify no documentation conflicts exist
4. **Monthly**: Review and update this hierarchy

### Maintainers
1. **Vision changes**: Require architecture review
2. **Architecture changes**: Require cascade update plan
3. **Conflicts found**: Resolve within 24 hours
4. **Documentation debt**: Never let it accumulate

---

## Authority Enforcement

This document serves as the **final arbiter** for all documentation conflicts. When in doubt:

1. **Check this document first** - It's the single source of truth
2. **Follow the hierarchy** - Level 1 always wins
3. **Update immediately** - Don't leave conflicts unresolved
4. **Document decisions** - Every resolution creates precedent

---

**Document Version**: 2.0  
**Created**: August 2025  
**Last Updated**: August 4, 2025  
**Authority**: Final arbiter for all documentation conflicts  
**Status**: Active - Enforce strictly