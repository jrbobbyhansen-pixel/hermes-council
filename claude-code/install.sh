#!/usr/bin/env bash
# hermes-council Claude Code install script
# Installs the council skill to ~/.claude/skills/council/

set -e

SKILL_DIR="$HOME/.claude/skills/council"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing council skill for Claude Code..."

mkdir -p "$SKILL_DIR/references/personas"
mkdir -p "$SKILL_DIR/scripts"

# Copy Claude Code adapted SKILL.md
cp "$SCRIPT_DIR/skills/council/SKILL.md" "$SKILL_DIR/SKILL.md"

# Copy shared assets from hermes skill
cp "$REPO_ROOT/skills/council/references/personas/"*.md "$SKILL_DIR/references/personas/"
cp "$REPO_ROOT/skills/council/references/provider-routing.md" "$SKILL_DIR/references/"
cp "$REPO_ROOT/skills/council/scripts/"*.py "$SKILL_DIR/scripts/"
cp "$REPO_ROOT/skills/council/scripts/"*.sh "$SKILL_DIR/scripts/"
chmod +x "$SKILL_DIR/scripts/"*.sh

# Update path references from hermes to claude
find "$SKILL_DIR/scripts" -type f | xargs sed -i '' 's|~/.hermes/|~/.claude/|g' 2>/dev/null || true

echo ""
echo "Council of High Intelligence installed to $SKILL_DIR"
echo ""
echo "22 council members ready. Single-provider mode uses Claude (claude-opus-4-6 for"
echo "dissenters, claude-sonnet-4-6 for builders). Multi-provider routing available"
echo "if additional API keys are configured in ~/.claude/.env"
echo ""
echo "Start a new Claude Code session and use:"
echo "  /council Should we open-source our agent framework?"
echo "  /council --deep What is the right architecture for our AI stack?"
