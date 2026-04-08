#!/usr/bin/env python3
"""
research-brief.py — Gathers grounding research for a council member before Round 1 analysis.

Usage:
    python3 research-brief.py --member feynman --question "Is Rust worth adopting?" --domain engineering
    python3 research-brief.py --member taleb --question "Should we expand?" --dry-run
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from html.parser import HTMLParser


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


MEMBER_FIGURES = {
    'feynman': 'Richard Feynman', 'socrates': 'Socrates', 'ada': 'Ada Lovelace',
    'torvalds': 'Linus Torvalds', 'machiavelli': 'Machiavelli', 'watts': 'Alan Watts',
    'aristotle': 'Aristotle', 'sun-tzu': 'Sun Tzu', 'aurelius': 'Marcus Aurelius',
    'lao-tzu': 'Lao Tzu', 'musashi': 'Miyamoto Musashi', 'karpathy': 'Andrej Karpathy',
    'sutskever': 'Ilya Sutskever', 'kahneman': 'Daniel Kahneman', 'meadows': 'Donella Meadows',
    'munger': 'Charlie Munger', 'taleb': 'Nassim Taleb', 'rams': 'Dieter Rams',
    'jensen': 'Jensen Huang', 'bezos': 'Jeff Bezos', 'graham': 'Paul Graham',
    'diogenes': 'Diogenes',
}


# --- Domain-specific query modifiers per member ---

MEMBER_QUERY_SUFFIXES = {
    "feynman":     "technical analysis research 2024 2025",
    "ada":         "technical analysis research 2024 2025",
    "karpathy":    "technical analysis research 2024 2025",
    "sun-tzu":     "competitive landscape market analysis",
    "machiavelli": "competitive landscape market analysis",
    "torvalds":    "engineering implementation benchmarks",
    "kahneman":    "decision research behavioral economics",
    "munger":      "decision research behavioral economics",
    "taleb":       "risk analysis systems research",
    "meadows":     "risk analysis systems research",
}

# torvalds also gets technical suffix (listed under both)
MEMBER_QUERY_SUFFIXES["torvalds"] = "engineering implementation benchmarks"


def build_query(member: str, question: str, domain: str) -> str:
    suffix = MEMBER_QUERY_SUFFIXES.get(member.lower(), "")
    base = question.strip()
    if domain and domain.lower() not in base.lower():
        base = f"{base} {domain}"
    if suffix:
        return f"{base} {suffix}"
    return base


# --- DuckDuckGo HTML parser ---

class DDGResultParser(HTMLParser):
    """Parses DuckDuckGo HTML results page for result titles, snippets, and URLs."""

    def __init__(self):
        super().__init__()
        self.results = []
        self._in_result = False
        self._in_title = False
        self._in_snippet = False
        self._current = {}
        self._tag_stack = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        self._tag_stack.append(tag)

        # Result container: <div class="result results_links results_links_deep web-result ...">
        if tag == "div":
            classes = attrs_dict.get("class", "")
            if "result__body" in classes or "result results_links" in classes or "web-result" in classes:
                self._in_result = True
                self._current = {"title": "", "snippet": "", "url": ""}

        # Title link: <a class="result__a" href="...">
        if tag == "a" and "result__a" in attrs_dict.get("class", ""):
            href = attrs_dict.get("href", "")
            if href and self._current is not None:
                self._current["url"] = href
            self._in_title = True

        # Snippet: <a class="result__snippet">
        if tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
            self._in_snippet = True

    def handle_endtag(self, tag):
        if self._tag_stack:
            self._tag_stack.pop()

        if tag == "a":
            if self._in_title:
                self._in_title = False
            if self._in_snippet:
                self._in_snippet = False
                if self._current.get("title") and self._current.get("snippet"):
                    self.results.append(dict(self._current))
                    self._current = {"title": "", "snippet": "", "url": ""}
                self._in_result = False

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_title and self._current is not None:
            self._current["title"] += text
        if self._in_snippet and self._current is not None:
            self._current["snippet"] += text + " "


def search_duckduckgo(query: str, timeout: int = 10) -> list:
    """Fetch DuckDuckGo HTML results and return top results as list of dicts."""
    encoded = urllib.parse.urlencode({"q": query})
    url = f"https://html.duckduckgo.com/html/?{encoded}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    parser = DDGResultParser()
    parser.feed(html)
    return parser.results[:3]


# --- Brief synthesis ---

BRIEF_TEMPLATES = {
    "feynman": (
        "From a first-principles technical view, the research highlights {key_themes}. "
        "The evidence suggests {finding}. "
        "Understanding the underlying mechanisms matters more than surface-level adoption patterns."
    ),
    "ada": (
        "Analytically speaking, the data points to {key_themes}. "
        "Careful examination of {finding} provides a structured basis for reasoning forward. "
        "Precision in framing the problem is essential before drawing conclusions."
    ),
    "karpathy": (
        "The technical landscape around {key_themes} is evolving rapidly. "
        "Benchmarks and implementation details reveal {finding}. "
        "The engineering tradeoffs here deserve empirical scrutiny rather than hype-driven decisions."
    ),
    "sun-tzu": (
        "The competitive terrain shows {key_themes}. "
        "Strategic positioning depends on understanding {finding}. "
        "Know the field before committing to a course of action."
    ),
    "machiavelli": (
        "Power dynamics in this domain center on {key_themes}. "
        "Those who control {finding} hold the decisive advantage. "
        "Effective strategy requires clear eyes about interests, not ideals."
    ),
    "torvalds": (
        "The engineering reality of {key_themes} is blunt. "
        "Implementation benchmarks show {finding}. "
        "Pragmatic execution beats theoretical elegance every time."
    ),
    "kahneman": (
        "Behavioral and cognitive factors shape {key_themes} more than rational models predict. "
        "The research on {finding} reveals systematic biases at play. "
        "Decisions in this space require deliberate System 2 engagement."
    ),
    "munger": (
        "Mental models applied to {key_themes} suggest a clear pattern. "
        "The evidence around {finding} is consistent with what rational incentive structures predict. "
        "Invert, always invert — what would cause failure here?"
    ),
    "taleb": (
        "The tail risk in {key_themes} is underappreciated. "
        "Research on {finding} exposes fragilities that conventional analysis misses. "
        "Robustness to unknown unknowns should dominate this decision."
    ),
    "meadows": (
        "System dynamics underlying {key_themes} reveal feedback loops worth mapping. "
        "The research on {finding} points to leverage points that are often overlooked. "
        "Short-term fixes frequently create long-term systemic drift."
    ),
}

DEFAULT_BRIEF_TEMPLATE = (
    "Research on {key_themes} surfaces the following signal: {finding}. "
    "This context grounds the analysis in current evidence rather than assumption. "
    "Further synthesis may be required depending on domain depth."
)


def _template_brief(member: str, sources: list) -> str:
    """Fallback: fill the static template from search result titles/snippets."""
    if not sources:
        return "No research sources were retrieved. Analysis will proceed from first principles."
    titles = [s["title"] for s in sources if s.get("title")]
    snippets = [s["snippet"] for s in sources if s.get("snippet")]
    key_themes = titles[0] if titles else "the queried topic"
    finding = snippets[0][:120].rstrip() + "..." if snippets else "mixed signals across sources"
    template = BRIEF_TEMPLATES.get(member.lower(), DEFAULT_BRIEF_TEMPLATE)
    return template.format(key_themes=key_themes, finding=finding)


def synthesize_brief(member: str, domain: str, question: str, sources: list) -> str:
    """Call LLM to generate a brief in the member's voice. Falls back to template on failure."""
    figure_name = MEMBER_FIGURES.get(member.lower(), member.title())
    formatted_sources = ""
    for i, s in enumerate(sources, 1):
        title = s.get("title", "")
        snippet = s.get("snippet", "").strip()
        formatted_sources += f"{i}. {title}\n   {snippet}\n\n"

    if not formatted_sources:
        formatted_sources = "No search results available."

    prompt = (
        f"You are {figure_name}. Based on these search results about \"{question}\", "
        f"write a 2-3 sentence research brief in your voice that will ground your analysis. "
        f"Focus on what is most relevant to your domain ({domain}). "
        f"Be specific and cite what you found.\n\n"
        f"Search results:\n{formatted_sources}\n"
        f"Brief (2-3 sentences, in your analytical voice):"
    )

    try:
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
                "max_tokens": 256,
                "messages": [{"role": "user", "content": prompt}],
            }
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(), headers=headers
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["content"][0]["text"].strip()

        xai_key = os.environ.get("XAI_API_KEY")
        if xai_key:
            url = "https://api.x.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {xai_key}",
                "content-type": "application/json",
            }
            payload = {
                "model": "grok-beta",
                "max_tokens": 256,
                "messages": [{"role": "user", "content": prompt}],
            }
            req = urllib.request.Request(
                url, data=json.dumps(payload).encode(), headers=headers
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return _template_brief(member, sources)


# --- Dry-run mock data ---

def dry_run_result(member: str, query: str) -> dict:
    return {
        "member": member,
        "query": query,
        "sources": [
            {
                "title": "[DRY RUN] Sample Research Result 1",
                "snippet": "This is a mock snippet representing what a real search result would contain. It covers the topic broadly.",
                "url": "https://example.com/result1",
            },
            {
                "title": "[DRY RUN] Sample Research Result 2",
                "snippet": "A second mock result offering a contrasting perspective or additional data point on the question.",
                "url": "https://example.com/result2",
            },
            {
                "title": "[DRY RUN] Sample Research Result 3",
                "snippet": "Third mock result with supporting evidence, often where nuance or caveats tend to appear.",
                "url": "https://example.com/result3",
            },
        ],
        "brief": f"[DRY RUN] This is a synthesized brief written from {member}'s perspective based on mock research data. The query was: '{query}'. In a real run, this would reflect actual search results.",
    }


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Gather grounding research for a council member.")
    parser.add_argument("--member", required=True, help="Council member name (e.g. feynman, taleb)")
    parser.add_argument("--question", required=True, help="The question being researched")
    parser.add_argument("--domain", default="", help="Optional domain context (e.g. engineering, strategy)")
    parser.add_argument("--dry-run", action="store_true", help="Return mock data without hitting the network")
    args = parser.parse_args()

    load_dotenv('~/.hermes/.env')

    query = build_query(args.member, args.question, args.domain)

    if args.dry_run:
        result = dry_run_result(args.member, query)
        print(json.dumps(result, indent=2))
        return

    try:
        sources = search_duckduckgo(query, timeout=10)
    except Exception:
        sources = []

    brief = synthesize_brief(args.member, args.domain, args.question, sources)

    result = {
        "member": args.member,
        "query": query,
        "sources": sources,
        "brief": brief,
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
