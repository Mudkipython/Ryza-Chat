#!/usr/bin/env python3
"""Isolated GPT-SoVITS CPU inference adapter; never trains or downloads models."""
import argparse
import io
import json
import os
from pathlib import Path
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def load_engine(root):
    repo = root / 'gpt-sovits'
    language_model = repo / 'GPT_SoVITS/pretrained_models/fast_langdetect/lid.176.bin'
    if not language_model.is_file():
        raise RuntimeError('缺少离线语言识别模型，请运行 prepare_sovits_trial.command。')
    os.chdir(repo)
    sys.path[:0] = [str(repo), str(repo / 'GPT_SoVITS')]
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
    os.environ['NLTK_DATA'] = str(repo / 'nltk_data')
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    import torch
    torch.set_num_threads(4)
    import pyopenjtalk
    dictionary = root / 'sovits-downloads/open_jtalk_dic_utf_8-1.11'
    archive = root / 'sovits-downloads/open_jtalk_dic_utf_8-1.11.tar.gz'
    if archive.is_file() and not dictionary.is_dir():
        import tarfile
        with tarfile.open(archive) as tar:
            tar.extractall(root / 'sovits-downloads', filter='data')
    if dictionary.is_dir():
        pyopenjtalk.OPEN_JTALK_DICT_DIR = str(dictionary).encode()
    import imageio_ffmpeg
    import tools.portable_runtime as portable
    portable.FFMPEG_EXE = Path(imageio_ffmpeg.get_ffmpeg_exe())
    from TTS_infer_pack.TTS import TTS, TTS_Config
    cfg = dict(TTS_Config.default_configs['v2ProPlus'])
    cfg.update(device='cpu', is_half=False)
    return TTS(TTS_Config({'custom':cfg}))


def synthesize(engine, root, text, language, reference=None):
    if language not in {'zh','zh-tw','ja'}:
        raise ValueError('Supported speech languages: zh, ja')
    import numpy as np
    import soundfile as sf
    if reference is None:
        profile = root / 'sovits-reference.json'
        choices = json.loads(profile.read_text()) if profile.is_file() else {}
        reference = choices.get('zh' if language.startswith('zh') else language, choices.get('reference', '03'))
    if reference not in {'01', '03', '03-voice-only'}:
        raise ValueError('Unknown reference profile')
    audio_path = root / ('sovits-reference-01.wav' if reference == '01' else 'ryza-reference.wav')
    text_path = root / ('sovits-reference-01.txt' if reference == '01' else 'ryza-reference.txt')
    chunks = list(engine.run({
        'text':text, 'text_lang':'all_zh' if language.startswith('zh') else 'all_ja',
        'ref_audio_path':str(audio_path),
        'prompt_text':'' if reference == '03-voice-only' else text_path.read_text().strip(),
        'prompt_lang':'all_ja', 'top_k':15, 'top_p':1.0, 'temperature':1.0,
        'seed':42, 'text_split_method':'cut5', 'batch_size':1,
        'parallel_infer':False, 'streaming_mode':False, 'repetition_penalty':1.35,
        'speed_factor':1.0, 'fragment_interval':0.2,
    }))
    if not chunks: raise RuntimeError('No audio generated')
    rate=chunks[0][0]
    if any(sr!=rate for sr,_ in chunks): raise RuntimeError('Inconsistent sample rates')
    buf=io.BytesIO()
    sf.write(buf,np.concatenate([a for _,a in chunks]),rate,format='WAV',subtype='PCM_16')
    return buf.getvalue()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--port',type=int)
    parser.add_argument('--text')
    parser.add_argument('--language',default='zh')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=args.root.resolve()
    output=args.output.resolve() if args.output else None
    engine=None
    if args.text:
        engine=load_engine(root)
        output.write_bytes(synthesize(engine,root,args.text,args.language))
        print('Saved',output,flush=True);return
    lock=threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def reply(self,code,body,kind='application/json'):
            self.send_response(code);self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        def do_GET(self):
            self.reply(200 if self.path=='/health' else 404,json.dumps({'ready':True,'engine':'GPT-SoVITS-v2ProPlus-CPU','engine_loaded':engine is not None}).encode())
        def do_POST(self):
            nonlocal engine
            if self.path!='/v1/audio/speech':return self.reply(404,b'{}')
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=16000:raise ValueError('Invalid request size')
                data=json.loads(self.rfile.read(size));text=data.get('input','')
                if not isinstance(text,str) or not 0<len(text.strip())<=1200:raise ValueError('Invalid input')
                language=data.get('language','zh')
                reference=data.get('reference')
                if language not in {'zh','zh-tw','ja'}:raise ValueError('Unsupported speech language')
                if reference is not None and reference not in {'01','03','03-voice-only'}:raise ValueError('Unknown reference profile')
                with lock:
                    if engine is None:engine=load_engine(root)
                    audio=synthesize(engine,root,text.strip(),language,reference)
                self.reply(200,audio,'audio/wav')
            except Exception as exc:self.reply(503,json.dumps({'error':str(exc)}).encode())
    print('GPT-SoVITS ready',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),Handler).serve_forever()


if __name__=='__main__':main()
