#!/bin/bash
# Optional local Chinese ASR; no cloud inference or user audio upload.
set -euo pipefail
cd "$(dirname "$0")/.."
.runtime/voice-venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
from pathlib import Path
import json, shutil
repo='mlx-community/Qwen3-ASR-0.6B-4bit'
revision='313d850181767edf09f00a9c289becca70e58cd0'
snapshot_download(repo, revision=revision, local_dir='.runtime/qwen3-asr')
Path('.runtime/qwen3-asr-source.json').write_text(json.dumps({'repo':repo,'revision':revision}))
shutil.copy2('config/local-asr.json', '.runtime/asr-profile.json')
PY
cp scripts/local_speech.py .runtime/local_speech.py
echo '中日英语音识别统一为 Qwen3-ASR。重新启动应用生效。'
