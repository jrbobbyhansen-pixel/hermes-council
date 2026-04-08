# hermes-council

**Council of High Intelligence — Hermes Agent Skill**

18 AI personas deliberate your hardest decisions in structured multi-round fights. One command.

Built for [Hermes Agent](https://github.com/hamelsmu/hermes). Adapted from [council-of-high-intelligence](https://github.com/0xNyk/council-of-high-intelligence) by [@0xNyk](https://github.com/0xNyk).

---

## Quickstart

```bash
./install.sh
```

Then in any Hermes session:

```
/council Should we open-source our agent framework?
/council --deep What is the right architecture for our AI stack?
```

---

## Why This Works

A single LLM gives you one reasoning path dressed up as confidence. The council gives you structured disagreement instead — 18 personas from different intellectual traditions who are explicitly designed to challenge each other.

**`/council`** auto-selects the 2 best complementary triads for your question (6 members), runs full 3-round deliberation, and delivers two triad verdicts + a Rupert meta-synthesis.

**`/council --deep`** runs all 18 members across multiple rounds with enforcement mechanisms (dissent quotas, novelty gates, counterfactual forcing, polarity pair adversarial challenges). Runs async, delivers to Telegram when done (~10 minutes).

---

## The 18 Council Members

| Member | Figure | Domain | Polarity |
|--------|--------|--------|----------|
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

## Deliberation Modes

### `/council [question]` — Standard (2-3 min)

1. Auto-selects 2 best complementary triads
2. Round 1: Independent analysis (6 members in parallel batches)
3. Round 2: Cross-examination (all 6 see all outputs)
4. Round 3: Final crystallization
5. Two triad verdicts + Rupert meta-synthesis

### `/council --deep [question]` — Extended (~10 min, async)

1. All 18 members
2. Problem Restate Gate (catches wrong questions)
3. Round 1: Independent analysis
4. Round 2: Full cross-examination with enforcement
5. Round 3: Polarity pair adversarial challenges (9 pairs)
6. Round 4: Final positions
7. Full council verdict with minority report + epistemic diversity scorecard

---

## Pre-defined Triads

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

## Installation

```bash
git clone https://github.com/bobbyhansenjr/hermes-council
cd hermes-council
./install.sh
```

The install script copies the skill and persona files to `~/.hermes/skills/council/`.

---

## File Structure

```
hermes-council/
├── README.md
├── install.sh
├── LICENSE
└── skills/
    └── council/
        ├── SKILL.md                    # Coordinator protocol
        └── references/
            └── personas/
                ├── ada.md
                ├── aristotle.md
                ├── aurelius.md
                ├── feynman.md
                ├── kahneman.md
                ├── karpathy.md
                ├── lao-tzu.md
                ├── machiavelli.md
                ├── meadows.md
                ├── munger.md
                ├── musashi.md
                ├── rams.md
                ├── socrates.md
                ├── sun-tzu.md
                ├── sutskever.md
                ├── taleb.md
                ├── torvalds.md
                └── watts.md
```

---

## Credits

- Original Claude Code skill: [council-of-high-intelligence](https://github.com/0xNyk/council-of-high-intelligence) by [@0xNyk](https://github.com/0xNyk)
- Hermes adaptation: [Bobby Hansen Jr.](https://github.com/jrbobbyhansen-pixel) ([@bobbyhansenjr](https://x.com/bobbyhansenjr)) + Rupert CLO

---

## License

[![CC0](https://licensebuttons.net/p/zero/1.0/88x31.png)](https://creativecommons.org/publicdomain/zero/1.0/)

CC0 — public domain. Do whatever you want with it.
