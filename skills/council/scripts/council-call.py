#!/usr/bin/env python3
"""
council-call.py — Unified council member caller.

Calls any supported LLM provider with a persona prompt and returns the member's analysis.
Used by the council coordinator to run members across different model families.

Usage:
  python3 council-call.py --provider anthropic --model claude-sonnet-4-5 \
    --persona /path/to/persona.md --question "Should we open-source?" \
    --round 1 --context ""

Supported providers:
  anthropic   — Claude via Anthropic API (ANTHROPIC_API_KEY)
  openai      — GPT via OpenAI API (OPENAI_API_KEY)
  openrouter  — Any model via OpenRouter (OPENROUTER_API_KEY)
  gemini      — Gemini via Google API (GEMINI_API_KEY)
  ollama      — Local models via Ollama (no key needed)
  xai         — Grok via xAI API (XAI_API_KEY)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def load_persona(path: str) -> str:
    with open(path) as f:
        return f.read()


def build_prompt(persona: str, question: str, round_num: int, context: str) -> str:
    round_instructions = {
        1: (
            "You are in Round 1: Independent Analysis.\n"
            "First, restate the question in ONE sentence through your analytical lens.\n"
            "Then produce your full analysis using your Standalone Output Format.\n"
            "Max 350 words. Reason from your own perspective — do NOT try to anticipate others.\n"
            "Be direct and take a clear position."
        ),
        2: (
            "You are in Round 2: Cross-Examination.\n"
            "You have read all other members' Round 1 analyses (provided in context).\n"
            "Respond using your Council Round 2 Output Format:\n"
            "1. Which member do you MOST disagree with and why? Engage their specific claims.\n"
            "2. Which member's insight strengthens your position? How?\n"
            "3. State your updated position (note any changes).\n"
            "4. Label your key claim: empirical | mechanistic | strategic | ethical | heuristic\n"
            "Max 250 words. Engage at least 2 members by name."
        ),
        3: (
            "You are in Round 3: Final Crystallization.\n"
            "State your final position in 75 words or less.\n"
            "No new arguments — only your clearest crystallized stance.\n"
            "Be direct. Take a side."
        ),
        99: (
            "You are in the Problem Restate Gate.\n"
            "In 2 sentences ONLY:\n"
            "1. Restate this problem through your analytical lens.\n"
            "2. Offer ONE alternative framing the original question may have missed.\n"
            "No analysis yet. Just the restatement."
        ),
    }

    instruction = round_instructions.get(round_num, round_instructions[1])

    prompt = f"""You are a council member in a structured multi-round deliberation.

Your persona and analytical framework:

{persona}

---

{instruction}

---

The question under deliberation:
{question}
"""

    if context:
        prompt += f"\n---\n\nContext from previous rounds / other members:\n{context}\n"

    return prompt


def call_anthropic(model: str, prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    payload = json.dumps({
        "model": model,
        "max_tokens": 700,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return data["content"][0]["text"]


def call_openai(model: str, prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com").rstrip("/")

    payload = json.dumps({
        "model": model,
        "max_tokens": 700,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def call_xai(model: str, prompt: str) -> str:
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        raise ValueError("XAI_API_KEY not set")

    payload = json.dumps({
        "model": model,
        "max_tokens": 700,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def call_openrouter(model: str, prompt: str) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not set")

    payload = json.dumps({
        "model": model,
        "max_tokens": 700,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jrbobbyhansen-pixel/hermes-council",
            "X-Title": "Council of High Intelligence",
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def call_gemini(model: str, prompt: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 700}
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"]


def call_ollama(model: str, prompt: str) -> str:
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 700}
    }).encode()

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read())
        return data["response"]


CALLERS = {
    "anthropic": call_anthropic,
    "openai": call_openai,
    "openrouter": call_openrouter,
    "gemini": call_gemini,
    "ollama": call_ollama,
    "xai": call_xai,
}


def main():
    parser = argparse.ArgumentParser(description="Call a council member on a specific provider.")
    parser.add_argument("--provider", required=True, choices=["anthropic", "openai", "openrouter", "gemini", "ollama", "xai"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--persona", required=True, help="Path to persona .md file")
    parser.add_argument("--question", required=True)
    parser.add_argument("--round", type=int, default=1, help="1=analysis, 2=cross-exam, 3=final, 99=restate")
    parser.add_argument("--context", default="", help="Context from prior rounds")
    parser.add_argument("--member", default="", help="Member name for labeling output")
    args = parser.parse_args()

    persona = load_persona(args.persona)
    prompt = build_prompt(persona, args.question, args.round, args.context)

    caller = CALLERS[args.provider]
    try:
        result = caller(args.model, prompt)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[ERROR] {args.provider}/{args.model} HTTP {e.code}: {body}", file=sys.stderr)
        # Fallback to anthropic if available
        if args.provider != "anthropic" and os.environ.get("ANTHROPIC_API_KEY"):
            print(f"[FALLBACK] Retrying {args.member} on anthropic/claude-sonnet-4-5", file=sys.stderr)
            result = call_anthropic("claude-sonnet-4-5", prompt)
        elif args.provider != "xai" and os.environ.get("XAI_API_KEY"):
            print(f"[FALLBACK] Retrying {args.member} on xai/grok-3-fast", file=sys.stderr)
            result = call_xai("grok-3-fast", prompt)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {args.provider}/{args.model}: {e}", file=sys.stderr)
        sys.exit(1)

    # Output JSON for easy parsing by coordinator
    output = {
        "member": args.member,
        "provider": args.provider,
        "model": args.model,
        "round": args.round,
        "analysis": result
    }
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
