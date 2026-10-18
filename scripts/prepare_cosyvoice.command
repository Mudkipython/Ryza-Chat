#!/bin/bash
# Optional Chinese expressive speech, isolated from the Qwen environment.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
[ "$(uname -m)" = arm64 ] || { echo '仅支持 Apple Silicon。'; exit 1; }
command -v uv >/dev/null || { echo '请先安装 uv。'; exit 1; }
[ -f .runtime/ryza-reference.wav ] || { echo '请先完成 prepare_mac_demo.command。'; exit 1; }
uv venv --python 3.12 --allow-existing .runtime/cosyvoice-venv
uv pip install --python .runtime/cosyvoice-venv/bin/python -r config/cosyvoice-trial-requirements.txt
HF_HOME="$PWD/.runtime/cosyvoice-cache" .runtime/cosyvoice-venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download('mlx-community/Fun-CosyVoice3-0.5B-2512-4bit',
    revision='55a6713d54751f1ec2645aa11294676f2067202a', local_dir='.runtime/cosyvoice3-4bit')
snapshot_download('mlx-community/S3TokenizerV3',
    revision='b143914b3e912278104824da706edc9c2d317c4e', local_dir='.runtime/cosyvoice-s3')
PY
cp scripts/cosyvoice_speech.py .runtime/cosyvoice_speech.py
echo 'CosyVoice 中文实验音色已准备。重新启动应用后在设置中选择。'
