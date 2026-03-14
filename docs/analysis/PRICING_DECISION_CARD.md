# Study Architect: Pricing & Cost Decision Card (March 2026)

Quick reference for API model selection, pricing strategy, and profitability targets.

---

## Current Prices (Verified March 2026)

### Claude API (Per Million Tokens)

| Model | Input | Output | Best For | Monthly/User (30 min) |
|-------|-------|--------|----------|-----|
| **Haiku 4.5** | $1.00 | $5.00 | Cost-optimized | $0.51 |
| **Sonnet 4.6** | $3.00 | $15.00 | Production baseline | $1.51 |
| **Opus 4.6** | $5.00 | $25.00 | Complex reasoning | $2.51 |

### Prompt Caching Savings
- Cache hits cost **0.1x base input** (90% savings)
- Breaks even after: 1 read for 5-min cache, 2 reads for 1-hour cache
- **Realistic impact**: -40% on tutoring sessions, -60% on extraction with system prompt reuse

### Batch API (Async Processing)
- **50% discount** on both input and output tokens
- Use for: grading, concept extraction, report generation, follow-up emails
- Don't use for: real-time tutoring, chat, live interaction

---

## Concept Extraction Cost (Your Use Case)

### Per Document (1.4K input + 3K output tokens)

| Model | Standard | + Cache (60% off) | + Batch (50% off) |
|-------|----------|------------------|-------------------|
| **Haiku** | $0.015 | $0.006 | $0.007 |
| **Sonnet** | $0.045 | $0.018 | $0.022 |
| **Opus** | $0.080 | $0.032 | $0.040 |

**Monthly for 5 docs**:
- Haiku: $0.075 baseline → $0.030 with caching → $0.035 with batch
- Sonnet: $0.225 baseline → $0.090 with caching → $0.110 with batch
- Opus: $0.400 baseline → $0.160 with caching → $0.200 with batch

---

## Revenue & Margin Model

### Consumer Pricing: $19.99/Month

| Item | Cost | Notes |
|------|------|-------|
| Revenue | **$19.99** | |
| API cost (Sonnet, caching) | $1.27 | 30 min tutoring + extraction |
| Ops cost (shared) | $0.50 | Infrastructure, support, payment processing |
| **Profit** | **$18.22** | |
| **Margin** | **91%** | ✓ Excellent |

### Breakeven & Conversion

| Metric | Value | Notes |
|--------|-------|-------|
| **Free user monthly cost** | $1.77 | API + ops, Sonnet |
| **Required conversion** | ~3% | To break even (realistic: 5–8%) |
| **CAC (organic)** | $5 | Typical for self-serve SaaS |
| **LTV (12 months)** | $240–$300 | 5–8% of free base converts |
| **LTV/CAC** | **48–60x** | ✓ Excellent |

---

## Model Selection Guide

### Decision 1: Real-Time Tutoring

```
START: Sonnet 4.6
  ↓ (After 100 user sessions)
  IF user satisfaction >= 95%:
    SWITCH TO: Haiku 4.5
    SAVES: 67% ($1.51 → $0.51/month)
  ELSE:
    KEEP: Sonnet 4.6
    OR TRY: Opus 4.6 (if reasoning issues)
```

**Why Sonnet first?**
- Best quality-to-cost ratio ($3/$15)
- Sufficient for most tutoring scenarios
- Easy downgrade to Haiku if performance acceptable

### Decision 2: Concept Extraction & Batch Processing

```
START: Sonnet 4.6 + Batch + Cache
  Cost: $0.022 per document
  ↓ (After 100 documents)
  IF Haiku extraction accuracy >= 95%:
    SWITCH TO: Haiku 4.5 + Batch + Cache
    SAVES: 67% ($0.022 → $0.007/doc)
    AT 1000 USERS: $1,400/month savings
  ELSE:
    KEEP: Sonnet 4.6
    OR TRY: Opus 4.6 (if complex docs)
```

**Why test Haiku first?**
- Haiku is reliable for structured extraction (JSON/schema output)
- Prompt caching makes it even cheaper
- Structured Outputs (GA) reduce hallucination risk

---

## Optimization Checklist (Priority Order)

