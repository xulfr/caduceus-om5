#!/bin/bash
# Caduceus for OM-5: double-click to make the SD card files in the "card" folder next to this file.
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null; then echo "Python 3 is needed: install it from https://www.python.org/downloads/ and try again."; read -r -p "Press Enter to close."; exit 1; fi
python3 patch.py --out card
read -r -p "Press Enter to close."
