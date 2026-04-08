#!/usr/bin/env bash
# hermes-council install script
# Copies the council skill to ~/.hermes/skills/council/

set -e

SKILL_DIR="$HOME/.hermes/skills/council"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing hermes-council skill..."

# Create skill directory
mkdir -p "$SKILL_DIR/references/personas"

# Copy SKILL.md
cp "$SCRIPT_DIR/skills/council/SKILL.md" "$SKILL_DIR/SKILL.md"

# Copy persona reference files
cp "$SCRIPT_DIR/skills/council/references/personas/"*.md "$SKILL_DIR/references/personas/"

echo ""
echo "Council of High Intelligence installed to $SKILL_DIR"
echo ""
echo "Usage in any Hermes session:"
echo "  /council Should we open-source our agent framework?"
echo "  /council --deep What is the right architecture for our AI stack?"
echo ""
echo "18 council members ready. Deliberate wisely."
