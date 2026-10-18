#!/usr/bin/env python3
"""Local character-voice TTS and Qwen3-ASR transcription; no cloud calls."""
import argparse
from email.parser import BytesParser
from email.policy import default
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.request import Request, urlopen
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
CLONE = None
KOKORO = None
ROOT = None
MODEL_ERROR = ''
ASR = None
ASR_PROFILE = {'engine': 'qwen3'}
VOICES = {'ryza_cosy', 'ryza_sovits', 'ryza', 'zf_xiaoxiao', 'zf_xiaobei', 'zf_xiaoni', 'zf_xiaoyi', 'system'}


def prepare_models(root):
    """Initialize paths only; optional TTS models load on first use."""
    global ROOT, CLONE, KOKORO, MODEL_ERROR, ASR, ASR_PROFILE
    ROOT = Path(root)
    CLONE = KOKORO = None
    MODEL_ERROR = ''
    ASR = None
    profile = ROOT / 'asr-profile.json'
    ASR_PROFILE = json.loads(profile.read_text()) if profile.is_file() else {'engine': 'qwen3'}
    if ASR_PROFILE.get('engine', 'qwen3') != 'qwen3' or ASR_PROFILE.get('languages'):
        raise ValueError('Unknown local ASR engine')


def asr_engine(language):
    return 'qwen3'


def asr_available(engine):
    name = 'qwen3-asr/model.safetensors'
    return (ROOT / name).is_file()


def clone_available():
    return all((ROOT / name).is_file() for name in (
        'qwen3-tts/model.safetensors',
        'qwen3-tts/speech_tokenizer/model.safetensors',
        'ryza-reference.wav', 'ryza-reference.txt'))


def load_clone():
    """Called under LOCK so simultaneous requests cannot duplicate weights."""
    global CLONE, MODEL_ERROR
    if CLONE is None:
        if not clone_available():
            raise RuntimeError('缺少 Qwen3-TTS 音色资源，请运行准备脚本；语音输入仍可使用。')
        try:
            from mlx_audio.tts.utils import load_model
            CLONE = load_model(str(ROOT / 'qwen3-tts'))
            MODEL_ERROR = ''
        except Exception as exc:
            MODEL_ERROR = str(exc)
            raise RuntimeError('角色音色加载失败：' + MODEL_ERROR) from exc
    return CLONE


def model_status():
    return {'service': 'ryza-local-speech', 'engine': 'on-demand local TTS',
            'clone_ready': clone_available(), 'clone_loaded': CLONE is not None,
            'kokoro_ready': (ROOT / 'kokoro/config.json').is_file(),
            'asr_ready': all(asr_available(asr_engine(lg)) for lg in ('zh', 'ja', 'en')),
            'asr_engine': asr_engine('zh'), 'asr_loaded': ASR is not None,
            'model_error': MODEL_ERROR}


def wav_bytes(parts, rate):
    import numpy as np
    import soundfile as sf
    if not parts:
        raise ValueError('No audio generated')
    buf = io.BytesIO()
    sf.write(buf, np.concatenate(parts), rate, format='WAV', subtype='PCM_16')
    return buf.getvalue()


def synthesize(text, voice, language='zh', emotion='', mode='chat', strength='standard'):
    if language not in {'zh', 'zh-tw', 'ja', 'en'}:
        raise ValueError('Unsupported speech language')
    if voice == 'ryza_cosy':
        base = os.environ.get('RYZA_COSYVOICE_URL', '')
        if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]+', base):
            raise RuntimeError('CosyVoice 尚未准备完成，请选择其他本地音色。')
        if language not in {'zh', 'zh-tw'}:
            raise ValueError('CosyVoice voice is Chinese only')
        body = json.dumps({'input': text, 'language': language, 'emotion': emotion, 'mode': mode, 'strength': strength}).encode()
        with urlopen(Request(base + '/v1/audio/speech', data=body,
                             headers={'Content-Type': 'application/json'}), timeout=180) as response:
            return response.read(), 'CosyVoice3 / MLX'
    if voice == 'ryza_sovits':
        base=os.environ.get('RYZA_SOVITS_URL','')
        if not re.fullmatch(r'http://127\.0\.0\.1:[0-9]+',base):
            raise RuntimeError('GPT-SoVITS 尚未准备完成，请先使用日语原声音色或备用中文音色。')
        body=json.dumps({'input':text,'language':language}).encode()
        with urlopen(Request(base+'/v1/audio/speech',data=body,headers={'Content-Type':'application/json'}),timeout=180) as response:
            return response.read(), 'GPT-SoVITS v2ProPlus / CPU'
    global KOKORO
    import numpy as np
    with LOCK:
        if voice == 'ryza':
            clone = load_clone()
            # Speaker embedding preserves timbre without carrying Japanese
            # phonetics into Chinese, which was unstable with transcript ICL.
            parts = [np.array(r.audio) for r in clone.generate(
                text=text, ref_audio=str(ROOT / 'ryza-reference.wav'),
                lang_code={'zh': 'Chinese', 'zh-tw': 'Chinese', 'ja': 'Japanese', 'en': 'English'}[language], temperature=0.5, top_k=30, top_p=0.9,
                repetition_penalty=1.1, max_tokens=500, verbose=False)]
            return wav_bytes(parts, 24000), 'Qwen3-TTS / Ryza reference'
        if voice != 'system':
            if KOKORO is None:
                if not (ROOT / 'kokoro/config.json').is_file():
                    raise RuntimeError('未安装 Kokoro 备用音色，请运行准备脚本 --with-kokoro。')
                from mlx_audio.tts.utils import load_model
                KOKORO = load_model(str(ROOT / 'kokoro'))
            parts = [np.array(r.audio) for r in KOKORO.generate(
                text, voice=str(ROOT / 'kokoro/voices' / (voice + '.safetensors')),
                lang_code='z', speed=1.05)]
            return wav_bytes(parts, 24000), 'Kokoro-82M / MLX'
        with tempfile.TemporaryDirectory(prefix='ryza-speech-') as tmp:
            src, aiff, wav = [Path(tmp) / n for n in ('text.txt', 'voice.aiff', 'voice.wav')]
            src.write_text(text, encoding='utf-8')
            subprocess.run(['/usr/bin/say', '-v', 'Tingting', '-r', '190', '-f', str(src),
                            '-o', str(aiff)], check=True, timeout=90, capture_output=True)
            subprocess.run(['/usr/bin/afconvert', '-f', 'WAVE', '-d', 'LEI16',
                            str(aiff), str(wav)], check=True, timeout=30, capture_output=True)
            return wav.read_bytes(), 'macOS Tingting'


