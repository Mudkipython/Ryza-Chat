const {wavBlob}=require('./audio_fixture');
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const state={tts:{provider:'localSpeech',mode:'preset',localSpeechVoice:'ryza',localSpeechBaseUrl:'http://127.0.0.1:12345/v1'},
 app:{cosyReady:true,sovitsReady:true},llm:{},state:{}};
let last,stops=0;
const box={Promise,Map,URL:{createObjectURL:()=> 'blob:test'},location:{origin:'http://127.0.0.1:9000'},
 Config:{section:key=>state[key]||{},set:(key,value)=>{const [a,b]=key.split('.');state[a][b]=value;}},
 Turn:{stopAll:()=>stops++},fetch:async(url,options)=>{last={url,body:JSON.parse(options.body)};return {ok:true,blob:async()=>wavBlob()};}};
box.window=box;
for(const file of ['providers.js','api.js','settings.js']){
 const source=file==='providers.js' && process.env.RYZA_PROVIDER_SOURCE ? process.env.RYZA_PROVIDER_SOURCE : path.join(__dirname,'../web/js',file);
 vm.runInNewContext(fs.readFileSync(source,'utf8'),box);
}
(async()=>{
 const {Providers:P,Settings:S,Api:A}=box;
 assert.equal(typeof P.localProfile,'function');
 assert(!P.localVoices('ja',state.app).some(v=>v.id==='ryza_cosy'));
 assert(!P.localVoices('zh',{}).some(v=>v.id==='ryza_cosy'));
 S.setLocalProfile('zh','chat','voice','ryza_cosy');
 S.setLocalProfile('zh','chat','strength','expressive');
 S.setLocalProfile('zh','asmr','voice','system');
 S.setLocalProfile('zh','asmr','strength','gentle');
 const saved=JSON.parse(JSON.stringify(state.tts.localProfiles));
 await A.speak('明天一起采药吧！','zh','chat','happy');
 assert.equal(last.body.voice,'ryza_cosy');assert.equal(last.body.emotion,'happy');
 assert.equal(last.body.strength,'expressive');assert.equal(last.body.mode,'chat');
 await A.speak('休息一下。','zh','asmr','sad');
 assert.equal(last.body.voice,'system');assert.equal(last.body.emotion,'');assert.equal(last.body.mode,'chat');
 S.setLocalProfile('zh','asmr','voice','ryza_cosy');
 await A.speak('休息一下。','zh','asmr','sad');
 assert.equal(last.body.mode,'asmr');assert.equal(last.body.strength,'gentle');
 await A.speak('こんにちは','ja','asmr','happy');
 assert.equal(last.body.voice,'ryza');assert.equal(last.body.emotion,'');assert.equal(last.body.mode,'chat');
 S.setLocalProfile('ja','chat','voice','ryza_cosy');
 assert.equal(state.tts.localProfiles['ja:chat'],undefined);
 S.setLocalProfile('zh','chat','strength','arbitrary instruction');
 assert.equal(state.tts.localProfiles['zh:chat'].strength,'expressive');
 state.tts.localProfiles=saved; // Serialization/restore keeps mode-specific preferences.
 assert.equal(P.localProfile(state.tts,'zh','chat').voice,'ryza_cosy');
 state.tts.localProfiles['ja:chat']={voice:'ryza_cosy'};
 await assert.rejects(A.speak('こんにちは','ja','chat'),/不支持/);
 assert(stops>=4);
 console.log('LOCAL VOICE PROFILES: PASS (language/mode routing, capabilities, strength, persistence, invalid selection)');
})().catch(e=>{console.error(e);process.exitCode=1;});
