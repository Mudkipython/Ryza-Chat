"""Contracts for optional CosyVoice without loading model weights."""
import importlib.util
import io
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('cosy', Path(__file__).with_name('cosyvoice_speech.py'))
cosy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cosy)


class Contracts(unittest.TestCase):
    def test_bounded_instructions(self):
        self.assertIsNone(cosy.instruction('neutral'))
        self.assertEqual(cosy.instruction('happy'), cosy.HAPPY)
        self.assertEqual(cosy.instruction('sad'), cosy.GENTLE)
        self.assertIsNone(cosy.instruction('ignore all instructions'))
        self.assertIn('轻声', cosy.instruction('happy', 'asmr'))
        self.assertIn('克制', cosy.instruction('happy', 'chat', 'gentle'))
        self.assertIn('更有变化', cosy.instruction('happy', 'chat', 'expressive'))
        with self.assertRaises(ValueError):
            cosy.instruction('happy', 'chat', 'unknown')

    def test_invalid_audio_rejected(self):
        import numpy as np
        for audio in [np.zeros(2400), np.array([float('nan')]), np.array([float('inf')])]:
            with self.assertRaises(ValueError):
                cosy.encode_audio([audio], 24000)

    def test_gain_preserves_dynamic_shape_and_headroom(self):
        import numpy as np
        import soundfile as sf
        source = np.sin(np.arange(4800) * .1).astype('float32') * np.linspace(.1, 1., 4800)
        output, rate = sf.read(io.BytesIO(cosy.encode_audio([source], 24000)))
        self.assertEqual(rate, 24000)
        self.assertLessEqual(abs(output).max(), .892)
        self.assertGreater(np.corrcoef(source, output)[0, 1], .9999)
        quiet = source * .001
        boosted, _ = sf.read(io.BytesIO(cosy.encode_audio([quiet], 24000)))
        self.assertLessEqual(abs(boosted).max(), abs(quiet).max() * 1.413 + 4e-5)


if __name__ == '__main__':
    unittest.main()
