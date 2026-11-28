// PRE module: mount the card, then write the setting cells in OM5_SEED (JSON {id: value}) with OM's setting writer
// 0x60855cdc (as hsl.s stock_ui_write), before any key. Used where a value has no key path in this build: the split-tone tints
// lost theirs on the wheel with the OM-3 v0.41 key map (2026-11-28) and get their own row later; earlier builds'
// one / all cell 2197 at "all" (0), which OM's own INFO used to leave there.
export default async function (g) {
  g.__M.dbgWrite(0x61e43b88, new Uint8Array([0, 0xf0, 0, 0]));
  for (const [id, value] of Object.entries(JSON.parse(process.env.OM5_SEED || '{}')))
    g.__call(0x60855cdc, { d0: Number(id), d1: Number(value) >>> 0, a0: 1 }, [0xf0, 20]);
}
