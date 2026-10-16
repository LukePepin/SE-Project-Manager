@echo off
rem Status: DECIDED (D-034). Windows: double-click to start the Games-People-Play dashboard (local only) and open it. Close this window to stop it.
cd /d "%~dp0.."
python dashboard\server.py --open
