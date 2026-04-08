# hermes-council

**Council of High Intelligence — Hermes Agent Skill**

22 AI personas deliberate your hardest decisions in structured multi-round fights across multiple model providers. One command.

Built for [Hermes Agent](https://github.com/hamelsmu/hermes). Adapted from [council-of-high-intelligence](https://github.com/0xNyk/council-of-high-intelligence) by [@0xNyk](https://github.com/0xNyk).

---

## Quickstart

```bash
git clone https://github.com/jrbobbyhansen-pixel/hermes-council
cd hermes-council
./install.sh
```

Then in any Hermes session:

```
/council Should we open-source our agent framework?
/council --deep What is the right architecture for our AI stack?
```

---

## Why This Works

A single LLM gives you one reasoning path dressed up as confidence. The council gives you structured disagreement instead — 22 personas from different intellectual traditions who are explicitly designed to challenge each other.

**Real model diversity, not costume changes.** The council automatically detects your available providers (Anthropic, xAI/Grok, OpenAI, OpenRouter, Gemini, Ollama) and routes members across them. The natural dissenters — Socrates, Taleb, Watts, Diogenes — route to Grok by default. The builders — Feynman, Torvalds, Ada, Karpathy — route to Anthropic/OpenAI. When they disagree, it's model weights arguing, not the same substrate playing dress-up.

**`/council`** auto-selects the 2 best complementary triads for your question (6 members), runs a full 3-round deliberation with web-grounded research, and delivers two triad verdicts + synthesized recommendation.

**`/council --deep`** runs all 22 members with enforcement mechanisms (dissent quotas, novelty gates, counterfactual forcing, polarity pair adversarial challenges). Runs async, delivers to Telegram when done.

**Single-provider mode** works too — if you only have Anthropic, every member runs on Claude. You get structured multi-angle self-reflection through 22 different analytical frames. Genuinely useful, just honestly described.

---

## The 22 Council Members

| Member | Figure | Domain | Polarity | Default Provider |
|--------|--------|--------|----------|-----------------|
| aristotle | Aristotle | Categorization & structure | Classifies everything | anthropic |
| socrates | Socrates | Assumption destruction | Questions everything | **xai** |
| sun-tzu | Sun Tzu | Adversarial strategy | Reads terrain & competition | openai |
| ada | Ada Lovelace | Formal systems & abstraction | What can/can't be mechanized | openai |
| aurelius | Marcus Aurelius | Resilience & moral clarity | Control vs acceptance | anthropic |
| machiavelli | Machiavelli | Power dynamics & realpolitik | How actors actually behave | openai |
| lao-tzu | Lao Tzu | Non-action & emergence | When less is more | anthropic |
| feynman | Feynman | First-principles debugging | Refuses unexplained complexity | openai |
| torvalds | Linus Torvalds | Pragmatic engineering | Ship it or shut up | openai |
| musashi | Miyamoto Musashi | Strategic timing | The decisive strike | openai |
| watts | Alan Watts | Perspective & reframing | Dissolves false problems | **xai** |
| karpathy | Andrej Karpathy | Neural network intuition | How models actually learn | openai |
| sutskever | Ilya Sutskever | Scaling frontier & AI safety | When capability becomes risk | anthropic |
| kahneman | Daniel Kahneman | Cognitive bias & decision science | Your thinking is the first error | anthropic |
| meadows | Donella Meadows | Systems thinking | Redesign the system not the symptom | openai |
| munger | Charlie Munger | Multi-model reasoning | Invert — what guarantees failure? | openai |
| taleb | Nassim Taleb | Antifragility & tail risk | Design for the tail not the average | **xai** |
| rams | Dieter Rams | User-centered design | Less, but better | openai |
| jensen | Jensen Huang | Infrastructure & compute strategy | The GPU era changes everything | openai |
| bezos | Jeff Bezos | Customer obsession & long-term compounding | Day 1 or Day 2 — there is no middle | anthropic |
| graham | Paul Graham | Startup reality & what actually matters early | Do things that don't scale | openai |
| diogenes | Diogenes | Radical simplicity & assumption auditing | What if none of this matters? | **xai** |

Dissenters (socrates, taleb, watts, diogenes) route to xAI/Grok by default. Builders route to Anthropic/OpenAI. Polarity pairs are separated across providers as a hard constraint.

---

## Deliberation Modes

### `/council [question]` — Standard (2-3 min)

1. Provider detection — sources `~/.hermes/.env`, builds routing table across available providers
2. Auto-selects 2 best complementary triads (6 members, no overlap)
3. Web research brief per member (domain-specific DuckDuckGo + LLM synthesis)
4. Round 1: Independent analysis, blind-first (parallel batches of 3)
5. Round 2: Cross-examination — all 6 see all outputs, challenge each other across providers
6. Round 3: Final crystallization (75 words max per member)
7. Two triad verdicts + full synthesized recommendation

### `/council --deep [question]` — Extended (~10 min, async)

1. All 22 members across all available providers
2. Problem Restate Gate — each member reframes the question before analysis
3. Round 1: Independent analysis (400 words, blind-first)
4. Round 2: Full cross-examination with enforcement:
   - Dissent quota: <4 non-overlapping objections → force dissent prompt
   - Novelty gate: restating R1 without engaging → sent back
   - Agreement check: >60% consensus → counterfactual prompt to 3 dissenters
5. Round 3: Polarity pair adversarial challenges (11 pairs fight directly)
6. Round 4: Final positions (100 words max)
7. Full verdict with minority report + epistemic diversity scorecard
8. Delivered to Telegram when complete

---

## Pre-defined Triads (24 total)

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
| customer | bezos + rams + machiavelli | Customer obsession + user design + incentive reality |
| early-stage | graham + musashi + torvalds | Startup reality + strategic timing + ship it |
| infrastructure | jensen + karpathy + ada | Compute strategy + ML intuition + formal systems |
| simplicity | diogenes + lao-tzu + watts | Radical subtraction + emergence + reframing |

---

## Multi-Provider Routing

Credentials are loaded automatically from `~/.hermes/.env`. No manual export needed.

Supported providers:

| Provider | Env Var | High-tier Model | Mid-tier Model |
|----------|---------|-----------------|----------------|
| anthropic | `ANTHROPIC_API_KEY` | claude-opus-4-5 | claude-sonnet-4-5 |
| xai | `XAI_API_KEY` | grok-3 | grok-3-fast |
| openai | `OPENAI_API_KEY` | gpt-4o | gpt-4o-mini |
| openrouter | `OPENROUTER_API_KEY` | any | any |
| gemini | `GEMINI_API_KEY` | gemini-1.5-pro | gemini-1.5-flash |
| ollama | *(local)* | best available | best available |

`OPENAI_BASE_URL` is respected if set — useful for custom endpoints or providers with OpenAI-compatible APIs.

Run detection manually to see what's available:
```bash
bash skills/council/scripts/detect-providers.sh
```

---

## Advanced Features

### Web Research Per Member
Before Round 1, each member runs a domain-specific DuckDuckGo search and an LLM synthesizes the results in that member's voice. Feynman gets benchmarks. Sun Tzu gets competitive landscape. Karpathy gets recent ML results. Grounds the analysis in actual current data rather than pure model priors.

### Memory Integration
`inject-context.py` reads your Hermes project state — top-of-mind notes, session checkpoint, active project summaries — and injects it as context before deliberation. The council knows what you're building and your constraints. They deliberate on your actual situation.

### Verdict Tracking
`council-tracker.py` logs every verdict to a local SQLite database. Record what you actually decided (`decide`). Later, record what happened (`outcome`). The `stats` command shows member accuracy over time — which personas have been right most often on which types of questions.

```bash
# Log a verdict
python3 skills/council/scripts/council-tracker.py log --verdict-file verdict.json

# Record your decision
python3 skills/council/scripts/council-tracker.py decide --id {id} --decision "We shipped it"

# Record the outcome
python3 skills/council/scripts/council-tracker.py outcome --id {id} --outcome "Grew 40% in 3 months"

# See member accuracy leaderboard
python3 skills/council/scripts/council-tracker.py stats
```

### Streaming Output
`stream-council.py` runs the full deliberation and emits results as each member finishes each round — then produces a synthesized verdict at the end. Text mode for humans, JSON mode for pipes.

```bash
python3 skills/council/scripts/stream-council.py \
  --question "Should we open-source this?" \
  --members "feynman,socrates,ada,torvalds,machiavelli,watts" \
  --emit-format text
```

## File Structure

```
hermes-council/
├── README.md
├── install.sh                          # Installs full skill to ~/.hermes/skills/council/
├── LICENSE
└── skills/
    └── council/
        ├── SKILL.md                    # Full coordinator protocol for Hermes
        ├── references/
        │   ├── provider-routing.md     # Member→provider affinity map + tier→model table
        │   └── personas/               # 22 persona definition files
        │       ├── ada.md
        │       ├── aristotle.md
        │       ├── aurelius.md
        │       ├── bezos.md
        │       ├── diogenes.md
        │       ├── feynman.md
        │       ├── graham.md
        │       ├── jensen.md
        │       ├── kahneman.md
        │       ├── karpathy.md
        │       ├── lao-tzu.md
        │       ├── machiavelli.md
        │       ├── meadows.md
        │       ├── munger.md
        │       ├── musashi.md
        │       ├── rams.md
        │       ├── socrates.md
        │       ├── sun-tzu.md
        │       ├── sutskever.md
        │       ├── taleb.md
        │       ├── torvalds.md
        │       └── watts.md
        └── scripts/
            ├── detect-providers.sh     # Auto-detects available LLM providers
            ├── council-call.py         # Unified caller (anthropic/xai/openai/openrouter/gemini/ollama)
            ├── stream-council.py       # Full orchestrator with streaming output + synthesis
            ├── research-brief.py       # Domain-specific web research + LLM synthesis per member
            ├── inject-context.py       # Project memory injection from Hermes context files
            └── council-tracker.py      # SQLite verdict tracker with member accuracy stats
```

---

## Credits

- Original Claude Code skill: [council-of-high-intelligence](https://github.com/0xNyk/council-of-high-intelligence) by [@0xNyk](https://github.com/0xNyk)
- Hermes adaptation: [Bobby Hansen Jr.](https://github.com/jrbobbyhansen-pixel) ([@bobbyhansenjr](https://x.com/bobbyhansenjr)) + Rupert CLO

---

## License

[![CC0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)

CC0 — public domain. Do whatever you want with it.
