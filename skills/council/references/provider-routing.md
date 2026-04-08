# Provider Routing Reference

## Member → Provider Affinity Map

Each member has a preferred provider and a tier (high=opus-class, mid=sonnet-class).
Polarity pairs are flagged — they MUST be separated across providers when possible.

| Member | Tier | Primary Affinity | Secondary | Polarity Pair |
|--------|------|-----------------|-----------|---------------|
| aristotle | high | anthropic | openrouter | lao-tzu |
| socrates | high | anthropic | openrouter | feynman |
| sun-tzu | mid | openai | openrouter | aurelius |
| ada | mid | openai | anthropic | machiavelli, rams |
| aurelius | high | anthropic | openrouter | sun-tzu |
| machiavelli | mid | openai | openrouter | ada |
| lao-tzu | high | anthropic | openrouter | aristotle |
| feynman | mid | openai | anthropic | socrates, kahneman |
| torvalds | mid | openai | anthropic | watts, musashi, meadows |
| musashi | mid | openai | openrouter | torvalds |
| watts | high | anthropic | openrouter | torvalds |
| karpathy | mid | openai | anthropic | sutskever, ada |
| sutskever | high | anthropic | openrouter | karpathy |
| kahneman | high | anthropic | openrouter | feynman |
| meadows | mid | openai | anthropic | torvalds |
| munger | mid | openai | openrouter | aristotle |
| taleb | high | anthropic | openrouter | karpathy |
| rams | mid | openai | anthropic | ada |
| jensen | mid | openai | openrouter | lao-tzu, watts |
| bezos | high | anthropic | openrouter | torvalds, musashi |
| graham | mid | openai | anthropic | aristotle, meadows |
| diogenes | high | anthropic | openrouter | bezos, aristotle |

## Tier → Model Map

### anthropic
- high → claude-opus-4-5
- mid  → claude-sonnet-4-5

### openai
- high → gpt-4o
- mid  → gpt-4o-mini

### openrouter
- high → anthropic/claude-opus-4-5
- mid  → openai/gpt-4o-mini

### gemini
- high → gemini-1.5-pro
- mid  → gemini-1.5-flash

### ollama
- high → best available (prefer qwen2.5:72b, llama3.3:70b)
- mid  → best available (prefer qwen2.5:7b, llama3.2:3b)

## Auto-Routing Algorithm

When the coordinator runs, apply this logic:

1. **Detect available providers** — run `detect-providers.sh`, parse JSON
2. **If only 1 provider available** — skip routing, assign all members to that provider
3. **If 2+ providers available:**
   a. For each polarity pair where BOTH members are selected: assign to different providers (hard constraint)
   b. Distribute remaining members evenly across available providers
   c. Use affinity map as tiebreaker when a member could go either way
   d. Higher-tier members (opus) get the premium model slot on their assigned provider
4. **Log the routing table** before running — transparency for the user

## Routing Table Output Format

Before every council run, emit this table:

```
Council Routing Table
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Member        Provider      Model                   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
feynman       openai        gpt-4o                  
torvalds      openai        gpt-4o-mini             
sun-tzu       anthropic     claude-sonnet-4-5       
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Polarity pairs separated: feynman/socrates ✓
Provider spread: 2 providers, 3 members
```

## Fallback Chain

If a provider call fails:
1. First retry on the same provider (once)
2. If still failing → fallback to anthropic/claude-sonnet-4-5
3. Log: `[FALLBACK] {member} failed on {provider}/{model} → anthropic/claude-sonnet-4-5`
4. Note the fallback in the final verdict's Provider Routing section

## Single-Provider Mode

If only anthropic is available (most common for standard Hermes installs):
- All members run on claude-sonnet-4-5 (mid) or claude-opus-4-5 (high tier)
- Routing table shows "Default models (single provider)"
- Deliberation still works — just less model diversity
- Note in verdict: "Single-provider run — model diversity limited"
