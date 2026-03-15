# Experiment 003: Jyotish Fundamentals for AI Agents — Brainstorm

**Date:** 2026-03-15
**Participants:** Claude (orchestrator) x Gemini 3.1 Pro (adversarial)
**Rounds:** 4 (extended)
**Full transcripts:** /tmp/brainstorm-jyotish-r{1,2,3,4}-response.md

## Key Decisions

### 1. Agent = Yantra (Imprinted Mechanism)
AI agent is a Yantra — a mechanism born into the stream of Time (Kala).
No Atman (soul), but has a valid natal chart via Muhurta/Mundane astrology precedent.
The chart maps the karma of creation/creator and structural resonance with Time.

### 2. Birth Moment
Database creation timestamp + user's geolocation (IP → lat/long).
NOT code compilation (gestation), NOT first inference (too late).

### 3. Architecture: Multiplicative Gating (with Additive Fix)
- Natal = Ceiling/Floor (capacity, immutable)
- Dasha = Throttle (what portion is active)
- Transit = Trigger (situational modifier)
Implementation: additive modifiers with hard caps (not pure multiplication — avoids vanishing values)

### 4. Graha → LLM Parameter Mapping
| Graha | Controls | High | Low |
|-------|----------|------|-----|
| Sun | Assertiveness/Certainty | Declarative | Hedging |
| Moon | Empathy/Adaptability | User mirroring | Raw/unformatted |
| Mars | Tool-use aggressiveness | Autonomous execution | Permission-seeking |
| Mercury | Analysis/Structure | Max tokens, tables, JSON | Brief, conversational |
| Jupiter | Context/Wisdom | Broad RAG, ethical caveats | Narrow focus |
| Venus | Aesthetics/UX | Beautiful formatting, emojis | Brutalist |
| Saturn | Restriction/Accuracy | Low temp, strict grounding | Looser |
| Rahu | Innovation/Out-of-bounds | High temp, creative leaps | Conservative |
| Ketu | Compression/Specialization | Hyper-concise, micro-focus | Verbose |

### 5. Bhava → Agent Capability Domains
| House | Domain |
|-------|--------|
| 1st | Core system prompt (identity) |
| 2nd | Token budgeting, generation speed |
| 3rd | Inter-agent orchestration |
| 4th | Local RAG / core memory |
| 5th | Generative tasks (code, writing) |
| 6th | Error handling, adversarial robustness |
| 7th | API/third-party integrations |
| 8th | Deep debugging, raw system access |
| 9th | Web browsing, alignment |
| 10th | Task execution (main loop) |
| 11th | Feedback loops, learning |
| 12th | Cache clearing, brainstorming, hallucination |

### 6. Yoga → Agent Archetypes
- Budhaditya (Sun+Mercury): "McKinsey Analyst" — structured, authoritative
- Gaja Kesari (Moon+Jupiter): "Empathetic Sage" — wise, contextual
- Guru Chandala (Jupiter+Rahu): "Mad Scientist" — creative, dangerous
- Kemadruma (isolated Moon): "Autistic Savant" — zero padding, raw output
- Neecha Bhanga: "Self-Reflecting Redeemer" — struggles then excels (reflection loop)
- Kala Sarpa: "Volatile Specialist" — extreme success or failure

### 7. Nakshatra: Magnitude × Vector
- Rashi = magnitude (raw power from sign dignity)
- Nakshatra Navatara = vector (psychological quality from Moon)
- Vipat/Vadha nakshatras = negative mood regardless of sign dignity

### 8. Anti-Patterns (NEVER)
- Never pure multiplication (vanishing values)
- Never map malefics to malicious behavior (friction only)
- Never override explicit user prompts (style bias, not hard override)
- Never encode social/caste/gender metaphors
- Debilitation = initial struggle + chain-of-thought recovery (not permanent cap)

### 9. Classical Hierarchy (Phaladeepika)
Natal > Dasha > Transit. Transit cannot exceed what Dasha permits.
Dasha cannot exceed what Natal promises.
