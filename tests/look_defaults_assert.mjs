// POST module for tests/run_look_defaults.py: the Color Profile 1 values after a Hold OK reset.
// OM5_LOOK_EXPECT = JSON {film: index in tools/dev/films-test.json or null, sat0: value} (null: a slot with no look,
// whose reset keeps OM's default 0; sat0 is the colour that case changed on the wheel and did not reset).
import assert from 'node:assert/strict';
import fs from 'node:fs';

export default function(g) {
  const want = JSON.parse(process.env.OM5_LOOK_EXPECT);
  const films = JSON.parse(fs.readFileSync(new URL('../tools/dev/films-test.json', import.meta.url), 'utf8'));
  const R = (id) => g.__call(0x602f50f8, { d0: id, d1: 1 }).d0 >>> 0;
  const G = (id) => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const nib = (v, s) => ((v >> s) << 28) >> 28;
  const got = {
    pm: G(111),
    sat: [...Array(12).keys()].map((k) => G(928 + k)),
    hue: [...Array(12).keys()].map((k) => nib(R(928 + k) & 15, 0)),
    light: [...Array(12).keys()].map((k) => nib(R(928 + k) & 0xf0, 4)),
    contrast: G(908), sharpness: G(904), shading: G(912), shadows: G(978), midtones: G(977), highlights: G(976),
    bw: [965, 966, 967, 993, 997, 1020].map(G),
  };
  console.log('LOOK DEFAULTS ' + JSON.stringify(got));
  const f = want.film === null ? {} : films[want.film];
  const zero12 = Array(12).fill(0);
  const exp = {
    pm: 54, sat: [...(f.sat ?? zero12)], hue: f.hue ?? zero12, light: f.light ?? zero12,
    contrast: f.contrast ?? 0, sharpness: f.sharpness ?? 0, shading: f.shading ?? 0,
    shadows: f.shadows ?? 0, midtones: f.midtones ?? 0, highlights: f.highlights ?? 0, bw: Array(6).fill(0),
  };
  if (want.sat0 !== undefined) exp.sat[0] = want.sat0;
  assert.deepEqual(got, exp, 'Color Profile 1 after Hold OK');
  console.log('ASSERTIONS passed');
}
