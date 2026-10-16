"""The dashboard's pages: home, one page per project, new project, library, documents and /start runs (D-052).

Status: PROPOSED (AI-drafted by Claude on 2026-10-10 from Luke's direction: "different pages for each project,
display more information, link to the file system remove the old skill flow at the top, make a light/dark mode
that changes with the system setting, generally make the layout better and have me do a lot more inside the
application"; not reviewed by Luke).

HTML only: the data comes from build_dashboard.py and every change goes through server.py. Light and dark follow
the system setting (prefers-color-scheme), in the app window and in a browser. Standard library only. Every
value from a file is escaped; Luke's words are only ever form input or escaped text.
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import build_dashboard as bd

CSS = """
:root{color-scheme:light dark;
--bg:#f7f6f2;--surface:#ffffff;--panel:#f1efe9;--fg:#1c1c1c;--mute:#5f6368;--line:#e4e1d9;--accent:#1f3a5f;
--accent-fg:#ffffff;--link:#1f3a5f;--go:#2e6b3f;--shrink:#8a6a12;--nogo:#9b2c2c;--green:#2e7d32;--yellow:#c9a227;
--red:#b3261e;--grey:#9e9e9e;--input:#ffffff;--input-line:#cfccc4;--code:#1f3a5f;--shadow:0 1px 2px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root{
--bg:#14161a;--surface:#1b1e23;--panel:#22262c;--fg:#e7e5e0;--mute:#9aa0a6;--line:#2e333b;--accent:#8fb3e0;
--accent-fg:#0e1420;--link:#a9c6ec;--go:#7fc28f;--shrink:#dcb95c;--nogo:#ec8b85;--green:#5cb85f;--yellow:#e0b83c;
--red:#e5534b;--grey:#7d8590;--input:#16191d;--input-line:#3a404a;--code:#a9c6ec;--shadow:none}}
*{box-sizing:border-box}
html,body{margin:0;background:var(--bg);color:var(--fg)}
body{font:16px/1.55 Georgia,"Times New Roman",serif}
.ui,button,.btn,.tag,.nav,.kv,.meta,.help,.crumb,input,select,textarea,.toast,.pill{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:var(--link)}
.nav{position:sticky;top:0;z-index:5;background:var(--surface);border-bottom:1px solid var(--line);box-shadow:var(--shadow)}
.nav .in{max-width:1180px;margin:0 auto;padding:10px 20px;display:flex;align-items:center;gap:22px}
.brand{font:20px Georgia,serif;color:var(--accent);text-decoration:none;margin-right:8px}
.nav a.item{color:var(--mute);text-decoration:none;font-size:14px;padding:4px 0;border-bottom:2px solid transparent}
.nav a.item.on,.nav a.item:hover{color:var(--fg);border-bottom-color:var(--accent)}
.nav .sp{flex:1}
main{max-width:1180px;margin:0 auto;padding:24px 20px 56px}
h1{font-size:30px;font-weight:normal;margin:0;color:var(--fg)}
h2{font:600 12px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;text-transform:uppercase;letter-spacing:1.1px;
   color:var(--mute);margin:0 0 10px}
h3{font-size:18px;font-weight:normal;margin:0}
.crumb{font-size:13px;color:var(--mute);margin:0 0 6px}.crumb a{color:var(--mute);text-decoration:none}
.crumb a:hover{color:var(--fg)}
.sub{color:var(--mute);margin:4px 0 0;font-style:italic}
.head{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;margin:0 0 6px}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 22px}
.box{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:16px 18px;margin:0 0 18px;box-shadow:var(--shadow)}
.box.tint{background:var(--panel)}
.cols{display:grid;grid-template-columns:minmax(0,1fr) 330px;gap:22px;align-items:start}
@media (max-width:900px){.cols{grid-template-columns:1fr}}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.pcard{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;display:flex;
       flex-direction:column;gap:8px;box-shadow:var(--shadow);border-top:3px solid var(--grey)}
.pcard.st-green{border-top-color:var(--green)}.pcard.st-yellow{border-top-color:var(--yellow)}
.pcard.st-red{border-top-color:var(--red)}.pcard.st-closed{opacity:.75}
.pcard .pname{font-size:19px;color:var(--fg);text-decoration:none}.pcard .pname:hover{text-decoration:underline}
.pcard .pnext{margin:0;font-size:15px}
.pcard .pfoot{display:flex;justify-content:space-between;gap:8px;font:12px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--mute);margin-top:auto}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.tags{display:flex;flex-wrap:wrap;gap:6px}
.tag{font-size:12px;color:var(--mute);border:1px solid var(--line);border-radius:4px;padding:0 6px;white-space:nowrap}
.v-go,.v-GO{color:var(--go);border-color:var(--go)}.v-shrink,.v-SHRINK{color:var(--shrink);border-color:var(--shrink)}
.v-no-go,.v-NO-GO{color:var(--nogo);border-color:var(--nogo)}
.dot{display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--grey);flex:none}
.s-green{background:var(--green)}.s-yellow{background:var(--yellow)}.s-red{background:var(--red)}.s-closed{background:var(--grey)}
.summary{display:flex;flex-wrap:wrap;gap:18px;font:14px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;margin:0 0 16px;align-items:center}
.summary span{display:inline-flex;align-items:center;gap:6px}
.btn,button{font-size:14px;padding:6px 13px;border:1px solid var(--accent);background:var(--accent);color:var(--accent-fg);
            border-radius:6px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;gap:6px;line-height:1.3}
.btn.ghost,button.ghost{background:transparent;color:var(--link);border-color:var(--line)}
.btn.ghost:hover,button.ghost:hover{border-color:var(--accent)}
.btn.small,button.small{font-size:12.5px;padding:2px 9px}
code,pre{font:13px Menlo,Consolas,monospace;color:var(--code)}
code{word-break:break-all}
pre{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:10px 12px;overflow:auto;white-space:pre-wrap}
.next{background:var(--panel);border-left:3px solid var(--accent);border-radius:0 6px 6px 0;padding:10px 14px}
.next .what{font-size:16px;margin-bottom:6px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13.5px;margin:0}
.kv dt{color:var(--mute)}.kv dd{margin:0;word-break:break-word}
.list{list-style:none;margin:0;padding:0}
.list li{display:flex;gap:10px;align-items:baseline;padding:7px 0;border-top:1px solid var(--line)}
.list li:first-child{border-top:0}
.list .grow{flex:1;min-width:0}
.steps li label{display:flex;gap:10px;align-items:baseline;cursor:pointer;flex:1}
.steps li.done span{color:var(--mute);text-decoration:line-through}
.notes .when{font:12px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--mute)}
.notes p{margin:2px 0 0;white-space:pre-wrap}
.meta,.help{color:var(--mute);font-size:13px}
.help{margin:6px 0 0}
label.f{display:block;font:14px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;margin:12px 0 4px}
input[type=text],input[type=number],input[type=search],select,textarea{width:100%;font:15px Georgia,serif;padding:8px 9px;
    border:1px solid var(--input-line);background:var(--input);color:var(--fg);border-radius:6px}
