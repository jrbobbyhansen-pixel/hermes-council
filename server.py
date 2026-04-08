#!/usr/bin/env python3
"""
server.py — Council of High Intelligence: Public API Server

Provides an HTTP API so external callers can POST a question and poll for a
council verdict. Uses only Python stdlib (http.server, threading, json, subprocess).

===== API REFERENCE =====

POST /council
  Body: {"question": str, "mode": "standard|deep", "triads": [...optional]}
  Returns: {"id": str, "status": "running", "question": str}
  Kicks off council-call.py subprocess chain asynchronously.
  The council runs stream-council.py under the hood.

GET /council/{id}
  Returns: {
    "id": str,
    "status": "running|complete|error",
    "question": str,
    "mode": str,
    "verdict": str|null,       -- full text output when complete
    "error": str|null,         -- error message if status=error
    "started_at": str,         -- ISO timestamp
    "completed_at": str|null   -- ISO timestamp when done
  }

GET /health
  Returns: {"status": "ok", "version": "1.0.0", "active_jobs": int}

GET /members
  Returns: {"members": [...]} — all 18 council members with name, figure, domain, polarity

===== Running =====

  python3 server.py --port 8742 --host 0.0.0.0

  Options:
    --port PORT     Port to listen on (default: 8742)
    --host HOST     Host to bind (default: 127.0.0.1)
    --personas-dir  Path to persona .md files
    --routing       Path to routing JSON (member → provider/model)
    --persist       Path to jobs JSON file for persistence across restarts
    --workers N     Max parallel council-call workers (default: 3)

===== Notes =====

- Jobs are stored in-memory + optionally persisted to a JSON file.
- If the server restarts, in-flight "running" jobs are marked "interrupted".
- The server does NOT call stream-council.py for single-member calls;
  it uses the same council-call.py subprocess pattern directly for simplicity.
- For --mode deep, the full 18-member deep protocol runs (takes ~10 min).
- CORS headers are included for browser/API client access.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from concurrent.futures import ThreadPoolExecutor, as_completed

VERSION = "1.0.0"

# All 18 council members
COUNCIL_MEMBERS = [
    {"name": "aristotle",   "figure": "Aristotle",         "domain": "Categorization & structure",         "polarity": "Classifies everything"},
    {"name": "socrates",    "figure": "Socrates",           "domain": "Assumption destruction",             "polarity": "Questions everything"},
    {"name": "sun-tzu",     "figure": "Sun Tzu",            "domain": "Adversarial strategy",              "polarity": "Reads terrain & competition"},
    {"name": "ada",         "figure": "Ada Lovelace",       "domain": "Formal systems & abstraction",      "polarity": "What can/can't be mechanized"},
    {"name": "aurelius",    "figure": "Marcus Aurelius",    "domain": "Resilience & moral clarity",        "polarity": "Control vs acceptance"},
    {"name": "machiavelli", "figure": "Machiavelli",        "domain": "Power dynamics & realpolitik",      "polarity": "How actors actually behave"},
    {"name": "lao-tzu",     "figure": "Lao Tzu",            "domain": "Non-action & emergence",            "polarity": "When less is more"},
    {"name": "feynman",     "figure": "Feynman",            "domain": "First-principles debugging",        "polarity": "Refuses unexplained complexity"},
    {"name": "torvalds",    "figure": "Linus Torvalds",     "domain": "Pragmatic engineering",             "polarity": "Ship it or shut up"},
    {"name": "musashi",     "figure": "Miyamoto Musashi",   "domain": "Strategic timing",                  "polarity": "The decisive strike"},
    {"name": "watts",       "figure": "Alan Watts",         "domain": "Perspective & reframing",           "polarity": "Dissolves false problems"},
    {"name": "karpathy",    "figure": "Andrej Karpathy",    "domain": "Neural network intuition",          "polarity": "How models actually learn"},
    {"name": "sutskever",   "figure": "Ilya Sutskever",     "domain": "Scaling frontier & AI safety",     "polarity": "When capability becomes risk"},
    {"name": "kahneman",    "figure": "Daniel Kahneman",    "domain": "Cognitive bias & decision science", "polarity": "Your thinking is the first error"},
    {"name": "meadows",     "figure": "Donella Meadows",    "domain": "Systems thinking",                  "polarity": "Redesign the system not the symptom"},
    {"name": "munger",      "figure": "Charlie Munger",     "domain": "Multi-model reasoning",             "polarity": "Invert — what guarantees failure?"},
    {"name": "taleb",       "figure": "Nassim Taleb",       "domain": "Antifragility & tail risk",         "polarity": "Design for the tail not the average"},
    {"name": "rams",        "figure": "Dieter Rams",        "domain": "User-centered design",              "polarity": "Less, but better"},
]

# Standard triads for auto-selection
TRIADS = {
    "strategy":    ["sun-tzu", "machiavelli", "aurelius"],
    "ethics":      ["aurelius", "socrates", "lao-tzu"],
    "debugging":   ["feynman", "socrates", "ada"],
    "risk":        ["sun-tzu", "aurelius", "feynman"],
    "shipping":    ["torvalds", "musashi", "feynman"],
    "decision":    ["kahneman", "munger", "aurelius"],
    "systems":     ["meadows", "lao-tzu", "aristotle"],
    "uncertainty": ["taleb", "sun-tzu", "sutskever"],
    "ai":          ["karpathy", "sutskever", "ada"],
    "design":      ["rams", "torvalds", "watts"],
}

DEFAULT_TRIADS = ["strategy", "risk"]

# Global job store: id → job dict
_jobs: dict = {}
_jobs_lock = threading.Lock()

# Config (set in main)
CONFIG = {
    "personas_dir": os.path.expanduser("~/.hermes/skills/council/references/personas"),
    "routing": {},
    "persist_path": os.path.expanduser("~/.hermes/skills/council/data/jobs.json"),
    "workers": 3,
    "scripts_dir": os.path.dirname(os.path.abspath(__file__)),
}


# ─── Persistence ─────────────────────────────────────────────────────────────

def load_jobs_from_disk():
    path = CONFIG["persist_path"]
    if not os.path.exists(path):
        return
    try:
        with open(path) as f:
            stored = json.load(f)
        with _jobs_lock:
            for job_id, job in stored.items():
                # Mark in-flight jobs from a previous run as interrupted
                if job.get("status") == "running":
                    job["status"] = "interrupted"
                    job["error"] = "Server restarted while job was running"
                _jobs[job_id] = job
        print(f"[persistence] Loaded {len(stored)} jobs from {path}", flush=True)
    except Exception as e:
        print(f"[persistence] Could not load jobs: {e}", file=sys.stderr)


def save_jobs_to_disk():
    path = CONFIG["persist_path"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with _jobs_lock:
            snapshot = dict(_jobs)
        with open(path, "w") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[persistence] Could not save jobs: {e}", file=sys.stderr)


# ─── Council Job Runner ───────────────────────────────────────────────────────

def _call_member(member, question, round_num, context=""):
    """Call one council member via council-call.py. Returns parsed dict."""
    route = CONFIG["routing"].get(member, {})
    provider = route.get("provider", "anthropic")
    model = route.get("model", "claude-sonnet-4-5")
    persona_path = os.path.join(CONFIG["personas_dir"], f"{member}.md")

    council_call = os.path.join(CONFIG["scripts_dir"], "skills", "council", "scripts", "council-call.py")
    if not os.path.exists(council_call):
        # Try relative to server.py
        council_call = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "skills", "council", "scripts", "council-call.py")

    cmd = [
        sys.executable, council_call,
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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            return {"member": member, "error": result.stderr.strip(), "round": round_num}
        return json.loads(result.stdout.strip())
    except Exception as e:
        return {"member": member, "error": str(e), "round": round_num}


def _run_council_job(job_id, question, mode, triad_names):
    """Background thread: run the full council and update job state."""
    # Resolve members from triads
    members = []
    used = set()
    for t in triad_names:
        for m in TRIADS.get(t, []):
            if m not in used:
                members.append(m)
                used.add(m)

    if not members:
        # Fallback: strategy + risk
        for t in DEFAULT_TRIADS:
            for m in TRIADS.get(t, []):
                if m not in used:
                    members.append(m)
                    used.add(m)

    with _jobs_lock:
        _jobs[job_id]["members"] = members
        _jobs[job_id]["triads"] = triad_names

    output_lines = []
    output_lines.append(f"Council of High Intelligence — {mode.upper()} MODE")
    output_lines.append(f"Question: {question}")
    output_lines.append(f"Members ({len(members)}): {', '.join(members)}")
    output_lines.append(f"Triads: {', '.join(triad_names)}")
    output_lines.append("=" * 60)

    rounds = [1, 2, 3]
    round_labels = {
        1: "Round 1: Independent Analysis",
        2: "Round 2: Cross-Examination",
        3: "Round 3: Final Crystallization",
    }

    active_members = list(members)
    context = ""
    all_results = {}

    for round_num in rounds:
        label = round_labels[round_num]
        output_lines.append(f"\n{label}")
        output_lines.append("-" * 40)

        round_results = []
        with ThreadPoolExecutor(max_workers=CONFIG["workers"]) as pool:
            futures = {
                pool.submit(_call_member, m, question, round_num, context): m
                for m in active_members
            }
            for future in as_completed(futures):
                result = future.result()
                if "error" in result:
                    output_lines.append(f"[FAIL] {result['member']}: {result['error']}")
                else:
                    member = result["member"]
                    analysis = result.get("analysis", "")
                    output_lines.append(f"\n[{member.upper()}]")
                    output_lines.append(analysis)
                    round_results.append(result)

        all_results[round_num] = round_results
        if not round_results:
            output_lines.append(f"[ABORT] Round {round_num} produced no results.")
            break

        # Build context from this round
        parts = []
        for r in round_results:
            parts.append(f"=== {r['member'].upper()} ===\n{r.get('analysis', '')}")
        context = "\n\n".join(parts)

        succeeded = {r["member"] for r in round_results}
        active_members = [m for m in active_members if m in succeeded]

    # Final synthesis header
    output_lines.append("\n" + "=" * 60)
    output_lines.append("FINAL POSITIONS SUMMARY")
    output_lines.append("=" * 60)
    final = all_results.get(3, [])
    for r in final:
        output_lines.append(f"\n[{r['member'].upper()}] — Final Position:")
        output_lines.append(r.get("analysis", "").strip())

    output_lines.append(f"\n{'='*60}")
    output_lines.append(f"Session complete: {len(final)}/{len(members)} members completed all rounds.")

    verdict_text = "\n".join(output_lines)
    completed_at = datetime.now(timezone.utc).isoformat()

    with _jobs_lock:
        _jobs[job_id]["status"] = "complete"
        _jobs[job_id]["verdict"] = verdict_text
        _jobs[job_id]["completed_at"] = completed_at

    save_jobs_to_disk()
    print(f"[job:{job_id[:8]}] Complete — {len(final)}/{len(members)} members.", flush=True)


def start_council_job(question, mode, triad_names):
    """Create job entry, start background thread, return job id."""
    job_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    job = {
        "id": job_id,
        "status": "running",
        "question": question,
        "mode": mode,
        "triads": triad_names,
        "members": [],
        "verdict": None,
        "error": None,
        "started_at": started_at,
        "completed_at": None,
    }

    with _jobs_lock:
        _jobs[job_id] = job

    save_jobs_to_disk()

    t = threading.Thread(
        target=_run_council_job,
        args=(job_id, question, mode, triad_names),
        daemon=True,
    )
    t.start()
    print(f"[job:{job_id[:8]}] Started — question: {question[:60]}", flush=True)
    return job_id


# ─── HTTP Handler ─────────────────────────────────────────────────────────────

class CouncilHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        # Use our own format
        print(f"[{self.address_string()}] {fmt % args}", flush=True)

    def send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        return json.loads(self.rfile.read(length))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        if path == "/health":
            with _jobs_lock:
                active = sum(1 for j in _jobs.values() if j["status"] == "running")
            self.send_json(200, {"status": "ok", "version": VERSION, "active_jobs": active})

        elif path == "/members":
            self.send_json(200, {"members": COUNCIL_MEMBERS, "total": len(COUNCIL_MEMBERS)})

        elif path.startswith("/council/"):
            job_id = path[len("/council/"):]
            # Support prefix matching (first 8 chars)
            found = None
            with _jobs_lock:
                if job_id in _jobs:
                    found = dict(_jobs[job_id])
                else:
                    # Try prefix match
                    for jid, job in _jobs.items():
                        if jid.startswith(job_id):
                            found = dict(job)
                            break
            if not found:
                self.send_json(404, {"error": f"Job {job_id} not found"})
            else:
                self.send_json(200, found)

        else:
            self.send_json(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")

        if path == "/council":
            try:
                body = self.read_json_body()
            except (json.JSONDecodeError, Exception) as e:
                self.send_json(400, {"error": f"Invalid JSON body: {e}"})
                return

            question = body.get("question", "").strip()
            if not question:
                self.send_json(400, {"error": "'question' is required"})
                return

            mode = body.get("mode", "standard")
            if mode not in ("standard", "deep"):
                self.send_json(400, {"error": "'mode' must be 'standard' or 'deep'"})
                return

            triads = body.get("triads", DEFAULT_TRIADS)
            if not isinstance(triads, list):
                self.send_json(400, {"error": "'triads' must be a list"})
                return

            job_id = start_council_job(question, mode, triads)
            self.send_json(202, {
                "id": job_id,
                "status": "running",
                "question": question,
                "mode": mode,
                "triads": triads,
                "poll_url": f"/council/{job_id}",
            })

        else:
            self.send_json(404, {"error": f"Unknown endpoint: {path}"})


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Council of High Intelligence — API Server")
    parser.add_argument("--port", type=int, default=8742, help="Port to listen on (default: 8742)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument(
        "--personas-dir",
        default=os.path.expanduser("~/.hermes/skills/council/references/personas"),
        help="Directory containing persona .md files"
    )
    parser.add_argument(
        "--routing",
        help="Path to JSON routing file (member → {provider, model})"
    )
    parser.add_argument(
        "--persist",
        default=os.path.expanduser("~/.hermes/skills/council/data/jobs.json"),
        help="Path to persist jobs JSON (default: ~/.hermes/skills/council/data/jobs.json)"
    )
    parser.add_argument(
        "--workers", type=int, default=3,
        help="Max parallel council-call workers per job (default: 3)"
    )
    args = parser.parse_args()

    CONFIG["personas_dir"] = args.personas_dir
    CONFIG["persist_path"] = args.persist
    CONFIG["workers"] = args.workers

    if args.routing:
        with open(args.routing) as f:
            CONFIG["routing"] = json.load(f)

    # Load persisted jobs
    os.makedirs(os.path.dirname(args.persist), exist_ok=True)
    load_jobs_from_disk()

    server = HTTPServer((args.host, args.port), CouncilHandler)
    print(f"Council API server listening on http://{args.host}:{args.port}")
    print(f"  POST /council         — Submit a question")
    print(f"  GET  /council/{{id}}    — Poll for result")
    print(f"  GET  /health          — Health check")
    print(f"  GET  /members         — List all 18 members")
    print(f"  Personas: {args.personas_dir}")
    print(f"  Persist:  {args.persist}")
    print(f"  Workers:  {args.workers}")
    print("Press Ctrl+C to stop.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        save_jobs_to_disk()
        server.shutdown()


if __name__ == "__main__":
    main()
