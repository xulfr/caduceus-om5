#!/usr/bin/env python3
"""Caduceus for OM-5: make the SD-card update file from OM's official firmware.

    python3 patch.py                 newest release for the OM-5 Mark II; downloads OM's firmware 1.1 if it is not here
    python3 patch.py --stock FILE    use this copy of OLY_E_148_1100_0000_0000.BIN
    python3 patch.py --release NAME  another release from releases/
    python3 patch.py --out DIR       where to write (default: ./card)

Writes  DIR/DCOLYMP/E1489999.BIN       the patched update (copy the DCOLYMP folder to the top of the SD card)
        DIR/restore/DCOLYMP/E1489999.BIN  OM's own firmware 1.1, to go back
        DIR/OM5MOD/LOOKS.BIN            the starter films, when the release has them

Needs only Python 3.8+. It never talks to a camera. It contains no OM firmware: it works on the official file,
checks that file's SHA-256, applies this project's changes and checks the result against the release's SHA-256.
"""
import argparse, json, os, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'tools'))
from oly_container import parse, reconstruct, replace_payload, sha256   # noqa: E402
from oly_compress import expand_image, repack_image                      # noqa: E402
from oly_resource import alias_images                                    # noqa: E402

UNTESTED = """
  ************************************************************************
  THIS RELEASE HAS NOT RUN ON A CAMERA.

  Four OM-5 Mark II builds of this work left the owner's camera in a
  boot loop (November 2026). Each time OM's own firmware could be
  put back from the card, but nothing shows that this will always work.
  A camera that cannot start may need OM service, at your cost.

  Read docs/SAFETY.md first. If you still want the file, type  UNTESTED
  ************************************************************************
"""


class Refuse(Exception):
    pass


def fetch_stock(rel):
    """Ask OM's update server for the firmware, as OM Workspace does (request adapted from Caduceus,
    cakelesscoder/caduceus-ep7, Apache-2.0)."""
    import urllib.request, xml.etree.ElementTree as ET
    code, want = rel['model_code'], rel['stock']['file']
    t = time.strftime('%Y%m%d%H%M%S', time.gmtime())
    req = ("<?xml version='1.0' encoding='utf-8'?><firmware_demand><revision>0001</revision>"
           "<mac_address>00-00-00-00-00-00</mac_address><time>" + t + "</time><language>ENU</language>"
           "<application>FWUT</application><type>0000</type><version>00005000</version><os>WIN</os>"
           "<country_code>0001</country_code><hardwares><firmup_mode>0</firmup_mode><hardware_info>"
           f"<hard_code>OLY{code}000000000</hard_code><firmware_version>00001000</firmware_version>"
           "<serial_no>000000000</serial_no></hardware_info></hardwares></firmware_demand>")
    hdrs = {'User-Agent': 'Olympus', 'Content-Type': 'text/xml; Charset=UTF-8'}
    print(f'Asking OM Digital Solutions for the {rel["model"]} firmware ...')
    try:
        with urllib.request.urlopen(urllib.request.Request('https://fw01.om-digitalsolutions.net/ww_inform/fcache.do',
                                                           req.encode(), hdrs), timeout=60) as r:
            info = ET.fromstring(r.read()).find('.//firmware_info')
        name = info.findtext('file_name') if info is not None else None
        if name != want:
            raise Refuse(f'OM offers {name!r}, not {want} (a newer firmware, which this release does not support). '
                         f'Get {want} another way and use --stock FILE.')
        url = info.findtext('url')
        print(f'Downloading {want} from {url.split("/")[2]}')
        buf, size = bytearray(), rel['stock']['bytes']
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Olympus'}), timeout=120) as r:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                buf += chunk
                print(f'\r  {len(buf) >> 20} / {size >> 20} MiB', end='', flush=True)
        print()
        return bytes(buf)
    except (OSError, ET.ParseError) as e:
        raise Refuse(f'the download did not work ({e}). Get {want} another way and use --stock FILE.')


def find_stock(name):
    for d in (HERE, Path.cwd(), Path.home() / 'Downloads'):
        if (d / name).is_file():
            return d / name
    return None


def newest():
    def key(p):
        import re
        return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', p.name)]
    rels = sorted((p for p in (HERE / 'releases').iterdir() if (p / 'patch.json').is_file()), key=key)
    if not rels:
        raise Refuse('no release in releases/')
    return rels[-1].name


