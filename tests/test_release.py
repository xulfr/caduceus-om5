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
            if name not in {f'v0.1.0-alpha{n}' for n in range(1, 6)}:
                continue
            self.assertTrue(json.loads(source.read_text()).get('blocked'), name)
            result = subprocess.run([sys.executable, str(ROOT / 'patch.py'), '--release', name,
                                     '--stock', 'missing-stock.bin', '--i-accept-untested'],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('Do not flash it', result.stdout)
            self.assertNotIn('Traceback', result.stderr)

    def test_stream_length_rule(self):
        # Loader facts and the alpha5 case: research/OM5II-STREAM-LENGTH-2026-11-15.md
        sys.path.insert(0, str(ROOT / 'tools'))
        import oly_compress as oc
        self.assertIsNotNone(oc.length_fault(2502656))            # alpha5 section 7: 611 * 4096
        self.assertIsNotNone(oc.length_fault(2048 * 5 + 2017))    # loader would drop the last byte
        for good in (2250095, 2501620, 764647, 2254191, 2505716, 764680):
            self.assertIsNone(oc.length_fault(good), good)
        rel = json.loads((ROOT / 'releases/v0.1.0-alpha6/patch.json').read_text())
        self.assertEqual(rel['main']['stream_length'], 'stock-page')
        self.assertIn('lz4_recipe', rel['resource'])
        self.assertFalse(rel['camera_tested'])

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
