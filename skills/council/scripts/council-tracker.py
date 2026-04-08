#!/usr/bin/env python3
"""
council-tracker.py — SQLite-based verdict tracker for the Council of High Intelligence.

Tracks council decisions, user outcomes, and member accuracy over time.
DB lives at ~/.hermes/skills/council/data/verdicts.db

Commands:
  log                      Store a new verdict (reads JSON from stdin or --verdict-file)
  decide --id ID --decision TEXT   Record what user actually decided
  outcome --id ID --outcome TEXT   Record what happened (triggers accuracy scoring)
  stats                    Show member accuracy stats
  history [--limit N]      Show past verdicts (default: 10)
  pending                  Show verdicts waiting for outcome feedback

Verdict JSON format (for `log` command):
{
  "id": "optional-uuid",           # auto-generated if absent
  "question": "Should we...",
  "mode": "standard|deep",
  "triads": ["strategy", "risk"],
  "members": ["aristotle", "feynman"],
  "routing": {"aristotle": {"provider": "anthropic", "model": "claude-sonnet-4-5"}},
  "verdict_text": "Full verdict output...",
  "member_positions": [            # optional, for accuracy tracking
    {
      "member": "aristotle",
      "provider": "anthropic",
      "model": "claude-sonnet-4-5",
      "round1": "Aristotle round 1 text...",
      "round2": "Aristotle round 2 text...",
      "final_position": "Aristotle final stance..."
    }
  ]
}
"""

import argparse
import json
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone


DB_PATH = os.path.expanduser("~/.hermes/skills/council/data/verdicts.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS verdicts (
            id TEXT PRIMARY KEY,
            timestamp TEXT,
            question TEXT,
            mode TEXT,
            triads TEXT,
            members TEXT,
            routing TEXT,
            verdict_text TEXT,
            user_decision TEXT,
            outcome TEXT,
            outcome_timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS member_positions (
            verdict_id TEXT,
            member TEXT,
            provider TEXT,
            model TEXT,
            round1 TEXT,
            round2 TEXT,
            final_position TEXT,
            proved_right INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_mp_verdict ON member_positions(verdict_id);
        CREATE INDEX IF NOT EXISTS idx_verdicts_ts ON verdicts(timestamp DESC);
    """)
    conn.commit()


def cmd_log(args):
    if args.verdict_file:
        with open(args.verdict_file) as f:
            data = json.load(f)
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            print("[ERROR] No JSON input. Pipe JSON to stdin or use --verdict-file.", file=sys.stderr)
            sys.exit(1)
        data = json.loads(raw)

    verdict_id = data.get("id") or str(uuid.uuid4())
    timestamp = data.get("timestamp") or datetime.now(timezone.utc).isoformat()

    conn = get_db()
    init_db(conn)

    conn.execute("""
        INSERT OR REPLACE INTO verdicts
          (id, timestamp, question, mode, triads, members, routing, verdict_text,
           user_decision, outcome, outcome_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        verdict_id,
        timestamp,
        data.get("question", ""),
        data.get("mode", "standard"),
        json.dumps(data.get("triads", [])),
        json.dumps(data.get("members", [])),
        json.dumps(data.get("routing", {})),
        data.get("verdict_text", ""),
        data.get("user_decision"),
        data.get("outcome"),
        data.get("outcome_timestamp"),
    ))

    for pos in data.get("member_positions", []):
        conn.execute("""
            INSERT INTO member_positions
              (verdict_id, member, provider, model, round1, round2, final_position, proved_right)
            VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
        """, (
            verdict_id,
            pos.get("member", ""),
            pos.get("provider", ""),
            pos.get("model", ""),
            pos.get("round1", ""),
            pos.get("round2", ""),
            pos.get("final_position", ""),
        ))

    conn.commit()
    conn.close()

    print(f"Verdict logged: {verdict_id}")
    print(f"  Question: {data.get('question', '')[:80]}")
    print(f"  Mode: {data.get('mode', 'standard')}")
    members = data.get("members", [])
    if members:
        print(f"  Members: {', '.join(members)}")


def cmd_decide(args):
    conn = get_db()
    init_db(conn)
    cur = conn.execute("SELECT id, question FROM verdicts WHERE id = ?", (args.id,))
    row = cur.fetchone()
    if not row:
        print(f"[ERROR] Verdict {args.id} not found.", file=sys.stderr)
        sys.exit(1)
    conn.execute(
        "UPDATE verdicts SET user_decision = ? WHERE id = ?",
        (args.decision, args.id)
    )
    conn.commit()
    conn.close()
    print(f"Decision recorded for {args.id[:8]}...")
    print(f"  Question: {row['question'][:80]}")
    print(f"  Decision: {args.decision}")


def cmd_outcome(args):
    conn = get_db()
    init_db(conn)
    cur = conn.execute("SELECT id, question FROM verdicts WHERE id = ?", (args.id,))
    row = cur.fetchone()
    if not row:
        print(f"[ERROR] Verdict {args.id} not found.", file=sys.stderr)
        sys.exit(1)

    outcome_ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE verdicts SET outcome = ?, outcome_timestamp = ? WHERE id = ?",
        (args.outcome, outcome_ts, args.id)
    )

    # Score member accuracy if --scores provided
    # Format: --scores "aristotle:1,feynman:0,socrates:1"
    if args.scores:
        for pair in args.scores.split(","):
            pair = pair.strip()
            if ":" not in pair:
                continue
            member, score_str = pair.split(":", 1)
            try:
                score = int(score_str.strip())
            except ValueError:
                continue
            conn.execute(
                """UPDATE member_positions SET proved_right = ?
                   WHERE verdict_id = ? AND member = ?""",
                (score, args.id, member.strip())
            )

    conn.commit()
    conn.close()
    print(f"Outcome recorded for {args.id[:8]}...")
    print(f"  Question: {row['question'][:80]}")
    print(f"  Outcome: {args.outcome}")
    if args.scores:
        print(f"  Accuracy scores applied: {args.scores}")
    print()
    print("Tip: Use --scores 'member:1,member:0' to mark who proved right/wrong.")


