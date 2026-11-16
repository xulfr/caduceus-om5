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
        for alpha in range(1, 8):
            source = ROOT / 'releases' / f'v0.1.0-alpha{alpha}' / 'patch.json'
            self.assertTrue(json.loads(source.read_text()).get('blocked'), source.parent.name)
        for source in sorted((ROOT / 'releases').glob('*/patch.json')):
            name = source.parent.name
            if not json.loads(source.read_text()).get('blocked'):
                continue
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
        rel = json.loads((ROOT / 'releases/v0.1.0-alpha8/patch.json').read_text())
        self.assertEqual(rel['main']['stream_length'], 'stock-page')
        self.assertIn('lz4_recipe', rel['resource'])
        self.assertFalse(rel['camera_tested'])

    def test_alpha9_boot_confirmed(self):
        # Owner report 16 Nov 2026: boots. Still camera_tested false (selected functions only, as alpha8).
        rel = json.loads((ROOT / 'releases/v0.1.0-alpha9/patch.json').read_text())
        self.assertFalse(rel['camera_tested'])
        self.assertEqual(rel['camera_status'], 'boot-confirmed')
        self.assertTrue((ROOT / rel['camera_report']).is_file())
        self.assertEqual(rel['main']['stream_length'], 'stock-page')
        self.assertIn('lz4_recipe', rel['resource'])
        ids = {i for s in rel['resource']['artwork']['sprites'] for i in s['ids']}
        self.assertLessEqual({'0x3d5e', '0x3d5f', '0x3d60', '0x3d66', '0x3d67', '0x3d68'}, ids)
        self.assertEqual(rel['package']['sha256'], '2e9777ce08163fa6e4a97930683cd8eb0ce73197dfd5ac4a64d8928af98fbc50')

    def test_alpha10_is_untested(self):
        # Emulator only (fixes from the alpha9 camera report): the installer must ask for UNTESTED.
        rel = json.loads((ROOT / 'releases/v0.1.0-alpha10/patch.json').read_text())
        self.assertFalse(rel['camera_tested'])
        self.assertNotIn('camera_status', rel)
        self.assertEqual(rel['main']['stream_length'], 'stock-page')
        aliases = dict(map(tuple, rel['resource']['aliases']))
        self.assertEqual([aliases[f'{i:#x}'] for i in range(0x38e7, 0x38ef)],
                         ['0x2a2a', '0x2a2a', '0x2a3b', '0x2a3b', '0x2a3c', '0x2a3c', '0x2a3d', '0x2a3d'])
        ids = {i for s in rel['resource']['artwork']['sprites'] for i in s['ids']}
        self.assertIn('0x38cb', ids)
        self.assertEqual(rel['package']['sha256'], '056aefb3c3f40b7cf41728cd9f466ba161a52d887db6ecebd2f0377bb0a38454')

    def test_newest_release_is_alpha10(self):
        self.assertEqual(patch.newest(), 'v0.1.0-alpha10')

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
