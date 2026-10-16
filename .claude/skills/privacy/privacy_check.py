"""Block a push that would publish private terms or secrets (SAFE-01, SAFE-02).

Status: PROPOSED (AI-drafted by Claude on 2026-10-08 from Luke's direction, D-015; generalized
from I-Know-Puck's scripts/check_public.py; not reviewed by Luke).

What it checks, in every file git would publish:
  - Luke's global private terms, in `.privacy-terms.global` in the Games-People-Play repo
    (git-ignored there; found through $GPP_PRIVACY_GLOBAL, the library this script came from,
    or ~/Projects/Games-People-Play), applied to every project (D-033)
  - the project's own private terms, one per line in `.privacy-terms` at its repo root
    (`term` or `term  # label`). Neither term list may ever be published.
  - secrets: private keys, AWS / GitHub / Slack / Google / sk- style API keys,
    and `api_key = "..."`-style assignments
  - tracked `.env` files
A line containing `privacy: allow` is skipped (a deliberate, reviewable exception).
Hits are reported by file, line and label. The matched text itself is never printed.

Modes:
  python privacy_check.py                   scan tracked + untracked, non-ignored files (manual run)
  python privacy_check.py --ref <sha>       scan the files of one commit (the pre-push hook does this)
  python privacy_check.py --all-history    scan every commit reachable from any branch (before sharing a repo)
  python privacy_check.py --install-hook    install the pre-push hook and ignore .privacy-terms
Exit code: 0 clean, 1 hits found, 2 usage or git error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

TERMS_FILE = ".privacy-terms"
GLOBAL_FILE = ".privacy-terms.global"
ALLOW = "privacy: allow"
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".pkl", ".parquet", ".zip", ".gz", ".woff", ".woff2"}
SECRETS = [
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "GitHub token"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "Google API key"),
    (re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{24,}"), "API key (sk-)"),
    (re.compile(r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*['\"][^'\"\s]{8,}['\"]"),
     "credential assignment"),
]
HOOK = """#!/bin/sh
# Games-People-Play privacy check (SAFE-01): blocks a push that would publish private terms or secrets.
# Installed by privacy_check.py --install-hook. Remove this file to uninstall.
cd "$(git rev-parse --show-toplevel)" || exit 1
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
status=0
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$local_ref" in refs/heads/private*) echo "pre-push: refusing to push $local_ref (private branch)"; exit 1;; esac
  [ "$local_sha" = "0000000000000000000000000000000000000000" ] && continue
  "$PY" "{script}" --ref "$local_sha" || status=1