- [ ] **Week 1**: Implement prompt caching for system prompts (40% savings, ~$0.30/user/month)
- [ ] **Week 2**: Switch extraction to Batch API (50% cost reduction)
- [ ] **Week 3**: Run 100-document Haiku accuracy test (path to 67% extraction savings)
- [ ] **Week 4**: Launch free tier with paywall at day 3 (reduce free user cost, improve conversion)
- [ ] **Month 2**: A/B test Haiku vs Sonnet for tutoring (if Haiku ≥95% satisfaction, save $1/user/month)
- [ ] **Month 3**: Implement spaced repetition scheduling (use Batch API for reminders, save 70% on that workload)

---

## Risk Factors

| Risk | Mitigation | Timeline |
|------|-----------|----------|
| **Haiku accuracy misses 95%** | Keep Sonnet for tutoring; use Haiku for extraction only | Week 3 decision |
| **Conversion rate <3%** | Revise free tier (reduce daily limits) or paywall timing (try day 2 instead of day 3) | Month 2 adjustment |
| **API pricing increase >20%** | Keep OpenAI API key active as fallback; monitor Claude pricing monthly | Ongoing |
| **Prompt caching not effective** | Cache hit rate may be lower than expected; monitor actual usage | Week 1–2 data |

---

## Margin Sensitivity (At $19.99/Month)

| API Model | With Caching | Free User Cost | Margin % |
|-----------|-------------|-----------------|----------|
| **Haiku** | $0.43 | $0.93 | 95% |
| **Sonnet** | $1.27 | $1.77 | 91% |
| **Opus** | $2.11 | $2.61 | 87% |

**Key insight**: Even at Opus, margins are 87%+. Pricing power is high. Problem is user acquisition, not profitability.

---

## Pricing Tiers (Recommendation)

| Tier | Price | API Cost (Target) | Features |
|------|-------|-----------|----------|
| **Free** | $0 | $0.30 | 5 tutoring turns/day, no extraction |
| **Pro** | $19.99/mo | $1.50 | Unlimited tutoring, extraction, spaced rep |
| **Premium** | $99.99/year | $1.50 | + Export highlights, study plans |
| **K-12 District** | $3–$10/student/year | $0.50 (bulk savings) | Admin panel, class management, reports |

**Conversion targets**:
- Visitor → free: 10%
- Free → paid: 5–8% (target month 6)
- Overall: 0.5–0.8% (industry baseline: 0.1–1.5%)

---

## OpenAI as Fallback

If Claude API becomes unavailable or pricing diverges >20%:

| Model | Input/Output | Monthly (30 min) |
|-------|---|---|
| **GPT-5 Mini** | $0.25/$1.00 | **$0.40** (20% cheaper) |
| **GPT-4o** | $2.50/$10.00 | **$1.98** (30% more expensive) |
| **GPT-5** | $1.25/$10.00 | **$1.32** (12% cheaper) |

**Fallback strategy**: Keep OpenAI key active. Monitor Claude pricing quarterly. If Sonnet >$3.50 input or >$17 output, evaluate switch.

---

## Key Assumptions (Validate Monthly)

1. **Token estimates**: 30 min tutoring = 4,400 tokens/month/user (varies by subject/complexity)
2. **Conversion rate**: 5% freemium → paid (actual will vary by marketing channel)
3. **Caching effectiveness**: 75% of requests hit cache (depends on session length and user pattern)
4. **Batch API adoption**: 60% of grading/extraction workload can be async (limits: real-time feedback needs standard API)
5. **Ops cost**: $0.50/user/month (infrastructure, payment processing, support shared across all users)

---

## Data to Collect (For Future Tuning)

- **Per-session token count**: Average turns, average tokens per turn (refine from 4,400/month baseline)
- **Cache hit rate**: % of requests that hit cached context (current assumption: 75%)
- **Batch API adoption**: What % of grading/extraction can be delayed 2–24 hours?
- **Model accuracy**: Haiku vs Sonnet on tutoring quality scores and user satisfaction
- **Conversion funnel**: Visitor → free → paid at each step (track by cohort)
- **User churn**: Free and paid monthly retention rates

---

**Last Updated**: March 14, 2026
**Data Source**: https://platform.claude.com/docs/en/about-claude/pricing (verified)
**Next Review**: April 14, 2026 (quarterly pricing check)
