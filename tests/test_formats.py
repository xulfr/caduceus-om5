import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from card.mklooks import looks_bin


def js(**request):
    out = subprocess.run(['node', str(ROOT / 'tests/looks_bridge.cjs')], input=json.dumps(request),
                         text=True, capture_output=True, check=True)
    return json.loads(out.stdout)


class LooksTests(unittest.TestCase):
    def test_library_and_starter(self):
        library = json.loads((ROOT / 'looklab/films.json').read_text())['films']
        for i in range(0, len(library), 10):
            films = library[i:i + 10]
            data = looks_bin(films)
            self.assertEqual(data.hex(), js(films=films)['result'])
            self.assertEqual(data.hex(), js(films=js(read=data.hex())['result'])['result'])
        by_name = {f['name']: f for f in library}
        starter = [by_name[n] for n in json.loads((ROOT / 'card/starter.json').read_text())]
        self.assertEqual(looks_bin(starter), (ROOT / 'releases/v0.1.0-alpha1/LOOKS.BIN').read_bytes())

    def test_signed_boundaries_and_defaults(self):
        rng = random.Random(148)
        for count in (1, 3, 10):
            films = []
            for i in range(count):
                f = {'name': f'Film {i}'}
                for key, limit in [('hue', 7), ('light', 7), ('sat', 5)]:
                    f[key] = [-limit, limit] + [rng.randint(-limit, limit) for _ in range(10)]
                f.update(wb=[-7, 7], contrast=-2, sharpness=2, shading=-5, shadows=-7, midtones=7, highlights=0)
                films.append(f)
            self.assertEqual(looks_bin(films).hex(), js(films=films)['result'])
        self.assertEqual(looks_bin([{'name': 'Default'}]).hex(), js(films=[{'name': 'Default'}])['result'])

    def test_writers_reject_invalid_input(self):
        for bad in ({'name': ''}, {'name': ' thirteen chars'}, {'name': ' Film'}, {'name': 'é'}, {'name': '@A034@'},
                    {'sat': [6] * 12}, {'hue': [0] * 13}, {'light': [0.5] * 12},
                    {'contrast': True}, {'shading': 6}, {'wb': []}, {'wb': [8, 0]}):
            with self.subTest(bad=bad):
                films = [dict(name='Test', **bad)] if 'name' not in bad else [bad]
                with self.assertRaises((ValueError, UnicodeError)):
                    looks_bin(films)
                self.assertIn('error', js(films=films))
        for films in ([], [{'name': 'Test'}] * 11):
            with self.assertRaises(ValueError):
                looks_bin(films)
            self.assertIn('error', js(films=films))

    def test_reader_rejects_corruption(self):
        good = looks_bin([{'name': 'Test'}])
        for at, value in [(0, 0), (4, 0), (12, 2), (14, 11), (32, 8), (32 + 36, 2), (32 + 37, 8), (96, 64), (96, 31), (96, 127)]:
            bad = bytearray(good)
            bad[at] = value
            if at >= 12:
                struct.pack_into('<I', bad, 8, zlib.crc32(bad[12:]))
            self.assertIn('error', js(read=bad.hex()), at)
        bad = bytearray(good); bad[-1] ^= 1
        self.assertIn('error', js(read=bad.hex()))
        self.assertIn('error', js(read=good[:-1].hex()))
        # Padding inside the twelve displayed bytes is also checked by firmware.
        bad = bytearray(good); bad[101] = 64
        struct.pack_into('<I', bad, 8, zlib.crc32(bad[12:]))
        self.assertIn('error', js(read=bad.hex()))


if __name__ == '__main__':
    unittest.main()
