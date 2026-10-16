"""Serve the dashboard locally: projects, their pages, /start runs, notes and the library (D-034, D-047, D-052).

Status: DECIDED (D-034) (Luke, 10/8: "the dashboard might also have the tools to create a
project, insert notes and step by step recommend runs of skills so I don't need to use the terminal").

Safety:
  - binds to 127.0.0.1 only; every form carries a token made fresh each run, and requests from
    another origin are refused, so other web pages can't drive it
  - New project makes a folder with notes.md, the brain dump (brain_dump.md, verbatim) and a
    .gpp-project marker, nothing else. The documents
    still come from /elicit → /warden → /initialize (D-032). It never runs git, Claude or any skill.
  - Notes are appended to <project>/notes.md, only for projects the dashboard found under its roots.
  - /start (D-047, Luke 10/10: "integrate it all into the dashboard"): the Start form runs the /start
    engine. Its Claude steps run in the background through the Claude Code CLI on Luke's plan; the page
    polls until each finishes. A run touches only folders directly under the roots, and nothing is set up
    until Luke presses Approve.
  - Project pages (D-052): open, reveal or edit files and folders, tick plan steps, answer explain-backs and
    accept skills. Only paths inside a project on the dashboard or the library repo; Open never runs a
    program (other file types are only shown in Finder); edits touch only checklist lines, explain-back
    answers (Luke's words, verbatim) and a skill's status line when Luke presses Accept.
Standard library only.

Usage:
  python dashboard/server.py [--open | --app] [--port 8765] [--roots ~/Projects ~/Research ~/School]
  --app opens a window with no browser chrome (Chrome, Edge or Brave app mode) and stops the server
  when the window has been closed for a while; dashboard/make_app.py builds the macOS app around it.
"""

from __future__ import annotations

import argparse
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_dashboard as bd  # noqa: E402
import install_skills as inst  # noqa: E402

NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,59}$")


class Refused(Exception):
    pass


def create_project(roots: list[Path], root: str, name: str, kind: str, dump: str, when: str | None = None) -> Path:
    name = name.strip()
    if not NAME.match(name) or name.endswith(".") or ".." in name:
        raise Refused("Name: letters, numbers, spaces, - _ . (up to 60), starting with a letter or number.")
    base = Path(root).expanduser()
    if base.resolve() not in [r.resolve() for r in roots]:
        raise Refused("That folder is not one of the dashboard's roots.")
    if kind not in ("code", "household"):
        raise Refused("Kind must be code or household.")
    target = base / name
    if target.exists():
        raise Refused(f"{target} already exists.")
    target.mkdir(parents=True)
    (target / bd.CANDIDATE_MARK).write_text(kind + "\n", encoding="utf-8")
    stamp = when or datetime.now().strftime("%Y-%m-%d %H:%M")
    (target / "notes.md").write_text(
        f"# {name}: notes\n\nLuke's notes, newest last. Created from the dashboard on {stamp}; not a project yet:"
        f" next is /elicit, then /warden, then /initialize.\n", encoding="utf-8")
    if dump.strip():
        (target / "brain_dump.md").write_text(
            f"# Brain dump: {name}, {stamp}\n\n**Verbatim.** Typed by Luke in the dashboard. /elicit uses it as its"
            f" Stage 0 dump.\n\n{dump.strip()}\n", encoding="utf-8")
    return target


def add_note(known: list[Path], project: str, text: str, when: str | None = None) -> Path:
    target = Path(project)
    if target.resolve() not in [k.resolve() for k in known]:
        raise Refused("Notes can only go to a project shown on the dashboard.")
    text = text.strip()
    if not text:
        raise Refused("The note is empty.")
    notes = target / "notes.md"
    head = "" if notes.exists() else f"# {target.name}: notes\n\nLuke's notes, newest last.\n"
    with open(notes, "a", encoding="utf-8") as f:
        f.write(f"{head}\n## {when or datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{text[:4000]}\n")
    return notes


