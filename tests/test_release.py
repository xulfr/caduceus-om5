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

    def test_failed_releases_are_refused_before_file_access(self):
        # alpha5 boot-looped on a camera (15 Nov 2026); alpha1-4 share its startup code.
        for source in sorted((ROOT / 'releases').glob('*/patch.json')):
            name = source.parent.name
            self.assertTrue(json.loads(source.read_text()).get('blocked'), name)
            result = subprocess.run([sys.executable, str(ROOT / 'patch.py'), '--release', name,
                                     '--stock', 'missing-stock.bin', '--i-accept-untested'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Do not flash it', result.stdout)
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
