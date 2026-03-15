---
date: 2026-03-14
topic: monetization-model-routing-tiers
---

# Study Architect: Monetization, Model Routing & Feature Gating Strategy

## What We're Deciding

Three interconnected decisions that need to be made together:
1. **Model routing** -- which AI model handles which task (internal, never user-facing)
2. **Subscription tiers** -- what's free, what's paid, at what price
3. **Feature gating** -- what gets limited, what never gets limited

These decisions shape the product's economics, user experience, and alignment with our principles.

## Principles Check (CLAUDE.local.md)

Every decision below was stress-tested against:

| Principle | Implication |
|-----------|-------------|
| Don't gatekeep knowledge | Learning quality must be equal across tiers. Gate usage volume, never AI quality. |
| Build tools that teach | The product optimizes for learning, not model shopping. No model picker. |
| Build for every unique being | Free tier must be genuinely useful, not a crippled demo. |
| Don't extract value or attention | No dark patterns (countdown timers, "upgrade to continue" mid-session). |
| Don't optimize for vanity metrics | Conversion rate matters less than learning outcomes. |
| Don't build slot machines | No gamification of upgrades. No artificial scarcity. |
| Build for the commons | Core learning features stay free. Premium = convenience + volume. |

## Decision 1: Model Routing (Internal)

**Decision: Route by task complexity, not by user tier.**

Every user -- free or paid -- gets the same model quality for the same task. The product decides which model to use, not the user.

### Routing Table

| Task | Model | Cost/Use | Rationale |
|------|-------|----------|-----------|
| Concept extraction | Haiku 4.5 | $0.006/doc (cached) | Structured output, schema-constrained. Spike test confirmed comparable quality to Sonnet (13 vs 15 concepts, same confidence). 3.6x cheaper. |
| Socratic tutoring | Sonnet 4.6 | $1.27/user/mo (cached) | Core product experience. Quality directly affects learning outcomes. Evaluate Haiku downgrade after 100 sessions if satisfaction >= 95%. |
| Practice grading | Haiku 4.5 (batch) | $0.003/grade | Rubric-based evaluation, well-constrained. Batch API for 50% discount (grading is async). |
| Content analysis | Haiku 4.5 | $0.006/doc | Same as extraction -- structured output, schema-constrained. |
| Study plan generation | Sonnet 4.6 | ~$0.02/plan | Requires reasoning about concept dependencies. Less frequent (1x per subject). |
| SM-2 scheduling | No AI | $0 | Pure algorithm, no LLM needed. |

### Fallback Chain

```
Primary: Claude (model per task above)
  -> If Claude unavailable: OpenAI equivalent (GPT-5 Mini for Haiku tasks, GPT-5 for Sonnet tasks)
  -> If both unavailable: Cached response + "AI temporarily unavailable" message
```

### Cost Optimization Stack (implement in order)

1. **Prompt caching** -- cache system prompts across requests (-40% on tutoring, -60% on extraction)
2. **Batch API** -- async grading/extraction (-50% discount)
3. **Haiku downgrade testing** -- validate Haiku for tutoring after 100 sessions
4. **Response caching** -- Redis cache for identical extraction requests (same content = same concepts)

### What This Means: No Model Selection UI. Ever.

- Users don't see model names. They see "Extract Concepts" and "Start Tutoring."
- The product makes the smart choice. The user learns.
- This is how Duolingo, Khan Academy, Brilliant, MathAcademy, and every serious education tool works.
- Only general-purpose AI chatbots (ChatGPT, Claude.ai, Poe) expose model selection -- because their product IS the model access. Ours isn't.

## Decision 2: Subscription Tiers

**Decision: Usage-gated freemium with one paid tier.**

### Competitive Context

| App | Free | Paid | Price |
|-----|------|------|-------|
| Duolingo | Full curriculum, 5 hearts/day | Unlimited hearts, no ads | $12.99/mo |
| StudyFetch | 10 chats, 1 set, 2 uploads | Unlimited everything | $7.99-11.99/mo |
| Quizlet | Basic flashcards, ads | AI features, no ads | $7.99/mo |
| Brilliant | 2-3 lessons/course | Unlimited | $27.99/mo |
| MathAcademy | None (30-day refund) | Full access | $49/mo |
| Coursera | Audit (no grades) | Full access + certs | $59/mo |