def known_record(roots: list[Path], r: str) -> Path:
    """A /start record folder inside a project directly under one of the roots, or Refused."""
    rec = Path(r).expanduser().resolve()
    for root in roots:
        try:
            rel = rec.relative_to(root.expanduser().resolve())
        except ValueError:
            continue
        if len(rel.parts) >= 3 and (rec / bd.engine().STATE).exists():
            return rec
    raise Refused("That is not a /start record under the dashboard's folders.")


def start_run(roots: list[Path], form: dict) -> Path:
    """The Start form: a new folder or an existing one directly under a root, then the engine's first stop."""
    eng = bd.engine()
    kind, tier, dump = form.get("kind", "code"), form.get("tier", "small"), form.get("dump", "")
    if not dump.strip():
        raise Refused("The brain dump is empty.")
    if tier not in eng.TIERS or kind not in ("code", "household"):
        raise Refused("Pick a size and a kind.")
    existing = form.get("existing", "").strip()
    if existing:
        target = Path(existing)
        if target.resolve() not in [f.resolve() for f in bd.folders(roots)]:
            raise Refused("That folder is not directly under one of the dashboard's folders.")
        created = False
    else:
        if not form.get("name", "").strip():
            raise Refused("Name the new folder, or pick an existing project.")
        target = create_project(roots, form.get("root", ""), form.get("name", ""), kind, "")
        created = True
    try:
        return eng.new(target, kind, tier, dump, name=target.name, created=created)
    except eng.Refused as e:
        raise Refused(str(e))


class Jobs:
    """Background Claude steps, at most one per record."""

    def __init__(self, runner=None):
        self.runner = runner
        self.busy: set[str] = set()
        self.lock = threading.Lock()

    def kick(self, record: Path) -> None:
        key = str(record)
        with self.lock:
            if key in self.busy:
                return
            self.busy.add(key)

        def work():
            try:
                eng = bd.engine()
                eng.step(record, runner=self.runner or eng.run_claude)
            finally:
                with self.lock:
                    self.busy.discard(key)
        threading.Thread(target=work, daemon=True).start()


OPENABLE = {".md", ".txt", ".csv", ".json", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".html", ".py", ".ipynb",
            ".docx", ".xlsx", ".pptx", ".tex", ".bib", ".yaml", ".yml", ".toml", ".log", ".ics"}


def open_path(path: Path, how: str) -> str:
    """Open a folder or file the way Luke asked (D-052). Never runs a program: other files are only revealed."""
    mac, win = sys.platform == "darwin", sys.platform.startswith("win")
    folder = path if path.is_dir() else path.parent
    if how == "reveal" or (how == "open" and path.is_file() and path.suffix.lower() not in OPENABLE):
        cmd = ["open", "-R", str(path)] if mac else ["explorer", f"/select,{path}"] if win else ["xdg-open", str(folder)]
        said = "Shown in Finder" if mac else "Shown"
    elif how == "terminal":
        cmd = ["open", "-a", "Terminal", str(folder)] if mac else ["cmd", "/c", "start", "cmd", "/K", f"cd /d {folder}"] if win \
            else ["x-terminal-emulator", "--working-directory", str(folder)]
        said = "Opened a terminal there"
    elif how == "editor":
        code = shutil.which("code")
        cmd = (["open", "-a", "Visual Studio Code", str(path)] if mac and Path("/Applications/Visual Studio Code.app").exists()
               else [code, str(path)] if code else None)
        if cmd is None:
            raise Refused("VS Code was not found.")
        said = "Opened in VS Code"
    else:
        cmd = ["open", str(path)] if mac else ["explorer", str(path)] if win else ["xdg-open", str(path)]
        said = "Opened in Finder" if path.is_dir() and mac else "Opened"
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return said


