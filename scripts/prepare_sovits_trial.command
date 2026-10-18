#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [ ! -d .runtime/gpt-sovits ]; then
  git clone https://github.com/RVC-Boss/GPT-SoVITS.git .runtime/gpt-sovits
  git -C .runtime/gpt-sovits checkout 1b47ca07ef43a284e0b8bd7f29d3e1e3ff76082a
fi
if [ ! -x .runtime/sovits-venv/bin/python ]; then uv venv --python 3.11 .runtime/sovits-venv; fi
uv pip install --python .runtime/sovits-venv/bin/python -r config/sovits-trial-requirements.txt
.runtime/voice-venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download, hf_hub_download
from pathlib import Path
import zipfile
snapshot_download('lj1995/GPT-SoVITS',revision='8f8857563c040d542de108a2c18b0425abd6c9c5',local_dir='.runtime/gpt-sovits/GPT_SoVITS/pretrained_models',allow_patterns=['s1v3.ckpt','v2Pro/s2Gv2ProPlus.pth','sv/*','chinese-hubert-base/*','chinese-roberta-wwm-ext-large/*'],max_workers=3)
resources = {
    'G2PWModel.zip': Path('.runtime/gpt-sovits/GPT_SoVITS/text/G2PWModel/g2pW.onnx'),
    'nltk_data.zip': Path('.runtime/gpt-sovits/nltk_data/taggers'),
    'open_jtalk_dic_utf_8-1.11.tar.gz': Path('.runtime/sovits-downloads/open_jtalk_dic_utf_8-1.11/sys.dic'),
}
for name, installed in resources.items():
    if installed.exists():
        continue
    p=hf_hub_download('XXXXRT/GPT-SoVITS-Pretrained',name,revision='0c47645e02a7bc3688d7b263b0042c81e3cd82cd',local_dir='.runtime/sovits-downloads')
    if name=='G2PWModel.zip':
        with zipfile.ZipFile(p) as z:z.extractall('.runtime/gpt-sovits/GPT_SoVITS/text')
    if name=='nltk_data.zip':
        with zipfile.ZipFile(p) as z:z.extractall('.runtime/gpt-sovits')
PY
.runtime/sovits-venv/bin/python - <<'PY'
from pathlib import Path
from urllib.request import urlretrieve
import hashlib
p=Path('.runtime/gpt-sovits/GPT_SoVITS/pretrained_models/fast_langdetect/lid.176.bin')
p.parent.mkdir(parents=True,exist_ok=True)
if not p.is_file():
    tmp=p.with_suffix('.download')
    urlretrieve('https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin',tmp)
    if hashlib.md5(tmp.read_bytes()).hexdigest()!='01810bc59c6a3d2b79c79e6336612f65':
        raise SystemExit('语言模型校验失败')
    tmp.replace(p)
PY
cp web/assets/voice/ryza_wav/prologue_01.wav .runtime/sovits-reference-01.wav
printf '%s' 'これは、ライザの夢の世界。あなたと作る、一夏の物語。' > .runtime/sovits-reference-01.txt
cp scripts/sovits_speech.py .runtime/sovits_speech.py
printf '\n已准备独立 GPT-SoVITS 对照环境；需完成中文/日语样音验证后才能启用。\n'
