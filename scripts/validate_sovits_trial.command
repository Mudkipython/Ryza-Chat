#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
.runtime/sovits-venv/bin/python scripts/sovits_speech.py --root .runtime --language zh --text '你回来了！今天想和我一起去冒险吗？' --output output/ryza-sovits-chinese.wav
.runtime/sovits-venv/bin/python scripts/sovits_speech.py --root .runtime --language ja --text 'おかえり！今日は一緒に冒険に行こうよ。' --output output/ryza-sovits-japanese.wav
# This prints recognition evidence only. Listen to both files before adopting
# the timbre; matching ASR text alone cannot establish voice quality.
.runtime/voice-venv/bin/python - <<'PY'
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('service','scripts/local_speech.py')
service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
service.ROOT=Path('.runtime').resolve()
for lang,name in [('zh','chinese'),('ja','japanese')]:
    print(name+': '+service.transcribe(Path('output/ryza-sovits-'+name+'.wav').read_bytes(),lang))
PY