def make_handler(roots: list[Path], repo: Path, token: str, runner=None, beat=None, opener=open_path):
    jobs = Jobs(runner)
    started = time.time()

    def orphaned(rec: Path, st: dict) -> dict:
        """A step marked busy before this server started died with the old one: say so now, not in 10 minutes."""
        if st.get("busy") and st.get("busy_since", 0) < started and str(rec) not in jobs.busy:
            st.update(busy="", busy_since=0, error="The dashboard closed while Claude was working on this step.")
            bd.engine().save(rec, st)
        return st

    def project_of(path: str | Path) -> bd.Project | None:
        """The dashboard project that contains path, or None."""
        try:
            target = Path(path).expanduser().resolve()
        except (OSError, ValueError):
            return None
        for p in bd.projects(roots):
            root = p.path.resolve()
            if target == root or root in target.parents:
                return p
        return None

    def allowed(path: str | Path) -> Path:
        """A path inside a known project or the library repo: the only places the app opens, reads or edits."""
        target = Path(path).expanduser().resolve()
        if not target.exists():
            raise Refused("That file or folder does not exist.")
        lib = repo.resolve()
        if project_of(target) or target == lib or lib in target.parents:
            return target
        raise Refused("That is outside the dashboard's projects.")

    def project_stamp(p: bd.Project) -> str:
        files = [p.path / "notes.md", p.path / "plan.md"] + list(p.path.glob("elicitation/*/*")) + list(p.path.glob("docs/se/*.md"))
        mt = max((f.stat().st_mtime for f in files if f.exists()), default=0)
        return bd.signature([p]) + f"{mt:.0f}"

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep the terminal quiet
            pass

        def send_body(self, body: bytes | str, ctype: str = "text/html; charset=utf-8", status: int = 200):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def send_json(self, data: dict, status: int = 200):
            import json
            self.send_body(json.dumps(data), "application/json", status)

        def send_page(self, message: str = "", status: int = 200, selected: str = ""):
            ok = all(v == "installed" for v in inst.status(repo).values())
            self.send_body(bd.page(bd.projects(roots), bd.skills(repo), roots, token=token, message=message,
                                   skills_ok=ok, selected=selected), status=status)

        def redirect(self, where: str, message: str = ""):
            if not where.startswith("/") or where.startswith("//"):
                where = "/"
            if message:
                where += ("&" if "?" in where else "?") + "msg=" + quote(message)
            self.send_response(303)
            self.send_header("Location", where)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            if beat:
                beat()
            url = urlsplit(self.path)
            route, query = url.path, {k: v[0] for k, v in parse_qs(url.query).items()}
            msg = query.get("msg", "")[:500]
            pg = bd.pages()
            try:
                if route == "/stamp":
                    p = project_of(query["p"]) if "p" in query else None
                    self.send_body(project_stamp(p) if p else bd.signature(bd.projects(roots)), "text/plain")
                elif route in ("/run", "/run/state"):
                    rec = known_record(roots, query.get("r", ""))
                    st = orphaned(rec, bd.engine().load(rec))
                    if route == "/run/state":
                        self.send_body(bd.engine().phase(st), "text/plain")
                        return
                    if st["status"] in ("asking", "planning") and not st.get("busy") and not st.get("error"):
                        jobs.kick(rec)
                        st = bd.engine().load(rec)
                    self.send_body(bd.run_page(st, rec, token, msg))
                elif route == "/project":
                    p = project_of(query.get("p", ""))
                    if not p or p.path.resolve() != Path(query.get("p", "")).expanduser().resolve():
                        raise Refused("That project is not on the dashboard.")
                    self.send_body(pg.project_page(p, bd.detail(p), token, msg, project_stamp(p)))
                elif route == "/doc":
                    doc = allowed(query.get("p", ""))
                    if not doc.is_file() or doc.suffix.lower() not in (".md", ".txt"):
                        raise Refused("Only Markdown and text files open in the app; use Open for the rest.")
                    self.send_body(pg.doc_page(doc, project_of(doc), token, msg))
                elif route == "/new":
                    self.send_body(pg.new_page(roots, token, query.get("existing", ""), msg))
                elif route == "/library":
                    self.send_body(pg.library_page(bd.skills(repo), inst.review_state(repo), inst.status(repo), token, msg))
                elif route == "/":
                    self.send_page(msg)
                else:
                    self.send_error(404)
            except Refused as e:
                self.send_page(f"Not found: {e}", status=404)

        def run_post(self, form: dict) -> None:
            eng = bd.engine()
            rec = known_record(roots, form.get("r", ""))
            try:
                if self.path == "/run/answer":
                    answers = {k[2:]: v for k, v in form.items() if k.startswith("a_")}
                    eng.answer(rec, answers, stop=form.get("action") == "skip")
                    jobs.kick(rec)
                elif self.path == "/run/approve":
                    budget = form.get("budget", "").strip()
                    try:
                        hours = float(budget) if budget else None
                    except ValueError:
                        raise Refused("The budget is a number of hours.")
                    eng.approve(rec, hours, form.get("accept_list", []), form.get("override", ""),
                                by="Luke, in the dashboard")
                elif self.path == "/run/stop":
                    eng.stop(rec)
                elif self.path == "/run/retry":
                    st = eng.load(rec)
                    st.update(busy="", busy_since=0, error="")
                    eng.save(rec, st)
                    jobs.kick(rec)
            except eng.Refused as e:
                self.send_body(bd.run_page(eng.load(rec), rec, token, message=f"Not done: {e}"), status=400)
                return
            self.redirect(f"/run?r={quote(str(rec))}")

        def do_POST(self):
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            if origin and origin not in (f"http://{host}",):
                self.send_error(403, "Cross-origin request refused")
                return
            if beat:
                beat()
            length = min(int(self.headers.get("Content-Length") or 0), 100000)
            raw = parse_qs(self.rfile.read(length).decode("utf-8"))
            form = {k: v[0] for k, v in raw.items()}
            form["accept_list"] = raw.get("accept", [])
            if not secrets.compare_digest(form.get("token", ""), token):
                self.send_error(403, "Bad token: reload the page")
                return
            back = form.get("back", "/")
            try:
                if self.path.startswith("/run/"):
                    self.run_post(form)
                    return
                if self.path == "/open":  # fetch from the page: JSON back
                    try:
                        said = opener(allowed(form.get("path", "")), form.get("how", "open"))
                        self.send_json({"ok": True, "said": said})
                    except Refused as e:
                        self.send_json({"ok": False, "error": str(e)}, 400)
                    return
                if self.path == "/project/step":
                    try:
                        plan = allowed(form.get("plan", ""))
                        if plan.name != "plan.md":
                            raise Refused("Only a plan.md checklist can be ticked here.")
                        bd.set_step(plan, int(form.get("line", "-1")), bool(form.get("done")))
                        self.send_json({"ok": True})
                    except (Refused, ValueError) as e:
                        self.send_json({"ok": False, "error": str(e)}, 400)
                    return
                if self.path == "/group/move":  # drag and drop, or the project page's Folder menu (D-053)
                    try:
                        p = project_of(form.get("path", ""))
                        if not p or p.path.resolve() != Path(form.get("path", "")).resolve():
                            raise Refused("That project is not on the dashboard.")
                        bd.assign_group(str(p.path), form.get("group", ""))
                        self.send_json({"ok": True})
                    except (Refused, ValueError) as e:
                        self.send_json({"ok": False, "error": str(e)}, 400)
                    return
                if self.path in ("/group/add", "/group/rename", "/group/delete", "/group/order"):
                    try:
                        if self.path == "/group/add":
                            msg = f"Added the folder {bd.add_group(form.get('name', ''))}. Drag projects into it."
                        elif self.path == "/group/rename":
                            msg = f"Renamed it {bd.rename_group(form.get('old', ''), form.get('new', ''))}."
                        elif self.path == "/group/delete":
                            n = bd.delete_group(form.get("name", ""))
                            msg = f"Removed the folder; {n} project{'s' if n != 1 else ''} went back under {'their' if n != 1 else 'its'} root folder."
                        else:
                            bd.move_group(form.get("name", ""), int(form.get("step", "0")))
                            msg = ""
                    except ValueError as e:
                        raise Refused(str(e))
                    self.redirect("/", msg)
                    return
                if self.path == "/project/addstep":
                    plan = allowed(form.get("plan", ""))
                    if plan.name != "plan.md":
                        raise Refused("Steps can only be added to a plan.md.")
                    try:
                        bd.add_step(plan, form.get("text", ""))
                    except ValueError as e:
                        raise Refused(str(e))
                    p = project_of(plan)
                    self.redirect(f"/project?p={quote(str(p.path))}" if p else "/", "Step added.")
                    return
                if self.path == "/explain":
                    doc = allowed(form.get("doc", ""))
                    if doc.suffix != ".md":
                        raise Refused("Explain-backs live in Markdown documents.")
                    try:
                        bd.answer_explain_back(doc, int(form.get("n", "-1")), form.get("answer", ""))
                    except ValueError as e:
                        raise Refused(str(e))
                    self.redirect(back, "Your answer is saved, word for word.")
                    return
                if self.path == "/accept":
                    name = form.get("skill", "")
                    msg = accept_skill(repo, name)
                    self.redirect("/library", msg)
                    return
                if self.path == "/healthcheck":
                    out = run_healthcheck(repo)
                    self.send_body(bd.pages().library_page(bd.skills(repo), inst.review_state(repo), inst.status(repo),
                                                           token, "Healthcheck finished.", out))
                    return
                if self.path == "/start":
                    rec = start_run(roots, form)
                    if (rec / bd.engine().STATE).exists():
                        jobs.kick(rec)
                        self.redirect(f"/run?r={quote(str(rec))}")
                        return
                    handoff = bd.engine().TIERS["large"]["handoff"]
                    self.redirect(f"/project?p={quote(str(rec))}",
                                  f"Saved the dump to {rec / 'brain_dump.md'}. Large projects run the full gate in a Claude"
                                  f" chat: copy the prompt below ({handoff}).")
                    return
                if self.path == "/new":
                    t = create_project(roots, form.get("root", ""), form.get("name", ""),
                                       form.get("kind", "code"), form.get("dump", ""))
                    msg = f"Created {t}."
                elif self.path == "/note":
                    n = add_note([p.path for p in bd.projects(roots)], form.get("project", ""), form.get("text", ""))
                    msg = f"Note added to {n.parent.name}."
                elif self.path == "/archive":
                    known = {str(p.path) for p in bd.projects(roots)}
                    target = form.get("project", "")
                    if target not in known:
                        raise Refused("That project is not on the dashboard.")
                    archived = bd.load_archive()
                    if target in archived:
                        archived.discard(target)
                        msg = f"Moved {Path(target).name} back to active."
                    else:
                        archived.add(target)
                        msg = f"Archived {Path(target).name}. Nothing in its folder changed."
                    bd.save_archive(archived)
                elif self.path == "/install":
                    res = inst.install(repo)
                    blocked = [k for k, v in res.items() if v.startswith("blocked")]
                    msg = (f"Installed {len(res) - len(blocked)} skills for every Claude Code chat."
                           + (f" Blocked by existing skills: {', '.join(blocked)}." if blocked else "")
                           + " Open a new chat to use them.")
                    back = "/library"
                else:
                    self.send_error(404)
                    return
                if "back" in form or self.path == "/install":
                    self.redirect(back, msg)
                else:
                    self.send_page(msg)
            except Refused as e:
                if self.path.startswith("/start"):
                    self.send_body(bd.pages().new_page(roots, token, form.get("existing", ""), f"Not done: {e}"), status=400)
                elif "back" in form:
                    self.redirect(back, f"Not done: {e}")
                else:
                    self.send_page(f"Not done: {e}", status=400)

    return Handler