def parse_multipart(content_type, body):
    message = BytesParser(policy=default).parsebytes(
        ('Content-Type: ' + content_type + '\r\nMIME-Version: 1.0\r\n\r\n').encode() + body)
    if not message.is_multipart():
        raise ValueError('Expected multipart/form-data')
    audio = None
    language = 'zh'
    for part in message.iter_parts():
        name = part.get_param('name', header='content-disposition')
        if name == 'file':
            audio = part.get_payload(decode=True)
        elif name == 'language':
            language = (part.get_payload(decode=True) or b'zh').decode().strip()
    if not audio:
        raise ValueError('No audio file supplied')
    if language not in {'zh', 'ja', 'en'}:
        raise ValueError('Supported input languages: zh, ja, en')
    return audio, language


def transcribe(audio, language):
    global ASR
    if language not in {'zh', 'ja', 'en'}:
        raise ValueError('Unsupported input language')
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    data, rate = sf.read(io.BytesIO(audio), dtype='float32', always_2d=False)
    if data.ndim == 2:
        data = data.mean(axis=1)
    if not len(data) or len(data) / rate > 30:
        raise ValueError('Audio must contain at most 30 seconds')
    if np.sqrt(np.mean(data ** 2)) < 0.001:
        return ''
    if rate != 16000:
        divisor = math.gcd(rate, 16000)
        data = resample_poly(data, 16000 // divisor, rate // divisor).astype('float32')
    engine = asr_engine(language)
    if not asr_available(engine):
        raise RuntimeError('缺少本地识别模型：' + engine + '，请运行对应准备脚本。')
    with LOCK:
        if ASR is None:
            from mlx_audio.stt.utils import load_model
            ASR = load_model(str(ROOT / 'qwen3-asr'))
        result = ASR.generate(data, language={'zh': 'Chinese', 'ja': 'Japanese', 'en': 'English'}[language],
            max_tokens=256, hotwords=ASR_PROFILE.get('hotwords', {}).get(language, []),
            temperature=0.0, verbose=False)
        return result.text.strip()



def allowed_origin(origin):
    return not origin or origin == 'ryza://app' or bool(re.fullmatch(
        r'http://(?:127\.0\.0\.1|localhost)(?::\d+)?', origin))


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, content_type='application/json', engine=None):
        self.send_response(code)
        origin = self.headers.get('Origin', '')
        if origin and allowed_origin(origin):
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        if engine:
            self.send_header('X-Ryza-Speech-Engine', engine)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send(200 if allowed_origin(self.headers.get('Origin', '')) else 403, b'')

    def do_GET(self):
        if self.path != '/health':
            return self.send(404, b'{}')
        self.send(200, json.dumps(model_status(), ensure_ascii=False).encode())

    def do_POST(self):
        if not allowed_origin(self.headers.get('Origin', '')):
            return self.send(403, b'{"error":"Origin not allowed"}')
        if self.path not in {'/v1/audio/speech', '/v1/audio/transcriptions'}:
            return self.send(404, b'{}')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            limit = 4_000_000 if self.path.endswith('/transcriptions') else 16000
            if not 0 < size <= limit:
                raise ValueError('Invalid request size')
            body = self.rfile.read(size)
            if self.path.endswith('/transcriptions'):
                audio, language = parse_multipart(self.headers.get('Content-Type', ''), body)
                text = transcribe(audio, language)
                return self.send(200, json.dumps({'text': text}, ensure_ascii=False).encode())
            data = json.loads(body)
            text = data.get('input', '')
            voice = data.get('voice') or 'ryza'
            language = data.get('language') or 'zh'
            if language not in {'zh', 'zh-tw', 'ja', 'en'}:
                raise ValueError('Unsupported speech language')
            if not isinstance(text, str) or not text.strip() or len(text) > 1200:
                raise ValueError('input must contain 1–1200 characters')
            if voice not in VOICES:
                raise ValueError('Unsupported voice')
        except (ValueError, TypeError, AttributeError, RuntimeError) as exc:
            return self.send(400, json.dumps({'error': str(exc)}).encode())
        except Exception as exc:
            return self.send(503, json.dumps({'error': str(exc)}).encode())
        try:
            audio, engine = synthesize(text.strip(), voice, language, data.get('emotion', ''), data.get('mode', 'chat'), data.get('strength', 'standard'))
            self.send(200, audio, 'audio/wav', engine)
        except Exception as exc:
            self.send(503, json.dumps({'error': str(exc)}).encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8767)
    parser.add_argument('--root', required=True)
    args = parser.parse_args()
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
    prepare_models(args.root)
    print('Speech service ready; TTS loads on demand', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
