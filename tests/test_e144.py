import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from om5i_donor_patch import PATCH, build, adapt_main, donor_main_packing
from oly_container import parse, reconstruct, replace_payload, sha256
from oly_compress import repack_image


class RecipientTests(unittest.TestCase):
    def test_default_donor_and_bad_input(self):
        self.assertEqual(PATCH, ROOT / 'firmware/om5ii')
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            bad = folder / 'bad.bin'; bad.write_bytes(b'not a firmware')
            with self.assertRaisesRegex(ValueError, 'pinned official'):
                build(bad, bad, folder / 'output')
            self.assertFalse((folder / 'output').exists())
            with self.assertRaisesRegex(ValueError, 'must be new'):
                build(bad, bad, folder)

    def test_relocation_preimages(self):
        with self.assertRaisesRegex(ValueError, 'Unexpected donor bytes'):
            adapt_main(bytes(0x1800000), bytes(0x1800000))

    @unittest.skipUnless(all(os.environ.get(k) for k in ('OM5I_STOCK', 'OM5_STOCK', 'OM5I_BUILD', 'OM5II_BUILD')),
                         'set stock and build paths for E144 output checks')
    def test_built_output(self):
        folder = Path(os.environ['OM5I_BUILD'])
        donor_folder = Path(os.environ['OM5II_BUILD'])
        report = json.loads((folder / 'build.json').read_text())
        self.assertFalse(report['camera_tested'])
        self.assertFalse(report['hardware_compatibility_established'])
        self.assertIsNone(report['install'])
        self.assertFalse((folder / 'install').exists())
        stock = Path(os.environ['OM5I_STOCK']).read_bytes()
        self.assertEqual(stock, (folder / 'restore-stock/DCOLYMP/E1449999.BIN').read_bytes())
        blocks = parse(stock)
        donor = {b.kind: b for b in parse(Path(os.environ['OM5_STOCK']).read_bytes())}
        main = (folder / 'decoded/0100.bin').read_bytes()
        feature = (donor_folder / 'decoded/0100.bin').read_bytes()
        spec = json.loads((ROOT / 'firmware/om5ii/patch.json').read_text())
        for row in spec['ranges']:
            if row['component'] == '0x100' and 'address' in row:
                at = int(row['address'], 16) - 0x60021020
                self.assertEqual(main[at:at + row['bytes']], feature[at:at + row['bytes']], row['name'])
        rebuilt = []
        for b in blocks:
            data = (folder / 'decoded' / f'{b.kind:04x}.bin').read_bytes()
            if b.kind == 0x100:
                data = repack_image(donor[b.kind].payload, data, **donor_main_packing(spec))
            self.assertEqual(len(data), len(b.payload))
            self.assertEqual(sha256(data), report['components'][hex(b.kind)]['sha256'])
            if b.kind == 0x10e:
                self.assertEqual(data, b.payload)
            rebuilt.append(replace_payload(b, data))
        package = reconstruct(rebuilt)
        self.assertEqual(len(package), len(stock))
        self.assertEqual(sha256(package), report['package_sha256'])
        for before, after in zip(blocks, parse(package)):
            self.assertEqual(before.header, after.header)
        self.assertEqual(report['common_resources']['unchanged_leaf_records'], 557)
        self.assertEqual(len(report['pictures']['records']), 116)


if __name__ == '__main__':
    unittest.main()