def build(rel, stock):
    if sha256(stock) != rel['stock']['sha256']:
        raise Refuse(f'this is not {rel["stock"]["file"]} as OM publishes it (SHA-256 differs); nothing was written')
    blocks = parse(stock)
    by_kind = {b.kind: b for b in blocks}
    main = bytearray(expand_image(by_kind[0x100].payload))
    m = rel['main']
    if sha256(main) != m['expanded_before_sha256']:
        raise Refuse('the main program does not expand to the expected bytes')
    base = int(m['cpu_base'], 16)
    for e in m['edits']:
        at, new = int(e['address'], 16) - base, bytes.fromhex(e['bytes'])
        if sha256(main[at:at + len(new)]) != e['before_sha256']:
            raise Refuse(f'unexpected bytes at {e["address"]}')
        main[at:at + len(new)] = new
    if sha256(main) != m['expanded_after_sha256']:
        raise Refuse('the patched main program differs from the release')
    print('Packing the main program (about a quarter of a minute) ...')
    stored = repack_image(by_kind[0x100].payload, bytes(main), split=True, literal_limit=0)
    if sha256(stored) != m['stored_after_sha256']:
        raise Refuse('the packed main program differs from the release')
    res = alias_images(by_kind[0x101].payload, [(int(a, 16), int(b, 16)) for a, b in rel['resource']['aliases']])
    if sha256(res) != rel['resource']['after_sha256']:
        raise Refuse('the resource block differs from the release')
    new = {0x100: stored, 0x101: res}
    image = reconstruct([replace_payload(b, new[b.kind]) if b.kind in new else b for b in blocks])
    if len(image) != rel['package']['bytes'] or sha256(image) != rel['package']['sha256']:
        raise Refuse('the update file differs from the release; nothing was written')
    parse(image)                                    # every component checksum once more
    return image


def atomic_write(path, data):
    """Publish a complete file; a failed write must not truncate an existing update."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.',
                                         suffix='.tmp', delete=False) as f:
            temporary = Path(f.name)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--stock', type=Path)
    ap.add_argument('--release')
    ap.add_argument('--out', type=Path, default=Path.cwd() / 'card')
    ap.add_argument('--i-accept-untested', action='store_true', help=argparse.SUPPRESS)
    a = ap.parse_args()
    try:
        name = a.release or newest()
        folder = HERE / 'releases' / name
        if not (folder / 'patch.json').is_file():
            raise Refuse(f'no release {name}')
        rel = json.loads((folder / 'patch.json').read_text())
        print(f'Caduceus for OM-5, release {name}: {rel["model"]}, firmware {rel["firmware"]}')
        if rel.get('blocked'):
            raise Refuse(rel['blocked'] + ' Do not flash it. See docs/SAFETY.md; nothing was written')
        if not rel.get('camera_tested') and not a.i_accept_untested:
            print(UNTESTED)
            if input('> ').strip() != 'UNTESTED':
                raise Refuse('stopped; nothing was written')
        path = a.stock or find_stock(rel['stock']['file'])
        stock = path.read_bytes() if path else fetch_stock(rel)
        image = build(rel, stock)
        out = a.out
        # Publish recovery first and the install last. Never replace a user's looks.
        atomic_write(out / 'restore/DCOLYMP/E1489999.BIN', stock)
        looks = out / 'OM5MOD/LOOKS.BIN'
        kept_looks = looks.exists()
        if not kept_looks and (folder / 'LOOKS.BIN').is_file():
            atomic_write(looks, (folder / 'LOOKS.BIN').read_bytes())
        atomic_write(out / 'DCOLYMP/E1489999.BIN', image)
        print(f'\nDone. In {out}:')
        print('  DCOLYMP/E1489999.BIN          the patched update, SHA-256 ' + sha256(image))
        print('  restore/DCOLYMP/E1489999.BIN  OM\'s firmware 1.1, to go back')
        if (out / 'OM5MOD' / 'LOOKS.BIN').is_file():
            print('  OM5MOD/LOOKS.BIN              ' + ('your existing looks (kept)' if kept_looks else 'the starter looks'))
        print('Next: docs/INSTALL.md')
    except Refuse as e:
        print(f'\nStopped: {e}')
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print('\nStopped; preparation may be incomplete. Run again before copying files.')
        sys.exit(1)
    except OSError as e:
        print(f'\nStopped: {e}. Preparation is incomplete; run again before copying files.')
        sys.exit(1)


if __name__ == '__main__':
    main()
