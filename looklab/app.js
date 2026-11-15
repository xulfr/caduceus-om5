// LookLab for Caduceus for OM-5. No build step, no server: everything stays in this browser.
// The preview's colour numbers (sector centres and widths, the gains fitted to a camera, the WB gains) are those of
// Caduceus for OM-3's LookLab (androidfanman/caduceus-om3, webapp/src/preview.ts, Apache-2.0), which fitted them to
// the OM-3. The OM-5 Mark II has the same colour engine as far as this project knows, but nothing here has been
// compared with an OM-5 photo: the preview shows direction and rough strength only.
'use strict';

const SECTORS = ['Yellow', 'Orange', 'Orange-red', 'Red', 'Magenta', 'Violet', 'Blue', 'Blue-cyan', 'Cyan', 'Green-cyan', 'Green', 'Yellow-green'];
const SWATCH = ['#f2d600', '#f59a00', '#f05a00', '#e0102a', '#d4157a', '#7a33cc', '#2a4fd8', '#1f8fe0', '#12b8c8', '#10b87a', '#3aa935', '#a3c81e'];
const MAX_FILMS = 10, NAME_MAX = 12;
const RANGE = { hue: 7, light: 7, sat: 5, wb: 7, contrast: 2, sharpness: 2, shading: 5, tone: 7 };
const SAMPLES = [['frames', 'Picture frames'], ['portrait', 'Portrait'], ['taxi', 'Yellow taxi'], ['meadow', 'Mountain meadow'], ['ocean', 'Harbour']];
const STORE = 'caduceus-om5-looklab/1';

// ---------------------------------------------------------------- films and the LOOKS.BIN file (docs/FORMATS.md)
const blank = (name = 'New film') => ({ name, hue: Array(12).fill(0), light: Array(12).fill(0), sat: Array(12).fill(0), wb: null,
  contrast: 0, sharpness: 0, shading: 0, shadows: 0, midtones: 0, highlights: 0 });
const clone = (f) => JSON.parse(JSON.stringify(f));

const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(b) { let c = 0xffffffff; for (const x of b) c = CRC[(c ^ x) & 255] ^ (c >>> 8); return (c ^ 0xffffffff) >>> 0; }

function nameProblem(name) {
  if (!name.length) return 'The name is empty.';
  if (name !== name.trim()) return 'No spaces at the start or end.';
  if (name.length > NAME_MAX) return `At most ${NAME_MAX} characters (${name.length}).`;
  if (!/^[\x20-\x7e]+$/.test(name)) return 'Plain letters, digits, spaces and punctuation only.';
  if (name.includes('@')) return 'Use a name without @; the camera treats it as a display command.';
  return null;
}

function looksBin(films) {
  if (films.length < 1 || films.length > MAX_FILMS) throw new Error(`1 to ${MAX_FILMS} films`);
  const out = new Uint8Array(32 + 80 * films.length), dv = new DataView(out.buffer);
  out.set([0x4f, 0x4d, 0x35, 0x46]);                         // 'OM5F'
  dv.setUint32(4, out.length, true); dv.setUint16(12, 1, true); dv.setUint16(14, films.length, true);
  films.forEach((f, k) => {
    f = { ...blank(), ...f };
    for (const key of ['hue', 'light', 'sat']) if (!Array.isArray(f[key]) || f[key].length !== 12) throw new Error(`${key} needs 12 values`);
    if (f.wb !== null && (!Array.isArray(f.wb) || f.wb.length !== 2)) throw new Error('WB needs two values');
    const p = nameProblem(f.name); if (p) throw new Error(`${f.name || 'Film ' + (k + 1)}: ${p}`);
    const o = 32 + 80 * k, put = (at, v, n) => { if (!Number.isInteger(v) || Math.abs(v) > n) throw new Error(`${f.name}: a value is out of range`); dv.setInt8(o + at, v); };
    for (let i = 0; i < 12; i++) { put(i, f.hue[i], RANGE.hue); put(12 + i, f.light[i], RANGE.light); put(24 + i, f.sat[i], RANGE.sat); }
    if (f.wb) { dv.setInt8(o + 36, 1); put(37, f.wb[0], RANGE.wb); put(38, f.wb[1], RANGE.wb); }
    put(41, f.contrast, RANGE.contrast); put(42, f.sharpness, RANGE.sharpness); put(43, f.shading, RANGE.shading);
    put(44, f.shadows, RANGE.tone); put(45, f.midtones, RANGE.tone); put(46, f.highlights, RANGE.tone);
    for (let i = 0; i < f.name.length; i++) out[o + 64 + i] = f.name.charCodeAt(i);
  });
  dv.setUint32(8, crc32(out.subarray(12)), true);
  return out;
}

