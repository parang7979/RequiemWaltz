@echo off
rem SpriteCut production viewer launcher
setlocal DisableDelayedExpansion
where.exe py.exe >nul 2>nul
if errorlevel 1 (
    python "%~dp0spritecut-viewer.py"
) else (
    py -3 "%~dp0spritecut-viewer.py"
)
if errorlevel 1 pause