def cmd_stats(args):
    conn = get_db()
    init_db(conn)

    rows = conn.execute("""
        SELECT
            member,
            COUNT(*) as total,
            SUM(CASE WHEN proved_right = 1 THEN 1 ELSE 0 END) as correct,
            SUM(CASE WHEN proved_right = 0 THEN 1 ELSE 0 END) as wrong,
            SUM(CASE WHEN proved_right IS NULL THEN 1 ELSE 0 END) as unscored
        FROM member_positions
        GROUP BY member
        ORDER BY
            CAST(SUM(CASE WHEN proved_right = 1 THEN 1 ELSE 0 END) AS REAL) /
            NULLIF(SUM(CASE WHEN proved_right IS NOT NULL THEN 1 ELSE 0 END), 0) DESC NULLS LAST,
            COUNT(*) DESC
    """).fetchall()

    conn.close()

    if not rows:
        print("No member accuracy data yet. Use `outcome --id ID --scores member:1,member:0` to record accuracy.")
        return

    print("Member Accuracy Stats")
    print("=" * 58)
    print(f"{'Member':<16} {'Scored':>6} {'Correct':>8} {'Wrong':>6} {'Accuracy':>9} {'Unscored':>9}")
    print("-" * 58)
    for r in rows:
        scored = (r["correct"] or 0) + (r["wrong"] or 0)
        accuracy = (r["correct"] / scored * 100) if scored > 0 else None
        acc_str = f"{accuracy:.1f}%" if accuracy is not None else "—"
        print(
            f"{r['member']:<16} {scored:>6} {r['correct'] or 0:>8} "
            f"{r['wrong'] or 0:>6} {acc_str:>9} {r['unscored'] or 0:>9}"
        )
    print("-" * 58)

    total_scored = sum((r["correct"] or 0) + (r["wrong"] or 0) for r in rows)
    total_correct = sum(r["correct"] or 0 for r in rows)
    if total_scored > 0:
        print(f"\nOverall council accuracy: {total_correct}/{total_scored} = {total_correct/total_scored*100:.1f}%")


