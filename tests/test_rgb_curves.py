"""The R / G / B curve model (tests/rgb_curves.py) against the OM-3 project's model, and the cell format."""
import random
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rgb_curves as rc  # noqa: E402

OM3 = Path('/home/user/androidfanman/caduceus-om3/research/rgbcurves/model.py')


class RgbCurves(unittest.TestCase):
    def test_pack_round_trip(self):
        for v in ([0] * 5, [7, -7, 3, -1, 0], [-7] * 5, [7] * 5):
            self.assertEqual(rc.unpack(rc.pack(v)), v)
        self.assertEqual(rc.unpack(0), [0] * 5)
        self.assertEqual(rc.unpack(0x00012345), [0] * 5, 'untagged is flat')
        self.assertEqual(rc.unpack(rc.TAG << 24 | 8), [-7, 0, 0, 0, 0], '-8 reads as -7')

    def test_ends_and_points(self):
        for v in ([7, 0, 0, 0, 0], [0, 0, -7, 0, 0], [0, 2, 3, 4, 5], [-7, 7, -7, 7, -7]):
            d = rc.deltas(rc.pack(v))
            self.assertEqual(d[0], 48 * v[0])
            for j in (1, 2, 3):
                self.assertEqual(d[64 * j], 48 * v[j], f'point {j} of {v}')
        self.assertEqual(rc.deltas(rc.pack([0] * 5)), [0] * 256)

    def test_shift_form_matches(self):
        """rgb.s's shift form (s = 64 (k & 63), d = 4 dY, A = m >> 2) equals the model at t = 16 k."""
        rng = random.Random(5)
        for _ in range(300):
            v = [rng.randint(-7, 7) for _ in range(5)]
            Y = [48 * x for x in v]
            d = [4 * (Y[i + 1] - Y[i]) for i in range(4)]
            m = [d[0]] + [0] * 3 + [d[3]]
            for i in range(1, 4):
                a, b = d[i - 1], d[i]
                m[i] = 0 if a == 0 or b == 0 or (a < 0) != (b < 0) else rc.tdiv(2 * a * b, a + b)
            out = []
            for k in range(256):
                i, s = k >> 6, 64 * (k & 63)
                s2 = s * s >> 12
                s3 = s2 * s >> 12
                out.append(((2 * s3 - 3 * s2 + 4096) * Y[i] + (s3 - 2 * s2 + s) * (m[i] >> 2)
                            + (3 * s2 - 2 * s3) * Y[i + 1] + (s3 - s2) * (m[i + 1] >> 2)) >> 12)
            self.assertEqual(out, rc.deltas(rc.pack(v)), v)

    @unittest.skipUnless(OM3.is_file(), 'the OM-3 checkout is not here')
    def test_against_om3_model(self):
        ns = {}
        exec(compile(OM3.read_text(), str(OM3), 'exec'), ns)
        rng = random.Random(7)
        for _ in range(200):
            v = [rng.randint(-7, 7) for _ in range(5)]
            p = ns['prm']([v[0], 0, v[1], v[2], v[3], v[4]])
            self.assertEqual([ns['d_at'](p, 16 * k) for k in range(256)], rc.deltas(rc.pack(v)), v)


if __name__ == '__main__':
    unittest.main()
