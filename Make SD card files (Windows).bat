@echo off
setlocal
rem Caduceus for OM-5: double-click to make the SD card files in the "card" folder next to this file.
cd /d "%~dp0"
py -3 -c "pass" >nul 2>&1
if errorlevel 1 (
    python patch.py --out card
) else (
    py -3 patch.py --out card
)
set "patch_status=%errorlevel%"
pause
exit /b %patch_status%
