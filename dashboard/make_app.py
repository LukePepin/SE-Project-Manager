"""Build the Games-People-Play Mac app: the dashboard in its own window, no browser (D-049).

Status: PROPOSED (AI-drafted by Claude on 2026-10-10 from Luke's direction, "move it out of the port into a
'application' rather than a website"; not reviewed by Luke).

With Xcode's command-line tools (swiftc), it compiles dashboard/app/GamesPeoplePlay.swift into a native app:
a WebKit window that starts the dashboard server and stops it when the window closes. Without swiftc, the
app is a small launcher that runs `server.py --app` (a Chrome, Edge or Brave app window, else the default
browser; the server stops a while after the window closes). Either way the app runs this repo's code, so
library changes reach it when it is reopened. Rebuild when dashboard/app/ changes or the repo moves.

Standard library only. It writes one folder, the app, into /Applications (else ~/Applications), and
replaces an older copy of it, including one an earlier build left in ~/Applications.

Usage:
  python3 dashboard/make_app.py [--dest /Applications] [--python PATH] [--port 8765]
"""

from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NAME = "Games-People-Play"
EXE = "GamesPeoplePlay"
SWIFT = REPO / "dashboard" / "app" / "GamesPeoplePlay.swift"
ICON_SWIFT = REPO / "dashboard" / "app" / "icon.swift"


def default_dest() -> Path:
    """/Applications (where Finder, Launchpad and the Dock look) when writable, else ~/Applications."""
    system = Path("/Applications")
    import os
    return system if os.access(system, os.W_OK) else Path.home() / "Applications"


def make_icon(swift_cmd: list[str], resources: Path, tmp: Path) -> bool:
    """Draw the icon with icon.swift, then build AppIcon.icns with sips and iconutil (both ship with macOS)."""
    if not (shutil.which("sips") and shutil.which("iconutil")):
        return False
    exe, png = tmp / "icon", tmp / "icon.png"
    if subprocess.run(swift_cmd + ["-o", str(exe), str(ICON_SWIFT), "-framework", "Cocoa"], capture_output=True).returncode:
        return False
    if subprocess.run([str(exe), str(png)], capture_output=True).returncode or not png.exists():
        return False
    iconset = tmp / "AppIcon.iconset"
    iconset.mkdir()
    for px in (16, 32, 128, 256, 512):
        for scale in (1, 2):
            name = f"icon_{px}x{px}{'@2x' if scale == 2 else ''}.png"
            subprocess.run(["sips", "-z", str(px * scale), str(px * scale), str(png), "--out", str(iconset / name)],
                           capture_output=True)
    resources.mkdir(parents=True, exist_ok=True)
    return subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(resources / "AppIcon.icns")],
                          capture_output=True).returncode == 0


def default_python() -> str:
    venv = REPO / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else (shutil.which("python3") or "/usr/bin/python3")


def info_plist(python: str, port: int) -> dict:
    return {"CFBundleName": NAME, "CFBundleDisplayName": NAME, "CFBundleIdentifier": "local.games-people-play",
            "CFBundleExecutable": EXE, "CFBundlePackageType": "APPL", "CFBundleVersion": "1",
            "CFBundleShortVersionString": "1.0", "LSMinimumSystemVersion": "12.0", "NSHighResolutionCapable": True,
            "NSAppTransportSecurity": {"NSAllowsLocalNetworking": True},
            "CFBundleIconFile": "AppIcon",
            "GPPRepo": str(REPO), "GPPPython": python, "GPPPort": port}


def build(dest: Path, python: str, port: int, swiftc: str | None = None) -> tuple[Path, str]:
    """Returns (app path, 'native' or 'launcher')."""
    swiftc = swiftc if swiftc is not None else (shutil.which("swiftc") or ("xcrun" if shutil.which("xcrun") else ""))
    with tempfile.TemporaryDirectory() as tmp:
        app = Path(tmp) / f"{NAME}.app"
        macos = app / "Contents" / "MacOS"
        macos.mkdir(parents=True)
        (app / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info_plist(python, port)))
        kind = "launcher"
        if swiftc:
            swift_cmd = [swiftc] if swiftc != "xcrun" else ["xcrun", "swiftc"]
            cmd = swift_cmd + ["-O", "-o", str(macos / EXE), str(SWIFT), "-framework", "Cocoa", "-framework", "WebKit"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                kind = "native"
            else:  # say why, instead of quietly building the browser launcher
                print("Swift compile failed; building the browser launcher instead:\n" + (res.stderr or res.stdout)[-2000:])
            make_icon(swift_cmd, app / "Contents" / "Resources", Path(tmp))
        if kind == "launcher":
            script = macos / EXE
            script.write_text(f'#!/bin/sh\nexport PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"\n'
                              f'exec "{python}" "{REPO}/dashboard/server.py" --app --port {port}'
                              f' >>"$HOME/Library/Logs/{NAME}.log" 2>&1\n', encoding="utf-8")
            script.chmod(0o755)
        if shutil.which("codesign"):  # ad-hoc signature: a local build Gatekeeper accepts
            subprocess.run(["codesign", "--force", "--deep", "-s", "-", str(app)], capture_output=True)
        dest.mkdir(parents=True, exist_ok=True)
        out = dest / app.name
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(app, out, symlinks=True)
    old = Path.home() / "Applications" / app.name  # an earlier build in the hidden per-user folder
    if out != old and old.exists() and (old / "Contents" / "Info.plist").exists():
        if plistlib.loads((old / "Contents" / "Info.plist").read_bytes()).get("CFBundleIdentifier") == "local.games-people-play":
            shutil.rmtree(old)
    if shutil.which("touch"):
        subprocess.run(["touch", str(out)], capture_output=True)  # Finder and the Dock pick up the new icon
    return out, kind


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest", type=Path, default=None, help="default: /Applications, else ~/Applications")
    ap.add_argument("--python", default=default_python())
    ap.add_argument("--port", type=int, default=8765)
    args = ap.parse_args(argv)
    if sys.platform != "darwin":
        print("The app is for macOS. On Windows, double-click dashboard\\open_dashboard.bat"
              " (or run: python dashboard\\server.py --app).")
        return 2
    out, kind = build((args.dest or default_dest()).expanduser(), args.python, args.port)
    print(f"Built {out} ({'native window' if kind == 'native' else 'launcher: no swiftc, so it opens an app-mode browser window'}).")
    print("Open it from Applications, Launchpad or Spotlight. To keep it in the Dock: while it runs,"
          " right-click its Dock icon > Options > Keep in Dock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