def accept_skill(repo: Path, name: str) -> str:
    """Luke accepts a skill after answering its explain-back in the dashboard (D-052; SAFE-03)."""
    md = repo / ".claude" / "skills" / name / "SKILL.md"
    if not re.match(r"^[a-z0-9-]+$", name) or not md.exists():
        raise Refused("No such skill.")
    text = md.read_text(encoding="utf-8")
    ebs = bd.explain_back_list(text)
    if not ebs or not ebs[-1][1]:
        raise Refused("Answer its explain-back first.")
    today = datetime.now().strftime("%Y-%m-%d")
    text = re.sub(r"\*\*Status:\s*(PROPOSED|REVIEWED|DRAFT)\*\*",
                  f"**Status: ACCEPTED** (Luke answered the explain-back in the dashboard, {today}; was \\1)", text, count=1)
    if "**Status: ACCEPTED**" not in text:
        raise Refused("Its status line could not be updated; accept it in a chat.")
    md.write_text(text, encoding="utf-8")
    inst.accept(name, f"Luke, explain-back {today} (dashboard)", repo)
    return f"/{name} is accepted and pinned. Press Install to use it in every chat."


def run_healthcheck(repo: Path) -> str:
    script = repo / ".claude" / "skills" / "healthcheck" / "healthcheck.py"
    py = repo / ".venv" / "bin" / "python"
    try:
        out = subprocess.run([str(py if py.exists() else sys.executable), str(script)], capture_output=True, text=True,
                             timeout=300, cwd=str(repo))
    except (OSError, subprocess.SubprocessError) as e:
        return f"The healthcheck could not run: {e}"
    lines = (out.stdout + out.stderr).strip().splitlines()
    bad = [ln for ln in lines if "| fail |" in ln]
    return "\n".join(bad + lines[-1:]) if bad else (lines[-1] if lines else "No output.")