function readLooks(buf) {
  const b = new Uint8Array(buf), dv = new DataView(b.buffer, b.byteOffset, b.byteLength);
  if (b.length < 112 || String.fromCharCode(...b.subarray(0, 4)) !== 'OM5F') throw new Error('This is not a LOOKS.BIN for the OM-5 (an OM-3 file is a different format).');
  const n = dv.getUint16(14, true);
  if (dv.getUint32(4, true) !== b.length || dv.getUint16(12, true) !== 1 || n < 1 || n > MAX_FILMS || b.length !== 32 + 80 * n) throw new Error('The file is damaged (length).');
  if (dv.getUint32(8, true) !== crc32(b.subarray(12))) throw new Error('The file is damaged (checksum).');
  const films = [];
  for (let k = 0; k < n; k++) {
    const o = 32 + 80 * k, g = (at) => dv.getInt8(o + at), arr = (at) => Array.from({ length: 12 }, (_, i) => g(at + i));
    if (g(36) !== 0 && g(36) !== 1) throw new Error('Invalid WB flag');
    if (Math.abs(g(37)) > 7 || Math.abs(g(38)) > 7) throw new Error('Invalid WB shift');
    for (let i = 0; i < NAME_MAX; i++) {
      const c = b[o + 64 + i];
      if (c && (c < 32 || c > 126 || c === 64)) throw new Error('Invalid name byte');
    }
    let name = ''; for (let i = 0; i < NAME_MAX && b[o + 64 + i]; i++) name += String.fromCharCode(b[o + 64 + i]);
    films.push({ name, hue: arr(0), light: arr(12), sat: arr(24), wb: g(36) ? [g(37), g(38)] : null, contrast: g(41), sharpness: g(42), shading: g(43),
      shadows: g(44), midtones: g(45), highlights: g(46) });
  }
  looksBin(films); // Validate every imported value before it enters the editor.
  return films;
}

// ---------------------------------------------------------------- preview
const CENTRE = [12197, 9466, 8192, 6736, 3095, 30401, 28945, 27489, 24212, 20753, 16111, 15019].map((w) => (w / 32768) * 360);
const WIDTH = [3823, 5461, 3959, 2685, 5006, 9057, 6872, 2867, 4642, 6690, 8055, 5643].map((w) => (w / 32768) * 360);
const CAL = { gainPos: [306, 171, 618, 256, 517, 32, 622, 428, 724, 254, 250, 812], gainNeg: [988, 327, 1032, 493, 560, 186, 568, 474, 980, 389, 233, 498],
  hueDown: [19.3, 6.5, 10.1, 5.5, 7.4, 0.0, 7.5, 6.4, 19.0, 12.6, 0.0, 3.6], hueUp: [17.2, 6.7, 13.7, 5.5, 11.9, 0.1, 7.1, 7.7, 21.2, 6.4, 2.9, 5.5],
  light: 2.44, wbAB: [0.0379, 0.0118, -0.0129], wbGM: [-0.0097, 0.0181, -0.0131] };
