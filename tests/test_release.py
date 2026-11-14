import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import patch


class ReleaseTests(unittest.TestCase):
    def test_wrong_stock_is_rejected(self):
        rel = json.loads((ROOT / 'releases/v0.1.0-alpha1/patch.json').read_text())
        with self.assertRaises(patch.Refuse):
            patch.build(rel, b'wrong camera')

    def test_untested_gate_precedes_file_access(self):
        result = subprocess.run([sys.executable, str(ROOT / 'patch.py'), '--stock', 'missing-stock.bin'],
                                input='NO\n', text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('stopped; nothing was written', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    @unittest.skipUnless(os.environ.get('OM5_STOCK'), 'set OM5_STOCK for full firmware reproduction')
    def test_release_reproduction(self):
        stock = Path(os.environ['OM5_STOCK']).read_bytes()
        for source in sorted((ROOT / 'releases').glob('*/patch.json')):
            rel = json.loads(source.read_text())
            self.assertFalse(rel['camera_tested'])
            image = patch.build(rel, stock)
            self.assertEqual(len(image), rel['package']['bytes'])
            self.assertEqual(patch.sha256(image), rel['package']['sha256'])
            bad = copy.deepcopy(rel)
            bad['main']['edits'][0]['before_sha256'] = '0' * 64
            with self.assertRaises(patch.Refuse):
                patch.build(bad, stock)


if __name__ == '__main__':
    unittest.main()