def already_running(url: str) -> bool:
    """True when our dashboard answers at url (checked before starting a second copy)."""
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return b"<title>Games-People-Play</title>" in r.read(4000)
    except OSError:
        return False


APP_BROWSERS = [  # Chromium browsers that open a page as a window with no tabs or address bar
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


def open_app_window(url: str) -> str:
    """Open url as an app window; fall back to the default browser. Returns what was used."""
    for exe in APP_BROWSERS + [shutil.which(n) or "" for n in ("google-chrome", "chromium", "msedge")]:
        if exe and Path(exe).exists():
            profile = Path.home() / ".games-people-play" / "app-window"
            profile.mkdir(parents=True, exist_ok=True)
            subprocess.Popen([exe, f"--app={url}", f"--user-data-dir={profile}", "--no-first-run",
                              "--window-size=1200,860"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return Path(exe).stem
    webbrowser.open(url)
    return "default browser"


def watch_idle(server, last: list, idle: float) -> None:
    """Stop the server once no page has polled it for `idle` seconds (the window was closed)."""
    def loop():
        while True:
            time.sleep(min(10.0, idle / 3))
            if time.time() - last[0] > idle:
                server.shutdown()
                return
    threading.Thread(target=loop, daemon=True).start()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--roots", nargs="+", default=bd.DEFAULT_ROOTS)
    ap.add_argument("--repo", type=Path, default=bd.REPO)
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--open", action="store_true", help="open in the default browser")
    ap.add_argument("--app", action="store_true", help="open as an app window; stop when it has been closed a while")
    ap.add_argument("--idle-exit", type=float, default=0, help="stop after this many seconds with no page open")
    args = ap.parse_args(argv)
    roots = [Path(r).expanduser() for r in args.roots]
    token = secrets.token_urlsafe(24)
    last = [time.time()]

    def beat():
        last[0] = time.time()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(roots, args.repo, token, beat=beat))
    except OSError:
        url = f"http://127.0.0.1:{args.port}/"
        if already_running(url):
            print(f"The dashboard is already running at {url}; opening it.")
            if args.app:
                open_app_window(url)
            elif args.open:
                webbrowser.open(url)
            return 0
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(roots, args.repo, token, beat=beat))
        print(f"Port {args.port} is taken by another program; using a free port instead.")
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"Games-People-Play dashboard at {url} (local only). Ctrl-C to stop.", flush=True)
    idle = args.idle_exit or (90 if args.app else 0)
    if args.app:
        print(f"Opened in {open_app_window(url)}.", flush=True)
    elif args.open:
        webbrowser.open(url)
    if idle:
        watch_idle(server, last, idle)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
