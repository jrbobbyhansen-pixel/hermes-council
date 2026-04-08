#!/usr/bin/env python3
"""
inject-context.py — Injects project memory context into council sessions.
Reads Bobby's project files and formats them as council context.

Usage:
    python3 inject-context.py
    python3 inject-context.py --project hermes-council
    python3 inject-context.py --clawd-dir ~/clawd
    python3 inject-context.py --preview
"""

import argparse
import glob
import os
import sys


DEFAULT_CLAWD_DIR = os.path.expanduser("~/clawd")


def read_lines(path: str, n: int) -> list:
    """Read first n non-empty lines from a file. Returns [] if file missing."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for line in f:
                stripped = line.rstrip("\n")
                if stripped.strip():
                    lines.append(stripped)
                    if len(lines) >= n:
                        break
        return lines
    except (OSError, IOError):
        return []


def read_first_line(path: str) -> str:
    """Read first non-empty line from a file. Returns '' if missing."""
    lines = read_lines(path, 1)
    return lines[0] if lines else ""


def get_top_of_mind(clawd_dir: str) -> list:
    path = os.path.join(clawd_dir, "life", "areas", "bobby", "top-of-mind.md")
    return read_lines(path, 3)


def get_session_checkpoint(clawd_dir: str) -> list:
    path = os.path.join(clawd_dir, "memory", "session-checkpoint.md")
    return read_lines(path, 5)


def get_project_summaries(clawd_dir: str, target_project: str = "") -> list:
    """
    Returns list of (project_name, first_line_of_summary) tuples.
    Max 3 most recently modified summary files.
    If target_project is given, prioritize that one.
    """
    pattern = os.path.join(clawd_dir, "life", "projects", "*", "summary.md")
    matches = glob.glob(pattern)

    if not matches:
        return []

    # Sort by modification time, newest first
    matches.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)

    # If a project is specified, put it first if found
    if target_project:
        target_lower = target_project.lower()
        prioritized = [p for p in matches if target_lower in p.lower()]
        rest = [p for p in matches if p not in prioritized]
        matches = prioritized + rest

    selected = matches[:3]

    results = []
    for path in selected:
        project_name = os.path.basename(os.path.dirname(path))
        first_line = read_first_line(path)
        status = first_line.lstrip("#").strip() if first_line else "(no summary)"
        results.append((project_name, status))

    return results


def format_council_context(
    top_of_mind: list,
    project_summaries: list,
    session_context: list,
) -> str:
    """Formats all context as the council injection block."""
    if not top_of_mind and not project_summaries and not session_context:
        return ""

    lines = []
    lines.append("=== Council Context Injection ===")
    lines.append("User: Bobby Hansen Jr.")

    if top_of_mind:
        lines.append("Current focus: " + top_of_mind[0])
        for extra in top_of_mind[1:]:
            lines.append("               " + extra)
    else:
        lines.append("Current focus: (not available)")

    if project_summaries:
        lines.append("Active projects:")
        for name, status in project_summaries:
            lines.append(f"  - {name}: {status}")
    else:
        lines.append("Active projects: (none found)")

    if session_context:
        lines.append("Session context: " + session_context[0])
        for extra in session_context[1:]:
            lines.append("                " + extra)
    else:
        lines.append("Session context: (not available)")

    lines.append("=================================")
    return "\n".join(lines)


def format_preview(
    top_of_mind: list,
    project_summaries: list,
    session_context: list,
    clawd_dir: str,
) -> str:
    """Human-readable preview of what was found, without council formatting."""
    parts = []

    tom_path = os.path.join(clawd_dir, "life", "areas", "bobby", "top-of-mind.md")
    if top_of_mind:
        parts.append(f"top-of-mind.md ({tom_path}):")
        for line in top_of_mind:
            parts.append(f"  {line}")
    else:
        parts.append(f"top-of-mind.md: NOT FOUND ({tom_path})")

    cp_path = os.path.join(clawd_dir, "memory", "session-checkpoint.md")
    if session_context:
        parts.append(f"\nsession-checkpoint.md ({cp_path}):")
        for line in session_context:
            parts.append(f"  {line}")
    else:
        parts.append(f"\nsession-checkpoint.md: NOT FOUND ({cp_path})")

    if project_summaries:
        parts.append(f"\nproject summaries (up to 3 most recent):")
        for name, status in project_summaries:
            parts.append(f"  [{name}] {status}")
    else:
        proj_pattern = os.path.join(clawd_dir, "life", "projects", "*", "summary.md")
        parts.append(f"\nproject summaries: NONE FOUND (pattern: {proj_pattern})")

    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(
        description="Inject project memory context into council sessions."
    )
    parser.add_argument(
        "--project",
        default="",
        help="Target project name (optional; auto-detected if omitted)",
    )
    parser.add_argument(
        "--clawd-dir",
        default=DEFAULT_CLAWD_DIR,
        dest="clawd_dir",
        help="Path to the clawd directory (default: ~/clawd)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print what was found without council formatting",
    )
    args = parser.parse_args()

    clawd_dir = os.path.expanduser(args.clawd_dir)

    top_of_mind = get_top_of_mind(clawd_dir)
    session_context = get_session_checkpoint(clawd_dir)
    project_summaries = get_project_summaries(clawd_dir, args.project)

    if args.preview:
        output = format_preview(top_of_mind, project_summaries, session_context, clawd_dir)
    else:
        output = format_council_context(top_of_mind, project_summaries, session_context)

    if output:
        print(output)


if __name__ == "__main__":
    main()
