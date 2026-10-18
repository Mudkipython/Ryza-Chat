#!/usr/bin/env python3
"""Compare local models with the same prompts and bounded, non-thinking generation."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('chat', [{'role':'system','content':'你是莱莎，开朗自然的炼金术士。请用中文与玩家聊天，每次不超过两句话，不要输出分析。'},
              {'role':'user','content':'今天好累，什么都不想干。你会陪我吗？'}]),
    ('continuity', [{'role':'system','content':'你是莱莎，用自然简短的中文回答。记住玩家说过的安排，不编造物品或已发生的事情。'},
                    {'role':'user','content':'我叫小林。明天上午十点我们去山里采药，回来一起调合。'},
                    {'role':'assistant','content':'好呀，小林！我会记住明天上午十点的约定。'},
                    {'role':'user','content':'我们几点出发，回来做什么？'}]),
    ('translate', [{'role':'system','content':'将用户的中文台词翻译成自然口语日语，只输出译文，不添加内容或说明。'},
                   {'role':'user','content':'明天上午十点，我们去山里采药，回来以后再一起调合。'}]),
    ('format', [{'role':'system','content':'只输出一个JSON对象，不要Markdown。键为emotion和text。emotion必须是happy、neutral或sad之一；text是莱莎对玩家的一句中文回应。'},
                {'role':'user','content':'今天终于把任务做完啦！'}]),
]

def run_model(model, label, destination):
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    destination.parent.mkdir(parents=True,exist_ok=True)
    log=destination.with_suffix('.log').open('w')
    args=[str(ROOT/'.runtime/llama/llama-b11712/llama-server'),'-m',str(model),'--host','127.0.0.1',
          '--port',str(port),'-c','8192','-ngl','99','-t','4','--parallel','1','--jinja','--reasoning','off',
          '--chat-template-kwargs','{"enable_thinking":false}','--alias','ryza-local']
    process=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT)
    rows=[]
    try:
        deadline=time.monotonic()+120
        while True:
            if process.poll() is not None:raise RuntimeError(f'{label} failed; see {log.name}')
            try:
                with urlopen(base+'/health',timeout=2) as r:
                    if r.status==200:break
            except Exception:pass
            if time.monotonic()>deadline:raise TimeoutError('Model startup timed out')
            time.sleep(.25)
        cases = list(CASES)
        fixture = ROOT/'output/model-comparison/app-prompt.json'
        if fixture.is_file():
            cases.append(('app', [{'role':'system','content':json.loads(fixture.read_text())}, {'role':'user','content':'我叫小林。今天好累，你能陪我聊两句吗？'}]))
        for name,messages in cases:
            body={'model':'ryza-local','messages':messages,'temperature':.7,'top_p':.8,'top_k':20,'presence_penalty':1.5,'seed':42,'max_tokens':256,
                  'chat_template_kwargs':{'enable_thinking':False},'stream':True,'stream_options':{'include_usage':True}}
            if name == 'format': body['response_format'] = {'type':'json_object'}
            t=time.monotonic();first=None;answer='';reasoning='';usage={};timings={}
            with urlopen(Request(base+'/v1/chat/completions',data=json.dumps(body).encode(),
                         headers={'Content-Type':'application/json'}),timeout=120) as response:
                for raw in response:
                    if not raw.startswith(b'data: '):continue
                    data=raw[6:].strip()
                    if data==b'[DONE]':break
                    event=json.loads(data);usage=event.get('usage') or usage;timings=event.get('timings') or timings
                    for choice in event.get('choices',[]):
                        delta=choice.get('delta',{});part=delta.get('content') or ''
                        if part and first is None:first=round(time.monotonic()-t,3)
                        answer+=part;reasoning+=delta.get('reasoning_content') or ''
            row={'case':name,'text':answer,'reasoning':reasoning,'first_content_seconds':first,
                 'total_seconds':round(time.monotonic()-t,3),'usage':usage,'timings':timings}
            print(label,json.dumps(row,ensure_ascii=False),flush=True)
            if not answer.strip() or reasoning or '<think>' in answer:raise RuntimeError('Invalid answer/thinking: '+str(row))
            if name=='format':
                parsed=json.loads(answer);assert parsed['emotion'] in {'happy','neutral','sad'} and parsed['text']
            rows.append(row)
        destination.write_text(json.dumps({'model':label,'context':8192,'results':rows},ensure_ascii=False,indent=2))
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        log.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('model',type=Path);parser.add_argument('--label',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    run_model(args.model.resolve(),args.label,args.output.resolve())
