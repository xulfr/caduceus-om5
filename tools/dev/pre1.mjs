export default async function (g) {
  const W = (id, part, v) => g.__call(0x602f5121, { d0: id, d1: part, a0: v >>> 0 });
  const R = (id, part) => g.__call(0x602f50f8, { d0: id, d1: part }).d0 | 0;
  console.log('before', [904, 908, 912, 928, 929, 976, 977, 978].map((i) => R(i, 0)));
  W(904, 0, 2); W(908, 0, -1); W(912, 0, 3); W(928, 0, 3); W(929, 0, -2); W(976, 0, 4); W(977, 0, -3); W(978, 0, 5);
  console.log('after', [904, 908, 912, 928, 929, 976, 977, 978].map((i) => R(i, 0)));
}
