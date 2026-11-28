"""Shared by the emulator tests: a card folder holding OM5MOD/CADUCEUS.BIN made for the build under test
(tools/mkcardblock.py). The Picture Mode page graphics live in that block, so tests that read them pass its folder
to tools/dev/sess.mjs with --card=."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import mkcardblock  # noqa: E402


def card_for(build, out):
    """out/card with OM5MOD/CADUCEUS.BIN for build (made once per out folder)."""
    card = Path(out).resolve() / 'card'
    block = card / 'OM5MOD' / 'CADUCEUS.BIN'
    if not block.is_file():
        block.parent.mkdir(parents=True, exist_ok=True)
        mkcardblock.build(Path(build).resolve(), block)
    return card
