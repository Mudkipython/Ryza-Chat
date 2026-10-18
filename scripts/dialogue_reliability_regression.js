'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const web=path.join(__dirname,'../web/js');
function env(){
 const sent=[],store={};
 class XHR{
  open(){} setRequestHeader(){} send(body){this.body=JSON.parse(body);sent.push(this);}
  abort(){this.aborted=true;if(this.onabort)this.onabort();}
  chunk(s){this.status=200;this.responseText=(this.responseText||'')+s;if(this.onprogress)this.onprogress();}
  event(text){this.chunk('data: '+JSON.stringify({choices:[{delta:{content:text}}]})+'\n\n');}
  finish(){this.chunk('data: [DONE]\n\n');this.onload();}
  json(text){this.status=200;this.responseText=JSON.stringify({choices:[{message:{content:text}}]});this.onload();}
 }
 const box={console,Promise,Map,Date,AbortController,XMLHttpRequest:XHR,location:{origin:'http://127.0.0.1:9000'},
 navigator:{language:'zh'},localStorage:{getItem:k=>store[k]||null,setItem:(k,v)=>store[k]=v},
 document:{addEventListener(){}}};box.window=box;
 for(const name of ['util.js','config.js','api.js','longterm.js','providers.js','app.js']){
  const override=process.env.RYZA_RELIABILITY_SOURCE && path.join(process.env.RYZA_RELIABILITY_SOURCE,name);
  vm.runInNewContext(fs.readFileSync(override&&fs.existsSync(override)?override:path.join(web,name),'utf8'),box);
 }
 box.Config.set('llm.apiKey','test-only');box.Config.set('llm.baseUrl','http://127.0.0.1:12345/v1');
 box.Config.set('llm.model','ryza-local');box.Config.set('llm.lang','zh');
 return {box,sent,store};
}
const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
async function stream(){
 const {box:b,sent}=env(),seen=[];
 assert.equal(b.Api.visibleReply('<think>secret'), '');
 assert.equal(b.Api.visibleReply('<think>a<think>b</think>c</think>你好'), '你好');
 assert.equal(b.Api.visibleReply('</think>你好'), '你好');
 assert.equal(b.Api.visibleReply('你好<tool_'), '你好');
 assert.equal(b.Api.visibleReply('<answer>你好</answer><state>{"energy":1}'), '你好');
 const promise=b.Api.chat([],'你好',{lang:'zh',onText:s=>seen.push(s)});
 const x=sent[0];assert.equal(x.body.stream,true);
 x.chunk('data: {"choices":[{"delta":{"content":"<thi');
 assert.equal(seen.length,0);
 x.chunk('nk>secret</think><answer>今天一起去冒险吧！"}}]}\n\n');
 x.event('</answer><state>{"energy":1}</state>');x.finish();
 const reply=await promise;
 assert.equal(reply.text,'今天一起去冒险吧！');assert(reply.streamed);
 assert(seen.every(s=>!s.includes('secret')&&!s.includes('energy')&&!s.includes('<')));
 const aborted=b.Api.chat([],'再见',{onText:()=>assert.fail('stale text exposed')});
 const reject=assert.rejects(aborted,e=>e.stale);b.Api.newTurn();await reject;
 const broken=b.Api.chat([],'test',{onText:()=>{}});const bad=assert.rejects(broken,/INCOMPLETE_STREAM/);
 sent.at(-1).event('未完整回复');sent.at(-1).onload();await bad;
}
async function language(){
 const {box:b,sent}=env();
 assert(!b.Api.languageMismatch('ライザ','zh'));
 assert(!b.Api.languageMismatch('錬金術','zh'));
 const p=b.Api.chat([],'hello',{lang:'zh'});
 sent[0].json('今日は一緒に冒険に行こう。新しい道具も持っているから楽しみだね。');
 await tick();assert.equal(sent.length,2);
 sent[1].json('今天一起去冒险吧，我带上了新道具。');
 assert.equal((await p).text,'今天一起去冒险吧，我带上了新道具。');
 const p2=b.Api.chat([],'again',{lang:'zh'});
 sent[2].json('今日は一緒に冒険に行こう。新しい道具も持っているから楽しみだね。');
 await tick();sent[3].json('今日は一緒に冒険に行こう。新しい道具も持っているから楽しみだね。');
 await assert.rejects(p2,/LANGUAGE_MISMATCH/);assert.equal(sent.length,4);
 const translation=b.Api.translate('我们明天一起去山里采药吧。','ja',null,'zh');
 sent[4].json('我们明天一起去山里采药吧。');await tick();
 sent[5].json('明日は一緒に山で薬草を採ろう。');
 assert.equal(await translation,'明日は一緒に山で薬草を採ろう。');assert.equal(sent.length,6);
}
async function memory(){
 const {box:b}=env(),L=b.LongTerm;
 let resolve,calls=0;
 L.setLLM((sys,user)=>{calls++;JSON.parse(user);return new Promise(r=>resolve=r);});
 L.note('user','旧对话',{noConsolidate:true});
 const a=L.consolidate(),same=L.consolidate();await tick();assert.equal(a,same);assert.equal(calls,1);
 L.note('assistant','新对话',{noConsolidate:true});
 resolve('{"digest":"已核对的旧内容","entries":[]}');await a;
 assert.equal(L.pendingTurns(),1);assert.equal(L._state().pending[0].text,'新对话');
 const bad=L.consolidate();await tick();resolve('invalid');await bad;assert.equal(L.pendingTurns(),1);
 const old=L.consolidate();await tick();
 L.restore({entries:[],digest:'另一个存档'});resolve('{"digest":"旧存档不能写入","entries":[]}');await old;
 assert.equal(L.digest(),'另一个存档');assert.equal(L.pendingTurns(),0);
 L.note('user','快照待办',{noConsolidate:true});const snap=L.snapshot();L._reset();L.restore(snap);
 assert.equal(L.pendingTurns(),1);assert.equal(L._state().pending[0].text,'快照待办');
}
async function audio(){
 const {box:b}=env(),{wavBlob}=require('./audio_fixture');
 assert.equal(await b.Providers.validateLocalAudio(wavBlob()) instanceof Blob,true);
 await assert.rejects(b.Providers.validateLocalAudio(new Blob(['<html>error</html>'])),/INVALID_AUDIO/);
 const bad=await wavBlob().arrayBuffer();new DataView(bad).setUint32(40,999999,true);
 await assert.rejects(b.Providers.validateLocalAudio(new Blob([bad])),/INVALID_AUDIO/);
}
(async()=>{
 let failures=0;
 for(const [name,test] of Object.entries({stream,language,memory,audio})){
  try{await test();console.log('PASS '+name);}catch(e){failures++;console.error('FAIL '+name,e.message);}
 }
 if(failures)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
