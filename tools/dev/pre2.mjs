export default async function (g) {
  const G = (id) => g.__call(0x602d000d, { d0: id }, [0, 4]).d0 | 0;
  const RG = (id, ctx, st) => g.__call(0x602d2fc2, { a0: id, d0: ctx, d1: st }, [0x80, 8]).d0 | 0;
  const RS = (id, v, ctx, st) => g.__call(0x602d2fdb, { a0: id, a1: v >>> 0, d0: ctx, d1: st }, [0xa0, 12]);
  const ids = [904, 908, 912, 928, 929, 976, 977, 978];
  console.log('stock_get', ids.map(G), 'ctx0 st1', ids.map((i) => RG(i, 0, 1)), 'st2', ids.map((i) => RG(i, 0, 2)), 'st0', ids.map((i) => RG(i, 0, 0)));
  const mode = process.env.MODE;
  if (mode === 'rs1') { RS(904, 2, 0, 1); RS(908, -1, 0, 1); RS(912, 3, 0, 1); RS(928, 3, 0, 1); RS(929, -2, 0, 1); RS(976, 4, 0, 1); RS(977, -3, 0, 1); RS(978, 5, 0, 1); }
  if (mode === 'rs2') { RS(976, 4, 0, 2); RS(977, -3, 0, 2); RS(978, 5, 0, 2); RS(904, 2, 0, 2); }
  if (mode === 'ui') { for (const [i, v] of [[904, 2], [908, -1], [912, 3], [928, 3], [929, -2], [976, 4], [977, -3], [978, 5]]) g.__call(0x60855cdc, { d0: i, d1: v >>> 0, a0: 0 }, [0xf0, 20]); }
  console.log('stock_get', ids.map(G), 'ctx0 st1', ids.map((i) => RG(i, 0, 1)), 'st2', ids.map((i) => RG(i, 0, 2)), 'st0', ids.map((i) => RG(i, 0, 0)));
}
