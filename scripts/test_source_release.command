#!/bin/bash
# Source-only gate: no downloads, microphone or model inference.
set -euo pipefail
export RYZA_SOURCE_ONLY=1
cd "$(dirname "$0")/.."
for suite in dialogue_reliability bilingual_speech local_voice_profiles mac_local longterm save_slot game_logic memory voice speech_queue stt transport_error sitting electron_storage proxy_target nsfw_intent; do
  node "scripts/${suite}_regression.js"
done
node scripts/layering_check.js
python3 scripts/privacy_check.py web
python3 scripts/check_readme_translations.py