const L_LUT = [-300, -250, -200, -150, -100, -50, -25, 0, 25, 50, 100, 150, 200, 250, 300];
const BINS = 720, ANGLE_OFFSET = 15, SAT_SCALE = 1.5;
const DEC = new Float32Array(256).map((_, i) => { const x = i / 255; return x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
const ENC = new Float32Array(4097).map((_, i) => { const x = i / 4096; return x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055; });
const enc = (x) => ENC[Math.max(0, Math.min(4096, (x * 4096 + 0.5) | 0))];
const clamp01 = (x) => (x < 0 ? 0 : x > 1 ? 1 : x);

function sectorLut(f) {
  const hue = f.hue.map((v) => -v);                       // the engine's sign is the camera's negated
  const satMul = new Float32Array(BINS), shift = new Float32Array(BINS), lsum = new Float32Array(BINS);
  const sc = f.sat.map((s, k) => (s * (s >= 0 ? CAL.gainPos[k] : CAL.gainNeg[k])) / 5 * SAT_SCALE);
  const deg = hue.map((v, k) => (v >= 0 ? CAL.hueDown[k] : CAL.hueUp[k]));
  const centre = CENTRE.map((c) => (c + ANGLE_OFFSET) % 360), w = new Float64Array(12);
  for (let b = 0; b < BINS; b++) {
    const h = (b + 0.5) * (360 / BINS); let sum = 0;
    for (let k = 0; k < 12; k++) { const d = ((h - centre[k] + 540) % 360) - 180, x = Math.max(-1, Math.min(1, d / Math.max(WIDTH[k], 1))); w[k] = Math.max(0, Math.cos(x * Math.PI / 2)); sum += w[k]; }
    let s = 0, hs = 0, l = 0;
    for (let k = 0; k < 12; k++) { const wk = sum > 1e-6 ? w[k] / sum : 1 / 12; s += wk * sc[k]; hs += wk * hue[k] * deg[k]; l += wk * L_LUT[Math.max(-7, Math.min(7, f.light[k])) + 7] * CAL.light; }
    satMul[b] = Math.max(0, Math.min(3, 1 + s / 1000)); shift[b] = (hs * Math.PI) / 180; lsum[b] = l / 4096;
  }
  return { satMul, shift, lsum };
}

/** Luminance curve: Contrast as a gentle S, then Shadows / Midtones / Highlights as three overlapping lifts (our own
 *  approximation of the camera's tone curve; 7 steps move a region by about a sixth of the range). */
function toneLut(f) {
  const lut = new Float32Array(1025), k = 0.024;
  for (let i = 0; i <= 1024; i++) {
    let y = i / 1024;
    y = clamp01(y + 0.5 * 0.035 * f.contrast * Math.sin(2 * Math.PI * (y - 0.5)));
    const sh = Math.pow(1 - y, 2) * y * 6.75, hi = Math.pow(y, 2) * (1 - y) * 6.75, mid = Math.pow(4 * y * (1 - y), 1.5);
    lut[i] = clamp01(y + k * (f.shadows * sh + f.midtones * mid + f.highlights * hi));
  }
  return lut;
}

function render(src, dst, f) {
  const { width: w, height: h } = src, s = src.data, d = dst.data, n = w * h;
  const ab = f.wb ? f.wb[0] : 0, gm = f.wb ? f.wb[1] : 0, wb = ab || gm;
  const g = [0, 1, 2].map((c) => 1 + CAL.wbAB[c] * ab + CAL.wbGM[c] * gm);
  const lut = sectorLut(f), tl = toneLut(f);
  const cx = w / 2, cy = h / 2, rr = cx * cx + cy * cy, shade = f.shading * 0.07;
  for (let i = 0; i < n; i++) {
    const p = i * 4;
    let r, gg, b;
    if (wb) { r = enc(DEC[s[p]] * g[0]); gg = enc(DEC[s[p + 1]] * g[1]); b = enc(DEC[s[p + 2]] * g[2]); } else { r = s[p] / 255; gg = s[p + 1] / 255; b = s[p + 2] / 255; }
    let y = 0.299 * r + 0.587 * gg + 0.114 * b, cb = -0.168736 * r - 0.331264 * gg + 0.5 * b, cr = 0.5 * r - 0.418688 * gg - 0.081312 * b;
    y = tl[Math.max(0, Math.min(1024, (y * 1024 + 0.5) | 0))];
    const chroma = Math.hypot(cb, cr);
    if (chroma > 1e-5) {
      let hd = (Math.atan2(cr, cb) * 180) / Math.PI; if (hd < 0) hd += 360;
      const bin = Math.min(BINS - 1, (hd * (BINS / 360)) | 0), ang = (hd * Math.PI) / 180 + lut.shift[bin], ch = chroma * lut.satMul[bin];
      y += lut.lsum[bin] * Math.min(1, chroma / 0.25); cb = ch * Math.cos(ang); cr = ch * Math.sin(ang);
    }
    if (shade) { const x = (i % w) - cx, yy = ((i / w) | 0) - cy, q = (x * x + yy * yy) / rr; y *= 1 + shade * q * q; }
    d[p] = clamp01(y + 1.402 * cr) * 255 + 0.5; d[p + 1] = clamp01(y - 0.344136 * cb - 0.714136 * cr) * 255 + 0.5; d[p + 2] = clamp01(y + 1.772 * cb) * 255 + 0.5; d[p + 3] = 255;
  }
}

// ---------------------------------------------------------------- state
const $ = (id) => document.getElementById(id);
const el = (tag, attrs = {}, ...kids) => { const e = document.createElement(tag); for (const [k, v] of Object.entries(attrs)) { if (k === 'class') e.className = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else if (v !== false && v != null) e.setAttribute(k, v); } for (const c of kids) e.append(c); return e; };
let library = [], films = [], sel = 0, tab = 'sat', srcData = null, showOriginal = false, sample = 'frames';

function save() { try { localStorage.setItem(STORE, JSON.stringify({ films, sel, sample })); } catch (e) { /* private mode */ } }
function load() { try { const s = JSON.parse(localStorage.getItem(STORE)); if (s && Array.isArray(s.films) && s.films.length) { films = s.films; sel = Math.min(s.sel | 0, films.length - 1); sample = s.sample || sample; return true; } } catch (e) { /* none */ } return false; }
const cur = () => films[sel];
const sgn = (v) => (v > 0 ? '+' + v : v === 0 ? '±0' : String(v));
function say(text, bad) { const m = $('msg'); m.textContent = text; m.className = bad ? 'msg bad' : 'msg'; }

// ---------------------------------------------------------------- views
function drawList() {
  const ul = $('films'); ul.replaceChildren();
  films.forEach((f, k) => {
    const slot = k < 3 ? `first press on Color Profile ${k + 1}` : '';
    ul.append(el('li', { class: k === sel ? 'on' : '', onclick: () => { sel = k; drawAll(); } },
      el('span', { class: 'num' }, String(k + 1)), el('span', { class: 'nm' }, f.name || '(no name)'), el('span', { class: 'hint' }, slot)));
  });
  $('count').textContent = `${films.length} of ${MAX_FILMS}`;
  $('add').disabled = $('dup').disabled = films.length >= MAX_FILMS;
  $('del').disabled = films.length <= 1; $('up').disabled = sel === 0; $('down').disabled = sel >= films.length - 1;
}

function slider(label, get, set, n, colour) {
  const val = el('output', {}, sgn(get()));
  const inp = el('input', { type: 'range', min: -n, max: n, step: 1, value: get(), 'aria-label': label,
    oninput: () => { set(Number(inp.value)); val.textContent = sgn(get()); changed(); }, ondblclick: () => { inp.value = 0; set(0); val.textContent = sgn(0); changed(); } });
  return el('label', { class: 'row' }, el('span', { class: 'lbl' }, colour ? el('i', { class: 'sw', style: `background:${colour}` }) : '', label), inp, val);
}

function drawEditor() {
  const f = cur(), ed = $('editor'); ed.replaceChildren();
  const name = el('input', { type: 'text', value: f.name, maxlength: NAME_MAX, id: 'name', 'aria-label': 'Film name',
    oninput: () => { f.name = name.value; const p = nameProblem(f.name); say(p || '', !!p); drawList(); save(); } });
  ed.append(el('div', { class: 'namerow' }, el('label', { for: 'name' }, 'Name'), name, el('span', { class: 'hint' }, `${NAME_MAX} characters`)));
  const tabs = el('div', { class: 'tabs', role: 'tablist' });
  for (const [id, label] of [['sat', 'Saturation'], ['hue', 'Hue'], ['light', 'Lightness']]) tabs.append(el('button', { class: tab === id ? 'on' : '', role: 'tab', 'aria-selected': tab === id, onclick: () => { tab = id; drawEditor(); } }, label));
  ed.append(el('h3', {}, 'Colour wheel'), tabs);
  const help = { sat: 'How strong each colour is.', hue: 'Turns a colour toward its neighbour on the wheel.', light: 'Makes a colour brighter or darker.' }[tab];
  ed.append(el('p', { class: 'hint' }, help + ' Double-click a slider to zero it. The camera\'s own editor reaches ±5.'));
  const grid = el('div', { class: 'grid' });
  SECTORS.forEach((s, i) => grid.append(slider(s, () => f[tab][i], (v) => { f[tab][i] = v; }, RANGE[tab], SWATCH[i])));
  ed.append(grid);
  ed.append(el('h3', {}, 'Tone'), el('div', { class: 'grid' },
    slider('Shadows', () => f.shadows, (v) => { f.shadows = v; }, RANGE.tone), slider('Midtones', () => f.midtones, (v) => { f.midtones = v; }, RANGE.tone),
    slider('Highlights', () => f.highlights, (v) => { f.highlights = v; }, RANGE.tone), slider('Contrast', () => f.contrast, (v) => { f.contrast = v; }, RANGE.contrast),
    slider('Sharpness', () => f.sharpness, (v) => { f.sharpness = v; }, RANGE.sharpness), slider('Shading', () => f.shading, (v) => { f.shading = v; }, RANGE.shading)));
  const on = el('input', { type: 'checkbox', id: 'wbon', onchange: () => { f.wb = on.checked ? [0, 0] : null; changed(); drawEditor(); } }); on.checked = !!f.wb;
  ed.append(el('h3', {}, 'White balance shift'), el('label', { class: 'check', for: 'wbon' }, on, ' This film sets the A/B and G/M shift'));
  if (f.wb) ed.append(el('div', { class: 'grid' }, slider('A/B (amber +)', () => f.wb[0], (v) => { f.wb[0] = v; }, RANGE.wb), slider('G/M (green +)', () => f.wb[1], (v) => { f.wb[1] = v; }, RANGE.wb)));
  ed.append(el('p', { class: 'hint' }, 'Sharpness is not shown in the preview. The shift is added to whatever white balance mode the camera is on.'));
}

let pending = 0;
function drawPreview() {
  if (!srcData) return;
  cancelAnimationFrame(pending);
  pending = requestAnimationFrame(() => {
    const c = $('view'), ctx = c.getContext('2d');
    if (showOriginal) { ctx.putImageData(srcData, 0, 0); return; }
    const out = ctx.createImageData(srcData.width, srcData.height); render(srcData, out, cur()); ctx.putImageData(out, 0, 0);
  });
}
function changed() { save(); drawPreview(); }
function drawAll() { drawList(); drawEditor(); drawPreview(); save(); }

function setImage(img) {
  const c = $('view'), k = Math.min(1, 900 / Math.max(img.naturalWidth || img.width, img.naturalHeight || img.height));
  c.width = Math.round((img.naturalWidth || img.width) * k); c.height = Math.round((img.naturalHeight || img.height) * k);
  const ctx = c.getContext('2d', { willReadFrequently: true }); ctx.drawImage(img, 0, 0, c.width, c.height);
  srcData = ctx.getImageData(0, 0, c.width, c.height); drawPreview();
}
function loadSample(id) { sample = id; const img = new Image(); img.onload = () => setImage(img); img.src = `samples/${id}.jpg`; save(); }

function download(bytes, name) { const a = el('a', { href: URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' })), download: name }); document.body.append(a); a.click(); setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 500); }

function fillLibrary() {
  const s = $('lib'); s.replaceChildren(el('option', { value: '' }, 'Add a film from the library…'));
  const groups = { neg: 'Colour negative', slide: 'Slide film', fuji: 'Fujifilm simulations', instant: 'Instant film', print: 'Cinema print' };
  for (const [g, label] of Object.entries(groups)) { const og = el('optgroup', { label }); library.filter((f) => f.group === g).forEach((f) => og.append(el('option', { value: f.name, title: f.desc }, f.name))); if (og.children.length) s.append(og); }
}
const fromLib = (f) => ({ name: f.name, hue: [...f.hue], light: [...f.light], sat: [...f.sat], wb: f.wb ? [...f.wb] : null, contrast: f.contrast, sharpness: f.sharpness, shading: f.shading, shadows: f.shadows, midtones: f.midtones, highlights: f.highlights });

async function start() {
  try { library = (await (await fetch('films.json')).json()).films; } catch (e) { library = []; }
  const starter = ['Portra 400', 'Portra 160', 'Gold 200', 'Ektar 100', 'Kodachrome64', 'CineStill800', 'Velvia 50', 'Provia 100F', 'Pro 400H', 'Superia 400'];
  if (!load()) { films = starter.map((n) => library.find((f) => f.name === n)).filter(Boolean).map(fromLib); if (!films.length) films = [blank()]; }
  fillLibrary();
  const ss = $('sample'); SAMPLES.forEach(([id, label]) => ss.append(el('option', { value: id }, label))); ss.value = sample;
  ss.onchange = () => loadSample(ss.value);
  $('photo').onchange = (e) => { const file = e.target.files[0]; if (!file) return; const img = new Image(); img.onload = () => { setImage(img); URL.revokeObjectURL(img.src); }; img.src = URL.createObjectURL(file); };
  $('lib').onchange = (e) => { const f = library.find((x) => x.name === e.target.value); e.target.value = ''; if (!f || films.length >= MAX_FILMS) return; films.push(fromLib(f)); sel = films.length - 1; drawAll(); say(f.desc); };
  $('add').onclick = () => { films.push(blank()); sel = films.length - 1; drawAll(); };
  $('dup').onclick = () => { const c = clone(cur()); films.splice(sel + 1, 0, c); sel++; drawAll(); };
  $('del').onclick = () => { films.splice(sel, 1); sel = Math.min(sel, films.length - 1); drawAll(); };
  $('up').onclick = () => { [films[sel - 1], films[sel]] = [films[sel], films[sel - 1]]; sel--; drawAll(); };
  $('down').onclick = () => { [films[sel + 1], films[sel]] = [films[sel], films[sel + 1]]; sel++; drawAll(); };
  $('reset').onclick = () => { const n = cur().name; const lib = library.find((x) => x.name === n); films[sel] = lib ? fromLib(lib) : blank(n); drawAll(); say(lib ? `${n}: back to the library's values.` : `${n}: all values zero.`); };
  $('savebin').onclick = () => { try { const b = looksBin(films); download(b, 'LOOKS.BIN'); say(`LOOKS.BIN saved (${films.length} films, ${b.length} bytes). Put it in a folder OM5MOD at the top of the SD card.`); } catch (e) { say(e.message, true); } };
  $('openbin').onchange = async (e) => { const file = e.target.files[0]; e.target.value = ''; if (!file) return; try { films = readLooks(await file.arrayBuffer()); sel = 0; drawAll(); say(`${file.name}: ${films.length} films opened.`); } catch (err) { say(err.message, true); } };
  $('starter').onclick = () => { films = starter.map((n) => library.find((f) => f.name === n)).filter(Boolean).map(fromLib); sel = 0; drawAll(); say('The ten starter films.'); };
  const v = $('view'), hold = (on) => () => { showOriginal = on; drawPreview(); };
  v.addEventListener('pointerdown', hold(true)); v.addEventListener('pointerup', hold(false)); v.addEventListener('pointerleave', hold(false));
  drawList(); drawEditor(); loadSample(sample);
}
if (typeof document !== 'undefined') start();
if (typeof module !== 'undefined') module.exports = { looksBin, readLooks, crc32, blank, nameProblem };
