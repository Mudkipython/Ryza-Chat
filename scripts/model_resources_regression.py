import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from local_model_resources import check_model

class Resources(unittest.TestCase):
    def test_pinned_model_requires_size_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'desktop').mkdir();(root/'.runtime/models').mkdir(parents=True)
            model=root/'.runtime/models/test.gguf';model.write_bytes(b'GGUFfixture')
            preset={'llm':{'filename':'test.gguf','size':model.stat().st_size,'sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'label':'test'}}
            (root/'desktop/model-manifest.json').write_text(json.dumps(preset))
            self.assertEqual(check_model(root),preset)
            model.write_bytes(b'GGUFmutated')
            with self.assertRaisesRegex(RuntimeError,'SHA256'):check_model(root)
            model.unlink()
            with self.assertRaisesRegex(RuntimeError,'test'):check_model(root)

if __name__=='__main__':unittest.main()
