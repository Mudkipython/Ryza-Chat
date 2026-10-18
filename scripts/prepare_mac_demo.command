#!/bin/bash
# Rebuild the local demo environment; downloads need internet only during setup.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ "$(uname -m)" != arm64 ]; then echo '此试玩版面向 Apple Silicon Mac。'; exit 1; fi
command -v uv >/dev/null || { echo '请先安装 uv：https://docs.astral.sh/uv/'; exit 1; }
command -v npm >/dev/null || { echo '请先安装 Node.js。'; exit 1; }
WITH_KOKORO=0
case "${1:-}" in
  '') ;;
  --with-kokoro) WITH_KOKORO=1 ;;
  *) echo '用法：prepare_mac_demo.command [--with-kokoro]'; exit 1 ;;
esac
export RYZA_WITH_KOKORO="$WITH_KOKORO"
mkdir -p .runtime
uv venv --python 3.12 --allow-existing .runtime/voice-venv
uv pip install --python .runtime/voice-venv/bin/python 'mlx-audio==0.5.9' 'misaki[zh]' soundfile
.runtime/voice-venv/bin/python scripts/local_model_resources.py --download
HF_HOME="$PWD/.runtime/huggingface" .runtime/voice-venv/bin/python - <<'PY'
import os
from huggingface_hub import snapshot_download
if os.environ.get('RYZA_WITH_KOKORO') == '1':
    snapshot_download('mlx-community/Kokoro-82M-bf16', local_dir='.runtime/kokoro',
                      allow_patterns=['config.json','*.safetensors','voices/zf_*.safetensors','README.md','LICENSE*'])
snapshot_download('mlx-community/Qwen3-TTS-12Hz-1.7B-Base-4bit',
  revision='37e955a1deb861c088ae5f3a67043185f3d1a60c', local_dir='.runtime/qwen3-tts')
PY
scripts/prepare_qwen_asr.command
if [ -z "$(find web/assets -name '*.skel' -print -quit)" ]; then
  curl -fL --retry 3 -C - https://github.com/zeroa234/ryza-ai-revive/releases/download/v1.2.23/RyzaChat-1.2.23.apk -o .runtime/RyzaChat-1.2.23.apk
  .runtime/voice-venv/bin/python scripts/restore_media.py .runtime/RyzaChat-1.2.23.apk
fi
.runtime/voice-venv/bin/python - <<'PYREF'
import json, shutil
from pathlib import Path
ref=json.loads(Path('config/ryza-voice-reference.json').read_text())
shutil.copy2(ref['source'], '.runtime/ryza-reference.wav')
Path('.runtime/ryza-reference.txt').write_text(ref['transcript'])
PYREF
cp scripts/local_speech.py .runtime/local_speech.py
(cd desktop && npm ci && node node_modules/electron/install.js)
echo '准备完成。请运行 scripts/build_mac_demo.command，然后双击 scripts/start_mac_demo.command。'
