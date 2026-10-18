#!/usr/bin/env python3
"""Prepare or verify the pinned local LLM and llama.cpp resources."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from urllib.request import urlretrieve

ROOT = Path(__file__).resolve().parents[1]

def check_model(root=ROOT):
    manifest=json.loads((root/'desktop/model-manifest.json').read_text())
    preset=manifest['llm'];model=root/'.runtime/models'/preset['filename']
    if not model.is_file() or model.stat().st_size!=preset['size']:
        raise RuntimeError('缺少完整的 '+preset['label']+'；请运行准备脚本。')
    digest=hashlib.sha256()
    with model.open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):digest.update(chunk)
    if digest.hexdigest()!=preset['sha256']:raise RuntimeError('模型 SHA256 校验失败。')
    return manifest

def prepare():
    manifest=json.loads((ROOT/'desktop/model-manifest.json').read_text())
    runtime=ROOT/'.runtime';runtime.mkdir(exist_ok=True)
    engine=runtime/manifest['engine']['directory']
    if not (engine/'llama-server').is_file():
        archive=runtime/'llama.tar.gz'
        urlretrieve(manifest['engine']['url'],archive)
        target=runtime/'llama';target.mkdir(exist_ok=True)
        with tarfile.open(archive) as f:f.extractall(target,filter='data')
        if not (engine/'llama-server').is_file():raise RuntimeError('引擎解压失败。')
        archive.unlink()
    preset=manifest['llm'];model=runtime/'models'/preset['filename']
    if not model.is_file() or model.stat().st_size!=preset['size']:
        from huggingface_hub import hf_hub_download
        hf_hub_download(preset['repo'],preset['filename'],revision=preset['revision'],local_dir=runtime/'models')
    return check_model()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=prepare() if args.download else check_model()
    print('MODEL VERIFIED:',result['llm']['label'])
