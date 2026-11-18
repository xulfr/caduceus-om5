"""Small synthetic fixtures only: never require or embed stock firmware."""
import contextlib
import io
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import space_map as sm


class SpaceMapTests(unittest.TestCase):
    def fixture(self):
        base = 0x60021020
        image = bytearray(b'\x55' * 256)
        image[32:48] = b'\xff' * 16
        image[64:80] = b'\x00' * 16
        image[128:144] = b'\xff' * 16  # Outside the native load: never free.
        # Unaligned, uncached pointer from resident boot into the ZERO run.
        struct.pack_into('<I', image, 3, base + 0x40000000 + 68)
        regions = [dict(id=1, start=base+16, end=base+96, source=0x40001010, compressed=0)]
        manifest = {'ranges': [dict(name='ext2', component='0x100', address=hex(base+36), bytes=4)]}
        return image, regions, manifest

    def test_bounds_alias_pointer_and_usage(self):
        image, regions, manifest = self.fixture()
        result = sm.build_map(image, regions, manifest)
        self.assertEqual(len(result['gaps']), 2)
        self.assertEqual(result['gaps'][0]['candidate_free_bytes'], 12)
        self.assertEqual(result['gaps'][1]['candidate_free_bytes'], 0)
        self.assertEqual(result['gaps'][1]['pointer_refs'][0]['from'], sm.BASE+3)
        self.assertEqual(result['sections'][0]['file_offset'], 48)
        self.assertEqual(result['sections'][0]['patch_bytes_used'], 4)
        self.assertEqual(result['regions'][0]['candidate_free_bytes'], 8)
        self.assertLessEqual(len(sm.summary(result).splitlines()), 40)

    def test_ref_to_middle_rejects_whole_run(self):
        image, regions, manifest = self.fixture()
        struct.pack_into('<I', image, 9, sm.BASE+42)
        result = sm.build_map(image, regions, manifest)
        self.assertEqual(result['sections'][0]['candidate_free_bytes'], 0)

    def test_manifest_outside_load_is_error(self):
        image, regions, manifest = self.fixture()
        manifest['ranges'][0]['address'] = hex(sm.BASE+128)
        with self.assertRaisesRegex(ValueError, 'outside native'):
            sm.build_map(image, regions, manifest)

    def test_overlap_usage_is_counted_once(self):
        image, regions, manifest = self.fixture()
        manifest['ranges'].append(dict(name='hook', component='0x100', address=hex(sm.BASE+38), bytes=4))
        self.assertEqual(sm.build_map(image, regions, manifest)['sections'][0]['patch_bytes_used'], 6)

    def test_optional_built_changes_and_size(self):
        image, regions, manifest = self.fixture()
        built = bytearray(image)
        built[36] = 17
        built[20] = 17
        result = sm.build_map(image, regions, manifest, built=built)
        self.assertEqual(result['sections'][0]['changed_bytes'], 2)
        self.assertEqual(result['sections'][0]['changes_outside_manifest'], 1)
        with self.assertRaisesRegex(ValueError, 'size differs'):
            sm.build_map(image, regions, manifest, built=built[:-1])

    def test_missing_stock_fails_clearly(self):
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(sm.main(['--stock', '__missing_e148__.BIN']), 1)
        self.assertIn('stock firmware unavailable', errors.getvalue())

    def test_wrong_stock_hash(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'stock.bin'
            path.write_bytes(b'not firmware')
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                sm.read_stock(path)


if __name__ == '__main__':
    unittest.main()
