#!/bin/bash
set -euo pipefail

JARVIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source "$JARVIS_DIR/venv/bin/activate"

cd "$JARVIS_DIR"

python briefing_pi.py >> "$JARVIS_DIR/briefing.log" 2>&1
