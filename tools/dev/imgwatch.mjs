// PRE module: mount the card; print every image-table read for IDs LO..HI (env IMG_LO/IMG_HI, hex) as it happens.
export default async function (g) {
  const M = g.__M; const T = 0xa3435ccc;
  const lo = parseInt(process.env.IMG_LO ?? '3800', 16), hi = parseInt(process.env.IMG_HI ?? '3a00', 16);
  M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  const log = (r) => { const a = (r.addr >>> 0) & 0xbfffffff; console.log('IMG ' + (((a - T) >>> 2)).toString(16) + ' pc ' + (r.pc >>> 0).toString(16)); };
  M.setWatchpoints([{ id: 9, lo: T + 4 * lo, hi: T + 4 * hi, kind: 1, stop: false }, { id: 10, lo: T + 4 * lo + 0x40000000, hi: T + 4 * hi + 0x40000000, kind: 1, stop: false }], { onLog: log });
}
