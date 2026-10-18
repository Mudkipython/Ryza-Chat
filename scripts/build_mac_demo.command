#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PYTHON=".runtime/voice-venv/bin/python"
if [ ! -x "$PYTHON" ]; then
  echo '缺少本地运行环境，请先运行 scripts/prepare_mac_demo.command。'; exit 1
fi
"$PYTHON" scripts/local_model_resources.py --check
"$PYTHON" - <<'PY'
from pathlib import Path
root=Path('.')
for required in ['qwen3-tts/model.safetensors','qwen3-tts/speech_tokenizer/model.safetensors','qwen3-asr/model.safetensors','asr-profile.json','ryza-reference.wav','ryza-reference.txt']:
    if not (root/'.runtime'/required).is_file(): raise SystemExit('缺少本地语音资源：'+required)
if not list((root/'web/assets').rglob('*.skel')):
    raise SystemExit('缺少角色动画，请先恢复发行包媒体。')
PY
cp scripts/local_speech.py .runtime/local_speech.py
cp scripts/sovits_speech.py .runtime/sovits_speech.py
cp scripts/cosyvoice_speech.py .runtime/cosyvoice_speech.py
"$PYTHON" scripts/privacy_check.py web
cd desktop
CSC_IDENTITY_AUTO_DISCOVERY=false npm run dist:mac
cd ..
# A relative link keeps this local demo relocatable together with its project.
ln -sfn ../../../.runtime output/desktop/mac-arm64/local-runtime
printf '\n试玩应用：%s/output/desktop/mac-arm64/RyzaChat.app\n' "$PWD"
