"""Language-conditioning contract for the optional GPT-SoVITS adapter."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import numpy as np
import soundfile as sf
spec=importlib.util.spec_from_file_location('adapter',Path(__file__).with_name('sovits_speech.py'))
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class Contracts(unittest.TestCase):
    def test_reference_and_target_languages_are_independent(self):
        calls=[]
        class Engine:
            def run(self,inputs):
                calls.append(inputs)
                yield 32000,np.zeros(3200,dtype='int16')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'ryza-reference.txt').write_text('こんにちは。')
            for language,expected in [('zh','all_zh'),('ja','all_ja')]:
                blob=adapter.synthesize(Engine(),root,'你好' if language=='zh' else 'こんにちは',language)
                self.assertEqual(calls[-1]['text_lang'],expected)
                self.assertEqual(calls[-1]['prompt_lang'],'all_ja')
                self.assertEqual(calls[-1]['prompt_text'],'こんにちは。')
                audio,rate=sf.read(io.BytesIO(blob));self.assertEqual(rate,32000)
                self.assertEqual(len(audio),3200)
    def test_voice_only_does_not_condition_on_japanese_text(self):
        calls=[]
        class Engine:
            def run(self,inputs):
                calls.append(inputs)
                yield 32000,np.zeros(3200,dtype='int16')
        with tempfile.TemporaryDirectory() as directory:
            adapter.synthesize(Engine(),Path(directory),'你好','zh','03-voice-only')
        self.assertEqual(calls[0]['prompt_text'],'')
        self.assertEqual(calls[0]['text_lang'],'all_zh')

    def test_reference_profile_is_allowlisted(self):
        with self.assertRaises(ValueError):adapter.synthesize(None,Path('.'),'你好','zh','../../secret')

    def test_unknown_language_rejected(self):
        with self.assertRaises(ValueError):adapter.synthesize(None,Path('.'),'test','bad')
if __name__=='__main__':unittest.main()
