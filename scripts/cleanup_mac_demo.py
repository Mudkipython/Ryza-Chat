#!/usr/bin/env python3
"""Remove only redundant installation archives after checking extracted resources."""
import argparse
import json
import shutil
from local_model_resources import check_model
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / '.runtime'
ARCHIVES = {
    'sovits-downloads/G2PWModel.zip': ['gpt-sovits/GPT_SoVITS/text/G2PWModel/g2pW.onnx'],
    'sovits-downloads/nltk_data.zip': ['gpt-sovits/nltk_data/corpora', 'gpt-sovits/nltk_data/taggers'],
    'sovits-downloads/open_jtalk_dic_utf_8-1.11.tar.gz': ['sovits-downloads/open_jtalk_dic_utf_8-1.11/sys.dic'],
    'llama.tar.gz': ['llama/llama-b11712/llama-server'],
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='delete verified redundant archives; default is preview')
    parser.add_argument('--obsolete', action='store_true', help='also remove retired 8B, Whisper, Kokoro and unused old venv after checking replacement resources')
    args = parser.parse_args()
    total = 0
    for archive, extracted in ARCHIVES.items():
        source = ROOT / archive
        if source.is_symlink() or not source.is_file():
            continue
        if not all((ROOT / name).exists() for name in extracted):
            print('Keep (extracted resource missing):', archive)
            continue
        total += source.stat().st_size
        print('Remove:' if args.apply else 'Would remove:', archive)
        if args.apply:
            source.unlink()
    print(('Freed' if args.apply else 'Reclaimable') + f': {total / 1024**2:.1f} MiB')

    if args.obsolete:
        check_model(ROOT.parent)
        profile=json.loads((ROOT/'asr-profile.json').read_text())
        if profile.get('engine') != 'qwen3' or profile.get('languages') or not (ROOT/'qwen3-asr/model.safetensors').is_file():
            raise SystemExit('Unified Qwen3-ASR must be ready before removing retired components.')
        for name in ['venv', 'whisper-small', 'kokoro', 'models/Qwen3-8B-Q4_K_M.gguf']:
            source=ROOT/name
            if source.is_symlink() or not source.exists():continue
            print('Remove retired:' if args.apply else 'Would remove retired:', name)
            if args.apply:
                if source.is_dir():shutil.rmtree(source)
                else:source.unlink()
