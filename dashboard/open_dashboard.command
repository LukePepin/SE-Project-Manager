#!/bin/sh
# Status: DECIDED (D-034). macOS: double-click to start the Games-People-Play dashboard (local only) and open it. Close this window to stop it.
cd "$(dirname "$0")/.." && python3 dashboard/server.py --open
