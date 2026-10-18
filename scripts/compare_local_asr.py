#!/usr/bin/env python3
"""Evaluate local ASR fixtures without microphone recording or cloud requests.
Optional --whisper-model PATH needs a separately installed mlx-whisper baseline.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--whisper-model',type=Path)
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('speech',Path(__file__).with_name('local_speech.py'))
    service=importlib.util.module_from_spec(spec);spec.loader.exec_module(service)
    service.prepare_models(ROOT/'.runtime')
    files=[(ROOT/'output'/name,'zh') for name in ['ryza-sovits-app-chinese.wav','ryza-sovits-voice-only-short.wav','ryza-character-voice.wav']]
    files += [(p,'ja') for p in sorted((ROOT/'web/assets/voice/ryza_wav').glob('*.wav'))]
    rows=[]
    for path,language in files:
        if not path.is_file():continue
        t=time.monotonic();text=service.transcribe(path.read_bytes(),language)
        row={'file':str(path.relative_to(ROOT)),'language':language,'qwen':text,'seconds':round(time.monotonic()-t,3)}
        if args.whisper_model:
            import mlx_whisper,numpy as np,soundfile as sf
            from scipy.signal import resample_poly
            from math import gcd
            data,rate=sf.read(path,dtype='float32');data=data.mean(1) if data.ndim==2 else data
            d=gcd(rate,16000);data=resample_poly(data,16000//d,rate//d).astype('float32')
            row['whisper']=mlx_whisper.transcribe(data,path_or_hf_repo=str(args.whisper_model.resolve()),language=language,condition_on_previous_text=False,temperature=0.0,verbose=False)['text'].strip()
        print(json.dumps(row,ensure_ascii=False),flush=True);rows.append(row)
    out=ROOT/'output/speech-comparison';out.mkdir(parents=True,exist_ok=True)
    (out/'current-asr.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
