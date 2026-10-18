#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ -d output/desktop/mac-arm64/RyzaChat.app ]; then
  open output/desktop/mac-arm64/RyzaChat.app
else
  cp scripts/local_speech.py .runtime/local_speech.py
  cd desktop
  npm start
fi