### Study Architect Tiers

| | Free | Pro |
|---|---|---|
| **Price** | $0 | $9.99/mo or $79.99/yr |
| **Subjects** | 3 | Unlimited |
| **Tutoring** | 10 messages/day | Unlimited |
| **Concept extraction** | 2/month | Unlimited |
| **Practice questions** | 5/day | Unlimited |
| **Spaced repetition** | Full (never gated) | Full |
| **Analytics dashboard** | Basic (streak, time) | Full (mastery curves, predictions) |
| **Content uploads** | 3 total | Unlimited |
| **Export/download** | No | Yes |
| **AI model quality** | Same as Pro | Same as Free |

### Why $9.99/mo (not $19.99)

The cost research showed 91% margin at $19.99 with Sonnet. At $9.99 with Haiku routing:
- API cost: ~$0.50/user/mo (Haiku for extraction/grading, Sonnet for tutoring with caching)
- Ops cost: ~$0.50/user/mo
- **Margin: ~90% at $9.99**

$9.99 sits in the "student-friendly" sweet spot ($7.99-$12.99 range where StudyFetch, Quizlet, and Duolingo compete). $19.99 feels like ChatGPT Plus -- a general AI tool, not a focused learning product. Our target is students, not professionals.

Annual pricing ($79.99 = $6.67/mo effective) encourages commitment and reduces churn.

### What's NEVER gated (principles compliance)

- **Learning quality** -- same AI model quality on both tiers
- **Spaced repetition** -- core learning mechanism, gating it gatekeeps knowledge
- **Concept viewing** -- if concepts are extracted, you can always see them
- **Mastery tracking** -- basic progress is always visible

### What IS gated (fair usage limits)

- **Volume** -- messages/day, extractions/month, uploads, subjects
- **Convenience** -- export, advanced analytics, unlimited content
- **These are compute costs, not knowledge** -- limiting API calls is economically necessary, not gatekeeping

## Decision 3: Feature Gating Implementation

### When to Implement

**Not now.** Current priorities:
- Phase 3: Chat + content MUI removal
- Phase 4: Practice generation (the core loop)
- Phase 5: SM-2 scheduling + analytics

Monetization infrastructure (Stripe, subscription management, usage tracking) is **Phase 6** work. Implementing it before the core learning loop exists is premature optimization of revenue for a product that doesn't yet prove learning outcomes.

### What to Build When Ready

1. **Usage counter middleware** -- track messages/day, extractions/month per user
2. **Stripe integration** -- subscription management, webhook handling
3. **Tier enforcement** -- rate limiting by tier (extend existing `rate_limiter.py` pattern)
4. **Upgrade prompts** -- tasteful, non-dark-pattern ("You've used your 10 messages for today. Upgrade for unlimited, or come back tomorrow.")

### What NOT to Build

- Model selection dropdown
- Token usage display
- "Credits" system (too gamified)
- Multiple paid tiers (one tier is simpler, less decision fatigue)
- Enterprise/B2B tier (premature -- validate consumer PMF first)

## Approaches Considered

### Approach A: Usage-Gated Freemium (CHOSEN)

Gate on volume (messages/day, extractions/month). Same quality everywhere. One paid tier.

**Pros**: Proven in education SaaS. Fair. Simple. 90% margins.
**Cons**: Free users cost money (~$0.50/mo each). Need 5% conversion to break even.
**Best when**: Building consumer product with organic growth.

### Approach B: Time-Based Trial then Paywall

7-day full access, then paywall. No free tier.

**Pros**: Simpler. No free-rider problem. Higher conversion (forced).
**Cons**: Kills organic growth. Students who need it during exams 2 months later won't return. MathAcademy is the only education app that succeeds without free tier -- and they have 7 years of product-market fit.
**Best when**: Product has proven PMF and strong word-of-mouth.

