"""R / G / B curves (roadmap phase 4): the integer model the card block's rgb.s builds into the delta tables.

Derived from the OM-3 project's research/rgbcurves/model.py (androidfanman/caduceus-om3, try/v0.41-beta4,
Apache-2.0, Copyright 2026 androidfanman): 5 points at 0 / 25 / 50 / 75 / 100 % of the 12-bit output, offsets
-7..+7 steps of 48, a monotone cubic (Hermite, Fritsch-Butland tangents) in Q12 integer maths, truncating division
as the CPU's div. Here a channel's 5 offsets are used directly (the OM-3 keeps 6 values, the second unused), and the
curve is evaluated at t = 16 k for the split-tone delta tables (one entry per 16 output levels).

Cells: channel c of Color Profile p is IDS[3p + c] (working cell, 32 bits): TAG << 24 | offset j in bits
4j..4j+3 (two's complement); untagged = flat."""
X = [0, 1024, 2048, 3072, 4096]
H = [X[i + 1] - X[i] for i in range(4)]
INV = [(1 << 24) // h for h in H]
STEP = 48
TAG = 0xC5
IDS = [985, 986, 987, 1030, 1031, 1032, 1002, 1006, 1010]


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def prm(v):
    """5 offsets -> (Y[5], A[4], B[4]), as the OM-3 model's prm on its points."""
    Y = [max(-7, min(7, x)) * STEP for x in v]
    d = [tdiv((Y[i + 1] - Y[i]) << 12, H[i]) for i in range(4)]
    m = [d[0]] + [0] * 3 + [d[3]]
    for i in range(1, 4):
        a, b = d[i - 1], d[i]
        m[i] = 0 if a == 0 or b == 0 or (a < 0) != (b < 0) else tdiv(2 * a * b, a + b)
    A = [(H[i] * m[i]) >> 12 for i in range(4)]
    B = [(H[i] * m[i + 1]) >> 12 for i in range(4)]
    return Y, A, B


def d_at(p, t):
    Y, A, B = p
    i = min(3, t >> 10)
    s = ((t - X[i]) * INV[i]) >> 12
    s2 = (s * s) >> 12
    s3 = (s2 * s) >> 12
    h00 = 2 * s3 - 3 * s2 + 4096
    h10 = s3 - 2 * s2 + s
    h01 = 3 * s2 - 2 * s3
    h11 = s3 - s2
    return (h00 * Y[i] + h10 * A[i] + h01 * Y[i + 1] + h11 * B[i]) >> 12


def pack(v):
    """5 offsets -7..+7 -> the cell value."""
    if len(v) != 5 or any(not -7 <= x <= 7 for x in v):
        raise ValueError('five offsets -7..+7')
    return TAG << 24 | sum((x & 15) << (4 * j) for j, x in enumerate(v))


def unpack(cell):
    """cell -> 5 offsets; untagged = flat."""
    if cell >> 24 & 255 != TAG:
        return [0] * 5
    out = []
    for j in range(5):
        n = cell >> (4 * j) & 15
        out.append(max(-7, n - 16 if n >= 8 else n))
    return out


def deltas(cell):
    """the 256 entries rgb.s adds to one channel's delta table."""
    v = unpack(cell)
    if not any(v):
        return [0] * 256
    p = prm(v)
    return [d_at(p, 16 * k) for k in range(256)]
