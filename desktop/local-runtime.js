'use strict';
const fs = require('fs');
const path = require('path');
const net = require('net');
const { spawn } = require('child_process');
const { randomBytes } = require('crypto');
const manifest = require('./model-manifest.json');

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.on('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}
async function waitReady(url, child, timeout = 120000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    if (child.exitCode !== null || child.spawnError) throw new Error('本地引擎启动失败，请查看日志。');
    try {
      const r = await fetch(url, { signal: AbortSignal.timeout(2000) });
      if (r.ok) return;
    } catch (_) {}
    await new Promise(r => setTimeout(r, 300));
  }
  throw new Error('本地引擎启动超时，请查看日志。');
}
class LocalRuntime {
  constructor(root, logDir) { this.root = root; this.logDir = logDir; this.children = []; }
  launch(exe, args, name, env = {}) {
    fs.mkdirSync(this.logDir, { recursive: true });
    const fd = fs.openSync(path.join(this.logDir, name + '.log'), 'a');
    const child = spawn(exe, args, { env: { ...process.env, ...env }, stdio: ['ignore', fd, fd] });
    fs.closeSync(fd);
    child.on('error', error => { child.spawnError = error; });
    this.children.push(child);
    return child;
  }
  async start() {
    const preset = manifest.llm;
    const binDir = path.join(this.root, manifest.engine.directory);
    const model = path.join(this.root, 'models', preset.filename);
    if (!fs.existsSync(model) || fs.statSync(model).size !== preset.size) {
      throw new Error('缺少完整的 ' + preset.label + ' 本地模型，请运行试玩目录内的准备脚本。');
    }
    const llmPort = await freePort();
    const sessionKey = randomBytes(24).toString('hex');
    const llm = this.launch(path.join(binDir, 'llama-server'), [
      '-m', model, '--host', '127.0.0.1', '--port', String(llmPort),
      '-c', String(preset.contextWindow), '-ngl', '99', '-t', '4', '--parallel', '1',
      '--alias', preset.alias, '--jinja', '--reasoning', 'off',
      '--chat-template-kwargs', JSON.stringify(preset.chatTemplateKwargs),
      '--top-k', String(preset.sampling.topK), '--top-p', String(preset.sampling.topP),
      '--presence-penalty', String(preset.sampling.presencePenalty),
      '--api-key', sessionKey, '--cors-origins', 'ryza://app'
    ], 'llm');
    let sovitsUrl = '';
    if (fs.existsSync(path.join(this.root, 'sovits-ready.json'))) {
      const sovitsPort = await freePort();
      sovitsUrl = `http://127.0.0.1:${sovitsPort}`;
      const sovits = this.launch(path.join(this.root, 'sovits-venv/bin/python'), [
        path.join(this.root, 'sovits_speech.py'), '--root', this.root, '--port', String(sovitsPort)
      ], 'sovits', { HF_HUB_OFFLINE: '1', TRANSFORMERS_OFFLINE: '1', PYTHONUNBUFFERED: '1' });
      await waitReady(sovitsUrl + '/health', sovits);
    }
    let cosyUrl = '';
    const cosyFiles = ['cosyvoice-venv/bin/python', 'cosyvoice3-4bit/model.safetensors',
      'cosyvoice-s3/model.safetensors', 'cosyvoice_speech.py'];
    if (cosyFiles.every(file => fs.existsSync(path.join(this.root, file)))) {
      const cosyPort = await freePort();
      cosyUrl = `http://127.0.0.1:${cosyPort}`;
      const cosy = this.launch(path.join(this.root, 'cosyvoice-venv/bin/python'), [
        path.join(this.root, 'cosyvoice_speech.py'), '--root', this.root, '--port', String(cosyPort)
      ], 'cosyvoice', { HF_HUB_OFFLINE: '1', TRANSFORMERS_OFFLINE: '1',
        HF_HOME: path.join(this.root, 'cosyvoice-cache'), PYTHONUNBUFFERED: '1' });
      await waitReady(cosyUrl + '/health', cosy);
    }
    const speechPort = await freePort();
    const python = path.join(this.root, 'voice-venv', 'bin', 'python');
    const speech = this.launch(fs.existsSync(python) ? python : '/usr/bin/python3', [
      path.join(this.root, 'local_speech.py'), '--port', String(speechPort),
      '--root', this.root
    ], 'speech', { HF_HOME: path.join(this.root, 'huggingface'), HF_HUB_OFFLINE: '1',
                   TOKENIZERS_PARALLELISM: 'false', PYTHONUNBUFFERED: '1', RYZA_SOVITS_URL: sovitsUrl, RYZA_COSYVOICE_URL: cosyUrl });
    await Promise.all([waitReady(`http://127.0.0.1:${llmPort}/health`, llm),
      waitReady(`http://127.0.0.1:${speechPort}/health`, speech)]);
    const speechHealth = await (await fetch(`http://127.0.0.1:${speechPort}/health`)).json();
    if (!speechHealth.asr_ready) {
      throw new Error('本地识别模型未就绪：' + (speechHealth.model_error || '请运行准备脚本。'));
    }
    return {
      llm: { baseUrl: `http://127.0.0.1:${llmPort}/v1`, model: preset.alias, apiKey: sessionKey,
        thinking: 'off', thinkingStyle: 'none', contextWindow: preset.contextWindow, maxTokens: 400,
        historyTurns: 6, temperature: 0.7, lang: 'zh' },
      tts: { provider: 'localSpeech', mode: 'preset', lang: 'ja',
        localSpeechBaseUrl: `http://127.0.0.1:${speechPort}/v1`, localSpeechVoice: 'ryza' },
      stt: { provider: 'whisper', engine: 'capture', model: 'ryza-asr',
        baseUrl: `http://127.0.0.1:${speechPort}/v1`, apiKey: '' },
      voice: { lang: 'ja' },
      app: { lang: 'zh', voice: true, stt: 'off', calmMotion: false, motionMode: 'gentle', localModel: preset.label, kokoroReady: !!speechHealth.kokoro_ready, localAsr: speechHealth.asr_engine || 'whisper', sentenceSpeech: true, cosyReady: !!cosyUrl, sovitsReady: !!sovitsUrl },
      chara: { extra: '请用自然简短的中文交流；自称“我”，不要在中文对白夹杂日语。每次约两三句话。' }
    };
  }
  stop() {
    for (const child of this.children) {
      if (child.exitCode === null) {
        child.kill('SIGTERM');
        const timer = setTimeout(() => { if (child.exitCode === null) child.kill('SIGKILL'); }, 2000);
        timer.unref();
      }
    }
    this.children = [];
  }
}
module.exports = { LocalRuntime, freePort, waitReady };