### Approach C: Open Core (Free tutoring, paid extraction/analytics)

Full tutoring free. Gate on advanced features only.

**Pros**: Maximally generous. Great for adoption.
**Cons**: Free tier is too complete -- no incentive to convert. Tutoring is the most expensive feature (Sonnet). Extraction (Haiku) is cheaper but gated. Economics are backwards.
**Best when**: VC-funded growth stage where revenue is secondary to user count.

**Why A wins**: It's the only approach where the economics, principles, and competitive landscape all align. The free tier is genuinely useful (10 messages/day is enough for light study). The paid tier is clearly better for serious students. The price is student-friendly. And same-quality-everywhere honors "don't gatekeep knowledge."

## Why This Is Settled (Not a Trade-off Menu)

Most strategy docs present options and say "it depends." This one doesn't, because the research converged to a single dominant answer across every dimension:

| Dimension | Answer | Why it's not a trade-off |
|-----------|--------|--------------------------|
| **Cost** | Haiku for structured tasks, Sonnet for tutoring | Haiku is 3.6x cheaper with comparable extraction quality (13 vs 15 concepts, same 0.92 confidence). No quality sacrifice. |
| **Quality** | Same model quality for free and paid users | Compute is cheap enough (90% margin at $9.99). Gating learning quality for a learning product is like a hospital giving worse medicine to uninsured patients -- it undermines the core promise. |
| **UX** | No model picker, ever | Every successful education product hides this. Products that expose it (Poe, ChatGPT) sell AI access. We sell learning outcomes. Different product, different UX. |
| **Pricing** | $9.99/mo | $19.99 puts us in ChatGPT territory (competing on AI access). Below $7.99 leaves margin on the table. $9.99 is the intersection of student-affordable, 90% margin, and market-competitive. |
| **Gating** | Usage volume, never AI quality | Only approach where economics (90% margin), principles (don't gatekeep knowledge), and competitive reality (every competitor does freemium) all align. Not a compromise -- it's dominant. |
| **Model selection** | Internal routing by task, not user choice | Users are students, not AI engineers. The product makes the smart choice. The user learns. |

### What IS genuinely "test and learn"

The strategy is settled. Only the exact parameter values need real user data:

- **Free tier limits**: 10 messages/day or 15? 2 extractions/month or 5?
- **Price point**: $9.99 or $12.99? Annual ratio?
- **Haiku tutoring threshold**: When satisfaction data shows >= 95%, downgrade Sonnet to Haiku for tutoring (saves 67%)
- **Conversion funnel**: Actual free-to-paid conversion rate (target 5-8%, breakeven at 3%)

These are tuning knobs, not strategy questions. The product direction doesn't change based on whether the answer is 10 or 15 messages/day.

## Open Questions (Deferred to Implementation Phase)

1. **Exact free tier limits** -- 10 messages/day or 15? Test with early users.
2. **Annual vs monthly ratio** -- $9.99/$79.99 or $9.99/$59.99? Test price sensitivity.
3. **Student discount** -- .edu email verification for 50% off? Or is $9.99 already student-priced?
4. **Referral program** -- "Invite a friend, both get 1 month free"? Deferred until CAC data exists.

## Related Documents

- `docs/analysis/AI_EDUCATION_COST_MODELING_2026.md` -- full cost modeling with per-user economics
- `docs/analysis/PRICING_DECISION_CARD.md` -- one-page quick reference for model selection and pricing
- `docs/analysis/COST_COMPARISON_TABLE.csv` -- spreadsheet format for all model costs

## Next Steps

This is a **strategy document**, not a plan. No code changes needed now.

1. **Now**: This doc is the source of truth for monetization decisions
2. **Phase 4-5**: Build the core learning loop (practice + spaced repetition). Monetization is meaningless until the product proves learning outcomes.
3. **Phase 6**: Implement Stripe + tier enforcement + usage tracking. Reference this doc.
4. **Post-launch**: Validate assumptions with real user data. Adjust limits and pricing based on actual conversion rates and usage patterns.
