const {wavBlob}=require('./audio_fixture');
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const base = process.env.RYZA_SPEECH_SOURCE || path.join(__dirname, '../web/js');
const requests = [], fetches = [], revoked = [], cached = [];
class XHR {
  open() {} setRequestHeader() {}
  send(body) { this.body=JSON.parse(body); requests.push(this); }
  abort() { this.aborted=true; this.onabort(); }
  reply(text) { this.status=200; this.responseText=JSON.stringify({choices:[{message:{content:text}}]});this.onload(); }
}
const config = {llm:{apiKey:'test-only',baseUrl:'http://127.0.0.1:12345/v1',model:'ryza-local'},
 tts:{provider:'localSpeech',mode:'preset',localSpeechVoice:'ryza',localSpeechBaseUrl:'http://127.0.0.1:12346/v1'},state:{mode:'chat'}};
const box = {console,Promise,AbortController,XMLHttpRequest:XHR, location:{origin:'http://127.0.0.1:9000'},
 document:{addEventListener(){}}, Config:{section:n=>config[n]||{}},
 Langs:{llm:()=> 'zh',tts:()=> 'ja'},
 URL:{createObjectURL:()=> 'blob:test',revokeObjectURL:u=>revoked.push(u)},
 fetch:(url,options)=>{fetches.push({url,options});return Promise.resolve({ok:true,blob:()=>Promise.resolve(wavBlob())});},
 VoiceCache:{put:(key)=>cached.push(key)}};
box.window=box;
for(const file of ['providers.js','api.js','app.js'])vm.runInNewContext(fs.readFileSync(path.join(base,file),'utf8'),box);
const {Api,App}=box;
const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
(async()=>{
 // A real transport must abort, not silently fall back to Chinese speech.
 let c=new AbortController();
 const pending=Api.translate('你好','ja',c.signal);
 c.abort();
 assert.equal(requests.at(-1).aborted,true,'translation XHR was not aborted');
 await assert.rejects(pending,e=>e.name==='AbortError');
 const count=requests.length;
 await assert.rejects(Api.translate('你好','ja',c.signal),e=>e.name==='AbortError');
 assert.equal(requests.length,count,'already cancelled request was sent');
 const fallback=Api.translate('你好','ja');requests.at(-1).onerror();assert.equal(await fallback,'你好');

 // Existing Chinese display string is not rewritten; only the spoken line is Japanese.
 const source='明天一起采药吧。', meta={emotion:'happy'};c=new AbortController();
 const voiced=App._synthesizeSpeech(source,meta,c.signal);
 requests.at(-1).reply('明日、一緒に薬草を採りに行こう。');
 assert.equal(await voiced,'blob:test');
 assert.equal(source,'明天一起采药吧。');
 assert.equal(meta.spokenText,'明日、一緒に薬草を採りに行こう。');
 assert.equal(fetches[0].options.signal,c.signal);
 assert.equal(JSON.parse(fetches[0].options.body).language,'ja');
 assert.equal(JSON.parse(fetches[0].options.body).input,meta.spokenText);
 assert.equal(JSON.parse(fetches[0].options.body).emotion,''); // Qwen adapter does not claim emotion control.
 assert.equal(JSON.parse(fetches[0].options.body).mode,'chat');
 assert.equal(App._speechText('太好了！！！！……真的？？？？'),'太好了！！……真的？？');
 // Persist the spoken translation with its source record and reuse it after cache eviction.
 const record={who:'ryza',text:source};App.memory=[record];
 let saves=0;App.saveMemory=()=>{saves++;};
 await App._synthesizeSpeech(source,{record,replyLang:'zh',ttsLang:'ja'},c.signal);
 assert.equal(saves,1);assert.equal(record.translations[0].language,'ja');
 Api._translationCache.clear();const storedRequests=requests.length;
 await App._synthesizeSpeech(source,{record,replyLang:'zh',ttsLang:'ja'},c.signal);
 assert.equal(requests.length,storedRequests,'saved translation was not reused');
 Api._translationCache.set(JSON.stringify([config.llm.baseUrl,config.llm.model,config.llm.apiKey,'ja',source]),meta.spokenText);
 const requestCount=requests.length;
 assert.equal(await Api.translate(source,'ja'),meta.spokenText);
 assert.equal(requests.length,requestCount,'successful translation was not reused');
 config.llm.model='different-model';
 const isolated=Api.translate(source,'ja');
 assert.equal(requests.length,requestCount+1,'different model reused a cached translation');
 requests.at(-1).reply('別の翻訳');await isolated;
 config.llm.model='ryza-local';
 for(let i=0;i<35;i++){
   const translated=Api.translate('台词'+i,'ja');requests.at(-1).reply('訳'+i);await translated;
 }
 assert.equal(Api._translationCache.size,32);
 await tick();assert.equal(cached.length,3);

 const priorFetch=fetches.length;c=new AbortController();
 const stopped=App._synthesizeSpeech('不要读出这句',{},c.signal);
 const rejection=assert.rejects(stopped,e=>e.name==='AbortError');c.abort();await rejection;
 assert.equal(fetches.length,priorFetch,'cancelled translation started TTS');

 // Cancellation during synthesis reaches fetch and cannot create a stale blob.
 let finish;
 box.fetch=(url,options)=>new Promise(resolve=>{finish=()=>resolve({ok:true,blob:async()=>wavBlob()});assert.equal(options.signal,c.signal);});
 c=new AbortController();
 const local=Api.speak('こんにちは','ja','chat','',c.signal);
 c.abort();finish();await assert.rejects(local,e=>e.name==='AbortError');

 // Providers that complete after cancellation still have their blob discarded.
 const realSpeak=Api.speak;
 Api.speak=()=>new Promise(resolve=>{finish=()=>resolve('blob:late');});
 c=new AbortController();
 const late=App._synthesizeSpeech('日本語',{translated:true},c.signal);
 await tick();c.abort();finish();assert.equal(await late,null);
 assert(revoked.includes('blob:late'));assert.equal(cached.length,3);
 Api.speak=realSpeak;
 console.log('BILINGUAL SPEECH: PASS (translation abort/fallback, Japanese handoff, no stale synth/cache, blob disposal)');
})().catch(e=>{console.error(e);process.exitCode=1;});
