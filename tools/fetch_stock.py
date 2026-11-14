#!/usr/bin/env python3
"""Download OM's official firmware files that the builders need, from OM's own update server, and check them.

    python3 tools/fetch_stock.py E148          OM-5 Mark II 1.1
    python3 tools/fetch_stock.py E144 E148     original OM-5 1.2 and OM-5 Mark II 1.1 (the OM-5 pre-alpha needs both)

Files are written to the current directory (a file already there with the right checksum is kept). Nothing is
sent to a camera. The files are OM's: keep them local, do not share or commit them."""
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import patch  # noqa: E402

STOCK = {
    'E148': {'model': 'OM-5 Mark II', 'model_code': 'E148', 'stock': {'file': 'OLY_E_148_1100_0000_0000.BIN',
             'bytes': 90832896, 'sha256': '9de5d77e1d290fa2ed4ebc7d75cee0ed490befbc89566722467d1d421d66d637'}},
    'E144': {'model': 'OM-5', 'model_code': 'E144', 'stock': {'file': 'OLY_E_144_1200_0000_0000.BIN',
             'bytes': 92274688, 'sha256': 'a0c91f3ac7caaf0925b2af609e711183cf3b5982b3333224bcef26c0c5943d11'}},
}


def main():
    codes = sys.argv[1:]
    if not codes or any(c not in STOCK for c in codes):
        sys.exit(__doc__)
    for code in codes:
        rel = STOCK[code]
        path = Path(rel['stock']['file'])
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == rel['stock']['sha256']:
            print(f'{path}: already here, checksum OK')
            continue
        try:
            data = patch.fetch_stock(rel)
        except patch.Refuse as e:
            sys.exit(f'Stopped: {e}')
        if len(data) != rel['stock']['bytes'] or hashlib.sha256(data).hexdigest() != rel['stock']['sha256']:
            sys.exit(f'Stopped: the download is not {path} as OM publishes it (checksum differs); nothing was written')
        path.write_bytes(data)
        print(f'{path}: downloaded, checksum OK')


if __name__ == '__main__':
    main()
