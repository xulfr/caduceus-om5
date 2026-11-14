@echo off
rem Caduceus for OM-5: double-click to make the SD card files in the "card" folder next to this file.
cd /d "%~dp0"
py -3 patch.py --out card || python patch.py --out card
pause
