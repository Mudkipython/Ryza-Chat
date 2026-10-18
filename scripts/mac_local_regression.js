const {wavBlob}=require('./audio_fixture');
'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const js = path.join(__dirname, '../web/js');
function config(saved, defaults) {
  const sandbox = { __ryzaLocalDefaults: defaults, navigator: { language: 'en' },
    localStorage: { getItem: () => saved ? JSON.stringify(saved) : null, setItem() {} },
    URL, console, Promise };
  sandbox.window = sandbox;
  vm.runInNewContext(fs.readFileSync(path.join(js, 'config.js'), 'utf8'), sandbox);
  return sandbox.Config;
}
const defaults = { llm: { baseUrl: 'http://127.0.0.1:23456/v1', model: 'ryza-local', apiKey: 'new-session-test-key' },
  tts: { provider: 'localSpeech', localSpeechBaseUrl: 'http://127.0.0.1:23457/v1' }, app: { lang: 'zh' } };
assert.equal(config(null, defaults).section('app').lang, 'zh');
const restarted = config({ llm: { baseUrl: 'http://127.0.0.1:11111/v1', model: 'ryza-local', apiKey: 'old-session-test-key' },
  tts: { provider: 'localSpeech', localSpeechBaseUrl: 'http://127.0.0.1:11112/v1' },
  chara: { callMe: '旅行者' } }, defaults);
assert.equal(restarted.section('llm').baseUrl, defaults.llm.baseUrl);
assert.equal(restarted.section('llm').apiKey, defaults.llm.apiKey);
assert.equal(restarted.section('tts').localSpeechBaseUrl, defaults.tts.localSpeechBaseUrl);
assert.equal(restarted.section('chara').callMe, '旅行者');
assert.equal(config({ llm: { baseUrl: 'https://example.com/v1', model: 'mine' } }, defaults)
  .section('llm').baseUrl, 'https://example.com/v1');
const voiceDefaults = { ...defaults, stt: { provider: 'whisper', engine: 'capture',
  model: 'ryza-whisper', baseUrl: 'http://127.0.0.1:23457/v1', apiKey: 'new-stt-key' },
  tts: { ...defaults.tts, localSpeechVoice: 'ryza' } };
const upgraded = config({ llm: { model: 'ryza-local', baseUrl: 'http://127.0.0.1:11111/v1' },
  stt: { baseUrl: '', model: 'whisper-1', engine: 'auto' },
  tts: { provider: 'localSpeech', localSpeechVoice: 'zf_xiaoxiao' },
  app: { autoSend: false } }, voiceDefaults);
assert.equal(upgraded.section('stt').baseUrl, voiceDefaults.stt.baseUrl);
assert.equal(upgraded.section('stt').engine, 'capture');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza');
assert.equal(upgraded.section('app').autoSend, false);
assert.equal(upgraded.section('app').calmMotion, false);
assert.equal(upgraded.section('app').motionMode, 'gentle');
assert.equal(upgraded.section('app').sentenceSpeech, true);
assert.equal(upgraded.section('tts').lang, 'ja');
assert.equal(upgraded.section('voice').lang, 'ja');
assert.equal(upgraded.section('llm').lang, 'zh');
const languageChoice = config({tts: {provider: 'localSpeech', localSpeechVoice: 'ryza', lang: 'en'},
  app: {localVoiceVersion: 2, localLanguageVersion: 1}}, voiceDefaults);
assert.equal(languageChoice.section('tts').lang, 'en');
const keepChoice = config({ tts: { provider: 'localSpeech', localSpeechVoice: 'system' },
  app: { localVoiceVersion: 2 } }, voiceDefaults);
assert.equal(keepChoice.section('tts').localSpeechVoice, 'system');
const localSettings = { window: null, Config: upgraded, Turn: {stopAll() {}} };
localSettings.window = localSettings;
vm.runInNewContext(fs.readFileSync(path.join(js, 'settings.js'), 'utf8'), localSettings);
localSettings.Settings.setLocalLanguage('zh');
assert.equal(upgraded.section('tts').lang, 'zh');
assert.equal(upgraded.section('voice').lang, 'ja');
assert.equal(upgraded.section('llm').lang, 'zh');
localSettings.Settings.setLocalLanguage('ja');
assert.equal(upgraded.section('tts').lang, 'ja');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza');
upgraded.set('app.sovitsReady', true);
localSettings.Settings.setLocalLanguage('zh');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza_sovits');
localSettings.Settings.setLocalLanguage('ja');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza');
upgraded.set('tts.localJapaneseVoice', 'ryza_sovits');
localSettings.Settings.setLocalLanguage('zh');
localSettings.Settings.setLocalLanguage('ja');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza_sovits');
upgraded.set('app.sovitsReady', false);
localSettings.Settings.setLocalLanguage('ja');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza');
upgraded.set('app.cosyReady', true);
upgraded.set('tts.localChineseVoice', 'ryza_cosy');
localSettings.Settings.setLocalLanguage('zh');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza_cosy');
upgraded.set('tts.localSpeechVoice', 'system');
localSettings.Settings.setLocalLanguage('zh');
assert.equal(upgraded.section('tts').localSpeechVoice, 'system');
localSettings.Settings.setLocalLanguage('ja');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza');
localSettings.Settings.setLocalLanguage('zh');
assert.equal(upgraded.section('tts').localSpeechVoice, 'ryza_cosy');
const newAsr = config({stt:{baseUrl:'http://127.0.0.1:1/v1',model:'ryza-whisper'},
  chara:{extra:'请用自然简短的中文交流，每次约两三句话。 /no_think'}},
  {...voiceDefaults,stt:{...voiceDefaults.stt,model:'ryza-asr'}});
assert.equal(newAsr.section('stt').model,'ryza-asr');
assert.equal(newAsr.section('chara').extra,'请用自然简短的中文交流；自称“我”，不要在中文对白夹杂日语。每次约两三句话。');
const manifest = require('../desktop/model-manifest.json');
assert.equal(manifest.llm.chatTemplateKwargs.enable_thinking,false);
assert.equal(manifest.llm.alias,'ryza-local');
assert.equal(manifest.llm.filename,'Qwen3.5-9B-Q4_K_M.gguf');
const sandbox = { URL: { createObjectURL: () => 'blob:test' } }; sandbox.window = sandbox;
vm.runInNewContext(fs.readFileSync(path.join(js, 'providers.js'), 'utf8'), sandbox);
(async () => {
  let call;
  const creds = sandbox.Providers.credentials({ provider: 'localSpeech' });
  const result = await sandbox.Providers.speakLocal(creds, { text: 'こんにちは', lang: 'ja', fetch: async (url, options) => {
    call = { url, options }; return { ok: true, blob: async () => wavBlob() };
  } });
  assert.equal(result, 'blob:test');
  assert.equal(call.url, 'http://127.0.0.1:8767/v1/audio/speech');
  assert.equal(JSON.parse(call.options.body).input, 'こんにちは');
  assert.equal(call.options.headers.Authorization, undefined);
  assert.equal(JSON.parse(call.options.body).language, 'ja');
  await assert.rejects(sandbox.Providers.speakLocal({ ...creds, baseUrl: 'https://remote.example/v1' },
    { text: 'hello', fetch: () => { throw Error('must not send'); } }));
  await assert.rejects(sandbox.Providers.speakLocal(creds, { text: '你好', fetch: async () => ({ ok: false, status: 503 }) }), /503/);
  console.log('MAC LOCAL: ALL PASS (new profile, restart ports, saved preferences, loopback TTS, no key, error response)');
})().catch(error => { console.error(error); process.exitCode = 1; });
