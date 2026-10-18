#!/usr/bin/env python3
"""Standalone CosyVoice3 MLX trial. Generate in cosyvoice-venv; analyze in voice-venv."""
import argparse
import json
import math
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/cosyvoice3-trial'
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
os.environ.setdefault('HF_HOME', str(ROOT / '.runtime/cosyvoice-cache'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.runtime/cache/matplotlib'))
SAMPLES = [
    ('ja', 'Japanese', '私はライザ。錬金術で、新しい道具を作るのが大好きなんだ。', True),
    ('zh-cross', 'Chinese', '我是莱莎，最喜欢用炼金术制作新的道具。明天一起去山里采药吧！', False),
    ('zh-transcript', 'Chinese', '我是莱莎，最喜欢用炼金术制作新的道具。明天一起去山里采药吧！', True),
]
INSTRUCTIONS = {}


def generate():
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from mlx_audio.tts.utils import load_model
    from mlx_audio.codec.models.s3tokenizer import S3TokenizerV3

    OUT.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    model = load_model(ROOT / '.runtime/cosyvoice3-4bit')
    # This upstream helper only accepts Hub IDs; load the pinned local weights
    # through the same constructor/load_weights path to keep the trial offline.
    model._s3_tokenizer = S3TokenizerV3('speech_tokenizer_v3')
    s3_weights = mx.load(str(ROOT / '.runtime/cosyvoice-s3/model.safetensors'))
    model._s3_tokenizer.load_weights(list(s3_weights.items()))
    mx.eval(model._s3_tokenizer.parameters())
    del s3_weights
    model._ensure_model_loaded()
    model._ensure_tokenizers_loaded()
    loaded = time.monotonic() - started
    audio, rate = sf.read(ROOT / '.runtime/ryza-reference.wav', dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    divisor = math.gcd(rate, model.sample_rate)
    reference = mx.array(resample_poly(audio, model.sample_rate // divisor, rate // divisor))
    transcript = (ROOT / '.runtime/ryza-reference.txt').read_text().strip()
    report = {'model': json.loads((ROOT / '.runtime/cosyvoice3-4bit/trial-revision.json').read_text()),
              'tokenizer': json.loads((ROOT / '.runtime/cosyvoice-s3/trial-revision.json').read_text()),
              'source_commit': '4c9ec6a8489e790b5ba8964ab1f1d63150476f9f',
              'load_seconds': loaded, 'reference_seconds': len(reference) / model.sample_rate,
              'reference_text': transcript, 'stream': False, 'seed': 42, 'samples': []}
    print('Loaded model and reference components', round(loaded, 3), flush=True)
    for label, _, text, with_transcript in SAMPLES:
        started = time.monotonic()
        chunks = []
        for result in model.generate(text=text, ref_audio=reference,
                                     ref_text=transcript if with_transcript else None,
                                     seed=42, max_tokens=512, stream=False,
                                     instruct_text=INSTRUCTIONS.get(label)):
            mx.eval(result.audio)
            chunks.append(np.asarray(result.audio).reshape(-1))
        elapsed = time.monotonic() - started
        waveform = np.concatenate(chunks)
        assert waveform.size and np.isfinite(waveform).all(), 'Invalid audio'
        sf.write(OUT / f'{label}.wav', waveform, model.sample_rate)
        row = {'label': label, 'text': text, 'reference_transcript': with_transcript,
               'instruction': INSTRUCTIONS.get(label),
               'file': f'{label}.wav', 'seconds': elapsed,
               'duration': len(waveform) / model.sample_rate,
               'peak_mlx_gb': mx.get_peak_memory() / 1e9,
               'max_amplitude': float(np.max(np.abs(waveform)))}
        row['rtf'] = elapsed / row['duration']
        report['samples'].append(row)
        (OUT / 'generation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(json.dumps(row, ensure_ascii=False), flush=True)


def analyze():
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from mlx_audio.stt.utils import load_model
    model = load_model(str(ROOT / '.runtime/qwen3-asr'))
    rows = []
    for label, language, text, _ in SAMPLES:
        audio, rate = sf.read(OUT / f'{label}.wav', dtype='float32')
        divisor = math.gcd(rate, 16000)
        audio = resample_poly(audio, 16000 // divisor, rate // divisor).astype('float32')
        result = model.generate(audio, language=language, max_tokens=256, temperature=0.0)
        rows.append({'label': label, 'expected': text, 'asr': result.text, 'hotwords': False})
    (OUT / 'recognition.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(json.dumps(rows, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analyze', action='store_true')
    args = parser.parse_args()
    analyze() if args.analyze else generate()
