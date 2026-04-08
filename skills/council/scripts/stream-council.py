#!/usr/bin/env python3
"""
stream-council.py — Streaming council orchestrator.

Runs a full multi-round council session and emits results to stdout as each
round completes, rather than buffering everything until done. Useful for:
  - Streaming progress to Telegram
  - Watching deliberation unfold in a terminal
  - Piping partial results to other tools

Takes the same core arguments as council-call.py but orchestrates the full
flow: round 1 (independent) → round 2 (cross-exam) → round 3 (final).

Usage:
  python3 stream-council.py \\
    --question "Should we open-source our agent framework?" \\
    --triads strategy,risk \\
    --members "aristotle,feynman,sun-tzu,taleb,aurelius,socrates" \\
    --routing path/to/routing.json \\
    --personas-dir ~/.hermes/skills/council/references/personas \\
    [--mode standard|deep] \\
    [--emit-format text|json]

Routing JSON format (maps member → provider/model):
  {
    "aristotle": {"provider": "anthropic", "model": "claude-sonnet-4-5"},
    "feynman":   {"provider": "openai",    "model": "gpt-4o"},
    ...
  }
  If no routing file provided: all members use ANTHROPIC_API_KEY + claude-sonnet-4-5

Emit formats:
  text  — Human-readable round summaries (default, great for terminal/Telegram)
  json  — Machine-readable events, one JSON object per line (great for piping)

Exit codes:
  0 — All rounds completed
  1 — Fatal error (missing keys, all members failed)
  2 — Partial failure (some members failed but council completed with remaining)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone


def load_dotenv(path):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def synthesize_verdict(all_round_results, members, question):
    """Call LLM to synthesize a final council verdict from all round outputs."""
    final_results = all_round_results.get(3, [])
    r1_results = all_round_results.get(1, [])
    r2_results = all_round_results.get(2, [])

    formatted_final_positions = ""
    for r in final_results:
        member = r.get("member", "unknown")
        analysis = r.get("analysis", "").strip()
        formatted_final_positions += f"\n[{member.upper()}]\n{analysis}\n"

    key_earlier_points = ""
    for r in r1_results:
        member = r.get("member", "unknown")
        analysis = r.get("analysis", "").strip()
        # Take first 200 chars as key point
        snippet = analysis[:200].rstrip() + ("..." if len(analysis) > 200 else "")
        key_earlier_points += f"\nR1 [{member.upper()}]: {snippet}\n"
    for r in r2_results:
        member = r.get("member", "unknown")
        analysis = r.get("analysis", "").strip()
        snippet = analysis[:200].rstrip() + ("..." if len(analysis) > 200 else "")
        key_earlier_points += f"\nR2 [{member.upper()}]: {snippet}\n"

    prompt = (
        f"You are synthesizing a council deliberation verdict.\n\n"
        f"The question debated: {question}\n\n"
        f"Final positions from all council members:\n{formatted_final_positions}\n"
        f"Key points from earlier rounds:\n{key_earlier_points}\n"
        f"Produce a structured synthesis:\n"
        f"## What the Council Agreed On\n"
        f"## The Core Tension (irreconcilable disagreement)\n"
        f"## Minority Report (strongest dissenting view)\n"
        f"## Recommended Action\n"
        f"## What the Council Doesn't Know\n\n"
        f"Be direct and concrete. 400 words max."
    )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers=headers
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]

    xai_key = os.environ.get("XAI_API_KEY")
    if xai_key:
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {xai_key}",
            "content-type": "application/json",
        }
        payload = {
            "model": "grok-beta",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode(), headers=headers
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]

    return None

# Path to council-call.py (same directory as this script)
COUNCIL_CALL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "council-call.py")

# Default fallback provider/model
DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-5"


def emit_text(msg, flush=True):
    print(msg, flush=flush)


def emit_json(event_type, data):
    obj = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data
    }
    print(json.dumps(obj, ensure_ascii=False), flush=True)


def call_member(member, provider, model, persona_path, question, round_num, context=""):
    """Run council-call.py for one member and return parsed output dict."""
    cmd = [
        sys.executable, COUNCIL_CALL,
        "--provider", provider,
        "--model", model,
        "--persona", persona_path,
        "--question", question,
        "--round", str(round_num),
        "--member", member,
    ]
    if context:
        cmd += ["--context", context]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            return {
                "member": member,
                "error": result.stderr.strip() or f"exit code {result.returncode}",
                "round": round_num,
            }
        return json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        return {"member": member, "error": "timeout after 180s", "round": round_num}
    except json.JSONDecodeError as e:
        return {"member": member, "error": f"JSON parse error: {e}", "round": round_num}
    except Exception as e:
        return {"member": member, "error": str(e), "round": round_num}


def run_round(
    round_num,
    members,
    routing,
    personas_dir,
    question,
    context,
    emit_fmt,
    max_workers=3,
):
    """
    Run one round for all members in parallel (up to max_workers at once).
    Emits progress as each member completes.
    Returns list of result dicts.
    """
    round_labels = {1: "Round 1: Independent Analysis", 2: "Round 2: Cross-Examination", 3: "Round 3: Final Crystallization"}
    label = round_labels.get(round_num, f"Round {round_num}")

    if emit_fmt == "text":
        emit_text(f"\n{'='*60}")
        emit_text(f"  {label}")
        emit_text(f"{'='*60}")
    else:
        emit_json("round_start", {"round": round_num, "label": label, "members": members})

    results = []
    failed = []

    futures_map = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for member in members:
            route = routing.get(member, {})
            provider = route.get("provider", DEFAULT_PROVIDER)
            model = route.get("model", DEFAULT_MODEL)
            persona_path = os.path.join(personas_dir, f"{member}.md")

            if not os.path.exists(persona_path):
                if emit_fmt == "text":
                    emit_text(f"  [SKIP] {member}: persona file not found at {persona_path}")
                else:
                    emit_json("member_skip", {"member": member, "reason": "persona not found", "round": round_num})
                failed.append(member)
                continue

            future = pool.submit(
                call_member,
                member, provider, model, persona_path,
                question, round_num, context
            )
            futures_map[future] = (member, provider, model)

        for future in as_completed(futures_map):
            member, provider, model = futures_map[future]
            result = future.result()

            if "error" in result:
                if emit_fmt == "text":
                    emit_text(f"  [FAIL] {member} ({provider}/{model}): {result['error']}")
                else:
                    emit_json("member_error", {
                        "member": member, "provider": provider, "model": model,
                        "error": result["error"], "round": round_num
                    })
                failed.append(member)
            else:
                analysis = result.get("analysis", "")
                word_count = len(analysis.split())
                if emit_fmt == "text":
                    emit_text(f"\n  [{member.upper()}] ({provider}/{model}) — {word_count} words")
                    emit_text(f"  {'-'*55}")
                    # Print the analysis indented
                    for line in analysis.strip().splitlines():
                        emit_text(f"  {line}")
                else:
                    emit_json("member_complete", {
                        "member": member, "provider": provider, "model": model,
                        "round": round_num, "analysis": analysis, "word_count": word_count
                    })
                results.append(result)

    if emit_fmt == "text":
        n_ok = len(results)
        n_fail = len(failed)
        emit_text(f"\n  [{label}] Complete: {n_ok} succeeded, {n_fail} failed")
    else:
        emit_json("round_complete", {
            "round": round_num, "succeeded": len(results), "failed": len(failed)
        })

    return results, failed


def build_context_from_results(results):
    """Format all member analyses into a context block for the next round."""
    parts = []
    for r in results:
        member = r.get("member", "unknown")
        analysis = r.get("analysis", "")
        parts.append(f"=== {member.upper()} ===\n{analysis}")
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Stream a full council deliberation round-by-round."
    )
    parser.add_argument("--question", required=True, help="The question under deliberation")
    parser.add_argument(
        "--members", required=True,
        help="Comma-separated member names (e.g. aristotle,feynman,sun-tzu)"
    )
    parser.add_argument(
        "--triads", default="",
        help="Comma-separated triad names (metadata only, e.g. strategy,risk)"
    )
    parser.add_argument(
        "--routing",
        help="Path to JSON routing file (member → provider/model). Default: all on anthropic."
    )
    parser.add_argument(
        "--personas-dir",
        default=os.path.expanduser("~/.hermes/skills/council/references/personas"),
        help="Directory containing persona .md files"
    )
    parser.add_argument(
        "--mode", choices=["standard", "deep"], default="standard",
        help="standard=3 rounds, deep=4 rounds with adversarial (default: standard)"
    )
    parser.add_argument(
        "--emit-format", choices=["text", "json"], default="text",
        help="Output format: text (human readable) or json (one event per line)"
    )
    parser.add_argument(
        "--workers", type=int, default=3,
        help="Max parallel member calls per round (default: 3)"
    )
    args = parser.parse_args()

    load_dotenv('~/.hermes/.env')

    members = [m.strip() for m in args.members.split(",") if m.strip()]
    triads = [t.strip() for t in args.triads.split(",") if t.strip()] if args.triads else []

    if not members:
        print("[ERROR] No members specified.", file=sys.stderr)
        sys.exit(1)

    routing = {}
    if args.routing:
        with open(args.routing) as f:
            routing = json.load(f)

    emit_fmt = args.emit_format
    start_ts = datetime.now(timezone.utc).isoformat()

    if emit_fmt == "text":
        emit_text(f"\nCouncil of High Intelligence — Streaming Session")
        emit_text(f"{'='*60}")
        emit_text(f"  Question: {args.question}")
        emit_text(f"  Mode: {args.mode}")
        emit_text(f"  Members ({len(members)}): {', '.join(members)}")
        if triads:
            emit_text(f"  Triads: {', '.join(triads)}")
        emit_text(f"  Started: {start_ts[:19].replace('T', ' ')} UTC")
        emit_text(f"{'='*60}")
    else:
        emit_json("session_start", {
            "question": args.question,
            "mode": args.mode,
            "members": members,
            "triads": triads,
        })

    # Determine rounds to run
    rounds = [1, 2, 3]  # standard
    if args.mode == "deep":
        rounds = [1, 2, 3]  # deep mode in stream-council runs 3 full rounds
        # (full 18-member deep mode with adversarial R4 is better orchestrated by the agent)

    all_round_results = {}
    active_members = list(members)
    context = ""

    for round_num in rounds:
        if not active_members:
            if emit_fmt == "text":
                emit_text("\n[ABORT] No members remaining after failures.")
            else:
                emit_json("session_abort", {"reason": "no members remaining"})
            sys.exit(1)

        results, failed = run_round(
            round_num=round_num,
            members=active_members,
            routing=routing,
            personas_dir=args.personas_dir,
            question=args.question,
            context=context,
            emit_fmt=emit_fmt,
            max_workers=args.workers,
        )

        all_round_results[round_num] = results

        if not results:
            if emit_fmt == "text":
                emit_text(f"\n[ABORT] Round {round_num} produced zero results — aborting.")
            else:
                emit_json("session_abort", {"reason": f"round {round_num} zero results"})
            sys.exit(1)

        # Build context from successful members for next round
        context = build_context_from_results(results)

        # Only carry forward members that succeeded
        succeeded = {r["member"] for r in results}
        active_members = [m for m in active_members if m in succeeded]

    # Final summary
    final_results = all_round_results.get(3, [])
    end_ts = datetime.now(timezone.utc).isoformat()

    if emit_fmt == "text":
        emit_text(f"\n{'='*60}")
        emit_text("  FINAL POSITIONS")
        emit_text(f"{'='*60}")
        for r in final_results:
            emit_text(f"\n  [{r['member'].upper()}]")
            for line in r.get("analysis", "").strip().splitlines():
                emit_text(f"  {line}")
        emit_text(f"\n{'='*60}")
        emit_text(f"  Session complete. {len(final_results)}/{len(members)} members reached final round.")
        emit_text(f"  Ended: {end_ts[:19].replace('T', ' ')} UTC")
        emit_text(f"{'='*60}")
    else:
        emit_json("session_complete", {
            "members_completed": len(final_results),
            "members_total": len(members),
            "final_positions": [
                {"member": r["member"], "final_position": r.get("analysis", "")}
                for r in final_results
            ],
        })

    # Synthesis step
    synthesis = None
    try:
        synthesis = synthesize_verdict(all_round_results, members, args.question)
    except Exception as e:
        if emit_fmt == "text":
            emit_text(f"\n  [SYNTHESIS ERROR] {e}")
        else:
            emit_json("synthesis_error", {"error": str(e)})

    if synthesis:
        if emit_fmt == "text":
            emit_text(f"\n{'='*60}")
            emit_text("  COUNCIL SYNTHESIS")
            emit_text(f"{'='*60}")
            for line in synthesis.strip().splitlines():
                emit_text(f"  {line}")
            emit_text(f"{'='*60}")
        else:
            emit_json("synthesis", {"verdict": synthesis})
    else:
        if emit_fmt == "text":
            emit_text("\n  [SYNTHESIS] No API key available — skipping synthesized verdict.")
        else:
            emit_json("synthesis", {"verdict": None, "reason": "no API key available"})

    exit_code = 0 if len(final_results) == len(members) else 2
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
