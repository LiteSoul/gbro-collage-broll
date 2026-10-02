#!/usr/bin/env bash
# gbro-collage-broll environment self-check.
# Exit 0 = all good; exit 1 = at least one item missing (details on stdout).

set -u

MODE="manual"
for arg in "$@"; do
  case "$arg" in
    --mode=api|--api) MODE="api" ;;
    --mode=manual|--manual) MODE="manual" ;;
  esac
done

VENV_PY="$HOME/hyperframes-projects/.omni-venv/bin/python"
FAIL=0

ok()   { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; FAIL=1; }
info() { printf 'INFO  %s\n' "$1"; }

printf '=== gbro-collage-broll Environment Check [Mode: %s] ===\n' "$(echo "$MODE" | tr '[:lower:]' '[:upper:]')"

# 1. ffmpeg / ffprobe
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  ok "ffmpeg / ffprobe available (used for frame scaling, background generation, audio stripping, QA sheets)"
else
  bad "ffmpeg / ffprobe missing (macOS: brew install ffmpeg; Ubuntu: sudo apt install ffmpeg; Windows: winget install Gyan.FFmpeg)"
fi

# 2. Python >= 3.10
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  ok "python3 >= 3.10"
elif command -v python >/dev/null 2>&1 && python -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
  ok "python >= 3.10"
else
  bad "Python missing or version is lower than 3.10"
fi

# 3. Mode-specific check
if [ "$MODE" = "api" ]; then
  if [ -n "${GEMINI_API_KEY:-}" ]; then
    ok "GEMINI_API_KEY configured"
  else
    bad "GEMINI_API_KEY is not set (Create one at https://aistudio.google.com/apikey)"
  fi

  if [ -x "$VENV_PY" ] && "$VENV_PY" - <<'PY' 2>/dev/null
import sys
from google import genai
parts = [int(x) for x in genai.__version__.split(".")[:2]]
sys.exit(0 if parts >= [2, 10] else 1)
PY
  then
    ok "Shared venv ready (google-genai >= 2.10.0)"
  else
    bad "Shared venv missing or google-genai is outdated (Run: python3 -m venv ~/hyperframes-projects/.omni-venv && ~/hyperframes-projects/.omni-venv/bin/python -m pip install --upgrade 'google-genai>=2.10.0')"
  fi
else
  if [ -n "${GEMINI_API_KEY:-}" ]; then
    info "GEMINI_API_KEY detected (optional in manual mode)"
  else
    ok "Manual Mode active (No API key required! Prompts and keyframes will be written to file)"
  fi
fi

exit $FAIL
