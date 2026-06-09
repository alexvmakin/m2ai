"""M2AI — Methodology-to-AI Research Portal (MVP).

Стиль: «карандаш и мел» — светлый чертёжный. Лендинг, статьи, файлы,
дорожная карта, лента изменений (news.json). Полный REST+MCP — позже (KAN-258).
"""
import os
import html
import json
from pathlib import Path
from urllib.parse import quote

import markdown as md
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent.parent
CONTENT = Path(os.environ.get("CONTENT_DIR", BASE / "content"))
ROADMAP_FILE = BASE / "roadmap" / "roadmap.json"
NEWS_FILE = BASE / "roadmap" / "news.json"

app = FastAPI(title="M2AI — Methodology-to-AI Research Portal", docs_url="/api-docs")

if CONTENT.exists():
    app.mount("/content", StaticFiles(directory=str(CONTENT), html=False), name="content")

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600'
         '&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">')

CSS = """
:root{--ink:#16181d;--ink2:#5b606b;--line:#dcdee3;--line2:#bcbfc7;--paper:#ffffff;
--red:#c0392b;--wash:#f7f8fa;--grid:#eef1f5}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:Inter,system-ui,sans-serif;
-webkit-font-smoothing:antialiased;line-height:1.6;
background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px);
background-size:28px 28px}
.mono{font-family:"IBM Plex Mono",ui-monospace,monospace}
a{color:var(--ink);text-decoration:none}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px}
header.top{display:flex;justify-content:space-between;align-items:center;padding:18px 0;border-bottom:2px solid var(--ink)}
.brand{font-weight:600;font-size:19px;letter-spacing:-.01em}
.brand i{color:var(--red);font-style:normal;margin:0 2px}
.brand small{display:block;font-family:"IBM Plex Mono",monospace;font-weight:400;font-size:10px;
letter-spacing:.2em;text-transform:uppercase;color:var(--ink2);margin-top:3px}
nav a{color:var(--ink2);font-size:13px;margin-left:20px}
nav a:hover{color:var(--ink);text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:4px}
.metastrip{display:flex;gap:24px;flex-wrap:wrap;padding:8px 0;border-bottom:1px solid var(--line);
font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink2)}
.layout{display:grid;grid-template-columns:1fr 308px;gap:0}
.layout.full{grid-template-columns:1fr}
.main{padding:32px 38px 40px 0;border-right:1px solid var(--line)}
.layout.full .main{border-right:none;padding-right:0}
.idx{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink2)}
h1{font-size:46px;line-height:1.04;letter-spacing:-.025em;font-weight:600;margin:12px 0 16px}
h1 .u{text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:6px}
h2{font-size:22px;font-weight:600;margin:34px 0 14px;letter-spacing:-.01em}
h3{font-size:16px;font-weight:600;margin:24px 0 10px}
.lead{font-size:17px;line-height:1.55;color:#2a2d34;max-width:600px}
.diagram{display:flex;align-items:center;margin:30px 0;font-family:"IBM Plex Mono",monospace;font-size:11px;flex-wrap:wrap;gap:8px 0}
.node{border:1.5px solid var(--ink);padding:9px 13px;text-align:center;min-width:90px;line-height:1.2;background:var(--paper)}
.node small{display:block;color:var(--ink2);font-size:10px;margin-top:3px}
.arr{flex:0 0 34px;height:1.5px;background:var(--ink);position:relative}
.arr::after{content:"";position:absolute;right:0;top:-4px;border-left:7px solid var(--ink);border-top:4px solid transparent;border-bottom:4px solid transparent}
.stats{display:flex;flex-wrap:wrap;border:1px solid var(--ink);margin:26px 0;background:var(--paper)}
.stats div{flex:1;min-width:90px;padding:15px 14px;border-right:1px solid var(--line)}
.stats div:last-child{border-right:none}
.stats b{display:block;font-size:28px;font-weight:600;letter-spacing:-.02em}
.stats span{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--ink2);letter-spacing:.05em;text-transform:uppercase}
.list{list-style:none;padding:0;margin:0}
.list li{display:flex;align-items:baseline;gap:16px;padding:15px 0;border-top:1px solid var(--line)}
.list li .k{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--red);width:34px;flex:0 0 34px}
.list li a{font-size:19px;font-weight:500}
.list li a:hover{text-decoration:underline;text-decoration-color:var(--red);text-underline-offset:4px}
.list li .d{margin-left:auto;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink2)}
.crumbs{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink2);margin:6px 0 14px}
.md{max-width:720px}.md pre{background:var(--wash);padding:12px 14px;border:1px solid var(--line);overflow:auto}
.md code{background:var(--wash);padding:1px 5px;border:1px solid var(--line)}
.md table{border-collapse:collapse}.md td,.md th{border:1px solid var(--line);padding:6px 10px}
.md h1{font-size:30px;margin-top:8px}.md h2{font-size:20px}.md h3{font-size:16px}
aside.news{padding:32px 0 40px 28px}
aside.news h4{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink2);margin:0 0 4px}
aside.news .rule{height:2px;background:var(--ink);margin-bottom:14px}
.it{padding:13px 0;border-bottom:1px solid var(--line)}
.it .dt{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink2)}
.it .dt b{color:var(--red);font-weight:500}
.it .tg{font-family:"IBM Plex Mono",monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;border:1px solid var(--line2);color:var(--ink2);padding:1px 6px;margin-left:6px}
.it p{margin:6px 0 0;font-size:13px;line-height:1.45}
.it p b{font-weight:600}
footer{border-top:2px solid var(--ink);margin-top:0;padding:14px 0 30px;font-family:"IBM Plex Mono",monospace;
font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
.proj{border:1px solid var(--line2);padding:16px 18px;margin-bottom:14px;background:var(--paper)}
.proj h3{margin:0 0 4px;font-size:18px}
.proj .code{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink2)}
.proj p.sum{color:#2a2d34;margin:8px 0 12px;font-size:14px}
.bar{height:7px;background:var(--wash);border:1px solid var(--line);overflow:hidden;margin:10px 0}
.bar>i{display:block;height:100%;background:var(--ink)}
.chip{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:10px;padding:2px 8px;border:1px solid var(--line2);margin-right:6px;text-transform:uppercase;letter-spacing:.04em}
.s-live{background:#e7f6ee;color:#1c7a4d;border-color:#bfe3cf}
.s-done{background:#e9f1fb;color:#27557f;border-color:#cadcef}
.s-in_progress{background:#fbf3e0;color:#9a6b12;border-color:#ecd9a8}
.s-next{background:#f1ebfb;color:#6a3fa3;border-color:#ddccef}
.s-backlog{background:#f0f1f3;color:#5b606b;border-color:#dcdee3}
.s-idea{background:#f6f6f7;color:#75797f;border-color:#e3e4e7}
.meta-row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink2)}
.epic{border:1px solid var(--line);padding:12px 14px;margin:10px 0;background:var(--wash)}
.epic h4{margin:0 0 8px;font-size:15px}
.tasks{list-style:none;padding:0;margin:0}
.tasks li{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-top:1px dashed var(--line2);font-size:14px}
.tasks li:first-child{border-top:none}
.tl{list-style:none;padding:0;margin:0}
.tl li{padding:8px 0 8px 16px;border-left:2px solid var(--line2);margin-left:6px;font-size:14px}
.tl li b{font-family:"IBM Plex Mono",monospace;color:var(--red);font-weight:500;font-size:12px}
.grp h2{margin-top:28px}
"""


