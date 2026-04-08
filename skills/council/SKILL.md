---
name: council
description: "Convene the Council of High Intelligence for multi-persona deliberation. /council runs 2 best triads with full 3-round deliberation + Rupert synthesis. /council --deep runs all 18 members in an extended multi-round fight, delivered async."
version: 1.0.0
author: Bobby Hansen Jr. (bobbyhansenjr) + Rupert CLO
license: CC0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [council, deliberation, multi-agent, decision, strategy]
    homepage: https://github.com/bobbyhansenjr/hermes-council
    triggers: ["/council", "/council --deep"]
---

# Council of High Intelligence — Hermes Skill

A multi-persona deliberation system. 18 thinkers argue your hardest decisions across multiple rounds with structured disagreement, enforcement mechanisms, and verdict synthesis.

Adapted from [council-of-high-intelligence](https://github.com/0xNyk/council-of-high-intelligence) for Hermes Agent.

---

## Invocation

```
/council Should we open-source our agent framework?
/council --deep What is the right architecture for KEEP's MLX agent stack?
```

**`/council [question]`** — Standard deliberation
- Auto-selects the 2 best complementary triads for the question (6 members total)
- Full 3-round deliberation: independent analysis → cross-examination → final crystallization
- Produces one verdict per triad + Rupert meta-synthesis

**`/council --deep [question]`** — Extended deliberation
- All 18 council members
- Extended multi-round deliberation with enforcement (dissent quota, novelty gate, counterfactual forcing)
- Runs as a background task (~10 minutes), delivered to Telegram when complete

---

## The 18 Council Members

| Name | Figure | Domain | Polarity |
|------|--------|--------|----------|
| aristotle | Aristotle | Categorization & structure | Classifies everything |
| socrates | Socrates | Assumption destruction | Questions everything |
| sun-tzu | Sun Tzu | Adversarial strategy | Reads terrain & competition |
| ada | Ada Lovelace | Formal systems & abstraction | What can/can't be mechanized |
| aurelius | Marcus Aurelius | Resilience & moral clarity | Control vs acceptance |
| machiavelli | Machiavelli | Power dynamics & realpolitik | How actors actually behave |
| lao-tzu | Lao Tzu | Non-action & emergence | When less is more |
| feynman | Feynman | First-principles debugging | Refuses unexplained complexity |
| torvalds | Linus Torvalds | Pragmatic engineering | Ship it or shut up |
| musashi | Miyamoto Musashi | Strategic timing | The decisive strike |
| watts | Alan Watts | Perspective & reframing | Dissolves false problems |
| karpathy | Andrej Karpathy | Neural network intuition | How models actually learn |
| sutskever | Ilya Sutskever | Scaling frontier & AI safety | When capability becomes risk |
| kahneman | Daniel Kahneman | Cognitive bias & decision science | Your thinking is the first error |
| meadows | Donella Meadows | Systems thinking | Redesign the system not the symptom |
| munger | Charlie Munger | Multi-model reasoning | Invert — what guarantees failure? |
| taleb | Nassim Taleb | Antifragility & tail risk | Design for the tail not the average |
| rams | Dieter Rams | User-centered design | Less, but better |

---

## Triads Reference

| Domain | Members | Rationale |
|--------|---------|-----------|
| architecture | aristotle + ada + feynman | Classify + formalize + simplicity-test |
| strategy | sun-tzu + machiavelli + aurelius | Terrain + incentives + moral grounding |
| ethics | aurelius + socrates + lao-tzu | Duty + questioning + natural order |
| debugging | feynman + socrates + ada | Bottom-up + assumption testing + formal verification |
| innovation | ada + lao-tzu + aristotle | Abstraction + emergence + classification |
| conflict | socrates + machiavelli + aurelius | Expose + predict + ground |
| complexity | lao-tzu + aristotle + ada | Emergence + categories + formalism |
| risk | sun-tzu + aurelius + feynman | Threats + resilience + empirical verification |
| shipping | torvalds + musashi + feynman | Pragmatism + timing + first-principles |
| product | torvalds + machiavelli + watts | Ship it + incentives + reframing |
| founder | musashi + sun-tzu + torvalds | Timing + terrain + engineering reality |
| ai | karpathy + sutskever + ada | Empirical ML + scaling frontier + formal limits |
| ai-product | karpathy + torvalds + machiavelli | ML capability + shipping pragmatism + incentives |
| ai-safety | sutskever + aurelius + socrates | Safety frontier + moral clarity + assumption destruction |
| decision | kahneman + munger + aurelius | Bias detection + inversion + moral clarity |
| systems | meadows + lao-tzu + aristotle | Feedback loops + emergence + categories |
| uncertainty | taleb + sun-tzu + sutskever | Tail risk + terrain + scaling frontier |
| design | rams + torvalds + watts | User clarity + maintainability + reframing |
| economics | munger + machiavelli + sun-tzu | Models + incentives + competition |
| bias | kahneman + socrates + watts | Cognitive bias + assumption destruction + frame audit |

---

## Polarity Pairs (Separation Constraint)

Never place these in the same triad when avoidable:
- Socrates ↔ Feynman (destroys top-down vs rebuilds bottom-up)
- Aristotle ↔ Lao Tzu (classifies everything vs structure IS the problem)
- Torvalds ↔ Musashi (ship now vs wait for perfect timing)
- Torvalds ↔ Watts (build it vs question if it should exist)
- Karpathy ↔ Sutskever (iterate fast vs pause and ensure safety)
- Kahneman ↔ Feynman (your cognition is the error vs trust first-principles)
- Meadows ↔ Torvalds (redesign the system vs fix the symptom)
- Taleb ↔ Karpathy (hidden tails vs smooth empirical curves)
- Rams ↔ Ada (what user needs vs what computation can do)

---

## Execution Protocol — /council (Standard)

### STEP 0: Detect mode and parse question

If input contains `--deep` → run DEEP MODE (see below)
Otherwise → run STANDARD MODE (this section)

### STEP 0.5: Provider Detection & Routing

Run provider detection:
```bash
bash ~/.hermes/skills/council/scripts/detect-providers.sh
```

Parse the JSON output:
- `provider_count == 1` → single-provider mode, skip routing, use that provider for all members
- `provider_count >= 2` → apply routing algorithm from `references/provider-routing.md`

**Routing algorithm (multi-provider):**
1. Load member→affinity map from `references/provider-routing.md`
2. For every polarity pair where both members are selected: assign to DIFFERENT providers (hard constraint)
3. Distribute remaining members evenly across available providers
4. Use affinity map as tiebreaker
5. High-tier members (aurelius, aristotle, socrates, lao-tzu, watts, sutskever, kahneman, taleb) → premium model slot
6. Mid-tier (all others) → standard model slot

**Emit routing table before proceeding** (always show this to the user):
```
Council Routing Table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Member        Provider      Model
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[member]      [provider]    [model]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Polarity pairs separated: [pair] ✓/✗
Provider spread: [N] providers, [M] members
```

**[CHECKPOINT]** Routing table confirmed before proceeding.

### STEP 1: Auto-Select 2 Complementary Triads

1. Read the question carefully
2. Score all 20 triads against the question using keyword matching + semantic fit
3. Select the TOP triad (most directly relevant)
4. Select the SECOND best triad that is COMPLEMENTARY — different domain, non-overlapping members
5. State your selection and rationale before proceeding

Selection rules:
- No member appears in both triads (6 unique members total)
- Prefer triads whose domains are orthogonal (e.g., `strategy` + `systems`, not `strategy` + `conflict`)
- If question is technical: ensure one technical triad + one strategic/systems triad
- If question is strategic: ensure one strategy triad + one risk/decision triad

**[CHECKPOINT]** State: "Triad 1: [name] → [members]. Triad 2: [name] → [members]. Rationale: [why these two]."

### STEP 2: Load Persona Definitions

For each of the 6 members, read their compact persona from the skill references:
`skill_view(name='council', file_path='references/personas/{name}.md')`

Extract for each member:
- Identity (who they are, how they think)
- Grounding Protocol (constraints on their reasoning)
- Output Format (how they structure their response)

### STEP 3: Round 1 — Independent Analysis (Parallel)

**Two execution paths based on routing:**

**Path A — Multi-provider (2+ providers detected):**
Use `council-call.py` via terminal for each member on their assigned provider:
```bash
python3 ~/.hermes/skills/council/scripts/council-call.py \
  --provider [PROVIDER] \
  --model [MODEL] \
  --persona ~/.hermes/skills/council/references/personas/[NAME].md \
  --question "[QUESTION]" \
  --round 1 \
  --member [NAME]
```
Run members in parallel batches of 3 via `delegate_task`. Each delegate runs the terminal command and returns the JSON output. Parse `analysis` field from each result.

**Path B — Single provider (delegate_task with embedded persona):**
Run 2 batches of 3 via `delegate_task` (parallel within batch):
Each member gets this prompt with full persona embedded:
```
You are [FIGURE] deliberating a hard question. Your identity and constraints:

[PASTE FULL PERSONA: Identity + Grounding Protocol]

The question under deliberation:
[QUESTION]

First, restate the question in ONE sentence through your analytical lens.
Then produce your independent analysis using your Standalone Output Format.
Max 350 words. Be direct.
```

Collect all 6 Round 1 outputs. Note which provider/model each came from.
**[CHECKPOINT]** Confirm 6 outputs collected. Log: `[R1 COMPLETE] {member} on {provider}/{model}: {word_count} words`

### STEP 4: Round 2 — Cross-Examination (Parallel within triad)

Each member sees ALL 6 Round 1 outputs (both triads). This creates productive cross-triad tension.

Run 2 batches:
```
You are [FIGURE] in Round 2 of a structured deliberation.

Your identity:
[PASTE PERSONA: Identity + Grounding Protocol]

Here are ALL Round 1 analyses from both triads:
[ALL 6 ROUND 1 OUTPUTS]

Now respond:
1. Which member do you MOST disagree with and why? Engage their specific claims.
2. Which member's insight strengthens your position? How?
3. Has your position changed? State your updated position.
4. Label your key claim: empirical | mechanistic | strategic | ethical | heuristic

Max 250 words. Engage at least 2 members by name.
```

**[CHECKPOINT]** Confirm 6 Round 2 outputs collected.

**Enforcement scan (run mentally):**
- At least 2 members must have non-overlapping objections (if not, note the convergence risk)
- If >70% agree: note this as low epistemic diversity in the verdict
- Each response must contain at least 1 new claim vs their Round 1 (if not, flag it)

### STEP 5: Round 3 — Final Crystallization (Parallel)

All 6 members simultaneously:
```
Final round. State your position in 75 words or less.
[FIGURE]: No new arguments — only crystallization of your stance.
```

Run as 2 batches of 3.
**[CHECKPOINT]** Confirm 6 final positions collected.

### STEP 6: Synthesize Verdict

Produce two separate triad verdicts, then one Rupert meta-synthesis.

**Triad Verdict Template:**
```
## [TRIAD NAME] Verdict — [Domain]
Members: [name] + [name] + [name]

### What They Agreed On
[Points of convergence]

### The Core Disagreement
[Irreconcilable tension between members]

### Minority Report
[The dissenting position and its strongest argument]

### Key Insight
[The single most valuable thing this triad contributed]

### Recommended Action
[Concrete next step emerging from this triad]
```

**Rupert Meta-Synthesis:**
```
## Rupert's Synthesis

### Where the triads agreed (cross-triad signal)
[What both triads converged on — high confidence]

### Where they diverged (tension to hold)
[What one triad saw that the other missed]

### What the council doesn't know
[Unresolved questions — what you'd need to know to decide more confidently]

### My recommendation
[Rupert's direct take integrating both triads]

### The question behind your question
[What this deliberation revealed about the real underlying issue]
```

---

## Execution Protocol — /council --deep (Extended)

### Overview

All 18 members. Extended rounds. Enforcement mechanisms. Background task.

Immediately respond: "Deep council convened — 18 members, extended deliberation. I'll ping you when the verdict is ready (approx. 10 minutes)."

Then spawn as a background `delegate_task` with this full protocol:

### DEEP STEP 1: Auto-Select Domain Focus

Identify the 3 most relevant triads for the question. These define the focal lenses, but ALL 18 members participate.

### DEEP STEP 2: Problem Restate Gate

Run all 18 members in 6 batches of 3:
```
You are [FIGURE]. In 2 sentences only:
1. Restate this problem through your analytical lens.
2. Offer one alternative framing the original question may have missed.
Question: [QUESTION]
```

Review all 18 restatements. Flag if >3 members reframe the question significantly differently — this means the question itself may be the problem.

### DEEP STEP 3: Round 1 — Independent Analysis

6 batches of 3, parallel within batch:
- Same prompt as standard mode but 400 words max
- Each member sees ONLY the question (blind-first)

### DEEP STEP 4: Round 2 — Full Cross-Examination

6 batches of 3:
- Each member sees ALL 18 Round 1 outputs
- Must engage 3+ other members by name
- 300 words max

**Enforcement (hard):**
- Dissent quota: if <4 members have non-overlapping objections → force dissent prompt on the 2 most consensus-aligned members
- Novelty gate: if any member restates R1 without engaging challenges → send back once
- Agreement check: if >60% agree → trigger counterfactual prompt to 3 most likely dissenters
- Anti-recursion: Socrates limited to 1 question per round

### DEEP STEP 5: Round 3 — Adversarial Challenge

Each member's strongest argument gets directly challenged by their polarity pair:
- Run 9 polarity pair challenges (2 members each = 9 mini-debates)
- Each pair: 150 words per member, direct engagement only

### DEEP STEP 6: Round 4 — Final Positions

All 18 members:
- 100 words max
- Crystallize final stance
- Note any position changes from earlier rounds

### DEEP STEP 7: Verdict Synthesis

Full council verdict with:
- Majority position (if 2/3 consensus exists)
- Minority report (dissenting coalition)
- Epistemic diversity scorecard
- Cross-triad signal (what MOST members agreed on)
- The question behind the question
- Rupert meta-synthesis and direct recommendation

Deliver to Telegram when complete.

---

## Adaptation Notes (Claude Code → Hermes)

The original council-of-high-intelligence was built for Claude Code's native subagent system. Key differences when running in Hermes:

- **delegate_task max 3 parallel**: Claude Code spawns N subagents freely; Hermes caps at 3 concurrent. Always batch in groups of 3, sequential between batches.
- **No ~/.claude/agents/ reads**: Claude Code agents auto-read their own definition file. In Hermes, the full Identity + Grounding Protocol must be embedded directly in the delegate_task prompt — reference files don't get auto-injected.
- **No /command system**: Hermes detects `/council` as a trigger phrase in user input; it's not a registered slash command. The skill coordinator protocol runs inline in the main conversation.
- **Async delivery for --deep**: Claude Code can run long sessions interactively. Hermes --deep should respond immediately ("convening...") then deliver results to Telegram when done.

## Pitfalls

- **delegate_task max 3 parallel**: Always batch 3 at a time, sequential between batches
- **Context window**: For --deep, each delegate gets only the context they need (not the full conversation history)
- **Persona fidelity**: Always embed the full Identity + Grounding Protocol in the persona prompt — don't summarize
- **Round 2 cross-triad**: Make sure ALL 6 R1 outputs go to all members in Round 2, not just same-triad outputs
- **Don't force consensus**: If members disagree irreconcilably, that IS the verdict — present the tension, don't paper over it

---

## Notes

- Persona reference files live in `references/personas/{name}.md` — 18 files, one per member
- Each persona file contains: Identity, Grounding Protocol, and Output Format (both Standalone and Council Round 2)
- The original Claude Code skill lives at `~/clawd/council-ref/` — these are adapted versions for Hermes
- GitHub: https://github.com/bobbyhansenjr/hermes-council
