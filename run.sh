#!/usr/bin/env bash
cd "$(dirname "$0")"
[ -d .venv ] || { python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt; }
. .venv/bin/activate
export LLM_PROVIDER=openai LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/ LLM_MODEL=gemini-flash-latest
[ -f key.txt ] || { read -rp "Ключ Gemini API: " k; echo "$k" > key.txt; }
export LLM_API_KEY="$(cat key.txt)"
python -m web.app