def _load_json(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def news_rail():
    data = _load_json(NEWS_FILE) or {"items": []}
    items = data.get("items", [])[:6]
    rows = ""
    for it in items:
        d = html.escape(it.get("date", ""))
        tg = it.get("tag", "")
        tg_html = f'<span class="tg">{html.escape(tg)}</span>' if tg else ""
        rows += (f'<div class="it"><div class="dt"><b>{d}</b>{tg_html}</div>'
                 f'<p>{html.escape(it.get("text",""))}</p></div>')
    return (f'<aside class="news"><h4>{html.escape(data.get("title","Лента изменений"))}</h4>'
            f'<div class="rule"></div>{rows}'
            f'<div class="it" style="border:none"><a class="mono" style="font-size:11px;color:var(--red)" href="/news">все записи →</a></div></aside>')


NAV = ('<nav><a href="/">Главная</a><a href="/articles">Статьи</a>'
       '<a href="/files">Файлы</a><a href="/roadmap">Дорожная карта</a>'
       '<a href="/news">Лента</a><a href="/api-docs">API</a></nav>')

META = ('<div class="metastrip mono"><span>M2AI · Research Portal</span>'
        '<span>Г.П. Щедровицкий</span><span>1956 — 1987</span>'
        '<span>www.m-2ai.com</span></div>')


def page(title: str, body: str, rail: bool = False) -> str:
    inner = (f'<div class="layout"><div class="main">{body}</div>{news_rail()}</div>'
             if rail else f'<div class="layout full"><div class="main">{body}</div></div>')
    return (
        f'<!doctype html><html lang=ru><head><meta charset=utf-8>'
        f'<meta name=viewport content="width=device-width,initial-scale=1">'
        f'<title>{html.escape(title)}</title>{FONTS}<style>{CSS}</style></head><body>'
        f'<div class="wrap"><header class="top"><div class="brand">М2<i>/</i>Методология'
        f'<small>M2AI — Methodology to AI</small></div>{NAV}</header>{META}'
        f'{inner}'
        f'<footer><span>M2AI — Methodology to AI</span>'
        f'<span>Наследие Г.П. Щедровицкого · алфавит операций мышления</span></footer></div></body></html>'
    )


def fsize(p: Path) -> str:
    n = p.stat().st_size
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if n < 1024 or unit == "ГБ":
            return f"{n:.0f} {unit}" if unit == "Б" else f"{n:.1f} {unit}"
        n /= 1024


VIZ_TITLES = {
    "GP_DECOMPOSITION_RESULTS.html": "GP-разложение: результаты (7-табовый дашборд)",
    "NAVIGATOR_ENTITIES.html": "Навигатор сущностей",
    "NAVIGATOR_MERGED_ALL.html": "Объединённый навигатор",
    "GP_RESEARCH_PROGRAM_v1.html": "Исследовательская программа GP",
}
MD_ARTICLES = {
    "entities/_MASTER_INDEX.md": "Мастер-индекс сущностей",
    "skills/gp-decomposition-SKILL.md": "Методология GP-разложения (алгоритм)",
}


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"


@app.get("/", response_class=HTMLResponse)
def landing():
    ent = len(list((CONTENT / "entities").rglob("entity.md"))) if (CONTENT / "entities").exists() else 0
    bdir = CONTENT / "books"
    books = sum(1 for p in bdir.rglob("*") if p.is_file() and p.suffix.lower() in (".pdf", ".docx")) if bdir.exists() else 0
    decomp = len(list((CONTENT / "decompositions").glob("*.json"))) if (CONTENT / "decompositions").exists() else 0
    body = (
        '<div class="idx mono">00 — Общий вид</div>'
        '<h1>Операции <span class="u">мышления</span>,<br>разложенные.</h1>'
        '<p class="lead">Наследие Г.П. Щедровицкого как формальная система: тексты разложены '
        'на элементарные операции «сопоставление + отнесение», типы сведены в алфавит, '
        'сущности связаны в граф, результаты — в навигаторы и интерактивные отчёты.</p>'
        '<div class="diagram">'
        '<div class="node">ТЕКСТ<small>источник</small></div><div class="arr"></div>'
        '<div class="node">ОПЕРАЦИЯ<small>S1–S6</small></div><div class="arr"></div>'
        '<div class="node">ТИП<small>A01–A18</small></div><div class="arr"></div>'
        '<div class="node">ГРАФ<small>связи</small></div></div>'
        '<div class="stats">'
        f'<div><b>{ent}</b><span>сущности</span></div>'
        '<div><b>18</b><span>типов · A01–A18</span></div>'
        f'<div><b>{decomp}</b><span>разложений</span></div>'
        f'<div><b>{books}</b><span>книг</span></div></div>'
        '<h2>Разделы</h2><ul class="list">'
        '<li><span class="k mono">§01</span><a href="/articles">Статьи и визуализации</a><span class="d">дашборды · методология</span></li>'
        '<li><span class="k mono">§02</span><a href="/files">Библиотека файлов</a><span class="d">книги · разложения · данные</span></li>'
        '<li><span class="k mono">§03</span><a href="/roadmap">Дорожная карта</a><span class="d">8 проектов · логи</span></li>'
        '<li><span class="k mono">§04</span><a href="/api-docs">API / MCP</a><span class="d">интеграции · агенты</span></li>'
        '</ul>'
    )
    return page("M2AI — Research Portal", body, rail=True)


@app.get("/news", response_class=HTMLResponse)
def news_page():
    data = _load_json(NEWS_FILE) or {"items": []}
    rows = ""
    for it in data.get("items", []):
        tg = it.get("tag", "")
        tg_html = f'<span class="tg">{html.escape(tg)}</span>' if tg else ""
        rows += (f'<div class="it"><div class="dt"><b>{html.escape(it.get("date",""))}</b>{tg_html}</div>'
                 f'<p>{html.escape(it.get("text",""))}</p></div>')
    body = '<div class="idx mono">Журнал</div><h2 style="margin-top:8px">Лента изменений</h2>' + rows
    return page("Лента изменений — M2AI", body)


@app.get("/articles", response_class=HTMLResponse)
def articles():
    viz_dir = CONTENT / "visualizations"
    items = "".join(
        f'<li><span class="k mono">{i+1:02d}</span><a href="/content/visualizations/{quote(f)}">{html.escape(t)}</a><span class="d">интерактив</span></li>'
        for i, (f, t) in enumerate(VIZ_TITLES.items()) if (viz_dir / f).exists()
    )
    md_items = "".join(
        f'<li><span class="k mono">{i+1:02d}</span><a href="/md/{quote(rel)}">{html.escape(t)}</a><span class="d">текст</span></li>'
        for i, (rel, t) in enumerate(MD_ARTICLES.items()) if (CONTENT / rel).exists()
    )
    body = ('<div class="idx mono">§01 — Статьи</div><h2 style="margin-top:8px">Визуализации</h2>'
            f'<ul class="list">{items or "<li>—</li>"}</ul>'
            f'<h2>Документы</h2><ul class="list">{md_items or "<li>—</li>"}</ul>')
    return page("Статьи — M2AI", body, rail=True)


@app.get("/md/{relpath:path}", response_class=HTMLResponse)
def render_md(relpath: str):
    target = (CONTENT / relpath).resolve()
    if not str(target).startswith(str(CONTENT.resolve())) or target.suffix.lower() != ".md" or not target.exists():
        raise HTTPException(404, "Документ не найден")
    htmlc = md.markdown(target.read_text(encoding="utf-8", errors="replace"),
                        extensions=["tables", "fenced_code", "toc"])
    body = f'<div class="crumbs"><a href="/articles">← Статьи</a></div><div class="md">{htmlc}</div>'
    return page(target.stem, body)


@app.get("/files", response_class=HTMLResponse)
@app.get("/files/{relpath:path}", response_class=HTMLResponse)
def files(relpath: str = ""):
    root = CONTENT
    target = (root / relpath).resolve()
    if not str(target).startswith(str(root.resolve())) or not target.exists():
        raise HTTPException(404, "Путь не найден")
    if target.is_file():
        return FileResponse(str(target), filename=target.name)
    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    rows = ""
    if relpath:
        parent = "/".join(relpath.rstrip("/").split("/")[:-1])
        rows += f'<li><span class="k mono">··</span><a href="/files/{quote(parent)}">наверх</a></li>'
    for p in entries:
        rel = f"{relpath}/{p.name}" if relpath else p.name
        if p.is_dir():
            cnt = sum(1 for _ in p.iterdir())
            rows += f'<li><span class="k mono">DIR</span><a href="/files/{quote(rel)}">{html.escape(p.name)}/</a><span class="d">{cnt} элем.</span></li>'
        else:
            rows += f'<li><span class="k mono">·</span><a href="/content/{quote(rel)}">{html.escape(p.name)}</a><span class="d">{fsize(p)}</span></li>'
    body = (f'<div class="idx mono">§02 — Файлы</div><div class="crumbs">content/{html.escape(relpath)}</div>'
            f'<ul class="list">{rows}</ul>')
    return page("Файлы — M2AI", body)


HORIZON_ORDER = [("now", "Сейчас"), ("next", "Следующее"), ("later", "Дальше"), ("done", "Завершено")]


def _chip(status):
    return f'<span class="chip s-{html.escape(status)}">{html.escape(status)}</span>'


@app.get("/roadmap", response_class=HTMLResponse)
def roadmap():
    rm = _load_json(ROADMAP_FILE) or {"projects": []}
    projs = rm.get("projects", [])
    by_h = {}
    for p in projs:
        by_h.setdefault(p.get("horizon", "later"), []).append(p)
    total = len(projs)
    avg = round(sum(p.get("progress", 0) for p in projs) / total) if total else 0
    body = ('<div class="idx mono">§03 — Дорожная карта</div>'
            '<p class="lead" style="margin-top:10px">Портфель проектов «Методологии»: статусы, эпики, '
            'зависимости и лог движения. Данные — связанный граф объектов (roadmap.json).</p>'
            '<div class="stats">'
            f'<div><b>{total}</b><span>проектов</span></div>'
            f'<div><b>{sum(1 for p in projs if p.get("status") in ("live","done"))}</b><span>готово / в проде</span></div>'
            f'<div><b>{avg}%</b><span>средний прогресс</span></div></div>')
    for hkey, htitle in HORIZON_ORDER:
        items = by_h.get(hkey, [])
        if not items:
            continue
        body += f'<div class="grp"><h2>{html.escape(htitle)}</h2>'
        for p in items:
            deps = p.get("depends_on") or []
            depstr = (" · зависит: " + ", ".join(deps)) if deps else ""
            body += (
                f'<div class="proj"><div class="code">{html.escape(p.get("code",""))}{depstr}</div>'
                f'<h3><a href="/roadmap/{html.escape(p.get("id",""))}">{html.escape(p.get("title",""))}</a></h3>'
                f'<div class="meta-row">{_chip(p.get("status","backlog"))}'
                f'<span>приоритет: {html.escape(p.get("priority","-"))}</span><span>{p.get("progress",0)}%</span></div>'
                f'<div class="bar"><i style="width:{p.get("progress",0)}%"></i></div>'
                f'<p class="sum">{html.escape(p.get("summary",""))}</p></div>'
            )
        body += '</div>'
    return page("Дорожная карта — M2AI", body, rail=True)


@app.get("/roadmap/{pid}", response_class=HTMLResponse)
def roadmap_project(pid: str):
    rm = _load_json(ROADMAP_FILE) or {"projects": []}
    p = next((x for x in rm.get("projects", []) if x.get("id") == pid), None)
    if not p:
        raise HTTPException(404, "Проект не найден")
    deps = ", ".join(p.get("depends_on") or []) or "—"
    body = ('<div class="crumbs"><a href="/roadmap">← Дорожная карта</a></div>'
            f'<div class="idx mono">{html.escape(p.get("code",""))}</div>'
            f'<h2 style="margin-top:6px">{html.escape(p.get("title",""))}</h2>'
            f'<div class="meta-row">{_chip(p.get("status","backlog"))}'
            f'<span>приоритет: {html.escape(p.get("priority","-"))}</span>'
            f'<span>горизонт: {html.escape(p.get("horizon","-"))}</span>'
            f'<span>зависит: {html.escape(deps)}</span></div>'
            f'<div class="bar"><i style="width:{p.get("progress",0)}%"></i></div>'
            f'<p class="lead" style="font-size:15px">{html.escape(p.get("summary",""))}</p>'
            '<h3>Эпики и задачи</h3>')
    for e in p.get("epics", []):
        body += f'<div class="epic"><h4>{_chip(e.get("status","backlog"))} {html.escape(e.get("title",""))}</h4><ul class="tasks">'
        for t in e.get("tasks", []):
            body += f'<li><span>{html.escape(t.get("title",""))}</span>{_chip(t.get("status","backlog"))}</li>'
        body += '</ul></div>'
    log = p.get("log", [])
    body += '<h3>Лог движения</h3>'
    body += ('<ul class="tl">' + "".join(
        f'<li><b>{html.escape(l.get("date",""))}</b><br>{html.escape(l.get("entry",""))}</li>' for l in log
    ) + '</ul>') if log else '<p class="sum">записей пока нет</p>'
    return page(p.get("title", "Проект") + " — M2AI", body)
