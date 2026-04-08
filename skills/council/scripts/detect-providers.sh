#!/usr/bin/env bash
# council/scripts/detect-providers.sh
# Detects which LLM providers are available and outputs a JSON routing table.
# Run before any council session to determine provider spread.
#
# Output: JSON with available providers, their models, and member assignments.

set -e

PROVIDERS=()
PROVIDER_JSON=""

# --- Detect Anthropic ---
if [ -n "$ANTHROPIC_API_KEY" ]; then
  PROVIDERS+=("anthropic")
  ANTHROPIC_MODELS='["claude-opus-4-5","claude-sonnet-4-5"]'
else
  ANTHROPIC_MODELS="null"
fi

# --- Detect OpenAI ---
if [ -n "$OPENAI_API_KEY" ]; then
  PROVIDERS+=("openai")
  OPENAI_MODELS='["gpt-4o","gpt-4o-mini"]'
else
  OPENAI_MODELS="null"
fi

# --- Detect OpenRouter ---
if [ -n "$OPENROUTER_API_KEY" ]; then
  PROVIDERS+=("openrouter")
  OPENROUTER_MODELS='["anthropic/claude-opus-4-5","openai/gpt-4o","google/gemini-pro-1.5","meta-llama/llama-3.3-70b-instruct"]'
else
  OPENROUTER_MODELS="null"
fi

# --- Detect Gemini ---
if [ -n "$GEMINI_API_KEY" ]; then
  PROVIDERS+=("gemini")
  GEMINI_MODELS='["gemini-1.5-pro","gemini-1.5-flash"]'
else
  GEMINI_MODELS="null"
fi

# --- Detect Ollama (local) ---
if command -v ollama &>/dev/null && curl -s http://localhost:11434/api/tags &>/dev/null; then
  OLLAMA_MODELS_RAW=$(curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
print(json.dumps(models))
" 2>/dev/null || echo "[]")
  if [ "$OLLAMA_MODELS_RAW" != "[]" ]; then
    PROVIDERS+=("ollama")
    OLLAMA_MODELS="$OLLAMA_MODELS_RAW"
  else
    OLLAMA_MODELS="null"
  fi
else
  OLLAMA_MODELS="null"
fi

PROVIDER_COUNT=${#PROVIDERS[@]}

# --- Output JSON ---
cat <<EOF
{
  "provider_count": $PROVIDER_COUNT,
  "providers": $(printf '%s\n' "${PROVIDERS[@]}" | python3 -c "import sys,json; print(json.dumps([l.strip() for l in sys.stdin]))"),
  "models": {
    "anthropic": $ANTHROPIC_MODELS,
    "openai": $OPENAI_MODELS,
    "openrouter": $OPENROUTER_MODELS,
    "gemini": $GEMINI_MODELS,
    "ollama": $OLLAMA_MODELS
  }
}
EOF
