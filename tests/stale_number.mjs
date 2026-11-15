export default function (g) {
  const c = g.__call; const get = (id) => c(0x602d000d, { d0: id }, [0, 4]).d0;
  console.log('before: 111=' + get(111) + ' 903=' + get(903));
  c(0x60855cdc, { d0: 903, d1: Number(process.env.N903 ?? 1), a0: 1 }, [0xf0, 20]);
  if (process.env.N989) c(0x60855cdc, { d0: 989, d1: Number(process.env.N989), a0: 1 }, [0xf0, 20]);
  console.log('stale: 111=' + get(111) + ' 903=' + get(903) + ' 989=' + get(989));
  g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
}