done
exit $status
"""


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout


def global_terms_path() -> Path | None:
    env = os.environ.get("GPP_PRIVACY_GLOBAL")
    if env:
        return Path(env).expanduser()
    for repo in (Path(__file__).resolve().parents[3], Path.home() / "Projects" / "Games-People-Play"):
        if (repo / GLOBAL_FILE).exists():
            return repo / GLOBAL_FILE
    return None


def load_terms(root: Path, include_global: bool = True) -> list[tuple[str, str]]:
    terms = read_terms(root / TERMS_FILE)
    g = global_terms_path() if include_global else None
    return terms + (read_terms(g) if g else [])


def read_terms(path: Path) -> list[tuple[str, str]]:
    if not path.exists():
        return []
    terms = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        term, _, label = line.partition("  #")
        terms.append((term.strip(), label.strip() or "private term"))
    return [(t, label) for t, label in terms if t]


def publishable(root: Path, ref: str | None) -> list[tuple[str, str | None]]:
    """(path, text) pairs; text is None for files that are not UTF-8 text."""
    if ref:
        names = git(root, "ls-tree", "-r", "--name-only", ref).splitlines()
        out = []
        for n in names:
            if Path(n).suffix.lower() in SKIP_SUFFIX:
                continue
            blob = subprocess.run(["git", "cat-file", "-p", f"{ref}:{n}"], cwd=root, capture_output=True)
            try:
                out.append((n, blob.stdout.decode("utf-8")))
            except UnicodeDecodeError:
                out.append((n, None))
        return out
    names = git(root, "ls-files", "--cached", "--others", "--exclude-standard").splitlines()
    out = []
    for n in names:
        f = root / n
        if not f.is_file() or f.is_symlink() or f.suffix.lower() in SKIP_SUFFIX:
            continue
        try:
            out.append((n, f.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            out.append((n, None))
    return out


def scan(files: list[tuple[str, str | None]], terms: list[tuple[str, str]]) -> list[str]:
    hits = []
    for name, text in files:
        base = Path(name).name
        if base in (TERMS_FILE, GLOBAL_FILE):
            hits.append(f"{name}: the private term list would be published (it must be git-ignored)")
            continue
        if base == ".env" or (base.endswith(".env") and not base.endswith(".example.env")):
            hits.append(f"{name}: .env file")
        if text is None:
            continue
        for no, line in enumerate(text.splitlines(), 1):
            if ALLOW in line:
                continue
            low = line.lower()
            for term, label in terms:
                if term.lower() in low:
                    hits.append(f"{name}:{no}: {label}")
            for pattern, label in SECRETS:
                if pattern.search(line):
                    hits.append(f"{name}:{no}: {label}")
    return sorted(set(hits))


def install_hook(root: Path, script: Path, force: bool = False) -> str:
    hooks = Path(git(root, "rev-parse", "--git-path", "hooks").strip())
    hooks = hooks if hooks.is_absolute() else root / hooks
    hooks.mkdir(parents=True, exist_ok=True)
    hook = hooks / "pre-push"
    try:
        rel = script.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = script.resolve().as_posix()
    body = HOOK.replace("{script}", rel)
    if hook.exists() and hook.read_text(encoding="utf-8") != body and not force:
        raise FileExistsError(f"{hook} exists and differs; rerun with --force to replace it")
    hook.write_text(body, encoding="utf-8")
    hook.chmod(0o755)
    ignore = root / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
    missing = [f for f in (TERMS_FILE, GLOBAL_FILE) if f not in lines]
    if missing:
        ignore.write_text("\n".join(lines + missing) + "\n", encoding="utf-8")
    return str(hook)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--ref", help="scan the files of this commit instead of the working tree")
    p.add_argument("--all-history", action="store_true", help="scan every commit, not just the working tree")
    p.add_argument("--install-hook", action="store_true")
    p.add_argument("--force", action="store_true", help="replace an existing, different pre-push hook")
    args = p.parse_args(argv)
    try:
        root = Path(git(args.repo, "rev-parse", "--show-toplevel").strip())
        if args.install_hook:
            print(f"Installed {install_hook(root, Path(__file__), args.force)}; {TERMS_FILE} is git-ignored.")
            return 0
        terms = load_terms(root)
        if args.all_history:
            hits = []
            for sha in git(root, "rev-list", "--all").split():
                hits += [f"{sha[:10]} {h}" for h in scan(publishable(root, sha), terms)]
            if hits:
                print(f"Private data found in git history ({len(set(hits))} hits); a rewrite is Luke's decision:")
                for h in sorted(set(hits)):
                    print("  " + h)
                return 1
            print(f"OK: every commit checked against {len(terms)} private terms; nothing private in history.")
            return 0
        files = publishable(root, args.ref)
    except (subprocess.CalledProcessError, FileExistsError) as e:
        print(f"privacy check: {e}", file=sys.stderr)
        return 2
    hits = scan(files, terms)
    where = f"commit {args.ref[:10]}" if args.ref else "the working tree"
    if hits:
        print(f"Private data found in {where} (would be published):")
        for h in hits:
            print("  " + h)
        print("Fix the files, or mark a deliberate exception with 'privacy: allow' on that line. Never push with --no-verify.")
        return 1
    print(f"OK: {len(files)} files in {where} checked against {len(terms)} private terms (project + global) and"
          f" {len(SECRETS)} secret patterns; nothing private found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
