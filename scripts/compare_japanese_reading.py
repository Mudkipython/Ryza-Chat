#!/usr/bin/env python3
"""One-variable Japanese kanji/kana experiment; does not change application settings.
Generate with sovits-venv; use --analyze with voice-venv and Metal access.
ASR is a screening signal, not a listening or voice-similarity judgment.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/japanese-reading-ab'
PAIRS=[('original','私はライザ。錬金術で、新しい道具を作るのが大好きなんだ。'),
       ('kana','私はライザ。れんきんじゅつで、新しい道具を作るのが大好きなんだ。')]
os.environ.setdefault('HF_HUB_OFFLINE','1')
os.environ.setdefault('TRANSFORMERS_OFFLINE','1')
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.runtime/cache/matplotlib'))


def generate():
    import soundfile as sf
    spec=importlib.util.spec_from_file_location('adapter',ROOT/'scripts/sovits_speech.py')
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    engine=adapter.load_engine(ROOT/'.runtime')
    rows=[]
    for label,text in PAIRS:
        pieces=engine.text_preprocessor.preprocess(text,'all_ja','cut5',engine.configs.version)
        trace=[{'normalized':p['norm_text'],'phones':p['phones'],
                'bert_zero':bool((p['bert_features']==0).all().item())} for p in pieces]
        t=time.monotonic();audio=adapter.synthesize(engine,ROOT/'.runtime',text,'ja','03')
        destination=OUT/(label+'.wav');destination.write_bytes(audio)
        waveform,rate=sf.read(destination)
        rows.append({'label':label,'text':text,'file':destination.name,'reference':'03','seed':42,
                     'seconds':round(time.monotonic()-t,3),'duration':len(waveform)/rate,
                     'sha256':hashlib.sha256(audio).hexdigest(),'frontend':trace})
    a,b=rows
    result={'changed_word':{'from':'錬金術','to':'れんきんじゅつ'},
            'same_phone_ids':[p['phones'] for p in a['frontend']]==[p['phones'] for p in b['frontend']],
            'same_wav':a['sha256']==b['sha256'],'samples':rows}
    (OUT/'generation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!='samples'},ensure_ascii=False),flush=True)


def analyze():
    import math
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly
    from mlx_audio.stt.utils import load_model
    model=load_model(str(ROOT/'.runtime/qwen3-asr'))
    rows=[]
    for label,_ in PAIRS:
        data,rate=sf.read(OUT/(label+'.wav'),dtype='float32')
        d=math.gcd(rate,16000);data=resample_poly(data,16000//d,rate//d).astype('float32')
        result=model.generate(data,language='Japanese',max_tokens=256,temperature=0.0)
        rows.append({'label':label,'asr':result.text,'hotwords':False})
    (OUT/'recognition.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
    print(json.dumps(rows,ensure_ascii=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--analyze',action='store_true')
    args=parser.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    analyze() if args.analyze else generate()
