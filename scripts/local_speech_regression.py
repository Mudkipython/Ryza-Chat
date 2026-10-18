"""Contract tests for the local audio service; models are not loaded here."""
import importlib.util
import io
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('local_speech', Path(__file__).with_name('local_speech.py'))
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)


class AudioContracts(unittest.TestCase):
    def test_startup_does_not_import_or_load_tts(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as root:
            service.prepare_models(root)
            self.assertIsNone(service.CLONE)
            self.assertFalse(service.model_status()['clone_ready'])
            self.assertFalse(service.model_status()['clone_loaded'])
            Path(root, 'qwen3-asr').mkdir()
            Path(root, 'qwen3-asr/model.safetensors').touch()
            self.assertTrue(service.model_status()['asr_ready'])
            with self.assertRaisesRegex(RuntimeError, 'Qwen3-TTS'):
                service.load_clone()

    def test_clone_loads_once_and_health_distinguishes_loaded(self):
        import sys
        from tempfile import TemporaryDirectory
        from types import ModuleType
        from unittest.mock import Mock, patch
        fake = ModuleType('mlx_audio.tts.utils')
        fake.load_model = Mock(return_value=object())
        with TemporaryDirectory() as root:
            service.prepare_models(root)
            for name in ('qwen3-tts/model.safetensors',
                         'qwen3-tts/speech_tokenizer/model.safetensors',
                         'ryza-reference.wav', 'ryza-reference.txt'):
                target = Path(root, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.touch()
            self.assertTrue(service.model_status()['clone_ready'])
            self.assertFalse(service.model_status()['clone_loaded'])
            with patch.dict(sys.modules, {'mlx_audio.tts.utils': fake}):
                self.assertIs(service.load_clone(), service.load_clone())
            fake.load_model.assert_called_once()
            self.assertTrue(service.model_status()['clone_loaded'])
        service.CLONE = None

    def test_qwen_asr_receives_pcm_language_and_hotwords(self):
        import json
        import sys
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace, ModuleType
        from unittest.mock import Mock, patch
        import numpy as np
        import soundfile as sf
        fake = ModuleType('mlx_audio.stt.utils')
        model = SimpleNamespace(generate=Mock(return_value=SimpleNamespace(text='莱莎，去调合吧。')))
        fake.load_model = Mock(return_value=model)
        with TemporaryDirectory() as root:
            Path(root, 'qwen3-asr').mkdir()
            Path(root, 'qwen3-asr/model.safetensors').touch()
            Path(root, 'asr-profile.json').write_text(json.dumps({'engine':'qwen3','hotwords':{'zh':['莱莎','调合']}}))
            service.prepare_models(root)
            audio = io.BytesIO()
            sf.write(audio, np.ones(16000, dtype='float32') * 0.03, 16000, format='WAV')
            with patch.dict(sys.modules, {'mlx_audio.stt.utils':fake}):
                for language in ['zh','ja','en']:
                    self.assertEqual(service.transcribe(audio.getvalue(), language), '莱莎，去调合吧。')
            fake.load_model.assert_called_once()
            self.assertEqual([c.kwargs['language'] for c in model.generate.call_args_list], ['Chinese','Japanese','English'])
            self.assertEqual(model.generate.call_args_list[0].kwargs['hotwords'], ['莱莎','调合'])
            self.assertTrue(service.model_status()['asr_loaded'])
        service.ASR = None
        service.ASR_PROFILE = {'engine':'qwen3'}

    def test_multipart_keeps_binary_wav_exactly(self):
        binary = b'RIFF' + bytes(range(256)) * 5
        boundary = 'RyzaBoundary123'
        body = (b'--RyzaBoundary123\r\nContent-Disposition: form-data; name="language"\r\n\r\nzh\r\n'
                b'--RyzaBoundary123\r\nContent-Disposition: form-data; name="file"; filename="voice.wav"\r\n'
                b'Content-Type: audio/wav\r\n\r\n' + binary + b'\r\n--RyzaBoundary123--\r\n')
        audio, language = service.parse_multipart('multipart/form-data; boundary='+boundary, body)
        self.assertEqual(audio, binary)
        self.assertEqual(language, 'zh')

    def test_missing_audio_and_invalid_language_fail(self):
        with self.assertRaises(ValueError):
            service.parse_multipart('application/json', b'{}')
        with self.assertRaises(ValueError):
            service.parse_multipart('multipart/form-data; boundary=x',
                b'--x\r\nContent-Disposition: form-data; name="language"\r\n\r\n../../model\r\n'
                b'--x\r\nContent-Disposition: form-data; name="file"\r\n\r\nWAV\r\n--x--\r\n')

    def test_origins_are_local_only(self):
        for origin in ['', 'ryza://app', 'http://127.0.0.1:1234', 'http://localhost:8765']:
            self.assertTrue(service.allowed_origin(origin))
        for origin in ['https://evil.example', 'http://localhost.evil.example:8765', 'null']:
            self.assertFalse(service.allowed_origin(origin))

    def test_long_audio_rejected_before_model_inference(self):
        import numpy as np
        import soundfile as sf
        audio = io.BytesIO()
        sf.write(audio, np.zeros(16000*31, dtype='float32'), 16000, format='WAV')
        with self.assertRaisesRegex(ValueError, '30 seconds'):
            service.transcribe(audio.getvalue(), 'zh')

    def test_sovits_unconfigured_fails_without_cloud_or_silent_fallback(self):
        from unittest.mock import patch
        with patch.dict(service.os.environ, {'RYZA_SOVITS_URL':''}):
            with self.assertRaisesRegex(RuntimeError, 'GPT-SoVITS'):
                service.synthesize('你好', 'ryza_sovits', 'zh')
        with patch.dict(service.os.environ, {'RYZA_SOVITS_URL':'https://remote.example'}):
            with self.assertRaises(RuntimeError):
                service.synthesize('你好', 'ryza_sovits', 'zh')

    def test_silence_does_not_hallucinate(self):
        import numpy as np
        import soundfile as sf
        audio = io.BytesIO()
        sf.write(audio, np.zeros(16000, dtype='float32'), 16000, format='WAV')
        self.assertEqual(service.transcribe(audio.getvalue(), 'zh'), '')

    def test_cosy_forwarding_is_loopback_and_carries_emotion(self):
        from unittest.mock import patch, MagicMock
        import json
        with patch.dict(service.os.environ, {'RYZA_COSYVOICE_URL': 'https://remote.example'}):
            with self.assertRaises(RuntimeError):
                service.synthesize('你好', 'ryza_cosy', 'zh', 'happy')
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'local-wav'
        with patch.dict(service.os.environ, {'RYZA_COSYVOICE_URL': 'http://127.0.0.1:12345'}), patch.object(service, 'urlopen', return_value=response) as opened:
            audio, engine = service.synthesize('你好', 'ryza_cosy', 'zh', 'happy', 'chat')
            self.assertEqual(audio, b'local-wav')
            body = json.loads(opened.call_args.args[0].data)
            self.assertEqual(body['emotion'], 'happy')
            self.assertEqual(body['mode'], 'chat')
            self.assertEqual(engine, 'CosyVoice3 / MLX')
            with self.assertRaises(ValueError):
                service.synthesize('こんにちは', 'ryza_cosy', 'ja')


if __name__ == '__main__':
    unittest.main()