def cmd_history(args):
    conn = get_db()
    init_db(conn)

    limit = args.limit if args.limit else 10
    rows = conn.execute("""
        SELECT id, timestamp, question, mode, user_decision, outcome
        FROM verdicts
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    if not rows:
        print("No verdicts logged yet.")
        return

    print(f"Last {len(rows)} Verdicts")
    print("=" * 70)
    for r in rows:
        ts = r["timestamp"][:19].replace("T", " ") if r["timestamp"] else "unknown"
        decision_marker = " ✓" if r["user_decision"] else ""
        outcome_marker = " [outcome recorded]" if r["outcome"] else " [pending outcome]"
        print(f"\n{r['id'][:8]}...  {ts}  [{r['mode']}]{decision_marker}")
        print(f"  Q: {r['question'][:75]}")
        if r["user_decision"]:
            print(f"  Decision: {r['user_decision'][:60]}")
        if r["outcome"]:
            print(f"  Outcome: {r['outcome'][:60]}")
        else:
            print(f"  {outcome_marker.strip()}")
    print()


def cmd_pending(args):
    conn = get_db()
    init_db(conn)

    rows = conn.execute("""
        SELECT id, timestamp, question, mode, user_decision
        FROM verdicts
        WHERE outcome IS NULL
        ORDER BY timestamp DESC
    """).fetchall()
    conn.close()

    if not rows:
        print("No pending verdicts — all have outcome feedback.")
        return

    print(f"{len(rows)} verdict(s) pending outcome feedback:")
    print("=" * 65)
    for r in rows:
        ts = r["timestamp"][:19].replace("T", " ") if r["timestamp"] else "unknown"
        has_decision = "decision ✓" if r["user_decision"] else "no decision yet"
        print(f"\n{r['id'][:8]}...  {ts}  [{r['mode']}]  {has_decision}")
        print(f"  Q: {r['question'][:70]}")
        if r["user_decision"]:
            print(f"  Decided: {r['user_decision'][:60]}")
        print(f"  Record outcome: council-tracker.py outcome --id {r['id'][:8]} --outcome \"...\"")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Council verdict tracker — log, track outcomes, and measure member accuracy."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # log
    p_log = subparsers.add_parser("log", help="Store a new verdict from stdin or file")
    p_log.add_argument("--verdict-file", help="Path to JSON file (default: read from stdin)")

    # decide
    p_decide = subparsers.add_parser("decide", help="Record what the user actually decided")
    p_decide.add_argument("--id", required=True, help="Verdict UUID (or prefix)")
    p_decide.add_argument("--decision", required=True, help="What the user decided")

    # outcome
    p_outcome = subparsers.add_parser("outcome", help="Record what happened (enables accuracy scoring)")
    p_outcome.add_argument("--id", required=True, help="Verdict UUID (or prefix)")
    p_outcome.add_argument("--outcome", required=True, help="Description of what happened")
    p_outcome.add_argument(
        "--scores",
        help="Member accuracy: 'aristotle:1,feynman:0' (1=proved right, 0=proved wrong)"
    )

    # stats
    subparsers.add_parser("stats", help="Show member accuracy stats")

    # history
    p_history = subparsers.add_parser("history", help="Show past verdicts")
    p_history.add_argument("--limit", type=int, default=10, help="Number of verdicts to show (default: 10)")

    # pending
    subparsers.add_parser("pending", help="Show verdicts waiting for outcome feedback")

    args = parser.parse_args()

    if args.command == "log":
        cmd_log(args)
    elif args.command == "decide":
        cmd_decide(args)
    elif args.command == "outcome":
        cmd_outcome(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "pending":
        cmd_pending(args)


if __name__ == "__main__":
    main()