textarea{min-height:90px;resize:vertical;line-height:1.5}
textarea.big{min-height:260px}
input[type=search]{max-width:320px;font:14px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.choices{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px}
.choice{display:flex;gap:9px;align-items:flex-start;border:1px solid var(--line);background:var(--surface);border-radius:8px;padding:10px 12px;cursor:pointer;margin:0}
.choice input{margin-top:5px}.choice small{display:block;color:var(--mute);font-size:13px;margin-top:2px}
.choice:has(input:checked){border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.msg{border-left:3px solid var(--accent);background:var(--panel);padding:9px 13px;margin:0 0 18px;border-radius:0 6px 6px 0}
.group{margin:0 0 26px}.group>h2{display:flex;gap:8px;align-items:baseline}
.group>h2 .cnt{color:var(--mute);font-weight:normal;letter-spacing:0;text-transform:none}
details.shelf>summary{cursor:pointer;font:600 12px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;text-transform:uppercase;
   letter-spacing:1.1px;color:var(--mute);margin:0 0 10px}
.toast{position:fixed;right:18px;bottom:18px;background:var(--fg);color:var(--bg);padding:8px 14px;border-radius:6px;
       font-size:14px;opacity:0;transition:opacity .2s;pointer-events:none}
.toast.on{opacity:.95}
.doc{line-height:1.6}.doc h1{font-size:26px;margin:0 0 12px}.doc h2{font:600 19px Georgia,serif;text-transform:none;letter-spacing:0;color:var(--fg);margin:24px 0 8px}
.doc h3{font-size:17px;margin:18px 0 6px}.doc table{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0;display:block;overflow:auto}
.doc th,.doc td{border:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}.doc th{background:var(--panel)}
.doc blockquote{margin:8px 0;padding:4px 14px;border-left:3px solid var(--line);color:var(--mute)}
.doc hr{border:0;border-top:1px solid var(--line);margin:20px 0}
.stops{display:flex;flex-wrap:wrap;gap:6px 18px;list-style:none;padding:0;margin:12px 0 20px;font:14px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--mute)}
.stops .on{color:var(--fg);font-weight:600}.stops .ok{color:var(--go)}
.vbox{border-left:4px solid var(--accent)}.vbox.v-GO{border-left-color:var(--go)}.vbox.v-SHRINK{border-left-color:var(--shrink)}
.vbox.v-NO-GO{border-left-color:var(--nogo)}
.cite{font:12px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;color:var(--mute)}
.q{margin:0 0 14px}.q label{font-size:16px;display:block;margin-bottom:4px}.q textarea{min-height:64px}
.prop{display:flex;gap:8px;align-items:flex-start;margin:6px 0}.prop input{margin-top:5px}
.wait{font-size:18px;color:var(--accent)}
.empty{color:var(--mute);font-style:italic}
footer{margin-top:36px;border-top:1px solid var(--line);padding-top:10px}
.filters{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:0 0 14px;padding:10px 12px;background:var(--surface);
         border:1px solid var(--line);border-radius:8px}
.filters input[type=search]{flex:1 1 220px;max-width:none}
.chips{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.chip{background:transparent;color:var(--mute);border:0;border-right:1px solid var(--line);border-radius:0;padding:4px 10px;font-size:13px}
.chip:last-child{border-right:0}.chip.on{background:var(--accent);color:var(--accent-fg)}
.filters select{width:auto;font:13px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;padding:3px 6px}
.group>h2{align-items:center}.gtools{display:inline-flex;gap:6px;align-items:center;text-transform:none;letter-spacing:0;font-weight:normal}
.gtools form{display:inline}
details.inline{display:inline-block;position:relative}details.inline>summary{list-style:none}
details.inline>summary::-webkit-details-marker{display:none}
details.inline[open]>form{position:absolute;right:0;top:110%;z-index:4;background:var(--surface);border:1px solid var(--line);
   border-radius:8px;padding:8px;box-shadow:0 4px 14px rgba(0,0,0,.15);width:260px;flex-wrap:nowrap}
section.group[data-drop]{border-radius:10px;transition:background .12s,outline-color .12s;outline:2px dashed transparent;outline-offset:6px}
section.group.over{outline-color:var(--accent);background:var(--panel)}
.pcard[draggable=true]{cursor:grab}.pcard.dragging{opacity:.4}
.dropnote{margin:0;padding:14px;border:1px dashed var(--line);border-radius:8px;text-align:center}
.hidden{display:none!important}
"""

JS = """<script>
(function () {
  var token = document.querySelector('meta[name=gpp-token]').content;
  function toast(t) {
    var el = document.getElementById('toast'); el.textContent = t; el.classList.add('on');
    clearTimeout(el._t); el._t = setTimeout(function () { el.classList.remove('on'); }, 1800);
  }
  function post(url, data) {
    var body = new URLSearchParams(data); body.set('token', token);
    return fetch(url, {method: 'POST', body: body}).then(function (r) {
      return r.json().catch(function () { return {ok: r.ok}; });
    });
  }
  document.addEventListener('click', function (ev) {
    var c = ev.target.closest('[data-copy]');
    if (c) {
      var text = c.getAttribute('data-copy');
      var mac = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.copy;
      if (mac) { mac.postMessage(text); toast('Copied'); }  // the desktop app (dashboard/app)
      else navigator.clipboard.writeText(text).then(function () { toast('Copied'); });
      return;
    }
    var o = ev.target.closest('[data-open]');
    if (o) {
      ev.preventDefault();
      post('/open', {path: o.getAttribute('data-open'), how: o.getAttribute('data-how') || 'open'})
        .then(function (r) { toast(r.ok ? (r.said || 'Opened') : (r.error || 'Not opened')); });
    }
  });
  document.addEventListener('change', function (ev) {
    var g = ev.target.closest('select[data-group-for]');
    if (g) {
      post('/group/move', {path: g.getAttribute('data-group-for'), group: g.value}).then(function (r) {
        toast(r.ok ? (g.value ? 'Filed in ' + g.value : 'Out of its folder') : (r.error || 'Not moved'));
      });
      return;
    }
    var s = ev.target.closest('input[data-step]');
    if (!s) return;
    post('/project/step', {plan: s.getAttribute('data-plan'), line: s.getAttribute('data-step'), done: s.checked ? '1' : ''})
      .then(function (r) {
        if (!r.ok) { s.checked = !s.checked; toast(r.error || 'Not saved'); return; }
        s.closest('li').classList.toggle('done', s.checked); toast(s.checked ? 'Done' : 'Not done');
      });
  });
  // Filters and sort on the home page, remembered in this browser only (D-053).
  var f = document.getElementById('filter');
  if (f) {
    var st = {q: '', state: '', kind: '', verdict: '', sort: 'state'};
    try { Object.assign(st, JSON.parse(localStorage.getItem('gpp-filters') || '{}')); } catch (x) {}
    var sortSel = document.getElementById('sort');
    function apply() {
      f.value = st.q; sortSel.value = st.sort;
      document.querySelectorAll('.chips').forEach(function (c) {
        var key = c.getAttribute('data-filter');
        c.querySelectorAll('.chip').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-value') === st[key]); });
      });
      var q = st.q.trim().toLowerCase(), shown = 0, total = 0;
      document.querySelectorAll('.pcard').forEach(function (el) {
        var ok = (!q || el.getAttribute('data-text').indexOf(q) >= 0) &&
          (!st.state || el.getAttribute('data-state') === st.state) &&
          (!st.kind || el.getAttribute('data-kind') === st.kind) &&
          (!st.verdict || el.getAttribute('data-verdict') === st.verdict);
        el.classList.toggle('hidden', !ok); total++; if (ok) shown++;
      });
      document.querySelectorAll('.grid').forEach(function (g) {
        var cards = Array.prototype.slice.call(g.children);
        cards.sort(function (a, b) {
          if (st.sort === 'name') return a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
          if (st.sort === 'active') return (b.getAttribute('data-active') || '').localeCompare(a.getAttribute('data-active') || '');
          return (a.getAttribute('data-order') - b.getAttribute('data-order')) || a.getAttribute('data-name').localeCompare(b.getAttribute('data-name'));
        }).forEach(function (c) { g.appendChild(c); });
      });
      var filtering = q || st.state || st.kind || st.verdict;
      document.querySelectorAll('section.group, details.shelf').forEach(function (sec) {
        var any = sec.querySelector('.pcard:not(.hidden)');
        sec.classList.toggle('hidden', !!filtering && !any);  // empty folders stay visible as drop targets otherwise
      });
      document.getElementById('shown').textContent = filtering ? shown + ' of ' + total + ' shown' : '';
      try { localStorage.setItem('gpp-filters', JSON.stringify(st)); } catch (x) {}
    }
    f.addEventListener('input', function () { st.q = f.value; apply(); });
    sortSel.addEventListener('change', function () { st.sort = sortSel.value; apply(); });
    document.querySelectorAll('.chips').forEach(function (c) {
      c.addEventListener('click', function (ev) {
        var b = ev.target.closest('.chip'); if (!b) return;
        st[c.getAttribute('data-filter')] = b.getAttribute('data-value'); apply();
      });
    });
    document.getElementById('clear').addEventListener('click', function () {
      st = {q: '', state: '', kind: '', verdict: '', sort: st.sort}; apply();
    });
    apply();
  }
  // Drag a card onto a folder (D-053). Only the dashboard's grouping changes; nothing moves on disk.
  var dragged = null;
  document.addEventListener('dragstart', function (ev) {
    var c = ev.target.closest && ev.target.closest('.pcard[draggable=true]'); if (!c) return;
    dragged = c; c.classList.add('dragging');
    ev.dataTransfer.effectAllowed = 'move'; ev.dataTransfer.setData('text/plain', c.getAttribute('data-path'));
  });
  document.addEventListener('dragend', function () {
    if (dragged) dragged.classList.remove('dragging'); dragged = null;
    document.querySelectorAll('section.over').forEach(function (s) { s.classList.remove('over'); });
  });
  function zone(ev) {
    var s = ev.target.closest && ev.target.closest('section[data-drop]');
    if (!s || !dragged) return null;
    var root = s.getAttribute('data-droproot');
    if (root && root !== dragged.getAttribute('data-root')) return null;  // another root would mean moving the folder on disk
    return s;
  }
  document.addEventListener('dragover', function (ev) {
    var s = zone(ev);
    document.querySelectorAll('section.over').forEach(function (o) { if (o !== s) o.classList.remove('over'); });
    if (!s) return;
    ev.preventDefault(); ev.dataTransfer.dropEffect = 'move'; s.classList.add('over');
  });
  document.addEventListener('drop', function (ev) {
    var s = zone(ev); if (!s) return;
    ev.preventDefault(); s.classList.remove('over');
    var card = dragged, group = s.getAttribute('data-drop');
    post('/group/move', {path: card.getAttribute('data-path'), group: group}).then(function (r) {
      if (!r.ok) { toast(r.error || 'Not moved'); return; }
      s.querySelector('.grid').appendChild(card);
      var note = s.querySelector('.dropnote'); if (note) note.remove();
      toast(group ? 'Filed in ' + group : 'Back under its root folder');
      setTimeout(function () { location.reload(); }, 400);
    });
  });
  var meta = document.querySelector('meta[name=gpp-stamp]');
  if (meta) {
    var url = meta.getAttribute('data-url'), stamp = meta.content;
    var busy = function () {
      var a = document.activeElement;
      if (a && /INPUT|TEXTAREA|SELECT/.test(a.tagName) && a.type !== 'checkbox') return true;
      return Array.prototype.some.call(document.querySelectorAll('textarea, input[type=text]'),
        function (el) { return el.value.trim() !== ''; });
    };
    setInterval(function () {
      fetch(url, {cache: 'no-store'}).then(function (r) { return r.text(); }).then(function (s) {
        if (s && s !== stamp) { if (busy()) { stamp = s; } else { location.reload(); } }
      }).catch(function () {});
    }, Number(meta.getAttribute('data-ms') || 4000));
  }
})();
</script>"""


def e(x) -> str:
    return html.escape(str(x))


def q(x) -> str:
    return quote(str(x), safe="")


def short(path: Path | str) -> str:
    """A path with the home folder shown as ~."""
    s, home = str(path), str(Path.home())
    return "~" + s[len(home):] if s.startswith(home) else s


NAV = [("projects", "/", "Projects"), ("new", "/new", "New project"), ("library", "/library", "Library")]


def shell(title: str, body: str, token: str = "", active: str = "", stamp: tuple[str, str, int] | None = None) -> str:
    """The frame of every page. stamp = (url, value, ms): reload when url's value changes (unless Luke is typing)."""
    live = bool(token)
    nav = "".join(f'<a class="item{" on" if k == active else ""}" href="{u}">{t}</a>' for k, u, t in NAV) if live else ""
    metas = f'<meta name="gpp-token" content="{e(token)}">' if live else ""
    if live and stamp:
        metas += f'<meta name="gpp-stamp" content="{e(stamp[1])}" data-url="{e(stamp[0])}" data-ms="{stamp[2]}">'
    right = '<span class="meta">Live</span>' if live else f'<span class="meta">Snapshot {datetime.now():%Y-%m-%d %H:%M}</span>'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark">
<title>Games-People-Play</title>{metas}<style>{CSS}</style></head>
<body><nav class="nav"><div class="in"><a class="brand" href="/">Games-People-Play</a>{nav}<span class="sp"></span>{right}</div></nav>
<main>{body}</main><div class="toast" id="toast"></div>{JS if live else ""}</body></html>
"""


def message_box(message: str) -> str:
    return f'<p class="msg">{e(message)}</p>' if message else ""


def hidden(token: str, **fields) -> str:
    out = f'<input type="hidden" name="token" value="{e(token)}">'
    return out + "".join(f'<input type="hidden" name="{e(k)}" value="{e(v)}">' for k, v in fields.items())


def open_btn(path, label: str, how: str = "open", cls: str = "ghost small") -> str:
    return f'<button type="button" class="{cls}" data-open="{e(str(path))}" data-how="{how}">{e(label)}</button>'


def verdict_tag(v: str) -> str:
    return f'<span class="tag v-{e(v)}">{e(v)}</span>' if v else '<span class="tag">not gated</span>'


# ------------------------------------------------------------------------------------------------ home

STATE_LABEL = {"red": "blocked or stalled", "yellow": "needs a step", "green": "on track", "closed": "closed"}
ORDER = {"red": 0, "yellow": 1, "green": 2, "closed": 3}


def card(p: bd.Project, token: str) -> str:
    st, why = bd.state(p)
    step, _ = bd.recommend(p)
    link = f"/project?p={q(p.path)}" if token else p.path.as_uri()
    folder = open_btn(p.path, "Folder") if token else ""
    kind = bd.KIND_LABEL.get(p.kind, p.kind)
    text = " ".join([p.name, step, kind, bd.tier_label(p), p.verdict or "not gated", why, p.group]).lower()
    drag = (f' draggable="true" data-path="{e(str(p.path))}" data-root="{e(p.root)}"' if token and not p.archived and not p.closed else "")
    return (f'<article class="pcard st-{st}" data-name="{e(p.name.lower())}" data-text="{e(text)}" data-state="{st}"'
            f' data-kind="{e(p.kind)}" data-verdict="{e(p.verdict or "none")}" data-active="{e(p.active or "")}"'
            f' data-order="{ORDER[st]}"{drag}>'
            f'<div class="row"><span class="dot s-{st}" title="{e(why)}"></span>'
            f'<a class="pname" href="{e(link)}" draggable="false">{e(p.name)}</a><span style="flex:1"></span>{folder}</div>'
            f'<div class="tags"><span class="tag">{e(kind)}</span>'
            f'<span class="tag">{e(bd.tier_label(p))}</span>{verdict_tag(p.verdict)}</div>'
            f'<p class="pnext">{e(step)}</p>'
            f'<div class="pfoot"><span>{e(why)}</span><span>{e(p.active or "")}</span></div></article>')


def section(title: str, ps: list, token: str, drop: str = "", root: str = "", tools: str = "", hint: str = "") -> str:
    """A group of cards. drop: the dashboard folder a dropped card joins ("" = back under its root)."""
    zone = (f' data-drop="{e(drop)}" data-droproot="{e(root)}"' if token else "")
    cards = "".join(card(p, token) for p in sorted(ps, key=lambda p: (ORDER[bd.state(p)[0]], p.name.lower())))
    empty = f'<p class="help dropnote">{e(hint)}</p>' if hint and not ps else ""
    return (f'<section class="group"{zone}><h2>{e(title)}<span class="cnt">{len(ps)}</span>{tools}</h2>'
            f'<div class="grid">{cards}</div>{empty}</section>')


def group_tools(token: str, name: str, first: bool, last: bool) -> str:
    h = hidden(token, name=name)
    up = "" if first else f'<form method="post" action="/group/order">{h}<input type="hidden" name="step" value="-1"><button class="ghost small" title="Move up">↑</button></form>'
    down = "" if last else f'<form method="post" action="/group/order">{h}<input type="hidden" name="step" value="1"><button class="ghost small" title="Move down">↓</button></form>'
    return (f'<span style="flex:1"></span><span class="gtools">{up}{down}'
            f'<details class="inline"><summary class="btn ghost small">Rename</summary><form method="post" action="/group/rename" class="row">'
            f'{hidden(token, old=name)}<input type="text" name="new" value="{e(name)}" maxlength="40" required><button class="small">Save</button></form></details>'
            f'<form method="post" action="/group/delete">{h}<button class="ghost small" title="Its projects go back under their root folder">Remove folder</button></form></span>')


def filters_bar(projs: list) -> str:
    def chips(name: str, opts: list[tuple[str, str]]) -> str:
        return (f'<span class="chips" data-filter="{name}">'
                + "".join(f'<button type="button" class="chip{" on" if v == "" else ""}" data-value="{e(v)}">{e(t)}</button>'
                          for v, t in opts) + "</span>")
    states = [("", "Any state")] + [(k, STATE_LABEL[k]) for k in ("red", "yellow", "green")]
    kinds = [("", "Any kind"), ("code", "Technical"), ("household", "Hands-on")]
    verdicts = [("", "Any verdict"), ("GO", "GO"), ("SHRINK", "SHRINK"), ("NO-GO", "NO-GO"), ("none", "not gated")]
    return (f'<div class="filters"><input type="search" id="filter" placeholder="Search names, next steps, tags">'
            f'{chips("state", states)}{chips("kind", kinds)}{chips("verdict", verdicts)}'
            f'<label class="meta">Sort <select id="sort"><option value="state">by state</option><option value="name">by name</option>'
            f'<option value="active">by last activity</option></select></label>'
            f'<span class="meta" id="shown"></span><button type="button" class="ghost small" id="clear">Clear</button></div>')


def home(projs: list, roots: list[Path], token: str = "", message: str = "", skills_ok: bool | None = None,
         groups: list[str] | None = None) -> str:
    groups = groups if groups is not None else bd.load_groups()["groups"]
    active = [p for p in projs if not p.archived and not p.closed]
    completed = [p for p in projs if p.closed and not p.archived]
    archived = [p for p in projs if p.archived]
    counts = {k: 0 for k in ORDER}
    for p in active:
        counts[bd.state(p)[0]] += 1
    counts["closed"] = len(completed)
    summary = '<div class="summary">' + "".join(
        f'<span><span class="dot s-{k}"></span>{counts[k]} {STATE_LABEL[k]}</span>' for k in ORDER if counts[k]) + "</div>"
    body = (f'<div class="head"><h1>Projects</h1><span class="meta">{len(active)} active</span>'
            + ('<span style="flex:1"></span>'
               f'<details class="inline"><summary class="btn ghost">New folder</summary><form method="post" action="/group/add" class="row">'
               f'{hidden(token)}<input type="text" name="name" maxlength="40" required placeholder="Folder name"><button class="small">Add</button></form></details>'
               '<a class="btn" href="/new">New project</a>' if token else "") + "</div>")
    body += message_box(message) + summary + (filters_bar(projs) if token else "")
    if not token:
        body += ('<p class="help">A read-only snapshot. Open the Games-People-Play app (or run'
                 ' <code>dashboard/open_dashboard.command</code>) to start projects, answer questions and add notes.</p>')
    elif groups:
        body += '<p class="help">Drag a card onto a folder to file it there; drag it back to its root folder to unfile it. Nothing moves on disk.</p>'
    else:
        body += '<p class="help">Make a folder (New folder), then drag cards into it. Folders only group cards here; nothing moves on disk.</p>'
    for i, g in enumerate(groups):
        ps = [p for p in active if p.group == g]
        body += section(g, ps, token, drop=g, tools=group_tools(token, g, i == 0, i == len(groups) - 1) if token else "",
                        hint="Empty. Drag a project here.")
    by_root: dict[str, list] = {str(r): [] for r in roots}
    for p in active:
        if not p.group:
            by_root.setdefault(p.root or str(p.path.parent), []).append(p)
    for root, ps in by_root.items():
        if ps or groups:
            body += section(short(root), ps, token, drop="", root=root, hint="Drag a card here to take it out of its folder.")
    if not active:
        body += '<p class="empty">No active projects.</p>'
    for title, ps, empty in (("Completed", completed, "A project lands here when its closeout is filed (/closeout)."),
                             ("Archived", archived, "Parked projects. Archive one from its page.")):
        inner = (f'<div class="grid">{"".join(card(p, token) for p in sorted(ps, key=lambda p: p.name.lower()))}</div>'
                 if ps else f'<p class="help">{empty}</p>')
        body += f'<details class="shelf group"><summary>{title} ({len(ps)})</summary>{inner}</details>'
    if token and skills_ok is False:
        body += ('<p class="help">Some accepted skills aren\'t installed for every Claude Code chat yet:'
                 ' <a href="/library">Library</a>.</p>')
    body += (f'<footer class="meta">{e(", ".join(short(r) for r in roots))} · {e(bd.skill_summary())} · read from local'
             f' files only. Green: on track. Yellow: needs a step. Red: the warden said no, or no activity for'
             f' {bd.DEAD_DAYS}+ days.</footer>')
    return shell("Projects", body, token, "projects", ("/stamp", bd.signature(projs), 4000))


# ------------------------------------------------------------------------------------------------ project

def group_select(p: bd.Project) -> str:
    groups = bd.load_groups()["groups"]
    if not groups:
        return ""
    opts = f'<option value="">{e(short(p.root or p.path.parent))} (no folder)</option>' + "".join(
        f'<option value="{e(g)}"{" selected" if g == p.group else ""}>{e(g)}</option>' for g in groups)
    return f'<label class="meta row" style="gap:6px">Folder <select data-group-for="{e(str(p.path))}" style="width:auto">{opts}</select></label>'


def next_panel(p: bd.Project, token: str) -> str:
    step, prompt = bd.recommend(p)
    buttons = f'<button type="button" class="ghost small" data-copy="{e(prompt)}">Copy prompt</button>'
    if p.run and p.run_phase not in ("done", "stopped"):
        buttons = f'<a class="btn small" href="/run?r={q(p.run)}">Continue the run</a>' + buttons
    elif prompt.startswith("/start"):
        buttons = f'<a class="btn small" href="/new?existing={q(p.path)}">Start it here</a>' + buttons
    return (f'<div class="next"><div class="what">{e(step)}</div><div class="row"><code>{e(prompt)}</code></div>'
            f'<div class="row" style="margin-top:8px">{buttons}</div></div>')


def project_page(p: bd.Project, d: bd.Detail, token: str, message: str = "", stamp: str = "") -> str:
    st, why = bd.state(p)
    editor = Path("/Applications/Visual Studio Code.app").exists()
    bar = (open_btn(p.path, "Open folder", cls="btn small") + open_btn(p.path, "Terminal here", "terminal")
           + (open_btn(p.path, "Open in VS Code", "editor") if editor else "")
           + (open_btn(d.plan_file, "Open plan", "open") if d.plan_file else "")
           + f'<a class="btn ghost small" href="/new?existing={q(p.path)}">New /start run</a>'
           + group_select(p)
           + f'<form method="post" action="/archive" style="display:inline">{hidden(token, project=p.path, back=f"/project?p={q(p.path)}")}'
           f'<button class="ghost small">{"Unarchive" if p.archived else "Archive"}</button></form>')
    head = (f'<p class="crumb"><a href="/">Projects</a> / {e(Path(p.root).name if p.root else p.path.parent.name)}</p>'
            f'<div class="head"><span class="dot s-{st}" title="{e(why)}"></span><h1>{e(p.name)}</h1>'
            f'<span class="tag">{e(bd.KIND_LABEL.get(p.kind, p.kind))}</span><span class="tag">{e(bd.tier_label(p))}</span>'
            f'{verdict_tag(p.verdict)}<span class="meta">{e(why)}</span></div>'
            f'<p class="meta">{e(short(p.path))}</p><div class="bar">{bar}</div>')
    main = f'<div class="box">{next_panel(p, token)}</div>'
    if d.goal or d.done_when:
        main += (f'<div class="box"><h2>Goal</h2><p style="margin:0 0 8px">{inline(d.goal or "not recorded", p.path)}</p>'
                 f'<h2>Done when</h2><p style="margin:0">{inline(d.done_when or "not recorded", p.path)}</p>'
                 + (f'<p class="help">Time: {e(d.budget)}</p>' if d.budget else "") + "</div>")
    if d.plan_file:
        done = sum(1 for _, x, _ in d.steps if x)
        items = "".join(
            f'<li class="{"done" if x else ""}"><label><input type="checkbox" data-step="{i}" data-plan="{e(d.plan_file)}"'
            f'{" checked" if x else ""}><span>{e(t)}</span></label></li>' for i, x, t in d.steps)
        main += (f'<div class="box"><div class="row"><h2 style="margin:0">Plan</h2><span class="meta">{done} of {len(d.steps)}'
                 f' done</span><span style="flex:1"></span>{open_btn(d.plan_file, "Edit file", "editor" if editor else "open")}</div>'
                 f'<ul class="list steps" style="margin-top:8px">{items or "<li class=empty>No checklist steps yet.</li>"}</ul>'
                 f'<form method="post" action="/project/addstep" class="row" style="margin-top:10px">'
                 f'{hidden(token, plan=d.plan_file, project=p.path)}<input type="text" name="text" placeholder="Add a step"'
                 f' maxlength="300" style="flex:1"><button class="ghost small">Add</button></form>'
                 f'<p class="help">{e(short(d.plan_file))}</p></div>')
    if p.verdict:
        reasons = "".join(f"<li>{inline(r, p.path)}</li>" for r in d.reasons)
        main += (f'<div class="box vbox v-{e(p.verdict)}"><h2>Warden: {e(p.verdict)}</h2>'
                 + (f"<ul style='margin:0;padding-left:20px'>{reasons}</ul>" if reasons else "") + "</div>")
    if d.docs:
        rows, last = "", ""
        for doc in d.docs:
            if doc.group != last:
                rows += f'<li><h2 style="margin:10px 0 0">{e(doc.group)}</h2></li>'
                last = doc.group
            eb = (f'<span class="tag">{doc.answered}/{doc.prompts} explain-backs</span>' if doc.prompts else "")
            stt = f'<span class="tag">{e(doc.status)}</span>' if doc.status else ""
            rows += (f'<li><span class="grow"><a href="/doc?p={q(doc.path)}">{e(doc.title)}</a>'
                     f' <span class="meta">{e(doc.path.name)}</span></span>{stt}{eb}{open_btn(doc.path, "Open")}</li>')
        main += f'<div class="box"><h2>Documents</h2><ul class="list">{rows}</ul></div>'
    if d.decisions:
        items = "".join(f'<li><span class="tag">#{e(i)}</span><span class="grow">{inline(t, p.path)}</span></li>' for i, t in d.decisions)
        main += f'<div class="box"><h2>Open decisions</h2><ul class="list">{items}</ul></div>'
    if d.records:
        items = ""
        for r in d.records:
            run = (f'<a class="btn ghost small" href="/run?r={q(r["path"])}">{e(r["run"])}</a>' if r["run"] else "")
            items += (f'<li><span class="grow">{e(r["name"])} {("<span class=tag>/start " + e(r["tier"]) + "</span>") if r["tier"] else ""}'
                      f'</span>{verdict_tag(r["verdict"]) if r["verdict"] else ""}{run}{open_btn(r["path"], "Folder")}</li>')
        main += f'<div class="box"><h2>Elicitation records</h2><ul class="list">{items}</ul></div>'
    facts = [("Kind", bd.KIND_LABEL.get(p.kind, p.kind)), ("Tier", bd.tier_label(p))]
    if p.docs:
        facts += [("Documents", f"{p.docs}, {p.accepted_docs} accepted"), ("Explain-backs", f"{p.answered} of {p.explain_backs} answered")]
    if p.reqs:
        facts.append(("Requirements", ", ".join(f"{n} {s.lower()}" for s, n in sorted(
            p.reqs.items(), key=lambda kv: bd.REQ_STATUSES.index(kv[0])))))
    if p.record:
        facts.append(("Latest record", f"{p.record}: {p.items} items, {p.stated} in your words"))
    if p.time:
        facts.append(("Suggested hours", p.time))
    facts.append(("Last activity", p.active or "unknown"))
    side = '<div class="box"><h2>Facts</h2><dl class="kv">' + "".join(
        f"<dt>{e(k)}</dt><dd>{e(v)}</dd>" for k, v in facts) + "</dl></div>"
    if d.git:
        commits = "".join(f'<li><span class="meta">{e(c[0])}</span><span class="grow">{e(c[1])}</span></li>'
                          for c in d.git.get("commits", []))
        hook = {"library": "privacy hook", "own": "the project's own", "none": "none"}.get(p.hook, p.hook)
        side += (f'<div class="box"><h2>Git</h2><dl class="kv"><dt>Branch</dt><dd>{e(d.git.get("branch", ""))}</dd>'
                 f'<dt>Uncommitted</dt><dd>{d.git.get("dirty", 0)} files</dd><dt>Pre-push hook</dt><dd>{e(hook)}</dd>'
                 + (f'<dt>Remote</dt><dd>{e(d.git["remote"])}</dd>' if d.git.get("remote") else "")
                 + f'</dl><ul class="list" style="margin-top:8px;font-size:14px">{commits}</ul></div>')
    notes = "".join(f'<li><div class="grow"><div class="when">{e(w)}</div><p>{e(t)}</p></div></li>' for w, t in d.notes[:30])
    side += (f'<div class="box"><h2>Notes</h2><form method="post" action="/note">'
             f'{hidden(token, project=p.path, back=f"/project?p={q(p.path)}")}'
             f'<textarea name="text" required maxlength="4000" placeholder="Add a note" style="min-height:70px"></textarea>'
             f'<div class="row" style="margin-top:6px"><button class="small">Add note</button>'
             f'{open_btn(p.path / "notes.md", "Open notes.md") if (p.path / "notes.md").exists() else ""}</div></form>'
             f'<ul class="list notes" style="margin-top:10px">{notes or "<li class=empty>No notes yet.</li>"}</ul></div>')
    body = head + message_box(message) + f'<div class="cols"><div>{main}</div><aside>{side}</aside></div>'
    return shell(p.name, body, token, "projects", (f"/stamp?p={q(p.path)}", stamp, 4000))


# ------------------------------------------------------------------------------------------------ new project

def new_page(roots: list[Path], token: str, selected: str = "", message: str = "") -> str:
    eng = bd.engine()
    opts = "".join(f'<option value="{e(str(r))}">{e(short(r))}</option>' for r in roots)
    existing = '<option value="">A new folder (name it below)</option>' + "".join(
        f'<option value="{e(str(f))}"{" selected" if str(f) == selected else ""}>{e(f.parent.name)} / {e(f.name)}</option>'
        for f in bd.folders(roots))
    tiers = "".join(
        f'<label class="choice"><input type="radio" name="tier" value="{t}"{" checked" if t == "small" else ""}>'
        f'<span>{e(bd.TIER_LABEL[t])}<small>{e(bd.TIER_HINT[t])}</small></span></label>' for t in ("small", "medium", "large"))
    kinds = "".join(
        f'<label class="choice"><input type="radio" name="kind" value="{k}"{" checked" if k == "code" else ""}>'
        f'<span>{e(bd.KIND_LABEL[k])}<small>{e(bd.KIND_HINT[k])}</small></span></label>' for k in ("code", "household"))
    rounds = ", ".join(f"{bd.TIER_LABEL[t].lower()} {c['rounds']}×{c['questions']}" for t, c in eng.TIERS.items() if "rounds" in c)
    body = (f'<p class="crumb"><a href="/">Projects</a></p><div class="head"><h1>New project</h1></div>'
            f'<p class="sub">Three stops: your brain dump, a few questions, one approval. Nothing is created before you approve.</p>'
            + message_box(message) +
            f'<form method="post" action="/start" class="box" style="margin-top:18px">{hidden(token)}'
            f'<div class="cols" style="grid-template-columns:1fr 1fr"><div><label class="f" for="existing">Project folder</label>'
            f'<select id="existing" name="existing">{existing}</select></div>'
            f'<div><label class="f" for="name">Name (for a new folder)</label><div class="row" style="flex-wrap:nowrap">'
            f'<input type="text" id="name" name="name" maxlength="60" placeholder="My-Project"><select name="root" style="max-width:200px">{opts}</select></div></div></div>'
            f'<label class="f">Size</label><div class="choices">{tiers}</div>'
            f'<label class="f">Kind</label><div class="choices">{kinds}</div>'
            f'<label class="f" for="dump">Brain dump</label>'
            f'<textarea id="dump" name="dump" class="big" required maxlength="20000" placeholder="Everything about it, in any order:'
            f' what it is, why it matters, what bugs you, what you have tried, who is involved, what worries you, what done looks like."></textarea>'
            f'<p class="help">Saved word for word; sending it is the whole dump. Questions per size: {e(rounds)}.</p>'
            f'<p class="row" style="margin-top:12px"><button>Start</button></p></form>')
    return shell("New project", body, token, "new")


# ------------------------------------------------------------------------------------------------ library

def library_page(skills: list, states: dict, installed: dict, token: str, message: str = "", health: str = "") -> str:
    rows = ""
    for s in skills:
        stv = states.get(s.name, "?")
        label = {"accepted": "accepted", "changed": "changed since acceptance"}.get(stv, s.status.lower() or stv)
        inst_state = installed.get(s.name, "not installable" if stv != "accepted" else "")
        ebs = bd.explain_back_list(bd.read(s.path))
        action = ""
        if stv != "accepted":
            open_eb = [(i, pr) for i, (pr, ans) in enumerate(ebs) if not ans]
            answered = [pr for pr, ans in ebs if ans]
            if open_eb:
                i, pr = open_eb[-1]
                action = (f'<form method="post" action="/explain" style="margin-top:8px">{hidden(token, doc=s.path, n=i, back="/library")}'
                          f'<label class="f">Explain-back: {e(pr)}</label><textarea name="answer" required maxlength="4000"></textarea>'
                          f'<button class="small" style="margin-top:6px">Save my answer</button></form>')
            elif answered:
                action = (f'<form method="post" action="/accept" style="margin-top:8px">{hidden(token, skill=s.name)}'
                          f'<p class="help">You answered its explain-back. Accepting pins this content and lets it install for every chat.</p>'
                          f'<button class="small">Accept /{e(s.name)}</button></form>')
        rows += (f'<li><div class="grow"><div class="row"><a href="/doc?p={q(s.path)}"><b>/{e(s.name)}</b></a>'
                 f'<span class="tag">{e(label)}</span>{("<span class=tag>" + e(inst_state) + "</span>") if inst_state else ""}</div>'
                 f'<p class="meta" style="margin:4px 0 0">{e(s.description[:260])}</p>{action}</div></li>')
    missing = [k for k, v in installed.items() if v != "installed"]
    install = (f'<form method="post" action="/install">{hidden(token)}<button>Install accepted skills for every chat</button></form>'
               f'<p class="help">Pinned copies in ~/.claude/skills. {len(missing)} not installed or out of date.</p>'
               if missing else '<p class="help">Every accepted skill is installed for every Claude Code chat.</p>')
    hc = (f'<form method="post" action="/healthcheck">{hidden(token)}<button class="ghost">Run the healthcheck</button></form>'
          f'<p class="help">Checks the skills, scripts, dashboard and tests. Changes nothing. About 10 seconds.</p>'
          + (f"<pre>{e(health)}</pre>" if health else ""))
    body = (f'<div class="head"><h1>Library</h1></div><p class="sub">The skills behind the gate, their review state,'
            f' and upkeep.</p>' + message_box(message) +
            f'<div class="cols" style="margin-top:18px"><div class="box"><h2>Skills</h2><ul class="list">{rows}</ul></div>'
            f'<aside><div class="box"><h2>Every chat</h2>{install}</div><div class="box"><h2>Healthcheck</h2>{hc}</div>'
            f'<div class="box"><h2>The app</h2><p class="help" style="margin:0">Rebuild it only if this repo moves:</p>'
            f'<pre>python3 dashboard/make_app.py</pre><p class="help">Then keep it in the Dock: right-click its icon,'
            f' Options, Keep in Dock.</p>{open_btn(bd.REPO, "Open the library folder")}</div></aside></div>')
    return shell("Library", body, token, "library")


# ------------------------------------------------------------------------------------------------ documents

def inline(text: str, base: Path) -> str:
    """Escape, then a small set of Markdown: code, bold, italics, links (local .md links open in the viewer)."""
    parts = re.split(r"(`[^`]+`)", text)
    out = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append(f"<code>{e(part[1:-1])}</code>")
            continue
        s = e(part)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"<i>\1</i>", s)

        def link(m):
            label, target = m.group(1), html.unescape(m.group(2))
            if re.match(r"^(https?|mailto):", target):
                return f'<a href="{e(target)}">{label}</a>'
            path = (base / target.split("#")[0].split(":")[0]).resolve()
            return f'<a href="/doc?p={q(path)}">{label}</a>' if path.suffix == ".md" else f'<a href="#" data-open="{e(path)}">{label}</a>'
        s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
        out.append(s)
    return "".join(out)


def markdown(text: str, base: Path) -> str:
    """Enough Markdown for Luke's documents: headings, paragraphs, lists, checkboxes, tables, quotes, code, rules."""
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)  # skill frontmatter
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append(f"<pre>{e(chr(10).join(lines[i + 1:j]))}</pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,6}) (.*)$", ln)
        if m:
            n = min(len(m.group(1)), 3)
            out.append(f"<h{n}>{inline(m.group(2), base)}</h{n}>")
            i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", ln):
            out.append("<hr>")
            i += 1
            continue
        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                if not re.match(r"^\|[\s:|-]+\|?\s*$", lines[i]):
                    rows.append([c.strip() for c in re.split(r"(?<!\\)\|", lines[i].strip().strip("|"))])
                i += 1
            if rows:
                head = "".join(f"<th>{inline(c, base)}</th>" for c in rows[0])
                body = "".join("<tr>" + "".join(f"<td>{inline(c.replace(chr(92) + '|', '|'), base)}</td>" for c in r) + "</tr>"
                               for r in rows[1:])
                out.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
            continue
        if ln.startswith(">"):
            block = []
            while i < len(lines) and lines[i].startswith(">"):
                block.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>" + "<br>".join(inline(b, base) for b in block) + "</blockquote>")
            continue
        if re.match(r"^\s*([-*]|\d+\.) ", ln):
            ordered = bool(re.match(r"^\s*\d+\. ", ln))
            items = []
            while i < len(lines) and (re.match(r"^\s*([-*]|\d+\.) ", lines[i]) or (lines[i].startswith("   ") and items)):
                if re.match(r"^\s*([-*]|\d+\.) ", lines[i]):
                    items.append(re.sub(r"^\s*([-*]|\d+\.) ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1

            def li(t):
                m2 = re.match(r"^\[( |x|X)\] (.*)$", t)
                if m2:
                    return f'<li style="list-style:none;margin-left:-18px">{"☑" if m2.group(1) != " " else "☐"} {inline(m2.group(2), base)}</li>'
                return f"<li>{inline(t, base)}</li>"
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(li(t) for t in items) + f"</{tag}>")
            continue
        if not ln.strip():
            i += 1
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6} |\||>|```|\s*([-*]|\d+\.) )", lines[i]):
            para.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(para), base) + "</p>")
    return "\n".join(out)


def doc_page(doc: Path, project: bd.Project | None, token: str, message: str = "") -> str:
    text = bd.read(doc)
    editor = Path("/Applications/Visual Studio Code.app").exists()
    crumb = '<a href="/">Projects</a>'
    if project:
        crumb += f' / <a href="/project?p={q(project.path)}">{e(project.name)}</a>'
    else:
        crumb += ' / <a href="/library">Library</a>'
    ebs = bd.explain_back_list(text)
    eb = ""
    for i, (prompt, ans) in enumerate(ebs):
        if ans:
            eb += f'<li><div class="grow"><b>{e(prompt)}</b><p class="meta" style="white-space:pre-wrap">{e(ans)}</p></div></li>'
        else:
            back = f"/doc?p={q(doc)}"
            eb += (f'<li><form class="grow" method="post" action="/explain">{hidden(token, doc=doc, n=i, back=back)}'
                   f'<b>{e(prompt)}</b><textarea name="answer" required maxlength="4000" style="margin-top:6px"'
                   f' placeholder="Your answer, in your own words. Saved verbatim."></textarea>'
                   f'<button class="small" style="margin-top:6px">Save my answer</button></form></li>')
    side = (f'<div class="box"><h2>File</h2><p class="meta" style="margin:0 0 8px;word-break:break-all">{e(short(doc))}</p>'
            f'<div class="row">{open_btn(doc, "Open", cls="btn small")}{open_btn(doc, "Show in Finder", "reveal")}'
            f'{open_btn(doc, "Edit in VS Code", "editor") if editor else ""}</div>'
            + (f'<p class="help">Status: {e(bd.doc_status(text))}</p>' if bd.doc_status(text) else "") + "</div>")
    if ebs:
        side += (f'<div class="box"><h2>Explain-backs ({sum(1 for _, a in ebs if a)} of {len(ebs)} answered)</h2>'
                 f'<ul class="list">{eb}</ul></div>')
    body = (f'<p class="crumb">{crumb}</p>{message_box(message)}<div class="cols"><article class="box doc">'
            f'{markdown(text, doc.parent)}</article><aside>{side}</aside></div>')
    return shell(doc.name, body, token, "projects" if project else "library")


# ------------------------------------------------------------------------------------------------ /start runs

RUN_STOPS = [("dump", "1 Brain dump"), ("questions", "2 A few questions"), ("approve", "3 One approval"), ("done", "Set up")]
THINKING = {"ask": "reading your dump and picking the questions that matter",
            "plan": "judging it as the warden and drafting the plan"}


def run_page(st: dict, record: Path, token: str, message: str = "") -> str:
    """One /start run (D-047): the page for whichever stop it is at."""
    eng = bd.engine()
    ph = eng.phase(st)
    cfg = eng.TIERS.get(st["tier"], {})
    hid = hidden(token, r=record)
    at = {"thinking": "questions" if st.get("busy") == "ask" else "approve", "stale": "questions", "error": "questions",
          "asking": "questions", "answering": "questions", "planning": "approve", "approving": "approve",
          "done": "done", "stopped": "done"}.get(ph, "dump")
    if ph in ("stale", "error") and st.get("plan") is None and st["status"] == "planning":
        at = "approve"
    order = [k for k, _ in RUN_STOPS]
    stops = "".join(f'<li class="{"on" if k == at else "ok" if order.index(k) < order.index(at) else ""}">'
                    f'{"✓ " if order.index(k) < order.index(at) else ""}{e(label)}</li>' for k, label in RUN_STOPS)
    if ph == "thinking":
        model = cfg.get("models", {}).get(st.get("busy"), "Claude")
        body = (f'<div class="box tint"><p class="wait">Claude ({e(model)}) is {e(THINKING.get(st.get("busy"), "working"))}…</p>'
                f'<p class="help">Usually 10 to 40 seconds. This page moves on by itself.</p></div>')
    elif ph in ("stale", "error"):
        err = st.get("error") or "The last step stopped part way (the dashboard may have closed)."
        body = (f'<div class="box"><p><b>That step did not finish.</b> {e(err)}</p><div class="row">'
                f'<form method="post" action="/run/retry">{hid}<button>Try again</button></form>'
                f'<form method="post" action="/run/stop">{hid}<button class="ghost">Stop here</button></form></div></div>')
    elif ph == "answering":
        rnd = st["rounds"][-1]
        qs = "".join(f'<div class="q"><label for="{e(x["id"])}">{e(x["text"])}</label>'
                     f'<textarea id="{e(x["id"])}" name="a_{e(x["id"])}" maxlength="4000"></textarea></div>'
                     for x in rnd["questions"])
        body = (f'<div class="box"><h2>Round {rnd["n"]} of {cfg.get("rounds", 1)}</h2>'
                f'<form method="post" action="/run/answer">{hid}{qs}'
                f'<p class="help">Your answers are saved word for word. Leave one blank to skip it.</p><div class="row">'
                f'<button name="action" value="send">Send answers</button>'
                f'<button class="ghost" name="action" value="skip">Send and go straight to the plan</button></div></form></div>')
    elif ph in ("approving", "done"):
        body = approval(st, hid, ph == "done")
    elif ph == "stopped":
        body = f'<div class="box"><p>Stopped at the gate. The record stays in <code>{e(short(record))}</code>.</p></div>'
    else:
        body = '<div class="box"><p>Waiting to start the next step…</p></div>'
    fast = ph in ("thinking", "asking", "planning")
    project = Path(st["project"])
    head = (f'<p class="crumb"><a href="/">Projects</a> / <a href="/project?p={q(project)}">{e(st["name"])}</a></p>'
            f'<div class="head"><h1>{e(st["name"])}</h1><span class="tag">/start {e(cfg.get("label", st["tier"]).lower())}</span>'
            f'<span class="tag">{e(bd.KIND_LABEL.get(st["kind"], st["kind"]))}</span></div>')
    foot = (f'<footer class="meta">{e(eng.usage_line(st))}<br>Record: {e(short(record))} '
            f'{open_btn(record, "Open folder")}</footer>')
    page = head + f'<ol class="stops">{stops}</ol>' + message_box(message) + body + foot
    return shell(st["name"], page, token, "projects", (f"/run/state?r={q(record)}", ph, 2000 if fast else 15000))


def approval(st: dict, hid: str, done: bool) -> str:
    p, t, a = st["plan"], st.get("time") or {}, st.get("approved") or {}
    v = p["verdict"]
    reasons = "".join(f'<li>{e(x["text"])} <span class="cite">{e(", ".join(x["cites"]))}</span></li>' for x in p["reasons"])
    floor_note = (f'<p class="help">The checks made it stricter than Claude\'s {e(p["model_verdict"])}: {e(" ".join(p["floor"]))}</p>'
                  if p.get("floor") else "")
    concerns = ("<details><summary class='meta'>Concerns (Claude's inferences or your calendar, not reasons)</summary><ul>"
                + "".join(f"<li>{e(c)}</li>" for c in p["concerns"]) + "</ul></details>") if p["concerns"] else ""
    steps = "".join(f'<li>{e(x["text"])} <span class="cite">about {x["hours"]:g} h</span></li>' for x in p["steps"])
    out_scope = ("<p><b>Not in this project:</b> " + e("; ".join(p["out_of_scope"])) + "</p>") if p["out_of_scope"] else ""
    head = (f'<div class="box vbox v-{e(v)}"><h2>Warden: {e(v)}</h2><p style="margin:0 0 6px">{e(p["verdict_line"])}</p>'
            f'<ul>{reasons}</ul>{floor_note}{concerns}</div>'
            f'<div class="box"><p><b>Goal:</b> {e(p["goal"])}</p><p><b>Done when:</b> {e(p["done_when"])}</p>'
            f'<h2>Plan</h2><ol>{steps}</ol>{out_scope}</div>')
    hours = t.get("hours")
    if done:
        res = st.get("result") or {}
        lines = "".join(f"<li>{e(k.capitalize())}: {e(', '.join(x))}</li>" for k, x in res.items() if x and k != "notes")
        notes = "".join(f"<li>{e(x)}</li>" for x in res.get("notes", []))
        approved = ", ".join(a.get("accepted", [])) or "none"
        budget = "%g h" % a["budget"] if a.get("budget") else "not set"
        project = Path(st["project"])
        return (f'<div class="box tint"><h2>Set up</h2><p>Approved by {e(a.get("by", "Luke"))} on {e(a.get("date", ""))}.'
                f' Budget: {e(budget)}. Changes approved: {e(approved)}.</p><ul>{lines}{notes}</ul>'
                f'<div class="row"><a class="btn small" href="/project?p={q(project)}">Go to the project</a>'
                f'{open_btn(project, "Open folder")}</div></div>' + head)
    props = "".join(f'<label class="prop"><input type="checkbox" name="accept" value="{e(x["id"])}">'
                    f'<span><b>{e(x["id"])}</b> {e(x["change"])} <span class="cite">{e(x["why"])}</span></span></label>'
                    for x in p["proposals"])
    props = f"<h2>Proposed changes</h2><p class=\"help\">Tick the ones you approve. None is applied otherwise.</p>{props}" if props else ""
    sugg = (f'Suggested {hours:g} h (the time equation, from Claude\'s estimates'
            + (", assuming 5 h a week free" if t.get("assumed_availability") else "") + ").") if hours is not None else ""
    use = (f'<button type="button" class="ghost small" onclick="document.getElementById(\'budget\').value=\'{hours:g}\'">'
           f'Use {hours:g} h</button>') if hours else ""
    override = (f'<label class="f" for="override">The warden said no. To go ahead anyway, say why (recorded as your override):</label>'
                f'<textarea id="override" name="override" maxlength="2000" style="min-height:60px"></textarea>') if v == "NO-GO" else ""
    go = "Override and set it up" if v == "NO-GO" else "Approve and set it up"
    form = (f'<form method="post" action="/run/approve" class="box">{hid}{props}'
            f'<h2 style="margin-top:12px">Your budget</h2><div class="row"><input type="number" id="budget" name="budget" min="0.1" step="any"'
            f' placeholder="hours" style="max-width:120px"> {use}<span class="help">{e(sugg)} Your number is the one that counts.</span></div>'
            f'{override}<p class="row" style="margin-top:12px"><button>{go}</button></p></form>'
            f'<form method="post" action="/run/stop">{hid}<button class="ghost">Stop here</button></form>')
    return head + form
