#!/usr/bin/env python3
"""Optional isolated Chinese CosyVoice MLX worker. No training or downloads."""
import argparse
import io
import json
import math
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HAPPY = '请用中文说话。语气开心、亲切，像和朋友分享好消息，重音和语调自然起伏，不要夸张。'
GENTLE = '请用中文说话。语气温柔、关切，放慢一点，像在安慰朋友，句尾轻柔。'


def instruction(emotion='', mode='chat', strength='standard'):
    if strength not in {'gentle', 'standard', 'expressive'}:
        raise ValueError('Unknown emotion strength')
    suffix = {'gentle': '情感表达克制，只保留轻微的重音和句尾起伏。',
              'expressive': '让重音、停顿和句尾语调更有变化，但保持同一音色，不要喊叫。',
              'standard': ''}[strength]
    if mode == 'asmr':
        return '请用中文说话。轻声、温柔地说，像在身边陪伴朋友，保留清楚发音，不要夸张。' + suffix
    if emotion in {'sad', 'crying', 'shy', 'cuddle'}:
        return GENTLE + suffix
    if emotion in {'happy', 'laughing', 'tease'}:
        return HAPPY + suffix
    return None  # Neutral keeps the validated audio-only cross-lingual mode.


def load_engine(root):
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
    import mlx.core as mx
    import soundfile as sf
    from scipy.signal import resample_poly
    from mlx_audio.tts.utils import load_model
    from mlx_audio.codec.models.s3tokenizer import S3TokenizerV3
    model = load_model(root / 'cosyvoice3-4bit')
    tokenizer = S3TokenizerV3('speech_tokenizer_v3')
    tokenizer.load_weights(list(mx.load(str(root / 'cosyvoice-s3/model.safetensors')).items()))
    mx.eval(tokenizer.parameters())
    model._s3_tokenizer = tokenizer
    model._ensure_model_loaded()
    model._ensure_tokenizers_loaded()
    audio, rate = sf.read(root / 'ryza-reference.wav', dtype='float32')
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    divisor = math.gcd(rate, model.sample_rate)
    reference = mx.array(resample_poly(audio, model.sample_rate // divisor, rate // divisor))
    return model, reference


def encode_audio(parts, rate):
    import numpy as np
    import soundfile as sf
    audio = np.concatenate(parts).reshape(-1)
    if not audio.size or not np.isfinite(audio).all():
        raise ValueError('Invalid generated audio')
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if peak < 1e-5 or rms < 1e-6:
        raise ValueError('Generated audio is silent')
    # One gain per utterance retains its expressive envelope; never compress
    # individual syllables. Limit boosts to 3dB and leave 1dB peak headroom.
    gain = min(10 ** (-22 / 20) / rms, 10 ** (3 / 20), 10 ** (-1 / 20) / peak)
    buf = io.BytesIO()
    sf.write(buf, audio * gain, rate, format='WAV', subtype='PCM_16')
    return buf.getvalue()


def synthesize(engine, text, emotion='', mode='chat', strength='standard'):
    import mlx.core as mx
    import numpy as np
    model, reference = engine
    parts = []
    for result in model.generate(text=text, ref_audio=reference, ref_text=None,
                                 instruct_text=instruction(emotion, mode, strength), seed=42,
                                 max_tokens=512, stream=False):
        mx.eval(result.audio)
        parts.append(np.asarray(result.audio))
    if not parts:
        raise ValueError('No audio generated')
    return encode_audio(parts, model.sample_rate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    engine = None
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, code, body, kind='application/json'):
            self.send_response(code)
            self.send_header('Content-Type', kind)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            self.reply(200 if self.path == '/health' else 404,
                       json.dumps({'ready': True, 'engine_loaded': engine is not None}).encode())

        def do_POST(self):
            nonlocal engine
            if self.path != '/v1/audio/speech':
                return self.reply(404, b'{}')
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 16000:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(size))
                text = data.get('input')
                if not isinstance(text, str) or not 0 < len(text.strip()) <= 1200:
                    raise ValueError('Invalid input')
                if data.get('language', 'zh') not in {'zh', 'zh-tw'}:
                    raise ValueError('CosyVoice voice is Chinese only')
                emotion, mode = data.get('emotion', ''), data.get('mode', 'chat')
                if not isinstance(emotion, str) or not isinstance(mode, str):
                    raise ValueError('Invalid style')
                strength = data.get('strength', 'standard')
                if strength not in {'gentle', 'standard', 'expressive'}:
                    raise ValueError('Unknown emotion strength')
            except (ValueError, TypeError, AttributeError) as exc:
                return self.reply(400, json.dumps({'error': str(exc)}).encode())
            try:
                with lock:
                    if engine is None:
                        engine = load_engine(root)
                    audio = synthesize(engine, text.strip(), emotion, mode, strength)
                self.reply(200, audio, 'audio/wav')
            except Exception as exc:
                self.reply(503, json.dumps({'error': str(exc)}).encode())

    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
