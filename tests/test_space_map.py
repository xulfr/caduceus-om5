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
        self.assertEqual(result['gaps'][1]['candidate_free_bytes'], 15)
        self.assertEqual(result['gaps'][1]['reference_ranges'], [
            {'start': sm.BASE+68, 'end': sm.BASE+69, 'pointee_extent_known': False}])
        self.assertEqual(result['gaps'][1]['pointer_refs'][0]['from'], sm.BASE+3)
        self.assertEqual(result['sections'][0]['file_offset'], 48)
        self.assertEqual(result['sections'][0]['patch_bytes_used'], 4)
        self.assertEqual(result['regions'][0]['candidate_free_bytes'], 23)
        self.assertLessEqual(len(sm.summary(result).splitlines()), 40)

    def test_ref_to_middle_reserves_only_target_and_reports_unknown_extent(self):
        image, regions, manifest = self.fixture()
        struct.pack_into('<I', image, 9, sm.BASE+42)
        result = sm.build_map(image, regions, manifest)
        self.assertEqual(result['sections'][0]['candidate_free_bytes'], 26)

    def test_ref_inside_used_bytes_does_not_erase_free_tail(self):
        image, regions, manifest = self.fixture()
        struct.pack_into('<I', image, 9, sm.BASE+38)
        result = sm.build_map(image, regions, manifest)
        self.assertEqual(result['gaps'][0]['candidate_free_bytes'], 12)
        self.assertEqual(result['regions'][0]['candidate_free_bytes'], 23)

    def test_interval_subtraction_merges_clips_and_deduplicates(self):
        self.assertEqual(sm.subtract_intervals(10, 30, [(8, 12), (11, 14), (20, 22), (20, 22), (28, 40)]),
                         [(14, 20), (22, 28)])

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

    def test_compressed_span_does_not_authorize_its_extra_tail(self):
        # A 96-byte synthetic stream occupies a reserved span, but the native
        # loader selects only its first 32 bytes. Its remaining FF is NOT free.
        import oly_compress
        raw = b'\x55' * 16 + b'\xff' * 80
        packed = oly_compress._encode(raw)
        # Literal-only encoding needs a larger reservation than this tiny raw
        # span; use a normal offset-1 match followed by five final literals.
        packed = oly_compress._encode(raw[:17], 1, 74) + oly_compress._encode(raw[-5:])
        stored = bytearray(b'\x55' * 256)
        stored[128:144] = oly_compress.MAGIC
        struct.pack_into('<II', stored, 144, len(packed), len(raw))
        stored[152:160] = bytes(8)
        stored[160:160+len(packed)] = packed
        image = oly_compress.expand_image(stored)
        regions = [dict(id=1, start=sm.BASE+128, end=sm.BASE+160, source=0x40001000, compressed=1)]
        result = sm.build_map(image, regions, {'ranges': []})
        self.assertEqual(result['sections'][0]['candidate_free_bytes'], 16)
        self.assertEqual(result['gaps'][0]['end'], sm.BASE+160)
        self.assertEqual(len(image), 256)


if __name__ == '__main__':
    unittest.main()
