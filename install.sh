#!/usr/bin/env bash
# hermes-council install script
# Copies the full council skill to ~/.hermes/skills/council/

set -e

SKILL_DIR="$HOME/.hermes/skills/council"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing hermes-council skill..."

# Create all directories
mkdir -p "$SKILL_DIR/references/personas"
mkdir -p "$SKILL_DIR/scripts"
mkdir -p "$SKILL_DIR/data"

# Copy SKILL.md
cp "$SCRIPT_DIR/skills/council/SKILL.md" "$SKILL_DIR/SKILL.md"

# Copy persona reference files
cp "$SCRIPT_DIR/skills/council/references/personas/"*.md "$SKILL_DIR/references/personas/"

# Copy routing config
cp "$SCRIPT_DIR/skills/council/references/provider-routing.md" "$SKILL_DIR/references/"

# Copy all scripts
cp "$SCRIPT_DIR/skills/council/scripts/"*.py "$SKILL_DIR/scripts/"
cp "$SCRIPT_DIR/skills/council/scripts/"*.sh "$SKILL_DIR/scripts/"
chmod +x "$SKILL_DIR/scripts/"*.sh

echo ""
echo "Council of High Intelligence installed to $SKILL_DIR"
echo ""
echo "Providers supported: anthropic, xai (grok), openai, openrouter, gemini, ollama"
echo "Credentials are loaded from ~/.hermes/.env automatically."
echo ""
echo "Usage in any Hermes session:"
echo "  /council Should we open-source our agent framework?"
echo "  /council --deep What is the right architecture for our AI stack?"
echo ""
echo "22 council members ready. Deliberate wisely."
